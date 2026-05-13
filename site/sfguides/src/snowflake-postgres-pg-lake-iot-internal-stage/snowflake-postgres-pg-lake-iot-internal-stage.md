author: Brian Pace
id: snowflake-postgres-pg-lake-iot-internal-stage
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Build bidirectional data pipelines between Snowflake Postgres (pg_lake) and Snowflake - Internal Stage
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Bidirectional Data Pipelines with pg_lake and Snowflake - Internal Stage
<!-- ------------------------ -->
## Overview 

### What is pg_lake?

PostgreSQL (Postgres) extensions are loadable modules that add new functionality to the database—such as data types, functions, operators, and storage engines—without modifying the core Postgres code. For more details, see the [Postgres Extensions documentation](https://www.postgresql.org/docs/current/extend-extensions.html).

[pg_lake](https://github.com/Snowflake-Labs/pg_lake) is a powerful Postgres extension available in Snowflake Postgres that enables direct reading and writing of data lake files stored in cloud object storage or Snowflake internal stages. With pg_lake, you can export data from Postgres tables directly to storage in various formats (CSV, Parquet, JSON), query files using foreign tables without importing the data, and create Iceberg tables for open table format storage.

When combined with Snowflake's data platform, pg_lake enables simple bidirectional data pipelines that leverage the operational strengths of Postgres alongside Snowflake's powerful analytics and AI capabilities.

### External Stage vs. Internal Stage

pg_lake supports two storage options for exchanging data between Postgres and Snowflake:

| | External Stage | Internal Stage |
|---|---|---|
| Storage location | Customer-provided object storage (e.g. Amazon S3, Azure Blob) | Snowflake-managed internal object storage |
| Configuration | Requires IAM roles, trust policies, and storage integrations for both Postgres and Snowflake | Minimal setup — automatically provisioned with the Postgres instance |
| Data residency | Data resides in the customer's cloud account | Data never leaves the Snowflake security perimeter |
| Use when | You need to share data with systems outside of Snowflake, retain data in your own storage, or integrate with existing data lake architectures | You want the simplest setup, maximum security, and data exchange is exclusively between Snowflake Postgres and Snowflake |

This quickstart uses the **internal stage** approach. For the external stage version using customer-provided S3 storage, see [Bidirectional Data Pipelines with pg_lake and Snowflake - External Stage](en/developers/guides/snowflake-postgres-pg-lake-iot/).

### Use Case: IoT Sensor Monitoring

This quickstart demonstrates a practical IoT sensor monitoring scenario where:
- **Postgres** handles real-time sensor data ingestion from building systems (HVAC, power meters, etc.)
- **Internal Stage** serves as the data exchange layer between systems
- **Snowflake** performs AI-powered anomaly detection using Cortex and returns insights back to Postgres

This pattern is common in operational scenarios where transactional systems need to share data with analytical platforms while receiving enriched results back.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BIDIRECTIONAL DATA FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐         ┌─────────────┐         ┌──────────────┐         │
│   │  PostgreSQL  │  ────►  │  Internal   │  ────►  │  Snowflake   │         │
│   │              │         │  Stage      │         │              │         │
│   │  • pg_lake   │  CSV    │  • export/  │  COPY   │  • Cortex AI │         │
│   │  • Iceberg   │  Parquet│  • sync/    │  INTO   │  • Streams   │         │
│   │              │  JSON   │  • archive/ │         │  • Tasks     │         │
│   │              │         │             │         │              │         │
│   │              │  ◄────  │             │  ◄────  │              │         │
│   └──────────────┘         └─────────────┘         └──────────────┘         │
│           Foreign Tables           Stream + COPY                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What You Will Learn 

- Export data from Postgres to Internal Stage in multiple formats using Postgres's COPY command
- Query Internal Stage files directly from Postgres using foreign tables (no data import required)
- Load data into Snowflake from Internal Stage using COPY INTO
- Detect anomalies and generate AI explanations using Snowflake Cortex
- Sync analytical results back to Postgres via Internal Stage

### Data Model

This lab simulates IoT sensor readings from 10 devices across a building complex:

| Sensor Type  | Devices | Value Range | Unit | Description |
|--------------|---------|-------------|------|-------------|
| Temperature  | 5       | 68-80       | °F   | HVAC systems, server rooms, freezers |
| Power        | 5       | 100-500     | kW   | Main panels, UPS, motors |

The lab generates approximately 100,000 sensor readings spanning several months of historical data at 15-minute intervals.

### Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Local terminal session to run `psql`
- `psql` client installed locally (install with `brew install postgresql` on macOS)
- Familiarity with SQL and basic Postgres concepts

<!-- ------------------------ -->
## Postgres Instance Setup

Create a Snowflake Postgres instance with pg_lake enabled.

### Step 1: Create Network Policy

Snowflake Postgres requires a network policy to allow client connections. Replace `nnn.nnn.nnn.nnn/32` with a specific IP address (or subnet) and CIDR for your organization.

```sql
-- Postgres Instance Setup: Step 1 - Create Network Policy
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS PG_NETWORK_DB;
CREATE SCHEMA IF NOT EXISTS PG_NETWORK_DB.PG_NETWORK;

USE SCHEMA PG_NETWORK_DB.PG_NETWORK;

-- Get current IP if needed for Network Rule.  
-- This value may be used for `nnn.nnn.nnn.nnn` to limit access to your connection.
SELECT CURRENT_IP_ADDRESS();

CREATE OR REPLACE NETWORK RULE PG_IOT_INGRESS_RULE
    TYPE = IPV4
    VALUE_LIST = ('nnn.nnn.nnn.nnn/32')
    MODE = POSTGRES_INGRESS
    COMMENT = 'Allow Postgres client connections (restrict in production)';

CREATE OR REPLACE NETWORK POLICY PG_IOT_NETWORK_POLICY
    ALLOWED_NETWORK_RULE_LIST = ('PG_IOT_INGRESS_RULE')
    COMMENT = 'Network policy for Snowflake Postgres instances';
```

### Step 2: Create Postgres Instance

```sql
-- Postgres Instance Setup: Step 2 - Create Postgres Instance
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

CREATE POSTGRES INSTANCE IOT_PG
    AUTHENTICATION_AUTHORITY = POSTGRES
    COMPUTE_FAMILY = 'STANDARD_L'
    STORAGE_SIZE_GB = 200
    POSTGRES_VERSION = 18
    HIGH_AVAILABILITY = FALSE
    NETWORK_POLICY = 'PG_IOT_NETWORK_POLICY'
    COMMENT = 'IoT Lab Postgres instance for pg_lake demos';
```

> **Important:** Save the user and password displayed in the `access_roles` field and the `host` - you'll need it to connect.

### Step 3: Monitor Instance Status

Wait for the instance to reach READY state:

```sql
-- Postgres Instance Setup: Step 3 - Monitor Instance Status
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

SHOW POSTGRES INSTANCES;

DESCRIBE POSTGRES INSTANCE IOT_PG;
```

Record the **host** value from the DESCRIBE output.

### Step 4: Configure psql Connection

Set environment variables in your terminal:

```bash
export PGHOST=<hostname from DESCRIBE output>
export PGPORT=5432
export PGDATABASE=postgres
export PGUSER=snowflake_admin
export PGPASSWORD=<password from CREATE output>
export PGSSLMODE=require
```

Test the connection:

```bash
psql -c "SELECT version();"
```
<!-- -------------------------->

## Storage Integration Configuration

When using pg_lake to move data between Postgres and Snowflake via an internal stage, no external cloud storage is required. The internal stage is automatically provisioned when the Postgres instance is created. On the Snowflake side, you need to configure a storage integration that points to it. Both platforms share this stage location to exchange data. The key advantage of using the internal stage is that data never leaves the security perimeter of Snowflake.

Run the following in Snowflake, replacing `IOT_PG` with the name of your Postgres instance if you used a different name:

```sql
-- Snowflake Setup: Internal Stage Configuration
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE STORAGE INTEGRATION SF_LAB_INTS3_INTEGRATION
    TYPE = POSTGRES_INTERNAL_STORAGE
    POSTGRES_INSTANCE = 'IOT_PG'
    ENABLED = TRUE;
```

<!---------------------------->
## Snowflake Setup

Create the Snowflake database objects that will receive data from Postgres and store anomaly detection results.

### Step 1: Create Database and Warehouse

```sql
-- Snowflake Setup: Step 1 - Create Database and Warehouse
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS IOT_LAB;
CREATE SCHEMA IF NOT EXISTS IOT_LAB.SENSORS;

USE SCHEMA IOT_LAB.SENSORS;

CREATE WAREHOUSE IF NOT EXISTS IOT_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

USE WAREHOUSE IOT_WH;
```

### Step 2: Create Tables

```sql
-- Snowflake Setup: Step 2 - Create Tables
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

CREATE OR REPLACE TABLE SENSOR_READINGS (
    READING_ID       INT,
    SENSOR_NAME      VARCHAR(50),
    SENSOR_TYPE      VARCHAR(20),
    READING_TS       TIMESTAMP_NTZ,
    VALUE            NUMBER(10,2),
    UNIT             VARCHAR(10),
    LOADED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE SENSOR_ANOMALIES (
    ANOMALY_ID       INT AUTOINCREMENT PRIMARY KEY,
    SENSOR_NAME      VARCHAR(50),
    SENSOR_TYPE      VARCHAR(20),
    READING_TS       TIMESTAMP_NTZ,
    PREDICTED_VALUE  NUMBER(10,2),
    ACTUAL_VALUE     NUMBER(10,2),
    ANOMALY_SCORE    NUMBER(5,4),
    AI_EXPLANATION   VARCHAR(1000),
    DETECTED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```


### Step 3: Create Storage Integration

```sql
-- Snowflake Setup: Step 3 - Verify Stage Access
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;  

CREATE OR REPLACE STAGE IOT_INT_STAGE
    STORAGE_INTEGRATION = SF_LAB_INTS3_INTEGRATION
    RELATIVE_URL = '/';
```

### Step 4: Create File Format

```sql
-- Snowflake Setup: Step 4 - Create File Format
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

CREATE OR REPLACE FILE FORMAT CSV_FORMAT_IOT
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null', '');
```

### Step 5: Verify Stage Access

```sql
-- Snowflake Setup: Step 5 - Verify Stage Access
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

LIST @IOT_INT_STAGE/;
```

This should return an empty result (no files yet) without errors, confirming access is working.

<!---------------------------->

## Postgres Setup

Create the IoT sens

 Note: `psql` is relying on the environment variables set earlier for the connection string information.or tables and generate sample data in Postgres.

### Step 1: Enable Extensions

[psql](https://www.postgresql.org/docs/current/app-psql.html) is the interactive terminal for PostgreSQL, allowing you to enter queries, execute SQL commands, and manage the database from the command line.

Connect to Postgres via `psql` and enable pg_lake:

```bash
psql
```

```sql
-- Postgres Setup: Step 1 - Enable Extensions
-- Execute in: psql (Postgres)
CREATE EXTENSION IF NOT EXISTS pg_lake CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_incremental;
```

The `CASCADE` option automatically creates required dependencies like the `pg_lake` foreign data wrapper server.

### Step 2: Create Sensor Readings Table

```sql
-- Postgres Setup: Step 2 - Create Sensor Readings Table
-- Execute in: psql (Postgres)
CREATE TABLE sensor_readings (
    reading_id   BIGSERIAL PRIMARY KEY,
    sensor_name  TEXT NOT NULL,
    sensor_type  TEXT NOT NULL,
    reading_ts   TIMESTAMP NOT NULL,
    value        NUMERIC(10,2) NOT NULL,
    unit         TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_readings_ts ON sensor_readings (reading_ts);
CREATE INDEX idx_readings_sensor ON sensor_readings (sensor_name, reading_ts);
```

### Step 3: Generate Historical Sensor Data

This generates approximately 100,000 readings from 10 sensors over several months:

```sql
-- Postgres Setup: Step 3 - Generate Historical Sensor Data
-- Execute in: psql (Postgres)
INSERT INTO sensor_readings (sensor_name, sensor_type, reading_ts, value, unit)
SELECT   sensor_name,
         sensor_type,
         ts,
         CASE sensor_type
             WHEN 'temperature' THEN 68 + (random() * 12)::numeric(10,2)
             WHEN 'power'       THEN 100 + (random() * 400)::numeric(10,2)
         END AS value,
         CASE sensor_type
             WHEN 'temperature' THEN '°F'
             WHEN 'power'       THEN 'kW'
         END AS unit
FROM     (
             SELECT * FROM (VALUES
                 ('HVAC-Floor1',     'temperature'),
                 ('HVAC-Floor2',     'temperature'),
                 ('HVAC-Floor3',     'temperature'),
                 ('Freezer-Main',    'temperature'),
                 ('ServerRoom-A',    'temperature'),
                 ('MainPanel-A',     'power'),
                 ('MainPanel-B',     'power'),
                 ('DataCenter-UPS',  'power'),
                 ('HVAC-Compressor', 'power'),
                 ('Elevator-Motor',  'power')
             ) AS s(sensor_name, sensor_type)
         ) sensors
CROSS JOIN generate_series(1, 10000) AS n
CROSS JOIN LATERAL (
    SELECT now() - (n * interval '15 minutes') AS ts
) timestamps;
```

### Step 4: Verify Data Load

```sql
-- Postgres Setup: Step 4 - Verify Data Load
-- Execute in: psql (Postgres)
SELECT   sensor_type,
         count(*) AS readings,
         round(avg(value), 2) AS avg_value,
         min(reading_ts) AS earliest,
         max(reading_ts) AS latest
FROM     sensor_readings
GROUP BY sensor_type
ORDER BY sensor_type;
```

You should see approximately 50,000 readings per sensor type.

### Step 5: Create Anomalies Table

This table will receive AI-enriched anomaly data from Snowflake:

```sql
-- Postgres Setup: Step 5 - Create Anomalies Table
-- Execute in: psql (Postgres)
CREATE TABLE sensor_anomalies (
    anomaly_id       BIGSERIAL PRIMARY KEY,
    sensor_name      TEXT NOT NULL,
    sensor_type      TEXT NOT NULL,
    reading_ts       TIMESTAMP NOT NULL,
    predicted_value  NUMERIC(10,2),
    actual_value     NUMERIC(10,2),
    anomaly_score    NUMERIC(5,4),
    ai_explanation   TEXT,
    detected_at      TIMESTAMP DEFAULT now()
);
```

### Step 6: Create Foreign Table for Sync Files

This foreign table will read anomaly files exported from Snowflake:

```sql
-- Postgres Setup: Step 6 - Create Foreign Table for Sync Files
-- Execute in: psql (Postgres)
CREATE FOREIGN TABLE sync_anomalies (
    sensor_name      TEXT,
    sensor_type      TEXT,
    reading_ts       TEXT,
    predicted_value  TEXT,
    actual_value     TEXT,
    anomaly_score    TEXT,
    ai_explanation   TEXT,
    _filename        TEXT
)
SERVER pg_lake
OPTIONS (
    header 'true',
    format 'csv',
    filename 'true',
    compression 'gzip',
    quote '"',    
    path '@STAGE/iot/sync/*'
);
```

<!---------------------------->

## Export Data from Postgres

Use pg_lake to export sensor data from Postgres to the internal stage. This demonstrates the first half of bidirectional data movement.

### Understanding pg_lake COPY

The pg_lake extension extends Postgres's standard `COPY` command to support internal stage and object storage destinations. The syntax is similar to standard COPY but writes directly to the stage instead of local files.

### Step 1: Check Data to Export

```sql
-- Export Data from Postgres: Step 1 - Check Data to Export
-- Execute in: psql (Postgres)
SELECT   sensor_type, count(1) AS cnt
FROM     sensor_readings
GROUP BY sensor_type;
```

### Step 2: Export to CSV

Export sensor readings to the internal stage in compressed CSV format:

```sql
-- Export Data from Postgres: Step 2 - Export to CSV
-- Execute in: psql (Postgres)
COPY (
    SELECT   reading_id, sensor_name, sensor_type, reading_ts, value, unit
    FROM     sensor_readings
) TO '@STAGE/iot/export/sensor_readings.csv.gz'
WITH (header true, compression gzip, format csv);
```

A subquery was used to show how you could be more selective in the data that was copied. By using the subquery you could filter specific rows, columns, or even join to another table. Alternatively, you could omit the subquery and use the table name directly to copy the entire table.

> **Format Note:** pg_lake supports multiple output formats. You can specify the format either through the file extension (`.csv`, `.parquet`, `.json`) or explicitly in the `WITH` clause using `format csv|json|parquet`. Additional options like `compression gzip` can reduce file sizes significantly.

### Step 3: Verify Export

Use `lake_file.list()` to browse the internal stage contents directly from Postgres:

```sql
-- Export Data from Postgres: Step 3 - Verify Export
-- Execute in: psql (Postgres)
SELECT * FROM lake_file.list('@STAGE/iot/export/*');
```

You should see the exported CSV file with its size and modification timestamp.

<!---------------------------->

## Query CSV with Foreign Tables

pg_lake enables querying files directly in object storage without importing data into Postgres tables. This is useful for ad-hoc analysis of exported data or for building data pipelines.

### Understanding Foreign Tables

Foreign tables in pg_lake create a virtual table that reads from the internal stage on demand. The data stays in the stage — queries execute by fetching and processing the data at query time. This is ideal for:
- Verifying exported data before loading elsewhere
- Querying archived data without storage overhead
- Building lightweight data pipelines

### Step 1: Create CSV Foreign Table

Create the `readings_csv` foreign table:

```sql
-- Query Internal Stage with Foreign Tables: Step 1 - Create CSV Foreign Table
-- Execute in: psql (Postgres)
CREATE FOREIGN TABLE readings_csv()
SERVER pg_lake
OPTIONS (
    header 'true',
    format 'csv',
    filename 'true',
    path '@STAGE/iot/export/sensor_readings.csv.gz'
);
```

The empty parentheses `()` tell pg_lake to infer the schema from the file. The `filename 'true'` option adds a `_filename` column showing the source file.

### Step 2: Query the Foreign Table

```sql
-- Query Internal Stage with Foreign Tables: Step 2 - Query the Foreign Table
-- Execute in: psql (Postgres)
SELECT * FROM readings_csv LIMIT 10;
```

This reads directly from the internal stage — no data is stored in Postgres.

### Step 3: Aggregate Data from Internal Stage

Foreign tables support standard SQL operations:

```sql
-- Query Internal Stage with Foreign Tables: Step 3 - Aggregate Data from Internal Stage
-- Execute in: psql (Postgres)
SELECT   sensor_type, 
         count(*) AS readings, 
         round(avg(value::numeric), 2) AS avg_value
FROM     readings_csv
GROUP BY sensor_type;
```

<!---------------------------->

## Load Data into Snowflake

Loaiot/d the exported sensor data from the internal stage into Snowflake for analytics processing.

### Step 1: Verify Files in Stage

In Snowflake:

```sql
-- Preview Data into Snowflake
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

SELECT   $1, $2, $3, $4, $5, $6
FROM     @IOT_INT_STAGE/iot/export/sensor_readings.csv.gz
LIMIT    10;
```

### Step 2: Load CSV Data

```sql
-- Load Data into Snowflake: Step 2 - Load CSV Data
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

COPY INTO SENSOR_READINGS (READING_ID, SENSOR_NAME, SENSOR_TYPE, READING_TS, VALUE, UNIT)
FROM @IOT_INT_STAGE/iot/export/
FILE_FORMAT = 'CSV_FORMAT_IOT'
PATTERN = '.*readings.*\\.csv.gz'
ON_ERROR = 'CONTINUE';
```

> **Automation Note:** For production pipelines, this COPY command can be automated in several ways:
> - **Snowpipe**: Configure auto-ingest to automatically load new files as they arrive in the stage
> - **Tasks**: Schedule periodic COPY operations using Snowflake Tasks
> - **Streams + Tasks**: Combine change data capture with scheduled processing for event-driven pipelines
>
> See the [Snowpipe Documentation](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro) for auto-ingest configuration.

### Step 3: Verify Load

```sql
-- Load Data into Snowflake: Step 3 - Verify Load
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

SELECT   SENSOR_TYPE,
         COUNT(*) AS READINGS,
         ROUND(AVG(VALUE), 2) AS AVG_VALUE,
         MIN(READING_TS) AS EARLIEST,
         MAX(READING_TS) AS LATEST
FROM     SENSOR_READINGS
GROUP BY SENSOR_TYPE
ORDER BY SENSOR_TYPE;
```

<!---------------------------->

## Anomaly Detection with Cortex AI

Use Snowflake Cortex to detect anomalies and generate AI-powered explanations. This demonstrates enriching operational data with AI capabilities.

### Understanding Cortex Complete

Snowflake Cortex provides access to large language models (LLMs) directly within SQL queries. The `COMPLETE` function sends prompts to an LLM and returns generated text. This enables AI enrichment without external API calls or data movement.

### Step 1: Detect Anomalies and Generate AI Explanations

This single statement simulates anomalies (using a simplified scoring approach for this lab) and generates natural language explanations using Cortex:

```sql
-- Anomaly Detection with Cortex AI: Step 1 - Detect Anomalies and Generate AI Explanations
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

INSERT INTO SENSOR_ANOMALIES (SENSOR_NAME, SENSOR_TYPE, READING_TS, PREDICTED_VALUE, ACTUAL_VALUE, ANOMALY_SCORE, AI_EXPLANATION)
SELECT   SENSOR_NAME, 
         SENSOR_TYPE, 
         READING_TS, 
         ROUND(VALUE * 0.9, 2) AS PREDICTED_VALUE,
         VALUE AS ACTUAL_VALUE,
         0.75 AS ANOMALY_SCORE,
         SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b',
             'In 1 sentence, explain this IoT anomaly: ' || SENSOR_NAME || 
             ' (' || SENSOR_TYPE || ') read ' || VALUE || ' ' || UNIT
         )
FROM     SENSOR_READINGS
ORDER BY RANDOM()
LIMIT    100;
```

This generates 100 sample anomalies with AI explanations. In production, you would use statistical methods (Z-score, IQR, ML models) for actual anomaly detection.

### Step 2: View AI-Explained Anomalies

```sql
-- Anomaly Detection with Cortex AI: Step 2 - View AI-Explained Anomalies
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

SELECT   ANOMALY_ID, 
         SENSOR_NAME, 
         SENSOR_TYPE, 
         ANOMALY_SCORE, 
         AI_EXPLANATION, 
         DETECTED_AT
FROM     SENSOR_ANOMALIES
ORDER BY DETECTED_AT DESC
LIMIT    10;
```

Each anomaly now has a human-readable explanation generated by the LLM, making it easier for operators to understand and act on alerts.

<!---------------------------->

## Sync Anomalies to Postgres

Export the AI-enriched anomalies back to internal stage for Postgres to consume, completing the bidirectional data flow.

### Step 1: Export to Internal Stage

```sql
-- Sync Anomalies to Postgres: Step 1 - Export to Internal Stage
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

COPY INTO @IOT_INT_STAGE/iot/sync/
FROM (
    SELECT sensor_name, sensor_type, reading_ts, predicted_value, actual_value,
           anomaly_score, ai_explanation
    FROM   sensor_anomalies
)
FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"')
HEADER = TRUE
INCLUDE_QUERY_ID = TRUE
SINGLE = FALSE
MAX_FILE_SIZE = 16000000
OVERWRITE = FALSE;
```

> **Automation Note:** This COPY command can be wrapped in a Snowflake Task to run automatically on a schedule or when the stream contains data. Example:
> ```sql
> CREATE TASK EXPORT_ANOMALIES_TASK
>     WAREHOUSE = IOT_WH
>     SCHEDULE = '5 MINUTE'
> WHEN
>     SYSTEM$STREAM_HAS_DATA('ANOMALIES_STREAM')
> AS
>     COPY INTO @IOT_INT_STAGE/iot/sync/ FROM (...);
> ```
> This creates an event-driven pipeline that exports anomalies as soon as they're detected.

### Step 2: Verify Export

```sql
-- Sync Anomalies to Postgres: Step 2 - Verify Export
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

LIST @IOT_INT_STAGE/iot/sync/;
```

You should see one or more CSV files containing the anomaly data.

<!---------------------------->

## Receive Anomalies in Postgres

Import the AI-enriched anomaly data back into Postgres, completing the round trip.

### Step 1: Check for Sync Files

In Postgres, use the list function to check for files from Snowflake:

```sql
-- Receive Anomalies in Postgres: Step 1 - Check for Sync Files
-- Execute in: psql (Postgres)
SELECT * FROM lake_file.list('@STAGE/iot/sync/*');
```

### Step 2: Import Anomalies

Load the anomaly data using the pre-configured foreign table:

```sql
-- Receive Anomalies in Postgres: Step 2 - Import Anomalies
-- Execute in: psql (Postgres)
INSERT INTO sensor_anomalies (sensor_name, sensor_type, reading_ts, predicted_value, actual_value, anomaly_score, ai_explanation)
(SELECT   sensor_name::text, 
          sensor_type::text, 
          reading_ts::timestamp, 
          predicted_value::numeric(10,2),
          actual_value::numeric(10,2), 
          anomaly_score::numeric(5,4), 
          ai_explanation::text
FROM     sync_anomalies
WHERE    _filename IN (SELECT path FROM lake_file.list('@STAGE/iot/sync/*')))
ON CONFLICT DO NOTHING;
```

The `ON CONFLICT DO NOTHING` clause ensures idempotent processing - running this multiple times won't create duplicates.

### Step 3: View AI-Enriched Anomalies in Postgres

```sql
-- Receive Anomalies in Postgres: Step 3 - View AI-Enriched Anomalies in Postgres
-- Execute in: psql (Postgres)
SELECT   sensor_name, 
         sensor_type, 
         reading_ts, 
         anomaly_score, 
         ai_explanation, 
         detected_at
FROM     sensor_anomalies
ORDER BY detected_at DESC
LIMIT    10;
```

The anomalies detected in Snowflake with AI explanations are now available in Postgres for operational use.

<!---------------------------->

## Cleanup

### Postgres Cleanup

```sql
-- Cleanup: Postgres Cleanup
-- Execute in: psql (Postgres)
DROP TABLE IF EXISTS sensor_anomalies CASCADE;
DROP TABLE IF EXISTS sensor_readings CASCADE;

DROP FOREIGN TABLE IF EXISTS sync_anomalies CASCADE;
DROP FOREIGN TABLE IF EXISTS readings_csv CASCADE;

-- Remove Files
SET pg_lake_table.enable_delete_file_function=true;
SELECT lake_file.delete(path) FROM lake_file.list('@STAGE/iot/export/*');
SELECT lake_file.delete(path) FROM lake_file.list('@STAGE/iot/sync/*');
SELECT lake_file_cache.remove(path) FROM lake_file_cache.list();
```

### Snowflake Cleanup

```sql
-- Cleanup: Snowflake Cleanup
-- Execute in: Snowsight (Snowflake)
USE ROLE SYSADMIN;
USE SCHEMA IOT_LAB.SENSORS;

DROP TABLE IF EXISTS SENSOR_ANOMALIES;
DROP TABLE IF EXISTS SENSOR_READINGS;

DROP STAUSE ROLE ACCOUNTADMIN;

DROP STORAGE INTEGRATION IF EXISTS SF_LAB_INTS3_INTEGRATION;

DROP POSTGRES INSTANCE IF EXISTS IOT_PG;

USE SCHEMA PG_NETWORK_DB.PG_NETWORK;

DROP NETWORK POLICY IF EXISTS PG_IOT_NETWORK_POLICY;
DROP NETWORK RULE IF EXISTS PG_IOT_INGRESS_RULE;Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

DROP POSTGRES INSTANCE IF EXISTS IOT_PG;

USE SCHEMA PG_NETWORK_DB.PG_NETWORK;

DROP NETWORK POLICY IF EXISTS PG_IOT_NETWORK_POLICY;
DROP NETWORK RULE IF EXISTS PGand _IOT_INGRESS_RULE;

DROP STAGE IF EXISTS IOT_INT_STAGE;
DROP STORAGE INTEGRATION IF EXISTS SF_LAB_INTS3_INTEGRATION;
```

<!---------------------------->

## Conclusion and Resources

### What You Learned

Congratulations! You have successfully:

- Created a Snowflake Postgres instance with pg_lake enabled
- Configured internal stage storage integration for both pg_lake and Snowflake
- Exported data from Postgres to internal stage in CSV format using pg_lake
- Queried internal stage files directly using pg_lake foreign tables
- Loaded data into Snowflake using COPY INTO
- Generated AI-powered anomaly explanations using Snowflake Cortex
- Synchronized analytical results back to Postgres via internal stage

### Key Capabilities Demonstrated

| Postgres (pg_lake) | Snowflake |
|---------------------|-----------|
| COPY TO Internal Stage (CSV, Parquet, JSON) | Internal Stage with COPY INTO |
| Foreign Tables for Internal Stage queries | COPY INTO for data loading |
| lake_file.list() for Internal Stage browsing | Streams for change capture |

### Related Resources

- [Snowpipe Documentation](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro)
- [Snowflake Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/about)

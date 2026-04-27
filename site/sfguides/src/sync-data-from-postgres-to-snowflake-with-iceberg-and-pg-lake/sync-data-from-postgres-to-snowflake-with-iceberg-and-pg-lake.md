author: Elizabeth Christensen
id: sync-data-from-postgres-to-snowflake-with-iceberg-and-pg-lake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Learn how to sync data from Postgres to Snowflake using a shared Apache Iceberg table and the pg_lake extension
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Sync Data from Snowflake Postgres to Snowflake with Iceberg and pg_lake
<!-- ------------------------ -->
## Overview

Duration: 5

>**Note:
>pg_lake features are in preview and under rapid development. Some features may not be available.**<br>

If you're running an application on Snowflake Postgres, you probably have operational data that would be valuable for analytics in Snowflake. The [**pg_lake**](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-pg_lake) extension makes this easy — it lets you create Iceberg tables directly from Postgres using standard SQL (`CREATE TABLE ... USING iceberg`), and Snowflake can read those tables natively through a catalog integration. No ETL pipelines, no data movement tooling, no extra infrastructure.

In a typical pattern, your application writes to regular Postgres tables for fast transactional operations. You then copy that data into an Iceberg table managed by pg_lake, and use [**pg_incremental**](https://github.com/CrunchyData/pg_incremental) to keep the Iceberg table in sync as new data arrives — automatically. Snowflake picks up changes through a catalog integration.

In this quickstart, you will set up an operational Postgres database, copy its data to Iceberg, automate incremental sync, and query the results in Snowflake.

### What You Will Build
- A Snowflake Postgres instance with an operational sensor data table
- An Iceberg table synced from the operational table using pg_lake
- An automated incremental pipeline using pg_incremental
- A Snowflake catalog integration connected to the Postgres Iceberg catalog
- A queryable Iceberg table in Snowflake sourced from Postgres

### What You Will Learn
- How to set up an operational Postgres table and copy data to Iceberg using pg_lake
- How to automate incremental sync with pg_incremental for exactly-once processing
- How to connect Snowflake to Postgres-managed Iceberg tables
- How to query Iceberg data from Snowflake
- How to manually refresh and enable auto-refresh for Iceberg tables

### Prerequisites
- Access to a Snowflake account with Snowflake Postgres enabled
- A SQL client capable of connecting to Postgres (e.g., `psql`)

<!-- ------------------------ -->
## Create a Postgres Instance

Duration: 5

### Overview
Start by creating a new Snowflake Postgres instance. You will need the instance name in a later step when configuring the Snowflake catalog integration.

### Create the Instance
Create a new Snowflake Postgres instance from the Snowflake UI or SQL. If this is your first time, follow the [Getting Started with Snowflake Postgres](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-postgres/) guide for detailed instructions. Copy and save the **instance name** — you will need it when setting up the catalog integration in Snowflake.

### Connect to the Instance
Connect to your Snowflake Postgres instance using `psql` or your preferred SQL client:

```bash
psql postgres://<user>:<password>@<instance-host>:5432/postgres
```

> aside positive
> 
> **Tip**: Keep your instance name handy — you will reference it in the Snowflake catalog integration step.

<!-- ------------------------ -->
## Set Up the Operational Database

Duration: 5

### Overview
Before setting up pg_lake or our analytics, start by creating a regular Postgres table to represent your application's operational data. In a real scenario, this is the table your application writes to — inserts, updates, and deletes happen here as part of normal operations. Later, you will copy this data into an Iceberg table for analytics in Snowflake.

### Create the Sensor Readings Table
Create a standard heap table for IoT sensor data:

```sql
CREATE TABLE sensor_readings (
    sensor_id INT,
    device_type TEXT,
    reading_time TIMESTAMPTZ,
    temperature NUMERIC(5,2),
    humidity NUMERIC(5,2),
    battery_pct NUMERIC(4,1)
);
```

### Seed Sample Data
Insert 5,000 rows of simulated sensor data spanning the last 90 days:

```sql
INSERT INTO sensor_readings (sensor_id, device_type, reading_time, temperature, humidity, battery_pct)
SELECT
    (random() * 50)::int AS sensor_id,
    (ARRAY['thermostat', 'weather_station', 'greenhouse', 'cold_storage', 'hvac'])[1 + (random() * 4)::int] AS device_type,
    now() - (random() * interval '90 days') AS reading_time,
    (random() * 40 + 5)::numeric(5,2) AS temperature,
    (random() * 60 + 20)::numeric(5,2) AS humidity,
    (random() * 80 + 20)::numeric(4,1) AS battery_pct
FROM generate_series(1, 5000);
```

### Verify the Data
Confirm the data looks correct:

```sql
SELECT count(*) AS total_rows FROM sensor_readings;

SELECT device_type, count(*) AS readings, round(avg(temperature), 2) AS avg_temp
FROM sensor_readings
GROUP BY device_type
ORDER BY device_type;
```

You should see 5,000 total rows spread across the five device types.

<!-- ------------------------ -->
## Set Up pg_lake and Copy to Iceberg

Duration: 10

### Overview
Now that you have an active operational table, enable pg_lake and create an Iceberg table to hold a copy of the data for Snowflake analytics. The Iceberg table lives in cloud object storage and is managed by Postgres as the Iceberg catalog — Snowflake reads from it directly.

### Enable Extensions
Install pg_lake, this a series of extensions to connect Postgres to object storage files:

```sql
CREATE EXTENSION pg_lake CASCADE;
```

### Create the Iceberg Table
Create an Iceberg table with the same schema as the operational table. The `USING iceberg` clause tells Postgres to store this table in Iceberg format on cloud object storage:

```sql
CREATE TABLE sensor_readings_iceberg (
    sensor_id INT,
    device_type TEXT,
    reading_time TIMESTAMPTZ,
    temperature NUMERIC(5,2),
    humidity NUMERIC(5,2),
    battery_pct NUMERIC(4,1)
) USING iceberg;
```

### Bulk Copy Existing Data
Copy all existing data from the operational table into the Iceberg table:

```sql
INSERT INTO sensor_readings_iceberg
SELECT * FROM sensor_readings;
```

### Verify the Copy
Confirm both tables have the same row count:

```sql
SELECT
    (SELECT count(*) FROM sensor_readings) AS heap_rows,
    (SELECT count(*) FROM sensor_readings_iceberg) AS iceberg_rows;
```

Both counts should show 5,000.

<!-- ------------------------ -->
## Automate Incremental Sync with pg_incremental

Duration: 10

### Overview
The bulk copy handled the initial backfill, but new data will keep arriving in the operational table. Rather than re-copying everything each time, you can use [**pg_incremental**](https://github.com/CrunchyData/pg_incremental) to automatically sync only new rows on a schedule. pg_incremental is built on pg_cron and provides exactly-once semantics — each time range is processed once and only once, so you will never get duplicates in the Iceberg table.

### Create the Incremental Pipeline

### Install extensions


```sql
CREATE EXTENSION pg_cron;
CREATE EXTENSION pg_incremental;
```
#### Create an append data stream

Define a pipeline that runs every minute and copies new rows based on `reading_time`. The `$1` and `$2` placeholders represent the start and end of each time interval that pg_incremental processes:

```sql
SELECT incremental.create_time_interval_pipeline(
    pipeline_name      := 'sync_readings_to_iceberg',
    time_interval      := '1 hour',
    source_table_name  := 'sensor_readings',
    start_time         := (SELECT min(reading_time) FROM sensor_readings),
    command            := $$
        INSERT INTO sensor_readings_iceberg
        SELECT sensor_id, device_type, reading_time, temperature, humidity, battery_pct
        FROM sensor_readings
        WHERE reading_time >= $1 AND reading_time < $2
    $$
);
```

> aside positive
> 
> **How it works**: pg_incremental tracks which time intervals have already been processed. On each run (every minute by default), it advances the window and executes the `command` for only the new interval. Setting `source_table_name` ensures the pipeline waits for any in-flight writes to `sensor_readings` before processing, preventing data from being skipped.

### Simulate New Data
Insert a batch of 500 new sensor readings with recent timestamps to simulate ongoing application writes:

```sql
INSERT INTO sensor_readings (sensor_id, device_type, reading_time, temperature, humidity, battery_pct)
SELECT
    (random() * 50)::int AS sensor_id,
    (ARRAY['thermostat', 'weather_station', 'greenhouse', 'cold_storage', 'hvac'])[1 + (random() * 4)::int] AS device_type,
    now() - (random() * interval '5 minutes') AS reading_time,
    (random() * 40 + 5)::numeric(5,2) AS temperature,
    (random() * 60 + 20)::numeric(5,2) AS humidity,
    (random() * 80 + 20)::numeric(4,1) AS battery_pct
FROM generate_series(1, 500);
```

### Verify the Incremental Sync
Wait about a minute for the pipeline to run, then check that the new rows have been picked up:

```sql
SELECT
    (SELECT count(*) FROM sensor_readings) AS heap_rows,
    (SELECT count(*) FROM sensor_readings_iceberg) AS iceberg_rows;
```

The Iceberg table should now show 5,500 rows (the original 5,000 plus the 500 new ones). From this point on, any new rows inserted into `sensor_readings` will automatically flow into the Iceberg table on the next pipeline run.

### Check Pipeline Status
You can inspect the pipeline's execution history:

```sql
SELECT * FROM incremental.pipelines;
```

<!-- ------------------------ -->
## Connect Snowflake to Iceberg

Duration: 10

### Overview
Now switch to Snowflake. You will create a catalog integration that connects Snowflake to the Iceberg metadata managed by Postgres, then create an Iceberg table in Snowflake that reads from it.

### Create a Database
Create a database to hold your Iceberg tables in Snowflake:

```sql
CREATE DATABASE pglake;
USE DATABASE pglake;
```

### Create the Catalog Integration
Create a catalog integration that points Snowflake at the Postgres Iceberg catalog. Replace `{instance_name}` with the Snowflake Postgres instance name you saved earlier:

```sql
CREATE OR REPLACE CATALOG INTEGRATION postgres_iceberg_integration
  CATALOG_SOURCE    = SNOWFLAKE_POSTGRES
  TABLE_FORMAT      = ICEBERG
  CATALOG_NAMESPACE = 'public'
  REST_CONFIG = (
    POSTGRES_INSTANCE      = '{instance_name}'
    CATALOG_NAME           = 'postgres'
    ACCESS_DELEGATION_MODE = VENDED_CREDENTIALS
  )
  ENABLED = TRUE;
```

### Create the Iceberg Table
Create an Iceberg table in Snowflake that references the `sensor_readings_iceberg` table in Postgres:

```sql
CREATE OR REPLACE ICEBERG TABLE iot_sensors_from_postgres
    CATALOG = 'postgres_iceberg_integration'
    CATALOG_TABLE_NAME = 'sensor_readings_iceberg';
```

<!-- ------------------------ -->
## Query Iceberg Data

Duration: 5

### Overview
With the Iceberg table created in Snowflake, you can now query data that lives in Postgres-managed Iceberg storage.

### Verify Row Count
Confirm data is visible in Snowflake:

```sql
SELECT COUNT(*) FROM iot_sensors_from_postgres;
```

### Analyze the Data
Run any typical Snowflake analytics. For example, with the sample data loaded above, you can see how many readings land on each day over the 90-day window:

```sql
SELECT
    READING_TIME::DATE AS reading_date,
    COUNT(*) AS record_count
FROM iot_sensors_from_postgres
GROUP BY reading_date
ORDER BY reading_date;
```

<!-- ------------------------ -->
## Refresh and Auto-Refresh

Duration: 10

### Overview
With pg_lake, Postgres is the Iceberg catalog and Snowflake reads the Iceberg metadata through the catalog integration. This makes the table "externally managed" from Snowflake's perspective — Snowflake can query and refresh the data, but Postgres owns the table lifecycle.

Key points:
- You can always run a **manual refresh** to pull the latest data
- **Auto-refresh** (continuous polling) is available but off by default — you must explicitly enable it per table
- The polling frequency is controlled on the catalog integration via `REFRESH_INTERVAL_SECONDS` (default 30s)

### Manual Refresh
If you have inserted new data in Postgres and want it visible in Snowflake immediately, run a manual refresh:

```sql
ALTER ICEBERG TABLE iot_sensors_from_postgres REFRESH;
```

Verify the new data is visible:

```sql
SELECT COUNT(*) FROM iot_sensors_from_postgres;
```

### Enable Auto-Refresh
Enable automatic refresh so Snowflake continuously polls for changes:

```sql
ALTER ICEBERG TABLE iot_sensors_from_postgres SET AUTO_REFRESH = TRUE;
```

### Configure Refresh Interval
The catalog integration controls how often Snowflake polls for changes. Check the current setting:

```sql
DESCRIBE CATALOG INTEGRATION postgres_iceberg_integration;
```

To change the refresh interval (for example, refresh every 60 seconds):

```sql
ALTER CATALOG INTEGRATION postgres_iceberg_integration SET REFRESH_INTERVAL_SECONDS = 60;
```

### Monitor Auto-Refresh
Check whether auto-refresh is running:

```sql
SELECT SYSTEM$AUTO_REFRESH_STATUS('iot_sensors_from_postgres');
```

An `executionState` of `RUNNING` confirms auto-refresh is working.

View the refresh history to see when snapshots were last picked up:

```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.ICEBERG_TABLE_SNAPSHOT_REFRESH_HISTORY(
  TABLE_NAME => 'iot_sensors_from_postgres'
)) ORDER BY REFRESHED_ON DESC LIMIT 10;
```

<!-- ------------------------ -->
## Conclusion and Resources

Duration: 2

### Congratulations!
You have successfully synced data from an operational Postgres database to Snowflake using Iceberg tables, pg_lake, and pg_incremental — with no external ETL pipeline required.

### What You Learned
- How to set up an operational Postgres table and copy data to an Iceberg table using pg_lake
- How to automate incremental sync with pg_incremental for exactly-once processing
- How to create a Snowflake catalog integration that connects to Postgres-managed Iceberg metadata
- How to query Iceberg data from Snowflake
- How to manually refresh Iceberg tables and enable auto-refresh for continuous sync
- How to tune refresh intervals for different workload requirements

### Going Further
This guide covered a single-table sync with time-based incremental processing. In production, you can extend this pattern further:

- **[pg_cron](https://github.com/citusdata/pg_cron)**: Schedule arbitrary SQL jobs directly inside Postgres — useful for aggregations, cleanup tasks, or custom sync logic beyond what pg_incremental handles.
- **[Table partitioning](https://www.snowflake.com/en/engineering-blog/postgres-time-series-iceberg/)**: Combine Postgres declarative partitioning with pg_lake to build automated archiving — keep recent data in local Postgres partitions for fast writes, then offload older partitions to Iceberg on S3 for analytics in Snowflake.


### Related Resources
- [Introducing pg_lake: Integrate Your Data Lakehouse with Postgres](https://www.snowflake.com/en/engineering-blog/pg-lake-postgres-lakehouse-integration/) (blog)
- [Snowflake Postgres: Unify Postgres and Analytics on One Platform](https://www.snowflake.com/en/blog/streamline-data-movement-snowflake-postgres/) (blog)
- [pg_lake: Configuring S3 Storage](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-pg_lake)
- [Snowflake Postgres Extensions](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-extensions)
- [pg_lake GitHub Repository](https://github.com/Snowflake-Labs/pg_lake)
- [pg_lake Iceberg Tables Documentation](https://github.com/Snowflake-Labs/pg_lake/blob/main/docs/iceberg-tables.md)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [Snowflake Documentation](https://docs.snowflake.com/)

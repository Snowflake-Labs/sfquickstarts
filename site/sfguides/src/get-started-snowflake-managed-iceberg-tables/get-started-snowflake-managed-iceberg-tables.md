author: Gilberto Hernandez, Scott Teal
id: get-started-snowflake-managed-iceberg-tables
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/apache-iceberg, snowflake-site:taxonomy/snowflake-feature/lakehouse-analytics, snowflake-site:taxonomy/snowflake-feature/ingestion, snowflake-site:taxonomy/snowflake-feature/interoperable-storage
language: en
summary: Create Snowflake-managed Iceberg tables, stream and transform fleet data, query with Snowflake Intelligence, and read the same tables from DuckDB and Apache Spark.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/get-started-snowflake-managed-iceberg-tables/assets


# Get Started with Iceberg Tables on Snowflake-Managed Storage
<!-- ------------------------ -->
## Overview

Apache Iceberg tables in Snowflake give you the benefits of an open table format — interoperability with engines like Spark, DuckDB, and Flink — while Snowflake handles storage, optimization, and governance for you. With Snowflake-managed Iceberg storage, you don't need to configure a cloud bucket or external volume. Snowflake stores and manages all Iceberg data and metadata files internally, so you can focus on building pipelines and analytics rather than infrastructure.

> **Note**: Snowflake-managed Iceberg tables can be stored in your own cloud storage bucket or in Snowflake-managed storage. For simplicity, this guide uses Snowflake-managed storage so you can get started without any external cloud configuration.

In this Quickstart, you'll build a fleet analytics pipeline using Snowflake-managed Iceberg tables. You'll work with a fictitious fleet management company that collects vehicle telemetry, sensor readings, and maintenance logs. Along the way, you'll stream data, create declarative transformation pipelines, power an AI agent with your data, and prove interoperability by querying the same tables from DuckDB and Apache Spark — without moving a single byte of data.

Let's get started!

### What You'll Learn

- How to create Snowflake-managed Iceberg tables with `EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'`
- How to stream semi-structured data into Iceberg tables using a Python script
- How to batch-load JSON files into Iceberg tables with `COPY INTO`
- How to build declarative transformation pipelines with Dynamic Iceberg Tables
- How to query Iceberg data with natural language using Snowflake Intelligence
- How to read Snowflake-managed Iceberg tables from DuckDB via Horizon Catalog
- How to read Snowflake-managed Iceberg tables from Apache Spark via Horizon Catalog

### What You'll Need

- A Snowflake account ([trial](https://signup.snowflake.com/developers), or otherwise) on **AWS** or **Azure** (Snowflake-managed Iceberg storage is not available on Google Cloud)
- **ACCOUNTADMIN** access
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation) installed with a [configured connection](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/specify-credentials)
- Python 3.9+

### What You'll Build

- Snowflake-managed Iceberg tables for streaming telemetry, sensor readings, vehicle data, and maintenance logs
- A Dynamic Iceberg Table pipeline for automated incremental transformations
- A Cortex Agent for natural language querying of fleet data via Snowflake Intelligence
- DuckDB and Spark notebooks demonstrating cross-engine interoperability on the same Iceberg tables

<!-- ------------------------ -->
## Set Up Environment

This section guides you through setting up your environment. We'll download the companion assets, configure a few variables, and run a setup script that creates all the Snowflake objects we need.

### Download the Assets

Download the companion assets from the [assets folder](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/get-started-snowflake-managed-iceberg-tables/assets) and place them in a local directory. Then navigate into that directory in your terminal.

### Configure Variables

Copy the template to create your configuration file:

```bash
cp config.env.template config.env
```

Then edit **config.env** with your values:

```bash
# Required: Snowflake CLI connection name (run `snow connection list` to see yours)
SNOWFLAKE_CONNECTION="default"

# Required: Account identifier and username (used by DuckDB/Spark interop scripts)
# Find yours: SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME();
SNOWFLAKE_ACCOUNT="your_account_identifier"
SNOWFLAKE_USER="your_username"

# Required: Programmatic Access Token (PAT)
# Create one at: User Menu → My Profile → Programmatic Access Tokens
SNOWFLAKE_PAT=""
```

The streaming script uses `SNOWFLAKE_CONNECTION` to connect via your existing Snowflake CLI configuration in `~/.snowflake/config.toml` — no need to duplicate credentials. The account and user fields are only needed by the DuckDB and Spark interoperability scripts to construct the Horizon Catalog endpoint URL.

> **Note**: Make sure your Snowflake CLI connection is configured. If you haven't set one up yet, run:
> ```bash
> snow connection add --connection-name default --account <your-account> --user <your-user>
> ```

### Run Setup Script

The setup script creates all the Snowflake objects we'll use throughout this Quickstart:

```bash
chmod +x setup.sh
./setup.sh
```

Here's what the setup script does:

- Creates a database called **FLEET_DB** with two schemas: **RAW** and **ANALYTICS**
- Creates a warehouse called **FLEET_WH**
- Sets the database default external volume to `SNOWFLAKE_MANAGED`
- Creates Snowflake-managed Iceberg tables for vehicle telemetry, sensor readings, vehicle registry, and maintenance logs
- Creates Dynamic Iceberg Tables for transformation pipelines
- Loads sample data into the vehicle registry and sensor readings tables
- Uploads JSON maintenance log files to an internal stage
- Sets up a Python virtual environment for the streaming script

### Verify Setup

After the script completes, verify that the objects were created:

```sql
USE DATABASE FLEET_DB;
SHOW ICEBERG TABLES IN SCHEMA RAW;
SHOW DYNAMIC TABLES IN SCHEMA ANALYTICS;
```

You should see four Iceberg tables in the **RAW** schema and two Dynamic Tables in the **ANALYTICS** schema.

<!-- ------------------------ -->
## Create Snowflake-Managed Iceberg Tables

Let's take a closer look at the Iceberg tables the setup script created. The DDL for these tables lives in **02_create_iceberg_tables.sql**. Understanding it is important because it shows how simple it is to create Iceberg tables with Snowflake-managed storage.

### What Makes These Tables "Iceberg"?

Two parameters in the `CREATE ICEBERG TABLE` statement control the storage and catalog:

- **`CATALOG = 'SNOWFLAKE'`** — Snowflake manages the Iceberg metadata (catalog entries, snapshots, manifest files)
- **`EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'`** — Snowflake stores the Iceberg data files internally, just like standard Snowflake tables

Together, these mean you get the open Iceberg format — readable by any engine that speaks the Iceberg REST protocol — without managing cloud storage yourself.

### Vehicle Telemetry (Streaming Target)

This table receives real-time streaming vehicle telemetry. It uses a `VARIANT` column for the flexible-schema telemetry payload:

```sql
CREATE OR REPLACE ICEBERG TABLE FLEET_DB.RAW.VEHICLE_TELEMETRY_STREAM (
    VEHICLE_ID STRING NOT NULL,
    EVENT_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    TELEMETRY_DATA VARIANT NOT NULL,
    INGESTED_AT TIMESTAMP_LTZ(6)
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';
```

The `VARIANT` column is key here. It lets us stream semi-structured JSON telemetry without defining a rigid schema upfront, while still supporting efficient querying with dot notation (e.g., `TELEMETRY_DATA:speed_mph`).

### Vehicle Registry (Master Data)

This table holds master data about vehicles and drivers:

```sql
CREATE OR REPLACE ICEBERG TABLE FLEET_DB.RAW.VEHICLE_REGISTRY (
    VEHICLE_ID STRING NOT NULL,
    VIN STRING,
    MAKE STRING,
    MODEL STRING,
    YEAR INT,
    LICENSE_PLATE STRING,
    DRIVER_NAME STRING,
    DRIVER_EMAIL STRING,
    FLEET_REGION STRING,
    VEHICLE_STATUS STRING DEFAULT 'ACTIVE',
    REGISTRATION_DATE DATE,
    LAST_SERVICE_DATE DATE
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';
```

### Sensor Readings (Time-Series)

This table stores high-frequency sensor data for time-series analysis:

```sql
CREATE OR REPLACE ICEBERG TABLE FLEET_DB.RAW.SENSOR_READINGS (
    READING_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    READING_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    ENGINE_TEMP_F FLOAT,
    OIL_PRESSURE_PSI FLOAT,
    BATTERY_VOLTAGE FLOAT,
    FUEL_CONSUMPTION_GPH FLOAT,
    ODOMETER_MILES FLOAT
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';
```

### Maintenance Logs (Batch JSON)

This table will hold JSON maintenance logs loaded from files:

```sql
CREATE OR REPLACE ICEBERG TABLE FLEET_DB.RAW.MAINTENANCE_LOGS (
    LOG_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    LOG_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    LOG_DATA VARIANT NOT NULL,
    SOURCE_FILE STRING
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';
```

Every one of these tables is a proper Apache Iceberg table stored in the open format — yet creating them requires zero cloud infrastructure setup on your part.

<!-- ------------------------ -->
## Load Data

Now let's populate our tables. The setup script already loaded sample data into the vehicle registry and sensor readings tables. In this step, we'll load JSON maintenance logs from staged files.

### Verify Pre-Loaded Data

The setup script inserted sample data using `INSERT ... SELECT` with Snowflake's `GENERATOR` function. Let's verify:

```sql
USE DATABASE FLEET_DB;
USE WAREHOUSE FLEET_WH;

SELECT 'VEHICLE_REGISTRY' AS table_name, COUNT(*) AS row_count FROM RAW.VEHICLE_REGISTRY
UNION ALL
SELECT 'SENSOR_READINGS', COUNT(*) FROM RAW.SENSOR_READINGS;
```

You should see 100 vehicles in the registry and 10,000 sensor readings.

### Load JSON Maintenance Logs

The setup script uploaded JSON maintenance log files to an internal stage. Let's load them into the **MAINTENANCE_LOGS** Iceberg table:

```sql
-- View the staged files
LIST @RAW.LOGS_STAGE;

-- Load the JSON files into the Iceberg table
COPY INTO RAW.MAINTENANCE_LOGS (LOG_ID, VEHICLE_ID, LOG_TIMESTAMP, LOG_DATA, SOURCE_FILE)
FROM (
    SELECT
        $1:log_id::VARCHAR,
        $1:vehicle_id::VARCHAR,
        $1:log_timestamp::TIMESTAMP_NTZ,
        $1,
        METADATA$FILENAME
    FROM @RAW.LOGS_STAGE
)
FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)
PATTERN = '.*maintenance_log.*\.json';
```

Here's what the code does:

- Lists the staged JSON files to confirm they're present
- Uses `COPY INTO` with a subquery to extract typed fields from the raw JSON (`$1` refers to the entire JSON object in each file)
- Stores the full JSON payload in the `LOG_DATA` VARIANT column for flexible querying
- Captures the source file name in `SOURCE_FILE` for lineage tracking

Let's verify the load and query the VARIANT data:

```sql
-- Verify and query the loaded logs
SELECT
    LOG_ID,
    VEHICLE_ID,
    LOG_TIMESTAMP,
    LOG_DATA:event_type::STRING AS event_type,
    LOG_DATA:severity::STRING AS severity,
    LOG_DATA:description::STRING AS description,
    LOG_DATA:total_cost::FLOAT AS total_cost
FROM RAW.MAINTENANCE_LOGS
ORDER BY LOG_TIMESTAMP DESC
LIMIT 10;
```

You should see maintenance events like oil changes, tire rotations, and engine diagnostics — all extracted from the VARIANT column with dot notation.

<!-- ------------------------ -->
## Stream Data

Let's bring real-time data into our Iceberg table. We'll use a Python script that simulates vehicle telemetry and inserts it directly into the **VEHICLE_TELEMETRY_STREAM** Iceberg table.

### Start the Streaming Script

Open a terminal and navigate to the assets directory:

```bash
cd get-started-snowflake-managed-iceberg-tables/assets

# Activate the Python environment created by setup.sh
source fleet_venv/bin/activate

# Start the streaming simulation (runs for 5 minutes by default)
python stream_telemetry.py
```

The script simulates a fleet of 50 vehicles, each emitting telemetry events containing speed, location, engine metrics, and driver behavior data. Each event is a JSON payload inserted into the `TELEMETRY_DATA` VARIANT column.

Here's an example of what each streaming event looks like:

```json
{
    "location": {"lat": 37.7749, "lon": -122.4194},
    "speed_mph": 65.3,
    "heading": 285,
    "engine": {
        "rpm": 3200,
        "temperature_f": 195,
        "oil_pressure_psi": 42,
        "fuel_level_pct": 67.5
    },
    "diagnostics": {
        "check_engine": false,
        "tire_pressure_warning": false,
        "codes": []
    },
    "driver_behavior": {
        "hard_acceleration_count": 2,
        "hard_brake_count": 1,
        "sharp_turn_count": 0
    }
}
```

### Watch Data Flow In

While the streaming script runs, open a SQL worksheet and query the table:

```sql
-- Check current count of streaming events
SELECT COUNT(*) AS event_count FROM RAW.VEHICLE_TELEMETRY_STREAM;

-- View the latest events, extracting fields from the VARIANT column
SELECT
    VEHICLE_ID,
    EVENT_TIMESTAMP,
    TELEMETRY_DATA:location:lat::FLOAT AS latitude,
    TELEMETRY_DATA:location:lon::FLOAT AS longitude,
    TELEMETRY_DATA:speed_mph::FLOAT AS speed_mph,
    TELEMETRY_DATA:engine:temperature_f::INT AS engine_temp,
    TELEMETRY_DATA:engine:fuel_level_pct::FLOAT AS fuel_level
FROM RAW.VEHICLE_TELEMETRY_STREAM
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 10;
```

The data is immediately queryable! Snowflake's dot notation on VARIANT columns makes it easy to extract nested fields from the JSON telemetry payload — no schema flattening required.

> **Tip**: You can stop the streaming script at any time with **Ctrl+C**. The data already streamed will remain in the table.

<!-- ------------------------ -->
## Transform with Dynamic Iceberg Tables

With data flowing into our raw tables, let's build a transformation pipeline using Dynamic Iceberg Tables. Dynamic Tables let you define transformations declaratively — you write a `SELECT` statement that describes the output, and Snowflake handles incremental refresh, dependency management, and scheduling automatically.

The setup script created two Dynamic Iceberg Tables. Let's explore them.

### Tier 1: Enriched Telemetry

This Dynamic Iceberg Table joins streaming telemetry with the vehicle registry to add driver and vehicle details:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE FLEET_DB.ANALYTICS.TELEMETRY_ENRICHED
    TARGET_LAG = '10 minutes'
    WAREHOUSE = FLEET_WH
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE'
AS
SELECT
    t.VEHICLE_ID,
    t.EVENT_TIMESTAMP,
    t.TELEMETRY_DATA:speed_mph::FLOAT AS speed_mph,
    t.TELEMETRY_DATA:engine:temperature_f::INT AS engine_temp_f,
    t.TELEMETRY_DATA:engine:fuel_level_pct::FLOAT AS fuel_level_pct,
    t.TELEMETRY_DATA:diagnostics:check_engine::BOOLEAN AS check_engine,
    CASE
        WHEN t.TELEMETRY_DATA:engine:temperature_f::INT > 230 THEN 'CRITICAL'
        WHEN t.TELEMETRY_DATA:engine:temperature_f::INT > 210 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS engine_health_status,
    v.MAKE,
    v.MODEL,
    v.DRIVER_NAME,
    v.FLEET_REGION
FROM FLEET_DB.RAW.VEHICLE_TELEMETRY_STREAM t
INNER JOIN FLEET_DB.RAW.VEHICLE_REGISTRY v
    ON t.VEHICLE_ID = v.VEHICLE_ID;
```

Here's what the code does:

- Extracts key fields from the VARIANT telemetry payload using dot notation
- Classifies engine health into NORMAL, WARNING, or CRITICAL based on temperature thresholds
- Joins with the vehicle registry to enrich each event with make, model, driver, and region
- Refreshes automatically within 10 minutes of source data changes thanks to `TARGET_LAG`

### Tier 2: Daily Fleet Summary

This Dynamic Iceberg Table aggregates the enriched telemetry into daily business metrics:

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE FLEET_DB.ANALYTICS.DAILY_FLEET_SUMMARY
    TARGET_LAG = 'DOWNSTREAM'
    WAREHOUSE = FLEET_WH
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE'
AS
SELECT
    DATE(EVENT_TIMESTAMP) AS summary_date,
    FLEET_REGION,
    COUNT(*) AS total_events,
    COUNT(DISTINCT VEHICLE_ID) AS active_vehicles,
    ROUND(AVG(speed_mph), 1) AS avg_speed_mph,
    ROUND(AVG(engine_temp_f), 1) AS avg_engine_temp_f,
    ROUND(AVG(fuel_level_pct), 1) AS avg_fuel_level_pct,
    SUM(CASE WHEN engine_health_status = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_events,
    SUM(CASE WHEN check_engine THEN 1 ELSE 0 END) AS check_engine_events
FROM FLEET_DB.ANALYTICS.TELEMETRY_ENRICHED
GROUP BY DATE(EVENT_TIMESTAMP), FLEET_REGION;
```

Note the `TARGET_LAG = 'DOWNSTREAM'`. This means the table refreshes only when a downstream consumer needs fresh data, creating an efficient pull-based refresh model.

### Trigger and Observe a Refresh

Let's manually trigger a refresh to see incremental processing in action:

```sql
-- Refresh the pipeline
ALTER DYNAMIC TABLE FLEET_DB.ANALYTICS.TELEMETRY_ENRICHED REFRESH;
ALTER DYNAMIC TABLE FLEET_DB.ANALYTICS.DAILY_FLEET_SUMMARY REFRESH;

-- Check refresh history — look at the refresh_action column
SELECT name, refresh_action, state, refresh_start_time
FROM TABLE(FLEET_DB.INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name IN ('TELEMETRY_ENRICHED', 'DAILY_FLEET_SUMMARY')
ORDER BY refresh_start_time DESC
LIMIT 10;
```

Look at the `refresh_action` column. After the initial full refresh, subsequent refreshes should show **INCREMENTAL**, meaning Snowflake processed only the new data — not the entire table.

### Query the Transformed Data

```sql
-- Enriched telemetry with vehicle details
SELECT
    VEHICLE_ID, MAKE, MODEL, DRIVER_NAME, FLEET_REGION,
    speed_mph, engine_temp_f, engine_health_status, EVENT_TIMESTAMP
FROM ANALYTICS.TELEMETRY_ENRICHED
WHERE engine_health_status != 'NORMAL'
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 10;

-- Daily fleet summary
SELECT *
FROM ANALYTICS.DAILY_FLEET_SUMMARY
ORDER BY summary_date DESC, FLEET_REGION
LIMIT 20;
```

You've now built a two-tier declarative pipeline on top of Snowflake-managed Iceberg tables. Snowflake handles all the incremental processing and dependency management for you.

<!-- ------------------------ -->
## Query with Snowflake Intelligence

Let's make this data accessible to business users who may not know SQL. We'll create a Cortex Agent that lets anyone ask natural language questions about the fleet data through Snowflake Intelligence.

### Create a Semantic View

First, we'll create a semantic view that describes our data in business terms. Rather than writing this manually, we'll use Snowflake's AI-powered UI to generate it.

1. In Snowsight, navigate to **AI & ML → Analyst** in the left navigation menu

2. Click **Create New: Semantic View** in the top right

3. In the dialog:
   - **Name**: Enter `fleet_semantic_view`
   - **Location**: Select database **FLEET_DB** and schema **ANALYTICS**

4. Click **Next** and skip the "Provide context" step

5. Select the following tables:
   - `ANALYTICS.TELEMETRY_ENRICHED`
   - `ANALYTICS.DAILY_FLEET_SUMMARY`
   - `RAW.VEHICLE_REGISTRY`
   - `RAW.SENSOR_READINGS`

6. Click **Next**, select all columns, and click **Create and Save**

Cortex Analyst will analyze the tables and automatically generate descriptions, logical names, and relationships. This takes a few moments.

### Create a Cortex Agent

Now let's create an agent that uses the semantic view:

1. Navigate to **AI & ML → Agents** in the left navigation menu

2. Click **Create agent**

3. In the dialog:
   - **Database**: Select **FLEET_DB**
   - **Schema**: Select **ANALYTICS**
   - **Agent object name**: Enter `fleet_agent`
   - **Display name**: Enter `Fleet Analytics Agent`

4. Click **Create**

5. Click the **Tools** tab, then click **Add+** next to **Cortex Analyst**

6. Select the semantic view we just created: **FLEET_DB.ANALYTICS.FLEET_SEMANTIC_VIEW**

7. Enter a name for the tool and click **Generate with Cortex** for the description

8. Click **Add**, then **Save**

### Ask Questions in Snowflake Intelligence

1. Navigate to **AI & ML → Agents** and click the **Snowflake Intelligence** tab

2. Click **Add existing agent**, then select the **fleet_agent** you just created

3. Once added, open **Snowflake Intelligence** from the left navigation menu and select the **Fleet Analytics Agent**

4. Try asking questions like:

- "What are the top 5 fleet regions by average speed?"
- "Show me vehicles with critical engine health events"
- "How many check engine events occurred per region today?"
- "Which drivers have the most telemetry events?"

The agent translates natural language into SQL, executes it against your Iceberg tables, and returns results with charts and explanations.

> **Note**: If you see a region availability error, enable cross-region inference:
> ```sql
> USE ROLE ACCOUNTADMIN;
> ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
> ```

<!-- ------------------------ -->
## Query from DuckDB

Here's where interoperability gets exciting. Because our tables are stored in the open Apache Iceberg format, external engines can read them directly through Snowflake's Horizon Catalog — without copying data, without ETL, without Snowflake compute.

DuckDB is a lightweight, in-process analytical database. It supports the Iceberg REST Catalog protocol, which means it can connect to Horizon Catalog and read our Snowflake-managed Iceberg tables.

### Install DuckDB

If you've deactivated the virtual environment, reactivate it first (`source fleet_venv/bin/activate`). Then install DuckDB:

```bash
pip install duckdb requests
```

### Run the DuckDB Interoperability Script

The companion script **duckdb_interop.py** connects DuckDB to your Snowflake-managed Iceberg tables via Horizon Catalog. It reads your connection details and PAT from **config.env**, so no extra configuration is needed:

```bash
python duckdb_interop.py
```

Here's what the script does:

- Installs and loads the DuckDB Iceberg extension
- Creates a bearer token secret using your Snowflake PAT
- Attaches to your Snowflake database through the Horizon Iceberg REST Catalog API
- The `ENDPOINT` points to Snowflake's built-in Polaris endpoint — no separate catalog server needed

The script runs several queries to demonstrate interoperability. Here's a look at what it executes:

```python
# List tables visible through Horizon Catalog
conn.execute("SHOW TABLES IN horizon.RAW").show()

# Query the vehicle registry
conn.execute("""
    SELECT VEHICLE_ID, MAKE, MODEL, YEAR, FLEET_REGION
    FROM horizon.RAW.VEHICLE_REGISTRY
    LIMIT 10
""").show()

# Aggregate sensor readings by vehicle
conn.execute("""
    SELECT
        VEHICLE_ID,
        COUNT(*) AS reading_count,
        ROUND(AVG(ENGINE_TEMP_F), 1) AS avg_engine_temp,
        ROUND(AVG(FUEL_CONSUMPTION_GPH), 2) AS avg_fuel_gph
    FROM horizon.RAW.SENSOR_READINGS
    GROUP BY VEHICLE_ID
    ORDER BY avg_fuel_gph DESC
    LIMIT 10
""").show()
```

DuckDB is reading directly from the Iceberg files managed by Snowflake. No data was copied. No Snowflake warehouse was used. The data is in an open format, and any engine that speaks Iceberg can read it.

> **Tip**: DuckDB reads VARIANT columns as strings. You can use DuckDB's `json_extract` function to parse nested fields from VARIANT data.

This is the core value proposition of Snowflake-managed Iceberg tables: your data lives in an open format managed by Snowflake, but it's accessible from any compatible engine.

<!-- ------------------------ -->
## Query from Apache Spark

For teams that rely on Apache Spark, the same Horizon Catalog endpoint works with Spark's Iceberg REST catalog integration. Spark 4.0+ adds native VARIANT support, so you get full access to the semi-structured telemetry data.

### Set Up the Spark Environment

The setup script created a Conda environment with Spark and all necessary dependencies. Deactivate the virtual environment if it's still active, then activate the Spark environment, install dependencies, and launch the notebook:

```bash
deactivate
conda activate fleet-spark
pip install pyspark==4.0.0 jupyter python-dotenv requests
jupyter notebook spark_iceberg_interop.ipynb
```

> **Note**: PySpark 4.0 requires **Java 17 or 21**. Java 25 is not compatible. Check with `java -version` before running the notebook.

### Connect Spark to Horizon Catalog

The pre-configured notebook creates a Spark session with the Horizon Catalog:

```python
from pyspark.sql import SparkSession

# Configuration
SNOWFLAKE_ACCOUNT_URL = "your-org-your-account"
SNOWFLAKE_PAT = "your-programmatic-access-token"
SNOWFLAKE_DATABASE = "FLEET_DB"
SNOWFLAKE_ROLE = "ACCOUNTADMIN"

ICEBERG_VERSION = "1.10.1"
SCALA_VERSION = "2.13"

spark = SparkSession.builder \
    .appName("Fleet Analytics - Iceberg Interop") \
    .master("local[*]") \
    .config("spark.driver.host", "127.0.0.1") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .config("spark.jars.packages",
            f"org.apache.iceberg:iceberg-spark-runtime-4.0_{SCALA_VERSION}:{ICEBERG_VERSION},"
            f"org.apache.iceberg:iceberg-aws-bundle:{ICEBERG_VERSION}") \
    .config("spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.horizon", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.horizon.type", "rest") \
    .config("spark.sql.catalog.horizon.uri",
            f"https://{SNOWFLAKE_ACCOUNT_URL}.snowflakecomputing.com/polaris/api/catalog") \
    .config("spark.sql.catalog.horizon.credential", SNOWFLAKE_PAT) \
    .config("spark.sql.catalog.horizon.warehouse", SNOWFLAKE_DATABASE) \
    .config("spark.sql.catalog.horizon.scope", f"session:role:{SNOWFLAKE_ROLE}") \
    .config("spark.sql.catalog.horizon.header.X-Iceberg-Access-Delegation",
            "vended-credentials") \
    .config("spark.sql.iceberg.vectorization.enabled", "false") \
    .getOrCreate()

print(f"Spark {spark.version} connected to Horizon Catalog!")
```

Here's what the code does:

- Creates a local Spark session with Iceberg extensions
- Configures the `horizon` catalog to use Snowflake's Iceberg REST API endpoint
- Uses vended credentials so Spark can access the underlying Iceberg files without direct cloud storage permissions
- The `scope` parameter ensures Spark uses your Snowflake role for access control

### List and Query Tables

```python
# Show all tables visible through Horizon
spark.sql("SHOW TABLES IN horizon.RAW").show(truncate=False)

# Query the vehicle registry
spark.sql("""
    SELECT VEHICLE_ID, MAKE, MODEL, YEAR, FLEET_REGION
    FROM horizon.RAW.VEHICLE_REGISTRY
    LIMIT 10
""").show()
```

### Query VARIANT Data with Spark 4.0

Spark 4.0 supports the Iceberg V3 VARIANT type natively. Use `variant_get()` to extract nested fields:

```python
# Extract nested fields from the VARIANT telemetry payload
df = spark.sql("""
    SELECT
        VEHICLE_ID,
        EVENT_TIMESTAMP,
        variant_get(TELEMETRY_DATA, '$.speed_mph', 'float') AS speed_mph,
        variant_get(TELEMETRY_DATA, '$.engine.temperature_f', 'int') AS engine_temp,
        variant_get(TELEMETRY_DATA, '$.location.lat', 'float') AS latitude,
        variant_get(TELEMETRY_DATA, '$.location.lon', 'float') AS longitude
    FROM horizon.RAW.VEHICLE_TELEMETRY_STREAM
    WHERE variant_get(TELEMETRY_DATA, '$.speed_mph', 'float') > 60
    LIMIT 10
""")
df.show()
```

Spark is reading the same Iceberg tables that Snowflake manages, including the semi-structured VARIANT data. No data movement, no ETL, no duplication.

### Dynamic Iceberg Tables Are Visible Too

Dynamic Iceberg Tables appear as regular Iceberg tables to external engines:

```python
# Query the Dynamic Iceberg Table
spark.sql("SHOW TABLES IN horizon.ANALYTICS").show(truncate=False)

spark.sql("""
    SELECT *
    FROM horizon.ANALYTICS.DAILY_FLEET_SUMMARY
    ORDER BY summary_date DESC
    LIMIT 10
""").show()
```

This is a powerful pattern: Snowflake handles the transformation pipeline (Dynamic Tables), and any engine can read the results.

<!-- ------------------------ -->
## Clean Up

Let's clean up your Snowflake account. Run the following in a SQL worksheet:

```sql
USE ROLE ACCOUNTADMIN;

-- Drop the database (removes all tables, dynamic tables, stages, etc.)
DROP DATABASE IF EXISTS FLEET_DB;

-- Drop the warehouse
DROP WAREHOUSE IF EXISTS FLEET_WH;
```

If you created a Cortex Agent, you can remove it from the **AI & ML → Agents** page in Snowsight before dropping the database.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You built a fleet analytics pipeline on Snowflake-managed Iceberg tables and proved that the same data is accessible from DuckDB and Apache Spark — without configuring cloud storage, without moving data, and without giving up Snowflake's governance and performance.

### What You Learned

- Creating Snowflake-managed Iceberg tables with `EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'` — no cloud bucket required
- Streaming semi-structured JSON data into VARIANT columns in Iceberg tables
- Batch-loading JSON files into Iceberg tables with `COPY INTO`
- Building incremental transformation pipelines with Dynamic Iceberg Tables
- Querying fleet data with natural language through a Cortex Agent in Snowflake Intelligence
- Reading Snowflake-managed Iceberg tables from DuckDB via Horizon Catalog
- Reading Snowflake-managed Iceberg tables from Apache Spark via Horizon Catalog, including VARIANT data with `variant_get()`

### Related Resources

- [Snowflake Storage for Apache Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-internal-storage)
- [Query Iceberg Tables with an External Engine through Horizon Catalog](https://docs.snowflake.com/en/user-guide/tables-iceberg-query-using-external-query-engine-snowflake-horizon)
- [Dynamic Iceberg Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-create-iceberg)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- [Snowpipe Streaming](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)

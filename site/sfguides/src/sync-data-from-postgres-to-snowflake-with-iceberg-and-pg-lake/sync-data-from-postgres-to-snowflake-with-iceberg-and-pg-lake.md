author: Elizabeth Christensen
id: sync-data-from-postgres-to-snowflake-with-iceberg-and-pg-lake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Learn how to sync data from Postgres to Snowflake using a shared Apache Iceberg table and the pg_lake extension
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Postgres

# Sync Data from Snowflake Postgres to Snowflake with Iceberg and pg_lake
<!-- ------------------------ -->

>**Note:
>pg_lake features are in preview and under rapid development. Some features may not be available.**<br>

If you're running an application on Snowflake Postgres, you probably have operational data that would be valuable for analytics in Snowflake. The [**pg_lake**](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-pg_lake) extension makes this easy — it lets you create Iceberg tables directly from Postgres using standard SQL (`CREATE TABLE ... USING iceberg`), and Snowflake can read those tables natively through a catalog integration. No ETL pipelines, no data movement tooling, no extra infrastructure.

In a typical pattern, your application writes to regular Postgres tables for fast transactional operations. You then use an Iceberg table managed by pg_lake along with [pg_incremental](https://github.com/CrunchyData/pg_incremental) to automatically sync data — both the initial backfill and ongoing new rows. Snowflake picks up changes through a catalog integration.

In this quickstart, you will set up an operational Postgres database, create an Iceberg table, automate a data sync to Iceberg and Snowflake, and query the results in Snowflake.

### What You Will Build
- A Snowflake Postgres instance with an operational sensor data table
- An Iceberg table managed by pg_lake
- An automated pipeline using pg_incremental that backfills existing data and syncs new rows
- A Snowflake catalog integration connected to the Postgres Iceberg catalog
- A queryable Iceberg table in Snowflake sourced from Postgres

### What You Will Learn
- How to set up an operational Postgres table and an Iceberg table using pg_lake
- How to use pg_incremental to backfill and continuously sync data with exactly-once processing
- How to connect Snowflake to Postgres-managed Iceberg tables
- How to query Iceberg data from Snowflake
- How to manually refresh and enable auto-refresh for Iceberg tables

### Prerequisites
- Access to a Snowflake account with Snowflake Postgres enabled
- A SQL client capable of connecting to Postgres (e.g., `psql`)

<!-- ------------------------ -->
## Create a Postgres Instance

Start by creating a new Snowflake Postgres instance. You will need the instance name in a later step when configuring the Snowflake catalog integration.

### Create the Instance
Create a new Snowflake Postgres instance from the Snowflake UI or SQL. If this is your first time, follow the [Getting Started with Snowflake Postgres](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-postgres/) guide for detailed instructions. Copy and save the **instance name** — you will need it when setting up the catalog integration in Snowflake. Keep your instance name handy — you will reference it in the Snowflake catalog integration step.

### Connect to the Instance
Connect to your Snowflake Postgres instance using `psql` or your preferred SQL client:

```bash
psql postgres://<user>:<password>@<instance-host>:5432/postgres
```

<!-- ------------------------ -->
## Set Up the Operational Database

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
## Set Up pg_lake and Create an Iceberg Table

Now that you have an active operational table, enable pg_lake and create an Iceberg table to hold a copy of the data for Snowflake analytics. The Iceberg table lives in cloud object storage and is managed by Postgres as the Iceberg catalog — Snowflake reads from it directly. You will populate it using an automated pipeline in the next step.

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

<!-- ------------------------ -->
## Automate Sync with pg_incremental

Rather than manually copying data, you can use pg_incremental to automatically sync rows on a schedule — both the initial backfill and ongoing new data. pg_incremental is built on pg_cron and provides exactly-once semantics — each time range is processed once and only once, so you will never get duplicates in the Iceberg table.

### Install Extensions

```sql
CREATE EXTENSION pg_cron;
CREATE EXTENSION pg_incremental;
```

### Create the Pipeline

Define a pipeline that copies rows based on `reading_time`. The `$1` and `$2` placeholders represent the start and end of each time interval that pg_incremental processes. Setting `start_time` to the minimum `reading_time` tells the pipeline to backfill all existing data first, then continue syncing new rows as they arrive.

```sql
SELECT incremental.create_time_interval_pipeline(
    pipeline_name      := 'sync_postgres_to_iceberg',
    time_interval      := '1 minute',
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

When the pipeline is created, it immediately processes all completed intervals from `start_time` to now — this is the initial backfill. After that, it runs every minute and processes only new intervals as they complete. Setting `source_table_name` ensures the pipeline waits for any in-flight writes to `sensor_readings` before processing, preventing data from being skipped.

You can set the `time_interval` to your preference (minutes, hours, days, etc.) depending on how frequently you want new data to sync.

### Verify the data copy to Iceberg
Confirm the pipeline added all existing data to the Iceberg tables. Both counts should show 5,000:

```sql
SELECT
    (SELECT count(*) FROM sensor_readings) AS heap_rows,
    (SELECT count(*) FROM sensor_readings_iceberg) AS iceberg_rows;
```

### Simulate New Data
Now insert 100 new rows with current timestamps to simulate real application writes arriving after the pipeline is running:

```sql
INSERT INTO sensor_readings (sensor_id, device_type, reading_time, temperature, humidity, battery_pct)
SELECT
    (random() * 50)::int AS sensor_id,
    (ARRAY['thermostat', 'weather_station', 'greenhouse', 'cold_storage', 'hvac'])[1 + (random() * 4)::int] AS device_type,
    now() AS reading_time,
    (random() * 40 + 5)::numeric(5,2) AS temperature,
    (random() * 60 + 20)::numeric(5,2) AS humidity,
    (random() * 80 + 20)::numeric(4,1) AS battery_pct
FROM generate_series(1, 100);
```

### Verify the Incremental Sync
Wait about two minutes for the pipeline to process the new interval, then check that the new rows have been picked up:

```sql
SELECT
    (SELECT count(*) FROM sensor_readings) AS heap_rows,
    (SELECT count(*) FROM sensor_readings_iceberg) AS iceberg_rows;
```

Both counts should show 5,100 (the original 5,000 plus the 100 new ones). From this point on, any new rows inserted into `sensor_readings` will automatically flow into the Iceberg table on the next pipeline run.


<!-- ------------------------ -->
## Connect Snowflake to Iceberg

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

With pg_lake, Postgres is the Iceberg catalog and Snowflake reads the Iceberg metadata through the catalog integration. This makes the table "externally managed" from Snowflake's perspective — Snowflake can query and refresh the data, but Postgres owns the table lifecycle.

Key points:
- You can always run a **manual refresh** to pull the latest data using `ALTER ICEBERG TABLE iot_sensors_from_postgres REFRESH;`.
- **Auto-refresh** (continuous polling) is available but off by default — you must explicitly enable it per table
- The polling frequency is controlled on the catalog integration via `REFRESH_INTERVAL_SECONDS` (default 30s)

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

### Test Auto-Refresh

Now you can add another 100 rows to Postgres, see the Iceberg row count rise, along with your Snowflake table row count.

In Postgres:
```sql
INSERT INTO sensor_readings (sensor_id, device_type, reading_time, temperature, humidity, battery_pct)
SELECT
    (random() * 50)::int AS sensor_id,
    (ARRAY['thermostat', 'weather_station', 'greenhouse', 'cold_storage', 'hvac'])[1 + (random() * 4)::int] AS device_type,
    now() AS reading_time,
    (random() * 40 + 5)::numeric(5,2) AS temperature,
    (random() * 60 + 20)::numeric(5,2) AS humidity,
    (random() * 80 + 20)::numeric(4,1) AS battery_pct
FROM generate_series(1, 100);
```

In Snowflake:
```sql
SELECT COUNT(*) FROM iot_sensors_from_postgres;
```

<!-- ------------------------ -->
## Conclusion and Resources

### Congratulations!
You have successfully synced data from an operational Postgres database to Snowflake using Iceberg tables, pg_lake, and pg_incremental — with no external ETL pipeline required.

### What You Learned
- How to set up an operational Postgres table and an Iceberg table using pg_lake
- How to use pg_incremental to backfill and continuously sync data with exactly-once processing
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
- [pg_lake GitHub Repository](https://github.com/Snowflake-Labs/pg_lake)
- [pg_lake for Snowflake Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-pg_lake)

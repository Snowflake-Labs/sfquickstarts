-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- 01_create_tables.sql -- Zero-Ops Iceberg Table Creation (Module 1)
-- =============================================================================
-- THE KEY TAKEAWAY: 1 SQL statement, no customer-managed bucket, no IAM config,
-- no lifecycle policy, no compaction schedule. Snowflake Storage for Iceberg
-- provisions and manages all storage internally as open Parquet + Iceberg metadata.
-- This script uses explicit internal-storage syntax on every Iceberg table:
--   CATALOG = SNOWFLAKE
--   EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
--
-- Two tables, two governance stories (see 03_horizon_governance.sql):
--   yellow_trips  -> Path A: no policy, Databricks vended-creds direct read
--   green_trips   -> Path B: masking + RLS, Databricks routed through SF compute
--
-- TIMESTAMP PRECISION NOTE:
--   This database uses ICEBERG_VERSION_DEFAULT = 3 (set in 00_setup.sql).
--   Under Iceberg V3, TIMESTAMP_NTZ without an explicit scale defaults to
--   nanosecond precision (timestamp_ns in Iceberg metadata). Apache Spark's
--   iceberg-spark-runtime 1.10.x does NOT support timestamp_ns reads.
--
--   TLC Parquet files store datetime columns as INT96 timestamps (legacy
--   encoding). When read through a stage, these require an intermediate
--   ::STRING cast for safe parsing via TO_TIMESTAMP_NTZ(). The final
--   ::TIMESTAMP_NTZ(6) forces microsecond precision, which maps to the
--   Iceberg V2 "timestamp" type that all engines support.
--
--   green_trips_nano is a small proof table (1000 rows) that you will use
--   to observe the Spark incompatibility firsthand in Databricks.
-- =============================================================================

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- yellow_trips: Path A governance table
--   No masking or RLS policies will be applied to this table.
--   Databricks will receive vended credentials and read Parquet directly
--   from Snowflake-managed storage -- zero Snowflake compute consumed.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE yellow_trips
    CATALOG = SNOWFLAKE
    EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
    AS SELECT
        $1:VendorID::INT                      AS VendorID,
        TO_TIMESTAMP_NTZ($1:tpep_pickup_datetime::STRING)::TIMESTAMP_NTZ(6) AS tpep_pickup_datetime, -- Explicit microsecond precision for Spark 4.0/Iceberg 1.10.x compatibility
        TO_TIMESTAMP_NTZ($1:tpep_dropoff_datetime::STRING)::TIMESTAMP_NTZ(6) AS tpep_dropoff_datetime,
        $1:passenger_count::INT               AS passenger_count,
        $1:trip_distance::FLOAT               AS trip_distance,
        $1:RatecodeID::INT                    AS RatecodeID,
        $1:store_and_fwd_flag::STRING         AS store_and_fwd_flag,
        $1:PULocationID::INT                  AS PULocationID,
        $1:DOLocationID::INT                  AS DOLocationID,
        $1:payment_type::INT                  AS payment_type,
        $1:fare_amount::FLOAT                 AS fare_amount,
        $1:extra::FLOAT                       AS extra,
        $1:mta_tax::FLOAT                     AS mta_tax,
        $1:tip_amount::FLOAT                  AS tip_amount,
        $1:tolls_amount::FLOAT                AS tolls_amount,
        $1:improvement_surcharge::FLOAT       AS improvement_surcharge,
        $1:total_amount::FLOAT                AS total_amount,
        $1:congestion_surcharge::FLOAT        AS congestion_surcharge,
        $1:Airport_fee::FLOAT                 AS Airport_fee,
        $1:cbd_congestion_fee::FLOAT          AS cbd_congestion_fee
    FROM @TLC_STAGE/yellow/ (FILE_FORMAT => 'parquet_ff');

-- Expected: This CTAS may take a few minutes.
SELECT COUNT(*) AS yellow_row_count FROM yellow_trips;

-- ---------------------------------------------------------------------------
-- green_trips: Path B governance table
--   Masking policy (financial columns) + RLS (borough-based) will be applied
--   in 03_horizon_governance.sql. Databricks queries will be routed through
--   Snowflake compute -- policies enforced server-side.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE ICEBERG TABLE green_trips
    CATALOG = SNOWFLAKE
    EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
    AS SELECT
        $1:VendorID::INT                      AS VendorID,
        TO_TIMESTAMP_NTZ($1:lpep_pickup_datetime::STRING)::TIMESTAMP_NTZ(6) AS lpep_pickup_datetime, -- Explicit microsecond precision for Spark 4.0/Iceberg 1.10.x compatibility
        TO_TIMESTAMP_NTZ($1:lpep_dropoff_datetime::STRING)::TIMESTAMP_NTZ(6) AS lpep_dropoff_datetime,
        $1:passenger_count::INT               AS passenger_count,
        $1:trip_distance::FLOAT               AS trip_distance,
        $1:RatecodeID::INT                    AS RatecodeID,
        $1:store_and_fwd_flag::STRING         AS store_and_fwd_flag,
        $1:PULocationID::INT                  AS PULocationID,
        $1:DOLocationID::INT                  AS DOLocationID,
        $1:payment_type::INT                  AS payment_type,
        $1:fare_amount::FLOAT                 AS fare_amount,
        $1:extra::FLOAT                       AS extra,
        $1:mta_tax::FLOAT                     AS mta_tax,
        $1:tip_amount::FLOAT                  AS tip_amount,
        $1:tolls_amount::FLOAT                AS tolls_amount,
        $1:improvement_surcharge::FLOAT       AS improvement_surcharge,
        $1:total_amount::FLOAT                AS total_amount,
        $1:congestion_surcharge::FLOAT        AS congestion_surcharge,
        $1:trip_type::INT                     AS trip_type,
        $1:ehail_fee::FLOAT                   AS ehail_fee
    FROM @TLC_STAGE/green/ (FILE_FORMAT => 'parquet_ff');

-- Count Check
SELECT COUNT(*) AS green_row_count FROM green_trips;

-- ---------------------------------------------------------------------------
-- green_trips_nano: Nanosecond timestamp proof table
--   Identical schema to green_trips but with TIMESTAMP_NTZ(9) — nanosecond
--   precision. This maps to Iceberg V3 "timestamp_ns" in metadata.
--   Snowflake reads this table perfectly. Spark 1.10.x CANNOT — it rejects
--   the timestamp_ns type at schema load time.
--   No governance policies — this is a pure timestamp compatibility test.
--   Limited to 1000 rows for fast creation.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE green_trips_nano
    CATALOG = SNOWFLAKE
    EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
    AS SELECT
        $1:VendorID::INT                      AS VendorID,
        TO_TIMESTAMP_NTZ($1:lpep_pickup_datetime::STRING)::TIMESTAMP_NTZ(9) AS lpep_pickup_datetime,
        TO_TIMESTAMP_NTZ($1:lpep_dropoff_datetime::STRING)::TIMESTAMP_NTZ(9) AS lpep_dropoff_datetime,
        $1:passenger_count::INT               AS passenger_count,
        $1:trip_distance::FLOAT               AS trip_distance,
        $1:PULocationID::INT                  AS PULocationID,
        $1:DOLocationID::INT                  AS DOLocationID,
        $1:fare_amount::FLOAT                 AS fare_amount,
        $1:tip_amount::FLOAT                  AS tip_amount,
        $1:total_amount::FLOAT                AS total_amount
    FROM @TLC_STAGE/green/ (FILE_FORMAT => 'parquet_ff')
    LIMIT 1000;

SELECT COUNT(*) AS green_nano_row_count FROM green_trips_nano;

SELECT SYSTEM$GET_ICEBERG_TABLE_INFORMATION('green_trips_nano') AS nano_metadata;

SELECT * FROM green_trips_nano LIMIT 5;

-- ---------------------------------------------------------------------------
-- zone_lookup: dimension table (regular Snowflake table, not Iceberg)
--   Standard Snowflake table used as a dimension for borough lookups.
--   Referenced by the row access policy in 03_horizon_governance.sql to
--   resolve PULocationID -> Borough for borough-based row filtering.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE zone_lookup (
    LocationID   INT,
    Borough      VARCHAR,
    Zone         VARCHAR,
    service_zone VARCHAR
);

COPY INTO zone_lookup
FROM @TLC_STAGE/lookup/
FILE_FORMAT = (FORMAT_NAME = 'csv_ff');

SELECT COUNT(*) AS zone_count FROM zone_lookup;

-- ---------------------------------------------------------------------------
-- Verify: both tables are Iceberg V3 (FORMAT_VERSION = 3)
--   metadataLocation will point to Snowflake-managed internal storage.
--   This is NOT the customer's S3 bucket. Snowflake owns and manages it.
-- ---------------------------------------------------------------------------
-- Confirm FORMAT_VERSION=3 and metadataLocation points to SF-managed storage (not a customer bucket)

SELECT SYSTEM$GET_ICEBERG_TABLE_INFORMATION('yellow_trips') AS yellow_metadata;

-- Same check for green_trips: expect FORMAT_VERSION=3 and SF-managed metadataLocation
SELECT SYSTEM$GET_ICEBERG_TABLE_INFORMATION('green_trips')  AS green_metadata;

SHOW ICEBERG TABLES IN SCHEMA ICEBERG_DEMO.PUBLIC;

-- ---------------------------------------------------------------------------
-- Summary row counts
--   Validation query: confirm all three tables loaded successfully.
--   Run this after CTAS + COPY to verify row counts before proceeding to
--   Module 2 (02_ssv2_streaming_setup.sql).
-- ---------------------------------------------------------------------------
SELECT 'yellow_trips' AS table_name, COUNT(*) AS row_count FROM ICEBERG_DEMO.PUBLIC.yellow_trips
UNION ALL
SELECT 'green_trips',  COUNT(*) FROM ICEBERG_DEMO.PUBLIC.green_trips
UNION ALL
SELECT 'zone_lookup',  COUNT(*) FROM ICEBERG_DEMO.PUBLIC.zone_lookup;


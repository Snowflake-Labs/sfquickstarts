-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- teardown_full.sql -- Full Data and Governance Reset
-- =============================================================================
-- Drops all quickstart tables, pipes, policies, and tags. Preserves the database,
-- warehouse, roles, external stage, and file formats (created by 00_setup.sql with
-- IF NOT EXISTS / OR REPLACE, so they are safe to re-run).
--
-- After running this script, rebuild from Module 1:
--   1. 01_create_tables.sql    (yellow_trips, green_trips, green_trips_nano, zone_lookup)
--   2. 02_ssv2_streaming_setup.sql (nyc_weather_ssv2, pipe)
--   3. Run Java SSV2 ingest (SKIP_ARCHIVE=false, LIVE_MODE=false)
--   4. 03_horizon_governance.sql (policies, tags, grants)
-- =============================================================================

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- Governance objects (must detach before dropping tables)
-- ---------------------------------------------------------------------------
ALTER ICEBERG TABLE IF EXISTS green_trips
    DROP ROW ACCESS POLICY ICEBERG_DEMO.PUBLIC.borough_rls;

ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN fare_amount  UNSET MASKING POLICY;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN tip_amount   UNSET MASKING POLICY;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN total_amount UNSET MASKING POLICY;

ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN fare_amount  UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN tip_amount   UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN total_amount UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;

DROP MASKING POLICY IF EXISTS ICEBERG_DEMO.PUBLIC.financial_mask;
DROP ROW ACCESS POLICY IF EXISTS ICEBERG_DEMO.PUBLIC.borough_rls;
DROP TAG IF EXISTS ICEBERG_DEMO.PUBLIC.data_sensitivity;

-- ---------------------------------------------------------------------------
-- Pipe (must drop before the table it targets)
-- ---------------------------------------------------------------------------
DROP PIPE IF EXISTS nyc_weather_ssv2_pipe;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------
DROP ICEBERG TABLE IF EXISTS nyc_weather_ssv2;
DROP ICEBERG TABLE IF EXISTS green_trips_nano;
DROP ICEBERG TABLE IF EXISTS yellow_trips;
DROP ICEBERG TABLE IF EXISTS green_trips;
DROP TABLE IF EXISTS zone_lookup;

-- ---------------------------------------------------------------------------
-- Revoke grants
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;

REVOKE SELECT ON ALL TABLES IN SCHEMA ICEBERG_DEMO.PUBLIC FROM ROLE DEMO_DBX_READER;
REVOKE SELECT ON ALL ICEBERG TABLES IN SCHEMA ICEBERG_DEMO.PUBLIC FROM ROLE DEMO_DBX_READER;

SELECT 'Full teardown complete. Re-run from Module 1 (01_create_tables.sql).' AS status;

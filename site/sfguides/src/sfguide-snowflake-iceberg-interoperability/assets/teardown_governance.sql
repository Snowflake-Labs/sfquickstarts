-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- teardown_governance.sql -- Remove Governance Objects Only
-- =============================================================================
-- Lightweight teardown: removes all policies, tags, and grants applied by
-- 03_horizon_governance.sql. Tables and data are NOT touched.
--
-- Use this when you need to re-run Module 3 (03_horizon_governance.sql) without
-- rebuilding the 40M+ row Iceberg tables.
--
-- After running this script, re-run Module 3 (03_horizon_governance.sql) to reapply
-- policies and grants.
-- =============================================================================

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- Remove row access policy from green_trips
-- ---------------------------------------------------------------------------
ALTER ICEBERG TABLE IF EXISTS green_trips
    DROP ROW ACCESS POLICY ICEBERG_DEMO.PUBLIC.borough_rls;

-- ---------------------------------------------------------------------------
-- Remove masking policies from green_trips financial columns
-- ---------------------------------------------------------------------------
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN fare_amount  UNSET MASKING POLICY;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN tip_amount   UNSET MASKING POLICY;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN total_amount UNSET MASKING POLICY;

-- ---------------------------------------------------------------------------
-- Remove sensitivity tags from green_trips financial columns
-- ---------------------------------------------------------------------------
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN fare_amount  UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN tip_amount   UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;
ALTER ICEBERG TABLE IF EXISTS green_trips ALTER COLUMN total_amount UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;

-- ---------------------------------------------------------------------------
-- Drop policy and tag objects
-- ---------------------------------------------------------------------------
DROP MASKING POLICY IF EXISTS ICEBERG_DEMO.PUBLIC.financial_mask;
DROP ROW ACCESS POLICY IF EXISTS ICEBERG_DEMO.PUBLIC.borough_rls;
DROP TAG IF EXISTS ICEBERG_DEMO.PUBLIC.data_sensitivity;

-- ---------------------------------------------------------------------------
-- Revoke Databricks reader grants (re-applied by Module 3)
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;

REVOKE SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.yellow_trips FROM ROLE DEMO_DBX_READER;
REVOKE SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.green_trips  FROM ROLE DEMO_DBX_READER;
REVOKE SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2 FROM ROLE DEMO_DBX_READER;
REVOKE SELECT ON TABLE ICEBERG_DEMO.PUBLIC.zone_lookup FROM ROLE DEMO_DBX_READER;

SELECT 'Governance teardown complete. Tables and data untouched. Re-run Module 3 to reapply.' AS status;

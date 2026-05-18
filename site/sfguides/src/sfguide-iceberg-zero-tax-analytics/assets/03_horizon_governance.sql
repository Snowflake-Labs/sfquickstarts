-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- 03_horizon_governance.sql -- Horizon Catalog: Path A and Path B (Module 3)
-- =============================================================================
-- Demonstrates the two Horizon governance execution paths for external engines.
-- You will set up policies on one table and leave another policy-free, then
-- observe different behavior when Databricks reads each table.
--
--   PATH A (yellow_trips): No masking/RLS policy attached.
--     Horizon vends temporary STS credentials to Databricks.
--     Databricks reads Parquet files DIRECTLY from Snowflake-managed storage.
--     Zero Snowflake warehouse compute consumed.
--     Verify: check SF credit usage before and after Databricks reads.
--
--   PATH B (green_trips): Masking + RLS policies attached.
--     Snowflake detects the active policy on the table.
--     Databricks query is ROUTED THROUGH Snowflake compute.
--     Policy enforced server-side. Databricks receives masked results.
--     Zero storage copies -- governance travels with the catalog, not the data.
--
-- These paths are mutually exclusive per query. Same Horizon IRC endpoint.
-- Same Databricks cluster. Different outcome based on policy attachment only.
-- =============================================================================

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- PERSONALIZATION -- set your Snowflake username before running anything
-- ---------------------------------------------------------------------------
-- Must match the username used in 00_setup.sql.
SET MY_USER = '<YOUR_SNOWFLAKE_USERNAME>';

-- ---------------------------------------------------------------------------
-- SECTION 1: Confirm PATH A is clean (yellow_trips has NO policies)
-- ---------------------------------------------------------------------------
-- Why verify this? yellow_trips is our Path A table. For Path A to work,
-- it MUST have zero policies attached. When Horizon sees no policies, it
-- vends short-lived STS credentials so Databricks reads Parquet files
-- directly from Snowflake-managed storage -- zero Snowflake warehouse
-- compute is consumed. If any policy were attached, Horizon would
-- automatically route the query through Snowflake compute instead.
-- This query establishes the baseline: yellow_trips is policy-free.
SELECT *
FROM TABLE(INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME    => 'ICEBERG_DEMO.PUBLIC.yellow_trips',
    REF_ENTITY_DOMAIN  => 'TABLE'
));
-- Expected: 0 rows. No policies attached. This is Path A.

-- ---------------------------------------------------------------------------
-- SECTION 2: Create governance objects for PATH B
-- ---------------------------------------------------------------------------

-- Object tags: classify columns by sensitivity BEFORE attaching policies.
-- Best practice: "classify first, protect second." Tags label columns by
-- their sensitivity category (FINANCIAL, PII, etc.) so auditors and
-- governance dashboards can see what is sensitive at a glance. Masking
-- and RLS policies are then layered on top of the tagged columns.
CREATE TAG IF NOT EXISTS ICEBERG_DEMO.PUBLIC.data_sensitivity
    ALLOWED_VALUES 'FINANCIAL', 'PII';

-- Defensive: remove existing tags before re-applying (safe if not currently set)
ALTER ICEBERG TABLE green_trips ALTER COLUMN fare_amount  UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;
ALTER ICEBERG TABLE green_trips ALTER COLUMN tip_amount   UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;
ALTER ICEBERG TABLE green_trips ALTER COLUMN total_amount UNSET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity;

ALTER ICEBERG TABLE green_trips ALTER COLUMN fare_amount  SET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity = 'FINANCIAL';
ALTER ICEBERG TABLE green_trips ALTER COLUMN tip_amount   SET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity = 'FINANCIAL';
ALTER ICEBERG TABLE green_trips ALTER COLUMN total_amount SET TAG ICEBERG_DEMO.PUBLIC.data_sensitivity = 'FINANCIAL';

-- Column masking policy: financial columns.
-- Policy logic: DEMO_ADMIN (the admin role) sees the real financial
-- values. All other roles -- including DEMO_DBX_READER, which is the
-- role used by the Databricks SparkSession -- receive -1.0 as a sentinel.
-- When you read green_trips from Databricks in Module 4, you will see
-- -1.0 for financial columns, proving the masking policy is enforced.
CREATE OR REPLACE MASKING POLICY ICEBERG_DEMO.PUBLIC.financial_mask
    AS (val FLOAT)
    RETURNS FLOAT ->
    CASE
        WHEN CURRENT_ROLE() IN ('DEMO_ADMIN') THEN val
        ELSE -1.0
    END;

-- Defensive: remove existing masking policies before re-applying
ALTER ICEBERG TABLE green_trips ALTER COLUMN fare_amount  UNSET MASKING POLICY;
ALTER ICEBERG TABLE green_trips ALTER COLUMN tip_amount   UNSET MASKING POLICY;
ALTER ICEBERG TABLE green_trips ALTER COLUMN total_amount UNSET MASKING POLICY;

ALTER ICEBERG TABLE green_trips ALTER COLUMN fare_amount  SET MASKING POLICY ICEBERG_DEMO.PUBLIC.financial_mask;
ALTER ICEBERG TABLE green_trips ALTER COLUMN tip_amount   SET MASKING POLICY ICEBERG_DEMO.PUBLIC.financial_mask;
ALTER ICEBERG TABLE green_trips ALTER COLUMN total_amount SET MASKING POLICY ICEBERG_DEMO.PUBLIC.financial_mask;

-- Row access policy: controls which rows each role can see.
-- DEMO_ADMIN and DEMO_ANALYST see all rows (TRUE). DEMO_DBX_READER
-- (the role used by the Databricks cluster) only sees rows where the
-- pickup location is in Manhattan. This is enforced via a subquery join
-- to the zone_lookup table that maps LocationID to Borough. Any role
-- This demonstrates
-- that RLS policies are enforced server-side even for external engines.
-- When you read green_trips from Databricks, you will see only Manhattan rows.
CREATE OR REPLACE ROW ACCESS POLICY ICEBERG_DEMO.PUBLIC.borough_rls
    AS (pickup_location_id INT)
    RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() = 'DEMO_ADMIN'      THEN TRUE
        WHEN CURRENT_ROLE() = 'DEMO_ANALYST'    THEN TRUE
        WHEN CURRENT_ROLE() = 'DEMO_DBX_READER' THEN
            EXISTS (SELECT 1 FROM ICEBERG_DEMO.PUBLIC.zone_lookup z
                    WHERE z.LocationID = pickup_location_id AND z.Borough = 'Manhattan')
        ELSE FALSE
    END;

-- Defensive: remove existing row access policy before re-adding
-- ALTER ICEBERG TABLE green_trips DROP ROW ACCESS POLICY ICEBERG_DEMO.PUBLIC.borough_rls;

ALTER ICEBERG TABLE green_trips
    ADD ROW ACCESS POLICY ICEBERG_DEMO.PUBLIC.borough_rls ON (PULocationID);

-- ---------------------------------------------------------------------------
-- SECTION 3: Verify PATH B policies are attached to green_trips only
-- ---------------------------------------------------------------------------
SELECT
    POLICY_NAME,
    POLICY_KIND,
    REF_COLUMN_NAME
FROM TABLE(INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME    => 'ICEBERG_DEMO.PUBLIC.green_trips',
    REF_ENTITY_DOMAIN  => 'TABLE'
));
-- Expected: 3 masking policy rows (fare, tip, total) + 1 RLS row

-- yellow_trips still has zero policies (Path A)
SELECT *
FROM TABLE(INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME    => 'ICEBERG_DEMO.PUBLIC.yellow_trips',
    REF_ENTITY_DOMAIN  => 'TABLE'
));
-- Expected: 0 rows

-- ---------------------------------------------------------------------------
-- SECTION 4: Grant SELECT to Databricks reader role
-- ---------------------------------------------------------------------------
-- These grants give DEMO_DBX_READER SELECT access to all quickstart tables.
-- DEMO_DBX_READER is the role that the Databricks cluster authenticates
-- with via a Programmatic Access Token (PAT) set in the SparkSession
-- config. Because the role has masking and RLS policies on green_trips,
-- Databricks will receive masked/filtered results for that table.
USE ROLE ACCOUNTADMIN;

GRANT SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.yellow_trips TO ROLE DEMO_DBX_READER;
GRANT SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.green_trips  TO ROLE DEMO_DBX_READER;
GRANT SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2 TO ROLE DEMO_DBX_READER;
GRANT SELECT ON ICEBERG TABLE ICEBERG_DEMO.PUBLIC.green_trips_nano TO ROLE DEMO_DBX_READER;
GRANT SELECT ON TABLE ICEBERG_DEMO.PUBLIC.zone_lookup           TO ROLE DEMO_DBX_READER;

-- ---------------------------------------------------------------------------
-- SECTION 5: IRC Endpoint + PAT generation
-- ---------------------------------------------------------------------------
-- Horizon IRC (Iceberg REST Catalog) is Snowflake's built-in catalog
-- endpoint that implements the open-source Apache Iceberg REST Catalog
-- specification. External engines such as Databricks, Apache Spark, and
-- Trino connect to this endpoint to discover and read Snowflake-managed
-- Iceberg tables without needing a Snowflake driver or JDBC connection.
USE ROLE ACCOUNTADMIN;

-- Get account identifier (needed for Databricks SparkSession config)
SELECT
    CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS account_identifier,
    'https://' || CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME()
        || '.snowflakecomputing.com/polaris/api/catalog' AS horizon_irc_endpoint;

-- Generate a Programmatic Access Token (PAT) for Databricks.
-- The PAT is scoped to the DEMO_DBX_READER role with a 1-day expiry for
-- security. This token is used as the OAuth/bearer credential in the
-- Databricks SparkSession config so the cluster authenticates to the
-- Horizon IRC endpoint as DEMO_DBX_READER (and inherits its policies).
-- Option A (Snowsight): User Menu > My Profile > Programmatic Access Tokens > Generate
-- Option B (SQL):
--
--   ALTER USER IDENTIFIER($MY_USER)
--     ADD PROGRAMMATIC ACCESS TOKEN quickstart_dbx_pat
--     DAYS_TO_EXPIRY = 1
--     ROLE_RESTRICTION = 'DEMO_DBX_READER'
--     COMMENT = 'Quickstart Databricks IRC token';
-- --
-- Copy the PAT value -- it is shown only once.

-- ---------------------------------------------------------------------------
-- SECTION 6: Credit usage comparison (Path A vs Path B proof)
-- ---------------------------------------------------------------------------
USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;

-- Run this query BEFORE and AFTER your Databricks reads to compare credits.
-- Path A (yellow_trips): no policies attached, so Horizon vends storage
--   credentials and Databricks reads Parquet directly. This path will
--   show ZERO additional warehouse credits in the metering history.
-- Path B (green_trips): masking + RLS policies attached, so the query is
--   routed through Snowflake compute for server-side enforcement. This
--   path will show credits consumed by the warehouse that executed the
--   policy-enforced query on behalf of Databricks.

SELECT
    WAREHOUSE_NAME,
    ROUND(SUM(CREDITS_USED), 4)                AS credits_used,
    ROUND(SUM(CREDITS_USED_CLOUD_SERVICES), 6) AS cloud_svc_credits
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START => DATEADD('minute', -15, CURRENT_TIMESTAMP()),
    DATE_RANGE_END   => CURRENT_TIMESTAMP()
))
WHERE WAREHOUSE_NAME = 'DEMO_WH'
GROUP BY WAREHOUSE_NAME
ORDER BY credits_used DESC;


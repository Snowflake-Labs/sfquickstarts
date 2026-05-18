-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- 00_setup.sql -- Environment Setup (Module 0)
-- =============================================================================
-- This script sets up all environment prerequisites so the remaining modules
-- can run cleanly. Run each statement sequentially in Snowsight or your
-- preferred SQL client.
--
-- Run as ACCOUNTADMIN to set up your environment.
-- Snowflake Storage for Iceberg (SSI) only.
-- Iceberg tables in this quickstart use explicit Snowflake-managed storage:
--   CATALOG = SNOWFLAKE
--   EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
-- This script provisions roles, warehouse, database, external stage
-- (Snowflake S3 bucket), network access, and file formats.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 0. PERSONALIZATION -- set your Snowflake username before running anything
-- ---------------------------------------------------------------------------
-- Replace with your own Snowflake username.
-- This value is used for role grants, RSA key registration, and PAT creation.
SET MY_USER = '<YOUR_SNOWFLAKE_USERNAME>';

-- ---------------------------------------------------------------------------
-- 1. Warehouse
-- ---------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS DEMO_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND   = 120
    AUTO_RESUME    = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Quickstart -- Snowflake + Iceberg Interoperability';

CREATE WAREHOUSE IF NOT EXISTS DEMO_WH_2
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND   = 120
    AUTO_RESUME    = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Quickstart -- Snowflake + Iceberg Interoperability';

-- ---------------------------------------------------------------------------
-- 2. Database + Schema
-- ---------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS ICEBERG_DEMO
    COMMENT = 'Quickstart -- Snowflake Storage for Iceberg';

CREATE SCHEMA IF NOT EXISTS ICEBERG_DEMO.PUBLIC;

-- ---------------------------------------------------------------------------
-- 3. Roles
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS DEMO_ADMIN
    COMMENT = 'Full access -- admin role for this quickstart';

CREATE ROLE IF NOT EXISTS DEMO_ANALYST
    COMMENT = 'Analyst role -- sees masked financial columns';

CREATE ROLE IF NOT EXISTS DEMO_DBX_READER
    COMMENT = 'Read-only role for Databricks IRC access';

-- ---------------------------------------------------------------------------
-- 4. Role Hierarchy
-- ---------------------------------------------------------------------------
GRANT ROLE DEMO_ADMIN      TO ROLE ACCOUNTADMIN;
GRANT ROLE DEMO_ANALYST    TO ROLE ACCOUNTADMIN;
GRANT ROLE DEMO_DBX_READER TO ROLE ACCOUNTADMIN;

-- Grant DEMO_DBX_READER directly to your user.
-- Required so the PAT you create in 03_horizon_governance.sql can use ROLE_RESTRICTION = 'DEMO_DBX_READER'.
GRANT ROLE DEMO_DBX_READER TO USER IDENTIFIER($MY_USER);

-- ---------------------------------------------------------------------------
-- 4b. RSA Key Pair Setup
-- ---------------------------------------------------------------------------
-- This quickstart uses TWO authentication methods. Here is why:
--
--   Auth Method     | Used By                          | Why
--   --------------- | -------------------------------- | ----------------------------------
--   PAT (token)     | Horizon IRC catalog credential   | Iceberg REST Catalog spec uses
--                   | (Databricks SparkSession config) | OAuth bearer tokens. PAT works.
--   RSA key-pair    | Spark Connector JDBC fallback    | Path B tables (masking/RLS) route
--                   | (Databricks spark.snowflake.*)   | through JDBC. JDBC does NOT accept
--                   |                                  | PATs -- key-pair auth is required.
--   RSA key-pair    | Java SSV2 ingest app             | Snowpipe Streaming SDK authenticates
--                   | (ssv2-streaming/profile.json)    | via key-pair, not PAT.
--
-- In short: PAT handles catalog-level access (discovering tables).
--           Key-pair handles compute-level access (JDBC queries + streaming).
--
-- You will create the PAT later in Module 3 (03_horizon_governance.sql).
-- The RSA key pair is set up here because it must be registered on your
-- Snowflake user BEFORE any downstream modules can use it.
--
-- Step 1 -- Generate key pair locally (run in terminal, not here):
--   openssl genrsa 2048 | openssl pkcs8 -topk8 -nocrypt -out rsa_key.p8
--   openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
--   Store both files securely on your local machine (do NOT commit to git).
--
-- Step 2 -- Register the public key on your Snowflake user (run this SQL):
--   Copy the single-line content of rsa_key.pub (strip BEGIN/END headers)
--   then paste it as the RSA_PUBLIC_KEY value below:
ALTER USER IDENTIFIER($MY_USER)
    SET RSA_PUBLIC_KEY = '<paste single-line public key here>';
--
-- Step 3 -- The private key (rsa_key.p8, headers stripped) goes into:
--   a) ssv2-streaming/profile.json (for Java SSV2 ingest)
--   b) cell 1 of scripts/04_databricks_read.ipynb (for Databricks)
--   Command to extract it:
--     grep -v "BEGIN\|END" rsa_key.p8 | tr -d '\n'

-- ---------------------------------------------------------------------------
-- 5. Warehouse Grants
-- ---------------------------------------------------------------------------
GRANT USAGE ON WAREHOUSE DEMO_WH TO ROLE DEMO_ADMIN;
GRANT USAGE ON WAREHOUSE DEMO_WH TO ROLE DEMO_ANALYST;
GRANT USAGE ON WAREHOUSE DEMO_WH TO ROLE DEMO_DBX_READER;

-- ---------------------------------------------------------------------------
-- 6. Database + Schema Grants
-- ---------------------------------------------------------------------------
GRANT OWNERSHIP ON DATABASE ICEBERG_DEMO TO ROLE DEMO_ADMIN COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA ICEBERG_DEMO.PUBLIC TO ROLE DEMO_ADMIN COPY CURRENT GRANTS;

GRANT USAGE ON DATABASE ICEBERG_DEMO TO ROLE DEMO_ANALYST;
GRANT USAGE ON SCHEMA ICEBERG_DEMO.PUBLIC TO ROLE DEMO_ANALYST;

GRANT USAGE ON DATABASE ICEBERG_DEMO TO ROLE DEMO_DBX_READER;
GRANT USAGE ON SCHEMA ICEBERG_DEMO.PUBLIC TO ROLE DEMO_DBX_READER;

-- ---------------------------------------------------------------------------

-- 7. External Stage for TLC Parquet Files (DevRel S3 Bucket)
--    Original source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
--
--    TLC Parquet files are hosted in the Snowflake DevRel public S3 bucket
--    (sfquickstarts). Because the bucket is public, no storage integration
--    or IAM role is required — Snowflake reads directly via anonymous S3 access.
--
--    Bucket layout:
--      s3://sfquickstarts/vhol_snowflake_storage_iceberg_horizon_catalog/yellow/   (26 Parquet files)
--      s3://sfquickstarts/vhol_snowflake_storage_iceberg_horizon_catalog/green/    (26 Parquet files)
--      s3://sfquickstarts/vhol_snowflake_storage_iceberg_horizon_catalog/lookup/   (1 CSV)
--
--    HTTPS inspection: https://sfquickstarts.s3.amazonaws.com/vhol_snowflake_storage_iceberg_horizon_catalog/
-- ---------------------------------------------------------------------------

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

CREATE OR REPLACE STAGE TLC_STAGE
    URL = 's3://sfquickstarts/vhol_snowflake_storage_iceberg_horizon_catalog/'
    FILE_FORMAT = (TYPE = PARQUET)
    COMMENT = 'NYC TLC Parquet files -- Yellow + Green Taxi, Jan 2024 - Feb 2026 (DevRel public S3)';

LIST @TLC_STAGE/;
-- ---------------------------------------------------------------------------
-- 8. File Formats
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FILE FORMAT parquet_ff
    TYPE = PARQUET;

CREATE OR REPLACE FILE FORMAT csv_ff
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- ---------------------------------------------------------------------------
-- 9. Iceberg V3 Default
--    Setting the database default to Iceberg V3 (Apache Iceberg format v3).
--    V3 is required for several features used in this quickstart:
--      - VARIANT columns: native complex/semi-structured types in Iceberg format
--      - Deletion vectors: efficient row-level DML (UPDATE/DELETE/MERGE) without
--        rewriting entire data files
--      - Row lineage: tracking row-level provenance across table operations
--    Without this setting, new Iceberg tables default to V2, which lacks all
--    of the above capabilities.
-- ---------------------------------------------------------------------------
ALTER DATABASE ICEBERG_DEMO SET ICEBERG_VERSION_DEFAULT = 3;
SHOW PARAMETERS LIKE 'ICEBERG_VERSION_DEFAULT' IN DATABASE ICEBERG_DEMO;

-- ---------------------------------------------------------------------------
-- 10. Network Rule + External Access Integration for Open-Meteo API
--     Open-Meteo (archive-api.open-meteo.com) is the weather data source used
--     in script 02_ssv2_streaming_setup.sql for live streaming ingest.
--
--     The Java SSV2 (Snowpipe Streaming V2) client runs externally on
--     your local machine, so it calls the Open-Meteo API directly and does
--     NOT need this External Access Integration (EAI).
--
--     This EAI would only be needed if you wanted to call Open-Meteo from
--     inside Snowflake -- for example, via a Snowpark Python UDF, stored
--     procedure, or Snowflake Notebook. It is kept here if you want to
--     experiment with in-Snowflake API calls after completing the quickstart.
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NETWORK RULE ICEBERG_DEMO.PUBLIC.OPEN_METEO_NETWORK_RULE
    MODE       = EGRESS
    TYPE       = HOST_PORT
    VALUE_LIST = ('archive-api.open-meteo.com:443');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION OPEN_METEO_ACCESS
    ALLOWED_NETWORK_RULES = (ICEBERG_DEMO.PUBLIC.OPEN_METEO_NETWORK_RULE)
    ENABLED = TRUE
    COMMENT = 'External access for Open-Meteo historical weather API';

GRANT USAGE ON INTEGRATION OPEN_METEO_ACCESS TO ROLE DEMO_ADMIN;

-- ---------------------------------------------------------------------------
-- 11. Verification
--     Run these checks to confirm your environment is ready.
-- ---------------------------------------------------------------------------
USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;

LIST @TLC_STAGE/yellow/;
-- Expected: 26 Parquet files (yellow_tripdata_2024-01 through 2026-02)

LIST @TLC_STAGE/green/;
-- Expected: 26 Parquet files (green_tripdata_2024-01 through 2026-02)

LIST @TLC_STAGE/lookup/;
-- Expected: 1 CSV file (taxi_zone_lookup.csv)
-- If LIST returns 0 files, verify the sfquickstarts bucket is accessible.

SHOW INTEGRATIONS LIKE 'OPEN_METEO_ACCESS';
-- Expected: 1 row, enabled = true

-- Expected: ICEBERG_VERSION_DEFAULT = 3 at the database level.

SELECT 'Setup complete. Proceed to Module 1 (01_create_tables.sql).' AS status;

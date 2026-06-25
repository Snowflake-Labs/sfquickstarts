-- ================================================================
-- SCENARIO 2 — STEP 2 of 2: SNOWFLAKE FEDERATES DATABRICKS UC TABLES
--
-- What this does:
--   1. Creates a Catalog Integration connecting Snowflake to Databricks
--      Unity Catalog's Iceberg REST endpoint.
--   2. Creates a Catalog-Linked Database — Snowflake auto-discovers all
--      schemas and tables from the Databricks UC catalog.
--   3. Applies Snowflake Horizon masking policy on the federated
--      sensitive_orders table (Snowflake governance is independent
--      from Databricks UC policies).
--   4. Demonstrates governance comparison: ACCOUNTADMIN sees raw
--      credit cards; reader role sees masked values.
--
-- Prerequisites:
--   • Run 03_databricks_create_uc_tables.py in Databricks first.
--   • Have the Databricks PAT or service-principal token ready.
--   • Run as ACCOUNTADMIN.
--
-- !! REPLACE only: SF_WAREHOUSE, SF_USERNAME, DBX_WORKSPACE_HOST,
--                  DBX_UC_CATALOG, and DBX_PAT_TOKEN.
--    Everything else is pre-set for the demo.
-- ================================================================


-- ----------------------------------------------------------------
-- Parameters — SET YOUR VALUES HERE (change only this block)
-- ----------------------------------------------------------------

-- !! REPLACE: your Snowflake warehouse
SET SF_WAREHOUSE        = '<YOUR_WAREHOUSE>';

-- !! REPLACE: your Snowflake username
SET SF_USERNAME         = '<YOUR_USERNAME>';

-- !! REPLACE: Databricks workspace hostname (no https://)
--    e.g. 'adb-1234567890.12.azuredatabricks.net'
SET DBX_WORKSPACE_HOST  = '<DBX_WORKSPACE_HOST>';

-- !! REPLACE: Unity Catalog catalog name (must match 03_databricks_create_uc_tables.py)
SET DBX_UC_CATALOG      = '<DBX_UC_CATALOG>';

-- !! REPLACE: Databricks PAT — NEVER commit to source control
--    Generate: Databricks workspace → avatar → Settings → Developer → Access Tokens
SET DBX_PAT_TOKEN       = '<DBX_PAT_TOKEN>';

-- Pre-set demo values — no changes needed below this line
SET SF_FEDERATED_DB     = 'DATABRICKS_DEMO_DB';
SET SF_FEDERATED_SCHEMA = 'horizon_demo';
SET SF_EXTERNAL_VOLUME  = 'ICEBERG_EXTERNAL_S3_VOLUME';
SET SF_GOVERNANCE_DB    = 'HORIZON_DEMO_SFDB';
SET SF_READER_ROLE      = 'EXT_COMPUTE_ENG_DEMO_ROLE';

-- ----------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE IDENTIFIER($SF_WAREHOUSE);


-- ----------------------------------------------------------------
-- 1. Catalog Integration
--    Connects Snowflake to Databricks Unity Catalog Iceberg REST.
--    ACCESS_DELEGATION_MODE = EXTERNAL_VOLUME_CREDENTIALS means
--    Snowflake uses its own IAM role (via SF_EXTERNAL_VOLUME) to
--    read S3 directly — no credential vending from Databricks needed.
-- ----------------------------------------------------------------
CREATE OR REPLACE CATALOG INTEGRATION MY_DATABRICKS_UC_CI
    CATALOG_SOURCE = ICEBERG_REST
    TABLE_FORMAT   = ICEBERG
    REST_CONFIG = (
        CATALOG_URI           = 'https://' || $DBX_WORKSPACE_HOST || '/api/2.1/unity-catalog/iceberg-rest'
        CATALOG_NAME          = $DBX_UC_CATALOG
        ACCESS_DELEGATION_MODE = EXTERNAL_VOLUME_CREDENTIALS
    )
    REST_AUTHENTICATION = (
        TYPE         = BEARER
        BEARER_TOKEN = $DBX_PAT_TOKEN
    )
    ENABLED = TRUE;


-- ----------------------------------------------------------------
-- 2. Verify Connectivity
-- ----------------------------------------------------------------

-- Integration enabled
SHOW CATALOG INTEGRATIONS LIKE 'MY_DATABRICKS_UC_CI';

-- Test connection — must return {"success": true}
SELECT SYSTEM$VERIFY_CATALOG_INTEGRATION('MY_DATABRICKS_UC_CI');

-- List schemas in the Databricks catalog
SELECT SYSTEM$LIST_NAMESPACES_FROM_CATALOG('MY_DATABRICKS_UC_CI');
-- Expected: ["horizon_demo", "default", "information_schema"]

-- List Iceberg tables in the schema
SELECT SYSTEM$LIST_ICEBERG_TABLES_FROM_CATALOG('MY_DATABRICKS_UC_CI', $SF_FEDERATED_SCHEMA);
-- Expected: customer_orders, sensitive_orders


-- ----------------------------------------------------------------
-- 3. Catalog-Linked Database
--    Snowflake auto-discovers all schemas and tables from the
--    Databricks UC catalog. Tables appear as Iceberg objects.
--    Unity Catalog uses case-insensitive identifiers — use lowercase
--    or unquoted names when querying.
-- ----------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS IDENTIFIER($SF_FEDERATED_DB)
    EXTERNAL_VOLUME = $SF_EXTERNAL_VOLUME
    LINKED_CATALOG = (
        CATALOG = 'MY_DATABRICKS_UC_CI'
    )
    COMMENT = 'Iceberg Federation Demo — Federated from Databricks Unity Catalog';

-- Wait ~30 seconds for auto-discovery to complete, then verify:
SHOW ICEBERG TABLES IN DATABASE IDENTIFIER($SF_FEDERATED_DB);

-- Quick read test (use lowercase schema name)
SELECT * FROM DATABRICKS_DEMO_DB.horizon_demo.customer_orders LIMIT 5;


-- ----------------------------------------------------------------
-- 4. Demo Queries — Snowflake reads Databricks Iceberg tables
-- ----------------------------------------------------------------

-- 4a. Open table — all data, no policies
SELECT * FROM DATABRICKS_DEMO_DB.horizon_demo.customer_orders;

-- 4b. Aggregate by status
SELECT   status, COUNT(*) AS orders, SUM(amount) AS revenue
FROM     DATABRICKS_DEMO_DB.horizon_demo.customer_orders
GROUP BY status
ORDER BY revenue DESC;

-- 4c. Sensitive table — raw Parquet values before masking policy
SELECT * FROM DATABRICKS_DEMO_DB.horizon_demo.sensitive_orders;


-- ----------------------------------------------------------------
-- 5. Snowflake Horizon Governance on Databricks Tables
--
--    Masking policy applied to credit_card column.
--    Note: Databricks UC policies do NOT propagate to Snowflake.
--    Snowflake defines and enforces its own independent policies.
-- ----------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS HORIZON_DEMO_SFDB.GOVERNANCE_POLICIES;

CREATE OR REPLACE MASKING POLICY HORIZON_DEMO_SFDB.GOVERNANCE_POLICIES.MASK_CREDIT_CARD
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
        ELSE CONCAT('****-****-****-', RIGHT(val, 4))
    END;

ALTER ICEBERG TABLE DATABRICKS_DEMO_DB.horizon_demo.sensitive_orders
    MODIFY COLUMN "credit_card"
    SET MASKING POLICY HORIZON_DEMO_SFDB.GOVERNANCE_POLICIES.MASK_CREDIT_CARD;


-- ----------------------------------------------------------------
-- 6. Governance Comparison
-- ----------------------------------------------------------------

-- Create a non-admin reader role
CREATE ROLE IF NOT EXISTS IDENTIFIER($SF_READER_ROLE);
GRANT USAGE  ON DATABASE IDENTIFIER($SF_FEDERATED_DB)                                    TO ROLE IDENTIFIER($SF_READER_ROLE);
GRANT USAGE  ON SCHEMA   DATABRICKS_DEMO_DB.horizon_demo                                 TO ROLE IDENTIFIER($SF_READER_ROLE);
GRANT SELECT ON ALL ICEBERG TABLES IN SCHEMA DATABRICKS_DEMO_DB.horizon_demo             TO ROLE IDENTIFIER($SF_READER_ROLE);
GRANT ROLE IDENTIFIER($SF_READER_ROLE) TO USER IDENTIFIER($SF_USERNAME);

-- ACCOUNTADMIN: unmasked credit card
USE ROLE ACCOUNTADMIN;
SELECT CURRENT_ROLE() AS role, order_id, customer_name, credit_card
FROM DATABRICKS_DEMO_DB.horizon_demo.sensitive_orders;
-- credit_card: 4111-1111-1111-1111 (raw value)

-- Reader role: masked credit card
USE ROLE IDENTIFIER($SF_READER_ROLE);
SELECT CURRENT_ROLE() AS role, order_id, customer_name, credit_card
FROM DATABRICKS_DEMO_DB.horizon_demo.sensitive_orders;
-- credit_card: ****-****-****-1111 (masked)

USE ROLE ACCOUNTADMIN;


-- ----------------------------------------------------------------
-- 7. Sync Catalog-Linked Database
--    Catalog-linked databases auto-sync every 30 s by default.
--    RESUME DISCOVERY forces an immediate re-poll after new
--    tables or data is added in Databricks.
-- ----------------------------------------------------------------
ALTER DATABASE IDENTIFIER($SF_FEDERATED_DB) RESUME DISCOVERY;
SELECT SYSTEM$CATALOG_LINK_STATUS($SF_FEDERATED_DB);


-- ----------------------------------------------------------------
-- 8. Cleanup
-- ----------------------------------------------------------------
-- USE ROLE ACCOUNTADMIN;
-- DROP DATABASE          IF EXISTS IDENTIFIER($SF_FEDERATED_DB);
-- DROP CATALOG INTEGRATION IF EXISTS MY_DATABRICKS_UC_CI;
-- DROP ROLE              IF EXISTS IDENTIFIER($SF_READER_ROLE);
-- DROP SCHEMA            IF EXISTS HORIZON_DEMO_SFDB.GOVERNANCE_POLICIES CASCADE;

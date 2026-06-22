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
--      credit cards; SNOWFLAKE_READER_ROLE sees masked values.
--
-- Prerequisites:
--   • Run 03_databricks_create_uc_tables.py in Databricks first.
--   • Have the Databricks PAT or service-principal token ready.
--   • Run as ACCOUNTADMIN.
--
-- !! REPLACE all <PLACEHOLDER> values before running:
--      <SF_WAREHOUSE>           your warehouse name
--      <DBX_WORKSPACE_HOST>     Databricks workspace hostname (no https://)
--      <DBX_UC_CATALOG>         Unity Catalog catalog name  (e.g. my_demo)
--      <DBX_PAT_TOKEN>          Databricks PAT — NEVER commit to source control
--      <SF_EXTERNAL_VOLUME>     external volume for S3 access (if not using vended creds)
--      <SF_FEDERATED_DB>        Snowflake database for federated tables
--      <SF_GOVERNANCE_DB>       existing Snowflake DB for masking policy storage
--      <SF_READER_ROLE>         non-admin reader role (e.g. SNOWFLAKE_READER_ROLE)
--      <SF_USERNAME>            your Snowflake username
--      <SF_FEDERATED_SCHEMA>    schema name in the federated DB (lowercase, matches DBX)
-- ================================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE <SF_WAREHOUSE>;


-- ----------------------------------------------------------------
-- 1. Catalog Integration
--    Connects Snowflake to Databricks Unity Catalog Iceberg REST.
--    ACCESS_DELEGATION_MODE = EXTERNAL_VOLUME_CREDENTIALS means
--    Snowflake uses its own IAM role (via <SF_EXTERNAL_VOLUME>) to
--    read S3 directly — no credential vending from Databricks needed.
-- ----------------------------------------------------------------
CREATE OR REPLACE CATALOG INTEGRATION MY_DATABRICKS_UC_CI
    CATALOG_SOURCE = ICEBERG_REST
    TABLE_FORMAT   = ICEBERG
    REST_CONFIG = (
        CATALOG_URI           = 'https://<DBX_WORKSPACE_HOST>/api/2.1/unity-catalog/iceberg-rest'
        CATALOG_NAME          = '<DBX_UC_CATALOG>'
        ACCESS_DELEGATION_MODE = EXTERNAL_VOLUME_CREDENTIALS
    )
    REST_AUTHENTICATION = (
        TYPE         = BEARER
        BEARER_TOKEN = '<DBX_PAT_TOKEN>'  -- !! REPLACE with your Databricks PAT
        -- Generate: Databricks workspace → avatar → Settings → Developer → Access Tokens
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
-- Expected: ["<DBX_UC_SCHEMA>", "default", "information_schema"]

-- List Iceberg tables in the schema
SELECT SYSTEM$LIST_ICEBERG_TABLES_FROM_CATALOG('MY_DATABRICKS_UC_CI', '<DBX_UC_SCHEMA>');
-- Expected: customer_orders, sensitive_orders


-- ----------------------------------------------------------------
-- 3. Catalog-Linked Database
--    Snowflake auto-discovers all schemas and tables from the
--    Databricks UC catalog. Tables appear as Iceberg objects.
--    Unity Catalog uses case-insensitive identifiers — use lowercase
--    or unquoted names when querying.
-- ----------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS <SF_FEDERATED_DB>
    EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>'
    LINKED_CATALOG = (
        CATALOG = 'MY_DATABRICKS_UC_CI'
    )
    COMMENT = 'Iceberg Federation Demo — Federated from Databricks Unity Catalog';

-- Wait ~30 seconds for auto-discovery to complete, then verify:
SHOW ICEBERG TABLES IN DATABASE <SF_FEDERATED_DB>;

-- Quick read test (use lowercase schema name)
SELECT * FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.customer_orders LIMIT 5;


-- ----------------------------------------------------------------
-- 4. Demo Queries — Snowflake reads Databricks Iceberg tables
-- ----------------------------------------------------------------

-- 4a. Open table — all data, no policies
SELECT * FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.customer_orders;

-- 4b. Aggregate by status
SELECT   status, COUNT(*) AS orders, SUM(amount) AS revenue
FROM     <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.customer_orders
GROUP BY status
ORDER BY revenue DESC;

-- 4c. Sensitive table — raw Parquet values before masking policy
SELECT * FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders;


-- ----------------------------------------------------------------
-- 5. Snowflake Horizon Governance on Databricks Tables
--
--    Masking policy applied to credit_card column.
--    Note: Databricks UC policies do NOT propagate to Snowflake.
--    Snowflake defines and enforces its own independent policies.
-- ----------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES;

CREATE OR REPLACE MASKING POLICY <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES.MASK_CREDIT_CARD
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
        ELSE CONCAT('****-****-****-', RIGHT(val, 4))
    END;

ALTER ICEBERG TABLE <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders
    MODIFY COLUMN "credit_card"
    SET MASKING POLICY <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES.MASK_CREDIT_CARD;


-- ----------------------------------------------------------------
-- 6. Governance Comparison
-- ----------------------------------------------------------------

-- Create a non-admin reader role
CREATE ROLE IF NOT EXISTS <SF_READER_ROLE>;
GRANT USAGE  ON DATABASE <SF_FEDERATED_DB>                       TO ROLE <SF_READER_ROLE>;
GRANT USAGE  ON SCHEMA   <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA> TO ROLE <SF_READER_ROLE>;
GRANT SELECT ON ALL ICEBERG TABLES IN SCHEMA <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>
    TO ROLE <SF_READER_ROLE>;
GRANT ROLE <SF_READER_ROLE> TO USER <SF_USERNAME>;

-- ACCOUNTADMIN: unmasked credit card
USE ROLE ACCOUNTADMIN;
SELECT CURRENT_ROLE() AS role, order_id, customer_name, credit_card
FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders;
-- credit_card: 4111-1111-1111-1111 (raw value)

-- <SF_READER_ROLE>: masked credit card
USE ROLE <SF_READER_ROLE>;
SELECT CURRENT_ROLE() AS role, order_id, customer_name, credit_card
FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders;
-- credit_card: ****-****-****-1111 (masked)

USE ROLE ACCOUNTADMIN;


-- ----------------------------------------------------------------
-- 7. Sync Catalog-Linked Database
--    Catalog-linked databases auto-sync every 30 s by default.
--    RESUME DISCOVERY forces an immediate re-poll after new
--    tables or data is added in Databricks.
-- ----------------------------------------------------------------
ALTER DATABASE <SF_FEDERATED_DB> RESUME DISCOVERY;
SELECT SYSTEM$CATALOG_LINK_STATUS('<SF_FEDERATED_DB>');


-- ----------------------------------------------------------------
-- 8. Cleanup
-- ----------------------------------------------------------------
-- USE ROLE ACCOUNTADMIN;
-- DROP DATABASE   IF EXISTS <SF_FEDERATED_DB>;
-- DROP CATALOG INTEGRATION IF EXISTS MY_DATABRICKS_UC_CI;
-- DROP ROLE       IF EXISTS <SF_READER_ROLE>;
-- DROP SCHEMA     IF EXISTS <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES CASCADE;

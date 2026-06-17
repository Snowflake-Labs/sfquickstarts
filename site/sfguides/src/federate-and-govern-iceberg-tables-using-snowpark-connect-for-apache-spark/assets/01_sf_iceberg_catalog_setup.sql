-- ================================================================
-- SCENARIO 1 — SNOWFLAKE AS ICEBERG CATALOG
--
-- What this does:
--   • Creates two Snowflake-managed Iceberg tables in a dedicated
--     database that acts as an Iceberg REST Catalog (Horizon IRC).
--   • OPEN_TABLE    — Databricks can READ and WRITE.
--   • PROTECTED_TABLE — Databricks can READ only; writes are
--     blocked at the S3 credential-vending layer.
--   • Snowflake Horizon governance policies (column masking +
--     row access) are applied but only enforced via Snowflake SQL;
--     Databricks reads raw Parquet via vended S3 credentials.
--
-- Prerequisites:
--   1. An external volume pointing to your S3/ADLS/GCS bucket.
--      Create with:
--        CREATE EXTERNAL VOLUME <SF_EXTERNAL_VOLUME>
--          STORAGE_LOCATIONS = ((
--            NAME = 'my-location'
--            STORAGE_PROVIDER = 'S3'
--            STORAGE_BASE_URL = 's3://your-bucket/iceberg/'
--            STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::ACCT:role/ROLE'
--          ));
--   2. Run as ACCOUNTADMIN.
--
-- !! REPLACE the following before running:
--      <SF_WAREHOUSE>           your warehouse name
--      <SF_MANAGED_ICEBERG_DB>  database to create (e.g. BNY_ICEBERG_DB)
--      <SF_DEMO_SCHEMA>         schema name        (e.g. DEMO_SCHEMA)
--      <SF_EXTERNAL_VOLUME>     your external volume name
--      <SF_DATABRICKS_ROLE>     Snowflake role for Databricks (e.g. DATABRICKS_DEMO_ROLE)
--      <SF_USERNAME>            your Snowflake username
-- ================================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE <SF_WAREHOUSE>;


-- ----------------------------------------------------------------
-- 1. Database & Schema
-- ----------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>
    EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>'
    COMMENT = 'BNY Demo — Snowflake-managed Iceberg catalog (Horizon IRC)';

CREATE SCHEMA IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>;


-- ----------------------------------------------------------------
-- 2. OPEN_TABLE — No governance restrictions
--    Databricks: READ + WRITE (write-capable S3 credentials vended)
-- ----------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE (
    id          INT,
    product     STRING,
    quantity    INT,
    price       DECIMAL(10, 2),
    created_at  TIMESTAMP
)
CATALOG = 'SNOWFLAKE';


-- ----------------------------------------------------------------
-- 3. PROTECTED_TABLE — Governance policies applied
--    Databricks: READ only (read-only S3 credentials vended)
-- ----------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE (
    id              INT,
    customer_name   STRING,
    sensitive_data  STRING,   -- column masking policy applied below
    amount          DECIMAL(10, 2),
    created_at      TIMESTAMP
)
CATALOG = 'SNOWFLAKE';


-- ----------------------------------------------------------------
-- 4. Snowflake Horizon Governance Policies
--
--    These policies are enforced ONLY for Snowflake SQL access.
--    Databricks reading via Horizon IRC receives vended S3
--    credentials and reads raw Parquet — policies do NOT apply.
--    Write access is controlled by credential vending (Step 7).
-- ----------------------------------------------------------------

-- 4a. Column masking: hide sensitive_data from non-admin roles
ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    MODIFY COLUMN sensitive_data UNSET MASKING POLICY;

CREATE OR REPLACE MASKING POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.MASK_SENSITIVE
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
        ELSE '*** MASKED ***'
    END;

ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    MODIFY COLUMN sensitive_data
    SET MASKING POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.MASK_SENSITIVE;

-- 4b. Row access policy: non-admin roles see current-year rows only
ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    DROP ROW ACCESS POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.CURRENT_YEAR_ONLY;

CREATE OR REPLACE ROW ACCESS POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.CURRENT_YEAR_ONLY
    AS (created_at TIMESTAMP) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN')
        OR YEAR(created_at) = YEAR(CURRENT_DATE());

ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    ADD ROW ACCESS POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.CURRENT_YEAR_ONLY
    ON (created_at);


-- ----------------------------------------------------------------
-- 5. Sample Data
-- ----------------------------------------------------------------
INSERT INTO <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE VALUES
    (1, 'Laptop',    5,  999.99, CURRENT_TIMESTAMP()),
    (2, 'Mouse',    20,   29.99, CURRENT_TIMESTAMP()),
    (3, 'Keyboard', 15,   49.99, CURRENT_TIMESTAMP());

INSERT INTO <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE VALUES
    (1, 'Alice Johnson', 'SSN-123-45-6789', 5000.00, CURRENT_TIMESTAMP()),
    (2, 'Bob Smith',     'SSN-987-65-4321', 7500.00, CURRENT_TIMESTAMP()),
    -- Row 3 is year 2023 — filtered by row access policy for non-admin roles
    (3, 'Carol White',   'SSN-456-78-9012', 3200.00, '2023-03-15 10:00:00');


-- ----------------------------------------------------------------
-- 6. Snowflake Role for Databricks
-- ----------------------------------------------------------------
CREATE ROLE IF NOT EXISTS <SF_DATABRICKS_ROLE>;

GRANT USAGE ON WAREHOUSE <SF_WAREHOUSE>                              TO ROLE <SF_DATABRICKS_ROLE>;
GRANT USAGE ON DATABASE  <SF_MANAGED_ICEBERG_DB>                     TO ROLE <SF_DATABRICKS_ROLE>;
GRANT USAGE ON SCHEMA    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>    TO ROLE <SF_DATABRICKS_ROLE>;


-- ----------------------------------------------------------------
-- 7. Database Roles — Credential Vending Control
--
--    How write protection works via Horizon IRC:
--      Role has SELECT only          → Snowflake vends READ-ONLY S3 creds
--                                      → s3:PutObject returns 403
--      Role has INSERT/UPDATE/DELETE → Snowflake vends WRITE-CAPABLE S3 creds
--                                      → writes succeed
--
--    OPEN_TABLE      → OPEN_TABLE_RW   (SELECT + INSERT + UPDATE + DELETE)
--    PROTECTED_TABLE → PROTECTED_TABLE_RO (SELECT only)
-- ----------------------------------------------------------------

-- OPEN_TABLE: read + write
CREATE DATABASE ROLE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT USAGE  ON DATABASE <SF_MANAGED_ICEBERG_DB>                           TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT USAGE  ON SCHEMA   <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>          TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT SELECT ON TABLE    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT INSERT ON TABLE    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT UPDATE ON TABLE    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT DELETE ON TABLE    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;

-- PROTECTED_TABLE: read only
CREATE DATABASE ROLE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO;
GRANT USAGE  ON DATABASE <SF_MANAGED_ICEBERG_DB>                                TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO;
GRANT USAGE  ON SCHEMA   <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>               TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO;
GRANT SELECT ON TABLE    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO;

-- Wire database roles to the Databricks account role
GRANT DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW       TO ROLE <SF_DATABRICKS_ROLE>;
GRANT DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO  TO ROLE <SF_DATABRICKS_ROLE>;

GRANT ROLE <SF_DATABRICKS_ROLE> TO USER <SF_USERNAME>;


-- ----------------------------------------------------------------
-- 8. Generate Snowflake PAT for Databricks
--    ⚠  Copy the token value immediately — shown only once.
--    Paste it into 02_databricks_rw_sf_iceberg.py as SNOWFLAKE_PAT.
-- ----------------------------------------------------------------
ALTER USER <SF_USERNAME>
    ADD PROGRAMMATIC ACCESS TOKEN BNY_DEMO_PAT
    COMMENT = 'BNY Demo — Databricks Horizon IRC integration';


-- ----------------------------------------------------------------
-- 9. Verify Setup
-- ----------------------------------------------------------------
SHOW ICEBERG TABLES IN SCHEMA <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>;
SHOW DATABASE ROLES IN DATABASE <SF_MANAGED_ICEBERG_DB>;
SHOW GRANTS TO ROLE <SF_DATABRICKS_ROLE>;

-- Governance comparison via Snowflake SQL
-- As ACCOUNTADMIN: 3 rows, unmasked sensitive_data
SELECT 'ACCOUNTADMIN view' AS role_context, *
FROM <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE;

-- As <SF_DATABRICKS_ROLE>: 2 rows (2023 row filtered), *** MASKED ***
USE ROLE <SF_DATABRICKS_ROLE>;
SELECT 'DATABRICKS_DEMO_ROLE view' AS role_context, *
FROM <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE;

USE ROLE ACCOUNTADMIN;


-- ----------------------------------------------------------------
-- 10. Cleanup (run after demo)
-- ----------------------------------------------------------------
-- ALTER USER <SF_USERNAME> REMOVE PROGRAMMATIC ACCESS TOKEN BNY_DEMO_PAT;
-- DROP DATABASE IF EXISTS <SF_MANAGED_ICEBERG_DB>;
-- DROP ROLE   IF EXISTS   <SF_DATABRICKS_ROLE>;

-- ================================================================
-- SCENARIO 1 — SNOWFLAKE AS ICEBERG CATALOG
--
-- What this does:
--   • Creates two Snowflake-managed Iceberg tables in a dedicated
--     database that acts as an Iceberg REST Catalog (Horizon IRC).
--   • OPEN_TABLE      — External engine can READ and WRITE.
--   • PROTECTED_TABLE — External engine can READ only; writes are
--     blocked at the S3 credential-vending layer.
--   • Snowflake Horizon governance policies (column masking +
--     row access) are applied but only enforced via Snowflake SQL;
--     external engines read raw Parquet via vended S3 credentials.
--
-- Prerequisites:

--   1. Run as ACCOUNTADMIN.
--
-- !! REPLACE the values in the Parameters block below.
--    Everything else runs without modification.
-- ================================================================


-- ----------------------------------------------------------------
-- Parameters — SET YOUR VALUES HERE (change only this block)
-- ----------------------------------------------------------------
SET SF_WAREHOUSE          = '<YOUR_WAREHOUSE>';           -- !! REPLACE: e.g. 'COMPUTE_WH'
SET SF_MANAGED_ICEBERG_DB = 'HORIZON_DEMO_SFDB';             -- database to create
SET SF_DEMO_SCHEMA        = 'DEMO_SCHEMA';                -- schema name
SET SF_EXTERNAL_VOLUME    = 'SNOWFLAKE_MANAGED';         -- your external volume
SET SF_EXT_COMPUTE_ROLE   = 'EXT_COMPUTE_ENG_DEMO_ROLE'; -- Snowflake role for external engine
SET SF_USERNAME           = '<YOUR_USERNAME>';            -- !! REPLACE: your Snowflake username

-- Derived (auto-computed — do not change)
SET DB_SCHEMA = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA;
SET TBL_OPEN       = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.OPEN_TABLE';                                              
SET TBL_PROTECTED  = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.PROTECTED_TABLE';
SET MSK_POLICY     = $DB_SCHEMA || '.MASK_SENSITIVE';
SET ROW_ACCS_POLICY = $DB_SCHEMA || '.CURRENT_YEAR_ONLY';

SET ROLE_OPENTBL_RW = $SF_MANAGED_ICEBERG_DB || '.OPEN_TABLE_RW';
SET ROLE_PROTECTEDTBL_RO = $SF_MANAGED_ICEBERG_DB || '.PROTECTED_TABLE_RO';
-- ----------------------------------------------------------------
-- Setup
-- ----------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE IDENTIFIER($SF_WAREHOUSE);


-- ----------------------------------------------------------------
-- 1. Database & Schema
-- ----------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS IDENTIFIER ($SF_MANAGED_ICEBERG_DB)
    EXTERNAL_VOLUME = $SF_EXTERNAL_VOLUME
    COMMENT = 'Iceberg Federation Demo — Snowflake-managed Iceberg catalog (Horizon IRC)';

CREATE SCHEMA IF NOT EXISTS IDENTIFIER ($DB_SCHEMA);


-- ----------------------------------------------------------------
-- 2. OPEN_TABLE — No governance restrictions
--    External engine: READ + WRITE (write-capable S3 credentials vended)
-- ----------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE IDENTIFIER ($TBL_OPEN) (
    id          INT,
    product     STRING,
    quantity    INT,
    price       DECIMAL(10, 2),
    created_at  TIMESTAMP
)
CATALOG = 'SNOWFLAKE';


-- ----------------------------------------------------------------
-- 3. PROTECTED_TABLE — Governance policies applied
--    External engine: READ only (read-only S3 credentials vended)
-- ----------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE IDENTIFIER($TBL_PROTECTED) (
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
--    External engines reading via Horizon IRC receive vended S3
--    credentials and read raw Parquet — policies do NOT apply.
--    Write access is controlled by credential vending (Step 7).
-- ----------------------------------------------------------------

-- 4a. Column masking: hide sensitive_data from non-admin roles
--ALTER ICEBERG TABLE IDENTIFIER($TBL_PROTECTED)
--    MODIFY COLUMN sensitive_data UNSET MASKING POLICY;

CREATE OR REPLACE MASKING POLICY IDENTIFIER($MSK_POLICY)
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
        ELSE '*** MASKED ***'
    END;

ALTER ICEBERG TABLE IDENTIFIER($TBL_PROTECTED)
    MODIFY COLUMN sensitive_data
    SET MASKING POLICY IDENTIFIER($MSK_POLICY);

-- 4b. Row access policy: non-admin roles see current-year rows only

CREATE OR REPLACE ROW ACCESS POLICY IDENTIFIER($ROW_ACCS_POLICY)
    AS (created_at TIMESTAMP) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN')
        OR YEAR(created_at) = YEAR(CURRENT_DATE());

ALTER ICEBERG TABLE IDENTIFIER($TBL_PROTECTED)
    ADD ROW ACCESS POLICY IDENTIFIER($ROW_ACCS_POLICY)
    ON (created_at);


-- ----------------------------------------------------------------
-- 5. Sample Data
-- ----------------------------------------------------------------
INSERT INTO IDENTIFIER($TBL_OPEN) VALUES
    (1, 'Laptop',    5,  999.99, CURRENT_TIMESTAMP()),
    (2, 'Mouse',    20,   29.99, CURRENT_TIMESTAMP()),
    (3, 'Keyboard', 15,   49.99, CURRENT_TIMESTAMP());

INSERT INTO IDENTIFIER($TBL_PROTECTED) VALUES
    (1, 'Alice Johnson', 'SSN-123-45-6789', 5000.00, CURRENT_TIMESTAMP()),
    (2, 'Bob Smith',     'SSN-987-65-4321', 7500.00, CURRENT_TIMESTAMP()),
    -- Row 3 is year 2023 — filtered by row access policy for non-admin roles
    (3, 'Carol White',   'SSN-456-78-9012', 3200.00, '2023-03-15 10:00:00');


-- ----------------------------------------------------------------
-- 6. Snowflake Role for External Compute Engine
-- ----------------------------------------------------------------
CREATE ROLE IF NOT EXISTS IDENTIFIER($SF_EXT_COMPUTE_ROLE);

GRANT USAGE ON WAREHOUSE IDENTIFIER($SF_WAREHOUSE)          TO ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);
GRANT USAGE ON DATABASE  IDENTIFIER($SF_MANAGED_ICEBERG_DB) TO ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);
GRANT USAGE ON SCHEMA    IDENTIFIER($DB_SCHEMA)             TO ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);


-- ----------------------------------------------------------------
-- 7. Database Roles — Credential Vending Control
--
--    How write protection works via Horizon IRC:
--      Role has SELECT only          → Snowflake vends READ-ONLY S3 creds
--                                      → s3:PutObject returns 403
--      Role has INSERT/UPDATE/DELETE → Snowflake vends WRITE-CAPABLE S3 creds
--                                      → writes succeed
--
--    OPEN_TABLE      → OPEN_TABLE_RW      (SELECT + INSERT + UPDATE + DELETE + TRUNCATE)
--    PROTECTED_TABLE → PROTECTED_TABLE_RO (SELECT only)
-- ----------------------------------------------------------------

-- OPEN_TABLE: read + write
CREATE DATABASE ROLE IF NOT EXISTS IDENTIFIER($ROLE_OPENTBL_RW);
GRANT USAGE  ON DATABASE IDENTIFIER($SF_MANAGED_ICEBERG_DB)          TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);
GRANT USAGE  ON SCHEMA   IDENTIFIER($DB_SCHEMA)                      TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);
GRANT SELECT ON TABLE    IDENTIFIER($TBL_OPEN)                      TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);
GRANT INSERT    ON TABLE    IDENTIFIER($TBL_OPEN)     TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);
GRANT UPDATE    ON TABLE    IDENTIFIER($TBL_OPEN)     TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);
GRANT DELETE    ON TABLE    IDENTIFIER($TBL_OPEN)     TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);
GRANT TRUNCATE  ON TABLE    IDENTIFIER($TBL_OPEN)     TO DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW);

-- PROTECTED_TABLE: read only
CREATE DATABASE ROLE IF NOT EXISTS IDENTIFIER($ROLE_PROTECTEDTBL_RO);
GRANT USAGE  ON DATABASE IDENTIFIER($SF_MANAGED_ICEBERG_DB)               TO DATABASE ROLE IDENTIFIER($ROLE_PROTECTEDTBL_RO);
GRANT USAGE  ON SCHEMA   IDENTIFIER($DB_SCHEMA)                           TO DATABASE ROLE IDENTIFIER($ROLE_PROTECTEDTBL_RO);
GRANT SELECT ON TABLE    IDENTIFIER($TBL_PROTECTED)     TO DATABASE ROLE IDENTIFIER($ROLE_PROTECTEDTBL_RO);

-- Wire database roles to the external compute account role
GRANT DATABASE ROLE IDENTIFIER($ROLE_OPENTBL_RW)      TO ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);
GRANT DATABASE ROLE IDENTIFIER($ROLE_PROTECTEDTBL_RO) TO ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);

GRANT ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE) TO USER IDENTIFIER($SF_USERNAME);


-- ----------------------------------------------------------------
-- 8. Generate Snowflake PAT for External Compute Engine
--    ⚠  Copy the token value immediately — shown only once.
--    Paste it into 03_<external engine>_rw_sf_iceberg.py as SNOWFLAKE_PAT.
-- ----------------------------------------------------------------
ALTER USER IDENTIFIER($SF_USERNAME)
    ADD PROGRAMMATIC ACCESS TOKEN MY_DEMO_PAT
    COMMENT = 'Iceberg Federation Demo — External engine Horizon IRC integration';


-- ----------------------------------------------------------------
-- 9. Verify Setup
-- ----------------------------------------------------------------
SHOW ICEBERG TABLES IN SCHEMA IDENTIFIER($DB_SCHEMA);
SHOW DATABASE ROLES IN DATABASE IDENTIFIER($SF_MANAGED_ICEBERG_DB);
SHOW GRANTS TO ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);

-- Governance comparison via Snowflake SQL
-- As ACCOUNTADMIN: 3 rows, unmasked sensitive_data
SELECT 'ACCOUNTADMIN view' AS role_context, *
FROM IDENTIFIER($TBL_PROTECTED);

-- As SF_EXT_COMPUTE_ROLE: 2 rows (2023 row filtered), *** MASKED ***
USE ROLE IDENTIFIER($SF_EXT_COMPUTE_ROLE);
SELECT $SF_EXT_COMPUTE_ROLE || ' view' AS role_context, *
FROM IDENTIFIER($TBL_PROTECTED);

USE ROLE ACCOUNTADMIN;


-- ----------------------------------------------------------------
-- 10. Cleanup (run after demo)
-- ----------------------------------------------------------------
-- ALTER USER IDENTIFIER($SF_USERNAME) REMOVE PROGRAMMATIC ACCESS TOKEN MY_DEMO_PAT;
-- DROP DATABASE IF EXISTS IDENTIFIER($SF_MANAGED_ICEBERG_DB);
-- DROP ROLE   IF EXISTS   IDENTIFIER($SF_EXT_COMPUTE_ROLE);

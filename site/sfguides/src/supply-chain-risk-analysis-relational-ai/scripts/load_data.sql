-- =============================================================================
-- RelationalAI in Snowflake Notebooks: load the synthetic supply-chain data
--
-- Creates a demo role, warehouse, database and tables, connects the quickstart
-- Git repository, and loads the CSV files from its data/ directory.
--
-- Run as ACCOUNTADMIN (or a role that can create roles, warehouses, databases
-- and API integrations). Safe to re-run.
--
-- Using a fork of the companion repository? Change the ORIGIN of the Git repository and
-- API_ALLOWED_PREFIXES below.
-- =============================================================================
USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 1. Role, warehouse, database
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS RAI_QS_ROLE COMMENT = 'RelationalAI notebook quickstart';
GRANT ROLE RAI_QS_ROLE TO ROLE SYSADMIN;
SET my_user = CURRENT_USER();
GRANT ROLE RAI_QS_ROLE TO USER IDENTIFIER($my_user);

-- RAI_DEVELOPER is created during the RelationalAI app setup and carries the
-- application role needed to run PyRel.
GRANT ROLE RAI_DEVELOPER TO ROLE RAI_QS_ROLE;

CREATE WAREHOUSE IF NOT EXISTS RAI_QS_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;
-- Cap runaway statements (e.g. a recursive query looping on the planted supplier cycle).
ALTER WAREHOUSE RAI_QS_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 600;
GRANT USAGE ON WAREHOUSE RAI_QS_WH TO ROLE RAI_QS_ROLE;

CREATE DATABASE IF NOT EXISTS RAI_QUICKSTART;
CREATE SCHEMA IF NOT EXISTS RAI_QUICKSTART.SUPPLY_CHAIN;
GRANT OWNERSHIP ON DATABASE RAI_QUICKSTART TO ROLE RAI_QS_ROLE COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA RAI_QUICKSTART.SUPPLY_CHAIN TO ROLE RAI_QS_ROLE COPY CURRENT GRANTS;

-- ---------------------------------------------------------------------------
-- 2. Git repository with the sample data (public repo, no secret needed)
--
--    The data lives in the companion repository, not in sfquickstarts itself:
--    Snowflake cannot clone sfquickstarts ("Git Repository exceeds set limits").
--    TODO: replace the placeholder with the published companion repository.
-- ---------------------------------------------------------------------------
CREATE API INTEGRATION IF NOT EXISTS RAI_QS_GIT_INTEGRATION
  API_PROVIDER = GIT_HTTPS_API
  API_ALLOWED_PREFIXES = ('https://github.com/Snowflake-Labs')
  ENABLED = TRUE;
GRANT USAGE ON INTEGRATION RAI_QS_GIT_INTEGRATION TO ROLE RAI_QS_ROLE;

USE ROLE RAI_QS_ROLE;
USE WAREHOUSE RAI_QS_WH;
USE SCHEMA RAI_QUICKSTART.SUPPLY_CHAIN;

CREATE OR REPLACE GIT REPOSITORY RAI_QS_REPO
  API_INTEGRATION = RAI_QS_GIT_INTEGRATION
  ORIGIN = 'https://github.com/Snowflake-Labs/sfguide-getting-started-with-notebooks-relational-ai.git';
ALTER GIT REPOSITORY RAI_QS_REPO FETCH;

-- COPY INTO cannot read a Git repository directly: copy the CSVs to an internal stage first.
CREATE STAGE IF NOT EXISTS DATA_STAGE;
COPY FILES INTO @DATA_STAGE
  FROM @RAI_QS_REPO/branches/main/data/
  PATTERN = '.*[.]csv';

-- Alternative without Git: upload the files from data/ yourself, then skip the two Git
-- statements above. In Snowsight: Data > Databases > RAI_QUICKSTART > SUPPLY_CHAIN >
-- Stages > DATA_STAGE > + Files. Or with the Snowflake CLI:
--   snow stage copy data/ @RAI_QUICKSTART.SUPPLY_CHAIN.DATA_STAGE --recursive
LIST @DATA_STAGE;

CREATE OR REPLACE FILE FORMAT CSV_FORMAT
  TYPE = CSV PARSE_HEADER = TRUE FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- ---------------------------------------------------------------------------
-- 3. Tables
--    CHANGE_TRACKING is required: RelationalAI syncs source tables via CDC.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE PARTS (
  PART_ID   VARCHAR NOT NULL PRIMARY KEY,
  PART_NAME VARCHAR,
  PART_TYPE VARCHAR,          -- FINISHED | ASSEMBLY | COMPONENT
  UNIT_COST NUMBER(10,2)
) CHANGE_TRACKING = TRUE COMMENT = 'Finished goods, assemblies and components';

CREATE OR REPLACE TABLE PRODUCTS (
  PRODUCT_ID   VARCHAR NOT NULL PRIMARY KEY,
  PRODUCT_NAME VARCHAR,
  PART_ID      VARCHAR REFERENCES PARTS (PART_ID),   -- top-level part in the BOM
  LIST_PRICE   NUMBER(10,2)
) CHANGE_TRACKING = TRUE COMMENT = 'Sellable products';

CREATE OR REPLACE TABLE BOM (
  PARENT_PART_ID VARCHAR REFERENCES PARTS (PART_ID),
  CHILD_PART_ID  VARCHAR REFERENCES PARTS (PART_ID),
  QTY_PER        NUMBER(6,0)
) CHANGE_TRACKING = TRUE COMMENT = 'Bill of materials: variable depth, shared subassemblies';

CREATE OR REPLACE TABLE SUBSTITUTES (
  PART_ID            VARCHAR REFERENCES PARTS (PART_ID),
  SUBSTITUTE_PART_ID VARCHAR REFERENCES PARTS (PART_ID),
  RATIO              NUMBER(6,2)
) CHANGE_TRACKING = TRUE COMMENT = 'Approved alternative components';

CREATE OR REPLACE TABLE SUPPLIERS (
  SUPPLIER_ID   VARCHAR NOT NULL PRIMARY KEY,
  SUPPLIER_NAME VARCHAR,
  TIER          NUMBER(1,0),
  COUNTRY       VARCHAR,
  REGION        VARCHAR
) CHANGE_TRACKING = TRUE COMMENT = 'Suppliers in tiers 1 to 4';

CREATE OR REPLACE TABLE SUPPLIER_PARTS (
  SUPPLIER_ID       VARCHAR REFERENCES SUPPLIERS (SUPPLIER_ID),
  PART_ID           VARCHAR REFERENCES PARTS (PART_ID),
  CAPACITY_PER_WEEK NUMBER(8,0),
  LEAD_TIME_DAYS    NUMBER(4,0),
  UNIT_PRICE        NUMBER(10,2)
) CHANGE_TRACKING = TRUE COMMENT = 'Tier-1 suppliers of components';

CREATE OR REPLACE TABLE SUPPLIER_DEPENDENCIES (
  SUPPLIER_ID            VARCHAR REFERENCES SUPPLIERS (SUPPLIER_ID),
  DEPENDS_ON_SUPPLIER_ID VARCHAR REFERENCES SUPPLIERS (SUPPLIER_ID)
) CHANGE_TRACKING = TRUE COMMENT = 'Tier-N supplier dependencies (may contain cycles)';

CREATE OR REPLACE TABLE INVENTORY (
  PART_ID     VARCHAR REFERENCES PARTS (PART_ID),
  ON_HAND_QTY NUMBER(8,0)
) CHANGE_TRACKING = TRUE COMMENT = 'Stock on hand per part';

CREATE OR REPLACE TABLE CUSTOMERS (
  CUSTOMER_ID   VARCHAR NOT NULL PRIMARY KEY,
  CUSTOMER_NAME VARCHAR,
  REGION        VARCHAR
) CHANGE_TRACKING = TRUE;

CREATE OR REPLACE TABLE ORDERS (
  ORDER_ID    VARCHAR NOT NULL PRIMARY KEY,
  CUSTOMER_ID VARCHAR REFERENCES CUSTOMERS (CUSTOMER_ID),
  PRODUCT_ID  VARCHAR REFERENCES PRODUCTS (PRODUCT_ID),
  QUANTITY    NUMBER(6,0),
  DUE_DATE    DATE,
  ORDER_VALUE NUMBER(12,2)
) CHANGE_TRACKING = TRUE COMMENT = 'Open customer orders';

-- ---------------------------------------------------------------------------
-- 4. Load
-- ---------------------------------------------------------------------------
COPY INTO PARTS                 FROM @DATA_STAGE/parts.csv                 FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO PRODUCTS              FROM @DATA_STAGE/products.csv              FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO BOM                   FROM @DATA_STAGE/bom.csv                   FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO SUBSTITUTES           FROM @DATA_STAGE/substitutes.csv           FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO SUPPLIERS             FROM @DATA_STAGE/suppliers.csv             FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO SUPPLIER_PARTS        FROM @DATA_STAGE/supplier_parts.csv        FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO SUPPLIER_DEPENDENCIES FROM @DATA_STAGE/supplier_dependencies.csv FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO INVENTORY             FROM @DATA_STAGE/inventory.csv             FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO CUSTOMERS             FROM @DATA_STAGE/customers.csv             FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;
COPY INTO ORDERS                FROM @DATA_STAGE/orders.csv                FILE_FORMAT = CSV_FORMAT MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE FORCE = TRUE;

-- ---------------------------------------------------------------------------
-- 5. Check row counts
--    Expected: PARTS 315, PRODUCTS 20, BOM 469, SUBSTITUTES 60, SUPPLIERS 80,
--    SUPPLIER_PARTS 483, SUPPLIER_DEPENDENCIES 81, INVENTORY 315, CUSTOMERS 100, ORDERS 1500
-- ---------------------------------------------------------------------------
SELECT 'PARTS' AS table_name, COUNT(*) AS row_count FROM PARTS
UNION ALL SELECT 'PRODUCTS', COUNT(*) FROM PRODUCTS
UNION ALL SELECT 'BOM', COUNT(*) FROM BOM
UNION ALL SELECT 'SUBSTITUTES', COUNT(*) FROM SUBSTITUTES
UNION ALL SELECT 'SUPPLIERS', COUNT(*) FROM SUPPLIERS
UNION ALL SELECT 'SUPPLIER_PARTS', COUNT(*) FROM SUPPLIER_PARTS
UNION ALL SELECT 'SUPPLIER_DEPENDENCIES', COUNT(*) FROM SUPPLIER_DEPENDENCIES
UNION ALL SELECT 'INVENTORY', COUNT(*) FROM INVENTORY
UNION ALL SELECT 'CUSTOMERS', COUNT(*) FROM CUSTOMERS
UNION ALL SELECT 'ORDERS', COUNT(*) FROM ORDERS
ORDER BY table_name;

-- ================================================================
-- SCENARIO 4 — CORTEX AI ENRICHMENT PIPELINE ON ICEBERG
--
-- What this demonstrates:
--   Snowflake Cortex LLM functions enrich federated Iceberg data
--   and persist AI-generated results as a new Snowflake-managed
--   Iceberg table. Horizon governance applies to AI output the same
--   way it applies to raw data. A Cortex Agent queries all three
--   Iceberg tables using natural language.
--
-- Prerequisites:
--   Run 01_sf_iceberg_catalog_setup.sql  (Scenario 1 tables)
--   Run 05_sf_federate_databricks_uc.sql (Scenario 3 CLD tables)
--
-- !! REPLACE all <PLACEHOLDER> values below before running.
-- ================================================================

-- !! REPLACE: Snowflake database for Snowflake-managed Iceberg tables (Scenario 1)
-- e.g. MY_ICEBERG_DB
SET SF_MANAGED_ICEBERG_DB = '<SF_MANAGED_ICEBERG_DB>';

-- !! REPLACE: Schema inside the managed Iceberg database
-- e.g. DEMO_SCHEMA
SET SF_DEMO_SCHEMA = '<SF_DEMO_SCHEMA>';

-- !! REPLACE: Catalog-linked database federated from external catalog (Scenario 3)
-- e.g. MY_DATABRICKS_DB
SET SF_FEDERATED_DB = '<SF_FEDERATED_DB>';

-- !! REPLACE: Lowercase schema name inside the catalog-linked database
-- e.g. my_demo_schema
SET SF_FEDERATED_SCHEMA = '<SF_FEDERATED_SCHEMA>';

-- !! REPLACE: External volume used for Snowflake-managed Iceberg storage
-- e.g. SNOWFLAKE_MANAGED
SET SF_EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>';

-- !! REPLACE: Non-admin reader role (same as used in Scenario 1)
-- e.g. DATABRICKS_DEMO_ROLE
SET SF_READER_ROLE = '<SF_READER_ROLE>';

-- !! REPLACE: Warehouse for Cortex compute
-- e.g. LOAD_WH
SET SF_WAREHOUSE = '<SF_WAREHOUSE>';

-- !! REPLACE: Snowflake database and schema for governance policies
-- e.g. HORIZON_DEMO_SFDB.DEMO_SCHEMA
SET SF_GOVERNANCE_SCHEMA = '<SF_GOVERNANCE_DB>.<SF_GOVERNANCE_SCHEMA>';

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE IDENTIFIER($SF_WAREHOUSE);

-- ================================================================
-- STEP 1 — VERIFY CORTEX IS AVAILABLE
-- ================================================================
-- Run this cell first. If it errors, your account region does not
-- support Cortex LLM functions (switch to us-east-1 or us-west-2).

SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'llama3.1-8b',
    'Reply with exactly one word: ready'
) AS cortex_status;

-- ================================================================
-- STEP 2 — CREATE AI_ORDER_INSIGHTS ICEBERG TABLE
--
-- Reads from the catalog-linked database (Scenario 3 federated tables)
-- and writes Cortex-enriched results to a new Snowflake-managed table.
-- ================================================================

CREATE OR REPLACE ICEBERG TABLE IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
    CATALOG = 'SNOWFLAKE'
    AS
WITH deduped_orders AS (
    SELECT order_id, customer_id, product, amount, order_date, status
    FROM IDENTIFIER($SF_FEDERATED_DB || '.' || $SF_FEDERATED_SCHEMA || '.customer_orders')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
),
deduped_sensitive AS (
    SELECT order_id, region
    FROM IDENTIFIER($SF_FEDERATED_DB || '.' || $SF_FEDERATED_SCHEMA || '.sensitive_orders')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
)
SELECT
    co.order_id,
    co.customer_id,
    co.product,
    co.amount,
    co.order_date,
    co.status,
    COALESCE(so.region, 'UNKNOWN') AS region,
    -- Rule-based risk tier (deterministic — reliable for governance demo)
    CASE
        WHEN co.status = 'CANCELLED' THEN 'HIGH'
        WHEN co.amount >= 500        THEN 'HIGH'
        WHEN co.amount >= 100        THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_level,
    -- Cortex-generated operational note (natural language)
    SNOWFLAKE.CORTEX.COMPLETE(
        'llama3.1-8b',
        CONCAT(
            'You are a logistics AI assistant. Write one actionable sentence (max 15 words) ',
            'for the operations team about this order. ',
            'Product: ', co.product, ', Amount: $', co.amount::STRING,
            ', Status: ', co.status,
            CASE WHEN so.region IS NOT NULL THEN ', Region: ' || so.region ELSE '' END, '.'
        )
    )::VARCHAR AS ops_note,
    CURRENT_TIMESTAMP()::TIMESTAMP_LTZ(6) AS enriched_at
FROM deduped_orders co
LEFT JOIN deduped_sensitive so ON co.order_id = so.order_id;

-- Re-apply masking policy immediately after CTAS
-- CREATE OR REPLACE drops all column policies; this must run every time
ALTER ICEBERG TABLE IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
    MODIFY COLUMN risk_level
    SET MASKING POLICY IDENTIFIER($SF_GOVERNANCE_SCHEMA || '.MASK_RISK_LEVEL');

-- Verify results
SELECT order_id, product, amount, status, region, risk_level, ops_note
FROM IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
ORDER BY order_id;

-- ================================================================
-- STEP 3 — APPLY HORIZON GOVERNANCE ON AI OUTPUT
--
-- The same Horizon masking framework applies to AI-generated columns.
-- Non-admin roles see *** RESTRICTED *** for HIGH risk orders.
-- ================================================================

CREATE OR REPLACE MASKING POLICY IDENTIFIER($SF_GOVERNANCE_SCHEMA || '.MASK_RISK_LEVEL')
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
        WHEN val = 'HIGH' THEN '*** RESTRICTED ***'
        ELSE val
    END;

ALTER ICEBERG TABLE IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
    MODIFY COLUMN risk_level
    SET MASKING POLICY IDENTIFIER($SF_GOVERNANCE_SCHEMA || '.MASK_RISK_LEVEL');

-- Grant reader role access to the AI insights table
GRANT SELECT ON TABLE IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
    TO ROLE IDENTIFIER($SF_READER_ROLE);

-- ================================================================
-- STEP 4 — GOVERNANCE COMPARISON: AI-GENERATED COLUMN
-- ================================================================

-- ACCOUNTADMIN: sees actual risk levels including HIGH
USE ROLE ACCOUNTADMIN;
SELECT
    'ACCOUNTADMIN'   AS role_context,
    order_id, product, amount, region, risk_level, ops_note
FROM IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
ORDER BY order_id;

-- Reader role: HIGH risk masked to *** RESTRICTED ***
USE ROLE IDENTIFIER($SF_READER_ROLE);
SELECT
    $SF_READER_ROLE  AS role_context,
    order_id, product, amount, region, risk_level
FROM IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
ORDER BY order_id;

USE ROLE ACCOUNTADMIN;

-- ================================================================
-- STEP 5 — GRANT READER ROLE ACCESS TO SEMANTIC VIEW
-- ================================================================

GRANT SELECT ON TABLE IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
    TO ROLE IDENTIFIER($SF_READER_ROLE);

-- ================================================================
-- STEP 6 — CREATE CORTEX ANALYST SEMANTIC VIEW
--
-- Semantic views are the recommended path for Cortex Analyst (replaces
-- legacy YAML files). This DDL-based object:
--   - Appears in Snowsight → AI & ML → Cortex Analyst automatically
--   - Supports natural language queries across both Iceberg tables
--   - Enforces Horizon masking policies (risk_level masked per role)
--   - Spans both SF-managed and catalog-linked database tables
-- ================================================================

CREATE OR REPLACE SEMANTIC VIEW IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.ICEBERG_AI_SEMANTIC_VIEW')
TABLES (
  orders     AS IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS')
               PRIMARY KEY (order_id)
               WITH SYNONYMS = ('ai orders', 'enriched orders', 'risk orders'),

  fed_orders AS IDENTIFIER($SF_FEDERATED_DB || '.' || $SF_FEDERATED_SCHEMA || '.customer_orders')
               PRIMARY KEY (order_id)
               WITH SYNONYMS = ('federated orders', 'source orders', 'databricks orders')
)
RELATIONSHIPS (
  orders(order_id) REFERENCES fed_orders
)
FACTS (
  orders.amount AS amount
    WITH SYNONYMS = ('order value', 'revenue', 'price')
)
DIMENSIONS (
  orders.product    AS product     WITH SYNONYMS = ('item', 'product name'),
  orders.status     AS status      WITH SYNONYMS = ('fulfillment status', 'order status'),
  orders.region     AS region      WITH SYNONYMS = ('geography', 'location'),
  orders.risk_level AS risk_level  WITH SYNONYMS = ('risk', 'risk tier', 'risk classification'),
  orders.order_date AS order_date,
  orders.ops_note   AS ops_note    WITH SYNONYMS = ('operational note', 'ai note', 'action item')
)
METRICS (
  orders.total_revenue   AS SUM(orders.amount)      WITH SYNONYMS = ('revenue', 'total sales'),
  orders.order_count     AS COUNT(orders.order_id)  WITH SYNONYMS = ('number of orders'),
  orders.avg_order_value AS AVG(orders.amount)       WITH SYNONYMS = ('average order', 'AOV')
);

-- Grant reader role access to the semantic view
GRANT SELECT ON SEMANTIC VIEW IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.ICEBERG_AI_SEMANTIC_VIEW')
    TO ROLE IDENTIFIER($SF_READER_ROLE);

-- Verify it was created
SHOW SEMANTIC VIEWS IN SCHEMA IDENTIFIER($SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA);

-- ================================================================
-- STEP 7 — CORTEX ANALYST DEMO (Snowsight)
--
-- Open: Snowsight → AI & ML → Cortex Analyst
-- Select: <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.ICEBERG_AI_SEMANTIC_VIEW
--
-- Suggested demo prompts:
--   "What is the total revenue by risk level?"
--   "Which orders are classified as HIGH risk?"
--   "Show me all SHIPPED orders in the US-WEST region"
--   "What is the average order value by status?"
--   "Compare revenue from enriched orders vs federated source orders"
--
-- Switch to <SF_READER_ROLE> in Snowsight and ask about HIGH risk orders
-- → risk_level shows *** RESTRICTED *** — Horizon masking via Cortex Analyst
-- ================================================================

-- ================================================================
-- CLEANUP (run after demo)
-- ================================================================
-- DROP SEMANTIC VIEW IF EXISTS <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.ICEBERG_AI_SEMANTIC_VIEW;
-- DROP ICEBERG TABLE IF EXISTS <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.AI_ORDER_INSIGHTS;
-- ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.AI_ORDER_INSIGHTS
--     MODIFY COLUMN risk_level UNSET MASKING POLICY;

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
-- !! REPLACE the values in the Parameters block below.
--    Everything else runs without modification.
-- ================================================================

-- ----------------------------------------------------------------
-- Parameters — SET YOUR VALUES HERE (change only this block)
-- ----------------------------------------------------------------
SET SF_MANAGED_ICEBERG_DB = 'HORIZON_DEMO_SFDB';    -- Scenario 1 database
SET SF_DEMO_SCHEMA        = 'DEMO_SCHEMA';           -- schema inside managed DB
SET SF_FEDERATED_DB       = 'DATABRICKS_DEMO_DB';    -- catalog-linked database (Scenario 3)
SET SF_FEDERATED_SCHEMA   = 'horizon_demo';          -- lowercase schema in CLD
SET SF_EXTERNAL_VOLUME    = 'SNOWFLAKE_MANAGED';     -- external volume
SET SF_READER_ROLE        = 'EXT_COMPUTE_ENG_DEMO_ROLE'; -- non-admin reader role
SET SF_WAREHOUSE          = '<YOUR_WAREHOUSE>';      -- !! REPLACE: e.g. 'LOAD_WH'

-- Derived (auto-computed — do not change)
SET AI_INSIGHTS_TBL  = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.AI_ORDER_INSIGHTS';
SET SEMANTIC_VIEW    = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.ICEBERG_AI_SEMANTIC_VIEW';
SET MASK_RISK        = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA || '.MASK_RISK_LEVEL';
SET FED_ORDERS       = $SF_FEDERATED_DB || '.' || $SF_FEDERATED_SCHEMA || '.customer_orders';
SET FED_SENSITIVE    = $SF_FEDERATED_DB || '.' || $SF_FEDERATED_SCHEMA || '.sensitive_orders';
SET DB_SCHEMA        = $SF_MANAGED_ICEBERG_DB || '.' || $SF_DEMO_SCHEMA;

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
-- CREATE OR REPLACE drops the old table first, which automatically
-- releases any masking policy associations — making it safe to
-- CREATE OR REPLACE the masking policy in Step 3 on every re-run.
-- ================================================================

CREATE OR REPLACE ICEBERG TABLE IDENTIFIER($AI_INSIGHTS_TBL)
    CATALOG = 'SNOWFLAKE'
    AS
WITH deduped_orders AS (
    SELECT order_id, customer_id, product, amount, order_date, status
    FROM IDENTIFIER($FED_ORDERS)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
),
deduped_sensitive AS (
    SELECT order_id, region
    FROM IDENTIFIER($FED_SENSITIVE)
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

-- ================================================================
-- STEP 3 — APPLY HORIZON GOVERNANCE ON AI OUTPUT
--
-- CREATE OR REPLACE TABLE (above) dropped the old table, releasing
-- any masking policy associations. It is now safe to CREATE OR REPLACE
-- the masking policy and re-apply it on every run.
-- ================================================================

CREATE OR REPLACE MASKING POLICY IDENTIFIER($MASK_RISK)
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
        WHEN val = 'HIGH' THEN '*** RESTRICTED ***'
        ELSE val
    END;

-- Apply to AI-generated risk_level column
ALTER ICEBERG TABLE IDENTIFIER($AI_INSIGHTS_TBL)
    MODIFY COLUMN risk_level
    SET MASKING POLICY IDENTIFIER($MASK_RISK);

-- Grant reader role access
GRANT SELECT ON TABLE IDENTIFIER($AI_INSIGHTS_TBL)
    TO ROLE IDENTIFIER($SF_READER_ROLE);

-- Verify results
SELECT order_id, product, amount, status, region, risk_level, ops_note
FROM IDENTIFIER($AI_INSIGHTS_TBL)
ORDER BY order_id;

-- ================================================================
-- STEP 4 — GOVERNANCE COMPARISON: AI-GENERATED COLUMN
--
-- Same Horizon masking framework as Scenario 1.
-- Non-admin roles see *** RESTRICTED *** for HIGH risk orders.
-- ================================================================

-- ACCOUNTADMIN: sees actual risk levels including HIGH
USE ROLE ACCOUNTADMIN;
SELECT
    'ACCOUNTADMIN'   AS role_context,
    order_id, product, amount, region, risk_level, ops_note
FROM IDENTIFIER($AI_INSIGHTS_TBL)
ORDER BY order_id;

-- Reader role: HIGH risk masked to *** RESTRICTED ***
USE ROLE IDENTIFIER($SF_READER_ROLE);
SELECT
    $SF_READER_ROLE  AS role_context,
    order_id, product, amount, region, risk_level
FROM IDENTIFIER($AI_INSIGHTS_TBL)
ORDER BY order_id;

USE ROLE ACCOUNTADMIN;

-- ================================================================
-- STEP 5 — CREATE CORTEX ANALYST SEMANTIC VIEW
--
-- Semantic views are the recommended path for Cortex Analyst.
-- This DDL-based object:
--   - Appears in Snowsight → AI & ML → Cortex Analyst automatically
--   - Supports natural language queries across both Iceberg tables
--   - Enforces Horizon masking policies (risk_level masked per role)
--   - Spans both SF-managed and catalog-linked database tables
-- ================================================================

CREATE OR REPLACE SEMANTIC VIEW IDENTIFIER($SEMANTIC_VIEW)
TABLES (
  orders     AS IDENTIFIER($AI_INSIGHTS_TBL)
               PRIMARY KEY (order_id)
               WITH SYNONYMS = ('ai orders', 'enriched orders', 'risk orders'),

  fed_orders AS IDENTIFIER($FED_ORDERS)
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
GRANT SELECT ON SEMANTIC VIEW IDENTIFIER($SEMANTIC_VIEW)
    TO ROLE IDENTIFIER($SF_READER_ROLE);

-- Verify it was created
SHOW SEMANTIC VIEWS IN SCHEMA IDENTIFIER($DB_SCHEMA);

-- ================================================================
-- STEP 6 — CORTEX ANALYST DEMO (Snowsight)
--
-- Open: Snowsight → AI & ML → Cortex Analyst
-- Select: HORIZON_DEMO_SFDB.DEMO_SCHEMA.ICEBERG_AI_SEMANTIC_VIEW
--
-- Suggested demo prompts:
--   "What is the total revenue by risk level?"
--   "Which orders are classified as HIGH risk?"
--   "Show me all SHIPPED orders in the US-WEST region"
--   "What is the average order value by status?"
--   "Compare revenue from enriched orders vs federated source orders"
--
-- Switch to EXT_COMPUTE_ENG_DEMO_ROLE in Snowsight and ask about HIGH risk orders
-- → risk_level shows *** RESTRICTED *** — Horizon masking via Cortex Analyst
-- ================================================================

-- ================================================================
-- CLEANUP (run after demo)
-- ================================================================
-- DROP SEMANTIC VIEW IF EXISTS IDENTIFIER($SEMANTIC_VIEW);
-- ALTER ICEBERG TABLE IDENTIFIER($AI_INSIGHTS_TBL) MODIFY COLUMN risk_level UNSET MASKING POLICY;
-- DROP ICEBERG TABLE IF EXISTS IDENTIFIER($AI_INSIGHTS_TBL);
-- DROP MASKING POLICY IF EXISTS IDENTIFIER($MASK_RISK);

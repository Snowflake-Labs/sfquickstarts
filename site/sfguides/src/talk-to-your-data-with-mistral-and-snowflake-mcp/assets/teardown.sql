-- =============================================================================
-- Shipping Logistics Demo — Teardown / Cleanup
-- =============================================================================
-- Removes all objects created by this quickstart.
-- Run this when you are done with the demo and want to clean up your account.
--
-- Run as: ACCOUNTADMIN (or the role that owns the objects)
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- 1. Drop MCP Server (depends on Agent, Analyst, Search)
-- =============================================================================

DROP MCP SERVER IF EXISTS LOGISTICS_C.SHIPPING_MARTS.SHIPPING_MCP_SERVER;

-- =============================================================================
-- 2. Drop Cortex Agent
-- =============================================================================

DROP AGENT IF EXISTS LOGISTICS_C.SHIPPING_MARTS.SHIPPING_LOGISTICS_AGENT;

-- =============================================================================
-- 3. Drop Semantic View
-- =============================================================================

DROP SEMANTIC VIEW IF EXISTS LOGISTICS_C.SHIPPING_MARTS.SHIPMENT_ANALYTICS_SV;

-- =============================================================================
-- 4. Drop Cortex Search Service
-- =============================================================================

DROP CORTEX SEARCH SERVICE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS_SEARCH;

-- =============================================================================
-- 5. Drop Tables
-- =============================================================================

DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENT_EVENTS;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENT_PERFORMANCE;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENTS;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.DIM_CUSTOMERS;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.DIM_VESSELS;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.DIM_PORTS;
DROP TABLE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.DIM_ROUTES;

-- =============================================================================
-- 6. Drop Stage and File Format (created by load_sample_data.sql)
-- =============================================================================

DROP STAGE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE;
DROP FILE FORMAT IF EXISTS LOGISTICS_C.SHIPPING_MARTS.CSV_LOAD_FORMAT;

-- =============================================================================
-- 7. Drop Schema and Database
-- =============================================================================
-- Uncomment the lines below if you want to remove the entire database.
-- WARNING: This will delete ALL objects in the database, not just this demo.

-- DROP SCHEMA IF EXISTS LOGISTICS_C.SHIPPING_MARTS;
-- DROP DATABASE IF EXISTS LOGISTICS_C;

-- =============================================================================
-- 8. Drop Role and PAT (optional)
-- =============================================================================
-- Uncomment if you created a dedicated role for this quickstart.

-- DROP ROLE IF EXISTS MCP_USER_ROLE;

-- To remove the PAT:
-- ALTER USER <YOUR_USERNAME> DROP PROGRAMMATIC ACCESS TOKEN TOKEN_NAME = 'mistral_mcp_token';

-- =============================================================================
-- Verification
-- =============================================================================

SHOW MCP SERVERS IN SCHEMA LOGISTICS_C.SHIPPING_MARTS;
-- Expected: empty result

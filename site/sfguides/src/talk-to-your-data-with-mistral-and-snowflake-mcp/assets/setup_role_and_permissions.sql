-- =============================================================================
-- Role & Permissions Setup for Snowflake MCP Server Access
-- =============================================================================
-- This script creates a dedicated role with the minimum permissions needed 
-- to access the MCP Server and its underlying objects (Semantic View, Cortex
-- Search Service, Cortex Agent, and source tables).
--
-- Run as: ACCOUNTADMIN (or a role with MANAGE GRANTS)
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- Step 1: Create a dedicated role for MCP access
-- ---------------------------------------------------------------------------

CREATE ROLE IF NOT EXISTS MCP_USER_ROLE
  COMMENT = 'Role for accessing Snowflake MCP Server and underlying Cortex objects';

-- ---------------------------------------------------------------------------
-- Step 2: Grant database and schema access
-- ---------------------------------------------------------------------------

-- Database-level usage
GRANT USAGE ON DATABASE LOGISTICS_C TO ROLE MCP_USER_ROLE;

-- Schema-level usage
GRANT USAGE ON SCHEMA LOGISTICS_C.SHIPPING_MARTS TO ROLE MCP_USER_ROLE;

-- ---------------------------------------------------------------------------
-- Step 3: Grant warehouse usage (required for Cortex Analyst queries)
-- ---------------------------------------------------------------------------

GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE MCP_USER_ROLE;

-- ---------------------------------------------------------------------------
-- Step 4: Grant access to the MCP Server
-- ---------------------------------------------------------------------------

GRANT USAGE ON MCP SERVER LOGISTICS_C.SHIPPING_MARTS.SHIPPING_MCP_SERVER 
  TO ROLE MCP_USER_ROLE;

-- ---------------------------------------------------------------------------
-- Step 5: Grant access to underlying Cortex objects
-- ---------------------------------------------------------------------------

-- Cortex Agent
GRANT USAGE ON AGENT LOGISTICS_C.SHIPPING_MARTS.SHIPPING_LOGISTICS_AGENT 
  TO ROLE MCP_USER_ROLE;

-- Semantic View (used by Cortex Analyst)
GRANT SELECT ON SEMANTIC VIEW LOGISTICS_C.SHIPPING_MARTS.SHIPMENT_ANALYTICS_SV 
  TO ROLE MCP_USER_ROLE;

-- Cortex Search Service
GRANT USAGE ON CORTEX SEARCH SERVICE LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS_SEARCH 
  TO ROLE MCP_USER_ROLE;

-- ---------------------------------------------------------------------------
-- Step 6: Grant SELECT on source tables (required for Semantic View resolution)
-- ---------------------------------------------------------------------------

-- Dimension tables
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.DIM_CUSTOMERS TO ROLE MCP_USER_ROLE;
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.DIM_VESSELS TO ROLE MCP_USER_ROLE;
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.DIM_PORTS TO ROLE MCP_USER_ROLE;
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.DIM_ROUTES TO ROLE MCP_USER_ROLE;

-- Fact tables
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENTS TO ROLE MCP_USER_ROLE;
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENT_EVENTS TO ROLE MCP_USER_ROLE;
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENT_PERFORMANCE TO ROLE MCP_USER_ROLE;

-- Unstructured data table
GRANT SELECT ON TABLE LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS TO ROLE MCP_USER_ROLE;

-- ---------------------------------------------------------------------------
-- Step 7: Grant the role to the user who will generate the PAT
-- ---------------------------------------------------------------------------
-- Replace <YOUR_USERNAME> with the actual Snowflake username

GRANT ROLE MCP_USER_ROLE TO USER <YOUR_USERNAME>;

-- ---------------------------------------------------------------------------
-- Verification
-- ---------------------------------------------------------------------------

SHOW GRANTS TO ROLE MCP_USER_ROLE;

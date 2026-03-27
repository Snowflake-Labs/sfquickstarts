/*=============================================================
  09 — Create MCP Server + OAuth Integration
  SUPPLY_CHAIN_MCP_SERVER — exposes Cortex Agent over SSE
  AMAZON_BEDROCK_MCP_OAUTH — OAuth for Amazon Quick Suite
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- ============================================================
-- 1. MCP Server
-- ============================================================

CREATE OR REPLACE MCP SERVER SUPPLY_CHAIN_MCP_SERVER
FROM SPECIFICATION $$
version: 1
tools:
  - title: "Supply Chain Intelligence Agent"
    name: "supply-chain-agent"
    identifier: "SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLY_CHAIN_AGENT"
    type: "CORTEX_AGENT_RUN"
    description: "Supply chain intelligence agent for the Supply and Inventory domain.
      Answers questions about suppliers (reliability scores, lead times, countries),
      products (categories, costs, prices), warehouses (capacity, locations),
      inventory (stock levels, reorder points, stockout risk), and purchase orders
      (delivery delays, costs, status). Also searches supplier emails and warehouse
      inspection notes. Send natural language questions directly."
$$;

-- ============================================================
-- 2. Account-level setting: allow privileged roles in OAuth
--    Required so ACCOUNTADMIN is not auto-blocked
-- ============================================================

ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE;

-- ============================================================
-- 3. OAuth Security Integration for Amazon Quick Suite
--    Update OAUTH_REDIRECT_URI if your Quick Suite region differs
-- ============================================================

CREATE OR REPLACE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://us-west-2.quicksight.aws.amazon.com/sn/oauthcallback'
  OAUTH_ISSUE_REFRESH_TOKENS = TRUE
  OAUTH_REFRESH_TOKEN_VALIDITY = 86400
  OAUTH_USE_SECONDARY_ROLES = 'IMPLICIT'
  BLOCKED_ROLES_LIST = ()
  ENABLED = TRUE;

-- ============================================================
-- 4. Retrieve OAuth credentials (run manually after creation)
--    Copy Client ID, Client Secret, Token URL, Authorization URL
--    into the Amazon Quick Suite MCP Actions integration settings.
-- ============================================================

-- Client ID + endpoints:
DESCRIBE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH;

-- Client Secret (contains OAUTH_CLIENT_SECRET and OAUTH_CLIENT_ID):
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('AMAZON_BEDROCK_MCP_OAUTH');

-- ============================================================
-- SSE Endpoint (replace <YOUR_ACCOUNT> with your account ID):
-- https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
--
-- For this account:
-- https://SFSEAPAC-BSURESH.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
--
-- Amazon Quick Suite Authentication Settings (for MCP Actions integration):
--   Authentication method:  User authentication
--   Authentication type:    Custom user based OAuth
--   Client ID:              (from DESCRIBE output → OAUTH_CLIENT_ID)
--   Client Secret:          (from SYSTEM$SHOW_OAUTH_CLIENT_SECRETS → OAUTH_CLIENT_SECRET)
--   Token URL:              https://sfseapac-bsuresh.snowflakecomputing.com/oauth/token-request
--   Authorization URL:      https://sfseapac-bsuresh.snowflakecomputing.com/oauth/authorize
--   Redirect URL:           https://us-west-2.quicksight.aws.amazon.com/sn/oauthcallback
-- ============================================================

-- Verify
SHOW MCP SERVERS IN SUPPLY_CHAIN_DEMO.PUBLIC;
DESCRIBE MCP SERVER SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLY_CHAIN_MCP_SERVER;
SHOW SECURITY INTEGRATIONS LIKE 'AMAZON_BEDROCK_MCP_OAUTH';

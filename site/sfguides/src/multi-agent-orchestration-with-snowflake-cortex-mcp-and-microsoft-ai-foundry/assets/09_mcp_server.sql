/*=============================================================
  09 — Create MCP Server
  SUPPLY_CHAIN_MCP_SERVER — exposes Cortex Agent over SSE
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

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
-- SSE Endpoint (replace <YOUR_ACCOUNT> with your account ID):
-- https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
--
-- For this account:
-- https://SFSEAPAC-BSURESH.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
-- ============================================================

-- Verify
SHOW MCP SERVERS IN SUPPLY_CHAIN_DEMO.PUBLIC;
DESCRIBE MCP SERVER SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLY_CHAIN_MCP_SERVER;

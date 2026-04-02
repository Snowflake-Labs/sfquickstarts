author: Bharath Suresh, Arun Prakash(Microsoft)
id: multi-agent-orchestration-with-snowflake-cortex-mcp-and-microsoft-ai-foundry
language: en
summary: Build a multi-agent orchestrator that routes natural language queries across Snowflake Cortex MCP and Microsoft Fabric through a unified AI Foundry agent, powered by Cortex Agents, Cortex Analyst, Cortex Search, MCP, and OAuth 2.0.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/multi-agent-orchestration-with-snowflake-cortex-mcp-and-microsoft-ai-foundry

# Multi-Agent Agentic Orchestrator with Snowflake Cortex MCP and Microsoft AI Foundry

<!-- -------------------------->
## Overview

Through this guide, you will build a multi-agent architecture that routes natural language queries across Snowflake and Microsoft Fabric through a unified AI Foundry orchestrator agent. Powered by Snowflake Cortex Agent, Cortex Analyst, Cortex Search, and the Model Context Protocol (MCP), the orchestrator answers supply chain questions by automatically selecting the right data source, structured tables via text-to-SQL, unstructured text via semantic search, or Fabric Lakehouse Delta table and combining results when a question spans both platforms.

### Prerequisites

- Snowflake account with ACCOUNTADMIN role (or equivalent) and Cortex features enabled
- Azure subscription with access to Microsoft AI Foundry
- Microsoft Fabric F2 with Fabric enabled
- Azure CLI installed and authenticated (`az login`) - for SDK-based agent creation (optional)
- Python 3.10+ (optional, for SDK-based agent creation)

### What You'll Learn

- Creating a Snowflake Cortex Agent with Cortex Analyst and Cortex Search tools
- Building a Semantic View to power natural-language-to-SQL queries
- Exposing a Cortex Agent over the Model Context Protocol (MCP) with OAuth 2.0
- Setting up a Microsoft Fabric Lakehouse with a Fabric Data Agent
- Configuring a Microsoft AI Foundry orchestrator agent that routes queries across Snowflake and Fabric

### What You'll Build

**A multi-agent supply chain intelligence system** with two data source tools orchestrated by a Microsoft AI Foundry agent:

- **Snowflake MCP Server** exposing a Cortex Agent with 3 sub-tools: Cortex Analyst (text-to-SQL across 5 structured tables), Supplier Email Search (RAG search over 200 supplier emails), and Inspection Search (RAG search over warehouse inspection notes)
- **Fabric Data Agent** with a Lakehouse containing freight cost records (60 rows) and customer return complaints (40 rows) in Delta tables
- **Cross-platform query routing** that automatically splits questions across both platforms, joins on `product_id`, and presents unified answers

**End result: A unified chat interface where users ask natural language questions about suppliers, inventory, purchase orders, shipping costs, and customer returns---and the orchestrator routes each question to the right data source automatically.**


<!-- ------------------------ -->
## Setup Snowflake Infrastructure

Navigate to <a href="https://app.snowflake.com/_deeplink/#/workspaces?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=multi-agent-supply-chain-orchestrator&utm_cta=developer-guides-deeplink" class="_deeplink">**Projects → Workspaces**</a> in Snowsight and create a new SQL worksheet. Run the following scripts **in order**.

### Step 1: Create Database and Warehouse

Run `assets/01_database_and_warehouse.sql`:

```sql
USE ROLE ACCOUNTADMIN;

-- Create the demo database
CREATE DATABASE IF NOT EXISTS SUPPLY_CHAIN_DEMO;

-- Create a dedicated warehouse (X-Small, auto-suspend after 60s)
CREATE WAREHOUSE IF NOT EXISTS SUPPLY_CHAIN_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE;

-- Set context
USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- Verify
SHOW DATABASES LIKE 'SUPPLY_CHAIN_DEMO';
SHOW WAREHOUSES LIKE 'SUPPLY_CHAIN_WH';
```

### Step 2: Create Tables

Run `assets/02_create_tables.sql` to create 8 tables and 1 internal stage:

| Category | Tables | Description |
|---|---|---|
| Structured (5) | `SUPPLIERS`, `PRODUCTS`, `WAREHOUSES`, `INVENTORY`, `PURCHASE_ORDERS` | Core supply chain data with foreign key relationships |
| Semi-structured (1) | `IOT_SENSOR_LOGS` | VARIANT column for JSON sensor readings |
| Unstructured (2) | `SUPPLIER_EMAILS`, `WAREHOUSE_INSPECTION_NOTES` | Free-text communications and inspection reports |
| Stage | `SEMANTIC_MODELS` | Internal stage for semantic model YAML files |

### Step 3: Load Structured Data

Run `assets/03_load_structured_data.sql` to load ~640 rows across the 5 structured tables:

| Table | Rows | Key Details |
|---|---|---|
| SUPPLIERS | 20 | Global suppliers across 4 regions; 4 have reliability scores below 0.7 |
| PRODUCTS | 50 | 9 categories (Raw Materials, Components, Electronics, etc.); product_id 1001-1050 |
| WAREHOUSES | 8 | US locations from Los Angeles to Miami |
| INVENTORY | 162 | ~30% at or below reorder point; critical items with days_of_supply <= 5 |
| PURCHASE_ORDERS | 200 | ~25% with delivery delays; low-reliability suppliers have 7-19 day delays |

### Step 4: Load Semi-Structured Data

Run `assets/04_load_semi_structured_data.sql` to load 180 JSON sensor readings into `IOT_SENSOR_LOGS` using `PARSE_JSON()`. Covers 3 warehouses with temperature, humidity, air quality, door, and motion sensor types.

### Step 5: Load Unstructured Data

Run `assets/05_load_unstructured_data.sql` to load free-text data:

| Table | Rows | Content |
|---|---|---|
| SUPPLIER_EMAILS | 200 | Communications about pricing, delays, quality issues, contract negotiations |
| WAREHOUSE_INSPECTION_NOTES | 170 | Facility inspection findings with ratings (Excellent to Critical) |

<!-- ------------------------ -->
## Create Cortex Search Services

Run `assets/06_cortex_search_services.sql` to create 2 Cortex Search services for semantic search over unstructured text:

```sql
USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- 1. SUPPLIER_COMMS_SEARCH --- search supplier emails
CREATE OR REPLACE CORTEX SEARCH SERVICE SUPPLIER_COMMS_SEARCH
  ON EMAIL_BODY
  ATTRIBUTES SUPPLIER_NAME, SUBJECT, DATE_SENT, SENDER, PRIORITY
  WAREHOUSE = SUPPLY_CHAIN_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT EMAIL_BODY, SUPPLIER_NAME, SUBJECT,
           DATE_SENT::VARCHAR AS DATE_SENT, SENDER, PRIORITY
    FROM SUPPLIER_EMAILS
  );

-- 2. WAREHOUSE_INSPECTIONS_SEARCH --- search inspection notes
CREATE OR REPLACE CORTEX SEARCH SERVICE WAREHOUSE_INSPECTIONS_SEARCH
  ON INSPECTION_NOTES
  ATTRIBUTES INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED
  WAREHOUSE = SUPPLY_CHAIN_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT INSPECTION_NOTES, INSPECTION_DATE::VARCHAR AS INSPECTION_DATE,
           INSPECTOR, OVERALL_RATING,
           FOLLOW_UP_REQUIRED::VARCHAR AS FOLLOW_UP_REQUIRED
    FROM WAREHOUSE_INSPECTION_NOTES
  );
```

> NOTE:
>
> Wait **2-3 minutes** after running this script for the search services to finish indexing before proceeding.

Verify:
```sql
SHOW CORTEX SEARCH SERVICES IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

<!-- ------------------------ -->
## Create Semantic View

Run `assets/07_semantic_view.sql` to create the `SUPPLY_CHAIN_ANALYTICS` semantic view using `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML()`. This powers Cortex Analyst text-to-SQL queries.

| Component | Count | Details |
|---|---|---|
| **Tables** | 5 | SUPPLIERS, PRODUCTS, WAREHOUSES, INVENTORY, PURCHASE_ORDERS |
| **Relationships** | 6 | Foreign key joins (Products->Suppliers, Inventory->Products, Inventory->Warehouses, PO->Suppliers, PO->Products, PO->Warehouses) |
| **Facts** | 14 | Numeric columns: quantities, costs, scores, lead times, delays, weights |
| **Dimensions** | 25 | Categorical columns: names, IDs, statuses, categories, regions |
| **Metrics** | 9 | AVG_RELIABILITY_SCORE, AVG_LEAD_TIME, TOTAL_STOCK_ON_HAND, AVG_DAYS_OF_SUPPLY, LOW_STOCK_ITEMS, TOTAL_PO_VALUE, AVG_DELAY_DAYS, TOTAL_ORDERS, ON_TIME_DELIVERY_RATE |
| **Filters** | 5 | LOW_RELIABILITY_SUPPLIERS, PERISHABLE_PRODUCTS, CRITICAL_STOCK, DELIVERED_ORDERS, DELAYED_ORDERS |
| **Verified Queries** | 3 | Suppliers with delivery delays, products at risk of stockout, on-time delivery rate by supplier |

<!-- ------------------------ -->
## Create Cortex Agent

Run `assets/08_cortex_agent.sql` to create `SUPPLY_CHAIN_AGENT` with 3 tools:

```sql
CREATE OR REPLACE AGENT SUPPLY_CHAIN_AGENT
  COMMENT = 'Supply chain intelligence agent combining structured data queries (Cortex Analyst) with unstructured text search (Cortex Search) across supplier communications and warehouse inspections.'
  FROM SPECIFICATION
  $$
  orchestration:
    budget:
      seconds: 60
      tokens: 16000

  instructions:
    system: >
      You are a supply chain intelligence assistant. You help users analyze
      supplier performance, inventory levels, purchase orders, and warehouse
      operations. You combine structured data analysis with unstructured
      text search across supplier emails and warehouse inspection notes.
      Shipments, delivery tracking, store sales, carrier data, and logistics
      incident reports are managed in Microsoft Fabric and are not available here.
    orchestration: >
      Use Analyst for questions about suppliers, products, inventory levels,
      purchase orders, costs, delays, and delivery rates.
      Use SupplierEmailSearch for questions about supplier communications,
      emails, negotiations, complaints, or correspondence.
      Use InspectionSearch for questions about warehouse inspections,
      facility conditions, compliance, or inspection findings.
      For logistics incidents, safety events, or disruptions, mention that
      this data is available in the Microsoft Fabric domain.
    response: >
      Provide concise, data-driven answers. When presenting numbers,
      include context and comparisons where possible. If data from
      Microsoft Fabric (shipments, sales, incidents) is needed, mention
      that it is available in the Fabric domain.
    sample_questions:
      - question: "Which suppliers have the worst on-time delivery rates?"
        answer: "I'll query the purchase orders data to calculate on-time delivery rates by supplier."
      - question: "What products are at risk of stockout?"
        answer: "I'll analyze current inventory levels against reorder points to identify at-risk items."
      - question: "Show me recent supplier complaints."
        answer: "I'll search supplier emails for recent complaints and quality issues."

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "Analyst"
        description: "Queries structured supply chain data including suppliers, products,
          warehouses, inventory levels, and purchase orders. Use for quantitative
          questions about costs, delays, stock levels, and delivery performance."
    - tool_spec:
        type: "cortex_search"
        name: "SupplierEmailSearch"
        description: "Searches supplier email communications for information about
          negotiations, complaints, updates, and correspondence with suppliers."
    - tool_spec:
        type: "cortex_search"
        name: "InspectionSearch"
        description: "Searches warehouse inspection notes for facility conditions,
          compliance findings, and maintenance issues."

  tool_resources:
    Analyst:
      semantic_view: "SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLY_CHAIN_ANALYTICS"
      execution_environment:
        type: "warehouse"
        warehouse: "SUPPLY_CHAIN_WH"
    SupplierEmailSearch:
      name: "SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLIER_COMMS_SEARCH"
      max_results: "5"
    InspectionSearch:
      name: "SUPPLY_CHAIN_DEMO.PUBLIC.WAREHOUSE_INSPECTIONS_SEARCH"
      max_results: "5"
  $$;
```

Verify:
```sql
SHOW AGENTS IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

<!-- ------------------------ -->
## Create MCP Server and OAuth Integration

Run `assets/09_mcp_server.sql` to expose the Cortex Agent over MCP with OAuth 2.0 authentication for Microsoft AI Foundry.

### MCP Server

```sql
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
```

### OAuth Security Integration

```sql
-- Allow privileged roles in OAuth
ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE;

-- Create OAuth security integration for AI Foundry
CREATE OR REPLACE SECURITY INTEGRATION foundry_mcp_oauth
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  ENABLED = TRUE
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://ai.azure.com/oauth/callback'
  OAUTH_ISSUE_REFRESH_TOKENS = TRUE
  OAUTH_REFRESH_TOKEN_VALIDITY = 86400
  OAUTH_USE_SECONDARY_ROLES = 'IMPLICIT'
  BLOCKED_ROLES_LIST = ();
```

### Retrieve OAuth Credentials

Save these values---you will need them when configuring Microsoft AI Foundry:

```sql
-- Client ID + endpoints:
DESCRIBE SECURITY INTEGRATION foundry_mcp_oauth;

-- Client Secret:
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('FOUNDRY_MCP_OAUTH');
```

**Cortex MCP Endpoint:**
```
https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
```

Replace `<YOUR_ACCOUNT>` with your Snowflake account identifier.

Verify:
```sql
SHOW MCP SERVERS IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

<!-- ------------------------ -->
## Setup Microsoft Fabric Lakehouse

Create a Fabric workspace with a Lakehouse containing supplementary freight cost and customer return datasets. Two CSV files are included in the `assets/` directory of the repository.

| File | Rows | Key Columns |
|---|---|---|
| `freight_costs.csv` | 60 | shipment_id, product_id (1001-1050), carrier_name, shipping_cost_usd, on_time |
| `customer_returns.csv` | 40 | return_id, product_id (1001-1050), reason_category, customer_complaint, refund_amount |

### Create a Fabric Workspace

1. Go to [https://app.fabric.microsoft.com](https://app.fabric.microsoft.com) and sign in
2. In the left navigation, select **Workspaces** > **New workspace**
3. Name it: `SupplyChainDemo`
4. Under **License mode**, select a capacity that supports Fabric (Trial, Premium, or Fabric F2+)
5. Click **Apply**

### Create a Lakehouse

1. Inside the `SupplyChainDemo` workspace, click **+ New item**
2. Search for **Lakehouse** and select it
3. Name it: `SupplyChainLakehouse`
4. Click **Create**
5. Wait for the Lakehouse to provision (~30 seconds)

### Upload CSV Files

1. In the Lakehouse explorer, click the **Files** folder
2. Click the **...** (ellipsis) menu next to **Files** > **New subfolder** > name it `supply_chain_data`
3. Click the **...** menu next to `supply_chain_data` > **Upload** > **Upload files**
4. Select both CSV files from the `fabric_csv/` directory and upload them

### Load CSV Files into Delta Tables

For each CSV file:

1. In the Lakehouse explorer, navigate to **Files** > `supply_chain_data`
2. Click the **...** menu next to each CSV file
3. Select **Load to Tables** > **New table**
4. Use the filename (without `.csv`) as the table name
5. Click **Load**

Repeat for both files: `freight_costs`, `customer_returns`

### Verify the Lakehouse Tables

1. In the Lakehouse explorer, expand **Tables** > **dbo** and confirm both tables appear
2. Click each table to preview data
3. Switch to **SQL analytics endpoint** (top-right dropdown) and run:

```sql
-- Verify freight costs
SELECT carrier_name, COUNT(*) AS shipment_count,
       AVG(shipping_cost_usd) AS avg_cost,
       SUM(CASE WHEN on_time = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS on_time_pct
FROM freight_costs
GROUP BY carrier_name
ORDER BY shipment_count DESC;

-- Verify customer returns
SELECT reason_category, COUNT(*) AS return_count,
       SUM(refund_amount) AS total_refunds,
       COUNT(DISTINCT product_id) AS products_affected
FROM customer_returns
GROUP BY reason_category
ORDER BY return_count DESC;
```

<!-- ------------------------ -->
## Create Fabric Data Agent

1. In the `SupplyChainDemo` workspace, click **+ New item**
2. Search for **Data Agent** and select **Fabric data agent** (Preview)
3. Name it: `sc_fabric_agent`
4. Click **Create**

### Add the Lakehouse as a Data Source

1. In the OneLake catalog that appears, find and select `SupplyChainLakehouse`
2. Click **Add**
3. In the Explorer pane, expand the lakehouse and select both tables:
   - `freight_costs`
   - `customer_returns`

### Add Data Agent Instructions

Click the **Data agent instructions** button (top right) and paste:

```
You are a Supply Chain Data Agent for freight cost and customer return data.

Data Source: SupplyChainLakehouse with two tables:

1. freight_costs --- Shipment-level freight records: shipment_id, product_id, carrier_name,
   origin_warehouse, destination_store, ship_date, shipping_cost_usd, weight_kg,
   distance_miles, on_time (Yes/No)
2. customer_returns --- Customer return records with complaint narratives: return_id,
   product_id, store_id, return_date, reason_category (Damaged in Transit / Quality Issue /
   Defective / Wrong Item / Changed Mind), customer_complaint (free-text narrative),
   refund_amount

Guidelines:
- For freight/shipping questions, query the freight_costs table
- For return/complaint questions, query the customer_returns table
- Use product_id to link records to Snowflake's product catalog (numeric IDs 1001-1050)
- Use store_id to link returns to specific stores (STR-xyz format)
- Use carrier_name to analyze carrier performance (FastFreight Logistics, TransGlobal
  Shipping, ExpressRoute Carriers, PrimeHaul Transport, SwiftMove Inc, Pacific Carriers
  Ltd, MidWest Express)
- The on_time column in freight_costs is Yes/No --- use it for on-time delivery rate calculations
- The customer_complaint column contains free-text narratives --- use LIKE for keyword searches
- When summarizing complaints, extract key details: what happened, product impact, and
  resolution requested
```

### Add Example Queries

Click **Example queries** and add these question-SQL pairs:

**Question 1:** Which carriers have the highest on-time delivery rate?
```sql
SELECT carrier_name, COUNT(*) AS total_shipments,
       SUM(CASE WHEN on_time = 'Yes' THEN 1 ELSE 0 END) AS on_time_count,
       SUM(CASE WHEN on_time = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS on_time_pct
FROM freight_costs
GROUP BY carrier_name
ORDER BY on_time_pct DESC
```

**Question 2:** What customer returns mention damaged or defective products?
```sql
SELECT return_id, return_date, product_id, store_id, reason_category,
       customer_complaint, refund_amount
FROM customer_returns
WHERE reason_category IN ('Damaged in Transit', 'Defective')
ORDER BY return_date DESC
```

**Question 3:** What is the average shipping cost by carrier?
```sql
SELECT carrier_name, COUNT(*) AS shipment_count,
       AVG(shipping_cost_usd) AS avg_cost,
       AVG(weight_kg) AS avg_weight,
       AVG(distance_miles) AS avg_distance
FROM freight_costs
GROUP BY carrier_name
ORDER BY avg_cost DESC
```

### Publish the Data Agent

1. Test the agent using the chat interface with sample questions:
   - "Which carrier has the best on-time delivery rate?"
   - "What are the most common return reasons?"
   - "Show me customer complaints about damaged products"
2. Click **Publish** in the top toolbar

<!-- ------------------------ -->
## Configure Microsoft AI Foundry Orchestrator

### Create an AI Foundry Project

1. Go to [https://ai.azure.com](https://ai.azure.com) (Microsoft Foundry portal)
2. Click **+ Create project** (or select an existing project)
3. Configure:
   - **Project name:** `SupplyChainOrchestrator`
   - **Region:** `East US 2` (recommended --- widest model availability)
   - **Resource group:** Create new or select existing
4. Click **Create**

### Deploy an OpenAI Model

1. In your Foundry project, go to **Models + endpoints** in the left navigation
2. Click **+ Deploy model** > **Deploy base model**
3. Search for and select your preferred model (e.g., **gpt-4o** or later)
4. Configure deployment:
   - **Deployment name:** `gpt-supply-chain` (or your preferred name)
   - **Deployment type:** Global Standard
   - **Tokens per minute rate limit:** Start with 30K (adjust based on usage)
5. Click **Deploy**
6. Note the **deployment name** --- you will need it when creating the agent

### Create the Orchestrator Agent

1. In your Foundry project, go to **Agents** in the left navigation
2. Click **+ New agent**
3. Configure:
   - **Name:** `SupplyChainOrchestrator`
   - **Model:** Select your deployed model
   - **Instructions:** Paste the full content from `assets/10_foundry_instructions.md` (see below)
4. Under **Tools**, you will add the Snowflake MCP Server and Fabric Data Agent in the next steps

**Orchestrator Instructions** (from `assets/10_foundry_instructions.md`):

```
You are a supply chain assistant with two data sources. Your job is to query BOTH sources
and combine the results.

You have two tools:
- snowflake-mcp-supplychain: inventory, suppliers, purchase orders, warehouses, products,
  supplier emails, warehouse inspections, IoT sensor logs
- sc_fabric_agent: freight costs/shipment data, customer returns with complaint narratives

These two tools have completely different data. One tool cannot answer for the other.

Snowflake (snowflake-mcp-supplychain) has STRUCTURED + UNSTRUCTURED data:
  - Suppliers, products, warehouses, inventory levels, purchase orders
  - Supplier emails (searchable)
  - Warehouse inspection notes (searchable)
  - IoT sensor logs

Fabric (sc_fabric_agent) has two tables:
  - freight_costs: shipment-level freight records with shipment_id, product_id, carrier_name,
    origin_warehouse, destination_store, ship_date, shipping_cost_usd, weight_kg,
    distance_miles, on_time (Yes/No)
  - customer_returns: return records with return_id, product_id, store_id, return_date,
    reason_category, customer_complaint (free-text narrative), refund_amount

Cross-platform join keys:
  - product_id: links Snowflake products/suppliers to Fabric freight costs and customer returns
  - carrier_name: Fabric freight_costs uses the same carrier names as referenced in Snowflake data
  - origin_warehouse / destination_store: city-based in Fabric, can be correlated with
    Snowflake warehouse data

For every user question, you must complete three phases before answering:

PHASE 1: Rewrite the question for each tool. Each tool should only be asked about data
it has. Always include linking IDs (product_id, store_id) in your request so results can
be joined later.

PHASE 2: Call both tools with their rewritten questions. You must call both tools before answering.

PHASE 3: Combine the results. Join on product_id (or other shared keys). Present one unified
answer showing data from both tools. Label which data came from which tool.

You are not allowed to answer the user until you have completed all three phases. If you
answer after calling only one tool, your answer is incomplete and wrong.

If one tool returns no results, still present the other tool's data and note the gap.
```

<!-- ------------------------ -->
## Add MCP Server and Fabric Tools to the Agent

### Add Snowflake MCP Server as a Tool

#### Create an OAuth Connection in AI Foundry

1. In your Foundry project, go to **Management** > **Connected resources** (or **Settings** > **Connections**)
2. Click **+ New connection**
3. Select **Custom** connection type
4. Configure:

| Setting | Value |
|---|---|
| **Name** | `snowflake-mcp-connection` |
| **Access** | Project-level |
| **Authentication type** | OAuth 2.0 |
| **Client ID** | From `DESCRIBE SECURITY INTEGRATION foundry_mcp_oauth` |
| **Client Secret** | From `SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('FOUNDRY_MCP_OAUTH')` |
| **Token endpoint** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/oauth/token-request` |
| **Authorization endpoint** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/oauth/authorize` |

5. Click **Save**

#### Add the MCP Server Tool

1. Go to your agent **SupplyChainOrchestrator**
2. Click **Tools** in the agent configuration
3. Click **+ Add tool** > **MCP Server**
4. Configure:
   - **Server label:** `supply-chain-snowflake`
   - **Server URL:** `https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER`
   - **Connection:** Select `snowflake-mcp-connection`
   - **Require approval:** `never` (for demo; use `always` in production)
5. Click **Save**

### Connect Fabric Data Agent

1. In your **SupplyChainOrchestrator** agent, click **Tools** > **+ Add tool**
2. Select **Fabric** from the available integrations
   - If Fabric appears as a connected service, select your workspace `SupplyChainDemo`
   - Select the `sc_fabric_agent`
3. Click **Add**

> NOTE:
>
> **Alternative --- A2A Protocol:** If direct Fabric integration is not available in your region, use the Agent-to-Agent (A2A) protocol: In **Tools** > **+ Add tool** > **A2A endpoint**, provide the Fabric Data Agent's endpoint URL and configure authentication via Entra ID.

Replace `<YOUR_ACCOUNT>` with your Snowflake account identifier in all URLs above.

<!-- ------------------------ -->
## Test the Multi-Agent Orchestrator

Open the AI Foundry agent chat interface and test queries across all routing paths.

### Snowflake-Routed Queries (via snowflake-mcp-supplychain)

Copy and paste these into the chat agent:

```
Which suppliers have reliability scores below 0.7?
```

This tests the Cortex Analyst tool, querying the SUPPLIERS table through the semantic view.

```
What products are at risk of stockout in the next 5 days?
```

This tests a multi-table join through Cortex Analyst (INVENTORY + PRODUCTS + WAREHOUSES) using the CRITICAL_STOCK filter.

```
Search supplier emails about quality complaints
```

This tests the SupplierEmailSearch tool, performing semantic search over the SUPPLIER_EMAILS table.

```
Show me warehouse inspection reports with Poor ratings
```

This tests the InspectionSearch tool, searching WAREHOUSE_INSPECTION_NOTES for low-rated facilities.

### Fabric-Routed Queries (via sc_fabric_agent)

```
Which carriers have the highest average shipping costs?
```

This queries the freight_costs Delta table for carrier cost comparisons.

```
What are the most common reasons for customer returns?
```

This queries the customer_returns Delta table, grouping by reason_category.

```
Show me customer complaints about defective products
```

This searches the free-text customer_complaint column in the returns data.

### Cross-Platform Queries (Both Tools)

```
Need information on products which has high freight cost
```

Which carriers cause maximum delys and what products do they handle?

```
Which suppliers produce products with the highest return rates?
```

The agent should call Fabric for return counts by product_id and Snowflake for the supplier-product-reliability mapping, combining results into a single answer.

| Query Type | Tool | Data Source |
|---|---|---|
| Inventory, suppliers, POs | snowflake-mcp-supplychain | Snowflake Cortex Agent |
| Supplier emails, inspections | snowflake-mcp-supplychain | Snowflake Cortex Search |
| Freight costs, carrier performance | sc_fabric_agent | Fabric Lakehouse |
| Customer returns, complaints | sc_fabric_agent | Fabric Lakehouse |
| Cross-platform analysis | Both tools | Snowflake + Fabric |

<!-- ------------------------ -->
## Cleanup

To remove all resources created by this guide:

**Snowflake:**
```sql
DROP DATABASE IF EXISTS SUPPLY_CHAIN_DEMO;
DROP WAREHOUSE IF EXISTS SUPPLY_CHAIN_WH;
DROP SECURITY INTEGRATION IF EXISTS foundry_mcp_oauth;
ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = TRUE;
```

**Microsoft Fabric:**
- Delete the `sc_fabric_agent` data agent
- Delete the `SupplyChainLakehouse` lakehouse
- Delete the `SupplyChainDemo` workspace

**Microsoft AI Foundry:**
- Delete the `SupplyChainOrchestrator` agent
- Delete the model deployment
- Delete the project (if no longer needed)

<!-- ------------------------ -->
## Conclusion

Congratulations! You've built a multi-agent supply chain intelligence orchestrator.

### What You Accomplished

- Created a Snowflake Cortex Agent combining text-to-SQL and semantic search across 8 tables and ~870 rows of data
- Built a Semantic View with 9 metrics, 5 filters, and 3 verified queries for Cortex Analyst
- Exposed the Cortex Agent over MCP with OAuth 2.0 authentication
- Set up a Microsoft Fabric Lakehouse with freight and customer returns data
- Created a Fabric Data Agent with NL2SQL over Delta tables
- Built an AI Foundry orchestrator agent that routes queries to the right data source automatically
- Tested cross-platform queries that combine Snowflake and Fabric results via product_id joins

### What You Learned

- Setting up Cortex Search services for semantic search over unstructured text
- Building Semantic Views with metrics, filters, and verified queries for Cortex Analyst
- Creating Cortex Agents with multiple tool types (Analyst + Search)
- Exposing agents via MCP Server with OAuth 2.0 security integrations
- Creating Fabric Lakehouses and Data Agents for supplementary datasets
- Orchestrating cross-platform queries through Microsoft AI Foundry

### Related Resources

- [Snowflake Managed MCP Server Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [Snowflake Cortex Agent Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake OAuth for Custom Clients](https://docs.snowflake.com/en/user-guide/oauth-custom)
- [Microsoft AI Foundry Agent Quickstart](https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code)
- [AI Foundry: Connect to MCP Servers](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol)
- [Create a Fabric Data Agent](https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent)
- [Create a Fabric Lakehouse](https://learn.microsoft.com/en-us/fabric/data-engineering/tutorial-build-lakehouse)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)

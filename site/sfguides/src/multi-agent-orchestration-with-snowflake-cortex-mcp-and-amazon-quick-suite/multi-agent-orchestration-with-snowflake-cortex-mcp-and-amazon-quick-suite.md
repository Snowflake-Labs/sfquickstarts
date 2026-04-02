author: Bharath Suresh, Avinash Venkatagiri(AWS)
id: multi-agent-orchestration-with-snowflake-cortex-mcp-and-amazon-quick-suite
language: en
summary: Build a multi-agent orchestrator that routes natural language queries across Snowflake and Amazon S3 through a unified Amazon Quick Suite chat agent, powered by Cortex Agent, MCP, and OAuth 2.0.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-multi-agent-supply-chain-orchestrator


# Multi-Agent Supply Chain Orchestrator with Snowflake Cortex MCP and Amazon Quick Suite

<!-- ------------------------ -->
## Overview

Through this guide, you will build a multi-agent architecture that routes natural language queries across Snowflake and Amazon S3 through a unified Amazon Quick Suite chat agent. Powered by Snowflake Cortex Agent, Cortex Analyst, Cortex Search, and the Model Context Protocol (MCP), the orchestrator answers supply chain questions by automatically selecting the right data source---structured tables via text-to-SQL, unstructured text via semantic search, or CSV knowledge bases in S3---and combining results when a question spans both platforms.

### Prerequisites

- Snowflake account with ACCOUNTADMIN role (or equivalent) and Cortex features enabled
- AWS account with access to Amazon S3 and Amazon Quick Suite
- Amazon Quick Suite Professional ($20/user/month) or Enterprise ($40/user/month) subscription

### What You'll Learn

- Creating a Snowflake Cortex Agent with Cortex Analyst and Cortex Search tools
- Building a Semantic View to power natural-language-to-SQL queries
- Exposing a Cortex Agent over the Model Context Protocol (MCP) with OAuth 2.0
- Configuring an Amazon Quick Suite chat agent that orchestrates across Snowflake and S3

### What You'll Need

- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account
- An AWS account with S3 and Quick Suite access
- The repository files including SQL setup scripts, CSV data files, and agent instructions

### What You'll Build

**A multi-agent supply chain intelligence system** with two data source tools orchestrated by an Amazon Quick Suite chat agent:

- **Snowflake MCP Server** exposing a Cortex Agent with 3 sub-tools: Cortex Analyst (text-to-SQL across 5 structured tables), SupplierEmailSearch (semantic search over 200 supplier emails), and InspectionSearch (semantic search over 170 warehouse inspection notes)
- **Amazon S3 Knowledge Base** containing freight cost records (60 rows) and customer return complaints (40 rows)
- **Cross-platform query routing** that automatically splits questions across both platforms and joins results on `product_id`

**End result:** A unified chat interface where users ask natural language questions about suppliers, inventory, purchase orders, shipping costs, and customer returns---and the orchestrator routes each question to the right data source automatically.

<!-- ------------------------ -->
## Setup Snowflake Infrastructure

Navigate to <a href="https://app.snowflake.com/_deeplink/#/workspaces?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=multi-agent-supply-chain-orchestrator&utm_cta=developer-guides-deeplink" class="_deeplink">**Projects → Workspaces**</a> in Snowsight and create a new SQL worksheet. Run the following scripts **in order**.

> NOTE:
>
> All scripts use the `ACCOUNTADMIN` role. The data is loaded via INSERT statements---no external staging required for the Snowflake side.

### Step 1: Create Database and Warehouse

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

Run `setup/02_create_tables.sql` to create 8 tables and 1 internal stage:

| Category | Tables | Description |
|---|---|---|
| Structured (5) | `SUPPLIERS`, `PRODUCTS`, `WAREHOUSES`, `INVENTORY`, `PURCHASE_ORDERS` | Core supply chain data with foreign key relationships |
| Semi-structured (1) | `IOT_SENSOR_LOGS` | VARIANT column for JSON sensor readings |
| Unstructured (2) | `SUPPLIER_EMAILS`, `WAREHOUSE_INSPECTION_NOTES` | Free-text communications and inspection reports |
| Stage | `SEMANTIC_MODELS` | Internal stage for semantic model YAML files |

### Step 3: Load Structured Data

Run `setup/03_load_structured_data.sql` to load ~640 rows across the 5 structured tables:

| Table | Rows | Key Details |
|---|---|---|
| SUPPLIERS | 20 | Global suppliers across 4 regions; 4 have reliability scores below 0.7 |
| PRODUCTS | 50 | 9 categories (Raw Materials, Components, Electronics, etc.); product_id 1001-1050 |
| WAREHOUSES | 8 | US locations from Los Angeles to Miami |
| INVENTORY | 162 | ~30% at or below reorder point; critical items with days_of_supply <= 5 |
| PURCHASE_ORDERS | 200 | ~25% with delivery delays; low-reliability suppliers have 7-19 day delays |

### Step 4: Load Semi-Structured Data

Run `setup/04_load_semi_structured_data.sql` to load 180 JSON sensor readings into `IOT_SENSOR_LOGS`. Covers 3 warehouses with temperature, humidity, air quality, door, and motion sensor types.

> NOTE:
>
> Snowflake does not allow scalar functions like `PARSE_JSON()` directly inside a `VALUES` clause. The script uses the pattern `SELECT $1, $2, PARSE_JSON($3) FROM VALUES (...)` to apply the function after the literal values are bound.

> NOTE:
>
> IoT sensor data is loaded for completeness but is **not exposed** through the Cortex Agent tools. The agent will mention its existence if asked.

### Step 5: Load Unstructured Data

Run `setup/05_load_unstructured_data.sql` to load free-text data:

| Table | Rows | Content |
|---|---|---|
| SUPPLIER_EMAILS | 200 | Communications about pricing, delays, quality issues, contract negotiations |
| WAREHOUSE_INSPECTION_NOTES | 170 | Facility inspection findings with ratings (Excellent to Critical) |

<!-- ------------------------ -->
## Create Cortex Search Services

Run `setup/06_cortex_search_services.sql` to create 2 Cortex Search services for semantic search over unstructured text:

```sql
USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- 1. SUPPLIER_COMMS_SEARCH — search supplier emails
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

-- 2. WAREHOUSE_INSPECTIONS_SEARCH — search inspection notes
CREATE OR REPLACE CORTEX SEARCH SERVICE WAREHOUSE_INSPECTIONS_SEARCH
  ON INSPECTION_NOTES
  ATTRIBUTES INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED
  WAREHOUSE = SUPPLY_CHAIN_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT INSPECTION_NOTES, INSPECTION_DATE::VARCHAR AS INSPECTION_DATE,
           INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED::VARCHAR AS FOLLOW_UP_REQUIRED
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

Run `setup/07_semantic_view.sql` to create the `SUPPLY_CHAIN_ANALYTICS` semantic view using `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML()`. This powers Cortex Analyst text-to-SQL queries.

| Component | Count | Details |
|---|---|---|
| **Tables** | 5 | SUPPLIERS, PRODUCTS, WAREHOUSES, INVENTORY, PURCHASE_ORDERS |
| **Relationships** | 5 | Foreign key joins (Products→Suppliers, Inventory→Products, Inventory→Warehouses, PO→Suppliers, PO→Products) |
| **Facts** | 20 | Numeric columns: quantities, costs, scores, lead times, delays, weights |
| **Dimensions** | 38 | Categorical columns: names, IDs, statuses, categories, regions |
| **Metrics** | 9 | AVG_RELIABILITY_SCORE, AVG_LEAD_TIME, TOTAL_STOCK_ON_HAND, AVG_DAYS_OF_SUPPLY, CRITICAL_STOCK_ITEMS, TOTAL_PO_VALUE, AVG_DELAY_DAYS, TOTAL_ORDERS, ON_TIME_DELIVERY_RATE |
| **Filters** | 5 | LOW_RELIABILITY_SUPPLIERS, PERISHABLE_PRODUCTS, CRITICAL_STOCK, DELIVERED_ORDERS, DELAYED_ORDERS |
| **Verified Queries** | 3 | Suppliers with delivery delays, products at risk of stockout, on-time delivery rate by supplier |

<!-- ------------------------ -->
## Create Cortex Agent

Run `setup/08_cortex_agent.sql` to create `SUPPLY_CHAIN_AGENT` with 3 tools:

```sql
CREATE OR REPLACE AGENT SUPPLY_CHAIN_AGENT
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
    orchestration: >
      Use Analyst for questions about suppliers, products, inventory levels,
      purchase orders, costs, delays, and delivery rates.
      Use SupplierEmailSearch for questions about supplier communications,
      emails, negotiations, complaints, or correspondence.
      Use InspectionSearch for questions about warehouse inspections,
      facility conditions, compliance, or inspection findings.
    response: >
      Provide concise, data-driven answers. When presenting numbers,
      include context and comparisons where possible. If data from
      Amazon S3 (freight costs, customer returns) is needed, mention
      that it is available in the S3 knowledge base.

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "Analyst"
        description: "Queries structured supply chain data including suppliers, products,
          warehouses, inventory levels, and purchase orders."
    - tool_spec:
        type: "cortex_search"
        name: "SupplierEmailSearch"
        description: "Searches supplier email communications for information about
          negotiations, complaints, updates, and correspondence."
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

Run `setup/09_mcp_server.sql` to expose the Cortex Agent over MCP with OAuth 2.0 authentication for Amazon Quick Suite.

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
    description: "Supply chain intelligence agent for the Supply and Inventory domain."
$$;
```

### OAuth Security Integration

```sql
-- Allow privileged roles in OAuth
ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE;

-- Create OAuth integration for Amazon Quick Suite
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
```

> NOTE:
>
> Update the region in `OAUTH_REDIRECT_URI` (`us-west-2`) to match your Quick Suite region if needed.

### Retrieve OAuth Credentials

Save these values---you will need them when configuring Amazon Quick Suite:

```sql
-- Client ID + endpoints:
DESCRIBE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH;

-- Client Secret:
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('AMAZON_BEDROCK_MCP_OAUTH');
```

**SSE Endpoint:**
```
https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
```

Replace `<YOUR_ACCOUNT>` with your Snowflake account identifier.

Verify:
```sql
SHOW MCP SERVERS IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

<!-- ------------------------ -->
## Setup Amazon S3 Knowledge Base

Upload the supplementary CSV files to S3 for the Quick Suite Knowledge Base. These files are in the `assets/` directory of the repository.

| File | Rows | Key Columns |
|---|---|---|
| `freight_costs.csv` | 60 | shipment_id, product_id (1001-1050), carrier_name, shipping_cost_usd, on_time |
| `customer_returns.csv` | 40 | return_id, product_id (1001-1050), reason_category, customer_complaint, refund_amount |

### Upload to S3

1. Go to **Amazon S3** > **Buckets** > **Create bucket**
2. Name the bucket (e.g., `supply-chain-demo-data`) and select your preferred region
3. Keep default settings and click **Create bucket**
4. Open the bucket, click **Upload**, add both CSV files from `assets/`, and click **Upload**

Or via AWS CLI:
```bash
aws s3 mb s3://supply-chain-demo-data --region us-west-2
aws s3 cp assets/freight_costs.csv s3://supply-chain-demo-data/
aws s3 cp assets/customer_returns.csv s3://supply-chain-demo-data/
```

### Create Quick Suite Knowledge Base

1. Open Amazon Quick Suite console
2. Navigate to **Knowledge Bases** > **Create knowledge base**
3. Configure:
   - **Name:** `supply_chain_space_s3`
   - **Description:** "Freight costs and customer returns data for supply chain analysis"
   - **Data source:** Amazon S3
   - **S3 bucket:** `supply-chain-demo-data`
   - **Files:** Select both CSV files
4. Click **Create** and wait for indexing to complete

> NOTE:
>
> The knowledge base name `supply_chain_space_s3` must match what is referenced in the agent instructions (`setup/10_quicksuite_instructions.md`). If you use a different name, update the instructions accordingly.

<!-- ------------------------ -->
## Configure Amazon Quick Suite Chat Agent

### Add Snowflake MCP Actions Integration

1. In Amazon Quick Suite, go to **Integrations** > **Actions** tab > **Create new integration**
2. Select **Model Context Protocol** as the integration type
3. Configure:
   - **Name:** `snowflake-mcp-supply-chain`
   - **MCP Server URL:** The SSE endpoint from the previous step
4. Configure OAuth authentication with the credentials from `DESCRIBE SECURITY INTEGRATION`:

| Setting | Value |
|---|---|
| **Client ID** | From `DESCRIBE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH` |
| **Client Secret** | From `SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('AMAZON_BEDROCK_MCP_OAUTH')` |
| **Token URL** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/oauth/token-request` |
| **Authorization URL** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/oauth/authorize` |

5. Click **Create**---Quick Suite will discover the `supply-chain-agent` tool

### Create a Space for S3 Data

1. Navigate to **Spaces** > **Create space**
2. **Name:** `Supply Chain S3 Data`
3. **Data sources:** Select the `supply_chain_space_s3` knowledge base
4. Click **Create**

### Create the Chat Agent

1. Navigate to **Chat Agents** > **Create agent**
2. **Name:** `SupplyChainOrchestrator`
3. **Description:** "Multi-agent orchestrator for supply chain data across Snowflake and S3"
4. Add both tools:

| Tool | Type | Source |
|---|---|---|
| `supply-chain-agent` | MCP Actions Integration | Snowflake MCP Server |
| `supply_chain_space_s3` | Knowledge Base | S3 Knowledge Base |

5. In the **Instructions** field, paste the full content from `setup/10_quicksuite_instructions.md`---this contains routing rules, schema details, and the three-phase protocol for cross-platform queries
6. Click **Create**

<!-- ------------------------ -->
## Test the Multi-Agent Orchestrator

Open the Quick Suite chat agent interface and test queries across all routing paths.

### Snowflake-Routed Queries (via supply-chain-agent)

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

### S3-Routed Queries (via supply_chain_space_s3)

```
Which carriers have the highest average shipping costs?
```

This queries the freight_costs.csv knowledge base for carrier cost comparisons.

```
What are the most common reasons for customer returns?
```

This queries the customer_returns.csv knowledge base, grouping by reason_category.

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

The agent should call S3 for return counts by product_id and Snowflake for the supplier-product mapping, combining results into a single answer.

<!-- ------------------------ -->
## Cleanup

To remove all resources created by this guide:

**Snowflake:**
```sql
DROP DATABASE IF EXISTS SUPPLY_CHAIN_DEMO;
DROP WAREHOUSE IF EXISTS SUPPLY_CHAIN_WH;
DROP SECURITY INTEGRATION IF EXISTS AMAZON_BEDROCK_MCP_OAUTH;
ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = TRUE;
```

**Amazon S3:**
- Delete all objects in your S3 bucket (e.g., `supply-chain-demo-data`), then delete the bucket

**Amazon Quick Suite:**
- Delete the `SupplyChainOrchestrator` chat agent
- Delete the `snowflake-mcp-supply-chain` Actions integration
- Delete the `supply_chain_space_s3` knowledge base
- Delete any Spaces created for this demo

<!-- ------------------------ -->
## Conclusion

Congratulations! You've built a multi-agent supply chain intelligence orchestrator.

### What You Accomplished

- Created a Snowflake Cortex Agent combining text-to-SQL and semantic search across 8 tables and 1,090 rows of data
- Exposed the agent over MCP with OAuth 2.0 authentication
- Connected an Amazon S3 knowledge base with freight and returns data
- Built a Quick Suite chat agent that routes queries to the right data source automatically
- Tested cross-platform queries that combine Snowflake and S3 results

### What You Learned

- Setting up Cortex Search services for semantic search over unstructured text
- Building Semantic Views with metrics, filters, and verified queries for Cortex Analyst
- Creating Cortex Agents with multiple tool types (Analyst + Search)
- Exposing agents via MCP Server with OAuth 2.0 security integrations
- Orchestrating cross-platform queries through Amazon Quick Suite

### Related Resources

- [Snowflake Managed MCP Server Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [Snowflake Cortex Agent Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake OAuth for Custom Clients](https://docs.snowflake.com/en/user-guide/oauth-custom)
- [Amazon Quick Suite MCP Integration](https://aws.amazon.com/blogs/machine-learning/connect-amazon-quick-suite-to-enterprise-apps-and-agents-with-mcp/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)

<div align="center">

# Multi-Agent Orchestrator

### Snowflake Cortex MCP + Amazon S3 + Amazon Quick Suite

[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)](https://www.snowflake.com)
[![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white)](https://aws.amazon.com/s3/)
[![Amazon Quick Suite](https://img.shields.io/badge/Amazon_Quick_Suite-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/quick/)

[![MCP Protocol](https://img.shields.io/badge/MCP-Model_Context_Protocol-00ADD8?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJMMiA3bDEwIDUgMTAtNS0xMC01ek0yIDE3bDEwIDUgMTAtNS0xMC01LTEwIDV6TTIgMTJsMTAgNSAxMC01LTEwLTUtMTAgNXoiLz48L3N2Zz4=)](https://modelcontextprotocol.io)
[![Cortex Agent](https://img.shields.io/badge/Cortex-Agent_|_Analyst_|_Search-29B5E8?style=flat-square)](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
[![OAuth 2.0](https://img.shields.io/badge/Auth-OAuth_2.0-EB5424?style=flat-square&logo=auth0&logoColor=white)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

**A production-ready multi-agent architecture that routes natural language queries across
Snowflake and Amazon S3 through a unified Amazon Quick Suite chat agent.**

[Get Started](#-quick-start) | [Architecture](#-architecture) | [Setup Guide](#-phase-1-snowflake-setup-scripts-0109) | [Testing](#-phase-4-testing--validation) | [Troubleshooting](#-troubleshooting)

</div>

---

## Highlights

| | Feature | Description |
|---|---|---|
| <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="20"> | **Cortex Agent** | Text-to-SQL via Cortex Analyst + semantic search via 2 Cortex Search services |
| <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="20"> | **MCP Server** | Exposes the Cortex Agent over the Model Context Protocol (SSE) with OAuth 2.0 |
| <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="20"> | **S3 Knowledge Base** | CSV-based knowledge base with freight costs and customer returns data |
| <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="20"> | **Quick Suite Chat Agent** | Orchestrator agent that routes queries to the right data source |
| | **Cross-Platform Queries** | Single question can pull data from both Snowflake and S3 simultaneously |

---

## Architecture

```
                    ┌─────────────────────────┐
                    │   User (Quick Suite      │
                    │   Chat / Dashboard)      │
                    └────────┬────────────────┘
                             │
                    ┌────────▼────────────────┐
                    │  Amazon Quick Suite      │
                    │  Chat Agent              │
                    │  (Orchestrator)          │
                    └────┬──────────┬─────────┘
                         │          │
            ┌────────────▼──┐  ┌───▼─────────────┐
            │  Snowflake    │  │  Amazon S3       │
            │  MCP Server   │  │  Knowledge Base  │
            │  (SSE+OAuth)  │  │                  │
            └───────┬───────┘  └───┬──────────────┘
                    │              │
        ┌───────────▼──┐    ┌─────▼────────────┐
        │ Cortex Agent │    │ S3 CSV Files      │
        │ - Analyst    │    │ - freight_costs   │
        │ - Search x2  │    │ - customer_returns│
        └──────────────┘    └──────────────────┘
```

| Layer | Platform | Purpose |
|---|---|---|
| **Quick Suite Chat Agent** | <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="14"> Amazon Quick Suite | Routes user questions to the right data source |
| **Snowflake MCP Server** | <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="14"> Snowflake | Exposes Cortex Agent as an MCP tool over SSE with OAuth 2.0 |
| **Cortex Agent** | <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="14"> Snowflake | Orchestrates Cortex Analyst (SQL) + 2 Cortex Search services |
| **S3 Knowledge Base** | <img src="https://img.shields.io/badge/-569A31?style=flat-square&logo=amazons3&logoColor=white" height="14"> Amazon S3 | CSV-based knowledge base for freight costs and customer returns |

---

## Quick Start

> **16 steps across 4 phases — from zero to a working multi-agent orchestrator.**

| Phase | Platform | Steps | What You Build |
|:---:|---|---|---|
| **1** | <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="16"> Snowflake | Steps 1–9 | Database, tables, data, Cortex Search, Semantic View, Agent, MCP Server + OAuth |
| **2** | <img src="https://img.shields.io/badge/-569A31?style=flat-square&logo=amazons3&logoColor=white" height="16"> S3 + Quick Suite | Steps 10–12 | S3 bucket, CSV upload, Quick Suite Knowledge Base |
| **3** | <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="16"> Quick Suite | Steps 13–15 | Snowflake MCP connection, Quick Suite Chat Agent creation |
| **4** | All | Step 16 | End-to-end testing across all platforms |

---

## Prerequisites

| Requirement | Details |
|---|---|
| <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="14"> **Snowflake account** | With ACCOUNTADMIN role (or equivalent) and Cortex features enabled |
| <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="14"> **AWS account** | With access to Amazon S3 and Amazon Quick Suite |
| <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="14"> **Amazon Quick Suite** | Professional ($20/user/month) or Enterprise ($40/user/month) subscription |

---

## Repository Structure

```
.
├── README.md                                   # Project overview
├── S3_csvs/                                    # CSV files for S3 Knowledge Base
│   ├── freight_costs.csv                       # Shipping cost records (60 rows)
│   └── customer_returns.csv                    # Customer returns with complaint text (40 rows)
└── setup/
    ├── 00_README.md                            # Setup guide (this file)
    ├── 01_database_and_warehouse.sql           # Phase 1, Step 1
    ├── 02_create_tables.sql                    # Phase 1, Step 2
    ├── 03_load_structured_data.sql             # Phase 1, Step 3
    ├── 04_load_semi_structured_data.sql        # Phase 1, Step 4
    ├── 05_load_unstructured_data.sql           # Phase 1, Step 5
    ├── 06_cortex_search_services.sql           # Phase 1, Step 6
    ├── 07_semantic_view.sql                    # Phase 1, Step 7
    ├── 08_cortex_agent.sql                     # Phase 1, Step 8
    ├── 09_mcp_server.sql                       # Phase 1, Step 9 (MCP Server + OAuth)
    └── 10_quicksuite_instructions.md           # Phase 3, Step 15 (chat agent instructions)
```

---

<div align="center">

## <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="28"> Phase 1: Snowflake Setup (Scripts 01–09)

*Run these SQL scripts **in order** in a Snowflake worksheet or via SnowSQL.*

</div>

---

### Step 1 — Create Database and Warehouse

> **Script:** `setup/01_database_and_warehouse.sql`

Creates:
- **Database:** `SUPPLY_CHAIN_DEMO`
- **Warehouse:** `SUPPLY_CHAIN_WH` (X-Small, auto-suspend 60 seconds)

```sql
-- Key commands in the script:
CREATE OR REPLACE DATABASE SUPPLY_CHAIN_DEMO;
CREATE OR REPLACE WAREHOUSE SUPPLY_CHAIN_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;
```

Run the full script, then confirm:
```sql
SHOW DATABASES LIKE 'SUPPLY_CHAIN_DEMO';
SHOW WAREHOUSES LIKE 'SUPPLY_CHAIN_WH';
```

---

### Step 2 — Create Tables

> **Script:** `setup/02_create_tables.sql`

Creates 8 tables across three categories and a stage for semantic models:

<details>
<summary><b>Structured Tables (5)</b> — click to expand</summary>

| Table | Key Columns | Notes |
|---|---|---|
| `SUPPLIERS` | SUPPLIER_ID (PK), SUPPLIER_NAME, COUNTRY, RELIABILITY_SCORE, CONTACT_EMAIL | 20 global suppliers |
| `PRODUCTS` | PRODUCT_ID (PK), PRODUCT_NAME, CATEGORY, SUPPLIER_ID (FK), SHELF_LIFE_DAYS | 50 products across 9 categories |
| `WAREHOUSES` | WAREHOUSE_ID (PK), WAREHOUSE_NAME, CITY, STATE, CAPACITY_SQFT, MANAGER_NAME | 8 US warehouses |
| `INVENTORY` | INVENTORY_ID (auto), PRODUCT_ID, WAREHOUSE_ID, QUANTITY_ON_HAND, REORDER_POINT | 162 stock records |
| `PURCHASE_ORDERS` | PO_ID (PK), SUPPLIER_ID, PRODUCT_ID, ORDER_QTY, DELAY_DAYS, WAREHOUSE_ID | 200 orders |

</details>

<details>
<summary><b>Semi-Structured Table (1)</b> — VARIANT column with JSON</summary>

| Table | Key Columns | Notes |
|---|---|---|
| `IOT_SENSOR_LOGS` | LOG_ID (auto), WAREHOUSE_ID, SENSOR_PAYLOAD (VARIANT) | 180 temperature/humidity readings |

</details>

<details>
<summary><b>Unstructured Tables (2)</b> — Free text</summary>

| Table | Key Columns | Notes |
|---|---|---|
| `SUPPLIER_EMAILS` | EMAIL_ID (PK), SUPPLIER_ID, SUBJECT, EMAIL_BODY | 200 supplier communications |
| `WAREHOUSE_INSPECTION_NOTES` | INSPECTION_ID (PK), WAREHOUSE_ID, INSPECTION_NOTES, OVERALL_RATING | 170 inspection findings |

</details>

Also creates:
```sql
CREATE OR REPLACE STAGE SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE);
```

---

### Step 3 — Load Structured Data

> **Script:** `setup/03_load_structured_data.sql`

Loads ~640 rows across the 5 structured tables:

| Table | Row Count |
|---|---|
| SUPPLIERS | 20 |
| PRODUCTS | 50 |
| WAREHOUSES | 8 |
| INVENTORY | 162 |
| PURCHASE_ORDERS | 200 |

---

### Step 4 — Load Semi-Structured Data

> **Script:** `setup/04_load_semi_structured_data.sql`

Loads JSON data using `PARSE_JSON()` into VARIANT columns:

| Table | Row Count |
|---|---|
| IOT_SENSOR_LOGS | 180 |

```sql
-- Example insert pattern:
INSERT INTO IOT_SENSOR_LOGS (WAREHOUSE_ID, SENSOR_TIMESTAMP, SENSOR_PAYLOAD)
SELECT 'WH-001', '2025-01-15 06:00:00',
  PARSE_JSON('{"sensor_id":"TEMP-001","temperature_f":38.2,"humidity_pct":45,...}');
```

---

### Step 5 — Load Unstructured Data

> **Script:** `setup/05_load_unstructured_data.sql`

| Table | Row Count | Content |
|---|---|---|
| SUPPLIER_EMAILS | 200 | Communications about pricing, delays, quality issues |
| WAREHOUSE_INSPECTION_NOTES | 170 | Facility inspection findings and ratings |

---

### Step 6 — Create Cortex Search Services

> **Script:** `setup/06_cortex_search_services.sql`

Creates 2 Cortex Search services for semantic search over unstructured text:

| Service Name | Source Table | Search Column | Attributes |
|---|---|---|---|
| `SUPPLIER_COMMS_SEARCH` | SUPPLIER_EMAILS | EMAIL_BODY | SUPPLIER_ID, SUBJECT, EMAIL_DATE |
| `WAREHOUSE_INSPECTIONS_SEARCH` | WAREHOUSE_INSPECTION_NOTES | INSPECTION_NOTES | WAREHOUSE_ID, INSPECTOR_NAME, OVERALL_RATING |

All services use warehouse `SUPPLY_CHAIN_WH` with `TARGET_LAG = '1 hour'`.

> [!IMPORTANT]
> Wait **2–3 minutes** after running this script for the search services to finish indexing before testing.

```sql
-- Verify:
SHOW CORTEX SEARCH SERVICES IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

---

### Step 7 — Create Semantic View

> **Script:** `setup/07_semantic_view.sql`

Creates the semantic view `SUPPLY_CHAIN_ANALYTICS` using the Cortex Analyst (CA) extension. This is what powers natural-language-to-SQL queries.

| Component | Count | Details |
|---|---|---|
| **Tables** | 5 | SUPPLIERS, PRODUCTS, WAREHOUSES, INVENTORY, PURCHASE_ORDERS |
| **Relationships** | 6 | Foreign key joins between tables |
| **Facts** | 20 | Numeric columns (quantities, costs, scores, etc.) |
| **Dimensions** | 38 | Categorical columns (names, statuses, dates, etc.) |
| **Metrics** | 9 | Pre-defined aggregations (avg reliability, total PO value, avg delay, etc.) |
| **Verified queries** | 3 | Known-good question-to-SQL mappings for accuracy |

<details>
<summary>Example verified query</summary>

```
"What are the top 5 suppliers by total purchase order value?"
→ SELECT s.SUPPLIER_NAME, SUM(po.TOTAL_COST) AS total_po_value
  FROM PURCHASE_ORDERS po JOIN SUPPLIERS s ON po.SUPPLIER_ID = s.SUPPLIER_ID
  GROUP BY s.SUPPLIER_NAME ORDER BY total_po_value DESC LIMIT 5;
```

</details>

---

### Step 8 — Create Cortex Agent

> **Script:** `setup/08_cortex_agent.sql`

Creates `SUPPLY_CHAIN_AGENT` with 3 tools:

| Tool Name | Type | Purpose | Data Source |
|---|---|---|---|
| `Analyst` | `CORTEX_ANALYST` | Natural language to SQL | Semantic view (5 structured tables) |
| `SupplierEmailSearch` | `CORTEX_SEARCH` | Search supplier emails | SUPPLIER_COMMS_SEARCH |
| `InspectionSearch` | `CORTEX_SEARCH` | Search inspection notes | WAREHOUSE_INSPECTIONS_SEARCH |

Configuration: **Model:** auto | **Budget:** 16,000 tokens per response

```sql
-- Verify:
SHOW AGENTS IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

---

### Step 9 — Create MCP Server + OAuth Integration

> **Script:** `setup/09_mcp_server.sql`

This script creates the MCP Server and sets up OAuth 2.0 authentication for Amazon Quick Suite:

**1. MCP Server:**
```sql
CREATE OR REPLACE MCP SERVER SUPPLY_CHAIN_MCP_SERVER
  AGENT = SUPPLY_CHAIN_AGENT
  TOOLS = (
    TYPE = CORTEX_AGENT_RUN
  );
```

**2. Account-level OAuth setting:**
```sql
ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE;
```

**3. OAuth Security Integration:**
```sql
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

> [!NOTE]
> The redirect URI above uses the current Quick Suite OAuth callback endpoint. Update the region (`us-west-2`) to match your Quick Suite region if needed.

**4. Retrieve OAuth credentials** (needed for Quick Suite connection in Phase 3):
```sql
DESCRIBE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH;
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('AMAZON_BEDROCK_MCP_OAUTH');
```

> [!WARNING]
> Save the `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` securely. You will need them in Phase 3 (Step 13).

**SSE Endpoint:**
```
https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse
```

> [!NOTE]
> Replace `<YOUR_ACCOUNT>` with your Snowflake account identifier (e.g., `SFSEAPAC-BSURESH`).

```sql
-- Verify:
SHOW MCP SERVERS IN SUPPLY_CHAIN_DEMO.PUBLIC;
```

---

### Verify Phase 1

After running all 9 scripts, run these verification queries:

```sql
-- Check all tables have data
SELECT 'SUPPLIERS' AS tbl, COUNT(*) AS cnt FROM SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLIERS
UNION ALL SELECT 'PRODUCTS', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.PRODUCTS
UNION ALL SELECT 'WAREHOUSES', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.WAREHOUSES
UNION ALL SELECT 'INVENTORY', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.INVENTORY
UNION ALL SELECT 'PURCHASE_ORDERS', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.PURCHASE_ORDERS
UNION ALL SELECT 'IOT_SENSOR_LOGS', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.IOT_SENSOR_LOGS
UNION ALL SELECT 'SUPPLIER_EMAILS', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLIER_EMAILS
UNION ALL SELECT 'INSPECTION_NOTES', COUNT(*) FROM SUPPLY_CHAIN_DEMO.PUBLIC.WAREHOUSE_INSPECTION_NOTES;

-- Check Cortex Search services
SHOW CORTEX SEARCH SERVICES IN SUPPLY_CHAIN_DEMO.PUBLIC;

-- Check agent
SHOW AGENTS IN SUPPLY_CHAIN_DEMO.PUBLIC;

-- Check MCP server
SHOW MCP SERVERS IN SUPPLY_CHAIN_DEMO.PUBLIC;

-- Check OAuth integration
DESCRIBE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH;
```

<details>
<summary><b>Expected row counts</b></summary>

| Table | Rows |
|---|---|
| SUPPLIERS | 20 |
| PRODUCTS | 50 |
| WAREHOUSES | 8 |
| INVENTORY | 162 |
| PURCHASE_ORDERS | 200 |
| IOT_SENSOR_LOGS | 180 |
| SUPPLIER_EMAILS | 200 |
| WAREHOUSE_INSPECTION_NOTES | 170 |

</details>

---

<div align="center">

## <img src="https://img.shields.io/badge/-569A31?style=flat-square&logo=amazons3&logoColor=white" height="28"> Phase 2: Amazon S3 — Upload CSV Data

*Upload the supplementary CSV files to an S3 bucket for the Quick Suite Knowledge Base.*

</div>

---

### Step 10 — Create an S3 Bucket and Upload CSV Files

Two CSV files are included in the `S3_csvs/` directory of this repository:

| File | Description | Rows | Size | Key Columns |
|---|---|---|---|---|
| `freight_costs.csv` | Shipping cost records with carrier, route, and on-time data | 60 | 5.2 KB | shipment_id, product_id, carrier_name, shipping_cost_usd, on_time |
| `customer_returns.csv` | Customer returns with free-text complaint narratives | 40 | 12.8 KB | return_id, product_id, reason_category, customer_complaint, refund_amount |

> [!NOTE]
> `customer_returns.csv` contains an unstructured `customer_complaint` column with 2–4 sentence narratives describing each return reason. This complements the unstructured text on the Snowflake side (supplier emails, inspection notes).

**Upload steps:**

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/s3/)
2. Go to **Amazon S3** > **Buckets** > **Create bucket**
3. Name the bucket (e.g., `supply-chain-demo-data`) and select your preferred region
4. Keep default settings (block public access enabled) and click **Create bucket**
5. Open the new bucket and click **Upload**
6. Click **Add files**, select both CSV files from the `S3_csvs/` directory, and click **Upload**

**Alternatively, use the AWS CLI:**
```bash
# Create the bucket (choose your region)
aws s3 mb s3://supply-chain-demo-data --region us-west-2

# Upload CSV files
aws s3 cp S3_csvs/freight_costs.csv s3://supply-chain-demo-data/
aws s3 cp S3_csvs/customer_returns.csv s3://supply-chain-demo-data/
```

---

### Step 11 — Verify S3 Data

Confirm both files are uploaded:

```bash
aws s3 ls s3://supply-chain-demo-data/
```

Expected output:
```
2025-xx-xx xx:xx:xx       5281 freight_costs.csv
2025-xx-xx xx:xx:xx      13059 customer_returns.csv
```

---

### Step 12 — Create a Quick Suite Knowledge Base (S3 Data Source)

1. Open [Amazon Quick Suite](https://quicksuite.aws.amazon.com/) console
2. Navigate to **Knowledge Bases** in the left navigation
3. Click **Create knowledge base**
4. Configure:
   - **Name:** `supply_chain_space_s3`
   - **Description:** "Freight costs and customer returns data for supply chain analysis"
   - **Data source:** Select **Amazon S3**
   - **S3 bucket:** Select or enter `supply-chain-demo-data` (the bucket from Step 10)
   - **Files:** Select both `freight_costs.csv` and `customer_returns.csv`
5. Click **Create**
6. Wait for the knowledge base to finish indexing the CSV files

> [!IMPORTANT]
> The knowledge base name `supply_chain_space_s3` must match what is referenced in the agent instructions (`setup/10_quicksuite_instructions.md`). If you use a different name, update the instructions accordingly.

**Verify:** In the knowledge base details, confirm:
- Status: **Active**
- Documents indexed: **2** (freight_costs.csv, customer_returns.csv)

---

<div align="center">

## <img src="https://img.shields.io/badge/-FF9900?style=flat-square&logo=amazonaws&logoColor=white" height="28"> Phase 3: Amazon Quick Suite — Agent Setup

*Create the Quick Suite chat agent that connects to both the Snowflake MCP Server and the S3 Knowledge Base.*

</div>

---

### Step 13 — Add Snowflake MCP Server as an Actions Integration

This step adds the Snowflake MCP Server as an MCP Actions integration in Amazon Quick Suite using OAuth 2.0 authentication.

You will need the OAuth credentials from Step 9:

| Setting | Value |
|---|---|
| **Client ID** | From `DESCRIBE SECURITY INTEGRATION AMAZON_BEDROCK_MCP_OAUTH` (OAUTH_CLIENT_ID row) |
| **Client Secret** | From `SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('AMAZON_BEDROCK_MCP_OAUTH')` |
| **Token URL** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/oauth/token-request` |
| **Authorization URL** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/oauth/authorize` |
| **MCP Server URL (SSE)** | `https://<YOUR_ACCOUNT>.snowflakecomputing.com/api/v2/databases/SUPPLY_CHAIN_DEMO/schemas/PUBLIC/mcp-servers/SUPPLY_CHAIN_MCP_SERVER/sse` |

> [!NOTE]
> Replace `<YOUR_ACCOUNT>` with your Snowflake account identifier (e.g., `SFSEAPAC-BSURESH`).

**Steps:**

1. Sign in to [Amazon Quick Suite](https://quicksuite.aws.amazon.com/) with an **Author Pro** or **Enterprise** role
2. From the Home screen, select **Integrations** in the left navigation
3. Click the **Actions** tab, then **Create new integration**
4. Select **Model Context Protocol** as the integration type
5. Enter:
   - **Name:** `snowflake-mcp-supply-chain`
   - **Description:** "Snowflake Cortex Agent for supply chain data (suppliers, inventory, purchase orders, emails, inspections)"
   - **MCP Server URL:** Paste the SSE endpoint from the table above
6. Click **Next**
7. Configure OAuth authentication:
   - **Authentication type:** OAuth (3LO or 2LO depending on your flow)
   - Fill in Client ID, Client Secret, Token URL, and Authorization URL from the table above
8. Click **Create**
9. Quick Suite will connect to the MCP server and discover available tools (you should see `supply-chain-agent`)

> [!TIP]
> If you get "The role ALL requested has been explicitly blocked", verify that Step 9 included:
> - `ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE;`
> - `BLOCKED_ROLES_LIST = ()` in the security integration
> - `OAUTH_USE_SECONDARY_ROLES = 'IMPLICIT'` in the security integration

---

### Step 14 — Create a Space for S3 Data

If you haven't already created a Space for the S3 knowledge base:

1. In Amazon Quick Suite, navigate to **Spaces** in the left navigation
2. Click **Create space**
3. Configure:
   - **Name:** `Supply Chain S3 Data`
   - **Data sources:** Select the `supply_chain_space_s3` knowledge base from Step 12
4. Click **Create**

This gives the chat agent access to the S3 CSV data as a queryable space.

---

### Step 15 — Create the Quick Suite Chat Agent

1. In Amazon Quick Suite, navigate to **Chat Agents** (or use the default **My Assistant** agent)
2. Click **Create agent** (or edit an existing agent)
3. Configure:
   - **Name:** `SupplyChainOrchestrator`
   - **Description:** "Multi-agent orchestrator for supply chain data across Snowflake and S3"

#### Add Tools

Add both data source tools:

| Tool | Type | Source |
|---|---|---|
| **supply-chain-agent** | MCP Actions Integration | Snowflake MCP Server (from Step 13) |
| **supply_chain_space_s3** | Knowledge Base | S3 Knowledge Base (from Step 12) |

#### Add Instructions

Click the **Instructions** field and paste the full content from `setup/10_quicksuite_instructions.md`.

This file contains:
- Detailed schema for both tools (tables, columns, row counts)
- Routing rules for single-tool vs. cross-platform questions
- Three-phase protocol for cross-platform queries (Rewrite → Call both → Combine)
- Response formatting guidelines

#### Save and Activate

1. Review the configuration
2. Click **Create** or **Save**
3. The agent is now ready for testing in Phase 4

---

<div align="center">

## Phase 4: Testing & Validation

*Verify the multi-agent orchestrator routes queries correctly across all platforms.*

</div>

---

### Step 16 — Test the Multi-Agent Orchestrator

In the Quick Suite chat agent interface, test these queries:

#### <img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="16"> Snowflake-routed queries (via supply-chain-agent)

1. "Which suppliers have reliability scores below 0.7?"
2. "What products are at risk of stockout in the next 5 days?"
3. "Show me all purchase orders delayed by more than 10 days"
4. "Search supplier emails about pricing changes"
5. "Show me warehouse inspection reports with Poor ratings"

#### <img src="https://img.shields.io/badge/-569A31?style=flat-square&logo=amazons3&logoColor=white" height="16"> S3-routed queries (via supply_chain_space_s3)

6. "Which carriers have the highest average shipping costs?"
7. "What are the most common reasons for customer returns?"
8. "Show me customer complaints mentioning defective products"
9. "Which products have the most returns?"

#### Cross-platform queries (both tools)

10. "Which products with stockout risk have the most customer complaints?"
    - *Expected: Agent calls Snowflake for inventory/stockout data, S3 KB for customer returns, matches on product_id*
11. "Which suppliers produce products with the highest return rates?"
    - *Expected: Agent calls S3 KB for return counts by product_id AND Snowflake for supplier-product mapping*

| Query Type | Tool | Data Source |
|---|---|---|
| Inventory, suppliers, POs | supply-chain-agent | Snowflake |
| Supplier emails, inspections | supply-chain-agent | Snowflake |
| Freight costs, carrier performance | supply_chain_space_s3 | Amazon S3 |
| Customer returns, complaints | supply_chain_space_s3 | Amazon S3 |
| Cross-platform | Both tools | Snowflake + S3 |

---

## Data Summary

<details>
<summary><b>Snowflake Data</b> — via Cortex Agent + MCP</summary>

| Category | Tables | Total Rows |
|---|---|---|
| Structured | SUPPLIERS, PRODUCTS, WAREHOUSES, INVENTORY, PURCHASE_ORDERS | 640 |
| Semi-structured | IOT_SENSOR_LOGS | 180 |
| Unstructured | SUPPLIER_EMAILS, WAREHOUSE_INSPECTION_NOTES | 370 |

</details>

<details>
<summary><b>Amazon S3 Knowledge Base</b> — via supply_chain_space_s3</summary>

| File | Rows | Key Data |
|---|---|---|
| `freight_costs.csv` | 60 | Shipping costs with carrier, route, weight, on-time flag |
| `customer_returns.csv` | 40 | Customer returns with free-text complaint narratives |

</details>

---

## Troubleshooting

| Issue | Solution |
|---|---|
| MCP tool call times out | Snowflake MCP non-streaming timeout is 50s. MCP operations in Quick Suite have a 60s timeout. Simplify queries or increase warehouse size |
| OAuth token errors | Verify `OAUTH_CLIENT_ID` and secret. Ensure security integration is `ENABLED = TRUE` |
| "Role ALL requested has been explicitly blocked" | Run `ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE` and set `BLOCKED_ROLES_LIST = ()` on the integration |
| S3 knowledge base not indexed | Wait a few minutes after creation for indexing. Check that CSV files are in the correct S3 bucket |
| Chat agent doesn't route correctly | Review instructions in `10_quicksuite_instructions.md` — ensure routing rules are explicit |
| MCP hostname issues | Use hyphens (-) not underscores (_) in hostnames for MCP server connections |
| Cortex Search returns no results | Wait 2–3 minutes after creating search services for indexing to complete |
| Semi-structured queries fail | Ensure VARIANT columns are queried with path notation (e.g., `SENSOR_PAYLOAD:temperature`) |
| Semantic view errors | Check that all 5 structured tables have data before creating the semantic view |
| OAuth redirect mismatch | Ensure the redirect URL in the Snowflake security integration matches the Quick Suite callback URI |
| MCP tool list not refreshing | Tool lists remain static after initial registration in Quick Suite. Manually refresh actions to detect server-side changes |
| IP not allowed (error 390420) | Add your IP to the Snowflake network policy: `ALTER NETWORK POLICY ... SET ALLOWED_IP_LIST = (...)` |

---

## Cleanup

<details>
<summary><b>Remove all resources</b></summary>

**Snowflake:**
```sql
DROP DATABASE IF EXISTS SUPPLY_CHAIN_DEMO;
DROP WAREHOUSE IF EXISTS SUPPLY_CHAIN_WH;
DROP SECURITY INTEGRATION IF EXISTS AMAZON_BEDROCK_MCP_OAUTH;
ALTER ACCOUNT SET OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = TRUE;
```

**Amazon S3:**
1. Go to **S3** > select your bucket (e.g., `supply-chain-demo-data`)
2. Delete all objects, then delete the bucket

**Amazon Quick Suite:**
1. Delete the `SupplyChainOrchestrator` chat agent (or remove tools from it)
2. Delete the `snowflake-mcp-supply-chain` Actions integration
3. Delete the `supply_chain_space_s3` knowledge base
4. Delete any Spaces created for this demo

</details>

---

## References

| Resource | Link |
|---|---|
| Snowflake Managed MCP Server | [docs.snowflake.com](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp) |
| Snowflake Cortex Agent | [docs.snowflake.com](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent) |
| Snowflake OAuth for Custom Clients | [docs.snowflake.com](https://docs.snowflake.com/en/user-guide/oauth-custom) |
| Amazon Quick Suite User Guide | [docs.aws.amazon.com](https://docs.aws.amazon.com/quicksuite/latest/userguide/what-is.html) |
| Quick Suite MCP Integration | [docs.aws.amazon.com](https://docs.aws.amazon.com/quicksuite/latest/userguide/mcp-integration.html) |
| Connect Quick Suite to Enterprise Apps via MCP | [aws.amazon.com/blogs](https://aws.amazon.com/blogs/machine-learning/connect-amazon-quick-suite-to-enterprise-apps-and-agents-with-mcp/) |
| Amazon S3 User Guide | [docs.aws.amazon.com](https://docs.aws.amazon.com/AmazonS3/latest/userguide/) |
| Model Context Protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io) |

---

<div align="center">

### Built With

<a href="https://www.snowflake.com"><img src="https://cdn.simpleicons.org/snowflake/29B5E8" width="40" alt="Snowflake"></a>
&nbsp;&nbsp;&nbsp;
<a href="https://aws.amazon.com/quick/"><img src="https://img.shields.io/badge/Amazon-Quick_Suite-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="Amazon Quick Suite"></a>
&nbsp;&nbsp;&nbsp;
<a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-Protocol-00ADD8?style=flat-square" alt="MCP"></a>

---

If you found this useful, give it a star!

[![GitHub stars](https://img.shields.io/github/stars/curious-bigcat/snowflake-cortex-mcp-foundry-fabric-multi-agent?style=social)](https://github.com/curious-bigcat/snowflake-cortex-mcp-foundry-fabric-multi-agent)

</div>

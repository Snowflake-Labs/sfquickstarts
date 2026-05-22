author: Dash Desai
id: sfguide-build-end-to-end-ai-app-on-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/product/data-engineering,snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: Build a complete AI-powered retail analytics platform on Snowflake — from streaming ingestion through Cortex Agents, Semantic Views, and MCP Servers.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Build an End-to-End AI Application on Snowflake
<!-- ------------------------ -->
## Overview

In this hands-on lab, you'll build a complete AI-powered retail analytics platform entirely within Snowflake — no external infrastructure required. Using Cortex Code as your AI-assisted development environment, you'll work through the full data lifecycle: stream real-time orders via Snowpipe Streaming, MERGE them into production tables with Gen2 Warehouses, transform them through a 3-tier Dynamic Tables pipeline, and serve them with Interactive Tables for low-latency point lookups.

You'll build analytical models with dbt, monitor data quality with Data Metric Functions, explore Iceberg V3 features, and create custom CoCo skills for reusable workflows. Tie it all together with Snowflake Intelligence — a conversational AI interface where a Cortex Agent orchestrates Cortex Analyst and Agentic Search to answer "what happened" and "why" from both structured and unstructured data. Finally, evaluate your agent with ground-truth datasets, implement row-level security, and expose your agent as a managed MCP server for external AI clients.

### What You'll Learn
- Accelerate development with Cortex Code (AI-assisted SQL, deployment, and data exploration)
- Stream real-time data with Snowpipe Streaming and transform with Dynamic Tables
- Serve low-latency queries with Interactive Tables and Gen2 Warehouses
- Build analytical models with dbt
- Monitor data quality automatically with Data Metric Functions
- Create and query managed Iceberg V3 tables (deletion vectors, row lineage)
- Create custom CoCo skills for reusable team workflows
- Build a Cortex Agent with Cortex Analyst (semantic view + verified queries) and Agentic Search (multi-index Cortex Search)
- Evaluate agent quality with ground-truth datasets and LLM judges
- Expose agents as managed MCP servers for external AI clients
- Implement transparent row-level security with Row Access Policies

### What You'll Build

A production-grade AI-powered retail analytics platform featuring a streaming data pipeline, dynamic transformations, interactive serving layer, conversational AI agent (text-to-SQL + unstructured search), data quality monitoring, row-level security, and an MCP server — all running natively on Snowflake.

```
Snowpipe Streaming (Python SDK)
        |
        v
STAGING tables (append-only landing zone)
        |
        v
Gen2 Warehouse MERGE (dedup + upsert into RAW)
        |
        v
Dynamic Tables (3-tier incremental pipeline)
        |
        v
Interactive Tables (low-latency point lookups)
        |
        v
Cortex Agent + Semantic View (natural language queries)
        |
        v
Row Access Policies (transparent security)
```

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Python 3.8+ installed locally
- Git installed locally
- Basic familiarity with SQL and command-line tools

<!-- ------------------------ -->
## Setup

### Install Snowflake CLI and Cortex Code

Run the installer script for your platform:

**macOS / Linux:**
```bash
bash install.sh
```

**Windows (PowerShell):**
```powershell
.\install.ps1
```

This installs:
- **Snowflake CLI** (`snow`) — for SQL execution and deployments
- **Cortex Code CLI** (`cortex`) — AI-powered coding assistant for Snowflake

Verify the installation:
```bash
snow --version
cortex --version
```

### Configure Snowflake Connection

```bash
snow connection add
# Enter: account identifier, username, password
# Set role: ACCOUNTADMIN
# Set warehouse: HOL_WH
# Set database: DASH_AUTOMATED_INTELLIGENCE_DB
```

### Generate RSA Key Pair

Generate keys for Snowpipe Streaming authentication:

```bash
# Generate private key (unencrypted PEM)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Upload public key to your Snowflake user
snow sql -q "ALTER USER <your-username> SET RSA_PUBLIC_KEY='$(grep -v -- '-----' rsa_key.pub | tr -d '\n')'"

# Verify
snow sql -q "DESC USER <your-username>" | grep RSA_PUBLIC_KEY_FP
```

Keep `rsa_key.p8` — you'll use it in Section 4.

### Clone the Lab Repository

```bash
git clone https://github.com/Snowflake-Labs/automated-intelligence-dev-day-2026-hol.git
cd automated-intelligence-dev-day-2026-hol
```

### Run Infrastructure Setup

Launch Cortex Code and verify your connection:

```bash
cortex
```

Then run the core infrastructure script:

```bash
snow sql -f setup.sql -c <your-connection>
```

This creates the database, schemas, warehouses, tables, Dynamic Tables pipeline, Interactive Tables, Cortex Search Services, Semantic View, seed data (50M orders, 161M order items, 2M customers), and Row Access Policy.

<!-- ------------------------ -->
## Streaming Ingestion

Stream orders into the STAGING schema using the Snowpipe Streaming Python SDK:

```bash
cd snowpipe-streaming-python
pip install -r requirements.txt

# Copy and configure profile
cp profile.json.template profile.json
```

Edit `profile.json` and set your `account`, `user`, `private_key` (contents of rsa_key.p8), and `role`.

```bash
# Stream 10,000 orders
python src/automated_intelligence_streaming.py 10000
```

### Verify Data Landed

```sql
SELECT COUNT(*) FROM dash_automated_intelligence_db.staging.orders_staging;
SELECT COUNT(*) FROM dash_automated_intelligence_db.staging.order_items_staging;
```

You should see 10,000 orders and ~50,000 order items in staging.

<!-- ------------------------ -->
## Gen2 Warehouse and MERGE

Use Cortex Code to merge staged data into production:

**Prompt CoCo:**

> *"Switch to the Gen2 warehouse, check how many rows are in staging, then merge them into RAW and show me the results"*

CoCo will switch to `hol_gen2_wh`, check staging row counts, call `staging.merge_staging_to_raw(TRUE)`, and display timing results.

### Demonstrate Optima Indexing

Ask CoCo:

> *"Run a point lookup for customer_id 5000 on the Gen2 warehouse"*

Open the query profile in Snowsight to see partition pruning — only a fraction of partitions scanned despite no explicit clustering key. This is Gen2's Optima Indexing in action.

<!-- ------------------------ -->
## Dynamic Tables Pipeline

**Prompt CoCo:**

> *"Show me the Dynamic Tables pipeline status — names, target lag, last refresh time, and row counts for each tier"*

CoCo displays the 3-tier pipeline:
- **Tier 1** (1-min lag): `enriched_orders` (50M rows), `enriched_order_items` (161M rows)
- **Tier 2** (DOWNSTREAM): `fact_orders` (161M rows)
- **Tier 3** (DOWNSTREAM): `daily_business_metrics` (365 rows), `product_performance_metrics` (4 rows)

### Explore Results

Ask CoCo:

> *"Show me a sample of the daily business metrics — top 5 days by revenue"*

Expected: Top-5 days are in December 2025 (holiday peak), each with ~$755M revenue and ~258K orders.

<!-- ------------------------ -->
## Iceberg V3 Features

### Create a Managed Iceberg Table

**Prompt CoCo:**

> *"Create a managed Iceberg table from RAW.ORDERS with clustering by year and month, then query it to show partition pruning"*

CoCo creates the table with `CATALOG='SNOWFLAKE'` (no external volume needed) and demonstrates partition pruning on filtered queries.

### Explore V3: Deletion Vectors

> *"Create an Iceberg V3 table from RAW.ORDERS (ICEBERG_VERSION=3) with merge-on-read enabled, insert 1000 rows, then update 10 of them to demonstrate deletion vectors"*

CoCo creates a V3 table with `ENABLE_ICEBERG_MERGE_ON_READ = TRUE`, inserts data, then runs an UPDATE that uses deletion vectors instead of full file rewrites.

### Explore V3: Default Values

> *"Add a new column 'priority' with default value 'STANDARD' to the V3 table and show that existing rows get the default without a backfill"*

This demonstrates V3 schema evolution without rewriting data files.

<!-- ------------------------ -->
## Interactive Tables

### Point Lookups

Run queries in Snowsight to observe sub-second latency:

```sql
USE WAREHOUSE hol_interactive_wh;
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- Point lookup by customer ID
SELECT * FROM dash_automated_intelligence_db.interactive.customer_order_analytics
WHERE customer_id = 1;

-- Point lookup by order ID
SELECT * FROM dash_automated_intelligence_db.interactive.order_lookup
WHERE order_id = '<any-order-uuid>';
```

### Concurrency Load Test

**Prompt CoCo:**

> *"Run the interactive tables load test at interactive/load_test.py"*

This fires 200 concurrent sessions (1000 queries total) against both Interactive and Standard warehouses, then compares P50/P90/P99 latencies. Expected: ~10x faster P50 on Interactive.

Run the load test a second time for the full speedup (~10-12x) after the cache warms.

<!-- ------------------------ -->
## Data Quality

The setup script injected ~200 NULL values into `orders.total_amount` and `order_items.quantity`, plus ~150 NULLs into `order_items.product_name`. DMFs detect the first two — but there's a gap.

### Discover the Gap

**Prompt CoCo:**

> *"Check the data quality monitoring results and show me which columns have NULL violations"*

CoCo shows that `TOTAL_AMOUNT` (200 NULLs) and `QUANTITY` (200 NULLs) have violations — but `product_name` NULLs are going undetected.

> *"Are there any NULL values in order_items.product_name? Is that column being monitored?"*

CoCo finds ~150 NULLs and reveals the DMF is mis-attached to `product_category` instead of `product_name`.

### Fix the Coverage

> *"Fix the DMF — remove the NULL check from product_category and add it to product_name instead"*

```sql
ALTER TABLE order_items DROP DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (product_category);
ALTER TABLE order_items ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT ON (product_name);
```

This demonstrates the real-world workflow: monitor, discover gaps, fix coverage.

<!-- ------------------------ -->
## dbt Analytics

**Prompt CoCo:**

> *"Install dbt dependencies and build all models in the dbt-analytics project"*

CoCo runs `dbt deps` then `dbt build` to create all staging views and mart tables (9+ models).

### Explore Results

> *"Show me the customer lifetime value segments — how many customers are in each value tier?"*

<!-- ------------------------ -->
## CoCo Custom Skill

Create a reusable skill that automates table profiling:

**Prompt CoCo:**

> *"Create a custom CoCo skill called 'profile-table' that takes a table name, counts rows, checks for NULL columns, shows distinct value counts, and flags potential data quality issues"*

CoCo creates `.cortex/skills/profile-table/SKILL.md` with the skill definition, triggers, and step-by-step instructions.

### Test It

> *"$profile-table DASH_AUTOMATED_INTELLIGENCE_DB.RAW.ORDERS"*

This demonstrates how teams package repeatable workflows as shareable CoCo skills.

<!-- ------------------------ -->
## Snowflake Intelligence

### Create the Agent

**Prompt CoCo:**

> *"Run snowflake-intelligence/create_agent.sql to create the Business Insights Agent"*

### Test Agent Routing

Each question demonstrates different tool routing:

| Question | Tools Used |
|----------|-----------|
| "Show me monthly revenue trend from June 2025 to April 2026" | Cortex Analyst (text-to-SQL) |
| "Revenue dropped in February — what caused it and what do reviews say?" | Cortex Analyst + Agentic Search |
| "Find reviews mentioning wrong size with a rating below 3" | Agentic Search (filtered) |
| "Why are customers returning ski boots?" | Agentic Search (reviews + tickets) |
| "What is our total revenue and customer count by state?" | Cortex Analyst (text-to-SQL) |
| "What are the top complaint themes in support tickets from February 2026?" | Agentic Search (filter + AI_AGG) |
| "How many reviews mention sizing issues, and which products are most affected?" | Agentic Search (search + breakdown) |

This is the capstone moment — the agent routes across structured data (text-to-SQL) and unstructured data (Cortex Search) to answer "what happened" and "why."

<!-- ------------------------ -->
## Security and Governance

The Row Access Policy and WEST_COAST_MANAGER role were created by `setup.sql`. Demonstrate the contrast using Snowflake Intelligence:

1. Open **Snowflake Intelligence** in Snowsight
2. Ask the Business Insights Agent: *"What is our total revenue and customer count by state?"*
3. Note the result — all 10 states visible as ACCOUNTADMIN
4. Switch role to `WEST_COAST_MANAGER` and ask the same question
5. Only CA, OR, WA appear — the Row Access Policy transparently filters data

Key insight: Same agent, same question — different results based on who's asking. Row-level security works transparently through AI agents.

<!-- ------------------------ -->
## Streamlit Dashboard

**Prompt CoCo:**

> *"Deploy the Streamlit dashboard to Snowflake"*

CoCo runs `snow streamlit deploy` from the `streamlit-dashboard/` directory.

Open in Snowsight to see the data pipeline in action — staging ingestion, Gen2 MERGE to production, pipeline health, and product analytics.

<!-- ------------------------ -->
## Agent Evaluation

The evaluation dataset (7 questions + ground truth) was created by `setup.sql`. Run the evaluation in Snowsight:

### Run via Snowsight UI

1. Navigate to **AI and ML > Agents > BUSINESS_INSIGHTS_AGENT > Evaluations** tab
2. Click **New evaluation run**
3. Name it (e.g. `hol-eval-run-1`)
4. Select **Create new dataset** with source table: `DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC.AGENT_EVALUATION_DATA`
5. Map columns: `INPUT_QUERY` to query_text, `GROUND_TRUTH` to ground_truth
6. Toggle on **Answer Correctness** and **Logical Consistency**
7. Click **Create** — evaluation starts automatically (~3 min)

### Interpret Results

- **Answer Correctness** — Did the agent's response match ground truth? Scored 0-1 per question.
- **Logical Consistency** — Were planning steps, tool calls, and response internally consistent? (Reference-free.)
- **Per-question drill-down** — Select any row to see the full thread: planning, tool invocations, response generation.

### Improve Scores (Stretch)

If questions score low on logical consistency:
1. Click a low-scoring row and view Thread details
2. Look for vague reasoning about tool selection in the Planning step
3. Update the agent's instructions to be more explicit
4. Recreate the agent and re-run the evaluation

<!-- ------------------------ -->
## MCP Server

Expose the Business Insights Agent as a managed MCP server:

**Prompt CoCo:**

> *"Create a Snowflake-managed MCP server that exposes our Business Insights Agent, semantic view, and customer feedback search as tools"*

CoCo creates the MCP server:

```sql
CREATE MCP SERVER business_insights_mcp
  FROM SPECIFICATION $$
    tools:
      - name: "business-insights-agent"
        type: "CORTEX_AGENT_RUN"
        identifier: "DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC.BUSINESS_INSIGHTS_AGENT"
        description: "AI agent that answers business questions using structured data and customer feedback"
        title: "Business Insights Agent"

      - name: "revenue-analytics"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC.BUSINESS_ANALYTICS_SEMANTIC"
        description: "Text-to-SQL for revenue, orders, customers, and product metrics"
        title: "Revenue Analytics"

      - name: "customer-feedback-search"
        type: "CORTEX_SEARCH_SERVICE_QUERY"
        identifier: "DASH_AUTOMATED_INTELLIGENCE_DB.RAW.CUSTOMER_FEEDBACK_SEARCH"
        description: "Search across product reviews and support tickets"
        title: "Customer Feedback Search"
  $$;
```

### Connect from CoCo

```bash
cortex mcp add business-insights https://<account_url>/api/v2/databases/DASH_AUTOMATED_INTELLIGENCE_DB/schemas/SEMANTIC/mcp-servers/BUSINESS-INSIGHTS-MCP --type http
```

Now any MCP-compatible client (CoCo, Claude Desktop, custom apps) can discover and call these tools via the standard MCP protocol.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built a complete AI-powered retail analytics platform on Snowflake — from streaming ingestion through conversational AI and MCP server exposure.

### What You Learned
- How to stream real-time data with Snowpipe Streaming and merge with Gen2 Warehouses
- How to build incremental transformation pipelines with Dynamic Tables
- How to serve sub-second point lookups with Interactive Tables
- How to create and query Iceberg V3 tables with deletion vectors and default values
- How to monitor and fix data quality gaps with Data Metric Functions
- How to build dbt analytical models on Snowflake
- How to create custom CoCo skills for repeatable workflows
- How to build a Cortex Agent that routes across structured (Analyst) and unstructured (Search) data
- How to evaluate agent quality with ground-truth datasets
- How to implement transparent row-level security through AI agents
- How to expose AI capabilities as managed MCP servers

### Related Resources

Documentation:
- [Snowpipe Streaming SDK](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Interactive Tables](https://docs.snowflake.com/en/user-guide/interactive)
- [Gen2 Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-gen2)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Semantic Views](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Data Metric Functions](https://docs.snowflake.com/en/user-guide/data-quality-intro)
- [Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)

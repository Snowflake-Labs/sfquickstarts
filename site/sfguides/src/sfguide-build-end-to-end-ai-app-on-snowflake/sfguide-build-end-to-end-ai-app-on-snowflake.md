author: Dash Desai
id: sfguide-build-end-to-end-ai-app-on-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/product/data-engineering,snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: Build a complete AI-powered retail analytics platform on Snowflake — from streaming ingestion through Cortex Agents, Semantic Views, and MCP Servers.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Build an End-to-End Application Using CoCo on Snowflake
<!-- ------------------------ -->
## Overview

In this hands-on lab, you'll build a complete AI-powered retail analytics platform entirely within Snowflake — no external infrastructure required. Using Snowflake CoCo as your AI-assisted development environment, you'll work through the full data lifecycle: stream real-time orders via Snowpipe Streaming, MERGE them into production tables with Gen2 Warehouses, transform them through a 3-tier Dynamic Tables pipeline, and serve them with Interactive Tables for low-latency point lookups.

You'll build analytical models with dbt, monitor data quality with Data Metric Functions, and create custom CoCo skills for reusable workflows. Tie it all together with Snowflake CoWork — a conversational AI interface where a Cortex Agent orchestrates Cortex Analyst and Agentic Search to answer "what happened" and "why" from both structured and unstructured data. Finally, evaluate your agent with ground-truth datasets, implement row-level security, and expose your agent as a managed MCP server for external AI clients.

### What You'll Learn
- Accelerate development with Snowflake CoCo (AI-assisted SQL, deployment, and data exploration)
- Stream real-time data with Snowpipe Streaming and transform with Dynamic Tables
- Serve low-latency queries with Interactive Tables and Gen2 Warehouses
- Build analytical models with dbt
- Monitor data quality automatically with Data Metric Functions
- Create and query managed Iceberg V3 tables (deletion vectors, default values) *(optional)*
- Stream real-time data with Snowpipe Streaming *(optional)*
- Create custom CoCo skills and package them as shareable plugins
- Build a Cortex Agent with Cortex Analyst (semantic view + verified queries) and Agentic Search (multi-index Cortex Search)
- Use Deep Research for multi-step investigations, save Artifacts, and schedule Automations
- Evaluate agent quality with ground-truth datasets and LLM judges
- Expose agents as managed MCP servers for external AI clients
- Implement transparent row-level security with Row Access Policies

### What You'll Build

A production-grade AI-powered retail analytics platform on Snowflake — from raw data to conversational AI insights, entirely within a single platform. You'll create dynamic transformation pipelines, interactive low-latency tables, dbt analytical models, a Cortex Agent that answers questions across structured and unstructured data, Deep Research reports that cross-reference multiple data sources, governed Artifacts you can share with your team, scheduled Automations for recurring analysis, row-level security that works transparently through AI, and an MCP server that exposes your agent to external clients.

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) — or a trial (Enterprise edition, AWS US West 2 / US East 1) so Cortex AI, CoWork, and Interactive Tables are available
- Python 3.8+ installed locally
- Git installed locally
- Basic familiarity with SQL and command-line tools

<!-- ------------------------ -->

## Table of Contents

1. [Setup](#setup)
2. [Explore Your Data](#explore-your-data)
3. [Data Quality](#data-quality)
4. [Dynamic Tables Pipeline](#dynamic-tables-pipeline)
5. [dbt Analytics](#dbt-analytics)
6. [Gen2 Warehouse: Optima Indexing](#gen2-warehouse-optima-indexing)
7. [Interactive Tables](#interactive-tables)
8. [CoCo Custom Skill](#coco-custom-skill)
9. [CoCo Plugin](#coco-plugin)
10. [Snowflake CoWork](#snowflake-cowork)
11. [Security and Governance](#security-and-governance)
12. [Streamlit Dashboard](#streamlit-dashboard)
13. [Agent Evaluation](#agent-evaluation)
14. [Agent Observability](#agent-observability)
15. [MCP Server](#mcp-server)
16. [Optional: Iceberg V3 Features](#optional-iceberg-v3-features)
17. [Optional: Streaming Ingestion](#optional-streaming-ingestion)
18. [Cleanup](#cleanup)
19. [Resources](#resources)

### How to Use This Guide

Throughout this guide you'll see three types of instructions:

- **"Prompt CoCo:"** — Type the quoted text into Snowflake CoCo (your AI-assisted IDE). CoCo translates natural language into SQL, runs it, and shows results. This is the recommended workflow.
- **"In CoWork:"** — Type the quoted text into Snowflake CoWork (the conversational AI interface at [ai.snowflake.com](https://ai.snowflake.com)), not into CoCo.
- **SQL code blocks** — Raw SQL you can run directly in Snowsight or via `snow sql`. Use these when you want precise control or when CoCo isn't available.

CoCo and SQL paths produce the same result. Use whichever feels natural.

<!-- ------------------------ -->

## Setup

### Install Snowflake CLI

The Snowflake CLI (`snow`) lets you run SQL, deploy apps, and manage Snowflake objects from your terminal.

**macOS (using Homebrew):**

If you don't have Homebrew installed, first install it by opening Terminal and running:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install Snowflake CLI:
```bash
brew install snowflake-cli
```

**Windows:**
```powershell
pip install snowflake-cli
```

**Linux:**
```bash
pip install snowflake-cli
```

Verify the installation:
```bash
snow --version
```

You should see output like `Snowflake CLI version: 3.x.x`.

### Install Snowflake CoCo

Snowflake CoCo is an AI-powered coding assistant that runs in your terminal. It helps you write SQL, build pipelines, deploy apps, and explore your data using natural language prompts.

**macOS and Linux:**
```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

Verify the installation:
```bash
cortex --version
```

### Alternative: Snowflake CoCo Desktop

If you prefer a visual IDE experience, [download CoCo Desktop](https://www.snowflake.com/en/product/limited-access/cortex-code/) instead of (or alongside) the CLI. It's a native Mac/Windows app with a file editor, integrated terminal, agentic browser, and the same AI capabilities. CoCo Desktop is Generally Available (GA) to all accounts.

On first launch, follow the onboarding wizard:
1. Click **Next** on the Welcome screen
2. Add your connection (same account identifier and credentials from above) or select an existing one detected from `connections.toml`
3. Choose **Agent** mode
4. Pick your theme, then click **Get Started**

> **Tip:** If you already configured a connection with `snow connection add` (below), CoCo Desktop detects it automatically — just select it from the list.

See [CoCo Desktop documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/index) for full details.

### Configure Snowflake Connection

Before you can run any commands against Snowflake, you need to configure a connection. This tells the CLI which Snowflake account to connect to and how to authenticate.

Run the interactive connection wizard:
```bash
snow connection add
```

You'll be prompted for the following values (enter them one at a time):

| Prompt | What to enter | Example |
|--------|---------------|---------|
| Connection name | A short name for this connection | `hol` |
| Account identifier | Your Snowflake account URL (without `.snowflakecomputing.com`) | `myorg-myaccount` |
| User | Your Snowflake username | `jsmith` |
| Password | Your Snowflake password | *(hidden)* |
| Role | `ACCOUNTADMIN` | `ACCOUNTADMIN` |

Leave the rest empty.

> **Tip:** Your account identifier is the part before `.snowflakecomputing.com` in your Snowflake URL. For example, if you log in at `https://myorg-myaccount.snowflakecomputing.com`, your account identifier is `myorg-myaccount`.

Test that your connection works:
```bash
snow connection test -c hol
```

You should see `Status: OK`.

### Clone the Lab Repository

```bash
git clone https://github.com/Snowflake-Labs/sfguide-build-end-to-end-ai-app-on-snowflake.git
cd sfguide-build-end-to-end-ai-app-on-snowflake
```

### Run Infrastructure Setup

Launch Snowflake CoCo and verify your connection:

```bash
cortex -c hol
```

> **What to expect:** CoCo will start an interactive session in your terminal. You'll see your active connection, role, and warehouse displayed. You can type natural language prompts and CoCo will translate them into SQL or actions.

Then run the core infrastructure script (this takes ~5 minutes with the default 10M-row dataset):

```bash
snow sql -f setup.sql -c hol
```

This creates the database, schemas, warehouses, tables, Dynamic Tables pipeline, Interactive Tables, Cortex Search Services, Semantic View, seed data (10M orders, 25M order items, 2M customers), and Row Access Policy.

> **Using CoCo Desktop?** All "Prompt CoCo" instructions below work identically in both CLI and Desktop — type the same text into the chat input. Anywhere you see `cortex` as a terminal command, use the Desktop's built-in terminal or chat instead.

<!-- ------------------------ -->

## Explore Your Data

Now that setup is complete, let's get familiar with what was created. This is your first interaction with CoCo — try asking natural language questions about your data.

**Prompt CoCo:**

> *"What schemas and tables are in my database?"*

CoCo queries `INFORMATION_SCHEMA` and shows the database structure: RAW (source tables + views), STAGING (streaming landing zone), DYNAMIC_TABLES (pipeline), INTERACTIVE (low-latency), and SEMANTIC (AI layer).

> *"Show me 5 sample rows from the orders table"*

> *"How many orders, customers, and products do we have?"*

Expected: ~10M orders, ~25M order items, 2M customers, 10 products, ~240 reviews, ~192 support tickets.

> *"What's the date range of our order data?"*

Expected: August to November 2026.

This gives you a mental model of the dataset before we start transforming and analyzing it.

<!-- ------------------------ -->

## Data Quality

[Data Metric Functions (DMFs)](https://docs.snowflake.com/en/user-guide/data-quality-intro) let you attach automated quality checks directly to table columns. Snowflake runs them on a schedule and stores results in `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS`. Built-in DMFs include `NULL_COUNT`, `DUPLICATE_COUNT`, `UNIQUE_COUNT`, and `FRESHNESS` — or you can write custom ones.

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

## Dynamic Tables Pipeline

[Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about) are declarative data pipelines — you define the target state as a SQL query and Snowflake handles incremental refresh automatically. The `TARGET_LAG` parameter controls freshness: set a time-based lag (e.g., `1 minute`) for Tier 1 tables, or use `DOWNSTREAM` for tables that refresh only when their upstream sources change.

**Prompt CoCo:**

> *"Show me the Dynamic Tables pipeline status — names, target lag, last refresh time, and row counts for each tier"*

CoCo displays the 3-tier pipeline:
- **Tier 1** (1-min lag): `enriched_orders` (10M rows), `enriched_order_items` (25M rows)
- **Tier 2** (DOWNSTREAM): `fact_orders` (25M rows)
- **Tier 3** (DOWNSTREAM): `daily_business_metrics` (118 rows), `product_performance_metrics` (4 rows)

> **Note:** Row counts shown are for the default `data_scale = '10M'`. If you chose `'50M'` in `setup.sql`, expect ~50M enriched_orders, ~161M order_items, and 365 daily metrics rows.

### Explore Results

Ask CoCo:

> *"Show me a sample of the daily business metrics — top 5 days by revenue"*

Expected: Top-5 days are in November 2026 (holiday peak), each with ~$183M revenue and ~117K orders.

<!-- ------------------------ -->

## dbt Analytics

[dbt-snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake) transforms raw data into analytics-ready models using SQL SELECT statements. The dbt-snowflake adapter integrates natively with Snowflake, supporting incremental models, snapshots, and built-in testing. In this HOL, dbt creates staging views and mart tables for customer lifetime value, segmentation, product performance, and support analytics.

> **Prerequisites:** `dbt-core` and `dbt-snowflake` must be installed (`pip install dbt-snowflake`). CoCo will handle this for you if not already installed.

**Prompt CoCo:**

> *"Install dbt dependencies and build all models in the dbt-analytics project"*

CoCo runs `dbt deps` then `dbt build` to create all staging views and mart tables (9+ models).

**Running dbt locally (agent guidance):** `dbt-analytics/profiles.yml` uses `env_var()` for `account`, `user`, `password`, and `warehouse` (defaulting to `HOL_WH`), so it works with no hardcoded secrets. When running dbt locally, resolve the credentials from the active `hol` Snowflake CLI connection (`snow connection list`) and export them as environment variables — **do not print or transcribe the password into the transcript or any file**. For example, set the env vars in the shell, then run:

```bash
export SNOWFLAKE_ACCOUNT=<account locator from snow connection list>
export SNOWFLAKE_USER=<user from snow connection list>
export SNOWFLAKE_PASSWORD=<password from snow connection list>
export SNOWFLAKE_WAREHOUSE=HOL_WH
cd dbt-analytics
dbt deps
dbt build --profiles-dir . --target dev
```

If dbt is run inside Snowflake (e.g., from Snowsight), no env vars are needed — the active session provides authentication.

> **Expected output:** 71 tests pass, 1 warning (the `source_not_null_raw_orders_total_amount` test detects the 200 NULLs we injected for the Data Quality exercise — this is working as designed).

### Explore Results

> *"Show me the customer lifetime value segments — how many customers are in each value tier?"*

<!-- ------------------------ -->

## Gen2 Warehouse: Optima Indexing

[Gen2 Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-gen2) introduce Optima Indexing — an automatic indexing layer that prunes partitions at query time without explicit clustering keys. Gen2 warehouses learn from your query patterns and build internal indices that accelerate point lookups and filtered scans.

[Optima Indexing](https://docs.snowflake.com/en/user-guide/snowflake-optima) builds these hidden indexes in the background, on a best-effort basis, after it observes repeated point-lookup patterns on a table. On freshly loaded lab data it usually hasn't kicked in yet, so **don't expect a before/after difference during the lab**. This section shows you how to confirm which generation a warehouse is and where to look for Optima's effect on your own workloads.

### Confirm Warehouse Generations

**Prompt CoCo:**

> *"Show me the generation and resource constraint of each HOL warehouse"*

Or run:

```sql
SHOW WAREHOUSES LIKE 'HOL%';
```

Check the `generation` and `resource_constraint` columns. `HOL_GEN2_WH` shows `2` / `STANDARD_GEN_2`, and `HOL_GEN1_WH` shows `1` / `STANDARD_GEN_1`. Note that `HOL_WH` is Gen2 too: new standard warehouses default to Gen2 unless you specify `GENERATION = '1'`.

### Read the Query Profile

Run a point lookup on the Gen2 warehouse with the result cache off, so the query actually executes:

```sql
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
USE WAREHOUSE hol_gen2_wh;
SELECT * FROM dash_automated_intelligence_db.raw.orders WHERE customer_id = 5000;
```

Then open its Query Profile: in Snowsight go to **Monitoring > Query History**, select the query, and open the **Query Profile** tab.

- In the **Statistics** pane, compare **Partitions scanned** with **Partitions total**.
- Look for a **Partitions pruned by Snowflake Optima** row. It appears only once Optima has built an index for this pattern, so on fresh lab data it's typically absent and most partitions are scanned.
- The **Query insights** pane shows **Snowflake Optima used** when a query benefits from Optima.

> **Optional:** Skip this section if you're short on time. Nothing later in the lab depends on it.

<!-- ------------------------ -->

## Interactive Tables

[Interactive Tables](https://docs.snowflake.com/en/user-guide/interactive) are purpose-built for low-latency, high-concurrency point lookups. They maintain pre-computed results with clustering optimized for equality predicates, delivering sub-second response times for dashboard filters and application queries that would otherwise require full table scans.

### Point Lookups

Run queries in Snowsight to observe low-latency lookups:

```sql
USE WAREHOUSE hol_interactive_wh;
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- Point lookup by customer ID
SELECT * FROM dash_automated_intelligence_db.interactive.customer_order_analytics
WHERE customer_id = 1;

-- Point lookup by order ID (picks a real order ID for you)
SET sample_order_id = (SELECT order_id FROM dash_automated_intelligence_db.interactive.order_lookup LIMIT 1);
SELECT * FROM dash_automated_intelligence_db.interactive.order_lookup
WHERE order_id = $sample_order_id;
```

**What to expect:** in our testing each lookup executed in roughly 20–50 ms. The total time shown in the worksheet is higher (from about 0.2 s up to ~3 s), because it also includes compilation and network round-trip. The first queries after the warehouse starts are slower while its cache warms, so run each lookup twice.

To see the execution time on its own, open the Query Profile: in Snowsight go to **Monitoring > Query History**, select the query, and open the **Query Profile** tab. The **Execution** time there is the number to compare.

### Concurrency Load Test

> **Prerequisite:** `pip install snowflake-connector-python` (the load test script uses it directly).

**Prompt CoCo:**

> *"Run the interactive tables load test at interactive/load_test.py"*

This fires 200 concurrent sessions (1000 queries total) against both Interactive and Standard warehouses, then compares P50/P90/P99 latencies. You should see notably lower latency and higher throughput on the Interactive warehouse.

Run the load test a second time to observe the effect of warm caches. Results may vary depending on account, region, and data scale.

<!-- ------------------------ -->

## CoCo Custom Skill

[CoCo Custom Skills](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility#skills) let you package repeatable workflows into named commands that any team member can invoke. A skill is a Markdown file (`.cortex/skills/<name>/SKILL.md`) that defines triggers, parameters, and step-by-step instructions CoCo follows when the skill is activated.

Create a reusable skill that automates table profiling:

**Prompt CoCo:**

> *"Create a custom CoCo skill called 'profile-table' that takes a table name, counts rows, checks for NULL columns, shows distinct value counts, and flags potential data quality issues"*

CoCo creates `.cortex/skills/profile-table/SKILL.md` with the skill definition, triggers, and step-by-step instructions.

> **Note:** Confirm the new skill is loaded with `/skill list`. If it isn't listed, start a new session (in Desktop, open a new session from the sidebar).

### Test It

Skill invocation differs by surface: CoCo CLI uses `$`, CoCo Desktop and CoCo in Snowsight use `/`.

- **CLI:** *"$profile-table DASH_AUTOMATED_INTELLIGENCE_DB.RAW.ORDERS"*
- **Desktop / Snowsight:** *"/profile-table DASH_AUTOMATED_INTELLIGENCE_DB.RAW.ORDERS"*

This demonstrates how teams package repeatable workflows as shareable CoCo skills.

<!-- ------------------------ -->

## CoCo Plugin

[CoCo Plugins](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-plugins) bundle skills, MCP servers, hooks, and subagents into a single shareable package. Once packaged, anyone on your team can install the plugin and get all your extensions in one step — via GitHub, the Plugins Catalog, or by dropping it into a project directory.

### Package the Skill as a Plugin

**Prompt CoCo:**

> *"Package our profile-table skill as a CoCo plugin called retail-analytics"*

CoCo creates the plugin directory with a manifest and copies the skill into it.

**Manual fallback:**

```bash
mkdir -p .cortex/plugins/retail-analytics/.cortex-plugin
mkdir -p .cortex/plugins/retail-analytics/skills
```

Create `.cortex/plugins/retail-analytics/.cortex-plugin/plugin.json`:
```json
{
  "name": "retail-analytics",
  "description": "Data profiling skill for retail analytics",
  "version": "1.0.0"
}
```

```bash
cp -r .cortex/skills/profile-table .cortex/plugins/retail-analytics/skills/
```

### Validate

```bash
cortex plugin validate .cortex/plugins/retail-analytics
```

Expected output: `Plugin 'retail-analytics' is valid.`

### Test the Plugin

The plugin is auto-discovered from `.cortex/plugins/` in your project directory. If you created it in a running session, run `/plugin reload` to load it.

Plugin skills are namespaced by the plugin name, so call the plugin's copy explicitly (confirm the exact name with `/skill list`):

- **CLI:** *"$retail-analytics:profile-table DASH_AUTOMATED_INTELLIGENCE_DB.RAW.ORDERS"*
- **Desktop / Snowsight:** *"/retail-analytics:profile-table DASH_AUTOMATED_INTELLIGENCE_DB.RAW.ORDERS"*

The skill runs from the plugin — same behavior as before, but now it's a portable, installable package. Share it by pushing to GitHub (`cortex plugin install your-org/retail-analytics`) or publishing to the Plugins Catalog from CoCo Desktop.

<!-- ------------------------ -->

## Snowflake CoWork

[Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) are multi-tool AI orchestrators that route questions to the right data source. They combine [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) (text-to-SQL over [Semantic Views](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)) with [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview) (vector + keyword search over unstructured data) to answer both "what happened" and "why" from a single conversational interface.

### Create the Agent

**Prompt CoCo:**

> *"Run snowflake-cowork/create_agent.sql to create the Business Insights Agent"*

If your account has a CoWork (Snowflake Intelligence) object, only agents added to it appear in CoWork. The script detects this and registers the agent automatically; on accounts without one, the agent is visible by default.

> **Note:** A new agent can take a minute or two to show up in CoWork. If you don't see it yet, wait and refresh the page.

### Test Agent Routing

Open **Snowflake CoWork** at [ai.snowflake.com](https://ai.snowflake.com), or from Snowsight: **AI & ML > Agents > BUSINESS_INSIGHTS_AGENT > Preview in Snowflake CoWork**. Select the **Business Insights** agent.

**In CoWork:** try each question to see different tool routing:

| Question | Tools Used |
|----------|-----------|
| "Show me monthly revenue trend from August to November 2026" | Cortex Analyst (text-to-SQL) |
| "Which month had the lowest revenue, and what do customer reviews say about that period?" | Cortex Analyst + Agentic Search |
| "Find reviews mentioning wrong size with a rating below 3" | Agentic Search (filtered) |
| "Why are customers returning ski boots?" | Agentic Search (reviews + tickets) |
| "What is our total revenue and customer count by state?" | Cortex Analyst (text-to-SQL) |
| "What are the top complaint themes in support tickets?" | Agentic Search (filter + AI_AGG) |
| "How many reviews mention sizing issues, and which products are most affected?" | Agentic Search (search + breakdown) |

This is the capstone moment — the agent routes across structured data (text-to-SQL) and unstructured data (Cortex Search) to answer "what happened" and "why."

### Deep Research

For complex questions that span multiple data sources, use [Deep Research](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork) — an investigation mode that decomposes your question into parallel sub-investigations and synthesizes findings into a fully-cited report.

**In CoWork:** click the **+** button in the message bar and select **Deep Research**, then ask:

> *"What are the root causes of customer dissatisfaction? Investigate across order cancellations, product reviews, and support tickets to identify the top drivers and which products are most affected."*

CoWork runs parallel agents that cross-reference structured metrics (cancellation rates, return patterns) with unstructured feedback (reviews mentioning sizing issues, tickets about defects), then produces a multi-section report with every claim traced back to source data.

> **Note:** Deep Research can take 10 minutes or more. Start it, continue with **Save as Artifact** below in a separate chat, and come back to the report when it finishes.

### Save as Artifact

When the agent produces a useful chart or table, save it for reuse. After the agent responds to a revenue question with a chart:

1. Click the **save** icon on the chart to create an Artifact
2. Name it (e.g. "Monthly Revenue Trend")
3. Click **Share** to generate a link

Artifacts are persistent, live references — they refresh with the latest data on demand. Shared links respect RBAC: a colleague opening the same artifact sees results filtered through their own data permissions.

### Set Up an Automation

Turn a one-time insight into a recurring report. After getting a useful answer:

**In CoWork:**

> *"Send me this report every Monday morning"*

CoWork creates a scheduled automation that re-runs the query weekly with fresh data and emails you the results — including a summary, key metrics, and a link to the full report for follow-up questions. Manage automations from the **Automations** tab in CoWork.

> **Note:** Automations require a verified email address in Snowsight. Go to your profile (bottom-left) → verify your email if you haven't already.

<!-- ------------------------ -->

## Security and Governance

[Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro) enforce row-level security declaratively — you define a boolean expression that determines which rows are visible to which roles, and Snowflake applies it transparently to every query (including those generated by AI agents). No application code changes required.

The Row Access Policy and WEST_COAST_MANAGER role were created by `setup.sql`. Demonstrate how row-level security transparently filters data based on role:

**As ACCOUNTADMIN (full access):**

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE HOL_WH;
SELECT c.state, SUM(o.total_amount) AS total_revenue, COUNT(DISTINCT c.customer_id) AS customer_count
FROM dash_automated_intelligence_db.raw.orders o
JOIN dash_automated_intelligence_db.raw.customers c ON o.customer_id = c.customer_id
GROUP BY c.state ORDER BY total_revenue DESC;
```

Result: all 10 regions visible (9 US states + British Columbia).

**As WEST_COAST_MANAGER (restricted):**

```sql
USE ROLE WEST_COAST_MANAGER;
USE WAREHOUSE HOL_WH;
SELECT c.state, SUM(o.total_amount) AS total_revenue, COUNT(DISTINCT c.customer_id) AS customer_count
FROM dash_automated_intelligence_db.raw.orders o
JOIN dash_automated_intelligence_db.raw.customers c ON o.customer_id = c.customer_id
GROUP BY c.state ORDER BY total_revenue DESC;
```

Result: only CA, OR, WA appear — the Row Access Policy transparently filters data.

Key insight: Same query, same tables — different results based on who's asking. Row-level security enforces data boundaries without changing application logic.

### Verify Through CoWork

Cortex Agents run with the querying user's **default role**, not the active role selected in Snowsight, so switching your role in the Snowsight UI has no effect on the agent's results. To see the Row Access Policy filter the agent, temporarily make `WEST_COAST_MANAGER` your default role (`setup.sql` already granted it to you). No separate user or password is needed:

```sql
SET current_user = (SELECT CURRENT_USER());
ALTER USER IDENTIFIER($current_user) SET DEFAULT_ROLE = WEST_COAST_MANAGER;
```

Refresh CoWork and start a **new chat** with the Business Insights agent.

**In CoWork:**

> *"What is our total revenue and customer count by state?"*

The agent returns results for only CA, OR, and WA — the Row Access Policy filters data transparently, even through AI-generated SQL.

Restore your default role afterward:

```sql
SET current_user = (SELECT CURRENT_USER());
ALTER USER IDENTIFIER($current_user) SET DEFAULT_ROLE = AUTOMATED_INTELLIGENCE_ADMIN;
```

<!-- ------------------------ -->

## Streamlit Dashboard

[Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit) lets you build and deploy interactive data applications directly within your Snowflake account — no external infrastructure needed. Apps run securely inside Snowflake, with native access to your data and governed by the same role-based access control.

> **Prerequisites:** The dbt models must be built first (see the **dbt Analytics** section). The dashboard queries `DBT_ANALYTICS` and `DBT_STAGING` tables. Confirm they exist in the account you're deploying to:
>
> ```sql
> SHOW TABLES IN SCHEMA dash_automated_intelligence_db.dbt_analytics;
> ```
>
> You should see 7 tables, including `CUSTOMER_LIFETIME_VALUE` and `PRODUCT_AFFINITY`. If they're missing, dbt ran against a different account or connection; re-run the dbt section using your `hol` connection.

**Prompt CoCo:**

> *"Deploy the Streamlit dashboard to Snowflake"*

CoCo runs `snow streamlit deploy` from the `streamlit-dashboard/` directory. Deployment can take more than one attempt; if CoCo reports an error, let it retry. You can also deploy directly with the Snowflake CLI:

```bash
cd streamlit-dashboard
snow streamlit deploy --replace -c hol
```

Once deployed, open the app URL in Snowsight to explore:

- **Summary** — Revenue KPIs, order trends, customer counts
- **Customer & Product Analytics** — Lifetime value segments, product performance
- **Pipeline Health** — Dynamic Tables refresh status, data freshness monitoring

<!-- ------------------------ -->

## Agent Evaluation

[Agent Evaluation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents#evaluating-agents) lets you measure agent quality using ground-truth datasets and LLM-as-judge scoring. You define input queries and expected answers, then Snowflake runs the agent against each question and scores responses on Answer Correctness (does the response match ground truth?) and Logical Consistency (are the reasoning steps internally coherent?).

The evaluation dataset (7 questions + ground truth) was created by `setup.sql` and registered as the `HOL_EVAL_DATASET` dataset. Run the evaluation in Snowsight:

### Run via Snowsight UI

1. Switch to the **ACCOUNTADMIN** role in Snowsight (top-left role selector)
2. Navigate to **AI & ML > Agent Studio** (labeled **Agents** in some accounts) **> BUSINESS_INSIGHTS_AGENT > Evaluations** tab
3. Click **Use existing dataset** (or **Create evaluation run** if a run already exists), then **Run an evaluation manually**
4. Name the run (e.g. `hol-eval-run-1`), click **Next**
5. Select **Existing dataset**, set Database and schema to `DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC`, then select **`HOL_EVAL_DATASET`**. Click **Next**
6. Under **Input query**, select `INPUT_QUERY`
7. Toggle on **Answer Correctness** and set its ground truth column to `GROUND_TRUTH`
8. Toggle on **Logical Consistency**
9. For each metric, set the version dropdown to **v3**. The default v1 judge model is legacy, so evaluations on newer accounts can fail without it
10. Click **Create**. The evaluation starts automatically (~3 min)

**Or Prompt CoCo:**

> *"Run an evaluation of the BUSINESS_INSIGHTS_AGENT agent using the existing HOL_EVAL_DATASET dataset in DASH_AUTOMATED_INTELLIGENCE_DB.SEMANTIC, with answer correctness and logical consistency metrics pinned to version v3"*

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

## Agent Observability

[Agent Observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents#monitor-cortex-agent-requests) lets you inspect what happened inside every agent request — which model was used, how many tokens were consumed, which tools were called, and how the agent planned its response. This is essential for production cost monitoring and debugging.

### View Reasoning Steps and Token Usage

```sql
-- See each planning/response step, model used, and token counts
SELECT 
    RECORD:name::STRING AS step,
    RECORD_ATTRIBUTES:"snow.ai.observability.agent.planning.model"::STRING AS model,
    RECORD_ATTRIBUTES:"snow.ai.observability.agent.planning.token_count.input"::INT AS input_tokens,
    RECORD_ATTRIBUTES:"snow.ai.observability.agent.planning.token_count.output"::INT AS output_tokens,
    TIMESTAMP
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    'DASH_AUTOMATED_INTELLIGENCE_DB', 'SEMANTIC', 'BUSINESS_INSIGHTS_AGENT', 'CORTEX AGENT'
))
WHERE RECORD:name::STRING LIKE 'ReasoningAgentStep%'
ORDER BY TIMESTAMP DESC
LIMIT 10;
```

### View Tool Calls

```sql
-- See which tools the agent invoked and when
SELECT 
    RECORD:name::STRING AS tool_event,
    TIMESTAMP
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    'DASH_AUTOMATED_INTELLIGENCE_DB', 'SEMANTIC', 'BUSINESS_INSIGHTS_AGENT', 'CORTEX AGENT'
))
WHERE RECORD:name::STRING LIKE '%Tool%'
ORDER BY TIMESTAMP DESC
LIMIT 10;
```

You'll see the full trace: planning steps → tool selection (Cortex Analyst, Search, SQL execution) → chart generation → response. Use this to debug slow responses, understand token costs, and verify the agent is routing to the correct tools.

> **Production tip:** To set per-user daily credit limits, budgets, or quotas for CoCo usage, see [Cost controls for CoCo](https://docs.snowflake.com/en/user-guide/cortex-code/cost-controls).

<!-- ------------------------ -->

## MCP Server

[Snowflake MCP Servers](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents#managed-mcp-servers) expose your Cortex Agents, Semantic Views, and Search Services as tools discoverable via the open Model Context Protocol (MCP). Any MCP-compatible client (CoCo CLI, Claude Desktop, custom apps) can connect to the server endpoint and invoke tools programmatically — turning your Snowflake AI stack into a reusable service layer.

Expose the Business Insights Agent as a managed MCP server:

**Prompt CoCo:**

> *"Create a Snowflake-managed MCP server that exposes our Business Insights Agent, semantic view, and customer feedback search as tools"*

CoCo creates the MCP server:

> **Note:** CoCo generates tool names (like `revenue-analytics`, `customer-feedback-search`) based on your prompt. Your names may differ — what matters is that the `type` and `identifier` point to the correct objects.

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

**CoCo Desktop (recommended):** Go to **Settings → MCP** and add a new HTTP server with this endpoint URL:

```
https://<account_url>/api/v2/databases/DASH_AUTOMATED_INTELLIGENCE_DB/schemas/SEMANTIC/mcp-servers/BUSINESS-INSIGHTS-MCP
```

Or type `/mcp` in the chat to manage MCP connections.

**CoCo CLI:** Register the server (Desktop picks this up automatically):

```bash
cortex mcp add business-insights https://<account_url>/api/v2/databases/DASH_AUTOMATED_INTELLIGENCE_DB/schemas/SEMANTIC/mcp-servers/BUSINESS-INSIGHTS-MCP --type http
```

Now any MCP-compatible client (CoCo Desktop, Claude Desktop, custom apps) can discover and call these tools via the standard MCP protocol.

<!-- ------------------------ -->

## Optional: Iceberg V3 Features

> **Note:** This section is optional. It demonstrates Iceberg V3 capabilities (deletion vectors, default values) using CoCo-generated SQL. No other sections depend on it.

> **Note:** CoCo may take a few attempts to generate correct SQL for Iceberg V3 features (these are newer APIs). If you see "error executing SQL," let CoCo retry — it will self-correct and the end result will work.

### Create a Managed Iceberg Table

**Prompt CoCo:**

> *"Create a managed Iceberg table from RAW.ORDERS with clustering by year and month, then query it to show partition pruning"*

CoCo creates the table with `CATALOG='SNOWFLAKE'` (no external volume needed) and demonstrates partition pruning on filtered queries.

### Explore V3: Deletion Vectors

> *"Create an Iceberg V3 table and load enough data from RAW.ORDERS to demonstrate deletion vectors, then update a few rows and show that Snowflake used a deletion vector instead of rewriting the file."*

CoCo creates a V3 Snowflake-managed Iceberg table (merge-on-read is the default for V3 managed tables), loads enough rows to exceed the data-file threshold below which deletion vectors are suppressed, then UPDATEs a small fraction of rows so Snowflake writes a deletion vector rather than rewriting the file.

### Explore V3: Default Values

> *"Add a new column 'priority' with default value 'STANDARD' to the V3 table and show that existing rows get the default without a backfill"*

This demonstrates V3 schema evolution without rewriting data files.

<!-- ------------------------ -->

## Optional: Streaming Ingestion

> **Note:** This section is optional. The `setup.sql` script already loads all 10M orders directly. This section demonstrates how you *would* stream data in production using the Snowpipe Streaming Python SDK.

### Generate RSA Key Pair

Generate keys for Snowpipe Streaming authentication:

```bash
# Generate private key (unencrypted PEM)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Upload public key to your Snowflake user (replace <your-username>)
snow sql -q "ALTER USER <your-username> SET RSA_PUBLIC_KEY='$(grep -v -- '-----' rsa_key.pub | tr -d '\n')'" -c hol

# Verify
snow sql -q "DESC USER <your-username>" -c hol | grep RSA_PUBLIC_KEY_FP
```

### Stream Data

```bash
cd snowpipe-streaming-python

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **macOS Apple Silicon:** If your default `python3` is Rosetta-emulated (e.g. Anaconda), use Homebrew's arm64 Python to avoid a `No matching distribution found` error:
> ```bash
> /opt/homebrew/bin/python3.11 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```

```bash
# Copy and configure profile
cp profile.json.template profile.json
```

Edit `profile.json` and set your `account`, `user`, `private_key_file` (path to rsa_key.p8), and `role`.

```bash
# Stream orders into staging
python src/automated_intelligence_streaming.py 1000
```

### Verify Data Landed

```sql
SELECT COUNT(*) FROM dash_automated_intelligence_db.staging.orders_staging;
SELECT COUNT(*) FROM dash_automated_intelligence_db.staging.order_items_staging;
```

Verify that row counts in both tables are consistent (each order should have matching order items).

### Merge into Production

Use CoCo to merge the streamed data:

> *"Switch to the Gen2 warehouse, check how many rows are in staging, then merge them into RAW and show me the results"*

<!-- ------------------------ -->

## Cleanup

To remove all objects created during this lab:

```bash
snow sql -f cleanup.sql -c hol
```

<!-- ------------------------ -->

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| DMF results missing after setup | `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS` populates asynchronously (up to 15 min) | Wait, or run `EXECUTE ALERT dash_automated_intelligence_db.raw.data_quality_alert;` to force check |
| Dynamic Table stuck in REFRESHING | Upstream DT hasn't finished first refresh | Check `SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())` for errors |
| Agent not appearing in CoWork | Account has a CoWork object and the agent isn't registered with it, or it's still provisioning | Wait a minute and refresh; re-run `snowflake-cowork/create_agent.sql` (it registers the agent automatically) |
| Cortex Search returns stale results | Incremental refresh doesn't pick up attribute value changes | Recreate with `CREATE OR REPLACE CORTEX SEARCH SERVICE` |
| Interactive Warehouse burns credits | Interactive warehouses don't auto-suspend | Run `ALTER WAREHOUSE hol_interactive_wh SUSPEND` when not in use |
| `load_test.py` connection error | Missing connector package | `pip install snowflake-connector-python` |
| Dashboard shows "dbt models not yet deployed" | dbt tables missing in this account (dbt ran against another connection) | `SHOW TABLES IN SCHEMA dash_automated_intelligence_db.dbt_analytics;` then re-run the dbt section with your `hol` connection |
| Agent evaluation fails with a judge/model error | Default v1 judge model is legacy | Set each metric's version to **v3** when creating the run |

<!-- ------------------------ -->

## Conclusion

Congratulations! You've built a complete AI-powered retail analytics platform on Snowflake — from raw data ingestion to conversational AI insights.

### What You Learned
- How to accelerate development with Snowflake CoCo
- How to stream real-time data with Snowpipe Streaming and transform with Dynamic Tables
- How to serve low-latency queries with Interactive Tables and Gen2 Warehouses
- How to build analytical models with dbt
- How to monitor data quality with Data Metric Functions
- How to create custom CoCo skills and plugins
- How to build a Cortex Agent with Cortex Analyst and Agentic Search
- How to use Deep Research, Artifacts, and Automations in CoWork
- How to evaluate agent quality with ground-truth datasets
- How to expose agents as managed MCP servers
- How to implement row-level security with Row Access Policies

### Related Resources
- [Snowpipe Streaming SDK](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Interactive Tables](https://docs.snowflake.com/en/user-guide/interactive)
- [Gen2 Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-gen2)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Semantic Views](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Data Metric Functions](https://docs.snowflake.com/en/user-guide/data-quality-intro)
- [Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Snowflake CoCo](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
- [Source Code Repository](https://github.com/Snowflake-Labs/sfguide-build-end-to-end-ai-app-on-snowflake)

author: Gilberto Hernandez
id: snowflake-dynamic-tables-data-pipeline
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/transformation
language: en
summary: Build declarative data pipelines using Dynamic Tables, driven by natural language prompts to Cortex Code inside Snowsight Workspaces.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-declarative-pipelines-dynamic-tables

# Build Autonomous SQL Pipelines with Cortex Code & Dynamic Tables
<!-- ------------------------ -->
## Overview 

What if you could build a production data pipeline by simply describing what you want? In this quickstart, you'll do exactly that — using **Cortex Code** as your AI co-pilot inside Snowsight Workspaces to build an end-to-end **Dynamic Tables** pipeline from natural language prompts.

Dynamic Tables let you declare *what* your pipeline should produce using SQL. Cortex Code lets you describe *what* you want in plain English and generates the SQL for you. Together, they represent a fully declarative approach to data engineering — from intent to production pipeline with zero boilerplate.

You'll work with the Tasty Bytes dataset (a fictitious food truck company) to build a three-tier pipeline that enriches raw order data, joins it into fact tables, and pre-aggregates business metrics — all by giving Cortex Code prompts.

### Prerequisites
- Basic familiarity with data engineering concepts (data loading, transformations)
- No SQL knowledge required — Cortex Code writes it for you

### What You'll Learn 
- How to use Cortex Code as a data engineering co-pilot inside Snowsight Workspaces
- How to build Dynamic Tables by describing your pipeline in natural language
- How to configure refresh strategies (TARGET_LAG, DOWNSTREAM) through prompts
- How Dynamic Tables handle incremental refresh automatically
- How to monitor pipeline operations conversationally
- How to create semantic views and AI agents using Cortex Code

### What You'll Need 
- A Snowflake account ([trial](https://signup.snowflake.com/developers), or otherwise)
- ACCOUNTADMIN access (available in trial accounts)
- Cortex Code enabled in your account ([setup guide](https://docs.snowflake.com/en/user-guide/cortex-code))

### What You'll Build 
- A three-tier declarative data pipeline processing ~1 billion order records
- A stored procedure for generating synthetic test data
- Monitoring queries for pipeline observability
- A semantic view for natural language querying
- A Cortex Agent for conversational data exploration

<!-- ------------------------ -->
## Create a Workspace from Git

In this step, you'll create a Snowsight Workspace linked to the companion repository on GitHub.

1. Navigate to **Projects > Workspaces** in Snowsight.
2. Click **Create** (+) and select **Git repository**.
3. Enter the repository URL: `https://github.com/Snowflake-Labs/sfguide-declarative-pipelines-dynamic-tables`
4. Select an API Integration for GitHub ([create one if needed](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git#label-create-a-git-workspace)).
5. Select **Public repository**.

Once the workspace is created, you'll see these files in the file explorer:

| File | Purpose |
|:-----|:--------|
| `00_setup_environment.sql` | Environment setup and data loading |
| `01_dynamic_tables.sql` | Dynamic Tables pipeline |
| `02_sproc.sql` | Test data stored procedure |
| `03_incremental_refresh.sql` | Incremental refresh testing |
| `04_monitoring.sql` | Pipeline monitoring |
| `05_semantic_view_agent.sql` | Semantic view and agent |
| `06_cleanup.sql` | Teardown |

### Open Cortex Code

Each file contains a **CORTEX CODE PROMPT** block at the top. Instead of running the SQL manually, you'll copy each prompt into Cortex Code:

1. Open the Cortex Code panel by pressing **Cmd+L** (Mac) or **Ctrl+L** (Windows), or click the Cortex Code icon in the workspace toolbar
2. You'll see a chat interface — this is where you'll give your prompts

**The workflow for each step:**
1. Open the SQL file in your workspace
2. Copy the prompt from the header block
3. Paste it into Cortex Code
4. Review the generated SQL (compare against the expected output in the file)
5. Tell CoCo to execute

> **Tip**: The SQL in each file is fully runnable on its own. If you prefer the traditional approach, you can run the files directly instead of using prompts.

<!-- ------------------------ -->
## Set Up the Environment

Let's set up our database, warehouse, and load the Tasty Bytes dataset.

Open **00_setup_environment.sql** in your workspace. Copy the prompt from the top of the file into Cortex Code:

**Prompt:**
```
Set up a lab environment: create role lab_role with CREATE WAREHOUSE and 
CREATE DATABASE privileges. Create database tasty_bytes_db with schemas 
raw and analytics. Create a 2XL standard warehouse tasty_bytes_wh with 
60s auto-suspend. Create tables order_header, order_detail, and menu in 
the raw schema. Set up a CSV file format and external stage pointing to 
s3://sfquickstarts/tasty-bytes-builder-education/. Load all tables using 
COPY INTO from the raw_pos/ subdirectories.
```

Cortex Code will generate the SQL to:
- Create `lab_role` with necessary privileges
- Create `tasty_bytes_db` with `raw` and `analytics` schemas
- Create a 2XL warehouse for fast data loading
- Define tables for order headers, order details, and menu items
- Load ~1 billion rows from S3

Review CoCo's output against the expected SQL in the file, then let it execute. The data load takes a few minutes due to the volume.

> **What just happened**: CoCo created all infrastructure objects and loaded nearly 1 billion rows of food truck order data. Compare CoCo's SQL against the file to see how closely it matched.

<!-- ------------------------ -->
## Understanding Dynamic Tables

Before we build the pipeline, let's understand the key concepts.

**Dynamic Tables** are a declarative way of defining data transformations in Snowflake. Instead of writing stored procedures, streams, and tasks to orchestrate your pipeline, you define the desired result using a `SELECT` statement. Snowflake automatically:

- Identifies and processes only changed rows (incremental refresh)
- Refreshes tables based on a target lag setting
- Manages dependencies between Dynamic Tables

**Key Concepts:**

- **TARGET_LAG**: The maximum acceptable delay between source changes and the Dynamic Table reflecting them. Example: `TARGET_LAG = '1 hour'` means data is at most 1 hour stale.

- **DOWNSTREAM**: A special TARGET_LAG value meaning "refresh only when downstream consumers need it." Creates an efficient pull-based refresh model.

- **Incremental Refresh**: Dynamic Tables process only changed data rather than recomputing everything. Processing 500 new orders out of 1 billion is nearly instant.

- **Dependency Graph**: Snowflake tracks dependencies between Dynamic Tables and determines refresh order automatically.

Now let's tell Cortex Code to build a three-tier pipeline using these concepts.

<!-- ------------------------ -->
## Build the Pipeline

This is the core of the quickstart — you'll describe an entire three-tier data pipeline to Cortex Code, and it will generate all the Dynamic Table DDL.

Open **01_dynamic_tables.sql** in your workspace. Copy the prompt into Cortex Code:

**Prompt:**
```
Build a 3-tier dynamic table pipeline in tasty_bytes_db.analytics using 
warehouse tasty_bytes_wh:

Tier 1 - Enrichment (TARGET_LAG = DOWNSTREAM):
- orders_enriched: From raw.order_header. Add temporal dimensions 
  (order_date, day_name, order_hour). Cast discount amount to NUMBER(10,2). 
  Add has_discount boolean flag. Filter nulls.
- order_items_enriched: Join raw.order_detail with raw.menu on menu_item_id.
  Calculate unit_profit, line_profit, profit_margin_pct.

Tier 2 - Fact Table (TARGET_LAG = DOWNSTREAM):
- order_fact: Join orders_enriched with order_items_enriched on order_id.

Tier 3 - Aggregated Metrics (TARGET_LAG = 1 hour):
- daily_business_metrics: Aggregate order_fact by date.
- product_performance_metrics: Aggregate order_fact by product.
```

> **Important**: Before executing, **review the generated SQL**. Compare it against the expected output in `01_dynamic_tables.sql`. Verify:
> - TARGET_LAG values match your specifications (DOWNSTREAM for Tier 1-2, 1 hour for Tier 3)
> - Join conditions are correct (menu_item_id for items, order_id for fact)
> - The dependency graph flows correctly: raw → Tier 1 → Tier 2 → Tier 3

When satisfied, tell CoCo to execute. The first refresh will process the full ~1 billion rows and may take several minutes. Subsequent refreshes will be incremental (much faster).

> **What just happened**: You described a multi-tier pipeline in plain English and CoCo generated 5 CREATE DYNAMIC TABLE statements with proper dependency management. Snowflake now automatically tracks the DAG and handles refreshes.

<!-- ------------------------ -->
## View Dependency Graph

Snowflake automatically tracks dependencies between your Dynamic Tables. Let's visualize this.

1. Navigate to your `tasty_bytes_db` database in the Snowflake UI
2. Click on the `analytics` schema
3. Click on any Dynamic Table (e.g., `order_fact`)
4. Look for the **Graph** tab

You'll see:
- **Upstream**: `orders_enriched`, `order_items_enriched`
- **Downstream**: `daily_business_metrics`, `product_performance_metrics`

![dag](./assets/dag.png)

Optionally, ask CoCo:

```
Show me all dynamic tables in tasty_bytes_db.analytics with their target lag settings
```

<!-- ------------------------ -->
## Generate Test Data

To test incremental refresh, we need a way to generate new orders. Let's ask CoCo to create a stored procedure for this.

Open **02_sproc.sql** in your workspace. Copy the prompt into Cortex Code:

**Prompt:**
```
Create a stored procedure tasty_bytes_db.raw.generate_demo_orders(num_rows INTEGER) 
that generates synthetic orders for testing incremental refresh. It should:
- Sample random existing orders from order_header
- Generate new unique order IDs
- Update timestamps to current date preserving time-of-day
- Randomize prices ±20%
- Generate matching order_detail records maintaining referential integrity
- Return a summary string with counts
```

**Review the generated SQL** — this is a complex stored procedure. Key things to verify:
- Uses a temp table to track original vs new order IDs
- Maintains referential integrity between order_header and order_detail
- Applies UNIFORM for randomization
- Properly cleans up the temp table

Compare against the expected output in `02_sproc.sql`, then execute.

> **What just happened**: CoCo generated a multi-step stored procedure with variables, temp tables, and proper referential integrity logic — all from a natural language description.

<!-- ------------------------ -->
## Test Incremental Refresh

Now let's see incremental refresh in action. Open **03_incremental_refresh.sql** — this file has multiple sequential prompts.

Give CoCo these prompts one at a time:

**Prompt 1** — Establish baseline:
```
How many rows are currently in tasty_bytes_db.raw.order_header and order_detail?
```

**Prompt 2** — Generate new data:
```
Call tasty_bytes_db.raw.generate_demo_orders with 500 rows
```

**Prompt 3** — Trigger refresh:
```
Manually refresh all dynamic tables in tasty_bytes_db.analytics in dependency 
order: first orders_enriched and order_items_enriched, then order_fact, then 
daily_business_metrics and product_performance_metrics
```

**Prompt 4** — Verify incremental behavior:
```
Show me the refresh history for all 5 dynamic tables. Was the latest refresh 
incremental or full? How long did each take?
```

> **Key insight**: Look at the `refresh_action` column. You should see **INCREMENTAL** — Snowflake processed only the 500 new orders through the entire pipeline, not the full billion-row dataset. This is what makes Dynamic Tables efficient at scale.

**Prompt 5** — View results:
```
Show me the latest daily business metrics and top 10 products by revenue
```

You should see today's date in the daily metrics with the newly generated orders included.

<!-- ------------------------ -->
## Monitor Pipeline

Monitoring is crucial for production pipelines. Ask CoCo for a monitoring summary.

Open **04_monitoring.sql** and copy the prompt:

**Prompt:**
```
Show me a monitoring dashboard for all dynamic tables in tasty_bytes_db.analytics: 
list each table with its scheduling state, target lag, and for the most recent 
refresh show the refresh type (incremental vs full), state, and duration in seconds
```

CoCo will query `INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY()` and format the results. Key columns:

- **refresh_action**: `INCREMENTAL` (efficient) vs `FULL` (first run or when incremental isn't possible)
- **state**: `SUCCEEDED` or `FAILED`
- **refresh_duration_seconds**: How long the refresh took

These monitoring patterns are essential for production pipeline observability.

<!-- ------------------------ -->
## Create Semantic View and Agent

Let's make our pipeline data queryable in natural language by creating a semantic view and AI agent.

Open **05_semantic_view_agent.sql** and copy the prompt:

**Prompt:**
```
Create a semantic view called tasty_bytes_semantic_model in TASTY_BYTES_DB.ANALYTICS 
over all 5 dynamic tables in the analytics schema. Then create a Cortex Agent 
called tasty_bytes_agent that uses this semantic view. Set the display name to 
"Tasty Bytes Analytics Agent".
```

CoCo will use its semantic view and agent creation skills to set up both objects.

### Test Your Agent

Once created, navigate to **AI & ML → Snowflake Intelligence** in Snowsight, select your agent, and try:

- "What are the top 10 products by revenue?"
- "Show me daily revenue trends for the last 30 days"
- "Which truck brands are most profitable?"
- "What's the average order value by day of week?"

The agent translates natural language into SQL queries against your Dynamic Tables and returns results with visualizations.

![agent](./assets/gent.png)

<!-- ------------------------ -->
## Clean up

To remove all objects created during this quickstart, open **06_cleanup.sql** and give CoCo the prompt:

**Prompt:**
```
Clean up: drop database tasty_bytes_db and warehouse tasty_bytes_wh using lab_role. 
Then using ACCOUNTADMIN, drop the lab_role.
```

This drops all databases, tables, Dynamic Tables, semantic views, agents, and compute resources.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've built a complete production data pipeline without writing a single line of SQL manually. By combining **Cortex Code** (your AI co-pilot) with **Dynamic Tables** (declarative pipeline infrastructure), you achieved:

- Fully automated, incremental data pipelines
- Natural language-driven development inside Snowsight
- AI-powered data access through semantic views and agents

### What You Learned

- Using Cortex Code inside Snowsight Workspaces to generate and execute SQL from prompts
- Building multi-tier Dynamic Table pipelines declaratively
- Configuring TARGET_LAG and DOWNSTREAM refresh strategies
- Verifying incremental refresh behavior
- Monitoring pipeline operations conversationally
- Creating semantic views and AI agents with natural language

### Related Resources

- [Cortex Code Documentation](https://docs.snowflake.com/en/user-guide/cortex-code)
- [Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-intro)
- [Dynamic Table Refresh](https://docs.snowflake.com/en/user-guide/dynamic-tables-refresh)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [AI Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/agents)
- [GitHub Repository](https://github.com/Snowflake-Labs/sfguide-declarative-pipelines-dynamic-tables)

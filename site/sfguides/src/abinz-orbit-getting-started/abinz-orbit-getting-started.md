author: Nabin Pariyar
id: abinz-orbit-getting-started
summary: Learn how to install ABINZ Orbit from the Snowflake Marketplace, connect your data, auto-discover relationships, generate a Cortex Analyst semantic model, and query your data in plain English — all within your Snowflake account.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/marketplace-and-integrations
environments: web
status: Published
language: en
feedback link: https://github.com/abinz-aiml/abinz-orbit-quickstart/issues
fork repo link: https://github.com/abinz-aiml/abinz-orbit-quickstart
open in snowflake: https://app.snowflake.com/marketplace/listing/GZU6Z1HLBPAXN/abinz-llc-abinz-orbit

# Getting Started with ABINZ Orbit on Snowflake

<!-- ------------------------ -->
## Overview
Duration: 5

ABINZ Orbit is a **Snowflake Native App** that creates a governed semantic layer on top of your Snowflake tables.

It automatically profiles your data, discovers relationships between tables, and generates a **Cortex Analyst semantic model** — so users can query data in plain English and receive SQL-backed results.

The app runs entirely within your Snowflake account using the Native Apps framework. No data leaves your environment.

ABINZ Orbit operates entirely within Snowflake using:
- Snowflake Native Apps framework
- Serverless Tasks for background processing
- Snowflake Cortex for natural language query interpretation

In most environments, this setup can be completed within an hour.

### Prerequisites
- A Snowflake account (any cloud, any region)
- ACCOUNTADMIN role for installation and initial grants
- At least one database with tables you want to analyze
- Snowflake Cortex enabled in your account (required for AI query functionality)

### What You'll Learn
- How to install a Snowflake Native App from the Marketplace
- How to profile tables and detect PII automatically using Snowflake Serverless Tasks
- How ABINZ Orbit discovers table relationships using AI-assisted heuristics
- How to generate a Cortex Analyst semantic model from your data
- How to query your data in plain English using Snowflake Cortex
- (Optional) How to use the Metrics Library to define and reference reusable business metrics

### What You'll Build
- A fully governed AI semantic layer on top of your Snowflake tables
- A Cortex Analyst model you can query in plain English
- (Optional) A KPI Outcome Contract to track business results over time

> **Note:** No sample data is required. ABINZ Orbit works with tables already in your Snowflake account. To follow along with a known dataset, use `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` which is available in all Snowflake accounts.

<!-- ------------------------ -->
## Install ABINZ Orbit from the Marketplace
Duration: 2

1. Log in to your Snowflake account at **app.snowflake.com**
2. Click **Data Products** → **Marketplace** in the left sidebar
3. Search for **ABINZ Orbit**
4. Click **Get** on the listing
5. Choose a warehouse (e.g., `COMPUTE_WH`)
6. Click **Get** to confirm — the app installs in under a minute

Once installed, navigate to **Data Products** → **Apps** → **ABINZ Orbit** to open it.

<!-- ------------------------ -->
## Grant the App Access to Your Data
Duration: 3

ABINZ Orbit can only read tables you explicitly grant it access to. Run the following as **ACCOUNTADMIN**:

> **Important:** Grants are scoped only to the schemas you specify. ABINZ Orbit does not have access to any data unless explicitly granted.

```sql
-- Grant access to a specific database and schema
GRANT USAGE ON DATABASE <YOUR_DATABASE> TO APPLICATION ABINZ_ORBIT;
GRANT USAGE ON SCHEMA <YOUR_DATABASE>.<YOUR_SCHEMA> TO APPLICATION ABINZ_ORBIT;
GRANT SELECT ON ALL TABLES IN SCHEMA <YOUR_DATABASE>.<YOUR_SCHEMA> TO APPLICATION ABINZ_ORBIT;

-- (Optional) Include future tables automatically
GRANT SELECT ON FUTURE TABLES IN SCHEMA <YOUR_DATABASE>.<YOUR_SCHEMA> TO APPLICATION ABINZ_ORBIT;
```

**Example using Snowflake sample data:**

```sql
GRANT USAGE ON DATABASE SNOWFLAKE_SAMPLE_DATA TO APPLICATION ABINZ_ORBIT;
GRANT USAGE ON SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 TO APPLICATION ABINZ_ORBIT;
GRANT SELECT ON ALL TABLES IN SCHEMA SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 TO APPLICATION ABINZ_ORBIT;
```

<!-- ------------------------ -->
## Grant App Roles to Your Users
Duration: 2

ABINZ Orbit has two application roles:

| Role | Who gets it | Capabilities |
|---|---|---|
| `ABINZ_APP_ADMIN_ROLE` | You (the admin) | Create/delete workspaces, start workers, manage settings |
| `ABINZ_APP_ANALYST_ROLE` | Your team members | Create workspaces, run analysis, ask AI questions |

Grant analyst access using the built-in stored procedure:

```sql
CALL ABINZ_ORBIT.ABINZ_KG.GRANT_ANALYST_ACCESS_TO_USER('<YOUR_SNOWFLAKE_USERNAME>');
```

To assign admin-level access, grant the application role directly:

```sql
GRANT APPLICATION ROLE ABINZ_ORBIT.ABINZ_APP_ADMIN_ROLE TO ROLE <ACCOUNT_ROLE_NAME>;
```

<!-- ------------------------ -->
## Start the Background Worker
Duration: 1

ABINZ Orbit uses a **Snowflake Serverless Task** — no warehouse needed — to process metadata in the background. This is a one-time setup:

```sql
CALL ABINZ_ORBIT.ABINZ_KG.START_BACKGROUND_WORKERS();
```

This creates a task that runs every 60 seconds to process analysis jobs in the background. The task runs on a schedule and processes jobs only when work is available.

Verify the worker is running:

```sql
SHOW TASKS IN APPLICATION ABINZ_ORBIT;
```

A healthy output shows the task with `state = started` and a recent `scheduled_time` timestamp. If state shows `suspended`, re-run the `START_BACKGROUND_WORKERS` call.

> **Note:** Starting the worker now ensures it is ready to pick up jobs the moment you add tables in the next steps.

> **Tip:** If no tables move out of `PENDING`, verify that the background worker is running and that required privileges were granted.

<!-- ------------------------ -->
## Create a Workspace
Duration: 2

> **Role note:** From this step onward, ACCOUNTADMIN is no longer required. Proceed as a user with `ABINZ_APP_ADMIN_ROLE` or `ABINZ_APP_ANALYST_ROLE`.

A workspace is an isolated project that holds your analysis for a specific database and schema combination.

1. Open ABINZ Orbit — you land on the **Home** module
2. Click **Create New Workspace**
3. Name it something descriptive, e.g., `My First Workspace`
4. Click **Create**

All analysis, relationships, and AI queries in this workspace are isolated from other workspaces.

<!-- ------------------------ -->
## Connect Your Data Source
Duration: 2

1. Go to the **Data Sources** module (left sidebar)
2. Click **Browse Databases**
3. Select the database and schema you granted access to in the **Grant the App Access** step
4. Select the tables you want to include — you can pick individual tables or include all
5. Click **Add to Workspace**

Once you add tables, ABINZ Orbit automatically starts analyzing them in the background.

<!-- ------------------------ -->
## Run Metadata Analysis
Duration: 5

The background worker processes your tables automatically. For each table it:

- Counts rows and columns
- Profiles each column: data type, cardinality, null rate, sample values
- Flags potential PII columns (e.g., SSN, DOB, email) based on column names and naming patterns — flagging is **informational only** and does not enforce access restrictions
- Calculates a **trust score** (0–100) based on completeness and consistency

Watch progress in the **Data Sources** module:

| Status | Meaning |
|---|---|
| `PENDING` | Queued, waiting for worker |
| `RUNNING` | Currently being analyzed |
| `COMPLETED` | Analysis done, ready to use |
| `FAILED` | Error — check the table for issues |

Analysis typically completes in 1–3 minutes per table, depending on table size and warehouse performance.

> **Large tables:** For tables over 10,000 rows, ABINZ Orbit automatically samples 500 rows to keep analysis fast. Full row counts are still captured.

<!-- ------------------------ -->
## Discover Relationships
Duration: 5

Once at least two tables are analyzed, go to the **Relationships** module and click **Discover Relationships**.

ABINZ Orbit's NAME_MATCH heuristic:
- Compares column names across tables (e.g., `order_key` in one table → `order_key` in another)
- Checks data types and sample value overlap
- Assigns a **confidence score** from 0.0 to 1.0

This approach enables relationship discovery even when foreign keys are not explicitly defined.

High-confidence relationships are automatically accepted (default threshold: 0.7, configurable in Settings). Lower the threshold (e.g., 0.5) to surface more candidates for manual review; raise it (e.g., 0.85) to accept only the highest-certainty matches automatically.

You can:
- Review and confirm suggested joins
- Add manual relationships the heuristic missed
- Remove false positives
- Adjust the confidence threshold in Settings

> **Note:** Relationship discovery typically completes in 1–2 minutes. For schemas with many tables, it may take slightly longer — this is normal.

Accepted relationships feed directly into the semantic model generation step.

<!-- ------------------------ -->
## Generate a Cortex Analyst Semantic Model
Duration: 3

Go to the **Model Preview** module and click **Generate Semantic Model**.

ABINZ Orbit builds a Cortex Analyst-compatible YAML model from your tables and confirmed relationships. The model defines:

- **Tables** with human-readable descriptions
- **Columns** with business-friendly names and data types
- **Joins** based on confirmed relationships
- **Metrics** for common aggregations (count, sum, average)

You can review and edit the YAML directly in the module before saving. The model is stored in your Snowflake account — Cortex Analyst uses it to translate plain English into SQL.

<!-- ------------------------ -->
## Ask a Question in Plain English
Duration: 3

Go to the **AI Assistant** module and type a question in the chat box. For example:

- *"What are the top 10 orders by total price?"*
- *"Show me the count of line items by status."*
- *"Which parts have the highest average supply cost?"*

ABINZ Orbit uses **Snowflake Cortex** to interpret your question using the semantic model:

1. Generates a SQL query based on your intent
2. Executes it inside your Snowflake account
3. Returns results in a table and natural language summary

If the generated SQL fails (e.g., due to a schema change), the **Self-Healing SQL** engine attempts to detect the error, adjust the query, and retry execution using updated schema context — without any action from you.

<!-- ------------------------ -->
## (Optional) Set a KPI Outcome Contract
Duration: 3

Beyond querying data, Orbit also lets you track whether insights translate into real business outcomes.

> This step is optional and not required for querying data.

The **KPI Studio** module lets you define a KPI, set a target, and measure actual lift over time.

1. Go to **KPI Studio** → **Outcome Contracts**
2. Click **New Contract**
3. Define your KPI (e.g., "Order Fulfillment Rate")
4. Set a baseline value and a target
5. Log the intervention you are testing
6. Click **Save Contract**

ABINZ Orbit tracks the KPI over time and shows the measured lift — the actual change vs. your target — giving you a quantifiable record of business outcomes.

<!-- ------------------------ -->
## (Optional) Use the Metrics Library
Duration: 2

Go to the **Metrics Library** module to find pre-defined reusable metrics. You can:

- Browse metrics by type: `SIMPLE`, `DERIVED`, `RATIO`, `CUMULATIVE`
- Add custom metrics relevant to your business
- Reference metrics in AI queries by name (e.g., "Show me order_fulfillment_rate by month")

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 1

You have successfully:

- Installed ABINZ Orbit as a Snowflake Native App with no additional infrastructure
- Connected your data without moving it outside Snowflake
- Profiled tables and flagged potential PII automatically
- Discovered table joins using AI-assisted relationship matching
- Generated a Cortex Analyst semantic model
- Queried your data in plain English using Snowflake Cortex
- (Optionally) set up KPI tracking with Outcome Contracts

All of this ran entirely inside your Snowflake account. No data left your environment, and no external services were required. Your existing Snowflake governance, RBAC, and encryption policies continue to apply automatically.

### What You Learned
- How to install and configure a Snowflake Native App
- How ABINZ Orbit profiles tables and detects PII using Snowflake Serverless Tasks
- How AI-assisted relationship discovery works and how to tune confidence thresholds
- How to generate and use a Cortex Analyst semantic model
- How to query Snowflake data in plain English with Self-Healing SQL
- (Optional) How to use the Metrics Library to define and track reusable business metrics

Install ABINZ Orbit from the Snowflake Marketplace and connect your first dataset to get started.

### Related Resources
- [ABINZ Orbit — Free Trial on Snowflake Marketplace](https://app.snowflake.com/marketplace/listing/GZU6Z1HLBPAXN/abinz-llc-abinz-orbit)
- [ABINZ Orbit Enterprise Edition](https://app.snowflake.com/marketplace/listing/GZU6Z1HLBPBCL/abinz-llc-abinz-orbit-enterprise-edition)
- [Full Quickstart on GitHub](https://github.com/abinz-aiml/abinz-orbit-quickstart)
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Native Apps Framework](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)
- [abinz.ai](https://abinz.ai) | [info@abinz.ai](mailto:info@abinz.ai)

author: Colin Mattimore
id: ai-cost-dashboard
summary: Build a unified cost reporting dashboard for all Snowflake Cortex AI services with dynamic tiered pricing and a Cortex Analyst chatbot.
categories: getting-started,data-science-&-ml,app-development
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
tags: Getting Started, Cortex, AI, Streamlit, Cost Management, Cortex Analyst

# Cortex AI Cost Dashboard
<!-- ------------------------ -->
## Overview
Duration: 2

A unified cost reporting dashboard for all Snowflake Cortex AI services, with dynamic tiered pricing based on account configuration and a Cortex Analyst chatbot.

This dashboard aggregates usage data from Cortex AI service views in `SNOWFLAKE.ACCOUNT_USAGE` into local tables for fast querying, computes dollar costs using a **service-tier and region-based pricing model**, then visualizes the data in a Streamlit app with an integrated Cortex Analyst chatbot.

> aside negative
> You must hard code your customer's credit rate in the `MERGE INTO CREDIT_BASE_RATES tgt` statement and the `INSERT INTO {{DATABASE}}.{{SCHEMA}}.CREDIT_BASE_RATES` statement (command in lines 269 to 282 of `setup.sql`).

### Prerequisites
- Snowflake account with `SYSADMIN` role (or equivalent with `ACCOUNT_USAGE` access)
- A warehouse for query execution
- Streamlit in Snowflake (SiS) enabled

### What You'll Learn
- How to aggregate Cortex AI usage data across services
- How to model tiered, region-based pricing for Cortex services
- How to build a Streamlit-in-Snowflake dashboard with an integrated Cortex Analyst chatbot

### What You'll Build
- 16 Snowflake tables (1 unified summary + 1 user costs + 14 detail tables)
- Reference tables for tiered credit rates and per-model token rates
- 2 stored procedures with dynamic pricing logic
- A daily refresh task
- A Streamlit dashboard with a Cortex Analyst chatbot

<!-- ------------------------ -->
## Pricing Model
Duration: 3

### Service Tiers

Services are classified into two tiers:

| Tier | Services |
|------|----------|
| AI_SERVICES | Cortex Code CLI, Cortex Code Snowsight, Cortex Agent, Snowflake Intelligence |
| STANDARD | All other services (AISQL, Analyst, Search, Document Processing, etc.) |

### Credit Rates (`CREDIT_BASE_RATES` table) - Customize with your account pricing

| Service Tier | Region Type | Base Rate | Tier Discount | Effective Rate | Period |
|--------------|-------------|-----------|---------------|----------------|--------|
| AI_SERVICES | GLOBAL | $2.00 | 0% | $2.00/credit | 2026-04-01 onwards |
| AI_SERVICES | REGIONAL | $2.20 | 0% | $2.20/credit | 2026-04-01 onwards |
| STANDARD | ANY | $3.00 | 0% | $3.00/credit | 2026-04-01 onwards |
| STANDARD | ANY | $3.00 | 0% | $3.00/credit | 2025-01-01 to 2026-03-31 |

### Region Detection

At refresh time, the stored procedures run `SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT`. This applies to **AI_SERVICES tier only** — STANDARD services use a flat rate regardless of cross-region setting:

| Parameter Value | Region Type |
|-----------------|-------------|
| `ANY_REGION`, `AWS_GLOBAL`, `GCP_GLOBAL`, `AZURE_GLOBAL` | GLOBAL |
| Any other value | REGIONAL |

### Cost Formula

- **AI_SERVICES tier**: `COST_USD = CREDITS × BASE_RATE × (1 - TIER_DISCOUNT_PCT / 100)` (rate depends on GLOBAL/REGIONAL)
- **STANDARD tier**: `COST_USD = CREDITS × BASE_RATE` (flat rate, no region classification)
- **REST API**: `COST_USD = (INPUT_TOKENS × INPUT_RATE + OUTPUT_TOKENS × OUTPUT_RATE) / 1,000,000 × (1 - DISCOUNT_PCT/100)` from `REST_API_TOKEN_RATES` table (per Snowflake Credit Consumption Table 6(c))

<!-- ------------------------ -->
## Cortex AI Services Covered
Duration: 1

| Service | Description | Cost Basis |
|---------|-------------|------------|
| CORTEX_AISQL | AI SQL functions (COMPLETE, EXTRACT, SUMMARIZE, etc.) | Credits (STANDARD) |
| CORTEX_ANALYST | Text-to-SQL natural language queries | Credits (STANDARD) |
| CORTEX_DOCUMENT_PROCESSING | Document parsing and extraction | Credits (STANDARD) |
| CORTEX_FINE_TUNING | Model fine-tuning | Credits (STANDARD) |
| CORTEX_FUNCTIONS_QUERY | Per-query LLM function details | Credits (STANDARD) |
| CORTEX_PROVISIONED_THROUGHPUT | PTU consumption | Credits (STANDARD) |
| CORTEX_REST_API | REST API calls | $ per 1M tokens |
| CORTEX_SEARCH | Cortex Search daily usage | Credits (STANDARD) |
| CORTEX_SEARCH_SERVING | Search serving costs | Credits (STANDARD) |
| DOCUMENT_AI | Document AI extraction | Credits (STANDARD) |
| CORTEX_CODE_CLI | Cortex Code CLI usage | Credits (AI_SERVICES) |
| CORTEX_CODE_SNOWSIGHT | Cortex Code Snowsight usage | Credits (AI_SERVICES) |
| CORTEX_AGENT | Cortex Agent invocations | Credits (AI_SERVICES) |
| SNOWFLAKE_INTELLIGENCE | Snowflake Intelligence queries | Credits (AI_SERVICES) |

<!-- ------------------------ -->
## Setup: Run the SQL Setup Script
Duration: 5

1. Download [`setup.sql`](assets/setup.sql) from this guide's assets folder.
2. Connect to your Snowflake account with `SYSADMIN` role (or `ACCOUNTADMIN`).
3. Open `setup.sql` in a Snowflake worksheet.
4. (Optional) Modify the configuration at the top:
   ```sql
   USE ROLE ACCOUNTADMIN; -- Use role with appropriate privileges (Create DB, Create Task, IMPORTED PRIVILEGES on SNOWFLAKE DB, USAGE ON WAREHOUSE)
   USE WAREHOUSE {{WAREHOUSE}};
   USE DATABASE {{DATABASE}};
   ```
5. Run the entire script.

This will create:
- 16 tables (1 unified summary + 1 user costs + 14 detail tables)
- 1 reference table (`CREDIT_BASE_RATES`) with tiered/regional rates
- 1 reference table (`REST_API_TOKEN_RATES`) with per-model token rates
- 2 stored procedures (`REFRESH_CORTEX_AI_COSTS`, `REFRESH_USER_AI_COSTS`) with dynamic pricing logic
- 1 daily refresh task (runs at 6 AM UTC on `{{WAREHOUSE}}`, auto-resumed)
- Initial data load for the last 365 days

<!-- ------------------------ -->
## Setup: Deploy the Streamlit App
Duration: 3

Upload [`streamlit_app.py`](assets/streamlit_app.py) and [`cortex_ai_costs_model.yaml`](assets/cortex_ai_costs_model.yaml) and create the Streamlit object:

```sql
CREATE STAGE IF NOT EXISTS {{DATABASE}}.{{SCHEMA}}.STREAMLIT_STAGE;

PUT file:///path/to/streamlit_app.py @{{DATABASE}}.{{SCHEMA}}.STREAMLIT_STAGE OVERWRITE=TRUE AUTO_COMPRESS=FALSE;
PUT file:///path/to/cortex_ai_costs_model.yaml @{{DATABASE}}.{{SCHEMA}}.STREAMLIT_STAGE OVERWRITE=TRUE AUTO_COMPRESS=FALSE;

CREATE OR REPLACE STREAMLIT {{DATABASE}}.{{SCHEMA}}.CORTEX_AI_COST_DASHBOARD
  ROOT_LOCATION='@{{DATABASE}}.{{SCHEMA}}.STREAMLIT_STAGE'
  MAIN_FILE='/streamlit_app.py'
  QUERY_WAREHOUSE='{{WAREHOUSE}}'
  TITLE='Cortex AI Cost Dashboard';
```

<!-- ------------------------ -->
## Using the Dashboard
Duration: 3

### Dashboard Features

- **KPI Metrics**: Total credits, total cost ($), tokens, requests, services used, active days, active users
- **Credit Distribution by Category**: Metric cards showing cost breakdown per service category
- **Month over Month Costs**: Bar chart with credit and dollar tooltips
- **Daily Credit Trend**: Area chart showing usage over time
- **Credits by Service**: Bar chart per service
- **Tokens by Model**: Pie chart showing top 10 models by token consumption

### Detailed Data Tabs

| Tab | Description |
|-----|-------------|
| Unified Summary | Aggregated costs by date, service, and model |
| By Service | Costs grouped by service category |
| By Model | Costs grouped by AI model |
| By User | Per-user cost breakdown with drill-down to individual queries |
| Cortex Agent | Costs by agent name (nulls shown as 'API CALL'), with daily detail |
| Snowflake Intelligence | Costs by SI name (nulls shown as 'API CALL'), with daily detail |
| Cortex Code | Credits by user for the last 30 days — Snowsight grid on top, CLI grid below |

### Cortex Analyst Chatbot

The dashboard includes an integrated Cortex Analyst chatbot at the bottom, powered by a semantic model (`cortex_ai_costs_model.yaml`). Ask natural language questions about your AI costs, e.g.:
- "What is the total cost in dollars over the last 30 days?"
- "Which service has the highest credit usage this month?"
- "Show me daily costs for Cortex Agent"

### Sidebar Controls

- **Time Range**: Filter by last 7/14/30/60/90/365 days or custom range
- **Service Categories**: Filter by specific service types
- **Refresh Data**: Click to call both stored procedures and pull latest data

<!-- ------------------------ -->
## Refreshing Data
Duration: 1

```sql
CALL {{DATABASE}}.{{SCHEMA}}.REFRESH_CORTEX_AI_COSTS(N); -- # of days
CALL {{DATABASE}}.{{SCHEMA}}.REFRESH_USER_AI_COSTS(N); -- # of days
```

### Scheduled Refresh

The daily task runs automatically at 6 AM UTC on `{{WAREHOUSE}}`. To check status:

```sql
SHOW TASKS LIKE 'REFRESH_CORTEX_AI_COSTS_DAILY' IN SCHEMA {{DATABASE}}.{{SCHEMA}};
```

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

You've built an end-to-end Cortex AI cost dashboard with tiered pricing and a Cortex Analyst chatbot.

### What You Learned
- Aggregating Cortex AI usage from `SNOWFLAKE.ACCOUNT_USAGE`
- Modeling tiered, region-based pricing for Cortex services
- Building a Streamlit-in-Snowflake dashboard with Cortex Analyst

### Related Resources
- [Cortex AI Documentation](https://docs.snowflake.com/en/guides-overview-ai-features)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)

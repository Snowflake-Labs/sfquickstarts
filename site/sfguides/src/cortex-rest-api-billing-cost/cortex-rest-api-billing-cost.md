author: Priya Joseph
id: cortex-rest-api-billing-cost
summary: Estimate Cortex REST API billing costs with granular token breakdowns, prompt caching discounts, and per-model pricing in a Streamlit dashboard.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Cortex, REST API, Billing, Cost Analysis, Prompt Caching, Streamlit, AI
language: en

# Cortex REST API Billing & Cost Analysis

<!-- ------------------------ -->
## Overview
Duration: 3

The companion quickstarts — [Cortex REST API Usage Monitor](https://www.snowflake.com/en/developers/guides/cortex-rest-api-usage/) and [Cortex REST API Budget Monitors](https://www.snowflake.com/en/developers/guides/cortex-rest-api-budget-monitors/) — track **token volumes**. This guide fills the remaining gap: **estimated USD cost** using the `TOKENS_GRANULAR` column, per-model pricing tiers, and the 90% prompt-caching discount.

### What You'll Learn
- How to use the `TOKENS_GRANULAR` OBJECT column to split input, output, and cached input tokens
- How prompt caching works (implicit for OpenAI models at 1,024+ tokens, explicit `cache_control` for Claude)
- How to load per-model pricing from a Snowflake table sourced from the [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)
- How to build a cost-estimation Streamlit dashboard with monthly, daily, and model-level breakdowns

### What You'll Need
- A Snowflake account with Cortex REST API access
- ACCOUNTADMIN role or appropriate privileges to query ACCOUNT_USAGE views
- Basic familiarity with Streamlit

### What You'll Build
A Streamlit in Snowflake (SiS) dashboard with:
- Monthly cost summary with input / cached-input / output cost split
- A configurable pricing table loaded from the `CORTEX_AI_PRICING` Snowflake table
- Daily cost trend chart
- Model-level cost breakdown

<!-- ------------------------ -->
## Understanding TOKENS_GRANULAR
Duration: 3

The `TOKENS_GRANULAR` column in `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY` is a SQL OBJECT that provides a per-request breakdown of token types:

| Key | Description |
|-----|-------------|
| `input` | Regular input (prompt) tokens |
| `output` | Output (completion) tokens |
| `cache_read_input` | Input tokens served from the prompt cache |

### Prompt Caching Rules

- **OpenAI models** — caching is implicit. Prompts with **1,024+ tokens** are automatically cached; no request changes needed.
- **Claude models** — caching is explicit. Add `cache_control` breakpoints to content blocks you want cached (ephemeral type, 5-minute or 1-hour TTL).

### The 90% Discount Logic

Cached input tokens are billed at **10% of the regular input rate** (a 90% discount), but only when the `cache_read_input` count for a request is **>= 1,024 tokens**. Below that threshold the tokens are billed at the full input rate.

```sql
-- Qualifying cached tokens (>= 1024): billed at 10% of input rate
-- Non-qualifying cached tokens (< 1024): billed at full input rate
CASE
    WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) >= 1024
        THEN TOKENS_GRANULAR:"cache_read_input"::NUMBER
    ELSE 0
END AS cached_input_tokens
```

<!-- ------------------------ -->
## Per-Model Pricing
Duration: 2

Pricing varies by model and token direction. Rather than hardcoding a pricing dictionary, the dashboard loads rates from the `CORTEX_AI_PRICING` Snowflake table at startup (cached for 1 hour). This table is sourced from the [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf) and includes all models from **Tables 6(b)** (REST API with Prompt Caching) and **6(c)** (REST API). Prices are in **USD per 1M tokens** (Global region where available).

The pricing table query:

```sql
SELECT MODEL_NAME, SOURCE_TABLE,
       INPUT_PRICE_PER_1M_TOKENS, OUTPUT_PRICE_PER_1M_TOKENS,
       CACHE_READ_PRICE_PER_1M_TOKENS
FROM CORTEX_AI_PRICING
WHERE SOURCE_TABLE IN ('6b', '6c');
```

If a model is not found in the table, a fallback rate of $2.00 / $0.20 / $8.00 (input / cached / output) is used. You can override any rate in the sidebar pricing editor.

> **Important**: The prices shown in this guide are examples only. For actual current pricing, always consult the official [Snowflake Service Consumption Table (PDF)](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf).

**Table 6(b) — REST API with Prompt Caching** (example rates — for current pricing, consult the [Consumption Table PDF](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)):

| Model | Input | Cache Read | Output |
|-------|-------|------------|--------|
| claude-sonnet-4-5 | $3.00 | $0.30 | $15.00 |
| claude-sonnet-4-6 | $3.00 | $0.30 | $15.00 |
| claude-haiku-4-5 | $1.00 | $0.10 | $5.00 |
| claude-opus-4-5 | $5.00 | $0.50 | $25.00 |
| claude-opus-4-6 | $5.00 | $0.50 | $25.00 |
| openai-gpt-5 | $1.25 | $0.13 | $10.00 |
| openai-gpt-5.2 | $1.75 | $0.18 | $14.00 |
| openai-gpt-5.4 | $2.50 | $0.25 | $15.00 |
| openai-gpt-4.1 | $2.00 | $0.50 | $8.00 |

**Table 6(c) — REST API** (example rates — for current pricing, consult the [Consumption Table PDF](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)):

| Model | Input | Output |
|-------|-------|--------|
| deepseek-r1 | $1.35 | $5.40 |
| mistral-large2 | $2.00 | $6.00 |
| llama3.3-70b | $0.72 | $0.72 |
| llama4-maverick | $0.24 | $0.97 |
| snowflake-llama-3.3-70b | $0.72 | $0.72 |

> **Note**: Table 6(c) models do not support prompt caching, so `cached_input` rate is $0.00. The sidebar pricing editor lets you add or update any model at runtime.

<!-- ------------------------ -->
## The Core SQL Query
Duration: 5

Below is the full monthly cost-estimation query. The dashboard runs this (and variants of it) behind the scenes.

```sql
SELECT
    DATE_TRUNC('MONTH', START_TIME) AS month,
    MODEL_NAME,
    SUM(TOKENS_GRANULAR:"input"::NUMBER) AS input_tokens,
    -- Cached tokens qualifying for discount (>= 1024)
    SUM(
        CASE
            WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) >= 1024
                THEN TOKENS_GRANULAR:"cache_read_input"::NUMBER
            ELSE 0
        END
    ) AS cached_input_tokens,
    -- Cached tokens NOT qualifying (< 1024, billed at full input rate)
    SUM(
        CASE
            WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) < 1024
                THEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0)
            ELSE 0
        END
    ) AS non_cached_input_tokens,
    SUM(TOKENS_GRANULAR:"output"::NUMBER) AS output_tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
WHERE START_TIME >= DATEADD(month, -6, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1, 2;
```

Cost is then calculated by joining the token counts with the per-model pricing table:

```
input_cost          = (input_tokens + non_cached_input_tokens) / 1e6 * input_rate
cached_input_cost   = cached_input_tokens / 1e6 * cached_input_rate
output_cost         = output_tokens / 1e6 * output_rate
total_cost          = input_cost + cached_input_cost + output_cost
```

<!-- ------------------------ -->
## Setup
Duration: 2

### Prerequisites

Grant access to the SNOWFLAKE database for your role:

```sql
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <your_role>;
```

Ensure the `CORTEX_AI_PRICING` table exists in your database/schema (see the [Credit Consumption MCP Guide](#) for how to parse and load pricing data from the PDF).

### Create the Streamlit App

1. Navigate to **Streamlit** in Snowsight
2. Click **+ Streamlit App**
3. Name your app `CORTEX_REST_API_BILLING_COST`
4. Select your warehouse and database/schema
5. Copy the code from `billing_dashboard.py` into the app

The app uses `get_active_session()` to connect — no connection configuration is needed when running in Snowsight.

<!-- ------------------------ -->
## The Streamlit Dashboard
Duration: 5

The dashboard has four sections:

### 1. Lookback & Run

Use the **Lookback** slider to choose how many months of history to analyze (1–12 months), then click **Run Cost Analysis** to execute the query.

![Lookback Slider](https://github.com/Snowflake-Labs/sfguides/blob/master/site/sfguides/src/cortex-rest-api-billing-cost/assets/LookbackinTime.png?raw=true)

![Run Cost Analysis](https://github.com/Snowflake-Labs/sfguides/blob/master/site/sfguides/src/cortex-rest-api-billing-cost/assets/runCostAnalysis.png?raw=true)

### 2. Cost Summary & Monthly Trend

KPI metrics at the top show:
- **Total Estimated Cost** (USD)
- **Input Cost** / **Cached Input Cost** / **Output Cost** split
- **Cache Savings** — the dollar amount saved by prompt caching vs. full input pricing

Below the KPIs, a **Monthly Cost Trend** stacked bar chart shows the cost breakdown over time by cost type (input, cached input, output).

![Cost Summary and Monthly Trend](https://github.com/Snowflake-Labs/sfguides/blob/master/site/sfguides/src/cortex-rest-api-billing-cost/assets/DailyCostTrend.png?raw=true)

### 3. Cost by Model

A table and horizontal bar chart ranking models by estimated cost, with columns for input tokens, cached tokens, output tokens, and the full cost breakdown per model.

![Cost by Model](https://github.com/Snowflake-Labs/sfguides/blob/master/site/sfguides/src/cortex-rest-api-billing-cost/assets/DailyCostByModel.png?raw=true)

### 4. Daily Drill-Down

A daily cost chart with a model selector dropdown. Choose **All Models** or a specific model to see the daily cost distribution and spot spikes.

![Daily Cost Drill-Down](https://github.com/Snowflake-Labs/sfguides/blob/master/site/sfguides/src/cortex-rest-api-billing-cost/assets/DailyCostDrillDownApr8.png?raw=true)

<!-- ------------------------ -->
## Cleanup
Duration: 1

To remove the app, navigate to **Streamlit** in Snowsight, find `CORTEX_REST_API_BILLING_COST`, and delete it.

The dashboard reads from `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY` and the `CORTEX_AI_PRICING` pricing table. To fully remove, also drop the pricing table if no longer needed.

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 1

You have built a cost-estimation dashboard that leverages `TOKENS_GRANULAR` to break down Cortex REST API spend by token type, model, and time period — with prompt-caching discount logic built in.

### Companion Guides
- [Cortex REST API Usage Monitor](https://www.snowflake.com/en/developers/guides/cortex-rest-api-usage/) — volume-based token tracking
- [Cortex REST API Budget Monitors](https://www.snowflake.com/en/developers/guides/cortex-rest-api-budget-monitors/) — token budget enforcement with alerts

### Related Resources
- [Cortex REST API Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api)
- [CORTEX_REST_API_USAGE_HISTORY View](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_rest_api_usage_history)
- [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

---
name: analyze-report
description: "Analyze Snowflake AI cost data and generate insights and reports."
parent_skill: ai-cost-dashboard
---

# Analyze / Report AI Costs

## When to Load

From `ai-cost-dashboard` SKILL.md when user selects Analyze / Report intent.

## Prerequisites

- AI Cost Dashboard is deployed (tables exist in `ADMIN_DB.AI_COSTS`)
- Snowflake connection is active

## Data Sources

| Table | Purpose |
|-------|---------|
| `ADMIN_DB.AI_COSTS.CORTEX_AI_UNIFIED_COSTS` | Aggregated costs by date/service/model |
| `ADMIN_DB.AI_COSTS.USER_AI_COSTS` | Per-user, per-query cost detail |

**Service categories in unified table:** LLM Functions, Analyst, Document Processing, Fine Tuning, Provisioned Throughput, REST API, Search, Document AI, LLM Functions Query, Cortex Code CLI

## Workflow

### Step 1: Determine Analysis Scope

**Goal:** Understand what the user wants to analyze.

**Actions:**

1. **Ask** user for analysis parameters:
   ```
   What would you like to analyze?

   1. Overall AI credit consumption
   2. Cost breakdown by service category
   3. Cost trends and anomalies
   4. Cost attribution by user
   5. Model-level token usage

   Time range: Last 7 / 30 / 90 / 365 days / Custom
   ```

2. **Optionally refresh** data first:
   ```sql
   CALL ADMIN_DB.AI_COSTS.REFRESH_CORTEX_AI_COSTS(<days>);
   CALL ADMIN_DB.AI_COSTS.REFRESH_USER_AI_COSTS(<days>);
   ```

**Output:** Defined analysis scope and time range

### Step 2: Execute Cost Queries

**Goal:** Retrieve AI cost data.

**Actions:**

1. **Overall consumption:**
   ```sql
   SELECT SERVICE_CATEGORY, SUM(CREDITS) AS TOTAL_CREDITS, SUM(TOKENS) AS TOTAL_TOKENS, SUM(REQUEST_COUNT) AS TOTAL_REQUESTS
   FROM ADMIN_DB.AI_COSTS.CORTEX_AI_UNIFIED_COSTS
   WHERE USAGE_DATE >= DATEADD('day', -<days>, CURRENT_DATE())
   GROUP BY SERVICE_CATEGORY
   ORDER BY TOTAL_CREDITS DESC;
   ```

2. **Daily trend:**
   ```sql
   SELECT USAGE_DATE, SUM(CREDITS) AS DAILY_CREDITS
   FROM ADMIN_DB.AI_COSTS.CORTEX_AI_UNIFIED_COSTS
   WHERE USAGE_DATE >= DATEADD('day', -<days>, CURRENT_DATE())
   GROUP BY USAGE_DATE ORDER BY USAGE_DATE;
   ```

3. **Top users:**
   ```sql
   SELECT FULL_NAME, SUM(CREDITS) AS TOTAL_CREDITS, COUNT(DISTINCT QUERY_ID) AS REQUESTS
   FROM ADMIN_DB.AI_COSTS.USER_AI_COSTS
   WHERE USAGE_DATE >= DATEADD('day', -<days>, CURRENT_DATE())
   GROUP BY FULL_NAME ORDER BY TOTAL_CREDITS DESC LIMIT 20;
   ```

4. **Model usage:**
   ```sql
   SELECT MODEL_NAME, SUM(TOKENS) AS TOTAL_TOKENS, SUM(CREDITS) AS TOTAL_CREDITS
   FROM ADMIN_DB.AI_COSTS.CORTEX_AI_UNIFIED_COSTS
   WHERE USAGE_DATE >= DATEADD('day', -<days>, CURRENT_DATE())
   GROUP BY MODEL_NAME ORDER BY TOTAL_TOKENS DESC;
   ```

**Output:** Raw cost data

### Step 3: Generate Insights

**Goal:** Analyze data and surface key findings.

**Actions:**

1. **Calculate** key metrics:
   - Total credits consumed in period
   - Daily average credit consumption
   - Top cost-driving services and models
   - Most active users
   - Trend direction (increasing/decreasing/stable)

2. **Identify** anomalies:
   - Daily spikes above 2x average
   - Unusual service patterns
   - New cost sources appearing

3. **Compile** findings

**Output:** Analysis summary

### Step 4: Present Report

**Goal:** Deliver findings to user.

**Actions:**

1. **Present** structured report:
   ```
   Cortex AI Cost Analysis Report
   Period: <start> to <end>

   Summary:
   - Total credits: X
   - Total tokens: X
   - Total requests: X
   - Daily average: X credits/day

   Top Services:
   1. <category> - X credits (Y%)
   2. <category> - X credits (Y%)

   Top Users:
   1. <name> - X credits, N requests

   Top Models:
   1. <model> - X tokens

   Anomalies:
   - [Any spikes or unusual patterns]

   Recommendations:
   - [Actionable suggestions]
   ```

2. **STOP**: Ask if user wants deeper analysis on any area.

3. **If requested**, drill down and repeat from Step 2 with narrower scope.

**Output:** Delivered report

## Stopping Points

- After Step 1: Confirm analysis scope
- After Step 4: Before any follow-up deep dives

## Output

AI cost analysis report with insights, trends, anomalies, and recommendations.

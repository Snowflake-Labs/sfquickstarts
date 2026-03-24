---
description: "**[REQUIRED]** Use for ALL Cortex REST API questions: token usage, API consumption, chat completions usage, model usage, budget monitoring, token budgets, API costs, usage history, usage by model, usage by user, Cortex REST API usage history, inference costs, LLM token tracking."
---

# Cortex REST API Usage & Budget Monitor Skill

> **Primary data source:** `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY`  
> This view tracks all Cortex REST API token consumption including chat completions.

---

## Routing

Match the user's question to keywords and read the corresponding file **before writing any queries**.

| Keywords | Route |
|----------|-------|
| "token usage", "total tokens", "how many tokens", "token consumption" | `references/queries/token-usage.md` |
| "usage by model", "model usage", "which models", "model breakdown" | `references/queries/by-model.md` |
| "usage by user", "who is using", "user consumption", "top users" | `references/queries/by-user.md` |
| "daily usage", "usage over time", "usage trend", "historical usage" | `references/queries/daily-usage.md` |
| "budget", "token budget", "spending limit", "alert threshold", "over budget" | `references/queries/budget-monitor.md` |
| "chat completions", "inference", "API calls", "request count" | `references/queries/chat-completions.md` |

**Never write ad-hoc queries when a verified query exists in the routed file.**

---

## Key View: CORTEX_REST_API_USAGE_HISTORY

```sql
-- Available columns:
-- START_TIME, END_TIME, USER_ID, MODEL_NAME, TOKENS, REQUEST_ID
```

**Important:** This view has up to 2 hours of latency.

---

## Reference Files & Directories

| Path | Type | Contents |
|------|------|----------|
| `references/queries/` | Directory | Category-specific query files |
| `references/tables.md` | File | Table schemas and column definitions |
| `references/streamlit-app.md` | File | Streamlit in Snowflake app code |

---

## Quick Start Queries

### Total Usage (Last 30 Days)
```sql
SELECT 
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS total_requests,
    COUNT(DISTINCT MODEL_NAME) AS unique_models,
    COUNT(DISTINCT USER_ID) AS unique_users
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP());
```

### Usage by Model
```sql
SELECT 
    MODEL_NAME,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```

---

## Prerequisites

Grant access to the SNOWFLAKE database:

```sql
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <your_role>;
```

---

## Streamlit App

For a full dashboard, see `references/streamlit-app.md` which provides:
- KPI metrics (total tokens, requests, models, users)
- Budget status with configurable thresholds
- Token usage charts by model
- Usage breakdown by user
- Daily usage details

---

## Slash Commands (Tab 2 — Budget Monitor)

The Streamlit dashboard's Tab 2 includes a command bar with the following slash commands. Run **"Run Budget Monitor Queries"** first, then type any command:

| Command | Alias | Description |
|---------|-------|-------------|
| `/budget-status` | `/status` | Show daily and weekly budget status snapshot (tokens used, % used, OK/WARNING/OVER BUDGET) |
| `/burn-rate` | `/burn` | Show latest daily burn, 7-day rolling average, and projected weekly/monthly usage |
| `/alerts` | `/rolling-alerts` | Show 30-day rolling alerts table with days that breached daily or weekly thresholds |
| `/budget-summary` | `/summary` | Combined view: budget status + projections + burn rate + alert count |

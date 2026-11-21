---
name: ai-cost-dashboard
description: "Build and manage a Snowflake AI Cost Dashboard using stored procedures and Streamlit. Use for **ALL** requests involving: AI cost, AI spending, cost dashboard, spending dashboard, Snowflake AI credits, Cortex cost tracking. DO NOT attempt AI cost dashboard work manually - invoke this skill first."
---

# AI Cost Dashboard

Deploys and manages a Cortex AI Cost Dashboard tracking credit usage across Snowflake AI services via stored procedures and a Streamlit app.

## Source Files

- **Setup SQL:** `cortex_ai_cost_dashboard/setup.sql` (template — uses `{{WAREHOUSE}}` placeholder)
- **Streamlit App:** `cortex_ai_cost_dashboard/streamlit_app.py` (dynamic — derives DB/schema from session context)
- **Semantic Model:** `cortex_ai_cost_dashboard/cortex_ai_costs_model.yaml` (template — uses `{{DATABASE}}`/`{{SCHEMA}}` placeholders)
- **Snowflake CLI config:** `cortex_ai_cost_dashboard/snowflake.yml` (template — uses `{{DATABASE}}`/`{{SCHEMA}}`/`{{WAREHOUSE}}` placeholders)
- **Deploy Skill:** `cortex_ai_cost_dashboard/skills/ai-cost-dashboard-deploy/SKILL.md`

## Architecture

```
SNOWFLAKE.ACCOUNT_USAGE (usage history views)
  -> MERGE (incremental)
<DATABASE>.<SCHEMA> (detail tables + unified + user-level)
  -> Queried by
Streamlit App (CORTEX_AI_COST_DASHBOARD)
```

**All object names (database, schema, warehouse, role, credit rate) are configurable at deploy time.**

**Key objects (created in user-specified database.schema):**
- Procedures: `REFRESH_CORTEX_AI_COSTS(DAYS_BACK)`, `REFRESH_USER_AI_COSTS(DAYS_BACK)`
- Tables: `CORTEX_AI_UNIFIED_COSTS`, `USER_AI_COSTS`, plus detail tables
- Task: `REFRESH_CORTEX_AI_COSTS_DAILY` (CRON 0 6 * * * UTC)

## Configurable Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Connection | Snowflake CLI connection name | — |
| Database | Target database | ADMIN_DB |
| Schema | Target schema | AI_COSTS |
| Warehouse | Warehouse for queries and tasks | COMPUTE_WH |
| Role | Deployment role | ACCOUNTADMIN |
| Credit Rate | Current standard $/credit rate | 2.88 |
| Historical Rate | Previous $/credit rate (before current) | 3.01 |

## Intent Detection

| Intent | Triggers | Load |
|--------|----------|------|
| SETUP | "set up", "deploy", "create", "install", "build dashboard" | `setup-deploy/SKILL.md` |
| ANALYZE | "analyze", "report", "show costs", "insights", "spending breakdown" | `analyze-report/SKILL.md` |

## Workflow

### Step 1: Identify Intent

**Ask** the user what they want to do:

```
What would you like to do with the AI Cost Dashboard?

1. Setup / Deploy - Deploy stored procedures and Streamlit app from scratch
2. Analyze / Report - Analyze current AI cost data and generate insights
```

**Route based on selection:**
- Option 1 -> **Load** `setup-deploy/SKILL.md`
- Option 2 -> **Load** `analyze-report/SKILL.md`

**If intent is clear from context**, skip the question and route directly.

## Prerequisites

- Snowflake account with ACCOUNTADMIN or role with ACCOUNT_USAGE access
- Warehouse for query execution

## Output

Deployed AI cost dashboard or cost analysis report depending on intent.

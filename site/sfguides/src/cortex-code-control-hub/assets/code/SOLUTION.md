# CoCo Control Hub — Solution Document

**Version:** 3.1

---

## 1. Business Requirements

### 1.1 Problem Statement

Snowflake Cortex Code (CLI + Snowsight + Desktop) is billed on token consumption. The native
platform provides per-surface daily credit limits per user, but large enterprises face these gaps:

| # | Gap | Impact |
|---|---|---|
| 1 | No cohort/role-level management | Admins must run N `ALTER USER` statements per team |
| 2 | No audit trail | Who changed what limit, when, why? |
| 3 | No self-service | User hits limit → blocked until midnight UTC |
| 4 | No intelligence | Unused credits from inactive users are wasted daily |
| 5 | No monitoring UI | No dashboards for usage trends by team/model/surface |
| 6 | No observability | No visibility into what prompts are being sent or how models perform |
| 7 | No hard monthly enforcement | Daily limits reset nightly; no monthly budget cap per user |

### 1.2 Solution Overview

A **Streamlit-in-Snowflake (SiS) application** that wraps native parameters with a full governance layer:

1. **Access Management** — Grant/revoke Cortex Code access via UI
2. **Credit Configuration** — Account, cohort, and user-level daily limits
3. **Native Per-User Quotas** _(Preview)_ — Hard monthly/daily enforcement via `SNOWFLAKE.CORE.QUOTA`
4. **Usage Trends** — Pre-aggregated dashboards with date/cohort filters and forecasting
5. **Cost Attribution** — Per-prompt and per-session credit costs via billing join
6. **AI Observability** — 11-tab span-level intelligence: latency, tokens, tool calls, sessions
7. **Responsible AI** — Prompt/response governance: keyword/regex/semantic policy rules, violation tracking, alerts
8. **Model Intelligence** — Cross-model latency, Token Economics, Cache Hit Rate, LLM-as-Judge quality scores
9. **Budget Forecast** — Linear regression projections for 7d/30d/90d credit spend
10. **Audit Trail** — Every action logged to `CC_AUDIT_LOG`

### 1.3 Stakeholders

| Role | Access | Pages |
|---|---|---|
| Platform Admin (ACCOUNTADMIN / CC_ADMIN_ROLE) | Full | All 18 pages |
| End User (CC_USER_ROLE) | Limited | Home + Credit Requests |

---

## 2. Architecture

### 2.1 Security Model (Owner's Rights SPs)

```
Human Roles                  App Roles                    Snowflake
─────────────               ──────────                   ─────────
ACCOUNTADMIN ──(one-time)──► CC_SP_OWNER_ROLE            ALTER ACCOUNT/USER
                              │ Owns all SPs               GRANT/REVOKE ROLES
                              │ Has MANAGE GRANTS           SHOW PARAMETERS
                              │ NEVER assumed by humans     CREATE QUOTA
                              │
CC_ADMIN_ROLE ──────────────► CC_APP_ROLE ──(CALL SP)──► SPs (EXECUTE AS OWNER)
CC_USER_ROLE  ──────────────► CC_APP_ROLE                │
                              │ USAGE on SPs only          ▼
                              │ Read ACCOUNT_USAGE         Platform actions
                              │ Read/write app tables
                              ✗ CANNOT ALTER USER directly
```

**Why this works:** The app runs as `CC_APP_ROLE` — it can only CALL stored procedures. The SPs
execute as owner (`CC_SP_OWNER_ROLE`) which has elevated privileges. Input validation (regex,
whitelist) happens inside each SP.

### 2.2 Data Architecture

```
SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS  (raw spans, Snowflake-managed)
         │
         ▼  [SP_CC_CLASSIFY_PROMPTS — nightly 2am UTC]
CC_PROMPT_EVENTS          ← typed columns, token economics, categories, cost, session ID
CC_PROMPT_VIOLATIONS      ← policy violations per prompt
CC_PROMPT_ANALYSIS_DAILY  ← per-user daily risk aggregation

ACCOUNT_USAGE.CORTEX_CODE_*_USAGE_HISTORY (billing, up to 45min latency)
         │
         ▼  [SP_CC_REFRESH_USAGE_SUMMARIES — every 30 min]
CC_USAGE_DAILY_SUMMARY    ← credits/tokens/queries by user+surface+date (all billing)
CC_USAGE_HOURLY_SUMMARY   ← hourly breakdown for trend prediction

AI_OBSERVABILITY_EVENTS.Agent span (request_id = billing REQUEST_ID)
         │
         ▼  [Cost Attribution per-request query]
Per-prompt & per-session cost (joins billing via Agent.request_id)
```

### 2.3 Session ID Architecture

`SESSION_ID` in the app is the real terminal session ID from
`CodingAgentRun.snow.ai.observability.agent.coding_agent.session_id`.
Format: `USER:ACCOUNT:CONNECTION_ID`. Multiple messages in the same CLI session share the same
SESSION_ID. Falls back to `trace_id` (per-message) when no `CodingAgentRun` span is available.

### 2.4 Intelligence Engine (Credit Rebalancing)

When a user requests additional credits:
1. Identifies all members in the same cohort (role)
2. Predicts rest-of-day usage using EWMA on 14 days of hourly data
3. Same day-of-week patterns weighted 60% higher
4. Calculates safe surplus = `limit - used_today - predicted_remaining - buffer`
5. Ranks donors by surplus, selects minimum donors to cover request
6. Auto-executes or queues for admin approval

---

## 3. File Structure

```
cortex-code-credit-manager/
├── streamlit_app.py              Entry point, sidebar nav, page dispatch, CSS
├── config.py                     Constants, security helpers, page lists
├── config.yaml                   Deployment DB/schema + admin role whitelist
├── audit.py                      log_activity() → CC_AUDIT_LOG
├── utils.py                      Snowflake helpers, cached data access, SP calls
├── intelligence.py               EWMA prediction, surplus calc, donor selection
├── sp_definitions.py             DDL generators for all Python SPs
├── pages/
│   ├── home.py                   Personal dashboard (all users)
│   ├── setup.py                  5-phase install wizard (admin)
│   ├── access_management.py      Grant/revoke Cortex access (admin)
│   ├── credit_config.py          Account/cohort/user limits + AI Budgets (admin)
│   ├── user_quotas.py            Native per-user quotas — SNOWFLAKE.CORE.QUOTA (Preview)
│   ├── model_access.py           Model tier management + role-model mapping (admin)
│   ├── credit_requests.py        Request form (user) + approval queue (admin)
│   ├── usage_trends.py           Trend charts, heatmap, spike detection (admin)
│   ├── budget_forecast.py        Linear regression forecasting (admin)
│   ├── cost_attribution.py       Per-prompt & per-session costs (admin)
│   ├── observability.py          11-tab AI Observability dashboard (admin)
│   ├── user_intelligence.py      Per-user credit + prompt + quality profile (admin)
│   ├── prompt_analysis.py        Responsible AI governance dashboard (admin)
│   ├── policy_rules.py           Keyword/regex/semantic rule CRUD (admin)
│   ├── alerts.py                 Alert rules, history, email notifications (admin)
│   ├── model_intelligence.py     LLM comparison: latency, tokens, quality (admin)
│   ├── settings.py               App configuration (admin)
│   └── audit_logs.py             Audit log viewer (admin)
├── prerequisites.sql             DDL, SPs, tasks, alerts, RBAC setup
├── environment.yml               Anaconda channel dependencies
├── pyproject.toml                Python 3.11 + streamlit[snowflake]
├── snowflake.yml                 SiS deployment config
├── SOLUTION.md                   This document
├── DEPLOYMENT_GUIDE.md           Step-by-step deployment
└── AGENTS.md                     Cortex Code CLI project context
```

---

## 4. Key Features

### Native Per-User Quotas (Preview)
Uses `SNOWFLAKE.CORE.QUOTA` objects for hard monthly/daily enforcement. Blocks fire within
**minutes** of breach and auto-release at cycle reset. Cohort scoping via `CC_COHORT_TAG` —
all resolved cohort members are tagged and the quota scopes to that tag.

### AI Observability (11 tabs)
Activity Trend · Top Users · Model Usage · Tool Calls · Prompt Browser · Sessions · Token
Economics · Tool Intelligence · Entrypoints · Quality Scores · Prompt Patterns

### Token Economics
Input/output/cache breakdown extracted from `AI_OBSERVABILITY_EVENTS` `CodingAgent.Step-0`
spans. Cache Hit Rate = `cache_read / (cache_read + cache_write)`.
Input tokens already include cache_read — total = input + output only.

### Responsible AI Classification
3-tier pipeline: KEYWORD (free, SQL FLATTEN) → REGEX (Python) → SEMANTIC (AI_CLASSIFY).
Classifies prompts into: PII_RISK, SECURITY, PERSONAL_USE, USAGE_ANOMALY, and CUSTOM categories.

### LLM-as-Judge Quality Evaluation (Experimental)
Scores AI responses on 4 dimensions: Answer Relevance, Groundedness, Coherence, Safety.
Uses `SNOWFLAKE.CORTEX.AI_COMPLETE` with a configurable judge model.

---

## 5. Stored Procedures

All SPs are `EXECUTE AS OWNER` (CC_SP_OWNER_ROLE).

| SP | Phase | Purpose |
|---|---|---|
| SP_CC_SET_ACCOUNT_CREDIT_LIMIT | A | ALTER ACCOUNT SET surface limit |
| SP_CC_SET_USER_CREDIT_LIMIT | A | ALTER USER SET surface limit |
| SP_CC_UNSET_USER_CREDIT_LIMIT | A | ALTER USER UNSET surface limit |
| SP_CC_GRANT_CORTEX_ACCESS | A | GRANT DATABASE ROLE to user |
| SP_CC_REVOKE_CORTEX_ACCESS | A | REVOKE DATABASE ROLE from user |
| SP_CC_REBALANCE_CREDITS | A | Transfer credits between users |
| SP_CC_BULK_GRANT_ACCESS | A | Batch grant to role members |
| SP_CC_BULK_SET_COHORT_LIMITS | A | Batch set limits for all cohort members |
| SP_CC_COMPUTE_REBALANCE | A | EWMA prediction + donor selection |
| SP_CC_REFRESH_USAGE_SUMMARIES | A | Incremental MERGE from ACCOUNT_USAGE |
| SP_CC_DAILY_RESET_LIMITS | A | Reset rebalanced limits to cohort defaults |
| SP_CC_RESOLVE_USER_COHORTS | A | Build CC_USER_COHORT_RESOLVED from role grants |
| SP_CC_CLASSIFY_PROMPTS | C | Nightly prompt classification + cost attribution |
| SP_CC_CHECK_ALERTS | C | Batch + real-time alert evaluation |
| SP_CC_EVALUATE_RESPONSES | C | LLM-as-Judge quality scoring |
| SP_CC_REFRESH_BUDGET_USAGE | C | AI Budget spending refresh |
| SP_CC_MANAGE_QUOTA | C | Native per-user quota management (Preview) |

---

## 6. Scheduled Tasks

| Task | Schedule | What |
|---|---|---|
| CC_REFRESH_USAGE_SUMMARIES | Every 30 min | Incremental refresh of daily + hourly summaries |
| CC_DAILY_RESET_LIMITS | Midnight UTC | Restore rebalanced limits to cohort defaults |
| CC_CLASSIFY_PROMPTS_TASK | 2am UTC | Nightly prompt classification + cost attribution |
| CC_ALERT_CHECK | Every 1 hr | Batch alert evaluation with email notifications |
| CC_REALTIME_VIOLATION_ALERT | Every 1 hr | Stream-based HIGH severity detection |

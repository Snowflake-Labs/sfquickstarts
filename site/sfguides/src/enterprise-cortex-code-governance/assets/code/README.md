# Cortex Code Credit Manager

> Govern AI spend. Rebalance automatically. Audit everything.

A **Streamlit-in-Snowflake** application that wraps Snowflake's native Cortex Code credit parameters with enterprise governance — cohort budgets, intelligent rebalancing, model-tier enforcement, and a full audit trail. Everything runs inside your Snowflake account. Zero external dependencies.

[![Snowflake](https://img.shields.io/badge/Built%20for-Snowflake-29B5E8)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
[![Platform](https://img.shields.io/badge/Deployment-Streamlit%20in%20Snowflake-blue)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

---

## The Problem

Snowflake Cortex Code bills on token consumption. Native controls are minimal:

```sql
ALTER ACCOUNT SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = 20;  -- everyone
ALTER USER john SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = 30; -- one person
```

For an enterprise with 5,000–50,000 users this doesn't scale:

| Gap | Business impact |
|---|---|
| No team-level budgets | Admin runs N `ALTER USER` statements per team change |
| No audit trail | Compliance can't answer who changed what limit, when, and why |
| No self-service | Developer hits limit at 2 PM → blocked for the day → files a ticket |
| No intelligence | 60 % of daily allocations go unused while others are blocked |
| No model governance | Junior analyst uses Opus when Sonnet handles the task fine |
| No budget forecasting | Finance asks "what will AI cost next quarter?" — no answer |
| No delegation | Single platform team bottleneck for all business domains |

---

## What's Inside

### 10 Pages

| Page | Purpose |
|---|---|
| **Setup** | In-app setup wizard — verify prerequisites, create missing objects, seed defaults. No CLI required. |
| **Home** | Feature overview + account KPIs, top users, model breakdown, daily credit trend. |
| **Access Management** | Grant `CORTEX_USER` + `COPILOT_USER` to users, roles, or by user tag. View role inheritance. |
| **Credit Configuration** | Set daily limits at account, cohort (role or tag), or individual user level. Temporary overrides auto-revert. |
| **Usage Trends** | Stacked area trend, scatter plot (users coloured by cohort), timezone-aware heatmap, spike detection, recommendations. |
| **Budget Forecast** | Linear regression projections. Trend-adjusted 7d / 30d / 90d. Per-cohort spend breakdown. |
| **Model Access** | Discover models in use, assign to tiers (TIER_1/2/3), map tiers to roles, enforce via `CORTEX_MODELS_ALLOWLIST`. |
| **Credit Requests** | User self-service: request more credits or a model tier upgrade. Admin/domain-lead approval queue with system recommendations. |
| **Settings** | Approval mode, rebalance parameters, donor strategy, rate limits, domain lead assignment. |
| **Audit Log** | Immutable log of every grant, limit change, approval, rejection, and rebalance. Filterable, CSV export. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit in Snowflake                  │
│   (owner-rights: all SQL runs as Streamlit owner role)  │
│                                                         │
│  pages/          ← UI rendering, zero direct DDL        │
│  utils.py        ← Read-only cached data access         │
│  intelligence.py ← EWMA prediction + donor selection    │
│  audit.py        ← Write-only audit log                 │
│  config.py       ← 3-tier DB/schema resolution          │
│  sp_definitions.py ← Bulk SP DDL for setup              │
└──────────────┬───────────────────────────────┬──────────┘
               │  CALL SP (elevated actions)    │  SELECT (reads)
               ▼                               ▼
┌──────────────────────┐         ┌──────────────────────────┐
│  Owner-Rights SPs    │         │  App Tables (CC_*)        │
│  EXECUTE AS OWNER    │         │  CC_USAGE_DAILY_SUMMARY   │
│  ─────────────────   │         │  CC_USAGE_HOURLY_SUMMARY  │
│  SP_CC_BULK_SET_*    │         │  CC_CREDIT_CONFIG         │
│  SP_CC_BULK_GRANT_*  │         │  CC_AUDIT_LOG             │
│  SP_CC_SET_USER_*    │         │  CC_CREDIT_REQUESTS       │
│  SP_CC_GRANT_ACCESS  │         │  CC_APP_CONFIG            │
│  SP_CC_REBALANCE_*   │         │  CC_MODEL_CONFIG          │
│  SP_CC_REFRESH_*     │         │  CC_USER_COHORT_RESOLVED  │
│  SP_CC_DAILY_RESET   │         └──────────────────────────┘
└──────────────────────┘
               │  ALTER USER / GRANT DATABASE ROLE
               ▼
┌──────────────────────────────────┐
│   Snowflake Account Metadata     │
│   User parameters, role grants   │
│   ACCOUNT_USAGE views            │
└──────────────────────────────────┘
```

### Owner-Rights Execution Model

All SQL — including `ALTER USER`, `GRANT DATABASE ROLE`, and `CREATE TABLE` — runs as the role that **owns the Streamlit object** (recommended: ACCOUNTADMIN). End users never need elevated privileges. Every privileged action is channelled through stored procedures that validate inputs before executing.

### Role Separation

| Role | Owns | Purpose |
|---|---|---|
| `CC_SP_OWNER_ROLE` | All SPs and tasks | Has MANAGE GRANTS + ALTER USER privileges. Assumed by nobody — only used via EXECUTE AS OWNER. |
| `CC_APP_ROLE` | App tables | Streamlit runtime role. Can read/write CC_* tables and CALL SPs. |
| `CC_ADMIN_ROLE` | — | Inherits CC_APP_ROLE. Grant to platform admins who manage the app. |
| `CC_USER_ROLE` | — | Inherits CC_APP_ROLE. Grant to Cortex Code end users. |

> **In practice** you don't need CC_ADMIN_ROLE or CC_USER_ROLE. Just add your existing org roles to `admin_roles` in `config.yaml`. The only non-negotiable role is `CC_SP_OWNER_ROLE` — it's what makes `ALTER USER` safe without handing out ACCOUNTADMIN.

---

## Intelligence Engine

When a user requests additional credits, the system decides automatically whether to fulfill the request — no admin intervention needed in AUTO mode.

### How EWMA Prediction Works

```
For each potential donor in the cohort:

  1. Collect 14 days of hourly usage history
  2. For each remaining hour today:
       predicted_hour = ewm(alpha=0.3).mean()     ← EWMA, recent data weighted higher
       if >= 3 same-weekday observations:
           predicted_hour = 0.4 × all-days + 0.6 × same-weekday   ← DOW adjustment
  3. predicted_remaining = sum(predicted hours)
  4. safe_surplus = limit - used_today - predicted_remaining - (limit × buffer%)
  5. transferable = min(safe_surplus, limit × max_transfer_cap%)
```

**Cold-start guard:** Users with fewer than 5 days of history are treated as full-consumption (transferable = 0). New joiners are never selected as donors.

### Four Donor Strategies

| Strategy | Behaviour | Best for |
|---|---|---|
| **WEIGHTED_RANDOM** | Probabilistic selection proportional to surplus. Same person not always chosen. | Most deployments (default) |
| **HIGHEST_SURPLUS** | Always take from whoever has the most available. Predictable. | Conservative/audit-sensitive orgs |
| **MINIMUM_DONORS** | Tries to satisfy the full request from a single donor first; falls back to greedy-from-largest. | Minimise blast radius |
| **ROUND_ROBIN** | Skips donors who donated in the last N hours. Most equitable rotation. | Fairness-sensitive teams |

---

## Deployment

### Option A — In-App Setup (no CLI required)

1. Deploy the Streamlit app:
   ```bash
   git clone https://github.com/Snowflake-Labs/sfquickstarts.git
   cd sfquickstarts/site/sfguides/src/enterprise-cortex-code-governance/assets/code
   ```

2. Edit `config.yaml`:
   ```yaml
   deployment:
     database: YOUR_DB
     schema: YOUR_SCHEMA

   admin:
     roles:
       - ACCOUNTADMIN
       - YOUR_PLATFORM_ADMIN_ROLE   # optional
   ```

3. Deploy:
   ```bash
   snow streamlit deploy \
     --connection YOUR_CONNECTION \
     --database YOUR_DB \
     --schema YOUR_SCHEMA
   ```

4. Open the app → **Setup** page → click **Run Check**, then **Create Missing Objects**, then **Seed Default Settings**, then **Run Initial Data Refresh**.

Done. All DDL (tables, SPs, roles, tasks) runs from within the app as the owner role.

---

### Option B — CLI Prerequisites (traditional)

If you prefer to run the DDL manually before deploying:

```bash
snow sql -f prerequisites.sql --connection YOUR_CONNECTION
```

Creates:

| Type | Count | Names |
|---|---|---|
| Roles | 4 | CC_SP_OWNER_ROLE, CC_APP_ROLE, CC_ADMIN_ROLE, CC_USER_ROLE |
| Tables | 11 | CC_CREDIT_CONFIG, CC_AUDIT_LOG, CC_USAGE_DAILY_SUMMARY, CC_USAGE_HOURLY_SUMMARY, CC_CREDIT_REQUESTS, CC_APP_CONFIG, CC_MODEL_CONFIG, CC_MODEL_ROLE_MAPPING, CC_USER_COHORT_RESOLVED, CC_COHORT_LEADS, CC_SP_JOB_LOG |
| Stored Procs | 13 | SP_CC_SET_USER_CREDIT_LIMIT, SP_CC_BULK_SET_COHORT_LIMITS, SP_CC_GRANT_CORTEX_ACCESS, SP_CC_BULK_GRANT_ACCESS, SP_CC_REBALANCE_CREDITS, SP_CC_REFRESH_USAGE_SUMMARIES, SP_CC_DAILY_RESET_LIMITS, SP_CC_RESOLVE_USER_COHORTS, SP_CC_EXPIRE_TEMPORARY_CREDITS, SP_CC_ENFORCE_MODEL_ACCESS, SP_CC_SET_ACCOUNT_CREDIT_LIMIT, SP_CC_UNSET_USER_CREDIT_LIMIT, SP_CC_REVOKE_CORTEX_ACCESS |
| Tasks | 2 | CC_REFRESH_USAGE_SUMMARIES (every 30 min), CC_DAILY_RESET_LIMITS (midnight UTC) |

Then deploy and open the app. Skip the "Create Missing Objects" step — objects already exist.

---

### Verification

After setup, run **Setup → Run Check**. All items should show green:

```
TABLES (11/11)      SPs (13/13)         TASKS (2/2)        ROLES (4/4)
✓ CC_CREDIT_CONFIG  ✓ SP_CC_SET_USER_*  ✓ CC_REFRESH_*     ✓ CC_SP_OWNER_ROLE
✓ CC_AUDIT_LOG      ✓ SP_CC_BULK_*      ✓ CC_DAILY_*       ✓ CC_APP_ROLE
...                 ...                                     ✓ CC_ADMIN_ROLE
                                                            ✓ CC_USER_ROLE
```

---

## Configuration Reference

### `config.yaml`

```yaml
deployment:
  database: CORTEX_CODE_MGMT   # DB where app tables and SPs live
  schema: APP                   # Schema within that DB

admin:
  roles:                        # Roles that see all 10 admin pages
    - ACCOUNTADMIN
    - SYSADMIN                  # optional
```

The sidebar **Deployment Target** picker overrides these values at runtime without redeploying — useful when managing multiple environments from one app.

### App Settings (via Settings page)

| Setting | Default | Description |
|---|---|---|
| `APPROVAL_MODE` | `ADMIN` | `AUTO` = instant rebalance. `ADMIN` = queue for review. |
| `DONOR_STRATEGY` | `WEIGHTED_RANDOM` | See Intelligence Engine section above. |
| `REBALANCE_BUFFER_PCT` | `20` | Safety margin % kept with donor after prediction. |
| `REBALANCE_MAX_TRANSFER_PCT` | `50` | Max % of donor's limit that can be transferred. |
| `REBALANCE_LOOKBACK_DAYS` | `14` | Days of hourly history used for EWMA prediction. |
| `DONOR_PROTECTION_HOURS` | `4` | Hours before a recent donor can be selected again (ROUND_ROBIN). |
| `MAX_REQUESTS_PER_USER_PER_DAY` | `2` | Rate limit: max credit requests per UTC day. |
| `REQUEST_COOLDOWN_MINUTES` | `60` | Wait time between two requests. |
| `MAX_EXTRA_CREDITS_PER_WEEK` | `20` | Rolling 7-day extra credit cap per user. |
| `DAILY_RESET_ENABLED` | `TRUE` | Restore rebalanced limits to cohort defaults at midnight UTC. |

---

## Scale Design

Built for 50,000+ users:

| Challenge | Solution |
|---|---|
| Cohort apply (N ALTER USER calls) | `SP_CC_BULK_SET_COHORT_LIMITS` — single SP call, server-side loop, no CLIENT_ABORT risk |
| Bulk access grants | `SP_CC_BULK_GRANT_ACCESS` — single SP call with JSON array, returns `{success, failed, errors}` |
| User search dropdown | Server-side `ACCOUNT_USAGE.USERS ILIKE '%query%' LIMIT 50` — never loads 50K users into browser |
| Per-render SQL overhead | `get_current_user`, `user_is_admin`, `SHOW DATABASES` all cached with `@st.cache_data(ttl=600)` |
| New user as donor | Cold-start guard: < 5 days history → transferable = 0 |
| Managed service accounts in role picker | UUID-pattern and SVC_ prefix filter on `SHOW GRANTS OF ROLE` results |

---

## SQL Injection Prevention

Four independent layers:

### Layer 1 — Python identifier validation

```python
def sanitize_identifier(identifier: str) -> str:
    if not re.match(r"^[A-Za-z0-9_$\-\.@]+$", identifier):
        raise ValueError(f"Invalid identifier: {identifier}")
    return identifier.upper()
```

### Layer 2 — SQL literal escaping

```python
def escape_sql_literal(value) -> str:
    return str(value).replace("'", "''")
```

### Layer 3 — SP-level REGEXP_LIKE validation

Every stored procedure re-validates its inputs:
```sql
IF (NOT REGEXP_LIKE(:USER_NAME, '^[A-Za-z0-9_$\\-\\.@]+$')) THEN
    RETURN 'ERROR: Invalid username format';
END IF;
```

### Layer 4 — Role separation

`CC_APP_ROLE` cannot execute `ALTER USER` or `GRANT` directly. Only owner-rights SPs can — and they validate first. A compromised Streamlit session cannot escalate privileges beyond what `CC_APP_ROLE` is explicitly allowed.

---

## Daily Data Flow

```
Every 30 min:
  CC_REFRESH_USAGE_SUMMARIES task
    └─ MERGE from CORTEX_CODE_CLI_USAGE_HISTORY
    └─ MERGE from CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
    └─ Incremental only (since last REFRESHED_AT)
    └─ Updates CC_USAGE_DAILY_SUMMARY + CC_USAGE_HOURLY_SUMMARY

00:00 UTC:
  CC_DAILY_RESET_LIMITS task
    └─ SP_CC_EXPIRE_TEMPORARY_CREDITS: revert expired overrides
    └─ SP_CC_RESOLVE_USER_COHORTS: rebuild recursive role hierarchy (depth 10)
    └─ Reset rebalanced limits → cohort defaults
    └─ Permanent admin overrides are NOT reset
    └─ Audit log entry per reset action
```

> **Note:** ACCOUNT_USAGE views have up to 90-minute latency. Data appearing in the app may lag real-time usage by up to 2 hours.

---

## Timezone

Daily credit limits always reset at **midnight UTC** regardless of where users are. The timezone selector in the sidebar is display-only — it shifts the heatmap hours for readability but does not affect when limits reset.

---

## Repository Structure

```
cortex-code-credit-manager/
├── streamlit_app.py      Main entry, sidebar nav, page dispatch
├── config.py             Constants, 3-tier DB/schema resolution, security helpers
├── utils.py              Cached read queries, search_users, call_sp, call_bulk_sp
├── intelligence.py       EWMA prediction, surplus calculation, donor strategies
├── audit.py              Single log_activity() function, always SELECT-based INSERT
├── sp_definitions.py     Bulk SP DDL (SP_CC_BULK_GRANT_ACCESS, SP_CC_BULK_SET_COHORT_LIMITS)
├── prerequisites.sql     One-time setup DDL — roles, tables, SPs, tasks
├── config.yaml           Deployment target + admin role whitelist
├── environment.yml       Streamlit-in-Snowflake package manifest (no pinned versions)
├── snowflake.yml         Snow CLI deployment spec
└── pages/
    ├── home.py            Feature tiles + account KPIs + personal usage
    ├── setup.py           In-app setup wizard with green/red verification chips
    ├── access_management.py  Grant/revoke + role membership + tag-based + inheritance viewer
    ├── credit_config.py   Account / cohort / user limit configuration
    ├── usage_trends.py    Altair charts, heatmap, spike detection, recommendations
    ├── budget_forecast.py Linear regression projection, per-cohort breakdown
    ├── model_access.py    Model discovery, tier assignment, role-model mapping
    ├── credit_requests.py Self-service requests + rate limiting + admin approval queue
    ├── settings.py        All configurable parameters with worked examples
    └── audit_logs.py      Filterable audit trail, CSV export
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Snowflake Enterprise or higher | Required for ACCOUNT_USAGE views |
| ACCOUNTADMIN (one-time) | For running setup — either via CLI or in-app |
| Cortex Code enabled on account | Contact your Snowflake account team if not active |
| Any warehouse (XSMALL sufficient) | App is read-heavy; smallest warehouse works fine |
| Snowflake CLI (Option B only) | `pip install snowflake-cli-labs` |

---

## Contributing

Visualization standard: **Altair only**. Every chart must use `configure_view(strokeWidth=0)` and `.configure(background='#0e1117')`. No Plotly. No pie charts. No hardcoded FQNs — always use `fq_table(session, TABLE_NAME)`.

Built with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code).

# Cortex Code Credit Manager — Solution Document

**Version:** 1.0.0 | 
---

## 1. Business Requirements Document (BRD)

### 1.1 Problem Statement

Snowflake Cortex Code (CLI + Snowsight) is billed on token consumption. The native
platform provides two credit-limit parameters:

- `CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER`
- `CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER`

Each can be set at **account level** (applies to all users) or **user level** (overrides
account). Only `ACCOUNTADMIN` can execute the `ALTER` statements.

**Gaps for enterprise customers (5,000+ users):**

| # | Gap | Impact |
|---|---|---|
| 1 | No cohort/role-level management | Admins must run N `ALTER USER` statements per team |
| 2 | No audit trail | Who changed what limit, when, why? |
| 3 | No self-service | User hits limit at 1 PM → blocked until next day |
| 4 | No intelligence | Unused credits from inactive users are wasted daily |
| 5 | No monitoring UI | No dashboards for usage trends by team/model |
| 6 | ACCOUNT_USAGE latency (up to 60 min) | Decisions need analytics, not stale data |

### 1.2 Solution Overview

A **Streamlit-in-Snowflake (SiS) application** that wraps the native parameters with:

1. **Access Management** — Grant/revoke `SNOWFLAKE.CORTEX_USER` via UI
2. **Credit Configuration** — Account, cohort (role), and user-level limits
3. **Usage Trends** — Pre-aggregated dashboards (Plotly) with date/cohort filters
4. **Credit Requests** — Self-service with intelligent rebalancing within cohorts
5. **Full Audit Trail** — Every action logged to `CC_AUDIT_LOG`
6. **Admin Controls** — Role-gated pages, configurable approval mode

### 1.3 Stakeholders

| Role | Access | Pages |
|---|---|---|
| Platform Admin (ACCOUNTADMIN / CC_ADMIN_ROLE) | Full | All 7 pages |
| End User (CC_USER_ROLE) | Limited | Home + Credit Requests |

### 1.4 Success Criteria

- Admins can set limits for a 50-person team in one action (< 30 seconds)
- Users can request additional credits without filing a ticket
- All actions auditable with actor, timestamp, old/new values
- Dashboard loads in < 3 seconds (pre-aggregated data)
- No human ever directly assumes the elevated SP owner role

---

## 2. Architecture

### 2.1 Security Model (Owner's Rights SPs)

```
Human Roles                  App Roles                    Snowflake
─────────────               ──────────                   ─────────
ACCOUNTADMIN ──(one-time)──► CC_SP_OWNER_ROLE            ALTER ACCOUNT/USER
                             │ Owns all SPs               GRANT/REVOKE ROLES
                             │ Has MANAGE GRANTS           SHOW PARAMETERS
                             │ NEVER assumed by humans
                             │
CC_ADMIN_ROLE ──────────────► CC_APP_ROLE ──(CALL SP)──► SPs (EXECUTE AS OWNER)
CC_USER_ROLE  ──────────────► CC_APP_ROLE                │
                             │ USAGE on SPs only          ▼
                             │ Read ACCOUNT_USAGE         Platform actions
                             │ Read/write app tables
                             ✗ CANNOT ALTER USER directly
```

**Why this works:** The Streamlit app runs as `CC_APP_ROLE`. It can only CALL stored
procedures — never run `ALTER USER` directly. The SPs execute as the owner role
(`CC_SP_OWNER_ROLE`) which has the elevated privileges. Input validation happens
inside each SP (regex check on identifiers, whitelist on parameter names).

### 2.2 Data Architecture

```
ACCOUNT_USAGE (source, up to 60 min latency)
├── CORTEX_CODE_CLI_USAGE_HISTORY
├── CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
└── USERS (for USER_ID → USER_NAME join)
        │
        ▼  (Scheduled TASK every 30 min — incremental MERGE)
App Tables (pre-aggregated, fast reads)
├── CC_USAGE_DAILY_SUMMARY     ← daily × user × surface × model
├── CC_USAGE_HOURLY_SUMMARY    ← hourly × user × surface (for trend prediction)
├── CC_CREDIT_CONFIG           ← cohort definitions + user overrides
├── CC_CREDIT_REQUESTS         ← self-service workflow queue
├── CC_AUDIT_LOG               ← every action
└── CC_APP_CONFIG              ← key-value settings
```

**Performance design decisions:**
- All dashboard queries hit pre-aggregated tables, never ACCOUNT_USAGE directly
- `USAGE_CACHE_TTL = 300s` on all data reads (Streamlit `@st.cache_data`)
- Incremental MERGE uses watermark (`MAX(REFRESHED_AT)`) — only processes new rows
- LATERAL FLATTEN on `CREDITS_GRANULAR` extracts per-model breakdown at ETL time
- Hourly summary table enables EWMA trend prediction without re-scanning raw data

### 2.3 Intelligence Engine (Credit Rebalancing)

When a user requests additional credits, the system:

1. Identifies all members in the same cohort (role)
2. For each member, predicts rest-of-day usage using EWMA on 14 days of hourly data
3. Same day-of-week patterns weighted 60% higher (e.g., Mondays are different from Fridays)
4. Calculates safe surplus = `limit - used_today - predicted_remaining - buffer`
5. Ranks donors by surplus, selects minimum number of donors to cover request
6. Either auto-executes (ALTER USER for donor + requester) or queues for admin approval

**Safeguards:**
- 20% buffer (configurable) — donors never reduced below predicted need + buffer
- 50% max transfer cap — never take more than half a donor's original limit
- Midnight reset task restores all limits to cohort defaults
- User overrides are respected (excluded from reset)

---

## 3. File Structure

```
cortex-code-credit-manager/
├── streamlit_app.py              Entry point, sidebar nav, page dispatch, CSS
├── config.py                     Constants, security helpers, admin role check
├── config.yaml                   Deployment DB/schema + admin role whitelist
├── audit.py                      log_activity() → CC_AUDIT_LOG
├── utils.py                      Snowflake helpers, cached data access, SP calls
├── intelligence.py               EWMA prediction, surplus calc, donor selection
├── pages/
│   ├── home.py                   Personal dashboard (all users)
│   ├── access_management.py      Grant/revoke Cortex access (admin)
│   ├── credit_config.py          Account/cohort/user limits (admin)
│   ├── usage_trends.py           Dashboards + Plotly charts (admin)
│   ├── credit_requests.py        Request form (user) + approval queue (admin)
│   ├── settings.py               App configuration (admin)
│   └── audit_logs.py             Audit log viewer (admin)
├── prerequisites.sql             DDL, owner-rights SPs, tasks, RBAC
├── environment.yml               Anaconda channel dependencies
├── snowflake.yml                 SiS deployment config
├── SOLUTION.md                   This document
├── DEPLOYMENT_GUIDE.md           Step-by-step deployment
└── AGENTS.md                     Cortex Code CLI project context
```

---

## 4. Page Descriptions

### Home (All Users)
- Current CLI + Snowsight limits with progress bars
- Today's usage (from pre-aggregated hourly table)
- 7-day personal trend (stacked bar chart)
- Warning when approaching limit (70%+ threshold)

### Access Management (Admin)
- Search users or select by role
- Multiselect → grant/revoke `SNOWFLAKE.CORTEX_USER` or `SNOWFLAKE.CORTEX_ANALYST_USER`
- Current access status table with revoke capability
- Every action audited

### Credit Configuration (Admin)
- **Tab 1: Account Defaults** — Set CLI + Snowsight limits for entire account
- **Tab 2: Cohort (by Role)** — Select role → set limits → preview ALTER statements → apply to all members. "Sync New Members" button for role membership drift
- **Tab 3: User Override** — Override cohort defaults for power users. Remove override to fall back to cohort
- Config stored in `CC_CREDIT_CONFIG` (ACCOUNT / COHORT / USER_OVERRIDE types)

### Usage Trends (Admin)
- Date presets: 1D / 7D / 30D / 90D / 365D
- Cohort filter dropdown
- Summary metrics: total credits, active users, avg/user, total requests
- **Trend tab:** Stacked area chart (CLI vs Snowsight by day)
- **By Cohort tab:** Model usage pie chart + data table
- **By User tab:** Top 20 users horizontal bar chart
- **Heatmap tab:** Hour-of-day × day-of-week usage patterns

### Credit Requests (User + Admin)
- **User section:** Current status, request form (surface, amount, reason), system feasibility analysis, request history
- **Admin section (below):** Pending approval queue with system recommendation, approve/reject buttons

### Settings (Admin)
- Approval mode: AUTO or ADMIN (radio)
- Rebalance buffer %, max transfer cap %, lookback days
- Daily reset toggle

### Audit Log (Admin)
- Filterable by period and action type
- CSV export

---

## 5. Data Model

### CC_CREDIT_CONFIG
| Column | Type | Description |
|---|---|---|
| CONFIG_ID | NUMBER (PK, auto) | Unique identifier |
| CONFIG_TYPE | VARCHAR | ACCOUNT, COHORT, or USER_OVERRIDE |
| ROLE_NAME | VARCHAR | Cohort role (NULL for ACCOUNT/USER_OVERRIDE) |
| USER_NAME | VARCHAR | Override user (NULL for ACCOUNT/COHORT) |
| CLI_DAILY_LIMIT | NUMBER(10,2) | CLI credit limit |
| SNOWSIGHT_DAILY_LIMIT | NUMBER(10,2) | Snowsight credit limit |
| IS_ACTIVE | BOOLEAN | Soft delete flag |
| CREATED_BY / CREATED_AT | | Creator and timestamp |
| UPDATED_BY / UPDATED_AT | | Last modifier and timestamp |

### CC_AUDIT_LOG
| Column | Type | Description |
|---|---|---|
| LOG_ID | NUMBER (PK, auto) | Unique identifier |
| TIMESTAMP | TIMESTAMP_LTZ | When |
| ACTOR / ACTOR_ROLE | VARCHAR | Who |
| ACTION_TYPE | VARCHAR | What (GRANT_ACCESS, SET_COHORT_LIMIT, REBALANCE_INCREASE, etc.) |
| TARGET_USER / TARGET_ROLE | VARCHAR | Affected entity |
| DETAILS | VARIANT | JSON payload with context |
| OLD_VALUE / NEW_VALUE | VARCHAR | Before/after |
| STATUS | VARCHAR | SUCCESS or FAILED |

### CC_USAGE_DAILY_SUMMARY
| Column | Type | Description |
|---|---|---|
| USAGE_DATE | DATE (PK) | Calendar date |
| USER_NAME | VARCHAR (PK) | User |
| SURFACE | VARCHAR (PK) | CLI or SNOWSIGHT |
| MODEL_NAME | VARCHAR (PK) | LLM model used |
| COHORT_ROLE | VARCHAR | Resolved cohort at refresh time |
| TOTAL_CREDITS / TOTAL_TOKENS / QUERY_COUNT | NUMBER | Aggregated metrics |
| REFRESHED_AT | TIMESTAMP_LTZ | Watermark for incremental refresh |

### CC_USAGE_HOURLY_SUMMARY
Same as daily but with `USAGE_HOUR` (0-23) added to PK. Used for trend prediction.

### CC_CREDIT_REQUESTS
| Column | Type | Description |
|---|---|---|
| REQUEST_ID | NUMBER (PK, auto) | Unique identifier |
| REQUESTER / COHORT_ROLE / SURFACE | VARCHAR | Request context |
| AMOUNT_REQUESTED / AMOUNT_APPROVED | NUMBER | Credits |
| REASON | VARCHAR | User-provided justification |
| DONOR_USER / DONOR_REDUCTION | | Who gave, how much |
| STATUS | VARCHAR | PENDING, APPROVED, REJECTED |
| APPROVED_BY / APPROVED_AT / REJECTION_REASON | | Resolution |

### CC_APP_CONFIG
Key-value settings table. Keys: `APPROVAL_MODE`, `REBALANCE_BUFFER_PCT`,
`REBALANCE_MAX_TRANSFER_PCT`, `REBALANCE_LOOKBACK_DAYS`, `DAILY_RESET_ENABLED`.

---

## 6. Stored Procedures (Owner's Rights)

All SPs are `EXECUTE AS OWNER` (CC_SP_OWNER_ROLE). Input validation inside each SP.

| SP Name | Parameters | What It Does |
|---|---|---|
| SP_CC_SET_ACCOUNT_CREDIT_LIMIT | surface, limit | ALTER ACCOUNT SET/UNSET |
| SP_CC_SET_USER_CREDIT_LIMIT | username, surface, limit | ALTER USER SET |
| SP_CC_UNSET_USER_CREDIT_LIMIT | username, surface | ALTER USER UNSET |
| SP_CC_GRANT_CORTEX_ACCESS | username, database_role | GRANT DATABASE ROLE TO USER |
| SP_CC_REVOKE_CORTEX_ACCESS | username, database_role | REVOKE DATABASE ROLE FROM USER |
| SP_CC_REBALANCE_CREDITS | donor, donor_limit, requester, requester_limit, surface | ALTER both users |
| SP_CC_REFRESH_USAGE_SUMMARIES | (none) | Incremental MERGE from ACCOUNT_USAGE |
| SP_CC_DAILY_RESET_LIMITS | (none) | Reset all users to cohort defaults |

---

## 7. Scheduled Tasks

| Task | Schedule | What |
|---|---|---|
| CC_REFRESH_USAGE_SUMMARIES | Every 30 min | Incremental refresh of daily + hourly summary tables |
| CC_DAILY_RESET_LIMITS | Midnight UTC | Restore rebalanced limits to cohort defaults |

---

## 8. Self-Review: Engineering Assessment

### Performance
- **Dashboard latency:** All reads from pre-aggregated tables with 5-min cache. No ACCOUNT_USAGE queries at render time. Expected < 2s page loads.
- **Incremental refresh:** MERGE uses watermark — scans only new rows since last refresh. Full backfill only on first run (30 days).
- **LATERAL FLATTEN:** Extracts per-model credits at ETL time, not at query time. Model breakdown pie chart is a simple GROUP BY on summary table.
- **Cohort resolution in ETL:** User → cohort mapping resolved during refresh task via GRANTS_TO_USERS join. Dashboard queries just filter on COHORT_ROLE column.

### Latency Considerations
- ACCOUNT_USAGE views have up to 60-minute latency for Cortex Code usage data
- Pre-aggregated tables refresh every 30 minutes → effective worst-case: ~90 min lag
- Intelligence engine uses 14-day hourly trends to predict, not real-time data
- Credit request feasibility analysis is based on best-available data + predictions
- This is explicitly called out in the UI ("Data refreshes every 30 minutes")

### Security
- All identifiers validated with `REGEXP_LIKE('^[A-Za-z0-9_$]+$')` inside SPs
- Database role whitelist in grant/revoke SP (only CORTEX_USER and CORTEX_ANALYST_USER)
- App role cannot ALTER USER/ACCOUNT — only CALL SPs
- SQL literals escaped with `replace("'", "''")`
- Admin page access gated by `CURRENT_AVAILABLE_ROLES()` check against config.yaml whitelist
- No sensitive data in cache keys

### Optimization Opportunities (Future)
- Add clustering key on `CC_USAGE_DAILY_SUMMARY (USAGE_DATE)` if table grows large
- Add stream + task pattern instead of watermark-based MERGE for lower latency
- Consider materialized view for top-users aggregation if query patterns stabilize

---

## 9. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| ACCOUNT_USAGE latency | Medium | Pre-aggregation + trend prediction + documented limitation |
| Wrong rebalance prediction | Medium | 20% buffer + 50% max cap + midnight reset |
| SP owner role is powerful | Low | One-time setup, never assumed by humans, audited |
| Rolling 24hr window ≠ calendar day | Low | Prediction math uses rolling windows |
| Role membership drift | Low | "Sync New Members" button + optional scheduled sync |
| Large user base (5,000+) | Low | Cohort batching, progress bars, incremental processing |

# CoCo Control Hub — Project Context (v3.1)

## What This Is
A **Streamlit-in-Snowflake (SiS)** admin dashboard for governing Snowflake Cortex Code usage
across an enterprise. Gives admins visibility into who uses Cortex Code, what they're asking,
how much it costs, whether usage is compliant with responsible AI policies, and how LLMs perform.

## Key Files
| File | Purpose |
|---|---|
| `streamlit_app.py` | Entry point, sidebar nav, page dispatch, global CSS |
| `config.py` | All constants, security helpers, admin role check, page lists |
| `config.yaml` | Deployment DB/schema + admin role whitelist |
| `utils.py` | Snowflake data access layer — cached reads, SP calls, session helpers |
| `intelligence.py` | EWMA trend prediction for credit rebalancing |
| `audit.py` | `log_activity()` → CC_AUDIT_LOG |
| `sp_definitions.py` | DDL generators for all Python SPs (Phase A bulk SPs + Phase C analytics SPs) |
| `prerequisites.sql` | DDL, owner-rights SPs, tasks, alerts, RBAC setup |
| `pages/` | 18 page modules (see below) |

## Pages (18 total)
| Page | Group | Who |
|---|---|---|
| `home.py` | — | All users |
| `setup.py` | Admin | Admin |
| `settings.py` | Admin | Admin |
| `audit_logs.py` | Admin | Admin |
| `access_management.py` | Access & Limits | Admin |
| `credit_config.py` | Access & Limits | Admin |
| `model_access.py` | Access & Limits | Admin |
| `credit_requests.py` | Access & Limits | All users |
| `usage_trends.py` | Usage & Cost | Admin |
| `budget_forecast.py` | Usage & Cost | Admin |
| `cost_attribution.py` | Usage & Cost | Admin |
| `observability.py` | Observability | Admin |
| `user_intelligence.py` | Observability | Admin |
| `prompt_analysis.py` | Responsible AI | Admin |
| `policy_rules.py` | Responsible AI | Admin |
| `alerts.py` | Responsible AI | Admin |
| `model_intelligence.py` | Intelligence | Admin |
| `user_quotas.py` | Access & Limits | Admin (Preview) |

## Snowflake Objects
**Tables:** CC_CREDIT_CONFIG, CC_AUDIT_LOG, CC_USAGE_DAILY_SUMMARY, CC_USAGE_HOURLY_SUMMARY,
CC_CREDIT_REQUESTS, CC_APP_CONFIG, CC_MODEL_CONFIG, CC_MODEL_ROLE_MAPPING, CC_USER_COHORT_RESOLVED,
CC_COHORT_LEADS, CC_POLICY_RULES, CC_PROMPT_EVENTS, CC_PROMPT_VIOLATIONS, CC_PROMPT_ANALYSIS_DAILY,
CC_ALERT_CONFIG, CC_ALERT_HISTORY, CC_RESPONSE_QUALITY, CC_AI_BUDGETS, CC_AI_BUDGET_USAGE,
CC_NATIVE_QUOTAS

**Phase A SPs (owner-rights):** SP_CC_SET_ACCOUNT_CREDIT_LIMIT, SP_CC_SET_USER_CREDIT_LIMIT,
SP_CC_UNSET_USER_CREDIT_LIMIT, SP_CC_GRANT_CORTEX_ACCESS, SP_CC_REVOKE_CORTEX_ACCESS,
SP_CC_REBALANCE_CREDITS, SP_CC_BULK_GRANT_ACCESS, SP_CC_BULK_SET_COHORT_LIMITS,
SP_CC_COMPUTE_REBALANCE, SP_CC_REFRESH_USAGE_SUMMARIES, SP_CC_DAILY_RESET_LIMITS,
SP_CC_RESOLVE_USER_COHORTS, SP_CC_ENFORCE_MODEL_ACCESS

**Phase C SPs (analytics, owner-rights):** SP_CC_CLASSIFY_PROMPTS, SP_CC_CHECK_ALERTS,
SP_CC_EVALUATE_RESPONSES, SP_CC_REFRESH_BUDGET_USAGE, SP_CC_MANAGE_QUOTA

**Tasks:** CC_REFRESH_USAGE_SUMMARIES (30 min), CC_DAILY_RESET_LIMITS (midnight UTC),
CC_CLASSIFY_PROMPTS_TASK (2am UTC), CC_ALERT_CHECK (1hr), CC_REALTIME_VIOLATION_ALERT (1hr)

**Roles:** CC_SP_OWNER_ROLE, CC_APP_ROLE, CC_ADMIN_ROLE, CC_USER_ROLE

## Security Model
- Owner-rights SPs: app role can CALL but never ALTER USER directly
- Admin pages gated by `user_is_admin()` check against `config.yaml admin.roles`
- All SQL identifiers validated with `sanitize_identifier()` / `sql_identifier()`
- Prompts written via `session.write_pandas()` — never appear in QUERY_HISTORY

## Data Sources
- `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` — raw Cortex Code spans (nightly via SP)
- `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_*_USAGE_HISTORY` — billing (30min via task)
- Pre-aggregated into CC_USAGE_DAILY_SUMMARY / CC_USAGE_HOURLY_SUMMARY

## Key Architecture Decisions
- All dashboard queries hit pre-aggregated tables — never ACCOUNT_USAGE at render time
- `SESSION_ID` in CC_PROMPT_EVENTS = real terminal session ID from `CodingAgentRun.session_id`
  (falls back to trace_id for non-interactive requests)
- Cost Attribution per-request joins billing on `Agent` span `request_id` (not Step-0)
- Native per-user quotas use `SNOWFLAKE.CORE.QUOTA` objects (Preview feature)

## Deployment
Update `snowflake.yml` (database/schema/warehouse) and `config.yaml` (admin roles),
then run `snow streamlit deploy --replace`. Use Setup page for all object creation.
See DEPLOYMENT_GUIDE.md for full instructions.

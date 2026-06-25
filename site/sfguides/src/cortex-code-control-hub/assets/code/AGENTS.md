# Cortex Code Credit Manager

## Project Context
This is a Streamlit-in-Snowflake (SiS) app for enterprise Cortex Code credit governance.
It manages daily credit limits for Cortex Code CLI and Snowsight via owner-rights stored procedures.

## Key Files
- `streamlit_app.py` — Entry point, sidebar navigation, page dispatch
- `config.py` — All constants, security helpers, admin role whitelist
- `config.yaml` — Deployment-specific DB/schema and admin roles
- `utils.py` — Snowflake data access layer (cached reads from pre-aggregated tables)
- `intelligence.py` — EWMA trend prediction for credit rebalancing
- `audit.py` — Audit logging to CC_AUDIT_LOG
- `prerequisites.sql` — DDL, owner-rights SPs, scheduled tasks, RBAC setup
- `pages/` — 7 page modules (home, access_management, credit_config, usage_trends, credit_requests, settings, audit_logs)

## Snowflake Objects
- **Tables:** CC_CREDIT_CONFIG, CC_AUDIT_LOG, CC_USAGE_DAILY_SUMMARY, CC_USAGE_HOURLY_SUMMARY, CC_CREDIT_REQUESTS, CC_APP_CONFIG
- **SPs (EXECUTE AS OWNER):** SP_CC_SET_ACCOUNT_CREDIT_LIMIT, SP_CC_SET_USER_CREDIT_LIMIT, SP_CC_UNSET_USER_CREDIT_LIMIT, SP_CC_GRANT_CORTEX_ACCESS, SP_CC_REVOKE_CORTEX_ACCESS, SP_CC_REBALANCE_CREDITS, SP_CC_REFRESH_USAGE_SUMMARIES, SP_CC_DAILY_RESET_LIMITS
- **Tasks:** CC_REFRESH_USAGE_SUMMARIES (30 min), CC_DAILY_RESET_LIMITS (midnight UTC)
- **Roles:** CC_SP_OWNER_ROLE, CC_APP_ROLE, CC_ADMIN_ROLE, CC_USER_ROLE

## Security Model
- Owner-rights SPs: app role can CALL but never ALTER USER directly
- Admin pages gated by CURRENT_AVAILABLE_ROLES() check against config.yaml whitelist
- All SQL identifiers validated with regex inside SPs

## Data Sources
- SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
- SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
- Pre-aggregated into CC_USAGE_DAILY_SUMMARY and CC_USAGE_HOURLY_SUMMARY

## Conventions
- Same patterns as AI Monitoring Dashboard (CSS, Altair charts, date presets, pre-aggregation)
- Same patterns as MDI DQ app (admin role gating, audit table, two-phase confirm)
- Same patterns as Domain Admin Utility (config.py/config.yaml, sanitize_identifier, SP FQN)

## Deployment
Run `prerequisites.sql` as ACCOUNTADMIN first, then deploy via `snow streamlit deploy`.
See DEPLOYMENT_GUIDE.md for full instructions.

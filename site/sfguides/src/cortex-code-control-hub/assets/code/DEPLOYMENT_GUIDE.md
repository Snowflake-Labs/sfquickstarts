# Deployment Guide — CoCo Control Hub

## Prerequisites

- **ACCOUNTADMIN** — for the one-time Account Prerequisites, and to own the app while running Setup Phases A and C (on install and on every upgrade)
- A warehouse (XSMALL is sufficient for the app and its tasks)
- A database and schema for the app (set in `config.yaml` and `snowflake.yml`)
- **Snowflake CLI** (`snow`) — required for `snow streamlit deploy`. See [Installing Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation). Alternatively upload the files in Snowsight.
- **Cortex Code CLI** _(optional)_ — only for the AI-assisted deploy in `GETTING_STARTED.md`

---

## Step 1: Configure the Deployment Target

Edit `config.yaml`:

```yaml
deployment:
  database: YOUR_DB
  schema: YOUR_SCHEMA

admin:
  roles:
    - ACCOUNTADMIN
    - YOUR_CUSTOM_ADMIN_ROLE  # optional — roles that see the admin pages
```

Edit `snowflake.yml` and replace the `MY_DATABASE`, `MY_SCHEMA` and `MY_WAREHOUSE` placeholders. Keep the `artifacts` list as shipped — every listed file must be deployed (including `prerequisites.sql`, `pages/user_quotas.py` and `.streamlit/config.toml`).

---

## Step 2: Deploy the Streamlit App

```bash
snow streamlit deploy --connection YOUR_CONNECTION
```

**Snowsight alternative:** create a Streamlit app, set `streamlit_app.py` as the main file, and upload every file listed under `artifacts` in `snowflake.yml`, keeping the `pages/` and `.streamlit/` folders.

---

## Step 3: Make Sure ACCOUNTADMIN Owns the App

Setup runs as the app's **owner**. The credit-limit stored procedures only work when ACCOUNTADMIN owns them (Snowflake only lets an owner's-rights procedure set `CORTEX_CODE_*_DAILY_EST_CREDIT_LIMIT_PER_USER` when ACCOUNTADMIN owns it), so ACCOUNTADMIN must own the app while you run Phases A and C.

```sql
SHOW STREAMLITS IN SCHEMA YOUR_DB.YOUR_SCHEMA;   -- check the "owner" column
GRANT OWNERSHIP ON STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER
  TO ROLE ACCOUNTADMIN COPY CURRENT GRANTS;
```

---

## Step 4: Account Prerequisites (once, as ACCOUNTADMIN)

Open the app → **Setup → Account Prerequisites** and run the 7 SQL blocks in a Snowsight worksheet as ACCOUNTADMIN. They include:

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';   -- or region groups, e.g. 'AWS_US'
GRANT APPLICATION ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_SP_OWNER_ROLE;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CC_SP_OWNER_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CC_USER_ROLE;   -- or CORTEX_AGENT_USER
```

Run Phase A first if the `CC_*` roles do not exist yet — Phase A creates them.

---

## Step 5: Run Setup Phases A–E

In **Setup**:

| Phase | What it does |
|---|---|
| **A** | Runs `prerequisites.sql` (roles, tables, tasks, alerts, stream, email integration, core SPs), then creates the bulk, rebalance, model-access and Phase C SPs and grants USAGE on every app SP to `CC_APP_ROLE` and `CC_SP_OWNER_ROLE`. Idempotent. |
| **B** | Seeds default settings |
| **C** | Recreates the SPs defined in `sp_definitions.py` and re-applies USAGE grants |
| **D** | Initial data load (D1 usage summaries, D2 prompt events, D3 model config) |
| **E** | Verifies every object, the ownership of the credit-limit SPs, and the temporary-limit columns |

Phases A and C must run with the app owned by ACCOUNTADMIN (Step 3). The Setup page shows a red warning if it is not.

> **Running `prerequisites.sql` outside the app** (after substituting the `__DB__`, `__SCHEMA__`, `__WH__` and `__*_ROLE__` placeholders) creates only the objects in that file. You still need Setup Phases A and C for the SPs in `sp_definitions.py` and the USAGE grants.

### Objects and owners

| Object | Owner |
|---|---|
| Roles `CC_SP_OWNER_ROLE`, `CC_APP_ROLE`, `CC_ADMIN_ROLE`, `CC_USER_ROLE` | ACCOUNTADMIN |
| `CC_*` tables | `CC_SP_OWNER_ROLE` |
| Credit-limit SPs: `SP_CC_SET_ACCOUNT_CREDIT_LIMIT`, `SP_CC_SET_USER_CREDIT_LIMIT`, `SP_CC_UNSET_USER_CREDIT_LIMIT`, `SP_CC_REBALANCE_CREDITS`, `SP_CC_DAILY_RESET_LIMITS`, `SP_CC_EXPIRE_TEMPORARY_CREDITS`, `SP_CC_BULK_SET_COHORT_LIMITS`, `SP_CC_COMPUTE_REBALANCE` | **ACCOUNTADMIN — never transfer** |
| All other SPs | ACCOUNTADMIN or `CC_SP_OWNER_ROLE` (depending on which phase last created them — both work) |
| Tasks: `CC_REFRESH_USAGE_SUMMARIES` (every 30 min), `CC_DAILY_RESET_LIMITS` (00:00 UTC), `CC_EXPIRE_TEMPORARY_CREDITS` (hourly), `CC_CLASSIFY_PROMPTS_TASK` (02:00 UTC), `CC_REFRESH_BUDGET_USAGE` (02:00 UTC, starts suspended) | `CC_SP_OWNER_ROLE` |
| Alerts: `CC_ALERT_CHECK`, `CC_REALTIME_VIOLATION_ALERT` (start suspended) | `CC_SP_OWNER_ROLE` |

Tasks and alerts run as `CC_SP_OWNER_ROLE`; Setup grants that role USAGE on the SPs they call.

---

## Step 6: Grant Access to Admins and Users

```sql
GRANT USAGE ON STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER TO ROLE CC_ADMIN_ROLE;
GRANT USAGE ON STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER TO ROLE CC_USER_ROLE;

GRANT ROLE CC_ADMIN_ROLE TO USER your_admin_user;   -- admin pages (or list the role in config.yaml admin.roles)
GRANT ROLE CC_USER_ROLE  TO USER your_end_user;     -- Home + Credit Requests
```

---

## Step 7: Verify

1. **Setup → Phase E** — all checks green
2. `SHOW TASKS LIKE 'CC_%' IN SCHEMA YOUR_DB.YOUR_SCHEMA;` — the tasks you use are `started`
3. **Usage Trends** shows data after the first refresh (up to 30 minutes)
4. **Audit Log** shows the setup entries

---

## Upgrading an Existing Installation

This release adds temporary-limit expiry, new security checks on the privileged stored procedures, and keeps the credit-limit stored procedures owned by ACCOUNTADMIN. **Run Phases A and C after updating.**

1. Get the latest code from `assets/code/` and keep your own values in `config.yaml` and `snowflake.yml` (database, schema, warehouse, admin roles).
2. Redeploy the app: `snow streamlit deploy --replace --connection <your_connection>`
3. Make sure the app is **owned by ACCOUNTADMIN** — Setup runs as the app owner, and the credit-limit SPs only work when ACCOUNTADMIN owns them:
   ```sql
   SHOW STREAMLITS IN SCHEMA <db>.<schema>;   -- check the "owner" column
   GRANT OWNERSHIP ON STREAMLIT <db>.<schema>.CORTEX_CODE_CREDIT_MANAGER TO ROLE ACCOUNTADMIN COPY CURRENT GRANTS;
   ```
4. If not done before, grant AI Observability access (it is an **application** role):
   `GRANT APPLICATION ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_SP_OWNER_ROLE;`
5. Open the app → **Setup** → run **Phase A**. It is idempotent: it adds the temporary-limit columns to `CC_CREDIT_CONFIG`, creates the hourly `CC_EXPIRE_TEMPORARY_CREDITS` task, recreates the SPs, re-applies USAGE grants, and resumes alerts and the budget refresh task if they were running.
6. Run **Phase C**.
7. Run **Phase E**. All checks must be green — including ownership of the credit-limit SPs and the new columns.
8. Confirm the tasks are running: `SHOW TASKS LIKE 'CC_%' IN SCHEMA <db>.<schema>;`

**Behaviour changes in this release**
- Model Access no longer offers an account-wide option (`CORTEX_MODELS_ALLOWLIST` is retired by BCR-2378). Use **Role Directly** or **Role Members** (model RBAC).
- Access grants offer `CORTEX_USER` or `CORTEX_AGENT_USER`; `COPILOT_USER` is transitional (BCR-2445).
- Temporary limits created before this release have no expiry date recorded and will not auto-revert — re-apply them as Temporary if needed.
- If the app was owned by a custom role, transfer it to ACCOUNTADMIN for Phases A and C, then transfer it back.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Credit-limit changes fail with "Insufficient privileges" | Setup ran while the app was owned by another role. Transfer the app to ACCOUNTADMIN, re-run Phases A and C, and check Phase E. |
| A task or alert fails with "Unknown user-defined function" | USAGE grants were lost after the SPs were recreated. Re-run Phase A (or C) — both re-apply the grants. |
| "Access denied" on admin pages | Add your role to `config.yaml → admin.roles`, or grant `CC_ADMIN_ROLE`. |
| No usage data | Wait for the first 30-minute refresh, or `CALL YOUR_DB.YOUR_SCHEMA.SP_CC_REFRESH_USAGE_SUMMARIES();`. Check `SELECT COUNT(*) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY;`. |
| A task is suspended | `ALTER TASK YOUR_DB.YOUR_SCHEMA.<task> RESUME;` |
| Credit-request approval fails | The request stays PENDING with the error shown; fix the cause and approve again. |
| Bulk grant rejects a role | Only `SNOWFLAKE.CORTEX_USER`, `CORTEX_AGENT_USER`, `COPILOT_USER` and `CORTEX_ANALYST_USER` can be granted. System roles, `PUBLIC` (for account roles) and the SP owner role cannot be grant targets. |

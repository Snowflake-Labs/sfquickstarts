# Deployment Guide — Cortex Code Credit Manager

## Prerequisites

- ACCOUNTADMIN access (one-time setup only)
- A warehouse (any size, XSMALL sufficient for app + tasks)
- A database and schema for the app tables and SPs
- Cortex Code CLI installed (`curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh`)
- Snowflake CLI installed (`snow` command available)

---

## Step 1: Configure Deployment Target

Edit `config.yaml` with your target database and schema:

```yaml
deployment:
  database: YOUR_DB
  schema: YOUR_SCHEMA

admin:
  roles:
    - ACCOUNTADMIN
    - YOUR_CUSTOM_ADMIN_ROLE  # optional
```

---

## Step 2: Run Prerequisites SQL

This creates roles, tables, stored procedures, and tasks. **Run as ACCOUNTADMIN.**

Open `prerequisites.sql` and update the three variables at the top:

```sql
SET APP_DB     = 'YOUR_DB';
SET APP_SCHEMA = 'YOUR_SCHEMA';
SET APP_WH     = 'YOUR_WAREHOUSE';
```

Then execute the entire file:

```bash
# Option A: Via Cortex Code CLI
cortex
> Run the prerequisites.sql file against my Snowflake account

# Option B: Via Snowflake CLI
snow sql -f prerequisites.sql --connection YOUR_CONNECTION

# Option C: Via Snowsight
# Copy-paste and run in a worksheet
```

### What This Creates

| Object Type | Names | Owner |
|---|---|---|
| Roles | CC_SP_OWNER_ROLE, CC_APP_ROLE, CC_ADMIN_ROLE, CC_USER_ROLE | ACCOUNTADMIN |
| Tables (6) | CC_CREDIT_CONFIG, CC_AUDIT_LOG, CC_USAGE_DAILY_SUMMARY, CC_USAGE_HOURLY_SUMMARY, CC_CREDIT_REQUESTS, CC_APP_CONFIG | CC_SP_OWNER_ROLE |
| SPs (8) | SP_CC_SET_ACCOUNT_CREDIT_LIMIT, SP_CC_SET_USER_CREDIT_LIMIT, SP_CC_UNSET_USER_CREDIT_LIMIT, SP_CC_GRANT_CORTEX_ACCESS, SP_CC_REVOKE_CORTEX_ACCESS, SP_CC_REBALANCE_CREDITS, SP_CC_REFRESH_USAGE_SUMMARIES, SP_CC_DAILY_RESET_LIMITS | CC_SP_OWNER_ROLE |
| Tasks (2) | CC_REFRESH_USAGE_SUMMARIES (every 30 min), CC_DAILY_RESET_LIMITS (midnight UTC) | CC_SP_OWNER_ROLE |

---

## Step 3: Verify Prerequisites

```sql
USE ROLE ACCOUNTADMIN;
SHOW TABLES LIKE 'CC_%' IN SCHEMA YOUR_DB.YOUR_SCHEMA;
SHOW PROCEDURES LIKE 'SP_CC_%' IN SCHEMA YOUR_DB.YOUR_SCHEMA;
SHOW TASKS LIKE 'CC_%' IN SCHEMA YOUR_DB.YOUR_SCHEMA;
```

Optionally seed initial data:

```sql
-- Run the refresh SP manually for first-time backfill (30 days)
CALL YOUR_DB.YOUR_SCHEMA.SP_CC_REFRESH_USAGE_SUMMARIES();
```

---

## Step 4: Grant Access to Admins and Users

```sql
-- Grant admin access (can see all pages)
GRANT ROLE CC_ADMIN_ROLE TO USER your_admin_user;

-- Grant user access (Home + Credit Requests only)
GRANT ROLE CC_USER_ROLE TO USER your_end_user;
```

---

## Step 5: Deploy the Streamlit App

### Option A: Via Snowflake CLI (Recommended)

Update `snowflake.yml` with your target:

```yaml
definition_version: 2
entities:
  cortex_code_credit_manager:
    type: streamlit
    identifier:
      name: CORTEX_CODE_CREDIT_MANAGER
    title: "Cortex Code Credit Manager"
    query_warehouse: YOUR_WAREHOUSE
    main_file: streamlit_app.py
    pages_dir: pages/
    additional_source_files:
      - config.py
      - config.yaml
      - audit.py
      - utils.py
      - intelligence.py
    stage: CORTEX_CODE_CREDIT_MANAGER_STAGE
```

Then deploy:

```bash
cd streamlit-apps/cortex-code-credit-manager
snow streamlit deploy --connection YOUR_CONNECTION --database YOUR_DB --schema YOUR_SCHEMA
```

### Option B: Via Cortex Code CLI

```bash
cd streamlit-apps/cortex-code-credit-manager
cortex
> Deploy this Streamlit app to Snowflake using database YOUR_DB and schema YOUR_SCHEMA
```

### Option C: Via Snowsight UI

1. Go to Snowsight → Projects → Streamlit
2. Create new app
3. Upload all `.py` files, `config.yaml`, and `environment.yml`
4. Set main file to `streamlit_app.py`

---

## Step 6: Set the App to Run as CC_APP_ROLE

After deployment, ensure the Streamlit app's execution role is `CC_APP_ROLE`:

```sql
ALTER STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER
    SET QUERY_WAREHOUSE = 'YOUR_WAREHOUSE';

-- Grant CC_APP_ROLE access to the Streamlit app
GRANT USAGE ON STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER TO ROLE CC_ADMIN_ROLE;
GRANT USAGE ON STREAMLIT YOUR_DB.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER TO ROLE CC_USER_ROLE;
```

---

## Step 7: Verify Deployment

1. Open the app in Snowsight
2. Check sidebar shows admin pages (if logged in as admin role)
3. Navigate to **Settings** → verify default values loaded
4. Navigate to **Usage Trends** → confirm data appears (may take 30 min after first refresh)
5. Navigate to **Audit Log** → confirm entries from prerequisites run

---

## Troubleshooting

### "Access denied" on admin pages
- Verify your role is in `config.yaml → admin.roles`
- Or verify you have `CC_ADMIN_ROLE` granted

### No usage data in dashboards
- Wait 30 minutes for the first task run
- Or manually call: `CALL YOUR_DB.YOUR_SCHEMA.SP_CC_REFRESH_USAGE_SUMMARIES();`
- Verify ACCOUNT_USAGE access: `SELECT COUNT(*) FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY;`

### SP calls fail with "insufficient privileges"
- Verify CC_SP_OWNER_ROLE has `MANAGE GRANTS ON ACCOUNT`
- Verify CC_APP_ROLE has `USAGE ON PROCEDURE` for all SPs

### Task not running
- `SHOW TASKS LIKE 'CC_%';` — check STATE is 'started'
- `ALTER TASK CC_REFRESH_USAGE_SUMMARIES RESUME;` if suspended

---

## Updating the App

After code changes, redeploy:

```bash
snow streamlit deploy --connection YOUR_CONNECTION --replace
```

Or via Cortex Code CLI:

```bash
cortex
> Redeploy the Cortex Code Credit Manager Streamlit app
```

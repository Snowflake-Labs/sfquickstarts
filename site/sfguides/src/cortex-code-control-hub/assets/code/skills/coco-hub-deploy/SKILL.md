---
name: coco-hub-deploy
description: >
  Interactive deployment guide for CoCo Control Hub (Cortex Code Credit Manager).
  Invoke when someone wants to deploy, install, or set up CoCo Control Hub in
  their Snowflake account. Asks targeted questions about their deployment target
  (SPCS container vs warehouse Streamlit), database/schema, compute preferences,
  existing admin roles, and account prerequisites. Guides them step-by-step
  through the complete installation including Account Prerequisites (7 steps),
  Phases A–E, post-install tasks, and common upgrade scenarios.
  CRITICAL RULE: The app code must be deployed exactly as-is. No modifications
  to any source files are permitted during deployment.
triggers:
  - deploy CoCo Control Hub
  - install CoCo
  - set up Cortex Code Credit Manager
  - deploy the app
  - how do I install
  - deploy in my Snowflake account
  - set up the credit manager
  - redeploy
  - upgrade CoCo
---

# CoCo Control Hub — Deployment Guide

## CRITICAL RULE — Read First

**The code must be deployed exactly as-is. Do NOT modify any source files.**

- Do NOT edit `sp_definitions.py`, `config.py`, `prerequisites.sql`, `pages/*.py`, or `streamlit_app.py`
- The ONLY files you may modify are `snowflake.yml` (deployment target) and `config.yaml` (admin roles + deployment database/schema)
- All customisation happens through the app's Setup page AFTER deployment, never before

---

## Phase 0 — Gather Requirements

Ask the user ALL of these questions before doing anything. Do not proceed until all are answered.

### Question Set A — Deployment Type

```
1. How will you deploy the Streamlit app?
   a) Streamlit on Warehouse (standard — no special compute needed)
   b) Streamlit on Container (SPCS — requires compute pool, higher performance)
```

**If SPCS (b):** Also ask:
- What is the name of your compute pool? (e.g. `COCO_HUB_POOL`)
- Runtime: `SYSTEM_STREAMLIT_CONTAINER` (standard)

### Question Set B — Snowflake Target

```
2. Where should the app be deployed?
   - Database name (e.g. MY_DB)
   - Schema name (e.g. APPS)
   - Warehouse name (e.g. COMPUTE_WH, COCO_HUB_WH)
```

### Question Set C — Data Schema

```
3. Where should the app's data tables (CC_PROMPT_EVENTS, CC_USAGE_DAILY_SUMMARY, etc.) be stored?
   a) Same database/schema as the app (most common — simpler)
   b) Separate database/schema (for separation of concerns)
```

### Question Set D — Deployment Role

```
4. Which Snowflake role will you use to deploy the app and run Setup?
   a) ACCOUNTADMIN (simplest — has all required privileges)
   b) Custom role (e.g. PLATFORM_ADMIN, DBA_ROLE)
      → If custom role: what is the role name?
```

### Question Set E — App Admin Roles

```
5. Which roles should see ALL admin pages in the app?
   (These go in config.yaml → admin.roles)

   a) Just ACCOUNTADMIN (default — safe starting point)
   b) ACCOUNTADMIN + an existing org role (e.g. PLATFORM_ADMIN)
      → What is the existing role name?
   c) A completely custom new role you want to create specifically for CoCo

   Note: End users (non-admins) only see Home and Credit Requests.
   Admins see all 16 pages. You can add multiple roles.
```

### Question Set F — Existing Infrastructure

```
6. Do you already have:
   [ ] A database and schema created (or will the deploy role create them?)
   [ ] Cross-region inference enabled? (ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY')
   [ ] AI Observability reader granted? (for prompt/token data)
   [ ] ACCOUNT_USAGE access for the SP owner role? (for credit data)

   Don't worry if not — the Setup page will guide you through all of these.
```

### Question Set G — Prerequisites Check

```
7. Confirm you have:
   [ ] App code folder (git clone or zip)
   [ ] Snowflake CLI installed: snow --version
   [ ] Python 3.9+
   [ ] Access to required Snowflake role (ACCOUNTADMIN or custom from Question D)
```

---

## Phase 0b — Custom Role Privilege Setup

**Only needed if Question D answer is (b) — custom role.**
**Skip entirely if using ACCOUNTADMIN.**

Run as ACCOUNTADMIN to grant the deploying role all needed privileges:

```sql
-- Replace MY_DEPLOY_ROLE, MY_DB, MY_SCHEMA, MY_WH with actual values
USE ROLE ACCOUNTADMIN;

-- 1. Database and schema access
GRANT CREATE DATABASE ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;       -- if DB doesn't exist yet
GRANT USAGE ON DATABASE MY_DB TO ROLE MY_DEPLOY_ROLE;
GRANT USAGE, CREATE SCHEMA ON DATABASE MY_DB TO ROLE MY_DEPLOY_ROLE;
GRANT ALL ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT USAGE ON WAREHOUSE MY_WH TO ROLE MY_DEPLOY_ROLE;

-- 2. Streamlit deployment
GRANT CREATE STREAMLIT ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE STAGE ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;

-- 3. Object creation for Setup Phase A
GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE TASK ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;
GRANT EXECUTE ALERT ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE STREAM ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE ALERT ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE PROCEDURE ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE TABLE ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE VIEW ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_DEPLOY_ROLE;
GRANT CREATE ROLE ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;

-- 4. Data access (for SP_CC_REFRESH_USAGE_SUMMARIES and SP_CC_CLASSIFY_PROMPTS)
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE MY_DEPLOY_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE MY_DEPLOY_ROLE;

-- 5. SPCS only (skip if Streamlit on Warehouse)
GRANT USAGE ON COMPUTE POOL MY_COMPUTE_POOL TO ROLE MY_DEPLOY_ROLE;
-- Or to create a new pool:
-- GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE MY_DEPLOY_ROLE;

-- 6. Grant the deploy role to your user
GRANT ROLE MY_DEPLOY_ROLE TO USER MY_USERNAME;
```

**If your security team won't grant MANAGE GRANTS:**
Have a DBA run Setup Phase A under ACCOUNTADMIN, then use the custom role for all subsequent operations.

---

## Phase 1 — Configure the Two Files

After gathering answers, update **only** these two files.

### 1a. Update `snowflake.yml`

**Streamlit on Warehouse:**
```yaml
definition_version: 2
entities:
  cortex_code_credit_manager:
    type: streamlit
    identifier:
      name: CORTEX_CODE_CREDIT_MANAGER
      database: <DATABASE>
      schema: <SCHEMA>
    title: "CoCo Control Hub"
    query_warehouse: <WAREHOUSE>
    main_file: streamlit_app.py
    artifacts:
      - config.py
      - config.yaml
      - .streamlit/config.toml
      - audit.py
      - utils.py
      - intelligence.py
      - sp_definitions.py
      - prerequisites.sql
      - environment.yml
      - pages/__init__.py
      - pages/home.py
      - pages/access_management.py
      - pages/credit_config.py
      - pages/usage_trends.py
      - pages/model_access.py
      - pages/credit_requests.py
      - pages/settings.py
      - pages/audit_logs.py
      - pages/setup.py
      - pages/observability.py
      - pages/cost_attribution.py
      - pages/prompt_analysis.py
      - pages/policy_rules.py
      - pages/alerts.py
      - pages/model_intelligence.py
      - pages/user_intelligence.py
    stage: CORTEX_CODE_CREDIT_MANAGER_STAGE
```

**Add these 2 lines for SPCS:**
```yaml
    runtime_name: SYSTEM_STREAMLIT_CONTAINER
    compute_pool: <COMPUTE_POOL_NAME>
```

### 1b. Update `config.yaml`

```yaml
deployment:
  database: ""    # Leave blank → uses CURRENT_DATABASE(). Or set: MY_DB
  schema: ""      # Leave blank → uses CURRENT_SCHEMA(). Or set: APPS

admin:
  roles:
    - ACCOUNTADMIN
    # Add your existing org admin role here if applicable (from Question E):
    # - PLATFORM_ADMIN
    # - DBA_ROLE
```

**Important:** Do NOT put your personal dev account name (e.g. YOUR_DB, YOUR_SCHEMA). Leave blank if unsure — the sidebar Deployment Target picker overrides this at runtime.

---

## Phase 2 — Deploy the App

```bash
cd /path/to/cortex-code-credit-manager

# Add connection if not set up
snow connection add

# Deploy
snow streamlit deploy --replace --connection <connection_name>
```

Success: `Streamlit successfully deployed and available under https://app.snowflake.com/...`

---

## Phase 3 — Account Prerequisites (BEFORE Phase A)

Open the app → **Setup** → expand **"⚡ Account Prerequisites"**. Run each SQL block in Snowsight as ACCOUNTADMIN. These are one-time account-level grants.

| Step | SQL | Required? |
|---|---|---|
| 1 | `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY'` | ✅ Needed for most models |
| 2 | `GRANT DATABASE ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_SP_OWNER_ROLE` | ✅ For prompt/token data |
| 3 | `GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CC_SP_OWNER_ROLE` | ✅ For credit/usage data |
| 4 | `GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CC_USER_ROLE` + `GRANT USE AI FUNCTIONS ON ACCOUNT TO ROLE CC_USER_ROLE` | ✅ For users to call AI functions |
| 5 | `ALTER ACCOUNT SET CORTEX_CODE_CREDIT_LIMIT = N` | Optional |
| 6 | AI Guardrails (Enterprise only) | Optional |
| 7 | Native AI Budgets (Preview) | Optional |

Status chips on the page show ✓ green (done) / ⚠ amber (not yet configured).

---

## Phase 4 — Run Setup Phases in the App

Open the app → **Setup** sidebar. Run in order:

| Phase | Button | What it does |
|---|---|---|
| **A** | Run Phase A — Create Objects | Creates all tables, roles, tasks, alerts, stream, email integration, seeds 8 policy rules |
| A | Grant App Roles to Me | Grants CC_ADMIN_ROLE + CC_USER_ROLE to current user |
| **B** | Run Phase B — Seed Defaults | Populates CC_APP_CONFIG with default settings |
| **C** | Run Phase C — Create SPs | Creates SP_CC_CLASSIFY_PROMPTS, SP_CC_CHECK_ALERTS, SP_CC_EVALUATE_RESPONSES |
| D1 | Run D1 — Backfill Usage | Backfill credit/usage history (pick 90 days) |
| D2 | Run D2 — Backfill Prompts | Backfill prompt events, insights, surface detection (pick 90 days, 10–30 min) |
| D3 | Run D3 — Model Config | Seed model tier config (one-time) |
| D4 | Run D4 — Quality Eval | Custom Quality (Experimental) — optional, costs credits |
| **E** | Run Phase E — Verify | Confirm all 70+ objects exist (green chips) |

---

## Phase 5 — Post-Install

### Resume nightly tasks
```sql
ALTER TASK CC_CLASSIFY_PROMPTS_TASK RESUME;
ALTER TASK CC_REFRESH_USAGE_SUMMARIES RESUME;
-- Only if enforcing credit limits:
-- ALTER TASK CC_DAILY_RESET_LIMITS RESUME;
```

### Enable email alerts
Go to **Alerts → Notification Config** → enter recipient email → Save → Send Test Email

### Grant app access to end users
```sql
GRANT ROLE CC_USER_ROLE TO USER <end_user>;
-- Or to a department role:
GRANT ROLE CC_USER_ROLE TO ROLE <department_role>;

-- App visibility
GRANT USAGE ON DATABASE <db> TO ROLE CC_USER_ROLE;
GRANT USAGE ON SCHEMA <db>.<schema> TO ROLE CC_USER_ROLE;
GRANT USAGE ON STREAMLIT <db>.<schema>.CORTEX_CODE_CREDIT_MANAGER TO ROLE CC_USER_ROLE;
```

### Add a custom admin role AFTER deploy
If you want to add an existing org role (e.g. PLATFORM_ADMIN) as an app admin later:
1. Edit `config.yaml` → add role to `admin.roles`
2. Redeploy: `snow streamlit deploy --replace`
3. No SP re-run needed — config.yaml is read at runtime

---

## Upgrade Path (code update on existing install)

After pulling latest code and running `snow streamlit deploy --replace`:

| What changed | Action needed |
|---|---|
| `pages/*.py` only | None — takes effect on reload |
| `sp_definitions.py` | **Phase C** (recreate SPs) |
| `sp_definitions.py` + new data needed | **Phase C** then **Phase D2** (re-backfill) |
| `prerequisites.sql` (new tables) | **Phase A** (idempotent — safe to re-run) |
| `config.yaml` admin roles | None — read at runtime |

### New column migration (existing install)
If upgrading from an older version that's missing columns:

```sql
USE DATABASE <db>;
USE SCHEMA <schema>;

ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS INPUT_TOKENS NUMBER;
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS OUTPUT_TOKENS NUMBER;
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS CACHE_READ_TOKENS NUMBER;
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS CACHE_WRITE_TOKENS NUMBER;
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS STEP_NUMBER NUMBER;
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS ENTRYPOINT VARCHAR(50);
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS PROMPT_CATEGORY VARCHAR(100);
ALTER TABLE IF EXISTS CC_PROMPT_EVENTS ADD COLUMN IF NOT EXISTS PROMPT_COST_CREDITS FLOAT;
```

Then redeploy + Phase C + Phase D2.

---

## Common Issues

| Error / Observation | Cause | Fix |
|---|---|---|
| `Database 'X' does not exist` | Wrong connection or snowflake.yml | Check connection and database |
| `Insufficient privileges to MANAGE GRANTS` | Custom role missing MANAGE GRANTS | Grant it or run Phase A as ACCOUNTADMIN |
| `AI_OBSERVABILITY_EVENTS not found` | Missing AI Observability reader | Grant `SNOWFLAKE.AI_OBSERVABILITY_READER` to CC_SP_OWNER_ROLE (Account Prerequisites Step 2) |
| Phase E SHOW TASKS/ALERTS slow | Still running IN ACCOUNT | Ensure latest code deployed — now scoped to IN SCHEMA |
| Snowsight sessions show as "Surface Unknown" | Snowflake doesn't populate `entrypoint` for Snowsight | Run Phase C (recreates SP with client_type fallback) + Phase D2 (re-backfill) |
| Sessions show SDK-TYPESCRIPT | VS Code / TypeScript client surface | Expected — shown in "SDK / Extensions" bucket. Normal behaviour. |
| `ALLOWED_RECIPIENTS` error on test email | Integration not configured | Save email in Alerts page first — auto-runs ALTER INTEGRATION |
| `invalid identifier 'TIER'` in D3 | Old SP code | Redeploy, Phase C, then D3 |
| Phase D2 very slow (20–40 min) | Large account with many spans | Normal — 90 days on 50K users. Reduce backfill window if needed. |
| Prompt Intelligence numbers unchanged when changing period | CC_PROMPT_EVENTS only has data for periods SP was run | Run D2 with larger window to fill gaps |
| GPT models show 100% Cache Hit Rate | OpenAI doesn't report cache_write tokens | Expected — shown as N/A in latest version. Re-deploy to get the fix. |
| Custom Quality (Experimental) scores very low (0.2–0.3) | Evaluating planning steps not final responses | Run Phase C (updated SP), truncate CC_RESPONSE_QUALITY, re-run D4 |
| Alert health shows STARTED but no alerts fire | All rules disabled in Alert Rules tab | Expected — scheduler runs but nothing triggers. Shows info message in latest version. |
| "Pii Risk" showing in category chart | Old deploy with .str.title() bug | Redeploy — now shows "PII Risk" correctly |
| Config.yaml has YOUR_DB/YOUR_SCHEMA | Developer's personal values were left in | Set database/schema to empty string — uses CURRENT_DATABASE/SCHEMA |
| COCO_HUB_ADMIN role not found | Hardcoded in old config.yaml | Comment it out — config.yaml admin.roles should only have roles that exist in the account |

---

## Post-Deploy Data Correction SQLs

### Fix system-injected prompts misclassified as documentation
```sql
UPDATE <db>.<schema>.CC_PROMPT_EVENTS
SET PROMPT_CATEGORY = 'system_internal'
WHERE PROMPT_CATEGORY IS NOT NULL
  AND PROMPT_CATEGORY != 'system_internal'
  AND (
      LOWER(PROMPT) ILIKE 'cortex ctx task %'
      OR LOWER(PROMPT) ILIKE 'cortex ctx step %'
      OR LOWER(PROMPT) ILIKE 'cortex memory remember%'
  );
```

### Clear low-quality evaluation scores and re-evaluate
```sql
TRUNCATE TABLE <db>.<schema>.CC_RESPONSE_QUALITY;
-- Then run D4 in Setup → Phase D
```

---

## What NOT to Do

- **Do NOT** modify any `.py` files during deployment
- **Do NOT** modify `prerequisites.sql`
- **Do NOT** run `prerequisites.sql` directly — it has `__PLACEHOLDER__` tokens. Use Setup Phase A.
- **Do NOT** enable `CC_DAILY_RESET_LIMITS` task unless you plan to enforce credit limits
- **Do NOT** drop `CC_SP_OWNER_ROLE` — all SPs execute as this role
- **Do NOT** leave `YOUR_DB` or `APPS` in config.yaml — use empty strings or your actual values
- **Do NOT** add a role to config.yaml admin.roles that doesn't exist in the account (causes startup error)

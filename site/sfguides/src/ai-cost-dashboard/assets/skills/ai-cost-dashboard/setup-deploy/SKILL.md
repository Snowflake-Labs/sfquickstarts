---
name: setup-deploy
description: "Deploy AI Cost Dashboard stored procedures and Streamlit app to Snowflake."
parent_skill: ai-cost-dashboard
---

# Setup / Deploy AI Cost Dashboard

## When to Load

From `ai-cost-dashboard` SKILL.md when user selects Setup / Deploy intent.

## Prerequisites

- Snowflake connection is active
- ACCOUNTADMIN role or role with ACCOUNT_USAGE access
- Source files available at `cortex_ai_cost_dashboard/`

## Configurable Parameters

All object names are configurable. The source files use template placeholders (`{{DATABASE}}`, `{{SCHEMA}}`, `{{WAREHOUSE}}`). The deploy process resolves these before execution.

## Workflow

### Step 1: Configure Deployment Parameters

**Goal:** Collect or confirm all deployment targets.

**Actions:**

1. **Ask** user using `ask_user_question` with **all parameters in a single call**:
   - Connection name (text, default: current connection)
   - Database (text, default: "ADMIN_DB")
   - Schema (text, default: "AI_COSTS")
   - Warehouse (text, default: "COMPUTE_WH")
   - Role (text, default: "ACCOUNTADMIN")
   - Credit rate — the customer's current standard $/credit (text, default: "2.88")
   - Historical credit rate — the customer's previous $/credit before current rate (text, default: "3.01")

2. Store as `CONNECTION`, `DATABASE`, `SCHEMA`, `WAREHOUSE`, `ROLE`, `CREDIT_RATE`, `HISTORICAL_CREDIT_RATE`.

**Output:** Confirmed deployment parameters

### Step 2: Resolve Templates and Run Setup SQL

**Goal:** Create database, schema, tables, stored procedures, rate tables, and daily task.

**Actions:**

1. **Read** `cortex_ai_cost_dashboard/setup.sql`
2. **Resolve** the `{{WAREHOUSE}}` placeholder with user's warehouse value
3. **Update** `{{CREDIT_RATE}}` with user's current credit rate and `{{HISTORICAL_CREDIT_RATE}}` with their historical rate
4. **Write** resolved SQL to `/tmp/ai_cost_dashboard_deploy/setup.sql`

5. **Present** deployment plan:
   ```
   Will create in <DATABASE>.<SCHEMA>:
   - 15+ tables (CORTEX_AI_UNIFIED_COSTS, USER_AI_COSTS, + detail tables)
   - 2 stored procedures (REFRESH_CORTEX_AI_COSTS, REFRESH_USER_AI_COSTS)
   - 1 scheduled task (REFRESH_CORTEX_AI_COSTS_DAILY - 6AM UTC daily)
   - Credit rate tables (current: $<CREDIT_RATE>/credit, historical: $<HISTORICAL_CREDIT_RATE>/credit)
   - Initial data load: 365 days
   ```

6. **STOP**: Get user approval before executing.

7. **Execute** via bash:
   ```
   snow sql -f /tmp/ai_cost_dashboard_deploy/setup.sql \
     --connection <CONNECTION> --role <ROLE> \
     --warehouse <WAREHOUSE> --database <DATABASE> --schema <SCHEMA>
   ```

8. **Verify**:
   ```sql
   SELECT TABLE_NAME, ROW_COUNT
   FROM <DATABASE>.INFORMATION_SCHEMA.TABLES
   WHERE TABLE_SCHEMA = '<SCHEMA>'
   ORDER BY TABLE_NAME;
   ```

**If errors occur:**
- ACCOUNT_USAGE access denied -> User needs ACCOUNTADMIN or IMPORTED PRIVILEGES on SNOWFLAKE db
- Table/procedure creation fails -> Check role permissions on target database

**Output:** Created database objects

### Step 3: Deploy Streamlit App

**Goal:** Deploy the Streamlit app to Snowflake.

**Actions:**

1. **Resolve** `cortex_ai_cost_dashboard/snowflake.yml` — replace `{{DATABASE}}` → `<DATABASE>`, `{{SCHEMA}}` → `<SCHEMA>`, `{{WAREHOUSE}}` → `<WAREHOUSE>`. Write back in-place (will restore after deploy).

2. **Create** stage:
   ```sql
   USE SCHEMA <DATABASE>.<SCHEMA>;
   CREATE STAGE IF NOT EXISTS STREAMLIT_STAGE;
   ```

3. **Deploy** via bash from the project directory:
   ```
   snow streamlit deploy --connection <CONNECTION> --replace
   ```

4. **Restore** snowflake.yml to its template version (with `{{}}` placeholders).

5. **Verify**:
   ```sql
   SHOW STREAMLITS LIKE 'CORTEX_AI_COST_DASHBOARD' IN SCHEMA <DATABASE>.<SCHEMA>;
   ```

**Output:** Deployed Streamlit app

### Step 4: Upload Semantic Model

**Goal:** Upload resolved semantic model YAML to stage.

**Actions:**

1. **Resolve** `cortex_ai_cost_dashboard/cortex_ai_costs_model.yaml` — replace `{{DATABASE}}` → `<DATABASE>`, `{{SCHEMA}}` → `<SCHEMA>`. Write to `/tmp/ai_cost_dashboard_deploy/cortex_ai_costs_model.yaml`.

2. **Upload** via bash:
   ```
   snow stage copy /tmp/ai_cost_dashboard_deploy/cortex_ai_costs_model.yaml \
     @<DATABASE>.<SCHEMA>.STREAMLIT_STAGE --connection <CONNECTION> --overwrite
   ```

**Output:** Semantic model on stage

### Step 5: End-to-End Validation

**Goal:** Confirm everything works together.

**Actions:**

1. **Test** stored procedures:
   ```sql
   CALL <DATABASE>.<SCHEMA>.REFRESH_CORTEX_AI_COSTS(7);
   CALL <DATABASE>.<SCHEMA>.REFRESH_USER_AI_COSTS(7);
   ```

2. **Check** task status:
   ```sql
   SHOW TASKS LIKE 'REFRESH_CORTEX_AI_COSTS_DAILY' IN SCHEMA <DATABASE>.<SCHEMA>;
   ```
   Ask user if they want to resume the task.

3. **Cleanup**: `rm -rf /tmp/ai_cost_dashboard_deploy`

4. **Present** summary:
   ```
   Deployment complete:
   - Database/Schema: <DATABASE>.<SCHEMA>
   - Warehouse: <WAREHOUSE>
   - Credit Rate: $<CREDIT_RATE>/credit (current), $<HISTORICAL_CREDIT_RATE>/credit (historical)
   - Tables: created and populated
   - Procedures: REFRESH_CORTEX_AI_COSTS, REFRESH_USER_AI_COSTS
   - Task: REFRESH_CORTEX_AI_COSTS_DAILY (suspended/resumed)
   - Streamlit: <DATABASE>.<SCHEMA>.CORTEX_AI_COST_DASHBOARD
   - Semantic Model: @<DATABASE>.<SCHEMA>.STREAMLIT_STAGE/cortex_ai_costs_model.yaml
   ```

**Output:** Validated deployment

## Stopping Points

- After Step 2 plan: Before executing setup SQL
- After Step 3 plan: Before deploying Streamlit app

## Output

Fully deployed AI Cost Dashboard with all objects in user-specified `<DATABASE>.<SCHEMA>`.

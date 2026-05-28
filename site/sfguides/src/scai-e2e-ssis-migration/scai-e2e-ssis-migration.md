author: Andres Aguilar Moya
id: scai-e2e-ssis-migration
language: en
summary: End-to-end migration of a Microsoft SQL Server database and SSIS workflows to Snowflake using SnowConvert AI, Cortex Code, and the Snowflake CLI.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/migrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration
tags: Quickstart, Migrations, SnowConvert, SQL Server, SSIS, Cortex Code, dbt

# SnowConvert AI End-to-End SQL Server and SSIS Migration

<!-- ------------------------ -->

## Overview

Through this guide you will learn how to do an end-to-end migration of a Microsoft SQL Server environment with SSIS to Snowflake using SnowConvert AI, the Cortex Code CLI, and the Snowflake CLI. This guide walks you through project setup, extracting your source DDLs, converting them, leveraging AI to fix remaining issues in the converted code, deploying objects, migrating historical data with a **locally-run orchestrator + worker**, and finally replatforming your SSIS ETL pipelines into a Snowflake task graph plus a Snowflake-native dbt project.

The lab is driven entirely from a single Cortex Code session — at each step you tell the assistant what you want and the bundled `snowflake-migration:migration` skill orchestrates the underlying `scai` / `snow` / SQL calls.

### Prerequisites

- Familiarity with Snowflake SQL.
- Familiarity with Microsoft SQL Server and SSIS.
- Familiarity with dbt Projects on Snowflake and Snowflake tasks.

### What You'll Learn

By the end of this guide, you will learn to work with:

- The SnowConvert AI CLI to perform end-to-end migrations of SQL Server (code conversion, data migration, ETL replatform).
- The Cortex Code CLI and its bundled `snowflake-migration:migration` skill for orchestrating every phase of the migration journey.
- The Snowflake CLI's `snow dbt deploy` command to publish a Snowflake-native dbt project produced by SnowConvert.

### What You'll Need

- A SQL Server database where you have full read and write permissions.
- A Snowflake account with the `ACCOUNTADMIN` role.
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction) installed.
- [SnowConvert AI CLI](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README) installed.
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed.
- A text editor (we recommend [Visual Studio Code](https://code.visualstudio.com/)).

### What You'll Build

An end-to-end migration of a SQL Server database and an SSIS package to Snowflake, including: code conversion, hand-fixed deploy/test/fix loop, data migration using a **locally-run** Data Migration & Validation orchestrator + worker, and deployment of an SSIS-derived Snowflake task graph that calls a Snowflake-native dbt project.

## Project Setup

### Clone the Quickstart Repository

All of the source scripts, the SSIS package, and the SQL used in this quickstart live in the [`sfguide-scai-e2e-ssis-migration`](https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration) repository. Clone it to your local machine before continuing:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration.git
cd sfguide-scai-e2e-ssis-migration
```

The repository contains:

- `sourcedb/00_ddl.sql` and `sourcedb/01_data.sql` — SQL Server DDL and sample data for the TastyBytes database.
- `snowflake/init.sql` — initial Snowflake database and schemas.
- `etl/daily_sales_agg.dtsx` — the SSIS package you will migrate to Snowflake.

Later steps reference these paths (for example, when Cortex Code asks for the filesystem path to your SSIS folder, you will point it at this repository's `etl/` directory).

### SQL Server DDL and Data

1. In the SQL Server instance you will be using for this quickstart, run the `sourcedb/00_ddl.sql` script to create the database, schema, and DDLs that we will be converting.
2. Once the DDLs have been deployed successfully, run the `sourcedb/01_data.sql` script to insert sample data into the tables of the TastyBytes database.

### Snowflake Account

In your Snowflake account, run the `snowflake/init.sql` script to create the initial database (`TASTYBYTESDB`) and warehouse (`XSMALL_WH`) we will deploy into. Because this lab runs the data-migration orchestrator and worker **locally**, you do **not** need to create an SPCS compute pool.

### Snowflake Connection

To enable the Snowflake CLI and SnowConvert AI to run against our Snowflake account, we need to add the connection details to the `config.toml` file used by both CLIs. Follow the steps in this [guide](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-cli) to set up your `config.toml` with your connection details.

Test the connection:

```bash
snow connection test --connection <YOUR_SNOWFLAKE_CONNECTION_NAME>
```

In this quickstart we use a Snowflake connection named **`migrations_sc`** configured with warehouse `XSMALL_WH`, database `TASTYBYTESDB`, schema `TASTYBYTES`, and role `ACCOUNTADMIN`.

### SnowConvert AI Source Connection

Run the following command to register your SQL Server connection with SnowConvert AI so it can later extract your code and migrate your data:

```bash
scai connection add-sql-server
```

Test it:

```bash
scai connection test -l sqlserver -s <YOUR_SQL_SERVER_CONNECTION_NAME>
```

You should see a `Status: Success` row in the output. We use a SQL Server connection named **`tastybytesdb`** throughout this quickstart.

## Drive the Migration with Cortex Code

Rather than running each `scai` command manually, we drive the entire migration from a single Cortex Code session. Cortex Code ships with a `snowflake-migration:migration` skill that orchestrates project initialization, source extraction, conversion, assessment, deployment, data migration, and ETL replatforming through a guided conversation.

The sections below show the **exact prompts you'll send during the lab** and the answers we selected for this quickstart, in order.

### Start Cortex Code

From the directory where you want to host the migration project (for example, an existing `migrations_hol_summit/` folder), launch Cortex Code:

```bash
cortex
```

### Prompt 1 — Kick Off the End-to-End Migration

Tell the assistant exactly what you want, including how the data infrastructure should be deployed and what to skip:

> ```
> Migrate my SQL Server workload and SSIS packages to Snowflake by doing
> a full end-to-end migration from scratch. I want you to connect to my
> SQL Server database using the `tastybytesdb` connection registered
> already in `scai` to extract my SQL code and migrate the data from my
> tables. Make sure to setup data migration infrastructure locally and
> also do not do ETL stabilization. When the data is migrated, do not
> validate, skip to the deploy/test/fix loop
> ```

This prompt does four important things in one shot:

1. Pins the SQL Server source to the existing `tastybytesdb` connection.
2. Asks for **local** data-migration infrastructure (orchestrator + worker on the host machine — no SPCS / compute pool needed).
3. Tells Cortex Code to **skip ETL stabilization**.
4. Tells Cortex Code to **skip data validation** after the data lands and jump straight to the deploy/test/fix loop.

The skill prints:

> **Welcome to the Snowflake Migrations plugin.** Let me get started by configuring your session.

It then walks through a series of one-line prompts. Answer them as below.

### Step 1 — Initial Configuration Prompts

Cortex Code asks four short questions before it touches any code:

| Question | Answer | Why |
| --- | --- | --- |
| Enable the local migration dashboard at `http://127.0.0.1:7878`? | **Yes** | Lets you watch the migration progress in a browser. |
| Reduce permission prompts? Allowlist 12 read-only MCP tools in `settings.json`. | **Allow** | Avoids being prompted for every read-only MCP call. |
| Which source database are you migrating from? | **SQL Server** | |
| Are you starting a new migration, or do you already have pre-converted Snowflake SQL? | **Starting fresh** | |

It then confirms the active Snowflake connection and asks for the target database:

| Question | Answer |
| --- | --- |
| The active Snowflake connection is `migrations_sc`. Use it for this migration? | **Yes, use `migrations_sc`** |
| Which Snowflake database should migrated objects be deployed to? | **`TASTYBYTESDB`** |

Cortex Code verifies that `TASTYBYTESDB` exists, picks it as the deploy target, and writes `.scai/config/project.local.yml` for the project.

### Step 2 — Source Connection

Because the kickoff prompt named `tastybytesdb`, Cortex Code goes straight to the SQL Server connection list, selects `tastybytesdb`, and runs a connection test that returns `connection_test: ok`.

### Step 3 — Extract Source Code from SQL Server

Cortex Code routes into the `register-code-units` sub-skill and runs:

```bash
scai code extract -s tastybytesdb --json
```

For TastyBytes the extraction reports **19 objects in ~4s** with no failures:

| Type      | Count |
| --------- | ----- |
| Database  | 1     |
| Schema    | 3     |
| Table     | 11    |
| View      | 2     |
| Function  | 1     |
| Procedure | 1     |

SQL files land under `sqlserver-migration/source/tastybytesdb/<schema>/<object_type>/`.

### Step 4 — Convert with SnowConvert (SQL + SSIS)

The `convert` sub-skill runs next. When asked whether you have ETL code to include, point it at the cloned repo's `etl/` directory:

```
/Users/<you>/migrations_hol_summit/sfguide-scai-e2e-ssis-migration/etl
```

Cortex Code calls:

```bash
scai code convert --etl-replatform-sources-path <PATH>/etl --json
```

The conversion completes in ~12 s and reports:

- **Files processed:** 19
- **Code units converted:** 270 LOC
- **EWIs:** 2 (1 Critical, 1 Low)
- **FDMs:** 54
- **PRFs:** 27
- **ETL replatforming:** 1 SSIS package processed, 3 issues

Converted artifacts land in:

- `sqlserver-migration/snowflake/tastybytesdb/<schema>/<object_type>/` — converted tables, views, functions, procedures.
- `sqlserver-migration/snowflake/_etl/daily_sales_agg/` — Snowflake task graph SQL plus a `df_load_daily_sales` dbt project (staging views, ephemeral intermediate models, an incremental mart).
- `sqlserver-migration/reports/SnowConvert/` — CSV/JSON conversion reports.

### Step 5 — Run the Migration Assessment

Cortex Code drives `scai assessment` and asks four short questions to scope the run. For this lab pick the lean defaults:

| Question | Answer |
| --- | --- |
| Default wave size is 40-80 objects. | **Default (40-80)** |
| Any objects to push into the earliest waves? | **No prioritization** |
| How should waves be ordered? | **Category-based (default)** |
| Auto-review every Dynamic SQL occurrence? | **Skip** (no dynamic SQL in this workload) |
| Run the AI-driven per-package SSIS analysis? | **Generate-only** |

Cortex Code then dispatches three sub-skills in parallel — `waves-generator`, `object-exclusion-detection`, and `etl-assessment` — and finally renders a multi-tab HTML report at `sqlserver-migration/assessment/multi_report.html`.

The result for TastyBytes:

- **Waves:** 1 partition, 24 nodes, 8 edges, 0 cycles.
- **Object exclusion:** 0 of 19 objects excluded (no temp/staging/deprecated patterns).
- **SSIS:** 1 package classified (Data Transformation, baseline JSON only).

Open the report to review:

```bash
open sqlserver-migration/assessment/multi_report.html
```

At this point Phase 1 (setup + assessment) is complete.

## Phase 2 — Deploy Objects with the Deploy/Test/Fix Loop

Per the kickoff prompt, Cortex Code now goes straight into the deploy/test/fix loop. It asks two questions to configure the testing framework:

| Question | Answer |
| --- | --- |
| Testing path? Integration uses representative source data; unit synthesizes test data. | **Integration (source data)** |
| Optional: do you have query logs (CSV) capturing real proc invocations? | **No** (the framework will scaffold from source DB queries) |

Cortex Code then auto-deploys the `VALIDATION` schema, claims **all 16 wave-1 objects** (3 schemas, 11 tables, 1 ETL, 1 function), and walks them through their tasks.

### Step 1 — Deploy Schemas

Cortex Code calls the `deploy` MCP tool for the 3 schemas (`TastyBytes`, `dbo`, `etl_results`). All 3 succeed.

### Step 2 — Deploy Tables

Cortex Code deploys all 11 tables (`Customer`, `FoodTruck`, `OrderDetail`, `Country`, `Inventory`, `OrderHeader`, `City`, `Menu`, `etl_logs`, `EmployeeShift`, `MenuItem`). All 11 succeed.

### Step 3 — Migrate Data Locally

Because we asked for **local** data-migration infrastructure, Cortex Code:

1. Generates `.scai/settings/DataExchangeWorkerConfig.toml` from the source connection credentials.
2. Starts the local Data Exchange Worker:
   ```bash
   scai data worker start --local .scai/settings/DataExchangeWorkerConfig.toml
   ```
3. Generates the migration workflow YAML at `artifacts/data_migration/workflows/where-<hash>.yaml` covering all 11 tables (Full / Native, partitioned by primary key).
4. Runs the migration with the local orchestrator:
   ```bash
   scai data migrate start \
       --config artifacts/data_migration/workflows/where-<hash>.yaml \
       -c migrations_sc --json
   ```

The workflow finishes in ~2.3 minutes:

```
workflowName:        DATA_MIGRATION_WORKFLOW_2026_05_28_12_51_02
workflowStatus:      Finished
totalTables:         11
preprocessedTables:  11
loadedPartitions:    11/11
```

### Step 4 — Seed Tests for the Function

Cortex Code runs:

```bash
scai test seed --where "source.canonicalName ILIKE '%fn_FormatPhoneNumber%'" --append
```

This produces `artifacts/tastybytesdb/tastybytes/function/fn_formatphonenumber/test/fn_FormatPhoneNumber.yml` with the step-based template. Because this is a simple 1-parameter scalar UDF (3 branches: 10-digit / 11-digit / fallthrough), Cortex Code fills `test_cases:` directly with 20 hand-crafted rows covering each branch, plus NULL and empty-string boundary cases:

```yaml
validation:
  steps:
    - source_query: SELECT TastyBytesDB.TastyBytes.fn_FormatPhoneNumber({0}) AS "fn_FormatPhoneNumber"
      target_query: SELECT TastyBytesDB.TastyBytes.fn_FormatPhoneNumber({0}) AS "fn_FormatPhoneNumber"
  test_cases:
    # 10-digit branch
    - ["5551234567"]
    - ["555-123-4567"]
    - ["(555) 123-4567"]
    # ... 17 more cases
```

### Step 5 — Deploy the Function (Hand-Fix the Critical EWI)

The first deploy attempt fails:

```
Unsupported expression for Snowscript UDF: CASE(LEN(null), 10, ...) ...
```

SnowConvert produced a Snowflake Scripting block (`DECLARE … BEGIN … END`) inside a `LANGUAGE SQL` UDF — Snowflake's SQL UDFs only accept a single scalar expression. Rewrite the file at `sqlserver-migration/snowflake/tastybytesdb/tastybytes/function/fn_formatphonenumber.sql` as a pure scalar SQL UDF:

```sql
CREATE OR REPLACE FUNCTION TastyBytes.fn_FormatPhoneNumber (RAWPHONE STRING)
RETURNS VARCHAR(20)
LANGUAGE SQL
AS
$$
    CASE LEN(REPLACE(TRANSLATE(NVL(RAWPHONE, ''),
                ' ()-.+abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '                                                          '
            ), ' ', ''))
        WHEN 10 THEN '(' || LEFT(...) || ') ' || SUBSTRING(...) || '-' || RIGHT(...)
        WHEN 11 THEN '+' || LEFT(...) || ' (' || SUBSTRING(...) || ') ' || ...
        ELSE REPLACE(TRANSLATE(...), ' ', '')
    END
$$;
```

Redeploy and the function compiles. A quick smoke test confirms each branch:

```sql
SELECT
  TASTYBYTESDB.TASTYBYTES.fn_FormatPhoneNumber('5551234567')        AS ten_digit,
  TASTYBYTESDB.TASTYBYTES.fn_FormatPhoneNumber('15551234567')       AS eleven_digit,
  TASTYBYTESDB.TASTYBYTES.fn_FormatPhoneNumber('+1 (555) 123-4567') AS formatted_input,
  TASTYBYTESDB.TASTYBYTES.fn_FormatPhoneNumber('123')               AS short,
  TASTYBYTESDB.TASTYBYTES.fn_FormatPhoneNumber(NULL)                AS null_input;
-- → (555) 123-4567 | +1 (555) 123-4567 | +1 (555) 123-4567 | 123 | NULL
```

### Step 6 — Capture Baselines and Run Functional Tests

Now that the function is deployed, Cortex Code captures the source baselines and runs the cross-DB test:

```bash
scai test capture  --where "source.canonicalName ILIKE '%fn_FormatPhoneNumber%'"
scai test validate --where "source.canonicalName ILIKE '%fn_FormatPhoneNumber%'"
```

Result:

```
SUMMARY: 20 test cases
Passed: 20  Failed: 0  Errors: 0
```

All 20 cases match SQL Server output exactly.

### Step 7 — Claim and Deploy Wave 1 Remainder

Cortex Code now claims the remaining 3 wave-1 objects (1 procedure, 2 views) and walks them through deploy/test/fix.

### Step 8 — Deploy Views (Hand-Fix `vw_TopSellingItems`)

The `vw_CustomerOrderHistory` view deploys cleanly. `vw_TopSellingItems` fails: SnowConvert flagged the SQL Server `CROSS APPLY ... TOP 5 ORDER BY` with `SSC-EWI-TS0082` and emitted an unresolved `!!!RESOLVE EWI!!!` marker plus a non-lateral `LEFT OUTER JOIN`, which won't run in Snowflake.

Replace the file at `sqlserver-migration/snowflake/tastybytesdb/tastybytes/view/vw_topsellingitems.sql` with a window-function rewrite:

```sql
CREATE OR REPLACE VIEW TastyBytes.vw_TopSellingItems AS
WITH agg AS (
    SELECT
        oh.TruckID, mi.MenuItemID, mi.ItemName,
        SUM(od.Quantity)                AS TotalQuantitySold,
        SUM(od.Quantity * od.UnitPrice) AS TotalRevenue
    FROM TastyBytes.OrderDetail od
    INNER JOIN TastyBytes.OrderHeader oh ON od.OrderID = oh.OrderID
    INNER JOIN TastyBytes.MenuItem   mi ON od.MenuItemID = mi.MenuItemID
    WHERE oh.OrderStatus = 'Completed'
    GROUP BY oh.TruckID, mi.MenuItemID, mi.ItemName
),
ranked AS (
    SELECT a.*,
           ROW_NUMBER() OVER (PARTITION BY a.TruckID
                              ORDER BY a.TotalQuantitySold DESC) AS rn
    FROM agg a
)
SELECT ft.TruckID, ft.TruckName,
       r.MenuItemID, r.ItemName,
       r.TotalQuantitySold, r.TotalRevenue
FROM TastyBytes.FoodTruck ft
INNER JOIN ranked r ON r.TruckID = ft.TruckID
WHERE r.rn <= 5;
```

Redeploy. Both views return 25 rows, matching the source.

### Step 9 — Deploy and Test the Procedure

Cortex Code seeds tests for `sp_UpdateInventory` (a procedure that updates `Inventory` rows for a given truck, with an `Override` flag controlling absolute-set vs. increment behavior, and an early return when `TruckID IS NULL`):

```bash
scai test seed --where "source.canonicalName ILIKE '%sp_UpdateInventory%'" --append
```

Cortex Code fills `test_cases:` with 10 rows covering:

- Override = 1 (absolute set) for valid truck IDs.
- Override = 0 (increment) for valid truck IDs.
- NULL `TruckID` (early-return path).
- Non-existent `TruckID` (no rows match).

Deploy the procedure:

```sql
-- (Cortex Code runs CREATE OR REPLACE PROCEDURE … from snowflake/…/sp_updateinventory.sql)
```

Capture baselines and run validation:

```bash
scai test capture  --where "source.canonicalName ILIKE '%sp_UpdateInventory%'"
scai test validate --where "source.canonicalName ILIKE '%sp_UpdateInventory%'"
```

Manual smoke tests confirm the procedure's behavior matches SQL Server semantics on all three branches:

```sql
-- Override = 1 sets QuantityOnHand absolutely
CALL TASTYBYTESDB.TASTYBYTES.sp_UpdateInventory(1, 999.00, 1);
SELECT INVENTORYID, QUANTITYONHAND
FROM TASTYBYTESDB.TASTYBYTES.INVENTORY WHERE TRUCKID = 1;
-- → all 3 rows: 999.00

-- Override = 0 increments
CALL TASTYBYTESDB.TASTYBYTES.sp_UpdateInventory(1, 50.00, 0);
-- → all 3 rows: 1049.00 (= 999 + 50)

-- NULL TruckID → no rows changed
CALL TASTYBYTESDB.TASTYBYTES.sp_UpdateInventory(NULL, 100.00, 1);
-- → 0 rows updated
```

### Verify the Code Deployment

A quick sanity check against `INFORMATION_SCHEMA`:

```sql
SELECT 'BASE TABLE' AS kind, COUNT(*) AS cnt
FROM TASTYBYTESDB.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'TASTYBYTES' AND table_type='BASE TABLE'
UNION ALL SELECT 'VIEW',     COUNT(*) FROM TASTYBYTESDB.INFORMATION_SCHEMA.VIEWS      WHERE table_schema='TASTYBYTES'
UNION ALL SELECT 'FUNCTION', COUNT(*) FROM TASTYBYTESDB.INFORMATION_SCHEMA.FUNCTIONS  WHERE function_schema='TASTYBYTES'
UNION ALL SELECT 'PROCEDURE',COUNT(*) FROM TASTYBYTESDB.INFORMATION_SCHEMA.PROCEDURES WHERE procedure_schema='TASTYBYTES';
```

Expected:

| KIND       | CNT |
| ---------- | --- |
| BASE TABLE | 11  |
| VIEW       | 2   |
| FUNCTION   | 1   |
| PROCEDURE  | 1   |

Plus the `TASTYBYTESDB.ETL_RESULTS.ETL_LOGS` helper table in `etl_results`.

## Phase 3 — Verify the Migrated Data

The data was already migrated in Phase 2 / Step 3. Confirm row counts on Snowflake:

```sql
SELECT 'Country'       AS tbl, COUNT(*) AS row_cnt FROM TASTYBYTESDB.TASTYBYTES.Country
UNION ALL SELECT 'City',          COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.City
UNION ALL SELECT 'Customer',      COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.Customer
UNION ALL SELECT 'FoodTruck',     COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.FoodTruck
UNION ALL SELECT 'Menu',          COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.Menu
UNION ALL SELECT 'MenuItem',      COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.MenuItem
UNION ALL SELECT 'Inventory',     COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.Inventory
UNION ALL SELECT 'OrderHeader',   COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.OrderHeader
UNION ALL SELECT 'OrderDetail',   COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.OrderDetail
UNION ALL SELECT 'EmployeeShift', COUNT(*) FROM TASTYBYTESDB.TASTYBYTES.EmployeeShift
ORDER BY tbl;
```

## Phase 4 — Deploy the dbt Project and the SSIS Task Graph

With the database workload migrated, the last phase is to deploy the SSIS-derived artifacts. SnowConvert produced two things under `sqlserver-migration/snowflake/_etl/daily_sales_agg/`:

- A **task-graph SQL file** (`daily_sales_agg.sql`) defining a 4-task chain: a root task → an `_insert_start_log` task → a `_df_load_daily_sales` task that calls `EXECUTE DBT PROJECT …` → an `_insert_end_log` task. The root task has **no warehouse** and the children all use `WAREHOUSE=DUMMY_WAREHOUSE` placeholders.
- A **dbt project** (`df_load_daily_sales/`) with two staging views, four ephemeral intermediate models, an incremental mart (`ole_db_destination` → materializes as `DAILYSALESAGG`), `dbt_project.yml`, and `profiles.yml` — but with placeholder values like `YOUR_PROJECT_NAME` and `YOUR_PROFILE_NAME`.

### Prompt 2 — Deploy the dbt Project and the Task Graph

Tell Cortex Code:

> ```
> Now I want to deploy my generated dbt project and my Snowflake task graph
> to Snowflake. Make sure to deploy my task graph using the `XSMALL_WH`
> warehouse for each task.
> ```

Cortex Code loads the `dbt-projects-on-snowflake` skill and starts patching the placeholders.

### Step 1 — Patch the dbt Project Files

Cortex Code rewrites the three files with concrete values pulled from the active session config:

`dbt_project.yml`:

```yaml
name: df_load_daily_sales
version: 1.0.0
config-version: 2
profile: df_load_daily_sales
model-paths:   [models]
macro-paths:   [macros]
seed-paths:    [seeds]
test-paths:    [tests]
analysis-paths:[analyses]
snapshot-paths:[snapshots]
models:
  df_load_daily_sales:
    staging:      { +materialized: view }
    intermediate: { +materialized: ephemeral }
    marts:        { +materialized: incremental }
```

`profiles.yml` (the `snow dbt deploy` validator requires `role`; `account` and `user` are not needed because dbt runs **inside** Snowflake):

```yaml
df_load_daily_sales:
  target: dev
  outputs:
    dev:
      type: snowflake
      role: ACCOUNTADMIN
      database: TASTYBYTESDB
      schema: PUBLIC
      threads: 4
```

`models/sources.yml`:

```yaml
version: 2
sources:
  - name: raw
    database: TASTYBYTESDB
    schema: TASTYBYTES
    tables:
      - name: OrderDetail
      - name: OrderHeader
```

### Step 2 — Deploy dbt project with the Snowflake CLI

Cortex Code runs:

```bash
snow dbt deploy df_load_daily_sales \
    --source <PATH>/sqlserver-migration/snowflake/_etl/daily_sales_agg/df_load_daily_sales \
    --database TASTYBYTESDB \
    --schema PUBLIC
```

The successful run looks like:

```
Creating temporary stage
Copying project files to stage
  Copied 13 files
Creating DBT project
+-------------------------------------------+
| status                                    |
|-------------------------------------------|
| DF_LOAD_DAILY_SALES successfully created. |
+-------------------------------------------+
```

> **Heads-up — schema resolution.** `snow dbt deploy` honors the connection's default schema over the `--schema` flag, so the dbt project actually lands at **`TASTYBYTESDB.TASTYBYTES.DF_LOAD_DAILY_SALES`** (matching the connection's `schema = "TASTYBYTES"`), not `TASTYBYTESDB.PUBLIC`. We'll use the actual location when wiring up the task graph below.

Verify with SQL:

```sql
SHOW DBT PROJECTS;
```

You should see `DF_LOAD_DAILY_SALES` at version `VERSION$1` running dbt 1.9.4.

### Step 3 — Deploy the Task Graph (XSMALL_WH per Task)

Cortex Code rewrites the task-graph file to:

- Replace every `WAREHOUSE=DUMMY_WAREHOUSE` with `WAREHOUSE = XSMALL_WH`.
- Add `WAREHOUSE = XSMALL_WH` to the root task `daily_sales_agg` (which SnowConvert left without a warehouse).
- Re-point the `EXECUTE DBT PROJECT` call from the placeholder `public.df_load_daily_sales` to the actual location `TASTYBYTESDB.TASTYBYTES.DF_LOAD_DAILY_SALES`.
- Qualify the `INSERT INTO etl_results.etl_logs` calls with the database (`TASTYBYTESDB.ETL_RESULTS.ETL_LOGS`).

The final file:

```sql
USE DATABASE TASTYBYTESDB;
USE SCHEMA PUBLIC;

CREATE OR REPLACE TASK PUBLIC.daily_sales_agg
  WAREHOUSE = XSMALL_WH
AS SELECT 1;

CREATE OR REPLACE TASK PUBLIC.daily_sales_agg_insert_start_log
  WAREHOUSE = XSMALL_WH
  AFTER PUBLIC.daily_sales_agg
AS
BEGIN
  INSERT INTO TASTYBYTESDB.ETL_RESULTS.ETL_LOGS (name, execution_date)
  VALUES ('pkg_daily_sales_aggregate start', CURRENT_TIMESTAMP());
END;

CREATE OR REPLACE TASK PUBLIC.daily_sales_agg_df_load_daily_sales
  WAREHOUSE = XSMALL_WH
  AFTER PUBLIC.daily_sales_agg_insert_start_log
AS
BEGIN
  EXECUTE DBT PROJECT TASTYBYTESDB.TASTYBYTES.DF_LOAD_DAILY_SALES
    ARGS='build --target dev';
END;

CREATE OR REPLACE TASK PUBLIC.daily_sales_agg_insert_end_log
  WAREHOUSE = XSMALL_WH
  AFTER PUBLIC.daily_sales_agg_df_load_daily_sales
AS
BEGIN
  INSERT INTO TASTYBYTESDB.ETL_RESULTS.ETL_LOGS (name, execution_date)
  VALUES ('pkg_daily_sales_aggregate end', CURRENT_TIMESTAMP());
END;
```

Cortex Code applies the file via `sql_execute` for each `CREATE OR REPLACE TASK` statement. Verify:

```sql
SHOW TASKS IN SCHEMA TASTYBYTESDB.PUBLIC;
```

All 4 tasks should appear with `XSMALL_WH`. Three children (`_insert_start_log`, `_df_load_daily_sales`, `_insert_end_log`) come up `started` automatically; the root `daily_sales_agg` is `suspended` (correct — root tasks without a SCHEDULE stay suspended and are triggered on-demand).

### Prompt 3 — Resume and Run the Task Graph

Tell Cortex Code:

> ```
> now resume and deploy the task graph
> ```

Trying to `ALTER TASK ... RESUME` on the root will fail with:

```
Task TASTYBYTESDB.PUBLIC.DAILY_SALES_AGG should have a SCHEDULE, AFTER, FINALIZE
or WHEN to be resumed.
```

That's expected — the root has no SCHEDULE. Cortex Code asks how to proceed:

| Question | Answer |
| --- | --- |
| The root task `daily_sales_agg` needs a SCHEDULE before it can be resumed. What should I do? | **Execute once now** |

Cortex Code triggers it on-demand:

```sql
EXECUTE TASK TASTYBYTESDB.PUBLIC.daily_sales_agg;
```

### Step 4 — Verify the Run

Poll the run history a minute later:

```sql
SELECT NAME, STATE, ERROR_CODE, QUERY_START_TIME, COMPLETED_TIME
FROM TABLE(TASTYBYTESDB.INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('minute', -10, CURRENT_TIMESTAMP()),
    RESULT_LIMIT => 50))
WHERE NAME LIKE 'DAILY_SALES_AGG%'
ORDER BY QUERY_START_TIME;
```

All 4 tasks should be `SUCCEEDED`. End-to-end execution is roughly 19 seconds:

```
DAILY_SALES_AGG                       SUCCEEDED  ~1s
  └─→ DAILY_SALES_AGG_INSERT_START_LOG  SUCCEEDED  ~1s
        └─→ DAILY_SALES_AGG_DF_LOAD_DAILY_SALES SUCCEEDED ~14s  (EXECUTE DBT PROJECT)
              └─→ DAILY_SALES_AGG_INSERT_END_LOG SUCCEEDED  ~1s
```

### Step 5 — Inspect the Side-Effects

```sql
-- Logs written by the start/end log tasks
SELECT NAME, EXECUTION_DATE
FROM TASTYBYTESDB.ETL_RESULTS.ETL_LOGS
ORDER BY EXECUTION_DATE DESC LIMIT 5;
-- → 'pkg_daily_sales_aggregate end'   <ts>
-- → 'pkg_daily_sales_aggregate start' <ts>

-- Tables and views the dbt project materialized in TASTYBYTESDB.PUBLIC
SELECT TABLE_NAME, TABLE_TYPE
FROM TASTYBYTESDB.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
ORDER BY TABLE_NAME;
-- → DAILYSALESAGG               BASE TABLE   (the incremental mart)
-- → STG_RAW__ORDERDETAILSOURCE  VIEW         (staging view)
-- → STG_RAW__ORDERHEADER        VIEW         (staging view)
```

### Prompt 4 — Inspect the Mart

> ```
> show me the mart model rows.
> ```

```sql
SELECT * FROM TASTYBYTESDB.PUBLIC.DAILYSALESAGG ORDER BY SALEDATE, TRUCKID;
```

Expected: 22 rows, one per `(TruckID, SaleDate)` pair from completed orders, with `OrderCount`, `GrossRevenue`, `TotalTips`, and `ItemsSold` aggregated per truck-day. Totals across the mart: 22 truck-day rows, 22 orders, $1,015.31 gross revenue, $139.50 tips, 39 items sold.

The intermediate models stay ephemeral (inlined as CTEs) — they don't appear in `INFORMATION_SCHEMA.TABLES`.

At this point all four phases are complete:

```
✅ Setup       — project initialized, connections registered, local infra ready
✅ Phase 1     — 19 objects extracted, 19 files converted, assessment generated
✅ Phase 2     — 16 wave-1 objects deployed (deploy/test/fix loop)
                 + 3 additional objects (1 procedure, 2 views) hand-fixed and deployed
                 + 11 tables, 185 rows migrated locally
                 + data validation skipped per kickoff prompt
                 + ETL stabilization skipped per kickoff prompt
✅ Phase 3     — row counts verified on Snowflake
✅ Phase 4     — dbt project deployed via `snow dbt deploy`,
                 4-task graph deployed with XSMALL_WH per task, executed end-to-end
```

<!-- ------------------------ -->

## Conclusion And Resources

Congratulations! You've taken a Microsoft SQL Server database and an SSIS pipeline all the way from source extraction to a fully deployed, populated, and *running* workload in Snowflake — driven end-to-end by the Cortex Code CLI and its `snowflake-migration:migration` skill, plus the `snow dbt deploy` workflow for the SnowConvert-generated dbt project.

You started from a blank project, set up **local** data-migration infrastructure (no SPCS / compute pool needed), registered 19 SQL Server objects and 1 SSIS package, converted them with SnowConvert AI, generated a deployment plan with a classified SSIS assessment, deployed every in-scope database object using a deploy/test/fix loop (hand-fixing 2 conversion artifacts — a SQL UDF that needed to be turned into a pure scalar UDF, and a `CROSS APPLY` view rewritten with window functions), migrated 185 rows of data via the locally-run orchestrator + worker, and finally hand-patched and deployed both the SnowConvert-generated dbt project (`snow dbt deploy`) and the SnowConvert-generated Snowflake task graph (with `XSMALL_WH` per task), executing the full graph end-to-end on demand.

### What You Learned

- How to drive an end-to-end SQL Server + SSIS migration with **Cortex Code** and the bundled `snowflake-migration:migration` skill, using just five chat prompts.
- How **SnowConvert AI** extracts, converts, and deploys a SQL Server workload to Snowflake, and how to read its EWIs, FDMs, and PRFs.
- How to triage and hand-fix common SnowConvert outputs — turning a procedural Snowflake Scripting block into a pure scalar SQL UDF, and rewriting a SQL Server `CROSS APPLY ... TOP` with `ROW_NUMBER() OVER (PARTITION BY ...)`.
- How to run the data-migration orchestrator and Data Exchange Worker **locally** for SQL Server → Snowflake table loads, without provisioning SPCS.
- How to use the seed → capture → validate testing framework against your source database to verify the migrated function produces identical output to the SQL Server original.
- How to deploy a SnowConvert-generated dbt project to Snowflake via `snow dbt deploy`, then point a Snowflake task graph at it with `EXECUTE DBT PROJECT`.

### Related Resources

- **Quickstart source code**: [`sfguide-scai-e2e-ssis-migration`](https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration) — DDLs, sample data, the SSIS package, and the initial Snowflake setup used throughout this guide.
- [SnowConvert AI CLI documentation](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README) — reference for `scai code extract`, `scai code convert`, `scai code deploy`, `scai data migrate`, `scai test seed/capture/validate`.
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) — install and usage guide for the CLI that hosts the migration skills.
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction) — used here for the connection config that both `scai` and `snow` share, and for `snow dbt deploy`.
- [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects/about-dbt-projects) — target pattern for the replatformed SSIS data flows produced by `migrate-etl-package`.
- [Snowflake tasks](https://docs.snowflake.com/en/user-guide/tasks-intro) — background for the four-task graph with `EXECUTE DBT PROJECT` deployed in Phase 4.
- [Snowflake Scripting reference](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/index) — background for the procedure rewrites.

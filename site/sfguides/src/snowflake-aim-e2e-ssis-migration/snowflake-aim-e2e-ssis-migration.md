author: Andres Aguilar Moya
id: snowflake-aim-e2e-ssis-migration
language: en
summary: End-to-end migration of a Microsoft SQL Server database and SSIS workflows to Snowflake using Snowflake AIM, Cortex Code, and the Snowflake CLI.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/migrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration

# Snowflake AIM End-to-End SQL Server and SSIS Migration
<!-- ------------------------ -->
## Overview

Snowflake AIM unifies the proven capabilities of SnowConvert AI, Snowpark Migration Accelerator, and Datometry into a single AI-powered platform for assessing, modernizing, and migrating enterprise data and code workloads to Snowflake. Designed to reduce the complexity, risk, and operational overhead traditionally associated with large-scale migrations, Snowflake AIM enables organizations to define their target state while the platform orchestrates the migration process end to end. From analyzing Spark code and converting APIs to Snowpark, to modernizing warehouses, tables, views, ETL pipelines, reporting assets, and stored procedures across major platforms, Snowflake AIM combines intelligent assessment, automated code conversion, dependency mapping, orchestration, and virtualization into a unified migration experience. By eliminating the need to rebuild workloads from scratch or maintain parallel legacy environments, Snowflake AIM dramatically accelerates modernization timelines while minimizing disruption to ongoing business operations.

Through this guide you will learn how to do an end-to-end migration of a Microsoft SQL Server environment with SSIS to Snowflake using Snowflake AIM, the Cortex Code CLI, and the Snowflake CLI. This guide walks you through project setup, extracting your source DDLs, converting them, leveraging AI to fix remaining issues in the converted code, deploying objects, migrating historical data with a **locally-run orchestrator + worker**, and finally replatforming your SSIS ETL pipelines into a Snowflake task graph plus a Snowflake-native dbt project.

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

All of the source scripts, the SSIS package, and the SQL used in this quickstart live in the `[sfguide-scai-e2e-ssis-migration](https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration)` repository. Clone it to your local machine before continuing:

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

In this quickstart we use a Snowflake connection named `**migrations_sc**` configured with warehouse `XSMALL_WH`, database `TASTYBYTESDB`, schema `TASTYBYTES`, and role `ACCOUNTADMIN`.

### SnowConvert AI Source Connection

Run the following command to register your SQL Server connection with SnowConvert AI so it can later extract your code and migrate your data:

```bash
scai connection add-sql-server
```

Test it:

```bash
scai connection test -l sqlserver -s <YOUR_SQL_SERVER_CONNECTION_NAME>
```

You should see a `Status: Success` row in the output. We use a SQL Server connection named `**tastybytesdb**` throughout this quickstart.

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
> also do not do ETL stabilization. When the tables are deployed and
> their data is migrated, do not validate their data, 
> skip to deployment and validation of the views, functions, and procedures.
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


| Question                                                                              | Answer             | Why                                                 |
| ------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------- |
| Enable the local migration dashboard at `http://127.0.0.1:7878`?                      | **Yes**            | Lets you watch the migration progress in a browser. |
| Reduce permission prompts? Allowlist 12 read-only MCP tools in `settings.json`.       | **Allow**          | Avoids being prompted for every read-only MCP call. |
| Which source database are you migrating from?                                         | **SQL Server**     |                                                     |
| Are you starting a new migration, or do you already have pre-converted Snowflake SQL? | **Starting fresh** |                                                     |


It then confirms the active Snowflake connection and asks for the target database:


| Question                                                                       | Answer                       |
| ------------------------------------------------------------------------------ | ---------------------------- |
| The active Snowflake connection is `migrations_sc`. Use it for this migration? | **Yes, use `migrations_sc`** |
| Which Snowflake database should migrated objects be deployed to?               | `**TASTYBYTESDB**`           |


Cortex Code verifies that `TASTYBYTESDB` exists, picks it as the deploy target, and writes `.scai/config/project.local.yml` for the project.

### Step 2 — Source Connection

Because the kickoff prompt named `tastybytesdb`, Cortex Code goes straight to the SQL Server connection list, selects `tastybytesdb`, and runs a connection test that returns `connection_test: ok`.

### Step 3 — Extract Source Code from SQL Server

Cortex Code routes into the `register-code-units` sub-skill and runs:

```bash
scai code extract -s tastybytesdb --json
```

For TastyBytes the extraction reports **18 objects in ~1.5s** with no failures:


| Type      | Count |
| --------- | ----- |
| Database  | 1     |
| Schema    | 3     |
| Table     | 11    |
| View      | 1     |
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

The conversion completes in ~10 s and reports:

- **Files processed:** 18
- **Code units converted:** 250 LOC
- **EWIs:** 2 (1 High, 1 Medium)
- **FDMs:** 57
- **PRFs:** 28
- **ETL replatforming:** 1 SSIS package processed, 3 issues

Converted artifacts land in:

- `sqlserver-migration/snowflake/tastybytesdb/<schema>/<object_type>/` — converted tables, views, functions, procedures.
- `sqlserver-migration/snowflake/_etl/daily_sales_agg/` — Snowflake task graph SQL plus a `df_load_daily_sales` dbt project (staging views, ephemeral intermediate models, an incremental mart).
- `sqlserver-migration/reports/SnowConvert/` — CSV/JSON conversion reports.

### Step 5 — Run the Migration Assessment

Cortex Code drives `scai assessment` and asks four short questions to scope the run. For this lab pick the lean defaults:


| Question                                     | Answer                                     |
| -------------------------------------------- | ------------------------------------------ |
| Default wave size is 40-80 objects.          | **Default (40-80)**                        |
| Any objects to push into the earliest waves? | **No prioritization**                      |
| How should waves be ordered?                 | **Category-based (default)**               |
| Auto-review every Dynamic SQL occurrence?    | **Skip** (no dynamic SQL in this workload) |
| Run the AI-driven per-package SSIS analysis? | **Generate-only**                          |


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


| Question                                                                               | Answer                                                      |
| -------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Testing path? Integration uses representative source data; unit synthesizes test data. | **Integration (source data)**                               |
| Optional: do you have query logs (CSV) capturing real proc invocations?                | **Yes** — point it at `sfguide-scai-e2e-ssis-migration/source_db/query_log.csv` so test cases are seeded from real calls |


Cortex Code then auto-deploys the `VALIDATION` schema and claims the **14 deployable wave-1 objects** (3 schemas, 11 tables) — leaving the SSIS/ETL object unclaimed per the *skip ETL stabilization* instruction — and walks them through their tasks. The view, function, and procedure are claimed in a later batch once their dependency tables are migrated.

### Step 1 — Deploy Schemas

Cortex Code calls the `deploy` MCP tool for the 3 schemas (`TastyBytes`, `dbo`, `etl_results`). All 3 succeed.

### Step 2 — Deploy Tables

Cortex Code deploys all 11 tables (`Customer`, `FoodTruck`, `OrderDetail`, `Country`, `Inventory`, `OrderHeader`, `City`, `Menu`, `etl_logs`, `EmployeeShift`, `MenuItem`). All 11 succeed.

### Step 3 — Migrate Data Locally

Because we asked for **local** data-migration infrastructure (no SPCS / compute pool), Cortex Code:

1. Verifies the Microsoft ODBC Driver for SQL Server is installed (required by the Data Exchange Worker).
2. Generates `.scai/settings/DataExchangeWorkerConfig.toml` from the source connection credentials.
3. Generates the migration workflow YAML at `artifacts/data_migration/workflows/where-<hash>.yaml` covering all 11 tables (Full / Native, each partitioned by its integer primary key — an empty `columnNamesToPartitionBy` would finish the workflow without moving any data, so a key column per table is required).
4. Runs the migration with a **local** orchestrator and worker in a single command. The local path uses `create-workflow` with `--start-orchestrator --start-worker` (not `scai data migrate start`, which targets the SPCS/cloud orchestrator):
  ```bash
   scai data migrate create-workflow \
       --config artifacts/data_migration/workflows/where-<hash>.yaml \
       --start-orchestrator --start-worker
  ```

The workflow finishes in a few minutes with every partition loaded:

```
workflowName:        DATA_MIGRATION_WORKFLOW_2026_06_29_15_01_48
workflowStatus:      Finished
totalTables:         11
preprocessedTables:  11
loadedPartitions:    11/11
```

### Step 4 — Seed Tests for the Function

Because we answered **Yes** to the query-log question, Cortex Code runs `scai test seed` with `--execution-log` so the cases are hydrated from real captured calls:

```bash
scai test seed \
  --where "source.canonicalName ILIKE '%fn_FormatCustomerName%'" \
  --append \
  --execution-log <PATH>/sfguide-scai-e2e-ssis-migration/source_db/query_log.csv
```

This produces `artifacts/tastybytesdb/tastybytes/function/fn_formatcustomername/test/fn_FormatCustomerName.yml`. The seed finds 6 executions in the log and populates `test_cases:` with the 3 distinct `CustomerID` values that were actually called — so no AI swarm fill is needed:

```yaml
validation:
  steps:
    - source_query: SELECT TastyBytesDB.TastyBytes.fn_FormatCustomerName({0}) AS "fn_FormatCustomerName"
      target_query: SELECT TastyBytesDB.TastyBytes.fn_FormatCustomerName({0}) AS "fn_FormatCustomerName"
  test_cases:
    - [2]
    - [3]
    - [1]
```

### Step 5 — Deploy the Function

SnowConvert produced a clean Snowflake SQL UDF for this scalar function — no manual rewrites required. The converted file at `sqlserver-migration/snowflake/tastybytesdb/tastybytes/function/fn_formatcustomername.sql` deploys directly:

```sql
CREATE OR REPLACE FUNCTION TastyBytes.fn_FormatCustomerName (P_CUSTOMERID INT)
RETURNS NVARCHAR(402)
LANGUAGE SQL
AS
$$
    WITH CTE1 AS (
        SELECT
            CAST(UPPER(RTRIM(LTRIM(NVL(LastName, '')))) ||
                 ', ' || RTRIM(LTRIM(NVL(FirstName, ''))) AS NVARCHAR(402)) AS FULLNAME
        FROM TastyBytes.Customer
        WHERE CustomerID = P_CUSTOMERID
    )
    SELECT FULLNAME FROM CTE1
$$;
```

A quick smoke test against the seeded customer IDs:

```sql
SELECT
  TASTYBYTESDB.TASTYBYTES.fn_FormatCustomerName(1) AS customer_1,
  TASTYBYTESDB.TASTYBYTES.fn_FormatCustomerName(2) AS customer_2,
  TASTYBYTESDB.TASTYBYTES.fn_FormatCustomerName(3) AS customer_3;
-- → "LASTNAME, Firstname" for each existing customer
```

### Step 6 — Capture Baselines and Run Functional Tests

Now that the function is deployed, Cortex Code captures the source baselines and runs the cross-DB test:

```bash
scai test capture  --where "source.canonicalName ILIKE '%fn_FormatCustomerName%'"
scai test validate --where "source.canonicalName ILIKE '%fn_FormatCustomerName%'"
```

Result:

```
SUMMARY: 3 test cases
Passed: 3  Failed: 0  Errors: 0
```

All 3 cases match SQL Server output exactly (`data_match`) on the first run.

### Step 7 — Claim and Deploy Wave 1 Remainder

Cortex Code now claims the remaining wave-1 objects — the **view and the procedure** — and walks them through deploy/test/fix.

### Step 8 — Deploy the View (Hand-Fix `vw_TopSellingItems`)

`vw_TopSellingItems` fails to deploy with a SQL compilation error (`unexpected '!'`). The SQL Server view uses `SELECT TOP 1 PERCENT ... ORDER BY ...` in two subqueries combined with `UNION`. SnowConvert flagged `SSC-EWI-0040` (the `TOP PERCENT` clause is not supported in Snowflake) and left unresolved `!!!RESOLVE EWI!!!` marker text in the file, alongside a leading `USE DATABASE TastyBytesDB;` that points at the **source** database. The fix is to delete the marker text and the `USE DATABASE` line, fully qualify the view name with the target database, and rewrite each `TOP 1 PERCENT ... ORDER BY <expr> DESC` as a Snowflake `QUALIFY ROW_NUMBER() OVER (ORDER BY <expr> DESC) <= CEIL(0.01 * COUNT(*) OVER ())` — which preserves SQL Server's ceiling semantics for the percentage of rows returned.

Replace the file at `sqlserver-migration/snowflake/tastybytesdb/tastybytes/view/vw_topsellingitems.sql` with:

```sql
CREATE OR REPLACE VIEW TASTYBYTESDB.TastyBytes.vw_TopSellingItems
AS
SELECT * FROM (
    SELECT
        mi.MenuItemID,
        mi.ItemName,
        SUM(od.Quantity)                AS TotalQuantitySold,
        SUM(od.Quantity * od.UnitPrice) AS TotalRevenue,
        'By Quantity'                   AS RankingBasis
    FROM TASTYBYTESDB.TastyBytes.OrderDetail od
    INNER JOIN TASTYBYTESDB.TastyBytes.OrderHeader oh ON od.OrderID = oh.OrderID
    INNER JOIN TASTYBYTESDB.TastyBytes.MenuItem   mi ON od.MenuItemID = mi.MenuItemID
    WHERE oh.OrderStatus = 'Completed'
    GROUP BY mi.MenuItemID, mi.ItemName
    QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(od.Quantity) DESC, mi.MenuItemID)
            <= CEIL(0.01 * COUNT(*) OVER ())
) AS q
UNION
SELECT * FROM (
    SELECT
        mi.MenuItemID,
        mi.ItemName,
        SUM(od.Quantity)                AS TotalQuantitySold,
        SUM(od.Quantity * od.UnitPrice) AS TotalRevenue,
        'By Revenue'                    AS RankingBasis
    FROM TASTYBYTESDB.TastyBytes.OrderDetail od
    INNER JOIN TASTYBYTESDB.TastyBytes.OrderHeader oh ON od.OrderID = oh.OrderID
    INNER JOIN TASTYBYTESDB.TastyBytes.MenuItem   mi ON od.MenuItemID = mi.MenuItemID
    WHERE oh.OrderStatus = 'Completed'
    GROUP BY mi.MenuItemID, mi.ItemName
    QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(od.Quantity * od.UnitPrice) DESC, mi.MenuItemID)
            <= CEIL(0.01 * COUNT(*) OVER ())
) AS r;
```

Redeploy. Cortex Code then validates the view against the source by comparing row counts and a 10-row spot check — both sides return **2 rows** with matching values (the only differences are cosmetic: Snowflake folds identifiers to uppercase and shows trailing decimal zeros).

### Step 9 — Deploy and Test the Procedure

Cortex Code seeds tests for `sp_UpdateInventory` (a procedure that updates `Inventory` rows for a given truck, with an `Override` flag controlling absolute-set vs. increment behavior, and an early return when `TruckID IS NULL`). It returns **no result set**, so we seed from the query log:

```bash
scai test seed \
  --where "source.canonicalName ILIKE '%sp_UpdateInventory%'" \
  --append \
  --execution-log <PATH>/sfguide-scai-e2e-ssis-migration/source_db/query_log.csv
```

The seed populates 3 `test_cases:` of `[TruckID, StockCount, Override]`. Because this proc is **side-effect-only DML**, the default seeded YAML (which only compares the empty return) would pass trivially. Cortex Code edits the YAML to mark the CALL step `validate: false` and add a post-condition step that compares the affected `Inventory` row on both source and target, plus the `modifies_data` / `affected_tables` hints for delta capture:

```yaml
validation:
  steps:
    - source_query: EXECUTE TastyBytesDB.TastyBytes.sp_UpdateInventory @TruckID = {0}, @StockCount = {1}, @Override = {2}
      target_query: CALL TastyBytesDB.TastyBytes.sp_UpdateInventory({0}, {1}, {2})
      validate: false
    - both: "SELECT QuantityOnHand FROM TastyBytesDB.TastyBytes.Inventory WHERE TruckID = {0}"
  modifies_data: true
  affected_tables:
    - TastyBytesDB.TastyBytes.Inventory
  test_cases:
    - [3, 75.00, 1]
    - [1, 100.00, 1]
    - [2, 25.50, 0]
```

Deploy the procedure:

```sql
-- (Cortex Code runs CREATE OR REPLACE PROCEDURE … from snowflake/…/sp_updateinventory.sql)
```

Re-capture baselines (now that the YAML reads the affected table) and run validation:

```bash
scai test capture  --where "source.canonicalName ILIKE '%sp_UpdateInventory%'"
scai test validate --where "source.canonicalName ILIKE '%sp_UpdateInventory%'"
```

All 3 cases come back as **PASS** with `result_and_delta_match` — both the post-condition row and the captured table delta match SQL Server:


| Case                                             | Status | Notes                     |
| ------------------------------------------------ | ------ | ------------------------- |
| `TruckID = 3, StockCount = 75.00, Override = 1`  | PASS   | Absolute-set on truck 3.  |
| `TruckID = 1, StockCount = 100.00, Override = 1` | PASS   | Absolute-set on truck 1.  |
| `TruckID = 2, StockCount = 25.50, Override = 0`  | PASS   | Increment on truck 2.     |


The procedure produces identical post-run `Inventory` state on SQL Server and Snowflake across every test case, confirming the converted Snowflake Scripting body matches the original T-SQL semantics exactly.

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
| VIEW       | 1   |
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

### Prompt 2 — Deploy and Run Everything

Tell Cortex Code:

> ```
> Now I want to deploy my generated dbt project and my Snowflake task graph
> to Snowflake in the `snowflake` directory and using the `snow dbt deploy`
> command, the dbt project object in Snowflake should be deployed in
> the TastyBytes schema.
> Make sure to deploy my task graph using the `XSMALL_WH` warehouse
> for each task and that the dbt project is referenced through the 
> TastyBytes schema. Once the dbt project and the task graph are both deployed
> execute the task graph and show me the rows of the materialized mart model
> in the dbt project.
> ```

Cortex Code loads the `dbt-projects-on-snowflake` skill and works through three high-level steps before triggering the run:

1. **Patch the dbt project files.** SnowConvert wrote `dbt_project.yml`, `profiles.yml`, and `models/sources.yml` with placeholders (`YOUR_PROJECT_NAME`, `YOUR_PROFILE_NAME`, `YOUR_DB`, `YOUR_SCHEMA`). Cortex Code rewrites them with the concrete project name `df_load_daily_sales`, target `dev`, role `ACCOUNTADMIN`, warehouse `XSMALL_WH`, database `TASTYBYTESDB`, sources at `TASTYBYTESDB.TASTYBYTES`, and drops the `account` / `user` / `password` fields (dbt runs *inside* Snowflake, so those aren't needed).
2. **Deploy the dbt project with `snow dbt deploy`:**
  ```bash
   snow dbt deploy df_load_daily_sales \
       --source <PATH>/snowflake/_etl/daily_sales_agg/df_load_daily_sales \
       --database TASTYBYTESDB --schema PUBLIC
  ```
   `snow dbt deploy` honors the connection's default schema over `--schema`, so the project actually lands at `**TASTYBYTESDB.TASTYBYTES.DF_LOAD_DAILY_SALES**` (matching the connection's `schema = "TASTYBYTES"`). Cortex Code re-points the task graph at the actual location.
3. **Deploy the 4-task graph and run it.** Cortex Code rewrites `daily_sales_agg.sql`: every `WAREHOUSE=DUMMY_WAREHOUSE` becomes `WAREHOUSE = XSMALL_WH`, the root task gets `WAREHOUSE = XSMALL_WH` added, the `INSERT INTO etl_results.etl_logs` calls get fully qualified to `TASTYBYTESDB.ETL_RESULTS.ETL_LOGS`, and the `EXECUTE DBT PROJECT` call points at `TASTYBYTESDB.TASTYBYTES.DF_LOAD_DAILY_SALES`. Cortex Code applies the four `CREATE OR REPLACE TASK` statements, resumes the three child tasks, and triggers the root with `EXECUTE TASK TASTYBYTESDB.PUBLIC.daily_sales_agg`.

Once `EXECUTE TASK` is dispatched, Cortex Code polls `TASK_HISTORY` until all four tasks land at `SUCCEEDED`:

```
DAILY_SALES_AGG                       SUCCEEDED  ~1s
  └─→ DAILY_SALES_AGG_INSERT_START_LOG  SUCCEEDED  ~1s
        └─→ DAILY_SALES_AGG_DF_LOAD_DAILY_SALES SUCCEEDED ~14s  (EXECUTE DBT PROJECT)
              └─→ DAILY_SALES_AGG_INSERT_END_LOG SUCCEEDED  ~1s
```

The `EXECUTE DBT PROJECT` call ran `dbt build --target dev` inside Snowflake: 2 staging views, 4 ephemeral intermediate models (inlined as CTEs and not visible in `INFORMATION_SCHEMA.TABLES`), and 1 incremental mart materialized as `TASTYBYTESDB.PUBLIC.DAILYSALESAGG`. The two `_insert_*_log` tasks wrote start/end markers to `TASTYBYTESDB.ETL_RESULTS.ETL_LOGS`, exactly the side-effect SnowConvert lifted from the original SSIS package.

Finally, Cortex Code shows the materialized mart:

```sql
SELECT * FROM TASTYBYTESDB.PUBLIC.DAILYSALESAGG ORDER BY TRUCKID, SALEDATE;
```

22 rows, one per `(TruckID, SaleDate)` pair from completed orders, aggregating `OrderCount`, `GrossRevenue`, `TotalTips`, and `ItemsSold` per truck-day. A sample of the output:


| TRUCKID | SALEDATE   | ORDERCOUNT | GROSSREVENUE | TOTALTIPS | ITEMSSOLD |
| ------- | ---------- | ---------- | ------------ | --------- | --------- |
| 1       | 2024-07-10 | 1          | 59.96        | 10.00     | 2         |
| 1       | 2024-08-15 | 1          | 16.99        | 2.50      | 1         |
| 1       | 2024-09-01 | 1          | 10.99        | 2.00      | 1         |
| 1       | 2024-09-12 | 1          | 55.96        | 8.00      | 2         |
| 2       | 2024-07-15 | 1          | 25.98        | 4.00      | 3         |
| 2       | 2024-09-15 | 1          | 4.50         | 1.00      | 1         |
| 3       | 2024-07-23 | 1          | 128.91       | 18.00     | 3         |
| …       | …          | …          | …            | …         | …         |
| 11      | 2024-10-05 | 1          | 12.99        | 2.00      | 1         |


Totals across the mart: 22 truck-day rows, 22 orders, $1,015.31 gross revenue, $139.50 tips, 39 items sold. Cross-checking against `TASTYBYTESDB.ETL_RESULTS.ETL_LOGS` shows the two markers `pkg_daily_sales_aggregate start` and `pkg_daily_sales_aggregate end` written one task apart, confirming the full task graph executed end-to-end.

At this point all four phases are complete:

```
✅ Setup       — project initialized, connections registered, local infra ready
✅ Phase 1     — 18 objects extracted, 18 files converted, assessment generated
✅ Phase 2     — 14 wave-1 objects deployed (3 schemas, 11 tables)
                 + view, function, and procedure deployed and validated (deploy/test/fix loop)
                 + 1 view hand-fixed (TOP 1 PERCENT rewritten as QUALIFY, EWI markers removed)
                 + 11 tables migrated locally
                 + table data validation skipped per kickoff prompt
                 + ETL stabilization skipped per kickoff prompt
✅ Phase 3     — row counts verified on Snowflake
✅ Phase 4     — dbt project deployed via `snow dbt deploy`,
                 4-task graph deployed with XSMALL_WH per task, executed end-to-end
```



## Conclusion And Resources

Congratulations! You've taken a Microsoft SQL Server database and an SSIS pipeline all the way from source extraction to a fully deployed, populated, and *running* workload in Snowflake — driven end-to-end by the Cortex Code CLI and its `snowflake-migration:migration` skill, plus the `snow dbt deploy` workflow for the SnowConvert-generated dbt project.

You started from a blank project, set up **local** data-migration infrastructure (no SPCS / compute pool needed), registered 18 SQL Server objects and 1 SSIS package, converted them with SnowConvert AI, generated a deployment plan with a classified SSIS assessment, deployed every in-scope database object using a deploy/test/fix loop (hand-fixing 1 conversion artifact — a view whose SQL Server `TOP 1 PERCENT` clause was rewritten as a Snowflake `QUALIFY ROW_NUMBER() ... <= CEIL(0.01 * COUNT(*) OVER ())` and whose unresolved SnowConvert EWI markers were removed), migrated the table data via the locally-run orchestrator + worker, and finally hand-patched and deployed both the SnowConvert-generated dbt project (`snow dbt deploy`) and the SnowConvert-generated Snowflake task graph (with `XSMALL_WH` per task), executing the full graph end-to-end on demand.

### What You Learned

- How to drive an end-to-end SQL Server + SSIS migration with **Cortex Code** and the bundled `snowflake-migration:migration` skill, using just five chat prompts.
- How **SnowConvert AI** extracts, converts, and deploys a SQL Server workload to Snowflake, and how to read its EWIs, FDMs, and PRFs.
- How to triage and hand-fix common SnowConvert outputs — rewriting an unsupported SQL Server `TOP 1 PERCENT` clause as a Snowflake `QUALIFY ROW_NUMBER()` window filter and removing unresolved `!!!RESOLVE EWI!!!` markers from a view, and customizing a step-based test YAML to validate a side-effect-only DML procedure.
- How to run the data-migration orchestrator and Data Exchange Worker **locally** for SQL Server → Snowflake table loads, without provisioning SPCS.
- How to use the seed → capture → validate testing framework against your source database — seeding cases from a query log — to verify the migrated function *and* procedure produce identical output and table side-effects to the SQL Server originals.
- How to deploy a SnowConvert-generated dbt project to Snowflake via `snow dbt deploy`, then point a Snowflake task graph at it with `EXECUTE DBT PROJECT`.

### Related Resources

- **Quickstart source code**: `[sfguide-scai-e2e-ssis-migration](https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration)` — DDLs, sample data, the SSIS package, and the initial Snowflake setup used throughout this guide.
- [SnowConvert AI CLI documentation](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README) — reference for `scai code extract`, `scai code convert`, `scai code deploy`, `scai data migrate`, `scai test seed/capture/validate`.
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) — install and usage guide for the CLI that hosts the migration skills.
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction) — used here for the connection config that both `scai` and `snow` share, and for `snow dbt deploy`.
- [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects/about-dbt-projects) — target pattern for the replatformed SSIS data flows produced by `migrate-etl-package`.
- [Snowflake tasks](https://docs.snowflake.com/en/user-guide/tasks-intro) — background for the four-task graph with `EXECUTE DBT PROJECT` deployed in Phase 4.
- [Snowflake Scripting reference](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/index) — background for the procedure rewrites.

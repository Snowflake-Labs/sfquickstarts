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

Through this guide you will learn how to do an end-to-end migration of a Microsoft SQL Server environment with SSIS to Snowflake using tools like SnowConvert AI, Cortex Code CLI, and the Snowflake CLI. This guide walks you through project setup, extracting your source DDLs, converting them, leveraging AI to fix remaining issues in your converted code, deploying objects, migrating and validating historical data, and finally replatforming your SSIS ETL pipelines to Snowflake SQL and dbt Projects.

### Prerequisites

- Familiarity with Snowflake SQL.
- Familiarity with Microsoft SQL Server and SSIS.
- Familiarity with dbt Projects in Snowflake and tasks.

### What You'll Learn

By the end of this guide, you will learn to work with:

- The SnowConvert AI CLI to perform end-to-end migrations of SQL Server (code conversion, data migration, data validation, and ETL replatform).
- The Cortex Code CLI and its bundled `snowflake-migration:migration` skill for orchestrating every phase of the migration journey.

### What You'll Need

- A SQL Server database where you have full read and write permissions for creating DDLs and running DMLs.
- A Snowflake account with the `ACCOUNTADMIN` role.
- An SPCS-enabled Snowflake account (required for cloud data migration and validation).
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction) installed.
- [SnowConvert AI CLI](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README) installed.
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed.
- A text editor (we recommend [Visual Studio Code](https://code.visualstudio.com/)).

### What You'll Build

An end-to-end migration of a SQL Server database and SSIS workflows to Snowflake, including code conversion, code deployment with hand-fixes, data migration, and data validation.

## Project Setup

### Clone the Quickstart Repository

All of the source scripts, SSIS package, and SQL used in this quickstart live in the [`sfguide-scai-e2e-ssis-migration`](https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration) repository. Clone it to your local machine before continuing:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration.git
cd sfguide-scai-e2e-ssis-migration
```

The repository contains:

- `sourcedb/00_ddl.sql` and `sourcedb/01_data.sql` — SQL Server DDL and sample data for the TastyBytes database.
- `snowflake/init.sql` — initial Snowflake database and schemas.
- `etl/ssis_snowflake_demo.dtsx` — the SSIS package you will migrate to Snowflake.

Later steps reference these paths (for example, when Cortex Code asks for the filesystem path to your SSIS folder, you will point it at this repository's `etl/` directory).

### SQL Server DDL and Data

1. In the SQL Server instance you will be using for this quickstart, run the `sourcedb/00_ddl.sql` script to create the database, schema, and DDLs that we will be converting.
2. Once the DDLs have been deployed successfully, run the `sourcedb/01_data.sql` script to insert sample data into the tables of the TastyBytes database.

### Snowflake Account

1. In your Snowflake account, run the `snowflake/init.sql` script to create the initial database and schemas where our DDLs and data will be deployed.
2. Create a dedicated SPCS compute pool that the cloud data-migration orchestrator will use:

   ```sql
   CREATE COMPUTE POOL IF NOT EXISTS TASTYBYTES_MIG_POOL
     MIN_NODES = 1
     MAX_NODES = 2
     INSTANCE_FAMILY = CPU_X64_S
     AUTO_RESUME = TRUE
     AUTO_SUSPEND_SECS = 600
     COMMENT = 'Compute pool for TastyBytes SQL Server -> Snowflake data migration';
   ```

### Snowflake Connection

To enable the Snowflake CLI to run against our Snowflake account, we need to add the connection details to the `config.toml` file used by the Snowflake CLI and the SnowConvert AI CLI. Follow the steps in this [guide](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-cli) to set up your `config.toml` file with your connection details.

You can run the command below to test if the CLI can connect to your account.

```bash
snow connection test --connection <YOUR_SNOWFLAKE_CONNECTION_NAME>
```

In this quickstart we use a Snowflake connection named `migrations_sc` configured with warehouse `xsmall_wh`, database `TASTYBYTESDB`, schema `tastybytes`, and role `ACCOUNTADMIN`.

### SnowConvert AI Source Connection

Run the following command in your terminal to provide your SQL Server connection information to the SnowConvert AI CLI so it can later convert your code and your data to Snowflake.

```bash
scai connection add-sql-server
```

Once your connection has been added, you can test it using the command below:

```bash
scai connection test -l sqlserver -s <YOUR_CONNECTION_NAME>
```

You should see a message like this in your terminal.

```
╭─────────────────┬─────────────────────────────────────╮
│ Key             │ Value                               │
├─────────────────┼─────────────────────────────────────┤
│ Connection name │ tasty-bytes-db                      │
│                 │                                     │
│ Credentials     │ {                                   │
│                 │   "user": "sa",                     │
│                 │   "server_url": "127.0.0.1",        │
│                 │   "database": "TastyBytesDB",       │
│                 │   "connection_timeout": 200,        │
│                 │   "port": "1433",                   │
│                 │   "trust_server_certificate": true, │
│                 │   "encrypt": false,                 │
│                 │   "auth_method": "standard",        │
│                 │   "password": "***"                 │
│                 │ }                                   │
│                 │                                     │
│ Status          │ Success                             │
╰─────────────────┴─────────────────────────────────────╯
```

We use a connection named `tasty-bytes-db` throughout this quickstart.

## Initialize the Migration Project with Cortex Code

Rather than running each `scai` command manually, we will drive the migration from the Cortex Code CLI. Cortex Code ships with a `snowflake-migration:migration` skill that orchestrates project initialization, source extraction, conversion, assessment, deployment, data migration, and data validation through a guided conversation.

The sections that follow walk through the exact prompts the skill will ask and the answers we selected for this quickstart, in the order you will see them.

### Start Cortex Code

From the directory where you want to host the migration project (for example, an existing `sfquickstarts/` folder), launch Cortex Code:

```bash
$ cortex
```

Inside the Cortex Code session, tell the assistant what you want to do:

```
lets start migrating my sql server workload to snowflake
```

The assistant will recognize the task and invoke the `snowflake-migration:migration` skill, which prints:

> **Welcome to the Snowflake Migrations plugin.** Let me get started by configuring your session.

It will then call `configure` with the current directory and call `migration_status` to detect that no project exists yet.

### Step 1 — Choose the Project Directory

If your current directory is not empty, the skill will offer to create a subdirectory for the migration project. For this quickstart, pick **`sfquickstarts/sqlserver-migration`** so all migration artifacts (source, converted SQL, reports, waves, assessment) live under `./sqlserver-migration/`.

> The current directory `/Users/<you>/projects/sfquickstarts` isn't empty. Where would you like to initialize the SQL Server migration project?
>
> 1. **`sqlserver-migration` (subdir)** ← select this
> 2. `mssql-to-snowflake` (subdir)

Behind the scenes the skill calls `configure(project_dir=..., source_language='sqlserver')` which scaffolds the `.scai/`, `source/`, and `snowflake/` folders and prints a **Phase 1 / Phase 2** overview of the migration plan.

### Step 2 — Confirm Entry Mode

Cortex Code then asks whether this is a fresh migration or whether you already have pre-converted Snowflake SQL:

> Are you starting a new migration, or do you already have source SQL **and** pre-converted Snowflake SQL?
>
> 1. **Starting fresh** ← select this
> 2. Existing migration

It also asks which Snowflake connection to use:

> Should we use your active Snowflake connection (`migrations_sc`) for this migration?
>
> 1. **Use migrations_sc** ← select this

### Step 3 — Set Up the SQL Server Source Connection

Cortex Code then routes you into the connection sub-skill:

> Will you need to connect to your SQL Server source system?
>
> 1. **Yes — set up connection** ← select this
> 2. No — skip for now

It runs `scai connection list -l sqlserver` and presents the existing connections. Pick the one we tested above:

> Which SQL Server connection would you like to use?
>
> 1. `adventureworks`
> 2. `sqlserver_northwind`
> 3. **`tasty-bytes-db`** ← select this
> 4. `tasybytesdbaws`
> 5. Create new connection

The skill calls `configure(source_connection='tasty-bytes-db')` to persist the choice.

### Step 4 — Save Project Defaults

Next, Cortex Code asks how to store project-level defaults:

> How would you like to configure project defaults?
>
> 1. Shared project defaults
> 2. **Local project defaults** ← select this
> 3. Skip for now

Pick **Local project defaults** so the values land in `.scai/config/project.local.yml` (gitignored). Cortex Code then asks for the four Snowflake-side values:

> Do you want to specify Snowflake target database/schema/warehouse/role now, or just save the connection names?
>
> 1. **Specify target database** ← select this
> 2. Save connections only

Provide the values for this quickstart:

| Question        | Answer            |
| --------------- | ----------------- |
| Target database | `TASTYBYTESDB`    |
| Target schema   | `tastybytes`      |
| Warehouse       | `xsmall_wh`       |
| Role            | `ACCOUNTADMIN`    |

Cortex Code runs:

```bash
scai project defaults set \
  -s tasty-bytes-db -c migrations_sc \
  --warehouse xsmall_wh --database TASTYBYTESDB \
  --schema tastybytes --role ACCOUNTADMIN
```

Both connections are tested before the values are written. You should see a `Project defaults set` confirmation.

### Step 5 — Configure Data Migration and Validation Infrastructure

Cortex Code then asks whether to configure the shared data-migration infrastructure now:

> Will you also need to migrate data from SQL Server into Snowflake?
>
> 1. **Yes — migrate data + validate** ← select this
> 2. Yes — migrate data only
> 3. No — skip

Pick **Yes — migrate data + validate** so the skill provisions the SPCS orchestrator + worker config up front. It runs `SHOW COMPUTE POOLS` against your account and asks which pool to use:

> Which compute pool should we use for the data migration orchestrator?
>
> 1. **`TASTYBYTES_MIG_POOL`** ← select this
> 2. `SYSTEM_COMPUTE_POOL_CPU`

The skill calls `configure(compute_pool='TASTYBYTES_MIG_POOL')`. This persists the value to `.scai/settings/cloud-migration.yaml` and auto-generates `.scai/settings/DataExchangeWorkerConfig.toml` with placeholder values. Cortex Code then walks you through filling those placeholders by asking three questions:

| Question                | Answer for this quickstart |
| ----------------------- | -------------------------- |
| Source database name    | `TastyBytesDB`             |
| Source schema           | `tastybytes`               |
| Source host             | `127.0.0.1`                |

It rewrites `.scai/settings/DataExchangeWorkerConfig.toml` with the credentials from the SQL Server connection profile so the worker can read from the source. The result looks like:

```toml
[connections.source.sqlserver]
username = "sa"
password = "Password2024"
database = "TastyBytesDB"
host = "127.0.0.1"
port = 1433

[connections.target.snowflake_connection_name]
connection_name = "migrations_sc"
```

Finally, the migration-approach prompts:

> What migration type would you like for the data migration?
>
> 1. Preliminary
> 2. Incremental
> 3. **Full** ← select this

> What target table type?
>
> 1. **Native** ← select this
> 2. Iceberg

The workflow config (`.scai/settings/workflow-config.yaml`) is generated later in the flow, after the code registry exists.

## Extract Source Code from SQL Server

With the project initialized, the skill loads the `register-code-units` sub-skill and asks:

> How would you like to add source code?
>
> 1. **Extract from database** ← select this
> 2. Add local files

It first verifies the connection by running `scai connection test -l sqlserver -s tasty-bytes-db` (you should see `Status: Success`), then asks what to extract:

> What would you like to extract from TastyBytesDB?
>
> 1. **All objects** ← select this
> 2. Schema: tastybytes
> 3. Tables + Views only

Under the hood, Cortex Code runs:

```bash
scai code extract -s tasty-bytes-db
```

The extraction discovers and writes 32 SQL files to `source/`, broken down as:

| Type      | Count |
| --------- | ----- |
| Table     | 11    |
| Procedure | 7     |
| View      | 5     |
| Function  | 5     |
| Schema    | 3     |
| Database  | 1     |

SQL files land under `source/tastybytesdb/tastybytes/` split by object type (`table/`, `view/`, `function/`, `procedure/`).

## Convert the Source Code to Snowflake SQL

Once registration is complete, Cortex Code loads the `convert` sub-skill and asks whether you have ETL code to include:

> Do you have any ETL code (SSIS or Informatica) to include in the conversion?
>
> 1. **Yes — SSIS or Informatica** ← select this
> 2. No — SQL only

> Which ETL platform?
>
> 1. **SSIS** ← select this
> 2. Informatica

> What is the filesystem path to your SSIS packages?

Provide the absolute path to the directory that contains your `.dtsx` files. For this quickstart that's the cloned repo's `etl/` directory:

```
/Users/<you>/projects/sfguide-scai-e2e-ssis-migration/etl
```

Cortex Code then runs:

```bash
scai code convert \
  --etl-replatform-sources-path /Users/<you>/projects/sfguide-scai-e2e-ssis-migration/etl \
  --show-ewis
```

A successful conversion reports:

- **Files processed:** 32
- **Code units converted:** 654 LOC
- **Total issues:** 90 (15 EWIs across 6 unique codes, 45 FDMs, 30 PRFs)
- **Execution time:** ~14s

Converted artifacts land in:

- `snowflake/tastybytesdb/tastybytes/` — converted tables, views, functions, procedures.
- `snowflake/_etl/ssis_snowflake_demo/` — replatformed SSIS package (Snowflake tasks + dbt models).
- `reports/SnowConvert/` — CSV/JSON conversion reports.

### Review Conversion Issues

SnowConvert annotates each converted file with three classes of findings:

- **EWIs (Early Warning Issues)** — items that need attention before deployment. Severity levels are Critical, High, Medium, and Low.
- **FDMs (Functional Differences)** — cases where Snowflake behavior differs from SQL Server and you should confirm the new behavior is acceptable.
- **PRFs (Performance Remarks)** — optimization suggestions.

For this quickstart, the conversion produced:

| Code             | Description                                          | Count | Severity |
| ---------------- | ---------------------------------------------------- | ----- | -------- |
| `SSC-EWI-TS0082` | CROSS APPLY converted to LEFT OUTER JOIN             | 2     | Critical |
| `SSC-EWI-0108`   | Subquery matches a pattern considered invalid        | 6     | High     |
| `SSC-EWI-0021`   | Syntax not supported in Snowflake                    | 2     | Medium   |
| `SSC-EWI-TS0035` | Uninitialized cursor declared                        | 2     | Medium   |
| `SSC-EWI-TS0036` | Snowflake Scripting only supports local cursors      | 2     | Medium   |
| `SSC-EWI-TS0077` | Collation Not Supported                              | 1     | Low      |

The dominant FDMs are `SSC-FDM-TS0002` (collation values × 27) and `SSC-FDM-TS0029` (commented-out `SET NOCOUNT`, × 7). The dominant PRF is `SSC-PRF-0002` (case-insensitive columns × 27).

The SSIS replatforming summary shows **1 package processed**, **0 EWIs**, and **2 FDMs** (both `SSC-FDM-0007` referencing the missing `etl_results.etl_logs` table).

## Run the Migration Assessment

With conversion complete, Cortex Code offers to run the migration assessment. The skill first tells you it can run all five analyses, then asks whether you want the full run or a subset:

> Proceed with the full assessment, or pick a subset?
>
> 1. Run all 5 — proceed
> 2. **Subset — let me choose** ← select this

> Which assessments would you like to run? (multi-select)
>
> 1. **Waves** ← select this
> 2. Object exclusion
> 3. Dynamic SQL
> 4. **SSIS / ETL** ← select this
> 5. **HTML report** ← select this

For this quickstart we skip Object Exclusion and Dynamic SQL because our workload has no temp/staging objects and no dynamic SQL.

### Dependency Waves

Cortex Code calls `scai assessment waves`, which produces `assessment/waves_analysis_<timestamp>.json`. With the default min/max sizes (40–80) and a small workload of 40 graph nodes, the entire workload fits in a single deployment wave with **0 cycles**.

To produce the registry-mode waves bundle that the multi-tab HTML report consumes, the skill also runs the underlying script:

```bash
uv run --project <ASSESSMENT_SKILL_DIR> \
  python <ASSESSMENT_SKILL_DIR>/waves-generator/scripts/analyze_dependencies_registry.py \
  --registry-dir ./sqlserver-migration/registry \
  --reports-dir ./sqlserver-migration/reports/SnowConvert \
  --output ./sqlserver-migration/assessment/dependency_analysis
```

This emits `dependency_analysis_<timestamp>/` with `partition_membership.csv`, `deployment_partitions.json`, `wave_deployment_order.json`, `missing_dependencies.json`, and several human-readable reports. After merging small partitions, the result is **2 deployment partitions** covering 28 in-scope objects, with 5 referenced-but-out-of-scope objects flagged.

### SSIS Assessment

For the single SSIS package, Cortex Code runs `scai_assessment_analyzer` over `ETL.Elements.*.csv`, `ETL.Issues.*.csv`, and the source `.dtsx` file to produce `assessment/ssis/etl_assessment_analysis.json`. Then it writes an HTML executive summary at `assessment/ssis/ai_ssis_summary.html` and registers it back into the JSON via the `ai-summary` command.

For `ssis_snowflake_demo.dtsx` the assessment concludes:

- **Classification:** Data Transformation (two linear `OLEDBSource → DerivedColumn → OLEDBDestination` pipelines, no external systems, no script tasks).
- **Components:** 10 total — 2 ExecuteSQLTask, 2 OLEDBSource, 2 DerivedColumn, 2 OLEDBDestination, 2 Pipeline.
- **Complexity:** **Very Easy** — 100% conversion success rate, 0 EWIs.
- **Only functional gap:** `SSC-FDM-0007` × 2 — the `etl_results.etl_logs` table referenced by the start/end logging tasks does not exist in the extracted source and must be created in Snowflake before the converted tasks can run.

### Multi-Tab Assessment Report

Finally, the assessment produces a consolidated HTML report:

```bash
uv run --project <ASSESSMENT_SKILL_DIR> \
  python <ASSESSMENT_SKILL_DIR>/scripts/generate_multi_report.py \
  --waves-analysis-dir ./sqlserver-migration/assessment/dependency_analysis/dependency_analysis_<ts> \
  --registry-dir ./sqlserver-migration/registry \
  --snowconvert-reports-dir ./sqlserver-migration/reports/SnowConvert \
  --ssis-json ./sqlserver-migration/assessment/ssis/etl_assessment_analysis.json \
  --output ./sqlserver-migration/assessment/multi_report.html
```

Open it with:

```bash
open ./sqlserver-migration/assessment/multi_report.html
```

The report (~420 KB) includes tabs for **Overview**, **Waves**, **SSIS**, per-package detail pages, and a **Missing Objects** view for cross-scope references.

At this point, the setup phase is complete:

- Connected to SQL Server (`tasty-bytes-db`) and Snowflake (`migrations_sc`).
- Project initialized at `./sqlserver-migration` with local defaults targeting `TASTYBYTESDB.tastybytes` on `xsmall_wh`.
- SPCS compute pool `TASTYBYTES_MIG_POOL` registered; worker config written.
- 32 SQL Server objects extracted (11 tables, 7 procedures, 5 views, 5 functions, 3 schemas, 1 database) and 1 SSIS package imported.
- 32 files converted to Snowflake SQL; 15 EWIs, 45 FDMs, 30 PRFs catalogued.
- 2 deployment partitions generated.
- SSIS package classified as Data Transformation, Very Easy complexity.
- Multi-tab assessment HTML report produced.

## Phase 2 — Deploy Objects to Snowflake

Cortex Code asks how to proceed:

> What would you like to do next?
>
> 1. **Start migrating objects** ← select this
> 2. Review the report first
> 3. Set up data validation
> 4. Fix critical EWIs first

The migrate-objects skill normally walks each object through a deploy → test → fix loop using a baseline-capture validation framework. For this quickstart we want to keep things lean and skip the testing phase, so we override the default flow:

```
lets skip the testing phase of the objects, lets just deploy and fix
```

Cortex Code uses `scai code deploy --all` to push every converted object in dependency order, with `--continue-on-error` so partial failures don't block the rest of the deployment.

### Run the Initial Deployment

```bash
scai code deploy --all -c migrations_sc -d TASTYBYTESDB --continue-on-error
```

The first pass succeeds for **28 of 35 objects** (database, schemas, all 11 tables, 5 views, 2 of 5 functions, 4 of 7 procedures, plus 3 helper UDFs in `PUBLIC`), and fails for the remaining **7**:

| Object                          | Type      | Root cause                                                          |
| ------------------------------- | --------- | ------------------------------------------------------------------- |
| `fn_FormatPhoneNumber`          | Function  | `!!!RESOLVE EWI!!!` markers + nested UDF call inside SQL UDF        |
| `fn_ParseTruckConfigJSON`       | Function  | `!!!RESOLVE EWI!!!` marker + parameter / column collision           |
| `fn_CalculateTax`               | Function  | Self-referencing `CTE2` (broken recursion), missing `TAXAMOUNT`     |
| `sp_ReconcileShifts`            | Procedure | 6× `!!!RESOLVE EWI!!!` markers around correlated subqueries         |
| `sp_ProcessDailyOrders`         | Procedure | Orphan uninitialized `AUDITCURSOR CURSOR;` + EWI markers            |
| `sp_MergeCustomerData`          | Procedure | Orphan `LOGCURSOR` + cursor against a not-yet-existing staging table |
| `vw_TopSellingItems`            | View      | `SELECT TOP 5` + correlated reference inside a regular `LEFT JOIN`  |

When asked how to fix the failures, choose **One at a time** so you can review each rewrite:

> How would you like to fix the 7 failed deployments?
>
> 1. Auto-fix all 7
> 2. **One at a time** ← select this
> 3. Prioritize critical

### Fix 1/7 — `fn_FormatPhoneNumber`

The converted file uses Snowflake Scripting (`DECLARE`, `WHILE LOOP`) inside a `LANGUAGE SQL` UDF and calls the helper `PUBLIC.PATINDEX_UDF` from inside the UDF body — both invalid. Rewrite as a pure SQL UDF using `REGEXP_REPLACE`:

```sql
CREATE OR REPLACE FUNCTION TastyBytes.fn_FormatPhoneNumber(RAWPHONE STRING)
RETURNS VARCHAR(20)
LANGUAGE SQL
AS
$$
    CASE
        WHEN LENGTH(REGEXP_REPLACE(RAWPHONE, '[^0-9]', '')) = 10 THEN
            '(' || SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 1, 3) || ') ' ||
            SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 4, 3) || '-' ||
            SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 7, 4)
        WHEN LENGTH(REGEXP_REPLACE(RAWPHONE, '[^0-9]', '')) = 11 THEN
            '+' || SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 1, 1) || ' (' ||
            SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 2, 3) || ') ' ||
            SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 5, 3) || '-' ||
            SUBSTR(REGEXP_REPLACE(RAWPHONE, '[^0-9]', ''), 8, 4)
        ELSE REGEXP_REPLACE(RAWPHONE, '[^0-9]', '')
    END
$$;
```

Smoke-test:

```sql
SELECT TastyBytes.fn_FormatPhoneNumber('555-123-4567');     -- (555) 123-4567
SELECT TastyBytes.fn_FormatPhoneNumber('1-555-123-4567');   -- +1 (555) 123-4567
```

### Fix 2/7 — `fn_ParseTruckConfigJSON`

The converted UDF uses `OPENJSON_UDF` as a table function inside a `LEFT OUTER JOIN`, has the unsupported `!!!RESOLVE EWI!!!` marker for the original `CROSS APPLY`, and the parameter `TRUCKID` collides with the column name `ft.TruckID`. Replace with a native `LATERAL FLATTEN` and rename the parameter:

```sql
CREATE OR REPLACE FUNCTION TastyBytes.fn_ParseTruckConfigJSON(P_TRUCKID INT)
RETURNS INT
LANGUAGE SQL
AS
$$
    SELECT NVL(COUNT(*), 0)
    FROM TastyBytes.FoodTruck ft,
         LATERAL FLATTEN(input => PARSE_JSON(ft.TruckConfig):Equipment) e
    WHERE ft.TruckID = P_TRUCKID
      AND ft.TruckConfig IS NOT NULL
      AND e.value:IsOperational::BOOLEAN = TRUE
$$;
```

### Fix 3/7 — `fn_CalculateTax`

SnowConvert produced a chain of CTEs where `CTE2` self-references itself (invalid) and the final `SELECT TAXAMOUNT FROM CTE4` references a column that doesn't exist in `CTE4`. Collapse to the original intent — `amount × (taxrate / 100)`:

```sql
CREATE OR REPLACE FUNCTION TastyBytes.fn_CalculateTax(AMOUNT NUMBER(38, 4), P_COUNTRYID INT)
RETURNS NUMBER(38, 4)
LANGUAGE SQL
AS
$$
    SELECT AMOUNT * NVL((
        SELECT TaxRate / 100.0
        FROM TastyBytes.Country
        WHERE CountryID = P_COUNTRYID
    ), 0)
$$;
```

### Fix 4/7 — `sp_ReconcileShifts`

The procedure is structurally correct — only the `!!!RESOLVE EWI!!! /*** SSC-EWI-0108 ... ***/!!!` markers around six correlated subqueries block compilation. Strip those markers (a regex find-and-replace works) and redeploy. The cleaned procedure compiles and `CALL TastyBytes.sp_ReconcileShifts(CURRENT_DATE())` returns the expected (empty) result set against the still-empty tables.

### Fix 5/7 — `sp_ProcessDailyOrders`

In addition to EWI markers, the converted SQL declares `AUDITCURSOR CURSOR;` without a `FOR` clause — invalid in Snowflake Scripting and never used. Drop the orphan declaration, remove the EWI markers, and clean a stray semicolon left over from the commented-out `DEALLOCATE`. The `OrderCursor FOR LOOP` body is preserved.

### Fix 6/7 — `sp_MergeCustomerData`

Same pattern as 5/7 plus an extra wrinkle: the cursor selects `FROM TastyBytes.CustomerStaging`, a table that the source procedure creates lazily via `OBJECT_ID_UDF`. Snowflake Scripting validates the cursor's source table at compile time, so we pre-create the staging table and remove the orphan `LOGCURSOR`:

```sql
CREATE TABLE IF NOT EXISTS TastyBytes.CustomerStaging (
    Email VARCHAR(255) NOT NULL,
    FirstName VARCHAR(100),
    LastName VARCHAR(100),
    PhoneNumber VARCHAR(20),
    PreferredCityID INT
);
```

Then deploy the cleaned procedure.

### Fix 7/7 — `vw_TopSellingItems`

The converted view has three problems: a `!!!RESOLVE EWI!!!` marker, `SELECT TOP 5` (SQL Server only), and a correlated `WHERE oh.TruckID = ft.TruckID` reference inside a regular `LEFT OUTER JOIN` (which doesn't work without `LATERAL`). The cleanest Snowflake idiom is to pre-aggregate per truck and use `QUALIFY ROW_NUMBER()` to keep top 5 per truck:

```sql
CREATE OR REPLACE VIEW TastyBytes.vw_TopSellingItems AS
WITH item_sales AS (
    SELECT
        oh.TruckID,
        mi.MenuItemID,
        mi.ItemName,
        SUM(od.Quantity)                AS TotalQuantitySold,
        SUM(od.Quantity * od.UnitPrice) AS TotalRevenue
    FROM TastyBytes.OrderDetail od
    INNER JOIN TastyBytes.OrderHeader oh ON od.OrderID = oh.OrderID
    INNER JOIN TastyBytes.MenuItem mi    ON od.MenuItemID = mi.MenuItemID
    WHERE oh.OrderStatus = 'Completed'
    GROUP BY oh.TruckID, mi.MenuItemID, mi.ItemName
)
SELECT
    ft.TruckID, ft.TruckName,
    s.MenuItemID, s.ItemName,
    s.TotalQuantitySold, s.TotalRevenue
FROM TastyBytes.FoodTruck ft
LEFT JOIN item_sales s ON s.TruckID = ft.TruckID
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ft.TruckID
    ORDER BY s.TotalQuantitySold DESC NULLS LAST
) <= 5;
```

### Verify the Code Deployment

A quick sanity check against `INFORMATION_SCHEMA` confirms everything landed:

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
| VIEW       | 5   |
| FUNCTION   | 5   |
| PROCEDURE  | 7   |

All 28 in-scope database objects (plus the `etl_results.etl_logs` helper table and the 3 `PUBLIC` UDF helpers) are now deployed.

## Phase 3 — Migrate Data from SQL Server to Snowflake

When prompted, tell Cortex Code:

```
Migrate data
```

The skill generates the cloud-migration workflow config from the registry now that all tables are registered:

```bash
scai data generate-cloud-migration-config -o .scai/settings/workflow-config.yaml
```

This writes `.scai/settings/workflow-config.yaml` covering all 11 tables (10 in `TastyBytes` + 1 in `etl_results`) with `synchronization.strategy = none` and `extraction.strategy = regular` — matching the **Full / Native** approach we picked in Step 5.

Cortex Code then calls the `migrate_data` MCP tool, which manages both the SPCS orchestrator service and the local Data Exchange Worker for you. Internally it runs:

```bash
scai cloud-migrate
```

The tool returns a `job_id` immediately and the migration proceeds asynchronously. You can poll with:

```bash
scai data cloud-migrate-status
```

For TastyBytes the migration completes in roughly 5 minutes:

```
Workflow:               DATA_MIGRATION_WORKFLOW_2026_05_12_13_36_23
Preprocessing tables:   11/11 (100%)
Partition Progress:     11/11 partitions
■ Pending: 0  ■ Extracting: 0  ■ Loading: 0  ■ Loaded: 11
Overall Progress:       100% complete
```

Verify in Snowflake with a row-count query:

```sql
SELECT 'Country' AS tbl, COUNT(*) AS row_cnt FROM TASTYBYTESDB.TASTYBYTES.Country
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

Expected (185 rows total):

| TBL           | ROW_CNT |
| ------------- | ------- |
| City          | 12      |
| Country       | 8       |
| Customer      | 15      |
| EmployeeShift | 20      |
| FoodTruck     | 12      |
| Inventory     | 16      |
| Menu          | 12      |
| MenuItem      | 26      |
| OrderDetail   | 39      |
| OrderHeader   | 25      |

## Phase 4 — Validate Data Between SQL Server and Snowflake

Tell Cortex Code:

```
now lets do data validation
```

It loads the data-validation sub-skill and asks you to scope the run:

> Which tables should be validated?
>
> 1. All deployed tables
> 2. **TastyBytes schema only** ← select this

> Which validation checks should be enabled? (multi-select)
>
> 1. **Schema validation** ← select
> 2. **Metrics validation** ← select
> 3. Row-level validation

> Failure handling?
>
> 1. **Continue on failure** ← select this
> 2. Stop on first failure

Cortex Code generates the validation config from the registry:

```bash
scai data generate-cloud-validation-config \
  --where "source.schema = 'TastyBytes'" \
  -o .scai/settings/data-validation-config.json
```

This emits a JSON file targeting the 10 `TastyBytes`-schema tables with `schema_validation`, `metrics_validation`, and `continue_on_failure` set to `true` and `row_validation` set to `false`.

Before kicking off the run, set the default SQL Server connection so the orchestrator's preflight check passes (otherwise you'll see `DMG0015: No default source connection found`):

```bash
scai connection set-default -l sqlserver -s tasty-bytes-db
```

Verify the orchestrator service is `READY`:

```sql
SELECT SYSTEM$GET_SERVICE_STATUS('SNOWCONVERT_AI.DATA_MIGRATION.DATA_MIGRATION_SERVICE');
```

Then call the `validate_data` MCP tool through Cortex Code — internally it runs `scai cloud-validate` with the local Data Exchange Worker and returns a `job_id`. Poll the status until it finishes:

```
Workflow:      DATA_VALIDATION_WORKFLOW_2026_05_12_13_46_37
Status:        Finished
Total Tables:  10
Validated:     10
Failed:        0
```

### Inspect the Validation Results

Schema validation results live in `SNOWCONVERT_AI.DATA_VALIDATION.SCHEMA_VALIDATION_RESULTS`. First, confirm row-counts match:

```sql
SELECT TABLE_NAME, EVALUATION_CRITERIA, SOURCE_VALUE, SNOWFLAKE_VALUE, STATUS
FROM SNOWCONVERT_AI.DATA_VALIDATION.SCHEMA_VALIDATION_RESULTS
WHERE WORKFLOW_ID = (SELECT MAX(WORKFLOW_ID) FROM SNOWCONVERT_AI.DATA_VALIDATION.SCHEMA_VALIDATION_RESULTS)
  AND EVALUATION_CRITERIA = 'ROW_COUNT'
ORDER BY TABLE_NAME;
```

Every row returns `STATUS = 'SUCCESS'` and matching `SOURCE_VALUE` / `SNOWFLAKE_VALUE` — all 10 tables match exactly (185 rows total).

Then look at the column-level checks that did *not* match:

```sql
SELECT EVALUATION_CRITERIA, COUNT(*) AS fail_count
FROM SNOWCONVERT_AI.DATA_VALIDATION.SCHEMA_VALIDATION_RESULTS
WHERE WORKFLOW_ID = (SELECT MAX(WORKFLOW_ID) FROM SNOWCONVERT_AI.DATA_VALIDATION.SCHEMA_VALIDATION_RESULTS)
  AND STATUS != 'SUCCESS'
GROUP BY EVALUATION_CRITERIA
ORDER BY fail_count DESC;
```

For TastyBytes you'll see:

| EVALUATION_CRITERIA      | FAIL_COUNT |
| ------------------------ | ---------- |
| `NUMERIC_PRECISION`      | 34         |
| `CHARACTER_MAXIMUM_LENGTH` | 20       |

These are **expected, non-blocking** type-widening differences from the SQL Server → Snowflake mapping:

- SQL Server `INT` (precision 10) becomes Snowflake `NUMBER(38, 0)` (precision 38). Snowflake stores all integers as 38-digit `NUMBER` regardless of the declared precision, so this difference has no storage cost or semantic impact.
- SQL Server `NVARCHAR(N)` becomes Snowflake `VARCHAR(2N)`. Every comment in the result set reads `Source value is lower than target value`, meaning the target type is strictly more permissive than the source.

No data was lost: every row was preserved and every column can hold the source values.

At this point all four phases are complete:

```
✅ Setup       — project initialized, connections registered, infra configured
✅ Phase 1     — 32 objects extracted, 32 files converted, assessment generated
✅ Phase 2     — 28 in-scope objects deployed (7 hand-fixed)
✅ Phase 3     — 11 tables, 185 rows migrated to Snowflake
✅ Phase 4     — schema + metrics validation: 0 failures, 54 expected type-widening differences
⬚ SSIS deploy — ssis_snowflake_demo dbt + Snowflake Task ready under snowflake/_etl/
```

<!-- ------------------------ -->

## Conclusion And Resources

Congratulations! You've taken a Microsoft SQL Server database all the way from source extraction to a fully deployed, populated, and validated schema in Snowflake, driven end-to-end by the Cortex Code CLI and its `snowflake-migration:migration` skill. You started from a blank project, configured the SPCS data-migration infrastructure, registered 32 SQL Server objects and 1 SSIS package, converted them with SnowConvert AI, generated a deployment plan with a classified SSIS assessment, deployed all 28 in-scope database objects (including hand-fixing 7 conversion artifacts), migrated 185 rows of data via the cloud orchestrator, and validated schema + metrics parity against the source.

### What You Learned

- How to drive a full migration from the **Cortex Code CLI** via the bundled `snowflake-migration:migration` skill — including the interactive prompts for project setup, source-connection reuse, SPCS infrastructure, code conversion, deployment, data migration, and data validation.
- How to use the **SnowConvert AI CLI** under the hood to initialize a project, extract source DDL/code from a live SQL Server instance, import SSIS `.dtsx` packages, convert the full workload, and deploy converted code with `scai code deploy --all`.
- How to read the three classes of SnowConvert findings — **EWIs** (conversion gaps), **FDMs** (functional differences), and **PRFs** (performance remarks) — and triage them before deployment.
- How to generate and interpret a **dependency-wave deployment plan** plus a multi-tab HTML assessment report that includes a per-package SSIS classification.
- How to recognize and fix the most common patterns that still require hand-editing when SnowConvert can't fully translate T-SQL:
  - `CROSS APPLY` → `LATERAL FLATTEN` for JSON projection.
  - `SELECT TOP N` + correlated subquery → pre-aggregated CTE + `QUALIFY ROW_NUMBER()` for "top N per group".
  - SnowConvert's `!!!RESOLVE EWI!!! /*** ... ***/!!!` inline markers, and which EWIs (such as `SSC-EWI-TS0036` "local cursors") are informational versus structural.
  - Multi-statement T-SQL TVFs and self-referencing CTE artefacts collapsed into idiomatic Snowflake SQL UDFs (`REGEXP_REPLACE`, single-`SELECT` math, `LATERAL FLATTEN`).
  - Orphan uninitialized `CURSOR` declarations and parameter / column name collisions inside Snowflake Scripting procedures and UDFs.
- How to provision an **SPCS compute pool** and a **Data Exchange Worker config** to run the cloud data-migration orchestrator, then trigger `migrate_data` to load full tables from SQL Server into Snowflake.
- How to run schema- and metrics-level **cloud data validation** between SQL Server and Snowflake, query `SNOWCONVERT_AI.DATA_VALIDATION` for results, and distinguish real data drift from expected type-widening differences (`INT` → `NUMBER(38)`, `NVARCHAR(N)` → `VARCHAR(2N)`).

### Related Resources

- **Quickstart source code**: [`sfguide-scai-e2e-ssis-migration`](https://github.com/Snowflake-Labs/sfguide-scai-e2e-ssis-migration) — DDLs, sample data, SSIS package, and the initial Snowflake setup used throughout this guide.
- [SnowConvert AI CLI documentation](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README) — reference for `scai init`, `scai code extract`, `scai code convert`, `scai code deploy`, and the cloud data-migration orchestrator.
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) — install and usage guide for the CLI that hosts the migration skills.
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction) — used here for the Snowflake connection config that both `scai` and `snow` share.
- [Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview) — the platform the cloud-migration orchestrator runs on.
- [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects/about-dbt-projects) — target pattern for the replatformed SSIS data flows produced by `migrate-etl-package`.
- [Snowflake Scripting reference](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/index) — background for the procedure rewrites (cursors, `RESULTSET`, `RETURN TABLE`).

sidebar: true
sidebar_json: ai-cookbook
author: Parker Erickson
id: ai-cookbook-agentic-schema-mapping
categories: snowflake-site:taxonomy/product/ai
language: en
summary: A Cortex Agent profiles messy CSV files, proposes column mappings with AI_COMPLETE, resolves free-text values, and loads approved mappings through allowlisted SQL.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-ai-functions/agentic-schema-mapping

# Agentic schema mapping: messy CSVs to canonical tables with a Cortex Agent

## Overview

Finance teams receive the same kinds of data (expenses, vendor invoices, mileage claims) in endless shapes: terse
headers like `Amt` and `Dt`, amounts written `$1,200` or `~38`, dates in four formats, and vendors spelled five ways.
This recipe builds a Cortex Agent that maps each file onto one canonical table. The model proposes the mapping and
matches free-text values to canonical lists, a person approves, and deterministic SQL does the load. You end with
three messy sample files loaded cleanly, a cache that makes repeat file shapes free, and a semantic view the agent can
answer questions from.

| At a glance | |
|---|---|
| Status | GA |
| Stage | Build |
| Topics | Cortex AI Functions, Cortex Agents |
| Time | 45 min |
| Edition | Any edition with Cortex AI Functions and Cortex Agents |
| Regions | Regions where the chosen AI_COMPLETE model and Cortex Agents are available, or cross-region inference enabled |
| Privileges | ACCOUNTADMIN for the account statements in 01_setup.sql and for teardown; everything else runs as COOKBOOK_AGENTIC_SCHEMA_MAPPING_ROLE |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-ai-functions/agentic-schema-mapping) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bagentic-schema-mapping%5D%20&recipe=recipes%2Fcortex-ai-functions%2Fagentic-schema-mapping) |

## When to use this

- Files arrive in shapes you do not control, and writing a pipeline per shape does not scale.
- The target schema is fixed and known, and a human can review a mapping before it runs.
- Free-text values (vendor, department, payment method) must be normalized to a canonical list.

When not to use it:

- The file layout is stable. Write the `COPY INTO` once; no model is needed.
- Loads must run unattended. This design requires an approval step before every new mapping executes.
- Files are wider than 20 columns, or huge. The landing step reads up to 20 columns and refreshes every staged file
  on each `list_files` call.

## How it works

![How it works: Agentic schema mapping: messy CSVs to canonical tables with a Cortex Agent](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/agentic-schema-mapping/assets/agentic-schema-mapping-01.png)

- **The model proposes; SQL decides.** `AI_COMPLETE` with `response_format` returns a mapping whose `operation` and
  `ref_domain` are constrained by `enum`. Nothing the model returns is executed as SQL. The loader builds the
  `INSERT` from fixed templates (`TEXT`, `AMOUNT`, `DATE`, `RESOLVE`) and identifiers that passed an allowlist.
- **Allowlists, not string cleaning.** File names must exist in `RAW_ROWS`, target tables in `TARGET_REGISTRY`,
  target columns in `TARGET_COLUMNS` (built from `INFORMATION_SCHEMA`), and reference domains in `REF_VALUES`. The
  `PROPOSAL_LINES` view reports the reason any line fails. File values are never concatenated into SQL: the file name
  and run id are bind variables, and resolved values are joined from a table.
- **One fixed landing statement.** Every CSV, whatever its header, lands in `RAW_ROWS` as an array of strings per line,
  so profiling and resolution are plain SQL with no dynamic statements.
- **Pay the model once per shape and per value.** Approved mappings are cached by a hash of the header. Resolutions
  are stored per value, so only values never seen before go to the model, and any canonical value the model invents is
  discarded.
- **Caller's rights throughout.** Every procedure runs `EXECUTE AS CALLER`, so the agent can only read and write what
  the calling user's role can.

## Prerequisites

| Requirement | Notes |
| --- | --- |
| Cortex AI Functions and Cortex Agents | The recipe role gets `SNOWFLAKE.CORTEX_USER`. |
| Model access | Default `claude-sonnet-4-6` (in `MODEL_CONFIG`). Enable cross-region inference if it is not in your region, or change `MODEL` in `01_setup.sql`. The agent's orchestration model is `auto`. |
| ACCOUNTADMIN | Only for the account statements at the top of `01_setup.sql` and for `99_teardown.sql`. |
| Default role | Cortex Agents in Snowflake CoWork use the calling user's default role, not the session role. Give users a default role that has been granted `COOKBOOK_AGENTIC_SCHEMA_MAPPING_ROLE`, and a default warehouse. `SNOWFLAKE.CORTEX.DATA_AGENT_RUN` called from SQL ran the tools with the session role in testing, so `07` and the SQL example below work without it. |
| Fixed object names | The procedure bodies, the semantic view YAML, and the agent spec name `COOKBOOK_AGENTIC_SCHEMA_MAPPING` literally, so tool calls work regardless of the caller's current database. Keep the names as written; change only the warehouse size and `MODEL`. |

## Quickstart

Run in order, in one session (Snowsight worksheet, or `snow sql -f <file>` for each):

1. [sql/01_setup.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/01_setup.sql): role, warehouse, database, stage, target tables, allowlists, operational tables.
2. [sql/02_seed_reference_data.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/02_seed_reference_data.sql): canonical values (fictional vendors).
3. [sql/03_stage_sample_files.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/03_stage_sample_files.sql): writes three messy CSV files to the stage.
4. [sql/04_deploy_tools.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/04_deploy_tools.sql): parsers, views, model UDFs, and the six tool procedures.
5. [sql/05_semantic_view.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/05_semantic_view.sql): the `EXPENSE_DATA` semantic view.
6. [sql/06_agent.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/06_agent.sql): the `SCHEMA_MAPPER_AGENT`.
7. [sql/07_run_and_test.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/07_run_and_test.sql): runs the whole pipeline without the agent and prints PASS/FAIL checks.
8. Talk to the agent in Snowflake CoWork: "Map invoices_chaotic.csv".
9. [sql/99_teardown.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-functions/agentic-schema-mapping/sql/99_teardown.sql) when done.

To map your own file, upload it to `@COOKBOOK_AGENTIC_SCHEMA_MAPPING.INGESTION.UPLOAD_STAGE` (Snowsight, or
`PUT file:///path/file.csv @... AUTO_COMPRESS = FALSE`) and ask the agent to map it.

## Walkthrough

### 1. Land and profile

`LIST_FILES()` runs one `COPY INTO RAW_ROWS` with a fixed column list (`ARRAY_CONSTRUCT($1, ..., $20)`) over every
`.csv` on the stage. The header row is row 1. `PROFILE_FILE(file_name)` is plain SQL over `RAW_ROWS`:

```text
File: invoices_chaotic.csv
Data rows: 6
Columns:
1. "From": 6 non-empty, 6 distinct, samples ["Contoso","Lucerne Ship Co","Proseware","Litware Inc","Fabrikam"]
2. "Ref": 6 non-empty, 6 distinct, samples ["INV-2025-0001", ...]
...
```

An unknown file name returns `Unknown file: call list_files ...`, so a path like `../../etc/passwd` never reaches a
stage reference.

### 2. Propose a mapping

`PROPOSE_MAPPING(file_name)` first looks up `MAPPING_CONFIGS` by a SHA-2 hash of the sorted, lowercased header. On a
miss it calls `AI_PROPOSE_MAPPING`, a SQL UDF over `AI_COMPLETE`:

```sql
AI_COMPLETE(
  model => MODEL_NAME,                      -- from MODEL_CONFIG, passed as a bind variable
  prompt => PROMPT,                         -- target schemas + the file profile
  model_parameters => {'temperature': 0, 'max_tokens': 2048},
  response_format => {'type': 'json', 'schema': {... 'operation': {'type': 'string', 'enum': ['TEXT', 'AMOUNT', 'DATE', 'RESOLVE']},
                                                 'ref_domain': {'type': 'string', 'enum': ['NONE', 'DEPARTMENT', 'VENDOR', ...]} ...}})
```

The proposal is stored as `PENDING` and returned with a per-line check from `PROPOSAL_LINES`:

```text
proposal_id: 7c65b450-...   source: llm   target_table: PURCHASE_EXPENSES
| Source column | Target column | Operation | Check |
| team | DEPARTMENT | RESOLVE (DEPARTMENT) | ok |
| when | TRANSACTION_DATE | DATE | ok |
| what/where | VENDOR_NAME | RESOLVE (VENDOR) | ok |
| cost | AMOUNT | AMOUNT | ok |
...
Target columns left empty: ["EMPLOYEE_ID","COST_CENTER","EXPENSE_CATEGORY"]
```

### 3. Resolve free text

`PREVIEW_RESOLUTION(proposal_id)` collects the distinct values of each `RESOLVE` column, skips values already in
`VALUE_RESOLUTION`, and asks `AI_RESOLVE_VALUES` to match the rest to the domain's canonical list. An answer is kept
only if it exactly matches a value in `REF_VALUES`; anything else is stored as no match. On the sample expenses file,
"gas station (Northwind)" resolves to Northwind Fuel and "Sales & BD" to Sales, while the bare "Amex", "visa", and
"petty cash" come back as `NO MATCH`. That is the point of the preview: the user settles them with
`SET_RESOLUTION('PAYMENT_METHOD', 'Amex', 'Corporate Amex')`, which rejects any value that is not canonical. User
corrections take precedence over model answers in `VALUE_RESOLUTION_CURRENT`.

### 4. Execute an approved mapping

`EXECUTE_MAPPING(proposal_id, approved)` refuses unless `approved` is true, the proposal is still `PENDING`, and every
line passes validation. It then builds the load from templates:

```sql
INSERT INTO COOKBOOK_AGENTIC_SCHEMA_MAPPING.INGESTION.PURCHASE_EXPENSES (DEPARTMENT, TRANSACTION_DATE, ..., SOURCE_FILE, LOAD_RUN_ID)
SELECT v0.CANONICAL_VALUE, COOKBOOK_AGENTIC_SCHEMA_MAPPING.INGESTION.PARSE_DATE_LOOSE(r.COLS[4]::VARCHAR), ...,
       p.FILE_NAME, p.RUN_ID
FROM COOKBOOK_AGENTIC_SCHEMA_MAPPING.INGESTION.RAW_ROWS r
JOIN (SELECT ? AS FILE_NAME, ? AS RUN_ID) p ON r.FILE_NAME = p.FILE_NAME
LEFT JOIN COOKBOOK_AGENTIC_SCHEMA_MAPPING.INGESTION.VALUE_RESOLUTION_CURRENT v0
  ON v0.REF_DOMAIN = 'DEPARTMENT' AND v0.SOURCE_VALUE = NULLIF(TRIM(r.COLS[5]::VARCHAR), '')
...
WHERE r.ROW_NUM > 1
```

It runs with `EXECUTE IMMEDIATE :load_sql USING (v_file, run_id)` inside a transaction that first deletes the file's
earlier rows, so reloading a file replaces it. The generated SQL is kept in `RUN_HISTORY.LOAD_SQL` for audit, and the
approved mapping is saved to `MAPPING_CONFIGS`.

### 5. The agent

`06_agent.sql` creates `SCHEMA_MAPPER_AGENT` with `CREATE AGENT IF NOT EXISTS`, then applies the spec with
`ALTER AGENT ... MODIFY LIVE VERSION SET SPECIFICATION`, so reruns update it in place. The spec is assembled in a
Snowflake Scripting block so `$WH` (checked to be a plain identifier) becomes each tool's `execution_environment`
warehouse. The orchestration instructions encode the workflow and forbid calling `execute_mapping` before an explicit
yes. A `cortex_analyst_text_to_sql` tool over `EXPENSE_DATA` answers questions about loaded data.

Run it from SQL:

```sql
SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'COOKBOOK_AGENTIC_SCHEMA_MAPPING.INGESTION.SCHEMA_MAPPER_AGENT',
  $${"messages": [{"role": "user", "content": [{"type": "text",
     "text": "Map invoices_chaotic.csv. Show me the proposed mapping and the resolution preview, but do not load anything yet."}]}]}$$));
```

The response calls `list_files`, `profile_file`, `propose_mapping`, and `preview_resolution` in order, and stops
without loading.

## Verify

`07_run_and_test.sql` ends with a PASS/FAIL table. Expected, all `PASS`:

| Test | Expected detail |
| --- | --- |
| all three files loaded in full | `expenses_messy.csv=10/10, invoices_chaotic.csv=6/6, mileage_messy.csv=5/5` |
| every file went to a different canonical table | `PURCHASE_EXPENSES, VENDOR_INVOICES, MILEAGE_CLAIMS` |
| expense amounts and dates parsed | `total 9812.7100` |
| expense departments and vendors are canonical | canonical department names only |
| invoice dates parsed / mileage distance units stripped | no NULLs; total distance `338.8000` |
| repeat header served from cache | `cache` |
| unapproved execute refused / executed proposal cannot be replayed | `Not executed...` / `Proposal is EXECUTED...` |
| injected identifiers refused | `Not executed. Fix these lines first: ...` |
| non-canonical resolution refused / unknown file refused | `Rejected...` / `Unknown file...` |

Then ask the agent "How much did each department spend on purchases that are already loaded?". It answers through
`query_loaded_data`, for example Engineering 7,150.00 USD across 2 purchases.

## Gotchas

| Symptom | Cause | Fix |
| --- | --- | --- |
| Agent tool fails with "does not exist or not authorized" | Agents run as the user's default role, not the session role | Grant the recipe role to the user's default role and set a default warehouse |
| "Argument number 0 ... needs to be a string literal" | The `AI_COMPLETE` model argument came from a column | Pass the model as a bind variable or literal, as the procedures do |
| Proposal line shows "target column does not exist on the target table" | The model guessed a column name | Nothing runs; call `propose_mapping` again or adjust the prompt |
| A `RESOLVE` value loads as NULL | It was `NO MATCH` and was not corrected | Call `set_resolution` before `execute_mapping` |
| `01/02/2025` loads as January 2 | `PARSE_DATE_LOOSE` reads slash dates as month first | Add a day-first format for your locale, or map that column with your own parser |
| Columns beyond the 20th are missing | `LIST_FILES` lands `$1` to `$20` | Extend `ARRAY_CONSTRUCT` in `LIST_FILES` |
| File contents try to steer the mapping | The profile, including sample values, is part of the prompt | The prompt labels it as data, outputs are allowlisted, and a person approves; keep the approval step |
| Tools fail after `$DB` was changed | Procedure bodies, YAML, and spec use the literal name | Keep the fixed names. Rerun `01_setup.sql` to `06_agent.sql` as written |

## Teardown

```sql
-- sql/99_teardown.sql
DROP DATABASE IF EXISTS COOKBOOK_AGENTIC_SCHEMA_MAPPING;     -- agent, semantic view, stage, tables, procedures
DROP WAREHOUSE IF EXISTS COOKBOOK_AGENTIC_SCHEMA_MAPPING_WH;
DROP ROLE IF EXISTS COOKBOOK_AGENTIC_SCHEMA_MAPPING_ROLE;
```

The recipe makes no account-level changes beyond the role, warehouse, and database.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Install or enable these Cortex Code skills before you start, and use them for the sub-tasks they cover:
cortex-ai-function-studio and agent-optimization (bundled), and check-agent-access and semantic-view-patterns
(install from Snowflake-Labs/coco-skills).

Run the recipe in recipes/cortex-ai-functions/agentic-schema-mapping on my current Snowflake connection.
1. Confirm the target with SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE() and show me before continuing.
2. sql/01_setup.sql makes account-level changes as ACCOUNTADMIN: it creates a role, a warehouse and a database, and
   grants the role to me and to SYSADMIN. Show me those statements and wait for my confirmation.
3. Run sql/01_setup.sql through sql/07_run_and_test.sql in order (snow sql -f per file; each script sets its own
   context). Do not rename objects. Stop on the first error.
4. Show me the PASS/FAIL table from 07. Every row must be PASS.
5. Check my default role and default warehouse. Snowflake CoWork runs the agent as my default role, so tell me if
   that role has not been granted COOKBOOK_AGENTIC_SCHEMA_MAPPING_ROLE. Do not change my user.
6. Using the recipe role as the session role, call the agent with DATA_AGENT_RUN: "Map invoices_chaotic.csv. Show the mapping and resolution preview, do not load."
   Report which tools it called.
7. Use check-agent-access to confirm which roles can run SCHEMA_MAPPER_AGENT and its tools.
8. When I say so, run sql/99_teardown.sql, then confirm nothing named COOKBOOK_AGENTIC_SCHEMA_MAPPING% remains. Only
   drop objects named COOKBOOK_AGENTIC_SCHEMA_MAPPING*.
```

## Related skills

- `cortex-ai-function-studio` (bundled): designing and costing `AI_COMPLETE` calls with structured output.
- `agent-optimization` (bundled): evaluating and tuning the agent's instructions and tools.
- `check-agent-access` (coco-skills): auditing who can run the agent and each custom tool.
- `semantic-view-patterns` (coco-skills): extending `EXPENSE_DATA` (for example with verified queries from the
  `ai_metadata` snippet) once you load real data.

## References

- [AI_COMPLETE (Structured outputs)](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-structured-outputs)
- [AI_COMPLETE (Single string)](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-string)
- [Create and manage agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [Cortex Agents REST API (tool resources)](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- [SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML](https://docs.snowflake.com/en/sql-reference/stored-procedures/system_create_semantic_view_from_yaml)
- [EXECUTE IMMEDIATE](https://docs.snowflake.com/en/sql-reference/sql/execute-immediate)
- [Querying data in staged files](https://docs.snowflake.com/en/user-guide/querying-stage)

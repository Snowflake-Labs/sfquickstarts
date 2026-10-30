author: Yoav Ostrinsky, Charlie Hammond
id: getting-started-with-task-graphs
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/transformation
language: en
summary: Build a Snowflake task graph object with parallel branches, a quality check, a fallback branch and a finalizer, then change it while it runs.
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-task-graphs

# Getting Started with Task Graphs
<!-- ------------------------ -->
## Overview

A task graph runs a set of tasks as one pipeline: each task starts when the tasks before it finish, and independent steps run side by side. In Snowflake, a task graph is its own database object. The graph owns the schedule, the root task, the finalizer, the run configuration and the defaults that every member task inherits, such as the warehouse. Member tasks are ordinary tasks linked by AFTER.

Because the graph is an object, you change it the way you'd change code. You edit a running graph without suspending it, the edits wait as staged changes, and nothing reaches a run until you COMMIT. Every run uses the committed version it started with.

In this guide you'll build a small orders pipeline and put it through three situations:

1. **Build and run it.** A root task loads a batch of orders, two branches summarize it in parallel and pass their counts on as return values, and a quality check decides whether the summaries get published.
2. **Change it while it's resumed.** You add a task to the resumed graph, inspect the staged change, commit it, and watch the next run pick it up.
3. **Break it on purpose.** You run one bad batch so the quality check fails. A fallback branch quarantines the batch, and the finalizer records what happened.

This guide is about building and operating a graph with SQL. For the concepts behind tasks and task graphs, see the [comprehensive guide to orchestration](/en/developers/guides/comprehensive-guide-to-orchestration/). To build the same kind of pipeline visually, see [Getting Started with Pipeline Builder](/en/developers/guides/getting-started-with-pipeline-builder/).

### What You'll Build

A task graph called ORDERS_PIPELINE with seven member tasks:

![The ORDERS_PIPELINE task graph](assets/task_graph_overview.png)

Screenshot placeholder: the Snowsight graph view of ORDERS_PIPELINE showing all seven tasks and the finalizer, captured after the first run in Commit and Run the Graph.

| Task | Role |
|:-----|:-----|
| LOAD_ORDERS | Root. Loads 100 synthetic orders and returns the row count |
| SUMMARIZE_BY_REGION | Branch. Revenue by region, returns how many orders it summarized |
| SUMMARIZE_BY_PRODUCT | Branch. Revenue by product, returns how many orders it summarized |
| CHECK_QUALITY | Compares both branch counts and fails on negative amounts |
| PUBLISH_SUMMARIES | Success path. Runs only when the check passes |
| QUARANTINE_BATCH | Fallback path. Runs only when the check fails |
| RECORD_OUTCOME | Finalizer. Runs after every run and records the outcome |

### What You'll Learn

- How to create a task graph object with a schedule, a finalizer, a run configuration and member defaults
- How to pass return values between tasks that run in parallel
- How to run a task only when an upstream task fails, with SYSTEM$PREDECESSORS_STATE
- How COMMIT, committed versions and EXECUTE TASK GRAPH fit together
- How to change a resumed graph and inspect the change before you release it
- How to read a run with TASK_HISTORY and COMPLETE_TASK_GRAPHS

### Prerequisites

- A Snowflake account and access to the ACCOUNTADMIN role, for the first few statements of the setup script only. They create a dedicated demo role, and everything else runs as that role
- Basic familiarity with SQL and Snowflake Scripting

<!-- ------------------------ -->
## Create a Workspace from Git

In this step, you'll create a Snowsight Workspace linked to the sample task graph repository on GitHub.

1. Navigate to **Projects > Workspaces** in Snowsight.
2. Click **Create** (+) and select **Git repository**.
3. Enter the repository URL: `https://github.com/Snowflake-Labs/sfguide-getting-started-with-task-graphs`
4. Select an API Integration for GitHub ([create one if needed](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git#label-create-a-git-workspace)).
5. Select **Public repository**.

![Creating a Workspace from a Git repository](assets/create_workspace.png)

Screenshot placeholder: the Git repository dialog with the companion repository URL filled in, captured during step 3 above.

Once the workspace is created, you'll see the repository files in the file explorer. The `scripts/` folder contains numbered SQL files that you'll run at different stages of this guide:

| File | When to Run |
|:-----|:------------|
| 01_setup.sql | First, to create the demo role, warehouse, database and tables |
| 02_build_task_graph.sql | To build the graph, commit it and run it once |
| 03_change_while_running.sql | To change the graph while it's resumed |
| 04_force_failure.sql | To run a bad batch and see the fallback branch |
| 05_cleanup.sql | When you're done and want to tear everything down |

Open `scripts/01_setup.sql` in the workspace. You'll run it from there in the next step, and the same goes for the other scripts.

**Prefer a terminal?** Clone the repository and run each script with the [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index), as shown at the end of each section. Every step in this guide works the same way from the CLI.

<!-- ------------------------ -->
## Set Up the Environment

Run all of `01_setup.sql`. It starts as ACCOUNTADMIN and creates a role, DEMO_TASK_GRAPHS_ROLE, with only the account privileges this guide needs:

```sql
CREATE ROLE IF NOT EXISTS DEMO_TASK_GRAPHS_ROLE
  COMMENT = 'Getting Started with Task Graphs: owns every object the guide creates';
GRANT CREATE DATABASE ON ACCOUNT TO ROLE DEMO_TASK_GRAPHS_ROLE;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE DEMO_TASK_GRAPHS_ROLE;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE DEMO_TASK_GRAPHS_ROLE;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE DEMO_TASK_GRAPHS_ROLE;
GRANT ROLE DEMO_TASK_GRAPHS_ROLE TO ROLE SYSADMIN;

SET my_user = CURRENT_USER();
GRANT ROLE DEMO_TASK_GRAPHS_ROLE TO USER IDENTIFIER($my_user);
```

EXECUTE TASK lets the role run tasks. EXECUTE MANAGED TASK is there for a less obvious reason: the member tasks in this guide run on a warehouse, but none of them names one, because the graph supplies it. Snowflake checks a task created without a WAREHOUSE for the serverless privilege, so without this grant the first CREATE TASK fails with "WAREHOUSE not specified and missing serverless task privilege". Granting the role to SYSADMIN keeps the objects it owns visible to your administrators.

The rest of the script, and every later script, runs as DEMO_TASK_GRAPHS_ROLE. As that role it creates:

- A warehouse, DEMO_TASK_GRAPHS_WH (XSMALL, suspends after 60 seconds), that every member task will use
- A database and schema, DEMO_TASK_GRAPHS.PIPELINE
- Four tables: RAW_ORDERS for the incoming batch, REGION_SUMMARY and PRODUCT_SUMMARY for the two branches, and PIPELINE_LOG, where every task writes one row per run

PIPELINE_LOG is how you'll follow each run. Every task stamps its row with the run group ID that Snowflake gives each graph run, so you can group a run's rows together later:

```sql
CREATE OR REPLACE TABLE PIPELINE_LOG (
  RUN_ID    VARCHAR,
  TASK_NAME VARCHAR,
  DETAIL    VARCHAR,
  LOGGED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'One row per task step, keyed by the graph run group ID';
```

The script ends with SHOW TABLES, which should list the four tables, all owned by DEMO_TASK_GRAPHS_ROLE.

**To start over at any point, run `05_cleanup.sql` and then `01_setup.sql`.** Running the later scripts a second time on a graph that has already been through them doesn't give the results shown in this guide.

**CLI alternative:**

```bash
snow sql -f scripts/01_setup.sql
```

<!-- ------------------------ -->
## Build the Task Graph

Open `02_build_task_graph.sql`. The first half creates the member tasks, and the second half creates the graph object over them. Read through this section first, then run the script in the next section.

### Member tasks carry logic, not settings

None of the member tasks names a warehouse or a schedule. The warehouse comes from the graph's member defaults, and the schedule belongs to the graph. Setting a graph-wide property such as SCHEDULE or CONFIG on a member task returns an error.

The task bodies are Snowflake Scripting blocks wrapped in EXECUTE IMMEDIATE with dollar quotes. The wrapper keeps each CREATE TASK in one statement, so the scripts run the same way from a worksheet and from the Snowflake CLI, which splits a file on semicolons.

### The root task reads the run configuration

LOAD_ORDERS truncates RAW_ORDERS and loads 100 generated orders. It reads one setting, inject_bad_rows, from the graph's configuration with SYSTEM$GET_TASK_GRAPH_CONFIG. When the setting is true, three orders get a negative amount. The graph you're about to create sets it to false, so ignore it for now. You'll flip it for a single run in the last act.

An excerpt from the LOAD_ORDERS body, with the load itself elided:

```sql
  LET bad BOOLEAN := COALESCE(SYSTEM$GET_TASK_GRAPH_CONFIG('inject_bad_rows')::BOOLEAN, FALSE);
  ...
  IF (:bad) THEN
    UPDATE RAW_ORDERS SET AMOUNT = -AMOUNT WHERE ORDER_ID <= 3;
  END IF;
  LET loaded VARCHAR := (SELECT COUNT(*) FROM RAW_ORDERS)::VARCHAR;
  ...
  CALL SYSTEM$SET_RETURN_VALUE(:loaded);
```

### Two branches pass return values

SUMMARIZE_BY_REGION and SUMMARIZE_BY_PRODUCT both run AFTER LOAD_ORDERS, so they start together once the root finishes. Each reads the root's row count with SYSTEM$GET_PREDECESSOR_RETURN_VALUE, writes its summary table, and returns the number of orders it summarized:

```sql
CREATE OR REPLACE TASK DEMO_TASK_GRAPHS.PIPELINE.SUMMARIZE_BY_REGION
  COMMENT = 'Branch: revenue by region'
  AFTER DEMO_TASK_GRAPHS.PIPELINE.LOAD_ORDERS
AS
EXECUTE IMMEDIATE $$
BEGIN
  LET run_id VARCHAR := SYSTEM$TASK_RUNTIME_INFO('CURRENT_TASK_GRAPH_RUN_GROUP_ID');
  LET loaded VARCHAR := SYSTEM$GET_PREDECESSOR_RETURN_VALUE('LOAD_ORDERS');
  DELETE FROM REGION_SUMMARY;
  INSERT INTO REGION_SUMMARY SELECT REGION, COUNT(*), SUM(AMOUNT) FROM RAW_ORDERS GROUP BY REGION;
  LET total VARCHAR := (SELECT SUM(ORDER_COUNT) FROM REGION_SUMMARY)::VARCHAR;
  LET detail VARCHAR := 'root loaded ' || :loaded || ', summarized ' || :total;
  INSERT INTO PIPELINE_LOG (RUN_ID, TASK_NAME, DETAIL) VALUES (:run_id, 'SUMMARIZE_BY_REGION', :detail);
  CALL SYSTEM$SET_RETURN_VALUE(:total);
END;
$$;
```

Two details here are easy to get wrong:

- **Pass a variable to SYSTEM$SET_RETURN_VALUE.** An expression such as a cast inside the call fails with "needs to be constant". Convert the value into a VARCHAR variable first, as above.
- **Pass the bare task name to SYSTEM$GET_PREDECESSOR_RETURN_VALUE**, in uppercase: LOAD_ORDERS, not the fully qualified name.

### The quality check joins the branches

CHECK_QUALITY runs AFTER both branches, so it waits for both. It reads both return values, counts negative amounts, and raises an exception when anything is off. A raised exception fails the task, and that failure is what the rest of the graph reacts to. An excerpt, with the run ID and return-value lines elided:

```sql
CREATE OR REPLACE TASK DEMO_TASK_GRAPHS.PIPELINE.CHECK_QUALITY
  COMMENT = 'Quality check: fail when any order has a negative amount'
  AFTER DEMO_TASK_GRAPHS.PIPELINE.SUMMARIZE_BY_REGION, DEMO_TASK_GRAPHS.PIPELINE.SUMMARIZE_BY_PRODUCT
AS
EXECUTE IMMEDIATE $$
DECLARE
  quality_check_failed EXCEPTION (-20001, 'Quality check failed: negative amounts or mismatched branch totals');
BEGIN
  ...
  LET bad_rows NUMBER := (SELECT COUNT(*) FROM RAW_ORDERS WHERE AMOUNT < 0);
  LET detail VARCHAR := 'region=' || :by_region || ' product=' || :by_product || ' bad_rows=' || :bad_rows;
  INSERT INTO PIPELINE_LOG (RUN_ID, TASK_NAME, DETAIL) VALUES (:run_id, 'CHECK_QUALITY', :detail);
  IF (:bad_rows > 0 OR :by_region <> :by_product) THEN
    RAISE quality_check_failed;
  END IF;
END;
$$;
```

The task writes its PIPELINE_LOG row before it raises, so a failed check still leaves a record of what it found.

### Two paths out of the check

Both PUBLISH_SUMMARIES and QUARANTINE_BATCH run AFTER CHECK_QUALITY. PUBLISH_SUMMARIES has no condition, so by default it runs only when its predecessor succeeded. QUARANTINE_BATCH uses advanced branching: its WHEN clause calls SYSTEM$PREDECESSORS_STATE, so it runs only when CHECK_QUALITY failed:

```sql
CREATE OR REPLACE TASK DEMO_TASK_GRAPHS.PIPELINE.QUARANTINE_BATCH
  COMMENT = 'Fallback path: runs only when the quality check fails'
  AFTER DEMO_TASK_GRAPHS.PIPELINE.CHECK_QUALITY
  WHEN SYSTEM$PREDECESSORS_STATE('ALL_FAILED')
AS
  INSERT INTO PIPELINE_LOG (RUN_ID, TASK_NAME, DETAIL)
    SELECT SYSTEM$TASK_RUNTIME_INFO('CURRENT_TASK_GRAPH_RUN_GROUP_ID'), 'QUARANTINE_BATCH',
           (SELECT COUNT(*) FROM RAW_ORDERS WHERE AMOUNT < 0) || ' bad rows quarantined';
```

Once any task in a graph uses advanced branching, Snowflake schedules every task in the graph on every run. A task whose condition isn't met shows up in task history as SKIPPED instead of being left out, which makes it easy to see which path a run took. The [comprehensive guide to orchestration](/en/developers/guides/comprehensive-guide-to-orchestration/) explains the other conditions you can use, and SYSTEM$TASK_COMPLETION_STATE for branching on one named task.

### The finalizer is an ordinary task

RECORD_OUTCOME has no AFTER. It becomes the finalizer because the graph names it, and it runs after every run, whichever path the run took. It looks at what the run logged and records either PUBLISHED or QUARANTINED:

```sql
CREATE OR REPLACE TASK DEMO_TASK_GRAPHS.PIPELINE.RECORD_OUTCOME
  COMMENT = 'Finalizer: record the outcome of every run'
AS
  INSERT INTO PIPELINE_LOG (RUN_ID, TASK_NAME, DETAIL)
    SELECT SYSTEM$TASK_RUNTIME_INFO('CURRENT_TASK_GRAPH_RUN_GROUP_ID'), 'RECORD_OUTCOME',
           IFF(COUNT_IF(TASK_NAME = 'PUBLISH_SUMMARIES') > 0, 'outcome=PUBLISHED', 'outcome=QUARANTINED')
      FROM PIPELINE_LOG
     WHERE RUN_ID = SYSTEM$TASK_RUNTIME_INFO('CURRENT_TASK_GRAPH_RUN_GROUP_ID');
```

### The graph object holds the settings

With the members in place, the graph wraps them:

```sql
CREATE OR REPLACE TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE
  SCHEDULE = '720 MINUTE'
  ROOTS = (DEMO_TASK_GRAPHS.PIPELINE.LOAD_ORDERS)
  FINALIZER = DEMO_TASK_GRAPHS.PIPELINE.RECORD_OUTCOME
  CONFIG = $${"inject_bad_rows": false}$$
  COMMENT = 'Orders pipeline: load, summarize, check, publish or quarantine'
  TASK_DEFAULTS (WAREHOUSE = DEMO_TASK_GRAPHS_WH, LOG_LEVEL = 'INFO');
```

- **ROOTS** names the single root task. Every task reachable from it through AFTER belongs to the graph.
- **FINALIZER** names the finalizer on the graph. The finalizer task itself has no FINALIZE clause.
- **SCHEDULE** is every 720 minutes, so the graph won't fire on its own while you work through this guide. You'll trigger runs by hand.
- **CONFIG** is a JSON string every task can read.
- **TASK_DEFAULTS** cascades the warehouse and log level to every member that doesn't set its own.

Write the task names in ROOTS and FINALIZER fully qualified. An unqualified name resolves against your session's current schema, not the graph's, and the root must live in the graph's schema. Run the CREATE from another schema with an unqualified root and it fails with "Invalid root task ... The task must exist in the same schema as the task graph".

**Watch the clause order.** The properties (SCHEDULE, ROOTS, FINALIZER, CONFIG, COMMENT and the rest) can come in any order, but TASK_DEFAULTS must come after all of them, and a graph-level WHEN, if you use one, must come last. Putting COMMENT after TASK_DEFAULTS fails with "syntax error ... unexpected 'COMMENT'", and putting TASK_DEFAULTS after WHEN fails with "unexpected 'TASK_DEFAULTS'".

<!-- ------------------------ -->
## Commit and Run the Graph

Now run all of `02_build_task_graph.sql`. After creating the tasks and the graph, it does three things.

**It commits the graph.** A new graph has no committed version, and a graph only ever runs a committed version. COMMIT freezes the current definition as version 1. It doesn't start the schedule:

```sql
ALTER TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE COMMIT;
```

SHOW TASK GRAPHS then lists ORDERS_PIPELINE as SUSPENDED, with has_pending_changes false and a task_defaults column that holds the warehouse and log level as JSON.

**It runs the graph once.** EXECUTE TASK GRAPH starts one run of the committed version right away. The graph doesn't need to be resumed:

```sql
EXECUTE TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE;

CALL SYSTEM$WAIT(60);
```

SYSTEM$WAIT pauses the script for a minute so the run can finish. A run takes about 30 seconds on an XSMALL warehouse that has to resume first.

**It reads the run.** Task history for a task graph is keyed by the graph's ID, so the script captures the ID from SHOW TASK GRAPHS and passes it to TASK_HISTORY as GRAPH_ID. Don't use ROOT_TASK_ID for a task graph object: it's NULL on these runs, so a query that filters on it returns no rows.

```sql
SHOW TASK GRAPHS LIKE 'ORDERS_PIPELINE' IN SCHEMA DEMO_TASK_GRAPHS.PIPELINE;
SET graph_id = (SELECT "id" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())));

SELECT NAME, STATE, RETURN_VALUE, GRAPH_VERSION
  FROM TABLE(DEMO_TASK_GRAPHS.INFORMATION_SCHEMA.TASK_HISTORY(
         GRAPH_ID => $graph_id,
         SCHEDULED_TIME_RANGE_END => CURRENT_TIMESTAMP()))
QUALIFY GRAPH_RUN_GROUP_ID = FIRST_VALUE(GRAPH_RUN_GROUP_ID) OVER (ORDER BY SCHEDULED_TIME DESC)
 ORDER BY SCHEDULED_TIME, NAME;
```

| NAME | STATE | RETURN_VALUE | GRAPH_VERSION |
|:-----|:------|:-------------|:--------------|
| LOAD_ORDERS | SUCCEEDED | 100 | 1 |
| SUMMARIZE_BY_PRODUCT | SUCCEEDED | 100 | 1 |
| SUMMARIZE_BY_REGION | SUCCEEDED | 100 | 1 |
| CHECK_QUALITY | SUCCEEDED | NULL | 1 |
| PUBLISH_SUMMARIES | SUCCEEDED | NULL | 1 |
| QUARANTINE_BATCH | SKIPPED | NULL | 1 |
| RECORD_OUTCOME | SUCCEEDED | NULL | 1 |

If a task still shows as EXECUTING or the finalizer is missing, wait a few seconds and run the query again.

The return values show the hand-off: the root returned 100, and each branch returned the 100 orders it summarized. QUARANTINE_BATCH is SKIPPED because its predecessor succeeded. The last query in the script shows what each task logged:

| TASK_NAME | DETAIL |
|:----------|:-------|
| LOAD_ORDERS | loaded 100 rows, inject_bad_rows=false |
| SUMMARIZE_BY_REGION | root loaded 100, summarized 100 |
| SUMMARIZE_BY_PRODUCT | root loaded 100, summarized 100 |
| CHECK_QUALITY | region=100 product=100 bad_rows=0 |
| PUBLISH_SUMMARIES | summaries published |
| RECORD_OUTCOME | outcome=PUBLISHED |

The two branches can appear in either order, because they ran in parallel. Take note of this run: it's the baseline you'll compare against at the end.

To see the same run in Snowsight, go to **Catalog > Database Explorer**, expand DEMO_TASK_GRAPHS, then PIPELINE, then Tasks, select LOAD_ORDERS, and open its **Graph** and **Run History** tabs.

![Task graph run in Snowsight](assets/task_graph_first_run.png)

Screenshot placeholder: the Snowsight graph view of the first run, with QUARANTINE_BATCH shown as skipped, captured after 02_build_task_graph.sql finishes.

**CLI alternative:** this runs the whole script, including the wait, and prints every result.

```bash
snow sql -f scripts/02_build_task_graph.sql
```

<!-- ------------------------ -->
## Change the Graph While It's Resumed

The analytics team wants the pipeline to flag the top revenue region after every published batch. With a graph built from root-task settings, you'd suspend the root, change the tasks, and resume. With a task graph object you leave it running.

Run all of `03_change_while_running.sql`.

### Resume the graph

```sql
ALTER TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE RESUME;
```

The graph is now on its 720-minute schedule. RESUME needs a committed version, and that version must have a SCHEDULE or a WHEN condition. Without one, RESUME fails with "the committed snapshot has no SCHEDULE or WHEN condition". You resume and suspend the graph as a whole: once a graph has a committed version, ALTER TASK ... SUSPEND on a single member fails and tells you to use ALTER TASK GRAPH.

### Add a task without suspending

The new task is an ordinary task with an AFTER that hangs it off PUBLISH_SUMMARIES, so it runs only on the success path:

```sql
CREATE TASK IF NOT EXISTS DEMO_TASK_GRAPHS.PIPELINE.FLAG_TOP_REGION
  COMMENT = 'Added while resumed: log the top revenue region'
  AFTER DEMO_TASK_GRAPHS.PIPELINE.PUBLISH_SUMMARIES
AS
  INSERT INTO PIPELINE_LOG (RUN_ID, TASK_NAME, DETAIL)
    SELECT SYSTEM$TASK_RUNTIME_INFO('CURRENT_TASK_GRAPH_RUN_GROUP_ID'), 'FLAG_TOP_REGION', 'top region ' || REGION
      FROM REGION_SUMMARY
     ORDER BY REVENUE DESC
     LIMIT 1;
```

The statement succeeds while the graph is resumed. The change is staged: it's part of the graph's live definition but not of the committed version, so scheduled and manual runs keep using version 1.

IF NOT EXISTS makes this statement safe to repeat, but it also means a second run of the script stages nothing, because FLAG_TOP_REGION is already committed. The change tables below then come back empty. To see them again, start over with `05_cleanup.sql` and `01_setup.sql`.

### Inspect the staged change

SHOW TASK GRAPHS now reports the change:

| name | state | has_pending_changes |
|:-----|:------|:--------------------|
| ORDERS_PIPELINE | STARTED | true |

TASK_GRAPH_CHANGES shows exactly what a COMMIT would release, one row per added, removed or changed task or graph setting. BEFORE holds the committed DDL and AFTER the staged DDL, so a NULL on either side means the entity was added or removed:

```sql
SELECT ENTITY_TYPE, ENTITY_NAME, BEFORE IS NULL AS IS_NEW, AFTER IS NULL AS IS_REMOVED
  FROM TABLE(DEMO_TASK_GRAPHS.INFORMATION_SCHEMA.TASK_GRAPH_CHANGES(
         TASK_GRAPH_NAME => 'DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE'));
```

| ENTITY_TYPE | ENTITY_NAME | IS_NEW | IS_REMOVED |
|:------------|:------------|:-------|:-----------|
| TASK | FLAG_TOP_REGION | TRUE | FALSE |

Two SHOW commands give you the two views of the graph. SHOW TASKS reflects the live definition, so it lists eight tasks, including FLAG_TOP_REGION. SHOW COMMITTED TASKS reflects what runs, so it still lists seven, all at version 1:

```sql
SHOW COMMITTED TASKS IN GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE
  ->> SELECT "name", "version", "warehouse" FROM $1 ORDER BY "name";
```

| name | version | warehouse |
|:-----|:--------|:----------|
| CHECK_QUALITY | 1 | DEMO_TASK_GRAPHS_WH |
| LOAD_ORDERS | 1 | DEMO_TASK_GRAPHS_WH |
| PUBLISH_SUMMARIES | 1 | DEMO_TASK_GRAPHS_WH |
| QUARANTINE_BATCH | 1 | DEMO_TASK_GRAPHS_WH |
| RECORD_OUTCOME | 1 | DEMO_TASK_GRAPHS_WH |
| SUMMARIZE_BY_PRODUCT | 1 | DEMO_TASK_GRAPHS_WH |
| SUMMARIZE_BY_REGION | 1 | DEMO_TASK_GRAPHS_WH |

The warehouse column shows TASK_DEFAULTS at work: no member names a warehouse, and every committed task runs on DEMO_TASK_GRAPHS_WH.

### Commit and run the new version

```sql
ALTER TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE COMMIT;
```

SHOW COMMITTED TASKS now lists eight tasks at version 2, and TASK_GRAPH_CHANGES returns no rows. The script then runs the graph and reads the run:

| NAME | STATE | GRAPH_VERSION |
|:-----|:------|:--------------|
| LOAD_ORDERS | SUCCEEDED | 2 |
| SUMMARIZE_BY_PRODUCT | SUCCEEDED | 2 |
| SUMMARIZE_BY_REGION | SUCCEEDED | 2 |
| CHECK_QUALITY | SUCCEEDED | 2 |
| PUBLISH_SUMMARIES | SUCCEEDED | 2 |
| QUARANTINE_BATCH | SKIPPED | 2 |
| FLAG_TOP_REGION | SUCCEEDED | 2 |
| RECORD_OUTCOME | SUCCEEDED | 2 |

The run used version 2, and FLAG_TOP_REGION ran after PUBLISH_SUMMARIES. The graph's next scheduled run moves to the new version too. A run that's already in progress when you commit finishes on the version it started with.

![The graph after adding FLAG_TOP_REGION](assets/task_graph_version_2.png)

Screenshot placeholder: the Snowsight graph view showing FLAG_TOP_REGION after PUBLISH_SUMMARIES, captured after 03_change_while_running.sql finishes.

**To change a member that's already committed, use ALTER TASK, not CREATE OR REPLACE TASK.** ALTER TASK ... MODIFY AS replaces the body and ALTER TASK ... SET changes a property, and both become staged changes like the one above. While the graph is resumed, Snowflake rejects a replace or drop of a committed member. On a suspended graph the replace goes through but throws away the graph's committed version, and the graph won't run again until you COMMIT.

**CLI alternative:**

```bash
snow sql -f scripts/03_change_while_running.sql
```

<!-- ------------------------ -->
## Force a Failure

So far every batch has been clean, and QUARANTINE_BATCH has been skipped on every run. Time to send a bad batch through.

Remember the inject_bad_rows setting? Run all of `04_force_failure.sql`. It starts with one run that overrides the graph's configuration:

```sql
EXECUTE TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE
  USING CONFIG = $${"inject_bad_rows": true}$$;
```

USING CONFIG merges into the graph's CONFIG for this run only: keys you pass override the graph's values, and keys you leave out keep them. The graph definition keeps inject_bad_rows set to false, so the next run is clean again.

### What the run did

LOAD_ORDERS flipped three amounts negative, the branches summarized as usual, and CHECK_QUALITY raised its exception. That one failure sent the run down the other path. The script's TASK_HISTORY query returns NAME, STATE and ERROR_MESSAGE:

| NAME | STATE |
|:-----|:------|
| LOAD_ORDERS | SUCCEEDED |
| SUMMARIZE_BY_PRODUCT | SUCCEEDED |
| SUMMARIZE_BY_REGION | SUCCEEDED |
| CHECK_QUALITY | FAILED |
| PUBLISH_SUMMARIES | SKIPPED |
| QUARANTINE_BATCH | SUCCEEDED |
| FLAG_TOP_REGION | SKIPPED |
| RECORD_OUTCOME | SUCCEEDED |

The error message for CHECK_QUALITY is your own exception: "Uncaught exception of type 'QUALITY_CHECK_FAILED' on line 12 at position 4 : Quality check failed: negative amounts or mismatched branch totals". The two skipped tasks explain themselves too: "Conditional expression for task evaluated to false. This task defines no condition of its own; the evaluated condition was the default requirement for all predecessors to succeed."

PUBLISH_SUMMARIES and the FLAG_TOP_REGION task below it were skipped, QUARANTINE_BATCH ran, and the finalizer ran anyway.

### Every run, side by side

The next query in the script groups PIPELINE_LOG by run, so the whole story fits in one result:

```sql
SELECT MIN(LOGGED_AT) AS RUN_STARTED,
       MAX(IFF(TASK_NAME = 'LOAD_ORDERS', DETAIL, NULL)) AS LOADED,
       MAX(IFF(TASK_NAME = 'CHECK_QUALITY', DETAIL, NULL)) AS QUALITY_CHECK,
       BOOLOR_AGG(TASK_NAME = 'PUBLISH_SUMMARIES') AS PUBLISHED,
       BOOLOR_AGG(TASK_NAME = 'QUARANTINE_BATCH') AS QUARANTINED,
       MAX(IFF(TASK_NAME = 'RECORD_OUTCOME', DETAIL, NULL)) AS FINALIZER
  FROM PIPELINE_LOG
 GROUP BY RUN_ID
 ORDER BY RUN_STARTED;
```

| RUN_STARTED | LOADED | QUALITY_CHECK | PUBLISHED | QUARANTINED | FINALIZER |
|:------------|:-------|:--------------|:----------|:------------|:----------|
| ... | loaded 100 rows, inject_bad_rows=false | region=100 product=100 bad_rows=0 | TRUE | FALSE | outcome=PUBLISHED |
| ... | loaded 100 rows, inject_bad_rows=false | region=100 product=100 bad_rows=0 | TRUE | FALSE | outcome=PUBLISHED |
| ... | loaded 100 rows, inject_bad_rows=true | region=100 product=100 bad_rows=3 | FALSE | TRUE | outcome=QUARANTINED |

The first two rows are your runs on version 1 and version 2. Any extra run you started along the way adds a row of its own. The last row is the bad batch: the quality check found three bad rows, nothing was published, the batch was quarantined, and the finalizer recorded it.

### How the graph reports the run

COMPLETE_TASK_GRAPHS has one row per finished graph run. The script filters it on the graph ID, because GRAPH_NAME takes the bare graph name and also matches older graphs with the same name:

| STATE | GRAPH_VERSION | FIRST_ERROR_TASK_NAME |
|:------|:--------------|:----------------------|
| FAILED | 2 | CHECK_QUALITY |
| SUCCEEDED | 2 | NULL |
| SUCCEEDED | 1 | NULL |

The graph run is FAILED even though the fallback handled the bad batch, because one of its tasks failed. Keep that in mind if you alert on graph failures: a failure your fallback absorbs still counts as one.

![The failed run in Snowsight](assets/task_graph_failed_run.png)

Screenshot placeholder: the Snowsight graph view of the bad-batch run, with CHECK_QUALITY failed, PUBLISH_SUMMARIES and FLAG_TOP_REGION skipped, and QUARANTINE_BATCH succeeded, captured after the payoff query in 04_force_failure.sql.

<!-- ------------------------ -->
## Retire a Task and Park the Graph

The top-region flag was a one-off request, so the end of `04_force_failure.sql` takes FLAG_TOP_REGION out again. A task in the committed version of a resumed graph can't be dropped. DROP TASK fails and its error spells out the way around it: sever the task, commit, then drop. The ALTER and the DROP both use IF EXISTS, so the end of the script doesn't fail if FLAG_TOP_REGION is already gone.

```sql
ALTER TASK IF EXISTS DEMO_TASK_GRAPHS.PIPELINE.FLAG_TOP_REGION
  REMOVE AFTER DEMO_TASK_GRAPHS.PIPELINE.PUBLISH_SUMMARIES;
```

REMOVE AFTER cuts the task's only link to the graph. TASK_GRAPH_CHANGES shows the staged removal:

| ENTITY_TYPE | ENTITY_NAME | IS_NEW | IS_REMOVED |
|:------------|:------------|:-------|:-----------|
| TASK | FLAG_TOP_REGION | FALSE | TRUE |

```sql
ALTER TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE COMMIT;

DROP TASK IF EXISTS DEMO_TASK_GRAPHS.PIPELINE.FLAG_TOP_REGION;
```

After the COMMIT, FLAG_TOP_REGION isn't part of any committed version, so the DROP succeeds.

Finally, the script suspends the graph so it won't run again on its schedule:

```sql
ALTER TASK GRAPH DEMO_TASK_GRAPHS.PIPELINE.ORDERS_PIPELINE SUSPEND;
```

| name | state | has_pending_changes |
|:-----|:------|:--------------------|
| ORDERS_PIPELINE | SUSPENDED | false |

A suspended graph keeps its committed version. You can still run it on demand with EXECUTE TASK GRAPH, or put it back on its schedule with RESUME.

**CLI alternative:**

```bash
snow sql -f scripts/04_force_failure.sql
```

<!-- ------------------------ -->
## Cleanup

Run `05_cleanup.sql` to remove everything this guide created, including the demo role. It runs as ACCOUNTADMIN, which inherits DEMO_TASK_GRAPHS_ROLE through SYSADMIN, so it can drop the role's objects and still runs cleanly a second time:

```sql
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS DEMO_TASK_GRAPHS;
DROP WAREHOUSE IF EXISTS DEMO_TASK_GRAPHS_WH;
DROP ROLE IF EXISTS DEMO_TASK_GRAPHS_ROLE;
```

Dropping the database removes the schema, the task graph, its member tasks and the tables in one statement, even while the graph is resumed. To remove only the graph and keep its tasks, use DROP TASK GRAPH instead: the member tasks stay behind as ordinary suspended tasks, AFTER links intact. To run the guide again, run `01_setup.sql` after this.

**CLI alternative:**

```bash
snow sql -f scripts/05_cleanup.sql
```

<!-- ------------------------ -->
## Conclusion and Resources

You built a task graph object, ran it, changed it while it was resumed, and watched it take its fallback path on a bad batch.

### What You Learned

- The graph object owns the schedule, root, finalizer, CONFIG and TASK_DEFAULTS. Member tasks carry only their logic and their AFTER links
- Return values pass data between tasks, and SYSTEM$PREDECESSORS_STATE gives a task a fallback path
- A graph only runs committed versions. Edits stay staged until COMMIT, and TASK_GRAPH_CHANGES shows them first
- EXECUTE TASK GRAPH with USING CONFIG runs once with different settings, and TASK_HISTORY with GRAPH_ID shows what each run did
- To retire a member of a resumed graph: REMOVE AFTER, COMMIT, then DROP

### Related Resources

- [Comprehensive guide to orchestration](/en/developers/guides/comprehensive-guide-to-orchestration/)
- [Getting Started with Pipeline Builder](/en/developers/guides/getting-started-with-pipeline-builder/)
- [Declare Task Graph as an object](https://docs.snowflake.com/en/user-guide/task-graph-object)
- [CREATE TASK GRAPH](https://docs.snowflake.com/en/sql-reference/sql/create-task-graph)
- [ALTER TASK GRAPH](https://docs.snowflake.com/en/sql-reference/sql/alter-task-graph)
- [EXECUTE TASK GRAPH](https://docs.snowflake.com/en/sql-reference/sql/execute-task-graph)
- [TASK_GRAPH_CHANGES](https://docs.snowflake.com/en/sql-reference/functions/task_graph_changes)
- [Control when tasks run with advanced branching](https://docs.snowflake.com/en/user-guide/tasks-graphs#label-task-graph-advanced-branching)
- [Companion repository](https://github.com/Snowflake-Labs/sfguide-getting-started-with-task-graphs)

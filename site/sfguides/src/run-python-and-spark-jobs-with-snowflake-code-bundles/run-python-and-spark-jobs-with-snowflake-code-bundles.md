author: Gilberto Hernandez, Snowflake CoCo
id: run-python-and-spark-jobs-with-snowflake-code-bundles
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Run your existing Python project on Snowflake with Code Bundles. If you also have PySpark, run it as a native Spark job from the same bundle.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-run-python-and-spark-jobs-with-code-bundles

# Run Python or Spark Jobs on Snowflake with Code Bundles
<!-- ------------------------ -->
## Overview

> **Note:** Code Bundles are in Public Preview.

You have Python scripts that process data already sitting in Snowflake, but the scripts run somewhere else: on a VM, a cron server, a notebook host, or a Spark cluster you provision and pay for whether it's running or not. You could rewrite everything as stored procedures, but that means matching handler signatures, re-declaring packages, and splitting a project that works as a unit into separate database objects.

In this Quickstart, we'll skip all of that. We'll take a clickstream pipeline as-is – a Python sessionizer, a PySpark analytics job, shared helpers – package it as a single **Code Bundle**, and run each file on Snowflake. The Python job runs on a warehouse. The PySpark job runs as a native Spark job, with **no Spark cluster** required. By the end, you'll have the pipeline scheduled on a Task and producing fictional funnel metrics from ~50K clickstream events.

### What You'll Learn
- How to package a project as a Code Bundle and run it on Snowflake compute
- How to run a Python job on a **warehouse** with `EXECUTE CODE BUNDLE`
- How to override a bundle's specification at execution time with `WITH SPECIFICATION`
- How to submit a PySpark job via the REST API, SQL, or from a stage – no Spark cluster required
- How to orchestrate a multi-stage pipeline with a Snowflake **Task**
- How to version, run asynchronously, and monitor your jobs in production

### What You'll Need
- A Snowflake account with access to Code Bundles, with a role that can create warehouses and databases (for example, **ACCOUNTADMIN**)
- The [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index):
  ```bash
  pip install snowflake-cli
  # or: uv tool install snowflake-cli
  ```
- A configured Snowflake CLI connection (verify with `snow connection list`)
- Basic familiarity with Python, PySpark, and SQL

> **Tip:** You can run this Quickstart with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code), Snowflake's AI coding assistant. Point Cortex Code at this guide and it can execute each step for you, explain what's happening, and help you adapt the pipeline to your own data. You can also use it side-by-side as you work through the guide in your terminal.


### What You'll Build
- A clickstream pipeline with two independent stages – a warehouse Python sessionizer and a native Spark analytics job – packaged as a Code Bundle and sequenced by a Task:

```console
   RAW_EVENTS (50K clickstream events)
      │
      ├──────────────────────────────┐
      ▼                              ▼
 ┌─────────────────────┐   ┌─────────────────────────┐
 │  sessionize.py      │   │  spark_analytics.py      │
 │  (warehouse Python) │   │  (Spark job)             │
 └─────────────────────┘   └─────────────────────────┘
      │  SESSIONS              │  FUNNEL_METRICS
      │                        │  PRODUCT_PAIRS
      ▼                        ▼
   Sequenced by a Snowflake Task
```

Let's get started!

<!-- ------------------------ -->
## What are Code Bundles?

A Code Bundle is a named Snowflake object that contains your project source files – Python scripts, PySpark jobs, shared helpers, a spec file – created from a stage, workspace, or local directory. You run any file in the bundle with `EXECUTE CODE BUNDLE`, choosing the compute type per-run.

Key properties:

- One deployment unit, multiple entrypoints. A multi-file project stays together as one object. You don't create a separate bundle (or stored procedure) for each script – you run different files from the same bundle.
- A spec declares the default runtime. A **code_bundle.yml** file in the root of your project describes how the bundle runs by default (language, compute type, packages). You can override it per-run with `WITH SPECIFICATION` when a different file needs a different runtime.
- Production-ready out of the box. Code Bundles support versioning, asynchronous execution, and run history – no additional scaffolding.

### How it differs from stored procedures

With stored procedures, you rewrite each script to a handler signature, declare packages per-object, and split a multi-file project into separate database objects. With Code Bundles, you bring your project directory as-is – the files, the imports between them, the argument parsing – bundle them together and run all of it directly.

### When to use each compute type

A Code Bundle can target different workloads depending on the runtime:

| Workload | Type | Compute Type | How it runs | Example |
|----------|------|-------------|-------------|---------|
| Python | `custom` | `warehouse` | Pushes SQL/UDF work down to the engine | Sessionizing events with window functions |
| PySpark | `spark` | `warehouse` | DataFrame API runs on the Snowflake engine via Snowpark Connect | Funnel analysis, co-occurrence with self-joins |
| Python on a compute pool | `custom` | `compute_pool` | Full Python runtime on container compute | Training a scikit-learn model, GPU inference |

<!-- ------------------------ -->
## Set up your account

Let's create the objects our pipeline needs and generate the clickstream data. We'll produce ~50K events across 1,000 users, 200 products, 10 categories, and 30 days – enough to produce meaningful funnels and co-occurrence patterns.

Clone the companion repo and open the project:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-run-python-and-spark-jobs-with-code-bundles
```

```bash
cd sfguide-run-python-and-spark-jobs-with-code-bundles
```

Run the setup script:

```bash
snow sql -f setup.sql
```

Here's what the setup creates:

```sql
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS CB_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS CODE_BUNDLES_DB;
CREATE SCHEMA   IF NOT EXISTS CODE_BUNDLES_DB.PIPELINE;

USE WAREHOUSE CB_WH;
USE DATABASE  CODE_BUNDLES_DB;
USE SCHEMA    PIPELINE;
```

The full **setup.sql** generates a `PRODUCTS` dimension table (200 products across 10 categories) and a `RAW_EVENTS` table with ~50K clickstream events. Events follow a realistic funnel shape: ~40% page views, ~30% product views, ~20% add-to-carts, and ~10% purchases, distributed across five traffic sources (organic, paid search, social, email, direct) and three device types.

The verification query at the end confirms ~50K total events with the expected funnel distribution.

<!-- ------------------------ -->
## Explore the pipeline code

The pipeline you're migrating is just Python. Let's look at both stages before we deploy them – the important part is that we don't change them to run on Snowflake.

### Stage 1: The sessionizer (**sessionize.py**)

This job reads raw events and assigns session IDs based on 30-minute inactivity gaps – a standard sessionization pattern. It then computes per-session metrics: duration, event counts by type, revenue, and whether the session converted.

Here's what the code does:

- Uses `LAG` to find the previous event per user, then flags new sessions wherever the gap exceeds 30 minutes
- Aggregates events within each session into metrics (page views, carts, purchases, revenue)
- Writes a `SESSIONS` table – one row per session with dimensions (device, traffic source) carried forward

The key detail is `get_session()` in **helpers.py**. It calls `get_active_session()`, which returns the Snowpark session that Snowflake injects at runtime when the bundle executes:

```python
# sessionize.py
from helpers import get_session, log_step

def main() -> None:
    args = parse_args()
    session = get_session()

    log_step(f"Sessionizing {args.source_table} (timeout: {args.inactivity_minutes} min)")

    session.sql(f"""
        CREATE OR REPLACE TABLE {args.output_table} AS
        WITH ordered_events AS (
            SELECT *,
                LAG(EVENT_TIMESTAMP) OVER (
                    PARTITION BY USER_ID ORDER BY EVENT_TIMESTAMP
                ) AS prev_event_ts
            FROM {args.source_table}
        ),
        session_boundaries AS (
            SELECT *,
                CASE
                    WHEN prev_event_ts IS NULL THEN 1
                    WHEN DATEDIFF('minute', prev_event_ts, EVENT_TIMESTAMP) > {args.inactivity_minutes} THEN 1
                    ELSE 0
                END AS is_new_session
            FROM ordered_events
        ),
        ...
    """).collect()
```

```python
# helpers.py
from snowflake.snowpark.context import get_active_session

def get_session() -> Session:
    try:
        return get_active_session()
    except Exception:
        raise RuntimeError("No active Snowpark session found. ...")
```

When a file runs as a Code Bundle, Snowflake injects the session automatically – no credentials in your code, no connection setup. The helper's error message makes it clear that this script is meant to be executed via `EXECUTE CODE BUNDLE`.

The wrapper in **helpers.py** isn't required – all you need is `get_active_session()`. We use a shared helper here because **sessionize.py** imports from it (for both `get_session` and `log_step`), and it's a natural pattern when a project has multiple entrypoints that may share utility code.

### Stage 2: The Spark analytics (**spark_analytics.py**)

This is PySpark – DataFrames and `functions.*`. The only Snowflake-specific line is the session initialization, which uses Snowpark Connect to create a SparkSession that compiles DataFrame operations into SQL and runs them on the warehouse:

```python
from snowflake.snowpark_connect import init_spark_session
from pyspark.sql import functions as F

def main() -> None:
    args = parse_args()
    spark = init_spark_session()

    events = spark.table(args.events_table)

    # Funnel analysis: step-by-step conversion per traffic_source × device
    funnel = build_funnel(events)
    funnel.write.mode("overwrite").saveAsTable(args.funnel_output)

    # Product co-occurrence: which products are browsed together?
    pairs = build_product_pairs(events)
    pairs.write.mode("overwrite").saveAsTable(args.pairs_output)
```

Here's what the analytics compute:

- Funnel analysis – for each traffic source and device type, how many sessions reached each step (page view → product view → cart → purchase), with conversion rates and drop-off percentages at each stage
- Product co-occurrence – within each user's browsing history, which products appear together and how much more often than chance (lift score)

Both of these are textbook PySpark patterns: iterative aggregation over user-level event sequences and combinatorial pair generation. On Snowflake, `init_spark_session()` returns a SparkSession powered by Snowpark Connect, which compiles the Spark DataFrame API into SQL and runs it on the warehouse – no Spark cluster to stand up or manage. Everything after the session init is standard PySpark: DataFrames, Column expressions, GroupedData, and `functions.*`.

<!-- ------------------------ -->
## Run the sessionizer on a warehouse

Now let's run **sessionize.py** on Snowflake. Because this job orchestrates SQL (window functions in this case) over Snowflake data, a warehouse is the correct compute type.

A single file, **code_bundle.yml**, describes the default way the bundle runs. It's a default, but is also mutable. You can override it per-run when a different file in the project needs different settings:

```yaml
bundle:
  type: custom
  compute_type: warehouse
  language: python
  compute_options:
    runtime_version: '3.11'
  properties:
    requirements_file: pyproject.toml
```

Here's what the specification says:

- `compute_type: warehouse` – run on the warehouse set in the session
- `runtime_version: '3.11'` – the Python version for the run (always quote the value)
- `requirements_file` – packages to install, resolved from Snowflake's PyPI proxy

From the project root, create the Code Bundle from your local files and run it. We'll name the bundle CLICKSTREAM_PIPELINE:

> **Note:** The CLI needs to know which database and schema to create the bundle in. You can pass `--database` and `--schema` on each command (as shown below), or add `database = "CODE_BUNDLES_DB"` and `schema = "PIPELINE"` to your connection in **connections.toml** so you don't have to repeat them.

```bash
snow bundle create CLICKSTREAM_PIPELINE --source . --exclude ".venv/**" --exclude "setup.sql" --database CODE_BUNDLES_DB --schema PIPELINE
```

Now run the sessionizer. Everything after `--` is passed straight to your script's `argparse`. 

```bash
snow bundle execute CLICKSTREAM_PIPELINE \
  --entrypoint sessionize.py \
  --database CODE_BUNDLES_DB --schema PIPELINE \
  -- --source-table RAW_EVENTS \
     --output-table SESSIONS \
     --inactivity-minutes 30
```

Your first job is running on Snowflake – sessionizing 50K events into structured sessions with no rewrite, no stored procedure. 

When the run finishes, confirm the output. You should see thousands of sessions:

```bash
snow sql -q "SELECT COUNT(*) AS total_sessions, SUM(CASE WHEN CONVERTED THEN 1 ELSE 0 END) AS converted, ROUND(AVG(DURATION_SECONDS)) AS avg_duration_sec FROM CODE_BUNDLES_DB.PIPELINE.SESSIONS;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Example output:

```bash
+-----------------------------------------------+
| TOTAL_SESSIONS | CONVERTED | AVG_DURATION_SEC |
|----------------+-----------+------------------|
| 5952           | 3460      | 637              |
+-----------------------------------------------+
```


<!-- ------------------------ -->
## Run the Spark analytics

If your work is Python-only, you've already learned the core Code Bundles workflow – packaging, deploying, and running a project on Snowflake. The following sections show how the same bundle handles Spark and compute pool workloads.

Both **sessionize.py** and **spark_analytics.py** live in the same project alongside shared helpers. The bundle keeps them together as a single deployment unit – you don't create a second bundle for a second script. Instead, you run a different file with a different spec.

A Spark job uses `type: spark` instead of `type: custom`, and an empty `compute_options: {}` to run on the latest Snowpark Connect client version. You can pin a specific version with `runtime_version` for reproducibility. Everything else – entrypoint, arguments, compute on a warehouse – works the same way.

### Submit via the REST API

The Code Bundles REST API is the recommended way to submit Spark jobs, especially from external orchestrators like Airflow, CI/CD pipelines, or custom UIs. If you're a Spark engineer, this pattern aligns with patterns you may already use on other platforms: POST a job definition, get back an ID, poll for status.

The REST API submits jobs from a stage path rather than a stored bundle. Let's upload the project files to a stage first. Run the following commands from within the companion repo directory:

```bash
snow sql -q "CREATE STAGE IF NOT EXISTS CODE_BUNDLES_DB.PIPELINE.SPARK_STAGE;" --database CODE_BUNDLES_DB --schema PIPELINE
snow stage copy spark_analytics.py @CODE_BUNDLES_DB.PIPELINE.SPARK_STAGE --database CODE_BUNDLES_DB --schema PIPELINE
snow stage copy helpers.py @CODE_BUNDLES_DB.PIPELINE.SPARK_STAGE --database CODE_BUNDLES_DB --schema PIPELINE
```

Submit the Spark analytics job asynchronously by POSTing to the `/api/v2/code-bundle-executions` endpoint. First, generate a JWT for authentication (this requires [key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth) configured on your CLI connection).

Run the following in your terminal:

```bash
SNOWFLAKE_TOKEN=$(snow connection generate-jwt)
```

Now submit the job:


```bash
curl -X POST \
  "https://<account_identifier>.snowflakecomputing.com/api/v2/code-bundle-executions?asyncExec=true" \
  -H "Authorization: Bearer ${SNOWFLAKE_TOKEN}" \
  -H "X-Snowflake-Authorization-Token-Type: KEYPAIR_JWT" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "User-Agent: myApplicationName/1.0" \
  -H "X-Snowflake-Role: ACCOUNTADMIN" \
  -H "X-Snowflake-Warehouse: CB_WH" \
  -H "X-Snowflake-Database: CODE_BUNDLES_DB" \
  -H "X-Snowflake-Schema: PIPELINE" \
  -d '{
    "from_location": "@CODE_BUNDLES_DB.PIPELINE.SPARK_STAGE",
    "entrypoint": "spark_analytics.py",
    "arguments": ["--events-table", "CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS",
                   "--funnel-output", "CODE_BUNDLES_DB.PIPELINE.FUNNEL_METRICS",
                   "--pairs-output", "CODE_BUNDLES_DB.PIPELINE.PRODUCT_PAIRS"],
    "specification": {
      "bundle": {
        "type": "spark",
        "compute_type": "warehouse",
        "language": "python",
        "compute_options": {}
      }
    }
  }'
```

An async submission returns `202 Accepted` with a `job_id` you use to check status or cancel the run:

```json
{
  "code": "392604",
  "message": "Request execution in progress.",
  "job_id": "01c51743-c819-4261-0000-5349586311aa"
}
```

Check status with:

```bash
curl -X GET \
  "https://<account_identifier>.snowflakecomputing.com/api/v2/code-bundle-executions/<job_id>" \
  -H "Authorization: Bearer ${SNOWFLAKE_TOKEN}" \
  -H "X-Snowflake-Authorization-Token-Type: KEYPAIR_JWT" \
  -H "Accept: application/json" \
  -H "User-Agent: myApplicationName/1.0" \
  -H "X-Snowflake-Role: ACCOUNTADMIN" \
  -H "X-Snowflake-Database: CODE_BUNDLES_DB" \
  -H "X-Snowflake-Schema: PIPELINE"
```

> **Note:** The `X-Snowflake-Database` and `X-Snowflake-Schema` headers are required on the GET status endpoint. Without them, the response will be an empty array.

For details on the REST API, including idempotent submission and the full specification reference, see [Submit Spark jobs on Snowflake](https://docs.snowflake.com/en/developer-guide/code-bundles/spark-code-bundles#submit-with-rest).

### Submit from a stage with SQL

You can also submit the Spark job with SQL instead of the REST API, which integrates natively with Snowflake Tasks for scheduling. This uses the same stage we created above:

```sql
EXECUTE CODE BUNDLE FROM '@CODE_BUNDLES_DB.PIPELINE.SPARK_STAGE'
  ENTRYPOINT = 'spark_analytics.py'
  ARGUMENTS  = (
    '--events-table', 'CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS',
    '--funnel-output', 'CODE_BUNDLES_DB.PIPELINE.FUNNEL_METRICS',
    '--pairs-output', 'CODE_BUNDLES_DB.PIPELINE.PRODUCT_PAIRS'
  )
  WITH SPECIFICATION $$
bundle:
  type: spark
  compute_type: warehouse
  language: python
  compute_options: {}
$$;
```

### Submit from a stored bundle

Alternatively, if you've already created a stored bundle, you can run it as such:

```bash
snow sql -q "
USE DATABASE CODE_BUNDLES_DB;
USE SCHEMA PIPELINE;
USE WAREHOUSE CB_WH;
EXECUTE CODE BUNDLE CLICKSTREAM_PIPELINE
  ENTRYPOINT = 'spark_analytics.py'
  ARGUMENTS  = (
    '--events-table', 'CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS',
    '--funnel-output', 'CODE_BUNDLES_DB.PIPELINE.FUNNEL_METRICS',
    '--pairs-output', 'CODE_BUNDLES_DB.PIPELINE.PRODUCT_PAIRS'
  )
  WITH SPECIFICATION \$\$
bundle:
  type: spark
  compute_type: warehouse
  language: python
  compute_options: {}
\$\$;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

Note that in the stage-based and stored-bundle examples above, the `WITH SPECIFICATION` override replaces the stored spec entirely. Every required field must be repeated, even if it hasn't changed. This is helpful when a single bundle contains files that need different runtimes. For example, a Python sessionizer and a Spark analytics job in the same project, each run with its own spec.

In our pipeline, the Spark job runs on the session warehouse and writes FUNNEL_METRICS and PRODUCT_PAIRS. The output is an empty result row, which indicates a successful run. The actual results are in the tables the job wrote – we'll query them next.

<!-- ------------------------ -->
## Query the results

Let's explore the funnel metrics and product co-occurrence data.

Which traffic sources convert best?

```bash
snow sql -q "SELECT TRAFFIC_SOURCE, DEVICE, SESSIONS, CONVERSION_RATE, DROP_OFF_PCT FROM FUNNEL_METRICS WHERE STEP = 'purchase' ORDER BY CONVERSION_RATE DESC;" --database CODE_BUNDLES_DB --schema PIPELINE
```

You should see clear differences: some traffic sources convert significantly better than others, and device type matters.

Where do users drop off in the funnel?

```bash
snow sql -q "SELECT STEP, SESSIONS, CONVERSION_RATE, DROP_OFF_PCT FROM FUNNEL_METRICS WHERE TRAFFIC_SOURCE = 'organic' AND DEVICE = 'desktop' ORDER BY STEP_ORDER;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Watch the `SESSIONS` column shrink at each step. The `DROP_OFF_PCT` column shows what percentage of sessions failed to advance from the previous step.

Which products are frequently browsed together?

```bash
snow sql -q "SELECT PRODUCT_A, CATEGORY_A, PRODUCT_B, CATEGORY_B, CO_OCCURRENCE_COUNT, LIFT FROM PRODUCT_PAIRS ORDER BY LIFT DESC LIMIT 20;" --database CODE_BUNDLES_DB --schema PIPELINE
```

A `LIFT` score above 1.0 means the pair appears together more often than random chance. The top pairs with high lift and high co-occurrence count are your strongest "customers also viewed" candidates.

<!-- ------------------------ -->
## Orchestrate the pipeline with a Task

A pipeline should run on a schedule without you manually triggering it. Because `EXECUTE CODE BUNDLE` is a SQL statement, you can wrap each stage in a Snowflake Task and chain them into a graph without needing an external scheduler.

Let's create two tasks. First, the root task – it runs **sessionize.py** on a nightly schedule:

```bash
snow sql -q "
CREATE OR REPLACE TASK SESSIONIZE_TASK
  WAREHOUSE = CB_WH
  SCHEDULE  = 'USING CRON 0 2 * * * UTC'
AS
  EXECUTE CODE BUNDLE CLICKSTREAM_PIPELINE
    ENTRYPOINT = 'sessionize.py'
    ARGUMENTS  = ('--source-table', 'RAW_EVENTS',
                  '--output-table', 'SESSIONS',
                  '--inactivity-minutes', '30');
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

The analytics task runs after the sessionizer succeeds. The `AFTER` clause chains them into a dependency graph:

```bash
snow sql -q "
CREATE OR REPLACE TASK ANALYTICS_TASK
  WAREHOUSE = CB_WH
  AFTER SESSIONIZE_TASK
AS
  EXECUTE CODE BUNDLE CLICKSTREAM_PIPELINE
    ENTRYPOINT = 'spark_analytics.py'
    ARGUMENTS  = (
      '--events-table', 'CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS',
      '--funnel-output', 'CODE_BUNDLES_DB.PIPELINE.FUNNEL_METRICS',
      '--pairs-output', 'CODE_BUNDLES_DB.PIPELINE.PRODUCT_PAIRS'
    )
    WITH SPECIFICATION \$\$
bundle:
  type: spark
  compute_type: warehouse
  language: python
  compute_options: {}
\$\$;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

Here's what the code does:

- SESSIONIZE_TASK is the root task, scheduled nightly at 2:00 AM UTC
- ANALYTICS_TASK runs `AFTER` the root task, forming a two-step graph
- Each task runs one stage of the pipeline as a Code Bundle – same project, but with different entrypoints and specs

Tasks are created in a suspended state, by default. Resume the child task first, then the root – this ensures the graph is fully wired before the root fires. Then trigger a run to test it:

```bash
snow sql -q "ALTER TASK ANALYTICS_TASK RESUME; ALTER TASK SESSIONIZE_TASK RESUME; EXECUTE TASK SESSIONIZE_TASK;" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

> **Important:** An active root task runs on its schedule and consumes credits. Suspend it with `snow sql -q "ALTER TASK SESSIONIZE_TASK SUSPEND;" --database CODE_BUNDLES_DB --schema PIPELINE` when you're done testing.

<!-- ------------------------ -->
## Operate in production

Getting a job to run is one thing; operating it and iterating on it is another. Code Bundles give you versioning, asynchronous execution, and full run history out of the box.

### Ship a new version

As you iterate on your pipeline – fixing a bug, tuning the sessionization window, adding a new analytics step – you need to push the latest code to Snowflake. You can ship newer versions of the Code Bundle by recreating the bundle with `--overwrite` to replace it with your current local files (equivalent to `CREATE OR REPLACE` in SQL):

```bash
snow bundle create CLICKSTREAM_PIPELINE --source . --exclude ".venv/**" --exclude "setup.sql" --overwrite --database CODE_BUNDLES_DB --schema PIPELINE
```

> **Note:** If you create your bundle from a stage or workspace instead of a local directory, you can use `snow bundle alter CLICKSTREAM_PIPELINE --add-version @STAGE/path` to add immutable version snapshots without replacing the bundle.

### Run asynchronously

For long jobs, the `--async` flag submits the run and returns immediately with a query ID instead of waiting for it to finish:

```bash
snow bundle execute CLICKSTREAM_PIPELINE --entrypoint sessionize.py --async \
  --database CODE_BUNDLES_DB --schema PIPELINE \
  -- --source-table RAW_EVENTS --output-table SESSIONS --inactivity-minutes 30
```

You'll see output like `Request submitted. Query ID: 01c51743-c819-4261-0000-5349586311aa`. Use the ID returned to you to check on the run:

```bash
# Replace with the query ID returned by your --async run
snow bundle status 01c51743-c819-4261-0000-5349586311aa
```

### Review run history

The `CODE_BUNDLE_HISTORY` table function returns a record for every job run:

```bash
snow sql -q "SELECT ENTRYPOINT, STATUS, BUNDLE_TYPE, COMPUTE_TYPE, START_TIME, END_TIME, ERROR_MESSAGE FROM TABLE(INFORMATION_SCHEMA.CODE_BUNDLE_HISTORY(BUNDLE_NAME => 'CLICKSTREAM_PIPELINE', RESULT_LIMIT => 20)) ORDER BY START_TIME DESC;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Example output:

```bash
+----------------------------------------------------------------------------------------------------------------------------------+
| ENTRYPOINT         | STATUS | BUNDLE_TYPE | COMPUTE_TYPE | START_TIME                | END_TIME                  | ERROR_MESSAGE |
|--------------------+--------+-------------+--------------+---------------------------+---------------------------+---------------|
| spark_analytics.py | DONE   | SPARK       | WAREHOUSE    | 2026-08-27 07:52:07-07:00 | 2026-08-27 07:53:16-07:00 |               |
| sessionize.py      | DONE   | CUSTOM      | WAREHOUSE    | 2026-08-26 15:09:22-07:00 | 2026-08-26 15:09:32-07:00 |               |
+----------------------------------------------------------------------------------------------------------------------------------+
```


### Search logs and stack traces

If you configure an [event table](https://docs.snowflake.com/en/developer-guide/logging-tracing/event-table-setting-up) for your account, Code Bundle runs automatically emit application logs there – tagged with the run's query ID. You can filter by severity (`ERROR`, `FATAL`) to surface stack traces when a run fails, without needing to reproduce the issue.

Look at the `STATUS` column in the history results – a successful run shows `DONE`, and a failure carries details in `ERROR_MESSAGE`. That's your production loop: version, run, monitor, debug.

<!-- ------------------------ -->
## (Optional) Train a model on a compute pool

When your job requires powerful compute – training a model, running on GPUs, or installing packages from any source – a compute pool is the right compute type for your job run. Compute pools provide you with a full Python runtime powered by Snowpark Container Services.

Create a small compute pool:

```bash
snow sql -q "CREATE COMPUTE POOL IF NOT EXISTS CB_ML_POOL MIN_NODES = 1 MAX_NODES = 1 INSTANCE_FAMILY = CPU_X64_S;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Wait for the pool to reach IDLE or ACTIVE state before proceeding (this typically takes 1–3 minutes):

```bash
snow sql -q "DESCRIBE COMPUTE POOL CB_ML_POOL;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Here's the compute pool specification – compare it to the warehouse and Spark specs we've used so far. The key differences are `compute_type: compute_pool`, a named pool, and a Container Runtime version:

```yaml
bundle:
  type: custom
  compute_type: compute_pool
  language: python
  compute_options:
    compute_pool: CB_ML_POOL
    query_warehouse: CB_WH
    runtime_version: 'V2.5-CPU-PY3.11'
```

**train_model.py** trains a scikit-learn model to predict purchase amount from product and category, then logs it to the Snowflake Model Registry:

```python
import argparse
import pandas as pd
from snowflake.ml.registry import Registry
from snowflake.snowpark.context import get_active_session

def main() -> None:
    args = parse_args()  # --source-table, --database, --schema, --model-name, --version
    session = get_active_session()

    rows = session.table(args.source_table).filter(
        "EVENT_TYPE = 'purchase'"
    ).select("PRODUCT_ID", "CATEGORY", "REVENUE").collect()
    df = pd.DataFrame([row.as_dict() for row in rows])
    # ... fit a scikit-learn pipeline ...
    registry = Registry(session=session, database_name=args.database, schema_name=args.schema)
    registry.log_model(model, model_name=args.model_name, version_name=args.version,
                       sample_input_data=X.head())
```

Run it with `WITH SPECIFICATION` to override the stored warehouse spec, just like we did for the Spark job:

```bash
snow sql -q "
USE DATABASE CODE_BUNDLES_DB;
USE SCHEMA PIPELINE;
USE WAREHOUSE CB_WH;
EXECUTE CODE BUNDLE CLICKSTREAM_PIPELINE
  ENTRYPOINT = 'train_model.py'
  ARGUMENTS  = (
    '--source-table', 'CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS',
    '--database', 'CODE_BUNDLES_DB',
    '--schema', 'PIPELINE'
  )
  WITH SPECIFICATION \$\$
bundle:
  type: custom
  compute_type: compute_pool
  language: python
  compute_options:
    compute_pool: CB_ML_POOL
    query_warehouse: CB_WH
    runtime_version: 'V2.5-CPU-PY3.11'
\$\$;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

Here's what the code does:

- Reads purchase events directly from Snowflake with the injected session
- Trains the model in the Python process on the compute pool
- Registers the model so it's versioned and ready for batch inference

A successful run will return a confirmation that the statement was executed successfully.

<!-- ------------------------ -->
## Clean up

Let's remove everything we created. First, suspend and drop the tasks, then the bundle and remaining objects:

```bash
snow sql -q "
ALTER TASK IF EXISTS SESSIONIZE_TASK SUSPEND;
DROP TASK IF EXISTS ANALYTICS_TASK;
DROP TASK IF EXISTS SESSIONIZE_TASK;
DROP CODE BUNDLE IF EXISTS CLICKSTREAM_PIPELINE;
DROP COMPUTE POOL IF EXISTS CB_ML_POOL;
DROP DATABASE IF EXISTS CODE_BUNDLES_DB;
DROP WAREHOUSE IF EXISTS CB_WH;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You migrated a clickstream pipeline onto Snowflake as a Code Bundle – without rewriting your jobs as stored procedures. You sessionized 50K events on a warehouse, ran PySpark analytics as a native Spark job from the same bundle, orchestrated both stages with a Task, and operated the pipeline with versioning, async execution, and run history.

The theme throughout was matching compute to the job – a warehouse for the SQL-heavy sessionization, a Spark job for the combinatorial analytics – while keeping the project together as one deployment unit. You deployed once and ran different files with different runtimes, without duplicating shared code or decomposing into one object per script.

### What You Learned
- How to package a project as a Code Bundle and run it on Snowflake compute
- How to run a Python job on a warehouse and a PySpark job as a native Spark job
- How to override a bundle's specification at execution time with `WITH SPECIFICATION`
- How to orchestrate a multi-stage pipeline with a Snowflake Task
- How to version, run asynchronously, and monitor Code Bundle jobs in production

### Related Resources
- [Snowflake Code Bundles documentation](https://docs.snowflake.com/en/developer-guide/code-bundles/code-bundles)
- [Submit Spark jobs on Snowflake](https://docs.snowflake.com/en/developer-guide/code-bundles/spark-code-bundles)
- [Code Bundles Quickstart companion repo](https://github.com/Snowflake-Labs/sfguide-run-python-and-spark-jobs-with-code-bundles)
- [Snowflake Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Snowpark Connect for Apache Spark](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)

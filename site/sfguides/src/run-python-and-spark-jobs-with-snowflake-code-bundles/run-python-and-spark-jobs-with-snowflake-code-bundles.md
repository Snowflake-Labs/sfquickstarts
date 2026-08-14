author: Gilberto Hernandez, Snowflake CoCo
id: run-python-and-spark-jobs-with-snowflake-code-bundles
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Run Python, PySpark as a native Spark job, and orchestrate it all with a Task, using Snowflake Code Bundles.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-run-python-and-spark-jobs-with-code-bundles

# Run Python and Spark Jobs on Snowflake with Code Bundles
<!-- ------------------------ -->
## Overview

> **Note:** Code Bundles are in Public Preview.

You have a nightly pipeline running on a Spark cluster. A Python script sessionizes raw clickstream events, a PySpark job computes conversion funnels and product affinity scores, and a cron entry glues the two together. The events already land in Snowflake, but the pipeline runs somewhere else: on infrastructure you provision, patch, and pay for whether it's processing data or not.

You could rewrite both jobs as stored procedures, but that means matching handler signatures, re-declaring packages, and splitting a project that works as a unit into separate database objects.

In this Quickstart, we'll skip all of that. We'll take the pipeline as-is – the Python sessionizer, the PySpark analytics, the shared helpers – package it as a single **Code Bundle**, and run each file on the compute that fits: the sessionizer on a warehouse (it's SQL-based), and the PySpark job as a native Spark job, with no Spark cluster required. By the end, you'll have the pipeline scheduled on a Task and producing fictional funnel metrics from ~50K clickstream events.

### What You'll Learn
- How to package a project as a Code Bundle and run it on Snowflake compute
- How to run a Python job on a **warehouse** with `EXECUTE CODE BUNDLE`
- How to lift-and-shift an existing **PySpark** analytics job as a native Spark job – no cluster, no rewrites
- How to override a bundle's specification at execution time with `WITH SPECIFICATION`
- How to orchestrate a multi-stage pipeline with a Snowflake **Task**
- How to version, run asynchronously, and monitor your jobs in production

### What You'll Need
- A Snowflake account **enrolled in the Code Bundles Public Preview**, with a role that can create warehouses and databases (for example, **ACCOUNTADMIN**)
- The development build of the [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) with Code Bundle support:
  ```bash
  uv tool install git+https://github.com/snowflakedb/snowflake-cli@code
  # or: pip install git+https://github.com/snowflakedb/snowflake-cli@code
  ```
- A configured Snowflake CLI connection (verify with `snow connection list`)
- Basic familiarity with Python, PySpark, and SQL

### What You'll Build
- A two-stage clickstream pipeline – a warehouse Python sessionizer and a native Spark analytics job – packaged as a Code Bundle and orchestrated as a scheduled Task:

```console
   RAW_EVENTS (50K clickstream events)
      │
      ▼
 ┌──────────────────────────────┐   Code Bundle (warehouse Python)
 │  sessionize.py               │   assign sessions from inactivity gaps,
 │                              │   compute per-session metrics
 └──────────────────────────────┘
      │  SESSIONS
      ▼
 ┌──────────────────────────────┐   Code Bundle (Spark job)
 │  spark_analytics.py          │   conversion funnels by traffic source,
 │                              │   product co-occurrence with lift scores
 └──────────────────────────────┘
      │  FUNNEL_METRICS + PRODUCT_PAIRS
      ▼
   Scheduled nightly by a Snowflake Task
```

Let's get started!

<!-- ------------------------ -->
## Set up your account

Let's create the objects our pipeline needs and generate the clickstream data. We'll produce ~50K events across 1,000 users, 200 products, 10 categories, and 30 days – enough to produce meaningful funnels and co-occurrence patterns.

From the companion repo, run the setup script:

```bash
snow sql -f setup.sql
```

If you prefer Snowsight, open **notebook.ipynb** and run the setup cells instead.

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

CREATE STAGE IF NOT EXISTS CODE_BUNDLE_STAGE;
```

The full **setup.sql** generates a `PRODUCTS` dimension table (200 products across 10 categories) and a `RAW_EVENTS` table with ~50K clickstream events. Events follow a realistic funnel shape: ~40% page views, ~30% product views, ~20% add-to-carts, and ~10% purchases, distributed across five traffic sources (organic, paid search, social, email, direct) and three device types.

Run the full **setup.sql**. At the end you should see a verification query confirming ~50K total events with the expected funnel distribution.

<!-- ------------------------ -->
## Explore the pipeline code

The pipeline you're migrating is just Python. Let's look at both stages before we deploy them – the important part is that we don't change them to run on Snowflake.

Clone the companion repo and open the project:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-run-python-and-spark-jobs-with-code-bundles
cd sfguide-run-python-and-spark-jobs-with-code-bundles
```

### Stage 1: The sessionizer (`sessionize.py`)

This job reads raw events and assigns session IDs based on 30-minute inactivity gaps – a standard sessionization pattern. It then computes per-session metrics: duration, event counts by type, revenue, and whether the session converted.

```python
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

Here's what the code does:

- Uses `LAG` to find the previous event per user, then flags new sessions wherever the gap exceeds 30 minutes
- Aggregates events within each session into metrics (page views, carts, purchases, revenue)
- Writes a `SESSIONS` table – one row per session with dimensions (device, traffic source) carried forward

The key detail is `get_session()` in **helpers.py**. It calls `get_active_session()` – and that single line is what lets the same file run in both places:

```python
from snowflake.snowpark.context import get_active_session

def get_session() -> Session:
    try:
        return get_active_session()
    except Exception:
        raise RuntimeError("No active Snowpark session found. ...")
```

Locally, `get_active_session()` connects via your **connections.toml**. When this same file runs as a Code Bundle, Snowflake injects the session at runtime – no credentials in your code. **You write the script once and run it anywhere.**

The wrapper in `helpers.py` isn't required – all you need is `get_active_session()`. We use a shared helper here because both `sessionize.py` and `spark_analytics.py` import from it, which is a natural pattern when a project has multiple entrypoints sharing utility code.

### Stage 2: The Spark analytics (`spark_analytics.py`)

This is standard PySpark – `SparkSession`, DataFrames, window functions. Nothing about it is Snowflake-specific:

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("clickstream_analytics").getOrCreate()

    events = spark.table(args.events_table)

    # Funnel analysis: step-by-step conversion per traffic_source × device
    funnel = build_funnel(events)
    funnel.write.mode("overwrite").saveAsTable(args.funnel_output)

    # Product co-occurrence: which products are browsed together?
    pairs = build_product_pairs(events)
    pairs.write.mode("overwrite").saveAsTable(args.pairs_output)
```

Here's what the analytics compute:

- **Funnel analysis** – for each traffic source and device type, how many users reached each step (page view → product view → cart → purchase), with conversion rates and drop-off at each stage
- **Product co-occurrence** – within each user's browsing history, which products appear together and how much more often than chance (lift score)

Both of these are textbook PySpark patterns: iterative aggregation over user-level event sequences and combinatorial pair generation. On Snowflake, the Spark DataFrame API runs directly on the Snowflake engine (powered by **Snowpark Connect**), so there's no Spark cluster to stand up or manage. You bring the code you already have and run it with zero changes.

<!-- ------------------------ -->
## Run the sessionizer on a warehouse

Now let's run **sessionize.py** on Snowflake. Because this job orchestrates SQL window functions over Snowflake data, a warehouse is the right compute – no compute pool to provision.

A single file, **code_bundle.yml**, describes the default way the bundle runs. It's a default, not a contract – you can override it per-run when a different file in the project needs different settings (we'll do exactly that for the Spark job later):

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

- **compute_type: warehouse** – run on the warehouse set in the session, with no compute pool to manage
- **runtime_version: '3.11'** – the Python version for the run (always quote the value)
- **requirements_file** – packages to install, resolved from Snowflake's PyPI proxy

From the project root, create the Code Bundle from your local files and run it. We'll name the bundle **CLICKSTREAM_PIPELINE**:

> **Note:** The CLI needs to know which database and schema to create the bundle in. You can pass `--database` and `--schema` on each command (as shown below), or add `database = "CODE_BUNDLES_DB"` and `schema = "PIPELINE"` to your connection in **connections.toml** so you don't have to repeat them.

```bash
snow bundle create CLICKSTREAM_PIPELINE --source . --exclude "venv/**" --database CODE_BUNDLES_DB --schema PIPELINE
```

Now run the sessionizer. Everything after `--` is passed straight to your script's `argparse`:

```bash
snow bundle execute CLICKSTREAM_PIPELINE \
  --entrypoint sessionize.py \
  --database CODE_BUNDLES_DB --schema PIPELINE \
  -- --source-table RAW_EVENTS \
     --output-table SESSIONS \
     --inactivity-minutes 30
```

When the run finishes, confirm the output. You should see thousands of sessions:

```bash
snow sql -q "SELECT COUNT(*) AS total_sessions, SUM(CASE WHEN CONVERTED THEN 1 ELSE 0 END) AS converted, ROUND(AVG(DURATION_SECONDS)) AS avg_duration_sec FROM CODE_BUNDLES_DB.PIPELINE.SESSIONS;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Your first job is running on Snowflake – sessionizing 50K events into structured sessions with no rewrite, no stored procedure.

<!-- ------------------------ -->
## Run the Spark analytics

If you prefer Snowsight, open **notebook.ipynb** and run the cells under "Run the Spark analytics job."

Both `sessionize.py` and `spark_analytics.py` live in the same project and share `helpers.py`. The bundle keeps them together as a single deployment unit – you don't create a second bundle for a second script. Instead, you run a different file with a different spec.

Our stored specification says `type: custom` and `compute_type: warehouse` (the Python sessionizer). This run is a Spark job, so we need a different spec. Compare it to the one we used before – the key difference is `type: spark` and `runtime_version: '1.29'` (the Spark runtime):

```yaml
bundle:
  type: spark
  compute_type: warehouse
  language: python
  compute_options:
    runtime_version: '1.29'
```

We pass this inline at execution time with **WITH SPECIFICATION**, which overrides the stored **code_bundle.yml** for this one run:

```bash
snow sql -q "
EXECUTE CODE BUNDLE CLICKSTREAM_PIPELINE
  ENTRYPOINT = 'spark_analytics.py'
  ARGUMENTS  = (
    '--events-table', 'CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS',
    '--sessions-table', 'CODE_BUNDLES_DB.PIPELINE.SESSIONS',
    '--funnel-output', 'CODE_BUNDLES_DB.PIPELINE.FUNNEL_METRICS',
    '--pairs-output', 'CODE_BUNDLES_DB.PIPELINE.PRODUCT_PAIRS'
  )
  WITH SPECIFICATION \$\$
bundle:
  type: spark
  compute_type: warehouse
  language: python
  compute_options:
    runtime_version: '1.29'
\$\$;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

Here's what this does:

- **type: spark** tells Snowflake to run the file as a Spark application
- **WITH SPECIFICATION** overrides the bundle's stored **code_bundle.yml** for this one run – same project, different runtime
- The Spark job runs on the session warehouse and writes **FUNNEL_METRICS** and **PRODUCT_PAIRS**

You just ran an existing PySpark analytics pipeline on Snowflake – no cluster provisioned, no cluster to shut down, no infrastructure to manage.

<!-- ------------------------ -->
## Query the results

If you prefer Snowsight, open **notebook.ipynb** and run the cells under "Query the results."

This is what the pipeline produced. Let's explore the funnel metrics and product co-occurrence data.

**Which traffic sources convert best?**

```bash
snow sql -q "SELECT TRAFFIC_SOURCE, DEVICE, VISITORS, CONVERSION_RATE FROM FUNNEL_METRICS WHERE STEP = 'purchase' ORDER BY CONVERSION_RATE DESC;" --database CODE_BUNDLES_DB --schema PIPELINE
```

You should see clear differences: some traffic sources convert significantly better than others, and device type matters. This is the kind of insight that drives marketing spend decisions.

**Where do users drop off in the funnel?**

```bash
snow sql -q "SELECT STEP, VISITORS, CONVERSION_RATE FROM FUNNEL_METRICS WHERE TRAFFIC_SOURCE = 'organic' AND DEVICE = 'desktop' ORDER BY STEP_ORDER;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Watch the `VISITORS` column shrink at each step. The biggest absolute drop-off tells you where to focus UX improvements.

**Which products are frequently browsed together?**

```bash
snow sql -q "SELECT PRODUCT_A, CATEGORY_A, PRODUCT_B, CATEGORY_B, CO_OCCURRENCE_COUNT, LIFT FROM PRODUCT_PAIRS ORDER BY LIFT DESC LIMIT 20;" --database CODE_BUNDLES_DB --schema PIPELINE
```

A `LIFT` score above 1.0 means the pair appears together more often than random chance. The top pairs with high lift and high co-occurrence count are your strongest "customers also viewed" candidates.

<!-- ------------------------ -->
## Orchestrate the pipeline with a Task

If you prefer Snowsight, open **notebook.ipynb** and run the cells under "Orchestrate with a Task."

A pipeline should run on a schedule without you triggering it. Because `EXECUTE CODE BUNDLE` is a SQL statement, you can wrap each stage in a Snowflake **Task** and chain them into a graph – no external scheduler.

Let's create two tasks. First, the root task – it runs the sessionizer on a nightly schedule:

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

The analytics task runs after the sessionizer succeeds – the `AFTER` clause chains them into a dependency graph:

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
      '--sessions-table', 'CODE_BUNDLES_DB.PIPELINE.SESSIONS',
      '--funnel-output', 'CODE_BUNDLES_DB.PIPELINE.FUNNEL_METRICS',
      '--pairs-output', 'CODE_BUNDLES_DB.PIPELINE.PRODUCT_PAIRS'
    )
    WITH SPECIFICATION \$\$
bundle:
  type: spark
  compute_type: warehouse
  language: python
  compute_options:
    runtime_version: '1.29'
\$\$;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

Here's what the code does:

- **SESSIONIZE_TASK** is the root task, scheduled nightly at 2:00 AM UTC
- **ANALYTICS_TASK** runs `AFTER` the root task, forming a two-step graph
- Each task runs one stage of the pipeline as a Code Bundle – same project, different entrypoints and specs

Tasks are created suspended. Resume the graph from the child up to the root, then trigger a run to test it:

```bash
snow sql -q "ALTER TASK ANALYTICS_TASK RESUME; ALTER TASK SESSIONIZE_TASK RESUME; EXECUTE TASK SESSIONIZE_TASK;" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

> **Important:** A resumed root task runs on its schedule and consumes credits. Suspend it with `snow sql -q "ALTER TASK SESSIONIZE_TASK SUSPEND;" --database CODE_BUNDLES_DB --schema PIPELINE` when you're done testing.

<!-- ------------------------ -->
## Operate in production

If you prefer Snowsight, open **notebook.ipynb** and run the cells under "Operate in production."

Getting a job to run is one thing; operating it is another. Code Bundles give you versioning, asynchronous execution, and full run history out of the box.

**Ship a new version.** As you iterate on your pipeline – fixing a bug, tuning the sessionization window, adding a new analytics step – you need to push the latest code to Snowflake. Re-create the bundle with `--overwrite` to replace it with your current local files (equivalent to `CREATE OR REPLACE` in SQL):

```bash
snow bundle create CLICKSTREAM_PIPELINE --source . --exclude "venv/**" --overwrite --database CODE_BUNDLES_DB --schema PIPELINE
```

> **Note:** If you create your bundle from a stage or workspace instead of a local directory, you can use `snow bundle alter CLICKSTREAM_PIPELINE --add-version @STAGE/path` to add immutable version snapshots without replacing the bundle.

**Run asynchronously.** For long jobs, the `--async` flag submits the run and returns immediately with a query ID instead of waiting for it to finish:

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

**Review run history.** The `CODE_BUNDLE_HISTORY` table function returns a record for every run – warehouse or Spark:

```bash
snow sql -q "SELECT ENTRYPOINT, STATUS, BUNDLE_TYPE, COMPUTE_TYPE, START_TIME, END_TIME, ERROR_MESSAGE FROM TABLE(INFORMATION_SCHEMA.CODE_BUNDLE_HISTORY(BUNDLE_NAME => 'CLICKSTREAM_PIPELINE', RESULT_LIMIT => 20)) ORDER BY START_TIME DESC;" --database CODE_BUNDLES_DB --schema PIPELINE
```

**Find logs and stack traces.** If you configure an [event table](https://docs.snowflake.com/en/developer-guide/logging-tracing/event-table-setting-up) for your account, Code Bundle runs automatically emit application logs there – tagged with the run's query ID. You can filter by severity (`ERROR`, `FATAL`) to surface stack traces when a run fails, without needing to reproduce the issue.

Look at the `STATUS` column in the history results – a successful run shows `DONE`, and a failure carries details in `ERROR_MESSAGE`. That's your production loop: version, run, monitor, debug.

<!-- ------------------------ -->
## (Optional) Train a model on a compute pool

If you prefer Snowsight, open **notebook.ipynb** and run the cells under "Train a model on a compute pool."

When the heavy lifting happens in your code rather than in pushed-down SQL – training a model, running on GPUs, or installing packages from any source – a **compute pool** is the right target. It gives you a full Python runtime powered by Snowpark Container Services.

Create a small compute pool:

```bash
snow sql -q "CREATE COMPUTE POOL IF NOT EXISTS CB_ML_POOL MIN_NODES = 1 MAX_NODES = 1 INSTANCE_FAMILY = CPU_X64_S;" --database CODE_BUNDLES_DB --schema PIPELINE
```

Wait for the pool to reach IDLE state before proceeding (this takes about 20–30 seconds):

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
  properties:
    requirements_file: requirements-ml.txt
```

**train_model.py** trains a scikit-learn model to predict purchase amount from product and category, then logs it to the Snowflake **Model Registry**:

```python
from snowflake.ml.registry import Registry
from snowflake.snowpark.context import get_active_session

session = get_active_session()
rows = session.table("CODE_BUNDLES_DB.PIPELINE.RAW_EVENTS").filter(
    "EVENT_TYPE = 'purchase'"
).select("PRODUCT_ID", "CATEGORY", "REVENUE").collect()
df = pd.DataFrame([row.as_dict() for row in rows])
# ... fit a scikit-learn pipeline ...
registry = Registry(session=session, database_name="CODE_BUNDLES_DB", schema_name="PIPELINE")
registry.log_model(model, model_name="PURCHASE_AMOUNT_PREDICTOR", version_name="v1",
                   sample_input_data=X.head())
```

Run it with `WITH SPECIFICATION` to override the stored warehouse spec, just like we did for the Spark job:

```bash
snow sql -q "
EXECUTE CODE BUNDLE CLICKSTREAM_PIPELINE
  ENTRYPOINT = 'train_model.py'
  WITH SPECIFICATION \$\$
bundle:
  type: custom
  compute_type: compute_pool
  language: python
  compute_options:
    compute_pool: CB_ML_POOL
    query_warehouse: CB_WH
    runtime_version: 'V2.5-CPU-PY3.11'
  properties:
    requirements_file: requirements-ml.txt
\$\$;
" --database CODE_BUNDLES_DB --schema PIPELINE --warehouse CB_WH
```

Here's what the code does:

- Reads purchase events directly from Snowflake with the injected session
- Trains the model in the Python process on the compute pool
- Registers the model so it's versioned and ready for batch inference

<!-- ------------------------ -->
## Clean up

If you prefer Snowsight, open **notebook.ipynb** and run the cells under "Clean up."

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

Congratulations! You migrated a real clickstream pipeline onto Snowflake as a Code Bundle – without rewriting your jobs as stored procedures. You sessionized 50K events on a warehouse, ran PySpark funnel and co-occurrence analytics as a native Spark job, queried the results, orchestrated the stages with a Task, and operated the pipeline with versioning, async execution, and run history.

The theme throughout was matching compute to the job – a warehouse for the SQL-heavy sessionization, a Spark job for the combinatorial analytics – while keeping the project together as one deployment unit. You deployed once and ran different files with different runtimes, without duplicating shared code or decomposing into one object per script. Bring the code you already have, and run it where your data already lives.

### What You Learned
- How to package a project as a Code Bundle and run it on Snowflake compute
- How to run a Python job on a warehouse and a PySpark job as a native Spark job
- How to override a bundle's specification at execution time with `WITH SPECIFICATION`
- How to orchestrate a multi-stage pipeline with a Snowflake Task
- How to version, run asynchronously, and monitor Code Bundle jobs in production

### Related Resources
- [Snowflake Code Bundles documentation](https://docs.snowflake.com/en/LIMITEDACCESS/code-bundles/code-bundles)
- [Submit Spark jobs on Snowflake](https://docs.snowflake.com/en/LIMITEDACCESS/code-bundles/spark-code-bundles)
- [Code Bundles Quickstart companion repo](https://github.com/Snowflake-Labs/sfguide-run-python-and-spark-jobs-with-code-bundles)
- [Snowflake Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Snowpark Connect for Apache Spark](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)

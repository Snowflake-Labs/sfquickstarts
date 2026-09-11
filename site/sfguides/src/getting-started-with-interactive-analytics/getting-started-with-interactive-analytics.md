author: Chanin Nantasenamat
id: getting-started-with-interactive-analytics
summary: This guide demonstrates how to set up and use Snowflake's Interactive Analytics to achieve sub-second query performance.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/interactive-warehouse
language: en
environments: web
status: Published

# Getting Started with Snowflake Interactive Analytics

## Overview

When it comes to near real-time (or sub-second) analytics, the ideal scenario involves achieving consistent, rapid query performance and managing costs effectively, even with large datasets and high user demand. 

Snowflake's new Interactive Warehouses are designed to deliver on these needs. They provide a high-concurrency, low-latency serving layer for near real-time analytics, and can query your existing standard tables directly through zero-copy interactive analytics, with no data conversion required. This allows consistent, sub-second query performance for live dashboards and APIs with great price-for-performance. With this end-to-end solution, you can avoid operational complexities and tool sprawl.

### What You'll Learn
- The core concepts behind Snowflake's Interactive Warehouses and how they provide low-latency analytics.
- How to create and configure an Interactive Warehouse using SQL.
- How zero-copy interactive analytics lets an interactive warehouse query your standard tables directly, with no data conversion required.
- How to attach a table to an Interactive Warehouse to pre-warm the data cache for faster queries.
- A methodology for benchmarking and comparing the query latency and throughput of an interactive warehouse versus a standard warehouse.

### What You'll Build

You will build a complete, functioning interactive analytics environment in Snowflake, including a dedicated Interactive Warehouse configured to query your data directly. You will also create a Python-based performance test that executes queries against both your interactive warehouse and a standard warehouse, culminating in benchmark charts that visually demonstrate the latency and throughput improvements.

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Basic knowledge of SQL and Python.
- Familiarity with data warehousing and performance concepts.
- A Snowflake role with privileges to create warehouses and tables (*i.e.*, `SYSADMIN` is used in the notebook).

## Understand Interactive Warehouses

To boost query performance for interactive, sub-second analytics, Snowflake introduces the interactive warehouse: a specialized compute engine tuned for low-latency, high-concurrency workloads.

### Interactive Warehouses
An interactive warehouse tunes the Snowflake engine specially for low-latency, interactive workloads. This type of warehouse is optimized to run continuously, serving high volumes of concurrent queries. All interactive warehouses run on the latest generation of hardware. Through zero-copy interactive analytics, an interactive warehouse can query your standard tables, Iceberg tables, and dynamic tables directly, with no conversion required.

### Zero-copy interactive analytics

An interactive warehouse can query the following table types directly:

- **Standard tables.** Your existing Snowflake tables are queryable with no `CREATE INTERACTIVE TABLE` step.
- **Iceberg tables.** Open-format Iceberg data served at interactive latency.
- **Dynamic tables.** Incrementally refreshed results that an interactive warehouse can query directly.

The setup is straightforward. Create an interactive warehouse, optionally attach your highest-priority tables for proactive cache warming, then query any standard table directly:

```sql
-- 1. Create an interactive warehouse
CREATE OR REPLACE INTERACTIVE WAREHOUSE analytics_iwh
  WAREHOUSE_SIZE = 'XSMALL';

-- 2. (Optional) Attach high-priority tables for proactive caching
ALTER WAREHOUSE analytics_iwh
  ADD TABLES (your_db.your_schema.critical_table_1, your_db.your_schema.critical_table_2);

-- 3. Query any standard table, no conversion needed
USE WAREHOUSE analytics_iwh;
SELECT * FROM your_db.your_schema.any_standard_table WHERE ...;
```

With this pattern, `ADD TABLES` is a performance optimization, not a requirement: attaching a table proactively warms the cache, but unattached tables are still fully queryable and cached on demand when first accessed. The hands-on demo below follows this exact pattern, querying a standard table directly on an interactive warehouse.

> Note: Before zero-copy interactive analytics, the only way to query data at interactive latency was to convert it into an interactive table. Interactive tables still exist and remain supported, mainly for compatibility with earlier interactive analytics setups. For new work, Snowflake recommends querying your standard tables directly through zero-copy interactive analytics instead.

### Use cases
Interactive warehouses are built for one specific shape of work: simple, repetitive queries that must return in well under a second, run at high concurrency, against fresh data, and at a low cost per query. These aren't the complex, long-running transformations you'd send to a standard warehouse. Instead, they're the same handful of query patterns executed over and over, by thousands of users and, increasingly, by AI agents. Wherever that pattern shows up, an interactive warehouse is a strong fit.

![](assets/use-cases.png)

Three domains capture where it matters most:

- **AI & Agents.** Agentic and AI-driven applications fire off large volumes of small, concurrent queries, such as a retrieval step here or a metric lookup there, and each one needs to come back instantly and cheaply. Interactive warehouses make this practical for low-cost RAG retrieval, AI observability (monitoring model and agent behavior in near real time), and high-concurrency MCP servers that expose your data to many agents at once.
- **Customer-Facing Data Apps.** When query latency is visible to your end users, consistency matters as much as raw speed. Interactive warehouses power data APIs that serve predictable, sub-second responses to customer-facing applications, embedded analytics inside your product, and live dashboards that stay responsive even under heavy, simultaneous use.
- **Operational Analytics.** Internal, decision-driving workloads depend on fresh data and fast answers. Interactive warehouses suit trading and risk management, infrastructure observability and alerting (high-throughput monitoring where every second counts), and supply chain and inventory tracking that must reflect the latest state of the business.

What unites all of these is the same set of requirements, namely low latency, high concurrency, fresh data, and low cost per query, met by simple queries repeated at scale. That is exactly the workload interactive warehouses were designed for.


### Limitations

The queries that work best with interactive warehouses are usually `SELECT` statements with selective `WHERE` clauses, optionally including a `GROUP BY` clause on a few dimensions.

Here are some limitations of interactive warehouses:
- An interactive warehouse is designed to stay up and running. It supports auto-suspend and auto-resume, but the minimum auto-suspend interval is 24 hours (86400 seconds), so it suspends only after 24 hours of inactivity. You can also suspend and resume it manually. Either way, expect significant query latency right after a resume, while the data cache warms up again.
- Interactive warehouses cancel any query that runs longer than 5 seconds, since they're tuned for short, low-latency queries. To protect p99 latency, configure a fallback warehouse so those queries are transparently re-run on a standard warehouse (see the "Configure a fallback warehouse" section below).
- You can't run `CALL` commands to call stored procedures through interactive warehouse

<!-- ------------------------ -->
## Setup

### Data operations

> Note: The companion notebook creates all of these objects automatically using the `{{DB_NAME}}` and `{{STANDARD_WH_NAME}}` variables defined in the "Set common variables" cell. The steps below show the equivalent manual SQL. If running outside the notebook, replace `{{DB_NAME}}` and `{{STANDARD_WH_NAME}}` with your own names (e.g. `JSMITH_MY_DEMO_DB` and `JSMITH_STD_WH`).

#### Optional: Create warehouse

In order to load data into a standard table, you'll need to use a standard warehouse.
You can use any existing warehouse or create a new one, here we'll create a new warehouse called `{{STANDARD_WH_NAME}}`:

```sql
CREATE OR REPLACE WAREHOUSE {{STANDARD_WH_NAME}} WITH WAREHOUSE_SIZE='X-SMALL';
```

#### Step 1: Create a Database and Schema

First, we'll start by creating a database called `{{DB_NAME}}` and `BENCHMARK_FDN` as a schema:

```sql
CREATE DATABASE IF NOT EXISTS {{DB_NAME}};
CREATE SCHEMA IF NOT EXISTS {{DB_NAME}}.BENCHMARK_FDN;
```

#### Step 2: Create a new stage
Next, we'll create a stage called `my_csv_stage` where the CSV file will soon be stored:

```sql
-- Define database and schema to use
USE SCHEMA {{DB_NAME}}.BENCHMARK_FDN;

-- Create a stage that includes the definition for the CSV file format
CREATE OR REPLACE STAGE my_csv_stage
  FILE_FORMAT = (
    TYPE = 'CSV'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  );
```

#### Step 3: Upload CSV to a stage

1. In the Snowflake UI, navigate to the database/schema that you've created (`{{DB_NAME}}.BENCHMARK_FDN`).
2. Go to the `my_csv_stage` stage
3. Upload the [`synthetic_hits_data.csv`](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Interactive_Analytics/synthetic_hits_data.csv) file to this stage.

#### Step 4: Create the Table and Load Data

Now that we have the CSV file in the stage, we'll need to create the `HITS2_CSV` table and extract contents from the CSV file into it.

```sql
-- Use your database and schema
USE SCHEMA {{DB_NAME}}.BENCHMARK_FDN;

-- Create the table with the correct data types
CREATE OR REPLACE TABLE HITS2_CSV (
    EventDate DATE,
    CounterID INT,
    ClientIP STRING,
    SearchEngineID INT,
    SearchPhrase STRING,
    ResolutionWidth INT,
    Title STRING,
    IsRefresh INT,
    DontCountHits INT
);

-- Copy the data from your stage into the table
-- Make sure to replace 'my_csv_stage' with your stage name
COPY INTO HITS2_CSV FROM @my_csv_stage/synthetic_hits_data.csv
  FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);
```

#### Step 5: Query the data

Finally, we'll now retrieve contents from the table by performing a simple query with the `SELECT` statement:

```sql
USE WAREHOUSE {{STANDARD_WH_NAME}};
SELECT * FROM {{DB_NAME}}.BENCHMARK_FDN.HITS2_CSV LIMIT 100;
```

This essentially retrieves data from the `{{DB_NAME}}` database, `BENCHMARK_FDN` schema and `HITS2_CSV` table:

![](assets/hits2csv-data.png)

<!-- ------------------------ -->
## Performance demo of Snowflake's Interactive Warehouses

To proceed with carrying out this performance comparison of an interactive warehouse against a standard one, you can download notebook file [Getting_Started_with_Interactive_Analytics.ipynb](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Interactive_Analytics/Getting_Started_with_Interactive_Analytics.ipynb) provided in the repo.

### Set common variables

First, we'll derive session-scoped variable names from your Snowflake username. This ensures database and warehouse names are unique per user and avoids conflicts when multiple users run the notebook on the same account:

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
USER = session.sql("SELECT CURRENT_USER()").collect()[0][0]
DB_NAME = f'{USER}_MY_DEMO_DB'
INTERACTIVE_WH_NAME = f'{USER}_INT_WH'
STANDARD_WH_NAME = f'{USER}_STD_WH'

print(f"User: {USER}\nDatabase: {DB_NAME}\nInteractive WH: {INTERACTIVE_WH_NAME}\nStandard WH: {STANDARD_WH_NAME}")
```

### Set up role, warehouse, and database

Interactive Warehouses are now generally available (GA) and enabled by default on your account, so there's no need to check the Snowflake version or verify any account parameters.

The following SQL cell creates the standard warehouse, database, and schemas used throughout the notebook. All statements use `IF NOT EXISTS`, so this cell is safe to re-run:

```sql
USE ROLE SYSADMIN;

-- Create the compute and database objects used throughout this notebook (idempotent)
CREATE WAREHOUSE IF NOT EXISTS {{STANDARD_WH_NAME}} WITH WAREHOUSE_SIZE = 'X-SMALL';
CREATE DATABASE IF NOT EXISTS {{DB_NAME}};

CREATE SCHEMA IF NOT EXISTS {{DB_NAME}}.BENCHMARK_FDN;

USE WAREHOUSE {{STANDARD_WH_NAME}};
USE DATABASE {{DB_NAME}};
```

> Note: In a Snowflake Notebook, SQL and Python cells share the same session. Any `USE ROLE`, `USE DATABASE`, or `USE WAREHOUSE` statement you run in a SQL cell also applies to subsequent Python cells (and vice versa).

### Create an interactive warehouse

![](assets/create-turn-on-interactive-warehouse.png)

Next, let's create our interactive warehouse using a SQL cell:

```sql
CREATE OR REPLACE INTERACTIVE WAREHOUSE {{INTERACTIVE_WH_NAME}}
    WAREHOUSE_SIZE = 'XSMALL'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 1
    COMMENT = 'Interactive warehouse demo';
```

### Data setup and loading

Before loading data, ensure the standard warehouse is active:

```sql
USE WAREHOUSE {{STANDARD_WH_NAME}};
```

The following Python cell creates the `HITS2_CSV` table and loads it from the `synthetic_hits_data.csv` file bundled with the notebook. The load is idempotent: it checks whether the table already contains rows and, if so, skips the load on subsequent runs.

> Note: The data is loaded from the bundled CSV using `pandas` and `write_pandas` with no external network access required. Make sure `synthetic_hits_data.csv` is added to the notebook's files.

```python
import pandas as pd

DB, SCHEMA, TABLE = DB_NAME, "BENCHMARK_FDN", "HITS2_CSV"
FQ = f"{DB}.{SCHEMA}.{TABLE}"
CSV_FILE = "synthetic_hits_data.csv"  # bundled with this notebook

# Create the source table if it doesn't already exist
session.sql(f"""
CREATE TABLE IF NOT EXISTS {FQ} (
    EventDate DATE,
    CounterID INT,
    ClientIP STRING,
    SearchEngineID INT,
    SearchPhrase STRING,
    ResolutionWidth INT,
    Title STRING,
    IsRefresh INT,
    DontCountHits INT
)
""").collect()

# Idempotent load: only load when the table is empty
row_count = session.sql(f"SELECT COUNT(*) FROM {FQ}").collect()[0][0]
if row_count > 0:
    print(f"{FQ} already has {row_count:,} rows. Skipping data load.")
else:
    print(f"Loading data into {FQ} ...")
    pdf = pd.read_csv(CSV_FILE)
    pdf["EventDate"] = pd.to_datetime(pdf["EventDate"]).dt.date    
    session.write_pandas(pdf, TABLE, database=DB, schema=SCHEMA, quote_identifiers=False)
    row_count = session.sql(f"SELECT COUNT(*) FROM {FQ}").collect()[0][0]
    print(f"Loaded {row_count:,} rows into {FQ}.")
```

The bundled CSV has 100,000 rows, which is too small to show a clear concurrency advantage. The following Python cell scales the table up to roughly 2 million rows by replicating the loaded data 20 times with small jittered variations (a randomized `ClientIP` and `ResolutionWidth`, and a small `EventDate` offset), so each replicated batch looks like distinct traffic rather than exact duplicates. This step is also idempotent: it checks the row count first and skips the expansion if the table has already been scaled up.

```python
TARGET_MULTIPLIER = 20

row_count = session.sql(f"SELECT COUNT(*) FROM {FQ}").collect()[0][0]
if row_count >= TARGET_MULTIPLIER * 100_000 * 0.9:
    print(f"{FQ} already has {row_count:,} rows. Skipping data expansion.")
else:
    print(f"Expanding {FQ} to roughly {TARGET_MULTIPLIER * 100_000:,} rows ...")
    session.sql(f"""
        INSERT INTO {FQ}
        SELECT
            DATEADD(day, UNIFORM(-3, 3, RANDOM()), t.EventDate),
            t.CounterID,
            CONCAT(TO_VARCHAR(UNIFORM(1, 255, RANDOM())), '.', TO_VARCHAR(UNIFORM(1, 255, RANDOM())), '.',
                   TO_VARCHAR(UNIFORM(1, 255, RANDOM())), '.', TO_VARCHAR(UNIFORM(1, 255, RANDOM()))),
            t.SearchEngineID,
            t.SearchPhrase,
            GREATEST(1, t.ResolutionWidth + UNIFORM(-100, 100, RANDOM())),
            t.Title,
            t.IsRefresh,
            t.DontCountHits
        FROM {FQ} AS t, TABLE(GENERATOR(ROWCOUNT => {TARGET_MULTIPLIER - 1})) AS g
    """).collect()
    row_count = session.sql(f"SELECT COUNT(*) FROM {FQ}").collect()[0][0]
    print(f"Expanded {FQ} to {row_count:,} rows.")
```

We can then verify the loaded data with a quick query:

```sql
USE WAREHOUSE {{STANDARD_WH_NAME}};
SELECT * FROM {{DB_NAME}}.BENCHMARK_FDN.HITS2_CSV LIMIT 100;
```

This essentially retrieves data from the database, `BENCHMARK_FDN` schema and `HITS2_CSV` table:

![](assets/hits2csv-data.png)

### Attach a table to the interactive warehouse

![](assets/attach-standard-table-to-warehouse.png)

Next, we'll attach our standard table to the interactive warehouse, which pre-warms the data cache for optimal query performance:

```sql
USE DATABASE {{DB_NAME}};
ALTER WAREHOUSE {{INTERACTIVE_WH_NAME}} ADD TABLES(BENCHMARK_FDN.HITS2_CSV);
```

> Note: `ADD TABLES` is a performance optimization, not a requirement. It proactively warms the warehouse's data cache so queries avoid a cold start. Any table you don't attach is still queryable and gets cached on demand the first time it's accessed. Proactive warming is currently limited to 10 tables.

### Configure a fallback warehouse

Interactive warehouses are tuned for short, sub-second queries, so Snowflake fixes their statement timeout at a maximum of 5 seconds and automatically cancels any query that runs longer. To make sure an occasional heavy or ad-hoc query still completes instead of failing, you can designate a **fallback warehouse**: a standard warehouse that automatically re-runs any query that exceeds the 5-second timeout on the interactive warehouse.

This retry is transparent to the client (it behaves as an internal retry), so the query still returns its result. It keeps fast dashboard queries responsive while isolating them from the occasional long-running query.

We'll reuse the standard warehouse created earlier as the fallback, then confirm the setting via the `FALLBACK_WAREHOUSE` column:

```sql
ALTER WAREHOUSE {{INTERACTIVE_WH_NAME}} SET FALLBACK_WAREHOUSE = {{STANDARD_WH_NAME}};

SHOW WAREHOUSES LIKE '{{INTERACTIVE_WH_NAME}}';
```

A few things to keep in mind about fallback warehouses:
- The fallback is a **standard** warehouse and can be shared with non-interactive workloads. Choose a size that's the same as or larger than the interactive warehouse.
- It must be started (or set to auto-resume) to accept retried queries, and standard credit consumption applies once it's active.
- The querying role needs `USAGE` on both the interactive warehouse and its fallback warehouse. Setting a fallback requires `ALTER WAREHOUSE` on the interactive warehouse and `USAGE` on the fallback.
- When a retry occurs, the time spent on the interactive warehouse before the retry appears as `fault_handling_time` in the query profile.
- To remove the fallback warehouse later, run `ALTER WAREHOUSE {{INTERACTIVE_WH_NAME}} UNSET FALLBACK_WAREHOUSE;`.

### Sequential Query Benchmark

To directly compare performance, we'll benchmark both the interactive and standard warehouses over 50 sequential runs and plot their latencies side-by-side in a grouped bar chart:

```python
import time
import numpy as np

cursor = session.connection.cursor()

runs = 50

def run_and_measure(count, mode):
    wh = INTERACTIVE_WH_NAME if mode == "iw" else STANDARD_WH_NAME
    table = "BENCHMARK_FDN.HITS2_CSV"
    query = f"""
        SELECT SearchEngineID, ClientIP, COUNT(*) AS c, SUM(IsRefresh), AVG(ResolutionWidth)
        FROM {table}
        WHERE SearchPhrase <> ''
        GROUP BY SearchEngineID, ClientIP
        ORDER BY c DESC LIMIT 10
    """
    cursor.execute(f"USE WAREHOUSE {wh}")
    cursor.execute('ALTER SESSION SET USE_CACHED_RESULT = FALSE;')

    timings = []
    for _ in range(count + 1):
        t0 = time.time()
        cursor.execute(query).fetchall()
        timings.append(time.time() - t0)
    return timings[1:] # skip warm-up run

counts_iw = run_and_measure(runs, "iw")
print(counts_iw)

counts_std = run_and_measure(runs, "std")
print(counts_std)
```

The first chart plots per-run latency side-by-side:

```python
import matplotlib.pyplot as plt

titles = [(i+1) for i in range(0, len(counts_iw))]

x = np.arange(len(titles))  # the label locations
width = 0.35  # bar width

fig, ax = plt.subplots(figsize=(15, 5))
ax.bar(x - width/2, counts_std, width, label="Standard", color="#5B5B5B")
ax.bar(x + width/2, counts_iw, width, label="Interactive", color="#29B5E8")

ax.set_ylabel("Latency")
ax.set_xlabel("Query run")
ax.set_title("Standard vs Interactive warehouse")
ax.set_xticks(x)
ax.set_xticklabels(titles)
ax.legend(
    loc='upper center',
    bbox_to_anchor=(0.5, -0.15),
    ncol=2
)
plt.show()
```

![](assets/sequential-benchmark-std-vs-int-wh.png)

The second chart compares mean latency with standard deviation error bars:

```python
# Calculate means and standard deviations for error bars
mean_std = np.mean(counts_std)
mean_iw = np.mean(counts_iw)
std_std = np.std(counts_std)
std_iw = np.std(counts_iw)

fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(["Standard", "Interactive"], [mean_std, mean_iw],
              yerr=[std_std, std_iw], capsize=8,
              color=["#5B5B5B", "#29B5E8"], width=0.5)

ax.set_ylabel("Latency (seconds)")
ax.set_title("Standard vs Interactive warehouse\n(mean over {} runs with std dev)".format(len(counts_std)))
plt.tight_layout()
plt.show()
```

![](assets/sequential-benchmark-std-vs-int-wh-50runs.png)

### Concurrent Query Benchmark

To simulate real-world dashboard load, we'll stress-test both warehouses with concurrent queries. The benchmark uses a mixed query pool (light, medium, and heavy queries) with staggered Poisson-distributed arrivals, ramping from 1 to 8 concurrent workers. It measures server-side latency (p50, p90, p99) and throughput (queries per second) across multiple rounds for statistical reliability.

```python
import random, time, numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

QUERY_TEMPLATES = {
    "light": "SELECT * FROM {table} WHERE CounterID = 62 LIMIT 1",
    "medium": """SELECT SearchEngineID, ClientIP, COUNT(*) AS c, SUM(IsRefresh), AVG(ResolutionWidth)
        FROM {table} WHERE SearchPhrase <> ''
        GROUP BY SearchEngineID, ClientIP ORDER BY c DESC LIMIT 10""",
    "heavy": """SELECT EventDate, COUNT(*) AS hits, COUNT(DISTINCT ClientIP) AS unique_ips,
        AVG(ResolutionWidth), SUM(CASE WHEN SearchPhrase <> '' THEN 1 ELSE 0 END)
        FROM {table} GROUP BY EventDate ORDER BY EventDate""",
}

def build_query_pool(table):
    return [(k, v.format(table=table)) for k, v in QUERY_TEMPLATES.items()]

def worker(conn, wh_name, query_pool, n_queries=6, arrival_rate=5):
    cur = conn.cursor()
    cur.execute(f"USE WAREHOUSE {wh_name}")
    cur.execute("ALTER SESSION SET USE_CACHED_RESULT = FALSE")
    latencies = []
    for _ in range(n_queries):
        time.sleep(random.expovariate(arrival_rate))
        _, query = random.choice(query_pool)
        cur.execute(query).fetchall()
        qid = cur.sfqid
        ms = cur.execute(f"SELECT TOTAL_ELAPSED_TIME FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_SESSION()) WHERE QUERY_ID = '{qid}'").fetchone()[0]
        latencies.append(ms / 1000.0)
    cur.close()
    return latencies

def run_concurrent_benchmark(conn, wh_name, table, concurrency_levels, rounds=10):
    query_pool = build_query_pool(table)
    all_results = []
    for n in concurrency_levels:
        print(f"  concurrency={n} ({rounds} rounds) ...", end=" ", flush=True)
        round_stats = []
        for _ in range(rounds):
            t0 = time.time()
            with ThreadPoolExecutor(max_workers=n) as pool:
                futures = [pool.submit(worker, conn, wh_name, query_pool) for _ in range(n)]
                lats = [l for f in as_completed(futures) for l in f.result()]
            wall = time.time() - t0
            round_stats.append({"p50": np.percentile(lats, 50), "p90": np.percentile(lats, 90),
                                "p99": np.percentile(lats, 99), "throughput_qps": len(lats) / wall})
        result = {"concurrency": n}
        for m in ["p50", "p90", "p99", "throughput_qps"]:
            vals = [r[m] for r in round_stats]
            result[f"{m}_mean"], result[f"{m}_std"] = np.mean(vals), np.std(vals)
        all_results.append(result)
        print(f"p50={result['p50_mean']:.3f}s(±{result['p50_std']:.3f})  p90={result['p90_mean']:.3f}s(±{result['p90_std']:.3f})  qps={result['throughput_qps_mean']:.1f}(±{result['throughput_qps_std']:.1f})")
    return all_results

concurrency_levels = [1, 2, 4, 8]
conn = session.connection

print("Interactive warehouse:")
results_iw = run_concurrent_benchmark(conn, INTERACTIVE_WH_NAME, "BENCHMARK_FDN.HITS2_CSV", concurrency_levels)

print("\nStandard warehouse:")
results_std = run_concurrent_benchmark(conn, STANDARD_WH_NAME, "BENCHMARK_FDN.HITS2_CSV", concurrency_levels)

print(f"\nBenchmark complete ({run_concurrent_benchmark.__defaults__[0]} rounds per level).")
```

The results are visualized in two side-by-side charts:

- **Concurrency vs Latency.** Shows how p50, p90, and p99 change as concurrent workers increase. A flat line means the warehouse handles more load without slowing down.
- **Concurrency vs Throughput.** Shows queries per second at each concurrency level. Higher is better; a plateau indicates the warehouse is saturated.

```python
import matplotlib.pyplot as plt

benchmark_rounds = run_concurrent_benchmark.__defaults__[0]
levels = [r["concurrency"] for r in results_iw]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

for results, label, color in [(results_std, "Standard", "#5B5B5B"), (results_iw, "Interactive", "#29B5E8")]:
    for metric, marker, ls, alpha in [("p50", "o", "-", 1.0), ("p90", "s", "--", 0.6), ("p99", "^", ":", 0.4)]:
        ax1.errorbar(levels, [r[f"{metric}_mean"] for r in results],
                     yerr=[r[f"{metric}_std"] for r in results],
                     fmt=f"{marker}{ls}", color=color, alpha=alpha, capsize=4, label=f"{label} {metric}")

ax1.set(xlabel="Concurrent Workers", ylabel="Latency (seconds)", xticks=levels)
ax1.set_ylim(bottom=0)
ax1.set_title(f"Concurrency vs Latency (lower is better)\nmean ± std over {benchmark_rounds} rounds")
ax1.legend(fontsize=7, ncol=2)
ax1.grid(True, alpha=0.3)

x = np.arange(len(levels))
w = 0.35
for results, label, color, offset in [(results_std, "Standard", "#5B5B5B", -w/2), (results_iw, "Interactive", "#29B5E8", w/2)]:
    ax2.bar(x + offset, [r["throughput_qps_mean"] for r in results], w,
            yerr=[r["throughput_qps_std"] for r in results], capsize=4, label=label, color=color)

ax2.set(xlabel="Concurrent Workers", ylabel="Queries / Second", xticks=x)
ax2.set_xticklabels(levels)
ax2.set_title(f"Concurrency vs Throughput (higher is better)\nmean ± std over {benchmark_rounds} rounds")
ax2.legend()
ax2.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.show()
```

![](assets/concurrency-benchmark.png)

A final cell dynamically generates a written interpretation of the results, comparing the two warehouses across every concurrency level and surfacing scaling issues, tail latency spikes, throughput plateaus, and actionable suggestions when the interactive warehouse underperforms.

## Conclusion and Resources

In this guide, we explored how to address the challenge of low-latency, near real-time analytics using Snowflake's interactive warehouses. We walked through the complete setup process, from creating the necessary database objects and loading data to configuring and attaching a standard table to an interactive warehouse via zero-copy interactive analytics. The sequential and concurrent performance benchmarks clearly demonstrated the substantial latency and throughput improvements this provides over a standard warehouse, across both individual query runs and high-concurrency workloads. This confirms its value as a powerful solution for demanding use cases like live dashboards and high-throughput data APIs, where sub-second performance is critical.

### What You Learned
- The core concepts behind Snowflake's Interactive Warehouses and how they deliver low-latency analytics for use cases like live dashboards and APIs.
- How zero-copy interactive analytics lets an interactive warehouse query your standard, Iceberg, and dynamic tables directly, with no conversion required.
- How to create, configure, and attach a table to an interactive warehouse using SQL to prepare a high-performance analytics environment.
- How to run a sequential benchmark and visualize per-run latency and mean latency with standard deviation to prove interactive performance gains.
- How to simulate real-world concurrent dashboard load and measure p50, p90, p99 latency and throughput across multiple concurrency levels.

### Related Resources

Data and Notebook:
- [synthetic_hits_data.csv](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Interactive_Analytics/synthetic_hits_data.csv)
- [Getting_Started_with_Interactive_Analytics.ipynb](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Interactive_Analytics/Getting_Started_with_Interactive_Analytics.ipynb)

Documentation:
- [Snowflake interactive analytics](https://docs.snowflake.com/en/user-guide/interactive)
- [Zero-copy interactive analytics: using standard and Iceberg tables](https://docs.snowflake.com/en/user-guide/interactive#using-standard-and-iceberg-tables-public-preview)

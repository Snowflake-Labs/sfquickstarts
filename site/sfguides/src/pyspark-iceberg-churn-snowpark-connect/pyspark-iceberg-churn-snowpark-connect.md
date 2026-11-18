author: Vino Duraisamy
id: pyspark-iceberg-churn-snowpark-connect
language: en
summary: Run an existing PySpark churn pipeline on Snowflake with Snowpark Connect for Spark, writing Apache Iceberg tables with partitions, tags, incremental reads, time travel and Write-Audit-Publish branches.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/apache-iceberg, snowflake-site:taxonomy/snowflake-feature/snowpark
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Run PySpark on Apache Iceberg Tables with Snowpark Connect for Spark
<!-- ------------------------ -->
## Overview

StreamCo, a fictional streaming company, wants to know which subscribers are about to cancel. Their data team already has a churn pipeline written in PySpark. In this Quickstart, we'll run that pipeline unchanged on Snowflake using **Snowpark Connect for Spark**, and store every layer as an open **Apache Iceberg** table.

Along the way we'll use the Iceberg features data engineers reach for most: day partitions, partition overwrites, tags, incremental reads, changelogs, time travel and Write-Audit-Publish (WAP) on branches. Everything runs on Snowflake-managed Iceberg tables, so there's no cloud storage or external catalog to set up.

### Prerequisites
- A Snowflake account (or [free trial](https://signup.snowflake.com/))
- Familiarity with Python and PySpark

### What You'll Learn
- How to start a Spark session on Snowflake with Snowpark Connect for Spark
- How to read staged files with Spark and write Iceberg tables with DataFrameWriterV2
- How to partition, overwrite partitions and set table properties on Iceberg tables
- How to bookmark a snapshot with an Iceberg tag and read it back with time travel
- How to process only changed rows with incremental reads and the changelog
- How to gate bad data with Write-Audit-Publish on Iceberg branches
- How to inspect lineage with Iceberg metadata tables

### What You'll Need
- A Snowflake account with the ACCOUNTADMIN role (or an admin who can run the role & grants block below)
- Access to **Workspaces** notebooks in Snowsight
- Basic familiarity with PySpark DataFrames

### What You'll Build
- A bronze, silver and gold churn pipeline on Snowflake-managed Iceberg tables, driven entirely by PySpark
- A churn feature table with an explainable risk score, tagged at its training snapshot
- A WAP flow that rejects a broken data batch and publishes a clean one

<!-- ------------------------ -->
## Setup: Role & Grants

Before we begin, we'll create a dedicated role for this Quickstart and grant it the privileges you'll need. If you don't have ACCOUNTADMIN access in your Snowflake account, send the SQL block below to your Snowflake admin — they can review and run it to provision the role on your behalf.

The role needs to create one database, use a warehouse, run a Workspaces notebook on a compute pool and install packages from the shared PyPI repository.

```sql
-- Run as ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;

-- 1. Create the role for this Quickstart
CREATE ROLE IF NOT EXISTS SCOS_CHURN_ROLE;

-- 2. Grant the role to the user who will run the Quickstart
GRANT ROLE SCOS_CHURN_ROLE TO USER <your_username>;

-- 3. Warehouse privileges
CREATE WAREHOUSE IF NOT EXISTS SCOS_CHURN_WH WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60;
GRANT USAGE ON WAREHOUSE SCOS_CHURN_WH TO ROLE SCOS_CHURN_ROLE;

-- 4. Database & schema privileges
GRANT CREATE DATABASE ON ACCOUNT TO ROLE SCOS_CHURN_ROLE;

-- 5. Integration privileges
-- GRANT USAGE ON INTEGRATION <INT_NAME> TO ROLE SCOS_CHURN_ROLE;
-- -- N/A for this guide

-- 6. Future grants
-- GRANT SELECT ON FUTURE TABLES IN SCHEMA <DB_NAME>.<SCHEMA_NAME> TO ROLE SCOS_CHURN_ROLE;
-- -- N/A for this guide (the role owns everything it creates)

-- 7. Stage privileges
-- GRANT READ ON STAGE <STAGE_NAME> TO ROLE SCOS_CHURN_ROLE;
-- -- N/A for this guide (the role creates and owns its stage)

-- 8. Guide-specific grants
-- Run the Workspaces notebook on a compute pool
GRANT USAGE ON COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU TO ROLE SCOS_CHURN_ROLE;
-- Install snowpark-connect from the shared PyPI repository
GRANT DATABASE ROLE SNOWFLAKE.PYPI_REPOSITORY_USER TO ROLE SCOS_CHURN_ROLE;

-- 9. Switch into the role for the rest of the Quickstart
USE ROLE SCOS_CHURN_ROLE;
```

> **Note:** If you don't have ACCOUNTADMIN access, send the SQL block above to your Snowflake admin to run on your behalf. Once the role is granted, run `USE ROLE SCOS_CHURN_ROLE;` and continue with the Quickstart.

Now let's create the database, the bronze, silver and gold schemas, and an internal stage where raw files will land.

```sql
USE ROLE SCOS_CHURN_ROLE;
USE WAREHOUSE SCOS_CHURN_WH;

CREATE DATABASE IF NOT EXISTS CHURN_DEMO;
CREATE SCHEMA IF NOT EXISTS CHURN_DEMO.BRONZE;
CREATE SCHEMA IF NOT EXISTS CHURN_DEMO.SILVER;
CREATE SCHEMA IF NOT EXISTS CHURN_DEMO.GOLD;
CREATE STAGE IF NOT EXISTS CHURN_DEMO.BRONZE.RAW_LANDING DIRECTORY = (ENABLE = TRUE);
```

The output should confirm the creation of each object.

> **Note:** If a `CHURN_DEMO` database already exists in your account and is owned by another role, the stage creation fails with an insufficient privileges error. Pick a different database name here and set the same name in the notebook's `DB` variable.

<!-- ------------------------ -->
## Open the Notebook

The whole pipeline lives in one notebook. You can run the [companion notebook](assets/scos-iceberg-churn-demo.ipynb) cell by cell, or paste the code from each step of this guide into a new notebook.

1. Download **scos-iceberg-churn-demo.ipynb**.
2. In Snowsight, go to **Projects** > **Workspaces** and upload the file.
3. Open the notebook and connect it to a service running as **SCOS_CHURN_ROLE**.
4. Under **Artifact Repository**, select `snowflake.snowpark.pypi_shared_repository` so the notebook can install Snowpark Connect.

The first cell installs Snowpark Connect with Iceberg support.

```python
!pip install -q "snowpark-connect[iceberg]>=1.44.0"
```

> **Important:** Restart the kernel once the install finishes (**Connect** > **Restart kernel**), then continue with the next cell.

Next, set the configuration. Change `WAREHOUSE` if you used a different warehouse in the setup step.

```python
DB = "CHURN_DEMO"
WAREHOUSE = "SCOS_CHURN_WH"
N_CUSTOMERS = 50_000   # synthetic customers
DAYS = 60              # days of viewing history
```

<!-- ------------------------ -->
## Start a Spark Session

One Snowpark session drives everything: Spark through Snowpark Connect, plus the few Snowflake SQL statements Spark can't express. Snowpark Connect needs a current database and schema, so we set those first.

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
session.sql(f"USE WAREHOUSE {WAREHOUSE}").collect()
session.sql(f"USE SCHEMA {DB}.BRONZE").collect()
print(session.sql("SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()").collect()[0])
```

Now let's start Snowpark Connect on that session and get a regular `SparkSession` back.

```python
import logging
import time
from snowflake import snowpark_connect

logging.getLogger("snowflake_connect_server").setLevel(logging.WARNING)

snowpark_connect.start_session(snowpark_session=session)
spark = snowpark_connect.get_session()
spark.conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")

from pyspark.sql.connect import functions as F


def latest_snapshot(table):
    return spark.sql(f"SELECT snapshot_id FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1").collect()[0][0]


def with_retry(fn, attempts=5, wait_s=15):
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if "background maintenance" not in str(e) or i == attempts - 1:
                raise
            print(f"Table busy with background maintenance, retrying in {wait_s}s...")
            time.sleep(wait_s)


spark.sql("SELECT 1 AS ok").show()
```

Here's what the code does:

- Starts a Spark Connect server backed by your Snowflake session, so Spark code executes on your warehouse
- Enables the Iceberg SQL extensions, which add branches, tags and `VERSION AS OF`
- Imports functions from `pyspark.sql.connect`, because the classic `pyspark.sql.functions` would look for a local JVM
- Defines two helpers: one to fetch a table's latest snapshot ID, and one to retry a write that collides with Snowflake's background Iceberg maintenance

You should see a one-row table with `ok = 1`.

<!-- ------------------------ -->
## Generate Synthetic Data

Let's land raw files on the stage the way an upstream system would. The data is synthetic but has real signal: each customer gets a hidden risk value, and risky customers watch less over time, file more tickets and are more likely to cancel.

| Folder | Format | Content |
|---|---|---|
| initial/subscriptions/ | CSV | One row per customer: plan, monthly revenue, start and cancel dates |
| initial/usage_events/ | JSON lines | Viewing sessions over 60 days |
| initial/support_tickets/ | CSV | Tickets with a sentiment score |
| increment/usage_events/ | JSON lines | One new day of viewing, used for incremental processing |
| wap_bad/, wap_good/ | CSV | Two incoming subscription batches, used for Write-Audit-Publish |

```python
import csv
import io
import json
import random
from datetime import date, datetime, timedelta

random.seed(42)
START = date(2026, 8, 1)
STAGE = f"@{DB}.BRONZE.RAW_LANDING"
PLANS = [("basic", 7.99), ("standard", 15.49), ("premium", 22.99)]
DEVICES = ["tv", "mobile", "web", "tablet"]
SUB_HEADER = ["customer_id", "plan_tier", "mrr", "start_date", "cancel_date", "country"]


def risk(cid):
    return random.Random(cid).random()  # stable per customer


def put(path, text):
    session.file.put_stream(io.BytesIO(text.encode()), f"{STAGE}/{path}", auto_compress=False, overwrite=True)


def to_csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def usage_day(d):
    day = START + timedelta(days=d)
    rows = []
    for cid in random.sample(range(1, N_CUSTOMERS + 1), int(N_CUSTOMERS * 0.16)):
        r = risk(cid)
        base = 120 * (1 - r) * (1 - 0.6 * r * d / DAYS)  # risky users fade out
        ts = datetime.combine(day, datetime.min.time()) + timedelta(seconds=random.randint(0, 86_399))
        rows.append(json.dumps({"customer_id": f"C{cid:06d}", "event_ts": ts.isoformat(sep=" "),
                                "minutes_watched": max(1, int(random.gauss(base, 25))),
                                "device": random.choice(DEVICES)}))
    return rows


# Subscriptions
subs = []
for cid in range(1, N_CUSTOMERS + 1):
    plan, mrr = random.choice(PLANS)
    start = START - timedelta(days=random.randint(30, 900))
    cancel = (START + timedelta(days=random.randint(10, DAYS - 1))).isoformat() if risk(cid) > 0.82 else ""
    subs.append([f"C{cid:06d}", plan, mrr, start.isoformat(), cancel, random.choice(["US", "CA", "UK", "DE", "IN"])])
put("initial/subscriptions/subscriptions.csv", to_csv(SUB_HEADER, subs))

# Usage events, 10 days per file, plus one incremental day
for f in range(0, DAYS, 10):
    lines = [l for d in range(f, min(f + 10, DAYS)) for l in usage_day(d)]
    put(f"initial/usage_events/usage_{f // 10:03d}.json", "\n".join(lines))
put("increment/usage_events/usage_000.json", "\n".join(usage_day(DAYS)))

# Support tickets
tickets = []
for _ in range(int(N_CUSTOMERS * 0.6)):
    cid = random.randint(1, N_CUSTOMERS)
    r = risk(cid)
    if random.random() > 0.3 + r * 0.7:
        continue
    ts = datetime.combine(START + timedelta(days=random.randint(0, DAYS - 1)), datetime.min.time())
    tickets.append([f"C{cid:06d}", ts.isoformat(sep=" "), random.choice(["billing", "playback", "account", "content"]),
                    round(max(-1, min(1, random.gauss(0.4 - r, 0.3))), 2)])
put("initial/support_tickets/support_tickets.csv", to_csv(["customer_id", "ticket_ts", "category", "sentiment"], tickets))


# Two incoming batches for WAP: one broken billing export, one clean
def wap_batch(bad):
    rows = []
    for i in range(500):
        plan, mrr = random.choice(PLANS)
        cid = f"C{N_CUSTOMERS + i + 1:06d}"
        if bad and i % 7 == 0:
            cid = ""      # missing customer_id
        if bad and i % 11 == 0:
            mrr = -mrr    # negative revenue
        rows.append([cid, plan, mrr, (START + timedelta(days=DAYS)).isoformat(), "", "US"])
    return rows


put("wap_bad/subscriptions.csv", to_csv(SUB_HEADER, wap_batch(True)))
put("wap_good/subscriptions.csv", to_csv(SUB_HEADER, wap_batch(False)))

for r in session.sql(f"LIST {STAGE}").collect():
    print(f"{r['size']:>10,}  {r['name']}")
```

You should see a list of eleven files on the stage with their sizes.

<!-- ------------------------ -->
## Bronze: Raw Files to Iceberg

Standard Spark readers read straight from the Snowflake stage. Then `writeTo(...).using("iceberg")`, the **DataFrameWriterV2** API, lands each dataset as a Snowflake-managed Iceberg table.

```python
subs_raw = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{STAGE}/initial/subscriptions/")
usage_raw = spark.read.json(f"{STAGE}/initial/usage_events/")
tickets_raw = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{STAGE}/initial/support_tickets/")
subs_raw.printSchema()

for name, df in [("SUBSCRIPTIONS_RAW", subs_raw), ("USAGE_EVENTS_RAW", usage_raw), ("SUPPORT_TICKETS_RAW", tickets_raw)]:
    df.writeTo(f"{DB}.BRONZE.{name}").using("iceberg").createOrReplace()
    print(f"BRONZE.{name}: {spark.table(f'{DB}.BRONZE.{name}').count():,} rows")
```

You should see the inferred subscriptions schema, followed by a row count for each of the three bronze tables.

<!-- ------------------------ -->
## Silver: Clean, Type and Partition

The silver layer casts types, removes duplicates and aggregates viewing into one row per customer per day. Three Iceberg features show up here:

- `partitionedBy(F.days("event_date"))` creates a day-partitioned Iceberg table
- `tableProperty(...)` sets Iceberg table properties such as a comment and the format version
- Change tracking is turned on with Snowflake SQL, because Spark has no equivalent, so the changelog works later

```python
subs = (spark.table(f"{DB}.BRONZE.SUBSCRIPTIONS_RAW")
        .select("customer_id", "plan_tier", F.col("mrr").cast("double").alias("mrr"),
                F.to_date("start_date").alias("start_date"), F.to_date("cancel_date").alias("cancel_date"), "country")
        .dropDuplicates(["customer_id"]))
(subs.writeTo(f"{DB}.SILVER.SUBSCRIPTIONS").using("iceberg")
     .tableProperty("comment", "StreamCo subscriptions - validated via WAP")
     .tableProperty("format-version", "2")
     .createOrReplace())

usage = (spark.table(f"{DB}.BRONZE.USAGE_EVENTS_RAW")
         .withColumn("event_ts", F.to_timestamp("event_ts"))
         .groupBy("customer_id", F.to_date("event_ts").alias("event_date"))
         .agg(F.sum("minutes_watched").alias("minutes_watched"), F.count("*").alias("sessions")))
(usage.writeTo(f"{DB}.SILVER.USAGE_DAILY").using("iceberg")
      .partitionedBy(F.days("event_date"))
      .tableProperty("comment", "Daily viewing per customer")
      .createOrReplace())

(spark.table(f"{DB}.BRONZE.SUPPORT_TICKETS_RAW").withColumn("ticket_ts", F.to_timestamp("ticket_ts"))
     .writeTo(f"{DB}.SILVER.SUPPORT_TICKETS").using("iceberg").createOrReplace())

for t in ["SUBSCRIPTIONS", "USAGE_DAILY"]:
    session.sql(f"ALTER ICEBERG TABLE {DB}.SILVER.{t} SET CHANGE_TRACKING = TRUE").collect()
```

Now imagine a late-arriving correction for the last three days of viewing. Instead of rewriting the whole table, `overwritePartitions()` replaces only the day partitions present in the DataFrame.

```python
last_day = (START + timedelta(days=DAYS - 1)).isoformat()
fix = (usage.filter(F.col("event_date") >= F.date_sub(F.lit(last_day), 2))
            .withColumn("minutes_watched", F.col("minutes_watched") + 1))
with_retry(lambda: fix.writeTo(f"{DB}.SILVER.USAGE_DAILY").overwritePartitions())

spark.sql(f"SELECT partition, record_count FROM {DB}.SILVER.USAGE_DAILY.partitions ORDER BY partition DESC LIMIT 5").show(truncate=False)
for t in ["SUBSCRIPTIONS", "USAGE_DAILY", "SUPPORT_TICKETS"]:
    print(f"SILVER.{t}: {spark.table(f'{DB}.SILVER.{t}').count():,} rows")
```

The `.partitions` metadata table shows the five most recent day partitions and their record counts.

> **Note:** A write right after a table is created can collide with Snowflake's background Iceberg maintenance (error 093924). The `with_retry` helper waits and tries again.

<!-- ------------------------ -->
## Gold: Churn Features

The gold table has one row per customer with an explainable churn risk score from 0 to 100. It combines three signals: the recent usage trend, the number of support tickets and negative ticket sentiment. It stands in for a real model.

```python
AS_OF = (START + timedelta(days=DAYS)).isoformat()
GOLD = f"{DB}.GOLD.CHURN_FEATURES"


def churn_features(customer_filter=None):
    s = spark.table(f"{DB}.SILVER.SUBSCRIPTIONS")
    if customer_filter is not None:
        s = s.join(customer_filter, "customer_id", "left_semi")
    as_of = F.to_date(F.lit(AS_OF))
    u = spark.table(f"{DB}.SILVER.USAGE_DAILY").groupBy("customer_id").agg(
        F.sum(F.when(F.col("event_date") >= F.date_sub(as_of, 14), F.col("minutes_watched")).otherwise(0)).alias("mins_last_14d"),
        F.sum(F.when(F.col("event_date") < F.date_sub(as_of, 14), F.col("minutes_watched")).otherwise(0)).alias("mins_prior"),
        F.max("event_date").alias("last_active_date"))
    t = spark.table(f"{DB}.SILVER.SUPPORT_TICKETS").groupBy("customer_id").agg(
        F.count("*").alias("ticket_count"), F.round(F.avg("sentiment"), 2).alias("avg_sentiment"))
    f = (s.join(u, "customer_id", "left").join(t, "customer_id", "left")
         .fillna({"mins_last_14d": 0, "mins_prior": 0, "ticket_count": 0, "avg_sentiment": 0.0})
         .withColumn("tenure_days", F.datediff(as_of, "start_date"))
         .withColumn("usage_trend", F.round(F.col("mins_last_14d") / F.greatest(F.col("mins_prior") / 3.0, F.lit(1.0)), 2))
         .withColumn("churned", F.col("cancel_date").isNotNull()))
    score = (40 * (1 - F.least(F.col("usage_trend"), F.lit(1.0)))
             + 8 * F.least(F.col("ticket_count"), F.lit(5))
             + 20 * (F.col("avg_sentiment") < 0).cast("int"))
    return f.withColumn("churn_risk", F.round(F.least(score, F.lit(100.0)), 1)).select(
        "customer_id", "plan_tier", "mrr", "country", "tenure_days", "mins_last_14d", "usage_trend",
        "ticket_count", "avg_sentiment", "last_active_date", "churned", "churn_risk")


churn_features().writeTo(GOLD).using("iceberg").tableProperty("comment", "Churn model features").createOrReplace()
spark.table(GOLD).orderBy(F.col("churn_risk").desc()).show(5)
spark.sql(f"SELECT churned, count(*) customers, round(avg(churn_risk), 1) avg_risk FROM {GOLD} GROUP BY churned").show()
```

Here's what the code does:

- Compares minutes watched in the last 14 days with the prior period to get a usage trend
- Counts support tickets and averages their sentiment per customer
- Scores risk from those signals, capped at 100
- Wraps the logic in a function with an optional customer filter, so we can rescore a subset later

In the last result, customers who actually churned should have a clearly higher average risk.

Now let's bookmark this snapshot as the one the model was trained on. An Iceberg **tag** is a named, immutable pointer to one snapshot, so we can always get back to the exact training data.

```python
spark.sql(f"ALTER TABLE {GOLD} CREATE TAG model_train_q3")
spark.sql(f"SELECT name, type, snapshot_id FROM {GOLD}.refs").show(truncate=False)
```

The `.refs` table should list `main` as a branch and `model_train_q3` as a tag.

<!-- ------------------------ -->
## Incremental Processing

A new day of viewing data arrives. Instead of reprocessing everything, we'll process only what changed, in three steps:

1. **Incremental read:** `start-snapshot-id` and `end-snapshot-id` return only the rows appended between two snapshots.
2. **Changelog:** the `.changes` table shows row-level inserts and deletes.
3. **Targeted rescore:** `overwrite(condition)` replaces only the affected customers in the gold table.

```python
USAGE = f"{DB}.SILVER.USAGE_DAILY"
start_snap = latest_snapshot(USAGE)

new_day = (spark.read.json(f"{STAGE}/increment/usage_events/")
           .withColumn("event_ts", F.to_timestamp("event_ts"))
           .groupBy("customer_id", F.to_date("event_ts").alias("event_date"))
           .agg(F.sum("minutes_watched").alias("minutes_watched"), F.count("*").alias("sessions")))
new_day.writeTo(USAGE).append()
end_snap = latest_snapshot(USAGE)

delta = (spark.read.format("iceberg")
         .option("start-snapshot-id", start_snap)
         .option("end-snapshot-id", end_snap)
         .load(USAGE))
print(f"Full table: {spark.table(USAGE).count():,} rows | incremental read: {delta.count():,} rows")
delta.show(3)
```

The incremental read returns only the new day, a small fraction of the full table.

Next, let's look at the changelog. It includes the partition overwrite from the silver step as well as today's append.

```python
spark.sql(f"SELECT _change_type, count(*) AS n FROM {USAGE}.changes GROUP BY _change_type").show()
```

Finally, we rescore only the customers with new activity.

```python
affected = delta.select("customer_id").distinct()
ids = [r[0] for r in affected.collect()]
churn_features(customer_filter=affected).writeTo(GOLD).overwrite(F.col("customer_id").isin(ids))
print(f"Rescored {len(ids):,} of {spark.table(GOLD).count():,} customers")
```

You should see that only a subset of the 50,000 customers was rescored.

<!-- ------------------------ -->
## Time Travel

The scores have changed since the model was trained. Let's read the gold table three ways, by tag, by snapshot ID and by timestamp, and then measure the drift.

```python
snaps = spark.sql(f"SELECT snapshot_id, committed_at, operation FROM {GOLD}.snapshots ORDER BY committed_at")
snaps.show(truncate=False)
first_snap = snaps.collect()[0]["snapshot_id"]

by_tag = spark.read.format("iceberg").option("tag", "model_train_q3").load(GOLD)
by_snap = spark.read.format("iceberg").option("snapshot-id", first_snap).load(GOLD)
by_ts = spark.read.format("iceberg").option("as-of-timestamp", int(time.time() * 1000)).load(GOLD)
print(f"tag model_train_q3 : {by_tag.count():,} rows")
print(f"snapshot-id        : {by_snap.count():,} rows")
print(f"as-of-timestamp now: {by_ts.count():,} rows")

spark.sql(f"SELECT count(*) AS n FROM {GOLD} VERSION AS OF 'model_train_q3'").show()
```

The last line shows the same tag read in Spark SQL with `VERSION AS OF`. Now let's compare current scores with the training snapshot.

```python
now = spark.table(GOLD).select("customer_id", F.col("churn_risk").alias("risk_now"))
then = by_tag.select("customer_id", F.col("churn_risk").alias("risk_at_training"))
drift = (now.join(then, "customer_id")
         .withColumn("delta", F.round(F.col("risk_now") - F.col("risk_at_training"), 1))
         .filter("delta != 0"))
print(f"{drift.count():,} customers changed risk since model_train_q3")
drift.orderBy(F.abs("delta").desc()).show(5)
```

You should see how many customers moved, and the five with the biggest change in risk.

<!-- ------------------------ -->
## Write-Audit-Publish on Branches

> **Note:** Spark Write-Audit-Publish on Iceberg branches is in preview. If your account doesn't have it yet, this step fails; the rest of the Quickstart still runs.

Bad data should never reach the table that consumers read. **Write-Audit-Publish** (WAP) solves this with Iceberg branches:

1. **Write:** create a branch and land the batch there. `main` doesn't change.
2. **Audit:** run quality checks against the branch.
3. **Publish or reject:** if the checks pass, `fast_forward` moves `main` to the branch in one metadata-only commit. If they fail, drop the branch.

```python
SUBS = f"{DB}.SILVER.SUBSCRIPTIONS"


def load_batch(folder):
    return (spark.read.option("header", "true").option("inferSchema", "true").csv(f"{STAGE}/{folder}/")
            .select("customer_id", "plan_tier", F.col("mrr").cast("double").alias("mrr"),
                    F.to_date("start_date").alias("start_date"), F.to_date("cancel_date").alias("cancel_date"), "country"))


def audit(branch):
    df = spark.read.format("iceberg").option("branch", branch).load(SUBS)
    checks = {
        "null customer_id": df.filter("customer_id IS NULL OR customer_id = ''").count(),
        "negative mrr": df.filter("mrr < 0").count(),
        "duplicate customer_id": df.count() - df.select("customer_id").distinct().count(),
    }
    for name, bad in checks.items():
        print(f"  {'FAIL' if bad else 'PASS'}  {name}: {bad}")
    return all(v == 0 for v in checks.values())


def wap(folder):
    branch = f"audit_{folder}_{datetime.now():%H%M%S}"
    before = spark.table(SUBS).count()
    print(f"WRITE   {folder} -> branch {branch}")
    spark.sql(f"ALTER TABLE {SUBS} CREATE BRANCH {branch}")
    spark.conf.set("spark.wap.branch", branch)   # writes in this session go to the branch
    load_batch(folder).writeTo(SUBS).append()
    spark.conf.unset("spark.wap.branch")
    print(f"        main still has {spark.table(SUBS).count():,} rows")
    print(f"AUDIT   {branch}")
    if audit(branch):
        print("PUBLISH fast_forward main -> branch")
        spark.sql(f"CALL {DB}.system.fast_forward('{SUBS}', 'main', '{branch}')").collect()
    else:
        print("REJECT  drop the branch; main was never touched")
    spark.sql(f"ALTER TABLE {SUBS} DROP BRANCH {branch}")
    print(f"        main rows: {before:,} -> {spark.table(SUBS).count():,}\n")
```

Here's what the code does:

- `spark.wap.branch` routes every write in the session to the audit branch
- `audit()` reads the branch with `option("branch", ...)` and counts missing IDs, negative revenue and duplicates
- `fast_forward` publishes the branch to `main` only when every check passes

> **Note:** Read a branch with `spark.read.format("iceberg").option("branch", b).load(t)`. The `option("branch", b).table(t)` form can silently return `main`.

Let's run it on the broken billing export first.

```python
wap("wap_bad")
```

The audit should fail on missing IDs and negative revenue, and the `main` row count should stay the same. Now the clean batch:

```python
wap("wap_good")
```

This time every check passes, and `main` grows by 500 rows.

<!-- ------------------------ -->
## Lineage

Iceberg metadata tables record every snapshot and every ref, which lets us prove what shipped. Both batches appear as appends, but only the good one is an ancestor of `main`.

```python
spark.sql(f"SELECT snapshot_id, parent_id, committed_at, operation FROM {SUBS}.snapshots ORDER BY committed_at").show(truncate=False)
spark.sql(f"SELECT name, type, snapshot_id FROM {SUBS}.refs").show(truncate=False)
spark.sql(f"CALL {DB}.system.ancestors_of('{SUBS}')").show(truncate=False)
spark.sql(f"SELECT name, type, snapshot_id FROM {GOLD}.refs").show(truncate=False)
```

Here's what each query shows:

- `.snapshots` lists every commit on the subscriptions table, including the rejected batch
- `.refs` shows the branches and tags that still exist; the audit branches were dropped
- `ancestors_of` walks the history of `main`, which skips the rejected snapshot
- The gold `.refs` still holds the `model_train_q3` tag

<!-- ------------------------ -->
## Clean Up

Let's drop every object this Quickstart created. Run this in a SQL worksheet or a SQL cell.

```sql
USE ROLE ACCOUNTADMIN;

-- Drop guide objects
DROP DATABASE IF EXISTS CHURN_DEMO;
DROP WAREHOUSE IF EXISTS SCOS_CHURN_WH;

-- Drop the role created for this Quickstart
DROP ROLE IF EXISTS SCOS_CHURN_ROLE;
```

Also delete the uploaded notebook from **Workspaces** if you no longer need it.

<!-- ------------------------ -->
## Conclusion And Resources

You ran a complete PySpark churn pipeline on Snowflake without rewriting it. Every layer is an open Apache Iceberg table, so other engines can read the same data.

### What You Learned
- How to run PySpark on Snowflake with Snowpark Connect for Spark
- How to write partitioned Iceberg tables and overwrite single partitions with DataFrameWriterV2
- How to bookmark training data with Iceberg tags and read it back with time travel
- How to process only new data with incremental reads, the changelog and targeted overwrites
- How to keep bad data out of production with Write-Audit-Publish on branches
- How to audit history with Iceberg metadata tables

### Next Steps

The same code also works on Iceberg tables managed by an external catalog such as AWS Glue. To try it, connect Glue through a catalog integration and a catalog-linked database, then point the pipeline at that database.

### Resources
- [Snowpark Connect for Spark](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
- [Apache Iceberg tables in Snowflake](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Catalog-linked databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Notebooks in Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-overview)

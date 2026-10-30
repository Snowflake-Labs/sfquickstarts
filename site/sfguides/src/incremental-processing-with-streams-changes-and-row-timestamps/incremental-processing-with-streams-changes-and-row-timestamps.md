author: Yoav Ostrinsky
id: incremental-processing-with-streams-changes-and-row-timestamps
language: en
summary: Process only changed data in Snowflake with streams, the CHANGES clause and row timestamps, and choose the right primitive for each pipeline.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/transformation
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Incremental Processing with Streams, CHANGES and Row Timestamps
<!-- ------------------------ -->
## Overview

Most pipelines don't need to reprocess a whole table every run. They need the rows that changed since the last run, applied to a target exactly once. Snowflake gives you three primitives for this, and they make different promises:

- **Streams** keep an offset for you. You read the changes since the offset, and the offset moves forward only when a DML transaction that reads the stream commits.
- **The CHANGES clause** is stateless. You ask for the changes between two points in time, and you can ask again for the same window as often as you like.
- **Row timestamps** stamp every row with the time its last change committed, exposed as the METADATA$ROW_LAST_COMMIT_TIME column. You keep your own watermark and filter on it.

In this guide you build one small order table and load it into a target three times, once with each primitive. Then you change the source (an update, a delete, a new order and a late, backfilled order), run the three loads again and compare the results in one query. Along the way you'll see how a stream behaves when a transaction fails, how streams go stale, why an event-time watermark misses late rows that a commit-time watermark catches, and how to measure latency across a pipeline step.

The core sections need no scheduler. Tasks appear only in the section on triggered tasks; for scheduling and orchestration in general, see the [comprehensive guide to orchestration](/en/developers/guides/comprehensive-guide-to-orchestration/).

### What You'll Learn

- How standard and append-only streams differ, and how a stream offset advances
- How to write an exactly-once MERGE that consumes a stream, and what happens to the offset on failure
- How to read a replayable window of changes with CHANGES, AT, BEFORE and END
- How to build a commit-time watermark with row timestamps, and why it catches backfilled rows
- How to measure the latency of a pipeline step with row timestamps
- How stream staleness and data retention interact, and how to recover a stale stream
- How to use the same patterns from dbt and from Spark through Snowpark Connect
- When to use dynamic tables instead

### What You'll Build

A source table, DEMO_ORDERS, and four targets loaded from it: one per primitive plus a naive event-time loader for contrast. You'll also build a dbt incremental model and read an Iceberg table incrementally from Spark.

### Prerequisites

- A Snowflake account and a role that can create a database and a warehouse (the guide uses ACCOUNTADMIN for brevity)
- For the triggered task section, the EXECUTE TASK and EXECUTE MANAGED TASK privileges
- For the Iceberg section, an account on AWS or Azure (Snowflake storage for Iceberg tables isn't available on Google Cloud)
- For the dbt section, the [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) version 3.31.0 or later, with a connection configured for this account
- For the Spark section, Python 3.10 to 3.12, [uv](https://docs.astral.sh/uv/), and a default connection in the Snowflake CLI configuration whose role can read DEMO_INCREMENTAL_DB

<!-- ------------------------ -->
## Set Up the Demo Data

Open a Snowsight worksheet and run the following to create the database, warehouse and schema. Every object in this guide carries a comment so you can find it later.

```sql
CREATE DATABASE IF NOT EXISTS DEMO_INCREMENTAL_DB COMMENT = 'Incremental processing quickstart';
CREATE WAREHOUSE IF NOT EXISTS DEMO_INCREMENTAL_WH WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 INITIALLY_SUSPENDED = TRUE COMMENT = 'Incremental processing quickstart';
CREATE OR REPLACE SCHEMA DEMO_INCREMENTAL_DB.DEMO COMMENT = 'Incremental processing quickstart';
USE SCHEMA DEMO_INCREMENTAL_DB.DEMO;
USE WAREHOUSE DEMO_INCREMENTAL_WH;
```

Now create the source table. It holds one row per order, and orders are updated in place as their status changes. Two table properties matter here. CHANGE_TRACKING records the change metadata that streams and CHANGES read. ROW_TIMESTAMP adds the METADATA$ROW_LAST_COMMIT_TIME column.

```sql
CREATE OR REPLACE TABLE DEMO_ORDERS (
  ORDER_ID    INT,
  CUSTOMER_ID INT,
  STATUS      STRING,
  AMOUNT      NUMBER(10,2),
  EVENT_TS    TIMESTAMP_NTZ
) CHANGE_TRACKING = TRUE ROW_TIMESTAMP = TRUE
  COMMENT = 'Source: one row per order, updated in place';
```

Next, create four identical targets, one per loading method, and a small state table that the CHANGES and watermark loaders use to remember where they stopped.

```sql
CREATE OR REPLACE TABLE DEMO_ORDERS_BY_STREAM     LIKE DEMO_ORDERS COMMENT = 'Target loaded from a stream';
CREATE OR REPLACE TABLE DEMO_ORDERS_BY_CHANGES    LIKE DEMO_ORDERS COMMENT = 'Target loaded with CHANGES';
CREATE OR REPLACE TABLE DEMO_ORDERS_BY_WATERMARK  LIKE DEMO_ORDERS COMMENT = 'Target loaded with a commit-time watermark';
CREATE OR REPLACE TABLE DEMO_ORDERS_BY_EVENT_TIME LIKE DEMO_ORDERS COMMENT = 'Target loaded with a naive event-time watermark';

CREATE OR REPLACE TABLE DEMO_LOAD_STATE (LOADER STRING, HIGH_WATER TIMESTAMP_LTZ) COMMENT = 'Where each stateless loader stopped';
INSERT INTO DEMO_LOAD_STATE VALUES
  ('CHANGES', CURRENT_TIMESTAMP()),
  ('WATERMARK', '1970-01-01 00:00:00'::TIMESTAMP_LTZ);
SET STATE_ROWS_QUERY = LAST_QUERY_ID();

CREATE OR REPLACE TABLE DEMO_LOAD_LOG (LOADER STRING, ROWS_SEEN INT, LOADED_AT TIMESTAMP_LTZ) COMMENT = 'One row per committed stream load';
```

**Note that** the CHANGES loader starts its window at the moment you created the state rows, so it sees every change from here on. The session variable STATE_ROWS_QUERY keeps that statement's query ID for later.

Create the stream last, so it starts tracking from this point:

```sql
CREATE OR REPLACE STREAM DEMO_ORDERS_STREAM ON TABLE DEMO_ORDERS COMMENT = 'Standard stream feeding DEMO_ORDERS_BY_STREAM';
CREATE OR REPLACE STREAM DEMO_ORDERS_APPEND_STREAM ON TABLE DEMO_ORDERS APPEND_ONLY = TRUE COMMENT = 'Append-only stream, for comparison';
```

Finally, load the first batch of five orders:

```sql
INSERT INTO DEMO_ORDERS VALUES
  (1, 101, 'NEW', 120.00, '2026-10-01 09:00:00'), (2, 102, 'NEW', 80.00, '2026-10-02 10:00:00'),
  (3, 103, 'NEW', 45.50, '2026-10-03 11:00:00'), (4, 101, 'NEW', 300.00, '2026-10-04 12:00:00'),
  (5, 104, 'NEW', 15.00, '2026-10-05 13:00:00');
```

<!-- ------------------------ -->
## Load 1: Streams

A stream doesn't hold data. It stores an offset into the source table's change history and returns the rows that changed after it, plus three metadata columns: METADATA$ACTION (INSERT or DELETE), METADATA$ISUPDATE and METADATA$ROW_ID. Querying a stream does not move the offset. The offset advances only when the stream is read inside a DML statement whose transaction commits.

Look at both streams before consuming anything:

```sql
SELECT ORDER_ID, STATUS, METADATA$ACTION, METADATA$ISUPDATE FROM DEMO_ORDERS_STREAM ORDER BY ORDER_ID;
SELECT ORDER_ID, STATUS, METADATA$ACTION FROM DEMO_ORDERS_APPEND_STREAM ORDER BY ORDER_ID;
```

Both return the five inserts. The difference shows up once rows are updated or deleted, which you'll do in a later step.

Snowflake has three stream types:

| Stream type | What it returns | Where it's supported |
|:--|:--|:--|
| Standard | The net row-level delta: inserts, updates (as a DELETE and INSERT pair) and deletes | Standard tables, dynamic tables, Snowflake-managed Iceberg tables, externally managed V3 Iceberg tables, directory tables, views |
| Append-only | Inserted rows only; updates, deletes and truncates are ignored | Standard tables, dynamic tables, Snowflake-managed Iceberg tables, views |
| Insert-only | Inserted rows only, for sources made of files | External tables, externally managed Iceberg tables, Delta Direct tables without partition columns |

Insert-only streams are rejected on a standard table with the error "Streams of type INSERT_ONLY can only be created on external tables or Iceberg tables with an external catalog integration."

### Consume the stream exactly once

The load below applies the stream to the target with one MERGE and records an audit row, both in one explicit transaction. The filter on the USING clause drops the DELETE half of each update pair, so an update arrives as a single row with METADATA$ISUPDATE set, and a true delete arrives as a DELETE with METADATA$ISUPDATE false.

```sql
BEGIN TRANSACTION;

MERGE INTO DEMO_ORDERS_BY_STREAM T
USING (
  SELECT * FROM DEMO_ORDERS_STREAM
  WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED AND S.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);

INSERT INTO DEMO_LOAD_LOG SELECT 'STREAM', COUNT(*), CURRENT_TIMESTAMP() FROM DEMO_ORDERS_STREAM;

COMMIT;
```

Inside the transaction both statements see the same set of stream rows, because streams use repeatable read isolation: every read of the stream in the transaction returns the changes up to the moment the transaction began. When the COMMIT succeeds, the offset moves to that moment, and the next load picks up from there. Check it:

```sql
SELECT * FROM DEMO_LOAD_LOG;
SELECT COUNT(*) AS PENDING_CHANGES FROM DEMO_ORDERS_STREAM;
```

The log shows five rows seen, and the stream is now empty.

<!-- ------------------------ -->
## Load 2: The CHANGES Clause

CHANGES reads the same change-tracking metadata as a stream, but keeps no offset. You give it a start point with AT or BEFORE and, optionally, an end point with END, and it returns the changes in that window. Reading a window doesn't consume it, so you can run the same query twice and get the same rows. That makes CHANGES the natural fit for replay and backfill, and it means you must store the window boundary yourself. Here the boundary lives in DEMO_LOAD_STATE.

The values passed to TIMESTAMP and OFFSET must be constant expressions, so a subquery can't go inside AT. Read the boundary into session variables first:

```sql
SET LOAD_FROM = (SELECT HIGH_WATER FROM DEMO_LOAD_STATE WHERE LOADER = 'CHANGES');
SET LOAD_TO = CURRENT_TIMESTAMP();

SELECT ORDER_ID, STATUS, METADATA$ACTION, METADATA$ISUPDATE
FROM DEMO_ORDERS CHANGES (INFORMATION => DEFAULT) AT (TIMESTAMP => $LOAD_FROM) END (TIMESTAMP => $LOAD_TO)
ORDER BY ORDER_ID;
```

Now apply that window and move the boundary forward in one transaction, so the target and the boundary can never disagree:

```sql
BEGIN TRANSACTION;

MERGE INTO DEMO_ORDERS_BY_CHANGES T
USING (
  SELECT * FROM DEMO_ORDERS CHANGES (INFORMATION => DEFAULT) AT (TIMESTAMP => $LOAD_FROM) END (TIMESTAMP => $LOAD_TO)
  WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED AND S.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);

UPDATE DEMO_LOAD_STATE SET HIGH_WATER = $LOAD_TO WHERE LOADER = 'CHANGES';

COMMIT;
```

Because the MERGE is keyed on ORDER_ID, running it again for the same window leaves the target unchanged. That's what makes a CHANGES load safe to replay.

### Choosing the start and end points

CHANGES accepts the same reference points as Time Travel. A few behaviours are worth knowing:

- AT (STATEMENT => query ID) starts after that statement's changes; BEFORE (STATEMENT => query ID) includes them. Use BEFORE when you want the statement that created the rows to be part of the window.
- END is inclusive of the end point.
- AT (STREAM => 'name') starts at a stream's current offset without consuming it, which is handy for checking what the next stream load will see.
- INFORMATION => APPEND_ONLY returns inserted rows only and skips the join that computes the net delta, so it's cheaper when you only care about inserts.

Here is the append-only view of everything since the CHANGES loader started, using the query ID you saved during setup as the start point:

```sql
SELECT ORDER_ID, METADATA$ACTION FROM DEMO_ORDERS CHANGES (INFORMATION => APPEND_ONLY) AT (STATEMENT => $STATE_ROWS_QUERY) ORDER BY ORDER_ID;
```

Change tracking must cover the whole window. On a table without it, CHANGES fails with "Change tracking is not enabled or has been missing for the time range requested", and a start point older than the table's Time Travel retention fails with "Time travel data is not available for table".

<!-- ------------------------ -->
## Load 3: A Row-Timestamp Watermark

With ROW_TIMESTAMP enabled, every row exposes METADATA$ROW_LAST_COMMIT_TIME: the time its most recent change committed. Rows changed in the same transaction share one timestamp, and rows changed in different transactions are ordered by commit time within the table. Look at it:

```sql
SELECT ORDER_ID, STATUS, EVENT_TS, METADATA$ROW_LAST_COMMIT_TIME AS COMMIT_TS FROM DEMO_ORDERS ORDER BY ORDER_ID;
```

All five rows share one commit time, because they were inserted in one statement.

A watermark loader keeps the highest commit time it has applied and, on the next run, takes the rows committed after it. Capture the upper bound before the MERGE so that a row committed while the load runs falls into the next window instead of being skipped:

```sql
SET WM_FROM = (SELECT HIGH_WATER FROM DEMO_LOAD_STATE WHERE LOADER = 'WATERMARK');
SET WM_TO = (SELECT COALESCE(MAX(METADATA$ROW_LAST_COMMIT_TIME), $WM_FROM) FROM DEMO_ORDERS);

BEGIN TRANSACTION;

MERGE INTO DEMO_ORDERS_BY_WATERMARK T
USING (
  SELECT ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS FROM DEMO_ORDERS
  WHERE METADATA$ROW_LAST_COMMIT_TIME > $WM_FROM AND METADATA$ROW_LAST_COMMIT_TIME <= $WM_TO
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);

UPDATE DEMO_LOAD_STATE SET HIGH_WATER = $WM_TO WHERE LOADER = 'WATERMARK';

COMMIT;
```

This loader reads the table itself, not change metadata, so it has no retention limit and no offset to go stale. The trade-off is that a deleted row simply isn't there to read. A watermark load can't see hard deletes; you'll see the effect in the next step.

For contrast, here is the loader many pipelines start with: a watermark on the business event time, EVENT_TS.

```sql
MERGE INTO DEMO_ORDERS_BY_EVENT_TIME T
USING (
  SELECT * FROM DEMO_ORDERS
  WHERE EVENT_TS > (SELECT COALESCE(MAX(EVENT_TS), '1970-01-01'::TIMESTAMP_NTZ) FROM DEMO_ORDERS_BY_EVENT_TIME)
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED THEN UPDATE SET T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
```

All four targets now hold the same five orders.

<!-- ------------------------ -->
## Change the Source and Compare

Now make the kind of changes real pipelines see: an update, a delete, a new order, and a late order that belongs to October 2 but arrives today, for example from a backfill or a delayed upstream system.

```sql
UPDATE DEMO_ORDERS SET STATUS = 'SHIPPED' WHERE ORDER_ID = 2;
DELETE FROM DEMO_ORDERS WHERE ORDER_ID = 5;
INSERT INTO DEMO_ORDERS VALUES (6, 105, 'NEW', 60.00, '2026-10-06 14:00:00');
INSERT INTO DEMO_ORDERS VALUES (7, 102, 'NEW', 99.00, '2026-10-02 18:00:00');
```

Before reloading, compare the two streams. The standard stream shows the update as a DELETE and INSERT pair with METADATA$ISUPDATE set, the delete of order 5 and the two inserts. The append-only stream has not been consumed yet, so it still shows the original five inserts plus orders 6 and 7, including order 5, which no longer exists: append-only streams ignore deletes.

```sql
SELECT ORDER_ID, STATUS, METADATA$ACTION, METADATA$ISUPDATE FROM DEMO_ORDERS_STREAM ORDER BY ORDER_ID, METADATA$ACTION;
SELECT ORDER_ID, STATUS, METADATA$ACTION FROM DEMO_ORDERS_APPEND_STREAM ORDER BY ORDER_ID;
```

The standard stream returns:

| ORDER_ID | STATUS | METADATA$ACTION | METADATA$ISUPDATE |
|:--|:--|:--|:--|
| 2 | NEW | DELETE | TRUE |
| 2 | SHIPPED | INSERT | TRUE |
| 5 | NEW | DELETE | FALSE |
| 6 | NEW | INSERT | FALSE |
| 7 | NEW | INSERT | FALSE |

The append-only stream returns orders 1 to 7, all as INSERT with status NEW.

Now rerun the three loads exactly as before. The statements are repeated here so you can run the block in one go.

```sql
-- Stream load
BEGIN TRANSACTION;
MERGE INTO DEMO_ORDERS_BY_STREAM T
USING (SELECT * FROM DEMO_ORDERS_STREAM WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED AND S.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
INSERT INTO DEMO_LOAD_LOG SELECT 'STREAM', COUNT(*), CURRENT_TIMESTAMP() FROM DEMO_ORDERS_STREAM;
COMMIT;

-- CHANGES load
SET LOAD_FROM = (SELECT HIGH_WATER FROM DEMO_LOAD_STATE WHERE LOADER = 'CHANGES');
SET LOAD_TO = CURRENT_TIMESTAMP();
BEGIN TRANSACTION;
MERGE INTO DEMO_ORDERS_BY_CHANGES T
USING (
  SELECT * FROM DEMO_ORDERS CHANGES (INFORMATION => DEFAULT) AT (TIMESTAMP => $LOAD_FROM) END (TIMESTAMP => $LOAD_TO)
  WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED AND S.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
UPDATE DEMO_LOAD_STATE SET HIGH_WATER = $LOAD_TO WHERE LOADER = 'CHANGES';
COMMIT;

-- Commit-time watermark load
SET WM_FROM = (SELECT HIGH_WATER FROM DEMO_LOAD_STATE WHERE LOADER = 'WATERMARK');
SET WM_TO = (SELECT COALESCE(MAX(METADATA$ROW_LAST_COMMIT_TIME), $WM_FROM) FROM DEMO_ORDERS);
BEGIN TRANSACTION;
MERGE INTO DEMO_ORDERS_BY_WATERMARK T
USING (
  SELECT ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS FROM DEMO_ORDERS
  WHERE METADATA$ROW_LAST_COMMIT_TIME > $WM_FROM AND METADATA$ROW_LAST_COMMIT_TIME <= $WM_TO
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
UPDATE DEMO_LOAD_STATE SET HIGH_WATER = $WM_TO WHERE LOADER = 'WATERMARK';
COMMIT;

-- Naive event-time load
MERGE INTO DEMO_ORDERS_BY_EVENT_TIME T
USING (
  SELECT * FROM DEMO_ORDERS
  WHERE EVENT_TS > (SELECT COALESCE(MAX(EVENT_TS), '1970-01-01'::TIMESTAMP_NTZ) FROM DEMO_ORDERS_BY_EVENT_TIME)
) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED THEN UPDATE SET T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
```

Now the payoff. One query lines up every order across the source and the four targets:

```sql
WITH IDS AS (
  SELECT ORDER_ID FROM DEMO_ORDERS UNION SELECT ORDER_ID FROM DEMO_ORDERS_BY_STREAM
  UNION SELECT ORDER_ID FROM DEMO_ORDERS_BY_WATERMARK UNION SELECT ORDER_ID FROM DEMO_ORDERS_BY_EVENT_TIME
)
SELECT I.ORDER_ID,
       O.STATUS AS SOURCE,
       S.STATUS AS BY_STREAM,
       C.STATUS AS BY_CHANGES,
       W.STATUS AS BY_COMMIT_TIME,
       E.STATUS AS BY_EVENT_TIME
FROM IDS I
LEFT JOIN DEMO_ORDERS O               ON O.ORDER_ID = I.ORDER_ID
LEFT JOIN DEMO_ORDERS_BY_STREAM S     ON S.ORDER_ID = I.ORDER_ID
LEFT JOIN DEMO_ORDERS_BY_CHANGES C    ON C.ORDER_ID = I.ORDER_ID
LEFT JOIN DEMO_ORDERS_BY_WATERMARK W  ON W.ORDER_ID = I.ORDER_ID
LEFT JOIN DEMO_ORDERS_BY_EVENT_TIME E ON E.ORDER_ID = I.ORDER_ID
ORDER BY I.ORDER_ID;
```

| ORDER_ID | SOURCE | BY_STREAM | BY_CHANGES | BY_COMMIT_TIME | BY_EVENT_TIME |
|:--|:--|:--|:--|:--|:--|
| 1 | NEW | NEW | NEW | NEW | NEW |
| 2 | SHIPPED | SHIPPED | SHIPPED | SHIPPED | NEW |
| 3 | NEW | NEW | NEW | NEW | NEW |
| 4 | NEW | NEW | NEW | NEW | NEW |
| 5 | NULL | NULL | NULL | NEW | NEW |
| 6 | NEW | NEW | NEW | NEW | NEW |
| 7 | NEW | NEW | NEW | NEW | NULL |

![Comparison of the four targets](assets/compare_targets.png)

Screenshot placeholder: the result grid of the comparison query after the second round of loads, with the NULL cells for orders 5 and 7 visible.

Read the result row by row:

- **The stream and CHANGES targets match the source exactly.** Both see updates, deletes and inserts.
- **The commit-time watermark caught the update and the late order 7**, because both committed after the last watermark. It still shows order 5, because a deleted row isn't there to read.
- **The event-time watermark missed order 7** (its EVENT_TS is older than the highest EVENT_TS already loaded) **and missed the update to order 2** (an update that doesn't touch EVENT_TS doesn't move it past the watermark). It also kept order 5.

### Comparing the three primitives

| | Stream | CHANGES | Row-timestamp watermark |
|:--|:--|:--|:--|
| Consumption semantics | Stateful: Snowflake stores the offset, and a committed DML read advances it | Stateless: you pass the window on every query | Stateless: you store the highest commit time you applied |
| What it sees | Inserts, updates and deletes (standard); inserts only (append-only) | Inserts, updates and deletes (DEFAULT); inserts only (APPEND_ONLY) | Current rows changed after the watermark; no hard deletes |
| Idempotency and replay | Exactly once per committed transaction; replaying an old window needs CHANGES or a new stream created with Time Travel | Any window can be read again within retention; pair it with a keyed MERGE | Rerun from any watermark you like; pair it with a keyed MERGE |
| Retention and staleness | Becomes stale if not consumed within the extended retention period, and must then be recreated | The window must fall within the table's Time Travel retention | No retention limit; row timestamps live as long as the rows |
| Qualitative cost | The stream stores only an offset; an unconsumed stream extends the table's retention, which adds storage; reads are billed as warehouse compute | Hidden change-tracking columns add a little storage; reads are billed as warehouse compute; APPEND_ONLY skips the delta join | No change-tracking metadata to read; each load is an ordinary query on the source table, billed as warehouse compute |

<!-- ------------------------ -->
## Exactly-Once Loads and Failure

The stream load above is exactly once because the MERGE, the audit insert and the offset move commit together. It's worth seeing what happens when they don't commit.

Add one order, then start a load and roll it back:

```sql
INSERT INTO DEMO_ORDERS VALUES (8, 106, 'NEW', 42.00, '2026-10-07 09:00:00');

BEGIN TRANSACTION;
MERGE INTO DEMO_ORDERS_BY_STREAM T
USING (SELECT * FROM DEMO_ORDERS_STREAM WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)) S
ON T.ORDER_ID = S.ORDER_ID
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
ROLLBACK;

SELECT COUNT(*) AS PENDING_CHANGES FROM DEMO_ORDERS_STREAM;
```

The stream still has one pending row: a rolled-back transaction leaves the offset where it was, and the target doesn't have order 8.

The trap is a statement that fails inside a transaction that your script then commits. By default, a failed statement doesn't abort the surrounding transaction. If the MERGE succeeded and a later statement failed, a COMMIT still commits the MERGE and moves the offset, and the work of the failed statement is lost. Set TRANSACTION_ABORT_ON_ERROR so that any error aborts the whole transaction:

```sql
ALTER SESSION SET TRANSACTION_ABORT_ON_ERROR = TRUE;

BEGIN TRANSACTION;
MERGE INTO DEMO_ORDERS_BY_STREAM T
USING (SELECT * FROM DEMO_ORDERS_STREAM WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)) S
ON T.ORDER_ID = S.ORDER_ID
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
INSERT INTO DEMO_LOAD_LOG SELECT 'STREAM', 1 / 0, CURRENT_TIMESTAMP();
COMMIT;

SELECT COUNT(*) AS PENDING_CHANGES FROM DEMO_ORDERS_STREAM;
ALTER SESSION UNSET TRANSACTION_ABORT_ON_ERROR;
```

The INSERT fails with a division by zero, on purpose. With the parameter set, the transaction is aborted, the COMMIT fails with "COMMIT failed. Your transaction ... was already aborted.", the MERGE is undone and the stream still holds order 8. In this guide's test runs, the same sequence without the parameter committed the MERGE and emptied the stream even though the audit insert had failed.

The next successful run picks up the pending change. Run the normal load once more to apply order 8:

```sql
BEGIN TRANSACTION;
MERGE INTO DEMO_ORDERS_BY_STREAM T
USING (SELECT * FROM DEMO_ORDERS_STREAM WHERE NOT (METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE)) S
ON T.ORDER_ID = S.ORDER_ID
WHEN MATCHED AND S.METADATA$ACTION = 'DELETE' THEN DELETE
WHEN MATCHED THEN UPDATE SET T.CUSTOMER_ID = S.CUSTOMER_ID, T.STATUS = S.STATUS, T.AMOUNT = S.AMOUNT, T.EVENT_TS = S.EVENT_TS
WHEN NOT MATCHED AND S.METADATA$ACTION = 'INSERT' THEN
  INSERT (ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS) VALUES (S.ORDER_ID, S.CUSTOMER_ID, S.STATUS, S.AMOUNT, S.EVENT_TS);
INSERT INTO DEMO_LOAD_LOG SELECT 'STREAM', COUNT(*), CURRENT_TIMESTAMP() FROM DEMO_ORDERS_STREAM;
COMMIT;

SELECT ORDER_ID, STATUS FROM DEMO_ORDERS_BY_STREAM WHERE ORDER_ID = 8;
```

Two more rules keep stream loads exactly once. Give each consumer its own stream, because one consumer's commit moves the offset for everyone reading that stream. And remember that a plain SELECT never advances the offset, even inside a transaction; only DML does.

<!-- ------------------------ -->
## Staleness and Retention

A stream reads change history that the source table keeps for its Time Travel retention period. If the offset falls outside that history, the stream becomes stale and must be recreated. To give an unconsumed stream more room, Snowflake temporarily extends the table's retention, up to MAX_DATA_EXTENSION_TIME_IN_DAYS (14 days by default).

SHOW STREAMS reports when a stream is predicted to go stale. STALE_AFTER is the last consumption time plus the larger of the table's DATA_RETENTION_TIME_IN_DAYS and MAX_DATA_EXTENSION_TIME_IN_DAYS:

```sql
SHOW STREAMS LIKE 'DEMO_ORDERS_STREAM';
SELECT "name", "mode", "stale", "stale_after" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
```

Raise the extension limit on the source table, and STALE_AFTER moves out accordingly:

```sql
ALTER TABLE DEMO_ORDERS SET MAX_DATA_EXTENSION_TIME_IN_DAYS = 30;
SHOW STREAMS LIKE 'DEMO_ORDERS_STREAM';
SELECT "name", "stale", "stale_after" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
```

In the test run, STALE_AFTER moved from 14 days after the last consumption to 30 days after it.

To see a stale stream without waiting two weeks, use a scratch table with no retention and no extension. The stream is reported stale straight away:

```sql
CREATE OR REPLACE TABLE DEMO_STALE_SRC (ID INT) DATA_RETENTION_TIME_IN_DAYS = 0 MAX_DATA_EXTENSION_TIME_IN_DAYS = 0 COMMENT = 'Scratch table for the staleness demo';
INSERT INTO DEMO_STALE_SRC VALUES (1), (2);
CREATE OR REPLACE STREAM DEMO_STALE_STREAM ON TABLE DEMO_STALE_SRC COMMENT = 'Stream that goes stale';
SHOW STREAMS LIKE 'DEMO_STALE_STREAM';
SELECT "name", "stale", "stale_after" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
```

The docs warn that reading a stream after STALE_AFTER can still succeed for a while, but that its results can't be trusted. Don't rely on them. The recovery is to recreate the stream and rebuild the target from the current table state. SHOW_INITIAL_ROWS = TRUE makes the new stream return every current row as an INSERT on its first read, so the same keyed MERGE rebuilds the target:

```sql
CREATE OR REPLACE STREAM DEMO_STALE_STREAM ON TABLE DEMO_STALE_SRC SHOW_INITIAL_ROWS = TRUE COMMENT = 'Recreated after going stale';
SELECT ID, METADATA$ACTION FROM DEMO_STALE_STREAM ORDER BY ID;
```

Rows that were deleted from the source while the stream was stale won't appear, so if deletes matter, also remove target rows that no longer exist in the source.

A stream also goes stale, immediately, when its source table is recreated with CREATE OR REPLACE, or when a table under a source view is dropped or recreated. Renaming the source doesn't break the stream.

CHANGES has the same history limit without the extension: its window must fall inside the table's Time Travel retention. A row-timestamp watermark has no such limit. If a pipeline can be paused for longer than its retention allows, that's a reason to prefer a watermark, or to raise retention on the source.

<!-- ------------------------ -->
## Commit Time, Event Time and Latency

The comparison showed the core difference. EVENT_TS is business time, set by whoever produced the row, so late and backfilled rows can arrive with an EVENT_TS older than your watermark. METADATA$ROW_LAST_COMMIT_TIME is set by Snowflake when the change commits, so a watermark on it sees every row that changed after the last load, whatever its business time.

Two limits apply. Row timestamps reflect the last change, not when the row was created, and rows that existed before you enabled ROW_TIMESTAMP have a NULL commit time, so a watermark on them would skip those rows. Backfill those once, then switch to the watermark. Two settings save you from enabling ROW_TIMESTAMP table by table. ALTER SCHEMA ... SET ROW_TIMESTAMP_DEFAULT = TRUE turns it on for every table created in the schema afterwards, and SYSTEM$SET_ROW_TIMESTAMP_ON_ALL_SUPPORTED_TABLES enables it on the existing eligible tables in a schema, database or account and sets that default at the same time:

```sql
SELECT SYSTEM$SET_ROW_TIMESTAMP_ON_ALL_SUPPORTED_TABLES('schema', 'DEMO_INCREMENTAL_DB.DEMO');
```

In the test run, a table that already held a row came back with ROW_TIMESTAMP on, the existing row still had a NULL commit time, and the next row inserted got one. You need the MODIFY privilege on the container. Row timestamps also can't be read through a stream or through CHANGES ("invalid identifier 'METADATA$ROW_LAST_COMMIT_TIME'"), and they aren't supported on Iceberg tables, external tables, hybrid tables or views.

You can carry the source commit time through a stream by putting a view in between. A view can select the metadata column, and a stream on that view returns it as an ordinary column. Give the target its own row timestamps, and the difference between the two is the latency of the step:

```sql
CREATE OR REPLACE VIEW DEMO_ORDERS_WITH_COMMIT_TS COMMENT = 'Exposes the source commit time to a stream' AS
  SELECT ORDER_ID, STATUS, METADATA$ROW_LAST_COMMIT_TIME AS SOURCE_COMMIT_TS FROM DEMO_ORDERS;
CREATE OR REPLACE STREAM DEMO_ORDERS_LATENCY_STREAM ON VIEW DEMO_ORDERS_WITH_COMMIT_TS COMMENT = 'Stream on a view';
CREATE OR REPLACE TABLE DEMO_ORDER_LATENCY (ORDER_ID INT, STATUS STRING, SOURCE_COMMIT_TS TIMESTAMP_LTZ) ROW_TIMESTAMP = TRUE COMMENT = 'Latency of the stream-to-table step';
```

Now change an order and run the step:

```sql
UPDATE DEMO_ORDERS SET STATUS = 'DELIVERED' WHERE ORDER_ID = 2;

INSERT INTO DEMO_ORDER_LATENCY
  SELECT ORDER_ID, STATUS, SOURCE_COMMIT_TS FROM DEMO_ORDERS_LATENCY_STREAM WHERE METADATA$ACTION = 'INSERT';

SELECT ORDER_ID, STATUS, SOURCE_COMMIT_TS,
       METADATA$ROW_LAST_COMMIT_TIME AS TARGET_COMMIT_TS,
       TIMESTAMPDIFF(MILLISECOND, SOURCE_COMMIT_TS, METADATA$ROW_LAST_COMMIT_TIME) AS STEP_LATENCY_MS
FROM DEMO_ORDER_LATENCY;
```

| ORDER_ID | STATUS | SOURCE_COMMIT_TS | TARGET_COMMIT_TS | STEP_LATENCY_MS |
|:--|:--|:--|:--|:--|
| 2 | DELIVERED | ... | ... | 1081 |

In this run the latency is the time between the UPDATE and the INSERT, because you ran them by hand. In a scheduled pipeline it's the end-to-end delay of the step. Row timestamps are ordered within one table, and the docs caution against comparing them across tables or other time sources. Treat cross-table differences like this one as a latency measurement, not as a way to order events.

<!-- ------------------------ -->
## Triggered Tasks

To run a stream load only when there is something to load, attach it to a triggered task: a WHEN SYSTEM$STREAM_HAS_DATA condition and no schedule. Give the task its own stream so it doesn't compete with the loads above. Omitting WAREHOUSE makes it serverless, and COMMENT has to come before WHEN.

```sql
CREATE OR REPLACE TABLE DEMO_ORDER_AUDIT (ORDER_ID INT, STATUS STRING, SEEN_AT TIMESTAMP_LTZ) COMMENT = 'Written by the triggered task';
CREATE OR REPLACE STREAM DEMO_ORDERS_TASK_STREAM ON TABLE DEMO_ORDERS APPEND_ONLY = TRUE COMMENT = 'Feeds the triggered task';
CREATE OR REPLACE TASK DEMO_AUDIT_TASK
  TARGET_COMPLETION_INTERVAL = '1 MINUTE'
  COMMENT = 'Triggered task: runs when the stream has data'
  WHEN SYSTEM$STREAM_HAS_DATA('DEMO_ORDERS_TASK_STREAM')
AS
  INSERT INTO DEMO_ORDER_AUDIT SELECT ORDER_ID, STATUS, CURRENT_TIMESTAMP() FROM DEMO_ORDERS_TASK_STREAM;
ALTER TASK DEMO_AUDIT_TASK RESUME;
INSERT INTO DEMO_ORDERS VALUES (9, 107, 'NEW', 10.00, '2026-10-08 09:00:00');
```

Within about a minute, DEMO_ORDER_AUDIT holds order 9; the cleanup step suspends the task. For schedules, run history, task graphs and retries, see the [comprehensive guide to orchestration](/en/developers/guides/comprehensive-guide-to-orchestration/).

<!-- ------------------------ -->
## Streams on Views and Shared Tables

You already built a stream on a view in the latency section. Streams on views follow the view's query, so a filter in the view filters the change rows too. The view can use projections, filters, inner or cross joins and UNION ALL; views with GROUP BY, QUALIFY, DISTINCT, LIMIT or subqueries outside the FROM clause aren't supported. Try one:

```sql
CREATE OR REPLACE VIEW DEMO_ORDERS_BY_CUSTOMER COMMENT = 'Aggregating view, cannot be streamed' AS
  SELECT CUSTOMER_ID, COUNT(*) AS ORDERS FROM DEMO_ORDERS GROUP BY CUSTOMER_ID;
CREATE OR REPLACE STREAM DEMO_ORDERS_BY_CUSTOMER_STREAM ON VIEW DEMO_ORDERS_BY_CUSTOMER COMMENT = 'Fails on purpose';
```

The CREATE STREAM fails, on purpose, with "Change tracking is not supported on queries with GROUP BY". Change tracking must be enabled on the view and on each underlying table. When the view's owner also owns the tables, creating the stream enables it for you; otherwise the owner runs ALTER VIEW ... SET CHANGE_TRACKING = TRUE.

Shared tables and views work the same way from the consumer side: a consumer can create a stream on a shared table or a shared secure view, provided the provider has enabled change tracking on the shared tables (or on the tables under a shared view) and set a retention period long enough for the consumer's load cadence. Two differences matter. A consumer's stream doesn't extend the provider's retention period, so it goes stale on the provider's retention schedule. And a consumer can't select METADATA$ROW_LAST_COMMIT_TIME from a shared table, even when the provider enabled row timestamps. A provider who wants to share commit times shares a view that selects the column, like this one:

```sql
CREATE OR REPLACE SECURE VIEW DEMO_ORDERS_FOR_SHARING COMMENT = 'Shares row timestamps with consumers' AS
  SELECT ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS, METADATA$ROW_LAST_COMMIT_TIME AS COMMIT_TS FROM DEMO_ORDERS;
ALTER VIEW DEMO_ORDERS_FOR_SHARING SET CHANGE_TRACKING = TRUE;
```

The provider then grants the view to a share as usual, and the consumer can stream it or filter on COMMIT_TS.

<!-- ------------------------ -->
## Incremental Models in dbt

dbt's incremental materialization needs a reliable "what changed since last time" filter, and a commit-time watermark is exactly that. The model below reads DEMO_ORDERS as a source and, on incremental runs, keeps only rows committed after the newest commit time already in the model. Row timestamps aren't supported on Iceberg tables, streams or views, so the source must be a standard table (or a dynamic table) with ROW_TIMESTAMP enabled.

Create a local folder named demo_incremental with these files.

dbt_project.yml:

```yaml
name: demo_incremental
version: "1.0.0"
config-version: 2
profile: demo_incremental
model-paths: ["models"]
```

dbt_projects_profiles.yml (read only by dbt Projects on Snowflake; authentication comes from the Snowflake session):

```yaml
demo_incremental:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "not needed"
      user: "not needed"
      role: ACCOUNTADMIN
      warehouse: DEMO_INCREMENTAL_WH
      database: DEMO_INCREMENTAL_DB
      schema: DEMO
      threads: 4
```

models/sources.yml:

```yaml
version: 2
sources:
  - name: demo
    database: DEMO_INCREMENTAL_DB
    schema: DEMO
    tables:
      - name: DEMO_ORDERS
```

models/orders_by_commit_time.sql:

```sql
{{ config(materialized='incremental', unique_key='ORDER_ID', incremental_strategy='merge') }}

SELECT ORDER_ID,
       CUSTOMER_ID,
       STATUS,
       AMOUNT,
       EVENT_TS,
       METADATA$ROW_LAST_COMMIT_TIME AS SOURCE_COMMIT_TS,
       CURRENT_TIMESTAMP() AS LOADED_AT
FROM {{ source('demo', 'DEMO_ORDERS') }}
{% if is_incremental() %}
WHERE METADATA$ROW_LAST_COMMIT_TIME > (SELECT MAX(SOURCE_COMMIT_TS) FROM {{ this }})
{% endif %}
```

The model persists the source commit time as SOURCE_COMMIT_TS, because the target can't read the source's metadata column later. LOADED_AT is there only so you can see which rows each run touched. Like the watermark loader, this model doesn't see hard deletes.

From the folder that contains demo_incremental, deploy the project as a dbt project object with the Snowflake CLI (add --connection with your connection name if it isn't the default):

```bash
snow dbt deploy DEMO_ORDERS_DBT --source ./demo_incremental --database DEMO_INCREMENTAL_DB --schema DEMO
```

Run it once to build the model with every order:

```sql
EXECUTE DBT PROJECT DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDERS_DBT ARGS = 'run';
SELECT ORDER_ID, STATUS, LOADED_AT FROM DEMO_INCREMENTAL_DB.DEMO.ORDERS_BY_COMMIT_TIME ORDER BY ORDER_ID;
```

Now change two orders, run again and see which rows were touched:

```sql
UPDATE DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDERS SET STATUS = 'SHIPPED' WHERE ORDER_ID = 6;
INSERT INTO DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDERS VALUES (10, 108, 'NEW', 75.00, '2026-10-01 08:00:00');

EXECUTE DBT PROJECT DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDERS_DBT ARGS = 'run';
SELECT ORDER_ID, STATUS, LOADED_AT FROM DEMO_INCREMENTAL_DB.DEMO.ORDERS_BY_COMMIT_TIME ORDER BY LOADED_AT DESC, ORDER_ID;
```

| ORDER_ID | STATUS | LOADED_AT |
|:--|:--|:--|
| 6 | SHIPPED | second run |
| 10 | NEW | second run |
| 1 | NEW | first run |
| 2 | DELIVERED | first run |
| ... | ... | first run |

Only orders 6 and 10 carry the second run's LOADED_AT. Order 10 is another backfilled row, with an EVENT_TS older than every other order, and the commit-time filter picks it up anyway.

![dbt project run output](assets/dbt_execute_output.png)

Screenshot placeholder: the output of the second EXECUTE DBT PROJECT run in Snowsight, showing the incremental model succeeded.

If you change the model's logic later, run it once with ARGS = 'run --full-refresh' so the existing rows are rebuilt with the new logic.

<!-- ------------------------ -->
## Incremental Reads from Spark on Iceberg

Snowpark Connect runs PySpark code on Snowflake. For Iceberg tables it supports Iceberg's incremental read options, start-snapshot-id (exclusive) and end-snapshot-id (inclusive), which return only the rows appended between two snapshots. On a Snowflake-managed Iceberg table this needs change tracking on the table.

Create a Snowflake-managed Iceberg table. With CATALOG set to SNOWFLAKE and EXTERNAL_VOLUME set to SNOWFLAKE_MANAGED, Snowflake stores the files for you, so there's no external volume or cloud bucket to configure. Then write three batches:

```sql
CREATE OR REPLACE ICEBERG TABLE DEMO_ORDER_EVENTS_ICE (ORDER_ID INT, STATUS STRING)
  CATALOG = 'SNOWFLAKE' EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED' CHANGE_TRACKING = TRUE
  COMMENT = 'Iceberg table read incrementally from Spark';
CALL SYSTEM$WAIT(5);

INSERT INTO DEMO_ORDER_EVENTS_ICE VALUES (1, 'NEW'), (2, 'NEW');
SET FIRST_ICE_BATCH = LAST_QUERY_ID();
CALL SYSTEM$WAIT(5);

INSERT INTO DEMO_ORDER_EVENTS_ICE VALUES (3, 'NEW');
CALL SYSTEM$WAIT(5);

INSERT INTO DEMO_ORDER_EVENTS_ICE VALUES (4, 'NEW'), (5, 'NEW');
CALL SYSTEM$WAIT(15);
```

Each INSERT produces an Iceberg snapshot, and GET_TABLE_VERSIONS lists the data snapshots Snowflake has indexed. In this guide's test runs, inserts committed within about a second of each other were listed as a single entry, which is why the block waits after the CREATE and after each INSERT. List the snapshot IDs, oldest first:

```sql
SELECT VERSION_ID, VERSION_CREATED_AT
FROM TABLE(INFORMATION_SCHEMA.GET_TABLE_VERSIONS('DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDER_EVENTS_ICE'))
ORDER BY VERSION_CREATED_AT;
```

You should see three rows, one per batch. The VERSION_ID values are long integers that differ on every run. Indexing can lag the write by several seconds, so if you see fewer than three rows, wait a moment and run the query again. The first two IDs are the ones the Spark script needs.

Snowflake-managed Iceberg tables support standard and append-only streams and CHANGES (see the stream types table above). This guide's test runs used CHANGES with APPEND_ONLY here. This query returns the same rows the Spark read below returns for an open-ended window, using the first batch's statement as the start point:

```sql
SELECT ORDER_ID FROM DEMO_ORDER_EVENTS_ICE CHANGES (INFORMATION => APPEND_ONLY) AT (STATEMENT => $FIRST_ICE_BATCH) ORDER BY ORDER_ID;
```

CHANGES identifies its start and end by timestamp, offset, statement or stream. It doesn't accept an Iceberg snapshot ID: AT (VERSION => snapshot ID) works for a plain Time Travel query on the table, but inside CHANGES it fails with "Invalid data type". In Spark, snapshot IDs are the natural boundary, and Snowpark Connect handles them for you.

Set up a Python project with uv, pinned to the current Snowpark Connect release:

```bash
uv init --bare demo-incremental-spark && cd demo-incremental-spark
uv python pin 3.12
uv add "snowpark-connect[iceberg,jdk]==1.47.0"
```

Save this as incremental_read.py. It connects with your default Snowflake CLI connection, and takes the first two snapshot IDs from the GET_TABLE_VERSIONS result:

```python
import sys
from snowflake import snowpark_connect

spark = snowpark_connect.init_spark_session()
spark.conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")

TABLE = "DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDER_EVENTS_ICE"
first_snapshot, second_snapshot = int(sys.argv[1]), int(sys.argv[2])

print("Everything appended after the first snapshot:")
(spark.read.format("iceberg")
    .option("start-snapshot-id", first_snapshot)
    .load(TABLE).orderBy("ORDER_ID").show())

print("Only what the second snapshot appended:")
(spark.read.format("iceberg")
    .option("start-snapshot-id", first_snapshot)
    .option("end-snapshot-id", second_snapshot)
    .load(TABLE).orderBy("ORDER_ID").show())
```

Run it with the first two VERSION_ID values:

```bash
uv run incremental_read.py <first VERSION_ID> <second VERSION_ID>
```

```text
Everything appended after the first snapshot:
+--------+------+
|ORDER_ID|STATUS|
+--------+------+
|       3|   NEW|
|       4|   NEW|
|       5|   NEW|
+--------+------+

Only what the second snapshot appended:
+--------+------+
|ORDER_ID|STATUS|
+--------+------+
|       3|   NEW|
+--------+------+
```

The first read returns orders 3, 4 and 5, the rows appended after the first snapshot. The second returns only order 3. Because the start snapshot is exclusive, store the last snapshot ID you processed and pass it as start-snapshot-id on the next run.

These options return appended rows only. For row-level changes including deletes, Snowpark Connect 1.43.0 and later also expose Iceberg's changelog through the table's .changes suffix on Snowflake-managed tables.

<!-- ------------------------ -->
## Choosing a Primitive, and When to Use Dynamic Tables

| If you need | Use |
|:--|:--|
| Exactly-once processing of every insert, update and delete, with Snowflake keeping the position | A standard stream, consumed in a transaction |
| Only new rows from an insert-heavy table, as cheaply as possible | An append-only stream, or CHANGES with APPEND_ONLY |
| To replay or backfill a specific window, or several consumers reading different windows without extra objects | CHANGES with AT, BEFORE and END |
| A position that never goes stale, or one that survives long pipeline pauses | A row-timestamp watermark |
| Late and backfilled rows picked up by an incremental load | A row-timestamp watermark, or a stream |
| Hard deletes propagated to the target | A standard stream or CHANGES with DEFAULT |
| To measure pipeline latency | Row timestamps on the source and target |
| An incremental dbt model on a standard table | A row-timestamp watermark in the is_incremental filter |
| Incremental reads of an Iceberg table from Spark | Snapshot IDs with start-snapshot-id and end-snapshot-id |
| A declarative result kept fresh to a target lag, with no load code | A dynamic table |

Much of what streams and tasks are used for is better expressed as a dynamic table. You write the SELECT that describes the result, and Snowflake tracks the changes, decides when to refresh and skips refreshes when nothing changed. For this guide's target, the whole stream load becomes:

```sql
CREATE OR REPLACE DYNAMIC TABLE DEMO_ORDERS_DT
  TARGET_LAG = '1 minute'
  WAREHOUSE = DEMO_INCREMENTAL_WH
  REFRESH_MODE = INCREMENTAL
  COMMENT = 'The stream load, as a dynamic table'
AS
  SELECT ORDER_ID, CUSTOMER_ID, STATUS, AMOUNT, EVENT_TS FROM DEMO_ORDERS;
SELECT COUNT(*) AS ROWS_IN_DT FROM DEMO_ORDERS_DT;
```

If you're coming from streams and tasks, this is how the pieces map:

| Streams and tasks | Dynamic tables |
|:--|:--|
| Stream on the base table | Not needed; Snowflake tracks changes itself |
| Task body with INSERT or MERGE | The SELECT in the dynamic table definition |
| Task schedule | TARGET_LAG, a freshness goal rather than a fixed interval |
| Task graph of root and child tasks | A pipeline of dynamic tables; intermediate ones use a downstream target lag |
| MERGE that keeps the latest row per key | A window function such as ROW_NUMBER with QUALIFY |
| SYSTEM$STREAM_HAS_DATA check | Not needed; refreshes are skipped when the sources haven't changed |
| An existing orchestrator calling the task | A dynamic table with its scheduler disabled, refreshed by the orchestrator |

If your load has to keep MERGE or INSERT logic, for example different handling per change type, a custom incremental dynamic table runs that logic in its REFRESH USING clause on top of CHANGES, with Snowflake advancing the position. Streams and tasks remain the better fit for loops and cursor-based procedural code, side effects such as external calls, writing several tables in one transaction, sources that dynamic tables don't support (external and directory tables), or latency below the one-minute [minimum target lag](https://docs.snowflake.com/en/user-guide/dynamic-tables-target-lag). For everything else about dynamic tables, see the [comprehensive guide to dynamic tables](/en/developers/guides/comprehensive-guide-to-dynamic-tables/).

<!-- ------------------------ -->
## Cleanup

Suspend the task and the dynamic table, then drop everything this guide created:

```sql
ALTER TASK DEMO_INCREMENTAL_DB.DEMO.DEMO_AUDIT_TASK SUSPEND;
ALTER DYNAMIC TABLE DEMO_INCREMENTAL_DB.DEMO.DEMO_ORDERS_DT SUSPEND;
DROP DATABASE IF EXISTS DEMO_INCREMENTAL_DB;
DROP WAREHOUSE IF EXISTS DEMO_INCREMENTAL_WH;
```

On your machine, delete the demo_incremental dbt folder and the demo-incremental-spark uv project.

<!-- ------------------------ -->
## Conclusion and Resources

You loaded the same changing table three ways and saw where each primitive stands:

- **Streams** give you exactly-once change processing with Snowflake keeping the offset, as long as you consume them in a transaction that aborts on error, and before they go stale.
- **CHANGES** gives you any window of changes on demand, which makes replay and backfill simple, within Time Travel retention.
- **Row timestamps** give you a commit-time watermark that never goes stale and catches late rows, at the cost of not seeing hard deletes, plus a direct way to measure latency.
- **Dynamic tables** replace most stream-and-task pipelines with a single SELECT.

### Related Resources

- [Introduction to streams](https://docs.snowflake.com/en/user-guide/streams-intro)
- [CHANGES](https://docs.snowflake.com/en/sql-reference/constructs/changes)
- [Use row timestamps to measure latency in your pipelines](https://docs.snowflake.com/en/user-guide/data-engineering/row-timestamps)
- [Triggered tasks](https://docs.snowflake.com/en/user-guide/tasks-triggered)
- [Migrate from streams and tasks to dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/migrate-streams-tasks)
- [Apache Iceberg tables with Snowpark Connect](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-iceberg)
- [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)
- [Comprehensive guide to orchestration](/en/developers/guides/comprehensive-guide-to-orchestration/)
- [Comprehensive guide to dynamic tables](/en/developers/guides/comprehensive-guide-to-dynamic-tables/)

author: Adam Timm
id: hybrid-tables-operations-patterns
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/hybrid-tables
language: en
summary: Learn data management and operations patterns for Hybrid Tables — fan-in aggregation across multiple HTs, hot/cold data tiering, and alert-based monitoring with AGGREGATE_QUERY_HISTORY.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, operations, fan-in, aggregation, hot cold tiering, archive, monitoring, AGGREGATE_QUERY_HISTORY, alert, throttling, Unistore, data management
related_concepts: storage quota, micro-partition, DELETE compaction, AGGREGATE_QUERY_HISTORY latency, hybrid_table_requests_throttled_count, CREATE ALERT, SCHEDULE
prerequisite_guides: getting-started-with-hybrid-tables
skill_level: intermediate
estimated_time_minutes: 35
snowflake_features: hybrid_tables, tasks, alerts, aggregate_query_history
-->

# Data Management and Operations Patterns for Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** The SQL in this quickstart uses string literals for clarity. Production OLTP workloads should use bound variables (parameterized queries). See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices).

As Hybrid Table workloads grow in production, three operational challenges emerge: analytics needs to join across multiple HTs from different domains, HT storage grows unboundedly and needs a tiering strategy, and sub-second OLTP queries are invisible to standard monitoring tools. This guide addresses all three.

### Patterns in This Guide

| Pattern | Freshness | Best For |
|---------|-----------|----------|
| Post-Load Foreign Key | One-time | Enforcing a relationship recognized after data already exists |
| Fan-In Aggregation | Minutes | Cross-domain analytics joining multiple HTs |
| Hot/Cold Data Tiering | Daily | Managing HT storage growth (2 TB quota per DB) |
| Alert-Based Monitoring | 3-hour view latency | Latency regression, throttling detection |

### Other Guides in This Series

- **[Analytics Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)** — Task snapshot, Dynamic Tables, MVs, Precomputed KPI serving
- **[Streaming and Change Detection](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)** — HT ingest buffer, watermark CDC, outbound event notifications

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Familiarity with Snowflake Tasks and AGGREGATE_QUERY_HISTORY

<!-- ------------------------ -->
## Setup

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_OPS_QS_ROLE;
GRANT ROLE HT_OPS_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_OPS_QS_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_OPS_QS_WH TO ROLE HT_OPS_QS_ROLE;

CREATE OR REPLACE DATABASE HT_OPS_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_OPS_QS_DB TO ROLE HT_OPS_QS_ROLE;

-- Every pattern in this guide is driven by a Task. Owning a task is not enough
-- to run one: the owner role needs the EXECUTE TASK privilege, or each run fails
-- with "Cannot execute task, EXECUTE TASK privilege must be granted to owner role".
GRANT EXECUTE TASK ON ACCOUNT TO ROLE HT_OPS_QS_ROLE;

USE ROLE HT_OPS_QS_ROLE;
CREATE OR REPLACE SCHEMA HT_OPS_QS_DB.DATA;
USE WAREHOUSE HT_OPS_QS_WH;
USE DATABASE HT_OPS_QS_DB;
USE SCHEMA DATA;
```

### Create Sample Hybrid Tables

```sql
CREATE OR REPLACE HYBRID TABLE orders (
    order_id     NUMBER NOT NULL,
    customer_id  NUMBER NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10) NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    total_amount NUMBER(12,2) NOT NULL,
    PRIMARY KEY (order_id),
    INDEX idx_orders_customer (customer_id),
    CONSTRAINT chk_order_status
      CHECK (status IN ('PENDING','SHIPPED','DELIVERED','CANCELLED'))
)
AS SELECT SEQ4(), UNIFORM(1,10000,RANDOM())::NUMBER,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    DATEADD(SECOND,UNIFORM(0,7776000,RANDOM()),DATEADD(DAY,-90,CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ,
    ROUND(UNIFORM(5.00,2500.00,RANDOM()),2)
FROM TABLE(GENERATOR(ROWCOUNT => 500000));

CREATE OR REPLACE HYBRID TABLE customers (
    customer_id   NUMBER NOT NULL,
    customer_name VARCHAR NOT NULL,
    tier          VARCHAR(20) NOT NULL,
    region        VARCHAR(10) NOT NULL,
    PRIMARY KEY (customer_id),
    CONSTRAINT chk_customer_tier
      CHECK (tier IN ('BRONZE','SILVER','GOLD','PLATINUM'))
)
AS SELECT SEQ4() + 1, 'customer_' || (SEQ4() + 1)::VARCHAR,
    ARRAY_CONSTRUCT('BRONZE','SILVER','GOLD','PLATINUM')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR
FROM TABLE(GENERATOR(ROWCOUNT => 10000));
```

Two details in that DDL matter for the rest of this guide.

**The customer keys are offset by one on purpose.** `SEQ4()` starts at zero, while `orders.customer_id`
is drawn from `UNIFORM(1, 10000, RANDOM())`. A bare `SEQ4()` would generate customers `0` through
`9999`, so every order that drew customer `10000` would have no matching parent row — enough to
prevent the foreign key you add in the next section from validating. `SEQ4() + 1` produces exactly
`1` through `10000` and makes the two key sets line up.

**Each table declares a `CHECK` constraint** for the vocabulary its generator produces: order status
and customer tier. On a hybrid table a `CHECK` constraint can only be declared when the table is
created, so it has to be part of this DDL rather than something you add later.

Confirm the key sets match before continuing:

```sql
SELECT MIN(customer_id) AS c_min, MAX(customer_id) AS c_max FROM customers;
-- Expected: 1, 10000

SELECT COUNT(*) AS orphan_orders
FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = o.customer_id);
-- Expected: 0
```

Each constraint rejects a value outside its list:

```sql
INSERT INTO orders VALUES (9999999, 1, 'REFUNDED', 'EU',
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 10.00);
```

```
001185 (23514): Operation on table ORDERS failed because CHECK constraint
CHK_ORDER_STATUS, which requires that status IN
('PENDING','SHIPPED','DELIVERED','CANCELLED'), was violated
```

<!-- ------------------------ -->
## Add the Foreign Key After Loading

`orders` and `customers` are related, but nothing yet enforces that relationship. Add it now, after
both tables are loaded, which is the normal situation in production: the relationship is recognized
after the data already exists rather than designed in from the start.

```sql
ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id);
```

### The DDL Result Does Not Mean It Worked

That statement returns `Statement executed successfully` immediately, which tells you the constraint
was accepted, not that it was validated. The supporting index builds asynchronously, and the only
way to see where it stands is `SHOW INDEXES`:

```sql
SHOW INDEXES IN TABLE orders;
```

Immediately after the `ALTER TABLE`, the new entry is still working:

| Index Name | Status | Status Info |
|------------|--------|-------------|
| FK_ORDERS_CUSTOMER | BUILD IN PROGRESS | The index is being built. |

Re-run `SHOW INDEXES` until it settles. On data with no orphans it reaches `ACTIVE`, which means the
rows already in the table have been validated and the index is available to serve queries:

| Index Name | Columns | Status |
|------------|---------|--------|
| FK_ORDERS_CUSTOMER | CUSTOMER_ID | ACTIVE |

> **Note:** Treat `SHOW INDEXES` as a required step whenever you add a foreign key to a table that
> already holds data. A successful DDL result tells you the constraint was accepted, not that the
> existing rows passed validation, and nothing raises an error to tell you otherwise.

### When Validation Fails

If the existing rows violate the constraint, the DDL still succeeds and the build still starts, then
ends in a terminal failure state. Introduce an order referencing a customer that does not exist and
watch it happen:

```sql
ALTER TABLE orders DROP CONSTRAINT fk_orders_customer;

INSERT INTO orders VALUES (9999998, 999999, 'PENDING', 'EU',
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 10.00);

ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id);
```

The `ALTER TABLE` reports success. `SHOW INDEXES` reports what actually happened:

| Index Name | Status | Status Info |
|------------|--------|-------------|
| FK_ORDERS_CUSTOMER | BUILD VALIDATION FAILURE | Index creation failed validation. The existing data violates the constraint. Please review the data, resolve the violations, and try creating the constraint again. |

This state is easy to misread, so it is worth being precise about what it means. A constraint left in
`BUILD VALIDATION FAILURE` **still enforces every new write**. Statements that would violate it fail,
valid statements succeed, and `TRUNCATE TABLE` on the referenced table fails. Only the rows that were
already in the table when you added the constraint remain unvalidated. The constraint is not inert —
it is half-applied, which is the more dangerous condition: the orphans you already had are still
there, while the table behaves as though the relationship holds.

It is also nearly invisible. `SHOW INDEXES` is the only command that reports this state.
`SHOW IMPORTED KEYS`, `SHOW PRIMARY KEYS`, the `TABLE_CONSTRAINTS` view, and `GET_DDL` all list the
constraint exactly as they would if it had validated. Treat a validation failure as something to
investigate, not something to retry.

A failed constraint does not repair itself and cannot be retried in place. Drop it, fix the data,
then add it again:

```sql
ALTER TABLE orders DROP CONSTRAINT fk_orders_customer;

DELETE FROM orders
WHERE customer_id NOT IN (SELECT customer_id FROM customers);

ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id);
```

Confirm it reaches `ACTIVE` before relying on it.

### What the Constraint Changes for the Patterns Below

Once the foreign key is active, `customers` is a parent table and deleting from it is restricted
while matching orders exist:

```sql
DELETE FROM customers WHERE customer_id = 1;
```

```
200008 (22000): Foreign keys that reference key values still exist.
```

That matters for the tiering pattern in Step 2. Archiving removes rows from `orders`, the child
side, which the constraint permits. Any process that removes customers has to deal with their orders
first. It is also why you should not reach for dropping the foreign key as a way around a failed
delete — that trades referential integrity for convenience, and the constraint has to be rebuilt and
revalidated afterward.

<!-- ------------------------ -->
## Step 1: Fan-In Aggregation

In production, multiple Hybrid Tables often serve different domains (orders, customers, inventory). Analytics teams need to join across these domains — but running a large JOIN directly across multiple HTs produces multiple COLUMN_BASED scans. The fan-in pattern consolidates the data into a single denormalized standard table.

### Full Refresh Fan-In (CTAS)

For smaller datasets (up to a few million rows), a full CTAS refresh is simple and reliable:

```sql
CREATE OR REPLACE TASK refresh_consolidated_analytics
  WAREHOUSE = HT_OPS_QS_WH
  SCHEDULE = '15 MINUTES'
AS
  CREATE OR REPLACE TABLE consolidated_orders AS
  SELECT
    o.order_id,
    o.customer_id,
    c.customer_name,
    c.tier          AS customer_tier,
    o.status,
    o.region,
    o.created_at,
    o.total_amount
  FROM orders o
  LEFT JOIN customers c ON o.customer_id = c.customer_id;

ALTER TASK refresh_consolidated_analytics RESUME;
```

Resuming the task schedules it; it does not run it. On a 15-minute schedule the first run can be up
to fifteen minutes away, and `consolidated_orders` does not exist until that run completes. Trigger
one now so you can verify the pattern immediately:

```sql
EXECUTE TASK refresh_consolidated_analytics;
```

That submits a run rather than waiting for it, so give it a few seconds and confirm it finished
before querying the table:

```sql
SELECT NAME, STATE, SCHEDULED_TIME, COMPLETED_TIME, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    TASK_NAME => 'REFRESH_CONSOLIDATED_ANALYTICS'))
WHERE COMPLETED_TIME IS NOT NULL
ORDER BY COMPLETED_TIME DESC
LIMIT 5;
-- Wait for the most recent row to show STATE = SUCCEEDED before continuing
```

The `COMPLETED_TIME IS NOT NULL` filter matters. Because the task is resumed, the history also
contains a row for the next scheduled run with `STATE = SCHEDULED`, and that row sorts first by
scheduled time even though it has not run. Filtering to completed runs shows only what actually
executed.

Verify:

```sql
SELECT COUNT(*) AS consolidated_rows FROM consolidated_orders;
-- Expected: 500000
```

```sql
SELECT customer_tier, COUNT(*), SUM(total_amount) FROM consolidated_orders GROUP BY customer_tier;

ALTER TASK refresh_consolidated_analytics SUSPEND;
```

The join is written as a `LEFT JOIN` so the fan-in never silently drops an order. With the foreign
key active that distinction no longer changes the result, because every order is guaranteed a parent:

```sql
SELECT COUNT(*) AS rows_missing_customer
FROM consolidated_orders WHERE customer_name IS NULL;
-- Expected: 0
```

Before the key sets were aligned, that query returned a non-zero count and the `LEFT JOIN` was the
only reason those orders appeared in the output at all, with null customer attributes. Keep the
`LEFT JOIN` as a safety net, but treat a non-zero result here as a signal that something upstream has
broken the relationship.

> **Note:** Keep this aggregation in a Task, not an Inline Stored Procedure. It reads a hybrid table
> and writes a standard table, and an Inline Stored Procedure can only touch hybrid tables in a single
> database. It also uses DDL, which an Inline Stored Procedure does not allow. `CREATE OR REPLACE
> TABLE` is already atomic, so there is nothing to gain by wrapping it.

### Incremental Fan-In (MERGE)

For larger datasets where a full CTAS is too slow, use MERGE per source table:

```sql
-- Run as separate tasks or combine into a single Task with scripting
MERGE INTO consolidated_orders AS tgt
USING (
    SELECT o.order_id, o.customer_id, c.customer_name, c.tier AS customer_tier,
           o.status, o.region, o.created_at, o.total_amount
    FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.created_at > DATEADD(MINUTE, -20, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
) AS src
ON tgt.order_id = src.order_id
WHEN MATCHED AND tgt.status != src.status THEN UPDATE SET tgt.status = src.status, tgt.customer_tier = src.customer_tier
WHEN NOT MATCHED THEN INSERT VALUES (src.order_id, src.customer_id, src.customer_name, src.customer_tier, src.status, src.region, src.created_at, src.total_amount);
```

### When to Use Full Refresh vs Incremental

| | Full Refresh (CTAS) | Incremental (MERGE) |
|--|---------------------|---------------------|
| Dataset size | Up to ~5M rows | Any size |
| Source tables with deletions | Correct (rebuilds entire result) | Requires delete handling |
| Complexity | Low | Medium |
| Downtime during refresh | None (CTAS is atomic) | None |

<!-- ------------------------ -->
## Step 2: Hot/Cold Data Tiering

Hybrid Tables are optimized for recent, actively-queried data. Historical rows that are rarely accessed should be moved to standard tables where they benefit from columnar compression, clustering, and lower storage costs.

**Why tiering matters:**
- Hybrid Table storage quota: **2 TB per database**
- Keeping all-time historical data in a HT means the row store grows unboundedly
- Each row in the HT occupies row-store space; old rows that are never point-looked-up waste that space
- Platform background maintenance jobs scale with HT row count — keeping the HT small keeps maintenance fast

### Create the Archive Table

```sql
CREATE OR REPLACE TABLE orders_archive (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL,
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    total_amount NUMBER(12,2)  NOT NULL,
    archived_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (created_at);
```

### Age-Off Task

```sql
CREATE OR REPLACE TASK archive_old_orders
  WAREHOUSE = HT_OPS_QS_WH
  SCHEDULE = 'USING CRON 0 2 * * * UTC'
AS
BEGIN
  INSERT INTO orders_archive (order_id, customer_id, status, region, created_at, total_amount)
    SELECT order_id, customer_id, status, region, created_at, total_amount
    FROM orders
    WHERE created_at < DATEADD(DAY, -90, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;

  DELETE FROM orders
    WHERE created_at < DATEADD(DAY, -90, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;
END;
```

Test the archive manually:

```sql
INSERT INTO orders_archive (order_id, customer_id, status, region, created_at, total_amount)
  SELECT order_id, customer_id, status, region, created_at, total_amount
  FROM orders
  WHERE created_at < DATEADD(DAY, -60, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;

SELECT COUNT(*) AS archived_rows FROM orders_archive;

DELETE FROM orders
  WHERE created_at < DATEADD(DAY, -60, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;

SELECT COUNT(*) AS remaining_in_ht FROM orders;
```

### Query Across Hot and Cold

```sql
CREATE OR REPLACE VIEW orders_all AS
  SELECT order_id, customer_id, status, region, created_at, total_amount FROM orders
  UNION ALL
  SELECT order_id, customer_id, status, region, created_at, total_amount FROM orders_archive;

SELECT COUNT(*) FROM orders_all;
```

### Storage Sizing Notes

- DELETE from HT reclaims space via background compaction — space is recovered over hours, not instantly
- The archive standard table compresses to ~20-30% of its raw size using columnar compression
- Cluster the archive table on `created_at` for fast historical range scans

### Why This Stays Outside an Inline Stored Procedure

The age-off task moves rows from a hybrid table into a standard table and then deletes them. That
spans two table types, so it is not eligible for an Inline Stored Procedure, which is restricted to
hybrid tables within one database. A Task is the right container here.

Note also which side of the relationship this pattern touches. Archiving deletes from `orders`, the
child table, which the foreign key permits. If you later add a tiering process for `customers`, it
has to archive or reassign the matching orders first, or the delete fails with `200008`.

<!-- ------------------------ -->
## Step 3: Alert-Based Monitoring

Hybrid Table queries that complete in under 1 second do not appear in `QUERY_HISTORY`. Use `SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY` — which captures all queries aggregated in 1-minute windows — for monitoring and alerting.

### Query Top Workloads

```sql
SELECT
    query_parameterized_hash,
    ANY_VALUE(query_text)              AS sample_query,
    SUM(calls)                         AS total_executions,
    AVG(total_elapsed_time:"avg"::FLOAT) AS avg_latency_ms,
    MAX(total_elapsed_time:"p99"::FLOAT) AS p99_latency_ms
FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
WHERE interval_start_time > DATEADD(DAY, -1, CURRENT_TIMESTAMP())
  AND warehouse_name = 'HT_OPS_QS_WH'
GROUP BY query_parameterized_hash
ORDER BY total_executions DESC
LIMIT 10;
```

### Monitor Throttling

```sql
SELECT
    interval_start_time,
    SUM(calls)                                  AS total_calls,
    SUM(hybrid_table_requests_throttled_count)  AS throttled_requests
FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
WHERE interval_start_time > DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
  AND hybrid_table_requests_throttled_count > 0
GROUP BY interval_start_time
ORDER BY interval_start_time DESC;
```

### Create an Alert Log Table

```sql
CREATE OR REPLACE TABLE alert_log (
    alert_ts    TIMESTAMP_NTZ,
    alert_type  VARCHAR,
    message     VARCHAR
);
```

### Create a Throttling Alert

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ALERT ht_throttle_alert
  WAREHOUSE = HT_OPS_QS_WH
  SCHEDULE = '5 MINUTE'
  IF( EXISTS(
    SELECT 1
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE hybrid_table_requests_throttled_count > 50
      AND interval_start_time > DATEADD(MINUTE, -10, CURRENT_TIMESTAMP())
  ))
  THEN
    INSERT INTO HT_OPS_QS_DB.DATA.alert_log
    VALUES (CURRENT_TIMESTAMP(), 'THROTTLE', 'More than 50 throttled HT requests in the last 10 minutes');

ALTER ALERT ht_throttle_alert RESUME;
USE ROLE HT_OPS_QS_ROLE;
```

Verify:

```sql
SHOW ALERTS;
SELECT * FROM alert_log ORDER BY alert_ts DESC;

-- Suspend the alert after this quickstart
USE ROLE ACCOUNTADMIN;
ALTER ALERT ht_throttle_alert SUSPEND;
USE ROLE HT_OPS_QS_ROLE;
```

### AGGREGATE_QUERY_HISTORY Notes

- **Latency:** Up to 3 hours. Not suitable for real-time alerting. Use Query Profile for immediate diagnosis.
- **Sub-second queries:** All queries appear regardless of duration, aggregated per 1-minute window.
- **Key columns:** `calls`, `total_elapsed_time` (with sub-fields `avg`, `p90`, `p99`, `max`), `hybrid_table_requests_throttled_count`, `errors`.

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your own workload:

> "Assess my Hybrid Table for hot/cold data tiering opportunities. My schema is: [paste DDL]. Recommend a tiering strategy and generate the Task SQL to move cold rows to a Standard Table."

> "Design a fan-in aggregation pipeline for my Hybrid Table. I have [N] source tables writing to a single HT. Generate the MERGE task that prevents lock contention."

> "Generate Snowflake Alert SQL to notify me when my Hybrid Table p99 latency exceeds 100ms or my error rate exceeds 1% over the past hour."

<!-- ------------------------ -->
## Cleanup

```sql
ALTER TASK IF EXISTS refresh_consolidated_analytics SUSPEND;
ALTER TASK IF EXISTS archive_old_orders SUSPEND;
USE ROLE ACCOUNTADMIN;
ALTER ALERT IF EXISTS ht_throttle_alert SUSPEND;
DROP ALERT IF EXISTS ht_throttle_alert;
DROP DATABASE IF EXISTS HT_OPS_QS_DB;
DROP WAREHOUSE IF EXISTS HT_OPS_QS_WH;
DROP ROLE IF EXISTS HT_OPS_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now:
- Enforce a relationship on data that already exists by adding a foreign key after load, and confirm it validated instead of trusting the DDL result
- Constrain column vocabularies with `CHECK` constraints declared at table creation
- Consolidate multiple Hybrid Tables into a single analytics surface using fan-in aggregation
- Tier hot/cold data to manage HT storage growth and keep the row store performant
- Monitor HT workloads with AGGREGATE_QUERY_HISTORY for sub-second query visibility
- Create automated throttling and latency alerts

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Streaming and Change Detection Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)
- [Architectural Patterns Overview and Decision Matrix](https://www.snowflake.com/en/developers/guides/hybrid-tables-architectural-patterns/)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [AGGREGATE_QUERY_HISTORY View](https://docs.snowflake.com/en/sql-reference/account-usage/aggregate_query_history)
- [Snowflake Alerts](https://docs.snowflake.com/en/user-guide/alerts)

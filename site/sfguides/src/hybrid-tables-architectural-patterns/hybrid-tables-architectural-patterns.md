author: Adam Timm
id: hybrid-tables-architectural-patterns
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn architectural patterns for integrating Hybrid Tables with analytics pipelines, change detection, event-driven architectures, and operational monitoring.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, architectural patterns, Task, MERGE, snapshot, Dynamic Table, Materialized View, change detection, watermark, event-driven, Kafka, SNS, notification, alert, AGGREGATE_QUERY_HISTORY, hot cold tiering, fan-in, Unistore, OLTP, analytics
related_concepts: Streams limitation, DT limitation, MV limitation, result cache, COLUMN_BASED scan, ROW_BASED scan, bound variables, plan cache, freshness SLA
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-standard-to-hybrid-migration
skill_level: advanced
estimated_time_minutes: 60
snowflake_features: hybrid_tables, tasks, merge, dynamic_tables, materialized_views, alerts, notification_integrations, aggregate_query_history
-->

# Architectural Patterns for Hybrid Table Workloads
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** The SQL in this quickstart uses string literals for clarity. Production OLTP workloads should use bound variables (parameterized queries) so Snowflake can cache and reuse query plans. See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices) and [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test).

Hybrid Tables are optimized for low-latency point lookups and small transactional writes. They are not designed for analytical workloads. Several Snowflake features commonly used in analytics pipelines are not available on Hybrid Tables:

- **Streams** (change tracking)
- **Dynamic Tables** (cannot read from a HT)
- **Materialized Views** (cannot be created on a HT)
- **Result cache** (does not apply to HT queries)
- **Clustering keys** (HT uses indexes instead)

This does not mean you cannot do analytics on Hybrid Table data. It means you need an architectural layer between the Hybrid Table and your analytics consumers. This quickstart teaches eight patterns that address these limitations.

### Scenario

You operate the order management backend for an e-commerce platform. The `orders` Hybrid Table handles real-time writes and point lookups from your application. Business teams need dashboards, change feeds, and historical archives from this same data. You will build the pipeline layer that bridges operational and analytical needs.

### What You Will Learn

- Why running analytics directly on a Hybrid Table is an anti-pattern
- How to snapshot HT data to a standard table using scheduled Tasks and MERGE
- How to detect changes without Streams using timestamp watermarks
- How to publish events to external systems (SNS, PubSub, webhooks) from HT data
- How to layer Dynamic Tables and Materialized Views on the standard table copy
- How to consolidate multiple HTs into a single analytics table (fan-in)
- How to tier hot/cold data between Hybrid and standard tables
- How to monitor HT workloads with AGGREGATE_QUERY_HISTORY and Snowflake Alerts

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Completion of [Converting Standard Tables to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-standard-to-hybrid-migration/) (recommended)
- Familiarity with Snowflake Tasks, MERGE, and query profiles

<!-- ------------------------ -->
## Setup

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_ARCH_QS_ROLE;
GRANT ROLE HT_ARCH_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_ARCH_QS_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_ARCH_QS_WH TO ROLE HT_ARCH_QS_ROLE;

CREATE OR REPLACE DATABASE HT_ARCH_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_ARCH_QS_DB TO ROLE HT_ARCH_QS_ROLE;

USE ROLE HT_ARCH_QS_ROLE;

CREATE OR REPLACE SCHEMA HT_ARCH_QS_DB.DATA;

USE WAREHOUSE HT_ARCH_QS_WH;
USE DATABASE HT_ARCH_QS_DB;
USE SCHEMA DATA;
```

### Create the Hybrid Table

```sql
CREATE OR REPLACE HYBRID TABLE orders (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2)  NOT NULL,
    PRIMARY KEY (order_id),
    INDEX idx_orders_customer_id (customer_id),
    INDEX idx_orders_status_region_ts (status, region, created_at)
)
AS SELECT
    SEQ4()                                                AS order_id,
    UNIFORM(1, 10000, RANDOM())::NUMBER                  AS customer_id,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')
        [UNIFORM(0, 3, RANDOM())]::VARCHAR               AS status,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')
        [UNIFORM(0, 3, RANDOM())]::VARCHAR               AS region,
    DATEADD(SECOND,
        UNIFORM(0, 7776000, RANDOM()),
        DATEADD(DAY, -90, CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ  AS created_at,
    NULL::TIMESTAMP_NTZ                                  AS updated_at,
    ROUND(UNIFORM(5.00, 2500.00, RANDOM()), 2)           AS total_amount
FROM TABLE(GENERATOR(ROWCOUNT => 500000));
```

Verify the table:

```sql
SELECT COUNT(*) FROM orders;
-- Expected: 500000
```

<!-- ------------------------ -->
## Step 1: The Analytics Anti-Pattern

Before building the pipeline layer, observe what happens when you run analytics directly on the Hybrid Table.

```sql
SELECT region, status, COUNT(*) AS order_count, SUM(total_amount) AS revenue
FROM orders
GROUP BY region, status
ORDER BY revenue DESC;
```

Open the Query Profile. You will see:
- Operator: `TableScan`
- Scan Mode: `COLUMN_BASED`
- Rows scanned: ~500,000 (full table)

This query reads the entire column-store copy of the data. It works, but:
- No result cache means it rescans on every execution
- No clustering means no partition pruning
- No Materialized View means no precomputation
- Latency is hundreds of milliseconds to seconds, not the single-digit ms you expect from HT

For a BI tool executing this every 30 seconds for a dashboard refresh, you are paying full scan cost every time. The solution: snapshot the data to a standard table where all analytics features are available.

<!-- ------------------------ -->
## Step 2: Task-Based Snapshot (MERGE Pattern)

The canonical pattern for bridging HT to analytics is a scheduled Task that uses MERGE to keep a standard table copy in sync.

### Create the Standard Table Mirror

```sql
CREATE OR REPLACE TABLE orders_analytics (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL,
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2)  NOT NULL,
    snapshot_ts  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

### Initial Load

```sql
INSERT INTO orders_analytics (order_id, customer_id, status, region, created_at, updated_at, total_amount)
SELECT order_id, customer_id, status, region, created_at, updated_at, total_amount
FROM orders;
```

### Create the Snapshot Task

```sql
CREATE OR REPLACE TASK snapshot_orders_to_analytics
  WAREHOUSE = HT_ARCH_QS_WH
  SCHEDULE = '5 MINUTES'
AS
  MERGE INTO orders_analytics AS tgt
  USING orders AS src
  ON tgt.order_id = src.order_id
  WHEN MATCHED AND (src.status != tgt.status OR src.updated_at != tgt.updated_at OR src.total_amount != tgt.total_amount)
    THEN UPDATE SET
      tgt.status = src.status,
      tgt.updated_at = src.updated_at,
      tgt.total_amount = src.total_amount,
      tgt.snapshot_ts = CURRENT_TIMESTAMP()
  WHEN NOT MATCHED
    THEN INSERT (order_id, customer_id, status, region, created_at, updated_at, total_amount, snapshot_ts)
    VALUES (src.order_id, src.customer_id, src.status, src.region, src.created_at, src.updated_at, src.total_amount, CURRENT_TIMESTAMP());

ALTER TASK snapshot_orders_to_analytics RESUME;
```

### Verify the Task

```sql
SHOW TASKS;
```

The task will run every 5 minutes, merging any new or updated rows from the Hybrid Table into the standard analytics table. BI tools and dashboards should read from `orders_analytics`, not directly from `orders`.

> **Note:** The MERGE scans the full Hybrid Table on each execution (COLUMN_BASED). For tables with millions of rows, consider adding a watermark filter (covered in Step 3) to limit the scan to recently modified rows.

### Pause the Task (for this quickstart)

```sql
ALTER TASK snapshot_orders_to_analytics SUSPEND;
```

<!-- ------------------------ -->
## Step 3: HT as Ingest Buffer with Real-Time Rollup and Data Share Delivery

This pattern is common in high-frequency streaming workloads (financial data, IoT, clickstreams) where an external system writes to a Hybrid Table continuously and a downstream consumer needs a fresh aggregated view delivered in real time.

The key insight: **the Hybrid Table is not the permanent store**. Its PRIMARY KEY enforces exactly-once deduplication on ingest. A fast serverless Task flushes new rows to a clustered standard table every 30 seconds, computes the rollup there (where columnar GROUP BY is 50-100x faster than KV storage), and the HT is intentionally kept small via a rolling retention window.

### The Problem This Solves

A naive approach uses the Hybrid Table for both ingest and aggregation. As rows accumulate through the day, the cumulative GROUP BY must scan an ever-growing dataset through FoundationDB's KV storage. At 500K rows the scan takes ~17 seconds; at 2.35M rows (mid-session) it takes 35 seconds; by end of day it can reach 2 minutes — well past any reasonable SLA.

The fix is separating the two concerns: **HT handles ingest and dedup, standard table handles aggregation**.

### Architecture

```
[External Source]                   [Hybrid Table]
(Kafka / app)   -- JDBC INSERT -->  PK: dedup guarantee
                                    Retention: 2-4 hours only
                                         |
                                    Task (30s serverless)
                                    1. Delta INSERT → ST
                                    2. GROUP BY on ST (columnar)
                                    3. INSERT OVERWRITE rollup
                                    4. Advance checkpoint
                                         |
                              +----------+----------+
                              |                     |
                      [raw_events_st]       [events_rollup]
                      Permanent record      TRANSIENT, 0-day retention
                      Clustered columnar    INSERT OVERWRITE (no churn)
                              |                     |
                              └──── Data Share ──────┘
                                    Consumer queries live SQL
                                    No CSV, no file polling
```

### Create the Tables

The Hybrid Table serves as the ingest buffer. Its PRIMARY KEY enforces exactly-once delivery — duplicate writes from the producer are silently rejected:

```sql
CREATE OR REPLACE HYBRID TABLE events_ht (
    event_id      VARCHAR       NOT NULL,
    source_id     VARCHAR       NOT NULL,
    event_type    VARCHAR       NOT NULL,
    region        VARCHAR(10)   NOT NULL,
    value         NUMBER(12,4)  NOT NULL,
    event_ts      TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (event_id),
    INDEX idx_events_source_ts (source_id, event_ts)
);
```

The standard table is the permanent columnar record, clustered for fast range scans:

```sql
CREATE OR REPLACE TABLE raw_events_st (
    event_id      VARCHAR       NOT NULL,
    source_id     VARCHAR       NOT NULL,
    event_type    VARCHAR       NOT NULL,
    region        VARCHAR(10)   NOT NULL,
    value         NUMBER(12,4)  NOT NULL,
    event_ts      TIMESTAMP_NTZ NOT NULL,
    ingested_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (event_type, event_ts);
```

The rollup table is TRANSIENT with zero retention — it is a derived artifact, always recomputable from `raw_events_st`:

```sql
CREATE OR REPLACE TRANSIENT TABLE events_rollup (
    event_type    VARCHAR       NOT NULL,
    region        VARCHAR(10)   NOT NULL,
    event_count   NUMBER        NOT NULL,
    total_value   NUMBER(12,4)  NOT NULL,
    min_value     NUMBER(12,4)  NOT NULL,
    max_value     NUMBER(12,4)  NOT NULL,
    window_start  TIMESTAMP_NTZ NOT NULL,
    last_updated  TIMESTAMP_NTZ NOT NULL
)
DATA_RETENTION_TIME_IN_DAYS = 0;
```

The checkpoint table tracks the last flushed timestamp per window:

```sql
CREATE OR REPLACE TABLE events_checkpoint (
    window_date    DATE          NOT NULL,
    last_flush_ts  TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (window_date)
);

INSERT INTO events_checkpoint VALUES (CURRENT_DATE(), '1970-01-01'::TIMESTAMP_NTZ);
```

### Load Sample Data into the HT Buffer

```sql
INSERT INTO events_ht (event_id, source_id, event_type, region, value, event_ts)
SELECT
    'evt_' || SEQ4()::VARCHAR,
    'src_' || UNIFORM(1, 100, RANDOM())::VARCHAR,
    ARRAY_CONSTRUCT('CLICK','VIEW','PURCHASE','CANCEL')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ROUND(UNIFORM(0.01, 999.99, RANDOM()), 4),
    DATEADD(SECOND, UNIFORM(0, 3600, RANDOM()),
        DATEADD(HOUR, -2, CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ
FROM TABLE(GENERATOR(ROWCOUNT => 100000));
```

### Create the 30-Second Serverless Task

```sql
CREATE OR REPLACE TASK events_pipeline_30s
  SCHEDULE = '30 SECONDS'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
DECLARE
  v_today      DATE          := CURRENT_DATE();
  v_now        TIMESTAMP_NTZ := CURRENT_TIMESTAMP()::TIMESTAMP_NTZ;
  v_checkpoint TIMESTAMP_NTZ;
BEGIN
  SELECT last_flush_ts INTO v_checkpoint
  FROM events_checkpoint WHERE window_date = :v_today;

  -- Step 1: Delta flush — only new rows since last checkpoint
  -- Uses the secondary index on (source_id, event_ts) for a fast seek
  INSERT INTO raw_events_st (event_id, source_id, event_type, region, value, event_ts)
  SELECT event_id, source_id, event_type, region, value, event_ts
  FROM events_ht
  WHERE event_ts > :v_checkpoint
    AND event_ts <= :v_now;

  -- Step 2: Cumulative rollup on the standard table (columnar GROUP BY, ~100ms at 500K rows)
  -- INSERT OVERWRITE atomically replaces all rows — no DELETE + INSERT micro-partition churn
  INSERT OVERWRITE INTO events_rollup
  SELECT
    event_type,
    region,
    COUNT(*)                    AS event_count,
    SUM(value)                  AS total_value,
    MIN(value)                  AS min_value,
    MAX(value)                  AS max_value,
    MIN(event_ts)               AS window_start,
    :v_now                      AS last_updated
  FROM raw_events_st
  WHERE event_ts::DATE = :v_today
  GROUP BY event_type, region;

  -- Step 3: Advance checkpoint
  MERGE INTO events_checkpoint AS tgt
  USING (SELECT :v_today AS window_date, :v_now AS last_flush_ts) AS src
  ON tgt.window_date = src.window_date
  WHEN MATCHED THEN UPDATE SET tgt.last_flush_ts = src.last_flush_ts
  WHEN NOT MATCHED THEN INSERT (window_date, last_flush_ts) VALUES (src.window_date, src.last_flush_ts);
END;

ALTER TASK events_pipeline_30s RESUME;
```

> **Note:** `INSERT OVERWRITE` is critical here. Refreshing a rollup table 2,880 times per day (30s interval) with `DELETE + INSERT` would accumulate deleted micro-partitions in Time Travel storage. `INSERT OVERWRITE` atomically replaces the data without creating Time Travel overhead. Combined with `DATA_RETENTION_TIME_IN_DAYS = 0` (TRANSIENT table), there is zero storage churn from the rollup refreshes.

### Verify the Pipeline

```sql
-- Confirm delta flush populated the standard table
SELECT COUNT(*) FROM raw_events_st;

-- Check the rollup
SELECT * FROM events_rollup ORDER BY total_value DESC;

-- Confirm checkpoint advanced
SELECT * FROM events_checkpoint;
```

### Maintain the HT Buffer Window

Once `raw_events_st` is the permanent record, purge the HT periodically to keep it small. This is the key that makes the pattern sustainable: a small HT means fast ingest, fast dedup, and fast platform maintenance jobs.

```sql
CREATE OR REPLACE TASK purge_ht_buffer
  SCHEDULE = 'USING CRON 0 * * * * UTC'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
  DELETE FROM events_ht
  WHERE event_ts < DATEADD(HOUR, -4, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;

ALTER TASK purge_ht_buffer RESUME;
```

### Deliver via Data Share (Optional)

Replace file-based delivery with a live Data Share. Consumers query `events_rollup` directly as a standard Snowflake table — always current, no file management:

```sql
-- Run as ACCOUNTADMIN
CREATE SHARE events_data_share;
GRANT USAGE ON DATABASE HT_ARCH_QS_DB TO SHARE events_data_share;
GRANT USAGE ON SCHEMA HT_ARCH_QS_DB.DATA TO SHARE events_data_share;
GRANT SELECT ON TABLE HT_ARCH_QS_DB.DATA.events_rollup TO SHARE events_data_share;
-- ALTER SHARE events_data_share ADD ACCOUNTS = <consumer_account>;
```

### Pause the Tasks (for this quickstart)

```sql
ALTER TASK events_pipeline_30s SUSPEND;
ALTER TASK purge_ht_buffer SUSPEND;
```

### When to Use This Pattern

- High-frequency streaming ingest (financial data, IoT sensors, clickstreams) where exactly-once delivery matters
- Consumer needs a fresh aggregated view, not raw rows
- Current pipeline uses Python + file export — replace with serverless Task + Data Share
- HT is growing unboundedly because it's used for both ingest and long-term storage

<!-- ------------------------ -->
## Step 4: Change Detection Without Streams

Since Streams are not supported on Hybrid Tables, you need an alternative to detect which rows changed since the last sync. The timestamp watermark pattern uses an `updated_at` column to track modifications.

### Simulate Updates

First, add some updates to the Hybrid Table so there is changed data to detect:

```sql
UPDATE orders
SET status = 'SHIPPED', updated_at = CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
WHERE order_id IN (SELECT order_id FROM orders WHERE status = 'PENDING' LIMIT 100);
```

### Watermark-Based Incremental Sync

Track the last sync time and only merge rows modified after that point:

```sql
CREATE OR REPLACE TABLE sync_watermarks (
    table_name   VARCHAR NOT NULL,
    last_sync_ts TIMESTAMP_NTZ NOT NULL
);

INSERT INTO sync_watermarks VALUES ('orders', '2000-01-01'::TIMESTAMP_NTZ);
```

### Incremental MERGE with Watermark

```sql
SET last_watermark = (SELECT last_sync_ts FROM sync_watermarks WHERE table_name = 'orders');
SET current_watermark = CURRENT_TIMESTAMP()::TIMESTAMP_NTZ;

MERGE INTO orders_analytics AS tgt
USING (
    SELECT * FROM orders
    WHERE updated_at > $last_watermark
       OR created_at > $last_watermark
) AS src
ON tgt.order_id = src.order_id
WHEN MATCHED
  THEN UPDATE SET
    tgt.status = src.status,
    tgt.updated_at = src.updated_at,
    tgt.total_amount = src.total_amount,
    tgt.snapshot_ts = $current_watermark
WHEN NOT MATCHED
  THEN INSERT (order_id, customer_id, status, region, created_at, updated_at, total_amount, snapshot_ts)
  VALUES (src.order_id, src.customer_id, src.status, src.region, src.created_at, src.updated_at, src.total_amount, $current_watermark);

UPDATE sync_watermarks SET last_sync_ts = $current_watermark WHERE table_name = 'orders';
```

### Requirements for This Pattern

- The Hybrid Table must have an `updated_at` column that your application sets on every UPDATE
- New inserts must set `created_at` to the current timestamp
- The watermark query uses an index on `updated_at` or `created_at` if one exists (otherwise COLUMN_BASED scan)

### Periodic Full Reconciliation

Watermarks can miss rows if application bugs skip setting `updated_at`. Run a full MERGE periodically (daily or weekly) as a safety net:

```sql
-- Full reconciliation (no watermark filter)
MERGE INTO orders_analytics AS tgt
USING orders AS src
ON tgt.order_id = src.order_id
WHEN MATCHED AND (src.status != tgt.status OR src.total_amount != tgt.total_amount)
  THEN UPDATE SET tgt.status = src.status, tgt.updated_at = src.updated_at,
    tgt.total_amount = src.total_amount, tgt.snapshot_ts = CURRENT_TIMESTAMP()
WHEN NOT MATCHED
  THEN INSERT (order_id, customer_id, status, region, created_at, updated_at, total_amount, snapshot_ts)
  VALUES (src.order_id, src.customer_id, src.status, src.region, src.created_at, src.updated_at, src.total_amount, CURRENT_TIMESTAMP());
```

<!-- ------------------------ -->
## Step 5: Event-Driven CDC (External Notifications)

For systems that need real-time event delivery (Kafka consumers, microservices, alerting), Snowflake can publish notifications to cloud queues and webhooks.

> **Note:** This step covers *outbound* event delivery — publishing events from Snowflake to external systems. For *inbound* Kafka ingestion (streaming Kafka data into a Hybrid Table), see the [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/) quickstart, which covers the Spring Boot + JDBC micro-batch pattern.

### Architecture

```
[Application] --> [Hybrid Table] --> [Task (polls for changes)]
                                          |
                                          v
                                  [Notification Integration]
                                          |
                          +---------------+---------------+
                          |               |               |
                     [AWS SNS]    [GCP PubSub]    [Webhook/Slack]
```

### Create a Notification Integration (AWS SNS Example)

```sql
-- This requires ACCOUNTADMIN for the integration creation
-- Replace ARNs with your actual values
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NOTIFICATION INTEGRATION orders_sns_integration
  TYPE = QUEUE
  NOTIFICATION_PROVIDER = AWS_SNS
  DIRECTION = OUTBOUND
  AWS_SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:123456789012:order-events'
  AWS_SNS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-sns-role';

GRANT USAGE ON INTEGRATION orders_sns_integration TO ROLE HT_ARCH_QS_ROLE;

USE ROLE HT_ARCH_QS_ROLE;
```

### Task-Based Event Publisher

```sql
CREATE OR REPLACE TASK publish_order_events
  WAREHOUSE = HT_ARCH_QS_WH
  SCHEDULE = '1 MINUTES'
AS
DECLARE
  new_orders NUMBER;
BEGIN
  SELECT COUNT(*) INTO new_orders
  FROM orders
  WHERE created_at > DATEADD(MINUTE, -1, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;

  IF (new_orders > 0) THEN
    CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
      SNOWFLAKE.NOTIFICATION.TEXT_PLAIN(
        :new_orders || ' new orders in the last minute'
      ),
      SNOWFLAKE.NOTIFICATION.INTEGRATION('orders_sns_integration')
    );
  END IF;
END;
```

> **Note:** This pattern provides near-real-time event delivery (1-minute granularity). For true sub-second event streaming, the application layer should publish events directly to Kafka/SNS at write time, in addition to writing to the Hybrid Table.

### Webhook Alternative (Slack/Teams)

For simpler notifications, use a webhook integration:

```sql
-- CREATE NOTIFICATION INTEGRATION orders_webhook
--   TYPE = WEBHOOK
--   WEBHOOK_URL = 'https://hooks.slack.com/services/...'
--   WEBHOOK_BODY_TEMPLATE = '{"text": "SNOWFLAKE_WEBHOOK_MESSAGE"}'
--   WEBHOOK_HEADERS = ('Content-Type'='application/json');
```

<!-- ------------------------ -->
## Step 6: Dynamic Tables on the Standard Table Copy

Now that `orders_analytics` is being maintained by the snapshot Task, you can layer Dynamic Tables on top for derived datasets.

### Create a Regional Revenue Summary DT

```sql
CREATE OR REPLACE DYNAMIC TABLE regional_revenue
  TARGET_LAG = '10 MINUTES'
  WAREHOUSE = HT_ARCH_QS_WH
AS
  SELECT
    region,
    DATE_TRUNC('day', created_at) AS order_date,
    COUNT(*) AS order_count,
    SUM(total_amount) AS daily_revenue,
    AVG(total_amount) AS avg_order_value
  FROM orders_analytics
  GROUP BY region, DATE_TRUNC('day', created_at);
```

### Create a Customer Activity DT

```sql
CREATE OR REPLACE DYNAMIC TABLE customer_activity
  TARGET_LAG = '10 MINUTES'
  WAREHOUSE = HT_ARCH_QS_WH
AS
  SELECT
    customer_id,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS lifetime_value,
    MAX(created_at) AS last_order_at,
    COUNT_IF(status = 'PENDING') AS pending_orders
  FROM orders_analytics
  GROUP BY customer_id;
```

### Verify DT Refresh

```sql
SHOW DYNAMIC TABLES;

SELECT * FROM regional_revenue WHERE region = 'US-EAST' ORDER BY order_date DESC LIMIT 5;
SELECT * FROM customer_activity ORDER BY lifetime_value DESC LIMIT 10;
```

The Dynamic Tables refresh automatically within 10 minutes of changes appearing in `orders_analytics`. BI dashboards can query these DTs directly with result cache enabled.

<!-- ------------------------ -->
## Step 7: Materialized Views on the Standard Table Copy

For simpler precomputed aggregations that benefit from automatic incremental maintenance:

```sql
CREATE OR REPLACE MATERIALIZED VIEW mv_order_status_summary AS
  SELECT
    status,
    region,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_revenue
  FROM orders_analytics
  GROUP BY status, region;
```

Query the MV:

```sql
SELECT * FROM mv_order_status_summary ORDER BY total_revenue DESC;
```

The Materialized View is refreshed incrementally as `orders_analytics` changes. Queries against the MV use the precomputed result, avoiding a full scan every time.

### When to Use DT vs MV

| Feature | Dynamic Table | Materialized View |
|---------|--------------|------------------|
| Query complexity | Any SQL (joins, subqueries, window functions) | Limited (no joins, no window functions) |
| Refresh model | Full or incremental, TARGET_LAG based | Incremental, automatic |
| Result cache | Yes | Yes |
| Storage cost | Full copy of results | Precomputed aggregation |
| Best for | Complex derived datasets | Simple aggregations on a single table |

<!-- ------------------------ -->
## Step 8: Precomputed Analytics Served from a Hybrid Table

The previous patterns move data from HT to standard tables for analytics. This pattern goes the other direction: precompute analytics on standard tables and store the results in a Hybrid Table for fast point-lookup serving in dashboards.

### Why This Pattern?

Dashboards often display the same KPIs filtered by a single dimension (customer, region, product). If the underlying aggregation is expensive (joining large standard tables, window functions, complex rollups), you do not want the dashboard to recompute it on every page load. By materializing the results into a Hybrid Table, each dashboard filter becomes a single-digit millisecond indexed lookup instead of a multi-second analytical query.

### Create the Dashboard-Serving Hybrid Table

```sql
CREATE OR REPLACE HYBRID TABLE dashboard_customer_kpis (
    customer_id    NUMBER        NOT NULL,
    total_orders   NUMBER        NOT NULL,
    lifetime_value NUMBER(12,2)  NOT NULL,
    avg_order_size NUMBER(12,2)  NOT NULL,
    last_order_at  TIMESTAMP_NTZ,
    pending_count  NUMBER        NOT NULL,
    region         VARCHAR(10)   NOT NULL,
    computed_at    TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (customer_id),
    INDEX idx_dck_region (region)
);
```

### Populate from Analytics Tables

```sql
INSERT INTO dashboard_customer_kpis
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS lifetime_value,
    AVG(total_amount) AS avg_order_size,
    MAX(created_at) AS last_order_at,
    COUNT_IF(status = 'PENDING') AS pending_count,
    (SELECT region FROM orders_analytics WHERE customer_id = oa.customer_id ORDER BY created_at DESC LIMIT 1) AS region,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS computed_at
FROM orders_analytics oa
GROUP BY customer_id;
```

### Refresh Task

```sql
CREATE OR REPLACE TASK refresh_dashboard_kpis
  WAREHOUSE = HT_ARCH_QS_WH
  SCHEDULE = '15 MINUTES'
AS
BEGIN
  TRUNCATE TABLE dashboard_customer_kpis;
  INSERT INTO dashboard_customer_kpis
  SELECT
    customer_id,
    COUNT(*),
    SUM(total_amount),
    AVG(total_amount),
    MAX(created_at),
    COUNT_IF(status = 'PENDING'),
    (SELECT region FROM orders_analytics WHERE customer_id = oa.customer_id ORDER BY created_at DESC LIMIT 1),
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
  FROM orders_analytics oa
  GROUP BY customer_id;
END;
```

### Dashboard Query (Single-Digit ms)

```sql
SET DASHBOARD_CUSTOMER = (SELECT customer_id FROM dashboard_customer_kpis LIMIT 1);

SELECT * FROM dashboard_customer_kpis WHERE customer_id = $DASHBOARD_CUSTOMER;
```

The Query Profile shows `TableScan` with `ROW_BASED` mode and 1 row scanned — a primary key lookup. The dashboard gets instant results regardless of how complex the underlying aggregation is.

### Query by Region (Index Seek)

```sql
SELECT customer_id, lifetime_value, total_orders
FROM dashboard_customer_kpis
WHERE region = 'US-EAST'
ORDER BY lifetime_value DESC
LIMIT 20;
```

This uses `IndexScan` on `idx_dck_region` — fast enough for paginated dashboard panels.

### When to Use This Pattern

- Dashboard panels filtered by a single dimension (customer, region, product)
- KPIs that require expensive joins or window functions to compute
- High-concurrency dashboards where hundreds of users hit the same page
- Latency requirement is single-digit ms (result cache on standard tables adds ~50-200ms overhead even on cache hit)

### Architecture Flow

```
[Standard Tables / DW] → [Scheduled Task: aggregation SQL] → [Hybrid Table: KPIs]
                                                                      ↑
                                                              [Dashboard reads here]
```

<!-- ------------------------ -->
## Step 9: Fan-In Aggregation

In production systems, multiple Hybrid Tables often serve different domains (orders, inventory, customers). Analytics often needs to join across these domains.

### Create Additional Hybrid Tables

```sql
CREATE OR REPLACE HYBRID TABLE inventory (
    product_id   NUMBER NOT NULL,
    warehouse_id NUMBER NOT NULL,
    quantity     NUMBER NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    PRIMARY KEY (product_id, warehouse_id)
)
AS SELECT
    MOD(SEQ4(), 1000) + 1,
    MOD(SEQ4() / 1000, 10) + 1,
    UNIFORM(0, 500, RANDOM())::NUMBER,
    DATEADD(SECOND, UNIFORM(0, 86400, RANDOM()), DATEADD(DAY, -1, CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

CREATE OR REPLACE HYBRID TABLE customers (
    customer_id  NUMBER NOT NULL,
    customer_name VARCHAR NOT NULL,
    tier         VARCHAR(20) NOT NULL,
    region       VARCHAR(10) NOT NULL,
    PRIMARY KEY (customer_id)
)
AS SELECT
    SEQ4(),
    'customer_' || SEQ4()::VARCHAR,
    ARRAY_CONSTRUCT('BRONZE','SILVER','GOLD','PLATINUM')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR
FROM TABLE(GENERATOR(ROWCOUNT => 10000));
```

### Fan-In to a Consolidated Analytics Table

```sql
CREATE OR REPLACE TABLE consolidated_analytics AS
SELECT
    o.order_id,
    o.customer_id,
    c.customer_name,
    c.tier AS customer_tier,
    o.status,
    o.region,
    o.created_at,
    o.total_amount
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id;
```

### Fan-In Refresh Task

```sql
CREATE OR REPLACE TASK refresh_consolidated_analytics
  WAREHOUSE = HT_ARCH_QS_WH
  SCHEDULE = '15 MINUTES'
AS
  CREATE OR REPLACE TABLE consolidated_analytics AS
  SELECT
    o.order_id,
    o.customer_id,
    c.customer_name,
    c.tier AS customer_tier,
    o.status,
    o.region,
    o.created_at,
    o.total_amount
  FROM orders o
  LEFT JOIN customers c ON o.customer_id = c.customer_id;
```

This provides a denormalized, analytics-ready table that joins data from multiple Hybrid Tables. The CTAS-based refresh is appropriate when the full dataset is small enough to rebuild (under a few million rows). For larger datasets, use the MERGE pattern from Step 2 on each source table.

<!-- ------------------------ -->
## Step 10: Hot/Cold Data Tiering

Hybrid Tables are optimized for recent, actively-queried data. Historical data that is rarely accessed should be moved to standard tables where it benefits from columnar compression and lower storage costs.

### Create the Archive Table

```sql
CREATE OR REPLACE TABLE orders_archive (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL,
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2)  NOT NULL,
    archived_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

### Age-Off Task

```sql
CREATE OR REPLACE TASK archive_old_orders
  WAREHOUSE = HT_ARCH_QS_WH
  SCHEDULE = 'USING CRON 0 2 * * * UTC'
AS
BEGIN
  INSERT INTO orders_archive (order_id, customer_id, status, region, created_at, updated_at, total_amount)
    SELECT order_id, customer_id, status, region, created_at, updated_at, total_amount
    FROM orders
    WHERE created_at < DATEADD(DAY, -90, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;

  DELETE FROM orders
    WHERE created_at < DATEADD(DAY, -90, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;
END;
```

### Query Across Hot and Cold

When you need the full history, UNION the two tables:

```sql
CREATE OR REPLACE VIEW orders_all AS
  SELECT order_id, customer_id, status, region, created_at, updated_at, total_amount FROM orders
  UNION ALL
  SELECT order_id, customer_id, status, region, created_at, updated_at, total_amount FROM orders_archive;
```

### Sizing Considerations

- **Hybrid Table storage quota:** 2 TB per database. Tiering prevents hitting this limit.
- **DELETE reclamation:** Space freed by DELETEs is reclaimed by background compaction over hours, not instantly.
- **Archive query performance:** Standard tables with clustering on `created_at` provide excellent range-scan performance for historical queries.

<!-- ------------------------ -->
## Step 11: Alert-Based Monitoring

Hybrid Table queries that complete in under 1 second do not appear in `QUERY_HISTORY`. Use `AGGREGATE_QUERY_HISTORY` for monitoring, and Snowflake Alerts for automated notifications.

### Query AGGREGATE_QUERY_HISTORY

```sql
-- Top queries by execution count (last 24 hours)
SELECT
    query_parameterized_hash,
    ANY_VALUE(query_text) AS sample_query,
    SUM(calls) AS total_executions,
    AVG(total_elapsed_time:"avg"::FLOAT) AS avg_latency_ms,
    MAX(total_elapsed_time:"p99"::FLOAT) AS p99_latency_ms
FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
WHERE interval_start_time > DATEADD(DAY, -1, CURRENT_TIMESTAMP())
  AND warehouse_name = 'HT_ARCH_QS_WH'
GROUP BY query_parameterized_hash
ORDER BY total_executions DESC
LIMIT 10;
```

### Monitor Throttling

```sql
-- Check for HT request throttling (last hour)
SELECT
    interval_start_time,
    SUM(calls) AS total_calls,
    SUM(hybrid_table_requests_throttled_count) AS throttled_requests
FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
WHERE interval_start_time > DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
  AND hybrid_table_requests_throttled_count > 0
GROUP BY interval_start_time
ORDER BY interval_start_time DESC;
```

### Create a Throttling Alert

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ALERT ht_throttle_alert
  WAREHOUSE = HT_ARCH_QS_WH
  SCHEDULE = '5 MINUTE'
  IF( EXISTS(
    SELECT 1 FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE hybrid_table_requests_throttled_count > 50
      AND interval_start_time > DATEADD(MINUTE, -10, CURRENT_TIMESTAMP())
  ))
  THEN
    BEGIN
      -- Replace with your notification integration or email
      -- CALL SYSTEM$SEND_EMAIL('my_email_integration', 'ops@company.com',
      --   'HT Throttling Alert', 'More than 50 throttled requests in the last 10 minutes.');
      INSERT INTO HT_ARCH_QS_DB.DATA.alert_log VALUES (CURRENT_TIMESTAMP(), 'THROTTLE', 'More than 50 throttled requests detected');
    END;

ALTER ALERT ht_throttle_alert RESUME;

USE ROLE HT_ARCH_QS_ROLE;
```

### Create Alert Log Table

```sql
CREATE OR REPLACE TABLE alert_log (
    alert_ts    TIMESTAMP_NTZ,
    alert_type  VARCHAR,
    message     VARCHAR
);
```

> **Note:** AGGREGATE_QUERY_HISTORY has up to 3 hours of latency. For real-time throttling detection, monitor the `Hybrid Table Requests Throttling` percentage in the Query Profile of individual queries.

<!-- ------------------------ -->
## Decision Matrix

| Need | Pattern | Freshness | Complexity |
|------|---------|-----------|------------|
| BI dashboards on HT data | Task + MERGE to ST (Step 2) | Minutes | Low |
| High-freq ingest with real-time rollup | HT ingest buffer + 30s Task + Data Share (Step 3) | 30 seconds | Medium |
| Incremental change detection | Watermark polling (Step 4) | Minutes | Medium |
| Real-time event delivery | Task + Notification Integration (Step 5) | ~1 minute | Medium |
| Derived aggregations | DT on ST copy (Step 6) | TARGET_LAG | Low |
| Simple precomputed rollups | MV on ST copy (Step 7) | Automatic | Low |
| Fast dashboard point lookups | Precompute to HT (Step 8) | Minutes | Medium |
| Cross-domain analytics | Fan-in to consolidated ST (Step 9) | Minutes | Medium |
| Manage HT storage growth | Hot/cold tiering (Step 10) | Daily | Low |
| Operational monitoring | AGGREGATE_QUERY_HISTORY + Alerts (Step 11) | Hours (view latency) | Medium |

### Reference Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │           APPLICATION LAYER                  │
                    │   (writes + point reads via bound variables) │
                    └──────────────────┬──────────────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │            HYBRID TABLE (orders)             │
                    │   PK + secondary indexes, ROW_BASED access  │
                    └──────┬────────────┬────────────┬────────────┘
                           │            │            │
              Task (MERGE) │   Task (notify)  Task (archive)
                           │            │            │
                           ▼            ▼            ▼
              ┌────────────────┐  ┌──────────┐  ┌────────────────┐
              │ orders_analytics│  │ SNS/Kafka│  │ orders_archive │
              │ (standard table)│  │ consumers│  │ (standard table)│
              └───────┬────────┘  └──────────┘  └────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
  ┌──────────┐  ┌──────────┐  ┌──────────────────┐
  │Dynamic   │  │Materialized│ │Task (aggregate)  │
  │Tables    │  │Views      │  │      │           │
  └──────────┘  └──────────┘  │      ▼           │
                               │ ┌──────────────┐ │
                               │ │ HT (KPIs)    │ │
                               │ │ (dashboard   │ │
                               │ │  serving)    │ │
                               │ └──────────────┘ │
                               └──────────────────┘
```

<!-- ------------------------ -->
## Cleanup

Suspend tasks and remove all objects:

```sql
ALTER TASK IF EXISTS snapshot_orders_to_analytics SUSPEND;
ALTER TASK IF EXISTS refresh_consolidated_analytics SUSPEND;
ALTER TASK IF EXISTS archive_old_orders SUSPEND;

USE ROLE ACCOUNTADMIN;
ALTER ALERT IF EXISTS ht_throttle_alert SUSPEND;
DROP ALERT IF EXISTS ht_throttle_alert;
DROP DATABASE IF EXISTS HT_ARCH_QS_DB;
DROP WAREHOUSE IF EXISTS HT_ARCH_QS_WH;
DROP ROLE IF EXISTS HT_ARCH_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You have completed the Hybrid Tables Architectural Patterns quickstart. You can now:

- Avoid the analytics anti-pattern (running GROUP BY directly on Hybrid Tables)
- Build Task-based MERGE pipelines to keep standard table copies in sync
- Detect changes without Streams using timestamp watermarks
- Publish events to external systems via Notification Integrations
- Layer Dynamic Tables and Materialized Views on standard table copies
- Consolidate multiple Hybrid Tables into a single analytics surface
- Tier hot/cold data to manage storage growth
- Monitor HT workloads with AGGREGATE_QUERY_HISTORY and Alerts

### Related Resources

- [Hybrid Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-hybrid)
- [Hybrid Table Limitations](https://docs.snowflake.com/en/user-guide/tables-hybrid-limitations)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Tasks Documentation](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [AGGREGATE_QUERY_HISTORY View](https://docs.snowflake.com/en/sql-reference/account-usage/aggregate_query_history)
- [Snowflake Alerts](https://docs.snowflake.com/en/user-guide/alerts)
- [Notification Integrations](https://docs.snowflake.com/en/sql-reference/sql/create-notification-integration)
- [Converting Standard Tables to Hybrid Tables Quickstart](https://www.snowflake.com/en/developers/guides/hybrid-tables-standard-to-hybrid-migration/)
- [Secondary Index Design for Hybrid Tables Quickstart](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)
- [Connecting Applications to Hybrid Tables Quickstart](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)

<!-- ------------------------ -->
## FAQ and Troubleshooting

**Q: How fresh is the data in the standard table copy?**

Freshness equals your Task schedule interval. A 5-minute Task means data is at most 5 minutes stale. For tighter SLAs, reduce the interval (minimum is 1 minute for scheduled Tasks, or 30 seconds using serverless Tasks).

**Q: Will the MERGE Task cause a full scan of the Hybrid Table every time?**

Yes, unless you use the watermark pattern (Step 3). The full MERGE reads the HT via COLUMN_BASED scan. For tables under 1 million rows on an XSMALL warehouse, this typically completes in under 30 seconds. For larger tables, the watermark-filtered approach limits the scan to recently modified rows.

**Q: Can I use Snowpipe Streaming to write to a Hybrid Table?**

No. Snowpipe Streaming is not supported on Hybrid Tables. Use direct INSERT from your application, or COPY INTO for batch loads.

**Q: What happens if my Task fails mid-MERGE?**

MERGE is atomic. If the Task fails, no partial changes are applied to the standard table. The next Task execution will pick up all pending changes.

**Q: How do I monitor Task execution?**

```sql
SELECT name, state, completed_time, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE name = 'SNAPSHOT_ORDERS_TO_ANALYTICS'
ORDER BY completed_time DESC
LIMIT 10;
```

**Q: Can I use this pattern with multiple Hybrid Tables writing to the same analytics table?**

Yes. This is the fan-in pattern (Step 7). Create separate Tasks for each HT source, or a single Task that joins across all sources.

**Q: What is the storage overhead of maintaining both HT and ST copies?**

The standard table copy uses columnar compression (typically 3-5x compression). For 500K orders, expect roughly 5-15 MB in the standard table vs the row-store footprint in the HT. The tradeoff is storage cost vs analytics performance.

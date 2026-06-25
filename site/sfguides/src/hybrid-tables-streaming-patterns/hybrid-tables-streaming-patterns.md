author: Adam Timm
id: hybrid-tables-streaming-patterns
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn streaming and change detection patterns for Hybrid Tables — real-time ingest with deduplication, watermark-based CDC without Streams, outbound event notifications, and sharded multi-database architectures with Interactive Analytics.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, streaming, Kafka, ingest buffer, change detection, CDC, watermark, notification, SNS, webhook, Unistore, INSERT OVERWRITE, TRANSIENT, Data Share, serverless task, 30 seconds, Interactive Analytics, Interactive Table, Interactive Warehouse, sharded buffer, multi-database, per-database quota
related_concepts: Streams limitation, exactly-once delivery, watermark, checkpoint, NOTIFICATION INTEGRATION, SYSTEM$SEND_SNOWFLAKE_NOTIFICATION, INSERT OVERWRITE, TRANSIENT table, Interactive Table, TARGET_LAG, per-database ops quota
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-standard-to-hybrid-migration
skill_level: intermediate
estimated_time_minutes: 55
snowflake_features: hybrid_tables, tasks, notification_integrations, data_sharing, interactive_tables, interactive_warehouses
-->

# Streaming and Change Detection Patterns for Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** The SQL in this quickstart uses string literals for clarity. Production OLTP workloads should use bound variables (parameterized queries). See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices).

Hybrid Tables do not support Streams. If your workload needs change tracking, incremental processing, or real-time event delivery, you need alternative patterns. This guide covers four:

1. **HT as Ingest Buffer** — use the HT's PRIMARY KEY for exactly-once deduplication on high-frequency streaming ingest, then flush to a columnar standard table for aggregation and delivery
2. **Watermark-Based Change Detection** — detect changed rows without Streams using an `updated_at` timestamp watermark
3. **Outbound Event Notifications** — publish events from Hybrid Table data to external systems (SNS, webhooks)
4. **Sharded Buffer + Interactive Analytics** — split writes across multiple databases to exceed the 16K ops/sec per-database quota, then serve via Interactive Tables for sub-100ms analytical queries

### Patterns in This Guide

| Pattern | Freshness | Best For |
|---------|-----------|----------|
| HT Ingest Buffer + Real-Time Rollup | 30 seconds | Kafka/IoT/financial streaming where exactly-once and fresh aggregations matter |
| Watermark CDC | Minutes | Incremental MERGE for downstream consumers |
| Outbound Event Notifications | ~1 minute | Kafka consumers, microservices, alerting |
| Sharded Buffer + Interactive Analytics | 30s write → 60s IA | High-throughput streaming (>16K ops/sec) with sub-100ms analytical serving |

### Other Guides in This Series

- **[Analytics Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)** — Task snapshot, Dynamic Tables, MVs, Precomputed KPI serving
- **[Data Management and Operations](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)** — Fan-in aggregation, hot/cold tiering, monitoring

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Familiarity with Snowflake Tasks and Snowflake Scripting

<!-- ------------------------ -->
## Setup

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_STREAMING_QS_ROLE;
GRANT ROLE HT_STREAMING_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_STREAMING_QS_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_STREAMING_QS_WH TO ROLE HT_STREAMING_QS_ROLE;

CREATE OR REPLACE DATABASE HT_STREAMING_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_STREAMING_QS_DB TO ROLE HT_STREAMING_QS_ROLE;

USE ROLE HT_STREAMING_QS_ROLE;
CREATE OR REPLACE SCHEMA HT_STREAMING_QS_DB.DATA;
USE WAREHOUSE HT_STREAMING_QS_WH;
USE DATABASE HT_STREAMING_QS_DB;
USE SCHEMA DATA;
```

<!-- ------------------------ -->
## Step 1: HT as Ingest Buffer with Real-Time Rollup and Data Share Delivery

This pattern addresses high-frequency streaming workloads (Kafka, IoT, financial tick data) where you need:
- **Exactly-once delivery** — duplicate messages from the producer are silently rejected
- **Fresh aggregated view** — a rollup that updates every 30 seconds
- **Simple consumer delivery** — live SQL via Data Share instead of CSV file export

The key insight: the Hybrid Table is NOT the permanent store. Its PRIMARY KEY enforces deduplication on ingest. A 30-second serverless Task flushes new rows to a clustered standard table, computes the rollup there (columnar GROUP BY is 50-100x faster than KV storage), and the HT is intentionally kept to a short rolling window.

### Why This Matters for Performance

A naive approach runs the cumulative aggregation directly on the Hybrid Table. As rows accumulate through the session, the GROUP BY must scan an ever-growing dataset through the row store. At 500K rows the scan may take 17 seconds; at 2.35M rows (mid-session) it can take 35 seconds — far past any reasonable SLA. Moving the aggregation to columnar storage reduces this to ~136ms at 500K rows.

### Create the Tables

```sql
-- HT: ingest buffer and dedup gate (PK = exactly-once)
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

-- Standard table: permanent columnar record, clustered for range scans
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

-- Rollup table: TRANSIENT + 0-day retention = zero storage churn
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

-- Checkpoint: tracks the last-flushed timestamp per day
CREATE OR REPLACE TABLE events_checkpoint (
    window_date    DATE          NOT NULL,
    last_flush_ts  TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (window_date)
);

INSERT INTO events_checkpoint VALUES (CURRENT_DATE(), '1970-01-01'::TIMESTAMP_NTZ);
```

### Load Sample Data

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

  -- Delta flush: only new rows since last checkpoint (index seek via idx_events_source_ts)
  INSERT INTO raw_events_st (event_id, source_id, event_type, region, value, event_ts)
  SELECT event_id, source_id, event_type, region, value, event_ts
  FROM events_ht
  WHERE event_ts > :v_checkpoint
    AND event_ts <= :v_now;

  -- Cumulative rollup on columnar ST (~100ms at 500K rows)
  -- INSERT OVERWRITE atomically replaces rows — no DELETE+INSERT micro-partition churn
  INSERT OVERWRITE INTO events_rollup
  SELECT
    event_type,
    region,
    COUNT(*)     AS event_count,
    SUM(value)   AS total_value,
    MIN(value)   AS min_value,
    MAX(value)   AS max_value,
    MIN(event_ts) AS window_start,
    :v_now        AS last_updated
  FROM raw_events_st
  WHERE event_ts::DATE = :v_today
  GROUP BY event_type, region;

  -- Advance checkpoint
  MERGE INTO events_checkpoint AS tgt
  USING (SELECT :v_today AS window_date, :v_now AS last_flush_ts) AS src
  ON tgt.window_date = src.window_date
  WHEN MATCHED THEN UPDATE SET tgt.last_flush_ts = src.last_flush_ts
  WHEN NOT MATCHED THEN INSERT (window_date, last_flush_ts) VALUES (src.window_date, src.last_flush_ts);
END;

ALTER TASK events_pipeline_30s RESUME;
```

> **Why `INSERT OVERWRITE` + `TRANSIENT` table?** Refreshing a rollup table 2,880 times per day (30s intervals) with `DELETE + INSERT` accumulates deleted micro-partitions in Time Travel storage. `INSERT OVERWRITE` atomically replaces data without creating Time Travel overhead. `DATA_RETENTION_TIME_IN_DAYS = 0` on a TRANSIENT table eliminates Fail-safe storage entirely — the rollup is always recomputable from `raw_events_st`.

### Verify and Pause

```sql
SELECT COUNT(*) FROM raw_events_st;
SELECT * FROM events_rollup ORDER BY total_value DESC;
SELECT * FROM events_checkpoint;

ALTER TASK events_pipeline_30s SUSPEND;
```

### Keep the HT Buffer Small (Purge Task)

Once `raw_events_st` is the permanent record, purge old HT rows hourly. A small HT means fast ingest, fast dedup, and fast platform maintenance:

```sql
CREATE OR REPLACE TASK purge_ht_buffer
  SCHEDULE = 'USING CRON 0 * * * * UTC'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
  DELETE FROM events_ht
  WHERE event_ts < DATEADD(HOUR, -4, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;
```

### Deliver via Data Share

Replace file-based export with a live SQL share — no CSV, no polling, always current:

```sql
-- Run as ACCOUNTADMIN
CREATE SHARE events_data_share;
GRANT USAGE ON DATABASE HT_STREAMING_QS_DB TO SHARE events_data_share;
GRANT USAGE ON SCHEMA HT_STREAMING_QS_DB.DATA TO SHARE events_data_share;
GRANT SELECT ON TABLE HT_STREAMING_QS_DB.DATA.events_rollup TO SHARE events_data_share;
-- ALTER SHARE events_data_share ADD ACCOUNTS = <consumer_account>;
```

> For the application-side Kafka ingest pattern (Spring Boot + JDBC batch inserts into HT), see the [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/) quickstart.

### Optional: Add Interactive Analytics for Sub-100ms Analytical Serving

If your consumers need sub-100ms analytical queries (GROUP BY, aggregations, time-range scans) at high concurrency — such as real-time dashboards, data APIs, or agentic AI workloads — add an **Interactive Analytics** layer on top of `raw_events_st`.

Interactive Tables are Dynamic Tables optimized for low-latency serving. They auto-refresh from your Standard Table and are queried through a specialized Interactive Warehouse with pre-warmed caches.

```sql
-- Create an Interactive Warehouse (specialized for low-latency, high-concurrency)
CREATE OR REPLACE INTERACTIVE WAREHOUSE events_ia_wh;

-- Create an Interactive Table sourcing from the standard table
-- TARGET_LAG = '1 minute' (minimum is 60 seconds)
CREATE OR REPLACE INTERACTIVE TABLE events_rollup_it
  CLUSTER BY (event_type, region)
  TARGET_LAG = '1 minute'
  WAREHOUSE = HT_STREAMING_QS_WH
AS
SELECT
    event_type,
    region,
    COUNT(*)     AS event_count,
    SUM(value)   AS total_value,
    MIN(value)   AS min_value,
    MAX(value)   AS max_value,
    MIN(event_ts) AS window_start,
    MAX(event_ts) AS window_end
FROM raw_events_st
WHERE event_ts::DATE = CURRENT_DATE()
GROUP BY event_type, region;

-- Add the Interactive Table to the Interactive Warehouse (warms the cache)
ALTER WAREHOUSE events_ia_wh ADD TABLES (events_rollup_it);

-- Query through the Interactive Warehouse for sub-100ms latency
USE WAREHOUSE events_ia_wh;
SELECT * FROM events_rollup_it WHERE event_type = 'PURCHASE' ORDER BY total_value DESC;
```

> **Key constraints:**
> - Interactive Tables cannot source from Hybrid Tables — they must source from Standard Tables (which is why the HT → ST flush step is essential)
> - `TARGET_LAG` minimum is 60 seconds
> - Interactive Warehouses can **only** query Interactive Tables — you cannot mix table types in a single query
> - The Interactive Warehouse is always-on with pre-warmed caches; size it based on concurrency requirements

This gives you three query paths in the final architecture:

| Path | Target | Latency | Use Case |
|------|--------|---------|----------|
| HT point lookup | `events_ht` | Sub-50ms | Get specific event by PK |
| Interactive Analytics | `events_rollup_it` via IA Warehouse | Sub-100ms | Dashboards, APIs, aggregations |
| Standard Warehouse | `raw_events_st` | 200ms–seconds | Ad-hoc analytics, heavy scans |

<!-- ------------------------ -->
## Step 2: Change Detection Without Streams

Streams are not supported on Hybrid Tables. The timestamp watermark pattern detects changed rows using an `updated_at` column.

### Create the Orders Table and Mirror

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
    INDEX idx_orders_customer_id (customer_id)
)
AS SELECT
    SEQ4(),
    UNIFORM(1, 10000, RANDOM())::NUMBER,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    DATEADD(SECOND, UNIFORM(0,7776000,RANDOM()), DATEADD(DAY,-90,CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ,
    NULL::TIMESTAMP_NTZ,
    ROUND(UNIFORM(5.00,2500.00,RANDOM()),2)
FROM TABLE(GENERATOR(ROWCOUNT => 500000));

CREATE OR REPLACE TABLE orders_mirror (
    order_id     NUMBER NOT NULL,
    customer_id  NUMBER NOT NULL,
    status       VARCHAR(20) NOT NULL,
    region       VARCHAR(10) NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2) NOT NULL,
    snapshot_ts  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO orders_mirror (order_id, customer_id, status, region, created_at, updated_at, total_amount)
SELECT order_id, customer_id, status, region, created_at, updated_at, total_amount
FROM orders;

CREATE OR REPLACE TABLE sync_watermarks (
    table_name   VARCHAR NOT NULL,
    last_sync_ts TIMESTAMP_NTZ NOT NULL
);
INSERT INTO sync_watermarks VALUES ('orders', '2000-01-01'::TIMESTAMP_NTZ);
```

### Simulate Updates

```sql
UPDATE orders
SET status = 'SHIPPED', updated_at = CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
WHERE order_id IN (SELECT order_id FROM orders WHERE status = 'PENDING' LIMIT 100);
```

### Incremental MERGE with Watermark

```sql
SET last_watermark  = (SELECT last_sync_ts FROM sync_watermarks WHERE table_name = 'orders');
SET current_watermark = CURRENT_TIMESTAMP()::TIMESTAMP_NTZ;

MERGE INTO orders_mirror AS tgt
USING (
    SELECT * FROM orders
    WHERE updated_at > $last_watermark
       OR created_at > $last_watermark
) AS src
ON tgt.order_id = src.order_id
WHEN MATCHED
  THEN UPDATE SET
    tgt.status       = src.status,
    tgt.updated_at   = src.updated_at,
    tgt.total_amount = src.total_amount,
    tgt.snapshot_ts  = $current_watermark
WHEN NOT MATCHED
  THEN INSERT (order_id, customer_id, status, region, created_at, updated_at, total_amount, snapshot_ts)
  VALUES (src.order_id, src.customer_id, src.status, src.region, src.created_at, src.updated_at, src.total_amount, $current_watermark);

UPDATE sync_watermarks SET last_sync_ts = $current_watermark WHERE table_name = 'orders';
```

### Requirements for This Pattern

- The HT must have an `updated_at` column that your application sets on every UPDATE
- Without `updated_at`, run a full MERGE periodically as a safety net
- A secondary index on `updated_at` is not required but helps limit the scan scope

<!-- ------------------------ -->
## Step 3: Outbound Event Notifications

For systems that need near-real-time event delivery from HT changes — Kafka consumers, microservices, alerting — Snowflake can publish notifications to cloud queues and webhooks via Notification Integrations.

> **Note:** This covers *outbound* delivery from Snowflake to external systems. For *inbound* Kafka ingest into HT, see Step 1 of this guide and the [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/) quickstart.

### Create a Notification Integration (AWS SNS)

```sql
-- Run as ACCOUNTADMIN; replace ARNs with your actual values
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NOTIFICATION INTEGRATION orders_sns_integration
  TYPE = QUEUE
  NOTIFICATION_PROVIDER = AWS_SNS
  DIRECTION = OUTBOUND
  AWS_SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:123456789012:order-events'
  AWS_SNS_ROLE_ARN  = 'arn:aws:iam::123456789012:role/snowflake-sns-role';

GRANT USAGE ON INTEGRATION orders_sns_integration TO ROLE HT_STREAMING_QS_ROLE;
USE ROLE HT_STREAMING_QS_ROLE;
```

### Task-Based Event Publisher

```sql
CREATE OR REPLACE TASK publish_order_events
  WAREHOUSE = HT_STREAMING_QS_WH
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

> **Note:** This pattern provides ~1-minute event granularity. For true sub-second event streaming, publish events directly from the application layer (before or in addition to the HT write) rather than polling Snowflake.

### Webhook Alternative (Slack / Teams)

```sql
-- CREATE NOTIFICATION INTEGRATION orders_webhook
--   TYPE = WEBHOOK
--   WEBHOOK_URL = 'https://hooks.slack.com/services/...'
--   WEBHOOK_BODY_TEMPLATE = '{"text": "SNOWFLAKE_WEBHOOK_MESSAGE"}'
--   WEBHOOK_HEADERS = ('Content-Type'='application/json');
```

<!-- ------------------------ -->
## Step 4: Sharded Ingest Buffer with Interactive Analytics Serving

This pattern extends Step 1 to handle workloads that exceed the **16,000 ops/sec per-database Hybrid Table quota** — such as high-frequency financial event streaming (25K+ events/sec). The key insight: split the write path across multiple databases (each with its own quota), use a serverless Task to consolidate into a serving layer, and optionally accelerate analytical reads with Interactive Analytics.

### When You Need This Pattern

- Write throughput exceeds 16,000 ops/sec (the per-database HT hard ceiling)
- You need exactly-once deduplication AND fast analytical queries on the same data
- Multiple event types or partitions can be routed independently
- The serving layer must support both sub-50ms point lookups AND sub-100ms analytical queries

### Architecture Overview

```
Kafka / Event Source (25K+ events/sec)
  ↓ Application Router (route by event_type or partition key)
  ↓              ↓              ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Buffer   │ │ Buffer   │ │ Buffer   │  ← 3 HT databases (DATA_RETENTION=0)
│ DB 1     │ │ DB 2     │ │ DB 3     │    16K ops/sec quota each = 48K combined
└────┬─────┘ └────┬─────┘ └────┬─────┘
     └─────────────┼─────────────┘
                   ↓
         30s Serverless Task (cross-database read)
                 ↙    ↘
┌────────────────┐  ┌────────────────────┐
│ Serving HT     │  │ History ST         │  ← Durable serving + columnar archive
│ (current state)│  │ (18-month history) │
└────────────────┘  └────────┬───────────┘
                             ↓
                   ┌────────────────────┐
                   │ Interactive Tables  │  ← Auto-refresh (1 min TARGET_LAG)
                   │ + IA Warehouse     │     Sub-100ms analytical serving
                   └────────────────────┘
```

### Create the Sharded Buffer Databases

Each database gets its own 16,000 ops/sec HT quota. The HT PRIMARY KEY enforces exactly-once deduplication within each buffer.

```sql
USE ROLE ACCOUNTADMIN;

-- Three independent databases — each with its own ops/sec quota
CREATE OR REPLACE DATABASE events_buffer_db_1
  COMMENT = 'Ingest buffer: event_type_a (16K ops/sec quota)';
CREATE OR REPLACE DATABASE events_buffer_db_2
  COMMENT = 'Ingest buffer: event_type_b (16K ops/sec quota)';
CREATE OR REPLACE DATABASE events_buffer_db_3
  COMMENT = 'Ingest buffer: event_type_c (16K ops/sec quota)';

-- Serving database: consolidated current state + history
CREATE OR REPLACE DATABASE events_serving_db
  COMMENT = 'Serving layer: current state (HT) + full history (ST) + Interactive Tables';

-- Schemas
CREATE SCHEMA events_buffer_db_1.ingest;
CREATE SCHEMA events_buffer_db_2.ingest;
CREATE SCHEMA events_buffer_db_3.ingest;
CREATE SCHEMA events_serving_db.serving;
```

### Create Buffer Hybrid Tables

Each buffer HT uses `DATA_RETENTION_TIME_IN_DAYS = 0` — these are ephemeral buffers, not permanent stores. The PK provides exactly-once deduplication.

```sql
-- Repeat for each buffer database (shown for DB 1)
CREATE OR REPLACE HYBRID TABLE events_buffer_db_1.ingest.events_buffer (
    event_id        VARCHAR(100)  NOT NULL,
    partition_key   VARCHAR(50)   NOT NULL,
    entity_id       VARCHAR(50)   NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    event_ts        TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    payload         VARIANT       NOT NULL,
    PRIMARY KEY (event_id)
)
DATA_RETENTION_TIME_IN_DAYS = 0;

-- Buffer DB 2
CREATE OR REPLACE HYBRID TABLE events_buffer_db_2.ingest.events_buffer (
    event_id        VARCHAR(100)  NOT NULL,
    partition_key   VARCHAR(50)   NOT NULL,
    entity_id       VARCHAR(50)   NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    event_ts        TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    payload         VARIANT       NOT NULL,
    PRIMARY KEY (event_id)
)
DATA_RETENTION_TIME_IN_DAYS = 0;

-- Buffer DB 3
CREATE OR REPLACE HYBRID TABLE events_buffer_db_3.ingest.events_buffer (
    event_id        VARCHAR(100)  NOT NULL,
    partition_key   VARCHAR(50)   NOT NULL,
    entity_id       VARCHAR(50)   NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    event_ts        TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    payload         VARIANT       NOT NULL,
    PRIMARY KEY (event_id)
)
DATA_RETENTION_TIME_IN_DAYS = 0;
```

### Create the Serving Layer

The serving layer has two tables:
- **Current State HT** — one row per entity (INSERT OVERWRITE every 30s). Durable, supports sub-50ms point lookups.
- **History ST** — append-only columnar record. Clustered for time-range analytics.

```sql
-- Current state: one row per entity per event_type (point-lookup serving)
CREATE OR REPLACE HYBRID TABLE events_serving_db.serving.events_latest (
    partition_key   VARCHAR(50)   NOT NULL,
    entity_id       VARCHAR(50)   NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    event_id        VARCHAR(100)  NOT NULL,
    event_ts        TIMESTAMP_NTZ NOT NULL,
    payload         VARIANT       NOT NULL,
    updated_at      TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (partition_key, entity_id, event_type)
);

-- Full history: columnar, clustered, analytics-ready
CREATE OR REPLACE TABLE events_serving_db.serving.events_history (
    event_id        VARCHAR(100)  NOT NULL,
    partition_key   VARCHAR(50)   NOT NULL,
    entity_id       VARCHAR(50)   NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    event_ts        TIMESTAMP_NTZ NOT NULL,
    payload         VARIANT       NOT NULL,
    ingested_at     TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (DATE_TRUNC('day', event_ts), event_type);

-- Watermark checkpoint (one row per buffer database)
CREATE OR REPLACE TABLE events_serving_db.serving.pipeline_checkpoint (
    source_db       VARCHAR(100)  NOT NULL,
    last_event_ts   TIMESTAMP_NTZ NOT NULL DEFAULT '1970-01-01'::TIMESTAMP_NTZ,
    updated_at      TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (source_db)
);

INSERT INTO events_serving_db.serving.pipeline_checkpoint (source_db)
VALUES ('events_buffer_db_1'), ('events_buffer_db_2'), ('events_buffer_db_3');
```

### Create the 30-Second Consolidation Task

This Task reads the delta from all three buffer databases, appends to history, and performs INSERT OVERWRITE to maintain current state:

```sql
CREATE OR REPLACE TASK events_serving_db.serving.consolidation_30s
  SCHEDULE = '30 SECONDS'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
BEGIN
  LET v_cp1 TIMESTAMP_NTZ := (SELECT last_event_ts FROM events_serving_db.serving.pipeline_checkpoint WHERE source_db = 'events_buffer_db_1');
  LET v_cp2 TIMESTAMP_NTZ := (SELECT last_event_ts FROM events_serving_db.serving.pipeline_checkpoint WHERE source_db = 'events_buffer_db_2');
  LET v_cp3 TIMESTAMP_NTZ := (SELECT last_event_ts FROM events_serving_db.serving.pipeline_checkpoint WHERE source_db = 'events_buffer_db_3');

  -- Append delta to history (all events, append-only)
  INSERT INTO events_serving_db.serving.events_history
    (event_id, partition_key, entity_id, event_type, event_ts, payload)
  SELECT event_id, partition_key, entity_id, event_type, event_ts, payload
  FROM events_buffer_db_1.ingest.events_buffer WHERE event_ts > :v_cp1
  UNION ALL
  SELECT event_id, partition_key, entity_id, event_type, event_ts, payload
  FROM events_buffer_db_2.ingest.events_buffer WHERE event_ts > :v_cp2
  UNION ALL
  SELECT event_id, partition_key, entity_id, event_type, event_ts, payload
  FROM events_buffer_db_3.ingest.events_buffer WHERE event_ts > :v_cp3;

  -- INSERT OVERWRITE: atomically replace current state with latest per entity
  INSERT OVERWRITE INTO events_serving_db.serving.events_latest
    (partition_key, entity_id, event_type, event_id, event_ts, payload, updated_at)
  SELECT partition_key, entity_id, event_type, event_id, event_ts, payload, CURRENT_TIMESTAMP()
  FROM (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY partition_key, entity_id, event_type
      ORDER BY event_ts DESC
    ) AS rn
    FROM (
      SELECT partition_key, entity_id, event_type, event_id, event_ts, payload
      FROM events_serving_db.serving.events_latest
      UNION ALL
      SELECT partition_key, entity_id, event_type, event_id, event_ts, payload
      FROM events_buffer_db_1.ingest.events_buffer WHERE event_ts > :v_cp1
      UNION ALL
      SELECT partition_key, entity_id, event_type, event_id, event_ts, payload
      FROM events_buffer_db_2.ingest.events_buffer WHERE event_ts > :v_cp2
      UNION ALL
      SELECT partition_key, entity_id, event_type, event_id, event_ts, payload
      FROM events_buffer_db_3.ingest.events_buffer WHERE event_ts > :v_cp3
    )
  )
  WHERE rn = 1;

  -- Advance watermarks
  UPDATE events_serving_db.serving.pipeline_checkpoint
  SET last_event_ts = COALESCE((SELECT MAX(event_ts) FROM events_buffer_db_1.ingest.events_buffer), last_event_ts),
      updated_at = CURRENT_TIMESTAMP()
  WHERE source_db = 'events_buffer_db_1';

  UPDATE events_serving_db.serving.pipeline_checkpoint
  SET last_event_ts = COALESCE((SELECT MAX(event_ts) FROM events_buffer_db_2.ingest.events_buffer), last_event_ts),
      updated_at = CURRENT_TIMESTAMP()
  WHERE source_db = 'events_buffer_db_2';

  UPDATE events_serving_db.serving.pipeline_checkpoint
  SET last_event_ts = COALESCE((SELECT MAX(event_ts) FROM events_buffer_db_3.ingest.events_buffer), last_event_ts),
      updated_at = CURRENT_TIMESTAMP()
  WHERE source_db = 'events_buffer_db_3';
END;

ALTER TASK events_serving_db.serving.consolidation_30s RESUME;
```

### Purge Tasks (One Per Buffer Database)

```sql
CREATE OR REPLACE TASK events_buffer_db_1.ingest.purge_buffer
  SCHEDULE = 'USING CRON 0 * * * * UTC'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
  DELETE FROM events_buffer_db_1.ingest.events_buffer
  WHERE event_ts < DATEADD(HOUR, -4, CURRENT_TIMESTAMP());

CREATE OR REPLACE TASK events_buffer_db_2.ingest.purge_buffer
  SCHEDULE = 'USING CRON 0 * * * * UTC'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
  DELETE FROM events_buffer_db_2.ingest.events_buffer
  WHERE event_ts < DATEADD(HOUR, -4, CURRENT_TIMESTAMP());

CREATE OR REPLACE TASK events_buffer_db_3.ingest.purge_buffer
  SCHEDULE = 'USING CRON 0 * * * * UTC'
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
AS
  DELETE FROM events_buffer_db_3.ingest.events_buffer
  WHERE event_ts < DATEADD(HOUR, -4, CURRENT_TIMESTAMP());
```

### Optional: Add Interactive Analytics for Sub-100ms Serving

For workloads requiring sub-100ms analytical queries at high concurrency (dashboards, data APIs, Cortex AI), add Interactive Tables sourced from the history Standard Table:

```sql
-- Interactive Warehouse: specialized for low-latency, high-concurrency queries
CREATE OR REPLACE INTERACTIVE WAREHOUSE events_ia_wh;

-- Interactive Table: auto-refreshed current state (sources from history ST)
CREATE OR REPLACE INTERACTIVE TABLE events_serving_db.serving.events_latest_it
  CLUSTER BY (partition_key, entity_id, event_type)
  TARGET_LAG = '1 minute'
  WAREHOUSE = HT_STREAMING_QS_WH
AS
SELECT partition_key, entity_id, event_type, event_id, event_ts, payload
FROM (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY partition_key, entity_id, event_type
      ORDER BY event_ts DESC
    ) AS rn
    FROM events_serving_db.serving.events_history
)
WHERE rn = 1;

-- Interactive Table: full history for time-range analytics
CREATE OR REPLACE INTERACTIVE TABLE events_serving_db.serving.events_history_it
  CLUSTER BY (event_type, DATE_TRUNC('day', event_ts))
  TARGET_LAG = '1 minute'
  WAREHOUSE = HT_STREAMING_QS_WH
AS
SELECT event_id, partition_key, entity_id, event_type, event_ts, payload, ingested_at
FROM events_serving_db.serving.events_history;

-- Add both to the Interactive Warehouse
ALTER WAREHOUSE events_ia_wh ADD TABLES (
    events_serving_db.serving.events_latest_it,
    events_serving_db.serving.events_history_it
);

-- Query through IA warehouse for sub-100ms analytics
USE WAREHOUSE events_ia_wh;
SELECT event_type, COUNT(*) AS event_count, MAX(event_ts) AS latest
FROM events_serving_db.serving.events_history_it
WHERE event_ts > DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
GROUP BY event_type
ORDER BY event_count DESC;
```

### Three Query Paths in the Final Architecture

| Path | Target | Latency | Use Case |
|------|--------|---------|----------|
| HT point lookup | `events_latest` (Hybrid Table) | Sub-50ms | Get current state for entity X |
| Interactive Analytics | `events_latest_it` / `events_history_it` via IA Warehouse | Sub-100ms | Dashboards, APIs, aggregations |
| Standard Warehouse | `events_history` (Standard Table) | 200ms–seconds | Ad-hoc analytics, heavy full-table scans, Cortex AI |

### Capacity Planning

| Aspect | Formula | Example (25K events/sec) |
|--------|---------|--------------------------|
| Databases needed | `CEIL(target_ops / 16000)` | `CEIL(25000/16000)` = 2 (use 3 for headroom) |
| Connections per DB | `target_ops / (databases × rows_per_sec_per_conn)` | `25000 / (3 × 250)` ≈ 33 |
| Total connections | `connections_per_db × databases` | `33 × 3` = 99 |
| Buffer retention | Based on recovery window + purge frequency | 4 hours |
| Events_latest rows | `unique_entities × event_types` | 50K accounts × 3 types = 150K |
| IA refresh lag | `TARGET_LAG` minimum | 60 seconds |

> **When to use this pattern vs. Snowflake Postgres:** If the total connection requirement (e.g., 100 connections) is operationally challenging, or if you need sub-ms read-after-write latency, consider Snowflake Postgres + Data Mirroring as an alternative write path. It eliminates both the per-database quota ceiling and the connection requirement at ~8 total connections. The serving layer (HT + ST + IA) remains identical.

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your own workload:

> "Build a watermark CDC Task for my Hybrid Table. My schema is: [paste DDL]. The updated_at column is TIMESTAMPTZ. Generate the Task SQL that reads only rows modified since the last run."

> "I need to handle high-concurrency writes to my Hybrid Table from 1000+ parallel workers. Design an ingest buffer pattern using a Standard Table to absorb writes and batch-merge into the HT."

> "Configure outbound event notifications from my Hybrid Table so that when a row matching [condition] is written, a message is sent to an SNS topic. Generate the alert and notification integration SQL."

> "My application writes 25K events/sec across 3 event types. Design a sharded buffer architecture with one HT database per event type, a 30-second consolidation Task, and an Interactive Analytics layer for sub-100ms dashboard queries. Include the capacity planning math."

<!-- ------------------------ -->
## Cleanup

```sql
ALTER TASK IF EXISTS events_pipeline_30s SUSPEND;
ALTER TASK IF EXISTS purge_ht_buffer SUSPEND;
ALTER TASK IF EXISTS publish_order_events SUSPEND;
ALTER TASK IF EXISTS events_serving_db.serving.consolidation_30s SUSPEND;
ALTER TASK IF EXISTS events_buffer_db_1.ingest.purge_buffer SUSPEND;
ALTER TASK IF EXISTS events_buffer_db_2.ingest.purge_buffer SUSPEND;
ALTER TASK IF EXISTS events_buffer_db_3.ingest.purge_buffer SUSPEND;
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_STREAMING_QS_DB;
DROP DATABASE IF EXISTS events_buffer_db_1;
DROP DATABASE IF EXISTS events_buffer_db_2;
DROP DATABASE IF EXISTS events_buffer_db_3;
DROP DATABASE IF EXISTS events_serving_db;
DROP WAREHOUSE IF EXISTS HT_STREAMING_QS_WH;
DROP WAREHOUSE IF EXISTS events_ia_wh;
DROP ROLE IF EXISTS HT_STREAMING_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now:
- Use HT PRIMARY KEY as an exactly-once ingest dedup gate for high-frequency streaming
- Build 30-second serverless Task pipelines with `INSERT OVERWRITE` + TRANSIENT rollup tables
- Detect changes without Streams using timestamp watermarks
- Publish events to external systems via Notification Integrations
- Scale beyond the 16K ops/sec per-database quota using sharded multi-database buffers
- Accelerate analytical queries to sub-100ms using Interactive Tables and Interactive Warehouses

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Data Management and Operations Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)
- [Architectural Patterns Overview and Decision Matrix](https://www.snowflake.com/en/developers/guides/hybrid-tables-architectural-patterns/)
- [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Notification Integrations](https://docs.snowflake.com/en/sql-reference/sql/create-notification-integration)
- [Interactive Tables and Warehouses](https://docs.snowflake.com/en/user-guide/interactive)
- [CREATE INTERACTIVE WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/create-interactive-warehouse)

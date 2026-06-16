author: Adam Timm
id: hybrid-tables-streaming-patterns
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn streaming and change detection patterns for Hybrid Tables — real-time ingest with deduplication, watermark-based CDC without Streams, and outbound event notifications.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, streaming, Kafka, ingest buffer, change detection, CDC, watermark, notification, SNS, webhook, Unistore, INSERT OVERWRITE, TRANSIENT, Data Share, serverless task, 30 seconds
related_concepts: Streams limitation, exactly-once delivery, watermark, checkpoint, NOTIFICATION INTEGRATION, SYSTEM$SEND_SNOWFLAKE_NOTIFICATION, INSERT OVERWRITE, TRANSIENT table
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-standard-to-hybrid-migration
skill_level: intermediate
estimated_time_minutes: 40
snowflake_features: hybrid_tables, tasks, notification_integrations, data_sharing
-->

# Streaming and Change Detection Patterns for Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** The SQL in this quickstart uses string literals for clarity. Production OLTP workloads should use bound variables (parameterized queries). See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices).

Hybrid Tables do not support Streams. If your workload needs change tracking, incremental processing, or real-time event delivery, you need alternative patterns. This guide covers three:

1. **HT as Ingest Buffer** — use the HT's PRIMARY KEY for exactly-once deduplication on high-frequency streaming ingest, then flush to a columnar standard table for aggregation and delivery
2. **Watermark-Based Change Detection** — detect changed rows without Streams using an `updated_at` timestamp watermark
3. **Outbound Event Notifications** — publish events from Hybrid Table data to external systems (SNS, webhooks)

### Patterns in This Guide

| Pattern | Freshness | Best For |
|---------|-----------|----------|
| HT Ingest Buffer + Real-Time Rollup | 30 seconds | Kafka/IoT/financial streaming where exactly-once and fresh aggregations matter |
| Watermark CDC | Minutes | Incremental MERGE for downstream consumers |
| Outbound Event Notifications | ~1 minute | Kafka consumers, microservices, alerting |

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
## Cleanup

```sql
ALTER TASK IF EXISTS events_pipeline_30s SUSPEND;
ALTER TASK IF EXISTS purge_ht_buffer SUSPEND;
ALTER TASK IF EXISTS publish_order_events SUSPEND;
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_STREAMING_QS_DB;
DROP WAREHOUSE IF EXISTS HT_STREAMING_QS_WH;
DROP ROLE IF EXISTS HT_STREAMING_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now:
- Use HT PRIMARY KEY as an exactly-once ingest dedup gate for high-frequency streaming
- Build 30-second serverless Task pipelines with `INSERT OVERWRITE` + TRANSIENT rollup tables
- Detect changes without Streams using timestamp watermarks
- Publish events to external systems via Notification Integrations

### Related Resources

- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Data Management and Operations Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)
- [Architectural Patterns Overview and Decision Matrix](https://www.snowflake.com/en/developers/guides/hybrid-tables-architectural-patterns/)
- [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Notification Integrations](https://docs.snowflake.com/en/sql-reference/sql/create-notification-integration)

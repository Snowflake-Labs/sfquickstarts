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
    INDEX idx_orders_customer (customer_id)
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
    PRIMARY KEY (customer_id)
)
AS SELECT SEQ4(), 'customer_' || SEQ4()::VARCHAR,
    ARRAY_CONSTRUCT('BRONZE','SILVER','GOLD','PLATINUM')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR
FROM TABLE(GENERATOR(ROWCOUNT => 10000));
```

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

Verify:

```sql
SELECT COUNT(*) FROM consolidated_orders; -- Expected: 500000
SELECT customer_tier, COUNT(*), SUM(total_amount) FROM consolidated_orders GROUP BY customer_tier;

ALTER TASK refresh_consolidated_analytics SUSPEND;
```

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

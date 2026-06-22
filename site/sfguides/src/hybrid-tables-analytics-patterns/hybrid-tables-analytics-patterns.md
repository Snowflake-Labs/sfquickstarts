author: Adam Timm
id: hybrid-tables-analytics-patterns
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn how to run analytics on Hybrid Table data using Task-based snapshots, Dynamic Tables, Materialized Views, and precomputed KPI serving patterns.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, analytics, Task, MERGE, snapshot, Dynamic Table, Materialized View, precomputed KPI, result cache, COLUMN_BASED scan, GROUP BY, Unistore, standard table, columnar
related_concepts: result cache limitation, COLUMN_BASED scan, ROW_BASED scan, Task schedule, MERGE, Dynamic Table TARGET_LAG, INSERT OVERWRITE, TRANSIENT table
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-standard-to-hybrid-migration
skill_level: intermediate
estimated_time_minutes: 40
snowflake_features: hybrid_tables, tasks, merge, dynamic_tables, materialized_views
-->

# Analytics Patterns for Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** The SQL in this quickstart uses string literals for clarity. Production OLTP workloads should use bound variables (parameterized queries). See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices).

Hybrid Tables are optimized for low-latency point lookups and transactional writes — not analytical aggregations. Running GROUP BY, window functions, or full-table scans directly on a Hybrid Table produces a `COLUMN_BASED` scan with no result cache and no partition pruning. For BI dashboards and analytics consumers, you need a standard table copy that supports Snowflake's full analytics feature set.

This guide covers four patterns that bridge Hybrid Tables to analytics workloads.

### Patterns in This Guide

| Pattern | Freshness | Best For |
|---------|-----------|----------|
| Task + MERGE Snapshot | Minutes | BI dashboards, general analytics |
| Dynamic Tables on ST copy | TARGET_LAG | Complex derived datasets, multi-table joins |
| Materialized Views on ST copy | Automatic | Simple precomputed aggregations |
| Precomputed Analytics to HT | Minutes | High-concurrency dashboard KPI point lookups |

### Other Guides in This Series

- **[Streaming and Change Detection](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)** — HT ingest buffer, watermark CDC, outbound event notifications
- **[Data Management and Operations](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)** — Fan-in aggregation, hot/cold tiering, monitoring

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Familiarity with Snowflake Tasks and MERGE

<!-- ------------------------ -->
## Setup

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_ANALYTICS_QS_ROLE;
GRANT ROLE HT_ANALYTICS_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_ANALYTICS_QS_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_ANALYTICS_QS_WH TO ROLE HT_ANALYTICS_QS_ROLE;

CREATE OR REPLACE DATABASE HT_ANALYTICS_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_ANALYTICS_QS_DB TO ROLE HT_ANALYTICS_QS_ROLE;

USE ROLE HT_ANALYTICS_QS_ROLE;
CREATE OR REPLACE SCHEMA HT_ANALYTICS_QS_DB.DATA;
USE WAREHOUSE HT_ANALYTICS_QS_WH;
USE DATABASE HT_ANALYTICS_QS_DB;
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
    SEQ4(),
    UNIFORM(1, 10000, RANDOM())::NUMBER,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    DATEADD(SECOND, UNIFORM(0,7776000,RANDOM()), DATEADD(DAY,-90,CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ,
    NULL::TIMESTAMP_NTZ,
    ROUND(UNIFORM(5.00,2500.00,RANDOM()),2)
FROM TABLE(GENERATOR(ROWCOUNT => 500000));

SELECT COUNT(*) FROM orders; -- Expected: 500000
```

<!-- ------------------------ -->
## Step 1: The Analytics Anti-Pattern

Before building a pipeline layer, observe what happens when you run analytics directly on the Hybrid Table.

```sql
SELECT region, status, COUNT(*) AS order_count, SUM(total_amount) AS revenue
FROM orders
GROUP BY region, status
ORDER BY revenue DESC;
```

Open the Query Profile. You will see `TableScan` with `COLUMN_BASED` scan mode and ~500,000 rows scanned. No result cache, no partition pruning. For a dashboard refreshing every 30 seconds with multiple concurrent users, you pay full scan cost every time.

The solution: snapshot the data to a standard table where clustering, result cache, Dynamic Tables, and Materialized Views are all available.

<!-- ------------------------ -->
## Step 2: Task-Based Snapshot (MERGE)

A scheduled Task uses MERGE to keep a standard table copy in sync with the Hybrid Table. BI tools read from the standard table, never from the HT directly.

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

INSERT INTO orders_analytics (order_id, customer_id, status, region, created_at, updated_at, total_amount)
SELECT order_id, customer_id, status, region, created_at, updated_at, total_amount
FROM orders;
```

### Create the Snapshot Task

```sql
CREATE OR REPLACE TASK snapshot_orders_to_analytics
  WAREHOUSE = HT_ANALYTICS_QS_WH
  SCHEDULE = '5 MINUTES'
AS
  MERGE INTO orders_analytics AS tgt
  USING orders AS src
  ON tgt.order_id = src.order_id
  WHEN MATCHED AND (src.status != tgt.status OR src.updated_at != tgt.updated_at OR src.total_amount != tgt.total_amount)
    THEN UPDATE SET
      tgt.status       = src.status,
      tgt.updated_at   = src.updated_at,
      tgt.total_amount = src.total_amount,
      tgt.snapshot_ts  = CURRENT_TIMESTAMP()
  WHEN NOT MATCHED
    THEN INSERT (order_id, customer_id, status, region, created_at, updated_at, total_amount, snapshot_ts)
    VALUES (src.order_id, src.customer_id, src.status, src.region, src.created_at, src.updated_at, src.total_amount, CURRENT_TIMESTAMP());

ALTER TASK snapshot_orders_to_analytics RESUME;
```

Verify:

```sql
SHOW TASKS;
SELECT COUNT(*) FROM orders_analytics; -- Expected: 500000
```

> **Note:** The MERGE scans the full Hybrid Table on each execution (COLUMN_BASED). For large tables, add a watermark filter to limit the scan to recently changed rows. See the [Streaming and Change Detection](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/) guide for the watermark pattern.

Suspend for this quickstart:

```sql
ALTER TASK snapshot_orders_to_analytics SUSPEND;
```

<!-- ------------------------ -->
## Step 3: Dynamic Tables on the Standard Table Copy

Dynamic Tables cannot read from Hybrid Tables directly. Create them on the standard table copy.

### Regional Revenue Summary

```sql
CREATE OR REPLACE DYNAMIC TABLE regional_revenue
  TARGET_LAG = '10 MINUTES'
  WAREHOUSE = HT_ANALYTICS_QS_WH
AS
  SELECT
    region,
    DATE_TRUNC('day', created_at) AS order_date,
    COUNT(*)                      AS order_count,
    SUM(total_amount)             AS daily_revenue,
    AVG(total_amount)             AS avg_order_value
  FROM orders_analytics
  GROUP BY region, DATE_TRUNC('day', created_at);
```

### Customer Lifetime Summary

```sql
CREATE OR REPLACE DYNAMIC TABLE customer_summary
  TARGET_LAG = '10 MINUTES'
  WAREHOUSE = HT_ANALYTICS_QS_WH
AS
  SELECT
    customer_id,
    COUNT(*)                           AS total_orders,
    SUM(total_amount)                  AS lifetime_value,
    MAX(created_at)                    AS last_order_at,
    COUNT_IF(status = 'PENDING')       AS pending_orders
  FROM orders_analytics
  GROUP BY customer_id;
```

```sql
SHOW DYNAMIC TABLES;

SELECT * FROM regional_revenue WHERE region = 'US-EAST' ORDER BY order_date DESC LIMIT 5;
SELECT * FROM customer_summary ORDER BY lifetime_value DESC LIMIT 10;
```

Dynamic Tables refresh automatically within `TARGET_LAG` of changes in `orders_analytics`. Result cache applies to consumer queries against the DT.

### When to Use Dynamic Tables vs MERGE Task

| | MERGE Task | Dynamic Table |
|--|------------|--------------|
| Query complexity | Any (including cross-HT joins) | Any SQL |
| Refresh trigger | Schedule-based | Lag-based (automatic) |
| Multiple source tables | Yes (explicit MERGE per source) | Yes (native JOIN support) |
| Incremental refresh | Manual (watermark) | Automatic where possible |

<!-- ------------------------ -->
## Step 4: Materialized Views on the Standard Table Copy

Materialized Views cannot be created on Hybrid Tables. Create them on the standard table copy for simple precomputed aggregations.

```sql
CREATE OR REPLACE MATERIALIZED VIEW mv_order_status_summary AS
  SELECT
    status,
    region,
    COUNT(*)          AS order_count,
    SUM(total_amount) AS total_revenue
  FROM orders_analytics
  GROUP BY status, region;
```

```sql
SELECT * FROM mv_order_status_summary ORDER BY total_revenue DESC;
```

The MV is maintained incrementally as `orders_analytics` changes. Consumer queries hit the precomputed result.

### When to Use MV vs Dynamic Table

| Feature | Materialized View | Dynamic Table |
|---------|------------------|--------------|
| Multi-table joins | No | Yes |
| Window functions | No | Yes |
| Refresh model | Automatic incremental | TARGET_LAG based |
| Storage cost | Aggregation result only | Full result set |
| Best for | Simple GROUP BY on one table | Complex derived datasets |

<!-- ------------------------ -->
## Step 5: Precomputed Analytics Served from a Hybrid Table

For high-concurrency dashboards where each panel filters by a single dimension (customer, region, product), precompute the aggregations on the standard table and store results in a Hybrid Table. Each dashboard request becomes a single-digit millisecond indexed point lookup instead of a repeated GROUP BY scan.

### Create the Dashboard-Serving HT

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

### Populate from the Standard Table

```sql
INSERT INTO dashboard_customer_kpis
SELECT
    customer_id,
    COUNT(*)                           AS total_orders,
    SUM(total_amount)                  AS lifetime_value,
    AVG(total_amount)                  AS avg_order_size,
    MAX(created_at)                    AS last_order_at,
    COUNT_IF(status = 'PENDING')       AS pending_count,
    MODE(region)                       AS region,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS computed_at
FROM orders_analytics
GROUP BY customer_id;
```

### Refresh Task

```sql
CREATE OR REPLACE TASK refresh_dashboard_kpis
  WAREHOUSE = HT_ANALYTICS_QS_WH
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
    MODE(region),
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
  FROM orders_analytics
  GROUP BY customer_id;
END;
```

### Dashboard Query — Single-Digit ms

```sql
SET CUSTOMER = (SELECT customer_id FROM dashboard_customer_kpis LIMIT 1);
SELECT * FROM dashboard_customer_kpis WHERE customer_id = $CUSTOMER;
```

Query Profile: `TableScan`, `ROW_BASED`, 1 row scanned. The expensive GROUP BY ran once on the standard table during the Task refresh; the dashboard gets a primary key lookup.

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your own workload:

> "I have a Hybrid Table with frequent GROUP BY queries that are slow. Help me design a Task-based snapshot pipeline to a Standard Table so analytics can run on columnar storage instead."

> "Convert this GROUP BY query running on my Hybrid Table to use the precomputed KPI serving pattern with a Hybrid Table as the serving layer: [paste query]."

> "Design a Dynamic Table layer on top of my Standard Table snapshot. My HT schema is: [paste DDL]. I need hourly refreshed aggregates for a BI dashboard."

<!-- ------------------------ -->
## Cleanup

```sql
ALTER TASK IF EXISTS snapshot_orders_to_analytics SUSPEND;
ALTER TASK IF EXISTS refresh_dashboard_kpis SUSPEND;
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_ANALYTICS_QS_DB;
DROP WAREHOUSE IF EXISTS HT_ANALYTICS_QS_WH;
DROP ROLE IF EXISTS HT_ANALYTICS_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now:
- Avoid the analytics anti-pattern (direct GROUP BY on HT)
- Build Task + MERGE snapshot pipelines for BI
- Layer Dynamic Tables and Materialized Views on the standard table copy
- Serve precomputed KPIs from a Hybrid Table for millisecond dashboard response

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Streaming and Change Detection Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)
- [Data Management and Operations Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)
- [Architectural Patterns Overview and Decision Matrix](https://www.snowflake.com/en/developers/guides/hybrid-tables-architectural-patterns/)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Tasks Documentation](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Converting Standard Tables to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-standard-to-hybrid-migration/)

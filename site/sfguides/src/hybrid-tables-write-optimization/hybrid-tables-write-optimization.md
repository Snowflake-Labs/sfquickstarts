author: Adam Timm
id: hybrid-tables-write-optimization
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn how to optimize write performance for Hybrid Tables — bound variables for plan cache reuse, batch INSERT patterns, stored procedure overhead, COPY INTO behavior, and common DML anti-patterns.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, write optimization, bound variables, prepared statements, plan cache, parameterized hash, batch INSERT, stored procedure, COPY INTO, CTAS, compilation, latency, OLTP, Unistore, schema qualification
related_concepts: query_parameterized_hash, plan cache hit, compilation overhead, AUTOCOMMIT, multi-statement transaction, bulk load optimization, ON_ERROR ABORT_STATEMENT
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-application-connectors
skill_level: intermediate
estimated_time_minutes: 35
snowflake_features: hybrid_tables, query_parameterized_hash, autocommit, copy_into, tasks
-->

# Optimizing Writes to Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note:** This guide focuses on Snowflake-side write optimization. For driver-specific patterns (JDBC, Python, Node.js connection pooling and batch APIs), see [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/).

Hybrid Table write performance depends on three factors: **plan compilation**, **row store write throughput**, and **index maintenance**. Of these, plan compilation is the most common source of avoidable latency. A well-optimized write path compiles a plan once and reuses it thousands of times per second. A poorly optimized path recompiles on every execution, adding 10-100ms of unnecessary overhead to every write.

This quickstart teaches you how to measure and eliminate compilation overhead, choose the right write pattern for your workload, and avoid the DML anti-patterns that silently degrade performance.

### What You Will Learn

- How the plan cache works and why bound variables are critical
- How to detect plan cache misses using `query_parameterized_hash`
- Why stored procedures add overhead and what to use instead
- How COPY INTO behaves on Hybrid Tables (and when to use it)
- How schema qualification inconsistency splits your plan cache
- The performance hierarchy: AUTOCOMMIT > multi-statement txn > stored procedures
- How to measure the write performance of your workload

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Familiarity with SQL and Snowflake query profiles
- Completion of [Getting Started with Hybrid Tables](https://www.snowflake.com/en/developers/guides/getting-started-with-hybrid-tables/) (recommended)

<!-- ------------------------ -->
## Setup

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_WRITE_QS_ROLE;
GRANT ROLE HT_WRITE_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_WRITE_QS_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_WRITE_QS_WH TO ROLE HT_WRITE_QS_ROLE;

CREATE OR REPLACE DATABASE HT_WRITE_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_WRITE_QS_DB TO ROLE HT_WRITE_QS_ROLE;

USE ROLE HT_WRITE_QS_ROLE;
CREATE OR REPLACE SCHEMA HT_WRITE_QS_DB.DATA;
USE WAREHOUSE HT_WRITE_QS_WH;
USE DATABASE HT_WRITE_QS_DB;
USE SCHEMA DATA;
```

### Create the Orders Table

```sql
CREATE OR REPLACE HYBRID TABLE orders (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    total_amount NUMBER(12,2)  NOT NULL,
    PRIMARY KEY (order_id),
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_status_region (status, region)
)
AS SELECT
    SEQ4(),
    UNIFORM(1, 10000, RANDOM())::NUMBER,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')[UNIFORM(0,3,RANDOM())]::VARCHAR,
    DATEADD(SECOND, UNIFORM(0,7776000,RANDOM()), DATEADD(DAY,-90,CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ,
    ROUND(UNIFORM(5.00,2500.00,RANDOM()),2)
FROM TABLE(GENERATOR(ROWCOUNT => 100000));
```

<!-- ------------------------ -->
## Step 1: Why Plan Compilation Matters

Every SQL statement Snowflake executes goes through two phases: **compilation** (parsing, optimization, plan generation) and **execution** (running the plan against storage). For standard analytical queries that run for seconds to minutes, compilation time is negligible. For Hybrid Table OLTP queries that target single-digit milliseconds, compilation can be 50% or more of total latency.

### Measure Compilation vs Execution

```sql
SET next_id = (SELECT MAX(order_id) + 1 FROM orders);

INSERT INTO orders (order_id, customer_id, status, region, created_at, total_amount)
VALUES ($next_id, 4200, 'PENDING', 'US-EAST', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 99.99);
```

Open the Query Profile. In the Profile Overview, note:
- **Compilation time** — time spent generating the query plan
- **Execution time** — time spent writing to the row store

For a single-row INSERT into a Hybrid Table, you will typically see compilation taking 20-60ms and execution taking 5-20ms. The write itself is fast; the compilation dominates.

### The Plan Cache

When you use **bound variables** (parameterized queries), Snowflake stores the compiled plan in a cache. Subsequent executions with different parameter values skip compilation entirely and reuse the cached plan. This reduces per-query overhead from 30-60ms (compile + execute) to 5-20ms (execute only).

Without bound variables (using string literals), every unique combination of values produces a new query text, which requires a new compilation. At 1,000 queries per second, that is 1,000 compilations per second — each adding unnecessary latency and consuming compilation resources.

<!-- ------------------------ -->
## Step 2: Bound Variables and the Parameterized Hash

### How the Plan Cache Identifies Reusable Plans

Snowflake computes a `query_parameterized_hash` for each query by replacing literal values in predicates with parameters, then hashing the canonicalized SQL text. Queries that produce the same hash reuse the same compiled plan.

### What Shares the Same Hash

Two queries share the same `query_parameterized_hash` if they differ only in:
- Literal values used in comparison operators (`=`, `!=`, `>=`, `<=`)
- Whitespace differences
- Comment differences
- Case-insensitive identifier, session variable, and stage name differences

### Demonstrating Plan Cache Behavior

Run several INSERTs with different literal values:

```sql
INSERT INTO orders VALUES (200001, 1001, 'PENDING', 'US-EAST', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 49.99);
INSERT INTO orders VALUES (200002, 2002, 'SHIPPED', 'EU', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 149.99);
INSERT INTO orders VALUES (200003, 3003, 'DELIVERED', 'APAC', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 299.99);
```

Now check the parameterized hash — all three should share the same hash because only the literal values differ:

```sql
SELECT query_parameterized_hash, query_text, compilation_time, execution_time, total_elapsed_time
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
    DATEADD('minutes', -5, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
WHERE query_text LIKE 'INSERT INTO orders VALUES%'
ORDER BY start_time DESC
LIMIT 5;
```

All three INSERTs should show the same `query_parameterized_hash`. The first one has compilation time (plan was generated); subsequent ones may show reduced compilation (plan reused from cache).

### What Breaks the Hash

These changes produce a DIFFERENT parameterized hash and force recompilation:

```sql
-- Different table reference (schema-qualified vs unqualified)
INSERT INTO orders VALUES (200004, 4004, 'PENDING', 'US-WEST', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 59.99);
INSERT INTO HT_WRITE_QS_DB.DATA.orders VALUES (200005, 5005, 'PENDING', 'EU', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 79.99);
```

```sql
SELECT query_parameterized_hash, query_text
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
    DATEADD('minutes', -5, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
WHERE query_text LIKE 'INSERT INTO%orders VALUES%'
ORDER BY start_time DESC
LIMIT 5;
```

The schema-qualified INSERT produces a **different hash** from the unqualified one. Your application now has two plan cache entries for what is logically the same operation. Each one compiles independently, reducing your effective cache hit rate.

> **Rule:** Pick one naming convention (fully-qualified or unqualified) and use it consistently across all application queries. Mixing them splits your plan cache.

<!-- ------------------------ -->
## Step 3: Schema Qualification Consistency

This is one of the most common silent performance issues in Hybrid Table workloads. It produces no errors, no warnings — just doubled compilation overhead that is invisible unless you look at parameterized hashes.

### The Problem

If your application has two code paths that write to the same table:

```sql
-- Path A (e.g., from a microservice using USE DATABASE/SCHEMA context)
INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?);

-- Path B (e.g., from a stored procedure or different service using fully-qualified names)
INSERT INTO HT_WRITE_QS_DB.DATA.orders VALUES (?, ?, ?, ?, ?, ?);
```

These produce different parameterized hashes. The plan cache maintains two entries, each warming up independently. Your cache hit rate is cut in half.

### How to Detect It

```sql
SELECT
    query_parameterized_hash,
    COUNT(*) AS execution_count,
    ANY_VALUE(query_text) AS sample_query,
    AVG(compilation_time) AS avg_compile_ms,
    AVG(total_elapsed_time) AS avg_total_ms
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
    DATEADD('hours', -1, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
WHERE query_text ILIKE '%INSERT INTO%orders%'
GROUP BY query_parameterized_hash
ORDER BY execution_count DESC;
```

If you see multiple hashes for what is logically the same INSERT statement, check the `sample_query` column — the difference is usually schema qualification.

### The Fix

Standardize on one convention. For applications that set session context (`USE DATABASE`, `USE SCHEMA`) at connection time, unqualified names are simpler:

```sql
-- At connection init (once)
USE DATABASE HT_WRITE_QS_DB;
USE SCHEMA DATA;

-- All subsequent queries (unqualified, same hash every time)
INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?);
```

<!-- ------------------------ -->
## Step 4: Stored Procedure Overhead

Snowflake documentation explicitly states: executing with AUTOCOMMIT enabled or multi-statement transactions offers better performance than calling a stored procedure.

### Why Stored Procedures Add Overhead

A stored procedure introduces:
1. **CALL compilation** — the SP call itself must be compiled
2. **Context switching** — execution transfers from Cloud Services to the XP layer for the SP runtime
3. **Child statement compilation** — each SQL statement inside the SP is compiled separately
4. **Round-trip overhead** — results pass back through the SP runtime to the caller

For a simple single-INSERT stored procedure, this overhead can be 50-100ms on top of the INSERT's own execution time.

### Demonstration

Create a simple SP wrapper:

```sql
CREATE OR REPLACE PROCEDURE insert_order(
    p_order_id NUMBER, p_customer_id NUMBER, p_status VARCHAR,
    p_region VARCHAR, p_amount NUMBER
)
RETURNS VARCHAR
LANGUAGE SQL
AS
BEGIN
    INSERT INTO orders (order_id, customer_id, status, region, created_at, total_amount)
    VALUES (:p_order_id, :p_customer_id, :p_status, :p_region, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, :p_amount);
    RETURN 'OK';
END;
```

Compare the two approaches:

```sql
-- Direct INSERT (faster)
SET direct_id = (SELECT MAX(order_id) + 1 FROM orders);
INSERT INTO orders (order_id, customer_id, status, region, created_at, total_amount)
VALUES ($direct_id, 7777, 'PENDING', 'US-EAST', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 199.99);

-- SP wrapper (slower)
SET sp_id = (SELECT MAX(order_id) + 2 FROM orders);
CALL insert_order($sp_id, 8888, 'PENDING', 'EU', 299.99);
```

Compare in query history:

```sql
SELECT query_text, total_elapsed_time, compilation_time, execution_time
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
    DATEADD('minutes', -5, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
WHERE query_text LIKE 'INSERT INTO orders%' OR query_text LIKE 'CALL insert_order%'
ORDER BY start_time DESC
LIMIT 5;
```

The CALL will show higher `total_elapsed_time` than the direct INSERT for the same logical operation.

### When Stored Procedures Are Appropriate

- Complex business logic that cannot be expressed in a single SQL statement
- Error handling and retry logic
- Multi-step workflows that need procedural flow control

For simple DML wrappers (single INSERT, single UPDATE), the SP adds overhead with no benefit. Use direct parameterized SQL instead.

### The Performance Hierarchy

From best to worst for Hybrid Table single-statement DML:

1. **Direct DML with AUTOCOMMIT=TRUE** (default) — lowest overhead, plan cache works optimally
2. **Multi-statement transaction** (explicit BEGIN/COMMIT) — slight overhead from transaction management, useful for batching related writes
3. **Stored procedure** — highest overhead, use only when procedural logic is required

<!-- ------------------------ -->
## Step 5: COPY INTO Behavior on Hybrid Tables

COPY INTO is supported for Hybrid Tables with specific limitations:

### Key Behaviors

- **`ON_ERROR`**: Only `ABORT_STATEMENT` is supported. `SKIP_FILE` and `CONTINUE` are not available.
- **Optimized bulk load**: COPY INTO an **empty** Hybrid Table uses the fast path (same as CTAS and INSERT INTO SELECT on empty tables). Loading into a non-empty table uses standard INSERT performance.
- **Approximate throughput on non-empty tables**: ~1 million rows per minute (varies with row width and index count)

### When to Use COPY INTO vs INSERT

| Scenario | Recommended Method |
|----------|-------------------|
| Initial table load (empty table) | CTAS (simplest) or COPY INTO (from stage) |
| Batch load from external stage (empty table) | COPY INTO — benefits from optimized path |
| Batch load into populated table | COPY INTO — works, but no fast path |
| Application real-time writes | Direct INSERT with bound variables |
| Kafka/streaming micro-batches | Batch INSERT via driver (see Connectors guide) |

### Verify the Optimized Path Was Used

After a COPY INTO or INSERT INTO SELECT on an empty table, check the Query Profile statistics. If the optimized path was used, the statistics will show **"Number of rows bulk loaded"** rather than "Number of rows inserted."

### Demonstration

```sql
-- Create a stage and export sample data as CSV
CREATE OR REPLACE FILE FORMAT csv_fmt TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"';
CREATE OR REPLACE STAGE orders_stage;

COPY INTO @orders_stage/orders_export
FROM (SELECT order_id, customer_id, status, region, created_at, total_amount FROM orders LIMIT 10000)
FILE_FORMAT = csv_fmt
HEADER = TRUE;

-- Create an empty HT and COPY INTO it (uses optimized bulk load path)
CREATE OR REPLACE HYBRID TABLE orders_copy (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL,
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    total_amount NUMBER(12,2)  NOT NULL,
    PRIMARY KEY (order_id)
);

CREATE OR REPLACE FILE FORMAT csv_load TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1;

COPY INTO orders_copy
FROM @orders_stage/orders_export
FILE_FORMAT = csv_load;

SELECT COUNT(*) FROM orders_copy;
-- Expected: 10000
```

Check the Query Profile for "Number of rows bulk loaded" in the statistics to confirm the fast path was used.

<!-- ------------------------ -->
## Step 6: DML Anti-Patterns

### Anti-Pattern 1: String Concatenation Instead of Bound Variables

```sql
-- BAD: Every unique value creates a new parameterized hash
-- (In application code, this looks like: f"INSERT INTO orders VALUES ({id}, ...)")
INSERT INTO orders VALUES (300001, 1001, 'PENDING', 'US-EAST', '2026-06-16'::TIMESTAMP_NTZ, 49.99);
INSERT INTO orders VALUES (300002, 1001, 'PENDING', 'US-EAST', '2026-06-16'::TIMESTAMP_NTZ, 49.99);
```

Both share the same hash in this case because the literals are in comparable positions. But if non-comparable positions change (e.g., table name constructed dynamically), each execution compiles separately.

```sql
-- GOOD: Use session variables or driver-level bound parameters
SET v_id = 300003;
SET v_cust = 1001;
INSERT INTO orders VALUES ($v_id, $v_cust, 'PENDING', 'US-EAST', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, 49.99);
```

In application code, always use prepared statements (see the [Connectors guide](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)).

### Anti-Pattern 2: CTAS Repeated Against a Populated Table

```sql
-- BAD: CREATE OR REPLACE on a non-empty HT re-creates indexes from scratch
-- every execution. Appropriate for initial load, not for repeated refresh.
CREATE OR REPLACE HYBRID TABLE orders (...) AS SELECT * FROM source_table;
```

If you need to periodically refresh a Hybrid Table from a source, use incremental patterns:
- **MERGE** for upsert semantics
- **INSERT for new rows** + DELETE for removals
- **CTAS+SWAP** only if you can tolerate the post-creation compaction window (see [Streaming Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/) guide, Step 3)

### Anti-Pattern 3: Single-Row INSERTs in a Loop

```sql
-- BAD: 1000 round-trips, 1000 compilations
-- (In application code: for row in rows: cursor.execute("INSERT ...", row))
```

Even with bound variables, each execution is a separate network round-trip. Use batch APIs instead:
- **Python**: `cursor.executemany(sql, list_of_tuples)`
- **JDBC**: `stmt.addBatch()` + `stmt.executeBatch()`
- **Node.js**: `binds: [[row1], [row2], ...]`

Recommended batch size: 500-1,000 rows per call.

### Anti-Pattern 4: BI Tool Running Full-Table CTAS on a HT

```sql
-- BAD: BI materialization running GROUP BY directly on HT
CREATE OR REPLACE TABLE dashboard_data AS
SELECT region, status, COUNT(*), SUM(total_amount)
FROM orders  -- This is the Hybrid Table
GROUP BY region, status;
```

This scans the entire HT via COLUMN_BASED mode on every materialization cycle. The fix: snapshot HT to a standard table first, then run analytics on the standard table. See [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/).

### Anti-Pattern 5: Inconsistent Schema Qualification (Covered in Step 3)

Mixing `INSERT INTO orders` and `INSERT INTO db.schema.orders` splits the plan cache. Pick one and stick with it.

<!-- ------------------------ -->
## Step 7: Measuring Write Performance

### Use AGGREGATE_QUERY_HISTORY for High-Throughput Workloads

Sub-second HT queries may not appear in `QUERY_HISTORY`. Use `AGGREGATE_QUERY_HISTORY` for accurate measurement:

```sql
SELECT
    query_parameterized_hash,
    ANY_VALUE(query_text) AS sample_query,
    SUM(calls) AS total_executions,
    AVG(compilation_time:"avg"::FLOAT) AS avg_compile_ms,
    AVG(execution_time:"avg"::FLOAT) AS avg_exec_ms,
    AVG(total_elapsed_time:"avg"::FLOAT) AS avg_total_ms,
    MAX(total_elapsed_time:"p99"::FLOAT) AS p99_total_ms
FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
WHERE interval_start_time > DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
  AND warehouse_name = 'HT_WRITE_QS_WH'
  AND query_text ILIKE '%INSERT%'
GROUP BY query_parameterized_hash
ORDER BY total_executions DESC;
```

### Key Metrics to Track

| Metric | Healthy | Investigate |
|--------|---------|-------------|
| avg_compile_ms / avg_total_ms | < 30% | > 50% (plan cache not warming) |
| Distinct parameterized hashes for same logical operation | 1 | > 1 (schema qualification issue) |
| P99 / P50 ratio | < 5x | > 10x (compaction or throttling interference) |
| `hybrid_table_requests_throttled_count` | 0 | > 0 (too many concurrent requests) |

### Quick Diagnostic

If writes are slower than expected:

1. Check `compilation_time` vs `execution_time` in query profile — if compilation dominates, it's a plan cache problem
2. Check `query_parameterized_hash` cardinality — multiple hashes for the same operation means cache splitting
3. Check for SP wrapper overhead — compare CALL latency vs child INSERT latency
4. Check for throttling — `hybrid_table_requests_throttled_count > 0` in AGGREGATE_QUERY_HISTORY

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your own workload:

> "Audit my Hybrid Table INSERT patterns for write amplification. Identify any bulk load anti-patterns and suggest fixes."

> "Rewrite these INSERT statements to use bound variables and eliminate redundant recompilation: [paste SQL]."

> "My Hybrid Table bulk load is slow. Review my approach and tell me whether I am using the optimized load path or the standard row-by-row path."

<!-- ------------------------ -->
## Cleanup

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_WRITE_QS_DB;
DROP WAREHOUSE IF EXISTS HT_WRITE_QS_WH;
DROP ROLE IF EXISTS HT_WRITE_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now:
- Use bound variables to achieve plan cache reuse and eliminate unnecessary compilation
- Detect plan cache splits caused by schema qualification inconsistency
- Avoid stored procedure overhead for simple DML operations
- Use COPY INTO correctly (understanding ON_ERROR and fast-path limitations)
- Measure write performance using `query_parameterized_hash` and AGGREGATE_QUERY_HISTORY
- Diagnose whether compilation or execution is the latency bottleneck

### Write Optimization Checklist

| Check | Action |
|-------|--------|
| Using bound variables? | All application queries should use prepared statements |
| One parameterized hash per logical operation? | Standardize schema qualification |
| SP wrapping simple DML? | Remove SP, use direct INSERT |
| Compilation > 50% of total latency? | Plan cache not warming — check hash cardinality |
| Loading into non-empty HT? | No fast path available — ~1M rows/min throughput |
| BI tool scanning HT directly? | Snapshot to standard table first |

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test)
- [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)
- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Streaming and Change Detection Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)
- [Secondary Index Design for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)
- [AGGREGATE_QUERY_HISTORY View](https://docs.snowflake.com/en/sql-reference/account-usage/aggregate_query_history)

<!-- ------------------------ -->
## FAQ

**Q: How do I know if my plan cache is working?**

Check `compilation_time` in query profiles. After the first execution, subsequent executions of the same parameterized query should show near-zero compilation time if the plan cache is active. You can also check `AGGREGATE_QUERY_HISTORY` — if `compilation_time:"avg"` is consistently high across thousands of executions, the cache is not being used.

**Q: Should I worry about plan cache eviction?**

The plan cache has a finite size. Extremely diverse workloads (thousands of distinct query shapes) may experience eviction. For typical OLTP workloads with a small number of distinct INSERT/SELECT/UPDATE patterns, eviction is unlikely. Reducing the number of distinct parameterized hashes (by fixing schema qualification issues) reduces eviction pressure.

**Q: Can I force a plan cache clear?**

No public mechanism exists to explicitly clear the plan cache. Suspending and resuming the warehouse will clear warehouse-level caches, but the plan cache (managed at the Cloud Services layer) has its own lifecycle.

**Q: Is there a plan cache hit rate metric?**

No public metric exposes plan cache hit rate directly. The closest proxy is monitoring `compilation_time` across repeated executions of the same parameterized hash — consistently low compilation time indicates the cache is working.

**Q: Why does COPY INTO only support ON_ERROR = ABORT_STATEMENT for Hybrid Tables?**

Hybrid Table writes are transactional and enforce constraints (PK uniqueness, FK integrity, NOT NULL). Partial-file loading (`SKIP_FILE`, `CONTINUE`) would require rolling back some rows while keeping others, which conflicts with the row-level constraint enforcement model. The entire COPY operation must succeed or fail atomically.

**Q: What batch size should I use for INSERT?**

There is no single answer — it depends on row width and index count. A practical starting point is 500-1,000 rows per batch call. Profile your specific workload: too small (10-50 rows) wastes round-trips; too large (10,000+) risks hitting query size limits or holding transactions too long.

author: Adam Timm
id: hybrid-tables-secondary-index-design
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn how to design, create, and validate secondary indexes for Hybrid Tables to achieve low-latency point lookups and efficient range scans in your OLTP workloads.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, secondary index, CREATE INDEX, INCLUDE columns, covering index, composite index, index design, query profile, IndexScan, TableScan, ROW_BASED, COLUMN_BASED, OLTP, Unistore, point lookup, range scan, probe scan, bound variables, TIMESTAMP_NTZ
related_concepts: primary key, B-tree index, predicate pushdown, plan cache, query optimization, data type matching, cardinality, selectivity
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-performance-optimization-primer
skill_level: intermediate
estimated_time_minutes: 45
snowflake_features: hybrid_tables, secondary_indexes, include_columns, create_index, show_indexes, query_profile
-->

# Secondary Index Design for Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** The SQL examples in this quickstart use string literals and session variables for clarity. Production OLTP workloads should use bound variables (parameterized queries) so Snowflake can cache and reuse query plans, which is critical for high-throughput workloads. See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices) and [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test).

A [Hybrid Table](https://docs.snowflake.com/en/user-guide/tables-hybrid) stores its data in a row-oriented store. Queries against a Hybrid Table typically resolve to one of three access patterns: row-based primary-key access, row-based secondary-index access, or column-based scans, depending on predicates, indexes, and query shape.

Unlike standard Snowflake tables, which can use micro-partition pruning, result cache, and clustering, Hybrid Tables depend heavily on well-designed primary and secondary indexes, along with plan cache warm-up and warehouse cache, to achieve low latency.

This quickstart teaches you how to design secondary indexes correctly, validate them using query profiles, and avoid the most common index anti-patterns that cause full table scans.

### Scenario

You are building the order management backend for an e-commerce platform. Orders are written by your application in real time and read by customer service agents, fulfillment systems, and operational dashboards. You will model this workload using Hybrid Tables and progressively improve query performance through index design.

### What You Will Learn

- How Hybrid Table indexes differ from standard table clustering
- How to create single-column and composite secondary indexes
- The **equality-first, range-last** rule for composite index column ordering
- How to create **covering indexes** with `INCLUDE` columns to eliminate probe scans
- How to add indexes to a live, actively-used Hybrid Table without downtime
- How to read query profiles to confirm index usage
- The predicates and patterns that **disqualify** a query from index use

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region (Hybrid Tables are not available in GCP, government regions, or trial accounts)
- Familiarity with SQL and Snowflake Snowsight
- ACCOUNTADMIN is used in this quickstart to set up the role, warehouse, and database. Hybrid Tables can be created on any existing database or schema as long as your role has `CREATE TABLE` privileges on that schema — ACCOUNTADMIN is not required for the Hybrid Table itself. Contact your Snowflake administrator if you need `CREATE TABLE` granted on an existing schema.
- To add secondary indexes to an existing Hybrid Table, the role must also have `SELECT` on the table

> **Note:** Queries executed in Snowsight carry additional overhead compared to driver-based access. The absolute latency numbers you observe here will be higher than what your application achieves via JDBC/Python/Node.js. The *relative* difference between indexed and unindexed queries is the key signal to observe.

<!-- ------------------------ -->
## Setup

Open a new SQL Worksheet in Snowsight and run the following to create an isolated environment for this quickstart.

### Create Role, Warehouse, and Database

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_INDEX_QS_ROLE;
GRANT ROLE HT_INDEX_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_INDEX_QS_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_INDEX_QS_WH TO ROLE HT_INDEX_QS_ROLE;

CREATE OR REPLACE DATABASE HT_INDEX_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_INDEX_QS_DB TO ROLE HT_INDEX_QS_ROLE;

CREATE OR REPLACE SCHEMA HT_INDEX_QS_DB.ORDERS;
GRANT OWNERSHIP ON SCHEMA HT_INDEX_QS_DB.ORDERS TO ROLE HT_INDEX_QS_ROLE;

USE ROLE HT_INDEX_QS_ROLE;
USE WAREHOUSE HT_INDEX_QS_WH;
USE DATABASE HT_INDEX_QS_DB;
USE SCHEMA ORDERS;
```

### Create the Orders Table (No Secondary Indexes Yet)

You will start with a Hybrid Table that has **only a primary key**. The primary key creates an index automatically; all other columns will require full table scans until you add secondary indexes.

> **Note:** In production, best practice is to define secondary indexes at table creation time using the `INDEX` clause in the CREATE HYBRID TABLE statement (e.g., `INDEX idx_customer (customer_id)`). This quickstart adds indexes separately after the table is created so you can observe the before/after effect in query profiles. See [Indexing Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-index) for the inline syntax.

```sql
CREATE OR REPLACE HYBRID TABLE orders (
    order_id     NUMBER        NOT NULL AUTOINCREMENT PRIMARY KEY,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2)  NOT NULL,
    created_by   VARCHAR(100)  NOT NULL
);
```

### Load Sample Data

Insert 500,000 orders spread across 10,000 customers, four statuses, and four regions, spanning the past 90 days.

```sql
INSERT INTO orders (customer_id, status, region, created_at, updated_at, total_amount, created_by)
SELECT
    UNIFORM(1, 10000, RANDOM())::NUMBER               AS customer_id,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')
        [UNIFORM(0, 3, RANDOM())]::VARCHAR            AS status,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')
        [UNIFORM(0, 3, RANDOM())]::VARCHAR            AS region,
    DATEADD(SECOND,
        UNIFORM(0, 7776000, RANDOM()),
        DATEADD(DAY, -90, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ)  AS created_at,
    NULL                                              AS updated_at,
    ROUND(UNIFORM(5.00, 2500.00, RANDOM()), 2)        AS total_amount,
    'user_' || UNIFORM(1, 500, RANDOM())::VARCHAR     AS created_by
FROM TABLE(GENERATOR(ROWCOUNT => 500000));
```

Confirm the row count:

```sql
SELECT COUNT(*) FROM orders;
-- Expected: 500000
```

Confirm there are no secondary indexes yet:

```sql
SHOW INDEXES IN TABLE orders;
-- Should show only the PRIMARY KEY index
```

<!-- ------------------------ -->
<!-- INTENT: Show that queries without a matching index cause COLUMN_BASED full scans -->
<!-- EXPECTED_BEHAVIOR: Query profile shows TableScan with Scan Mode = COLUMN_BASED -->
<!-- COMMON_MISTAKE: Assuming Hybrid Tables use micro-partition pruning like standard tables -->
## Step 1: The Cost of a Missing Index

Before adding any secondary indexes, run a query that is typical for a customer service lookup: **find all orders for a specific customer**.

```sql
-- Pick a real customer_id from the data
SET SAMPLE_CUSTOMER = (SELECT customer_id FROM orders LIMIT 1);

-- Customer lookup: no secondary index exists
SELECT order_id, status, created_at, total_amount
FROM orders
WHERE customer_id = $SAMPLE_CUSTOMER
ORDER BY created_at DESC;
```

After this query runs, open the **Query Profile** in Snowsight (click the query ID, then select View Query Profile). Select the **TableScan** operator at the bottom of the plan tree.

You will see:

| Attribute | Value |
|-----------|-------|
| **Scan Mode** | `COLUMN_BASED` |
| **Rows scanned** | ~500,000 (the entire table) |

`COLUMN_BASED` scan mode means Snowflake could not use the row store or any index, so it fell back to scanning the object storage copy of the data. This is the equivalent of a full table scan on a traditional RDBMS.

> **Note:** Any query on a Hybrid Table that does not filter on the primary key or a secondary index column will produce a `COLUMN_BASED` scan. For an OLTP workload with thousands of queries per second, this is the primary cause of high latency (hundreds of milliseconds instead of single-digit milliseconds).

<!-- ------------------------ -->
<!-- INTENT: Demonstrate CREATE INDEX on a single column and confirm ROW_BASED IndexScan in profile -->
<!-- EXPECTED_BEHAVIOR: IndexScan operator appears; Scan Mode = ROW_BASED; rows scanned proportional to matching rows only -->
<!-- COMMON_MISTAKE: Not waiting for index build to complete (status must be ACTIVE before testing) -->
## Step 2: Single-Column Secondary Index

Add a secondary index on `customer_id`, the most frequent lookup predicate in this workload.

```sql
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
```

The index is built concurrently, so the table remains available for reads and writes. Check the build status:

```sql
SHOW INDEXES IN TABLE orders;
-- Wait until the status column shows ACTIVE for idx_orders_customer_id
```

> **Note:** Only one index build can run at a time. If you submit multiple `CREATE INDEX` statements, they will queue.

Now re-run the same customer lookup:

```sql
SELECT order_id, status, created_at, total_amount
FROM orders
WHERE customer_id = $SAMPLE_CUSTOMER
ORDER BY created_at DESC;
```

Open the Query Profile again. The plan tree now shows an **IndexScan** operator (not TableScan) at the bottom.

| Attribute | Value |
|-----------|-------|
| **Scan Mode** | `ROW_BASED` |
| **Index name** | `IDX_ORDERS_CUSTOMER_ID` |
| **Access predicates** | `ORDERS.CUSTOMER_ID = (:SFAP_PRE_NR_1)` |
| **Rows scanned** | ~50 (rows matching that customer_id) |

`ROW_BASED` scan mode with an IndexScan means the query went directly to the relevant rows in the row store, with no full scan. You should see a significant latency improvement; exact numbers vary by data distribution, row count, and warehouse state.

### How It Works

When you create `idx_orders_customer_id`, Hybrid Table storage builds a separate B-tree structure in the row store keyed by `customer_id`. When a query filters on `customer_id = <value>`, the query optimizer seeks directly to matching entries in this index B-tree, then fetches only those rows from the primary store. The number of rows scanned is proportional to how many orders that customer has, not the total table size.

<!-- ------------------------ -->
<!-- INTENT: Teach composite index column ordering — equality columns first, range column last -->
<!-- EXPECTED_BEHAVIOR: All three predicates pushed as access predicates when order is correct -->
<!-- COMMON_MISTAKE: Putting range predicate (timestamp) as leading column; putting low-cardinality boolean first -->
## Step 3: Composite Indexes: Equality First, Range Last

A common operational query is: **find all PENDING orders in a specific region, created in the last 7 days**. This query has:
- Two equality predicates (`status`, `region`)
- One range predicate (`created_at >`)

The column ordering in a composite index matters. The rule is:

> **Rule:** Equality predicates come first. A range predicate comes last. Only one range predicate can benefit from the index.

### Correct Design

```sql
CREATE INDEX idx_orders_status_region_ts
    ON orders (status, region, created_at);
```

This index can be used when:
- Querying on `status` alone
- Querying on `status` + `region`
- Querying on `status` + `region` + a range on `created_at`

Run the operational query:

```sql
SELECT order_id, customer_id, created_at, total_amount
FROM orders
WHERE status   = 'PENDING'
  AND region   = 'US-EAST'
  AND created_at > DATEADD(DAY, -7, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
ORDER BY created_at DESC;
```

The query profile will show an **IndexScan** on `IDX_ORDERS_STATUS_REGION_TS` with all three predicates pushed as access predicates.

> **Note:** Predicate values must match the data type of the indexed column. `CURRENT_TIMESTAMP()` returns `TIMESTAMP_LTZ`. Since `created_at` is declared as `TIMESTAMP_NTZ`, the `::TIMESTAMP_NTZ` cast is required for the predicate to be pushed to the index. Without it, the implicit type conversion causes a full table scan.

### Why Column Order Matters

Consider what would happen if you reversed the columns to `INDEX (created_at, status, region)`:

- The index B-tree is sorted by `created_at` first.
- A filter on `status = 'PENDING'` **cannot** be pushed to the index seek position because `status` is not a leading key.
- The query would require scanning the entire time range to find matching statuses.

The rule is: order composite indexes to match your most common query patterns. Equality predicates go first, and the range predicate goes last.

### Verify Index Selectivity

Before investing in an index, check how selective your predicate is:

```sql
-- How many distinct customer_ids? High = good selectivity
SELECT APPROX_COUNT_DISTINCT(customer_id) AS distinct_customers FROM orders;

-- Distribution of status values? Low cardinality -- index alone on status is weak
SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY 2 DESC;
```

> **Note:** A single-column index on a low-cardinality column like `status` (only 4 values) is a poor standalone index because it still scans a large fraction of the table. It becomes more selective as the **leading** column of a composite index that also constrains `region` and `created_at`.

**Ordering within equality columns:** Within the equality prefix of a composite index, higher-cardinality columns should generally lead. A boolean column like `is_active` (2 distinct values) as the leading key means every seek still touches roughly half the index. A higher-cardinality column like `region` (4 values) or `customer_id` (10,000 values) narrows the seek range considerably.

```sql
-- Less effective: boolean column leads, large fraction of index scanned on every seek
CREATE INDEX idx_poor ON orders (is_active, region, created_at);

-- Better: higher-cardinality column leads, much smaller seek range
CREATE INDEX idx_better ON orders (region, is_active, created_at);
```

<!-- ------------------------ -->
<!-- INTENT: Show how INCLUDE columns create a covering index that eliminates the probe scan -->
<!-- EXPECTED_BEHAVIOR: No probe scan in query profile; IndexScan returns all projected columns directly -->
<!-- COMMON_MISTAKE: Including too many columns (increases storage and write overhead for marginal benefit) -->
## Step 4: Covering Indexes with INCLUDE

When a query uses a secondary index, Snowflake performs two operations. First, it seeks through the index to find rows matching the WHERE clause. Second, it goes back to the main table to fetch the columns in the SELECT that are not part of the index key. That second step is called a **probe scan**, and it adds a row store round-trip for every row the index returns.

`INCLUDE` lets you store additional columns inside the index itself. When all columns referenced by a query are available in the index, Snowflake can skip the probe scan entirely and return results from the index alone.

Think of it this way: without `INCLUDE`, the index is an address book -- it tells you where each row lives, then you go and fetch it. With `INCLUDE`, the index carries a copy of the data you need, so you never leave the index to get your answer.

The queries above retrieve `order_id, customer_id, created_at, total_amount`, but the index only stores `status`, `region`, and `created_at`. For each row matched by the index, Hybrid Table storage must perform a **probe scan** back to the primary store to fetch the remaining columns (`customer_id`, `total_amount`).

For hot query paths with very tight latency requirements, you can eliminate this probe scan by using `INCLUDE` columns.

```sql
-- Drop the existing index
DROP INDEX orders.idx_orders_status_region_ts;

-- Recreate with INCLUDE columns for the most common projected columns
CREATE INDEX idx_orders_status_region_ts
    ON orders (status, region, created_at)
    INCLUDE (customer_id, total_amount);
```

Now re-run the query:

```sql
SELECT order_id, customer_id, created_at, total_amount
FROM orders
WHERE status   = 'PENDING'
  AND region   = 'US-EAST'
  AND created_at > DATEADD(DAY, -7, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
ORDER BY created_at DESC;
```

In the Query Profile, the IndexScan will no longer have a **probe scan** step above it -- the index itself provides all the projected columns. This eliminates the round-trip back to the primary store for each matching row.

### When to Use INCLUDE

Use `INCLUDE` when:
- The query path is very hot (thousands of executions per second)
- The projected columns are stable and predictable (always the same set)
- You want to minimize row store round-trips for latency-sensitive reads

Be aware that `INCLUDE` columns increase the storage footprint of the index because those column values are stored twice (in the primary store and in the index). Do not use `INCLUDE` for wide rows or infrequently-queried paths.

<!-- ------------------------ -->
<!-- INTENT: Show that CREATE INDEX on existing tables is non-blocking (concurrent) -->
<!-- EXPECTED_BEHAVIOR: SHOW INDEXES shows status transitioning from BUILD IN PROGRESS to ACTIVE -->
<!-- COMMON_MISTAKE: Submitting multiple CREATE INDEX concurrently (only one build at a time) -->
## Step 5: Adding Indexes to a Live Table

In production, you will often need to add an index to a Hybrid Table that is already serving traffic. The `CREATE INDEX` command builds the index concurrently, so reads and writes continue normally during the build.

Add a final index for the scenario where the fulfillment system needs all orders for a specific region sorted by creation time:

```sql
CREATE INDEX idx_orders_region_created
    ON orders (region, created_at);
```

Check the build status by running `SHOW INDEXES` periodically. The index is live once the `status` column shows `ACTIVE`.

```sql
SHOW INDEXES IN TABLE orders;
```

Once all three builds complete, you should see three secondary indexes plus the primary key:

| Index Name | Columns | Is Unique | Status |
|------------|---------|-----------|--------|
| SYS_INDEX_ORDERS_PRIMARY | ORDER_ID | Y | ACTIVE |
| IDX_ORDERS_CUSTOMER_ID | CUSTOMER_ID | N | ACTIVE |
| IDX_ORDERS_STATUS_REGION_TS | STATUS, REGION, CREATED_AT | N | ACTIVE |
| IDX_ORDERS_REGION_CREATED | REGION, CREATED_AT | N | ACTIVE |

<!-- ------------------------ -->
<!-- INTENT: Teach how to diagnose index usage from query profile scan modes -->
<!-- EXPECTED_BEHAVIOR: Users can identify ROW_BASED vs COLUMN_BASED and take corrective action -->
<!-- COMMON_MISTAKE: Confusing TableScan ROW_BASED (PK access, good) with TableScan COLUMN_BASED (full scan, bad) -->
## Step 6: Reading Query Profiles for Index Diagnosis

The most important skill for operating a Hybrid Table workload is knowing how to quickly determine whether a query is using an index or performing a full scan.

### The Three Scan Patterns

Run each of these queries and compare their profiles:

**Pattern 1: Primary key lookup (fastest)**
```sql
-- Direct PK lookup: TableScan, ROW_BASED, 1 row scanned
SET SAMPLE_ORDER = (SELECT order_id FROM orders LIMIT 1);
SELECT * FROM orders WHERE order_id = $SAMPLE_ORDER;
```
Expected profile: `TableScan` operator, Scan Mode = `ROW_BASED`, rows scanned = 1.

**Pattern 2: Secondary index seek (fast)**
```sql
-- Uses idx_orders_customer_id: IndexScan, ROW_BASED, ~50 rows scanned
SELECT * FROM orders WHERE customer_id = 4200;
```
Expected profile: `IndexScan` operator, Scan Mode = `ROW_BASED`, index name visible in attributes.

**Pattern 3: Full table scan (slow)**
```sql
-- No index on total_amount: TableScan, COLUMN_BASED, 500K rows scanned
SELECT * FROM orders WHERE total_amount > 1000;
```
Expected profile: `TableScan` operator, Scan Mode = `COLUMN_BASED`, rows scanned = ~500,000.

### Quick Diagnostic Checklist

When a Hybrid Table query is slow, open the Query Profile and check the bottom-most operator:

| What You See | What It Means | Action |
|---|---|---|
| `IndexScan`, `ROW_BASED` | Index in use | Check rows scanned -- may need more selective index |
| `TableScan`, `ROW_BASED` | PK lookup in use | Normal for PK filters |
| `TableScan`, `COLUMN_BASED` | Full scan -- no index | Add a secondary index for the WHERE clause column(s) |

Also check the **Profile Overview** panel (deselect all operators) for a **Hybrid Table Requests Throttling** percentage. A high throttling percentage indicates too many requests are being sent to the row store simultaneously, which is often a sign of non-selective index scans.

<!-- ------------------------ -->
<!-- INTENT: Catalog the patterns that prevent index usage so users can avoid them -->
<!-- ANTI_PATTERNS: ILIKE, function_on_column, non_leading_column, range_before_equality, low_cardinality_standalone, non_deterministic_function -->
## Step 7: Index Anti-Patterns

The following patterns look like they should use an index but do not. Each causes a `COLUMN_BASED` full table scan.

### Anti-Pattern 1: `ILIKE` (case-insensitive LIKE)

**Avoid:** `ILIKE` always triggers a full table scan.

```sql
SELECT * FROM orders WHERE region ILIKE 'us%';
```

**Better:** `LIKE` with a constant prefix is index-eligible.

```sql
SELECT * FROM orders WHERE region LIKE 'US%';
```

**Best:** Normalize case at write time and use an equality predicate at read time.

```sql
SELECT * FROM orders WHERE region = 'US-EAST';
```

### Anti-Pattern 2: Function Applied to an Indexed Column

**Avoid:** Wrapping an indexed column in a function disqualifies the index.

```sql
SELECT * FROM orders WHERE LOWER(region) = 'us-east';
```

**Do this instead:** Store normalized values at write time and query without the function.

```sql
SELECT * FROM orders WHERE region = 'US-EAST';
```

### Anti-Pattern 3: Non-Leading Column in Composite Index

The composite index is `(status, region, created_at)`. Querying on `region` alone skips the leading column `status`, so the index cannot be used.

**Avoid:**

```sql
SELECT * FROM orders WHERE region = 'EU';
```

**Do this instead:** Use the dedicated `idx_orders_region_created` index, which has `region` as its leading column.

```sql
SELECT * FROM orders WHERE region = 'EU' AND created_at > DATEADD(DAY, -30, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ;
```

### Anti-Pattern 4: Range Predicate on a Non-Final Column

**Avoid:** Placing a range predicate before equality predicates in the index breaks the seek prefix. Only the columns before the gap can be used for seeking.

```sql
CREATE INDEX idx_bad ON orders (region, created_at, status);

SELECT * FROM orders WHERE region LIKE 'US%' AND created_at > '2026-01-01' AND status = 'PENDING';
```

Only `region` (via the LIKE prefix) benefits from this index. The predicates on `created_at` and `status` are applied as post-scan filters.

**Do this instead:** Equality predicates first, range predicate last.

```sql
-- idx_orders_status_region_ts (status, region, created_at) is the correct design
SELECT * FROM orders WHERE status = 'PENDING' AND region = 'US-EAST' AND created_at > '2026-01-01'::TIMESTAMP_NTZ;
```

### Anti-Pattern 5: Low-Cardinality Standalone Index

**Avoid:** An index on a column with very few distinct values (like `status` with 4 values) still scans a large fraction of the table and provides little benefit on its own.

```sql
CREATE INDEX idx_status_only ON orders (status);
```

**Do this instead:** Combine the low-cardinality column with higher-cardinality columns in a composite index. The index `(status, region, created_at)` seeks to a much smaller subset.

```sql
CREATE INDEX idx_orders_status_region_ts ON orders (status, region, created_at);
```

### Anti-Pattern 6: Non-Deterministic Session Functions in Predicates

Functions like `CURRENT_USER()`, `CURRENT_SESSION()`, `CURRENT_ACCOUNT()`, and `CURRENT_ROLE()` are evaluated at runtime and cannot be pushed to an index access predicate. A query filtering on one of these functions directly will produce a `COLUMN_BASED` full table scan regardless of whether an index exists on the column.

**Avoid:** Using a session function directly in the predicate.

```sql
CREATE INDEX idx_orders_created_by ON orders (created_by);

-- COLUMN_BASED scan even with the index, because CURRENT_USER() cannot
-- be pushed to an index access predicate at compile time
SELECT * FROM orders WHERE created_by = CURRENT_USER();
```

**Do this instead:** Capture the value in a session variable first, then use the variable as the predicate.

```sql
SET active_user = CURRENT_USER();
SELECT * FROM orders WHERE created_by = $active_user;
```

<!-- ------------------------ -->
## Cleanup

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_INDEX_QS_DB;
DROP WAREHOUSE IF EXISTS HT_INDEX_QS_WH;
DROP ROLE IF EXISTS HT_INDEX_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You have completed the Hybrid Tables Secondary Index Design quickstart. You can now:

- **Create secondary indexes** at table creation time and on live, active tables
- **Order composite index columns** correctly: equality predicates first, range predicate last
- **Eliminate probe scans** using `INCLUDE` columns for high-throughput query paths
- **Diagnose index usage** by reading `IndexScan` vs `TableScan` operators and `ROW_BASED` vs `COLUMN_BASED` scan modes in query profiles
- **Avoid** the anti-patterns (ILIKE, functions on indexed columns, non-leading column predicates) that force full table scans

### Index Design Decision Summary

| Scenario | Recommended Index |
|----------|------------------|
| Single-column equality lookups | `INDEX idx (col)` |
| Multi-column equality + one range | `INDEX idx (eq_col1, eq_col2, range_col)` |
| Hot read path, avoid probe scan | `INDEX idx (key_cols) INCLUDE (projected_cols)` |
| Adding index to live table | `CREATE INDEX idx ON table(col)`, then monitor with `SHOW INDEXES` |
| Low-cardinality column alone | Combine with high-cardinality column as leading prefix |

### Related Resources

- [Hybrid Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-hybrid)
- [Indexing Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-index)
- [Analyze Query Profiles for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-read-query-profiles)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test)
- [Getting Started with Hybrid Tables Quickstart](https://www.snowflake.com/en/developers/guides/getting-started-with-hybrid-tables/)
- [Hybrid Tables Performance Optimization Primer](https://www.snowflake.com/en/developers/guides/hybrid-tables-performance-optimization-primer/)

<!-- ------------------------ -->
## FAQ and Troubleshooting

**Q: My query still shows COLUMN_BASED scan even after I created an index. Why?**

Check these common causes in order:
1. The index build may not be complete. Run `SHOW INDEXES IN TABLE` and verify `status = ACTIVE`.
2. The predicate column may not match the leading column(s) of the index.
3. You may have a data type mismatch (e.g., comparing `TIMESTAMP_LTZ` against a `TIMESTAMP_NTZ` indexed column). Add an explicit cast.
4. The predicate may use a disqualifying pattern: `ILIKE`, a function wrapping the column, or a non-deterministic session function.

**Q: How many secondary indexes can I create on a single Hybrid Table?**

There is no hard limit on the number of secondary indexes. However, each index adds write overhead (indexes are maintained synchronously on every INSERT/UPDATE/DELETE) and increases storage consumption. Balance read performance gains against write latency requirements.

**Q: Should I use INCLUDE on every index?**

No. INCLUDE columns duplicate data from the primary store into the index, increasing storage. Use INCLUDE only on hot query paths where the projected columns are stable and the latency savings justify the storage cost.

**Q: Can I create an index on a VARIANT, ARRAY, OBJECT, or GEOGRAPHY column?**

No. Geospatial data types (GEOGRAPHY, GEOMETRY), semi-structured types (ARRAY, OBJECT, VARIANT), and vector types (VECTOR) are not supported in indexed columns. These columns can exist in a Hybrid Table but cannot be part of a PRIMARY KEY or secondary index.

**Q: What is the difference between IndexScan and TableScan with ROW_BASED mode?**

`TableScan` with `ROW_BASED` indicates a primary key lookup. `IndexScan` with `ROW_BASED` indicates a secondary index was used. Both are efficient row store operations. `TableScan` with `COLUMN_BASED` indicates a full scan of the object storage copy of the data (equivalent to a full table scan).

**Q: My index build is stuck at BUILD IN PROGRESS. What should I do?**

Only one index build can run at a time per table. If you submitted multiple `CREATE INDEX` commands, they queue sequentially. Wait for each to complete before expecting the next to start. If a build appears stuck for an extended period, check for long-running transactions that may be blocking the build.

**Q: Do bound variables affect index usage?**

Bound variables (parameterized queries) do not change whether an index is used, but they are critical for performance. When you use bound variables, Snowflake can cache the compiled query plan and reuse it across executions. With string literals, each unique value produces a new plan compilation. For high-throughput OLTP workloads, always use bound variables.

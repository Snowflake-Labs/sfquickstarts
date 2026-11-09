author: Adam Timm
id: hybrid-tables-standard-to-hybrid-migration
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/hybrid-tables
language: en
summary: Learn how to assess, migrate, and validate the conversion of standard Snowflake tables to Hybrid Tables for low-latency OLTP workloads.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, migration, standard table, convert, OLTP, primary key, secondary index, bulk load, zero downtime, rename, swap, query profile, ROW_BASED, COLUMN_BASED, Unistore, INSERT INTO SELECT, CTAS, bound variables
related_concepts: CREATE HYBRID TABLE, ALTER TABLE RENAME, foreign key, UNIQUE constraint, plan cache, IndexScan, TableScan, COLUMN_BASED scan
prerequisite_guides: getting-started-with-hybrid-tables
skill_level: intermediate
estimated_time_minutes: 40
snowflake_features: hybrid_tables, secondary_indexes, alter_table_rename, bulk_load_optimization, query_profile
-->

# Converting Standard Snowflake Tables to Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Migrations:** Always test migrations on a non-production copy first. Validate row counts, query plans, and application behavior before decommissioning the standard table. Production OLTP workloads should use bound variables (parameterized queries) for plan cache reuse. See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices) and [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test).

A [Hybrid Table](https://docs.snowflake.com/en/user-guide/tables-hybrid) stores data in a row-oriented store optimized for low-latency point lookups and small-range scans. Standard Snowflake tables store data in columnar micro-partitions optimized for analytical workloads.

If your workload has shifted toward OLTP patterns (frequent single-row lookups, status updates, point reads by ID), standard tables may no longer be the right fit. Hybrid Tables provide single-digit millisecond reads for indexed lookups, something standard tables cannot achieve once result cache misses.

This quickstart walks through the full migration lifecycle: assessing a standard table for suitability, creating the Hybrid Table equivalent, bulk-loading data, adding secondary indexes, validating with query profiles, and performing a zero-downtime swap.

### Scenario

You manage the order management backend for an e-commerce platform. The `orders` table was originally built as a standard Snowflake table. As order volume grew, operational queries (order lookups by customer, status checks by region) started hitting full table scans with inconsistent latency. You will migrate this table to a Hybrid Table.

### What You Will Learn

- How to assess whether a standard table is a good candidate for Hybrid Table conversion
- The DDL differences between standard tables and Hybrid Tables (PRIMARY KEY requirement, constraint support)
- How to bulk load data from a standard table into a Hybrid Table using the optimized path
- How to add secondary indexes on a populated Hybrid Table without downtime
- How to add a FOREIGN KEY to a populated Hybrid Table, monitor the background build, and recover from a validation failure
- How to carry business rules into the migration as CHECK constraints, and why they must be declared at creation time
- How to compare query profiles before and after migration (COLUMN_BASED vs ROW_BASED)
- How to perform a zero-downtime swap using ALTER TABLE RENAME

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region (Hybrid Tables are not available in GCP, government regions, or trial accounts)
- Familiarity with SQL and Snowflake Snowsight
- ACCOUNTADMIN is used in this quickstart to set up the role, warehouse, and database. Hybrid Tables can be created on any existing database or schema as long as your role has `CREATE TABLE` privileges on that schema.

<!-- ------------------------ -->
## Setup

Open a new SQL Worksheet in Snowsight and run the following to create an isolated environment for this quickstart.

### Create Role, Warehouse, and Database

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_MIGRATION_QS_ROLE;
GRANT ROLE HT_MIGRATION_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_MIGRATION_QS_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;
GRANT OWNERSHIP ON WAREHOUSE HT_MIGRATION_QS_WH TO ROLE HT_MIGRATION_QS_ROLE;

CREATE OR REPLACE DATABASE HT_MIGRATION_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_MIGRATION_QS_DB TO ROLE HT_MIGRATION_QS_ROLE;

USE ROLE HT_MIGRATION_QS_ROLE;

CREATE OR REPLACE SCHEMA HT_MIGRATION_QS_DB.ORDERS;

USE WAREHOUSE HT_MIGRATION_QS_WH;
USE DATABASE HT_MIGRATION_QS_DB;
USE SCHEMA ORDERS;
```

<!-- ------------------------ -->
## Step 1: Create the Standard Table

First, create a standard Snowflake table with 500,000 orders. This simulates the starting state of a workload that was built without OLTP optimization in mind. Notice there is no PRIMARY KEY or index.

```sql
CREATE OR REPLACE TABLE orders_standard (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2)  NOT NULL
);

INSERT INTO orders_standard (order_id, customer_id, status, region, created_at, updated_at, total_amount)
SELECT
    SEQ4()                                                AS order_id,
    UNIFORM(1, 10000, RANDOM())::NUMBER                  AS customer_id,
    ARRAY_CONSTRUCT('PENDING','SHIPPED','DELIVERED','CANCELLED')
        [UNIFORM(0, 3, RANDOM())]::VARCHAR               AS status,
    ARRAY_CONSTRUCT('US-EAST','US-WEST','EU','APAC')
        [UNIFORM(0, 3, RANDOM())]::VARCHAR               AS region,
    DATEADD(SECOND,
        UNIFORM(0, 7776000, RANDOM()),
        DATEADD(DAY, -90, CURRENT_TIMESTAMP()))::TIMESTAMP_NTZ  AS created_at,
    NULL                                                 AS updated_at,
    ROUND(UNIFORM(5.00, 2500.00, RANDOM()), 2)           AS total_amount
FROM TABLE(GENERATOR(ROWCOUNT => 500000));
```

Confirm the row count:

```sql
SELECT COUNT(*) FROM orders_standard;
-- Expected: 500000
```

### Run a Baseline Query

Run a typical operational query and note the latency:

```sql
SET SAMPLE_CUSTOMER = (SELECT customer_id FROM orders_standard LIMIT 1);

SELECT order_id, status, created_at, total_amount
FROM orders_standard
WHERE customer_id = $SAMPLE_CUSTOMER
ORDER BY created_at DESC;
```

Open the Query Profile. You will see a `TableScan` operator scanning all micro-partitions. Standard tables have no row-level index on `customer_id`, so every query on this column requires scanning the full table (or relying on result cache for repeated identical queries).

<!-- ------------------------ -->
## Step 2: Assess the Table for Hybrid Table Suitability

Not every standard table should be converted to a Hybrid Table. Use this checklist to evaluate candidates.

### Assessment Checklist

| Criterion | orders_standard |
|-----------|----------------|
| Has a natural primary key? | order_id (unique per row) |
| Dominant access pattern? | Point lookups by order_id, customer_id |
| Read:Write ratio? | Mixed (orders created and status-updated frequently) |
| Row count manageable? | 500K (well within HT capacity) |
| Needs result cache for repeated queries? | No (operational queries need fresh data) |
| Has Streams, Dynamic Tables, or MVs? | No downstream dependencies |
| Business rules to enforce in the database? | Yes: amounts must be positive, status must be a known value |

### Inventory the Business Rules You Want to Enforce

Migration is the moment to decide which business rules the database should enforce, because a CHECK constraint on a Hybrid
Table can only be declared when the table is created. Unlike a FOREIGN KEY, you cannot add one later with `ALTER TABLE`, so
a rule you skip here means recreating the table to introduce it.

A standard table that was never constrained often contains values the application assumed could not happen. Check the
candidate rules against the existing data before you migrate:

```sql
SELECT
    COUNT(*)                                                   AS total_rows,
    COUNT_IF(total_amount <= 0)                                AS nonpositive_amounts,
    COUNT_IF(status NOT IN ('PENDING','SHIPPED','DELIVERED','CANCELLED')) AS unknown_statuses
FROM orders_standard;
-- Expected for this dataset: 500000 total, 0 violations of either rule
```

Both counts must be zero before you add the matching constraint. A single violating row aborts the entire migration load,
so it is much cheaper to find them now than to debug a failed CTAS later.

### Verify Primary Key Uniqueness

Before migration, confirm the candidate PK column has no duplicates:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT order_id) AS distinct_order_ids
FROM orders_standard;
-- Both values should be 500000
```

### Check for Unsupported Downstream Dependencies

Hybrid Tables do not support:

- **Streams** (change tracking)
- **Dynamic Tables** (cannot be downstream of a HT)
- **Materialized Views**
- **Clustering keys** (HT uses indexes instead)

If your standard table has any of these attached, you will need to re-architect those components before migrating. A common pattern is to keep a Task-based snapshot from the Hybrid Table to a standard table for analytics and change-tracking purposes. For step-by-step implementation of these patterns, see the [Architectural Patterns for Hybrid Table Workloads](https://www.snowflake.com/en/developers/guides/hybrid-tables-architectural-patterns/) quickstart.

### Identify Index Candidates

Check the cardinality of your most common WHERE clause columns:

```sql
SELECT 'customer_id' AS column_name, APPROX_COUNT_DISTINCT(customer_id) AS distinct_values FROM orders_standard
UNION ALL
SELECT 'status', APPROX_COUNT_DISTINCT(status) FROM orders_standard
UNION ALL
SELECT 'region', APPROX_COUNT_DISTINCT(region) FROM orders_standard;
```

Expected results: customer_id has ~10,000 distinct values (high cardinality, excellent index candidate), status has 4, region has 4. Low-cardinality columns like status and region work well as leading columns in composite indexes.

<!-- ------------------------ -->
## Step 3: Create the Hybrid Table

Create the Hybrid Table equivalent with a PRIMARY KEY and secondary indexes defined inline. Best practice is to declare indexes at table creation time so they are populated during the initial bulk load.

```sql
CREATE OR REPLACE HYBRID TABLE orders_hybrid (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10)   NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    updated_at   TIMESTAMP_NTZ,
    total_amount NUMBER(12,2)  NOT NULL,
    PRIMARY KEY (order_id),
    INDEX idx_orders_customer_id (customer_id),
    INDEX idx_orders_status_region_ts (status, region, created_at),
    CONSTRAINT chk_total_amount_positive CHECK (total_amount > 0),
    CONSTRAINT chk_status_known CHECK (status IN ('PENDING','SHIPPED','DELIVERED','CANCELLED'))
)
AS SELECT * FROM orders_standard;
```

This single statement:
1. Defines the Hybrid Table schema with a PRIMARY KEY on `order_id`
2. Declares two secondary indexes inline (customer lookup and composite status/region/timestamp)
3. Declares the two business rules you inventoried in Step 2 as named CHECK constraints
4. Loads all 500,000 rows and populates the indexes using the optimized bulk load path

> **Note:** CTAS for Hybrid Tables requires you to declare the full column schema explicitly. Unlike standard table CTAS, the schema cannot be inferred from the SELECT. CTAS also cannot declare a FOREIGN KEY constraint. To create a Hybrid Table with a foreign key, load it with CTAS as shown above, then add the foreign key with `ALTER TABLE`. See **Add a Foreign Key After Loading**, below.

> **Important:** CHECK constraints behave the opposite way. A Hybrid Table accepts them in CTAS, but only at creation time — `ALTER TABLE ... ADD CONSTRAINT ... CHECK` fails with `001186 (42P16): Unsupported table type for CHECK constraint: Hybrid table`, and adding `ENABLE NOVALIDATE` does not change that. Declare every CHECK you need in the CREATE statement, because introducing one later means recreating the table.

> **Note:** You can also add secondary indexes after table creation using `CREATE INDEX`. This is useful when you discover new access patterns on a live table. For a full exploration of adding indexes to populated tables, composite index column ordering, INCLUDE columns, and anti-patterns, see the [Secondary Index Design for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/) quickstart.

### Validate Row Counts

```sql
SELECT 'orders_standard' AS table_name, COUNT(*) AS row_count FROM orders_standard
UNION ALL
SELECT 'orders_hybrid', COUNT(*) FROM orders_hybrid;
```

Both should show 500,000. If they differ, investigate constraint violations (NULL in NOT NULL columns, duplicate PKs).

### Confirm the Business Rules Are Enforced

The CTAS validated all 500,000 existing rows against both CHECK constraints as it loaded them. From now on the constraints
also reject new violating writes:

```sql
-- Fails: violates chk_total_amount_positive
INSERT INTO orders_hybrid
    (order_id, customer_id, status, region, created_at, updated_at, total_amount)
VALUES (999999901, 1, 'PENDING', 'EU', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, NULL, -10.00);

-- Fails: violates chk_status_known
INSERT INTO orders_hybrid
    (order_id, customer_id, status, region, created_at, updated_at, total_amount)
VALUES (999999902, 1, 'REFUNDED', 'EU', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, NULL, 10.00);
```

Both statements return an error naming the constraint that rejected them:

```
001185 (23514): Operation on table ORDERS_HYBRID failed because CHECK constraint
CHK_TOTAL_AMOUNT_POSITIVE, which requires that total_amount > 0, was violated
```

That error names `CHK_TOTAL_AMOUNT_POSITIVE` because the constraint was given a name. An unnamed inline CHECK such as
`total_amount NUMBER(12,2) CHECK (total_amount > 0)` is enforced identically, but reports a generated identifier like
`SYS_CONSTRAINT_9727f254-3bdc-44dc-836c-e0f58db5901b` instead, which tells an on-call engineer nothing. Name your
constraints.

#### If the CTAS Fails Instead of Loading

A CHECK is validated against the incoming rows, so a single bad row in the source aborts the whole statement rather than
loading part of the data:

```
001185 (23514): Operation on table ORDERS_HYBRID failed because CHECK constraint
CHK_TOTAL_AMOUNT_POSITIVE, which requires that total_amount > 0, was violated
```

The failure is atomic. If you are re-running `CREATE OR REPLACE` over a Hybrid Table that already exists, the existing table
and all of its rows are left untouched, so a failed attempt does not cost you the previous one. If the table did not exist
yet, nothing is created.

This is the migration working as intended: it refuses to carry data that breaks the rule you just declared. Find the
offending rows in the source, decide whether to correct them or relax the rule, then re-run the CTAS:

```sql
SELECT order_id, status, total_amount
FROM orders_standard
WHERE total_amount <= 0
   OR status NOT IN ('PENDING','SHIPPED','DELIVERED','CANCELLED')
LIMIT 100;
```

> **Important:** A CHECK constraint does not imply NOT NULL. If a column is NULL the predicate evaluates to NULL, which is
> not treated as a violation, so the row is accepted. Every `updated_at` value in this dataset is NULL, so a rule such as
> `CHECK (updated_at >= created_at)` would pass for all 500,000 rows while enforcing nothing. Pair the CHECK with NOT NULL
> when the rule is meant to apply to every row.

### Spot-Check Data Integrity

```sql
SET SAMPLE_ORDER = (SELECT order_id FROM orders_hybrid LIMIT 1);

SELECT * FROM orders_hybrid   WHERE order_id = $SAMPLE_ORDER;
SELECT * FROM orders_standard WHERE order_id = $SAMPLE_ORDER;
```

Both should return identical results.

### Verify Indexes

Confirm the secondary indexes were created and are active:

```sql
SHOW INDEXES IN TABLE orders_hybrid;
```

You should see:

| Index Name | Columns | Is Unique | Status |
|-----------|---------|-----------|--------|
| SYS_INDEX_ORDERS_HYBRID_PRIMARY | ORDER_ID | Y | ACTIVE |
| IDX_ORDERS_CUSTOMER_ID | CUSTOMER_ID | N | ACTIVE |
| IDX_ORDERS_STATUS_REGION_TS | STATUS, REGION, CREATED_AT | N | ACTIVE |

### Add a Foreign Key After Loading

CTAS cannot declare a FOREIGN KEY, but you can add one to the table you just populated. This keeps the optimized bulk load from the CTAS above and adds referential integrity afterward, with no table recreation and no second copy of the data.

First create the parent table that the `customer_id` column will reference:

```sql
CREATE OR REPLACE HYBRID TABLE customers (
    customer_id NUMBER      NOT NULL PRIMARY KEY,
    name        VARCHAR(50)
);

INSERT INTO customers
SELECT DISTINCT customer_id, 'cust_' || customer_id
FROM orders_standard;
```

Before adding the constraint, check for rows that would violate it. A foreign key can only be added if every child value already exists in the parent:

```sql
-- ORPHAN DETECTION: EXPECT 0
SELECT COUNT(*) AS orphan_rows
FROM orders_hybrid o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
```

Now add the constraint:

```sql
ALTER TABLE orders_hybrid
  ADD CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id);
```

This is an online operation. `orders_hybrid` stays available for reads and writes while Snowflake builds the index that backs the constraint in the background. Because the build is asynchronous, the `ALTER TABLE` statement returns *before* the constraint is in place, so a successful `ALTER TABLE` is not proof that the constraint is ready:

```sql
SHOW INDEXES IN TABLE orders_hybrid;
```

Immediately after the `ALTER TABLE`, `FK_CUSTOMER` reports a `status` of `BUILD IN PROGRESS` with a `status_info` of "The index is being built." **Re-run `SHOW INDEXES` until `FK_CUSTOMER` reports `ACTIVE` before you rely on the constraint.** The build runs in the background and takes longer than the `ALTER TABLE` that started it, and how much longer scales with the number of rows being validated, so poll rather than assuming a duration.

> **Note:** A FOREIGN KEY constraint builds its own underlying index, which appears in `SHOW INDEXES` alongside the indexes you declared at creation time. Dropping the constraint removes that index as well.

#### Recovering from a Validation Failure

If any child row has no matching parent, the `ALTER TABLE` still succeeds and the failure surfaces in the background build instead. The constraint lands in `BUILD VALIDATION FAILURE`:

| `status` | `status_info` |
|---|---|
| `BUILD VALIDATION FAILURE` | Index creation failed validation. The existing data violates the constraint. Please review the data, resolve the violations, and try creating the constraint again. |

The index that backs the constraint did not finish building, and it stays in that state until you intervene: it never
reaches `ACTIVE` on its own, and a non-active index is not used to retrieve data. Snowflake does still enforce the
constraint on new writes, so an INSERT or UPDATE that violates it fails with
`200009 (22000): Foreign key constraint "FK_CUSTOMER" was violated.` What the failed build does not do is fix the rows
that were already in the table, which are the rows that failed validation. Because the `ALTER TABLE` reported success,
`SHOW INDEXES` is the only place this shows up.

Recover by dropping the constraint, correcting the data, and adding it again:

```sql
-- FIND THE OFFENDING ROWS
SELECT o.order_id, o.customer_id
FROM orders_hybrid o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

ALTER TABLE orders_hybrid DROP CONSTRAINT fk_customer;

-- CORRECT THE DATA: EITHER INSERT THE MISSING PARENT ROWS,
-- OR REMOVE THE ORPHANED CHILD ROWS

ALTER TABLE orders_hybrid
  ADD CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id);
```

Then re-run `SHOW INDEXES` until `FK_CUSTOMER` reports `ACTIVE`.

<!-- ------------------------ -->
## Step 4: Validate with Query Profile Comparison

The key validation is comparing the same query against both the standard table and the Hybrid Table.

### Customer Lookup Comparison

```sql
SET SAMPLE_CUSTOMER = (SELECT customer_id FROM orders_hybrid LIMIT 1);
```

**Standard table query:**

```sql
SELECT order_id, status, created_at, total_amount
FROM orders_standard
WHERE customer_id = $SAMPLE_CUSTOMER
ORDER BY created_at DESC;
```

Open the Query Profile. You will see:
- Operator: `TableScan`
- Rows scanned: ~500,000 (full table)
- No index available, micro-partition pruning provides no benefit for this predicate

**Hybrid Table query:**

```sql
SELECT order_id, status, created_at, total_amount
FROM orders_hybrid
WHERE customer_id = $SAMPLE_CUSTOMER
ORDER BY created_at DESC;
```

Open the Query Profile. You will see:
- Operator: `IndexScan`
- Scan Mode: `ROW_BASED`
- Index: `IDX_ORDERS_CUSTOMER_ID`
- Rows scanned: ~50 (only rows matching that customer_id)

### Primary Key Lookup Comparison

```sql
SET SAMPLE_ORDER = (SELECT order_id FROM orders_hybrid LIMIT 1);
```

**Standard table:**

```sql
SELECT * FROM orders_standard WHERE order_id = $SAMPLE_ORDER;
```

**Hybrid Table:**

```sql
SELECT * FROM orders_hybrid WHERE order_id = $SAMPLE_ORDER;
```

The Hybrid Table query profile shows `TableScan` with `ROW_BASED` mode and exactly 1 row scanned. This is a direct primary key lookup.

### Composite Index Validation

```sql
SELECT order_id, customer_id, created_at, total_amount
FROM orders_hybrid
WHERE status = 'PENDING'
  AND region = 'US-EAST'
  AND created_at > DATEADD(DAY, -7, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
ORDER BY created_at DESC;
```

The Query Profile should show `IndexScan` using `IDX_ORDERS_STATUS_REGION_TS` with `ROW_BASED` scan mode and all three predicates pushed to the index.

> **Note:** The `::TIMESTAMP_NTZ` cast on `CURRENT_TIMESTAMP()` is required. Without it, the implicit conversion from TIMESTAMP_LTZ prevents the predicate from being pushed to the index. This applies whenever comparing a TIMESTAMP_NTZ indexed column against CURRENT_TIMESTAMP().

<!-- ------------------------ -->
## Step 5: Zero-Downtime Swap

Once you have validated that the Hybrid Table performs correctly, swap it into the production name so applications see no change.

### The Swap Pattern

```sql
ALTER TABLE orders_standard RENAME TO orders_standard_backup;
ALTER TABLE orders_hybrid   RENAME TO orders_standard;
```

Applications querying `orders_standard` now hit the Hybrid Table. No connection string or query changes required.

### Verify the Swap

```sql
SHOW TABLES LIKE 'orders%';
```

You should see:
- `ORDERS_STANDARD` with `is_hybrid = Y` (this is now the Hybrid Table)
- `ORDERS_STANDARD_BACKUP` with `is_hybrid = N` (the original, kept as rollback)

Confirm queries still work against the swapped name:

```sql
SELECT order_id, status, created_at, total_amount
FROM orders_standard
WHERE customer_id = $SAMPLE_CUSTOMER
ORDER BY created_at DESC;
```

The Query Profile should still show `IndexScan` with `ROW_BASED` scan mode.

### Rollback (If Needed)

If issues arise, reverse the swap immediately:

```sql
ALTER TABLE orders_standard        RENAME TO orders_hybrid;
ALTER TABLE orders_standard_backup RENAME TO orders_standard;
```

### Decommission the Backup (When Ready)

After the migration is validated in production for an appropriate period:

```sql
DROP TABLE orders_standard_backup;
```

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your own migration:

> "Assess this Standard Table DDL for Hybrid Table suitability. Identify the primary key candidate, recommended secondary indexes, and any incompatible column types: [paste DDL]."

> "Generate the migration SQL to convert this Standard Table to a Hybrid Table, including CREATE HYBRID TABLE, the initial load, and SWAP: [paste DDL and row count]. If I want CHECK constraints, declare them in the CREATE statement and use CTAS or INSERT INTO ... SELECT rather than COPY INTO."

> "Write a validation query to confirm my Standard-to-Hybrid migration was successful. Compare row counts, sample row checksums, and verify all constraints are enforced on the new HT."

<!-- ------------------------ -->
## Cleanup

Remove all objects created by this quickstart:

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_MIGRATION_QS_DB;
DROP WAREHOUSE IF EXISTS HT_MIGRATION_QS_WH;
DROP ROLE IF EXISTS HT_MIGRATION_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You have completed the Standard-to-Hybrid Table migration quickstart. You can now:

- Assess standard tables for Hybrid Table suitability using a structured checklist
- Create Hybrid Table equivalents with PRIMARY KEY using CTAS, then add FOREIGN KEY constraints to the populated table
- Carry business rules into the migration as named CHECK constraints, declared at creation time
- Bulk load data using the optimized path on fresh tables
- Add secondary indexes on populated tables without downtime
- Compare query profiles to validate migration success (COLUMN_BASED full scans to ROW_BASED index seeks)
- Perform zero-downtime swaps using ALTER TABLE RENAME

### Migration Decision Summary

| Scenario | Recommendation |
|----------|---------------|
| Point lookups by ID (PK) | Strong HT candidate |
| Mixed read/write with status updates | Strong HT candidate |
| Analytical aggregations, GROUP BY, window functions | Keep as standard table |
| Downstream Streams or Dynamic Tables required | Keep as standard table (or snapshot pattern) |
| Result cache critical for repeated queries | Keep as standard table |
| Low-latency writes + reads, application backend | Strong HT candidate |

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Hybrid Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-hybrid)
- [Creating Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-create)
- [Hybrid Table Limitations](https://docs.snowflake.com/en/user-guide/tables-hybrid-limitations)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test)
- [Getting Started with Hybrid Tables Quickstart](https://www.snowflake.com/en/developers/guides/getting-started-with-hybrid-tables/)
- [Secondary Index Design for Hybrid Tables Quickstart](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)
- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Streaming and Change Detection Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)
- [Data Management and Operations Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)

<!-- ------------------------ -->
## FAQ and Troubleshooting

**Q: Can I add a CHECK constraint after migrating?**

No. `ALTER TABLE ... ADD CONSTRAINT ... CHECK` on a Hybrid Table fails with `001186 (42P16): Unsupported table type for CHECK constraint: Hybrid table`, and `ENABLE NOVALIDATE` does not bypass it. CHECK constraints can only be declared when the table is created, which is why Step 2 asks you to inventory business rules before the migration rather than after. To introduce one later, recreate the table with CTAS from the existing Hybrid Table and swap it in using the same rename pattern as Step 5. This is the opposite of FOREIGN KEY and UNIQUE, which you can add and drop on a populated table at any time.

**Q: My CTAS failed with `001185` and no table was created. What happened?**

A row in the source data violates one of the CHECK constraints you declared. The constraint is validated against the incoming rows, so the whole load is rejected rather than partially applied, and the named constraint in the error message tells you which rule failed. Query the source for violating rows as shown in Step 3, correct them or relax the rule, then re-run the CTAS.

**Q: Can I load a Hybrid Table that has a CHECK constraint using COPY INTO?**

No. `COPY INTO` fails with `001187 (0A000): DML operation COPY INTO not supported for table <name> because it has CHECK constraints`. Load with CTAS as shown in Step 3, or with `INSERT INTO ... SELECT`. If your migration path depends on staged files, land them in a standard table first and then CTAS into the Hybrid Table.

**Q: Can I use CTAS to create a Hybrid Table with a FOREIGN KEY?**

Not in the CTAS statement itself. Declaring a FOREIGN KEY there fails with `391471 (0A000): A foreign key constraint definition in CTAS statements on hybrid tables is not supported.` You have two options. Load the table with CTAS and then add the constraint using `ALTER TABLE ... ADD CONSTRAINT`, which is the route shown in Step 3 and keeps the optimized bulk load path. Or create the table schema explicitly with the FK definition and load it using INSERT INTO ... SELECT. Adding and dropping FOREIGN KEY and UNIQUE constraints on an existing Hybrid Table is generally available, so the first option is usually simpler.

**Q: How long does the bulk load take?**

For an empty Hybrid Table, CTAS and INSERT INTO ... SELECT use an optimized bulk load path. Expect approximately 1 million rows per minute, though this varies with row width and warehouse size. The 500K-row dataset in this quickstart loads in 1-3 minutes on an XSMALL warehouse.

**Q: Will my applications break after the RENAME swap?**

No. ALTER TABLE RENAME changes the table name transparently. Applications using the original name will hit the Hybrid Table without any connection or query changes. Views referencing the table name will also resolve correctly.

**Q: What if the row counts do not match after migration?**

Check for rows that violate the Hybrid Table constraints:
- Rows with NULL in a NOT NULL column
- Rows with duplicate PRIMARY KEY values
- Rows with FOREIGN KEY values that do not exist in the referenced table

These will cause the INSERT or CTAS to fail. Resolve the data quality issues in the standard table before re-running the migration.

If you added the FOREIGN KEY after loading instead of declaring it up front, the row counts will match but the constraint build reports `BUILD VALIDATION FAILURE` in `SHOW INDEXES` rather than failing the load. See **Recovering from a Validation Failure** in Step 3.

**Q: Can I migrate a table with Streams attached?**

Hybrid Tables do not support Streams. If the standard table has a Stream, you must drop it before migrating. For change-tracking use cases, consider a Task-based snapshot pattern: the Hybrid Table serves live OLTP reads/writes, and a scheduled Task snapshots data to a standard table where Streams or Dynamic Tables can be applied.

**Q: Should I create indexes before or after loading data?**

After. When you use CTAS, you can include `INDEX` declarations in the CREATE statement and they will be populated during the load. If you use INSERT INTO ... SELECT on an already-created table, add indexes after the bulk load completes. Creating indexes on a populated table builds them concurrently without blocking reads or writes.

**Q: What about tables larger than a few million rows?**

There is no hard row limit for Hybrid Tables. The bulk load optimization works on fresh tables regardless of size. However, Hybrid Tables are optimized for OLTP access patterns (point lookups, small range scans). If you routinely scan millions of rows for analytics, keep a standard table copy for that purpose and use the Hybrid Table only for operational queries.

**Q: How does this relate to the Secondary Index Design quickstart?**

This guide covers the migration workflow (assess, create, load, swap). The [Secondary Index Design](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/) quickstart goes deeper on index design patterns: composite column ordering, INCLUDE columns for covering indexes, and anti-patterns to avoid. After completing your migration, use that guide to optimize your index strategy.

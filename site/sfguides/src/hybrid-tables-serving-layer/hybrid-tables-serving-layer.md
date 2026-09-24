author: Adam Timm
id: hybrid-tables-serving-layer
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn how to use Hybrid Tables as a low-latency serving layer for email personalization, API backends, and application workloads using the CTAS+SWAP refresh pattern.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, serving layer, reverse ETL, email personalization, API backend, CTAS SWAP, low latency, point lookup, high concurrency, multi-cluster warehouse, compaction, REST API, entitlements, session state, Unistore
related_concepts: CTAS, ALTER TABLE SWAP, CREATE OR REPLACE, compaction, plan cache, bound variables, multi-cluster warehouse, connection pooling
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-write-optimization, hybrid-tables-application-connectors
skill_level: intermediate
estimated_time_minutes: 40
snowflake_features: hybrid_tables, ctas, multi_cluster_warehouse, secondary_indexes
-->

# Serving Low-Latency Data with Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note on Production Workloads:** Production serving workloads should use bound variables (parameterized queries), private key authentication, and connection pooling. See [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices) and [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/).

Many data teams maintain expensive reverse ETL pipelines that extract data from Snowflake, transform it, and push it to external systems (Redis, DynamoDB, S3 JSON files) for low-latency serving. Hybrid Tables can eliminate this intermediate layer entirely by serving data directly from Snowflake at double-digit millisecond latency.

This quickstart covers two common serving scenarios:

1. **Email/Marketing Personalization** — precompute recommendations in a standard table, bulk-load into a Hybrid Table, serve to a downstream application or service at high concurrency
2. **API Backend** — use a Hybrid Table as the backing store for a REST API serving entitlements, session state, or configuration data via primary key lookups

Both scenarios use the same core pattern: **compute in columnar, serve from row store**.

### Why Not Just Use a Standard Table?

Standard Snowflake tables are optimized for analytical workloads. They provide excellent throughput for large scans but cannot deliver consistent double-digit millisecond latency for point lookups because:

- **Result cache** helps only for identical repeated queries (not per-user lookups)
- **No row-level index** means every point lookup scans micro-partitions
- **Latency variability** is high (varies widely depending on cache state and partition layout)

Hybrid Tables provide deterministic low latency for point lookups via the primary key index and secondary indexes stored in the row store.

### What You Will Learn

- How to design a Hybrid Table specifically for serving (schema, PK, indexes)
- How to enforce the serving contract with `CHECK` constraints, and why a CTAS+SWAP refresh can silently remove them
- The CTAS+SWAP pattern for atomic bulk refresh without downtime
- Why reads spike after a CTAS and how to mitigate the warm-up window
- How to size warehouses for high-concurrency serving workloads
- How to make a multi-statement entitlement change atomic with an Inline Stored Procedure, and when not to use one
- Two complete worked scenarios with DDL, data generation, and query patterns

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Familiarity with Hybrid Tables and [secondary indexes](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)
- Understanding of bound variables and plan cache (see [Write Optimization](https://www.snowflake.com/en/developers/guides/hybrid-tables-write-optimization/) guide)

<!-- ------------------------ -->
## Setup

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROLE HT_SERVE_QS_ROLE;
GRANT ROLE HT_SERVE_QS_ROLE TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE HT_SERVE_QS_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  MAX_CLUSTER_COUNT = 3
  SCALING_POLICY = 'STANDARD';
GRANT OWNERSHIP ON WAREHOUSE HT_SERVE_QS_WH TO ROLE HT_SERVE_QS_ROLE;

CREATE OR REPLACE DATABASE HT_SERVE_QS_DB;
GRANT OWNERSHIP ON DATABASE HT_SERVE_QS_DB TO ROLE HT_SERVE_QS_ROLE;

USE ROLE HT_SERVE_QS_ROLE;
CREATE OR REPLACE SCHEMA HT_SERVE_QS_DB.DATA;
USE WAREHOUSE HT_SERVE_QS_WH;
USE DATABASE HT_SERVE_QS_DB;
USE SCHEMA DATA;
```

> **Note:** The warehouse uses `MAX_CLUSTER_COUNT = 3` and `SCALING_POLICY = 'STANDARD'`. For serving workloads with high concurrency, multi-cluster warehouses scale horizontally to handle burst traffic without queuing.

<!-- ------------------------ -->
## Step 1: The Reverse ETL Problem

A typical reverse ETL pipeline for serving personalized data looks like this:

```
[Snowflake Standard Table]
    → ETL/Transform (Python, dbt, Airflow)
    → Export (COPY INTO S3 / API push)
    → External Cache (Redis, DynamoDB, S3 JSON)
    → Application reads from cache
```

This architecture introduces:
- **Staleness** — data is only as fresh as the last export cycle (often minutes to hours)
- **Operational complexity** — multiple systems to monitor, debug, and maintain
- **Cost** — compute for export, storage for cache, egress fees, cache infrastructure
- **Brittleness** — any failure in the chain breaks the serving path

The Hybrid Table serving pattern collapses this to:

```
[Snowflake Standard Table]
    → Task (CTAS+SWAP into Hybrid Table)
    → Application reads directly from Snowflake
```

One system. One copy. Deterministic freshness. No external cache.

<!-- ------------------------ -->
## Scenario 1: Email/Marketing Personalization

### The Use Case

A personalization engine scores users against content several times per day, producing millions of ranked recommendations. A downstream application or service needs to look up the top N recommendations for each user on demand, at high concurrency during peak traffic.

### Design the Serving Table

The serving table is designed for one access pattern: lookup by user_id, return their ranked recommendations.

```sql
CREATE OR REPLACE HYBRID TABLE user_recommendations (
    user_id         NUMBER       NOT NULL,
    content_id      NUMBER       NOT NULL,
    rank            NUMBER       NOT NULL,
    score           FLOAT        NOT NULL,
    content_title   VARCHAR(500),
    content_url     VARCHAR(2000),
    computed_at     TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (user_id, content_id),
    CONSTRAINT chk_rank_positive CHECK (rank > 0),
    CONSTRAINT chk_score_range   CHECK (score > 0 AND score <= 1)
);
```

The composite primary key `(user_id, content_id)` enables:
- Fast seek to all recommendations for a specific user
- Deduplication (same user+content pair cannot appear twice)
- Ordered retrieval within a user (PK is sorted by user_id first)

The two `CHECK` constraints encode what the scoring pipeline is supposed to produce: ranks start at
1, and scores are normalized to the interval `(0, 1]`. A serving table is read by applications that
trust its shape, so it is worth rejecting a malformed pipeline output at write time rather than
discovering it in production traffic.

> **Note:** On a hybrid table, a `CHECK` constraint must be declared when the table is created. You
> cannot add one later with `ALTER TABLE`. That constrains how you refresh this table, which the
> CTAS+SWAP section below covers.

### Create the Source Table (Simulates Scoring Pipeline Output)

```sql
CREATE OR REPLACE TABLE recommendations_source AS
SELECT
    user_id,
    content_id,
    rank,
    score,
    content_title,
    content_url,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS computed_at
FROM (
    SELECT
        u.user_id,
        c.content_id,
        ROW_NUMBER() OVER (PARTITION BY u.user_id ORDER BY RANDOM()) AS rank,
        ROUND(UNIFORM(0.01, 1.00, RANDOM()), 4) AS score,
        'Article ' || c.content_id::VARCHAR AS content_title,
        'https://example.com/content/' || c.content_id::VARCHAR AS content_url
    FROM
        (SELECT SEQ4() + 1 AS user_id FROM TABLE(GENERATOR(ROWCOUNT => 10000))) u
    CROSS JOIN
        (SELECT SEQ4() + 1 AS content_id FROM TABLE(GENERATOR(ROWCOUNT => 20))) c
)
WHERE rank <= 10;

SELECT COUNT(*) FROM recommendations_source;
-- Expected: 100000 (10,000 users x 10 recommendations each)
```

### Initial Load via CTAS

```sql
CREATE OR REPLACE HYBRID TABLE user_recommendations (
    user_id         NUMBER       NOT NULL,
    content_id      NUMBER       NOT NULL,
    rank            NUMBER       NOT NULL,
    score           FLOAT        NOT NULL,
    content_title   VARCHAR(500),
    content_url     VARCHAR(2000),
    computed_at     TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (user_id, content_id),
    CONSTRAINT chk_rank_positive CHECK (rank > 0),
    CONSTRAINT chk_score_range   CHECK (score > 0 AND score <= 1)
)
AS SELECT * FROM recommendations_source;
```

The `CHECK` constraints are validated against the incoming rows, so a CTAS load is also a
validation pass over whatever the scoring pipeline produced. If the source contains a rank of `0`,
the load fails rather than publishing bad data:

```
001185 (23514): Operation on table USER_RECOMMENDATIONS failed because CHECK
constraint CHK_RANK_POSITIVE, which requires that rank > 0, was violated
```

Because `CREATE OR REPLACE` is atomic, a failed load leaves the previous table and its rows intact.

### Serve: Lookup Recommendations for a User

```sql
SET TARGET_USER = (SELECT user_id FROM user_recommendations LIMIT 1);

SELECT content_id, rank, score, content_title, content_url
FROM user_recommendations
WHERE user_id = $TARGET_USER
ORDER BY rank;
```

Query Profile: `TableScan`, `ROW_BASED`, ~10 rows scanned (the user's recommendations). This is the query your email platform executes 20,000+ times per second during a send.

### Refresh: The CTAS+SWAP Pattern

When the scoring pipeline produces new recommendations, atomically replace the serving table:

```sql
-- Step 1: Build the new version (CTAS into a temporary name)
CREATE OR REPLACE HYBRID TABLE user_recommendations_new (
    user_id         NUMBER       NOT NULL,
    content_id      NUMBER       NOT NULL,
    rank            NUMBER       NOT NULL,
    score           FLOAT        NOT NULL,
    content_title   VARCHAR(500),
    content_url     VARCHAR(2000),
    computed_at     TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (user_id, content_id),
    CONSTRAINT chk_rank_positive CHECK (rank > 0),
    CONSTRAINT chk_score_range   CHECK (score > 0 AND score <= 1)
)
AS SELECT * FROM recommendations_source;

-- Step 2: Atomic swap (applications see no interruption)
ALTER TABLE user_recommendations SWAP WITH user_recommendations_new;

-- Step 3: Drop the old version (now in the _new name)
DROP TABLE user_recommendations_new;
```

### The Swap Carries Constraints With It

Repeat the `CHECK` constraints on **every** table you swap in. `SWAP WITH` exchanges the two tables'
constraints along with their data, and it does not require them to match. If the replacement table
omits them, the swap still succeeds and your live serving table comes out the other side with no
`CHECK` constraints at all.

That failure is silent. Nothing errors, and the next step drops the table that is now holding your
constraints:

```sql
-- What NOT to do: build the replacement without the constraints
CREATE OR REPLACE HYBRID TABLE user_recommendations_new (
    user_id NUMBER NOT NULL, content_id NUMBER NOT NULL,
    rank NUMBER NOT NULL, score FLOAT NOT NULL,
    content_title VARCHAR(500), content_url VARCHAR(2000),
    computed_at TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (user_id, content_id)
)
AS SELECT * FROM recommendations_source;

ALTER TABLE user_recommendations SWAP WITH user_recommendations_new;
```

After that swap, inspect what the serving table actually has:

```sql
SELECT GET_DDL('TABLE', 'user_recommendations');
```

The `CHECK` constraints are gone, and a row the pipeline should never produce is now accepted:

```sql
INSERT INTO user_recommendations
VALUES (999999, 1, 0, 0.5, 'bad', 'bad', CURRENT_TIMESTAMP()::TIMESTAMP_NTZ);
-- Succeeds, because rank > 0 is no longer enforced
```

Since a hybrid table's `CHECK` constraints can only be declared at creation time, you cannot repair
this with `ALTER TABLE` afterward. The only fix is another CTAS+SWAP using a correctly constrained
replacement table. Do that now, both to restore the constraints and to clear the invalid row:

```sql
DROP TABLE user_recommendations_new;

DELETE FROM user_recommendations WHERE rank <= 0;

CREATE OR REPLACE HYBRID TABLE user_recommendations_new (
    user_id         NUMBER       NOT NULL,
    content_id      NUMBER       NOT NULL,
    rank            NUMBER       NOT NULL,
    score           FLOAT        NOT NULL,
    content_title   VARCHAR(500),
    content_url     VARCHAR(2000),
    computed_at     TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (user_id, content_id),
    CONSTRAINT chk_rank_positive CHECK (rank > 0),
    CONSTRAINT chk_score_range   CHECK (score > 0 AND score <= 1)
)
AS SELECT * FROM user_recommendations;

ALTER TABLE user_recommendations SWAP WITH user_recommendations_new;
DROP TABLE user_recommendations_new;

SELECT GET_DDL('TABLE', 'user_recommendations');
-- The CHECK constraints are back
```

Note that the repair CTAS selects from the live table, so it also revalidates the rows already
there. Deleting the invalid row first is what allows that load to succeed.

> **Note:** Treat the replacement table's DDL as part of the serving contract, not as scratch. Any
> place that builds it — an ad hoc refresh, the scheduled task below, a CI job — must carry the same
> constraints, or the first refresh through that path quietly removes them.

> **Why SWAP instead of RENAME?** `ALTER TABLE ... SWAP WITH` exchanges the contents of two tables atomically in a single metadata operation. Applications querying `user_recommendations` see the new data immediately after the swap with zero downtime. `RENAME` requires two statements (rename old, rename new) which creates a brief window where the table name does not exist.

### Refresh Task (Scheduled)

```sql
CREATE OR REPLACE TASK refresh_user_recommendations
  WAREHOUSE = HT_SERVE_QS_WH
  SCHEDULE = 'USING CRON 0 */4 * * * UTC'
AS
BEGIN
  CREATE OR REPLACE HYBRID TABLE user_recommendations_new (
    user_id NUMBER NOT NULL, content_id NUMBER NOT NULL,
    rank NUMBER NOT NULL, score FLOAT NOT NULL,
    content_title VARCHAR(500), content_url VARCHAR(2000),
    computed_at TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (user_id, content_id),
    CONSTRAINT chk_rank_positive CHECK (rank > 0),
    CONSTRAINT chk_score_range   CHECK (score > 0 AND score <= 1)
  )
  AS SELECT * FROM recommendations_source;

  ALTER TABLE user_recommendations SWAP WITH user_recommendations_new;
  DROP TABLE user_recommendations_new;
END;
```

This is the path that runs unattended every four hours, so it is the most important place to keep
the constraints in sync. A task body missing them would strip the serving table on its next run,
with nothing in the task history to indicate that anything changed.

<!-- ------------------------ -->
## Scenario 2: API Backend (Entitlements/Session State)

### The Use Case

A REST API serves authorization decisions: given a user_id, return their entitlements (which portfolios, products, or resources they can access). The API needs double-digit millisecond responses at thousands of concurrent requests from multiple microservices.

### Design the Serving Table

```sql
CREATE OR REPLACE HYBRID TABLE user_entitlements (
    user_id         VARCHAR(100)  NOT NULL,
    resource_type   VARCHAR(50)   NOT NULL,
    resource_id     VARCHAR(200)  NOT NULL,
    access_level    VARCHAR(20)   NOT NULL,
    granted_at      TIMESTAMP_NTZ NOT NULL,
    expires_at      TIMESTAMP_NTZ,
    PRIMARY KEY (user_id, resource_type, resource_id),
    CONSTRAINT chk_expires_after_granted
      CHECK (expires_at IS NULL OR expires_at > granted_at)
);
```

The composite PK enables:
- Lookup all entitlements for a user: `WHERE user_id = ?`
- Lookup specific resource access: `WHERE user_id = ? AND resource_type = ? AND resource_id = ?`
- Both use the PK prefix seek (no secondary index needed)

The `CHECK` constraint enforces date ordering: an entitlement either never expires (`NULL`) or
expires after it was granted. An entitlement whose window is inverted would be invisible to every
access check that filters on `expires_at`, which is a difficult bug to notice from the application
side. A `NULL` `expires_at` still passes, so the constraint does not accidentally require an
expiration date.

### Load Sample Data

```sql
INSERT INTO user_entitlements
SELECT
    'user_' || u.id::VARCHAR AS user_id,
    ARRAY_CONSTRUCT('PORTFOLIO','REPORT','DASHBOARD','API_ENDPOINT')
        [UNIFORM(0,3,RANDOM())]::VARCHAR AS resource_type,
    'resource_' || UNIFORM(1, 500, RANDOM())::VARCHAR AS resource_id,
    ARRAY_CONSTRUCT('READ','WRITE','ADMIN')[UNIFORM(0,2,RANDOM())]::VARCHAR AS access_level,
    DATEADD(DAY, -UNIFORM(1,365,RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS granted_at,
    DATEADD(DAY, UNIFORM(30,365,RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS expires_at
FROM (SELECT SEQ4() + 1 AS id FROM TABLE(GENERATOR(ROWCOUNT => 50000))) u;
```

### API Query Patterns

**Check if user has access to a specific resource:**

```sql
SET API_USER = 'user_42';
SET API_RESOURCE_TYPE = 'PORTFOLIO';
SET API_RESOURCE_ID = 'resource_100';

SELECT access_level
FROM user_entitlements
WHERE user_id = $API_USER
  AND resource_type = $API_RESOURCE_TYPE
  AND resource_id = $API_RESOURCE_ID
  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP()::TIMESTAMP_NTZ);
```

Query Profile: `TableScan`, `ROW_BASED`, 1 row scanned. Low double-digit millisecond execution time.

**Get all active entitlements for a user:**

```sql
SELECT resource_type, resource_id, access_level, expires_at
FROM user_entitlements
WHERE user_id = $API_USER
  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP()::TIMESTAMP_NTZ)
ORDER BY resource_type;
```

Query Profile: `TableScan`, `ROW_BASED`, ~10-50 rows scanned (that user's entitlements).

### Incremental Updates (No CTAS+SWAP Needed)

Unlike the email scenario (bulk refresh), entitlement changes are incremental. Use direct DML:

```sql
-- Grant new access
INSERT INTO user_entitlements VALUES (
    'user_42', 'DASHBOARD', 'resource_999', 'READ',
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    DATEADD(DAY, 90, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
);

-- Revoke access (delete)
DELETE FROM user_entitlements
WHERE user_id = 'user_42' AND resource_type = 'DASHBOARD' AND resource_id = 'resource_999';
```

For the bulk sync, first stand up a source table representing what the upstream system sent. Keep
`expires_at` after `granted_at` so the merged rows satisfy the serving table's `CHECK` constraint:

```sql
CREATE OR REPLACE TABLE entitlements_source AS
SELECT 'user_' || u.id::VARCHAR                        AS user_id,
       'DASHBOARD'                                     AS resource_type,
       'resource_' || UNIFORM(1, 500, RANDOM())::VARCHAR AS resource_id,
       ARRAY_CONSTRUCT('READ','WRITE','ADMIN')
           [UNIFORM(0, 2, RANDOM())]::VARCHAR          AS access_level,
       CURRENT_TIMESTAMP()::TIMESTAMP_NTZ              AS granted_at,
       DATEADD(DAY, UNIFORM(30, 365, RANDOM()),
               CURRENT_TIMESTAMP())::TIMESTAMP_NTZ     AS expires_at
FROM (SELECT SEQ4() + 1 AS id FROM TABLE(GENERATOR(ROWCOUNT => 1000))) u;
```

```sql
-- Bulk sync from source system (MERGE)
MERGE INTO user_entitlements AS tgt
USING entitlements_source AS src
ON tgt.user_id = src.user_id
  AND tgt.resource_type = src.resource_type
  AND tgt.resource_id = src.resource_id
WHEN MATCHED THEN UPDATE SET
  tgt.access_level = src.access_level,
  tgt.expires_at = src.expires_at
WHEN NOT MATCHED THEN INSERT VALUES (
  src.user_id, src.resource_type, src.resource_id,
  src.access_level, src.granted_at, src.expires_at
);
```

### Optional: Change an Entitlement and Audit It Atomically

An entitlement change is often two writes: update the grant, and record who changed what. If the
second write fails, you do not want the first to stand. An
[Inline Stored Procedure](https://docs.snowflake.com/en/user-guide/hybrid-tables-inline-stored-procedures)
runs its body as a single atomic transaction, so the pair either both apply or neither does.

Start with an audit table. This one enforces the access-level vocabulary, which the entitlements
table deliberately does not:

```sql
CREATE OR REPLACE HYBRID TABLE entitlement_audit (
    audit_id      NUMBER        NOT NULL AUTOINCREMENT START 1 INCREMENT 1 ORDER,
    user_id       VARCHAR(100)  NOT NULL,
    resource_type VARCHAR(50)   NOT NULL,
    resource_id   VARCHAR(200)  NOT NULL,
    new_access    VARCHAR(20)   NOT NULL,
    changed_at    TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (audit_id),
    CONSTRAINT chk_audit_access CHECK (new_access IN ('READ','WRITE','ADMIN'))
);
```

```sql
CREATE OR REPLACE INLINE PROCEDURE change_entitlement(
    p_user_id       VARCHAR,
    p_resource_type VARCHAR,
    p_resource_id   VARCHAR,
    p_new_access    VARCHAR,
    p_changed_at    TIMESTAMP_NTZ
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN ATOMIC
    UPDATE user_entitlements
       SET access_level = :p_new_access
     WHERE user_id       = :p_user_id
       AND resource_type = :p_resource_type
       AND resource_id   = :p_resource_id;

    INSERT INTO entitlement_audit
        (user_id, resource_type, resource_id, new_access, changed_at)
    VALUES (:p_user_id, :p_resource_type, :p_resource_id, :p_new_access, :p_changed_at);

    RETURN 'ok';
END;
$$;
```

Two details are worth noting before you call it:

- The timestamp is a parameter. `CURRENT_TIMESTAMP()` is not available inside an Inline Stored
  Procedure, so any value the statements need must come from the caller.
- Bind variables appear bare in the `VALUES` clause and are prefixed with a colon when referenced.
  An Inline Stored Procedure cannot use `INSERT ... SELECT` with bind variables, so a fixed set of
  parameters per call is the shape to aim for.

Pick a real row and make a valid change:

```sql
SET E_USER = (SELECT MIN(user_id) FROM user_entitlements);
SET E_TYPE = (SELECT MIN(resource_type) FROM user_entitlements WHERE user_id = $E_USER);
SET E_RID  = (SELECT MIN(resource_id) FROM user_entitlements
              WHERE user_id = $E_USER AND resource_type = $E_TYPE);

CALL change_entitlement($E_USER, $E_TYPE, $E_RID, 'ADMIN',
                        CURRENT_TIMESTAMP()::TIMESTAMP_NTZ);

SELECT access_level FROM user_entitlements
 WHERE user_id = $E_USER AND resource_type = $E_TYPE AND resource_id = $E_RID;
SELECT COUNT(*) FROM entitlement_audit;
```

Both writes are visible: the grant is now `ADMIN` and the audit table has one row.

#### Seeing the Whole Change Roll Back

Now call it with an access level the audit table rejects. The `UPDATE` runs first and applies, then
the audit `INSERT` violates `chk_audit_access`:

```sql
CALL change_entitlement($E_USER, $E_TYPE, $E_RID, 'SUPERUSER',
                        CURRENT_TIMESTAMP()::TIMESTAMP_NTZ);
```

```
001185 (23514): Uncaught exception of type 'STATEMENT_ERROR' on line 9 at position 4 :
Operation on table ENTITLEMENT_AUDIT failed because CHECK constraint
CHK_AUDIT_ACCESS, which requires that new_access IN ('READ','WRITE','ADMIN'),
was violated
```

Confirm that the update was undone rather than left half-applied:

```sql
SELECT access_level FROM user_entitlements
 WHERE user_id = $E_USER AND resource_type = $E_TYPE AND resource_id = $E_RID;
-- Still ADMIN: the SUPERUSER update was rolled back

SELECT COUNT(*) FROM user_entitlements WHERE access_level = 'SUPERUSER';
-- 0

SELECT COUNT(*) FROM entitlement_audit;
-- Still 1: no audit row was written either
```

This is the property the procedure buys you. The same two statements sent separately by an
application would have left the grant changed with no audit record.

> **Note:** An Inline Stored Procedure must be called with autocommit enabled; it cannot run inside
> an open transaction. It also cannot contain DDL or explicit transaction control, and every table
> it touches must be a hybrid table in the same database.

#### Where Not to Use One

Leave the Scenario 1 refresh alone. The CTAS+SWAP workflow is DDL against a standard source table,
which an Inline Stored Procedure cannot do, and wrapping bulk refresh in a procedure would gain
nothing even if it could — `CREATE OR REPLACE` and `SWAP WITH` are already atomic on their own.
Reserve Inline Stored Procedures for small, bounded, multi-statement writes like the one above.

There is also a performance trade-off worth knowing. Statements executed inside a stored procedure
are not eligible for the
[operational query performance optimizations](https://docs.snowflake.com/en/user-guide/hybrid-tables-operational-query-performance)
that repeated parameterized queries benefit from. For a low-volume administrative write like an
entitlement change that is the right trade — atomicity matters more than latency. For the
high-volume read path in *API Query Patterns* above, keep the queries outside procedures so they
remain eligible.

<!-- ------------------------ -->
## Step 2: Managing the Compaction Window

After a CTAS+SWAP, the new table must warm up — plan cache, warehouse data cache, and row store layout all need to reach steady state. During this window (typically 1-5 minutes for tables under 1M rows), read latency may be elevated.

### Why Latency Spikes After a Refresh

After a CTAS+SWAP, the new table has no cached query plans or warm data in the warehouse. The first queries against the new table incur plan compilation and data loading overhead. This warm-up period is transparent to the application but can temporarily increase read latency until steady state is reached.

### Mitigation Strategies

**1. Schedule refreshes during low-traffic windows:**

```sql
-- Refresh at 2 AM when traffic is low
CREATE OR REPLACE TASK refresh_user_recommendations
  WAREHOUSE = HT_SERVE_QS_WH
  SCHEDULE = 'USING CRON 0 2 * * * UTC'
AS
BEGIN
  CREATE OR REPLACE HYBRID TABLE user_recommendations_new (...)
  AS SELECT * FROM recommendations_source;
  ALTER TABLE user_recommendations SWAP WITH user_recommendations_new;
  DROP TABLE user_recommendations_new;
END;
```

**2. Pre-warm after swap:**

Run a representative query immediately after the swap to trigger warehouse cache loading:

```sql
-- Add to the refresh task after the SWAP
SELECT COUNT(*) FROM user_recommendations WHERE user_id = 1;
```

**3. Size the serving warehouse to absorb the warm-up spike:**

A multi-cluster warehouse absorbs the temporary latency increase by routing new requests to idle clusters while the new table reaches steady state.

<!-- ------------------------ -->
## Step 3: Warehouse Sizing for High-Concurrency Serving

Hybrid Table serving workloads have different requirements than analytical workloads:

- **Concurrency over throughput** — thousands of small queries, not a few large ones
- **Latency over cost** — the goal is consistent double-digit millisecond latency, not maximum rows-per-credit
- **Horizontal scaling** — more clusters, not bigger clusters

### Recommended Configuration

```sql
-- For serving workloads: small size, multiple clusters, standard scaling
ALTER WAREHOUSE HT_SERVE_QS_WH SET
  WAREHOUSE_SIZE = 'XSMALL'
  MAX_CLUSTER_COUNT = 5
  MIN_CLUSTER_COUNT = 1
  SCALING_POLICY = 'STANDARD';
```

| Parameter | Recommendation | Why |
|-----------|---------------|-----|
| WAREHOUSE_SIZE | XSMALL or SMALL | Point lookups need minimal compute; start with XS and benchmark |
| MAX_CLUSTER_COUNT | 3-10 (based on peak concurrency) | Horizontal scaling for burst traffic |
| MIN_CLUSTER_COUNT | 1-2 | Keep 1-2 clusters warm to avoid cold-start latency |
| SCALING_POLICY | STANDARD | Scales up aggressively; scales down conservatively (fewer cold restarts) |
| AUTO_SUSPEND | 300-600 | Long enough to avoid suspend/resume during traffic dips |

### Why XSMALL?

Each HT point lookup consumes minimal compute. An XS cluster is typically sufficient for many operational serving workloads. Benchmark your specific query patterns to determine throughput per cluster, then scale horizontally by adding more clusters (not larger size). Larger warehouse sizes add compute power you do not need for point lookups and increase cost without reducing latency.

### When to Go Bigger

Increase warehouse size only if your serving queries involve:
- Joining the HT with another table (e.g., enrichment at query time)
- Scanning more than ~100 rows per query
- Running post-read transformations (JSON parsing, UDFs)

<!-- ------------------------ -->
## Serving Design Checklist

Before deploying a Hybrid Table as a serving layer, validate these requirements:

| Check | Email/Marketing | API Backend |
|-------|----------------|-------------|
| Access pattern | Lookup by user_id (PK prefix) | Lookup by composite key |
| Refresh frequency | Periodic (4-24 hours) | Incremental (real-time DML) |
| Refresh method | CTAS+SWAP (atomic bulk replace) | Direct INSERT/UPDATE/DELETE/MERGE |
| Concurrency target | 10K-50K QPS (campaign blasts) | 1K-10K QPS (steady API traffic) |
| Warehouse | XS, MAX_CLUSTER_COUNT=5-10 | XS, MAX_CLUSTER_COUNT=3-5 |
| Driver | REST API or SDK with pooling | JDBC/Python with HikariCP/SQLAlchemy pool |
| Bound variables | Required (plan cache) | Required (plan cache) |
| Warm-up concern | Yes (schedule refresh in low-traffic window) | No (incremental writes) |

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your own workload:

> "I need to serve precomputed results from my analytical pipeline to a low-latency API. Design a serving layer using a Hybrid Table as the target. My source Standard Table schema is: [paste DDL]."

> "Generate the Task SQL to snapshot my aggregated results into a Hybrid Table serving layer on an hourly schedule. My aggregation query is: [paste query]."

> "My serving layer Hybrid Table is returning slow results on secondary index lookups. Review my DDL and query patterns and recommend index optimizations: [paste DDL and queries]."

<!-- ------------------------ -->
## Cleanup

```sql
ALTER TASK IF EXISTS refresh_user_recommendations SUSPEND;
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS HT_SERVE_QS_DB;
DROP WAREHOUSE IF EXISTS HT_SERVE_QS_WH;
DROP ROLE IF EXISTS HT_SERVE_QS_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now:

- Replace reverse ETL pipelines with Hybrid Tables as a serving layer
- Design serving tables with composite primary keys for efficient point lookups
- Enforce a serving contract with `CHECK` constraints, and keep them intact across a CTAS+SWAP refresh
- Use CTAS+SWAP for atomic bulk refresh with zero application downtime
- Manage warm-up windows by scheduling refreshes during low-traffic periods
- Size multi-cluster warehouses for high-concurrency serving (XS + horizontal scaling)

### When to Use This Pattern vs External Cache

| Use Hybrid Table Serving | Keep External Cache (Redis/DynamoDB) |
|--------------------------|--------------------------------------|
| Latency target: double-digit ms | Latency target: <1ms |
| Data already in Snowflake | Data originates outside Snowflake |
| Want to eliminate pipeline complexity | Cache invalidation is simple for your use case |
| Refresh frequency: minutes to hours | Refresh frequency: sub-second |
| Concurrency: up to ~50K QPS | Concurrency: >100K QPS sustained |
| Data consistency matters (single source of truth) | Eventual consistency acceptable |

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test)
- [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)
- [Optimizing Writes to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-write-optimization/)
- [Secondary Index Design for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)
- [Converting Standard Tables to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-standard-to-hybrid-migration/)

<!-- ------------------------ -->
## FAQ

**Q: How does this compare to Snowflake's result cache?**

Hybrid Tables do not use the result cache. Every query against a Hybrid Table executes fresh — there is no cached result to return regardless of query text. This is by design: HT data changes frequently via DML, so cached results would be stale.

**Q: What if my serving table has 100 million rows?**

Hybrid Tables handle this well for point lookups. The PK index scales logarithmically — a PK lookup on 100M rows is nearly the same latency as on 1M rows. CTAS+SWAP bulk refresh will take longer (10-30 minutes on 100M rows), so schedule appropriately and consider the compaction window.

**Q: Can I serve from multiple Hybrid Tables in a single API call?**

Yes — JOIN two Hybrid Tables in a single query. If both sides use PK or FK joins, the query plan uses nested loop joins with row-based access on both sides. For best results, ensure the JOIN key matches a PK or has a foreign key relationship defined.

**Q: What about connection limits?**

Each Snowflake warehouse cluster handles connections independently. With MAX_CLUSTER_COUNT=5 on an XS, you have 5 independent clusters handling requests in parallel. Connection pooling at the application layer (HikariCP, SQLAlchemy) prevents exhausting connections per cluster.

**Q: Can I use ALTER TABLE SWAP WITH for tables with different schemas?**

No. Both tables must have identical column definitions (names, types, constraints). The SWAP operation exchanges only the data; the schema must already match.

**Q: What happens to in-flight queries during a SWAP?**

SWAP is a metadata operation. Queries that started before the SWAP read the old data. Queries that start after the SWAP read the new data. There is no interruption or error for either set.

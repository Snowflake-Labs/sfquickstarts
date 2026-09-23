author: Adam Timm
id: hybrid-tables-application-connectors
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/hybrid-tables
language: en
summary: Learn how to connect applications to Snowflake Hybrid Tables using JDBC, Python, Node.js, and Snowpark with bound variables, connection pooling, Inline Stored Procedures, and Kafka ingest patterns.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, JDBC, Python connector, Node.js, Snowpark, Spring Boot, Kafka, connection pool, HikariCP, bound variables, prepared statements, private key auth, batch insert, executemany, inline stored procedures, CALL, atomic block, OLTP, application development
related_concepts: plan cache, query compilation, bound parameters, autocommit, connection pooling, private key JWT auth, Kafka consumer, micro-batch, executeBatch, inline stored procedures, atomic execution, exception handling
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-secondary-index-design
skill_level: intermediate
estimated_time_minutes: 45
snowflake_features: hybrid_tables, jdbc_driver, python_connector, nodejs_driver, snowpark, inline_stored_procedures
-->

# Connecting Applications to Hybrid Tables
<!-- ------------------------ -->
## Overview

> **Note:** Driver-based connections are the only way to achieve the lowest possible latency with Hybrid Tables. Snowsight adds overhead that is not representative of production performance. Always benchmark using your application driver.

Hybrid Tables are designed for application workloads: high-concurrency point reads and writes issued by application backends, microservices, and event-driven pipelines. Getting the most out of Hybrid Tables requires using connectors correctly — with bound variables, connection pooling, and batch patterns tuned for OLTP throughput.

This quickstart covers the four primary connector patterns for Hybrid Table workloads:

- **JDBC / Spring Boot** — including a Kafka micro-batch ingest pattern
- **Python Connector** — `executemany` with bound parameters
- **Node.js** — array binding and connection pools
- **Snowpark** — when to use `session.sql()` vs the DataFrame API

It also covers calling **Inline Stored Procedures** from each driver, for multi-statement units of work that must be atomic.

### Why Connector Choice and Configuration Matter

The single most impactful configuration decision for Hybrid Table performance is whether you use **bound variables (parameterized queries)**. When you use bound variables, Snowflake compiles the query plan once and reuses it across all executions with different parameter values. When you use string literals, Snowflake compiles a new plan for every query — adding 10-100ms of compilation overhead to every request.

For a Hybrid Table workload executing 1,000 queries per second, this difference is the line between millisecond latency and second latency.

### What You Will Learn

- Minimum driver versions required for Hybrid Table support
- How to configure private key authentication for service accounts
- How to set up connection pools correctly (and avoid stale connection errors)
- How to use bound variables for plan cache reuse in each driver
- How to batch insert rows efficiently without row-by-row overhead
- How to call an Inline Stored Procedure with bound parameters, read its result, and handle its errors
- The Kafka → Spring Boot → Hybrid Table ingest pattern
- Anti-patterns to avoid: string literals, oversized pools, single-row loops

### Prerequisites

- A Snowflake paid account in an AWS or Azure commercial region
- Familiarity with at least one of: Java/Spring Boot, Python, or Node.js
- A Hybrid Table to connect to (see [Getting Started with Hybrid Tables](https://www.snowflake.com/en/developers/guides/getting-started-with-hybrid-tables/))
- An RSA key pair for private key authentication (recommended)

### Minimum Driver Versions

Hybrid Tables require minimum driver versions. Always use the **latest available version** for best performance:

| Driver | Minimum Version |
|--------|----------------|
| JDBC | 3.13.31 |
| Python Connector | 3.1.0 |
| Node.js | 1.9.0 |
| ODBC | 3.0.2 |
| Go | 1.6.25 |
| .NET | 2.1.2 |

<!-- ------------------------ -->
## Setup: Create the Demo Table

All connector examples in this guide write to and read from the same Hybrid Table. Run this SQL in Snowsight to create it:

```sql
CREATE OR REPLACE HYBRID TABLE orders (
    order_id     NUMBER        NOT NULL,
    customer_id  NUMBER        NOT NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    region       VARCHAR(10)   NOT NULL,
    amount       NUMBER(12,2)  NOT NULL,
    created_at   TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (order_id),
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_status_region (status, region)
);
```

Each connector section inserts rows into this table using its native batch and binding API.

<!-- ------------------------ -->
## Step 1: Connection Best Practices

These practices apply to every driver. Implement all of them before tuning anything else.

### Use Private Key Authentication

Private key (JWT) authentication is recommended for service accounts and application backends. It eliminates password rotation, MFA prompts, and credential exposure in config files.

```sql
-- Create a dedicated service user (run as ACCOUNTADMIN)
CREATE USER ht_app_user
  RSA_PUBLIC_KEY = '<paste_public_key_here>'
  DEFAULT_ROLE = <your_role>
  DEFAULT_WAREHOUSE = <your_warehouse>
  MUST_CHANGE_PASSWORD = FALSE;
```

Generate the RSA key pair:
```bash
openssl genrsa -out rsa_key.pem 2048
openssl pkcs8 -topk8 -inform PEM -in rsa_key.pem -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.pem -pubout -out rsa_key_pub.pem
```

### Use Connection Pooling with Long-Lived Connections

Establishing a new Snowflake connection takes 100-500ms due to authentication and session setup. For OLTP workloads, this overhead is unacceptable on every query. Connection pools keep connections warm and reuse them across requests.

Key rules:
- Size the pool to match your application's concurrency (not too large — each connection uses warehouse resources)
- Set a maximum lifetime to prevent stale connections
- Test connections before issuing them to catch network interruptions

### Keep AUTOCOMMIT Enabled

`AUTOCOMMIT = TRUE` (the default) is the correct setting for Hybrid Table OLTP workloads. Each DML statement is its own atomic transaction. Standard stored procedure wrappers add overhead. Use explicit `BEGIN`/`COMMIT` only when you need multi-statement atomicity, or an Inline Stored Procedure for a multi-statement unit of work against Hybrid Tables (see Step 6).

> **Note:** Inline Stored Procedures cannot be invoked from inside an open transaction — they must be called with autocommit enabled. If you plan to call them, keeping `AUTOCOMMIT = TRUE` is a requirement rather than only a recommendation.

### Colocate Application and Snowflake

Network round-trip time is the floor on your query latency. Deploy your application in the same cloud region as your Snowflake account. A cross-region deployment adds 30-100ms of network latency that no connector optimization can overcome.

<!-- ------------------------ -->
## Step 2: JDBC (Java / Spring Boot)

### Minimum version: 3.13.31

### Connection with Private Key

```java
Properties props = new Properties();
props.put("user", "ht_app_user");
props.put("private_key_file", "/secrets/rsa_key.p8");
props.put("db", "my_database");
props.put("schema", "my_schema");
props.put("warehouse", "my_warehouse");
props.put("role", "my_role");

Connection conn = DriverManager.getConnection(
    "jdbc:snowflake://<account>.snowflakecomputing.com",
    props
);
```

### Batch INSERT with Bound Variables

Use `prepareStatement` + `addBatch` + `executeBatch` for efficient multi-row inserts:

```java
String sql = "INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) " +
             "VALUES (?, ?, ?, ?, ?, ?)";

try (PreparedStatement stmt = conn.prepareStatement(sql)) {
    for (Order order : orders) {
        stmt.setLong(1, order.getOrderId());
        stmt.setLong(2, order.getCustomerId());
        stmt.setString(3, order.getStatus());
        stmt.setString(4, order.getRegion());
        stmt.setBigDecimal(5, order.getAmount());
        stmt.setTimestamp(6, Timestamp.from(order.getCreatedAt()));
        stmt.addBatch();
    }
    int[] results = stmt.executeBatch();
}
```

### HikariCP Connection Pool

```java
HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:snowflake://<account>.snowflakecomputing.com/" +
    "?warehouse=my_wh&db=my_db&schema=my_schema");
config.setUsername("ht_app_user");
config.addDataSourceProperty("private_key_file", "/secrets/rsa_key.p8");
config.setMaximumPoolSize(20);
config.setMinimumIdle(5);
config.setIdleTimeout(300_000);          // 5 min
config.setConnectionTimeout(30_000);     // 30s — fail fast
config.setKeepaliveTime(60_000);         // 1 min keepalive
config.setMaxLifetime(1_800_000);        // 30 min max lifetime

HikariDataSource dataSource = new HikariDataSource(config);
```

Set the Snowflake JDBC TTL to match the pool's `maxLifetime`:
```java
System.setProperty("net.snowflake.jdbc.ttl", "1800");
```

> **Important:** The default `net.snowflake.jdbc.ttl` is `-1` (infinite). Without setting this, idle connections may go stale and throw errors when reused. Always align this value with your pool's `maxLifetime`.

### Spring Boot + Kafka: Real-Time Ingest Pattern

For event-driven ingest from Kafka, the architecture is:

```
Kafka Topic → Spring Boot Consumer (batched, concurrent) → Hybrid Table
```

This replaces the traditional **Kafka → object store → ETL → Snowpipe** pipeline (5-30 minute lag) with near-real-time delivery (seconds) using the Hybrid Table's high-concurrency write capability.

**`application.yml`** — tune batch size and concurrency to match your Kafka partitions:

```yaml
spring:
  kafka:
    consumer:
      group-id: ht-order-writer
      max-poll-records: 500          # rows per micro-batch
      bootstrap-servers: localhost:9092

kafka-demo:
  topic:
    name: orders
    partitions: 20                   # concurrency = partitions
  snowflake:
    url: jdbc:snowflake://<account>.snowflakecomputing.com
    user: ht_app_user
    database: my_database
    schema: my_schema
    warehouse: my_warehouse
    private-key-file: /secrets/rsa_key.p8
```

**Kafka Listener** — one thread per partition, batch inserts per poll:

```java
@KafkaListener(
    id = "order-writer",
    topics = "${kafka-demo.topic.name}",
    groupId = "ht-order-writer",
    concurrency = "${kafka-demo.topic.partitions}",
    batch = "true"
)
public void writeOrders(
    @Payload List<Order> orders,
    @Header(KafkaHeaders.RECEIVED_PARTITION) List<Integer> partitions
) throws SQLException {
    String sql = "INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) " +
                 "VALUES (?, ?, ?, ?, ?, ?)";

    try (Connection conn = dataSource.getConnection();
         PreparedStatement stmt = conn.prepareStatement(sql)) {
        for (Order o : orders) {
            stmt.setLong(1, o.getOrderId());
            stmt.setLong(2, o.getCustomerId());
            stmt.setString(3, o.getStatus());
            stmt.setString(4, o.getRegion());
            stmt.setBigDecimal(5, o.getAmount());
            stmt.setTimestamp(6, Timestamp.from(o.getCreatedAt()));
            stmt.addBatch();
        }
        stmt.executeBatch();
    }
}
```

Key design decisions:
- **`concurrency = partitions`** — each Kafka partition gets its own thread and its own connection, maximizing write parallelism
- **`batch = "true"`** — collects up to `max-poll-records` messages before calling the listener, reducing round-trips to Snowflake
- **One connection per batch** (via `dataSource.getConnection()` inside the listener) — keeps the connection pool correctly utilized

> For a detailed walkthrough of this pattern including performance results, see [Fresh, Fast, and Value-Effective: Using Snowflake Hybrid Tables to Simplify Kafka Ingestion](https://medium.com/snowflake/fresh-fast-and-value-effective-using-snowflake-hybrid-tables-to-simplify-kafka-ingestion-2a4393c49a53) by Jon Osborn.

<!-- ------------------------ -->
## Step 3: Python Connector

### Minimum version: 3.1.0

Install: `pip install snowflake-connector-python`

### Connection with Private Key

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='<account_identifier>',
    user='ht_app_user',
    authenticator='SNOWFLAKE_JWT',
    private_key_file='/secrets/rsa_key.p8',
    warehouse='my_warehouse',
    database='my_database',
    schema='my_schema',
    autocommit=True,       # default; keep True for HT OLTP
    login_timeout=60,
    network_timeout=30
)
```

### Batch INSERT with `executemany`

Use `executemany` with `?` (qmark) binding. This sends a single batched request to Snowflake rather than individual statements:

```python
rows = [
    (1001, 5042, 'PENDING', 'US-EAST', 149.99),
    (1002, 3891, 'PENDING', 'EU',      89.50),
    (1003, 7204, 'SHIPPED', 'APAC',    220.00),
]

cursor = conn.cursor()
cursor.executemany(
    "INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) "
    "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ)",
    rows
)
```

> **Critical:** Always use `?` placeholders (qmark binding). Never construct SQL with Python string formatting (`f"...{value}..."`) — this bypasses plan caching and introduces SQL injection risk.

### Point Lookup with Bound Variable

```python
def get_order(conn, order_id: int):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE order_id = ?",
        (order_id,)
    )
    return cursor.fetchone()
```

### Connection Pooling with SQLAlchemy

The Python connector has no built-in pool. Use SQLAlchemy for pooled connections:

```python
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL

engine = create_engine(
    URL(
        account='<account>',
        user='ht_app_user',
        database='my_database',
        schema='my_schema',
        warehouse='my_warehouse',
    ),
    connect_args={
        'authenticator': 'SNOWFLAKE_JWT',
        'private_key_file': '/secrets/rsa_key.p8',
        'autocommit': True,
    },
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,          # validate connections before use
    pool_recycle=1800             # recycle connections every 30 min
)
```

### Recommended Batch Size

Aim for **500–1,000 rows per `executemany` call**. Larger batches risk hitting query size limits; smaller batches increase round-trip overhead. Profile your specific row width to find the optimal size.

<!-- ------------------------ -->
## Step 4: Node.js

### Minimum version: 1.9.0

Install: `npm install snowflake-sdk`

### Connection with Private Key

```javascript
const snowflake = require('snowflake-sdk');
const fs = require('fs');

const connection = snowflake.createConnection({
  account: '<account_identifier>',
  username: 'ht_app_user',
  authenticator: 'SNOWFLAKE_JWT',
  privateKey: fs.readFileSync('/secrets/rsa_key.p8', 'utf8'),
  database: 'my_database',
  schema: 'my_schema',
  warehouse: 'my_warehouse'
});

connection.connect((err, conn) => {
  if (err) throw err;
  console.log('Connected to Snowflake');
});
```

### Batch INSERT with Array Binding

Pass an array of arrays as `binds` to insert multiple rows in one call:

```javascript
connection.execute({
  sqlText: 'INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) ' +
           'VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ)',
  binds: [
    [1001, 5042, 'PENDING', 'US-EAST', 149.99],
    [1002, 3891, 'PENDING', 'EU',       89.50],
    [1003, 7204, 'SHIPPED', 'APAC',    220.00]
  ],
  complete: (err, stmt, rows) => {
    if (err) console.error('Insert failed:', err.message);
  }
});
```

### Point Lookup with Bound Variable

```javascript
function getOrder(connection, orderId, callback) {
  connection.execute({
    sqlText: 'SELECT * FROM orders WHERE order_id = ?',
    binds: [orderId],
    complete: (err, stmt, rows) => {
      if (err) return callback(err);
      callback(null, rows[0]);
    }
  });
}
```

### Connection Pool

```javascript
const pool = snowflake.createPool(
  {
    account: '<account_identifier>',
    username: 'ht_app_user',
    authenticator: 'SNOWFLAKE_JWT',
    privateKey: fs.readFileSync('/secrets/rsa_key.p8', 'utf8'),
    database: 'my_database',
    schema: 'my_schema',
    warehouse: 'my_warehouse'
  },
  {
    max: 10,
    min: 2,
    evictionRunIntervalMillis: 60000,   // run evictor every 60s
    idleTimeoutMillis: 300000           // evict connections idle > 5 min
  }
);

// Use a pooled connection
pool.use(async (conn) => {
  return new Promise((resolve, reject) => {
    conn.execute({
      sqlText: 'INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) ' +
               'VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ)',
      binds: [[1001, 5042, 'PENDING', 'US-EAST', 149.99]],
      complete: (err) => err ? reject(err) : resolve()
    });
  });
});
```

> **Important:** The default `evictionRunIntervalMillis` is `0` (eviction disabled). Without setting this, stale idle connections cause errors when reused after network interruptions. Always set `evictionRunIntervalMillis` in production.

<!-- ------------------------ -->
## Step 5: Snowpark

Snowpark is optimized for analytical (columnar) workloads. For Hybrid Table writes, use `session.sql()` with parameterized queries rather than the DataFrame write API.

### Connection

```python
from snowflake.snowpark import Session

session = Session.builder.configs({
    'account': '<account_identifier>',
    'user': 'ht_app_user',
    'authenticator': 'SNOWFLAKE_JWT',
    'private_key_file': '/secrets/rsa_key.p8',
    'database': 'my_database',
    'schema': 'my_schema',
    'warehouse': 'my_warehouse'
}).create()
```

### Single-Row INSERT (Parameterized)

```python
session.sql(
    "INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) "
    "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ)",
    params=[1001, 5042, 'PENDING', 'US-EAST', 149.99]
).collect()
```

### Bulk INSERT from a Staging Table

Snowpark's strength is large-scale SQL transformations. Use it to load batches from a staging table into a Hybrid Table:

```python
batch_id = 'batch_20260616_001'

session.sql(
    "INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) "
    "SELECT order_id, customer_id, status, region, amount, created_at "
    "FROM staging_orders "
    "WHERE batch_id = ?",
    params=[batch_id]
).collect()
```

### Why Not `save_as_table()` for HT?

The Snowpark DataFrame write API (`df.write.save_as_table()`, `df.write.mode()`) is designed for standard Snowflake tables and does not have documented support for Hybrid Tables. Use `session.sql()` to retain explicit control over the INSERT statement and ensure bound variable usage.

```python
# Correct for HT
session.sql("INSERT INTO orders ... VALUES (?, ?, ...)", params=[...]).collect()

# Not recommended for HT
df.write.mode("append").save_as_table("orders")  # may not honor HT constraints
```

<!-- ------------------------ -->
## Step 6: Inline Stored Procedures

Inline Stored Procedures are a stored procedure type built for operational workloads on Hybrid Tables. The entire body is compiled as one unit and pushed to the query processing layer, which avoids the per-statement overhead a standard stored procedure pays. Reach for one when several DML statements against Hybrid Tables have to succeed or fail together.

> **Note:** Inline Stored Procedures are in Public Preview and operate exclusively on Hybrid Tables. Statements that reference standard Snowflake tables, Iceberg tables, or other table types are not supported inside the body.

### Create the Procedure

This procedure updates an order and writes an audit record as one atomic unit. It uses the `orders` table from Setup plus a small audit table:

```sql
CREATE OR REPLACE HYBRID TABLE order_audit (
    audit_id    NUMBER        NOT NULL,
    order_id    NUMBER        NOT NULL,
    old_status  VARCHAR(20)   NOT NULL,
    new_status  VARCHAR(20)   NOT NULL,
    changed_at  TIMESTAMP_NTZ NOT NULL,
    PRIMARY KEY (audit_id)
);

CREATE OR REPLACE INLINE PROCEDURE update_order_status(
  p_order_id   NUMBER,
  p_new_status VARCHAR,
  p_audit_id   NUMBER,
  p_changed_at TIMESTAMP_NTZ
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
  v_old_status VARCHAR;
BEGIN ATOMIC
  SELECT status INTO :v_old_status
    FROM orders
    WHERE order_id = :p_order_id;

  UPDATE orders
    SET status = :p_new_status
    WHERE order_id = :p_order_id;

  INSERT INTO order_audit (audit_id, order_id, old_status, new_status, changed_at)
    VALUES (:p_audit_id, :p_order_id, :v_old_status, :p_new_status, :p_changed_at);

  RETURN 'Updated order ' || :p_order_id
         || ' from ' || :v_old_status
         || ' to ' || :p_new_status;
END;
$$;
```

Two details in that definition matter for your application code:

- **`p_changed_at` is an argument rather than a call to `CURRENT_TIMESTAMP()`.** Dynamic context functions — `CURRENT_TIMESTAMP`, `CURRENT_TIME`, `CURRENT_DATE`, `SYSDATE`, `SYSTIMESTAMP`, `GETDATE`, `LOCALTIME`, and `LOCALTIMESTAMP` — are not supported inside an Inline Stored Procedure, and calling one fails with error `090277`. Compute the value in your application and bind it, as the driver examples below do. The direct INSERT examples earlier in this guide call `CURRENT_TIMESTAMP()` inline, which is correct for direct DML but does not carry over into a procedure body.
- **Arguments are referenced with a colon prefix**, as in `:p_order_id`, inside the body.

> **Important:** Inline Stored Procedures are compiled at CALL time, not at CREATE time. A `CREATE` statement can succeed and the first `CALL` still fail on an unsupported construct. Call each new procedure once in a test environment before you deploy it.

This procedure is deliberately minimal so the call pattern stays readable. Before adapting it, note three things it does not do:

- **It does not verify the order exists.** `UPDATE ... WHERE order_id = :p_order_id` succeeds when it matches zero rows, and `SQLROWCOUNT` is not available inside an Inline Stored Procedure, so the body cannot check how many rows it changed. As written, a call with an unknown `order_id` can still write an audit row describing a change that never happened. Add an explicit `SELECT COUNT(*) INTO` guard against `orders` if that matters to you.
- **It is not a compare-and-swap.** All statements in the block share one read timestamp, so the `SELECT` is a snapshot read, not a version check. Two concurrent callers can both read `PENDING` and both write. Add the expected value to the predicate — `WHERE order_id = :p_order_id AND status = :p_expected_status` — if you need optimistic concurrency.
- **It is only as idempotent as `p_audit_id`.** Because `audit_id` is the audit table's primary key and the caller supplies it, reusing the same value on a retry makes the retry fail rather than double-write. That makes it a usable idempotency key, but only if your application reuses it deliberately on retry instead of generating a fresh one.

Inline Stored Procedures also run with **owner's rights** only; caller's rights execution is not supported, so the procedure's owner needs the privileges on the underlying tables.

> **Note:** This section covers the constraints most likely to affect application code. It is not the complete list — see [Inline Stored Procedures for Hybrid Tables](https://docs.snowflake.com/en/user-guide/hybrid-tables-inline-stored-procedures) for the full set, including restrictions on table functions, `OUT` arguments, `CONTINUE` handlers, session variables, and referencing more than one database.

### Call the Procedure with Bound Variables

`CALL` is an ordinary SQL statement, so no driver needs a special API for it. Each connector binds arguments the same way it does for any other parameterized statement, using the same bind APIs already shown for each driver earlier in this guide.

> **Note:** The Python example below was executed against a Hybrid Table. The JDBC, Node.js, and Snowpark examples translate the same bind pattern into each driver's own API — run them against your own account before relying on them in production.

#### Python

```python
cursor = conn.cursor()
cursor.execute(
    "CALL update_order_status(?, ?, ?, ?)",
    (1001, 'SHIPPED', 9001, '2026-09-23 11:00:00')
)
print(cursor.fetchone()[0])     # Updated order 1001 from PENDING to SHIPPED
```

#### JDBC

A `CALL` returns a single-row result set whose column is named after the procedure:

```java
String sql = "CALL update_order_status(?, ?, ?, ?)";

try (PreparedStatement stmt = conn.prepareStatement(sql)) {
    stmt.setLong(1, 1001L);
    stmt.setString(2, "SHIPPED");
    stmt.setLong(3, 9001L);
    stmt.setTimestamp(4, Timestamp.valueOf("2026-09-23 11:00:00"));

    try (ResultSet rs = stmt.executeQuery()) {
        if (rs.next()) {
            System.out.println(rs.getString(1));
        }
    }
}
```

> **Note:** `Timestamp.valueOf` produces a wall-clock value, which matches the `TIMESTAMP_NTZ` column used here. If you build the value from an `Instant` instead, convert it to the intended local time first so the stored value is not shifted.

#### Node.js

```javascript
connection.execute({
  sqlText: 'CALL update_order_status(?, ?, ?, ?)',
  binds: [1001, 'SHIPPED', 9001, '2026-09-23 11:00:00'],
  complete: (err, stmt, rows) => {
    if (err) return console.error('Call failed:', err.message);
    console.log(rows[0].UPDATE_ORDER_STATUS);
  }
});
```

#### Snowpark

```python
session.sql(
    "CALL update_order_status(?, ?, ?, ?)",
    params=[1001, 'SHIPPED', 9001, '2026-09-23 11:00:00']
).collect()
```

> **Important:** Inline Stored Procedures must be called with autocommit enabled and cannot run inside an open transaction. `AUTOCOMMIT = TRUE` is already the recommended setting for Hybrid Table workloads (see Step 1), so most applications need no change. If your framework or connection pool disables autocommit, commit or roll back the open transaction before calling.

### Returning a Result Set

Declare `RETURNS TABLE` to return rows rather than a scalar. Your driver then reads the result exactly as it reads a `SELECT`:

```sql
CREATE OR REPLACE INLINE PROCEDURE get_order(p_order_id NUMBER)
RETURNS TABLE(
  order_id    NUMBER,
  customer_id NUMBER,
  status      VARCHAR(20),
  region      VARCHAR(10),
  amount      NUMBER(12,2)
)
LANGUAGE SQL
AS
$$
BEGIN ATOMIC
  LET res RESULTSET := (
    SELECT order_id, customer_id, status, region, amount
      FROM orders
      WHERE order_id = :p_order_id
  );
  RETURN TABLE(res);
END;
$$;
```

The column types you declare must match the types the query returns exactly.

### Error Handling and Atomicity

When a statement inside the body fails and nothing handles the error, the failure propagates to your driver as a normal statement error and every change made earlier in the same call is rolled back. The error code is the failing statement's own code rather than a single procedure-level code: in testing, a duplicate primary key surfaced as `200001` and a division by zero as `100051`. Treat those as illustrative and catch your driver's exception type rather than matching one specific code.

```python
import logging

try:
    cursor.execute(
        "CALL update_order_status(?, ?, ?, ?)",
        (1001, 'RETURNED', 9001, '2026-09-23 12:00:00')
    )
except snowflake.connector.errors.ProgrammingError as e:
    # The server rejected the call, so neither the UPDATE nor the audit INSERT
    # took effect. Re-raise or route to your retry logic - do not swallow it.
    logging.warning("update_order_status failed: %s", e)
    raise
```

> **Note:** A client-side timeout is not the same as a server-side failure. If the connection drops after the server committed, your application sees an error for a call that actually succeeded, so catch connection and timeout errors separately and re-check state before retrying rather than assuming a rollback.

An `EXCEPTION` handler placed inside the procedure behaves differently, and the difference is easy to overlook:

> **Important:** A handler that returns makes the `CALL` succeed. Because the call completed normally, statements that already ran in that call are committed rather than rolled back — you have not caught and rolled back, you have converted a failure into a commit of whatever finished first. A procedure that updates a row and then fails to write its audit record leaves the update in place and still returns a value. **A returned error string is therefore not a rollback signal.** Use a handler only where partial completion is acceptable; when you need all-or-nothing behavior, leave the error unhandled so it reaches the caller.

> **Note:** Handlers only run for errors raised after compilation succeeds. Because the body is compiled at CALL time, statically detectable problems — an unknown column, a return-type mismatch, or an unsupported construct such as `CURRENT_TIMESTAMP` — are reported before any statement executes and cannot be caught by an `EXCEPTION` handler.

### When Not to Use One

For a plain single-statement write issued directly by your application, direct DML with bound variables is the simpler path and avoids the procedure entirely. Wrapping a single statement is still worthwhile when you want the abstraction or the access-control boundary a procedure gives you — Snowflake documents that case, because an Inline Stored Procedure executes the body as one unit and so avoids the per-statement overhead a standard stored procedure would add.

Inline Stored Procedures support only `SELECT`, `INSERT`, `UPDATE`, `DELETE`, and `MERGE`, which means they are not a bulk-loading path — keep using batch inserts and the Kafka pattern from Step 2 for ingest.

<!-- ------------------------ -->
## Step 7: Anti-Patterns

These patterns look correct but silently degrade performance or correctness on Hybrid Tables.

### Anti-Pattern 1: String Literals Instead of Bound Variables

**Avoid:**
```python
# Python — new query plan compiled on every execution
cursor.execute(f"SELECT * FROM orders WHERE order_id = {order_id}")

# Node.js — same problem
connection.execute({ sqlText: `SELECT * FROM orders WHERE order_id = ${orderId}` })
```

**Do this instead:** Use `?` or `:N` placeholders. Snowflake compiles the plan once and reuses it across all values.

### Anti-Pattern 2: Single-Row Inserts in a Loop

**Avoid:**
```python
for order in orders:
    cursor.execute("INSERT INTO orders VALUES (?, ?, ...)", order)
    # Each call is a separate round-trip — N orders = N network round-trips
```

**Do this instead:** Use `executemany` (Python), `addBatch`/`executeBatch` (JDBC), or array `binds` (Node.js) to send all rows in one request.

### Anti-Pattern 3: No Connection Pool (Reconnecting per Request)

**Avoid:**
```python
def handle_request(order):
    conn = snowflake.connector.connect(...)   # 100-500ms every time
    cursor.execute(...)
    conn.close()
```

**Do this instead:** Create one connection (or pool) at startup and reuse it across requests.

### Anti-Pattern 4: Oversized Connection Pool

Each connection holds a thread on the Snowflake warehouse. A pool of 200 connections on an XSMALL warehouse overwhelms the warehouse and creates queuing. Match pool size to warehouse concurrency:

| Warehouse Size | Recommended Max Pool Size |
|---------------|--------------------------|
| X-Small | 8-16 |
| Small | 16-32 |
| Medium | 32-64 |

### Anti-Pattern 5: Benchmarking via Snowsight

Snowsight adds compilation and UI overhead that is not representative of driver performance. Always measure latency using your application driver. Results from Snowsight can be 5-20x higher than driver latency for the same query.

### Anti-Pattern 6: Schema-Qualification Inconsistency

If some calls use `my_db.my_schema.orders` and others use just `orders`, Snowflake treats these as different parameterized query hashes and compiles separate plan cache entries for each. This splits your cache hit rate. Use a consistent naming convention across all queries in your application.

<!-- ------------------------ -->
## Get Started Faster with Cortex Code
Duration: 1

Use these prompts in [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to apply this guide to your application:

> "Review my JDBC connection configuration for Hybrid Table latency. I'm seeing [X]ms end-to-end but the query itself runs in [Y]ms. Diagnose the overhead and suggest fixes."

> "Rewrite this Python loop that inserts one row at a time into my Hybrid Table as a proper batch insert with bound variables and connection pooling: [paste code]."

> "Set up a Kafka Sink connector for my Hybrid Table. My HT schema is: [paste DDL]. My Kafka topic payload is: [paste schema]. Generate the connector config with appropriate batch size and error handling."

> "Convert this multi-statement transaction against my Hybrid Tables into an Inline Stored Procedure, and show me the parameterized CALL from [Python / Java / Node.js]: [paste code]. Flag anything in it that Inline Stored Procedures don't support."

<!-- ------------------------ -->
## Cleanup

```sql
DROP PROCEDURE IF EXISTS update_order_status(NUMBER, VARCHAR, NUMBER, TIMESTAMP_NTZ);
DROP PROCEDURE IF EXISTS get_order(NUMBER);
DROP TABLE IF EXISTS order_audit;
DROP TABLE IF EXISTS orders;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now connect applications to Hybrid Tables correctly across all major Snowflake drivers. Key takeaways:

- **Bound variables are non-negotiable** — string literals kill plan cache reuse and latency
- **Pool connections, don't reconnect** — connection setup overhead dominates for OLTP
- **Private key auth for service accounts** — no passwords, no rotation, no MFA prompts
- **Batch inserts** — send rows in batches of 500-1,000, not one at a time
- **Inline Stored Procedures** — for multi-statement units that must be atomic; call them with bound variables and autocommit enabled
- **Kafka ingest** — Kafka → Spring Boot (batched, concurrent) → HT replaces complex multi-hop pipelines
- **Never benchmark via Snowsight** — always measure with your application driver

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

### Related Resources

- [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test)
- [Inline Stored Procedures for Hybrid Tables](https://docs.snowflake.com/en/user-guide/hybrid-tables-inline-stored-procedures)
- [JDBC Driver Documentation](https://docs.snowflake.com/en/developer-guide/jdbc/jdbc)
- [Python Connector Documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [Node.js Driver Documentation](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver)
- [Snowpark Python Documentation](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Fresh, Fast, and Value-Effective: Kafka Ingestion with Hybrid Tables](https://medium.com/snowflake/fresh-fast-and-value-effective-using-snowflake-hybrid-tables-to-simplify-kafka-ingestion-2a4393c49a53) — Jon Osborn
- [Architectural Patterns Overview and Decision Matrix](https://www.snowflake.com/en/developers/guides/hybrid-tables-architectural-patterns/)
- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Streaming and Change Detection Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)
- [Secondary Index Design for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)

<!-- ------------------------ -->
## FAQ

**Q: Which driver gives the lowest latency for Hybrid Tables?**

All drivers support equivalent latency when configured correctly (bound variables, pooling, same-region deployment). JDBC and the Python connector are the most commonly used for OLTP workloads. Choose the driver that matches your application's language and ecosystem.

**Q: Can I use the SQL API for Hybrid Tables?**

The SQL API supports Hybrid Tables but is explicitly not recommended for latency-sensitive workloads. Use a native driver instead.

**Q: How many connections should my pool have?**

Match pool size to your warehouse's concurrent thread capacity. An XSMALL warehouse handles 8-16 concurrent queries well. Larger pools create queuing rather than parallelism. Monitor `QUERY_HISTORY` for queued queries as a signal your pool is oversized.

**Q: Do I need to change anything for `AUTOCOMMIT`?**

No — the default `AUTOCOMMIT = TRUE` is correct for Hybrid Table OLTP workloads. Do not disable it. If you need multi-statement atomicity, use explicit `BEGIN`/`COMMIT` in a single multi-statement transaction, or an Inline Stored Procedure, rather than a standard stored procedure. Note that an Inline Stored Procedure cannot be called from inside an open transaction, so autocommit must stay enabled to use one.

**Q: When should I use an Inline Stored Procedure instead of `BEGIN`/`COMMIT`?**

Use one when a unit of work runs several DML statements against Hybrid Tables and they must all succeed or all fail. The body is compiled and dispatched as a single unit, which avoids the per-statement round trips a standard stored procedure pays. For a plain single-statement write, direct DML with bound variables is simpler. Benchmark your own workload rather than assuming a margin. See Step 6.

**Q: My Inline Stored Procedure returned an error string instead of failing. Why did part of the work still commit?**

An `EXCEPTION` handler inside the procedure catches the error and returns a value, which makes the `CALL` succeed — so statements that already ran in that call are committed rather than rolled back. A returned error string is not a rollback signal. If you need all-or-nothing behavior, remove the handler and let the error propagate to your driver, then handle it in application code.

**Q: Can I use an ORM (Hibernate, SQLAlchemy, ActiveRecord) with Hybrid Tables?**

Yes, with caveats. ORMs that generate literal SQL (embedding values directly into query strings) defeat plan caching. Ensure your ORM is configured to use prepared statements. For example, in SQLAlchemy use `engine.execute(text("..."), {"key": value})` rather than raw string concatenation.

**Q: What happens if a Kafka batch partially fails due to a duplicate primary key?**

`executeBatch` in JDBC reports per-row results in the returned `int[]` array. Rows that fail due to duplicate PK violations will return `Statement.EXECUTE_FAILED` (-3). Implement a retry or dead-letter queue for failed rows. A future pattern covers error handling and dead-letter queue design in detail.

This is per-row behavior for a batch insert, and differs from an Inline Stored Procedure: an unhandled failure there rolls back the entire call rather than reporting per-row status. See Step 6.

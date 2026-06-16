author: Adam Timm
id: hybrid-tables-application-connectors
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn how to connect applications to Snowflake Hybrid Tables using JDBC, Python, Node.js, and Snowpark with bound variables, connection pooling, and Kafka ingest patterns.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, JDBC, Python connector, Node.js, Snowpark, Spring Boot, Kafka, connection pool, HikariCP, bound variables, prepared statements, private key auth, batch insert, executemany, OLTP, application development
related_concepts: plan cache, query compilation, bound parameters, autocommit, connection pooling, private key JWT auth, Kafka consumer, micro-batch, executeBatch
prerequisite_guides: getting-started-with-hybrid-tables, hybrid-tables-secondary-index-design
skill_level: intermediate
estimated_time_minutes: 45
snowflake_features: hybrid_tables, jdbc_driver, python_connector, nodejs_driver, snowpark
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

### Why Connector Choice and Configuration Matter

The single most impactful configuration decision for Hybrid Table performance is whether you use **bound variables (parameterized queries)**. When you use bound variables, Snowflake compiles the query plan once and reuses it across all executions with different parameter values. When you use string literals, Snowflake compiles a new plan for every query — adding 10-100ms of compilation overhead to every request.

For a Hybrid Table workload executing 1,000 queries per second, this difference is the line between millisecond latency and second latency.

### What You Will Learn

- Minimum driver versions required for Hybrid Table support
- How to configure private key authentication for service accounts
- How to set up connection pools correctly (and avoid stale connection errors)
- How to use bound variables for plan cache reuse in each driver
- How to batch insert rows efficiently without row-by-row overhead
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

`AUTOCOMMIT = TRUE` (the default) is the correct setting for Hybrid Table OLTP workloads. Each DML statement is its own atomic transaction. Explicit stored procedure wrappers add overhead. Use explicit `BEGIN`/`COMMIT` only when you need multi-statement atomicity.

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
    "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ)"
).bind([1001, 5042, 'PENDING', 'US-EAST', 149.99]).collect()
```

### Bulk INSERT from a Staging Table

Snowpark's strength is large-scale SQL transformations. Use it to load batches from a staging table into a Hybrid Table:

```python
batch_id = 'batch_20260616_001'

session.sql(
    "INSERT INTO orders (order_id, customer_id, status, region, amount, created_at) "
    "SELECT order_id, customer_id, status, region, amount, created_at "
    "FROM staging_orders "
    "WHERE batch_id = ?"
).bind([batch_id]).collect()
```

### Why Not `save_as_table()` for HT?

The Snowpark DataFrame write API (`df.write.save_as_table()`, `df.write.mode()`) is designed for standard Snowflake tables and does not have documented support for Hybrid Tables. Use `session.sql()` to retain explicit control over the INSERT statement and ensure bound variable usage.

```python
# Correct for HT
session.sql("INSERT INTO orders ... VALUES (?, ?, ...)").bind([...]).collect()

# Not recommended for HT
df.write.mode("append").save_as_table("orders")  # may not honor HT constraints
```

<!-- ------------------------ -->
## Step 6: Anti-Patterns

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
## Cleanup

```sql
DROP TABLE IF EXISTS orders;
```

<!-- ------------------------ -->
## Conclusion and Resources

You can now connect applications to Hybrid Tables correctly across all major Snowflake drivers. Key takeaways:

- **Bound variables are non-negotiable** — string literals kill plan cache reuse and latency
- **Pool connections, don't reconnect** — connection setup overhead dominates for OLTP
- **Private key auth for service accounts** — no passwords, no rotation, no MFA prompts
- **Batch inserts** — send rows in batches of 500-1,000, not one at a time
- **Kafka ingest** — Kafka → Spring Boot (batched, concurrent) → HT replaces complex multi-hop pipelines
- **Never benchmark via Snowsight** — always measure with your application driver

### Related Resources

- [Hybrid Tables Best Practices](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Performance Testing for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-test)
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

No — the default `AUTOCOMMIT = TRUE` is correct for Hybrid Table OLTP workloads. Do not disable it. If you need multi-statement atomicity, use explicit `BEGIN`/`COMMIT` in a single multi-statement transaction rather than stored procedures.

**Q: Can I use an ORM (Hibernate, SQLAlchemy, ActiveRecord) with Hybrid Tables?**

Yes, with caveats. ORMs that generate literal SQL (embedding values directly into query strings) defeat plan caching. Ensure your ORM is configured to use prepared statements. For example, in SQLAlchemy use `engine.execute(text("..."), {"key": value})` rather than raw string concatenation.

**Q: What happens if a Kafka batch partially fails due to a duplicate primary key?**

`executeBatch` in JDBC reports per-row results in the returned `int[]` array. Rows that fail due to duplicate PK violations will return `Statement.EXECUTE_FAILED` (-3). Implement a retry or dead-letter queue for failed rows. A future pattern covers error handling and dead-letter queue design in detail.

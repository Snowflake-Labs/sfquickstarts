author: Brian Pace
id: snowflake-postgres-insert-vs-copy
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Comparing INSERT, batch INSERT, and COPY performance in Postgres
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Comparing INSERT and COPY Performance
<!-- ------------------------ -->
## Overview 

When you need to load data into PostgreSQL, you have several options — but they're not created equal. A single-row INSERT is simple but slow when you have a high volume of rows to insert. Batching multiple rows into one INSERT helps, but there's an even faster approach: the COPY command.

In this hands-on guide, you'll load the same data using three different methods and measure the performance yourself. By the end, you'll understand not just *which* method is fastest, but *why* — so you can make informed decisions about data loading in your applications.

### What You'll Learn

- How to measure query execution time in PostgreSQL
- The performance characteristics of single-row INSERT statements
- How batch INSERT improves on single-row INSERT
- Why COPY dramatically outperforms both INSERT methods
- When to use each approach in your applications

### Prerequisites

- A running Snowflake Postgres instance
- Access to `psql` or another PostgreSQL client
- Basic familiarity with SQL INSERT statements

<!-- ------------------------ -->
## Setup

Before we start comparing performance, let's create a test environment. We'll use a simple table and load the same data using each method so we can make fair comparisons.

### Connect to Your Database

Connect to your Snowflake Postgres instance using psql:

```bash
psql -h <your-host> -U <your-user> -d <your-database>
```

### Create the Test Table

We'll use a simple table that's representative of real-world data loading scenarios:

```sql
-- Create a test table
DROP TABLE IF EXISTS load_test;

CREATE TABLE load_test (
    id SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    quantity INTEGER,
    price NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Enable Timing

PostgreSQL's `\timing` command shows how long each statement takes to execute. This is essential for our comparisons:

```sql
\timing on
```

You should see: `Timing is on.`

From now on, every command will display its execution time.

### Network Latency

Keep in mind during these tests that network latency will play a big part of the total response time.  You can run the following to get a feel for how much overhead network latency is contributing.

```sql
SELECT 1;
```

For example, if this returns 152ms, nearly all of that time is network latency since `SELECT 1` requires virtually no parsing or I/O on the server.

### Verify Setup

Let's make sure everything is working:

```sql
INSERT INTO load_test (product_name, quantity, price) 
VALUES ('Test Product', 10, 19.99);

SELECT * FROM load_test;
```

You should see your test row and the timing information. Now let's clear the table and start our real tests:

```sql
TRUNCATE load_test;
```

<!-- ------------------------ -->
## Method 1: Single-Row INSERT

The most straightforward way to add data to a table is with individual INSERT statements — one statement per row. This is how many applications work by default, especially when processing data one record at a time.

### Understanding Single-Row INSERT

Each INSERT statement follows this pattern:

```sql
INSERT INTO table_name (columns...) VALUES (values...);
```

When you execute this, PostgreSQL must:
1. Parse the SQL statement
2. Plan the execution
3. Insert the row
4. Write to the transaction log (WAL)
5. Return confirmation to the client

This overhead happens for *every single row*.

### Test: Insert 1,000 Rows One at a Time

Let's see this in action. We'll insert 1,000 rows using individual statements.

First, let's create a simple script that generates single-row INSERTs. In psql, we'll use `\o` to capture output, but we need to turn off headers and footers first:

```sql
-- Turn off headers and row count footer
\t on
\pset footer off

-- Generate 1,000 single-row INSERT statements to a file
\o /tmp/single_inserts.sql

SELECT 'INSERT INTO load_test (product_name, quantity, price) VALUES (''Product_' || 
       generate_series || ''', ' || 
       (random() * 100)::int || ', ' || 
       round((random() * 100)::numeric, 2) || ');'
FROM generate_series(1, 1000);

\o

-- Restore normal output settings
\t off
\pset footer on
```

Now clear the table and run the inserts:

```sql
TRUNCATE load_test;
```

```sql
\i /tmp/single_inserts.sql
```

Watch the timing for each statement. You'll notice each INSERT takes a few milliseconds.

**Note:** Network latency from your workstation may cause the response time to show higher than a real-world application would experience.  An INSERT operation in Postgres is typically 1 to 2 ms.

### Check the Results

```sql
SELECT COUNT(*) FROM load_test;
```

You should see 1,000 rows. 

### Record Your Time

Make note of approximately how long the entire process took. On most systems, inserting 1,000 rows one at a time takes **several seconds** due to the per-statement overhead.

> **Key Observation**: Each INSERT requires a full round-trip: the client sends the statement, waits for PostgreSQL to process it, and receives confirmation. This network and processing overhead adds up quickly.

<!-- ------------------------ -->
## Method 2: Batch INSERT

A smarter approach is to combine multiple rows into a single INSERT statement. This reduces the number of round-trips between the client and server.

### Understanding Batch INSERT

Instead of one row per statement:

```sql
INSERT INTO table_name (columns...) VALUES (row1), (row2), (row3), ...;
```

This means PostgreSQL only needs to:
- Parse one statement (instead of 1,000)
- Plan one execution (instead of 1,000)
- Make one network round-trip (instead of 1,000)

### Test: Insert 1,000 Rows in Batches

Let's insert the same 1,000 rows, but this time using batch INSERT statements with 100 rows each (10 statements total). To keep the test fair, we'll spool the statements to a file first, just like we did with single-row INSERTs.

First, generate the batch INSERT statements:

```sql
-- Turn off headers and row count footer
\t on
\pset footer off

-- Generate 10 batch INSERT statements (100 rows each) to a file
\o /tmp/batch_inserts.sql

SELECT 'INSERT INTO load_test (product_name, quantity, price) VALUES ' ||
       string_agg(
           '(''Product_' || s || ''', ' || 
           (random() * 100)::int || ', ' || 
           round((random() * 100)::numeric, 2) || ')',
           ', '
       ) || ';'
FROM generate_series(1, 1000) s
GROUP BY (s - 1) / 100;

-- Turn off spooling
\o

-- Restore normal output settings
\t off
\pset footer on
```

This creates 10 INSERT statements, each containing 100 rows in the VALUES clause.

Now clear the table and run the batch inserts:

```sql
TRUNCATE load_test;
```

```sql
\i /tmp/batch_inserts.sql
```

You'll see 10 INSERT statements execute, each inserting 100 rows.

### Check the Results

```sql
SELECT COUNT(*) FROM load_test;
```

### Compare the Times

You should see a significant improvement! The single batch INSERT is typically **10-50x faster** than 1,000 individual INSERTs.

| Method | Approximate Time |
|--------|------------------|
| 1,000 single INSERTs | Several seconds |
| 1 batch INSERT (1,000 rows) | Tens of milliseconds |

> **Key Observation**: Batch INSERT reduces network round-trips and parsing overhead. However, PostgreSQL still processes each row individually for transaction logging (WAL), which limits how fast it can go.

<!-- ------------------------ -->
## Method 3: COPY

The COPY command is PostgreSQL's high-performance bulk loading mechanism. It's specifically designed for loading large amounts of data as quickly as possible.

### Understanding COPY

COPY works fundamentally differently from INSERT. Instead of SQL statements, COPY uses a **streaming protocol** where the client sends raw data (typically CSV or tab-delimited), and PostgreSQL writes it directly to the table using optimized internal routines.

In psql, we use `\copy` (with a backslash) which is a client-side command that reads/writes files on your local machine:

```sql
\copy table_name (columns...) FROM '/path/to/file.csv' WITH (FORMAT csv)
```

### Test: Load 1,000 Rows with COPY

To keep our test fair, we'll first generate a CSV file with the same 1,000 rows, then load it using COPY.

**Step 1: Generate the CSV file**

```sql
-- Configure psql for clean CSV output (no headers, no alignment, no footer)
\pset format unaligned
\pset tuples_only on
\pset fieldsep ','

-- Spool the data to a CSV file
\o /tmp/load_data.csv

SELECT 
    'Product_' || s,
    (random() * 100)::int,
    round((random() * 100)::numeric, 2)
FROM generate_series(1, 1000) s;

-- Turn off spooling
\o

-- Restore normal output settings
\pset format aligned
\pset tuples_only off
\pset fieldsep '|'
```

**Step 2: Load the data with COPY**

```sql
TRUNCATE load_test;
```

```sql
-- Load 1,000 rows from the CSV file using client-side \copy
\copy load_test (product_name, quantity, price) FROM '/tmp/load_data.csv' WITH (FORMAT csv)
```

Notice how fast this executes compared to the INSERT methods!

### Check the Results

```sql
SELECT COUNT(*) FROM load_test;
```

### Compare All Three Methods

COPY should be the fastest by a significant margin:

| Method | Approximate Time | Relative Speed |
|--------|------------------|----------------|
| 1,000 single INSERTs | Several seconds | 1x (baseline) |
| 1 batch INSERT (1,000 rows) | ~50-100 ms | ~20-50x faster |
| COPY (1,000 rows) | ~10-30 ms | ~100-200x faster |

> **Key Observation**: COPY is dramatically faster because it bypasses the SQL parsing layer entirely and uses optimized bulk-write routines internally.

<!-- ------------------------ -->
## Why COPY Wins

Now that you've seen the performance differences firsthand, let's understand *why* COPY is so much faster. The answer lies in how PostgreSQL handles data at multiple levels.

### 1. Protocol Efficiency

**INSERT (even batch):**
- Sends complete SQL statements as text
- Each statement requires parsing and validation
- Standard request/response communication pattern

**COPY:**
- Switches the connection into a special "streaming mode"
- Sends raw data with minimal formatting
- No SQL parsing overhead for each row

Think of it like the difference between having a conversation (INSERT) versus using a conveyor belt (COPY).

### 2. Simplified Processing

**INSERT:**
Every INSERT statement — even with multiple rows — goes through PostgreSQL's full SQL processing pipeline:

```
SQL Text → Parser → Analyzer → Planner → Executor
```

Each value in your VALUES clause becomes an expression that must be evaluated.

**COPY:**
COPY uses a streamlined fast-path:

```
Raw Data → Type Conversion → Write to Table
```

No expression trees, no query planning — just direct data conversion and writing.

### 3. Smarter Transaction Logging (WAL)

This is one of the biggest differences.

**INSERT:**
- Writes one WAL (Write-Ahead Log) record per row
- 1,000 rows = 1,000 WAL records

**COPY:**
- Batches multiple rows into single WAL records
- Can write one record per *page* (which holds many rows)
- 1,000 rows might only need ~10-20 WAL records

Less logging means less disk I/O and faster commits.

### 4. Buffer Management

**INSERT:**
- Uses PostgreSQL's standard shared buffer pool
- Large inserts can "push out" frequently-used data from cache
- This is called "cache thrashing"

**COPY:**
- Uses a dedicated 16MB "ring buffer" for bulk writes
- Keeps your hot data in cache while loading new data separately
- Prevents bulk loads from disrupting normal database performance

### 5. Memory Efficiency

**INSERT:**
- Memory usage grows with statement size
- A 10,000-row INSERT builds a large in-memory structure

**COPY:**
- Processes one row at a time
- Memory usage stays flat regardless of data size
- Can load billions of rows without memory issues

### Summary: The Five Advantages of COPY

| Aspect | INSERT | COPY |
|--------|--------|------|
| **Protocol** | SQL commands | Data streaming |
| **Processing** | Full SQL pipeline | Optimized fast-path |
| **WAL Records** | One per row | One per page |
| **Buffer Usage** | Shared (can cause thrashing) | Isolated ring buffer |
| **Memory** | Grows with data size | Constant (flat) |

<!-- ------------------------ -->
## Using COPY in Applications

Understanding COPY performance is great, but how do you use it in real applications? Here are examples for popular programming languages.

### Python (psycopg)

```python
import psycopg

def bulk_load_with_copy(conn, data_rows):
    """Load data using COPY for maximum performance"""
    with conn.cursor() as cur:
        # COPY FROM STDIN streams data directly
        with cur.copy("COPY load_test (product_name, quantity, price) FROM STDIN") as copy:
            for row in data_rows:
                copy.write_row(row)
    conn.commit()

# Usage
data = [
    ("Product_1", 42, 29.99),
    ("Product_2", 17, 45.50),
    # ... more rows
]
bulk_load_with_copy(conn, data)
```

### Node.js (pg-copy-streams)

```javascript
const { from: copyFrom } = require('pg-copy-streams');
const { pipeline } = require('stream/promises');
const { Readable } = require('stream');

async function bulkLoadWithCopy(client, rows) {
    const copyStream = client.query(copyFrom(
        "COPY load_test (product_name, quantity, price) FROM STDIN WITH (FORMAT csv)"
    ));
    
    // Convert rows to CSV format and stream
    const dataStream = Readable.from(
        rows.map(row => `${row.product_name},${row.quantity},${row.price}\n`)
    );
    
    await pipeline(dataStream, copyStream);
}
```

### Go (pgx)

```go
func bulkLoadWithCopy(ctx context.Context, conn *pgx.Conn, rows [][]any) error {
    _, err := conn.CopyFrom(
        ctx,
        pgx.Identifier{"load_test"},
        []string{"product_name", "quantity", "price"},
        pgx.CopyFromRows(rows),
    )
    return err
}
```

### Java (JDBC CopyManager)

```java
import org.postgresql.copy.CopyManager;
import org.postgresql.core.BaseConnection;
import java.io.StringReader;
import java.sql.Connection;

public void bulkLoadWithCopy(Connection conn, List<Product> products) throws Exception {
    // Build CSV data in memory
    StringBuilder csvData = new StringBuilder();
    for (Product p : products) {
        csvData.append(p.getName()).append(",")
               .append(p.getQuantity()).append(",")
               .append(p.getPrice()).append("\n");
    }
    
    // Get CopyManager from PostgreSQL connection
    CopyManager copyManager = new CopyManager((BaseConnection) conn);
    
    // Execute COPY from the CSV string
    String copyCommand = "COPY load_test (product_name, quantity, price) FROM STDIN WITH (FORMAT csv)";
    copyManager.copyIn(copyCommand, new StringReader(csvData.toString()));
}
```

For larger datasets, stream directly from a file or use `BufferedReader`:

```java
import java.io.FileReader;
import java.io.BufferedReader;

public void bulkLoadFromFile(Connection conn, String filePath) throws Exception {
    CopyManager copyManager = new CopyManager((BaseConnection) conn);
    
    String copyCommand = "COPY load_test (product_name, quantity, price) FROM STDIN WITH (FORMAT csv)";
    
    try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
        copyManager.copyIn(copyCommand, reader);
    }
}
```

### When to Use Each Method

| Scenario | Recommended Method |
|----------|-------------------|
| Single record from user input | Single INSERT |
| Small batches (10-100 rows) | Batch INSERT |
| Bulk loading (1,000+ rows) | COPY |
| ETL / Data pipelines | COPY |
| Real-time event streaming | Batch INSERT or COPY |

<!-- ------------------------ -->
## Conclusion and Next Steps

Congratulations! You've now experienced firsthand the dramatic performance differences between INSERT and COPY, and you understand *why* these differences exist.

### What You Learned

1. How to measure SQL performance using `\timing`
2. Single-row INSERT is simple but slow due to per-statement overhead
3. Batch INSERT improves performance by reducing round-trips
4. COPY dramatically outperforms INSERT through protocol efficiency, optimized processing, and smarter WAL handling
5. The performance gap widens with larger datasets
6. How to use COPY in application code

### Key Takeaways

- **For bulk loading, always use COPY** — it's typically 5-20x faster than batch INSERT
- **Batch your INSERTs** when COPY isn't practical — even small batches help significantly
- **Avoid single-row INSERTs in loops** — this is the slowest possible approach
- **COPY's advantages compound** — the more data you load, the bigger the performance win

### When to Use Each Approach

| Method | Best For |
|--------|----------|
| Single INSERT | Interactive user input, single records |
| Batch INSERT | Small to medium batches, when COPY isn't available |
| COPY | Bulk loads, ETL, data migration, any large dataset |

### Resources

- [PostgreSQL COPY Documentation](https://www.postgresql.org/docs/current/sql-copy.html)
- [PostgreSQL INSERT Documentation](https://www.postgresql.org/docs/current/sql-insert.html)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/tables-postgres)

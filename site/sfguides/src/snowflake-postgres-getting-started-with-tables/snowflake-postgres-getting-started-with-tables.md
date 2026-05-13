author: Brian Pace
id: snowflake-postgres-getting-started-with-tables
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Follow this tutorial to learn the basics of PostgreSQL for transactional workloads
environments: local, cloud
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Snowflake Postgres Tables
<!-- ------------------------ -->
## Overview 

### Postgres for Transactional Workloads

[PostgreSQL](https://www.postgresql.org/) is a powerful, open-source object-relational database system that is optimized for transactional workloads requiring low latency and high throughput on small random point reads/writes. Pronounced `Post-gres-Q-L` or just `Postgres` for short.  Postgres supports robust referential integrity constraint enforcement, ACID compliance, and advanced indexing that is critical for transactional workloads. You can use Postgres tables with various features like partitioning, foreign data wrappers, logical replication, and a vast set of extensions to power transactional workloads with various needs.

Use cases that benefit from Postgres include:

- Application requires Postgres compatibility
- Low-latency data servicing and ingestion
- Implement full ACID-compliant transactional systems

### Architecture

Postgres uses a proven architecture with over 35 years of active development. The system consists of:

- **Client connections** via standard Postgres protocol (libpq)
- **Query parser and planner** that optimizes SQL queries for best performance
- **Storage engine** with MVCC (Multi-Version Concurrency Control) for concurrent access
- **WAL (Write-Ahead Logging)** for durability and crash recovery
- **Background processes** for vacuuming, checkpointing, and statistics

Key benefits of this architecture:

- ACID compliance ensures data consistency and reliability
- Support for concurrent reads and writes without blocking
- Advanced indexing (B-tree, Hash, GiST, GIN, BRIN) for optimal query performance
- Native support for JSON, full-text search, and geospatial data
- Extensible with custom functions, data types, and extensions

Postgres stores data in a row-oriented format by default, which provides excellent performance for transactional workloads. 

### What You Will Learn 

- The basics of Postgres tables and constraints
- How to create and use Postgres tables with indexes
- The advantages of proper constraint and index usage
- Postgres characteristics like indexes, primary keys, unique and foreign keys
- Row-level locking and transaction isolation

### Prerequisites

- Familiarity with SQL
- Snowflake Postgres cluster
- Postgres client (psql or your preferred client)
- Database superuser or sufficient privileges to create databases and roles
- Basic understanding of relational database concepts

Note:  Several of the commands used in this guide are specific to `psql`.  If another tool is used, some commands may need to be skipped.

## Setup

In this section, we will set up our Postgres environment, create a database, role, schema, and tables that we will use throughout this tutorial.  If you need to install `psql` on MacOS, use `brew install postgresql@18`.

### Step 1 Create Snowflake Postgres Cluster

Follow the ![Getting Started with Snowflake Postgres](en/developers/guides/getting-started-with-snowflake-postgres/) to create a Postgres instance and configure network policies and rules.

### Step 2 Connect to Postgres

To connect to Snowflake Postgres, you will need to get the login credentials for the `snowflake_admin` account.  These credentials are generated during the creation of the Postgres cluster or can be regenerated using `ALTER POSTGRES INSTANCE RESET ACCESS FOR 'snowflake_admin';`.

Save the credentials as environment variables to simplify the connection process.

```bash
export PGHOST="<Snowflake host name>"
export PGDATABASE="postgres"
export PGUSER="snowflake_admin"
export PGPASSWORD="<password>"
export PGSSLMODE=require
``` 

Connect to your Postgres instance using psql or your preferred client:

```bash
# Connect to Postgres as an admin user
psql -U snowflake_admin
```

### Step 3 Setup

#### Create Database Objects

Create a role, database, and schema for our quickstart:

```sql
-- Create role quickstart_user
CREATE ROLE quickstart_user WITH LOGIN PASSWORD 'secure_password_here';

-- Grant database creation privilege
ALTER ROLE quickstart_user CREATEDB;

-- Create database
CREATE DATABASE quickstart_db;
```

With the newly created `quickstart_db`, change the active (connected) database to be `quickstart_db` and create the `quickstart` schema.

```sql
-- Connect to the new database
\c quickstart_db

-- Create schema
CREATE SCHEMA IF NOT EXISTS quickstart;

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON SCHEMA quickstart TO quickstart_user;
GRANT ALL PRIVILEGES ON DATABASE quickstart_db TO quickstart_user;
```

#### Create Tables and Load Data

In this quickstart, we will use Tasty Bytes fictional food truck business data to simulate a typical transactional use case.

We will create three tables:
- **ORDER_HEADER** - Stores order metadata such as TRUCK_ID, CUSTOMER_ID, ORDER_AMOUNT, etc.
- **TRUCK** - Stores truck metadata such as TRUCK_ID, FRANCHISE_ID, MENU_TYPE_ID, etc.
- **TRUCK_HISTORY** - Stores historical TRUCK information, enabling you to track changes over time

First, let's create the TRUCK table with appropriate constraints:

```sql
-- Create TRUCK table
CREATE TABLE quickstart.truck (
    truck_id INTEGER NOT NULL,
    menu_type_id INTEGER,
    primary_city VARCHAR(255),
    region VARCHAR(255),
    iso_region VARCHAR(255),
    country VARCHAR(255),
    iso_country_code VARCHAR(10),
    franchise_flag INTEGER,
    year INTEGER,
    make VARCHAR(255),
    model VARCHAR(255),
    ev_flag INTEGER,
    franchise_id INTEGER,
    truck_opening_date DATE,
    truck_email VARCHAR(255) NOT NULL UNIQUE,
    record_start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (truck_id)
);

-- Create index on commonly queried columns
CREATE INDEX idx_truck_franchise ON quickstart.truck(franchise_id);
CREATE INDEX idx_truck_city ON quickstart.truck(primary_city);
```

Create the TRUCK_HISTORY table for tracking historical changes:

```sql
-- Create TRUCK_HISTORY table
CREATE TABLE quickstart.truck_history (
    truck_id INTEGER NOT NULL,
    menu_type_id INTEGER,
    primary_city VARCHAR(255),
    region VARCHAR(255),
    iso_region VARCHAR(255),
    country VARCHAR(255),
    iso_country_code VARCHAR(10),
    franchise_flag INTEGER,
    year INTEGER,
    make VARCHAR(255),
    model VARCHAR(255),
    ev_flag INTEGER,
    franchise_id INTEGER,
    truck_opening_date DATE,
    truck_email VARCHAR(255) NOT NULL,
    record_start_time TIMESTAMP WITH TIME ZONE,
    record_end_time TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (truck_id, record_start_time)
);

-- Create partial index for querying current records
CREATE INDEX idx_truck_history_current ON quickstart.truck_history(truck_id) 
WHERE record_end_time IS NULL;
```

Create the ORDER_HEADER table with foreign key relationships:

```sql
-- Create ORDER_HEADER table with constraints
CREATE TABLE quickstart.order_header (
    order_id BIGINT NOT NULL,
    truck_id INTEGER,
    location_id BIGINT,
    customer_id INTEGER,
    discount_id FLOAT,
    shift_id INTEGER,
    shift_start_time TIME,
    shift_end_time TIME,
    order_channel VARCHAR(255),
    order_ts TIMESTAMP,
    served_ts VARCHAR(255),
    order_currency VARCHAR(3),
    order_amount NUMERIC(10,4),
    order_tax_amount VARCHAR(255),
    order_discount_amount VARCHAR(255),
    order_total NUMERIC(10,4),
    order_status VARCHAR(50) DEFAULT 'INQUEUE',
    PRIMARY KEY (order_id),
    FOREIGN KEY (truck_id) REFERENCES quickstart.truck(truck_id)
);

-- Create indexes for performance
CREATE INDEX idx_order_header_truck ON quickstart.order_header(truck_id);
CREATE INDEX idx_order_header_ts ON quickstart.order_header(order_ts);
CREATE INDEX idx_order_header_status ON quickstart.order_header(order_status);
CREATE INDEX idx_order_header_customer ON quickstart.order_header(customer_id);
```

#### Load Sample Data

Now let's load sample data into our tables. We'll generate sample data using Postgres's `generate_series()` function. You can adjust the row counts to control the volume of test data.

**Step 1: Clear existing data**

First, clear any existing data from the tables. We truncate `truck_history` first, then `truck` with CASCADE to handle the foreign key relationship with `order_header`:

```sql
TRUNCATE TABLE quickstart.truck_history;
TRUNCATE TABLE quickstart.truck CASCADE;
```

**Step 2: Load the truck table (1,000 rows)**

Generate truck records with varied cities, makes, models, and other attributes:

```sql
INSERT INTO quickstart.truck (
    truck_id, menu_type_id, primary_city, region, iso_region, country, 
    iso_country_code, franchise_flag, year, make, model, ev_flag, franchise_id, 
    truck_opening_date, truck_email, record_start_time
)
SELECT 
    gs.id AS truck_id,
    (gs.id % 5) + 1 AS menu_type_id,
    (ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
           'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
           'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte',
           'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Boston'])[(gs.id % 20) + 1] AS primary_city,
    (ARRAY['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West'])[(gs.id % 5) + 1] AS region,
    (ARRAY['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'FL', 'OH', 'NC', 'WA'])[(gs.id % 10) + 1] AS iso_region,
    'United States' AS country,
    'US' AS iso_country_code,
    (gs.id % 2)::INTEGER AS franchise_flag,
    2015 + (gs.id % 10) AS year,
    (ARRAY['Ford', 'Mercedes', 'Freightliner', 'Chevrolet', 'GMC', 'RAM'])[(gs.id % 6) + 1] AS make,
    (ARRAY['Transit', 'Sprinter', 'MT45', 'Express', 'Savana', 'ProMaster'])[(gs.id % 6) + 1] AS model,
    (gs.id % 4 = 0)::INTEGER AS ev_flag,
    100 + (gs.id % 500) AS franchise_id,
    CURRENT_DATE - ((gs.id % 1825) || ' days')::INTERVAL AS truck_opening_date,
    gs.id || '_truck@email.com' AS truck_email,
    CURRENT_TIMESTAMP - ((gs.id % 365) || ' days')::INTERVAL AS record_start_time
FROM generate_series(1, 1000) AS gs(id);
```

**Step 3: Load the truck_history table**

Copy all truck records into the history table. This simulates having a historical record for each truck:

```sql
INSERT INTO quickstart.truck_history 
SELECT *, NULL AS record_end_time 
FROM quickstart.truck;
```

**Step 4: Load the order_header table (1,000,000 rows)**

Generate order records that reference existing trucks. This query uses a weighted distribution where 80% of orders go to the top 20% of trucks (simulating popular food trucks):

```sql
INSERT INTO quickstart.order_header (
    order_id, truck_id, location_id, customer_id, discount_id, 
    shift_id, shift_start_time, shift_end_time, order_channel, order_ts, 
    served_ts, order_currency, order_amount, order_tax_amount, 
    order_discount_amount, order_total, order_status
)
SELECT 
    1000 + gs.id AS order_id,
    -- Weighted truck selection: 80% of orders go to top 20% of trucks
    CASE 
        WHEN (gs.id * 17) % 100 < 80 THEN ((gs.id * 31) % 200) + 1  -- Top 200 trucks
        ELSE ((gs.id * 37) % 1000) + 1                              -- All trucks
    END AS truck_id,
    5000 + (gs.id % 1000) AS location_id,
    2000 + (gs.id % 5000) AS customer_id,
    CASE WHEN (gs.id * 7) % 100 < 10 THEN ((gs.id * 11) % 20)::FLOAT ELSE 0 END AS discount_id,
    (gs.id % 3) + 1 AS shift_id,
    CASE (gs.id % 3)
        WHEN 0 THEN '08:00:00'::TIME
        WHEN 1 THEN '16:00:00'::TIME
        ELSE '00:00:00'::TIME
    END AS shift_start_time,
    CASE (gs.id % 3)
        WHEN 0 THEN '16:00:00'::TIME
        WHEN 1 THEN '23:00:00'::TIME
        ELSE '08:00:00'::TIME
    END AS shift_end_time,
    (ARRAY['mobile', 'web', 'phone', 'kiosk'])[(gs.id % 4) + 1] AS order_channel,
    CURRENT_TIMESTAMP - ((1000000 - gs.id) % 180 || ' days')::INTERVAL 
        + ((gs.id % 86400) || ' seconds')::INTERVAL AS order_ts,
    CASE 
        WHEN (gs.id * 13) % 100 < 80 THEN 
            (CURRENT_TIMESTAMP - ((1000000 - gs.id) % 180 || ' days')::INTERVAL 
                + ((gs.id % 86400 + 300) || ' seconds')::INTERVAL)::TEXT
        ELSE ''
    END AS served_ts,
    'USD' AS order_currency,
    (10 + ((gs.id * 19) % 90))::NUMERIC(10,4) AS order_amount,
    ((10 + ((gs.id * 19) % 90)) * 0.08)::NUMERIC(10,4)::TEXT AS order_tax_amount,
    CASE 
        WHEN (gs.id * 23) % 100 < 10 THEN (((gs.id * 29) % 20) * 0.1)::NUMERIC(10,4)::TEXT
        ELSE '0'
    END AS order_discount_amount,
    ((10 + ((gs.id * 19) % 90)) * 1.08)::NUMERIC(10,4) AS order_total,
    (ARRAY['COMPLETED', 'COMPLETED', 'COMPLETED', 'INQUEUE', 'PROCESSING'])[(gs.id % 5) + 1] AS order_status
FROM generate_series(1, 1000000) AS gs(id);
```

> **Note**: This insert may take 30-60 seconds depending on your environment.

**Step 5: Verify data relationships**

Confirm the foreign key relationships are intact by checking that all orders reference valid trucks:

```sql
SELECT 
    (SELECT COUNT(*) FROM quickstart.truck) AS trucks,
    (SELECT COUNT(*) FROM quickstart.truck_history) AS truck_history,
    (SELECT COUNT(*) FROM quickstart.order_header) AS orders,
    (SELECT COUNT(DISTINCT truck_id) FROM quickstart.order_header) AS trucks_with_orders;
```

Although autovacuum will run and perform the necessary background statistics gathering, etc. the below commands will manually perform a vacuum and analyze on the newly populated tables.

```sql
VACUUM ANALYZE quickstart.truck;
VACUUM ANALYZE quickstart.truck_history;
VACUUM ANALYZE quickstart.order_header;
```

## Explore Data

In the previous Setup step, we created our database, schema, and tables. Let's explore them now.

```sql
-- Set context
\c quickstart_db
```

We created and loaded data into the TRUCK and ORDER_HEADER tables. Now we can run queries to get familiar with them.

View table information:

```sql
-- List all tables in the data schema and their size
\dt+ quickstart.*

-- View detailed table information
\d+ quickstart.truck
\d+ quickstart.order_header
\d+ quickstart.truck_history
```

Display information about constraints and indexes:

```sql
-- View all constraints on TRUCK table
SELECT con.conname AS constraint_name, con.contype AS constraint_type,
    CASE con.contype
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'c' THEN 'CHECK'
        ELSE 'OTHER'
    END AS constraint_description
FROM pg_constraint con
     JOIN pg_class rel ON rel.oid = con.conrelid
     JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname = 'quickstart' AND rel.relname = 'truck';

-- View all indexes
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'quickstart'
ORDER BY tablename, indexname;
```

Look at sample data from the tables:

```sql
-- Query 10 rows from TRUCK table
SELECT * FROM quickstart.truck LIMIT 10;

-- Query 10 rows from TRUCK_HISTORY table
SELECT * FROM quickstart.truck_history LIMIT 10;

-- Query 10 rows from ORDER_HEADER table
SELECT * FROM quickstart.order_header LIMIT 10;

-- View table row counts
SELECT 'truck' as table_name, COUNT(*) as row_count FROM quickstart.truck
UNION ALL
SELECT 'order_header', COUNT(*) FROM quickstart.order_header
UNION ALL
SELECT 'truck_history', COUNT(*) FROM quickstart.truck_history;
```

## Unique and Foreign Key Constraints

In this section, we will test Unique and Foreign Key constraints.

### Unique Constraints

Postgres's unique constraint ensures that all values in a column are different.

In the TRUCK table, we defined the TRUCK_EMAIL column as NOT NULL and UNIQUE.  A key difference between the uniqueness enforced by a PRIMARY KEY constraint and a UNIQUE constraint is the PRIMARY KEY does not allow NULL values where the UNIQUE constraint does.  In the case of the TRUCK_EMAIL we specified NOT NULL to require values for this field.

Display constraint information:

```sql
-- Set context
\c quickstart_db

-- View constraints on TRUCK table
\d quickstart.truck

-- Or get detailed constraint information
SELECT 
    con.conname AS constraint_name,
    pg_get_constraintdef(con.oid) AS constraint_definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
WHERE rel.relname = 'truck' AND con.contype IN ('u', 'p');
```

Due to the unique constraint, attempting to insert two records with the same email address will fail:

```sql
-- Attempt insert with duplicate email (will fail)
INSERT INTO quickstart.truck VALUES (
    (SELECT MAX(truck_id) + 1 FROM quickstart.truck),
    2, 'Stockholm', 'Stockholm län', 'Stockholm', 'Sweden', 'SE', 
    1, 2001, 'Freightliner', 'MT45 Utilimaster', 0, 276, '2020-10-01',
    (SELECT truck_email FROM quickstart.truck LIMIT 1),
    CURRENT_TIMESTAMP
);
```

You should receive an error message similar to:
```
ERROR: duplicate key value violates unique constraint "truck_truck_email_key"
DETAIL: Key (truck_email)=(1_truck@email.com) already exists.
```

Now let's insert a new record with a unique email address:

```sql
-- Create a new unique email and insert successfully using CTE
WITH new_truck AS (
    SELECT MAX(truck_id) + 1 as new_truck_id,
           (MAX(truck_id) + 1)::TEXT || '_truck@email.com' as new_email
    FROM quickstart.truck
)
INSERT INTO quickstart.truck (
    truck_id, menu_type_id, primary_city, region, iso_region, country,
    iso_country_code, franchise_flag, year, make, model, ev_flag, 
    franchise_id, truck_opening_date, truck_email, record_start_time
)
SELECT new_truck_id, 2, 'Stockholm', 'Stockholm län', 'Stockholm', 'Sweden',
    'SE', 1, 2001, 'Freightliner', 'MT45 Utilimaster', 0, 
    276, '2020-10-01', new_email, CURRENT_TIMESTAMP
FROM new_truck
RETURNING truck_id, truck_email;
```

Statement should run successfully.

### Foreign Key Constraints

Foreign key constraints ensure referential integrity between tables.

First, let's examine the foreign key constraints on the ORDER_HEADER table:

```sql
-- View foreign key constraints
SELECT con.conname AS constraint_name, pg_get_constraintdef(con.oid) AS constraint_definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
WHERE rel.relname = 'order_header' AND con.contype = 'f';
```

Now let's try to insert a record with a non-existent truck_id (this will fail):

```sql
-- Attempt to insert order with non-existent truck
INSERT INTO quickstart.order_header VALUES (
    (SELECT MAX(order_id) + 1 FROM quickstart.order_header),
    -1,  -- Non-existent truck_id
    6090, 0, 0, 0, '16:00:00', '23:00:00', 'web', 
    '2024-02-18 21:38:46', '', 'USD', 17.0000, '', '', 17.0000, 'PENDING'
);
```

The statement should fail with an error:
```
ERROR: insert or update on table "order_header" violates foreign key constraint "order_header_truck_id_fkey"
DETAIL: Key (truck_id)=(-1) is not present in table "truck".
```

Now let's insert with a valid truck_id:

```sql
-- Insert with valid truck_id
INSERT INTO quickstart.order_header VALUES (
    (SELECT MAX(order_id) + 1 FROM quickstart.order_header),
    (SELECT truck_id FROM quickstart.truck LIMIT 1),
    6090, 0, 0, 0, '16:00:00', '23:00:00', 'web', 
    '2024-02-18 21:38:46', '', 'USD', 17.0000, '', '', 17.0000, 'PENDING'
);
```

Statement should run successfully.

### Foreign Key and TRUNCATE

Tables referenced by foreign key constraints have special behavior with TRUNCATE:

```sql
-- Attempt to truncate the parent table (this will fail)
TRUNCATE TABLE quickstart.truck;
```

The statement should fail with an error:
```
ERROR: cannot truncate a table referenced in a foreign key constraint
DETAIL: Table "order_header" references "truck".
HINT: Truncate table "order_header" at the same time, or use TRUNCATE ... CASCADE.
```

### Foreign Key and DELETE

Records referenced by foreign keys cannot be deleted unless the referencing records are removed first:

```sql
-- Try to delete a truck that has orders (will fail)
DELETE FROM quickstart.truck WHERE truck_id = 1;
```

The statement should fail with:
```
ERROR: update or delete on table "truck" violates foreign key constraint "order_header_truck_id_fkey" on table "order_header"
DETAIL: Key (truck_id)=(1) is still referenced from table "order_header".
```

To successfully delete a truck, first delete its orders:

```sql
-- Delete order header
DELETE FROM quickstart.order_header
WHERE truck_id = 1;

-- Delete truck
DELETE FROM quickstart.truck
WHERE truck_id = 1;
```

Both operations complete successfully.  As an alternative, the foreign key constraint could have been created with the CASCADE clause that would automatically delete all child records when the parent was deleted.

## Row Level Locking

Postgres uses Multi-Version Concurrency Control (MVCC) with row-level locking for update operations. This allows for concurrent updates on independent records without blocking reads.

In this step, we will test concurrent updates to different records.

### Setup for Testing

Open two `psql` sessions or two connections using the client tool of your choice. We'll call them Session 1 and Session 2.  Remember to set the environment variables with the connection information in each session if using `psql`.  Optionally, open a third terminal/session to monitor locks.

**Session 1:**
```bash
psql -U snowflake_admin -d quickstart_db
```

**Session 2:**
```bash
psql -U snowflake_admin -d quickstart_db
```

### Running Concurrent Updates

In **Session 1**, start a transaction and update a record:

```sql
-- Session 1

-- Begin transaction
BEGIN;

-- Update the record with highest order_id
UPDATE quickstart.order_header
SET order_status = 'COMPLETED'
WHERE order_id = (SELECT MAX(order_id) FROM quickstart.order_header);

-- DO NOT COMMIT YET!
```

Note that we haven't committed the transaction. There's now an open lock on this record.

In **Session 2**, update a different record:

```sql
-- Session 2

-- Check active transactions
SELECT pid, usename, state, query_start, query 
FROM pg_stat_activity 
WHERE datname = 'quickstart_db' AND state = 'idle in transaction';

-- Update a different record (this will succeed immediately)
UPDATE quickstart.order_header
SET order_status = 'COMPLETED'
WHERE order_id = (SELECT MIN(order_id) FROM quickstart.order_header);
```

Since Postgres uses row-level locking, the second update succeeds immediately without waiting. The locked row in Session 1 doesn't block updates to other rows.

Back in **Session 1**, commit the transaction:

```sql
-- Session 1
-- Commit the transaction
COMMIT;
```

### Testing Lock Contention

Now let's see what happens when two sessions try to update the same row.

In **Session 1**:
```sql
-- Session 1
BEGIN;

UPDATE quickstart.order_header
SET order_status = 'PROCESSING'
WHERE order_id = (SELECT MIN(order_id) FROM quickstart.order_header);
-- Don't commit
```

In **Session 2**, try to update the same row:
```sql
-- Session 2
-- This will wait for Session 1 to commit or rollback
UPDATE quickstart.order_header
SET order_status = 'SHIPPED'
WHERE order_id = (SELECT MIN(order_id) FROM quickstart.order_header);
```

Session 2 will wait for Session 1's lock to be released.  This is known as a blocking lock.

In a third terminal, you can view the locks that have not been granted (blocked):

```shell
psql -U snowflake_admin -d quickstart_db
```

```sql
-- Session 3
SELECT l.locktype, l.relation::regclass, l.mode,
       l.granted, a.usename, a.query, a.state
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE a.datname = 'quickstart_db' and l.granted = false
ORDER BY l.granted;
```

Back in **Session 1**, commit to release the lock:
```sql
-- Session 1
COMMIT;
```

Session 2's update will now complete immediately.

## Consistency and Transactions

Postgres provides ACID compliance, allowing you to run multi-statement operations atomically. In this step, we'll demonstrate updating a truck's information while maintaining historical records.

### Multi-Statement Transaction

We'll simulate a truck owner acquiring a new truck of the same model. We'll:
1. Update the YEAR column in the TRUCK table
2. Update TRUCK_HISTORY to mark the old record's end time
3. Insert a new record in TRUCK_HISTORY

```sql
-- Begin transaction
BEGIN;

-- Update YEAR in TRUCK table
UPDATE quickstart.truck 
SET year = 2024, 
    record_start_time = current_timestamp
WHERE truck_id = 2;
    
-- Update TRUCK_HISTORY to mark the end of the old record
UPDATE quickstart.truck_history 
SET record_end_time = current_timestamp
WHERE truck_id = 2 AND record_end_time IS NULL;
    
-- Insert new record in TRUCK_HISTORY
INSERT INTO quickstart.truck_history 
SELECT *, NULL as record_end_time 
FROM quickstart.truck 
WHERE truck_id = 2;

-- Commit the transaction
COMMIT;
```

All three operations execute as a single atomic unit. If any operation fails, all changes are rolled back.

### Verify Changes Data 

Now let's verify the changes:

```sql
-- Should return two records (one closed, one current)
SELECT truck_id, year, record_start_time, record_end_time,
    CASE 
        WHEN record_end_time IS NULL THEN 'CURRENT'
        ELSE 'HISTORICAL'
    END as record_status
FROM quickstart.truck_history 
WHERE truck_id = 2
ORDER BY record_start_time;

-- Should return the updated record
SELECT truck_id, year, record_start_time 
FROM quickstart.truck 
WHERE truck_id = 2;
```

## Joining Tables

Postgres excels at joining tables efficiently using various join algorithms (nested loop, hash join, merge join).

### Explore Data 

Let's review our tables:

```sql
-- List all tables
\dt quickstart.*

-- View sample data
SELECT * FROM quickstart.truck_history LIMIT 10;
SELECT * FROM quickstart.order_header LIMIT 10;
```

### Join Tables

Join ORDER_HEADER with TRUCK_HISTORY to get order details with truck information:

```sql
-- Simple join
SELECT oh.order_id, oh.order_ts, oh.order_total, oh.order_status,
       th.truck_id, th.make, th.model, th.primary_city
FROM quickstart.order_header oh
     JOIN quickstart.truck_history th ON oh.truck_id = th.truck_id
WHERE th.record_end_time IS NULL
LIMIT 10;

-- More complex analytical query
SELECT th.primary_city, th.make, th.model,
    COUNT(oh.order_id) as total_orders,
    SUM(oh.order_total) as total_revenue,
    AVG(oh.order_total) as avg_order_value,
    MAX(oh.order_ts) as last_order_date
FROM quickstart.order_header oh
     JOIN quickstart.truck_history th ON oh.truck_id = th.truck_id
WHERE th.record_end_time IS NULL
      AND oh.order_status = 'COMPLETED'
GROUP BY th.primary_city, th.make, th.model
ORDER BY total_revenue DESC;
```

### Query Performance

View the query execution plan:

```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS, MEMORY)
    SELECT oh.order_id, oh.customer_id, oh.order_ts, t.primary_city, t.make, t.model
    FROM quickstart.order_header oh
         JOIN quickstart.truck t ON oh.truck_id = t.truck_id
    WHERE oh.order_status = 'COMPLETED';
```

The `EXPLAIN ANALYZE` output shows:
- Join method used (Hash Join, Nested Loop, Merge Join)
- Index usage
- Estimated vs actual rows
- Execution time

For a deeper dive into using EXPLAIN and understanding execution plans, see the [Understanding Execution Plans](/en/developers/guides/snowflake-postgres-execution-plan/) guide.

## Security & Governance

Postgres provides robust security features including role-based access control, row-level security, and data masking capabilities.

### Access Control and User Management

Postgres uses role-based access control (RBAC) similar to SQL standards.

Create a new role with limited privileges:

```sql
-- Create BI User
CREATE ROLE quickstart_bi_user WITH LOGIN PASSWORD 'bi_user_password';

-- Create a new role for BI users
CREATE ROLE quickstart_bi_role;

-- Grant connection to database
GRANT CONNECT ON DATABASE quickstart_db TO quickstart_bi_role;

-- Grant schema usage
GRANT USAGE ON SCHEMA quickstart TO quickstart_bi_role;

-- Grant role to BI user
GRANT quickstart_bi_role TO quickstart_bi_user;
```

In a new session, connect as the BI user.

```bash
psql -U quickstart_bi_user -d quickstart_db -W
```

Test access without SELECT privileges:

```sql
-- Try to select data (this will fail)
SELECT * FROM quickstart.order_header LIMIT 10;
```

You should receive an error:
```
ERROR: permission denied for table order_header
```

Grant SELECT privileges from the `snowflake_admin` session:

```sql
-- Back in the admin session
GRANT SELECT ON ALL TABLES IN SCHEMA quickstart TO quickstart_bi_role;

-- Grant SELECT on future tables too
ALTER DEFAULT PRIVILEGES IN SCHEMA quickstart 
GRANT SELECT ON TABLES TO quickstart_bi_role;
```

Now try again as the BI user:

```sql
-- As quickstart_bi_user
SELECT * FROM quickstart.order_header LIMIT 10;
```

This time it works!

### Column-Level Security

While Postgres doesn't have built-in dynamic data masking like some commercial databases, we can implement it using views and functions.

Create a masking function and view:

```sql
-- Create a function to mask email addresses
CREATE OR REPLACE FUNCTION quickstart.mask_email(email VARCHAR, user_role NAME)
RETURNS VARCHAR AS $$
BEGIN
    -- Show full email to admin roles only
    IF user_role IN ('snowflake_admin', 'quickstart_user') THEN
        RETURN email;
    ELSE
        RETURN '***MASKED***';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a view with masked data
CREATE OR REPLACE VIEW quickstart.truck_masked AS
SELECT 
    truck_id,
    menu_type_id,
    primary_city,
    region,
    iso_region,
    country,
    iso_country_code,
    franchise_flag,
    year,
    make,
    model,
    ev_flag,
    franchise_id,
    truck_opening_date,
    quickstart.mask_email(truck_email, current_user) as truck_email,
    record_start_time
FROM quickstart.truck;

-- Grant access to the view
GRANT SELECT ON quickstart.truck_masked TO quickstart_bi_role;
```

Test as admin (emails visible):

```sql
-- As snowflake_admin or quickstart_user
SELECT truck_id, truck_email FROM quickstart.truck_masked LIMIT 5;
```

Test as BI user (emails masked):

```sql
-- As quickstart_bi_user
SELECT truck_id, truck_email FROM quickstart.truck_masked LIMIT 5;
```

### Row Level Security (RLS)

Postgres supports row-level security to restrict which rows users can see:

```sql
-- Create a policy: BI user can only see completed orders
CREATE POLICY bi_user_completed_orders ON quickstart.order_header
    FOR SELECT
    TO quickstart_bi_user
    USING (order_status = 'COMPLETED');

-- Admin users can see all orders
CREATE POLICY admin_all_orders ON quickstart.order_header
    FOR ALL
    TO quickstart_user, snowflake_admin
    USING (true);

-- Enable RLS on order_header
ALTER TABLE quickstart.order_header ENABLE ROW LEVEL SECURITY;
```

Test as BI user (quickstart_bi_user) - only sees completed orders

```sql
SELECT order_status, count(1) cnt FROM quickstart.order_header GROUP BY order_status;
```

Test as admin (quickstart_user or snowflake_admin) - sees all orders

```sql
SELECT order_status, count(1) cnt FROM quickstart.order_header GROUP BY order_status;
```

## Cleanup

If you wish to keep the Postgres cluster for other testing, skip the following SQL and perform the Postgres Clean section.  

### Option 1: Drop Postgres Cluster

From in Snowsight, select the cluster Postgres instance lists.  Under the menu (three dots) beside the Manage menu, select Drop and follow the confirmation prompts to drop the Postgres Instance.

### Option 2: Postgres Cleanup

Option 2 is to clean-up Postgres if the goal is to keep the cluster.

To clean up your Postgres environment:

```sql
-- Connect as superuser
\c postgres

-- Terminate active connections to the database
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'quickstart_db' AND pid <> pg_backend_pid();

-- Drop database and roles
DROP DATABASE IF EXISTS quickstart_db;
DROP ROLE IF EXISTS quickstart_user;
DROP ROLE IF EXISTS quickstart_bi_user_role;
DROP ROLE IF EXISTS quickstart_bi_user;
```


## Conclusion and Resources

### What You Learned

Having completed this quickstart you have successfully:
- Created a Snowflake Postgres cluster
- Created Postgres tables and loaded data
- Explored table structures, constraints, and indexes
- Learned about unique and foreign key constraints
- Understood row-level locking and MVCC
- Implemented multi-statement transactions for data consistency
- Performed efficient joins between tables
- Implemented security and access control policies
- Created data masking and row-level security policies

### Related Resources:
- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Tutorial](https://www.crunchydata.com/developers/tutorials)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [PostgreSQL Security Best Practices](https://www.postgresql.org/docs/current/user-manag.html)
- [Understanding PostgreSQL Locks](https://www.postgresql.org/docs/current/explicit-locking.html)
- [PostgreSQL MVCC in Detail](https://www.postgresql.org/docs/current/mvcc.html)
- [Getting Started with Hybrid Tables](/en/developers/guides/getting-started-with-hybrid-tables/)
- [Understanding Execution Plans](/en/developers/guides/snowflake-postgres-execution-plan/)

### Next Steps:
- Explore [partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) for large tables
- Learn about [logical replication](https://www.postgresql.org/docs/current/logical-replication.html)
- Implement [full-text search](https://www.postgresql.org/docs/current/textsearch.html)
- Optimize queries with [advanced indexing strategies](https://www.postgresql.org/docs/current/indexes.html)

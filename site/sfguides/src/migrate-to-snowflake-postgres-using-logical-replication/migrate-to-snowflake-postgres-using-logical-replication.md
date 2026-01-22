author: Elizabeth Christensen
id: migrate-to-snowflake-postgres-using-logical-replication
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Learn how to lift and shift existing PostgreSQL workloads into Snowflake Postgres using logical replication for minimal downtime environments
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Migrate to Snowflake Postgres Using Logical Replication
<!-- ------------------------ -->
## Overview

If you're migrating to Snowflake Postgres from another platform, you a few options:

- **pg_dump and pg_restore**: A reliable way to collect an entire database and restore it to a new location. Great for smaller databases (50-150GB) where a brief downtime window is acceptable.

- **Logical replication**: When your database is too large for dump/restore downtime,  logical replication provides a path forward.

This guide focuses on the **logical replication** approach for migrating to Snowflake Postgres. Your existing database, aka the source, becomes the `publisher`, and Snowflake Postgres, aka the target, becomes the `subscriber`. During initial load, all data is copied from publisher to subscriber. After that, any transactions on the publisher are continuously sent to the subscriber, and then a final migration cutover is initiated.

### What You Will Build
- A sample remote database
- Snowflake Postgres instance
- Networking ingress/egress between Snowflake Postgres and a remote database
- A logical replication pipeline from a remote Postgres database to Snowflake Postgres
- A completed data migration from a Postgres to Snowflake Postgres

### What You Will Learn
- How to migrate schema to Snowflake Postgres
- How to configure your source database as a publisher
- How to set up Snowflake Postgres as a replication subscriber
- How to create a network ingress and egress policies to connect the two databases 
- How to monitor replication progress
- How to perform a minimal-downtime cutover
- How to fix sequences and clean up after migration

### Prerequisites
- A source Postgres database. Any self hosted or cloud Postgres database can be used by changing the connection details below.
- Access to a Snowflake account with Snowflake Postgres enabled


<!-- ------------------------ -->
## The Source Database

### Overview
For this guide, we'll create a PostgreSQL database as our origin system. This simulates having an existing production database that you want to migrate to Snowflake Postgres. Any environment for Postgres, including cloud managed environments like Amazon RDS can be used. 

### Create Sample Tables

This example SQL creates three tables that represent a simple ecommerce application: customers, products, and orders.

```sql
-- Create customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    city VARCHAR(50)
);

-- Create products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2)
);

-- Create orders table with foreign key constraints
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE DEFAULT CURRENT_DATE,
    customer_id INT,
    product_id INT,
    quantity INT,

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id) 
        REFERENCES customers(customer_id),

    CONSTRAINT fk_order_product
        FOREIGN KEY (product_id) 
        REFERENCES products(product_id)
);
```

### Insert Sample Data

Add sample data to work with during the migration:

```sql
-- Insert 10 Customers
INSERT INTO customers (first_name, last_name, email, city) VALUES
('Alice', 'Smith', 'alice@example.com', 'New York'),
('Bob', 'Johnson', 'bob@test.com', 'Los Angeles'),
('Charlie', 'Brown', 'charlie@sample.net', 'Chicago'),
('Diana', 'Prince', 'diana@themyscira.com', 'Houston'),
('Evan', 'Wright', 'evan@write.com', 'Phoenix'),
('Fiona', 'Gallagher', 'fiona@shameless.com', 'Chicago'),
('George', 'Martin', 'grrm@books.com', 'Santa Fe'),
('Hannah', 'Montana', 'hannah@music.com', 'Los Angeles'),
('Ian', 'Malcolm', 'ian@chaos.com', 'Austin'),
('Julia', 'Roberts', 'julia@movie.com', 'New York');

-- Insert 10 Products
INSERT INTO products (product_name, category, price) VALUES
('Wireless Mouse', 'Electronics', 25.99),
('Mechanical Keyboard', 'Electronics', 120.50),
('Gaming Monitor', 'Electronics', 300.00),
('Yoga Mat', 'Fitness', 20.00),
('Dumbbell Set', 'Fitness', 55.00),
('Running Shoes', 'Footwear', 89.99),
('Leather Jacket', 'Apparel', 150.00),
('Coffee Maker', 'Kitchen', 45.00),
('Blender', 'Kitchen', 30.00),
('Novel: The Great Gatsby', 'Books', 12.50);

-- Insert 10 Orders
INSERT INTO orders (order_date, customer_id, product_id, quantity) VALUES
('2023-10-01', 1, 1, 1),  -- Alice bought a Mouse
('2023-10-02', 2, 3, 1),  -- Bob bought a Monitor
('2023-10-03', 1, 10, 2), -- Alice bought 2 Books
('2023-10-04', 3, 2, 1),  -- Charlie bought a Keyboard
('2023-10-05', 4, 6, 1),  -- Diana bought Shoes
('2023-10-06', 5, 8, 1),  -- Evan bought Coffee Maker
('2023-10-07', 2, 2, 1),  -- Bob bought a Keyboard
('2023-10-08', 6, 4, 3),  -- Fiona bought 3 Yoga Mats
('2023-10-09', 7, 10, 1), -- George bought a Book
('2023-10-10', 8, 7, 1);  -- Hannah bought a Jacket
```

### Verify Your Setup

Confirm the data was created successfully:

```sql
SELECT 
    (SELECT COUNT(*) FROM customers) as customer_count,
    (SELECT COUNT(*) FROM products) as product_count,
    (SELECT COUNT(*) FROM orders) as order_count;
```

You should see 10 customers, 10 products, and 10 orders.

<!-- ------------------------ -->
## Create Snowflake Postgres Instance

### Overview
Set up Snowflake Postgres and the origin database to allow connections to each other.

### Creating an ingress and egress policy for Snowflake Postgres to initiate a database connection 

Follow the [Getting Started with Snowflake Postgres](/guide/getting-started-with-snowflake-postgres) quickstart to deploy an instance and connect to it, keeping in mind you'll need network policies like the sample below. 

For logical replication, Snowflake Postgres must be able to initiate a connection when the subscription is created. This is different from the connection needed for an outside application connection, psql session, or the schema import step below. You will need to create a special network egress rule to connect Snowflake Postgres to your source database. Here is a sample network statement and create database statements that use this network policy.

```sql
-- Create the ingress rule to allow traffic from origin or other application connections
CREATE NETWORK RULE PG_INGRESS
  TYPE = IPV4
  VALUE_LIST = ('204.236.226.69/32', '25.253.158.254/32')
  MODE = POSTGRES_INGRESS;

-- Create an egress rule to allow Snowflake Postgres to initiate a connection to the source
CREATE NETWORK RULE PG_EGRESS
  TYPE = IPV4
  VALUE_LIST = ('204.236.226.69/32')
  MODE = POSTGRES_EGRESS;

-- Create a new policy using both rules in the allowed list
CREATE NETWORK POLICY "EGRESS TO ORIGIN"
  ALLOWED_NETWORK_RULE_LIST = ('PG_INGRESS', 'PG_EGRESS')
  COMMENT = 'Ingress to internet, egress to bridge db';

-- Create a new Snowflake Postgres instance that uses the new network policy
CREATE POSTGRES INSTANCE SNOWFLAKE_POSTGRES_DEMO
  COMPUTE_FAMILY = 'STANDARD_L'
  STORAGE_SIZE_GB = 10
  AUTHENTICATION_AUTHORITY = POSTGRES
  POSTGRES_VERSION = 17
  NETWORK_POLICY = '"EGRESS TO ORIGIN"';
```

### Allowing connections from Snowflake Postgres to the origin database
For Snowflake Postgres to connect to the origin database, your source must be reachable over the network. Ensure your configuration allows connections from Snowflake's IP range and that your firewall allows inbound connections on port 5432. You can use the hostname in the Snowflake Postgres set up to find the underlying IP address by doing something like:

```
dig hmj7clwu.sfengineering-pgtest6.qa6.us-west-2.aws.postgres.snowflake.app
```

Virtual network peering and PrivateLink are also supported for this use case. 


<!-- ------------------------ -->
## Migrate Schema from Source to Target

### Overview
Logical replication only replicates data changes (`INSERT`, `UPDATE`, `DELETE`), so you must ensure that the target database has the correct schema beforehand. In this step, we'll copy the schema from the source `postgres` database to Snowflake Postgres.

### Set Up Connection Variables

First, set environment variables for your connection strings:

```bash
# Source database 
export SOURCE_DB_URI="postgres://postgres:your_password@mydb-instance.abc123xyz.us-west-2.rds.amazonaws.com:5432/postgres"

# Snowflake Postgres target (use your actual credentials)
export TARGET_DB_URI="postgres://snowflake_admin:********@hmj7c3jdlwu.sfengineering-pgtest6.qa6.us-west-2.aws.postgres.snowflake.app:5432/postgres"
```

### Export Schema from Source to Snowflake Postgres

Run `pg_dump` and `pg_restore` to copy the schema (without data) from source to target:

```bash
pg_dump -Fc -s $SOURCE_DB_URI | pg_restore --no-acl --no-owner --no-publications -d $TARGET_DB_URI
```

This command:
- `-Fc` creates a custom-format archive
- `-s` exports schema only (no data)
- `--no-acl` skips access privileges
- `--no-publications` skips exporting other replication publications
- `--no-owner` skips ownership information

### Verify Schema Migration

Connect to your Snowflake Postgres instance and verify the tables were created:

```bash
psql $TARGET_DB_URI
```

```sql
\dt
```

You should see the `customers`, `products`, and `orders` tables listed. The tables will be empty - that's expected, as data will be replicated in the next steps.

>  
>
> If your migration process proceeds while application development continues, you must keep the receiving database's schema in sync with any schema changes made on your source database.

<!-- ------------------------ -->
## Configure Replication Publisher in Source Database

### Overview
Configure your source database to act as a publisher for logical replication.

### Enable Logical Replication

Logical replication requires `wal_level = logical`. 

```sql
ALTER SYSTEM SET wal_level = 'logical';
```

Note: If you are using Amazon RDS or other managed services, you may need to modify additional parameters. See the host details for specifics. 

Configure the replication settings to allow at least one replication slot:

```sql
ALTER SYSTEM SET max_replication_slots = 4;
ALTER SYSTEM SET max_wal_senders = 4;
ALTER SYSTEM SET max_logical_replication_workers = 4;
ALTER SYSTEM SET max_worker_processes = 10;
ALTER SYSTEM SET max_sync_workers_per_subscription = 2;
```

These settings require a restart to take effect. After restarting, verify they are applied:

```sql
SHOW wal_level;
SHOW max_replication_slots;
```

See the PostgreSQL documentation on [logical replication configuration](https://www.postgresql.org/docs/current/logical-replication-config.html) for guidance on these parameters, for larger projects in production environments you may need to adjust the defaults. 

### Create a Replication User
Create a dedicated user for replication with the `REPLICATION` role attribute and read access to tables being replicated:

```sql
CREATE ROLE replication_user WITH REPLICATION LOGIN PASSWORD 'your_secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO replication_user;
```

### Create the Publication
Create a publication that includes all tables you want to replicate:

```sql
CREATE PUBLICATION snowflake_migration FOR ALL TABLES;
```

Verify your tables are included in the publication:

```sql
SELECT * FROM pg_publication_tables;
```

All tables you intend to migrate should appear in this list.

<!-- ------------------------ -->


### Create the Subscription

Connect to your Snowflake Postgres database and create a subscription using the connection details for your source database:

```sql
CREATE SUBSCRIPTION snowflake_migration 
CONNECTION 'host={source_host} port=5432 dbname=postgres user={replication_user} password={password}' 
PUBLICATION snowflake_migration;
```

Creating the subscription will:
1. Create a replication slot on the publisher
2. Begin copying data from tables in the publication
3. Create temporary slots for each table during initial synchronization

> 
> If the subscription creation fails check the network settings above, both that the source allows connections from Snowflake Postgres and Snowflake Postgres egress is configured to contact the external database.


<!-- ------------------------ -->
## Monitor Replication

### Overview
Monitor the initial data copy and ongoing replication to ensure everything is proceeding correctly.

### Check Subscription Status
On the subscriber (Snowflake Postgres), query `pg_stat_subscription` to see replication status:

```sql
SELECT * FROM pg_stat_subscription;
```

Example output:
```
-[ RECORD 1 ]---------+------------------------------
subid                 | 16726
subname               | snowflake_migration
worker_type           | table synchronization
pid                   | 260393
leader_pid            |
relid                 | 16651
received_lsn          |
last_msg_send_time    | 2026-01-22 18:09:24.763366+00
last_msg_receipt_time | 2026-01-22 18:09:24.763366+00
latest_end_lsn        |
latest_end_time       | 2026-01-22 18:09:24.763366+00
-[ RECORD 2 ]---------+------------------------------
subid                 | 16726
subname               | snowflake_migration
worker_type           | table synchronization
pid                   | 260504
leader_pid            |
relid                 | 16672
received_lsn          |
last_msg_send_time    | 2026-01-22 18:09:25.523061+00
last_msg_receipt_time | 2026-01-22 18:09:25.523061+00
latest_end_lsn        |
latest_end_time       | 2026-01-22 18:09:25.523061+00
```

### Check Per-Table Sync State
View the synchronization state of each table:

```sql
SELECT * FROM pg_subscription_rel;
```

The `srsubstate` column indicates the state:
| Code | State |
|------|-------|
| `d` | Data is being copied |
| `f` | Finished table copy |
| `s` | Synchronized |
| `r` | Ready (normal replication) |

### Verify Row Counts
Because of table bloat and internal statistics differences, you cannot reliably compare table sizes. Instead, compare row counts:

```sql
SELECT 
    (SELECT COUNT(*) FROM customers) as customer_count,
    (SELECT COUNT(*) FROM products) as product_count,
    (SELECT COUNT(*) FROM orders) as order_count;
```

Run this on both source and target to verify data completeness. You should see 10 customers, 10 products, and 10 orders on both sides.

<!-- ------------------------ -->
## Perform Cutover

### Overview
Once replication is caught up and you've validated the data, perform the cutover to complete your migration.

### Cutover Steps

1. **Stop application writes** to the source database
2. **Verify replication is caught up** - ensure all tables show state `r` (ready) in `pg_subscription_rel`
3. **Fix sequences** (see next section)
4. **Update application connection strings** to point to Snowflake Postgres
5. **Resume application operations**

> 
> Plan your cutover window carefully. While logical replication minimizes downtime, you still need a brief window where writes are stopped to ensure consistency.

<!-- ------------------------ -->
## Fix Sequences

### Overview
Logical replication copies data but doesn't update sequence values. You must synchronize sequences before resuming production operations.

### Generate Sequence Update Commands
Run this query on your source database to generate `setval` commands for all sequences, if there are any.

```sql
SELECT
    'SELECT setval(' || quote_literal(quote_ident(n.nspname) || '.' || quote_ident(c.relname)) || ', ' || s.last_value || ');'
FROM
    pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_sequences s ON s.schemaname = n.nspname
        AND s.sequencename = c.relname
WHERE
    c.relkind = 'S';
```

### Apply to Target
Execute the generated commands on your Snowflake Postgres database to synchronize all sequence values.

## Clean Up

### Overview
After a successful migration, clean up the replication configuration on both sides.

### On the Subscriber (Snowflake Postgres)
Drop the subscription:

```sql
DROP SUBSCRIPTION snowflake_migration;
```

### On the Publisher (Source Database)
Drop the publication:

```sql
DROP PUBLICATION snowflake_migration;
```

Optionally, remove the replication user if no longer needed:

```sql
DROP ROLE replication_user;
```

<!-- ------------------------ -->
## Conclusion and Resources

### Congratulations!
You've successfully migrated your Postgres database to Snowflake Postgres using logical replication!

### What You Learned
- How to export and apply schema using `pg_dump` and `pg_restore`
- How to configure a source database as a publisher with proper replication settings
- How to create subscriptions on Snowflake Postgres
- How to monitor replication progress and verify data consistency
- How to perform a minimal-downtime cutover
- How to synchronize sequences after migration

### Key Takeaways
Logical replication is a safe and effective migration strategy. Data consistency for replicated tables is ensured as long as:
- The subscriber's schema is identical to the publisher's
- Replication is one-way with no conflicting writes on the subscriber

### Related Resources
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/about)
- [PostgreSQL Logical Replication Documentation](https://www.postgresql.org/docs/current/logical-replication.html)

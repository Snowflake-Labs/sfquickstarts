author: Dharmendra Shavkani and Elizabeth Christensen
id: migrate_to_snowflake_postgres_using_cortex_code
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Learn how to lift and shift existing PostgreSQL workloads into Snowflake Postgres using Cortex Code CLI (one-time dump/restore and logical replication)
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Migration, Postgres, Cortex Code, Snowflake Postgres, Logical Replication, pg_dump, pg_restore

# Migrate to Snowflake Postgres Using Cortex Code

<!-- ------------------------ -->
## Overview

Duration: 3

If you're migrating to Snowflake Postgres from another platform, you have a few options:

- **pg_dump and pg_restore**: A reliable way to collect an entire database and restore it to a new location. Great for smaller databases (50-150GB) where a brief downtime window is acceptable.

- **Logical replication**: When your database is too large for dump/restore downtime, logical replication provides a path forward.

This guide focuses on using **Cortex Code** to migrate external PostgreSQL databases to Snowflake Postgres. Your existing database, aka the source, becomes the `publisher`, and Snowflake Postgres, aka the target, becomes the `subscriber`. During initial load, all data is copied from publisher to subscriber. After that, any transactions on the publisher are continuously sent to the subscriber, and then a final migration cutover is initiated.

### What You Will Build

- A Snowflake Postgres instance with network ingress and egress policies
- A data migration pipeline from an external PostgreSQL database to Snowflake Postgres
- A logical replication setup from a remote PostgreSQL database to Snowflake Postgres

### What You Will Learn

- How to migrate an external PostgreSQL database to Snowflake Postgres using Cortex Code CLI on macOS, Linux, or Windows
- How to create network ingress and egress policies to connect the two databases
- How to set up Snowflake Postgres as a replication subscriber
- How to monitor replication progress
- How to perform a minimal-downtime cutover
- How to fix sequences and clean up after migration

### What is Cortex Code?

Cortex Code is Snowflake's CLI-based AI coding assistant. It understands Snowflake APIs, SQL, and Python and can execute multi-step workflows through skills. This guide includes an open-source Cortex Code skill that automates the entire migration.

> **Note:** Cortex Code uses large language models (LLMs), so your generated SQL and results may differ from the screenshots in this guide. If you don't get a result (or the answer looks incomplete), try sending the same prompt again.

### What You Will Need

- A source PostgreSQL database. Any self-hosted or cloud-managed PostgreSQL database can be used.
- Access to a Snowflake account with Snowflake Postgres enabled and a role that has `CREATE POSTGRES INSTANCE` privilege (`ACCOUNTADMIN` has this by default).
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed and configured to connect to Snowflake.
- A terminal with `bash`, `zsh`, or `fish` (macOS / Linux) or PowerShell (Windows).
- For network setup: `CREATE NETWORK POLICY` and `CREATE NETWORK RULE` privileges (`ACCOUNTADMIN` has this by default).
- The `postgres-migration-to-snowflake` Cortex Code skill.

<!-- ------------------------ -->
## The Source Database

Duration: 3

### Overview

Any PostgreSQL environment can be used as the source, including cloud-managed services like Amazon RDS, Google Cloud SQL, or Azure Database for PostgreSQL. This guide uses the [Pagila](https://github.com/devrimgunduz/pagila) PostgreSQL database as a sample source for migration.

### Verify the Source Database

Open a terminal and confirm the database is available on your source system:

```bash
psql postgres
```

This produces:

```
postgres=# \l
                                                    List of databases
    Name     |   Owner   | Encoding | Locale Provider |   Collate   |    Ctype    | Locale | ICU Rules |    Access privileges
-------------+-----------+----------+-----------------+-------------+-------------+--------+-----------+-------------------------
 pagila      | username  | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           |
 postgres    | username  | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           |
 template0   | username  | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           | =c/username           +
             |           |          |                 |             |             |        |           | username=CTc/username
 template1   | username  | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           | =c/username           +
             |           |          |                 |             |             |        |           | username=CTc/username
```

<!-- ------------------------ -->
## Check Source Compatibility

Duration: 3

Before setting up any infrastructure, run two checks against your source database to identify potential issues early.

### Extension Compatibility

Compare the extensions installed on your source against what your Snowflake Postgres target supports. Run one query on each database:

**On the source database:**

```sql
SELECT extname AS extension FROM pg_extension ORDER BY extname;
```

**On the Snowflake Postgres target:**

```sql
SELECT name AS extension FROM pg_available_extensions ORDER BY name;
```

The migration skill will compare the two lists automatically. Any extension on the source that doesn't appear in the target's `pg_available_extensions` is unsupported. Example output:

```
         extension         | snowflake_postgres
---------------------------+--------------------
 btree_gist                | supported
 pg_stat_statements        | supported
 pgaudit                   | supported
 plpgsql                   | supported
 plpython3u                | NOT supported
```

Provider-specific extensions (e.g., `crunchy_*`, `rds_*`, `aiven_*`) will show as "NOT supported." These are safe to ignore — they will produce harmless errors during `pg_restore`, but all user tables, data, sequences, and constraints migrate correctly.

If an unsupported extension is one your application depends on (not a provider built-in), that feature may not work on Snowflake Postgres and you should plan accordingly before proceeding.

### Sequence Inventory

Record all user-defined sequences on the source so you know what to watch for after migration:

```sql
SELECT
    schemaname,
    sequencename,
    last_value,
    data_type
FROM pg_sequences
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, sequencename;
```

Example output:

```
 schemaname |    sequencename    | last_value | data_type
------------+--------------------+------------+-----------
 public     | customers_id_seq   |         15 | integer
 public     | orders_id_seq      |         25 | integer
```

This matters because:

- **pg_dump/pg_restore** includes sequence values automatically — no extra work needed.
- **Logical replication** does NOT replicate sequence values. After cutover, each sequence must be manually set to match the source. The migration skill handles this in the cutover step.

<!-- ------------------------ -->
## Set Up Cortex Code CLI

Duration: 8

Everything you can do manually in the [migration guide](https://www.snowflake.com/en/developers/guides/migrate-to-snowflake-postgres-using-logical-replication/) has been fully automated with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) — Snowflake's CLI-based AI coding assistant.

### Install the Cortex Code CLI

Install the Cortex Code CLI by following the [installation guide](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli/).

### Install the Skills

The migration skill lives in the [postgres-migration-to-snowflake](https://github.com/sfc-gh-dshavkani/postgres-migration-to-snowflake) repository. Clone the repo and add the skill directory using the Cortex Code CLI:

```bash
git clone https://github.com/sfc-gh-dshavkani/postgres-migration-to-snowflake.git
cortex skill add postgres-migration-to-snowflake/skills/postgres-migration-to-snowflake
```

You can verify the skill was installed by running:

```bash
cortex skill list
```

You should see `postgres-migration-to-snowflake` listed under `[EXTERNAL]` in the output. The skill is persisted and will be available in all future Cortex Code sessions.

The migration skill delegates to the **[built-in `snowflake-postgres` skill](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-cortex-code)** that ships with Cortex Code for instance creation, credential management, and connection handling. This built-in skill is already installed — no extra setup is needed. It securely saves credentials to `~/.pg_service.conf` and `~/.pgpass` so passwords never appear in chat. You can also use the built-in skill on its own for day-to-day Snowflake Postgres management (listing instances, health checks, diagnostics, suspending/resuming) by prompting Cortex Code directly without invoking the migration skill.

### Verify the Cortex Code CLI Installation

```bash
cortex --version
```

You should see the installed version number printed to the terminal.

<!-- ------------------------ -->
## Connect to Snowflake

Launch Cortex Code CLI by typing `cortex` in your terminal. A setup wizard walks you through connecting to Snowflake.

```bash
cortex
```

The wizard presents two options:

- **Use an existing connection** — If you already have connections defined in `~/.snowflake/connections.toml` (for example from the Snowflake CLI), select one from the list and press Enter.
- **Create a new connection** — Select *More options* and follow the prompts to enter your account identifier, username, and authentication method.

### Authentication Methods for Cortex Code

Cortex Code CLI supports two authentication methods:

| Method | When to Use |
|--------|-------------|
| Browser-based SSO (`externalbrowser`) | Interactive use on a machine with a web browser |
| Programmatic access token (PAT) | Headless environments or automation |

You can generate a PAT from Snowsight under your user menu. See [Using programmatic access tokens for authentication](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) for details.

### Verify the Connection

Once connected, Cortex Code CLI drops you into an interactive session. Type:

```
/status
```

This prints your active session, agent configuration, active connection, role, warehouse, database, schema, working directory, and configuration details.

<!-- ------------------------ -->
## Run Your First Query

With the session running, type a plain-English question:

```
What databases do I have access to?
```

Cortex Code CLI translates your request into SQL, runs it against Snowflake, and returns the results directly in the terminal.

<!-- ------------------------ -->
## Configure the Source Database Connection

Duration: 5

Before migrating, Cortex Code needs to connect to your source PostgreSQL database. There are several ways to provide your connection details:

### Option A: Use a PostgreSQL Service File (Recommended for Consistency)

You can add your source database to `~/.pg_service.conf` and `~/.pgpass` — the same standard PostgreSQL config files that the built-in `snowflake-postgres` skill uses for the target instance. This gives you consistent `psql "service=<name>"` usage for both source and target, and keeps passwords out of chat entirely.

Add a service entry for your source:

```ini
# Add to ~/.pg_service.conf
[my_source]
host=my-postgres-server.example.com
port=5432
dbname=pagila
user=myuser
```

Add the password to `~/.pgpass`:

```
# Add to ~/.pgpass (one line, colon-separated)
my-postgres-server.example.com:5432:pagila:myuser:mypassword
```

Make sure the pgpass file has the correct permissions:

```bash
chmod 600 ~/.pgpass
```

Then tell Cortex Code to use the service name:

```
Use service=my_source for the source database connection
```

### Option B: Provide Connection Details Inline (Recommended for Quick Start)

When the migration skill prompts you for source connection details, provide them directly:

```
Host: my-postgres-server.example.com
Port: 5432
Database: pagila
Username: myuser
Password: mypassword
```

Cortex Code will use these to construct the `pg_dump` or logical replication commands. Passwords are handled securely via environment variables — they are never echoed or written to disk.

### Option C: Store Credentials as a Cortex Code Secret

For repeated use, you can store your source database password as a Cortex Code secret so you don't have to paste it each time:

```bash
cortex secret store SOURCE_PG_PASSWORD --prompt
```

This prompts you to enter the password interactively. It is stored locally and encrypted.

Then when the migration skill runs, you can reference it:

```
Use my stored secret SOURCE_PG_PASSWORD for the source database password
```

To see what secrets you have stored:

```bash
cortex secret list
```

### Connection String Format

If you prefer to provide a single connection string, use standard PostgreSQL URI format:

```
postgres://username:password@hostname:port/database
```

For example:

```
postgres://myuser:mypassword@my-postgres-server.example.com:5432/pagila
```

The skill accepts either individual fields, a full connection string, or a service name.

### Network Requirements

Your source database must be reachable from Snowflake Postgres over the public internet (or through private connectivity). The skill will create egress network rules to allow outbound connections from Snowflake Postgres to your source database IP.

To find your source database's public IP, run on the source machine:

```bash
curl ifconfig.me
```

If your source is behind a firewall, ensure port 5432 (or your custom port) is open to inbound connections from Snowflake.

<!-- ------------------------ -->
## Example Prompts

Start a Cortex Code session and try any of these prompts to invoke the migration skill:

```
postgres-migration-to-snowflake
```

This produces:

```
✓  SKILL  postgres-migration-to-snowflake
  Migrate external PostgreSQL databases to Snowflake Postgres. Use when: settin...

* I'll invoke the postgres-migration-to-snowflake skill to get you the specialized instructions
  for migrating PostgreSQL databases to Snowflake Postgres.

* I'm ready to help you migrate a PostgreSQL database to Snowflake Postgres. Let me start by
  understanding what you need.

  What would you like to do?

  1. Create a new Snowflake Postgres instance (with network setup)
  2. Migrate an external PostgreSQL database to an existing Snowflake Postgres instance
  3. Both - Create a new instance AND migrate data into it

  Which option fits your situation? Also, if you're migrating, could you share:

  * Approximate database size
  * Whether brief downtime is acceptable (determines migration method: pg_dump vs logical replication)
```

Other example prompts:

```
Create a snowflake postgres instance
```

```
Migrate an external PostgreSQL "pagila" database to an existing Snowflake Postgres instance
```

```
Create a new instance AND migrate data into it
```

Cortex Code CLI displays its reasoning steps as it works. If it needs more information, it will ask a follow-up question.

<!-- ------------------------ -->
## Create a Snowflake Postgres Instance and Migrate Your Database

Duration: 20

In this example, we create a new Snowflake Postgres instance and migrate the Pagila database into it using pg_dump/pg_restore.

```
Migrate my external PostgreSQL "pagila" database to a new Snowflake Postgres instance.
```

Sample output:

```
* Let's start by creating your Snowflake Postgres instance, then migrate your data into it.

  Step 1: Instance Configuration

  Please provide the following details:

  | Setting           | Options / Example                                     |
  |-------------------|-------------------------------------------------------|
  | Instance name     | e.g., MY_POSTGRES_INSTANCE                            |
  | Compute size      | STANDARD_M, STANDARD_L, STANDARD_XL, HIGHMEM_L, etc. |
  | Storage size (GB) | Min 10, max 65535                                     |
  | Postgres version  | 16, 17, or 18                                         |
  | High Availability | True or False                                         |
  | Source DB IP      | For egress rule (to connect to your source DB)        |
  | Client/App IP     | For ingress rule (to connect to the new instance)     |

  Also, for network rule creation I'll need:

  * Database.Schema where the network rules should be created (e.g., SECURITYDB.MYRULES)

> PG_NETWORK_DATABASE.PG_NETWORK_SCHEMA

* Got it. I still need the rest of the instance configuration. Please provide:

  | Setting           | Your Value                                            |
  |-------------------|-------------------------------------------------------|
  | Instance name     | ?                                                     |
  | Compute size      | STANDARD_M, STANDARD_L, STANDARD_XL, HIGHMEM_L, etc. |
  | Storage size (GB) | Min 10, max 65535                                     |
  | Postgres version  | 16, 17, or 18                                         |
  | High Availability | True or False                                         |
  | Source DB IP      | For egress (migration connectivity)                   |
  | Client/App IP     | For ingress (your app connecting in)                  |

> create a postgres instance holpostgres, Compute size STANDARD_M, Storage size 10gb,
  Postgres version 18, High Availability false

* I have the instance configuration. I still need the network IPs before I can proceed:

  | Setting                  | Needed For                                                      |
  |--------------------------|-----------------------------------------------------------------|
  | Source database IP(s)    | Egress rule — allows Snowflake Postgres to reach your source DB |
  | Client/Application IP(s) | Ingress rule — allows your app/client to connect                |

  Please provide both (CIDR format, e.g., 203.0.113.10/32).

> 0.0.0.0/0

* To confirm, you want to use 0.0.0.0/0 for both ingress and egress rules. This is very
  permissive and not recommended for production — it opens your instance to the entire internet.
  For production, restrict to specific IPs.

  Configuration summary:

  | Setting                 | Value                                  |
  |-------------------------|----------------------------------------|
  | Instance name           | HOLPOSTGRES                            |
  | Compute size            | STANDARD_M                             |
  | Storage (GB)            | 10                                     |
  | Postgres version        | 18                                     |
  | High Availability       | False                                  |
  | Network rules DB.Schema | PG_NETWORK_DATABASE.PG_NETWORK_SCHEMA  |
  | Ingress (client IPs)    | 0.0.0.0/0                              |
  | Egress (source DB IPs)  | 0.0.0.0/0                              |

  Shall I go ahead and create the network rules, network policy, and the instance?

> yes

✓  SNOWFLAKE_SQL_EXECUTE  Create database for network rules
  SQL Result: PG_NETWORK_DATABASE already exists, statement succeeded.

✓  SNOWFLAKE_SQL_EXECUTE  Create schema for network rules
  SQL Result: PG_NETWORK_SCHEMA already exists, statement succeeded.

✓  SNOWFLAKE_SQL_EXECUTE  Create ingress network rule
  SQL Result: Network rule HOLPOSTGRES_INGRESS successfully created.

×  SNOWFLAKE_SQL_EXECUTE  Create egress network rule
  └─ Error: 0.0.0.0/0 is not allowed for POSTGRES_EGRESS mode. Snowflake requires specific IPs.

* The ingress rule was created successfully. The egress rule failed — 0.0.0.0/0 is not allowed
  for POSTGRES_EGRESS mode.

  I need the public IP address of the machine running your source PostgreSQL database:

    curl ifconfig.me

> 99.89.93.95

✓  SNOWFLAKE_SQL_EXECUTE  Create egress network rule with source DB IP
  SQL Result: Network rule HOLPOSTGRES_EGRESS successfully created.

✓  SNOWFLAKE_SQL_EXECUTE  Verify egress network rule
  | created_on                    | name               | database_name       |
  |-------------------------------|--------------------|---------------------|
  | 2026-03-27 10:26:30.525 -0700 | HOLPOSTGRES_EGRESS | PG_NETWORK_DATABASE |

✓  SNOWFLAKE_SQL_EXECUTE  Verify ingress network rule
  | created_on                    | name                | database_name       |
  |-------------------------------|---------------------|---------------------|
  | 2026-03-27 10:24:35.892 -0700 | HOLPOSTGRES_INGRESS | PG_NETWORK_DATABASE |

✓  SNOWFLAKE_SQL_EXECUTE  Create network policy
  SQL Result: Network policy HOLPOSTGRES_POLICY successfully created.

✓  BASH  pg_connect.py --create --instance-name HOLPOSTGRES --compute-pool STANDARD_M ...
  ├─ ✅ Created HOLPOSTGRES (STANDARD_M, 10GB)
  ├─ ⏳ Instance is provisioning (1-2 minutes)
  ├─ ✅ Connection saved to ~/.pg_service.conf
  ├─ ✅ Password saved to ~/.pgpass
  ├─ ✅ CA certificate saved, sslmode=verify-ca
  └─ Connect with: psql "service=HOLPOSTGRES"

* The instance is being provisioned. Credentials saved securely — no passwords displayed in chat.

  Which migration method would you like?

  1. pg_dump/pg_restore — recommended for databases < 150GB, involves brief downtime
  2. Logical Replication — recommended for large DBs, minimal downtime

  Please also provide your source PostgreSQL connection details:
  Host, Port (default 5432), Database name, Username, Password

> Option 1, Host - localhost, database name pagila, username sampleusername

✓  SNOWFLAKE_SQL_EXECUTE  Check Postgres instance status
  Result: state = READY

* The instance is READY. Please provide the password for sampleusername (and confirm port 5432).

> use default port 5432, Password - password

✓  BASH  pg_dump -Fc -h localhost -p 5432 -U sampleusername pagila | pg_restore --no-acl --no-owner --no-publications -d "service=HOLPOSTGRES"
  └─ Command completed with exit code 0

✓  BASH  Row count verification — source
  ├─ actor|200       ├─ address|603      ├─ category|16
  └─ ... (19 more tables)

✓  BASH  Row count verification — target
  ├─ actor|200       ├─ address|603      ├─ category|16
  └─ ... (19 more tables)

* All row counts match. Migration verified.

  Migration Summary

  | Table         | Source | Target | Match |
  |---------------|--------|--------|-------|
  | actor         | 200    | 200    | ✓     |
  | address       | 603    | 603    | ✓     |
  | category      | 16     | 16     | ✓     |
  | city          | 600    | 600    | ✓     |
  | country       | 109    | 109    | ✓     |
  | customer      | 599    | 599    | ✓     |
  | film          | 1,000  | 1,000  | ✓     |
  | film_actor    | 5,462  | 5,462  | ✓     |
  | film_category | 1,000  | 1,000  | ✓     |
  | inventory     | 4,581  | 4,581  | ✓     |
  | language      | 6      | 6      | ✓     |
  | payment       | 16,049 | 16,049 | ✓     |
  | rental        | 16,044 | 16,044 | ✓     |
  | staff         | 2      | 2      | ✓     |
  | store         | 2      | 2      | ✓     |

  All 22 tables migrated with 100% row count match.

  Sequence Verification

  | Sequence                        | Source | Target | Match |
  |---------------------------------|--------|--------|-------|
  | public.actor_actor_id_seq       | 200    | 200    | ✓     |
  | public.address_address_id_seq   | 605    | 605    | ✓     |
  | public.category_category_id_seq | 16     | 16     | ✓     |
  | ... (remaining sequences)       |        |        | ✓     |

  All sequences verified — last_value matches between source and target.

  Your Snowflake Postgres instance is ready to use:

  * Host: ih4xguuscvfvramvgsnarwduxe.northamerica-sampleregion-xxxx.xxxx.postgres.snowflake.app
  * Port: 5432
  * Database: postgres
  * User: snowflake_admin

  Connect with: psql "service=HOLPOSTGRES"

  Credentials are stored securely in ~/.pg_service.conf and ~/.pgpass.
```

<!-- ------------------------ -->
## Cutover and Cleanup

Duration: 5

After verifying your migration, complete the cutover to move your application to Snowflake Postgres.

### For pg_dump/pg_restore Migrations

Since pg_dump/pg_restore is a one-time copy, cutover is straightforward:

1. **Stop application writes** to the source database.
2. **Update application connection strings** to point to the Snowflake Postgres instance. Use the host, port, database, and credentials from the instance creation step.
3. **Resume operations** against Snowflake Postgres.
4. **Decommission the source** once you've confirmed the application is running correctly on Snowflake Postgres.

### For Logical Replication Migrations

Logical replication requires additional steps to ensure no data is lost during cutover:

1. **Stop application writes** to the source database.

2. **Verify replication has caught up** — all tables should show state `r` (ready):

```sql
-- Run on SNOWFLAKE POSTGRES
SELECT * FROM pg_subscription_rel;
```

3. **Fix sequences on the target.** Logical replication does not replicate sequence values. Run this query on the **source** to generate the `setval` commands:

```sql
-- Run on SOURCE
SELECT
    'SELECT setval(' || quote_literal(quote_ident(n.nspname) || '.' || quote_ident(c.relname)) || ', ' || s.last_value || ');'
FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_sequences s ON s.schemaname = n.nspname AND s.sequencename = c.relname
WHERE c.relkind = 'S';
```

Then execute the generated `setval` commands on the **Snowflake Postgres** target.

4. **Update application connection strings** to point to Snowflake Postgres.
5. **Resume operations.**

### Cleanup

After cutover is complete and your application is running on Snowflake Postgres:

**Drop the subscription** on Snowflake Postgres (logical replication only):

```sql
DROP SUBSCRIPTION snowflake_migration;
```

**Drop the publication and replication user** on the source (logical replication only):

```sql
DROP PUBLICATION snowflake_migration;
DROP ROLE replication_user;  -- Optional
```

**Remove egress network rules** if no longer needed. The egress rules were created to allow Snowflake Postgres to reach the source database during migration. Once migration is complete, they can be removed:

```sql
DROP NETWORK RULE <database>.<schema>.<INSTANCE_NAME>_EGRESS;
```

Then update the network policy to remove the egress rule reference.

<!-- ------------------------ -->
## Conclusion and Resources

### Congratulations!

You've successfully migrated the Pagila database to Snowflake Postgres using Cortex Code!

### What You Learned

- How to create a Snowflake Postgres instance with network ingress and egress policies
- How to migrate a database using `pg_dump` and `pg_restore`
- How to configure logical replication between a source database and Snowflake Postgres
- How to monitor replication progress and verify data consistency
- How to perform a minimal-downtime cutover
- How to synchronize sequences after migration

### Key Takeaways

Both `pg_dump`/`pg_restore` and logical replication are effective migration strategies. Data consistency for replicated tables is ensured as long as:

- The subscriber's schema is identical to the publisher's
- Replication is one-way with no conflicting writes on the subscriber

### Related Resources

- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/about)
- [PostgreSQL Logical Replication Documentation](https://www.postgresql.org/docs/current/logical-replication.html)

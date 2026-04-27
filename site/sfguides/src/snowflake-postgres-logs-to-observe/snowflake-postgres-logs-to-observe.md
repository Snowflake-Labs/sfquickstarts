author: Elizabeth Christensen
id: snowflake-postgres-logs-to-observe
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Monitor Snowflake Postgres with Observe using the native app and the event table for logs and metrics
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Monitor Snowflake Postgres with Observe

This guide walks through setting up Postgres monitoring with [Observe](https://observeinc.com) using the **Observe for Snowflake** native application. Postgres logs and metrics flow through the Snowflake event table and are pushed to Observe automatically, giving you log exploration, metrics dashboards, and alerting without any intermediate pipeline.

Snowflake Postgres logs and metrics are routed through Snowflake's account-level event table at `SNOWFLAKE.TELEMETRY.EVENTS`. This table is the bridge between your Postgres instance and Observe.

**What you'll build:** A monitoring pipeline where Snowflake Postgres logs and metrics are captured in Snowflake's event table and automatically ingested into Observe for monitoring, searching, and alerting.

### What You'll Learn

- How to configure Postgres logging parameters on a Snowflake Postgres instance
- How Snowflake's event table captures and stores Postgres logs and metrics
- How to set up Snowflake roles, grants, and network policies for Observe
- How to configure Observe's Snowflake integration for log and metric ingestion
- How to verify logs and metrics flow end-to-end from Postgres to Observe

## Prerequisites

- A **Snowflake account** with `ACCOUNTADMIN` access (needed for grants and network policies)
- A **Snowflake Postgres instance** in READY state (or ability to create one)
- An **[Observe](https://observeinc.com) account** with a valid ingest token
- A Snowflake warehouse (XS is sufficient)
- `ACCOUNTADMIN` or equivalent privileges

## 1: Enable Postgres Logging

Snowflake Postgres supports standard PostgreSQL logging parameters. Before flipping switches, it helps to understand what Postgres can log and why it matters.

### A Quick Primer on Postgres Logging

A modern Postgres instance produces comprehensive logs covering nearly every facet of database behavior. While logs are the go-to place for finding critical errors, they're also a key tool for application performance monitoring. Here are the parameters you should know about:

**Log severity level (`log_min_messages`):** Controls which server messages are logged based on severity. Setting a level includes that level and everything above it. The default in Snowflake Postgres is `NOTICE`, which is a sensible baseline for most environments.

- `DEBUG5` through `DEBUG1` — Increasingly verbose developer diagnostics. Rarely useful outside of Postgres core development.
- `INFO` — Messages explicitly requested by the user (e.g., output from `VACUUM VERBOSE`).
- `NOTICE` — Information the user should know about, such as truncation of long identifiers or index creation hints. **(default)**
- `WARNING` — Potential problems that don't prevent the operation from completing (e.g., committing outside a transaction block).
- `ERROR` — The current command failed and was aborted, but the session continues.
- `LOG` — Operational messages useful for administrators (e.g., checkpoint activity, connection authorized).
- `FATAL` — The current session is terminated due to an unrecoverable error.
- `PANIC` — The entire database server is shut down. All sessions are aborted.

**What SQL to log (`log_statement`):**
- `none` — Don't log SQL statements (errors and warnings still appear via `log_min_messages`)
- `ddl` — Log data definition changes only (table, column, and index changes). A good default for production.
- `mod` — Log all DDL plus data modifications (INSERT, UPDATE, DELETE)
- `all` — Log every SQL statement. Useful for development and debugging but generates high log volume.

**Slow query logging (`log_min_duration_statement`):** Captures queries that exceed a time threshold — a great way to surface inefficient queries without logging everything. A setting of `1s` or `500ms` is a common starting point.

**Lock wait logging (`log_lock_waits`):** Logs any time a query waits on a lock longer than `deadlock_timeout`. This is safe for production with virtually no overhead and helps identify contention.

**Temp file logging (`log_temp_files`):** Logs when Postgres spills operations to disk instead of keeping them in memory. Set this to your `work_mem` value to catch operations that exceed available memory — a signal you may need to tune memory settings, add indexes, or rewrite queries.

**Connection logging (`log_connections`, `log_disconnections`):** Logs session connect and disconnect events. Helpful for auditing and spotting connection churn.

> **Production vs. development trade-off:** `log_statement=all` generates a lot of log data and is generally not recommended for production workloads. For production, `ddl` combined with `log_min_duration_statement` for slow queries gives you the important details without the volume. For this guide, we use `all` so every test query is visible in Observe.

For a deeper dive on logging configuration, log formats, rotation, `auto_explain`, and using logs for performance tuning, see [Postgres Logging for Performance Optimization](https://www.crunchydata.com/blog/postgres-logging-for-performance-optimization).

### Snowflake Postgres log line prefix

The default `log_line_prefix` on Snowflake Postgres is:

```
[%p][%b][%v][%x] %q[user=%u,db=%d,app=%a] [%h]
```

This is a printf-style format string that gets prepended to every log line. Each escape sequence maps to a piece of metadata:

| Escape | Meaning | Example output |
|---|---|---|
| `%p` | Process ID (pid) | `1592908` |
| `%b` | Backend type | `client backend` |
| `%v` | Virtual transaction ID | `27/2` |
| `%x` | Transaction ID | `0` |
| `%q` | Non-session stop point (everything after `%q` only prints for session processes) | (controls conditional output) |
| `%u` | Username | `snowflake_admin` |
| `%d` | Database name | `postgres` |
| `%a` | Application name | `psql` |
| `%h` | Client hostname/IP | `34.214.158.144` |

### Configure Logging on Your Snowflake Postgres Instance

By default, Snowflake Postgres does not generate logs. You will need to set `log_statement` to enable them. If you do not have a production instance, you can set this to `all` for testing log ingestion. For production, review your necessary configurations.

```sql
ALTER SYSTEM SET log_statement = 'all';
```

<!-- ------------------------ -->
## 2: Confirm Logs and Metrics in the Snowflake Event Table

### Snowflake Postgres logs

After enabling logging (above), run a few queries against your Postgres instance to generate some log data. If you set `log_statement` to `all`, here's a sample to run:

```sql
CREATE TABLE cookie_monster (
    id SERIAL PRIMARY KEY,
    cookie_type VARCHAR(100),
    flavor VARCHAR(50),
    crunchiness INT CHECK (crunchiness BETWEEN 1 AND 10),
    nom_rating DECIMAL(3,1),
    eaten_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO cookie_monster (cookie_type, flavor, crunchiness, nom_rating)
VALUES
    ('Chocolate Chip', 'chocolate', 8, 9.5),
    ('Snickerdoodle', 'cinnamon', 6, 8.7),
    ('Oatmeal Raisin', 'oat', 7, 7.2),
    ('Double Chocolate', 'dark chocolate', 9, 9.8),
    ('Peanut Butter', 'peanut', 5, 8.1);

SELECT * FROM cookie_monster WHERE crunchiness > 7;
SELECT cookie_type, nom_rating FROM cookie_monster ORDER BY nom_rating DESC;
SELECT AVG(crunchiness) AS avg_crunch, MAX(nom_rating) AS best_nom FROM cookie_monster;
```

Now verify that logs appear in the event table:

```sql
-- Replace the instance ID with your Postgres instance's ID
-- Find it with: SHOW POSTGRES INSTANCES;  
SELECT
    TIMESTAMP,
    RESOURCE_ATTRIBUTES['instance.id']::STRING AS instance_id,
    VALUE['MESSAGE']::STRING AS message
FROM SNOWFLAKE.TELEMETRY.EVENTS
WHERE TIMESTAMP > DATEADD('hour', -1, CURRENT_TIMESTAMP())
  AND RECORD_TYPE = 'LOG'
  AND RESOURCE_ATTRIBUTES['instance.id']::STRING = '<YOUR_INSTANCE_ID>'
ORDER BY TIMESTAMP DESC
LIMIT 20;
```

> **Tip:** To find your Postgres instance ID, run `SHOW POSTGRES INSTANCES;` Use the first segment of the host column (everything before the first period). For example, if host is 4jypgsndvzd5ta6ufaryx6owja.sfdevrel-sfdevrel-enterprise.us-west-2.aws.postgres.snowflake.app, the instance ID is 4jypgsndvzd5ta6ufaryx6owja.

### Snowflake Postgres metrics

Snowflake Postgres collects metrics in `SNOWFLAKE.TELEMETRY.EVENTS` automatically via a monitoring agent every ~5 seconds. The tables below list every metric by category.

#### Postgres

| Metric | Type | Description |
|---|---|---|
| `postgres_connections` | gauge | Number of active backend connections |
| `postgres_databases_size_bytes` | gauge | Total size of all databases (bytes) |
| `postgres_wal_size_bytes` | gauge | WAL directory size (bytes) |
| `postgres_log_size_bytes` | gauge | Log directory size (bytes) |
| `postgres_tmp_size_bytes` | gauge | Temp file size (bytes) |
| `postgres_locking_transactions` | gauge | Number of granted locks |
| `postgres_locked_transactions` | gauge | Number of waiting/blocked locks |
| `server_version` | gauge | Postgres version as an integer (e.g., 180003 = 18.0.3) |

#### CPU

| Metric | Type | Unit | Dimensions |
|---|---|---|---|
| `system.cpu.time` | sum | seconds | state: user, system, wait, idle, nice, interrupt, softirq, steal |
| `system.cpu.load_average.1m` | gauge | threads | — |
| `system.cpu.load_average.5m` | gauge | threads | — |
| `system.cpu.load_average.15m` | gauge | threads | — |

> `system.cpu.time` is a cumulative counter. To get a percentage, compute the delta between consecutive samples and divide by the elapsed interval.

#### Memory

| Metric | Type | Unit | Dimensions |
|---|---|---|---|
| `system.memory.usage` | sum | bytes | state: used, free, cached, buffered, slab_reclaimable, slab_unreclaimable |

#### Disk

| Metric | Type | Unit | Dimensions |
|---|---|---|---|
| `system.filesystem.usage` | sum | bytes | mountpoint, device, state (used, free), type, mode |

#### Network

| Metric | Type | Unit | Dimensions |
|---|---|---|---|
| `system.network.io` | sum | bytes | device, direction (transmit, receive) |

#### Paging

| Metric | Type | Unit | Dimensions |
|---|---|---|---|
| `system.paging.usage` | sum | bytes | device, state (used, free) |

#### Resource attributes

Every metric row includes the following in `RESOURCE_ATTRIBUTES`:

| Attribute | Description | Example |
|---|---|---|
| `instance_id` | Postgres instance identifier | `4jypgsndvzd5ta6ufaryx6owja` |
| `host.id` | EC2 instance ID | `i-0f6724aef472706a3` |
| `host.type` | Instance family | `m8g.medium` |
| `cloud.region` | AWS region | `us-west-2` |
| `cloud.availability_zone` | Availability zone | `us-west-2b` |
| `application` | Always `postgres` | `postgres` |
| `os.type` | Always `linux` | `linux` |

Here's a query to check that metrics are being collected as expected.

```sql
    SELECT metric, state, time, value
    FROM (
        SELECT
            RECORD['metric']['name']::VARCHAR AS metric,
            RECORD_ATTRIBUTES['state']::VARCHAR AS state,
            TIMESTAMP AS time,
            ROUND(VALUE::FLOAT, 2) AS value,
            ROW_NUMBER() OVER (
                PARTITION BY metric, state
                ORDER BY TIMESTAMP DESC
            ) AS rn
        FROM SNOWFLAKE.TELEMETRY.EVENTS
        WHERE RECORD_TYPE = 'METRIC'
          AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '<your_instance_id>'
          AND TIMESTAMP > DATEADD('minute', -5, CURRENT_TIMESTAMP())
    )
    WHERE rn = 1
    ORDER BY metric, state;
```

<!-- ------------------------ -->


## 3: Create Snowflake integration in Observe

In Observe, go to **Data & Integrations → Applications** and add the Snowflake application.

During this process, you will create an **ingest token**. Save this token — you'll need it later for the Snowflake secrets.

Derive your **ingest endpoint** from the customer ID in your Observe URL: `https://114765337208.observeinc.com`.

```
<CUSTOMER_ID>.collect.observeinc.com
```

Example: `114765337208.collect.observeinc.com`


## 4: Install the Observe Native App

Install **Observe for Snowflake** from the Snowflake Marketplace:

1. Go to **Data Products → Marketplace** in Snowsight
2. Search for "Observe for Snowflake"
3. Click **Get** and follow the prompts

Verify the installation:

```sql
SHOW APPLICATIONS LIKE 'OBSERVE_FOR_SNOWFLAKE';
```

## 5: Create Supporting Snowflake Objects

Create a database and schema to hold the secrets and network rule:

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS SEND_TO_OBSERVE;
CREATE SCHEMA IF NOT EXISTS SEND_TO_OBSERVE.O4S;
```

### 5a. Create Secrets

Store your Observe ingest token and endpoint as Snowflake secrets:

```sql
USE SCHEMA SEND_TO_OBSERVE.O4S;

CREATE OR REPLACE SECRET OBSERVE_TOKEN
  TYPE = GENERIC_STRING
  SECRET_STRING = '<YOUR_OBSERVE_INGEST_TOKEN>';

CREATE OR REPLACE SECRET OBSERVE_ENDPOINT
  TYPE = GENERIC_STRING
  SECRET_STRING = '<YOUR_CUSTOMER_ID>.collect.observeinc.com';
```

### 5b. Create Network Rule

Allow outbound HTTPS traffic to the Observe ingest endpoint:

```sql
CREATE OR REPLACE NETWORK RULE SEND_TO_OBSERVE.O4S.OBSERVE_INGEST_NETWORK_RULE
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('<YOUR_CUSTOMER_ID>.collect.observeinc.com');
```

### 5c. Create External Access Integration

```sql
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION OBSERVE_INGEST_ACCESS_INTEGRATION
  ALLOWED_NETWORK_RULES = (SEND_TO_OBSERVE.O4S.OBSERVE_INGEST_NETWORK_RULE)
  ALLOWED_AUTHENTICATION_SECRETS = (SEND_TO_OBSERVE.O4S.OBSERVE_TOKEN, SEND_TO_OBSERVE.O4S.OBSERVE_ENDPOINT)
  ENABLED = TRUE;
```

### 5d: Grant Permissions to the Observe App

Grant the app access to the warehouse, integration, and secrets:

```sql
USE ROLE ACCOUNTADMIN;

-- Warehouse (use your own warehouse name)
GRANT USAGE ON WAREHOUSE <YOUR_WAREHOUSE> TO APPLICATION OBSERVE_FOR_SNOWFLAKE;

-- External access integration
GRANT USAGE ON INTEGRATION OBSERVE_INGEST_ACCESS_INTEGRATION TO APPLICATION OBSERVE_FOR_SNOWFLAKE;

-- Secrets
GRANT USAGE ON DATABASE SEND_TO_OBSERVE TO APPLICATION OBSERVE_FOR_SNOWFLAKE;
GRANT USAGE ON SCHEMA SEND_TO_OBSERVE.O4S TO APPLICATION OBSERVE_FOR_SNOWFLAKE;
GRANT READ ON SECRET SEND_TO_OBSERVE.O4S.OBSERVE_TOKEN TO APPLICATION OBSERVE_FOR_SNOWFLAKE;
GRANT READ ON SECRET SEND_TO_OBSERVE.O4S.OBSERVE_ENDPOINT TO APPLICATION OBSERVE_FOR_SNOWFLAKE;
```

Grant the `EVENTS_ADMIN` application role so the app can read the event table:

```sql
USE ROLE SECURITYADMIN;
GRANT APPLICATION ROLE SNOWFLAKE.EVENTS_ADMIN TO APPLICATION OBSERVE_FOR_SNOWFLAKE;
```

### 5e: Enable Telemetry Event Sharing

Allow the app to access telemetry events:

```sql
USE ROLE ACCOUNTADMIN;

ALTER APPLICATION OBSERVE_FOR_SNOWFLAKE
  SET AUTHORIZE_TELEMETRY_EVENT_SHARING = TRUE;

ALTER APPLICATION OBSERVE_FOR_SNOWFLAKE
  SET SHARED TELEMETRY EVENTS ('SNOWFLAKE$ALL');
```

## 6: Configure via the Observe Snowflake App UI

Open the Observe app's UI:

1. Go to **Data Products → Apps** in Snowsight
2. Click **OBSERVE_FOR_SNOWFLAKE**
3. The app opens a Streamlit interface
4. Navigate to the **Configure** tab

The app also has a Setup Instructions tab for reference.

### 6a. Enter your Observe connection details (endpoint, token references)

  • External Access Integration: OBSERVE_INGEST_ACCESS_INTEGRATION
  • Token: SEND_TO_OBSERVE.O4S.OBSERVE_TOKEN
  • Endpoint: SEND_TO_OBSERVE.O4S.OBSERVE_ENDPOINT

Click **Configure** and wait for "Connected" status

### 6b. Bind the warehouse to the Observe app

1. Go to the **Permissions** tab
2. Click **Add** next to the object access privileges
3. Select your warehouse (e.g., `WH_XS`)
4. Click **Save**

> **Important**: The warehouse must be bound via the UI, not just granted via SQL. Without this binding, the app's internal tasks will not run.

### 6c. Add the Event Table

1. Still in the Observe Snowflake app UI, find the Event Table section
2. Add the event table using its fully qualified name: `SNOWFLAKE.TELEMETRY.EVENTS`
3. Confirm it saves successfully

You can also add it via SQL:

```sql
CALL OBSERVE_FOR_SNOWFLAKE.PUBLIC.ADD_EVENT_TABLE('SNOWFLAKE.TELEMETRY.EVENTS');
```

## 7: Verify Logs and Metrics in Observe

1. Log into your Observe UI
2. View the log event data and search for `postgres` 
3. View metrics in the panel, see drop down list for Postgres specific and system parameters 

> **Note**: There may be a 1-3 minute delay between data appearing in the Snowflake event table and showing up in Observe. The app sends data in chunks approximately every 60 seconds. Newly created pipelines may take several minutes to appear. 

From here, use the Observe tools to filter logs, build metrics dashboards, create monitors, and set up alerts.

## 8: Build Metrics and Dashboards in Observe

Using the metrics panel, you can now create queries and filters for exactly the metrics you want to view. You'll see a dropdown of available metrics. Metrics in a Snowflake event table typically have data for many different services, so each metric needs to be filtered for the specific Postgres resource. In the filter area, enter something like this:

```
RESOURCE_ATTRIBUTES.instance_id = "4jypgsndvzd5ta6ufaryx6owja"
```

With the full metric catalog available (see Section 2), a good starting point for basic Postgres health monitoring is:

- **`postgres_connections`** — Track active connections relative to your `max_connections` setting. A sustained climb toward the limit signals connection pool issues or application connection leaks.
- **`system.cpu.load_average.1m`** — Quick read on whether the instance is under CPU pressure. Load sustained above your vCPU count indicates saturation.
- **`system.filesystem.usage`** — Monitor disk consumption before it becomes an emergency.

![Observe sample dashboard](observe%20sample%20dashboard.png)

### Alerts 

Once your dashboards are in place, consider adding Observe monitors for:

- **Connection saturation** — Alert when `postgres_connections` crosses a percentage of `max_connections` (e.g., 80%).
- **CPU pressure** — Alert when `system.cpu.load_average.5m` stays above your vCPU count for a sustained period.
- **Disk usage** — Alert when `system.filesystem.usage` (state: `used`) exceeds a threshold relative to total disk.
- **Error spikes** — Alert on a sudden increase in `ERROR`, `FATAL`, or `PANIC` log events from the Postgres syslog stream.



<!-- ------------------------ -->
## Conclusion and Resources

You now have a monitoring pipeline that pushes Postgres logs and metrics from the Snowflake event table into Observe automatically. Because the Observe native app handles ingestion on a recurring schedule, there's no external infrastructure to manage — data flows as long as the app is configured and the warehouse is bound.

### What You Learned

- How to configure Postgres logging parameters on a Snowflake Postgres instance
- How the Snowflake event table captures and stores Postgres logs and metrics
- How to set up the Observe native app with the required Snowflake roles, grants, and network policies
- How to build metrics dashboards and set up monitoring in Observe

### Resources

- [Snowflake Postgres Logging](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-logging)
- [PostgreSQL Log Configuration Documentation](https://www.postgresql.org/docs/current/runtime-config-logging.html)
- [Observe Snowflake Integration Documentation](https://docs.observeinc.com/docs/snowflake)
- [Snowflake Event Table Documentation](https://docs.snowflake.com/en/developer-guide/logging-tracing/event-table-setting-up)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/tables-postgres)
- [Blog: Postgres Logging for Performance Optimization](https://www.crunchydata.com/blog/postgres-logging-for-performance-optimization)

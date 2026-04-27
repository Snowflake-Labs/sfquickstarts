author: Elizabeth Christensen
id: snowflake-postgres-monitoring-grafana
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Monitor Snowflake Postgres with Grafana dashboards using the Snowflake data source plugin and the native event table
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Monitor Snowflake Postgres with Grafana
<!-- ------------------------ -->
## Overview

This guide walks through setting up Postgres monitoring dashboards in Grafana using the Snowflake data source plugin. Grafana connects directly to Snowflake and queries the event table where Postgres logs are stored, giving you metrics, real-time dashboards, log exploration, and alerting without any intermediate pipeline.

Snowflake Postgres logs and metrics are routed through Snowflake's account-level event table at `SNOWFLAKE.TELEMETRY.EVENTS`. This table is the bridge between your Postgres instance and Grafana.

**What you'll build:** A Grafana monitoring setup where Snowflake Postgres logs and metrics can be queried directly from the event table and visualized in dashboards for basic instance monitoring, log exploration, slow query tracking, error monitoring, and connection activity.

---

### What You'll Learn

- How to configure Postgres logging parameters on a Snowflake Postgres instance
- How Snowflake's event table captures and stores Postgres logs and metrics
- How to create a dedicated Snowflake role and service user for Grafana
- How to install and configure the Grafana Snowflake data source plugin
- How to build Grafana dashboards for Postgres monitoring

### Prerequisites

- A **Snowflake account** with `ACCOUNTADMIN` access (needed for grants)
- A **Snowflake Postgres instance** in READY state (or ability to create one)
- A **Grafana Cloud** account (any tier) or a **Grafana Enterprise** instance with an activated license
- **OpenSSL** installed locally (for RSA key generation)
- **psql** installed locally (for testing connections)




<!-- ------------------------ -->
## 1. Enable Postgres Logging

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

> **Production vs. development trade-off:** `log_statement=all` generates a lot of log data and is generally not recommended for production workloads. For production, `ddl` combined with `log_min_duration_statement` for slow queries gives you the important details without the volume. For this guide, we use `all` so every test query is visible in Grafana.

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
## 2. Confirm Logs and Metrics in the Snowflake Event Table

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
## 3. Create the Snowflake Role and Grants

Grafana connects to Snowflake as a dedicated role with specific privileges. This role needs access to the event table and a warehouse to run queries.

```sql
USE ROLE ACCOUNTADMIN;

-- Create the Grafana role
CREATE ROLE IF NOT EXISTS GRAFANA;
GRANT ROLE GRAFANA TO ROLE ACCOUNTADMIN;

-- Grant IMPORTED PRIVILEGES on the SNOWFLAKE database
-- Required for Grafana to read the event table.
-- USAGE alone is NOT sufficient — you must use IMPORTED PRIVILEGES.
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE GRAFANA;

-- Grant warehouse usage (replace with your warehouse name)
GRANT USAGE ON WAREHOUSE MY_WAREHOUSE TO ROLE GRAFANA;
```

Note that `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` grant is `ACCOUNTADMIN` only with no workaround. Some other SQL could be done with lower permissions. 

### Create a Proxy View for Grafana

The Grafana Snowflake plugin requires a database and schema context for its connection. The `SNOWFLAKE.TELEMETRY` schema uses `IMPORTED PRIVILEGES`, which is incompatible with the plugin's `USE SCHEMA` connection test. To work around this, create a dedicated database with a view that references the event table:

```sql
-- Create a database and schema for Grafana
CREATE DATABASE IF NOT EXISTS GRAFANA_DB;
CREATE SCHEMA IF NOT EXISTS GRAFANA_DB.MONITORING;

-- Create a view that filters to Postgres syslog events
CREATE OR REPLACE VIEW GRAFANA_DB.MONITORING.POSTGRES_LOGS AS
SELECT *
FROM SNOWFLAKE.TELEMETRY.EVENTS
WHERE RECORD_TYPE = 'LOG'
  AND RESOURCE_ATTRIBUTES['service.name']::STRING = 'postgres_syslog';

-- Grant access to the Grafana role
GRANT USAGE ON DATABASE GRAFANA_DB TO ROLE GRAFANA;
GRANT USAGE ON SCHEMA GRAFANA_DB.MONITORING TO ROLE GRAFANA;
GRANT SELECT ON VIEW GRAFANA_DB.MONITORING.POSTGRES_LOGS TO ROLE GRAFANA;
```

This view also simplifies your Grafana queries — you won't need to repeat the `RECORD_TYPE` and `service.name` filters in every panel.

Verify the grants:

```sql
SHOW GRANTS TO ROLE GRAFANA;
```

<!-- ------------------------ -->
## 4. Generate RSA Key Pair

The Grafana Snowflake plugin supports RSA key-pair authentication, which is more secure than password auth for service accounts. You'll generate a key pair, give the public key to Snowflake, and give the private key to Grafana.

### Generate the Keys

```bash
mkdir -p ~/.snowflake/grafana_keys

# Generate an unencrypted RSA private key (PKCS#8 format)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out ~/.snowflake/grafana_keys/grafana_rsa_key.p8 -nocrypt

# Extract the public key
openssl rsa -in ~/.snowflake/grafana_keys/grafana_rsa_key.p8 -pubout -out ~/.snowflake/grafana_keys/grafana_rsa_key.pub
```

### Get the Public Key Value (for Snowflake)

```bash
# Print the public key without the header/footer lines (this is what Snowflake expects)
grep -v "BEGIN\|END" ~/.snowflake/grafana_keys/grafana_rsa_key.pub | tr -d '\n'
```

Copy the output — you'll paste it into the `ALTER USER` command in the next step.

### Get the Private Key (for Grafana)

```bash
# Print the full private key including headers (Grafana needs the complete PEM block)
cat ~/.snowflake/grafana_keys/grafana_rsa_key.p8
```

Copy this entire output including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines — you'll paste it into Grafana.

<!-- ------------------------ -->
## 5. Create the Snowflake Service User

Create a dedicated service user for Grafana. This user authenticates with the RSA key pair (no password).

> **Key distinction:** `GRAFANA` is the **role**. `GRAFANA_USER` is the **user**. When configuring the Grafana data source, you'll enter `GRAFANA_USER` as the username and `GRAFANA` as the role.

```sql
USE ROLE ACCOUNTADMIN;

CREATE USER IF NOT EXISTS GRAFANA_USER
  TYPE = SERVICE
  DEFAULT_ROLE = GRAFANA
  DEFAULT_WAREHOUSE = MY_WAREHOUSE
  DEFAULT_NAMESPACE = GRAFANA_DB.MONITORING;

-- Assign the RSA public key (paste the key value from Step 4)
ALTER USER GRAFANA_USER SET RSA_PUBLIC_KEY = '<paste_public_key_here>';

-- Grant the GRAFANA role to the user
GRANT ROLE GRAFANA TO USER GRAFANA_USER;
```

<!-- ------------------------ -->
## 6. Install and Configure the Grafana Snowflake Data Source

Unlike other log pipeline services, Grafana queries Snowflake directly — there's no separate ingestion pipeline. The Snowflake data source plugin connects to your account and runs SQL queries on demand when you load a dashboard or explore logs.

### Install the Plugin

**Grafana Cloud:** The Snowflake plugin is available in the plugin catalog. Go to **Connections > Add new connection**, search for "Snowflake", and click **Install**.

**Self-managed Grafana Enterprise:** Install via the CLI:

```bash
grafana-cli plugins install grafana-snowflake-datasource
```

Then restart Grafana.

### Configure the Data Source

1. In Grafana, go to **Connections > Data sources**
2. Click **Add new data source**
3. Search for and select **Snowflake**
4. Fill in the fields:

| Field | Value |
|---|---|
| **Account** | Your Snowflake account identifier (e.g., `myorg-myaccount`) |
| **Username** | `GRAFANA_USER` |
| **Authentication Type** | Key Pair |
| **Private Key** | Paste the full PEM private key from Step 4 |
| **Role** | `GRAFANA` |
| **Warehouse** | `MY_WAREHOUSE` (your warehouse name) |
| **Database** | `GRAFANA_DB` |
| **Schema** | `MONITORING` |

> **Important:** Use the `GRAFANA_DB` database and `MONITORING` schema (the proxy view from Step 3) — not `SNOWFLAKE` / `TELEMETRY`. The Grafana plugin's connection test runs `USE SCHEMA`, which fails against schemas accessed via `IMPORTED PRIVILEGES`. The proxy view avoids this issue entirely.

5. Click **Save & test**

You should see "Data source is working."

<!-- ------------------------ -->
## 7. Explore Postgres Logs in Grafana

With the data source connected, you can start exploring Postgres logs immediately using Grafana's Explore view.

### Basic Log Exploration

1. Go to **Explore** in Grafana
2. Select your Snowflake data source
3. Set the visualization to **Table** (log queries return text, not numeric data for graphs)
4. Enter the following query to see recent Postgres logs:

```sql
SELECT
    TIMESTAMP AS time,
    VALUE['SEVERITY_TEXT']::STRING AS level,
    VALUE['MESSAGE']::STRING AS message,
    RESOURCE_ATTRIBUTES['instance.id']::STRING AS instance_id
FROM POSTGRES_LOGS
WHERE $__timeFilter(TIMESTAMP)
ORDER BY TIMESTAMP DESC
```

> **Grafana macros:** `$__timeFilter(TIMESTAMP)` is a Grafana macro that expands to a time range filter on the specified column, based on the time picker in the dashboard UI. This replaces the need to manually write `TIMESTAMP > $__timeFrom AND TIMESTAMP < $__timeTo`.

### Filter by Instance

If you have multiple Postgres instances, add an instance filter:

```sql
SELECT
    TIMESTAMP AS time,
    VALUE['SEVERITY_TEXT']::STRING AS level,
    VALUE['MESSAGE']::STRING AS message
FROM POSTGRES_LOGS
WHERE $__timeFilter(TIMESTAMP)
  AND RESOURCE_ATTRIBUTES['instance.id']::STRING = '<YOUR_INSTANCE_ID>'
ORDER BY TIMESTAMP DESC
```

### Errors and Warnings Only

```sql
SELECT
    TIMESTAMP AS time,
    VALUE['SEVERITY_TEXT']::STRING AS level,
    VALUE['MESSAGE']::STRING AS message
FROM POSTGRES_LOGS
WHERE $__timeFilter(TIMESTAMP)
  AND VALUE['SEVERITY_TEXT']::STRING IN ('ERROR', 'FATAL', 'PANIC', 'WARNING')
ORDER BY TIMESTAMP DESC
```

<!-- ------------------------ -->
## 8. Build a Postgres Monitoring Dashboard

Create a dedicated dashboard to monitor your Postgres instances. Go to **Dashboards > New dashboard** and add panels using the queries below. Here are a few samples of queries to get started. Please test and refine these for your particular instance and use case. 

### CPU usage and I/O wait

```sql
    SELECT time, metric, pct FROM (
        SELECT
            TIMESTAMP AS time,
            CASE RECORD_ATTRIBUTES['state']::VARCHAR
                WHEN 'wait' THEN 'I/O Wait'
                WHEN 'user' THEN 'User'
                WHEN 'system' THEN 'System'
            END AS metric,
            VALUE::FLOAT AS val,
            LAG(VALUE::FLOAT) OVER (
                PARTITION BY RECORD_ATTRIBUTES['state']::VARCHAR
                ORDER BY TIMESTAMP
            ) AS prev_val,
            DATEDIFF('second',
                LAG(TIMESTAMP) OVER (
                    PARTITION BY RECORD_ATTRIBUTES['state']::VARCHAR
                    ORDER BY TIMESTAMP
                ), TIMESTAMP) AS interval_secs,
            CASE WHEN interval_secs > 0
                THEN (val - prev_val) / interval_secs * 100
                ELSE NULL
            END AS pct
        FROM POSTGRES_METRICS
        WHERE RECORD['metric']['name']::VARCHAR = 'system.cpu.time'
          AND RECORD_ATTRIBUTES['state']::VARCHAR IN ('user', 'system', 'wait')
          AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '4jypgsndvzd5ta6ufaryx6owja'
          AND $__timeFilter(TIMESTAMP)
    )
    WHERE pct IS NOT NULL AND pct >= 0
    ORDER BY time
```

### CPU load

```sql
    SELECT
        TIMESTAMP AS time,
        RECORD['metric']['name']::VARCHAR AS metric,
        VALUE::FLOAT AS load_avg
    FROM POSTGRES_METRICS
    WHERE RECORD['metric']['name']::VARCHAR IN (
            'system.cpu.load_average.1m',
            'system.cpu.load_average.5m',
            'system.cpu.load_average.15m'
        )
      AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '4jypgsndvzd5ta6ufaryx6owja'
      AND $__timeFilter(TIMESTAMP)
    ORDER BY time;
```


### Memory Usage by State

```sql
    SELECT
        TIMESTAMP AS time,
        RECORD_ATTRIBUTES['state']::VARCHAR AS metric,
        VALUE::FLOAT / (1024*1024*1024) AS usage_gb
    FROM POSTGRES_METRICS
    WHERE RECORD['metric']['name']::VARCHAR = 'system.memory.usage'
      AND RECORD_ATTRIBUTES['state']::VARCHAR IN ('used', 'cached', 'buffered', 'free')
      AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '4jypgsndvzd5ta6ufaryx6owja'
      AND $__timeFilter(TIMESTAMP)
    ORDER BY time;
```

### Percent of Disk Used

```sql
    SELECT * FROM (
        SELECT
            'Database' AS label,
            ROUND(VALUE::FLOAT / (1024*1024), 1) AS size_mb
        FROM POSTGRES_METRICS
        WHERE RECORD['metric']['name']::VARCHAR = 'postgres_databases_size_bytes'
          AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '4jypgsndvzd5ta6ufaryx6owja'
          AND $__timeFilter(TIMESTAMP)
        ORDER BY TIMESTAMP DESC
        LIMIT 1
    )

    UNION ALL

    SELECT * FROM (
        SELECT
            'Total Disk' AS label,
            ROUND(SUM(VALUE::FLOAT) / (1024*1024), 1) AS size_mb
        FROM POSTGRES_METRICS
        WHERE RECORD['metric']['name']::VARCHAR = 'system.filesystem.usage'
          AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '4jypgsndvzd5ta6ufaryx6owja'
          AND $__timeFilter(TIMESTAMP)
        GROUP BY TIMESTAMP
        ORDER BY TIMESTAMP DESC
        LIMIT 1
    )
    ;
```


### Active connections

```sql
    SELECT VALUE::FLOAT AS connections
    FROM POSTGRES_METRICS
    WHERE RECORD['metric']['name']::VARCHAR = 'postgres_connections'
      AND RESOURCE_ATTRIBUTES['instance_id']::VARCHAR = '4jypgsndvzd5ta6ufaryx6owja'
      AND $__timeFilter(TIMESTAMP)
    ORDER BY TIMESTAMP DESC
    LIMIT 1;
```    

### Sample dashboard view

![Grafana sample dashboard](assets/snowflake-postgres-grafana-sample-dashboard.png)

<!-- ------------------------ -->
## Conclusion and Resources

You now have a Grafana monitoring setup that queries Postgres logs and metrics directly from the Snowflake event table. Because Grafana pulls data on demand rather than requiring a separate ingestion pipeline, you can start exploring logs and metrics immediately and iterate on dashboards without any additional infrastructure.

### What You Learned

- How to configure Postgres logging parameters on a Snowflake Postgres instance
- How the Snowflake event table captures and stores Postgres logs and metrics
- How to create a dedicated Snowflake role and service user for Grafana
- How to install and configure the Grafana Snowflake data source plugin with key-pair auth
- How to build monitoring dashboards from Postgres metrics

### Next Steps

- **Set up Grafana alerts:** Use [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/) to get notified on error spikes, FATAL/PANIC events, or other Postgres log patterns by querying the same Snowflake data source used in your dashboards.

### Resources

- [Snowflake Postgres Logging](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-logging)
- [PostgreSQL Log Configuration Documentation](https://www.postgresql.org/docs/current/runtime-config-logging.html)
- [Grafana Snowflake Data Source Plugin](https://grafana.com/docs/plugins/grafana-snowflake-datasource/latest/)
- [Grafana Snowflake Plugin Configuration](https://grafana.com/docs/plugins/grafana-snowflake-datasource/latest/configure/)
- [Snowflake Event Table Documentation](https://docs.snowflake.com/en/developer-guide/logging-tracing/event-table-setting-up)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/tables-postgres)
- [Blog: Postgres Logging for Performance Optimization](https://www.crunchydata.com/blog/postgres-logging-for-performance-optimization)

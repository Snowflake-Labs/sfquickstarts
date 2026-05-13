author: Elizabeth Christensen
id: snowflake-postgres-logs-to-datadog
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Stream Postgres logs from Snowflake into Datadog using the native event table
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Monitor Snowflake Postgres Logs with Datadog
<!-- ------------------------ -->
## Overview

This guide walks through the full end-to-end setup for streaming logs from a Snowflake Postgres instance into Datadog using Snowflake's native event table and Datadog's Snowflake integration.

Snowflake Postgres logs are routed through Snowflake's account-level event table at `SNOWFLAKE.TELEMETRY.EVENTS`. This table is the bridge between your Postgres instance and Datadog.

**What you'll build:** A pipeline where Snowflake Postgres logs are captured in Snowflake's event table and automatically ingested into Datadog's Log Explorer for monitoring, searching, and alerting.

---

### What You'll Learn

- How to configure Postgres logging parameters on a Snowflake Postgres instance
- How Snowflake's event table captures and stores Postgres logs
- How to set up Snowflake roles, grants, and network policies for Datadog
- How to configure Datadog's Snowflake integration for log ingestion
- How to verify logs flow end-to-end from Postgres to Datadog

### Prerequisites

- A **Snowflake account** with `ACCOUNTADMIN` access (needed for grants and network policies)
- A **Snowflake Postgres instance** in READY state (or ability to create one)
- A **Datadog account** with admin access to configure integrations
- **OpenSSL** installed locally (for RSA key generation)
- **psql** installed locally (for testing connections)

> **Know your Datadog site.** This guide uses placeholder values. Replace them with your site-specific values (US1, US3, US5, EU1, AP1). Your site determines the IP ranges to whitelist and the Datadog URLs.

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

> **Production vs. development trade-off:** `log_statement=all` generates a lot of log data and is generally not recommended for production workloads. For production, `ddl` combined with `log_min_duration_statement` for slow queries gives you the important details without the volume. For this guide, we use `all` so every test query is visible in Datadog.

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
## 2. Confirm Logs in the Snowflake Event Table

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

<!-- ------------------------ -->
## 3. Create the Snowflake Role and Grants

Datadog connects to Snowflake as a dedicated role with specific privileges. This role needs access to account usage, monitoring, and the event table.

```sql
-- Use ACCOUNTADMIN to create the role and assign grants
USE ROLE ACCOUNTADMIN;

-- Create the Datadog role
CREATE ROLE IF NOT EXISTS DATADOG;
GRANT ROLE DATADOG TO ROLE ACCOUNTADMIN;

-- CRITICAL: Grant IMPORTED PRIVILEGES on the SNOWFLAKE database
-- This is required for Datadog to read the event table and account usage views.
-- Using just USAGE is NOT sufficient -- you must use IMPORTED PRIVILEGES.
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE DATADOG;

-- Grant monitoring access
GRANT MONITOR USAGE ON ACCOUNT TO ROLE DATADOG;

-- Grant warehouse usage (replace with your warehouse name)
GRANT USAGE ON WAREHOUSE MY_WAREHOUSE TO ROLE DATADOG;
```

Note that `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` grant is `ACCOUNTADMIN` only with no workaround. Some other SQL could be done with lower permissions. 

```sql
SHOW GRANTS TO ROLE DATADOG;
```

<!-- ------------------------ -->
## 4. Generate RSA Key Pair

Datadog authenticates to Snowflake using RSA key-pair authentication (not password). You'll generate a key pair, give the public key to Snowflake, and give the private key to Datadog.

### Generate the Keys

```bash
# Create a directory for the keys
mkdir -p ~/.snowflake/datadog_keys

# Generate an unencrypted RSA private key (PKCS#8 format)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out ~/.snowflake/datadog_keys/datadog_rsa_key.p8 -nocrypt

# Extract the public key
openssl rsa -in ~/.snowflake/datadog_keys/datadog_rsa_key.p8 -pubout -out ~/.snowflake/datadog_keys/datadog_rsa_key.pub
```

### Get the Public Key Value (for Snowflake)

```bash
# Print the public key without the header/footer lines (this is what Snowflake expects)
grep -v "BEGIN\|END" ~/.snowflake/datadog_keys/datadog_rsa_key.pub | tr -d '\n'
```

Copy the output -- you'll paste it into the `ALTER USER` command in the next step.


<!-- ------------------------ -->
## 5. Create the Snowflake Service User

Create a dedicated service user for Datadog. This user authenticates with the RSA key pair (no password).

> **Key distinction:** `DATADOG` is the **role**. `DATADOG_USER` is the **user**. When configuring Datadog, you'll enter `DATADOG_USER` as the username and `DATADOG` as the role. Mixing these up is a common source of "integration broken" errors.

```sql
USE ROLE ACCOUNTADMIN;

-- Create the service user
CREATE USER IF NOT EXISTS DATADOG_USER
  TYPE = SERVICE
  DEFAULT_ROLE = DATADOG
  DEFAULT_WAREHOUSE = MY_WAREHOUSE
  DEFAULT_NAMESPACE = SNOWFLAKE.TELEMETRY;

-- Assign the RSA public key (paste the key value from Step 4)
ALTER USER DATADOG_USER SET RSA_PUBLIC_KEY = '<paste_public_key_here>';

-- Grant the DATADOG role to the user
GRANT ROLE DATADOG TO USER DATADOG_USER;
```

<!-- ------------------------ -->
## 6. Add Network Permissions for Datadog

Datadog connects to your Snowflake account to poll for data. If your account or Postgres instance has network policies in place, you need to whitelist Datadog's IP ranges so these connections are allowed.

### Find Your Datadog Site's IP Ranges

Datadog publishes its IP ranges at a site-specific URL. The ranges you need are under the webhooks section.

| Datadog Site | IP Ranges URL |
|---|---|
| US1 | `https://ip-ranges.datadoghq.com/` |
| US3 | `https://ip-ranges.us3.datadoghq.com/` |
| US5 | `https://ip-ranges.us5.datadoghq.com/` |
| EU1 | `https://ip-ranges.datadoghq.eu/` |
| AP1 | `https://ip-ranges.ap1.datadoghq.com/` |

Open the URL for your site and look for the `webhooks.prefixes_ipv4` array. These are the CIDR ranges to whitelist.

**Example (US5 as of writing):**
- `34.149.66.128/26`
- `34.160.40.115/32`
- `35.244.255.175/32`

> **Check this URL regularly.** Datadog may add new IP ranges over time. If your integration stops working, check for updated IPs.

### Create the Network Rules

You need both ingress (Datadog connecting to Snowflake) and egress (Snowflake responding to Datadog) rules:

```sql
USE ROLE ACCOUNTADMIN;

-- Ingress rule: allows Datadog to connect to Snowflake
CREATE OR REPLACE NETWORK RULE DATADOG_INGRESS
  TYPE = IPV4
  MODE = INGRESS
  VALUE_LIST = (
    '34.149.66.128/26',
    '34.160.40.115/32',
    '35.244.255.175/32'
  );

-- Egress rule: allows Snowflake to respond to Datadog
CREATE OR REPLACE NETWORK RULE DATADOG_EGRESS
  TYPE = IPV4
  MODE = EGRESS
  VALUE_LIST = (
    '34.149.66.128/26',
    '34.160.40.115/32',
    '35.244.255.175/32'
  );

-- Create a network policy using both rules
CREATE OR REPLACE NETWORK POLICY DATADOG_NETWORK_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('DATADOG_INGRESS', 'DATADOG_EGRESS');

-- Assign the policy to the Datadog user
ALTER USER DATADOG_USER SET NETWORK_POLICY = 'DATADOG_NETWORK_POLICY';
```

> **Scope the policy to the user, not the account.** Applying a network policy at the account level could lock out other users. Apply it only to `DATADOG_USER`.

> **Note:** Datadog may add or change IP ranges over time. When this happens, update your existing network rules rather than recreating the policy.

<!-- ------------------------ -->
## 7. Configure the Datadog Snowflake Integration

Now configure Datadog to connect to your Snowflake account using the role, user, and key you've set up.

1. Log into your Datadog account
2. Navigate to **Integrations** > **Integrations** (or search for "Snowflake")
3. Click the **Snowflake** integration tile
4. Click **+ Add Account**
5. Fill in the fields:

- **Account URL**: `<your-account>.snowflakecomputing.com`
- **Username**: `DATADOG_USER` 

6. Under **Data Collection**, enable the settings you'd like for your account. Make sure that **Events Records:** is toggled on — these are the Postgres logs.

7. Upload the private key file from above.

8. Click **Save**

### Account URL Format

This can be a common source of errors. Datadog normalizes underscores to hyphens in URLs, which can break the connection for accounts with underscores in their name.

**Use one of these formats:**

| Format | Example | Notes |
|---|---|---|
| **Connection alias** (recommended) | `myorg-myalias.snowflakecomputing.com` | Most reliable if you have one set up |
| **Legacy locator** | `myaccount.us-west-2.snowflakecomputing.com` | Include the region |
| **Org-account (regionless)** | `myorg-myaccount.snowflakecomputing.com` | May fail if account name has underscores |

> **If your account name contains underscores** (e.g., `MY_ACCOUNT`), Datadog may convert it to `MY-ACCOUNT` in the URL, causing authentication to fail. Use a connection alias or the legacy locator format to work around this.

**To create a connection alias in Snowflake:**

```sql
-- Via Snowsight: Admin > Accounts > select account > Create Connection
-- Or via SQL:
CREATE CONNECTION MY_ALIAS;
ALTER CONNECTION MY_ALIAS SET COMMENT = 'Alias for Datadog integration';
```

<!-- ------------------------ -->
## 8. Generate Test Logs and Verify

With everything configured, generate some test traffic against your Postgres instance and verify the logs flow through to Datadog. See the above steps for generating data and checking the event table.

### Verify in Datadog

1. Navigate to **Logs** > **Log Explorer** in Datadog
2. Search for `postgres` in the search bar to see logs being generated for the Postgres service.
3. You should see log entries with the SQL queries you ran. Filter by some of your sample query syntax like `cookie_monster` to make sure you're seeing logs that you expect.

> **Timing:** Datadog polls the event table at the interval you configured. If you set it to 1 hour, it may take up to an hour for new logs to appear. For testing, consider temporarily reducing the interval.

From here you can use Datadog's tools to search, filter, and create alerts around the Postgres logs. 


Snowflake Postgres also sends `RECORD_TYPE = 'METRIC'` to the event table, in addition to `RECORD_TYPE = 'LOG'`. Currently the Datadog web integration does not support metrics. However, events could be ingested through other API processes or agents. See [metrics API](https://docs.datadoghq.com/api/latest/metrics/) and [metric submission](https://docs.datadoghq.com/metrics/custom_metrics/dogstatsd_metrics_submission/?tab=python) for more details.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've built an end-to-end pipeline that streams Postgres logs from Snowflake into Datadog for monitoring, searching, and alerting.

### What You Learned

- How to configure Postgres logging parameters on a Snowflake Postgres instance
- How the Snowflake event table captures and stores Postgres logs
- How to create a dedicated Snowflake role and service user for Datadog with the correct grants
- How to generate and configure RSA key-pair authentication
- How to whitelist Datadog's IP ranges with Snowflake network policies
- How to configure and verify the Datadog Snowflake integration
 

### Resources

- [Snowflake Postgres Logging](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-logging)
- [PostgreSQL Log Configuration Documentation](https://www.postgresql.org/docs/current/runtime-config-logging.html)
- [Datadog Snowflake Integration Documentation](https://docs.datadoghq.com/integrations/snowflake/)
- [Snowflake Event Table Documentation](https://docs.snowflake.com/en/developer-guide/logging-tracing/event-table-setting-up)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/tables-postgres)
- [Blog: Postgres Logging for Performance Optimization](https://www.crunchydata.com/blog/postgres-logging-for-performance-optimization)

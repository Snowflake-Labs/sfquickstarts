author: Akhil Ramasagaram
id: dagster-plus-snowflake-assets-mcp
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/partner-solution, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Build one Snowflake asset with Dagster's dg CLI, materialize it with a key pair, ask the Dagster+ MCP server what ran, and read warehouse credits per asset.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Build a Snowflake asset with Dagster and query it from an agent

## Overview

This guide builds one Snowflake table as a Dagster asset, materializes it from the terminal with key-pair authentication, asks the Dagster+ MCP server which runs succeeded, and reads the warehouse credits Snowflake attributes to those queries.

It does not cover dbt, S3 ingestion, or schedules. That path is already published as [Data Engineering with Dagster, dbt, and Snowflake](https://www.snowflake.com/en/developers/guides/data-engineering-with-dagster-dbt-snowflake/).

### Prerequisites

Python, SQL, and a terminal. No prior Dagster experience.

### What You'll Learn

- How to create the Snowflake objects a Dagster run needs
- How to authenticate with an encrypted key pair instead of a password
- How to scaffold a Dagster project and materialize one asset
- How to connect an agent to the Dagster+ MCP server
- How to grant the database role that includes the Account Usage views, and which credit column to read

### What You'll Need

1. A Snowflake account, and `ACCOUNTADMIN` to create the role, user, warehouse, and database
2. Python 3.11 or newer
3. [uv](https://docs.astral.sh/uv/getting-started/installation/)
4. A Dagster+ Pro organization, only for the MCP and Insights steps
5. An MCP client. This guide uses Claude Code

### What You'll Build

One table, `DEMO.PUBLIC.DAILY_ROW`, created by a Dagster asset and materialized with `dg launch`.

## Set Up Snowflake

Sign in as `ACCOUNTADMIN` and run this in a worksheet. It creates an XSmall warehouse, a database, a role, and a user that authenticates with a public key.

```sql
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS DAGSTER_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS DEMO;

CREATE ROLE IF NOT EXISTS DAGSTER_ROLE;
GRANT USAGE ON WAREHOUSE DAGSTER_WH TO ROLE DAGSTER_ROLE;
GRANT USAGE ON DATABASE DEMO TO ROLE DAGSTER_ROLE;
GRANT USAGE ON SCHEMA DEMO.PUBLIC TO ROLE DAGSTER_ROLE;
GRANT CREATE TABLE ON SCHEMA DEMO.PUBLIC TO ROLE DAGSTER_ROLE;

CREATE USER IF NOT EXISTS DAGSTER_USER
  DEFAULT_ROLE = DAGSTER_ROLE
  DEFAULT_WAREHOUSE = DAGSTER_WH
  RSA_PUBLIC_KEY = '<PUBLIC_KEY>';

GRANT ROLE DAGSTER_ROLE TO USER DAGSTER_USER;
```

The Dagster Snowflake integration only supports an encrypted private key. Generate the key pair on your machine. `openssl` asks for a passphrase twice. Type it at the prompt. Do not put it on the command line.

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 des3 -inform PEM -out rsa_key.p8
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

The second command asks for the passphrase once. Put the public key in `RSA_PUBLIC_KEY` above as a single line, with the header and footer removed.

Confirm the fingerprint Snowflake stored matches the key you generated. `openssl` asks for the passphrase again.

```sql
DESC USER DAGSTER_USER;
```

```bash
openssl rsa -in rsa_key.p8 -pubout -outform DER | openssl dgst -sha256 -binary | openssl enc -base64
```

The `RSA_PUBLIC_KEY_FP` property and the fingerprint must match. Do not commit `rsa_key.p8` or `rsa_key.pub`.

## Create the Dagster project

```bash
uvx create-dagster@latest project dagster_snowflake_asset
cd dagster_snowflake_asset
uv add dagster-snowflake cryptography
source .venv/bin/activate
```

`create-dagster` installs `dg` into the project environment. `dg --version` confirms it.

## Define the asset

Scaffold the asset, then replace the file it writes.

```bash
dg scaffold defs dagster.asset assets/daily_row.py
```

That creates `src/dagster_snowflake_asset/defs/assets/daily_row.py`. Replace its contents with this. `private_key_path` points at the encrypted key, and `private_key_password` comes from the environment.

```python
import dagster as dg
from dagster_snowflake import SnowflakeResource


@dg.asset
def daily_row(snowflake: SnowflakeResource) -> dg.MaterializeResult:
    with snowflake.get_connection() as conn:
        conn.cursor().execute(
            "CREATE OR REPLACE TABLE DEMO.PUBLIC.DAILY_ROW AS "
            "SELECT CURRENT_DATE() AS RUN_DATE, 1 AS ROW_COUNT"
        )
    return dg.MaterializeResult(metadata={"table": "DEMO.PUBLIC.DAILY_ROW"})


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "snowflake": SnowflakeResource(
                account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                user=dg.EnvVar("SNOWFLAKE_USER"),
                private_key_path=dg.EnvVar("SNOWFLAKE_PRIVATE_KEY_PATH"),
                private_key_password=dg.EnvVar("SNOWFLAKE_PK_PASSWORD"),
                role="DAGSTER_ROLE",
                warehouse="DAGSTER_WH",
                database="DEMO",
                schema="PUBLIC",
            )
        }
    )
```

`CREATE OR REPLACE` rebuilds the table on every materialization, which makes the result easy to rerun. It also drops grants on that table.

Set the connection values in the shell, then check that the definitions load. `SNOWFLAKE_PK_PASSWORD` is the passphrase you typed when you encrypted the key.

```bash
export SNOWFLAKE_ACCOUNT="<account_identifier>"
export SNOWFLAKE_USER="DAGSTER_USER"
export SNOWFLAKE_PRIVATE_KEY_PATH="$PWD/rsa_key.p8"
export SNOWFLAKE_PK_PASSWORD="<passphrase>"
dg check defs
```

`SNOWFLAKE_ACCOUNT` is the account identifier, such as `xy12345.us-east-2.aws`. It is not the URL and it has no `https://`.

## Materialize the asset

```bash
dg launch --assets daily_row
```

A successful run ends with the run id and a success status. Read the table back in a worksheet.

```sql
USE ROLE DAGSTER_ROLE;
USE WAREHOUSE DAGSTER_WH;
SELECT * FROM DEMO.PUBLIC.DAILY_ROW;
```

The result is one row, today's date, and `ROW_COUNT` of 1.

## Ask the Dagster+ MCP server what ran

The remaining steps need Dagster+ Pro. The MCP server is in beta. It can list runs, read run logs, and launch a run. It cannot edit or delete an asset. Its permissions are the permissions of the user whose token you pass.

The server URL is `https://mcp.agent.dagster.cloud/mcp` for a US organization and `https://mcp.agent.eu.dagster.cloud/mcp` for an EU organization. Add it with a [user token](https://docs.dagster.io/dagster-plus/account/authentication/user-tokens) and the organization name.

```bash
claude mcp add --transport http dagster-plus https://mcp.agent.dagster.cloud/mcp \
  --header "Dagster-Cloud-Organization: <ORG>" \
  --header "Authorization: Bearer <TOKEN>"
```

In a Claude Code session, run `/mcp` and confirm `dagster-plus` is connected. Then ask:

```text
Which Dagster runs materialized daily_row, and which of them failed?
```

The answer lists the run you just launched. To have the agent materialize it again, ask it to launch a run for the `daily_row` asset. The server has a launch tool. It has no edit or delete tool.

If the client is Codex, the command is `codex mcp add dagster-plus --url https://mcp.agent.dagster.cloud/mcp`, and Codex runs the OAuth flow itself.

## Grant the role that includes the usage views

Dagster+ Insights reads `SNOWFLAKE.ACCOUNT_USAGE` to attribute Snowflake usage to an asset. The Insights docs say the credentials need access to `snowflake.account_usage.query_history`. A `SELECT` grant on that view is rejected. `SNOWFLAKE.GOVERNANCE_VIEWER` is the narrowest database role that includes `QUERY_HISTORY` and `QUERY_ATTRIBUTION_HISTORY`. The Insights docs do not name this role.

```sql
USE ROLE ACCOUNTADMIN;
GRANT DATABASE ROLE SNOWFLAKE.GOVERNANCE_VIEWER TO ROLE DAGSTER_ROLE;
```

That role also includes `ACCESS_HISTORY`, the policy views, and the billing document views. It is not access to one view.

The warehouse credit column is `SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY.CREDITS_ATTRIBUTED_COMPUTE`. It attributes warehouse credits to a query, a warehouse, a user, and a query tag. It does not include warehouse idle time, serverless credits, cloud services, or storage. After the asset has run, this returns the queries the role executed and the credits attributed to them.

```sql
SELECT query_id, user_name, warehouse_name, credits_attributed_compute
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY
WHERE user_name = 'DAGSTER_USER'
ORDER BY start_time DESC
LIMIT 20;
```

Account Usage lags about 45 minutes, and this view is retained for a year. Dagster+ Insights has its own limits: usage data can take up to 24 hours to appear, and external metrics are kept for 120 days.

## Clean up

```sql
USE ROLE ACCOUNTADMIN;
DROP USER IF EXISTS DAGSTER_USER;
DROP ROLE IF EXISTS DAGSTER_ROLE;
DROP DATABASE IF EXISTS DEMO;
DROP WAREHOUSE IF EXISTS DAGSTER_WH;
```

Delete `rsa_key.p8` and `rsa_key.pub` from the project directory.

## Conclusion

The project has one asset, an encrypted key pair instead of a password, and a table you can select. The MCP server answers questions about the run that created it, and `CREDITS_ATTRIBUTED_COMPUTE` is the warehouse credit column for those queries.

### What You Learned

- The Snowflake role needs `USAGE` on the warehouse, database, and schema, and `CREATE TABLE` on the schema
- `SnowflakeResource` accepts an encrypted private key and its passphrase in place of a password
- `dg launch --assets daily_row` materializes the asset from the terminal
- The Dagster+ MCP server can list runs and launch one, and it cannot edit or delete an asset
- `GRANT DATABASE ROLE SNOWFLAKE.GOVERNANCE_VIEWER` is the narrowest grant that includes the views a `SELECT` on `query_history` cannot reach

## Resources

- [Using Snowflake with Dagster](https://docs.dagster.io/integrations/libraries/snowflake/using-snowflake-with-dagster)
- [dagster-snowflake integration reference](https://docs.dagster.io/integrations/libraries/snowflake/reference)
- [Dagster+ MCP server](https://docs.dagster.io/getting-started/ai-tools/dagster-mcp)
- [Track Snowflake usage with Dagster+ Insights](https://docs.dagster.io/guides/observe/insights/snowflake)
- [QUERY_ATTRIBUTION_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_attribution_history)

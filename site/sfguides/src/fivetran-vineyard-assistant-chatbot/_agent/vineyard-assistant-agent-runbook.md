# Vineyard Assistant: agent runbook

This file lets an AI agent do the "Build a RAG-based, GenAI chatbot using Structured Data with Snowflake and Fivetran" quickstart for a person. It works with any agent that can read a markdown file and call tools (MCP servers, a shell, HTTP). It does not depend on one vendor's skill format.

Guide: https://www.snowflake.com/en/developers/guides/fivetran-vineyard-assistant-chatbot/

Guide source (markdown, the file to read SQL and code from): https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/fivetran-vineyard-assistant-chatbot/fivetran-vineyard-assistant-chatbot.md

Files this runbook uses, in the same repo folder: https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/fivetran-vineyard-assistant-chatbot (the `_postgres` folder holds the PostgreSQL page and the load files, and this `_agent` folder holds this runbook and `preflight_check.py`).

## Status of this file

- The manual click path (both the S3 and the PostgreSQL option) was tested end to end on 2026-10-13.
- An AI agent ran the S3 path end to end on 2026-10-13 against a personal Snowflake account: destination, S3 connection, sync (743 rows), both transform tables, vector search, and the Streamlit app. The payloads for the Snowflake destination and the S3 connection below are the ones that worked. Opening the deployed app in a browser stayed a human check.
- The PostgreSQL payload and the key pair route in Step 1 come from Fivetran's documentation and have not been run by an agent. Treat them as a test run, with a person watching.
- Anything marked UNTESTED has no known good result. If it fails, stop and tell the person. Do not guess.

## For the person: how to start

1. Download `preflight_check.py` (https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/fivetran-vineyard-assistant-chatbot/_agent/preflight_check.py) and run the check: `python3 preflight_check.py --snow-connection <NAME>`, where NAME is your Snowflake CLI connection (add `FIVETRAN_API_KEY` and `FIVETRAN_API_SECRET` to the environment to also test your Fivetran key). If it prints DRIFT FOUND, the Fivetran API or docs changed. Do not start the agent until this runbook is updated.
2. Give the agent this file and say: "Follow vineyard-assistant-agent-runbook.md. Use the S3 path" (or "the PostgreSQL path").
3. Stay available. The agent stops at the checkpoints marked **HUMAN** and waits for you.

## Rules for the agent

1. Never ask for a password, key or token in chat, and never print one. Read secrets from environment variables or files the person names. If a secret is needed and not available, stop and ask the person to set it.
2. Never delete or drop anything (connectors, databases, schemas, instances, files). Cleanup is a list for the person (Step 7).
3. Ask the person before each of these: creating a cloud resource, creating or changing a Snowflake user, role or key, trusting a TLS certificate, resuming a connector, creating a Streamlit app.
4. Work one step at a time. After each step run its check. If the check fails, stop and report the exact output.
5. Before creating anything, look for it first (list or show). If something with the same name already exists (a Fivetran connection or destination, a schema, a table, a Streamlit app, a database user), do not decide yourself. Show the person what you found (name, id, state, row count or last sync) and ask: reuse it, or create a new one with a different name? Wait for the answer. If they choose new, propose a name (for example add `_2` to PREFIX) and confirm it before creating. Never use `CREATE OR REPLACE` on an existing object without that answer, because it overwrites the old one.
6. If an API call is rejected because a field name or value changed, you may check the matching docs page named in the Appendix and retry once with the corrected field. A second failure means stop and report.
7. Keep a short log in `state.md` in the working folder: step number, what you did, the check result. Do not write secrets into it.
8. Use whichever tool route you have (see Tool map). The SQL and JSON in this file are the same on every route.

## Inputs to collect first

| Name | Meaning | Example |
|---|---|---|
| PATH | `s3` or `postgres` | `s3` |
| PREFIX | Destination schema prefix. Lower case letters, digits, underscores. Must be unique in the destination. | `smith_genai` |
| SF_DB | Snowflake database used by the Fivetran destination | `PC_FIVETRAN_DB` |
| SF_WH | Snowflake warehouse for queries and the app | `PC_FIVETRAN_WH` |
| SF_ROLE | Role you run the lab with (needs `SNOWFLAKE.CORTEX_USER`) | `ACCOUNTADMIN` |
| GROUP_ID | Fivetran destination group id (from `GET /v1/groups`) | `ruined_levee` |
| PG_HOST, PG_PORT, PG_DB, PG_USER | PostgreSQL path only | host, `5432`, `industry`, `fivetran` |

Secrets come from the environment, never from chat: `FIVETRAN_API_KEY`, `FIVETRAN_API_SECRET`, and for PostgreSQL `PG_ADMIN_PASSWORD` and `PG_FIVETRAN_PASSWORD`.

## Tool map

Use the first route you have for each system.

Fivetran:
- MCP server with connector tools (for example create, test, resume, sync). Tool names differ by server. At the time of writing Fivetran lists no officially supported MCP server, so check what your server really offers. If it cannot set `destination_schema_names` or `trust_certificates`, use the REST route.
- REST API: base `https://api.fivetran.com/v1`, header `Authorization: Basic base64(API_KEY:API_SECRET)`. Example: `curl -u "$FIVETRAN_API_KEY:$FIVETRAN_API_SECRET" https://api.fivetran.com/v1/groups`. OpenAPI file: https://fivetran.com/assets-docs/openapi/file_v1.json

Snowflake:
- Snowflake-managed MCP server with a `SYSTEM_EXECUTE_SQL` tool.
- Snowflake CLI: `snow sql -q "<statement>"`.
- SQL API or any SQL driver.

## Step 0: Preflight

Run `python3 preflight_check.py --snow-connection <NAME>` and read the result, where NAME is the Snowflake CLI connection for the account you chose in Step 1. Without a name the script tests the default connection, which may be a different account, and it prints a WARN. Check that the account, user, role and region it prints are the ones you intend to use. Then run these checks in Snowflake as SF_ROLE. Stop on any failure.

```sql
SELECT CURRENT_VERSION(), CURRENT_ROLE(), CURRENT_REGION();
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', 'preflight') IS NOT NULL AS embed_ok;
SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', 'Say OK') AS complete_ok;
```

If `COMPLETE` fails, the model is not offered in this region. Try another model from the `MODELS` list in the guide's Streamlit code and tell the person which one works. If `EMBED_TEXT_1024` fails the lab cannot continue in this region. Stop.

Then scan for existing objects with the names this run will use, and ask the person about each hit (rule 5):

- Fivetran: `GET /v1/connections?group_id=<GROUP_ID>` and look for a connection whose schema is `<PREFIX>`, `<PREFIX>.wine` (S3) or `<PREFIX>_pg` (PostgreSQL). Also look at the destination: `GET /v1/destinations`.
- Snowflake:

```sql
SHOW SCHEMAS LIKE '<PREFIX>%' IN DATABASE <SF_DB>;
SHOW STREAMLITS LIKE 'WINE_ASSISTANT' IN DATABASE <SF_DB>;
```

- PostgreSQL path: whether the database `industry`, the schema `agriculture` and the user `fivetran` already exist on the target server.

Report the hits in one short list, with each object's state (a connection's last sync and status, a table's row count), and ask once per object: reuse or create new. If the person says reuse, skip the matching create step and run only its check. Record the choices in `state.md`.

What to do when the preflight reports drift:

| Preflight result | Meaning | Action |
|---|---|---|
| FAIL endpoint ... not in the spec | Fivetran renamed or removed an endpoint | Stop. Show the line. Ask the person to update the Appendix or approve the dashboard route for that step. |
| FAIL create connection field ... or create destination field ... | The request body changed | Stop. Same as above. |
| FAIL create connection ... or create destination ... config fields missing | A config parameter was renamed or removed | Stop. Same as above. |
| FAIL ... required fields: the API requires, the runbook does not send | The API added a required field | Stop. Show the line. Add the field to the Appendix payload with the person's approval, then rerun the preflight. |
| FAIL docs page ... missing: x, y | A connector config parameter was renamed | Stop. Read the docs page, compare with the Appendix payload, propose the change to the person. Do not edit the runbook on your own. |
| WARN docs page ... could not fetch | The check could not read the page | Open the page by hand or with a fetch tool and compare the parameters listed in the Appendix. |
| FAIL live GET ... | The key is wrong or lacks rights | Stop. Ask the person to check the key. |

## Step 1: Snowflake and Fivetran accounts

**HUMAN** Creating the accounts is a browser task. Ask the person to use Snowflake Partner Connect (Admin, Partner Connect, or Marketplace, "Fivetran Platform", Start free trial, Connect to Fivetran) and to activate the Fivetran account. Partner Connect creates `PC_FIVETRAN_DB`, `PC_FIVETRAN_WH`, `PC_FIVETRAN_USER`, `PC_FIVETRAN_ROLE` and a Snowflake destination in Fivetran.

Check:

```sql
SHOW DATABASES LIKE 'PC_FIVETRAN_DB';
SHOW WAREHOUSES LIKE 'PC_FIVETRAN_WH';
```

And `GET /v1/groups` returns at least one group, then `GET /v1/destinations` shows a destination of service `snowflake` in it. Record GROUP_ID. Run `POST /v1/destinations/{destinationId}/test` (or the MCP equivalent) and require every setup test to pass.

If the person already has a Fivetran destination, show it (name, group id, test status) and ask whether to use it or create another one. If they pick it, run its test and go to Step 2.

If there is no destination and no Partner Connect (the destination payload was run by an agent, the key pair steps before it were done by hand there):
1. Ask the person for approval, then generate a key pair locally. Keep the private key in a file with mode 600 and never print it:
   `openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out fivetran_rsa_key.p8 -nocrypt` and `openssl rsa -in fivetran_rsa_key.p8 -pubout -out fivetran_rsa_key.pub`
2. With approval, set the public key on the Fivetran user as ACCOUNTADMIN, using the one line public key without the BEGIN and END lines: `ALTER USER PC_FIVETRAN_USER SET RSA_PUBLIC_KEY='<one line>';`
3. Destinations live in a Fivetran group. If the person has no group for this lab, ask for approval and create one (`POST /v1/groups` with a `name`, or the MCP equivalent). Record its id as GROUP_ID.
4. Create the destination with the Snowflake payload in the Appendix, reading `private_key` from the file. Then run the destination test. Setup tests that are skipped because they do not apply (for example Validate Passphrase for an unencrypted key) are normal. Require every test that ran to pass.
5. The response and `GET /v1/destinations/{id}` return `config.table_type` and `config.default_virtual_warehouse`. The lab needs `table_type` to be `NATIVE` (Snowflake Native Tables) and the warehouse to be set. If `table_type` is not returned, **HUMAN** ask the person to open the destination in the Fivetran dashboard and confirm it. If they cannot confirm, stop.

## Step 2A: S3 path

The data is one JSON file in a public bucket owned by Fivetran.

If a connection named `<PREFIX>.wine` already exists, ask the person: reuse it (then check its status and Step 3 only), or create a new one with a different PREFIX. The schema name of an existing connection cannot be changed, so a new connection needs a new PREFIX.

Otherwise create the connection (payload in the Appendix) with `paused: true` and `run_setup_tests: true`. The connection name will be `<PREFIX>.wine`.

Check: the response `data.id` exists, and `data.setup_tests` (or `GET /v1/connections/{id}` then `POST .../test`) shows every applicable test passed. A public bucket skips some tests (for example the ExternalID check), which is normal. A failed test means stop and report.

Go to Step 3.

## Step 2B: PostgreSQL path

Full human readable version: https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/fivetran-vineyard-assistant-chatbot/_postgres/postgresql-source.md. Summary for the agent:

1. **HUMAN** Create a PostgreSQL 12 or later database named `industry`, port 5432, public access on, in AWS, Google Cloud or Azure. The agent may create it with that cloud's CLI only after the person approves the exact command. Record PG_HOST.
2. Allow Fivetran to reach the database. Find the destination's Cloud Service Provider and Cloud Region (Destinations, the destination, Overview, Destination Connection Details), then look up the address block for that region at https://fivetran.com/docs/using-fivetran/ips and add it to the database networking on port 5432 (RDS security group inbound rule, Cloud SQL authorized network, Azure firewall rule with start and end address). Also allow the machine that will run the load, so it can reach the database.
3. Load the data (743 rows) with the psql route. Download https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/fivetran-vineyard-assistant-chatbot/_postgres/load_wine_data_to_postgres.sql and the JSON file https://ft-s3-lab-bkt.s3.amazonaws.com/winedata/california_wine_country_visits_202409021224.json into one folder, then run it from that folder with `PGPASSWORD` taken from the environment: `psql "host=$PG_HOST port=5432 dbname=industry user=<admin user> sslmode=require" -f load_wine_data_to_postgres.sql`. The last line must print 743. (Alternative: `load_wine_data_to_postgres.py` from the same folder.)
4. Create the Fivetran database user. Read the password from `PG_FIVETRAN_PASSWORD` and pass it with a psql variable so it never appears in the command text:

```sql
CREATE USER fivetran WITH PASSWORD :'ftpw';
GRANT CONNECT ON DATABASE industry TO fivetran;
GRANT USAGE ON SCHEMA agriculture TO fivetran;
GRANT SELECT ON ALL TABLES IN SCHEMA agriculture TO fivetran;
```

   (Run it with `psql -v ftpw="$PG_FIVETRAN_PASSWORD" ...`.)
5. **HUMAN** Approve trusting the database's TLS certificate. In the dashboard this is the "Confirm TLS Certificate" dialog. With the API, `trust_certificates: true` does the same for the setup tests. Explain this to the person and wait for a yes.
6. If a PostgreSQL connection with schema `<PREFIX>_pg` already exists, ask the person: reuse it (check its status and go to Step 3), or create a new one with a different PREFIX. A connection that was created with Source naming cannot be switched to Fivetran naming after its first sync, so if the existing one uses Source naming, say so and recommend a new one.

   Otherwise create the connection (payload in the Appendix) with `paused: true`, `run_setup_tests: true`, `trust_certificates: true`, and `destination_schema_names: "FIVETRAN_NAMING"`.

**Important:** use `FIVETRAN_NAMING`. The dashboard preselects Source naming, which creates a lower case schema called `agriculture` that the guide's SQL cannot find and that can collide with an existing schema. Naming cannot be changed after the first sync.

Check: `data.id` exists and all setup tests passed. Common failure: the setup test cannot connect. Then the Fivetran IP block is not allowed in the database networking. Stop and report.

## Step 3: Start the sync and verify the data landed

1. **HUMAN** Ask the person to confirm you may start the sync.
2. Resume the connection: `PATCH /v1/connections/{id}` with `{"paused": false}`. If after two minutes `GET /v1/connections/{id}` shows no sync running and no `succeeded_at`, call `POST /v1/connections/{id}/sync`.
3. Poll `GET /v1/connections/{id}` every 15 seconds for up to 10 minutes until `succeeded_at` is set. If `status.sync_state` shows a failure or `status.tasks` has entries, stop and report them.
4. Find the landing table (the schema name depends on the path):

```sql
SELECT table_schema, table_name, row_count
FROM <SF_DB>.INFORMATION_SCHEMA.TABLES
WHERE table_name = 'CALIFORNIA_WINE_COUNTRY_VISITS';
```

Expected: S3 path, schema `UPPER(PREFIX)`. PostgreSQL path, schema `UPPER(PREFIX)_AGRICULTURE`. The table has 743 rows. Confirm with `SELECT COUNT(*) FROM <SF_DB>.<SCHEMA>.CALIFORNIA_WINE_COUNTRY_VISITS;`. Record the schema as SF_SCHEMA. If there is more than one schema with that table, use the one that matches your PREFIX.

## Step 4: Transform the data

If `VINEYARD_DATA_SINGLE_STRING` or `VINEYARD_DATA_VECTORS` already exist in `SF_SCHEMA`, the guide's `CREATE OR REPLACE TABLE` statements would overwrite them. Show their row counts and ask: keep them (skip to the checks), or rebuild them.

The source of truth for the SQL is the guide section "Transform the Wine Structured Dataset". Extract the SQL code blocks from the guide file instead of retyping them, so this runbook cannot drift from it. Run them in this order with `USE SCHEMA <SF_DB>.<SF_SCHEMA>;` first:

1. The `USE SCHEMA` statement.
2. The statement that creates `vineyard_data_single_string`.
3. The statement that creates `vineyard_data_vectors` (it calls Cortex for each row and takes several seconds).

Checks:

```sql
SELECT COUNT(*) FROM VINEYARD_DATA_SINGLE_STRING;                              -- 743
SELECT COUNT(*) FROM VINEYARD_DATA_VECTORS WHERE WINERY_EMBEDDING IS NOT NULL; -- 743
SELECT winery_or_vineyard,
       VECTOR_COSINE_SIMILARITY(winery_embedding,
         SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', 'Kohlleffel Vineyards address')) AS score
FROM VINEYARD_DATA_VECTORS ORDER BY score DESC LIMIT 3;                        -- Kohlleffel Vineyards first
```

## Step 5: Create the Streamlit chatbot

The app must be created in the same database and schema as `VINEYARD_DATA_VECTORS`. It runs on the warehouse runtime (not the container runtime, which needs a compute pool).

1. **HUMAN** Ask for approval to create the app. If `WINE_ASSISTANT` already exists in that schema, the `CREATE OR REPLACE` below would overwrite it, so ask: reuse it (skip to the code and checks), replace it, or create another with a different name such as `WINE_ASSISTANT_2` (then use that name everywhere in this step).
2. Create it. This is the exact SQL from the guide, with your warehouse:

```sql
USE SCHEMA <SF_DB>.<SF_SCHEMA>;
CREATE OR REPLACE STREAMLIT WINE_ASSISTANT
  RUNTIME_NAME = 'SYSTEM$WAREHOUSE_RUNTIME'
  QUERY_WAREHOUSE = <SF_WH>
  MAIN_FILE = 'streamlit_app.py';
ALTER STREAMLIT WINE_ASSISTANT ADD LIVE VERSION FROM LAST;
```

3. Put the app code into the app. The code is the Python block that contains `MODELS = [` in the guide section "Build the Chatbot as a Streamlit Application" (it comes before the "Run the Chatbot" heading). Write it to a local `streamlit_app.py` without changing it and deploy it with the Snowflake CLI (`snow streamlit deploy`, tested) or upload it to the app's stage location. Do not trust the exit code alone. On a Snowflake account whose hostname has no region part (for example `<account>.snowflakecomputing.com`), CLI 3.20.0 uploaded the file and then exited 1 with "The connection host ... was missing or not in the expected format" while it built the app URL. So check the result before retrying: run `SHOW STREAMLITS LIKE 'WINE_ASSISTANT';` and `DESCRIBE STREAMLIT WINE_ASSISTANT;`, list the app's files with `LIST` on its stage, and, if you want proof, download the file with `GET` and compare it byte for byte with the guide's Python block. If the live file matches, the deploy worked and only the URL step failed, so do not redeploy and do not ask the person to paste code. If the file is missing or different, **HUMAN** ask the person to open Projects, Streamlit, WINE_ASSISTANT, click Edit, delete the default code, paste the code from the guide, and click Run. The warehouse runtime has Streamlit 1.22, which is why the guide's code falls back to `st.experimental_rerun`.
4. **HUMAN** Ask the person to open the app, keep "Use my own dataset" style context on, and ask: "Where is Kohlleffel Vineyards located?" The answer should give 1 Kohlleffel Lane, Cazadero, CA 95421. A model error means that model is not available in the region. Pick another from the model list.

## Step 6: Report

Tell the person: the connection name, the schema and table with the row count, the names of the two transform tables, the app name, and anything that needed a manual step. Include the cleanup list below.

## Step 7: Cleanup list (for the person, do not run)

- Fivetran: the connection created here (and the test connections, if any).
- Snowflake: the schema `SF_SCHEMA` (tables from Fivetran, `VINEYARD_DATA_SINGLE_STRING`, `VINEYARD_DATA_VECTORS`) and the `WINE_ASSISTANT` app. If you added a key: `ALTER USER PC_FIVETRAN_USER UNSET RSA_PUBLIC_KEY;` and delete the key files.
- PostgreSQL path: the cloud database instance (it keeps costing money), and the networking rules you added.

## Appendix: payloads and docs pages

Replace the values in angle brackets. Values from secrets must come from the environment.

PostgreSQL connection. Docs: https://fivetran.com/docs/connectors/databases/postgresql/setup-guide/api-configuration

```json
POST /v1/connections
{
  "group_id": "<GROUP_ID>",
  "service": "postgres",
  "paused": true,
  "run_setup_tests": true,
  "trust_certificates": true,
  "sync_frequency": 360,
  "destination_schema_names": "FIVETRAN_NAMING",
  "config": {
    "schema_prefix": "<PREFIX>_pg",
    "host": "<PG_HOST>",
    "port": 5432,
    "database": "industry",
    "user": "fivetran",
    "password": "<from PG_FIVETRAN_PASSWORD>",
    "connection_type": "Directly",
    "update_method": "QUERY_BASED",
    "delete_capture_enabled": true
  }
}
```

UNTESTED by an agent (the click path in the dashboard was tested by hand). The dashboard defaults to Logical Replication. The lab needs `QUERY_BASED`. The resulting schema is `<PREFIX>_pg_agriculture` (shown in Snowflake in upper case).

Amazon S3 connection. Docs: https://fivetran.com/docs/connectors/files/amazon-s3/api-configuration

```json
POST /v1/connections
{
  "group_id": "<GROUP_ID>",
  "service": "s3",
  "paused": true,
  "run_setup_tests": true,
  "sync_frequency": 360,
  "destination_schema_names": "FIVETRAN_NAMING",
  "config": {
    "schema": "<PREFIX>",
    "table_group_name": "wine",
    "bucket": "ft-s3-lab-bkt",
    "prefix": "winedata",
    "auth_type": "PUBLIC_BUCKET",
    "is_public": true,
    "file_type": "json",
    "json_delivery_mode": "Unpacked",
    "file_mapping_method": "DEFINE_PER_TABLE",
    "files": [
      { "table_name": "california_wine_country_visits", "file_pattern": ".*\\.json" }
    ]
  }
}
```

Tested by an agent on 2026-10-13: the API accepted `PUBLIC_BUCKET` together with `is_public: true` unchanged, the setup tests passed (some were skipped as not applicable for a public bucket), and the connection found the one expected file.

Snowflake destination (only when no destination exists). Docs: https://fivetran.com/docs/destinations/snowflake/api-configuration

```json
POST /v1/destinations
{
  "group_id": "<GROUP_ID>",
  "service": "snowflake",
  "region": "<Fivetran region code for the group>",
  "time_zone_offset": "0",
  "run_setup_tests": true,
  "config": {
    "auth": "KEY_PAIR",
    "host": "<account_identifier>.snowflakecomputing.com",
    "port": 443,
    "database": "PC_FIVETRAN_DB",
    "user": "PC_FIVETRAN_USER",
    "private_key": "<contents of fivetran_rsa_key.p8, read from the file>",
    "role": "PC_FIVETRAN_ROLE",
    "default_virtual_warehouse": "PC_FIVETRAN_WH"
  }
}
```

`time_zone_offset` is required. Without it the API answers HTTP 400 "Field 'time_zone_offset' is required". `"0"` (UTC) is fine for this lab, or use the person's offset as a string. `region` is the Fivetran processing region (for example `AWS_AP_SOUTHEAST_2`) and cannot be changed later, so ask the person. The `group_id` must already exist (`GET /v1/groups`, or create one with `POST /v1/groups`). An agent created a destination in a new, empty group with this payload on 2026-10-13, and the response showed `table_type` `NATIVE` and the warehouse that was set. Creating one in a group that already has a destination is UNTESTED.

Other references: create connection https://fivetran.com/docs/rest-api/api-reference/connections/create-connection and the API key page https://fivetran.com/docs/developer-resources/rest-api/getting-started

## Maintaining this file

- Run `preflight_check.py` before every agent run. A scheduled weekly run is enough to notice drift early.
- When the guide or the Fivetran setup screens change, update the payloads and the "tested" date at the top.
- Fix drift in the Appendix first, rerun the preflight, then run the agent.

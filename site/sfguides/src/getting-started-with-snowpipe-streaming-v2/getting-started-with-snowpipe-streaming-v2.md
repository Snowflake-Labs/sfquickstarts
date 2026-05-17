author: Vino Duraisamy, Chase Thomas
id: getting-started-with-snowpipe-streaming-v2
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Stream data into Snowflake in real-time using Snowpipe Streaming high-performance architecture with the Python SDK and monitor it with a live Streamlit dashboard.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Snowpipe Streaming high-performance architecture and Cortex Code
<!---------------------------->

## Overview

Duration: 3

Getting data into Snowflake shouldn't require staging files, managing pipes, or writing boilerplate infrastructure code. With [Snowpipe Streaming high-performance architecture](https://www.snowflake.com/en/engineering-blog/next-gen-snowpipe-streaming-architecture/), our next-gen architecture lets you stream rows directly into Snowflake tables with low latency — no staging files, no explicit pipe creation required.

The key difference from classic Snowpipe Streaming is the use of a **default auto-created pipe**. When you first stream data into a table, Snowflake automatically creates a managed pipe named `<TABLE_NAME>-streaming`. There is no `CREATE PIPE` SQL needed.

In this guide, you will build an end-to-end streaming pipeline in under a few minutes using [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code), Snowflake's AI-powered coding assistant that can automate the entire workflow with a single prompt. You will:

- Generate fake user data with the Python SDK and stream it into a Snowflake table via the default auto-created pipe
- Deploy a live Streamlit dashboard that auto refreshes as data arrives
- See how Cortex Code skills can replace every manual step with one command

> **Prefer the fast path?** If you have [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code) installed, skip ahead to [Automate With Cortex Code](#automate-with-cortex-code) and type `ssv2 quickstart`. It handles everything such as SQL objects, Python setup, and data streaming automatically.

### What You Will Learn

- How Snowpipe Streaming high-performance architecture works
- How to configure RSA key-pair (JWT) authentication for the Python SDK
- How to use the `snowpipe-streaming` Python SDK to open channels and stream rows
- How to deploy a real-time Streamlit in Snowflake dashboard
- How to automate the entire pipeline with Cortex Code skills

### What You Will Build

- A Snowflake landing table for streaming ingestion
- A Python script that generates and streams fake user data
- A live Streamlit dashboard that auto-refreshes to show data arriving

### What is Cortex Code?

Cortex Code is Snowflake's CLI-based AI coding assistant. It understands Snowflake APIs, SQL, and Python and can execute multi-step workflows through skills. This guide includes two open-source Cortex Code skills that automate the entire streaming pipeline. You can follow the manual steps below to learn how everything works, then use the skills to replicate (or extend) the pipeline instantly.

### What You Will Need

- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with `ACCOUNTADMIN` access
- Python 3.9 or higher installed locally
- OpenSSL installed locally (included by default on macOS and most Linux distributions)
- A terminal (macOS Terminal, Linux shell, or WSL2 on Windows)
- Basic familiarity with SQL and Python

<!---------------------------->

## Automate With Cortex Code

Duration: 5

Everything you did manually in this guide can be fully automated with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) — Snowflake's CLI-based AI coding assistant. Two open-source Cortex Code skills handle the entire pipeline for you, from RSA key generation to live dashboards.

### Install the Skills

The skills live in the [SSv2-AI-Webinar](https://github.com/sfc-gh-chathomas/SSv2-AI-Webinar) repository. Clone the repo and copy the skill directories into your Cortex Code skills folder:

```bash
git clone https://github.com/sfc-gh-chathomas/SSv2-AI-Webinar.git
mkdir -p ~/.snowflake/cortex/skills
cp -r SSv2-AI-Webinar/skills/ssv2-quickstart ~/.snowflake/cortex/skills/
cp -r SSv2-AI-Webinar/skills/ssv2-AI-webinar ~/.snowflake/cortex/skills/
```

The skills are automatically discovered by Cortex Code on the next session.

### Available Skills

| Skill | Trigger Phrase | What It Does |
|---|---|---|
| **SSv2 Quickstart** | `ssv2 quickstart` | Runs everything in this guide end-to-end (~5 min) |
| **SSv2 AI Webinar** | `ssv2 ai webinar` | Quickstart + Semantic View + Cortex Agent for live demos |

#### ssv2-quickstart

Automates every step in this guide: platform detection, RSA key-pair generation, Snowflake object creation, Python venv setup, Streamlit dashboard deployment, data streaming, and cleanup. Just type the trigger phrase and confirm.

#### ssv2-AI-webinar

Builds on the quickstart and adds an AI layer for live presentations:

- Streams data **in the background** for 30 minutes so you can keep presenting
- Creates a **Semantic View** on the streaming table with computed dimensions and metrics
- Creates a **Cortex Agent** for natural-language queries on live streaming data
- Runs showcase queries to prove everything works, then hands off to the presenter

### Example Prompts

Start a Cortex Code session and try any of these:

```
ssv2 quickstart
```

```
try snowpipe streaming
```

```
ssv2 ai webinar
```

```
demo snowpipe streaming
```

Each skill confirms your intent before creating any resources and asks for your preferences (database name, table name, etc.). When the demo is done, it offers to clean up all Snowflake objects automatically.

### What Gets Automated

Here is how the skill maps to the steps you completed manually in this guide:

| Manual Step | What the Skill Does |
|---|---|
| Generate RSA Keys | Runs `openssl` commands in a single batch |
| Create Snowflake Objects | Executes all CREATE/GRANT statements in one SQL call |
| Set Up Python | Creates venv, installs SDK and Faker, writes `profile.json` and `ssv2_demo.py` in parallel |
| Deploy Live Dashboard | Creates stage, uploads Streamlit app, creates Streamlit object — 3 parallel operations |
| Stream Sample Data | Runs the demo script (foreground for quickstart, background for webinar) |
| Clean Up | Drops all Snowflake objects in one SQL call |

> **Tip:** The AI Webinar skill is designed for [live presentations](https://www.snowflake.com/en/webinars/demo/build-high-performance-ai-pipelines-with-real-time-streaming-2026-03-11/). It streams data in the background while you build the Semantic View and Cortex Agent on stage. Re-ask the same natural-language question a few minutes later and the numbers will have changed — that's the wow factor.

<!---------------------------->

## Generate RSA Keys

Duration: 3

The Snowpipe Streaming Python SDK authenticates using **RSA key-pair (JWT)** authentication. You will generate a fresh key-pair for a dedicated demo user.

### Create a Working Directory

Open a terminal and create a directory for this quickstart:

```bash
mkdir -p ~/ssv2-quickstart && cd ~/ssv2-quickstart
```

### Generate the Key-Pair

Run the following command to generate a 2048-bit RSA key-pair and extract the public key body:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt \
  && chmod 600 rsa_key.p8 \
  && openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub \
  && echo "=== PUBLIC KEY BODY ===" \
  && grep -v KEY- rsa_key.pub | tr -d '\n' \
  && echo
```

This produces two files:

| File | Purpose |
|---|---|
| `rsa_key.p8` | Private key (PKCS#8 format, unencrypted) — used by the Python SDK |
| `rsa_key.pub` | Public key — registered with the Snowflake demo user |

Copy the base64 string printed after `=== PUBLIC KEY BODY ===`. You will need it in the next step.

> **Note:** The private key is unencrypted for demo simplicity. In production, use an encrypted key with a passphrase or a secrets manager.

<!---------------------------->

## Create Snowflake Objects

Duration: 5

In this step you will create the database, schema, landing table, a dedicated demo user with the RSA public key, and the necessary grants.

### Why a Dedicated Demo User?

The Python SDK requires RSA key-pair auth. Rather than overwriting any existing RSA key on your current user (which could break existing workflows), this guide creates a short-lived demo user `SSV2_DEMO_USER` with a dedicated role. You will clean it up at the end.

### Run the Setup SQL

Open a Snowflake worksheet in Snowsight and run the following SQL. Replace `<YOUR_PUBLIC_KEY_BODY>` with the base64 string you copied in the previous step, and `<YOUR_WAREHOUSE>` with an active warehouse:

```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS SSV2_QUICKSTART_DB;
CREATE SCHEMA IF NOT EXISTS SSV2_QUICKSTART_DB.SSV2_SCHEMA;

USE DATABASE SSV2_QUICKSTART_DB;
USE SCHEMA SSV2_SCHEMA;

-- Create landing table
CREATE OR REPLACE TABLE SSV2_QUICKSTART_USERS (
    user_id              INTEGER,
    first_name           VARCHAR(100),
    last_name            VARCHAR(100),
    email                VARCHAR(255),
    phone_number         VARCHAR(50),
    address              VARCHAR(500),
    date_of_birth        DATE,
    registration_date    TIMESTAMP_NTZ,
    city                 VARCHAR(100),
    state                VARCHAR(100),
    country              VARCHAR(100),
    order_amount         NUMBER(10,2)
);

-- Create demo role and user
CREATE ROLE IF NOT EXISTS SSV2_DEMO_ROLE;
CREATE USER IF NOT EXISTS SSV2_DEMO_USER DEFAULT_ROLE = SSV2_DEMO_ROLE;
GRANT ROLE SSV2_DEMO_ROLE TO USER SSV2_DEMO_USER;

-- Register the RSA public key
ALTER USER SSV2_DEMO_USER SET RSA_PUBLIC_KEY = '<YOUR_PUBLIC_KEY_BODY>';

-- Grant permissions
GRANT USAGE ON DATABASE SSV2_QUICKSTART_DB TO ROLE SSV2_DEMO_ROLE;
GRANT USAGE ON SCHEMA SSV2_QUICKSTART_DB.SSV2_SCHEMA TO ROLE SSV2_DEMO_ROLE;
GRANT USAGE ON WAREHOUSE <YOUR_WAREHOUSE> TO ROLE SSV2_DEMO_ROLE;
GRANT OWNERSHIP ON TABLE SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_QUICKSTART_USERS
    TO ROLE SSV2_DEMO_ROLE COPY CURRENT GRANTS;
GRANT SELECT ON TABLE SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_QUICKSTART_USERS
    TO ROLE <YOUR_CURRENT_ROLE>;

-- Verify the key was registered
DESC USER SSV2_DEMO_USER;
```

### Why GRANT OWNERSHIP on the Table?

The default auto-created pipe is Snowflake-managed and tied to the table. The role that streams data must own the table to ensure full access to the default pipe. The database and schema remain owned by your primary role so you can still query the table. The `SELECT` grant back to your role lets the Streamlit dashboard read the data.

### Verify

In the `DESC USER` output, confirm `RSA_PUBLIC_KEY` is set and not empty.

> **No `CREATE PIPE` is needed.** The high-performance architecture auto-creates a default pipe the first time data is streamed into the table. The Python SDK references it as: `SSV2_QUICKSTART_USERS-streaming` (note the **hyphen**, not underscore).

<!---------------------------->

## Set Up Python

Duration: 5

In this step you will create a Python virtual environment, install the SDK, and write the configuration and demo script files.

### Create Virtual Environment

From your `~/ssv2-quickstart` directory, run:

```bash
python3 -m venv ssv2_venv \
  && source ssv2_venv/bin/activate \
  && pip install --upgrade pip \
  && pip install snowpipe-streaming faker
```

Verify the installation:

```bash
python -c "from snowflake.ingest.streaming import StreamingIngestClient; print('SDK OK')"
python -c "from faker import Faker; print('Faker OK')"
```

Both commands should print `OK`. If either fails, check that your virtual environment is activated and that you are running Python 3.9+.

### Write profile.json

Create a file called `profile.json` in the `~/ssv2-quickstart` directory with the following content. Replace `<YOUR_ACCOUNT_IDENTIFIER>` with your Snowflake account identifier (e.g., `xy12345` or `myorg-myaccount`):

```json
{
    "user": "SSV2_DEMO_USER",
    "account": "<YOUR_ACCOUNT_IDENTIFIER>",
    "url": "https://<YOUR_ACCOUNT_IDENTIFIER>.snowflakecomputing.com:443",
    "private_key_file": "rsa_key.p8",
    "role": "SSV2_DEMO_ROLE"
}
```

### Write the Demo Script

Create a file called `ssv2_demo.py` in the same directory with the following content:

```python
import time
import os
import random
from faker import Faker

os.environ["SS_LOG_LEVEL"] = "warn"
from snowflake.ingest.streaming import StreamingIngestClient

fake = Faker()

# --- Configuration ---
BATCH_SIZE = 5
DEMO_MINUTES = 3
NUM_BATCHES = DEMO_MINUTES * 120  # 120 batches per minute (5 rows every 0.5s)
DATABASE = "SSV2_QUICKSTART_DB"
SCHEMA   = "SSV2_SCHEMA"

# Default auto-created pipe: <TABLE_NAME>-streaming (hyphen, not underscore)
PIPE     = "SSV2_QUICKSTART_USERS-streaming"

PROFILE_JSON_PATH = "profile.json"

# --- Initialize Streaming Client ---
print(f"Connecting to Snowflake...")
print(f"  Database: {DATABASE}")
print(f"  Schema:   {SCHEMA}")
print(f"  Pipe:     {PIPE} (default auto-created pipe)")

try:
    client = StreamingIngestClient(
        "SSV2_QUICKSTART_CLIENT",
        DATABASE,
        SCHEMA,
        PIPE,
        profile_json=PROFILE_JSON_PATH,
        properties=None,
    )
except Exception as e:
    print(f"\n[ERROR] Failed to create StreamingIngestClient:")
    print(f"  {e}")
    print(f"\nTroubleshooting:")
    print(f"  1. Verify profile.json exists and has correct values")
    print(f"  2. Check that rsa_key.p8 exists in the same directory")
    print(f"  3. Verify the public key is registered: DESC USER SSV2_DEMO_USER;")
    print(f"  4. Ensure network allows outbound HTTPS to Snowflake")
    raise SystemExit(1)

# --- Open channel ---
print(f"\nOpening channel...")
try:
    channel, status = client.open_channel("SSV2_QUICKSTART_CHANNEL")
    print(f"  Channel: {status.channel_name}")
    print(f"  Status:  {status.status_code}")
    print(f"  Latest committed offset: {status.latest_committed_offset_token}")
except Exception as e:
    print(f"\n[ERROR] Failed to open channel:")
    print(f"  {e}")
    print(f"\nTroubleshooting:")
    print(f"  1. Verify the table exists: SELECT * FROM {DATABASE}.{SCHEMA}.SSV2_QUICKSTART_USERS LIMIT 1;")
    print(f"  2. Check role has INSERT privilege on the table")
    print(f"  3. Verify database and schema names are correct")
    client.close()
    raise SystemExit(1)

# --- Stream fake user data in batches ---
total_rows = BATCH_SIZE * NUM_BATCHES
print(f"\nStreaming {total_rows} rows ({NUM_BATCHES} batches of {BATCH_SIZE}) over ~{DEMO_MINUTES} minute(s)...")
print(f"Watch your Streamlit dashboard to see data arrive in real-time!\n")
errors = []
row_id = 0
for batch in range(1, NUM_BATCHES + 1):
    for _ in range(BATCH_SIZE):
        row_id += 1
        row = {
            "user_id": row_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number(),
            "address": fake.address().replace("\n", ", "),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "registration_date": fake.date_time_this_year().isoformat(),
            "city": fake.city(),
            "state": fake.state(),
            "country": fake.country(),
            "order_amount": round(random.uniform(1, 100), 2),
        }
        try:
            channel.append_row(row, offset_token=str(row_id))
        except Exception as e:
            errors.append((row_id, str(e)))
            if len(errors) >= 5:
                print(f"\n[ERROR] Too many row errors ({len(errors)}). Stopping.")
                break
    if len(errors) >= 5:
        break

    if batch % 60 == 0:
        print(f"  [producer] batch {batch}/{NUM_BATCHES} (row {row_id})")

    time.sleep(0.5)

if errors:
    print(f"\n[WARNING] {len(errors)} rows failed to send:")
    for offset, err in errors[:5]:
        print(f"  Row {offset}: {err}")

# --- Wait for all data to be committed ---
print(f"\n[producer] Waiting for commits to reach offset {total_rows}...")
try:
    channel.wait_for_commit(
        lambda token: token is not None and int(token) >= total_rows,
        timeout_seconds=120
    )
    print("All rows committed.")
except Exception as e:
    print(f"\n[WARNING] Commit wait timed out or failed: {e}")
    print("Some rows may still be in flight. Check the table directly.")

# --- Display channel status ---
s = channel.get_channel_status()
print(f"\nChannel status:")
print(f"  Channel:              {s.channel_name}")
print(f"  Committed offset:     {s.latest_committed_offset_token}")
print(f"  Rows inserted:        {s.rows_inserted_count}")
print(f"  Rows errored:         {s.rows_error_count}")
print(f"  Avg server latency:   {s.server_avg_processing_latency}")
print(f"  Last error message:   {s.last_error_message}")

# --- Cleanup ---
print(f"\nFinal committed offset: {channel.get_latest_committed_offset_token()}")
channel.close()
client.close()
print("\nDemo complete!")
```

> **Tip:** You can change `DEMO_MINUTES` to a value between 1 and 10 to control how long the script streams data. At the default of 3 minutes, it sends 1,800 rows (5 rows every 0.5 seconds).

<!---------------------------->

## Deploy Live Dashboard

Duration: 5

Deploy a Streamlit in Snowflake app that auto-refreshes every 2 seconds so you can watch data arrive in real-time. This dashboard runs in the Snowflake cloud — no local Streamlit installation needed.

### Create a Stage

Run the following SQL in Snowsight:

```sql
CREATE STAGE IF NOT EXISTS SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_STREAMLIT_STAGE
    DIRECTORY = (ENABLE = TRUE);
```

### Write the Streamlit App

Create a file called `streamlit_app.py` in your `~/ssv2-quickstart` directory:

```python
import streamlit as st
import time

st.set_page_config(page_title="Snowpipe Streaming high-performance architecture Monitor", layout="wide")

conn = st.connection("snowflake")

DATABASE = "SSV2_QUICKSTART_DB"
SCHEMA   = "SSV2_SCHEMA"
TABLE    = "SSV2_QUICKSTART_USERS"
REFRESH_INTERVAL = 2

st.title("Snowpipe Streaming high-performance architecture — Live Monitor")
st.caption(f"Reading from `{DATABASE}.{SCHEMA}.{TABLE}` · refreshes every {REFRESH_INTERVAL}s")

try:
    metrics_df = conn.query(
        f"""SELECT COUNT(*) AS total_rows,
                   COALESCE(SUM(order_amount), 0) AS total_revenue
            FROM {DATABASE}.{SCHEMA}.{TABLE}""",
        ttl=0,
    )
    total_rows = metrics_df["TOTAL_ROWS"].iloc[0] if len(metrics_df) > 0 else 0
    total_revenue = metrics_df["TOTAL_REVENUE"].iloc[0] if len(metrics_df) > 0 else 0
except Exception as e:
    st.error(f"Error querying table: {e}")
    total_rows = 0
    total_revenue = 0

if total_rows > 0:
    latest_df = conn.query(
        f"""SELECT MAX(user_id) AS latest_id,
                   COUNT(DISTINCT country) AS unique_countries
            FROM {DATABASE}.{SCHEMA}.{TABLE}""",
        ttl=0,
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", f"{total_rows:,}")
    col2.metric("Revenue Total", f"${total_revenue:,.2f}")
    col3.metric("Latest User ID", latest_df["LATEST_ID"].iloc[0])
    col4.metric("Unique Countries", latest_df["UNIQUE_COUNTRIES"].iloc[0])
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", "0")
    col2.metric("Revenue Total", "$0.00")
    col3.metric("Latest User ID", "—")
    col4.metric("Unique Countries", "—")
    st.info("Waiting for data... Start the streaming demo to see rows appear.")

st.subheader("Most Recent Records")
if total_rows > 0:
    recent_df = conn.query(
        f"""SELECT user_id, first_name, last_name, email, country, order_amount
            FROM {DATABASE}.{SCHEMA}.{TABLE}
            ORDER BY user_id DESC
            LIMIT 20""",
        ttl=0,
    )
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
else:
    st.write("No data yet.")

if total_rows > 0:
    st.subheader("Revenue Over Time")
    time_df = conn.query(
        f"""SELECT
                DATE_TRUNC('second', registration_date) AS time_bucket,
                SUM(SUM(order_amount)) OVER (ORDER BY DATE_TRUNC('second', registration_date)) AS cumulative_revenue
            FROM {DATABASE}.{SCHEMA}.{TABLE}
            GROUP BY time_bucket
            ORDER BY time_bucket""",
        ttl=0,
    )
    st.line_chart(time_df.set_index("TIME_BUCKET"), y="CUMULATIVE_REVENUE", height=300)

    st.subheader("Top 10 Countries by Revenue")
    country_df = conn.query(
        f"""SELECT country, SUM(order_amount) AS revenue
            FROM {DATABASE}.{SCHEMA}.{TABLE}
            GROUP BY country
            ORDER BY revenue DESC
            LIMIT 10""",
        ttl=0,
    )
    st.dataframe(country_df, use_container_width=True, hide_index=True)

time.sleep(REFRESH_INTERVAL)
st.rerun()
```

### Upload and Deploy

Upload the Streamlit app to the stage and create the Streamlit object. Run these commands using the [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index):

```bash
snow stage copy streamlit_app.py @SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_STREAMLIT_STAGE --overwrite
```

Then run the following SQL in Snowsight:

```sql
CREATE OR REPLACE STREAMLIT SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_LIVE_MONITOR
    ROOT_LOCATION = '@SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_STREAMLIT_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = <YOUR_WAREHOUSE>
    TITLE = 'Snowpipe Streaming high-performance architecture Monitor';

-- Get the URL to open the dashboard
SHOW STREAMLITS IN SCHEMA SSV2_QUICKSTART_DB.SSV2_SCHEMA;
```

Open the Streamlit URL from the `SHOW STREAMLITS` output. The dashboard will show "Waiting for data..." until you start streaming in the next step.

<!---------------------------->

## Stream Sample Data

Duration: 5

Now run the demo script to stream fake user data into Snowflake. Make sure your Streamlit dashboard is open in another browser tab so you can watch data arrive in real-time.

### Activate the Virtual Environment

If you are in a new terminal session, reactivate the virtual environment:

```bash
cd ~/ssv2-quickstart
source ssv2_venv/bin/activate
```

### Run the Demo

```bash
python ssv2_demo.py
```

You should see output like:

```
Connecting to Snowflake...
  Database: SSV2_QUICKSTART_DB
  Schema:   SSV2_SCHEMA
  Pipe:     SSV2_QUICKSTART_USERS-streaming (default auto-created pipe)

Opening channel...
  Channel: SSV2_QUICKSTART_CHANNEL
  Status:  0
  Latest committed offset: None

Streaming 1800 rows (360 batches of 5) over ~3 minute(s)...
Watch your Streamlit dashboard to see data arrive in real-time!
```

Switch to your Streamlit dashboard tab — you should see the row count climbing, revenue accumulating, and the chart updating every 2 seconds.

> **What is happening behind the scenes?** The Python SDK sends batches of rows to Snowflake via a streaming channel. Snowflake's high-performance architecture uses a default auto-created pipe (`SSV2_QUICKSTART_USERS-streaming`) to ingest the data directly into the table — no staging files are involved.

<!---------------------------->

## Verify Results

Duration: 2

After the demo script finishes, verify that all rows arrived in the table.

### Check Row Count

Run in Snowsight:

```sql
SELECT COUNT(*) AS total_rows FROM SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_QUICKSTART_USERS;
```

You should see **1,800 rows** (or the total matching your `DEMO_MINUTES` setting).

### Sample the Data

```sql
SELECT *
FROM SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_QUICKSTART_USERS
ORDER BY user_id DESC
LIMIT 10;
```

### Check Revenue by Country

```sql
SELECT country, COUNT(*) AS users, SUM(order_amount) AS total_revenue
FROM SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_QUICKSTART_USERS
GROUP BY country
ORDER BY total_revenue DESC
LIMIT 10;
```

<!---------------------------->

## Clean Up

Duration: 2

Remove all Snowflake objects created during this quickstart. Run the following SQL in Snowsight:

```sql
DROP STREAMLIT IF EXISTS SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_LIVE_MONITOR;
DROP STAGE IF EXISTS SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_STREAMLIT_STAGE;
DROP TABLE IF EXISTS SSV2_QUICKSTART_DB.SSV2_SCHEMA.SSV2_QUICKSTART_USERS;
DROP SCHEMA IF EXISTS SSV2_QUICKSTART_DB.SSV2_SCHEMA;
DROP DATABASE IF EXISTS SSV2_QUICKSTART_DB;
DROP USER IF EXISTS SSV2_DEMO_USER;
DROP ROLE IF EXISTS SSV2_DEMO_ROLE;
```

Optionally, remove local files:

```bash
cd ~ && rm -rf ~/ssv2-quickstart
```

<!---------------------------->

## Conclusion And Resources

Duration: 1

Congratulations! You have successfully built an end-to-end real-time streaming pipeline using Snowpipe Streaming high-performance architecture and seen how Cortex Code can automate the entire workflow with a single prompt.

### What You Learned

- **Snowpipe Streaming high-performance architecture** uses default auto-created pipes — no `CREATE PIPE` SQL needed
- The default pipe follows the naming convention `<TABLE_NAME>-streaming` (with a **hyphen**)
- The Python SDK authenticates via **RSA key-pair (JWT)** and streams rows through channels
- **Streamlit in Snowflake** can be used to build real-time monitoring dashboards with zero local infrastructure
- **Cortex Code skills** can automate the entire workflow — from key generation to dashboard deployment — with a single prompt

### Related Resources

- [Snowpipe Streaming Documentation](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview)
- [Snowpipe Streaming Python SDK Reference](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-python-sdk)
- [Key-Pair Authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index)
- [Cortex Code Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
- [SSv2 Cortex Code Skills (GitHub)](https://github.com/sfc-gh-chathomas/SSv2-AI-Webinar)

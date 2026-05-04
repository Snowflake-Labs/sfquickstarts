author: Elizabeth Christensen
id: charts-graphs-and-ai-for-postgres-data-using-streamlit-and-cortex
summary: Build an IoT sensor dashboard with Snowflake Postgres, Streamlit in Snowflake, and a Cortex AI chatbot that answers questions about your data in plain English.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/product/applications-and-collaboration
environments: web
status: Published
language: en
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Streamlit, Postgres, AI, Cortex Analyst, IoT, Dashboard, Chatbot, Cortex Code

# Charts, Graphs, and AI for Postgres Data Using Streamlit and Cortex
<!-- ------------------------ -->
## Overview

In this quickstart, you will build a real-time IoT sensor dashboard powered by **Snowflake Postgres**, **Streamlit in Snowflake (SiS)**, and **Snowflake Cortex AI**. You will create a managed PostgreSQL instance, populate it with realistic smart-building sensor data, build interactive charts and filters, add a natural language chart generator, and wire up an AI chatbot that answers questions about your data in plain English using real numbers — all without leaving Snowflake.

This guide also shows you how to build the entire app using **Cortex Code (CoCo)** prompts — Snowflake's AI coding assistant. Each section includes the exact CoCo prompt you can use to generate that section of the app or you can skip to the bottom for the full CoCo prompt.

### What You Will Build
- A **Snowflake Postgres instance** loaded with IoT sensor data (buildings, sensors, readings)
- A **multi-page Streamlit dashboard** with KPI metrics, daily trend charts, and building summaries
- A **Charts on Demand** page with interactive filters, heatmaps, distribution histograms, and a **natural language chart generator** powered by Cortex AI
- An **AI Agent Search** chatbot that answers questions about your sensor data in plain English using real numbers from the database — not SQL queries
- A **Snow CLI deployment** using `snowflake.yml` for reproducible SiS deployments

### What You Will Learn
- How to create and configure a Snowflake Postgres instance
- How to generate realistic IoT data using PostgreSQL's `generate_series()` function
- How to build a multi-page Streamlit in Snowflake app with container runtime and `psycopg2`
- How to call Snowflake Cortex AI from both SiS (container runtime) and local development
- How to build a natural language chart generator (NL to SQL to chart)
- How to build an AI chatbot that gives direct answers with real data (not SQL queries) by injecting live data context into the prompt
- How to deploy to SiS using `snow streamlit deploy` with `snowflake.yml`
- How to pass Postgres credentials to container runtime using `.streamlit/secrets.toml` as a deployment artifact

### Prerequisites
- A role with the required privileges (see table below). **ACCOUNTADMIN** has all of these by default, but each can be granted individually to other roles.
- **Cortex AI** access — your role needs the `SNOWFLAKE.CORTEX_USER` database role
- A **warehouse** for the Streamlit app's query execution
- **Cortex Code CLI** (recommended, for AI-assisted development) — [getting started](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)

**Required privileges:**

| Privilege | What it's for | Grant statement |
|-----------|--------------|-----------------|
| `CREATE POSTGRES INSTANCE ON ACCOUNT` | Create the Postgres instance | `GRANT CREATE POSTGRES INSTANCE ON ACCOUNT TO ROLE my_role;` |
| `CREATE INTEGRATION ON ACCOUNT` | Create the External Access Integration | `GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE my_role;` |
| `CREATE NETWORK POLICY ON ACCOUNT` | Create network policies for Postgres ingress | `GRANT CREATE NETWORK POLICY ON ACCOUNT TO ROLE my_role;` |
| `CREATE STREAMLIT ON SCHEMA` | Create the Streamlit app | `GRANT CREATE STREAMLIT ON SCHEMA my_db.my_schema TO ROLE my_role;` |
| `SNOWFLAKE.CORTEX_USER` database role | Call Cortex AI LLM functions | `GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE my_role;` |

<!-- ------------------------ -->
## Create a Postgres Instance

In this step, you will create a managed PostgreSQL instance inside Snowflake and configure network access so your Streamlit app can connect to it.

### Step 1.1: Configure network access

Run the following in a **Snowsight SQL worksheet** with a role that has the required privileges (ACCOUNTADMIN works, or a custom role with the grants from the Prerequisites table):

```sql
CREATE NETWORK RULE IF NOT EXISTS iot_lab_ingress
  TYPE = IPV4
  VALUE_LIST = ('0.0.0.0/0')
  MODE = POSTGRES_INGRESS;

CREATE NETWORK POLICY IF NOT EXISTS iot_lab_policy
  ALLOWED_NETWORK_RULE_LIST = ('iot_lab_ingress');
```

> **Note:** The `0.0.0.0/0` rule allows connections from any IP address. This is fine for a lab environment. For production, restrict this to specific IP ranges or set up additional networking.

> **CoCo prompt:**
>
> ```
> Create a network rule and network policy for a Postgres instance.
> Allow all IPv4 ingress (0.0.0.0/0) for lab purposes.
> Name them iot_lab_ingress and iot_lab_policy.
> ```

### Step 1.2: Create the Postgres instance

```sql
CREATE POSTGRES INSTANCE iot_sensors
  COMPUTE_FAMILY = 'STANDARD_M'
  STORAGE_SIZE_GB = 10
  AUTHENTICATION_AUTHORITY = POSTGRES
  NETWORK_POLICY = 'iot_lab_policy'
  COMMENT = 'IoT sensor dashboard lab';
```

> **Tip:** This creates two users: `snowflake_admin` and `application` with auto-generated passwords. **Copy the passwords immediately** — they are only shown once.

### Step 1.3: Verify the instance is ready

```sql
-- Wait until state = READY (typically 3-5 minutes)
DESCRIBE POSTGRES INSTANCE iot_sensors;
```

### Step 1.4: Connect and verify

Using psql (replace `<hostname>` and `<password>` with your values):

```bash
psql "postgresql://snowflake_admin:<password>@<hostname>:5432/postgres?sslmode=require"
```

Run a quick test:

```sql
SELECT version();
```

You should see PostgreSQL 18 (or your selected version).

> **CoCo prompt:**
>
> ```
> Create a Snowflake Postgres instance called iot_sensors with STANDARD_M
> compute, 10GB storage, and the iot_lab_policy network policy. Then save
> the connection details when it is ready for building with this instance.
> ```

<!-- ------------------------ -->
## Generate IoT Sensor Data

Now you will create the schema and generate realistic smart-building sensor data entirely with SQL — no external files or downloads needed.

### Step 2.1: Create the schema

Connect to your Postgres instance and run:

```sql
-- Buildings in the sensor network
CREATE TABLE buildings (
    building_id   SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    location      TEXT NOT NULL,
    floors        INT NOT NULL
);

-- Sensors installed in buildings
CREATE TABLE sensors (
    sensor_id        SERIAL PRIMARY KEY,
    building_id      INT NOT NULL REFERENCES buildings(building_id),
    sensor_type      TEXT NOT NULL,    -- 'temperature', 'humidity', 'energy'
    unit             TEXT NOT NULL,    -- '°F', '%RH', 'kW'
    install_location TEXT NOT NULL,    -- e.g. 'Floor 1 - Lobby'
    is_active        BOOLEAN DEFAULT TRUE
);

-- Time-series sensor readings
CREATE TABLE readings (
    reading_id    BIGSERIAL PRIMARY KEY,
    sensor_id     INT NOT NULL REFERENCES sensors(sensor_id),
    reading_time  TIMESTAMP NOT NULL,
    value         NUMERIC(10,2) NOT NULL
);

-- Index for efficient time-range queries
CREATE INDEX idx_readings_sensor_time ON readings(sensor_id, reading_time);
CREATE INDEX idx_readings_time ON readings(reading_time);
```

### Step 2.2: Seed buildings and sensors

```sql
INSERT INTO buildings (name, location, floors) VALUES
    ('HQ Tower',        'Downtown Campus',  12),
    ('Data Center',     'East Campus',       3),
    ('Warehouse Alpha', 'West Campus',       1);

INSERT INTO sensors (building_id, sensor_type, unit, install_location) VALUES
    -- HQ Tower
    (1, 'temperature', '°F',  'Floor 1 - Lobby'),
    (1, 'temperature', '°F',  'Floor 6 - Office'),
    (1, 'temperature', '°F',  'Floor 12 - Executive'),
    (1, 'humidity',    '%RH', 'Floor 1 - Lobby'),
    (1, 'humidity',    '%RH', 'Floor 6 - Office'),
    (1, 'energy',      'kW',  'Main Panel'),
    -- Data Center
    (2, 'temperature', '°F',  'Server Room A'),
    (2, 'temperature', '°F',  'Server Room B'),
    (2, 'humidity',    '%RH', 'Server Room A'),
    (2, 'energy',      'kW',  'UPS System'),
    (2, 'energy',      'kW',  'Cooling Unit'),
    -- Warehouse Alpha
    (3, 'temperature', '°F',  'Loading Dock'),
    (3, 'temperature', '°F',  'Cold Storage'),
    (3, 'humidity',    '%RH', 'Cold Storage'),
    (3, 'energy',      'kW',  'Main Panel');
```

### Step 2.3: Generate realistic sensor readings

This query generates 30 days of readings at 15-minute intervals for every sensor. The values follow realistic patterns — daily temperature cycles, stable data center temps, and energy usage that peaks during business hours:

```sql
INSERT INTO readings (sensor_id, reading_time, value)
SELECT
    s.sensor_id,
    ts,
    CASE s.sensor_type
        -- Temperature: sine wave for daily cycle + random noise
        WHEN 'temperature' THEN
            CASE
                -- Data center server rooms: tight 65-72°F range
                WHEN s.install_location LIKE 'Server Room%' THEN
                    round((68 + 3 * sin(extract(HOUR FROM ts) * pi() / 12)
                           + (random() - 0.5) * 2)::numeric, 2)
                -- Cold storage: 34-38°F
                WHEN s.install_location = 'Cold Storage' THEN
                    round((36 + 1.5 * sin(extract(HOUR FROM ts) * pi() / 12)
                           + (random() - 0.5) * 1)::numeric, 2)
                -- Office/lobby: 68-78°F daily cycle
                ELSE
                    round((72 + 4 * sin((extract(HOUR FROM ts) - 6) * pi() / 12)
                           + (random() - 0.5) * 3)::numeric, 2)
            END
        -- Humidity: inverse of temperature pattern
        WHEN 'humidity' THEN
            CASE
                WHEN s.install_location LIKE 'Server Room%' THEN
                    round((45 + 3 * sin(extract(HOUR FROM ts) * pi() / 12)
                           + (random() - 0.5) * 2)::numeric, 2)
                WHEN s.install_location = 'Cold Storage' THEN
                    round((80 + 5 * sin(extract(HOUR FROM ts) * pi() / 12)
                           + (random() - 0.5) * 3)::numeric, 2)
                ELSE
                    round((50 + 8 * sin((extract(HOUR FROM ts) - 6) * pi() / 12)
                           + (random() - 0.5) * 4)::numeric, 2)
            END
        -- Energy: peaks during business hours (8am-6pm)
        WHEN 'energy' THEN
            CASE
                WHEN s.install_location = 'UPS System' THEN
                    round((200 + 80 * GREATEST(0, sin((extract(HOUR FROM ts) - 6) * pi() / 12))
                           + (random() - 0.5) * 20)::numeric, 2)
                WHEN s.install_location = 'Cooling Unit' THEN
                    round((150 + 100 * GREATEST(0, sin((extract(HOUR FROM ts) - 8) * pi() / 10))
                           + (random() - 0.5) * 15)::numeric, 2)
                ELSE
                    round((120 + 60 * GREATEST(0, sin((extract(HOUR FROM ts) - 7) * pi() / 11))
                           + (random() - 0.5) * 10)::numeric, 2)
            END
    END
FROM sensors s
CROSS JOIN generate_series(
    now() - INTERVAL '30 days',
    now(),
    INTERVAL '15 minutes'
) AS ts;
```

### Step 2.4: Verify the data

```sql
SELECT count(*) AS total_readings FROM readings;

SELECT s.sensor_type, count(*) AS readings, round(avg(r.value), 1) AS avg_value
FROM readings r
JOIN sensors s ON r.sensor_id = s.sensor_id
GROUP BY s.sensor_type
ORDER BY readings DESC;
```

You should see approximately 43,000 total readings across temperature, humidity, and energy sensors.

> **CoCo prompt:**
>
> ```
> Connect to my iot_sensors Postgres instance and create a schema for
> IoT sensor data: buildings, sensors, and readings tables. Then generate
> 30 days of realistic smart-building sensor readings at 15-minute
> intervals using generate_series(). Include temperature (with daily
> cycles), humidity, and energy (with business-hour peaks) sensors
> across 3 buildings. Verify the data loaded correctly.
> ```

<!-- ------------------------ -->
## Set Up Networking and Dependencies

The container runtime needs an **External Access Integration (EAI)** to make outbound connections to PyPI (for package installs) and to your Postgres instance. Cortex AI calls go through the Snowpark session internally, so no outbound egress rule is needed for Cortex.

### Step 3.1: Create the EAI

Run this in a Snowsight SQL worksheet. Replace `<your-postgres-hostname>` with your actual Postgres host from Step 2.3:

```sql
CREATE OR REPLACE NETWORK RULE iot_app_egress
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = (
    'pypi.org',
    'files.pythonhosted.org',
    '<your-postgres-hostname>:5432'
  );

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION iot_app_eai
  ALLOWED_NETWORK_RULES = (iot_app_egress)
  ENABLED = TRUE;
```

> **CoCo prompt:**
>
> ```
> Create an egress network rule that allows outbound access to PyPI
> (pypi.org, files.pythonhosted.org) and my iot_sensors Postgres host
> on port 5432. Then create an External Access Integration called
> iot_app_eai. My Postgres host is <paste-your-host-here>.
> ```

### Step 3.2: Create the database and schema

If you don't already have a database and schema for the app:

```sql
CREATE DATABASE IF NOT EXISTS iot_lab;
CREATE SCHEMA IF NOT EXISTS iot_lab.sensors;
```

### Step 3.3: Project structure

Create a project directory with this structure:

```
iot-streamlit-dashboard/
  streamlit_app.py          # Main entry point
  data.py                   # Shared Postgres connection + query layer
  cortex_ai.py              # Cortex AI helper functions
  pyproject.toml            # Dependencies
  snowflake.yml             # SiS deployment manifest
  .streamlit/
    secrets.toml            # Postgres connection credentials
  app_pages/
    home.py                 # Dashboard page
    charts.py               # Charts on Demand page
    agent.py                # AI Agent Search page
```

### Step 3.4: Add dependencies — `pyproject.toml`

```toml
[project]
name = "iot-streamlit-dashboard"
version = "0.1.0"
requires-python = ">=3.11"
    dependencies = [
        "streamlit>=1.54.0",
        "psycopg2-binary>=2.9.10",
        "snowflake-connector-python>=3.3.0",
        "snowflake-ml-python>=1.7.0",
        "altair>=5.5.0",
        "pandas>=2.2.0",
        "numpy>=1.26.0",
    ]
```

### Step 3.5: Add connection secrets — `.streamlit/secrets.toml`

```toml
[postgres]
host = "<your-postgres-hostname>"
port = 5432
dbname = "postgres"
user = "snowflake_admin"
password = "<your-password>"

[snowflake_cortex]
connection_name = "<your-snowflake-connection>"
```

Replace the placeholder values with your actual Postgres connection details (from Step 2.3) and your Snowflake connection name from `~/.snowflake/connections.toml`.

> **Important:** The `[postgres]` section is needed in both local development and SiS. The `[snowflake_cortex]` section is only needed for local development — in SiS, Cortex AI calls go through `st.connection("snowflake")` automatically. When deploying to SiS, you **must include `.streamlit/secrets.toml` in your deployment artifacts** (see Step 9). Without it, psycopg2 will fail with `fe_sendauth: no password supplied`.

### Step 3.6: Deployment manifest — `snowflake.yml`

```yaml
definition_version: 2
entities:
  iot_streamlit_dashboard:
    type: streamlit
    identifier:
      name: IOT_STREAMLIT_DASHBOARD
      database: IOT_LAB
      schema: SENSORS
    query_warehouse: <your-warehouse>
    compute_pool: <your-compute-pool>
    runtime_name: SYSTEM$ST_CONTAINER_RUNTIME_PY3_11
    external_access_integrations:
      - IOT_APP_EAI
    main_file: streamlit_app.py
    artifacts:
      - streamlit_app.py
      - pyproject.toml
      - data.py
      - cortex_ai.py
      - app_pages/home.py
      - app_pages/charts.py
      - app_pages/agent.py
      - .streamlit/secrets.toml
```

> **Tip:** Notice that `.streamlit/secrets.toml` is listed in `artifacts`. This is the key to making Postgres credentials available in the container runtime. Without this, `st.secrets["postgres"]` will not find the password and the app will fail to connect.

> **CoCo prompt:**
>
> ```
> I am building a Streamlit app in Snowflake (SiS) called IOT Streamlit Dashboard for Streamlit in Snowflake that connects
> to my iot_sensors Postgres instance. Create the project skeleton:
> pyproject.toml (with streamlit, psycopg2-binary, snowflake-connector-python,
> altair, pandas, numpy), .streamlit/secrets.toml with [postgres] section,
> and snowflake.yml for SiS container runtime deployment with the EAI
> iot_app_eai. Include .streamlit/secrets.toml in the deployment artifacts and use the saved Postgres credentials for the secrets file.
> ```

<!-- ------------------------ -->
## Build the Data Layer

The data layer provides a shared Postgres connection and cached query functions used by all three pages.

### `data.py`

```python
"""Shared database connection and query functions for the IOT dashboard."""

import psycopg2
import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Postgres connection
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_pg_connection():
    """Create a persistent Postgres connection.

    Reads credentials from .streamlit/secrets.toml (works both locally and in
    SiS when the secrets file is included in the deployment artifacts).
    """
    pg = st.secrets["postgres"]
    conn = psycopg2.connect(
        host=pg["host"],
        port=pg["port"],
        dbname=pg["dbname"],
        user=pg["user"],
        password=pg["password"],
        sslmode="require",
    )
    conn.autocommit = True
    return conn


def run_pg_query(sql: str) -> pd.DataFrame:
    """Run a SQL query against the Postgres instance and return a DataFrame."""
    conn = _get_pg_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(sql, conn)
    except Exception:
        st.cache_resource.clear()
        try:
            conn = _get_pg_connection()
            return pd.read_sql_query(sql, conn)
        except Exception as retry_err:
            st.error(f"Query failed: {retry_err}")
            return pd.DataFrame()


@st.cache_data(ttl=300)
def get_buildings() -> pd.DataFrame:
    return run_pg_query("SELECT * FROM buildings ORDER BY building_id")


@st.cache_data(ttl=300)
def get_sensors() -> pd.DataFrame:
    return run_pg_query("SELECT * FROM sensors ORDER BY sensor_id")


@st.cache_data(ttl=300)
def get_sensor_summary() -> pd.DataFrame:
    return run_pg_query("""
        SELECT
            s.sensor_type,
            s.unit,
            COUNT(DISTINCT s.sensor_id) AS sensor_count,
            COUNT(r.reading_id) AS total_readings,
            ROUND(AVG(r.value)::numeric, 2) AS avg_value,
            ROUND(MIN(r.value)::numeric, 2) AS min_value,
            ROUND(MAX(r.value)::numeric, 2) AS max_value
        FROM sensors s
        JOIN readings r ON s.sensor_id = r.sensor_id
        GROUP BY s.sensor_type, s.unit
        ORDER BY s.sensor_type
    """)


@st.cache_data(ttl=300)
def get_building_summary() -> pd.DataFrame:
    return run_pg_query("""
        SELECT
            b.name AS building,
            b.location,
            COUNT(DISTINCT s.sensor_id) AS sensors,
            COUNT(r.reading_id) AS readings,
            ROUND(AVG(r.value)::numeric, 2) AS avg_value
        FROM buildings b
        JOIN sensors s ON b.building_id = s.building_id
        JOIN readings r ON s.sensor_id = r.sensor_id
        GROUP BY b.name, b.location
        ORDER BY b.name
    """)


@st.cache_data(ttl=300)
def get_daily_avg_by_type() -> pd.DataFrame:
    return run_pg_query("""
        SELECT
            DATE(r.reading_time) AS day,
            s.sensor_type,
            ROUND(AVG(r.value)::numeric, 2) AS avg_value
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        GROUP BY DATE(r.reading_time), s.sensor_type
        ORDER BY day
    """)


@st.cache_data(ttl=300)
def get_hourly_avg(sensor_type: str, building: str | None = None) -> pd.DataFrame:
    where = "AND s.sensor_type = %s"
    params = [sensor_type]
    if building:
        where += " AND b.name = %s"
        params.append(building)

    sql = f"""
        SELECT
            DATE(r.reading_time) AS day,
            EXTRACT(HOUR FROM r.reading_time)::int AS hour,
            ROUND(AVG(r.value)::numeric, 2) AS avg_value
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        JOIN buildings b ON s.building_id = b.building_id
        WHERE 1=1 {where}
        GROUP BY DATE(r.reading_time), EXTRACT(HOUR FROM r.reading_time)
        ORDER BY day, hour
    """
    conn = _get_pg_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        st.cache_resource.clear()
        conn = _get_pg_connection()
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=300)
def get_readings_by_sensor(sensor_type: str, building: str | None = None,
                           days: int = 7) -> pd.DataFrame:
    where = "AND s.sensor_type = %s"
    params: list = [sensor_type]
    if building:
        where += " AND b.name = %s"
        params.append(building)

    sql = f"""
        SELECT
            r.reading_time,
            s.install_location AS location,
            b.name AS building,
            r.value,
            s.unit
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        JOIN buildings b ON s.building_id = b.building_id
        WHERE r.reading_time >= NOW() - INTERVAL '{days} days'
        {where}
        ORDER BY r.reading_time
    """
    conn = _get_pg_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        st.cache_resource.clear()
        conn = _get_pg_connection()
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=300)
def get_latest_readings() -> pd.DataFrame:
    return run_pg_query("""
        SELECT DISTINCT ON (s.sensor_id)
            b.name AS building,
            s.sensor_type,
            s.install_location AS location,
            r.value,
            s.unit,
            r.reading_time AS last_reading
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        JOIN buildings b ON s.building_id = b.building_id
        ORDER BY s.sensor_id, r.reading_time DESC
    """)


@st.cache_data(ttl=300)
def get_readings_for_chart(sensor_type: str, building: str | None = None,
                           days: int = 30) -> pd.DataFrame:
    where = "AND s.sensor_type = %s"
    params: list = [sensor_type]
    if building:
        where += " AND b.name = %s"
        params.append(building)

    sql = f"""
        SELECT
            r.reading_time,
            b.name AS building,
            s.install_location AS location,
            r.value
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        JOIN buildings b ON s.building_id = b.building_id
        WHERE r.reading_time >= NOW() - INTERVAL '{days} days'
        {where}
        ORDER BY r.reading_time
    """
    conn = _get_pg_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        st.cache_resource.clear()
        conn = _get_pg_connection()
        return pd.read_sql_query(sql, conn, params=params)
```

Key design decisions:
- **`st.secrets["postgres"]`** reads from `.streamlit/secrets.toml` — this works identically in local dev and in SiS when the file is deployed as an artifact
- **`@st.cache_resource`** keeps a single persistent connection across reruns
- **`@st.cache_data(ttl=300)`** caches query results for 5 minutes
- **Retry logic** clears the cached connection and reconnects if a query fails (handles stale connections)

> **CoCo prompt:**
>
> ```
> Create a data.py module with a shared Postgres connection using
> st.secrets["postgres"] and psycopg2. Add cached query functions for:
> get_buildings, get_sensors, get_sensor_summary, get_building_summary,
> get_daily_avg_by_type, get_hourly_avg (with sensor_type and optional
> building filters), get_readings_by_sensor, get_latest_readings, and
> get_readings_for_chart. Use @st.cache_data with 5-minute TTL and
> retry logic for stale connections.
> ```

<!-- ------------------------ -->
## Build the Cortex AI Layer

The Cortex AI helper provides a dual-mode interface — it detects whether the app is running in SiS or locally and calls Cortex accordingly.

### `cortex_ai.py`

```python
"""Shared Snowflake Cortex AI helper functions."""

import os
import streamlit as st


def _is_sis() -> bool:
    """Return True if running inside Streamlit in Snowflake (container runtime)."""
    return os.path.exists("/opt/streamlit-runtime")


def cortex_complete(prompt: str) -> str:
    """Call Snowflake Cortex COMPLETE and return the response text."""
    escaped = prompt.replace("\\", "\\\\").replace("'", "\\'")
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', '{escaped}')"

    if _is_sis():
        conn = st.connection("snowflake")
        df = conn.query(sql, ttl=0)
        if not df.empty:
            return df.iloc[0, 0]
    else:
        import snowflake.connector

        @st.cache_resource
        def _get_sf_conn():
            conn_name = st.secrets["snowflake_cortex"]["connection_name"]
            return snowflake.connector.connect(connection_name=conn_name)

        conn = _get_sf_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            result = cursor.fetchone()
        except Exception:
            st.cache_resource.clear()
            conn = _get_sf_conn()
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchone()
        finally:
            cursor.close()
        if result and result[0]:
            return result[0]

    return "Sorry, I couldn't generate a response."


def cortex_complete_stream(prompt: str):
    """Yield Cortex COMPLETE response in chunks for streaming UX."""
    response = cortex_complete(prompt)
    words = response.split(" ")
    chunk = []
    for word in words:
        chunk.append(word)
        if len(chunk) >= 3:
            yield " ".join(chunk) + " "
            chunk = []
    if chunk:
        yield " ".join(chunk)
```

How the dual-mode works:

- **In SiS (container runtime):** Detects SiS via `/opt/streamlit-runtime` and calls Cortex through `st.connection("snowflake")`, which uses the built-in Snowpark session. No extra credentials needed.
- **In local dev:** Uses `snowflake-connector-python` with `connection_name` from `~/.snowflake/connections.toml` (supports OAuth, SSO, and other auth methods). The connection name is read from `.streamlit/secrets.toml`.

> **Why not `get_active_session()`?** The `snowflake.snowpark.context.get_active_session()` approach works in SiS but requires `snowflake-snowpark-python` as a dependency and doesn't work for local development. The dual-mode approach here works in both environments without Snowpark.

> **Why not `_snowflake`?** The `_snowflake` module is only available in classic SiS runtime, not container runtime. If you see `ModuleNotFoundError: No module named '_snowflake'`, you're on container runtime and should use `st.connection("snowflake")` instead.

> **CoCo prompt:**
>
> ```
    > Create a cortex_ai.py module with dual-mode Cortex AI support.
    > In SiS (detect via /opt/streamlit-runtime), use st.connection("snowflake").
    > Locally, use snowflake-connector-python with connection_name from
    > st.secrets["snowflake_cortex"]["connection_name"]. Include a
    > cortex_complete() function and a cortex_complete_stream() function
    > that yields word chunks for streaming UX. Use llama3.1-70b model.
    > Add snowflake-ml-python to pyproject.toml (provides snowflake.cortex).
> ```

<!-- ------------------------ -->
## Build the Dashboard Pages

Now build the three app pages. The main entry point uses `st.navigation` for top-bar navigation.

### `streamlit_app.py` — Main entry point

```python
"""IOT Streamlit Dashboard - Main Entry Point"""

import streamlit as st

page = st.navigation(
    [
        st.Page("app_pages/home.py", title="Dashboard", icon=":material/dashboard:"),
        st.Page("app_pages/charts.py", title="Charts on Demand", icon=":material/bar_chart:"),
        st.Page("app_pages/agent.py", title="AI Agent Search", icon=":material/smart_toy:"),
    ],
    position="top",
)

page.run()
```

### `app_pages/home.py` — Dashboard landing page

```python
"""Landing page - KPI cards and overview charts."""

import pandas as pd
import altair as alt
import streamlit as st
from data import (
    get_sensor_summary,
    get_building_summary,
    get_daily_avg_by_type,
    get_latest_readings,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
sensor_summary = get_sensor_summary()
building_summary = get_building_summary()
daily_avg = get_daily_avg_by_type()
latest = get_latest_readings()

# Cast numeric columns
for df in [sensor_summary, building_summary, daily_avg, latest]:
    for col in df.columns:
        if col in ("avg_value", "min_value", "max_value", "value", "sensor_count",
                    "total_readings", "sensors", "readings"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# :material/sensors: IOT Streamlit Dashboard")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
if not sensor_summary.empty:
    total_sensors = int(sensor_summary["sensor_count"].sum())
    total_readings = int(sensor_summary["total_readings"].sum())
    sensor_types = len(sensor_summary)

    with st.container(horizontal=True):
        st.metric("Total Sensors", total_sensors, border=True)
        st.metric("Total Readings", f"{total_readings:,}", border=True)
        st.metric("Sensor Types", sensor_types, border=True)
        if not building_summary.empty:
            st.metric("Buildings", len(building_summary), border=True)

# ---------------------------------------------------------------------------
# Sensor type summary cards
# ---------------------------------------------------------------------------
st.subheader("Sensor Overview")

if not sensor_summary.empty:
    cols = st.columns(len(sensor_summary))
    for i, (_, row) in enumerate(sensor_summary.iterrows()):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{row['sensor_type'].title()}** ({row['unit']})")
                st.metric("Avg", f"{row['avg_value']:.1f}", border=True)
                with st.container(horizontal=True):
                    st.metric("Min", f"{row['min_value']:.1f}", border=True)
                    st.metric("Max", f"{row['max_value']:.1f}", border=True)

# ---------------------------------------------------------------------------
# Daily trend chart
# ---------------------------------------------------------------------------
st.subheader("Daily Averages by Sensor Type")

if not daily_avg.empty:
    daily_avg["day"] = pd.to_datetime(daily_avg["day"])

    chart = (
        alt.Chart(daily_avg)
        .mark_line(point=False)
        .encode(
            x=alt.X("day:T", title=None),
            y=alt.Y("avg_value:Q", title="Average Value"),
            color=alt.Color("sensor_type:N", title="Sensor Type"),
            tooltip=[
                alt.Tooltip("day:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("sensor_type:N", title="Type"),
                alt.Tooltip("avg_value:Q", title="Avg Value", format=",.2f"),
            ],
        )
        .properties(height=350)
    )
    st.altair_chart(chart)

# ---------------------------------------------------------------------------
# Building summary and latest readings
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Readings by Building")
    if not building_summary.empty:
        st.dataframe(
            building_summary,
            hide_index=True,
            column_config={
                "building": st.column_config.TextColumn("Building"),
                "location": st.column_config.TextColumn("Location"),
                "sensors": st.column_config.NumberColumn("Sensors"),
                "readings": st.column_config.NumberColumn("Readings", format="%d"),
                "avg_value": st.column_config.NumberColumn("Avg Value", format="%.2f"),
            },
        )

with col2:
    st.subheader("Latest Sensor Readings")
    if not latest.empty:
        latest["last_reading"] = pd.to_datetime(latest["last_reading"])
        st.dataframe(
            latest,
            hide_index=True,
            column_config={
                "building": st.column_config.TextColumn("Building"),
                "sensor_type": st.column_config.TextColumn("Type"),
                "location": st.column_config.TextColumn("Location"),
                "value": st.column_config.NumberColumn("Value", format="%.2f"),
                "unit": st.column_config.TextColumn("Unit"),
                "last_reading": st.column_config.DatetimeColumn(
                    "Last Reading", format="MMM DD, YYYY HH:mm"
                ),
            },
        )
```

> **CoCo prompt:**
>
> ```
> Build the Dashboard landing page (app_pages/home.py) for my IOT
> Streamlit Dashboard. It should show:
> 1. KPI row with total sensors, total readings, sensor types, buildings
> 2. Sensor overview cards showing avg/min/max for each sensor type
> 3. An Altair line chart of daily averages by sensor type
> 4. A two-column layout with building summary table and latest readings table
> Import data functions from the data.py module.
> ```

<!-- ------------------------ -->
## Build the Charts on Demand Page

This page provides interactive filtering and a **natural language chart generator** where users describe the chart they want in plain English and Cortex AI builds it.

### `app_pages/charts.py`

```python
"""Charts on Demand - Interactive sensor data exploration."""

import pandas as pd
import altair as alt
import streamlit as st
from data import get_buildings, get_readings_for_chart, get_hourly_avg
from cortex_ai import cortex_complete_stream

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# :material/bar_chart: Charts on Demand")
st.caption("Select a sensor type, building, and time range to generate charts.")

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
buildings_df = get_buildings()
building_names = buildings_df["name"].tolist() if not buildings_df.empty else []

with st.container(horizontal=True):
    sensor_type = st.selectbox(
        "Sensor Type",
        ["temperature", "humidity", "energy"],
        key="chart_sensor_type",
    )
    building = st.selectbox(
        "Building",
        ["All Buildings"] + building_names,
        key="chart_building",
    )
    days = st.selectbox(
        "Time Range",
        [7, 14, 30],
        format_func=lambda d: f"Last {d} days",
        key="chart_days",
    )

selected_building = None if building == "All Buildings" else building

UNITS = {"temperature": "°F", "humidity": "%RH", "energy": "kW"}
unit = UNITS.get(sensor_type, "")

# ---------------------------------------------------------------------------
# Time series chart
# ---------------------------------------------------------------------------
st.subheader(f"{sensor_type.title()} Over Time")

readings = get_readings_for_chart(sensor_type, selected_building, days)

if readings.empty:
    st.info("No data found for the selected filters.")
else:
    readings["reading_time"] = pd.to_datetime(readings["reading_time"])
    readings["value"] = pd.to_numeric(readings["value"], errors="coerce")

    # Build label for each series: "Building - Location"
    readings["series"] = readings["building"] + " - " + readings["location"]

    line_chart = (
        alt.Chart(readings)
        .mark_line(opacity=0.8)
        .encode(
            x=alt.X("reading_time:T", title=None),
            y=alt.Y("value:Q", title=f"{sensor_type.title()} ({unit})"),
            color=alt.Color("series:N", title="Sensor"),
            tooltip=[
                alt.Tooltip("reading_time:T", title="Time", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("series:N", title="Sensor"),
                alt.Tooltip("value:Q", title="Value", format=",.2f"),
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(line_chart)

    # -------------------------------------------------------------------
    # Summary statistics
    # -------------------------------------------------------------------
    st.subheader("Summary Statistics")
    stats = (
        readings.groupby("series")["value"]
        .agg(["mean", "min", "max", "std", "count"])
        .round(2)
        .reset_index()
    )
    stats.columns = ["Sensor", "Mean", "Min", "Max", "Std Dev", "Readings"]
    st.dataframe(stats, hide_index=True)

# ---------------------------------------------------------------------------
# Heatmap: hourly average
# ---------------------------------------------------------------------------
st.subheader(f"Hourly Average {sensor_type.title()} Heatmap")

hourly = get_hourly_avg(sensor_type, selected_building)

if hourly.empty:
    st.info("No hourly data available.")
else:
    hourly["day"] = pd.to_datetime(hourly["day"])
    hourly["hour"] = pd.to_numeric(hourly["hour"], errors="coerce").astype(int)
    hourly["avg_value"] = pd.to_numeric(hourly["avg_value"], errors="coerce")

    heatmap = (
        alt.Chart(hourly)
        .mark_rect()
        .encode(
            x=alt.X("hour:O", title="Hour of Day"),
            y=alt.Y("day:T", title=None),
            color=alt.Color(
                "avg_value:Q",
                title=f"Avg {unit}",
                scale=alt.Scale(scheme="redyellowgreen" if sensor_type == "temperature" else "blues"),
            ),
            tooltip=[
                alt.Tooltip("day:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("hour:O", title="Hour"),
                alt.Tooltip("avg_value:Q", title="Avg Value", format=",.2f"),
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(heatmap)

# ---------------------------------------------------------------------------
# Distribution chart
# ---------------------------------------------------------------------------
st.subheader(f"{sensor_type.title()} Value Distribution")

if not readings.empty:
    histogram = (
        alt.Chart(readings)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X("value:Q", bin=alt.Bin(maxbins=40), title=f"{sensor_type.title()} ({unit})"),
            y=alt.Y("count():Q", title="Frequency"),
            color=alt.Color("building:N", title="Building"),
            tooltip=[
                alt.Tooltip("value:Q", bin=alt.Bin(maxbins=40), title="Value Range"),
                alt.Tooltip("count():Q", title="Count"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(histogram)

# ---------------------------------------------------------------------------
# Natural Language Chart Generator
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader(":material/smart_toy: Generate a Chart with AI")
st.caption("Describe the chart you want in plain English and AI will build it for you.")

NL_CHART_PROMPT = """You are a PostgreSQL query generator for an IoT sensor database.
Given a user's natural language request, generate ONLY a JSON object with these fields:
- "sql": a valid PostgreSQL SELECT query
- "chart_type": one of "line", "bar", "area", "scatter"
- "x": the column name for the x-axis
- "y": the column name(s) for the y-axis (string or list of strings)
- "color": optional column name for color grouping (or null)
- "title": a short chart title

DATABASE SCHEMA:
- buildings (building_id INT PK, name TEXT, location TEXT, floors INT)
  Data: HQ Tower (Downtown Campus, 12 floors), Data Center (East Campus, 3 floors), Warehouse Alpha (West Campus, 1 floor)
- sensors (sensor_id INT PK, building_id INT FK, sensor_type TEXT, unit TEXT, install_location TEXT, is_active BOOLEAN)
  Types: temperature (°F), humidity (%RH), energy (kW). 15 sensors total.
- readings (reading_id BIGINT PK, sensor_id INT FK, reading_time TIMESTAMP, value NUMERIC(10,2))
  ~43,000 readings over 30 days.

RULES:
- Return ONLY valid JSON. No markdown, no explanation, no code fences.
- Always alias columns to short readable names (e.g. AS day, AS avg_temp).
- Use ROUND() for averages. Use DATE() or date_trunc() for time grouping.
- Always ORDER BY the x-axis column.
- Limit to 1000 rows max.

User request: {request}
"""

SUGGESTIONS_NL = [
    "Average temperature per building over time",
    "Daily energy usage comparison across buildings",
    "Humidity distribution by building as a bar chart",
    "Hourly temperature pattern for Data Center",
    "Energy consumption trend last 7 days",
]

if "nl_chart_history" not in st.session_state:
    st.session_state.nl_chart_history = []

# Suggestion pills
selected_suggestion = st.pills(
    "Try these:",
    SUGGESTIONS_NL,
    label_visibility="collapsed",
    key="nl_chart_suggestions",
)

nl_input = st.text_input(
    "Describe the chart you want:",
    value=selected_suggestion or "",
    placeholder="e.g. Show me average temperature by building over time as a line chart",
    key="nl_chart_input",
)

if st.button("Generate Chart", type="primary", key="nl_chart_btn") and nl_input:
    import json
    from data import run_pg_query
    from cortex_ai import cortex_complete

    with st.spinner("Generating chart..."):
        prompt = NL_CHART_PROMPT.format(request=nl_input)
        raw = cortex_complete(prompt)

        # Parse JSON from response (strip any accidental markdown fences)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            spec = json.loads(cleaned)
        except json.JSONDecodeError:
            st.error("AI returned invalid JSON. Try rephrasing your request.")
            st.code(raw, language="text")
            spec = None

    if spec:
        sql = spec.get("sql", "")
        chart_type = spec.get("chart_type", "line")
        x_col = spec.get("x", "")
        y_col = spec.get("y", "")
        color_col = spec.get("color")
        title = spec.get("title", nl_input)

        with st.expander("Generated SQL", expanded=False):
            st.code(sql, language="sql")

        df_result = run_pg_query(sql)

        if df_result.empty:
            st.warning("Query returned no data. Try a different request.")
        else:
            # Cast numeric columns
            if isinstance(y_col, list):
                y_cols = y_col
            else:
                y_cols = [y_col]
            for yc in y_cols:
                if yc in df_result.columns:
                    df_result[yc] = pd.to_numeric(df_result[yc], errors="coerce")
            if x_col in df_result.columns:
                # Try to parse as datetime
                try:
                    df_result[x_col] = pd.to_datetime(df_result[x_col])
                except (ValueError, TypeError):
                    pass

            st.markdown(f"**{title}**")

            if len(y_cols) == 1:
                y_arg = y_cols[0]
            else:
                y_arg = y_cols

            chart_args = {"x": x_col, "y": y_arg}
            if color_col and color_col in df_result.columns:
                chart_args["color"] = color_col

            if chart_type == "bar":
                st.bar_chart(df_result, **chart_args)
            elif chart_type == "area":
                st.area_chart(df_result, **chart_args)
            elif chart_type == "scatter":
                st.scatter_chart(df_result, **chart_args)
            else:
                st.line_chart(df_result, **chart_args)

            with st.expander("View data", expanded=False):
                st.dataframe(df_result, hide_index=True)

            # Save to history
            st.session_state.nl_chart_history.append(
                {"request": nl_input, "title": title}
            )

# Show history
if st.session_state.nl_chart_history:
    with st.expander(f"Chart history ({len(st.session_state.nl_chart_history)})"):
        for i, item in enumerate(reversed(st.session_state.nl_chart_history), 1):
            st.markdown(f"{i}. **{item['title']}** -- _{item['request']}_")
```

### How the NL chart generator works

1. The user types a plain-English description (e.g. "Average temperature per building over time")
2. Cortex AI generates a JSON spec with the SQL query, chart type, axis columns, and title
3. The app runs the SQL against Postgres and renders the chart using Streamlit's built-in chart functions
4. The generated SQL is shown in a collapsed expander for transparency

> **CoCo prompt:**
>
> ```
> Add a natural language chart generator to my Charts on Demand page.
> The user describes a chart in plain English, Cortex AI generates a
> JSON object with {sql, chart_type, x, y, color, title}, the app
> runs the SQL against Postgres and renders the chart. Include suggestion
> pills, a text input, and chart history. Use st.line_chart/bar_chart/
> area_chart/scatter_chart based on the chart_type.
> ```

<!-- ------------------------ -->
## Build the AI Agent Search Page

The AI Agent Search page is the key differentiator of this app. Unlike traditional text-to-SQL chatbots that return SQL queries for the user to run, this chatbot **pre-fetches live data from Postgres and injects it into the prompt** so the LLM can answer directly with real numbers.

### `app_pages/agent.py`

```python
"""AI Agent Search - Ask questions about your IoT sensor data using Cortex AI."""

import streamlit as st
from data import run_pg_query
from cortex_ai import cortex_complete_stream

# ---------------------------------------------------------------------------
# Pre-fetch live data summaries so the LLM can answer with real numbers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _build_data_context() -> str:
    """Query the Postgres database and build a data context string for the LLM."""
    parts = []

    # Sensor summary
    df = run_pg_query("""
        SELECT s.sensor_type, s.unit,
               COUNT(DISTINCT s.sensor_id) AS sensors,
               COUNT(r.reading_id) AS readings,
               ROUND(AVG(r.value)::numeric, 1) AS avg_val,
               ROUND(MIN(r.value)::numeric, 1) AS min_val,
               ROUND(MAX(r.value)::numeric, 1) AS max_val
        FROM sensors s JOIN readings r ON s.sensor_id = r.sensor_id
        GROUP BY s.sensor_type, s.unit ORDER BY s.sensor_type
    """)
    if not df.empty:
        parts.append("SENSOR SUMMARY:\n" + df.to_string(index=False))

    # Building summary
    df2 = run_pg_query("""
        SELECT b.name AS building, b.location, b.floors,
               COUNT(DISTINCT s.sensor_id) AS sensors,
               COUNT(r.reading_id) AS readings
        FROM buildings b
        JOIN sensors s ON b.building_id = s.building_id
        JOIN readings r ON s.sensor_id = r.sensor_id
        GROUP BY b.name, b.location, b.floors ORDER BY b.name
    """)
    if not df2.empty:
        parts.append("BUILDING SUMMARY:\n" + df2.to_string(index=False))

    # Latest readings per sensor
    df3 = run_pg_query("""
        SELECT DISTINCT ON (s.sensor_id)
            b.name AS building, s.sensor_type, s.install_location,
            r.value, s.unit, r.reading_time
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        JOIN buildings b ON s.building_id = b.building_id
        ORDER BY s.sensor_id, r.reading_time DESC
    """)
    if not df3.empty:
        parts.append("LATEST READINGS (most recent per sensor):\n" + df3.to_string(index=False))

    # Daily averages last 7 days
    df4 = run_pg_query("""
        SELECT DATE(r.reading_time) AS day, s.sensor_type,
               ROUND(AVG(r.value)::numeric, 1) AS avg_val
        FROM readings r JOIN sensors s ON r.sensor_id = s.sensor_id
        WHERE r.reading_time >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(r.reading_time), s.sensor_type
        ORDER BY day, s.sensor_type
    """)
    if not df4.empty:
        parts.append("DAILY AVERAGES (last 7 days):\n" + df4.to_string(index=False))

    # Building + type averages last 7 days
    df5 = run_pg_query("""
        SELECT b.name AS building, s.sensor_type, s.unit,
               ROUND(AVG(r.value)::numeric, 1) AS avg_val,
               ROUND(MIN(r.value)::numeric, 1) AS min_val,
               ROUND(MAX(r.value)::numeric, 1) AS max_val
        FROM readings r
        JOIN sensors s ON r.sensor_id = s.sensor_id
        JOIN buildings b ON s.building_id = b.building_id
        WHERE r.reading_time >= NOW() - INTERVAL '7 days'
        GROUP BY b.name, s.sensor_type, s.unit
        ORDER BY b.name, s.sensor_type
    """)
    if not df5.empty:
        parts.append("PER-BUILDING AVERAGES (last 7 days):\n" + df5.to_string(index=False))

    return "\n\n".join(parts)


SYSTEM_PROMPT = """You are an IoT sensor data analyst assistant. You answer questions about
building sensor data using the LIVE DATA provided below. 

IMPORTANT RULES:
- Answer directly with real numbers from the data. Do NOT write SQL queries.
- Never suggest the user run a query. You have the data -- use it.
- Give clear, conversational answers. Use specific values, buildings, and sensor locations.
- Explain what the data means in practical building management terms.
- If the user explicitly asks for a SQL query, then and only then provide PostgreSQL syntax.

DATABASE SCHEMA (for reference only):
- buildings: building_id, name, location, floors
- sensors: sensor_id, building_id, sensor_type (temperature/humidity/energy), unit, install_location, is_active
- readings: reading_id, sensor_id, reading_time, value

LIVE DATA FROM THE DATABASE:
{data_context}
"""

# ---------------------------------------------------------------------------
# Suggestion chips
# ---------------------------------------------------------------------------
SUGGESTIONS = {
    ":blue[:material/thermostat:] Temperature trends": "What are the temperature trends across buildings over the past week?",
    ":green[:material/bolt:] Energy usage": "Which building uses the most energy and what patterns do you see?",
    ":orange[:material/water_drop:] Humidity analysis": "Are there any concerning humidity readings in the Data Center server rooms?",
    ":red[:material/query_stats:] Write a query": "Write a SQL query to find the top 5 highest temperature readings with their building and location.",
}

# ---------------------------------------------------------------------------
# Page UI
# ---------------------------------------------------------------------------
st.markdown("# :material/smart_toy: AI Agent Search")
st.caption("Ask questions about your IoT sensor data using Snowflake Cortex AI.")

# Initialize chat history
if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

# Show suggestion chips before first message
if not st.session_state.agent_messages:
    selected = st.pills(
        "Try asking:",
        list(SUGGESTIONS.keys()),
        label_visibility="collapsed",
    )
    if selected:
        st.session_state.agent_messages.append(
            {"role": "user", "content": SUGGESTIONS[selected]}
        )
        st.rerun()

# Display chat history
for msg in st.session_state.agent_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Handle new input
if prompt := st.chat_input("Ask about your IoT sensor data..."):
    st.session_state.agent_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        data_context = _build_data_context()
        system = SYSTEM_PROMPT.format(data_context=data_context)
        conversation = system + "\n\n"
        for msg in st.session_state.agent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation += f"{role}: {msg['content']}\n\n"
        conversation += "Assistant:"

        response = st.write_stream(cortex_complete_stream(conversation))

    st.session_state.agent_messages.append(
        {"role": "assistant", "content": response}
    )

# Sidebar info
with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "This AI agent uses **Snowflake Cortex** (Llama 3.1 70B) "
        "to answer questions about the IoT sensor data in your "
        "Postgres instance."
    )
    st.markdown("---")
    st.markdown("**Data available:**")
    st.markdown("- 3 buildings")
    st.markdown("- 15 sensors (temp, humidity, energy)")
    st.markdown("- ~43K readings over 30 days")
    st.markdown("---")
    if st.button(":material/restart_alt: Clear Chat", type="tertiary"):
        st.session_state.agent_messages = []
        st.rerun()
```

### How the "answers first" approach works

The key insight is that instead of asking the LLM to generate SQL (which the user then has to run), we:

1. **Pre-fetch live data** using `_build_data_context()` — this runs 5 summary queries against Postgres and formats the results as plain text
2. **Inject the data into the system prompt** — the LLM receives real numbers alongside the schema
3. **Instruct the LLM to answer directly** — the system prompt explicitly says "Answer directly with real numbers. Do NOT write SQL queries."
4. The LLM responds with conversational answers like "The average temperature in HQ Tower is 72.3°F" instead of `SELECT AVG(value) FROM readings...`

This approach gives users immediate answers without needing to understand SQL, while still allowing them to request SQL queries when explicitly asked.

> **CoCo prompt:**
>
> ```
> Build an AI Agent Search page for my IoT dashboard. I want the AI to
> give me direct answers with real numbers from the database, NOT SQL
> queries. Pre-fetch live data from Postgres (sensor summary, building
> summary, latest readings, daily averages, per-building averages) and
> inject it into the Cortex AI system prompt. Include suggestion chips,
> chat history, streaming responses, and a clear chat button in the sidebar.
> Use llama3.1-70b via the cortex_ai.py module.
> ```

<!-- ------------------------ -->
## Deploy to Streamlit in Snowflake

Now deploy your app to SiS using the Snow CLI.

### Step 9.1: Deploy

From your project directory, run:

```bash
snow streamlit deploy --replace --connection <your-connection-name>
```

The first deployment creates the Streamlit app. Subsequent `--replace` deployments update it in-place.

> **Tip:** The `--connection` flag specifies which Snowflake connection from `~/.snowflake/connections.toml` to use for the deployment. This is the same connection name you use for local development.

### Step 9.2: Verify

After deployment, Snow CLI prints the app URL. Open it in your browser. The app should load with the Dashboard page showing KPIs and charts.

If the app fails to start, check the compute pool:

```sql
DESCRIBE COMPUTE POOL <your-compute-pool>;
```

If the pool is at capacity (`num_services` equals `max_nodes`), increase it:

```sql
ALTER COMPUTE POOL <your-compute-pool> SET MAX_NODES = 3;
```

> **CoCo prompt:**
>
> ```
> Deploy my IOT Streamlit Dashboard to SiS using snow streamlit deploy.
> Use the snowflake.yml manifest I already have. If the compute pool
> is full, increase max_nodes.
> ```

<!-- ------------------------ -->
## Networking

To limit network traffic to the Postgres instance, you might consider using a `HOST_PORT` (public) egress rule on the EAI side and scope the `POSTGRES_INGRESS` rule to Snowflake's egress CIDRs from `SYSTEM$GET_SNOWFLAKE_EGRESS_IP_RANGES()`. However, egress IPs for SPCS are shared across all accounts in the region and are not account-isolated. This approach is **not recommended for production Postgres instances** — use PrivateLink instead.

### PrivateLink

Streamlit in Snowflake (SiS) can connect to a Snowflake Postgres instance using an External Access Integration (EAI) with PrivateLink, keeping all traffic off the public internet. This approach uses `PRIVATE_HOST_PORT` network rules instead of `HOST_PORT`, routing egress traffic from SiS through an AWS PrivateLink tunnel directly to the Postgres instance's VPC endpoint service.

```sql
-- Step 1: Enable PrivateLink on the Postgres instance (takes ~3-10 min)
ALTER POSTGRES INSTANCE "my_instance" ENABLE PRIVATELINK;

-- Monitor until privatelink_service_identifier is non-NULL
DESCRIBE POSTGRES INSTANCE "my_instance";

-- Step 2: Provision outbound PrivateLink endpoint from Snowflake compute
SELECT SYSTEM$PROVISION_PRIVATELINK_ENDPOINT(
  '<privatelink_service_identifier>',   -- e.g. 'com.amazonaws.vpce.us-west-2.vpce-svc-...'
  '<postgres_host>'                      -- e.g. 'abc123.account.us-west-2.aws.postgres.snowflake.app'
);

-- Step 3: Find and authorize the pending connection
SHOW PRIVATELINK CONNECTIONS IN POSTGRES INSTANCE "my_instance";

ALTER POSTGRES INSTANCE "my_instance"
  AUTHORIZE PRIVATELINK CONNECTIONS = ('<connection_id>');

-- Step 4: Create PRIVATE_HOST_PORT network rule
CREATE OR REPLACE NETWORK RULE my_db.my_schema.pg_privatelink_rule
  MODE = EGRESS
  TYPE = PRIVATE_HOST_PORT
  VALUE_LIST = ('<postgres_host>:5432');

-- Step 5: Create secret with Postgres credentials
CREATE OR REPLACE SECRET my_db.my_schema.pg_secret
  TYPE = GENERIC_STRING
  SECRET_STRING = '<password>';

-- Step 6: Create External Access Integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pg_privatelink_eai
  ALLOWED_NETWORK_RULES = (my_db.my_schema.pg_privatelink_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (my_db.my_schema.pg_secret)
  ENABLED = TRUE;

-- Step 7: Create Streamlit app with the EAI
CREATE OR REPLACE STREAMLIT my_db.my_schema.my_app
  ROOT_LOCATION = '@my_db.my_schema.my_stage'
  MAIN_FILE = 'app.py'
  QUERY_WAREHOUSE = 'my_wh'
  EXTERNAL_ACCESS_INTEGRATIONS = (pg_privatelink_eai)
  SECRETS = ('pg_pass' = my_db.my_schema.pg_secret);

-- Optional: Remove public network policy for PrivateLink-only access
ALTER POSTGRES INSTANCE "my_instance" UNSET NETWORK_POLICY;
```

> **CoCo prompt:**
>
> ```
> Set up a PrivateLink connection between my Snowflake Postgres instance
> "<instance_name>" and a Streamlit in Snowflake app. Use the snowflake-postgres
> skill. The steps are:
>
> 1. Enable PrivateLink on the instance with ALTER POSTGRES INSTANCE ENABLE PRIVATELINK
> 2. Wait for privatelink_service_identifier to populate via DESCRIBE
> 3. Use SYSTEM$PROVISION_PRIVATELINK_ENDPOINT with the service identifier and
>    the PG host to create an outbound endpoint
> 4. Authorize the pending connection with ALTER POSTGRES INSTANCE AUTHORIZE
>    PRIVATELINK CONNECTIONS
> 5. Create a secret for the Postgres connection
> 6. Create a PRIVATE_HOST_PORT (not HOST_PORT) egress network rule for the PG
>    host on port 5432
> 7. Create an External Access Integration with the rule and secret
> 8. Create or update the Streamlit app with the EAI attached
> 9. (Optional) Remove any existing POSTGRES_INGRESS network policies so only PrivateLink
>    can connect
> ```



<!-- ------------------------ -->
## Conclusion and Resources

### What You Built

In this quickstart, you built a complete IoT sensor monitoring application:

1. A **Snowflake Postgres instance** with a smart-building sensor schema and 30 days of realistic generated data
2. A **multi-page Streamlit in Snowflake dashboard** with KPI metrics, interactive Altair charts, and building summary tables
3. A **Charts on Demand** page with interactive filters, heatmaps, distribution histograms, and a **natural language chart generator** powered by Cortex AI
4. An **AI Agent Search** chatbot using Snowflake Cortex AI that answers questions about your sensor data in plain English using real numbers — not SQL queries
5. A **Snow CLI deployment** using `snowflake.yml` with container runtime, EAI, and secrets management

### What You Learned

- How to create and configure Snowflake Postgres instances with network policies
- How to generate realistic time-series data with PostgreSQL's `generate_series()` function
- How to build a multi-page Streamlit in Snowflake app with `st.navigation` and container runtime
- How to connect to Postgres from container runtime using `psycopg2` and `.streamlit/secrets.toml` as a deployment artifact
- How to call Snowflake Cortex AI from both SiS and local development using dual-mode detection
- How to build a natural language chart generator (NL to SQL to chart) with JSON spec output
- How to build an AI chatbot that gives direct answers with real data by injecting live data context into the prompt
- How to deploy using `snow streamlit deploy` with `snowflake.yml`
- How to troubleshoot common container runtime issues (`_snowflake` module, secrets, compute pool capacity)

### Full CoCo Prompt (All-in-One)

If you prefer to give CoCo the entire app spec as a single prompt, here it is. This combines all the individual prompts above into one request:

```
I want to build a complete IoT sensor monitoring app using Snowflake Postgres,
Streamlit in Snowflake (container runtime), and Snowflake Cortex AI.

INFRASTRUCTURE:
- Create a network rule (iot_lab_ingress) and network policy (iot_lab_policy)
  allowing all IPv4 ingress (0.0.0.0/0) for lab purposes.
- Create a Snowflake Postgres instance called iot_sensors with STANDARD_M
  compute, 10GB storage, AUTHENTICATION_AUTHORITY = POSTGRES, and the
  iot_lab_policy network policy.
- Create an egress network rule (iot_app_egress) allowing outbound access to
  PyPI (pypi.org, files.pythonhosted.org) and my Postgres host on port 5432.
  Then create an External Access Integration called iot_app_eai.

DATA:
- Connect to the iot_sensors Postgres instance and create tables: buildings
  (building_id, name, location, floors), sensors (sensor_id, building_id,
  sensor_type, unit, install_location, is_active), and readings (reading_id,
  sensor_id, reading_time, value) with indexes on (sensor_id, reading_time)
  and (reading_time).
- Seed 3 buildings: HQ Tower (Downtown Campus, 12 floors), Data Center
  (East Campus, 3 floors), Warehouse Alpha (West Campus, 1 floor).
- Seed 15 sensors across all buildings covering temperature (°F), humidity
  (%RH), and energy (kW).
- Generate 30 days of realistic sensor readings at 15-minute intervals using
  generate_series(). Temperature should follow daily sine-wave cycles (with
  tight ranges for server rooms and cold storage), humidity should be inverse
  of temperature, and energy should peak during business hours (8am-6pm).

APP STRUCTURE:
- Multi-page Streamlit app using st.navigation with top-bar nav.
- Project files: streamlit_app.py (entry point), data.py (shared Postgres
  connection + cached query layer), cortex_ai.py (dual-mode Cortex AI helper),
  pyproject.toml (dependencies), snowflake.yml (SiS deployment manifest),
  .streamlit/secrets.toml (Postgres credentials), and app_pages/ directory
  with home.py, charts.py, and agent.py.

DATA LAYER (data.py):
- Shared Postgres connection using psycopg2 and st.secrets["postgres"].
- @st.cache_resource for the persistent connection, @st.cache_data(ttl=300)
  for query results.
- Retry logic that clears the cached connection and reconnects on failure.
- Query functions: get_buildings, get_sensors, get_sensor_summary,
  get_building_summary, get_daily_avg_by_type, get_hourly_avg (with
  sensor_type and optional building filter), get_readings_by_sensor,
  get_latest_readings, get_readings_for_chart, and run_pg_query.

CORTEX AI LAYER (cortex_ai.py):
- Dual-mode detection: in SiS (detect via /opt/streamlit-runtime) use
  st.connection("snowflake"); locally use snowflake-connector-python with
  connection_name from st.secrets["snowflake_cortex"]["connection_name"].
- cortex_complete(prompt) function calling SNOWFLAKE.CORTEX.COMPLETE with
  llama3.1-70b.
- cortex_complete_stream(prompt) function that yields word chunks for
  streaming UX.

PAGE 1 — DASHBOARD (app_pages/home.py):
- KPI row: total sensors, total readings, sensor types, buildings.
- Sensor overview cards showing avg/min/max for each sensor type.
- Altair line chart of daily averages by sensor type.
- Two-column layout: building summary table and latest readings table.

PAGE 2 — CHARTS ON DEMAND (app_pages/charts.py):
- Filter bar: sensor type, building, time range (7/14/30 days).
- Altair time-series line chart colored by sensor location.
- Summary statistics table per sensor.
- Hourly average heatmap (day × hour).
- Value distribution histogram by building.
- Natural language chart generator: user describes a chart in plain English,
  Cortex AI returns a JSON spec {sql, chart_type, x, y, color, title}, the
  app runs the SQL against Postgres and renders with st.line_chart/bar_chart/
  area_chart/scatter_chart. Include suggestion pills and chart history.

PAGE 3 — AI AGENT SEARCH (app_pages/agent.py):
- "Answers first" approach: pre-fetch live data from Postgres (sensor summary,
  building summary, latest readings, daily averages, per-building averages)
  and inject it into the Cortex AI system prompt.
- The LLM answers directly with real numbers. It does NOT write SQL queries
  unless the user explicitly asks for one.
- Chat UI with suggestion chips, streaming responses via st.write_stream,
  chat history in session state, and a clear chat button in the sidebar.

DEPLOYMENT:
- snowflake.yml for SiS container runtime deployment with the iot_app_eai
  External Access Integration.
- Include .streamlit/secrets.toml in the deployment artifacts so the Postgres
  password is available in the container runtime.
- Deploy with: snow streamlit deploy --replace --connection <connection-name>
```

### Cleanup

To remove the resources created in this guide:

```sql
DROP POSTGRES INSTANCE IF EXISTS iot_sensors;
DROP NETWORK POLICY IF EXISTS iot_lab_policy;
DROP NETWORK RULE IF EXISTS iot_lab_ingress;
DROP EXTERNAL ACCESS INTEGRATION IF EXISTS iot_app_eai;
DROP NETWORK RULE IF EXISTS iot_app_egress;
-- Drop the Streamlit app:
DROP STREAMLIT IF EXISTS iot_lab.sensors.iot_streamlit_dashboard;
```

### Related Resources

- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/LIMITEDACCESS/postgres-overview)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Snow CLI Installation](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation)
- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)

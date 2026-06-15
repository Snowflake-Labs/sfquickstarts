id: getting-started-with-cortex-agents-api-and-streamlit-on-container-runtime
categories: snowflake-site:taxonomy/solution-center/certification/guide, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/ai
language: en
summary: Deploy a Streamlit app on the Container Runtime that calls the Cortex Agents API (agent:run) using the Snowflake Documentation Cortex Knowledge Extension (CKE), with multi-turn chat via the Threads API.
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
authors: Rishu Saxena


# Call the Cortex Agents API from Streamlit on the Container Runtime
<!-- ------------------------ -->


## Overview

In this guide, you will build a Streamlit in Snowflake (SiS) app that runs on the **Container Runtime** and calls the **Cortex Agents API** from inside the app.

Why Container Runtime?
- Streamlit in Snowflake supports **two runtime environments**: *warehouse runtime* and *container runtime*. The container runtime serves your app as a **long-running, shared server** backed by a **compute pool** node (and uses a separate warehouse only for SQL queries). This makes it a great fit for interactive apps and caching. 
- On the **warehouse runtime**, Streamlit code executes in a stored-procedure-style environment where you can often rely on Snowflake-specific helpers like the **`_snowflake` module** for interacting with Snowflake services.
On the **container runtime**, your app runs as a long-lived service **outside** that stored procedure environment, which means **`_snowflake` isn’t available**—but you gain a more standard, app-server-like model. For calling Snowflake REST endpoints (including **Cortex / Agents APIs**), the recommended pattern is to **use the container session’s OAuth token** (read from **`/snowflake/session/token`**) and make direct HTTPS requests with a normal HTTP client like **`requests`**.


### Streamlit Runtime Environments: Warehouse vs Container

| Supported feature | Warehouse runtime | Container runtime |
|------------------|------------------|------------------|
| **Compute** | Virtual warehouse for app code and internal queries. | Compute pool node for app code. Virtual warehouse for internal queries. |
| **Base image** | Linux in a Python stored procedure. | Linux in a Snowpark container. |
| **Python versions** | 3.9, 3.10, 3.11 | 3.11 |
| **Streamlit versions** | 1.22+ (limited selection) | 1.49+ (any version, including streamlit-nightly) |
| **Dependencies** | Packages from the Snowflake Conda channel via `environment.yml`. Pin versions with `=`. Use version ranges with `*` wildcard. | Packages from an external index (e.g., PyPI) via `pyproject.toml` or `requirements.txt`. Pin versions with `==`. Use version ranges with `<`, `<=`, `>=`, `>`, `*`, and comma-separated lists. |
| **Entrypoint location** | Root of your source directory. | Root or subdirectory within your source directory. |
| **Streamlit server** | Temporary per-viewer instance. Does not share disk, compute, or memory between sessions. Does not support caching between sessions. | Persistent shared instance for all viewers. Shares disk, compute, and memory between sessions. Fully supports Streamlit caching. |
| **Startup times** | Slower per viewer (on-demand app creation). | Faster per viewer, but slower deployment (container startup). |
| **Access** | Requires ownership to edit. Uses owner’s rights for queries (similar limits to owner’s rights stored procedures). | Same as warehouse runtime. Owner’s rights for queries with option to use caller’s rights on some or all queries. |


### What you will learn
How to deploy a Streamlit app to the **Container Runtime** and call `agent:run` + `threads` (multi-turn chat)


### What you will build
A Streamlit chat app that:
- streams responses from your agent (Server-Sent Events)
- keeps context across turns via the **Threads API**
- answers questions by retrieving context from the **Snowflake Documentation CKE (Cortex Knowledge Extensions)**


## Prerequisites

- A Snowflake account with:
  - Access to **Snowsight**
  - Access to **Streamlit in Snowflake**
  - Access to **Snowpark Container Services / compute pools**
  - Access to **Cortex Agents** and **Cortex Knowledge Extensions (CKE)**
- Ability to use **ACCOUNTADMIN**

> In Snowsight, use **Projects » Workspaces** for the SQL in this guide.

## Step-by-Step guide

### Step 1: Create the project objects (SQL)

Open **Snowsight → Projects → Workspaces**, create a new **SQL File**, then run the following as **ACCOUNTADMIN**.

> Tip: Keep everything in a single database/schema so the Streamlit app and the agent share the same context.

```sql
-- Use Workspaces (Projects » Workspaces) to run this SQL.
USE ROLE ACCOUNTADMIN;

-- Pick names you’ll reuse throughout this guide.
CREATE OR REPLACE DATABASE AGENTS_STREAMLIT_DEMO;
CREATE OR REPLACE SCHEMA AGENTS_STREAMLIT_DEMO.APP;

USE DATABASE AGENTS_STREAMLIT_DEMO;
USE SCHEMA APP;

-- A small warehouse for queries executed by the app (container runtime uses a warehouse only for SQL queries).
CREATE OR REPLACE WAREHOUSE STREAMLIT_QUERY_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- A compute pool to host the Streamlit container runtime.
-- Increase MAX_NODES if you expect to run multiple container-runtime apps concurrently.
CREATE COMPUTE POOL IF NOT EXISTS STREAMLIT_COMPUTE_POOL
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_XS;

-- Stage for app files (used by CREATE STREAMLIT ... FROM '@stage/path').
CREATE OR REPLACE STAGE APP_STAGE;
```


### Step 2: Install the Snowflake Documentation CKE (Marketplace)

You’ll use the same external knowledge source as the “Getting Started with Snowflake Intelligence and CKE” guide:
**Snowflake Documentation** published as a **Cortex Knowledge Extension (CKE)** on Snowflake Marketplace.

1. In Snowsight, open **Data Products → Marketplace**
2. Search for **Snowflake Documentation** (CKE)
3. Select the listing and click **Get**
4. Click on **Get** on the opened dialog box

> A shared database **SNOWFLAKE_DOCUMENTATION** is created
> A shared search service **CKE_SNOWFLAKE_DOCS_SERVICE** is created under schema **SHARED**

After installation, confirm the CKE’s Cortex Search Service name:

```sql
USE ROLE ACCOUNTADMIN;

-- The listing creates a database; schemas/services depend on the listing.
SHOW CORTEX SEARCH SERVICES IN DATABASE SNOWFLAKE_DOCUMENTATION;
```


### Step 3: Create the Cortex Agent (SQL)

This guide creates an agent named **SNOWFLAKE_DOCUMENTATION** in the same schema as the Streamlit app:
`AGENTS_STREAMLIT_DEMO.APP`.

This agent uses **only one tool**:
- `cortex_search` pointing at the Snowflake Documentation CKE search service you found in the previous step.


```sql
USE ROLE ACCOUNTADMIN;

USE DATABASE AGENTS_STREAMLIT_DEMO;
USE SCHEMA APP;

CREATE OR REPLACE AGENT SNOWFLAKE_DOCUMENTATION
  COMMENT = 'Answers questions using the Snowflake Documentation CKE'
  PROFILE = '{"display_name":"Snowflake Documentation","avatar":"snowflake.png","color":"blue"}'
  FROM SPECIFICATION
$$
instructions:
  system: |
    You are a Snowflake documentation assistant.
    Use ONLY the Snowflake Documentation search tool to answer the user.
    If the documentation does not contain the answer, say you do not know.
    When you use retrieved content, include citations/attribution if available.

tools:
  - tool_spec:
      type: "cortex_search"
      name: "snowflake_docs_search"
      description: "Search Snowflake Documentation (CKE) to ground answers."

tool_resources:
  snowflake_docs_search:
    -- Fully-qualified Cortex Search Service name from the CKE database:
    -- Example format: SNOWFLAKE_DOCUMENTATION_CKE.SHARED.<SERVICE_NAME>
    name: "SNOWFLAKE_DOCUMENTATION.SHARED.CKE_SNOWFLAKE_DOCS_SERVICE"
    max_results: "5"
$$;
```

(Optional) sanity check:

```sql
SHOW AGENTS IN SCHEMA AGENTS_STREAMLIT_DEMO.APP;
```

> This guide uses ACCOUNTADMIN and does not add custom roles or grants.  


### Step 4: Download the apps files

Download the following files from [**assets**](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/getting-started-with-cortex-agents-api-and-streamlit-on-container-runtime/assets) folder:
1. `requirements.txt`
2. `streamlit_app.py`

#### `streamlit_app.py`

> This is the streamlit app that calls:
> - Threads API: `POST /api/v2/cortex/threads`
> - Agent Run API: `POST /api/v2/databases/<db>/schemas/<schema>/agents/SNOWFLAKE_DOCUMENTATION:run`
>
> The app reads the container session token from `/snowflake/session/token`.



### Step 5: Deploy the Streamlit app (Container Runtime)

You can deploy using **staged files** (SQL + Snowsight upload) or using **Git integration**. This guide uses staged files.

#### 5A) Upload files to the stage (Snowsight UI)

1. In Snowsight, go to **Data → Databases → AGENTS_STREAMLIT_DEMO → APP → Stages → APP_STAGE**
2. Upload:
   - `streamlit_app.py`
   - `requirements.txt`
   
   from the cloned git repo folder path.

Your stage should look like:
- `@AGENTS_STREAMLIT_DEMO.APP.APP_STAGE/streamlit_app.py`
- `@AGENTS_STREAMLIT_DEMO.APP.APP_STAGE/requirements.txt`

#### 5B) Create External Access Integration and Streamlit object (SQL)

In Snowsight, go to **Workspaces** and run:

```sql
USE ROLE ACCOUNTADMIN;

USE DATABASE AGENTS_STREAMLIT_DEMO;
USE SCHEMA APP;

-- Setup External Access Integration (EAI) to enable custom installation of packages in the streamlit app
-- 1) Allow egress to the PyPI domains Streamlit dependency installs need
CREATE OR REPLACE NETWORK RULE pypi_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org', 'files.pythonhosted.org');

-- 2) Create an External Access Integration using that rule
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
  ALLOWED_NETWORK_RULES = (pypi_network_rule)
  ENABLED = TRUE;

-- Create Streamlit app using the files and EAI
CREATE OR REPLACE STREAMLIT AGENTS_DOCS_CHAT_APP
  FROM '@APP_STAGE'
  MAIN_FILE = 'streamlit_app.py'
  RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
  COMPUTE_POOL = STREAMLIT_COMPUTE_POOL
  EXTERNAL_ACCESS_INTEGRATIONS = (pypi_access_integration)
  QUERY_WAREHOUSE = STREAMLIT_QUERY_WH;
```

Then open the app:
- Snowsight → **Projects → Streamlit** → `AGENTS_DOCS_CHAT_APP`
 
> The container runtime requires both `RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'` and a `COMPUTE_POOL`.


### Step 6: Try it out

In the Streamlit UI, ask questions like:

- “How do Streamlit container runtimes differ from warehouse runtimes?”
- “What is `RUNTIME_NAME = SYSTEM$ST_CONTAINER_RUNTIME_PY3_11` used for?”
- “How do I select a compute pool for Streamlit container runtime?”

You should see:
- Agents API response text (SSE)
- a multi-turn conversation that remembers prior messages via `thread_id`


## Troubleshooting

- **Agent not found**
  - Ensure you created the agent in the **same database and schema** as the Streamlit app (`AGENTS_STREAMLIT_DEMO.APP`), because the app uses `CURRENT_DATABASE()` and `CURRENT_SCHEMA()` to build the agent run URL.

- **401 / auth errors when calling the API**
  - Confirm the Streamlit app is running on **Container Runtime** and can read `/snowflake/session/token`.

- **No results from the CKE tool**
  - Re-run:
    ```sql
    SHOW CORTEX SEARCH SERVICES IN DATABASE SNOWFLAKE_DOCUMENTATION_CKE;
    ```
    and confirm the service name in the agent’s `tool_resources` is correct.

- **App is slow / runs out of resources**
  - Increase the compute pool node size (INSTANCE_FAMILY) or use a larger query warehouse for heavy SQL queries if you have added *Cortex Analyst* tool to your agent.


## Cleanup

```sql
USE ROLE ACCOUNTADMIN;

DROP STREAMLIT IF EXISTS AGENTS_STREAMLIT_DEMO.APP.AGENTS_DOCS_CHAT_APP;

DROP AGENT IF EXISTS AGENTS_STREAMLIT_DEMO.APP.SNOWFLAKE_DOCUMENTATION;

DROP STAGE IF EXISTS AGENTS_STREAMLIT_DEMO.APP.APP_STAGE;

DROP COMPUTE POOL IF EXISTS STREAMLIT_COMPUTE_POOL;

DROP WAREHOUSE IF EXISTS STREAMLIT_QUERY_WH;

DROP SCHEMA IF EXISTS AGENTS_STREAMLIT_DEMO.APP;
DROP DATABASE IF EXISTS AGENTS_STREAMLIT_DEMO;

-- Optional: also drop the Marketplace-installed database if you no longer need it.
-- DROP DATABASE IF EXISTS SNOWFLAKE_DOCUMENTATION_CKE;
```


## Conclusion and Resources

Congratulations! You’ve successfully deployed a Streamlit in Snowflake app on the **Container Runtime** and used it to call the **Cortex Agents API** to power a **multi-turn** chat experience grounded in the Snowflake Documentation **Cortex Knowledge Extension**.

### What You Learned

You learned how to run Streamlit on a compute pool and securely authenticate to Snowflake REST endpoints using the container session token—then connect it all together to create an agent-driven application that can reason over trusted documentation and respond from a single, interactive chat interface.

### Related Resources:
- [CKE in Snowflake Marketplace](https://app.snowflake.com/marketplace/data-products?sortBy=popular&categorySecondary=%5B%2226%22%5D)
- Runtime environments for Streamlit apps: https://docs.snowflake.com/developer-guide/streamlit/app-development/runtime-environments
- Manage secrets/configuration for Streamlit (container runtime + Cortex API calls): https://docs.snowflake.com/developer-guide/streamlit/app-development/secrets-and-configuration
- CREATE AGENT (agent specification + cortex_search tool config): https://docs.snowflake.com/sql-reference/sql/create-agent
- Cortex Knowledge Extensions overview: https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-knowledge-extensions/cke-overview

# dbt Labs | Fivetran | Snowflake Hands-On Lab

Welcome to the dbt Labs Hands-On Lab! In this workshop, you'll move data from a source database into Snowflake using Fivetran, transform it into trusted, production-ready data products using dbt, and see how modern data capabilities like the Fusion engine and State-Aware Orchestration make that process faster, smarter, and more efficient.

This is a **full-stack, end-to-end walkthrough of how modern data teams go from raw data to AI-powered outcomes** — no prior experience with any of these tools is required.

---

**⚠️ IMPORTANT:**
Before starting the lab, register for your Fivetran account at:
**https://fivetran-lab.web.app/**

---

## Prerequisites

- Web browser
- Valid email address (Snowflake, Fivetran, or dbt Labs)

## Getting Started

1. Register at https://fivetran-lab.web.app/
2. Check your email for your Fivetran invitation from `notifications@fivetran.com`
3. Accept the invitation and set your password
4. Get lab credentials: https://fivetran-lab.web.app/lab-credentials.html (passcode provided by instructor)
5. Log in to Fivetran and get ready to build!

---

# Part 1: Introduction to Fivetran

## What is Fivetran?

**Fivetran** is a data movement platform that automatically syncs data from source systems — databases, applications, cloud services — into your data warehouse. Instead of writing and maintaining custom ingestion scripts, Fivetran handles the pipeline for you: it connects to the source, extracts the data, and loads it into Snowflake on a schedule. Once set up, it runs automatically without any manual intervention.

Think of Fivetran as the on-ramp to your data platform — it gets raw data flowing into Snowflake so that tools like dbt can transform it into something useful.

---

## Step 1: Create Fivetran Connector to Snowflake

### 1.1 Configure PostgreSQL Source Connector

1. In Fivetran, click **+ Connector**
2. Search for and select **Google Cloud PostgreSQL**
3. Configure the connector:
   - **Destination**: `Snowflake_Summit_HOL_27_dbt` (pre-configured)
   - **Snowflake Destination Virtual Warehouse**: Keep default
   - **Destination schema prefix**: `yourfirstname_yourlastname` (lowercase, underscores only)
   - **Destination schema names**: Fivetran naming
   - **Host**: Use credentials from lab credentials page based on the first letter of `yourlastname`
   - **Port**: `5432`
   - **User**: Use credentials from lab credentials page
   - **Password**: Use credentials from lab credentials page
   - **Database**: `industry` (case-sensitive)
   - **Authentication Method**: Connect with a username and password
   - **Connection method**: Connect directly
   - **Update Method**: Query-based
4. Click **Save & Test**

### 1.2 Select Data to Sync

1. The `higher_education` schema and `hed_records` table will be pre-selected
2. Click **Continue**

### 1.3 Handle Schema Changes

1. Select **Allow all** (default)
2. Click **Continue**

### 1.4 Start Initial Sync

1. On the connector Status page, click **Start Initial Sync**

### 1.5 Verify Data in Snowflake (While Sync Runs)

1. Navigate to Snowflake Lab Account using credentials from lab credentials page
2. Log in with provided credentials
3. In Snowflake UI, click **Catalog** in the left navigation
4. Click on **RAW** database
5. Find your schema (e.g., `yourfirstname_yourlastname_higher_education`)
6. Click **Tables**
7. Click on **HED\_RECORDS** table
8. Click **Data Preview** tab to view the Fivetran synced data and scroll all the way to the right to see `_fivetran_synced`

> **✅ Expected:** You should see rows of student records loaded by Fivetran. The `_fivetran_synced` column shows the timestamp of the last sync — Fivetran automatically adds this to every table it manages.

---

# Part 2: Introduction to dbt

## What is dbt?

**dbt** (data build tool) is a transformation framework that lets data teams write modular SQL models, test them, and document them — all in one place. dbt runs *inside* your data warehouse (Snowflake), so no data ever leaves the platform. Think of it as version-controlled, tested, production-grade SQL.

Where Fivetran handles *moving* raw data into Snowflake, dbt handles *transforming* that raw data into clean, trusted data products that analysts, dashboards, and AI tools can rely on.

**What makes dbt different from just writing SQL?**
- Every model is a reusable, testable building block
- Data quality tests run automatically alongside your transformations
- Lineage is tracked from source to output — you always know where data came from
- Documentation is generated automatically and stays in sync with the code
- Changes go through version control (Git), just like application software

---

## Step 2: Transform Data with dbt

### 2.1 Register for dbt platform Workshop Account

1. Navigate to the dbt Workshop registration page: https://workshops.us1.dbt.com/workshop/
2. Fill in the registration form:
   - **First Name**: Your first name
   - **Last Name**: Your last name
   - **Company Email**: Your email address
   - **Workshop Selection**: Select **Snowflake Summit Hands-On Lab** from the dropdown
   - **Workshop Passcode**: Enter the passcode provided by your instructor
3. Click **Complete Registration** and wait for the success pop-up. It will include generated dbt Platform credentials for the workshop.
4. Record these credentials — you may need them to log back in during the lab.

### 2.2 Access dbt platform

1. In dbt platform, locate the **Project dropdown** on the left-hand side
2. Select **Snowflake Summit (Higher Education)** from the dropdown
3. Click **Studio** to load dbt Platform

### 2.3 Build Faster with Fusion

> **What is Fusion?** Fusion is dbt's next-generation execution engine, built directly into dbt platform Studio. Unlike a traditional SQL editor, Fusion understands the structure of your entire dbt project as you type — it knows which models exist, which columns they contain, and how they relate to each other. This means it can surface errors, preview intermediate results, and provide column-level context *before* you ever run a job.

This is a great place to get oriented in the dbt platform Studio IDE before we start building. You'll explore the project structure and see how Fusion makes working in dbt faster and safer than writing SQL in a traditional editor.

#### 2.3.1 Explore IntelliSense

The `vw_hed_data_quality` model is a great place to see Fusion's IntelliSense in action. It calculates a composite data quality score for student records by combining multiple upstream checks — making it easy to trace exactly where each component of the score comes from.

1. In the **Project Navigator**, open `vw_hed_data_quality.sql`
2. In the editor, hover over any column reference used in the composite score calculation — Fusion displays the column's data type and description inline, pulled directly from the upstream model that defines it
3. Click on a `ref()` call referencing an upstream model — Fusion lets you trace lineage directly, showing you which model and column the data flows from
4. Begin typing a column name in the editor — notice how Fusion suggests only valid column names from the models referenced in this file, preventing typos before they become errors

> **Note:** This is IntelliSense — the same kind of intelligent code completion used in modern software development tools, now applied to your dbt SQL. Instead of guessing column names or jumping between files, Fusion surfaces the full context of your data model as you write.

#### 2.3.2 See Real-Time Error Detection

1. In `vw_hed_data_quality.sql`, find any line that references an upstream model using `ref()`
2. Temporarily change the model name to something invalid — add a typo, such as changing `ref('stg_hed_records')` to `ref('stg_hed_recordz')`
3. Observe how Fusion immediately highlights the invalid reference with an error indicator — **without running the model**
4. Revert the change back to the correct model name

> **Note:** In a traditional SQL workflow, this error would only surface after a full job run — potentially minutes later, and after consuming warehouse compute. Fusion catches it instantly at the editor level.

#### 2.3.3 Preview a CTE

1. Still in `vw_hed_data_quality.sql`, locate one of the CTEs (the `WITH` blocks at the top of the file)
2. Click on the CTE name to place your cursor inside it
3. Click the **Preview** button in the editor toolbar
4. Review the intermediate output of that CTE — you're seeing the partial results of one component of the composite data quality score, without running the full model

> **✅ Expected:** A preview table appears showing the rows produced by that CTE. This is especially useful in a model like `vw_hed_data_quality` where multiple upstream checks feed into a single composite score — you can validate each component independently before running the full build.

### 2.4 Generate Tests with dbt Co-Pilot

Co-Pilot is dbt's AI assistant, powered by a dbt-native agent that understands your project structure, your models, and how dbt works. You'll use it here to automatically generate and run data quality tests for the `vw_hed_data_quality` model.

1. In the **Project Navigator**, locate and open `vw_hed_data_quality.sql`
2. Open the **Co-Pilot** panel in dbt Platform Studio
3. In the Co-Pilot prompt, type a request such as:
   > *"Generate data quality tests for the vw_hed_data_quality model"*
4. Review the tests Co-Pilot proposes — it will suggest appropriate checks (e.g., `not_null`, `unique`, `accepted_values`) based on the columns and their types in the model
5. Ask Co-Pilot to write the tests directly to a file by following up with:
   > *"Write these tests to the schema YAML file for this model"*
6. Co-Pilot will create or update the relevant `.yml` file with the test definitions — review the file in the **Project Navigator** to confirm the tests were added correctly
7. Ask Co-Pilot to run the new tests:
   > *"Run the tests for this model"*

> **Note:** Notice that Co-Pilot runs `dbt test` rather than `dbt build`. The dbt agent powering Co-Pilot understands the difference — `dbt build` would rebuild the model *and* run tests, consuming unnecessary warehouse compute. Since the model already exists and we only want to validate it, `dbt test` is the correct and more efficient command. Co-Pilot makes this call automatically.

> **✅ Expected:** All generated tests pass, confirming the data in `vw_hed_data_quality` meets the quality rules Co-Pilot defined. Any failures would surface specific rows or columns that don't meet the expected constraints.

### 2.5 Save and Commit Changes

1. Locate the **Git Integration button** in the top-left corner of dbt platform
2. Click the **Git Integration button** to commit and sync your changes
3. Follow the prompts to commit your work
4. Click to open a pull request in GitHub
5. Review the PR (no need to merge — lab changes won't be merged into the main branch)

**Note:** This step demonstrates the git workflow built into dbt Platform. In a real production environment, all model changes go through a PR review process before being promoted — the same engineering discipline used in software development.

### 2.6 Explore dbt Packages Configuration

1. In the **Project Navigator** (left sidebar), locate and open the `packages.yml` file
2. Review the file contents and note how the `snowflake_semantic_view` package is defined
   - This package enables dbt to create Snowflake Semantic Views
3. For more on this package, see: https://hub.getdbt.com/Snowflake-Labs/dbt_semantic_view/latest/

**Understanding Package Management:**

- When adding new packages, run `dbt deps` to install dependencies
- This command creates or updates `package-lock.yml`, which records specific package versions
- The lock file prevents compatibility issues when collaborating with other users

### 2.7 Examine and Run dbt Models

This project showcases two complementary approaches to defining semantic meaning on top of your data — both supported natively by dbt.

**Approach 1: Snowflake Semantic Views**
The `sv_hed_at_risk_students.sql` model creates a Snowflake Semantic View — a native Snowflake object that adds a business-friendly layer directly inside Snowflake. It labels columns, defines metrics (called "facts"), and categorizes attributes (called "dimensions"). This is what powers Cortex AI's ability to understand and query your student retention data using natural language later in the lab.

**Approach 2: dbt Semantic Layer**
dbt also has its own semantic and metric layer, defined using YAML-based metric files within the project. Open `sem_vw_hed_engagement_analytics.yml` in the **Project Navigator** to see an example — this file defines structured metrics on top of the HED engagement data (things like engagement rates, login activity, and risk distributions) using dbt's MetricFlow framework.

The key difference: Snowflake Semantic Views live inside Snowflake and are consumed by Snowflake-native tools like Cortex Analyst. dbt Semantic Layer metrics are defined and governed within dbt itself, making them accessible to any downstream tool that connects via the **dbt MCP server** — including AI agents, BI tools, and coding assistants like Claude. When a tool connects to the dbt MCP server, it can query these metrics directly using natural language or structured requests, with dbt handling the SQL generation and ensuring metric definitions stay consistent across every consumer — including Snowflake Cortex Agents, other AI agents, BI tools, and coding assistants like Claude.

1. In the **Project Navigator**, expand the `models` folder
2. Expand the `HED` subfolder, then expand the `semantic_models` subfolder inside it
3. Open `sv_hed_at_risk_students.sql` and review the Snowflake Semantic View definition
4. Open `sem_vw_hed_engagement_analytics.yml` and review the dbt metric definitions alongside it — note how the two approaches complement each other within the same project
5. Select `sv_hed_at_risk_students.sql` and click the **Run +model (Upstream)** button to build the semantic view and its upstream dependencies in your local Dev schema
6. Wait for the model to complete successfully

> **✅ Expected:** You should see a green success status for `sv_hed_at_risk_students` and its upstream model `vw_hed_retention_risk_analysis`.

### 2.8 Run a Production dbt Job

1. In the left-hand menu, navigate to **Orchestration > Jobs**
2. Locate and select the preconfigured **Prod Job** (running in the **Prod Environment**)
3. Click **Settings** in the top right, then click **Edit**
4. Confirm the execution command is set to `dbt build`
5. Ensure **Generate docs on run** is checked
6. Click **Save** in the top right to save your changes
7. Navigate back to the **Job Overview** page using the top navigation
8. Click **Run Now** to execute the job
9. Wait for the job to complete successfully

> **✅ Expected:** All HED models build successfully, including `vw_hed_retention_risk_analysis` and `sv_hed_at_risk_students`. You'll see green checkmarks next to each model in the run logs.

---

### 2.9 State-Aware Orchestration

> **What is State-Aware Orchestration?** By default, every time a dbt job runs it rebuilds *every* model from scratch — even if the underlying source data hasn't changed. State-Aware Orchestration (SAO) changes this behavior. dbt compares the current state of your source data against the last known state, and skips rebuilding any model whose inputs haven't changed. This means you only pay for warehouse compute on models that actually need to run — and your jobs complete faster.

#### 2.9.1 Enable Fusion Cost Optimization Features

1. Navigate to **Orchestration > Jobs** and open the **Prod Job**
2. Click **Settings**, then **Edit**
3. Locate the **Enable Fusion cost optimization features** toggle and turn it **ON**
4. Confirm both sub-options are enabled:
   - ✅ **State-aware orchestration** — dbt will skip models whose inputs haven't changed since the last run
   - ✅ **Efficient testing** — dbt will skip tests on models that were skipped, avoiding unnecessary test compute
5. Under **Advanced Settings**, locate the **Compare Changes** setting and set it to **Environment**
6. In the environment dropdown that appears, select your **Production** environment (the environment you used in Step 2.8) — this tells dbt to compare the current run against the last successful production run when determining what to skip
7. Click **Save**

#### 2.9.2 What Happens on Run #1

This is the first execution with Fusion cost optimization enabled. Because there is no previous production run state to compare against yet, dbt has no baseline — it treats everything as new and builds all models from scratch.

**What you'll see:** All models execute with `CREATE` or `OK` status in the run logs. This is your **baseline run** — dbt records the current state of your data so it can make smart skip decisions on every subsequent run.

#### 2.9.3 Execute Run #1

1. Navigate to the **Prod Job Overview** page
2. Click **Run Now**
3. Watch the run logs as the job executes — all models should build
4. Note the total run time displayed when the job completes

> **✅ Expected:** All models execute successfully. Note the run time — you'll compare this to Run #2.

#### 2.9.4 What Happens on Run #2

No new data has been loaded since Run #1 — the Fivetran sync has not run again, so `hed_records` is unchanged.

When you trigger the job a second time, dbt compares the current state of the source data against the baseline recorded in Run #1. Because nothing has changed, dbt determines there is nothing new to build and **skips every downstream model**. With efficient testing also enabled, tests on skipped models are skipped too — no unnecessary warehouse compute is used at all.

**What you'll see:** All models show `SKIP` status in the run logs. The job completes in seconds rather than minutes.

#### 2.9.5 Execute Run #2

1. Click **Run Now** again on the **Prod Job Overview** page
2. Watch the run logs carefully — compare what you see to Run #1

> **✅ Expected:** All models are skipped. The total run time should be a fraction of Run #1's time, and zero Snowflake compute is consumed on model execution or testing.

#### 2.9.6 Reflect

Take a moment to consider what just happened:

- **Run #1** built everything from scratch — this is the full cost of a traditional dbt job on every run, regardless of whether data changed
- **Run #2** completed in seconds with no compute consumed on transformations or tests — this is the value of Fusion cost optimization

In a real production environment where dbt jobs run on a schedule (hourly, daily), this means you're only paying for warehouse compute when data has actually changed. For large projects with hundreds of models, that's a significant reduction in both cost and job runtime.

---

# Part 3: Agentic Data Pipeline with Cortex Code

## What is Cortex Code?

**Cortex Code** is Snowflake's AI-powered coding assistant, available as an extension for VS Code, Cursor, and other compatible local IDEs. It connects to your Snowflake environment and a set of MCP servers, giving it live access to tools — Fivetran, dbt, Snowflake — that it can call on your behalf as part of a guided agentic workflow.

## What is an Agent Skill?

An **agent skill** is a pre-built, conversational workflow that runs end-to-end inside Cortex Code. When you invoke a skill, the agent takes over: it calls the right tools in the right order, shares context along the way, and prompts you only when a decision or confirmation is needed. You stay in your IDE the entire time — no browser tabs, no separate UIs.

In this section, you'll run the same end-to-end data pipeline you built manually in Parts 1 and 2 — but this time the agent does the work. The pipeline follows Fivetran & dbt's full **Open Data Infrastructure** story:

**Source → Move & Manage → Transform → Agent → Activate**

---

## Step 3: Run the Agentic Pipeline

### 3.1 Environment Setup

> **Note:** Part 3 runs entirely in a local IDE — VS Code, Cursor, or any equivalent editor with the Cortex Code extension installed. You'll need a working internet connection and the lab credentials provided by your instructor.

> **⚠️ Unable to run locally?** If your laptop has restrictions that prevent you from completing the local setup, visit the **Fivetran booth** where pre-configured workstations are available to run the demo.

#### 3.1.1 Clone the Lab Repository

Open a terminal and clone the lab repo:

```bash
git clone https://github.com/kellykohlleffel/snowflake-summit-2026
cd snowflake-summit-2026
```

#### 3.1.2 Run the Setup Script

The setup script checks all prerequisites, builds the required extensions and MCP servers, installs the HOL skill, and creates credential config files. It is safe to re-run if anything fails — it picks up where it left off.

```bash
./setup.sh
```

The script will check for and guide you through any missing prerequisites:

- Git
- Node.js v18+
- Python 3.12+
- VS Code `code` command (or equivalent IDE CLI)
- Cortex Code CLI
- GitHub CLI (`gh`)

If any prerequisite is missing, the script will print clear instructions and exit. Fix the issue and re-run `./setup.sh`.

> **✅ Expected:** The script completes with a "Setup Complete" summary showing all components installed and both credential files created.

#### 3.1.3 Fill In Your Credentials

The setup script creates three credential files with placeholder values. Open each file and fill in the values from your lab credentials page.

**File 1: `~/.fivetran-code/config.json`**

```json
{
  "fivetranApiKey": "YOUR_FIVETRAN_API_KEY",
  "fivetranApiSecret": "YOUR_FIVETRAN_API_SECRET",
  "anthropicApiKey": "YOUR_ANTHROPIC_API_KEY",
  "snowflakeAccount": "YOUR_SNOWFLAKE_ACCOUNT",
  "snowflakePatToken": "YOUR_SNOWFLAKE_PAT_TOKEN"
}
```

**File 2: `~/.snowflake/connections.toml`**

```toml
default_connection_name = "summit-hol"

[summit-hol]
account = "YOUR_SNOWFLAKE_ACCOUNT"
user = "YOUR_SNOWFLAKE_USER"
password = "YOUR_SNOWFLAKE_PAT_TOKEN"
warehouse = "HANDS_ON_LAB_WAREHOUSE"
database = "YOUR_SNOWFLAKE_DATABASE"
```

**File 3: `mcp-servers/se-demo/.env`**

Fill in the Snowflake and Fivetran values listed in the file — these allow the SE Demo MCP server to execute dbt and query Snowflake on your behalf.

#### 3.1.4 Reload Your IDE

Once credentials are filled in, reload your IDE to activate the Cortex Code extension with the new configuration.

- **VS Code:** `Cmd+Shift+P → Developer: Reload Window`
- **Cursor or other:** use the equivalent reload command for your editor

---

### 3.2 Launch Cortex Code and Start the Skill

#### 3.2.1 Open Cortex Code

Click the **Snowflake icon** in the activity bar (left sidebar) of your IDE to open the Cortex Code panel.

#### 3.2.2 Verify MCP Servers Are Connected

In the top right of the Cortex Code panel, the extension displays all connected MCP servers. Confirm you see **[N] MCP servers** connected, including:

- **`se-demo`** — handles Snowflake queries, dbt execution, Cortex Agent creation, and activation
- **`fivetran-code`** — handles Fivetran connector management, syncs, and schema configuration

> *(The exact count and list of MCP servers may be updated before the lab — your instructor will confirm what you should see.)*

If either server shows as disconnected, check that your credential files are filled in correctly and reload your IDE.

#### 3.2.3 Invoke the Skill

In the Cortex Code chat input, type:

```
/fivetran-snowflake-hol-sfsummit2026
```

#### 3.2.4 Select an Industry and Follow the Agent

The agent will display the lab roadmap and prompt you to choose an industry. Select whichever industry is most relevant to you and follow the agent's prompts from there — it will guide you through each step of the pipeline.

---

### 3.3 Agent-Guided Pipeline

This portion of the lab is guided by the Cortex agent. The process is outlined below.

**Step 1 — Prerequisites & Readiness Check:** The agent verifies your Snowflake and Fivetran connections, confirms your selected industry and dataset, and collects a schema prefix before proceeding.

**Step 2 — MOVE: Connect the Source:** The agent creates a PostgreSQL connector via the Fivetran API, handling TLS certificate approval, schema discovery, and table selection automatically. If asked to select a Fivetran destination group, choose **`Snowflake_Summit_HOL_27_dbt`**.

**Step 3 — MOVE & MANAGE: Sync to Snowflake:** The agent triggers the sync and shares context about Fivetran's data movement capabilities while the data loads. When prompted, say **"check"** and the agent will verify your data has landed in Snowflake.

**Step 4 — TRANSFORM: Build the dbt Project:** The agent runs `dbt run` and `dbt test` against your Snowflake destination, building the full model stack — staging, mart, and semantic view — and verifying the results.

**Step 5 — AGENT: Create & Deploy the Cortex Agent:** The agent creates a Snowflake Cortex Agent on top of the semantic view, ready to answer natural language questions about your data.

**Step 6 — ASK: Interactive Q&A:** The agent presents a set of sample questions for your chosen industry. Pick from the list or ask your own — this is the fully interactive step of the lab.

**Step 7 — ACTIVATE: Push to Business App:** The agent pushes the top insights from your dataset to a live business app. When prompted, open the activation app link in your browser to see the data appear in real time. The agent will then present a full summary of the end-to-end pipeline: **Move & Manage → Transform → Agent → Activate**.

---

## Need Help?

Ask a lab instructor for assistance.

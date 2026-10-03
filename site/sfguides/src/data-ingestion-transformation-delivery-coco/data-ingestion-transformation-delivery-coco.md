author: Gilberto Hernandez, Kevin Nguyen, Snowflake CoCo
id: snowflake-northstar-data-engineering
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/feature/cortex-analyst, snowflake-site:taxonomy/feature/dynamic-tables, snowflake-site:taxonomy/feature/semantic-views, snowflake-site:taxonomy/use-case/data-engineering
language: en
summary: Build a fully prompt-driven I-T-D data pipeline in Snowflake using CoCo and Dynamic Tables, then investigate a regional sales drop with a Cortex Agent accessed through Snowflake CoWork.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Data Ingestion, Transformation, and Delivery with Snowflake CoCo
<!-- ------------------------ -->
## Overview
Duration: 3

In this Quickstart, you'll build an end-to-end data pipeline in Snowflake using the **Ingestion–Transformation–Delivery** (I-T-D) framework — and you'll do it the modern way: by prompting **Snowflake CoCo** to write the SQL for you, inside a single **notebook** running in a **Git-backed Snowsight Workspace**.

**Ingestion**

We'll load data from:

- Snowflake Marketplace (live weather data share, installed programmatically)
- AWS S3 (Tasty Bytes sales CSVs via `COPY INTO`)

**Transformation**

We'll transform our data using:

- SQL User-Defined Functions (UDFs)
- **Dynamic Tables** (replacing static views with automatically-refreshing tables)

**Delivery**

We'll deliver a final data product using:

- A **Semantic View** that defines the business metrics analysts care about
- A **Cortex Agent** backed by Cortex Analyst
- **Snowflake CoWork** — the natural-language interface where analysts ask questions

### Prerequisites
- Some basic familiarity with SQL

### What You'll Learn
- The Ingestion-Transformation-Delivery (I-T-D) framework for data pipelines
- How to clone a public GitHub repo as a Git-backed Snowflake Workspace and run a notebook inside it
- How to connect a Snowflake Notebook to a runtime
- How to use **CoCo** to generate and run SQL from natural-language prompts
- How to load data from Snowflake Marketplace and AWS S3
- How to create **Dynamic Tables** that automatically refresh as source data changes
- How to write SQL UDFs and invoke them inside Dynamic Tables
- How to define a **Semantic View** with dimensions, metrics, and verified queries
- How to create a **Cortex Agent** backed by a Semantic View
- How to access the agent through **Snowflake CoWork** to answer business questions in natural language

### What You'll Need
- A free Snowflake trial account: [https://signup.snowflake.com/](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&trial=student&cloud=aws&region=us-east-2&utm_campaign=introtosnowflake&utm_cta=developer-guides)
- The companion GitHub repo: [sfguide-snowflake-northstar-data-engineering](https://github.com/Snowflake-Labs/sfguide-snowflake-northstar-data-engineering) (contains `data-eng-coco.ipynb`)

### What You'll Build
- A fully prompt-driven I-T-D data pipeline in a single notebook
- A Cortex Agent that investigates *"What caused the Hamburg sales gap in February 2022?"*

<!-- ------------------------ -->
## Open a Snowflake Trial Account
Duration: 5

To complete this lab, you'll need a Snowflake account. A free Snowflake trial account will work just fine. To open one:

1. Navigate to [https://signup.snowflake.com/](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&trial=student&cloud=aws&region=us-east-2&utm_campaign=introtosnowflake&utm_cta=developer-guides). This link pre-selects **AWS** and the **US East (Ohio)** region for you.

2. Complete the first page of the form.

3. On the next section, set the Snowflake edition to **Enterprise (Most popular)**.

4. Confirm **AWS – Amazon Web Services** is selected as the cloud provider (pre-filled by the link).

5. Confirm **US East (Ohio)** is selected as the region (pre-filled by the link).

6. Complete the rest of the form and click **Get started**.

![trial](./assets/trial.png)

<!-- ------------------------ -->
## Understand the Pipeline We'll Build
Duration: 3

Tasty Bytes is a food truck company that operates globally. You're a data engineer on the Tasty Bytes team. Data analysts recently flagged a troubling pattern:

> **Sales in Hamburg, Germany dropped to $0 for several days in February 2022.**

Your goal is to find out why — and to build an end-to-end pipeline that keeps analysts informed about Hamburg weather and sales in the future.

### The I-T-D Framework

Before diving in, it's worth understanding the framework we'll use: **Ingestion–Transformation–Delivery (I-T-D)**.

I-T-D is a standard pattern for structuring data pipelines. Instead of mixing raw data, business logic, and presentation into one place, it separates them into three distinct layers — each with a clear responsibility:

| Layer | Job |
|---|---|
| **Ingestion** | Land raw data exactly as it arrives, without modification |
| **Transformation** | Apply business logic, clean, enrich, and reshape the data |
| **Delivery** | Package the data as a consumable product for analysts or applications |

This separation matters because it makes pipelines easier to debug and extend. When something breaks, you know which layer to look at. When requirements change, you change the logic in one layer without touching the others.

### Here's the plan:

**Ingestion**

- Install a live weather data share from Snowflake Marketplace (Pelmorex) programmatically
- Load Tasty Bytes sales data from an AWS S3 bucket using `COPY INTO`

**Transformation**

- Create SQL UDFs to convert weather measurements to metric units
- Create four **Dynamic Tables** that automatically stay fresh as source data updates

**Delivery**

- Create a **Semantic View** joining sales and weather with business-friendly metric definitions
- Create a **Cortex Agent** backed by the Semantic View
- Register the agent in **Snowflake CoWork** and ask: *"What caused the Hamburg sales gap in February 2022?"*

The agent will surface the sales anomaly and correlate it with weather data.

Everything up through Transformation runs from a **single notebook** (`data-eng-coco.ipynb`) that you'll clone from the companion repo. For Delivery, you'll use CoCo to create the Semantic View, then configure the Cortex Agent in the Snowsight UI. Let's get started!

<!-- ------------------------ -->
## Set Up Your Workspace and Notebook
Duration: 10

There are no setup scripts to run and no SQL worksheets to open first. Your very first action is to create a **Git-backed Workspace** that clones the companion repo — which contains the notebook you'll run (`data-eng-coco.ipynb`).

### Sign in as ACCOUNTADMIN

Make sure you are signed into your trial account. Confirm your active role is **ACCOUNTADMIN**.

### Create a Git-backed Workspace

1. In Snowsight, navigate to **Projects » Workspaces**.

2. Click the **+** icon next to **Workspaces/Databases** → **Create new Git workspace**.

![github_workspaces](./assets/gitworkspaces.png)

3. Fill out the modal:
   - **Repository URL:** `https://github.com/Snowflake-Labs/sfguide-snowflake-northstar-data-engineering`
   - **Workspace name:** anything you like (e.g., `northstar-data-eng`)
   - **API integration:** click **+ API Integration** and provide:
     - **Name:** `GITHUB_SNOWFLAKE_LABS`
     - **Allowed prefixes:** `https://github.com/Snowflake-Labs`
   - Check **Public repository**.

4. Click **Create**.

> **What just happened?** The Workspace modal created a Git API integration for you — a one-time step that tells Snowflake which GitHub organization (`Snowflake-Labs`) is an allowed source for Git-backed Workspaces.

The Workspace opens with the repo's files visible in the file explorer on the left including the main notebook you'll need for this lab: `data-eng-coco.ipynb`.

### Open the notebook and set its compute

1. In the Workspace file explorer, open **`data-eng-coco.ipynb`**.

2. Click **Connect** next to the Run button and select **Create and connect**. You can monitor the connection status in the status bar at the bottom of the notebook — wait for it to show **Connected** before proceeding.

![connected](./assets/connected.png)

3. Set the notebook's active **role** and **warehouse** using the picker at the **top-left** of the Notebooks editor (you can also do this in a cell with `USE ROLE` / `USE WAREHOUSE`):
   - **Role:** **ACCOUNTADMIN**
   - **Warehouse:** **COMPUTE_WH** (the default warehouse in every trial account)

   This is the notebook's **query warehouse** — it runs every SQL cell and any Snowpark pushdown compute. (Rendering the interactive results grid doesn't consume credits.)

4. **Note on context:** notebooks in Workspaces do **not** automatically select a database or schema. This notebook handles that for you — its cells run `USE DATABASE` / `USE SCHEMA` and use fully qualified names (e.g., `TASTY_BYTES.RAW_POS.COUNTRY`) — so objects resolve no matter where you run it.

5. Work top-to-bottom through the notebook. Markdown cells explain each step; SQL cells contain the code (some of which you'll generate yourself with CoCo). Run a cell with **▶** (or **Shift+Enter**), or use **Run all** from the toolbar.

> The notebook session idle-suspends after about 30 minutes of inactivity. If it suspends, just restart the session (top-left) and re-run from where you left off — all objects you created persist in Snowflake.

> Throughout the lab, the notebook shows a **CoCo prompt** in the markdown cell directly above each empty SQL cell. Open the **CoCo** panel, paste the prompt, compare CoCo's output against the **Expected output** in the notebook cell, and click **Allow** to run it. Optionally, copy the SQL into the notebook cell for future reference.

The first SQL cell in the notebook (**`setup`**) creates the `TASTY_BYTES` database and three schemas that map directly to the I-T-D pipeline layers:

- `RAW_POS` — raw ingested data (Ingestion)
- `HARMONIZED` — transformed and enriched data (Transformation)
- `ANALYTICS` — data products ready for consumption (Delivery)

…and grants the Cortex Agent and CoWork privileges your role needs. Run the **`setup`** cell before continuing. You should see: *"Statement executed successfully."*

<!-- ------------------------ -->
## Install the Weather Data From Snowflake Marketplace
Duration: 5

The first data source in our pipeline is live weather data. Snowflake Marketplace lets you mount a live dataset directly into your account without copying or moving any data — the provider keeps it fresh automatically.

Rather than clicking through the Marketplace UI, we install the listing **programmatically** from the notebook. This is the repeatable, scriptable way to acquire a Marketplace dataset: accept the listing's legal terms, then create a database directly from the listing.

Run the **`weather_install`** cell in the notebook. You should see: *"Database FROSTBYTE_WEATHERSOURCE successfully created."*

![data](./assets/frostbytedata.png)

The share is now live in your account as `FROSTBYTE_WEATHERSOURCE`. No ingestion logic needed — the data is owned and refreshed by Pelmorex. Later transformation steps reference this database by name.

<!-- ------------------------ -->
## Ingest Sales Data From S3
Duration: 20

Now let's load the Tasty Bytes sales data. It lives across many CSV files in a public AWS S3 bucket. We'll use Snowflake's `COPY INTO` command to bring it in.

### Run the boilerplate table DDL

The notebook's next cell contains `CREATE TABLE` statements for all the raw POS tables plus the `ANALYTICS.ORDERS_V` view. `ORDERS_V` is a denormalized flat join across the raw POS tables — it exists so that every downstream query has a single, simple source for sales data without needing to know the raw schema. This is boilerplate — there's nothing to "solve" here. Run the **`raw_tables`** cell to create the empty target tables and the view.

### Open the CoCo panel

Open the **CoCo** chat panel from the notebook toolbar. Throughout this lab you'll copy prompts directly from the guide (and from the prompt cells in the notebook) and send them to CoCo.

![coco](./assets/coco.png)

> **Key principle:** Use CoCo to generate the hard parts and understand why. The workflow is: describe → generate → compare → run. After CoCo generates SQL, compare it against the **Expected output** shown in the notebook cell. If they match, click **Allow** to run it. Optionally, copy the SQL into the notebook cell for future reference.

### STEP 1 — Create a CSV file format

A **file format** tells Snowflake how to parse raw files during loading. We need one for the CSV data on S3.

Send this prompt to CoCo. Compare the output against the expected output in the notebook — if they match, click **Allow** to run it. Optionally, copy the SQL into the notebook cell for future reference.

> *"Create a CSV file format named CSV_FF in TASTY_BYTES.PUBLIC with type = 'csv'."*

![csvfileformat](./assets/csvfileformat.png)

### STEP 2 — Create the external stage

A **stage** is a pointer to an external storage location (in this case, an S3 bucket) so Snowflake knows where to find the files.

Send this prompt to CoCo. Compare the output against the expected output in the notebook — if they match, click **Allow** to run it.

> *"Create an external stage named S3LOAD in TASTY_BYTES.PUBLIC that points to 's3://sfquickstarts/tastybytes/' and uses the CSV_FF file format."*

![externalstage](./assets/externalstage.png)

### STEP 3 — Load the COUNTRY table (the teaching example)

`COPY INTO` is Snowflake's bulk-loading command — it reads files from a stage and inserts them into a table. This single load teaches you the pattern you'll repeat for every table.

Send this prompt to CoCo. Compare the output against the expected output in the notebook — if they match, click **Allow** to run it.

> *"Write a COPY INTO statement that loads data from @tasty_bytes.public.s3load/raw_pos/country/ into TASTY_BYTES.RAW_POS.COUNTRY. Use FILE_FORMAT = (FORMAT_NAME = TASTY_BYTES.PUBLIC.CSV_FF ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE) to handle extra columns in the source file."*

You should see about 30 rows loaded successfully. Optionally, copy the SQL into the notebook cell for future reference.

![countrytable](./assets/countrytable.png)

### STEP 4 — Load all remaining tables (scale-up)

Now we apply the same `COPY INTO` pattern at scale — loading six more tables in one shot. CoCo will also spin up a larger warehouse for performance, then tear it down to avoid idle credit burn.

Send this prompt to CoCo. Compare the output against the expected output in the notebook — if they match, click **Allow** to run it.

> *"Load the remaining Tasty Bytes tables from the S3 stage @tasty_bytes.public.s3load into their corresponding tables in TASTY_BYTES.RAW_POS: FRANCHISE (raw_pos/franchise/), LOCATION (raw_pos/location/), MENU (raw_pos/menu/), TRUCK (raw_pos/truck/), ORDER_HEADER (raw_pos/order_header/), ORDER_DETAIL (raw_pos/order_detail/). First create a dedicated LARGE warehouse named LOAD_WH with AUTO_SUSPEND = 60 and AUTO_RESUME = TRUE, switch to it, run the COPY INTOs using FILE_FORMAT = (FORMAT_NAME = TASTY_BYTES.PUBLIC.CSV_FF ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE), then drop LOAD_WH and switch back to COMPUTE_WH."*

CoCo will generate SQL that creates a LARGE warehouse (`LOAD_WH`), runs six `COPY INTO` statements, then drops `LOAD_WH` and restores `COMPUTE_WH`. Optionally, copy the SQL into the notebook cell for future reference.

> **Note:** This load covers ~1 GB of data across 6 tables and may take several minutes. Wait for all success messages before continuing.

After all six loads complete, confirm the tables and their row counts in the object explorer on the left.

![tablesloaded](./assets/tablesloaded.png)

This completes the **Ingestion** stage of the pipeline.

<!-- ------------------------ -->
## Transform With UDFs and Dynamic Tables
Duration: 15

We have the raw data. Now we need to transform it into something analysts can query. We'll start with two SQL UDFs for unit conversion, then build four Dynamic Tables that automatically stay fresh as source data updates.

### STEP 1 & 2 — Create the metric-conversion UDFs

A SQL UDF (User-Defined Function) is a reusable function you define once and call anywhere in SQL. The Pelmorex weather data uses imperial units, but analysts want metric. We'll create two UDFs — one to convert Fahrenheit to Celsius and one to convert inches to millimeters — that we'll invoke directly inside Dynamic Table queries.

> **What makes it a UDF:** a SQL UDF **must return a value** of the type declared in its `RETURNS` clause. Its body is a single expression whose result is returned every time you call the function. That's exactly what makes UDFs so handy for **data transformations** — encapsulate a unit conversion, formatting rule, or business calculation once, then reuse it everywhere in SQL, including inside Dynamic Table definitions like the ones below.

Send each prompt to CoCo one at a time. Each UDF encapsulates a single unit-conversion formula so you can call it like a built-in function anywhere in SQL. Compare CoCo's output against the expected output in the notebook — if they match, click **Allow** to run it. Optionally, copy the SQL into the notebook cell for future reference.

**STEP 1:**
> *"Create a SQL UDF named FAHRENHEIT_TO_CELSIUS in TASTY_BYTES.ANALYTICS that accepts a NUMBER(35,4) parameter TEMP_F and returns the Celsius equivalent as NUMBER(35,4)."*

**STEP 2:**
> *"Create a SQL UDF named INCH_TO_MILLIMETER in TASTY_BYTES.ANALYTICS that accepts a NUMBER(35,4) parameter INCH and returns the millimeter equivalent as NUMBER(35,4)."*

Confirm both appear in `TASTY_BYTES.ANALYTICS` in the object explorer.

![udfs](./assets/udfs.png)

### About Dynamic Tables

A **Dynamic Table** is a table whose contents are defined by a query that Snowflake keeps up to date for you automatically. You write the `SELECT` once and declare a target freshness (`TARGET_LAG`); Snowflake works out the refresh schedule and, where possible, only reprocesses the rows that changed (incremental refresh). You get the readability of a view with the query performance of a table — and you never write or schedule pipeline code.

> **Are Dynamic Tables only for "non-real-time" analytics? No.** `TARGET_LAG` can be set as low as **1 minute** (or `DOWNSTREAM`, so a table refreshes just in time for the tables that depend on it), which makes Dynamic Tables a great fit for **both batch and near-real-time / low-latency analytics** — you tune freshness against cost by choosing the lag. Relax it to hours or days when data doesn't change often; tighten it when analysts need current data. (For the *lowest*-latency, high-concurrency serving — think real-time dashboards powering thousands of concurrent users, or data-powered APIs — Snowflake also offers [Interactive Tables](https://docs.snowflake.com/en/sql-reference/sql/create-interactive-table).) See the [Dynamic Tables overview](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview).

> **Interoperability tip:** A Dynamic Table can also be a **Dynamic Iceberg Table** — it stores its results in open **Apache Iceberg** format on cloud storage so external engines like Spark and Trino can read the data directly, using the same refresh model. If your pipeline needs to feed a data lake or non-Snowflake engines, this is the option to reach for. See [Create a dynamic Apache Iceberg™ table](https://docs.snowflake.com/en/user-guide/dynamic-tables/create-iceberg).

The four Dynamic Tables in this pipeline build on each other in layers: `DAILY_WEATHER_DT` (base weather) feeds `WINDSPEED_HAMBURG_DT` and `WEATHER_HAMBURG_DT` (both Hamburg weather). `SALES_HAMBURG_DT` filters the sales data to Hamburg with a full date spine so zero-sales days are visible. `WEATHER_HAMBURG_DT` and `SALES_HAMBURG_DT` are the two tables that power the Semantic View.

### STEP 3 — DAILY_WEATHER_DT (full-refresh Dynamic Table)

This is the base weather Dynamic Table. It joins the live Pelmorex share with Hamburg postal codes to produce one row per postal code per day with city and country labels.

> **Key concept — why `REFRESH_MODE = FULL`?** The source here is the `FROSTBYTE_WEATHERSOURCE` share — a database we don't own. Snowflake can only enable the change tracking that powers *incremental* refresh on objects you own. For third-party shares, incremental refresh isn't possible, so we use `REFRESH_MODE = FULL` (Snowflake recomputes the whole table each cycle).

Run the **`daily_weather_dt`** cell in the notebook.

![dailyweatherdt](./assets/dailyweatherdt.png)

> This refresh takes a few minutes. The downstream Dynamic Tables will pick it up automatically once it completes.

### STEP 4 — WINDSPEED_HAMBURG_DT

This Dynamic Table filters `DAILY_WEATHER_DT` to Hamburg specifically, tracking daily maximum wind speed. It's the intermediate table that isolates Hamburg's weather pattern — critical context for understanding why sales dropped on specific days.

Run the **`windspeed_dt`** cell in the notebook.

![windspeed](./assets/windspeed.png)

> **Expected message — this is not an error.** When you create `WINDSPEED_HAMBURG_DT` (and `WEATHER_HAMBURG_DT` below), you may see:
>
> *"Dynamic table … successfully created. FULL refresh mode was selected because: Change tracking is not supported on dynamic tables with 'FULL' REFRESH_MODE unless the Dynamic Table has FROZEN WHERE constraint specified."*
>
> Here's what it means: these tables read from `DAILY_WEATHER_DT`, which is a **FULL-refresh** table (because *it* reads a third-party share). A Dynamic Table that depends on a FULL-refresh source can't do incremental refresh either — change tracking isn't available up the chain — so Snowflake automatically selects FULL refresh for it too, unless you pin the rows with a `FROZEN WHERE` constraint. The word "successfully" is the important part: the table was created correctly. It simply refreshes in full each cycle rather than incrementally.

### STEP 5 — WEATHER_HAMBURG_DT (with metric conversions)

This is the final weather Dynamic Table — one of the two that power the Semantic View. It aggregates the postal-level data from `DAILY_WEATHER_DT` into **one row per date** and converts temperature and precipitation to metric units using the UDFs you just created.

Run the **`weather_dt`** cell in the notebook.

![weather](./assets/weather.png)

### STEP 6 — SALES_HAMBURG_DT (Hamburg sales with date spine)

This is the sales-side counterpart to `WEATHER_HAMBURG_DT`. It filters sales to Hamburg and adds a **date spine** — a generated sequence of every calendar day — so that days with no orders still appear as rows in the data. Without the date spine, days with no activity would be absent entirely, making it impossible for the Semantic View to detect gaps in the sales record.

Run the **`sales_dt`** cell in the notebook.

After running the **`sales_dt`** cell, confirm `SALES_HAMBURG_DT` appears in `TASTY_BYTES.HARMONIZED`. The initial refresh runs in the background and may take a minute — wait before checking the preview.

![sales](./assets/sales.png)

### Summary

- `DAILY_WEATHER_DT` — weather for all Hamburg postal codes, full-refresh
- `WINDSPEED_HAMBURG_DT` — Hamburg wind speed over time
- `WEATHER_HAMBURG_DT` — Hamburg weather in metric units, one row per day
- `SALES_HAMBURG_DT` — Hamburg sales by day, including days with zero sales

This completes the **Transformation** stage of the pipeline.

<!-- ------------------------ -->
## Deliver With Cortex Agent and CoWork
Duration: 15

We have clean, refreshing data. Now we need to make it accessible to analysts — in natural language. We'll ask CoCo to create the Semantic View, configure a Cortex Agent in Snowsight, and access the agent through **Snowflake CoWork**.

### STEP 1 — Create the Semantic View with CoCo

A Semantic View describes the tables in **business terms**: dates to group by, sales and order values to analyze, weather conditions to compare, and the relationship that connects them. Cortex Analyst uses that model to answer questions about Hamburg sales and weather.

1. In Snowsight, navigate to **AI & ML → Cortex Analyst** and click **Create in Workspaces**.

2. Click **Create with CoCo**.

![CreateCoCo](./assets/createcoco.png)

3. Send CoCo this prompt:

   > *"Create the semantic view with these details:*
   > - *Name: HAMBURG_INSIGHTS_SV*
   > - *Location: TASTY_BYTES.ANALYTICS*
   > - *Source tables: TASTY_BYTES.HARMONIZED.SALES_HAMBURG_DT and TASTY_BYTES.HARMONIZED.WEATHER_HAMBURG_DT*
   > - *Include daily Hamburg sales, order counts, temperature, precipitation, and wind speed, with clear descriptions*
   > - *Use DATE_VALID_STD as the unique key for WEATHER_HAMBURG_DT. Do not set a unique key on SALES_HAMBURG_DT. Define the relationship as many-to-one from ORDER_DATE to DATE_VALID_STD."*

5. Allow CoCo to create the Semantic View draft in the Workspace. This creates an editable draft; it does not publish the view yet.

![semanticcreated](./assets/semanticcreated.png)

6. Review the draft in the Semantic View editor. Confirm it contains:
   - Both `SALES_HAMBURG_DT` and `WEATHER_HAMBURG_DT`, with `DAILY_SALES` and `NUM_ORDERS` under **Facts** for sales
     ![tables](./assets/tables.png)
   - `DATE_VALID_STD` as the unique key for `WEATHER_HAMBURG_DT`, and no unique key on `SALES_HAMBURG_DT.ORDER_DATE`. To find this, hover over the name of the table and click on the pencil to view the dimensions. 
     ![saleshamburg](./assets/saleshamburg.png)
     ![weatherhamburg](./assets/weatherhamburg.png)
   - A **many-to-one relationship** from `SALES_HAMBURG_DT.ORDER_DATE` to `WEATHER_HAMBURG_DT.DATE_VALID_STD`
     ![relationships](./assets/relationships.png)
   - `AVG_TEMPERATURE_CELSIUS`, `AVG_PRECIPITATION_MM`, and `MAX_WIND_SPEED_MPH` under **Facts** for `WEATHER_HAMBURG_DT`

   CoCo may also add time dimensions or metrics. You do not need to find a category named "measures" or require extra SUM metrics for this lab. If one of the items above differs, correct the draft before publishing.

7. Click **Publish**. If Snowsight asks for a name and location, confirm **Name** `HAMBURG_INSIGHTS_SV`, **Database** `TASTY_BYTES`, and **Schema** `ANALYTICS`. Confirm the published view appears under `TASTY_BYTES.ANALYTICS` before adding it to the agent.

### STEP 2 — Create the Cortex Agent

**Cortex Analyst** is Snowflake's text-to-SQL engine — it reads the Semantic View to understand your data model and converts natural-language questions into SQL queries. The **Cortex Agent** is the AI orchestration layer that receives questions from analysts and routes them to Cortex Analyst as the tool.

1. In Snowsight, navigate to **AI & ML → Agents**.

2. Click **Create agent** in the top right.

![createagent](./assets/createagent.png)

3. Configure:
   - **Database and schema:** `TASTY_BYTES.ANALYTICS`
   - **Agent object name:** `HAMBURG_AGENT`

4. Click **Create**.

![agentconfig](./assets/agentconfig.png)

5. Click **Configuration** near the top of the agent editor.

6. Under the **General** tab, set:
   - **Description:** `I am a Hamburg Sales & Weather Intelligence Agent. I analyze Tasty Bytes food truck sales in Hamburg, Germany alongside local weather data to help answer questions about why sales fluctuated.`
   - **Example questions:**
     - `What caused the Hamburg sales gap in February 2022?`
     - `What were Hamburg's best and worst sales months in 2022?`
     - `Is there a relationship between temperature and daily sales in Hamburg?`

![configuration](./assets/configuration.png)

7. Under the **Instructions** tab, set:
   - **Orchestration Instruction:** `Whenever you can answer visually with a chart, always choose to generate a chart even if the user didn't specify to.`
   - **Response instructions:** `Give concise, accurate answers about Tasty Bytes Hamburg sales and weather.`

![instructions](./assets/instructions.png)

8. Click **Tools → Add semantic view** and select **Add semantic view** from the options.

![semanticview](./assets/semanticview.png)

9. Configure the tool:
   - **Service database & schema:** `TASTY_BYTES.ANALYTICS`
   - **Select semantic view:** `HAMBURG_INSIGHTS_SV`
   - **Name:** `TASTY_BYTES_SALES_ANALYST`
   - **Description:** `Answers questions about Tasty Bytes Hamburg sales and weather`

![cortexanalyst](./assets/cortexanalyst.png)

10. Click **Add** then click **Save** in the top right.

![saveagent](./assets/saveagent.png)

### Ask the agent the key question

Since you created the agent through the UI, it is already available in Snowflake CoWork.

1. In Snowsight, navigate to **AI & ML → Snowflake CoWork**.

![cowork](./assets/cowork.png)

2. Select **HAMBURG_AGENT** from the agent list.

3. Ask:

   > *"What caused the Hamburg sales gap in February 2022?"*

![results](./assets/results.png)

The first question starts the investigation, rather than ending it. CoWork can use the Cortex Agent to turn a business question into queries against the Semantic View, then help you explore the results conversationally. Review the answer and any generated chart or SQL before drawing a conclusion: a sales gap that coincides with high wind speeds is a useful lead, but correlation alone does not prove what caused the gap.

### Investigate in CoWork

Continue the same conversation with these follow-up questions:

1. **Locate the gap.** Ask: *"Show daily Hamburg sales and order counts for February 2022. Which dates had zero orders?"*

   Check that zero-order dates appear in the result. The date spine in `SALES_HAMBURG_DT` is what makes those days visible instead of leaving holes in the timeline.

2. **Bring in weather.** Ask: *"For those zero-order dates, show daily sales, order counts, and maximum wind speed alongside the surrounding days. Plot the results by date."*

   This is where the Semantic View's relationship matters: it connects each sales date to the corresponding weather date. If CoWork offers a chart, use it to look for a pattern; if it returns a table, compare the dates and values directly.

3. **Test the explanation.** Ask: *"Were there other high-wind days in February 2022 when Hamburg still recorded sales? Compare them with the zero-order days."*

   A good investigation looks for counterexamples, not just a matching spike. Ask CoWork to show the dates and values behind its summary so you can check whether the proposed explanation holds up.

4. **Summarize the evidence.** Ask: *"Summarize what the sales and weather data show about the February 2022 gap. Separate observations from possible explanations, and say what additional data would be needed to confirm the cause."*

Your results may vary with the available data and the agent's response. Do not treat a generated narrative or visualization as proof without checking its underlying dates, measures, and query.

### What the Delivery Layer Adds

The notebook produced reusable, automatically refreshed sales and weather tables. The Semantic View gives those tables business meaning and defines how they relate. The Cortex Agent makes that model available to CoWork, where an analyst can move from a broad question to a date-by-date comparison without writing a new SQL query for every follow-up.

You have now completed the **Delivery** stage: the pipeline does more than store transformed data — it gives analysts a way to investigate it, challenge an initial hypothesis, and communicate what the evidence does and does not show.

<!-- ------------------------ -->
## Teardown
Duration: 2

> **Before running teardown:** If you're running this guide as part of a Northstar workshop, make sure to run the autograder and answer key before running the teardown. The autograder checks for objects created during this lab — dropping the databases beforehand will cause it to fail.

Once you've finished the lab, run the following to remove all objects created and stop any ongoing credit consumption. The Dynamic Tables created in this lab will continue to refresh automatically until they are dropped.

Run the **`teardown`** cell in the notebook, or execute the following in a SQL worksheet:

```sql
USE ROLE ACCOUNTADMIN;

-- Drops all schemas, tables, dynamic tables, UDFs, semantic view, and cortex agent
DROP DATABASE IF EXISTS TASTY_BYTES;

-- Removes the Marketplace weather share
DROP DATABASE IF EXISTS FROSTBYTE_WEATHERSOURCE;

-- Removes the Git API integration created for the workspace
DROP API INTEGRATION IF EXISTS GITHUB_SNOWFLAKE_LABS;
```

> **Note:** Dropping `TASTY_BYTES` cascades to everything inside it — you don't need to drop individual objects.

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 3

Congratulations! You've successfully built a fully prompt-driven, end-to-end data pipeline in Snowflake using the **Ingestion–Transformation–Delivery** framework — all from a single notebook plus a few UI steps.

### What You Learned

**Ingestion**

- Installed a live weather dataset from Snowflake Marketplace programmatically (zero copy, provider-maintained)
- Loaded ~1 GB of Tasty Bytes sales data from AWS S3 using `COPY INTO`

**Transformation**

- Wrote SQL UDFs that convert imperial weather measurements to metric
- Created four **Dynamic Tables** that refresh automatically:
  - `DAILY_WEATHER_DT` with `REFRESH_MODE = FULL` (required for third-party shares)
  - `WINDSPEED_HAMBURG_DT` filtering to Hamburg
  - `WEATHER_HAMBURG_DT` with metric conversions via UDFs
  - `SALES_HAMBURG_DT` with a date spine to expose zero-sales days

**Delivery**

- Defined a **Semantic View** with business-friendly dimensions and metrics using CoCo
- Created a **Cortex Agent** backed by Cortex Analyst using the Agents UI
- Accessed the agent through **Snowflake CoWork** and asked a natural-language question that produced a chart revealing the windspeed-sales correlation

**The pipeline surfaced the answer**: an analysis of Hamburg sales and weather data in February 2022 reveals a 6-day gap in sales that correlates with a significant windspeed event.

### Related Resources

- [Companion repo: sfguide-snowflake-northstar-data-engineering](https://github.com/Snowflake-Labs/sfguide-snowflake-northstar-data-engineering)
- [Git-backed Workspaces documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git)
- [Dynamic Tables documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview)
- [Create a dynamic Apache Iceberg™ table](https://docs.snowflake.com/en/user-guide/dynamic-tables/create-iceberg)
- [Semantic Views documentation](https://docs.snowflake.com/en/user-guide/views-semantic/sql)
- [Cortex Agents documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [Snowflake CoWork documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork/getting-started)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Learn more at Snowflake Northstar for developers](/en/developers/northstar/)

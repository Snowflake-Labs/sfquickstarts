# Narration

## Intro

We're going to build an AI agent that answers economic questions about the wellbeing of Americans — and make it available to anyone in the organization. The agent will live in Snowflake, but employees will talk to it from Gemini Enterprise, their everyday corporate AI assistant.

We start from raw public data. We land it in an [Apache Iceberg](https://iceberg.apache.org/) table on your own GCS bucket. We teach an AI model what the data means through a Semantic View. And we wrap it all in a Snowflake Cortex Agent powered by Gemini.

The key idea: define your business logic once, in the data layer, not in prompts. That way every consumer — a chat interface, a BI dashboard, an external AI assistant — gets the same correct answer from the same governed data.


## Setup

We need three environments for this lab:

1. **Google Cloud** — we create a GCS bucket for Iceberg storage. Later we use Gemini Enterprise to talk to our agent.
    - Open [Qwiklabs](https://explore.qwiklabs.com) or [direct link](https://explore.qwiklabs.com/classrooms/20821) for your GCP lab environment.
    - Log in or sign up using the same email you used when you registered for the workshop.
    - Qwiklabs will give you a URL to open Google Cloud Console with temporary credentials. Keep this information handy.
    - During setup you'll end up with a temporary profile and Chrome window as a student.
2. **Snowflake** — this is where we build everything: Iceberg tables, Semantic Views, Cortex Agents, and the MCP server.
    - Open a tab and go to [DataOps](https://go.dataops.live/snowflake-and-gemini-workshop) to sign in or register.
    - Open your Snowflake instance with the provided username and password.
3. **Looker** — we connect a BI dashboard to the same Iceberg data.
    - Login information will be provided during the workshop.


## Workspace

Snowflake Workspaces give you a full developer environment in the browser. It connects to a git repo so you can collaborate with a team, and runs Python and SQL files with a built-in compute engine.

We'll use a Snowflake Notebook that walks us through the course. The Notebook service lets you run cells with mixed SQL and Python code in the same session context. You can identify 3 types of cells in this notebook: markdown, python and sql.

Let's open a new workspace connected to [this repo](https://github.com/sfc-gh-akhosro/gcp-snowflake-solutions), then open `hands-on-lab-cortex-gemini/hol-cortex-gemini.ipynb` and start the service connection. It takes a few minutes — start it now and read ahead while it spins up.

> Open a **second browser tab** with the same [Snowflake instance](https://app.snowflake.com). Use that tab to explore the Snowflake UI and its left-hand panel (Marketplace, AI & ML, etc.) throughout this workshop while the first tab stays on the notebook. In this new tab, explore the left hand panel, find and familiarize yourself with Snowflake's Cortex Agents, Analyst, CoWork, Marketplace, and Data Explorer. We will need them later.

Throughout this lab we use two roles:

- **`hol_role`** — this is us, the developer. It runs the notebook and owns everything we create.
- **`end_user_role`** — this simulates a business user who can only ask questions through the agent but can't build or modify anything.

Let's create those roles and grant the needed privileges in our first cell. While you're at it, explore the notebook toolbar — you'll see run, stop, and cell controls up top.


## Architecture

[Apache Iceberg](https://iceberg.apache.org/) is the cornerstone of a modern data platform. It allows multiple engines to read and write directly to the same data, while that data stays in one place — your cloud storage. No copies between systems, no vendor lock-in.

We'll get our data sources from Snowflake Marketplace and land them in an Iceberg table on a GCS bucket. Snowflake Horizon serves as the catalog and governance layer. We could just as easily use Google Cloud Open Lakehouse Runtime or any other IRC-compliant catalog instead.

Next, we use Snowflake Semantic View Autopilot to create a Semantic View that defines the business logic of our Iceberg table. We wrap this in a Cortex Agent and use Gemini as the reasoning model behind it. Snowflake's Cortex adds critical context and logic that makes answers accurate and thorough — customers love it for reduced hallucination.

Then we build an MCP connection between Gemini Enterprise and our Cortex Agent, so employees can talk to their data through their corporate AI chat. Looker helps us visualize and get insights from the same data.

[diagram]

Here's a summary of what each component does:

- **Snowflake Marketplace** — instant access to curated, live datasets. No ETL, no ingestion pipelines.
- **Iceberg** — open table format on your GCS bucket. Multiple engines read the same files. You own the data.
- **Snowflake Horizon** — catalog and governance layer for Iceberg tables. Access control, lineage, and discoverability.
- **Semantic View** — business logic defined once in the data layer. Grounds the AI so it doesn't guess.
- **Cortex Agent** — natural-language interface that turns questions into governed SQL and returns correct answers.
- **Gemini** — the reasoning model powering our agent. Large context window, native to Google Cloud.
- **MCP** — open protocol to expose the agent. Connect once, access from any MCP-compatible client.
- **Snowflake CoWork** — chat interface inside Snowflake for business users who don't write SQL.
- **Gemini Enterprise** — Google Cloud's corporate AI assistant. Employees ask questions in a familiar interface and get grounded answers from Iceberg data via MCP.


## Marketplace

We get our source data from Snowflake Marketplace. It lets teams access curated, live datasets instantly — you click "Get" and the data appears in your account. No ETL pipelines, no data copying. For data providers, it's a secure channel to share or sell data to the world.

We want to build an economic dataset that tracks the financial wellbeing of Americans at the state level. We need income, inflation, mortgage rates, and unemployment — all on a monthly basis. That means four source tables from the Bureau of Labor Statistics and related public data.

Let's go get them.


## Iceberg

Now we need somewhere to land this data.

Iceberg is an open table format. Parquet data files and metadata sit in your own GCS bucket — you own them. Any engine that speaks Iceberg can read them directly: Snowflake, BigQuery, Managed Spark, or any Iceberg REST Catalog–compliant runtime. No copying between systems.

We use `catalog=snowflake`, which means Snowflake manages the table through Snowflake Horizon, handling governance, access control, and discoverability. But the actual data never leaves your bucket.

Let's create the bucket in Google Cloud Console, give Snowflake write access, and build our economic indicators table. When done, do a little exploration: pay attention to the CREATE statement to identify the catalog manager and where actual data sits — your GCS bucket. Go back to Google Cloud Console and explore the bucket; you'll see JSON metadata and Parquet data files. 

## Data Profiling

We have our Iceberg table. Let's look at what's inside.

Snowsight gives you profiling, charting, and pivot tables right in the cell output. You can understand the shape of a dataset without leaving the notebook.

Run the query below. Then try the **Chart** tab to visualize trends, and the **Query Profile** to see how the execution plan works.


## Semantic View

We have a clean Iceberg table. Any analyst can query it with SQL. But that doesn't make it AI-ready.

Here's the gap: when an LLM sees column names like `CPI_INDEX` or `GEO_ID`, it guesses what they mean. It guesses wrong. We need to tell it which columns are dimensions, which are facts, how metrics are calculated, and what kinds of questions this table can answer.

That's what a Semantic View does. You define your business logic once — in the data layer, not scattered across prompts — and every AI consumer inherits the same correct definitions.

The Semantic View is the grounding layer for our agent. We define dimensions (date, geography), facts (CPI, mortgage rate, unemployment, income), and metrics (year-over-year inflation, average mortgage rate by state).

We can also add verified queries — known-good question-to-SQL pairs that anchor the model's behavior for common questions. Without this layer, an LLM guesses and hallucinates. With it, a question like "How has inflation compared to income growth?" maps to the exact right SQL every time.

We use Snowflake Semantic View Autopilot to generate the initial view, then review and refine it.


## Cortex Agent

Now we wrap the Semantic View in a conversational interface.

A Cortex Agent takes a natural-language question and passes it to Cortex Analyst. Cortex Analyst uses the Semantic View to generate correct SQL, executes it, and returns a grounded answer with supporting data. We use Gemini as the reasoning model behind the agent.

The whole thing is defined in a single SQL statement — reproducible and version-controlled.


## CoWork

Snowflake CoWork is the chat surface for business users. No SQL knowledge needed, no notebook — just a conversation with the agent.

Let's switch to `end_user_role` to see what it looks like for someone who can only consume, not build. Ask the same economic question and notice how the response includes the generated SQL for transparency.

Same agent, same data, different role. A chat-based surface instead of a notebook.


## MCP

So far our agent lives inside Snowflake. But what if employees want to ask it questions from Gemini Enterprise, or from another AI tool?

That's where MCP comes in. Model Context Protocol is an open standard that gives AI applications a universal way to connect to data tools. We declare our agent as an MCP tool and add OAuth for secure access. Any MCP-compatible client can then connect — no custom connector per client.


## MCP Server

Let's create the actual MCP server.

We register our Cortex Agent as a callable tool inside a Snowflake-managed MCP server, then set up an OAuth security integration so external clients can authenticate securely. The output from this step gives us the credentials we'll register in Gemini Enterprise next.


## Gemini Enterprise

Gemini Enterprise is Google Cloud's corporate AI assistant — the chat interface employees across the organization already use daily.

By registering our Snowflake MCP server as a data connector, the Cortex Agent becomes a tool that Gemini calls when it needs economic data. Employees ask questions in Gemini and get grounded answers from governed Iceberg data. They don't need to know anything about Snowflake or SQL underneath.

Same question we asked in Snowflake CoWork, same correct answer — just a different surface.


## Looker

The same Iceberg data that powers the AI agent also feeds traditional BI. Looker connects directly to the Snowflake table — no additional copies, no separate pipeline. One data product serves both governed dashboards and AI chat.


## Wrap-up

Let's step back and look at what we built.

One copy of data on open Iceberg in your GCS bucket. A Semantic View that teaches AI what the data means. A Cortex Agent powered by Gemini that turns questions into governed SQL. And we consume it from Snowflake CoWork, Gemini Enterprise, Looker, and any MCP client — all pointing at the same source of truth.

No data copies between systems. No custom integrations for each surface. No hallucination from ungrounded prompts. Build it once, consume it everywhere.

author: Myles Borins
id: getting-started-with-snowflake-app-runtime
summary: Create, preview, change, and deploy your first Snowflake App Runtime app from a Snowsight workspace with Cortex Code. No local install required.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/applications-and-collaboration,snowflake-site:taxonomy/snowflake-feature/build
environments: web
status: Hidden
language: en
duration: 30
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Snowflake App Runtime
<!-- ------------------------ -->
## Overview

You will build and deploy Ask TPC-H, an AI data analyst for a parts distributor, without installing anything. Its charts explain themselves, and you can ask the data a question in plain English and get back a chart. You create the app from a template in a Snowsight workspace, watch it run in Preview, change it by chatting with Cortex Code, and deploy it to its own URL.

Snowflake App Runtime runs your app on Snowflake as an **APPLICATION SERVICE**. You don't build container images, run a registry, or set up a pipeline.

### What You'll Learn

* How to create a Snowflake App Runtime project in Workspaces
* How to run it live with Preview, where each edit reloads the app
* How to change the app with Cortex Code prompts
* How to query Snowflake data and call Cortex AI functions from the app
* How to deploy the app and open it at its own URL

### What You'll Need

* A Snowflake account with Snowflake App Runtime and workspace preview enabled
* A browser. Nothing to install.

<!-- ------------------------ -->
## Create Your App

1. In Snowsight, select **Projects » Workspaces**.
2. In the file explorer, select **+ Add new » Next.js App**.
3. Keep the suggested project name. It ends in a random suffix, so it won't clash with other apps in your account.

Workspaces creates a Next.js project from the Snowflake App Runtime template and opens its *app.yml*. The project includes:

* *app.yml*, the manifest that tells Snowflake how to build, run, and deploy the app
* *package.json*, whose ***dev*** script starts the dev server
* *app/page.tsx*, the home page
* *lib/snowflake.ts*, a helper for running queries from the app. You don't need to edit it.

<!-- ------------------------ -->
## Preview Your App

In the file explorer, hover over your project folder and select the eye icon (**Open to full screen**). This one click starts Preview, opens it full screen, and opens the Cortex Code chat next to it.

Wait for the dev server to start. Preview shows its progress in the logs pane, then shows your running app.

> **Tip:** You can also do this in steps: select **Preview** above *app.yml*, select **Fullscreen** on the Preview pane, then open Cortex Code with the star icon in the side bar.

Preview runs the dev server on Snowflake compute. It is yours alone: nobody else can open it, and it creates no service until you deploy.

> **Tip:** Leave Preview open while you work. When Cortex Code changes a file, the app reloads in place.

<!-- ------------------------ -->
## Change Your App

Paste each prompt into Cortex Code and watch Preview update. Before Cortex Code changes a file, it asks you to accept the change. Review it and accept it to let Cortex Code continue.

The template's home page shows who you are and how the app talks to Snowflake. You'll turn it into Ask TPC-H, built on the sample data in `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`.

> **Tip:** AI answers take a few seconds. The prompts ask Cortex Code to run AI calls in parallel and cache results, so reloads are fast.

### Build the AI dashboard

```text
Change the app's display title to "Ask TPC-H" (keep the name in
app.yml as it is) and pick a primary color I'd like. Make the home
page a sales dashboard on SNOWFLAKE_SAMPLE_DATA.TPCH_SF1: KPI cards
for revenue (sum of O_TOTALPRICE), orders and customers from ORDERS,
a monthly revenue line chart by O_ORDERDATE, and a revenue by region
bar chart joining ORDERS, CUSTOMER, NATION and REGION. Under each
chart, add a one-sentence insight from AI_COMPLETE given the chart's
rows as JSON. Run the AI calls in parallel and cache all results for
10 minutes.
```

The header and colors change, and each chart gets a sentence written by AI.

### Add an Ask box

```text
Add an Ask page with a question box and 4 example questions. On
submit, a server route sends the TPCH_SF1 tables and columns
(ORDERS, LINEITEM, CUSTOMER, NATION, REGION, PART, SUPPLIER) to
AI_COMPLETE with a structured response_format of {sql, chart_type,
x, y, title, answer}. On the server, allow only one SELECT or WITH
statement, reject DDL and DML, wrap it in a LIMIT 200 and set a 30
second timeout. If the SQL fails, send the error back to AI_COMPLETE
once to fix it. Show the chart, a short answer and the SQL.
```

Try "Top 5 nations by revenue in 1997." You get a chart, an answer, and the SQL that made it.

### Pin answers and polish

```text
Let me pin any answer to a Dashboard page, stored in the browser,
that reruns each pinned SQL on load in a grid. Then polish the whole
app: a loading state for every query and AI call, clear empty and
error states, light and dark mode, and a layout that works on a
phone.
```

> **Tip:** If something looks wrong, say so in plain words, for example "the chart is empty" or "make the table fit on my screen." Cortex Code reads the Preview logs and fixes it.

<!-- ------------------------ -->
## Deploy Your App

Preview runs a dev server. Deploying runs the app as a service at its own URL.

Ask Cortex Code:

```text
Deploy this app.
```

You can also select **Deploy** in the editor. The first deploy creates the **APPLICATION SERVICE** and can take a few minutes. Later deploys update the same URL.

When the deploy finishes, open the app: ask Cortex Code to open it, or select **Open deployed app** from the menu next to **Deploy**.

The app deploys to your personal database, so it's yours alone. To share apps with others, an admin first runs app development setup from **Settings » Apps**.

<!-- ------------------------ -->
## Keep Going

You have a working app. Pick a path.

### Stay in Workspaces

Try more prompts on the same app, then deploy again:

```text
Add a Story Cards page. Pick a random customer from
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER with nation and region,
compute their order count, total spend and first and last order date
from ORDERS, and send those stats to AI_COMPLETE with a structured
response_format for a title, persona, superpower and short quote.
Show it as a trading card with a "Draw another card" button.
```

```text
Add an AI Usage page that queries
SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY for the
last 24 hours: total credits, a bar chart of credits by function and
model, and the latest query IDs. If it is empty, say usage shows up
a few minutes after a call and add a refresh button.
```

> **Tip:** Usage takes a few minutes to show up, so try the AI Usage page last and check back if it is empty.

```text
Add a Data page that lists the databases I can access. Selecting a
database shows its schemas, and selecting a schema shows its tables
with row counts. Load each level only when I open it.
```

> **Tip:** To check the phone layout, open Preview in a new browser window and turn on your browser's device emulation in its developer tools.

To use your own data, name the table in the prompt. Your role needs **SELECT** on it.

### Build a bigger app on your laptop

[Build an AI Retention App with Snowflake App Runtime](https://www.snowflake.com/en/developers/guides/build-an-ai-retention-app-with-snowflake-app-runtime/) uses Cortex Code Desktop to build ChurnGuard in three steps: a dashboard, a workflow app that writes to Snowflake, and an app with a Cortex Agent.

<!-- ------------------------ -->
## Cleanup

Ask Cortex Code:

```text
Delete the deployed app for this project.
```

To remove the project too, delete its folder in Workspaces.

<!-- ------------------------ -->
## Conclusion And Resources

### What You Learned

* Create a Snowflake App Runtime project from the Next.js template in Workspaces
* Run it live with Preview
* Change it with Cortex Code prompts, including pages that query Snowflake and call AI_COMPLETE
* Deploy it to its own URL

### Related Resources

* [Snowflake App Runtime documentation](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime)
* [app.yml manifest reference](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/app-yml)
* [Query Snowflake from your app](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/query-snowflake)
* [Access control for Snowflake App Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/access-control)
* [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
* [TPC-H sample data](https://docs.snowflake.com/en/user-guide/sample-data-tpch)
* [AI_COMPLETE structured outputs](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-structured-outputs)

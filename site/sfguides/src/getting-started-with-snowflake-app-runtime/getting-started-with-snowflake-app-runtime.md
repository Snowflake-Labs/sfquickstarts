author: Myles Borins
id: getting-started-with-snowflake-app-runtime
summary: Create, preview, change, and deploy your first Snowflake App Runtime app from a Snowsight workspace with Cortex Code. No local install required.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/applications-and-collaboration,snowflake-site:taxonomy/snowflake-feature/build
environments: web
status: Archived
language: en
duration: 30
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Snowflake App Runtime
<!-- ------------------------ -->
## Overview

You will build and deploy Weather Watch, an AI weather analyst for the United States, without installing anything. It runs on real NOAA weather station data, its charts explain themselves, and you can ask the data a question in plain English and get back a chart. You create the app from a template in a Snowsight workspace, watch it run in Preview, change it by chatting with Cortex Code, and deploy it to its own URL.

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
* The free **Snowflake Curated Data (Free)** listing from Snowflake Marketplace. The next step shows how to get it.

<!-- ------------------------ -->
## Get the Data

Weather Watch uses free, public NOAA weather data that Snowflake curates and maintains.

1. Open the [Snowflake Curated Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255) listing in Snowflake Marketplace.
2. Select **Get**.
3. Keep the default database name, **SNOWFLAKE_CURATED_DATA_FREE**, and select **Get** again.

> **Note:** Getting a listing needs the **ACCOUNTADMIN** role or a role with the **IMPORT SHARE** privilege. On a trial account you have **ACCOUNTADMIN** already.

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

The template's home page shows who you are and how the app talks to Snowflake. You'll turn it into Weather Watch, built on the NOAA tables in `SNOWFLAKE_CURATED_DATA_FREE.PUBLIC_DATA_FREE`.

> **Tip:** The free listing has daily readings from thousands of US weather stations through July 24, 2026. The prompts ask Cortex Code to cache results, so charts load fast after the first view.

> **Tip:** The prompts name the `claude-sonnet-5` model for every AI call. Without a model name, Cortex Code may pick a smaller model that writes weaker SQL and insights.

### Give it a polished look

Start with a quick restyle, no data. Every later page inherits this look.

```text
Restyle the app: title "Weather Watch" (keep the name in app.yml),
dark theme by default, a sky blue accent color, and rounded cards
with soft shadows. Replace the home page demo cards with a hero over
a subtle sky gradient: the headline "Ask the weather anything", a
one-line subtitle, and three small feature cards for real NOAA data,
AI insights, and plain English questions.
```

The whole app changes look before any data shows up.

### Build the AI dashboard

```text
Below the hero, add a 2026 weather dashboard in the same style using
SNOWFLAKE_CURATED_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_METRICS_TI
MESERIES joined to NOAA_WEATHER_STATION_INDEX on
NOAA_WEATHER_STATION_ID, limited to COUNTRY_NAME = 'United States'
and DATE from 2026-01-01 to 2026-07-24. Values are in Celsius and
millimeters. Use only the VARIABLE values maximum_temperature,
minimum_temperature and precipitation. Show cards for the hottest
reading and its state, and the number of stations reporting. Add a
bar chart of the hottest temperature by STATE_NAME, top 10, and a
line chart of the weekly average high for a state picked from a
dropdown, defaulting to Arizona. Run the queries in parallel and
cache each result for 24 hours. Under each chart, add a one-sentence
insight from AI_COMPLETE with the claude-sonnet-5 model given the
chart's rows as JSON. Show a skeleton while each chart loads.
```

The bar chart puts California first at about 50 °C, and the AI points to Death Valley.

### Add an Ask box

```text
Add an Ask page with a question box and 4 example questions. On
submit, a server route sends the columns of SNOWFLAKE_CURATED_DATA_F
REE.PUBLIC_DATA_FREE.NOAA_WEATHER_METRICS_TIMESERIES and
NOAA_WEATHER_STATION_INDEX, the join key, the VARIABLE values
maximum_temperature, minimum_temperature, precipitation and
snowfall, and the date range 2026-01-01 to 2026-07-24 to AI_COMPLETE
(model claude-sonnet-5) with a structured response_format of {sql,
chart_type, x, y, title, answer}. Tell the model to average
precipitation per station when comparing places. On the server,
allow only one SELECT or WITH statement, reject DDL and DML, wrap it
in a LIMIT 200 and set a 60 second timeout. If the SQL fails, send
the error back to AI_COMPLETE once to fix it. Show the chart, a
short answer, and the SQL in a syntax-highlighted code block with a
copy button.
```

Try "Which 5 states got the most rain per station in July 2026?" You get a chart, an answer, and the SQL that made it.

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
Add a Station Cards page. Pick a random US station from SNOWFLAKE_CU
RATED_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_STATION_INDEX with its
name, state, elevation, latitude and longitude, plus its hottest and
coldest 2026 readings from NOAA_WEATHER_METRICS_TIMESERIES, and send
those to AI_COMPLETE (model claude-sonnet-5) with a structured
response_format for a nickname, a personality, a superpower and a
short weather forecast in its voice. Show it as a trading card with
a "Draw another card" button.
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
* [Snowflake Curated Data (Free) listing](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255)
* [AI_COMPLETE structured outputs](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-structured-outputs)

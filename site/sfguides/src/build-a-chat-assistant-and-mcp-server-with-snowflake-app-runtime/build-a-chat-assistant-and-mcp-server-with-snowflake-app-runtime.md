author: Myles Borins, Snowflake CoCo
id: build-a-chat-assistant-and-mcp-server-with-snowflake-app-runtime
summary: In a Snowsight workspace, give a Snowflake App Runtime app one set of tools, then serve them to an in-app chat assistant and to AI agents over MCP.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/applications-and-collaboration,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/snowflake-feature/build
environments: web
status: Published
language: en
duration: 40
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Build a Chat Assistant and MCP Server with Snowflake App Runtime
<!-- ------------------------ -->
## Overview

A [Snowflake App Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/about-snowflake-app-runtime) app can answer questions in two ways: through a chat box in the app, and through an MCP server that AI agents such as Snowflake CoCo call. In this guide you build Repo Radar, a small Next.js app on free GitHub star data that does both from one list of tools. Ask it which open source projects are trending, or how one repo's stars have grown.

You build, preview, and deploy the app in a Snowsight workspace, with nothing to install. You write each tool once. The chat route sends the tools to a model through the Cortex REST API and runs the ones it asks for. The MCP route serves the same tools to agents. Both run inside the app, with the app's sign-in and grants, so you don't create an agent object, an MCP server object, or an API key.

### What You'll Learn

* How to give an app one set of tools for both chat and agents
* How to build a chat assistant on the Cortex Chat Completions API
* How to serve the same tools over MCP
* How to build, preview, and deploy the app with CoCo in Workspaces

### What You'll Build

A Next.js app with a `/chat` page that answers questions about trending GitHub repos, and an MCP server that agents can call.

### What You'll Need

* A Snowflake account with Snowflake App Runtime and workspace preview enabled
* A browser
* The free Snowflake Curated Data (Free) listing from Snowflake Marketplace
* Optional: [CoCo CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) or [CoCo Desktop](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop), to call the MCP server from an agent at the end

<!-- ------------------------ -->
## Get the Data

Repo Radar uses the GitHub Archive data in a free listing that Snowflake curates and maintains. `GITHUB_STARS` has the number of new stars each public repo got each day, and `GITHUB_REPOS` maps each repo ID to its `owner/name`.

1. Open the [Snowflake Curated Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255) listing in Snowflake Marketplace.
2. Select **Get**.
3. Keep the default database name, `SNOWFLAKE_CURATED_DATA_FREE`, and select **Get** again.

Getting a listing needs the `ACCOUNTADMIN` role or a role with the `IMPORT SHARE` privilege.

<!-- ------------------------ -->
## Create the App

1. In Snowsight, select **Workspaces**.
2. Create a new workspace and give it a name.
3. In the workspace, select **+ Add new » Next.js App**.
4. Keep the suggested project name.

Workspaces creates a Next.js project from the Snowflake App Runtime template. The template already connects to Snowflake with the app's credentials, and **app.yml** tells Snowflake how to build, run, and deploy the app. CoCo builds the rest from your prompts.

<!-- ------------------------ -->
## Preview the App

In the file explorer, hover over your project folder and select the eye icon (**Open to full screen**). This starts Preview, opens it full screen, and opens the CoCo chat next to it. Wait for the dev server to start: Preview shows its progress in the logs pane, then shows the starter app.

Leave Preview open while you work. You build the rest of the app by pasting prompts into CoCo. Before CoCo changes a file, it asks you to accept the change. Review it and accept it, and the app reloads in place.

<!-- ------------------------ -->
## Define the Tools

The chat assistant and the MCP server share one set of tools. Each tool has a description that tells a model when to use it, checked arguments, and a query. Paste the following prompt into CoCo:

```text
Repo Radar answers questions about trending GitHub repos, both in an
in-app chat and over MCP, from one shared set of tools. Use the GitHub
star data in SNOWFLAKE_CURATED_DATA_FREE.PUBLIC_DATA_FREE.

Add a trending_repos tool for the repos that gained the most stars over
the last 7 to 90 days (default 30), up to the latest day in the data:
10 repos by default, at most 25. Leave out brand-new repos and repos whose
stars came in short bursts, which removes most star spam.

Add a repo_stars tool for one repo's new stars per week between two dates.

Describe each tool so a model knows when to use it, check every argument,
and bind arguments into the SQL instead of writing them into it.
```

Before you accept CoCo's change, check two things:

* Every argument goes into the SQL as a bind variable, never as text in the statement. A model writes these arguments, so treat them like any other user input.
* Each argument has limits, such as at most 25 repos, so a model can't ask for the whole table.

The queries run with the app owner's rights, so everyone who opens the app gets the same answers. A tool can run as the signed-in user instead. Preview has no caller's rights, so test those tools in the deployed app. See [Query Snowflake](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/query-snowflake).

<!-- ------------------------ -->
## Add the Chat Assistant

For each question, the chat assistant sends the conversation and the tools to the [Cortex Chat Completions API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api), runs any tools the model asks for, and repeats until the model answers. Paste the following prompt into CoCo:

```text
Add an Ask Repo Radar chat page and link to it from the home page. Answer
each question with the Cortex Chat Completions API and the claude-sonnet-5
model, and let the model call the Repo Radar tools until it can answer,
for at most 5 rounds. Send a failed tool call back to the model so it can
try again, and say which argument was wrong. Keep long tool results short
enough for the model, keep no conversation state on the server, and log
each tool call.
```

The app calls Cortex with its own credentials, so you don't create an API key. A few choices keep the loop safe and cheap:

* Each tool's arguments are checked before the tool runs.
* A tool that fails returns an error to the model, which can then try different arguments.
* The round limit and the cap on result size limit the work for each question.
* The browser sends the whole conversation each time, so the server keeps no state.

To use a different model, ask CoCo to switch to one that supports tool calling. See [Tool calling](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api).

### Try the chat

In Preview, select **Ask Repo Radar** and ask:

* "Which 5 repos gained the most stars in the last 30 days?"
* "Pick the top one and show its weekly stars since August."

The Preview logs show a line for each tool the model called. The first question takes a few seconds while the warehouse resumes. If something's wrong, tell CoCo in plain words, for example "the chat answers but never calls a tool." CoCo reads the Preview logs and fixes it.

<!-- ------------------------ -->
## Add the MCP Server

The MCP server gives AI agents the same tools as the chat. Paste the following prompt into CoCo:

```text
Serve the same Repo Radar tools to AI agents as an MCP server at /api/mcp.
Keep it stateless so it works when the app restarts or runs more than one
instance, return tool failures as MCP tool errors, and log each tool call.
```

A stateless server handles each request on its own, so any copy of the app can answer it.

The MCP server has no API key check. App Runtime signs each caller in before a request reaches the deployed app, the same way it does for the app's pages. You'll call it once the app is deployed.

<!-- ------------------------ -->
## Deploy the App

Select **Deploy** above **app.yml**. The first deploy creates the `APPLICATION SERVICE` that runs your app and can take a few minutes. When it finishes, select **Open deployed app** from the menu next to **Deploy**, then select **Ask Repo Radar** and ask a question again.

The app's URL ends in `.snowflakecomputing.app`. The MCP server is at that URL plus `/api/mcp`.

### Share it

The role you deployed with owns the app. Anyone who uses the chat page or the MCP server needs usage on the app:

```sql
GRANT USAGE ON APPLICATION SERVICE <database>.<schema>.<app_name> TO ROLE ANALYST;
```

Apps in your personal database stay private to you. To share apps with other roles, an admin first runs app development setup from **Settings » Apps**.

<!-- ------------------------ -->
## Call the MCP Server from CoCo

This step is optional and runs on your own machine, in CoCo CLI or CoCo Desktop. Add the deployed server, with your app's URL and the name of a Snowflake CLI connection to the same account:

```bash
cortex mcp add repo-radar https://<app-host>/api/mcp --type http --snowflake-connection <connection>
```

`--snowflake-connection` tells CoCo to sign in with that connection, so you don't create or store a token. In CoCo CLI, new servers start turned off: enter `/mcp`, select `repo-radar`, and turn it on. CoCo Desktop reads the same `~/.snowflake/cortex/mcp.json` file. Start a new CoCo session and ask:

```text
Use the repo-radar tools to find this week's trending repos and
compare weekly stars for the top two since September.
```

CoCo calls `trending_repos`, then `repo_stars` twice. The chat page and CoCo use the same tools, so they get the same numbers.

<!-- ------------------------ -->
## Cleanup

In the menu next to **Deploy**, delete the deployed app, or ask CoCo in the workspace:

```text
Delete the deployed app for this project.
```

To remove the project too, delete its folder in Workspaces. If you added the MCP server to CoCo, remove it:

```bash
cortex mcp remove repo-radar
```

<!-- ------------------------ -->
## Conclusion And Resources

### What You Learned

* Give an app one set of tools for both chat and agents
* Build a chat assistant on the Cortex Chat Completions API
* Serve the same tools to agents over MCP at `/api/mcp`
* Preview and deploy the app from a Snowsight workspace

Each model call uses Cortex REST API credits. See the [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf).

### Related Resources

* [Build an MCP server](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/build-mcp-server)
* [Build a chat assistant](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/build-chat-assistant)
* [Develop in Snowsight Workspaces](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/workspaces)
* [Snowflake App Runtime Node.js SDK](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/nodejs-sdk)
* [Cortex REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api)
* [Getting Started with Snowflake App Runtime](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-app-runtime/)
* [Snowflake Curated Data (Free) listing](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255)

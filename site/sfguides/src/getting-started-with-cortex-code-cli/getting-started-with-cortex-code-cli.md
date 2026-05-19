author: Dash Desai
id: getting-started-with-cortex-code-cli
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai
language: en
summary: Install Cortex Code CLI, connect to your Snowflake account, and run your first natural-language queries from the terminal in under 15 minutes.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-code-cli


# Get Started with Cortex Code CLI
<!-- ------------------------ -->
## Overview

Cortex Code is Snowflake's AI-powered coding agent. It is available in two interfaces: directly in [Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight) for web-based use, and as a **command-line interface (CLI)** for developers who prefer the terminal. This guide focuses on the CLI.

Cortex Code CLI lets you query data, build applications, and manage Snowflake resources using plain English directly from your terminal. Behind the scenes it writes and runs SQL, orchestrates Snowflake-native skills, and connects to external tools through the Model Context Protocol (MCP).

In this guide you will install the CLI, connect it to a Snowflake account, and run a handful of queries to see what it can do.

### What You'll Learn
- How to install Cortex Code CLI on macOS, Linux, or Windows
- How to connect to a Snowflake account using browser-based SSO or a programmatic access token
- How to ask natural-language questions and get SQL-backed answers
- How to explore query results with the built-in table viewer
- How to manage sessions so you can pause and resume work

### What You'll Build
A working Cortex Code CLI environment connected to your Snowflake account, ready for day-to-day use.

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) (or [sign up for a free Cortex Code CLI trial](https://signup.snowflake.com/cortex-code))
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation) installed on your workstation
- A terminal with `bash`, `zsh`, or `fish` (macOS / Linux) or PowerShell (Windows)
- The SNOWFLAKE.CORTEX_USER database role (granted to all users by default through the PUBLIC role)

<!-- ------------------------ -->
## Install the CLI

### macOS and Linux (including WSL)

Open a terminal and run the installer:

```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

The script installs the `cortex` executable to `~/.local/bin` and adds it to your PATH.

### Windows (native)

Open PowerShell and run:

```powershell
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

The executable installs to `%LOCALAPPDATA%\cortex` and is added to your PATH automatically.

### Verify the installation

```bash
cortex --version
```

You should see the installed version number printed to the terminal.

<!-- ------------------------ -->
## Connect to Snowflake

Launch Cortex Code CLI by typing `cortex` in your terminal. A setup wizard walks you through connecting to Snowflake.

```bash
cortex
```

The wizard presents two options:

- **Use an existing connection** -- If you already have connections defined in `~/.snowflake/connections.toml` (for example from the Snowflake CLI), select one from the list and press Enter.
- **Create a new connection** -- Select *More options* and follow the prompts to enter your account identifier, username, and authentication method.

### Authentication methods

Cortex Code CLI supports two authentication methods:

| Method | When to use |
|--------|------------|
| Browser-based SSO (`externalbrowser`) | Interactive use on a machine with a web browser |
| Programmatic access token (PAT) | Headless environments or automation |

You can generate a PAT from Snowsight or via SQL. See [Using programmatic access tokens for authentication](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) for details.

### Verify the connection

Once connected, Cortex Code CLI drops you into an interactive session. Type:

```
/status
```

This prints your active connection, role, warehouse, database, and schema.

> **Tip:** Cortex Code CLI defaults to the best available model for your account. Use `/model` to see or switch the active model at any time. Supported models include Claude Opus 4, Claude Sonnet 4, and OpenAI GPT -- see [Supported models](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli#supported-models) for the full list.

> **Note:** If your preferred model is not available in your region, an ACCOUNTADMIN can enable [cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference) to access it from another region.

<!-- ------------------------ -->
## Run Your First Query

With the session running, type a plain-English question:

```
What databases do I have access to?
```

Cortex Code CLI translates your request into SQL, runs it against Snowflake, and returns the results directly in the terminal.

### More examples

Try a few more requests to get a feel for what is possible:

```
Show me the top 10 largest tables in my account by row count
```

```
Write a query for the 5 most recent orders and run it
```

```
Explain what the SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY view contains
```

Cortex Code CLI displays its reasoning steps as it works. If it needs more information it will ask you a follow-up question.

<!-- ------------------------ -->
## Explore Results

### Table viewer

When a query returns tabular data, press **Ctrl+T** to open the built-in table viewer. Inside the viewer you can scroll through results, cycle between tables with **Tab**, and press **c** to copy the query to your clipboard.

### Direct SQL

You can also run SQL directly using the `/sql` slash command:

```
/sql SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE()
```

To limit the number of rows displayed:

```
/sql SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY --limit 50
```

### Reference a table with #

Prefix a fully qualified table name with `#` to pull its schema and sample rows into the conversation automatically:

```
Tell me about #SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
```

Cortex Code CLI fetches the column definitions and a sample of rows so it can answer questions about the table without you having to describe it.

<!-- ------------------------ -->
## Manage Sessions

Every conversation is saved automatically. You can pick up exactly where you left off.

### Resume a session

```
/resume
```

This opens a list of previous sessions. Select one and press Enter, or use `cortex --continue` when launching to jump straight into the most recent session.

### Start fresh

```
/new
```

### Rename the current session

```
/rename my-first-session
```

### Rewind

Made a wrong turn? Roll back to an earlier point in the conversation:

```
/rewind
```

### Fork

Want to try a different approach without losing your current progress? Fork the session:

```
/fork
```

This creates a new session branched from the current point.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully installed Cortex Code CLI, connected it to your Snowflake account, and run your first natural-language queries from the terminal.

From here you can explore slash commands (`/help`), enable plan mode (`/plan`) to review and approve each action before it runs, connect MCP servers for external tools, and add custom skills to tailor the assistant to your workflow.

### What You Learned
- How to install Cortex Code CLI on any supported platform
- How to connect to Snowflake using SSO or a programmatic access token
- How to ask natural-language questions and run SQL from the terminal
- How to explore query results with the table viewer and `#` table references
- How to manage, resume, fork, and rewind sessions

### Related Resources

Documentation:
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
- [Cortex Code CLI Reference](https://docs.snowflake.com/en/user-guide/cortex-code/cli-reference)
- [Cortex Code CLI Settings](https://docs.snowflake.com/en/user-guide/cortex-code/settings)
- [Cortex Code CLI Workflow Examples](https://docs.snowflake.com/en/user-guide/cortex-code/workflows)
- [Model Context Protocol (MCP)](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility.html#extensibility-mcp)

Guides:
- [Best Practices for Cortex Code CLI](https://www.snowflake.com/en/developers/guides/best-practices-cortex-code-cli/)
- [Getting Started with MCP Connectors](https://www.snowflake.com/en/developers/guides/sfguide-getting-started-with-mcp-connectors/)

Additional Reading:
- [Snowflake Developers Blog](https://developers.snowflake.com/blog/)
- [Snowflake Community](https://community.snowflake.com/s/)

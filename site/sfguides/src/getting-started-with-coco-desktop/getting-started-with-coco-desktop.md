author: James Cha-Earley
id: getting-started-with-coco-desktop
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform
language: en
summary: Download Cortex Code Desktop, connect to your Snowflake account, and run your first natural-language queries from a full AI-powered IDE in under 15 minutes.
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Get Started with Cortex Code Desktop
<!-- ------------------------ -->
## Overview

Cortex Code is Snowflake's AI-powered coding agent. It is available in three interfaces: directly in [Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight) for web-based use, as a [command-line interface (CLI)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) for developers who prefer the terminal, and as **Cortex Code Desktop** — a full AI-powered IDE built on VS Code that runs on your machine. This guide focuses on Desktop.

Cortex Code Desktop gives you a complete development environment where you can query data, build applications, and manage Snowflake resources using plain English — without leaving your editor. It has two modes: **Agent Mode** for driving and reviewing agent sessions across multiple projects, and **Editor Mode** for writing code with the agent at your side.

In this guide you will download Desktop, connect it to a Snowflake account, learn the interface, and run a handful of queries to see what it can do.

### What You'll Learn
- How to download and install Cortex Code Desktop on macOS or Windows
- How to connect to a Snowflake account using Local OAuth or SSO
- How to navigate Agent Mode and Editor Mode
- How to ask natural-language questions and get SQL-backed answers
- How to use the SQL Playground and `#` table references
- How to manage, resume, and fork sessions

### What You'll Build
A working Cortex Code Desktop environment connected to your Snowflake account, ready for day-to-day development.

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) (or [sign up for a free Cortex Code trial](https://signup.snowflake.com/cortex-code))
- A machine running macOS or Windows
- The SNOWFLAKE.CORTEX_USER database role (granted to all users by default through the PUBLIC role)

<!-- ------------------------ -->
## Download and Install
Duration: 3

### Download

Go to the [Cortex Code Desktop download page](https://www.snowflake.com/en/product/limited-access/cortex-code/) and download the installer for your platform.

| Platform | Installer |
|----------|-----------|
| macOS | `.dmg` disk image |
| Windows | `.exe` installer |

### macOS

1. Open the downloaded `.dmg` file.
2. Drag **Cortex Code** into your **Applications** folder.
3. Launch Cortex Code from Applications or Spotlight.

> **Note:** On first launch macOS may show a security prompt because the app was downloaded from the internet. Open **System Settings → Privacy & Security** and click **Open Anyway** if this appears. The macOS build is notarized by Apple.

### Windows

1. Run the downloaded `.exe` installer.
2. Follow the setup wizard — the default install location is fine for most users.
3. Launch Cortex Code from the Start menu or desktop shortcut.

### Verify the installation

Cortex Code Desktop launches directly to the onboarding screen. If you see the welcome screen you're ready for the next step.

<!-- ------------------------ -->
## Connect to Snowflake
Duration: 5

On first launch, Cortex Code Desktop walks you through a four-step setup flow: **welcome → connect → mode → theme**.

### Step 1 — Welcome

Click **Next** on the welcome screen to begin.

### Step 2 — Connect to Snowflake

If you already have a `~/.snowflake/connections.toml` file (for example from Cortex Code CLI), your existing connections appear automatically. Select one and click **Next**.

To create a new connection, click **Add connection** and fill in the form:

| Field | Example |
|-------|---------|
| Account identifier | `myorg-myaccount` |
| Connection name | Auto-generated; can be changed |
| Username | Your Snowflake login name |
| Authentication method | Local OAuth (recommended) |

Click **Sign in**. For OAuth or SSO, complete sign-in in your browser when prompted, then return to the app.

> **Tip:** To find your account identifier, sign in at [app.snowflake.com](https://app.snowflake.com), click your avatar in the bottom-left corner, and select **Connect a tool to Snowflake**. Your identifier is in `orgname-accountname` format.

#### Authentication methods

| Method | When to use |
|--------|-------------|
| Local OAuth (recommended) | Interactive use; tokens cached in your OS keychain |
| External Browser (SSO) | Accounts with Okta, Azure AD, or another Identity Provider |
| Password | Direct username/password; MFA-prompted if enabled |
| Key Pair (JWT) | Service accounts and automated workflows |

### Step 3 — Choose a mode

Pick your default startup layout:

- **Agent** — conversations front and center, best for driving and reviewing agent work across projects
- **Editor** — VS Code-style file editor with the agent in a side panel

You can switch between modes at any time with the toggle in the top-right corner (or **⌘E** / **Ctrl+E**).

### Step 4 — Choose a theme

Select **Light** or **Dark**, then click **Get Started** to launch the app.

### Verify the connection

Once in the app, click the connection name in the top navigation bar and select **Manage Snowflake Connections** to confirm your account is connected. You can also type `/connections` in the chat input to open the connection manager.

<!-- ------------------------ -->
## Explore the Interface
Duration: 5

Cortex Code Desktop has two modes. Understanding them helps you get the most out of the app.

### Agent Mode

Agent Mode puts the conversation first. The window has three regions:

| Region | What it does |
|--------|-------------|
| **Navigation panel (left)** | Lists your projects and past sessions. Use **New session** (⌘N / Ctrl+N) to start fresh or click any session to reopen it. |
| **Main chat area (center)** | Your conversation with the agent — messages, tool calls, SQL results, file diffs, and charts all appear here. |
| **Tool bar (right)** | Icons for SQL Playground, Files, Files Changed, Terminal, Browser, Source Control, and more. |

Use the chat input at the bottom: type your message, use `/` to invoke skills, and `@` to add context files or tables.

### Editor Mode

Editor Mode is a standard VS Code layout with the agent in a side panel:

| Region | What it does |
|--------|-------------|
| **Activity bar (left)** | Explorer, Search, Source Control, Run & Debug, Extensions, Snowflake Catalog, Skills, Apps, Agent Settings |
| **Main editor (center)** | File editing, notebooks, and quick-action cards |
| **Session panel (right)** | Your chat — same conversations as Agent Mode |

Switch to Editor Mode when you're writing code, debugging, or using editor extensions. Switch to Agent Mode when you want the agent driving the work.

> **Tip:** The active mode is shown in the top-right corner. Click **Agent** or **Editor** to switch. Your open files and conversation follow you across the toggle.

<!-- ------------------------ -->
## Run Your First Query
Duration: 5

With the session running, type a plain-English question in the chat input:

```
What databases do I have access to?
```

Cortex Code Desktop translates your request into SQL, runs it against Snowflake, and returns the results in the chat. You can see the SQL it generated and the reasoning steps as it works.

### More examples

Try a few more requests to get a feel for what is possible:

```
Show me the top 10 largest tables in my account by row count
```

```
What warehouses are available and what are their sizes?
```

```
Explain what the SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY view contains
```

```
Write a query to show my 5 most recent queries and run it
```

Cortex Code Desktop displays its reasoning steps as it works. If it needs more information it will ask a follow-up question.

### Reference a table with #

Prefix a fully qualified table name with `#` to pull its schema and sample rows into the conversation:

```
Tell me about #SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
```

Cortex Code Desktop fetches the column definitions and a sample of rows so it can answer questions about the table without you having to describe the schema.

### SQL Playground

Click the **SQL Playground** icon in the tool bar (or right-click any SQL block in the chat and select **Open in SQL Playground**) to run SQL directly against your account:

```sql
SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();
```

The SQL Playground is a full editor with syntax highlighting, auto-complete, and inline results — useful when you want to iterate on a query without going through the chat.

<!-- ------------------------ -->
## Manage Sessions
Duration: 3

Every conversation is saved automatically. You can pick up exactly where you left off.

### Resume a session

In Agent Mode, sessions are listed in the navigation panel under each project. Click any session to reopen it.

In Editor Mode, past sessions are listed in the **Session** panel on the right. Click **Recent sessions** to browse and reopen them.

### Start a new session

Click **New session** in the navigation panel, or press **⌘N** (macOS) / **Ctrl+N** (Windows).

### Rename a session

Right-click a session in the navigation panel and select **Rename**.

### Search and filter sessions

Use the customize control on the navigation panel header to search sessions by name, or filter to show only unread sessions.

### Switch between projects

Each project in the navigation panel has its own set of sessions. Click a different project to switch context, or click the **+** button to add a new project folder.

### Private Mode

For sensitive work, enable **Private Mode** from the connection menu in the top navigation bar. Private Mode disables conversation history for the session.

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 2

Congratulations! You've successfully installed Cortex Code Desktop, connected it to your Snowflake account, and run your first natural-language queries from a full AI-powered IDE.

From here you can enable Plan Mode to review and approve each action before it runs, connect MCP servers for external tools via Agent Settings, and add custom skills to tailor the assistant to your workflow.

### What You Learned
- How to download and install Cortex Code Desktop on macOS or Windows
- How to connect to Snowflake using Local OAuth or SSO
- How to navigate Agent Mode and Editor Mode
- How to ask natural-language questions and run SQL
- How to use the SQL Playground and `#` table references
- How to manage, resume, rename, and search sessions

### Related Resources

Documentation:
- [Cortex Code Desktop](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop)
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
- [Agent Mode and Editor Mode](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/agent-mode-and-editor-mode)
- [Onboarding and Authentication](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/onboarding-and-authentication)
- [Skills in Cortex Code Desktop](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop/skills)

Guides:
- [Get Started with Cortex Code CLI](https://quickstarts.snowflake.com/guide/getting-started-with-cortex-code-cli)
- [Getting Started with Cortex Agents](https://quickstarts.snowflake.com/guide/getting-started-with-cortex-agents)
- [Best Practices for Cortex Code CLI](https://quickstarts.snowflake.com/guide/best-practices-cortex-code-cli)

Additional Reading:
- [Snowflake Developers Blog](https://developers.snowflake.com/blog/)
- [Snowflake Community](https://community.snowflake.com/s/)

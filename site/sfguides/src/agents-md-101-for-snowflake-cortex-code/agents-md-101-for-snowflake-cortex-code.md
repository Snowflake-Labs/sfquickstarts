author: David Iken
id: agents-md-101-for-snowflake-cortex-code
language: en
summary: Get started with AGENTS.md in Snowflake Cortex Code — create your first project instruction file in under 5 minutes.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# AGENTS.md 101 for Snowflake Cortex Code
<!-- ------------------------ -->
## Overview

Cortex Code is Snowflake's native AI coding agent. It understands your data, compute, and governance context — but it doesn't know your specific project setup out of the box.

**AGENTS.md is how you tell it.** Drop a plain-text file at your project root and Cortex Code reads it automatically when you start a session. Define your warehouses, conventions, and guardrails once — they apply every session, for every teammate using the same directory.

> **What AGENTS.md is not:** It's not a config file. It doesn't set environment variables or establish connections. It's a set of plain-language instructions that shape how the agent behaves — which warehouses to use, what naming conventions to follow, what operations require approval.

This guide walks you through creating a working AGENTS.md in three steps.

### What You'll Learn

- How to create an AGENTS.md file for Cortex Code
- How to configure warehouse routing and safety guardrails
- How to grow AGENTS.md incrementally as you work
- How to use runtime shortcuts like `#`, `@`, plan mode, and skills

### What You'll Build

- A working AGENTS.md file that configures Cortex Code for your Snowflake project

### Prerequisites

- A [Snowflake account](https://signup.snowflake.com/) (a free trial works)
- Cortex Code CLI installed (see below)
- A text editor
- Familiarity with Snowflake concepts (warehouses, databases, schemas)

### Install Cortex Code CLI

**macOS / Linux / WSL:**
```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

Run `cortex` after install — a setup wizard walks you through connecting to Snowflake. For full details, see the [CLI docs](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).

<!-- ------------------------ -->
## Step 1: Create Your AGENTS.md

You can write AGENTS.md by hand or let Cortex Code generate one for you. Both work — pick whichever fits.

### Option A: Have Cortex Code do it

Start a session in your project directory and prompt:

```
> Look at my project and create an AGENTS.md file with the right Snowflake
  connection, warehouse rules, naming conventions, and safety guardrails.
```

Cortex Code inspects your project files and writes a tailored AGENTS.md. Review what it produces, edit anything that's wrong, and you're done.

### Option B: Manual

Create the file manually:

```bash
touch AGENTS.md
```

Paste this starter template, replacing the placeholder values with your actual Snowflake environment:

```markdown
# My Snowflake Project

## Warehouse Rules
- `COMPUTE_WH`: SELECT queries only (exploration, analysis, reporting)
- `LOAD_WH`: All DDL and DML (CREATE, INSERT, UPDATE, DELETE, MERGE)
- Always run `USE WAREHOUSE LOAD_WH;` before any DDL or DML

## Safety
- Never DROP or TRUNCATE a table without asking first
```


> **Where does it go?** Cortex Code reads AGENTS.md from the directory where you start your session. For most projects, that's the repo root. If you work in a monorepo, place it at whichever directory you `cd` into before running `cortex`.

### Try it

Start a Cortex Code session in your project directory and ask:

```
> Create a staging table for raw order data
```

The agent should pick your DDL warehouse without being told. If it does, your AGENTS.md is working.

<!-- ------------------------ -->
## Step 2: Improve As You Work

The best AGENTS.md files aren't written upfront — they improve from real usage. Work with Cortex Code normally. When you make a decision worth keeping — warehouse routing, a naming convention, a validation step — tell it:

```
> Add that to AGENTS.md
```

Cortex Code appends the rule to your file. Next session, it already knows.

### Prompts that build your AGENTS.md

The most natural way to refine AGENTS.md is through your normal workflow. Here are prompts you can copy-paste at the right moment:

**After Cortex Code resolves an error:**
```
> With what you now know about how to resolve that error, summarize it
  into the AGENTS.md file so you don't repeat the mistake.
```

**After you establish a pattern:**
```
> Add that rule to AGENTS.md so you remember it next time.
```

**When starting a new project:**
```
> Look at the project structure, the existing SQL files, and the dbt
  models, then create an AGENTS.md with build commands, naming conventions,
  and safety rules.
```

**When onboarding a teammate:**
```
> Read AGENTS.md and summarize what you know about this project's
  conventions, then run through the setup steps to verify they still work.
```

This is the core loop: work, learn, capture. Every error Cortex Code resolves and every convention you confirm becomes a permanent instruction — so the next session (or the next teammate) starts smarter.

### What to Capture

| Type | What it captures |
|------|-----------------|
| **Commands** | How to run things: build steps, deploy scripts, SQL validation |
| **Guardrails** | What never to do: forbidden tables, operations, credentials |
| **Conventions** | How to name things: prefixes, suffixes, casing |
| **Validation** | What to verify after changes: row counts, null checks |
| **Lessons learned** | Past mistakes and how to avoid them |

**1. Commands** — what the agent should run and how:

```markdown
## Commands
- Deploy: `scripts/deploy_dashboard.sh`
- Run dbt: `dbt build --select model_name+`
- Lint: `ruff check --fix . && ruff format .`
- Always run `USE WAREHOUSE LOAD_WH;` before any DDL or DML
```

**2. Guardrails** — what the agent must never do:

```markdown
## NEVER
- DROP or TRUNCATE tables outside of DEV
- Modify tables containing `_EXPERIMENT` or `_CONTROL` in the name
- Store credentials or keys in any committed file
```

**3. Conventions** — how your team names things:

```markdown
## Naming
- Tables: plural, snake_case (order_items, customer_events)
- Staging tables: STG_ prefix (STG_ORDERS)
- Temp tables: _TMP suffix, cleaned up at end of session
```

**4. Validation** — what to check after changes:

```markdown
## Validation
- After any CREATE TABLE: run a row count and null check on key columns
- After any data load: verify row count matches source
```

**5. Lessons learned** — mistakes the agent should never repeat:

This is the most valuable section over time. Every time Cortex Code hits an error and resolves it, capture the fix here so it sticks across sessions:

```markdown
## Lessons Learned
- ModuleNotFoundError: use `shared_modules/` imports, not the wheel package
- Regex `:\w+` matches Snowflake path operators — use `/(?<!:):\w+(?!:)/` instead
- Always strip SQL comments (`--` and `/* */`) before running regex on raw SQL
- Preview state disappears on rerun — protect session state keys from being cleared
```

### Nested AGENTS.md for larger projects

If your repo has multiple apps or packages, place a root AGENTS.md with shared rules and a separate AGENTS.md inside each subdirectory with app-specific instructions. Cortex Code reads the nearest one to the files it's working on:

```
my-repo/
├── AGENTS.md                  # Shared: warehouse rules, conventions
├── sales/use_case_health/
│   └── AGENTS.md              # App-specific: deploy command, SiS constraints
└── support/
    └── AGENTS.md              # App-specific: color palette, chart rules
```

### Try it

Ask Cortex Code to do something that hits an error — a wrong warehouse, a missing schema, a naming mismatch. Let it fix the problem, then prompt:

```
> With what you now know about how to resolve that error, summarize it
  into the AGENTS.md file so you don't repeat the mistake.
```

Open AGENTS.md and verify the rule was captured.

<!-- ------------------------ -->
## Step 3: Learn the Shortcuts

AGENTS.md loads once at session start. Cortex Code also has runtime shortcuts that speed up your workflow.

| Shortcut | What it does |
|----------|-------------|
| `#TABLE` | Injects table schema and sample rows as context |
| `@file` | Reads file contents as context |
| `/plan` | Enter plan mode — agent describes and waits for approval |
| `$skill` | Invoke a built-in skill (dbt, ML, Governance, and more) |
| `/compact` | Summarizes conversation to free the context window |

### Reference a Snowflake table with `#`

Type `#` followed by a fully qualified table name. Cortex Code injects the table's schema and sample rows as context:

```
> Summarize #MY_DB.PUBLIC.ORDERS by month
```

### Reference a file with `@`

Type `@` followed by a file path. Cortex Code reads the file and uses it as context:

```
> Explain the logic in @models/staging/stg_orders.sql
```

### Use plan mode for risky operations

Type `/plan` (or press `Shift+Tab` to cycle modes) to enter plan mode. The agent describes what it intends to do and waits for your approval before executing. Use it for any DDL in staging or production.

You can make this automatic by adding it to your AGENTS.md:

```markdown
## Safety
- Use plan mode for any DDL on STAGING or PROD tables
```

### Use skills for specialized tasks

Cortex Code ships with built-in skills for dbt, Streamlit, Machine Learning, Data Governance, and more. Invoke a skill by prefixing its name with `$`:

```
> $machine-learning help me register a model
```

Use `/skill` to open the interactive skill manager where you can browse all available skills.

### Keep sessions focused with `/compact`

Long sessions fill the context window. Use `/compact` to summarize the conversation and free up space without losing important context:

```
> /compact
```

### Pro tips

- **Resume sessions**: `cortex -r last` picks up where you left off.
- **Save rules across sessions**: `cortex ctx rule add "Always run tests before committing"` persists a rule that loads in every future session — independent of AGENTS.md.
- **Keep it short**: A focused 15-line AGENTS.md outperforms a 200-line one. Prioritize whatever affects your daily workflow most.
- **Commit it**: AGENTS.md belongs in version control. Every teammate who clones the repo inherits the same guardrails.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully created a working AGENTS.md for Cortex Code. Every session now starts with your rules loaded. As you work, tell Cortex Code to add new rules to the file. It gets smarter every session.

### The Complete Starter AGENTS.md

Copy this, fill in your values, and let it grow from there:

```markdown
# My Snowflake Project

## Warehouse Rules
- `COMPUTE_WH`: SELECT queries only (exploration, analysis, reporting)
- `LOAD_WH`: All DDL and DML (CREATE, INSERT, UPDATE, DELETE, MERGE)
- Always run `USE WAREHOUSE LOAD_WH;` before any DDL or DML

## Commands
- Validate SQL: `EXPLAIN <query>` before running
- Check tasks: `SHOW TASKS IN SCHEMA mydb.pipeline;`

## Safety
- Use plan mode for any DDL on STAGING or PROD tables
- Never DROP or TRUNCATE tables outside of DEV
- Never use ACCOUNTADMIN for routine work

## NEVER
- Modify tables containing `_EXPERIMENT` or `_CONTROL` in the name
- Store credentials or keys in any committed file

## Lessons Learned
<!-- Add entries here as you work. Prompt: "summarize that fix into AGENTS.md" -->
```

### What You Learned

- How to create an AGENTS.md — by hand or by prompting Cortex Code to scaffold one
- How to separate warehouses for safe DDL and DML execution
- How to grow AGENTS.md incrementally by capturing errors, conventions, and patterns as you work
- How to use runtime shortcuts (`#`, `@`, `/plan`, `$skill`, `/compact`) to speed up your workflow

### Related Resources

Cortex Code:
- [Cortex Code CLI extensibility](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility) — skills, subagents, hooks, and MCP reference
- [Cortex Code overview](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) — built-in skills for dbt, Streamlit, Data Governance, ML

Security:
- [Security best practices](https://docs.snowflake.com/en/user-guide/cortex-code/security) — permissions, sandboxing, managed settings

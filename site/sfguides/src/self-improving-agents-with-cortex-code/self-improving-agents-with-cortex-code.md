author: Josh Reini
id: self-improving-agents-with-cortex-code
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/cortex-code, snowflake-site:taxonomy/snowflake-feature/cortex-agents
language: en
summary: Build a Cortex Agent, evaluate it with Agent GPA, analyze failures, and optimize its instructions — all from Cortex Code.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex Agents, Evaluations, AI, LLM, Snowflake Cortex, Cortex Code, Agent GPA

# Self-Improving Agents with Cortex Code

## Overview

Building AI agents is just the beginning — understanding how well they perform and systematically improving them is what separates prototypes from production systems. In this guide, you'll build a marketing analytics agent, deploy it to production, stress-test it with hard queries, then use Cortex Code to mine failures from logs, evaluate with Agent GPA, and optimize the agent's instructions.

By the end, you'll have an agent with measurably better performance — and a repeatable workflow for continuous improvement.

| Step | What You'll Do |
|------|---------------|
| Setup | Deploy a production agent with 5 tools |
| Stress Test | Run hard queries in Snowflake Intelligence to generate failure traces |
| Install Cortex Code | Install the CLI while traces propagate (~10 min) |
| Evaluate | Mine logs, curate an eval dataset, run Agent GPA baseline |
| Optimize | Analyze failures, generate improved instructions, validate with a second eval |

### Architecture

```
┌──────────────────────────────────────────────────────┐
│              MARKETING CAMPAIGNS AGENT               │
│                                                      │
│  Tool 1: query_performance_metrics (Cortex Analyst)  │
│  Tool 2: search_campaign_content   (Cortex Search)   │
│  Tool 3: generate_campaign_report  (Stored Proc)     │
│  Tool 4: web_search                (Web Search)      │
│  Tool 5: data_to_chart             (Visualization)   │
└──────────────────────────────────────────────────────┘
        │                                     ▲
        ▼                                     │
┌───────────────┐    ┌──────────────┐   ┌─────────────┐
│  Evaluate     │───▶│  Analyze     │──▶│  Optimize   │
│  (Agent GPA)  │    │  (failures)  │   │  (AI-driven)│
└───────────────┘    └──────────────┘   └─────────────┘
```

### What You'll Learn

- How to build a Cortex Agent with multiple tool types (Cortex Analyst, Cortex Search, stored procedures, web search, data-to-chart)
- How to use Snowflake Intelligence to interact with your agent and generate observability traces
- How to use Cortex Code to mine agent logs and curate evaluation datasets
- How to run Agent GPA evaluations with built-in metrics
- How to analyze failure patterns and generate improved orchestration instructions
- How to validate improvements by comparing evaluation scores across agent iterations

### What You'll Build

A complete agent optimization workflow:

- A marketing campaigns agent with 5 tools
- An evaluation dataset curated from real agent interaction logs
- An optimized agent with improved orchestration instructions
- Before/after evaluation results demonstrating measurable improvement

### What You'll Need

- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN access
- [Cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-suite-cross-region) enabled (required for evaluation LLM judge models)
- ~5 minutes for setup script to complete

### Prerequisites

- Basic familiarity with Snowflake SQL and Cortex Agents

<!-- ------------------------ -->

## Run Setup

Download the [`setup.sql`](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/self-improving-agents-with-cortex-code/assets/setup.sql) file from the repository.

Open a Snowflake worksheet in Snowsight and run the entire `setup.sql` file. This creates:

- Database `SELF_IMPROVING_AGENT_DB` with schema `AGENTS`
- 4 data tables (25 campaigns, ~1578 performance records, content, feedback)
- Semantic view, Cortex Search service, report generation procedure
- The production agent `MARKETING_CAMPAIGNS_AGENT`

Verify setup succeeded — the final statement should print a success banner.

<!-- ------------------------ -->

## Stress-Test the Agent in Snowflake Intelligence

Open the agent in Snowflake Intelligence:

1. Go to [ai.snowflake.com](https://ai.snowflake.com) or in Snowsight select **AI & ML > Agents**
2. Select **MARKETING_CAMPAIGNS_AGENT**

Your goal is to generate a mix of successful and failing traces by asking progressively harder questions. Copy-paste these one at a time:

### Simple queries

```
What is the total spend across all campaigns?
```

```
What content was used in the Summer Sale campaign?
```

```
Which campaign had the highest ROI?
```

### Multi-tool queries

```
Which campaign had the highest ROI and what did customers say about it? Generate a report for that campaign too.
```

```
Find our worst performing campaigns, look up what customers complained about, compare to industry benchmarks, and recommend fixes
```

### Complex synthesis queries

```
For each of our top 5 campaigns by revenue, show me the customer feedback and whether the A/B test results support scaling them up
```

```
Build me a quarterly business review — top campaigns, underperformers, customer sentiment trends, and how we stack up against competitors
```

> **Note:** It can take up to 10 minutes for agent interaction traces to appear in the observability logs. If you just finished running the queries above, now is a good time to install Cortex Code (next step) while the traces propagate.

<!-- ------------------------ -->

## Install Cortex Code

Cortex Code is an AI-powered CLI that you'll use to mine agent logs, run evaluations, analyze failures, and generate improved agent instructions.

**Linux / macOS / WSL:**

```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

**Windows (PowerShell):**

```powershell
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

After installation, run `cortex` to launch the setup wizard — it will guide you through connecting to your Snowflake account.

For detailed setup instructions, see the [Cortex Code CLI docs](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).

<!-- ------------------------ -->

## Curate an Eval Dataset from Logs

Open Cortex Code and enter `/bypass` to enable bypass mode, then enter the following prompt:

```
Use the dataset-curation skill to pull production traces for
SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT and curate
an evaluation dataset. Store it in SELF_IMPROVING_AGENT_DB.AGENTS and register it as a new
evaluation dataset.
```

Cortex Code will:

1. Query the observability traces from the previous step
2. Help you select and annotate queries with ground truth
3. Create an eval table and register it via `SYSTEM$CREATE_EVALUATION_DATASET`

<!-- ------------------------ -->

## Run Baseline Evaluation

Run Agent GPA on your curated dataset. Enter this prompt in Cortex Code:

```
Run an evaluation for SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT
against the registered dataset. Once the eval completes, show me the evaluation results. Break down scores by metric and
identify which queries scored lowest. What are the common failure patterns?
```

**Common failure patterns you'll see:**

- Wrong tool selection for multi-tool queries
- Redundant tool calls
- VaIncomplete summaries missing key data

### Generate improved instructions

```
Based on the failure analysis, generate improved orchestration instructions
for SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT that fix
the identified issues. The instructions should tell the agent when to use
multiple tools and in what order. Apply the changes.
```

Cortex Code will:

1. Draft improved orchestration instructions with explicit tool routing rules
2. Apply via `ALTER AGENT ... SET SPECIFICATION = ...`

**What changes:** Only the `instructions.orchestration` field. Tools, tool_resources, and models stay identical. Better instructions are the only lever.

### Validate with a second eval

```
Run the evaluation of SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT
against the same dataset again. Compare the results
against the baseline — show me a side-by-side comparison of
scores by metric and highlight what improved.
```

**What to look for:**

- **Overall score improvement**: The optimized agent should score higher across both metrics
- **No regressions**: The optimized agent should still handle simple queries just as well as the baseline

<!-- ------------------------ -->

## Conclusion and Resources

Congratulations! You've built a self-improving AI agent workflow — deploying a production agent, stress-testing it, mining failures from logs, evaluating with Agent GPA, and validating that improved instructions lead to measurably better performance.

### What You Learned

- How to build a multi-tool Cortex Agent with Cortex Analyst, Cortex Search, stored procedures, web search, and data-to-chart capabilities
- How to generate observability traces by stress-testing your agent in Snowflake Intelligence
- How to use Cortex Code to mine agent logs and curate evaluation datasets
- How to run Agent GPA evaluations with built-in metrics
- How to analyze failure patterns and generate improved orchestration instructions
- How to validate improvements by comparing baseline vs optimized evaluation scores
- That better instructions — not more tools — are the key lever for agent improvement

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent GPA** | Evaluation framework with built-in metrics for answer correctness and logical consistency |
| **Orchestration Instructions** | Natural language instructions telling the agent how to route queries and coordinate tools — the key lever for improvement |
| **Eval Dataset** | Frozen snapshot of queries + ground truth used to score agent performance |
| **Cortex Code** | AI-powered CLI that mines agent logs, runs evaluations, identifies failures, and generates improved agent instructions |

### Related Resources

- [Agent GPA Paper](https://bit.ly/agent-gpa)
- [Cortex Agent Evals Guide](https://bit.ly/cortex-agent-evals)
- [DeepLearning.AI Course](https://bit.ly/deeplearning-agent-gpa)
- [Cortex Code CLI Docs](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)

### Cleanup

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS SELF_IMPROVING_AGENT_DB;
DROP ROLE IF EXISTS SELF_IMPROVING_AGENT_ROLE;
```

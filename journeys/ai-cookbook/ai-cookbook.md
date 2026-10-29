sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy, Parker Erickson
id: ai-cookbook
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Deployment patterns for Cortex AI, drawn from real Snowflake deployments, with verified code to adapt to your own account.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook

# Cortex AI Cookbook

## Overview

Deployment patterns for Cortex AI, drawn from real Snowflake deployments. Each recipe explains the design and the security model, then gives you verified code to run in your own account and adapt.

[View on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook)

> **Using these patterns.** The code is a reference implementation of each pattern, built on synthetic data with minimal names and sizes. Review it, then adapt roles, object names, warehouse sizes, secrets handling, and error handling to your environment before you take it to production. Questions about the Snowflake features a recipe uses go through your usual Snowflake support channels; problems with the cookbook code go to [GitHub issues](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues).

## How to use a recipe

1. Pick a recipe from the index below.
2. Read **When to use this** and **Prerequisites**. Recipes marked **Preview** depend on at least one preview feature.
3. Run the scripts in `sql/` in order, then the queries under **Verify**.
4. Run `sql/99_teardown.sql` when you are done. It drops everything the recipe created (every object is named `COOKBOOK_<RECIPE>`) and reverts any account-level change. Then adapt the pattern to your environment.

To have a coding agent do it, clone the repository, open it in Cortex Code (or any coding agent), and paste the prompt from the recipe's **Run it with a coding agent** section. [AGENTS.md](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/AGENTS.md) holds the rules agents follow in this repository.

## Recipes

Every recipe is runnable end to end, with setup, verification, and teardown. Recipes are listed in reading order, by the stage of a project each one applies to first: Scope, Build, Secure, Evaluate, Operate.

| Recipe | What it covers | Stage | Topics | Status |
|---|---|---|---|---|
| [Scoping agentic implementations: from 'talk to your data' to a testable agent spec](/en/developers/guides/ai-cookbook/scoping-agentic-implementations/) | A workshop method for turning a broad agent idea into personas, a question taxonomy, a registered evaluation dataset, and a phased delivery plan. | Scope, Evaluate | Cortex Agents, AI Observability, Cortex AI Functions | GA |
| [Snowflake-managed MCP or the Cortex Agents REST API](/en/developers/guides/ai-cookbook/mcp-or-agent-rest-api/) | Decide how people reach a Cortex Agent, with identity and policies in each lane, then best practices for managed MCP servers and the Agents REST API. | Scope, Secure, Build | Snowflake MCP, Cortex Agents | GA |
| [Agentic schema mapping: messy CSVs to canonical tables with a Cortex Agent](/en/developers/guides/ai-cookbook/agentic-schema-mapping/) | A Cortex Agent profiles messy CSV files, proposes column mappings with AI_COMPLETE, resolves free-text values, and loads approved mappings through allowlisted SQL. | Build | Cortex AI Functions, Cortex Agents | GA |
| [Embedded app context for a Cortex Agent](/en/developers/guides/ai-cookbook/embedded-app-context/) | Give an agent embedded in a Streamlit dashboard the page, filters, and persona the user is looking at, by prepending an app-context block to the user message. | Build | Cortex Agents | GA |
| [Attach documents to Cortex Agent conversations](/en/developers/guides/ai-cookbook/document-context/) | Let users attach PDFs, Office files, images, and CSVs to a custom agent frontend with a caller's-rights document tool, per-user stage folders, and authenticated middleware. | Build, Secure | Cortex Agents | GA |
| [Multi-agent orchestration with caller's-rights delegation](/en/developers/guides/ai-cookbook/multi-agent-orchestration/) | One orchestrator agent delegates to specialist agents through caller's-rights DATA_AGENT_RUN bridges, so Snowflake grants decide which specialist each user reaches. | Build, Secure | Cortex Agents, Semantic Views | GA |
| [PII redaction with AI_REDACT, AI_COMPLETE extraction, and an entity cache](/en/developers/guides/ai-cookbook/pii-redaction/) | Redact PII in free text with AI_REDACT, cover domain identifiers with AI_COMPLETE structured extraction, and serve redactions from a stream-maintained cache. | Build, Secure | Cortex AI Functions | GA |
| [Causally grounded Cortex Agent that refuses when the data cannot answer](/en/developers/guides/ai-cookbook/agent-causal-grounding/) | A Cortex Agent whose every number comes from a persisted causal estimator, and which declines to answer for cohorts where no honest estimate exists. | Build, Evaluate | Cortex Agents, Semantic Views | GA |
| [Mixed-grain tables: diagnose and fix wrong agent answers with a GRAIN dimension and verified queries](/en/developers/guides/ai-cookbook/mixed-grain-and-verified-queries/) | An agent double-counts a table that holds daily and monthly rows. Diagnose it from wrong answers, fix the semantic view with a GRAIN enum, rules, and verified queries, re-test. | Build, Evaluate | Semantic Views, Cortex Agents | GA |
| [Long-running Cortex Agent runs over managed MCP](/en/developers/guides/ai-cookbook/long-running-agents-over-mcp/) | Split one long MCP tool call into a fast submit and a bounded fetch over background agent runs, so no call nears a client's timeout and caller's rights still apply. | Build, Operate | Snowflake MCP, Cortex Agents | GA |
| [OAuth token passthrough to a Cortex Agent](/en/developers/guides/ai-cookbook/oauth-token-passthrough/) | Relay each signed-in user's Entra ID token to a Cortex Agent so the agent runs as that person, with per-user results from a row access policy on CURRENT_USER(). | Secure | Cortex Agents | GA |
| [Multi-tenant agents with session attributes and fail-closed policies](/en/developers/guides/ai-cookbook/multi-tenant-agents/) | Serve many tenants from one Cortex Agent: the app server names the end user in an immutable session attribute, and policies derive the tenant from an entitlement. | Secure, Build | Cortex Agents, Semantic Views | GA |
| [Semantic view description quality: a rubric, a linter, and how to apply fixes](/en/developers/guides/ai-cookbook/description-quality/) | Grade semantic view descriptions on preciseness, conciseness, non-circularity, and correctness, lint them in SQL, and apply fixes with CREATE OR ALTER or the YAML procedure. | Evaluate | Semantic Views, Cortex AI Functions | GA |
| [Evaluate and promote Cortex Agent versions](/en/developers/guides/ai-cookbook/agent-evaluations/) | Run Cortex Agent evaluations with pinned metric versions and a custom judge, compare two committed versions, and promote the winner by alias. | Evaluate, Operate | Cortex Agents | GA |
| [Refine a semantic view from agent logs: triage, SME review, and verified queries](/en/developers/guides/ai-cookbook/refinement-loop-from-agent-logs/) | Mine Cortex Agent traces for guessed, exploratory, and no-data answers, get the right answer from a subject matter expert, ship it into the semantic view, and re-test. | Evaluate, Operate | Semantic Views, AI Observability, Cortex Agents | GA |
| [Turn agent feedback and rephrased questions into an evaluation dataset](/en/developers/guides/ai-cookbook/agent-feedback-to-evals/) | Mine thumbs-down feedback and user rephrases from agent traces, confirm each with one LLM call, and write a deduplicated eval dataset. | Evaluate, Operate | AI Observability, Cortex Agents | GA |
| [Agent versioning and promotion](/en/developers/guides/ai-cookbook/agent-versioning-and-promotion/) | Commit, alias, promote, A/B route, and roll back Cortex Agent versions with runnable SQL and the behaviors observed along the way. | Operate | Cortex Agents | GA |
| [AI usage and cost attribution across agents, CoWork, Cortex Code, and AI functions](/en/developers/guides/ai-cookbook/ai-usage-cost-attribution/) | One reconciled view of Cortex AI credits by surface, user, agent, model, and cost center, plus budgets and per-user quotas. | Operate | AI Observability, Cortex Code, Cortex AI Functions | GA |
| [Diagnose slow Cortex Agent requests from their traces](/en/developers/guides/ai-cookbook/diagnose-agent-requests/) | A caller's-rights procedure that reads one agent request's trace, computes a time breakdown by span, and returns an LLM explanation. | Operate | AI Observability, Cortex Agents | GA |
| [Size Cortex Code per-user limits from real usage](/en/developers/guides/ai-cookbook/coco-user-budget-sizing/) | Tiered per-user CoCo quotas, daily limits, and alert-only team budgets, starting from conservative defaults and sized from your own ACCOUNT_USAGE. | Operate | AI Observability, Cortex Code | GA |
| [LangChain agents on Cortex AI Gateway with MCP tools and traces](/en/developers/guides/ai-cookbook/langchain-mcp-agent-tracing/) | External LangChain agents reason through Cortex AI Gateway, act through a Snowflake MCP server, and are analyzed from gateway traces and per-user cost. | Operate, Build | Cortex AI Gateway, Snowflake MCP, AI Observability | Preview |
| [Cortex AI Gateway governance quickstart](/en/developers/guides/ai-cookbook/gateway-governance-quickstart/) | Route an app through Cortex AI Gateway with its own identity: both API formats, a model allowlist, traces, per-user cost, and a blocking quota. | Operate, Secure | Cortex AI Gateway, AI Observability | Preview |
| [Agent CI/CD with dbt: per-PR builds, versioned deploys, and an evaluation gate](/en/developers/guides/ai-cookbook/agent-ci-cd-with-dbt/) | dbt builds the tables and semantic view, the agent ships as a versioned spec from a stage, and an evaluation gate in GitHub Actions blocks promotion. | Operate, Evaluate | Cortex Agents, Semantic Views | GA |

Each recipe's code is a reference implementation: review it and adapt it to your environment before production. Questions about Snowflake features go through your usual Snowflake support channels; problems with the cookbook code go to [GitHub issues](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues).

Looking for installable Cortex Code skills? See [coco-skills](https://github.com/Snowflake-Labs/coco-skills). Contributions welcome: [see the guide](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/CONTRIBUTING.md).

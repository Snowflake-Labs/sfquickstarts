Deployment patterns for Cortex AI, drawn from real Snowflake deployments. Each recipe explains the design and the security model, then gives you verified code to run in your own account and adapt.

[View on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook)

This page is a hand-built sample of the Cortex AI Cookbook journey, so the layout can be reviewed before the journey staging and nested-URL work is live. It contains two recipes under Cortex Agents; the full cookbook has more.

> **Using these patterns.** The code is a reference implementation of each pattern, built on synthetic data with minimal names and sizes. Review it, then adapt roles, object names, warehouse sizes, secrets handling, and error handling to your environment before you take it to production. Questions about the Snowflake features a recipe uses go through your usual Snowflake support channels; problems with the cookbook code go to [GitHub issues](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues).

## How to use a recipe

1. Pick a recipe from the index below.
2. Read **When to use this** and **Prerequisites**. Recipes marked **Preview** depend on at least one preview feature.
3. Run the scripts in `sql/` in order, then the queries under **Verify**.
4. Run `sql/99_teardown.sql` when you are done. It drops everything the recipe created (every object is named `COOKBOOK_<RECIPE>`) and reverts any account-level change. Then adapt the pattern to your environment.

To have a coding agent do it, open the recipe folder in Cortex Code (or any coding agent) and paste the prompt from the recipe's **Run it with a coding agent** section. [AGENTS.md](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/AGENTS.md) holds the rules agents follow in this repository.

## Recipes

Every recipe is runnable end to end, with setup, verification, and teardown. The full cookbook lists recipes in reading order, by the stage of a project each one applies to first: Scope, Build, Secure, Evaluate, then Operate. This sample includes the two below.

| Recipe | What it covers | Stage | Topics | Status |
|---|---|---|---|---|
| [Evaluate and promote Cortex Agent versions](https://www.snowflake.com/en/developers/guides/ai-cookbook/agent-evaluations/) | Run Cortex Agent evaluations with pinned metric versions and a custom judge, compare two committed versions, and promote the winner by alias. | Evaluate, Operate | Cortex Agents | GA |
| [Agent versioning and promotion](https://www.snowflake.com/en/developers/guides/ai-cookbook/agent-versioning-and-promotion/) | Commit, alias, promote, A/B route, and roll back Cortex Agent versions with runnable SQL and the behaviors observed along the way. | Operate | Cortex Agents | GA |

Each recipe's code is a reference implementation: review it and adapt it to your environment before production. Questions about Snowflake features go through your usual Snowflake support channels; problems with the cookbook code go to [GitHub issues](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues).

Looking for installable Cortex Code skills? See [coco-skills](https://github.com/Snowflake-Labs/coco-skills). Contributions welcome: [see the guide](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/CONTRIBUTING.md).

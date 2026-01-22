# Cortex Code Skills

This folder contains skills for deploying the NovaConnect Telco Operations AI solution using Cortex Code CLI.

## What are Skills?

Skills are structured markdown specifications that guide Cortex Code through complex procedures. They provide:

- **Step-by-step instructions** for deployment tasks
- **SQL and CLI commands** ready to execute
- **Verification steps** to confirm success
- **Troubleshooting guidance** for common issues

## Available Skills

| Skill | Description | Use When |
|-------|-------------|----------|
| [deploy-notebooks](deploy-notebooks.md) | Deploy Snowflake Notebooks | Setting up data processing and analysis notebooks |

## Using Skills with Cortex Code

### Method 1: Local Skill Reference

```
use the local skill from skills/deploy-notebooks
```

### Method 2: Natural Language

Simply describe what you want to do:

```
Deploy the Snowflake notebooks for the telco quickstart
```

Cortex Code will match your request to the appropriate skill.

## Skill Execution

When you invoke a skill, Cortex Code will:

1. Read the skill's markdown file
2. Execute each step in sequence
3. Pause at verification points for confirmation
4. Report success or provide troubleshooting guidance

## Creating Custom Skills

You can create your own skills by adding markdown files to this folder. A skill should include:

```markdown
# Skill Title

Description of what the skill does.

## Prerequisites

What must be in place before running.

## Steps

### Step 1: First Action

```sql
-- SQL commands to execute
```

### Step 2: Next Action

```bash
# CLI commands to run
```

## Verification

How to confirm success.

## Troubleshooting

Common issues and solutions.
```

## Related Resources

- [Cortex Code Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cortex-code/overview)
- [Telco Agent Builder Skill](../cortex_code_skill/telco-agent-builder.yaml) - Full deployment skill
- [Quickstart Guide](../../build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence.md)

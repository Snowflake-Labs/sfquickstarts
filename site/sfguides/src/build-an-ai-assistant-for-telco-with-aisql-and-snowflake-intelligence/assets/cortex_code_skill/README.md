# Telco Agent Builder - Cortex Code Skill

This skill enables you to build the **NovaConnect Telco Operations AI Agent** end-to-end using the Cortex Code CLI.

## What This Skill Does

The Telco Agent Builder skill guides you through deploying a complete AI-powered telecommunications operations assistant, including:

- **Database & Infrastructure**: Creates the TELCO_OPERATIONS_AI database with all required schemas, stages, and roles
- **Data Loading**: Uploads CSV data, PDFs, and audio files to Snowflake stages
- **Cortex Search Services**: Deploys semantic search over call transcripts and support tickets
- **Cortex Analyst**: Uploads semantic model YAML files for natural language to SQL
- **Snowflake Intelligence Agent**: Creates the unified AI assistant with all tools configured
- **Snowflake Notebooks**: Deploys data processing and analysis notebooks
- **SnowMail Native App**: Installs a Gmail-style email viewer for agent notifications

## Installation

### Option 1: Install from Local Directory

```bash
# Navigate to the skill directory
cd site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/cortex_code_skill

# Install the skill
cortex skill install telco-agent-builder.yaml
```

### Option 2: Copy to Cortex Code Skills Directory

Copy the `telco-agent-builder.yaml` file to your Cortex Code skills directory:

```bash
# macOS/Linux
cp telco-agent-builder.yaml ~/.cortex/skills/

# Windows
copy telco-agent-builder.yaml %USERPROFILE%\.cortex\skills\
```

## Usage

Once installed, you can invoke the skill in Cortex Code by:

1. **Direct invocation**:
   ```
   /telco-agent-builder
   ```

2. **Natural language triggers**:
   - "Build the telco agent"
   - "Deploy the NovaConnect quickstart"
   - "Set up the telco operations AI"
   - "Help me deploy the telecommunications agent"

## Prerequisites

Before running the skill, ensure you have:

1. **Snowflake Connection**: A configured connection in Cortex Code
   ```bash
   snow connection list
   ```

2. **ACCOUNTADMIN Role**: Required for creating databases, warehouses, and native apps

3. **Quickstart Assets**: The assets directory should be available locally:
   ```
   assets/
   ├── data/           # CSV files and PDFs
   ├── audio/          # MP3 call recordings
   ├── semantic_models/ # YAML files
   ├── Notebooks/      # Jupyter notebooks
   ├── native_app_snowmail/  # Native app source
   └── sql/            # SQL deployment scripts
   ```

## Deployment Steps

The skill guides you through these steps:

| Step | Description | SQL Script |
|------|-------------|------------|
| 1 | Configure Account (roles, warehouse, database) | 01_configure_account.sql |
| 2 | Create Data Foundation (tables, load data) | 02_data_foundation.sql |
| 3 | Deploy Cortex Search Services | 03_deploy_cortex_search.sql |
| 4 | Deploy Cortex Analyst & Intelligence Agent | 04_deploy_cortex_analyst.sql |
| 5 | Deploy Snowflake Notebooks | 05_deploy_notebooks.sql |
| 6 | Deploy SnowMail Native App | 06_deploy_snowmail.sql |
| 7 | Verify Deployment | (verification queries) |

## Example Session

```
You: Build the telco agent for me

Cortex Code: I'll help you deploy the NovaConnect Telco Operations AI Agent. 
Let me first check your Snowflake connection and verify the assets are available.

[Executes deployment steps with progress updates]

Deployment complete! Here's what was created:
- Database: TELCO_OPERATIONS_AI
- Agent: SNOWFLAKE_INTELLIGENCE.AGENTS."Telco Operations AI Agent"
- Cortex Search Services: CALL_TRANSCRIPT_SEARCH, SUPPORT_TICKET_SEARCH
- Notebooks: 1_DATA_PROCESSING, 2_ANALYZE_CALL_AUDIO, 3_INTELLIGENCE_LAB
- Native App: SNOWMAIL

Try asking the agent: "Which regions have the highest network latency?"
```

## Testing the Agent

After deployment, test your agent with these sample questions:

- "Which regions have the highest network latency issues?"
- "Show me 5G towers operating above 80% capacity"
- "Find calls mentioning network connectivity problems"
- "What are the top 3 customer complaints in October 2025?"
- "Find support tickets about billing issues"
- "Which customer segments have the highest churn risk?"

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Use ACCOUNTADMIN role |
| Stage copy fails | Check file paths and stage existence |
| Cortex Search fails | Ensure source tables have data |
| Agent creation fails | Verify all tool references (search services, semantic models) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Snowflake Intelligence                        │
│                 "Telco Operations AI Agent"                      │
├─────────────────────────────────────────────────────────────────┤
│                           Tools                                  │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  Cortex Analyst │  Cortex Analyst │      Cortex Search          │
│  (Network Perf) │  (Customer FB)  │  (Transcripts + Tickets)    │
├─────────────────┴─────────────────┴─────────────────────────────┤
│                    TELCO_OPERATIONS_AI                           │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐    │
│  │DEFAULT_SCHEMA│CORTEX_ANALYST│  NOTEBOOKS   │  STREAMLIT │    │
│  │  (Tables)    │(Semantic YAML│ (3 Notebooks)│            │    │
│  └──────────────┴──────────────┴──────────────┴────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    Native Apps: SNOWMAIL                         │
└─────────────────────────────────────────────────────────────────┘
```

## Related Resources

- [Snowflake Intelligence Documentation](https://docs.snowflake.com/en/user-guide/snowflake-intelligence)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Native Apps](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)

## License

This skill is part of the Snowflake Quickstart program.

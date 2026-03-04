# Assets for Telco AI Assistant Quickstart

This folder contains all assets for the Build an AI Assistant for Telco quickstart guide.

## Folder Structure

```
assets/
├── architecture.png          # Full architecture diagram
├── arch.png                  # Simplified architecture diagram
├── audio/                    # 25 MP3 call recordings
│   └── CALL_001.mp3 ... CALL_025.mp3
├── cortex_code_skill/        # Cortex Code CLI skill for automated deployment
│   ├── telco-agent-builder.yaml  # Skill definition
│   └── README.md                  # Skill documentation
├── create_agent/             # Agent creation screenshots
│   ├── agent_button.png
│   ├── agent_questions.jpg
│   ├── all_3_agents.jpg
│   ├── CALL_transcripts_search.jpg
│   ├── create_agent_button.png
│   ├── create_agent.png
│   ├── describe_agent.png
│   ├── detailed_description.jpg
│   ├── intel002.jpg
│   ├── intelligence.jpg
│   ├── search_services.jpg
│   ├── test_agent.jpg
│   └── yaml_files.jpg
├── data/                     # CSV data files and PDFs
│   ├── *.csv                 # Network, customer, feedback data
│   └── pdfs/                 # 8 help documents
├── intelligence/             # Snowflake Intelligence screenshots
│   ├── agent_conversation_interface.png
│   ├── agent_testing_example_1.png
│   ├── agent_testing_example_2.png
│   ├── intelligence_settings_panel.png
│   └── intelligence_tab_navigation.png
├── logos/                    # NovaConnect branding
│   ├── image.png             # Full logo
│   └── image_cropped.png     # Compact logo
├── native_app_snowmail/      # SnowMail Native App files
├── Notebooks/                # 3 Snowflake notebooks
├── semantic_models/          # 3 YAML semantic model definitions
└── sql/                      # 6 deployment scripts
```

## Deployment Options

### Option 1: Snowsight UI (Default)
Deploy directly from GitHub using Snowflake's Git integration. See the main quickstart guide.

### Option 2: Cortex Code CLI (New!)
Use the **Telco Agent Builder** skill for automated, guided deployment:

```bash
# Install the skill
cp cortex_code_skill/telco-agent-builder.yaml ~/.cortex/skills/

# Launch Cortex Code and invoke
cortex
> Build the telco agent for me
```

See `cortex_code_skill/README.md` for detailed instructions.

## Image References in Markdown

All images are referenced in the guide using paths like:

```markdown
![Architecture](assets/architecture.png)
![Create Agent](assets/create_agent/create_agent_button.png)
![Intelligence Tab](assets/intelligence/intelligence_tab_navigation.png)
![NovaConnect Logo](assets/logos/image.png)
```

## Source

These assets were copied from:
- `/Users/boconnor/sfguide-telco/assets/` - Project deployment files
- `/Users/boconnor/build-an-ai-assistant-for-telco-using-aisql-and-snowflake-intelligence-2/dataops/event/homepage/docs/` - Documentation screenshots

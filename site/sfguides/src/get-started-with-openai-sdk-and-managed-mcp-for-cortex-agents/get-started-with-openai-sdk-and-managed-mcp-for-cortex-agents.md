author: James Cha-Earley
id: get-started-with-openai-sdk-and-managed-mcp-for-cortex-agents
summary: Connect OpenAI SDK to Snowflake Cortex Agents via Managed MCP for AI assistant development and data-driven chatbots.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions, snowflake-site:taxonomy/industry/retail-and-cpg, snowflake-site:taxonomy/snowflake-feature/ml-functions
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
language: en



# Get Started with OpenAI SDK and Managed MCP for Cortex Agents
<!-- ------------------------ -->
## Overview 


### Overview

Learn how to access Snowflake-hosted AI models and data from external applications using two different approaches: the OpenAI SDK for simple chat interfaces and LangGraph with Model Context Protocol (MCP) for custom agent workflows.

### What You Will Build

You'll build two complete applications that demonstrate external access patterns for Snowflake:

**App 1: Chat with GPT-5** - A Streamlit chat interface that uses the OpenAI SDK to access Snowflake-hosted models like GPT-5 and Claude.

**App 2: LangGraph MCP Agent** - A LangGraph agent that connects to Snowflake's MCP server, enabling AI-powered sales intelligence through conversation search, metrics analysis, and data queries.

### What You Will Learn

- How to use the OpenAI SDK to access Snowflake-hosted models (GPT-5, Claude)
- How to build custom agents with LangGraph and Model Context Protocol
- How to configure OAuth 2.0 authentication for MCP servers
- How to create and expose Cortex Agents via MCP
- How to query structured and unstructured data with AI

### Prerequisites

- [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN role
- Python 3.11 or higher installed
- Basic knowledge of SQL and Python

<!-- ------------------------ -->
## Snowflake Setup

### Download Project Files

Download the [get-started-with-openai-sdk-and-managed-mcp-for-cortex-agents.zip](https://github.com/Snowflake-Labs/sfquickstarts/raw/refs/heads/master/site/sfguides/src/get-started-with-openai-sdk-and-managed-mcp-for-cortex-agents/resources/get-started-with-openai-sdk-and-managed-mcp-for-cortex-agents.zip) file which contains:
- `setup.sql` - Complete Snowflake environment setup
- `mcp_setup.sql` - MCP server and OAuth configuration
- `openai_sdk.py` - Streamlit chat application using OpenAI SDK
- `agent.py` - LangGraph MCP agent application
- `requirements.txt` - Python dependencies
- `.env.example` - Environment configuration template

Extract the zip file to your preferred location.

### Run Complete Setup Script

1. Open a SQL worksheet in Snowsight
   * Navigate to **Projects** → **Worksheets** in the left navigation
   * Click **+ Worksheet** to create a new SQL worksheet
2. Open the `setup.sql` file from the extracted zip folder
3. Copy and paste the entire script into the worksheet
4. Run all statements by clicking **Run All** at the top right

> This enables `CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'` so you can access GPT-5 and all models regardless of your region.

**What the setup script does:**
- ✅ Enable Cortex AI + cross-region inference (GPT-5 access)
- ✅ Create database, schema, warehouse
- ✅ Create sample sales data (conversations + metrics)
- ✅ Create Cortex Search service (for semantic search)
- ✅ Create semantic view for Cortex Analyst
- ✅ Setup role with permissions

<!-- ------------------------ -->
## Create Cortex Agent via UI


### Build the Sales Intelligence Agent

Before setting up the MCP server, create the Cortex Agent through Snowsight's UI:

1. Navigate to **AI & ML** → **Agents** in the left navigation menu
2. Click **+ Agent** in the top right corner
3. Configure the agent with the following settings:

**Basic Information:**
- **Name:** `SALES_AGENT`
- **Database:** `SALES_INTELLIGENCE`
- **Schema:** `DATA`
- **Description:** `AI agent that can search sales conversations, analyze metrics, and query sales data`

**Add Tools (in this order):**

**Tool 1 - Cortex Search:**
- Click **+ Tool** → Select **Cortex Search**
- **Cortex Search Service:** `SALES_INTELLIGENCE.DATA.SALES_CONVERSATIONS_SEARCH`
- **Description:** `Search through sales conversation transcripts`

**Tool 2 - Cortex Analyst:**
- Click **+ Tool** → Select **Cortex Analyst**  
- **Semantic Model:** `SALES_INTELLIGENCE.DATA.SALES_METRICS_SEMANTIC_VIEW`
- **Description:** `Answer questions about sales metrics and performance`

4. Click **Create Agent**

> The Cortex Agent combines all three tools into a single intelligent assistant that can search conversations, analyze metrics, and query data.

### Test Your Agent

Before proceeding, verify the agent works:

1. In the Agent interface, try asking: `"What are the top performing sales reps?"`
2. The agent should use Cortex Analyst to query the metrics
3. Try: `"Find conversations about budget concerns"`
4. The agent should use Cortex Search to find relevant conversations

<!-- ------------------------ -->
## Setup MCP Server with OAuth

### Create OAuth Integration and MCP Server

Now that your Cortex Agent is created, set up the MCP server to expose it externally:

1. Open a new SQL worksheet in Snowsight
   * Navigate to **Projects** → **Worksheets**
   * Click **+ Worksheet**
2. Open the `mcp_setup.sql` file from the extracted zip folder
3. Copy and paste the entire script into the worksheet
4. Run all statements by clicking **Run All**

**What the MCP setup script does:**
- ✅ Creates OAuth security integration for authentication
- ✅ Generates OAuth client credentials (client ID and secret)
- ✅ Creates MCP server that exposes your Cortex Agent
- ✅ Grants necessary permissions to the role

### Save OAuth Credentials

After running the script, you'll see output from `SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('SALES_MCP_OAUTH');`:

```json
{
  "OAUTH_CLIENT_ID": "abc123...",
  "OAUTH_CLIENT_SECRET": "xyz789..."
}
```

> **CRITICAL:** Copy and save both the `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` - you'll need these for the agent.py application and cannot retrieve them later!

<!-- ------------------------ -->
## Generate Programmatic Access Token

You'll need a Programmatic Access Token (PAT) for both applications.

1. In Snowsight, navigate to Profile → Settings → Authentication
2. Click **Generate new token**
3. Select **Single Role** → `SALES_INTELLIGENCE_ROLE`
4. **Copy the token** (you won't be able to retrieve it later!)

> Store this token securely - you'll use it in both applications' configuration.

<!-- ------------------------ -->
## Setup Python Environment


### Install Dependencies

Navigate to the extracted project directory:

```bash
cd get-started-with-openai-sdk-and-managed-mcp-for-cortex-agents
```

Both applications share the same Python environment and configuration:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` and add all your credentials:

```env
# Snowflake Account URL (for App 1 - OpenAI SDK)
SNOWFLAKE_ACCOUNT_URL="https://<account-identifier>.snowflakecomputing.com"
SNOWFLAKE_PAT=your_token_from_earlier

# Snowflake Connection Details (for App 2 - LangGraph MCP)
SNOWFLAKE_ACCOUNT=your-account-identifier
SNOWFLAKE_WAREHOUSE=SALES_INTELLIGENCE_WH
SNOWFLAKE_DATABASE=SALES_INTELLIGENCE
SNOWFLAKE_SCHEMA=DATA
SNOWFLAKE_ROLE=SALES_INTELLIGENCE_ROLE

# OAuth Credentials (for App 2 - from SYSTEM$SHOW_OAUTH_CLIENT_SECRETS)
OAUTH_CLIENT_ID="Your Client ID Here"
OAUTH_CLIENT_SECRET="Your Client Secret Here"

# MCP Server Name (for App 2)
MCP_SERVER_NAME=SALES_INTELLIGENCE_MCP
```

> This single `.env` file contains configuration for both applications.

<!-- ------------------------ -->
## App 1: Chat with GPT-5 (openai_sdk.py)


### What You'll Build

A simple chat interface that uses the OpenAI SDK to access Snowflake-hosted models.

**Architecture:**
```
Streamlit App (openai_sdk.py) → OpenAI SDK → Snowflake Cortex API → GPT-5/Claude
```

### Run the App

Start the Streamlit application:

```bash
streamlit run openai_sdk.py
```

The app will open at `http://localhost:8501`

### Test the Application

Try these sample queries:

```
What is Snowflake Cortex?

Write a Python function for calculating Fibonacci numbers

Generate SQL to find top 5 customers by revenue
```

### Available Models

Select from the dropdown menu:
- `openai-gpt-5` - GPT-5 (cutting edge)
- `openai-gpt-5-mini` - Faster GPT-5 variant
- `openai-gpt-5-nano` - Most efficient GPT-5 variant
- `openai-gpt-5-chat` - GPT-5 optimized for chat
- `openai-gpt-4-1` - GPT-4.1
- `claude-sonnet-4-5` - Anthropic Claude Sonnet 4.5
- `claude-4-sonnet` - Claude 4 Sonnet

> **Success!** You're using GPT-5 hosted in Snowflake via the standard OpenAI SDK.

<!-- ------------------------ -->
## App 2: LangGraph MCP Agent (agent.py)


### What You'll Build

A LangGraph agent that connects to Snowflake's Cortex Agent via Model Context Protocol (MCP) with OAuth 2.0 authentication.

**Architecture:**
```
Your LangGraph Agent (agent.py - MCP Client)
    ↓ OAuth 2.0 + MCP Protocol
Snowflake MCP Server
    ↓
Cortex Agent (SALES_AGENT)
    ↓
├─ Cortex Search (semantic search over conversations)
├─ Cortex Analyst (natural language to SQL)
└─ SQL Execution (direct queries)
```

### Understanding the Application

The `agent.py` application demonstrates how to build a custom LangGraph agent that connects to Snowflake's MCP server. Key features:

**1. OAuth 2.0 Authentication Flow:**
- Opens browser for user authorization
- Starts local callback server on port 3000
- Exchanges authorization code for access token
- Handles token refresh automatically

**2. MCP Protocol Integration:**
- Initializes MCP session with Snowflake
- Discovers available tools from Cortex Agent
- Sends JSON-RPC requests to MCP server
- Maintains session state across interactions

**3. LangGraph Workflow:**
- Uses Snowflake Cortex (GPT-5) as the reasoning LLM
- Maintains conversation history and context
- Orchestrates tool calls based on user queries
- Provides structured responses with source attribution

**4. Interactive Chat Interface:**
- Command-line based conversation interface
- Built-in test mode for tool verification
- Real-time streaming of agent responses
- Error handling and troubleshooting

> The agent uses Snowflake Cortex (GPT-5) as its LLM, keeping all computation within Snowflake.

### Run the Agent

Start the interactive agent:

```bash
python agent.py
```

Your agent will:
1. Open browser for OAuth 2.0 authorization
2. Connect to Snowflake's MCP server
3. Discover available Cortex Agent tools
4. Initialize LangGraph workflow with Snowflake Cortex LLM
5. Start interactive session

### Test Queries

Try these sample queries:

**Search conversations:**
```
Find conversations about budget concerns
```

**Query metrics:**
```
What is the total deal value by product line?
```

**Combined analysis:**
```
Who are the top performing sales reps and what conversations did they have?
```

**Direct SQL:**
```
Show me all closed deals
```

> **Success!** You built a custom agent with OAuth 2.0 authentication using LangGraph and MCP.

<!-- ------------------------ -->
## Conclusion and Resources


### Conclusion

Congratulations! You've successfully built two applications that access Snowflake externally using different approaches. The `openai_sdk.py` application demonstrated using the OpenAI SDK for simple LLM inference, while the `agent.py` application showed how to connect your LangGraph agent to Snowflake's Cortex Agent via Model Context Protocol with OAuth 2.0 authentication.

These patterns enable you to:
- Leverage Snowflake-hosted AI models from any application
- Connect custom agents to Snowflake's Cortex Agent capabilities
- Secure external access with OAuth 2.0 authentication
- Combine semantic search, natural language to SQL, and direct queries
- Access models like GPT-5 through familiar APIs

### What You Learned

- How to configure Snowflake for external AI model access
- How to use the OpenAI SDK with Snowflake-hosted models
- How to set up OAuth 2.0 authentication for MCP servers
- How to create and expose Cortex Agents via MCP
- How to build LangGraph agents using Model Context Protocol
- How to implement semantic search over unstructured data
- How to enable natural language to SQL translation with Cortex Analyst

### Resources

**Documentation:**
- [Snowflake Cortex AI](hhttps://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [MCP Servers in Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Model Context Protocol](https://modelcontextprotocol.io)

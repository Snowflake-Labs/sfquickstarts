author: James Cha-Earley, Mubashir Masood, Daniel Silva
id: getting-started-with-cortex-agents
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Build an intelligent sales assistant using Snowflake Cortex Agents with Cortex Code CLI, combining Cortex Search and Analyst for both structured and unstructured data.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
open in snowflake link: https://app.snowflake.com/templates?template=get_started_with_cortex_agents&utm_source=build&utm_medium=templates&utm_campaign=guides&utm_content=nov25


# Getting Started with Cortex Agents

## Overview

Modern organizations face the challenge of managing two types of data: 
- Structured Data: Fixed schema that fits neatly into rows and columns (like metrics and KPIs)
- Unstructured Data: No fixed schema that can have a more complex format (such as customer conversations, emails, and meeting transcripts)

The ability to analyze and derive insights from both types of data is crucial for understanding customer needs, improving processes, and driving business growth. 

In this quickstart, you'll learn how to build an Intelligent Sales Assistant that leverages Snowflake's capabilities for analyzing both sales conversations and metrics. Using **Cortex Code CLI** — Snowflake's AI-powered command-line assistant — we'll create, configure, and test the agent entirely from the terminal.

### What is Snowflake Cortex AI?
Snowflake Cortex AI allows you to turn your conversations, documents and images into intelligent insights with AI next to your data. You can access industry-leading LLMs at scale directly in SQL or via APIs, analyze multimodal data and build agents — all within Snowflake's secure perimeter. The platform leverages powerful capabilities:

#### Cortex Analyst
Use AI to accurately convert natural language to SQL; Simple to use, cost-efficient to scale.
- Converts natural language questions into SQL queries
- Understands semantic models defined in YAML files
- Enables querying data without writing SQL manually
- Handles complex analytical questions about sales metrics
- Achieves over 90% accuracy through user-generated semantic models that capture domain knowledge and business context

#### Cortex Search
Find information by asking questions within a given set of documents with fully managed text embedding, hybrid search (semantic + keyword) and retrieval.
- Delivers best-in-class search performance through a hybrid approach combining semantic and keyword search
- Leverages an advanced embedding model (E5) to understand complex semantic relationships
- Enables searching across unstructured data with exceptional accuracy and speed
- Supports real-time indexing and querying of large-scale text data
- Returns contextually relevant results ranked by relevance scores

#### Cortex Agents
Orchestrate across both structured and unstructured data to retrieve and synthesize high-quality data insights. The Cortex Agents is a stateless REST API endpoint that:
- Seamlessly combines Cortex Search's hybrid search capabilities with Cortex Analyst's 90%+ accurate SQL generation
- Streamlines complex workflows by handling:
  - Context retrieval through semantic and keyword search
  - Natural language to SQL conversion via semantic models
  - LLM orchestration and prompt management
- Enhances response quality through:
  - In-line citations to source documents
  - Built-in answer abstaining for irrelevant questions
  - Multi-message conversation context management
- Optimizes application development with:
  - Single API call integration
  - Streamed responses for real-time interactions
  - Reduced latency through efficient orchestration

#### Cortex Code CLI
Cortex Code is Snowflake's AI-powered command-line interface for building, testing, and managing Snowflake resources conversationally. It includes built-in **skills** — structured workflows that guide you through complex tasks like agent creation, evaluation, and optimization — all from your terminal.

These capabilities work together to:
1. Search through sales conversations for relevant context
2. Go from Text to SQL to answer analytical questions
3. Combine structured and unstructured data analysis
4. Provide natural language interactions with your data

### What You'll Learn
- How to use Cortex Code CLI to set up a sales intelligence database
- How to create and configure Cortex Search services via SQL
- How to create a Cortex Agent using the Cortex Code `cortex-agent` skill
- How to test your agent directly from Cortex Code
- How to build a Streamlit interface for external access via the REST API

### What You'll Build
A full-stack application that enables users to:
- Search through sales conversations using semantic similarity
- Analyze sales metrics and patterns
- Ask questions about sales data and get AI-powered responses

### Prerequisites
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed
- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with a role with sufficient privileges to create databases, schemas, tables, and agents
- **Cortex Agents Access**: You will need access to Snowflake Cortex AI, including [**Cortex Agents**](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents), [**Cortex Search**](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview), and [**Cortex Analyst**](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) features.

## Install Cortex Code CLI

If you don't already have Cortex Code CLI installed, run the following in your terminal:

**macOS and Linux (including WSL):**
```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

After installation, verify it works and connect to your Snowflake account:
```bash
cortex
```

On first launch, Cortex Code will guide you through connecting to your Snowflake account. Ensure your connection uses a role with privileges to create databases, schemas, tables, stages, Cortex Search services, and agents.

## Setup Data

We'll use Cortex Code to execute the SQL that creates our sales intelligence database. Clone the companion repository first:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents.git
cd sfguide-getting-started-with-cortex-agents
```

Now launch Cortex Code from the repo directory:
```bash
cortex
```

**Step 1.** Ask Cortex Code to run the setup SQL. You can paste this prompt:

```
Run the SQL in setup.sql to create the sales intelligence database, tables, 
sample data, and Cortex Search service.
```

Cortex Code will execute each statement from [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/setup.sql), which:
- Creates the `SALES_INTELLIGENCE` database, `DATA` schema, and `SALES_INTELLIGENCE_WH` warehouse
- Creates tables for sales conversations and metrics
- Loads sample sales data
- Enables change tracking for real-time updates
- Configures the `SALES_CONVERSATION_SEARCH` Cortex Search service
- Creates a `MODELS` stage for semantic models
- Grants the necessary permissions

**Step 2.** Upload the semantic model. The Agent needs rules to interpret your structured data. This semantic model defines key business terms to ensure the Agent generates highly accurate SQL. Ask Cortex Code:

```
Upload sales_metrics_model.yaml to the @SALES_INTELLIGENCE.DATA.MODELS stage.
```

Cortex Code will run:
```sql
PUT file://sales_metrics_model.yaml @SALES_INTELLIGENCE.DATA.MODELS AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

## Create Agent

Now we'll use Cortex Code's built-in **cortex-agent** skill to create the Sales Intelligence Agent. This skill provides a guided, interactive workflow for agent creation.

**Step 1.** In Cortex Code, ask it to create the agent:

```
Create an agent called SALES_INTELLIGENCE_AGENT in SALES_INTELLIGENCE.DATA
```

Cortex Code will load the `cortex-agent` skill and walk you through the creation workflow interactively.

**Step 2.** When prompted for **administrative setup**, provide:
- **Database**: `SALES_INTELLIGENCE`
- **Schema**: `DATA`
- **Agent Name**: `SALES_INTELLIGENCE_AGENT`
- **Role**: `SALES_INTELLIGENCE_ROLE`

**Step 3.** When prompted for the agent's **purpose and requirements**, explain:

```
This agent orchestrates between sales data for analyzing sales conversations 
using Cortex Search and metrics using Cortex Analyst. It should answer questions 
about both structured sales metrics (revenue, deals, KPIs) and unstructured 
sales conversations (call transcripts, meeting notes).
```

**Step 4.** When prompted for **tools**, select the existing tools in the `SALES_INTELLIGENCE.DATA` schema:
- **Cortex Search Service**: `SALES_CONVERSATION_SEARCH` — for searching through sales conversation transcripts
- **Cortex Analyst (Semantic Model)**: `sales_metrics_model.yaml` on the `MODELS` stage — for querying structured sales metrics

**Step 5.** When prompted for **response instructions**, provide:

```
You are a specialized analytics assistant focused on providing concise responses 
about sales metrics and sales conversations. Your primary objectives are:

For structured data queries (metrics, KPIs, sales figures):
- Use the Cortex Analyst which is YAML-based functionality
- Provide direct, numerical answers with minimal explanation
- Format responses clearly with relevant units and time periods
- Only include essential context needed to understand the metric

For unstructured content from sales conversations:
- Utilize the Cortex Search service SALES_INTELLIGENCE.DATA.SALES_CONVERSATION_SEARCH
- Extract relevant information from conversations
- Summarize findings in brief, focused responses
- Maintain context from the original sales conversations

Operating guidelines:
- Always identify whether you're using Cortex Analyst or Cortex Search for each response
- Keep responses under 3-4 sentences when possible
- Present numerical data in a structured format
- Don't speculate beyond available data
```

**Step 6.** When prompted for **orchestration instructions**, provide:

```
If a query spans both structured and unstructured data, clearly separate the sources. 
For any query, first determine whether it requires:
(a) Structured data analysis → Use YAML/Cortex Analyst
(b) Report content/context → Use Cortex Search
(c) Both → Combine both services with clear source attribution

Please confirm which approach you'll use before providing each response.
```

**Step 7.** Cortex Code will create the agent via the REST API and verify its configuration. You can confirm the agent was created by asking:

```
List agents in SALES_INTELLIGENCE.DATA
```

**Step 8.** Grant access to the role. Ask Cortex Code:

```
Grant usage on agent SALES_INTELLIGENCE.DATA.SALES_INTELLIGENCE_AGENT to role SALES_INTELLIGENCE_ROLE
```

## Test the Agent

Now that your Agent is fully configured, let's test it directly from Cortex Code. Ask Cortex Code to chat with the agent:

```
Chat with agent SALES_INTELLIGENCE.DATA.SALES_INTELLIGENCE_AGENT
```

Cortex Code will load the chat-with-agent capability. Try these questions to test both structured and unstructured data:

**Test 1 — Structured data (Cortex Analyst):**
```
How many deals did Sarah Johnson win compared to deals she lost?
```
This question requires the Agent to run a SQL query against the sales metrics table using Cortex Analyst.

**Test 2 — Unstructured data (Cortex Search):**
```
Tell me about the call with Securebank?
```
This question requires the Agent to look up contextual information within the long text transcripts in the sales conversations table using Cortex Search.

**Test 3 — Combined:**
```
What were Sarah Johnson's total deal values, and what feedback came up in her conversations?
```
This tests the agent's ability to orchestrate across both tools.

## Agent REST API

In addition to testing in Cortex Code, you can integrate your Agent into custom applications. You can interact with the Agent by calling the Snowflake REST API at `/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT}:run`.

We've created a simple Streamlit application that interacts with the REST API [here](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/data_agent_demo.py). You can use it as a building block to build your own applications. 

Since this API call is made outside of Snowsight, we need a secure key to authenticate your identity and grant the application permission to run the Agent. This key is a Programmatic Access Token (PAT).

Let's run the Streamlit app and call the API locally:

**Step 1.** Create a [Programmatic Access Token](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens). You can do this via Cortex Code:

```
Create a programmatic access token for the SALES_INTELLIGENCE_ROLE role
```

Or manually in Snowsight: Click on your profile (bottom left corner) → Settings → Authentication → Under `Programmatic access tokens`, click `Generate new token` → Select `Single Role` and select `sales_intelligence_role`. Copy and save the token.

**Step 2.** Find your account URL. Ask Cortex Code:

```
What is my account URL?
```

Or in Snowsight: Click on your profile (bottom left corner) → Account → View account details.

**Step 3.** Set up and run the Streamlit app. In the cloned repository directory, run:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

CORTEX_AGENT_DEMO_PAT=<PAT> \
CORTEX_AGENT_DEMO_HOST=<ACCOUNT_URL> \
CORTEX_AGENT_DEMO_DATABASE="SALES_INTELLIGENCE" \
CORTEX_AGENT_DEMO_SCHEMA="DATA" \
CORTEX_AGENT_DEMO_AGENT="SALES_INTELLIGENCE_AGENT" \
streamlit run data_agent_demo.py
```

Replace `<PAT>` with the token from Step 1 and `<ACCOUNT_URL>` with your account URL from Step 2.

When you're done using the application, press `Ctrl+C` in the terminal to shut down the Streamlit server.

## Conclusion And Resources

Congratulations! You've successfully built an Intelligent Sales Assistant using Snowflake Cortex Agents — entirely from the command line with Cortex Code CLI. This application demonstrates the power of combining structured and unstructured data analysis through:
- Natural language interactions with your sales data
- Semantic search across sales conversations
- Automated SQL generation for analytics
- Interactive agent testing directly in the terminal
- External application access via the REST API with Streamlit

### What You Learned
- **Cortex Code CLI**: How to use Snowflake's AI-powered CLI to create and manage agents conversationally
- **Cortex Agents**: How to create and configure agents using the `cortex-agent` skill for combining search and analysis capabilities
- **Cortex Search**: How to leverage hybrid search combining semantic and keyword approaches for more accurate results
- **Cortex Analyst**: How to convert natural language to SQL using semantic models for high-accuracy analytics
- **Testing**: How to chat with your agent directly from Cortex Code to validate behavior
- **Integration**: How to connect external applications via the REST API using Streamlit

### Related Resources
- [Cortex Code CLI Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Cortex Agents Guide](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Search Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Snowflake Intelligence Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)

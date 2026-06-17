author: James Cha-Earley, Mubashir Masood, Daniel Silva
id: getting-started-with-cortex-agents-with-coco
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Build an intelligent sales assistant for Summit Gear Co. using Snowflake Cortex Agents with Snowflake CoCo CLI, combining Cortex Search and Analyst for both structured and unstructured data.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with Cortex Agents with Snowflake CoCo CLI

## Overview

Modern organizations face the challenge of managing two types of data: 
- Structured Data: Fixed schema that fits neatly into rows and columns (like metrics and KPIs)
- Unstructured Data: No fixed schema that can have a more complex format (such as customer conversations, emails, and meeting transcripts)

The ability to analyze and derive insights from both types of data is crucial for understanding customer needs, improving processes, and driving business growth. 

In this quickstart, you'll build an Intelligent Sales Assistant for **Summit Gear Co.** — a fictional outdoor adventure brand — that leverages Snowflake's capabilities for analyzing both sales conversations and deal metrics. Using **Snowflake CoCo CLI** (Snowflake's AI-powered command-line assistant), we'll generate sample data, create search and analytics tools, build an agent, and test it — all from the terminal.

### About Summit Gear Co.

Summit Gear Co. is an outdoor adventure brand selling boots, jackets, packs, and accessories to retail and e-commerce customers across four U.S. territories. Their sales team of 8 reps manages a pipeline of 200 deals and tracks customer interactions through recorded sales calls.

### What is Snowflake Cortex AI?
Snowflake Cortex AI allows you to turn your conversations, documents and images into intelligent insights with AI next to your data. The platform leverages powerful capabilities:

#### Cortex Analyst
Converts natural language questions into SQL queries using semantic models. Achieves over 90% accuracy through semantic views that capture domain knowledge and business context.

#### Cortex Search
Delivers hybrid search (semantic + keyword) over unstructured text data with fully managed embeddings and retrieval.

#### Cortex Agents
Orchestrates across both structured and unstructured data. A stateless REST API that combines Cortex Search and Cortex Analyst into a single interface with in-line citations, answer abstaining, and streamed responses.

#### Snowflake CoCo CLI
Snowflake's AI-powered command-line interface for building, testing, and managing Snowflake resources conversationally. Includes built-in **skills** for agent creation, semantic views, and more.

### What You'll Learn
- How to use Snowflake CoCo CLI to generate and load sample data
- How to create a Cortex Search service over conversation transcripts
- How to create a Semantic View for structured analytics
- How to build a Cortex Agent using the `cortex-agent` skill
- How to test your agent directly from Snowflake CoCo

### What You'll Build
An intelligent sales assistant that enables users to:
- Search through 150 sales conversation transcripts using semantic search
- Analyze 200 deals across territories, products, and reps
- Ask questions about sales data and get AI-powered responses combining both data types

### Prerequisites
- [Snowflake CoCo CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed
- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN access (or a role with privileges to create databases, schemas, tables, search services, semantic views, and agents)

## Install Snowflake CoCo CLI

If you don't already have Snowflake CoCo CLI installed, run the following in your terminal:

**macOS and Linux (including WSL):**
```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

After installation, launch Snowflake CoCo and connect to your Snowflake account:
```bash
cortex
```

On first launch, Snowflake CoCo will guide you through connecting to your Snowflake account.

## Generate Sample Data

We'll use Snowflake CoCo to generate the complete Summit Gear Co. dataset. Paste the following prompt into Snowflake CoCo:

```
Set up a sales database for Summit Gear Co., an outdoor adventure brand. 
Create database SUMMIT_GEAR_CO with schema SALES and a small warehouse called SUMMIT_GEAR_WH. 
Then generate and load synthetic data into two tables:

Table 1: DEALS (200 rows)
Columns: deal_id, customer_name, deal_value, close_date, sales_stage, win_status, sales_rep, territory, product_name, product_category
- 8 sales reps: Jake Morrison, Mia Chen, Lucas Rivera, Ava Patel, Ethan Brooks, Sophie Nakamura, Caleb Washington, Lily O'Brien
- 4 territories: Pacific Northwest, Mountain West, Northeast, Southeast
- 30 customers (outdoor retailers and e-commerce): REI, Backcountry, Moosejaw, Mountain Hardwear Outlet, Wild Earth, Campmor, Sierra Trading, Steep & Cheap, Eastern Mountain Sports, Outdoor Voices, Fjallraven Store, Sundance Outfitters, Trailhead Sports, Alpine Start, Summit Supply, Peak Performance Shop, Ridge & River Co, Basecamp Goods, Powder House, Timberline Traders, The North Wall, Canyon Creek Outfitters, Glacier Point Gear, High Camp Provisions, Ridgeline Sports, Evergreen Adventures, Crestline Outdoors, BlueSky Gear, TerraPeak Supply, Venture Out Co
- 12 products across 4 categories: Boots (Alpine Pro, Trail Runner, Winter Grip), Jackets (Summit Shell, Basecamp Down, Storm Guard), Packs (Expedition 65L, Day Hiker 30L, Ultra Light 20L), Accessories (Trekking Poles, Headlamp Pro, Thermal Flask)
- Sales stages: Closed Won, Lost, Pending, Negotiation, Discovery
- Deal values ranging from $5,000 to $150,000
- Close dates to our current date

Table 2: SALES_CONVERSATIONS (150 rows)
Columns: conversation_id, transcript_text, customer_name, deal_stage, sales_rep, territory, conversation_date, deal_value, product_name
- transcript_text should be realistic 3-5 paragraph sales call transcripts discussing products, customer objections, competition, seasonal demand, pricing negotiations, and inventory concerns
- Reference actual product names and customer names from the lists above
- Include variety: discovery calls, demos, negotiations, closing conversations, and follow-ups

After loading, enable change tracking on SALES_CONVERSATIONS.
```

Snowflake CoCo will generate the database, tables, and all sample data. This may take a few minutes as it creates realistic conversation transcripts. When complete, verify the data:

```
How many rows are in SUMMIT_GEAR_CO.SALES.DEALS and SUMMIT_GEAR_CO.SALES.SALES_CONVERSATIONS?
```

You should see 200 deals and 150 conversations.

## Create Cortex Search Service

Now we'll create a Cortex Search service to enable semantic search over the sales conversation transcripts. Paste this prompt:

```
Create a Cortex Search service called SALES_CALL_SEARCH on the transcript_text column in SUMMIT_GEAR_CO.SALES.SALES_CONVERSATIONS with attributes customer_name, deal_stage, sales_rep, territory, product_name using warehouse SUMMIT_GEAR_WH
```

Snowflake CoCo will look up the correct syntax and execute the DDL. The search service builds a semantic index over all 150 transcripts, enabling natural language queries against the conversation content.

## Create Semantic View

Next, we'll create a Semantic View over the structured deals table. This gives Cortex Analyst the context it needs to generate accurate SQL from natural language questions. Paste:

```
Create a semantic view for the SUMMIT_GEAR_CO.SALES.DEALS table
```

Snowflake CoCo will load the `semantic-view` skill, which:
1. Automatically generate a semantic view from the table metadata
2. Annotates columns with descriptions, sample values, and synonyms
3. Creates and deploys the semantic view in Snowflake

When prompted for options (like naming or file location), select the defaults.

## Create Agent

Now we'll combine both tools into a single Cortex Agent. Paste:

```
Create an agent called SUMMIT_GEAR_AGENT in SUMMIT_GEAR_CO.SALES that uses the SALES_CALL_SEARCH cortex search service and the deals semantic view
```

Snowflake CoCo will load the `cortex-agent` skill and:
1. Initialize an agent workspace
2. Build the agent specification with both tools
3. Generate orchestration instructions that route questions to the right tool
4. Deploy the agent via the REST API

When complete, the agent will have two tools:
- **Cortex Search** — for searching conversation transcripts
- **Cortex Analyst** — for querying structured deal metrics via text-to-SQL

## Test the Agent

Let's test the agent with questions that exercise both tools. Paste:

```
Chat with agent SUMMIT_GEAR_CO.SALES.SUMMIT_GEAR_AGENT and ask: What is our win rate by territory this quarter?
```

This routes through **Cortex Analyst**, generating SQL against the DEALS table to compute win rates grouped by territory.

Now test the search capability:

```
Ask the agent: What objections came up in recent calls about our Alpine Pro boots?
```

This routes through **Cortex Search**, finding relevant conversation transcripts that mention Alpine Pro boots and surfacing customer objections.

Try a combined question:

```
Ask the agent: How is Sophie Nakamura performing in the Northeast, and what themes come up in her sales calls?
```

This tests the agent's ability to orchestrate across both tools — pulling deal metrics AND searching her conversation transcripts.

## Conclusion And Resources

Congratulations! You've built an Intelligent Sales Assistant for Summit Gear Co. entirely from Snowflake CoCo CLI. The application demonstrates combining structured and unstructured data analysis through:
- AI-generated sample data loaded directly via conversational prompts
- Semantic search across 150 sales conversation transcripts
- Text-to-SQL over 200 deals via a semantic view
- A unified agent that orchestrates both capabilities

### What You Learned
- **Snowflake CoCo CLI**: How to use Snowflake's AI-powered CLI to generate data, create services, and build agents conversationally
- **Cortex Search**: How to create a search service for hybrid semantic + keyword search over text data
- **Semantic Views**: How to use `semantic-view` skill to automatically build semantic view from table metadata
- **Cortex Agents**: How to combine search and analyst tools into a single orchestrated agent
- **Testing**: How to chat with your agent directly from Snowflake CoCo to validate behavior

### Related Resources
- [Snowflake CoCo CLI Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Cortex Agents Guide](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Search Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Semantic Views Documentation](https://docs.snowflake.com/en/user-guide/views-semantic)

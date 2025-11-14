author: Reid Lewis, Cameron Shimmin
id: supply-chain-assistant-with-snowflake-intelligence
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search
language: English
summary: Build an intelligent supply chain assistant using Snowflake Intelligence and Cortex AI capabilities to help operations managers make data-driven inventory management decisions.
categories: data-science, data-engineering, featured
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

tags: Snowflake Intelligence, Cortex Analyst, Cortex Search, Cortex AI, Supply Chain, RAG, Semantic Models

# Supply Chain Assistant with Snowflake Intelligence

<!-- ------------------------ -->

## Overview

Modern supply chain operations face a critical challenge: efficiently managing raw material inventory across multiple manufacturing facilities. Operations managers must constantly balance inventory levels, deciding whether to transfer materials between plants with excess and shortage, or purchase new materials from suppliers. Making these decisions manually is time-consuming, error-prone, and often results in suboptimal cost outcomes.

This quickstart demonstrates how to build an intelligent supply chain assistant using Snowflake Intelligence and Cortex AI capabilities. By combining natural language querying with semantic search over both structured and unstructured data, you'll create a complete solution that helps operations managers make data-driven decisions about inventory management.

### The Problem

![Alt text](assets/problem.png)

Supply chain operations managers face daily challenges managing raw material inventory across manufacturing facilities:

* **Inventory Imbalances**: Some plants have excess raw materials while others face shortages, creating inefficiency
* **Complex Decision Making**: Determining whether to transfer materials between plants or purchase from suppliers requires analyzing multiple factors including material costs, transport costs, lead times, and safety stock levels
* **Manual Analysis**: Traditional approaches require running multiple reports, spreadsheet analysis, and manual cost comparisons
* **Time Sensitivity**: Inventory decisions need to be made quickly to avoid production delays or excess carrying costs

### The Solution

![Alt text](assets/solution.png)

This solution leverages Snowflake Intelligence and Cortex AI capabilities to create an intelligent assistant that:

1. **Answers Ad-Hoc Questions**: Operations managers can ask natural language questions about inventory levels, orders, shipments, and supplier information - the agent automatically converts questions to SQL and executes them
2. **Provides Contextual Information**: The assistant can search and retrieve relevant information from supply chain documentation using semantic search
3. **Intelligent Routing**: Automatically determines whether to query structured data (via Cortex Analyst) or search documents (via Cortex Search) based on the nature of the question
4. **Complex Analysis**: Handles sophisticated multi-table queries like identifying plants with low inventory alongside plants with excess inventory of the same materials, and comparing costs between suppliers and inter-plant transfers
5. **No-Code Agent Creation**: Build and deploy the entire solution using Snowflake Intelligence's visual interface without writing application code

### Prerequisites

* A Snowflake account with Cortex features enabled
* A Snowflake account login with ACCOUNTADMIN role OR a role that has the ability to create databases, schemas, tables, stages, and Cortex Search services
* Cortex Analyst, Cortex Search, and Snowflake Intelligence must be available in your Snowflake region
* Familiarity with Snowflake SQL and Snowsight interface

> aside negative
> **Note:** The custom tools for web search and web scraping require external integration access, which is not available on trial accounts. You can still complete this quickstart without these tools by skipping the custom tool setup steps.

### What You'll Learn

* How to model a multi-tier supply chain in Snowflake with proper relationships
* How to create semantic models for Cortex Analyst with dimensions, measures, and verified queries
* How to set up Cortex Search services on unstructured documents
* How to build comprehensive AI agents using Snowflake Intelligence
* How to combine multiple semantic models in a single agent for cross-domain analysis
* How to integrate custom tools (functions and stored procedures) into your agent
* How to enable web search and scraping capabilities within your AI assistant
* How to write effective tool descriptions and semantic models for accurate AI responses
* How to handle complex analytics questions that span multiple data sources

### What You'll Build

* A comprehensive supply chain database with 11 tables and realistic sample data
* Two semantic models: one for supply chain data and one for weather forecasts
* A Cortex Search service indexed on supply chain documentation
* A Snowflake Intelligence agent with 7 tools:
  * 2 Cortex Analyst tools (supply chain and weather data)
  * 1 Cortex Search tool (documentation)
  * 4 Custom tools (web search, web scraping, HTML newsletter generation, email sending)
* Complex verified queries for inventory analysis, cost comparison, and rebalancing opportunities
* A production-ready AI assistant that combines structured data, unstructured data, and external web sources

<!-- ------------------------ -->

## Snowflake Cortex and Intelligence Overview

### What is Snowflake Cortex?

![Alt Text](assets/cortex_image.png)

Snowflake Cortex provides fully managed Generative AI capabilities that run securely within your Snowflake environment and governance boundary. Key features include:

**Cortex Analyst** - Enables business users to ask questions about structured data in natural language. It uses a semantic model to understand your data and generates accurate SQL queries automatically.

![Alt Text](assets/building_the_semantic_layer.png)

**Cortex Search** - Provides easy-to-use semantic search over unstructured data. It handles document chunking, embedding generation, and retrieval, making it simple to implement RAG (Retrieval Augmented Generation) patterns.

**Cortex Agents** - Orchestrates multiple AI capabilities (like Analyst and Search) to intelligently route user queries to the appropriate service and synthesize responses.

![Alt Text](assets/what_is_cortex_agent.png)

Learn more about [Snowflake Cortex](https://www.snowflake.com/en/product/features/cortex/).

### What is Snowflake Intelligence?

Snowflake Intelligence is a unified experience for building and deploying AI agents within Snowflake. It provides:

* **No-Code Agent Builder**: Create agents that combine multiple tools (Cortex Analyst, Cortex Search, Custom Tools) without writing code
* **Integrated Tools**: Easily connect your semantic models and search services as agent capabilities
* **Conversational Interface**: Interact with your agent through a chat interface within Snowsight
* **Enterprise Ready**: Built on Snowflake's security and governance foundation

Learn more about [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence).

<!-- ------------------------ -->

## Setup Database and Load Data

In this step, you'll create the complete supply chain database infrastructure with all necessary tables, stages, and sample data.

1. Navigate to **Projects > Workspaces** to create a new private workspace in Snowsight
2. Add a new SQL file to your workspace
3. Import the **scripts/setup.sql** file from the quickstart repository
4. Click **Run All** to execute the entire script

This script will create:

* **Database**: `SUPPLY_CHAIN_ASSISTANT_DB` with schemas `ENTITIES` and `WEATHER`
* **Warehouse**: `SUPPLY_CHAIN_ASSISTANT_WH`
* **Supply Chain Tables**: Including suppliers, plants, inventory, customers, orders, shipments, and more
* **Internal Stages**: For storing PDFs and semantic model files
* **Sample Data**: Realistic data loaded via INSERT statements for all tables
* **Custom Functions and Procedures**: Web search, web scraping, email, and HTML newsletter generation capabilities

The database schema models a complete supply chain network with:

* Manufacturing plants located in multiple cities
* Suppliers providing raw materials
* Customers placing orders for finished goods
* Inventory tracking for both raw materials and finished goods
* Shipment records with tracking information
* Weather forecast data for plant locations

<!-- ------------------------ -->

## Upload Documents and Semantic Models

Within the first step, all objects have been created in `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES` database/schema. Now you'll upload the necessary files to the internal stages.

### Upload PDF Documents

1. Navigate to **Database Explorer** from the left side menu under **Horizon Catalog**
2. Navigate to the `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES` database/schema
3. Click on **Stages** to view available stages
4. Select the **SUPPLY_CHAIN_ASSISTANT_PDF_STAGE** stage
5. Click the **+ Files** button on the top right
6. Upload the **pdfs/Supply Chain Network Overview.pdf** file from the quickstart repository

### Upload Semantic Model Files

1. In the same Stages view, select the **SEMANTIC_MODELS_STAGE** stage
2. Click the **+ Files** button
3. Upload both semantic model files:
   * **scripts/semantic_models/SUPPLY_CHAIN_ASSISTANT_MODEL.yaml**
   * **scripts/semantic_models/WEATHER_FORECAST.yaml**

These semantic models define the structure, relationships, and verified queries that Cortex Analyst will use to answer natural language questions about your supply chain and weather data.

<!-- ------------------------ -->

## Create Cortex Search Service

You have two options to create the Cortex Search service that will enable semantic search over your supply chain documentation.

### Option A: Using SQL Script

1. In your workspace in Snowsight, add a new SQL file
2. Import the **scripts/configure_search_services.sql** file from the quickstart repository
3. Click **Run All** to execute the script

This script will:

* Parse PDFs using Cortex PARSE_DOCUMENT function
* Chunk the content into searchable segments using recursive character splitting
* Create the `PARSED_PDFS` table with presigned URLs for document access
* Create the `SUPPLY_CHAIN_INFO` Cortex Search service
* Set up a task to refresh presigned URLs daily (they expire after 7 days)

The search service will automatically index the parsed and chunked PDF content, making it available for semantic search queries.

### Option B: Manual Creation via Snowsight UI

If you prefer to create the search service manually through the UI:

#### Step 1: Prepare the Data (SQL Required)

Even with the UI approach, you'll need to run SQL to parse and prepare the documents. In your workspace, add a new SQL file and run:

```sql
USE SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES;
USE WAREHOUSE SUPPLY_CHAIN_ASSISTANT_WH;

-- Scale up warehouse for PDF parsing
ALTER WAREHOUSE SUPPLY_CHAIN_ASSISTANT_WH SET WAREHOUSE_SIZE = 'X-LARGE';

-- Parse PDFs
CREATE OR REPLACE TABLE PARSE_PDFS AS 
SELECT RELATIVE_PATH, 
       SNOWFLAKE.CORTEX.PARSE_DOCUMENT(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE, 
                                        RELATIVE_PATH, 
                                        {'mode':'LAYOUT'}) AS DATA
FROM DIRECTORY(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE);

-- Chunk and prepare content
CREATE OR REPLACE TABLE PARSED_PDFS AS (
    WITH TMP_PARSED AS (
        SELECT RELATIVE_PATH,
               SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(TO_VARIANT(DATA):content, 'MARKDOWN', 1800, 300) AS CHUNKS
        FROM PARSE_PDFS 
        WHERE TO_VARIANT(DATA):content IS NOT NULL
    )
    SELECT TO_VARCHAR(C.value) AS PAGE_CONTENT,
           REGEXP_REPLACE(RELATIVE_PATH, '\\.pdf$', '') AS TITLE,
           RELATIVE_PATH,
           GET_PRESIGNED_URL(@SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_ASSISTANT_PDF_STAGE, RELATIVE_PATH, 604800) AS PAGE_URL
    FROM TMP_PARSED P, LATERAL FLATTEN(INPUT => P.CHUNKS) C
);

-- Scale warehouse back down
ALTER WAREHOUSE SUPPLY_CHAIN_ASSISTANT_WH SET WAREHOUSE_SIZE = 'SMALL';
```

#### Step 2: Create Search Service via UI

1. In Snowsight, navigate to **AI & ML** > **Cortex Search** in the left navigation
2. Click **Create** button
3. Configure the search service:
   * **Database:** `SUPPLY_CHAIN_ASSISTANT_DB`
   * **Schema:** `ENTITIES`
   * **Name:** `SUPPLY_CHAIN_INFO`
   * **Source Table to be Indexed:** `PARSED_PDFS`
   * **Search Column:** Select `PAGE_CONTENT`
   * **Attributes**: Click **Next**
   * **Select Columns**: Click **Next**
   * **Target Lag:** `1 hour`
   * **Warehouse:** `SUPPLY_CHAIN_ASSISTANT_WH`
4. Click **Create Search Service**

The search service will begin indexing your parsed PDF content and will be ready to use once indexing completes.

<!-- ------------------------ -->

## Build Your Snowflake Intelligence Agent

Now that you have your semantic models and search service created, you can combine them into an intelligent agent using Snowflake Intelligence. The agent will intelligently route user questions to the appropriate tool based on the nature of the query.

### Create the Agent

1. Click on **Agents** within the **AI & ML** section on the left-hand navigation bar in Snowsight
2. Click **Create Agent** button
3. Name it **Supply_Chain_Agent**
4. Once created, navigate to **Tools** tab

### Add First Cortex Analyst Tool - Supply Chain Data

1. Click **+ Add** next to **Cortex Analyst**
2. Configure the tool:
   * Select the **Semantic model file** radio button
   * **Database** `SUPPLY_CHAIN_ASSISTANT_DB`
   * **Schema** `ENTITIES`
   * **Stage** `SEMANTIC_MODELS_STAGE`
   * Select `SUPPLY_CHAIN_ASSISTANT_MODEL.yaml`
   * **Name:** `SUPPLY_CHAIN_ASSISTANT_MODEL`
   * **Description:** *"Tool for analyzing supply chain data."*
   * **Warehouse:** Select **Custom** radio button then choose `SUPPLY_CHAIN_ASSISTANT_WH`
3. Click **Save**

### Add Second Cortex Analyst Tool - Weather Data

1. Click **+ Add** next to **Cortex Analyst**
2. Configure the tool:
   * Select the **Semantic model file** radio button
   * **Database** `SUPPLY_CHAIN_ASSISTANT_DB`
   * **Schema** `ENTITIES`
   * **Stage** `SEMANTIC_MODELS_STAGE`
   * Select `WEATHER_FORECAST.yaml`
   * **Name:** `WEATHER_FORECAST`
   * **Description:** *"Tool for analyzing supply chain data."*
   * **Warehouse:** Select **Custom** radio button then choose `SUPPLY_CHAIN_ASSISTANT_WH`
3. Click **Save**

### Add Cortex Search Tool

1. Click **+ Add** next to **Cortex Search Services**
2. Configure the tool:
   * **Database** `SUPPLY_CHAIN_ASSISTANT_DB`
   * **Schema** `ENTITIES`
   * **Search Service:** Select `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES.SUPPLY_CHAIN_INFO`
   * **Name:** `SUPPLY_CHAIN_INFO`
   * **Description:** *"Tool for searching supply chain unstructured data."*
   * **ID Column:** `PAGE_URL`
   * **Title Column:** `TITLE`
3. Click **Save**

### Add Custom Tools

> aside negative
> **Note:** The WEB_SEARCH and WEB_SCRAPE custom tools require external integration access, which is not available on trial accounts. If you're using a trial account, you can skip adding these two tools and still use the other agent capabilities.

For each of the following custom tools, click **+ Add** next to **Custom Tool**, then configure:

#### 1. CREATE_HTML_NEWSLETTER

* **Type:** procedure
* **Schema:** `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES`
* **Custom tool identifier:** `CREATE_HTML_NEWSLETTER_SP`
* **Name:** `CREATE_HTML_NEWSLETTER_SP`
* **Warehouse:** `SUPPLY_CHAIN_ASSISTANT_WH`
* **Description:** *"Create HTML newsletter from responses."*

#### 2. WEB_SEARCH

* **Type:** function
* **Schema:** `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES`
* **Custom tool identifier:** `WEB_SEARCH`
* **Name:** `WEB_SEARCH`
* **Warehouse:** `SUPPLY_CHAIN_ASSISTANT_WH`
* **Description:** *"Search the web using DuckDuckGo."*

#### 3. WEB_SCRAPE

* **Type:** function
* **Schema:** `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES`
* **Custom tool identifier:** `WEB_SCRAPE`
* **Name:** `WEB_SCRAPE`
* **Warehouse:** `SUPPLY_CHAIN_ASSISTANT_WH`
* **Description:** *"Web scraping and content extraction."*

#### 4. SEND_MAIL

> aside negative
> **Note:** This tool requires a verified email address in Snowflake to function properly.

* **Type:** procedure
* **Schema:** `SUPPLY_CHAIN_ASSISTANT_DB.ENTITIES`
* **Custom tool identifier:** `SEND_MAIL`
* **Name:** `SEND_MAIL`
* **Warehouse:** `SUPPLY_CHAIN_ASSISTANT_WH`
* **Description:** *"Send emails to recipients with HTML formatted content."*

### Save and Access Your Agent

1. Click **Save** to save your agent configuration
2. You can test the agent directly in the right-hand pane
3. Alternatively, navigate to **Snowflake Intelligence** in the left navigation AI & ML menu
4. Select your **Supply_Chain_Agent** from the dropdown
5. Start asking questions!

<!-- ------------------------ -->

## Test Your Agent with Example Questions

Start with simple questions and build up to more complex analysis. Notice how the agent automatically determines which tool to use based on your question!

![Alt text](assets/Agent.gif)

### Supply Chain Data Questions

* "Where do I have critical low inventory levels?"
* "Where do we have low inventory of rare earth materials?"
* "Compare the cost of transferring this inventory from a plant with excess inventory versus replenishing from a supplier."
* "For plants with low inventory of a raw material, compare the cost of replenishing from a supplier vs transferring from another plant with excess inventory."
* "What type of weather events might impact this transfer?"
* "Draft an executive summary email with this analysis, our options, and a recommendation."

> aside negative
> **Note:** Sending emails requires proper email integration and verified email addresses.

<!-- ------------------------ -->

## Conclusion and Resources

Congratulations! You've built a comprehensive Supply Chain Assistant powered by Snowflake Intelligence that combines multiple AI capabilities into a single, intelligent agent.

### What You Learned

* How to set up a comprehensive supply chain database with realistic sample data
* How to create semantic models for Cortex Analyst to enable natural language queries
* How to parse and chunk PDF documents for Cortex Search
* How to build Cortex Search services for semantic search over unstructured data
* How to create a Snowflake Intelligence agent that combines multiple tools
* How to integrate Cortex Analyst, Cortex Search, and custom tools into a single agent
* How to enable web search and scraping capabilities in your AI assistant
* How the agent intelligently routes questions to appropriate tools
* How to test complex queries that span multiple data sources and tool types

### What You Built

Your Supply Chain Assistant now includes:

* **Dual Analytics:** Query both supply chain operations and weather data using natural language
* **Semantic Search:** Access unstructured supply chain documentation through intelligent retrieval
* **Web Integration:** Search and scrape external information from the internet
* **Communication:** Generate HTML newsletters and send emails (with proper integration)
* **Intelligent Routing:** Automatic determination of which tool to use based on question context
* **Complex Analysis:** Handle sophisticated multi-domain queries spanning structured and unstructured data

### Next Steps and Extensions

You can extend this solution further by:

* **Adding More Semantic Models**: Create additional semantic models for other business domains (finance, HR, sales, etc.)
* **Integrating Additional Data Sources**: Connect to external APIs or databases
* **Creating Custom Tools**: Build specific tools for your unique business processes
* **Building Streamlit Applications**: Create custom UIs that interact with your agent programmatically
* **Adding More Documents**: Index additional PDF documents, user manuals, or policy documents
* **Implementing Advanced Analytics**: Add tools for predictive analytics, optimization, or machine learning inference
* **Setting Up Email Integration**: Configure email sending capabilities for automated reporting

### Related Resources

* [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
* [Snowflake Intelligence Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
* [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
* [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
* [Semantic Model Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/semantic-model-spec)
* [Snowflake Quickstarts](https://quickstarts.snowflake.com/)
* [Snowflake Community](https://community.snowflake.com/)

### GitHub Repository

Access the complete code, scripts, and files for this quickstart:

* [Supply Chain Assistant GitHub Repository](#)

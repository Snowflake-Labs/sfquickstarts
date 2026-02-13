author: Mani Srinivasan
id: build-a-due-diligence-agent-in-snowflake-with-tavily
categories: snowflake-site:taxonomy/solution-center/quickstart, snowflake-site:taxonomy/product/ai-and-ml
language: en
summary: Build a due diligence and investment research agent in Snowflake that enriches NYSE financial data with real-time web intelligence using Tavily.
environments: web
status: Draft
feedback link: https://github.com/manisrinivasan2k1/sfquickstarts/issues

<style>
  img {
    width: 800px;
    height: auto;
  }
</style>


## Overview

In this guide, you will build a real-time Due Diligence and Investment Research Agent in Snowflake that enhances structured NYSE financial data with live external intelligence powered by Tavily Web Search.

You will learn how to create a Financial Agent that analyzes ticker-level fundamentals stored in Snowflake and enriches them with timely insights from across the web. Using Tavily’s real-time search capabilities, the agent retrieves recent news, regulatory updates, litigation developments, executive changes, and emerging risk signals that may not yet be reflected in financial statements.

By combining trusted financial reference data in Snowflake with Tavily’s up-to-date web intelligence, the agent performs contextual risk and opportunity analysis that goes beyond static datasets. This approach helps reduce blind spots between earnings cycles and surfaces early warning signals for buy-side, private equity, and corporate development workflows.

By the end of this guide, you will have a working Financial Agent that demonstrates how Snowflake and Tavily together enable intelligent, real-time financial analysis across structured and unstructured data sources.

### Prerequisites

- A Snowflake account with appropriate access to databases, schemas, Agents, and Cortex Analyst capabilities.  
  https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides

- A Tavily API key to enable real-time web search. Tavily offers 1,000 free API credits per month with no credit card required.  
  https://tavily.com/

- Familiarity with Snowflake SQL and basic AI agent concepts.

### What You Will Build

- A structured equity reference dataset in Snowflake containing NYSE ticker-level fundamentals.
- A Financial Agent configured with an `Equity_Intelligence_Analysis_Tool` to evaluate structured financial data.
- A `Tavily_Web_Search_Tool` to retrieve real-time external intelligence, including regulatory updates, litigation signals, executive changes, and adverse media.
- An end-to-end due diligence workflow that combines structured financial analysis with live web intelligence to surface emerging risk and opportunity signals.

By the end of this guide, you will have a working Financial Agent capable of analyzing a company’s fundamentals and enriching that analysis with real-time developments from across the web.

### How You Can Use It

This Financial Agent can support a variety of investment and corporate analysis workflows, including:

- Buy-side due diligence prior to capital deployment.
- Private equity portfolio monitoring and risk assessment.
- Corporate development research for M&A evaluation.
- Continuous monitoring of leadership changes, regulatory exposure, and litigation risk.
- Identifying early warning signals between earnings cycles.

By combining trusted financial reference data in Snowflake with Tavily’s real-time web intelligence, you reduce blind spots in traditional analysis and enable faster, more informed decision-making across structured and unstructured data sources.

## Setup

### Configuring the Tavily Web Search API

Follow the steps below to configure Tavily Web Search within Snowflake.

1. **Install Tavily from Snowflake Marketplace**

   - Navigate to **Snowflake Marketplace**.
   - Search for **Tavily Search API**.
   - Click on 'Get' and follow the prompts to install it in your account.

   ![SnowFlake Tavily Marketplace Image](assets/snowflake_tavily_marketplace.png)

2. **Provide Your Tavily API Key**

   - After installation, click on 'Open'
     ![Tavily Search Open](assets/tavily_search_open.png)
     
   - When prompted, enter your **Tavily API key** to enable real-time search functionality (If you do not have an API key, you can create one at: https://tavily.com/).
     ![Tavily API Config](assets/tavily_api_config.png)

   - External API access must be enabled in the API configuration settings to allow outbound calls (You should find it below the API config field).

3. **Validate the Configuration**

   - Once the API key is configured, click on 'Open Worksheet'.
     ![Tavily Open Worksheet](assets/tavily_open_worksheet.png)
   - Then run the default query by selecting your appropriate warehouse and ensuring the Database is set to TAVILY_SEARCH_API and the Schema is set to TAVILY_SCHEMA, as shown below.
     ![Tavily API Run](assets/tavily_api_run.png)
   - You should see the query results displayed in the output console, similar to the example shown above. 

### Load Financial Tables into Snowflake
- Ensure your account privileges, region, and other required configurations are properly set before proceeding to avoid errors.
- Run the commands shown in the image below to create your database and schema, and set the appropriate context to ensure everything is configured correctly.
  ![Create Database Schema](assets/create_database_schema.png)
- You can verify that your new database and schema are set correctly by checking the context displayed in the top-right corner.
  ![Confirm Database Schema](assets/confirm_database_schema.png)
- Click the **“+”** icon, then select **Table → From File**.  
  ![Create Table from File](assets/create_table_from_file.png)
- After uploading your CSV file, ensure the correct **database** and **schema** are selected. Then click **+ Create New Table** and provide an appropriate table name of your choice.  
  ![upload CSV File](assets/upload_csv_file.png)

**Once the table is created, verify that it appears under the selected database and schema before proceeding. You can also preview the data to confirm it has been loaded correctly.**
![Database Explorer](assets/database_explorer.png)

### Create a Snowflake Agent with Tavily Search and Cortex Analyst Tools

1. In the Snowflake UI, navigate to the **AI & ML** tab and select **Agents**.  
   <insert_image_here_later>

2. Click **Create Agent**, then provide a name, description, and relevant example questions for your agent.  
   ![Create Agent Image](assets/create_agent.png)
3. Navigate to the **Tools** tab and add the **Cortex Analyst** tool.  
   ![Create Tool Image](assets/create_tool.png)
   Add the Cortex Analyst Tool  
   ![Cortex Analyst Tool Creation Image](assets/cortex_analyst_tool_creation.png)

5. Create a new custom tool for the **Tavily Search API** and configure its required parameters.  
   ![Tavily Search tool Creation](assets/tavily_search_tool_creation.png)

6. Click **Save Updates** to apply the updates.

7. Launch **Snowflake Intelligence** and verify that the agent has access to both configured tools.
   ![Snowflake Intelligence Tool Image](assets/snowflake_intelligence.png)

## Using Snowflake Intelligence with Tavily Web Search and Cortex Analyst

- You can now interact with Snowflake Intelligence by asking questions and observing how it leverages Tavily’s fast, efficient web search API alongside Cortex Analyst to provide real-time context for your Snowflake data.

### 1) Example 1: Regulatory & Valuation Risk Assessment (Nike)

**User Prompt:**

> “Given Nike's NYSE fundamentals and latest earnings data, are there any recent regulatory investigations, lawsuits, or enforcement actions in the last 30 days that could materially impact valuation?”

![Example 1 Output](assets/example1.png)

---

#### What Happens Behind the Scenes

1. **Snowflake Intelligence calls `tavily_web_search` first**
   - The agent identifies that the question requires recent, time-bound external developments.
   - It invokes the Tavily Web Search Tool to retrieve regulatory and legal news.
   - Tavily’s fast and efficient search ensures:
     - Up-to-date information (last 30 days)
     - Relevant filtering around investigations and enforcement
     - Reduced hallucination risk by grounding responses in real web sources

2. **Snowflake Intelligence then calls the Cortex Analyst tool**
   - The agent generates SQL dynamically to retrieve financial fundamentals.
   - It queries revenue, net income, and other structured data from your Snowflake database.
   - The SQL execution establishes the financial baseline.

![Reasoning Trace 1](assets/reasoning_trace1.png)

3. **Synthesis**
   - External regulatory findings (Tavily)
   - Structured financial metrics (Cortex Analyst SQL)
   - Combined valuation-aware reasoning

Without Tavily, the agent would lack fresh regulatory intelligence.  
Without Cortex Analyst, it could not contextualize events against actual financial scale.

---

### 2) Example 2: Commodity Sensitivity & Market Developments (Exxon Mobil)

**User Prompt:**

> “Based on Exxon Mobil’s fundamentals, analyze its revenue scale and assess whether recent geopolitical or OPEC-related developments could impact forward cash flow.”

![Example 2 Output](assets/example2.png)

---

#### Step-by-Step Orchestration

1. **Cortex Analyst Tool is invoked**
   - The agent dynamically generates SQL to query revenue and net income.
   - It establishes a financial baseline directly from Snowflake tables.
   - SQL execution is visible in the reasoning trace.

![Reasoning Trace 2](assets/reasoning_trace_2.png)

2. **`tavily_web_search` is triggered**
   - The agent retrieves recent OPEC decisions and geopolitical developments.
   - Tavily delivers high-signal, relevant results in real time.

3. **Combined Financial + Market Intelligence**
   - Financial exposure (from structured data)
   - Market catalysts (from Tavily search)
   - Synthesized forward cash flow implications

---

### Why Tavily Strengthens the Financial Agent

Tavily’s fast and efficient search:

- Retrieves high-signal, recent developments
- Anchors analysis in real-world, time-sensitive events
- Reduces speculative or generic responses
- Grounds the Financial Agent’s reasoning with external validation

This transforms Snowflake Intelligence from a SQL-driven assistant into a contextual financial reasoning engine.

---

## Conclusion

Congratulations on completing this exercise!

By integrating Tavily Web Search with Cortex Analyst, Snowflake Intelligence becomes a multi-step reasoning system capable of:

- Generating SQL dynamically through Cortex Analyst
- Executing structured financial analysis directly in Snowflake
- Retrieving real-time external intelligence via Tavily
- Synthesizing both structured and unstructured data into valuation-aware insights

The Financial Agent moves beyond simple querying and becomes a grounded, decision-support system for due diligence and investment research.

---

## What You've Learned

- How Snowflake Intelligence orchestrates both Tavily Web Search and Cortex Analyst tools
- How Cortex Analyst dynamically generates SQL to query financial tables
- How Tavily provides real-time, high-quality external intelligence
- How combining structured financial data with live market signals improves analytical depth
- How to build a Financial Agent capable of contextual, risk-aware financial reasoning

You have now implemented a Financial Agent that bridges structured Snowflake data with live external intelligence — enabling real-time, grounded financial analysis.
```

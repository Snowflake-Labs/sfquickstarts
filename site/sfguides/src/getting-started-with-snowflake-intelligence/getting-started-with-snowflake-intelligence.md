id:  getting-started-with-snowflake-intelligence
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: This guide outlines the process for getting started with Snowflake CoWork, the personal work agent that brings deep analysis and automation to every knowledge worker.
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
authors: Dash Desai
open in snowflake link: https://app.snowflake.com/templates?template=get_started_with_snowflake_intelligence&utm_source=build&utm_medium=templates&utm_campaign=guides&utm_content=nov25


# Getting Started with Snowflake CoWork

## Overview

[Snowflake CoWork](https://www.snowflake.com/en/product/snowflake-cowork/) is the personal work agent that brings deep analysis and automation to every knowledge worker. It acts across the systems users already rely on, with built-in RBAC and governance for secure and trusted answers, all inside Snowflake's perimeter. It delivers governed, curated dashboards and shareable artifacts so insights become reusable team knowledge, turning everyday work into repeatable processes and enabling teams to share and build on each other’s insights.

Unlike standalone AI tools, CoWork is grounded in your enterprise data from day one, combining AI reasoning with Snowflake's governance layer so every answer is trusted, cited, and secure.

By the end of this guide, you will have a working Cortex Agent connected to CoWork that can answer business questions across structured sales data and unstructured support tickets, generate charts, and take actions like sending summary emails.

### Use Cases

CoWork moves teams from reactive Q&A to proactive, context-aware intelligence that drives decisions and execution across various business use cases:

* **Sales performance analysis:** Sales managers can quickly get answers to complex questions like "What were my top product sales in the West region last quarter, and why did product X outperform product Y?" while analysts can understand critical trends like "Why are support tickets increasing?" by reasoning across diverse data sources.

* **Enhanced research & financial insights:** Enrich internal data with external sources via Cortex Knowledge Extensions, allowing financial analysts to combine portfolio performance with market news, or product managers to analyze customer feedback alongside industry reports for deeper context.

* **Self-service data exploration:** Enable all business users to independently explore data and get immediate answers to complex questions, reducing reliance on data teams and accelerating decisions across the organization.

### Prerequisites

* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed

* Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with the ACCOUNTADMIN role in a region where you have access to the supported models. Otherwise, you will need to enable [cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference/?utm_source=snowflake-devrel&utm_medium=developer-guides) (see the optional statement at the end of `setup.sql`).


<!-- ------------------------ -->
## Setup


### Create database, schema, tables and load data from AWS S3

* Clone [GitHub repository](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence).

* In Snowsight, on the left hand navigation menu, select **Projects** >> **Workspaces**, click on **+ Add new** >> **SQL File**, and copy the contents of [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence/blob/main/setup.sql) into it.

* Execute all statements in order from top to bottom. Among other things, the script creates the Snowflake CoWork object (`SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT`), grants the **SNOWFLAKE_INTELLIGENCE_ADMIN** role usage on it, and creates the **SEND_EMAIL** stored procedure used later as a custom tool.


> NOTE: Switch your user role in Snowsight to **SNOWFLAKE_INTELLIGENCE_ADMIN**.

### Cortex Analyst

This tool enables the agent to query structured data in Snowflake by generating SQL. It relies on semantic views, which are mappings between business concepts (e.g., "product name," "sales") and the underlying tables and columns in your Snowflake account. This abstraction helps the LLM understand how to query your data effectively, even if your tables have complex or arbitrary naming conventions.

* In Snowsight, on the left hand navigation menu, select <a href="https://app.snowflake.com/_deeplink/#/cortex/analyst?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-getting-started-with-si&utm_cta=developer-guides-deeplink" class="_deeplink">**AI & ML** >> **Analyst**</a>
* On the top right, confirm that the role is set to **SNOWFLAKE_INTELLIGENCE_ADMIN**, click on **Create new** down arrow and select **Create new Semantic View**
    - Location: **DASH_DB_SI.RETAIL**
    - Name: SALES_AND_MARKETING_DATA
    - Description: *Semantic view for sales and marketing data analysis across campaigns, products, transactions, and social media engagement.*
* Click on **Next**, then **Skip** (no example SQL queries needed)
* Select the **DASH_DB_SI.RETAIL** schema and the **MARKETING_CAMPAIGN_METRICS**, **PRODUCTS**, **SALES**, and **SOCIAL_MEDIA** tables, then click on **Next**
* Select all available columns, then click on **Next**
* Review and accept the suggested relationships and metrics, then click on **Save** and wait for the semantic view to be created

### Cortex Search

This tool allows the agent to search and retrieve information from unstructured text data, such as customer support tickets, Slack conversations, or contracts. It leverages Cortex Search to index and query these text "chunks," enabling the agent to perform [Retrieval Augmented Generation](https://www.snowflake.com/en/fundamentals/rag/) (RAG).

* In Snowsight, on the left hand navigation menu, select <a href="https://app.snowflake.com/_deeplink/#/cortex/search?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-getting-started-with-si&utm_cta=developer-guides-deeplink" class="_deeplink">**AI & ML** >> **Search**</a> 
* On the top right, click on **Create**
    - Role and Warehouse: **SNOWFLAKE_INTELLIGENCE_ADMIN** | **DASH_WH_SI**
    - Database and Schema: **DASH_DB_SI.RETAIL**
    - Name: Support_Cases
    - Select data to be indexed: select SUPPORT_CASES table
    - Select a search column: select TRANSCRIPT
    - Select attribute column(s): select TITLE, PRODUCT 
    - Select columns to include in the service: Select all
    - Configure your Search Service: Keep default values **except** select **DASH_WH_SI** for "Warehouse for indexing" (Choose COMPUTE_WH if DASH_WH_SI is not available)

#### OPTIONAL: Aggregated Support Cases using Cortex AISQL

Instead of creating a Cortex Search service for individual support cases, you may create one on aggregated support cases. This is ideal if you want the Agent to answer questions based on high-level trends rather than individual ticket details. It really depends on your use case, but it's shown here as an example using Cortex AISQL.

Execute the following SQL statements that use [AI_AGG()](https://docs.snowflake.com/en/sql-reference/functions/ai_agg/) to create aggregated support cases summary which is inserted into a new table **AGGREGATED_SUPPORT_CASES_SUMMARY**. Then, a Cortex Search service is created on that table.

```sql
-- Use AI_AGG to aggregate support cases summary and insert into a new table AGGREGATED_SUPPORT_CASES_SUMMARY

use database DASH_DB_SI;
use schema RETAIL;

create or replace table AGGREGATED_SUPPORT_CASES_SUMMARY as
 select 
    ai_agg(transcript,'Read and analyze all support cases to provide a long-form text summary in no less than 5000 words.') as summary
    from support_cases;

-- Create Cortex Search service on table AGGREGATED_SUPPORT_CASES_SUMMARY

create or replace cortex search service AGGREGATED_SUPPORT_CASES 
on summary 
attributes
  summary 
warehouse = dash_wh_si 
embedding_model = 'snowflake-arctic-embed-m-v1.5' 
target_lag = '1 hour' 
initialize=on_schedule 
as (
  select
    summary
  from AGGREGATED_SUPPORT_CASES_SUMMARY
);
```
> NOTE: These SQL statements may take 3-5 minutes to run.


### Create Agent

An agent is an intelligent entity within Snowflake CoWork that acts on behalf of the user. Agents are configured with specific tools and orchestration logic to answer questions and perform tasks on top of your data. 

Note that you can create multiple agents for various use cases and/or business teams in your organization. 

* In Snowsight, on the left hand navigation menu, select <a href="https://app.snowflake.com/_deeplink/#/agents?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-getting-started-with-si&utm_cta=developer-guides-deeplink" class="_deeplink">**AI & ML** >> **Agents**</a> 
* On the top right, click on **Create agent**
     - Schema: **SNOWFLAKE_INTELLIGENCE.AGENTS**
     - Agent object name: Sales_AI
     - Display name: Sales//AI
* Select the newly created **Sales_AI** agent and click on **Edit** on the top right corner and make the following updates.

### Add Instructions

Add the following starter questions under **Example questions**:

- Show me the trend of sales by product category between June and August
- What issues are reported with jackets recently in customer support tickets?
- Why did sales of Fitness Wear grow so much in July?

### Add Tools

Tools are the capabilities an agent can use to accomplish a task. Think of them as the agent's skillset and note that you can add one or more of each of the following tools.

* Tools
  - **Cortex Analyst**
    - Click on **+ Add**
        - Add: Semantic view **DASH_DB_SI.RETAIL** >> **SALES_AND_MARKETING_DATA**
        - Name: Sales_And_Marketing_Data

        - Description: *The Sales and Marketing Data semantic view in DASH_DB_SI.RETAIL schema provides a complete view of retail business performance by connecting marketing campaigns, product information, sales data, and social media engagement. The view enables tracking of marketing campaign effectiveness through clicks and impressions, while linking to actual sales performance across different regions. Social media engagement is monitored through influencer activities and mentions, with all data connected through product categories and IDs. The temporal alignment across tables allows for comprehensive analysis of marketing impact on sales performance and social media engagement over time.*

        - Warehouse: Custom >> **DASH_WH_SI**
        - Query timeout (seconds): 60

  - **Cortex Search Services**
    - Click on **+ Add**

        - Search service: **DASH_DB_SI.RETAIL** >> **Support_Cases**
        - ID column: ID
        - Title column: TITLE
        - Name: Support_Cases

    >  NOTE: If you optionally created AGGREGATED_SUPPORT_CASES Cortex Search service, you may add it here as well.

  - **Custom tools**
    - Click on **+ Add**

      - Resource type: procedure
      - Database & Schema: **DASH_DB_SI.RETAIL**
      - Custom tool identifier: **DASH_DB_SI.RETAIL.SEND_EMAIL()**
      - Name: Send_Email
      - Warehouse: **DASH_WH_SI**
      - Parameter: body
        - Description: *Use HTML-Syntax for this. If the content you get is in markdown, translate it to HTML. If body is not provided, summarize the last question and use that as content for the email.*
      - Parameter: recipient_email
        - Description: *If the email is not provided, send it to the current user's email address.*
      - Parameter: subject
        - Description: *If the subject is not provided, use "Snowflake CoWork".*
      

* Orchestration Instructions: *Whenever you can answer visually with a chart, always choose to generate a chart even if the user didn't specify to.*

* Access: SNOWFLAKE_INTELLIGENCE_ADMIN


> NOTE: On the top right corner, click on **Save** to save the newly updated **Sales_AI** agent.

<!-- ------------------------ -->
## Snowflake CoWork



> PREREQUISITE: Successful completion of steps outlined under **Setup**.

Open <a href="https://ai.snowflake.com/_deeplink/#/ai?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-getting-started-with-si&utm_cta=developer-guides-deeplink" class="_deeplink">Snowflake CoWork</a> and make sure you're signed into the right account. If you're not sure, click on your name in the bottom left >> **Sign out** and sign back in. Also note that your role should be set to **SNOWFLAKE_INTELLIGENCE_ADMIN**, the warehouse should be set to **DASH_WH_SI**, and your agent should be set to Sales//AI.

Now, let's ask the following questions. Answers are generated live, so wording, numbers, and chart styles will vary from run to run. The notes under each question describe what to look for.

### Q1. *Show me the trend of sales by product category between June and August.*

**What to expect:** The agent uses the **Sales_And_Marketing_Data** tool to query the semantic view and returns a chart of sales by product category for June through August. Fitness Wear stands out with a sharp jump in July (roughly three times June's sales).

___

### Q2. *What issues are reported with jackets recently in customer support tickets?*

**What to expect:** The agent uses the **Support_Cases** search tool and summarizes the matching tickets. They point to one recurring problem: ThermoJacket Pro jackets tearing along the seams, which customers describe as a manufacturing defect. The answer cites the tickets it used.

___

### Q3. *Why did sales of Fitness Wear grow so much in July?*

**What to expect:** The agent combines sales, marketing, and social media data to explain the spike. The main driver it finds is influencer activity: Fitness Wear social mentions rose several-fold in July, led by an influencer who posted about the category only that month. Expect a chart and a short explanation of how each data source supports the conclusion.

### Q4. *Send a summary email*

*NOTE: The agent calls the **Send_Email** tool and confirms that the email was sent. Check your inbox for the summary email, which goes to the current user's email address unless you specify another one.*

### Q5. *Send me this summary every Monday morning*

This turns a one-time answer into an [Automation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork/automations) that re-runs the question on fresh data and emails you the results. You can review and manage it from the **Automations** tab.
___

### Other Questions
Your Agent is configured to handle a variety of complex queries that blend various types of data. Try these examples to further test the Agent:

#### *Which product categories perform best on social media?*

#### *What's the relationship between social media mentions and sales?*

#### *How do different regions respond to marketing campaigns?*

### Go Further

CoWork includes more capabilities you can try with the same agent:

* **Deep Research:** Select **+** in the message bar >> **Deep Research** and ask an open-ended question like *"Which product categories show the strongest link between marketing spend, social mentions, and sales, and why?"* to get a multi-step, cited report.
* **Artifacts:** Save charts and tables from any answer so you can share and revisit them without regenerating.
* **User skills:** Codify a repeatable workflow once and invoke it with **/**.
* **Document generation:** Turn analysis into PDF, Word, PowerPoint, or HTML reports. This requires adding the code execution tool to the agent.
* **File upload:** Attach a CSV, PDF, or image directly in the chat for additional context.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built a Cortex Agent for Snowflake CoWork that can respond to questions by reasoning over both structured and unstructured data.

### What You Learned

You've learned how to create the fundamental building blocks for Snowflake CoWork. This Cortex Agent is now a powerful asset, capable of combining deep analysis and automated tasks right from a single chat interface. 

### Related Resources

- [GitHub Repository](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence)
- [Snowflake CoWork Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork)
- [Overview of Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- [Best Practices to Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/)



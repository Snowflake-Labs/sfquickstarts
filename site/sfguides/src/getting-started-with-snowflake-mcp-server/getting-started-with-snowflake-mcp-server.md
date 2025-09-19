id: getting-started-with-snowflake-mcp-server
summary: This guide outlines the process for getting started with Snowflake MCP Server.
categories: featured,getting-started,data-science-&-ml,app-development
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Data-Science-&-Ai, Featured
authors: Dash Desai

# Getting Started with Snowflake MCP Server
<!-- ------------------------ -->

## Overview

Duration: 4

Snowflake MCP Server offers a powerful solution for organizations to access and activate their vast data. It addresses common challenges for business users struggling to get timely answers from scattered data, and for data teams overwhelmed by ad hoc requests. By using AI agents, it enables users to securely talk with their data, derive deeper insights, and initiate actions, all from a unified, easy-to-use interface. This transforms how businesses operate by bridging the gap between data and actionable insights.

*NOTE: Snowflake MCP Server is in Public Preview as of October 2025.*

### Prerequisites

* Access to a [Snowflake account](https://signup.snowflake.com/) with ACCOUNTADMIN role.

### What You Will Learn

How to create building blocks to create and interact with Snowflake MCP Server that can intelligently respond to questions by reasoning over both structured and unstructured data.

### What You Will Build

A Snowflake MCP Server that can intelligently respond to questions by reasoning over both structured and unstructured data.

<!-- ------------------------ -->
## Setup

Duration: 20 

### Create database, schema, tables and load data from AWS S3

* Clone [GitHub repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server).

* In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server/blob/main/setup.sql) to execute all statements in order from top to bottom.

### Cortex Analyst

This tool enables the agent to query structured data in Snowflake by generating SQL. It relies on semantic views, which are mappings between business concepts (e.g., "product name," "sales") and the underlying tables and columns in your Snowflake account. This abstraction helps the LLM understand how to query your data effectively, even if your tables have complex or arbitrary naming conventions.

* In Snowsight, on the left hand navigation menu, select [**AI & ML** >> **Cortex Analyst**](https://app.snowflake.com/_deeplink/#/cortex/analyst?utm_source=quickstart&utm_medium=quickstart&utm_campaign=-us-en-all&utm_content=app-getting-started-with-snowflake-mcp-server)
* On the top right, click on **Create new model** down arrow and select **Upload your YAML file** 
* Upload [financial_services_analytics.yaml](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server/blob/main/financial_services_analytics.yaml) | Select database, schema, and stage: **DASH_MCP_DB.DATA** >> **SEMANTIC_MODELS** 
* On the top right, click on **Save** 

### Cortex Search

This tool allows the agent to search and retrieve information from unstructured text data, such as customer support tickets, Slack conversations, or contracts. It leverages Cortex Search to index and query these text "chunks," enabling the agent to perform Retrieval Augmented Generation (RAG).

* In Snowsight, on the left hand navigation menu, select [**AI & ML** >> **Cortex Search**](https://app.snowflake.com/_deeplink/#/cortex/search?utm_source=quickstart&utm_medium=quickstart&utm_campaign=-us-en-all&utm_content=app-getting-started-with-snowflake-mcp-server) 
* On the top right, click on **Create**
    - Role and Warehouse: **ACCOUNTADMIN** | **DASH_WH_S**
    - Database and Schema: **DASH_MCP_DB.DATA**
    - Name: Support_Cases
    - Select data to be indexed: select FACT_SUPPORT_CASES table
    - Select a search column: select DESCRIPTION
    - Select attribute column(s): select STATUS, PRIORITY, CATEGORY, SUBCATEGORY, SATISFACTION_SCORE 
    - Select columns to include in the service: Select all
    - Configure your Search Service: Keep default values **except** select **DASH_WH_S** for "Warehouse for indexing"

<!-- ------------------------ -->
## Snowflake MCP Server

Duration: 5

> aside negative
> PREREQUISITE: Successful completion of steps outlined under **Setup**.



<!-- ------------------------ -->
## Conclusion And Resources

Duration: 1

Congratulations! You've successfully created a Snowflake MCP Server that can intelligently respond to questions by reasoning over both structured and unstructured data

### What You Learned

You've learned how to create building blocks for creating a Snowflake MCP Server that can intelligently respond to questions by reasoning over both structured and unstructured data.

### Related Resources

- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server)
- [Snowflake MCP Server Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-mcp-server)



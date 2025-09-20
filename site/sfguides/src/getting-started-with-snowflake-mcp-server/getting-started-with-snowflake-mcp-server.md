id: getting-started-with-snowflake-mcp-server
summary: This guide outlines the process for getting started with Snowflake MCP Server.
categories: featured,getting-started,data-science-&-ml,app-development
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Data-Science-&-Ai, Featured
authors: Dash Desai

# Getting Started with Managed Snowflake MCP Server
<!-- ------------------------ -->

## Overview

Duration: 4

The Snowflake MCP Server allows AI agents to securely retrieve data from Snowflake accounts without needing to deploy separate infrastructure. MCP clients discover and invoke tools, and retrieve data required for the application. The Snowflake MCP Server includes Cortex Analyst and Cortex Search as tools on the standards-based interface. It is now available with Model Context Protocol (MCP) so that AI Agents can discover and invoke tools (Cortex Analyst, Cortex Search) via a unified and standard based interface.

**Top 3 Benefits**

* Governed By Design: Enforce the same trusted governance policies, from role-based access to masking, for the MCP server as you do for your data.
* Reduced Integration: With the MCP Server, integration happens once. Any compatible agent can then connect without new development, accelerating adoption and reducing maintenance costs.
* Extensible Framework: Provide agents with out-of-the-box secure access to structured and unstructured data. You can refine the tools to improve how agents interact with your data.

**Why It Matters**

MCP Server on Snowflake simplifies the application architecture and eliminates the need for custom integrations. Enterprises can expedite delivery of generative AI applications with richer insights on a standards based architecture and a robust governance model with the Snowflake AI data cloud.

*NOTE: Snowflake MCP Server is in Public Preview as of October 2025.*

![MCP](assets/mcp.png)

### Prerequisites

* Access to a Snowflake account with ACCOUNTADMIN role. If you do not have access to an account, create a [free Snowflake trial account](https://signup.snowflake.com/?utm_cta=quickstarts_).
* Access to [Cursor](https://cursor.com/).

### What You Will Learn

- How to create building blocks for Snowflake MCP Server that can intelligently respond to questions by reasoning over data
- How to configure Cursor to interact with Snowflake MCP Server

### What You Will Build

A Snowflake MCP Server that intelligently responds to questions by reasoning over data from within Cursor.

<!-- ------------------------ -->
## Setup

Duration: 10

### Create database, schema, tables and load data from AWS S3

* Clone [GitHub repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server).

* In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server/blob/main/setup.sql) to execute all statements in order from top to bottom.

### Personal Access Token

Create a [Personal Access Token (PAT)](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) **for your role** and make a note/local copy of it. (You will need to paste it later.)

### Cortex Search

This tool allows the agent to search and retrieve information from unstructured text data, such as customer support tickets, Slack conversations, or contracts. It leverages Cortex Search to index and query these text "chunks," enabling the agent to perform Retrieval Augmented Generation (RAG).

* In Snowsight, on the left hand navigation menu, select [**AI & ML** >> **Cortex Search**](https://app.snowflake.com/_deeplink/#/cortex/search?utm_source=quickstart&utm_medium=quickstart&utm_campaign=-us-en-all&utm_content=app-getting-started-with-snowflake-mcp-server) 
* On the top right, click on **Create**
    - Role and Warehouse: **ACCOUNTADMIN** | **DASH_WH_S**
    - Database and Schema: **DASH_MCP_DB.DATA**
    - Name: Support_Tickets
    - Select data to be indexed: select FACT_SUPPORT_TICKETS table
    - Select a search column: select DESCRIPTION
    - Select attribute column(s): select CATEGORY, SUBCATEGORY, PRIORITY, CHANNEL, STATUS, SATISFACTION_SCORE 
    - Select columns to include in the service: Select all
    - Configure your Search Service: Keep default values and select **DASH_WH_S** for "Warehouse for indexing"

### Snowflake MCP Server

To create the Snowflake MCP server, run the following in the same SQL worksheet.

```sql
create or replace mcp server dash_mcp_server from specification
$$
tools:
  - name: "Support Tickets Search Service"
    identifier: "dash_mcp_db.data.support_tickets"
    type: "CORTEX_SEARCH_SERVICE_QUERY"
    description: "A tool that performs keyword and vector search over support tickets and call transcripts."
    title: "Support Tickets"
$$;
```

<!-- ------------------------ -->
## Cursor

Duration: 5

> aside negative
> PREREQUISITE: Successful completion of steps outlined under **Setup**.

In Cursor, open or create `mcp.json` located at the root of your project and add the following. NOTE: Replace **<YOUR-ORG>-<YOUR-ACCOUNT>** and **<YOUR_PAT_TOKEN>** with your values.

```json
{
    "mcpServers": {
      "Snowflake": {
        "url": "https://<YOUR-ORG>-<YOUR-ACCOUNT>.aws.snowflakecomputing.com/api/v2/databases/dash_mcp_db/schemas/data/mcp-servers/dash_mcp_server",
            "headers": {
              "Authorization": "Bearer <YOUR_PAT_TOKEN>"
            }
      }
    }
}
```

Then, select **Cursor** -> **Settings** -> **Cursor Settings** -> **MCP** (or Tools & Integrations) and you should see **Snowflake** under **Installed Servers**. 

NOTE: If it continues to say "Loading tools" running the following `curl` command to test your connection.

```curl
curl -X POST "https://<YOUR-ORG>-<YOUR-ACCOUNT>.snowflakecomputing.com/api/v2/databases/dash_mcp_db/schemas/data/mcp-servers/dash_mcp_server" \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json' \
  --header "Authorization: Bearer <YOUR_PAT_TOKEN>" \
  --data '{
    "jsonrpc": "2.0",
    "id": 12345,
    "method": "tools/list",
    "params": {}
  }'
```

### Q&A

Assuming you're able to see the tool **Support_Tickets_Search_Service** under newly installed **Snowflake** MCP server, let's chat! Start a new chat in Cursor and set your `mcp.json` as context to ask the following questions.

#### Q1. Can you summarize the overall sentiments based on the support calls?

#### Q2. Which support categories would benefit most from automated responses based on transcript analysis?

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 1

Congratulations! You've successfully created a Snowflake MCP Server intelligently responds to questions by reasoning over data from within Cursor.

### What You Learned

- How to create building blocks for Snowflake MCP Server that can intelligently respond to questions by reasoning over data
- How to configure Cursor to interact with Snowflake MCP Server

### Related Resources

- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-mcp-server)




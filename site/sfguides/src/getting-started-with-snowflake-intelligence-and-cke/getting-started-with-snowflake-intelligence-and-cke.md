id: getting-started-with-snowflake-intelligence-and-cke
summary: This guide outlines the process for getting started with Snowflake Intelligence and Cortex Knowledge Extensions.
categories: featured,getting-started,data-science-&-ml,app-development
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Data-Science-&-Ai, Featured
authors: Dash Desai

# Getting Started with Snowflake Intelligence and Cortex Knowledge Extensions
<!-- ------------------------ -->

## Overview

Duration: 4

Snowflake Intelligence offers a powerful solution for organizations to access and activate their vast data. It addresses common challenges for business users struggling to get timely answers from scattered data, and for data teams overwhelmed by ad hoc requests. By using AI agents, Snowflake Intelligence enables employees to securely talk with their data, derive deeper insights, and initiate actions, all from a unified, easy-to-use interface. This transforms how businesses operate by bridging the gap between data and actionable insights.

*NOTE: Snowflake Intelligence is in Public Preview as of August 2025.*

### What is Snowflake Intelligence? 

Snowflake Intelligence is an agentic AI solution, enabling business users to directly and securely interact with their organization's structured and unstructured data using natural language. Snowflake Intelligence provides:

* Natural language interaction: Engage with data like a trusted colleague to securely access and analyze both structured and unstructured data to uncover trends and understand the "why" behind the "what."

* Actionable intelligence: Go beyond just insights by configuring agents to perform tasks based on findings, such as sending notifications, updating records in other systems, or triggering workflows.

* Enterprise-grade security and governance: Honors existing access controls and governance, unifies information from Snowflake and third-party applications for a holistic view, and provides transparency on how answers are derived and data lineage.

![Snowflake Intelligence](assets/si.png)

### What are Cortex Knowledge Extensions?

Cortex Knowledge Extensions (CKEs) allow publishers to bring their documents (for example, news articles, market research reports, books, articles, etc.) to customers in their generative AI applications.

![Snowflake Intelligence](assets/cke.png)

### Prerequisites

* Access to a [Snowflake account](https://signup.snowflake.com/) with ACCOUNTADMIN role.

### What You Will Learn

How to create building blocks for creating a Snowflake Intelligence agent that can intelligently respond to questions by reasoning over data from Cortex Knowledge Extensions.

### What You Will Build

A Snowflake Intelligence agent that can intelligently respond to questions by reasoning over data from Cortex Knowledge Extensions.

<!-- ------------------------ -->
## Setup

Duration: 10

### Create database, schema, and role

* Clone [GitHub repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence-and-cke).

* In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence-and-cke/blob/main/setup.sql) to execute all statements in order from top to bottom.

> aside positive
> NOTE: Switch your user role in Snowsight to **SNOWFLAKE_INTELLIGENCE_ADMIN**.

### Cortex Knowledge Extension

* In Snowsight, on the left hand navigation menu, select **Data Products** >> **Marketplace** 
* In **Snowflake Marketplace**, search for **Snowflake Documentation** 
* Click on **Snowflake Documentation** 
* On the top right, click on **Get** and follow instructions while keeping the default values 

### Create Agent

An agent is an intelligent entity within Snowflake Intelligence that acts on behalf of the user. Agents are configured with specific tools and orchestration logic to answer questions and perform tasks on top of your data. 

Note that you can create multiple agents for various use cases and/or business teams in your organization. 

* In Snowsight, on the left hand navigation menu, select [**AI & ML** >> **Agents**](https://app.snowflake.com/_deeplink/#/agents?utm_source=quickstart&utm_medium=quickstart&utm_campaign=-us-en-all&utm_content=app-getting-started-with-si-and-cke)
* On the top right, click on **Create agent**
     - Schema: SNOWFLAKE_INTELLIGENCE.AGENTS
     - Select **Create this agent for Snowflake Intelligence**
     - Agent object name: Snowflake_Documentation
     - Display name: Snowflake_Documentation
* Select the newly created **Snowflake_Documentation** agent and click on **Edit** on the top right corner and make the following updates.

### Add Instructions

Add the following starter questions under **Sample questions**:

- How do I create a new Snowflake account and set up my first database?
- What are virtual warehouses in Snowflake, and how do I properly size them?
- Can you explain zero-copy cloning and how to clone a database or table?

### Add Tools

Tools are the capabilities an agent can use to accomplish a task. Think of them as the agent's skillset and note that you can add one or more of each of the following tools.

* Tools

  - **Cortex Search Services**
    - Click on **+ Add**
        - Name: Snowflake_Documentation
        - Database and Schema: **SNOWFLAKE_DOCUMENTATION.SHARED**
        - Search service: **SNOWFLAKE_DOCUMENTATION.SHARED.CKE_SNOWFLAKE_DOCS_SERVICE**
        - ID column: SOURCE_URL
        - Title column: DOCUMENT_TITLE
        
  - **Custom tools**
    - Click on **+ Add**
      - Name: Send_Email
      - Resource type: procedure
      - Database & Schema: **SNOWFLAKE_INTELLIGENCE.DATA**
      - Custom tool identifier: **SNOWFLAKE_INTELLIGENCE.DATA.SEND_EMAIL()**
      - Parameter: body
        - Description: *If body is not provided, summarize the last question and use that as content for the email.*
      - Parameter: recipient_email
        - Description: *If the email is not provided, send it to **YOUR_EMAIL_ADDRESS_GOES_HERE***.
      - Parameter: subject
        - Description: *If subject is not provided, use "Snowflake Intelligence"*.
      - Warehouse: **COMPUTE_WH**

* Orchestration: *Whenever you can answer visually with a chart, always choose to generate a chart even if the user didn't specify to.*

* Access: SNOWFLAKE_INTELLIGENCE_ADMIN

> aside positive
> NOTE: On the top right corner, click on **Save** to save the newly updated **Snowflake_Documentation** agent.

<!-- ------------------------ -->
## Snowflake Intelligence

Duration: 5

> aside negative
> PREREQUISITE: Successful completion of steps outlined under **Setup**.

Open [Snowflake Intelligence](https://ai.snowflake.com/_deeplink/#/ai?utm_source=quickstart&utm_medium=quickstart&utm_campaign=-us-en-all&utm_content=app-getting-started-with-si-and-cke) and make sure you're signed into the right account. If you're not sure, click on your name in the bottom left >> **Sign out** and sign back in. Also note that your role should be set to **SNOWFLAKE_INTELLIGENCE_ADMIN**. 

Now, let's ask the following questions.

### Q1. *How do I create a new Snowflake account and set up my first database?*
___

### Q2. *What are virtual warehouses in Snowflake, and how do I properly size them?*
___

### Q3. *Can you explain zero-copy cloning and how to clone a database or table?*
___

### Q4. *Send a summary email*

NOTE: Check your inbox to see the summary email that would have been sent to the email address set it **AI & ML** >> **Agents** >> **Snowflake_Documentation** >> **Custom tools** >> **Send_Email** >> **recipient_email** >> **Description**: "If the email is not provided, send it to YOUR_EMAIL_ADDRESS_GOES_HERE".

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 1

Congratulations! You've successfully created a Snowflake Intelligence agent that can intelligently respond to questions by reasoning over the data from Cortex Knowledge Extensions.

### What You Learned

You've learned how to create building blocks for creating a Snowflake Intelligence agent that can intelligently respond to questions by reasoning over the data from Cortex Knowledge Extensions.

### Related Resources

- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence-and-cke)
- [CKE in Snowflake Marketplace](https://app.snowflake.com/marketplace/data-products?sortBy=popular&categorySecondary=%5B%2226%22%5D)
- [Snowflake Intelligence Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-intelligence)



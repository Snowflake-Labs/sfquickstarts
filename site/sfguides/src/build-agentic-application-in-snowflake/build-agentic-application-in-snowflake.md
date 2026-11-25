id: build-agentic-application-in-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Build a Cortex Agent for Snowflake CoWork that reasons over structured and unstructured data using Cortex Analyst, Cortex Search, and a custom tool.
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
fork repo link: https://github.com/Snowflake-Labs/sfguide-build-data-agents-using-snowflake-cortex-ai
authors: Dash Desai


# Build an Agentic Application in Snowflake
<!-- ------------------------ -->

## Overview

In this guide, you'll build a [Cortex Agent](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) that answers questions by reasoning over both structured and unstructured data, and then use it in [Snowflake CoWork](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork). Agents are configured with a scope, the data sources (tools) they can access, and the actions they can take. They interpret a user's question within their domain, securely analyze the relevant data, and generate a response.

You'll use a custom dataset about bikes and skis. The dataset is intentionally artificial, so no external LLM has prior knowledge of it. That gives you a clean, controlled environment to test and evaluate your agent.

### What is Snowflake CoWork?

Snowflake CoWork is the personal work agent that brings deep analysis and automation to every knowledge worker. Users ask questions in natural language and get answers, charts, and actions grounded in their enterprise data, with built-in role-based access control and governance, all inside Snowflake's perimeter.

### What You'll Learn

- How to connect a GitHub repository to Snowflake and run a notebook in Workspaces
- How to process PDFs and images with Cortex AI functions and index them with Cortex Search
- How to create a semantic view for Cortex Analyst and improve literal matching with Cortex Search
- How to create a Cortex Agent with Cortex Analyst, Cortex Search, and custom tools, and use it in Snowflake CoWork

### What You'll Build

A **Dash//AI** agent in Snowflake CoWork that answers questions about bike and ski product documents and images, analyzes sales data with charts, and sends summary emails.

### What You'll Need

* Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with the ACCOUNTADMIN role in a region where you have access to the Claude models used in this guide. Otherwise, enable [cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference/?utm_source=snowflake-devrel&utm_medium=developer-guides) (see the optional statement at the top of `setup.sql`).

> NOTE: If you're creating a new trial account, choose the **Enterprise** edition, **AWS** as the cloud provider, and **US West (Oregon)** as the region.

<!-- ------------------------ -->
## Setup

The [setup.sql](https://github.com/Snowflake-Labs/sfguide-build-data-agents-using-snowflake-cortex-ai/blob/main/setup.sql) script creates everything you need before building the tools:

```text
Role:               DASH_AGENTS_ROLE
Warehouse:          DASH_WH_AGENTS
Compute pool:       DASH_AGENTS_COMPUTE_POOL (runs the notebook in Workspaces)
Database / schema:  DASH_CORTEX_AGENTS.DATA
Integrations:       DASH_AGENTS_GIT_API_INTEGRATION (GitHub access)
                    DASH_AGENTS_EMAIL_INTEGRATION (email notifications)
Git repository:     DASH_CORTEX_AGENTS.DATA.GIT_REPO
Stage:              DASH_CORTEX_AGENTS.DATA.DOCS (sample PDFs and images copied from the repo)
Procedure:          DASH_CORTEX_AGENTS.DATA.SEND_EMAIL (used later as a custom tool)
CoWork object:      SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT (created only if your account doesn't have one)
```

To run it:

* In Snowsight, on the left hand navigation menu, select **Projects** » **Workspaces**.
* Click **+ Add new** » **SQL file**, and name it `setup.sql`.
* Copy the contents of [setup.sql](https://github.com/Snowflake-Labs/sfguide-build-data-agents-using-snowflake-cortex-ai/blob/main/setup.sql) into the file.
* Execute all statements in order from top to bottom.

**What to expect:** The last statement returns `Congratulations! The setup has completed successfully!`. Earlier results include one `File registered successfully` row for each PDF and image copied to the **DOCS** stage. If your account already has a Snowflake CoWork object, that statement reports it already exists and leaves it unchanged.

> NOTE: Switch your role in Snowsight to **DASH_AGENTS_ROLE**: click your name in the bottom left » **Switch role** » **DASH_AGENTS_ROLE**. Use this role for the rest of the guide unless a step says otherwise.

<!-- ------------------------ -->
## Create Tools

You'll run a notebook in [Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-overview) that sets up the [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview) and [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) tools the agent will use.

### Create a workspace from the GitHub repository

* In Snowsight, on the left hand navigation menu, select **Projects** » **Workspaces**.
* In the **Workspaces** menu at the top left, select **From Git repository**. The **Create workspace from Git repository** dialog opens.
    - Repository URL: `https://github.com/Snowflake-Labs/sfguide-build-data-agents-using-snowflake-cortex-ai`
    - Workspace name: `build-agentic-app`
    - API integration: **DASH_AGENTS_GIT_API_INTEGRATION**
    - Select **Public repository**.
* Click **Create**.

**What to expect:** The **build-agentic-app** workspace opens on the **main** branch. The file list includes the `docs` folder, `SETUP_TOOLS.ipynb`, `semantic.yaml`, and `setup.sql`. A note in the dialog says you can't push changes with public authentication; that's fine, because you only read from the repository.

### Run the notebook

* Open `SETUP_TOOLS.ipynb`.
* Click **Connect** at the top of the notebook and create a notebook service:
    - Compute pool: **DASH_AGENTS_COMPUTE_POOL**
    - Leave the other settings at their defaults.
* After the service connects, click **Run all**.

> NOTE: Workspace notebooks don't set a role, warehouse, database, or schema for you. The first cells in the notebook run `USE ROLE DASH_AGENTS_ROLE`, `USE WAREHOUSE DASH_WH_AGENTS`, and `USE SCHEMA DASH_CORTEX_AGENTS.DATA`, so you don't need to change the role and warehouse picker.

> NOTE: Starting the notebook service can take a few minutes the first time. Running all cells takes about 3-5 minutes.

The notebook does the following:

* **PDFs:** Extracts the text from each PDF with [AI_PARSE_DOCUMENT](https://docs.snowflake.com/en/sql-reference/functions/ai_parse_document), splits it into chunks with [SPLIT_TEXT_RECURSIVE_CHARACTER](https://docs.snowflake.com/en/sql-reference/functions/split_text_recursive_character-snowflake-cortex), and labels each document as **Bike** or **Snow** with [AI_CLASSIFY](https://docs.snowflake.com/en/sql-reference/functions/ai_classify).
* **Images:** Describes each image with the multimodal [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete) function (`claude-sonnet-4-5`), classifies it, and adds the descriptions to the same **DOCS_CHUNKS_TABLE**.
* **Cortex Search:** Creates the **DOCS** search service on the chunks.
* **Structured data:** Creates and populates **DIM_ARTICLE** (8 products), **DIM_CUSTOMER** (5,000 customers), and **FACT_SALES** (80,000 sales over the past 3 years).
* **Semantic view:** Creates the **DASH_CORTEX_AGENTS.DATA.SALES_DATA** semantic view from `semantic.yaml`.
* **Literal search:** Creates the **ARTICLE_NAME_SEARCH** search service over product names, which you'll connect to the semantic view next.

**What to expect:** Every cell completes without errors. The `preview_updated_chunks` cell shows one row per image, each starting with `This is a picture describing the bike or ski:` followed by a generated description, and the `Create_semantic_view` cell reports `Semantic view was successfully created.`

<!-- ------------------------ -->
## Explore the Semantic View

A [semantic view](https://docs.snowflake.com/en/user-guide/views-semantic/overview) maps business terminology to structured data and adds contextual meaning. It allows Cortex Analyst to generate the correct SQL for a question asked in natural language.

### Open the semantic view

* On the left hand navigation menu, select **AI & ML** » **Analyst**.
* Select **SALES_DATA** in **DASH_CORTEX_AGENTS.DATA**.

**What to expect:** The semantic view opens in [Semantic Studio](https://docs.snowflake.com/en/user-guide/views-semantic/semantic-studio) as a YAML file. It has three logical tables (**DIM_ARTICLE**, **DIM_CUSTOMER**, **FACT_SALES**), the relationships that join them, and a verified query for monthly revenue trends.

### Improve literal matching with Cortex Search

Users rarely type a product name exactly as it's stored. Someone asking about "carvers" means the product **Carver Skis**. In the semantic view, the **ARTICLE_NAME** dimension of **DIM_ARTICLE** lists only three sample values, so Cortex Analyst can't map "carvers" to the right product. For example, asked *What are the total sales for the carvers?*, it filters on a product category named `Carvers`, which doesn't exist, and returns no results.

[Integrating the dimension with Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/cortex-analyst-search-integration) fixes this without listing every value in the semantic view. In the **ARTICLE_NAME** dimension, replace the `sample_values` block:

```yaml
        sample_values:
          - Mondracer Infant Bike
          - Premium Bicycle
          - The Ultimate Downhill Bike
```

with a reference to the **ARTICLE_NAME_SEARCH** service the notebook created:

```yaml
        cortex_search_service:
          database: DASH_CORTEX_AGENTS
          schema: DATA
          service: ARTICLE_NAME_SEARCH
```

Then click **Deploy**, select **DASH_CORTEX_AGENTS.DATA** as the target, review the diff, and confirm.

**What to expect:** Asked the same question again, Cortex Analyst now filters on `article_name = 'Carver Skis'` and returns the total sales for that product. The search service matched the imprecise "carvers" to the literal value, which makes the agent more forgiving of how users phrase questions.

<!-- ------------------------ -->
## Create the Agent

An agent is an intelligent entity that acts on behalf of the user. It's configured with tools and orchestration logic to answer questions and perform tasks on top of your data. You can create multiple agents for different use cases or business teams.

### Create the agent

* In Snowsight, on the left hand navigation menu, select **AI & ML** » **Agent Studio**.
* Click **Create agent**.
    - Database and schema: **DASH_CORTEX_AGENTS.DATA**
    - Agent object name: **DASH_AI**
    - Display name: **Dash//AI**
* Select the newly created **DASH_AI** agent, click **Edit**, and make the following updates.

### Add sample questions

Add the following under **Sample questions**:

- Show me monthly sales revenue trends by product category over the past 2 years.
- What is the guarantee of the premium bike?
- What is the length of the carver skis?
- Is there any brand in the frame of the downhill bike?
- How many carvers are we selling per year in the North region?

### Add tools

Tools are the capabilities an agent can use to accomplish a task. Think of them as the agent's skill set. You can add one or more of each of the following.

* **Cortex Analyst**: click **+ Add**
    - Semantic view: **DASH_CORTEX_AGENTS.DATA** » **SALES_DATA**
    - Name: Sales_Data
    - Description: *Retail sales analytics for bikes, skis, and ski boots across customers, products, and sales transactions. Use it for questions about sales, revenue, quantities, customers, regions, sales channels, and promotions. Don't use it for product specifications or usage information.*
    - Warehouse: Custom » **DASH_WH_AGENTS**
    - Query timeout (seconds): 60

* **Cortex Search Services**: click **+ Add**
    - Search service: **DASH_CORTEX_AGENTS.DATA** » **DOCS**
    - ID column: CHUNK_INDEX
    - Title column: RELATIVE_PATH
    - Name: Docs

* **Custom tools**: click **+ Add**
    - Resource type: procedure
    - Database & Schema: **DASH_CORTEX_AGENTS.DATA**
    - Custom tool identifier: **DASH_CORTEX_AGENTS.DATA.SEND_EMAIL()**
    - Name: Send_Email
    - Warehouse: **DASH_WH_AGENTS**
    - Query timeout (seconds): 60
    - Parameter: body
        - Description: *Use HTML-Syntax for this. If the content you get is in markdown, translate it to HTML. If body is not provided, summarize the last question and use that as content for the email.*
    - Parameter: recipient_email
        - Description: *If the email is not provided, send it to the current user's email address.*
    - Parameter: subject
        - Description: *If the subject is not provided, use "Snowflake CoWork".*

* **Orchestration instructions**: *Whenever you can answer visually with a chart, always choose to generate a chart even if the user didn't specify to.*

* **Access**: DASH_AGENTS_ROLE

> NOTE: On the top right corner, click **Save** to save the updated **DASH_AI** agent.

> NOTE: `SYSTEM$SEND_EMAIL` only delivers to [verified email addresses](https://docs.snowflake.com/en/user-guide/notifications/email-notifications#label-email-notification-verify-address). Make sure the email address on your Snowflake user is verified.

### Add the agent to Snowflake CoWork

Your account's [Snowflake CoWork object](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork/deploy-agents#snowflake-cowork-object) controls which agents appear in Snowflake CoWork. Adding an agent requires a role with MODIFY on that object, so run the following in your `setup.sql` file (or a new SQL file) in Workspaces:

```sql
USE ROLE ACCOUNTADMIN;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT ADD AGENT DASH_CORTEX_AGENTS.DATA.DASH_AI;
USE ROLE DASH_AGENTS_ROLE;
```

**What to expect:** The statement succeeds, and `SHOW AGENTS IN SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;` lists **DASH_AI** with the display name **Dash//AI**.

<!-- ------------------------ -->
## Snowflake CoWork

Open [Snowflake CoWork](https://ai.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-build-agentic-application-in-snowflake&utm_cta=developer-guides-deeplink) (or **AI & ML** » **Snowflake CoWork** in Snowsight) and make sure you're signed in to the right account. If you're not sure, click your name in the bottom left » **Sign out** and sign back in.

Snowflake CoWork starts your session with your default role and warehouse. Click your name in the bottom left and set the role to **DASH_AGENTS_ROLE** and the warehouse to **DASH_WH_AGENTS**, then select the **Dash//AI** agent.

> NOTE: The sales data is generated randomly when you run the notebook, so your numbers will differ from the examples below.

### Unstructured data

These questions are answered from the PDF documents and image descriptions.

#### Q. *What is the guarantee of the premium bike?*

**What to expect:** The agent uses the **Docs** tool and answers that the warranty lasts 14 months from the date of purchase and covers manufacturing defects and faults in materials and workmanship, with citations to the documents it used.

#### Q. *What is the length of the carver skis?*

**What to expect:** The agent uses the **Docs** tool and answers that Carver Skis come in 150 cm and 155 cm lengths, often with details such as the turn radius and weight.

#### Q. *Is there any brand in the frame of the downhill bike?*

**What to expect:** The agent answers from the image descriptions generated in the notebook, naming the brand printed on the frame in the downhill bike photo. It may also point out that the photo's brand differs from the product name in the documentation. This shows how processed images extend what the agent can answer.

> Feel free to explore the PDF documents and images to ask other questions.

### Structured data

These questions are answered from the sales tables through the semantic view.

#### Q. *Show me monthly sales revenue trends by product category over the past 2 years.*

**What to expect:** A line chart of monthly revenue for **Bike**, **Skis**, and **Ski Boots**. Bikes bring in far more revenue than the other categories, so the agent may plot them in a separate chart. Expect the current month to be lower because it's still in progress.

#### Q. *How many carvers are we selling per year in the North region?*

**What to expect:** A chart of yearly units of **Carver Skis** sold to North region customers. The agent resolves "carvers" to **Carver Skis** and joins all three tables to answer. The first and current years are partial because the data covers the past 3 years.

#### Q. *How many infant bikes are we selling per month?*

**What to expect:** A chart of monthly units of the **Mondracer Infant Bike**, the only infant bike in the catalog, with a typical monthly range.

#### Q. *What are the top 5 customers buying the carvers?*

**What to expect:** A ranked list or chart of the five customers with the highest **Carver Skis** revenue, with their region and segment.

### Take an action

#### Q. *Send a summary email*

**What to expect:** The agent uses the **Send_Email** tool and confirms that it sent the email. Check your inbox for an HTML summary of the previous answer.

> Feel free to explore the semantic view to ask other questions.

<!-- ------------------------ -->
## Clean Up

To remove the objects created in this guide:

* In Workspaces, open the notebook, click **Connected** » **Manage service**, and drop the notebook service you created. Then delete the workspace you created from the GitHub repository.
* Run the following SQL in a SQL file in Workspaces:

```sql
USE ROLE ACCOUNTADMIN;

ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT DROP AGENT DASH_CORTEX_AGENTS.DATA.DASH_AI;
DROP DATABASE IF EXISTS DASH_CORTEX_AGENTS;
ALTER COMPUTE POOL IF EXISTS DASH_AGENTS_COMPUTE_POOL STOP ALL;
DROP COMPUTE POOL IF EXISTS DASH_AGENTS_COMPUTE_POOL;
DROP WAREHOUSE IF EXISTS DASH_WH_AGENTS;
DROP INTEGRATION IF EXISTS DASH_AGENTS_EMAIL_INTEGRATION;
DROP INTEGRATION IF EXISTS DASH_AGENTS_GIT_API_INTEGRATION;
DROP ROLE IF EXISTS DASH_AGENTS_ROLE;
```

> NOTE: This leaves the `SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT` CoWork object in place, since other agents in your account may use it. Dropping the database also drops the agent, semantic view, search services, tables, stage, and procedure.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've built a Cortex Agent that reasons over both structured and unstructured data, and used it in Snowflake CoWork to answer questions, generate charts, and send emails.

### What You Learned

- How to connect a GitHub repository to Snowflake and run a notebook in Workspaces
- How to process PDFs and images with Cortex AI functions and index them with Cortex Search
- How to create a semantic view for Cortex Analyst and improve literal matching with Cortex Search
- How to create a Cortex Agent with Cortex Analyst, Cortex Search, and custom tools, and use it in Snowflake CoWork

### Related Resources

- [GitHub repository](https://github.com/Snowflake-Labs/sfguide-build-data-agents-using-snowflake-cortex-ai)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- [Snowflake CoWork](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork)
- [Best Practices for Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/)

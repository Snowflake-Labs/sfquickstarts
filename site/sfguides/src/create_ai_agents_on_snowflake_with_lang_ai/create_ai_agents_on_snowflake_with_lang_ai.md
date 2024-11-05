author: Lang.ai
id: create_ai_agents_on_snowflake_with_lang_ai
summary: Through this quickstart guide, you will set up an AI Agent running on Snowflake to set up recurring data analysis for your business teams.
categories: Getting-Started, Data-Science-&-Ai, Data-Science-&-Ml, partner-integrations 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, AI Agents 

# Create AI Agents on Snowflake with Lang.ai
<!-- ------------------------ -->
## Overview 
Duration: 1

Lang.ai Native Snowflake application provides AI agents for product managers that leverage your existing Snowflake data (unstructured and structured data) to serve meaningful product recommendations —with context— directly in Slack.

This quickstart is a guide to installing and running your first Lang AI agent for data analysis in your own Snowflake infrastructure.

![Snowflake and Lang logos](assets/overview_logos.png)

### Prerequisites
- Being part of Lang.ai AI Agent Design Partner program
- Sharing with Lang.ai's Account Executive your Snowflake Account Identifier

### What You'll Learn
- Installing and setting up the Lang.ai Native Application
- Creating and running your first AI agent

### What You’ll Need 
- A Snowflake account with _ACCOUNTADMIN_ access to grant account level privileges, allow external connections and create a Snowflake View.

### What You’ll Build 
- A Snowflake AI Agent for data analysis

<!-- ------------------------ -->
## Creating a sample database
Duration: 5

In this step we will be creating a sample database and a sample view. We will be using this data in the following steps to create our first AI agent.

Sign in to your Snowflake account and create a new SQL Worksheet.

![Creating a new SQL Worksheet](assets/sample_database_step_1.png)

To start, copy the <button>[SQL Script](https://raw.githubusercontent.com/lang-ai/snowflake-app-samples/main/retention-agent-demo/setup.sql)</button> and paste it into the SQL Worksheet, then click on the **Run All** button to execute the script.

![Running the script](assets/sample_database_step_2.png)

This script will:
- Create a Database called *zoom_cancellations* and populate it with demo data
- Create a Database called *zoom_users* and populate it with demo data
- Create a View called *zoom_cancellations_view* to connect the data from both tables

After the script has successfully executed, you will see a LANG_AI_DEMO database with the following tables and one view:

![Database created](assets/sample_database_step_3.png)

The view created by the script already includes the required fields to create AI agents:

> aside positive
> 
>- **id:** The id of the document (ticket, survey, etc.)
>- **text:** The unstructured text to be analyzed
>- **creation_date:** The date of creation of the unstructured text
>- **user_id:** The id of the user that generated the unstructured text

In this example, we are creating a simple view with the fields _id_, _text_, _creation_date_, _user_id_, and _Customer_Spend_. 

The last column _Customer_Spend_ is not mandatory, but it is included as we will configure the agent to use it to group the insights by the customer monthly spending. 

You may include additional columns that may be used by the AI agent to aggregate the insights generated. 


<!-- ------------------------ -->
## Installing the application
Duration: 5

> aside positive
> NOTE: This guide shows the steps needed to install the app via the user interface. If you prefer to install it using SQL scripts, please follow this [guide](https://help.lang.ai/en/articles/9813363-install-the-native-app-with-an-sql-script).


Log in to Snowsight as an ACCOUNTADMIN and follow these steps to install the Lang.ai Native App:

### 1. Install the application

Go to _Data Products > Private Sharing > Shared With You_ and click on _Get_ to install the app.

Once installed, click on the name of the application to open the app.

### 2. Grant privileges

Click Grant to grant the application the necessary privileges:

#### Account-level Privileges
![Grant Account Level Privileges](assets/install_privileges.png)
- The **BIND SERVICE ENDPOINT** privilege enables the services in the app to connect to each other.
- The **CREATE WAREHOUSE** and **CREATE COMPUTE POOL** are required by the Lang.ai Native App to create and manage resources for performing service operations. Learn more [here]((https://help.lang.ai/en/articles/9813363-install-the-native-app-with-an-sql-script).


#### Give access to the Snowflake View

Share data with your AI Agents by creating and sharing access to a view. Learn more [here](https://help.lang.ai/en/articles/9914672-creating-an-sql-view-for-your-ai-agent).

```sql
-- Customize if needed
SET LANGAI_APP_NAME = 'LANGAI_APP';

--- Give the application access to the view  
GRANT USAGE ON DATABASE "lang_ai_demo" TO APPLICATION IDENTIFIER($LANGAI_APP_NAME);

GRANT USAGE ON SCHEMA "PUBLIC" TO APPLICATION IDENTIFIER($LANGAI_APP_NAME);

GRANT SELECT ON VIEW "zoom_cancellations" TO APPLICATION IDENTIFIER($LANGAI_APP_NAME);
```


### 3. Launch the app
Click *Activate* to activate the application.

Navigate back to the *Data Products > Apps* page and wait for the spinner in the INSTALLED column to stop running. When it’s done you’ll see “1 minute ago” in that column. Then click _Launch App_ to start the application.

<!-- ------------------------ -->
## Creating Your First AI Agent
Duration: 5

Learn to run your fist AI agent on top of Snowflake data.

### Select Your Goal
Begin by selecting the goal you want to achieve with your AI agent.

![Select Your Goal](assets/agent_step_1.png)

### Select Your AI Agent
Choose the AI agent that aligns with your goal. Once selected, you will be prompted to choose the attributes that will be used to segment the insights. For example, selecting "subscription plan" will ensure insights are generated with this in mind, helping the AI agent identify patterns relevant to your business objectives.

![Select Your AI Agent](assets/agent_step_2.png)

### Run Your AI Agent for the First Time
After completing the setup and creating your first agent, you're ready to run it for the first time.

To manually run your agent, click on **Run Agent**. The demo data has comments from July 2024, so make sure to select the entire month.

![Run Your AI Agent](assets/agent_step_4.png)


## Reviewing the Insights of Your AI Agent
Duration: 5

> aside positive
> Automate insight delivery to Slack! For instructions on setting up the Slack integration, please check this [guide](https://help.lang.ai/en/articles/9950927-connecting-the-slack-integration).

### Navigate Your Agent Insights
Once the agent has finished processing, click on table to see the generated insights. In the insights view, you can navigate through the data by sorting and searching. 

![Navigate Your Agent Insights](assets/review_agent_insights.png)

### Review the Data Associated with the Insights

To view the unstructured text that was analyzed to generate an insight, simply click on the specific insight.

Additionally, you have the option to download the data from your active filters by clicking on **Download CSV**.

![Review Data Associated with Insights](assets/review_agent_rows.png)

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

By following this guide, you have successfully set up an AI Agent running on Snowflake to automate your data analysis tasks.

### Related Resources
- [Marketplace Listing](https://app.snowflake.com/marketplace/listing/GZTSZ1TJ3IU/lang-ai-snowflake-ai-agents)
- [Lang.ai Help Center](https://help.lang.ai/en/collections/9808378-build-your-first-ai-agent)

### What You Learned
- How to set up the Lang.ai Snowflake Native App
- How to create and configure an AI Agent in Lang.ai
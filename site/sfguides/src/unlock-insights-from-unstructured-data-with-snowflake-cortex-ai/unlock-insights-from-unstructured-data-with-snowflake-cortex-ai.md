summary: Unlock Insights from Unstructured Data with Snowflake Cortex AI 
id: unlock-insights-from-unstructured-data-with-snowflake-cortex-ai
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
author: Sean Morris, Stephen Dickson
[environment_name]: ai209


fork repo link: https://github.com/Snowflake-Labs/sfguide-unlock-insights-from-unstructured-data-with-snowflake-cortex-ai
# Unlock Insights from Unstructured Data with Snowflake Cortex AI


<!-- ------------------------ -->
## Overview


This guide demonstrates how to create a Streamlit application running inside Snowflake that unlocks insights from unstructured data using **Snowflake Cortex AI**.  
It shows how to translate, summarize, classify text, generate emails, and even analyze images — all without deploying external infrastructure.

### Prerequisites
- A Snowflake account. If you don’t have one, you can sign up for a free trial [here](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).
- The ACCOUNTADMIN role to ensure you have full access for setup and configuration.

### What You’ll Learn
- How to create a database, schema, and stage in Snowflake
- How to store unstructured data in Snowflake stages
- How to use SQL to run LLM functions (`TRANSLATE`, `SENTIMENT`, `SUMMARIZE`, `COMPLETE`)
- How to build a frontend application with Streamlit inside Snowflake

### What You'll Build
A fully functioning **Streamlit app** inside Snowflake that:
- Translates between multiple languages
- Scores sentiment of call transcripts
- Summarizes long-form text
- Classifies customer service inquiries
- Analyzes uploaded images using multimodal LLMs

<!-- ------------------------ -->
## Setup


### Login to Snowsight

Log into Snowflake's web interface [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) using your Snowflake credentials.

### Enable Cross-Region Inference

In the Snowsight UI on the left hand sidebar, select the **Projects > Worksheets** tab.

In the top right hand corner, click the **+** button to create a new SQL worksheet.

Run the following SQL commands to [enable cortex cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference.html).

```sql
-- set role context
USE ROLE accountadmin;

-- enable Cortex Cross Region Inference
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

### Create Snowflake Objects

In the same SQL worksheet, run the following SQL commands to create the [warehouse](https://docs.snowflake.com/en/sql-reference/sql/create-warehouse.html), [database](https://docs.snowflake.com/en/sql-reference/sql/create-database.html), [schema](https://docs.snowflake.com/en/sql-reference/sql/create-schema.html), and [stage](https://docs.snowflake.com/en/sql-reference/sql/create-stage.html)

> 
> IMPORTANT:
> 
> If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.

```sql
-- Set role context
USE ROLE sysadmin;

-- Set Environment Name
SET var_name = 'ai209';

-- Generate Environment Identifiers
SET var_warehouse_name = $var_name||'_wh';
SET var_database_name = $var_name||'_db';
SET var_schema_name = $var_name||'_db.demo';

-- Set Warehouse Context
CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($var_warehouse_name) WITH
    WAREHOUSE_SIZE = xsmall
    AUTO_SUSPEND = 60
    INITIALLY_SUSPENDED = true;
USE WAREHOUSE IDENTIFIER($var_warehouse_name);

-- Set Database Schema Context
CREATE DATABASE IF NOT EXISTS IDENTIFIER($var_database_name);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($var_schema_name);
USE SCHEMA IDENTIFIER($var_schema_name);
```

<!-- ------------------------ -->
## Build Streamlit Application


Let's create a Streamlit application for interactive image analysis:

### Setting Up the Streamlit App

To create and configure your Streamlit application in Snowflake:

1. Navigate to Streamlit in Snowflake:
   * Click on the **Streamlit** tab in the left navigation pane
   * Click on **+ Streamlit App** button in the top right

2. Configure App Settings:
   * Enter a name for your app (e.g., "AI/ML Toolkit")
   * Select the warehouse **AI209_WH**
   * Choose **AI209_DB.DEMO** as your database and schema
   * Click **Create**

3. Create the app:
   * In the editor, paste the complete code provided in the [streamlit_app.py](https://github.com/Snowflake-Labs/sfguide-unlock-insights-from-unstructured-data-with-snowflake-cortex-ai/blob/main/streamlit_app.py) file
   * Click "Run" to launch your application

The application provides:
- Translation: Translate text between 14 different languages using Snowflake Cortex
- Sentiment Analysis: Analyze the sentiment of call transcripts
- Data Summarization: Generate concise summaries of large text datasets
- Next Best Action: Use foundation models to identify customer next actions
- Text Classification: Categorize text into predefined categories
- Email Generation: Create customer emails based on call transcripts
- Question Answering: Ask questions to foundation models
- Multi-Modal Image Analysis: Analyze and categorize images using multi-modal models

<!-- ------------------------ -->
## Conclusion And Resources


Congratulations! You’ve successfully built an end-to-end image analysis application using Snowflake Cortex AI models. This app showcases how to unlock value from unstructured data — including text and images - all within the Snowflake environment.

By combining Snowflake-native large language models (LLMs) and multimodal capabilities with Streamlit, you built an interactive solution that can:
- Translate and classify text across multiple languages
- Analyze sentiment and summarize long-form content
- Automatically generate emails and next-best-actions from transcripts
- Perform real-time image analysis using multimodal foundation models

This end-to-end pattern demonstrates how Snowflake Cortex can power intelligent applications directly on top of your data, reducing time-to-insight and simplifying operational complexity.

### What You Learned
- How to provision warehouses, databases, schemas, and stages in Snowflake
- How to store and process unstructured text and image data
- How to run SQL-based AI functions (TRANSLATE, SUMMARIZE, SENTIMENT, etc.)
- How to analyze visual data using foundation models
- How to build a secure, fully integrated frontend using Streamlit in Snowflake

### Related Resources
- [Snowflake Large Language Model (LLM) Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Snowflake Cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference)
- [Snowflake Cortex COMPLETE Multimodal](https://docs.snowflake.com/en/user-guide/snowflake-cortex/complete-multimodal)

author: Neelima Parakala
id: from-zero-to-agents
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/feature/cortex-ai, snowflake-site:taxonomy/feature/dynamic-tables
language: en
summary: Build governed AI agents in Snowflake by transforming raw data into actionable insights using Cortex AI for sentiment analysis and Dynamic Tables for automated enrichment.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# From Zero to Agents: Building End-to-End Data Pipelines for an AI Agent
<!-- ------------------------ -->

## Overview

This hands-on lab guides you through transforming raw data into actionable insights using Snowflake Cortex AI for sentiment analysis and classification. You will get hands-on experience with Cortex AI and Dynamic Tables to automate AI enrichment and construct a reliable semantic layer. Learn the architecture required to create a Marketing & Sales Intelligence Agent that leverages both structured data and enriched unstructured feedback while maintaining enterprise security standards.

### What You'll Learn
- How to use Cortex AI functions for sentiment analysis and text classification
- How to create Dynamic Tables for automated AI enrichment pipelines
- How to build a Semantic View to map technical columns to business terms
- How to create and configure an AI Agent with Analyst and Search tools
- How to implement Role-Based Access Control (RBAC) with Dynamic Data Masking

### What You'll Build
- An automated AI enrichment pipeline using Cortex AI and Dynamic Tables
- A Semantic View that provides business-friendly abstractions over your data
- A Marketing & Sales Intelligence Agent powered by Cortex Analyst and Cortex Search
- Enterprise-grade security controls with masking policies

### Prerequisites
- A [Snowflake account](https://signup.snowflake.com/) with a role that has the ability to create database, schema, tables, and virtual warehouse objects
- Basic familiarity with SQL
- Access to Snowsight (Snowflake's web interface)

<!-- ------------------------ -->

## Environment and Data Loading

Establish the secure foundation using the provided `setup.sql` script. This script automates the creation of roles, warehouses, and the ingestion of marketing data from public S3 buckets.

### Setup Instructions

Run [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence/blob/main/setup.sql) in a Snowsight SQL Worksheet.

### What Gets Provisioned

- **Infrastructure:** Provisions the `dash_wh_si` warehouse and `snowflake_intelligence` database
- **Ingestion:** Loads **structured metrics** (campaign spend, product sales) and **unstructured transcripts** (`support_cases`)

<!-- ------------------------ -->

## AI Enrichment with Cortex AI

**AI Enrichment with Cortex AI** refers to the process of using built-in generative AI functions directly within standard SQL queries to analyze, transform, and add value to your data.

In Snowflake, this is powered by **Snowflake Cortex AI**, which allows you to run high-performance Large Language Models (LLMs) without moving your data to an external service or managing complex infrastructure.

### How It Works

Traditionally, if you wanted to perform sentiment analysis or extract names from text, you had to export data to a Python environment or a third-party API. With Cortex AI Functions, the LLM is treated like any other SQL function (e.g., `SUM()` or `AVG()`).

### Core Cortex AI Functions

Snowflake provides several task-specific functions that make enrichment simple:

| Function | Description |
|----------|-------------|
| `SNOWFLAKE.CORTEX.AI_SENTIMENT(text)` | Returns a score from -1 (very negative) to 1 (very positive) |
| `SNOWFLAKE.CORTEX.AI_SUMMARIZE(text)` | Creates a concise summary of long documents or transcripts |
| `SNOWFLAKE.CORTEX.AI_EXTRACT_ANSWER(text, question)` | Finds a specific answer within a block of unstructured text |
| `SNOWFLAKE.CORTEX.AI_CLASSIFY(text, categories)` | Buckets text into predefined labels (e.g., "Refund," "Complaint," "Sales Inquiry") |
| `SNOWFLAKE.CORTEX.AI_TRANSLATE(text, source, target)` | Translates text between languages |

### Why Use AI Enrichment?

- **Scalability:** Process millions of rows of unstructured text using Snowflake's elastic compute (Warehouses)
- **Security:** Your data never leaves the Snowflake security perimeter, which is vital for GDPR/HIPAA compliance
- **Automation:** By putting these functions inside **Dynamic Tables**, your AI enrichment happens automatically as new data arrives
- **Low Friction:** Analysts who know SQL can now perform advanced "Data Science" tasks without learning Python or PyTorch

### Integration with AI Agents

AI Enrichment is the "Preprocessing" step. By enriching your data first:

1. The **Agent** doesn't have to read every raw transcript
2. It can simply query the `sentiment_score` column to find unhappy customers
3. This makes the agent faster, cheaper, and more accurate

### Extract Trends

Transform "dark data" (raw transcripts) into analytical trends using Cortex AI Functions. Run sentiment analysis on customer feedback to create measurable features:

```sql
SELECT 
    title,
    SNOWFLAKE.CORTEX.AI_SENTIMENT(transcript) AS sentiment_score,
    SNOWFLAKE.CORTEX.AI_CLASSIFY(transcript, ['Return', 'Quality', 'Shipping']) AS issue_category
FROM support_cases;
```

<!-- ------------------------ -->

## Create Live Enrichment Pipeline

To create a "Live" enrichment pipeline, we combine **Cortex AI Functions** with **Dynamic Tables**. This allows Snowflake to automatically process new data as it arrives, keeping your sentiment scores and classifications up to date without manual intervention.

### The Architecture of Live Enrichment

Instead of running a one-time enrichment, you define a **Dynamic Table**. This table acts as a materialized view that continuously "listens" for changes in your raw data (e.g., new customer feedback) and runs the AI functions only on the new or changed rows.

### Create the Enriched Dynamic Table

Create a Dynamic Table that automatically joins campaign metrics with AI-generated sentiment scores:

```sql
CREATE OR REPLACE DYNAMIC TABLE enriched_marketing_intelligence
TARGET_LAG = '1 minute'
WAREHOUSE = dash_wh_si
AS
SELECT m.campaign_name, m.clicks, 
       SNOWFLAKE.CORTEX.AI_SENTIMENT(s.transcript) AS avg_sentiment
FROM marketing_campaign_metrics m
JOIN support_cases s ON m.category = s.product;
```

<!-- ------------------------ -->

## Semantic Layer and Agent Creation

Provide the agent with a "map" to understand your business logic through a **Semantic View**.

### Create a Semantic View

Map technical columns to natural business terms like **"Ad Campaign"** and **"Customer Sentiment."**

1. Navigate to **AI & ML > Analyst** in Snowsight
2. Configure the following settings:
   - **Role:** `SNOWFLAKE_INTELLIGENCE_ADMIN`
   - **Warehouse:** `DASH_WH_SI`
   - **Location to store:** `DASH_DB_SI.Retail`
   - **Name:** `SEMANTIC_VIEW`
   - **Select tables:** `DASH_DB_SI.Retail`
   - **Select Columns:** Marketing Metrics

### Create a Cortex Search Service

1. Navigate to **AI & ML > Search** in Snowsight
2. Switch role to `SNOWFLAKE_INTELLIGENCE_ADMIN`
3. Select **Create**
4. Configure the following settings:
   - **Service database & schema:** `DASH_DB_SI.Retail`
   - **Service name:** `campaign_search`
   - **Select Data:** `marketing_campaign_metrics`
   - **Select search column:** `campaign name`
   - **Select attribute columns:** Select all

### Create the Agent

1. Navigate to **AI & ML > Agents** in Snowsight
2. Add the **Analyst Tool** (using your Semantic View) and the **Search Tool** (for transcript retrieval)
3. Configure the agent:
   - **Agent Name:** `agent`
   - **Agent Description:** 
   
   > I am a specialized Marketing & Sales Intelligence Assistant. My primary role is to provide accurate, data-driven insights by analyzing structured marketing metrics (spend, clicks, conversions) and unstructured customer feedback (support transcripts). I bridge the gap between 'what happened' (the numbers) and 'why it happened' (customer sentiment). Always maintain a professional, analytical tone and provide clear citations for information retrieved from support transcripts.

4. **Agent Tools:** Add Cortex Analyst & Cortex Search

<!-- ------------------------ -->

## Validation

Interact with the agent and verify that it respects enterprise-grade governance.

### Accessing the Agent

Once your agent is created and enabled for **Snowflake Intelligence**, it appears in a dedicated workspace:

1. In Snowsight, go to **AI & ML > Snowflake Intelligence**
2. You will see a list of agents you have access to
3. Select your **Marketing Intelligence Agent**

### The Conversational Interface

The UI is designed to handle natural language queries. It doesn't just return data; it provides a narrative response.

- **Natural Language Input:** Users type questions like, *"Which campaigns had a low budget but high customer sentiment last month?"*
- **Suggested Prompts:** Based on your Semantic View and Agent Description, the UI often provides "starter" questions to guide the user
- **Multimodal Answers:** The agent will combine text (summarizing feedback from Cortex Search) with tables or charts (visualizing metrics from Cortex Analyst)

## Security (optional)
### Trace Monitoring

For lab participants, the Trace is the most critical UI interaction. It allows you to debug the agent's logic:

1. **The Plan:** The UI displays how the agent broke down your prompt (e.g., "Step 1: Identify campaigns with budget < 5000. Step 2: Retrieve sentiment scores for those campaigns.")
2. **Tool Selection:** You can see which tool was invoked for which step—whether it chose the Analyst for the budget or Search for the "Why"
3. **Reflection:** You can see if the agent caught its own errors and re-ran a query to get a better result

<!-- ------------------------ -->
### Security Showcase

Apply **Dynamic Data Masking** to specific metrics to ensure the agent respects **RBAC** (Role-Based Access Control).

### Create the Marketing Role

If you ran the `setup.sql` exactly as provided in the GitHub repo, it created `snowflake_intelligence_admin`. Let's create the `marketing_intelligence_role` to represent your "Restricted Team" and give it the necessary access.

```sql
USE ROLE ACCOUNTADMIN;

-- Create the role
CREATE OR REPLACE ROLE marketing_intelligence_role;

-- Grant usage on the warehouse and database
GRANT USAGE ON WAREHOUSE dash_wh_si TO ROLE marketing_intelligence_role;
GRANT USAGE ON DATABASE dash_db_si TO ROLE marketing_intelligence_role;
GRANT USAGE ON SCHEMA dash_db_si.retail TO ROLE marketing_intelligence_role;

-- Grant access to the AI functions and the specific views
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE marketing_intelligence_role;
GRANT SELECT ON VIEW dash_db_si.retail.marketing_intelligence_view TO ROLE marketing_intelligence_role;

-- Assign to yourself for testing
GRANT ROLE marketing_intelligence_role TO USER IDENTIFIER($CURRENT_USER);
```

### Apply the Masking Policy

A masking policy exists in Snowflake but isn't "active" until it is **applied** to a specific column. We will mask the `CLICKS` column so the marketing role sees `0` while the admin sees the real data.

```sql
USE ROLE snowflake_intelligence_admin;
USE SCHEMA dash_db_si.retail;

-- 1. Create the policy
CREATE OR REPLACE MASKING POLICY mask_engagement_clicks AS (val number) 
RETURNS number ->
  CASE 
    WHEN CURRENT_ROLE() IN ('SNOWFLAKE_INTELLIGENCE_ADMIN', 'ACCOUNTADMIN') THEN val 
    ELSE 0 -- Masked value for other roles
  END;

-- 2. Apply the policy to the base table column
ALTER TABLE marketing_campaign_metrics MODIFY COLUMN clicks SET MASKING POLICY mask_engagement_clicks;

-- 3. Verify the policy is active
SELECT * FROM TABLE(INFORMATION_SCHEMA.POLICY_REFERENCES(
    policy_name => 'mask_engagement_clicks'
));
```

### Verify as Admin

```sql
-- Re-run the view to ensure it picks up the table-level masking
CREATE OR REPLACE SECURE VIEW marketing_intelligence_view AS
SELECT 
    campaign_name AS "Ad Campaign",
    category AS "Product Category",
    clicks AS "Engagement Clicks",
    -- avg_sentiment will come from the Dynamic Table
    0 AS "Customer Sentiment Score" 
FROM marketing_campaign_metrics;

USE ROLE snowflake_intelligence_admin;
-- You should see numbers like 11103
SELECT "Ad Campaign", "Engagement Clicks" FROM marketing_intelligence_view;
```

### Verify as Marketing Role

```sql
USE ROLE marketing_intelligence_role;
-- You should see 0 for all clicks
SELECT "Ad Campaign", "Engagement Clicks" FROM marketing_intelligence_view;
```

### Agent Interaction Verification

Now that the data is masked at the source, the **Agent** will automatically respect it.

1. Switch your UI role to `marketing_intelligence_role`
2. Ask the Agent: *"How many clicks did the Summer Fitness campaign get?"*
3. The Agent will query the view, receive `0` from the database engine, and reply: *"The Summer Fitness campaign received 0 clicks."*
4. **Show Reasoning:** Open the trace to prove the SQL was correct, but the **Data Engine** protected the values

<!-- ------------------------ -->

## Conclusion And Resources

Congratulations! You've successfully built an end-to-end data pipeline for an AI agent in Snowflake. You transformed raw marketing data and unstructured customer feedback into actionable insights using Cortex AI, automated the enrichment process with Dynamic Tables, and created a governed Marketing Intelligence Agent.

### What You Learned
- How to use Cortex AI functions (`AI_SENTIMENT`, `AI_CLASSIFY`) for text analysis directly in SQL
- How to create Dynamic Tables for automated, real-time AI enrichment
- How to build Semantic Views that map technical schemas to business-friendly terms
- How to configure AI Agents with Cortex Analyst and Cortex Search tools
- How to implement enterprise security using Dynamic Data Masking and RBAC

### Related Resources
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Dynamic Tables Overview](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Semantic Views Documentation](https://docs.snowflake.com/en/user-guide/views-semantic)
- [Getting Started with Snowflake Intelligence](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-intelligence)
- [Snowflake Documentation](https://docs.snowflake.com/)

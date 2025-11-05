author: Joviane Bellegarde
id: fan-engagement
summary: USOPC Fan Engagement - Exploring Fan Engagement Data with Snowflake Intelligence
categories: Cortex, AI, Intelligence Agents, Sports Marketing, Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Cortex, AI, Intelligence Agents, Streamlit, Sports Marketing, Fan Engagement

# Exploring Fan Engagement Data with Snowflake Intelligence
<!-- ------------------------ -->

## Overview

Fan engagement analytics is crucial for sports organizations to understand their fanbase and create targeted marketing campaigns. Through comprehensive data analysis and AI-powered insights, organizations can uncover patterns in fan behavior, identify high-value segments, and generate actionable marketing strategies.

In this Guide, we will explore how the United States Olympic & Paralympic Committee (USOPC) uses Snowflake Intelligence to transform 300,000+ fan profiles into actionable marketing campaigns through natural language conversations.

This Guide showcases a complete fan engagement platform with:
- **Unified Customer 360** - 300k fans with demographics, TransUnion enrichment, and ML predictions
- **Semantic Search** - Find fans by natural language descriptions using Cortex Search
- **AI Analytics** - Ask business questions in plain English using Cortex Analyst
- **Action-Taking Agent** - Intelligence Agent that not just provides insights but saves campaign lists for activation
- **Interactive Dashboard** - Streamlit application with 7 modules for data exploration

<!-- ![assets/architecture_diagram.png](assets/architecture_diagram.png) -->

### What You Will Build
- Complete fan engagement analytics platform with Intelligence Agent
- AI-powered semantic search for fan discovery using Cortex Search
- Natural language analytics using Cortex Analyst with semantic models
- Custom action tool (Python UDF) for saving campaign audiences
- Production-ready Streamlit application with advanced visualizations
- End-to-end analytics-to-activation pipeline

### What You Will Learn
- How to set up Snowflake Intelligence Agents with multiple tools
- How to use Snowflake Notebooks for complex AI processing workflows
- How to implement Cortex Search for semantic fan discovery
- How to build semantic models for Cortex Analyst
- How to create custom action tools using Python stored procedures
- How to deploy interactive Streamlit applications in Snowflake

### Prerequisites
- Familiarity with Python and SQL
- Familiarity with Streamlit applications
- Go to the [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) sign-up page and register for a free account

<!-- ------------------------ -->
## Setup Snowflake Environment  

In this step, you'll create the Snowflake database objects and upload all necessary files for the USOPC Fan Engagement platform.

### Step 1: Create Database Objects

1. In Snowsight, navigate to **Projects** > **Worksheets**
2. Create a new SQL worksheet
3. Copy the setup script from [setup.sql](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/scripts/setup.sql) and paste it into your worksheet
4. Run the script

The setup script creates:
- **Role**: `FAN_ENGAGEMENT` with all necessary permissions
- **Warehouse**: `FAN_ENGAGEMENT_WH` for compute resources
- **Database**: `FAN_ENGAGEMENT_DB` with `FAN_ENGAGEMENT` schema
- **2 Stages**: 
  - `USOPC_DATA` (for CSV data + Streamlit files)
  - `SEMANTIC_MODELS` (for YAML files)
- **Base Table**: `UNIFIED_CUSTOMER_PROFILE` structure (111 columns)
- **AI Access**: `SNOWFLAKE.CORTEX_USER` database role grant

### Step 2: Download Required Files

Download these files from the GitHub repository:

| File | Purpose | Download Link |
|------|---------|---------------|
| **Setup Script** | SQL setup script for infrastructure | [setup.sql](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/scripts/setup.sql) |
| **Data File** | USOPC fan profiles (300k records) | [unified_customer_profile.csv.gz](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/scripts/unified_customer_profile.csv.gz) |
| **Streamlit App** | Interactive analytics dashboard | [fan_engagement_dashboard.py](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/scripts/fan_engagement_dashboard.py) |
| **Environment File** | Streamlit dependencies | [environment.yml](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/scripts/environment.yml) |
| **Semantic Model** | Cortex Analyst semantic model | [USOPC_FAN_ENGAGEMENT_DEMO.yaml](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/scripts/USOPC_FAN_ENGAGEMENT_DEMO.yaml) |
| **Notebook** | Complete setup notebook | [usopc_fan_engagement_setup.ipynb](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/notebooks/usopc_fan_engagement_setup.ipynb) |

### Step 3: Upload Files to Stages

Now you'll upload the downloaded files to 2 stages via the Snowsight UI.

1. **Switch to the Fan Engagement role:**
   - In Snowsight, click your profile icon (top right)
   - Select `Switch Role` → `FAN_ENGAGEMENT`

2. **Navigate to Database Explorer:**
   - Go to `Catalog` → `Databases` → `FAN_ENGAGEMENT_DB` → `FAN_ENGAGEMENT` schema

3. **Upload to USOPC_DATA (3 files):**
   - Click `Stages` in the left sidebar
   - Click on `USOPC_DATA`
   - Click the `+ Files` button (top right)
   - Select and upload these 3 files together:
     - `unified_customer_profile.csv.gz` (~79MB - main data file)
     - `fan_engagement_dashboard.py` (~100KB - Streamlit app)
     - `environment.yml` (~72 bytes - Python dependencies)
   - Wait for all uploads to complete

4. **Upload to SEMANTIC_MODELS (1 file):**
   - Go back to `FAN_ENGAGEMENT` schema → `Stages`
   - Click on `SEMANTIC_MODELS`
   - Click the `+ Files` button
   - Select and upload:
     - `USOPC_FAN_ENGAGEMENT_DEMO.yaml` (~39KB - Cortex Analyst semantic model)
   - Wait for upload to complete

### Step 4: Import and Configure the Setup Notebook

1. **Import into Snowflake**:
   - Navigate to `Projects` → `Notebooks` in Snowsight
   - Click the down arrow next to `+ Notebook` and select `Import .ipynb file`
   - Choose `usopc_fan_engagement_setup.ipynb` from your downloads

2. **Configure the notebook settings**:
   - **Notebook Name**: `USOPC_FAN_ENGAGEMENT_SETUP`
   - **Location**: `FAN_ENGAGEMENT_DB.FAN_ENGAGEMENT`
   - **Query Warehouse**: Select `FAN_ENGAGEMENT_WH`
   - **Notebook Warehouse**: Select `FAN_ENGAGEMENT_WH`

3. **Click `Create`** to import the notebook

The notebook contains 8 sections that will:
- Load 300k fan profiles from CSV
- Create searchable table with enriched SEARCH_FIELD
- Create Cortex Search service for semantic fan discovery
- Create campaign infrastructure and save procedure
- Create Intelligence Agent with 3 tools
- Deploy Streamlit dashboard

<!-- ------------------------ -->
## Run Setup Notebook

### Execute the Complete Setup Workflow

1. Go to `Projects` → `Notebooks` in Snowsight
2. Click on `USOPC_FAN_ENGAGEMENT_SETUP` to open it
3. Click `Run all` to execute all cells in the notebook

**What the notebook does:**
- **Section 1-2**: Verifies infrastructure and loads 300k+ fan profiles
- **Section 3**: Creates searchable table with enriched SEARCH_FIELD (~1-2 min)
- **Section 4**: Creates Cortex Search service (indexes in background ~5 min)
- **Section 5-6**: Creates campaign infrastructure and save procedure
- **Section 7**: Creates Intelligence Agent with 3 tools
- **Section 8**: Deploys Streamlit dashboard with 7 modules

**Processing time:** ~5-7 minutes total (Cortex Search indexing happens in parallel)

<!-- ------------------------ -->
## Launch Analytics Dashboard

### Access Your Fan Engagement Platform

1. Navigate to `Projects` → `Streamlit` in Snowsight
2. Find and click on `Fan Engagement Dashboard`
3. Explore your 7-module analytics dashboard

Your platform includes:
- **Overview** - Executive metrics with time series and ranked grids
- **Product** - Product-level insights and comparisons
- **VS** - Side-by-side comparative analysis
- **Top N** - Ranked leaderboards by any dimension
- **Self Service** - Custom query builder for ad-hoc analysis
- **Search** - Cortex Search integration for semantic fan discovery
- **AI Assistant** - Cortex Analyst for natural language queries

<!-- ------------------------ -->
## Test Intelligence Agent

### Access Snowflake Intelligence

1. Navigate to `AI & ML` → `Intelligence` in Snowsight
2. Find and click on `FAN_ENGAGEMENT_ASSISTANT`
3. Try the sample questions below

### Demo Flow: 5 Key Questions

Ask these questions in order to demonstrate the full analytics-to-activation workflow:

---

**1. Education Demographics Analysis**

```
How many of our fans have degrees and how many do not?
```

**What It Shows:** Basic Cortex Analyst analytics—quick demographic segmentation with clear numerical results

---

**2. Comparative Segment Analysis**

```
Can you analyze and tell me which group we are appealing to more in terms of 
our engagement stats and spend stats?
```

**What It Shows:** Advanced multi-metric analysis across segments—demonstrates the agent's ability to combine engagement, value, and demographic data

---

**3. Campaign Strategy Development**

```
If I want to target the degree holders and develop a customized campaign to 
better optimize my relationship with them, how should I go about doing it? 
Give me a plan.
```

**What It Shows:** Strategic AI reasoning—the agent provides actionable campaign recommendations and engagement tactics

---

**4. Audience List Creation**

```
Give me a list of customer IDs to use in this initial campaign.
```

**What It Shows:** Data activation capability—insights immediately convert to actionable audience lists

---

**5. Advanced Semantic Search with Propensity Scoring**

```
Can you identify anyone who has a doctorate and is single and give me the 
propensity score for them to buy merchandise or attend an event?
```

**What It Shows:** Cortex Search integration + custom action—semantic fan discovery combined with ML-powered propensity scoring

---

### Verify Saved Campaigns

After asking the agent to save campaigns, verify they were persisted:

```sql
-- View all saved campaigns
SELECT * FROM FAN_ENGAGEMENT_DB.FAN_ENGAGEMENT.CAMPAIGN_AUDIENCES
ORDER BY created_at DESC;

-- Get campaign summary
SELECT 
    campaign_id,
    campaign_name,
    COUNT(*) as total_fans,
    ROUND(AVG(lifetime_value), 2) as avg_lifetime_value
FROM FAN_ENGAGEMENT_DB.FAN_ENGAGEMENT.CAMPAIGN_AUDIENCES
GROUP BY campaign_id, campaign_name
ORDER BY campaign_id DESC;
```

<!-- ------------------------ -->
## Clean Up Resources

### Remove All Created Objects

When you're ready to remove all the resources created during this guide:

1. Open a new SQL worksheet in Snowsight
2. Copy and paste the teardown script below
3. Run the script to remove all databases, warehouses, roles, and objects

```sql
-- Teardown Script
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS FAN_ENGAGEMENT_DB CASCADE;
DROP WAREHOUSE IF EXISTS FAN_ENGAGEMENT_WH;
DROP ROLE IF EXISTS FAN_ENGAGEMENT;
```

This will clean up all fan engagement components while preserving any other work in your Snowflake account.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've successfully built the complete USOPC Fan Engagement platform using Snowflake Intelligence!

### What You Learned
- **Intelligence Agent with Multi-Tool Orchestration**: How to build agents that combine Cortex Analyst, Cortex Search, and custom actions
- **Analytics-to-Activation Pipeline**: How to go from natural language questions to saved campaign audience lists in minutes
- **Semantic Search**: How to create Cortex Search services for semantic fan discovery
- **Cortex Analyst Integration**: How to build semantic models for natural language SQL generation
- **Custom Action Tools**: How to create Python stored procedures that enable agents to take actions, not just provide insights
- **Production-Ready Streamlit**: How to develop interactive dashboards with advanced visualizations

### Key Takeaways
1. **Snowflake Intelligence** combines multiple Cortex services for powerful AI workflows
2. **Semantic models** make Cortex Analyst business-context aware
3. **Custom tools** (Python UDFs) enable agents to take actions, not just provide insights
4. **Multi-tool orchestration** allows agents to analyze, discover, and act in one conversation
5. **Action-taking agents** bridge the gap from insight to activation in marketing workflows

### Resources
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Intelligence Agents](https://docs.snowflake.com/en/user-guide/snowflake-intelligence)
- [Streamlit in Snowflake](https://docs.snowflake.com/developer-guide/streamlit/about-streamlit)
- [Fork Notebook on GitHub](https://github.com/Snowflake-Labs/sfguides-exploring-fan-engagement-data-with-snowflake-intelligence/blob/main/notebooks/usopc_fan_engagement_setup.ipynb)



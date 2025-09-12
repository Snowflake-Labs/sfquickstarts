author: Joviane Bellegarde
id: snow_bear_leveraging_cortex_for_advanced_analytics
summary: Snow Bear Fan Experience Analytics - Leveraging Cortex for Advanced Analytics
categories: Cortex, Analytics, Getting-Started, AI
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Cortex, AI, Analytics, Streamlit, Sentiment Analysis

# Snow Bear Fan Experience Analytics - Leveraging Cortex for Advanced Analytics
<!-- ------------------------ -->

## Overview
Duration: 15

Customer experience analytics is crucial for businesses to understand their customers and improve their services. Through comprehensive data analysis and AI-powered insights, businesses can uncover patterns in customer feedback, identify pain points, and generate actionable recommendations.

In this Quickstart, we will build a comprehensive fan experience analytics platform for a basketball team called "Snow Bear". This demonstrates how to use Snowflake Cortex AI functions to analyze fan survey data, extract sentiment insights, generate business recommendations, and create advanced analytics dashboards.

This Quickstart showcases the complete Snow Bear analytics platform with:
- **7-module interactive analytics platform** with Executive Dashboard, Fan Journey Explorer, Sentiment Analysis, Theme Analysis, Recommendation Engine, Interactive Search, and AI Assistant
- **AI-powered sentiment analysis** across 8 feedback categories
- **Advanced theme extraction** and automated categorization
- **Cortex Search Service** for semantic search
- **Cortex Analyst integration** for natural language queries
- **500+ real basketball fan survey responses**

### What You Will Build
- Complete 7-module interactive analytics platform
- AI-powered sentiment analysis system using real basketball fan data
- Advanced theme extraction and categorization engine
- Business recommendation system with simple and complex recommendations
- Interactive Cortex Search Service for semantic search
- Production-ready Streamlit application with advanced visualizations
- Stage-based data loading workflow for scalability

### What You Will Learn
- How to set up a production data pipeline with Snowflake stages
- How to use Snowflake Notebooks for complex AI processing workflows
- How to implement all Cortex AI functions (SENTIMENT, EXTRACT_ANSWER, COMPLETE)
- How to build scalable analytics platforms with real data
- How to create automated theme analysis and fan segmentation
- How to deploy interactive Streamlit applications in Snowflake

### Prerequisites
- Familiarity with Python and SQL
- Familiarity with Streamlit applications
- Go to the [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) sign-up page and register for a free account

<!-- ------------------------ -->
## Setup Snowflake Environment  
Duration: 5

In this step, you'll create the Snowflake database objects and upload all necessary files for the Snow Bear analytics platform.

### Step 1: Create Database Objects

1. In Snowsight, click `Worksheets` in the left navigation
2. Click `+` in the top-right corner and choose `SQL Worksheet`
3. Download the setup script: [setup.sql](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/setup.sql)
4. Copy and paste the entire script into your worksheet and run it

The setup script creates:
- **Database**: `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB` with Bronze and Gold schemas
- **Role**: `SNOW_BEAR_DATA_SCIENTIST` with all necessary permissions  
- **Warehouse**: `SNOW_BEAR_WH` for compute resources
- **Stage**: `SNOW_BEAR_DATA_STAGE` for file uploads
- **File Format**: `CSV_FORMAT` for data loading
- **AI Access**: `SNOWFLAKE.CORTEX_USER` role for Cortex functions

### Step 2: Download Required Files

Download these 2 files from the GitHub repository:

| File | Purpose | Download Link |
|------|---------|---------------|
| **Data File** | Basketball fan survey data | [basketball_fan_survey_data.csv.gz](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/basketball_fan_survey_data.csv.gz) |
| **Streamlit App** | Interactive analytics dashboard | [snow_bear.py](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/snow_bear.py) |

### Step 3: Upload Files to Stage

1. Navigate to `Data` → `Databases` → `SNOW_BEAR_DB` → `ANALYTICS` → `Stages`
2. Click on `SNOW_BEAR_DATA_STAGE`
3. Upload the 2 downloaded files to the stage

### Step 4: Import the Analytics Notebook

1. **Download the notebook**: [snow_bear_complete_setup.ipynb](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/notebooks/snow_bear_complete_setup.ipynb)

2. **Import into Snowflake**:
   - Navigate to `Projects` → `Notebooks` in Snowsight
   - Click the down arrow next to `+ Notebook` and select `Import .ipynb file`
   - Choose `snow_bear_complete_setup.ipynb` from your downloads

3. **Configure the notebook settings**:
   - **Role**: Select `SNOW_BEAR_DATA_SCIENTIST`
   - **Database**: Select `SNOW_BEAR_DB`
   - **Schema**: Select `ANALYTICS`  
   - **Query Warehouse**: Select `SNOW_BEAR_WH`
   - **Notebook Warehouse**: Select `SNOW_BEAR_WH`

4. **Click `Create`** to import the notebook

The notebook contains all the SQL scripts and processing logic needed for the complete analytics platform.


<!-- ------------------------ -->
## Run Analytics Notebook
Duration: 25

### Execute the Complete Analytics Workflow

1. Navigate to `Projects` → `Notebooks` in Snowsight
2. Open `snow_bear_complete_setup.ipynb`
3. Run all cells sequentially using `Shift + Enter`
4. Wait for each cell to complete before proceeding to the next
5. The complete workflow takes approximately 20-25 minutes

The notebook contains detailed explanations for each step and will process your data, apply AI analytics, and create your Streamlit dashboard.

<!-- ------------------------ -->
## Launch Analytics Dashboard
Duration: 5

### Access Your Analytics Platform

1. Navigate to `Projects` → `Streamlit` in Snowsight
2. Find and click on `Snow Bear Fan Analytics`
3. Explore your 7-module analytics dashboard

Your platform includes executive dashboards, sentiment analysis, theme analysis, fan segmentation, AI recommendations, interactive search, and AI assistant capabilities.

<!-- ------------------------ -->
## Clean Up Resources
Duration: 5

### Remove All Created Objects

When you're ready to remove all the resources created during this quickstart:

1. Open the [setup.sql](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/setup.sql) script
2. Scroll to the bottom to find the "TEARDOWN SCRIPT" section
3. Uncomment the teardown statements by removing the `/*` and `*/` comment blocks
4. Copy and paste the uncommented teardown statements into a new SQL Worksheet in Snowsight
5. Run the script to remove all databases, warehouses, roles, and objects

The teardown script automatically removes all created objects including:
- All databases, schemas, tables, and stages
- The analytics warehouse and role
- All notebooks (including "Snow Bear Complete Setup")
- All Streamlit apps (including "Snow Bear Fan Analytics")

No manual cleanup of individual apps or notebooks is needed.

<!-- ------------------------ -->
## Conclusion
Duration: 2

Congratulations! You've successfully built the complete Snow Bear Fan Experience Analytics platform using Snowflake Cortex AI!

### What You Built
- **7-Module Analytics Platform**: Executive Dashboard, Sentiment Analysis, Theme Analysis, Fan Segments, AI Recommendations, Interactive Search, and AI Assistant
- **Advanced AI Processing**: Complete Cortex AI integration with SENTIMENT, EXTRACT_ANSWER, and COMPLETE functions
- **Cortex Search Service**: Semantic search across fan feedback with natural language queries
- **Production-Ready Streamlit App**: Complete interactive dashboard with advanced visualizations
- **500+ Fan Records**: Realistic basketball fan survey data with comprehensive feedback

### Resources
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions)
- [Cortex Search Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-search)
- [Streamlit in Snowflake](https://docs.snowflake.com/developer-guide/streamlit/about-streamlit)
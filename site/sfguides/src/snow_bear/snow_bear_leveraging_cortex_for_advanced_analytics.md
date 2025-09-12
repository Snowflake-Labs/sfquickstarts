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
3. Copy the setup script below and paste it into your worksheet
4. Run the script to create all necessary objects

```sql
-- Snow Bear Analytics Setup Script
-- Creates database, schemas, roles, warehouse, stage, and grants permissions

-- Create database and schemas
CREATE OR REPLACE DATABASE CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB;
CREATE OR REPLACE SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER;
CREATE OR REPLACE SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.GOLD_LAYER;

-- Create role and warehouse
CREATE OR REPLACE ROLE SNOW_BEAR_DATA_SCIENTIST;
CREATE OR REPLACE WAREHOUSE SNOW_BEAR_ANALYTICS_WH 
  WITH WAREHOUSE_SIZE = 'MEDIUM'
  INITIALLY_SUSPENDED = TRUE
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- Grant permissions
GRANT USAGE ON DATABASE CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB TO ROLE SNOW_BEAR_DATA_SCIENTIST;
GRANT USAGE ON SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER TO ROLE SNOW_BEAR_DATA_SCIENTIST;
GRANT USAGE ON SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.GOLD_LAYER TO ROLE SNOW_BEAR_DATA_SCIENTIST;
GRANT ALL ON SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER TO ROLE SNOW_BEAR_DATA_SCIENTIST;
GRANT ALL ON SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.GOLD_LAYER TO ROLE SNOW_BEAR_DATA_SCIENTIST;
GRANT USAGE ON WAREHOUSE SNOW_BEAR_ANALYTICS_WH TO ROLE SNOW_BEAR_DATA_SCIENTIST;
GRANT ROLE SNOW_BEAR_DATA_SCIENTIST TO USER CURRENT_USER();

-- Grant Cortex AI access
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SNOW_BEAR_DATA_SCIENTIST;

-- Create stage for file uploads
USE SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER;
CREATE OR REPLACE STAGE SNOW_BEAR_DATA_STAGE;

-- Create file format for CSV loading
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  RECORD_DELIMITER = '\n'
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TRIM_SPACE = TRUE
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
  ESCAPE = 'NONE'
  ESCAPE_UNENCLOSED_FIELD = '\134'
  DATE_FORMAT = 'AUTO'
  TIMESTAMP_FORMAT = 'AUTO'
  NULL_IF = ('');

-- Create bronze layer table
CREATE OR REPLACE TABLE CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER.GENERATED_DATA_MAJOR_LEAGUE_BASKETBALL_STRUCTURED (
    ID NUMBER,
    REVIEW_DATE DATE,
    OVERALL_RATING NUMBER,
    FOOD_OFFERING_RATING NUMBER,
    GAME_EXPERIENCE_RATING NUMBER,
    PARKING_RATING NUMBER,
    MERCHANDISE_PRICING_RATING NUMBER,
    SECURITY_RATING NUMBER,
    TICKET_PRICING_RATING NUMBER,
    OVERALL_COMMENTS STRING,
    FOOD_OFFERING_COMMENTS STRING,
    GAME_EXPERIENCE_COMMENTS STRING,
    PARKING_COMMENTS STRING,
    MERCHANDISE_PRICING_COMMENTS STRING,
    SECURITY_COMMENTS STRING,
    TICKET_PRICING_COMMENTS STRING
);

-- Set role for subsequent operations
USE ROLE SNOW_BEAR_DATA_SCIENTIST;
USE WAREHOUSE SNOW_BEAR_ANALYTICS_WH;
```

The setup script creates:
- **Database**: `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB` with Bronze and Gold schemas
- **Role**: `SNOW_BEAR_DATA_SCIENTIST` with all necessary permissions  
- **Warehouse**: `SNOW_BEAR_ANALYTICS_WH` for compute resources
- **Stage**: `SNOW_BEAR_DATA_STAGE` for file uploads
- **File Format**: `CSV_FORMAT` for data loading
- **AI Access**: `SNOWFLAKE.CORTEX_USER` role for Cortex functions

### Step 2: Download Required Files

Download all 3 files from the GitHub repository:

| File | Purpose | Download Link |
|------|---------|---------------|
| **Data File** | Basketball fan survey data | [basketball_fan_survey_data.csv.gz](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/basketball_fan_survey_data.csv.gz) |
| **Notebook** | Complete AI processing workflow | [snow_bear_complete_setup.ipynb](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/notebooks/snow_bear_complete_setup.ipynb) |
| **Streamlit App** | Interactive analytics dashboard | [snow_bear_complete_app.py](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/snow_bear_complete_app.py) |

### Step 3: Upload Files to Stage

1. Navigate to `Data` → `Databases` → `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB` → `BRONZE_LAYER` → `Stages`
2. Click on `SNOW_BEAR_DATA_STAGE`
3. Upload all 3 downloaded files to the stage

### Step 4: Import the Notebook

1. Navigate to `Projects` → `Notebooks`
2. Click `Import .ipynb file`
3. Select `snow_bear_complete_setup.ipynb` from your downloads
4. Configure the notebook settings:
   - **Database**: Select `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB`
   - **Schema**: Select `GOLD_LAYER`
   - **Warehouse**: Select `SNOW_BEAR_ANALYTICS_WH`
5. Click `Create` to import the notebook


<!-- ------------------------ -->
## Run Analytics Notebook and Launch App
Duration: 30

### Step 1: Execute the Complete Analytics Workflow

1. **Navigate to Notebooks**: Go to `Projects` → `Notebooks` in Snowsight
2. **Open your imported notebook**: Click on `snow_bear_complete_setup.ipynb`
3. **Set the warehouse**: Ensure the warehouse is set to `SNOW_BEAR_ANALYTICS_WH`
4. **Run all cells sequentially**: 
   - Click on the first cell and press `Shift + Enter` to run it
   - Continue running each cell one by one until you reach the end
   - Wait for each cell to complete before moving to the next (you'll see a spinning indicator while running)
   - The entire notebook will take approximately 20-25 minutes to complete

The notebook will automatically:
- Load basketball fan data from the stage
- Apply Cortex SENTIMENT analysis across 8 feedback categories
- Extract and classify 20+ themes using Cortex AI
- Create intelligent fan segments with recommendations
- Build a Cortex Search service for natural language queries
- Create your Streamlit analytics dashboard
- Validate all processing completed successfully

### Step 2: Access Your Analytics Dashboard

After the notebook completes successfully:

1. **Navigate to Streamlit**: Go to `Projects` → `Streamlit` in Snowsight
2. **Find your app**: Look for `Snow Bear Fan Analytics` in the list of apps
3. **Launch the dashboard**: Click on the app name to open your analytics platform
4. **Explore the features**: Your dashboard includes 7 modules:
   - Executive Dashboard with key metrics
   - Sentiment Analysis with AI insights
   - Theme Analysis with automated categorization
   - Fan Segmentation with recommendations
   - AI-generated business recommendations
   - Interactive search with natural language queries
   - AI Assistant integration point

**Note**: If you don't see the app immediately, wait a few minutes as it may take time to appear after creation.

<!-- ------------------------ -->
## Conclusion
Duration: 5

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
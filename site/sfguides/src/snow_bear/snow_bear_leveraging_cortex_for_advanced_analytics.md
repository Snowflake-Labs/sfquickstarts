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

### Create Database Objects and Stage

1. **Navigate to Worksheets**: In Snowsight, click `Worksheets` in the left navigation, then click `+` in the top-right corner and choose `SQL Worksheet`

2. **Download the setup script**: Get the complete setup script from [snow_bear_setup.sql](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/snow_bear_setup.sql)

3. **Execute the setup script**: Copy and paste the entire script into your worksheet and run it

The setup script creates:
- **Database**: `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB` with Bronze and Gold layer schemas
- **Role**: `SNOW_BEAR_DATA_SCIENTIST` with all necessary permissions
- **Warehouse**: `SNOW_BEAR_ANALYTICS_WH` for compute resources
- **Stage**: `SNOW_BEAR_DATA_STAGE` for CSV file upload
- **File Format**: `CSV_FORMAT` for data loading
- **Cortex AI Access**: Grants `SNOWFLAKE.CORTEX_USER` role for AI functions

### Upload Files and Import Notebook

4. **Download required files**:
   - Data file: [basketball_fan_survey_data.csv.gz](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/basketball_fan_survey_data.csv.gz)
   - Processing notebook: [snow_bear_complete_setup.ipynb](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/notebooks/snow_bear_complete_setup.ipynb)
   - Streamlit app: [snow_bear_complete_app.py](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/snow_bear_complete_app.py)

5. **Upload files to stage**: 
   - Navigate to `Data` → `Databases` → `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB` → `BRONZE_LAYER` → `Stages` → `SNOW_BEAR_DATA_STAGE`
   - Click the stage name, then upload all 3 downloaded files:
     - `basketball_fan_survey_data.csv.gz` (data)
     - `snow_bear_complete_app.py` (Streamlit app)
     - `snow_bear_complete_setup.ipynb` (notebook)

6. **Import the notebook**: 
   - Navigate to `Projects` → `Notebooks`
   - Click `Import .ipynb file` and select `snow_bear_complete_setup.ipynb` from the stage
   - Set the warehouse to `SNOW_BEAR_ANALYTICS_WH`

✅ **Your Snowflake environment is now ready for the Snow Bear analytics platform!**

<!-- ------------------------ -->
## Use the Notebook for AI Processing
Duration: 20

### Run the Complete Setup Notebook

All AI-enhanced analytics processing is handled by the notebook for the best user experience.

1. **Open the notebook**: In Snowflake, navigate to Projects → Notebooks
2. **Import or create**: Import `snow_bear_complete_setup.ipynb` or create a new notebook
3. **Run all cells**: The notebook will automatically:
   - Verify your setup and data upload
   - Create the AI-enhanced analytics tables
   - Apply Cortex AI functions for sentiment analysis
   - Generate theme extraction and classification
   - Create fan segmentation
   - Set up business recommendations
   - Create the Cortex Search Service

### What the Notebook Does

The notebook handles all the complex SQL processing including:
- **Cortex SENTIMENT**: Analyzes fan feedback across 8 categories
- **Cortex EXTRACT_ANSWER**: Generates theme summaries for each comment
- **Gold layer creation**: Builds the comprehensive analytics table
- **Data validation**: Ensures all steps completed successfully

<!-- ------------------------ -->
## Continue with the Notebook
Duration: 15

### Theme Analysis, Fan Segmentation, and More

The notebook continues with advanced AI processing:

**Automated Theme Analysis:**
- Extracts 20+ recurring themes from all fan feedback
- Uses Cortex COMPLETE for intelligent theme classification
- Applies themes to individual fan records

**Fan Segmentation:**
- Creates multiple segmentation approaches
- Generates business-focused recommendations
- Uses AI to classify fans into actionable segments

**Cortex Search Setup:**
- Creates semantic search service
- Enables natural language queries on fan feedback
- Provides production-ready search capabilities

### Troubleshooting Notes

If you encounter issues in the notebook:
- **Permission errors**: Ensure SNOWFLAKE.CORTEX_USER role is granted
- **Timeout errors**: Some AI operations may take several minutes
- **Model errors**: Retry the cell or check Cortex model availability
- **Empty results**: Verify data was loaded correctly from the stage

<!-- ------------------------ -->
## Streamlit Application
Duration: 25

### Building the Full Snow Bear Analytics Platform

1. Navigate to Streamlit in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) by clicking on `Projects` → `Streamlit`

2. Switch Role to `SNOW_BEAR_DATA_SCIENTIST`

3. Click `+ Streamlit App` and configure:
   - **App name**: `Snow Bear Fan Analytics`
   - **Warehouse**: `SNOW_BEAR_ANALYTICS_WH`
   - **App location**: `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.GOLD_LAYER`

4. Replace the default code with the complete Snow Bear analytics application.

   **Option A - Use the file from your stage:**
   - Navigate to `Data` → `Databases` → `CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB` → `BRONZE_LAYER` → `Stages` → `SNOW_BEAR_DATA_STAGE`
   - Download `snow_bear_complete_app.py` from the stage
   - Copy the entire contents and paste into your Streamlit app editor

   **Option B - Download directly from GitHub:**
   - Download from: [snow_bear_complete_app.py](https://github.com/Snowflake-Labs/sfguide-snow-bear-fan-experience-analytics-leveraging-cortex/blob/main/scripts/snow_bear_complete_app.py)
   - Copy the entire contents and paste into your Streamlit app editor
   
   The application includes 7 comprehensive modules:
   - 🏠 **Dashboard**: Overview metrics and satisfaction distribution
   - 😊 **Sentiment Analysis**: AI-powered sentiment insights by theme
   - 🎯 **Theme Analysis**: AI theme classification and performance
   - 👥 **Fan Segments**: Segmentation analysis and theme preferences
   - 🤖 **AI Recommendations**: Cortex-generated improvement suggestions
   - 🔍 **Interactive Search**: Cortex Search for natural language queries
   - 🧠 **AI Assistant**: Integration point for Cortex Analyst

5. Click `Run` to launch your complete Snow Bear Analytics application

**✅ You now have a complete 7-module analytics platform powered by Snowflake Cortex AI!**

<!-- ------------------------ -->
## Testing Platform
Duration: 10

### Validating All Features

1. **Test Executive Dashboard**: Verify metrics, charts, and KPIs
2. **Explore Fan Journeys**: Use Fan Journey Explorer with different fan profiles  
3. **Review Sentiment Analysis**: Check AI sentiment scoring across categories
4. **Examine Theme Analysis**: Verify automated theme extraction
5. **Test Recommendation Engine**: Review AI-generated business recommendations
6. **Use Interactive Search**: Test Cortex Search with various queries
7. **Try AI Assistant**: Test natural language queries (if Cortex Analyst is configured)

### Performance Validation

The notebook includes validation queries to verify your implementation. Check that:

- **Fan Data**: 500+ records loaded from the CSV file
- **AI Processing**: Sentiment analysis completed across all categories  
- **Themes**: Theme extraction and classification completed
- **Segmentation**: Fan segments and recommendations generated
- **Search Service**: Cortex Search Service created and functional
- **Streamlit App**: All 7 modules working with real data

All validation is handled automatically by the notebook's final validation cell.

<!-- ------------------------ -->
## Clean Up
Duration: 2

### Remove Snowflake Objects

Execute the cleanup script to remove:
- Cortex Search Service
- Database and all objects
- Warehouse and role

*Cleanup script will be provided separately*

<!-- ------------------------ -->
## Conclusion
Duration: 5

### Conclusion
Congratulations! You've successfully built the complete Snow Bear Fan Experience Analytics platform using Snowflake Cortex AI!

### What You Built - Complete Feature Parity
- **✅ 7-Module Analytics Platform**: Executive Dashboard, Fan Journey Explorer, Sentiment Analysis, Theme Analysis, Recommendation Engine, Interactive Search, AI Assistant
- **✅ Advanced AI Processing**: Complete Cortex AI integration with SENTIMENT, EXTRACT_ANSWER, and COMPLETE functions
- **✅ Theme Extraction System**: Automated theme analysis with 20+ themes and fan classification
- **✅ Fan Segmentation**: Multi-dimensional segmentation with primary and alternative segments
- **✅ Business Recommendations**: Both simple and complex multi-tier recommendation systems
- **✅ Cortex Search Service**: Semantic search across fan feedback with natural language queries
- **✅ Production-Ready Streamlit App**: Complete 7-tab interface with advanced visualizations
- **✅ 500+ Fan Records**: Realistic basketball fan survey data with comprehensive feedback

### Technical Features Demonstrated
- **Multi-Model AI Processing**: SENTIMENT analysis across 8 categories
- **Advanced Theme Extraction**: AI-powered categorization and classification
- **Intelligent Segmentation**: Multiple segmentation approaches for fan profiling
- **Business Intelligence**: Revenue-focused recommendation generation
- **Semantic Search**: Natural language search across unstructured feedback
- **Interactive Analytics**: Real-time filtering, drilling, and exploration
- **Production Architecture**: Bronze-to-Gold data processing with AI enhancement

### Next Steps
- **Scale Up**: Load the complete 500+ record dataset
- **Customize**: Adapt for your specific sports team or organization
- **Extend**: Add Cortex Analyst for natural language SQL generation
- **Deploy**: Package as a Snowflake Native App for distribution
- **Integrate**: Connect with your existing customer feedback systems

### Resources
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions)
- [Cortex Search Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-analyst)
- [Streamlit in Snowflake](https://docs.snowflake.com/developer-guide/streamlit/about-streamlit)
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/overview)
- [Snow Bear Analytics - Complete Implementation](https://github.com/Snowflake-Labs/sfguide-snow-bear-analytics)
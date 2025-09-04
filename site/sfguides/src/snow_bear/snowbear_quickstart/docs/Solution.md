# ❄️🏀 Snow Bear Fan Experience Analytics

## Access Instructions

### Open the Analytics Application

**1.)** Open Snowsight:

{{ snowsight_button() }}

**2.)** Switch to role: `{{ DATAOPS_CATALOG_SOLUTION_PREFIX }}_DATA_SCIENTIST`
   
**3.)** Navigate to: **Streamlit** > **{{ DATAOPS_CATALOG_SOLUTION_PREFIX }}_SNOWBEAR_FAN_360**


### Application Overview

The analytics platform contains 7 analysis modules:

1. **📊 Executive Dashboard** - High-level metrics, trends, and KPIs for business leaders
2. **👥 Fan Journey Explorer** - Individual fan profiles and experience deep-dives  
3. **💭 Sentiment Deep Dive** - AI-powered sentiment analysis across all touchpoints
4. **🎯 Theme & Segment Analysis** - Automated theme categorization and fan segmentation
5. **🚀 Recommendation Engine** - AI-generated business improvement suggestions
6. **🔍 Interactive Search** - Cortex Search for natural language queries
7. **🧠 AI Assistant** - Cortex Analyst for ad-hoc data exploration with natural language

### Key Features to Explore

- **AI-Powered Insights**: Cortex AI automatically extracts themes, analyzes sentiment, and generates business recommendations
- **Interactive Dashboards**: Filter and drill down into specific fan segments, themes, and time periods
- **Natural Language Search**: Use the Interactive Search tab to ask questions like "Show me fans with parking issues"
- **Cortex Analyst**: Ask complex questions like "What are the top pain points by month in 2024?" in the AI Assistant tab

### Dataset Information

Contains 500 synthetic basketball fan survey responses with:
- Multi-dimensional feedback across 8 categories
- Automated sentiment analysis results
- AI-generated theme classifications  
- Business recommendations from Cortex COMPLETE

### Technical Notes

- All Cortex AI functions demonstrated: SENTIMENT, EXTRACT_ANSWER, COMPLETE
- Cortex Search Service configured for semantic search
- Cortex Analyst enabled for natural language SQL generation
- Sample queries and interactions available in each module

author: Josh Klahr, Chanin Nantasenamat
id: snowflake-semantic-view-autopilot
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics
language: en
summary: Learn how to go from raw campaign data to a fully usable Snowflake Semantic View and seamlessly consume it in Tableau.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Build Semantic Views and Connect to Tableau with Snowflake
<!-- ------------------------ -->
## Overview

Welcome to this hands-on guide! In this session, we'll walk you through an end-to-end journey that shows how to go from raw campaign data to a fully usable **Snowflake Semantic View** and seamlessly consume it in **Tableau**.

This guide is designed to be practical and visual—you'll follow along in a Snowflake Notebook and see how each piece fits together in a modern analytics workflow.

### What You'll Learn
- How to load and explore campaign data in Snowflake
- How to automatically generate a Semantic View using the Semantic View Wizard
- How to query Semantic Views using standard SQL
- How to generate a Tableau Data Source (`.tds`) file from a Semantic View
- How to connect Tableau to Snowflake using the generated Semantic View

### What You'll Build

By the end of this guide, you will have:
- A fully functional marketing analytics database with dimension and fact tables
- A Semantic View generated from an existing Tableau workbook
- A Tableau Data Source file that connects directly to your Semantic View

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Snowflake account with ACCOUNTADMIN role (or equivalent privileges)
- Tableau Desktop installed (for the Tableau integration section)
- Basic familiarity with SQL and Snowflake UI

### Access the Notebook

You can follow along with this guide using the companion Snowflake Notebook:

1. Download the notebook from GitHub: [Semantic_View_Autopilot.ipynb](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Snowflake_Semantic_View_Autopilot/Semantic_View_Autopilot.ipynb)
2. In Snowsight, navigate to **Projects > Notebooks**
3. Click the down arrow next to **+ Notebook** and select **Import .ipynb file**
4. Upload the downloaded notebook file
5. Select a database, schema, and warehouse for the notebook
6. Click **Create** to import the notebook

<!-- ------------------------ -->
## Architecture

The Semantic View Autopilot workflow follows this architecture:

```
┌──────────────────────┐                 ┌────────────────────────────┐
│  Campaign Data       │                 │ Existing Tableau Workbook  │
│  (Snowflake Tables)  │                 │ (.twb file)                │
└──────────┬───────────┘                 └─────────────┬──────────────┘
           │                                           │
           ▼                                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Semantic View Autopilot "Fast-Gen"                                   │
│ (Generate Semantic View from existing analytics)                     │
└──────────┬───────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐                 ┌────────────────────────────┐
│ Snowflake Semantic   │                 │ Query History              │
│ View (Metrics + Dims)│                 │ (Real Usage Patterns)      │
└──────────┬───────────┘                 └─────────────┬──────────────┘
           │                                           │
           ▼                                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Semantic View Autopilot                                              │
│ (Suggest verified queries using usage patterns)                      │
└──────────┬───────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Downstream Consumers                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Snowflake   │  │ Cortex      │  │ Tableau     │  │ Any SQL     │ │
│  │ Intelligence│  │ Analyst API │  │ (via .tds)  │  │ Client      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

<!-- ------------------------ -->
## Setup Environment

### Create Database and Schema

First, let's set up the database and schema for our marketing analytics data. Run the following SQL in a Snowflake worksheet or notebook:

```sql
-- Switch to accountadmin role to create db, schema, and load data
USE ROLE ACCOUNTADMIN;

-- Create database and schema
CREATE OR REPLACE DATABASE SVA_VHOL_DB;
USE DATABASE SVA_VHOL_DB;

CREATE SCHEMA IF NOT EXISTS SVA_VHOL_SCHEMA;
USE SCHEMA SVA_VHOL_SCHEMA;

-- Optional: allow anyone to see the agents in this schema
GRANT USAGE ON DATABASE SVA_VHOL_DB TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA SVA_VHOL_DB.SVA_VHOL_SCHEMA TO ROLE PUBLIC;
```

### Create File Format

Create a file format for loading CSV data:

```sql
-- Create file format for CSV files
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
    DATE_FORMAT = 'YYYY-MM-DD'
    TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
    NULL_IF = ('NULL', 'null', '', 'N/A', 'n/a');
```

<!-- ------------------------ -->
## Load Marketing Data

### Set Up Git Integration

Create an API integration and Git repository to access the demo data:

```sql
-- Create API Integration for GitHub (public repository access)
CREATE OR REPLACE API INTEGRATION git_api_integration
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/NickAkincilar/')
    ENABLED = TRUE;
    
-- Create Git repository integration for the public demo repository
CREATE OR REPLACE GIT REPOSITORY SVA_VHOL_REPO
    API_INTEGRATION = git_api_integration
    ORIGIN = 'https://github.com/NickAkincilar/Snowflake_AI_DEMO.git';

-- Create internal stage for copied data files
CREATE OR REPLACE STAGE INTERNAL_DATA_STAGE
    FILE_FORMAT = CSV_FORMAT
    COMMENT = 'Internal stage for copied demo data files'
    DIRECTORY = ( ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

### Copy Data Files

Fetch the repository and copy data files to the internal stage:

```sql
-- Fetch the latest from the repository
ALTER GIT REPOSITORY SVA_VHOL_REPO FETCH;

-- Copy data files from Git repository to internal stage
COPY FILES 
    INTO @INTERNAL_DATA_STAGE
    FROM @SVA_VHOL_REPO/branches/main/data/;

-- Copy unstructured docs (including Tableau workbook)
COPY FILES 
    INTO @INTERNAL_DATA_STAGE/unstructured_docs/
    FROM @SVA_VHOL_REPO/branches/main/unstructured_docs/;

-- Refresh directory table
ALTER STAGE INTERNAL_DATA_STAGE REFRESH;
```

### Create Dimension Tables

Create the dimension tables for campaigns, channels, and products:

```sql
-- Create CAMPAIGN_DIM table
CREATE OR REPLACE TABLE CAMPAIGN_DIM (
    campaign_key INT,
    campaign_id VARCHAR(50),
    campaign_name VARCHAR(200),
    objective VARCHAR(100),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15,2),
    status VARCHAR(50)
);

COPY INTO CAMPAIGN_DIM
FROM @INTERNAL_DATA_STAGE/campaign_dim.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';

-- Create CHANNEL_DIM table
CREATE OR REPLACE TABLE CHANNEL_DIM (
    channel_key INT,
    channel_id VARCHAR(50),
    channel_name VARCHAR(100),
    channel_type VARCHAR(50),
    platform VARCHAR(100)
);

COPY INTO CHANNEL_DIM
FROM @INTERNAL_DATA_STAGE/channel_dim.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';

-- Create PRODUCT_DIM table
CREATE OR REPLACE TABLE PRODUCT_DIM (
    product_key INT,
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    price DECIMAL(10,2)
);

COPY INTO PRODUCT_DIM
FROM @INTERNAL_DATA_STAGE/product_dim.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';
```

### Create Fact Table

Create the marketing campaign fact table:

```sql
-- Create MARKETING_CAMPAIGN_FACT table
CREATE OR REPLACE TABLE MARKETING_CAMPAIGN_FACT (
    fact_key INT,
    date DATE,
    campaign_key INT,
    channel_key INT,
    product_key INT,
    impressions INT,
    clicks INT,
    spend DECIMAL(15,2),
    conversions INT,
    revenue DECIMAL(15,2),
    leads_generated INT
);

COPY INTO MARKETING_CAMPAIGN_FACT
FROM @INTERNAL_DATA_STAGE/marketing_campaign_fact.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';
```

### Verify Data Load

Verify the tables were created successfully:

```sql
-- List the tables
SHOW TABLES;
```

<!-- ------------------------ -->
## Run Sample Queries

Before creating the Semantic View, let's run some sample queries that the Semantic View Autopilot can use to suggest model improvements and verified queries.

### Marketing Performance by Month

```sql
SELECT
    DATE_TRUNC('month', mcf.date) AS month,
    SUM(mcf.spend) AS total_spend,
    SUM(mcf.impressions) AS total_impressions,
    SUM(mcf.leads_generated) AS total_leads,
    SUM(mcf.spend) / NULLIF(SUM(mcf.leads_generated), 0) AS cost_per_lead,
    SUM(mcf.leads_generated) / NULLIF(SUM(mcf.impressions), 0) AS lead_conversion_rate
FROM MARKETING_CAMPAIGN_FACT mcf
GROUP BY 1
ORDER BY 1;
```

### Channel Efficiency Analysis

```sql
SELECT
    cd.channel_name,
    SUM(mcf.spend) AS total_spend,
    SUM(mcf.leads_generated) AS total_leads,
    SUM(mcf.spend) / NULLIF(SUM(mcf.leads_generated), 0) AS cost_per_lead
FROM MARKETING_CAMPAIGN_FACT mcf
JOIN CHANNEL_DIM cd ON mcf.channel_key = cd.channel_key
GROUP BY 1
HAVING SUM(mcf.leads_generated) > 0
ORDER BY cost_per_lead ASC, total_leads DESC;
```

### Top Campaigns by Leads

```sql
SELECT
    c.campaign_name,
    c.objective,
    SUM(mcf.leads_generated) AS total_leads,
    SUM(mcf.spend) AS total_spend,
    SUM(mcf.impressions) AS total_impressions,
    SUM(mcf.spend) / NULLIF(SUM(mcf.leads_generated), 0) AS cpl
FROM MARKETING_CAMPAIGN_FACT mcf
JOIN CAMPAIGN_DIM c ON mcf.campaign_key = c.campaign_key
GROUP BY 1, 2
ORDER BY total_leads DESC
LIMIT 10;
```

<!-- ------------------------ -->
## Create Semantic View

### Use the Semantic View Wizard

Now let's create a Semantic View using the Semantic View Wizard with an existing Tableau workbook as context:

1. Navigate to the Semantic View wizard by going to **"AI & ML > Analyst"** from the left side menu in Snowflake
2. Pick `SVA_VHOL_DB.SVA_VHOL_SCHEMA` from the dropdown
3. Select **"Create New Semantic View"**

Note: Be sure to use the `ACCOUNTADMIN` role or a role that has ownership rights on `SVA_VHOL_DB.SVA_VHOL_SCHEMA`.

4. Name your semantic view `SVA_MARKETING_SV` and click **"Next"**
5. In the following screen, select **"Tableau Files"** as your context
6. Pick `SVA_VHOL_SCHEMA.INTERNAL_DATA_STAGE` and navigate to the `/unstructured_docs/BI_dashboards` folder
7. Select the `CampaignMetricsDash.twb` file and click **"Create and Save"**

### Test the Semantic View

On the next screen you will see a "first pass" version of a Snowflake Semantic View based on the imported `.twb` file.

Test it out by going to the **"Playground"** tab in the right-hand panel and asking:

*"Show me the top 10 most expensive products based on cost per lead"*

Congratulations! You just went from "zero-to-semantic-view" in 1 minute!

<!-- ------------------------ -->
## Query with Standard SQL

### Understanding Standard SQL for Semantic Views

Semantic View [Standard SQL](https://docs.snowflake.com/en/user-guide/views-semantic/querying#specifying-the-name-of-the-semantic-view-in-the-from-clause) in Snowflake allows you to write ANSI-style SQL queries against semantic views.

### Example Query

```sql
-- Switch to the correct context
USE ROLE ACCOUNTADMIN;
USE DATABASE SVA_VHOL_DB;
USE SCHEMA SVA_VHOL_SCHEMA;

-- Standard SQL query against the semantic view
SELECT
   -- dimensions and facts can be selected directly
   product_name,
   -- metrics must be aggregated using AGG, MIN, MAX, or ANYVALUE
   AGG(cost_per_lead) as total_cost_per_lead
FROM
   -- directly reference the semantic view name
   SVA_MARKETING_SV
-- you must include a GROUP BY if your SELECT statement includes any metrics
GROUP BY ALL
ORDER BY total_cost_per_lead DESC
LIMIT 10;
```

Note: When querying Semantic Views with Standard SQL, remember:
- Dimensions and facts can be selected directly
- Metrics must be aggregated using `AGG`, `MIN`, `MAX`, or `ANYVALUE`
- You must include a `GROUP BY` clause if your SELECT statement includes any metrics

<!-- ------------------------ -->
## Generate Tableau TDS File

### About the TDS Export Function

Snowflake has a system function that automatically generates a Tableau Data Source (`.tds`) file that points directly to the relevant Snowflake Semantic View with:
- A pre-configured connection
- Folders for organization
- Well-mapped metrics and dimensions

You can generate a TDS file with this statement:

```sql
SELECT SYSTEM$EXPORT_TDS_FROM_SEMANTIC_VIEW('SVA_VHOL_DB.SVA_VHOL_SCHEMA.SVA_MARKETING_SV');
```

### Using the TDS Generator App

For a more user-friendly experience, you can use the following Python code in a Snowflake Notebook to generate and download the TDS file:

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

def generate_and_download_tds():
    """Clean interface for TDS generation and download"""
    
    st.title("TDS Generator")
    st.write("Generate Tableau Data Source files from Snowflake Semantic Views")
    
    # Input section
    semantic_view = st.text_input(
        "Semantic View Name",
        value="SVA_VHOL_DB.SVA_VHOL_SCHEMA.SVA_MARKETING_SV",
        help="Enter the fully qualified semantic view name"
    )
    
    if st.button("Generate TDS", type="primary"):
        if not semantic_view:
            st.error("Please enter a semantic view name")
            return
            
        try:
            # Get Snowflake session
            session = get_active_session()
            
            # Call the system function
            with st.spinner("Generating TDS file..."):
                result = session.sql(
                    f"SELECT SYSTEM$EXPORT_TDS_FROM_SEMANTIC_VIEW('{semantic_view}');"
                ).collect()
                tds_content = result[0][0]
            
            # Check for errors
            if tds_content.startswith("<!-- Error"):
                st.error(f"Generation failed: {tds_content}")
                return
            
            # Success - show download
            st.success("TDS file generated successfully")
            
            # Create filename
            view_name = semantic_view.split('.')[-1] if '.' in semantic_view else semantic_view
            filename = f"{view_name}_Semantic_View.tds"
            
            # Download button
            st.download_button(
                label="Download TDS",
                data=tds_content,
                file_name=filename,
                mime="application/xml"
            )
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Run the app
generate_and_download_tds()
```

Run this cell and click **"Generate TDS"**, then open the `.tds` file using Tableau!

<!-- ------------------------ -->
## Connect Tableau

### Open the TDS File

1. Locate the downloaded `.tds` file on your computer
2. Double-click the file to open it in Tableau Desktop
3. Tableau will automatically connect to Snowflake using the pre-configured connection settings

### Authenticate to Snowflake

When prompted, enter your Snowflake credentials to authenticate the connection.

### Explore Your Data

Once connected, you'll see:
- All dimensions and metrics from your Semantic View organized in folders
- Pre-configured relationships and hierarchies
- Ready-to-use calculated fields based on your Semantic View metrics

You can now build visualizations and dashboards using the semantic layer you created in Snowflake!

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built an end-to-end workflow from raw campaign data to a fully functional Snowflake Semantic View, and connected it to Tableau for visualization. You've learned how to leverage the Semantic View Wizard to quickly generate semantic models from existing Tableau workbooks.

### What You Learned
- How to set up a Snowflake environment for marketing analytics data
- How to create a Semantic View using the Semantic View Wizard with Tableau workbook context
- How to query Semantic Views using standard SQL
- How to generate and use Tableau Data Source files from Semantic Views

### Related Resources

Documentation:
- [Overview of semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- [Semantic View Autopilot](https://docs.snowflake.com/en/user-guide/views-semantic/autopilot)
- [Querying semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/querying)

Happy analyzing!

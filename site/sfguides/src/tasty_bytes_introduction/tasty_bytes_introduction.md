author: Jacob Kranzler
id: tasty_bytes_introduction
summary: This is the Tasty Bytes Introduction and Data Foundation Quickstart guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Data Warehouse

<!-- ------------------------ -->

## Tasty Bytes - Introduction 
<img src="assets/tasty_bytes_header.png"/>

### Overview
Within this Tasty Bytes Introduction Quickstart you will first be learning about the fictious food truck brand, Tasty Bytes, created by the frostbyte team within the Snowflake Field CTO Office. 

After learning about the Tasty Bytes Organization, we will walk through the process of downloading a .sql file and importing it as a Worksheet in the Snowsight UI. This .sql file will then be ran in bulk which will complete the process of setting up a three zone (*raw, harmonized and analytics*) Tasty Bytes Data Model complete with Schemas, Tables, Views, Warehouses, Roles and all required Role Based Access Control (RBAC).

Upon finishing this Quickstart, you will be able to move on to the other Tasty Bytes Quickstarts seen in the Table of Contents section. These Tasty Bytes themed Quickstarts range from quick Zero to Snowflake feature/function rich walkthroughs to in-depth Workload Deep Dives.

### Who is Tasty Bytes?
<img src="assets/who_is_tasty_bytes.png"/>

### Prerequisites
- An Enterprise or Business Critical Snowflake Account
    - If you do not have a Snowflake Account, please [**sign up for a Free 30 Day Trial Account**](https://signup.snowflake.com/), select **Enterprise** edition and any Cloud/Region combination. After registering, you will receive an email with an activation link and your Snowflake Account URL.
    - <img src="assets/choose_edition.png" width="300"/>
    
### What You Will Learn 
1. How to Create a Snowflake Worksheet
2. How to Import a .sql File into a Snowflake Worksheet
3. How to Execute All Queries within a Snowflake Worksheet Synchronously
4. How to Explore Databases in your Snowflake Account
5. How to Explore Roles in your Snowflake Account
6. How to Explore Warehouse in your Snowflake Account

### What You Will Build
1. A Snowflake Database
2. Three Snowflake Schemas (Raw, Harmonized and Analytics) complete with Tables and Views
3. Workload Specific Snowflake Warehouses
4. Workload Specific Snowflake Roles

## Tasty Bytes - Quickstart Table of Contents
- The following Table of Contents covers the other Quickstart assets you can complete once you have finished all of the steps within this Quickstart. 

### Zero to Snowflake
- ### [Financial Governance](site/sfguides/src/tasty_bytes_zero_to_snowflake_financial_governance)
    - Learn about Snowflake Virtual Warehouses and their configurabilities, Resource Monitors, and Account and Warehouse Level Timeout Parameters
- ### [Transformation](site/sfguides/src/tasty_bytes_zero_to_snowflake_transformation)
    - Learn about Snowflake Zero Copy Cloning, Result Set Cache, Table Manipulation, Time-Travel and Table level SWAP, DROP and Undrop functionality.
- ### [Semi-Structured Data](site/sfguides/src/tasty_bytes_zero_to_snowflake_semi_structured_data)
    - Learn about Snowflake VARIANT Data Type, Semi-Structured Data Processing via Dot Notation and Lateral Flattening as well as View Creation and Snowsight Charting.
- ### [Data Governance](site/sfguides/src/tasty_bytes_zero_to_snowflake_data_governance)
    - Learn about Snowflake System Defined Roles, Create and apply GRANTS to a custom role, and deploy both Tag Based Dynamic Data Masking and Row-Access Policies.
- ### [Collaboration](site/sfguides/src/tasty_bytes_zero_to_snowflake_collaboration)
    - Learn about the Snowflake Marketplace by leveraging free, instantly available, live listings from Weathersource and Safegraph to conduct data driven analysis harmonizing first and third party sources.
- ### [Geospatial](site/sfguides/src/tasty_bytes_zero_to_snowflake_geospatial)
    - Learn about Snowflake Geospatial support starting with constructing Geographic Points (ST_POINT) and leveraging other Geospatial functionality to calculate distance (ST_DISTANCE), collect coordinates, draw a Minimum Bounding Polygon and find the polygons center point.

### Workload Deep Dives
- ### Data Engineering
    - ### Ingestion, Optimization & Automation (*Coming Soon*)
    - ### External Tables (*Coming Soon*)
- ### Data Science
    - ### Snowpark 101 (*Coming Soon*)

## Tasty Bytes - Setup
#### Overview
For this Quickstart, you will use the Snowflake web interface known as Snowsight. If this is your first time leveraging Snowsight we would highly consider taking a look at our [Snowsight Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight) for a high-level walkthrough.

#### Step 1 
-  Open a browser window and enter the URL of your Snowflake Account 

#### Step 2 
- Log into your Snowflake account.
    - <img src ="assets/log_into_snowflake.gif" width = "300"/>

#### Step 3 
- Click on [Worksheets](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs) Tab in the left-hand navigation bar.
    - <img src ="assets/worksheet_tab.png" width="250"/>

#### Step 4
- Within Worksheets, click the "+" button in the top-right corner of Snowsight and choose "SQL Worksheet"
    - <img src = "assets/+_sqlworksheet.png" width ="200">

#### Step 5
- Rename the Worksheet "Tasty Bytes - Setup"
    - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>

#### Step 6
- Click the button below to access the tasty_bytes_introduction.sql file that is hosted in GitHub.
<button>[tasty_bytes_introduction.sql](https://github.com/sfc-gh-jkranzler/sfquickstarts/blob/master/site/sfguides/src/tasty_bytes_introduction/assets/tasty_bytes_introduction.sql)</button>

#### Step 7 
- Within GitHub navigate to the right side and click "Copy raw contents".
    - <img src ="assets/github_copy_raw_contents.png"/>

#### Step 8 
- Path back to Snowsight and your newly created Worksheet and paste (CMD + V for Mac or CTRL + V for Windows) the contents of the tasty_bytes_introduction.sql file we copied from GitHub.

#### Step 9 
- Click inside the newly created worksheet, Select All (*CMD + A for Mac or CTRL + A for Windows*) and Click Run 
    - <img src ="assets/run_all_queries.gif"/>

#### Step 10
- After clicking Run you will see queries begin to execute. The entire run process should take around XYZ minutes and finish with a message stating XYZ message. Once this is complete, you can move onto the next section. 

## Tasty Bytes - Database and Database Objects

## Tasty Bytes - Warehouses

## Tasty Bytes - Roles








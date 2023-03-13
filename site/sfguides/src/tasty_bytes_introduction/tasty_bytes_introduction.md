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

Within this Tasty Bytes Introduction Quickstart you will first be learning about the fictious food truck brand, Tasty Bytes, created by the frostbyte team within the Snowflake Field CTO Office. 

After learning about the Tasty Bytes Organization, we will walk through the process of downloading a .sql file and importing it as a Worksheet in the Snowsight UI. This .sql file will then be ran in bulk which will complete the process of setting up a three zone (*raw, harmonized and analytics*) Tasty Bytes Data Model complete with Schemas, Tables, Views, Warehouses, Roles and all required Role Based Access Control (RBAC).

Upon finishing this Quickstart, you will be able to move on to the other Tasty Bytes Quickstarts seen in the Table of Contents section. These Tasty Bytes themed Quickstarts range from quick Zero to Snowflake feature/function rich walkthroughs to in-depth Workload Deep Dives.

### Who is Tasty Bytes?
<img src="assets/who_is_tasty_bytes.png"/>

### Prerequisites
- An Enterprise or Business Critical Snowflake Account
    - If you do not have a Snowflake Account, please [**sign up for a Free 30 Day Trial Account**](https://signup.snowflake.com/), select **Enterprise** edition and any Cloud/Region combination. After registering, you will receive an email with an activation link and your Snowflake Account URL.
<p align="center">
    <img src="assets/choose_edition.png" width="300"/>
</p>
       

### What You’ll Learn 
    - How to Create a Snowflake Worksheet
    - How to Import a .sql File into a Snowflake Worksheet
    - How to Execute an entire Snowflake Worksheet
    - How to Explore Databases in your Snowflake Account
    - How to Explore Roles in your Snowflake Account
    - How to Explore Warehouse in your Snowflake Account

### What You'll Build
- A Snowflake Database
- Three Snowflake Schemas (Raw, Harmonized and Analytics) complete with Tables and Views
- Workload Specific Snowflake Warehouses
- Workload Specific Snowflake Roles


## Tasty Bytes - Quickstart Table of Contents
The following Table of Contents covers the other Quickstarts you can complete once you have finished all of the steps within this Quickstart. 

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
- ### Data Engineering**
    - ### Ingestion, Optimization & Automation (*Coming Soon*)
    - ### External Tables (*Coming Soon*)
- ### Data Science**
    - ### Snowpark 101 (*Coming Soon*)

## Tasty Bytes - Setup
For this Quickstart, you will use the Snowflake web interface known as [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight).

**Step 1** - Download the [**tasty_bytes_introduction.sql**]() file 
#ToDo: find easiest way to download a .sql file

**Step 2** - Open a browser window and enter the URL of your existing Snowflake Account or the URL for the Snowflake 30-day Trial Account that was sent with your registration email.

**Step 3** - Log into your Snowflake account.
<p align="center">  
    <img src ="assets/log_into_snowflake.gif"/>
<p/>

**Step 4** - Click on [Worksheets](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs) Tab in the left-hand navigation bar.
<p align="center">  
    <img src ="assets/worksheet_tab.png" width="200"/>
<p/>

**Step 5** - Click on the "•••" button in the top-right and choose "Create Worksheet from SQL File"
<p align="center">  
    <img src ="assets/create_worksheet_from_sql.png" width="300"/>
<p/>

**Step 6** - Navigate to the location you saved your **tasty_bytes_introduction.sql** file and open it.


**Step 7** - Click inside the newly created worksheet, Select All (*Cmd + A - Mac | Ctrl + A - Windows*) and Click Run 
<p align="center">  
    <img src ="assets/run_all_queries.gif"/>
<p/>

## 4








author: Jacob Kranzler
id: tasty_bytes_introduction
summary: This is the Tasty Bytes Introduction and Data Foundation Quickstart guide
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake

# An Introduction to Tasty Bytes
<!-- ------------------------ -->

## An Introduction to Tasty Bytes 
Duration: 1
<img src="assets/tasty_bytes_header.png"/>

### Overview
Within this Tasty Bytes Introduction Quickstart you will first be learning about the fictious food truck brand, Tasty Bytes, created by the frostbyte team at Snowflake.

After learning about the Tasty Bytes Organization, we will complete the process of setting up the Tasty Bytes Foundational Data Model, Workload Specific Roles + Warehouses and all necessary Role Based Access Control (RBAC). 

Upon finishing this Quickstart, you will have deployed the foundation required to run the assets seen in Section 4 - Powered by Tasty Bytes - Quickstarts.

### Who is Tasty Bytes?
<img src="assets/who_is_tasty_bytes.png"/>

### Prerequisites
- A Supported Snowflake [Browser](https://docs.snowflake.com/en/user-guide/setup#browser-requirements)
- An Enterprise or Business Critical Snowflake Account
    - If you do not have a Snowflake Account, please [**sign up for a Free 30 Day Trial Account**](https://signup.snowflake.com/). When signing up, please make sure to select **Enterprise** edition. You are welcome to choose any [Snowflake Cloud/Region](https://docs.snowflake.com/en/user-guide/intro-regions).
    - After registering, you will receive an email with an activation link and your Snowflake Account URL.
    - <img src="assets/choose_edition.png" width="300"/>
    
### What You Will Learn 
- How to Create a Snowflake Worksheet
- How to Execute All Queries within a Snowflake Worksheet Synchronously
- How to Explore Databases, Schemas, Tables, Roles and Warehouses via SQL in a Snowflake Worksheet

### What You Will Build
- The Tasty Bytes Foundation that empowers you to run Powered by Tasty Bytes - Quickstarts. 
    - A Snowflake Database
    - Three Snowflake Schemas complete with Tables and Views
    - Workload Specific Snowflake Roles and Warehouses
    - Role Based Access Control (RBAC)

## Setting up Tasty Bytes
Duration: 6

### Overview
For this Quickstart, you will use the Snowflake web interface known as Snowsight. If this is your first time leveraging Snowsight we would highly consider taking a look at our [Snowsight Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight) for a high-level walkthrough.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account 

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.
    - <img src ="assets/log_into_snowflake.gif" width = "300"/>

### Step 3 - Navigating to Worksheets
- Click on the Worksheets Tab in the left-hand navigation bar.
    - <img src ="assets/worksheet_tab.png" width="250"/>

### Step 4 - Creating a Worksheet
- Within Worksheets, click the "+" button in the top-right corner of Snowsight and choose "SQL Worksheet"
    - <img src = "assets/+_sqlworksheet.png" width ="200">

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Setup"
    - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>

### Step 6 - Accessing hosted Setup SQL in GitHub
- Click the button below which will direct you to our Tasty Bytes SQL Setup file that is hosted on GitHub.
<button>[tasty_bytes_introduction.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/tasty_bytes_introduction/assets/tasty_bytes_introduction.sql)</button>

### Step 7 - Copying Setup SQL from GitHub
- Within GitHub navigate to the right side and click "Copy raw contents". This will copy all of the required SQL into your clipboard.
    - <img src ="assets/github_copy_raw_contents.png"/>

### Step 8 - Pasting Setup SQL from GitHub into your Snowflake Worksheet
- Path back to Snowsight and your newly created Worksheet and Paste (*CMD + V for Mac or CTRL + V for Windows*) what we just copied from GitHub.

### Step 9 - Synchronously Running all Setup SQL
- Click inside the newly created Tasty Bytes - Setup Worksheet, Select All (*CMD + A for Mac or CTRL + A for Windows*) and Click "► Run" 
    - <img src ="assets/run_all_queries.gif"/>

### Step 10 - Completing Setup
- After clicking "► Run" you will see queries begin to execute. These queries will run one after another with the entire worksheet taking around 5 minutes. Upon completion you will see a message stating *frostbyte_tasty_bytes setup database is now complete*. 
    - <img src="assets/setup_complete.png">

### Step 11 - Click Next -->

## Exploring the Tasty Bytes Foundation
Duration: 3

With our SQL Setup successful, let's now explore the Database, Roles and Warehouses within our Snowsight interface.
    - Within the Tasty Bytes - Setup worksheet you created in Step 2, please scroll to the bottom and Copy and Run the SQL from within each step below.

#### Step 1 - Exploring the Tasty Bytes Database
- This query will return the Database we created via [SHOW DATABASES](https://docs.snowflake.com/en/sql-reference/sql/show-databases.html).
```
SHOW DATABASES LIKE 'frostbyte_tasty_bytes';
```
<img src = "assets/show_tb_db.png"> 

#### Step 2 - Exploring the Schemas within the Tasty Bytes Database
- This query will return the Schemas within the Database we created via [SHOW SCHEMAS](https://docs.snowflake.com/en/sql-reference/sql/show-schemas) 
```
SHOW SCHEMAS IN DATABASE frostbyte_tasty_bytes;
```
<img src = "assets/show_tb_schemas.png"> 

#### Step 3 - Exploring the Tables within the RAW_POS Schema within the Tasty Bytes Database
- This query will return the Tables within the `raw_pos` schema via [SHOW TABLES](https://docs.snowflake.com/en/sql-reference/sql/show-tables)
```
SHOW TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos;
```
<img src = "assets/show_tb_tables.png"> 

#### Step 4 - Exploring the Tasty Bytes Roles
- This query will return the Roles we created via [SHOW ROLES](https://docs.snowflake.com/en/sql-reference/sql/show-roles)
```
SHOW ROLES LIKE 'tasty%';
```
<img src = "assets/show_tb_roles.png"> 

#### Step 5 - Exploring the Tasty Bytes Warehouses
- This query will return the Warehouses we created via [SHOW WAREHOUSES](https://docs.snowflake.com/en/sql-reference/sql/show-warehouses)
```
SHOW WAREHOUSES LIKE 'tasty%';
```
<img src = "assets/show_tb_whs.png"> 

#### Step 6 - Putting it all together
- These next three queries will:
    1. Assume the `tasty_data_engineer` role via [USE ROLE](https://docs.snowflake.com/en/sql-reference/sql/use-role.html)
    2. Leverage the `tasty_de_wh` Warehouse via [USE WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/use-warehouse.html)
    3. Query our `raw_pos.menu` table to find which Menu Items are sold at our Plant Palace branded food trucks.
    
```
USE ROLE tasty_data_engineer;
USE WAREHOUSE tasty_de_wh;

SELECT
    m.menu_type_id,
    m.menu_type,
    m.truck_brand_name,
    m.menu_item_name
FROM frostbyte_tasty_bytes.raw_pos.menu m
WHERE m.truck_brand_name = 'Plant Palace';
```
<img src = "assets/plant_palace.png"> 

## Powered by Tasty Bytes - Quickstarts
Duration: 0
Congratulations, you have now completed the Tasty Bytes Foundational Setup!

The Table of Contents below will outline all of the available Tasty Bytes Quickstarts that leverage the foundation you just completed.

<img src ="assets/pbtb_quickstarts.png"/>

### Zero to Snowflake

- #### [Financial Governance](site/sfguides/src/tasty_bytes_zero_to_snowflake_financial_governance)
    - Learn about Snowflake Virtual Warehouses and their configurabilities, Resource Monitors, and Account and Warehouse Level Timeout Parameters.
- #### [Transformation](site/sfguides/src/tasty_bytes_zero_to_snowflake_transformation)
    - Learn about Snowflake Zero Copy Cloning, Result Set Cache, Table Manipulation, Time-Travel and Table level SWAP, DROP and Undrop functionality.
- #### [Semi-Structured Data](site/sfguides/src/tasty_bytes_zero_to_snowflake_semi_structured_data)
    - Learn about Snowflake VARIANT Data Type, Semi-Structured Data Processing via Dot Notation and Lateral Flattening as well as View Creation and Snowsight Charting.
- #### [Data Governance](site/sfguides/src/tasty_bytes_zero_to_snowflake_data_governance)
    - Learn about Snowflake System Defined Roles, Create and apply GRANTS to a custom role, and deploy both Tag Based Dynamic Data Masking and Row-Access Policies.
- #### [Collaboration](site/sfguides/src/tasty_bytes_zero_to_snowflake_collaboration)
    - Learn about the Snowflake Marketplace by leveraging free, instantly available, live listings from Weathersource and Safegraph to conduct data driven analysis harmonizing first and third party sources.
- #### [Geospatial](site/sfguides/src/tasty_bytes_zero_to_snowflake_geospatial)
    - Learn about Snowflake Geospatial support starting with constructing Geographic Points (ST_POINT) and leveraging other Geospatial functionality to calculate distance (ST_DISTANCE), collect coordinates, draw a Minimum Bounding Polygon and find the polygons center point.

### Workload Deep Dives (*Coming Soon*)




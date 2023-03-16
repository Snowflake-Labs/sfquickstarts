author: Jacob Kranzler
id: tasty_bytes_zero_to_snowflake_semi_structured_data
summary: Tasty Bytes - Zero to Snowflake - Semi-Structured Data Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Data Warehouse

# Tasty Bytes - Zero to Snowflake - Semi-Structured Data
<!-- ------------------------ -->

## Semi-Structured Data Processing in Snowflake
Duration: 1
<img src = "assets/semi_structured_header.png">

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Semi-Structured Data Processing!

Within this Quickstart, we will learn about processing Semi-Structured Data in Snowflake by diving into the VARIANT Data Type, Semi-Structured Data Processing combinging Dot Notation and Lateral Flattening as well as View Creation and Snowsight Charting.

For more detail on Semi-Structured Data in Snowflake please visit the [Semi-Structured Data Overview documentation](https://docs.snowflake.com/en/user-guide/semistructured-concepts)

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- A

### What You Will Build
- B

## Creating a Worksheet and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming the Worksheet, Copying SQL from GitHub, and Pasting the SQL we will be leveraging within this Quickstart.

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

### Step 6 - Accessing Quickstart SQL in GitHub
- Click the button below which will direct you to our Tasty Bytes SQL file that is hosted on GitHub.
<button>[tb_zts_semi_structured_data.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/tasty_bytes_zero_to_snowflake_semi_structured_data/assets/tb_zts_semi_structured_data.sql)</button>

### Step 7 - Copying Setup SQL from GitHub
- Within GitHub navigate to the right side and click "Copy raw contents". This will copy all of the required SQL into your clipboard.
    - <img src ="assets/github_copy_raw_contents.png"/>

### Step 8 - Pasting Setup SQL from GitHub into your Snowflake Worksheet
- Path back to Snowsight and your newly created Worksheet and Paste (*CMD + V for Mac or CTRL + V for Windows*) what we just copied from GitHub.

### Step 9 - Click Next -->

## Profiling our Semi-Structured Menu Data
Duration: 0

### Overview
As a Tasty Bytes Data Engineer, we have been tasked with profiling our Menu data that includes a Semi-Structured Data column. From this menu table we need to produce an Analytics layer View that exposes Dietary and Ingredient data to our end users.

### Step 1 - Setting our Context and Querying our Table
To begin, let's execute the first three queries together which will:
    1. Set the Role context to `tasty_data_engineer`
    2. Set the Warehouse context to `tasty_de_wh`
    3. Produce a [TOP](https://docs.snowflake.com/en/sql-reference/constructs/top_n) 10 Result Set of our `raw_pos.menu` table

```
USE ROLE tasty_data_engineer;
USE WAREHOUSE tasty_de_wh;

SELECT TOP 10
    m.truck_brand_name,
    m.menu_type,
    m.menu_item_name,
    m.menu_item_health_metrics_obj
FROM frostbyte_tasty_bytes.raw_pos.menu m;
```

<img src = "assets/3.1.menu.png">

Within our output, we can see that the `menu_item_health_metrics_obj` must be the Semi-Structured Data we were told about. By clicking into one of the cells in this column, we will see Snowsight automatically expand the stats pane to give us a better view of what is inside.

<img src = "assets/3.1.2.stats.png">

### Step 2 - Exploring our Semi-Structured Column
To dive deeper into how this column in defined in Snowflake, please run the next query where we leverage [SHOW COLUMNS]() to explore the Data Types present in our `menu` table.

```
SHOW COLUMNS IN frostbyte_tasty_bytes.raw_pos.menu;
```

<img src = "assets/3.2.show_columns.png">

Looking at our result set, we see the `menu_item_health_metrics_obj` is a [VARIANT](https://docs.snowflake.com/en/sql-reference/data-types-semistructured) Data Type.

>aside positive
>For data that is mostly regular and uses only data types that are native to the semi-structured format you are using (e.g. strings and integers for JSON format), the storage requirements and query performance for operations on relational data and data in a VARIANT column is very similar.
>

### Step 3 - Traversing Semi-Structured Data using Dot Notation
Within our `menu_item_health_metrics_obj` column, we saw that `menu_item_id` was nested inside alongside the more nested ingredients and dietary restriction data we need to access. 

Please execute the next query where we begin to leverage [Dot Notation](https://docs.snowflake.com/en/user-guide/querying-semistructured#dot-notation) to traverse our Semi-Structured data.

```
SELECT 
    m.menu_item_health_metrics_obj:menu_item_id AS menu_item_id,
    m.menu_item_health_metrics_obj:menu_item_health_metrics AS menu_item_health_metrics
FROM frostbyte_tasty_bytes.raw_pos.menu m;
```

<img src = "assets/3.3.dot.png">

Using Dot Notation we were able to successfully extract `menu_item_id` in full, but look to still be left with additional semi-structured objects in the `menu_item_health_metrics` column output. Once again let's click into one of the cells within this column to take a further look.

<img src = "assets/3.3.2.stats.png">

We are making progress! Let's see how we can further process `menu_item_health_metrics` in the next section by using additional Snowflake functions.

### Step 4 - Click Next -->

## Flattening Semi-Structured Data
Duration: 0

### Overview

### Step 1 - Introduction to Lateral Flatten

### Step 2 - Exploring a Semi-Structured Data Function
[ARRAY_CONTAINS](https://docs.snowflake.com/en/sql-reference/functions/array_contains)


## Creating Structured Views over Semi-Structured Data
Duration: 0

## Running Array Analysis
### Overview
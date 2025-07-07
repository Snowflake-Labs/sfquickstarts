author: Cameron Shimmin
id: tasty_bytes_zero_to_snowflake_data_pipeline
summary: Tasty Bytes - Zero to Snowflake - Simple Data Pipeline Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, Data Engineering, Data Pipeline, Dynamic Tables, ELT

# Tasty Bytes - Zero To Snowflake - Simple Data Pipeline
## Building a Simple Data Pipeline
Duration: 1
<!-- <img src = "assets/data_pipeline_header.png"> -->

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on building a Simple Data Pipeline!

Within this Quickstart, we will learn how to build a simple, automated data pipeline in Snowflake. We will start by ingesting raw, semi-structured data from an external stage, and then use the power of Snowflake's Dynamic Tables to transform and enrich that data, creating a pipeline that automatically stays up-to-date as new data arrives.

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- How to ingest data from an external S3 stage.
- How to query and transform semi-structured VARIANT data.
- How to use the FLATTEN function to parse arrays.
- How to create and chain Dynamic Tables.
- How an ELT pipeline automatically processes new data.
- How to visualize a pipeline using the Directed Acyclic Graph (DAG).

### What You Will Build
- An external Stage for data ingestion.
- A staging table for raw data.
- A multi-step data pipeline using three chained Dynamic Tables.


## Creating a Worksheet and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart, we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming the Worksheet, and Pasting the SQL we will be leveraging within this Quickstart.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account.

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.

### Step 3 - Navigating to Worksheets
- Click on the **Projects** Tab in the left-hand navigation bar and click **Worksheets**.

### Step 4 - Creating a Worksheet
- Within Worksheets, click the **"+"** button in the top-right corner of Snowsight.

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Simple Data Pipeline".

### Step 6 - Pasting SQL into your Snowflake Worksheet
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** Asset:        Zero to Snowflake v2 - Simple Data Pipeline
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "data_pipeline"}}';

USE DATABASE tb_101;
USE ROLE tb_data_engineer;
USE WAREHOUSE tb_de_wh;

/* 1. Ingestion from External stage */

-- Create the menu stage
CREATE OR REPLACE STAGE raw_pos.menu_stage
COMMENT = 'Stage for menu data'
URL = 's3://sfquickstarts/frostbyte_tastybytes/raw_pos/menu/'
FILE_FORMAT = public.csv_ff;

CREATE OR REPLACE TABLE raw_pos.menu_staging
(
    menu_id NUMBER(19,0),
    menu_type_id NUMBER(38,0),
    menu_type VARCHAR(16777216),
    truck_brand_name VARCHAR(16777216),
    menu_item_id NUMBER(38,0),
    menu_item_name VARCHAR(16777216),
    item_category VARCHAR(16777216),
    item_subcategory VARCHAR(16777216),
    cost_of_goods_usd NUMBER(38,4),
    sale_price_usd NUMBER(38,4),
    menu_item_health_metrics_obj VARIANT
);

-- Load the data from the stage into the new menu_staging table.
COPY INTO raw_pos.menu_staging
FROM @raw_pos.menu_stage;

-- Optional: Verify successful load
SELECT * FROM raw_pos.menu_staging;

/* 2. Semi-Structured data in Snowflake */
SELECT menu_item_health_metrics_obj FROM raw_pos.menu_staging;

-- Query and cast semi-structured data
SELECT
    menu_item_name,
    CAST(menu_item_health_metrics_obj:menu_item_id AS INTEGER) AS menu_item_id,
    menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY AS ingredients
FROM raw_pos.menu_staging;

-- Use FLATTEN to parse arrays
SELECT
    i.value::STRING AS ingredient_name,
    m.menu_item_health_metrics_obj:menu_item_id::INTEGER AS menu_item_id
FROM
    raw_pos.menu_staging m,
    LATERAL FLATTEN(INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY) i;

/* 3. Dynamic Tables */

-- Create the Dynamic Table for Ingredients.
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient
    LAG = '1 minute'
    WAREHOUSE = 'TB_DE_WH'
AS
    SELECT
    ingredient_name,
    menu_ids
FROM (
    SELECT DISTINCT
        i.value::STRING AS ingredient_name, 
        ARRAY_AGG(m.menu_item_id) AS menu_ids
    FROM
        raw_pos.menu_staging m,
        LATERAL FLATTEN(INPUT => menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY) i
    GROUP BY i.value::STRING
);

-- Verify that the ingredients Dynamic Table was successfully created
SELECT * FROM harmonized.ingredient;

-- Insert a new menu item to test automatic refresh
INSERT INTO raw_pos.menu_staging 
SELECT 
    10101,
    15,
    'Sandwiches',
    'Better Off Bread',
    157,
    'Banh Mi',
    'Main',
    'Cold Option',
    9.0,
    12.0,
    PARSE_JSON('{
      "menu_item_health_metrics": [
        {
          "ingredients": [
            "French Baguette",
            "Mayonnaise",
            "Pickled Daikon",
            "Cucumber",
            "Pork Belly"
          ],
          "is_dairy_free_flag": "N",
          "is_gluten_free_flag": "N",
          "is_healthy_flag": "Y",
          "is_nut_free_flag": "Y"
        }
      ],
      "menu_item_id": 157
    }'
);

-- Verify new ingredients are showing in the ingredients table.
SELECT * FROM harmonized.ingredient 
WHERE ingredient_name IN ('French Baguette', 'Pickled Daikon');

/* 4. Simple Pipeline with Dynamic Tables */

-- Create an ingredient to menu lookup dynamic table.
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient_to_menu_lookup
    LAG = '1 minute'
    WAREHOUSE = 'TB_DE_WH'   
AS
SELECT
    i.ingredient_name,
    m.menu_item_health_metrics_obj:menu_item_id::INTEGER AS menu_item_id
FROM
    raw_pos.menu_staging m,
    LATERAL FLATTEN(INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients) f
JOIN harmonized.ingredient i ON f.value::STRING = i.ingredient_name;

-- Verify ingredient to menu lookup created successfully
SELECT * FROM harmonized.ingredient_to_menu_lookup
ORDER BY menu_item_id;

-- Insert order data
INSERT INTO raw_pos.order_header
SELECT 
    459520441, 15, 1030, 101565, null, 200322900,
    TO_TIMESTAMP_NTZ('08:00:00', 'hh:mi:ss'),
    TO_TIMESTAMP_NTZ('14:00:00', 'hh:mi:ss'),
    null, TO_TIMESTAMP_NTZ('2022-01-27 08:21:08.000'),
    null, 'USD', 14.00, null, null, 14.00;

INSERT INTO raw_pos.order_detail
SELECT
    904745311, 459520441, 157, null, 0, 2, 14.00, 28.00, null;

-- Create the final dynamic table in the pipeline
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient_usage_by_truck 
    LAG = '2 minute'
    WAREHOUSE = 'TB_DE_WH'  
    AS 
    SELECT
        oh.truck_id,
        EXTRACT(YEAR FROM oh.order_ts) AS order_year,
        MONTH(oh.order_ts) AS order_month,
        i.ingredient_name,
        SUM(od.quantity) AS total_ingredients_used
    FROM
        raw_pos.order_detail od
        JOIN raw_pos.order_header oh ON od.order_id = oh.order_id
        JOIN harmonized.ingredient_to_menu_lookup iml ON od.menu_item_id = iml.menu_item_id
        JOIN harmonized.ingredient i ON iml.ingredient_name = i.ingredient_name
        JOIN raw_pos.location l ON l.location_id = oh.location_id
    WHERE l.country = 'United States'
    GROUP BY
        oh.truck_id,
        order_year,
        order_month,
        i.ingredient_name
    ORDER BY
        oh.truck_id,
        total_ingredients_used DESC;

-- View the ingredient usage for truck #15 in January 2022
SELECT
    truck_id,
    ingredient_name,
    SUM(total_ingredients_used) AS total_ingredients_used
FROM
    harmonized.ingredient_usage_by_truck
WHERE
    order_month = 1
    AND truck_id = 15
GROUP BY truck_id, ingredient_name
ORDER BY total_ingredients_used DESC;

-------------------------------------------------------------------------
--RESET--
-------------------------------------------------------------------------
USE ROLE accountadmin;
DROP TABLE IF EXISTS raw_pos.menu_staging;
DROP TABLE IF EXISTS harmonized.ingredient;
DROP TABLE IF EXISTS harmonized.ingredient_to_menu_lookup;
DROP TABLE IF EXISTS harmonized.ingredient_usage_by_truck;

DELETE FROM raw_pos.order_detail
WHERE order_detail_id = 904745311;
DELETE FROM raw_pos.order_header
WHERE order_id = 459520441;

ALTER WAREHOUSE tb_de_wh SUSPEND;
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Ingestion from External Stage

Duration: 2

### Overview

Our raw menu data currently sits in an Amazon S3 bucket as CSV files. To begin our pipeline, we first need to ingest this data into Snowflake. We will do this by creating a Stage to point to the S3 bucket and then using the `COPY` command to load the data into a staging table.

### Step 1 - Set Context

First, let's set our session context to use the correct database, role, and warehouse. Execute the first few queries in your worksheet.

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "data_pipeline"}}';

USE DATABASE tb_101;
USE ROLE tb_data_engineer;
USE WAREHOUSE tb_de_wh;
```

### Step 2 - Create Stage and Staging Table

A Stage is a Snowflake object that specifies an external location where data files are stored. We'll create a stage that points to our public S3 bucket. Then, we'll create the table that will hold this raw data.

```sql
-- Create the menu stage
CREATE OR REPLACE STAGE raw_pos.menu_stage
COMMENT = 'Stage for menu data'
URL = 's3://sfquickstarts/frostbyte_tastybytes/raw_pos/menu/'
FILE_FORMAT = public.csv_ff;

CREATE OR REPLACE TABLE raw_pos.menu_staging
(
    menu_id NUMBER(19,0),
    menu_type_id NUMBER(38,0),
    menu_type VARCHAR(16777216),
    truck_brand_name VARCHAR(16777216),
    menu_item_id NUMBER(38,0),
    menu_item_name VARCHAR(16777216),
    item_category VARCHAR(16777216),
    item_subcategory VARCHAR(16777216),
    cost_of_goods_usd NUMBER(38,4),
    sale_price_usd NUMBER(38,4),
    menu_item_health_metrics_obj VARIANT
);
```

### Step 3 - Copy Data into Staging Table

With the stage and table in place, let's load the data from the stage into our `menu_staging` table using the `COPY INTO` command.

```sql
COPY INTO raw_pos.menu_staging
FROM @raw_pos.menu_stage;
```

> aside positive
> **[COPY INTO TABLE](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table)**: This powerful command loads data from a staged file into a Snowflake table. It is the primary method for bulk data ingestion.

### Step 4 - Click Next --\>

## Working with Semi-Structured Data

Duration: 2

### Overview

Snowflake excels at handling semi-structured data like JSON using its native `VARIANT` data type. One of the columns we ingested, `menu_item_health_metrics_obj`, contains JSON. Let's explore how to query it.

### Step 1 - Querying VARIANT Data

Let's look at the raw JSON. Notice it contains nested objects and arrays.

```sql
SELECT menu_item_health_metrics_obj FROM raw_pos.menu_staging;
```

<!-- \<img src="assets/variant\_column.png"/\> -->

We can use special syntax to navigate the JSON structure. The colon (`:`) accesses keys by name, and square brackets (`[]`) access array elements. We can also cast (`::`) the results to the proper data type.

```sql
SELECT
    menu_item_name,
    CAST(menu_item_health_metrics_obj:menu_item_id AS INTEGER) AS menu_item_id, -- Casting using 'AS'
    menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY AS ingredients -- Casting using double colon (::) syntax
FROM raw_pos.menu_staging;
```

### Step 2 - Parsing Arrays with FLATTEN

The `FLATTEN` function is a powerful tool for un-nesting arrays. It produces a new row for each element in an array. Let's use it to create a list of every ingredient for every menu item.

```sql
SELECT
    i.value::STRING AS ingredient_name,
    m.menu_item_health_metrics_obj:menu_item_id::INTEGER AS menu_item_id
FROM
    raw_pos.menu_staging m,
    LATERAL FLATTEN(INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY) i;
```

> aside positive
> **[Semi-Structured Data Types](https://docs.snowflake.com/en/sql-reference/data-types-semistructured)**: Snowflake's VARIANT, OBJECT, and ARRAY types allow you to store and query semi-structured data directly, without needing to define a rigid schema upfront.

### Step 3 - Click Next --\>

## Automating with Dynamic Tables

Duration: 3

### Overview

Our franchises are constantly adding new menu items. We need a way to process this new data automatically. For this, we can use Dynamic Tables, a powerful tool designed to simplify data transformation pipelines by declaratively defining the result of a query and letting Snowflake handle the refreshes.

### Step 1 - Creating the First Dynamic Table

We'll start by creating a dynamic table that extracts all unique ingredients from our staging table. We set a `LAG` of '1 minute', which tells Snowflake the maximum amount of time this table's data can be behind the source data.

```sql
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient
    LAG = '1 minute'
    WAREHOUSE = 'TB_DE_WH'
AS
    SELECT
    ingredient_name,
    menu_ids
FROM (
    SELECT DISTINCT
        i.value::STRING AS ingredient_name, 
        ARRAY_AGG(m.menu_item_id) AS menu_ids
    FROM
        raw_pos.menu_staging m,
        LATERAL FLATTEN(INPUT => menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY) i
    GROUP BY i.value::STRING
);
```

> aside positive
> **[Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)**: Dynamic Tables automatically refresh as their underlying source data changes, simplifying ELT pipelines and ensuring data freshness without manual intervention or complex scheduling.

### Step 2 - Testing the Automatic Refresh

Let's see the automation in action. One of our trucks has added a Banh Mi sandwich, which contains new ingredients. Let's insert this new menu item into our staging table.

```sql
INSERT INTO raw_pos.menu_staging 
SELECT 
    10101, 15, 'Sandwiches', 'Better Off Bread', 157, 'Banh Mi', 'Main', 'Cold Option', 9.0, 12.0,
    PARSE_JSON('{"menu_item_health_metrics": [{"ingredients": ["French Baguette","Mayonnaise","Pickled Daikon","Cucumber","Pork Belly"],"is_dairy_free_flag": "N","is_gluten_free_flag": "N","is_healthy_flag": "Y","is_nut_free_flag": "Y"}],"menu_item_id": 157}');
```

Now, query the `harmonized.ingredient` table. Within a minute, you should see the new ingredients appear automatically.

```sql
-- You may need to wait up to 1 minute and re-run this query
SELECT * FROM harmonized.ingredient 
WHERE ingredient_name IN ('French Baguette', 'Pickled Daikon');
```

### Step 3 - Click Next --\>

## Building Out the Pipeline

Duration: 3

### Overview

Now we can build a multi-step pipeline by creating more dynamic tables that read from other dynamic tables. This creates a chain, or a Directed Acyclic Graph (DAG), where updates automatically flow from the source to the final output.

### Step 1 - Creating a Lookup Table

Let's create a lookup table that maps ingredients to the menu items they are used in. This dynamic table reads from our `harmonized.ingredient` dynamic table.

```sql
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient_to_menu_lookup
    LAG = '1 minute'
    WAREHOUSE = 'TB_DE_WH'   
AS
SELECT
    i.ingredient_name,
    m.menu_item_health_metrics_obj:menu_item_id::INTEGER AS menu_item_id
FROM
    raw_pos.menu_staging m,
    LATERAL FLATTEN(INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients) f
JOIN harmonized.ingredient i ON f.value::STRING = i.ingredient_name;
```

### Step 2 - Adding Transactional Data

Let's simulate an order of two Banh Mi sandwiches by inserting records into our order tables.

```sql
INSERT INTO raw_pos.order_header
SELECT 
    459520441, 15, 1030, 101565, null, 200322900,
    TO_TIMESTAMP_NTZ('08:00:00', 'hh:mi:ss'),
    TO_TIMESTAMP_NTZ('14:00:00', 'hh:mi:ss'),
    null, TO_TIMESTAMP_NTZ('2022-01-27 08:21:08.000'),
    null, 'USD', 14.00, null, null, 14.00;
    
INSERT INTO raw_pos.order_detail
SELECT
    904745311, 459520441, 157, null, 0, 2, 14.00, 28.00, null;
```

### Step 3 - Creating the Final Pipeline Table

Finally, let's create our final dynamic table. This one joins our order data with our ingredient lookup tables to create a summary of monthly ingredient usage per truck. This table depends on the other dynamic tables, completing our pipeline.

```sql
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient_usage_by_truck 
    LAG = '2 minute'
    WAREHOUSE = 'TB_DE_WH'  
    AS 
    SELECT
        oh.truck_id,
        EXTRACT(YEAR FROM oh.order_ts) AS order_year,
        MONTH(oh.order_ts) AS order_month,
        i.ingredient_name,
        SUM(od.quantity) AS total_ingredients_used
    FROM
        raw_pos.order_detail od
        JOIN raw_pos.order_header oh ON od.order_id = oh.order_id
        JOIN harmonized.ingredient_to_menu_lookup iml ON od.menu_item_id = iml.menu_item_id
        JOIN harmonized.ingredient i ON iml.ingredient_name = i.ingredient_name
        JOIN raw_pos.location l ON l.location_id = oh.location_id
    WHERE l.country = 'United States'
    GROUP BY
        oh.truck_id,
        order_year,
        order_month,
        i.ingredient_name
    ORDER BY
        oh.truck_id,
        total_ingredients_used DESC;
```

### Step 4 - Querying the Final Output

Now, let's query the final table in our pipeline. After a few minutes for the refreshes to complete, you will see the ingredient usage from the Banh Mi order we inserted. The entire pipeline updated automatically.

```sql
-- You may need to wait up to 2 minutes and re-run this query
SELECT
    truck_id,
    ingredient_name,
    SUM(total_ingredients_used) AS total_ingredients_used
FROM
    harmonized.ingredient_usage_by_truck
WHERE
    order_month = 1
    AND truck_id = 15
GROUP BY truck_id, ingredient_name
ORDER BY total_ingredients_used DESC;
```

### Step 5 - Click Next --\>

## Visualizing the Pipeline with a DAG

Duration: 1

### Overview

Finally, let's visualize our pipeline's Directed Acyclic Graph, or DAG. The DAG shows how our data flows through the tables, and it can be used to monitor the health and lag of our pipeline.

### Step 1 - Accessing the Graph View

To access the DAG in Snowsight:

1.  Navigate to **Data** » **Database**.
2.  In the database object explorer, expand your database **TB\_101** and the schema **HARMONIZED**.
3.  Click on **Dynamic Tables**.
4.  Select any of the dynamic tables you created (e.g., `INGREDIENT_USAGE_BY_TRUCK`).
5.  Click on the **Graph** tab in the main window.

You will now see a visualization of your pipeline, showing how the base tables flow into your dynamic tables.

<!-- \<img src="assets/dag\_view.png"/\> -->

### Step 2 - Click Next --\>

## Conclusion and Next Steps

Duration: 1

### Conclusion

Fantastic work\! You have successfully completed the Tasty Bytes - Simple Data Pipeline Quickstart.

By doing so you have now learned how to:

  - Ingest data from an S3 Stage using `COPY INTO`.
  - Query and transform semi-structured `VARIANT` data.
  - Use `FLATTEN` to parse arrays into rows.
  - Build a multi-step, automated ELT pipeline using Dynamic Tables.
  - Visualize your pipeline's dependencies using the DAG.

If you would like to re-run this Quickstart, please run the `RESET` scripts located at the bottom of your worksheet.

### Next Steps

To continue your journey in the Snowflake AI Data Cloud, please now visit the link below to see all other Powered by Tasty Bytes - Quickstarts available to you.

  - ### [Powered by Tasty Bytes - Quickstarts Table of Contents](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html#3)

<!-- end list -->

```
```
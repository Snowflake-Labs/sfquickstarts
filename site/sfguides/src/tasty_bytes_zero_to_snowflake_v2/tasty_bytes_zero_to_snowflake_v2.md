author: Dureti Shemsi, Cameron Shimmin
id: tasty_bytes_zero_to_snowflake_v2
summary: Tasty Bytes - Zero to Snowflake
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, Governance, Horizon, Data Security, RBAC, Masking, Data Quality

# Tasty Bytes - Zero to Snowflake

## Zero to Snowflake

Duration: 1
<!-- \<img src = "assets/zts\_complete\_header.png"\> -->

### Overview

Welcome to the complete Powered by Tasty Bytes - Zero to Snowflake Quickstart\! This guide is a consolidated journey through four key areas of the Snowflake AI Data Cloud. You will start with the fundamentals of warehousing and data transformation, build an automated data pipeline, secure your data with powerful governance controls, and finally, enrich your analysis through seamless data collaboration.

### Prerequisites

  - Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn

  - **Module 1: Getting Started:** The fundamentals of Snowflake warehouses, caching, cloning, and Time Travel.
  - **Module 2: Simple Data Pipelines:** How to ingest and transform semi-structured data using Dynamic Tables.
  - **Module 3: [Dummy Vignette]:** A placeholder for your future content.
  - **Module 4: Governance with Horizon:** How to protect your data with roles, classification, masking, and row-access policies.
  - **Module 5: Apps & Collaboration:** How to leverage the Snowflake Marketplace to enrich your internal data with third-party datasets.

### What You Will Build

  - A comprehensive understanding of the core Snowflake platform.
  - Configured Virtual Warehouses.
  - An automated ELT pipeline with Dynamic Tables.
  - A robust data governance framework with roles and policies.
  - Enriched analytical views combining first- and third-party data.

## Creating a Worksheet and Copying in our SQL

Duration: 2

### Overview

This Quickstart consolidates all SQL scripts from the individual modules into one. You will only need one Snowsight Worksheet for this entire guide.

### Step 1 - Accessing Snowflake

  - Open a browser window and enter the URL of your Snowflake Account and log in.

### Step 2 - Creating and Renaming a Worksheet

  - Navigate to **Projects** » **Worksheets**.
  - Click the **"+"** button in the top-right corner to create a new worksheet.
  - Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Complete ZTS".

### Step 3 - Pasting SQL into your Worksheet

  - Copy the entire combined SQL block below and paste it into your worksheet. This single script contains all the SQL needed for all five modules. The `RESET` script at the end will clean up all created objects.

<!-- end list -->

```sql
/*==================================================================================================*/
/*==================================================================================================*/
/*======================== MODULE 1: GETTING STARTED WITH SNOWFLAKE ================================*/
/*==================================================================================================*/
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "getting_started_with_snowflake"}}';
USE DATABASE tb_101;
USE ROLE accountadmin;

-- Virtual Warehouses & Settings
SHOW WAREHOUSES;
CREATE OR REPLACE WAREHOUSE my_wh COMMENT = 'My TastyBytes warehouse' WAREHOUSE_TYPE = 'standard' WAREHOUSE_SIZE = 'xsmall' MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 2 SCALING_POLICY = 'standard' AUTO_SUSPEND = 60 INITIALLY_SUSPENDED = true, AUTO_RESUME = false;
USE WAREHOUSE my_wh;
SELECT * FROM raw_pos.truck_details; -- This will fail initially
ALTER WAREHOUSE my_wh RESUME;
ALTER WAREHOUSE my_wh SET AUTO_RESUME = TRUE;
SELECT * FROM raw_pos.truck_details;
ALTER WAREHOUSE my_wh SET warehouse_size = 'XLarge';
SELECT o.truck_brand_name, COUNT(DISTINCT o.order_id) AS order_count, SUM(o.price) AS total_sales FROM analytics.orders_v o GROUP BY o.truck_brand_name ORDER BY total_sales DESC;
ALTER WAREHOUSE my_wh SET warehouse_size = 'XSmall';

-- Basic Transformation Techniques
SELECT truck_build FROM raw_pos.truck_details;
CREATE OR REPLACE TABLE raw_pos.truck_dev CLONE raw_pos.truck_details;
SELECT TOP 15 * FROM raw_pos.truck_dev ORDER BY truck_id;
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS year NUMBER;
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS make VARCHAR(255);
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS model VARCHAR(255);
UPDATE raw_pos.truck_dev SET year = truck_build:year::NUMBER, make = truck_build:make::VARCHAR, model = truck_build:model::VARCHAR;
SELECT year, make, model FROM raw_pos.truck_dev;
SELECT make, COUNT(*) AS count FROM raw_pos.truck_dev GROUP BY make ORDER BY make ASC;
UPDATE raw_pos.truck_dev SET make = 'Ford' WHERE make = 'Ford_';
SELECT truck_id, make FROM raw_pos.truck_dev ORDER BY truck_id;
ALTER TABLE raw_pos.truck_details SWAP WITH raw_pos.truck_dev;
SELECT make, COUNT(*) AS count FROM raw_pos.truck_details GROUP BY make ORDER BY count DESC;
ALTER TABLE raw_pos.truck_details DROP COLUMN truck_build;
DROP TABLE raw_pos.truck_details; -- "Accidental" drop

-- Data Recovery with UNDROP
DESCRIBE TABLE raw_pos.truck_details; -- This will error
UNDROP TABLE raw_pos.truck_details;
SELECT * from raw_pos.truck_details;
DROP TABLE raw_pos.truck_dev; -- Drop the real dev table


/*==================================================================================================*/
/*==================================================================================================*/
/*======================== MODULE 2: SIMPLE DATA PIPELINE ==========================================*/
/*==================================================================================================*/
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "data_pipeline"}}';
USE DATABASE tb_101;
USE ROLE tb_data_engineer;
USE WAREHOUSE tb_de_wh;

-- Ingestion from External stage
CREATE OR REPLACE STAGE raw_pos.menu_stage COMMENT = 'Stage for menu data' URL = 's3://sfquickstarts/frostbyte_tastybytes/raw_pos/menu/' FILE_FORMAT = public.csv_ff;
CREATE OR REPLACE TABLE raw_pos.menu_staging (menu_id NUMBER(19,0), menu_type_id NUMBER(38,0), menu_type VARCHAR(16777216), truck_brand_name VARCHAR(16777216), menu_item_id NUMBER(38,0), menu_item_name VARCHAR(16777216), item_category VARCHAR(16777216), item_subcategory VARCHAR(16777216), cost_of_goods_usd NUMBER(38,4), sale_price_usd NUMBER(38,4), menu_item_health_metrics_obj VARIANT);
COPY INTO raw_pos.menu_staging FROM @raw_pos.menu_stage;

-- Semi-Structured data in Snowflake
SELECT menu_item_health_metrics_obj FROM raw_pos.menu_staging;
SELECT menu_item_name, CAST(menu_item_health_metrics_obj:menu_item_id AS INTEGER) AS menu_item_id, menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY AS ingredients FROM raw_pos.menu_staging;
SELECT i.value::STRING AS ingredient_name, m.menu_item_health_metrics_obj:menu_item_id::INTEGER AS menu_item_id FROM raw_pos.menu_staging m, LATERAL FLATTEN(INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY) i;

-- Dynamic Tables
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient LAG = '1 minute' WAREHOUSE = 'TB_DE_WH' AS SELECT ingredient_name, menu_ids FROM (SELECT DISTINCT i.value::STRING AS ingredient_name, ARRAY_AGG(m.menu_item_id) AS menu_ids FROM raw_pos.menu_staging m, LATERAL FLATTEN(INPUT => menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients::ARRAY) i GROUP BY i.value::STRING);
SELECT * FROM harmonized.ingredient;
INSERT INTO raw_pos.menu_staging SELECT 10101, 15, 'Sandwiches', 'Better Off Bread', 157, 'Banh Mi', 'Main', 'Cold Option', 9.0, 12.0, PARSE_JSON('{"menu_item_health_metrics": [{"ingredients": ["French Baguette","Mayonnaise","Pickled Daikon","Cucumber","Pork Belly"],"is_dairy_free_flag": "N","is_gluten_free_flag": "N","is_healthy_flag": "Y","is_nut_free_flag": "Y"}],"menu_item_id": 157}');
SELECT * FROM harmonized.ingredient WHERE ingredient_name IN ('French Baguette', 'Pickled Daikon'); -- May require waiting a minute
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient_to_menu_lookup LAG = '1 minute' WAREHOUSE = 'TB_DE_WH' AS SELECT i.ingredient_name, m.menu_item_health_metrics_obj:menu_item_id::INTEGER AS menu_item_id FROM raw_pos.menu_staging m, LATERAL FLATTEN(INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients) f JOIN harmonized.ingredient i ON f.value::STRING = i.ingredient_name;
INSERT INTO raw_pos.order_header SELECT 459520441, 15, 1030, 101565, null, 200322900, TO_TIMESTAMP_NTZ('08:00:00', 'hh:mi:ss'), TO_TIMESTAMP_NTZ('14:00:00', 'hh:mi:ss'), null, TO_TIMESTAMP_NTZ('2022-01-27 08:21:08.000'), null, 'USD', 14.00, null, null, 14.00;
INSERT INTO raw_pos.order_detail SELECT 904745311, 459520441, 157, null, 0, 2, 14.00, 28.00, null;
CREATE OR REPLACE DYNAMIC TABLE harmonized.ingredient_usage_by_truck LAG = '2 minute' WAREHOUSE = 'TB_DE_WH' AS SELECT oh.truck_id, EXTRACT(YEAR FROM oh.order_ts) AS order_year, MONTH(oh.order_ts) AS order_month, i.ingredient_name, SUM(od.quantity) AS total_ingredients_used FROM raw_pos.order_detail od JOIN raw_pos.order_header oh ON od.order_id = oh.order_id JOIN harmonized.ingredient_to_menu_lookup iml ON od.menu_item_id = iml.menu_item_id JOIN harmonized.ingredient i ON iml.ingredient_name = i.ingredient_name JOIN raw_pos.location l ON l.location_id = oh.location_id WHERE l.country = 'United States' GROUP BY oh.truck_id, order_year, order_month, i.ingredient_name ORDER BY oh.truck_id, total_ingredients_used DESC;
SELECT truck_id, ingredient_name, SUM(total_ingredients_used) AS total_ingredients_used FROM harmonized.ingredient_usage_by_truck WHERE order_month = 1 AND truck_id = 15 GROUP BY truck_id, ingredient_name ORDER BY total_ingredients_used DESC; -- May require waiting


/*==================================================================================================*/
/*==================================================================================================*/
/*======================== MODULE 3: [DUMMY VIGNETTE] ==============================================*/
/*==================================================================================================*/
-- ALTER SESSION SET query_tag = '{"vignette": "dummy_vignette"}';
-- USE ROLE ...
--
-- [Add SQL for Dummy Vignette Here]
--


/*==================================================================================================*/
/*==================================================================================================*/
/*======================== MODULE 4: GOVERNANCE WITH HORIZON =======================================*/
/*==================================================================================================*/
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "governance_with_horizon"}}';
USE ROLE useradmin;
USE DATABASE tb_101;
USE WAREHOUSE tb_dev_wh;

-- Roles and Access Control
CREATE OR REPLACE ROLE tb_data_steward COMMENT = 'Custom Role';
USE ROLE securityadmin;
GRANT OPERATE, USAGE ON WAREHOUSE tb_dev_wh TO ROLE tb_data_steward;
GRANT USAGE ON DATABASE tb_101 TO ROLE tb_data_steward;
GRANT USAGE ON ALL SCHEMAS IN DATABASE tb_101 TO ROLE tb_data_steward;
GRANT SELECT ON ALL TABLES IN SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT ALL ON SCHEMA governance TO ROLE tb_data_steward;
GRANT ALL ON ALL TABLES IN SCHEMA governance TO ROLE tb_data_steward;
GRANT ROLE tb_data_steward TO USER USER;

-- Tag-Based Classification
USE ROLE accountadmin;
CREATE OR REPLACE TAG governance.pii;
GRANT APPLY TAG ON ACCOUNT TO ROLE tb_data_steward;
GRANT EXECUTE AUTO CLASSIFICATION ON SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE tb_data_steward;
GRANT CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE ON SCHEMA governance TO ROLE tb_data_steward;
USE ROLE tb_data_steward;
CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE governance.tb_classification_profile({'minimum_object_age_for_classification_days': 0, 'maximum_classification_validity_days': 30, 'auto_tag': true});
CALL governance.tb_classification_profile!SET_TAG_MAP({'column_tag_map':[{'tag_name':'tb_101.governance.pii','tag_value':'pii','semantic_categories':['NAME', 'PHONE_NUMBER', 'POSTAL_CODE', 'DATE_OF_BIRTH', 'CITY', 'EMAIL']}]});
CALL SYSTEM$CLASSIFY('tb_101.raw_customer.customer_loyalty', 'tb_101.governance.tb_classification_profile');

-- Masking Policies
CREATE OR REPLACE MASKING POLICY governance.mask_string_pii AS (original_value STRING) RETURNS STRING -> CASE WHEN CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN') THEN '****MASKED****' ELSE original_value END;
CREATE OR REPLACE MASKING POLICY governance.mask_date_pii AS (original_value DATE) RETURNS DATE -> CASE WHEN CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN') THEN DATE_TRUNC('year', original_value) ELSE original_value END;
ALTER TAG governance.pii SET MASKING POLICY governance.mask_string_pii, MASKING POLICY governance.mask_date_pii;

-- Row Access Policies
CREATE OR REPLACE TABLE governance.row_policy_map (role STRING, country_permission STRING);
INSERT INTO governance.row_policy_map VALUES('tb_data_engineer', 'United States');
CREATE OR REPLACE ROW ACCESS POLICY governance.customer_loyalty_policy AS (country STRING) RETURNS BOOLEAN -> CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') OR EXISTS (SELECT 1 FROM governance.row_policy_map rp WHERE UPPER(rp.role) = CURRENT_ROLE() AND rp.country_permission = country);
ALTER TABLE raw_customer.customer_loyalty ADD ROW ACCESS POLICY governance.customer_loyalty_policy ON (country);

-- Data Metric Functions
CREATE OR REPLACE DATA METRIC FUNCTION governance.invalid_order_total_count(order_prices_t table(order_total NUMBER, unit_price NUMBER, quantity INTEGER)) RETURNS NUMBER AS 'SELECT COUNT(*) FROM order_prices_t WHERE order_total != unit_price * quantity';
INSERT INTO raw_pos.order_detail SELECT 904745312, 459520442, 52, null, 0, 2, 5.0, 5.0, null;
ALTER TABLE raw_pos.order_detail SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';
ALTER TABLE raw_pos.order_detail ADD DATA METRIC FUNCTION governance.invalid_order_total_count ON (price, unit_price, quantity);

-- Trust Center
USE ROLE accountadmin;
GRANT APPLICATION ROLE SNOWFLAKE.TRUST_CENTER_ADMIN TO ROLE tb_admin;

/*==================================================================================================*/
/*==================================================================================================*/
/*======================== MODULE 5: APPS & COLLABORATION ==========================================*/
/*==================================================================================================*/
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "apps_and_collaboration"}}';
USE ROLE tb_analyst;
USE WAREHOUSE tb_de_wh;

-- Integrating Weather Source Data
CREATE OR REPLACE VIEW harmonized.daily_weather_v COMMENT = 'Weather Source Daily History filtered to Tasty Bytes supported Cities' AS SELECT hd.*, TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm, pc.city_name AS city, c.country AS country_desc FROM zts_weathersource.onpoint_id.history_day hd JOIN zts_weathersource.onpoint_id.postal_codes pc ON pc.postal_code = hd.postal_code AND pc.country = hd.country JOIN raw_pos.country c ON c.iso_country = hd.country AND c.city = hd.city_name;
CREATE OR REPLACE VIEW analytics.daily_sales_by_weather_v COMMENT = 'Daily Weather Metrics and Orders Data' AS WITH daily_orders_aggregated AS (SELECT DATE(o.order_ts) AS order_date, o.primary_city, o.country, o.menu_item_name, SUM(o.price) AS total_sales FROM harmonized.orders_v o GROUP BY ALL) SELECT dw.date_valid_std AS date, dw.city_name, dw.country_desc, ZEROIFNULL(doa.total_sales) AS daily_sales, doa.menu_item_name, ROUND(dw.avg_temperature_air_2m_f, 2) AS avg_temp_fahrenheit, ROUND(dw.tot_precipitation_in, 2) AS avg_precipitation_inches, ROUND(dw.tot_snowdepth_in, 2) AS avg_snowdepth_inches, dw.max_wind_speed_100m_mph AS max_wind_speed_mph FROM harmonized.daily_weather_v dw LEFT JOIN daily_orders_aggregated doa ON dw.date_valid_std = doa.order_date AND dw.city_name = doa.primary_city AND dw.country_desc = doa.country ORDER BY date ASC;

-- Explore Safegraph POI data
CREATE OR REPLACE VIEW harmonized.tastybytes_poi_v AS SELECT l.location_id, sg.postal_code, sg.country, sg.city, sg.iso_country_code, sg.location_name, sg.top_category, sg.category_tags, sg.includes_parking_lot, sg.open_hours FROM raw_pos.location l JOIN zts_safegraph.public.frostbyte_tb_safegraph_s sg ON l.location_id = sg.location_id AND l.iso_country_code = sg.iso_country_code;
WITH TopWindiestLocations AS (SELECT TOP 3 p.location_id FROM harmonized.tastybytes_poi_v AS p JOIN zts_weathersource.onpoint_id.history_day AS hd ON p.postal_code = hd.postal_code WHERE p.country = 'United States' AND YEAR(hd.date_valid_std) = 2022 GROUP BY p.location_id, p.city, p.postal_code ORDER BY AVG(hd.max_wind_speed_100m_mph) DESC) SELECT o.truck_brand_name, ROUND(AVG(CASE WHEN hd.max_wind_speed_100m_mph <= 20 THEN o.order_total END), 2) AS avg_sales_calm_days, ZEROIFNULL(ROUND(AVG(CASE WHEN hd.max_wind_speed_100m_mph > 20 THEN o.order_total END), 2)) AS avg_sales_windy_days FROM analytics.orders_v AS o JOIN zts_weathersource.onpoint_id.history_day AS hd ON o.primary_city = hd.city_name AND DATE(o.order_ts) = hd.date_valid_std WHERE o.location_id IN (SELECT location_id FROM TopWindiestLocations) GROUP BY o.truck_brand_name ORDER BY o.truck_brand_name;
    
/*==================================================================================================*/
/*==================================================================================================*/
/*======================== COMPLETE RESET SCRIPT ===================================================*/
/*==================================================================================================*/
USE ROLE accountadmin;

-- Module 5 Reset
DROP VIEW IF EXISTS harmonized.daily_weather_v;
DROP VIEW IF EXISTS analytics.daily_sales_by_weather_v;
DROP VIEW IF EXISTS harmonized.tastybytes_poi_v;

-- Module 4 Reset
DROP ROLE IF EXISTS tb_data_steward;
ALTER TAG IF EXISTS governance.pii UNSET MASKING POLICY governance.mask_string_pii, MASKING POLICY governance.mask_date_pii;
DROP MASKING POLICY IF EXISTS governance.mask_string_pii;
DROP MASKING POLICY IF EXISTS governance.mask_date_pii;
ALTER SCHEMA IF EXISTS raw_customer UNSET CLASSIFICATION_PROFILE;
DROP SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE IF EXISTS tb_classification_profile;
ALTER TABLE IF EXISTS raw_customer.customer_loyalty DROP ALL ROW ACCESS POLICIES;
DROP ROW ACCESS POLICY IF EXISTS governance.customer_loyalty_policy;
DELETE FROM raw_pos.order_detail WHERE order_detail_id = 904745312;
ALTER TABLE IF EXISTS raw_pos.order_detail DROP DATA METRIC FUNCTION governance.invalid_order_total_count ON (price, unit_price, quantity);
DROP FUNCTION IF EXISTS governance.invalid_order_total_count(TABLE(NUMBER, NUMBER, INTEGER));
ALTER TABLE IF EXISTS raw_pos.order_detail UNSET DATA_METRIC_SCHEDULE;
ALTER TABLE IF EXISTS raw_customer.customer_loyalty MODIFY COLUMN first_name UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN last_name UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN e_mail UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN phone_number UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN postal_code UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN marital_status UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN gender UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN birthday_date UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN country UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY, COLUMN city UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY;
DROP TAG IF EXISTS governance.pii;

-- Module 2 Reset
DROP TABLE IF EXISTS raw_pos.menu_staging;
DROP TABLE IF EXISTS harmonized.ingredient;
DROP TABLE IF EXISTS harmonized.ingredient_to_menu_lookup;
DROP TABLE IF EXISTS harmonized.ingredient_usage_by_truck;
DELETE FROM raw_pos.order_detail WHERE order_detail_id = 904745311;
DELETE FROM raw_pos.order_header WHERE order_id = 459520441;

-- Module 1 Reset
DROP WAREHOUSE IF EXISTS my_wh;
-- Reset truck details table to its original state before transformation
CREATE OR REPLACE TABLE raw_pos.truck_details AS SELECT * EXCLUDE (year, make, model) FROM raw_pos.truck;

-- Unset Query Tag
ALTER SESSION UNSET query_tag;
```

### Step 4 - Click Next --\>

## 1. Getting Started with Snowflake
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** 
Asset:        Zero to Snowflake v2 - Getting Started with Snowflake
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

-- Before we start, run this query to set the session query tag.
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "getting_started_with_snowflake"}}';

-- We'll begin by setting our Workspace context. We will set our database, schema and role.

USE DATABASE tb_101;
USE ROLE accountadmin;

/* 1. Virtual Warehouses & Settings */

-- Let's first look at the warehouses that already exist on our account that you have access privileges for
SHOW WAREHOUSES;

-- You can easily create a warehouse with a simple SQL command
CREATE OR REPLACE WAREHOUSE my_wh
    COMMENT = 'My TastyBytes warehouse'
    WAREHOUSE_TYPE = 'standard'
    WAREHOUSE_SIZE = 'xsmall'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 2
    SCALING_POLICY = 'standard'
    AUTO_SUSPEND = 60
    INITIALLY_SUSPENDED = true,
    AUTO_RESUME = false;

-- Use the warehouse
USE WAREHOUSE my_wh;

-- We can try running a simple query, however, you will see an error message in the results pane
SELECT * FROM raw_pos.truck_details;
    
-- Resume the warehouse
ALTER WAREHOUSE my_wh RESUME;
 
-- Set auto-resume to true
ALTER WAREHOUSE my_wh SET AUTO_RESUME = TRUE;

-- The warehouse is now running, so lets try to run the query from before 
SELECT * FROM raw_pos.truck_details;

-- Scale up our warehouse
ALTER WAREHOUSE my_wh SET warehouse_size = 'XLarge';

-- Let's now take a look at the sales per truck.
SELECT
    o.truck_brand_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.price) AS total_sales
FROM analytics.orders_v o
GROUP BY o.truck_brand_name
ORDER BY total_sales DESC;

/* 2. Using Persisted Query Results */

-- We'll now start working with a smaller dataset, so we can scale the warehouse back down
ALTER WAREHOUSE my_wh SET warehouse_size = 'XSmall';


/* 3. Basic Transformation Techniques */

-- SELECT the truck_build column
SELECT truck_build FROM raw_pos.truck_details;

-- Create the truck_dev table as a Zero Copy clone of the truck table
CREATE OR REPLACE TABLE raw_pos.truck_dev CLONE raw_pos.truck_details;

-- Verify successful truck table clone into truck_dev 
SELECT TOP 15 * FROM raw_pos.truck_dev
ORDER BY truck_id;

-- Add new columns
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS year NUMBER;
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS make VARCHAR(255);
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS model VARCHAR(255);

-- Update the new columns with the data extracted from the truck_build column.
UPDATE raw_pos.truck_dev
SET 
    year = truck_build:year::NUMBER,
    make = truck_build:make::VARCHAR,
    model = truck_build:model::VARCHAR;

-- Verify the 3 columns were successfully added and populated
SELECT year, make, model FROM raw_pos.truck_dev;

-- Count the different makes
SELECT 
    make,
    COUNT(*) AS count
FROM raw_pos.truck_dev
GROUP BY make
ORDER BY make ASC;

-- Use UPDATE to change any occurrence of 'Ford_' to 'Ford'
UPDATE raw_pos.truck_dev
    SET make = 'Ford'
    WHERE make = 'Ford_';

-- Verify the make column has been successfully updated 
SELECT truck_id, make 
FROM raw_pos.truck_dev
ORDER BY truck_id;

-- SWAP the truck table with the truck_dev table
ALTER TABLE raw_pos.truck_details SWAP WITH raw_pos.truck_dev; 

-- Run the query from before to get an accurate make count
SELECT 
    make,
    COUNT(*) AS count
FROM raw_pos.truck_details
GROUP BY
    make
ORDER BY count DESC;

-- Drop the old truck build column
ALTER TABLE raw_pos.truck_details DROP COLUMN truck_build;

-- Now we can drop the truck_dev table (on purpose for the next step!)
DROP TABLE raw_pos.truck_details;

/* 4. Data Recovery with UNDROP */
-- Optional: run this query to verify the 'truck' table no longer exists
DESCRIBE TABLE raw_pos.truck_details;

-- Run UNDROP on the production 'truck' table to restore it
UNDROP TABLE raw_pos.truck_details;

-- Verify the table was successfully restored
SELECT * from raw_pos.truck_details;

-- Now drop the real truck_dev table
DROP TABLE raw_pos.truck_dev;

/* 5. Resource Monitors */
USE ROLE accountadmin;

-- Run the query below to create the resource monitor via SQL
CREATE OR REPLACE RESOURCE MONITOR my_resource_monitor
    WITH CREDIT_QUOTA = 100
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 75 PERCENT DO NOTIFY
             ON 90 PERCENT DO SUSPEND
             ON 100 PERCENT DO SUSPEND_IMMEDIATE;

-- With the Resource Monitor created, apply it to my_wh
ALTER WAREHOUSE my_wh 
    SET RESOURCE_MONITOR = my_resource_monitor;

/* 6. Budgets */
-- Let's first create our budget
CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET my_budget()
    COMMENT = 'My Tasty Bytes Budget';


-------------------------------------------------------------------------
--RESET--
-------------------------------------------------------------------------
-- Drop created objects
DROP RESOURCE MONITOR IF EXISTS my_resource_monitor;
DROP TABLE IF EXISTS raw_pos.truck_dev;
-- Reset truck details
CREATE OR REPLACE TABLE raw_pos.truck_details
AS 
SELECT * EXCLUDE (year, make, model)
FROM raw_pos.truck;

DROP WAREHOUSE IF EXISTS my_wh;

-- Unset Query Tag
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Virtual Warehouses and Settings

Duration: 3

### Overview

Virtual Warehouses are the dynamic, scalable, and cost-effective computing power that lets you perform analysis on your Snowflake data. Their purpose is to handle all your data processing needs without you having to worry about the underlying technical details.

### Step 1 - Setting Context

First, lets set our session context. To run the queries, highlight the three queries at the top of your worksheet and click the "► Run" button.

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "getting_started_with_snowflake"}}';

USE DATABASE tb_101;
USE ROLE accountadmin;
```

### Step 2 - Creating a Warehouse

Let's create our first warehouse\! This command creates a new X-Small warehouse that will initially be suspended and will not auto-resume.

```sql
CREATE OR REPLACE WAREHOUSE my_wh
    COMMENT = 'My TastyBytes warehouse'
    WAREHOUSE_TYPE = 'standard'
    WAREHOUSE_SIZE = 'xsmall'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 2
    SCALING_POLICY = 'standard'
    AUTO_SUSPEND = 60
    INITIALLY_SUSPENDED = true,
    AUTO_RESUME = false;
```

> **Virtual Warehouses**: A virtual warehouse, often referred to simply as a “warehouse”, is a cluster of compute resources in Snowflake. Warehouses are required for queries, DML operations, and data loading. For more information, see the [Warehouse Overview](https://docs.snowflake.com/en/user-guide/warehouses-overview).

### Step 3 - Using and Resuming a Warehouse

Now that we have a warehouse, we must set it as the active warehouse for our session. Execute the next statement.

```sql
USE WAREHOUSE my_wh;
```

If you try to run a query now, it will fail, because the warehouse is suspended. Let's resume it and set it to auto-resume in the future.

```sql
ALTER WAREHOUSE my_wh RESUME;
ALTER WAREHOUSE my_wh SET AUTO_RESUME = TRUE;
```

Now, try the query again. It should execute successfully.

```sql
SELECT * FROM raw_pos.truck_details;
```

### Step 4 - Scaling a Warehouse

Warehouses in Snowflake are designed for elasticity. We can scale our warehouse up on the fly to handle a more intensive workload. Let's scale our warehouse to an X-Large.

```sql
ALTER WAREHOUSE my_wh SET warehouse_size = 'XLarge';
```

With our larger warehouse, let's run a query to calculate total sales per truck brand.

```sql
SELECT
    o.truck_brand_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.price) AS total_sales
FROM analytics.orders_v o
GROUP BY o.truck_brand_name
ORDER BY total_sales DESC;
```

<!-- \<img src="assets/query\_results\_pane.png"/\> -->

### Step 5 - Click Next --\>

## Using Persisted Query Results

Duration: 1

### Overview

This is a great place to demonstrate another powerful feature in Snowflake: the Query Result Cache. When you first ran the 'sales per truck' query, it likely took several seconds. If you run the exact same query again, the result will be nearly instantaneous.

### Step 1 - Re-running a Query

Run the same 'sales per truck' query from the previous step. Note the execution time in the query details pane. It should be much faster.

```sql
SELECT
    o.truck_brand_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.price) AS total_sales
FROM analytics.orders_v o
GROUP BY o.truck_brand_name
ORDER BY total_sales DESC;
```

> **Query Result Cache**: Results are retained for any query for 24 hours. Hitting the result cache requires almost no compute resources, making it ideal for frequently run reports or dashboards. The cache resides in the Cloud Services Layer, making it globally accessible to all users and warehouses in the account. For more information, please visit the [documentation on using persisted query results](https://docs.snowflake.com/en/user-guide/querying-persisted-results).

### Step 2 - Scaling Down

We will now be working with smaller datasets, so we can scale our warehouse back down to an X-Small to conserve credits.

```sql
ALTER WAREHOUSE my_wh SET warehouse_size = 'XSmall';
```

### Step 3 - Click Next --\>

## Basic Data Transformation Techniques

Duration: 3

### Overview

In this section, we will see some basic transformation techniques to clean our data and use Zero-Copy Cloning to create development environments. Our goal is to analyze the manufacturers of our food trucks, but this data is currently nested inside a `VARIANT` column.

### Step 1 - Creating a Development Table with Zero-Copy Clone

First, let's take a look at the `truck_build` column. 
```sql
SELECT truck_build FROM raw_pos.truck_details;
```
This table contains data about the make, model and year of each truck, but it is nested, or embedded in an Object. We can perform operations on this column to extract these values, but first we'll create a development copy of the table.

Let's create a development copy of our `truck_details` table. Snowflake's Zero-Copy Cloning lets us create an identical, fully independent copy of the table instantly, without using additional storage.

```sql
CREATE OR REPLACE TABLE raw_pos.truck_dev CLONE raw_pos.truck_details;
```

> **[Zero-Copy Cloning](https://docs.snowflake.com/en/user-guide/object-clone)**: Cloning creates a copy of a database object without duplicating the storage. Changes made to either the original or the clone are stored as new micro-partitions, leaving the other object untouched.

### Step 2 - Adding New Columns and Transforming Data

Now that we have a safe development table, let's add columns for `year`, `make`, and `model`. Then, we will extract the data from the `truck_build` `VARIANT` column and populate our new columns.

```sql
-- Add new columns
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS year NUMBER;
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS make VARCHAR(255);
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS model VARCHAR(255);

-- Extract and update data
UPDATE raw_pos.truck_dev
SET 
    year = truck_build:year::NUMBER,
    make = truck_build:make::VARCHAR,
    model = truck_build:model::VARCHAR;
```

### Step 3 - Cleaning the Data

Let's run a query to see the distribution of truck makes.

```sql
SELECT 
    make,
    COUNT(*) AS count
FROM raw_pos.truck_dev
GROUP BY make
ORDER BY make ASC;
```

We can see a data quality issue: 'Ford' and 'Ford\_' are being treated as separate manufacturers. Let's fix this with an `UPDATE` statement.

```sql
UPDATE raw_pos.truck_dev
    SET make = 'Ford'
    WHERE make = 'Ford_';
```

### Step 4 - Promoting to Production with SWAP

Our development table is now cleaned and correctly formatted. We can instantly promote it to be the new production table using the `SWAP WITH` command. This atomically swaps the two tables.

```sql
ALTER TABLE raw_pos.truck_details SWAP WITH raw_pos.truck_dev;
```

### Step 5 - Final Cleanup

Now that the swap is complete, we can drop the unnecessary `truck_build` column from our new production table. We also need to drop the old production table, which is now named `truck_dev`. But for the sake of the next lesson, we will "accidentally" drop the main table.

```sql
ALTER TABLE raw_pos.truck_details DROP COLUMN truck_build;

-- Accidentally drop the production table!
DROP TABLE raw_pos.truck_details;
```

### Step 6 - Click Next --\>

## Data Recovery with UNDROP

Duration: 2

### Overview

Oh no\! We accidentally dropped the production `truck_details` table. Luckily, Snowflake's Time Travel feature allows us to recover it instantly. The `UNDROP` command restores dropped objects.

### Step 1 - Verify the Drop

If you run a `DESCRIBE` command on the table, you will get an error stating it does not exist.

```sql
DESCRIBE TABLE raw_pos.truck_details;
```

### Step 2 - Restore the Table with UNDROP

Let's restore the `truck_details` table to the exact state it was in before being dropped.

```sql
UNDROP TABLE raw_pos.truck_details;
```

> **[Time Travel & UNDROP](https://docs.snowflake.com/en/user-guide/data-time-travel)**: Snowflake Time Travel enables accessing historical data at any point within a defined period. This allows for restoring data that has been modified or deleted. `UNDROP` is a feature of Time Travel that makes recovery from accidental drops trivial.

### Step 3 - Verify Restoration and Clean Up

Verify the table was successfully restored by selecting from it. Then, we can safely drop the actual development table, `truck_dev`.

```sql
-- Verify the table was restored
SELECT * from raw_pos.truck_details;

-- Now drop the real truck_dev table
DROP TABLE raw_pos.truck_dev;
```

### Step 4 - Click Next --\>

## Monitoring Cost with Resource Monitors

Duration: 2

### Overview

Monitoring compute usage is critical. Snowflake provides Resource Monitors to track warehouse credit usage. You can define credit quotas and trigger actions (like notifications or suspension) when thresholds are reached.

### Step 1 - Creating a Resource Monitor

Let's create a resource monitor for `my_wh`. This monitor has a monthly quota of 100 credits and will send notifications at 75% and suspend the warehouse at 90% and 100% of the quota. First, ensure your role is `accountadmin`.

```sql
USE ROLE accountadmin;

CREATE OR REPLACE RESOURCE MONITOR my_resource_monitor
    WITH CREDIT_QUOTA = 100
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 75 PERCENT DO NOTIFY
             ON 90 PERCENT DO SUSPEND
             ON 100 PERCENT DO SUSPEND_IMMEDIATE;
```

<!-- \<img src="assets/create\_rm.png"/\> -->

### Step 2 - Applying the Resource Monitor

With the monitor created, apply it to `my_wh`.

```sql
ALTER WAREHOUSE my_wh 
    SET RESOURCE_MONITOR = my_resource_monitor;
```

> For more information on what each configuration handles, please visit the documentation for [Working with Resource Monitors](https://docs.snowflake.com/en/user-guide/resource-monitors).

### Step 3 - Click Next --\>

## Monitoring Cost with Budgets

Duration: 2

### Overview

While Resource Monitors track warehouse usage, Budgets provide a more flexible approach to managing all Snowflake costs. Budgets can track spend on any Snowflake object and notify users when a dollar amount threshold is reached.

### Step 1 - Creating a Budget via SQL

Let's first create the budget object.

```sql
CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET my_budget()
    COMMENT = 'My Tasty Bytes Budget';
```

### Step 2 - Configuring the Budget in Snowsight

Configuring a budget is done through the Snowsight UI.

1.  Make sure your role is set to `ACCOUNTADMIN`.
2.  Navigate to **Admin** » **Cost Management** » **Budgets**.
3.  Click on the **MY\_BUDGET** budget we created.
4.  Click **Edit** in the Budget Details panel on the right.
5.  Set the **Spending Limit** to `100`.
6.  Enter a verified notification email address.
7.  Click **+ Tags & Resources** and add the **TB\_101.ANALYTICS** schema and the **TB\_DE\_WH** warehouse to be monitored.
8.  Click **Save Changes**.

<!-- \<img src="assets/budgets\_ui.png"/\> -->

> For a detailed guide on Budgets, please see the [Snowflake Budgets Documentation](https://docs.snowflake.com/en/user-guide/budgets).

### Step 3 - Click Next --\>

## Exploring with Universal Search

Duration: 1

### Overview

Universal Search allows you to easily find any object in your account, plus explore data products in the Marketplace, relevant Snowflake Documentation, and Community Knowledge Base articles.

### Step 1 - Searching for an Object

Let's try it now.

1.  Click **Search** in the Navigation Menu on the left.
2.  Enter `truck` into the search bar.
3.  Observe the results. You will see categories of objects on your account, such as tables and views, as well as relevant documentation.

### Step 2 - Using Natural Language Search

You can also use natural language. For example, search for: `Which truck franchise has the most loyal customer base?`
Universal search will return relevant tables and views, even highlighting columns that might help answer your question, providing an excellent starting point for analysis.

<!-- \<img src="assets/universal\_search.png"/\> -->

### Step 3 - Click Next --\>

## 2. Simple Data Pipeline
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** 
Asset:        Zero to Snowflake v2 - Simple Data Pipeline
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

## Module 3: [DUMMY VIGNETTE - ADD TITLE HERE]

Duration: 5

### Overview

*[Add a brief, one-paragraph overview of what the user will learn or build in this module. For example: "In this module, we will explore advanced data modeling techniques by building a star schema from our raw data..."]*

### [Add Sub-Section Title Here]

Duration: 2

*[Add a description for the first part of this module.]*

**Step 1:** *[Add description for the first step.]*

```sql
-- [Add SQL for Step 1 here]
```

**Step 2:** *[Add description for the second step.]*

```sql
-- [Add SQL for Step 2 here]
```

### [Add Another Sub-Section Title Here]

Duration: 3

*[Add a description for the second part of this module.]*

**Step 1:** *[Add description for the first step.]*

```sql
-- [Add SQL for Step 1 here]
```

### Click Next --\>

## 4. Governance with Horizon
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** 
Asset:        Zero to Snowflake v2 - Governance with Horizon
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "governance_with_horizon"}}';

USE ROLE useradmin;
USE DATABASE tb_101;
USE WAREHOUSE tb_dev_wh;

/* 1. Introduction to Roles and Access Control */
SHOW ROLES;

CREATE OR REPLACE ROLE tb_data_steward
    COMMENT = 'Custom Role';
    
USE ROLE securityadmin;
GRANT OPERATE, USAGE ON WAREHOUSE tb_dev_wh TO ROLE tb_data_steward;

GRANT USAGE ON DATABASE tb_101 TO ROLE tb_data_steward;
GRANT USAGE ON ALL SCHEMAS IN DATABASE tb_101 TO ROLE tb_data_steward;

GRANT SELECT ON ALL TABLES IN SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT ALL ON SCHEMA governance TO ROLE tb_data_steward;
GRANT ALL ON ALL TABLES IN SCHEMA governance TO ROLE tb_data_steward;

GRANT ROLE tb_data_steward TO USER USER;

USE ROLE tb_data_steward;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

/* 2. Tag-Based Classification with Auto Tagging */
USE ROLE accountadmin;

CREATE OR REPLACE TAG governance.pii;
GRANT APPLY TAG ON ACCOUNT TO ROLE tb_data_steward;

GRANT EXECUTE AUTO CLASSIFICATION ON SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE tb_data_steward;
GRANT CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE ON SCHEMA governance TO ROLE tb_data_steward;

USE ROLE tb_data_steward;

CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE
  governance.tb_classification_profile(
    {
      'minimum_object_age_for_classification_days': 0,
      'maximum_classification_validity_days': 30,
      'auto_tag': true
    });
    
CALL governance.tb_classification_profile!SET_TAG_MAP(
  {'column_tag_map':[
    {
      'tag_name':'tb_101.governance.pii',
      'tag_value':'pii',
      'semantic_categories':['NAME', 'PHONE_NUMBER', 'POSTAL_CODE', 'DATE_OF_BIRTH', 'CITY', 'EMAIL']
    }]});
    
CALL SYSTEM$CLASSIFY('tb_101.raw_customer.customer_loyalty', 'tb_101.governance.tb_classification_profile');

SELECT 
    column_name,
    tag_database,
    tag_schema,
    tag_name,
    tag_value,
    apply_method
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('raw_customer.customer_loyalty', 'table'));

/* 3. Column-level Security with Masking Policies */
CREATE OR REPLACE MASKING POLICY governance.mask_string_pii AS (original_value STRING)
RETURNS STRING ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN '****MASKED****'
    ELSE original_value
  END;
  
CREATE OR REPLACE MASKING POLICY governance.mask_date_pii AS (original_value DATE)
RETURNS DATE ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN DATE_TRUNC('year', original_value)
    ELSE original_value
  END;
  
ALTER TAG governance.pii SET
    MASKING POLICY governance.mask_string_pii,
    MASKING POLICY governance.mask_date_pii;
    
USE ROLE public;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

USE ROLE tb_admin;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

/* 4. Row Level Security with Row Access Policies */
USE ROLE tb_data_steward;

CREATE OR REPLACE TABLE governance.row_policy_map
    (role STRING, country_permission STRING);
    
INSERT INTO governance.row_policy_map
    VALUES('tb_data_engineer', 'United States');
    
CREATE OR REPLACE ROW ACCESS POLICY governance.customer_loyalty_policy
    AS (country STRING) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') 
        OR EXISTS 
            (
            SELECT 1
                FROM governance.row_policy_map rp
            WHERE
                UPPER(rp.role) = CURRENT_ROLE()
                AND rp.country_permission = country
            );
            
ALTER TABLE raw_customer.customer_loyalty
    ADD ROW ACCESS POLICY governance.customer_loyalty_policy ON (country);
    
USE ROLE tb_data_engineer;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

/* 5. Data Quality Monitoring with Data Metric Functions */
USE ROLE tb_data_steward;

SELECT SNOWFLAKE.CORE.NULL_PERCENT(SELECT customer_id FROM raw_pos.order_header);
SELECT SNOWFLAKE.CORE.DUPLICATE_COUNT(SELECT order_id FROM raw_pos.order_header); 
SELECT SNOWFLAKE.CORE.AVG(SELECT order_total FROM raw_pos.order_header);

CREATE OR REPLACE DATA METRIC FUNCTION governance.invalid_order_total_count(
    order_prices_t table(order_total NUMBER, unit_price NUMBER, quantity INTEGER))
RETURNS NUMBER
AS
'SELECT COUNT(*) FROM order_prices_t WHERE order_total != unit_price * quantity';

INSERT INTO raw_pos.order_detail
SELECT 904745311, 459520442, 52, null, 0, 2, 5.0, 5.0, null;

SELECT governance.invalid_order_total_count(
    SELECT price, unit_price, quantity FROM raw_pos.order_detail
) AS num_orders_with_incorrect_price;
    
ALTER TABLE raw_pos.order_detail
    SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';
    
ALTER TABLE raw_pos.order_detail
    ADD DATA METRIC FUNCTION governance.invalid_order_total_count
    ON (price, unit_price, quantity);

/* 6. Account Security Monitoring with the Trust Center */
USE ROLE accountadmin;
GRANT APPLICATION ROLE SNOWFLAKE.TRUST_CENTER_ADMIN TO ROLE tb_admin;
USE ROLE tb_admin;

-------------------------------------------------------------------------
--RESET--
-------------------------------------------------------------------------
USE ROLE accountadmin;

DROP ROLE IF EXISTS tb_data_steward;

ALTER TAG IF EXISTS governance.pii UNSET
    MASKING POLICY governance.mask_string_pii,
    MASKING POLICY governance.mask_date_pii;
DROP MASKING POLICY IF EXISTS governance.mask_string_pii;
DROP MASKING POLICY IF EXISTS governance.mask_date_pii;

ALTER SCHEMA IF EXISTS raw_customer UNSET CLASSIFICATION_PROFILE;
DROP SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE IF EXISTS tb_classification_profile;

ALTER TABLE IF EXISTS raw_customer.customer_loyalty 
    DROP ALL ROW ACCESS POLICIES;
DROP ROW ACCESS POLICY IF EXISTS governance.customer_loyalty_policy;

DELETE FROM raw_pos.order_detail WHERE order_detail_id = 904745311;
ALTER TABLE IF EXISTS raw_pos.order_detail
    DROP DATA METRIC FUNCTION governance.invalid_order_total_count ON (price, unit_price, quantity);
DROP FUNCTION IF EXISTS governance.invalid_order_total_count(TABLE(NUMBER, NUMBER, INTEGER));
ALTER TABLE IF EXISTS raw_pos.order_detail UNSET DATA_METRIC_SCHEDULE;

ALTER TABLE IF EXISTS raw_customer.customer_loyalty
  MODIFY
    COLUMN first_name UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN last_name UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN e_mail UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN phone_number UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN postal_code UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN marital_status UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN gender UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN birthday_date UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN country UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN city UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY;

DROP TAG IF EXISTS governance.pii;
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Introduction to Roles and Access Control

Duration: 2

### Overview

Snowflake's security model is built on a framework of Role-based Access Control (RBAC) and Discretionary Access Control (DAC). Access privileges are assigned to roles, which are then assigned to users. This creates a powerful and flexible hierarchy for securing objects.

> aside positive
> **[Access Control Overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)**: To learn more about the key concepts of access control in Snowflake, including securable objects, roles, privileges, and users.

### Step 1 - Set Context and View Existing Roles

First, let's set our context for this exercise and view the roles that already exist in the account.

```sql
USE ROLE useradmin;
USE DATABASE tb_101;
USE WAREHOUSE tb_dev_wh;

SHOW ROLES;
```

### Step 2 - Create a Custom Role

We will now create a custom `tb_data_steward` role. This role will be responsible for managing and protecting our customer data.

```sql
CREATE OR REPLACE ROLE tb_data_steward
    COMMENT = 'Custom Role';
```

The typical hierarchy of system and custom roles might look something like this:

```
                                +---------------+
                                | ACCOUNTADMIN  |
                                +---------------+
                                  ^    ^     ^
                                  |    |     |
                    +-------------+-+  |    ++-------------+
                    | SECURITYADMIN |  |    |   SYSADMIN   |<------------+
                    +---------------+  |    +--------------+             |
                            ^          |     ^        ^                  |
                            |          |     |        |                  |
                    +-------+-------+  |     |  +-----+-------+  +-------+-----+
                    |   USERADMIN   |  |     |  | CUSTOM ROLE |  | CUSTOM ROLE |
                    +---------------+  |     |  +-------------+  +-------------+
                            ^          |     |      ^              ^      ^
                            |          |     |      |              |      |
                            |          |     |      |              |    +-+-----------+
                            |          |     |      |              |    | CUSTOM ROLE |
                            |          |     |      |              |    +-------------+
                            |          |     |      |              |           ^
                            |          |     |      |              |           |
                            +----------+-----+---+--+--------------+-----------+
                                                 |
                                            +----+-----+
                                            |  PUBLIC  |
                                            +----------+
```

### Step 3 - Grant Privileges to the Custom Role

We can't do much with our role without granting privileges to it. Let's switch to the `securityadmin` role to grant our new `tb_data_steward` role the necessary permissions to use a warehouse and access our database schemas and tables.

```sql
USE ROLE securityadmin;

-- Grant warehouse usage
GRANT OPERATE, USAGE ON WAREHOUSE tb_dev_wh TO ROLE tb_data_steward;

-- Grant database and schema usage
GRANT USAGE ON DATABASE tb_101 TO ROLE tb_data_steward;
GRANT USAGE ON ALL SCHEMAS IN DATABASE tb_101 TO ROLE tb_data_steward;

-- Grant table-level privileges
GRANT SELECT ON ALL TABLES IN SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT ALL ON SCHEMA governance TO ROLE tb_data_steward;
GRANT ALL ON ALL TABLES IN SCHEMA governance TO ROLE tb_data_steward;
```

### Step 4 - Grant and Use the New Role

Finally, we grant the new role to our own user. Then we can switch to the `tb_data_steward` role and run a query to see what data we can access.

```sql
-- Grant role to your user
GRANT ROLE tb_data_steward TO USER USER;

-- Switch to the new role
USE ROLE tb_data_steward;

-- Run a test query
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

Looking at the query results, it's clear this table contains a lot of Personally Identifiable Information (PII). In the next sections, we'll learn how to protect it.

### Step 5 - Click Next --\>

## Tag-Based Classification with Auto Tagging

Duration: 3

### Overview

A key first step in data governance is identifying and classifying sensitive data. Snowflake Horizon's auto-tagging capability can automatically discover sensitive information by monitoring columns in your schemas. We can then use these tags to apply security policies.

> aside positive
> **[Automatic Classification](https://docs.snowflake.com/en/user-guide/classify-auto)**: Learn how Snowflake can automatically classify sensitive data based on a schedule, simplifying governance at scale.

### Step 1 - Create PII Tag and Grant Privileges

Using the `accountadmin` role, we'll create a `pii` tag in our `governance` schema. We will also grant the necessary privileges to our `tb_data_steward` role to perform classification.

```sql
USE ROLE accountadmin;

CREATE OR REPLACE TAG governance.pii;
GRANT APPLY TAG ON ACCOUNT TO ROLE tb_data_steward;

GRANT EXECUTE AUTO CLASSIFICATION ON SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE tb_data_steward;
GRANT CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE ON SCHEMA governance TO ROLE tb_data_steward;
```

### Step 2 - Create a Classification Profile

Now, as the `tb_data_steward`, we'll create a classification profile. This profile defines how auto-tagging will behave.

```sql
USE ROLE tb_data_steward;

CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE
  governance.tb_classification_profile(
    {
      'minimum_object_age_for_classification_days': 0,
      'maximum_classification_validity_days': 30,
      'auto_tag': true
    });
```

### Step 3 - Map Semantic Categories to the PII Tag

Next, we'll define a mapping that tells the classification profile to apply our `governance.pii` tag to any column whose `SEMANTIC_CATEGORY` matches common PII types like `NAME`, `PHONE_NUMBER`, `EMAIL`, etc.

```sql
CALL governance.tb_classification_profile!SET_TAG_MAP(
  {'column_tag_map':[
    {
      'tag_name':'tb_101.governance.pii',
      'tag_value':'pii',
      'semantic_categories':['NAME', 'PHONE_NUMBER', 'POSTAL_CODE', 'DATE_OF_BIRTH', 'CITY', 'EMAIL']
    }]});
```

### Step 4 - Run Classification and View Results

Let's manually trigger the classification process on our `customer_loyalty` table. Then, we can query the `INFORMATION_SCHEMA` to see the tags that were automatically applied.

```sql
-- Trigger classification
CALL SYSTEM$CLASSIFY('tb_101.raw_customer.customer_loyalty', 'tb_101.governance.tb_classification_profile');

-- View applied tags
SELECT 
    column_name,
    tag_database,
    tag_schema,
    tag_name,
    tag_value,
    apply_method
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('raw_customer.customer_loyalty', 'table'));
```

Notice that columns identified as PII now have our custom `governance.pii` tag applied.

### Step 5 - Click Next --\>

## Column-Level Security with Masking Policies

Duration: 3

### Overview

Now that our sensitive columns are tagged, we can use Dynamic Data Masking to protect them. A masking policy is a schema-level object that determines whether a user sees the original data or a masked version at query time. We can apply these policies directly to our `pii` tag.

> aside positive
> **[Column-level Security](https://docs.snowflake.com/en/user-guide/security-column-intro)**: Column-level Security includes Dynamic Data Masking and External Tokenization to protect sensitive data.

### Step 1 - Create Masking Policies

We'll create two policies: one to mask string data and one to mask date data. The logic is simple: if the user's role is not privileged (i.e., not `ACCOUNTADMIN` or `TB_ADMIN`), return a masked value. Otherwise, return the original value.

```sql
-- Create the masking policy for sensitive string data
CREATE OR REPLACE MASKING POLICY governance.mask_string_pii AS (original_value STRING)
RETURNS STRING ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN '****MASKED****'
    ELSE original_value
  END;

-- Now create the masking policy for sensitive DATE data
CREATE OR REPLACE MASKING POLICY governance.mask_date_pii AS (original_value DATE)
RETURNS DATE ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN DATE_TRUNC('year', original_value)
    ELSE original_value
  END;
```

### Step 2 - Apply Masking Policies to the Tag

The power of tag-based governance comes from applying the policy once to the tag. This action automatically protects all columns that have that tag, now and in the future.

```sql
ALTER TAG governance.pii SET
    MASKING POLICY governance.mask_string_pii,
    MASKING POLICY governance.mask_date_pii;
```

### Step 3 - Test the Policies

Let's test our work. First, switch to the unprivileged `public` role and query the table. The PII columns should be masked.

```sql
USE ROLE public;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

<!-- \<img src="assets/masked\_data.png"/\> -->

Now, switch to a privileged role, `tb_admin`. The data should now be fully visible.

```sql
USE ROLE tb_admin;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

<!-- \<img src="assets/unmasked\_data.png"/\> -->

### Step 4 - Click Next --\>

## Row-Level Security with Row Access Policies

Duration: 3

### Overview

In addition to masking columns, Snowflake allows you to filter which rows are visible to a user with Row Access Policies. The policy evaluates each row against rules you define, often based on the user's role or other session attributes.

> aside positive
> **[Row-level Security](https://docs.snowflake.com/en/user-guide/security-row-intro)**: Row Access Policies determine which rows are visible in a query result, enabling fine-grained access control.

### Step 1 - Create a Policy Mapping Table

A common pattern for row access policies is to use a mapping table that defines which roles can see which data. We'll create a table that maps roles to the `country` values they are permitted to see.

```sql
USE ROLE tb_data_steward;

CREATE OR REPLACE TABLE governance.row_policy_map
    (role STRING, country_permission STRING);

-- Map the tb_data_engineer role to only see 'United States' data
INSERT INTO governance.row_policy_map
    VALUES('tb_data_engineer', 'United States');
```

### Step 2 - Create the Row Access Policy

Now we create the policy itself. This policy returns `TRUE` (allowing the row to be seen) if the user's role is an admin role OR if the user's role exists in our mapping table and matches the `country` value of the current row.

```sql
CREATE OR REPLACE ROW ACCESS POLICY governance.customer_loyalty_policy
    AS (country STRING) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') 
        OR EXISTS 
            (
            SELECT 1 FROM governance.row_policy_map rp
            WHERE
                UPPER(rp.role) = CURRENT_ROLE()
                AND rp.country_permission = country
            );
```

### Step 3 - Apply and Test the Policy

Apply the policy to the `country` column of our `customer_loyalty` table. Then, switch to the `tb_data_engineer` role and query the table.

```sql
-- Apply the policy
ALTER TABLE raw_customer.customer_loyalty
    ADD ROW ACCESS POLICY governance.customer_loyalty_policy ON (country);

-- Switch role to test the policy
USE ROLE tb_data_engineer;

-- Query the table
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

The result set should now only contain rows where the `country` is 'United States'.

### Step 4 - Click Next --\>

## Data Quality Monitoring with Data Metric Functions

Duration: 2

### Overview

Data governance isn't just about security; it's also about trust and reliability. Snowflake helps maintain data integrity with Data Metric Functions (DMFs). You can use system-defined DMFs or create your own to run automated quality checks on your tables.

> aside positive
> **[Data Quality Monitoring](https://docs.snowflake.com/en/user-guide/data-quality-intro)**: Learn how to ensure data consistency and reliability using built-in and custom Data Metric Functions.

### Step 1 - Use System DMFs

Let's use a few of Snowflake's built-in DMFs to check the quality of our `order_header` table.

```sql
USE ROLE tb_data_steward;

-- This will return the percentage of null customer IDs.
SELECT SNOWFLAKE.CORE.NULL_PERCENT(SELECT customer_id FROM raw_pos.order_header);

-- We can use DUPLICATE_COUNT to check for duplicate order IDs.
SELECT SNOWFLAKE.CORE.DUPLICATE_COUNT(SELECT order_id FROM raw_pos.order_header); 

-- Average order total amount for all orders.
SELECT SNOWFLAKE.CORE.AVG(SELECT order_total FROM raw_pos.order_header);
```

### Step 2 - Create a Custom DMF

We can also create custom DMFs for our specific business logic. Let's create one that checks for orders where the `order_total` does not equal `unit_price * quantity`.

```sql
CREATE OR REPLACE DATA METRIC FUNCTION governance.invalid_order_total_count(
    order_prices_t table(
        order_total NUMBER,
        unit_price NUMBER,
        quantity INTEGER
    )
)
RETURNS NUMBER
AS
'SELECT COUNT(*)
 FROM order_prices_t
 WHERE order_total != unit_price * quantity';
```

### Step 3 - Test and Schedule the DMF

Let's insert a bad record to test our DMF. Then, we'll call the function to see if it catches the error.

```sql
-- Insert a record with an incorrect total price
INSERT INTO raw_pos.order_detail
SELECT 904745311, 459520442, 52, null, 0, 2, 5.0, 5.0, null;

-- Call the custom DMF on the order detail table.
SELECT governance.invalid_order_total_count(
    SELECT price, unit_price, quantity FROM raw_pos.order_detail
) AS num_orders_with_incorrect_price;
```

To automate this check, we can associate the DMF with the table and set a schedule to have it run automatically whenever the data changes.

```sql
ALTER TABLE raw_pos.order_detail
    SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';

ALTER TABLE raw_pos.order_detail
    ADD DATA METRIC FUNCTION governance.invalid_order_total_count
    ON (price, unit_price, quantity);
```

### Step 4 - Click Next --\>

## Account Security Monitoring with the Trust Center

Duration: 2

### Overview

The Trust Center provides a centralized dashboard for monitoring security risks across your entire Snowflake account. It uses scheduled scanners to check for issues like missing Multi-Factor Authentication (MFA), over-privileged roles, or inactive users, and then provides recommended actions.

> aside positive
> **[Trust Center Overview](https://docs.snowflake.com/en/user-guide/trust-center/overview)**: The Trust Center enables automatic checks to evaluate and monitor security risks on your account.

### Step 1 - Grant Privileges and Navigate to the Trust Center

First, an `ACCOUNTADMIN` needs to grant the `TRUST_CENTER_ADMIN` application role to a user or role. We'll grant it to our `tb_admin` role.

```sql
USE ROLE accountadmin;
GRANT APPLICATION ROLE SNOWFLAKE.TRUST_CENTER_ADMIN TO ROLE tb_admin;
USE ROLE tb_admin; 
```

Now, navigate to the Trust Center in the Snowsight UI:

1.  Click the **Monitoring** tab in the left navigation bar.
2.  Click on **Trust Center**.

\<img src="assets/trust\_center.png"/\>

### Step 2 - Enable Scanner Packages

By default, most scanner packages are disabled. Let's enable them to get a comprehensive view of our account's security posture.

1.  In the Trust Center, click the **Scanner Packages** tab.
2.  Click on **CIS Benchmarks**.
3.  Click the **Enable Package** button.
4.  In the modal, set the **Frequency** to `Monthly` and click **Continue**.
5.  Repeat this process for the **Threat Intelligence** scanner package.

### Step 3 - Review Findings

After the scanners have had a moment to run, navigate back to the **Findings** tab.

  - You will see a dashboard summarizing violations by severity.
  - The list below details each violation, its severity, and the scanner that found it.
  - Clicking on any violation will open a details pane with a summary and recommended remediation steps.
  - You can filter the list by severity, status, or scanner package to focus on the most critical issues.

This powerful tool gives you a continuous, actionable overview of your Snowflake account's security health.

### Step 4 - Click Next --\>

## 5. Apps & Collaboration
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** 
Asset:        Zero to Snowflake v2 - Apps & Collaboration
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "apps_and_collaboration"}}';

USE DATABASE tb_101;
USE ROLE accountadmin;
USE WAREHOUSE tb_de_wh;

/* 1. Acquiring weather data from Snowflake Marketplace */
USE ROLE tb_analyst;

/* 2. Integrating Account Data with Weather Source Data */
SELECT 
    DISTINCT city_name,
    AVG(max_wind_speed_100m_mph) AS avg_wind_speed_mph,
    AVG(avg_temperature_air_2m_f) AS avg_temp_f,
    AVG(tot_precipitation_in) AS avg_precipitation_in,
    MAX(tot_snowfall_in) AS max_snowfall_in
FROM zts_weathersource.onpoint_id.history_day
WHERE country = 'US'
GROUP BY city_name;

CREATE OR REPLACE VIEW harmonized.daily_weather_v
COMMENT = 'Weather Source Daily History filtered to Tasty Bytes supported Cities'
    AS
SELECT
    hd.*,
    TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm,
    pc.city_name AS city,
    c.country AS country_desc
FROM zts_weathersource.onpoint_id.history_day hd
JOIN zts_weathersource.onpoint_id.postal_codes pc
    ON pc.postal_code = hd.postal_code
    AND pc.country = hd.country
JOIN raw_pos.country c
    ON c.iso_country = hd.country
    AND c.city = hd.city_name;

SELECT
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    AVG(dw.avg_temperature_air_2m_f) AS average_temp_f
FROM harmonized.daily_weather_v dw
WHERE dw.country_desc = 'Germany'
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = 2022
    AND MONTH(date_valid_std) = 2
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;

CREATE OR REPLACE VIEW analytics.daily_sales_by_weather_v
COMMENT = 'Daily Weather Metrics and Orders Data'
AS
WITH daily_orders_aggregated AS (
    SELECT
        DATE(o.order_ts) AS order_date,
        o.primary_city,
        o.country,
        o.menu_item_name,
        SUM(o.price) AS total_sales
    FROM
        harmonized.orders_v o
    GROUP BY ALL
)
SELECT
    dw.date_valid_std AS date,
    dw.city_name,
    dw.country_desc,
    ZEROIFNULL(doa.total_sales) AS daily_sales,
    doa.menu_item_name,
    ROUND(dw.avg_temperature_air_2m_f, 2) AS avg_temp_fahrenheit,
    ROUND(dw.tot_precipitation_in, 2) AS avg_precipitation_inches,
    ROUND(dw.tot_snowdepth_in, 2) AS avg_snowdepth_inches,
    dw.max_wind_speed_100m_mph AS max_wind_speed_mph
FROM
    harmonized.daily_weather_v dw
LEFT JOIN
    daily_orders_aggregated doa
    ON dw.date_valid_std = doa.order_date
    AND dw.city_name = doa.primary_city
    AND dw.country_desc = doa.country
ORDER BY 
    date ASC;
    
SELECT * EXCLUDE (city_name, country_desc, avg_snowdepth_inches, max_wind_speed_mph)
FROM analytics.daily_sales_by_weather_v
WHERE 
    country_desc = 'United States'
    AND city_name = 'Seattle'
    AND avg_precipitation_inches >= 1.0
ORDER BY date ASC;

/* 3. Explore Safegraph POI data */
CREATE OR REPLACE VIEW harmonized.tastybytes_poi_v
AS 
SELECT 
    l.location_id,
    sg.postal_code,
    sg.country,
    sg.city,
    sg.iso_country_code,
    sg.location_name,
    sg.top_category,
    sg.category_tags,
    sg.includes_parking_lot,
    sg.open_hours
FROM raw_pos.location l
JOIN zts_safegraph.public.frostbyte_tb_safegraph_s sg 
    ON l.location_id = sg.location_id
    AND l.iso_country_code = sg.iso_country_code;
    
SELECT TOP 3
    p.location_id,
    p.city,
    p.postal_code,
    AVG(hd.max_wind_speed_100m_mph) AS average_wind_speed
FROM harmonized.tastybytes_poi_v AS p
JOIN
    zts_weathersource.onpoint_id.history_day AS hd
    ON p.postal_code = hd.postal_code
WHERE
    p.country = 'United States'
    AND YEAR(hd.date_valid_std) = 2022
GROUP BY p.location_id, p.city, p.postal_code
ORDER BY average_wind_speed DESC;

WITH TopWindiestLocations AS (
    SELECT TOP 3
        p.location_id
    FROM harmonized.tastybytes_poi_v AS p
    JOIN
        zts_weathersource.onpoint_id.history_day AS hd
        ON p.postal_code = hd.postal_code
    WHERE
        p.country = 'United States'
        AND YEAR(hd.date_valid_std) = 2022
    GROUP BY p.location_id, p.city, p.postal_code
    ORDER BY AVG(hd.max_wind_speed_100m_mph) DESC
)
SELECT
    o.truck_brand_name,
    ROUND(
        AVG(CASE WHEN hd.max_wind_speed_100m_mph <= 20 THEN o.order_total END),
    2) AS avg_sales_calm_days,
    ZEROIFNULL(ROUND(
        AVG(CASE WHEN hd.max_wind_speed_100m_mph > 20 THEN o.order_total END),
    2)) AS avg_sales_windy_days
FROM analytics.orders_v AS o
JOIN
    zts_weathersource.onpoint_id.history_day AS hd
    ON o.primary_city = hd.city_name
    AND DATE(o.order_ts) = hd.date_valid_std
WHERE o.location_id IN (SELECT location_id FROM TopWindiestLocations)
GROUP BY o.truck_brand_name
ORDER BY o.truck_brand_name;
    
----------------------------------------------------------------------------------
-- Reset Script
----------------------------------------------------------------------------------
USE ROLE accountadmin;

DROP VIEW IF EXISTS harmonized.daily_weather_v;
DROP VIEW IF EXISTS analytics.daily_sales_by_weather_v;
DROP VIEW IF EXISTS harmonized.tastybytes_poi_v;

ALTER WAREHOUSE tb_de_wh SUSPEND;
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Acquiring Data from Snowflake Marketplace

Duration: 2

### Overview

One of our analysts wants to see how weather impacts food truck sales. To do this, he'll use the Snowflake Marketplace to get live weather data from Weather Source, which can then be joined directly with our own sales data. The Marketplace allows us to access live, ready-to-query data from third-party providers without any data duplication or ETL.

> aside positive
> **[Introduction to the Snowflake Marketplace](https://docs.snowflake.com/en/user-guide/data-sharing-intro)**: The Marketplace provides a centralized hub to discover and access a wide variety of third-party data, applications, and AI products.

### Step 1 - Set Initial Context

First, let's set our context to use the `accountadmin` role, which is required to acquire data from the Marketplace.

```sql
USE DATABASE tb_101;
USE ROLE accountadmin;
USE WAREHOUSE tb_de_wh;
```

### Step 2 - Acquire Weather Source Data

Follow these steps in the Snowsight UI to get the Weather Source data:

1.  Make sure you are using the `ACCOUNTADMIN` role.
2.  Navigate to **Data Products** » **Marketplace** from the left-hand navigation menu.
3.  In the search bar, enter: `Weather Source frostbyte`.
4.  Click on the **Weather Source LLC: frostbyte** listing.
5.  Click the **Get** button.
6.  In the options, change the **Database name** to `ZTS_WEATHERSOURCE`.
7.  Grant access to the **PUBLIC** role.
8.  Click **Get**.

<!-- \<img src="assets/marketplace\_listing.png"/\> -->

This process makes the Weather Source data instantly available in our account as a new database, ready to be queried.

### Step 3 - Click Next --\>

## Integrating Account Data with Shared Data

Duration: 3

### Overview

With the Weather Source data now in our account, our analyst can immediately begin joining it with our existing Tasty Bytes data. There's no need to wait for an ETL job to run.

### Step 1 - Explore the Shared Data

Let's switch to the `tb_analyst` role and begin exploring the new weather data. We'll start by getting a list of all distinct US cities available in the share, along with some average weather metrics.

```sql
USE ROLE tb_analyst;

SELECT 
    DISTINCT city_name,
    AVG(max_wind_speed_100m_mph) AS avg_wind_speed_mph,
    AVG(avg_temperature_air_2m_f) AS avg_temp_f,
    AVG(tot_precipitation_in) AS avg_precipitation_in,
    MAX(tot_snowfall_in) AS max_snowfall_in
FROM zts_weathersource.onpoint_id.history_day
WHERE country = 'US'
GROUP BY city_name;
```

### Step 2 - Create an Enriched View

Now, let's create a view that joins our raw `country` data with the historical daily weather data from the Weather Source share. This gives us a unified view of weather metrics for the cities where Tasty Bytes operates.

```sql
CREATE OR REPLACE VIEW harmonized.daily_weather_v
COMMENT = 'Weather Source Daily History filtered to Tasty Bytes supported Cities'
    AS
SELECT
    hd.*,
    TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm,
    pc.city_name AS city,
    c.country AS country_desc
FROM zts_weathersource.onpoint_id.history_day hd
JOIN zts_weathersource.onpoint_id.postal_codes pc
    ON pc.postal_code = hd.postal_code
    AND pc.country = hd.country
JOIN raw_pos.country c
    ON c.iso_country = hd.country
    AND c.city = hd.city_name;
```

### Step 3 - Analyze and Visualize Enriched Data

Using our new view, the analyst can query for the average daily temperature in Hamburg, Germany for February 2022. We can then visualize this as a line chart directly in Snowsight.

1.  Run the query below.
2.  In the **Results** pane, click **Chart**.
3.  Set the **Chart Type** to `Line`.
4.  Set the **X-Axis** to `DATE_VALID_STD`.
5.  Set the **Y-Axis** to `AVERAGE_TEMP_F`.

<!-- end list -->

```sql
SELECT
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    AVG(dw.avg_temperature_air_2m_f) AS average_temp_f
FROM harmonized.daily_weather_v dw
WHERE dw.country_desc = 'Germany'
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = 2022
    AND MONTH(date_valid_std) = 2
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;
```

<!-- \<img src="assets/line\_chart.png"/\> -->

### Step 4 - Create a Sales and Weather View

Let's take it a step further and combine our `orders_v` view with our new `daily_weather_v` to see how sales correlate with weather conditions.

```sql
CREATE OR REPLACE VIEW analytics.daily_sales_by_weather_v
COMMENT = 'Daily Weather Metrics and Orders Data'
AS
WITH daily_orders_aggregated AS (
    SELECT DATE(o.order_ts) AS order_date, o.primary_city, o.country,
        o.menu_item_name, SUM(o.price) AS total_sales
    FROM harmonized.orders_v o
    GROUP BY ALL
)
SELECT
    dw.date_valid_std AS date, dw.city_name, dw.country_desc,
    ZEROIFNULL(doa.total_sales) AS daily_sales, doa.menu_item_name,
    ROUND(dw.avg_temperature_air_2m_f, 2) AS avg_temp_fahrenheit,
    ROUND(dw.tot_precipitation_in, 2) AS avg_precipitation_inches,
    ROUND(dw.tot_snowdepth_in, 2) AS avg_snowdepth_inches,
    dw.max_wind_speed_100m_mph AS max_wind_speed_mph
FROM harmonized.daily_weather_v dw
LEFT JOIN daily_orders_aggregated doa
    ON dw.date_valid_std = doa.order_date
    AND dw.city_name = doa.primary_city
    AND dw.country_desc = doa.country
ORDER BY date ASC;
```

### Step 5 - Answer a Business Question

Our analyst can now answer complex business questions, such as: "How does significant precipitation impact our sales figures in the Seattle market?"

```sql
SELECT * EXCLUDE (city_name, country_desc, avg_snowdepth_inches, max_wind_speed_mph)
FROM analytics.daily_sales_by_weather_v
WHERE 
    country_desc = 'United States'
    AND city_name = 'Seattle'
    AND avg_precipitation_inches >= 1.0
ORDER BY date ASC;
```

### Step 6 - Click Next --\>

## Exploring Point-of-Interest (POI) Data

Duration: 3

### Overview

Our analyst now wants more insight into the specific locations of our food trucks. We can get Point-of-Interest (POI) data from Safegraph, another provider on the Snowflake Marketplace, to enrich our analysis even further.

### Step 1 - Acquire Safegraph POI Data

Follow the same procedure as before to acquire the Safegraph data from the Marketplace.

1.  Ensure you are using the `ACCOUNTADMIN` role.
2.  Navigate to **Data Products** » **Marketplace**.
3.  In the search bar, enter: `safegraph frostbyte`.
4.  Select the **Safegraph: frostbyte** listing and click **Get**.
5.  In the options, set the **Database name** to `ZTS_SAFEGRAPH`.
6.  Grant access to the **PUBLIC** role.
7.  Click **Get**.

### Step 2 - Create a POI View

Let's create a view that joins our internal `location` data with the Safegraph POI data.

```sql
CREATE OR REPLACE VIEW harmonized.tastybytes_poi_v
AS 
SELECT 
    l.location_id, sg.postal_code, sg.country, sg.city, sg.iso_country_code,
    sg.location_name, sg.top_category, sg.category_tags,
    sg.includes_parking_lot, sg.open_hours
FROM raw_pos.location l
JOIN zts_safegraph.public.frostbyte_tb_safegraph_s sg 
    ON l.location_id = sg.location_id
    AND l.iso_country_code = sg.iso_country_code;
```

### Step 3 - Combine POI and Weather Data

Now we can combine all three datasets: our internal data, the weather data, and the POI data. Let's find our top 3 windiest truck locations in the US in 2022.

```sql
SELECT TOP 3
    p.location_id, p.city, p.postal_code,
    AVG(hd.max_wind_speed_100m_mph) AS average_wind_speed
FROM harmonized.tastybytes_poi_v AS p
JOIN zts_weathersource.onpoint_id.history_day AS hd
    ON p.postal_code = hd.postal_code
WHERE
    p.country = 'United States'
    AND YEAR(hd.date_valid_std) = 2022
GROUP BY p.location_id, p.city, p.postal_code
ORDER BY average_wind_speed DESC;
```

### Step 4 - Analyze Brand Resilience to Weather

Finally, let's conduct a more complex analysis to determine brand resilience. We'll use a Common Table Expression (CTE) to first find the windiest locations, and then compare sales on "calm" vs. "windy" days for each truck brand at those locations. This can help inform operational decisions, like offering "Windy Day" promotions for brands that are less resilient.

```sql
WITH TopWindiestLocations AS (
    SELECT TOP 3
        p.location_id
    FROM harmonized.tastybytes_poi_v AS p
    JOIN zts_weathersource.onpoint_id.history_day AS hd ON p.postal_code = hd.postal_code
    WHERE p.country = 'United States' AND YEAR(hd.date_valid_std) = 2022
    GROUP BY p.location_id, p.city, p.postal_code
    ORDER BY AVG(hd.max_wind_speed_100m_mph) DESC
)
SELECT
    o.truck_brand_name,
    ROUND(AVG(CASE WHEN hd.max_wind_speed_100m_mph <= 20 THEN o.order_total END), 2) AS avg_sales_calm_days,
    ZEROIFNULL(ROUND(AVG(CASE WHEN hd.max_wind_speed_100m_mph > 20 THEN o.order_total END), 2)) AS avg_sales_windy_days
FROM analytics.orders_v AS o
JOIN zts_weathersource.onpoint_id.history_day AS hd
    ON o.primary_city = hd.city_name AND DATE(o.order_ts) = hd.date_valid_std
WHERE o.location_id IN (SELECT location_id FROM TopWindiestLocations)
GROUP BY o.truck_brand_name
ORDER BY o.truck_brand_name;
```

### Step 5 - Click Next --\>

## Conclusion and Next Steps

Duration: 1

### Conclusion

Congratulations\! You have successfully completed the entire Tasty Bytes - Zero to Snowflake journey.

You have now built and configured warehouses, cloned and transformed data, recovered a dropped table with Time Travel, built an automated data pipeline for semi-structured data, implemented a robust governance framework with roles and policies, and seamlessly enriched your own data with live datasets from the Snowflake Marketplace.

If you would like to re-run this Quickstart, please run the complete `RESET` script located at the bottom of your worksheet.

### Next Steps

To continue your journey in the Snowflake AI Data Cloud, please now visit the link below to see all other Powered by Tasty Bytes - Quickstarts available to you.

  - ### [Powered by Tasty Bytes - Quickstarts Table of Contents](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html#3)
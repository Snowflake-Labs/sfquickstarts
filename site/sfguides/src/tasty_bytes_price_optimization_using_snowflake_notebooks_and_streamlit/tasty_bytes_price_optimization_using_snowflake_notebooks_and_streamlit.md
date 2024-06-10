author: Joviane Bellegarde
id: tasty_bytes_price_optimization_using_snowflake_notebooks_and_streamlit
summary: Price Optimization Using Snowflake Notebooks and Streamlit
categories: Tasty-Bytes, Getting-Started
environments: web
status: Unpublished
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Price Optimization, Notebooks

# Price Optimization using Snowflake Notebooks and Streamlit in Snowflake
<!-- ------------------------ -->
## Overview
Duration: 1
<img src="assets/price_optimization_header.png"/>

Tasty Bytes is one of the largest food truck networks in the world with localized menu options spread across 15 food truck brands globally. Tasty Bytes is aiming to achieve 25% YoY sales growth over 5 years. Price optimization enables Tasty Bytes to achieve this goal by determining the right prices for their menu items to maximize profitability while maintaining customer satisfaction. 

### Prerequisites
- A Supported Snowflake [Browser](https://docs.snowflake.com/en/user-guide/setup#browser-requirements)
- A Snowflake Account
    - If you do not have a Snowflake Account, please [**sign up for a Free 30 Day Trial Account**](https://signup.snowflake.com/). When signing up, please make sure to select **Enterprise** edition. You can choose any AWS or Azure [Snowflake Region](https://docs.snowflake.com/en/user-guide/intro-regions).
    - After registering, you will receive an email with an activation link and your Snowflake Account URL.

### What does this Quickstart aim to solve?
- In the Machine Learning with Snowpark section for this vignette, we will train & deploy an ML model which leverages historical menu-item sale data to understand how menu-item demand changes with varying price. By utilizing this trained model, we would recommend the optimal day of week prices for all menu-items for the upcoming month to our food-truck brands.

#### Data Exploration
- Connect to Snowflake
- Snowpark DataFrame API

#### Feature Engineering
- Window & Aggregate functions
- Imputation and train/test split

#### Model Training & Deployment
- Train Snowpark ML model
- Register model on Model Registry

#### Model Untilization
- Stored prcedure to utilize deployed model
- Elsatic scalability
- Data Driven Insights

### What you will learn
In this Quickstart guide, we will implement price optimization for their diversified food-truck brands to inform their pricing and 
promotions by utilizing Snowflake Notebooks and Streamlit to:
- Train & deploy an ML model to understand how menu-item demand changes with varying price
- User-friendly application to use deployed ML-model to inform pricing strategies

<!-- ------------------------ -->
## Setting up Data in Snowflake
Duration: 3

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
- Create Snowflake objects (warehouse, database, schema, raw tables)
- Ingest data from S3 to raw tables

### Creating Objects, Loading Data, and Joining Data
- Navigate to Worksheets, click `+` in the top-right corner to create a new Worksheet, and choose `SQL Worksheet`.
- Paste and run both the following SQL in the worksheet to create Snowflake objects (warehouse, database, schema, raw tables), and ingest shift  data from S3
- [Price Optimization Setup SQL 1](https://github.com/Snowflake-Labs/sfguide-price-optimization-using-snowflake-notebooks-and-streamlit/blob/main/setup/po_setup_1.sql)
- [Price Optimization Setup SQL 2](https://github.com/Snowflake-Labs/sfguide-price-optimization-using-snowflake-notebooks-and-streamlit/blob/main/setup/po_setup_2.sql)

<!-- ------------------------ -->
## Machine Learning With Snowpark Part 1 - Price Optimization: Setting Up Snowflake Notebook
Duration 13

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.
- Download the notebook **tasty_bytes_price_optimization_and_recommendation.ipynb** using this repository [link](https://github.com/Snowflake-Labs/sfguide-price-optimization-using-snowflake-notebooks-and-streamlit/blob/main/notebook/tasty_bytes_price_optimization_and_recommendations.ipynb)
- Navigate to Notebooks in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) by clicking on Projects -> Notebook
- Using the import button on the top right, import the downloaded **tasty_bytes_price_optimization_and_recommendation.ipynb** notebook.
- Provide a name for the notebook and select appropriate database `JOVIANE_DEMO_TASTYBYTESPRICEOPTIMIZATION_PROD`, schema `ANALYTICS` and warehouse `JOVIANE_DEMO_TASTYBYTESPRICEOPTIMIZATION_DS_WH`.

- Open the notebook once created and add the following packages by using the "Packages" button on the top right and selecting their appropriate versions
    - matplotlib -> 3.7.3
    - ipywidgets -> latest
    - openpyxl -> latest
    - scikit-learn -> 1.2.2
    - snowflake-ml-python -> 1.4.0
    - shap -> latest
    - numpy -> 1.24.3
    - xgboost -> 1.7.3
    - seaborn -> latest

Once the notebook has uploaded, scroll down to cell 39 and click on `Run all above`.
<img src="assets/cell39.png"/>

<!-- ------------------------ -->
## Machine Learning With Snowpark Part 2 - Price Recommendations
Duration 3

### Overview
- Navigate to Worksheets, click `+` in the top-right corner to create a new Worksheet, and choose `SQL Worksheet`.
- Paste and run the following SQL in the worksheet to create Snowflake objects (warehouse, database, schema, raw tables)
```
/***************************************************************************************************
  _______           _            ____          _
 |__   __|         | |          |  _ \        | |
    | |  __ _  ___ | |_  _   _  | |_) | _   _ | |_  ___  ___
    | | / _` |/ __|| __|| | | | |  _ < | | | || __|/ _ \/ __|
    | || (_| |\__ \| |_ | |_| | | |_) || |_| || |_|  __/\__ \
    |_| \__,_||___/ \__| \__, | |____/  \__, | \__|\___||___/
                          __/ |          __/ |
                         |___/          |___/
Demo:         Tasty Bytes - Price Optimization SiS
Version:      v1
Vignette:     2 - SiS with Snowpark
Script:       setup_step_1_sis_tables_role.sql         
Create Date:  2023-06-08
Author:       Marie Coolsaet
Copyright(c): 2023 Snowflake Inc. All rights reserved.
****************************************************************************************************
Description: 
   Create tables used in SiS Streamlit App for Setting Monthly Pricing
****************************************************************************************************
SUMMARY OF CHANGES
Date(yyyy-mm-dd)    Author              Comments
------------------- ------------------- ------------------------------------------------------------
2023-06-08        Marie Coolsaet      Initial Release
2024-03-07        Shriya Rai          Update with Snowpark ML 
***************************************************************************************************/

/*----------------------------------------------------------------------------------
Instructions: Run all of this script to create the required tables and roles for the SiS app.

Note: In order for these scripts to run you will need to have run the notebook in
tasty_bytes_price_optimization.ipynb in 1 - Machine Learning with Snowpark.

 ----------------------------------------------------------------------------------*/

USE ROLE joviane_demo_tastybytespriceoptimization_data_scientist;
USE WAREHOUSE joviane_demo_tastybytespriceoptimization_ds_wh;

ALTER warehouse joviane_demo_tastybytespriceoptimization_ds_wh SET warehouse_size='large';

-- create the table that the app will write back to
CREATE OR REPLACE TABLE joviane_demo_tastybytespriceoptimization_prod.analytics.pricing_final (
    brand VARCHAR(16777216),
    item VARCHAR(16777216),
    day_of_week VARCHAR(16777216),
    new_price FLOAT,
    current_price FLOAT,
    recommended_price FLOAT,
    profit_lift FLOAT,
    comment VARCHAR(16777216),
    timestamp TIMESTAMP_NTZ(9)
);

-- create the table with required pricing information for the app
CREATE OR REPLACE TABLE joviane_demo_tastybytespriceoptimization_prod.analytics.pricing_detail AS
SELECT 
    a.truck_brand_name AS brand,
    a.menu_item_name AS item,
    case 
        when a.day_of_week = 0 then '7 - Sunday'
        when a.day_of_week = 1 then '1 - Monday'
        when a.day_of_week = 2 then '2 - Tuesday'
        when a.day_of_week = 3 then '3 - Wednesday'
        when a.day_of_week = 4 then '4 - Thursday'
        when a.day_of_week = 5 then '5 - Friday'
        else '6 - Saturday'
    end as day_of_week,
    round(b.price::FLOAT,2) AS current_price,
    round(a.price::FLOAT,2) AS recommended_price,
    joviane_demo_tastybytespriceoptimization_prod.analytics.DEMAND_ESTIMATION_MODEL!PREDICT(
        current_price,
        current_price - c.base_price,
        c.base_price,
        c.price_hist_dow,
        c.price_year_dow,
        c.price_month_dow,
        c.price_change_hist_dow,
        c.price_change_year_dow,
        c.price_change_month_dow,
        c.price_hist_roll,
        c.price_year_roll,
        c.price_month_roll,
        c.price_change_hist_roll,
        c.price_change_year_roll,
        c.price_change_month_roll):DEMAND_ESTIMATION::INT AS current_price_demand,
    joviane_demo_tastybytespriceoptimization_prod.analytics.DEMAND_ESTIMATION_MODEL!PREDICT(
        recommended_price,
        recommended_price - c.base_price,
        c.base_price,
        c.price_hist_dow,
        c.price_year_dow,
        c.price_month_dow,
        c.price_change_hist_dow,
        c.price_change_year_dow,
        c.price_change_month_dow,
        c.price_hist_roll,
        c.price_year_roll,
        c.price_month_roll,
        c.price_change_hist_roll,
        c.price_change_year_roll,
        c.price_change_month_roll):DEMAND_ESTIMATION::INT AS recommended_price_demand,
    round(((recommended_price_demand
        * (d.prev_avg_profit_wo_item 
            + recommended_price 
            - round(a.cost_of_goods_usd,2))) 
            - (current_price_demand
        * (d.prev_avg_profit_wo_item 
            + current_price 
            - round(a.cost_of_goods_usd,2))))
            ,0) AS profit_lift,
    c.base_price,
    c.price_hist_dow,
    c.price_year_dow,
    c.price_month_dow,
    c.price_change_hist_dow,
    c.price_change_year_dow,
    c.price_change_month_dow,
    c.price_hist_roll,
    c.price_year_roll,
    c.price_month_roll,
    c.price_change_hist_roll,
    c.price_change_year_roll,
    c.price_change_month_roll,
    d.prev_avg_profit_wo_item AS average_basket_profit,
    round(a.cost_of_goods_usd,2) AS item_cost,
    recommended_price_demand * (average_basket_profit
            + recommended_price 
            - item_cost) AS recommended_price_profit,
    current_price_demand * (average_basket_profit
            + current_price
            - item_cost) AS current_price_profit
FROM (
SELECT p.*,m.menu_item_name FROM joviane_demo_tastybytespriceoptimization_prod.analytics.price_recommendations p 
left join joviane_demo_tastybytespriceoptimization_prod.raw_pos.menu m on p.menu_item_id=m.menu_item_id) a
LEFT JOIN (SELECT * FROM joviane_demo_tastybytespriceoptimization_prod.analytics.demand_est_input_full WHERE (month = 3) AND (year=2023)) b
ON  a.day_of_week = b.day_of_week AND a.menu_item_id = b.menu_item_id
LEFT JOIN (SELECT * FROM joviane_demo_tastybytespriceoptimization_prod.analytics.demand_est_input_full WHERE (month = 4) AND (year=2023)) c
ON a.day_of_week = c.day_of_week AND a.menu_item_id = c.menu_item_id
LEFT JOIN (SELECT * FROM joviane_demo_tastybytespriceoptimization_prod.analytics.order_item_cost_agg_v WHERE (month = 4) AND (year=2023)) d
ON a.menu_item_id = d.menu_item_id
ORDER BY brand, item, day_of_week;

-- create pricing table to be displayed in the app
CREATE OR REPLACE TABLE joviane_demo_tastybytespriceoptimization_prod.analytics.pricing 
AS SELECT
brand, 
item, 
day_of_week, 
current_price AS new_price, 
current_price, 
recommended_price, 
profit_lift
FROM joviane_demo_tastybytespriceoptimization_prod.analytics.pricing_detail;

-- create brand manager role
USE ROLE securityadmin;
CREATE ROLE IF NOT EXISTS joviane_demo_tastybytespriceoptimization_brand_manager;

-- grant roles to user
SET my_user_var = (SELECT  '"' || CURRENT_USER() || '"' );
GRANT ROLE joviane_demo_tastybytespriceoptimization_data_scientist TO USER identifier($my_user_var);
GRANT ROLE joviane_demo_tastybytespriceoptimization_brand_manager TO USER identifier($my_user_var);

-- grant usage privileges for app
GRANT USAGE ON DATABASE joviane_demo_tastybytespriceoptimization_prod TO ROLE joviane_demo_tastybytespriceoptimization_brand_manager;
GRANT USAGE ON SCHEMA joviane_demo_tastybytespriceoptimization_prod.analytics TO ROLE joviane_demo_tastybytespriceoptimization_brand_manager;
```

Now, return to the notebook that was created in **Machine Learning With Snowpark Part 1 - Price Optimization: Setting Up Snowflake Notebook** and scroll down to cell 39 and click on `Run cell and advance`.

## Streamlit in Snowflake
Duration 3
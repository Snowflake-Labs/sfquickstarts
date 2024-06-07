author: Joviane Bellegarde
id: tasty_bytes_price_optimization_using_snowflake_notebooks_and_streamlit
summary: Price Optimization Using Snowflake Notebooks and Streamlit
categories: Tasty-Bytes, Getting-Started
environments: web
status: Unpublished
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Price Optimization, Notebooks

# Extracting Insights from Unstructured Data with Document AI
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
- 

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

## Setting up Data in Snowflake
Duration: 3

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
- Create Snowflake objects (warehouse, database, schema, raw tables)
- Ingest data from S3 to raw tables

### Creating Objects, Loading Data, and Joining Data
- Navigate to Worksheets, click `+` in the top-right corner to create a new Worksheet, and choose `SQL Worksheet`.
- Paste and run both the following SQL in the worksheet to create Snowflake objects (warehouse, database, schema, raw tables), and ingest shift  data from S3
- [Price Optimization Setup SQL 1](https://github.com/Snowflake-Labs/sfguide-price-optimization-using-snowflake-notebooks-and-streamlit/blob/main/po_setup_1.sql)
- [Price Optimization Setup SQL 2](https://github.com/Snowflake-Labs/sfguide-price-optimization-using-snowflake-notebooks-and-streamlit/blob/main/po_setup_2.sql)

## Setting up Snowflake Notebook
Duration 3

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.

- Download the notebook 

author: Pavan Pothukuchi, Caleb Baechtold, Lucy Zhu, Sho Tanaka
id: getting-started-with-cortex-code-cli-for-data-science-ml
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Build a customer lifetime value (LTV) prediction model and deploy it as a real-time REST endpoint on SPCS using Cortex Code CLI.
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with Cortex Code CLI for Data Science ML
<!-- ------------------------ -->
## Overview

[Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) is an AI-powered command-line coding agent that helps you build, debug, and deploy Snowflake applications through natural language conversations. In this quickstart, you will use Cortex Code CLI to build a complete ML workflow — loading synthetic e-commerce transaction data, performing exploratory data analysis (EDA), training a customer lifetime value (LTV) prediction model, logging it to the Snowflake Model Registry, and deploying it as a real-time REST endpoint on Snowpark Container Services (SPCS).

This guide walks through the CLI experience, which works well for users comfortable with terminal workflows. The same prompts also work in [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight) and the Desktop app.

> **Important:** Cortex Code is powered by LLMs and is non-deterministic. The code it generates may differ from what is shown in this guide. Always review the output and verify that the results match your expectations before proceeding to the next step.

> If you prefer Snowsight Workspaces with interactive visualizations and Warehouse-based batch inference, see the companion guide: [Getting Started with Cortex Code in Snowsight for Data Science ML](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-code-in-snowsight-for-data-science-ml/).

### What You Will Learn

- How to perform EDA and feature engineering using natural language prompts
- How to train and compare multiple regression models inside Snowflake
- How to log models with metrics to the Snowflake Model Registry
- How to deploy a model as a REST API on Snowpark Container Services (SPCS)
- How to profile inference latency for a real-time endpoint

### What You Will Build

An end-to-end customer LTV prediction pipeline including:
- A trained regression model that predicts a customer's total spend in the next 90 days
- A registered model in the Snowflake Model Registry with evaluation metrics
- A real-time inference REST endpoint on SPCS with latency profiling

### Prerequisites

- Access to a Snowflake account with a role that can create databases, schemas, tables, models, and compute pools. If you do not have access to an account, create a [free Snowflake trial account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) installed and configured
- Familiarity with basic ML concepts (training, evaluation, inference)

<!-- ------------------------ -->
## Setup

**Step 1.** Install Cortex Code CLI:

```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

After installing, run `cortex` and follow the setup wizard to connect to your Snowflake account.

For detailed installation and setup instructions, refer to the [Cortex Code CLI documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).

**Step 2.** Verify your connection. Once in a Cortex Code session, confirm you are connected and have the right permissions:

```
What role am I using and what databases can I access?
```

You are now ready to start building your ML pipeline.


**Step 3.** Copy the following SQL and paste it as a prompt in Cortex Code CLI to create the database objects and load the sample data. Alternatively, you can run [setup.sql](https://github.com/Snowflake-Labs/cortex-code-samples/blob/main/data-science-ml/setup.sql) in a [Snowsight SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-from-a-sql-file).

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS CORTEX_CODE_ML_DB;
CREATE SCHEMA IF NOT EXISTS CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA;
CREATE WAREHOUSE IF NOT EXISTS CORTEX_CODE_ML_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

USE DATABASE CORTEX_CODE_ML_DB;
USE SCHEMA CORTEX_CODE_ML_SCHEMA;
USE WAREHOUSE CORTEX_CODE_ML_WH;

CREATE OR REPLACE FILE FORMAT ml_csvformat
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TYPE = 'CSV';

CREATE OR REPLACE STAGE ml_ltv_data_stage
  FILE_FORMAT = ml_csvformat
  URL = 's3://sfquickstarts/sfguide_getting_started_with_cortex_code_for_ds_ml/ltv_transactions/';

CREATE OR REPLACE TABLE ML_LTV_TRANSACTIONS (
	CUSTOMER_ID VARCHAR(16777216),
	TRANSACTION_TIME TIMESTAMP_NTZ(9),
	AMOUNT NUMBER(12,2),
	PRODUCT_CATEGORY VARCHAR(15),
	CHANNEL VARCHAR(8)
);

COPY INTO ML_LTV_TRANSACTIONS
  FROM @ml_ltv_data_stage;

SELECT 'Setup complete — ML_LTV_TRANSACTIONS loaded.' AS STATUS;
```


<!-- ------------------------ -->
## Optional - Generate Synthetic Data

The `setup.sql` in the previous step already loads the `ML_LTV_TRANSACTIONS` table from S3. You can skip this step and proceed directly to Exploratory Data Analysis.

If you want to experience generating data with Cortex Code, use the following prompt. Note that this will **replace** the pre-loaded data.

```
Generate realistic looking synthetic e-commerce transaction data in
CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA. Create a table ML_LTV_TRANSACTIONS
with ~100000 transactions from ~500 customers over an 18-month period. Include
CUSTOMER_ID, TRANSACTION_TIME, AMOUNT, PRODUCT_CATEGORY, and CHANNEL. Make the
data realistic: customers should have varying purchase frequencies (some buy
weekly, others monthly), amounts should vary by category (electronics $50-$2000,
groceries $10-$200, apparel $20-$500), and channels should be web, mobile, or
in-store. About 10% of customers should be high-value (frequent buyers with
higher average spend).
```

> Replace `CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA` with your target database and schema if you have one.

Cortex Code generates the SQL or Python code to create and populate the table, then executes it in your Snowflake account.

<!-- ------------------------ -->
## Confirm Sample Data

Before you start EDA and model training, confirm that the sample dataset is loaded:

```
Confirm that #CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA.ML_LTV_TRANSACTIONS exists and that it contains data. Show me:
- total row count and number of unique customers
- date range of transactions
- average transaction amount by product category
- a few sample rows
```

> **Tip:** The `#` prefix tells Cortex Code CLI to resolve the table reference directly, grounding the conversation to that specific object.

If the table is empty (or missing), re-run `setup.sql` from the Setup section and repeat the steps above.

After you run the prompt, you should see a summary (row count, customer count, date range, and category breakdown) and a small sample of rows.

<!-- ------------------------ -->
## Exploratory Data Analysis (EDA)

Next, analyze the patterns in the data to identify the right features for predicting customer lifetime value:

```
#CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA.ML_LTV_TRANSACTIONS Do EDA and recommend the features needed to train a regression model that can predict each customer's total spend in the next 90 days
```

Cortex Code produces analysis code. While rich visualizations are best viewed by opening the generated Notebook in VS Code or Jupyter, the CLI will still output the key findings and feature recommendations as text.

The EDA step typically reveals patterns such as:
- High-value customers purchase more frequently and have higher average order values
- Recency of last purchase is a strong predictor of future spend
- Certain product categories correlate with higher lifetime value
- Channel preferences (web vs. mobile vs. in-store) vary across customer segments

Cortex Code will recommend features to use in the model based on these findings.

> **Tip**: Run Cortex Code CLI inside a VS Code or Cursor terminal to view generated Notebook files side-by-side.

<!-- ------------------------ -->
## Train the Model

Now build the features and train a regression model:

```
#CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA.ML_LTV_TRANSACTIONS
Build those features and train a regression model to predict each customer's total spend in the next 90 days. Use two different algorithms and evaluate the best one. Use 20% of the data as the eval set.
```

Cortex Code will:
1. Engineer the features based on the EDA recommendations (per-customer aggregations over the training window)
2. Split the data into training (80%) and evaluation (20%) sets
3. Train two different regression algorithms (e.g., XGBoost and LightGBM)
4. Compare their performance using metrics such as RMSE, MAE, and R-squared
5. Recommend the better-performing model

Review the evaluation metrics to confirm the model meets your requirements before proceeding.

<!-- ------------------------ -->
## Log to Model Registry

Log the better model to the Snowflake Model Registry and deploy it as a REST endpoint on SPCS:

```
#CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA.ML_LTV_TRANSACTIONS
Log the better model with metrics into Snowflake Model Registry, and use SPCS to create a REST endpoint for online inference.
```

Cortex Code handles the `log_model()` call with appropriate parameters including model metrics, sample input for schema inference, and the target platform set to `SNOWPARK_CONTAINER_SERVICES`. It then creates the SPCS service and endpoint for real-time inference.

<!-- ------------------------ -->
## Run Online Inference

Generate sample customer profiles and run LTV predictions via the deployed REST endpoint, then profile the latency:

```
Create feature profiles for 50 customers and run LTV predictions using the REST
API for online inference running on SPCS. Show the top 10 highest predicted LTV
customers and a latency profile (p50, p95, p99).
```

Cortex Code sends HTTP requests to the SPCS REST endpoint and displays results including:
- Predicted 90-day spend for each customer profile
- Per-request latency measurements
- A latency profile summary (p50, p95, p99) to help you understand the real-time performance characteristics of your deployment

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You have successfully built a customer LTV prediction model and deployed it as a real-time REST endpoint on SPCS using Cortex Code CLI.

### What You Learned

- How to use Cortex Code CLI to generate realistic synthetic data with natural language prompts
- How to perform exploratory data analysis and feature engineering conversationally
- How to train, compare, and select regression models inside Snowflake
- How to log models with metrics to the Snowflake Model Registry
- How to deploy a model as a REST API on SPCS for online inference
- How to profile inference latency for a real-time endpoint

### Related Resources

- [Getting Started with Cortex Code in Snowsight for Data Science ML](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-code-in-snowsight-for-data-science-ml/) — companion guide for Snowsight + Warehouse batch inference
- [Cortex Code CLI Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Cortex Code in Snowsight Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
- [Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Best Practices for Cortex Code CLI](https://www.snowflake.com/en/developers/guides/best-practices-cortex-code-cli/)

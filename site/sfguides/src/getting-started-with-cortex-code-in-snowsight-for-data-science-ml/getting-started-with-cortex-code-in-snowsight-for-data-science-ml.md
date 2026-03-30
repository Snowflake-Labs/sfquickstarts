author: Pavan Pothukuchi, Caleb Baechtold, Lucy Zhu, Sho Tanaka
id: getting-started-with-cortex-code-in-snowsight-for-data-science-ml
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Build a fraud detection ML model end-to-end using Cortex Code in Snowsight — from synthetic data generation to model training, registry, and batch inference.
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with Cortex Code in Snowsight for Data Science ML
<!-- ------------------------ -->
## Overview

[Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) is an AI-powered coding agent that helps you build, debug, and deploy Snowflake applications through natural language conversations. In this quickstart, you will use Cortex Code in Snowsight Workspaces to build a complete ML workflow — generating synthetic financial transaction data, performing exploratory data analysis (EDA), training a fraud detection model, logging it to the Snowflake Model Registry, and running batch inference on a Snowflake Warehouse.

This guide walks through the Snowsight Workspaces experience, which offers an interactive environment with visualizations, a curated Python environment, and automated Notebook cell creation and execution. The same prompts also work in the [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).

> **Important:** Cortex Code is powered by LLMs and is non-deterministic. The code it generates may differ from what is shown in this guide. Always review the output and verify that the results match your expectations before proceeding to the next step.

> If you prefer to use the CLI and deploy to SPCS for real-time inference, see the companion guide: [Getting Started with Cortex Code CLI for Data Science ML](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-code-cli-for-data-science-ml/).

### What You Will Learn

- How to perform EDA and feature engineering using natural language prompts
- How to train and compare multiple ML models inside Snowflake
- How to log models with metrics to the Snowflake Model Registry
- How to run batch inference on a Snowflake Warehouse

### What You Will Build

An end-to-end fraud detection pipeline including:
- A synthetic financial transactions dataset (~100,000 rows with ~0.5% fraud)
- A trained binary classification model (comparing two algorithms)
- A registered model in the Snowflake Model Registry with evaluation metrics
- Batch inference predictions via Snowflake Warehouse

### Prerequisites

- Access to a Snowflake account with a role that can create databases, schemas, tables, and models. If you do not have access to an account, create a [free Snowflake trial account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).
- Familiarity with basic ML concepts (training, evaluation, inference)

<!-- ------------------------ -->
## Setup

**Step 1.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/cortex-code-samples/blob/main/data-science-ml/setup.sql) to execute all statements in order from top to bottom.

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

CREATE OR REPLACE STAGE ml_fraud_data_stage
  FILE_FORMAT = ml_csvformat
  URL = 's3://sfquickstarts/sfguide_getting_started_with_cortex_code_for_ds_ml/fraud_transactions/';

CREATE OR REPLACE TABLE ML_FRAUD_TRANSACTIONS (
  TRANSACTION_ID NUMBER(38,0),
  TRANSACTION_TIME TIMESTAMP_NTZ(9),
  AMOUNT NUMBER(10,2),
  MERCHANT VARCHAR(16777216),
  LOCATION VARCHAR(16777216),
  IS_FRAUD BOOLEAN
);

COPY INTO ML_FRAUD_TRANSACTIONS
  FROM @ml_fraud_data_stage;

SELECT 'Setup complete — ML_FRAUD_TRANSACTIONS loaded.' AS STATUS;
```

**Step 2.** Create or open a **Workspace** from the left navigation.

**Step 3.** Open the **Cortex Code** editor from the right-hand side panel.

You are now ready to start prompting Cortex Code to build your ML pipeline.

<!-- ------------------------ -->
## Optional - Generate Synthetic Data

The `setup.sql` in the previous step already loads the `ML_FRAUD_TRANSACTIONS` table from S3. You can skip this step and proceed directly to Exploratory Data Analysis.

If you want to experience generating data with Cortex Code, use the following prompt. Note that this will **replace** the pre-loaded data.

```
Generate realistic looking synthetic data in CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA. Create a table
ML_FRAUD_TRANSACTIONS with 100000 financial transactions where ~0.5% of
them are fraudulent. Include Amount, Location, Merchant, and Time. Make the
fraudulent ones look suspicious based on location or amount, but add realistic
noise: ~1/3 of fraud transactions should have normal-looking patterns (typical
amounts, common locations, regular hours), and ~2% of legitimate transactions
should have suspicious characteristics (high amounts, unusual locations, or odd
hours).
```

> Replace `CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA` with your target database and schema if you have.

Cortex Code generates the SQL or Python code to create and populate the table, then executes it in your Snowflake account. You will see the code and results appear in a new Notebook in your Workspace.

<!-- ------------------------ -->
## Confirm Sample Data

Before you start EDA and model training, confirm that the sample dataset is loaded and that Cortex Code is “grounded” to the right database and schema.

### Select the Schema in Cortex Code

1. In your Workspace, open the **Cortex Code** panel on the right.
2. Click **+**.
3. Select **CORTEX_CODE_ML_SCHEMA** (in `CORTEX_CODE_ML_DB`).

![Select the schema for this quickstart](assets/snowsight-cortex-code-select-schema.jpg)

### Verify the Table Exists and Has Rows

Use Cortex Code with the following prompt:

```
Confirm that CORTEX_CODE_ML_DB.CORTEX_CODE_ML_SCHEMA.ML_FRAUD_TRANSACTIONS exists and that it contains data. Show me:
- row count
- fraud rate (percent where IS_FRAUD = TRUE)
- a few sample rows
```

If the table is empty (or missing), re-run `setup.sql` from the Setup section and repeat the steps above.

After you run the prompt, you should see a short summary (row count and fraud rate) and a small sample of rows.

![Sample data verification result in Cortex Code](assets/snowsight-cortex-code-confirm-sample-data.jpg)


<!-- ------------------------ -->
## Exploratory Data Analysis (EDA)

Next, analyze the patterns in the data to identify the right features for the model:

```
Do EDA and recommend the features needed to train a model that can predict fraud
```

Cortex Code typically breaks this into multiple steps (for example, analyzing amount, location, time-based patterns, and top merchants) and then summarizes key findings with recommended features.

![EDA results and feature recommendations in Cortex Code](assets/snowsight-cortex-code-eda-feature-recommendations.jpg)

In this example, Cortex Code identifies signals such as higher average amounts for fraud, fraud hotspots by location/merchant, and time-of-day effects. These insights translate into features like log(amount), hour-of-day/day-of-week, and categorical encodings for merchant and location.


The EDA step typically reveals patterns such as:
- Fraudulent transactions tend to have higher amounts
- Certain locations or merchant categories have elevated fraud rates
- Transactions at unusual hours may correlate with fraud

Cortex Code will recommend features to use in the model based on these findings.

<!-- ------------------------ -->
## Train the Model

Now build the features and train a classification model:

```
Build those features and train a model. Let's use two different algorithms and evaluate the best one. Use 20% of the data as the eval set.
```

Cortex Code typically creates a Notebook, generates feature engineering steps, trains two models, and reports evaluation metrics so you can choose the best performer.

![Training and evaluation workflow created by Cortex Code](assets/snowsight-cortex-code-train-two-models.jpg)

In this example, Cortex Code generates SQL/Python for feature engineering, runs training/evaluation steps, and produces a comparison section (metrics like AUC, precision/recall, and a confusion matrix) to help you pick the best model.

Cortex Code will:
1. Engineer the features based on the EDA recommendations
2. Split the data into training (80%) and evaluation (20%) sets
3. Train two different classification algorithms (e.g., Random Forest and XGBoost)
4. Compare their performance using metrics such as precision, recall, F1 score, and AUC-ROC
5. Recommend the better-performing model

Review the evaluation metrics to confirm the model meets your requirements before proceeding.

<!-- ------------------------ -->
## Log to Model Registry

Log the better model to the Snowflake Model Registry configured for Warehouse-based batch inference:

```
Log the better model with metrics into Snowflake Model Registry, and use Snowflake Warehouse for inference.
```

Cortex Code handles the `log_model()` call with appropriate parameters including model metrics, sample input for schema inference, and the target platform set to `WAREHOUSE`.

![Model logged to Snowflake Model Registry with metrics](assets/snowsight-cortex-code-model-registry-log-model.jpg)

In this example, the output confirms the model was registered successfully and shows key evaluation metrics recorded with the model version.

<!-- ------------------------ -->
## Run Batch Inference

Generate sample data and run batch predictions:

```
Create 100 sample requests with a mix of potential fraud and legit transactions and run the predictions for them.
```

![Batch inference results for 100 sample requests](assets/snowsight-cortex-code-batch-inference-100-requests.jpg)

In this example, Cortex Code generates the 100 requests, runs inference via your Snowflake Warehouse, and summarizes the predicted fraud vs. legitimate counts (with a detailed results table).

Cortex Code creates test transactions and calls the registered model's `predict` method using your Snowflake Warehouse. The results include the predicted class (fraud/legitimate) along with probability scores.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You have successfully built and deployed a fraud detection ML model using Cortex Code in Snowsight — from data generation through batch inference on a Snowflake Warehouse.

### What You Learned

- How to use Cortex Code in Snowsight to generate realistic synthetic data with natural language prompts
- How to perform exploratory data analysis and feature engineering conversationally
- How to train, compare, and select ML models inside Snowflake
- How to log models with metrics to the Snowflake Model Registry
- How to run batch inference on a Snowflake Warehouse

### Related Resources

- [Getting Started with Cortex Code CLI for Data Science ML](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-code-cli-for-data-science-ml/) — companion guide for CLI + SPCS online inference
- [Cortex Code in Snowsight Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
- [Cortex Code CLI Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Credit Card Fraud Detection using Snowflake ML](https://www.snowflake.com/en/developers/guides/credit-card-fraud-detection-using-snowflake-ml/)
- [Best Practices for Cortex Code CLI](https://www.snowflake.com/en/developers/guides/best-practices-cortex-code-cli/)


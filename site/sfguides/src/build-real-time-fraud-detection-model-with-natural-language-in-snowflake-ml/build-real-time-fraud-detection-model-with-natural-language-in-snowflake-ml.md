author: Chanin Nantasenamat, Sumit Kumar, Lucy Zhu
id: build-real-time-fraud-detection-model-with-natural-language-in-snowflake-ml
summary: Learn how to build a production-ready fraud detection system with real-time inference using Cortex Code and natural language prompts in Snowflake ML
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Machine Learning, Snowflake ML, Model Registry, SPCS, Fraud Detection, Cortex Code

# Build a Real-Time Fraud Detection Model with Natural Language in Snowflake ML
<!-- ------------------------ -->
## Overview

Detect fraudulent transactions in real-time using a natural language first approach. This quickstart demonstrates how to go from raw idea to production-grade REST API in minutes, not weeks, using only natural language prompts with Cortex Code CLI.

### What You'll Learn
- Generate realistic synthetic fraud data with natural language prompts
- Train an XGBoost machine learning model for fraud detection
- Deploy models to Snowpark Container Services (SPCS) with one-click deployment
- Create REST API endpoints for real-time online inference

### What You'll Build
A complete fraud detection pipeline featuring:
- Synthetic transaction dataset with realistic fraud patterns
- Trained XGBoost classification model
- Live REST API endpoint running on SPCS
- Performance benchmarking with latency profiling

![End-to-end fraud detection pipeline](assets/diagram.png)

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with `ACCOUNTADMIN` role (or a role with permissions for Snowflake ML and SPCS)
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) installed and configured
- A dedicated Snowflake warehouse
- A compute pool configured for SPCS

<!-- ------------------------ -->
## Setup

### Install Cortex Code CLI

Follow the [official installation guide](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) to install and configure Cortex Code CLI.

### Verify SPCS Access

Ensure you have access to create and manage compute pools. You can verify this in Snowsight under Admin > Compute Pools.

<!-- ------------------------ -->
## Generate Synthetic Data

The first step is creating realistic synthetic data for training our fraud detection model. Using Cortex Code CLI, we can generate this data with a simple natural language prompt.

### Prompt

Open Cortex Code CLI and enter the following prompt:

```
Generate realistic looking synthetic data in database ML and schema PROJECTS 
(create if it doesn't exist). Create a table Fraud_ML_TEST_ONLINE with 10000 
financial transactions where ~0.5% of them are fraudulent. Include Amount, 
Location, Merchant, and Time. Make the fraudulent ones look suspicious based 
on location or amount, but add realistic noise: ~1/3 of fraud transactions 
should have normal-looking patterns (typical amounts, common locations, 
regular hours), and ~2% of legitimate transactions should have suspicious 
characteristics (high amounts, unusual locations, or odd hours).
```

### What Gets Generated

Cortex Code will create the database, schema, and table, then insert 10,000 transactions with the specified fraud distribution:

```
✓  SNOWFLAKE_SQL_EXECUTE  Insert 10000 synthetic fraud transactions
  SQL Result (1 rows × 1 cols)
  ┌─────┬─────────────────────────┐
  │   # │ number of rows inserted │
  ├─────┼─────────────────────────┤
  │   1 │ 10000                   │
  └─────┴─────────────────────────┘
```

After verification, you will see a detailed breakdown:

```
Fraud Distribution (50 rows, 0.50%)

┌───────────────────────────────────────────────────────────────────────────┬───────┬──────────┐
│ Pattern                                                                   │ Count │ Avg Amt  │
├───────────────────────────────────────────────────────────────────────────┼───────┼──────────┤
│ Suspicious fraud (unusual locations, high amounts)                        │ 33    │ $5,532   │
├───────────────────────────────────────────────────────────────────────────┼───────┼──────────┤
│ Stealth fraud (normal-looking patterns)                                   │ 17    │ $112     │
└───────────────────────────────────────────────────────────────────────────┴───────┴──────────┘

Legitimate Transactions with Noise (9,950 rows)

┌─────────────────────────────────────┬───────┬────────────┐
│ Pattern                             │ Count │ Avg Amount │
├─────────────────────────────────────┼───────┼────────────┤
│ Normal legit                        │ 9,650 │ $200       │
├─────────────────────────────────────┼───────┼────────────┤
│ Suspicious legit: unusual location  │ 199   │ $2,825     │
├─────────────────────────────────────┼───────┼────────────┤
│ Suspicious legit: high amount       │ 101   │ $501       │
└─────────────────────────────────────┴───────┴────────────┘
```

<!-- ------------------------ -->
## Explore the Data

Before training a model, we need to understand our data patterns. Cortex Code can create a complete EDA notebook with a single prompt.

### Prompt

```
Create a Snowflake notebook and do exploratory data analysis and recommend 
the features needed to train a model that can predict fraud.
```

### What Gets Generated

Cortex Code will generate and upload a Snowflake notebook:

```
✓  BASH  cortex artifact create notebook fraud_eda
  ├─ "success": true,
  ├─ "message": "Successfully uploaded notebook 'fraud_eda' to snow://workspace/USER$.PUBLIC.DEFAULT$"
```

The notebook contains 16 cells organized into 7 sections:

```
┌──────────────────────────┬───────────────────────────────────────────────────────────────────┐
│ Section                  │ Content                                                           │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 1. Dataset Overview      │ Shape, types, nulls, fraud rate, amount summary stats             │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 2. Amount Analysis       │ Histograms (fraud vs legit), box plots, log-transformed distrib.  │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 3. Temporal Patterns     │ Fraud rate by hour-of-day, day-of-week, night vs daytime          │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 4. Location Analysis     │ Country/city fraud rates, domestic vs international breakdown     │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 5. Merchant Analysis     │ Fraud rate by category and merchant name, card type breakdown     │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 6. Feature Interactions  │ Cross-tabs (amount x location, amount x time), correlation heatm. │
├──────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ 7. Feature Recommend.    │ 20 recommended features with definitions and rationale            │
└──────────────────────────┴───────────────────────────────────────────────────────────────────┘
```

The notebook recommends 20 features across these categories:

- Amount (4): raw, log-transformed, z-score, percentile
- Temporal (5): hour, is_night, is_weekend, day_of_week, cyclical hour encoding
- Location (3): is_domestic, country risk score, city fraud rate
- Merchant (3): category risk score, merchant fraud rate, is_high_risk_category
- Card (1): card type encoding
- Interaction (4): high_amount x foreign, high_risk_cat x night, amount x country_risk, foreign x night

Open it in Snowsight to review the analysis and feature recommendations.

<!-- ------------------------ -->
## Train the Model

With our features identified, we can now train a machine learning model. XGBoost is an excellent choice for fraud detection due to its ability to handle imbalanced datasets and capture complex patterns.

### Prompt

```
Use features generated above to train a XGBoost machine learning model for 
real-time fraud detection.
```

### What Gets Generated

Cortex Code will first create a feature engineering view with all 24 features:

```
✓  SNOWFLAKE_SQL_EXECUTE  Create feature engineering view
  SQL Result (1 rows × 1 cols)
  ┌─────┬────────────────────────────────┐
  │   # │ status                         │
  ├─────┼────────────────────────────────┤
  │   1 │ View FRAUD_FEATURES_V success. │
  └─────┴────────────────────────────────┘
```

Then train the model and display results:

```
FRAUD DETECTION MODEL TRAINING
============================================================
Loading features from ML.PROJECTS.FRAUD_FEATURES_V...
Loaded 10000 rows with 24 features

Training XGBoost with scale_pos_weight=199...

EVALUATION RESULTS
------------------------------------------------------------
              precision    recall  f1-score   support
           0       1.00      0.97      0.98      1990
           1       0.14      0.80      0.24        10

ROC-AUC Score: 0.9723

CONFUSION MATRIX
------------------------------------------------------------
[[1928   62]
 [   2    8]]

TOP 10 FEATURES BY IMPORTANCE
------------------------------------------------------------
MERCHANT_FRAUD_RATE      0.2341
CATEGORY_RISK_SCORE      0.1892
COUNTRY_RISK_SCORE       0.1456
...

5-FOLD CROSS-VALIDATION
------------------------------------------------------------
AUC scores: [0.9634, 0.9012, 0.9567, 0.8923, 0.9401]
Mean AUC: 0.9307 (+/- 0.0352)
```

The model achieves a ROC-AUC of 0.9723 with 80% recall on fraud cases.

<!-- ------------------------ -->
## Deploy to SPCS

Now comes the powerful part: deploying our trained model to production with a single prompt. This would traditionally require containerization, infrastructure setup, and API development.

### Prompt

```
Use machine-learning skill to log the model into Snowflake Model Registry, 
deploy the model to SPCS and create a REST endpoint for online inference.
```

### What Gets Generated

This single prompt triggers a complete deployment pipeline. First, the model is registered:

```
MODEL REGISTRATION
============================================================
Registering model as ML.PROJECTS.FRAUD_XGBOOST_MODEL version V2...

✓  SNOWFLAKE_SQL_EXECUTE  Verify model V2 registration
  SQL Result (2 rows × 10 cols)
  ┌─────┬───────────────┬──────────────┬───────────────────┐
  │   # │ name          │ version_name │ min_num_arguments │
  ├─────┼───────────────┼──────────────┼───────────────────┤
  │   1 │ PREDICT       │ V2           │ 24                │
  │   2 │ PREDICT_PROBA │ V2           │ 24                │
  └─────┴───────────────┴──────────────┴───────────────────┘
```

Then deployed to SPCS (this takes several minutes as it builds the container):

```
✓  SNOWFLAKE_SQL_EXECUTE  Check if service exists now
  SQL Result (3 rows × 28 cols)
  ┌─────┬─────────────────────────┬─────────┬───────────────┬─────────────┐
  │   # │ name                    │ status  │ database_name │ schema_name │
  ├─────┼─────────────────────────┼─────────┼───────────────┼─────────────┤
  │   1 │ FRAUD_INFERENCE_SERVICE │ RUNNING │ ML            │ PROJECTS    │
  │   2 │ MODEL_BUILD_4A237CD4    │ DONE    │ ML            │ PROJECTS    │
  └─────┴─────────────────────────┴─────────┴───────────────┴─────────────┘

✓  SNOWFLAKE_SQL_EXECUTE  Get service endpoints for REST URL
  SQL Result (1 rows × 6 cols)
  ┌─────┬───────────┬───────┬──────────┬───────────┬────────────────────────────────────────────┐
  │   # │ name      │ port  │ protocol │ is_public │ ingress_url                                │
  ├─────┼───────────┼───────┼──────────┼───────────┼────────────────────────────────────────────┤
  │   1 │ inference │ 5000  │ HTTP     │ true      │ at5vt3-sriwlcc-ayb38567.snowflakecomputing │
  └─────┴───────────┴───────┴──────────┴───────────┴────────────────────────────────────────────┘
```

The service functions are tested via SQL:

```
✓  SNOWFLAKE_SQL_EXECUTE  Accuracy check - confusion matrix via SPCS service
  SQL Result (4 rows × 3 cols)
  ┌─────┬────────┬───────────┬───────┐
  │   # │ ACTUAL │ PREDICTED │ CNT   │
  ├─────┼────────┼───────────┼───────┤
  │   1 │ 0      │ 0         │ 9667  │
  │   2 │ 0      │ 1         │ 283   │
  │   3 │ 1      │ 0         │ 3     │
  │   4 │ 1      │ 1         │ 47    │
  └─────┴────────┴───────────┴───────┘
```

The model achieves 94% fraud recall, catching 47 out of 50 fraud cases.

<!-- ------------------------ -->
## Run Real-Time Inference

With our REST API deployed, let's test it with realistic traffic and analyze the performance characteristics.

### Prompt

```
Create 1000 sample requests with a mix of potential fraud and legit 
transactions and run the predictions using the REST API for online 
Inference running on SPCS and show the latency profile.
```

### What Gets Generated

Cortex Code will generate test transactions and run predictions through the SPCS service:

```
✓  SNOWFLAKE_SQL_EXECUTE  Test PREDICT_PROBA on fraud transactions
  SQL Result (10 rows × 4 cols)
  ┌──────┬────────────────┬──────────────┬────────┬────────────────────────────────┐
  │    # │ TRANSACTION_ID │ ACTUAL_FRAUD │ AMOUNT │ FRAUD_PROBABILITY              │
  ├──────┼────────────────┼──────────────┼────────┼────────────────────────────────┤
  │    1 │ TXN-000041     │ 1            │ 21.93  │ {"output_feature_0":0.43...    │
  │    2 │ TXN-000037     │ 1            │ 22.21  │ {"output_feature_0":0.36...    │
  │    3 │ TXN-000048     │ 1            │ 48.2   │ {"output_feature_0":0.63...    │
  └──────┴────────────────┴──────────────┴────────┴────────────────────────────────┘
```

For well-configured SPCS deployments, expect sub-second response times (mean: 50-150ms, p95: less than 300ms).

Cortex Code also outputs the SQL syntax for calling the service directly.

```
Service Functions (callable from SQL):

  -- Binary prediction (0/1)
  SELECT ML.PROJECTS.FRAUD_INFERENCE_SERVICE!PREDICT(
      AMOUNT, LOG_AMOUNT, AMOUNT_ZSCORE, AMOUNT_PERCENTILE,
      HOUR, IS_NIGHT, IS_WEEKEND, DAY_OF_WEEK, HOUR_SIN, HOUR_COS,
      IS_DOMESTIC, COUNTRY_RISK_SCORE, CITY_FRAUD_RATE,
      CATEGORY_RISK_SCORE, MERCHANT_FRAUD_RATE, IS_HIGH_RISK_CATEGORY,
      CARD_VISA, CARD_MASTERCARD, CARD_AMEX, CARD_DISCOVER,
      HIGH_AMOUNT_X_FOREIGN, HIGH_RISK_CAT_X_NIGHT, AMOUNT_X_COUNTRY_RISK, FOREIGN_X_NIGHT
  );
  
  -- Probability scores (output_feature_1 = fraud probability)
  SELECT ML.PROJECTS.FRAUD_INFERENCE_SERVICE!PREDICT_PROBA(...);
```

<!-- ------------------------ -->
## Handle Errors Gracefully

During any natural language coding session, errors are inevitable. The great thing about Cortex Code is its ability to assess the situation, environment, and error in order to fix issues automatically.

### Common Scenarios

**Notebook Execution Issues**

When a Jupyter kernel fails to connect, Cortex Code detects the issue and finds an alternative approach.

```
×  NOTEBOOK:EXECUTE_CELL  fraud_eda.ipynb cell 1
  └─ Cell execution failed (Jupyter server may have stopped): Tool error: Error executing tool exe...

* The notebook tool keeps using the hostname which can't be resolved. Let me take a different
  approach - I'll build the complete notebook as an .ipynb file directly, then upload it to
  Snowflake. This is more reliable.

✓  BASH  python3 -c "import json; cells = []..."
  └─ ... (334 more lines)

* Notebook file built with 16 cells. Let me mark the completed steps and upload to Snowflake.
```

**Artifact Upload Failures**

If an upload fails due to missing resources, Cortex Code investigates and finds a working path.

```
×  BASH  cortex artifact create notebook fraud_eda ... --location ML.PROJ...
  └─ {"error":"Error creating artifact: Upload failed: SQL compilation error:\nSch...

* The notebook needs a workspace. Let me check what's available and create one if needed.

✓  SNOWFLAKE_SQL_EXECUTE  List existing workspaces
  SQL Result (1 rows × 7 cols)
  │   1 │ DEFAULT$ │ USER$DATAPROFESSOR │ PUBLIC │

* There's a default workspace. Let me upload to it.

✓  BASH  cortex artifact create notebook fraud_eda ... --connection trial...
  └─ "success": true
```

**Model Training Errors**

When training fails due to parameter issues, Cortex Code diagnoses and fixes the problem automatically.

```
×  BASH  SNOWFLAKE_CONNECTION_NAME=trial ... train_fraud_model.py
  └─ ... AttributeError: best_iteration requires early stopping ...

* Need to fix: best_iteration requires early stopping. Let me fix the script.

✓  EDIT  /Users/cnantasenamat/fraud-eda/train_fraud_model.py +12 -12

* Running the fixed training script.

✓  BASH  SF_SKIP_WARNING_FOR_READ_PERMISSIONS_ON_CONFIG_FILE=true ...
  ├─ FRAUD DETECTION MODEL TRAINING
  ├─ ROC-AUC Score: 0.9723
  └─ ... 
```

### Best Practices

1. Start with `ACCOUNTADMIN` for initial setup, then create dedicated roles
2. Monitor compute pool resources during deployment
3. Review Cortex Code's explanations when it makes corrections

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built a complete fraud detection system with real-time inference capabilities, all using natural language prompts. You went from raw idea to production-grade REST API running on Snowpark Container Services.

### What You Learned
- Generate realistic synthetic fraud data with natural language prompts
- Perform comprehensive exploratory data analysis in Snowflake notebooks
- Train an XGBoost model optimized for imbalanced fraud detection
- Deploy models to SPCS with automatic containerization
- Create and test REST API endpoints for real-time inference

### Related Resources

Articles:
- [Snowflake ML Overview](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview) - Complete guide to machine learning in Snowflake
- [SPCS Overview](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview) - Container services for model deployment
- [Cortex Code CLI Guide](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) - Natural language coding interface

Documentation:
- [Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [XGBoost in Snowflake ML](https://docs.snowflake.com/en/developer-guide/snowflake-ml/modeling)

Additional Reading:
- [Snowflake Quickstarts](https://quickstarts.snowflake.com/) - More hands-on tutorials
- [Snowflake Community](https://community.snowflake.com/) - Connect with other developers

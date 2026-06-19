author: Qinyi Ding
id: optimized-batch-ml-inference-with-snowpark
summary: Build an end-to-end optimized batch ML inference pipeline in Snowflake, ingesting from Postgres with the Snowpark DB-API, engineering features with vectorized UDFs, and scoring with the Snowflake Model Registry using pre-fork model initialization.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/model-development
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Snowpark, Machine Learning, Model Registry, Postgres, Data Engineering


# Optimized Batch ML Inference with Snowpark
<!-- ------------------------ -->
## Overview

In this quickstart you will build an end-to-end **optimized batch ML inference** pipeline that ingests transactional data from an external Postgres database, engineers features in Snowflake, and scores every row with an XGBoost model registered in the **Snowflake Model Registry**. The pipeline is designed for the throughput and memory profile of production batch inference: parallel ingestion, vectorized feature engineering, and **pre-fork model initialization** that loads large models once and shares them across worker processes via copy-on-write memory.

The scenario: a financial services company runs its transaction processing system on Postgres. Their data science team publishes approved model packages to an internal artifact repository. We need to ingest 50,000 card transactions, engineer features, and produce a fraud probability for every transaction.

You will exercise four Snowpark capabilities together:

| Step | Feature | What it does |
|------|---------|------------|
| Ingest | **Snowpark DB-API** | Pull data from external databases (Postgres, MySQL, SQL Server) using Python's standard DB-API 2.0 drivers, with parallel partitioned reads. |
| Transform | **Vectorized UDFs** | Process millions of rows with pandas-level performance instead of row-by-row scalar UDFs. |
| Score | **Optimized Batch Inference** | Load an ML model once in the head worker and share it across all forked workers via copy-on-write memory. |
| Ecosystem | **Customer-Hosted Artifact Repository** | Pull UDF dependencies from your own Nexus, Artifactory, or other PyPI-compatible repository. |

### Prerequisites
- Familiarity with Python, SQL, and basic ML concepts
- An understanding of how Snowpark UDFs and stored procedures work

### What You'll Learn
- How to ingest data from Postgres into Snowflake with `session.read.dbapi()`
- How to write vectorized UDFs that operate on pandas Series for batch performance
- How to register an XGBoost model with the Snowflake Model Registry
- How to run optimized batch inference using pre-fork model initialization
- How to source Python packages from a customer-hosted artifact repository

### What You'll Need
- A Snowflake account with `ACCOUNTADMIN` (or equivalent) for one-time setup
- An external Postgres database reachable from Snowflake (an RDS instance is fine)
- *Optional:* A customer-hosted PyPI repository (Nexus, Artifactory, or similar). If you don't have one, you can use Snowflake's shared PyPI proxy instead.
- Privileges to create `SECRET`, `NETWORK RULE`, `EXTERNAL ACCESS INTEGRATION`, `API INTEGRATION`, and `ARTIFACT REPOSITORY` objects

### What You'll Build
- An end-to-end batch inference pipeline:
  - `RAW_TRANSACTIONS` ingested from Postgres
  - `TXN_FEATURES` engineered via vectorized UDFs and joined with customer profiles
  - A registered `fraud_scorer` model in the Snowflake Model Registry
  - `FRAUD_SCORES` containing a fraud probability for every transaction

<!-- ------------------------ -->
## Architecture

```
                    Postgres                                Snowflake
               +---------------+                    +---------------------------+
               |  payments.    |   DB-API           |  RAW_TRANSACTIONS         |
               | transactions  | -----------------> |  50K rows ingested        |
               |  (50K rows)   | Parallel Reads     |  via session.read.dbapi   |
               +---------------+                    |         |                 |
                                                    |         v                 |
                                                    |  Vectorized UDF           |
                                                    |  feature engineering      |
                                                    |         |                 |
                                                    |         v                 |
                                                    |  TXN_FEATURES             |
                                                    |  + CUSTOMER_PROFILES      |
                                                    |         |                 |
               +---------------+                    |         v                 |
               |   Nexus       |   Artifact Repo    |  Model Registry           |
               |  packages     | -----------------> |  fraud_scorer registered  |
               |  (PyPI)       |   Python Packages  |  pre-fork init enabled    |
               +---------------+                    |         |                 |
                                                    |         v                 |
                                                    |  FRAUD_SCORES             |
                                                    |  every txn scored 0-1     |
                                                    +---------------------------+
```

<!-- ------------------------ -->
## Set Up the Postgres Source

You can use any Postgres instance reachable from the public internet (RDS works well). The pipeline expects a `payments.transactions` table with 50,000 rows.

In your Postgres instance, run the seed script (see [scripts/postgres_seed.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/optimized-batch-ml-inference-with-snowpark/scripts/postgres_seed.sql) in this quickstart's repo):

```sql
CREATE SCHEMA IF NOT EXISTS payments;

CREATE TABLE payments.transactions (
    txn_id              BIGINT PRIMARY KEY,
    customer_id         INTEGER NOT NULL,
    txn_amount          NUMERIC(12, 2) NOT NULL,
    txn_timestamp       TIMESTAMP NOT NULL,
    merchant_category   TEXT NOT NULL,
    merchant_country    TEXT NOT NULL,
    is_online           BOOLEAN NOT NULL
);

-- Generate 50,000 synthetic transactions
INSERT INTO payments.transactions
SELECT
    i AS txn_id,
    1 + floor(random() * 500)::INT AS customer_id,
    round((random() * 2000 + 5)::numeric, 2) AS txn_amount,
    NOW() - (random() * interval '90 days') AS txn_timestamp,
    (ARRAY['travel','online_retail','electronics','restaurant','gas','grocery'])[1 + floor(random() * 6)] AS merchant_category,
    (ARRAY['US','CA','GB','FR','DE','JP'])[1 + floor(random() * 6)] AS merchant_country,
    random() < 0.4 AS is_online
FROM generate_series(1, 50000) AS i;

CREATE INDEX idx_txn_customer ON payments.transactions(customer_id);
CREATE INDEX idx_txn_timestamp ON payments.transactions(txn_timestamp);
```

Make a note of the Postgres host, port, database, username, and password — you will need them in the next step.

<!-- ------------------------ -->
## Configure External Access for Postgres

Snowflake reaches external endpoints through an **External Access Integration**. We will create three objects: a `SECRET` (credentials), a `NETWORK RULE` (egress allowlist), and an `EXTERNAL ACCESS INTEGRATION` that combines them.

Run this in a Snowflake worksheet:

```sql
USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS BATCH_INF_DEMO;
CREATE SCHEMA IF NOT EXISTS BATCH_INF_DEMO.PUBLIC;
USE SCHEMA BATCH_INF_DEMO.PUBLIC;
CREATE WAREHOUSE IF NOT EXISTS BATCH_INF_WH WITH WAREHOUSE_SIZE = 'MEDIUM';

-- Replace with your Postgres credentials
CREATE OR REPLACE SECRET pg_secret
    TYPE = PASSWORD
    USERNAME = 'postgres'
    PASSWORD = '<your-postgres-password>';

-- Replace with your Postgres host
CREATE OR REPLACE NETWORK RULE pg_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('<your-postgres-host>:5432');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pg_access_integration
    ALLOWED_NETWORK_RULES = (pg_network_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (pg_secret)
    ENABLED = TRUE;
```

<!-- ------------------------ -->
## Configure the Artifact Repository

Snowflake UDFs and stored procedures can pull Python packages from a customer-hosted PyPI-compatible repository (Nexus, Artifactory, etc.). This gives you the same package governance as your other Python codebases and lets you serve internal/proprietary wheels.

> aside negative
>
> **No Nexus?** You can skip this step and substitute `'snowflake.snowpark.pypi_shared_repository'` everywhere this quickstart references `'my_nexus_repo'`. That uses Snowflake's shared PyPI proxy and works for the public packages we use here (`psycopg2-binary`, `pandas`, `numpy`, `xgboost`).

```sql
CREATE OR REPLACE SECRET nexus_secret
    TYPE = PASSWORD
    USERNAME = '<your-nexus-username>'
    PASSWORD = '<your-nexus-password>';

CREATE OR REPLACE API INTEGRATION nexus_api_integration
    API_PROVIDER = ARTIFACT_REPOSITORY_API
    API_ALLOWED_PREFIXES = ('<your-nexus-host-prefix>')
    ALLOWED_AUTHENTICATION_SECRETS = (nexus_secret)
    ENABLED = TRUE;

CREATE OR REPLACE ARTIFACT REPOSITORY my_nexus_repo
    TYPE = PYPI
    API_INTEGRATION = nexus_api_integration
    INDEX_URL = '<your-nexus-pypi-index-url>'
    AUTHENTICATION_SECRET = nexus_secret
    COMMENT = 'Internal Nexus PyPI repository for ML model packages';
```

<!-- ------------------------ -->
## Load Customer Profiles into Snowflake

We need a `CUSTOMER_PROFILES` table in Snowflake to join against the transaction features. Run [scripts/customer_profiles.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/optimized-batch-ml-inference-with-snowpark/scripts/customer_profiles.sql) or paste this:

```sql
USE SCHEMA BATCH_INF_DEMO.PUBLIC;

CREATE OR REPLACE TABLE CUSTOMER_PROFILES (
    customer_id     INT,
    home_country    STRING,
    credit_limit    NUMBER(10, 2),
    risk_tier       STRING
);

INSERT INTO CUSTOMER_PROFILES
SELECT
    SEQ4() + 1 AS customer_id,
    CASE MOD(SEQ4(), 6)
        WHEN 0 THEN 'US' WHEN 1 THEN 'CA' WHEN 2 THEN 'GB'
        WHEN 3 THEN 'FR' WHEN 4 THEN 'DE' ELSE 'JP'
    END AS home_country,
    ROUND(UNIFORM(2000, 25000, RANDOM(42)), 2) AS credit_limit,
    CASE MOD(SEQ4(), 3)
        WHEN 0 THEN 'LOW' WHEN 1 THEN 'MEDIUM' ELSE 'HIGH'
    END AS risk_tier
FROM TABLE(GENERATOR(ROWCOUNT => 500));
```

<!-- ------------------------ -->
## Step 1: Ingest from Postgres with Snowpark DB-API

The new `session.read.dbapi()` API lets you pull data from any external database that ships a Python DB-API 2.0 driver. No Spark, no custom connectors — just `pip install psycopg2-binary` and define a connection factory.

Open a Snowflake notebook (or any Snowpark Python session) and run:

```python
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import sproc
from snowflake.snowpark import Session

session = get_active_session()
session.sql("USE DATABASE BATCH_INF_DEMO").collect()
session.sql("USE SCHEMA PUBLIC").collect()
session.sql("USE WAREHOUSE BATCH_INF_WH").collect()
session.sql("CREATE STAGE IF NOT EXISTS udf_stage").collect()


@sproc(
    name='BATCH_INF_DEMO.PUBLIC.ingest_from_postgres',
    is_permanent=True,
    stage_location='@BATCH_INF_DEMO.PUBLIC.udf_stage',
    replace=True,
    artifact_repository='my_nexus_repo',  # or 'snowflake.snowpark.pypi_shared_repository'
    packages=['snowflake-snowpark-python', 'psycopg2-binary'],
    external_access_integrations=['pg_access_integration'],
    secrets={'cred': 'pg_secret'},
)
def ingest_from_postgres(session: Session) -> str:
    import _snowflake
    creds = _snowflake.get_username_password('cred')

    def create_pg_connection():
        import psycopg2
        return psycopg2.connect(
            host='<your-postgres-host>',
            port=5432,
            dbname='postgres',
            user=creds.username,
            password=creds.password,
            application_name='snowflake-snowpark-python',
        )

    udtf_configs = {
        'external_access_integration': 'pg_access_integration',
        'secret': 'pg_secret',
    }

    df = session.read.dbapi(
        create_pg_connection,
        table='payments.transactions',
        udtf_configs=udtf_configs,
        column='txn_id',
        lower_bound=1,
        upper_bound=50000,
        num_partitions=4,
        fetch_size=10000,
    )

    df.write.save_as_table('BATCH_INF_DEMO.PUBLIC.RAW_TRANSACTIONS', mode='overwrite')
    return f"Ingested {session.table('BATCH_INF_DEMO.PUBLIC.RAW_TRANSACTIONS').count()} transactions"


print(session.call('BATCH_INF_DEMO.PUBLIC.ingest_from_postgres'))
session.table('BATCH_INF_DEMO.PUBLIC.RAW_TRANSACTIONS').show(10)
```

What's happening:

- **`column`, `lower_bound`, `upper_bound`, `num_partitions`** split the read into four parallel partitions on `txn_id`. Each partition runs in its own UDTF instance.
- **`fetch_size=10000`** overlaps reading from Postgres with writing to Snowflake.
- **`udtf_configs`** runs the ingestion entirely on Snowflake compute — no driver round-trips.
- **`artifact_repository='my_nexus_repo'`** sources `psycopg2-binary` from your internal repository.

<!-- ------------------------ -->
## Step 2: Engineer Features with a Vectorized UDF

Scalar UDFs process one row at a time. **Vectorized UDFs** receive batches of rows as pandas Series, enabling columnar numpy/pandas operations that run dramatically faster on numerical workloads.

We will compute four engineered features:

| Feature | Description | Why it matters for fraud |
|---------|-------------|-------------------------|
| `amt_zscore` | Z-score normalized transaction amount | Unusually large transactions are suspicious |
| `hour_sin`, `hour_cos` | Cyclical encoding of transaction hour | Fraud peaks at unusual hours |
| `category_risk` | Risk weight by merchant category | Travel and online retail have higher fraud rates |

```python
import numpy as np
import pandas as pd
from snowflake.snowpark.functions import udf
from snowflake.snowpark.types import PandasSeries

CATEGORY_RISK = {
    'travel': 0.8, 'online_retail': 0.6, 'electronics': 0.5,
    'restaurant': 0.2, 'gas': 0.15, 'grocery': 0.1,
}


@udf(
    name='BATCH_INF_DEMO.PUBLIC.compute_txn_features',
    replace=True,
    artifact_repository='my_nexus_repo',
    packages=['pandas', 'numpy', 'cloudpickle'],
)
def compute_txn_features(
    txn_amount: PandasSeries[float],
    txn_hour: PandasSeries[float],
    merchant_category: PandasSeries[str],
) -> PandasSeries[dict]:
    mean_amt, std_amt = txn_amount.mean(), txn_amount.std()
    amt_zscore = ((txn_amount - mean_amt) / std_amt).round(4)
    hour_sin = np.sin(2 * np.pi * txn_hour / 24).round(4)
    hour_cos = np.cos(2 * np.pi * txn_hour / 24).round(4)
    category_risk = merchant_category.map(CATEGORY_RISK).fillna(0.3).round(4)

    results = []
    for i in range(len(txn_amount)):
        results.append({
            'amt_zscore': float(amt_zscore.iloc[i]),
            'hour_sin': float(hour_sin.iloc[i]),
            'hour_cos': float(hour_cos.iloc[i]),
            'category_risk': float(category_risk.iloc[i]),
        })
    return pd.Series(results)
```

Now apply the UDF and join with `CUSTOMER_PROFILES`:

```python
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import FloatType

raw = session.table('BATCH_INF_DEMO.PUBLIC.RAW_TRANSACTIONS')

raw_with_features = raw.with_columns(
    ['TXN_HOUR', 'FEATURES'],
    [
        F.hour(F.col('TXN_TIMESTAMP')),
        F.call_udf(
            'BATCH_INF_DEMO.PUBLIC.compute_txn_features',
            F.col('TXN_AMOUNT').cast(FloatType()),
            F.hour(F.col('TXN_TIMESTAMP')).cast(FloatType()),
            F.col('MERCHANT_CATEGORY'),
        ),
    ],
)

customers = session.table('BATCH_INF_DEMO.PUBLIC.CUSTOMER_PROFILES')

joined = raw_with_features.join(
    customers,
    raw_with_features['CUSTOMER_ID'] == customers['CUSTOMER_ID'],
    'left',
).drop(customers['CUSTOMER_ID'])

txn_features = joined.select(
    raw_with_features['TXN_ID'],
    raw_with_features['CUSTOMER_ID'].alias('CUSTOMER_ID'),
    raw_with_features['TXN_AMOUNT'],
    raw_with_features['TXN_TIMESTAMP'],
    raw_with_features['MERCHANT_CATEGORY'],
    raw_with_features['IS_ONLINE'],
    raw_with_features['MERCHANT_COUNTRY'],
    F.col('FEATURES')['amt_zscore'].cast(FloatType()).alias('AMT_ZSCORE'),
    F.col('FEATURES')['hour_sin'].cast(FloatType()).alias('HOUR_SIN'),
    F.col('FEATURES')['hour_cos'].cast(FloatType()).alias('HOUR_COS'),
    F.col('FEATURES')['category_risk'].cast(FloatType()).alias('CATEGORY_RISK'),
    F.iff(raw_with_features['IS_ONLINE'], F.lit(1.0), F.lit(0.0)).alias('IS_ONLINE_FLAG'),
    F.iff(
        raw_with_features['MERCHANT_COUNTRY'] != customers['HOME_COUNTRY'],
        F.lit(1.0), F.lit(0.0),
    ).alias('IS_INTERNATIONAL'),
    (raw_with_features['TXN_AMOUNT'] / F.nullifzero(customers['CREDIT_LIMIT'])).alias('AMT_TO_LIMIT_RATIO'),
    customers['CREDIT_LIMIT'].alias('CREDIT_LIMIT'),
    customers['RISK_TIER'].alias('RISK_TIER'),
)

txn_features.write.save_as_table('BATCH_INF_DEMO.PUBLIC.TXN_FEATURES', mode='overwrite')
print(f"Feature table: {session.table('BATCH_INF_DEMO.PUBLIC.TXN_FEATURES').count()} rows")
```

<!-- ------------------------ -->
## Step 3: Train and Register a Model with Pre-Fork Initialization

Train a small XGBoost fraud model and register it to the Snowflake Model Registry. The Model Registry handles **pre-fork model initialization** automatically when you query the model — the model file is loaded once in the head worker process and shared across all forked workers via copy-on-write memory.

Without this optimization: parallelism of 8 with a 2 GB model = 16 GB of memory.
With this optimization: parallelism of 8 with a 2 GB model = 2 GB of memory.

```python
import logging
logging.getLogger('snowflake.ml').setLevel(logging.ERROR)

import numpy as np
import xgboost as xgb
import pandas as pd
from snowflake.ml.registry import Registry

# Synthetic training data
rng = np.random.RandomState(42)
X = rng.rand(5000, 8).astype(np.float32)
logit = (
    0.8 * X[:, 0] + 0.3 * X[:, 1] - 0.5 * X[:, 3] + 0.6 * X[:, 4]
    + 0.9 * X[:, 5] + 0.7 * X[:, 6] + 1.2 * X[:, 7]
    + rng.normal(0, 0.5, 5000)
)
y = (logit > np.percentile(logit, 90)).astype(int)
dtrain = xgb.DMatrix(X, label=y)
model = xgb.train(
    {'objective': 'binary:logistic', 'max_depth': 4, 'eta': 0.2, 'seed': 42},
    dtrain,
    num_boost_round=50,
)

# Register
reg = Registry(session=session, database_name='BATCH_INF_DEMO', schema_name='PUBLIC')
try:
    reg.delete_model('fraud_scorer')
except Exception:
    pass

mv = reg.log_model(
    model,
    model_name='fraud_scorer',
    version_name='v1',
    sample_input_data=pd.DataFrame(
        X[:5],
        columns=[
            'AMT_ZSCORE', 'TXN_VELOCITY', 'HOUR_SIN', 'HOUR_COS',
            'IS_ONLINE_FLAG', 'IS_INTERNATIONAL', 'CATEGORY_RISK', 'AMT_TO_LIMIT_RATIO',
        ],
    ),
    target_platforms=['WAREHOUSE'],
)
print(f"Registered: {mv.model_name} {mv.version_name}")
```

<!-- ------------------------ -->
## Step 4: Score All Transactions

Now apply the registered model against the feature table. Each row gets a fraud probability between 0 and 1.

```python
from snowflake.snowpark import Window, functions as F
from snowflake.snowpark.types import FloatType

features = session.table('BATCH_INF_DEMO.PUBLIC.TXN_FEATURES')

# 24-hour rolling transaction count per customer
window_spec = (
    Window.partition_by('CUSTOMER_ID')
    .order_by(F.builtin('DATE_PART')('epoch_second', F.col('TXN_TIMESTAMP')))
    .range_between(-86400, Window.CURRENT_ROW)
)

features_with_velocity = features.with_column(
    'TXN_VELOCITY',
    F.count('*').over(window_spec).cast(FloatType()),
)

scoring_input = features_with_velocity.select(
    F.col('TXN_ID'),
    F.col('CUSTOMER_ID'),
    F.col('TXN_AMOUNT'),
    F.col('TXN_TIMESTAMP'),
    F.col('MERCHANT_CATEGORY'),
    F.col('RISK_TIER'),
    F.col('AMT_ZSCORE'),
    F.col('TXN_VELOCITY'),
    F.col('HOUR_SIN'),
    F.col('HOUR_COS'),
    F.col('IS_ONLINE_FLAG'),
    F.col('IS_INTERNATIONAL'),
    F.col('CATEGORY_RISK'),
    F.coalesce(F.col('AMT_TO_LIMIT_RATIO'), F.lit(0.5)).alias('AMT_TO_LIMIT_RATIO'),
)

mv = reg.get_model('fraud_scorer').version('v1')
fraud_scores = mv.run(scoring_input, function_name='predict')

result = fraud_scores.select(
    F.col('TXN_ID'),
    F.col('CUSTOMER_ID'),
    F.col('TXN_AMOUNT'),
    F.col('TXN_TIMESTAMP'),
    F.col('MERCHANT_CATEGORY'),
    F.col('RISK_TIER'),
    F.col('"output_feature_0"').alias('FRAUD_PROBABILITY'),
)

result.write.save_as_table('BATCH_INF_DEMO.PUBLIC.FRAUD_SCORES', mode='overwrite')
print(f"Scored {session.table('BATCH_INF_DEMO.PUBLIC.FRAUD_SCORES').count()} transactions")
```

<!-- ------------------------ -->
## Analyze the Results

Pull the top 20 highest-risk transactions:

```python
from snowflake.snowpark import functions as F

session.table('BATCH_INF_DEMO.PUBLIC.FRAUD_SCORES').select(
    F.col('TXN_ID'),
    F.col('CUSTOMER_ID'),
    F.col('TXN_AMOUNT'),
    F.col('TXN_TIMESTAMP'),
    F.col('MERCHANT_CATEGORY'),
    F.round(F.col('FRAUD_PROBABILITY'), 4).alias('FRAUD_SCORE'),
).sort(F.col('FRAUD_PROBABILITY').desc()).show(20)
```

You can also query in SQL:

```sql
SELECT
    TXN_ID, CUSTOMER_ID, TXN_AMOUNT, MERCHANT_CATEGORY,
    ROUND(FRAUD_PROBABILITY, 4) AS FRAUD_SCORE
FROM BATCH_INF_DEMO.PUBLIC.FRAUD_SCORES
WHERE FRAUD_PROBABILITY > 0.5
ORDER BY FRAUD_PROBABILITY DESC
LIMIT 50;
```

<!-- ------------------------ -->
## Cleanup

```sql
USE ROLE ACCOUNTADMIN;
DROP TABLE IF EXISTS BATCH_INF_DEMO.PUBLIC.RAW_TRANSACTIONS;
DROP TABLE IF EXISTS BATCH_INF_DEMO.PUBLIC.TXN_FEATURES;
DROP TABLE IF EXISTS BATCH_INF_DEMO.PUBLIC.FRAUD_SCORES;
DROP TABLE IF EXISTS BATCH_INF_DEMO.PUBLIC.CUSTOMER_PROFILES;
DROP FUNCTION IF EXISTS BATCH_INF_DEMO.PUBLIC.compute_txn_features(FLOAT, FLOAT, VARCHAR);
DROP PROCEDURE IF EXISTS BATCH_INF_DEMO.PUBLIC.ingest_from_postgres();
DROP ARTIFACT REPOSITORY IF EXISTS my_nexus_repo;
DROP API INTEGRATION IF EXISTS nexus_api_integration;
DROP EXTERNAL ACCESS INTEGRATION IF EXISTS pg_access_integration;
DROP SECRET IF EXISTS pg_secret;
DROP SECRET IF EXISTS nexus_secret;
DROP NETWORK RULE IF EXISTS pg_network_rule;
DROP DATABASE IF EXISTS BATCH_INF_DEMO;
```

<!-- ------------------------ -->
## Conclusion And Resources

You built an end-to-end optimized batch ML inference pipeline that combines four Snowpark capabilities:

| Feature | Demonstrated by |
|---------|-----------------|
| Snowpark DB-API | Parallel partitioned ingestion from Postgres into `RAW_TRANSACTIONS` |
| Vectorized UDFs | `compute_txn_features` running pandas-batch operations on millions of rows |
| Optimized batch inference | Pre-fork model initialization in the Model Registry's `mv.run()` |
| Customer-hosted artifact repository | UDFs and stored procedures sourcing dependencies from internal Nexus |

### What You Learned
- How to ingest from external databases with `session.read.dbapi()` and partitioned reads
- How to write vectorized UDFs that operate on pandas Series for batch performance
- How to register and serve XGBoost models with the Snowflake Model Registry
- How optimized batch inference reduces memory pressure for large models
- How to source Python packages from a customer-hosted PyPI repository

### Related Resources
- [Snowpark DB-API documentation](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes#reading-data-from-external-databases-using-dbapi)
- [Vectorized Python UDFs](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-batch)
- [Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [External Access Integrations](https://docs.snowflake.com/en/developer-guide/external-network-access/external-network-access-overview)
- [Artifact repositories for UDFs and procedures](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages)

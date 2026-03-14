author: Aritra Bannerjee
id: guide-ml-model-development-deployment-snowflake
summary: Build and deploy an end-to-end ML pipeline using Snowflake Feature Store, Model Registry, SPCS real-time inference, Cortex Search, and a Streamlit dashboard — all on a single platform.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/snowflake-feature/streamlit
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
language: en
authors: Aritra Bannerjee

# ML Model Development and Deployment on Snowflake
<!-- ------------------------ -->
## Overview
Duration: 5

This guide walks through building and deploying a production-grade ML pipeline entirely within Snowflake. You will use a creator commerce scenario — matching brands with content creators — to exercise every major ML capability on the platform.

The pipeline covers:
- **Dynamic Tables** for automated feature computation from behavioral events
- **Feature Store** for governed, reusable feature engineering with online serving
- **Model Registry** for versioned model management with RBAC and lineage
- **Snowpark Container Services (SPCS)** for real-time model inference via REST API
- **Cortex Search** for hybrid semantic search over creator content
- **Streamlit in Snowflake** for an interactive dashboard

By the end, you will have a working system that takes a brand campaign brief and returns ranked creators with match scores in under 100ms — with zero data movement outside Snowflake.

### Prerequisites
- A Snowflake account with **Enterprise Edition** or higher
- A role with privileges to create databases, schemas, warehouses, compute pools, and models (ACCOUNTADMIN works, or a custom role with equivalent grants)
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) (`snow`) or [SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql) installed
- Python 3.9+ installed locally (for the data generation script)
- Familiarity with Python, SQL, and basic ML concepts

### What You Will Learn
- How to use Dynamic Tables for incremental feature computation
- How to register entities and feature views in Snowflake Feature Store
- How to train and log an XGBoost model to the Snowflake Model Registry
- How to deploy a model to SPCS with scale-to-zero for cost-optimized real-time inference
- How to build a Cortex Search service for hybrid semantic search
- How to create tiered creator profiles using batch inference
- How to wire everything together in a Streamlit dashboard

### What You Will Need
- A [Snowflake account](https://signup.snowflake.com/) (Enterprise Edition or higher)
- A local terminal with Python 3.9+ and the `snowflake-ml-python` package
- The demo files from this guide's `assets/` folder

### What You Will Build
- A complete ML pipeline: from raw behavioral data to real-time creator-brand match scoring, semantic search, and an interactive dashboard — all running natively on Snowflake.

<!-- ------------------------ -->
## Setup Environment
Duration: 10

### Create the Snowflake Infrastructure

Download `00_setup.sql` from this guide's `assets/` folder. This script creates:

| Object | Purpose |
|--------|---------|
| `CC_DEMO` database | Houses all demo schemas |
| `RAW` schema | Source data tables |
| `ML` schema | ML artifacts and Dynamic Tables |
| `ML_REGISTRY` schema | Model Registry objects |
| `FEATURE_STORE` schema | Feature Store entities and views |
| `APPS` schema | Streamlit dashboard |
| `CC_ML_WH` warehouse | Compute for ML workloads |
| `CC_COMPUTE_POOL` compute pool | SPCS model serving |

Run the setup script:

```sql
-- Execute via SnowSQL, Snowflake CLI, or paste into a Snowsight worksheet
-- File: assets/00_setup.sql

CREATE DATABASE IF NOT EXISTS CC_DEMO;

CREATE SCHEMA IF NOT EXISTS CC_DEMO.RAW;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.ML;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.ML_REGISTRY;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.FEATURE_STORE;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.APPS;

CREATE WAREHOUSE IF NOT EXISTS CC_ML_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

CREATE COMPUTE POOL IF NOT EXISTS CC_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_SUSPEND_SECS = 300;
```

The full `00_setup.sql` also creates the raw data tables and a Dynamic Table for feature computation. Run the complete file to set up everything at once.

### Generate Synthetic Data

Download `generate_synthetic_data.py` from `assets/` and run it locally:

```bash
pip install snowflake-ml-python snowflake-connector-python pandas numpy

# Set your connection (must have write access to CC_DEMO.RAW)
export SNOWFLAKE_CONNECTION_NAME=<your_connection>

python generate_synthetic_data.py
```

This creates:
| Table | Rows | Description |
|-------|------|-------------|
| `CREATORS` | 10,000 | Creator profiles with engagement metrics |
| `BRANDS` | 1,000 | Brands across 8 categories |
| `BEHAVIORAL_EVENTS` | 500,000 | Views, clicks, and purchases |
| `CREATOR_BRAND_INTERACTIONS` | 100,000 | Conversion records for training |
| `CREATOR_CONTENT` | 200 | Text samples for Cortex Search |

### Upload the Demo Notebook

Download `snowflake_ml_demo.py` from `assets/` and upload it to Snowsight:

1. Navigate to **Snowsight → Projects → Notebooks**
2. Click **Import .ipynb or .py file** and select `snowflake_ml_demo.py`
3. Set the database to `CC_DEMO` and warehouse to `CC_ML_WH`
4. Add the required packages: `snowflake-ml-python`, `xgboost`, `scikit-learn`, `sentence-transformers`

The notebook uses `get_active_session()` so it runs directly in Snowsight with no connection configuration needed.

<!-- ------------------------ -->
## Dynamic Tables for Feature Engineering
Duration: 5

### The Problem
Behavioral events arrive continuously. Computing rolling aggregates (7-day engagement, purchase counts, GMV) traditionally requires streaming pipelines and a separate feature store.

### The Snowflake Approach
A **Dynamic Table** handles incremental refresh automatically. The setup script already created `CREATOR_ENGAGEMENT_FEATURES` with a 2-minute target lag:

```sql
-- Already created by 00_setup.sql
CREATE OR REPLACE DYNAMIC TABLE CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES
    TARGET_LAG = '2 minutes'
    WAREHOUSE = CC_ML_WH
AS
SELECT
    CREATOR_ID,
    COUNT(DISTINCT SESSION_ID)    AS SESSIONS_7D,
    AVG(CLICK_THROUGH_RATE)       AS AVG_CTR_7D,
    SUM(CASE WHEN EVENT_TYPE = 'purchase' THEN 1 ELSE 0 END) AS PURCHASES_7D,
    SUM(GMV)                      AS GMV_7D,
    COUNT(DISTINCT BRAND_ID)      AS UNIQUE_BRANDS_7D,
    AVG(ENGAGEMENT_SCORE)         AS AVG_ENGAGEMENT_7D,
    CURRENT_TIMESTAMP()           AS FEATURE_TIMESTAMP
FROM CC_DEMO.RAW.BEHAVIORAL_EVENTS
WHERE EVENT_DATE >= DATEADD('day', -7, CURRENT_DATE())
GROUP BY CREATOR_ID;
```

### Verify in the Notebook

Run the Dynamic Table inspection cell in the notebook. You should see:
- **Refresh mode**: `INCREMENTAL` (Snowflake auto-selects the optimal mode)
- **Scheduling state**: `ACTIVE`
- **Row count**: ~10,000 (one row per creator)

> **Key insight**: No Spark cluster, no Kafka, no cron jobs. Snowflake manages the pipeline end-to-end.

<!-- ------------------------ -->
## Feature Store — Register, Discover, Govern
Duration: 10

### Create Entities and Feature Views

The Feature Store is a schema where entities and feature views are first-class Snowflake objects with RBAC and lineage. Run the Feature Store cells in the notebook:

```python
from snowflake.ml.feature_store import FeatureStore, FeatureView, Entity, CreationMode

fs = FeatureStore(
    session=session,
    database="CC_DEMO",
    name="FEATURE_STORE",
    default_warehouse="CC_ML_WH",
    creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
)

# Register the CREATOR entity
creator_entity = Entity(
    name="CREATOR",
    join_keys=["CREATOR_ID"],
    desc="Creator — lifestyle influencer on the platform",
)
fs.register_entity(creator_entity)

# Create an engagement feature view backed by the Dynamic Table
engagement_fv = FeatureView(
    name="CREATOR_ENGAGEMENT",
    entities=[creator_entity],
    feature_df=session.table("CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES"),
    desc="Rolling 7-day engagement features from behavioral events",
)
engagement_fv = fs.register_feature_view(
    feature_view=engagement_fv,
    version="V1",
    refresh_freq="2 minutes",
    block=True,
)
```

### Online Serving

The notebook also registers a **Creator Profile** feature view with online serving enabled. This allows sub-30ms feature retrieval for real-time inference:

```python
profile_fv = FeatureView(
    name="CREATOR_PROFILE",
    entities=[creator_entity],
    feature_df=session.table("CC_DEMO.RAW.CREATORS").select(
        "CREATOR_ID", "CATEGORY", "FOLLOWER_COUNT", "AVG_ENGAGEMENT", "COUNTRY"
    ),
    desc="Static creator profile attributes",
)
profile_fv = fs.register_feature_view(
    feature_view=profile_fv, version="V1", block=True,
)
```

### What You Should See
- Two feature views registered in `CC_DEMO.FEATURE_STORE`
- The engagement feature view backed by a Dynamic Table (auto-refreshing)
- The profile feature view backed by a static table

<!-- ------------------------ -->
## Train and Register an ML Model
Duration: 15

### Generate a Training Dataset

The Feature Store generates a point-in-time-correct training dataset by joining features with labels:

```python
from snowflake.ml.feature_store import FeatureStore

fs = FeatureStore(session=session, database="CC_DEMO", name="FEATURE_STORE",
                  default_warehouse="CC_ML_WH")

# Spine: labeled data with CREATOR_ID as the join key
spine_df = session.table("CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS").select(
    "CREATOR_ID", "CONVERTED"
)

# Generate dataset with all registered features
training_dataset = fs.generate_dataset(
    name="MATCH_TRAINING_DATA",
    spine_df=spine_df,
    features=[engagement_fv, profile_fv],
    output_type="dataset",
)
```

### Train XGBoost

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

pdf = training_dataset.read.to_pandas()
feature_cols = ["SESSIONS_7D", "AVG_CTR_7D", "PURCHASES_7D", "GMV_7D",
                "UNIQUE_BRANDS_7D", "AVG_ENGAGEMENT_7D", "FOLLOWER_COUNT",
                "AVG_ENGAGEMENT", "CATEGORY_ENCODED", "COUNTRY_ENCODED"]

X_train, X_test, y_train, y_test = train_test_split(
    pdf[feature_cols], pdf["CONVERTED"].astype(int), test_size=0.2, random_state=42
)

model = xgb.XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.1,
    eval_metric="auc", random_state=42,
)
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
print(f"Test AUC: {auc:.4f}")
```

**Expected result**: AUC ~0.70 or higher. This confirms the engagement and profile features have strong predictive signal for creator-brand match quality.

### Log to Model Registry

```python
from snowflake.ml.registry import Registry

reg = Registry(session=session, database_name="CC_DEMO", schema_name="ML_REGISTRY")
mv = reg.log_model(
    model_name="CREATOR_BRAND_MATCH",
    version_name="V1",
    model=model,
    conda_dependencies=["xgboost"],
    sample_input_data=X_train.head(10),
    comment=f"XGBoost creator-brand match | AUC={auc:.4f}",
)
```

### Version Management and RBAC

The notebook demonstrates production model management:

```python
# Set the PRODUCTION alias
m = reg.get_model("CREATOR_BRAND_MATCH")
m.default = mv  # Sets V1 as the default (PRODUCTION) version

# Grant inference access to a role
mv.grant_access(role="DATA_SCIENTIST", privilege="USAGE")
```

### ML Lineage

After logging, Snowflake automatically tracks lineage from source tables through feature views to the registered model:

```sql
-- View model lineage
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE QUERY_TEXT ILIKE '%CREATOR_BRAND_MATCH%'
ORDER BY QUERY_START_TIME DESC LIMIT 5;
```

<!-- ------------------------ -->
## Deploy Real-Time Inference with SPCS
Duration: 10

### Deploy the Model as a Service

Snowpark Container Services (SPCS) deploys the model as a containerized REST endpoint with scale-to-zero:

```python
mv = reg.get_model("CREATOR_BRAND_MATCH").version("V1")
mv.create_service(
    service_name="CC_MATCH_SERVICE",
    service_compute_pool="CC_COMPUTE_POOL",
    ingress_enabled=True,
    min_instances=0,   # Scale to zero when idle ($0 cost)
    max_instances=2,   # Scale up under load
)
```

**Cost behavior**: With `min_instances=0`, the service auto-suspends after ~30 minutes of inactivity. You pay nothing when it is idle.

### Invoke via SQL

Once the service is running, call it directly from SQL:

```sql
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
    0.08, 10, 1500.0, 5, 0.05, 500000, 1, 0.7, 0.6, 3
) AS match_score;
```

### Invoke via REST API

The notebook shows how to call the endpoint via HTTP for integration with external systems:

```python
import requests

url = f"https://{service_url}/predict"
payload = {
    "data": [[0.08, 10, 1500.0, 5, 0.05, 500000, 1, 0.7, 0.6, 3]]
}
headers = {
    "Authorization": f"Snowflake Token=\"{session.connection.rest.token}\"",
    "Content-Type": "application/json",
}
resp = requests.post(url, json=payload, headers=headers)
print(resp.json())
```

### What You Should See
- Service status: `READY` (may take 2-3 minutes on first deploy)
- Match score returned as a float between 0 and 1
- Response time under 100ms for single predictions

<!-- ------------------------ -->
## Cortex Search for Creator Discovery
Duration: 10

### Build a Semantic Search Service

Cortex Search provides hybrid (keyword + vector) search over creator content. The notebook creates a search service with automatic embedding and indexing:

```python
session.sql("""
    CREATE OR REPLACE CORTEX SEARCH SERVICE CC_DEMO.ML.CREATOR_CONTENT_SEARCH
    ON CONTENT_TEXT
    ATTRIBUTES CREATOR_ID, CATEGORY, PLATFORM
    WAREHOUSE = CC_ML_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT CREATOR_ID, CONTENT_TEXT, CATEGORY, PLATFORM
        FROM CC_DEMO.RAW.CREATOR_CONTENT
    )
""").collect()
```

### Query the Search Service

```sql
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'CC_DEMO.ML.CREATOR_CONTENT_SEARCH',
    '{"query": "sustainable fashion influencer",
      "columns": ["CREATOR_ID", "CONTENT_TEXT", "CATEGORY"],
      "limit": 5}'
);
```

This returns ranked results combining semantic similarity with keyword matching — no external search cluster needed.

<!-- ------------------------ -->
## Batch Inference and Creator Profiles
Duration: 10

### Score All Creators

The notebook runs batch inference to score every creator-brand pair and builds tiered profiles:

```python
# Batch predictions using the registered model
predictions_df = mv.run(input_df, function_name="predict_proba")

# Create tiered profiles
session.sql("""
    CREATE OR REPLACE TABLE CC_DEMO.ML.CREATOR_PROFILES AS
    SELECT
        CREATOR_ID,
        AVG(MATCH_SCORE) AS AVG_MATCH_SCORE,
        CASE
            WHEN AVG(MATCH_SCORE) >= 0.6 THEN 'PREMIUM'
            WHEN AVG(MATCH_SCORE) >= 0.2 THEN 'STANDARD'
            ELSE 'EMERGING'
        END AS CREATOR_TIER,
        COUNT(*) AS BRANDS_SCORED
    FROM CC_DEMO.ML.MATCH_PREDICTIONS
    GROUP BY CREATOR_ID
""").collect()
```

### Expected Tier Distribution

| Tier | Expected % | Avg Score |
|------|-----------|-----------|
| PREMIUM | ~11.6% | ~0.80 |
| STANDARD | ~40.7% | ~0.38 |
| EMERGING | ~47.8% | ~0.07 |

### Auto-Refreshing Profiles

A Dynamic Table keeps creator profiles up-to-date as new predictions are generated:

```sql
CREATE OR REPLACE DYNAMIC TABLE CC_DEMO.ML.CREATOR_PROFILES_LIVE
    TARGET_LAG = '5 minutes'
    WAREHOUSE = CC_ML_WH
AS
SELECT * FROM CC_DEMO.ML.CREATOR_PROFILES;
```

### Validate Results

```sql
-- Check tier distribution
SELECT CREATOR_TIER, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
FROM CC_DEMO.ML.CREATOR_PROFILES
GROUP BY 1
ORDER BY pct DESC;
```

<!-- ------------------------ -->
## Streamlit Dashboard
Duration: 5

### Deploy the Dashboard

The `streamlit_app.py` file in `assets/` provides an interactive demo UI. To deploy:

1. In Snowsight, navigate to **Streamlit**
2. Click **+ Streamlit App**
3. Set database to `CC_DEMO`, schema to `APPS`, warehouse to `CC_ML_WH`
4. Paste or upload the contents of `streamlit_app.py`
5. Click **Run**

The dashboard provides:
- **Creator search**: Find creators by keyword using Cortex Search
- **Match scoring**: Score a creator against a brand in real time
- **Tier explorer**: Browse creators by PREMIUM / STANDARD / EMERGING tier
- **Feature visualization**: View engagement metrics from the Feature Store

### Access the Dashboard

After deployment: **Snowsight → Streamlit → CREATOR_MATCH_DEMO**

<!-- ------------------------ -->
## Cleanup
Duration: 2

When you are done exploring, run the teardown script to remove all demo objects:

```sql
-- File: assets/99_teardown.sql
-- Drops ALL demo objects in the correct dependency order

DROP SERVICE IF EXISTS CC_DEMO.ML_REGISTRY.CC_MATCH_SERVICE;
DROP CORTEX SEARCH SERVICE IF EXISTS CC_DEMO.ML.CREATOR_CONTENT_SEARCH;
DROP STREAMLIT IF EXISTS CC_DEMO.APPS.CREATOR_MATCH_DEMO;
DROP MODEL IF EXISTS CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH;
DROP DYNAMIC TABLE IF EXISTS CC_DEMO.ML.CREATOR_PROFILES_LIVE;
DROP DYNAMIC TABLE IF EXISTS CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES;
DROP SCHEMA IF EXISTS CC_DEMO.FEATURE_STORE CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.ML_REGISTRY CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.ML CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.RAW CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.APPS CASCADE;
DROP DATABASE IF EXISTS CC_DEMO;
DROP WAREHOUSE IF EXISTS CC_ML_WH;
DROP COMPUTE POOL IF EXISTS CC_COMPUTE_POOL;
```

The full `99_teardown.sql` file in `assets/` includes status checks after each step.

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 2

### What You Built

An end-to-end ML pipeline on Snowflake that:

1. **Computes features automatically** using Dynamic Tables (no streaming infrastructure)
2. **Governs features** through the Feature Store with entities, versioning, and RBAC
3. **Trains and registers models** with the Model Registry including lineage tracking
4. **Serves predictions in real time** via SPCS with scale-to-zero cost optimization
5. **Searches unstructured content** using Cortex Search (hybrid semantic + keyword)
6. **Presents results** through a Streamlit dashboard

All on a single platform, with zero data movement.

### What You Learned
- How Dynamic Tables replace streaming feature pipelines
- How the Feature Store provides governed, reusable features with online serving
- How the Model Registry manages model versions, aliases, and access control
- How SPCS deploys models as REST endpoints with scale-to-zero
- How Cortex Search enables hybrid semantic search without external infrastructure
- How batch inference creates actionable creator profiles (PREMIUM / STANDARD / EMERGING)

### Related Resources
- [Snowflake Feature Store Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-ml/feature-store/overview)
- [Snowflake Model Registry Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-ml/model-registry/overview)
- [Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Snowflake ML Python API Reference](https://docs.snowflake.com/en/developer-guide/snowpark-ml/index)

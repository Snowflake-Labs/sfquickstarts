author: Abhinav Bannerjee
id: build-an-ai-matching-app-with-snowflake-ml
summary: Build an AI-powered matching application on Snowflake using Dynamic Tables, Feature Store, Model Registry, SPCS, Cortex Search, Model Monitoring, and Streamlit.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/snowflake-feature/streamlit, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/snowflake-ml-functions, snowflake-site:taxonomy/industry/advertising-media-and-entertainment
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Snowflake ML, Model Registry, Feature Store, SPCS, Cortex Search, Dynamic Tables, Streamlit, XGBoost, Machine Learning, Creator Economy, Model Monitoring
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets

# Build an AI Matching App with Snowflake ML
<!-- ------------------------ -->
## Overview

In this guide, you will build an AI-powered matching application entirely on Snowflake. The use case is **creator-brand matching** for a commerce platform, but the architecture pattern applies to any two-sided matching problem: job candidates to roles, patients to providers, products to customers, and more.

You will train an XGBoost classification model using Snowflake ML, deploy it for both batch and real-time inference, add semantic search over unstructured content, and wrap everything in an interactive Streamlit dashboard.

### Prerequisites

- Basic familiarity with SQL and Python
- Understanding of machine learning concepts (classification, training/test split, AUC)

### What You Will Learn

- How to use **Dynamic Tables** for automated feature engineering from behavioral event data
- How to register entities and feature views in the **Snowflake Feature Store** with online serving
- How to train an XGBoost model and log it to the **Snowflake Model Registry** with versioning, aliases, and RBAC
- How to deploy a model as a real-time REST API using **Snowpark Container Services (SPCS)** with scale-to-zero
- How to create a **Cortex Search** service for hybrid semantic search over creator content
- How to build a multi-page **Streamlit in Snowflake** dashboard that ties all components together

### What You Will Need

- A [Snowflake account](https://signup.snowflake.com/?utm_cta=quickstarts_) (Enterprise Edition or higher recommended)
- A role with privileges to create databases, schemas, warehouses, compute pools, and Streamlit apps
- Python 3.9+ with `pip` ([Miniconda](https://docs.conda.io/en/latest/miniconda.html) recommended)
- A SQL client or [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight) for running setup scripts

### What You Will Build

- A Dynamic Table that auto-refreshes engagement features from 500K behavioral events
- A Feature Store with a CREATOR entity and feature views for training and online serving
- An XGBoost match-score model registered in the Model Registry (V1 with auto-endpoints, V2 with custom multi-endpoint)
- A real-time SPCS inference service with a public REST endpoint
- A Cortex Search service over 200 creator content records with filtering by category and platform
- A 6-page Streamlit dashboard: Feature Store explorer, Model Registry viewer, Inference playground, CDP Profiles, Cortex Search, and Model Monitoring

<!-- ------------------------ -->
## Set Up Your Environment

### Download the Source Files

Download the source files from the [assets folder](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets) on GitHub.

Alternatively, use a sparse clone to download only this guide's files (~5 MB):

```bash
git clone --no-checkout --depth 1 --filter=blob:none --sparse \
  https://github.com/Snowflake-Labs/sfquickstarts.git
cd sfquickstarts
git sparse-checkout set site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets
```

### Install Python Dependencies

```bash
pip install snowflake-ml-python>=1.7.0 snowflake-connector-python xgboost scikit-learn pandas numpy sentence-transformers
```

Or use the provided conda environment file:

```bash
conda env create -f notebooks/environment.yml
conda activate creator_brand_match
```

### Run the Setup SQL

Open a SQL worksheet in Snowsight and paste the contents of [00_setup.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets/sql/00_setup.sql). This creates:

- **CC_DEMO** database with 5 schemas: `RAW`, `ML`, `ML_REGISTRY`, `FEATURE_STORE`, `APPS`
- **CC_ML_WH** warehouse (MEDIUM, auto-suspend 120s)
- **CC_COMPUTE_POOL** for SPCS model serving (CPU_X64_XS, max 2 nodes)
- Raw data tables: `CREATORS`, `BRANDS`, `BEHAVIORAL_EVENTS`, `CREATOR_BRAND_INTERACTIONS`, `CREATOR_CONTENT`
- A Dynamic Table `CREATOR_ENGAGEMENT_FEATURES` with 2-minute target lag
- 200 sample content records across 8 categories for Cortex Search

```sql
-- Run the full setup script in Snowsight
-- File: sql/00_setup.sql
```

### Generate Synthetic Data

The data generator creates realistic creator-brand interaction data using archetype-driven distributions. Download [generate_synthetic_data.py](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets/scripts/generate_synthetic_data.py) and run:

```bash
export SNOWFLAKE_CONNECTION_NAME=<your_connection>
python scripts/generate_synthetic_data.py
```

This populates:

| Table | Rows | Description |
|-------|------|-------------|
| CREATORS | 10,000 | Creators across 4 archetypes (Power Performer, Rising Star, Steady Earner, Long Tail) |
| BRANDS | 1,000 | Brands across 8 categories with 4 budget tiers |
| BEHAVIORAL_EVENTS | 500,000 | Click, view, purchase, share, and save events over 7 days |
| CREATOR_BRAND_INTERACTIONS | 100,000 | Campaign interaction records with conversion labels |

<!-- ------------------------ -->
## Build Dynamic Features

### How Dynamic Tables Work

The setup SQL already created a Dynamic Table that auto-computes rolling engagement features from raw behavioral events:

```sql
-- Already created by 00_setup.sql
CREATE OR REPLACE DYNAMIC TABLE CREATOR_ENGAGEMENT_FEATURES
    TARGET_LAG = '2 minutes'
    WAREHOUSE = CC_ML_WH
AS
SELECT
    CREATOR_ID,
    COUNT(DISTINCT SESSION_ID)                                AS SESSIONS_7D,
    AVG(CLICK_THROUGH_RATE)                                   AS AVG_CTR_7D,
    SUM(CASE WHEN EVENT_TYPE = 'purchase' THEN 1 ELSE 0 END) AS PURCHASES_7D,
    SUM(GMV)                                                  AS GMV_7D,
    COUNT(DISTINCT BRAND_ID)                                  AS UNIQUE_BRANDS_7D,
    AVG(ENGAGEMENT_SCORE)                                     AS AVG_ENGAGEMENT_7D,
    CURRENT_TIMESTAMP()                                       AS FEATURE_TIMESTAMP
FROM CC_DEMO.RAW.BEHAVIORAL_EVENTS
WHERE EVENT_DATE >= DATEADD('day', -7, CURRENT_DATE())
GROUP BY CREATOR_ID;
```

### Verify the Dynamic Table

Upload `notebooks/creator_brand_match.py` to Snowsight as a Python Notebook and run the first few cells:

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
session.use_database("CC_DEMO")
session.use_warehouse("CC_ML_WH")

# Check Dynamic Table status
session.sql("""
    SHOW DYNAMIC TABLES LIKE 'CREATOR_ENGAGEMENT%' IN SCHEMA CC_DEMO.ML
""").select('"name"', '"target_lag"', '"refresh_mode"', '"scheduling_state"', '"rows"').show()

# Preview features
session.table("CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES").limit(10).show()
```

The Dynamic Table refreshes automatically every 2 minutes. No scheduling, no ETL pipelines, no infrastructure to maintain.

<!-- ------------------------ -->
## Register Feature Store

### Create Entity and Feature Views

The Feature Store makes features discoverable, governed, and reusable. Register a `CREATOR` entity and attach the Dynamic Table as a feature view:

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

# Register engagement features from the Dynamic Table
engagement_df = session.table("CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES")
engagement_fv = FeatureView(
    name="CREATOR_ENGAGEMENT_7D",
    entities=[creator_entity],
    feature_df=engagement_df,
    timestamp_col="FEATURE_TIMESTAMP",
    refresh_freq="2 minutes",
    desc="Rolling 7-day creator engagement metrics from behavioral events",
)
engagement_fv = engagement_fv.attach_feature_desc({
    "SESSIONS_7D": "Distinct sessions in last 7 days",
    "AVG_CTR_7D": "Average click-through rate (7d)",
    "PURCHASES_7D": "Total purchases driven (7d)",
    "GMV_7D": "Total gross merchandise value driven (7d)",
    "UNIQUE_BRANDS_7D": "Distinct brands interacted with (7d)",
    "AVG_ENGAGEMENT_7D": "Average engagement score (7d)",
})
engagement_fv = fs.register_feature_view(feature_view=engagement_fv, version="V1")
```

### Generate a Training Dataset

The Feature Store generates training data with **ASOF joins** to prevent data leakage. Each row gets feature values that were available at the time of the interaction:

```python
spine_df = session.table("CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS").select(
    "CREATOR_ID", "BRAND_ID", "EVENT_TIMESTAMP", "CONVERTED"
).limit(50_000)

training_dataset = fs.generate_dataset(
    name="DEMO_TRAINING",
    spine_df=spine_df,
    features=[engagement_fv],
    spine_timestamp_col="EVENT_TIMESTAMP",
    desc="Training dataset for creator-brand match model",
    output_type="table",
)

training_pd = training_dataset.to_pandas()
print(f"Training dataset shape: {training_pd.shape}")
print(f"Label distribution:\n{training_pd['CONVERTED'].value_counts()}")
```

<!-- ------------------------ -->
## Train the Match Model

### Train XGBoost

Train an XGBoost classifier on the 6 engagement features to predict creator-brand match quality:

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import roc_auc_score, f1_score, classification_report

feature_cols = [
    "SESSIONS_7D", "AVG_CTR_7D", "PURCHASES_7D",
    "GMV_7D", "UNIQUE_BRANDS_7D", "AVG_ENGAGEMENT_7D",
]
label_col = "CONVERTED"

df = training_pd.dropna(subset=feature_cols)
X = df[feature_cols].fillna(0)
y = df[label_col].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- Baseline model (V0) ---
baseline_model = xgb.XGBClassifier(
    n_estimators=100, max_depth=4, learning_rate=0.1,
    eval_metric="logloss", random_state=42,
)
baseline_model.fit(X_train, y_train)
baseline_auc = roc_auc_score(y_test, baseline_model.predict_proba(X_test)[:, 1])
print(f"Baseline AUC-ROC: {baseline_auc:.4f}")

# --- Hyperparameter optimization via GridSearchCV ---
param_grid = {
    "max_depth": [4, 6, 8],
    "n_estimators": [100, 200],
    "learning_rate": [0.05, 0.1],
}

grid_search = GridSearchCV(
    estimator=xgb.XGBClassifier(eval_metric="logloss", random_state=42),
    param_grid=param_grid,
    cv=3,
    scoring="roc_auc",
    n_jobs=-1,
    verbose=1,
)
grid_search.fit(X_train, y_train)

model = grid_search.best_estimator_
print(f"\nBest parameters: {grid_search.best_params_}")
print(f"Best CV AUC-ROC: {grid_search.best_score_:.4f}")

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, y_prob)
f1 = f1_score(y_test, y_pred)

print(f"\nOptimized model — Test AUC-ROC: {auc:.4f}  (baseline: {baseline_auc:.4f})")
print(f"Optimized model — Test F1 Score: {f1:.4f}")
print()
print(classification_report(y_test, y_pred, target_names=["No Match", "Match"]))
```

You should see AUC around **0.70** and F1 around **0.65**, indicating the model has learned meaningful patterns from the engagement features.

### Log to Model Registry

Register the trained model as a first-class Snowflake object with versioning, metrics, and RBAC:

```python
from snowflake.ml.registry import Registry
from snowflake.ml.model import task

reg = Registry(session=session, database_name="CC_DEMO", schema_name="ML_REGISTRY")

try:
    mv = reg.get_model("CREATOR_BRAND_MATCH").version("V1")
    print("Model CREATOR_BRAND_MATCH V1 already exists — using existing version")
except:
    mv = reg.log_model(
        model=model,
        model_name="CREATOR_BRAND_MATCH",
        version_name="V1",
        conda_dependencies=["xgboost"],
        sample_input_data=X_test.head(10),
        comment="XGBoost creator-brand match model",
        metrics={"auc_roc": round(auc, 4), "f1_score": round(f1, 4)},
        task=task.Task.TABULAR_BINARY_CLASSIFICATION,
    )
    print("Model: CREATOR_BRAND_MATCH V1 — logged to registry")
print(f"\nAvailable functions:")
for fn in mv.show_functions():
    print(f"  {fn['name']} ({fn['target_method_function_type']})")
print(f"\nStored metrics: {mv.show_metrics()}")

# Set default version and production alias
m = reg.get_model("CREATOR_BRAND_MATCH")
m.default = "V1"

try:
    session.sql("""
        ALTER MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH
        VERSION V1 SET ALIAS = PRODUCTION
    """).collect()
    print("Alias 'PRODUCTION' set on V1")
except:
    print("Alias 'PRODUCTION' already exists on V1")

print("\nModel versions:")
print(m.show_versions().to_string())
```

V1 automatically gets `PREDICT`, `PREDICT_PROBA`, and `EXPLAIN` endpoints with zero additional code.

<!-- ------------------------ -->
## Deploy Real-Time Inference

### Batch Inference via Warehouse

Score all creators using SQL-based inference. This approach keeps CREATOR_ID in scope and runs entirely on the warehouse:

```python
results = session.sql("""
    SELECT
        e.CREATOR_ID,
        CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
            e.SESSIONS_7D, e.AVG_CTR_7D, e.PURCHASES_7D,
            e.GMV_7D, e.UNIQUE_BRANDS_7D, e.AVG_ENGAGEMENT_7D
        ):"output_feature_1"::FLOAT AS MATCH_SCORE
    FROM CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES e
    ORDER BY MATCH_SCORE DESC
""")

print("Top 10 Creators by Match Score:")
results.show(10)
```

### Deploy to SPCS

Deploy the model as a real-time REST API with Snowpark Container Services:

```python
mv.create_service(
    service_name="CC_MATCH_SERVICE",
    service_compute_pool="CC_COMPUTE_POOL",
    ingress_enabled=True,
    min_instances=0,   # Scale to zero when idle
    max_instances=3,
)
```

> **Tip:** `min_instances=0` enables scale-to-zero. The service auto-suspends after 30 minutes of inactivity, costing nothing when idle. First cold-start takes 2-3 minutes.

### Call the REST API

Once deployed, any external application can call the endpoint:

```bash
curl -X POST "https://<service-id>.snowflakecomputing.app/predict" \
  -H 'Authorization: Snowflake Token="<your-pat>"' \
  -H 'Content-Type: application/json' \
  -d '{
    "dataframe_split": {
      "columns": ["SESSIONS_7D","AVG_CTR_7D","PURCHASES_7D",
                   "GMV_7D","UNIQUE_BRANDS_7D","AVG_ENGAGEMENT_7D"],
      "data": [[25, 0.05, 3, 150.0, 5, 0.7]]
    }
  }'
```

Or invoke directly via SQL:

```sql
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
    10, 0.05, 3, 150.0, 5, 0.7
) AS MATCH_SCORE;
```

<!-- ------------------------ -->
## Build Multi-Endpoint Model

### Why a CustomModel

V1 provides automatic endpoints, but sometimes you need custom business logic. V2 uses `CustomModel` to define **three inference APIs** on a single set of weights:

- `predict_match_score` - Simple match probability
- `predict_ranked` - Ranked creator list with scores
- `predict_with_features` - Score plus per-feature contributions (SHAP workaround)

```python
import tempfile, joblib, xgboost as xgb
from snowflake.ml.model import custom_model

tmp_dir = tempfile.mkdtemp()
model_path = f"{tmp_dir}/xgb_model.joblib"
joblib.dump(model, model_path)

class CreatorMatchMultiEndpoint(custom_model.CustomModel):

    def __init__(self, context: custom_model.ModelContext) -> None:
        super().__init__(context)
        self.model = joblib.load(context.path("xgb_model"))

    @custom_model.inference_api
    def predict_match_score(self, input_df: pd.DataFrame) -> pd.DataFrame:
        proba = self.model.predict_proba(input_df)[:, 1]
        return pd.DataFrame({"MATCH_SCORE": proba})

    @custom_model.inference_api
    def predict_ranked(self, input_df: pd.DataFrame) -> pd.DataFrame:
        proba = self.model.predict_proba(input_df)[:, 1]
        result = input_df.copy()
        result["MATCH_SCORE"] = proba
        return result.sort_values("MATCH_SCORE", ascending=False).reset_index(drop=True)

    @custom_model.inference_api
    def predict_with_features(self, input_df: pd.DataFrame) -> pd.DataFrame:
        proba = self.model.predict_proba(input_df)[:, 1]
        booster = self.model.get_booster()
        dmat = xgb.DMatrix(input_df)
        contribs = booster.predict(dmat, pred_contribs=True)
        result = pd.DataFrame({"MATCH_SCORE": proba})
        for i, col in enumerate(input_df.columns):
            result[f"{col}_CONTRIB"] = contribs[:, i]
        result["BIAS"] = contribs[:, -1]
        return result

mc = custom_model.ModelContext(models={}, artifacts={"xgb_model": model_path})
multi_model = CreatorMatchMultiEndpoint(mc)

mv2 = reg.log_model(
    model=multi_model,
    model_name="CREATOR_BRAND_MATCH",
    version_name="V2",
    pip_requirements=["xgboost", "joblib"],
    sample_input_data=X_test.head(5),
    comment="Multi-endpoint CustomModel with 3 inference APIs",
)
```

### Invoke Any Endpoint via SQL

```sql
-- Match score only
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_MATCH_SCORE(
    10, 0.05, 3, 150.0, 5, 0.7
) AS SCORE;

-- Score with per-feature contributions
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_WITH_FEATURES(
    10, 0.05, 3, 150.0, 5, 0.7
) AS EXPLAINED;
```

<!-- ------------------------ -->
## Add Semantic Search

### Create a Cortex Search Service

Cortex Search provides hybrid semantic search (vector + keyword + reranking) with zero infrastructure:

```python
session.sql("""
    CREATE OR REPLACE CORTEX SEARCH SERVICE CC_DEMO.RAW.CREATOR_CONTENT_SEARCH
        ON content_text
        ATTRIBUTES category, creator_id, platform
        WAREHOUSE = CC_ML_WH
        TARGET_LAG = '1 day'
        EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
    AS (
        SELECT CREATOR_ID, CONTENT_TEXT, CATEGORY, PLATFORM
        FROM CC_DEMO.RAW.CREATOR_CONTENT
    )
""").collect()
```

### Search Creator Content

```python
from snowflake.core import Root

root = Root(session)
search_svc = (root
    .databases["CC_DEMO"]
    .schemas["RAW"]
    .cortex_search_services["CREATOR_CONTENT_SEARCH"]
)

results = search_svc.search(
    query="eco-friendly beauty products",
    columns=["CREATOR_ID", "CONTENT_TEXT", "CATEGORY"],
    limit=3,
)
for r in results.results:
    print(f"  {r['CREATOR_ID']} | {r['CATEGORY']:8s} | {r['CONTENT_TEXT'][:60]}")
```

This returns ranked results combining semantic understanding with keyword matching, filtered by category. Response time is typically under 200ms.

<!-- ------------------------ -->
## Build the Streamlit Dashboard

### Deploy the Dashboard

The [assets folder](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets/app) includes a 6-page Streamlit app. Deploy it to Snowflake:

1. In Snowsight, navigate to **Projects > Streamlit > + Streamlit App**
2. Name it `CREATOR_MATCH_DEMO` in the `CC_DEMO.APPS` schema
3. Select `CC_ML_WH` as the warehouse
4. Replace the default code with the contents of [streamlit_app.py](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets/app/streamlit_app.py)

### What Each Page Shows

**Page 1: Feature Store** - Browse registered entities and feature views. Preview the latest engagement features with distribution charts.

**Page 2: Model Registry** - View registered models, versions, aliases, and stored metrics (AUC, F1).

**Page 3: Inference & API** - Interactive form to test batch predictions. Enter creator features and get a real-time match score. Includes REST API reference for external integration.

**Page 4: CDP Profiles** - Creator tier distribution (PREMIUM / STANDARD / EMERGING) based on ML scores. Brand affinity clusters (POWER_CONVERTER, NICHE_SPECIALIST, BROAD_REACH, EMERGING_TALENT) and enriched profile data.

**Page 5: Cortex Search** - Interactive hybrid search over creator content with category and platform filters.

**Page 6: Model Monitoring** - Monitor status, prediction drift (Population Stability Index), prediction volume, and version comparison with metrics side-by-side.

<!-- ------------------------ -->
## Run CDP Enrichment

### Score All Creators and Assign Tiers

Use the model to enrich creator profiles with ML-inferred attributes. This is a two-step process: first score all creators, then build enriched profiles with tier assignments and brand affinity clusters.

```python
# Step 1: Batch inference — score all creators via SQL function
print("Step 1: Batch inference on all creators...")
session.sql("""
    CREATE OR REPLACE TABLE CC_DEMO.ML.MATCH_PREDICTIONS AS
    WITH scored AS (
        SELECT
            e.CREATOR_ID,
            e.SESSIONS_7D, e.AVG_CTR_7D, e.PURCHASES_7D,
            e.GMV_7D, e.UNIQUE_BRANDS_7D, e.AVG_ENGAGEMENT_7D,
            CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
                e.SESSIONS_7D, e.AVG_CTR_7D, e.PURCHASES_7D,
                e.GMV_7D, e.UNIQUE_BRANDS_7D, e.AVG_ENGAGEMENT_7D
            ) AS RAW_SCORE
        FROM CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES e
    )
    SELECT
        CREATOR_ID, SESSIONS_7D, AVG_CTR_7D, PURCHASES_7D,
        GMV_7D, UNIQUE_BRANDS_7D, AVG_ENGAGEMENT_7D,
        RAW_SCORE:"output_feature_1"::FLOAT AS MATCH_SCORE,
        CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS SCORED_AT
    FROM scored
""").collect()
pred_count = session.sql("SELECT COUNT(*) AS N FROM CC_DEMO.ML.MATCH_PREDICTIONS").collect()[0]["N"]
print(f"  Scored {pred_count} creators → CC_DEMO.ML.MATCH_PREDICTIONS")

# Step 2: Build enriched profile with tiers and clusters
print("\nStep 2: Building enriched CREATOR_PROFILES...")
session.sql("""
    CREATE OR REPLACE TABLE CC_DEMO.ML.CREATOR_PROFILES AS
    WITH interaction_stats AS (
        SELECT
            CREATOR_ID,
            AVG(CASE WHEN CONVERTED THEN 1 ELSE 0 END) AS CONVERSION_RATE,
            COUNT(DISTINCT BRAND_ID) AS BRAND_COUNT
        FROM CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS
        GROUP BY CREATOR_ID
    )
    SELECT
        c.CREATOR_ID, c.CREATOR_NAME, c.CATEGORY, c.FOLLOWER_COUNT, c.COUNTRY,
        s.SESSIONS_7D, s.AVG_CTR_7D, s.AVG_ENGAGEMENT_7D,
        s.MATCH_SCORE,
        CASE WHEN s.MATCH_SCORE >= 0.50 THEN 'PREMIUM'
             WHEN s.MATCH_SCORE >= 0.30 THEN 'STANDARD'
             ELSE 'EMERGING' END AS CREATOR_TIER,
        LEAST(100, GREATEST(0, ROUND(s.AVG_ENGAGEMENT_7D * 100 / 0.15, 1)))
            AS CONTENT_QUALITY_SCORE,
        CASE WHEN i.CONVERSION_RATE > 0.7 AND i.BRAND_COUNT >= 5 THEN 'POWER_CONVERTER'
             WHEN i.CONVERSION_RATE > 0.5 AND i.BRAND_COUNT < 5  THEN 'NICHE_SPECIALIST'
             WHEN i.BRAND_COUNT >= 8                               THEN 'BROAD_REACH'
             ELSE 'EMERGING_TALENT' END AS BRAND_AFFINITY_CLUSTER
    FROM CC_DEMO.RAW.CREATORS c
    JOIN CC_DEMO.ML.MATCH_PREDICTIONS s ON c.CREATOR_ID = s.CREATOR_ID
    LEFT JOIN interaction_stats i ON c.CREATOR_ID = i.CREATOR_ID
""").collect()
profile_count = session.sql("SELECT COUNT(*) AS N FROM CC_DEMO.ML.CREATOR_PROFILES").collect()[0]["N"]
print(f"  Built {profile_count} enriched profiles → CC_DEMO.ML.CREATOR_PROFILES")
```

### Expected Tier Distribution

| Tier | Target % | Description |
|------|----------|-------------|
| PREMIUM | ~18% | High-value creators with strong engagement |
| STANDARD | ~25% | Consistent performers with moderate scores |
| EMERGING | ~57% | Growing creators with developing engagement |

### Validate

```sql
SELECT CREATOR_TIER, COUNT(*) AS CNT,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS PCT
FROM CC_DEMO.ML.CREATOR_PROFILES
GROUP BY 1 ORDER BY PCT DESC;
```

<!-- ------------------------ -->
## Clean Up

### Remove All Demo Objects

When you are finished with the guide, run the teardown script to remove all objects:

```sql
-- Run in Snowsight: sql/99_teardown.sql
-- This drops (in order):
-- 1. SPCS inference service
-- 2. Cortex Search service
-- 3. Streamlit app
-- 4. Models from registry
-- 5. ML tables and Dynamic Tables
-- 6. Feature Store schema
-- 7. All remaining schemas
-- 8. CC_DEMO database
-- 9. CC_ML_WH warehouse
-- 10. CC_COMPUTE_POOL compute pool
```

Or run from the command line:

```bash
snowsql -c <your_connection> -f sql/99_teardown.sql
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You have successfully built an AI-powered matching application on Snowflake that covers the full ML lifecycle: feature engineering with Dynamic Tables, training with Feature Store, model versioning in the Registry, real-time deployment via SPCS, semantic search with Cortex Search, model monitoring with drift detection, and an interactive Streamlit dashboard.

### What You Learned

- How **Dynamic Tables** eliminate manual ETL by auto-refreshing engagement features
- How the **Feature Store** provides governed, reusable features with ASOF joins for training and online serving for inference
- How the **Model Registry** gives you immutable versioning, aliases for zero-downtime promotion, and RBAC for access control
- How **SPCS** turns any model into a real-time REST API with scale-to-zero cost optimization
- How **CustomModel** lets you define multiple inference endpoints on a single set of weights
- How **Cortex Search** provides hybrid semantic search with no infrastructure to manage
- How **Model Monitors** track prediction drift and volume over time with built-in metric functions
- How **Streamlit in Snowflake** brings all components together in an interactive dashboard

### Related Resources

- [Snowflake ML Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)
- [Feature Store Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview)
- [Model Registry Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Model Monitoring](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/model-monitor)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)

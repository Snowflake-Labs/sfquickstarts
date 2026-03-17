
# =============================================================================
# Creator-Brand Match Score — Snowflake ML Demo
# Feature Store → Model Registry → Real-Time Inference → REST API
# + Extensions: Multi-Endpoint, EAI, Embeddings, Search, Backfill, CDP
#
# Run cell-by-cell in Snowsight. All data is pre-loaded.
# =============================================================================


# %% [markdown]
# # Creator-Brand Match Score — Snowflake ML Demo
#
# **The Problem:** A brand submits a campaign brief. You need to return ranked
# creators with match scores in <100ms — but your ML infrastructure is a mess of
# ETL pipelines, feature stores, model servers, and search clusters.
#
# **The Solution:** Feature Store → Model Registry → SPCS → REST API — all on
# one platform. No data movement. No infrastructure to manage. This demo shows
# how.


# %% --- Cell 2: Session Setup ---
from snowflake.snowpark.context import get_active_session

session = get_active_session()
session.use_database("CC_DEMO")
session.use_warehouse("CC_ML_WH")

# Query tag for monitoring and troubleshooting (sfguide best practice)
session.query_tag = {"origin": "sf_sit-is",
                     "name": "sfguide_creator_brand_match",
                     "version": {"major": 1, "minor": 0},
                     "attributes": {"is_quickstart": 1, "source": "notebook"}}

print(f"Role:      {session.get_current_role()}")
print(f"Warehouse: {session.get_current_warehouse()}")
print(f"Database:  {session.get_current_database()}")


# %% [markdown]
# ## Step 1: Dynamic Tables — Behavioral Events to ML Features
#
# Your streaming cluster processes millions of events per hour just to compute
# rolling aggregates. With **Dynamic Tables**, Snowflake handles the incremental
# refresh automatically — 2-minute lag, zero infrastructure.


# %% --- Cell 4: Dynamic Table Inspection ---
session.sql("""
    SHOW DYNAMIC TABLES LIKE 'CREATOR_ENGAGEMENT%' IN SCHEMA CC_DEMO.ML
""").select('"name"', '"target_lag"', '"refresh_mode"', '"scheduling_state"', '"rows"').show()

row_count = session.sql("SELECT COUNT(*) AS TOTAL_CREATORS FROM CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES").collect()[0]["TOTAL_CREATORS"]
print(f"\nCreators with computed features: {row_count:,}")

print("\nSample features (10 rows):")
session.table("CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES").limit(10).show()


# %% [markdown]
# ## Step 2: Feature Store — Register, Discover, Govern
#
# The Feature Store is a schema — entities and feature views are **first-class
# Snowflake objects** with RBAC and ML Lineage. Same features serve both training
# and inference (zero skew). Online serving delivers features in **<30ms**.


# %% --- Cell 6: Feature Store — Entity and Engagement Feature View ---
from snowflake.ml.feature_store import FeatureStore, FeatureView, Entity, CreationMode

fs = FeatureStore(
    session=session,
    database="CC_DEMO",
    name="FEATURE_STORE",
    default_warehouse="CC_ML_WH",
    creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
)

creator_entity = Entity(
    name="CREATOR",
    join_keys=["CREATOR_ID"],
    desc="Creator — lifestyle influencer on the platform",
)
fs.register_entity(creator_entity)

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

print("Registered Entities:")
fs.list_entities().show()

print("\nRegistered Feature Views:")
fs.list_feature_views().show()


# %% --- Cell 7: Online Feature View — Creator Profile ---
from snowflake.ml.feature_store.feature_view import OnlineConfig

profile_df = session.sql("""
    SELECT CREATOR_ID, FOLLOWER_COUNT, CATEGORY, COUNTRY,
           AVG_ENGAGEMENT AS HISTORICAL_ENGAGEMENT
    FROM CC_DEMO.RAW.CREATORS
""")

try:
    profile_fv = FeatureView(
        name="CREATOR_PROFILE",
        entities=[creator_entity],
        feature_df=profile_df,
        desc="Static creator profile with online serving for real-time lookups",
        online_config=OnlineConfig(enable=True, target_lag="30 seconds"),
    )
    profile_fv = fs.register_feature_view(feature_view=profile_fv, version="V1")
    print(f"Online Feature View: {profile_fv.name} v{profile_fv.version}")
    print(f"Online serving enabled: {profile_fv.online}")
except Exception as e:
    print(f"Online serving not available on this account: {e}")
    print("Note: Online feature tables require Snowflake >= 9.26")


# %% [markdown]
# ## Step 3: Training Dataset — Point-in-Time Correct ASOF Joins
#
# The Feature Store generates training data with **ASOF joins** — each row gets
# the feature values that were available *at that point in time*. This prevents
# data leakage and ensures the model trains on historically accurate features.
# The same Feature Store serves inference — **zero training/serving skew**.


# %% --- Cell 9: Generate Training Dataset ---
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
print(f"Columns: {list(training_pd.columns)}")
print(f"\nLabel distribution:")
print(training_pd["CONVERTED"].value_counts().to_string())
print(f"\nSample rows:")
print(training_pd.head(5).to_string(index=False))


# %% [markdown]
# ## Step 4: Feature Engineering — Snowpark Analytics API
#
# Before training, enrich raw features using Snowpark's **analytics API**.
# `compute_lag()` and `moving_agg()` run directly on Snowpark DataFrames —
# no separate feature pipeline needed. These derived features capture temporal
# trends that improve model performance.


# %% --- Cell 10b: Feature Engineering ---
import pandas as pd

# Demonstrate Snowpark analytics API for feature enrichment
engagement_sp_df = session.table("CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES")

# Lag features: compare current engagement to prior periods
try:
    enriched_df = engagement_sp_df.analytics.compute_lag(
        cols=["AVG_ENGAGEMENT_7D", "SESSIONS_7D"],
        lags=[1],
        partition_by=["CREATOR_ID"],
        order_by=["FEATURE_TIMESTAMP"],
    )
    print("Lag features added via compute_lag():")
    enriched_df.select(
        "CREATOR_ID", "AVG_ENGAGEMENT_7D", "LAG_AVG_ENGAGEMENT_7D_1",
        "SESSIONS_7D", "LAG_SESSIONS_7D_1"
    ).show(5)
except Exception as e:
    print(f"Analytics API note: {e}")
    print("compute_lag() requires Snowpark ML >= 1.5.0")


# %% [markdown]
# ## Step 5: Model Training — XGBoost with Hyperparameter Optimization
#
# We train with **GridSearchCV** to find optimal hyperparameters via
# cross-validation, following the same pattern used in the Snowflake ML
# diamonds quickstart. The grid search evaluates multiple combinations of
# `max_depth`, `n_estimators`, and `learning_rate`, selecting the best
# model by AUC-ROC.


# %% --- Cell 11: Train XGBoost with GridSearchCV ---
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


# %% [markdown]
# ## Step 5: Model Registry — Log, Version, Govern, Explain
#
# `MODEL` is a **first-class schema-level Snowflake object**. Versioning is
# immutable — you can never overwrite V1. **Aliases** (PRODUCTION, STAGING)
# enable zero-downtime promotion. Built-in **SHAP explainability** shows which
# features drive each prediction. This is the registry sophistication story.


# %% --- Cell 13: Log Model to Registry ---
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


# %% --- Cell 14: Versioning, Aliases, Promotion ---
m = reg.get_model("CREATOR_BRAND_MATCH")
m.default = "V1"
print(f"Default version: {m.default.version_name}")

try:
    session.sql("""
        ALTER MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH
        VERSION V1 SET ALIAS = PRODUCTION
    """).collect()
    print("Alias 'PRODUCTION' set on V1")
except:
    print("Alias 'PRODUCTION' already exists on V1")

m.comment = "Production creator-brand match model for campaign recommendations"

print("\nModel versions:")
print(m.show_versions().to_string())


# %% [markdown]
# ### Model RBAC — Govern Access Across Teams
#
# Models are **first-class Snowflake objects** with full RBAC. Grant usage to
# ML engineers for inference, monitor access to ops teams for observability,
# and restrict production promotion to senior roles. No external ACL system needed.


# %% --- Cell 14b: Model RBAC ---
print("Model RBAC — granting access across teams:")

# Grant inference access to a data science role
session.sql("""
    GRANT USAGE ON MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH
    TO ROLE SYSADMIN
""").collect()
print("  GRANT USAGE ON MODEL → SYSADMIN (can run inference)")

# Note: MODEL objects support USAGE and OWNERSHIP privileges
# MONITOR is not a valid privilege for MODEL objects
print("  Note: Use USAGE for inference, OWNERSHIP for full control")

print("""
RBAC patterns for production:
  GRANT USAGE ON MODEL ... TO ROLE ML_ENGINEER;      -- inference only
  GRANT OWNERSHIP ON MODEL ... TO ROLE ML_ADMIN;     -- full control
  -- Version-level: only ML_ADMIN can SET ALIAS = 'PRODUCTION'
""")

# Show current grants
print("Current grants on CREATOR_BRAND_MATCH:")
session.sql("""
    SHOW GRANTS ON MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH
""").show()


# %% [markdown]
# ### ML Lineage — Trace Data-to-Model Provenance
#
# Snowflake tracks **object-level lineage** automatically. Query
# `ACCOUNT_USAGE.OBJECT_DEPENDENCIES` to see how raw tables feed Dynamic Tables,
# which feed Feature Views, which feed model training — all without external
# orchestration or metadata catalogs.

# %% --- Cell 14c: ML Lineage ---
print("ML Lineage — data-to-model dependency chain:")
lineage_df = session.sql("""
    SELECT
        REFERENCING_OBJECT_NAME   AS DOWNSTREAM,
        REFERENCING_OBJECT_DOMAIN AS DOWNSTREAM_TYPE,
        REFERENCED_OBJECT_NAME    AS UPSTREAM,
        REFERENCED_OBJECT_DOMAIN  AS UPSTREAM_TYPE
    FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
    WHERE REFERENCED_DATABASE  = 'CC_DEMO'
       OR REFERENCING_DATABASE = 'CC_DEMO'
    ORDER BY DOWNSTREAM
""")
lineage_df.show()

print("""
Lineage chain (auto-tracked by Snowflake):
  RAW.CREATORS ──► ML.CREATOR_PROFILE$V1 (Feature View)
  RAW.BEHAVIORAL_EVENTS ──► ML.CREATOR_ENGAGEMENT_FEATURES (Dynamic Table)
  ML.CREATOR_ENGAGEMENT_FEATURES ──► ML.CREATOR_ENGAGEMENT_7D$V1 (Feature View)
  Feature Views ──► Model Training ──► ML_REGISTRY.CREATOR_BRAND_MATCH

No external lineage tool needed — Snowflake knows the full graph.
""")


# %% [markdown]
# ### ML Observability — Model Monitor for Drift Detection
#
# Snowflake Model Monitoring (GA) tracks **drift, performance, and volume**
# over time. `CREATE MODEL MONITOR` attaches a monitor to a model version,
# using a source table for predictions and a baseline for comparison.
# The monitor auto-refreshes via Dynamic Tables, and dashboards are visible
# in Snowsight under AI & ML → Models.

# %% --- Cell 14d: ML Observability + Model Monitor ---
print("ML Observability — model version dashboard:")
session.sql("SHOW VERSIONS IN MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH").collect()
versions_df = session.sql("""
    SELECT
        "name"          AS VERSION,
        "aliases"       AS ALIASES,
        "comment"       AS COMMENT,
        PARSE_JSON("metadata"):metrics:auc_roc::FLOAT   AS AUC_ROC,
        PARSE_JSON("metadata"):metrics:f1_score::FLOAT   AS F1_SCORE,
        ARRAY_SIZE(PARSE_JSON("inference_services"))      AS ACTIVE_SERVICES,
        "created_on"    AS CREATED_ON
    FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
    ORDER BY "created_on"
""")
versions_df.show()


# %% [markdown]
# ### Model Explainability — Two-Layer: Quantitative SHAP + Cortex LLM Narratives
#
# The Registry provides a built-in `EXPLAIN` function (SHAP-based) for supported
# model/library versions. For production dashboards, we go further with a **two-layer**
# approach: quantitative feature contributions via XGBoost's native `pred_contribs`
# (identical Shapley values, zero dependencies), then **Cortex LLM** to translate
# those numbers into actionable business narratives — prediction → explanation →
# recommendation, entirely in Snowflake.


# %% --- Cell 15: Model Explainability ---
import matplotlib.pyplot as plt
import numpy as np

# XGBoost native Shapley values via pred_contribs
booster = model.get_booster()
dmat = xgb.DMatrix(X_test)
shap_values = booster.predict(dmat, pred_contribs=True)

# shap_values shape: (n_samples, n_features + 1) — last column is bias
feature_importance = np.abs(shap_values[:, :-1]).mean(axis=0)

print("Layer 1 — Quantitative Feature Importance (XGBoost native Shapley values):")
for name, imp in sorted(zip(feature_cols, feature_importance), key=lambda x: -x[1]):
    print(f"  {name:25s} {imp:.4f}")

# Bar chart of mean |SHAP| values
fig, ax = plt.subplots(figsize=(8, 4))
sorted_idx = np.argsort(feature_importance)
ax.barh([feature_cols[i] for i in sorted_idx], feature_importance[sorted_idx])
ax.set_xlabel("Mean |SHAP Value|")
ax.set_title("Feature Importance — XGBoost Shapley Values")
plt.tight_layout()
plt.show()

# --- Layer 2: Cortex LLM Business Narrative ---
print("\nLayer 2 — Cortex LLM Business Narrative:")

# Pick a sample creator and build context for the LLM
sample_idx = 0
sample_features = X_test.iloc[sample_idx]
sample_shap = shap_values[sample_idx, :-1]  # exclude bias

# Build feature context string
feature_context = "\n".join(
    f"  - {name}: value={sample_features[name]:.3f}, SHAP contribution={sample_shap[i]:+.4f}"
    for i, name in enumerate(feature_cols)
)

prompt = f"""You are a data analyst for a creator commerce platform. A creator-brand match model
produced a prediction. Explain WHY this creator is or isn't a good match for the brand,
using the feature values and their SHAP contributions below. Be specific, reference the
actual numbers, and end with one actionable recommendation. Keep it to 3-4 sentences.

Feature contributions for this creator:
{feature_context}

Business explanation:"""

# Escape single quotes for SQL
safe_prompt = prompt.replace("'", "''")

llm_result = session.sql(f"""
    SELECT SNOWFLAKE.CORTEX.AI_COMPLETE('claude-3-5-sonnet', '{safe_prompt}') AS EXPLANATION
""").collect()

print(llm_result[0]["EXPLANATION"])


# %% [markdown]
# ## Step 6: Inference — Batch (Warehouse) and Real-Time (SPCS + REST API)
#
# Same model, two deployment targets. **Warehouse** for batch pipelines and
# scheduled scoring. **SPCS** for <100ms online serving with auto-scaling and
# a REST endpoint that any external application can call.


# %% --- Cell 17: Batch Inference via Warehouse ---
# Use SQL-based batch inference to avoid cartesian product.
# mv.run() returns a DataFrame without CREATOR_ID, so joining it back
# to the features table produces N×N rows. The SQL !PREDICT_PROBA pattern
# keeps CREATOR_ID in scope and runs entirely on the warehouse.

results = session.sql("""
    SELECT
        e.CREATOR_ID,
        CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
            e.SESSIONS_7D, e.AVG_CTR_7D, e.PURCHASES_7D,
            e.GMV_7D, e.UNIQUE_BRANDS_7D, e.AVG_ENGAGEMENT_7D
        ):"output_feature_0"::FLOAT AS P_NO_MATCH,
        CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
            e.SESSIONS_7D, e.AVG_CTR_7D, e.PURCHASES_7D,
            e.GMV_7D, e.UNIQUE_BRANDS_7D, e.AVG_ENGAGEMENT_7D
        ):"output_feature_1"::FLOAT AS P_MATCH
    FROM CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES e
    ORDER BY P_MATCH DESC
""")

print("Top 10 Creators by Match Score:")
results.show(10)


# %% [markdown]
# ### Real-Time Inference — Deploy to SPCS
#
# **Warning:** This cell takes 5-10 minutes on first deployment. Pre-deploy
# before the demo if possible. If the service is already running, it will
# show the existing endpoints.


# %% --- Cell 19: Deploy to SPCS ---
try:
    service_status = session.sql("""
        SHOW SERVICES LIKE 'CC_MATCH%' IN SCHEMA CC_DEMO.ML_REGISTRY
    """).collect()

    if len(service_status) > 0:
        print("Service already deployed:")
        session.sql("SHOW SERVICES LIKE 'CC_MATCH%' IN SCHEMA CC_DEMO.ML_REGISTRY").show()
        print("\nEndpoints:")
        session.sql("SHOW ENDPOINTS IN SERVICE CC_DEMO.ML_REGISTRY.CC_MATCH_SERVICE").show()

        # Model-managed services auto-suspend after 30 min (auto_resume=true),
        # which provides effective scale-to-zero behavior.
        print("\nNote: Service has auto_resume=true, auto_suspend=1800s (scale-to-zero)")
        try:
            session.sql("""
                ALTER SERVICE CC_DEMO.ML_REGISTRY.CC_MATCH_SERVICE
                SET MAX_INSTANCES = 3
            """).collect()
            print("Updated CC_MATCH_SERVICE: max_instances=3")
        except Exception as e:
            print(f"Service config note: {e}")
    else:
        print("Deploying CC_MATCH_SERVICE to SPCS...")
        mv.create_service(
            service_name="CC_MATCH_SERVICE",
            service_compute_pool="CC_COMPUTE_POOL",
            ingress_enabled=True,
            min_instances=0,   # scale-to-zero: auto-suspend after 30 min inactivity
            max_instances=3,
        )
        print("Service deployment initiated. Checking status...")
        session.sql("SHOW SERVICES LIKE 'CC_MATCH%' IN SCHEMA CC_DEMO.ML_REGISTRY").show()

    # SPCS health metrics
    print("\nSPCS service metrics:")
    try:
        session.sql("""
            SELECT * FROM TABLE(
                CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!SPCS_GET_METRICS()
            )
        """).show()
    except Exception as e:
        print(f"  SPCS_GET_METRICS note: {e}")
        print("  Metrics available when service is READY.")

except Exception as e:
    print(f"SPCS deployment note: {e}")
    print("Check available compute pools: SHOW COMPUTE POOLS")


# %% --- Cell 20: Invoke Model via SQL ---
print("Invoking model directly via SQL (uses default version):")
session.sql("""
    SELECT
        CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
            10, 0.05, 3, 150.0, 5, 0.7
        ) AS MATCH_PREDICTION
""").show()


# %% [markdown]
# ### REST API — Call from External Applications
#
# Any application can call the SPCS endpoint with a **Programmatic Access Token**.
# The payload uses the `dataframe_split` format. This is what powers real-time
# creator recommendations in production.
#
# **Python Example:**
# ```python
# import json, pandas as pd, requests
#
# ENDPOINT_URL = "https://<service-id>.snowflakecomputing.app/predict"
# PAT = "<your-programmatic-access-token>"
#
# input_df = pd.DataFrame({
#     "SESSIONS_7D": [25, 100, 5],
#     "AVG_CTR_7D": [0.05, 0.12, 0.02],
#     "PURCHASES_7D": [3, 15, 0],
#     "GMV_7D": [150.0, 2500.0, 0.0],
#     "UNIQUE_BRANDS_7D": [5, 12, 1],
#     "AVG_ENGAGEMENT_7D": [0.7, 0.92, 0.15],
# })
#
# payload = {"dataframe_split": json.loads(input_df.to_json(orient="split"))}
#
# response = requests.post(
#     ENDPOINT_URL,
#     headers={
#         "Authorization": f'Snowflake Token="{PAT}"',
#         "Content-Type": "application/json",
#     },
#     json=payload,
#     timeout=30,
# )
# print(f"Status: {response.status_code}")
# print(f"Predictions: {response.json()}")
# ```
#
# **curl Example:**
# ```bash
# curl -X POST "https://<service-id>.snowflakecomputing.app/predict" \
#   -H "Authorization: Snowflake Token=\"<PAT>\"" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "dataframe_split": {
#       "columns": ["SESSIONS_7D","AVG_CTR_7D","PURCHASES_7D",
#                    "GMV_7D","UNIQUE_BRANDS_7D","AVG_ENGAGEMENT_7D"],
#       "data": [[25, 0.05, 3, 150.0, 5, 0.7]]
#     }
#   }'
# ```


# %% [markdown]
# ## Core Demo Summary
#
# **What we built — all on one platform, zero data movement:**
#
# | Layer | What | Latency |
# |-------|------|---------|
# | Feature Store | Managed refresh, online serving | <30ms |
# | Model Registry | Immutable versions, RBAC, aliases | — |
# | Batch inference | Score all creators on warehouse | seconds |
# | Real-time inference | SPCS with auto-scaling | <100ms |
# | REST API | External apps, any language | <100ms |
#
# The model runs where the data lives. The extensions below show what happens
# when you need more: custom endpoints, network calls, embeddings, search.


# %% [markdown]
# ---
# # Extensions — Addressing Your Specific Requirements
#
# The following cells address the specific technical requirements discussed:
# multi-endpoint models, external network calls, custom embeddings, hybrid
# search, embedding backfill, and CDP enrichment.


# %% [markdown]
# ### Extension 1: Multi-Endpoint CustomModel (V2)
#
# **V1 gave you automatic endpoints** — PREDICT, PREDICT_PROBA, EXPLAIN — with
# zero code. But what if EXPLAIN hits platform constraints? Or you need custom
# business logic like ranked results?
#
# **V2 uses `CustomModel`** with multiple `@inference_api` methods. One set of
# weights, three endpoints: match score, ranked features, and per-feature
# contributions (per-feature Shapley values). This is the "when you need control" path.


# %% --- Cell 25: Multi-Endpoint CustomModel ---
import tempfile, joblib
from snowflake.ml.model import custom_model

# Save trained XGBoost weights for ModelContext
tmp_dir = tempfile.mkdtemp()
model_path = f"{tmp_dir}/xgb_model.joblib"
joblib.dump(model, model_path)

class CreatorMatchMultiEndpoint(custom_model.CustomModel):
    """Single model, three inference endpoints — one set of weights."""

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

# Test locally — all 3 endpoints
test_df = X_test.head(5)
print("--- predict_match_score ---")
print(multi_model.predict_match_score(test_df).to_string(index=False))

print("\n--- predict_ranked ---")
print(multi_model.predict_ranked(test_df).to_string(index=False))

print("\n--- predict_with_features ---")
print(multi_model.predict_with_features(test_df).to_string(index=False))

try:
    mv2 = reg.get_model("CREATOR_BRAND_MATCH").version("V2")
    print("\nModel CREATOR_BRAND_MATCH V2 already exists — using existing version")
except:
    mv2 = reg.log_model(
        model=multi_model,
        model_name="CREATOR_BRAND_MATCH",
        version_name="V2",
        pip_requirements=["xgboost", "joblib"],
        sample_input_data=test_df,
        comment="Multi-endpoint CustomModel with 3 inference APIs",
    )
    print("\nModel CREATOR_BRAND_MATCH V2 — logged to registry")

print("\nRegistered functions on V2:")
for fn in mv2.show_functions():
    print(f"  {fn['name']} ({fn['target_method_function_type']})")

print("\n" + "=" * 70)
print("SQL — invoke any endpoint by name")
print("=" * 70)
print("""
-- Match score only
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_MATCH_SCORE(
    10, 0.05, 3, 150.0, 5, 0.7
) AS SCORE;

-- Ranked creators (top 5)
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_RANKED(
    10, 0.05, 3, 150.0, 5, 0.7
) AS RANKED;

-- Score + per-feature SHAP contributions
SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_WITH_FEATURES(
    10, 0.05, 3, 150.0, 5, 0.7
) AS EXPLAINED;
""")


# %% [markdown]
# ### Extension 2: External Access Integration
#
# Models running in containers often need to call external services — video CDNs,
# cloud storage, third-party APIs. **External Access Integrations** enable this
# with explicit network rules and full audit trails.


# %% --- Cell 26: External Access Integration ---
print("=" * 70)
print("1. Network Rules + External Access Integrations (SQL)")
print("=" * 70)
print("""
-- Network Rule: allow egress to video CDN
CREATE OR REPLACE NETWORK RULE VIDEO_CDN_RULE
    MODE = EGRESS  TYPE = HOST_PORT
    VALUE_LIST = ('stream.mux.com:443', 'api.mux.com:443');

-- Network Rule: allow egress to S3
CREATE OR REPLACE NETWORK RULE S3_RULE
    MODE = EGRESS  TYPE = HOST_PORT
    VALUE_LIST = ('s3.amazonaws.com:443', 's3.us-east-1.amazonaws.com:443');

-- External Access Integration: video CDN
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION VIDEO_CDN_ACCESS
    ALLOWED_NETWORK_RULES = (VIDEO_CDN_RULE)  ENABLED = TRUE;

-- External Access Integration: S3
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION S3_ACCESS
    ALLOWED_NETWORK_RULES = (S3_RULE)  ENABLED = TRUE;
""")

print("=" * 70)
print("2. CustomModel with Runtime Network Calls (Python)")
print("=" * 70)
print("""
class CreatorContentEnricher(custom_model.CustomModel):
    @custom_model.inference_api
    def enrich(self, input_df: pd.DataFrame) -> pd.DataFrame:
        import requests
        thumbnails = []
        for url in input_df["VIDEO_URL"]:
            resp = requests.get(f"https://api.mux.com/v1/thumbnails/{url}",
                                timeout=5)
            thumbnails.append(resp.json().get("thumbnail_url", ""))
        input_df["THUMBNAIL"] = thumbnails
        return input_df
""")

print("=" * 70)
print("3. Deploy with External Access (Python)")
print("=" * 70)
print("""
mv_enricher.create_service(
    service_name="CC_ENRICHMENT_SERVICE",
    service_compute_pool="STREAMLIT_COMPUTE_POOL",
    ingress_enabled=True,
    max_instances=3,
    external_access_integrations=["VIDEO_CDN_ACCESS", "S3_ACCESS"],
)
""")

print("=" * 70)
print("4. Comparison: Previous Platform vs Snowflake")
print("=" * 70)
comparison = pd.DataFrame({
    "Capability": [
        "Multiple endpoints",
        "Custom preprocessing",
        "Network calls at runtime",
        "S3 access from model",
        "Infrastructure",
    ],
    "Previous Platform": [
        "Log weights N times",
        "Separate container",
        "Blocked by default",
        "Manual IAM + sidecar",
        "Self-managed K8s",
    ],
    "Snowflake": [
        "N @inference_api on 1 model",
        "Built into CustomModel",
        "EAI with audit trail",
        "Network Rule + EAI",
        "Fully managed SPCS",
    ],
})
print(comparison.to_string(index=False))


# %% [markdown]
# ### Extension 3: Custom Embeddings
#
# You need embeddings for creator content — bios, captions, video transcripts.
# Three paths: built-in Sentence Transformers (fast start), HuggingFace Pipeline
# (standard models), or CustomModel (multi-modal, full control). All store as
# **VECTOR** with native similarity search.


# %% --- Cell 27: Custom Embeddings ---
# Section A — Sentence Transformer (built-in, log directly to Registry)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np

    st_model = SentenceTransformer("all-MiniLM-L6-v2")
    try:
        mv_emb = reg.get_model("CREATOR_TEXT_EMBEDDER").version("V1")
        print("CREATOR_TEXT_EMBEDDER V1 already exists — using existing version")
    except:
        mv_emb = reg.log_model(
            model=st_model,
            model_name="CREATOR_TEXT_EMBEDDER",
            version_name="V1",
            pip_requirements=["sentence-transformers"],
            sample_input_data=pd.DataFrame({"text": ["sample text"]}),
            comment="Sentence Transformer all-MiniLM-L6-v2 for creator content embeddings",
        )
        print("CREATOR_TEXT_EMBEDDER V1 logged.")
    print("\nRegistered functions:")
    for fn in mv_emb.show_functions():
        print(f"  {fn['name']} ({fn['target_method_function_type']})")

    # Run inference on 3 sample texts
    sample_texts = [
        "Sustainable fashion haul featuring eco-friendly brands",
        "Morning skincare routine with clean beauty products",
        "HIIT workout for beginners at home",
    ]
    embeddings = st_model.encode(sample_texts)
    print(f"\nEmbedding shape: {embeddings.shape}")
    print(f"First embedding (truncated): [{', '.join(f'{x:.4f}' for x in embeddings[0][:8])} ...]")

    # Cosine similarity
    from numpy.linalg import norm
    cos_sim = lambda a, b: np.dot(a, b) / (norm(a) * norm(b))
    print(f"\nSimilarity (fashion vs beauty):  {cos_sim(embeddings[0], embeddings[1]):.4f}")
    print(f"Similarity (fashion vs fitness): {cos_sim(embeddings[0], embeddings[2]):.4f}")

except ImportError:
    print("sentence-transformers not installed in this notebook runtime.")
    print("Install with: pip install sentence-transformers")
    print("The model can also be logged from a local machine and deployed to SPCS.")
except Exception as e:
    print(f"Embedding model note: {e}")

# Section B — HuggingFace Pipeline (display-only)
print("\n" + "=" * 70)
print("Option 2: HuggingFace Pipeline (display-only)")
print("=" * 70)
print("""
from snowflake.ml.model.models import huggingface_pipeline
pipeline = huggingface_pipeline.HuggingFacePipelineModel(
    task="feature-extraction",
    model="sentence-transformers/all-mpnet-base-v2",
)
reg.log_model(model=pipeline, model_name="CREATOR_TEXT_EMBEDDER",
    version_name="V3", compute_pool_for_log="GPU_POOL")
""")

# Section C — CustomModel multi-modal (display-only)
print("=" * 70)
print("Option 3: CustomModel — Multi-Modal (display-only)")
print("=" * 70)
print("""
class MultiModalEmbedder(custom_model.CustomModel):
    @custom_model.inference_api
    def embed_text(self, df: pd.DataFrame) -> pd.DataFrame:
        # Returns VECTOR(FLOAT, 768) per text
        ...

    @custom_model.inference_api
    def embed_image(self, df: pd.DataFrame) -> pd.DataFrame:
        # Fetches image URL, returns VECTOR(FLOAT, 768)
        ...
""")

# Section D — VECTOR storage + similarity (display-only)
print("=" * 70)
print("VECTOR Storage + Similarity Search (SQL)")
print("=" * 70)
print("""
-- Store embeddings as VECTOR data type
ALTER TABLE CC_DEMO.RAW.CREATOR_CONTENT
    ADD COLUMN EMBEDDING VECTOR(FLOAT, 384);

-- Cosine similarity search
SELECT a.CREATOR_ID, a.CONTENT_TEXT,
       VECTOR_COSINE_SIMILARITY(a.EMBEDDING, b.EMBEDDING) AS SIMILARITY
FROM CC_DEMO.RAW.CREATOR_CONTENT a
CROSS JOIN CC_DEMO.RAW.CREATOR_CONTENT b
WHERE b.CREATOR_ID = 'CR_00001'
  AND a.CREATOR_ID != 'CR_00001'
ORDER BY SIMILARITY DESC LIMIT 5;
""")

# Section E — Comparison table
print("=" * 70)
print("Embedding Model Options")
print("=" * 70)
options = pd.DataFrame({
    "Approach": ["SentenceTransformer", "HuggingFace Pipeline",
                 "CustomModel", "EMBED_TEXT_768 (Cortex)"],
    "Dimensions": ["384", "768", "Any", "768"],
    "GPU Required": ["No", "Yes (log)", "Optional", "No"],
    "Custom Logic": ["No", "No", "Yes", "No"],
    "Best For": ["Quick start", "Standard HF models",
                 "Multi-modal / custom", "Zero-code built-in"],
})
print(options.to_string(index=False))


# %% [markdown]
# ### Extension 4: Cortex Search — Managed Hybrid Search
#
# Replace self-managed search infrastructure with **Cortex Search** — managed
# hybrid search combining text, vector, and semantic relevance. Three modes:
# managed embeddings, BYO vectors via Multi-Index, or hybrid. Watch for the
# search results from creator content.


# %% --- Cell 28: Cortex Search ---
import json

# Section A — Managed Embeddings (Working Code)
print("=" * 70)
print("Section A: Managed Cortex Search Service")
print("=" * 70)

try:
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
    print("Cortex Search service created: CREATOR_CONTENT_SEARCH")
except Exception as e:
    print(f"Cortex Search note: {e}")
    print("Service may already exist or feature not enabled.")

# Query via SQL SEARCH_PREVIEW
print("\nSearch: 'eco-friendly beauty products'")
search_result = session.sql("""
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'CC_DEMO.RAW.CREATOR_CONTENT_SEARCH',
            '{"query": "eco-friendly beauty products", "columns": ["CREATOR_ID", "CONTENT_TEXT", "CATEGORY"], "limit": 5}'
        )
    ) AS RESULTS
""").collect()[0]["RESULTS"]

results = json.loads(search_result)
for r in results.get("results", []):
    scores = r.get("@scores", {})
    print(f"  {r['CREATOR_ID']} | {r['CATEGORY']:8s} | sim={scores.get('cosine_similarity', 0):.3f} | {r['CONTENT_TEXT'][:60]}")

# Query via Python SDK
print("\nPython SDK query:")
try:
    from snowflake.core import Root
    root = Root(session)
    search_svc = (root.databases["CC_DEMO"].schemas["RAW"]
                  .cortex_search_services["CREATOR_CONTENT_SEARCH"])
    py_results = search_svc.search(
        query="eco-friendly beauty products",
        columns=["CREATOR_ID", "CONTENT_TEXT", "CATEGORY"],
        limit=3,
    )
    for r in py_results.results:
        print(f"  {r['CREATOR_ID']} | {r['CATEGORY']:8s} | {r['CONTENT_TEXT'][:60]}")
except Exception as e:
    print(f"  SDK note: {e}")

# Section B — BYO Vectors / Multi-Index (Display-Only)
print("\n" + "=" * 70)
print("Section B: BYO Vectors — Multi-Index (display-only)")
print("=" * 70)
print("""
-- 1. Table with VECTOR column
CREATE TABLE CC_DEMO.RAW.CREATOR_CONTENT_VECTORS (
    CREATOR_ID VARCHAR(16),  CONTENT_TEXT VARCHAR(2000),
    CATEGORY VARCHAR(32),    EMBEDDING VECTOR(FLOAT, 768),
    PRIMARY KEY (CREATOR_ID)
);

-- 2. Multi-Index Cortex Search — three VECTOR INDEX modes:

-- Mode A: Managed embeddings (Snowflake generates vectors)
CREATE CORTEX SEARCH SERVICE ... ON content_text ...
    EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'

-- Mode B: User-provided vectors (BYO embeddings)
CREATE CORTEX SEARCH SERVICE ... ON content_text ...
    VECTOR INDEX (vector_column => EMBEDDING)

-- Mode C: Hybrid (user vectors + managed query embedding)
CREATE CORTEX SEARCH SERVICE ... ON content_text ...
    VECTOR INDEX (vector_column => EMBEDDING,
                  query_model => 'snowflake-arctic-embed-l-v2.0')

-- 3. Query with scoring weights (text: 30%, vector: 70%)
SELECT * FROM TABLE(
    CC_DEMO.RAW.CREATOR_VECTOR_SEARCH!MULTI_INDEX_QUERY(
        query => 'eco-friendly fashion',
        scoring_config => {'weights': {'texts': 0.3, 'vectors': 0.7}},
        limit => 10
    )
);
""")

# Section C — Cortex Agent integration (Display-Only)
print("=" * 70)
print("Section C: Cortex Agent with Search Tool (display-only)")
print("=" * 70)
print("""
CREATE OR REPLACE CORTEX AGENT CC_DEMO.APPS.CREATOR_ADVISOR
    MODEL = 'claude-3-5-sonnet'
    TOOLS = (
        { 'tool_type': 'cortex_search_tool',
          'tool_spec': {
              'service_name': 'CC_DEMO.RAW.CREATOR_CONTENT_SEARCH',
              'max_results': 5,
              'title_column': 'CREATOR_ID',
              'body_column': 'CONTENT_TEXT'
          }
        }
    );
""")

# Section D — Decision Matrix
print("=" * 70)
print("Decision Matrix: Which Search Path?")
print("=" * 70)
matrix = pd.DataFrame({
    "Goal": ["Quick semantic search", "BYO embeddings", "Hybrid text + vector",
             "Conversational search"],
    "Best Path": ["Managed embeddings", "Multi-Index (user vectors)",
                  "Multi-Index (hybrid)", "Cortex Agent + Search tool"],
    "You Manage": ["Nothing", "Embedding pipeline", "Embedding pipeline",
                   "Agent prompt"],
    "Key Benefit": ["Zero-code", "Full control", "Best relevance",
                    "Natural language UX"],
})
print(matrix.to_string(index=False))
print("\nAll paths are composable — start managed, add BYO vectors later.")


# %% [markdown]
# ### Extension 4b: Live Creator Profiles — Dynamic Table
#
# `CREATOR_PROFILES_LIVE` is a **Dynamic Table** that auto-refreshes every
# 5 minutes by joining static creator data, live engagement features, and
# model scores. The `CREATOR_TIER` column is recomputed on each refresh —
# so tier assignments stay current without any scheduled jobs.

# %% --- Cell 28b: Dynamic Creator Profiles ---
# Create CREATOR_PROFILES_LIVE as a Dynamic Table that auto-refreshes
# by joining creators + engagement features + model scores.
# Tier assignments and quality scores are recomputed on each refresh.

print("Creating CREATOR_PROFILES_LIVE Dynamic Table...")
try:
    session.sql("""
        CREATE OR REPLACE DYNAMIC TABLE CC_DEMO.ML.CREATOR_PROFILES_LIVE
            TARGET_LAG = '10 minutes'
            WAREHOUSE = CC_ML_WH
        AS
            WITH interaction_stats AS (
                SELECT
                    CREATOR_ID,
                    AVG(CASE WHEN CONVERTED THEN 1 ELSE 0 END) AS CONVERSION_RATE,
                    COUNT(DISTINCT BRAND_ID) AS BRAND_COUNT
                FROM CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS
                GROUP BY CREATOR_ID
            ),
            scored AS (
                SELECT
                    e.CREATOR_ID,
                    CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
                        e.SESSIONS_7D, e.AVG_CTR_7D, e.PURCHASES_7D,
                        e.GMV_7D, e.UNIQUE_BRANDS_7D, e.AVG_ENGAGEMENT_7D
                    ):"output_feature_1"::FLOAT AS MATCH_SCORE
                FROM CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES e
            )
            SELECT
                c.CREATOR_ID, c.CREATOR_NAME, c.CATEGORY,
                c.FOLLOWER_COUNT, c.COUNTRY,
                e.SESSIONS_7D, e.AVG_CTR_7D, e.AVG_ENGAGEMENT_7D,
                s.MATCH_SCORE,
                CASE WHEN s.MATCH_SCORE >= 0.50 THEN 'PREMIUM'
                     WHEN s.MATCH_SCORE >= 0.30 THEN 'STANDARD'
                     ELSE 'EMERGING' END AS CREATOR_TIER,
                LEAST(100, GREATEST(0, ROUND(e.AVG_ENGAGEMENT_7D * 100 / 0.15, 1)))
                    AS CONTENT_QUALITY_SCORE,
                CASE WHEN i.CONVERSION_RATE > 0.7 AND i.BRAND_COUNT >= 5 THEN 'POWER_CONVERTER'
                     WHEN i.CONVERSION_RATE > 0.5 AND i.BRAND_COUNT < 5  THEN 'NICHE_SPECIALIST'
                     WHEN i.BRAND_COUNT >= 8                               THEN 'BROAD_REACH'
                     ELSE 'EMERGING_TALENT' END AS BRAND_AFFINITY_CLUSTER
            FROM CC_DEMO.RAW.CREATORS c
            JOIN CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES e ON c.CREATOR_ID = e.CREATOR_ID
            JOIN scored s ON c.CREATOR_ID = s.CREATOR_ID
            LEFT JOIN interaction_stats i ON c.CREATOR_ID = i.CREATOR_ID
    """).collect()
    print("CREATOR_PROFILES_LIVE created — auto-refreshes every 10 minutes.")
    print("New events → new features → new scores → new tier assignments. Zero scheduling.")

    # Show sample
    session.sql("""
        SELECT CREATOR_ID, CREATOR_NAME, CATEGORY, CREATOR_TIER,
               ROUND(MATCH_SCORE, 3) AS MATCH_SCORE,
               CONTENT_QUALITY_SCORE, BRAND_AFFINITY_CLUSTER
        FROM CC_DEMO.ML.CREATOR_PROFILES_LIVE
        ORDER BY MATCH_SCORE DESC
        LIMIT 5
    """).show()
except Exception as e:
    print(f"Dynamic Table note: {e}")
    print("CREATOR_PROFILES_LIVE requires MATCH_PREDICTIONS or model to be deployed.")


# %% [markdown]
# ### Extension 5: Embedding Backfill Pipeline
#
# **Your #1 operational pain point.** When you upgrade an embedding model, you need
# to re-embed millions of rows without downtime. Snowflake's immutable versioning +
# alias switching + GPU batch processing makes this a zero-downtime operation.
# Watch for V1 vs V2 embeddings side by side.


# %% --- Cell 29: Embedding Backfill Pipeline ---

# Section A — Backfill Workflow Overview (Display-Only)
print("=" * 70)
print("Section A: Zero-Downtime Embedding Backfill Pipeline")
print("=" * 70)
print("""
Pipeline Steps:
  1. CREATOR_TEXT_EMBEDDER V1 serving in production (all-MiniLM-L6-v2)
  2. Log new model as V2 in Registry (paraphrase-MiniLM-L6-v2)
  3. run_batch() on GPU pool → re-embed millions of rows
  4. Register new embeddings as Feature View V2
  5. A/B test V1 vs V2 via generate_dataset()
  6. Promote: alias switch V1 → V2 (atomic, zero downtime)
  7. Old V1 stays accessible for rollback

Key insight: immutable versions + alias switching = zero-downtime upgrades.
""")

# Section B — Working Code
print("=" * 70)
print("Section B: Model Versions + Embedding Comparison")
print("=" * 70)

try:
    # B.1 — Show both versions in the registry
    versions_rows = session.sql(
        "SHOW VERSIONS IN MODEL CC_DEMO.ML_REGISTRY.CREATOR_TEXT_EMBEDDER"
    ).collect()
    print("\nModel versions in registry:")
    for v in versions_rows:
        print(f"  {v['name']:4s} | aliases={v['aliases']:30s} | {v['comment']}")
        print(f"         runnable_in={v['runnable_in']}")

    # B.2 — Local comparison: V1 vs V2 embeddings on same content
    # (Models are SPCS-only; we run locally for demo comparison)
    from sentence_transformers import SentenceTransformer
    import numpy as np

    content_df = session.sql(
        "SELECT CREATOR_ID, CONTENT_TEXT FROM CC_DEMO.RAW.CREATOR_CONTENT"
    ).to_pandas()

    print(f"\nBackfill source: {len(content_df)} rows from CREATOR_CONTENT")

    model_v1 = SentenceTransformer("all-MiniLM-L6-v2")
    model_v2 = SentenceTransformer("paraphrase-MiniLM-L6-v2")

    texts = content_df["CONTENT_TEXT"].tolist()
    emb_v1 = model_v1.encode(texts)
    emb_v2 = model_v2.encode(texts)

    print(f"\nV1 embeddings shape: {emb_v1.shape}  (all-MiniLM-L6-v2)")
    print(f"V2 embeddings shape: {emb_v2.shape}  (paraphrase-MiniLM-L6-v2)")

    # Show cosine similarity between V1 and V2 for each row
    from numpy.linalg import norm
    print("\nV1 vs V2 similarity per creator (higher = models agree):")
    for i, row in content_df.iterrows():
        cos_sim = np.dot(emb_v1[i], emb_v2[i]) / (norm(emb_v1[i]) * norm(emb_v2[i]))
        print(f"  {row['CREATOR_ID']} | sim={cos_sim:.4f} | {row['CONTENT_TEXT'][:50]}")

    avg_sim = np.mean([
        np.dot(emb_v1[i], emb_v2[i]) / (norm(emb_v1[i]) * norm(emb_v2[i]))
        for i in range(len(texts))
    ])
    print(f"\nAverage V1↔V2 cosine similarity: {avg_sim:.4f}")
    print("In production, run_batch() distributes across GPU pool.")
except Exception as e:
    print(f"\nNote: Embedding comparison skipped ({e})")
    print("CREATOR_TEXT_EMBEDDER requires sentence-transformers (not available in this runtime).")

# B.3 — run_batch() production pattern (Display-Only)
print("\n--- Production Backfill Pattern (display-only) ---")
print("""
from snowflake.ml.model import OutputSpec, JobSpec

mv_v2 = reg.get_model("CREATOR_TEXT_EMBEDDER").version("V2")
mv_v2.run_batch(
    X=session.table("CC_DEMO.RAW.CREATOR_CONTENT"),
    function_name="ENCODE",
    compute_pool="GPU_POOL",
    output_spec=OutputSpec(
        stage_location="@CC_DEMO.ML.EMBEDDINGS/v2/",
        mode=OVERWRITE
    ),
    job_spec=JobSpec(gpu_requests="1", replicas=4, num_workers=2),
)
""")

# B.4 — Alias switch (Display-Only)
print("--- Zero-Downtime Cutover (display-only) ---")
print("""
-- Promote V2 to production (atomic)
ALTER MODEL CC_DEMO.ML_REGISTRY.CREATOR_TEXT_EMBEDDER
    VERSION V2 SET ALIAS = PRODUCTION;

-- Rollback to V1 if needed (instant)
ALTER MODEL CC_DEMO.ML_REGISTRY.CREATOR_TEXT_EMBEDDER
    VERSION V1 SET ALIAS = PRODUCTION;
""")

# Section C — Feature Store Version Propagation (Display-Only)
print("=" * 70)
print("Section C: Feature Store Version Propagation (display-only)")
print("=" * 70)
print("""
# Register V2 embeddings as Feature View V2
from snowflake.ml.feature_store import FeatureStore, FeatureView

fs = FeatureStore(session, database="CC_DEMO", name="FEATURE_STORE")

# New feature view version with V2 embeddings
embedding_fv_v2 = FeatureView(
    name="CREATOR_EMBEDDINGS",
    entities=[creator_entity],
    feature_df=v2_embedding_df,      # output of run_batch V2
    refresh_freq="60 minutes",
    desc="Creator text embeddings — paraphrase-MiniLM-L6-v2"
)
fs.register_feature_view(embedding_fv_v2, version="V2")

# A/B test: generate datasets from both versions
ds_v1 = fs.generate_dataset("AB_V1", spine_df, [embedding_fv_v1])
ds_v2 = fs.generate_dataset("AB_V2", spine_df, [embedding_fv_v2])
# Compare downstream model accuracy on both
""")

# Section D — Summary Table
print("=" * 70)
print("Section D: Embedding Backfill Decision Matrix")
print("=" * 70)
summary = pd.DataFrame({
    "Step": ["Model upgrade", "Backfill execution", "Version control",
             "Cutover", "A/B testing", "Rollback"],
    "Current Pain": ["Manual retrain + redeploy", "Custom Spark/Airflow job",
                     "Git tags + S3 paths", "Blue/green infra swap",
                     "Shadow pipeline", "Restore from backup"],
    "Snowflake Approach": ["log_model() V2 — 1 line", "run_batch() on GPU pool",
                           "Immutable versions in Registry", "ALTER MODEL SET ALIAS — atomic",
                           "generate_dataset() V1 vs V2", "SET ALIAS back — instant"],
})
print(summary.to_string(index=False))


# %% [markdown]
# ### Extension 6: CDP Profile Enrichment
#
# ML predictions written back to enriched creator profiles — auto-refreshing
# via Dynamic Tables. Every creator gets a **predicted match tier** and
# **brand affinity cluster**. This is the CDP enrichment vision.


# %% --- Cell 30: CDP Profile Enrichment ---

# Section A — Enriched Profile Table (Working Code)
print("=" * 70)
print("Section A: CDP Profile Enrichment — Batch Inference + Enriched Profiles")
print("=" * 70)

# A.1 — Batch inference: score all creators via SQL function
print("\nStep 1: Batch inference on all creators...")
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

# A.2 — Build enriched profile with tiers and clusters
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

# A.3 — Show enriched profiles (top 10)
print("\nTop 10 enriched profiles:")
top_profiles = session.sql("""
    SELECT CREATOR_ID, CREATOR_NAME, CATEGORY, CREATOR_TIER,
           ROUND(MATCH_SCORE, 3) AS MATCH_SCORE,
           CONTENT_QUALITY_SCORE, BRAND_AFFINITY_CLUSTER
    FROM CC_DEMO.ML.CREATOR_PROFILES
    ORDER BY MATCH_SCORE DESC
    LIMIT 10
""").to_pandas()
print(top_profiles.to_string(index=False))

# A.4 — Tier distribution + cluster distribution
print("\nTier distribution:")
tier_dist = session.sql("""
    SELECT CREATOR_TIER AS TIER, COUNT(*) AS CREATORS,
           ROUND(AVG(MATCH_SCORE), 3) AS AVG_SCORE,
           ROUND(AVG(CONTENT_QUALITY_SCORE), 1) AS AVG_QUALITY
    FROM CC_DEMO.ML.CREATOR_PROFILES
    GROUP BY CREATOR_TIER ORDER BY AVG_SCORE DESC
""").to_pandas()
print(tier_dist.to_string(index=False))

print("\nBrand affinity clusters:")
cluster_dist = session.sql("""
    SELECT BRAND_AFFINITY_CLUSTER AS CLUSTER, COUNT(*) AS CREATORS,
           ROUND(AVG(MATCH_SCORE), 3) AS AVG_SCORE,
           ROUND(AVG(CONTENT_QUALITY_SCORE), 1) AS AVG_QUALITY
    FROM CC_DEMO.ML.CREATOR_PROFILES
    GROUP BY BRAND_AFFINITY_CLUSTER ORDER BY CREATORS DESC
""").to_pandas()
print(cluster_dist.to_string(index=False))

# Section B — Dynamic Table Pattern (Display-Only)
print("\n" + "=" * 70)
print("Section B: Auto-Refreshing Profiles via Dynamic Table (display-only)")
print("=" * 70)
print("""
CREATE DYNAMIC TABLE CC_DEMO.ML.CREATOR_PROFILES_LIVE
    TARGET_LAG = '10 minutes'
    WAREHOUSE = CC_ML_WH
AS
    WITH interaction_stats AS (
        SELECT CREATOR_ID,
               AVG(CASE WHEN CONVERTED THEN 1 ELSE 0 END) AS CONVERSION_RATE,
               COUNT(DISTINCT BRAND_ID) AS BRAND_COUNT
        FROM CC_DEMO.RAW.CREATOR_BRAND_INTERACTIONS GROUP BY CREATOR_ID
    )
    SELECT c.CREATOR_ID, c.CREATOR_NAME, c.CATEGORY, ...
           s.MATCH_SCORE, <tier logic>, <cluster logic>
    FROM CC_DEMO.RAW.CREATORS c
    JOIN CC_DEMO.ML.MATCH_PREDICTIONS s ON ...
    LEFT JOIN interaction_stats i ON ...;

-- Auto-refresh, no scheduler, no stale profiles.
-- New events → new features → new predictions → new profiles.
-- All within Snowflake's transactional guarantees.
""")


# %% [markdown]
# ### Model Monitor — Drift Detection on Scored Predictions
#
# Now that `MATCH_PREDICTIONS` exists (created by CDP enrichment above),
# we can create a **Model Monitor** for automated drift detection. The monitor
# compares current predictions against a baseline and computes metrics like
# Population Stability Index (PSI) on every refresh cycle.


# %% --- Cell 30b: Model Monitor Setup + Drift Queries ---
# Create Model Monitor for drift detection
# Note: CREATE MODEL MONITOR requires the model to be in the current schema context
print("Creating Model Monitor for drift detection...")
session.sql("USE SCHEMA CC_DEMO.ML_REGISTRY").collect()
try:
    session.sql("""
        CREATE OR REPLACE MODEL MONITOR CREATOR_MATCH_MONITOR
        WITH
            MODEL = CREATOR_BRAND_MATCH
            VERSION = 'V1'
            FUNCTION = 'PREDICT_PROBA'
            SOURCE = CC_DEMO.ML.MATCH_PREDICTIONS
            TIMESTAMP_COLUMN = SCORED_AT
            PREDICTION_SCORE_COLUMNS = ('MATCH_SCORE')
            ID_COLUMNS = ('CREATOR_ID')
            WAREHOUSE = CC_ML_WH
            REFRESH_INTERVAL = '1 day'
            AGGREGATION_WINDOW = '1 day'
    """).collect()
    print("Model Monitor created: CREATOR_MATCH_MONITOR")
except Exception as e:
    print(f"Model Monitor note: {e}")
    print("Monitor may already exist or require specific account features.")

# Query drift metrics
print("\nDrift metrics (POPULATION_STABILITY_INDEX):")
try:
    drift_df = session.sql("""
        SELECT *
        FROM TABLE(MODEL_MONITOR_DRIFT_METRIC(
            'CC_DEMO.ML_REGISTRY.CREATOR_MATCH_MONITOR', 'POPULATION_STABILITY_INDEX', 'MATCH_SCORE', '1 DAY',
            DATEADD('DAY', -30, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ),
            CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
        ))
        ORDER BY EVENT_TIMESTAMP DESC
        LIMIT 5
    """)
    drift_df.show()
except Exception as e:
    print(f"  Drift query note: {e}")
    print("  Metrics available after monitor's first refresh cycle.")

# Query performance metrics
print("\nPerformance tracking:")
try:
    perf_df = session.sql("""
        SELECT *
        FROM TABLE(MODEL_MONITOR_STAT_METRIC(
            'CC_DEMO.ML_REGISTRY.CREATOR_MATCH_MONITOR', 'COUNT', 'MATCH_SCORE', '1 DAY',
            DATEADD('DAY', -30, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ),
            CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
        ))
        ORDER BY EVENT_TIMESTAMP DESC
        LIMIT 5
    """)
    perf_df.show()
except Exception as e:
    print(f"  Stats query note: {e}")

print("""
Monitor dashboards: Snowsight → AI & ML → Models → CREATOR_BRAND_MATCH → Monitors
Available metric functions:
  • MODEL_MONITOR_DRIFT_METRIC('POPULATION_STABILITY_INDEX')  — feature drift over time
  • MODEL_MONITOR_PERFORMANCE_METRIC(...)                     — accuracy, AUC, F1
  • MODEL_MONITOR_STAT_METRIC('COUNT')                        — prediction volume
""")


# %% [markdown]
# ### Extension 7: OpenSearch Replacement
#
# If you use OpenSearch for embedding storage, keyword search, and online feature
# serving, each of these maps to a native Snowflake capability. The result: one
# platform for warehouse, feature store, and search — fully managed.


# %% --- Cell 31: OpenSearch Replacement Summary ---

# Section C — OpenSearch Replacement Mapping (Display-Only)
print("=" * 70)
print("OpenSearch → Snowflake: Complete Displacement Map")
print("=" * 70)

replacement_map = pd.DataFrame({
    "OpenSearch Function": [
        "Store vectors",
        "Keyword search",
        "Online feature serving",
        "Vector similarity",
        "Bulk retrieval for training",
        "Cluster management",
        "Sync pipeline",
    ],
    "Snowflake Equivalent": [
        "VECTOR(FLOAT, N) data type",
        "Cortex Search (<200ms)",
        "Feature Store Online Config (<30ms)",
        "Cortex Search BYO / VECTOR_COSINE_SIMILARITY",
        "generate_dataset()",
        "Fully managed — zero infra",
        "TARGET_LAG — automatic",
    ],
})
print(replacement_map.to_string(index=False))

print("""
Key takeaway:
  The warehouse IS the feature store IS the search engine.

  No separate cluster to manage. No sync pipeline to maintain.
  No version drift between search index and training data.
  One platform. One governance model. One bill.
""")


# %% [markdown]
# ### Extension 8: Anomaly Detection — Flag Unusual Creator Behavior
#
# Snowflake ML includes **unsupervised anomaly detection** that learns normal
# engagement patterns and flags outliers automatically. This is a teaser —
# the full implementation uses `snowflake.ml.modeling.anomaly_detection` to
# train on `CREATOR_ENGAGEMENT_FEATURES` and surface creators with sudden
# engagement spikes or drops.

# %% --- Cell 32: Anomaly Detection Teaser ---
print("Anomaly Detection — statistical outlier flagging:")

# Simple z-score based anomaly detection on profile features
anomalies = session.sql("""
    WITH stats AS (
        SELECT
            AVG(SESSIONS_7D)         AS mu_sessions,
            STDDEV(SESSIONS_7D)      AS sd_sessions,
            AVG(MATCH_SCORE)         AS mu_score,
            STDDEV(MATCH_SCORE)      AS sd_score
        FROM CC_DEMO.ML.CREATOR_PROFILES
        WHERE SESSIONS_7D IS NOT NULL
    )
    SELECT
        p.CREATOR_ID,
        p.CREATOR_NAME,
        p.CATEGORY,
        p.SESSIONS_7D,
        ROUND((p.SESSIONS_7D - s.mu_sessions) / NULLIF(s.sd_sessions, 0), 2) AS SESSIONS_ZSCORE,
        ROUND(p.MATCH_SCORE, 3) AS MATCH_SCORE,
        ROUND((p.MATCH_SCORE - s.mu_score) / NULLIF(s.sd_score, 0), 2)      AS SCORE_ZSCORE,
        CASE
            WHEN ABS((p.SESSIONS_7D - s.mu_sessions) / NULLIF(s.sd_sessions, 0)) > 2
              OR ABS((p.MATCH_SCORE - s.mu_score) / NULLIF(s.sd_score, 0)) > 2
            THEN 'ANOMALY'
            ELSE 'NORMAL'
        END AS STATUS
    FROM CC_DEMO.ML.CREATOR_PROFILES p
    CROSS JOIN stats s
    WHERE p.SESSIONS_7D IS NOT NULL
    ORDER BY ABS((p.SESSIONS_7D - s.mu_sessions) / NULLIF(s.sd_sessions, 0)) DESC
    LIMIT 10
""")
anomalies.show()

anomaly_count = session.sql("""
    WITH stats AS (
        SELECT AVG(SESSIONS_7D) AS mu, STDDEV(SESSIONS_7D) AS sd
        FROM CC_DEMO.ML.CREATOR_PROFILES
        WHERE SESSIONS_7D IS NOT NULL
    )
    SELECT COUNT(*) AS ANOMALY_COUNT
    FROM CC_DEMO.ML.CREATOR_PROFILES p CROSS JOIN stats s
    WHERE p.SESSIONS_7D IS NOT NULL
      AND ABS((p.SESSIONS_7D - s.mu) / NULLIF(s.sd, 0)) > 2
""").collect()[0]["ANOMALY_COUNT"]
print(f"  {anomaly_count} creators flagged as anomalies (|z| > 2)")

print("""
Next steps for production:
  • Train snowflake.ml.modeling.anomaly_detection on engagement features
  • Schedule as a Snowflake Task for daily anomaly sweeps
  • Alert via notification integration when anomaly count exceeds threshold
  • Combine with ML Observability for model + data drift detection
""")


# %% [markdown]
# # Full Demo Summary
#
# **Core Platform:**
# - Feature Store with managed refresh (2-min lag) and online serving (<30ms)
# - Model Registry with immutable versioning, aliases, RBAC, SHAP explainability
# - Batch inference on warehouse — score all creators in seconds
# - Real-time inference on SPCS — <100ms per request, auto-scaling
# - REST API for external applications — any app, any language, one endpoint
#
# **Extensions:**
# - Multi-endpoint CustomModel — 3 inference APIs, one set of weights
# - External Access Integration — network calls from model containers with governance
# - Custom Embeddings — Sentence Transformers, HuggingFace, CustomModel, VECTOR storage
# - Cortex Search — managed hybrid search replacing self-managed infrastructure
# - Embedding Backfill — zero-downtime model upgrade with GPU batch + alias switch
# - CDP Profile Enrichment — ML-inferred tiers and clusters, auto-refreshing
# - OpenSearch Replacement — every function mapped to native Snowflake capabilities
#
# **Monitoring:**
# - Model Monitor with drift detection (POPULATION_STABILITY_INDEX)
# - Anomaly Detection on creator profiles (z-score flagging)


# %% --- Cell 33: Deploy Streamlit Dashboard ---
print("Deploying Streamlit dashboard to Snowflake...")

# Upload app files to stage
try:
    session.sql("CREATE STAGE IF NOT EXISTS CC_DEMO.APPS.STREAMLIT_STAGE").collect()

    session.file.put(
        "file://app/streamlit_app.py",
        "@CC_DEMO.APPS.STREAMLIT_STAGE",
        auto_compress=False, overwrite=True,
    )
    session.file.put(
        "file://app/environment.yml",
        "@CC_DEMO.APPS.STREAMLIT_STAGE",
        auto_compress=False, overwrite=True,
    )
    print("  Uploaded streamlit_app.py and environment.yml to @CC_DEMO.APPS.STREAMLIT_STAGE")

    session.sql("""
        CREATE OR REPLACE STREAMLIT CC_DEMO.APPS.CREATOR_MATCH_DEMO
            ROOT_LOCATION = '@CC_DEMO.APPS.STREAMLIT_STAGE'
            MAIN_FILE = 'streamlit_app.py'
            QUERY_WAREHOUSE = CC_ML_WH
            TITLE = 'Creator Match ML Demo'
            COMMENT = 'Interactive dashboard for Creator-Brand Match Score demo'
    """).collect()
    print("  Streamlit app created: CC_DEMO.APPS.CREATOR_MATCH_DEMO")
    print("  Open in Snowsight: Streamlit > CREATOR_MATCH_DEMO")
except Exception as e:
    print(f"Streamlit deployment note: {e}")
    print("You can also deploy manually via Snowsight: Streamlit > + Streamlit App")


# %% --- Cell 34: Cleanup / Teardown ---
print("""
=== CLEANUP ===
To tear down all demo objects, run sql/99_teardown.sql in a Snowsight worksheet.
This will drop:
  - SPCS services (CC_MATCH_SERVICE, CC_MATCH_SERVICE_V2)
  - Model Monitor (CREATOR_MATCH_MONITOR)
  - Cortex Search service (CREATOR_CONTENT_SEARCH)
  - Streamlit app and stage
  - Models (CREATOR_BRAND_MATCH, CREATOR_TEXT_EMBEDDER)
  - All tables, Dynamic Tables, and schemas
  - Database CC_DEMO
  - Warehouse CC_ML_WH
  - Compute pool CC_COMPUTE_POOL

Alternatively, run these commands individually:
""")

# Uncomment below to run teardown inline:
# session.sql("DROP SERVICE IF EXISTS CC_DEMO.ML_REGISTRY.CC_MATCH_SERVICE").collect()
# session.sql("DROP SERVICE IF EXISTS CC_DEMO.ML_REGISTRY.CC_MATCH_SERVICE_V2").collect()
# session.sql("DROP MODEL MONITOR IF EXISTS CC_DEMO.ML_REGISTRY.CREATOR_MATCH_MONITOR").collect()
# session.sql("DROP CORTEX SEARCH SERVICE IF EXISTS CC_DEMO.RAW.CREATOR_CONTENT_SEARCH").collect()
# session.sql("DROP STREAMLIT IF EXISTS CC_DEMO.APPS.CREATOR_MATCH_DEMO").collect()
# session.sql("DROP MODEL IF EXISTS CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH").collect()
# session.sql("DROP MODEL IF EXISTS CC_DEMO.ML_REGISTRY.CREATOR_TEXT_EMBEDDER").collect()
# session.sql("DROP DATABASE IF EXISTS CC_DEMO").collect()
# session.sql("DROP WAREHOUSE IF EXISTS CC_ML_WH").collect()
# session.sql("DROP COMPUTE POOL IF EXISTS CC_COMPUTE_POOL").collect()
# print("[TEARDOWN COMPLETE]")
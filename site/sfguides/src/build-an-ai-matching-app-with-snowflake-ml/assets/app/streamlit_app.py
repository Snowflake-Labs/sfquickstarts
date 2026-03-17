
# =============================================================================
# Creator Commerce ML Demo — Streamlit Dashboard
# Live demo companion with 6 pages:
#   1. Feature Store explorer
#   2. Model Registry & metrics
#   3. Inference playground + REST API reference
#   4. CDP Profile Enrichment
#   5. Cortex Search
#   6. Model Monitoring & Drift
# Deploy via: CREATE STREAMLIT ... FROM ... or run locally.
# =============================================================================

import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="Creator Match ML Demo", layout="wide")
st.title("Creator-Brand Match Score — Snowflake ML Demo")
st.caption("Feature Store | Model Registry | Inference | Embeddings | Cortex Search | CDP | Monitoring")

# --- Sidebar: Navigation ---
page = st.sidebar.radio("Navigate", [
    "1. Feature Store",
    "2. Model Registry",
    "3. Inference & API",
    "4. CDP Profiles",
    "5. Cortex Search",
    "6. Model Monitoring",
])

# =========================================================================
# Page 1: Feature Store
# =========================================================================
if page == "1. Feature Store":
    st.header("Feature Store")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Registered Entities")
        try:
            # Feature Store entities are tagged via SNOWML_FEATURE_STORE_OBJECT.
            # Extract entity names from the SNOWML_FEATURE_VIEW_METADATA tag values.
            entities_df = session.sql("""
                SELECT DISTINCT
                    f.value::STRING AS ENTITY_NAME
                FROM (
                    SELECT TAG_VALUE
                    FROM TABLE(
                        CC_DEMO.INFORMATION_SCHEMA.TAG_REFERENCES(
                            'CC_DEMO.FEATURE_STORE.CREATOR_ENGAGEMENT_7D$V1', 'TABLE'
                        )
                    )
                    WHERE TAG_NAME = 'SNOWML_FEATURE_VIEW_METADATA'
                ),
                LATERAL FLATTEN(input => PARSE_JSON(TAG_VALUE):entities) f
            """).to_pandas()
            if len(entities_df) > 0:
                st.dataframe(entities_df, use_container_width=True)
            else:
                st.info("No entities registered yet. Run the demo notebook first.")
        except Exception:
            try:
                obj_df = session.sql("""
                    SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT
                    FROM CC_DEMO.INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = 'FEATURE_STORE'
                      AND TABLE_NAME NOT LIKE 'DEMO_TRAINING%'
                    ORDER BY TABLE_NAME
                """).to_pandas()
                if len(obj_df) > 0:
                    st.dataframe(obj_df, use_container_width=True)
                else:
                    st.info("No entities registered yet. Run the demo notebook first.")
            except Exception:
                st.info("Run the demo notebook first to register entities.")

    with col2:
        st.subheader("Feature Views")
        try:
            session.sql("SHOW DYNAMIC TABLES IN SCHEMA CC_DEMO.FEATURE_STORE").collect()
            fv_df = session.sql("""
                SELECT "name", "target_lag", "refresh_mode", "scheduling_state"
                FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
            """).to_pandas()
            if len(fv_df) > 0:
                st.dataframe(fv_df, use_container_width=True)
            else:
                st.info("No Feature Views registered yet.")
        except Exception:
            st.info("Run the demo notebook first to register feature views.")

    st.subheader("Sample Features: Creator Engagement (7d)")
    try:
        features_df = session.sql("""
            SELECT CREATOR_ID, SESSIONS_7D, AVG_CTR_7D, PURCHASES_7D,
                   GMV_7D, UNIQUE_BRANDS_7D, AVG_ENGAGEMENT_7D
            FROM CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES
            ORDER BY GMV_7D DESC
            LIMIT 20
        """).to_pandas()
        st.dataframe(features_df, use_container_width=True)

        st.subheader("Feature Distributions")
        col_a, col_b = st.columns(2)
        with col_a:
            st.bar_chart(features_df.set_index("CREATOR_ID")["GMV_7D"])
        with col_b:
            st.bar_chart(features_df.set_index("CREATOR_ID")["AVG_ENGAGEMENT_7D"])
    except Exception:
        st.info("Run the setup SQL and demo notebook first to populate engagement features.")

# =========================================================================
# Page 2: Model Registry
# =========================================================================
elif page == "2. Model Registry":
    st.header("Model Registry")

    st.subheader("Registered Models")
    try:
        session.sql("SHOW MODELS IN SCHEMA CC_DEMO.ML_REGISTRY").collect()
        models_df = session.sql("""
            SELECT "name", "model_type", "comment", "default_version_name", "created_on"
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        """).to_pandas()
        if len(models_df) > 0:
            st.dataframe(models_df, use_container_width=True)
        else:
            st.info("No models registered yet.")
    except Exception as e:
        st.warning(f"Could not list models: {e}")
        st.info("Run the demo notebook to log a model.")

    try:
        session.sql("SHOW MODELS IN SCHEMA CC_DEMO.ML_REGISTRY").collect()
        available_models = session.sql("""
            SELECT "name" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())) ORDER BY "name"
        """).to_pandas()["name"].tolist()
    except Exception:
        available_models = ["CREATOR_BRAND_MATCH"]

    model_name = st.selectbox(
        "Select model to inspect",
        available_models if available_models else ["CREATOR_BRAND_MATCH"]
    )

    st.subheader(f"Versions — {model_name}")
    try:
        session.sql(f"""
            SHOW VERSIONS IN MODEL CC_DEMO.ML_REGISTRY.{model_name}
        """).collect()
        versions_df = session.sql("""
            SELECT "name", "aliases", "comment", "is_default_version",
                   "functions", "created_on"
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        """).to_pandas()
        if len(versions_df) > 0:
            st.dataframe(versions_df, use_container_width=True)
        else:
            st.info(f"No versions found for {model_name}.")
    except Exception:
        st.info(f"Model {model_name} not yet registered.")

    if model_name == "CREATOR_BRAND_MATCH":
        st.subheader("Model Metrics")
        try:
            session.sql("SHOW VERSIONS IN MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH").collect()
            metrics_df = session.sql("""
                SELECT "name", "metadata" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
                WHERE "metadata" IS NOT NULL
            """).to_pandas()
            if len(metrics_df) > 0:
                import json
                meta = json.loads(metrics_df.iloc[0]["metadata"]) if metrics_df.iloc[0]["metadata"] else {}
                metrics = meta.get("metrics", {})
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("AUC-ROC", f"{metrics.get('auc_roc', 'N/A')}")
                with metric_col2:
                    st.metric("F1 Score", f"{metrics.get('f1_score', 'N/A')}")
            else:
                st.info("No metrics logged yet.")
        except Exception as e:
            st.warning(f"Could not load metrics: {e}")
            st.info("Log a model with metrics first.")

# =========================================================================
# Page 3: Inference & API
# =========================================================================
elif page == "3. Inference & API":
    st.header("Real-Time Inference & REST API")

    st.subheader("Deployed Services")
    try:
        session.sql("SHOW SERVICES IN SCHEMA CC_DEMO.ML_REGISTRY").collect()
        services_df = session.sql("""
            SELECT "name", "status", "compute_pool", "current_instances",
                   "target_instances", "min_instances", "max_instances"
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
            WHERE "is_job" = 'false'
        """).to_pandas()
        if len(services_df) > 0:
            st.dataframe(services_df, use_container_width=True)
        else:
            st.info("No services deployed yet. Run the SPCS deployment cell in the notebook.")
    except Exception as e:
        st.warning(f"Could not list services: {e}")
        st.info("Deploy a service first using `mv.create_service()`.")

    st.subheader("Try Batch Prediction (Warehouse)")
    st.markdown("Enter creator features to get a match score prediction:")

    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            sessions_val = st.number_input("Sessions (7d)", value=25, min_value=0)
            ctr = st.number_input("Avg CTR (7d)", value=0.05, format="%.4f")
        with c2:
            purchases = st.number_input("Purchases (7d)", value=3, min_value=0)
            gmv = st.number_input("GMV (7d)", value=150.0, format="%.2f")
        with c3:
            brands = st.number_input("Unique Brands (7d)", value=5, min_value=0)
            engagement = st.number_input("Avg Engagement (7d)", value=0.70, format="%.4f")

        submitted = st.form_submit_button("Predict Match Score")

    if submitted:
        try:
            result_df = session.sql(f"""
                SELECT CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH!PREDICT_PROBA(
                    {sessions_val}, {ctr}, {purchases}, {gmv}, {brands}, {engagement}
                ):"output_feature_1"::FLOAT AS MATCH_PROBABILITY
            """).to_pandas()
            prob = result_df.iloc[0, 0]
            st.success(f"Match Probability: **{prob:.2%}**")
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            st.info("Ensure the model is logged and the default version is set.")

    st.divider()
    st.subheader("REST API Reference")
    st.code("""
# After deploying with mv.create_service(ingress_enabled=True):

curl -X POST "<endpoint_url>/predict" \\
  -H 'Authorization: Snowflake Token="<pat>"' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "dataframe_split": {
      "index": [0],
      "columns": ["SESSIONS_7D","AVG_CTR_7D","PURCHASES_7D",
                   "GMV_7D","UNIQUE_BRANDS_7D","AVG_ENGAGEMENT_7D"],
      "data": [[25, 0.05, 3, 150.0, 5, 0.7]]
    }
  }'
    """, language="bash")

# =========================================================================
# Page 4: CDP Profile Enrichment
# =========================================================================
elif page == "4. CDP Profiles":
    st.header("CDP Profile Enrichment")
    st.caption("ML-inferred attributes on creator profiles — CREATOR_TIER, CONTENT_QUALITY_SCORE, BRAND_AFFINITY_CLUSTER")

    try:
        profiles_df = session.sql("""
            SELECT CREATOR_ID, CREATOR_NAME, CATEGORY, FOLLOWER_COUNT,
                   MATCH_SCORE, CREATOR_TIER,
                   CONTENT_QUALITY_SCORE, BRAND_AFFINITY_CLUSTER
            FROM CC_DEMO.ML.CREATOR_PROFILES
            ORDER BY MATCH_SCORE DESC
            LIMIT 50
        """).to_pandas()

        # Tier distribution
        st.subheader("Creator Tier Distribution")
        tier_df = session.sql("""
            SELECT CREATOR_TIER, COUNT(*) AS CREATOR_COUNT
            FROM CC_DEMO.ML.CREATOR_PROFILES
            GROUP BY CREATOR_TIER
            ORDER BY CREATOR_COUNT DESC
        """).to_pandas()

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(tier_df.set_index("CREATOR_TIER"))
        with col2:
            for _, row in tier_df.iterrows():
                st.metric(row["CREATOR_TIER"], f"{row['CREATOR_COUNT']:,} creators")

        # Cluster distribution
        st.subheader("Brand Affinity Clusters")
        cluster_df = session.sql("""
            SELECT BRAND_AFFINITY_CLUSTER, COUNT(*) AS CREATOR_COUNT,
                   ROUND(AVG(MATCH_SCORE), 3) AS AVG_MATCH_SCORE,
                   ROUND(AVG(CONTENT_QUALITY_SCORE), 1) AS AVG_QUALITY
            FROM CC_DEMO.ML.CREATOR_PROFILES
            GROUP BY BRAND_AFFINITY_CLUSTER
            ORDER BY AVG_MATCH_SCORE DESC
        """).to_pandas()
        st.dataframe(cluster_df, use_container_width=True)

        # Full table
        st.subheader("Top 50 Enriched Profiles")
        st.dataframe(profiles_df, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not load profiles: {e}")
        st.info("Run the CDP Profile Enrichment cell in the demo notebook first.")

# =========================================================================
# Page 5: Cortex Search
# =========================================================================
elif page == "5. Cortex Search":
    st.header("Cortex Search — Hybrid Search Over Creator Content")
    st.caption("Vector + keyword + reranking — managed, <200ms, zero infra")

    st.subheader("Search Creator Content")
    query = st.text_input("Enter a search query", value="sustainable fashion influencer")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        platform_filter = st.selectbox("Filter by platform", ["all", "instagram", "tiktok", "youtube", "app"])
    with col_filter2:
        category_filter = st.selectbox("Filter by category", ["all", "fashion", "beauty", "home", "fitness", "lifestyle", "food", "travel", "tech"])

    if st.button("Search"):
        try:
            from snowflake.core import Root
            root = Root(session)
            search_svc = (root
                .databases["CC_DEMO"]
                .schemas["RAW"]
                .cortex_search_services["CREATOR_CONTENT_SEARCH"]
            )

            # Build filter — use @and for multiple conditions
            filter_conditions = []
            if platform_filter != "all":
                filter_conditions.append({"@eq": {"PLATFORM": platform_filter}})
            if category_filter != "all":
                filter_conditions.append({"@eq": {"CATEGORY": category_filter}})

            kwargs = {
                "query": query,
                "columns": ["CONTENT_TEXT", "CREATOR_ID", "CATEGORY", "PLATFORM"],
                "limit": 10,
            }
            if len(filter_conditions) == 1:
                kwargs["filter"] = filter_conditions[0]
            elif len(filter_conditions) > 1:
                kwargs["filter"] = {"@and": filter_conditions}

            results = search_svc.search(**kwargs)

            import json
            results_list = json.loads(results.to_json()).get("results", [])
            if results_list:
                import pandas as pd
                results_df = pd.DataFrame(results_list)
                st.dataframe(results_df, use_container_width=True)
            else:
                st.warning("No results found.")

        except Exception as e:
            st.error(f"Search failed: {e}")
            st.info("Run the Cortex Search cell in the demo notebook to create the search service first.")

    st.divider()
    st.subheader("Content Table")
    try:
        content_df = session.sql("""
            SELECT * FROM CC_DEMO.RAW.CREATOR_CONTENT ORDER BY CREATOR_ID LIMIT 500
        """).to_pandas()
        st.dataframe(content_df, use_container_width=True)
    except Exception:
        st.info("Run the setup SQL to create the CREATOR_CONTENT table.")

# =========================================================================
# Page 6: Model Monitoring & Drift
# =========================================================================
elif page == "6. Model Monitoring":
    st.header("Model Monitoring & Drift Detection")
    st.caption("Track prediction drift, volume, and performance via Snowflake Model Monitor")

    st.subheader("Model Monitor Status")
    try:
        session.sql("SHOW MODEL MONITORS IN SCHEMA CC_DEMO.ML_REGISTRY").collect()
        monitors_df = session.sql("""
            SELECT "name", "monitor_state", "refresh_interval",
                   "aggregation_window", "model_task", "warehouse"
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        """).to_pandas()
        if len(monitors_df) > 0:
            st.dataframe(monitors_df, use_container_width=True)
        else:
            st.info("No model monitors created yet. Run the monitoring cell in the demo notebook.")
    except Exception as e:
        st.warning(f"Could not list monitors: {e}")
        st.info("Model monitoring requires running the CREATE MODEL MONITOR cell in the notebook.")

    st.subheader("Drift Metrics (Population Stability Index)")
    try:
        drift_df = session.sql("""
            SELECT *
            FROM TABLE(MODEL_MONITOR_DRIFT_METRIC(
                'CC_DEMO.ML_REGISTRY.CREATOR_MATCH_MONITOR',
                'POPULATION_STABILITY_INDEX', 'MATCH_SCORE', '1 DAY',
                DATEADD('DAY', -30, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ),
                CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
            ))
            ORDER BY EVENT_TIMESTAMP DESC
            LIMIT 10
        """).to_pandas()
        if len(drift_df) > 0:
            st.dataframe(drift_df, use_container_width=True)
            st.line_chart(drift_df.set_index("EVENT_TIMESTAMP")["METRIC_VALUE"])
        else:
            st.info("No drift data available yet. Metrics populate after the monitor's first refresh.")
    except Exception as e:
        st.info(f"Drift metrics not yet available: {e}")

    st.subheader("Prediction Volume")
    try:
        vol_df = session.sql("""
            SELECT *
            FROM TABLE(MODEL_MONITOR_STAT_METRIC(
                'CC_DEMO.ML_REGISTRY.CREATOR_MATCH_MONITOR',
                'COUNT', 'MATCH_SCORE', '1 DAY',
                DATEADD('DAY', -30, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ),
                CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
            ))
            ORDER BY EVENT_TIMESTAMP DESC
            LIMIT 10
        """).to_pandas()
        if len(vol_df) > 0:
            st.dataframe(vol_df, use_container_width=True)
        else:
            st.info("No volume data yet.")
    except Exception as e:
        st.info(f"Volume metrics not yet available: {e}")

    st.subheader("Version Comparison")
    try:
        session.sql("SHOW VERSIONS IN MODEL CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH").collect()
        version_cmp = session.sql("""
            SELECT
                "name"          AS VERSION,
                "aliases"       AS ALIASES,
                PARSE_JSON("metadata"):metrics:auc_roc::FLOAT   AS AUC_ROC,
                PARSE_JSON("metadata"):metrics:f1_score::FLOAT   AS F1_SCORE,
                ARRAY_SIZE(PARSE_JSON("inference_services"))      AS ACTIVE_SERVICES,
                "created_on"    AS CREATED_ON
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
            ORDER BY "created_on"
        """).to_pandas()
        st.dataframe(version_cmp, use_container_width=True)
    except Exception as e:
        st.info(f"Could not load version comparison: {e}")

    st.markdown("""
    **Monitoring dashboards** are also available in Snowsight:
    Navigate to **AI & ML > Models > CREATOR_BRAND_MATCH > Monitors**
    """)

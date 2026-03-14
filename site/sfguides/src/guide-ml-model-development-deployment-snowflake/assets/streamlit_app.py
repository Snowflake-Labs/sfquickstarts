
# =============================================================================
# Creator Commerce ML Demo — Streamlit Dashboard
# Live demo companion with 5 pages:
#   1. Feature Store explorer
#   2. Model Registry & metrics
#   3. Inference playground + REST API reference
#   4. CDP Profile Enrichment
#   5. Cortex Search
# Deploy via: CREATE STREAMLIT ... FROM ... or run locally.
# =============================================================================

import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="Creator Match ML Demo", layout="wide")
st.title("🎯 Creator-Brand Match Score — Snowflake ML Demo")
st.caption("Feature Store → Model Registry → Inference → Embeddings → Cortex Search → CDP")

# --- Sidebar: Navigation ---
page = st.sidebar.radio("Navigate", [
    "1. Feature Store",
    "2. Model Registry",
    "3. Inference & API",
    "4. CDP Profiles",
    "5. Cortex Search",
])

# =========================================================================
# Page 1: Feature Store
# =========================================================================
if page == "1. Feature Store":
    st.header("📊 Feature Store")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Entities")
        entities_df = session.sql("""
            SELECT TAG_NAME, TAG_VALUE
            FROM TABLE(CC_DEMO.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
                'CC_DEMO.FEATURE_STORE', 'SCHEMA'
            ))
            WHERE TAG_NAME ILIKE '%ENTITY%'
            LIMIT 20
        """)
        try:
            st.dataframe(entities_df.to_pandas(), use_container_width=True)
        except Exception:
            st.info("Run the demo notebook first to register entities.")

    with col2:
        st.subheader("Feature Views")
        try:
            fv_df = session.sql("""
                SHOW DYNAMIC TABLES IN SCHEMA CC_DEMO.FEATURE_STORE
            """).to_pandas()
            if len(fv_df) > 0:
                st.dataframe(
                    fv_df[["name", "target_lag", "refresh_mode", "scheduling_state"]],
                    use_container_width=True
                )
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
        st.info("Run 00_setup.sql and data generation first.")

# =========================================================================
# Page 2: Model Registry
# =========================================================================
elif page == "2. Model Registry":
    st.header("📦 Model Registry")

    st.subheader("Registered Models")
    try:
        models_df = session.sql("SHOW MODELS IN SCHEMA CC_DEMO.ML_REGISTRY").to_pandas()
        if len(models_df) > 0:
            st.dataframe(
                models_df[["name", "comment", "default_version_name", "created_on"]],
                use_container_width=True
            )
        else:
            st.info("No models registered yet.")
    except Exception:
        st.info("Run the demo notebook to log a model.")

    model_name = st.selectbox(
        "Select model to inspect",
        ["CREATOR_BRAND_MATCH", "CREATOR_TEXT_EMBEDDER"]
    )

    st.subheader(f"Versions — {model_name}")
    try:
        versions_df = session.sql(f"""
            SHOW VERSIONS IN MODEL CC_DEMO.ML_REGISTRY.{model_name}
        """).to_pandas()
        if len(versions_df) > 0:
            st.dataframe(versions_df, use_container_width=True)
    except Exception:
        st.info(f"Model {model_name} not yet registered.")

    if model_name == "CREATOR_BRAND_MATCH":
        st.subheader("Model Metrics")
        try:
            from snowflake.ml.registry import Registry
            reg = Registry(session=session, database_name="CC_DEMO", schema_name="ML_REGISTRY")
            mv = reg.get_model("CREATOR_BRAND_MATCH").default
            metrics = mv.show_metrics()

            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("AUC-ROC", f"{metrics.get('auc_roc', 'N/A')}")
            with metric_col2:
                st.metric("F1 Score", f"{metrics.get('f1_score', 'N/A')}")
        except Exception:
            st.info("Log a model first to see metrics.")

# =========================================================================
# Page 3: Inference & API
# =========================================================================
elif page == "3. Inference & API":
    st.header("⚡ Real-Time Inference & REST API")

    st.subheader("Deployed Services")
    try:
        services_df = session.sql("""
            SHOW SERVICES IN SCHEMA CC_DEMO.ML_REGISTRY
        """).to_pandas()
        if len(services_df) > 0:
            st.dataframe(services_df, use_container_width=True)
        else:
            st.info("No services deployed yet. Run Phase 10 in CoCo.")
    except Exception:
        st.info("Deploy a service first using `mv.create_service()`.")

    st.subheader("Try Batch Prediction (Warehouse)")
    st.markdown("Enter creator features to get a match score prediction:")

    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            sessions = st.number_input("Sessions (7d)", value=25, min_value=0)
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
            from snowflake.ml.registry import Registry
            import pandas as pd
            reg = Registry(session=session, database_name="CC_DEMO", schema_name="ML_REGISTRY")
            mv = reg.get_model("CREATOR_BRAND_MATCH").default
            input_df = pd.DataFrame([{
                "SESSIONS_7D": sessions, "AVG_CTR_7D": ctr, "PURCHASES_7D": purchases,
                "GMV_7D": gmv, "UNIQUE_BRANDS_7D": brands, "AVG_ENGAGEMENT_7D": engagement,
            }])
            result = mv.run(session.create_dataframe(input_df), function_name="predict_proba")
            prob = result.to_pandas().iloc[0, 0]
            st.success(f"🎯 Match Probability: **{prob:.2%}**")
            if prob > 0.7:
                st.balloons()
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            st.info("Ensure the model is logged and the PRODUCTION alias is set.")

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
    st.header("👤 CDP Profile Enrichment")
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

    except Exception:
        st.info("Run Phase 9 (CDP Profile Enrichment) in the demo notebook first.")

# =========================================================================
# Page 5: Cortex Search
# =========================================================================
elif page == "5. Cortex Search":
    st.header("🔍 Cortex Search — Hybrid Search Over Creator Content")
    st.caption("Vector + keyword + reranking — managed, <200ms, zero infra")

    st.subheader("Search Creator Content")
    query = st.text_input("Enter a search query", value="sustainable fashion influencer")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        platform_filter = st.selectbox("Filter by platform", ["all", "instagram", "tiktok", "youtube", "app"])
    with col_filter2:
        category_filter = st.selectbox("Filter by category", ["all", "fashion", "beauty", "home", "fitness", "food", "travel", "tech"])

    if st.button("Search"):
        try:
            from snowflake.core import Root
            root = Root(session)
            search_svc = (root
                .databases["CC_DEMO"]
                .schemas["RAW"]
                .cortex_search_services["CREATOR_CONTENT_SEARCH"]
            )

            filter_dict = {}
            if platform_filter != "all":
                filter_dict["@eq"] = {"platform": platform_filter}
            if category_filter != "all":
                eq = filter_dict.get("@eq", {})
                eq["category"] = category_filter
                filter_dict["@eq"] = eq

            kwargs = {
                "query": query,
                "columns": ["content_text", "creator_id", "category", "platform"],
                "limit": 10,
            }
            if filter_dict:
                kwargs["filter"] = filter_dict

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
            st.info("Run Phase 7 (Cortex Search) in the demo notebook to create the search service first.")

    st.divider()
    st.subheader("Content Table")
    try:
        content_df = session.sql("""
            SELECT * FROM CC_DEMO.RAW.CREATOR_CONTENT ORDER BY CREATOR_ID
        """).to_pandas()
        st.dataframe(content_df, use_container_width=True)
    except Exception:
        st.info("Run 00_setup.sql to create the CREATOR_CONTENT table.")

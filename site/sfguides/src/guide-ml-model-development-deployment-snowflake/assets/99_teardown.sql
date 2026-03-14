
-- =============================================================================
-- Creator Commerce ML Demo — Teardown
-- Drops ALL demo objects. Run only when demo is fully complete.
-- =============================================================================

-- 1. Drop SPCS inference service
DROP SERVICE IF EXISTS CC_DEMO.ML_REGISTRY.CC_MATCH_SERVICE;
SELECT '[PASS] Inference service dropped' AS STATUS;

-- 2. Drop Cortex Search services
DROP CORTEX SEARCH SERVICE IF EXISTS CC_DEMO.ML.CREATOR_CONTENT_SEARCH;
SELECT '[PASS] Cortex Search service dropped' AS STATUS;

-- 3. Drop Streamlit app and stage
DROP STREAMLIT IF EXISTS CC_DEMO.APPS.CREATOR_MATCH_DEMO;
DROP STAGE IF EXISTS CC_DEMO.APPS.STREAMLIT_STAGE;
SELECT '[PASS] Streamlit app and stage dropped' AS STATUS;

-- 4. Drop models from registry
DROP MODEL IF EXISTS CC_DEMO.ML_REGISTRY.CREATOR_BRAND_MATCH;
DROP MODEL IF EXISTS CC_DEMO.ML_REGISTRY.CREATOR_TEXT_EMBEDDER;
SELECT '[PASS] Models dropped' AS STATUS;

-- 5. Drop enrichment tables and Dynamic Tables
DROP DYNAMIC TABLE IF EXISTS CC_DEMO.ML.CREATOR_PROFILES_LIVE;
DROP TABLE IF EXISTS CC_DEMO.ML.CREATOR_PROFILES;
DROP TABLE IF EXISTS CC_DEMO.ML.MATCH_PREDICTIONS;
DROP DYNAMIC TABLE IF EXISTS CC_DEMO.ML.CREATOR_ENGAGEMENT_FEATURES;
SELECT '[PASS] ML tables dropped' AS STATUS;

-- 6. Drop Feature Store schema (entities + feature views are schema objects)
DROP SCHEMA IF EXISTS CC_DEMO.FEATURE_STORE CASCADE;
SELECT '[PASS] Feature Store schema dropped' AS STATUS;

-- 7. Drop remaining schemas
DROP SCHEMA IF EXISTS CC_DEMO.ML_REGISTRY CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.ML CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.RAW CASCADE;
DROP SCHEMA IF EXISTS CC_DEMO.APPS CASCADE;
SELECT '[PASS] All schemas dropped' AS STATUS;

-- 8. Drop database
DROP DATABASE IF EXISTS CC_DEMO;
SELECT '[PASS] Database CC_DEMO dropped' AS STATUS;

-- 9. Drop warehouse
DROP WAREHOUSE IF EXISTS CC_ML_WH;
SELECT '[PASS] Warehouse dropped' AS STATUS;

-- 10. Drop compute pool
DROP COMPUTE POOL IF EXISTS CC_COMPUTE_POOL;
SELECT '[PASS] Compute pool dropped' AS STATUS;

-- [TEARDOWN COMPLETE]
SELECT '[TEARDOWN COMPLETE] All demo objects removed' AS STATUS;

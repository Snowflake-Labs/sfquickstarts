{{
    config(
        materialized='table',
        schema='ML_FEATURES'
    )
}}

/*
    ML File Embeddings - ColBERT-style Token Embeddings via Snowflake Cortex
    
    This model generates embeddings using SNOWFLAKE.CORTEX.EMBED_TEXT_768
    which produces 768-dimensional vectors similar to ColBERT's approach:
    - Dense token-level representations
    - Late interaction scoring for retrieval
    - Suitable for semantic search and RAG pipelines
    
    ColPali extension: For multimodal docs, use EMBED_IMAGE functions
*/

WITH source_files AS (
    -- Sample file content for embedding generation
    -- In production, this would come from your staging layer
    SELECT 
        'security_analysis.py' AS file_path,
        'python' AS file_type,
        'def analyze_vulnerability(code): 
            """Analyze code for SQL injection, XSS, and other OWASP vulnerabilities."""
            patterns = ["SELECT.*FROM.*WHERE", "eval(", "innerHTML"]
            return [p for p in patterns if p in code]' AS file_content,
        CURRENT_TIMESTAMP() AS created_at
    UNION ALL
    SELECT 
        'data_pipeline.sql' AS file_path,
        'sql' AS file_type,
        'CREATE OR REPLACE TABLE processed_data AS
         SELECT customer_id, SUM(amount) as total_spend
         FROM raw_transactions
         GROUP BY customer_id
         HAVING total_spend > 1000' AS file_content,
        CURRENT_TIMESTAMP() AS created_at
    UNION ALL
    SELECT 
        'ml_model.py' AS file_path,
        'python' AS file_type,
        'import snowflake.ml as ml
         from snowflake.ml.modeling.xgboost import XGBClassifier
         
         model = XGBClassifier(n_estimators=100, max_depth=6)
         model.fit(X_train, y_train)
         predictions = model.predict(X_test)' AS file_content,
        CURRENT_TIMESTAMP() AS created_at
    UNION ALL
    SELECT 
        'api_handler.js' AS file_path,
        'javascript' AS file_type,
        'async function fetchData(endpoint) {
            const response = await fetch(endpoint);
            const data = await response.json();
            return data.results.map(r => r.value);
         }' AS file_content,
        CURRENT_TIMESTAMP() AS created_at
),

-- Generate ColBERT-style embeddings via Cortex
embeddings AS (
    SELECT
        file_path,
        file_type,
        file_content,
        created_at,
        
        -- Primary embedding using Cortex EMBED_TEXT_768 (ColBERT-compatible 768-dim)
        SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', file_content) AS content_embedding,
        
        -- Embedding model metadata
        'e5-base-v2' AS embedding_model,
        768 AS vector_length
    FROM source_files
),

-- DSPy-style metadata generation using Cortex COMPLETE
dspy_metadata AS (
    SELECT
        e.*,
        
        -- DSPy signature: file_content -> summary, category, keywords
        SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-7b',
            'Summarize this code file in one sentence: ' || e.file_content
        ) AS dspy_summary,
        
        -- Verifier category classification
        CASE 
            WHEN CONTAINS(LOWER(e.file_content), 'vulnerability') 
                 OR CONTAINS(LOWER(e.file_content), 'injection')
                 OR CONTAINS(LOWER(e.file_content), 'xss') THEN 'SECURITY'
            WHEN CONTAINS(LOWER(e.file_content), 'select') 
                 OR CONTAINS(LOWER(e.file_content), 'create table') THEN 'DATA_PIPELINE'
            WHEN CONTAINS(LOWER(e.file_content), 'model') 
                 OR CONTAINS(LOWER(e.file_content), 'train')
                 OR CONTAINS(LOWER(e.file_content), 'predict') THEN 'ML_MODEL'
            WHEN CONTAINS(LOWER(e.file_content), 'fetch') 
                 OR CONTAINS(LOWER(e.file_content), 'api')
                 OR CONTAINS(LOWER(e.file_content), 'async') THEN 'API_HANDLER'
            ELSE 'GENERAL'
        END AS verifier_category
        
    FROM embeddings e
)

SELECT
    file_path,
    file_type,
    file_content,
    content_embedding,
    embedding_model,
    vector_length,
    dspy_summary,
    verifier_category,
    created_at,
    
    -- Similarity search helper: cosine distance threshold
    0.8 AS similarity_threshold,
    
    -- ColBERT late interaction flag
    TRUE AS supports_late_interaction

FROM dspy_metadata

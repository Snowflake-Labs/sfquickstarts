{{
    config(
        materialized='table',
        schema='MARTS'
    )
}}

/*
    File Inventory Mart
    
    Business-oriented view of file inventory with:
    - Business value categorization
    - Processing recommendations
    - Data quality scoring
*/

WITH source_files AS (
    SELECT 
        'security_analysis.py' AS file_path,
        2.5 AS file_size_mb,
        'python' AS file_type,
        DATEADD(day, -5, CURRENT_TIMESTAMP()) AS last_modified,
        150 AS line_count
    UNION ALL
    SELECT 
        'data_pipeline.sql' AS file_path,
        0.8 AS file_size_mb,
        'sql' AS file_type,
        DATEADD(day, -2, CURRENT_TIMESTAMP()) AS last_modified,
        45 AS line_count
    UNION ALL
    SELECT 
        'ml_model.py' AS file_path,
        5.2 AS file_size_mb,
        'python' AS file_type,
        DATEADD(day, -1, CURRENT_TIMESTAMP()) AS last_modified,
        320 AS line_count
    UNION ALL
    SELECT 
        'config.json' AS file_path,
        0.01 AS file_size_mb,
        'json' AS file_type,
        DATEADD(day, -30, CURRENT_TIMESTAMP()) AS last_modified,
        12 AS line_count
    UNION ALL
    SELECT 
        'README.md' AS file_path,
        0.05 AS file_size_mb,
        'markdown' AS file_type,
        DATEADD(day, -60, CURRENT_TIMESTAMP()) AS last_modified,
        80 AS line_count
),

categorized AS (
    SELECT
        file_path,
        file_size_mb,
        file_type,
        last_modified,
        line_count,
        
        -- Business value categorization
        CASE
            WHEN file_type IN ('python', 'sql') AND line_count > 100 THEN 'HIGH'
            WHEN file_type IN ('python', 'sql', 'javascript') THEN 'MEDIUM'
            WHEN file_type IN ('json', 'yaml', 'toml') THEN 'LOW'
            ELSE 'MINIMAL'
        END AS business_value,
        
        -- Processing recommendation based on recency and size
        CASE
            WHEN DATEDIFF(day, last_modified, CURRENT_TIMESTAMP()) <= 7 
                 AND file_size_mb > 1 THEN 'IMMEDIATE'
            WHEN DATEDIFF(day, last_modified, CURRENT_TIMESTAMP()) <= 30 THEN 'SCHEDULED'
            ELSE 'BATCH'
        END AS processing_recommendation,
        
        -- Data quality scoring
        CASE
            WHEN line_count > 50 AND file_size_mb > 0.1 THEN 'EXCELLENT'
            WHEN line_count > 20 THEN 'GOOD'
            WHEN line_count > 5 THEN 'FAIR'
            ELSE 'POOR'
        END AS data_quality_score
        
    FROM source_files
)

SELECT
    file_path,
    file_size_mb,
    file_type,
    last_modified,
    line_count,
    business_value,
    processing_recommendation,
    data_quality_score,
    CURRENT_TIMESTAMP() AS processed_at

FROM categorized

/*
 * Copyright 2026 Snowflake Inc.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*******************************************************************************
 * PHASE 7: Load Unstructured Data
 * 
 * This script loads unstructured data from Python-generated JSON files
 * 
 * NOTE: Before running this script, ensure you have run the Python generators:
 *   cd python/data_generators
 *   python3 generate_maintenance_logs.py
 *   python3 generate_technical_manuals.py  
 *   python3 generate_visual_inspections.py
 *   python3 load_unstructured_full.py
 *
 * The load_unstructured_full.py script generates load_unstructured_data_full.sql
 * which contains all INSERT statements.
 * 
 * This SQL script is a placeholder that reminds users to run the Python loader.
 *******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA UNSTRUCTURED;

-- ============================================================================
-- IMPORTANT: Data Loading Instructions
-- ============================================================================

SELECT '⚠️  UNSTRUCTURED DATA LOADING' AS NOTICE,
       'Run: cd python/data_generators && python3 load_unstructured_full.py' AS STEP_1,
       'Then: snow sql -c <connection> -f load_unstructured_data_full.sql' AS STEP_2;

-- ============================================================================
-- Create Cortex Search Services
-- ============================================================================

-- Document Search Service (searches all maintenance logs and manuals)
CREATE OR REPLACE CORTEX SEARCH SERVICE DOCUMENT_SEARCH_SERVICE
ON DOCUMENT_TEXT
ATTRIBUTES DOCUMENT_ID, ASSET_ID, DOCUMENT_DATE
WAREHOUSE = GRID_RELIABILITY_WH
TARGET_LAG = '1 minute'
AS (
    SELECT 
        DOCUMENT_ID,
        ASSET_ID,
        DOCUMENT_DATE,
        DOCUMENT_TEXT
    FROM MAINTENANCE_LOG_DOCUMENTS
    UNION ALL
    SELECT 
        MANUAL_ID AS DOCUMENT_ID,
        NULL AS ASSET_ID,
        PUBLICATION_DATE AS DOCUMENT_DATE,
        DOCUMENT_TEXT
    FROM TECHNICAL_MANUALS
);

-- Maintenance Log Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE MAINTENANCE_LOG_SEARCH
ON DOCUMENT_TEXT
ATTRIBUTES DOCUMENT_ID, ASSET_ID, MAINTENANCE_TYPE, SEVERITY_LEVEL
WAREHOUSE = GRID_RELIABILITY_WH
TARGET_LAG = '1 minute'
AS (
    SELECT 
        DOCUMENT_ID,
        ASSET_ID,
        MAINTENANCE_TYPE,
        SEVERITY_LEVEL,
        DOCUMENT_TEXT
    FROM MAINTENANCE_LOG_DOCUMENTS
);

-- Technical Manual Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE TECHNICAL_MANUAL_SEARCH
ON DOCUMENT_TEXT
ATTRIBUTES MANUAL_ID, MANUFACTURER, MODEL, EQUIPMENT_TYPE
WAREHOUSE = GRID_RELIABILITY_WH
TARGET_LAG = '1 minute'
AS (
    SELECT 
        MANUAL_ID,
        MANUFACTURER,
        MODEL,
        EQUIPMENT_TYPE,
        DOCUMENT_TEXT
    FROM TECHNICAL_MANUALS
);

-- Grant permissions on Cortex Search Services  
GRANT USAGE ON CORTEX SEARCH SERVICE DOCUMENT_SEARCH_SERVICE TO ROLE GRID_OPERATOR;
GRANT USAGE ON CORTEX SEARCH SERVICE DOCUMENT_SEARCH_SERVICE TO ROLE GRID_ANALYST;
GRANT USAGE ON CORTEX SEARCH SERVICE MAINTENANCE_LOG_SEARCH TO ROLE GRID_OPERATOR;
GRANT USAGE ON CORTEX SEARCH SERVICE MAINTENANCE_LOG_SEARCH TO ROLE GRID_ANALYST;
GRANT USAGE ON CORTEX SEARCH SERVICE TECHNICAL_MANUAL_SEARCH TO ROLE GRID_OPERATOR;
GRANT USAGE ON CORTEX SEARCH SERVICE TECHNICAL_MANUAL_SEARCH TO ROLE GRID_ANALYST;

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 
    'MAINTENANCE_LOG_DOCUMENTS' AS TABLE_NAME, 
    COUNT(*) AS ROW_COUNT,
    COUNT(DISTINCT ASSET_ID) AS UNIQUE_ASSETS
FROM MAINTENANCE_LOG_DOCUMENTS
UNION ALL
SELECT 'TECHNICAL_MANUALS', COUNT(*), COUNT(DISTINCT MANUFACTURER) FROM TECHNICAL_MANUALS
UNION ALL
SELECT 'VISUAL_INSPECTIONS', COUNT(*), COUNT(DISTINCT ASSET_ID) FROM VISUAL_INSPECTIONS
UNION ALL
SELECT 'CV_DETECTIONS', COUNT(*), COUNT(DISTINCT ASSET_ID) FROM CV_DETECTIONS
ORDER BY TABLE_NAME;

SELECT CASE 
    WHEN (SELECT COUNT(*) FROM MAINTENANCE_LOG_DOCUMENTS) > 0 
    THEN '✅ Unstructured data loaded successfully!'
    ELSE '⚠️  No unstructured data found. Run Python data generators first.'
END AS STATUS;

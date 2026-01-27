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
 * AI-DRIVEN GRID RELIABILITY & PREDICTIVE MAINTENANCE
 * Unstructured Data Schema Setup
 * 
 * Purpose: Create infrastructure for unstructured data integration:
 *          1. Maintenance logs & inspection reports (PDFs)
 *          2. Visual inspection data (photos, videos, LiDAR)
 *          3. Technical manuals & specifications (PDFs)
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-18
 * Version: 1.0
 ******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;

-- =============================================================================
-- SECTION 1: CREATE UNSTRUCTURED SCHEMA
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS UNSTRUCTURED
    COMMENT = 'Schema for unstructured data: documents, images, videos';

USE SCHEMA UNSTRUCTURED;

-- =============================================================================
-- SECTION 2: CREATE STAGES FOR DOCUMENT STORAGE
-- =============================================================================

-- Stage for maintenance logs and inspection reports
CREATE OR REPLACE STAGE MAINTENANCE_DOCS_STAGE
    COMMENT = 'Storage for maintenance logs, inspection reports, and field notes (PDFs, docs, etc.)'
    DIRECTORY = (ENABLE = TRUE);

-- Stage for technical manuals and specifications
CREATE OR REPLACE STAGE TECHNICAL_MANUALS_STAGE
    COMMENT = 'Storage for equipment manuals, procedures, and technical specs (PDFs, docs, etc.)'
    DIRECTORY = (ENABLE = TRUE);

-- Stage for visual inspection data
CREATE OR REPLACE STAGE VISUAL_INSPECTION_STAGE
    COMMENT = 'Storage for inspection photos, videos, thermal images, LiDAR'
    DIRECTORY = (ENABLE = TRUE);

-- =============================================================================
-- SECTION 3: MAINTENANCE LOGS METADATA TABLE
-- =============================================================================

CREATE OR REPLACE TABLE MAINTENANCE_LOG_DOCUMENTS (
    DOCUMENT_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    DOCUMENT_TYPE VARCHAR(50), -- 'INSPECTION_REPORT', 'WORK_ORDER', 'FAILURE_REPORT', 'PREVENTIVE_MAINTENANCE'
    DOCUMENT_DATE DATE NOT NULL,
    TECHNICIAN_NAME VARCHAR(100),
    TECHNICIAN_ID VARCHAR(50),
    
    -- File metadata
    FILE_PATH VARCHAR(500) NOT NULL,
    FILE_SIZE_BYTES NUMBER(12),
    FILE_FORMAT VARCHAR(20), -- 'PDF', 'DOCX', 'TXT'
    UPLOAD_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Extracted structured data
    MAINTENANCE_TYPE VARCHAR(50), -- From RAW.MAINTENANCE_HISTORY
    DURATION_HOURS NUMBER(6,2),
    COST_USD NUMBER(12,2),
    FAILURE_OCCURRED BOOLEAN,
    
    -- Text content (extracted from PDF)
    DOCUMENT_TEXT VARCHAR(16777216), -- Full text extraction
    SUMMARY VARCHAR(5000), -- AI-generated summary
    
    -- NLP-extracted features
    ROOT_CAUSE_KEYWORDS ARRAY, -- Extracted failure indicators
    SEVERITY_LEVEL VARCHAR(20), -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    RECOMMENDED_ACTIONS ARRAY,
    PARTS_MENTIONED ARRAY,
    
    -- Search and classification
    EMBEDDING VECTOR(FLOAT, 768), -- For semantic search
    SENTIMENT_SCORE NUMBER(5,4), -- -1 to 1 (negative to positive tone)
    
    -- Audit
    PROCESSED_BY_CORTEX BOOLEAN DEFAULT FALSE,
    LAST_PROCESSED_TIMESTAMP TIMESTAMP_NTZ,
    
    FOREIGN KEY (ASSET_ID) REFERENCES RAW.ASSET_MASTER(ASSET_ID)
);

-- Note: Snowflake regular tables don't support indexes.
-- Use clustering keys or search optimization service for query performance.

-- =============================================================================
-- SECTION 4: TECHNICAL MANUALS METADATA TABLE
-- =============================================================================

CREATE OR REPLACE TABLE TECHNICAL_MANUALS (
    MANUAL_ID VARCHAR(50) PRIMARY KEY,
    MANUAL_TYPE VARCHAR(50), -- 'OPERATION_MANUAL', 'MAINTENANCE_GUIDE', 'TROUBLESHOOTING', 'SPECIFICATIONS'
    EQUIPMENT_TYPE VARCHAR(50), -- 'TRANSFORMER', 'CIRCUIT_BREAKER', 'RELAY'
    MANUFACTURER VARCHAR(100),
    MODEL VARCHAR(100),
    VERSION VARCHAR(20),
    PUBLICATION_DATE DATE,
    
    -- File metadata
    FILE_PATH VARCHAR(500) NOT NULL,
    FILE_SIZE_BYTES NUMBER(12),
    PAGE_COUNT NUMBER(6),
    UPLOAD_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Content
    DOCUMENT_TEXT VARCHAR(16777216),
    TABLE_OF_CONTENTS ARRAY,
    KEY_SPECIFICATIONS OBJECT, -- JSON object with specs
    
    -- Search
    EMBEDDING VECTOR(FLOAT, 768),
    
    -- Applicable assets
    APPLICABLE_TO_ASSETS ARRAY, -- List of ASSET_IDs using this equipment
    
    -- Audit
    LAST_UPDATED TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- SECTION 5: VISUAL INSPECTION DATA TABLES
-- =============================================================================

-- Main visual inspection metadata
CREATE OR REPLACE TABLE VISUAL_INSPECTIONS (
    INSPECTION_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    INSPECTION_DATE DATE NOT NULL,
    INSPECTOR_NAME VARCHAR(100),
    INSPECTOR_ID VARCHAR(50),
    
    -- Inspection method
    INSPECTION_METHOD VARCHAR(50), -- 'DRONE', 'HANDHELD_CAMERA', 'THERMAL', 'LIDAR', 'VIDEO'
    WEATHER_CONDITIONS VARCHAR(100),
    
    -- File metadata
    FILE_PATH VARCHAR(500) NOT NULL,
    FILE_TYPE VARCHAR(20), -- 'JPG', 'PNG', 'MP4', 'LAS' (LiDAR)
    FILE_SIZE_BYTES NUMBER(12),
    UPLOAD_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Image/Video properties
    RESOLUTION VARCHAR(20), -- '1920x1080', '4K'
    GPS_LATITUDE NUMBER(10,7),
    GPS_LONGITUDE NUMBER(10,7),
    
    -- CV Processing flags
    CV_PROCESSED BOOLEAN DEFAULT FALSE,
    CV_PROCESSING_TIMESTAMP TIMESTAMP_NTZ,
    
    FOREIGN KEY (ASSET_ID) REFERENCES RAW.ASSET_MASTER(ASSET_ID)
);

-- Computer Vision detection results
CREATE OR REPLACE TABLE CV_DETECTIONS (
    DETECTION_ID VARCHAR(50) PRIMARY KEY,
    INSPECTION_ID VARCHAR(50) NOT NULL,
    ASSET_ID VARCHAR(50) NOT NULL,
    
    -- Detection details
    DETECTION_TYPE VARCHAR(50), -- 'CORROSION', 'CRACK', 'LEAK', 'VEGETATION', 'HOTSPOT', 'STRUCTURAL_DAMAGE'
    CONFIDENCE_SCORE NUMBER(5,4), -- 0.0 to 1.0
    BOUNDING_BOX OBJECT, -- {x, y, width, height}
    
    -- Severity assessment
    SEVERITY_LEVEL VARCHAR(20), -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    REQUIRES_IMMEDIATE_ACTION BOOLEAN,
    
    -- Additional context
    DETECTED_AT_COMPONENT VARCHAR(100), -- 'BUSHING', 'TANK', 'RADIATOR', 'INSULATOR'
    DESCRIPTION VARCHAR(1000),
    
    -- AI Model info
    MODEL_NAME VARCHAR(100), -- 'yolov8_transformer_v2', 'thermal_anomaly_detector_v1'
    MODEL_VERSION VARCHAR(20),
    DETECTION_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    FOREIGN KEY (INSPECTION_ID) REFERENCES VISUAL_INSPECTIONS(INSPECTION_ID),
    FOREIGN KEY (ASSET_ID) REFERENCES RAW.ASSET_MASTER(ASSET_ID)
);

-- =============================================================================
-- SECTION 6: NLP FEATURE EXTRACTION VIEW
-- =============================================================================

-- View combining structured and unstructured data for ML
CREATE OR REPLACE VIEW VW_ENRICHED_ASSET_FEATURES AS
SELECT 
    a.ASSET_ID,
    a.ASSET_TYPE,
    a.MANUFACTURER,
    a.MODEL,
    DATEDIFF(day, a.INSTALL_DATE, CURRENT_DATE()) / 365.25 AS AGE_YEARS,
    a.CRITICALITY_SCORE,
    
    -- Maintenance history (structured)
    COUNT(DISTINCT m.MAINTENANCE_ID) as TOTAL_MAINTENANCE_COUNT,
    SUM(m.COST_USD) as TOTAL_MAINTENANCE_COST,
    
    -- Maintenance logs (unstructured - text features)
    COUNT(DISTINCT ml.DOCUMENT_ID) as INSPECTION_REPORT_COUNT,
    SUM(CASE WHEN ml.FAILURE_OCCURRED THEN 1 ELSE 0 END) as DOCUMENTED_FAILURE_COUNT,
    AVG(ml.SENTIMENT_SCORE) as AVG_INSPECTION_SENTIMENT,
    ARRAY_AGG(DISTINCT ml.ROOT_CAUSE_KEYWORDS) as ALL_ROOT_CAUSES,
    MAX(ml.DOCUMENT_DATE) as LAST_INSPECTION_DATE,
    DATEDIFF(day, MAX(ml.DOCUMENT_DATE), CURRENT_DATE()) as DAYS_SINCE_LAST_INSPECTION,
    
    -- Visual inspections (computer vision features)
    COUNT(DISTINCT vi.INSPECTION_ID) as VISUAL_INSPECTION_COUNT,
    COUNT(DISTINCT cv.DETECTION_ID) as TOTAL_CV_DETECTIONS,
    SUM(CASE WHEN cv.SEVERITY_LEVEL = 'CRITICAL' THEN 1 ELSE 0 END) as CRITICAL_VISUAL_ISSUES,
    SUM(CASE WHEN cv.SEVERITY_LEVEL = 'HIGH' THEN 1 ELSE 0 END) as HIGH_VISUAL_ISSUES,
    SUM(CASE WHEN cv.DETECTION_TYPE = 'CORROSION' THEN 1 ELSE 0 END) as CORROSION_DETECTIONS,
    SUM(CASE WHEN cv.DETECTION_TYPE = 'LEAK' THEN 1 ELSE 0 END) as LEAK_DETECTIONS,
    AVG(cv.CONFIDENCE_SCORE) as AVG_CV_CONFIDENCE,
    MAX(CASE WHEN cv.REQUIRES_IMMEDIATE_ACTION THEN 1 ELSE 0 END) as HAS_URGENT_VISUAL_ISSUE,
    
    -- Latest sensor data
    sr.OIL_TEMPERATURE_C,
    sr.LOAD_CURRENT_A,
    sr.VIBRATION_MM_S
    
FROM RAW.ASSET_MASTER a
LEFT JOIN RAW.MAINTENANCE_HISTORY m ON a.ASSET_ID = m.ASSET_ID
LEFT JOIN MAINTENANCE_LOG_DOCUMENTS ml ON a.ASSET_ID = ml.ASSET_ID
LEFT JOIN VISUAL_INSPECTIONS vi ON a.ASSET_ID = vi.ASSET_ID
LEFT JOIN CV_DETECTIONS cv ON a.ASSET_ID = cv.ASSET_ID
LEFT JOIN (
    SELECT ASSET_ID, 
           OIL_TEMPERATURE_C, 
           LOAD_CURRENT_A, 
           VIBRATION_MM_S,
           ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY READING_TIMESTAMP DESC) as rn
    FROM RAW.SENSOR_READINGS
) sr ON a.ASSET_ID = sr.ASSET_ID AND sr.rn = 1
WHERE a.STATUS = 'ACTIVE'
GROUP BY 
    a.ASSET_ID, a.ASSET_TYPE, a.MANUFACTURER, a.MODEL, a.INSTALL_DATE,
    a.CRITICALITY_SCORE, sr.OIL_TEMPERATURE_C, sr.LOAD_CURRENT_A, sr.VIBRATION_MM_S;

-- =============================================================================
-- SECTION 7: DOCUMENT SEARCH OPTIMIZATION TABLE
-- =============================================================================

-- Optimized table for Cortex Search
CREATE OR REPLACE TABLE DOCUMENT_SEARCH_INDEX AS
SELECT 
    DOCUMENT_ID as ID,
    'MAINTENANCE_LOG' as DOCUMENT_TYPE,
    ASSET_ID,
    DOCUMENT_DATE,
    TECHNICIAN_NAME,
    CONCAT_WS(' | ',
        'Asset: ' || ASSET_ID,
        'Type: ' || MAINTENANCE_TYPE,
        'Date: ' || DOCUMENT_DATE::VARCHAR,
        'Technician: ' || TECHNICIAN_NAME,
        'Summary: ' || SUMMARY,
        'Root Causes: ' || ARRAY_TO_STRING(ROOT_CAUSE_KEYWORDS, ', ')
    ) as SEARCH_TEXT,
    DOCUMENT_TEXT as FULL_TEXT,
    SEVERITY_LEVEL,
    FILE_PATH
FROM MAINTENANCE_LOG_DOCUMENTS
UNION ALL
SELECT 
    MANUAL_ID as ID,
    'TECHNICAL_MANUAL' as DOCUMENT_TYPE,
    NULL as ASSET_ID,
    PUBLICATION_DATE as DOCUMENT_DATE,
    MANUFACTURER as TECHNICIAN_NAME,
    CONCAT_WS(' | ',
        'Manufacturer: ' || MANUFACTURER,
        'Model: ' || MODEL,
        'Type: ' || MANUAL_TYPE,
        'Equipment: ' || EQUIPMENT_TYPE
    ) as SEARCH_TEXT,
    DOCUMENT_TEXT as FULL_TEXT,
    NULL as SEVERITY_LEVEL,
    FILE_PATH
FROM TECHNICAL_MANUALS;

-- =============================================================================
-- SECTION 8: GRANT PERMISSIONS
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- Grant schema usage
GRANT USAGE ON SCHEMA UNSTRUCTURED TO ROLE GRID_ANALYST;
GRANT USAGE ON SCHEMA UNSTRUCTURED TO ROLE GRID_DATA_ENGINEER;
GRANT USAGE ON SCHEMA UNSTRUCTURED TO ROLE GRID_ML_ENGINEER;

-- Grant stage access
GRANT READ, WRITE ON STAGE MAINTENANCE_DOCS_STAGE TO ROLE GRID_DATA_ENGINEER;
GRANT READ, WRITE ON STAGE TECHNICAL_MANUALS_STAGE TO ROLE GRID_DATA_ENGINEER;
GRANT READ, WRITE ON STAGE VISUAL_INSPECTION_STAGE TO ROLE GRID_DATA_ENGINEER;

GRANT READ ON STAGE MAINTENANCE_DOCS_STAGE TO ROLE GRID_ANALYST;
GRANT READ ON STAGE TECHNICAL_MANUALS_STAGE TO ROLE GRID_ANALYST;

-- Grant table access
GRANT SELECT ON ALL TABLES IN SCHEMA UNSTRUCTURED TO ROLE GRID_ANALYST;
GRANT SELECT ON ALL VIEWS IN SCHEMA UNSTRUCTURED TO ROLE GRID_ANALYST;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA UNSTRUCTURED TO ROLE GRID_DATA_ENGINEER;
GRANT SELECT ON ALL VIEWS IN SCHEMA UNSTRUCTURED TO ROLE GRID_DATA_ENGINEER;

GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA UNSTRUCTURED TO ROLE GRID_ML_ENGINEER;
GRANT SELECT ON ALL VIEWS IN SCHEMA UNSTRUCTURED TO ROLE GRID_ML_ENGINEER;

-- =============================================================================
-- SECTION 9: SUMMARY
-- =============================================================================

SELECT 'Unstructured data schema created successfully!' as STATUS;
SELECT '3 stages created: MAINTENANCE_DOCS, TECHNICAL_MANUALS, VISUAL_INSPECTION' as STAGES;
SELECT '6 tables created for metadata and CV detections' as TABLES;
SELECT '2 views created for enriched features and document search' as VIEWS;

-- Check created objects
SHOW STAGES IN SCHEMA UNSTRUCTURED;
SHOW TABLES IN SCHEMA UNSTRUCTURED;
SHOW VIEWS IN SCHEMA UNSTRUCTURED;


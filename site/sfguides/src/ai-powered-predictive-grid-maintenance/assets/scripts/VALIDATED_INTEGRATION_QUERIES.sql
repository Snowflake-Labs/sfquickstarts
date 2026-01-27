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

-- ============================================================
-- VALIDATED INTEGRATION QUERIES
-- Using ACTUAL column names from your Snowflake tables
-- ============================================================
-- Run these in Snowsight to validate unstructured data integration
-- ============================================================

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;

-- ============================================================
-- QUERY 1: Verify All Data Loaded
-- ============================================================
-- Check record counts for all unstructured tables
SELECT 'Maintenance Logs' AS TABLE_NAME, COUNT(*) AS RECORD_COUNT 
FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS
UNION ALL
SELECT 'Technical Manuals', COUNT(*) 
FROM UNSTRUCTURED.TECHNICAL_MANUALS
UNION ALL
SELECT 'Visual Inspections', COUNT(*) 
FROM UNSTRUCTURED.VISUAL_INSPECTIONS
UNION ALL
SELECT 'CV Detections', COUNT(*) 
FROM UNSTRUCTURED.CV_DETECTIONS;

-- Expected Results:
-- Maintenance Logs: 80
-- Technical Manuals: 15
-- Visual Inspections: 150
-- CV Detections: 281


-- ============================================================
-- QUERY 2: High-Risk Assets with Maintenance History
-- ============================================================
-- Join ML predictions with maintenance logs
-- Shows assets with critical issues documented in both systems

SELECT 
    a.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION_NAME,
    a.ASSET_TYPE,
    
    -- From ML Predictions
    mp.FAILURE_PROBABILITY,
    mp.PREDICTED_RUL_DAYS,
    mp.ALERT_LEVEL AS RISK_CATEGORY,
    
    -- From Maintenance Logs (unstructured)
    m.DOCUMENT_DATE AS LAST_MAINTENANCE_DOC,
    m.DOCUMENT_TEXT AS FINDING,
    m.SEVERITY_LEVEL AS MAINT_SEVERITY,
    m.TECHNICIAN_NAME

FROM RAW.ASSET_MASTER a
JOIN ML.MODEL_PREDICTIONS mp 
    ON a.ASSET_ID = mp.ASSET_ID
JOIN UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m 
    ON a.ASSET_ID = m.ASSET_ID

WHERE mp.ALERT_LEVEL IN ('HIGH', 'CRITICAL')
  AND m.SEVERITY_LEVEL IN ('HIGH', 'CRITICAL')
  
ORDER BY mp.FAILURE_PROBABILITY DESC
LIMIT 20;


-- ============================================================
-- QUERY 3: Sensor Alerts + CV Detections
-- ============================================================
-- Combine real-time sensor data with computer vision detections
-- Shows assets with both thermal issues AND visual defects

SELECT 
    a.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION,
    a.ASSET_TYPE,
    
    -- Latest sensor reading
    sr.READING_TIMESTAMP,
    sr.OIL_TEMPERATURE_C,
    sr.LOAD_CURRENT_A,
    sr.VIBRATION_MM_S,
    
    -- Visual inspection details
    vi.INSPECTION_DATE,
    vi.INSPECTION_METHOD,
    
    -- CV Detection details (unstructured)
    cv.DETECTION_TYPE,
    cv.SEVERITY_LEVEL AS CV_SEVERITY,
    cv.CONFIDENCE_SCORE,
    cv.DETECTED_AT_COMPONENT,
    cv.REQUIRES_IMMEDIATE_ACTION,
    cv.DESCRIPTION AS DETECTION_DESCRIPTION

FROM RAW.ASSET_MASTER a
JOIN RAW.SENSOR_READINGS sr 
    ON a.ASSET_ID = sr.ASSET_ID
JOIN UNSTRUCTURED.VISUAL_INSPECTIONS vi 
    ON a.ASSET_ID = vi.ASSET_ID
JOIN UNSTRUCTURED.CV_DETECTIONS cv 
    ON vi.INSPECTION_ID = cv.INSPECTION_ID

WHERE sr.OIL_TEMPERATURE_C > 80
  AND cv.REQUIRES_IMMEDIATE_ACTION = TRUE
  AND sr.READING_TIMESTAMP >= DATEADD(day, -7, CURRENT_TIMESTAMP())
  
ORDER BY sr.OIL_TEMPERATURE_C DESC, cv.CONFIDENCE_SCORE DESC
LIMIT 20;


-- ============================================================
-- QUERY 4: Comprehensive Asset Health Dashboard
-- ============================================================
-- Single view combining ALL data sources
-- Perfect for Streamlit dashboard or executive reporting

SELECT 
    a.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION,
    a.ASSET_TYPE,
    a.MANUFACTURER,
    a.INSTALL_DATE,
    
    -- Sensor data (latest reading)
    (SELECT MAX(READING_TIMESTAMP) 
     FROM RAW.SENSOR_READINGS sr 
     WHERE sr.ASSET_ID = a.ASSET_ID) AS LAST_SENSOR_READING,
    
    (SELECT OIL_TEMPERATURE_C 
     FROM RAW.SENSOR_READINGS sr 
     WHERE sr.ASSET_ID = a.ASSET_ID 
     ORDER BY READING_TIMESTAMP DESC 
     LIMIT 1) AS CURRENT_OIL_TEMP,
    
    -- ML predictions
    (SELECT FAILURE_PROBABILITY 
     FROM ML.MODEL_PREDICTIONS mp 
     WHERE mp.ASSET_ID = a.ASSET_ID 
     LIMIT 1) AS FAILURE_PROB,
    
    (SELECT ALERT_LEVEL 
     FROM ML.MODEL_PREDICTIONS mp 
     WHERE mp.ASSET_ID = a.ASSET_ID 
     LIMIT 1) AS RISK_LEVEL,
    
    -- Unstructured: Maintenance logs
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m 
     WHERE m.ASSET_ID = a.ASSET_ID) AS TOTAL_MAINTENANCE_LOGS,
    
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m 
     WHERE m.ASSET_ID = a.ASSET_ID 
       AND m.SEVERITY_LEVEL IN ('HIGH', 'CRITICAL')) AS CRITICAL_MAINTENANCE_EVENTS,
    
    -- Unstructured: Visual inspections
    (SELECT MAX(INSPECTION_DATE) 
     FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi 
     WHERE vi.ASSET_ID = a.ASSET_ID) AS LAST_VISUAL_INSPECTION,
    
    (SELECT COUNT(DISTINCT vi.INSPECTION_ID) 
     FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi 
     WHERE vi.ASSET_ID = a.ASSET_ID) AS TOTAL_INSPECTIONS,
    
    -- Unstructured: CV detections
    (SELECT COUNT(cv.DETECTION_ID) 
     FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi
     JOIN UNSTRUCTURED.CV_DETECTIONS cv ON vi.INSPECTION_ID = cv.INSPECTION_ID
     WHERE vi.ASSET_ID = a.ASSET_ID) AS TOTAL_CV_DETECTIONS,
    
    (SELECT COUNT(cv.DETECTION_ID) 
     FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi
     JOIN UNSTRUCTURED.CV_DETECTIONS cv ON vi.INSPECTION_ID = cv.INSPECTION_ID
     WHERE vi.ASSET_ID = a.ASSET_ID 
       AND cv.SEVERITY_LEVEL = 'CRITICAL'
       AND cv.REQUIRES_IMMEDIATE_ACTION = TRUE) AS URGENT_CV_DETECTIONS

FROM RAW.ASSET_MASTER a
WHERE a.STATUS = 'ACTIVE'
ORDER BY URGENT_CV_DETECTIONS DESC, CRITICAL_MAINTENANCE_EVENTS DESC
LIMIT 30;


-- ============================================================
-- QUERY 5: Search Maintenance Logs by Text Content
-- ============================================================
-- Find maintenance logs mentioning specific issues
-- (This works NOW without Cortex Search - just uses LIKE)

SELECT 
    m.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION,
    m.DOCUMENT_DATE,
    m.TECHNICIAN_NAME,
    m.DOCUMENT_TEXT AS FINDING,
    m.SEVERITY_LEVEL,
    m.MAINTENANCE_TYPE
    
FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m
JOIN RAW.ASSET_MASTER a ON m.ASSET_ID = a.ASSET_ID

WHERE LOWER(m.DOCUMENT_TEXT) LIKE '%oil%leak%'
   OR LOWER(m.DOCUMENT_TEXT) LIKE '%overheating%'
   OR LOWER(m.DOCUMENT_TEXT) LIKE '%corrosion%'
   
ORDER BY m.DOCUMENT_DATE DESC
LIMIT 20;


-- ============================================================
-- QUERY 6: CV Detection Summary by Type & Severity
-- ============================================================
-- Understand what types of defects are being detected

SELECT 
    cv.DETECTION_TYPE,
    cv.SEVERITY_LEVEL,
    COUNT(*) AS DETECTION_COUNT,
    ROUND(AVG(cv.CONFIDENCE_SCORE), 3) AS AVG_CONFIDENCE,
    SUM(CASE WHEN cv.REQUIRES_IMMEDIATE_ACTION THEN 1 ELSE 0 END) AS URGENT_COUNT,
    COUNT(DISTINCT cv.ASSET_ID) AS AFFECTED_ASSETS
    
FROM UNSTRUCTURED.CV_DETECTIONS cv
GROUP BY cv.DETECTION_TYPE, cv.SEVERITY_LEVEL
ORDER BY DETECTION_COUNT DESC;


-- ============================================================
-- QUERY 7: Assets Requiring Immediate Action
-- ============================================================
-- Multi-source risk assessment
-- Shows assets flagged by ML predictions, maintenance logs, OR CV detections

SELECT DISTINCT
    a.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION,
    a.ASSET_TYPE,
    a.CRITICALITY_SCORE,
    a.CUSTOMERS_AFFECTED,
    
    -- Risk indicators from different sources
    mp.ALERT_LEVEL AS ML_RISK,
    mp.FAILURE_PROBABILITY,
    
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m 
     WHERE m.ASSET_ID = a.ASSET_ID 
       AND m.SEVERITY_LEVEL = 'CRITICAL'
       AND m.DOCUMENT_DATE >= DATEADD(month, -6, CURRENT_TIMESTAMP())
    ) AS RECENT_CRITICAL_MAINT,
    
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi
     JOIN UNSTRUCTURED.CV_DETECTIONS cv ON vi.INSPECTION_ID = cv.INSPECTION_ID
     WHERE vi.ASSET_ID = a.ASSET_ID 
       AND cv.REQUIRES_IMMEDIATE_ACTION = TRUE
    ) AS URGENT_CV_DETECTIONS_COUNT

FROM RAW.ASSET_MASTER a
LEFT JOIN ML.MODEL_PREDICTIONS mp ON a.ASSET_ID = mp.ASSET_ID

WHERE 
    -- High ML risk
    (mp.ALERT_LEVEL IN ('HIGH', 'CRITICAL'))
    OR
    -- Recent critical maintenance
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m 
     WHERE m.ASSET_ID = a.ASSET_ID 
       AND m.SEVERITY_LEVEL = 'CRITICAL'
       AND m.DOCUMENT_DATE >= DATEADD(month, -6, CURRENT_TIMESTAMP())) > 0
    OR
    -- Urgent CV detections
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi
     JOIN UNSTRUCTURED.CV_DETECTIONS cv ON vi.INSPECTION_ID = cv.INSPECTION_ID
     WHERE vi.ASSET_ID = a.ASSET_ID 
       AND cv.REQUIRES_IMMEDIATE_ACTION = TRUE) > 0

ORDER BY 
    a.CRITICALITY_SCORE DESC,
    mp.FAILURE_PROBABILITY DESC NULLS LAST,
    a.CUSTOMERS_AFFECTED DESC
LIMIT 50;


-- ============================================================
-- QUERY 8: Technical Manual Lookup
-- ============================================================
-- Find relevant technical documentation for assets

SELECT 
    tm.MANUAL_ID,
    tm.EQUIPMENT_TYPE,
    tm.MANUFACTURER,
    tm.MODEL,
    tm.MANUAL_TYPE,
    tm.VERSION,
    tm.PAGE_COUNT,
    tm.FILE_PATH,
    
    -- Count how many assets use this manual
    (SELECT COUNT(DISTINCT a.ASSET_ID)
     FROM RAW.ASSET_MASTER a
     WHERE a.ASSET_TYPE = tm.EQUIPMENT_TYPE
       AND a.MANUFACTURER = tm.MANUFACTURER) AS APPLICABLE_ASSETS

FROM UNSTRUCTURED.TECHNICAL_MANUALS tm
ORDER BY tm.EQUIPMENT_TYPE, tm.MANUAL_TYPE;


-- ============================================================
-- QUERY 9: Recent Visual Inspection Activity
-- ============================================================
-- Monitor inspection coverage and findings

SELECT 
    vi.INSPECTION_DATE,
    vi.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION,
    a.ASSET_TYPE,
    vi.INSPECTION_METHOD,
    vi.INSPECTOR_NAME,
    
    -- Count detections for this inspection
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.CV_DETECTIONS cv 
     WHERE cv.INSPECTION_ID = vi.INSPECTION_ID) AS TOTAL_DETECTIONS,
    
    (SELECT COUNT(*) 
     FROM UNSTRUCTURED.CV_DETECTIONS cv 
     WHERE cv.INSPECTION_ID = vi.INSPECTION_ID 
       AND cv.SEVERITY_LEVEL IN ('HIGH', 'CRITICAL')) AS CRITICAL_DETECTIONS

FROM UNSTRUCTURED.VISUAL_INSPECTIONS vi
JOIN RAW.ASSET_MASTER a ON vi.ASSET_ID = a.ASSET_ID
ORDER BY vi.INSPECTION_DATE DESC
LIMIT 30;


-- ============================================================
-- QUERY 10: Assets with Oil Temperature Issues + Leak History
-- ============================================================
-- Specific use case: Find transformers with current thermal issues
-- AND documented oil leak history in maintenance logs

SELECT 
    a.ASSET_ID,
    a.LOCATION_SUBSTATION AS SUBSTATION,
    a.ASSET_TYPE,
    
    -- Current sensor reading
    sr.OIL_TEMPERATURE_C AS CURRENT_OIL_TEMP,
    sr.READING_TIMESTAMP AS LAST_READING,
    
    -- Historical maintenance mentioning oil leaks
    m.DOCUMENT_DATE AS LEAK_REPORTED_DATE,
    m.DOCUMENT_TEXT AS MAINTENANCE_FINDING,
    m.TECHNICIAN_NAME,
    
    -- ML prediction
    mp.FAILURE_PROBABILITY,
    mp.PREDICTED_RUL_DAYS

FROM RAW.ASSET_MASTER a
JOIN RAW.SENSOR_READINGS sr 
    ON a.ASSET_ID = sr.ASSET_ID
LEFT JOIN UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS m 
    ON a.ASSET_ID = m.ASSET_ID
    AND LOWER(m.DOCUMENT_TEXT) LIKE '%oil%leak%'
LEFT JOIN ML.MODEL_PREDICTIONS mp 
    ON a.ASSET_ID = mp.ASSET_ID

WHERE sr.OIL_TEMPERATURE_C > 75
  AND sr.READING_TIMESTAMP >= DATEADD(day, -7, CURRENT_TIMESTAMP())
  AND a.ASSET_TYPE LIKE '%TRANSFORMER%'
  
ORDER BY sr.OIL_TEMPERATURE_C DESC
LIMIT 20;


-- ============================================================
-- ✅ ALL QUERIES USE CORRECT COLUMN NAMES
-- ✅ ALL QUERIES VALIDATED AGAINST ACTUAL SCHEMA
-- ✅ RUN ANY OF THESE IN SNOWSIGHT TO TEST INTEGRATION
-- ============================================================


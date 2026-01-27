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

-- ========================================================
-- Grid Reliability: Business Analytics Views
-- ========================================================
-- Creates views with ROI, cost avoidance, and reliability metrics
-- ========================================================

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA ANALYTICS;

-- ========================================================
-- View 1: Cost Avoidance Report
-- ========================================================
CREATE OR REPLACE VIEW VW_COST_AVOIDANCE_REPORT AS
WITH high_risk_assets AS (
    SELECT 
        p.ASSET_ID,
        p.FAILURE_PROBABILITY,
        p.RISK_SCORE,
        p.PREDICTED_RUL_DAYS,
        a.CUSTOMERS_AFFECTED,
        a.CRITICALITY_SCORE
    FROM ML.MODEL_PREDICTIONS p
    JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
    WHERE p.RISK_SCORE >= 70  -- High risk threshold (HIGH and CRITICAL only)
),
cost_calculations AS (
    SELECT 
        COUNT(*) AS HIGH_RISK_ASSETS,
        SUM(CUSTOMERS_AFFECTED) AS TOTAL_CUSTOMERS_PROTECTED,
        
        -- Emergency repair cost if all high-risk assets fail
        -- Average emergency repair: $450,000 per asset
        COUNT(*) * 450000 AS EMERGENCY_REPAIR_COST_AVOIDANCE,
        
        -- Preventive maintenance cost
        -- Average preventive maintenance: $45,000 per asset
        COUNT(*) * 45000 AS PREVENTIVE_MAINTENANCE_COST,
        
        -- Net cost avoidance
        (COUNT(*) * 450000) - (COUNT(*) * 45000) AS NET_COST_AVOIDANCE,
        
        -- SAIDI impact calculation
        -- Average outage: 4.2 hours, utility customer base: 5.8M
        (SUM(CUSTOMERS_AFFECTED) * 4.2 * 60) / 5800000.0 AS SAIDI_IMPACT_PREVENTED,
        
        -- Customer impact
        SUM(CUSTOMERS_AFFECTED * 4.2) AS TOTAL_CUSTOMER_HOURS_SAVED
        
    FROM high_risk_assets
)
SELECT 
    HIGH_RISK_ASSETS,
    TOTAL_CUSTOMERS_PROTECTED,
    EMERGENCY_REPAIR_COST_AVOIDANCE,
    PREVENTIVE_MAINTENANCE_COST,
    NET_COST_AVOIDANCE,
    SAIDI_IMPACT_PREVENTED,
    TOTAL_CUSTOMER_HOURS_SAVED,
    CURRENT_TIMESTAMP() AS CALCULATED_AT
FROM cost_calculations;

-- ========================================================
-- View 2: Reliability Metrics
-- ========================================================
CREATE OR REPLACE VIEW VW_RELIABILITY_METRICS AS
WITH asset_stats AS (
    SELECT 
        COUNT(*) AS TOTAL_ASSETS,
        COUNT(CASE WHEN p.RISK_SCORE >= 85 THEN 1 END) AS CRITICAL_ASSETS,
        COUNT(CASE WHEN p.RISK_SCORE >= 70 AND p.RISK_SCORE < 85 THEN 1 END) AS HIGH_RISK_ASSETS,
        COUNT(CASE WHEN p.RISK_SCORE >= 40 AND p.RISK_SCORE < 70 THEN 1 END) AS MEDIUM_RISK_ASSETS,
        COUNT(CASE WHEN p.RISK_SCORE < 40 THEN 1 END) AS LOW_RISK_ASSETS,
        SUM(a.CUSTOMERS_AFFECTED) AS TOTAL_CUSTOMERS_SERVED,
        AVG(p.FAILURE_PROBABILITY) AS AVG_FAILURE_PROBABILITY,
        AVG(p.PREDICTED_RUL_DAYS) AS AVG_PREDICTED_RUL
    FROM ML.MODEL_PREDICTIONS p
    JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
),
reliability_calcs AS (
    SELECT 
        TOTAL_ASSETS,
        CRITICAL_ASSETS,
        HIGH_RISK_ASSETS,
        MEDIUM_RISK_ASSETS,
        LOW_RISK_ASSETS,
        TOTAL_CUSTOMERS_SERVED,
        AVG_FAILURE_PROBABILITY,
        AVG_PREDICTED_RUL,
        
        -- Customers at risk (critical + high risk >= 70)
        (SELECT SUM(a.CUSTOMERS_AFFECTED) 
         FROM ML.MODEL_PREDICTIONS p
         JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
         WHERE p.RISK_SCORE >= 70) AS TOTAL_CUSTOMERS_AT_RISK,
        
        -- Potential SAIDI impact if high-risk assets fail
        -- Formula: (customers affected * outage hours * 60) / total customers
        COALESCE(((SELECT SUM(a.CUSTOMERS_AFFECTED) 
          FROM ML.MODEL_PREDICTIONS p
          JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
          WHERE p.RISK_SCORE >= 70) * 4.2 * 60) / NULLIF(TOTAL_CUSTOMERS_SERVED, 0), 0) AS POTENTIAL_SAIDI_POINTS,
        
        -- Potential SAIFI impact (number of interruptions)
        -- Assuming each failure affects 1 interruption per customer
        COALESCE((SELECT SUM(a.CUSTOMERS_AFFECTED) 
          FROM ML.MODEL_PREDICTIONS p
          JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
          WHERE p.RISK_SCORE >= 70) / NULLIF(TOTAL_CUSTOMERS_SERVED, 0), 0) AS POTENTIAL_SAIFI_POINTS,
        
        -- Fleet health score (0-100, inverse of average risk)
        COALESCE(100 - (SELECT AVG(RISK_SCORE) FROM ML.MODEL_PREDICTIONS), 100) AS FLEET_HEALTH_SCORE
        
    FROM asset_stats
)
SELECT 
    TOTAL_ASSETS,
    CRITICAL_ASSETS,
    HIGH_RISK_ASSETS,
    MEDIUM_RISK_ASSETS,
    LOW_RISK_ASSETS,
    TOTAL_CUSTOMERS_SERVED,
    TOTAL_CUSTOMERS_AT_RISK,
    ROUND(AVG_FAILURE_PROBABILITY, 4) AS AVG_FAILURE_PROBABILITY,
    ROUND(AVG_PREDICTED_RUL, 2) AS AVG_PREDICTED_RUL,
    ROUND(POTENTIAL_SAIDI_POINTS, 6) AS POTENTIAL_SAIDI_POINTS,
    ROUND(POTENTIAL_SAIFI_POINTS, 6) AS POTENTIAL_SAIFI_POINTS,
    ROUND(FLEET_HEALTH_SCORE, 2) AS FLEET_HEALTH_SCORE,
    CURRENT_TIMESTAMP() AS CALCULATED_AT
FROM reliability_calcs;

-- ========================================================
-- View 3: Asset Health Dashboard (Enhanced)
-- ========================================================
CREATE OR REPLACE VIEW VW_ASSET_HEALTH_DASHBOARD AS
SELECT 
    p.ASSET_ID,
    a.ASSET_TYPE,
    a.LOCATION_SUBSTATION,
    a.LOCATION_CITY,
    a.LOCATION_COUNTY,
    a.LOCATION_LAT,
    a.LOCATION_LON,
    a.CUSTOMERS_AFFECTED,
    a.CRITICALITY_SCORE,
    
    -- Predictions
    ROUND(p.RISK_SCORE, 2) AS RISK_SCORE,
    ROUND(p.FAILURE_PROBABILITY, 4) AS FAILURE_PROBABILITY,
    ROUND(p.PREDICTED_RUL_DAYS, 2) AS PREDICTED_RUL_DAYS,
    ROUND(p.ANOMALY_SCORE, 4) AS ANOMALY_SCORE,
    ROUND(p.CONFIDENCE, 4) AS CONFIDENCE,
    p.ALERT_LEVEL,
    
    -- Risk categorization (aligned with ALERT_LEVEL thresholds)
    CASE 
        WHEN p.RISK_SCORE >= 85 THEN 'CRITICAL'
        WHEN p.RISK_SCORE >= 70 THEN 'HIGH'
        WHEN p.RISK_SCORE >= 40 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS RISK_CATEGORY,
    
    -- Asset details
    DATEDIFF(day, a.INSTALL_DATE, CURRENT_DATE()) / 365.25 AS ASSET_AGE_YEARS,
    DATEDIFF(day, 
        (SELECT MAX(MAINTENANCE_DATE) 
         FROM RAW.MAINTENANCE_HISTORY m 
         WHERE m.ASSET_ID = p.ASSET_ID),
        CURRENT_DATE()
    ) AS DAYS_SINCE_MAINTENANCE,
    
    -- Financial impact
    CASE 
        WHEN p.RISK_SCORE >= 70 THEN 450000  -- Emergency repair cost for HIGH and CRITICAL
        ELSE 0
    END AS POTENTIAL_FAILURE_COST,
    
    45000 AS PREVENTIVE_MAINTENANCE_COST,
    
    -- SAIDI impact
    (a.CUSTOMERS_AFFECTED * 4.2 * 60) / 5800000.0 AS ESTIMATED_SAIDI_IMPACT,
    
    p.PREDICTION_TIMESTAMP,
    p.MODEL_ID
    
FROM ML.MODEL_PREDICTIONS p
JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
ORDER BY p.RISK_SCORE DESC;

-- ========================================================
-- View 4: High-Risk Assets (Enhanced)
-- ========================================================
CREATE OR REPLACE VIEW VW_HIGH_RISK_ASSETS AS
SELECT 
    p.ASSET_ID,
    a.ASSET_TYPE,
    a.LOCATION_SUBSTATION,
    a.LOCATION_CITY,
    a.LOCATION_COUNTY,
    a.LOCATION_LAT,
    a.LOCATION_LON,
    
    -- Risk metrics
    ROUND(p.RISK_SCORE, 2) AS RISK_SCORE,
    ROUND(p.FAILURE_PROBABILITY, 4) AS FAILURE_PROBABILITY,
    ROUND(p.PREDICTED_RUL_DAYS, 2) AS PREDICTED_RUL_DAYS,
    ROUND(p.ANOMALY_SCORE, 4) AS ANOMALY_SCORE,
    p.ALERT_LEVEL,
    
    -- Impact
    a.CUSTOMERS_AFFECTED,
    a.CRITICALITY_SCORE,
    
    -- Maintenance
    DATEDIFF(day, 
        (SELECT MAX(MAINTENANCE_DATE) 
         FROM RAW.MAINTENANCE_HISTORY m 
         WHERE m.ASSET_ID = p.ASSET_ID),
        CURRENT_DATE()
    ) AS DAYS_SINCE_MAINTENANCE,
    
    -- Recommendations (aligned with ALERT_LEVEL thresholds)
    CASE 
        WHEN p.RISK_SCORE >= 85 THEN 'IMMEDIATE - Within 7 days'
        WHEN p.RISK_SCORE >= 70 THEN 'URGENT - Within 14 days'
        WHEN p.RISK_SCORE >= 40 THEN 'SCHEDULED - Within 30 days'
        ELSE 'ROUTINE - Next maintenance cycle'
    END AS RECOMMENDED_ACTION_TIMELINE,
    
    CASE 
        WHEN p.RISK_SCORE >= 85 THEN 1
        WHEN p.RISK_SCORE >= 70 THEN 2
        WHEN p.RISK_SCORE >= 40 THEN 3
        ELSE 4
    END AS WORK_ORDER_PRIORITY,
    
    -- Financial impact
    450000 AS ESTIMATED_FAILURE_COST,
    45000 AS PREVENTIVE_MAINTENANCE_COST,
    405000 AS COST_AVOIDANCE_POTENTIAL,
    
    -- Reliability impact
    ROUND((a.CUSTOMERS_AFFECTED * 4.2 * 60) / 5800000.0, 6) AS ESTIMATED_SAIDI_IMPACT,
    ROUND(a.CUSTOMERS_AFFECTED / 5800000.0, 6) AS ESTIMATED_SAIFI_IMPACT,
    
    p.PREDICTION_TIMESTAMP
    
FROM ML.MODEL_PREDICTIONS p
JOIN RAW.ASSET_MASTER a ON p.ASSET_ID = a.ASSET_ID
WHERE p.RISK_SCORE >= 70  -- High risk threshold (HIGH and CRITICAL only)
ORDER BY p.RISK_SCORE DESC;

-- ========================================================
-- Verification Queries
-- ========================================================

-- Check cost avoidance
SELECT * FROM VW_COST_AVOIDANCE_REPORT;

-- Check reliability metrics
SELECT * FROM VW_RELIABILITY_METRICS;

-- Check asset health dashboard
SELECT * FROM VW_ASSET_HEALTH_DASHBOARD LIMIT 10;

-- Check high-risk assets
SELECT * FROM VW_HIGH_RISK_ASSETS LIMIT 10;

-- ========================================================
-- Summary Statistics
-- ========================================================
SELECT 
    'Cost Avoidance' AS METRIC_TYPE,
    CONCAT('$', ROUND(NET_COST_AVOIDANCE/1000000.0, 2), 'M') AS VALUE
FROM VW_COST_AVOIDANCE_REPORT
UNION ALL
SELECT 
    'ROI',
    CONCAT(ROUND((NET_COST_AVOIDANCE/NULLIF(PREVENTIVE_MAINTENANCE_COST, 0))*100, 0), '%')
FROM VW_COST_AVOIDANCE_REPORT
UNION ALL
SELECT 
    'High-Risk Assets',
    CAST(HIGH_RISK_ASSETS AS VARCHAR)
FROM VW_COST_AVOIDANCE_REPORT
UNION ALL
SELECT 
    'Customers Protected',
    CAST(TOTAL_CUSTOMERS_PROTECTED AS VARCHAR)
FROM VW_COST_AVOIDANCE_REPORT
UNION ALL
SELECT 
    'SAIDI Impact Prevented',
    CONCAT(ROUND(SAIDI_IMPACT_PREVENTED, 4), ' points')
FROM VW_COST_AVOIDANCE_REPORT
UNION ALL
SELECT 
    'Fleet Health Score',
    CONCAT(ROUND(FLEET_HEALTH_SCORE, 1), '/100')
FROM VW_RELIABILITY_METRICS;


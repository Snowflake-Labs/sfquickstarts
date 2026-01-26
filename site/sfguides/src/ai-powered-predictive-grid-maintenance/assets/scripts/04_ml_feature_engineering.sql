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
 * ML Pipeline - Part 1: Feature Engineering
 * 
 * Purpose: Create views that compute engineered features for ML models
 * These features combine sensor readings with asset characteristics
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-15
 * Version: 1.0
 ******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA ML;

-- =============================================================================
-- SECTION 1: HOURLY ASSET FEATURES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: VW_ASSET_FEATURES_HOURLY
-- Purpose: Compute engineered features at hourly granularity
-- Features include rolling statistics, trends, and anomaly indicators
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_ASSET_FEATURES_HOURLY AS
WITH sensor_stats AS (
    SELECT 
        ASSET_ID,
        DATE_TRUNC('hour', READING_TIMESTAMP) as FEATURE_TIMESTAMP,
        
        -- Current values (hourly average)
        AVG(OIL_TEMPERATURE_C) as OIL_TEMP_CURRENT,
        AVG(WINDING_TEMPERATURE_C) as WINDING_TEMP_CURRENT,
        AVG(LOAD_CURRENT_A) as LOAD_CURRENT_CURRENT,
        AVG(LOAD_VOLTAGE_KV) as LOAD_VOLTAGE_CURRENT,
        AVG(AMBIENT_TEMP_C) as AMBIENT_TEMP_CURRENT,
        AVG(HUMIDITY_PCT) as HUMIDITY_CURRENT,
        AVG(VIBRATION_MM_S) as VIBRATION_CURRENT,
        AVG(ACOUSTIC_DB) as ACOUSTIC_CURRENT,
        AVG(DISSOLVED_H2_PPM) as H2_CURRENT,
        AVG(DISSOLVED_CO_PPM) as CO_CURRENT,
        AVG(DISSOLVED_CO2_PPM) as CO2_CURRENT,
        AVG(DISSOLVED_CH4_PPM) as CH4_CURRENT,
        AVG(BUSHING_TEMP_C) as BUSHING_TEMP_CURRENT,
        AVG(PARTIAL_DISCHARGE_PC) as PARTIAL_DISCHARGE_CURRENT,
        AVG(POWER_FACTOR) as POWER_FACTOR_CURRENT,
        
        -- Peak values in hour
        MAX(OIL_TEMPERATURE_C) as OIL_TEMP_MAX,
        MAX(LOAD_CURRENT_A) as LOAD_CURRENT_MAX,
        
        -- Variability indicators
        STDDEV(OIL_TEMPERATURE_C) as OIL_TEMP_STDDEV,
        STDDEV(LOAD_CURRENT_A) as LOAD_CURRENT_STDDEV,
        
        COUNT(*) as READING_COUNT
        
    FROM RAW.SENSOR_READINGS
    WHERE READING_TIMESTAMP >= DATEADD(hour, -24*90, CURRENT_TIMESTAMP()) -- Last 90 days
    GROUP BY ASSET_ID, DATE_TRUNC('hour', READING_TIMESTAMP)
),
rolling_stats AS (
    SELECT 
        ASSET_ID,
        FEATURE_TIMESTAMP,
        OIL_TEMP_CURRENT,
        WINDING_TEMP_CURRENT,
        LOAD_CURRENT_CURRENT,
        LOAD_VOLTAGE_CURRENT,
        AMBIENT_TEMP_CURRENT,
        HUMIDITY_CURRENT,
        VIBRATION_CURRENT,
        ACOUSTIC_CURRENT,
        H2_CURRENT,
        CO_CURRENT,
        CO2_CURRENT,
        CH4_CURRENT,
        BUSHING_TEMP_CURRENT,
        PARTIAL_DISCHARGE_CURRENT,
        POWER_FACTOR_CURRENT,
        OIL_TEMP_MAX,
        LOAD_CURRENT_MAX,
        OIL_TEMP_STDDEV,
        LOAD_CURRENT_STDDEV,
        READING_COUNT,
        
        -- 7-day rolling averages
        AVG(OIL_TEMP_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
        ) as OIL_TEMP_7D_AVG,
        
        AVG(LOAD_CURRENT_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
        ) as LOAD_CURRENT_7D_AVG,
        
        AVG(H2_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
        ) as H2_7D_AVG,
        
        AVG(VIBRATION_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
        ) as VIBRATION_7D_AVG,
        
        -- 30-day rolling averages
        AVG(OIL_TEMP_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 719 PRECEDING AND CURRENT ROW
        ) as OIL_TEMP_30D_AVG,
        
        AVG(LOAD_CURRENT_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 719 PRECEDING AND CURRENT ROW
        ) as LOAD_CURRENT_30D_AVG,
        
        AVG(H2_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 719 PRECEDING AND CURRENT ROW
        ) as H2_30D_AVG,
        
        -- 30-day standard deviations
        STDDEV(OIL_TEMP_CURRENT) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_TIMESTAMP 
            ROWS BETWEEN 719 PRECEDING AND CURRENT ROW
        ) as OIL_TEMP_30D_STDDEV,
        
        -- Rate of change (7-day vs 30-day)
        LAG(OIL_TEMP_CURRENT, 168) OVER (PARTITION BY ASSET_ID ORDER BY FEATURE_TIMESTAMP) as OIL_TEMP_7D_AGO,
        LAG(H2_CURRENT, 168) OVER (PARTITION BY ASSET_ID ORDER BY FEATURE_TIMESTAMP) as H2_7D_AGO
        
    FROM sensor_stats
)
SELECT 
    rs.ASSET_ID,
    rs.FEATURE_TIMESTAMP,
    
    -- Current measurements
    rs.OIL_TEMP_CURRENT,
    rs.WINDING_TEMP_CURRENT,
    rs.LOAD_CURRENT_CURRENT,
    rs.LOAD_VOLTAGE_CURRENT,
    rs.AMBIENT_TEMP_CURRENT,
    rs.HUMIDITY_CURRENT,
    rs.VIBRATION_CURRENT,
    rs.ACOUSTIC_CURRENT,
    rs.H2_CURRENT,
    rs.CO_CURRENT,
    rs.CO2_CURRENT,
    rs.CH4_CURRENT,
    rs.BUSHING_TEMP_CURRENT,
    rs.PARTIAL_DISCHARGE_CURRENT,
    rs.POWER_FACTOR_CURRENT,
    
    -- Rolling averages
    rs.OIL_TEMP_7D_AVG,
    rs.OIL_TEMP_30D_AVG,
    rs.LOAD_CURRENT_7D_AVG,
    rs.LOAD_CURRENT_30D_AVG,
    rs.H2_7D_AVG,
    rs.H2_30D_AVG,
    rs.VIBRATION_7D_AVG,
    
    -- Variability
    rs.OIL_TEMP_30D_STDDEV,
    rs.OIL_TEMP_STDDEV as OIL_TEMP_HOURLY_STDDEV,
    
    -- Rate of change features
    CASE WHEN rs.OIL_TEMP_7D_AGO IS NOT NULL AND rs.OIL_TEMP_7D_AGO > 0
         THEN (rs.OIL_TEMP_CURRENT - rs.OIL_TEMP_7D_AGO) / rs.OIL_TEMP_7D_AGO
         ELSE 0 END as OIL_TEMP_7D_CHANGE_PCT,
    
    CASE WHEN rs.H2_7D_AGO IS NOT NULL AND rs.H2_7D_AGO > 0
         THEN (rs.H2_CURRENT - rs.H2_7D_AGO) / rs.H2_7D_AGO
         ELSE 0 END as H2_7D_CHANGE_PCT,
    
    -- Deviation from normal (using 30-day baseline)
    CASE WHEN rs.OIL_TEMP_30D_AVG > 0 AND rs.OIL_TEMP_30D_STDDEV > 0
         THEN (rs.OIL_TEMP_CURRENT - rs.OIL_TEMP_30D_AVG) / rs.OIL_TEMP_30D_STDDEV
         ELSE 0 END as OIL_TEMP_Z_SCORE,
    
    -- Asset characteristics (from master data)
    am.CAPACITY_MVA,
    am.VOLTAGE_RATING_KV,
    am.CRITICALITY_SCORE,
    am.CUSTOMERS_AFFECTED,
    
    -- Asset age and maintenance
    DATEDIFF(day, am.INSTALL_DATE, rs.FEATURE_TIMESTAMP::DATE) / 365.25 as ASSET_AGE_YEARS,
    DATEDIFF(day, am.LAST_MAINTENANCE_DATE, rs.FEATURE_TIMESTAMP::DATE) as DAYS_SINCE_MAINTENANCE,
    
    -- Load utilization
    (rs.LOAD_CURRENT_CURRENT / (am.CAPACITY_MVA * 1000 / am.VOLTAGE_RATING_KV)) as LOAD_UTILIZATION_PCT,
    (rs.LOAD_CURRENT_MAX / (am.CAPACITY_MVA * 1000 / am.VOLTAGE_RATING_KV)) as LOAD_UTILIZATION_PEAK_PCT,
    
    -- Thermal stress indicator
    (rs.OIL_TEMP_CURRENT - rs.AMBIENT_TEMP_CURRENT) as THERMAL_RISE,
    
    -- DGA ratios (dissolved gas analysis)
    CASE WHEN rs.CO_CURRENT > 0 THEN rs.H2_CURRENT / rs.CO_CURRENT ELSE 0 END as H2_CO_RATIO,
    CASE WHEN rs.CO2_CURRENT > 0 THEN rs.CO_CURRENT / rs.CO2_CURRENT ELSE 0 END as CO_CO2_RATIO,
    
    -- Composite DGA indicator (simplified Duval triangle)
    (rs.H2_CURRENT + rs.CH4_CURRENT + rs.CO_CURRENT) as TOTAL_COMBUSTIBLE_GASES,
    
    -- Data quality
    rs.READING_COUNT as HOURLY_READING_COUNT

FROM rolling_stats rs
JOIN RAW.ASSET_MASTER am ON rs.ASSET_ID = am.ASSET_ID
WHERE am.STATUS = 'ACTIVE';

-- =============================================================================
-- SECTION 2: DAILY AGGREGATED FEATURES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: VW_ASSET_FEATURES_DAILY
-- Purpose: Daily aggregated features for trend analysis
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_ASSET_FEATURES_DAILY AS
SELECT 
    ASSET_ID,
    DATE_TRUNC('day', FEATURE_TIMESTAMP) as FEATURE_DATE,
    
    -- Daily averages
    AVG(OIL_TEMP_CURRENT) as OIL_TEMP_DAILY_AVG,
    MAX(OIL_TEMP_CURRENT) as OIL_TEMP_DAILY_MAX,
    MIN(OIL_TEMP_CURRENT) as OIL_TEMP_DAILY_MIN,
    
    AVG(LOAD_UTILIZATION_PCT) as LOAD_UTILIZATION_DAILY_AVG,
    MAX(LOAD_UTILIZATION_PEAK_PCT) as LOAD_UTILIZATION_DAILY_PEAK,
    
    AVG(H2_CURRENT) as H2_DAILY_AVG,
    MAX(H2_CURRENT) as H2_DAILY_MAX,
    
    AVG(VIBRATION_CURRENT) as VIBRATION_DAILY_AVG,
    MAX(VIBRATION_CURRENT) as VIBRATION_DAILY_MAX,
    
    AVG(THERMAL_RISE) as THERMAL_RISE_DAILY_AVG,
    MAX(THERMAL_RISE) as THERMAL_RISE_DAILY_MAX,
    
    AVG(TOTAL_COMBUSTIBLE_GASES) as COMBUSTIBLE_GASES_DAILY_AVG,
    
    -- Operating hours (assume >30% load is operating)
    COUNT_IF(LOAD_UTILIZATION_PCT > 0.3) as OPERATING_HOURS,
    
    -- Asset characteristics (take latest)
    MAX(ASSET_AGE_YEARS) as ASSET_AGE_YEARS,
    MAX(DAYS_SINCE_MAINTENANCE) as DAYS_SINCE_MAINTENANCE,
    MAX(CAPACITY_MVA) as CAPACITY_MVA,
    MAX(CRITICALITY_SCORE) as CRITICALITY_SCORE,
    MAX(CUSTOMERS_AFFECTED) as CUSTOMERS_AFFECTED

FROM VW_ASSET_FEATURES_HOURLY
GROUP BY ASSET_ID, DATE_TRUNC('day', FEATURE_TIMESTAMP);

-- =============================================================================
-- SECTION 3: DEGRADATION INDICATORS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: VW_DEGRADATION_INDICATORS
-- Purpose: Specific indicators of asset health degradation
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_DEGRADATION_INDICATORS AS
WITH daily_features AS (
    SELECT * FROM VW_ASSET_FEATURES_DAILY
    WHERE FEATURE_DATE >= DATEADD(day, -90, CURRENT_DATE())
),
trends AS (
    SELECT 
        ASSET_ID,
        FEATURE_DATE,
        OIL_TEMP_DAILY_AVG,
        H2_DAILY_AVG,
        LOAD_UTILIZATION_DAILY_AVG,
        VIBRATION_DAILY_AVG,
        THERMAL_RISE_DAILY_AVG,
        
        -- 30-day trends using linear regression approximation
        AVG(OIL_TEMP_DAILY_AVG) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_DATE 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as OIL_TEMP_30D_MEAN,
        
        AVG(H2_DAILY_AVG) OVER (
            PARTITION BY ASSET_ID 
            ORDER BY FEATURE_DATE 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) as H2_30D_MEAN
        
    FROM daily_features
)
SELECT 
    t.ASSET_ID,
    t.FEATURE_DATE as INDICATOR_DATE,
    
    -- Oil quality index (0-100, lower is worse)
    100 - LEAST(100, (
        (t.H2_DAILY_AVG / 500 * 40) +  -- H2 contributes up to 40 points of degradation
        (GREATEST(0, t.OIL_TEMP_DAILY_AVG - 90) / 20 * 30) +  -- Excess temp up to 30 points
        (t.VIBRATION_DAILY_AVG / 10 * 30)  -- Vibration up to 30 points
    )) as OIL_QUALITY_INDEX,
    
    -- Thermal stress index (0-100, higher is more stressed)
    LEAST(100, (
        t.THERMAL_RISE_DAILY_AVG / 80 * 100
    )) as THERMAL_STRESS_INDEX,
    
    -- Electrical stress index
    LEAST(100, (
        t.LOAD_UTILIZATION_DAILY_AVG * 100
    )) as ELECTRICAL_STRESS_INDEX,
    
    -- Mechanical stress index
    LEAST(100, (
        t.VIBRATION_DAILY_AVG / 8 * 100
    )) as MECHANICAL_STRESS_INDEX,
    
    -- Maintenance effectiveness (based on recent maintenance)
    CASE 
        WHEN df.DAYS_SINCE_MAINTENANCE < 90 THEN 100
        WHEN df.DAYS_SINCE_MAINTENANCE < 180 THEN 90
        WHEN df.DAYS_SINCE_MAINTENANCE < 365 THEN 70
        WHEN df.DAYS_SINCE_MAINTENANCE < 730 THEN 50
        ELSE 30
    END as MAINTENANCE_EFFECTIVENESS,
    
    -- Overall health index (0-100, 100 is perfect health)
    (
        (100 - LEAST(100, (t.H2_DAILY_AVG / 500 * 40) + (GREATEST(0, t.OIL_TEMP_DAILY_AVG - 90) / 20 * 30) + (t.VIBRATION_DAILY_AVG / 10 * 30))) * 0.3 +
        (100 - LEAST(100, (t.THERMAL_RISE_DAILY_AVG / 80 * 100))) * 0.2 +
        (100 - LEAST(100, (t.LOAD_UTILIZATION_DAILY_AVG * 100))) * 0.2 +
        (100 - LEAST(100, (t.VIBRATION_DAILY_AVG / 8 * 100))) * 0.15 +
        (CASE WHEN df.DAYS_SINCE_MAINTENANCE < 90 THEN 100 WHEN df.DAYS_SINCE_MAINTENANCE < 180 THEN 90 
              WHEN df.DAYS_SINCE_MAINTENANCE < 365 THEN 70 WHEN df.DAYS_SINCE_MAINTENANCE < 730 THEN 50 ELSE 30 END) * 0.15
    ) as OVERALL_HEALTH_INDEX,
    
    -- Trending (positive means getting worse)
    CASE WHEN t.OIL_TEMP_30D_MEAN > 0 
         THEN (t.OIL_TEMP_DAILY_AVG - t.OIL_TEMP_30D_MEAN) / t.OIL_TEMP_30D_MEAN * 100
         ELSE 0 END as OIL_TEMP_TREND_PCT,
    
    CASE WHEN t.H2_30D_MEAN > 0 
         THEN (t.H2_DAILY_AVG - t.H2_30D_MEAN) / t.H2_30D_MEAN * 100
         ELSE 0 END as H2_TREND_PCT,
    
    -- Asset info
    df.ASSET_AGE_YEARS,
    df.DAYS_SINCE_MAINTENANCE,
    df.CAPACITY_MVA,
    df.CRITICALITY_SCORE,
    df.CUSTOMERS_AFFECTED

FROM trends t
JOIN daily_features df ON t.ASSET_ID = df.ASSET_ID AND t.FEATURE_DATE = df.FEATURE_DATE;

-- =============================================================================
-- SECTION 4: ANOMALY SCORES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: VW_ANOMALY_SCORES
-- Purpose: Statistical anomaly detection using z-scores
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW VW_ANOMALY_SCORES AS
WITH hourly_features AS (
    SELECT * FROM VW_ASSET_FEATURES_HOURLY
    WHERE FEATURE_TIMESTAMP >= DATEADD(day, -90, CURRENT_DATE())
),
asset_baselines AS (
    SELECT 
        ASSET_ID,
        AVG(OIL_TEMP_CURRENT) as OIL_TEMP_BASELINE,
        STDDEV(OIL_TEMP_CURRENT) as OIL_TEMP_BASELINE_STD,
        AVG(H2_CURRENT) as H2_BASELINE,
        STDDEV(H2_CURRENT) as H2_BASELINE_STD,
        AVG(VIBRATION_CURRENT) as VIBRATION_BASELINE,
        STDDEV(VIBRATION_CURRENT) as VIBRATION_BASELINE_STD,
        AVG(LOAD_UTILIZATION_PCT) as LOAD_BASELINE,
        STDDEV(LOAD_UTILIZATION_PCT) as LOAD_BASELINE_STD
    FROM hourly_features
    GROUP BY ASSET_ID
)
SELECT 
    hf.ASSET_ID,
    hf.FEATURE_TIMESTAMP,
    
    -- Z-scores for key parameters
    CASE WHEN ab.OIL_TEMP_BASELINE_STD > 0
         THEN ABS((hf.OIL_TEMP_CURRENT - ab.OIL_TEMP_BASELINE) / ab.OIL_TEMP_BASELINE_STD)
         ELSE 0 END as OIL_TEMP_Z_SCORE,
    
    CASE WHEN ab.H2_BASELINE_STD > 0
         THEN ABS((hf.H2_CURRENT - ab.H2_BASELINE) / ab.H2_BASELINE_STD)
         ELSE 0 END as H2_Z_SCORE,
    
    CASE WHEN ab.VIBRATION_BASELINE_STD > 0
         THEN ABS((hf.VIBRATION_CURRENT - ab.VIBRATION_BASELINE) / ab.VIBRATION_BASELINE_STD)
         ELSE 0 END as VIBRATION_Z_SCORE,
    
    CASE WHEN ab.LOAD_BASELINE_STD > 0
         THEN ABS((hf.LOAD_UTILIZATION_PCT - ab.LOAD_BASELINE) / ab.LOAD_BASELINE_STD)
         ELSE 0 END as LOAD_Z_SCORE,
    
    -- Composite anomaly score (max z-score)
    GREATEST(
        CASE WHEN ab.OIL_TEMP_BASELINE_STD > 0 THEN ABS((hf.OIL_TEMP_CURRENT - ab.OIL_TEMP_BASELINE) / ab.OIL_TEMP_BASELINE_STD) ELSE 0 END,
        CASE WHEN ab.H2_BASELINE_STD > 0 THEN ABS((hf.H2_CURRENT - ab.H2_BASELINE) / ab.H2_BASELINE_STD) ELSE 0 END,
        CASE WHEN ab.VIBRATION_BASELINE_STD > 0 THEN ABS((hf.VIBRATION_CURRENT - ab.VIBRATION_BASELINE) / ab.VIBRATION_BASELINE_STD) ELSE 0 END
    ) as MAX_Z_SCORE,
    
    -- Anomaly flag (z-score > 3 is typically anomalous)
    CASE WHEN GREATEST(
        CASE WHEN ab.OIL_TEMP_BASELINE_STD > 0 THEN ABS((hf.OIL_TEMP_CURRENT - ab.OIL_TEMP_BASELINE) / ab.OIL_TEMP_BASELINE_STD) ELSE 0 END,
        CASE WHEN ab.H2_BASELINE_STD > 0 THEN ABS((hf.H2_CURRENT - ab.H2_BASELINE) / ab.H2_BASELINE_STD) ELSE 0 END,
        CASE WHEN ab.VIBRATION_BASELINE_STD > 0 THEN ABS((hf.VIBRATION_CURRENT - ab.VIBRATION_BASELINE) / ab.VIBRATION_BASELINE_STD) ELSE 0 END
    ) > 3 THEN TRUE ELSE FALSE END as IS_ANOMALY

FROM hourly_features hf
JOIN asset_baselines ab ON hf.ASSET_ID = ab.ASSET_ID;

-- =============================================================================
-- SCRIPT COMPLETE
-- =============================================================================

SELECT 'Feature engineering views created successfully!' as STATUS;
SELECT 'Views created: VW_ASSET_FEATURES_HOURLY, VW_ASSET_FEATURES_DAILY, VW_DEGRADATION_INDICATORS, VW_ANOMALY_SCORES' as VIEWS;
SELECT 'Next Step: Run 02_training_data_prep.sql' as NEXT_STEP;


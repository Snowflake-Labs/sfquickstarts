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
 * ML Pipeline - Part 2: Training Data Preparation
 * 
 * Purpose: Create labeled training datasets from historical data
 * Labels failures that occurred within 30 days of snapshot
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-15
 * Version: 1.0
 ******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA ML;

-- =============================================================================
-- SECTION 1: CREATE TRAINING DATA FROM HISTORICAL FAILURES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- This script creates labeled training data by:
-- 1. Taking snapshots of features at various points in time
-- 2. Looking forward 30 days to see if failure occurred
-- 3. Labeling each snapshot as FAILURE or NO_FAILURE
-- -----------------------------------------------------------------------------

TRUNCATE TABLE IF EXISTS TRAINING_DATA;

INSERT INTO TRAINING_DATA (
    ASSET_ID,
    SNAPSHOT_DATE,
    FAILURE_WITHIN_30_DAYS,
    DAYS_TO_FAILURE,
    FAILURE_TYPE,
    FEATURES,
    TRAINING_SET
)
WITH date_sequence AS (
    -- Generate a sequence of numbers from 0 to 25 (26 weeks)
    SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1 as WEEK_NUM
    FROM TABLE(GENERATOR(ROWCOUNT => 26))
),
snapshot_dates AS (
    -- Create snapshots every 7 days for each asset over last 6 months
    SELECT 
        am.ASSET_ID,
        DATEADD(day, ds.WEEK_NUM * 7, DATEADD(month, -6, CURRENT_DATE())) as SNAPSHOT_DATE
    FROM RAW.ASSET_MASTER am
    CROSS JOIN date_sequence ds
    WHERE am.STATUS = 'ACTIVE'
      AND DATEADD(day, ds.WEEK_NUM * 7, DATEADD(month, -6, CURRENT_DATE())) <= CURRENT_DATE()
),
failure_labels AS (
    -- For each snapshot, check if failure occurred within next 30 days
    SELECT 
        sd.ASSET_ID,
        sd.SNAPSHOT_DATE,
        fe.EVENT_ID,
        fe.FAILURE_TIMESTAMP,
        fe.FAILURE_TYPE,
        DATEDIFF(day, sd.SNAPSHOT_DATE, fe.FAILURE_TIMESTAMP::DATE) as DAYS_TO_FAILURE
    FROM snapshot_dates sd
    LEFT JOIN RAW.FAILURE_EVENTS fe 
        ON sd.ASSET_ID = fe.ASSET_ID
        AND fe.FAILURE_TIMESTAMP::DATE BETWEEN sd.SNAPSHOT_DATE 
                                          AND DATEADD(day, 30, sd.SNAPSHOT_DATE)
),
feature_snapshots AS (
    -- Get features at each snapshot date
    SELECT 
        fl.ASSET_ID,
        fl.SNAPSHOT_DATE,
        fl.EVENT_ID IS NOT NULL as FAILURE_WITHIN_30_DAYS,
        fl.DAYS_TO_FAILURE,
        fl.FAILURE_TYPE,
        
        -- Get features from nearest available date (within 1 day)
        df.OIL_TEMP_DAILY_AVG,
        df.OIL_TEMP_DAILY_MAX,
        df.H2_DAILY_AVG,
        df.H2_DAILY_MAX,
        df.VIBRATION_DAILY_AVG,
        df.LOAD_UTILIZATION_DAILY_AVG,
        df.LOAD_UTILIZATION_DAILY_PEAK,
        df.THERMAL_RISE_DAILY_AVG,
        df.COMBUSTIBLE_GASES_DAILY_AVG,
        df.OPERATING_HOURS,
        df.ASSET_AGE_YEARS,
        df.DAYS_SINCE_MAINTENANCE,
        df.CAPACITY_MVA,
        df.CRITICALITY_SCORE,
        df.CUSTOMERS_AFFECTED,
        
        -- Get degradation indicators
        di.OIL_QUALITY_INDEX,
        di.THERMAL_STRESS_INDEX,
        di.ELECTRICAL_STRESS_INDEX,
        di.MECHANICAL_STRESS_INDEX,
        di.MAINTENANCE_EFFECTIVENESS,
        di.OVERALL_HEALTH_INDEX,
        di.OIL_TEMP_TREND_PCT,
        di.H2_TREND_PCT
        
    FROM failure_labels fl
    LEFT JOIN ML.VW_ASSET_FEATURES_DAILY df 
        ON fl.ASSET_ID = df.ASSET_ID
        AND df.FEATURE_DATE BETWEEN DATEADD(day, -1, fl.SNAPSHOT_DATE) 
                                AND fl.SNAPSHOT_DATE
    LEFT JOIN ML.VW_DEGRADATION_INDICATORS di
        ON fl.ASSET_ID = di.ASSET_ID
        AND di.INDICATOR_DATE BETWEEN DATEADD(day, -1, fl.SNAPSHOT_DATE)
                                  AND fl.SNAPSHOT_DATE
    WHERE df.OIL_TEMP_DAILY_AVG IS NOT NULL  -- Ensure we have data
),
training_records AS (
    SELECT 
        ASSET_ID,
        SNAPSHOT_DATE,
        FAILURE_WITHIN_30_DAYS,
        DAYS_TO_FAILURE,
        FAILURE_TYPE,
        
        -- Package all features into VARIANT
        OBJECT_CONSTRUCT(
            'oil_temp_avg', OIL_TEMP_DAILY_AVG,
            'oil_temp_max', OIL_TEMP_DAILY_MAX,
            'h2_avg', H2_DAILY_AVG,
            'h2_max', H2_DAILY_MAX,
            'vibration_avg', VIBRATION_DAILY_AVG,
            'load_util_avg', LOAD_UTILIZATION_DAILY_AVG,
            'load_util_peak', LOAD_UTILIZATION_DAILY_PEAK,
            'thermal_rise_avg', THERMAL_RISE_DAILY_AVG,
            'combustible_gases', COMBUSTIBLE_GASES_DAILY_AVG,
            'operating_hours', OPERATING_HOURS,
            'asset_age_years', ASSET_AGE_YEARS,
            'days_since_maintenance', DAYS_SINCE_MAINTENANCE,
            'capacity_mva', CAPACITY_MVA,
            'criticality_score', CRITICALITY_SCORE,
            'customers_affected', CUSTOMERS_AFFECTED,
            'oil_quality_index', OIL_QUALITY_INDEX,
            'thermal_stress_index', THERMAL_STRESS_INDEX,
            'electrical_stress_index', ELECTRICAL_STRESS_INDEX,
            'mechanical_stress_index', MECHANICAL_STRESS_INDEX,
            'maintenance_effectiveness', MAINTENANCE_EFFECTIVENESS,
            'overall_health_index', OVERALL_HEALTH_INDEX,
            'oil_temp_trend_pct', OIL_TEMP_TREND_PCT,
            'h2_trend_pct', H2_TREND_PCT
        ) as FEATURES,
        
        -- Randomly assign to train/test/validation (70/20/10 split)
        CASE 
            WHEN UNIFORM(0::float, 1::float, RANDOM()) < 0.7 THEN 'TRAIN'
            WHEN UNIFORM(0::float, 1::float, RANDOM()) < 0.9 THEN 'TEST'
            ELSE 'VALIDATION'
        END as TRAINING_SET
        
    FROM feature_snapshots
)
SELECT * FROM training_records;

-- =============================================================================
-- SECTION 2: TRAINING DATA STATISTICS
-- =============================================================================

-- Show training data statistics
SELECT 'Training Data Statistics' as METRIC_TYPE, NULL as METRIC_NAME, NULL as METRIC_VALUE
UNION ALL
SELECT '', 'Total Records', COUNT(*)::VARCHAR FROM TRAINING_DATA
UNION ALL
SELECT '', 'Failure Cases', COUNT_IF(FAILURE_WITHIN_30_DAYS)::VARCHAR FROM TRAINING_DATA
UNION ALL
SELECT '', 'Non-Failure Cases', COUNT_IF(NOT FAILURE_WITHIN_30_DAYS)::VARCHAR FROM TRAINING_DATA
UNION ALL
SELECT '', 'Failure Rate', ROUND(COUNT_IF(FAILURE_WITHIN_30_DAYS) * 100.0 / COUNT(*), 2)::VARCHAR || '%' FROM TRAINING_DATA
UNION ALL
SELECT '', '', ''
UNION ALL
SELECT 'By Training Set', NULL, NULL
UNION ALL
SELECT '', 'TRAIN', COUNT_IF(TRAINING_SET = 'TRAIN')::VARCHAR FROM TRAINING_DATA
UNION ALL
SELECT '', 'TEST', COUNT_IF(TRAINING_SET = 'TEST')::VARCHAR FROM TRAINING_DATA
UNION ALL
SELECT '', 'VALIDATION', COUNT_IF(TRAINING_SET = 'VALIDATION')::VARCHAR FROM TRAINING_DATA
UNION ALL
SELECT '', '', ''
UNION ALL
SELECT 'Failures by Type', NULL, NULL
UNION ALL
SELECT '', FAILURE_TYPE, COUNT(*)::VARCHAR 
FROM TRAINING_DATA 
WHERE FAILURE_WITHIN_30_DAYS = TRUE 
GROUP BY FAILURE_TYPE;

-- =============================================================================
-- SECTION 3: FEATURE ANALYSIS
-- =============================================================================

-- Show feature statistics for failed vs non-failed assets
CREATE OR REPLACE TEMP TABLE FEATURE_COMPARISON AS
SELECT 
    FAILURE_WITHIN_30_DAYS,
    COUNT(*) as RECORD_COUNT,
    
    -- Average values for key features
    AVG(FEATURES:oil_temp_avg::FLOAT) as AVG_OIL_TEMP,
    AVG(FEATURES:h2_avg::FLOAT) as AVG_H2,
    AVG(FEATURES:vibration_avg::FLOAT) as AVG_VIBRATION,
    AVG(FEATURES:load_util_avg::FLOAT) as AVG_LOAD_UTIL,
    AVG(FEATURES:days_since_maintenance::FLOAT) as AVG_DAYS_SINCE_MAINT,
    AVG(FEATURES:overall_health_index::FLOAT) as AVG_HEALTH_INDEX,
    AVG(FEATURES:oil_temp_trend_pct::FLOAT) as AVG_OIL_TEMP_TREND,
    AVG(FEATURES:h2_trend_pct::FLOAT) as AVG_H2_TREND
    
FROM TRAINING_DATA
GROUP BY FAILURE_WITHIN_30_DAYS;

SELECT 
    CASE WHEN FAILURE_WITHIN_30_DAYS THEN 'FAILED ASSETS' ELSE 'HEALTHY ASSETS' END as CATEGORY,
    RECORD_COUNT,
    ROUND(AVG_OIL_TEMP, 2) as AVG_OIL_TEMP_C,
    ROUND(AVG_H2, 2) as AVG_H2_PPM,
    ROUND(AVG_VIBRATION, 2) as AVG_VIBRATION,
    ROUND(AVG_LOAD_UTIL * 100, 2) as AVG_LOAD_UTIL_PCT,
    ROUND(AVG_DAYS_SINCE_MAINT, 0) as AVG_DAYS_SINCE_MAINT,
    ROUND(AVG_HEALTH_INDEX, 2) as AVG_HEALTH_INDEX,
    ROUND(AVG_OIL_TEMP_TREND, 2) as AVG_TEMP_TREND_PCT,
    ROUND(AVG_H2_TREND, 2) as AVG_H2_TREND_PCT
FROM FEATURE_COMPARISON
ORDER BY FAILURE_WITHIN_30_DAYS DESC;

-- =============================================================================
-- SECTION 4: CLASS IMBALANCE HANDLING (OPTIONAL)
-- =============================================================================

-- Create a balanced training set using oversampling of minority class
-- This is optional - can be used if failure rate is very low (<5%)

CREATE OR REPLACE TABLE TRAINING_DATA_BALANCED AS
WITH failure_samples AS (
    SELECT * FROM TRAINING_DATA WHERE FAILURE_WITHIN_30_DAYS = TRUE
),
non_failure_samples AS (
    SELECT * FROM TRAINING_DATA WHERE FAILURE_WITHIN_30_DAYS = FALSE
),
sample_counts AS (
    SELECT 
        (SELECT COUNT(*) FROM failure_samples) as FAILURE_CNT,
        (SELECT COUNT(*) FROM non_failure_samples) as NON_FAILURE_CNT
),
replication_sequence AS (
    -- Use fixed GENERATOR with max 100 replications
    -- This is a workaround since GENERATOR requires constant values
    SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) as REPLICATION_NUM
    FROM TABLE(GENERATOR(ROWCOUNT => 100))
),
-- Replicate failure samples to match non-failure samples
replicated_failures AS (
    SELECT 
        fs.ASSET_ID,
        fs.SNAPSHOT_DATE,
        fs.FAILURE_WITHIN_30_DAYS,
        fs.DAYS_TO_FAILURE,
        fs.FAILURE_TYPE,
        fs.FEATURES,
        fs.TRAINING_SET,
        ROW_NUMBER() OVER (ORDER BY RANDOM()) as RN
    FROM failure_samples fs
    CROSS JOIN replication_sequence rs
    CROSS JOIN sample_counts sc
    WHERE rs.REPLICATION_NUM <= GREATEST(1, FLOOR(sc.NON_FAILURE_CNT::FLOAT / NULLIF(sc.FAILURE_CNT, 0)))
)
SELECT 
    ASSET_ID,
    SNAPSHOT_DATE,
    FAILURE_WITHIN_30_DAYS,
    DAYS_TO_FAILURE,
    FAILURE_TYPE,
    FEATURES,
    TRAINING_SET
FROM non_failure_samples
UNION ALL
SELECT 
    ASSET_ID,
    SNAPSHOT_DATE,
    FAILURE_WITHIN_30_DAYS,
    DAYS_TO_FAILURE,
    FAILURE_TYPE,
    FEATURES,
    TRAINING_SET
FROM replicated_failures
WHERE RN <= (SELECT NON_FAILURE_CNT FROM sample_counts);

-- Show balanced dataset statistics
SELECT 'Balanced Training Data' as CATEGORY,
       COUNT(*) as TOTAL_RECORDS,
       COUNT_IF(FAILURE_WITHIN_30_DAYS) as FAILURE_RECORDS,
       COUNT_IF(NOT FAILURE_WITHIN_30_DAYS) as NON_FAILURE_RECORDS,
       ROUND(COUNT_IF(FAILURE_WITHIN_30_DAYS) * 100.0 / COUNT(*), 2) as FAILURE_PCT
FROM TRAINING_DATA_BALANCED;

-- =============================================================================
-- SECTION 5: EXPORT TRAINING DATA FOR MODEL DEVELOPMENT
-- =============================================================================

-- Export to stage for use with Snowpark ML or external tools
-- CREATE OR REPLACE STAGE ML.TRAINING_DATA_STAGE;

/*
-- Example: Export training data to stage as Parquet
COPY INTO @ML.TRAINING_DATA_STAGE/training_data_
FROM (
    SELECT 
        ASSET_ID,
        SNAPSHOT_DATE,
        FAILURE_WITHIN_30_DAYS::NUMBER as TARGET_FAILURE,
        DAYS_TO_FAILURE,
        TRAINING_SET,
        FEATURES:oil_temp_avg::FLOAT as FEAT_OIL_TEMP_AVG,
        FEATURES:oil_temp_max::FLOAT as FEAT_OIL_TEMP_MAX,
        FEATURES:h2_avg::FLOAT as FEAT_H2_AVG,
        FEATURES:h2_max::FLOAT as FEAT_H2_MAX,
        FEATURES:vibration_avg::FLOAT as FEAT_VIBRATION_AVG,
        FEATURES:load_util_avg::FLOAT as FEAT_LOAD_UTIL_AVG,
        FEATURES:load_util_peak::FLOAT as FEAT_LOAD_UTIL_PEAK,
        FEATURES:thermal_rise_avg::FLOAT as FEAT_THERMAL_RISE_AVG,
        FEATURES:combustible_gases::FLOAT as FEAT_COMBUSTIBLE_GASES,
        FEATURES:operating_hours::NUMBER as FEAT_OPERATING_HOURS,
        FEATURES:asset_age_years::FLOAT as FEAT_ASSET_AGE_YEARS,
        FEATURES:days_since_maintenance::NUMBER as FEAT_DAYS_SINCE_MAINT,
        FEATURES:capacity_mva::NUMBER as FEAT_CAPACITY_MVA,
        FEATURES:criticality_score::NUMBER as FEAT_CRITICALITY_SCORE,
        FEATURES:customers_affected::NUMBER as FEAT_CUSTOMERS_AFFECTED,
        FEATURES:oil_quality_index::FLOAT as FEAT_OIL_QUALITY_INDEX,
        FEATURES:thermal_stress_index::FLOAT as FEAT_THERMAL_STRESS_INDEX,
        FEATURES:electrical_stress_index::FLOAT as FEAT_ELECTRICAL_STRESS_INDEX,
        FEATURES:mechanical_stress_index::FLOAT as FEAT_MECHANICAL_STRESS_INDEX,
        FEATURES:maintenance_effectiveness::NUMBER as FEAT_MAINT_EFFECTIVENESS,
        FEATURES:overall_health_index::FLOAT as FEAT_OVERALL_HEALTH_INDEX,
        FEATURES:oil_temp_trend_pct::FLOAT as FEAT_OIL_TEMP_TREND_PCT,
        FEATURES:h2_trend_pct::FLOAT as FEAT_H2_TREND_PCT
    FROM TRAINING_DATA
)
FILE_FORMAT = (TYPE = PARQUET)
OVERWRITE = TRUE
SINGLE = FALSE
MAX_FILE_SIZE = 104857600;  -- 100MB files
*/

-- =============================================================================
-- SCRIPT COMPLETE
-- =============================================================================

SELECT 'Training data preparation complete!' as STATUS;
SELECT 'Tables created: TRAINING_DATA, TRAINING_DATA_BALANCED' as TABLES;
SELECT 'Records created: ' || (SELECT COUNT(*) FROM TRAINING_DATA)::VARCHAR as TRAINING_RECORDS;
SELECT 'Failure rate: ' || (SELECT ROUND(COUNT_IF(FAILURE_WITHIN_30_DAYS) * 100.0 / COUNT(*), 2) FROM TRAINING_DATA)::VARCHAR || '%' as FAILURE_RATE;
SELECT 'Next Step: Run 03_model_training_stored_proc.sql' as NEXT_STEP;


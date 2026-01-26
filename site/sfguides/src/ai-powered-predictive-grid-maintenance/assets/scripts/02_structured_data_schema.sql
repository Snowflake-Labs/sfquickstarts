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
 * Database Setup Script - Part 1: Core Schema
 * 
 * Purpose: Create complete database schema for Grid Reliability system
 * Database: UTILITIES_GRID_RELIABILITY
 * Warehouse: XS (GRID_RELIABILITY_WH)
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-15
 * Version: 1.0
 ******************************************************************************/

-- =============================================================================
-- SECTION 1: DATABASE AND SCHEMA CREATION
-- =============================================================================

CREATE DATABASE IF NOT EXISTS UTILITIES_GRID_RELIABILITY
    COMMENT = 'Grid Reliability and Predictive Maintenance AI System';

USE DATABASE UTILITIES_GRID_RELIABILITY;

-- Create Schemas following medallion architecture
CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Bronze layer - Raw data ingestion from OT sensors and IT systems';

CREATE SCHEMA IF NOT EXISTS FEATURES
    COMMENT = 'Silver layer - Engineered features for ML models';

CREATE SCHEMA IF NOT EXISTS ML
    COMMENT = 'ML artifacts - models, predictions, training data';

CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Gold layer - Business analytics and reliability metrics';

CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'Temporary staging area for data ingestion';

-- =============================================================================
-- SECTION 2: COMPUTE WAREHOUSE
-- =============================================================================

CREATE WAREHOUSE IF NOT EXISTS GRID_RELIABILITY_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Compute warehouse for grid reliability workloads';

USE WAREHOUSE GRID_RELIABILITY_WH;

-- =============================================================================
-- SECTION 3: RAW SCHEMA TABLES
-- =============================================================================

USE SCHEMA RAW;

-- -----------------------------------------------------------------------------
-- Table: ASSET_MASTER
-- Purpose: Master inventory of all monitored T&D and substation assets
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE ASSET_MASTER (
    ASSET_ID VARCHAR(50) PRIMARY KEY,
    ASSET_TYPE VARCHAR(50) NOT NULL,
    ASSET_SUBTYPE VARCHAR(50),
    MANUFACTURER VARCHAR(100),
    MODEL VARCHAR(100),
    SERIAL_NUMBER VARCHAR(100),
    INSTALL_DATE DATE,
    EXPECTED_LIFE_YEARS NUMBER(3),
    LOCATION_SUBSTATION VARCHAR(100),
    LOCATION_CITY VARCHAR(100),
    LOCATION_COUNTY VARCHAR(100),
    LOCATION_LAT NUMBER(10,6),
    LOCATION_LON NUMBER(10,6),
    VOLTAGE_RATING_KV NUMBER(10,2),
    CAPACITY_MVA NUMBER(10,2),
    CRITICALITY_SCORE NUMBER(3),
    CUSTOMERS_AFFECTED NUMBER(10),
    REPLACEMENT_COST_USD NUMBER(12,2),
    LAST_MAINTENANCE_DATE DATE,
    STATUS VARCHAR(20) DEFAULT 'ACTIVE',
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    METADATA VARIANT
) 
COMMENT = 'Master inventory of T&D and substation assets with location and criticality data'
CLUSTER BY (ASSET_TYPE, STATUS);

-- -----------------------------------------------------------------------------
-- Table: SENSOR_READINGS
-- Purpose: Time-series operational data from OT sensors (SCADA, DCS, IoT)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SENSOR_READINGS (
    READING_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    READING_TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    
    -- Thermal Measurements
    OIL_TEMPERATURE_C NUMBER(5,2),
    WINDING_TEMPERATURE_C NUMBER(5,2),
    AMBIENT_TEMP_C NUMBER(5,2),
    BUSHING_TEMP_C NUMBER(5,2),
    
    -- Electrical Measurements
    LOAD_CURRENT_A NUMBER(10,2),
    LOAD_VOLTAGE_KV NUMBER(10,2),
    POWER_FACTOR NUMBER(5,4),
    PARTIAL_DISCHARGE_PC NUMBER(8,2),
    
    -- Environmental
    HUMIDITY_PCT NUMBER(5,2),
    
    -- Mechanical/Vibration
    VIBRATION_MM_S NUMBER(8,4),
    ACOUSTIC_DB NUMBER(6,2),  -- Increased from (5,2) to handle values > 999.99
    
    -- Dissolved Gas Analysis (DGA)
    DISSOLVED_H2_PPM NUMBER(10,2),
    DISSOLVED_CO_PPM NUMBER(10,2),
    DISSOLVED_CO2_PPM NUMBER(10,2),
    DISSOLVED_CH4_PPM NUMBER(10,2),
    
    -- Operational
    TAP_POSITION NUMBER(3),
    
    -- Metadata
    INGESTION_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_SENSOR_ASSET FOREIGN KEY (ASSET_ID) REFERENCES ASSET_MASTER(ASSET_ID)
)
COMMENT = 'Time-series sensor data from OT systems - high volume table'
CLUSTER BY (READING_TIMESTAMP, ASSET_ID);

-- Note: Snowflake regular tables don't support indexes. 
-- CLUSTER BY provides query optimization instead.

-- -----------------------------------------------------------------------------
-- Table: MAINTENANCE_HISTORY
-- Purpose: Historical maintenance and inspection records
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE MAINTENANCE_HISTORY (
    MAINTENANCE_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    MAINTENANCE_DATE DATE NOT NULL,
    MAINTENANCE_TYPE VARCHAR(50) NOT NULL, -- INSPECTION, REPAIR, REPLACEMENT, PREVENTIVE
    DESCRIPTION VARCHAR(5000),
    TECHNICIAN VARCHAR(100),
    COST_USD NUMBER(12,2),
    DOWNTIME_HOURS NUMBER(5,2),
    OUTCOME VARCHAR(50), -- SUCCESS, PARTIAL, FAILED
    PARTS_REPLACED VARIANT,
    FINDINGS VARIANT,
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_MAINT_ASSET FOREIGN KEY (ASSET_ID) REFERENCES ASSET_MASTER(ASSET_ID)
)
COMMENT = 'Historical maintenance work orders and inspection records'
CLUSTER BY (MAINTENANCE_DATE, ASSET_ID);

-- -----------------------------------------------------------------------------
-- Table: FAILURE_EVENTS
-- Purpose: Historical asset failure incidents for model training
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE FAILURE_EVENTS (
    EVENT_ID VARCHAR(50) PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    FAILURE_TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    FAILURE_TYPE VARCHAR(100) NOT NULL,
    ROOT_CAUSE VARCHAR(5000),
    CUSTOMERS_AFFECTED NUMBER(10),
    OUTAGE_DURATION_HOURS NUMBER(5,2),
    REPAIR_COST_USD NUMBER(12,2),
    REPLACEMENT_FLAG BOOLEAN DEFAULT FALSE,
    PREVENTABLE_FLAG BOOLEAN,
    ADVANCED_WARNING_DAYS NUMBER(5),
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_FAILURE_ASSET FOREIGN KEY (ASSET_ID) REFERENCES ASSET_MASTER(ASSET_ID)
)
COMMENT = 'Historical failure incidents with root cause and impact data'
CLUSTER BY (FAILURE_TIMESTAMP);

-- -----------------------------------------------------------------------------
-- Table: WEATHER_DATA
-- Purpose: Environmental conditions from weather stations
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE WEATHER_DATA (
    WEATHER_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    LOCATION_LAT NUMBER(10,6) NOT NULL,
    LOCATION_LON NUMBER(10,6) NOT NULL,
    OBSERVATION_TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    TEMPERATURE_C NUMBER(5,2),
    HUMIDITY_PCT NUMBER(5,2),
    WIND_SPEED_MPS NUMBER(5,2),
    PRECIPITATION_MM NUMBER(5,2),
    SOLAR_RADIATION_WM2 NUMBER(8,2),
    HEAT_INDEX_C NUMBER(5,2),
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Weather station data for environmental context'
CLUSTER BY (OBSERVATION_TIMESTAMP, LOCATION_LAT, LOCATION_LON);

-- -----------------------------------------------------------------------------
-- Table: SCADA_EVENTS
-- Purpose: Operational events and alarms from SCADA systems
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SCADA_EVENTS (
    EVENT_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    EVENT_TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    EVENT_TYPE VARCHAR(50) NOT NULL, -- ALARM, WARNING, INFO, ERROR
    EVENT_CODE VARCHAR(20),
    EVENT_DESCRIPTION VARCHAR(1000),
    SEVERITY NUMBER(1), -- 1=Low, 5=Critical
    ACKNOWLEDGED BOOLEAN DEFAULT FALSE,
    ACKNOWLEDGED_BY VARCHAR(100),
    ACKNOWLEDGED_TS TIMESTAMP_NTZ,
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_EVENT_ASSET FOREIGN KEY (ASSET_ID) REFERENCES ASSET_MASTER(ASSET_ID)
)
COMMENT = 'SCADA operational events and alarms'
CLUSTER BY (EVENT_TIMESTAMP, ASSET_ID);

-- =============================================================================
-- SECTION 4: ML SCHEMA TABLES
-- =============================================================================

USE SCHEMA ML;

-- -----------------------------------------------------------------------------
-- Table: TRAINING_DATA
-- Purpose: Labeled dataset for ML model training
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE TRAINING_DATA (
    RECORD_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    SNAPSHOT_DATE DATE NOT NULL,
    
    -- Target Labels
    FAILURE_WITHIN_30_DAYS BOOLEAN NOT NULL,
    DAYS_TO_FAILURE NUMBER(10),
    FAILURE_TYPE VARCHAR(100),
    
    -- Features (stored as VARIANT for flexibility)
    FEATURES VARIANT NOT NULL,
    
    -- Metadata
    TRAINING_SET VARCHAR(20), -- TRAIN, TEST, VALIDATION
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Labeled training data for supervised learning models'
CLUSTER BY (SNAPSHOT_DATE, ASSET_ID);

-- -----------------------------------------------------------------------------
-- Table: MODEL_REGISTRY
-- Purpose: Model metadata, versioning, and artifacts
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE MODEL_REGISTRY (
    MODEL_ID VARCHAR(50) PRIMARY KEY,
    MODEL_NAME VARCHAR(100) NOT NULL,
    MODEL_TYPE VARCHAR(50) NOT NULL, -- CLASSIFICATION, REGRESSION, ANOMALY
    ALGORITHM VARCHAR(50) NOT NULL,
    VERSION VARCHAR(20) NOT NULL,
    TRAINING_DATE TIMESTAMP_NTZ NOT NULL,
    MODEL_OBJECT VARCHAR(16777216), -- Serialized model
    MODEL_STAGE VARCHAR(16777216), -- Snowflake stage path for model file
    FEATURE_SCHEMA VARIANT,
    HYPERPARAMETERS VARIANT,
    TRAINING_METRICS VARIANT,
    STATUS VARCHAR(20) DEFAULT 'TRAINING', -- TRAINING, TESTING, PRODUCTION, RETIRED
    CREATED_BY VARCHAR(100),
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    DEPLOYED_TS TIMESTAMP_NTZ
)
COMMENT = 'ML model registry with versions and metadata';

-- -----------------------------------------------------------------------------
-- Table: MODEL_PREDICTIONS
-- Purpose: Real-time model inference results
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE MODEL_PREDICTIONS (
    PREDICTION_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    ASSET_ID VARCHAR(50) NOT NULL,
    PREDICTION_TIMESTAMP TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    MODEL_ID VARCHAR(50) NOT NULL,
    
    -- Model Outputs
    ANOMALY_SCORE NUMBER(5,4), -- 0-1 scale
    FAILURE_PROBABILITY NUMBER(5,4), -- 0-1 scale
    PREDICTED_RUL_DAYS NUMBER(10,2),
    RISK_SCORE NUMBER(5,2), -- 0-100 composite score
    CONFIDENCE NUMBER(5,4), -- 0-1 scale
    
    -- Features Used
    FEATURE_VALUES VARIANT,
    
    -- Alert Status
    ALERT_GENERATED BOOLEAN DEFAULT FALSE,
    ALERT_LEVEL VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_PRED_ASSET FOREIGN KEY (ASSET_ID) REFERENCES RAW.ASSET_MASTER(ASSET_ID),
    CONSTRAINT FK_PRED_MODEL FOREIGN KEY (MODEL_ID) REFERENCES MODEL_REGISTRY(MODEL_ID)
)
COMMENT = 'Real-time ML predictions and risk scores'
CLUSTER BY (PREDICTION_TIMESTAMP, ASSET_ID);

-- -----------------------------------------------------------------------------
-- Table: MODEL_PERFORMANCE
-- Purpose: Model evaluation metrics over time
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE MODEL_PERFORMANCE (
    EVAL_ID VARCHAR(50) PRIMARY KEY,
    MODEL_ID VARCHAR(50) NOT NULL,
    EVAL_DATE DATE NOT NULL,
    DATASET_TYPE VARCHAR(20) NOT NULL, -- TRAIN, TEST, PRODUCTION
    
    -- Classification Metrics
    ACCURACY NUMBER(5,4),
    PRECISION NUMBER(5,4),
    RECALL NUMBER(5,4),
    F1_SCORE NUMBER(5,4),
    ROC_AUC NUMBER(5,4),
    
    -- Regression Metrics
    MAE NUMBER(10,4),
    RMSE NUMBER(10,4),
    R2_SCORE NUMBER(5,4),
    
    -- Business Metrics
    TRUE_POSITIVES NUMBER(10),
    FALSE_POSITIVES NUMBER(10),
    TRUE_NEGATIVES NUMBER(10),
    FALSE_NEGATIVES NUMBER(10),
    
    -- Cost Metrics
    COST_WEIGHTED_ACCURACY NUMBER(5,4),
    
    CREATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_PERF_MODEL FOREIGN KEY (MODEL_ID) REFERENCES MODEL_REGISTRY(MODEL_ID)
)
COMMENT = 'Model performance tracking and evaluation metrics';

-- -----------------------------------------------------------------------------
-- Table: FEATURE_IMPORTANCE
-- Purpose: Model explainability - feature importance scores
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE FEATURE_IMPORTANCE (
    IMPORTANCE_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    MODEL_ID VARCHAR(50) NOT NULL,
    FEATURE_NAME VARCHAR(100) NOT NULL,
    IMPORTANCE_SCORE NUMBER(10,6),
    IMPORTANCE_RANK NUMBER(10),
    COMPUTATION_DATE DATE NOT NULL,
    
    CONSTRAINT FK_IMPORTANCE_MODEL FOREIGN KEY (MODEL_ID) REFERENCES MODEL_REGISTRY(MODEL_ID)
)
COMMENT = 'Feature importance scores for model explainability';

-- =============================================================================
-- SECTION 5: STAGING SCHEMA TABLES
-- =============================================================================

USE SCHEMA STAGING;

-- -----------------------------------------------------------------------------
-- Table: SENSOR_STAGING
-- Purpose: Temporary landing zone for incoming sensor data
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE SENSOR_STAGING (
    STAGING_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    RAW_DATA VARIANT NOT NULL,
    SOURCE_FILE VARCHAR(500),
    INGESTION_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PROCESSED BOOLEAN DEFAULT FALSE,
    ERROR_MESSAGE VARCHAR(5000)
)
COMMENT = 'Staging table for sensor data ingestion via Snowpipe';

-- -----------------------------------------------------------------------------
-- Table: ASSET_STAGING
-- Purpose: Temporary landing zone for asset master data updates
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE ASSET_STAGING (
    STAGING_ID NUMBER(38,0) AUTOINCREMENT PRIMARY KEY,
    RAW_DATA VARIANT NOT NULL,
    SOURCE_FILE VARCHAR(500),
    INGESTION_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PROCESSED BOOLEAN DEFAULT FALSE,
    ERROR_MESSAGE VARCHAR(5000)
)
COMMENT = 'Staging table for asset master data updates';

-- =============================================================================
-- SECTION 6: HELPER FUNCTIONS
-- =============================================================================

USE SCHEMA RAW;

-- -----------------------------------------------------------------------------
-- Function: CALCULATE_ASSET_AGE
-- Purpose: Calculate asset age in years from install date
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION CALCULATE_ASSET_AGE(INSTALL_DATE DATE)
RETURNS NUMBER(5,2)
LANGUAGE SQL
AS
$$
    DATEDIFF(day, INSTALL_DATE, CURRENT_DATE()) / 365.25
$$;

-- -----------------------------------------------------------------------------
-- Function: CALCULATE_DAYS_SINCE_MAINTENANCE
-- Purpose: Calculate days since last maintenance
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION CALCULATE_DAYS_SINCE_MAINTENANCE(LAST_MAINT_DATE DATE)
RETURNS NUMBER(10)
LANGUAGE SQL
AS
$$
    DATEDIFF(day, LAST_MAINT_DATE, CURRENT_DATE())
$$;

-- =============================================================================
-- SECTION 7: DATA QUALITY CONSTRAINTS
-- =============================================================================

-- Note: Snowflake regular tables don't support CHECK constraints.
-- Data quality validation should be implemented using:
-- 1. Application-level validation before data insertion
-- 2. ETL/ELT validation in data pipelines
-- 3. Snowflake Streams + Tasks for monitoring and alerting
-- 4. dbt tests or similar data quality frameworks
--
-- Expected data ranges (for documentation):
-- - OIL_TEMPERATURE_C: -50 to 200
-- - HUMIDITY_PCT: 0 to 100
-- - CRITICALITY_SCORE: 0 to 100
-- - RISK_SCORE: 0 to 100

-- =============================================================================
-- SECTION 8: INITIAL DATA SETUP
-- =============================================================================

-- Create a reference table for failure types
USE SCHEMA RAW;

CREATE OR REPLACE TABLE FAILURE_TYPE_REFERENCE (
    FAILURE_TYPE_CODE VARCHAR(20) PRIMARY KEY,
    FAILURE_TYPE_NAME VARCHAR(100),
    DESCRIPTION VARCHAR(500),
    TYPICAL_ROOT_CAUSES VARIANT,
    AVG_REPAIR_COST_USD NUMBER(12,2)
);

INSERT INTO FAILURE_TYPE_REFERENCE 
SELECT 'WINDING_FAIL', 'Winding Failure', 'Insulation breakdown in transformer winding', PARSE_JSON('["Thermal stress", "Electrical stress", "Moisture ingress"]'), 425000
UNION ALL
SELECT 'BUSHING_FAULT', 'Bushing Fault', 'Bushing insulation failure', PARSE_JSON('["Contamination", "Moisture", "Mechanical damage"]'), 85000
UNION ALL
SELECT 'OIL_LEAK', 'Oil Leak', 'Loss of transformer oil', PARSE_JSON('["Gasket failure", "Corrosion", "Physical damage"]'), 45000
UNION ALL
SELECT 'TAP_CHANGER', 'Tap Changer Failure', 'On-load tap changer malfunction', PARSE_JSON('["Contact wear", "Mechanical wear", "Contamination"]'), 125000
UNION ALL
SELECT 'COOLING_FAIL', 'Cooling System Failure', 'Cooling fan or pump failure', PARSE_JSON('["Motor failure", "Mechanical wear", "Control circuit"]'), 35000
UNION ALL
SELECT 'CORE_FAIL', 'Core Failure', 'Magnetic core damage', PARSE_JSON('["Core overheating", "Manufacturing defect"]'), 450000;

-- =============================================================================
-- SECTION 9: PERMISSIONS AND ROLES
-- =============================================================================

-- Create roles for different user types
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS GRID_ADMIN COMMENT = 'Full admin access to grid reliability database';
CREATE ROLE IF NOT EXISTS GRID_DATA_ENGINEER COMMENT = 'Data engineering and ETL development';
CREATE ROLE IF NOT EXISTS GRID_ML_ENGINEER COMMENT = 'ML model development and training';
CREATE ROLE IF NOT EXISTS GRID_ANALYST COMMENT = 'Read-only analyst access';
CREATE ROLE IF NOT EXISTS GRID_OPERATOR COMMENT = 'Operations team access to dashboard and predictions';

-- Grant privileges
GRANT ALL ON DATABASE UTILITIES_GRID_RELIABILITY TO ROLE GRID_ADMIN;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.RAW TO ROLE GRID_ADMIN;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.FEATURES TO ROLE GRID_ADMIN;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.ML TO ROLE GRID_ADMIN;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.ANALYTICS TO ROLE GRID_ADMIN;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.STAGING TO ROLE GRID_ADMIN;

-- Data Engineer permissions
GRANT USAGE ON DATABASE UTILITIES_GRID_RELIABILITY TO ROLE GRID_DATA_ENGINEER;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.RAW TO ROLE GRID_DATA_ENGINEER;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.STAGING TO ROLE GRID_DATA_ENGINEER;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA UTILITIES_GRID_RELIABILITY.RAW TO ROLE GRID_DATA_ENGINEER;

-- ML Engineer permissions
GRANT USAGE ON DATABASE UTILITIES_GRID_RELIABILITY TO ROLE GRID_ML_ENGINEER;
GRANT USAGE ON SCHEMA UTILITIES_GRID_RELIABILITY.RAW TO ROLE GRID_ML_ENGINEER;
GRANT USAGE ON SCHEMA UTILITIES_GRID_RELIABILITY.FEATURES TO ROLE GRID_ML_ENGINEER;
GRANT ALL ON SCHEMA UTILITIES_GRID_RELIABILITY.ML TO ROLE GRID_ML_ENGINEER;
GRANT SELECT ON ALL TABLES IN SCHEMA UTILITIES_GRID_RELIABILITY.RAW TO ROLE GRID_ML_ENGINEER;
GRANT SELECT ON ALL VIEWS IN SCHEMA UTILITIES_GRID_RELIABILITY.FEATURES TO ROLE GRID_ML_ENGINEER;

-- Analyst permissions (read-only)
GRANT USAGE ON DATABASE UTILITIES_GRID_RELIABILITY TO ROLE GRID_ANALYST;
GRANT USAGE ON SCHEMA UTILITIES_GRID_RELIABILITY.ANALYTICS TO ROLE GRID_ANALYST;
GRANT SELECT ON ALL VIEWS IN SCHEMA UTILITIES_GRID_RELIABILITY.ANALYTICS TO ROLE GRID_ANALYST;

-- Operator permissions
GRANT USAGE ON DATABASE UTILITIES_GRID_RELIABILITY TO ROLE GRID_OPERATOR;
GRANT USAGE ON SCHEMA UTILITIES_GRID_RELIABILITY.ANALYTICS TO ROLE GRID_OPERATOR;
GRANT SELECT ON ALL VIEWS IN SCHEMA UTILITIES_GRID_RELIABILITY.ANALYTICS TO ROLE GRID_OPERATOR;
GRANT SELECT ON TABLE UTILITIES_GRID_RELIABILITY.ML.MODEL_PREDICTIONS TO ROLE GRID_OPERATOR;

-- Warehouse usage
GRANT USAGE ON WAREHOUSE GRID_RELIABILITY_WH TO ROLE GRID_ADMIN;
GRANT USAGE ON WAREHOUSE GRID_RELIABILITY_WH TO ROLE GRID_DATA_ENGINEER;
GRANT USAGE ON WAREHOUSE GRID_RELIABILITY_WH TO ROLE GRID_ML_ENGINEER;
GRANT USAGE ON WAREHOUSE GRID_RELIABILITY_WH TO ROLE GRID_ANALYST;
GRANT USAGE ON WAREHOUSE GRID_RELIABILITY_WH TO ROLE GRID_OPERATOR;

-- =============================================================================
-- SCRIPT COMPLETE
-- =============================================================================

SELECT 'Database schema creation complete!' as STATUS;
SELECT 'Database: UTILITIES_GRID_RELIABILITY' as DATABASE_NAME;
SELECT 'Warehouse: GRID_RELIABILITY_WH (X-SMALL)' as WAREHOUSE;
SELECT 'Next Step: Run 02_create_stages.sql' as NEXT_STEP;



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
 * GRID RELIABILITY & PREDICTIVE MAINTENANCE - Infrastructure Setup
 * 
 * Purpose: Create database, warehouse, schemas, stages, and file formats
 * Execution: Run this first - creates all foundational infrastructure
 * 
 * Author: Grid Reliability AI/ML Team
 * Version: 2.0 (Consolidated for Solution Page)
 ******************************************************************************/

-- =============================================================================
-- SECTION 0: ACCOUNT SETTINGS FOR CORTEX
-- =============================================================================

-- Enable cross-region Cortex inference for regions without local Cortex availability
-- Required for Cortex Search, Cortex Analyst, and Snowflake Intelligence features
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- =============================================================================
-- SECTION 1: DATABASE AND WAREHOUSE
-- =============================================================================

CREATE DATABASE IF NOT EXISTS UTILITIES_GRID_RELIABILITY
    COMMENT = 'Grid Reliability and Predictive Maintenance AI System';

USE DATABASE UTILITIES_GRID_RELIABILITY;

CREATE WAREHOUSE IF NOT EXISTS GRID_RELIABILITY_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Compute warehouse for grid reliability workloads';

USE WAREHOUSE GRID_RELIABILITY_WH;

-- =============================================================================
-- SECTION 2: SCHEMAS (Medallion Architecture)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Bronze layer - Raw data ingestion from OT sensors and IT systems';

CREATE SCHEMA IF NOT EXISTS FEATURES
    COMMENT = 'Silver layer - Engineered features for ML models';

CREATE SCHEMA IF NOT EXISTS ML
    COMMENT = 'ML artifacts - models, predictions, training data';

CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Gold layer - Business analytics and reliability metrics';

CREATE SCHEMA IF NOT EXISTS UNSTRUCTURED
    COMMENT = 'Unstructured data - Documents, images, videos, CV detections';

CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT = 'Temporary staging area for data ingestion';

-- =============================================================================
-- SECTION 3: FILE FORMATS
-- =============================================================================

USE SCHEMA RAW;

-- CSV Format for Asset Master Data
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE = 'CSV'
    COMPRESSION = 'AUTO'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    DATE_FORMAT = 'AUTO'
    TIMESTAMP_FORMAT = 'AUTO'
    NULL_IF = ('NULL', 'null', '');

-- JSON Format for Sensor Data
CREATE OR REPLACE FILE FORMAT JSON_FORMAT
    TYPE = 'JSON'
    COMPRESSION = 'AUTO'
    STRIP_OUTER_ARRAY = TRUE
    STRIP_NULL_VALUES = FALSE;

-- Parquet Format for Bulk Historical Data
CREATE OR REPLACE FILE FORMAT PARQUET_FORMAT
    TYPE = 'PARQUET'
    COMPRESSION = 'SNAPPY';

-- =============================================================================
-- SECTION 4: INTERNAL STAGES
-- =============================================================================

-- Sensor Data Stage
CREATE OR REPLACE STAGE SENSOR_DATA_STAGE
    FILE_FORMAT = JSON_FORMAT
    COMMENT = 'Internal stage for sensor data ingestion';

-- Asset Data Stage
CREATE OR REPLACE STAGE ASSET_DATA_STAGE
    FILE_FORMAT = CSV_FORMAT
    COMMENT = 'Internal stage for asset master data';

-- Maintenance Data Stage
CREATE OR REPLACE STAGE MAINTENANCE_DATA_STAGE
    FILE_FORMAT = CSV_FORMAT
    COMMENT = 'Internal stage for maintenance records';

-- Weather Data Stage
CREATE OR REPLACE STAGE WEATHER_DATA_STAGE
    FILE_FORMAT = CSV_FORMAT
    COMMENT = 'Internal stage for weather data';

-- ML Model Artifacts Stage
USE SCHEMA ML;
CREATE OR REPLACE STAGE MODEL_ARTIFACTS_STAGE
    FILE_FORMAT = RAW.PARQUET_FORMAT
    COMMENT = 'Storage for serialized ML models and artifacts';

-- Training Data Stage
CREATE OR REPLACE STAGE TRAINING_DATA_STAGE
    FILE_FORMAT = RAW.PARQUET_FORMAT
    COMMENT = 'Storage for ML training datasets';

-- Semantic Model Stage
USE SCHEMA ANALYTICS;
CREATE OR REPLACE STAGE SEMANTIC_MODEL_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Storage for Cortex Analyst semantic models';

-- =============================================================================
-- SECTION 5: VERIFICATION
-- =============================================================================

SELECT '✅ Infrastructure setup complete!' AS STATUS;
SELECT 
    'Database: UTILITIES_GRID_RELIABILITY' AS OBJECT_1,
    'Warehouse: GRID_RELIABILITY_WH' AS OBJECT_2,
    'Schemas: RAW, FEATURES, ML, ANALYTICS, UNSTRUCTURED, STAGING' AS OBJECT_3;

-- Next Step: Run 02_structured_data_schema.sql

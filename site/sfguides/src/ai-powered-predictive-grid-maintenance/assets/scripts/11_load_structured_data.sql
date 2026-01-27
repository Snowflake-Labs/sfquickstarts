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
 * GRID RELIABILITY & PREDICTIVE MAINTENANCE - Load Structured Data
 * 
 * Purpose: Load structured data (assets, sensors, maintenance history, failures)
 * Prerequisites: 
 *   1. Run scripts 01-10 first
 *   2. Generate data files: python3 python/data_generators/generate_asset_data.py
 *   3. Upload files to stages (see instructions below)
 * 
 * Author: Grid Reliability AI/ML Team
 * Version: 3.0 (Production Ready)
 ******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA RAW;

-- =============================================================================
-- INSTRUCTIONS: Upload data files before running this script
-- =============================================================================
-- Run these commands in SnowSQL or Snowflake CLI from the project root:
--
-- cd generated_data
-- PUT file://asset_master.csv @RAW.ASSET_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
-- PUT file://maintenance_history.csv @RAW.ASSET_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
-- PUT file://failure_events.csv @RAW.ASSET_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
-- PUT file://sensor_readings_batch_*.json @RAW.SENSOR_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
-- cd ..
--
-- Or use the snow CLI:
-- export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin:$PATH"
-- cd generated_data && snow sql -c <connection> -q "USE DATABASE UTILITIES_GRID_RELIABILITY; USE SCHEMA RAW; PUT file://asset_master.csv @ASSET_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;" && cd ..
-- =============================================================================

-- =============================================================================
-- SECTION 1: LOAD ASSET MASTER DATA
-- =============================================================================

COPY INTO ASSET_MASTER (
    ASSET_ID, ASSET_TYPE, ASSET_SUBTYPE, MANUFACTURER, MODEL, SERIAL_NUMBER,
    INSTALL_DATE, EXPECTED_LIFE_YEARS, LOCATION_SUBSTATION, LOCATION_CITY, LOCATION_COUNTY,
    LOCATION_LAT, LOCATION_LON, VOLTAGE_RATING_KV, CAPACITY_MVA, CRITICALITY_SCORE,
    CUSTOMERS_AFFECTED, REPLACEMENT_COST_USD, LAST_MAINTENANCE_DATE, STATUS
)
FROM (
    SELECT 
        $1::VARCHAR,
        $2::VARCHAR,
        $3::VARCHAR,
        $4::VARCHAR,
        $5::VARCHAR,
        $6::VARCHAR,
        $7::DATE,
        $8::NUMBER,
        $9::VARCHAR,
        $10::VARCHAR,
        $11::VARCHAR,
        $12::NUMBER(10,6),
        $13::NUMBER(10,6),
        $14::NUMBER(10,2),
        $15::NUMBER(10,2),
        $16::NUMBER(3),
        $17::NUMBER(10),
        $18::NUMBER(12,2),
        $19::DATE,
        $20::VARCHAR
    FROM @ASSET_DATA_STAGE/asset_master.csv.gz
)
FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL', 'null', '')
)
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

SELECT 'Asset Master loaded: ' || COUNT(*) || ' records' AS STATUS FROM ASSET_MASTER;

-- =============================================================================
-- SECTION 2: LOAD SENSOR READINGS (JSON format - may take 2-3 minutes)
-- =============================================================================

COPY INTO SENSOR_READINGS (
    ASSET_ID, READING_TIMESTAMP, OIL_TEMPERATURE_C, WINDING_TEMPERATURE_C,
    AMBIENT_TEMP_C, BUSHING_TEMP_C, LOAD_CURRENT_A, LOAD_VOLTAGE_KV,
    POWER_FACTOR, PARTIAL_DISCHARGE_PC, HUMIDITY_PCT, VIBRATION_MM_S,
    ACOUSTIC_DB, DISSOLVED_H2_PPM, DISSOLVED_CO_PPM, DISSOLVED_CO2_PPM,
    DISSOLVED_CH4_PPM, TAP_POSITION
)
FROM (
    SELECT 
        $1:ASSET_ID::VARCHAR,
        $1:READING_TIMESTAMP::TIMESTAMP_NTZ,
        $1:OIL_TEMPERATURE_C::NUMBER(5,2),
        $1:WINDING_TEMPERATURE_C::NUMBER(5,2),
        $1:AMBIENT_TEMP_C::NUMBER(5,2),
        $1:BUSHING_TEMP_C::NUMBER(5,2),
        $1:LOAD_CURRENT_A::NUMBER(10,2),
        $1:LOAD_VOLTAGE_KV::NUMBER(10,2),
        $1:POWER_FACTOR::NUMBER(5,4),
        $1:PARTIAL_DISCHARGE_PC::NUMBER(8,2),
        $1:HUMIDITY_PCT::NUMBER(5,2),
        $1:VIBRATION_MM_S::NUMBER(8,4),
        $1:ACOUSTIC_DB::NUMBER(6,2),
        $1:DISSOLVED_H2_PPM::NUMBER(10,2),
        $1:DISSOLVED_CO_PPM::NUMBER(10,2),
        $1:DISSOLVED_CO2_PPM::NUMBER(10,2),
        $1:DISSOLVED_CH4_PPM::NUMBER(10,2),
        $1:TAP_POSITION::NUMBER(3)
    FROM @SENSOR_DATA_STAGE
)
FILE_FORMAT = (
    TYPE = JSON
    STRIP_OUTER_ARRAY = FALSE
)
PATTERN = '.*sensor_readings.*\\.json\\.gz'
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

SELECT 'Sensor Readings loaded: ' || COUNT(*) || ' records' AS STATUS FROM SENSOR_READINGS;

-- =============================================================================
-- SECTION 3: LOAD MAINTENANCE HISTORY
-- =============================================================================

COPY INTO MAINTENANCE_HISTORY (
    MAINTENANCE_ID, ASSET_ID, MAINTENANCE_DATE, MAINTENANCE_TYPE, DESCRIPTION, TECHNICIAN,
    COST_USD, DOWNTIME_HOURS, OUTCOME
)
FROM (
    SELECT 
        $1::VARCHAR,
        $2::VARCHAR,
        $3::DATE,
        $4::VARCHAR,
        $5::VARCHAR,
        $6::VARCHAR,
        $7::NUMBER(12,2),
        $8::NUMBER(5,2),
        $9::VARCHAR
    FROM @ASSET_DATA_STAGE/maintenance_history.csv.gz
)
FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL', 'null', '')
)
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

SELECT 'Maintenance History loaded: ' || COUNT(*) || ' records' AS STATUS FROM MAINTENANCE_HISTORY;

-- =============================================================================
-- SECTION 4: LOAD FAILURE EVENTS
-- =============================================================================

COPY INTO FAILURE_EVENTS (
    EVENT_ID, ASSET_ID, FAILURE_TIMESTAMP, FAILURE_TYPE, ROOT_CAUSE,
    CUSTOMERS_AFFECTED, OUTAGE_DURATION_HOURS, REPAIR_COST_USD,
    REPLACEMENT_FLAG, PREVENTABLE_FLAG, ADVANCED_WARNING_DAYS
)
FROM (
    SELECT 
        $1::VARCHAR,
        $2::VARCHAR,
        $3::TIMESTAMP_NTZ,
        $4::VARCHAR,
        $5::VARCHAR,
        $6::NUMBER(10),
        $7::NUMBER(5,2),
        $8::NUMBER(12,2),
        $9::BOOLEAN,
        $10::BOOLEAN,
        $11::NUMBER(5)
    FROM @ASSET_DATA_STAGE/failure_events.csv.gz
)
FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL', 'null', '')
)
ON_ERROR = 'CONTINUE'
FORCE = TRUE;

SELECT 'Failure Events loaded: ' || COUNT(*) || ' records' AS STATUS FROM FAILURE_EVENTS;

-- =============================================================================
-- SECTION 5: COMPREHENSIVE VERIFICATION
-- =============================================================================

SELECT 
    'ASSET_MASTER' AS TABLE_NAME, 
    COUNT(*) AS ROW_COUNT,
    MIN(CREATED_TS) AS MIN_TIMESTAMP,
    MAX(CREATED_TS) AS MAX_TIMESTAMP
FROM ASSET_MASTER
UNION ALL
SELECT 
    'SENSOR_READINGS', 
    COUNT(*),
    MIN(INGESTION_TS),
    MAX(INGESTION_TS)
FROM SENSOR_READINGS
UNION ALL
SELECT 
    'MAINTENANCE_HISTORY', 
    COUNT(*),
    MIN(CREATED_TS),
    MAX(CREATED_TS)
FROM MAINTENANCE_HISTORY
UNION ALL
SELECT 
    'FAILURE_EVENTS', 
    COUNT(*),
    MIN(CREATED_TS),
    MAX(CREATED_TS)
FROM FAILURE_EVENTS
ORDER BY TABLE_NAME;

-- Expected row counts (demo data):
-- ASSET_MASTER: 100
-- SENSOR_READINGS: ~432,000 (100 assets × 72 readings/day × 60 days)
-- MAINTENANCE_HISTORY: ~100-200
-- FAILURE_EVENTS: ~15

-- Verify sample data
SELECT 'Sample Asset Data:' AS INFO;
SELECT ASSET_ID, ASSET_TYPE, LOCATION_SUBSTATION, STATUS FROM ASSET_MASTER LIMIT 5;

SELECT 'Sample Sensor Data:' AS INFO;
SELECT ASSET_ID, READING_TIMESTAMP, OIL_TEMPERATURE_C, LOAD_CURRENT_A FROM SENSOR_READINGS LIMIT 5;

SELECT 'Structured data loading complete!' AS STATUS;

-- Next Step: Run 12_load_unstructured_data.sql

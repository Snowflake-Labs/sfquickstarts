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
 * GENERATE RECENT SENSOR DATA FOR DASHBOARD
 * 
 * Purpose: Generate sensor readings for the last 30 days to support
 *          dashboard visualization and trend analysis
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2026-01-06
 * Version: 1.0
 *******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA RAW;

-- ============================================================================
-- GENERATE SENSOR READINGS FOR LAST 30 DAYS
-- ============================================================================
-- This creates hourly sensor readings for all active assets
-- with realistic patterns (daily cycles, noise, etc.)

INSERT INTO SENSOR_READINGS (
    ASSET_ID, READING_TIMESTAMP,
    OIL_TEMPERATURE_C, WINDING_TEMPERATURE_C, AMBIENT_TEMP_C, BUSHING_TEMP_C,
    LOAD_CURRENT_A, LOAD_VOLTAGE_KV, POWER_FACTOR,
    PARTIAL_DISCHARGE_PC, HUMIDITY_PCT, VIBRATION_MM_S, ACOUSTIC_DB,
    DISSOLVED_H2_PPM, DISSOLVED_CO_PPM, DISSOLVED_CO2_PPM, DISSOLVED_CH4_PPM,
    TAP_POSITION
)
WITH asset_list AS (
    SELECT ASSET_ID, CAPACITY_MVA
    FROM ASSET_MASTER 
    WHERE STATUS = 'ACTIVE'
    LIMIT 100
),
time_series AS (
    -- Generate hourly timestamps for the last 30 days
    SELECT 
        DATEADD(hour, SEQ4(), DATEADD(day, -30, CURRENT_TIMESTAMP())) as TIMESTAMP_VAL
    FROM TABLE(GENERATOR(ROWCOUNT => 720))  -- 30 days * 24 hours = 720
)
SELECT 
    al.ASSET_ID,
    ts.TIMESTAMP_VAL as READING_TIMESTAMP,
    
    -- Oil Temperature: 50-95°C with daily sinusoidal pattern (peaks at noon)
    60 + UNIFORM(0, 20, RANDOM()) + 10 * SIN(2 * 3.14159 * HOUR(ts.TIMESTAMP_VAL) / 24) as OIL_TEMPERATURE_C,
    
    -- Winding Temperature: typically 5-10°C higher than oil
    65 + UNIFORM(0, 20, RANDOM()) + 10 * SIN(2 * 3.14159 * HOUR(ts.TIMESTAMP_VAL) / 24) as WINDING_TEMPERATURE_C,
    
    -- Ambient Temperature: 15-35°C
    25 + UNIFORM(-10, 10, RANDOM()) as AMBIENT_TEMP_C,
    
    -- Bushing Temperature: similar to oil, slightly lower
    58 + UNIFORM(0, 15, RANDOM()) as BUSHING_TEMP_C,
    
    -- Load Current: varies by time of day (peak load during day, low at night)
    (al.CAPACITY_MVA * 1000 * 0.6) + 
    (al.CAPACITY_MVA * 1000 * 0.3 * SIN(2 * 3.14159 * HOUR(ts.TIMESTAMP_VAL) / 24)) as LOAD_CURRENT_A,
    
    -- Voltage: relatively stable around 138 kV ± 2 kV
    138 + UNIFORM(-2, 2, RANDOM()) as LOAD_VOLTAGE_KV,
    
    -- Power Factor: 0.85-0.95 (healthy range)
    0.90 + UNIFORM(-0.05, 0.05, RANDOM()) as POWER_FACTOR,
    
    -- Partial Discharge: 10-50 pC (low values indicate good insulation)
    UNIFORM(10, 50, RANDOM()) as PARTIAL_DISCHARGE_PC,
    
    -- Humidity: 30-70%
    50 + UNIFORM(-20, 20, RANDOM()) as HUMIDITY_PCT,
    
    -- Vibration: 0.5-3.0 mm/s (normal range)
    1.5 + UNIFORM(-1, 1.5, RANDOM()) as VIBRATION_MM_S,
    
    -- Acoustic: 40-60 dB
    50 + UNIFORM(-10, 10, RANDOM()) as ACOUSTIC_DB,
    
    -- Dissolved Gases (DGA): Low values indicate healthy oil
    UNIFORM(20, 100, RANDOM()) as DISSOLVED_H2_PPM,
    UNIFORM(100, 500, RANDOM()) as DISSOLVED_CO_PPM,
    UNIFORM(500, 2000, RANDOM()) as DISSOLVED_CO2_PPM,
    UNIFORM(5, 50, RANDOM()) as DISSOLVED_CH4_PPM,
    
    -- Tap Position: -10 to +10
    UNIFORM(-10, 10, RANDOM()) as TAP_POSITION
FROM asset_list al
CROSS JOIN time_series ts
WHERE UNIFORM(0, 100, RANDOM()) < 95  -- 95% data availability (some missing for realism)
LIMIT 65000;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 
    'Recent Sensor Data Generated' as STATUS,
    COUNT(*) as TOTAL_READINGS,
    COUNT(DISTINCT ASSET_ID) as ASSETS_WITH_DATA,
    MIN(READING_TIMESTAMP) as OLDEST_READING,
    MAX(READING_TIMESTAMP) as NEWEST_READING,
    DATEDIFF(hour, MAX(READING_TIMESTAMP), CURRENT_TIMESTAMP()) as HOURS_AGO
FROM SENSOR_READINGS
WHERE READING_TIMESTAMP >= DATEADD(day, -30, CURRENT_TIMESTAMP());


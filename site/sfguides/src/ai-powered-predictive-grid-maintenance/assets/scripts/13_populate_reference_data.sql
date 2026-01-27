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
 * POPULATE REFERENCE DATA - SCADA_EVENTS & WEATHER_DATA
 *******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA RAW;

-- ============================================================================
-- POPULATE SCADA_EVENTS  
-- ============================================================================

TRUNCATE TABLE IF EXISTS SCADA_EVENTS;

INSERT INTO SCADA_EVENTS (
    ASSET_ID,
    EVENT_TIMESTAMP,
    EVENT_TYPE,
    EVENT_CODE,
    EVENT_DESCRIPTION,
    SEVERITY,
    ACKNOWLEDGED,
    ACKNOWLEDGED_BY,
    ACKNOWLEDGED_TS
)
WITH asset_list AS (
    SELECT ASSET_ID FROM ASSET_MASTER WHERE STATUS = 'ACTIVE'
),
hourly_sequence AS (
    SELECT DATEADD(hour, -SEQ4(), CURRENT_TIMESTAMP()) as EVENT_TS
    FROM TABLE(GENERATOR(ROWCOUNT => 4320))  -- 180 days * 24 hours
)
SELECT
    al.ASSET_ID,
    hs.EVENT_TS as EVENT_TIMESTAMP,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'ALARM'
        WHEN 2 THEN 'WARNING'  
        WHEN 3 THEN 'ERROR'
        ELSE 'INFO'
    END as EVENT_TYPE,
    'EVT-' || LPAD(UNIFORM(100, 999, RANDOM()), 3, '0') as EVENT_CODE,
    CASE UNIFORM(1, 8, RANDOM())
        WHEN 1 THEN 'High oil temperature detected'
        WHEN 2 THEN 'Load exceeding threshold'
        WHEN 3 THEN 'Cooling system performance degraded'
        WHEN 4 THEN 'Bushing temperature elevated'
        WHEN 5 THEN 'H2 concentration increasing'
        WHEN 6 THEN 'Vibration levels abnormal'
        WHEN 7 THEN 'Partial discharge detected'
        ELSE 'Normal operational status'
    END as EVENT_DESCRIPTION,
    UNIFORM(1, 5, RANDOM()) as SEVERITY,
    CASE WHEN UNIFORM(0, 100, RANDOM()) < 70 THEN TRUE ELSE FALSE END as ACKNOWLEDGED,
    CASE WHEN UNIFORM(0, 100, RANDOM()) < 70 THEN 'OPERATOR-' || LPAD(UNIFORM(1, 15, RANDOM()), 2, '0') ELSE NULL END as ACKNOWLEDGED_BY,
    CASE WHEN UNIFORM(0, 100, RANDOM()) < 70 THEN DATEADD(hour, UNIFORM(1, 24, RANDOM()), hs.EVENT_TS) ELSE NULL END as ACKNOWLEDGED_TS
FROM asset_list al
CROSS JOIN hourly_sequence hs
WHERE UNIFORM(0, 100, RANDOM()) < 5  -- 5% of possible combinations
LIMIT 10000;

SELECT 'SCADA_EVENTS loaded: ' || COUNT(*) || ' records' AS STATUS FROM SCADA_EVENTS;

-- ============================================================================
-- POPULATE WEATHER_DATA
-- ============================================================================

TRUNCATE TABLE IF EXISTS WEATHER_DATA;

INSERT INTO WEATHER_DATA (
    LOCATION_LAT,
    LOCATION_LON,
    OBSERVATION_TIMESTAMP,
    TEMPERATURE_C,
    HUMIDITY_PCT,
    WIND_SPEED_MPS,
    PRECIPITATION_MM,
    SOLAR_RADIATION_WM2,
    HEAT_INDEX_C
)
WITH asset_locations AS (
    SELECT DISTINCT 
        LOCATION_LAT as LAT, 
        LOCATION_LON as LON 
    FROM ASSET_MASTER 
    WHERE STATUS = 'ACTIVE'
),
hourly_sequence AS (
    SELECT DATEADD(hour, -SEQ4(), CURRENT_TIMESTAMP()) as OBS_TS
    FROM TABLE(GENERATOR(ROWCOUNT => 4320))  -- 180 days * 24 hours
)
SELECT
    al.LAT as LOCATION_LAT,
    al.LON as LOCATION_LON,
    hs.OBS_TS as OBSERVATION_TIMESTAMP,
    
    -- Temperature (Florida climate: 15-35°C range with seasonal/daily variation)
    ROUND(25 + 8 * SIN((MONTH(hs.OBS_TS) - 1) * 3.14159 / 6) + 4 * SIN((HOUR(hs.OBS_TS) - 6) * 3.14159 / 12) + UNIFORM(-3, 3, RANDOM()), 2) as TEMPERATURE_C,
    
    -- Humidity (60-90% range)
    ROUND(75 + 10 * SIN((MONTH(hs.OBS_TS) - 1) * 3.14159 / 6) + UNIFORM(-10, 10, RANDOM()), 2) as HUMIDITY_PCT,
    
    -- Wind speed in meters per second (0-12 m/s)
    ROUND(4 + 3 * UNIFORM(0, 1, RANDOM()) + UNIFORM(0, 2, RANDOM()), 2) as WIND_SPEED_MPS,
    
    -- Precipitation (most days dry, occasional rain)
    CASE WHEN UNIFORM(0, 100, RANDOM()) < 15 THEN ROUND(UNIFORM(0.1, 20, RANDOM()), 2) ELSE 0 END as PRECIPITATION_MM,
    
    -- Solar radiation (0-1000 W/m²)
    CASE 
        WHEN HOUR(hs.OBS_TS) BETWEEN 6 AND 18 
        THEN ROUND(1000 * SIN((HOUR(hs.OBS_TS) - 6) * 3.14159 / 12) * UNIFORM(0.5, 1.0, RANDOM()), 2)
        ELSE 0
    END as SOLAR_RADIATION_WM2,
    
    -- Heat index (approximation based on temperature and humidity)
    ROUND(
        25 + 8 * SIN((MONTH(hs.OBS_TS) - 1) * 3.14159 / 6) + 
        4 * SIN((HOUR(hs.OBS_TS) - 6) * 3.14159 / 12) + 
        (75 + 10 * SIN((MONTH(hs.OBS_TS) - 1) * 3.14159 / 6)) * 0.05,  -- Add humidity effect
        2
    ) as HEAT_INDEX_C

FROM asset_locations al
CROSS JOIN hourly_sequence hs
WHERE UNIFORM(0, 100, RANDOM()) < 8  -- Sample 8% for better coverage
LIMIT 15000;

SELECT 'WEATHER_DATA loaded: ' || COUNT(*) || ' records' AS STATUS FROM WEATHER_DATA;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 
    'SCADA_EVENTS' as TABLE_NAME,
    COUNT(*) as TOTAL_RECORDS,
    COUNT(DISTINCT ASSET_ID) as UNIQUE_IDENTIFIERS,
    MIN(EVENT_TIMESTAMP) as EARLIEST,
    MAX(EVENT_TIMESTAMP) as LATEST
FROM SCADA_EVENTS
UNION ALL
SELECT 
    'WEATHER_DATA',
    COUNT(*),
    COUNT(DISTINCT LOCATION_LAT || ',' || LOCATION_LON) as UNIQUE_LOCATIONS,
    MIN(OBSERVATION_TIMESTAMP),
    MAX(OBSERVATION_TIMESTAMP)
FROM WEATHER_DATA;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 
    'SCADA_EVENTS' as TABLE_NAME,
    COUNT(*) as TOTAL_RECORDS,
    COUNT(DISTINCT ASSET_ID) as UNIQUE_IDENTIFIERS,
    MIN(EVENT_TIMESTAMP) as EARLIEST,
    MAX(EVENT_TIMESTAMP) as LATEST
FROM SCADA_EVENTS
UNION ALL
SELECT 
    'WEATHER_DATA',
    COUNT(*),
    COUNT(DISTINCT LOCATION_LAT || ',' || LOCATION_LON) as UNIQUE_LOCATIONS,
    MIN(OBSERVATION_TIMESTAMP),
    MAX(OBSERVATION_TIMESTAMP)
FROM WEATHER_DATA;

SELECT EVENT_TYPE, COUNT(*) as COUNT FROM SCADA_EVENTS GROUP BY EVENT_TYPE ORDER BY COUNT DESC;

SELECT '✅ Reference data complete!' as STATUS;


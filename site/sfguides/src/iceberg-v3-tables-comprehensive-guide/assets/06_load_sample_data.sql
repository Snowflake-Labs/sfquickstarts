-- Snowflake Iceberg V3 Comprehensive Guide
-- Script 06: Load Sample Data
-- ===========================

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_ANALYTICS_DB;
USE SCHEMA RAW;
USE WAREHOUSE FLEET_ANALYTICS_WH;

-- ============================================
-- COPY JSON MAINTENANCE LOGS FROM STAGE
-- ============================================

-- First, verify files are in the stage
LIST @LOGS_STAGE;

-- Load JSON files into MAINTENANCE_LOGS table
COPY INTO MAINTENANCE_LOGS (LOG_ID, VEHICLE_ID, LOG_TIMESTAMP, LOG_DATA, SOURCE_FILE)
FROM (
    SELECT 
        $1:log_id::VARCHAR,
        $1:vehicle_id::VARCHAR,
        $1:log_timestamp::TIMESTAMP_NTZ,
        $1,
        METADATA$FILENAME
    FROM @LOGS_STAGE
)
FILE_FORMAT = (TYPE = 'JSON')
PATTERN = '.*maintenance_log.*\.json'
ON_ERROR = 'CONTINUE';

-- Verify load
SELECT COUNT(*) AS logs_loaded FROM MAINTENANCE_LOGS;
SELECT * FROM MAINTENANCE_LOGS LIMIT 5;

-- ============================================
-- GENERATE ADDITIONAL SAMPLE SENSOR DATA
-- ============================================

-- Insert more time-series sensor data with varied patterns
INSERT INTO SENSOR_READINGS (
    READING_ID, VEHICLE_ID, READING_TIMESTAMP,
    ENGINE_TEMP_F, OIL_PRESSURE_PSI, BATTERY_VOLTAGE,
    FUEL_CONSUMPTION_GPH, TIRE_PRESSURE_FL, TIRE_PRESSURE_FR,
    TIRE_PRESSURE_RL, TIRE_PRESSURE_RR, ODOMETER_MILES
)
SELECT 
    UUID_STRING() AS READING_ID,
    'VH-' || LPAD(MOD(SEQ4(), 100)::VARCHAR, 4, '0') AS VEHICLE_ID,
    -- Create readings at irregular intervals to simulate real sensor data
    TIMESTAMPADD(
        'millisecond', 
        -SEQ4() * 1000 - UNIFORM(0, 500, RANDOM())::INT,
        CURRENT_TIMESTAMP()
    )::TIMESTAMP_NTZ(9) AS READING_TIMESTAMP,
    -- Simulate temperature patterns (higher during daytime)
    180 + 
    30 * SIN(PI() * HOUR(READING_TIMESTAMP) / 12) + 
    UNIFORM(-10, 10, RANDOM()) AS ENGINE_TEMP_F,
    -- Oil pressure varies with engine RPM
    35 + UNIFORM(-5, 10, RANDOM()) AS OIL_PRESSURE_PSI,
    -- Battery voltage
    12.0 + UNIFORM(-0.5, 1.5, RANDOM()) AS BATTERY_VOLTAGE,
    -- Fuel consumption varies by speed
    3 + UNIFORM(0, 5, RANDOM()) AS FUEL_CONSUMPTION_GPH,
    -- Tire pressures with occasional low readings
    CASE WHEN UNIFORM(0, 100, RANDOM()) > 95 THEN 28 + UNIFORM(0, 2, RANDOM())
         ELSE 35 + UNIFORM(-2, 2, RANDOM()) END AS TIRE_PRESSURE_FL,
    35 + UNIFORM(-2, 2, RANDOM()) AS TIRE_PRESSURE_FR,
    35 + UNIFORM(-2, 2, RANDOM()) AS TIRE_PRESSURE_RL,
    35 + UNIFORM(-2, 2, RANDOM()) AS TIRE_PRESSURE_RR,
    -- Odometer increases over time
    50000 + SEQ4() * 0.5 + UNIFORM(0, 0.5, RANDOM()) AS ODOMETER_MILES
FROM TABLE(GENERATOR(ROWCOUNT => 20000));

-- ============================================
-- GENERATE ADDITIONAL LOCATION DATA
-- ============================================

-- Insert more location data with realistic route patterns
INSERT INTO VEHICLE_LOCATIONS (
    LOCATION_ID, VEHICLE_ID, LOCATION_TIMESTAMP,
    LATITUDE, LONGITUDE, LOCATION_POINT,
    ALTITUDE_FT, HEADING_DEGREES, SPEED_MPH, FLEET_REGION
)
WITH base_locations AS (
    SELECT 
        SEQ4() AS seq,
        'VH-' || LPAD(MOD(SEQ4(), 100)::VARCHAR, 4, '0') AS VEHICLE_ID,
        TIMESTAMPADD('second', -SEQ4() * 15, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS LOCATION_TIMESTAMP,
        MOD(SEQ4(), 5) AS region_id,
        SEQ4() * 0.001 AS route_progress
    FROM TABLE(GENERATOR(ROWCOUNT => 10000))
)
SELECT 
    UUID_STRING() AS LOCATION_ID,
    VEHICLE_ID,
    LOCATION_TIMESTAMP,
    -- Create route patterns by slowly varying lat/lon
    CASE region_id
        WHEN 0 THEN 47.60 + SIN(route_progress) * 0.1 + UNIFORM(-0.01, 0.01, RANDOM())
        WHEN 1 THEN 34.05 + SIN(route_progress) * 0.15 + UNIFORM(-0.01, 0.01, RANDOM())
        WHEN 2 THEN 39.74 + SIN(route_progress) * 0.08 + UNIFORM(-0.01, 0.01, RANDOM())
        WHEN 3 THEN 41.88 + SIN(route_progress) * 0.12 + UNIFORM(-0.01, 0.01, RANDOM())
        ELSE 40.71 + SIN(route_progress) * 0.1 + UNIFORM(-0.01, 0.01, RANDOM())
    END AS LATITUDE,
    CASE region_id
        WHEN 0 THEN -122.33 + COS(route_progress) * 0.1 + UNIFORM(-0.01, 0.01, RANDOM())
        WHEN 1 THEN -118.24 + COS(route_progress) * 0.15 + UNIFORM(-0.01, 0.01, RANDOM())
        WHEN 2 THEN -104.99 + COS(route_progress) * 0.08 + UNIFORM(-0.01, 0.01, RANDOM())
        WHEN 3 THEN -87.63 + COS(route_progress) * 0.12 + UNIFORM(-0.01, 0.01, RANDOM())
        ELSE -74.01 + COS(route_progress) * 0.1 + UNIFORM(-0.01, 0.01, RANDOM())
    END AS LONGITUDE,
    ST_POINT(LONGITUDE, LATITUDE) AS LOCATION_POINT,
    100 + UNIFORM(0, 500, RANDOM()) AS ALTITUDE_FT,
    -- Heading follows route direction
    MOD(DEGREES(ATAN2(COS(route_progress + 0.001) - COS(route_progress), 
                       SIN(route_progress + 0.001) - SIN(route_progress))) + 360, 360) AS HEADING_DEGREES,
    -- Speed varies realistically
    CASE 
        WHEN HOUR(LOCATION_TIMESTAMP) BETWEEN 7 AND 9 THEN 15 + UNIFORM(0, 20, RANDOM())  -- Rush hour
        WHEN HOUR(LOCATION_TIMESTAMP) BETWEEN 16 AND 18 THEN 15 + UNIFORM(0, 20, RANDOM()) -- Rush hour
        WHEN HOUR(LOCATION_TIMESTAMP) BETWEEN 1 AND 5 THEN 45 + UNIFORM(0, 25, RANDOM())   -- Night
        ELSE 30 + UNIFORM(0, 35, RANDOM())  -- Normal hours
    END AS SPEED_MPH,
    CASE region_id
        WHEN 0 THEN 'Pacific Northwest'
        WHEN 1 THEN 'California'
        WHEN 2 THEN 'Mountain West'
        WHEN 3 THEN 'Midwest'
        ELSE 'Northeast'
    END AS FLEET_REGION
FROM base_locations;

-- ============================================
-- VERIFY ALL DATA LOADS
-- ============================================

SELECT 'Data Loading Summary' AS TITLE;

SELECT 
    'VEHICLE_REGISTRY' AS TABLE_NAME, 
    COUNT(*) AS ROW_COUNT,
    MIN(CREATED_AT) AS EARLIEST_RECORD,
    MAX(CREATED_AT) AS LATEST_RECORD
FROM VEHICLE_REGISTRY
UNION ALL
SELECT 'SENSOR_READINGS', COUNT(*), MIN(READING_TIMESTAMP), MAX(READING_TIMESTAMP) 
FROM SENSOR_READINGS
UNION ALL
SELECT 'VEHICLE_LOCATIONS', COUNT(*), MIN(LOCATION_TIMESTAMP), MAX(LOCATION_TIMESTAMP)
FROM VEHICLE_LOCATIONS
UNION ALL
SELECT 'MAINTENANCE_LOGS', COUNT(*), MIN(LOG_TIMESTAMP), MAX(LOG_TIMESTAMP)
FROM MAINTENANCE_LOGS
UNION ALL
SELECT 'VEHICLE_TELEMETRY_STREAM', COUNT(*), MIN(EVENT_TIMESTAMP), MAX(EVENT_TIMESTAMP)
FROM VEHICLE_TELEMETRY_STREAM
UNION ALL
SELECT 'API_WEATHER_DATA', COUNT(*), MIN(INGESTED_AT), MAX(INGESTED_AT)
FROM API_WEATHER_DATA;

SELECT 'Sample data loaded successfully!' AS STATUS;

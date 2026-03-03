-- Snowflake Iceberg V3 Comprehensive Guide
-- Script 03: Create Iceberg V3 Tables
-- ====================================

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_ANALYTICS_DB;
USE SCHEMA RAW;
USE WAREHOUSE FLEET_ANALYTICS_WH;

-- ============================================
-- Table 1: VEHICLE_TELEMETRY_STREAM
-- Purpose: Real-time streaming vehicle telemetry with VARIANT
-- Note: Using TIMESTAMP(6) for microsecond precision (Spark compatibility)
-- ============================================
CREATE OR REPLACE ICEBERG TABLE VEHICLE_TELEMETRY_STREAM (
    VEHICLE_ID STRING NOT NULL,
    EVENT_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    TELEMETRY_DATA VARIANT NOT NULL,
    INGESTED_AT TIMESTAMP_LTZ(6))
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/RAW/VEHICLE_TELEMETRY_STREAM'
    COMMENT = 'Real-time vehicle telemetry events streamed via Snowpipe Streaming';

-- ============================================
-- Table 2: MAINTENANCE_LOGS
-- Purpose: Batch-loaded JSON maintenance/diagnostic logs
-- Note: Using TIMESTAMP(6) for microsecond precision (Spark compatibility)
-- ============================================
CREATE OR REPLACE ICEBERG TABLE MAINTENANCE_LOGS (
    LOG_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    LOG_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    LOG_DATA VARIANT NOT NULL,
    SOURCE_FILE STRING,
    INGESTED_AT TIMESTAMP_LTZ(6))
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/RAW/MAINTENANCE_LOGS'
    COMMENT = 'Maintenance and diagnostic logs loaded from JSON files';

-- ============================================
-- Table 3: SENSOR_READINGS
-- Purpose: High-precision time-series sensor data
-- Note: Using TIMESTAMP(6) for microsecond precision (Spark compatibility)
-- ============================================
CREATE OR REPLACE ICEBERG TABLE SENSOR_READINGS (
    READING_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    READING_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,  -- Microsecond precision for Spark compatibility
    ENGINE_TEMP_F FLOAT,
    OIL_PRESSURE_PSI FLOAT,
    BATTERY_VOLTAGE FLOAT,
    FUEL_CONSUMPTION_GPH FLOAT,
    TIRE_PRESSURE_FL FLOAT,
    TIRE_PRESSURE_FR FLOAT,
    TIRE_PRESSURE_RL FLOAT,
    TIRE_PRESSURE_RR FLOAT,
    ODOMETER_MILES FLOAT,
    INGESTED_AT TIMESTAMP_LTZ(6))
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/RAW/SENSOR_READINGS'
    COMMENT = 'High-precision time-series sensor readings';

-- ============================================
-- Table 4: VEHICLE_LOCATIONS
-- Purpose: Geospatial vehicle position data
-- Note: Using TIMESTAMP(6) for microsecond precision (Spark compatibility)
-- ============================================
CREATE OR REPLACE ICEBERG TABLE VEHICLE_LOCATIONS (
    LOCATION_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    LOCATION_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    LATITUDE FLOAT NOT NULL,
    LONGITUDE FLOAT NOT NULL,
    LOCATION_POINT GEOGRAPHY,
    ALTITUDE_FT FLOAT,
    HEADING_DEGREES FLOAT,
    SPEED_MPH FLOAT,
    FLEET_REGION STRING,
    INGESTED_AT TIMESTAMP_LTZ(6))
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/RAW/VEHICLE_LOCATIONS'
    COMMENT = 'Geospatial vehicle location data with GEOGRAPHY type';

-- ============================================
-- Table 5: VEHICLE_REGISTRY
-- Purpose: Master data for vehicles and drivers
-- Note: Using TIMESTAMP(6) for microsecond precision (Spark compatibility)
-- ============================================
CREATE OR REPLACE ICEBERG TABLE VEHICLE_REGISTRY (
    VEHICLE_ID STRING NOT NULL,
    VIN STRING,
    MAKE STRING,
    MODEL STRING,
    YEAR INT,
    LICENSE_PLATE STRING,
    DRIVER_ID STRING,
    DRIVER_NAME STRING,
    DRIVER_EMAIL STRING,
    DRIVER_PHONE STRING,
    FLEET_REGION STRING,
    VEHICLE_STATUS STRING DEFAULT 'ACTIVE',
    REGISTRATION_DATE DATE,
    LAST_SERVICE_DATE DATE,
    CREATED_AT TIMESTAMP_LTZ(6),
    UPDATED_AT TIMESTAMP_LTZ(6))
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/RAW/VEHICLE_REGISTRY'
    COMMENT = 'Master data for vehicles and drivers (contains PII)';

-- ============================================
-- Table 6: API_WEATHER_DATA
-- Purpose: Weather data from public API with VARIANT
-- Note: Using TIMESTAMP(6) for microsecond precision (Spark compatibility)
-- ============================================
CREATE OR REPLACE ICEBERG TABLE API_WEATHER_DATA (
    CITY_NAME STRING NOT NULL,
    LATITUDE FLOAT NOT NULL,
    LONGITUDE FLOAT NOT NULL,
    WEATHER_DATA VARIANT NOT NULL,
    INGESTED_AT TIMESTAMP_LTZ(6))
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/RAW/API_WEATHER_DATA'
    COMMENT = 'Weather data fetched from Open-Meteo API';

-- ============================================
-- Load Sample Data into VEHICLE_REGISTRY
-- ============================================
INSERT INTO VEHICLE_REGISTRY (
    VEHICLE_ID, VIN, MAKE, MODEL, YEAR, LICENSE_PLATE,
    DRIVER_ID, DRIVER_NAME, DRIVER_EMAIL, DRIVER_PHONE,
    FLEET_REGION, VEHICLE_STATUS, REGISTRATION_DATE, LAST_SERVICE_DATE
)
SELECT 
    'VH-' || LPAD(SEQ4()::VARCHAR, 4, '0') AS VEHICLE_ID,
    UPPER(RANDSTR(17, RANDOM())) AS VIN,
    CASE MOD(SEQ4(), 5)
        WHEN 0 THEN 'Ford'
        WHEN 1 THEN 'Chevrolet'
        WHEN 2 THEN 'Toyota'
        WHEN 3 THEN 'Ram'
        ELSE 'Freightliner'
    END AS MAKE,
    CASE MOD(SEQ4(), 5)
        WHEN 0 THEN 'Transit'
        WHEN 1 THEN 'Express'
        WHEN 2 THEN 'Tacoma'
        WHEN 3 THEN 'ProMaster'
        ELSE 'Cascadia'
    END AS MODEL,
    2020 + MOD(SEQ4(), 6) AS YEAR,
    UPPER(RANDSTR(3, RANDOM())) || '-' || LPAD(MOD(SEQ4() * 7, 9999)::VARCHAR, 4, '0') AS LICENSE_PLATE,
    'DRV-' || LPAD(SEQ4()::VARCHAR, 4, '0') AS DRIVER_ID,
    CASE MOD(SEQ4(), 10)
        WHEN 0 THEN 'John Smith'
        WHEN 1 THEN 'Sarah Johnson'
        WHEN 2 THEN 'Michael Brown'
        WHEN 3 THEN 'Emily Davis'
        WHEN 4 THEN 'David Wilson'
        WHEN 5 THEN 'Jessica Taylor'
        WHEN 6 THEN 'Christopher Lee'
        WHEN 7 THEN 'Amanda Martinez'
        WHEN 8 THEN 'Daniel Anderson'
        ELSE 'Jennifer Garcia'
    END AS DRIVER_NAME,
    LOWER(SPLIT_PART(DRIVER_NAME, ' ', 1)) || '.' || LOWER(SPLIT_PART(DRIVER_NAME, ' ', 2)) || '@fleetco.com' AS DRIVER_EMAIL,
    '+1-555-' || LPAD(MOD(SEQ4() * 13, 9999)::VARCHAR, 4, '0') AS DRIVER_PHONE,
    CASE MOD(SEQ4(), 5)
        WHEN 0 THEN 'Pacific Northwest'
        WHEN 1 THEN 'California'
        WHEN 2 THEN 'Mountain West'
        WHEN 3 THEN 'Midwest'
        ELSE 'Northeast'
    END AS FLEET_REGION,
    CASE WHEN MOD(SEQ4(), 20) = 0 THEN 'MAINTENANCE' ELSE 'ACTIVE' END AS VEHICLE_STATUS,
    DATEADD('day', -MOD(SEQ4() * 17, 1000), CURRENT_DATE()) AS REGISTRATION_DATE,
    DATEADD('day', -MOD(SEQ4() * 7, 90), CURRENT_DATE()) AS LAST_SERVICE_DATE
FROM TABLE(GENERATOR(ROWCOUNT => 100));

-- ============================================
-- Load Sample Data into SENSOR_READINGS
-- ============================================
INSERT INTO SENSOR_READINGS (
    READING_ID, VEHICLE_ID, READING_TIMESTAMP,
    ENGINE_TEMP_F, OIL_PRESSURE_PSI, BATTERY_VOLTAGE,
    FUEL_CONSUMPTION_GPH, TIRE_PRESSURE_FL, TIRE_PRESSURE_FR,
    TIRE_PRESSURE_RL, TIRE_PRESSURE_RR, ODOMETER_MILES
)
SELECT 
    UUID_STRING() AS READING_ID,
    'VH-' || LPAD(MOD(SEQ4(), 100)::VARCHAR, 4, '0') AS VEHICLE_ID,
    -- Spread readings over 30 days to overlap with maintenance logs
    TIMESTAMPADD('minute', -SEQ4() * 5, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ(6) AS READING_TIMESTAMP,
    180 + RANDOM() / POWER(10, 18) * 50 AS ENGINE_TEMP_F,
    30 + RANDOM() / POWER(10, 18) * 30 AS OIL_PRESSURE_PSI,
    11.5 + RANDOM() / POWER(10, 18) * 3 AS BATTERY_VOLTAGE,
    2 + RANDOM() / POWER(10, 18) * 8 AS FUEL_CONSUMPTION_GPH,
    32 + RANDOM() / POWER(10, 18) * 6 AS TIRE_PRESSURE_FL,
    32 + RANDOM() / POWER(10, 18) * 6 AS TIRE_PRESSURE_FR,
    32 + RANDOM() / POWER(10, 18) * 6 AS TIRE_PRESSURE_RL,
    32 + RANDOM() / POWER(10, 18) * 6 AS TIRE_PRESSURE_RR,
    10000 + SEQ4() * 50 + RANDOM() / POWER(10, 18) * 100 AS ODOMETER_MILES
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- ============================================
-- Load Sample Data into VEHICLE_LOCATIONS
-- ============================================
-- Using CTEs to generate realistic coordinates around major US cities
INSERT INTO VEHICLE_LOCATIONS (
    LOCATION_ID, VEHICLE_ID, LOCATION_TIMESTAMP,
    LATITUDE, LONGITUDE, LOCATION_POINT,
    ALTITUDE_FT, HEADING_DEGREES, SPEED_MPH, FLEET_REGION
)
WITH city_centers AS (
    -- Define city centers for each region (lat, lon, city, region)
    SELECT * FROM (VALUES
        (47.6062, -122.3321, 'Seattle', 'Pacific Northwest'),
        (45.5152, -122.6784, 'Portland', 'Pacific Northwest'),
        (34.0522, -118.2437, 'Los Angeles', 'California'),
        (37.7749, -122.4194, 'San Francisco', 'California'),
        (32.7157, -117.1611, 'San Diego', 'California'),
        (39.7392, -104.9903, 'Denver', 'Mountain West'),
        (40.7608, -111.8910, 'Salt Lake City', 'Mountain West'),
        (33.4484, -112.0740, 'Phoenix', 'Mountain West'),
        (41.8781, -87.6298, 'Chicago', 'Midwest'),
        (44.9778, -93.2650, 'Minneapolis', 'Midwest'),
        (39.0997, -94.5786, 'Kansas City', 'Midwest'),
        (40.7128, -74.0060, 'New York', 'Northeast'),
        (42.3601, -71.0589, 'Boston', 'Northeast'),
        (39.9526, -75.1652, 'Philadelphia', 'Northeast'),
        (38.9072, -77.0369, 'Washington DC', 'Northeast'),
        (29.7604, -95.3698, 'Houston', 'Texas'),
        (32.7767, -96.7970, 'Dallas', 'Texas'),
        (30.2672, -97.7431, 'Austin', 'Texas'),
        (33.4484, -84.3880, 'Atlanta', 'Southeast'),
        (25.7617, -80.1918, 'Miami', 'Southeast')
    ) AS t(base_lat, base_lon, city, region)
),
numbered_cities AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY base_lat) - 1 AS city_idx
    FROM city_centers
),
base_data AS (
    SELECT 
        SEQ4() AS seq,
        'VH-' || LPAD(MOD(SEQ4(), 100)::VARCHAR, 4, '0') AS VEHICLE_ID,
        TIMESTAMPADD('second', -SEQ4() * 30, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS LOCATION_TIMESTAMP,
        MOD(SEQ4(), 20) AS city_selector
    FROM TABLE(GENERATOR(ROWCOUNT => 5000))
)
SELECT 
    UUID_STRING() AS LOCATION_ID,
    b.VEHICLE_ID,
    b.LOCATION_TIMESTAMP,
    -- Add random offset within ~30 miles (0.5 degrees) of city center
    c.base_lat + (UNIFORM(-50, 50, RANDOM()) / 100.0) AS LATITUDE,
    c.base_lon + (UNIFORM(-50, 50, RANDOM()) / 100.0) AS LONGITUDE,
    ST_POINT(
        c.base_lon + (UNIFORM(-50, 50, RANDOM()) / 100.0),
        c.base_lat + (UNIFORM(-50, 50, RANDOM()) / 100.0)
    ) AS LOCATION_POINT,
    UNIFORM(100, 5000, RANDOM())::FLOAT AS ALTITUDE_FT,
    UNIFORM(0, 359, RANDOM())::FLOAT AS HEADING_DEGREES,
    UNIFORM(0, 80, RANDOM())::FLOAT AS SPEED_MPH,
    c.region AS FLEET_REGION
FROM base_data b
JOIN numbered_cities c ON b.city_selector = c.city_idx;

-- Verify tables
SHOW ICEBERG TABLES IN SCHEMA RAW;

SELECT 'VEHICLE_REGISTRY' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM VEHICLE_REGISTRY
UNION ALL
SELECT 'SENSOR_READINGS', COUNT(*) FROM SENSOR_READINGS
UNION ALL
SELECT 'VEHICLE_LOCATIONS', COUNT(*) FROM VEHICLE_LOCATIONS;

SELECT 'Iceberg tables created and sample data loaded!' AS STATUS;

-- Get Started with Snowflake-Managed Iceberg Tables
-- Script 04: Load Sample Data
-- ============================================

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_DB;
USE SCHEMA RAW;
USE WAREHOUSE FLEET_WH;

-- ============================================
-- Load VEHICLE_REGISTRY (100 vehicles)
-- ============================================
INSERT INTO VEHICLE_REGISTRY (
    VEHICLE_ID, VIN, MAKE, MODEL, YEAR, LICENSE_PLATE,
    DRIVER_NAME, DRIVER_EMAIL,
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
-- Load SENSOR_READINGS (10,000 readings)
-- ============================================
INSERT INTO SENSOR_READINGS (
    READING_ID, VEHICLE_ID, READING_TIMESTAMP,
    ENGINE_TEMP_F, OIL_PRESSURE_PSI, BATTERY_VOLTAGE,
    FUEL_CONSUMPTION_GPH, ODOMETER_MILES
)
SELECT
    UUID_STRING() AS READING_ID,
    'VH-' || LPAD(MOD(SEQ4(), 100)::VARCHAR, 4, '0') AS VEHICLE_ID,
    TIMESTAMPADD('minute', -SEQ4() * 5, CURRENT_TIMESTAMP())::TIMESTAMP_NTZ(6) AS READING_TIMESTAMP,
    180 + RANDOM() / POWER(10, 18) * 50 AS ENGINE_TEMP_F,
    30 + RANDOM() / POWER(10, 18) * 30 AS OIL_PRESSURE_PSI,
    11.5 + RANDOM() / POWER(10, 18) * 3 AS BATTERY_VOLTAGE,
    2 + RANDOM() / POWER(10, 18) * 8 AS FUEL_CONSUMPTION_GPH,
    10000 + SEQ4() * 50 + RANDOM() / POWER(10, 18) * 100 AS ODOMETER_MILES
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- ============================================
-- Load MAINTENANCE_LOGS from staged JSON files
-- ============================================
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
FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)
PATTERN = '.*maintenance_log.*\.json';

-- Verify
SELECT 'VEHICLE_REGISTRY' AS table_name, COUNT(*) AS row_count FROM VEHICLE_REGISTRY
UNION ALL
SELECT 'SENSOR_READINGS', COUNT(*) FROM SENSOR_READINGS
UNION ALL
SELECT 'MAINTENANCE_LOGS', COUNT(*) FROM MAINTENANCE_LOGS;

SELECT 'Sample data loaded!' AS STATUS;

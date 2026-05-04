-- Get Started with Snowflake-Managed Iceberg Tables
-- Script 02: Create Iceberg Tables
-- ============================================

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_DB;
USE SCHEMA RAW;
USE WAREHOUSE FLEET_WH;

-- ============================================
-- Table 1: VEHICLE_TELEMETRY_STREAM
-- Real-time streaming vehicle telemetry with VARIANT
-- ============================================
CREATE OR REPLACE ICEBERG TABLE VEHICLE_TELEMETRY_STREAM (
    VEHICLE_ID STRING NOT NULL,
    EVENT_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    TELEMETRY_DATA VARIANT NOT NULL,
    INGESTED_AT TIMESTAMP_LTZ(6)
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';

-- ============================================
-- Table 2: VEHICLE_REGISTRY
-- Master data for vehicles and drivers
-- ============================================
CREATE OR REPLACE ICEBERG TABLE VEHICLE_REGISTRY (
    VEHICLE_ID STRING NOT NULL,
    VIN STRING,
    MAKE STRING,
    MODEL STRING,
    YEAR INT,
    LICENSE_PLATE STRING,
    DRIVER_NAME STRING,
    DRIVER_EMAIL STRING,
    FLEET_REGION STRING,
    VEHICLE_STATUS STRING DEFAULT 'ACTIVE',
    REGISTRATION_DATE DATE,
    LAST_SERVICE_DATE DATE
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';

-- ============================================
-- Table 3: SENSOR_READINGS
-- High-precision time-series sensor data
-- ============================================
CREATE OR REPLACE ICEBERG TABLE SENSOR_READINGS (
    READING_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    READING_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    ENGINE_TEMP_F FLOAT,
    OIL_PRESSURE_PSI FLOAT,
    BATTERY_VOLTAGE FLOAT,
    FUEL_CONSUMPTION_GPH FLOAT,
    ODOMETER_MILES FLOAT
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';

-- ============================================
-- Table 4: MAINTENANCE_LOGS
-- Batch-loaded JSON maintenance/diagnostic logs
-- ============================================
CREATE OR REPLACE ICEBERG TABLE MAINTENANCE_LOGS (
    LOG_ID STRING NOT NULL,
    VEHICLE_ID STRING NOT NULL,
    LOG_TIMESTAMP TIMESTAMP_NTZ(6) NOT NULL,
    LOG_DATA VARIANT NOT NULL,
    SOURCE_FILE STRING
)
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE';

-- Verify
SHOW ICEBERG TABLES IN SCHEMA RAW;
SELECT 'Iceberg tables created!' AS STATUS;

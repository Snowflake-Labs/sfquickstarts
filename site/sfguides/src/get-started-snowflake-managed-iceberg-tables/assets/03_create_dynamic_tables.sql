-- Get Started with Snowflake-Managed Iceberg Tables
-- Script 03: Create Dynamic Iceberg Tables
-- ============================================

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_DB;
USE SCHEMA ANALYTICS;
USE WAREHOUSE FLEET_WH;

-- ============================================
-- Dynamic Iceberg Table 1: TELEMETRY_ENRICHED
-- Joins streaming telemetry with vehicle registry
-- ============================================
CREATE OR REPLACE DYNAMIC ICEBERG TABLE TELEMETRY_ENRICHED
    TARGET_LAG = '10 minutes'
    WAREHOUSE = FLEET_WH
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE'
AS
SELECT
    t.VEHICLE_ID,
    t.EVENT_TIMESTAMP,
    t.TELEMETRY_DATA:speed_mph::FLOAT AS speed_mph,
    t.TELEMETRY_DATA:engine:temperature_f::INT AS engine_temp_f,
    t.TELEMETRY_DATA:engine:fuel_level_pct::FLOAT AS fuel_level_pct,
    t.TELEMETRY_DATA:diagnostics:check_engine::BOOLEAN AS check_engine,
    CASE
        WHEN t.TELEMETRY_DATA:engine:temperature_f::INT > 230 THEN 'CRITICAL'
        WHEN t.TELEMETRY_DATA:engine:temperature_f::INT > 210 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS engine_health_status,
    v.MAKE,
    v.MODEL,
    v.DRIVER_NAME,
    v.FLEET_REGION
FROM FLEET_DB.RAW.VEHICLE_TELEMETRY_STREAM t
INNER JOIN FLEET_DB.RAW.VEHICLE_REGISTRY v
    ON t.VEHICLE_ID = v.VEHICLE_ID;

-- ============================================
-- Dynamic Iceberg Table 2: DAILY_FLEET_SUMMARY
-- Aggregates enriched telemetry into daily metrics
-- ============================================
CREATE OR REPLACE DYNAMIC ICEBERG TABLE DAILY_FLEET_SUMMARY
    TARGET_LAG = 'DOWNSTREAM'
    WAREHOUSE = FLEET_WH
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    CATALOG = 'SNOWFLAKE'
AS
SELECT
    DATE(EVENT_TIMESTAMP) AS summary_date,
    FLEET_REGION,
    COUNT(*) AS total_events,
    COUNT(DISTINCT VEHICLE_ID) AS active_vehicles,
    ROUND(AVG(speed_mph), 1) AS avg_speed_mph,
    ROUND(AVG(engine_temp_f), 1) AS avg_engine_temp_f,
    ROUND(AVG(fuel_level_pct), 1) AS avg_fuel_level_pct,
    SUM(CASE WHEN engine_health_status = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_events,
    SUM(CASE WHEN check_engine THEN 1 ELSE 0 END) AS check_engine_events
FROM FLEET_DB.ANALYTICS.TELEMETRY_ENRICHED
GROUP BY DATE(EVENT_TIMESTAMP), FLEET_REGION;

-- Verify
SHOW DYNAMIC TABLES IN SCHEMA ANALYTICS;
SELECT 'Dynamic Iceberg Tables created!' AS STATUS;

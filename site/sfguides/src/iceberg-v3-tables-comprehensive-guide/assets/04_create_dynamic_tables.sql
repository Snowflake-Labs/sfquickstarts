-- Snowflake Iceberg V3 Comprehensive Guide
-- Script 04: Create Dynamic Iceberg Tables
-- ========================================

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_ANALYTICS_DB;
USE WAREHOUSE FLEET_ANALYTICS_WH;

-- ============================================
-- Dynamic Table 1: TELEMETRY_ENRICHED
-- Purpose: Join streaming telemetry with vehicle registry
-- ============================================
CREATE OR REPLACE DYNAMIC ICEBERG TABLE CURATED.TELEMETRY_ENRICHED
    TARGET_LAG = '1 minute'
    WAREHOUSE = FLEET_ANALYTICS_WH
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/CURATED/TELEMETRY_ENRICHED'
AS
SELECT 
    t.VEHICLE_ID,
    t.EVENT_TIMESTAMP,
    t.TELEMETRY_DATA,
    -- Extract key metrics from variant for easier querying
    t.TELEMETRY_DATA:speed_mph::FLOAT AS speed_mph,
    t.TELEMETRY_DATA:location:lat::FLOAT AS latitude,
    t.TELEMETRY_DATA:location:lon::FLOAT AS longitude,
    t.TELEMETRY_DATA:heading::FLOAT AS heading,
    t.TELEMETRY_DATA:engine:rpm::INT AS engine_rpm,
    t.TELEMETRY_DATA:engine:temperature_f::INT AS engine_temp_f,
    t.TELEMETRY_DATA:engine:oil_pressure_psi::FLOAT AS oil_pressure_psi,
    t.TELEMETRY_DATA:engine:fuel_level_pct::FLOAT AS fuel_level_pct,
    t.TELEMETRY_DATA:diagnostics:check_engine::BOOLEAN AS check_engine_light,
    t.TELEMETRY_DATA:diagnostics:tire_pressure_warning::BOOLEAN AS tire_pressure_warning,
    t.TELEMETRY_DATA:driver_behavior:hard_acceleration_count::INT AS hard_accelerations,
    t.TELEMETRY_DATA:driver_behavior:hard_brake_count::INT AS hard_brakes,
    t.TELEMETRY_DATA:driver_behavior:sharp_turn_count::INT AS sharp_turns,
    -- Join with vehicle registry
    v.MAKE,
    v.MODEL,
    v.YEAR,
    v.DRIVER_ID,
    v.DRIVER_NAME,
    v.FLEET_REGION,
    v.VEHICLE_STATUS,
    -- Derived metrics
    CASE 
        WHEN t.TELEMETRY_DATA:engine:temperature_f::INT > 230 THEN 'CRITICAL'
        WHEN t.TELEMETRY_DATA:engine:temperature_f::INT > 210 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS engine_health_status,
    CASE 
        WHEN t.TELEMETRY_DATA:speed_mph::FLOAT > 80 THEN 'SPEEDING'
        WHEN t.TELEMETRY_DATA:speed_mph::FLOAT > 65 THEN 'HIGHWAY'
        WHEN t.TELEMETRY_DATA:speed_mph::FLOAT > 30 THEN 'CITY'
        ELSE 'SLOW'
    END AS driving_mode,
    CASE
        WHEN t.TELEMETRY_DATA:driver_behavior:hard_brake_count::INT > 3 
             OR t.TELEMETRY_DATA:driver_behavior:hard_acceleration_count::INT > 3
        THEN 'AGGRESSIVE'
        ELSE 'NORMAL'
    END AS driving_behavior
FROM RAW.VEHICLE_TELEMETRY_STREAM t
LEFT JOIN RAW.VEHICLE_REGISTRY v ON t.VEHICLE_ID = v.VEHICLE_ID;

-- ============================================
-- Dynamic Table 2: MAINTENANCE_ANALYSIS
-- Purpose: Analyze maintenance logs with extracted fields
-- ============================================
CREATE OR REPLACE DYNAMIC ICEBERG TABLE CURATED.MAINTENANCE_ANALYSIS
    TARGET_LAG = '5 minutes'
    WAREHOUSE = FLEET_ANALYTICS_WH
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/CURATED/MAINTENANCE_ANALYSIS'
AS
SELECT 
    m.LOG_ID,
    m.VEHICLE_ID,
    m.LOG_TIMESTAMP,
    m.LOG_DATA:event_type::STRING AS event_type,
    m.LOG_DATA:severity::STRING AS severity,
    m.LOG_DATA:description::STRING AS description,
    m.LOG_DATA:technician::STRING AS technician,
    m.LOG_DATA:service_center::STRING AS service_center,
    m.LOG_DATA:parts_replaced AS parts_replaced,
    m.LOG_DATA:labor_hours::FLOAT AS labor_hours,
    m.LOG_DATA:total_cost::FLOAT AS total_cost,
    ARRAY_SIZE(m.LOG_DATA:diagnostic_codes) AS diagnostic_code_count,
    m.LOG_DATA:diagnostic_codes AS diagnostic_codes,
    m.LOG_DATA:next_service_date::DATE AS next_service_date,
    -- Vehicle info
    v.MAKE,
    v.MODEL,
    v.YEAR,
    v.FLEET_REGION,
    v.ODOMETER_ESTIMATE,
    -- Derived fields
    DATEDIFF('day', v.LAST_SERVICE_DATE, m.LOG_TIMESTAMP) AS days_since_last_service,
    CASE 
        WHEN m.LOG_DATA:severity::STRING = 'CRITICAL' THEN 1
        WHEN m.LOG_DATA:severity::STRING = 'HIGH' THEN 2
        WHEN m.LOG_DATA:severity::STRING = 'MEDIUM' THEN 3
        ELSE 4
    END AS severity_rank
FROM RAW.MAINTENANCE_LOGS m
LEFT JOIN (
    SELECT 
        VEHICLE_ID, MAKE, MODEL, YEAR, FLEET_REGION, LAST_SERVICE_DATE,
        10000 + ROW_NUMBER() OVER (ORDER BY VEHICLE_ID) * 500 AS ODOMETER_ESTIMATE
    FROM RAW.VEHICLE_REGISTRY
) v ON m.VEHICLE_ID = v.VEHICLE_ID;

-- ============================================
-- Dynamic Table 3: DAILY_FLEET_SUMMARY
-- Purpose: Aggregated daily fleet analytics
-- ============================================
CREATE OR REPLACE DYNAMIC ICEBERG TABLE ANALYTICS.DAILY_FLEET_SUMMARY
    TARGET_LAG = '5 minutes'
    WAREHOUSE = FLEET_ANALYTICS_WH
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/ANALYTICS/DAILY_FLEET_SUMMARY'
    REFRESH_MODE = INCREMENTAL
AS
SELECT 
    DATE(EVENT_TIMESTAMP) AS summary_date,
    FLEET_REGION,
    COUNT(DISTINCT VEHICLE_ID) AS active_vehicles,
    COUNT(*) AS total_events,
    AVG(speed_mph) AS avg_speed_mph,
    MAX(speed_mph) AS max_speed_mph,
    AVG(fuel_level_pct) AS avg_fuel_level,
    AVG(engine_temp_f) AS avg_engine_temp,
    SUM(hard_accelerations) AS total_hard_accelerations,
    SUM(hard_brakes) AS total_hard_brakes,
    SUM(sharp_turns) AS total_sharp_turns,
    SUM(CASE WHEN engine_health_status = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_events,
    SUM(CASE WHEN engine_health_status = 'WARNING' THEN 1 ELSE 0 END) AS warning_events,
    SUM(CASE WHEN driving_behavior = 'AGGRESSIVE' THEN 1 ELSE 0 END) AS aggressive_driving_events,
    SUM(CASE WHEN check_engine_light THEN 1 ELSE 0 END) AS check_engine_events
FROM CURATED.TELEMETRY_ENRICHED
GROUP BY DATE(EVENT_TIMESTAMP), FLEET_REGION;

-- ============================================
-- Dynamic Table 4: VEHICLE_HEALTH_SCORE
-- Purpose: Rolling vehicle health scores
-- ============================================
CREATE OR REPLACE DYNAMIC ICEBERG TABLE ANALYTICS.VEHICLE_HEALTH_SCORE
    TARGET_LAG = '10 minutes'
    WAREHOUSE = FLEET_ANALYTICS_WH
    EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'FLEET_ANALYTICS_DB/ANALYTICS/VEHICLE_HEALTH_SCORE'
AS
WITH recent_telemetry AS (
    SELECT 
        VEHICLE_ID,
        AVG(engine_temp_f) AS avg_engine_temp,
        AVG(oil_pressure_psi) AS avg_oil_pressure,
        SUM(CASE WHEN check_engine_light THEN 1 ELSE 0 END) AS check_engine_count,
        SUM(CASE WHEN tire_pressure_warning THEN 1 ELSE 0 END) AS tire_warning_count,
        COUNT(*) AS event_count,
        MAX(EVENT_TIMESTAMP) AS last_event
    FROM CURATED.TELEMETRY_ENRICHED
    WHERE EVENT_TIMESTAMP > DATEADD('day', -7, CURRENT_TIMESTAMP())
    GROUP BY VEHICLE_ID
),
recent_maintenance AS (
    SELECT 
        VEHICLE_ID,
        COUNT(*) AS maintenance_count,
        SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_issues,
        MAX(LOG_TIMESTAMP) AS last_maintenance
    FROM CURATED.MAINTENANCE_ANALYSIS
    WHERE LOG_TIMESTAMP > DATEADD('day', -30, CURRENT_TIMESTAMP())
    GROUP BY VEHICLE_ID
)
SELECT 
    v.VEHICLE_ID,
    v.MAKE,
    v.MODEL,
    v.YEAR,
    v.FLEET_REGION,
    v.DRIVER_NAME,
    t.avg_engine_temp,
    t.avg_oil_pressure,
    t.check_engine_count,
    t.tire_warning_count,
    t.event_count AS telemetry_events_7d,
    m.maintenance_count AS maintenance_events_30d,
    m.critical_issues AS critical_issues_30d,
    -- Calculate health score (0-100)
    GREATEST(0, LEAST(100,
        100 
        - (CASE WHEN t.avg_engine_temp > 210 THEN 20 ELSE 0 END)
        - (CASE WHEN t.avg_oil_pressure < 25 THEN 15 ELSE 0 END)
        - (t.check_engine_count * 10)
        - (t.tire_warning_count * 5)
        - (COALESCE(m.critical_issues, 0) * 15)
    )) AS health_score,
    -- Health status
    CASE 
        WHEN health_score >= 80 THEN 'EXCELLENT'
        WHEN health_score >= 60 THEN 'GOOD'
        WHEN health_score >= 40 THEN 'FAIR'
        WHEN health_score >= 20 THEN 'POOR'
        ELSE 'CRITICAL'
    END AS health_status,
    t.last_event AS last_telemetry,
    m.last_maintenance
FROM RAW.VEHICLE_REGISTRY v
LEFT JOIN recent_telemetry t ON v.VEHICLE_ID = t.VEHICLE_ID
LEFT JOIN recent_maintenance m ON v.VEHICLE_ID = m.VEHICLE_ID
WHERE t.VEHICLE_ID IS NOT NULL;

-- Verify dynamic tables were created
SHOW DYNAMIC TABLES IN DATABASE FLEET_ANALYTICS_DB;

SELECT 'Dynamic Iceberg tables created!' AS STATUS;

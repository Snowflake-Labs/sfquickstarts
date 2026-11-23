-- Snowflake Iceberg V3 Comprehensive Guide
-- Script 07: Create Snowflake Intelligence Agent
-- ==============================================
-- Note: Cortex Agents require Enterprise Edition or higher

USE ROLE ACCOUNTADMIN;
USE DATABASE FLEET_ANALYTICS_DB;
USE WAREHOUSE FLEET_ANALYTICS_WH;

-- ============================================
-- ENABLE CROSS-REGION INFERENCE (Optional)
-- ============================================
-- Cortex Agents require LLMs that may not be available in all regions.
-- If you see "None of the preferred models are authorized or available in your region",
-- enable cross-region inference to route AI requests to regions with model support.
-- 
-- Your data stays in your region - only inference is routed cross-region.
-- For more info: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference

-- Uncomment to enable (requires ACCOUNTADMIN):
-- ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- To check current setting:
-- SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;

-- ============================================
-- CREATE HELPER VIEWS FOR AGENT
-- ============================================
-- These views simplify data access for the agent

CREATE OR REPLACE VIEW RAW.VEHICLE_OVERVIEW AS
SELECT 
    v.VEHICLE_ID,
    v.MAKE,
    v.MODEL,
    v.YEAR,
    v.DRIVER_NAME,
    v.FLEET_REGION,
    v.VEHICLE_STATUS,
    h.health_score,
    h.health_status,
    h.avg_engine_temp,
    h.check_engine_count AS recent_check_engine_alerts,
    h.maintenance_events_30d
FROM RAW.VEHICLE_REGISTRY v
LEFT JOIN ANALYTICS.VEHICLE_HEALTH_SCORE h ON v.VEHICLE_ID = h.VEHICLE_ID;

CREATE OR REPLACE VIEW RAW.FLEET_PERFORMANCE AS
SELECT 
    FLEET_REGION,
    summary_date,
    active_vehicles,
    total_events,
    ROUND(avg_speed_mph, 1) AS avg_speed_mph,
    ROUND(max_speed_mph, 1) AS max_speed_mph,
    ROUND(avg_fuel_level, 1) AS avg_fuel_level_pct,
    ROUND(avg_engine_temp, 1) AS avg_engine_temp_f,
    total_hard_accelerations + total_hard_brakes + total_sharp_turns AS total_driving_events,
    critical_events,
    warning_events,
    aggressive_driving_events
FROM ANALYTICS.DAILY_FLEET_SUMMARY
ORDER BY summary_date DESC, FLEET_REGION;

CREATE OR REPLACE VIEW RAW.MAINTENANCE_SUMMARY AS
SELECT 
    VEHICLE_ID,
    event_type,
    severity,
    description,
    LOG_TIMESTAMP,
    technician,
    service_center,
    labor_hours,
    total_cost,
    diagnostic_code_count,
    MAKE,
    MODEL,
    FLEET_REGION
FROM CURATED.MAINTENANCE_ANALYSIS
ORDER BY LOG_TIMESTAMP DESC;

-- ============================================
-- CREATE CORTEX AGENT
-- ============================================
-- Reference: https://docs.snowflake.com/en/sql-reference/sql/create-agent
-- Note: After creation, you must configure data sources through the UI

-- Create the agent with full YAML specification
-- Reference: https://docs.snowflake.com/en/sql-reference/sql/create-agent#examples
CREATE OR REPLACE AGENT FLEET_ANALYTICS_DB.RAW.FLEET_ANALYTICS_AGENT
    COMMENT = 'AI assistant for fleet management analytics on Iceberg V3 tables'
    PROFILE = '{"display_name": "Fleet Analytics Agent", "color": "blue"}'
    FROM SPECIFICATION
    $$
    orchestration:
      budget:
        seconds: 60
        tokens: 32000

    instructions:
      response: "Provide clear, concise answers with relevant data. Format numbers for readability."
      orchestration: "Use the Analyst tool for all data queries about vehicles, sensors, maintenance, and locations."
      system: |
        You are a fleet analytics assistant helping users understand their vehicle fleet operations.
        The data comes from commercial vehicles tracked across the United States.
        
        Key entities:
        - Vehicles are identified by VEHICLE_ID in format 'VH-XXXX'
        - Fleet regions: Pacific Northwest, California, Mountain West, Midwest, Northeast, Texas, Southeast
        
        Data sources available:
        - SENSOR_READINGS: Has FUEL_CONSUMPTION_GPH, ENGINE_TEMP_F, OIL_PRESSURE_PSI
        - VEHICLE_TELEMETRY_STREAM: VARIANT TELEMETRY_DATA with nested JSON (speed_mph, engine.temperature_f)
        - VEHICLE_LOCATIONS: GEOGRAPHY LOCATION_POINT for geospatial, use H3 functions
        - MAINTENANCE_LOGS: VARIANT LOG_DATA with event_type, severity, total_cost
        - VEHICLE_REGISTRY: Driver info (may be masked), vehicle make/model/year
        - DAILY_FLEET_SUMMARY: Aggregated metrics by region and date
        
        Query tips:
        - For VARIANT columns: use TELEMETRY_DATA:speed_mph::FLOAT
        - For geospatial: use H3_POINT_TO_CELL_STRING(LOCATION_POINT, 6)
      sample_questions:
        - question: "Which vehicles had the highest fuel consumption last week?"
          answer: "I'll query the SENSOR_READINGS table to analyze fuel consumption by vehicle."
        - question: "Show me all critical maintenance events"
          answer: "I'll search MAINTENANCE_LOGS for events with severity = 'CRITICAL'."
        - question: "What's the average speed by fleet region?"
          answer: "I'll aggregate speed data from VEHICLE_TELEMETRY_STREAM grouped by region."
        - question: "Find vehicles with check engine warnings"
          answer: "I'll look for check_engine flags in the telemetry data."
        - question: "Which drivers have the most hard braking events?"
          answer: "I'll analyze hard_brake_count from the telemetry data joined with driver info."

    tools:
      - tool_spec:
          type: "cortex_analyst_text_to_sql"
          name: "FleetAnalyst"
          description: "Converts natural language to SQL queries for fleet analytics data"

    tool_resources:
      FleetAnalyst:
        semantic_model_file: "@FLEET_ANALYTICS_DB.RAW.LOGS_STAGE/fleet_semantic_model.yaml"
    $$;

-- Grant access to the agent
GRANT USAGE ON AGENT FLEET_ANALYTICS_DB.RAW.FLEET_ANALYTICS_AGENT TO ROLE FLEET_ANALYST;
GRANT USAGE ON AGENT FLEET_ANALYTICS_DB.RAW.FLEET_ANALYTICS_AGENT TO ROLE FLEET_ADMIN;

-- Grant access to helper views
GRANT SELECT ON RAW.VEHICLE_OVERVIEW TO ROLE FLEET_ANALYST;
GRANT SELECT ON RAW.FLEET_PERFORMANCE TO ROLE FLEET_ANALYST;
GRANT SELECT ON RAW.MAINTENANCE_SUMMARY TO ROLE FLEET_ANALYST;

-- ============================================
-- VERIFY AGENT CREATION
-- ============================================

SHOW AGENTS IN SCHEMA RAW;

SELECT 'Fleet Analytics Agent created successfully!' AS STATUS;
SELECT 'Navigate to Cortex AI > Agents to test the agent.' AS NEXT_STEP;

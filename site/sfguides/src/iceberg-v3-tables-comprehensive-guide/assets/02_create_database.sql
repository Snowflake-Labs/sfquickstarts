-- Snowflake Iceberg V3 Comprehensive Guide
-- Script 02: Create Database, Schema, and Warehouse
-- ================================================

-- Use ACCOUNTADMIN role for setup
USE ROLE ACCOUNTADMIN;

-- Create warehouse for all operations
CREATE WAREHOUSE IF NOT EXISTS FLEET_ANALYTICS_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for Fleet Analytics Iceberg V3 Guide';

-- Create the main database with Iceberg V3 as default
CREATE DATABASE IF NOT EXISTS FLEET_ANALYTICS_DB
    COMMENT = 'Iceberg V3 Comprehensive Guide - Fleet Analytics';

-- Set Iceberg V3 as the default version for all Iceberg tables in this database
-- See: https://docs.snowflake.com/en/LIMITEDACCESS/iceberg/tables-iceberg-v3-specification-support
ALTER DATABASE FLEET_ANALYTICS_DB SET ICEBERG_VERSION_DEFAULT = 3;

-- Set default external volume for all Iceberg tables in this database
-- This is set after the external volume is created in 01_external_volume.sql
-- ALTER DATABASE FLEET_ANALYTICS_DB SET EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL';

-- Create schema for raw/source tables
CREATE SCHEMA IF NOT EXISTS FLEET_ANALYTICS_DB.RAW
    COMMENT = 'Raw data layer - source Iceberg tables';

-- Create schema for transformed/curated tables
CREATE SCHEMA IF NOT EXISTS FLEET_ANALYTICS_DB.CURATED
    COMMENT = 'Curated data layer - transformed Iceberg tables';

-- Create schema for analytics/reporting
CREATE SCHEMA IF NOT EXISTS FLEET_ANALYTICS_DB.ANALYTICS
    COMMENT = 'Analytics layer - aggregated Iceberg tables';

-- Create internal stage for JSON log files
CREATE STAGE IF NOT EXISTS FLEET_ANALYTICS_DB.RAW.LOGS_STAGE
    COMMENT = 'Internal stage for maintenance log JSON files';

-- Create file format for JSON
CREATE FILE FORMAT IF NOT EXISTS FLEET_ANALYTICS_DB.RAW.JSON_FORMAT
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE
    COMMENT = 'JSON file format for log ingestion';

-- ============================================
-- EXTERNAL ACCESS INTEGRATION for API calls
-- Required for Python code in notebooks to access external APIs
-- ============================================

-- Create network rule allowing access to Open-Meteo weather API
CREATE OR REPLACE NETWORK RULE FLEET_ANALYTICS_DB.RAW.OPEN_METEO_NETWORK_RULE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('api.open-meteo.com:443');

-- Create external access integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION OPEN_METEO_ACCESS
    ALLOWED_NETWORK_RULES = (FLEET_ANALYTICS_DB.RAW.OPEN_METEO_NETWORK_RULE)
    ENABLED = TRUE
    COMMENT = 'External access for Open-Meteo weather API';

-- Verify setup
USE DATABASE FLEET_ANALYTICS_DB;
SHOW SCHEMAS;
SHOW STAGES IN SCHEMA RAW;
SHOW WAREHOUSES LIKE 'FLEET_ANALYTICS_WH';

SELECT 'Database setup complete!' AS STATUS;

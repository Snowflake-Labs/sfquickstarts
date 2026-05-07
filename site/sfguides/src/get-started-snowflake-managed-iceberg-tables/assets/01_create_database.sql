-- Get Started with Snowflake-Managed Iceberg Tables
-- Script 01: Create Database and Schemas
-- ============================================

USE ROLE ACCOUNTADMIN;

-- Create the warehouse
CREATE WAREHOUSE IF NOT EXISTS FLEET_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

USE WAREHOUSE FLEET_WH;

-- Create the database
CREATE OR REPLACE DATABASE FLEET_DB;

-- Set the default external volume to Snowflake-managed storage.
-- All Iceberg tables in this database will use Snowflake-managed storage
-- unless overridden at the table level.
ALTER DATABASE FLEET_DB SET EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED';

-- Use Iceberg spec v3 (required for VARIANT columns in Iceberg tables)
ALTER DATABASE FLEET_DB SET ICEBERG_VERSION_DEFAULT = 3;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS FLEET_DB.RAW;
CREATE SCHEMA IF NOT EXISTS FLEET_DB.ANALYTICS;

-- Create an internal stage for JSON file uploads
CREATE STAGE IF NOT EXISTS FLEET_DB.RAW.LOGS_STAGE;

SELECT 'Database, schemas, and stage created!' AS STATUS;

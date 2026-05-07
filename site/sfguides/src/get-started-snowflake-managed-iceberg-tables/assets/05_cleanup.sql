-- Get Started with Snowflake-Managed Iceberg Tables
-- Script 05: Clean Up
-- ============================================

USE ROLE ACCOUNTADMIN;

-- Drop the database (removes all tables, dynamic tables, stages, etc.)
DROP DATABASE IF EXISTS FLEET_DB;

-- Drop the warehouse
DROP WAREHOUSE IF EXISTS FLEET_WH;

SELECT 'Cleanup complete!' AS STATUS;

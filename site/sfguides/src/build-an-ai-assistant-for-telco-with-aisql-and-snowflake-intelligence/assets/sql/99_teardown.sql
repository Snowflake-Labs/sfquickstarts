-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 99: Teardown - Complete Cleanup
-- ============================================================================
-- Description: Removes ALL components created by the Telco Operations AI quickstart
-- WARNING: This script will permanently delete all data, objects, and configurations
-- Run this script to completely uninstall the quickstart from your account
-- ============================================================================

-- ============================================================================
-- IMPORTANT: Review before running!
-- ============================================================================
-- This script will remove:
-- - SnowMail Native Application and Package
-- - Snowflake Intelligence Agent
-- - All Cortex Search Services
-- - All Notebooks
-- - TELCO_OPERATIONS_AI database (including all tables, views, stages, data)
-- - SNOWFLAKE_INTELLIGENCE database (if empty after agent removal)
-- - TELCO_WH warehouse
-- - TELCO_ANALYST_ROLE role
-- - Application package database (TELCO_OPERATIONS_AI_SNOWMAIL_PKG)
-- ============================================================================

USE ROLE ACCOUNTADMIN;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql", "action":"teardown"}}';

-- ============================================================================
-- Step 1: Drop SnowMail Native Application
-- ============================================================================

SELECT '=== Step 1: Removing SnowMail Native Application ===' AS status;

-- Drop the application instance first
DROP APPLICATION IF EXISTS SNOWMAIL CASCADE;

-- Drop the application package
DROP APPLICATION PACKAGE IF EXISTS SNOWMAIL_PKG;

-- Drop the application package database
DROP DATABASE IF EXISTS TELCO_OPERATIONS_AI_SNOWMAIL_PKG;

SELECT 'SnowMail Native Application removed' AS status;

-- ============================================================================
-- Step 2: Drop Snowflake Intelligence Agent
-- ============================================================================

SELECT '=== Step 2: Removing Snowflake Intelligence Agent ===' AS status;

-- Drop the agent (use quotes for the name with spaces)
DROP AGENT IF EXISTS SNOWFLAKE_INTELLIGENCE.AGENTS."Telco Operations AI Agent";

-- Check if AGENTS schema is empty, if so drop it
-- Note: Only drop SNOWFLAKE_INTELLIGENCE if it was created by this quickstart
-- and has no other agents

SELECT 'Snowflake Intelligence Agent removed' AS status;

-- ============================================================================
-- Step 3: Drop Cortex Search Services
-- ============================================================================

SELECT '=== Step 3: Removing Cortex Search Services ===' AS status;

DROP CORTEX SEARCH SERVICE IF EXISTS TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.CALL_TRANSCRIPT_SEARCH;
DROP CORTEX SEARCH SERVICE IF EXISTS TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.SUPPORT_TICKET_SEARCH;

SELECT 'Cortex Search Services removed' AS status;

-- ============================================================================
-- Step 4: Drop Notebooks
-- ============================================================================

SELECT '=== Step 4: Removing Notebooks ===' AS status;

DROP NOTEBOOK IF EXISTS TELCO_OPERATIONS_AI.NOTEBOOKS."1_DATA_PROCESSING";
DROP NOTEBOOK IF EXISTS TELCO_OPERATIONS_AI.NOTEBOOKS."2_ANALYZE_CALL_AUDIO";
DROP NOTEBOOK IF EXISTS TELCO_OPERATIONS_AI.NOTEBOOKS."3_INTELLIGENCE_LAB";

-- Drop notebook stages (each notebook has its own stage)
DROP STAGE IF EXISTS TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_1_DATA_PROCESSING;
DROP STAGE IF EXISTS TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_2_ANALYZE_CALL_AUDIO;
DROP STAGE IF EXISTS TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_3_INTELLIGENCE_LAB;

SELECT 'Notebooks and notebook stages removed' AS status;

-- ============================================================================
-- Step 5: Drop TELCO_OPERATIONS_AI Database
-- ============================================================================
-- This removes all schemas, tables, views, stages, and data

SELECT '=== Step 5: Removing TELCO_OPERATIONS_AI Database ===' AS status;

DROP DATABASE IF EXISTS TELCO_OPERATIONS_AI CASCADE;

SELECT 'TELCO_OPERATIONS_AI database and all contents removed' AS status;

-- ============================================================================
-- Step 6: Drop Warehouse
-- ============================================================================

SELECT '=== Step 6: Removing TELCO_WH Warehouse ===' AS status;

DROP WAREHOUSE IF EXISTS TELCO_WH;

SELECT 'TELCO_WH warehouse removed' AS status;

-- ============================================================================
-- Step 7: Revoke Intelligence Privileges and Drop Role
-- ============================================================================

SELECT '=== Step 7: Removing TELCO_ANALYST_ROLE ===' AS status;

-- Revoke Intelligence privileges first (ignore errors if not granted)
BEGIN
    REVOKE DATABASE ROLE SNOWFLAKE.INTELLIGENCE_MODIFY FROM ROLE TELCO_ANALYST_ROLE;
EXCEPTION
    WHEN OTHER THEN
        -- Ignore if privilege doesn't exist
        NULL;
END;

BEGIN
    REVOKE DATABASE ROLE SNOWFLAKE.INTELLIGENCE_USER FROM ROLE TELCO_ANALYST_ROLE;
EXCEPTION
    WHEN OTHER THEN
        -- Ignore if privilege doesn't exist
        NULL;
END;

BEGIN
    REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_USER FROM ROLE TELCO_ANALYST_ROLE;
EXCEPTION
    WHEN OTHER THEN
        -- Ignore if privilege doesn't exist
        NULL;
END;

-- Drop the role
DROP ROLE IF EXISTS TELCO_ANALYST_ROLE;

SELECT 'TELCO_ANALYST_ROLE removed' AS status;

-- ============================================================================
-- Step 8: Optional - Clean up SNOWFLAKE_INTELLIGENCE database
-- ============================================================================
-- Only uncomment if you want to remove the SNOWFLAKE_INTELLIGENCE database
-- WARNING: This may affect other agents if they exist in this database

-- SELECT '=== Step 8: Checking SNOWFLAKE_INTELLIGENCE Database ===' AS status;

-- Check if there are any remaining agents
-- SELECT COUNT(*) as remaining_agents FROM INFORMATION_SCHEMA.AGENTS WHERE DATABASE_NAME = 'SNOWFLAKE_INTELLIGENCE';

-- Uncomment below to drop the database if empty:
-- DROP DATABASE IF EXISTS SNOWFLAKE_INTELLIGENCE CASCADE;

-- ============================================================================
-- Verification
-- ============================================================================

SELECT '=== Teardown Complete ===' AS status;

-- Verify objects are removed
SELECT 'Verification - These should return no results:' AS check_type;

-- Check for remaining databases
SELECT 'Databases' as object_type, DATABASE_NAME 
FROM INFORMATION_SCHEMA.DATABASES 
WHERE DATABASE_NAME IN ('TELCO_OPERATIONS_AI', 'TELCO_OPERATIONS_AI_SNOWMAIL_PKG');

-- Check for remaining warehouses
SHOW WAREHOUSES LIKE 'TELCO_WH';

-- Check for remaining roles
SHOW ROLES LIKE 'TELCO_ANALYST_ROLE';

-- Check for remaining applications
SHOW APPLICATIONS LIKE 'SNOWMAIL';

SELECT '=============================================' AS separator;
SELECT 'Telco Operations AI Quickstart teardown complete!' AS final_status,
       'All components have been removed from your account.' AS message,
       CURRENT_TIMESTAMP() AS completed_at;

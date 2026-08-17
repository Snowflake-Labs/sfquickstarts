-- ============================================================================
-- Snowflake Teardown Script for Online Feature Store with Postgres Demo
-- ============================================================================
-- This script removes all resources created by the setup script.
-- Run this when you're completely done with the demo.
--
-- IMPORTANT: Before running this script, drop the Postgres online service
-- from your notebook to avoid leaving a running service:
--
--   fs.drop_online_service()
--
-- ============================================================================

USE ROLE ACCOUNTADMIN;

SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;

-- Set query tag for tracking
ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"sfguide_intro_to_online_feature_with_postgres_store", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"sql", "action":"teardown"}}';

-- ============================================================================
-- SECTION 1: STOP SERVICES AND DROP COMPUTE POOL
-- ============================================================================

USE ROLE FS_DEMO_ROLE;

-- Drop SPCS inference service if it was created (optional step)
DROP SERVICE IF EXISTS FEATURE_STORE_DEMO.TAXI_FEATURES.NYC_TAXI_ETA_V1;

-- Stop all services running in the compute pool
ALTER COMPUTE POOL IF EXISTS trip_eta_prediction_pool STOP ALL;

-- Drop compute pool
DROP COMPUTE POOL IF EXISTS trip_eta_prediction_pool;

-- ============================================================================
-- SECTION 2: DROP EXTERNAL ACCESS INTEGRATION
-- ============================================================================

-- Switch to ACCOUNTADMIN to drop integration
USE ROLE ACCOUNTADMIN;

-- Drop external access integration
DROP INTEGRATION IF EXISTS FEATURE_STORE_DEMO_ALLOW_ALL_INTEGRATION;

-- ============================================================================
-- SECTION 3: DROP DATABASE AND WAREHOUSE
-- ============================================================================

-- Switch back to FS_DEMO_ROLE to drop database and warehouse
USE ROLE FS_DEMO_ROLE;

-- Drop database (also drops schema, network rule, stage, and all objects inside)
DROP DATABASE IF EXISTS FEATURE_STORE_DEMO;

-- Drop warehouse
DROP WAREHOUSE IF EXISTS FS_DEMO_WH;

-- ============================================================================
-- SECTION 4: REVOKE ACCOUNT-LEVEL PERMISSIONS AND DROP ROLE
-- ============================================================================

-- Switch to ACCOUNTADMIN to revoke permissions and drop role
USE ROLE ACCOUNTADMIN;

-- Revoke account-level permissions
REVOKE CREATE DATABASE ON ACCOUNT FROM ROLE FS_DEMO_ROLE;
REVOKE CREATE WAREHOUSE ON ACCOUNT FROM ROLE FS_DEMO_ROLE;
REVOKE CREATE COMPUTE POOL ON ACCOUNT FROM ROLE FS_DEMO_ROLE;
REVOKE BIND SERVICE ENDPOINT ON ACCOUNT FROM ROLE FS_DEMO_ROLE;
REVOKE IMPORT SHARE ON ACCOUNT FROM ROLE FS_DEMO_ROLE;
REVOKE EXECUTE TASK ON ACCOUNT FROM ROLE FS_DEMO_ROLE;
REVOKE EXECUTE MANAGED TASK ON ACCOUNT FROM ROLE FS_DEMO_ROLE;

-- Revoke role from user
REVOKE ROLE FS_DEMO_ROLE FROM USER identifier($USERNAME);

-- Drop the role
DROP ROLE IF EXISTS FS_DEMO_ROLE;

-- ============================================================================
-- TEARDOWN COMPLETE
-- ============================================================================

SELECT 'Teardown complete! All resources have been removed.' AS STATUS;

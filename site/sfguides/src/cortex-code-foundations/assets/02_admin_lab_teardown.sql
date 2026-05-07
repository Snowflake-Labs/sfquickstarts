-- ============================================================================
-- CoCo CLI Hands-on Lab — Full Teardown (run AFTER the event is over)
-- ============================================================================
-- Removes everything created by the lab: database, warehouse, role.
-- This is a DESTRUCTIVE operation — only run when the lab is fully finished.
--
-- Run as: ACCOUNTADMIN
-- ============================================================================

-- ============================================================================
-- 1. REVOKE ROLE FROM ALL USERS
-- ============================================================================

USE ROLE SECURITYADMIN;

-- Revoke Cortex database roles
USE ROLE ACCOUNTADMIN;
REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_USER         FROM ROLE COCO_WORKSHOP_ROLE;
REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_ANALYST_USER FROM ROLE COCO_WORKSHOP_ROLE;
REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER   FROM ROLE COCO_WORKSHOP_ROLE;

-- ============================================================================
-- 2. DROP DATABASE (cascades all schemas, tables, DTs, views, agents, etc.)
-- ============================================================================

USE ROLE SYSADMIN;

DROP DATABASE IF EXISTS COCO_WORKSHOP;

-- ============================================================================
-- 3. DROP WAREHOUSE
-- ============================================================================

DROP WAREHOUSE IF EXISTS COCO_WORKSHOP_WH;

-- ============================================================================
-- 4. DROP ROLE
-- ============================================================================

USE ROLE SECURITYADMIN;

DROP ROLE IF EXISTS COCO_WORKSHOP_ROLE;

-- ============================================================================
-- 5. VERIFY
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- All should return 0 rows
SHOW DATABASES LIKE 'COCO_WORKSHOP';
SHOW WAREHOUSES LIKE 'COCO_WORKSHOP_WH';
SHOW ROLES LIKE 'COCO_WORKSHOP_ROLE';

SELECT 'Lab teardown complete — all resources removed' AS STATUS;

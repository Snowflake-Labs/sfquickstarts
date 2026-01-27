/*
 * Copyright 2026 Snowflake Inc.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*******************************************************************************
 * ASSIGN ROLES TO USERS - Grid Reliability Project
 * 
 * Purpose: Template script to assign roles to users
 * Database: UTILITIES_GRID_RELIABILITY
 * 
 * Instructions:
 * 1. Replace placeholder usernames with actual user emails
 * 2. Uncomment the appropriate GRANT statements
 * 3. Run as ACCOUNTADMIN or a role with GRANT privileges
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-15
 * Version: 1.0
 ******************************************************************************/

USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- VERIFY ROLES EXIST
-- =============================================================================

SHOW ROLES LIKE 'GRID_%';

-- You should see:
-- GRID_ANALYST
-- GRID_DATA_ENGINEER
-- GRID_ML_ENGINEER

-- =============================================================================
-- VIEW CURRENT ROLE PERMISSIONS
-- =============================================================================

-- Uncomment to see what each role has access to
-- SHOW GRANTS TO ROLE GRID_ANALYST;
-- SHOW GRANTS TO ROLE GRID_DATA_ENGINEER;
-- SHOW GRANTS TO ROLE GRID_ML_ENGINEER;

-- =============================================================================
-- ASSIGN ROLES TO USERS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- GRID_ANALYST - For Business Analysts, Operations Managers, Executives
-- -----------------------------------------------------------------------------

-- Example: Assign to analyst
-- GRANT ROLE GRID_ANALYST TO USER john.smith@utility.com;
-- GRANT ROLE GRID_ANALYST TO USER susan.executive@utility.com;
-- GRANT ROLE GRID_ANALYST TO USER mike.operations@utility.com;

-- Set as default role (optional)
-- ALTER USER john.smith@utility.com SET DEFAULT_ROLE = GRID_ANALYST;

-- -----------------------------------------------------------------------------
-- GRID_DATA_ENGINEER - For Data Engineers, ETL Developers
-- -----------------------------------------------------------------------------

-- Example: Assign to data engineer
-- GRANT ROLE GRID_DATA_ENGINEER TO USER sarah.dataeng@utility.com;

-- Also give analyst role for easy querying
-- GRANT ROLE GRID_ANALYST TO USER sarah.dataeng@utility.com;

-- Set as default role
-- ALTER USER sarah.dataeng@utility.com SET DEFAULT_ROLE = GRID_DATA_ENGINEER;

-- -----------------------------------------------------------------------------
-- GRID_ML_ENGINEER - For Data Scientists, ML Engineers
-- -----------------------------------------------------------------------------

-- Example: Assign to ML engineer
-- GRANT ROLE GRID_ML_ENGINEER TO USER alex.datascientist@utility.com;

-- Also give analyst role for reporting
-- GRANT ROLE GRID_ANALYST TO USER alex.datascientist@utility.com;

-- Set as default role
-- ALTER USER alex.datascientist@utility.com SET DEFAULT_ROLE = GRID_ML_ENGINEER;

-- =============================================================================
-- ROLE HIERARCHY (OPTIONAL)
-- =============================================================================

-- If you have existing organizational roles, you can grant Grid roles to them

-- Example: Grant to existing BI team role
-- GRANT ROLE GRID_ANALYST TO ROLE BUSINESS_INTELLIGENCE;

-- Example: Grant to existing data engineering team role
-- GRANT ROLE GRID_DATA_ENGINEER TO ROLE DATA_ENGINEERING_TEAM;

-- Example: Grant to existing DS team role
-- GRANT ROLE GRID_ML_ENGINEER TO ROLE DATA_SCIENCE_TEAM;

-- =============================================================================
-- VERIFY USER ROLE ASSIGNMENTS
-- =============================================================================

-- Check what roles a user has
-- SHOW GRANTS TO USER john.smith@utility.com;

-- Check who has a specific role
-- SHOW GRANTS OF ROLE GRID_ANALYST;

-- =============================================================================
-- TEST ROLE ACCESS (RUN AS USER)
-- =============================================================================

-- Switch to the role and test
-- USE ROLE GRID_ANALYST;
-- USE DATABASE UTILITIES_GRID_RELIABILITY;
-- USE WAREHOUSE GRID_RELIABILITY_WH;

-- This should work (SELECT permission)
-- SELECT * FROM ANALYTICS.VW_ASSET_HEALTH_DASHBOARD LIMIT 5;

-- This should FAIL for GRID_ANALYST (no INSERT permission)
-- INSERT INTO RAW.ASSET_MASTER VALUES (...);

-- =============================================================================
-- REVOKE ROLE FROM USER (IF NEEDED)
-- =============================================================================

-- To remove a role from a user
-- REVOKE ROLE GRID_ANALYST FROM USER john.smith@utility.com;

-- =============================================================================
-- MONITORING & AUDIT
-- =============================================================================

-- View recent queries by role
/*
SELECT 
    USER_NAME,
    ROLE_NAME,
    QUERY_TEXT,
    START_TIME,
    END_TIME,
    TOTAL_ELAPSED_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE ROLE_NAME IN ('GRID_ANALYST', 'GRID_DATA_ENGINEER', 'GRID_ML_ENGINEER')
  AND START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC
LIMIT 100;
*/

-- View role usage statistics
/*
SELECT 
    ROLE_NAME,
    COUNT(*) as QUERY_COUNT,
    COUNT(DISTINCT USER_NAME) as UNIQUE_USERS,
    SUM(TOTAL_ELAPSED_TIME)/1000 as TOTAL_SECONDS
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE ROLE_NAME IN ('GRID_ANALYST', 'GRID_DATA_ENGINEER', 'GRID_ML_ENGINEER')
  AND START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY ROLE_NAME
ORDER BY QUERY_COUNT DESC;
*/

-- =============================================================================
-- TEMPLATE: ASSIGN ROLES TO YOUR TEAM
-- =============================================================================

-- Copy and modify this template for your actual users:
/*
-- Business Analysts
GRANT ROLE GRID_ANALYST TO USER analyst1@utility.com;
GRANT ROLE GRID_ANALYST TO USER analyst2@utility.com;
ALTER USER analyst1@utility.com SET DEFAULT_ROLE = GRID_ANALYST;

-- Data Engineers
GRANT ROLE GRID_DATA_ENGINEER TO USER dataeng1@utility.com;
GRANT ROLE GRID_ANALYST TO USER dataeng1@utility.com;
ALTER USER dataeng1@utility.com SET DEFAULT_ROLE = GRID_DATA_ENGINEER;

-- ML Engineers
GRANT ROLE GRID_ML_ENGINEER TO USER mleng1@utility.com;
GRANT ROLE GRID_ANALYST TO USER mleng1@utility.com;
ALTER USER mleng1@utility.com SET DEFAULT_ROLE = GRID_ML_ENGINEER;

-- Operations Managers
GRANT ROLE GRID_ANALYST TO USER ops.manager@utility.com;
ALTER USER ops.manager@utility.com SET DEFAULT_ROLE = GRID_ANALYST;

-- Executives (Read-Only)
GRANT ROLE GRID_ANALYST TO USER executive@utility.com;
ALTER USER executive@utility.com SET DEFAULT_ROLE = GRID_ANALYST;
*/

-- =============================================================================
-- COMPLETE
-- =============================================================================

SELECT 'Role assignment script ready!' as STATUS;
SELECT 'Edit this file with actual usernames and run the GRANT statements' as NEXT_STEP;



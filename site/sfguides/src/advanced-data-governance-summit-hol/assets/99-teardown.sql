
/***************************************************************************************************
 Advanced Data Governance: AI-Powered Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Lab Teardown
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL
***************************************************************************************************/

/*
  TEARDOWN — Removes all objects created during this lab.

  Run this script after completing the lab to clean up your Snowflake account.
  Dropping HRZN_DB cascades to all schemas, tables, views, functions,
  stages, policies, tags, and classifiers inside it.

  Objects removed:
    Database:    HRZN_DB (and all contents)
    Roles:       HRZN_DATA_ENGINEER, HRZN_DATA_GOVERNOR, HRZN_DATA_USER,
                 HRZN_IT_ADMIN, HRZN_DATA_ANALYST
    Warehouse:   HRZN_WH
*/

-- ============================================================================
-- STEP 1: Remove classification profile from database before dropping
-- ============================================================================

USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;

-- Detach the classification profile so it can be dropped with the database
ALTER DATABASE HRZN_DB UNSET CLASSIFICATION_PROFILE;

-- Drop the classification profile explicitly
DROP SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE IF EXISTS
    HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE;

-- ============================================================================
-- STEP 2: Drop the database (cascades to all objects inside it)
-- ============================================================================

USE ROLE HRZN_DATA_ENGINEER;
DROP DATABASE IF EXISTS HRZN_DB;

-- HRZN_DB drop removes:
--   Schemas:   HRZN_SCH, TAG_SCHEMA, CLASSIFIERS, SEC_POLICIES_SCHEMA
--   Tables:    CUSTOMER, CUSTOMER_ORDERS, CUSTOMER_COPY, CUSTOMER_FEEDBACK_REDACTED,
--              ROW_POLICY_MAP, CUSTOMER_CONSENT_MAP
--   Views:     CUSTOMER_FEEDBACK_SECURE
--   Policies:  DATA_CLASSIFICATION_MASK_STRING/NUMBER/DATE/TIMESTAMP,
--              CUSTOMER_OPTIN_POLICY, CUSTOMER_STATE_RESTRICTIONS,
--              AGGREGATION_POLICY, PROJECTION_POLICY
--   Tags:      DATA_CLASSIFICATION (with propagation)

-- ============================================================================
-- STEP 3: Drop custom roles
-- ============================================================================

USE ROLE SECURITYADMIN;
DROP ROLE IF EXISTS HRZN_DATA_GOVERNOR;
DROP ROLE IF EXISTS HRZN_DATA_USER;
DROP ROLE IF EXISTS HRZN_IT_ADMIN;
DROP ROLE IF EXISTS HRZN_DATA_ENGINEER;
DROP ROLE IF EXISTS HRZN_DATA_ANALYST;

-- ============================================================================
-- STEP 4: Drop the warehouse
-- ============================================================================

USE ROLE SYSADMIN;
DROP WAREHOUSE IF EXISTS HRZN_WH;

SELECT 'Teardown complete. All lab objects have been removed.' AS status;

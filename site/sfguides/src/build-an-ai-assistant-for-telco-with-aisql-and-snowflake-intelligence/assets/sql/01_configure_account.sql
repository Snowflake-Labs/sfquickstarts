-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 01: Configure Account
-- ============================================================================
-- Description: Creates roles, warehouse, database, schemas, and stages
-- Run this script first to set up the Snowflake environment
-- ============================================================================

USE ROLE ACCOUNTADMIN;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- Step 1: Create Custom Role for Telco Analytics
-- ============================================================================

CREATE ROLE IF NOT EXISTS TELCO_ANALYST_ROLE
    COMMENT = 'Role for Telco Operations AI hands-on lab';

-- Grant necessary privileges
GRANT CREATE DATABASE ON ACCOUNT TO ROLE TELCO_ANALYST_ROLE;

-- Grant CORTEX_USER database role (required for Cortex AI functions)
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE TELCO_ANALYST_ROLE;

-- Enable cross-region inference for Cortex AI functions
-- This allows using AI models hosted in other regions when not available locally
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- Grant role to ACCOUNTADMIN and SYSADMIN for administrative access
GRANT ROLE TELCO_ANALYST_ROLE TO ROLE ACCOUNTADMIN;
GRANT ROLE TELCO_ANALYST_ROLE TO ROLE SYSADMIN;

-- Grant TELCO_ANALYST_ROLE to current user
SET current_user = (SELECT CURRENT_USER());
GRANT ROLE TELCO_ANALYST_ROLE TO USER IDENTIFIER($current_user);

-- ============================================================================
-- Grant Snowflake Intelligence Privileges (for custom agent appearances)
-- ============================================================================
-- MODIFY privilege is required to add agents to Snowflake Intelligence
-- and customize agent appearances (avatar, color, display name)

GRANT DATABASE ROLE SNOWFLAKE.INTELLIGENCE_MODIFY TO ROLE TELCO_ANALYST_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.INTELLIGENCE_USER TO ROLE TELCO_ANALYST_ROLE;

SELECT 'Role configuration complete' AS status,
       CURRENT_USER() as user,
       'TELCO_ANALYST_ROLE' as role_granted,
       'INTELLIGENCE_MODIFY granted' as intelligence_access;

-- ============================================================================
-- Step 2: Create Dedicated Warehouse
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS TELCO_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for Telco Operations AI';

GRANT USAGE ON WAREHOUSE TELCO_WH TO ROLE TELCO_ANALYST_ROLE;
GRANT OPERATE ON WAREHOUSE TELCO_WH TO ROLE TELCO_ANALYST_ROLE;

-- ============================================================================
-- Step 3: Create Database and Schemas
-- ============================================================================

USE ROLE TELCO_ANALYST_ROLE;

CREATE DATABASE IF NOT EXISTS TELCO_OPERATIONS_AI
    COMMENT = 'Database for Telco Operations AI - Build an AI Assistant for Telco';

USE DATABASE TELCO_OPERATIONS_AI;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS DEFAULT_SCHEMA
    COMMENT = 'Main schema for call center data tables';

CREATE SCHEMA IF NOT EXISTS CORTEX_ANALYST
    COMMENT = 'Schema for Cortex Analyst semantic views';

CREATE SCHEMA IF NOT EXISTS NOTEBOOKS
    COMMENT = 'Schema for Snowflake notebooks';

CREATE SCHEMA IF NOT EXISTS STREAMLIT
    COMMENT = 'Schema for Streamlit applications';

CREATE SCHEMA IF NOT EXISTS MODELS
    COMMENT = 'Schema for ML models and UDFs';

-- ============================================================================
-- Step 4: Create File Formats
-- ============================================================================

USE SCHEMA DEFAULT_SCHEMA;

CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    ESCAPE_UNENCLOSED_FIELD = NONE
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    NULL_IF = ('NULL', 'null', '')
    COMMENT = 'Standard CSV format for telco data files';

CREATE OR REPLACE FILE FORMAT JSON_FORMAT
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE
    COMMENT = 'JSON format for structured data';

-- ============================================================================
-- Step 5: Create Stages
-- ============================================================================

CREATE OR REPLACE STAGE AUDIO_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for call center audio files (MP3)';

CREATE OR REPLACE STAGE CSV_STAGE
    DIRECTORY = (ENABLE = TRUE)
    FILE_FORMAT = CSV_FORMAT
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for CSV data files';

CREATE OR REPLACE STAGE PDF_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for PDF documentation files';

CREATE OR REPLACE STAGE NOTEBOOK_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for Snowflake notebook files';

CREATE OR REPLACE STAGE STREAMLIT_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for Streamlit application files';

-- ============================================================================
-- Step 6: Create Network Rule and External Access Integration (Optional)
-- ============================================================================
-- Note: External Access Integration may not be available on trial accounts
-- Uncomment if needed for web search features

/*
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NETWORK RULE telco_web_access_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('www.google.com', 'www.bing.com', 'api.openai.com', 'api.anthropic.com');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION telco_external_access
  ALLOWED_NETWORK_RULES = (telco_web_access_rule)
  ENABLED = TRUE
  COMMENT = 'External access for web search and API calls';

GRANT USAGE ON INTEGRATION telco_external_access TO ROLE TELCO_ANALYST_ROLE;
*/

-- ============================================================================
-- Set Context
-- ============================================================================

USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;
USE DATABASE TELCO_OPERATIONS_AI;
USE SCHEMA DEFAULT_SCHEMA;

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'Account configuration complete!' AS status,
       'TELCO_OPERATIONS_AI' AS database_created,
       'TELCO_WH' AS warehouse_created,
       'TELCO_ANALYST_ROLE' AS role_created,
       CURRENT_TIMESTAMP() as deployed_at;


-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 03: Deploy Cortex Search Services
-- ============================================================================
-- Description: Creates Cortex Search Services for call transcripts and support tickets
-- Prerequisites: Run 01_configure_account.sql and 02_data_foundation.sql first
-- ============================================================================

USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;
USE DATABASE TELCO_OPERATIONS_AI;
USE SCHEMA DEFAULT_SCHEMA;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- Step 1: Create Cortex Search Service for Call Transcripts
-- ============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE CALL_TRANSCRIPT_SEARCH
ON SEGMENT_TEXT
ATTRIBUTES CALL_ID, SPEAKER_ROLE, SENTIMENT_SCORE, CALL_TIMESTAMP
WAREHOUSE = TELCO_WH
TARGET_LAG = '1 hour'
COMMENT = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}'
AS (
    SELECT 
        SEGMENT_TEXT,
        CALL_ID,
        SPEAKER_ROLE,
        SENTIMENT_SCORE,
        CALL_TIMESTAMP
    FROM CALL_TRANSCRIPTS
);

-- ============================================================================
-- Step 2: Create Cortex Search Service for Support Tickets  
-- ============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE SUPPORT_TICKET_SEARCH
ON DESCRIPTION
ATTRIBUTES TICKET_ID, CUSTOMER_ID, CATEGORY, STATUS, PRIORITY, SUBJECT
WAREHOUSE = TELCO_WH
TARGET_LAG = '1 hour'
COMMENT = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}'
AS (
    SELECT 
        DESCRIPTION,
        TICKET_ID,
        CUSTOMER_ID,
        CATEGORY,
        STATUS,
        PRIORITY,
        SUBJECT
    FROM SUPPORT_TICKETS
);

-- ============================================================================
-- Verification
-- ============================================================================

SHOW CORTEX SEARCH SERVICES IN SCHEMA DEFAULT_SCHEMA;

SELECT 'Cortex Search Services deployed!' AS status,
       'CALL_TRANSCRIPT_SEARCH' AS service_1,
       'SUPPORT_TICKET_SEARCH' AS service_2,
       CURRENT_TIMESTAMP() AS deployed_at;


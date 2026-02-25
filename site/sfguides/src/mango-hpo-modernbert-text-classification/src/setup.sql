-- =============================================================================
-- SNOWFLAKE ENVIRONMENT SETUP FOR CFPB TEXT CLASSIFICATION
-- Distributed Text Classification with Mango HPO + TF-IDF + Snowflake DPF
-- =============================================================================

-- Create dedicated database
CREATE DATABASE IF NOT EXISTS CFPB_ML_DB;

-- Create schema for text analytics
CREATE SCHEMA IF NOT EXISTS CFPB_ML_DB.TEXT_ANALYTICS;

-- Set context
USE DATABASE CFPB_ML_DB;
USE SCHEMA TEXT_ANALYTICS;

-- =============================================================================
-- STAGES
-- =============================================================================

-- Create internal stage for ML artifacts (models, metrics, results)
CREATE STAGE IF NOT EXISTS ML_ARTIFACTS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for storing trained models, metrics, and classification results';

-- Create stage for raw data files
CREATE STAGE IF NOT EXISTS RAW_DATA_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for uploading raw CSV files';

-- =============================================================================
-- FILE FORMATS
-- =============================================================================

-- CSV file format for CFPB complaints data
CREATE FILE FORMAT IF NOT EXISTS CFPB_CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('', 'NA', 'NULL', 'N/A')
    EMPTY_FIELD_AS_NULL = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- =============================================================================
-- TABLES
-- =============================================================================

-- Main table for CFPB consumer complaints
CREATE TABLE IF NOT EXISTS CFPB_COMPLAINTS (
    DATE_RECEIVED DATE,
    PRODUCT VARCHAR(200),
    SUB_PRODUCT VARCHAR(300),
    ISSUE VARCHAR(500),
    SUB_ISSUE VARCHAR(500),
    CONSUMER_COMPLAINT_NARRATIVE TEXT,
    COMPANY_PUBLIC_RESPONSE VARCHAR(500),
    COMPANY VARCHAR(300),
    STATE VARCHAR(10),
    ZIP_CODE VARCHAR(20),
    TAGS VARCHAR(100),
    CONSUMER_CONSENT_PROVIDED VARCHAR(50),
    SUBMITTED_VIA VARCHAR(50),
    DATE_SENT_TO_COMPANY DATE,
    COMPANY_RESPONSE_TO_CONSUMER VARCHAR(200),
    TIMELY_RESPONSE VARCHAR(10),
    CONSUMER_DISPUTED VARCHAR(10),
    COMPLAINT_ID VARCHAR(50)
);

-- Results table for classification metrics
CREATE TABLE IF NOT EXISTS CLASSIFICATION_RESULTS (
    RUN_ID VARCHAR(100),
    RUN_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PARTITION_KEY VARCHAR(200),
    RECORDS_PROCESSED INT,
    TRAIN_RECORDS INT,
    TEST_RECORDS INT,
    NUM_CLASSES INT,
    BEST_ACCURACY FLOAT,
    BEST_F1_SCORE FLOAT,
    BEST_PARAMS VARIANT,
    TRAINING_TIME_SECONDS FLOAT,
    HPO_ITERATIONS INT,
    STATUS VARCHAR(50)
);

-- =============================================================================
-- DATA LOADING
-- =============================================================================

-- Option 1: Load from stage after PUT command
-- Run from SnowSQL or Snowflake CLI:
-- PUT file:///path/to/complaints100K.csv @RAW_DATA_STAGE/;

-- Then run this COPY command:
/*
COPY INTO CFPB_COMPLAINTS
FROM @RAW_DATA_STAGE/complaints100K.csv
FILE_FORMAT = CFPB_CSV_FORMAT
ON_ERROR = 'CONTINUE'
FORCE = TRUE;
*/

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check record count
-- SELECT COUNT(*) AS TOTAL_RECORDS FROM CFPB_COMPLAINTS;

-- Check records by product category (partition column)
-- SELECT PRODUCT, COUNT(*) AS RECORD_COUNT 
-- FROM CFPB_COMPLAINTS 
-- GROUP BY PRODUCT 
-- ORDER BY RECORD_COUNT DESC;

-- Check records with complaint narratives (required for text classification)
-- SELECT COUNT(*) AS RECORDS_WITH_TEXT 
-- FROM CFPB_COMPLAINTS 
-- WHERE CONSUMER_COMPLAINT_NARRATIVE IS NOT NULL 
--   AND LENGTH(CONSUMER_COMPLAINT_NARRATIVE) > 10;

-- Sample data preview
-- SELECT DATE_RECEIVED, PRODUCT, ISSUE, LEFT(CONSUMER_COMPLAINT_NARRATIVE, 200) AS NARRATIVE_PREVIEW
-- FROM CFPB_COMPLAINTS
-- WHERE CONSUMER_COMPLAINT_NARRATIVE IS NOT NULL
-- LIMIT 5;

-- =============================================================================
-- PERMISSIONS (Adjust role name as needed)
-- =============================================================================

-- Grant permissions to your role
-- GRANT USAGE ON DATABASE CFPB_ML_DB TO ROLE <YOUR_ROLE>;
-- GRANT USAGE ON SCHEMA CFPB_ML_DB.TEXT_ANALYTICS TO ROLE <YOUR_ROLE>;
-- GRANT ALL ON ALL TABLES IN SCHEMA CFPB_ML_DB.TEXT_ANALYTICS TO ROLE <YOUR_ROLE>;
-- GRANT ALL ON ALL STAGES IN SCHEMA CFPB_ML_DB.TEXT_ANALYTICS TO ROLE <YOUR_ROLE>;
-- GRANT CREATE TABLE ON SCHEMA CFPB_ML_DB.TEXT_ANALYTICS TO ROLE <YOUR_ROLE>;

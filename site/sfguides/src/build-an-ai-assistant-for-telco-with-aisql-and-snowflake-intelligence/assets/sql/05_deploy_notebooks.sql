-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 05: Deploy Notebooks
-- ============================================================================
-- Description: Deploys Snowflake Notebooks for data processing and analysis
-- Prerequisites: Run scripts 01-04 first
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE TELCO_OPERATIONS_AI;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- Step 1: Create Notebooks Schema and Stages
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS NOTEBOOKS;

-- Create individual stages for each notebook (1 stage per notebook for clean UI navigation)
CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_1_DATA_PROCESSING 
    DIRECTORY = (ENABLE = TRUE) 
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for 1_DATA_PROCESSING notebook';

CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_2_ANALYZE_CALL_AUDIO 
    DIRECTORY = (ENABLE = TRUE) 
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for 2_ANALYZE_CALL_AUDIO notebook';

CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_3_INTELLIGENCE_LAB 
    DIRECTORY = (ENABLE = TRUE) 
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for 3_INTELLIGENCE_LAB notebook';

-- ============================================================================
-- Step 2: Copy Notebook Files from Git Repository to Stages
-- ============================================================================

-- Notebook 1: Data Processing
COPY FILES INTO @TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_1_DATA_PROCESSING
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/Notebooks/
FILES = ('1_DATA_PROCESSING.ipynb', 'environment.yml');

-- Notebook 2: Analyze Call Audio
COPY FILES INTO @TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_2_ANALYZE_CALL_AUDIO
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/Notebooks/
FILES = ('2_ANALYZE_CALL_AUDIO.ipynb', 'environment.yml');

-- Notebook 3: Intelligence Lab
COPY FILES INTO @TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_3_INTELLIGENCE_LAB
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/Notebooks/
FILES = ('3_INTELLIGENCE_LAB.ipynb', 'environment.yml');

-- Refresh all notebook stages
ALTER STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_1_DATA_PROCESSING REFRESH;
ALTER STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_2_ANALYZE_CALL_AUDIO REFRESH;
ALTER STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_3_INTELLIGENCE_LAB REFRESH;

SELECT 'Notebook files copied from Git repository' AS status;

-- ============================================================================
-- Step 3: Grant Notebook Creation Privileges
-- ============================================================================

GRANT CREATE NOTEBOOK ON SCHEMA TELCO_OPERATIONS_AI.NOTEBOOKS TO ROLE TELCO_ANALYST_ROLE;

-- ============================================================================
-- Step 4: Create Notebooks
-- ============================================================================

USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;

-- Create Notebook 1: Data Processing
CREATE OR REPLACE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."1_DATA_PROCESSING"
    FROM '@TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_1_DATA_PROCESSING'
    MAIN_FILE = '1_DATA_PROCESSING.ipynb'
    QUERY_WAREHOUSE = 'TELCO_WH'
    COMMENT = '{"origin":"sf_sit-is", "name":"Telco Operations AI - 1. Data Processing", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"notebook", "order":1}}';

ALTER NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."1_DATA_PROCESSING" ADD LIVE VERSION FROM LAST;

-- Create Notebook 2: Analyze Call Audio
CREATE OR REPLACE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."2_ANALYZE_CALL_AUDIO"
    FROM '@TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_2_ANALYZE_CALL_AUDIO'
    MAIN_FILE = '2_ANALYZE_CALL_AUDIO.ipynb'
    QUERY_WAREHOUSE = 'TELCO_WH'
    COMMENT = '{"origin":"sf_sit-is", "name":"Telco Operations AI - 2. Analyze Call Audio", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"notebook", "order":2}}';

ALTER NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."2_ANALYZE_CALL_AUDIO" ADD LIVE VERSION FROM LAST;

-- Create Notebook 3: Intelligence Lab
CREATE OR REPLACE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."3_INTELLIGENCE_LAB"
    FROM '@TELCO_OPERATIONS_AI.NOTEBOOKS.STAGE_3_INTELLIGENCE_LAB'
    MAIN_FILE = '3_INTELLIGENCE_LAB.ipynb'
    QUERY_WAREHOUSE = 'TELCO_WH'
    COMMENT = '{"origin":"sf_sit-is", "name":"Telco Operations AI - 3. Intelligence Lab", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"notebook", "order":3}}';

ALTER NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."3_INTELLIGENCE_LAB" ADD LIVE VERSION FROM LAST;

-- ============================================================================
-- Verification
-- ============================================================================

SHOW NOTEBOOKS IN SCHEMA TELCO_OPERATIONS_AI.NOTEBOOKS;

SELECT 'Notebooks deployed successfully!' AS status,
       '1_DATA_PROCESSING' AS notebook_1,
       '2_ANALYZE_CALL_AUDIO' AS notebook_2,
       '3_INTELLIGENCE_LAB' AS notebook_3,
       CURRENT_TIMESTAMP() AS deployed_at;


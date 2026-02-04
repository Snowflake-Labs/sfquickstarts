-- ============================================================================
-- Distributed Medical Image Processing with MONAI - Setup Script
-- ============================================================================
-- Run this script BEFORE importing the notebooks.
-- This creates all required Snowflake objects for the MONAI solution.
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- ROLE SETUP
-- ============================================================================
CREATE OR REPLACE ROLE MONAI_DATA_SCIENTIST
  COMMENT = 'Role for MONAI medical image processing notebooks';

-- Grant role to current user
SET my_user_var = (SELECT '"' || CURRENT_USER() || '"');
GRANT ROLE MONAI_DATA_SCIENTIST TO USER identifier($my_user_var);

-- Grant Cortex privileges (required for AI/ML functions)
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE MONAI_DATA_SCIENTIST;

-- ============================================================================
-- WAREHOUSE SETUP
-- ============================================================================
CREATE OR REPLACE WAREHOUSE MONAI_WH
  WAREHOUSE_SIZE = 'SMALL'
  WAREHOUSE_TYPE = 'STANDARD'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for MONAI medical image processing';

GRANT USAGE ON WAREHOUSE MONAI_WH TO ROLE MONAI_DATA_SCIENTIST;
GRANT OPERATE ON WAREHOUSE MONAI_WH TO ROLE MONAI_DATA_SCIENTIST;

-- ============================================================================
-- DATABASE AND SCHEMAS
-- ============================================================================
CREATE OR REPLACE DATABASE MONAI_DB
  COMMENT = 'Database for MONAI medical image processing solution';

USE DATABASE MONAI_DB;

CREATE OR REPLACE SCHEMA UTILS
  COMMENT = 'MONAI utilities: stages, models, and configurations';

CREATE OR REPLACE SCHEMA RESULTS
  COMMENT = 'MONAI inference results and metrics';

-- Grant database and schema access
GRANT USAGE ON DATABASE MONAI_DB TO ROLE MONAI_DATA_SCIENTIST;
GRANT USAGE ON SCHEMA MONAI_DB.UTILS TO ROLE MONAI_DATA_SCIENTIST;
GRANT USAGE ON SCHEMA MONAI_DB.RESULTS TO ROLE MONAI_DATA_SCIENTIST;
GRANT ALL ON SCHEMA MONAI_DB.UTILS TO ROLE MONAI_DATA_SCIENTIST;
GRANT ALL ON SCHEMA MONAI_DB.RESULTS TO ROLE MONAI_DATA_SCIENTIST;

USE SCHEMA UTILS;

-- ============================================================================
-- ENCRYPTED STAGES FOR MEDICAL IMAGES
-- ============================================================================
CREATE OR REPLACE STAGE MONAI_MEDICAL_IMAGES_STG 
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Lung CT scans and segmentation masks in NIfTI format';

CREATE OR REPLACE STAGE RESULTS_STG 
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Registered images, model checkpoints, and inference outputs';

-- Grant stage access
GRANT READ, WRITE ON STAGE MONAI_DB.UTILS.MONAI_MEDICAL_IMAGES_STG TO ROLE MONAI_DATA_SCIENTIST;
GRANT READ, WRITE ON STAGE MONAI_DB.UTILS.RESULTS_STG TO ROLE MONAI_DATA_SCIENTIST;

-- ============================================================================
-- NETWORK RULE AND EXTERNAL ACCESS INTEGRATION
-- ============================================================================
CREATE OR REPLACE NETWORK RULE ALLOW_ALL_NETWORK_RULES
  MODE = EGRESS 
  TYPE = HOST_PORT
  VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80')
  COMMENT = 'Allow outbound HTTPS/HTTP for package installation';

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION MONAI_ALLOW_ALL_EAI 
  ALLOWED_NETWORK_RULES = (MONAI_DB.UTILS.ALLOW_ALL_NETWORK_RULES)
  ENABLED = TRUE
  COMMENT = 'External access for MONAI notebooks to install dependencies';

GRANT USAGE ON INTEGRATION MONAI_ALLOW_ALL_EAI TO ROLE MONAI_DATA_SCIENTIST;

-- ============================================================================
-- GPU COMPUTE POOL
-- ============================================================================
CREATE COMPUTE POOL IF NOT EXISTS MONAI_GPU_ML_M_POOL 
  MIN_NODES = 1
  MAX_NODES = 8 
  INSTANCE_FAMILY = 'GPU_NV_M'
  COMMENT = 'GPU compute pool for MONAI medical image processing';

GRANT USAGE ON COMPUTE POOL MONAI_GPU_ML_M_POOL TO ROLE MONAI_DATA_SCIENTIST;

-- ============================================================================
-- NOTEBOOK PRIVILEGES
-- ============================================================================
GRANT CREATE NOTEBOOK ON SCHEMA MONAI_DB.UTILS TO ROLE MONAI_DATA_SCIENTIST;
GRANT CREATE MODEL ON SCHEMA MONAI_DB.UTILS TO ROLE MONAI_DATA_SCIENTIST;
GRANT CREATE TABLE ON SCHEMA MONAI_DB.UTILS TO ROLE MONAI_DATA_SCIENTIST;
GRANT CREATE TABLE ON SCHEMA MONAI_DB.RESULTS TO ROLE MONAI_DATA_SCIENTIST;

-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT 'Setup complete! Verify objects below:' AS status;
SHOW SCHEMAS IN DATABASE MONAI_DB;
SHOW STAGES IN SCHEMA MONAI_DB.UTILS;
SHOW NETWORK RULES IN SCHEMA MONAI_DB.UTILS;
SHOW EXTERNAL ACCESS INTEGRATIONS LIKE '%MONAI%';
SHOW COMPUTE POOLS LIKE '%MONAI%';

-- Switch to the data scientist role for notebook work
USE ROLE MONAI_DATA_SCIENTIST;
USE WAREHOUSE MONAI_WH;
USE DATABASE MONAI_DB;
USE SCHEMA UTILS;

SELECT 'Infrastructure setup complete!' AS status, 
       CURRENT_ROLE() AS current_role, 
       CURRENT_WAREHOUSE() AS current_warehouse,
       CURRENT_DATABASE() AS current_database;

-- ============================================================================
-- NEXT STEPS: IMPORT NOTEBOOKS VIA SNOWSIGHT UI
-- ============================================================================
-- 1. Download notebooks from GitHub:
--    https://github.com/Snowflake-Labs/sfguide-distributed-medical-image-processing-with-monai/tree/main/notebooks
--
-- 2. In Snowsight, navigate to Data → Notebooks
--
-- 3. Click the + button and select "Import .ipynb file"
--
-- 4. Import each notebook:
--    - 01_ingest_data.ipynb
--    - 02_model_training.ipynb  
--    - 03_model_inference.ipynb
--
-- 5. For EACH notebook, configure these settings:
--    - Database: MONAI_DB
--    - Schema: UTILS
--    - Warehouse: MONAI_WH
--    - Compute Pool: MONAI_GPU_ML_M_POOL
--    - External Access Integration: MONAI_ALLOW_ALL_EAI
--
-- 6. Run notebooks in order: 01 → 02 → 03
-- ============================================================================

-- ============================================================================
-- TEARDOWN SCRIPT (Uncomment to clean up all resources)
-- ============================================================================
-- IMPORTANT: Stop and delete notebooks manually in Snowsight first,
-- then run the commands below.

-- USE ROLE ACCOUNTADMIN;
-- DROP COMPUTE POOL IF EXISTS MONAI_GPU_ML_M_POOL;
-- DROP EXTERNAL ACCESS INTEGRATION IF EXISTS MONAI_ALLOW_ALL_EAI;
-- DROP DATABASE IF EXISTS MONAI_DB CASCADE;
-- DROP WAREHOUSE IF EXISTS MONAI_WH;
-- DROP ROLE IF EXISTS MONAI_DATA_SCIENTIST;

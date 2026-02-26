-- MONAI Quickstart: Snowflake Infrastructure Setup
-- Run as ACCOUNTADMIN

-- ============================================================================
-- ROLE AND USER
-- ============================================================================

CREATE ROLE IF NOT EXISTS MONAI_USER;

-- Grant role to the user running this script
SET current_user_name = CURRENT_USER();
GRANT ROLE MONAI_USER TO USER IDENTIFIER($current_user_name);

-- ============================================================================
-- WAREHOUSE
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS MONAI_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

GRANT USAGE ON WAREHOUSE MONAI_WH TO ROLE MONAI_USER;

-- ============================================================================
-- DATABASE AND SCHEMA
-- ============================================================================

CREATE DATABASE IF NOT EXISTS MONAI_QUICKSTART_DB;
CREATE SCHEMA IF NOT EXISTS MONAI_QUICKSTART_DB.ML;

GRANT USAGE ON DATABASE MONAI_QUICKSTART_DB TO ROLE MONAI_USER;
GRANT ALL ON SCHEMA MONAI_QUICKSTART_DB.ML TO ROLE MONAI_USER;

-- ============================================================================
-- STAGES
-- ============================================================================

USE SCHEMA MONAI_QUICKSTART_DB.ML;

CREATE STAGE IF NOT EXISTS MEDICAL_IMAGES_STG
    DIRECTORY = (ENABLE = TRUE);

CREATE STAGE IF NOT EXISTS MODEL_ARTIFACTS_STG;
CREATE STAGE IF NOT EXISTS BATCH_INPUT_STG;
CREATE STAGE IF NOT EXISTS BATCH_OUTPUT_STG;

GRANT ALL ON ALL STAGES IN SCHEMA MONAI_QUICKSTART_DB.ML TO ROLE MONAI_USER;

-- ============================================================================
-- COMPUTE POOL (GPU)
-- ============================================================================

CREATE COMPUTE POOL IF NOT EXISTS MONAI_GPU_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = GPU_NV_S
    AUTO_RESUME = TRUE;

GRANT USAGE ON COMPUTE POOL MONAI_GPU_POOL TO ROLE MONAI_USER;

-- ============================================================================
-- EXTERNAL ACCESS (for downloading data and packages)
-- ============================================================================

-- PyPI access for installing Python packages in remote jobs
CREATE OR REPLACE NETWORK RULE PYPI_RULE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('pypi.org:443', 'files.pythonhosted.org:443');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION PYPI_EAI
    ALLOWED_NETWORK_RULES = (PYPI_RULE)
    ENABLED = TRUE;

GRANT USAGE ON INTEGRATION PYPI_EAI TO ROLE MONAI_USER;

-- Zenodo access for downloading sample data
CREATE OR REPLACE NETWORK RULE ZENODO_RULE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('zenodo.org:443');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION ZENODO_EAI
    ALLOWED_NETWORK_RULES = (ZENODO_RULE)
    ENABLED = TRUE;

GRANT USAGE ON INTEGRATION ZENODO_EAI TO ROLE MONAI_USER;

-- ============================================================================
-- MODEL REGISTRY PERMISSIONS
-- ============================================================================

GRANT CREATE MODEL ON SCHEMA MONAI_QUICKSTART_DB.ML TO ROLE MONAI_USER;

-- ============================================================================
-- VERIFY
-- ============================================================================

SHOW GRANTS TO ROLE MONAI_USER;

SELECT 'Setup complete. Switch to MONAI_USER role to continue.' AS STATUS;

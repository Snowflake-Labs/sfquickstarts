-- =============================================================================
-- RelationalAI for supply chain analysis: notebook access
--
-- Run after load_data.sql, as ACCOUNTADMIN.
-- Prerequisite: the RelationalAI Native App is installed and activated
-- (https://docs.relational.ai/get-started/set-up-relationalai-in-snowflake).
-- =============================================================================
USE ROLE ACCOUNTADMIN;

-- 1. Check the RelationalAI app is healthy: expect main / otel-collector = READY and CDC_ENABLED = TRUE.
CALL RELATIONALAI.APP.SERVICE_STATUS();
CALL RELATIONALAI.APP.CDC_STATUS();

-- 2. Egress rule for RelationalAI query results.
--    PyRel downloads results from a presigned URL on the RelationalAI app's S3 stage.
--    Replace the host with the one for your account/region. You can find it in the
--    "Max retries exceeded ... HTTPSConnectionPool(host='...')" error from a first query run.
CREATE OR REPLACE NETWORK RULE RAI_QUICKSTART.SUPPLY_CHAIN.RAI_RESULTS_RULE
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('sfc-ie-ds1-31-customer-stage.s3.eu-west-1.amazonaws.com:443');

-- 3. External access integration: PyPI (to pip install relationalai) + RelationalAI results.
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION RAI_NOTEBOOK_ACCESS
  ALLOWED_NETWORK_RULES = (SNOWFLAKE.EXTERNAL_ACCESS.PYPI_RULE, RAI_QUICKSTART.SUPPLY_CHAIN.RAI_RESULTS_RULE)
  ENABLED = TRUE;

-- 4. Let the demo role use the integration and a Container Runtime compute pool, and create notebooks.
GRANT USAGE ON INTEGRATION RAI_NOTEBOOK_ACCESS TO ROLE RAI_QS_ROLE;
GRANT USAGE ON COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU TO ROLE RAI_QS_ROLE;
GRANT CREATE NOTEBOOK ON SCHEMA RAI_QUICKSTART.SUPPLY_CHAIN TO ROLE RAI_QS_ROLE;

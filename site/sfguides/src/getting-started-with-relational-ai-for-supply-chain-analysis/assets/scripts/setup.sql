-- =============================================================================
-- RelationalAI for supply chain analysis: warehouse and database
--
-- Run once as ACCOUNTADMIN, after the RelationalAI setup
-- (https://docs.relational.ai/get-started/set-up-relationalai-in-snowflake).
-- That setup creates the role RAI_DEVELOPER and the OAuth integration that PyRel
-- signs in with. This script only adds a warehouse and an empty schema for that role.
-- =============================================================================
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS RAI_QS_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;
-- Cap runaway statements (e.g. a recursive query looping on the planted supplier cycle).
ALTER WAREHOUSE RAI_QS_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 600;
GRANT USAGE ON WAREHOUSE RAI_QS_WH TO ROLE RAI_DEVELOPER;

CREATE DATABASE IF NOT EXISTS RAI_QUICKSTART;
CREATE SCHEMA IF NOT EXISTS RAI_QUICKSTART.SUPPLY_CHAIN;
GRANT OWNERSHIP ON DATABASE RAI_QUICKSTART TO ROLE RAI_DEVELOPER COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA RAI_QUICKSTART.SUPPLY_CHAIN TO ROLE RAI_DEVELOPER COPY CURRENT GRANTS;

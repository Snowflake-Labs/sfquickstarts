USE ROLE ACCOUNTADMIN;

-- Configuration — edit these values
SET config_database   = 'SEC_FILINGS';
SET config_schema     = 'FILING_DATA';
SET config_warehouse  = 'FILING_WH';
SET config_user_agent = 'YourOrg SEC-Filing-Demo your_name@company.com';
SET config_start_date = '2025-02-03';  -- single day for quickstart
SET config_end_date   = '2025-02-03';

-- Create database and schema
CREATE DATABASE IF NOT EXISTS IDENTIFIER($config_database);
USE DATABASE IDENTIFIER($config_database);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($config_schema);
USE SCHEMA IDENTIFIER($config_schema);

-- Create a dedicated warehouse
CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($config_warehouse)
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'SEC pipeline: dynamically resized by RUN_PIPELINE()';
USE WAREHOUSE IDENTIFIER($config_warehouse);

-- Network access for SEC EDGAR
CREATE OR REPLACE NETWORK RULE SEC_EDGAR_NETWORK_RULE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('www.sec.gov:443', 'data.sec.gov:443', 'efts.sec.gov:443');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION SEC_EDGAR_EAI
    ALLOWED_NETWORK_RULES = (SEC_EDGAR_NETWORK_RULE)
    ENABLED = TRUE;
-- Using ACCOUNTADMIN, create a new role for this exercise 
USE ROLE ACCOUNTADMIN;
SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;
CREATE OR REPLACE ROLE E2E_SNOW_MLOPS_ROLE;

-- Grant necessary permissions to create databases, compute pools, and service endpoints to new role
GRANT CREATE DATABASE on ACCOUNT to ROLE E2E_SNOW_MLOPS_ROLE; 
GRANT CREATE COMPUTE POOL on ACCOUNT to ROLE E2E_SNOW_MLOPS_ROLE;
GRANT BIND SERVICE ENDPOINT on ACCOUNT to ROLE E2E_SNOW_MLOPS_ROLE;

-- grant new role to user and switch to that role
GRANT ROLE E2E_SNOW_MLOPS_ROLE to USER identifier($USERNAME);
USE ROLE E2E_SNOW_MLOPS_ROLE;

-- Create warehouse
CREATE OR REPLACE WAREHOUSE E2E_SNOW_MLOPS_WH WITH WAREHOUSE_SIZE='MEDIUM';

-- Create Database 
CREATE OR REPLACE DATABASE E2E_SNOW_MLOPS_DB;

-- Create Schema
CREATE OR REPLACE SCHEMA MLOPS_SCHEMA;


-- Create compute pool
CREATE COMPUTE POOL IF NOT EXISTS MLOPS_COMPUTE_POOL 
 MIN_NODES = 1
 MAX_NODES = 1
 INSTANCE_FAMILY = CPU_X64_M;

-- Using accountadmin, grant privilege to create network rules and integrations on newly created db
USE ROLE ACCOUNTADMIN;
GRANT CREATE NETWORK RULE on SCHEMA MLOPS_SCHEMA to ROLE E2E_SNOW_MLOPS_ROLE;
GRANT CREATE INTEGRATION on ACCOUNT to ROLE E2E_SNOW_MLOPS_ROLE;
USE ROLE E2E_SNOW_MLOPS_ROLE;


 --Create network rule and api integration to install packages from pypi
CREATE OR REPLACE NETWORK RULE mlops_pypi_network_rule
 MODE = EGRESS
 TYPE = HOST_PORT
 VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org',  'files.pythonhosted.org');

 -- Create external access integration on top of network rule for pypi access
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION mlops_pypi_access_integration
 ALLOWED_NETWORK_RULES = (mlops_pypi_network_rule)
 ENABLED = true;

-- Create an API integration with Github
CREATE OR REPLACE API INTEGRATION GITHUB_INTEGRATION_E2E_SNOW_MLOPS
   api_provider = git_https_api
   api_allowed_prefixes = ('https://github.com/sfc-gh-ebotwick/')
   enabled = true
   comment='Git integration with Snowflake Demo Github Repository.';

-- Create the integration with the Github demo repository
CREATE OR REPLACE GIT REPOSITORY GITHUB_REPO_E2E_SNOW_MLOPS
   ORIGIN = 'https://github.com/sfc-gh-ebotwick/e2e_ML_in_Snowflake' 
   API_INTEGRATION = 'GITHUB_INTEGRATION_E2E_SNOW_MLOPS' 
   COMMENT = 'Github Repository ';

-- Fetch most recent files from Github repository
ALTER GIT REPOSITORY GITHUB_REPO_E2E_SNOW_MLOPS FETCH;

-- Copy notebook into snowflake configure runtime settings
CREATE OR REPLACE NOTEBOOK E2E_SNOW_MLOPS_DB.MLOPS_SCHEMA.TRAIN_DEPLOY_MONITOR_ML
FROM '@E2E_SNOW_MLOPS_DB.MLOPS_SCHEMA.GITHUB_REPO_E2E_SNOW_MLOPS/branches/main/' 
MAIN_FILE = 'train_deploy_monitor_ML_in_snowflake.ipynb' QUERY_WAREHOUSE = E2E_SNOW_MLOPS_WH
RUNTIME_NAME = 'SYSTEM$BASIC_RUNTIME' 
COMPUTE_POOL = 'MLOPS_COMPUTE_POOL'
IDLE_AUTO_SHUTDOWN_TIME_SECONDS = 3600;

alter NOTEBOOK E2E_SNOW_MLOPS_DB.MLOPS_SCHEMA.TRAIN_DEPLOY_MONITOR_ML set EXTERNAL_ACCESS_INTEGRATIONS = ( 'mlops_pypi_access_integration' )

--DONE! Now you can access your newly created notebook with your E2E_SNOW_MLOPS_ROLE and run through the end-to-end workflow!

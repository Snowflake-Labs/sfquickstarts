ALTER SESSION SET query_tag = '{"origin":"sf_pse", "name":"aiml_multinode_multigpu_notebooks_container_runtime", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"sql"}}';
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS MULTINODE_MULTIGPU_MYDB;
USE DATABASE MULTINODE_MULTIGPU_MYDB;

CREATE SCHEMA IF NOT EXISTS AUDIO_TRANSCRIPTION_SCH;
USE SCHEMA AUDIO_TRANSCRIPTION_SCH;

CREATE WAREHOUSE ML_MODEL_WH;
USE WAREHOUSE ML_MODEL_WH;

-- Create COMPUTE POOLS

CREATE COMPUTE POOL if not exists audio_processing_cp_data_download
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_M
  INITIALLY_SUSPENDED = TRUE
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 300;

CREATE COMPUTE POOL if not exists audio_processing_cp_gpu_nv_s_5_nodes
  MIN_NODES = 5
  MAX_NODES = 5
  INSTANCE_FAMILY = GPU_NV_S
  INITIALLY_SUSPENDED = TRUE
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 300;


-- Create and grant access to EAIs
-- Substep #1: create network rules (these are schema-level objects; end users do not need direct access to the network rules)

create or replace network rule allow_all_rule
  TYPE = 'HOST_PORT'
  MODE= 'EGRESS'
  VALUE_LIST = ('0.0.0.0:443','0.0.0.0:80');


-- Substep #2: create external access integration (these are account-level objects; end users need access to this to access the public internet with endpoints defined in network rules)

USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION allow_all_integration
  ALLOWED_NETWORK_RULES = (allow_all_rule)
  ENABLED = true;

GRANT USAGE ON INTEGRATION allow_all_integration TO ROLE sysadmin;
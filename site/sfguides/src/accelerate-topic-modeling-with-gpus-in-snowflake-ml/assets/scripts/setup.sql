-- ============================================
-- SETUP FOR TOPIC MODELING NOTEBOOK
-- ============================================

-- Step 1: Create Network Rule (Allow All)
-- ============================================
CREATE OR REPLACE NETWORK RULE allow_all_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80');


-- Step 2: Create External Access Integration
-- ============================================
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION topic_modeling_eai
  ALLOWED_NETWORK_RULES = (allow_all_rule)
  ENABLED = TRUE;


-- Step 3: Create GPU Compute Pool
-- ============================================
CREATE COMPUTE POOL IF NOT EXISTS topic_modeling_gpu_pool
  MIN_NODES = 3
  MAX_NODES = 3
  INSTANCE_FAMILY = GPU_NV_M
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 600;


-- Step 4: Grant Permissions 
-- ============================================
GRANT USAGE ON COMPUTE POOL topic_modeling_gpu_pool TO ROLE ACCOUNTADMIN;
GRANT USAGE ON INTEGRATION topic_modeling_eai TO ROLE ACCOUNTADMIN;

-- ============================================
-- COMPLETE SETUP FOR TOPIC MODELING NOTEBOOK
-- ============================================


-- ============================================================
-- STEP 1: SNOWFLAKE RBAC SETUP
-- ============================================================
-- Creates tenant roles, service users, and assigns roles.
-- Run as ACCOUNTADMIN in a Snowsight worksheet.
-- ============================================================

USE ROLE ACCOUNTADMIN;

-- Create tenant roles
CREATE ROLE IF NOT EXISTS COCO_TENANT_ALPHA;
CREATE ROLE IF NOT EXISTS COCO_TENANT_BETA;

-- Grant Cortex access to both roles
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE COCO_TENANT_ALPHA;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE COCO_TENANT_BETA;

-- Create service users (TYPE=SERVICE means no interactive login)
CREATE USER IF NOT EXISTS COCO_USER_ALPHA
    TYPE = SERVICE
    DEFAULT_ROLE = COCO_TENANT_ALPHA;
CREATE USER IF NOT EXISTS COCO_USER_BETA
    TYPE = SERVICE
    DEFAULT_ROLE = COCO_TENANT_BETA;

-- Assign roles
GRANT ROLE COCO_TENANT_ALPHA TO USER COCO_USER_ALPHA;
GRANT ROLE COCO_TENANT_BETA TO USER COCO_USER_BETA;

-- Register RSA public keys (replace with your actual keys)
-- Extract key content: awk 'NR>1 && !/END/' keys/alpha_rsa_key.pub | tr -d '\n'
ALTER USER COCO_USER_ALPHA SET RSA_PUBLIC_KEY='MIIBIjANBgkqhki...your-alpha-key...';
ALTER USER COCO_USER_BETA  SET RSA_PUBLIC_KEY='MIIBIjANBgkqhki...your-beta-key...';

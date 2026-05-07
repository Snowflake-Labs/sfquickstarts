-- ============================================================
-- STEP 2: ENABLE MODEL RBAC
-- ============================================================
-- Refreshes available model roles, enforces strict RBAC,
-- and grants specific models to each tenant role.
-- Run as ACCOUNTADMIN in a Snowsight worksheet.
-- ============================================================

USE ROLE ACCOUNTADMIN;

-- Refresh available model roles
CALL SNOWFLAKE.MODELS.CORTEX_BASE_MODELS_REFRESH();

-- Enforce strict RBAC (no open access)
ALTER ACCOUNT SET CORTEX_MODELS_ALLOWLIST = 'None';

-- Alpha models
GRANT APPLICATION ROLE SNOWFLAKE."CORTEX-MODEL-ROLE-CLAUDE-4-SONNET" TO ROLE COCO_TENANT_ALPHA;
GRANT APPLICATION ROLE SNOWFLAKE."CORTEX-MODEL-ROLE-MISTRAL-LARGE2" TO ROLE COCO_TENANT_ALPHA;

-- Beta models
GRANT APPLICATION ROLE SNOWFLAKE."CORTEX-MODEL-ROLE-OPENAI-GPT-4.1" TO ROLE COCO_TENANT_BETA;
GRANT APPLICATION ROLE SNOWFLAKE."CORTEX-MODEL-ROLE-LLAMA3.1-70B" TO ROLE COCO_TENANT_BETA;
GRANT APPLICATION ROLE SNOWFLAKE."CORTEX-MODEL-ROLE-DEEPSEEK-R1" TO ROLE COCO_TENANT_BETA;

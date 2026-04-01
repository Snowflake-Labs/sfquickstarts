/*=============================================================================
  02 - S3 STORAGE INTEGRATION & EXTERNAL STAGES
  Healthcare AI Intelligence Pipeline

  Creates:
    - S3 storage integration (Snowflake <-> AWS trust)
    - 3 external stages (PDFs, TXT, Audio) linked to S3 prefixes
    - 1 internal stage for semantic model YAML

  IMPORTANT: Replace these placeholders before running:
    <YOUR_S3_BUCKET_NAME>     -> your actual S3 bucket name
    <YOUR_AWS_IAM_ROLE_ARN>   -> arn:aws:iam::<account_id>:role/<role_name>

  Depends on: 01_database_and_schemas.sql
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 1. STORAGE INTEGRATION
-----------------------------------------------------------------------
CREATE OR REPLACE STORAGE INTEGRATION HEALTHCARE_S3_INTEGRATION
  TYPE                      = EXTERNAL_STAGE
  STORAGE_PROVIDER          = 'S3'
  ENABLED                   = TRUE
  STORAGE_AWS_ROLE_ARN      = '<YOUR_AWS_IAM_ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<YOUR_S3_BUCKET_NAME>/healthcare/')
  COMMENT = 'Storage integration for Healthcare AI demo S3 bucket';

-- Get Snowflake IAM user ARN and external ID for AWS trust policy:
DESCRIBE INTEGRATION HEALTHCARE_S3_INTEGRATION;
-- Record: STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID
-- Update your IAM role trust policy with these values (see 14_aws_setup_guide.sql)

-----------------------------------------------------------------------
-- 2. GRANT USAGE (if using roles other than ACCOUNTADMIN)
-----------------------------------------------------------------------
GRANT USAGE ON INTEGRATION HEALTHCARE_S3_INTEGRATION TO ROLE SYSADMIN;

-----------------------------------------------------------------------
-- 3. EXTERNAL STAGES (one per file type prefix in S3)
-----------------------------------------------------------------------
CREATE OR REPLACE STAGE RAW.S3_MEDICAL_DOCS
  URL                 = 's3://<YOUR_S3_BUCKET_NAME>/healthcare/pdfs/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY           = (ENABLE = TRUE AUTO_REFRESH = TRUE)
  COMMENT = 'S3 stage for incoming medical PDF documents';

CREATE OR REPLACE STAGE RAW.S3_MEDICAL_TXT
  URL                 = 's3://<YOUR_S3_BUCKET_NAME>/healthcare/txt/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY           = (ENABLE = TRUE AUTO_REFRESH = TRUE)
  COMMENT = 'S3 stage for incoming medical text documents';

CREATE OR REPLACE STAGE RAW.S3_MEDICAL_AUDIO
  URL                 = 's3://<YOUR_S3_BUCKET_NAME>/healthcare/audio/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY           = (ENABLE = TRUE AUTO_REFRESH = TRUE)
  COMMENT = 'S3 stage for incoming patient consultation audio files (WAV and MP3)';

-----------------------------------------------------------------------
-- 4. INTERNAL STAGE (for semantic model YAML)
-----------------------------------------------------------------------
CREATE OR REPLACE STAGE ANALYTICS.SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Internal stage for semantic model YAML files';

-----------------------------------------------------------------------
-- 5. VERIFY
-----------------------------------------------------------------------
SHOW INTEGRATIONS LIKE 'HEALTHCARE%';
SHOW STAGES IN DATABASE HEALTHCARE_AI_DEMO;

-- Run as a role that can create a database, an external stage, and an Iceberg table.
-- Replace the placeholders before you execute the script.
--
-- Pick one storage path:
--   A. SNOWFLAKE_MANAGED  — AWS or Azure commercial accounts. No external volume.
--   B. Customer volume    — name the volume and a base-location prefix.
-- The extract stage is required on both paths. Its URL must be the path the extract writes to.

CREATE DATABASE IF NOT EXISTS ICEBERG_LAB;
CREATE SCHEMA IF NOT EXISTS ICEBERG_LAB.PUBLIC;

-- The migration role needs to create the Iceberg table. ACCOUNTADMIN already can.
-- GRANT CREATE ICEBERG TABLE ON SCHEMA ICEBERG_LAB.PUBLIC TO ROLE <MIGRATION_ROLE>;

-- ---------------------------------------------------------------------------
-- Extract stage. Point URL at the bucket or container the extract will write.
-- CETAS, UNLOAD, and WRITE_NOS each land in one path. The stage must be that path.
-- ---------------------------------------------------------------------------

CREATE STORAGE INTEGRATION IF NOT EXISTS ICEBERG_LAB_EXTRACT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'  -- or 'AZURE'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<IAM_ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('<EXTRACT_URL>');

-- After DESCRIBE STORAGE INTEGRATION ICEBERG_LAB_EXTRACT, put
-- STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID on the IAM trust policy.

CREATE STAGE IF NOT EXISTS ICEBERG_LAB.PUBLIC.EXTRACT_STAGE
  URL = '<EXTRACT_URL>'
  STORAGE_INTEGRATION = ICEBERG_LAB_EXTRACT;

-- ---------------------------------------------------------------------------
-- Path B only. Skip this block when externalVolume will be SNOWFLAKE_MANAGED.
-- ---------------------------------------------------------------------------

-- CREATE EXTERNAL VOLUME IF NOT EXISTS ICEBERG_LAB_VOLUME
--   STORAGE_LOCATIONS = (
--     (
--       NAME = 'iceberg-lab-location'
--       STORAGE_BASE_URL = '<TABLE_BASE_URL>'
--       STORAGE_PROVIDER = 'S3'
--       STORAGE_AWS_ROLE_ARN = '<IAM_ROLE_ARN>'
--     )
--   );
--
-- DESCRIBE EXTERNAL VOLUME ICEBERG_LAB_VOLUME;
-- SELECT SYSTEM$VERIFY_EXTERNAL_VOLUME('ICEBERG_LAB_VOLUME');
-- GRANT USAGE ON EXTERNAL VOLUME ICEBERG_LAB_VOLUME TO ROLE <MIGRATION_ROLE>;

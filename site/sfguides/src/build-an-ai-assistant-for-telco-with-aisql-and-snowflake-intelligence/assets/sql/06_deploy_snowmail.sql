-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 06: Deploy SnowMail Native App
-- ============================================================================
-- Description: Deploys SnowMail as a Snowflake Native Application
-- providing a Gmail-style email viewer for Telco Operations AI
-- Prerequisites: Run scripts 01-05 first
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE TELCO_WH;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- Step 1: Create Application Package Infrastructure
-- ============================================================================

CREATE DATABASE IF NOT EXISTS TELCO_OPERATIONS_AI_SNOWMAIL_PKG;
CREATE SCHEMA IF NOT EXISTS TELCO_OPERATIONS_AI_SNOWMAIL_PKG.APP_CODE;

CREATE STAGE IF NOT EXISTS TELCO_OPERATIONS_AI_SNOWMAIL_PKG.APP_CODE.SNOWMAIL_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for SnowMail Native App artifacts';

-- ============================================================================
-- Step 2: Copy Application Files from Git Repository
-- ============================================================================

COPY FILES INTO @TELCO_OPERATIONS_AI_SNOWMAIL_PKG.APP_CODE.SNOWMAIL_STAGE
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/native_app_snowmail/
FILES = ('manifest.yml', 'setup.sql');

COPY FILES INTO @TELCO_OPERATIONS_AI_SNOWMAIL_PKG.APP_CODE.SNOWMAIL_STAGE/streamlit/
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/native_app_snowmail/streamlit/
FILES = ('email_viewer.py');

-- Verify files uploaded
LIST @TELCO_OPERATIONS_AI_SNOWMAIL_PKG.APP_CODE.SNOWMAIL_STAGE;

-- ============================================================================
-- Step 3: Create Application Package
-- ============================================================================

DROP APPLICATION IF EXISTS SNOWMAIL;
DROP APPLICATION PACKAGE IF EXISTS SNOWMAIL_PKG;

CREATE APPLICATION PACKAGE SNOWMAIL_PKG
    COMMENT = 'SnowMail - Gmail-style email viewer for Telco Operations AI'
    ENABLE_RELEASE_CHANNELS = FALSE;

ALTER APPLICATION PACKAGE SNOWMAIL_PKG 
    ADD VERSION V1_0
    USING '@TELCO_OPERATIONS_AI_SNOWMAIL_PKG.APP_CODE.SNOWMAIL_STAGE'
    LABEL = 'SnowMail v1.0 - Telco Operations AI';

ALTER APPLICATION PACKAGE SNOWMAIL_PKG
    SET DEFAULT RELEASE DIRECTIVE
    VERSION = V1_0
    PATCH = 0;

-- ============================================================================
-- Step 4: Create Application Instance
-- ============================================================================

CREATE APPLICATION SNOWMAIL
    FROM APPLICATION PACKAGE SNOWMAIL_PKG
    COMMENT = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- Step 5: Grant Permissions to SnowMail Application
-- ============================================================================

GRANT USAGE ON DATABASE TELCO_OPERATIONS_AI TO APPLICATION SNOWMAIL;
GRANT USAGE ON SCHEMA TELCO_OPERATIONS_AI.DEFAULT_SCHEMA TO APPLICATION SNOWMAIL;
GRANT SELECT, DELETE ON TABLE TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.EMAIL_PREVIEWS TO APPLICATION SNOWMAIL;
GRANT USAGE ON WAREHOUSE TELCO_WH TO APPLICATION SNOWMAIL;

-- ============================================================================
-- Step 6: Create Email Notification Procedure
-- ============================================================================

CREATE OR REPLACE PROCEDURE TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.SEND_EMAIL_NOTIFICATION(
    SUBJECT_TEXT VARCHAR,
    MESSAGE_CONTENT VARCHAR,
    RECIPIENT_EMAIL VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    email_id VARCHAR;
    snowmail_url VARCHAR;
    org_name VARCHAR;
    account_name VARCHAR;
BEGIN
    -- Generate unique email ID
    email_id := 'EMAIL_' || TO_VARCHAR(DATEADD(ms, UNIFORM(1, 999, RANDOM()), CURRENT_TIMESTAMP()), 'YYYYMMDDHH24MISSFF3');
    
    -- Get account info for URL construction
    org_name := (SELECT CURRENT_ORGANIZATION_NAME());
    account_name := (SELECT CURRENT_ACCOUNT_NAME());
    
    -- Insert email into EMAIL_PREVIEWS table
    INSERT INTO TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.EMAIL_PREVIEWS (
        EMAIL_ID,
        RECIPIENT_EMAIL,
        SUBJECT,
        HTML_CONTENT,
        CREATED_AT,
        IS_READ,
        IS_STARRED
    )
    VALUES (
        :email_id,
        :RECIPIENT_EMAIL,
        :SUBJECT_TEXT,
        '<html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;">' ||
        '<h2 style="color: #29B5E8;">' || :SUBJECT_TEXT || '</h2>' ||
        '<p><strong>Date:</strong> ' || TO_VARCHAR(CURRENT_TIMESTAMP(), 'Mon DD, YYYY HH24:MI') || '</p>' ||
        '<div style="margin-top: 20px;">' || :MESSAGE_CONTENT || '</div>' ||
        '</body></html>',
        CURRENT_TIMESTAMP(),
        FALSE,
        FALSE
    );
    
    -- Construct SnowMail URL
    snowmail_url := 'https://app.snowflake.com/' || LOWER(:org_name) || '/' || LOWER(:account_name) || '/#/apps/application/SNOWMAIL/schema/APP_SCHEMA/streamlit/EMAIL_VIEWER';
    
    -- Return success message with URL
    RETURN '📧 Email sent! Email ID: ' || :email_id || '\n' ||
           '📬 VIEW IN SNOWMAIL: ' || :snowmail_url;
END;
$$;

GRANT USAGE ON PROCEDURE TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.SEND_EMAIL_NOTIFICATION(VARCHAR, VARCHAR, VARCHAR) TO ROLE PUBLIC;

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'SnowMail Native App deployed successfully!' as STATUS,
       'SNOWMAIL' as APP_NAME,
       'SNOWMAIL_PKG' as PACKAGE_NAME,
       'V1_0' as VERSION,
       CURRENT_TIMESTAMP() as deployed_at;


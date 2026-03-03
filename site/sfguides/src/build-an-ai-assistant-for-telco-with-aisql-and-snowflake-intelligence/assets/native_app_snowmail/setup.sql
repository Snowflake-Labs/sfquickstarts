-- SnowMail Native App Setup Script
-- Creates the necessary schema, roles, and Streamlit for the email viewer

-- Create application role
CREATE APPLICATION ROLE IF NOT EXISTS app_public;

-- Create versioned schema
CREATE OR ALTER VERSIONED SCHEMA app_schema;
GRANT USAGE ON SCHEMA app_schema TO APPLICATION ROLE app_public;

-- Note: The EMAIL_PREVIEWS table will be granted to the application during deployment
-- The Streamlit will query it directly

-- Create Streamlit email viewer
CREATE OR REPLACE STREAMLIT app_schema.email_viewer
    FROM 'streamlit'
    MAIN_FILE = 'email_viewer.py'
;

GRANT USAGE ON STREAMLIT app_schema.email_viewer TO APPLICATION ROLE app_public;

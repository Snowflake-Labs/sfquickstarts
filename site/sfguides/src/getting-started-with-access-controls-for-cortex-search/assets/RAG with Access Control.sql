USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS RAG_OWNER;
CREATE ROLE IF NOT EXISTS SKI;
CREATE ROLE IF NOT EXISTS BICYCLE;

-- Create the users to test access controls. It is strongly recommended that MFA is enabled for these users
CREATE OR REPLACE USER bicycle_user
    PASSWORD             = '<enter initial password>'
    LOGIN_NAME           = 'bicycle_user'
    FIRST_NAME           = 'Bicycle'
    LAST_NAME            = 'User'
    EMAIL                = '<enter your email>'
    DEFAULT_ROLE         = BICYCLE  
    MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE BICYCLE TO USER bicycle_user;

CREATE OR REPLACE USER ski_user
    PASSWORD             = '<enter initial password>'
    LOGIN_NAME           = 'ski_user'
    FIRST_NAME           = 'Ski'
    LAST_NAME            = 'User'
    EMAIL                = '<enter your email>'
    DEFAULT_ROLE         = SKI 
    MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE SKI TO USER ski_user;

GRANT CREATE DATABASE ON ACCOUNT TO ROLE RAG_OWNER;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE RAG_OWNER;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE RAG_OWNER;

SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;
GRANT ROLE RAG_OWNER to USER identifier($USERNAME);

-- Create compute

USE ROLE RAG_OWNER;

CREATE COMPUTE POOL IF NOT EXISTS RAG_STREAMLIT
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_XS;

CREATE WAREHOUSE IF NOT EXISTS RAG_WH
  WAREHOUSE_TYPE = STANDARD
  WAREHOUSE_SIZE = XSMALL;

--- Create database and schema

CREATE DATABASE IF NOT EXISTS RAG_DB;
USE DATABASE RAG_DB;
CREATE SCHEMA IF NOT EXISTS RAG_DB.RAG_SCHEMA;
USE SCHEMA RAG_SCHEMA;

--- Create network rule and apply it in External Access Integration

CREATE OR REPLACE NETWORK RULE pypi_network_rule
 MODE = EGRESS
 TYPE = HOST_PORT
 VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org',  'files.pythonhosted.org');

USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
 ALLOWED_NETWORK_RULES = (pypi_network_rule)
 ENABLED = true;

-- Grant necessary privileges

GRANT USAGE ON INTEGRATION pypi_access_integration TO ROLE RAG_OWNER;

GRANT CREATE STREAMLIT ON SCHEMA RAG_DB.RAG_SCHEMA TO ROLE RAG_OWNER;

GRANT USAGE ON WAREHOUSE RAG_WH TO ROLE BICYCLE;
GRANT USAGE ON WAREHOUSE RAG_WH TO ROLE SKI;

GRANT USAGE ON COMPUTE POOL RAG_STREAMLIT TO ROLE BICYCLE;
GRANT USAGE ON COMPUTE POOL RAG_STREAMLIT TO ROLE SKI;

GRANT USAGE ON DATABASE RAG_DB TO ROLE BICYCLE;
GRANT USAGE ON SCHEMA RAG_DB.RAG_SCHEMA TO ROLE BICYCLE;

GRANT USAGE ON DATABASE RAG_DB TO ROLE SKI;
GRANT USAGE ON SCHEMA RAG_DB.RAG_SCHEMA TO ROLE SKI;

-- Create stages for streamlit source code and source documentation

USE ROLE RAG_OWNER;

CREATE OR REPLACE STAGE STREAMLIT_UI DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE='SNOWFLAKE_SSE');
CREATE OR REPLACE STAGE SOURCE_DOCUMENTS DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE='SNOWFLAKE_SSE');

-- Return to UI to upload documents to SOURCE_DOCUMENTS stage

LS @SOURCE_DOCUMENTS;

USE SCHEMA RAG_DB.RAG_SCHEMA;

CREATE OR REPLACE TABLE documents_table AS
  (SELECT TO_FILE('@source_documents', RELATIVE_PATH) AS docs, 
    RELATIVE_PATH as RELATIVE_PATH
    FROM DIRECTORY(@source_documents));

-- Use Cortex AI function to parse PDF. Create identifier column so we can filter based on user attribute
CREATE OR REPLACE TABLE EXTRACTED_TEXT_TABLE AS (
    SELECT  RELATIVE_PATH, 
            AI_PARSE_DOCUMENT(docs, {'mode': 'OCR'}):content::VARCHAR AS EXTRACTED_TEXT,
            CASE
                WHEN RELATIVE_PATH ILIKE '%ski%' THEN 'SKI'
                WHEN RELATIVE_PATH ILIKE '%bike%' OR RELATIVE_PATH ILIKE '%bicycle%' THEN 'BICYCLE'
                ELSE 'Other'
            END AS product_department
            FROM documents_table
            );

-- Chunk parsed document for RAG
CREATE OR REPLACE TABLE CHUNKED_TABLE AS (
        SELECT
            e.*,
            c.value::VARCHAR AS chunk
        FROM EXTRACTED_TEXT_TABLE e,
        LATERAL FLATTEN(
            INPUT => snowflake.cortex.split_text_recursive_character(
                EXTRACTED_TEXT,
                'none',
                2000,
                300
            )
        ) c
    );

SELECT * FROM CHUNKED_TABLE;

--- Create Cortex Search Service

CREATE OR REPLACE CORTEX SEARCH SERVICE rag_cortex_search_service
  ON chunk
  ATTRIBUTES product_department
  WAREHOUSE = RAG_WH
  TARGET_LAG = '1 hour'
  INITIALIZE = ON_SCHEDULE
AS SELECT * FROM RAG_DB.RAG_SCHEMA.CHUNKED_TABLE;

DESC CORTEX SEARCH SERVICE rag_cortex_search_service;

ALTER CORTEX SEARCH SERVICE RAG_DB.RAG_SCHEMA.rag_cortex_search_service
  ADD SCORING PROFILE IF NOT EXISTS default_with_components
  '{
    "component_scores": true
  }';

  SELECT PARSE_JSON(
  SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
      'rag_cortex_search_service',
      '{
         "query": "Tell me about the Ski Bootz",
         "filter": {"@eq": {"product_department": "SKI"} },
         "limit":10
      }'
  )
)['results'] as results;

CREATE OR REPLACE STREAMLIT rag_access_control_app
  FROM '@rag_db.rag_schema.streamlit_ui/'
  MAIN_FILE = 'rag_access_control_streamlit_ui.py'
  RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
  COMPUTE_POOL = RAG_STREAMLIT
  QUERY_WAREHOUSE = RAG_WH
  EXTERNAL_ACCESS_INTEGRATIONS = (pypi_access_integration);

ALTER STREAMLIT rag_access_control_app ADD LIVE VERSION FROM LAST;

-- Clean Up
USE ROLE ACCOUNTADMIN;
DROP ROLE RAG_OWNER;
DROP ROLE SKI;
DROP ROLE BICYCLE;

DROP USER bicycle_user;
DROP USER ski_user;

ALTER COMPUTE POOL RAG_STREAMLIT STOP ALL;
DROP COMPUTE POOL RAG_STREAMLIT;
DROP WAREHOUSE RAG_WH;
DROP DATABASE RAG_DB CASCADE;
DROP EXTERNAL ACCESS INTEGRATION pypi_access_integration;
/*=============================================================================
  16 - SNOWFLAKE INTELLIGENCE SETUP & AGENT TESTS
  Healthcare AI Intelligence Pipeline

  Snowflake Intelligence provides a chat-based UI on top of the Cortex Agent.
  This file covers:
    1. UI setup instructions (manual — done in Snowsight)
    2. Direct SQL agent invocation tests
    3. Sample file read & AI function smoke tests

  Depends on: 13 (Cortex Agent)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 1. SNOWFLAKE INTELLIGENCE SETUP (UI Steps)
-----------------------------------------------------------------------
/*
  1. Navigate to Snowflake Intelligence in the Snowsight UI
     (left sidebar -> AI & ML -> Intelligence)
  2. Click "New Agent" or "Create"
  3. Configure:
     - Name: Healthcare Intelligence
     - Agent: HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT
  4. The agent automatically inherits 4 tools:
     - HealthcareAnalyst (structured queries via semantic view)
     - PDFSearch (search parsed PDF medical documents)
     - TXTSearch (search enriched text documents)
     - AudioSearch (search transcribed consultations)
  5. Test with the sample questions below
  6. Share with your team as needed
*/

-----------------------------------------------------------------------
-- 2. AGENT TEST QUERIES (run via SQL or Snowflake Intelligence)
-----------------------------------------------------------------------

-- Structured data queries (uses HealthcareAnalyst tool)
-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Which providers have the highest total billed amounts?'
-- );

-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'How many claims were denied and what were the reasons?'
-- );

-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Show me patients on Medicare Advantage with cardiology appointments'
-- );

-- PDF search queries (uses PDFSearch tool)
-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Find PDF documents mentioning diabetes or hypertension'
-- );

-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Find radiology reports with abnormal findings'
-- );

-- TXT search queries (uses TXTSearch tool)
-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Search text documents for clinical notes about medication changes'
-- );

-- Audio search queries (uses AudioSearch tool)
-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'What consultations discussed medication changes?'
-- );

-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Summarize the consultation notes for follow-up visits'
-- );

-- Cross-tool queries (uses multiple tools)
-- SELECT SNOWFLAKE.CORTEX.INVOKE_AGENT(
--   'HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT',
--   'Which patients have both documents and audio recordings? What were they about?'
-- );

-----------------------------------------------------------------------
-- 3. QUICK AI FUNCTION SMOKE TESTS ON STAGED FILES
--    Run these to verify S3 -> Stage -> AI Function works end-to-end
-----------------------------------------------------------------------

-- Test AI_PARSE_DOCUMENT on first PDF
SELECT
  d.RELATIVE_PATH                         AS FILE_NAME,
  LEFT(
    AI_PARSE_DOCUMENT(
      TO_FILE('@RAW.S3_MEDICAL_DOCS', d.RELATIVE_PATH), 'OCR'
    ):content::VARCHAR,
    300
  )                                       AS PARSED_TEXT_PREVIEW
FROM DIRECTORY(@RAW.S3_MEDICAL_DOCS) d
LIMIT 1;

-- Test reading a TXT file
SELECT
  d.RELATIVE_PATH                         AS FILE_NAME,
  LEFT(
    AI_COMPLETE(
      'claude-3-5-sonnet',
      CONCAT('Return the first 500 characters of this document exactly as-is:\n\n',
        TO_VARCHAR(TO_FILE('@RAW.S3_MEDICAL_TXT', d.RELATIVE_PATH)))
    ), 500
  )                                       AS CONTENT_PREVIEW
FROM DIRECTORY(@RAW.S3_MEDICAL_TXT) d
LIMIT 1;

-- Test AI_TRANSCRIBE on first audio file
SELECT
  d.RELATIVE_PATH                         AS FILE_NAME,
  LEFT(
    AI_TRANSCRIBE(
      TO_FILE('@RAW.S3_MEDICAL_AUDIO', d.RELATIVE_PATH),
      OBJECT_CONSTRUCT('mode', 'transcript')
    ):text::VARCHAR,
    300
  )                                       AS TRANSCRIPT_PREVIEW
FROM DIRECTORY(@RAW.S3_MEDICAL_AUDIO) d
LIMIT 1;

-----------------------------------------------------------------------
-- 4. PIPELINE SUMMARY
-----------------------------------------------------------------------
SELECT 'FILES_LOG'           AS OBJECT, COUNT(*) AS ROW_COUNT FROM RAW.FILES_LOG
UNION ALL
SELECT 'PDF_INTELLIGENCE',   COUNT(*) FROM PROCESSED.PDF_INTELLIGENCE
UNION ALL
SELECT 'TXT_INTELLIGENCE',   COUNT(*) FROM PROCESSED.TXT_INTELLIGENCE
UNION ALL
SELECT 'AUDIO_INTELLIGENCE', COUNT(*) FROM PROCESSED.AUDIO_INTELLIGENCE
UNION ALL
SELECT 'PROVIDERS',          COUNT(*) FROM ANALYTICS.PROVIDERS
UNION ALL
SELECT 'PATIENTS',           COUNT(*) FROM ANALYTICS.PATIENTS
UNION ALL
SELECT 'CLAIMS',             COUNT(*) FROM ANALYTICS.CLAIMS
UNION ALL
SELECT 'APPOINTMENTS',       COUNT(*) FROM ANALYTICS.APPOINTMENTS;

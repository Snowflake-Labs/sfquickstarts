/*=============================================================================
  11 - CORTEX SEARCH SERVICES (one per intelligence table)
  Healthcare AI Intelligence Pipeline

  Three search services for RAG over unstructured content:
    1. PDF_SEARCH   — parsed medical documents (PDFs)
    2. TXT_SEARCH   — text medical documents (TXT)
    3. AUDIO_SEARCH — transcribed patient consultations (WAV/MP3)

  Depends on: 04 (intelligence tables)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA PROCESSED;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 1. PDF SEARCH — over parsed & enriched PDF content
-----------------------------------------------------------------------
CREATE OR REPLACE CORTEX SEARCH SERVICE PROCESSED.PDF_SEARCH
  ON SEARCH_TEXT
  ATTRIBUTES DOC_CATEGORY, PATIENT_NAME, PROVIDER_NAME, DIAGNOSIS, DETECTED_LANGUAGE, SENTIMENT_SCORE, PROCESSED_AT
  WAREHOUSE = HEALTHCARE_AI_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
  COMMENT = 'Cortex Search over AI-parsed medical PDF documents'
AS (
    SELECT
      DOC_ID,
      FILE_NAME,
      CONCAT(
        COALESCE(PARSED_TEXT, ''), '\n\n',
        'SUMMARY: ', COALESCE(SUMMARY, ''), '\n\n',
        'INSIGHTS: ', COALESCE(KEY_INSIGHTS, ''), '\n\n',
        'DIAGNOSIS: ', COALESCE(EXTRACTED_FIELDS:diagnosis::VARCHAR, '')
      )                                                   AS SEARCH_TEXT,
      DOC_CATEGORY,
      COALESCE(EXTRACTED_FIELDS:patient_name::VARCHAR, 'Unknown')  AS PATIENT_NAME,
      COALESCE(EXTRACTED_FIELDS:provider_name::VARCHAR, 'Unknown') AS PROVIDER_NAME,
      COALESCE(EXTRACTED_FIELDS:diagnosis::VARCHAR, '')   AS DIAGNOSIS,
      DETECTED_LANGUAGE,
      SENTIMENT_SCORE::VARCHAR                            AS SENTIMENT_SCORE,
      PROCESSED_AT::VARCHAR                               AS PROCESSED_AT
    FROM PROCESSED.PDF_INTELLIGENCE
);

-----------------------------------------------------------------------
-- 2. TXT SEARCH — over enriched text document content
-----------------------------------------------------------------------
CREATE OR REPLACE CORTEX SEARCH SERVICE PROCESSED.TXT_SEARCH
  ON SEARCH_TEXT
  ATTRIBUTES DOC_CATEGORY, PATIENT_NAME, PROVIDER_NAME, DIAGNOSIS, DETECTED_LANGUAGE, SENTIMENT_SCORE, PROCESSED_AT
  WAREHOUSE = HEALTHCARE_AI_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
  COMMENT = 'Cortex Search over AI-enriched medical text documents'
AS (
    SELECT
      TXT_ID,
      FILE_NAME,
      CONCAT(
        COALESCE(RAW_TEXT, ''), '\n\n',
        'SUMMARY: ', COALESCE(SUMMARY, ''), '\n\n',
        'INSIGHTS: ', COALESCE(KEY_INSIGHTS, ''), '\n\n',
        'DIAGNOSIS: ', COALESCE(EXTRACTED_FIELDS:diagnosis::VARCHAR, '')
      )                                                   AS SEARCH_TEXT,
      DOC_CATEGORY,
      COALESCE(EXTRACTED_FIELDS:patient_name::VARCHAR, 'Unknown')  AS PATIENT_NAME,
      COALESCE(EXTRACTED_FIELDS:provider_name::VARCHAR, 'Unknown') AS PROVIDER_NAME,
      COALESCE(EXTRACTED_FIELDS:diagnosis::VARCHAR, '')   AS DIAGNOSIS,
      DETECTED_LANGUAGE,
      SENTIMENT_SCORE::VARCHAR                            AS SENTIMENT_SCORE,
      PROCESSED_AT::VARCHAR                               AS PROCESSED_AT
    FROM PROCESSED.TXT_INTELLIGENCE
);

-----------------------------------------------------------------------
-- 3. AUDIO SEARCH — over transcribed consultation recordings
-----------------------------------------------------------------------
CREATE OR REPLACE CORTEX SEARCH SERVICE PROCESSED.AUDIO_SEARCH
  ON SEARCH_TEXT
  ATTRIBUTES CALL_CATEGORY, PATIENT_NAME, PROVIDER_NAME, CHIEF_COMPLAINT, DURATION_SECS, SPEAKER_COUNT, DETECTED_LANGUAGE, SENTIMENT_SCORE, PROCESSED_AT
  WAREHOUSE = HEALTHCARE_AI_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
  COMMENT = 'Cortex Search over transcribed patient consultations (WAV/MP3 audio)'
AS (
    SELECT
      AUDIO_ID,
      FILE_NAME,
      CONCAT(
        COALESCE(TRANSCRIPT_TEXT, ''), '\n\n',
        'SUMMARY: ', COALESCE(SUMMARY, ''), '\n\n',
        'CONSULTATION NOTES: ', COALESCE(CONSULTATION_NOTES, ''), '\n\n',
        'CHIEF COMPLAINT: ', COALESCE(EXTRACTED_FIELDS:chief_complaint::VARCHAR, '')
      )                                                   AS SEARCH_TEXT,
      CALL_CATEGORY,
      COALESCE(EXTRACTED_FIELDS:patient_name::VARCHAR, 'Unknown')  AS PATIENT_NAME,
      COALESCE(EXTRACTED_FIELDS:provider_name::VARCHAR, 'Unknown') AS PROVIDER_NAME,
      COALESCE(EXTRACTED_FIELDS:chief_complaint::VARCHAR, '')      AS CHIEF_COMPLAINT,
      AUDIO_DURATION_SECS::VARCHAR                        AS DURATION_SECS,
      SPEAKER_COUNT::VARCHAR                              AS SPEAKER_COUNT,
      DETECTED_LANGUAGE,
      SENTIMENT_SCORE::VARCHAR                            AS SENTIMENT_SCORE,
      PROCESSED_AT::VARCHAR                               AS PROCESSED_AT
    FROM PROCESSED.AUDIO_INTELLIGENCE
);

-----------------------------------------------------------------------
-- 4. VERIFY
-----------------------------------------------------------------------
SHOW CORTEX SEARCH SERVICES IN DATABASE HEALTHCARE_AI_DEMO;

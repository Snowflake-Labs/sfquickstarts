/*=============================================================================
  06 - STORED PROCEDURE: PROCESS TXT FILES
  Healthcare AI Intelligence Pipeline

  Processes unprocessed TXT files from RAW.FILES_LOG using 8 AI functions:
    1. AI_PARSE_DOCUMENT  — read text content from TXT file (LAYOUT mode)
    2. AI_EXTRACT         — pull structured healthcare fields
    3. AI_CLASSIFY        — categorize document type
    4. AI_SENTIMENT       — overall + multi-dimensional sentiment
    5. AI_SUMMARIZE       — concise summary
    6. AI_TRANSLATE       — detect language, translate if non-English
    7. AI_REDACT          — remove PII
    8. AI_COMPLETE        — generate key insights and action items
    9. AI_EMBED           — vector embedding for search

  TXT files are read via AI_PARSE_DOCUMENT (LAYOUT mode).

  Inserts results into PROCESSED.TXT_INTELLIGENCE.

  Depends on: 03 (FILES_LOG), 04 (TXT_INTELLIGENCE table)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA PROCESSED;
USE WAREHOUSE HEALTHCARE_AI_WH;

CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_TXT_FILES()
  RETURNS VARCHAR
  LANGUAGE SQL
  COMMENT = 'Processes unprocessed TXT files through 8 Cortex AI functions into TXT_INTELLIGENCE'
  EXECUTE AS CALLER
AS
$$
BEGIN

  INSERT INTO PROCESSED.TXT_INTELLIGENCE (
      FILE_ID, FILE_NAME, RAW_TEXT,
      EXTRACTED_FIELDS, DOC_CATEGORY, DOC_CATEGORY_CONFIDENCE,
      SENTIMENT_SCORE, SENTIMENT_DIMENSIONS, SUMMARY,
      DETECTED_LANGUAGE, TRANSLATED_TEXT, REDACTED_TEXT,
      KEY_INSIGHTS, EMBEDDING
  )
  WITH txt_content AS (
    SELECT
      f.FILE_ID,
      f.FILE_NAME,
      -- Read TXT file content via AI_PARSE_DOCUMENT (LAYOUT mode)
      AI_PARSE_DOCUMENT(
        TO_FILE('@RAW.S3_MEDICAL_TXT', f.FILE_NAME),
        OBJECT_CONSTRUCT('mode', 'LAYOUT')
      ):content::VARCHAR AS FILE_TEXT
    FROM RAW.FILES_LOG f
    WHERE f.FILE_TYPE = 'TXT'
      AND f.IS_PROCESSED = FALSE
  )
  SELECT
      t.FILE_ID,
      t.FILE_NAME,

      -- Raw text content
      t.FILE_TEXT                                            AS RAW_TEXT,

      -----------------------------------------------------------
      -- 1. AI_EXTRACT — structured healthcare fields
      -----------------------------------------------------------
      AI_EXTRACT(
        t.FILE_TEXT,
        OBJECT_CONSTRUCT(
          'patient_name',       'string: full name of the patient',
          'date_of_birth',      'string: patient date of birth',
          'provider_name',      'string: name of the doctor or provider',
          'facility_name',      'string: hospital or clinic name',
          'document_date',      'string: date of the document',
          'diagnosis',          'string: primary diagnosis or findings',
          'medications',        'array: list of medications mentioned',
          'procedures',         'array: list of procedures or tests',
          'follow_up_actions',  'array: recommended follow-up actions',
          'insurance_id',       'string: insurance or policy number if present',
          'total_amount',       'number: total billed amount if present'
        )
      )                                                     AS EXTRACTED_FIELDS,

      -----------------------------------------------------------
      -- 2. AI_CLASSIFY — categorize document type
      -----------------------------------------------------------
      AI_CLASSIFY(
        t.FILE_TEXT,
        ARRAY_CONSTRUCT(
          'Lab Report', 'Discharge Summary', 'Prescription',
          'Radiology Report', 'Insurance Claim', 'Referral Letter',
          'Clinical Notes', 'Pathology Report',
          'Patient Intake Form', 'Nursing Notes'
        )
      ):labels[0]::VARCHAR                                  AS DOC_CATEGORY,

      NULL::FLOAT                                           AS DOC_CATEGORY_CONFIDENCE,

      -----------------------------------------------------------
      -- 3. AI_SENTIMENT — overall + multi-dimensional
      -----------------------------------------------------------
      SNOWFLAKE.CORTEX.SENTIMENT(t.FILE_TEXT)               AS SENTIMENT_SCORE,

      AI_SENTIMENT(t.FILE_TEXT)                              AS SENTIMENT_DIMENSIONS,

      -----------------------------------------------------------
      -- 4. AI_SUMMARIZE — concise summary
      -----------------------------------------------------------
      SNOWFLAKE.CORTEX.SUMMARIZE(t.FILE_TEXT)               AS SUMMARY,

      -----------------------------------------------------------
      -- 5. AI_TRANSLATE — detect language + translate if needed
      -----------------------------------------------------------
      AI_CLASSIFY(
        t.FILE_TEXT,
        ARRAY_CONSTRUCT('English', 'Spanish', 'French', 'German',
                        'Portuguese', 'Chinese', 'Japanese', 'Korean', 'Arabic')
      ):labels[0]::VARCHAR                                  AS DETECTED_LANGUAGE,

      CASE
        WHEN AI_CLASSIFY(
          t.FILE_TEXT,
          ARRAY_CONSTRUCT('English', 'Spanish', 'French', 'German',
                          'Portuguese', 'Chinese', 'Japanese', 'Korean', 'Arabic')
        ):labels[0]::VARCHAR != 'English'
        THEN AI_TRANSLATE(t.FILE_TEXT, '', 'en')
        ELSE NULL
      END                                                   AS TRANSLATED_TEXT,

      -----------------------------------------------------------
      -- 6. AI_REDACT — remove PII
      -----------------------------------------------------------
      AI_REDACT(t.FILE_TEXT)                                AS REDACTED_TEXT,

      -----------------------------------------------------------
      -- 7. AI_COMPLETE — key insights and action items
      -----------------------------------------------------------
      AI_COMPLETE(
        'claude-3-5-sonnet',
        CONCAT(
          'You are a medical document analyst. Given the following medical document, ',
          'provide: 1) Three key clinical insights, 2) Any urgent action items, ',
          '3) Recommended follow-ups. Be concise. Document: ',
          t.FILE_TEXT
        )
      )                                                     AS KEY_INSIGHTS,

      -----------------------------------------------------------
      -- 8. AI_EMBED — vector embedding for Cortex Search
      -----------------------------------------------------------
      AI_EMBED('snowflake-arctic-embed-m-v1.5', t.FILE_TEXT) AS EMBEDDING

  FROM txt_content t;

  -- Mark TXT files as processed
  UPDATE RAW.FILES_LOG
  SET IS_PROCESSED = TRUE,
      PROCESSED_AT = CURRENT_TIMESTAMP()
  WHERE FILE_TYPE = 'TXT'
    AND IS_PROCESSED = FALSE;

  RETURN 'TXT processing complete: ' || CURRENT_TIMESTAMP()::VARCHAR;

END;
$$

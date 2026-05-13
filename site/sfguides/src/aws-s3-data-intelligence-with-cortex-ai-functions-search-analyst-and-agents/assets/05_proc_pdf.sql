/*=============================================================================
  05 - STORED PROCEDURE: PROCESS PDF FILES
  Healthcare AI Intelligence Pipeline

  Processes unprocessed PDF files from RAW.FILES_LOG using 9 AI functions:
    1. AI_PARSE_DOCUMENT (OCR mode)  — extract raw text from PDF
    2. AI_PARSE_DOCUMENT (LAYOUT)    — structured layout extraction
    3. AI_EXTRACT                    — pull structured healthcare fields
    4. AI_CLASSIFY                   — categorize document type
    5. AI_SENTIMENT                  — overall + multi-dimensional sentiment
    6. AI_SUMMARIZE                  — concise summary
    7. AI_TRANSLATE                  — detect language, translate if non-English
    8. AI_REDACT                     — remove PII
    9. AI_COMPLETE                   — generate key insights and action items
   10. AI_EMBED                      — vector embedding for search

  Inserts results into PROCESSED.PDF_INTELLIGENCE.

  Depends on: 03 (FILES_LOG), 04 (PDF_INTELLIGENCE table)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA PROCESSED;
USE WAREHOUSE HEALTHCARE_AI_WH;

CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_PDF_FILES()
  RETURNS VARCHAR
  LANGUAGE SQL
  COMMENT = 'Processes unprocessed PDF files through 9 Cortex AI functions into PDF_INTELLIGENCE'
  EXECUTE AS CALLER
AS
BEGIN

  INSERT INTO PROCESSED.PDF_INTELLIGENCE (
      FILE_ID, FILE_NAME, PARSED_TEXT, PARSED_LAYOUT,
      EXTRACTED_FIELDS, DOC_CATEGORY, DOC_CATEGORY_CONFIDENCE,
      SENTIMENT_SCORE, SENTIMENT_DIMENSIONS, SUMMARY,
      DETECTED_LANGUAGE, TRANSLATED_TEXT, REDACTED_TEXT,
      KEY_INSIGHTS, EMBEDDING
  )
  SELECT
      f.FILE_ID,
      f.FILE_NAME,

      -----------------------------------------------------------
      -- 1. AI_PARSE_DOCUMENT (OCR) — raw text from PDF
      -----------------------------------------------------------
      AI_PARSE_DOCUMENT(
        TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME),
        OBJECT_CONSTRUCT('mode', 'OCR')
      ):content::VARCHAR                                    AS PARSED_TEXT,

      -----------------------------------------------------------
      -- 2. AI_PARSE_DOCUMENT (LAYOUT) — structured output
      -----------------------------------------------------------
      AI_PARSE_DOCUMENT(
        TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME),
        OBJECT_CONSTRUCT('mode', 'LAYOUT')
      )                                                     AS PARSED_LAYOUT,

      -----------------------------------------------------------
      -- 3. AI_EXTRACT — structured healthcare fields
      -----------------------------------------------------------
      AI_EXTRACT(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR,
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
      -- 4. AI_CLASSIFY — categorize document type
      -----------------------------------------------------------
      AI_CLASSIFY(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR,
        ARRAY_CONSTRUCT(
          'Lab Report', 'Discharge Summary', 'Prescription',
          'Radiology Report', 'Insurance Claim', 'Referral Letter',
          'Clinical Notes', 'Pathology Report'
        )
      ):labels[0]::VARCHAR                                  AS DOC_CATEGORY,

      NULL::FLOAT                                           AS DOC_CATEGORY_CONFIDENCE,

      -----------------------------------------------------------
      -- 5. AI_SENTIMENT — overall + multi-dimensional
      -----------------------------------------------------------
      SNOWFLAKE.CORTEX.SENTIMENT(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR
      )                                                     AS SENTIMENT_SCORE,

      AI_SENTIMENT(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR
      )                                                     AS SENTIMENT_DIMENSIONS,

      -----------------------------------------------------------
      -- 6. AI_SUMMARIZE — concise summary
      -----------------------------------------------------------
      SNOWFLAKE.CORTEX.SUMMARIZE(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR
      )                                                     AS SUMMARY,

      -----------------------------------------------------------
      -- 7. AI_TRANSLATE — detect language + translate if needed
      -----------------------------------------------------------
      AI_CLASSIFY(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR,
        ARRAY_CONSTRUCT('English', 'Spanish', 'French', 'German',
                        'Portuguese', 'Chinese', 'Japanese', 'Korean', 'Arabic')
      ):labels[0]::VARCHAR                                  AS DETECTED_LANGUAGE,

      CASE
        WHEN AI_CLASSIFY(
          AI_PARSE_DOCUMENT(
            TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
          ):content::VARCHAR,
          ARRAY_CONSTRUCT('English', 'Spanish', 'French', 'German',
                          'Portuguese', 'Chinese', 'Japanese', 'Korean', 'Arabic')
        ):labels[0]::VARCHAR != 'English'
        THEN AI_TRANSLATE(
          AI_PARSE_DOCUMENT(
            TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
          ):content::VARCHAR,
          '',
          'en'
        )
        ELSE NULL
      END                                                   AS TRANSLATED_TEXT,

      -----------------------------------------------------------
      -- 8. AI_REDACT — remove PII
      -----------------------------------------------------------
      AI_REDACT(
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR
      )                                                     AS REDACTED_TEXT,

      -----------------------------------------------------------
      -- 9. AI_COMPLETE — key insights and action items
      -----------------------------------------------------------
      AI_COMPLETE(
        'claude-3-5-sonnet',
        CONCAT(
          'You are a medical document analyst. Given the following medical document, ',
          'provide: 1) Three key clinical insights, 2) Any urgent action items, ',
          '3) Recommended follow-ups. Be concise.\n\nDocument:\n',
          AI_PARSE_DOCUMENT(
            TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
          ):content::VARCHAR
        )
      )                                                     AS KEY_INSIGHTS,

      -----------------------------------------------------------
      -- 10. AI_EMBED — vector embedding for Cortex Search
      -----------------------------------------------------------
      AI_EMBED(
        'snowflake-arctic-embed-m-v1.5',
        AI_PARSE_DOCUMENT(
          TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
        ):content::VARCHAR
      )                                                     AS EMBEDDING

  FROM RAW.FILES_LOG f
  WHERE f.FILE_TYPE = 'PDF'
    AND f.IS_PROCESSED = FALSE;

  -- Mark PDF files as processed
  UPDATE RAW.FILES_LOG
  SET IS_PROCESSED = TRUE,
      PROCESSED_AT = CURRENT_TIMESTAMP()
  WHERE FILE_TYPE = 'PDF'
    AND IS_PROCESSED = FALSE;

  RETURN 'PDF processing complete: ' || CURRENT_TIMESTAMP()::VARCHAR;

END;

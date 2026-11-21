/*=============================================================================
  07 - STORED PROCEDURE: PROCESS AUDIO FILES (WAV & MP3)
  Healthcare AI Intelligence Pipeline

  Processes unprocessed WAV/MP3 files from RAW.FILES_LOG using 8 AI functions:
    1. AI_TRANSCRIBE    — speech-to-text transcription
    2. AI_EXTRACT       — pull structured fields from transcript
    3. AI_CLASSIFY      — categorize consultation type
    4. AI_SENTIMENT     — overall + multi-dimensional sentiment
    5. AI_SUMMARIZE     — executive summary
    6. AI_TRANSLATE     — detect language, translate if non-English
    7. AI_COMPLETE      — generate structured SOAP consultation notes
    8. AI_EMBED         — vector embedding for search

  Inserts results into PROCESSED.AUDIO_INTELLIGENCE.

  Depends on: 03 (FILES_LOG), 04 (AUDIO_INTELLIGENCE table)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA PROCESSED;
USE WAREHOUSE HEALTHCARE_AI_WH;

CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_AUDIO_FILES()
  RETURNS VARCHAR
  LANGUAGE SQL
  COMMENT = 'Processes unprocessed WAV/MP3 files through 8 Cortex AI functions into AUDIO_INTELLIGENCE'
  EXECUTE AS CALLER
AS
$$
BEGIN

  INSERT INTO PROCESSED.AUDIO_INTELLIGENCE (
      FILE_ID, FILE_NAME, TRANSCRIPT_TEXT, TRANSCRIPT_SEGMENTS,
      AUDIO_DURATION_SECS, SPEAKER_COUNT,
      EXTRACTED_FIELDS, CALL_CATEGORY, CALL_CATEGORY_CONFIDENCE,
      SENTIMENT_SCORE, SENTIMENT_DIMENSIONS, SUMMARY,
      DETECTED_LANGUAGE, TRANSLATED_TRANSCRIPT,
      CONSULTATION_NOTES, EMBEDDING
  )
  WITH transcribed AS (
    SELECT
      f.FILE_ID,
      f.FILE_NAME,
      AI_TRANSCRIBE(
        TO_FILE('@RAW.S3_MEDICAL_AUDIO', f.FILE_NAME)
      ) AS RAW_TRANSCRIPT
    FROM RAW.FILES_LOG f
    WHERE f.FILE_TYPE IN ('WAV', 'MP3')
      AND f.IS_PROCESSED = FALSE
  )
  SELECT
      t.FILE_ID,
      t.FILE_NAME,

      -----------------------------------------------------------
      -- 1. AI_TRANSCRIBE — full text
      -----------------------------------------------------------
      t.RAW_TRANSCRIPT:text::VARCHAR                        AS TRANSCRIPT_TEXT,

      -----------------------------------------------------------
      -- 2. AI_TRANSCRIBE — segments with timestamps
      -----------------------------------------------------------
      t.RAW_TRANSCRIPT:segments                             AS TRANSCRIPT_SEGMENTS,

      t.RAW_TRANSCRIPT:audio_duration::FLOAT                AS AUDIO_DURATION_SECS,

      NULL::INT                                             AS SPEAKER_COUNT,

      -----------------------------------------------------------
      -- 3. AI_EXTRACT — structured fields from transcript
      -----------------------------------------------------------
      AI_EXTRACT(
        t.RAW_TRANSCRIPT:text::VARCHAR,
        OBJECT_CONSTRUCT(
          'patient_name',        'string: full name of the patient',
          'provider_name',       'string: name of the doctor or provider',
          'chief_complaint',     'string: main reason for the consultation',
          'diagnosis_discussed', 'string: any diagnosis or condition discussed',
          'medications_discussed', 'array: medications mentioned',
          'follow_up_actions',   'array: action items or follow-ups agreed upon',
          'next_appointment',    'string: date or timeframe of next visit if mentioned'
        )
      )                                                     AS EXTRACTED_FIELDS,

      -----------------------------------------------------------
      -- 4. AI_CLASSIFY — categorize consultation type
      -----------------------------------------------------------
      AI_CLASSIFY(
        t.RAW_TRANSCRIPT:text::VARCHAR,
        ARRAY_CONSTRUCT(
          'Initial Consultation', 'Follow-Up Visit',
          'Specialist Referral', 'Prescription Review',
          'Lab Results Discussion', 'Mental Health Session',
          'Insurance Discussion', 'Emergency Consultation'
        )
      ):labels[0]::VARCHAR                                  AS CALL_CATEGORY,

      NULL::FLOAT                                           AS CALL_CATEGORY_CONFIDENCE,

      -----------------------------------------------------------
      -- 5. AI_SENTIMENT — overall + multi-dimensional
      -----------------------------------------------------------
      SNOWFLAKE.CORTEX.SENTIMENT(t.RAW_TRANSCRIPT:text::VARCHAR) AS SENTIMENT_SCORE,

      AI_SENTIMENT(t.RAW_TRANSCRIPT:text::VARCHAR)          AS SENTIMENT_DIMENSIONS,

      -----------------------------------------------------------
      -- 6. AI_SUMMARIZE — executive summary
      -----------------------------------------------------------
      SNOWFLAKE.CORTEX.SUMMARIZE(t.RAW_TRANSCRIPT:text::VARCHAR) AS SUMMARY,

      -----------------------------------------------------------
      -- 7. AI_TRANSLATE — detect language + translate if needed
      -----------------------------------------------------------
      AI_CLASSIFY(
        t.RAW_TRANSCRIPT:text::VARCHAR,
        ARRAY_CONSTRUCT('English', 'Spanish', 'French', 'German',
                        'Portuguese', 'Chinese', 'Japanese', 'Korean', 'Arabic')
      ):labels[0]::VARCHAR                                  AS DETECTED_LANGUAGE,

      CASE
        WHEN AI_CLASSIFY(
          t.RAW_TRANSCRIPT:text::VARCHAR,
          ARRAY_CONSTRUCT('English', 'Spanish', 'French', 'German',
                          'Portuguese', 'Chinese', 'Japanese', 'Korean', 'Arabic')
        ):labels[0]::VARCHAR != 'English'
        THEN AI_TRANSLATE(t.RAW_TRANSCRIPT:text::VARCHAR, '', 'en')
        ELSE NULL
      END                                                   AS TRANSLATED_TRANSCRIPT,

      -----------------------------------------------------------
      -- 8. AI_COMPLETE — structured SOAP consultation notes
      -----------------------------------------------------------
      AI_COMPLETE(
        'claude-3-5-sonnet',
        CONCAT(
          'You are a medical scribe. Given the following patient consultation transcript, ',
          'generate structured SOAP notes (Subjective, Objective, Assessment, Plan). ',
          'Be concise and clinically accurate. Transcript: ',
          t.RAW_TRANSCRIPT:text::VARCHAR
        )
      )                                                     AS CONSULTATION_NOTES,

      -----------------------------------------------------------
      -- 9. AI_EMBED — vector embedding for Cortex Search
      -----------------------------------------------------------
      AI_EMBED(
        'snowflake-arctic-embed-m-v1.5',
        t.RAW_TRANSCRIPT:text::VARCHAR
      )                                                     AS EMBEDDING

  FROM transcribed t;

  -- Mark audio files as processed
  UPDATE RAW.FILES_LOG
  SET IS_PROCESSED = TRUE,
      PROCESSED_AT = CURRENT_TIMESTAMP()
  WHERE FILE_TYPE IN ('WAV', 'MP3')
    AND IS_PROCESSED = FALSE;

  RETURN 'Audio processing complete: ' || CURRENT_TIMESTAMP()::VARCHAR;

END;
$$

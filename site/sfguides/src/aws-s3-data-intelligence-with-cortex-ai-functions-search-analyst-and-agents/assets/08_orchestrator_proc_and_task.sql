/*=============================================================================
  08 - ORCHESTRATOR STORED PROCEDURE & TASK
  Healthcare AI Intelligence Pipeline

  The orchestrator proc calls the 3 file-type-specific procs in sequence:
    1. PROCESS_PDF_FILES()   — 9 AI functions -> PDF_INTELLIGENCE
    2. PROCESS_TXT_FILES()   — 8 AI functions -> TXT_INTELLIGENCE
    3. PROCESS_AUDIO_FILES() — 8 AI functions -> AUDIO_INTELLIGENCE

  The TASK polls the FILES_LOG_STREAM and fires the orchestrator when
  new unprocessed files are detected.

  Depends on: 03 (stream), 05 (PDF proc), 06 (TXT proc), 07 (Audio proc)
  Must run AFTER all 3 procs are created.
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA PROCESSED;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 1. ORCHESTRATOR STORED PROCEDURE
-----------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_NEW_FILES()
  RETURNS VARCHAR
  LANGUAGE SQL
  COMMENT = 'Orchestrator: calls PDF, TXT, and Audio processing procs in sequence'
  EXECUTE AS CALLER
AS
BEGIN

  LET pdf_result  VARCHAR;
  LET txt_result  VARCHAR;
  LET audio_result VARCHAR;

  -- Process PDFs
  CALL PROCESSED.PROCESS_PDF_FILES();
  pdf_result := SQLROWCOUNT || ' PDF rows';

  -- Process TXT files
  CALL PROCESSED.PROCESS_TXT_FILES();
  txt_result := SQLROWCOUNT || ' TXT rows';

  -- Process Audio files (WAV + MP3)
  CALL PROCESSED.PROCESS_AUDIO_FILES();
  audio_result := SQLROWCOUNT || ' Audio rows';

  RETURN 'Processing complete: ' || :pdf_result || ', ' || :txt_result || ', ' || :audio_result
         || ' at ' || CURRENT_TIMESTAMP()::VARCHAR;

END;

-----------------------------------------------------------------------
-- 2. TASK — triggered by stream, calls orchestrator proc
-----------------------------------------------------------------------
CREATE OR REPLACE TASK RAW.PROCESS_NEW_FILES_TASK
  WAREHOUSE = HEALTHCARE_AI_WH
  SCHEDULE  = '1 MINUTE'
  COMMENT   = 'Polls stream for new files and triggers AI processing via orchestrator'
  WHEN SYSTEM$STREAM_HAS_DATA('RAW.FILES_LOG_STREAM')
AS
  CALL PROCESSED.PROCESS_NEW_FILES();

-- Task is created in suspended state. Resume once the full pipeline is verified:
-- ALTER TASK RAW.PROCESS_NEW_FILES_TASK RESUME;

-----------------------------------------------------------------------
-- 3. VERIFY
-----------------------------------------------------------------------
SHOW PROCEDURES IN SCHEMA PROCESSED;
SHOW TASKS IN SCHEMA RAW;

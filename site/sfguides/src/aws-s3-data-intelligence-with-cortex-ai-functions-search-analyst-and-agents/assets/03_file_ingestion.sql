/*=============================================================================
  03 - FILE INGESTION: FILES_LOG, File Format, Snowpipes (SQS) & Stream
  Healthcare AI Intelligence Pipeline

  Flow:
    S3 file upload -> S3 Event Notification -> SQS (Snowflake-managed)
    -> Snowpipe (AUTO_INGEST) -> RAW.FILES_LOG -> Stream
    -> Task (in 08) -> orchestrator proc -> individual file-type procs

  Snowpipe AUTO_INGEST on AWS uses SQS. When you create a pipe with
  AUTO_INGEST = TRUE, Snowflake provisions an SQS queue. You configure
  S3 event notifications to send to that queue.

  After creating pipes, run SHOW PIPES to get the notification_channel
  (SQS queue ARN) and configure S3 event notifications (see 14_aws_setup_guide.sql).

  Depends on: 01 (database/schemas), 02 (stages)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA RAW;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 1. FILES_LOG TABLE -- every file that lands in S3 gets a row here
-----------------------------------------------------------------------
CREATE OR REPLACE TABLE RAW.FILES_LOG (
    FILE_ID         NUMBER AUTOINCREMENT PRIMARY KEY,
    FILE_NAME       VARCHAR        NOT NULL,
    FILE_PATH       VARCHAR        NOT NULL,
    FILE_TYPE       VARCHAR(10)    NOT NULL COMMENT 'PDF, TXT, WAV, or MP3',
    S3_EVENT_TIME   TIMESTAMP_NTZ,
    LANDED_AT       TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
    IS_PROCESSED    BOOLEAN        DEFAULT FALSE,
    PROCESSED_AT    TIMESTAMP_NTZ
);

-----------------------------------------------------------------------
-- 2. FILE FORMAT
--    We only need METADATA$ columns (file name, scan time), not file
--    content. CSV with no delimiters avoids parse errors on binary
--    (PDF, WAV, MP3) and plain text files.
-----------------------------------------------------------------------
CREATE OR REPLACE FILE FORMAT RAW.METADATA_ONLY_FORMAT
  TYPE             = 'CSV'
  RECORD_DELIMITER = NONE
  FIELD_DELIMITER  = NONE
  COMMENT = 'Format for metadata-only ingestion -- skips file content parsing';

-----------------------------------------------------------------------
-- 3. SNOWPIPE FOR PDFs
-----------------------------------------------------------------------
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_DOCS
  AUTO_INGEST = TRUE
  COMMENT = 'Auto-ingest pipe for PDF medical documents from S3 via SQS'
AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT
      METADATA$FILENAME            AS FILE_NAME,
      METADATA$FILENAME            AS FILE_PATH,
      'PDF'                        AS FILE_TYPE,
      METADATA$START_SCAN_TIME     AS S3_EVENT_TIME
    FROM @RAW.S3_MEDICAL_DOCS
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-----------------------------------------------------------------------
-- 4. SNOWPIPE FOR TXT
-----------------------------------------------------------------------
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_TXT
  AUTO_INGEST = TRUE
  COMMENT = 'Auto-ingest pipe for TXT medical documents from S3 via SQS'
AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT
      METADATA$FILENAME            AS FILE_NAME,
      METADATA$FILENAME            AS FILE_PATH,
      'TXT'                        AS FILE_TYPE,
      METADATA$START_SCAN_TIME     AS S3_EVENT_TIME
    FROM @RAW.S3_MEDICAL_TXT
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-----------------------------------------------------------------------
-- 5. SNOWPIPE FOR AUDIO (WAV and MP3)
-----------------------------------------------------------------------
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_AUDIO
  AUTO_INGEST = TRUE
  COMMENT = 'Auto-ingest pipe for WAV/MP3 audio consultations from S3 via SQS'
AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT
      METADATA$FILENAME            AS FILE_NAME,
      METADATA$FILENAME            AS FILE_PATH,
      CASE
        WHEN METADATA$FILENAME ILIKE '%.mp3' THEN 'MP3'
        ELSE 'WAV'
      END                          AS FILE_TYPE,
      METADATA$START_SCAN_TIME     AS S3_EVENT_TIME
    FROM @RAW.S3_MEDICAL_AUDIO
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-----------------------------------------------------------------------
-- 6. GET SQS QUEUE ARNs
--    The notification_channel column contains the Snowflake-managed
--    SQS queue ARN. All pipes share the same ARN per account.
--    Copy this ARN for S3 event notification setup.
-----------------------------------------------------------------------
SHOW PIPES IN SCHEMA RAW;

-- Per-pipe details:
DESC PIPE RAW.PIPE_MEDICAL_DOCS;
DESC PIPE RAW.PIPE_MEDICAL_TXT;
DESC PIPE RAW.PIPE_MEDICAL_AUDIO;

-----------------------------------------------------------------------
-- 7. STREAM on FILES_LOG -- captures new inserts for processing
-----------------------------------------------------------------------
CREATE OR REPLACE STREAM RAW.FILES_LOG_STREAM
  ON TABLE RAW.FILES_LOG
  APPEND_ONLY = TRUE
  COMMENT = 'Captures new file arrivals for AI processing';

-----------------------------------------------------------------------
-- 8. VERIFY
-----------------------------------------------------------------------
SHOW PIPES IN SCHEMA RAW;
SHOW STREAMS IN SCHEMA RAW;

SELECT SYSTEM$PIPE_STATUS('RAW.PIPE_MEDICAL_DOCS')  AS DOCS_PIPE_STATUS;
SELECT SYSTEM$PIPE_STATUS('RAW.PIPE_MEDICAL_TXT')   AS TXT_PIPE_STATUS;
SELECT SYSTEM$PIPE_STATUS('RAW.PIPE_MEDICAL_AUDIO') AS AUDIO_PIPE_STATUS;

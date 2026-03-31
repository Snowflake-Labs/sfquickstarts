author: Bharath Suresh
id: aws-s3-data-intelligence-with-cortex-ai-functions-search-analyst-and-agents
language: en
summary: Integrate S3 files (PDF, TXT, Audio) into Snowflake via Snowpipe auto-ingest, extract structured intelligence using 11 Cortex AI functions, and build a conversational interface with Cortex Search, Cortex Analyst, Cortex Agent, and Snowflake Intelligence.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/curious-bigcat/healthcare-ai-intelligence-pipeline


# AWS S3 Data Intelligence with Cortex AI Functions and Cortex Agents
<!-- -------------------------->
## Overview
Duration: 5

This guide walks through a complete pattern for turning unstructured files sitting in Amazon S3 into queryable intelligence inside Snowflake. You will auto-ingest files via Snowpipe, run them through Cortex AI functions to extract text, entities, sentiment, summaries, and embeddings, then expose everything through Cortex Search (semantic retrieval), Cortex Analyst (natural-language-to-SQL), and a Cortex Agent that combines both --- all accessible through Snowflake Intelligence as a chat UI.
Healthcare documents are used as the example dataset, but the patterns apply to any domain: legal contracts, financial reports, support tickets, call center recordings, or any mix of PDFs, text files, and audio.

### What You'll Learn

- **S3 → Snowflake auto-ingest**: Configuring S3 Event Notifications → SQS → Snowpipe to automatically capture file metadata as files land in S3
- **Cortex AI function pipeline**: Applying 11 AI functions (parse, transcribe, extract, classify, sentiment, summarize, translate, redact, complete, embed, similarity) to files on external stages
- **Cortex Search**: Building semantic search services over AI-enriched unstructured content
- **Cortex Analyst**: Creating a Semantic View that powers natural-language-to-SQL queries over structured data
- **Cortex Agent**: Assembling an agent with multiple tool types (Analyst + Search) for unified question answering
- **Snowflake Intelligence**: Exposing the agent as a chat UI for end users

### What You'll Build

```
S3 Bucket (pdfs/, txt/, audio/)
        |
  S3 Event Notification → SQS (Snowflake-managed)
        |
  Snowpipe (x3) → FILES_LOG → Stream → Task
        |
  Stored Procedures (one per file type)
  applying 9/8/8 Cortex AI functions
        |
  Intelligence Tables (PDF, TXT, Audio)
        |
  ┌─────────────────────────────────────┐
  │  Cortex Search (3 services)         │
  │  Cortex Analyst (Semantic View)     │
  │  Cortex Agent (4 tools)             │
  │  Snowflake Intelligence (chat UI)   │
  └─────────────────────────────────────┘
```

### Prerequisites

- Snowflake account with ACCOUNTADMIN role and Cortex AI functions enabled
- AWS account with Amazon S3 access
- Python 3.10+ (for sample file generation only)

<!-- ------------------------ -->
## S3 Integration and Snowpipe Auto-Ingest
Duration: 15

This section covers the core pattern: getting files from S3 into Snowflake automatically using Snowpipe with SQS auto-ingest.

### How It Works

When you create a Snowpipe with `AUTO_INGEST = TRUE` on AWS, Snowflake provisions a managed SQS queue. You configure S3 to send `ObjectCreated` event notifications to that queue. When a file lands in S3, the event triggers Snowpipe, which runs a `COPY INTO` statement to load file metadata into a landing table.

> aside positive
>
> We only ingest **file metadata** (name, path, type, timestamp) --- not file content. The actual files stay in S3 and are read directly by AI functions via `TO_FILE()` on external stages. This avoids parsing issues with binary files (PDF, WAV, MP3).

### Step 1: Create Database and Schemas

Run `01_database_and_schemas.sql`:

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE DATABASE HEALTHCARE_AI_DEMO;

-- Three schemas for separation of concerns
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.RAW;        -- File metadata landing zone
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.PROCESSED;  -- AI-enriched output tables
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.ANALYTICS;  -- Structured data, views, agent

CREATE OR REPLACE WAREHOUSE HEALTHCARE_AI_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
```

### Step 2: Create Storage Integration and External Stages

Run `02_s3_integration_and_stages.sql`:

> aside negative
>
> Replace `<YOUR_S3_BUCKET_NAME>` and `<YOUR_AWS_IAM_ROLE_ARN>` with your actual values. The IAM role is created in the AWS setup steps below.

```sql
-- Trust relationship between Snowflake and your AWS account
CREATE OR REPLACE STORAGE INTEGRATION HEALTHCARE_S3_INTEGRATION
  TYPE                      = EXTERNAL_STAGE
  STORAGE_PROVIDER          = 'S3'
  ENABLED                   = TRUE
  STORAGE_AWS_ROLE_ARN      = '<YOUR_AWS_IAM_ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<YOUR_S3_BUCKET_NAME>/healthcare/');

-- One external stage per file type prefix
CREATE OR REPLACE STAGE RAW.S3_MEDICAL_DOCS
  URL = 's3://<YOUR_S3_BUCKET_NAME>/healthcare/pdfs/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = TRUE);

CREATE OR REPLACE STAGE RAW.S3_MEDICAL_TXT
  URL = 's3://<YOUR_S3_BUCKET_NAME>/healthcare/txt/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = TRUE);

CREATE OR REPLACE STAGE RAW.S3_MEDICAL_AUDIO
  URL = 's3://<YOUR_S3_BUCKET_NAME>/healthcare/audio/'
  STORAGE_INTEGRATION = HEALTHCARE_S3_INTEGRATION
  DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = TRUE);

-- Retrieve Snowflake's IAM user ARN and external ID (needed for AWS trust policy)
DESCRIBE INTEGRATION HEALTHCARE_S3_INTEGRATION;
```

### Step 3: Create Snowpipes with Metadata-Only Ingestion

Run `03_file_ingestion.sql`. The key pattern here is using a CSV file format with no delimiters to skip content parsing entirely --- we only capture `METADATA$` pseudocolumns:

```sql
-- Landing table for file metadata
CREATE OR REPLACE TABLE RAW.FILES_LOG (
    FILE_ID       NUMBER AUTOINCREMENT PRIMARY KEY,
    FILE_NAME     VARCHAR NOT NULL,
    FILE_PATH     VARCHAR NOT NULL,
    FILE_TYPE     VARCHAR(10) NOT NULL,   -- PDF, TXT, WAV, MP3
    S3_EVENT_TIME TIMESTAMP_NTZ,
    LANDED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    IS_PROCESSED  BOOLEAN DEFAULT FALSE,
    PROCESSED_AT  TIMESTAMP_NTZ
);

-- Metadata-only format: skips content parsing for binary files
CREATE OR REPLACE FILE FORMAT RAW.METADATA_ONLY_FORMAT
  TYPE = 'CSV' RECORD_DELIMITER = NONE FIELD_DELIMITER = NONE;

-- Snowpipe for PDFs (AUTO_INGEST provisions a Snowflake-managed SQS queue)
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_DOCS AUTO_INGEST = TRUE AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT METADATA$FILENAME, METADATA$FILENAME, 'PDF', METADATA$START_SCAN_TIME
    FROM @RAW.S3_MEDICAL_DOCS
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-- Snowpipe for TXT
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_TXT AUTO_INGEST = TRUE AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT METADATA$FILENAME, METADATA$FILENAME, 'TXT', METADATA$START_SCAN_TIME
    FROM @RAW.S3_MEDICAL_TXT
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-- Snowpipe for Audio (WAV + MP3, distinguished by extension)
CREATE OR REPLACE PIPE RAW.PIPE_MEDICAL_AUDIO AUTO_INGEST = TRUE AS
  COPY INTO RAW.FILES_LOG (FILE_NAME, FILE_PATH, FILE_TYPE, S3_EVENT_TIME)
  FROM (
    SELECT METADATA$FILENAME, METADATA$FILENAME,
      CASE WHEN METADATA$FILENAME ILIKE '%.mp3' THEN 'MP3' ELSE 'WAV' END,
      METADATA$START_SCAN_TIME
    FROM @RAW.S3_MEDICAL_AUDIO
  )
  FILE_FORMAT = (FORMAT_NAME = 'RAW.METADATA_ONLY_FORMAT');

-- Get the SQS queue ARN (needed for S3 event notification config)
SHOW PIPES IN SCHEMA RAW;
-- The notification_channel column contains the Snowflake-managed SQS ARN

-- Append-only stream to detect new file arrivals
CREATE OR REPLACE STREAM RAW.FILES_LOG_STREAM
  ON TABLE RAW.FILES_LOG APPEND_ONLY = TRUE;
```

### Step 4: Configure AWS

Full details are in `14_aws_setup_guide.sql`. The key steps:

1. **Create S3 bucket** with prefixes `healthcare/pdfs/`, `healthcare/txt/`, `healthcare/audio/`
2. **Create IAM policy** granting `s3:GetObject`, `s3:GetObjectVersion`, `s3:ListBucket`, `s3:GetBucketLocation` on your bucket
3. **Create IAM role** with a trust policy using the `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID` from `DESCRIBE INTEGRATION`
4. **Configure S3 event notifications** pointing `s3:ObjectCreated:*` events (filtered by prefix) to the SQS queue ARN from `SHOW PIPES`

```bash
# Example: upload sample files to trigger the pipeline
aws s3 cp sample_files/pdfs/  s3://YOUR-BUCKET/healthcare/pdfs/  --recursive
aws s3 cp sample_files/txt/   s3://YOUR-BUCKET/healthcare/txt/   --recursive
aws s3 cp sample_files/audio/ s3://YOUR-BUCKET/healthcare/audio/ --recursive
```

5. **Resume pipes** in Snowflake:

```sql
ALTER PIPE RAW.PIPE_MEDICAL_DOCS  SET PIPE_EXECUTION_PAUSED = FALSE;
ALTER PIPE RAW.PIPE_MEDICAL_TXT   SET PIPE_EXECUTION_PAUSED = FALSE;
ALTER PIPE RAW.PIPE_MEDICAL_AUDIO SET PIPE_EXECUTION_PAUSED = FALSE;

-- Verify files landed (wait 1-2 minutes after upload)
SELECT FILE_TYPE, COUNT(*) AS FILES FROM RAW.FILES_LOG GROUP BY FILE_TYPE;
```

> aside negative
>
> If FILES_LOG is empty after 2 minutes: (1) verify S3 event notifications point to the correct SQS ARN, (2) check IAM trust policy has the correct Snowflake user ARN and external ID, (3) try `ALTER PIPE RAW.PIPE_MEDICAL_DOCS REFRESH;` for manual refresh.

<!-- ------------------------ -->
## Extracting Intelligence with Cortex AI Functions
Duration: 10

This is the core of the pipeline: reading files directly from S3 stages using `TO_FILE()` and applying Cortex AI functions to extract structured intelligence. Each file type gets its own stored procedure with a tailored AI function chain.

### The 11 Cortex AI Functions

| Function | What It Does | Input | Output |
|---|---|---|---|
| `AI_PARSE_DOCUMENT` | Extracts text from PDFs and documents | FILE + `OBJECT_CONSTRUCT('mode','OCR'/'LAYOUT')` | VARIANT with `:content` |
| `AI_TRANSCRIBE` | Converts audio to text | FILE (single argument) | VARIANT with `:text`, `:segments` |
| `AI_EXTRACT` | Pulls structured fields from text | text + OBJECT schema | VARIANT with named fields |
| `AI_CLASSIFY` | Categorizes text into labels | text + ARRAY of labels | VARIANT with `:labels[0]` |
| `SNOWFLAKE.CORTEX.SENTIMENT` | Returns sentiment as a float | text | FLOAT (-1 to 1) |
| `AI_SENTIMENT` | Returns multi-dimensional sentiment | text | VARIANT with categories |
| `SNOWFLAKE.CORTEX.SUMMARIZE` | Generates a concise summary | text | VARCHAR |
| `AI_TRANSLATE` | Translates text to a target language | text, source_lang, target_lang | VARCHAR |
| `AI_REDACT` | Removes PII from text | text | VARCHAR |
| `AI_COMPLETE` | LLM generation (insights, notes) | model_name, prompt | VARCHAR |
| `AI_EMBED` | Creates vector embeddings | model_name, text | VECTOR(FLOAT, 768) |

> aside positive
>
> **Key syntax details discovered during implementation:**
> - `AI_PARSE_DOCUMENT` requires `OBJECT_CONSTRUCT('mode', 'OCR')` as the second argument --- a plain string like `'OCR'` causes an "Invalid argument types" error
> - `AI_TRANSCRIBE` accepts only a single FILE argument --- passing an options object returns "invalid options object"
> - `AI_SUMMARIZE` may not exist in all accounts --- use `SNOWFLAKE.CORTEX.SUMMARIZE` instead
> - `AI_SENTIMENT` returns an OBJECT (not a float) --- use `SNOWFLAKE.CORTEX.SENTIMENT` for a float score
> - `AI_CLASSIFY` returns `{labels: ["Label"]}` --- access via `:labels[0]::VARCHAR`
> - Model names use hyphens: `claude-3-5-sonnet` (not dots)

### Output Tables

Run `04_processing_tables.sql` to create one intelligence table per file type:

| Table | Key Columns | AI Functions Applied |
|---|---|---|
| `PROCESSED.PDF_INTELLIGENCE` | PARSED_TEXT, PARSED_LAYOUT, EXTRACTED_FIELDS, DOC_CATEGORY, SENTIMENT_SCORE, SUMMARY, REDACTED_TEXT, KEY_INSIGHTS, EMBEDDING | 9 (parse, extract, classify, sentiment, summarize, translate, redact, complete, embed) |
| `PROCESSED.TXT_INTELLIGENCE` | RAW_TEXT, EXTRACTED_FIELDS, DOC_CATEGORY, SENTIMENT_SCORE, SUMMARY, REDACTED_TEXT, KEY_INSIGHTS, EMBEDDING | 8 (parse-layout, extract, classify, sentiment, summarize, translate, redact, complete, embed) |
| `PROCESSED.AUDIO_INTELLIGENCE` | TRANSCRIPT_TEXT, TRANSCRIPT_SEGMENTS, EXTRACTED_FIELDS, CALL_CATEGORY, SENTIMENT_SCORE, SUMMARY, CONSULTATION_NOTES, EMBEDDING | 8 (transcribe, extract, classify, sentiment, summarize, translate, complete, embed) |

### Stored Procedure Pattern

Each proc follows the same pattern: **SELECT with AI functions FROM FILES_LOG WHERE not yet processed, INSERT INTO intelligence table, UPDATE FILES_LOG to mark as processed.** Run `05_proc_pdf.sql`, `06_proc_txt.sql`, and `07_proc_audio.sql`.

Here is the core pattern from the PDF proc (abbreviated):

```sql
CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_PDF_FILES()
  RETURNS VARCHAR LANGUAGE SQL EXECUTE AS CALLER
AS $$
BEGIN
  INSERT INTO PROCESSED.PDF_INTELLIGENCE (FILE_ID, FILE_NAME, PARSED_TEXT, ...)
  SELECT
    f.FILE_ID,
    f.FILE_NAME,

    -- Read PDF content via AI_PARSE_DOCUMENT
    AI_PARSE_DOCUMENT(
      TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME),
      OBJECT_CONSTRUCT('mode', 'OCR')
    ):content::VARCHAR AS PARSED_TEXT,

    -- Extract structured fields
    AI_EXTRACT(
      AI_PARSE_DOCUMENT(
        TO_FILE('@RAW.S3_MEDICAL_DOCS', f.FILE_NAME), OBJECT_CONSTRUCT('mode', 'OCR')
      ):content::VARCHAR,
      OBJECT_CONSTRUCT(
        'patient_name', 'string: full name of the patient',
        'diagnosis',    'string: primary diagnosis or findings',
        'medications',  'array: list of medications mentioned'
        -- ... additional fields
      )
    ) AS EXTRACTED_FIELDS,

    -- Classify document type
    AI_CLASSIFY(
      ...,
      ARRAY_CONSTRUCT('Lab Report', 'Discharge Summary', 'Prescription', ...)
    ):labels[0]::VARCHAR AS DOC_CATEGORY,

    -- Sentiment (float)
    SNOWFLAKE.CORTEX.SENTIMENT(...) AS SENTIMENT_SCORE,

    -- Summary
    SNOWFLAKE.CORTEX.SUMMARIZE(...) AS SUMMARY,

    -- PII redaction
    AI_REDACT(...) AS REDACTED_TEXT,

    -- LLM-generated insights
    AI_COMPLETE('claude-3-5-sonnet', CONCAT('Analyze this document: ', ...)) AS KEY_INSIGHTS,

    -- Vector embedding for search
    AI_EMBED('snowflake-arctic-embed-m-v1.5', ...) AS EMBEDDING

  FROM RAW.FILES_LOG f
  WHERE f.FILE_TYPE = 'PDF' AND f.IS_PROCESSED = FALSE;

  UPDATE RAW.FILES_LOG SET IS_PROCESSED = TRUE, PROCESSED_AT = CURRENT_TIMESTAMP()
  WHERE FILE_TYPE = 'PDF' AND IS_PROCESSED = FALSE;

  RETURN 'PDF processing complete';
END; $$;
```

**TXT files** (`06_proc_txt.sql`): Use `AI_PARSE_DOCUMENT` with LAYOUT mode to read text content (since `TO_VARCHAR(TO_FILE(...))` is not supported). Same AI function chain minus the separate OCR step.

**Audio files** (`07_proc_audio.sql`): Use `AI_TRANSCRIBE(TO_FILE(...))` (single argument) to get transcript text, then apply the same chain. `AI_COMPLETE` generates SOAP consultation notes instead of generic insights.

### Orchestrator and Event-Driven Task

Run `08_orchestrator_proc_and_task.sql` to create a stream-triggered task that fires automatically when new files arrive:

```sql
-- Orchestrator calls all 3 procs in sequence
CREATE OR REPLACE PROCEDURE PROCESSED.PROCESS_NEW_FILES()
  RETURNS VARCHAR LANGUAGE SQL EXECUTE AS CALLER
AS $$
BEGIN
  CALL PROCESSED.PROCESS_PDF_FILES();
  CALL PROCESSED.PROCESS_TXT_FILES();
  CALL PROCESSED.PROCESS_AUDIO_FILES();
  RETURN 'Processing complete: ' || CURRENT_TIMESTAMP()::VARCHAR;
END; $$;

-- Stream-triggered task: polls every minute, fires when new files land
CREATE OR REPLACE TASK RAW.PROCESS_NEW_FILES_TASK
  WAREHOUSE = HEALTHCARE_AI_WH
  SCHEDULE  = '1 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('RAW.FILES_LOG_STREAM')
AS
  CALL PROCESSED.PROCESS_NEW_FILES();

ALTER TASK RAW.PROCESS_NEW_FILES_TASK RESUME;
```

<!-- ------------------------ -->
## Building Cortex Search Services
Duration: 5

Cortex Search provides semantic retrieval over the AI-enriched content. Each search service indexes a text column and exposes filterable attributes. Run `11_cortex_search.sql`.

### Pattern

The pattern is: concatenate the most useful text fields (raw content + summary + insights + key extracted fields) into a single `SEARCH_TEXT` column, and expose structured attributes for filtering.

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE PROCESSED.PDF_SEARCH
  ON SEARCH_TEXT
  ATTRIBUTES DOC_CATEGORY, PATIENT_NAME, PROVIDER_NAME, DIAGNOSIS,
             DETECTED_LANGUAGE, SENTIMENT_SCORE, PROCESSED_AT
  WAREHOUSE = HEALTHCARE_AI_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
AS (
    SELECT
      DOC_ID, FILE_NAME,
      CONCAT(
        COALESCE(PARSED_TEXT, ''), '\n\n',
        'SUMMARY: ', COALESCE(SUMMARY, ''), '\n\n',
        'INSIGHTS: ', COALESCE(KEY_INSIGHTS, ''), '\n\n',
        'DIAGNOSIS: ', COALESCE(EXTRACTED_FIELDS:diagnosis::VARCHAR, '')
      ) AS SEARCH_TEXT,
      DOC_CATEGORY,
      COALESCE(EXTRACTED_FIELDS:patient_name::VARCHAR, 'Unknown') AS PATIENT_NAME,
      COALESCE(EXTRACTED_FIELDS:provider_name::VARCHAR, 'Unknown') AS PROVIDER_NAME,
      COALESCE(EXTRACTED_FIELDS:diagnosis::VARCHAR, '') AS DIAGNOSIS,
      DETECTED_LANGUAGE,
      SENTIMENT_SCORE::VARCHAR AS SENTIMENT_SCORE,
      PROCESSED_AT::VARCHAR AS PROCESSED_AT
    FROM PROCESSED.PDF_INTELLIGENCE
);
```

The same pattern is applied for `TXT_SEARCH` (over TXT_INTELLIGENCE) and `AUDIO_SEARCH` (over AUDIO_INTELLIGENCE, using transcript + consultation notes + chief complaint).

> aside negative
>
> Wait **2-3 minutes** after creating search services for indexing to complete before testing.

```sql
-- Verify all 3 services are active
SHOW CORTEX SEARCH SERVICES IN DATABASE HEALTHCARE_AI_DEMO;
```

<!-- ------------------------ -->
## Building the Semantic View for Cortex Analyst
Duration: 5

Cortex Analyst converts natural language questions into SQL. It requires a Semantic View that defines tables, relationships, dimensions, and metrics. Run `09_structured_data.sql` to load the example structured data, then `10_analytics_views.sql` for analytics views, and `12_semantic_view.sql` for the semantic view.

### Structured Data (Example: Healthcare)

| Table | Rows | Purpose |
|---|---|---|
| `ANALYTICS.PROVIDERS` | 12 | Entity master (who provides the service) |
| `ANALYTICS.PATIENTS` | 15 | Entity master (who receives the service) |
| `ANALYTICS.CLAIMS` | 30 | Transactional data (billing, procedures, diagnoses) |
| `ANALYTICS.APPOINTMENTS` | 24 | Transactional data (scheduling, visit types) |

### Semantic View Pattern

The semantic view declares tables, primary keys, foreign key relationships, dimensions (categorical columns), and metrics (aggregations). This is what Cortex Analyst uses to generate correct SQL.

```sql
CREATE OR REPLACE SEMANTIC VIEW ANALYTICS.HEALTHCARE_ANALYTICS

  TABLES (
    PATIENTS AS ANALYTICS.PATIENTS PRIMARY KEY (PATIENT_ID)
      COMMENT = 'Patient demographics and registration',
    PROVIDERS AS ANALYTICS.PROVIDERS PRIMARY KEY (PROVIDER_ID)
      COMMENT = 'Provider directory and specialties',
    CLAIMS AS ANALYTICS.CLAIMS PRIMARY KEY (CLAIM_ID)
      COMMENT = 'Claims data including billing, diagnosis, procedures, and status',
    APPOINTMENTS AS ANALYTICS.APPOINTMENTS PRIMARY KEY (APPOINTMENT_ID)
      COMMENT = 'Appointment scheduling, visit types, and recording status'
  )

  RELATIONSHIPS (
    patients_to_providers AS
      PATIENTS (PRIMARY_PROVIDER_ID) REFERENCES PROVIDERS (PROVIDER_ID),
    claims_to_patients AS
      CLAIMS (PATIENT_ID) REFERENCES PATIENTS (PATIENT_ID),
    claims_to_providers AS
      CLAIMS (PROVIDER_ID) REFERENCES PROVIDERS (PROVIDER_ID),
    appointments_to_patients AS
      APPOINTMENTS (PATIENT_ID) REFERENCES PATIENTS (PATIENT_ID),
    appointments_to_providers AS
      APPOINTMENTS (PROVIDER_ID) REFERENCES PROVIDERS (PROVIDER_ID)
  )

  DIMENSIONS (
    -- Every column Analyst should know about, with descriptive comments
    PATIENTS.insurance_plan AS INSURANCE_PLAN
      COMMENT = 'Insurance plan name (Aetna PPO, UnitedHealth, Cigna, Anthem, Medicare)',
    CLAIMS.claim_status AS CLAIM_STATUS
      COMMENT = 'Status: Approved, Denied, Pending, Under Review',
    -- ... 28 more dimensions across all 4 tables
  )

  METRICS (
    -- Aggregations that Analyst can compute
    CLAIMS.total_billed_amount AS SUM(BILLED_AMOUNT)
      COMMENT = 'Total amount billed in dollars',
    CLAIMS.claim_count AS COUNT(CLAIM_ID)
      COMMENT = 'Number of claims',
    APPOINTMENTS.avg_duration_minutes AS AVG(DURATION_MINUTES)
      COMMENT = 'Average appointment duration in minutes',
    -- ... 11 more metrics
  )

  COMMENT = 'Healthcare analytics semantic view for Cortex Analyst.';
```

> aside positive
>
> **Tip:** Descriptive `COMMENT` values on dimensions and metrics significantly improve Analyst's ability to understand your schema. Include the actual categorical values (e.g., "Approved, Denied, Pending") and units (e.g., "in dollars", "in minutes").

```sql
-- Verify
DESCRIBE SEMANTIC VIEW ANALYTICS.HEALTHCARE_ANALYTICS;
```

<!-- ------------------------ -->
## Assembling the Cortex Agent
Duration: 5

A Cortex Agent combines multiple tools --- Cortex Analyst for structured queries and Cortex Search for semantic retrieval --- into a single conversational endpoint. Run `13_cortex_agent.sql`.

### Agent Specification

```sql
CREATE OR REPLACE AGENT ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT
  COMMENT = 'Intelligence agent combining structured data queries with
    unstructured search across PDF, text, and audio content.'
  FROM SPECIFICATION
$$
models:
  orchestration: auto

instructions:
  system: >
    You are an intelligence assistant. You help users explore structured data,
    search through documents, and find information in audio transcripts.
  orchestration: >
    Use HealthcareAnalyst for quantitative questions about patients, providers,
    claims, and appointments.
    Use PDFSearch for content found in PDF documents.
    Use TXTSearch for content found in text documents.
    Use AudioSearch for content found in audio consultation transcripts.
    If a question spans both structured and unstructured data, use multiple
    tools and combine the results.
  sample_questions:
    - question: "Which providers have the highest total billed amounts?"
    - question: "Find documents mentioning diabetes or hypertension"
    - question: "What consultations discussed medication changes?"
    - question: "Compare findings across PDF and text documents"

tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: HealthcareAnalyst
      description: "Queries structured data: patients, providers, claims, appointments."
  - tool_spec:
      type: cortex_search
      name: PDFSearch
      description: "Searches AI-processed PDF documents."
  - tool_spec:
      type: cortex_search
      name: TXTSearch
      description: "Searches AI-processed text documents."
  - tool_spec:
      type: cortex_search
      name: AudioSearch
      description: "Searches transcribed audio recordings."

tool_resources:
  HealthcareAnalyst:
    semantic_view: "HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_ANALYTICS"
  PDFSearch:
    name: "HEALTHCARE_AI_DEMO.PROCESSED.PDF_SEARCH"
  TXTSearch:
    name: "HEALTHCARE_AI_DEMO.PROCESSED.TXT_SEARCH"
  AudioSearch:
    name: "HEALTHCARE_AI_DEMO.PROCESSED.AUDIO_SEARCH"
$$;
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **One search service per file type** | Different file types have different attributes (PDFs have DOC_CATEGORY, audio has CALL_CATEGORY and DURATION). Separate services allow type-specific filtering. |
| **Orchestration instructions** | Explicitly mapping question types to tools improves routing accuracy. |
| **`sample_questions`** | Helps the agent understand the expected query patterns. |

```sql
-- Verify
DESCRIBE AGENT ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT;
```

<!-- ------------------------ -->
## Snowflake Intelligence as the Chat Frontend
Duration: 5

Snowflake Intelligence provides a no-code chat UI on top of the Cortex Agent. Run `16_snowflake_intelligence.sql` for SQL-based verification queries, then set up the UI.

### Create a Snowflake Intelligence App

1. Navigate to **AI & ML → Intelligence** in Snowsight
2. Click **New Agent** or **Create**
3. Set **Agent** to `HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT`
4. The 4 tools (HealthcareAnalyst, PDFSearch, TXTSearch, AudioSearch) are inherited automatically
5. Click **Create**

### Verify the Full Pipeline

```sql
SELECT 'FILES_LOG'           AS OBJECT, COUNT(*) AS ROWS FROM RAW.FILES_LOG
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
```

Expected (with the sample healthcare dataset):

| Object | Rows |
|---|---|
| FILES_LOG | 15 |
| PDF_INTELLIGENCE | 6 |
| TXT_INTELLIGENCE | 4 |
| AUDIO_INTELLIGENCE | 5 |
| PROVIDERS | 12 |
| PATIENTS | 15 |
| CLAIMS | 30 |
| APPOINTMENTS | 24 |

<!-- ------------------------ -->
## Test: Query Across All Tools
Duration: 10

Open Snowflake Intelligence and test queries that exercise each tool. Full validation queries are in `15_validation_queries.sql`.

### Structured Data (Cortex Analyst)

These route to the HealthcareAnalyst tool and generate SQL via the semantic view:

```
Which providers have the highest total billed amounts?
```

```
How many claims were denied and what were the reasons?
```

```
What is the average claim amount by specialty?
```

### Unstructured Search (Cortex Search)

These route to the search services for semantic retrieval:

```
Find documents mentioning diabetes or hypertension
```

```
What consultations discussed medication changes?
```

```
Search for post-operative nursing observations
```

### Cross-Tool (Agent Orchestration)

These require the agent to call multiple tools and combine results:

```
Which patients have both documents and audio recordings? What were they about?
```

```
What are the most common diagnoses across all medical documents?
```

```
Compare findings across PDF and text documents for the same patient
```

<!-- ------------------------ -->
## Cleanup
Duration: 2

```sql
ALTER TASK HEALTHCARE_AI_DEMO.RAW.PROCESS_NEW_FILES_TASK SUSPEND;

DROP DATABASE IF EXISTS HEALTHCARE_AI_DEMO;
DROP WAREHOUSE IF EXISTS HEALTHCARE_AI_WH;
DROP STORAGE INTEGRATION IF EXISTS HEALTHCARE_S3_INTEGRATION;
```

```bash
# AWS cleanup
aws s3 rb s3://YOUR-BUCKET --force
aws iam detach-role-policy --role-name SnowflakeHealthcareRole \
  --policy-arn arn:aws:iam::<ACCOUNT>:policy/SnowflakeHealthcareS3Access
aws iam delete-role --role-name SnowflakeHealthcareRole
aws iam delete-policy --policy-arn arn:aws:iam::<ACCOUNT>:policy/SnowflakeHealthcareS3Access
```

<!-- ------------------------ -->
## Conclusion
Duration: 1

You've built a complete pipeline from S3 file ingestion to conversational AI.

### Patterns You Can Reuse

| Pattern | Key Technique | Reusable For |
|---|---|---|
| **Metadata-only Snowpipe** | CSV format with `RECORD_DELIMITER=NONE`, `METADATA$` pseudocolumns | Any binary/mixed file ingestion from S3 |
| **AI function chain** | `TO_FILE()` + `AI_PARSE_DOCUMENT` / `AI_TRANSCRIBE` → extract → classify → summarize → embed | Any document/audio processing pipeline |
| **Stream + Task** | `SYSTEM$STREAM_HAS_DATA()` trigger | Event-driven processing of new file arrivals |
| **Cortex Search** | Concatenated text + filterable attributes | Semantic search over any enriched content |
| **Semantic View** | Tables + relationships + dimensions + metrics | Natural-language-to-SQL for any structured dataset |
| **Cortex Agent** | Multiple tool types (Analyst + Search) | Unified Q&A across structured + unstructured data |

### Related Resources

- [Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Agent](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
- [Snowpipe AUTO_INGEST with S3](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-s3)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-intelligence)

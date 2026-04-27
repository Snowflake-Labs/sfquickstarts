-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 02: Data Foundation
-- ============================================================================
-- Description: Creates tables and loads data from Git repository
-- Prerequisites: Run 01_configure_account.sql first
-- ============================================================================

USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;
USE DATABASE TELCO_OPERATIONS_AI;
USE SCHEMA DEFAULT_SCHEMA;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- Enable cross-region inference for Cortex AI functions
-- This allows using AI models hosted in other regions when not available locally
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- ============================================================================
-- Step 1: Copy Data Files from Git Repository to Stages
-- ============================================================================

-- Copy CSV data files from Git repository to CSV_STAGE
COPY FILES INTO @CSV_STAGE
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/data/
PATTERN = '.*\.csv';

-- Copy PDF files from Git repository to PDF_STAGE
COPY FILES INTO @PDF_STAGE
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/data/pdfs/
PATTERN = '.*\.pdf';

-- Copy audio files from Git repository to AUDIO_STAGE
COPY FILES INTO @AUDIO_STAGE/call_recordings/
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/audio/
PATTERN = '.*\.mp3';

-- Refresh stage metadata
ALTER STAGE CSV_STAGE REFRESH;
ALTER STAGE PDF_STAGE REFRESH;
ALTER STAGE AUDIO_STAGE REFRESH;

SELECT 'Files copied from Git repository to stages' AS status;

-- ============================================================================
-- Step 2: Create Tables from CSV Files
-- ============================================================================

-- Table: NETWORK_PERFORMANCE
CREATE OR REPLACE TABLE network_performance (
    tower_id VARCHAR(50),
    tower_name VARCHAR(100),
    region VARCHAR(50),
    network_type VARCHAR(10),
    measurement_date DATE,
    measurement_hour INT,
    avg_latency_ms FLOAT,
    avg_download_speed_mbps FLOAT,
    avg_upload_speed_mbps FLOAT,
    packet_loss_pct FLOAT,
    signal_strength_dbm FLOAT,
    active_users INT,
    data_volume_gb FLOAT,
    peak_concurrent_users INT,
    call_drop_rate_pct FLOAT,
    handover_success_rate_pct FLOAT,
    availability_pct FLOAT
) COMMENT = 'Network performance metrics from towers';

COPY INTO network_performance
FROM @CSV_STAGE/network_performance.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- Table: INFRASTRUCTURE_CAPACITY
CREATE OR REPLACE TABLE infrastructure_capacity (
    tower_id VARCHAR(50),
    tower_name VARCHAR(100),
    region VARCHAR(50),
    network_type VARCHAR(10),
    capacity_date DATE,
    total_bandwidth_gbps FLOAT,
    used_bandwidth_gbps FLOAT,
    available_bandwidth_gbps FLOAT,
    utilization_pct FLOAT,
    equipment_status VARCHAR(20),
    last_maintenance_date DATE,
    next_scheduled_maintenance DATE,
    expected_growth_pct FLOAT,
    upgrade_recommended BOOLEAN,
    estimated_capacity_exhaustion_date DATE
) COMMENT = 'Infrastructure capacity and utilization data';

COPY INTO infrastructure_capacity
FROM @CSV_STAGE/infrastructure_capacity.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- Table: CUSTOMER_FEEDBACK_SUMMARY
CREATE OR REPLACE TABLE customer_feedback_summary (
    feedback_date DATE,
    region VARCHAR(50),
    feedback_type VARCHAR(50),
    total_feedback_count INT,
    complaint_count INT,
    compliment_count INT,
    inquiry_count INT,
    avg_sentiment_score FLOAT,
    negative_sentiment_count INT,
    neutral_sentiment_count INT,
    positive_sentiment_count INT,
    network_issue_count INT,
    billing_issue_count INT,
    service_issue_count INT,
    other_issue_count INT
) COMMENT = 'Aggregated customer feedback metrics';

COPY INTO customer_feedback_summary
FROM @CSV_STAGE/customer_feedback_summary.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- Table: CUSTOMER_DETAILS
CREATE OR REPLACE TABLE customer_details (
    customer_id VARCHAR(50),
    customer_segment VARCHAR(50),
    region VARCHAR(50),
    signup_date DATE,
    plan_type VARCHAR(50),
    monthly_revenue FLOAT,
    tenure_months INT,
    is_churned BOOLEAN,
    churn_date DATE,
    churn_reason VARCHAR(200)
) COMMENT = 'Customer demographics and account details';

COPY INTO customer_details
FROM @CSV_STAGE/customer_details.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- Table: CUSTOMER_INTERACTION_HISTORY
CREATE OR REPLACE TABLE customer_interaction_history (
    customer_id VARCHAR(50),
    total_calls INT,
    total_complaints INT,
    avg_csat_score FLOAT,
    avg_sentiment_score FLOAT,
    first_contact_date DATE,
    last_contact_date DATE,
    total_network_issues INT,
    total_billing_issues INT,
    total_service_issues INT,
    escalation_count INT,
    unresolved_issues INT,
    is_at_risk BOOLEAN
) COMMENT = 'Historical customer interaction metrics';

COPY INTO customer_interaction_history
FROM @CSV_STAGE/customer_interaction_history.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- Table: CSAT_SURVEYS
CREATE OR REPLACE TABLE csat_surveys (
    survey_id VARCHAR(50),
    call_id VARCHAR(50),
    customer_id VARCHAR(50),
    survey_date DATE,
    csat_score INT,
    nps_score INT,
    would_recommend BOOLEAN,
    survey_comments TEXT
) COMMENT = 'Customer satisfaction survey responses';

COPY INTO csat_surveys
FROM @CSV_STAGE/csat_surveys.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- Table: CUSTOMER_CALL_TRANSCRIPTS (populated via AI_TRANSCRIBE in Step 5)
CREATE OR REPLACE TABLE customer_call_transcripts (
    call_id VARCHAR(50),
    customer_id VARCHAR(50),
    call_date TIMESTAMP,
    call_duration_seconds INT,
    audio_file_path VARCHAR(500),
    transcript_text TEXT,
    sentiment_score VARIANT,
    key_issues ARRAY,
    summary TEXT,
    resolution_status VARCHAR(50),
    agent_name VARCHAR(100),
    call_reason VARCHAR(100),
    csat_score INT
) COMMENT = 'Call transcripts from audio files - populated via AI_TRANSCRIBE';

-- Table: CUSTOMER_COMPLAINT_DOCUMENTS (populated via AI_PARSE_DOCUMENT in Step 6)
CREATE OR REPLACE TABLE CUSTOMER_COMPLAINT_DOCUMENTS (
    DOCUMENT_ID VARCHAR(50),
    CUSTOMER_ID VARCHAR(50),
    DOCUMENT_TYPE VARCHAR(100),
    FILE_PATH VARCHAR(500),
    RAW_CONTENT TEXT,
    PARSED_CONTENT VARIANT,
    SUMMARY TEXT,
    SENTIMENT_SCORE VARIANT,
    KEY_TOPICS ARRAY,
    COMPLAINT_CATEGORY VARCHAR(100),
    URGENCY_LEVEL VARCHAR(20),
    EXTRACTED_AT TIMESTAMP
) COMMENT = 'Parsed customer complaint documents from PDFs - populated via AI_PARSE_DOCUMENT';

-- Table: CALL_TRANSCRIPTS (pre-loaded sample data)
CREATE OR REPLACE TABLE CALL_TRANSCRIPTS (
    CALL_ID VARCHAR(50),
    SEGMENT_ID VARCHAR(50),
    SEGMENT_NUMBER INT,
    SPEAKER_ID INT,
    SPEAKER_ROLE VARCHAR(20),
    SEGMENT_TEXT VARCHAR(16777216),
    SENTIMENT_SCORE FLOAT,
    SEGMENT_START_TIME FLOAT,
    SEGMENT_END_TIME FLOAT,
    CALL_TIMESTAMP TIMESTAMP_NTZ,
    CALL_DURATION_SECONDS INT,
    CONSTRAINT pk_call_transcripts PRIMARY KEY (SEGMENT_ID)
) COMMENT = 'Pre-transcribed call segments';

COPY INTO CALL_TRANSCRIPTS
FROM @CSV_STAGE/call_transcripts_sample.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- View: CALL_SENTIMENT_SUMMARY
CREATE OR REPLACE VIEW CALL_SENTIMENT_SUMMARY AS
SELECT 
    CALL_ID,
    MAX(CALL_TIMESTAMP) as CALL_TIMESTAMP,
    MAX(CALL_DURATION_SECONDS) as CALL_DURATION_SECONDS,
    'cust_' || SUBSTRING(CALL_ID, 6, 4) as CUSTOMER_ID,
    'agent_' || (HASH(CALL_ID) % 50 + 1) as AGENT_ID,
    CASE 
        WHEN CALL_ID LIKE '%001%' THEN 'Technical'
        WHEN CALL_ID LIKE '%002%' THEN 'Billing'
        WHEN CALL_ID LIKE '%003%' THEN 'Retention'
        WHEN CALL_ID LIKE '%004%' THEN 'Sales'
        ELSE 'General'
    END as CALL_CATEGORY,
    CASE 
        WHEN AVG(SENTIMENT_SCORE) > 0.5 THEN 'Resolved'
        WHEN AVG(SENTIMENT_SCORE) < -0.5 THEN 'Escalated'
        ELSE 'Follow-up Required'
    END as RESOLUTION_STATUS,
    AVG(SENTIMENT_SCORE) as AVG_SENTIMENT_SCORE,
    MIN(SENTIMENT_SCORE) as MIN_SENTIMENT_SCORE,
    MAX(SENTIMENT_SCORE) as MAX_SENTIMENT_SCORE,
    CASE 
        WHEN MAX(SENTIMENT_SCORE) - MIN(SENTIMENT_SCORE) > 0.5 THEN 'Improving'
        WHEN MIN(SENTIMENT_SCORE) - MAX(SENTIMENT_SCORE) > 0.5 THEN 'Declining'
        ELSE 'Stable'
    END as SENTIMENT_TREND,
    AVG(CASE WHEN SPEAKER_ROLE = 'Customer' THEN SENTIMENT_SCORE END) as CUSTOMER_SENTIMENT_AVG,
    AVG(CASE WHEN SPEAKER_ROLE = 'Agent' THEN SENTIMENT_SCORE END) as AGENT_SENTIMENT_AVG
FROM CALL_TRANSCRIPTS
GROUP BY CALL_ID;

-- Table: CUSTOMER_PROFILES
CREATE OR REPLACE TABLE CUSTOMER_PROFILES (
    CUSTOMER_ID VARCHAR(50) PRIMARY KEY,
    CUSTOMER_NAME VARCHAR(200),
    EMAIL VARCHAR(200),
    PHONE VARCHAR(20),
    ACCOUNT_NUMBER VARCHAR(50),
    CUSTOMER_SEGMENT VARCHAR(50),
    TENURE_MONTHS INT,
    MONTHLY_CHARGES FLOAT,
    TOTAL_LIFETIME_VALUE FLOAT,
    SERVICE_PLAN VARCHAR(50),
    CONTRACT_TYPE VARCHAR(50),
    AUTO_PAY_ENABLED BOOLEAN,
    PAYMENT_METHOD VARCHAR(50),
    CHURN_RISK_SCORE FLOAT,
    CHURNED BOOLEAN,
    CHURN_DATE DATE
) COMMENT = 'Customer demographics and account information';

-- Populate CUSTOMER_PROFILES from CUSTOMER_DETAILS
INSERT INTO CUSTOMER_PROFILES
SELECT
    cd.customer_id,
    CONCAT(
        ARRAY_CONSTRUCT('Ahmad', 'Siti', 'Muhammad', 'Nurul', 'Mohd', 'Tan', 'Lee', 'Wong', 'Lim', 'Kumar')[UNIFORM(0, 9, RANDOM())], ' ',
        ARRAY_CONSTRUCT('bin Abdullah', 'binti Hassan', 'Wei Ming', 'Ah Kow', 'Raj', 'Kaur', 'Ibrahim', 'Yusof')[UNIFORM(0, 7, RANDOM())]
    ) as customer_name,
    LOWER(REPLACE(cd.customer_id, '_', '')) || '@novaconnect.my' as email,
    '+60' || UNIFORM(10, 19, RANDOM())::VARCHAR || UNIFORM(1000000, 9999999, RANDOM())::VARCHAR as phone,
    'ACC' || LPAD(UNIFORM(100000, 999999, RANDOM())::VARCHAR, 8, '0') as account_number,
    cd.customer_segment,
    cd.tenure_months,
    cd.monthly_revenue as monthly_charges,
    cd.monthly_revenue * cd.tenure_months as total_lifetime_value,
    cd.plan_type as service_plan,
    ARRAY_CONSTRUCT('Monthly', '12 Months', '24 Months')[UNIFORM(0, 2, RANDOM())] as contract_type,
    UNIFORM(0, 1, RANDOM()) = 1 as auto_pay_enabled,
    ARRAY_CONSTRUCT('Credit Card', 'Debit Card', 'Bank Transfer', 'E-Wallet')[UNIFORM(0, 3, RANDOM())] as payment_method,
    CASE 
        WHEN cd.is_churned THEN 1.0
        WHEN cih.is_at_risk THEN UNIFORM(60, 90, RANDOM()) / 100.0
        WHEN cih.avg_csat_score < 3 THEN UNIFORM(50, 80, RANDOM()) / 100.0
        ELSE UNIFORM(5, 40, RANDOM()) / 100.0
    END as churn_risk_score,
    cd.is_churned as churned,
    cd.churn_date
FROM customer_details cd
LEFT JOIN customer_interaction_history cih ON cd.customer_id = cih.customer_id;

-- Table: SUPPORT_TICKETS
CREATE OR REPLACE TABLE SUPPORT_TICKETS (
    TICKET_ID VARCHAR(50) PRIMARY KEY,
    CUSTOMER_ID VARCHAR(50),
    CREATED_AT TIMESTAMP_NTZ,
    UPDATED_AT TIMESTAMP_NTZ,
    STATUS VARCHAR(50),
    PRIORITY VARCHAR(20),
    CATEGORY VARCHAR(50),
    SUBCATEGORY VARCHAR(100),
    SUBJECT VARCHAR(500),
    DESCRIPTION VARCHAR(16777216),
    AGENT_ID VARCHAR(50),
    RESOLUTION_TIME_HOURS FLOAT,
    CUSTOMER_SATISFACTION_RATING INT,
    SENTIMENT_SCORE FLOAT,
    ESCALATED BOOLEAN,
    REOPENED_COUNT INT
) COMMENT = 'Customer support tickets';

-- Generate SUPPORT_TICKETS data based on customer interaction history
INSERT INTO SUPPORT_TICKETS
WITH customer_sample AS (
    SELECT customer_id, total_complaints, total_network_issues, total_billing_issues, total_service_issues
    FROM customer_interaction_history
    WHERE total_complaints > 0
)
SELECT
    'TKT_' || LPAD(ROW_NUMBER() OVER (ORDER BY RANDOM())::VARCHAR, 6, '0') as TICKET_ID,
    cs.customer_id as CUSTOMER_ID,
    DATEADD(day, -UNIFORM(1, 90, RANDOM()), CURRENT_TIMESTAMP()) as CREATED_AT,
    DATEADD(hour, UNIFORM(1, 72, RANDOM()), CREATED_AT) as UPDATED_AT,
    ARRAY_CONSTRUCT('Open', 'In Progress', 'Resolved', 'Closed')[UNIFORM(0, 3, RANDOM())] as STATUS,
    ARRAY_CONSTRUCT('Low', 'Medium', 'High', 'Urgent')[UNIFORM(0, 3, RANDOM())] as PRIORITY,
    ARRAY_CONSTRUCT('Network', 'Billing', 'Service', 'Technical')[UNIFORM(0, 3, RANDOM())] as CATEGORY,
    CASE 
        WHEN CATEGORY = 'Network' THEN ARRAY_CONSTRUCT('Slow Speed', 'No Connection', 'Intermittent', 'Coverage')[UNIFORM(0, 3, RANDOM())]
        WHEN CATEGORY = 'Billing' THEN ARRAY_CONSTRUCT('Overcharge', 'Payment Issue', 'Bill Dispute', 'Refund')[UNIFORM(0, 3, RANDOM())]
        WHEN CATEGORY = 'Service' THEN ARRAY_CONSTRUCT('Activation', 'Plan Change', 'Cancellation', 'Upgrade')[UNIFORM(0, 3, RANDOM())]
        ELSE ARRAY_CONSTRUCT('Equipment', 'App Issue', 'Account Access', 'General')[UNIFORM(0, 3, RANDOM())]
    END as SUBCATEGORY,
    CATEGORY || ' Issue - ' || SUBCATEGORY || ' reported by customer' as SUBJECT,
    'Customer reported an issue regarding ' || LOWER(CATEGORY) || '. Details: ' || SUBCATEGORY || '. Customer requires assistance with their account.' as DESCRIPTION,
    'agent_' || UNIFORM(1, 50, RANDOM()) as AGENT_ID,
    UNIFORM(1, 48, RANDOM()) + UNIFORM(0, 100, RANDOM()) / 100.0 as RESOLUTION_TIME_HOURS,
    UNIFORM(1, 5, RANDOM()) as CUSTOMER_SATISFACTION_RATING,
    (UNIFORM(-100, 100, RANDOM()) / 100.0) as SENTIMENT_SCORE,
    UNIFORM(0, 10, RANDOM()) < 2 as ESCALATED,
    UNIFORM(0, 3, RANDOM()) as REOPENED_COUNT
FROM customer_sample cs,
     TABLE(GENERATOR(ROWCOUNT => 5)) g
LIMIT 500;

-- Table: AGENT_PERFORMANCE
CREATE OR REPLACE TABLE AGENT_PERFORMANCE (
    AGENT_ID VARCHAR(50) PRIMARY KEY,
    AGENT_NAME VARCHAR(200),
    HIRE_DATE DATE,
    TEAM VARCHAR(50),
    SHIFT VARCHAR(20),
    CALLS_HANDLED_LAST_30_DAYS INT,
    AVG_CALL_DURATION_SECONDS INT,
    FIRST_CALL_RESOLUTION_RATE FLOAT,
    AVG_CUSTOMER_SENTIMENT FLOAT,
    AVG_SATISFACTION_RATING FLOAT,
    ESCALATION_RATE FLOAT,
    TICKETS_HANDLED_LAST_30_DAYS INT,
    AVG_TICKET_RESOLUTION_TIME_HOURS FLOAT,
    QUALITY_SCORE INT,
    CERTIFICATION_LEVEL VARCHAR(20)
) COMMENT = 'Agent performance metrics';

-- Generate sample agent data
INSERT INTO AGENT_PERFORMANCE
SELECT
    'agent_' || SEQ4() as AGENT_ID,
    CONCAT(
        ARRAY_CONSTRUCT('Mike', 'Lisa', 'John', 'Sarah', 'David')[UNIFORM(0, 4, RANDOM())], ' ',
        ARRAY_CONSTRUCT('Anderson', 'Chen', 'Smith', 'Johnson', 'Martinez')[UNIFORM(0, 4, RANDOM())]
    ) as AGENT_NAME,
    DATEADD(month, -(UNIFORM(6, 60, RANDOM())), CURRENT_DATE()) as HIRE_DATE,
    ARRAY_CONSTRUCT('Technical Support', 'Billing', 'Sales', 'General Support')[UNIFORM(0, 3, RANDOM())] as TEAM,
    ARRAY_CONSTRUCT('Morning', 'Afternoon', 'Evening', 'Night')[UNIFORM(0, 3, RANDOM())] as SHIFT,
    UNIFORM(100, 400, RANDOM()) as CALLS_HANDLED_LAST_30_DAYS,
    UNIFORM(200, 600, RANDOM()) as AVG_CALL_DURATION_SECONDS,
    UNIFORM(70, 95, RANDOM()) / 100.0 as FIRST_CALL_RESOLUTION_RATE,
    UNIFORM(40, 80, RANDOM()) / 100.0 as AVG_CUSTOMER_SENTIMENT,
    UNIFORM(35, 50, RANDOM()) / 10.0 as AVG_SATISFACTION_RATING,
    UNIFORM(3, 15, RANDOM()) / 100.0 as ESCALATION_RATE,
    UNIFORM(40, 120, RANDOM()) as TICKETS_HANDLED_LAST_30_DAYS,
    UNIFORM(10, 60, RANDOM()) / 10.0 as AVG_TICKET_RESOLUTION_TIME_HOURS,
    UNIFORM(70, 100, RANDOM()) as QUALITY_SCORE,
    ARRAY_CONSTRUCT('Junior', 'Standard', 'Senior', 'Expert')[UNIFORM(0, 3, RANDOM())] as CERTIFICATION_LEVEL
FROM TABLE(GENERATOR(ROWCOUNT => 50));

-- Table: NETWORK_INCIDENTS
CREATE OR REPLACE TABLE NETWORK_INCIDENTS (
    INCIDENT_ID VARCHAR(50) PRIMARY KEY,
    INCIDENT_TYPE VARCHAR(50),
    SEVERITY VARCHAR(20),
    STATUS VARCHAR(20),
    START_TIME TIMESTAMP_NTZ,
    END_TIME TIMESTAMP_NTZ,
    DURATION_MINUTES INT,
    AFFECTED_AREA VARCHAR(200),
    AFFECTED_CUSTOMERS_COUNT INT,
    SERVICE_TYPE VARCHAR(50),
    ROOT_CAUSE VARCHAR(1000),
    RESOLUTION_NOTES VARCHAR(1000),
    RELATED_CALLS_COUNT INT
) COMMENT = 'Network outages and performance issues';

INSERT INTO NETWORK_INCIDENTS
SELECT
    'inc_' || LPAD(SEQ4()::VARCHAR, 5, '0') as INCIDENT_ID,
    ARRAY_CONSTRUCT('Outage', 'Degradation', 'Maintenance')[UNIFORM(0, 2, RANDOM())] as INCIDENT_TYPE,
    ARRAY_CONSTRUCT('Low', 'Medium', 'High', 'Critical')[UNIFORM(0, 3, RANDOM())] as SEVERITY,
    'Resolved' as STATUS,
    DATEADD(hour, -(UNIFORM(1, 720, RANDOM())), CURRENT_TIMESTAMP()) as START_TIME,
    DATEADD(hour, UNIFORM(1, 12, RANDOM()), START_TIME) as END_TIME,
    DATEDIFF(minute, START_TIME, END_TIME) as DURATION_MINUTES,
    ARRAY_CONSTRUCT('Downtown', 'North Suburbs', 'South Region', 'East Side')[UNIFORM(0, 3, RANDOM())] as AFFECTED_AREA,
    UNIFORM(50, 2000, RANDOM()) as AFFECTED_CUSTOMERS_COUNT,
    ARRAY_CONSTRUCT('Internet', 'Voice', 'TV', 'Mobile')[UNIFORM(0, 3, RANDOM())] as SERVICE_TYPE,
    'Resolved incident - services restored' as ROOT_CAUSE,
    'Full resolution completed' as RESOLUTION_NOTES,
    UNIFORM(10, 300, RANDOM()) as RELATED_CALLS_COUNT
FROM TABLE(GENERATOR(ROWCOUNT => 300));

-- ============================================================================
-- Step 3: Create Analytical Views
-- ============================================================================

CREATE OR REPLACE VIEW VW_CALL_CENTER_METRICS AS
SELECT 
    DATE_TRUNC('day', CALL_TIMESTAMP) as call_date,
    COUNT(DISTINCT CALL_ID) as total_calls,
    AVG(CALL_DURATION_SECONDS) as avg_call_duration,
    AVG(AVG_SENTIMENT_SCORE) as avg_sentiment,
    SUM(CASE WHEN RESOLUTION_STATUS = 'Resolved' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as resolution_rate
FROM CALL_SENTIMENT_SUMMARY
GROUP BY call_date;

CREATE OR REPLACE VIEW VW_CUSTOMER_HEALTH AS
SELECT 
    cp.CUSTOMER_ID,
    cp.CUSTOMER_NAME,
    cp.CHURN_RISK_SCORE,
    COUNT(DISTINCT cs.CALL_ID) as total_calls,
    AVG(cs.AVG_SENTIMENT_SCORE) as avg_sentiment
FROM CUSTOMER_PROFILES cp
LEFT JOIN CALL_SENTIMENT_SUMMARY cs ON cp.CUSTOMER_ID = cs.CUSTOMER_ID
GROUP BY cp.CUSTOMER_ID, cp.CUSTOMER_NAME, cp.CHURN_RISK_SCORE;

CREATE OR REPLACE VIEW customer_360_view AS
SELECT 
    cd.customer_id,
    cd.customer_segment,
    cd.region,
    cd.plan_type,
    cd.monthly_revenue,
    cd.tenure_months,
    cd.signup_date,
    COALESCE(cih.total_calls, 0) as total_calls,
    COALESCE(cih.total_complaints, 0) as total_complaints,
    cih.avg_csat_score,
    cih.unresolved_issues,
    COALESCE(cih.is_at_risk, 
        CASE 
            WHEN cd.is_churned = TRUE THEN TRUE
            WHEN cih.avg_csat_score < 3 THEN TRUE
            WHEN cih.unresolved_issues > 2 THEN TRUE
            ELSE FALSE
        END) as is_at_risk,
    cd.is_churned
FROM customer_details cd
LEFT JOIN customer_interaction_history cih ON cd.customer_id = cih.customer_id;

-- ============================================================================
-- Step 4: Create EMAIL_PREVIEWS Table for SnowMail App
-- ============================================================================

CREATE OR REPLACE TABLE EMAIL_PREVIEWS (
    EMAIL_ID VARCHAR(50) PRIMARY KEY,
    RECIPIENT_EMAIL VARCHAR(200),
    SUBJECT VARCHAR(500),
    HTML_CONTENT TEXT,
    CREATED_AT TIMESTAMP,
    IS_READ BOOLEAN DEFAULT FALSE,
    IS_STARRED BOOLEAN DEFAULT FALSE
) COMMENT = 'Email previews for SnowMail application';

COPY INTO EMAIL_PREVIEWS
FROM (
    SELECT 
        $1 as EMAIL_ID,
        $2 as RECIPIENT_EMAIL,
        $3 as SUBJECT,
        $4 as HTML_CONTENT,
        TRY_TO_TIMESTAMP($5, 'YYYY-MM-DD HH24:MI:SS') as CREATED_AT,
        FALSE as IS_READ,
        FALSE as IS_STARRED
    FROM @CSV_STAGE/telco_email_previews.csv
)
FILE_FORMAT = CSV_FORMAT
ON_ERROR = CONTINUE;

-- ============================================================================
-- Step 5: Process Audio Files with AI_TRANSCRIBE
-- ============================================================================
-- This populates CUSTOMER_CALL_TRANSCRIPTS using AI to transcribe audio files
-- Note: AI_TRANSCRIBE processes audio files to extract text transcripts

-- Process audio files directly with AI_TRANSCRIBE using DIRECTORY table function
MERGE INTO CUSTOMER_CALL_TRANSCRIPTS tgt
USING (
    SELECT
        SPLIT_PART(SPLIT_PART(RELATIVE_PATH, '/', -1), '.', 1) as call_id,
        'cust_' || LPAD((ABS(HASH(RELATIVE_PATH)) % 1000 + 1)::VARCHAR, 4, '0') as customer_id,
        DATEADD(day, -ABS(HASH(RELATIVE_PATH) % 30 + 1), CURRENT_TIMESTAMP()) as call_date,
        ABS(HASH(RELATIVE_PATH) % 600 + 180) as call_duration_seconds,
        '@TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.AUDIO_STAGE/' || RELATIVE_PATH as audio_file_path,
        AI_TRANSCRIBE(
            TO_FILE('@TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.AUDIO_STAGE/' || RELATIVE_PATH)
        ):text::VARCHAR as transcript_text
    FROM DIRECTORY('@TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.AUDIO_STAGE')
    WHERE RELATIVE_PATH LIKE '%.mp3'
) src
ON tgt.CALL_ID = src.call_id
WHEN NOT MATCHED THEN INSERT (
    CALL_ID, CUSTOMER_ID, CALL_DATE, CALL_DURATION_SECONDS, AUDIO_FILE_PATH,
    TRANSCRIPT_TEXT, SENTIMENT_SCORE, KEY_ISSUES, SUMMARY, RESOLUTION_STATUS,
    AGENT_NAME, CALL_REASON, CSAT_SCORE
) VALUES (
    src.call_id,
    src.customer_id,
    src.call_date,
    src.call_duration_seconds,
    src.audio_file_path,
    src.transcript_text,
    SNOWFLAKE.CORTEX.SENTIMENT(src.transcript_text),
    ARRAY_CONSTRUCT(
        CASE 
            WHEN LOWER(src.transcript_text) LIKE '%network%' OR LOWER(src.transcript_text) LIKE '%internet%' THEN 'Network Issue'
            WHEN LOWER(src.transcript_text) LIKE '%bill%' OR LOWER(src.transcript_text) LIKE '%charge%' THEN 'Billing'
            WHEN LOWER(src.transcript_text) LIKE '%slow%' OR LOWER(src.transcript_text) LIKE '%speed%' THEN 'Speed Issue'
            ELSE 'General Inquiry'
        END
    ),
    SNOWFLAKE.CORTEX.SUMMARIZE(src.transcript_text),
    CASE 
        WHEN SNOWFLAKE.CORTEX.SENTIMENT(src.transcript_text) > 0 THEN 'Resolved'
        WHEN SNOWFLAKE.CORTEX.SENTIMENT(src.transcript_text) < 0 THEN 'Escalated'
        ELSE 'Pending'
    END,
    ARRAY_CONSTRUCT('Ahmad Ibrahim', 'Siti Aminah', 'Lee Wei Ming', 'Kumar Raj', 'Wong Ah Kow')[ABS(HASH(src.call_id) % 5)],
    ARRAY_CONSTRUCT('Technical Support', 'Billing Inquiry', 'Service Request', 'Complaint', 'Account Issue')[ABS(HASH(src.audio_file_path) % 5)],
    ABS(HASH(src.call_id) % 5 + 1)
);

-- ============================================================================
-- Step 6: Process PDF Documents with AI_PARSE_DOCUMENT
-- ============================================================================
-- This populates CUSTOMER_COMPLAINT_DOCUMENTS using AI to parse PDF files

-- Process PDF files with AI_PARSE_DOCUMENT
INSERT INTO CUSTOMER_COMPLAINT_DOCUMENTS
WITH parsed_docs AS (
    SELECT
        RELATIVE_PATH,
        AI_PARSE_DOCUMENT(
            TO_FILE('@TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.PDF_STAGE/' || RELATIVE_PATH),
            {'mode': 'LAYOUT'}
        ) as parsed_result
    FROM DIRECTORY('@TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.PDF_STAGE')
    WHERE RELATIVE_PATH LIKE '%.pdf'
)
SELECT
    'DOC_' || LPAD(ROW_NUMBER() OVER (ORDER BY RELATIVE_PATH)::VARCHAR, 4, '0') as document_id,
    'cust_' || LPAD((ABS(HASH(RELATIVE_PATH)) % 1000 + 1)::VARCHAR, 4, '0') as customer_id,
    'Product Information' as document_type,
    '@TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.PDF_STAGE/' || RELATIVE_PATH as file_path,
    parsed_result:content::VARCHAR as raw_content,
    parsed_result as parsed_content,
    SNOWFLAKE.CORTEX.SUMMARIZE(parsed_result:content::VARCHAR) as summary,
    SNOWFLAKE.CORTEX.SENTIMENT(parsed_result:content::VARCHAR) as sentiment_score,
    ARRAY_CONSTRUCT(
        CASE 
            WHEN LOWER(RELATIVE_PATH) LIKE '%5g%' THEN '5G Services'
            WHEN LOWER(RELATIVE_PATH) LIKE '%fiber%' THEN 'Fiber Internet'
            WHEN LOWER(RELATIVE_PATH) LIKE '%prepaid%' THEN 'Prepaid Plans'
            WHEN LOWER(RELATIVE_PATH) LIKE '%help%' THEN 'Customer Support'
            ELSE 'General'
        END
    ) as key_topics,
    CASE 
        WHEN LOWER(RELATIVE_PATH) LIKE '%5g%' THEN 'Mobile'
        WHEN LOWER(RELATIVE_PATH) LIKE '%fiber%' THEN 'Broadband'
        WHEN LOWER(RELATIVE_PATH) LIKE '%prepaid%' THEN 'Prepaid'
        ELSE 'General'
    END as complaint_category,
    ARRAY_CONSTRUCT('Low', 'Medium', 'High', 'Critical')[ABS(HASH(RELATIVE_PATH) % 4)] as urgency_level,
    CURRENT_TIMESTAMP() as extracted_at
FROM parsed_docs;

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 
    'CALL_TRANSCRIPTS' as table_name, COUNT(*) as row_count FROM CALL_TRANSCRIPTS
UNION ALL SELECT 'network_performance', COUNT(*) FROM network_performance
UNION ALL SELECT 'infrastructure_capacity', COUNT(*) FROM infrastructure_capacity
UNION ALL SELECT 'customer_feedback_summary', COUNT(*) FROM customer_feedback_summary
UNION ALL SELECT 'customer_details', COUNT(*) FROM customer_details
UNION ALL SELECT 'CUSTOMER_PROFILES', COUNT(*) FROM CUSTOMER_PROFILES
UNION ALL SELECT 'SUPPORT_TICKETS', COUNT(*) FROM SUPPORT_TICKETS
UNION ALL SELECT 'AGENT_PERFORMANCE', COUNT(*) FROM AGENT_PERFORMANCE
UNION ALL SELECT 'NETWORK_INCIDENTS', COUNT(*) FROM NETWORK_INCIDENTS
UNION ALL SELECT 'EMAIL_PREVIEWS', COUNT(*) FROM EMAIL_PREVIEWS
UNION ALL SELECT 'CUSTOMER_CALL_TRANSCRIPTS', COUNT(*) FROM CUSTOMER_CALL_TRANSCRIPTS
UNION ALL SELECT 'CUSTOMER_COMPLAINT_DOCUMENTS', COUNT(*) FROM CUSTOMER_COMPLAINT_DOCUMENTS;

SELECT 'Data foundation complete!' AS status,
       'TELCO_OPERATIONS_AI' AS database_name,
       CURRENT_TIMESTAMP() AS deployed_at;


author: Ravi Kumar
id: build-fwa-detection-platform-cortex-ai
summary: Build a complete Fraud, Waste, and Abuse detection platform for healthcare claims using Snowflake Cortex AI, Dynamic Tables, Snowflake ML, Cortex Search, Cortex Agents, and Streamlit.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions,snowflake-site:taxonomy/snowflake-feature/dynamic-tables,snowflake-site:taxonomy/snowflake-feature/ml-functions,snowflake-site:taxonomy/snowflake-feature/cortex-search,snowflake-site:taxonomy/snowflake-feature/cortex-analyst,snowflake-site:taxonomy/industry/public-sector,snowflake-site:taxonomy/industry/healthcare-and-life-sciences
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
language: en

# Build a Fraud, Waste, and Abuse Detection Platform with Snowflake Cortex AI
<!-- ------------------------ -->
## Overview

Duration: 5

**Author:** Ravi Kumar, Partner Solutions Architect

Public sector agencies rely on "pay and chase" — send the payment, then try to recover fraudulent dollars after the fact. A modern FWA platform needs to do many things at once: ingest and unify claims from disparate systems, profile provider behavior against peers in real time, run ML models for anomaly detection and predictive scoring, classify fraud types with LLM explainability, detect collusion rings through graph analysis, parse clinical documents and transcribe audio for evidence, and give investigators a natural-language interface to query it all — without moving sensitive PHI/PII outside the platform boundary.

Snowflake is uniquely suited for this because every one of these capabilities runs natively inside a single platform — no data egress, no external ML infrastructure, no separate graph database, no third-party LLM APIs. Dynamic Tables replace batch ETL with continuous refresh. Snowflake ML trains and scores anomaly detection and classification models in pure SQL. Cortex AI functions (AI_CLASSIFY, COMPLETE, AI_PARSE_DOCUMENT, AI_TRANSCRIBE, AI_SUMMARIZE) bring LLM intelligence directly to your data. Cortex Search indexes unstructured evidence for retrieval. Cortex Agents orchestrate structured and unstructured queries behind a single natural-language interface. And Streamlit in Snowflake delivers the investigator UI — all governed by Snowflake's native RBAC, masking policies, and encryption.

This guide builds a complete, end-to-end FWA detection platform for healthcare claims. Every SQL block is copy-pastable and validated. Nothing leaves Snowflake.

### Why Now?
- ML infrastructure now processes massive claim volumes in near real time at falling cost.
- LLMs unlock explainability — AI returns reasoning behind a flag, giving investigators probable cause.
- Fraudsters use AI too (fake records, synthetic identities). Agencies must match these tools for defense.

### Prerequisites
- Snowflake account with ACCOUNTADMIN (or roles with ML, Cortex AI, Cortex Search, Cortex Agent, and Streamlit privileges)
- A warehouse (MEDIUM) and familiarity with SQL and basic Python
- Cortex AI LLM functions require supported regions — check Snowflake docs for availability

### What You'll Learn
- How to build continuously refreshing provider behavior profiles with Dynamic Tables
- How to classify fraud types with LLM explainability using Cortex AI
- How to train anomaly detection and predictive models with Snowflake ML in pure SQL
- How to detect fraud rings with SQL-based graph analysis
- How to parse documents and transcribe audio with Cortex AI functions
- How to build a Cortex Agent for natural-language investigation
- How to deploy a Streamlit investigator application

### What You'll Build
- Unified data foundation with synthetic sample data
- Continuously refreshing provider behavior profiles (Dynamic Tables)
- LLM-driven fraud classification with plain-English explanations (Cortex AI)
- Anomaly detection and predictive fraud scoring (Snowflake ML)
- Fraud ring detection via SQL-based graph analysis
- Document and audio analysis pipelines (Cortex AI)
- Cortex Agent for natural-language investigation queries
- Streamlit in Snowflake investigator application

### Architecture

The platform follows four phases:

| Phase | What Happens | Guide Steps |
|-------|-------------|-------------|
| **1. Ingest & Contextualize** | Bring in claims, enrich into risk-scored profiles | Steps 2-3 |
| **2. Detect & Score** | LLM classification, anomaly detection, fraud rings | Steps 4-6 |
| **3. Analyze & Evidence** | Document/audio parsing, Cortex Agent | Steps 7-8 |
| **4. Decide & Act** | Streamlit UI, security, case management | Steps 9-11 |

<!-- ------------------------ -->
## Setup and Data Foundation

Duration: 10

### Create Infrastructure

```sql
-- Create the database and schema that hold all FWA objects
CREATE DATABASE IF NOT EXISTS FWA_QS;
CREATE SCHEMA IF NOT EXISTS FWA_QS.DETECTION;
USE DATABASE FWA_QS;
USE SCHEMA DETECTION;

-- Warehouse for all compute (Dynamic Tables, ML training, Cortex AI calls)
CREATE WAREHOUSE IF NOT EXISTS FWA_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60     -- suspend after 60s idle to save credits
  AUTO_RESUME = TRUE;   -- auto-resume when a query arrives

USE WAREHOUSE FWA_WH;

-- Internal stages for unstructured files (PDFs, invoices, audio recordings)
-- Snowflake-managed encryption keeps data secure at rest
CREATE STAGE IF NOT EXISTS FWA_QS.DETECTION.DOCUMENTS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
CREATE STAGE IF NOT EXISTS FWA_QS.DETECTION.AUDIO_FILES
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

### Create Base Tables

```sql
-- Providers: ADDRESS, PHONE, BANK_ACCOUNT columns enable fraud ring detection (Step 6)
CREATE OR REPLACE TABLE FWA_QS.DETECTION.PROVIDERS (
    PROVIDER_ID       VARCHAR(10) PRIMARY KEY,
    PROVIDER_NAME     VARCHAR(100),
    SPECIALTY         VARCHAR(50),
    ADDRESS           VARCHAR(200),
    PHONE             VARCHAR(20),
    BANK_ACCOUNT      VARCHAR(30),
    LICENSE_STATUS    VARCHAR(20) DEFAULT 'ACTIVE',
    STATE             VARCHAR(2)
);

-- Medicaid/Medicare beneficiaries (patients)
CREATE OR REPLACE TABLE FWA_QS.DETECTION.BENEFICIARIES (
    BENEFICIARY_ID    VARCHAR(10) PRIMARY KEY,
    FIRST_NAME        VARCHAR(50),
    LAST_NAME         VARCHAR(50),
    DOB               DATE,
    STATE             VARCHAR(2),
    ENROLLMENT_DATE   DATE
);

-- Claims: the central fact table. IS_FRAUD is NULL until an investigator confirms/rejects.
CREATE OR REPLACE TABLE FWA_QS.DETECTION.CLAIMS (
    CLAIM_ID          VARCHAR(10) PRIMARY KEY,
    PROVIDER_ID       VARCHAR(10) REFERENCES FWA_QS.DETECTION.PROVIDERS(PROVIDER_ID),
    BENEFICIARY_ID    VARCHAR(10) REFERENCES FWA_QS.DETECTION.BENEFICIARIES(BENEFICIARY_ID),
    PROCEDURE_CODE    VARCHAR(10),
    DIAGNOSIS_CODE    VARCHAR(10),
    CLAIM_AMOUNT      NUMBER(12,2),
    CLAIM_DATE        DATE,
    PRIOR_AUTH_FLAG   BOOLEAN,
    PLACE_OF_SERVICE  VARCHAR(50),
    IS_FRAUD          BOOLEAN DEFAULT NULL
);

-- OIG/state exclusion and watch list entries — drives 45-point risk score component
CREATE OR REPLACE TABLE FWA_QS.DETECTION.WATCH_LIST (
    PROVIDER_ID       VARCHAR(10),
    REASON            VARCHAR(200),
    ADDED_DATE        DATE,
    SOURCE            VARCHAR(50)
);

-- Tracks clinical documents (PDFs, invoices) uploaded to the DOCUMENTS stage
CREATE OR REPLACE TABLE FWA_QS.DETECTION.DOCUMENT_METADATA (
    DOC_ID            VARCHAR(10) PRIMARY KEY,
    CLAIM_ID          VARCHAR(10),
    FILE_NAME         VARCHAR(200),
    DOC_TYPE          VARCHAR(50),
    UPLOAD_DATE       DATE
);

-- Tracks audio files (hotline calls, whistleblower recordings) uploaded to AUDIO_FILES stage
CREATE OR REPLACE TABLE FWA_QS.DETECTION.AUDIO_METADATA (
    AUDIO_ID          VARCHAR(10) PRIMARY KEY,
    FILE_NAME         VARCHAR(200),
    SOURCE_TYPE       VARCHAR(50),
    RELATED_PROVIDER  VARCHAR(10),
    RECEIVED_DATE     DATE
);
```

<!-- ------------------------ -->
## Load Sample Data

Duration: 5

```sql
-- Providers: P-1001 and P-1002 share an address (fraud ring signal)
-- P-1002 and P-1003 share a bank account (fraud ring signal)
-- P-1008, P-1009, P-1010 are legitimate low-billing cardiology providers
-- that establish a realistic peer baseline for the billing ratio calculation
INSERT INTO FWA_QS.DETECTION.PROVIDERS VALUES
('P-1001','Dr. Alpha Medical','Cardiology','100 Main St, Austin TX','512-555-0101','ACCT-9999','ACTIVE','TX'),
('P-1002','Beta Health Corp','Cardiology','100 Main St, Austin TX','512-555-0102','ACCT-8888','ACTIVE','TX'),
('P-1003','Gamma Clinic','Orthopedics','200 Oak Ave, Dallas TX','214-555-0201','ACCT-8888','ACTIVE','TX'),
('P-1004','Delta Wellness','Cardiology','300 Elm St, Houston TX','713-555-0301','ACCT-7777','ACTIVE','TX'),
('P-1005','Epsilon Care','Orthopedics','400 Pine St, Austin TX','512-555-0401','ACCT-6666','ACTIVE','TX'),
('P-1006','Zeta Medical Group','General Practice','500 Cedar Ln, Dallas TX','214-555-0501','ACCT-5555','ACTIVE','TX'),
('P-1008','Theta Cardiology','Cardiology','600 Birch St, Houston TX','713-555-0601','ACCT-3333','ACTIVE','TX'),
('P-1009','Iota Heart Center','Cardiology','700 Maple Dr, Dallas TX','214-555-0701','ACCT-2222','ACTIVE','TX'),
('P-1010','Kappa Cardiac Care','Cardiology','800 Walnut Blvd, Austin TX','512-555-0801','ACCT-1111','ACTIVE','TX');

-- Beneficiaries
INSERT INTO FWA_QS.DETECTION.BENEFICIARIES VALUES
('B-2001','John','Smith','1955-03-15','TX','2020-01-01'),
('B-2002','Jane','Doe','1962-07-22','TX','2019-06-15'),
('B-2003','Robert','Johnson','1948-11-30','TX','2021-03-01'),
('B-2004','Maria','Garcia','1970-05-10','TX','2018-09-01'),
('B-2005','James','Wilson','1958-01-20','TX','2022-01-15');

-- Claims: P-1001 and P-1002 have suspiciously high amounts ($7K-$9.5K) and missing prior auth
-- P-1008, P-1009, P-1010 bill normal amounts ($150-$210) — legitimate cardiology baseline
-- C-3015 has IS_FRAUD = NULL — unconfirmed, used to demo the predictive model
INSERT INTO FWA_QS.DETECTION.CLAIMS VALUES
('C-3001','P-1001','B-2001','99214','I10',250.00,'2024-01-15',TRUE,'Office',FALSE),
('C-3002','P-1001','B-2002','99215','I25',8500.00,'2024-01-16',FALSE,'Office',TRUE),
('C-3003','P-1001','B-2003','99215','I10',9200.00,'2024-01-17',FALSE,'Office',TRUE),
('C-3004','P-1002','B-2001','99214','M54',7800.00,'2024-01-18',FALSE,'Office',TRUE),
('C-3005','P-1002','B-2004','99213','I10',350.00,'2024-01-19',TRUE,'Office',FALSE),
('C-3006','P-1003','B-2003','27447','M17',4500.00,'2024-02-01',TRUE,'Hospital',FALSE),
('C-3007','P-1003','B-2005','27447','M17',4700.00,'2024-02-05',TRUE,'Hospital',FALSE),
('C-3008','P-1004','B-2002','99213','I10',180.00,'2024-02-10',TRUE,'Office',FALSE),
('C-3009','P-1004','B-2004','99214','I25',220.00,'2024-02-12',TRUE,'Office',FALSE),
('C-3010','P-1005','B-2005','29881','M23',3800.00,'2024-02-15',TRUE,'Ambulatory',FALSE),
('C-3011','P-1006','B-2001','99213','J06',150.00,'2024-02-20',TRUE,'Office',FALSE),
('C-3012','P-1006','B-2003','99214','J20',200.00,'2024-02-22',TRUE,'Office',FALSE),
('C-3013','P-1001','B-2004','99215','I10',9500.00,'2024-03-01',FALSE,'Office',TRUE),
('C-3014','P-1002','B-2005','99215','I25',8100.00,'2024-03-05',FALSE,'Office',TRUE),
('C-3015','P-1001','B-2005','99215','I10',8800.00,'2024-03-10',FALSE,'Office',NULL),
-- Legitimate low-billing cardiology claims (establish peer baseline)
('C-3016','P-1008','B-2001','99213','I10',175.00,'2024-02-18',TRUE,'Office',FALSE),
('C-3017','P-1008','B-2003','99213','I10',200.00,'2024-02-19',TRUE,'Office',FALSE),
('C-3018','P-1008','B-2004','99214','I25',190.00,'2024-02-20',TRUE,'Office',FALSE),
('C-3019','P-1009','B-2002','99213','I10',160.00,'2024-02-21',TRUE,'Office',FALSE),
('C-3020','P-1009','B-2005','99214','I25',210.00,'2024-02-22',TRUE,'Office',FALSE),
('C-3021','P-1009','B-2001','99213','I10',185.00,'2024-02-23',TRUE,'Office',FALSE),
('C-3022','P-1010','B-2003','99213','I10',165.00,'2024-02-24',TRUE,'Office',FALSE),
('C-3023','P-1010','B-2004','99214','I25',195.00,'2024-02-25',TRUE,'Office',FALSE),
('C-3024','P-1010','B-2005','99213','I10',170.00,'2024-02-26',TRUE,'Office',FALSE);

-- Watch list
INSERT INTO FWA_QS.DETECTION.WATCH_LIST VALUES
('P-1001','Unusually high billing volume flagged by OIG','2023-06-01','OIG'),
('P-1002','Complaints from multiple beneficiaries','2023-09-15','State Medicaid');

-- Document metadata: links uploaded files to claims for document-vs-claim comparison
INSERT INTO FWA_QS.DETECTION.DOCUMENT_METADATA VALUES
('D-5001','C-3002','claim_C3002_invoice.pdf','Invoice','2024-01-20'),
('D-5002','C-3003','claim_C3003_clinical_notes.pdf','Clinical Notes','2024-01-21'),
('D-5003','C-3013','claim_C3013_procedure_report.pdf','Procedure Report','2024-03-05');

-- Audio metadata: links uploaded audio files (hotline calls, whistleblower recordings)
INSERT INTO FWA_QS.DETECTION.AUDIO_METADATA VALUES
('A-6001','hotline_call_20240201.mp3','Fraud Hotline','P-1001','2024-02-01'),
('A-6002','whistleblower_report_20240315.mp3','Whistleblower','P-1002','2024-03-15');
```

> **Verify:** `SELECT COUNT(*) FROM FWA_QS.DETECTION.CLAIMS;` — expect 24 rows.

<!-- ------------------------ -->
## Provider Behavior Profiles (Dynamic Tables)

Duration: 5

Dynamic Tables refresh automatically as new claims arrive — no batch jobs, no ETL scheduler. This profile compares each provider against specialty peers and incorporates watch list status into a composite risk score (0-100).

```sql
-- Dynamic Table: auto-refreshes within 1 hour as new claims arrive
-- Compares each provider's billing against specialty peers and scores risk 0-100
CREATE OR REPLACE DYNAMIC TABLE FWA_QS.DETECTION.PROVIDER_PROFILES
  TARGET_LAG = '1 hour'   -- Snowflake refreshes automatically within this lag
  WAREHOUSE = FWA_WH      -- compute used for incremental refreshes
AS
SELECT
    p.PROVIDER_ID,
    p.PROVIDER_NAME,
    p.SPECIALTY,
    COUNT(c.CLAIM_ID)                                          AS TOTAL_CLAIMS,
    ROUND(AVG(c.CLAIM_AMOUNT), 2)                              AS AVG_CLAIM_AMOUNT,
    ROUND(AVG(c.CLAIM_AMOUNT) / NULLIF(
        AVG(AVG(c.CLAIM_AMOUNT)) OVER (PARTITION BY p.SPECIALTY), 0
    ), 2)                                                      AS PEER_BILLING_RATIO,
    ROUND(SUM(CASE WHEN c.PRIOR_AUTH_FLAG = FALSE THEN 1 ELSE 0 END)::FLOAT
        / NULLIF(COUNT(c.CLAIM_ID), 0), 2)                    AS PRIOR_AUTH_GAP_RATE,
    MAX(CASE WHEN w.PROVIDER_ID IS NOT NULL THEN 1 ELSE 0 END) AS ON_WATCH_LIST,
    -- Composite risk score: peer billing (30) + auth gaps (25) + watch list (45)
    (
      CASE WHEN AVG(c.CLAIM_AMOUNT) / NULLIF(
          AVG(AVG(c.CLAIM_AMOUNT)) OVER (PARTITION BY p.SPECIALTY), 0
      ) > 3 THEN 30 ELSE 0 END
      + CASE WHEN SUM(CASE WHEN c.PRIOR_AUTH_FLAG = FALSE THEN 1 ELSE 0 END)::FLOAT
            / NULLIF(COUNT(c.CLAIM_ID), 0) > 0.3 THEN 25 ELSE 0 END
      + CASE WHEN MAX(CASE WHEN w.PROVIDER_ID IS NOT NULL THEN 1 ELSE 0 END) = 1
            THEN 45 ELSE 0 END
    )                                                          AS RISK_SCORE
FROM FWA_QS.DETECTION.PROVIDERS p
JOIN FWA_QS.DETECTION.CLAIMS c ON p.PROVIDER_ID = c.PROVIDER_ID
LEFT JOIN FWA_QS.DETECTION.WATCH_LIST w ON p.PROVIDER_ID = w.PROVIDER_ID
GROUP BY p.PROVIDER_ID, p.PROVIDER_NAME, p.SPECIALTY;
```

> **Verify:** P-1001 scores 100 (30 peer billing + 25 auth gaps + 45 watch list), P-1002 scores 70 (25 + 45).
```sql
SELECT PROVIDER_ID, PROVIDER_NAME, PEER_BILLING_RATIO, RISK_SCORE
FROM FWA_QS.DETECTION.PROVIDER_PROFILES
ORDER BY RISK_SCORE DESC;
```

<!-- ------------------------ -->
## Fraud Classification (Cortex AI)

Duration: 10

Materialize LLM-driven classification so downstream services can index the results. Each claim is classified into a fraud type with a plain-English explanation.

```sql
-- Materialize LLM results into a table so Cortex Search can index them
-- AI_CLASSIFY: assigns each claim to a fraud category
-- COMPLETE: generates a plain-English explanation for investigators
CREATE OR REPLACE TABLE FWA_QS.DETECTION.FRAUD_CLASSIFICATIONS AS
SELECT
    c.CLAIM_ID,
    c.PROVIDER_ID,
    c.CLAIM_AMOUNT,
    c.PROCEDURE_CODE,
    p.SPECIALTY,
    pp.RISK_SCORE,
    pp.PEER_BILLING_RATIO,
    SNOWFLAKE.CORTEX.AI_CLASSIFY(
        'Healthcare claim — Procedure: ' || c.PROCEDURE_CODE
            || ', Amount: $' || c.CLAIM_AMOUNT::VARCHAR
            || ', Specialty: ' || p.SPECIALTY
            || ', Provider risk score: ' || pp.RISK_SCORE::VARCHAR,
        ['Upcoding','Phantom Billing','Unbundling','Provider Ring','Identity Theft','Legitimate']
    ):"labels"[0]::VARCHAR                                     AS FRAUD_TYPE,
    SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b',
        'You are a healthcare fraud analyst. In 2 sentences, explain why this claim '
        || 'may be fraudulent. Procedure: ' || c.PROCEDURE_CODE
        || ', Amount: $' || c.CLAIM_AMOUNT::VARCHAR
        || ', Peer billing ratio: ' || pp.PEER_BILLING_RATIO::VARCHAR || 'x'
        || ', Prior auth gap rate: ' || pp.PRIOR_AUTH_GAP_RATE::VARCHAR
        || ', On watch list: ' || pp.ON_WATCH_LIST::VARCHAR
    )                                                          AS EXPLANATION
FROM FWA_QS.DETECTION.CLAIMS c
JOIN FWA_QS.DETECTION.PROVIDERS p ON c.PROVIDER_ID = p.PROVIDER_ID
JOIN FWA_QS.DETECTION.PROVIDER_PROFILES pp ON c.PROVIDER_ID = pp.PROVIDER_ID
WHERE pp.RISK_SCORE >= 25;
```

Only claims from providers with RISK_SCORE >= 25 are sent through LLM classification, controlling cost at scale.

> **Verify:**
```sql
SELECT CLAIM_ID, FRAUD_TYPE, LEFT(EXPLANATION, 80) AS EXPLANATION_PREVIEW
FROM FWA_QS.DETECTION.FRAUD_CLASSIFICATIONS;
```

<!-- ------------------------ -->
## Anomaly Detection and Predictive Scoring (Snowflake ML)

Duration: 10

Pure SQL — no Python, no notebooks, no external tools.

### Anomaly Detection

```sql
-- Train an unsupervised anomaly model on claims before March 2024
-- The model learns normal billing patterns from this baseline period
-- LABEL_COLNAME => '' means unsupervised (no pre-labeled anomalies)
CREATE OR REPLACE SNOWFLAKE.ML.ANOMALY_DETECTION FWA_QS.DETECTION.CLAIMS_ANOMALY_MODEL(
    INPUT_DATA => SYSTEM$QUERY_REFERENCE(
        'SELECT CLAIM_DATE, CLAIM_AMOUNT FROM FWA_QS.DETECTION.CLAIMS WHERE CLAIM_DATE < ''2024-03-01'''
    ),
    TIMESTAMP_COLNAME => 'CLAIM_DATE',
    TARGET_COLNAME => 'CLAIM_AMOUNT',
    LABEL_COLNAME => ''
);

-- Run inference on newer claims (must be after training period)
-- Returns IS_ANOMALY flag, prediction interval, and distance from expected range
CALL FWA_QS.DETECTION.CLAIMS_ANOMALY_MODEL!DETECT_ANOMALIES(
    INPUT_DATA => SYSTEM$QUERY_REFERENCE(
        'SELECT CLAIM_DATE, CLAIM_AMOUNT FROM FWA_QS.DETECTION.CLAIMS WHERE CLAIM_DATE >= ''2024-03-01'''
    ),
    TIMESTAMP_COLNAME => 'CLAIM_DATE',
    TARGET_COLNAME => 'CLAIM_AMOUNT'
);
```

### Predictive Fraud Scoring

```sql
-- Feature view: joins claim-level data with provider profile metrics
-- Only includes claims where IS_FRAUD has been confirmed (not NULL)
CREATE OR REPLACE VIEW FWA_QS.DETECTION.TRAINING_FEATURES_V AS
SELECT
    c.CLAIM_ID,
    c.CLAIM_AMOUNT,
    c.PRIOR_AUTH_FLAG,
    pp.PEER_BILLING_RATIO,
    pp.PRIOR_AUTH_GAP_RATE,
    pp.RISK_SCORE,
    pp.ON_WATCH_LIST,
    pp.TOTAL_CLAIMS       AS PROVIDER_TOTAL_CLAIMS,
    c.IS_FRAUD
FROM FWA_QS.DETECTION.CLAIMS c
JOIN FWA_QS.DETECTION.PROVIDER_PROFILES pp ON c.PROVIDER_ID = pp.PROVIDER_ID
WHERE c.IS_FRAUD IS NOT NULL;

-- Train a gradient-boosted classifier to predict fraud probability
-- Snowflake ML automatically handles train/test split, hyperparameters, and feature importance
CREATE OR REPLACE SNOWFLAKE.ML.CLASSIFICATION FWA_QS.DETECTION.FRAUD_PREDICTION_MODEL(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'FWA_QS.DETECTION.TRAINING_FEATURES_V'),
    TARGET_COLNAME => 'IS_FRAUD'
);
```

<!-- ------------------------ -->
## Fraud Ring Detection (Graph Analysis)

Duration: 5

Build edges from shared provider attributes and cluster them. No separate graph database required.

### Build Edges

```sql
-- Build an edge list: two providers are "connected" if they share an address,
-- bank account, or phone number. Self-joins with ID < ID avoid duplicates.
CREATE OR REPLACE TABLE FWA_QS.DETECTION.PROVIDER_EDGES AS
SELECT a.PROVIDER_ID AS PROVIDER_A, b.PROVIDER_ID AS PROVIDER_B,
       'SHARED_ADDRESS' AS CONNECTION_TYPE
FROM FWA_QS.DETECTION.PROVIDERS a
JOIN FWA_QS.DETECTION.PROVIDERS b
    ON a.ADDRESS = b.ADDRESS AND a.PROVIDER_ID < b.PROVIDER_ID
UNION ALL
SELECT a.PROVIDER_ID, b.PROVIDER_ID, 'SHARED_BANK_ACCOUNT'
FROM FWA_QS.DETECTION.PROVIDERS a
JOIN FWA_QS.DETECTION.PROVIDERS b
    ON a.BANK_ACCOUNT = b.BANK_ACCOUNT AND a.PROVIDER_ID < b.PROVIDER_ID
UNION ALL
SELECT a.PROVIDER_ID, b.PROVIDER_ID, 'SHARED_PHONE'
FROM FWA_QS.DETECTION.PROVIDERS a
JOIN FWA_QS.DETECTION.PROVIDERS b
    ON a.PHONE = b.PHONE AND a.PROVIDER_ID < b.PROVIDER_ID;
```

### Cluster Into Rings

```sql
-- Find connected components: assign each provider the minimum reachable PROVIDER_ID
-- Uses a multi-hop approach that handles chains (A-B via address, B-C via bank account)
CREATE OR REPLACE TABLE FWA_QS.DETECTION.FRAUD_RINGS AS
WITH
-- Make edges bidirectional so we can traverse in both directions
edges_both_ways AS (
    SELECT PROVIDER_A AS P1, PROVIDER_B AS P2 FROM FWA_QS.DETECTION.PROVIDER_EDGES
    UNION ALL
    SELECT PROVIDER_B, PROVIDER_A FROM FWA_QS.DETECTION.PROVIDER_EDGES
),
-- Hop 1: for each provider, find their minimum direct neighbor
hop1 AS (
    SELECT P1 AS PROVIDER_ID, MIN(P2) AS MIN_NEIGHBOR
    FROM edges_both_ways
    GROUP BY P1
),
-- Hop 2: follow the neighbor's minimum neighbor (handles A→B→C chains)
hop2 AS (
    SELECT h1.PROVIDER_ID,
           LEAST(h1.MIN_NEIGHBOR, COALESCE(MIN(h2.MIN_NEIGHBOR), h1.MIN_NEIGHBOR)) AS CLUSTER_ID
    FROM hop1 h1
    LEFT JOIN hop1 h2 ON h1.MIN_NEIGHBOR = h2.PROVIDER_ID
    GROUP BY h1.PROVIDER_ID, h1.MIN_NEIGHBOR
)
SELECT PROVIDER_ID, MIN(CLUSTER_ID) AS CLUSTER_ID
FROM hop2
GROUP BY PROVIDER_ID;
```

> **Verify:** P-1001, P-1002, P-1003 share a cluster (address + bank account links).
```sql
SELECT * FROM FWA_QS.DETECTION.FRAUD_RINGS;
```

<!-- ------------------------ -->
## Document and Audio Analysis (Cortex AI)

Duration: 5

### Document Analysis

Parse clinical documents, compare to the associated claim, and flag mismatches:

```sql
-- Upload documents first, then parse and analyze:
-- PUT file:///path/to/doc.pdf @FWA_QS.DETECTION.DOCUMENTS;

-- AI_PARSE_DOCUMENT: extracts text/OCR from PDFs and images on the stage
-- COMPLETE: compares extracted text against claim details to find mismatches
SELECT
    d.DOC_ID,
    d.FILE_NAME,
    d.CLAIM_ID,
    SNOWFLAKE.CORTEX.AI_PARSE_DOCUMENT(
        @FWA_QS.DETECTION.DOCUMENTS, d.FILE_NAME
    ):content::VARCHAR AS EXTRACTED_TEXT,
    SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b',
        'You are a healthcare fraud auditor. Compare this clinical document to the claim details '
        || 'and list any mismatches. Document text: '
        || SNOWFLAKE.CORTEX.AI_PARSE_DOCUMENT(@FWA_QS.DETECTION.DOCUMENTS, d.FILE_NAME):content::VARCHAR
        || ' | Claim: procedure=' || c.PROCEDURE_CODE
        || ', diagnosis=' || c.DIAGNOSIS_CODE
        || ', amount=$' || c.CLAIM_AMOUNT::VARCHAR
    ) AS MISMATCH_ANALYSIS
FROM FWA_QS.DETECTION.DOCUMENT_METADATA d
JOIN FWA_QS.DETECTION.CLAIMS c ON d.CLAIM_ID = c.CLAIM_ID;
```

### Audio Analysis

Transcribe hotline calls or whistleblower reports, summarize, and extract key entities:

```sql
-- Upload audio first, then transcribe and summarize:
-- PUT file:///path/to/call.mp3 @FWA_QS.DETECTION.AUDIO_FILES;

-- AI_TRANSCRIBE: converts speech to text directly from audio files on the stage
-- AI_SUMMARIZE: condenses the transcript into key findings
SELECT
    a.AUDIO_ID,
    a.FILE_NAME,
    a.SOURCE_TYPE,
    SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
        @FWA_QS.DETECTION.AUDIO_FILES, a.FILE_NAME
    ) AS TRANSCRIPTION,
    SNOWFLAKE.CORTEX.AI_SUMMARIZE(
        SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
            @FWA_QS.DETECTION.AUDIO_FILES, a.FILE_NAME
        )
    ) AS SUMMARY
FROM FWA_QS.DETECTION.AUDIO_METADATA a;
```

> **In production**, Snowflake Cortex AI provides a full suite of functions for audio and multilingual workflows: AI_TRANSCRIBE, AI_TRANSLATE, AI_SUMMARIZE, AI_CLASSIFY, AI_EXTRACT, AI_COMPLETE, AI_SENTIMENT, AI_PARSE_DOCUMENT. These run inside Snowflake — no external API calls, no data movement. Combine them to build end-to-end pipelines, e.g. AI_TRANSCRIBE → AI_TRANSLATE → AI_SUMMARIZE for multilingual hotline calls.

<!-- ------------------------ -->
## Investigation Agent (Cortex Agent)

Duration: 15

### Cortex Search Services

Create search indexes over fraud explanations, documents, audio, and fraud ring clusters:

```sql
-- Search service over LLM-generated fraud explanations
-- Investigators can search by fraud type, provider, or free text
CREATE OR REPLACE CORTEX SEARCH SERVICE FWA_QS.DETECTION.FRAUD_EXPLANATIONS_SEARCH
  ON EXPLANATION
  WAREHOUSE = FWA_WH
  TARGET_LAG = '1 hour'
AS (
    SELECT CLAIM_ID, PROVIDER_ID, FRAUD_TYPE, EXPLANATION, CLAIM_AMOUNT, RISK_SCORE
    FROM FWA_QS.DETECTION.FRAUD_CLASSIFICATIONS
);

-- Search service over parsed document text (clinical notes, invoices)
CREATE OR REPLACE CORTEX SEARCH SERVICE FWA_QS.DETECTION.DOCUMENT_SEARCH
  ON EXTRACTED_TEXT
  WAREHOUSE = FWA_WH
  TARGET_LAG = '1 hour'
AS (
    SELECT
        d.DOC_ID, d.CLAIM_ID, d.FILE_NAME, d.DOC_TYPE,
        SNOWFLAKE.CORTEX.AI_PARSE_DOCUMENT(
            @FWA_QS.DETECTION.DOCUMENTS, d.FILE_NAME
        ):content::VARCHAR AS EXTRACTED_TEXT
    FROM FWA_QS.DETECTION.DOCUMENT_METADATA d
);

-- Search service over transcribed audio (hotline calls, whistleblower reports)
CREATE OR REPLACE CORTEX SEARCH SERVICE FWA_QS.DETECTION.AUDIO_SEARCH
  ON TRANSCRIPTION_TEXT
  WAREHOUSE = FWA_WH
  TARGET_LAG = '1 hour'
AS (
    SELECT
        a.AUDIO_ID, a.FILE_NAME, a.SOURCE_TYPE, a.RELATED_PROVIDER,
        SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
            @FWA_QS.DETECTION.AUDIO_FILES, a.FILE_NAME
        )::VARCHAR AS TRANSCRIPTION_TEXT
    FROM FWA_QS.DETECTION.AUDIO_METADATA a
);

-- Search service over fraud ring clusters — find providers by ring membership
CREATE OR REPLACE CORTEX SEARCH SERVICE FWA_QS.DETECTION.CLUSTER_SEARCH
  ON CLUSTER_DETAIL
  WAREHOUSE = FWA_WH
  TARGET_LAG = '1 hour'
AS (
    SELECT
        fr.CLUSTER_ID,
        fr.PROVIDER_ID,
        p.PROVIDER_NAME,
        pp.RISK_SCORE,
        'Cluster ' || fr.CLUSTER_ID || ': ' || p.PROVIDER_NAME
            || ' (risk=' || pp.RISK_SCORE::VARCHAR || ')' AS CLUSTER_DETAIL
    FROM FWA_QS.DETECTION.FRAUD_RINGS fr
    JOIN FWA_QS.DETECTION.PROVIDERS p ON fr.PROVIDER_ID = p.PROVIDER_ID
    JOIN FWA_QS.DETECTION.PROVIDER_PROFILES pp ON fr.PROVIDER_ID = pp.PROVIDER_ID
);
```

### Semantic Model

Save the following as `fwa_semantic_model.yaml` and upload to the stage:

```yaml
# fwa_semantic_model.yaml
# NOTE: base_table must use nested database/schema/table format
# All dimensions require data_type; use facts (not measures) for numeric columns
name: FWA_Investigation_Model
tables:
  - name: CLAIMS
    base_table:
      database: FWA_QS
      schema: DETECTION
      table: CLAIMS
    dimensions:
      - name: CLAIM_ID
        expr: CLAIM_ID
        data_type: TEXT
      - name: PROVIDER_ID
        expr: PROVIDER_ID
        data_type: TEXT
      - name: BENEFICIARY_ID
        expr: BENEFICIARY_ID
        data_type: TEXT
      - name: PROCEDURE_CODE
        expr: PROCEDURE_CODE
        data_type: TEXT
    time_dimensions:
      - name: CLAIM_DATE
        expr: CLAIM_DATE
        data_type: DATE
    facts:
      - name: CLAIM_AMOUNT
        expr: CLAIM_AMOUNT
        data_type: NUMBER

  - name: PROVIDER_PROFILES
    base_table:
      database: FWA_QS
      schema: DETECTION
      table: PROVIDER_PROFILES
    dimensions:
      - name: PROVIDER_ID
        expr: PROVIDER_ID
        data_type: TEXT
      - name: PROVIDER_NAME
        expr: PROVIDER_NAME
        data_type: TEXT
      - name: SPECIALTY
        expr: SPECIALTY
        data_type: TEXT
    facts:
      - name: RISK_SCORE
        expr: RISK_SCORE
        data_type: NUMBER
      - name: AVG_CLAIM_AMOUNT
        expr: AVG_CLAIM_AMOUNT
        data_type: NUMBER
      - name: TOTAL_CLAIMS
        expr: TOTAL_CLAIMS
        data_type: NUMBER

  - name: FRAUD_CLASSIFICATIONS
    base_table:
      database: FWA_QS
      schema: DETECTION
      table: FRAUD_CLASSIFICATIONS
    dimensions:
      - name: CLAIM_ID
        expr: CLAIM_ID
        data_type: TEXT
      - name: FRAUD_TYPE
        expr: FRAUD_TYPE
        data_type: TEXT
    facts:
      - name: CLAIM_AMOUNT
        expr: CLAIM_AMOUNT
        data_type: NUMBER
      - name: RISK_SCORE
        expr: RISK_SCORE
        data_type: NUMBER
```

### Create Analyst Tool and Agent

```sql
-- Stage to hold the semantic model YAML file
CREATE STAGE IF NOT EXISTS FWA_QS.DETECTION.SEMANTIC_MODELS
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
-- PUT file:///path/to/fwa_semantic_model.yaml @FWA_QS.DETECTION.SEMANTIC_MODELS;

-- Create a Cortex Agent using CREATE AGENT with a YAML specification
-- The agent orchestrates: an Analyst tool (structured SQL via semantic model)
-- and Cortex Search services (unstructured text search)
-- execution_environment specifies the warehouse for running analyst SQL queries
CREATE OR REPLACE AGENT FWA_QS.DETECTION.INVESTIGATION_AGENT
  FROM SPECIFICATION
  $$
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "FWA_ANALYST"
        description: "Answers structured SQL questions about claims, providers, risk scores, and fraud classifications"
    - tool_spec:
        type: "cortex_search"
        name: "FRAUD_EXPLANATIONS"
        description: "Searches LLM-generated fraud explanations for claims"
    - tool_spec:
        type: "cortex_search"
        name: "CLUSTER_SEARCH"
        description: "Searches fraud ring cluster details and connected providers"

  tool_resources:
    FWA_ANALYST:
      semantic_model_file: "@FWA_QS.DETECTION.SEMANTIC_MODELS/fwa_semantic_model.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "FWA_WH"
    FRAUD_EXPLANATIONS:
      search_service: "FWA_QS.DETECTION.FRAUD_EXPLANATIONS_SEARCH"
    CLUSTER_SEARCH:
      search_service: "FWA_QS.DETECTION.CLUSTER_SEARCH"
  $$;
```

### Test the Agent

```sql
-- Test 1: routes to analyst tool (structured SQL query against profiles + classifications)
-- DATA_AGENT_RUN takes the agent name, a JSON messages payload, and TRUE to wait for completion
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'FWA_QS.DETECTION.INVESTIGATION_AGENT',
    $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Which providers have a risk score above 50 and what fraud types are they flagged for?"}]}]}$$,
    TRUE
);

-- Test 2: routes to cluster search service (unstructured ring data)
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'FWA_QS.DETECTION.INVESTIGATION_AGENT',
    $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Show me fraud ring clusters and explain why cluster P-1001 was flagged."}]}]}$$,
    TRUE
);

-- Test 3: routes to fraud explanations search service
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'FWA_QS.DETECTION.INVESTIGATION_AGENT',
    $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Why were claims from Provider P-1001 flagged as upcoding?"}]}]}$$,
    TRUE
);
```

<!-- ------------------------ -->
## Streamlit Investigator Application

Duration: 10

Create a Streamlit in Snowflake app. Create a new Streamlit app in Snowsight (Projects > Streamlit) and paste the code below.

### environment.yml

```yaml
name: fwa_app
channels:
  - snowflake
dependencies:
  - snowflake-snowpark-python
  - streamlit
```

### app.py

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="FWA Investigation Platform", layout="wide")
st.title("Fraud, Waste & Abuse Investigation Platform")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Provider Profiles", "Fraud Classifications", "Anomaly Detection",
    "Fraud Rings", "Document & Audio", "Investigation Agent"
])

# --- Tab 1: Provider Profiles ---
with tab1:
    st.header("Provider Behavior Profiles")
    risk_threshold = st.slider("Minimum Risk Score", 0, 100, 25)
    profiles = session.sql(f"""
        SELECT PROVIDER_ID, PROVIDER_NAME, SPECIALTY, TOTAL_CLAIMS,
               AVG_CLAIM_AMOUNT, PEER_BILLING_RATIO, PRIOR_AUTH_GAP_RATE,
               ON_WATCH_LIST, RISK_SCORE
        FROM FWA_QS.DETECTION.PROVIDER_PROFILES
        WHERE RISK_SCORE >= {risk_threshold}
        ORDER BY RISK_SCORE DESC
    """).to_pandas()
    st.dataframe(profiles, use_container_width=True)

# --- Tab 2: Fraud Classifications ---
with tab2:
    st.header("LLM Fraud Classifications")
    classifications = session.sql("""
        SELECT CLAIM_ID, PROVIDER_ID, CLAIM_AMOUNT, FRAUD_TYPE,
               LEFT(EXPLANATION, 300) AS EXPLANATION, RISK_SCORE
        FROM FWA_QS.DETECTION.FRAUD_CLASSIFICATIONS
        ORDER BY RISK_SCORE DESC
    """).to_pandas()
    fraud_filter = st.multiselect("Filter by Fraud Type",
        classifications["FRAUD_TYPE"].unique().tolist(),
        default=classifications["FRAUD_TYPE"].unique().tolist())
    st.dataframe(
        classifications[classifications["FRAUD_TYPE"].isin(fraud_filter)],
        use_container_width=True
    )

# --- Tab 3: Anomaly Detection ---
with tab3:
    st.header("Claim Amount Anomalies")
    st.info("Anomaly detection scores claims from March 2024 onward against the pre-March baseline.")
    try:
        anomalies = session.sql("""
            SELECT * FROM TABLE(FWA_QS.DETECTION.CLAIMS_ANOMALY_MODEL!DETECT_ANOMALIES(
                INPUT_DATA => SYSTEM$QUERY_REFERENCE(
                    'SELECT CLAIM_DATE, CLAIM_AMOUNT FROM FWA_QS.DETECTION.CLAIMS WHERE CLAIM_DATE >= ''2024-03-01'''
                ),
                TIMESTAMP_COLNAME => 'CLAIM_DATE',
                TARGET_COLNAME => 'CLAIM_AMOUNT'
            ))
            ORDER BY TS DESC
        """).to_pandas()
        st.dataframe(anomalies, use_container_width=True)
    except Exception as e:
        st.error(f"Anomaly detection error: {e}")

# --- Tab 4: Fraud Rings ---
with tab4:
    st.header("Fraud Ring Clusters")
    rings = session.sql("""
        SELECT fr.CLUSTER_ID, fr.PROVIDER_ID, p.PROVIDER_NAME,
               p.ADDRESS, p.BANK_ACCOUNT, pp.RISK_SCORE
        FROM FWA_QS.DETECTION.FRAUD_RINGS fr
        JOIN FWA_QS.DETECTION.PROVIDERS p ON fr.PROVIDER_ID = p.PROVIDER_ID
        JOIN FWA_QS.DETECTION.PROVIDER_PROFILES pp ON fr.PROVIDER_ID = pp.PROVIDER_ID
        ORDER BY fr.CLUSTER_ID, pp.RISK_SCORE DESC
    """).to_pandas()
    st.dataframe(rings, use_container_width=True)

    edges = session.sql("""
        SELECT PROVIDER_A, PROVIDER_B, CONNECTION_TYPE
        FROM FWA_QS.DETECTION.PROVIDER_EDGES
    """).to_pandas()
    st.subheader("Connection Edges")
    st.dataframe(edges, use_container_width=True)

# --- Tab 5: Document & Audio ---
with tab5:
    st.header("Document & Audio Analysis")
    st.subheader("Documents")
    st.info("Upload files to @FWA_QS.DETECTION.DOCUMENTS and populate DOCUMENT_METADATA to see results.")
    st.subheader("Audio")
    st.info("Upload files to @FWA_QS.DETECTION.AUDIO_FILES and populate AUDIO_METADATA to see results.")

# --- Tab 6: Investigation Agent ---
with tab6:
    st.header("Ask the Investigation Agent")
    user_question = st.text_input("Ask a question about claims, providers, fraud rings, or documents:")
    if user_question:
        with st.spinner("Agent is investigating..."):
            import json
            escaped_q = user_question.replace('"', '\\"')
            result = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                    'FWA_QS.DETECTION.INVESTIGATION_AGENT',
                    $${{"messages": [{{"role": "user", "content": [{{"type": "text", "text": "{escaped_q}"}}]}}]}}$$,
                    TRUE
                ) AS RESPONSE
            """).to_pandas()
            resp = json.loads(result["RESPONSE"].iloc[0])
            for item in resp.get("content", []):
                if item.get("type") == "text":
                    st.markdown(item["text"])
```

<!-- ------------------------ -->
## Security Best Practices

Duration: 5

```sql
-- Least-privilege roles: avoid running production workloads as ACCOUNTADMIN
CREATE ROLE IF NOT EXISTS FWA_ADMIN;          -- manages the platform
CREATE ROLE IF NOT EXISTS FWA_INVESTIGATOR;   -- reviews and acts on flagged claims

-- FWA_ADMIN: full read/write on all FWA objects
GRANT USAGE ON DATABASE FWA_QS TO ROLE FWA_ADMIN;
GRANT USAGE ON SCHEMA FWA_QS.DETECTION TO ROLE FWA_ADMIN;
GRANT ALL ON ALL TABLES IN SCHEMA FWA_QS.DETECTION TO ROLE FWA_ADMIN;
GRANT USAGE ON WAREHOUSE FWA_WH TO ROLE FWA_ADMIN;

-- FWA_INVESTIGATOR: read-only on results, agent access
GRANT USAGE ON DATABASE FWA_QS TO ROLE FWA_INVESTIGATOR;
GRANT USAGE ON SCHEMA FWA_QS.DETECTION TO ROLE FWA_INVESTIGATOR;
GRANT SELECT ON FWA_QS.DETECTION.PROVIDER_PROFILES TO ROLE FWA_INVESTIGATOR;
GRANT SELECT ON FWA_QS.DETECTION.FRAUD_CLASSIFICATIONS TO ROLE FWA_INVESTIGATOR;
GRANT SELECT ON FWA_QS.DETECTION.FRAUD_RINGS TO ROLE FWA_INVESTIGATOR;
GRANT USAGE ON WAREHOUSE FWA_WH TO ROLE FWA_INVESTIGATOR;

-- Dynamic data masking: protects PHI/PII at query time without duplicating data
-- Investigators see '***MASKED***' for patient names; admins see real values
CREATE OR REPLACE MASKING POLICY FWA_QS.DETECTION.NAME_MASK AS (val STRING)
  RETURNS STRING ->
    CASE WHEN CURRENT_ROLE() IN ('FWA_ADMIN','ACCOUNTADMIN') THEN val
         ELSE '***MASKED***' END;

ALTER TABLE FWA_QS.DETECTION.BENEFICIARIES
  MODIFY COLUMN FIRST_NAME SET MASKING POLICY FWA_QS.DETECTION.NAME_MASK;
ALTER TABLE FWA_QS.DETECTION.BENEFICIARIES
  MODIFY COLUMN LAST_NAME SET MASKING POLICY FWA_QS.DETECTION.NAME_MASK;
```

<!-- ------------------------ -->
## Operating, Demoing, and Case Management

Duration: 10

### Architecture Mapping

| Phase | Steps | Key Snowflake Features |
|-------|-------|----------------------|
| **1. Ingest & Contextualize** | Steps 2-4 | Tables, Stages, Dynamic Tables |
| **2. Detect & Score** | Steps 5-7 | Cortex AI, Snowflake ML, SQL Graph Analysis |
| **3. Analyze & Evidence** | Steps 8-9 | AI_PARSE_DOCUMENT, AI_TRANSCRIBE, Cortex Agent |
| **4. Decide & Act** | Steps 10-12 | Streamlit, RBAC, Masking, Case Management |

### Case Management and Feedback Loop

Investigators can confirm, reject, or escalate flagged claims, and their decisions feed back into model retraining.

```sql
-- Tracks investigator decisions: confirm fraud, reject as false positive, or escalate
-- Each row is an auditable action tied to a claim and the investigator who made it
CREATE OR REPLACE TABLE FWA_QS.DETECTION.CASE_ACTIONS (
    CASE_ID         VARCHAR(10) DEFAULT 'CA-' || SEQ4()::VARCHAR,
    CLAIM_ID        VARCHAR(10),
    PROVIDER_ID     VARCHAR(10),
    ACTION          VARCHAR(20),   -- CONFIRMED_FRAUD, FALSE_POSITIVE, ESCALATED, PENDING
    INVESTIGATOR    VARCHAR(100) DEFAULT CURRENT_USER(),
    ACTION_DATE     TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    NOTES           VARCHAR(500),
    RECOVERY_AMOUNT NUMBER(12,2) DEFAULT NULL
);

-- Grant investigators write access to this table
GRANT INSERT, UPDATE ON FWA_QS.DETECTION.CASE_ACTIONS TO ROLE FWA_INVESTIGATOR;
```

### Automated Retrain Trigger

```sql
-- Stream captures change data (inserts/updates) on CASE_ACTIONS for the task trigger
CREATE OR REPLACE STREAM FWA_QS.DETECTION.CASE_ACTIONS_STREAM
  ON TABLE FWA_QS.DETECTION.CASE_ACTIONS;

-- Automated retrain: Snowflake Task checks the stream weekly for new investigator decisions
-- Only fires if new case actions exist (SYSTEM$STREAM_HAS_DATA), avoiding unnecessary retrains
CREATE OR REPLACE TASK FWA_QS.DETECTION.RETRAIN_ON_NEW_LABELS
  WAREHOUSE = FWA_WH
  SCHEDULE = 'USING CRON 0 2 * * 0 America/New_York'  -- weekly Sunday 2 AM
  WHEN SYSTEM$STREAM_HAS_DATA('FWA_QS.DETECTION.CASE_ACTIONS_STREAM')
AS
  CREATE OR REPLACE SNOWFLAKE.ML.CLASSIFICATION FWA_QS.DETECTION.FRAUD_PREDICTION_MODEL(
      INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'FWA_QS.DETECTION.TRAINING_FEATURES_V'),
      TARGET_COLNAME => 'IS_FRAUD'
  );

-- Resume the task so it starts running on schedule
ALTER TASK FWA_QS.DETECTION.RETRAIN_ON_NEW_LABELS RESUME;
```

This completes the cycle: claims flow in (Phase 1) → get detected and scored (Phase 2) → investigators analyze evidence (Phase 3) → they decide and act, and those decisions improve the next round of detection (Phase 4 → back to Phase 2).

<!-- ------------------------ -->
## Conclusion and Resources

Duration: 2

Congratulations! You have built a complete Fraud, Waste, and Abuse detection platform on Snowflake — from data ingestion through ML scoring, LLM classification, graph-based ring detection, document/audio analysis, a natural-language investigation agent, and an investigator UI with case management.

### What You Learned
- How Dynamic Tables replace batch ETL with continuously refreshing provider profiles
- How Cortex AI (AI_CLASSIFY, COMPLETE) classifies fraud with plain-English explanations
- How Snowflake ML trains anomaly detection and classification models in pure SQL
- How SQL graph analysis detects fraud rings without an external graph database
- How Cortex AI functions parse documents and transcribe audio for evidence
- How Cortex Agents orchestrate structured and unstructured queries in plain English
- How Streamlit in Snowflake delivers an investigator application
- How RBAC, masking policies, and case management close the decide-and-act loop

### Summary

| Capability | Snowflake Feature | Step |
|---|---|---|
| Data foundation | Tables, Stages | 2-3 |
| Real-time profiles | Dynamic Tables | 4 |
| Fraud classification | Cortex AI (AI_CLASSIFY, COMPLETE) | 5 |
| Anomaly detection | Snowflake ML Anomaly Detection | 6 |
| Predictive scoring | Snowflake ML Classification | 6 |
| Fraud ring mapping | SQL graph analysis | 7 |
| Document analysis | Cortex AI (AI_PARSE_DOCUMENT, COMPLETE) | 8 |
| Audio analysis | Cortex AI (AI_TRANSCRIBE, AI_SUMMARIZE) | 8 |
| Natural-language investigation | Cortex Agent + Cortex Search + Cortex Analyst | 9 |
| Investigator UI | Streamlit in Snowflake | 10 |
| Data protection | Roles, Masking Policies | 11 |
| Case management | Tables, Streams, Tasks | 12 |

### Related Resources
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Cortex AI LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Snowflake ML](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

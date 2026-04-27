author: Rahul Reddy, Sreedhar Bolneni, Jeevan Rag, Cameron Shimmin
id: powering-ai-ready-data-products-by-unpacking-complex-hl7-data-using-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/cortex-ai
language: en
summary: Build a unified healthcare intelligence platform that transforms HL7 v2.7 cancer pathology messages into AI-ready data products using Snowflake Cortex AI, OpenFlow, Semantic Views, and Snowflake Intelligence Agents.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork_repo_link: https://github.com/Snowflake-Labs/sfguide-powering-AI-Ready-Data-Products-by-unpacking-complex-HL7-data-using-Snowflake

# Powering AI-Ready Data Products by Unpacking Complex HL7 Data Using Snowflake
<!-- ------------------------ -->
## Overview

This guide walks you through building a **Unified Healthcare Intelligence Platform** that combines Population Health Analytics with Cancer Pathology Intelligence, all powered by Snowflake Cortex AI.

You will ingest HL7 v2.7 cancer pathology messages (optionally via OpenFlow real-time streaming), parse them through a Bronze → Silver → Gold pipeline, extract 20+ structured clinical fields using Cortex AI, and query the results through a unified Snowflake Intelligence Agent.

### What You'll Learn
- How to parse complex HL7 v2.7 messages into structured clinical data using a Bronze/Silver/Gold pipeline
- How to use Cortex AI (Mistral Large 2) to extract 20+ structured fields from unstructured pathology reports
- How to build a Semantic View for healthcare analytics with Cortex Analyst
- How to create Cortex Search Services for semantic search over pathology reports, medical transcripts, and conditions
- How to deploy a unified Snowflake Intelligence Agent with 4 tools (Cortex Analyst + 3 Cortex Search)

### What You'll Build
- A complete HL7 pathology data pipeline (Bronze → Silver → Gold)
- AI-extracted structured pathology fields (TNM staging, molecular markers: MSI, KRAS, BRAF, HER2, ER, PR)
- A Semantic View spanning patients, encounters, conditions, and cancer pathology
- 3 Cortex Search Services (pathology reports, medical transcripts, conditions)
- A unified Snowflake Intelligence Agent for natural language healthcare queries

> **Note:** This demo cannot be run in a Snowflake trial account. Trial accounts do not support creating SPCS (Snowpark Container Services) deployments, which are required for OpenFlow ingestion.

<!-- ------------------------ -->
## Setup Infrastructure

### Clone the Repository

Clone or download the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-powering-AI-Ready-Data-Products-by-unpacking-complex-HL7-data-using-Snowflake):

```bash
git clone https://github.com/Snowflake-Labs/sfguide-powering-AI-Ready-Data-Products-by-unpacking-complex-HL7-data-using-Snowflake.git
```

### Run Infrastructure Setup

Open a Snowflake SQL worksheet and execute the contents of `scripts/01_setup_infrastructure.sql`.

This script creates the following objects:

| Object | Name |
|--------|------|
| Database | `HL7_PATHOLOGY_AI` |
| Schemas | `POPULATION_HEALTH`, `CANCER_PATHOLOGY`, `ANALYTICS`, `STAGING` |
| Warehouse | `HL7_PATHOLOGY_WH` (X-Small) |
| Role | `HEALTHCARE_ANALYST_ROLE` |
| Stage | `STAGING.DATA_STAGE` |
| (Optional) OpenFlow | `OPENFLOW_DB`, `OPENFLOW_ADMIN` role, compute pool |

**Note:** The script must be run with `ACCOUNTADMIN` role. Subsequent scripts use the `HEALTHCARE_ANALYST_ROLE`.

**Verify:**

```sql
SHOW SCHEMAS IN DATABASE HL7_PATHOLOGY_AI;
```

You should see: `POPULATION_HEALTH`, `CANCER_PATHOLOGY`, `ANALYTICS`, `STAGING`, and `PUBLIC`.

<!-- ------------------------ -->
## Create Tables and Procedures

Execute the contents of `scripts/02_create_tables.sql`.

This creates all tables across both schemas and the HL7 parsing stored procedures:

**Population Health Tables:**
- `PATIENTS` — Demographics, location, healthcare costs
- `ENCOUNTERS` — Visits, costs, reasons
- `CONDITIONS` — Diagnoses
- `MEDICAL_TRANSCRIPTS_RAW` — Clinical notes

**Cancer Pathology Tables (Bronze → Silver → Gold):**
- `LANDING_HL7_MESSAGES` — Raw HL7 JSON (Bronze)
- `SILVER_MSH_SEGMENTS`, `SILVER_PID_SEGMENTS`, `SILVER_OBR_SEGMENTS`, `SILVER_OBX_SEGMENTS` — Parsed segments (Silver)
- `SILVER_PID_NAME_EXPANDED`, `SILVER_OBX_IDENTIFIER_EXPANDED` — Expanded fields
- `GOLD_CANCER_PATHOLOGY_REPORTS` — AI-enriched reports with 20+ structured fields (Gold)

**Stored Procedures:**
- `PARSE_HL7_MSH_SEGMENTS()`, `PARSE_HL7_PID_SEGMENTS()`, `PARSE_HL7_OBX_SEGMENTS()`, `PARSE_HL7_OBR_SEGMENTS()`
- `EXPAND_PID_NAMES()`, `EXPAND_OBX_IDENTIFIERS()`
- `BUILD_GOLD_PATHOLOGY_REPORTS()`
- `EXTRACT_PATHOLOGY_FIELDS_WITH_CLAUDE()` — AI extraction using Mistral Large 2
- `RUN_HL7_PATHOLOGY_PIPELINE()` — Master orchestration procedure

**Verify:**

```sql
SHOW TABLES IN SCHEMA HL7_PATHOLOGY_AI.POPULATION_HEALTH;
SHOW TABLES IN SCHEMA HL7_PATHOLOGY_AI.CANCER_PATHOLOGY;
```

<!-- ------------------------ -->
## Upload and Load Data

### Upload CSV Files to Stage

Upload all CSV files from the `data/csv/` directory to the `DATA_STAGE` stage.

**Option A: Using Snowsight UI**

1. Navigate to **Data > Databases > HL7_PATHOLOGY_AI > STAGING**
2. Click on the `DATA_STAGE` stage
3. Click **+ Files** and upload:
   - `PATIENTS_SMALL.csv`
   - `ENCOUNTERS_SMALL.csv`
   - `CONDITIONS_SMALL.csv`
   - `medical_transcripts.csv`

**Option B: Using SnowSQL**

```bash
snowsql -a <account> -u <user> -q "PUT file:///path/to/data/csv/*.csv @HL7_PATHOLOGY_AI.STAGING.DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
```

### Load Data into Tables

Execute the contents of `scripts/03_load_data.sql`.

This loads Population Health data (patients, encounters, conditions) and medical transcripts from the stage into the tables.

**Verify:**

```sql
SELECT 'PATIENTS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM POPULATION_HEALTH.PATIENTS
UNION ALL SELECT 'ENCOUNTERS', COUNT(*) FROM POPULATION_HEALTH.ENCOUNTERS
UNION ALL SELECT 'CONDITIONS', COUNT(*) FROM POPULATION_HEALTH.CONDITIONS;
```

<!-- ------------------------ -->
## Load HL7 Data — Choose Your Path

At this point, choose **one** of the following methods to load HL7 pathology messages:

| Path | Time | Best For |
|------|------|----------|
| **Option A: OpenFlow** | ~15 min | Learning real-time HL7 ingestion with OpenFlow |
| **Option B: Batch** | ~5 min | Quick setup, no OpenFlow experience needed |

Both paths load data into the same `LANDING_HL7_MESSAGES` table.

### Option A: OpenFlow Ingestion (15 minutes)

Use this path to learn OpenFlow by setting up a NiFi-based ingestion pipeline with a custom HL7 parser processor.

#### Step 1: Create OpenFlow Deployment

1. In Snowsight, navigate to **Data** → **Ingestion** → **OpenFlow**
2. Click **Launch OpenFlow** → **Deployments** tab → **+ Create a deployment**
3. Configure:
   - **Type**: Snowflake
   - **Name**: `HL7_PATHOLOGY_DEPLOYMENT`
4. Wait for status to become **Active** (~3-5 minutes)

#### Step 2: Create OpenFlow Runtime

1. Click **Runtimes** tab → **+ Create Runtime**
2. Configure:
   - **Deployment**: `HL7_PATHOLOGY_DEPLOYMENT`
   - **Name**: `HL7_PATHOLOGY_RUNTIME`
   - **Node Type**: Medium, Min: 1, Max: 3
   - **Runtime Role**: `HEALTHCARE_ANALYST_ROLE`
3. Wait for status to become **Active** (~3 minutes)

#### Step 3: Upload Custom HL7 NAR File

1. Click on `HL7_PATHOLOGY_RUNTIME` to open the NiFi Canvas
2. Click your username → **Controller Settings** → **Local Extensions** tab
3. Click **+** and upload: `openflow/hl7_processors-0.2.0.nar`
4. Verify by dragging a Processor onto canvas and searching for `ParseHL7Messages`

#### Step 4: Import and Configure Flow

1. Drag **Create Process Group** onto canvas
2. Upload `openflow/Openflow-HL7-Flow.json`
3. Right-click the process group → **Controller Services** → Verify `SnowflakeConnectionService` settings:
   - Database: `HL7_PATHOLOGY_AI`
   - Schema: `CANCER_PATHOLOGY`
   - Warehouse: `HL7_PATHOLOGY_WH`
   - Role: `HEALTHCARE_ANALYST_ROLE`
4. Right-click → **Enable all controller services** → **Enable**

#### Step 5: Start Flow and Ingest

1. Right-click canvas → **Start**
2. Verify:

```sql
SELECT COUNT(*) AS MESSAGE_COUNT FROM CANCER_PATHOLOGY.LANDING_HL7_MESSAGES;
-- Expected: 28 records
```

> Once you see the 28 records in your database, go back into the runtime, right-click the canvas, and select **Stop** to stop the processor.

### Option B: Batch Ingestion (5 minutes)

Load the pre-generated HL7 messages directly:

#### Upload HL7 JSON to Stage

Upload `data/hl7_messages/synthea_pathology_messages.json` to `@HL7_PATHOLOGY_AI.STAGING.DATA_STAGE`.

#### Load HL7 Messages

Execute the contents of `data/hl7_messages/load_hl7_messages.sql`.

**Verify:**

```sql
SELECT COUNT(*) FROM CANCER_PATHOLOGY.LANDING_HL7_MESSAGES;
```

<!-- ------------------------ -->
## Run HL7 Pathology Pipeline

Execute the contents of `scripts/04_run_pipeline.sql`.

This calls the master orchestration procedure `RUN_HL7_PATHOLOGY_PIPELINE()` which runs 8 steps:

1. **Parse MSH Segments** — Message headers (sender, receiver, timestamps)
2. **Parse PID Segments** — Patient demographics linked to Synthea IDs
3. **Parse OBX Segments** — Observation results containing pathology report text
4. **Parse OBR Segments** — Order/request details
5. **Expand Patient Names** — Split HL7 name components into readable format
6. **Expand OBX Identifiers** — Classify observation types (Final Diagnosis, Key Findings, etc.)
7. **Build Gold Reports** — Join all segments into unified pathology reports
8. **AI Extraction** — Use Cortex AI (Mistral Large 2) to extract structured fields:
   - Tumor site, size, histologic type/grade
   - TNM staging, AJCC stage group
   - Lymph node counts
   - Margin status, perineural/lymphovascular invasion
   - Molecular markers: MSI, KRAS, BRAF, HER2, ER, PR

**Verify:**

```sql
SELECT 
    REPORT_ID,
    PATIENT_FULL_NAME,
    TUMOR_SITE,
    HISTOLOGIC_TYPE,
    AJCC_STAGE_GROUP,
    MSI_STATUS,
    KRAS_STATUS,
    DATA_QUALITY_SCORE
FROM CANCER_PATHOLOGY.GOLD_CANCER_PATHOLOGY_REPORTS
LIMIT 10;
```

<!-- ------------------------ -->
## Create Analytics Layer

Execute the contents of `scripts/05_setup_analytics.sql`.

This creates:

### Semantic View

The `HL7_PATHOLOGY_SEMANTIC_VIEW` provides a unified semantic model across 4 tables:

| Table | Synonyms | Key Fields |
|-------|----------|------------|
| `PATIENTS` | patients, members | Demographics, healthcare costs, income |
| `ENCOUNTERS` | visits, appointments | Visit type, costs, reasons |
| `CONDITIONS` | diagnoses, diseases | Medical conditions, SNOMED codes |
| `GOLD_CANCER_PATHOLOGY_REPORTS` | pathology, cancer reports | Staging, molecular markers, findings |

The view includes relationships, facts (numeric measures), dimensions (categorical fields), metrics (aggregations), and AI SQL generation instructions for optimal query behavior.

### Cortex Search Services

| Service | Searches Over | Use Case |
|---------|---------------|----------|
| `PATHOLOGY_REPORT_SEARCH` | Final diagnoses and pathology findings | Find specific cancer types, staging, molecular markers |
| `MEDICAL_TRANSCRIPT_SEARCH` | Clinical notes and discharge summaries | Search clinical documentation |
| `CONDITION_SEARCH` | Patient conditions and diagnoses | Find patients with specific conditions |

**Verify:**

```sql
USE SCHEMA ANALYTICS;
DESCRIBE SEMANTIC VIEW HL7_PATHOLOGY_SEMANTIC_VIEW;
SHOW CORTEX SEARCH SERVICES IN SCHEMA ANALYTICS;
```

<!-- ------------------------ -->
## Create Intelligence Agent

Execute the contents of `scripts/06_setup_agent.sql`.

This creates the `HL7_PATHOLOGY_AGENT` — a unified Snowflake Intelligence Agent with 4 tools:

| Tool | Type | Description |
|------|------|-------------|
| `healthcare_analytics` | Cortex Analyst (text-to-SQL) | Structured queries on patients, encounters, conditions, pathology |
| `search_pathology_reports` | Cortex Search | Semantic search over cancer diagnoses and findings |
| `search_conditions` | Cortex Search | Search patient medical conditions |
| `search_medical_transcripts` | Cortex Search | Search clinical notes and transcripts |

The agent uses Claude 3.5 Sonnet for orchestration and is added to Snowflake Intelligence for UI access.

**Verify:**

```sql
DESCRIBE AGENT HL7_PATHOLOGY_AI.ANALYTICS.HL7_PATHOLOGY_AGENT;
```

<!-- ------------------------ -->
## Test the Platform

### Test via SQL

```sql
-- Population overview
SELECT SNOWFLAKE.CORE.AGENT_QUERY(
    'HL7_PATHOLOGY_AI.ANALYTICS.HL7_PATHOLOGY_AGENT', 
    'How many patients do we have and how many have cancer?'
);

-- Cancer analytics
SELECT SNOWFLAKE.CORE.AGENT_QUERY(
    'HL7_PATHOLOGY_AI.ANALYTICS.HL7_PATHOLOGY_AGENT', 
    'What types of cancer are in our pathology data?'
);

-- Molecular markers
SELECT SNOWFLAKE.CORE.AGENT_QUERY(
    'HL7_PATHOLOGY_AI.ANALYTICS.HL7_PATHOLOGY_AGENT', 
    'Which patients have MSI-High status?'
);

-- Cost analysis
SELECT SNOWFLAKE.CORE.AGENT_QUERY(
    'HL7_PATHOLOGY_AI.ANALYTICS.HL7_PATHOLOGY_AGENT', 
    'What are the total healthcare costs for patients with Stage III or IV cancer?'
);
```

### Test in Snowflake Intelligence UI

1. Navigate to **AI & ML > Snowflake Intelligence** in Snowsight
2. Find `HL7 Pathology Intelligence Agent`
3. Click to open the chat interface
4. Try questions like:
   - "Show me a summary of our cancer patient population"
   - "Find patients with colon cancer and show their KRAS and BRAF mutation status"
   - "Which patients have triple-negative breast cancer?"
   - "Compare healthcare costs between cancer and non-cancer patients"

### Diagnostic Queries

```sql
-- Check pipeline status
SELECT 'LANDING' AS LAYER, COUNT(*) AS RECORDS FROM CANCER_PATHOLOGY.LANDING_HL7_MESSAGES
UNION ALL SELECT 'SILVER_MSH', COUNT(*) FROM CANCER_PATHOLOGY.SILVER_MSH_SEGMENTS
UNION ALL SELECT 'SILVER_PID', COUNT(*) FROM CANCER_PATHOLOGY.SILVER_PID_SEGMENTS
UNION ALL SELECT 'GOLD', COUNT(*) FROM CANCER_PATHOLOGY.GOLD_CANCER_PATHOLOGY_REPORTS;

-- Check AI extraction quality
SELECT TUMOR_SITE, AJCC_STAGE_GROUP, DATA_QUALITY_SCORE
FROM CANCER_PATHOLOGY.GOLD_CANCER_PATHOLOGY_REPORTS;
```

<!-- ------------------------ -->
## Cleanup

When you are done with the guide, you can clean up all objects by executing `scripts/teardown.sql`.

This removes:
- The `HL7_PATHOLOGY_AI` database (cascades all schemas, tables, views, stages, procedures, semantic views, cortex search services, and agents)
- The `HL7_PATHOLOGY_WH` warehouse
- The `HEALTHCARE_ANALYST_ROLE` role
- The agent from Snowflake Intelligence (if registered)

```sql
-- Run with ACCOUNTADMIN role
-- Execute the contents of: scripts/teardown.sql
```

**Warning:** This is a destructive operation. Make sure you no longer need the data before running the teardown script.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You have successfully built a **Unified Healthcare Intelligence Platform** that:

- **Ingests** HL7 v2.7 cancer pathology messages (via OpenFlow or batch)
- **Parses** complex HL7 segments through a Bronze → Silver → Gold pipeline
- **Extracts** 20+ structured clinical fields using Cortex AI
- **Enables** natural language queries through a unified Snowflake Intelligence Agent
- **Provides** semantic search across pathology reports, medical transcripts, and conditions

### What You Learned
- How to build a healthcare data pipeline for HL7 v2.7 messages in Snowflake
- How to use Cortex AI for structured data extraction from unstructured pathology text
- How to create Semantic Views for multi-table healthcare analytics
- How to build Cortex Search Services for clinical data discovery
- How to deploy a Snowflake Intelligence Agent with multiple tools

### Related Resources
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Semantic Views Documentation](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
- [OpenFlow Documentation](https://docs.snowflake.com/en/user-guide/data-load/openflow)
- [GitHub Repository](https://github.com/Snowflake-Labs/sfguide-powering-AI-Ready-Data-Products-by-unpacking-complex-HL7-data-using-Snowflake)

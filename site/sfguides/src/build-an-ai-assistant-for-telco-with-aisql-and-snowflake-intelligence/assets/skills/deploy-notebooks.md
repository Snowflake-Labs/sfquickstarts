# Deploy Snowflake Notebooks

This skill deploys the NovaConnect Telco Operations notebooks to Snowflake.

## Overview

Deploys 3 Snowflake Notebooks for data processing and analysis:
- **1_DATA_PROCESSING** - Load CSV data, transcribe audio, parse PDFs
- **2_ANALYZE_CALL_AUDIO** - Review pre-transcribed call data
- **3_INTELLIGENCE_LAB** - Hands-on exploration with Cortex AI functions

## Prerequisites

Before running this skill, ensure:
1. The account has been configured (01_configure_account.sql completed)
2. Data has been uploaded to stages (02_data_foundation.sql completed)
3. You have the notebook files locally in `assets/Notebooks/`

## Steps

### Step 1: Verify Prerequisites

Check that required objects exist:

```sql
-- Verify database and schemas exist
SHOW SCHEMAS IN DATABASE TELCO_OPERATIONS_AI;

-- Verify data stages have files
LIST @TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.raw_files;
```

**Stop and verify**: Confirm the database exists and stages have files before proceeding.

### Step 2: Create Notebook Stages

Create individual stages for each notebook (provides clean navigation in UI):

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE TELCO_OPERATIONS_AI;

-- Create NOTEBOOKS schema if not exists
CREATE SCHEMA IF NOT EXISTS NOTEBOOKS;

-- Create individual stages for each notebook
CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK1 
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for 1_DATA_PROCESSING notebook';

CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK2 
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for 2_ANALYZE_CALL_AUDIO notebook';

CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK3 
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for 3_INTELLIGENCE_LAB notebook';
```

### Step 3: Upload Notebook Files

Upload notebook files to their respective stages:

```bash
# Navigate to the Notebooks directory
cd assets/Notebooks

# Upload each notebook to its dedicated stage
snow stage copy 1_DATA_PROCESSING.ipynb @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK1 --overwrite
snow stage copy environment.yml @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK1 --overwrite

snow stage copy 2_ANALYZE_CALL_AUDIO.ipynb @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK2 --overwrite
snow stage copy environment.yml @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK2 --overwrite

snow stage copy 3_INTELLIGENCE_LAB.ipynb @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK3 --overwrite
snow stage copy environment.yml @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK3 --overwrite
```

### Step 4: Create Notebooks

Create the notebook objects from the uploaded files:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE TELCO_OPERATIONS_AI;
USE SCHEMA NOTEBOOKS;

-- Create Notebook 1: Data Processing
CREATE OR REPLACE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."1_DATA_PROCESSING"
    FROM '@TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK1'
    MAIN_FILE = '1_DATA_PROCESSING.ipynb'
    QUERY_WAREHOUSE = 'TELCO_WH'
    COMMENT = 'NovaConnect Data Processing - Load CSV, transcribe audio, parse PDFs';

ALTER NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."1_DATA_PROCESSING" ADD LIVE VERSION FROM LAST;

-- Create Notebook 2: Analyze Call Audio
CREATE OR REPLACE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."2_ANALYZE_CALL_AUDIO"
    FROM '@TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK2'
    MAIN_FILE = '2_ANALYZE_CALL_AUDIO.ipynb'
    QUERY_WAREHOUSE = 'TELCO_WH'
    COMMENT = 'Review pre-transcribed call data and sentiment analysis';

ALTER NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."2_ANALYZE_CALL_AUDIO" ADD LIVE VERSION FROM LAST;

-- Create Notebook 3: Intelligence Lab
CREATE OR REPLACE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."3_INTELLIGENCE_LAB"
    FROM '@TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK3'
    MAIN_FILE = '3_INTELLIGENCE_LAB.ipynb'
    QUERY_WAREHOUSE = 'TELCO_WH'
    COMMENT = 'Hands-on exploration with Cortex AI functions and visualizations';

ALTER NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."3_INTELLIGENCE_LAB" ADD LIVE VERSION FROM LAST;
```

### Step 5: Grant Permissions

Grant access to the TELCO_ANALYST_ROLE:

```sql
USE ROLE ACCOUNTADMIN;

-- Grant schema usage
GRANT USAGE ON SCHEMA TELCO_OPERATIONS_AI.NOTEBOOKS TO ROLE TELCO_ANALYST_ROLE;

-- Grant notebook permissions
GRANT ALL ON ALL NOTEBOOKS IN SCHEMA TELCO_OPERATIONS_AI.NOTEBOOKS TO ROLE TELCO_ANALYST_ROLE;

-- Grant stage permissions for future updates
GRANT READ, WRITE ON ALL STAGES IN SCHEMA TELCO_OPERATIONS_AI.NOTEBOOKS TO ROLE TELCO_ANALYST_ROLE;
```

### Step 6: Verify Deployment

Confirm notebooks are deployed correctly:

```sql
-- List all notebooks
SHOW NOTEBOOKS IN SCHEMA TELCO_OPERATIONS_AI.NOTEBOOKS;

-- Check notebook details
DESCRIBE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."1_DATA_PROCESSING";
DESCRIBE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."2_ANALYZE_CALL_AUDIO";
DESCRIBE NOTEBOOK TELCO_OPERATIONS_AI.NOTEBOOKS."3_INTELLIGENCE_LAB";
```

**Expected output**: 3 notebooks should be listed with LIVE versions.

## Accessing Notebooks

After deployment, access notebooks in Snowsight:

1. Navigate to **Projects** → **Notebooks**
2. Select database **TELCO_OPERATIONS_AI**
3. Select schema **NOTEBOOKS**
4. Click on any notebook to open it

### Recommended Execution Order

1. **1_DATA_PROCESSING** - Run first to load all data
2. **2_ANALYZE_CALL_AUDIO** - Review transcribed call data
3. **3_INTELLIGENCE_LAB** - Explore with 11 hands-on exercises

## Notebook Contents

### 1_DATA_PROCESSING (10 cells)
| Cell | Name | Description |
|------|------|-------------|
| 0 | intro-overview | Purpose and prerequisites |
| 1 | setup-session | Initialize Snowpark session |
| 2-3 | part1-csv | Load 6 CSV files from @raw_files |
| 4-5 | part2-audio | Transcribe 25 audio files with AI_TRANSCRIBE |
| 6-7 | part3-pdf | Parse 8 PDFs with AI_PARSE_DOCUMENT |
| 8-9 | summary | Verify all data loaded |

### 2_ANALYZE_CALL_AUDIO (7 cells)
| Cell | Name | Description |
|------|------|-------------|
| 0 | intro-overview | Overview and learning objectives |
| 1 | setup-session | Initialize session |
| 2-3 | step1-list-audio | List pre-loaded audio files |
| 4-5 | step2-review | Review pre-transcribed data |
| 6 | summary | Benefits and next steps |

### 3_INTELLIGENCE_LAB (25 cells)
| Cell | Name | Description |
|------|------|-------------|
| 0-1 | intro/setup | Overview and session setup |
| 2-3 | ex1 | Data exploration and summary |
| 4-5 | ex2 | AI_TRANSLATE for multilingual |
| 6-7 | ex3 | Sentiment analysis visualization |
| 8-9 | ex4 | CSAT score analysis |
| 10-11 | ex5 | Network performance by region |
| 12-13 | ex6 | Cortex Search semantic queries |
| 14-15 | ex7 | Customer risk identification |
| 16-17 | ex8 | Revenue impact quantification |
| 18-19 | ex9 | AI_REDACT for data privacy |
| 20-21 | ex10 | Custom analysis experiments |
| 22-23 | ex11 | ML churn prediction model |
| 24 | lab-summary | Completion summary |

## Troubleshooting

**Notebook creation fails**:
- Verify stage has the .ipynb file: `LIST @TELCO_OPERATIONS_AI.NOTEBOOKS.TELCO_NOTEBOOK1;`
- Check file name matches exactly (case-sensitive)

**Notebook won't open**:
- Ensure TELCO_WH warehouse is running
- Check you have TELCO_ANALYST_ROLE or ACCOUNTADMIN

**Import errors in notebook**:
- Add required packages in notebook settings (matplotlib, pandas)
- Verify environment.yml is uploaded

**Data not found errors**:
- Run 1_DATA_PROCESSING first to load all data
- Verify @raw_files stage has CSV, audio, and PDF files

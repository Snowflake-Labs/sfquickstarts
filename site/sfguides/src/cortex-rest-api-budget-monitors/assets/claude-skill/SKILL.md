---
id: claude-skill-skill
language: en
name: cortex-usage-report
description: "Generate Cortex REST API usage report as PDF. Use when: user wants usage report, token consumption report, API usage summary, cortex usage PDF. Triggers: usage report, cortex usage, token report, API consumption."
---

# Cortex Usage Report

Generate a PDF report showing Cortex REST API usage metrics.

## Workflow

### Step 1: Query Usage Data

Run these SQL queries against `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY`:

```sql
-- KPI Totals
SELECT 
    SUM(TOKENS) as total_tokens,
    COUNT(*) as total_requests,
    COUNT(DISTINCT MODEL_NAME) as unique_models
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= :start_date

-- Daily Usage
SELECT 
    DATE_TRUNC('day', START_TIME)::DATE AS usage_date,
    SUM(TOKENS) as total_tokens,
    COUNT(*) as request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= :start_date
GROUP BY 1 ORDER BY 1

-- Usage by Model
SELECT 
    MODEL_NAME,
    SUM(TOKENS) as total_tokens,
    COUNT(*) as request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= :start_date
GROUP BY 1 ORDER BY 2 DESC

-- Daily by Model (for pivot)
SELECT 
    DATE_TRUNC('day', START_TIME)::DATE AS usage_date,
    MODEL_NAME,
    SUM(TOKENS) as total_tokens,
    COUNT(*) as request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= :start_date
GROUP BY 1, 2 ORDER BY 1, 2
```

### Step 2: View in Streamlit (Default)

The budget monitor dashboard shows results interactively:

```bash
SNOWFLAKE_CONNECTION_NAME=<your_connection> streamlit run <SKILL_DIR>/scripts/budget_monitor.py --server.port 8501 --server.headless true
```

Tab 1 (Claude Skill) displays KPIs, daily trends, model breakdowns, and daily-by-model table.

### Step 3: Generate PDF via `/pdf` Command

In the Streamlit app's Tab 1, type `/pdf` in the command bar to generate a downloadable PDF report from the queried data.

Alternatively, generate a PDF from the CLI:

```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/generate_report.py \
    --totals '<totals_json>' \
    --daily '<daily_json>' \
    --by-model '<by_model_json>' \
    --daily-by-model '<daily_by_model_json>' \
    --start-date '<start_date>' \
    --output '<output_path.pdf>'
```

**Arguments:**
- `--totals`: JSON string with total_tokens, total_requests, unique_models
- `--daily`: JSON array of {usage_date, total_tokens, request_count}
- `--by-model`: JSON array of {model_name, total_tokens, request_count}
- `--daily-by-model`: JSON array of {usage_date, model_name, total_tokens}
- `--start-date`: Report start date (e.g., "2025-02-13")
- `--output`: Output PDF file path

### Step 4: Present Results

Tell user the PDF location and offer to open it.

## Output

PDF report containing:
- KPI summary (total tokens, requests, models)
- Daily token usage bar chart
- Tokens by model bar chart
- Daily usage breakdown table

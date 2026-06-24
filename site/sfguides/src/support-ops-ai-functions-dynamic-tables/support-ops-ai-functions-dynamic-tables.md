id: support-ops-ai-functions-dynamic-tables
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/snowflake-feature/streamlit
language: en
summary: Build an automated support ticket enrichment pipeline using Cortex AI Functions, Dynamic Tables, and Streamlit in Snowflake.
environments: web
status: Draft
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: AI, Cortex, AI_CLASSIFY, AI_COMPLETE, AI_TRANSCRIBE, AI_REDACT, Dynamic Tables, Streamlit, Support Operations
authors: James Cha-Earley

# AI-Powered Support Operations with Cortex AI Functions & Dynamic Tables
<!-- ------------------------ -->
## Overview

Customer support teams spend significant time reading tickets to classify issues, gauge urgency, and decide on next steps. This quickstart shows how to automate that entire workflow using Snowflake Cortex AI Functions, with a Dynamic Table that keeps results fresh and a Streamlit dashboard for operational visibility.

You'll build a pipeline that:
- **Transcribes** phone call recordings into text with `AI_TRANSCRIBE`
- **Classifies** every ticket into your taxonomy with `AI_CLASSIFY`
- **Scores sentiment** on a continuous numeric scale with `AI_COMPLETE`
- **Generates operational recommendations** per ticket with `AI_COMPLETE`
- **Auto-refreshes** via a Dynamic Table — no scheduler, no Airflow
- **Surfaces results** in a Streamlit in Snowflake dashboard

### Architecture

```
  [Web/Email Forms] ──►  RAW.SUPPORT_TICKETS (text)
  [Phone Calls]     ──►  @SUPPORT_AUDIO_STAGE (audio files)
                              │
                              ▼  Dynamic Table (auto-refresh)
                    ANALYTICS.ENRICHED_TICKETS
                      ← AI_TRANSCRIBE  (audio → text)
                      ← AI_CLASSIFY    (issue category)
                      ← AI_COMPLETE    (sentiment score)
                      ← AI_COMPLETE    (recommended action)
                              │
                              ▼
                    Streamlit in Snowflake (Ops Dashboard)
```

### Prerequisites

- A Snowflake account with ACCOUNTADMIN role in a [supported region](https://docs.snowflake.com/user-guide/snowflake-cortex/aisql-regional-availability)
- The SNOWFLAKE.CORTEX_USER database role granted to your user

### What You Will Learn

- How to use `AI_TRANSCRIBE` to convert audio files to text
- How to use `AI_CLASSIFY` for zero-training-data ticket routing
- How to use `AI_COMPLETE` for numeric sentiment scoring and action generation
- How to use `TRY_TO_DOUBLE` for safe casting of LLM outputs
- How to structure a Dynamic Table with CTEs to avoid column-alias errors
- How to build a Streamlit in Snowflake operations dashboard

### What You Will Build

An end-to-end support ticket enrichment pipeline that automatically classifies, scores, and recommends actions on every inbound ticket — with a live dashboard for operations managers.

<!-- ------------------------ -->
## Setup

**Step 1.** In Snowsight, create a SQL Worksheet and run the following to set up your environment:

```sql
-- Create the database and schemas
CREATE DATABASE IF NOT EXISTS SUPPORT_OPS_AI;
CREATE SCHEMA IF NOT EXISTS SUPPORT_OPS_AI.RAW;
CREATE SCHEMA IF NOT EXISTS SUPPORT_OPS_AI.ANALYTICS;

-- Create a warehouse for AI Function processing
CREATE WAREHOUSE IF NOT EXISTS SUPPORT_OPS_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

USE DATABASE SUPPORT_OPS_AI;
USE SCHEMA RAW;
USE WAREHOUSE SUPPORT_OPS_WH;

-- Create the stage for phone call recordings
CREATE STAGE IF NOT EXISTS SUPPORT_AUDIO_STAGE
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Create the raw tickets table
CREATE TABLE IF NOT EXISTS SUPPORT_TICKETS (
  ticket_id     VARCHAR DEFAULT UUID_STRING(),
  channel       VARCHAR,
  raw_text      VARCHAR,
  audio_path    VARCHAR,
  created_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

**Step 2.** Insert sample support tickets:

```sql
INSERT INTO SUPPORT_TICKETS (channel, raw_text) VALUES
('email', 'Our API integration has been timing out for the past 3 hours. We are losing transactions and this is affecting our revenue. This needs to be fixed immediately.'),
('web', 'I cannot log in with SSO. Every time I click the login button it redirects me back to the login page. I have tried clearing cookies and using incognito mode. Nothing works.'),
('email', 'I was charged the full monthly rate even though I upgraded mid-cycle. According to your pricing page, upgrades should be prorated. Please issue a credit for the difference.'),
('web', 'Would love to see a dark mode option in the dashboard. The current white background is harsh during late-night monitoring sessions.'),
('email', 'Hi, just wanted to confirm whether your platform supports webhooks for real-time event notifications. We are evaluating tools for our integration layer.'),
('web', 'The API has been returning 504 errors intermittently since yesterday morning. Our batch processing jobs are failing and we have a client delivery deadline tomorrow.'),
('email', 'I have been locked out of my account for 2 days now. The password reset email never arrives. I have checked spam. This is completely unacceptable for a paid service.'),
('web', 'Your invoice from last month shows a charge for 50 seats but we only have 32 active users. Can someone look into this and issue a correction?'),
('email', 'It would be really helpful if the analytics dashboard had an export-to-PDF feature. Right now I have to screenshot everything for my weekly reports.'),
('web', 'Just wanted to say the new onboarding flow is excellent. Took me 5 minutes to get set up compared to an hour last year. Great improvement.'),
('email', 'API latency has spiked to 8 seconds on average. Normal is under 200ms. Something is seriously wrong on your end. We need an update ASAP.'),
('web', 'SSO login works fine on Chrome but fails completely on Firefox. The SAML assertion seems to be malformed for Firefox user agents.'),
('email', 'Can you explain why my bill went up 40% this month? I did not change my plan or add any users. There is no explanation on the invoice.'),
('web', 'Feature request: please add support for custom RBAC roles. The current admin/viewer split is too coarse for our team structure.'),
('email', 'Quick question: do you offer volume discounts for organizations with 500+ seats? We are planning a company-wide rollout next quarter.');
```

**Step 3.** (Optional) If you have sample audio files (.wav, .mp3, .flac), upload them to the stage using Snowsight: **Data → Add Data → Load files into a Stage** → select `SUPPORT_OPS_AI.RAW.SUPPORT_AUDIO_STAGE`. Then insert corresponding rows:

```sql
-- Example: register a phone ticket pointing to your uploaded audio file
INSERT INTO SUPPORT_TICKETS (channel, audio_path)
VALUES ('phone', 'sample_call.wav');
```

<!-- ------------------------ -->
## Transcribe Phone Calls

For tickets that arrive as phone recordings, `AI_TRANSCRIBE` converts the audio to text. The audio never leaves Snowflake.

```sql
-- Preview transcription (run only if you uploaded audio files)
SELECT
  ticket_id,
  AI_TRANSCRIBE(
    TO_FILE('@SUPPORT_AUDIO_STAGE', audio_path)
  ):text::VARCHAR AS transcript
FROM RAW.SUPPORT_TICKETS
WHERE channel = 'phone';
```

`AI_TRANSCRIBE` accepts a FILE type object (created with `TO_FILE`) and returns a JSON object with a `text` field containing the full transcript. Language is auto-detected — no language parameter needed.

After this step, all tickets (text and audio) can be treated identically by downstream AI Functions.

<!-- ------------------------ -->
## Classify and Score Tickets

### Classify with AI_CLASSIFY

`AI_CLASSIFY` routes each ticket into your predefined categories with zero training data:

```sql
SELECT
  ticket_id,
  raw_text,
  AI_CLASSIFY(
    raw_text,
    ARRAY_CONSTRUCT(
      'System Bug: API Timeout',
      'Account Access: SSO',
      'Billing: Prorated Upgrades',
      'Feature Request',
      'General Inquiry'
    )
  ):labels[0]::VARCHAR AS issue_category
FROM RAW.SUPPORT_TICKETS
WHERE channel != 'phone'
LIMIT 5;
```

Unlike rules-based classifiers, `AI_CLASSIFY` handles natural language variation. A ticket saying "I keep getting kicked out of the API" routes to `System Bug: API Timeout` even without those exact words.

### Score Sentiment Numerically

`AI_SENTIMENT` returns categorical labels (positive, negative, neutral). For a continuous score that lets you rank severity, use `AI_COMPLETE` with a structured prompt:

```sql
SELECT
  ticket_id,
  raw_text,
  TRY_TO_DOUBLE(
    AI_COMPLETE(
      'claude-4-sonnet',
      CONCAT(
        'Rate the sentiment of this support ticket on a scale from -1.0 ',
        '(extremely frustrated) to +1.0 (satisfied/positive). ',
        'Return ONLY a decimal number, no explanation. ',
        'Ticket: ', raw_text
      )
    )::VARCHAR
  ) AS sentiment_score
FROM RAW.SUPPORT_TICKETS
WHERE channel != 'phone'
LIMIT 5;
```


<!-- ------------------------ -->
## Build the Dynamic Table Pipeline

Rather than scheduling ETL jobs, wrap the entire pipeline in a Dynamic Table. Snowflake refreshes it automatically as new tickets arrive.

The key architectural decision: use **CTEs** to avoid referencing column aliases in the same SELECT (which Snowflake does not allow):

```sql
USE SCHEMA SUPPORT_OPS_AI.ANALYTICS;

CREATE OR REPLACE DYNAMIC TABLE ENRICHED_TICKETS
  TARGET_LAG = '1 hour'
  WAREHOUSE = SUPPORT_OPS_WH
AS
WITH transcribed AS (
  SELECT
    ticket_id, channel, created_at,
    CASE
      WHEN channel = 'phone'
        THEN AI_TRANSCRIBE(
               TO_FILE('@RAW.SUPPORT_AUDIO_STAGE', audio_path)
             ):text::VARCHAR
      ELSE raw_text
    END AS ticket_text
  FROM RAW.SUPPORT_TICKETS
),
classified AS (
  SELECT *,
    AI_CLASSIFY(
      ticket_text,
      ARRAY_CONSTRUCT(
        'System Bug: API Timeout',
        'Account Access: SSO',
        'Billing: Prorated Upgrades',
        'Feature Request',
        'General Inquiry'
      )
    ):labels[0]::VARCHAR AS issue_category,
    TRY_TO_DOUBLE(
      AI_COMPLETE(
        'claude-4-sonnet',
        CONCAT('Rate sentiment -1.0 to +1.0. Return only a number. Ticket: ', ticket_text)
      )::VARCHAR
    ) AS sentiment_score
  FROM transcribed
)
SELECT
  ticket_id, channel, created_at, ticket_text,
  issue_category, sentiment_score,
  AI_COMPLETE(
    'claude-4-sonnet',
    CONCAT(
      'Support ops manager. Category: ', issue_category,
      '. Sentiment: ', ROUND(sentiment_score, 2)::VARCHAR,
      '. Recommend one operational action in 1-2 sentences.'
    )
  )::VARCHAR AS recommended_action
FROM classified;
```

Once created, this table refreshes itself. Insert a new ticket into `RAW.SUPPORT_TICKETS` and within an hour it appears in `ENRICHED_TICKETS` — classified, scored, and with a recommendation.

### Verify the Pipeline

```sql
-- Check that the Dynamic Table populated
SELECT * FROM ANALYTICS.ENRICHED_TICKETS LIMIT 10;

-- Check refresh status
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME => 'SUPPORT_OPS_AI.ANALYTICS.ENRICHED_TICKETS'
)) ORDER BY REFRESH_START_TIME DESC LIMIT 5;
```

<!-- ------------------------ -->
## Build the Streamlit Dashboard

Create a Streamlit in Snowflake app to give operations managers a live view of issue volume, sentiment trends, and AI-generated recommendations.

**Step 1.** In Snowsight, open a **Workspace** (or go to **Projects → Streamlit** and click **+ Streamlit App**).

**Step 2.** Set the app database to `SUPPORT_OPS_AI`, schema to `ANALYTICS`, and warehouse to `SUPPORT_OPS_WH`.

**Step 3.** Paste the following code:

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd

session = get_active_session()

st.title("Support Operations Intelligence")
st.caption("Powered by Snowflake AI Functions · Refreshes every hour")

df = session.sql("""
    SELECT
        issue_category,
        COUNT(*)                          AS volume,
        ROUND(AVG(sentiment_score), 2)    AS avg_sentiment,
        ANY_VALUE(recommended_action)     AS recommended_action
    FROM analytics.enriched_tickets
    WHERE created_at >= DATEADD('day', -30, CURRENT_TIMESTAMP())
    GROUP BY issue_category
    ORDER BY volume DESC
""").to_pandas()

def sentiment_label(score):
    if score <= -0.7:   return "Frustrated"
    elif score <= -0.4: return "Stressed"
    elif score <= -0.1: return "Annoyed"
    elif score <= 0.3:  return "Neutral"
    else:               return "Positive"

df["Sentiment Label"] = df["AVG_SENTIMENT"].apply(sentiment_label)
df["Avg. Sentiment"]  = df.apply(
    lambda r: f"{r['AVG_SENTIMENT']} ({r['Sentiment Label']})", axis=1
)

col1, col2, col3 = st.columns(3)
col1.metric("Total Tickets (30d)", f"{df['VOLUME'].sum():,}")
col2.metric("Avg. Sentiment", f"{(df['AVG_SENTIMENT'] * df['VOLUME']).sum() / df['VOLUME'].sum():.2f}")
col3.metric("Issue Categories", len(df))

st.divider()

st.subheader("Issue Summary & Recommended Actions")
st.dataframe(
    df[["ISSUE_CATEGORY", "Avg. Sentiment", "VOLUME", "RECOMMENDED_ACTION"]].rename(columns={
        "ISSUE_CATEGORY":       "Issue Category",
        "VOLUME":               "Volume",
        "RECOMMENDED_ACTION":   "Sample Recommendation"
    }),
    use_container_width=True,
    hide_index=True
)

st.subheader("Daily Sentiment Trend")
trend_df = session.sql("""
    SELECT
        DATE_TRUNC('day', created_at) AS day,
        issue_category,
        ROUND(AVG(sentiment_score), 3) AS avg_sentiment
    FROM analytics.enriched_tickets
    WHERE created_at >= DATEADD('day', -30, CURRENT_TIMESTAMP())
    GROUP BY 1, 2
    ORDER BY 1
""").to_pandas()

st.line_chart(
    trend_df.pivot(index="DAY", columns="ISSUE_CATEGORY", values="AVG_SENTIMENT")
)
```

<!-- ------------------------ -->
## Best Practices

### PII Handling with AI_REDACT

Support tickets routinely contain customer PII. Use `AI_REDACT` before surfacing data to broader teams:

```sql
SELECT
  ticket_id,
  AI_REDACT(ticket_text) AS redacted_text,
  issue_category,
  sentiment_score,
  recommended_action
FROM ANALYTICS.ENRICHED_TICKETS
LIMIT 5;
```

For production, apply [Dynamic Data Masking](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro) policies on the `ticket_text` column to restrict access by role.

### Cost Optimization

| Task | Recommended Model | Reason |
|------|-------------------|--------|
| Classification | `AI_CLASSIFY` (managed) | Optimized internally by Snowflake |
| Sentiment scoring | `claude-4-sonnet` | Good structured output at lower cost |
| Recommendations | `claude-4-sonnet` | Balanced quality and cost |
| Complex edge cases | `claude-4-opus` | Strongest reasoning for ambiguous tickets |

### Human-in-the-Loop

- Treat AI recommendations as **suggestions**, not automated triggers
- Audit a 5% sample weekly against human labels
- Use the [Cortex AI Function Studio](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-function-studio) to evaluate and optimize prompt quality over time

<!-- ------------------------ -->
## Cleanup

To remove all objects created in this quickstart:

```sql
DROP DATABASE IF EXISTS SUPPORT_OPS_AI;
DROP WAREHOUSE IF EXISTS SUPPORT_OPS_WH;
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've built an end-to-end AI-powered support operations pipeline entirely within Snowflake — no external APIs, no separate ML infrastructure, no schedulers.

### What You Learned

- **AI_TRANSCRIBE** converts audio to text with auto language detection
- **AI_CLASSIFY** routes tickets into your taxonomy with zero training data
- **AI_COMPLETE** with `TRY_TO_DOUBLE` provides safe numeric sentiment scoring
- **Dynamic Tables with CTEs** create auto-refreshing pipelines without column-alias errors
- **Streamlit in Snowflake** gives operations teams a live dashboard with no external deployment

### Related Resources

- [Cortex AI Functions Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql)
- [Dynamic Tables Guide](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview)
- [AI_TRANSCRIBE Reference](https://docs.snowflake.com/en/sql-reference/functions/ai_transcribe)
- [AI_CLASSIFY Reference](https://docs.snowflake.com/en/sql-reference/functions/ai_classify)
- [Cortex AI Function Studio](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-function-studio)
- [Getting Started with Cortex AI Functions Quickstart](https://quickstarts.snowflake.com/guide/getting-started-with-cortex-aisql/)

author: Abhinav Vadrevu, Nick El-Rayess
id: how-to-ingest-power-bi-semantic-models
language: en
summary: Bring your Power BI semantic layer (relationships + measures) into Snowflake Semantic Views so the same governed business definitions power Cortex Analyst / Snowflake Intelligence and Power BI.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# How to Ingest Power BI Semantic Models

## Overview

Power BI models often contain years of institutional knowledge: table relationships, filters, and business logic embedded in DAX measures like “active users” or “monthly recurring revenue”. When you build AI experiences directly on raw tables, that context is missing—leading to inconsistent numbers and confusing answers.

In this guide, you’ll take a Power BI semantic layer and turn it into a **Snowflake Semantic View**, a governed semantic layer stored as a Snowflake schema object. Then you’ll use that same semantic layer for:

- Cortex Analyst (natural language analytics)
- Snowflake Intelligence (agentic/assistant experiences, where available)

## Prerequisites

- Snowflake account with access to **Semantic Views** and **Cortex Analyst**
- A role with privileges to create semantic views:
  - `CREATE SEMANTIC VIEW` on the target schema
  - `USAGE` on the database and schema
  - `SELECT` on the underlying tables/views
- Power BI Desktop (or access to a Power BI workspace that allows downloading a template)
- A Power BI report/model you can export/download as a `.pbit`

## What you will learn

- How to export a Power BI model as a `.pbit`
- How to create a Snowflake Semantic View from BI context
- How to validate semantic metrics/dimensions and query the semantic view

## Part 1: Export your semantic layer from Power BI

1. Open the report in **Power BI Desktop**.
2. Export the report as a Power BI template (`.pbit`):
   - **File** → **Export** → **Power BI template**
3. Confirm your model contains meaningful semantic logic you want to reuse:
   - Relationships between tables
   - Measures (DAX)
   - Calculated columns (optional)

If you’re starting from the Power BI service, your org policies must allow downloading the `.pbit`.

## Part 2: Create a semantic view in Snowflake

There are two ways to provide “BI context” to Snowflake when creating the semantic view:

- **Option A (Private Preview)**: Import a `.pbit` file directly (only if your account has this capability enabled).
- **Option B (GA)**: Use **Semantic View Autopilot** with example SQL queries and table metadata (works in any account with semantic views).

### Option A: Import a `.pbit` (if enabled in your account)

1. Sign in to **Snowsight**.
2. Navigate to **AI & ML** → **Cortex Analyst**.
3. Select **Create new** → **Create new Semantic View**.
4. If you see a Power BI import/upload option, choose it and upload your `.pbit`.
5. In the review steps, confirm Snowflake extracted:
   - The tables/columns referenced by the model
   - Relationships (joins) between tables
   - Measures/metrics derived from DAX (review carefully—some DAX patterns may need refinement)
6. Create and save the semantic view.

If you don’t see a `.pbit` import option, use Option B.

### Option B: Use Semantic View Autopilot (recommended GA path)

1. Sign in to **Snowsight**.
2. Navigate to **AI & ML** → **Cortex Analyst**.
3. Select **Create new** → **Create new Semantic View**.
4. Pick the **database/schema** to store the semantic view, and give it a name (for example, `POWERBI_SEMANTICS`).
5. Provide context:
   - **Select tables**: choose the Snowflake tables/views that back your Power BI model.
   - **SQL queries (recommended)**: paste 2–5 “gold” queries you want the semantic layer to support. These are used to infer relationships and may be added as **verified queries**.
6. Select columns to include (Snowflake recommends <= 50 columns for performance and accuracy). Prefer:
   - Join keys
   - Core dimensions used for slicing (date, customer, product, region)
   - Facts used in metrics (amounts, counts)
7. Enable (recommended):
   - **Sample values** (improves accuracy for entity/value recognition)
   - **AI-generated descriptions** (you’ll review/edit later)
8. Select **Create and save**, then wait for generation to complete.

## Part 3: Validate and query your semantic view

After creation, validate what Snowflake generated.

### Add custom instructions to reflect Power BI defaults (recommended)

If your Power BI report applies default filters, slicers, or “implicit” measure behavior, capture those assumptions as semantic view custom instructions so Cortex Analyst results align with what users see in Power BI.

In Snowsight, open your semantic view and add custom instructions similar to the following (edit to match your report defaults):

```
When answering questions, mirror the default Power BI report settings:
- Apply the report’s default date range (for example: last 12 full months, excluding the current partial month).
- Respect default filters/slicers (for example: exclude blank/unknown categories; include only Active customers = true).
- Unless the user asks otherwise, use the same default aggregation/format as Power BI visuals (for example: revenue is SUM, rounded to whole currency units).
- If Power BI uses a specific “as of” date or snapshot logic, use that same definition consistently.
```

### Inspect the semantic view objects

Run these in a worksheet (replace placeholders):

```sql
SHOW SEMANTIC VIEWS IN SCHEMA <DB>.<SCHEMA>;

DESCRIBE SEMANTIC VIEW <DB>.<SCHEMA>.<SEMANTIC_VIEW_NAME>;

SHOW SEMANTIC METRICS IN SEMANTIC VIEW <DB>.<SCHEMA>.<SEMANTIC_VIEW_NAME>;
SHOW SEMANTIC DIMENSIONS IN SEMANTIC VIEW <DB>.<SCHEMA>.<SEMANTIC_VIEW_NAME>;
```

### Query the semantic view with SQL

You can query semantic views in two common ways.

**A) Use the `SEMANTIC_VIEW(...)` table function form** (explicit dimensions/metrics):

```sql
SELECT *
FROM SEMANTIC_VIEW(
  <DB>.<SCHEMA>.<SEMANTIC_VIEW_NAME>
  METRICS <LOGICAL_TABLE>.<METRIC_NAME>
  DIMENSIONS <LOGICAL_TABLE>.<DIMENSION_NAME>
)
ORDER BY 1;
```

**B) Query the semantic view name directly** (more “BI-like”):

```sql
SELECT
  <DIMENSION_NAME>,
  AGG(<METRIC_NAME>) AS metric_value
FROM <DB>.<SCHEMA>.<SEMANTIC_VIEW_NAME>
GROUP BY 1
ORDER BY 1;
```

## Part 4: Ask business questions with Cortex Analyst (and Snowflake Intelligence)

### Cortex Analyst

1. In Snowsight, go to **AI & ML** → **Cortex Analyst**.
2. Select your semantic view.
3. Ask natural-language questions that rely on the imported definitions, for example:
   - “What was our total revenue last quarter?”
   - “Show me our top 10 customers by lifetime value.”
   - “How has our active user count trended over the past 6 months?”
4. Review the generated SQL and results.

If you see suggestions/verified-query recommendations, review and apply the ones that match your business logic.

### Snowflake Intelligence (where available)

If your org uses Snowflake Intelligence with semantic views enabled, connect your assistant/agent experience to the semantic view you created and reuse the same questions above. The key check is that the assistant uses the governed metrics/dimensions from the semantic view (not ad hoc SQL against raw tables).

## Troubleshooting

- **No `.pbit` import option in Snowsight**: Use Semantic View Autopilot with SQL queries (Option B). `.pbit` ingestion may require an enablement/preview flag.
- **Metrics don’t match Power BI**: Check whether Power BI applies default report/page/visual filters or implicit measure behavior (for example: default date windows, slicers, “(Blank)” handling, visual-level filters, rounding/formatting, or “Summarize by” defaults). Then review generated metrics and relationships, and add custom instructions to reflect those default settings.
- **Wrong joins or fan-out**: Ensure primary/unique keys are set correctly in logical tables and relationships. Add or correct relationships in the semantic view editor.
- **Poor natural-language accuracy**: Add sample values, improve descriptions/synonyms, and add verified queries that reflect how users ask questions.

## Resources

- [Semantic View Autopilot](https://docs.snowflake.com/en/user-guide/views-semantic/autopilot)
- [Using Snowsight to create and manage semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/ui)
- [Querying semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/querying)
- [CREATE SEMANTIC VIEW (SQL)](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)

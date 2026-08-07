author: Rida Safdar
id: accelerate-app-dev-cortex-code
language: en
summary: Build end-to-end AI applications on your Snowflake data using Cortex Complete, Cortex Search, and CoCo — no data movement required.
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration,snowflake-site:taxonomy/snowflake-feature/cortex-code
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Building AI Applications with Snowflake Cortex: RAG, Text-to-SQL & CoCo

<!-- ------------------------ -->
## Overview

In this hands-on lab you will go from data consumer to AI builder. Starting from a fresh Snowflake trial account — with no uploads, no external APIs, and no data movement — you will build two AI-powered applications:

1. A **Retrieval-Augmented Generation (RAG)** app that answers questions from a corpus of text documents
2. A **Text-to-SQL** interface that answers business questions from structured tables in plain English

Along the way, you will use **CoCo**, Snowflake's AI coding assistant, to write and accelerate the most complex parts of the lab.

### Prerequisites
- A Snowflake Trial Account (any cloud region). [Sign up here](https://signup.snowflake.com/)
- Basic familiarity with SQL
- No Python experience required for Module 1; basic Python familiarity helps for Module 2

### What You'll Learn
- How to call large language models (LLMs) directly in Snowflake using `CORTEX.COMPLETE`
- The architecture behind Retrieval-Augmented Generation (RAG) and why it prevents hallucinations
- How to build a production RAG app using `CORTEX SEARCH SERVICE` and a Snowflake Notebook
- How to use CoCo to generate complex Snowflake SQL and Python from plain English
- How to evaluate your AI application's response quality with Snowsight Evaluations
- Why naive LLM text-to-SQL produces silently wrong numbers — and how Semantic Views and Cortex Analyst fix it

### What You'll Need
- A Snowflake Trial Account — [signup.snowflake.com](https://signup.snowflake.com/)
- A web browser (Chrome or Firefox recommended)
- No local software installation required

### What You'll Build
- A **text corpus pipeline** — ingest, chunk, and index text documents inside Snowflake
- A **Cortex Search Service** that supports hybrid keyword + semantic search
- A **Python RAG application** that retrieves context and generates grounded answers
- A **Semantic View** encoding correct business metric formulas and a **Cortex Analyst** interface for production-grade Text-to-SQL

### Lab Files
This lab includes a pre-built Snowflake Notebook (`building-ai-apps-snowflake-cortex.ipynb`) with all Python cells ready to run. You will upload it in the next section — no manual cell creation required.

<!-- ------------------------ -->
## Set Up Your Environment


All setup runs in a **SQL Worksheet** in Snowsight. Navigate to **Left Pane > Create (+) Button ** and click **SQL File** to create a new worksheet.

### Step 1: Enable Your Personal Database and Secondary Roles


```sql
--Find your USER IDENTIFIER. Paste this value in the CURRENT_USER field.
SELECT CURRENT_USER();

-- Enable secondary roles for permission inheritance. Replace CURRENT_USER in the script with the USER IDENTIFIER from the previous step.
ALTER USER CURRENT_USER SET DEFAULT_SECONDARY_ROLES = ('ALL');

-- Activate secondary roles in the current session
USE SECONDARY ROLES ALL;

-- Enable a Personal Database for Private Notebooks
ALTER ACCOUNT SET ENABLE_PERSONAL_DATABASE = TRUE;
```

### Step 2: Create the Workshop Database and Schemas

```sql
-- Create the main workshop database
CREATE DATABASE IF NOT EXISTS AI_WORKSHOP_DB;

-- Schema for our RAG / unstructured data pipeline
CREATE SCHEMA IF NOT EXISTS AI_WORKSHOP_DB.RAG_DATA;

-- Schema for structured analytics (Text-to-SQL)
CREATE SCHEMA IF NOT EXISTS AI_WORKSHOP_DB.ANALYTICS;

USE DATABASE AI_WORKSHOP_DB;
USE SCHEMA RAG_DATA;
```

### Step 3: Create a Warehouse

```sql
CREATE WAREHOUSE IF NOT EXISTS WORKSHOP_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE;

USE WAREHOUSE WORKSHOP_WH;
```

> **Note:** X-Small warehouses are sufficient for all steps in this lab. Cortex Search and Cortex Complete use serverless compute that does not consume warehouse credits.

<!-- ------------------------ -->
## Upload the Workshop Notebook

All Python steps in this lab run from a single pre-built Snowflake Notebook. Upload it once and run cells sequentially — no manual cell creation required.

### Step 1: Upload the Notebook

1. In Snowsight, navigate to **Projects > Workspaces**
2. Click on **+ Add new > Upload files** and the select the downloaded [`accelerate-app-dev-cortex-code.ipynb`](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/accelerate-app-dev-cortex-code/assets/accelerate-app-dev-cortex-code.ipynb)
3. Click on **Connect** next to the **Run** button and select **Create and connect**
4. Wait for connection to complete
6. Set **Warehouse** to `WORKSHOP_WH`

### Step 2: Run the Setup Cell

Now run the setup code cell in the notebook imports all libraries and sets the active database, schema, and warehouse. **Run this cell before any other.** You should see:

```
Session ready.
  Database : AI_WORKSHOP_DB
  Schema   : RAG_DATA
  Warehouse: WORKSHOP_WH
```

If you see an error, confirm the SQL Worksheet setup steps completed successfully.

> **Tip:** Run cells individually to follow along with the lab guide.

<!-- ------------------------ -->
## Snowflake CoCo: Your AI Pair Programmer

Before we write a single line of lab code, take 10 minutes to meet the tool that will accelerate every step that follows.

**CoCo** is Snowflake's AI coding assistant. It understands Snowflake's full API surface — every SQL function, DDL syntax, Cortex primitive, and Snowpark class — and it generates runnable code from plain-English descriptions. It is available directly in Snowsight on all trial accounts.

### Opening CoCo in Snowsight

Navigate back to your SQL Worksheet, look for the icon (sparkle ✦) in the right side. Click it to open the CoCo chat panel.

> **Tip:** CoCo is context-aware. It can see your active database, schema, and table names, so your prompts don't need to be overly specific.

### Demo 1: Generate Setup SQL

In the CoCo chat panel, type the following prompt exactly:

```
Create an internal stage in the AI_WORKSHOP_DB database and RAG_DATA schema called DOCS_STAGE with directory
tables enabled and Snowflake SSE encryption.
```

CoCo will return the SQL below. Accept it and run the command in your worksheet:

```sql
CREATE OR REPLACE STAGE AI_WORKSHOP_DB.RAG_DATA.DOCS_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```
You should see the text "Stage DOCS_STAGE created with directory tables enabled and Snowflake SSE encryption."

> **What just happened?** You described what you wanted in plain English, and CoCo produced syntactically correct, Snowflake-idiomatic SQL — including the less-obvious `DIRECTORY` and `ENCRYPTION` parameters. Throughout this lab, use CoCo whenever you encounter a function or DDL pattern you haven't seen before.

### Demo 2: Explore an Unknown Function

Now try this prompt in the CoCo panel:

```
How do I use SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER to chunk text into
pieces of 1500 characters with 200-character overlap?
```

CoCo will return a working example of SQL functions with explanation. Keep this pattern in mind — you'll use this exact function in Module 2.

### Key Principle

> Use CoCo to **generate the hard parts** and **understand why** — don't just accept output blindly. The best workflow is: describe → generate → read → run → iterate.

<!-- ------------------------ -->
## Module 1 – Your AI Foundation


### The Two Types of AI Questions

Every AI application over data falls into one of two categories:

| Question Type | Data Type | Technique |
|---|---|---|
| "What does our policy say about refunds?" | Text, PDFs, docs | **RAG** — retrieve relevant chunks, ground the LLM |
| "What were total sales last quarter?" | Tables, structured data | **Text-to-SQL** — translate to SQL, execute, return result |

This module covers the foundations. Module 2 builds the production version.

### Step 1: Your First LLM Call

Open your uploaded notebook and run the **Step 1 cell** (Module 1 section).

```python
model  = 'mistral-7b'
prompt = 'In two sentences, explain the difference between structured and unstructured data.'
print(complete(model, prompt))
```

You just called a hosted LLM running inside your Snowflake account. No API key, no data leaving your security perimeter.

Run the **model comparison cell** below it to contrast `mistral-7b` and `llama3-70b` side by side.

### Step 2: The Hallucination Problem

Run the **Step 2 cell**. The model is asked for a specific private financial figure it cannot know:

```python
response = complete('mistral-7b', 'What is the exact revenue figure for Snowflake in Q4 FY26?')
print(response)
```

The model guesses, hedges, or states something unverifiable. This is the **hallucination problem** — and it is why RAG exists.

### Step 3: RAG — Grounding Fixes Hallucination

The solution is to **retrieve** relevant facts from your own data and **inject** them into the prompt as context. The LLM then answers using only what you provided.

Run the Step 3 cell. It pulls the top 5 customers by revenue live from `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` — the TPC-H order dataset pre-loaded in every trial account — formats them as context, and asks the LLM a grounded question using only that data.

Compare the grounded answer to Step 2. This is the RAG pattern: **your data → context → accurate answer**.

> In production, the context is not hand-crafted — it is retrieved automatically from a search index over your full corpus. Module 2 builds that.

### Step 4: Create Your Text Corpus

Run the **Step 4 cell** in the notebook. It creates `FEATURE_DOCS` and loads 15 Snowflake product feature descriptions using `session.write_pandas()` — no SQL cell or worksheet switch needed. You should see:

```
Corpus loaded: 15 documents
```

This table is your document library — the raw material for the RAG app in Module 2.

<!-- ------------------------ -->
## Module 2 – Production RAG with Cortex Search


### Architecture Overview

```
FEATURE_DOCS table
       │
       ▼
  Chunk the text            ← SPLIT_TEXT_RECURSIVE_CHARACTER
       │
       ▼
  CHUNKED_DOCS table
       │
       ▼
  Cortex Search Service     ← automatic embedding + hybrid index
       │
       ▼
  Python RAG App            ← retrieve context → Complete LLM → answer
```

### Step 1: Chunk the Text

Real documents are too long to fit in a single LLM prompt. We break them into overlapping chunks so the search index can return the most relevant piece. Cortex Search indexes chunks, not the whole document. The search service finds the most relevant chunk for a question. If you indexed full documents, you'd retrieve a wall of text (much of it irrelevant) and would send it all to the LLM. Precision in this case improves answer quality and provides you a higher groundedness score (covered later in this lab).

Run the **Step 1 cell** in the notebook. It splits each document into chunks of 1500 characters with a 200-character overlap between consecutive chunks, then writes the results to `CHUNKED_DOCS`. The overlap ensures that answers near a chunk boundary aren't cut off. You should see:

```
Chunks created: 15
```

Our documents are short so most produce a single chunk. With real PDFs or long articles you would see many more chunks per source document.

### Step 2: Create the Cortex Search Service

A single DDL statement creates a fully managed hybrid search index — Snowflake handles embedding, vectorization, and retrieval automatically.

Run the **Step 2 cell** in the notebook. It creates `FEATURE_SEARCH_SERVICE` and polls until the service is active (usually under 3 minutes). You should see:

```
Service is ACTIVE — ready to query.
```

### Step 3: Build the RAG Application

Run the **Step 3 cell** in the notebook to define and instantiate `RAG_App`. You should see:

```
RAG app ready.
  app.query(question)      -> Cortex Search (unstructured docs)
  app.query_data(question) -> Cortex Analyst (structured tables) [Module 3]
```

### Step 4: Test Your Application

Run the **Step 4 cell** in the notebook. It asks 5 test questions against your RAG app and prints each answer. Each response is scoped entirely to your 15-row corpus — the application cannot hallucinate beyond what you gave it. Note this cell may take a few minutes to run. You should see output like:

```
Q: What is the difference between Cortex Search and Cortex Analyst?
A: Cortex Search is for unstructured data like documents...
------------------------------------------------------------
Q: How does Snowpipe know when new files arrive?
A: Snowpipe can be triggered by cloud storage notifications...
------------------------------------------------------------
```

### Step 5: Evaluate Response Quality

Run the **Step 5 cell** in the notebook. This cell makes 15 LLM calls (5 questions × 3 metrics each) and will take 4–6 minutes. It scores each answer on three metrics (0.0–1.0) and prints a summary table:

```
                               question  groundedness  context_relevance  answer_relevance
  What is the difference between ...          0.95               0.92              0.94
  How does Snowpipe know when ...             0.90               0.88              0.91
  ...

Mean — Groundedness: 0.92 | Context Relevance: 0.90 | Answer Relevance: 0.93
```

A well-tuned RAG app should score **> 0.8 on all metrics**.

- If **Groundedness** is low, your prompt isn't constraining the model tightly enough.
- If **Context Relevance** is low, your search service or chunking needs improvement.
- If **Answer Relevance** is low, the model is retrieving the right context but generating poor answers.

<!-- ------------------------ -->
## Module 3 – Text-to-SQL with Sample Data

In Module 2 we built `app.query()` for **unstructured** questions (documents, PDFs). Now we tackle **structured** data — tables with numbers.

The naive approach: give an LLM your schema and let it write SQL. We'll prove this fails silently, then fix it with a **Semantic View** and **Cortex Analyst**.

| Step | What We Do |
|------|-----------|
| 1 | Explore the TPC-H schema |
| 2 | Establish gold-standard answers for Revenue and COGS |
| 3 | Let a naive LLM try — observe silent failures |
| 4 | Understand why it failed |
| 5 | Create a Semantic View |
| 6 | Use Cortex Analyst for production-grade accuracy |

### Step 1: Explore the Schema

`SNOWFLAKE_SAMPLE_DATA` is pre-loaded in every Snowflake trial. We use the **TPC-H** schema — a standard benchmark modelling a wholesale distributor that buys parts from suppliers and sells to customers.

| Table | What It Represents | Rows |
|-------|-------------------|------|
| **ORDERS** | One row per customer order | 1.5M |
| **LINEITEM** | One row per product within an order (1–7 per order) | 6M |
| **CUSTOMER** | Customer master data | 150K |
| **PARTSUPP** | What we pay each supplier per part | 800K |
| **NATION / REGION** | Geography reference tables | 25 / 5 |

> **Key insight:** `ORDERS.O_TOTALPRICE` is **not** revenue — it includes tax. True revenue must be calculated from LINEITEM.

Run the **schema exploration cell** in the Module 3 section of the notebook.

### Step 2: Establish Gold-Standard Answers

Before we ask an LLM anything, establish the **correct** formulas and numbers.

**Revenue** — net amount earned from selling goods (discounts applied, tax excluded):
```
Revenue = SUM( L_EXTENDEDPRICE × (1 - L_DISCOUNT) )
```

**Cost of Goods Sold (COGS)** — what we pay suppliers for the goods we sold:
```
COGS = SUM( PS_SUPPLYCOST × L_QUANTITY )
```

Run the **Step 2 cell**. You should see the correct values — note the **BUILDING segment** figures, which you'll use to verify correctness in Steps 3 and 6:

```
REVENUE by Market Segment (Gold Standard)
  BUILDING      $  44.14 B
  ...

COGS by Market Segment (Gold Standard)
  BUILDING      $  15.49 B
  ...
```

### Step 3: Naive Text-to-SQL — Let the LLM Try

Run the **Step 3 cells**. We give the LLM only the table and column names — no business definitions, no formulas — and ask it to write SQL for Revenue and COGS.

Both queries run without errors. Both return plausible-looking numbers. Run the **comparison cell** to see the discrepancy against the gold standard from Step 2.

> **Note:** The COGS cell may take 1–3 minutes — it calls `mistral-large2` (a larger, slower model) and executes a join across LINEITEM (6M rows) and PARTSUPP (800K rows) on an XSmall warehouse.

### Step 4: Why It Failed

Both queries ran without errors. Both are wrong.

| Metric | What Happened | Root Cause |
|--------|--------------|-----------| 
| **Revenue** | Used `SUM(O_TOTALPRICE)` instead of line-item formula | `O_TOTALPRICE` includes tax — a convenient shortcut that's subtly wrong (+4%) |
| **COGS** | Computed revenue and labeled it "cost" | No column named "cost" at the right level, so the LLM grabbed the biggest money formula it could find (2.8× wrong) |

> **The failure mode of naive text-to-SQL isn't "query fails." It's "query succeeds with wrong numbers."**

The pattern: LLMs take shortcuts they cannot validate. When there's a plausible-looking column (`O_TOTALPRICE`), they grab it. When there isn't, they improvise — often catastrophically. This is the production risk: **silent errors that look correct.**

### Step 5: The Fix — Semantic Views

A **Semantic View** is a Snowflake object that formally defines the business meaning of your data:

- **Metric definitions** — exact formulas (e.g., `revenue = SUM(ext_price * (1 - discount))`)
- **Join paths** — which tables connect and via which keys
- **Synonyms** — so "revenue", "sales", "net revenue" all resolve to the same metric
- **Dimensions** — categorical attributes for grouping (segment, region, year)

Think of it as a **contract between your business logic and the AI**. It's a native Snowflake object with RBAC, sharing, catalog integration, and governance.

Run the **Step 5 cell** in the notebook to create the production Semantic View. Notice the `WITH SYNONYMS` and `COMMENT` fields — these encode business knowledge that cannot be inferred from column names alone, and are what make Cortex Analyst accurate. You should see:

```
Semantic View created: AI_WORKSHOP_DB.ANALYTICS.TPCH_ORDER_ANALYTICS

  Metrics encoded:
    total_revenue       = SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT))
    total_cost_of_goods = SUM(PS_SUPPLYCOST * L_QUANTITY)
    total_profit        = revenue - COGS
```

### Step 6: Cortex Analyst — The Production Approach

**Cortex Analyst** is Snowflake's managed text-to-SQL service:

1. Reads the **Semantic View** definition (metrics, dimensions, joins, synonyms)
2. Uses state-of-the-art LLMs (automatically selected) to interpret the question
3. Generates SQL that **follows your metric definitions exactly** — no guessing

The key difference: **the AI has access to your business logic**, not just column names.

Run the **Step 6 cell** to connect `RAG_App` to the Semantic View and ask the same Revenue and COGS questions via `app.query_data()`. Both match the gold standard — every time, deterministically.

| | Naive LLM | Cortex Analyst + Semantic View |
|---|-----------|-------------------------------|
| **Revenue** | Used `O_TOTALPRICE` — **+4% inflated** (includes tax) | Correct formula every time |
| **COGS** | Computed revenue, labeled it "cost" — **2.8× too high** | Correct formula every time |
| SQL errors? | None — both queries ran fine | None |
| Deterministic? | No — varies between runs | Yes — same SQL every time |

Your `RAG_App` now handles both data types:

```python
app.query("What is Cortex Search?")        # Cortex Search — unstructured docs
app.query_data("Revenue by segment?")      # Cortex Analyst — structured tables
```

Run the **bonus cell** to ask your own question against the Semantic View.

<!-- ------------------------ -->
## Conclusion & Resources


### What You Built

In this lab you built two fully functional AI applications from scratch on a Snowflake trial account:

- A **RAG application** backed by Cortex Search that retrieves grounded answers from a text corpus — with no hallucination outside your data
- A **production Text-to-SQL interface** backed by a Semantic View that encodes correct metric formulas (revenue, COGS, profit) and Cortex Analyst for deterministic, governed queries
- Used **CoCo** throughout to generate complex SQL and Python from natural language, cutting development time on the hardest parts of the lab

### What You Learned

- How to call LLMs with `COMPLETE` in Python and SQL
- The RAG architecture — retrieval → grounding → generation — and why it prevents hallucination
- How to chunk text with `SPLIT_TEXT_RECURSIVE_CHARACTER` and build a `CORTEX SEARCH SERVICE`
- How to write a reusable RAG Python class using `snowflake.core` and `snowflake.cortex`
- How to use CoCo to generate Snowflake-idiomatic SQL and Python from descriptions
- How to evaluate application quality with Snowsight Evaluations
- Why naive LLM text-to-SQL fails silently — and the exact failure modes (revenue inflated by tax, COGS wrong by 2.8×)
- How Semantic Views encode business metric definitions as a contract between your data and the AI
- How to use Cortex Analyst with a Semantic View for deterministic, production-grade Text-to-SQL

### Next Steps

- **Scale your corpus:** Upload real PDFs to a Snowflake Stage and use `PARSE_DOCUMENT` to extract and chunk their contents
- **Add a UI:** Wrap your `RAG_App` in a [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit) app for a shareable chat interface
- **Extend the Semantic View:** Add your own tables, define custom metrics, and expand synonyms to serve your specific business domain using [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- **Combine both:** Build a unified agent that routes questions to Cortex Search or Cortex Analyst based on whether the question is about documents or structured tables

### Related Resources

- [Snowflake Cortex Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [CoCo (Snowflake Copilot)](https://docs.snowflake.com/en/user-guide/snowflake-copilot)
- [Getting Started with Cortex Agents — Quickstart](https://quickstarts.snowflake.com/guide/getting_started_with_cortex_agents)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

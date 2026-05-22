author: Rida Safdar
id: accelerate-app-dev-cortex-code
language: en
summary: Build end-to-end AI applications on your Snowflake data using Cortex Complete, Cortex Search, and Cortex Code — no data movement required.
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration,snowflake-site:taxonomy/snowflake-feature/cortex-code
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Building AI Applications with Snowflake Cortex: RAG, Text-to-SQL & Cortex Code

<!-- ------------------------ -->
## Overview

In this hands-on lab you will go from data consumer to AI builder. Starting from a fresh Snowflake trial account — with no uploads, no external APIs, and no data movement — you will build two AI-powered applications:

1. A **Retrieval-Augmented Generation (RAG)** app that answers questions from a corpus of text documents
2. A **Text-to-SQL** interface that answers business questions from structured tables in plain English

Along the way, you will use **Cortex Code**, Snowflake's AI coding assistant, to write and accelerate the most complex parts of the lab.

### Prerequisites
- A Snowflake Trial Account (any cloud region). [Sign up here](https://signup.snowflake.com/)
- Basic familiarity with SQL
- No Python experience required for Module 1; basic Python familiarity helps for Module 2

### What You'll Learn
- How to call large language models (LLMs) directly in Snowflake using `CORTEX.COMPLETE`
- The architecture behind Retrieval-Augmented Generation (RAG) and why it prevents hallucinations
- How to build a production RAG app using `CORTEX SEARCH SERVICE` and a Snowflake Notebook
- How to use Cortex Code to generate complex Snowflake SQL and Python from plain English
- How to evaluate your AI application's response quality with Snowsight Evaluations

### What You'll Need
- A Snowflake Trial Account — [signup.snowflake.com](https://signup.snowflake.com/)
- A web browser (Chrome or Firefox recommended)
- No local software installation required

### What You'll Build
- A **text corpus pipeline** — ingest, chunk, and index text documents inside Snowflake
- A **Cortex Search Service** that supports hybrid keyword + semantic search
- A **Python RAG application** that retrieves context and generates grounded answers
- A reusable **prompt pattern** for Text-to-SQL using sample data pre-loaded in your trial account

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

1. In Snowsight, navigate to **Projects > Legacy Notebooks**
2. Click the **⋮** menu (top right) and select **Import .ipynb file**
3. Upload `accelerate-app-dev-cortex-code.ipynb`
4. Set **Database** to `AI_WORKSHOP_DB` and **Schema** to `RAG_DATA`
5. Set **Warehouse** to `WORKSHOP_WH`
6. Click **Create**

### Step 2: Run the Setup Cell

Before you run the setup cell, from the 'Packages' drop down on the top right, install the following: 'snowflake.core'. You will be prompted to restart the session. 

Now run The setup code cell in the notebook imports all libraries and sets the active database, schema, and warehouse. **Run this cell before any other.** You should see:

```
Session ready.
  Database : AI_WORKSHOP_DB
  Schema   : RAG_DATA
  Warehouse: WORKSHOP_WH
```

If you see an error, confirm the SQL Worksheet setup steps completed successfully.

> **Tip:** Run cells individually to follow along with the lab guide.

<!-- ------------------------ -->
## Cortex Code: Your AI Pair Programmer

Before we write a single line of lab code, take 10 minutes to meet the tool that will accelerate every step that follows.

**Cortex Code** is Snowflake's AI coding assistant. It understands Snowflake's full API surface — every SQL function, DDL syntax, Cortex primitive, and Snowpark class — and it generates runnable code from plain-English descriptions. It is available directly in Snowsight on all trial accounts.

### Opening Cortex Code in Snowsight

Navigate back to your SQL Worksheet, look for the icon (sparkle ✦) in the right side. Click it to open the Cortex Code chat panel.

> **Tip:** Cortex Code is context-aware. It can see your active database, schema, and table names, so your prompts don't need to be overly specific.

### Demo 1: Generate Setup SQL

In the Cortex Code chat panel, type the following prompt exactly:

```
Create an internal stage in the RAG_DATA schema called DOCS_STAGE with directory
tables enabled and Snowflake SSE encryption.
```

Cortex Code will return the SQL below. Accept it and run the command in your worksheet:

```sql
CREATE OR REPLACE STAGE AI_WORKSHOP_DB.RAG_DATA.DOCS_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```
You should see the text "Stage DOCS_STAGE created with directory tables enabled and Snowflake SSE encryption."

> **What just happened?** You described what you wanted in plain English, and Cortex Code produced syntactically correct, Snowflake-idiomatic SQL — including the less-obvious `DIRECTORY` and `ENCRYPTION` parameters. Throughout this lab, use Cortex Code whenever you encounter a function or DDL pattern you haven't seen before.

### Demo 2: Explore an Unknown Function

Now try this prompt in the Cortex Code panel:

```
How do I use SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER to chunk text into
pieces of 1500 characters with 200-character overlap?
```

Cortex Code will return a working example of SQL functions with explanation. Keep this pattern in mind — you'll use this exact function in Module 2.

### Key Principle

> Use Cortex Code to **generate the hard parts** and **understand why** — don't just accept output blindly. The best workflow is: describe → generate → read → run → iterate.

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
print(cortex.complete(model, prompt))
```

You just called a hosted LLM running inside your Snowflake account. No API key, no data leaving your security perimeter.

Run the **model comparison cell** below it to contrast `mistral-7b`, `snowflake-arctic`, and `llama3-70b` side by side.

### Step 2: The Hallucination Problem

Run the **Step 2 cell**. The model is asked for a specific private financial figure it cannot know:

```python
response = cortex.complete('mistral-7b', 'What is the exact revenue figure for Snowflake in Q4 FY26?')
print(response)
```

The model guesses, hedges, or states something unverifiable. This is the **hallucination problem** — and it is why RAG exists.

### Step 3: RAG — Grounding Fixes Hallucination

The solution is to **retrieve** relevant facts from your own data and **inject** them into the prompt as context. The LLM then answers using only what you provided.

Run the **Step 3 cell**. It pulls the top 5 customers by revenue live from `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` — the TPC-H order dataset pre-loaded in every trial account — and grounds the LLM with that data:

```python
top_customers = session.sql("""
    SELECT
        c.C_NAME,
        c.C_MKTSEGMENT,
        ROUND(SUM(o.O_TOTALPRICE), 0)       AS TOTAL_SPENT,
        COUNT(DISTINCT o.O_ORDERKEY)         AS NUM_ORDERS
    FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER c
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS   o ON c.C_CUSTKEY = o.O_CUSTKEY
    GROUP BY 1, 2
    ORDER BY TOTAL_SPENT DESC
    LIMIT 5
""").to_pandas()

# ... formats as context string and asks a grounded question
```

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

Real documents are too long to fit in a single LLM prompt. We break them into overlapping chunks so the search index can return the most relevant piece. Cortex Search indexes chucnks, not the whole document. The search service finds the most relevant chunk for a question. If you indexed full documents, you'd retrieve a wall of text (much of it irrelevant) and would send it all to the LLM. Precision in this case improves answer quality and provides you a higher groundedness score (covered later in this lab).

> **Cortex Code prompt to try first:**  
> *"Chunk the content column in FEATURE_DOCS into 1500-character pieces with 200-character overlap using SPLIT_TEXT_RECURSIVE_CHARACTER and store in CHUNKED_DOCS"*

Click to run the command provided by Cortex Code. You should see it created 15 chunks across 15 features with each each at most 1500 characters and a 200-character overlap between consecutive chunks.


> Our documents are short so most produce a single chunk. With real PDFs or long articles, you would see many more chunks per source document.

### Step 2: Create the Cortex Search Service

A single DDL statement creates a fully managed hybrid search index — Snowflake handles embedding, vectorization, and retrieval automatically.

> **Cortex Code prompt to try first:**  
> *"Create a Cortex Search Service called FEATURE_SEARCH_SERVICE on CHUNKED_DOCS.chunk_text, with feature_name as an attribute, using snowflake-arctic-embed-l-v2.0 and a 1-minute target lag"*

Click to run the command provided by Cortex Code. The FEATURE_SEARCH_SERVICE is created. The service will index automaticall, but may take a few minutes to become active. 

Ask Cortex Code after a few minutes: 
> *"Is the service active and ready to query?"*

If you see that it is active for both indexing and serving with all 15 rows indexed and ready to query, you can proceed to the next step. 

### Step 3: Build the RAG Application

Run the **Step 3 cell** in the notebook to define and instantiate `RAG_App`.

### Step 4: Test Your Application

Run the **Step 4 cell** in the notebook. It asks 5 test questions against your RAG app and prints each answer. Each response is scoped entirely to your 15-row corpus — the application cannot hallucinate beyond what you gave it. Note this cell may take a few minutes to run. 

### Step 5: Evaluate Response Quality

Run the **Evaluate Response Quality** quality step in the notebook. 

This uses Cortex LLM to score the quality of the your RAG app's answers. For each test question, the service calls retrieve_context() to fetch the top 3 matching chunks from Cortex Search. Then, it calls generate_answer() to send those chunks and the question to mistral-large2 to product an answer. It score on three metrics: groundedness, context relevance, and answer relevance on a scale from 0.0 to 1.0 asking the LLM to judge. 

A well-tuned RAG app should score **> 0.8 on all metrics**. If Groundedness is low, tighten the prompt instructions. If Context Relevance is low, your search service or chunking needs improvement. If groundedness is low, your prompt isn't constraining the model tightly enough. If answer relevance is low, the model is retrieving the right context, but generating poor answers. 

<!-- ------------------------ -->
## Module 3 – Text-to-SQL with Sample Data

This module uses `SNOWFLAKE_SAMPLE_DATA` — the TPC-H order dataset pre-loaded in every trial account — as structured data for a Text-to-SQL interface. All steps run from Python cells in the notebook; no worksheet switching is needed.

### Step 1: Explore the Schema

Run the **schema exploration cell** in the Module 3 section of the notebook. It queries `INFORMATION_SCHEMA` via `session.sql()` and prints the table list:

```
Tables in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1:
 CUSTOMER, LINEITEM, NATION, ORDERS, PART, PARTSUPP, REGION, SUPPLIER
```

### Step 2: Build and Run Text-to-SQL

Run the **`ask_structured_data` cell**. It:
1. Sends a natural-language question + the schema description to `CORTEX.COMPLETE`
2. Extracts the generated SQL
3. Executes it against `SNOWFLAKE_SAMPLE_DATA` via `session.sql()` and returns a DataFrame

> **Note:** For production accuracy, use [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) with a YAML semantic model.

Finally, run the **additional questions cell** to test three more questions — all from the same notebook, no context switching.


<!-- ------------------------ -->
## Conclusion & Resources


### What You Built

In this lab you built two fully functional AI applications from scratch on a Snowflake trial account:

- A **RAG application** backed by Cortex Search that retrieves grounded answers from a text corpus — with no hallucination outside your data
- A **Text-to-SQL interface** that translates plain-English questions into executable Snowflake queries against real sample data
- Used **Cortex Code** throughout to generate complex SQL and Python from natural language, cutting development time on the hardest parts of the lab

### What You Learned

- How to call LLMs with `CORTEX.COMPLETE` in Python and SQL
- The RAG architecture — retrieval → grounding → generation — and why it prevents hallucination
- How to chunk text with `SPLIT_TEXT_RECURSIVE_CHARACTER` and build a `CORTEX SEARCH SERVICE`
- How to write a reusable RAG Python class using `snowflake.core` and `snowflake.cortex`
- How to use Cortex Code to generate Snowflake-idiomatic SQL and Python from descriptions
- How to evaluate application quality with Snowsight Evaluations

### Next Steps

- **Scale your corpus:** Upload real PDFs to a Snowflake Stage and use `PARSE_DOCUMENT` to extract and chunk their contents
- **Add a UI:** Wrap your `RAG_App` in a [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit) app for a shareable chat interface
- **Production Text-to-SQL:** Explore [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) with a YAML semantic model for business-grade accuracy
- **Combine both:** Build a unified agent that routes questions to Cortex Search or Cortex Analyst based on whether the question is about documents or structured tables

### Related Resources

- [Snowflake Cortex Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Cortex Code (Snowflake Copilot)](https://docs.snowflake.com/en/user-guide/snowflake-copilot)
- [Getting Started with Cortex Agents — Quickstart](https://quickstarts.snowflake.com/guide/getting_started_with_cortex_agents)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

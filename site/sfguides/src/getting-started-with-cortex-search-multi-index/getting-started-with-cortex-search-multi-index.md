author: Lucas Galan
id: getting-started-with-cortex-search-multi-index
language: en
summary: Learn how to use Cortex Search multi-index to solve retail catalog retrieval — combining exact brand recall and semantic intent search in a single service. No fan-out, no manual reranking.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-search
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Cortex Search Multi-Index for Retail Catalog Retrieval
<!-- ------------------------ -->
## Overview

**Solve the two hardest search problems in retail — exact brand recall and semantic intent — in a single Cortex Search service with four indexes.**

This guide walks you step-by-step through building a production-ready product catalog search using **Cortex Search multi-index**: a single service that simultaneously maintains BM25 keyword indexes over structured columns (brand, item name, subcategory) and a vector semantic index over free-text descriptions. We use **SNOWFIELD PRO**, a synthetic winter sports ecommerce catalog of 1,040 products, as the hero example.

> aside positive
> **Download the assets for this quickstart:**
> - [setup_snowfield_pro_search.sql](https://github.com/Snowflake-Labs/sfguides/blob/master/site/sfguides/src/getting-started-with-cortex-search-multi-index/assets/setup_snowfield_pro_search.sql) — Full SQL worksheet (setup + optional AI enrichment + all queries)
>
> Open the worksheet alongside this guide in a Snowflake worksheet tab and run sections in order.

At a high level:

-   **Keyword-only search** finds exact brand names but fails on intent queries like _"warm boot for icy terrain"_
-   **Vector-only search** handles intent queries beautifully but loses exact brand name recall (e.g. _"ridgeline"_ returns ski pants instead of Ridgeline brand gear)
-   **Multi-index search** solves both problems in a single service — one DDL, one call, one reranker-fused result list

### What You'll Need

-   A Snowflake account with the SYSADMIN (or equivalent) role
-   A Snowflake warehouse (SMALL or larger)
-   Basic familiarity with SQL
-   _(Optional)_ Python 3.9+ with the `snowflake-ml-python` SDK — only required for the optional Python SDK section

### What You'll Learn

-   Why keyword-only and vector-only search each fail in different ways on retail catalogs
-   How Cortex Search `TEXT INDEXES` and `VECTOR INDEXES` work within a single service
-   How to construct the `SEARCH_TEXT` column for maximum retrieval coverage
-   How to query all indexes simultaneously from SQL using `SNOWFLAKE.CORTEX.SEARCH_PREVIEW()`
-   How to derive category breakdowns from result attributes (not from separate services)
-   _(Optional)_ How to use `SNOWFLAKE.CORTEX.COMPLETE()` to enrich product descriptions with AI before indexing
-   _(Optional)_ How to query with the Python SDK using `multi_index_query`
-   _(Optional)_ How to build a full-stack demo app around Cortex Search

### What You'll Build

-   A product catalog table with a pre-computed `SEARCH_TEXT` column
-   A single **Cortex Search service** with three TEXT indexes and one VECTOR index
-   Working SQL queries using `SEARCH_PREVIEW` that demonstrate brand recall, intent search, attribute filtering, and category breakdowns
-   _(Optional)_ AI-enriched product descriptions using `SNOWFLAKE.CORTEX.COMPLETE()` for deeper semantic recall
-   _(Optional)_ A Python query function using `multi_index_query` that hits all four indexes at once
-   _(Optional)_ A live SNOWFIELD PRO demo app with debounced auto-search

<!-- ------------------------ -->
## The Retail Catalog Retrieval Problem

**The most common search failure mode in retail is not a technology limitation — it is choosing one retrieval strategy when the catalog needs two.**

Consider a winter sports catalog with 1,040 products across Equipment, Apparel, Protection, and Accessories. Users issue two fundamentally different query types:

### Query Type 1 — Brand Name Lookup

The user knows exactly what they want:

```
"ridgeline"
"black crows skis"
"marker kingpin"
```

These are **exact match queries**. BM25 keyword search excels here — a brand name is a literal string, and BM25 will surface it at rank 1. But a pure embedding model struggles: brand names are proper nouns with little semantic neighbourhood in the training corpus. A vector-only search for _"ridgeline"_ may return Dynastar Vertical ski pants (the word "ridgeline" appears in the description) ranked above actual Ridgeline brand products.

### Query Type 2 — Intent / Brand Voice

The user knows what they need but not which brand:

```
"warm waterproof jacket for off-piste skiing"
"protective gear for a beginner on groomed runs"
"lightweight boot for touring in variable snow"
```

These are **semantic queries**. A vector index over descriptive text handles this naturally — the embedding captures the intent and matches products even when no keyword overlaps. BM25 would return zero results for most of these queries.

### Why Single-Strategy Search Fails

| Search Strategy | Brand Recall | Intent Recall | Root Cause |
|----------------|-------------|--------------|------------|
| BM25 keyword-only | ✓ High | ✗ Low | Requires exact keyword match |
| Vector-only | ✗ Low | ✓ High | Brand names sparse in embedding space |
| Multi-index | ✓✓ High | ✓✓ High | BM25 + vector signals fused by reranker |

The solution is not to build two services and fan out — that introduces synchronization complexity, duplicate infrastructure, and manual reranking. The solution is **Cortex Search multi-index**: a single service with multiple indexed columns, queried in one call, results fused by the built-in reranker.

<!-- ------------------------ -->
## Understanding Cortex Search Multi-Index

**Multi-index is not fan-out. It is multiple indexed columns within a single service.**

Snowflake Cortex Search supports two index types that can coexist in a single service:

### TEXT INDEXES

BM25 keyword indexes over one or more string columns. Each column gets its own inverted index. Useful for:

-   Exact brand name recall
-   Product name keyword match
-   Category and subcategory lookup
-   SKU and model number search

### VECTOR INDEXES

Dense embedding indexes over a single text column, using a Snowflake Arctic embedding model. Useful for:

-   Semantic / intent queries
-   Brand voice and description matching
-   Synonym and paraphrase handling
-   Cross-lingual retrieval

### The `multi_index_query` Parameter

When you call `svc.search()` with a `multi_index_query` dict, the SDK routes your query to all specified indexed columns simultaneously. The built-in reranker fuses the signals and returns a single ranked list:

```python
response = svc.search(
    multi_index_query={
        "BRAND":       [{"text": query}],
        "ITEM_NAME":   [{"text": query}],
        "SUBCATEGORY": [{"text": query}],
        "SEARCH_TEXT": [{"text": query}],
    },
    columns=["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", ...],
    limit=20,
)
```

> **NOTE:** Each key in `multi_index_query` must correspond to a column declared in `TEXT INDEXES` or `VECTOR INDEXES` in the service DDL. If a column is not indexed, the SDK will raise an error.

### What Multi-Index Is NOT

Multi-index is **not** a fan-out pattern across four separate services. You do not need:

-   A separate EQUIPMENT_SEARCH service
-   A separate APPAREL_SEARCH service
-   A `ThreadPoolExecutor` to parallelize requests
-   Manual result merging or reranking code

One service, one call, one result list. The reranker is built in.

<!-- ------------------------ -->
## Setting Up Your Snowflake Environment

**All SQL in this guide runs in a single worksheet. Expected setup time: under 5 minutes.**

### Step 1 — Create the Database and Warehouse

```sql
-- Create the database and schemas
CREATE DATABASE IF NOT EXISTS CATALOG_SEARCH_DB;
CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.DATA;
CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.APP;

-- Create a dedicated warehouse for the search service
CREATE WAREHOUSE IF NOT EXISTS CATALOG_SEARCH_WH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'Warehouse for Cortex Search service and queries';

USE DATABASE CATALOG_SEARCH_DB;
USE SCHEMA DATA;
USE WAREHOUSE CATALOG_SEARCH_WH;
```

### Step 2 — Verify Your Role

```sql
-- Confirm you are using SYSADMIN or a role with CREATE CORTEX SEARCH SERVICE privilege
SELECT CURRENT_ROLE();

-- If needed, switch role:
-- USE ROLE SYSADMIN;
```

> **NOTE:** Creating a Cortex Search Service requires the `CREATE CORTEX SEARCH SERVICE` privilege on the target schema. SYSADMIN has this by default in most accounts. If you are using a custom role, run `GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA APP TO ROLE <your_role>`.

<!-- ------------------------ -->
## Preparing the Product Catalog

**The key to effective multi-index retrieval is a well-constructed `SEARCH_TEXT` column that encodes everything a customer might ask about a product.**

### Step 1 — Create the PRODUCTS Table

```sql
CREATE OR REPLACE TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS (
    PRODUCT_ID      NUMBER AUTOINCREMENT PRIMARY KEY,
    ITEM_NAME       VARCHAR(500),
    BRAND           VARCHAR(200),
    CATEGORY        VARCHAR(100),     -- Equipment | Apparel | Protection | Accessories
    SUBCATEGORY     VARCHAR(200),
    DISCIPLINE      VARCHAR(100),     -- Alpine | Freeride | Nordic | Touring | Park
    SKILL_LEVEL     VARCHAR(50),      -- Beginner | Intermediate | Advanced | Expert
    GENDER          VARCHAR(50),
    PRICE           NUMBER(10, 2),
    PRODUCT_TYPE    VARCHAR(100),
    FLEX_RATING     VARCHAR(50),
    DESCRIPTION     VARCHAR(2000),
    SEARCH_TEXT     VARCHAR(4000)
);
```

### Step 2 — Load the Sample Catalog

The downloadable SQL worksheet (Section 3) contains 30 representative product rows across Equipment, Apparel, Protection, and Accessories. Run that INSERT block now, or substitute your own catalog data.

> **NOTE:** In production, this is your existing catalog table. You do not need to load sample data — just point the search service at your real PRODUCTS table.

### Step 3 — Build the SEARCH_TEXT Column

The `SEARCH_TEXT` column concatenates every attribute a user might describe — brand, product name, subcategory, discipline, skill level, gender, and the full description. This gives the vector index maximum coverage.

```sql
UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET SEARCH_TEXT = TRIM(
    COALESCE(BRAND,        '') || ' ' ||
    COALESCE(ITEM_NAME,    '') || ' ' ||
    COALESCE(SUBCATEGORY,  '') || ' ' ||
    COALESCE(DISCIPLINE,   '') || ' ' ||
    COALESCE(SKILL_LEVEL,  '') || ' ' ||
    COALESCE(GENDER,       '') || ' ' ||
    COALESCE(DESCRIPTION,  '')
);
```

> **NOTE:** `SEARCH_TEXT` is the column that gets the vector index. It should be as descriptive as possible. If you run the optional AI enrichment section next, it will rewrite DESCRIPTION before you build this column — giving the vector index richer, more searchable content.

### Step 4 — Verify the Data

```sql
-- Check row count and sample SEARCH_TEXT content
SELECT COUNT(*) AS total_products FROM CATALOG_SEARCH_DB.DATA.PRODUCTS;

SELECT PRODUCT_ID, BRAND, ITEM_NAME, CATEGORY,
       LEFT(SEARCH_TEXT, 200) AS search_text_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;
```

Expected output: catalog rows with a `SEARCH_TEXT` preview that reads naturally (e.g. _"Ridgeline Freeride Jacket Outerwear Freeride Advanced Male 449.00 3-layer Gore-Tex shell with powder skirt..."_).

<!-- ------------------------ -->
## (Optional) Enrich Product Descriptions with Cortex AI

**Short hand-written descriptions limit semantic recall. `SNOWFLAKE.CORTEX.COMPLETE()` rewrites every product description in the natural language your customers actually use.**

### Why Enrich Before Indexing?

The vector index encodes the semantic meaning of `SEARCH_TEXT`. If descriptions are terse (e.g. _"Gore-Tex shell with powder skirt"_), they miss the synonyms, use cases, and natural language patterns customers type into search:

-   _"best jacket for deep powder days"_
-   _"waterproof shell for aggressive off-piste skiing"_
-   _"breathable ski jacket that works on the uptrack"_

An LLM rewrites each description as a product page would — richer, more natural, search-optimised. This enrichment happens once at load time and is then indexed into the vector embedding for the lifetime of the product.

### Step 1 — Preview Enrichment on 3 Rows

Always preview before committing to a mass update:

```sql
SELECT
    PRODUCT_ID,
    ITEM_NAME,
    BRAND,
    LEFT(DESCRIPTION, 100)                     AS original_description,
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large2',
        CONCAT(
            'Write a rich, engaging product description for an online ski shop catalog. ',
            'Use natural language a customer would search for. Mention key use cases, ',
            'target skill level, and standout features. Keep it under 150 words.\n\n',
            'Product: ',     ITEM_NAME,    '\n',
            'Brand: ',       BRAND,        '\n',
            'Category: ',    SUBCATEGORY,  '\n',
            'Discipline: ',  DISCIPLINE,   '\n',
            'Skill Level: ', SKILL_LEVEL,  '\n',
            'Gender: ',      GENDER,       '\n',
            'Original description: ', DESCRIPTION
        )
    )                                           AS enriched_description
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 3;
```

Compare the `original_description` and `enriched_description` columns. The enriched version should feel like a product page — actionable, descriptive, and search-friendly.

### Step 2 — Preserve Originals (Recommended)

```sql
-- Add a backup column before overwriting
ALTER TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS
    ADD COLUMN DESCRIPTION_ORIGINAL VARCHAR(2000);

UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
    SET DESCRIPTION_ORIGINAL = DESCRIPTION;
```

### Step 3 — Enrich All Product Descriptions

```sql
-- Cost: ~1-2 credits per 1,000 rows with mistral-large2
-- Runtime: ~30-60 sec for 30 rows | ~3-5 min for 1,040 rows
UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET DESCRIPTION = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    CONCAT(
        'Write a rich, engaging product description for an online ski shop catalog. ',
        'Use natural language a customer would search for. Mention key use cases, ',
        'target skill level, and standout features. Keep it under 150 words.\n\n',
        'Product: ',     ITEM_NAME,    '\n',
        'Brand: ',       BRAND,        '\n',
        'Category: ',    SUBCATEGORY,  '\n',
        'Discipline: ',  DISCIPLINE,   '\n',
        'Skill Level: ', SKILL_LEVEL,  '\n',
        'Gender: ',      GENDER,       '\n',
        'Original description: ', DESCRIPTION
    )
);
```

### Step 4 — Rebuild SEARCH_TEXT with Enriched Descriptions

Now that DESCRIPTION is richer, rebuild the `SEARCH_TEXT` column so the vector index captures the full enriched content:

```sql
UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET SEARCH_TEXT = TRIM(
    COALESCE(BRAND,        '') || ' ' ||
    COALESCE(ITEM_NAME,    '') || ' ' ||
    COALESCE(SUBCATEGORY,  '') || ' ' ||
    COALESCE(DISCIPLINE,   '') || ' ' ||
    COALESCE(SKILL_LEVEL,  '') || ' ' ||
    COALESCE(GENDER,       '') || ' ' ||
    COALESCE(DESCRIPTION,  '')
);

-- Verify the enriched SEARCH_TEXT preview
SELECT PRODUCT_ID, BRAND, ITEM_NAME,
       LEFT(SEARCH_TEXT, 250) AS search_text_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;
```

> **NOTE:** After completing this section, proceed to "Creating the Multi-Index Search Service". The service will index your enriched `SEARCH_TEXT` automatically.

<!-- ------------------------ -->
## Creating the Multi-Index Search Service

**One DDL statement creates all four indexes and starts the indexing pipeline.**

### The Service DDL

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH
    TEXT INDEXES   BRAND, ITEM_NAME, SUBCATEGORY
    VECTOR INDEXES SEARCH_TEXT(model='snowflake-arctic-embed-l-v2.0')
    ATTRIBUTES     PRODUCT_ID, ITEM_NAME, BRAND, CATEGORY, SUBCATEGORY,
                   SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING
    WAREHOUSE  = CATALOG_SEARCH_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT
            PRODUCT_ID,
            SEARCH_TEXT,
            ITEM_NAME,
            BRAND,
            CATEGORY,
            SUBCATEGORY,
            SKILL_LEVEL,
            DISCIPLINE,
            GENDER,
            PRICE,
            PRODUCT_TYPE,
            FLEX_RATING
        FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
    );
```

### What Each Clause Does

| Clause | Purpose |
|--------|---------|
| `TEXT INDEXES BRAND, ITEM_NAME, SUBCATEGORY` | Creates BM25 indexes on three structured columns for exact keyword match |
| `VECTOR INDEXES SEARCH_TEXT(model=...)` | Creates a dense embedding index on the concatenated description column |
| `ATTRIBUTES ...` | Columns returned with each result (not indexed — used for display/filtering) |
| `WAREHOUSE` | Compute used for initial indexing and incremental refresh |
| `TARGET_LAG = '1 hour'` | Maximum time between source table update and index refresh |

### Verify Service Status

```sql
-- Check that the service has indexed your rows
SHOW CORTEX SEARCH SERVICES IN SCHEMA CATALOG_SEARCH_DB.APP;

-- Detailed status
DESCRIBE CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH;
```

Wait for `indexing_state` to show `READY` before running queries. For 1,040 rows this typically takes 2–5 minutes.

> **NOTE:** The `TARGET_LAG` setting controls how frequently the service checks for new or updated rows. For a demo/dev catalog that rarely changes, `'1 hour'` is appropriate. For a live production catalog, use `'1 minute'` or `'30 seconds'`.

<!-- ------------------------ -->
## Querying with SEARCH_PREVIEW (SQL)

**`SNOWFLAKE.CORTEX.SEARCH_PREVIEW()` is the SQL interface for Cortex Search — query all four indexes from a worksheet, a Streamlit app, or any SQL-capable tool.**

The function takes the fully-qualified service name and a JSON payload with `query`, `columns`, an optional `filter`, and `limit`. Results come back as a JSON object with a `results` array.

### Test 1 — Brand Name Lookup (exercises TEXT INDEX on BRAND)

```sql
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "ridgeline",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "SUBCATEGORY", "PRICE"],
            "limit": 10
        }'
    )
) AS search_results;
```

Expected: all Ridgeline brand products surface at the top of the ranked list, regardless of whether "ridgeline" appears in their description. This is the TEXT INDEX on BRAND at work.

### Test 2 — Intent / Semantic Query (exercises VECTOR INDEX on SEARCH_TEXT)

```sql
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "warm waterproof jacket for off-piste skiing",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "PRICE"],
            "limit": 10
        }'
    )
) AS search_results;
```

Expected: freeride and outerwear products surface at the top — even for products whose descriptions use different words than the query. This is the VECTOR INDEX on SEARCH_TEXT at work.

### Test 3 — Attribute Filter (server-side filtering by SKILL_LEVEL)

```sql
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "protective gear",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "SKILL_LEVEL", "PRICE"],
            "filter": {"@eq": {"SKILL_LEVEL": "Beginner"}},
            "limit": 10
        }'
    )
) AS search_results;
```

> **NOTE:** The `filter` clause is applied server-side before ranking — only products matching the filter are scored and returned. This is more efficient than fetching all results and filtering in your application.

### Test 4 — Category Breakdown (grouping on result attributes)

This query demonstrates how a single service can power a faceted UI — the category breakdown is derived from the `CATEGORY` attribute on each result, not from multiple services:

```sql
WITH raw AS (
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
            '{
                "query": "ridgeline",
                "columns": ["CATEGORY"],
                "limit": 100
            }'
        )
    ) AS results
),
flattened AS (
    SELECT f.value:CATEGORY::STRING AS category
    FROM raw, LATERAL FLATTEN(input => results:results) f
)
SELECT category, COUNT(*) AS result_count
FROM flattened
GROUP BY 1
ORDER BY 2 DESC;
```

Expected output:

```
CATEGORY       RESULT_COUNT
Equipment      7
Apparel        4
Protection     2
Accessories    1
```

One service. One query. Category breakdown from result attributes, not from four separate services.

> **NOTE:** `SEARCH_PREVIEW` is the fastest path to testing Cortex Search from SQL. For production applications, the Python SDK's `svc.search()` method with `multi_index_query` returns structured Python objects and gives you full multi-index control. See the optional SDK section below.

<!-- ------------------------ -->
## (Optional) Querying with the Python SDK

**A single Python function replaces the fan-out pattern, the merge logic, and the manual reranker.**

### Install the Snowflake Python SDK

```bash
pip install snowflake-ml-python
```

### Connect and Retrieve the Service

```python
from snowflake.ml.utils.connection_params import SnowflakeLoginOptions
from snowflake.core import Root

# Connect using your connection config
connection_params = SnowflakeLoginOptions("your_connection_name")
root = Root(snowflake.connector.connect(**connection_params))

svc = (
    root
    .databases["CATALOG_SEARCH_DB"]
    .schemas["APP"]
    .cortex_search_services["PRODUCT_SEARCH"]
)
```

### The Query Function

```python
SEARCH_COLUMNS = [
    "PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY",
    "SUBCATEGORY", "SKILL_LEVEL", "DISCIPLINE",
    "GENDER", "PRICE", "PRODUCT_TYPE", "FLEX_RATING",
]

def multi_search(query: str, limit: int = 20) -> dict:
    """
    Query the PRODUCT_SEARCH service across all four indexes simultaneously.
    Returns a dict with 'results' (list) and category_breakdown (dict).
    """
    response = svc.search(
        multi_index_query={
            "BRAND":       [{"text": query}],   # TEXT INDEX — exact brand recall
            "ITEM_NAME":   [{"text": query}],   # TEXT INDEX — product name match
            "SUBCATEGORY": [{"text": query}],   # TEXT INDEX — category keyword
            "SEARCH_TEXT": [{"text": query}],   # VECTOR INDEX — semantic intent
        },
        columns=SEARCH_COLUMNS,
        limit=limit,
    )

    results = response.results

    # Derive category breakdown from the CATEGORY attribute on each result
    # (not from which service the result came from — there is only one service)
    category_counts = {}
    for r in results:
        cat = r.get("CATEGORY", "Unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "results": results,
        "total": len(results),
        "category_breakdown": category_counts,
    }
```

### Testing the Query

```python
# Test 1 — brand name lookup (relies on TEXT INDEX: BRAND)
result = multi_search("ridgeline")
print(f"Total results: {result['total']}")
print(f"Category breakdown: {result['category_breakdown']}")
for r in result['results'][:5]:
    print(f"  {r['BRAND']} — {r['ITEM_NAME']} ({r['CATEGORY']})")

# Test 2 — intent query (relies on VECTOR INDEX: SEARCH_TEXT)
result = multi_search("warm waterproof jacket for off-piste skiing")
print(f"\nTotal results: {result['total']}")
for r in result['results'][:5]:
    print(f"  {r['BRAND']} — {r['ITEM_NAME']} ({r['SUBCATEGORY']})")
```

Expected output for `"ridgeline"`:

```
Total results: 12
Category breakdown: {'Equipment': 5, 'Apparel': 4, 'Protection': 2, 'Accessories': 1}
  Ridgeline — Freeride Jacket (Apparel)
  Ridgeline — Powder Skis Pro (Equipment)
  Ridgeline — All-Mountain Helmet (Protection)
  ...
```

Expected output for `"warm waterproof jacket for off-piste skiing"`:

```
Total results: 9
  Black Crows — Corpus Freebird Jacket (Apparel)
  Ridgeline — Freeride Jacket (Apparel)
  Salomon — QST Charge Jacket (Apparel)
  ...
```

> **NOTE:** The `multi_index_query` parameter sends the same query text to all four indexes. The reranker fuses the BM25 scores (from BRAND, ITEM_NAME, SUBCATEGORY) and the vector similarity score (from SEARCH_TEXT) into a single ranked list. You do not need to implement your own score fusion logic.

<!-- ------------------------ -->
## (Optional) Want to Wrap This in a Website?

**You've seen the power of Cortex Search multi-index from SQL. Now let's put it behind a FastAPI backend and a React frontend — with debounced auto-search and a multi-index insights panel.**

The full SNOWFIELD PRO demo connects a FastAPI backend to a React frontend. The Python SDK's `multi_index_query` drives the search; every result carries a `CATEGORY` attribute that powers the live category breakdown sidebar.

### Backend — FastAPI Route

```python
# backend/routes/search.py
from fastapi import APIRouter
from pydantic import BaseModel
from snowflake.core import Root
import snowflake.connector

router = APIRouter()

CATEGORY_COLORS = {
    "Equipment":   "#3B82F6",
    "Apparel":     "#10B981",
    "Protection":  "#F59E0B",
    "Accessories": "#8B5CF6",
}
_FETCH_LIMIT = 100
_SEARCH_COLUMNS = [
    "PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "SUBCATEGORY",
    "SKILL_LEVEL", "DISCIPLINE", "GENDER", "PRICE", "PRODUCT_TYPE", "FLEX_RATING",
]

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

@router.post("/search")
def multi_search(body: SearchRequest):
    conn = snowflake.connector.connect(connection_name="your_connection")
    root = Root(conn)
    svc = (
        root.databases["CATALOG_SEARCH_DB"]
        .schemas["APP"]
        .cortex_search_services["PRODUCT_SEARCH"]
    )

    response = svc.search(
        multi_index_query={
            "BRAND":       [{"text": body.query}],
            "ITEM_NAME":   [{"text": body.query}],
            "SUBCATEGORY": [{"text": body.query}],
            "SEARCH_TEXT": [{"text": body.query}],
        },
        columns=_SEARCH_COLUMNS,
        limit=_FETCH_LIMIT,
    )

    results = response.results

    # Build category breakdown with colours for the insights panel
    breakdown = {}
    for r in results:
        cat = r.get("CATEGORY", "Unknown")
        if cat not in breakdown:
            breakdown[cat] = {"count": 0, "color": CATEGORY_COLORS.get(cat, "#6B7280")}
        breakdown[cat]["count"] += 1

    return {
        "results": results[:body.limit],
        "total": len(results),
        "query": body.query,
        "category_breakdown": breakdown,
    }
```

### Frontend — Debounced Auto-Search (React)

```typescript
// Header.tsx — debounced auto-search fires 400ms after typing stops
useEffect(() => {
    if (inputValue.trim().length < 3) return;
    const timer = setTimeout(() => {
        onSearch(inputValue.trim());
    }, 400);
    return () => clearTimeout(timer);
}, [inputValue]);
```

### Multi-Index Insights Panel

The `MultiIndexInsights` component renders a compact right sidebar showing how results break down by category. Since there is only one service, categories come from the `CATEGORY` attribute on each result — not from which service the result came from:

```typescript
// constants.ts
export const INDEX_COLORS: Record<string, string> = {
    'Equipment':   '#3B82F6',
    'Apparel':     '#10B981',
    'Protection':  '#F59E0B',
    'Accessories': '#8B5CF6',
};
```

### Running the Demo Locally

```bash
# Backend (requires Python 3.9+ with fastapi, uvicorn, snowflake-ml-python)
SNOWFLAKE_CONNECTION=your_connection_name uvicorn main:app --reload --port 8000

# Frontend (requires Node 18+)
cd frontend && npm install && npm run dev
```

Navigate to `http://localhost:5173`, search for `"ridgeline"` and observe all Ridgeline brand products surface at rank 1. Then search `"warm waterproof jacket for freeride"` and observe semantic results with no keyword overlap.

<!-- ------------------------ -->
## Tuning and Optimization

**Multi-index retrieval is production-ready out of the box, but these practices improve recall further.**

### 1. Enrich SEARCH_TEXT for Better Vector Coverage

The more descriptive the `SEARCH_TEXT`, the better the semantic index performs. Include everything a customer might say:

```sql
-- Enrich with brand taglines and synonyms if available
UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET SEARCH_TEXT = TRIM(
    COALESCE(BRAND, '') || ' ' ||
    COALESCE(ITEM_NAME, '') || ' ' ||
    COALESCE(SUBCATEGORY, '') || ' ' ||
    COALESCE(DISCIPLINE, '') || ' ' ||
    COALESCE(SKILL_LEVEL, '') || ' ' ||
    COALESCE(GENDER, '') || ' ' ||
    COALESCE(DESCRIPTION, '') || ' ' ||
    -- Add brand tagline / voice if you have it
    COALESCE(BRAND_TAGLINE, '') || ' ' ||
    COALESCE(MATERIAL_TAGS, '')
);
```

### 2. Granular TEXT INDEXES for Niche Catalogs

For catalogs with strong SKU or model number search patterns, add those columns to TEXT INDEXES:

```sql
-- Example: add SKU and MODEL_NUMBER as TEXT indexes
-- (requires recreating the service)
CREATE OR REPLACE CORTEX SEARCH SERVICE ...
    TEXT INDEXES BRAND, ITEM_NAME, SUBCATEGORY, SKU, MODEL_NUMBER
    VECTOR INDEXES SEARCH_TEXT(model='snowflake-arctic-embed-l-v2.0')
    ...
```

### 3. Use ATTRIBUTES for Post-Search Filtering

ATTRIBUTES are returned with results but are not part of the ranking. Use them to add client-side filters (price range, skill level, gender) after retrieval:

```python
# Filter results client-side after retrieval
filtered = [
    r for r in results
    if r.get("SKILL_LEVEL") in ["Beginner", "Intermediate"]
    and float(r.get("PRICE", 0)) <= 300
]
```

> **NOTE:** Snowflake Cortex Search also supports server-side `filter` expressions in the `svc.search()` call. For high-cardinality filter combinations (e.g. 50+ attribute values), server-side filtering is more efficient than fetching all results and filtering in Python.

<!-- ------------------------ -->
## Cleanup

**Run this SQL to remove all objects created in this quickstart.**

```sql
-- Drop the Cortex Search service
DROP CORTEX SEARCH SERVICE IF EXISTS CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH;

-- Drop the schemas
DROP SCHEMA IF EXISTS CATALOG_SEARCH_DB.APP;
DROP SCHEMA IF EXISTS CATALOG_SEARCH_DB.DATA;

-- Drop the database
DROP DATABASE IF EXISTS CATALOG_SEARCH_DB;

-- Drop the warehouse
DROP WAREHOUSE IF EXISTS CATALOG_SEARCH_WH;
```

> **NOTE:** Dropping a Cortex Search service does not incur additional charges. Storage costs for the indexed data are also removed when the service is dropped. If you drop only the service but keep the source table, you can recreate the service at any time.

<!-- ------------------------ -->
## Conclusion and Resources

**You have built a production-ready retail catalog search using Cortex Search multi-index — one service, four indexes, zero manual reranking.**

### What You Built

-   A product catalog table with a pre-computed `SEARCH_TEXT` column combining brand, name, subcategory, and description
-   A single **Cortex Search service** with three TEXT indexes (BRAND, ITEM_NAME, SUBCATEGORY) and one VECTOR index (SEARCH_TEXT)
-   Working SQL queries using `SNOWFLAKE.CORTEX.SEARCH_PREVIEW()` demonstrating brand recall, intent search, attribute filtering, and category breakdowns
-   _(Optional)_ AI-enriched product descriptions generated with `SNOWFLAKE.CORTEX.COMPLETE()` for deeper semantic recall
-   _(Optional)_ A Python `multi_search()` function using `multi_index_query` to hit all four indexes in one SDK call
-   _(Optional)_ A full SNOWFIELD PRO demo app with debounced auto-search and a multi-index insights sidebar

### Key Takeaways

-   **Multi-index is native, not a pattern** — `TEXT INDEXES` and `VECTOR INDEXES` are first-class DDL clauses in Cortex Search. One service, one call.
-   **Brand recall requires a TEXT INDEX on BRAND** — vector embeddings alone cannot reliably surface brand names at rank 1. BM25 on the BRAND column solves this.
-   **Intent recall requires a VECTOR INDEX** — keyword search cannot match _"warm boot for icy terrain"_ against products that use different words. Embeddings solve this.
-   **The reranker is built in** — you do not write score fusion logic. The service fuses BM25 and vector signals automatically.
-   **CATEGORY comes from result attributes** — in a single-service architecture, the category breakdown is a grouping of the `CATEGORY` attribute on each result, not a reflection of which service matched.
-   **AI enrichment amplifies semantic recall** — running `CORTEX.COMPLETE()` on descriptions before indexing closes the vocabulary gap between terse product copy and natural customer queries.

### Resources

-   [Cortex Search Overview — Snowflake Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
-   [Cortex Search Service DDL Reference](https://docs.snowflake.com/en/sql-reference/sql/create-cortex-search-service)
-   [Snowflake Python SDK — CortexSearchService](https://docs.snowflake.com/en/developer-guide/snowflake-ml/reference/latest/cortex_search_service)
-   [SNOWFLAKE.CORTEX.COMPLETE() Reference](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
-   [snowflake-arctic-embed Models](https://huggingface.co/collections/Snowflake/snowflake-arctic-embed-661f62f3c91aafe00b4aee3b)
-   [SNOWFIELD PRO Demo Source Code](https://github.com/Snowflake-Labs/sfguides)

# TurboPuffer Integration Reference

Pipeline: pandas → Ibis memtable → Cortex AI enrichment → Cortex embeddings → TurboPuffer index → ANN/hybrid/filtered search.

See full example in `turbopuffer_demo.py`.

## Setup

```bash
pip install turbopuffer
export TURBOPUFFER_API_KEY=tpuf_A1...
export TURBOPUFFER_REGION=aws-us-east-1    # match your Snowflake region
```

```python
from turbopuffer import Turbopuffer
tpuf = Turbopuffer(api_key=os.environ["TURBOPUFFER_API_KEY"])
```

## Step 1 — Enrich with Cortex (via Ibis memtable)

```python
import ibis
from cortex_ibis import ai_sentiment, ai_classify, variant_str, variant_float

tbl = ibis.memtable(df)           # no CREATE TABLE privilege needed
enriched = tbl.mutate(
    sentiment_label=ai_sentiment(tbl.body),
    sentiment_score=cortex_sentiment(tbl.body),
    category=variant_str(ai_classify(tbl.body, CATEGORIES), "label"),
).execute()
```

## Step 2 — Generate Embeddings

```python
# Uses raw SQL via con.raw_sql() + CAST to VARCHAR for Python connector compatibility
sql = f"""
    SELECT id, CAST(SNOWFLAKE.CORTEX.EMBED_TEXT_768('{MODEL}', body) AS VARCHAR) AS vec_str
    FROM (VALUES {rows_sql}) AS t(id, body)
"""
result = con.raw_sql(sql)
vec_map = {row[0]: json.loads(row[1]) for row in result.fetchall()}
df["vector"] = df["id"].map(vec_map)
```

## Step 3 — Index into TurboPuffer

```python
ns = tpuf.namespace("cortex-ibis-reviews")
ns.write(
    upsert_rows=[{"id": ..., "vector": [...], "body": ..., "category": ..., "sentiment_label": ...}],
    distance_metric="cosine_distance",
    schema={"body": {"type": "string", "full_text_search": True}, "category": {"type": "string"}},
)
```

## Search Patterns

```python
# ANN (vector-only)
ns.query(rank_by=("vector", "ANN", query_vec), limit=5,
         include_attributes=["body", "category", "sentiment_label"])

# Filtered ANN
ns.query(rank_by=("vector", "ANN", query_vec),
         filters=("sentiment_label", "Eq", "negative"), limit=5)

# Hybrid (70% vector + 30% BM25)
ns.query(rank_by=("Sum", [
    ("Product", 0.7, ("vector", "ANN", query_vec)),
    ("Product", 0.3, ("body", "BM25", query_text)),
]), limit=5)

# Pure BM25 full-text
ns.query(rank_by=("body", "BM25", "refund missing package"), limit=5)

# Aggregations
ns.query(aggregate_by={"count": ("Count",)}, group_by=["category"])

# Namespace branching (copy-on-write, O(1))
branch = tpuf.namespace("cortex-ibis-reviews-branch")
branch.write(branch_from_namespace="cortex-ibis-reviews")
```

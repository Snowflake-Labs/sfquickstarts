# Semantic Search Reference

Uses `SNOWFLAKE.CORTEX.EMBED_TEXT_768/1024` + `VECTOR_COSINE_SIMILARITY / L2 / INNER_PRODUCT`.
Query embedding is computed **inside Snowflake** — no Python-side API call needed.

## semantic_search() Helper

```python
from cortex_ibis import semantic_search

results = semantic_search(
    embed_tbl,                                 # table with pre-computed 'embedding' column
    text_col="body",
    query="delayed shipment and missing item",
    top_k=10,
    metric="cosine",                           # "cosine" | "l2" | "inner_product"
    model="snowflake-arctic-embed-m-v1.5",
    dims=768,
    id_cols=["id", "product_id", "body"],      # columns to include in result
)
# Returns: id | product_id | body | similarity, ordered by similarity DESC
```

## Pre-compute and Cache Embeddings (recommended)

```python
from cortex_ibis import cache_embeddings

embed_tbl = cache_embeddings(
    con,
    source_table="CUSTOMER_REVIEWS",
    text_col="body",
    dest_table="CUSTOMER_REVIEWS_EMBEDDINGS",
    id_cols=["id", "product_id"],
    model="snowflake-arctic-embed-m-v1.5",
    dims=768,
    overwrite=True,
)
# Created: CUSTOMER_REVIEWS_EMBEDDINGS (id, product_id, body, embedding VECTOR(FLOAT,768))
```

## Manual Similarity with Threshold

```python
from cortex_ibis import embed_768, vector_cosine_similarity
import ibis

query_vec = embed_768("snowflake-arctic-embed-m-v1.5", ibis.literal("broken product"))

results = (
    embed_tbl
    .mutate(sim=vector_cosine_similarity(embed_tbl.embedding, query_vec))
    .filter(ibis._.sim > 0.7)                   # threshold
    .select("id", "product_id", "body", "sim")
    .order_by(ibis.desc("sim"))
    .limit(20)
)
```

## Supported Models

| Model | Dims | Use for |
|---|---|---|
| `snowflake-arctic-embed-m-v1.5` | 768 | General semantic search (default) |
| `snowflake-arctic-embed-l-v2` | 1024 | Higher accuracy, slower |
| `e5-base-v2` | 768 | Alternative general-purpose |
| `nv-embed-qa-4` | 1024 | Q&A / retrieval tasks |

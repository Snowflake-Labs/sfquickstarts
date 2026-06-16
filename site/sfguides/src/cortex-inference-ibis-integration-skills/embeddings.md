# Embeddings Reference

Two embedding functions available as Ibis built-in UDFs.

## Functions

```python
from cortex_ibis import embed_768, embed_1024

# Returns VECTOR(FLOAT, 768) — annotated as Array(float32) for Ibis compatibility
vec_col = embed_768("snowflake-arctic-embed-m-v1.5", table.body)

# Returns VECTOR(FLOAT, 1024)
vec_col = embed_1024("snowflake-arctic-embed-l-v2", table.body)
```

## add_embeddings Helper

```python
from cortex_ibis import add_embeddings

table = add_embeddings(
    table, "body",
    model="snowflake-arctic-embed-m-v1.5",
    dims=768,
    out="embedding",
)
```

## cache_embeddings — Pre-compute Once, Query Many Times

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
```

## On-the-fly Query Embedding (runs inside Snowflake)

```python
import ibis
from cortex_ibis import embed_768

query_vec = embed_768("snowflake-arctic-embed-m-v1.5", ibis.literal("your query text"))
# Compiled to: SNOWFLAKE.CORTEX.EMBED_TEXT_768('model', 'your query text')
```

## Vector Similarity Functions

```python
from cortex_ibis import vector_cosine_similarity, vector_l2_distance, vector_inner_product

# Cosine: higher = more similar (range [-1, 1])
sim = vector_cosine_similarity(table.embedding, query_vec)

# L2: lower = more similar
dist = vector_l2_distance(table.embedding, query_vec)

# Inner product: for normalised vectors ≡ cosine
dot = vector_inner_product(table.embedding, query_vec)
```

## Ibis Type Note

Snowflake returns `VECTOR(FLOAT, N)` which has no direct Ibis type. The functions annotate the return as `Array(float32)` so Ibis accepts the expression — the emitted SQL is valid Snowflake.

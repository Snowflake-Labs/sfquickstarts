# EnrichmentPipeline Reference

Fluent builder for composing Cortex enrichment steps. Nothing runs until `.execute()` or `.cache()`.

```python
from cortex_ibis import EnrichmentPipeline

result = (
    EnrichmentPipeline(con.table("CUSTOMER_REVIEWS"))
    .filter_ai("Is this written in English? ", "body")       # drops non-English rows
    .classify("body", ["billing", "delivery", "product quality", "support"])
    .sentiment("body")                                         # float score column
    .summarize("body")                                         # abstractive summary
    .embed("body", model="snowflake-arctic-embed-m-v1.5", dims=768)
    .translate("body", "en", "es", out="body_es")
    .complete("body", "Write a brief customer-service reply to: ", model="claude-4-sonnet")
    .execute()                                                 # → pandas DataFrame
)
```

## Available Chain Methods

| Method | Output column(s) | Notes |
|---|---|---|
| `.classify(col, categories)` | `category`, `category_score` | AI_CLASSIFY + VARIANT unpack |
| `.sentiment(col)` | `sentiment` | SNOWFLAKE.CORTEX.SENTIMENT float |
| `.summarize(col)` | `summary` | SNOWFLAKE.CORTEX.SUMMARIZE |
| `.embed(col, model, dims)` | `embedding` | EMBED_TEXT_768 or EMBED_TEXT_1024 |
| `.translate(col, src, tgt)` | `translated` | SNOWFLAKE.CORTEX.TRANSLATE |
| `.complete(col, prefix, model)` | `completion` | AI_COMPLETE |
| `.filter_ai(condition, col)` | — (filters rows) | AI_FILTER |

## Materialise to Snowflake Table

```python
# Returns an Ibis table expression pointing at the new table
enriched = (
    EnrichmentPipeline(reviews)
    .classify("body", ["billing", "support"])
    .sentiment("body")
).cache(con, "REVIEWS_ENRICHED", overwrite=True)
```

## Inspect SQL Without Running

```python
pipeline = EnrichmentPipeline(reviews).sentiment("body").summarize("body")
print(pipeline.sql())    # compiled Snowflake SQL
```

## Pattern: Filter First, Enrich Only Relevant Rows

```python
# Cheap vector pre-filter → expensive LLM only on matched subset
from cortex_ibis import embed_768, vector_cosine_similarity
import ibis

query_vec = embed_768("snowflake-arctic-embed-m-v1.5", ibis.literal("refund request"))
relevant = (
    embed_tbl
    .mutate(sim=vector_cosine_similarity(embed_tbl.embedding, query_vec))
    .filter(ibis._.sim > 0.75)
)
# Now enrich only ~relevant rows (much cheaper than enriching everything)
result = EnrichmentPipeline(relevant).classify("body", ["billing"]).execute()
```

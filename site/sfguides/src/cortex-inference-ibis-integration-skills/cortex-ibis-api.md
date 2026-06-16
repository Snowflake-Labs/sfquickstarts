# Cortex + Ibis API Reference

All functions in `cortex_ibis.py`. Use these before writing custom SQL.

## AI_* Functions (new unprefixed — preferred)

```python
from cortex_ibis import (
    ai_complete, ai_sentiment, ai_translate,
    ai_classify, ai_extract, ai_filter, ai_redact,
    ai_summarize_agg, ai_agg,          # aggregates
)

# Scalar
table.mutate(sentiment=ai_sentiment(table.body))
table.mutate(translated=ai_translate(table.body, "en", "es"))
table.mutate(reply=ai_complete("claude-4-sonnet", "Reply to: " + table.body))
table.filter(ai_filter("Is this a complaint? " + table.body))

# Aggregate (use inside .agg())
table.group_by("product_id").agg(summary=ai_summarize_agg(table.body))
table.group_by("product_id").agg(
    top_issue=ai_agg("What is the main complaint?", table.body)
)
```

## SNOWFLAKE.CORTEX.* Functions (classic namespaced)

```python
from cortex_ibis import (
    cortex_complete, cortex_summarize, cortex_sentiment,
    cortex_translate, cortex_extract_answer,
)

# cortex_sentiment returns float in [-1, 1]
table.mutate(score=cortex_sentiment(table.body))

# cortex_extract_answer returns VARIANT {answer, score}
raw = cortex_extract_answer(table.body, "What product is reviewed?")
table.mutate(answer=variant_str(raw, "answer"), conf=variant_float(raw, "score"))
```

## VARIANT Helpers

```python
from cortex_ibis import variant_str, variant_float, variant_int, unpack_classify

# Unpack AI_CLASSIFY → {label, score}
cls = ai_classify(table.body, ["billing", "delivery", "product quality"])
table.mutate(
    category=variant_str(cls, "label"),
    score=variant_float(cls, "score"),
)

# Shorthand
unpacked = unpack_classify(cls)   # {'label': StringColumn, 'score': FloatingColumn}
```

## High-Level Helpers

```python
from cortex_ibis import add_sentiment, add_summary, add_classification, add_extraction, add_embeddings

table = add_sentiment(table, "body")                                      # → float 'sentiment'
table = add_summary(table, "body")                                        # → str 'summary'
table = add_classification(table, "body", ["billing", "delivery"])        # → 'category', 'category_score'
table = add_extraction(table, "body", {"order_id": {"type": "string"}})   # → VARIANT 'extracted'
table = add_embeddings(table, "body", model="snowflake-arctic-embed-m-v1.5", dims=768)  # → VECTOR 'embedding'
```

## SQL Preview (always do this before .execute())

```python
import ibis
print(ibis.to_sql(table_expr, dialect="snowflake"))
```

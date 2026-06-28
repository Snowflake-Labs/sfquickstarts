"""
demo.py — End-to-end walkthrough of cortex_ibis

Demonstrates:
  1. Connecting via Ibis → Snowflake
  2. Basic Cortex AI enrichment (sentiment, classification, extraction)
  3. Lazy chaining with EnrichmentPipeline
  4. Embedding generation and caching
  5. Semantic search (cosine, L2, inner product)
  6. Materialising enriched results back to Snowflake
  7. VARIANT / typed-output field unpacking

All steps are annotated with the SQL Ibis will generate.
"""

import ibis
ibis.options.interactive = True   # auto-print tables in notebooks / REPL

from cortex_ibis import (
    # AI_* functions
    ai_complete, ai_sentiment, ai_translate, ai_classify,
    ai_extract, ai_filter, ai_summarize_agg, ai_agg,
    # SNOWFLAKE.CORTEX.* inference
    cortex_complete, cortex_summarize, cortex_sentiment,
    cortex_translate, cortex_extract_answer,
    # Embeddings
    embed_768, embed_1024,
    # Vector similarity
    vector_cosine_similarity, vector_l2_distance, vector_inner_product,
    # VARIANT helpers
    variant_str, variant_float, unpack_classify,
    # High-level helpers
    add_classification, add_sentiment, add_summary,
    add_embeddings, semantic_search,
    # Pipeline builder
    EnrichmentPipeline,
    # Materialisation
    cache_embeddings,
)


# ─────────────────────────────────────────────────────────────────────────────
# CONNECT
# ─────────────────────────────────────────────────────────────────────────────

con = ibis.snowflake.connect(
    user="you@example.com",
    account="my_org-my_account",
    database="DEMO_DB/PUBLIC",
    warehouse="COMPUTE_WH",
    authenticator="externalbrowser",
)

# Or from an existing Snowpark session:
#   import snowflake.snowpark as sp
#   session = sp.Session.builder.configs(connection_params).create()
#   con = ibis.snowflake.from_snowpark(session)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  BASIC  TABLE  ACCESS
# ─────────────────────────────────────────────────────────────────────────────

reviews = con.table("CUSTOMER_REVIEWS")
# reviews.columns → ['id', 'product_id', 'customer_id', 'body', 'created_at']


# ─────────────────────────────────────────────────────────────────────────────
# 2.  SCALAR  ENRICHMENT  (lazy — nothing runs until .execute())
# ─────────────────────────────────────────────────────────────────────────────

# ── 2a. Sentiment (float score via SNOWFLAKE.CORTEX.SENTIMENT) ──────────────
scored = reviews.mutate(score=cortex_sentiment(reviews.body))
# SQL: SELECT *, SNOWFLAKE.CORTEX.SENTIMENT("body") AS "score" FROM "CUSTOMER_REVIEWS"

# ── 2b. Label sentiment with new AI_SENTIMENT (returns text label) ───────────
labelled = reviews.mutate(sentiment=ai_sentiment(reviews.body))
# SQL: SELECT *, AI_SENTIMENT("body") AS "sentiment" FROM "CUSTOMER_REVIEWS"

# ── 2c. Classification with label+score unpack ───────────────────────────────
classified = add_classification(
    reviews, "body",
    categories=["billing", "delivery", "product quality", "support"],
)
# Produces 'category' (string) and 'category_score' (float) columns

# ── 2d. Structured extraction ────────────────────────────────────────────────
extracted = add_extraction(
    reviews, "body",
    schema={"order_number": {"type": "string"}, "amount": {"type": "number"}},
    out="fields",
)
# Unpack individual fields:
with_order = extracted.mutate(
    order_number=variant_str(extracted.fields, "order_number"),
    amount=variant_float(extracted.fields, "amount"),
)

# ── 2e. Translation ──────────────────────────────────────────────────────────
translated = reviews.mutate(
    body_es=cortex_translate(reviews.body, "en", "es"),
)

# ── 2f. LLM completion ───────────────────────────────────────────────────────
drafted = reviews.mutate(
    draft_reply=ai_complete(
        "llama3.1-70b",
        "Write a polite customer-service reply to: " + reviews.body,
    )
)

# ── 2g. AI filter (keep only actionable reviews) ────────────────────────────
actionable = reviews.filter(
    ai_filter("Does this review request a specific action or refund? " + reviews.body)
)

# ── 2h. EXTRACT_ANSWER (classic two-arg QA) ──────────────────────────────────
answered = reviews.mutate(
    qa_raw=cortex_extract_answer(reviews.body, "What product is being reviewed?")
)
with_answer = answered.mutate(
    answer=variant_str(answered.qa_raw, "answer"),
    answer_score=variant_float(answered.qa_raw, "score"),
)


# ─────────────────────────────────────────────────────────────────────────────
# 3.  AGGREGATE  FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

# Summarise all reviews per product
product_summaries = (
    reviews
    .group_by("product_id")
    .agg(
        n=reviews.id.count(),
        avg_score=cortex_sentiment(reviews.body).mean(),
        summary=ai_summarize_agg(reviews.body),
        top_complaint=ai_agg(
            "What is the single most common complaint?",
            reviews.body,
        ),
    )
)

# ── Inspect SQL before running ───────────────────────────────────────────────
print(ibis.to_sql(product_summaries, dialect="snowflake"))


# ─────────────────────────────────────────────────────────────────────────────
# 4.  LAZY  CHAIN  WITH  EnrichmentPipeline
# ─────────────────────────────────────────────────────────────────────────────

pipeline = (
    EnrichmentPipeline(reviews)
    # Keep only English-language reviews (AI filter)
    .filter_ai("Is this text written in English? ", "body")
    # Classify into topic buckets
    .classify("body", ["billing", "delivery", "product quality", "support"])
    # Float sentiment score
    .sentiment("body")
    # Short summary of each review
    .summarize("body")
    # 768-dim embeddings for later search
    .embed("body", model="snowflake-arctic-embed-m-v1.5", dims=768)
    # Draft a personalised reply
    .complete("body", "Write a brief, helpful customer service reply to: ")
)

# Peek at SQL without running anything
print(pipeline.sql())

# Execute → pandas DataFrame (runs ALL steps in a single SQL query in Snowflake)
df = pipeline.execute()

# Or materialise as a Snowflake table (for reuse / downstream consumers)
enriched_table = pipeline.cache(con, "CUSTOMER_REVIEWS_ENRICHED", overwrite=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5.  EMBEDDINGS  WORKFLOW
# ─────────────────────────────────────────────────────────────────────────────

# ── 5a. Compute on the fly (small tables / ad-hoc) ───────────────────────────
embedded = reviews.mutate(
    vec=embed_768("snowflake-arctic-embed-m-v1.5", reviews.body)
)

# ── 5b. Pre-compute and cache (recommended for repeated search) ──────────────
embed_table = cache_embeddings(
    con,
    source_table="CUSTOMER_REVIEWS",
    text_col="body",
    dest_table="CUSTOMER_REVIEWS_EMBEDDINGS",
    id_cols=["id", "product_id"],
    model="snowflake-arctic-embed-m-v1.5",
    dims=768,
    overwrite=True,
)
# Creates:  CUSTOMER_REVIEWS_EMBEDDINGS (id, product_id, body, embedding VECTOR)

# ── 5c. Load the cached embedding table ──────────────────────────────────────
embed_tbl = con.table("CUSTOMER_REVIEWS_EMBEDDINGS")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  SEMANTIC  SEARCH
# ─────────────────────────────────────────────────────────────────────────────

# The query embedding is computed inside Snowflake — no Python-side API call.

query = "delayed shipment and missing item"

# ── 6a. Cosine similarity on cached embeddings ───────────────────────────────
results_cos = semantic_search(
    embed_tbl,
    text_col="body",
    query=query,
    top_k=10,
    metric="cosine",
    model="snowflake-arctic-embed-m-v1.5",
    dims=768,
    id_cols=["id", "product_id", "body"],
)
# Emitted SQL (simplified):
# SELECT id, product_id, body,
#        VECTOR_COSINE_SIMILARITY(embedding,
#            SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', 'delayed shipment...'))
#            AS similarity
# FROM CUSTOMER_REVIEWS_EMBEDDINGS
# ORDER BY similarity DESC
# LIMIT 10

# ── 6b. L2 distance (lower = more similar) ───────────────────────────────────
results_l2 = semantic_search(
    embed_tbl, text_col="body", query=query,
    top_k=10, metric="l2", id_cols=["id", "product_id", "body"],
)

# ── 6c. Inner product ────────────────────────────────────────────────────────
results_ip = semantic_search(
    embed_tbl, text_col="body", query=query,
    top_k=10, metric="inner_product", id_cols=["id", "product_id", "body"],
)

# ── 6d. Manual similarity (more control) ────────────────────────────────────
query_vec = embed_768("snowflake-arctic-embed-m-v1.5", ibis.literal(query))

manual = (
    embed_tbl
    .mutate(sim=vector_cosine_similarity(embed_tbl.embedding, query_vec))
    .filter(ibis._.sim > 0.7)                   # threshold filter
    .select("id", "product_id", "body", "sim")
    .order_by(ibis.desc("sim"))
    .limit(20)
)

# ── 6e. Semantic search + enrichment in one chain ────────────────────────────
top_complaints = (
    EnrichmentPipeline(embed_tbl)
    # Narrow to semantically relevant rows first (cheap vector op)
    # then enrich only those rows (expensive LLM ops)
    # Note: filter_ai here would work but vector pre-filter is much cheaper
)
# Build it manually for the hybrid pattern:
query_vec2 = embed_768("snowflake-arctic-embed-m-v1.5", ibis.literal("refund request"))
hybrid = (
    embed_tbl
    .mutate(sim=vector_cosine_similarity(embed_tbl.embedding, query_vec2))
    .filter(ibis._.sim > 0.75)
    # Now enrich only the ~relevant subset
    .mutate(
        category=variant_str(
            ai_classify(ibis._.body, ["billing", "delivery", "product quality"]),
            "label",
        ),
        summary=cortex_summarize(ibis._.body),
    )
    .drop("embedding")
    .order_by(ibis.desc("sim"))
)

print(ibis.to_sql(hybrid, dialect="snowflake"))
df_hybrid = hybrid.execute()


# ─────────────────────────────────────────────────────────────────────────────
# 7.  MULTI-METRIC  COMPARISON  (rank by several metrics at once)
# ─────────────────────────────────────────────────────────────────────────────

qv = embed_768("snowflake-arctic-embed-m-v1.5", ibis.literal("broken product arrived damaged"))

multi_metric = (
    embed_tbl
    .mutate(
        cos_sim=vector_cosine_similarity(embed_tbl.embedding, qv),
        l2_dist=vector_l2_distance(embed_tbl.embedding, qv),
        dot_prod=vector_inner_product(embed_tbl.embedding, qv),
    )
    .select("id", "product_id", "body", "cos_sim", "l2_dist", "dot_prod")
    .order_by(ibis.desc("cos_sim"))
    .limit(10)
)


# ─────────────────────────────────────────────────────────────────────────────
# 8.  WRITE  RESULTS  BACK  TO  SNOWFLAKE
# ─────────────────────────────────────────────────────────────────────────────

# Option A — create a new table from any expression
con.create_table(
    "REVIEWS_WITH_SENTIMENT",
    scored.select("id", "product_id", "body", "score"),
    overwrite=True,
)

# Option B — insert into an existing table
con.insert("AUDIT_LOG", product_summaries.select("product_id", "summary"))

# Option C — write to pandas first, then upload
df_local = classified.execute()
df_local.to_csv("enriched_reviews.csv", index=False)

# Option D — create a view (no data copy; Cortex called at query time)
con.create_view(
    "V_REVIEWS_LIVE_SENTIMENT",
    scored,
    overwrite=True,
)

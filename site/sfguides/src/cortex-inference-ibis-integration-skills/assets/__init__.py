"""
cortex_ibis — Snowflake Cortex AI + Inference functions for Ibis.

Quick start
-----------
    import ibis
    from cortex_ibis import EnrichmentPipeline, semantic_search

    con = ibis.snowflake.connect(
        user="you@example.com",
        account="my_org-my_account",
        database="MY_DB/MY_SCHEMA",
        authenticator="externalbrowser",
    )
"""

from cortex_ibis.cortex_ibis import (
    # AI_* scalar
    ai_complete,
    ai_sentiment,
    ai_translate,
    ai_classify,
    ai_extract,
    ai_filter,
    ai_redact,
    # AI_* aggregate
    ai_summarize_agg,
    ai_agg,
    # SNOWFLAKE.CORTEX.* inference
    cortex_complete,
    cortex_summarize,
    cortex_sentiment,
    cortex_translate,
    cortex_extract_answer,
    # Embeddings
    embed_768,
    embed_1024,
    # Vector similarity
    vector_cosine_similarity,
    vector_l2_distance,
    vector_inner_product,
    # VARIANT helpers
    variant_str,
    variant_float,
    variant_int,
    unpack_classify,
    # High-level helpers
    add_sentiment,
    add_summary,
    add_classification,
    add_extraction,
    add_embeddings,
    semantic_search,
    # Pipeline
    EnrichmentPipeline,
    # Materialisation
    cache_embeddings,
)

__all__ = [
    "ai_complete", "ai_sentiment", "ai_translate", "ai_classify",
    "ai_extract", "ai_filter", "ai_redact",
    "ai_summarize_agg", "ai_agg",
    "cortex_complete", "cortex_summarize", "cortex_sentiment",
    "cortex_translate", "cortex_extract_answer",
    "embed_768", "embed_1024",
    "vector_cosine_similarity", "vector_l2_distance", "vector_inner_product",
    "variant_str", "variant_float", "variant_int", "unpack_classify",
    "add_sentiment", "add_summary", "add_classification",
    "add_extraction", "add_embeddings", "semantic_search",
    "EnrichmentPipeline",
    "cache_embeddings",
]

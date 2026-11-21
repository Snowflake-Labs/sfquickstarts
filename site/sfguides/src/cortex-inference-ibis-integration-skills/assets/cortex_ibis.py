"""
cortex_ibis.py — Snowflake Cortex AI + Inference functions for Ibis

Covers:
  - AI_*  (new, no-prefix functions)
  - Shannon entropy & distribution analysis (category_entropy, normalized_entropy, entropy_from_pandas)
  - SNOWFLAKE.CORTEX.*  (classic inference)
  - VECTOR_COSINE_SIMILARITY / L2_DISTANCE / INNER_PRODUCT
  - VARIANT helpers (typed field extraction from AI_CLASSIFY / AI_EXTRACT)
  - Embedding generation, caching, and semantic search
  - Lazy-chain helpers and table materialisation utilities

Install:
    pip install 'ibis-framework[snowflake]'

Connect (example):
    import ibis
    con = ibis.snowflake.connect(
        user="you@example.com",
        account="my_org-my_account",
        database="MY_DB/MY_SCHEMA",
        authenticator="externalbrowser",
    )
"""

from __future__ import annotations

from typing import Optional
import ibis
import ibis.expr.datatypes as dt
import ibis.expr.types as ir


# ──────────────────────────────────────────────────────────────────────────────
# 1.  NEW  AI_*  FUNCTIONS  (preferred, no-prefix)
# ──────────────────────────────────────────────────────────────────────────────

@ibis.udf.scalar.builtin
def ai_complete(model: str, prompt: str) -> str:
    """AI_COMPLETE(model, prompt) → text completion."""
    ...


@ibis.udf.scalar.builtin
def ai_sentiment(text: str) -> str:
    """AI_SENTIMENT(text) → 'positive' | 'negative' | 'neutral'."""
    ...


@ibis.udf.scalar.builtin
def ai_translate(text: str, target_language: str) -> str:
    """AI_TRANSLATE(text, target_language) → translated string."""
    ...


@ibis.udf.scalar.builtin
def ai_classify(text: str, categories) -> dt.json:
    """AI_CLASSIFY(text, array_of_labels) → {label, score}."""
    ...


@ibis.udf.scalar.builtin
def ai_extract(text: str, schema) -> dt.json:
    """AI_EXTRACT(text, schema_object) → extracted fields as VARIANT."""
    ...


@ibis.udf.scalar.builtin
def ai_filter(prompt: str) -> bool:
    """AI_FILTER(prompt_with_embedded_text) → boolean; use in .filter()."""
    ...


@ibis.udf.scalar.builtin
def ai_redact(text: str) -> str:
    """AI_REDACT(text) → PII-redacted string."""
    ...


# Aggregates
@ibis.udf.agg.builtin
def ai_summarize_agg(text: str) -> str:
    """AI_SUMMARIZE_AGG(text) → rolling summary across group."""
    ...


@ibis.udf.agg.builtin
def ai_agg(question: str, text: str) -> str:
    """AI_AGG(question, text) → answer derived from aggregated text."""
    ...


# ──────────────────────────────────────────────────────────────────────────────
# 2.  CLASSIC  SNOWFLAKE.CORTEX.*  INFERENCE  FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.COMPLETE")
def cortex_complete(model: str, prompt: str) -> str:
    """SNOWFLAKE.CORTEX.COMPLETE — classic namespaced LLM completion."""
    ...


@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.SUMMARIZE")
def cortex_summarize(text: str) -> str:
    """SNOWFLAKE.CORTEX.SUMMARIZE — abstractive summary."""
    ...


@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.SENTIMENT")
def cortex_sentiment(text: str) -> float:
    """SNOWFLAKE.CORTEX.SENTIMENT — float score in [-1, 1]."""
    ...


@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.TRANSLATE")
def cortex_translate(text: str, source_language: str, target_language: str) -> str:
    """SNOWFLAKE.CORTEX.TRANSLATE — language translation."""
    ...


@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.EXTRACT_ANSWER")
def cortex_extract_answer(context: str, question: str) -> dt.json:
    """SNOWFLAKE.CORTEX.EXTRACT_ANSWER — returns {answer, score}."""
    ...


# ──────────────────────────────────────────────────────────────────────────────
# 3.  EMBEDDINGS  (SNOWFLAKE.CORTEX.EMBED_TEXT_* → VECTOR type)
# ──────────────────────────────────────────────────────────────────────────────
# Snowflake returns VECTOR(FLOAT, N) — not directly representable in Ibis dtype
# system. We annotate with Array(float32) so Ibis accepts the expression;
# the emitted SQL is valid Snowflake.

@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.EMBED_TEXT_768")
def embed_768(model: str, text: str) -> dt.Array(dt.float32()):
    """EMBED_TEXT_768 — 768-dim vector from model (e.g. 'snowflake-arctic-embed-m')."""
    ...


@ibis.udf.scalar.builtin(name="SNOWFLAKE.CORTEX.EMBED_TEXT_1024")
def embed_1024(model: str, text: str) -> dt.Array(dt.float32()):
    """EMBED_TEXT_1024 — 1024-dim vector from model (e.g. 'snowflake-arctic-embed-l-v2')."""
    ...


# ──────────────────────────────────────────────────────────────────────────────
# 4.  VECTOR  SIMILARITY  METRICS
# ──────────────────────────────────────────────────────────────────────────────

@ibis.udf.scalar.builtin(name="VECTOR_COSINE_SIMILARITY")
def vector_cosine_similarity(v1, v2) -> float:
    """Cosine similarity in [−1, 1]. Higher → more similar."""
    ...


@ibis.udf.scalar.builtin(name="VECTOR_L2_DISTANCE")
def vector_l2_distance(v1, v2) -> float:
    """Euclidean (L2) distance. Lower → more similar."""
    ...


@ibis.udf.scalar.builtin(name="VECTOR_INNER_PRODUCT")
def vector_inner_product(v1, v2) -> float:
    """Dot-product inner product. For normalised vectors ≡ cosine similarity."""
    ...


# ──────────────────────────────────────────────────────────────────────────────
# 5.  VARIANT  FIELD  HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def variant_str(col: ir.Column, field: str) -> ir.StringColumn:
    """Extract a string field from a VARIANT/json column: col['field']::STRING."""
    return col[field].cast("string")


def variant_float(col: ir.Column, field: str) -> ir.FloatingColumn:
    """Extract a float field from a VARIANT/json column."""
    return col[field].cast("float64")


def variant_int(col: ir.Column, field: str) -> ir.IntegerColumn:
    """Extract an integer field from a VARIANT/json column."""
    return col[field].cast("int64")


# Convenience: unpack the {label, score} object that AI_CLASSIFY returns.
def unpack_classify(col: ir.Column) -> dict[str, ir.Column]:
    """Return {'label': StringColumn, 'score': FloatingColumn} from AI_CLASSIFY output."""
    return {
        "label": variant_str(col, "label"),
        "score": variant_float(col, "score"),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 6.  HIGH-LEVEL  ENRICHMENT  HELPERS
# ──────────────────────────────────────────────────────────────────────────────

_DEFAULT_EMBED_MODEL = "snowflake-arctic-embed-m-v1.5"
_DEFAULT_LLM         = "llama3.1-70b"


def add_sentiment(table: ir.Table, text_col: str, *, out: str = "sentiment") -> ir.Table:
    """Append a float sentiment score column via SNOWFLAKE.CORTEX.SENTIMENT."""
    return table.mutate(**{out: cortex_sentiment(table[text_col])})


def add_summary(table: ir.Table, text_col: str, *, out: str = "summary") -> ir.Table:
    """Append an abstractive summary via SNOWFLAKE.CORTEX.SUMMARIZE."""
    return table.mutate(**{out: cortex_summarize(table[text_col])})


def add_classification(
    table: ir.Table,
    text_col: str,
    categories: list[str],
    *,
    out_label: str = "category",
    out_score: str = "category_score",
) -> ir.Table:
    """
    Classify text and append label + score columns.

    Uses AI_CLASSIFY; unpacks the VARIANT automatically.
    """
    raw = ai_classify(table[text_col], categories)
    return table.mutate(
        **{
            out_label: variant_str(raw, "label"),
            out_score: variant_float(raw, "score"),
        }
    )


def add_extraction(
    table: ir.Table,
    text_col: str,
    schema: dict,
    *,
    out: str = "extracted",
) -> ir.Table:
    """
    Append extracted fields (as a VARIANT column) via AI_EXTRACT.

    Access individual keys afterwards with variant_str() / variant_float().
    """
    return table.mutate(**{out: ai_extract(table[text_col], schema)})


def add_embeddings(
    table: ir.Table,
    text_col: str,
    *,
    model: str = _DEFAULT_EMBED_MODEL,
    dims: int = 768,
    out: str = "embedding",
) -> ir.Table:
    """Append a VECTOR embedding column."""
    fn = embed_768 if dims == 768 else embed_1024
    return table.mutate(**{out: fn(model, table[text_col])})


# ──────────────────────────────────────────────────────────────────────────────
# 7.  SEMANTIC  SEARCH
# ──────────────────────────────────────────────────────────────────────────────

def semantic_search(
    table: ir.Table,
    text_col: str,
    query: str,
    *,
    top_k: int = 10,
    metric: str = "cosine",
    model: str = _DEFAULT_EMBED_MODEL,
    dims: int = 768,
    id_cols: Optional[list[str]] = None,
) -> ir.Table:
    """
    Return the top_k most similar rows to `query` using vector similarity.

    Parameters
    ----------
    table     : Ibis table with a text column (and optionally pre-computed embeddings)
    text_col  : Column to embed on-the-fly (ignored if table already has 'embedding')
    query     : Plain-text query string
    top_k     : Number of results to return
    metric    : 'cosine' | 'l2' | 'inner_product'
    model     : Cortex embed model name
    dims      : 768 or 1024
    id_cols   : Extra columns to include in result; defaults to all non-embedding cols

    Notes
    -----
    The query embedding is computed inside Snowflake as a SQL literal —
    no Python-side API call required.
    """
    embed_fn = embed_768 if dims == 768 else embed_1024
    sim_fn = {
        "cosine": vector_cosine_similarity,
        "l2": vector_l2_distance,
        "inner_product": vector_inner_product,
    }[metric]

    # Build or reuse the embedding column
    has_embedding = "embedding" in table.columns
    enriched = table if has_embedding else table.mutate(
        embedding=embed_fn(model, table[text_col])
    )

    # Compute query embedding as a SQL expression (runs server-side)
    query_vec = embed_fn(model, ibis.literal(query))

    scored = enriched.mutate(similarity=sim_fn(enriched.embedding, query_vec))

    # Sort: cosine/inner_product → descending (higher = better)
    #       l2                   → ascending  (lower  = better)
    order = ibis.desc("similarity") if metric != "l2" else ibis.asc("similarity")

    cols = id_cols or [c for c in table.columns if c != "embedding"]
    return scored.select([*cols, "similarity"]).order_by(order).limit(top_k)


# ──────────────────────────────────────────────────────────────────────────────
# 8.  CHAINING  HELPERS  (lazy evaluation)
# ──────────────────────────────────────────────────────────────────────────────

class EnrichmentPipeline:
    """
    Fluent builder for composing Cortex enrichment steps lazily.

    Nothing executes until you call .execute() or .cache().

    Example
    -------
    result = (
        EnrichmentPipeline(con.table("REVIEWS"))
        .classify("body", ["billing", "product", "support"])
        .sentiment("body")
        .summarize("body")
        .embed("body")
        .execute()
    )
    """

    def __init__(self, table: ir.Table) -> None:
        self._expr = table

    @property
    def expr(self) -> ir.Table:
        """The current (unexecuted) Ibis expression."""
        return self._expr

    def classify(
        self,
        col: str,
        categories: list[str],
        *,
        out_label: str = "category",
        out_score: str = "category_score",
    ) -> "EnrichmentPipeline":
        self._expr = add_classification(
            self._expr, col, categories,
            out_label=out_label, out_score=out_score,
        )
        return self

    def sentiment(self, col: str, *, out: str = "sentiment") -> "EnrichmentPipeline":
        self._expr = add_sentiment(self._expr, col, out=out)
        return self

    def summarize(self, col: str, *, out: str = "summary") -> "EnrichmentPipeline":
        self._expr = add_summary(self._expr, col, out=out)
        return self

    def embed(
        self,
        col: str,
        *,
        model: str = _DEFAULT_EMBED_MODEL,
        dims: int = 768,
        out: str = "embedding",
    ) -> "EnrichmentPipeline":
        self._expr = add_embeddings(self._expr, col, model=model, dims=dims, out=out)
        return self

    def translate(
        self, col: str, source: str, target: str, *, out: str = "translated"
    ) -> "EnrichmentPipeline":
        self._expr = self._expr.mutate(
            **{out: cortex_translate(self._expr[col], source, target)}
        )
        return self

    def complete(
        self,
        col: str,
        prompt_prefix: str,
        *,
        model: str = _DEFAULT_LLM,
        out: str = "completion",
    ) -> "EnrichmentPipeline":
        self._expr = self._expr.mutate(
            **{out: ai_complete(model, prompt_prefix + self._expr[col])}
        )
        return self

    def filter_ai(self, condition_prefix: str, col: str) -> "EnrichmentPipeline":
        """Keep only rows where AI_FILTER returns True."""
        self._expr = self._expr.filter(
            ai_filter(condition_prefix + self._expr[col])
        )
        return self

    def sql(self, *, dialect: str = "snowflake") -> str:
        """Return the compiled SQL without executing."""
        return ibis.to_sql(self._expr, dialect=dialect)

    def execute(self):
        """Execute and return a pandas DataFrame."""
        return self._expr.execute()

    def cache(
        self,
        con: "ibis.backends.snowflake.Backend",
        table_name: str,
        *,
        overwrite: bool = False,
    ) -> ir.Table:
        """
        Materialise the pipeline result as a Snowflake table.

        Returns an Ibis table expression pointing at the new table.
        """
        return con.create_table(table_name, self._expr, overwrite=overwrite)


# ──────────────────────────────────────────────────────────────────────────────
# 9.  MATERIALISATION  UTILITIES
# ──────────────────────────────────────────────────────────────────────────────

def cache_embeddings(
    con: "ibis.backends.snowflake.Backend",
    source_table: str,
    text_col: str,
    dest_table: str,
    *,
    id_cols: Optional[list[str]] = None,
    model: str = _DEFAULT_EMBED_MODEL,
    dims: int = 768,
    overwrite: bool = False,
) -> ir.Table:
    """
    Pre-compute and store embeddings in a dedicated Snowflake table.

    This is the recommended approach: compute embeddings once, query many times.
    The resulting table has (id_cols..., text_col, embedding VECTOR).

    Returns the Ibis table expression for the created table.
    """
    src = con.table(source_table)
    cols = id_cols or [c for c in src.columns if c != text_col]
    embed_fn = embed_768 if dims == 768 else embed_1024

    expr = src.select(
        *cols,
        src[text_col],
        embedding=embed_fn(model, src[text_col]),
    )
    return con.create_table(dest_table, expr, overwrite=overwrite)


# ──────────────────────────────────────────────────────────────────────────────
# 10.  SHANNON  ENTROPY  &  DISTRIBUTION  ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────

def category_entropy(
    table: ir.Table,
    group_cols: list[str],
    category_col: str,
) -> ir.Table:
    """
    Shannon entropy (bits) of the category_col distribution per group — pure SQL via Ibis.

    Returns a table with group_cols + [entropy, dominant_category, dominant_share].

    Intuition
    ---------
    * H ≈ log2(N) → perfectly uniform across N categories (max uncertainty)
    * H ≈ 0       → single dominant category (fully predictable)

    For customer reviews with 4 categories:
        H = 2.0 bits → reviews spread evenly across billing/delivery/defect/positive
        H = 0.0 bits → all reviews in one category (e.g. all positive)

    Example
    -------
    entropy_tbl = category_entropy(
        classified_reviews,   # table with 'product_id' and 'category' columns
        group_cols=["product_id"],
        category_col="category",
    )
    # → product_id | entropy | dominant_category | dominant_share
    """
    # Step 1: count per (group, category)
    counts = (
        table
        .group_by([*group_cols, category_col])
        .agg(n=table[category_col].count())
    )

    # Step 2: total per group
    totals = (
        counts
        .group_by(group_cols)
        .agg(total=counts.n.sum())
    )

    # Step 3: join and compute p_i
    joined = counts.join(totals, group_cols)
    with_p = joined.mutate(p=(joined.n.cast("float64") / joined.total.cast("float64")))

    # Step 4: compute -p * log2(p) term; guard p==0 with filter
    with_term = with_p.filter(with_p.p > 0).mutate(
        term=-(with_p.p * with_p.p.log2())
    )

    # Step 5: sum entropy + find dominant category per group
    entropy_tbl = (
        with_term
        .group_by(group_cols)
        .agg(entropy=with_term.term.sum())
    )

    # Step 6: dominant category (argmax share)
    dominant = (
        with_p
        .order_by([*group_cols, ibis.desc("p")])
        .group_by(group_cols)
        .agg(
            dominant_category=with_p[category_col].first(),
            dominant_share=with_p.p.max(),
        )
    )

    return entropy_tbl.join(dominant, group_cols).order_by("entropy")


def normalized_entropy(
    table: ir.Table,
    group_cols: list[str],
    category_col: str,
    num_categories: int,
) -> ir.Table:
    """
    Normalized Shannon entropy in [0, 1] — entropy / log2(num_categories).

    1.0 = perfectly uniform distribution (maximum diversity)
    0.0 = single dominant category (zero diversity)

    Useful for comparing entropy across datasets with different category counts.

    Example
    -------
    norm_tbl = normalized_entropy(
        classified_reviews,
        group_cols=["product_id"],
        category_col="category",
        num_categories=4,
    )
    # → product_id | entropy | normalized_entropy | dominant_category | dominant_share
    """
    import math
    base = math.log2(num_categories)
    raw = category_entropy(table, group_cols, category_col)
    return raw.mutate(normalized_entropy=(raw.entropy / base))


def entropy_from_pandas(
    df: "pd.DataFrame",
    group_col: str,
    category_col: str,
    *,
    base: float = 2.0,
    count_col: Optional[str] = None,
) -> "pd.DataFrame":
    """
    Compute Shannon entropy from a pandas DataFrame using scipy.

    Works on raw rows (count_col=None) or pre-aggregated counts (count_col="n").

    Parameters
    ----------
    df            : DataFrame with at least group_col and category_col.
    group_col     : Column to group by (e.g. "product_id").
    category_col  : Column whose distribution is analysed (e.g. "category").
    base          : Logarithm base (2 = bits, math.e = nats). Default 2.
    count_col     : If provided, use this column as pre-computed counts instead of
                    counting rows.

    Returns
    -------
    DataFrame with columns:
        group_col, entropy, normalized_entropy, dominant_category, dominant_share
    """
    try:
        from scipy.stats import entropy as scipy_entropy
        import pandas as pd
    except ImportError as exc:
        raise ImportError("entropy_from_pandas requires: pip install scipy pandas") from exc

    import math

    if count_col:
        counts = df[[group_col, category_col, count_col]].copy()
        counts = counts.rename(columns={count_col: "_n"})
    else:
        counts = (
            df.groupby([group_col, category_col])
            .size()
            .reset_index(name="_n")
        )

    results = []
    for group_val, grp in counts.groupby(group_col):
        p = grp["_n"].values.astype(float)
        p /= p.sum()
        h = float(scipy_entropy(p, base=base))
        n_cats = len(p)
        h_max = math.log2(n_cats) if base == 2 and n_cats > 1 else (
            math.log(n_cats) if n_cats > 1 else 1.0
        )
        dominant_idx = grp["_n"].idxmax()
        results.append({
            group_col:             group_val,
            "entropy":             round(h, 4),
            "normalized_entropy":  round(h / h_max, 4) if h_max > 0 else 0.0,
            "dominant_category":   grp.loc[dominant_idx, category_col],
            "dominant_share":      round(float(grp.loc[dominant_idx, "_n"] / grp["_n"].sum()), 4),
        })

    import pandas as pd
    return pd.DataFrame(results).sort_values("entropy").reset_index(drop=True)

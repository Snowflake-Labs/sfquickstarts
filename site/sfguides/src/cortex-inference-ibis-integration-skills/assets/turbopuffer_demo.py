"""
turbopuffer_demo.py — Snowflake Cortex + Ibis + TurboPuffer end-to-end demo

Pipeline
--------
  pandas synthetic data
    → Ibis memtable (no persistent Snowflake table needed)
    → Cortex AI: sentiment, classification     [runs in Snowflake]
    → Cortex EMBED_TEXT_768: 768-dim vectors   [runs in Snowflake]
    → TurboPuffer namespace: upsert rows
    → TurboPuffer queries: ANN, hybrid, filtered, branching

Install
-------
  pip install 'ibis-framework[snowflake]' turbopuffer pandas pyarrow

Env vars
--------
  TURBOPUFFER_API_KEY=tpuf_A1...
  TURBOPUFFER_REGION=aws-us-east-1        # pick closest to your Snowflake region
  SNOWFLAKE_ACCOUNT=myorg-myaccount
  SNOWFLAKE_USER=you@example.com
"""

from __future__ import annotations

import json
import os
import textwrap
from typing import Optional

import pandas as pd
import ibis
import ibis.expr.datatypes as dt
from turbopuffer import Turbopuffer

# ── local module (same package) ──────────────────────────────────────────────
from cortex_ibis import (
    ai_sentiment,
    ai_classify,
    cortex_sentiment,
    variant_str,
    variant_float,
    EnrichmentPipeline,
)

ibis.options.interactive = True


# ─────────────────────────────────────────────────────────────────────────────
# 1.  SYNTHETIC  DATASET  (20 customer reviews, no Snowflake table required)
# ─────────────────────────────────────────────────────────────────────────────

REVIEWS = [
    (1,  "P001", "My order never arrived. Three weeks and nothing. I want a full refund immediately."),
    (2,  "P001", "Shipped fast, product works great. Very happy with the quality."),
    (3,  "P002", "I was charged twice for the same item. Please fix this billing error."),
    (4,  "P002", "Fantastic product, exactly as described. Will definitely buy again."),
    (5,  "P003", "The item arrived broken. Packaging was completely destroyed."),
    (6,  "P003", "Customer support resolved my issue in minutes. Outstanding service."),
    (7,  "P004", "Wrong item delivered. I ordered blue, got red. Very disappointing."),
    (8,  "P004", "Best purchase I've made this year. Exceeds all expectations."),
    (9,  "P005", "Delivery took 6 weeks. No communication whatsoever from the seller."),
    (10, "P005", "Reasonable price, solid build quality. Does exactly what it says."),
    (11, "P001", "The refund process is incredibly frustrating. Nobody responds to emails."),
    (12, "P002", "Smooth checkout, arrived on time, product works perfectly."),
    (13, "P003", "Defective unit out of the box. USB port doesn't work at all."),
    (14, "P004", "Impressed by the attention to detail. Premium feel for the price."),
    (15, "P005", "Tracking number never updated. I have no idea where my package is."),
    (16, "P001", "Returned the item, got store credit instead of the refund I requested."),
    (17, "P002", "Delivery driver left it in the rain. Everything was soaked."),
    (18, "P003", "Simple setup, intuitive interface. My kids love it."),
    (19, "P004", "Advertised as waterproof but it is clearly not. Broke after light rain."),
    (20, "P005", "Great value. Arrived ahead of schedule in perfect condition."),
]

raw_df = pd.DataFrame(REVIEWS, columns=["id", "product_id", "body"])


# ─────────────────────────────────────────────────────────────────────────────
# 2.  CONNECT  —  Snowflake (Ibis)  +  TurboPuffer
# ─────────────────────────────────────────────────────────────────────────────

def connect_snowflake() -> ibis.backends.snowflake.Backend:
    return ibis.snowflake.connect(
        user=os.environ["SNOWFLAKE_USER"],
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        database=os.environ.get("SNOWFLAKE_DATABASE", "SNOWFLAKE_SAMPLE_DATA/TPCH_SF1"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        authenticator=os.environ.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
    )


def connect_turbopuffer() -> Turbopuffer:
    return Turbopuffer(
        api_key=os.environ["TURBOPUFFER_API_KEY"],
        region=os.environ.get("TURBOPUFFER_REGION", "aws-us-east-1"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3.  STEP 1: CORTEX  ENRICHMENT  (sentiment + classification via Ibis)
# ─────────────────────────────────────────────────────────────────────────────

def enrich_reviews(con: ibis.backends.snowflake.Backend, df: pd.DataFrame) -> pd.DataFrame:
    """
    Upload df as an Ibis memtable, apply Cortex AI functions in Snowflake,
    return enriched pandas DataFrame.

    Snowflake executes everything in a single compiled SQL query.
    """
    tbl = ibis.memtable(df)  # ephemeral in-session table; no CREATE TABLE privilege needed

    categories = ["billing issue", "delivery problem", "product defect", "positive feedback"]

    classify_raw = ai_classify(tbl.body, categories)

    enriched = tbl.mutate(
        sentiment_label=ai_sentiment(tbl.body),
        sentiment_score=cortex_sentiment(tbl.body),
        category=variant_str(classify_raw, "label"),
        category_score=variant_float(classify_raw, "score"),
    )

    print("\n── Enrichment SQL (sent to Snowflake) ──────────────────────────────")
    print(ibis.to_sql(enriched, dialect="snowflake"))
    print("────────────────────────────────────────────────────────────────────\n")

    return enriched.execute()


# ─────────────────────────────────────────────────────────────────────────────
# 4.  STEP 2: GENERATE  EMBEDDINGS  via Snowflake Cortex
# ─────────────────────────────────────────────────────────────────────────────

_EMBED_MODEL = "snowflake-arctic-embed-m-v1.5"


def generate_embeddings(
    con: ibis.backends.snowflake.Backend,
    df: pd.DataFrame,
    text_col: str = "body",
) -> pd.DataFrame:
    """
    Generate 768-dim embeddings for each row using SNOWFLAKE.CORTEX.EMBED_TEXT_768.

    Returns df with a new 'vector' column (list[float]).

    Note: EMBED_TEXT_768 returns a VECTOR(FLOAT, 768) type in Snowflake.
    We CAST to VARCHAR so the Python connector can return it as a JSON string,
    then parse back to list[float].
    """
    # Build VALUES clause from df rows
    rows_sql = ",\n    ".join(
        f"({row.id}, $${row[text_col]}$$)"   # $$ quoting handles single quotes in text
        for row in df.itertuples()
    )

    sql = textwrap.dedent(f"""
        SELECT
            id,
            CAST(
                SNOWFLAKE.CORTEX.EMBED_TEXT_768('{_EMBED_MODEL}', body) AS VARCHAR
            ) AS vec_str
        FROM (VALUES {rows_sql}) AS t(id, body)
    """).strip()

    print("\n── Embedding SQL ────────────────────────────────────────────────────")
    print(sql[:300], "...")
    print("────────────────────────────────────────────────────────────────────\n")

    result = con.raw_sql(sql)
    rows = result.fetchall()
    result.close()

    vec_map = {row[0]: json.loads(row[1]) for row in rows}
    df = df.copy()
    df["vector"] = df["id"].map(vec_map)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 5.  STEP 3: INDEX  INTO  TURBOPUFFER
# ─────────────────────────────────────────────────────────────────────────────

_NAMESPACE = "cortex-ibis-reviews"
_SCHEMA = {
    "body":     {"type": "string", "full_text_search": True},
    "category": {"type": "string", "full_text_search": True},
    "product_id": {"type": "string"},
    "sentiment_label": {"type": "string"},
}


def index_to_turbopuffer(
    tpuf: Turbopuffer,
    df: pd.DataFrame,
    namespace: str = _NAMESPACE,
) -> None:
    """Upsert enriched+embedded rows into a TurboPuffer namespace."""
    ns = tpuf.namespace(namespace)

    upsert_rows = [
        {
            "id":              int(row.id),
            "vector":          row.vector,           # list[float], 768-dim
            "body":            row.body,
            "product_id":      row.product_id,
            "category":        row.category,
            "sentiment_label": row.sentiment_label,
            "sentiment_score": float(row.sentiment_score),
        }
        for row in df.itertuples()
    ]

    ns.write(
        upsert_rows=upsert_rows,
        distance_metric="cosine_distance",
        schema=_SCHEMA,
    )
    print(f"✓  Indexed {len(upsert_rows)} rows into TurboPuffer namespace '{namespace}'")


# ─────────────────────────────────────────────────────────────────────────────
# 6.  STEP 4: TURBOPUFFER  SEARCH  PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

def embed_query(con: ibis.backends.snowflake.Backend, text: str) -> list[float]:
    """Embed a query string via Snowflake Cortex. Returns list[float]."""
    sql = f"""
        SELECT CAST(
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('{_EMBED_MODEL}', $${text}$$) AS VARCHAR
        ) AS vec_str
    """
    result = con.raw_sql(sql)
    row = result.fetchone()
    result.close()
    return json.loads(row[0])


def demo_ann_search(tpuf: Turbopuffer, query_vec: list[float]) -> None:
    """Pure ANN: find nearest reviews by vector similarity."""
    print("\n── 6a. ANN Search ───────────────────────────────────────────────────")
    ns = tpuf.namespace(_NAMESPACE)

    results = ns.query(
        rank_by=("vector", "ANN", query_vec),
        limit=5,
        include_attributes=["body", "category", "sentiment_label"],
    )
    for row in results.rows:
        print(f"  [{row.id:2d}] dist={row.__dict__.get('$dist', '?'):.4f}  "
              f"[{row.sentiment_label}] {row.body[:70]}...")


def demo_filtered_search(tpuf: Turbopuffer, query_vec: list[float]) -> None:
    """ANN restricted to negative reviews only."""
    print("\n── 6b. Filtered ANN (negative reviews only) ─────────────────────────")
    ns = tpuf.namespace(_NAMESPACE)

    results = ns.query(
        rank_by=("vector", "ANN", query_vec),
        filters=("sentiment_label", "Eq", "negative"),
        limit=5,
        include_attributes=["body", "category", "sentiment_label"],
    )
    for row in results.rows:
        dist = row.__dict__.get("$dist", "?")
        print(f"  [{row.id:2d}] dist={dist:.4f}  [{row.category}] {row.body[:65]}...")


def demo_hybrid_search(tpuf: Turbopuffer, query_vec: list[float], query_text: str) -> None:
    """
    Hybrid search: 70% vector ANN + 30% BM25 full-text.
    Best for when semantic closeness AND keyword relevance both matter.
    """
    print("\n── 6c. Hybrid Search (ANN 0.7 + BM25 0.3) ──────────────────────────")
    ns = tpuf.namespace(_NAMESPACE)

    results = ns.query(
        rank_by=("Sum", [
            ("Product", 0.7, ("vector", "ANN", query_vec)),
            ("Product", 0.3, ("body",   "BM25", query_text)),
        ]),
        limit=5,
        include_attributes=["body", "category", "sentiment_label"],
    )
    for row in results.rows:
        dist = row.__dict__.get("$dist", "?")
        print(f"  [{row.id:2d}] score={dist:.4f}  [{row.category}] {row.body[:65]}...")


def demo_category_filter(tpuf: Turbopuffer, query_vec: list[float]) -> None:
    """ANN scoped to a specific Cortex-assigned category."""
    print("\n── 6d. Category-filtered Search (billing issues) ────────────────────")
    ns = tpuf.namespace(_NAMESPACE)

    results = ns.query(
        rank_by=("vector", "ANN", query_vec),
        filters=("category", "Eq", "billing issue"),
        limit=5,
        include_attributes=["body", "product_id", "sentiment_score"],
    )
    for row in results.rows:
        dist = row.__dict__.get("$dist", "?")
        print(f"  [{row.id:2d}] dist={dist:.4f}  product={row.product_id}  {row.body[:65]}...")


def demo_fts_only(tpuf: Turbopuffer) -> None:
    """Pure BM25 full-text search — no vector needed."""
    print("\n── 6e. Full-Text Search only (BM25) ─────────────────────────────────")
    ns = tpuf.namespace(_NAMESPACE)

    results = ns.query(
        rank_by=("body", "BM25", "refund missing package"),
        limit=5,
        include_attributes=["body", "category"],
    )
    for row in results.rows:
        dist = row.__dict__.get("$dist", "?")
        print(f"  [{row.id:2d}] bm25={dist:.4f}  [{row.category}] {row.body[:65]}...")


def demo_aggregations(tpuf: Turbopuffer) -> None:
    """Count reviews per category (no LLM call needed)."""
    print("\n── 6f. Grouped Aggregations ─────────────────────────────────────────")
    ns = tpuf.namespace(_NAMESPACE)

    result = ns.query(
        aggregate_by={"count": ("Count",)},
        group_by=["category"],
    )
    for row in result.aggregation_groups:
        print(f"  {row.category:<25}  count={row.count}")


def demo_branching(tpuf: Turbopuffer) -> None:
    """
    Clone namespace for safe experimentation.
    Branches are copy-on-write; creation is O(1) regardless of size.
    """
    print("\n── 6g. Namespace Branching ───────────────────────────────────────────")
    branch_ns = f"{_NAMESPACE}-branch"
    branch = tpuf.namespace(branch_ns)
    branch.write(branch_from_namespace=_NAMESPACE)
    print(f"  Branched '{_NAMESPACE}' → '{branch_ns}'")

    # Verify: query the branch independently
    result = branch.query(
        rank_by=("body", "BM25", "refund"),
        limit=3,
        include_attributes=["body"],
    )
    print(f"  Branch query returned {len(result.rows)} rows (independent of main)")

    # Clean up branch
    branch.delete_all_rows()
    print(f"  Cleaned up branch namespace '{branch_ns}'")


# ─────────────────────────────────────────────────────────────────────────────
# 7.  ROUND-TRIP  — bring TurboPuffer results back through Ibis
# ─────────────────────────────────────────────────────────────────────────────

def results_to_ibis(
    con: ibis.backends.snowflake.Backend,
    tpuf: Turbopuffer,
    query_vec: list[float],
    top_k: int = 10,
) -> pd.DataFrame:
    """
    Fetch ANN results from TurboPuffer, convert to Ibis memtable,
    then apply a Cortex summarisation across the result set —
    demonstrating TurboPuffer → Ibis → Cortex chaining.
    """
    print("\n── 7. Round-trip: TurboPuffer → Ibis → Cortex summarise ─────────────")
    ns = tpuf.namespace(_NAMESPACE)

    hits = ns.query(
        rank_by=("vector", "ANN", query_vec),
        limit=top_k,
        include_attributes=["body", "category", "sentiment_label", "product_id"],
    )

    rows = [
        {
            "id":              r.id,
            "body":            r.body,
            "product_id":      r.product_id,
            "category":        r.category,
            "sentiment_label": r.sentiment_label,
            "dist":            r.__dict__.get("$dist", None),
        }
        for r in hits.rows
    ]
    hits_df = pd.DataFrame(rows)

    # Load back into Ibis and apply AI_COMPLETE to generate a group summary
    from cortex_ibis import ai_complete
    hits_tbl = ibis.memtable(hits_df)
    with_reply = hits_tbl.mutate(
        draft_reply=ai_complete(
            "llama3.1-70b",
            "Write a one-sentence customer service acknowledgement for: " + hits_tbl.body,
        )
    )

    enriched_hits = with_reply.execute()
    print(enriched_hits[["id", "dist", "category", "draft_reply"]].to_string(index=False))
    return enriched_hits


# ─────────────────────────────────────────────────────────────────────────────
# 8.  MAIN  RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("  Snowflake Cortex + Ibis + TurboPuffer — end-to-end demo")
    print("=" * 70)

    # ── Connect ───────────────────────────────────────────────────────────
    print("\n[1/5] Connecting …")
    con  = connect_snowflake()
    tpuf = connect_turbopuffer()
    print(f"  Snowflake: {con.current_catalog} / {con.current_database}")
    print(f"  TurboPuffer region: {os.environ.get('TURBOPUFFER_REGION', 'aws-us-east-1')}")

    # ── Enrich with Cortex (sentiment + classification) ───────────────────
    print("\n[2/5] Enriching 20 reviews with Cortex AI (sentiment + classify) …")
    enriched_df = enrich_reviews(con, raw_df)
    print(enriched_df[["id", "sentiment_label", "sentiment_score", "category"]].to_string(index=False))

    # ── Generate embeddings ───────────────────────────────────────────────
    print("\n[3/5] Generating 768-dim embeddings via CORTEX.EMBED_TEXT_768 …")
    embedded_df = generate_embeddings(con, enriched_df)
    print(f"  Generated {len(embedded_df)} vectors of dim {len(embedded_df['vector'].iloc[0])}")

    # ── Index into TurboPuffer ────────────────────────────────────────────
    print("\n[4/5] Indexing into TurboPuffer …")
    index_to_turbopuffer(tpuf, embedded_df)

    # ── Search demos ──────────────────────────────────────────────────────
    print("\n[5/5] Running search demos …")
    query_text = "my order is missing and I need a refund"
    query_vec  = embed_query(con, query_text)
    print(f"\n  Query: \"{query_text}\"")

    demo_ann_search(tpuf, query_vec)
    demo_filtered_search(tpuf, query_vec)
    demo_hybrid_search(tpuf, query_vec, query_text)
    demo_category_filter(tpuf, query_vec)
    demo_fts_only(tpuf)
    demo_aggregations(tpuf)
    demo_branching(tpuf)
    results_to_ibis(con, tpuf, query_vec)

    print("\n" + "=" * 70)
    print("  Done.")
    print("=" * 70)


if __name__ == "__main__":
    main()

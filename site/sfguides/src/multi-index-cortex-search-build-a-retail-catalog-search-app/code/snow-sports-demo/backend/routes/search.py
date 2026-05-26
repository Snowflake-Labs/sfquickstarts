"""
Search Routes — Cortex Multi-Index Search
------------------------------------------
Single PRODUCT_SEARCH service with TEXT INDEXES (BRAND, ITEM_NAME, SUBCATEGORY)
and VECTOR INDEXES (SEARCH_TEXT). Queries all indexes simultaneously via
multi_index_query. Category breakdown is derived from the CATEGORY attribute
on each result.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from snowflake.core import Root

from services.snowflake_client import get_snowpark_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "Equipment":   "#3B82F6",
    "Apparel":     "#10B981",
    "Protection":  "#F59E0B",
    "Accessories": "#8B5CF6",
}

_DB      = "CATALOG_SEARCH_DB"
_SCHEMA  = "APP"
_SERVICE = "PRODUCT_SEARCH"

_SEARCH_COLUMNS = [
    "PRODUCT_ID",
    "ITEM_NAME",
    "BRAND",
    "CATEGORY",
    "SUBCATEGORY",
    "SKILL_LEVEL",
    "DISCIPLINE",
    "GENDER",
    "PRICE",
    "PRODUCT_TYPE",
    "FLEX_RATING",
]

# Fetch more candidates than we return so score-based trimming has enough range
_FETCH_LIMIT = 100

# ---------------------------------------------------------------------------
# Service handle cache
# ---------------------------------------------------------------------------

_root: Optional[Root] = None
_service = None


def _get_service():
    global _root, _service
    if _service is None:
        session = get_snowpark_session()
        _root = Root(session)
        _service = (
            _root
            .databases[_DB]
            .schemas[_SCHEMA]
            .cortex_search_services[_SERVICE]
        )
        logger.info("Cortex Search service handle initialised: %s", _SERVICE)
    return _service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_result(row: dict) -> dict:
    raw_price = row.get("PRICE", 0)
    try:
        price = float(raw_price)
    except (TypeError, ValueError):
        price = 0.0

    scores = row.get("@scores", {}) or {}
    reranker = scores.get("reranker_score", scores.get("cosine_similarity", 0)) or 0

    category = row.get("CATEGORY", "")
    return {
        "product_id":   row.get("PRODUCT_ID"),
        "item_name":    row.get("ITEM_NAME"),
        "brand":        row.get("BRAND"),
        "category":     category,
        "subcategory":  row.get("SUBCATEGORY"),
        "skill_level":  row.get("SKILL_LEVEL"),
        "discipline":   row.get("DISCIPLINE"),
        "gender":       row.get("GENDER"),
        "price":        price,
        "product_type": row.get("PRODUCT_TYPE"),
        "flex_rating":  row.get("FLEX_RATING"),
        "_score":       float(reranker),
        # Category used as the "source" for the breakdown chart
        "source_index": category,
        "source_label": category,
        "source_color": CATEGORY_COLORS.get(category, "#64748B"),
    }


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=20, ge=1, le=100)
    filters: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/multi")
async def multi_search(body: SearchRequest):
    """
    Query PRODUCT_SEARCH across all column indexes simultaneously:
      TEXT INDEXES:   BRAND, ITEM_NAME, SUBCATEGORY  (keyword/BM25)
      VECTOR INDEXES: SEARCH_TEXT                    (semantic)
    Results are sorted by reranker score. Category breakdown is derived
    from the CATEGORY attribute on each result.
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    try:
        svc = _get_service()

        search_kwargs: dict = {
            "multi_index_query": {
                "BRAND":       [{"text": body.query}],
                "ITEM_NAME":   [{"text": body.query}],
                "SUBCATEGORY": [{"text": body.query}],
                "SEARCH_TEXT": [{"text": body.query}],
            },
            "columns": _SEARCH_COLUMNS,
            "limit":   _FETCH_LIMIT,
        }

        if body.filters:
            search_kwargs["filter"] = {
                "@and": [{"@eq": {k: v}} for k, v in body.filters.items()]
            }

        response = svc.search(**search_kwargs)
        rows = response.results if hasattr(response, "results") else (response or [])

    except Exception as exc:
        logger.error("Search error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    # Results are already ranked by the Cortex Search reranker — preserve order
    results = [_row_to_result(r) for r in rows]
    results = results[: body.limit]

    # Build category breakdown from the returned results
    index_breakdown: dict = {
        cat: {"count": 0, "label": cat, "color": CATEGORY_COLORS[cat]}
        for cat in CATEGORY_COLORS
    }
    for r in results:
        cat = r["category"]
        if cat in index_breakdown:
            index_breakdown[cat]["count"] += 1

    return {
        "query":           body.query,
        "total_results":   len(results),
        "results":         results,
        "index_breakdown": index_breakdown,
    }


@router.get("/single/{service_name}")
async def single_search(
    service_name: str,
    q: str = Query(..., description="Search query string"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Thin passthrough kept for notebook demos — just calls the main service."""
    body = SearchRequest(query=q, limit=limit)
    return await multi_search(body)

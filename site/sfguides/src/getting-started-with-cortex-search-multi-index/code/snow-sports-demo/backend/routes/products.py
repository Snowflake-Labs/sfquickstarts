"""
Product Catalog Routes
-----------------------
Paginated browsing and filtering of the CATALOG_SEARCH_DB.DATA.PRODUCTS table.
Uses parameterized queries via snowflake.connector to prevent SQL injection.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from services.snowflake_client import get_cursor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])

# Fully-qualified table reference
_PRODUCTS_TABLE = "CATALOG_SEARCH_DB.DATA.PRODUCTS"

# Columns returned in listing / detail responses
_LIST_COLUMNS = (
    "PRODUCT_ID, ITEM_NAME, DESCRIPTION, CATEGORY, SUBCATEGORY, BRAND, "
    "PRICE, SKILL_LEVEL, DISCIPLINE, GENDER, PRODUCT_TYPE, FLEX_RATING, WEIGHT_G"
)


def _row_to_dict(row: dict) -> dict:
    """Lower-case all column keys for a consistent JSON response."""
    return {k.lower(): v for k, v in row.items()}


# ---------------------------------------------------------------------------
# GET /api/products
# ---------------------------------------------------------------------------

@router.get("")
async def list_products(
    category:    Optional[str]   = Query(default=None),
    brand:       Optional[str]   = Query(default=None),
    skill_level: Optional[str]   = Query(default=None),
    discipline:  Optional[str]   = Query(default=None),
    gender:      Optional[str]   = Query(default=None),
    min_price:   Optional[float] = Query(default=None, ge=0),
    max_price:   Optional[float] = Query(default=None, ge=0),
    limit:       int             = Query(default=20, ge=1, le=200),
    offset:      int             = Query(default=0, ge=0),
):
    """
    Return a paginated, filtered list of products.
    All filter parameters are optional and ANDed together.
    """
    where_clauses: list[str] = []
    bind_params: list = []

    # Build WHERE clauses dynamically — use %s placeholders (pyformat style)
    filters_applied: dict = {}

    if category:
        where_clauses.append("CATEGORY = %s")
        bind_params.append(category)
        filters_applied["category"] = category

    if brand:
        where_clauses.append("BRAND = %s")
        bind_params.append(brand)
        filters_applied["brand"] = brand

    if skill_level:
        where_clauses.append("SKILL_LEVEL = %s")
        bind_params.append(skill_level)
        filters_applied["skill_level"] = skill_level

    if discipline:
        where_clauses.append("DISCIPLINE = %s")
        bind_params.append(discipline)
        filters_applied["discipline"] = discipline

    if gender:
        where_clauses.append("GENDER = %s")
        bind_params.append(gender)
        filters_applied["gender"] = gender

    if min_price is not None:
        where_clauses.append("PRICE >= %s")
        bind_params.append(min_price)
        filters_applied["min_price"] = min_price

    if max_price is not None:
        where_clauses.append("PRICE <= %s")
        bind_params.append(max_price)
        filters_applied["max_price"] = max_price

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    count_sql = f"SELECT COUNT(*) AS CNT FROM {_PRODUCTS_TABLE} {where_sql}"
    data_sql  = (
        f"SELECT {_LIST_COLUMNS} "
        f"FROM {_PRODUCTS_TABLE} {where_sql} "
        f"ORDER BY PRODUCT_ID "
        f"LIMIT %s OFFSET %s"
    )

    try:
        with get_cursor() as cur:
            # Total count (reuse same bind params, no limit/offset)
            cur.execute(count_sql, bind_params)
            total = cur.fetchone()["CNT"]

            # Paginated rows
            cur.execute(data_sql, bind_params + [limit, offset])
            rows = cur.fetchall()

    except Exception as exc:
        logger.error("Error fetching products: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch products")

    return {
        "products":        [_row_to_dict(r) for r in rows],
        "total":           total,
        "limit":           limit,
        "offset":          offset,
        "filters_applied": filters_applied,
    }


# ---------------------------------------------------------------------------
# GET /api/products/meta/filters  — must come before /{product_id}
# ---------------------------------------------------------------------------

@router.get("/meta/filters")
async def get_filter_options():
    """
    Return distinct values for all filterable fields.
    Used by the frontend to populate dropdown/chip filter controls.
    """
    fields = {
        "categories":   "CATEGORY",
        "brands":       "BRAND",
        "skill_levels": "SKILL_LEVEL",
        "disciplines":  "DISCIPLINE",
        "genders":      "GENDER",
    }

    result: dict = {}

    try:
        with get_cursor() as cur:
            for key, column in fields.items():
                cur.execute(
                    f"SELECT DISTINCT {column} AS VAL "
                    f"FROM {_PRODUCTS_TABLE} "
                    f"WHERE {column} IS NOT NULL "
                    f"ORDER BY {column}"
                )
                result[key] = [r["VAL"] for r in cur.fetchall()]
    except Exception as exc:
        logger.error("Error fetching filter options: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch filter options")

    return result


# ---------------------------------------------------------------------------
# GET /api/products/{product_id}
# ---------------------------------------------------------------------------

@router.get("/{product_id}")
async def get_product(product_id: int):
    """Return the full detail record for a single product."""
    sql = (
        f"SELECT {_LIST_COLUMNS} "
        f"FROM {_PRODUCTS_TABLE} "
        f"WHERE PRODUCT_ID = %s "
        f"LIMIT 1"
    )

    try:
        with get_cursor() as cur:
            cur.execute(sql, (product_id,))
            row = cur.fetchone()
    except Exception as exc:
        logger.error("Error fetching product %s: %s", product_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch product")

    if row is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    return _row_to_dict(row)

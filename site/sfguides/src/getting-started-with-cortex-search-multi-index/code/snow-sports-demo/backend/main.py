"""
Snow Sports Catalog Search — FastAPI Backend
=============================================
Entry point for the backend API. Demonstrates:
  - Cortex Search multi-index (single service with TEXT + VECTOR indexes)
  - Parameterized product catalog browsing with filters
  - Static file serving of the React frontend (production / SPCS)

Run locally:
  uvicorn main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import search, products
from services.snowflake_client import close_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("Starting Snow Sports Catalog Search backend")
    yield
    close_connection()
    logger.info("Backend shutdown complete")


app = FastAPI(
    title="Snow Sports Catalog Search",
    description="Demo backend showcasing Snowflake Cortex Search multi-index",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow all origins for local development
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

app.include_router(search.router)
app.include_router(products.router)


@app.get("/api/health")
async def health():
    """Simple liveness check — also confirms which Snowflake database is targeted."""
    return {"status": "ok", "database": "CATALOG_SEARCH_DB"}


# ---------------------------------------------------------------------------
# Serve React frontend static files in production (SPCS / Docker)
# ---------------------------------------------------------------------------

_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
    logger.info("Serving frontend from %s", _frontend_dist)

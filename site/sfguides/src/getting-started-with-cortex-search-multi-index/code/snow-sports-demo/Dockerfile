# =============================================================================
# Snow Sports Catalog Search — Multi-stage Docker build
# Stage 1: Build React frontend static assets
# Stage 2: Python FastAPI server serving the React app + API routes
# =============================================================================

# --- Stage 1: Build React frontend ---
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first (layer caching)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python FastAPI backend ---
FROM python:3.11-slim AS production

WORKDIR /app

# Install system dependencies required by the Snowflake connector
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built React assets from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Environment variables (overridden by SPCS spec or docker run)
ENV SNOWFLAKE_DATABASE=CATALOG_SEARCH_DB
ENV SNOWFLAKE_SCHEMA=APP
ENV SNOWFLAKE_WAREHOUSE=CATALOG_SEARCH_WH
ENV PORT=8000

EXPOSE 8000

# Run from the backend directory so relative imports work
WORKDIR /app/backend

# Run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

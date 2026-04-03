# Build an AI Matching App with Snowflake ML - Assets

This folder contains all the source code for the **Build an AI Matching App with Snowflake ML** quickstart guide.

## Quick Start

### Option A: Download Individual Files

Browse the folders below on GitHub and download the files you need.

### Option B: Sparse Clone (recommended for Git users)

Download only this guide's files (~5 MB instead of the full repository):

```bash
git clone --no-checkout --depth 1 --filter=blob:none --sparse \
  https://github.com/Snowflake-Labs/sfquickstarts.git
cd sfquickstarts
git sparse-checkout set site/sfguides/src/build-an-ai-matching-app-with-snowflake-ml/assets
```

## Folder Structure

```
assets/
├── README.md
├── app/
│   ├── streamlit_app.py          # 6-page Streamlit dashboard
│   └── environment.yml           # Streamlit package dependencies
├── notebooks/
│   ├── creator_brand_match.py    # Core ML notebook (Feature Store → Registry → SPCS → API)
│   └── environment.yml           # Notebook package dependencies
├── scripts/
│   └── generate_synthetic_data.py  # Archetype-driven synthetic data generator
└── sql/
    ├── 00_setup.sql              # Database, warehouse, compute pool, tables, Dynamic Table
    └── 99_teardown.sql           # Clean up all demo objects
```

## What Each File Does

| File | Purpose |
|------|---------|
| `sql/00_setup.sql` | Creates the CC_DEMO database, warehouse, compute pool, raw tables, and a Dynamic Table for engagement features |
| `scripts/generate_synthetic_data.py` | Generates 500K behavioral events across 10K creators and 1K brands using archetype-driven distributions |
| `notebooks/creator_brand_match.py` | End-to-end ML workflow: Feature Store, model training, Registry, SPCS deployment, Cortex Search, CDP enrichment |
| `app/streamlit_app.py` | Interactive 6-page dashboard: Feature Store, Model Registry, Inference, CDP Profiles, Cortex Search, Model Monitoring |

## Prerequisites

- Snowflake account (Enterprise Edition or higher recommended)
- Python 3.9+ with pip or conda
- A role with privileges to create databases, warehouses, compute pools, and Streamlit apps

## Cleanup

Run `sql/99_teardown.sql` in a Snowsight SQL worksheet to remove all objects created by this guide.

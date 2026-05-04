# Iceberg V3 Tables Comprehensive Guide - Assets

This folder contains all the scripts, sample data, and notebooks for the **Iceberg V3 Tables Comprehensive Guide**.

## 📋 Overview

Build a complete analytics platform using Snowflake's Iceberg V3 tables with:
- **Streaming ingestion** via Snowpipe Streaming
- **Semi-structured data** with VARIANT columns
- **Time-series analytics** with nanosecond precision
- **Geospatial intelligence** with GEOGRAPHY types
- **Dynamic Tables** for declarative transformations
- **Enterprise governance** with masking and data quality
- **AI agents** via Snowflake Intelligence
- **Spark interoperability** with enforced access controls

## 🚀 Quick Start

### 1. Download and Configure

```bash
# Clone the sfquickstarts repo and navigate to the assets
git clone https://github.com/Snowflake-Labs/sfquickstarts.git
cd sfquickstarts/site/sfguides/src/iceberg-v3-tables-comprehensive-guide/assets

# Copy the template and edit with your values
cp config.env.template config.env
# Edit config.env with your Snowflake account details
```

### 2. Run Setup

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Import the Snowflake Notebook

1. Sign in to [Snowsight](https://app.snowflake.com)
2. Navigate to **Projects » Notebooks**
3. Click the down arrow next to **+ Notebook** and select **Import .ipynb file**
4. Select `fleet_analytics_notebook.ipynb` from this folder
5. Set the notebook location to `FLEET_ANALYTICS_DB.RAW` and warehouse to `FLEET_ANALYTICS_WH`
6. Click **Create** to import

For more details, see [Create a notebook](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-create#create-a-new-notebook).

### 4. Start Streaming (Optional)

```bash
source iceberg_v3_demo_venv/bin/activate
python stream_telemetry.py
```

### 5. Follow the Guide

Open the [Snowflake Quickstart Guide](https://www.snowflake.com/en/developers/guides/iceberg-v3-tables-comprehensive-guide/) and follow along!

## 📁 Folder Structure

```
assets/
├── config.env.template           # Configuration template (copy to config.env)
├── setup.sh                      # Main setup script
├── README.md
│
├── 02_create_database.sql        # SQL setup scripts
├── 03_create_iceberg_tables.sql
├── 04_create_dynamic_tables.sql
├── 05_create_governance.sql
├── 06_load_sample_data.sql
├── 07_create_agent.sql
├── 08_network_policy.sql
│
├── stream_telemetry.py           # Snowpipe Streaming simulator
│
├── maintenance_log_001.json      # Sample JSON files (10 files total)
├── maintenance_log_002.json
├── ...
├── fleet_semantic_model.yaml     # Semantic model for Cortex Agent
│
├── fleet_analytics_notebook.ipynb    # Snowflake Notebook
├── spark_iceberg_interop.ipynb       # Spark interoperability notebook
│
├── create_external_volume.png    # Guide images
├── dit_graph.png
├── ...
```

## ⚙️ Configuration Options

### Iceberg storage (default: Snowflake-managed)

By default, `USE_SNOWFLAKE_STORAGE=true` stores Iceberg table files in [Snowflake-managed storage](https://docs.snowflake.com/en/user-guide/tables-iceberg-internal-storage) (`SNOWFLAKE_MANAGED`). No external volume or cloud bucket setup is required (AWS- and Azure-hosted accounts only).

**Customer-managed object storage** — set `USE_SNOWFLAKE_STORAGE=false`, then either:

**Use an existing external volume**
```env
USE_SNOWFLAKE_STORAGE=false
USE_EXISTING_VOLUME=true
EXISTING_VOLUME_NAME="your_volume_name"
```

**Create a new external volume (`FLEET_ICEBERG_VOL`)**
```env
USE_SNOWFLAKE_STORAGE=false
USE_EXISTING_VOLUME=false
STORAGE_PROVIDER="S3"  # S3, GCS, AZURE
```

See `config.env.template` for provider-specific configuration (S3, GCS, Azure).

## 🎯 Use Case: Smart Fleet IoT Analytics

The guide uses a realistic fleet management scenario:

| Data Type | Table | Description |
|-----------|-------|-------------|
| Streaming VARIANT | `VEHICLE_TELEMETRY_STREAM` | Real-time vehicle telemetry |
| Batch VARIANT | `MAINTENANCE_LOGS` | JSON diagnostic logs |
| Time-series | `SENSOR_READINGS` | High-precision sensor data |
| Geospatial | `VEHICLE_LOCATIONS` | GPS positions with GEOGRAPHY |
| Master data | `VEHICLE_REGISTRY` | Vehicle and driver info (PII) |
| API data | `API_WEATHER_DATA` | Weather data from Open-Meteo |

## 📊 Dynamic Tables Created

| Table | Purpose | Target Lag |
|-------|---------|------------|
| `TELEMETRY_ENRICHED` | Joins telemetry with vehicle registry | 1 minute |
| `MAINTENANCE_ANALYSIS` | Extracts and enriches maintenance logs | 5 minutes |
| `DAILY_FLEET_SUMMARY` | Daily aggregated metrics | 5 minutes |
| `VEHICLE_HEALTH_SCORE` | Rolling health scores | 10 minutes |

## 🔒 Governance Features

- **Masking Policies**: PII protection for driver information
- **Data Metric Functions**: Quality checks for coordinates, vehicle IDs
- **Classification Tags**: Data sensitivity and domain tags
- **Access Roles**: FLEET_ANALYST (masked) vs FLEET_ENGINEER (full access)

## 🔧 Prerequisites

### Required
- Snowflake account with ACCOUNTADMIN access
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation) installed
- Python 3.9+ with pip

### For Spark Interoperability
- Conda package manager
- Apache Spark 4.0+ (for VARIANT support)

### For customer-managed Iceberg storage (optional)
- Set `USE_SNOWFLAKE_STORAGE=false` in `config.env`
- AWS S3, GCS, Azure Blob, ADLS Gen2, or OneLake bucket/container and IAM roles or service principals

## 📚 Related Documentation

- [Iceberg Tables in Snowflake](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Snowflake storage for Iceberg tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-internal-storage)
- [Snowpipe Streaming](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)

## 🧹 Cleanup

To remove all objects created by this guide:

```sql
DROP DATABASE IF EXISTS FLEET_ANALYTICS_DB CASCADE;
-- Only if you used customer-managed storage (USE_SNOWFLAKE_STORAGE=false)
DROP EXTERNAL VOLUME IF EXISTS FLEET_ICEBERG_VOL;
DROP WAREHOUSE IF EXISTS FLEET_ANALYTICS_WH;
DROP ROLE IF EXISTS FLEET_ANALYST;
DROP ROLE IF EXISTS FLEET_ENGINEER;
```

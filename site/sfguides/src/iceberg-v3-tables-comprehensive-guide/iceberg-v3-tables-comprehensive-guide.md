authors: Scott Teal (scottteal)
id: iceberg-v3-tables-comprehensive-guide
summary: Build an end-to-end enterprise lakehouse platform using Iceberg V3 tables with streaming, variant data, time-series, geospatial analytics, governance, and AI.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/lakehouse-analytics, snowflake-site:taxonomy/snowflake-feature/apache-iceberg, snowflake-site:taxonomy/snowflake-feature/ingestion, snowflake-site:taxonomy/snowflake-feature/interoperable-storage, snowflake-site:taxonomy/snowflake-feature/transformation, snowflake-site:taxonomy/snowflake-feature/geospatial, snowflake-site:taxonomy/snowflake-feature/time-series-functions, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/snowflake-ml-functions, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/snowflake-feature/snowpipe-streaming, snowflake-site:taxonomy/snowflake-feature/horizon, snowflake-site:taxonomy/snowflake-feature/data-lake
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/iceberg-v3-tables-comprehensive-guide/assets


# Enterprise Lakehouse Platform for Iceberg V3
<!-- ------------------------ -->
## Overview

This comprehensive guide demonstrates how to build a complete data engineering, analytics, and AI platform using Snowflake's Iceberg V3 tables. You'll work with a realistic Smart Fleet IoT Analytics use case that encompasses streaming semi-structured data, JSON log analysis, time-series analytics with nanosecond precision, and geospatial intelligence.

Apache Iceberg V3 tables in Snowflake support the VARIANT data type, enabling efficient storage and querying of semi-structured data while maintaining the open table format's interoperability benefits. Combined with Snowflake's enterprise features for governance, AI/ML, and business continuity, you can build a truly modern lakehouse architecture.

### Use Case: Smart Fleet IoT Analytics

You'll build an analytics platform for a fleet management company that:

- **Streams real-time vehicle telemetry** - Speed, location, engine diagnostics, fuel consumption as semi-structured VARIANT data
- **Ingests maintenance logs** - JSON-formatted diagnostic reports and service records from cloud storage
- **Analyzes time-series sensor data** - High-precision timestamp data for trend analysis and forecasting
- **Performs geospatial analytics** - Route optimization, geofencing, location-based insights
- **Powers AI agents** - Natural language querying of fleet analytics via Snowflake Intelligence

### What You Will Learn

- Creating and managing Iceberg V3 tables with Snowflake Horizon Catalog
- Streaming semi-structured data into VARIANT columns in Iceberg tables using Snowpipe Streaming
- Ingesting data from web APIs and batch loading JSON logs
- Building declarative transformation pipelines with Dynamic Iceberg Tables, powered by row lineage
- Applying enterprise governance: PII detection, masking policies, data quality
- Performing time-series analysis, forecasting, and geospatial analytics with Iceberg v3 data types
- Enabling AI agents on Iceberg data with Snowflake Intelligence
- Setting up cross-region replication for business continuity on v3 Iceberg tables
- Querying Iceberg tables from Apache Spark via Iceberg REST API with vended storage credentials and Horizon fine-grained access controls

### What You Will Build

- **6+ Iceberg V3 tables** covering streaming events, logs, time-series, and geospatial data
- **Dynamic Iceberg Tables** for automated incremental transformations
- **Streaming pipeline** using Snowpipe Streaming with Python SDK
- **Governance framework** with masking policies and data quality functions
- **ML forecasting model** for predictive maintenance
- **Snowflake Intelligence agent** for natural language analytics
- **Spark notebooks** demonstrating interoperability with enforced access controls

### Prerequisites

**Snowflake Requirements:**
- Snowflake account with `ACCOUNTADMIN` role access
- Standard Edition or higher (Enterprise features noted where applicable)
- Ability to create databases, schemas, warehouses, and Iceberg tables

**Required Tools:**
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation) installed with a [configured connection](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/specify-credentials)
- Python 3.9+ with pip

> **Snowflake CLI Connection**: Before running the setup, configure a connection named `default`:
> ```bash
> snow connection add --connection-name default --account <your-account> --user <your-user>
> ```

**For External Storage:**
- AWS S3, Google Cloud Storage, or Azure Storage (Blob, ADLS Gen2, or OneLake)
- Appropriate IAM roles/service principals configured

**For Spark Interoperability Section:**
- Conda package manager installed (for isolated PySpark environment)
- Apache Spark 4.0+ (required for VARIANT support in Iceberg V3)

> **Note**: At the time of writing, Spark does not support nanosecond timestamps or geospatial data types in Iceberg tables.

### Objects Created in This Guide

| Object Type | Name | Purpose |
|------------|------|---------|
| Database | FLEET_ANALYTICS_DB | Contains all demo objects |
| Warehouse | FLEET_ANALYTICS_WH | Compute for all operations |
| External Volume | FLEET_ICEBERG_VOL | Storage for Iceberg data |
| Iceberg Table | VEHICLE_TELEMETRY_STREAM | Real-time streaming events (VARIANT) |
| Iceberg Table | MAINTENANCE_LOGS | Batch-loaded JSON logs (VARIANT) |
| Iceberg Table | SENSOR_READINGS | Time-series sensor data |
| Iceberg Table | VEHICLE_LOCATIONS | Geospatial vehicle positions |
| Iceberg Table | VEHICLE_REGISTRY | Vehicle master data |
| Iceberg Table | API_WEATHER_DATA | Weather data from public API (VARIANT) |
| Dynamic Table | TELEMETRY_ENRICHED | Joined and enriched telemetry |
| Dynamic Table | DAILY_FLEET_SUMMARY | Aggregated fleet analytics |
| Masking Policy | PII_MASK | Masks sensitive driver information |
| Data Metric Function | CHECK_VALID_COORDINATES | Validates geospatial data |
| Stage | LOGS_STAGE | Internal stage for JSON files |
| External Access Integration | OPEN_METEO_ACCESS | Allows notebook API calls |
| Network Policy (optional) | FLEET_STREAMING_POLICY | Allows streaming script connections |
| Cortex Agent | FLEET_ANALYTICS_AGENT | Natural language querying of fleet data |

<!-- ------------------------ -->
## Environment Setup

This section guides you through setting up your environment. The setup is designed to be as simple as possible: clone the repo, configure a few variables, and run the setup script.

### Step 1: Download the Assets

Download or clone the guide assets from the [assets folder](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/iceberg-v3-tables-comprehensive-guide/assets):

```bash
# Clone the sfquickstarts repo and navigate to the assets
git clone https://github.com/Snowflake-Labs/sfquickstarts.git
cd sfquickstarts/site/sfguides/src/iceberg-v3-tables-comprehensive-guide/assets
```

### Step 2: Configure Variables

Edit the `config.env` file in the repository root:

```bash
# Required: Snowflake Account Information
SNOWFLAKE_ACCOUNT="your_account_identifier"
SNOWFLAKE_USER="your_username"
SNOWFLAKE_ROLE="ACCOUNTADMIN"
SNOWFLAKE_WAREHOUSE="FLEET_ANALYTICS_WH"
SNOWFLAKE_DATABASE="FLEET_ANALYTICS_DB"

# External Volume Configuration: Choose ONE option

# OPTION A: Use an existing external volume (if you already have one configured)
USE_EXISTING_VOLUME=false
EXISTING_VOLUME_NAME=""

# OPTION B: Create a new external volume (configure provider below)
STORAGE_PROVIDER="S3"  # Options: S3, GCS, AZURE

# --- AWS S3 ---
S3_BUCKET_NAME="your-bucket-name"
S3_PATH="iceberg/fleet-analytics/"
AWS_ROLE_ARN=""  # Your IAM role ARN (see AWS S3 Setup below)

# --- Google Cloud Storage ---
GCS_BUCKET_NAME="your-bucket-name"
GCS_PATH="iceberg/fleet-analytics/"

# --- Azure Storage (Blob, ADLS Gen2, or OneLake) ---
# See: https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-azure
AZURE_TENANT_ID="your-tenant-id"
AZURE_STORAGE_ACCOUNT="your-storage-account"
AZURE_CONTAINER="your-container"
AZURE_PATH="iceberg/fleet-analytics/"
# For OneLake, set USE_ONELAKE=true and provide workspace/lakehouse GUIDs
USE_ONELAKE=false
ONELAKE_WORKSPACE_GUID=""
ONELAKE_LAKEHOUSE_GUID=""
```

### Step 3: Run Setup Script

The setup script will create all necessary Snowflake objects.

```bash
# Make the script executable
chmod +x setup.sh

# Run the setup
./setup.sh
```

**What the setup script does:**

1. Creates the database, schema, and warehouse
2. Configures the external volume (or uses your existing one)
3. Creates all Iceberg V3 tables with appropriate schemas
4. Creates Dynamic Iceberg Tables for transformation pipelines
5. Creates governance objects (masking policies, data quality functions) - *Enterprise edition only*
6. Uploads sample JSON log files to the internal stage
7. Creates the Snowflake Intelligence agent configuration

### Step 4: Import the Snowflake Notebook

Import the pre-populated notebook into Snowflake to follow along with the live demo:

1. Sign in to [Snowsight](https://app.snowflake.com)
2. In the navigation menu, select **Projects » Notebooks**
3. Click the down arrow next to **+ Notebook** and select **Import .ipynb file**
4. Navigate to the cloned repository and select `assets/fleet_analytics_notebook.ipynb`
5. In the import dialog:
   - **Notebook location**: Select `FLEET_ANALYTICS_DB` and `RAW` schema
   - **Query warehouse**: Select `FLEET_ANALYTICS_WH`
6. Click **Create** to import the notebook

> **Note**: The notebook is pre-configured with SQL and Python cells that should import with the correct cell types.

**After importing**, enable external API access for the weather data section:
1. Click **Notebook settings** (⋮ icon, top right)
2. Select **External access**
3. Toggle ON **OPEN_METEO_ACCESS**
4. Click **Save**

For more details on creating notebooks, see [Create a notebook](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-create#create-a-new-notebook).

### External Volume Setup Details

Iceberg tables require an external volume pointing to your cloud storage. If you don't already have one configured, you'll need to complete provider-specific setup before running the setup script. 

You can also create External Volumes from Snowflake's web UI by navigating to **Catalog > External data > External volumes tab**.

![Create External Volume](/assets/create_external_volume.png)

**AWS S3 Setup:**

1. Create an IAM policy granting Snowflake access to your S3 bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        }
    ]
}
```

2. Create an IAM role with this policy and update the trust relationship after running `DESCRIBE EXTERNAL VOLUME` to get the Snowflake AWS IAM user ARN.

**GCS Setup:**

1. Create a Cloud Storage service account
2. Grant `storage.objectAdmin` role on your bucket
3. After running `DESCRIBE EXTERNAL VOLUME`, grant the Snowflake service account access

**Azure Setup:**

1. Create an Azure AD application registration
2. Grant `Storage Blob Data Contributor` role on your container
3. Configure the application for Snowflake access

The setup script will provide specific instructions for your chosen provider.

### Verify Setup

After running the setup script, verify everything was created:

```sql
-- Connect to Snowflake and run:
USE DATABASE FLEET_ANALYTICS_DB;
SHOW ICEBERG TABLES;
SHOW DYNAMIC TABLES;
SHOW MASKING POLICIES;
SHOW DATA METRIC FUNCTIONS;
LIST @LOGS_STAGE;
```

You should see all the Iceberg tables, dynamic tables, and governance objects listed.

<!-- ------------------------ -->
## Streaming and Ingest

This section demonstrates various methods Snowflake supports for loading semi-structured data into Iceberg V3 tables with the VARIANT data type.

### Snowpipe Streaming: Real-Time Vehicle Telemetry

Snowpipe Streaming enables low-latency ingestion of streaming data directly into Iceberg tables. The high-performance architecture provides sub-second latency for getting data queryable in Snowflake.

#### Review the Streaming Target Table

The setup script created an Iceberg table designed to receive streaming telemetry:

```sql
USE DATABASE FLEET_ANALYTICS_DB;

-- View the table structure
DESCRIBE TABLE VEHICLE_TELEMETRY_STREAM;
```

```sql
-- Confirm the table exists but is empty
SELECT COUNT(*) FROM VEHICLE_TELEMETRY_STREAM;
-- Returns: 0

-- View the table properties showing it's an Iceberg V3 table with VARIANT column
SELECT 
    GET_DDL('TABLE', 'VEHICLE_TELEMETRY_STREAM');
```

You'll see a VARIANT column called `TELEMETRY_DATA` designed to hold the flexible schema vehicle telemetry payload.

#### Start the Streaming Simulation

Open a terminal and navigate to the cloned repository:

```bash
cd iceberg-v3-tables-comprehensive-guide/assets

# Activate the Python environment (created by setup.sh)
source iceberg_v3_demo_venv/bin/activate

# Start the streaming simulation (runs for 5 minutes max)
python stream_telemetry.py
```

> **Troubleshooting Connection Issues**: If you're on a VPN or corporate network and get connection errors, you may need a network policy to allow inbound connections. Set `ENABLE_NETWORK_POLICY=true` in `config.env` and re-run setup, or manually run `08_network_policy.sql` in Snowsight, then apply the policy to your user:
> ```sql
> ALTER USER <your_username> SET NETWORK_POLICY = FLEET_STREAMING_POLICY;
> ```

The Python script uses the Snowpipe Streaming SDK to simulate vehicle telemetry events:

```python
# Example of what the streaming script sends
{
    "vehicle_id": "VH-2847",
    "event_timestamp": "2026-02-03T14:32:15.847293847",  # Nanosecond precision
    "telemetry_data": {
        "location": {"lat": 37.7749, "lon": -122.4194},
        "speed_mph": 65.3,
        "heading": 285,
        "engine": {
            "rpm": 3200,
            "temperature_f": 195,
            "oil_pressure_psi": 42,
            "fuel_level_pct": 67.5
        },
        "diagnostics": {
            "check_engine": false,
            "tire_pressure_warning": false,
            "codes": []
        },
        "driver_behavior": {
            "hard_acceleration_count": 2,
            "hard_brake_count": 1,
            "sharp_turn_count": 0
        }
    }
}
```

#### Observe Data Flowing In

While the streaming script runs, watch data appear in Snowflake:

```sql
-- Check current count of streaming events
SELECT COUNT(*) AS event_count FROM VEHICLE_TELEMETRY_STREAM;

-- View the latest streaming events with VARIANT extraction
SELECT 
    VEHICLE_ID,
    EVENT_TIMESTAMP,
    TELEMETRY_DATA:location:lat::FLOAT AS latitude,
    TELEMETRY_DATA:location:lon::FLOAT AS longitude,
    TELEMETRY_DATA:speed_mph::FLOAT AS speed_mph,
    TELEMETRY_DATA:engine:temperature_f::INT AS engine_temp,
    TELEMETRY_DATA:engine:fuel_level_pct::FLOAT AS fuel_level
FROM VEHICLE_TELEMETRY_STREAM
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 10;
```

The streaming data is immediately queryable with full SQL capabilities on the VARIANT column!

### Pull from a Web API: Weather Data

Instead of multi-step file-based ingestion, Snowflake can connect directly to web APIs and ingest semi-structured responses into Iceberg tables with VARIANT.

#### Enable External Access in Your Notebook

Snowflake Notebooks require an **External Access Integration** to call external APIs. The setup script created an integration for the Open-Meteo weather API.

**Before running the Python cell:**

1. In your Snowflake Notebook, click the **Notebook settings** (⋮ icon, top right)
2. Select **External access**
3. Toggle ON **OPEN_METEO_ACCESS**
4. Click **Save**

> **Note**: If you don't see `OPEN_METEO_ACCESS`, run this SQL first:
> ```sql
> CREATE OR REPLACE NETWORK RULE FLEET_ANALYTICS_DB.RAW.OPEN_METEO_NETWORK_RULE
>     MODE = EGRESS TYPE = HOST_PORT VALUE_LIST = ('api.open-meteo.com:443');
> CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION OPEN_METEO_ACCESS
>     ALLOWED_NETWORK_RULES = (FLEET_ANALYTICS_DB.RAW.OPEN_METEO_NETWORK_RULE) ENABLED = TRUE;
> ```

#### View the Target Table

```sql
-- The table was created during setup
DESCRIBE TABLE API_WEATHER_DATA;

-- Confirm it's empty
SELECT COUNT(*) AS current_count FROM API_WEATHER_DATA;
```

#### Create and Run the API Ingestion Function

In your Snowflake Notebook (or worksheet), create a Python function to fetch weather data:

```python
# This is pre-populated in the Snowflake Notebook
import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, parse_json, current_timestamp
import requests

def fetch_weather_data(session: snowpark.Session, cities: list) -> str:
    """
    Fetches weather data from Open-Meteo API and loads into Iceberg table.
    Open-Meteo is a free, open-source weather API requiring no API key.
    """
    
    weather_records = []
    
    for city in cities:
        # Using Open-Meteo free API
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": city["lat"],
            "longitude": city["lon"],
            "current": "temperature_2m,wind_speed_10m,precipitation",
            "hourly": "temperature_2m,precipitation_probability"
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            weather_records.append({
                "city_name": city["name"],
                "latitude": city["lat"],
                "longitude": city["lon"],
                "api_response": response.text,
                "fetched_at": datetime.now().isoformat()
            })
    
    # Create DataFrame and write to Iceberg table
    df = session.create_dataframe(weather_records)
    df = df.with_column("WEATHER_DATA", parse_json(col("API_RESPONSE")))
    df.select(
        col("CITY_NAME"),
        col("LATITUDE"),
        col("LONGITUDE"), 
        col("WEATHER_DATA"),
        current_timestamp().alias("INGESTED_AT")
    ).write.mode("append").save_as_table("API_WEATHER_DATA")
    
    return f"Loaded weather data for {len(weather_records)} cities"

# Define cities for fleet operations
fleet_cities = [
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Seattle", "lat": 47.6062, "lon": -122.3321},
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298}
]

# Execute the function
result = fetch_weather_data(session, fleet_cities)
print(result)
```

#### Query the Weather Data

```sql
-- View the loaded weather data
SELECT 
    CITY_NAME,
    WEATHER_DATA:current:temperature_2m::FLOAT AS current_temp_c,
    WEATHER_DATA:current:wind_speed_10m::FLOAT AS wind_speed_kmh,
    WEATHER_DATA:current:precipitation::FLOAT AS precipitation_mm,
    INGESTED_AT
FROM API_WEATHER_DATA;

-- Extract hourly forecast for a city
SELECT 
    CITY_NAME,
    f.value::FLOAT AS hourly_temp
FROM API_WEATHER_DATA,
LATERAL FLATTEN(input => WEATHER_DATA:hourly:temperature_2m) f
WHERE CITY_NAME = 'San Francisco'
LIMIT 24;
```

> **Tip**: This ingestion pattern can be orchestrated natively in Snowflake using [Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro) or [Serverless Tasks](https://docs.snowflake.com/en/user-guide/tasks-serverless) for scheduled API pulls.

### Batch Ingest JSON Logs

Snowflake handles batch or continuous ingestion of semi-structured data stored in files, such as JSON diagnostic logs.

#### View the Staged Files

The setup script uploaded 10 sample JSON files mimicking maintenance diagnostic logs:

```sql
-- List the staged JSON files
LIST @LOGS_STAGE;
```

You should see files like:
- `maintenance_log_001.json`
- `maintenance_log_002.json`
- ... through `maintenance_log_010.json`

#### Load JSON Logs into Iceberg Table

```sql
-- Load JSON files into Iceberg table
COPY INTO MAINTENANCE_LOGS (LOG_ID, VEHICLE_ID, LOG_TIMESTAMP, LOG_DATA, SOURCE_FILE)
FROM (
    SELECT 
        $1:log_id::VARCHAR,
        $1:vehicle_id::VARCHAR,
        $1:log_timestamp::TIMESTAMP_NTZ,
        $1,
        METADATA$FILENAME
    FROM @LOGS_STAGE
)
FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)
PATTERN = '.*maintenance_log.*\.json';

-- View the loaded maintenance logs with VARIANT data
SELECT 
    LOG_ID,
    VEHICLE_ID,
    LOG_TIMESTAMP,
    LOG_DATA:event_type::STRING AS event_type,
    LOG_DATA:severity::STRING AS severity,
    LOG_DATA:description::STRING AS description,
    LOG_DATA:total_cost::FLOAT AS total_cost
FROM MAINTENANCE_LOGS
ORDER BY LOG_TIMESTAMP DESC
LIMIT 10;
```

<!-- ------------------------ -->
## Transformation

This section demonstrates how Snowflake powers transformation pipelines on Iceberg tables using Dynamic Tables. Dynamic Tables provide a declarative approach to data transformation—you define what the output should look like, and Snowflake handles the incremental refresh automatically.

Row lineage is used under the hood of Dynamic Iceberg V3 Tables to power change data capture (CDC) and incremental processing.

### Dynamic Iceberg Tables Overview

The setup script created several Dynamic Iceberg Tables that form a transformation pipeline:

```sql
-- View all dynamic tables in the pipeline
SHOW DYNAMIC TABLES IN DATABASE FLEET_ANALYTICS_DB;
```

These tables automatically refresh based on their TARGET_LAG setting, processing only incremental changes from source tables.

#### Explore the Pipeline in the UI

1. Navigate to **Transformation** → **Dynamic Tables** in the left pane
2. Filter by database: **FLEET_ANALYTICS_DB**
3. Click on any dynamic table (e.g., `TELEMETRY_ENRICHED`)
4. Explore the tabs:
   - **Graph**: Visualize the full pipeline and dependencies
   - **Refresh History**: See incremental refresh operations
   - **Definition**: Review the declarative SQL that defines the transformation

#### View the Dynamic Table Graph

The transformation pipeline looks like this:

![Dynamic Iceberg Table Graph](/assets/dit_graph.png)

#### Monitor Incremental Refreshes

As streaming data flows in, watch the dynamic tables refresh:

![Dynamic Iceberg Table Incremental Refresh](/assets/dit_incremental_refresh.png)

The `REFRESH_MODE = INCREMENTAL` setting ensures only new or changed data is processed, making the pipeline highly efficient.

#### Query Transformed Data

```sql
-- Query enriched telemetry with vehicle details
SELECT 
    VEHICLE_ID,
    MAKE,
    MODEL,
    DRIVER_NAME,
    FLEET_REGION,
    speed_mph,
    engine_temp_f,
    engine_health_status,
    driving_behavior,
    EVENT_TIMESTAMP
FROM CURATED.TELEMETRY_ENRICHED
WHERE engine_health_status != 'NORMAL' OR driving_behavior = 'AGGRESSIVE'
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 20;
```

### Deletion Vectors Overview



<!-- ------------------------ -->
## Security and Governance

This section highlights Horizon Catalog as the central, unified, interoperable catalog with enterprise-grade security features. All governance capabilities work seamlessly with Iceberg V3 tables.

### PII Detection with Classification

Snowflake can automatically detect and classify sensitive data across your entire database, including Iceberg tables.

#### Classify the Schema

1. Navigate to **Data** → **Databases** → **FLEET_ANALYTICS_DB** → **RAW** (the schema)
2. Click the **three dots menu** (⋮) in the top right corner
3. Select **Classify and Tag Sensitive Data**
4. Select all Iceberg tables in the schema
5. Toggle **Automatically tag data** ON
6. Click **Classify and Tag Sensitive Data**

![Classify and Tag Sensitive Data](/assets/classify_sensitive_data.png)

#### View Applied Tags

After classification completes:

1. Navigate to any table (e.g., `VEHICLE_REGISTRY`)
2. Click the **Columns** tab
3. Notice tags applied to sensitive columns like `DRIVER_NAME`, `DRIVER_EMAIL`, `DRIVER_PHONE`

![Tagged Sensitive Data](/assets/classification_tag.png)

Common tags that may be applied:
- `SEMANTIC_CATEGORY:NAME` - Personal names
- `SEMANTIC_CATEGORY:EMAIL` - Email addresses
- `SEMANTIC_CATEGORY:PHONE_NUMBER` - Phone numbers
- `SEMANTIC_CATEGORY:US_SSN` - Social Security Numbers

> **Tip**: You can also create [custom tags that automatically propagate](https://docs.snowflake.com/en/user-guide/object-tagging/work#define-a-tag-that-will-automatically-propagate) to existing and new downstream objects.

### Fine-Grained Access Control with Masking Policies

The setup script created masking policies to protect sensitive information. Now apply them to your Iceberg tables.

#### View Created Masking Policies

```sql
-- View all masking policies in the database
SHOW MASKING POLICIES IN DATABASE FLEET_ANALYTICS_DB;
```

The `PII_MASK` policy was created:

```sql
-- View the policy definition
SELECT GET_DDL('MASKING_POLICY', 'PII_MASK');
```

```sql
CREATE OR REPLACE MASKING POLICY PII_MASK AS (val STRING) 
RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('FLEET_ADMIN', 'ACCOUNTADMIN') THEN val
        WHEN CURRENT_ROLE() = 'FLEET_ANALYST' THEN 
            CONCAT(LEFT(val, 2), '****', RIGHT(val, 2))
        ELSE '********'
    END;
```

#### Apply Masking Policies via UI

1. Navigate to **Data** → **Databases** → **FLEET_ANALYTICS_DB** → **RAW** → **VEHICLE_REGISTRY**
2. Click the **Columns** tab
3. Find the `DRIVER_NAME` column
4. In the **Policies** column, click the **+** button
5. Select `PII_NAME_MASK` and click **Done**
6. Repeat for `DRIVER_EMAIL` and `DRIVER_PHONE` with `PII_EMAIL_MASK` and `PII_PHONE_MASK`

![Mask Tagged Columns](/assets/tag_mask.png)

#### Test Masking Behavior

```sql
-- As ACCOUNTADMIN, see full PII values (unmasked)
SELECT VEHICLE_ID, DRIVER_NAME, DRIVER_EMAIL, DRIVER_PHONE
FROM VEHICLE_REGISTRY LIMIT 5;

-- Create a test analyst role and grant it to the current user
CREATE ROLE IF NOT EXISTS FLEET_ANALYST;
GRANT USAGE ON DATABASE FLEET_ANALYTICS_DB TO ROLE FLEET_ANALYST;
GRANT USAGE ON SCHEMA FLEET_ANALYTICS_DB.RAW TO ROLE FLEET_ANALYST;
GRANT SELECT ON ALL TABLES IN SCHEMA FLEET_ANALYTICS_DB.RAW TO ROLE FLEET_ANALYST;
GRANT USAGE ON WAREHOUSE FLEET_ANALYTICS_WH TO ROLE FLEET_ANALYST;

-- Grant the role to the current user so we can switch to it
SET MY_USER = CURRENT_USER();
GRANT ROLE FLEET_ANALYST TO USER IDENTIFIER($MY_USER);

-- Switch to analyst role and observe MASKED values
USE ROLE FLEET_ANALYST;
SELECT VEHICLE_ID, DRIVER_NAME, DRIVER_EMAIL, DRIVER_PHONE
FROM VEHICLE_REGISTRY LIMIT 5;
-- Results show masked values: "Jo****hn", "jo****om"

-- Switch back to ACCOUNTADMIN for remaining operations
USE ROLE ACCOUNTADMIN;
```

### Data Quality Monitoring

The setup script created Data Metric Functions (DMFs) to monitor data quality on Iceberg tables.

#### View Data Quality Setup

```sql
-- Show data metric functions
SHOW DATA METRIC FUNCTIONS IN DATABASE FLEET_ANALYTICS_DB;
```

Example DMF for validating geospatial coordinates:

```sql
CREATE OR REPLACE DATA METRIC FUNCTION CHECK_VALID_COORDINATES(
    arg_t TABLE(lat FLOAT, lon FLOAT)
)
RETURNS NUMBER
AS
$$
    SELECT COUNT(*) 
    FROM arg_t
    WHERE lat < -90 OR lat > 90 
       OR lon < -180 OR lon > 180
$$;
```

#### Review Data Quality Results

> **Note**: The Data Quality dashboard will initially be empty. DMFs run on a schedule (default: when triggered by Snowflake). To see results sooner, set a shorter schedule and insert new data to trigger the DMF.

To configure DMF scheduling and verify results:

```sql
-- Set DMFs to trigger when data changes
ALTER ICEBERG TABLE RAW.VEHICLE_LOCATIONS SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';
ALTER ICEBERG TABLE RAW.SENSOR_READINGS SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';

-- Or set a specific schedule (e.g., every 5 minutes)
-- ALTER ICEBERG TABLE RAW.VEHICLE_LOCATIONS SET DATA_METRIC_SCHEDULE = '5 MINUTE';

-- Check which DMFs are attached to VEHICLE_LOCATIONS
SELECT * FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
    REF_ENTITY_NAME => 'FLEET_ANALYTICS_DB.RAW.VEHICLE_LOCATIONS',
    REF_ENTITY_DOMAIN => 'TABLE'
));

-- Insert a row to trigger the DMF (if using TRIGGER_ON_CHANGES)
INSERT INTO RAW.VEHICLE_LOCATIONS (LOCATION_ID, VEHICLE_ID, LOCATION_TIMESTAMP, LATITUDE, LONGITUDE, LOCATION_POINT, SPEED_MPH, HEADING_DEGREES, FLEET_REGION)
SELECT UUID_STRING(), VEHICLE_ID, CURRENT_TIMESTAMP(), LATITUDE, LONGITUDE, LOCATION_POINT, SPEED_MPH, HEADING_DEGREES, FLEET_REGION
FROM RAW.VEHICLE_LOCATIONS LIMIT 1;

-- Check DMF results (may take a minute to populate after data insert)
SELECT 
    TABLE_NAME,
    METRIC_NAME,
    VALUE,
    MEASUREMENT_TIME
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
WHERE TABLE_DATABASE = 'FLEET_ANALYTICS_DB'
ORDER BY MEASUREMENT_TIME DESC
LIMIT 20;
```

> **Tip**: Insert or modify data in the table to trigger the DMF if using `TRIGGER_ON_CHANGES`. The Data Quality tab will populate after the next scheduled run.

To view the Data Quality dashboard:

1. Navigate to **Data** → **Databases** → **FLEET_ANALYTICS_DB** → **RAW** → **VEHICLE_LOCATIONS**
2. Click on the **Data Quality** tab
3. After DMFs have run, you'll see:
   - Quality check results over time
   - Failed record counts  
   - Data quality trends by dimension (Freshness, Volume, Accuracy, etc.)

For more details, see [Getting Started with Data Quality in Snowflake](https://www.snowflake.com/en/developers/guides/getting-started-with-data-quality-in-snowflake/#review).

### Data Lineage

Snowflake automatically tracks lineage for all objects, including Iceberg tables and Dynamic Tables.

#### View Lineage Graph

1. Navigate to **Data** → **Databases** → **FLEET_ANALYTICS_DB** → **RAW** → **MAINTENANCE_LOGS**
2. Click on the **Lineage** tab
3. Explore the lineage graph showing both upstream and downstream tables, including upstream lineage from an external telemetry messaging service

The lineage graph is valuable for:
- **Impact analysis**: Understanding what's affected when source data changes
- **Data quality investigation**: Tracing issues back to their source
- **Security auditing**: Understanding data flow for sensitive information

![Data Lineage](/assets/lineage.png)

<!-- ------------------------ -->
## Analytics and AI

This section demonstrates Snowflake's analytical capabilities on Iceberg V3 tables, including semi-structured data querying, time-series analysis, geospatial functions, and AI agents.

### Semi-Structured Data Analytics

Snowflake efficiently queries VARIANT data in Iceberg tables with automatic pruning and optimization.

#### Query Nested Variant Data

```sql
-- Extract nested fields from VARIANT with dot notation
SELECT 
    VEHICLE_ID,
    TELEMETRY_DATA:speed_mph::FLOAT AS speed,
    TELEMETRY_DATA:engine:rpm::INT AS engine_rpm,
    TELEMETRY_DATA:engine:temperature_f::INT AS engine_temp,
    TELEMETRY_DATA:diagnostics:check_engine::BOOLEAN AS check_engine_light,
    TELEMETRY_DATA:driver_behavior:hard_brake_count::INT AS hard_brakes
FROM RAW.VEHICLE_TELEMETRY_STREAM
WHERE TELEMETRY_DATA:speed_mph::FLOAT > 50
LIMIT 20;

-- Aggregate on variant fields - find vehicles with check engine warnings
SELECT 
    TELEMETRY_DATA:diagnostics:check_engine::BOOLEAN AS check_engine,
    COUNT(*) AS event_count,
    ROUND(AVG(TELEMETRY_DATA:speed_mph::FLOAT), 1) AS avg_speed,
    COUNT(DISTINCT VEHICLE_ID) AS vehicle_count
FROM RAW.VEHICLE_TELEMETRY_STREAM
GROUP BY 1
ORDER BY event_count DESC;
```

#### Observe Query Pruning

```sql
-- Run with profile to see pruning efficiency
SELECT 
    VEHICLE_ID,
    EVENT_TIMESTAMP,
    TELEMETRY_DATA:speed_mph::FLOAT AS speed
FROM VEHICLE_TELEMETRY_STREAM
WHERE VEHICLE_ID = 'VH-1234'
  AND TELEMETRY_DATA:engine:temperature_f::INT > 200;

-- Check query profile in History tab to see partition pruning statistics
```

### Time-Series Analytics and Forecasting

The `SENSOR_READINGS` table contains high-precision time-series data for analysis.

#### AS OF Join for Point-in-Time Analysis

```sql
-- AS OF join: Find closest sensor reading before each maintenance event
SELECT 
    m.VEHICLE_ID,
    m.LOG_TIMESTAMP AS maintenance_time,
    m.LOG_DATA:event_type::STRING AS maintenance_type,
    s.READING_TIMESTAMP AS closest_reading_time,
    s.ENGINE_TEMP_F,
    s.OIL_PRESSURE_PSI
FROM RAW.MAINTENANCE_LOGS m
ASOF JOIN RAW.SENSOR_READINGS s
    MATCH_CONDITION (m.LOG_TIMESTAMP >= s.READING_TIMESTAMP)
    ON m.VEHICLE_ID = s.VEHICLE_ID
WHERE m.LOG_DATA:severity::STRING IN ('CRITICAL', 'HIGH')
ORDER BY m.LOG_TIMESTAMP DESC
LIMIT 15;
```

#### Time-Series Aggregation with 

Window functions enable powerful time-series analysis directly in SQL:
- **Rolling averages** to smooth out noise
- **Running totals** for cumulative metrics
- **Lag/Lead** for period-over-period comparisons

```sql
-- Calculate rolling averages for engine temperature
SELECT 
    VEHICLE_ID,
    READING_TIMESTAMP,
    ENGINE_TEMP_F,
    AVG(ENGINE_TEMP_F) OVER (
        PARTITION BY VEHICLE_ID 
        ORDER BY READING_TIMESTAMP 
        RANGE BETWEEN INTERVAL '1 HOUR' PRECEDING AND CURRENT ROW
    ) AS rolling_avg_temp,
    MAX(ENGINE_TEMP_F) OVER (
        PARTITION BY VEHICLE_ID 
        ORDER BY READING_TIMESTAMP 
        RANGE BETWEEN INTERVAL '1 HOUR' PRECEDING AND CURRENT ROW
    ) AS rolling_max_temp
FROM RAW.SENSOR_READINGS
ORDER BY VEHICLE_ID, READING_TIMESTAMP
LIMIT 50;
```

#### ML Forecasting for Predictive Maintenance

> ⏱️ **Training Time**: Model training may take **2-5 minutes** depending on data volume and warehouse size. To speed up training:
> - Use a **larger warehouse** (e.g., MEDIUM or LARGE) - training scales with compute
> - Reduce the number of time series by filtering to specific vehicles  
> - Limit historical data range (e.g., 14 days instead of 30)

```sql
-- Create a forecast model for fuel consumption
-- For Iceberg tables, we must use SYSTEM$QUERY_REFERENCE instead of TABLE reference
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST fuel_consumption_forecast(
    INPUT_DATA => SYSTEM$QUERY_REFERENCE('
        SELECT 
            VEHICLE_ID,
            READING_TIMESTAMP,
            FUEL_CONSUMPTION_GPH
        FROM RAW.SENSOR_READINGS
        WHERE READING_TIMESTAMP > DATEADD(''day'', -30, CURRENT_TIMESTAMP())
    '),
    TIMESTAMP_COLNAME => 'READING_TIMESTAMP',
    TARGET_COLNAME => 'FUEL_CONSUMPTION_GPH',
    SERIES_COLNAME => 'VEHICLE_ID'
);

-- Generate 7-day forecast and save results
CALL fuel_consumption_forecast!FORECAST(
    FORECASTING_PERIODS => 168,  -- 7 days * 24 hours
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

-- FORECAST: Generate a 7-day forecast (168 hours) and save to a table for visualization
CALL fuel_consumption_forecast!FORECAST(
    FORECASTING_PERIODS => 168,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
);

-- Save forecast results to a table for visualization
CREATE OR REPLACE TEMPORARY TABLE FUEL_FORECAST_RESULTS AS
SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

-- Preview forecast results
SELECT * FROM FUEL_FORECAST_RESULTS ORDER BY SERIES, TS LIMIT 20;
```

#### Visualize Historical + Forecast Data

Use Streamlit in a Snowflake Notebook to plot historical data alongside the forecast:

```python
# 📈 Visualize Historical + Forecast Fuel Consumption
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

session = get_active_session()

# Get historical data (last 30 days for one vehicle)
historical_df = session.sql("""
    SELECT 
        READING_TIMESTAMP AS ts,
        FUEL_CONSUMPTION_GPH AS value,
        'Historical' AS data_type
    FROM RAW.SENSOR_READINGS
    WHERE VEHICLE_ID = (SELECT SERIES FROM FUEL_FORECAST_RESULTS LIMIT 1)
      AND READING_TIMESTAMP > DATEADD('day', -30, CURRENT_TIMESTAMP())
    ORDER BY READING_TIMESTAMP
""").to_pandas()

# Get forecast data (column names vary - check with DESCRIBE first if needed)
forecast_df = session.sql("""
    SELECT 
        TS AS ts,
        FORECAST AS value,
        'Forecast' AS data_type
    FROM FUEL_FORECAST_RESULTS
    WHERE SERIES = (SELECT SERIES FROM FUEL_FORECAST_RESULTS LIMIT 1)
    ORDER BY TS
""").to_pandas()

# Get the vehicle ID for the title
vehicle_id = session.sql("SELECT SERIES FROM FUEL_FORECAST_RESULTS LIMIT 1").collect()[0][0]

st.subheader(f"📈 Fuel Consumption Forecast: {vehicle_id}")
st.caption("Historical data (30 days) + 7-day forecast")

# Normalize column names to lowercase
historical_df.columns = historical_df.columns.str.lower()
forecast_df.columns = forecast_df.columns.str.lower()

# Combine for plotting
combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)
combined_df['ts'] = pd.to_datetime(combined_df['ts'])
combined_df = combined_df.sort_values('ts')

# Create the chart using Streamlit's native line chart
# Pivot data for multi-line chart
chart_data = combined_df.pivot_table(index='ts', columns='data_type', values='value', aggfunc='first')
st.line_chart(chart_data, use_container_width=True)

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Avg Historical (GPH)", f"{historical_df['value'].mean():.2f}")
col2.metric("Avg Forecast (GPH)", f"{forecast_df['value'].mean():.2f}")
change = ((forecast_df['value'].mean() - historical_df['value'].mean()) / historical_df['value'].mean()) * 100
col3.metric("Projected Change", f"{change:+.1f}%")

st.caption("💡 The forecast helps identify vehicles likely to have higher fuel consumption, enabling proactive maintenance scheduling.")
```

### Geospatial Analytics

H3 is Uber's hierarchical geospatial indexing system. Snowflake's H3 functions enable:
- Aggregating vehicles by geographic cell
- Efficient spatial joins and clustering
- Multi-resolution analysis (cells at different zoom levels)

The `VEHICLE_LOCATIONS` table contains GEOGRAPHY data for spatial analysis.

#### Basic Geospatial Queries

```sql
-- Calculate distance between consecutive positions
SELECT 
    VEHICLE_ID,
    LOCATION_TIMESTAMP,
    LAG(LOCATION_POINT) OVER (
        PARTITION BY VEHICLE_ID ORDER BY LOCATION_TIMESTAMP
    ) AS prev_location,
    LOCATION_POINT AS current_location,
    ST_DISTANCE(
        LOCATION_POINT,
        LAG(LOCATION_POINT) OVER (PARTITION BY VEHICLE_ID ORDER BY LOCATION_TIMESTAMP)
    ) / 1609.34 AS distance_miles  -- Convert meters to miles
FROM VEHICLE_LOCATIONS
ORDER BY VEHICLE_ID, LOCATION_TIMESTAMP
LIMIT 50;
```

#### Geofencing Analysis

```sql
-- Define a geofence (San Francisco downtown)
SET sf_downtown = ST_MAKEPOLYGON(TO_GEOGRAPHY(
    'LINESTRING(-122.42 37.78, -122.42 37.79, -122.40 37.79, -122.40 37.78, -122.42 37.78)'
));

-- Find vehicles inside the geofence
SELECT 
    VEHICLE_ID,
    LOCATION_TIMESTAMP,
    ST_X(LOCATION_POINT) AS longitude,
    ST_Y(LOCATION_POINT) AS latitude
FROM VEHICLE_LOCATIONS
WHERE ST_WITHIN(LOCATION_POINT, $sf_downtown)
ORDER BY LOCATION_TIMESTAMP DESC
LIMIT 20;

-- Geospatial: Aggregate vehicles by H3 cell (resolution 6)
SELECT 
    H3_POINT_TO_CELL_STRING(LOCATION_POINT, 6) AS h3_cell,
    FLEET_REGION,
    COUNT(DISTINCT VEHICLE_ID) AS vehicle_count,
    ROUND(AVG(SPEED_MPH), 1) AS avg_speed
FROM RAW.VEHICLE_LOCATIONS
WHERE LOCATION_TIMESTAMP > DATEADD('hour', -24, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY vehicle_count DESC
LIMIT 20;
```

#### Interactive Map Visualization with Streamlit

In the Snowflake Notebook, you can visualize the H3 geospatial data on an interactive map using Streamlit (built into Snowflake Notebooks):

```python
# Visualize fleet locations on an interactive map using Streamlit
import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

# Query location data with H3 cell centers (use ST_X/ST_Y for GEOGRAPHY type)
df = session.sql("""
    SELECT 
        H3_POINT_TO_CELL_STRING(LOCATION_POINT, 6) AS h3_cell,
        ST_X(H3_CELL_TO_POINT(H3_POINT_TO_CELL_STRING(LOCATION_POINT, 6))) AS longitude,
        ST_Y(H3_CELL_TO_POINT(H3_POINT_TO_CELL_STRING(LOCATION_POINT, 6))) AS latitude,
        FLEET_REGION,
        COUNT(DISTINCT VEHICLE_ID) AS vehicle_count,
        ROUND(AVG(SPEED_MPH), 1) AS avg_speed
    FROM RAW.VEHICLE_LOCATIONS
    WHERE LOCATION_TIMESTAMP > DATEADD('hour', -24, CURRENT_TIMESTAMP())
    GROUP BY 1, 2, 3, 4
    ORDER BY vehicle_count DESC
    LIMIT 100
""").to_pandas()

st.subheader("🗺️ Fleet Vehicle Distribution")
st.caption("Each point represents an H3 cell with vehicle activity in the last 24 hours")

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total H3 Cells", len(df))
col2.metric("Total Vehicles", int(df['VEHICLE_COUNT'].sum()))
col3.metric("Avg Speed", f"{df['AVG_SPEED'].mean():.1f} mph")

# Interactive map visualization - point size scales with vehicle count
st.map(df, latitude='LATITUDE', longitude='LONGITUDE', size='VEHICLE_COUNT')

# Show data table
st.dataframe(df[['FLEET_REGION', 'VEHICLE_COUNT', 'AVG_SPEED']].head(10))
```

This produces an interactive map showing vehicle distribution across the US, with:
- Points sized by vehicle count per H3 cell
- Summary metrics for cells, vehicles, and average speed
- Data table with regional breakdown

### AI Agents with Snowflake Intelligence

The setup script creates a Cortex Agent (`FLEET_ANALYTICS_AGENT`) that enables natural language querying of your fleet data.

> **Note**: Cortex Agents require Enterprise Edition or higher.

#### Region Availability and Cross-Region Inference

Cortex Agents and Cortex Analyst rely on LLMs that may not be available in all Snowflake regions. If you see an error like:

```
None of the preferred models are authorized or available in your region...
```

You have two options:

1. **Enable Cross-Region Inference** (recommended): This allows Snowflake to route AI requests to regions where models are available, while keeping your data secure.

```sql
-- Enable cross-region inference for your account
USE ROLE ACCOUNTADMIN;
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

2. **Use a supported region**: Deploy your Snowflake account in a region with native LLM support.

For more details, see:
- [Cortex Analyst Region Availability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst#region-availability)
- [Cross-Region Inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference)

> **Privacy Note**: With cross-region inference, only the AI inference is routed cross-region. Your underlying data remains in your account's region and is protected by Snowflake's governance controls.

#### Agent Configuration

The setup script creates the agent with a complete YAML specification including:
- **Sample questions** to help users get started
- **Orchestration instructions** explaining the data schema
- **Cortex Analyst tool** linked to a semantic model describing all tables

The semantic model (`fleet_semantic_model.yaml`) is uploaded to the stage and defines:
- Table structures for SENSOR_READINGS, VEHICLE_TELEMETRY_STREAM, VEHICLE_LOCATIONS, etc.
- VARIANT column extraction patterns
- Dimension and measure definitions

> **Note**: If the agent creation fails due to syntax issues, you can configure it manually through **Cortex AI** → **Agents** → **FLEET_ANALYTICS_AGENT**.

#### Using the Fleet Analytics Agent

1. Navigate to **Cortex AI** → **Agents** in the left sidebar
2. Select **FLEET_ANALYTICS_AGENT**
3. Start asking questions in natural language:

**Example queries:**

- "Which vehicles had the highest fuel consumption last week?"
- "Show me all critical maintenance events"
- "What's the average speed by fleet region?"
- "Find vehicles with check engine warnings"
- "Which drivers have the most hard braking events?"
- "Show vehicle health scores below 60"
- "How many vehicles are in each H3 cell in California?"

The agent understands your Iceberg table schema including:
- **VARIANT columns**: Extracts nested JSON fields using colon notation
- **GEOGRAPHY columns**: Uses H3 and ST_* functions for geospatial analysis
- **Time-series data**: Performs ASOF joins and window functions

#### Agent Configuration

The agent was created with access to these tables:

| Table | Description |
|-------|-------------|
| `RAW.VEHICLE_TELEMETRY_STREAM` | Real-time streaming telemetry (VARIANT) |
| `RAW.VEHICLE_LOCATIONS` | Geospatial positions (GEOGRAPHY) |
| `RAW.SENSOR_READINGS` | High-precision time-series sensor data |
| `RAW.MAINTENANCE_LOGS` | Maintenance events (VARIANT) |
| `RAW.VEHICLE_REGISTRY` | Vehicle and driver master data |
| `ANALYTICS.DAILY_FLEET_SUMMARY` | Daily aggregated metrics |
| `ANALYTICS.VEHICLE_HEALTH_SCORE` | Calculated health scores |

To view or modify the agent configuration:

```sql
-- View agent details
SHOW AGENTS IN SCHEMA FLEET_ANALYTICS_DB.RAW;

-- Describe the agent
DESCRIBE AGENT FLEET_ANALYTICS_DB.RAW.FLEET_ANALYTICS_AGENT;
```

For more on building agents, see [Snowflake Intelligence documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence).

<!-- ------------------------ -->
## Business Continuity and Disaster Recovery

This section highlights Snowflake's enterprise-grade, out-of-the-box business continuity and disaster recovery capabilities that extend to Iceberg V3 tables.

> **Note**: Replication features require Business Critical Edition or higher.

### Iceberg Table Replication Overview

Snowflake supports replicating Iceberg tables across regions and clouds, ensuring your data lakehouse is protected against regional outages. See [Iceberg Table Replication documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg-replication) for details.

### Setting Up Replication via UI

Follow these steps to set up cross-region replication for your Iceberg tables:

#### Step 1: Create a Replication Group

1. Navigate to **Admin** → **Accounts**
2. Click on the **Replication** tab
3. Click **+ Group** (or **+ Failover Group** for automatic failover)

#### Step 2: Select Target Account

1. Choose the target Snowflake account in a different cloud or region
2. If no secondary accounts exist, you'll need to create one first

#### Step 3: Configure Objects

1. Select all objects to replicate:
   - Databases (includes all Iceberg tables)
   - Warehouses (optional)
   - Roles and privileges (recommended for consistent access)

#### Step 4: Enable and Monitor

1. Click **Create** to enable replication
2. Monitor replication status in the Replication tab
3. View replication lag and sync history

### Verify Replication

In the secondary account:

```sql
-- Check that Iceberg tables exist
USE DATABASE FLEET_ANALYTICS_DB;
SHOW ICEBERG TABLES;

-- Query replicated data
SELECT COUNT(*) FROM VEHICLE_TELEMETRY_STREAM;
SELECT COUNT(*) FROM MAINTENANCE_LOGS;
```

### Failover Testing

For Failover Groups (automatic failover):

1. In the Replication tab, select your failover group
2. Click **Failover** to initiate failover to secondary
3. Verify applications can connect to secondary account
4. Use **Failback** when primary is restored

For detailed steps, see [Creating Replication/Failover Groups via Snowsight](https://docs.snowflake.com/en/user-guide/account-replication-config#create-a-replication-or-failover-group-using-snowsight).

<!-- ------------------------ -->
## Interoperability

This section demonstrates that external engines like Apache Spark can access Iceberg V3 tables managed by Snowflake. Horizon provides temporary, scoped storage credentials and enforces centralized row/column-level access controls for any engine.

### Prerequisites for Spark

Ensure you have:
- Conda installed
- The repository cloned (`sfguide-iceberg-v3-comprehensive-guide`)

### Start the Spark Environment

The setup script created a Conda environment with Spark 4.0+ and all necessary dependencies:

```bash
cd sfguide-iceberg-v3-comprehensive-guide/assets

# Activate the Spark environment
conda activate fleet-spark

# Start Jupyter notebook
jupyter notebook spark_iceberg_interop.ipynb
```

### Spark Notebook Walkthrough

The pre-configured Jupyter notebook contains all the code needed. Here's what you'll do:

#### Cell 1: Setup and Imports

```python
from pyspark.sql import SparkSession
import os

# Load configuration (from the same config.env used during setup)
from dotenv import load_dotenv
load_dotenv('../config.env')

SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
```

#### Cell 2: Create Spark Session with Horizon Catalog

```python
from pyspark.sql import SparkSession

# Configuration
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_ROLE = 'ACCOUNTADMIN'
SNOWFLAKE_SCHEMA = 'RAW'
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'FLEET_ANALYTICS_WH')
SF_URL = f"{SNOWFLAKE_ACCOUNT_URL}.snowflakecomputing.com"

# Versions - Note: Spark 3.5 required for Snowflake Connector masking support
SNOWFLAKE_JDBC_VERSION = "3.24.0"
SNOWFLAKE_SPARK_CONNECTOR_VERSION = "3.1.6"

# Create Spark session with Iceberg and Snowflake catalog configuration
# Note: 
# - driver.host and bindAddress ensure Spark uses localhost (avoids VPN issues)
# - Using Spark 4.0 + Iceberg 1.10.1 for native VARIANT support
spark = SparkSession.builder \
    .appName("Fleet Analytics - Iceberg V3 Interop") \
    .master("local[*]") \
    .config("spark.driver.host", "127.0.0.1") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .config("spark.jars.packages", 
            f"org.apache.iceberg:iceberg-spark-runtime-4.0_{SCALA_VERSION}:{ICEBERG_VERSION},"
            f"org.apache.iceberg:iceberg-aws-bundle:{ICEBERG_VERSION},"
            f"net.snowflake:snowflake-jdbc:{SNOWFLAKE_JDBC_VERSION},"
            f"net.snowflake:spark-snowflake_{SCALA_VERSION}:{SNOWFLAKE_SPARK_CONNECTOR_VERSION}") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.horizon", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.horizon.type", "rest") \
    .config("spark.sql.catalog.horizon.uri", f"https://{SNOWFLAKE_ACCOUNT_URL}.snowflakecomputing.com/polaris/api/catalog") \
    .config("spark.sql.catalog.horizon.credential", SNOWFLAKE_ACCOUNTADMIN_TOKEN) \
    .config("spark.sql.catalog.horizon.warehouse", SNOWFLAKE_DATABASE) \
    .config("spark.sql.catalog.horizon.scope", f"session:role:{SNOWFLAKE_ROLE}") \
    .config("spark.sql.catalog.horizon.header.X-Iceberg-Access-Delegation","vended-credentials") \
    .config("spark.snowflake.sfURL", SF_URL) \
    .config("spark.snowflake.sfUser", os.getenv('SNOWFLAKE_USER')) \
    .config("spark.snowflake.sfPassword", SNOWFLAKE_FLEET_ANALYST_TOKEN) \
    .config("spark.snowflake.sfDatabase", SNOWFLAKE_DATABASE) \
    .config("spark.snowflake.sfSchema", SNOWFLAKE_SCHEMA) \
    .config("spark.snowflake.sfRole", SNOWFLAKE_ROLE) \
    .config("spark.snowflake.sfWarehouse", SNOWFLAKE_WAREHOUSE) \
    .config("spark.sql.iceberg.vectorization.enabled", "false") \
    .getOrCreate()

print("Spark session created successfully!")
print(f"Spark version: {spark.version}")
```

#### Cell 3: List Available Tables

```python
# Show all tables visible to Spark
spark.sql("SHOW TABLES IN horizon.RAW").show(truncate=False)
spark.sql("SHOW TABLES IN horizon.CURATED").show(truncate=False)
spark.sql("SHOW TABLES IN horizon.ANALYTICS").show(truncate=False)
```

Output:
```
+---------+------------------------+-----------+
|namespace|tableName               |isTemporary|
+---------+------------------------+-----------+
|RAW      |API_WEATHER_DATA        |false      |
|RAW      |MAINTENANCE_LOGS        |false      |
|RAW      |SENSOR_READINGS         |false      |
|RAW      |VEHICLE_LOCATIONS       |false      |
|RAW      |VEHICLE_REGISTRY        |false      |
|RAW      |VEHICLE_TELEMETRY_STREAM|false      |
+---------+------------------------+-----------+

+---------+--------------------+-----------+
|namespace|tableName           |isTemporary|
+---------+--------------------+-----------+
|CURATED  |MAINTENANCE_ANALYSIS|false      |
|CURATED  |TELEMETRY_ENRICHED  |false      |
+---------+--------------------+-----------+

+---------+--------------------+-----------+
|namespace|tableName           |isTemporary|
+---------+--------------------+-----------+
|ANALYTICS|DAILY_FLEET_SUMMARY |false      |
|ANALYTICS|VEHICLE_HEALTH_SCORE|false      |
+---------+--------------------+-----------+
```

Note that Dynamic Iceberg Tables are also visible!

#### Cell 4: Describe Table with Variant Column

```python
# See variant column in Iceberg table
spark.sql("DESCRIBE TABLE snowflake.RAW.VEHICLE_TELEMETRY_STREAM").show(truncate=False)
```

Output:
```
+-------------------+---------------+-------+
|col_name           |data_type      |comment|
+-------------------+---------------+-------+
|VEHICLE_ID         |string         |null   |
|EVENT_TIMESTAMP    |timestamp      |null   |
|TELEMETRY_DATA     |variant        |null   |
+-------------------+---------------+-------+
```

#### Cell 5: Query Data with Variant

```python
# Use Spark's variant_get() function to extract nested fields from VARIANT
# This query succeeds, and no Snowflake compute is used, since there's no masking policy on the Iceberg table.
df = spark.sql(f"""
    SELECT 
        VEHICLE_ID,
        EVENT_TIMESTAMP,
        variant_get(TELEMETRY_DATA, '$.speed_mph', 'float') AS speed_mph,
        variant_get(TELEMETRY_DATA, '$.engine.temperature_f', 'int') AS engine_temp,
        variant_get(TELEMETRY_DATA, '$.location.lat', 'float') AS latitude,
        variant_get(TELEMETRY_DATA, '$.location.lon', 'float') AS longitude
    FROM snowflake.RAW.VEHICLE_TELEMETRY_STREAM
    WHERE variant_get(TELEMETRY_DATA, '$.speed_mph', 'float') > 60
    LIMIT 10
""")
df.show()
```

#### Cell 6: Demonstrate Access Control (Masking Enforcement)

```python
# To enforce masking policies from Spark, we need the Snowflake Connector for Spark
# which routes queries through Snowflake for policy evaluation
# See: https://docs.snowflake.com/en/user-guide/tables-iceberg-query-using-external-query-engine-snowflake-horizon-enforce-access-policies

# Stop the previous Spark session first
spark.stop()
from pyspark.sql import SparkSession

# Configuration
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_ROLE = 'FLEET_ANALYST'
SNOWFLAKE_SCHEMA = 'RAW'
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'FLEET_ANALYTICS_WH')
SF_URL = f"{SNOWFLAKE_ACCOUNT_URL}.snowflakecomputing.com"

# Versions - Note: Spark 3.5 required for Snowflake Connector masking support
SNOWFLAKE_JDBC_VERSION = "3.24.0"
SNOWFLAKE_SPARK_CONNECTOR_VERSION = "3.1.6"

spark_analyst = SparkSession.builder \
    .appName("Fleet Analytics - Analyst View") \
    .master("local[*]") \
    .config("spark.driver.host", "127.0.0.1") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .config("spark.jars.packages", 
            f"org.apache.iceberg:iceberg-spark-runtime-4.0_{SCALA_VERSION}:{ICEBERG_VERSION},"
            f"org.apache.iceberg:iceberg-aws-bundle:{ICEBERG_VERSION},"
            f"net.snowflake:snowflake-jdbc:{SNOWFLAKE_JDBC_VERSION},"
            f"net.snowflake:spark-snowflake_{SCALA_VERSION}:{SNOWFLAKE_SPARK_CONNECTOR_VERSION}") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.defaultCatalog", "horizon") \
    .config("spark.sql.catalog.horizon", "org.apache.spark.sql.snowflake.catalog.SnowflakeFallbackCatalog") \
    .config("spark.sql.catalog.horizon.catalog-impl", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.horizon.type", "rest") \
    .config("spark.sql.catalog.horizon.uri", f"https://{SNOWFLAKE_ACCOUNT_URL}.snowflakecomputing.com/polaris/api/catalog") \
    .config("spark.sql.catalog.horizon.warehouse", SNOWFLAKE_DATABASE) \
    .config("spark.sql.catalog.horizon.scope", f"session:role:{SNOWFLAKE_ROLE}") \
    .config("spark.sql.catalog.horizon.credential", SNOWFLAKE_FLEET_ANALYST_TOKEN) \
    .config("spark.sql.catalog.horizon.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
    .config("spark.sql.catalog.horizon.header.X-Iceberg-Access-Delegation", "vended-credentials") \
    .config("spark.snowflake.sfURL", SF_URL) \
    .config("spark.snowflake.sfUser", os.getenv('SNOWFLAKE_USER')) \
    .config("spark.snowflake.sfPassword", SNOWFLAKE_FLEET_ANALYST_TOKEN) \
    .config("spark.snowflake.sfDatabase", SNOWFLAKE_DATABASE) \
    .config("spark.snowflake.sfSchema", SNOWFLAKE_SCHEMA) \
    .config("spark.snowflake.sfRole", SNOWFLAKE_ROLE) \
    .config("spark.snowflake.sfWarehouse", SNOWFLAKE_WAREHOUSE) \
    .config("spark.sql.iceberg.vectorization.enabled", "false") \
    .getOrCreate()

spark_analyst.sparkContext.setLogLevel("ERROR")
```

Iceberg tables are still accessible via Iceberg REST API
```python
spark_analyst.sql("SHOW TABLES in horizon.RAW").show(truncate=False)
```

When reading an Iceberg table with a maskign policy, Snowflake returns masked results
```python
spark_analyst.sql("""
    SELECT
        VEHICLE_ID,
        MAKE,
        MODEL,
        YEAR,
        LICENSE_PLATE,
        DRIVER_NAME,
        DRIVER_EMAIL,
        DRIVER_PHONE,
        FLEET_REGION
    FROM horizon.RAW.VEHICLE_REGISTRY
""").show(truncate=True)
```

![Interoperable Masking](/assets/spark_masked.png)


The masking policies defined in Snowflake are enforced even when accessing data through Spark!

For more details on Spark integration, see:
- [Query Iceberg Tables Using External Engines](https://docs.snowflake.com/en/user-guide/tables-iceberg-query-using-external-query-engine-snowflake-horizon)
- [Enforce Access Policies for External Engines](https://docs.snowflake.com/en/user-guide/tables-iceberg-query-using-external-query-engine-snowflake-horizon-enforce-access-policies)

<!-- ------------------------ -->
## Cleanup

To remove all objects created by this guide:

```sql
USE ROLE ACCOUNTADMIN;

-- Drop the database (this removes all tables, schemas, and objects)
DROP DATABASE IF EXISTS FLEET_ANALYTICS_DB;

-- Drop the external volume (if you created one)
DROP EXTERNAL VOLUME IF EXISTS FLEET_ICEBERG_VOL;

-- Drop the warehouse
DROP WAREHOUSE IF EXISTS FLEET_ANALYTICS_WH;

-- Drop roles
DROP ROLE IF EXISTS FLEET_ANALYST;
DROP ROLE IF EXISTS FLEET_ENGINEER;
DROP ROLE IF EXISTS FLEET_ADMIN;

-- If you created replication groups, remove them
DROP REPLICATION GROUP IF EXISTS FLEET_ANALYTICS_REPLICATION;

-- Remove network policy from user (if applied)
ALTER USER <your_username> UNSET NETWORK_POLICY;
DROP NETWORK POLICY IF EXISTS FLEET_STREAMING_POLICY;

-- External access integration
DROP INTEGRATION IF EXISTS OPEN_METEO_ACCESS;

SELECT 'Uncomment the commands above to cleanup' AS NOTE;
```

If you used external cloud storage, you may also want to clean up the Iceberg data files in your bucket/container.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've built a comprehensive analytics platform using Snowflake Iceberg V3 tables, demonstrating the full power of Snowflake's modern lakehouse architecture.

### What You Learned

- **Iceberg V3 Tables**: Created tables with VARIANT columns for semi-structured data, supporting flexible schemas
- **Streaming Ingestion**: Used Snowpipe Streaming to ingest real-time vehicle telemetry with sub-second latency
- **Multi-Source Ingestion**: Loaded data from web APIs and batch JSON files into Iceberg tables
- **Declarative Pipelines**: Built incremental transformation pipelines with Dynamic Iceberg Tables
- **Enterprise Governance**: Applied PII detection, masking policies, and data quality monitoring
- **Advanced Analytics**: Performed time-series analysis, forecasting, and geospatial queries
- **AI Integration**: Connected Iceberg data to Snowflake Intelligence for natural language analytics
- **Business Continuity**: Configured cross-region replication for disaster recovery
- **Interoperability**: Queried Iceberg tables from Spark with enforced access controls

### Key Benefits of Iceberg V3 Tables in Snowflake

1. **Open Format**: Data stored in open Apache Iceberg format, accessible by any compatible engine
2. **VARIANT Support**: Full semi-structured data capabilities with V3 table format
3. **Unified Governance**: Single place to manage security, quality, and lineage across all engines
4. **Incremental Processing**: Dynamic Tables automatically handle incremental transformations
5. **Enterprise Features**: Time travel, cloning, replication all work with Iceberg tables
6. **Performance**: Snowflake's query optimization applies to Iceberg tables

### Related Resources

**Documentation:**
- [Iceberg V3 Support in Snowflake](https://docs.snowflake.com/en/LIMITEDACCESS/iceberg/tables-iceberg-v3-specification-support)
- [Snowpipe Streaming](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
- [Dynamic Iceberg Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-create-iceberg)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- [Iceberg Table Replication](https://docs.snowflake.com/en/user-guide/tables-iceberg-replication)

**Guides:**
- [Build Declarative Pipelines with Dynamic Iceberg Tables](/en/developers/guides/declarative-pipelines-using-dynamic-iceberg-tables/)
- [Getting Started with Data Quality in Snowflake](/en/developers/guides/getting-started-with-data-quality-in-snowflake/)

**Assets:**
- [Guide Assets Folder](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/iceberg-v3-tables-comprehensive-guide/assets)

author: Doris Lee, Dureti Shemsi
language: en
id: intro-to-online-feature-store-in-snowflake
summary: Build real-time ML predictions using Snowflake Online Feature Store for low-latency feature serving 
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/applied-analytics, snowflake-site:taxonomy/snowflake-feature/snowflake-ml-functions, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/dynamic-tables,snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-intro-to-online-feature-store-in-snowflake


# Introduction to Online Feature Store in Snowflake

<!-- ------------------------ -->
## Overview

The Snowflake Online Feature Store provides low-latency, key-based feature retrieval for real-time ML inference. This guide demonstrates how to build an end-to-end machine learning workflow using the Online Feature Store to predict taxi trip durations in New York City.

You'll learn how to register entities and feature views, perform feature engineering, and use both online and offline stores for real-time inference.

### Prerequisites
- A Snowflake account (non-trial) in AWS or Azure commercial regions
- Basic knowledge of Python and SQL
- Familiarity with machine learning concepts
- ACCOUNTADMIN access or equivalent permissions

### What You'll Learn
- How to set up the Snowflake Feature Store
- How to register entities and create feature views
- How to enable online serving for low-latency inference
- How to train an XGBoost model using feature store data
- How to make real-time predictions using online features

### What You'll Need
- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account
- Basic understanding of Snowpark and Snowflake ML

### What You'll Build
- A complete feature store for taxi trip prediction
- Online feature views for real-time inference
- An XGBoost regression model
- A real-time prediction system using online features

<!-- ------------------------ -->
## Setup and Data Preparation

This section covers environment setup, notebook upload, and loading the sample dataset for the feature store guide.

### Run the Setup Script

1. Open Snowflake and navigate to <a href="https://app.snowflake.com/_deeplink/#/workspaces?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=intro-to-online-feature-store-in-snowflake&utm_cta=developer-guides-deeplink" class="_deeplink">**Projects** > **Workspaces**</a>
2. Create a new SQL file
3. Copy and paste the following setup script
4. Run the entire script as **ACCOUNTADMIN**

```sql
-- ============================================================================
-- Snowflake Setup Script for Online Feature Store Demo
-- ============================================================================

USE ROLE ACCOUNTADMIN;

SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;

-- Set query tag for tracking
ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"sfguide_intro_to_online_feature_store", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- SECTION 1: CREATE ROLE AND GRANT ACCOUNT-LEVEL PERMISSIONS
-- ============================================================================

-- Create role for Feature Store operations and grant to current user
CREATE OR REPLACE ROLE FS_DEMO_ROLE;
GRANT ROLE FS_DEMO_ROLE TO USER identifier($USERNAME);

-- Grant account-level permissions
GRANT CREATE DATABASE ON ACCOUNT TO ROLE FS_DEMO_ROLE;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE FS_DEMO_ROLE;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE FS_DEMO_ROLE;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE FS_DEMO_ROLE;
GRANT IMPORT SHARE ON ACCOUNT TO ROLE FS_DEMO_ROLE;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE FS_DEMO_ROLE;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE FS_DEMO_ROLE;

-- ============================================================================
-- SECTION 2: SWITCH TO ROLE AND CREATE RESOURCES
-- ============================================================================

USE ROLE FS_DEMO_ROLE;

-- Create warehouse
CREATE OR REPLACE WAREHOUSE FS_DEMO_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for Feature Store demo';

-- Create database and schema
CREATE OR REPLACE DATABASE FEATURE_STORE_DEMO
    COMMENT = 'Database for Feature Store with taxi trip prediction';

CREATE OR REPLACE SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES
    COMMENT = 'Schema for taxi features and online feature store';

-- Use the created resources
USE WAREHOUSE FS_DEMO_WH;
USE DATABASE FEATURE_STORE_DEMO;
USE SCHEMA TAXI_FEATURES;

-- Create stage for model assets with directory enabled
CREATE OR REPLACE STAGE FS_DEMO_ASSETS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for storing model assets and data files';

-- Grant full privileges on database and schema to the role
GRANT ALL PRIVILEGES ON DATABASE FEATURE_STORE_DEMO TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON WAREHOUSE FS_DEMO_WH TO ROLE FS_DEMO_ROLE;

-- Grant future privileges to handle dynamically created objects
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE DYNAMIC TABLES IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE STAGES IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE FUNCTIONS IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE IMAGE REPOSITORIES IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;
GRANT ALL PRIVILEGES ON FUTURE SERVICES IN SCHEMA FEATURE_STORE_DEMO.TAXI_FEATURES TO ROLE FS_DEMO_ROLE;

-- ============================================================================
-- SECTION 3: NETWORK RULES AND EXTERNAL ACCESS FOR NOTEBOOKS
-- ============================================================================

-- Create network rule to allow all external access (required for notebooks)
CREATE OR REPLACE NETWORK RULE ALLOW_ALL_RULE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80');

-- Switch back to ACCOUNTADMIN to create integration
USE ROLE ACCOUNTADMIN;

-- Create external access integration (requires ACCOUNTADMIN)
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION ALLOW_ALL_INTEGRATION
    ALLOWED_NETWORK_RULES = (FEATURE_STORE_DEMO.TAXI_FEATURES.ALLOW_ALL_RULE)
    ENABLED = TRUE;

-- Grant usage on the external access integration to FS_DEMO_ROLE
GRANT USAGE ON INTEGRATION ALLOW_ALL_INTEGRATION TO ROLE FS_DEMO_ROLE;

-- Switch back to FS_DEMO_ROLE
USE ROLE FS_DEMO_ROLE;

-- ============================================================================
-- SECTION 4: COMPUTE POOL FOR MODEL DEPLOYMENT
-- ============================================================================

-- Create compute pool for SPCS model serving
CREATE COMPUTE POOL IF NOT EXISTS trip_eta_prediction_pool
    MIN_NODES = 3
    MAX_NODES = 3
    INSTANCE_FAMILY = 'CPU_X64_L'
    AUTO_RESUME = TRUE
    COMMENT = 'Compute pool for taxi ETA prediction service';

-- Grant usage on compute pool
GRANT USAGE ON COMPUTE POOL trip_eta_prediction_pool TO ROLE FS_DEMO_ROLE;
GRANT OPERATE ON COMPUTE POOL trip_eta_prediction_pool TO ROLE FS_DEMO_ROLE;

-- ============================================================================
-- SETUP COMPLETE
-- ============================================================================
```

This will create:
- A dedicated role: `FS_DEMO_ROLE`
- A warehouse: `FS_DEMO_WH`
- A database: `FEATURE_STORE_DEMO`
- A schema: `TAXI_FEATURES`
- A stage: `FS_DEMO_ASSETS` 
- Network rule and external access integration for notebooks
- Compute pool for SPCS model deployment

The setup script automatically grants the `FS_DEMO_ROLE` to your current user.

### Upload and Open Notebook

Now that your environment is set up, import the guide notebook to Snowflake.

### Run the Notebook

Download the notebook file to your local machine:

1. Click this link: [0_start_here.ipynb](https://github.com/Snowflake-Labs/sfguide-intro-to-online-feature-store-in-snowflake/blob/main/notebooks/0_start_here.ipynb)
2. On the GitHub page, click the **Download raw file** button (download icon in the top right of the file preview)
3. Save the `.ipynb` file to your computer

Now import the notebook into Snowflake:

1. Change role to `FS_DEMO_ROLE`
2. Navigate to **Projects** > **Notebooks** in Snowsight
3. Click **Import .ipynb** from the **+ Notebook** dropdown
4. Select the downloaded `0_start_here.ipynb` file from your computer
5. Create a new notebook with the following settings:
   - **Notebook Location**: `FEATURE_STORE_DEMO`, `TAXI_FEATURES`
   - **Run On**: Container
   - **Warehouse**: `FS_DEMO_WH`
   - **Compute Pool**: `trip_eta_prediction_pool`

The notebook will open and be ready to run.

### Add External Access to Notebook

After creating the notebook, you need to configure external access to allow the notebook to install Python packages and access external resources required by Snowflake ML libraries.

1. Open the notebook in Snowsight
2. Click the **three dots menu** (⋮) in the top right
3. Select **Notebook settings**
4. Under **External Access Integrations**, click **+ External Access Integration**
5. Select `ALLOW_ALL_INTEGRATION` from the dropdown
6. Click **Save** to apply changes

> NOTE:
> The `ALLOW_ALL_INTEGRATION` external access integration was created by the setup script and allows the notebook to install Python packages and access external APIs required by Snowflake ML libraries.

### Load Sample Data

The notebook uses NYC taxi trip data to demonstrate the Online Feature Store. The data is loaded automatically using Snowflake ML's example helper.

### What's in the Dataset

The NYC Yellow Taxi dataset contains:
- **Pickup and dropoff location IDs**: Geographic areas in NYC
- **Timestamps**: When trips started and ended
- **Trip metrics**: Distance, duration, fare amounts
- **Additional features**: Vendor ID, passenger count, payment type

### Loading the Data

Run the data loading cells in the notebook:

```python
from snowflake.ml.feature_store.examples.example_helper import ExampleHelper

example_helper = ExampleHelper(session, TAXI_DB, TAXI_SCHEMA)
source_tables = example_helper.load_example('new_york_taxi_features')
```

This creates the `NYC_YELLOW_TRIPS` table with sample taxi trip data ready for feature engineering.

<!-- ------------------------ -->
## Build Feature Store

This section covers initializing the feature store, registering entities, and engineering features for the taxi trip prediction model.

### Create Feature Store Instance

```python
from snowflake.ml.feature_store import CreationMode, FeatureStore

fs = FeatureStore(
    session=session,
    database=TAXI_DB,
    name=TAXI_SCHEMA,
    default_warehouse=session.get_current_warehouse(),
    creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
)
```

The Feature Store will:
- Store feature definitions and metadata
- Manage feature versioning
- Handle data synchronization between offline and online stores
- Track feature lineage

### Register Entities

Entities represent the keys used to join features. For taxi trip prediction, we define entities for routes and pickup times.

### Define Route Entity

The route entity represents a trip from one location to another:

```python
from snowflake.ml.feature_store.entity import Entity

route_entity = Entity(
    name="route",
    join_keys=["PULOCATIONID", "DOLOCATIONID"],
    desc="A taxi route defined by pickup and dropoff location IDs"
)
```

### Define Pickup Time Entity

The pickup time entity captures temporal patterns:

```python
pickup_time_entity = Entity(
    name="pickup_time",
    join_keys=["PICKUP_HOUR", "PICKUP_DAY_OF_WEEK"],
    desc="Pickup time bucketed by hour and day of week"
)
```

### Register Entities

```python
fs.register_entity(route_entity)
fs.register_entity(pickup_time_entity)

# View registered entities
fs.list_entities().show()
```

### Engineer Features

Create meaningful features from raw taxi trip data to improve model predictions.

### Time-Based Features

Extract temporal patterns:

```python
df = df.with_columns([
    hour(col("TPEP_PICKUP_DATETIME")).alias("PICKUP_HOUR"),
    dayofweek(col("TPEP_PICKUP_DATETIME")).alias("PICKUP_DAY_OF_WEEK"),
    month(col("TPEP_PICKUP_DATETIME")).alias("PICKUP_MONTH"),
])
```

### Derived Features

Calculate trip characteristics:

```python
df = df.with_column(
    "SPEED_MPH",
    (col("TRIP_DISTANCE") / nullifzero(col("TRIP_DURATION_MIN")) * 60)
)

df = df.with_column(
    "IS_RUSH_HOUR",
    when((col("PICKUP_HOUR") >= 7) & (col("PICKUP_HOUR") <= 9), 1)
    .when((col("PICKUP_HOUR") >= 16) & (col("PICKUP_HOUR") <= 18), 1)
    .otherwise(0)
)
```

### Aggregate Features

Compute route-level statistics:

```python
route_stats = df.group_by("PULOCATIONID", "DOLOCATIONID").agg([
    avg("TRIP_DURATION_MIN").alias("AVG_ETA_ROUTE"),
    avg("TRIP_DISTANCE").alias("AVG_DISTANCE_ROUTE"),
    avg("SPEED_MPH").alias("AVG_SPEED_ROUTE")
])
```

<!-- ------------------------ -->
## Enable Online Feature Serving

This section covers creating feature views with online serving enabled and monitoring the refresh process.

### Define Feature View

```python
from snowflake.ml.feature_store import feature_view

route_fv = feature_view.FeatureView(
    name="nyc_taxi_trip_fv",
    entities=[route_entity, pickup_time_entity],
    feature_df=feature_df,
    timestamp_col="TPEP_PICKUP_DATETIME",
    refresh_freq="60s",
    desc="Trip-based features for taxi ETA prediction",
    online_config=feature_view.OnlineConfig(
        enable=True, 
        target_lag="10s"
    ),
)
```

### Key Configuration Parameters

- **refresh_freq**: How often to refresh the offline feature table (Dynamic Table)
- **target_lag**: Maximum acceptable lag for online features
- **online_config.enable**: Enables online serving for low-latency lookups

### Register Feature View

```python
registered_route_fv = fs.register_feature_view(route_fv, "v1", overwrite=True)

print("Registered feature view:", registered_route_fv.name)
print("Online feature table:", registered_route_fv.fully_qualified_online_table_name())
```

The online feature table will automatically sync data from the offline store based on the target lag setting.

### Monitor Online Feature Refresh

Check that the online feature table is refreshing properly.

### View Refresh History

```python
fs.get_refresh_history(
    registered_route_fv, 
    store_type=feature_view.StoreType.ONLINE
).show()
```

This shows:
- Refresh timestamps
- Number of rows updated
- Refresh status (success/failure)
- Any error messages

### Read from Online Store

Once refreshed, you can read from the online feature store:

```python
online_df = fs.read_feature_view(
    registered_route_fv,
    store_type=feature_view.StoreType.ONLINE,
)
online_df.show()
```

> NOTE:
> The first refresh may take 10-30 seconds. If you see "not refreshed yet" error, wait a moment and re-run the cell.

<!-- ------------------------ -->
## Train ML Model

Train an XGBoost regression model to predict taxi trip durations using features from the feature store.

### Create Train/Test Split

```python
train_spine_df, test_spine_df = df.select(spine_cols).random_split([0.85, 0.15], seed=42)
```

### Generate Training Dataset

Use the feature store to automatically join features:

```python
train_df = fs.generate_training_set(
    spine_df=train_spine_df,
    features=[registered_route_fv],
    spine_timestamp_col="TPEP_PICKUP_DATETIME",
    include_feature_view_timestamp_col=False
)
```

### Train XGBoost Model

```python
from snowflake.ml.modeling.xgboost import XGBRegressor

regressor = XGBRegressor(
    input_cols=feature_columns,
    label_cols=["ETA_MINUTES"],
    output_cols=["predicted_eta"]
)
regressor.fit(train_df)
```

### Evaluate Model

```python
from sklearn.metrics import mean_squared_error, r2_score

predictions = regressor.predict(test_df)
predictions_pd = predictions.to_pandas()

mse = mean_squared_error(predictions_pd["ETA_MINUTES"], predictions_pd["predicted_eta"])
r2 = r2_score(predictions_pd["ETA_MINUTES"], predictions_pd["predicted_eta"])

print(f"Test MSE: {mse:.2f}")
print(f"Test R²: {r2:.2f}")
```

<!-- ------------------------ -->
## Make Real-Time Predictions

Use online features for low-latency, real-time predictions.

### Define Prediction Function

```python
def predict_trip_duration(pu_location_id, do_location_id, pickup_hour, pickup_day_of_week):
    trip = [[pu_location_id, do_location_id, pickup_hour, pickup_day_of_week]]
    
    # Fetch latest features from online store
    features_df = fs.read_feature_view(
        registered_route_fv,
        keys=trip,
        store_type=feature_view.StoreType.ONLINE
    )
    
    features_pd = features_df.to_pandas()
    if features_pd.empty:
        print("No online features found")
        return None
    
    return regressor.predict(features_pd)
```

### Make a Prediction

```python
# Predict trip from location 141 to 236 at 8am on Sunday
prediction = predict_trip_duration(141, 236, 8, 0)
print(f"Predicted trip duration: {prediction['predicted_eta'][0]:.1f} minutes")
```

### Why Use Online Features?

- **Low latency**: Point lookups by key (milliseconds)
- **Always fresh**: Automatic background refresh
- **Scalable**: Built on Snowflake's elastic infrastructure
- **Consistent**: Same features for training and serving

### Register Model (Optional)

Register your trained model in Snowflake Model Registry for versioning and deployment.

#### Log Model

```python
from snowflake.ml.registry import Registry

registry = Registry(session=session)
model_name = "NYC_TAXI_ETA_XGB"

mv = registry.log_model(
    model=regressor,
    model_name=model_name,
    comment="Predict NYC taxi trip durations using Feature Store",
    metrics={"test_mse": float(mse), "test_r2": float(r2)},
    version_name="v1",
)
```

#### View Registered Models

```python
registry.show_models()
```

The Model Registry provides:
- Version control for models
- Lineage tracking
- Deployment management
- Performance metrics storage

### Deploy Model to SPCS (Optional)

Deploy your model as a containerized service for scalable inference.

#### Prerequisites

Ensure the compute pool was created during setup:

```sql
SHOW COMPUTE POOLS LIKE 'trip_eta_prediction_pool';
```

#### Create Service

```python
latest_model = registry.get_model(model_name).version("v1")
service_name = "NYC_TAXI_ETA_V1"

latest_model.create_service(
    service_name=service_name,
    service_compute_pool="trip_eta_prediction_pool",
    ingress_enabled=True
)
```

#### Make Predictions via Service

```python
spcs_prediction = latest_model.run(
    features_pd, 
    function_name='predict', 
    service_name=service_name
)
print("Prediction from SPCS:", spcs_prediction)
```

<!-- ------------------------ -->
## Clean Up Guide Resources

When you're finished with the guide, you can remove all created resources to avoid incurring costs.

### Run the Teardown Script

Download the teardown script to your local machine:

1. Click this link: [teardown.sql](https://github.com/Snowflake-Labs/sfguide-intro-to-online-feature-store-in-snowflake/blob/main/scripts/teardown.sql)
2. On the GitHub page, click the **Download raw file** button (download icon in the top right of the file preview)
3. Save the `.sql` file to your computer

Now run the teardown script in Snowflake:

1. Open Snowflake and navigate to **Projects** > **Workspaces**
2. Create a new SQL file
3. Open the downloaded `teardown.sql` file and copy all its contents
4. Paste the script into your Snowflake SQL file
5. Run the entire script as **ACCOUNTADMIN**

The teardown script will:
- Stop all running services
- Drop the compute pool
- Drop the external access integration
- Drop the database (including all tables, views, and dynamic tables)
- Drop the warehouse
- Revoke all account-level permissions
- Drop the `FS_DEMO_ROLE`

> NOTE:
> This will permanently delete all data and resources created during the guide.

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've successfully built an end-to-end ML workflow using Snowflake Online Feature Store.

### What You Learned
- How to set up and configure the Snowflake Feature Store
- How to register entities and create feature views
- How to enable online serving for real-time inference
- How to engineer features for machine learning
- How to train models using feature store data
- How to make low-latency predictions with online features
- (Optional) How to deploy models to Snowpark Container Services

### Key Takeaways

- **Online Feature Store** provides millisecond-latency feature retrieval
- **Feature Views** manage both offline (training) and online (inference) features
- **Automatic Refresh** keeps online features in sync with minimal lag
- **Point Lookups** by entity keys enable real-time ML applications

### Related Resources

- [GitHub Repository - Complete Code and Notebooks](https://github.com/Snowflake-Labs/sfguide-intro-to-online-feature-store-in-snowflake)
- [Snowflake Feature Store Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview)
- [Snowflake ML for Python](https://docs.snowflake.com/en/developer-guide/snowpark-ml/index)
- [Online Feature Tables Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python)
- [Snowpark ML Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)

### Next Steps

- Try the feature store with your own datasets
- Explore incremental refresh modes for cost optimization
- Integrate online features into production applications
- Experiment with different ML models and feature combinations

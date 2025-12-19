author: Vino Duraisamy
id: analyze-logistics-data-using-snowpark-connect-for-apache-spark
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/snowpark
language: en
summary: Analyze logistics and supply chain data with Snowpark Connect for Apache Spark™ on Snowflake for shipping and inventory insights.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Analyzing Logistics Data using Snowpark Connect for Apache Spark
<!-- ------------------------ -->

## Overview

Through this quickstart, you will learn how to analyze logistics and supply chain data using [Snowpark Connect for Apache Spark™](/en/blog/snowpark-connect-apache-spark-preview/). You'll work with carrier performance metrics and freight bills data to identify delivery risks and performance patterns.

### What You'll Learn

By the end of this quickstart, you will learn how to:

* Connect to the Snowpark Connect server and initialize a Spark session
* Load and analyze carrier performance data
* Examine freight bill details and delivery confirmations
* Join multiple datasets using PySpark DataFrame operations
* Identify shipments at risk of delays
* Write analyzed data back to Snowflake tables

### Key Features

* **Zero Migration Overhead**: Bring existing Spark code to Snowflake with minimal changes
* **Better Performance**: Use Snowpark runtime for improved analytics performance
* **Native DataFrame APIs**: Use familiar PySpark DataFrame operations on Snowflake data

### Dataset Description

You'll be analyzing two main datasets:

1. **Carrier Performance Metrics**: Historical performance data for different shipping carriers including on-time delivery rates, damage claims, and customer satisfaction scores
2. **Freight Bills**: Detailed shipping transaction records including costs, routes, origin/destination information, and delivery details

### What You'll Build

* A complete logistics analytics pipeline using PySpark on Snowflake
* Carrier performance analysis reports
* Freight bill cost and route analytics
* An integrated `deliveries_at_risk` table for operational monitoring

### Prerequisites

* A Snowflake account. If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).

### Learn More About Snowpark Connect

For a comprehensive introduction to Snowpark Connect for Apache Spark, refer to the [Intro to Snowpark Connect notebook](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/intro_to_snowpark_connect.ipynb). You can also explore the official [Snowpark Connect documentation](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview) to learn more about its capabilities and features.

<!-- ------------------------ -->
## Setup 

Sign up for a [Snowflake Free Trial](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account and login to Snowflake home page.

Download the `Analyze_logistics_data_using_Snowpark_connect.ipynb` from [this git repository](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/Analyze_logistics_data_using_Snowpark_connect.ipynb).

### Import the Notebook into Snowflake

* In the Snowsight UI, navigate to `Projects` and click on `Notebooks`.
* On the top right, click on the down arrow next to `+ Notebook` and select `Import ipynb file`.
* Select the `Analyze_logistics_data_using_Snowpark_connect.ipynb` you had downloaded earlier.
* Select notebook location as `snowflake_learning_db` and `public` schema.
* Select `run on warehouse` option, select `query warehouse` as `compute_wh` and `create`.

Now you have successfully imported the notebook that contains PySpark code for logistics analysis.

### Install snowpark-connect Package

Select the packages drop down at the top right of the notebook. Look for `snowpark-connect` package and install it using the package picker.

After the installation is complete, start or restart the notebook session.

<!-- ------------------------ -->
## Load Data

The first step is to initialize the Spark session using Snowpark Connect. This connects your PySpark code to the Snowflake compute engine.

```python
import warnings
warnings.filterwarnings('ignore')

from snowflake import snowpark_connect
from snowflake.snowpark.context import get_active_session

from pyspark.sql.functions import col, avg, sum

session = get_active_session()
print(session)

spark = snowpark_connect.server.init_spark_session()
```

### Set Up Database and Schema

First, configure the database and schema for your logistics data:

```sql
use schema stratos_dynamics_scm.data;
```

### Create File Format

Create a CSV file format to properly parse the incoming data files:

```sql
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  NULL_IF = ('', 'NULL')
  EMPTY_FIELD_AS_NULL = TRUE
  COMPRESSION = 'AUTO';
```

### Create External Stage

Set up an external stage pointing to the S3 bucket containing the logistics data:

```sql
CREATE OR REPLACE STAGE stratos_public_s3_stage
  URL = 's3://sfquickstarts/logistics-data-stratos-dynamics/'
  FILE_FORMAT = csv_format;
```

### Create Target Tables

Create a table to store carrier performance data:

```sql
CREATE OR REPLACE TABLE carrier_performance_metrics (
    metric_id                     VARCHAR,
    carrier_name                  VARCHAR,
    reporting_period              VARCHAR,
    period_start_date             DATE,
    period_end_date               DATE,
    total_shipments               INT,
    on_time_deliveries            INT,
    on_time_percentage            FLOAT,
    total_weight_lbs              FLOAT,
    damage_claims                 INT,
    damage_rate_percentage        FLOAT,
    total_damage_cost             NUMERIC(18, 2),
    average_transit_days          FLOAT,
    customer_satisfaction_score   FLOAT,
    total_freight_cost            NUMERIC(18, 2),
    cost_per_shipment             NUMERIC(18, 2),
    load_timestamp                TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);
```

Create a table to store freight bill transaction data:

```sql
CREATE OR REPLACE TABLE freight_bills (
    bill_id                 VARCHAR,
    pro_number              VARCHAR,
    po_number               VARCHAR,
    carrier_name            VARCHAR,
    ship_date               DATE,
    delivery_date           DATE,
    origin_city             VARCHAR,
    origin_state            VARCHAR,
    origin_country          VARCHAR,
    origin_zip              INT,
    destination_city        VARCHAR,
    destination_state       VARCHAR,
    destination_country     VARCHAR,
    destination_zip         INT,
    destination_facility    VARCHAR,
    component_code          VARCHAR,
    component_name          VARCHAR,
    quantity                INT,
    weight_lbs              FLOAT,
    declared_value          INT,
    freight_class           FLOAT,
    base_charge             NUMERIC(18, 2),
    weight_charge           NUMERIC(18, 2),
    fuel_surcharge          NUMERIC(18, 2),
    accessorial_charges     NUMERIC(18, 2),
    total_charge            NUMERIC(18, 2),
    payment_terms           VARCHAR,
    payment_status          VARCHAR,
    invoice_date            DATE,
    load_timestamp          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);
```

<!-- ------------------------ -->
## Run PySpark Code

### Analyze Carrier Performance Metrics

Load and analyze the carrier performance data using PySpark DataFrames:

```python
carrier_metrics = "stratos_dynamics_scm.data.carrier_performance_metrics"
carrier_metrics_df = spark.sql(f"select * from {carrier_metrics}")
carrier_metrics_df.show()
```

### Analyze Delivery Confirmations

Examine delivery confirmation data to track actual vs. scheduled delivery dates. This helps identify potential delivery delays and at-risk shipments:

```python
deliveries = "build25_de_keynote.data.delivery_confirmations"
deliveries_df = spark.sql(f"select * from {deliveries}")
deliveries_df.show(5)
```

### Analyze Freight Bill Details

Examine freight bill data to understand shipping costs, routes, and transaction details:

```python
freight_bills = "build25_de_keynote.data.freight_bills"
freight_bills_df = spark.sql(f"select * from {freight_bills}")
freight_bills_df.show(5)
```

### Join and Analyze Datasets

Combine freight bill data with delivery confirmations to create a comprehensive view of shipments. This join helps:

1. **Identify At-Risk Deliveries**: Compare scheduled vs. actual delivery dates
2. **Cost Analysis**: Associate costs with delivery performance
3. **Route Analytics**: Understand shipping patterns and potential bottlenecks
4. **Operational Insights**: Create actionable data for logistics optimization

```python
dc = deliveries_df.alias("dc")
fb = freight_bills_df.alias("fb")

# Join with aliases
deliveries_at_risk = dc.join(fb, on="bill_id", how="inner")

# Select specific columns using aliases
deliveries_at_risk = deliveries_at_risk.select(
    "bill_id",
    col("dc.pro_number").alias("pro_number"),
    col("dc.po_number").alias("po_number"),
    col("dc.carrier_name").alias("carrier_name"),
    col("dc.scheduled_delivery_date").alias("scheduled_delivery_date"),
    col("dc.actual_delivery_date").alias("actual_delivery_date"),
    col("fb.destination_city"),
    col("fb.destination_state"),
    col("fb.destination_country"),
    col("fb.destination_zip"),
    col("fb.destination_facility"),
    col("fb.origin_city"),
    col("fb.origin_state"),
    col("fb.origin_country"),
    col("fb.origin_zip"),
    col("fb.component_code"),
    col("fb.component_name"),
    col("fb.quantity"),
    col("fb.weight_lbs"),
    col("fb.declared_value"),
    col("fb.total_charge"),
    col("fb.payment_terms"),
    col("fb.payment_status"),
    col("fb.invoice_date"),
    col("fb.quantity").alias("product_quantity"),
    col("fb.freight_class")
)

deliveries_at_risk.show()
```

### Write Results to Snowflake

Write the joined and analyzed data as a new Snowflake table called `deliveries_at_risk`. This table serves as an operational dashboard for logistics teams to monitor and take action on potential delivery issues:

```python
deliveries_at_risk.write.mode("append").saveAsTable(f"{db_name}.{schema_name}.deliveries_at_risk")
```

The `deliveries_at_risk` table is now available for business intelligence tools, reporting dashboards, and operational workflows.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations, you have successfully completed this quickstart!

### What You Built

* ✅ **Data Infrastructure**: Set up file formats, external stages, and table schemas in Snowflake
* ✅ **Data Loading**: Imported carrier performance and freight bill data from S3
* ✅ **Spark Analytics**: Used familiar PySpark DataFrames on Snowflake data
* ✅ **Data Integration**: Joined multiple datasets to create operational insights
* ✅ **Actionable Results**: Created a `deliveries_at_risk` table for ongoing monitoring

### What You Learned

* Connect to the Snowpark Connect server and initialize a Spark session
* Load and analyze carrier performance data
* Examine freight bill details and delivery confirmations
* Join multiple datasets using PySpark DataFrame operations
* Write analyzed data back to Snowflake tables

### Related Resources

* [Snowpark Connect Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
* [Source code on GitHub](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/Analyze_logistics_data_using_Snowpark_connect.ipynb)
* [Getting Started with Snowpark Connect](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/getting_started_with_snowpark_connect_for_apache_spark.ipynb)
* [Comprehensive Intro to Snowpark Connect](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/intro_to_snowpark_connect.ipynb)


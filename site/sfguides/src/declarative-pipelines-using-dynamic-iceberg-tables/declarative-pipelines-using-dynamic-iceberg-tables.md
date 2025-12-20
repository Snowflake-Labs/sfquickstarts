authors: Phani Alapaty, Vino Duraisamy
id: declarative-pipelines-using-dynamic-iceberg-tables
summary: Build declarative data pipelines with Snowflake Dynamic Iceberg Tables for automatic, incremental transformations in open formats.
categories: snowflake-site:taxonomy/snowflake-feature/dynamic-tables
environments: web
language: en
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, Iceberg Tables, Dynamic Tables, Python

# Build Declarative Pipelines using Snowflake Dynamic Iceberg Tables
<!-- ------------------------ -->
## Overview 



This guide demonstrates how to build a declarative incremental pipeline and establish a multi-layered lakehouse architecture in Snowflake using Dynamic Iceberg Tables that read from and write back to an external AWS Glue Catalog-managed Iceberg data lake.

### What You Will Learn

By the end of this guide, you will learn to work with:
* Configuring Snowflake Catalog Integrations to connect to an external AWS Glue Catalog.
* Creating a Linked Database to query external Iceberg tables in the Bronze layer as if they were native Snowflake tables.
* Implementing Dynamic Iceberg Tables in the Silver and Gold layers for automated refresh (using TARGET_LAG) and write-back to the external S3 location defined by an External Volume.
* Modeling a multi-layered lakehouse: Bronze (raw data), Silver (cleaned and enhanced data), and Gold (aggregated, analytical data).
* Verifying how incremental data inserts into the Bronze layer automatically propagate through the Silver and Gold layers.

### What You'll Build

You will build a three-tiered lakehouse architecture in Snowflake:
**Bronze Layer**: Connects Snowflake to the AWS Glue Managed Iceberg tables using Snowflake Catalog Integration and Catalog Linked Database.
**Silver Layer**: Creates dynamic Iceberg tables that apply cleaning and standardization to the Bronze data, with results stored as Snowflake Managed Iceberg tables back in S3.
**Gold Layer**: Creates final, denormalized, and aggregated Snowflake dynamic Iceberg tables optimized for analytical reporting by joining the Silver-layer entities.

### Prerequisites

* A Snowflake account with the necessary permissions to create Catalog Integrations, External Volumes, and Dynamic Iceberg Tables.
* An external AWS Glue Catalog managing Iceberg metadata.
* An S3 bucket containing the Iceberg data files.
* Appropriate IAM roles configured for Snowflake to access both the Glue Catalog (via SIGV4 for the Catalog Integration) and the S3 data location (for the External Volume).

<!--------------->

## AWS Setup


Creating Glue managed Iceberg tables in the AWS Glue Catalog is a key step to setting up the Bronze layer for the Snowflake Iceberg integration. You can create the Glue managed Iceberg tables using the AWS Management Console (via AWS Glue or Lake Formation) or using SQL via Amazon Athena. For now, we will use Athena to define the schema and table properties for Iceberg.

### Prerequisites in AWS

Before creating the tables, ensure these components are ready:

AWS Glue Database: You must have the bronze_analytics_db created in your AWS Glue Catalog.
S3 Location: An S3 path (e.g., s3://<your-bucket-name>/glue-iceberg/) where the Iceberg metadata and data files will reside. This location must correspond to the STORAGE_BASE_URL defined in your Snowflake EXTERNAL VOLUME.
Permissions: You need the appropriate AWS IAM permissions to create tables in the Glue Catalog and read/write to the S3 location (often configured via AWS Lake Formation if it is enabled).

### Create Iceberg Tables using Amazon Athena

Amazon Athena provides a simple SQL interface to create and manage Glue-managed Iceberg tables.

* Setup and Database Selection
    1. Navigate to the Amazon Athena console
    2. Select the workgroup configured to interact with Iceberg and your S3 query results location.
    3. Ensure the correct database is selected in the editor: bronze_analytics_db.
* Table Creation SQL
Use the CREATE TABLE statement with the TBLPROPERTIES clause to specify the Iceberg format and the Amazon S3 location. Repeat this for all four tables, replacing <S3_ICEBERG_ROOT_PATH> with your specific S3 path (e.g., s3://<bucket_name>/glue-iceberg/).

de_orders Table Creation. This table contains the core transactional order information.

```sql
CREATE TABLE bronze_analytics_db.de_orders (
    billing_address STRING,
    created_at TIMESTAMP,
    currency STRING,
    customer_id BIGINT,
    delivery_date TIMESTAMP,
    discount_amount DOUBLE,
    notes STRING,
    order_date TIMESTAMP,
    order_id BIGINT,
    order_status STRING,
    order_uuid STRING,
    payment_method STRING,
    payment_status STRING,
    shipping_address STRING,
    shipping_cost DOUBLE,
    shipping_date TIMESTAMP,
    shipping_method STRING,
    subtotal DOUBLE,
    tax_amount DOUBLE,
    total_amount DOUBLE,
    updated_at TIMESTAMP)
LOCATION 's3://<s3_bucket>/glue-iceberg/de_orders'
TBLPROPERTIES (
  'table_type'='iceberg',
  'write_compression'='snappy'
);

```

de_order_items Table Creation. This table holds the line-item details for each order.

```sql

CREATE TABLE IF NOT EXISTS bronze_analytics_db.de_order_items (
    created_at TIMESTAMP,
    discount_percent BIGINT,
    line_total DOUBLE,
    order_id BIGINT,
    order_item_id BIGINT,
    product_id BIGINT,
    quantity BIGINT,
    tax_rate DOUBLE,
    total_price DOUBLE,
    unit_price DOUBLE,
    updated_at TIMESTAMP
)
LOCATION 's3://<s3_bucket>/glue-iceberg/de_order_items'
TBLPROPERTIES (
  'table_type'='iceberg',
  'write_compression'='snappy'
);

```

de_products Table Creation. This table stores the product dimension data.

```sql
CREATE TABLE bronze_analytics_db.de_products (
  barcode string,
  brand string,
  category string,
  color string,
  cost_price double,
  created_at timestamp,
  description string,
  dimensions_cm string,
  is_active boolean,
  launch_date timestamp,
  material string,
  product_id bigint,
  product_name string,
  product_uuid string,
  reorder_level bigint,
  size string,
  sku string,
  stock_quantity bigint,
  subcategory string,
  supplier_id bigint,
  unit_price double,
  updated_at timestamp,
  weight_kg double)
LOCATION 's3://<s3_bucket>/glue-iceberg/de_products'
TBLPROPERTIES (
  'table_type'='iceberg',
  'write_compression'='snappy'
);

```

de_customers Table Creation. This table stores the customer dimension data.

```sql
CREATE TABLE bronze_analytics_db.de_customers (
  address_line1 string,
  address_line2 string,
  city string,
  country string,
  created_at timestamp,
  customer_id bigint,
  customer_segment string,
  customer_uuid string,
  date_of_birth timestamp,
  email string,
  first_name string,
  gender string,
  is_active boolean,
  last_login_date timestamp,
  last_name string,
  phone string,
  postal_code string,
  registration_date timestamp,
  state string,
  total_orders bigint,
  total_spent double,
  updated_at timestamp)
LOCATION 's3://<s3_bucket>/glue-iceberg/de_customers'
TBLPROPERTIES (
  'table_type'='iceberg',
  'write_compression'='snappy'
);
```

### Check if the tables are created in AWS Glue console

* Navigate to the AWS Glue console.
* Go to Tables and filter by the database bronze_analytics_db.
* Confirm that all four tables (de_orders, de_order_items, de_products, de_customers) are listed.
* Check the Table Properties for each table to confirm:
table_type is set to ICEBERG.
* The location points to your S3 Iceberg metadata path.

Note: I have also provided an AWS Glue job to populate the Glue managed Iceberg tables with test data. This is the AWS glue script which can be reused for populating the tables with mock data.

Download the iceberg_dt.py file from [this git repository](https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/dynamic_iceberg_tables) and run it from Glue.

<!--------------->

## Snowflake Setup


### Catalog Integration and Catalog Linked Database (CLD)

#### Snowflake Catalog Integration

This step creates a Snowflake Catalog Integration to connect to the AWS Glue Catalog, which acts as the metadata store for the Iceberg tables. A catalog integration is a named, account-level Snowflake object that stores information about how your table metadata is organized for the following scenarios:

* When you don’t use Snowflake as the Iceberg catalog. For example, you need a catalog integration if your table is managed by AWS Glue.
* When you want to integrate with Snowflake Open Catalog to:
        * Query an Iceberg table in Snowflake Open Catalog using Snowflake.
        * Sync a Snowflake-managed Iceberg table with Snowflake Open Catalog so that third-party compute engines can query the table.

```sql
CREATE or replace CATALOG INTEGRATION glue_catalog_integration
  CATALOG_SOURCE = ICEBERG_REST -- Connects to the Iceberg REST Catalog endpoint
  TABLE_FORMAT = ICEBERG
  CATALOG_NAMESPACE = 'bronze_analytics_db'
    REST_CONFIG = (
    CATALOG_URI = 'https://glue.us-east-1.amazonaws.com/iceberg'
    CATALOG_API_TYPE = AWS_GLUE
    CATALOG_NAME = '<Your AWS Account ID>'
  )
  REST_AUTHENTICATION = (
    TYPE = SIGV4
    SIGV4_IAM_ROLE = 'arn:aws:iam::<Your AWS Account ID>:role/<role_arn>'
    SIGV4_SIGNING_REGION = 'us-east-1'   
)
ENABLED = TRUE;

```

#### External Volume Creation

An External Volume is created to define the S3 location where the actual Iceberg data files reside and specifies the IAM role for Snowflake to read/write the data.

```sql
CREATE OR REPLACE EXTERNAL VOLUME de_external_volume
  STORAGE_LOCATIONS =
    (
      (
        NAME = 'de_external_vol'
        STORAGE_PROVIDER = 'S3'
        STORAGE_BASE_URL = 's3://<bucket_name>/glue-iceberg/' -- S3 path for Iceberg data files 
        STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<account_id>:role/<role_arn>' -- IAM role for S3 read/write
        ENCRYPTION = ( TYPE = 'AWS_SSE_S3' )
      )
    )
  ALLOW_WRITES = TRUE;

```

#### Catalog Linked Database 

A catalog-linked database is a Snowflake database connected to an external Iceberg REST catalog. Snowflake automatically syncs with the external catalog to detect namespaces and Iceberg tables, and registers the remote tables to the catalog-linked database. Catalog-linked databases also support creating and dropping schemas or Iceberg tables.

```sql
CREATE OR REPLACE DATABASE glue_catalog_linked_db
  LINKED_CATALOG = (
    CATALOG = 'glue_catalog_integration',
    ALLOWED_NAMESPACES = ('bronze_analytics_db') -- Limit scope to the Bronze database 
    NAMESPACE_MODE = FLATTEN_NESTED_NAMESPACE,
    NAMESPACE_FLATTEN_DELIMITER = '-',
    SYNC_INTERVAL_SECONDS = 60 -- Snowflake checks for metadata updates every 60 seconds
  ),
  EXTERNAL_VOLUME = 'de_external_volume';
```

#### Verification and Exploration

Verify the setup and explore the discovered Bronze tables.

```sql

SELECT SYSTEM$VERIFY_CATALOG_INTEGRATION('glue_catalog_integration');

-- List schemas/namespaces available
SELECT SYSTEM$LIST_NAMESPACES_FROM_CATALOG('glue_catalog_integration', '',0);

-- Check the status of the new linked database
SELECT SYSTEM$CATALOG_LINK_STATUS('glue_catalog_linked_db');

-- List the Iceberg tables discovered
SELECT SYSTEM$LIST_ICEBERG_TABLES_FROM_CATALOG('glue_catalog_integration');

-- Show the linked schemas/namespaces
show schemas in database glue_catalog_linked_db;
use schema "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db";
show iceberg tables;
```

### Silver Layer Creation: Dynamic Iceberg Tables

The Silver layer applies cleaning, standardization, and enrichment, using Dynamic Iceberg Tables for automated refresh. The resulting tables are stored as Iceberg tables back in S3 via the External Volume.

```sql
CREATE DATABASE IF NOT EXISTS silver_analytics_db;
USE DATABASE silver_analytics_db;
```

#### Products Cleaning and Standardization

Creates a dynamic Iceberg table for cleaned and enhanced product data.

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE silver_analytics_db.public."de_products_cleaned"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'de_products_cleaned'
  AS
  SELECT 
    "product_id",
    "product_uuid",
    TRIM(UPPER("product_name")) as "product_name_clean",
    TRIM("description") as "product_description",
    UPPER("category") as "category_standardized",
    UPPER("subcategory") as "subcategory_standardized",
    UPPER("brand") as "brand_standardized",
    "unit_price" as "price",
    COALESCE("cost_price", 0) as "cost",
    ROUND("unit_price" - COALESCE("cost_price", 0), 2) as "profit_margin",
    CASE 
        WHEN "unit_price" - COALESCE("cost_price", 0) <= 0 THEN 'No Profit'
        WHEN ("unit_price" - COALESCE("cost_price", 0)) / NULLIF("unit_price", 0) >= 0.5 THEN 'High Margin'
        WHEN ("unit_price" - COALESCE("cost_price", 0)) / NULLIF("unit_price", 0) >= 0.3 THEN 'Medium Margin'
        ELSE 'Low Margin'
    END as "margin_tier",
    "weight_kg" as "weight",
    "dimensions_cm" as "dimensions",
    UPPER("color") as "color_standardized",
    UPPER("size") as "size_standardized",
    "material",
    "supplier_id",
    "stock_quantity",
    CASE 
        WHEN "stock_quantity" > 100 THEN 'High Stock'
        WHEN "stock_quantity" > 50 THEN 'Medium Stock'
        WHEN "stock_quantity" > 0 THEN 'Low Stock'
        ELSE 'Out of Stock'
    END as "stock_status",
    "reorder_level",
    "is_active",
    "sku",
    "barcode",
    "launch_date",
    "created_at",
    "updated_at"
FROM "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_products"
WHERE "product_id" IS NOT NULL 
  AND "product_name" IS NOT NULL;

```

#### Customers Cleaning and Standardization

Creates a dynamic Iceberg table for cleaned and enriched customer data.

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE silver_analytics_db.public."de_customers_cleaned"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'de_customers_cleaned'
  AS
  SELECT 
    "customer_id",
    "customer_uuid",
    TRIM(UPPER("first_name")) as "first_name",
    TRIM(UPPER("last_name")) as "last_name",
    LOWER(TRIM("email")) as "email",
    REGEXP_REPLACE("phone", '[^0-9]', '') as "phone_clean",
    "phone",
    "date_of_birth",
    CASE 
        WHEN "gender" IN ('M', 'Male', 'MALE', 'm') THEN 'M'
        WHEN "gender" IN ('F', 'Female', 'FEMALE', 'f') THEN 'F'
        ELSE 'O'
    END as "gender_standardized",
    "gender",
    TRIM("address_line1") as "address_line1",
    TRIM("address_line2") as "address_line2",
    TRIM(UPPER("city")) as "city",
    TRIM(UPPER("state")) as "state",
    REGEXP_REPLACE("postal_code", '[^0-9]', '') as "postal_code_clean",
    "postal_code",
    UPPER("country") as "country",
    "customer_segment",
    "registration_date",
    "last_login_date",
    COALESCE("total_orders", 0) as "total_orders",
    COALESCE("total_spent", 0) as "total_spent",
    "is_active",
    YEAR("updated_at") - YEAR("date_of_birth") as "age_approx",
    DATEDIFF('day', "registration_date", "updated_at") as "days_since_registration_approx",
    DATEDIFF('day', "last_login_date", "updated_at") as "days_since_last_login_approx",
    CASE 
        WHEN "total_spent" >= 1000 THEN 'High Value'
        WHEN "total_spent" >= 500 THEN 'Medium Value'
        ELSE 'Low Value'
    END as "value_tier",
    "created_at",
    "updated_at"
FROM "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_customers"
WHERE "email" IS NOT NULL 
  AND "email" LIKE '%@%'
  AND "customer_id" IS NOT NULL;

```

Orders and Order Items Processing. Creates dynamic Iceberg tables for cleaned orders and enriched order items.

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE silver_analytics_db.public."de_orders_cleaned"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'de_orders_cleaned'
  AS
  SELECT 
    "order_id",
    "order_uuid",
    "customer_id",
    "order_date",
    "order_status",
    CASE 
        WHEN "order_status" IN ('delivered', 'completed', 'shipped') THEN 'Fulfilled'
        WHEN "order_status" IN ('pending', 'processing', 'confirmed') THEN 'In Progress'
        WHEN "order_status" IN ('cancelled', 'refunded') THEN 'Cancelled'
        ELSE 'Other'
    END as "order_status_category",
    "total_amount",
    CASE 
        WHEN "total_amount" >= 500 THEN 'High Value'
        WHEN "total_amount" >= 200 THEN 'Medium Value'
        WHEN "total_amount" >= 50 THEN 'Low Value'
        ELSE 'Minimal Value'
    END as "order_value_tier",
    "discount_amount",
    "tax_amount",
    "shipping_cost" as "shipping_amount",
    "payment_method",
    "payment_status",
    "shipping_address",
    "billing_address",
    "shipping_method",
    "currency",
    "subtotal",
    "delivery_date" as "estimated_delivery_date",
    "shipping_date" as "actual_shipping_date",
    CASE 
        WHEN "delivery_date" IS NOT NULL AND "shipping_date" IS NOT NULL
        THEN DATEDIFF('day', "shipping_date", "delivery_date")
        ELSE NULL
    END as "estimated_delivery_days",
    CASE 
        WHEN "delivery_date" IS NOT NULL AND "shipping_date" IS NOT NULL
        THEN CASE 
            WHEN DATEDIFF('day', "shipping_date", "delivery_date") <= 3 THEN 'Fast Delivery'
            WHEN DATEDIFF('day', "shipping_date", "delivery_date") <= 7 THEN 'Standard Delivery'
            ELSE 'Slow Delivery'
        END
        ELSE 'Unknown'
    END as "delivery_speed_category",
    "notes",
    "created_at",
    "updated_at",
    EXTRACT(YEAR FROM "order_date") as "order_year",
    EXTRACT(MONTH FROM "order_date") as "order_month",
    EXTRACT(QUARTER FROM "order_date") as "order_quarter",
    DAYNAME("order_date") as "order_day_of_week"
FROM "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_orders"
WHERE "order_id" IS NOT NULL 
  AND "customer_id" IS NOT NULL
  AND "order_date" IS NOT NULL;

-- Silver Table 3: ORDER ITEMS ENRICHED
  
CREATE OR REPLACE DYNAMIC ICEBERG TABLE silver_analytics_db.public."de_order_items_enriched"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'de_order_items_enriched'
  REFRESH_MODE = INCREMENTAL
  AS
  SELECT 
    "order_item_id",
    "order_id",
    "product_id",
    "quantity",
    "unit_price",
    "line_total",
    "total_price",
    "discount_percent",
    "tax_rate",
    ("unit_price" * "quantity") as "gross_amount",
    CASE 
        WHEN "discount_percent" > 0 
        THEN ("unit_price" * "quantity" * "discount_percent" / 100)
        ELSE 0
    END as "discount_amount",
    "created_at",
    "updated_at"
FROM "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_order_items"
WHERE "order_item_id" IS NOT NULL
  AND "order_id" IS NOT NULL
  AND "product_id" IS NOT NULL;

```

Customer Order Summary. Creates a summary table by joining Bronze-layer customer and order data, calculating the sequential order number for each customer.

```sql
-- Silver Table 4: Customer Order Summary 
CREATE OR REPLACE DYNAMIC ICEBERG TABLE silver_analytics_db.public."de_customer_order_summary"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'de_customer_order_summary'
  AS
  SELECT 
    c."customer_id",
    c."customer_uuid",
    c."first_name",
    c."last_name",
    c."email",
    c."customer_segment",
    c."registration_date",
    c."total_orders",
    c."total_spent",
    c."is_active",
    c."last_login_date",
    -- Order aggregations
    o."order_id",
    o."order_date",
    o."order_status",
    o."total_amount",
    o."payment_method",
    o."payment_status",
    o."currency",
    -- Customer demographics  
    YEAR(o."order_date") - YEAR(c."date_of_birth") as "customer_age_at_order",
    c."gender" as "customer_gender",
    c."city",
    c."state",
    c."country",
    c."address_line1",
    c."address_line2",
    c."postal_code",
    c."phone",
    DATEDIFF('day', c."registration_date", o."order_date") as "days_since_registration_to_order",
    ROW_NUMBER() OVER (PARTITION BY c."customer_id" ORDER BY o."order_date") as "order_sequence",
    c."created_at" as "customer_created_at",
    o."created_at" as "order_created_at"
FROM "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_customers" c
INNER JOIN "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_orders" o 
    ON c."customer_id" = o."customer_id"
WHERE c."customer_id" IS NOT NULL 
  AND o."order_id" IS NOT NULL;

```

<!---------------------->

## Analytics


### Gold Layer Creation: Analytical Aggregations

The Gold layer creates final, denormalized tables optimized for analytical reporting.

```sql
CREATE DATABASE IF NOT EXISTS gold_analytics_db;
USE DATABASE gold_analytics_db;
```

Order Summary.A pass-through of cleaned orders with data type standardization.

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE  gold_analytics_db.public."order_summary"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'order_summary'
  REFRESH_MODE = INCREMENTAL
  AS
  SELECT 
    "order_id",
    "order_uuid",
    "customer_id",
    "order_date",
    "order_status",
    "order_status_category",
    CAST("total_amount" AS DECIMAL(18,2)) as "total_amount",
    "order_value_tier",
    CAST("discount_amount" AS DECIMAL(18,2)) as "discount_amount",
    CAST("tax_amount" AS DECIMAL(18,2)) as "tax_amount",
    CAST("shipping_amount" AS DECIMAL(18,2)) as "shipping_amount",
    "payment_method",
    "payment_status",
    "currency",
    "order_year",
    "order_month",
    "order_quarter",
    "order_day_of_week",
    "created_at",
    "updated_at"
FROM silver_analytics_db.public."de_orders_cleaned"
WHERE "order_id" IS NOT NULL 
  AND "customer_id" IS NOT NULL
  AND "order_date" IS NOT NULL;
```

Sales Summary Trends (Denormalized Fact Table). The primary analytical table, which joins all cleaned Silver entities (Orders, Items, Customers, Products, and Customer Order Summary) into a single, comprehensive view.

```sql
CREATE OR REPLACE DYNAMIC ICEBERG TABLE gold_analytics_db.public."sales_summary_trends"
  TARGET_LAG = '1 minute'
  WAREHOUSE = HOL_ICE_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'de_external_volume'
  BASE_LOCATION = 'sales_summary_trends'
  REFRESH_MODE = INCREMENTAL
  AS
  SELECT 
    -- Order information
    o."order_id",
    o."customer_id",
    o."order_date",
    o."order_status",
    o."order_status_category",
    CAST(o."total_amount" AS DECIMAL(18,2)) as "order_total_amount",
    CAST(o."discount_amount" AS DECIMAL(18,2)) as "order_discount_amount",
    o."payment_method",
    o."payment_status",
    o."currency",
    o."order_year",
    o."order_month",
    o."order_quarter",
    o."order_day_of_week",
    
    -- Order item information
    oi."order_item_id",
    oi."product_id",
    oi."quantity",
    CAST(oi."unit_price" AS DECIMAL(18,2)) as "unit_price",
    CAST(oi."total_price" AS DECIMAL(18,2)) as "item_total_price",
    CAST(oi."gross_amount" AS DECIMAL(18,2)) as "gross_amount",
    CAST(oi."discount_amount" AS DECIMAL(18,2)) as "item_discount_amount",
    
    -- Customer information
    c."customer_uuid",
    c."customer_segment",
    c."gender_standardized" as "customer_gender",
    c."city" as "customer_city",
    c."state" as "customer_state",
    c."country" as "customer_country",
    c."value_tier" as "customer_value_tier",
    CAST(c."total_spent" AS DECIMAL(18,2)) as "customer_total_spent",
    c."total_orders" as "customer_total_orders",
    
    -- Product information
    p."product_name_clean" as "product_name",
    p."category_standardized" as "product_category",
    p."subcategory_standardized" as "product_subcategory",
    p."brand_standardized" as "product_brand",
    CAST(p."price" AS DECIMAL(18,2)) as "product_price",
    CAST(p."cost" AS DECIMAL(18,2)) as "product_cost",
    p."margin_tier" as "product_margin_tier",
    p."stock_status" as "product_stock_status",
    
    -- Simple calculated fields (no aggregations)
    CAST((oi."total_price" - (oi."quantity" * COALESCE(p."cost", 0))) AS DECIMAL(18,2)) as "item_profit",
    
    -- Customer order sequence
    cos."order_sequence",
    CASE 
        WHEN cos."order_sequence" = 1 THEN 'New Customer Order'
        ELSE 'Repeat Customer Order'
    END as "customer_order_type",
    
    -- Date dimensions
    CAST(DATE_TRUNC('month', o."order_date") AS DATE) as "order_month_date",
    CAST(DATE_TRUNC('week', o."order_date") AS DATE) as "order_week_date",
    CAST(DATE_TRUNC('day', o."order_date") AS DATE) as "order_day_date",
    
    -- Status flags
    CASE WHEN o."order_status_category" = 'Fulfilled' THEN 1 ELSE 0 END as "is_fulfilled",
    CASE WHEN o."order_status_category" = 'Cancelled' THEN 1 ELSE 0 END as "is_cancelled",
    CASE WHEN o."payment_method" = 'credit_card' THEN 1 ELSE 0 END as "is_credit_card",
    CASE WHEN cos."order_sequence" = 1 THEN 1 ELSE 0 END as "is_new_customer",
    CASE WHEN c."value_tier" = 'High Value' THEN 1 ELSE 0 END as "is_high_value_customer",
    
    -- Timestamps
    o."created_at" as "order_created_at",
    oi."created_at" as "item_created_at",
    c."created_at" as "customer_created_at",
    p."created_at" as "product_created_at"
    
FROM silver_analytics_db.public."de_orders_cleaned" o
INNER JOIN silver_analytics_db.public."de_order_items_enriched" oi 
    ON o."order_id" = oi."order_id"
LEFT JOIN silver_analytics_db.public."de_customers_cleaned" c 
    ON o."customer_id" = c."customer_id"
LEFT JOIN silver_analytics_db.public."de_products_cleaned" p 
    ON oi."product_id" = p."product_id"
LEFT JOIN silver_analytics_db.public."de_customer_order_summary" cos 
    ON o."order_id" = cos."order_id"
WHERE o."order_date" IS NOT NULL
  AND oi."order_item_id" IS NOT NULL;
```

Gold Layer Verification

```sql
USE DATABASE GOLD_ANALYTICS_DB;
SHOW DYNAMIC TABLES;

```

### Incremental Load Demonstration and Verification

This section illustrates how a write to the Bronze layer in AWS automatically refreshes up the Silver and Gold layers via Dynamic Tables in Snowflake.

#### Mimic Incremental Insert into Bronze

Note: In a real scenario, an external process (like an ETL job or CDC tool or a streaming job) would write these records to S3, and the Glue Catalog would be updated. For demonstration, we simulate an INSERT into the AWS Glue managed Iceberg tables.

```sql
-- Insert 5 rows for de_orders table

INSERT INTO "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_orders"
("billing_address", "created_at", "currency", "customer_id", "delivery_date", "discount_amount", "notes", "order_date", "order_id", "order_status", "order_uuid", "payment_method", "payment_status", "shipping_address", "shipping_cost", "shipping_date", "shipping_method", "subtotal", "tax_amount", "total_amount", "updated_at")
VALUES
('123 Main St, City, State 12345', TO_TIMESTAMP_LTZ('2024-12-20 09:00:00'), 'USD', 5001, TO_TIMESTAMP_LTZ('2024-12-25 14:00:00'), 0.00, 'Standard delivery', TO_TIMESTAMP_LTZ('2024-12-20 09:00:00'), 1500048, 'confirmed', 'ORD-2024-1500048', 'credit_card', 'paid', '123 Main St, City, State 12345', 15.99, TO_TIMESTAMP_LTZ('2024-12-22 10:00:00'), 'standard', 125.99, 10.08, 151.06, TO_TIMESTAMP_LTZ('2024-12-20 09:00:00')),
('456 Oak Ave, Town, State 23456', TO_TIMESTAMP_LTZ('2024-12-20 10:30:00'), 'USD', 5002, TO_TIMESTAMP_LTZ('2024-12-25 15:30:00'), 25.00, 'Express delivery requested', TO_TIMESTAMP_LTZ('2024-12-20 10:30:00'), 1500049, 'confirmed', 'ORD-2024-1500049', 'paypal', 'paid', '456 Oak Ave, Town, State 23456', 29.99, TO_TIMESTAMP_LTZ('2024-12-21 11:00:00'), 'express', 249.99, 20.00, 274.98, TO_TIMESTAMP_LTZ('2024-12-20 10:30:00')),
('789 Pine Rd, Village, State 34567', TO_TIMESTAMP_LTZ('2024-12-20 11:15:00'), 'USD', 5003, TO_TIMESTAMP_LTZ('2024-12-26 16:15:00'), 0.00, 'Gift wrapping included', TO_TIMESTAMP_LTZ('2024-12-20 11:15:00'), 1500050, 'processing', 'ORD-2024-1500050', 'credit_card', 'paid', '789 Pine Rd, Village, State 34567', 12.99, TO_TIMESTAMP_LTZ('2024-12-23 12:00:00'), 'standard', 89.99, 7.20, 109.18, TO_TIMESTAMP_LTZ('2024-12-20 11:15:00')),
('321 Elm Dr, County, State 45678', TO_TIMESTAMP_LTZ('2024-12-20 12:45:00'), 'USD', 5004, TO_TIMESTAMP_LTZ('2024-12-27 17:45:00'), 15.00, 'Holiday special discount', TO_TIMESTAMP_LTZ('2024-12-20 12:45:00'), 1500051, 'confirmed', 'ORD-2024-1500051', 'debit_card', 'paid', '321 Elm Dr, County, State 45678', 18.99, TO_TIMESTAMP_LTZ('2024-12-22 13:30:00'), 'standard', 199.99, 16.00, 219.98, TO_TIMESTAMP_LTZ('2024-12-20 12:45:00')),
('654 Maple Ln, District, State 56789', TO_TIMESTAMP_LTZ('2024-12-20 14:20:00'), 'USD', 5005, TO_TIMESTAMP_LTZ('2024-12-28 19:20:00'), 0.00, 'Signature required', TO_TIMESTAMP_LTZ('2024-12-20 14:20:00'), 1500052, 'shipped', 'ORD-2024-1500052', 'credit_card', 'paid', '654 Maple Ln, District, State 56789', 22.99, TO_TIMESTAMP_LTZ('2024-12-21 15:00:00'), 'express', 349.99, 28.00, 400.98, TO_TIMESTAMP_LTZ('2024-12-20 14:20:00')); 
-- Insert 5 rows for de_order_items table--

INSERT INTO "GLUE_CATALOG_LINKED_DB"."bronze_analytics_db"."de_order_items"
("created_at", "discount_percent", "line_total", "order_id", "order_item_id", "product_id", "quantity", "tax_rate", "total_price", "unit_price", "updated_at")
VALUES
(TO_TIMESTAMP_LTZ('2024-12-20 09:00:00'), 0, 125.99, 1500048, 2970625, 3051, 1, 0.08, 125.99, 125.99, TO_TIMESTAMP_LTZ('2024-12-20 09:00:00')),
(TO_TIMESTAMP_LTZ('2024-12-20 10:30:00'), 10, 249.99, 1500049, 2970626, 3052, 1, 0.08, 224.99, 249.99, TO_TIMESTAMP_LTZ('2024-12-20 10:30:00')),
(TO_TIMESTAMP_LTZ('2024-12-20 10:30:00'), 0, 25.00, 1500049, 2970627, 3053, 1, 0.08, 25.00, 25.00, TO_TIMESTAMP_LTZ('2024-12-20 10:30:00')),
(TO_TIMESTAMP_LTZ('2024-12-20 11:15:00'), 0, 89.99, 1500050, 2970628, 3054, 1, 0.08, 89.99, 89.99, TO_TIMESTAMP_LTZ('2024-12-20 11:15:00')),
(TO_TIMESTAMP_LTZ('2024-12-20 12:45:00'), 10, 199.99, 1500051, 2970629, 3055, 1, 0.08, 179.99, 199.99, TO_TIMESTAMP_LTZ('2024-12-20 12:45:00')); 
```

#### Updated Layer Counts (After Dynamic Table Refresh)

After inserting the new data into the Bronze layer, wait for the Dynamic Tables to automatically refresh (configured with a TARGET_LAG of '1 minute'). Then, check the updated row counts in the downstream layers.

```sql
--- Check the updated counts in the SILVER layer based on dynamic iceberg table refresh
select count(*) from silver_analytics_db.public."de_order_items_enriched";
select count(*) from silver_analytics_db.public."de_orders_cleaned";

--Gold Layer - Check the updated counts in the GOLD layer based on dynamic iceberg table refresh
select count(*) from gold_analytics_db.public."sales_summary_trends";

```

<!-------------->

## Conclusion and Resources


This implementation successfully demonstrates a multi-layered lakehouse architecture using Snowflake Dynamic Iceberg Tables integrated with the AWS Glue Catalog.

The key takeaways from this exercise include:

**Decoupled Metadata and Data**: The Bronze Layer successfully connects Snowflake to the external Iceberg data in S3 using the Snowflake Catalog Integration and catalog linked Databases, keeping the data lake open and accessible by other engines.
**Automated Data Pipeline**: The Silver and Gold layers are powered by Snowflake Dynamic Iceberg Tables. By setting a TARGET_LAG of '1 minute' and sourcing data from the linked Bronze tables, the entire pipeline automatically processes, cleans, and transforms data as soon as new records land in the data lake.
**Incremental Efficiency**: The REFRESH_MODE = INCREMENTAL setting on key Silver and Gold tables (de_order_items_enriched, order_summary, sales_summary_trends) ensures that only the new or modified data is processed, leading to a highly efficient and low-latency data flow.
**Full CRUD/ACID Capabilities**: The ability to INSERT data directly into the Glue-managed Iceberg tables from Snowflake (as demonstrated in the incremental test ) confirms the transactional capabilities necessary for a true lakehouse architecture.

By leveraging Snowflake Dynamic Iceberg Tables, you have built a near real-time data platform that provides low-latency analytics while maintaining the flexibility and scalability of an open Iceberg data lake.

### What You Learned

So far, you learned to work with:

* Configuring Snowflake Catalog Integrations to connect to an external AWS Glue Catalog.
* Creating a Linked Database to query external Iceberg tables in the Bronze layer as if they were native Snowflake tables.
* Implementing Dynamic Iceberg Tables in the Silver and Gold layers for automated refresh (using TARGET_LAG) and write-back to the external S3 location defined by an External Volume.
* Modeling a multi-layered lakehouse: Bronze (raw data), Silver (cleaned and enhanced data), and Gold (aggregated, analytical data).
* Verifying how incremental data inserts into the Bronze layer automatically propagate through the Silver and Gold layers.

### Relevant Resources

* [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
* [Make your lakehouse AI-ready](/en/developers/solutions-center/modern-lakehouse-analytics-blueprint/)
* [Catalog Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
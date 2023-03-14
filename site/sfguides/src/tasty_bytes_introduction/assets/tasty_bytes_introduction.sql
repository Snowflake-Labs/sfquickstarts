/***************************************************************************************************
  _______           _            ____          _             
 |__   __|         | |          |  _ \        | |            
    | |  __ _  ___ | |_  _   _  | |_) | _   _ | |_  ___  ___ 
    | | / _` |/ __|| __|| | | | |  _ < | | | || __|/ _ \/ __|
    | || (_| |\__ \| |_ | |_| | | |_) || |_| || |_|  __/\__ \
    |_| \__,_||___/ \__| \__, | |____/  \__, | \__|\___||___/
                          __/ |          __/ |               
                         |___/          |___/            
Demo:         Tasty Bytes Demo
Version:      v1
Vignette:     Setup
Script:       setup_snowflake_account_blob_tb.sql         
Create Date:  2023-01-12
Author:       Jacob Kranzler
Copyright(c): 2022 Snowflake Inc. All rights reserved.
****************************************************************************************************
Description: 
   Setup for Tasty Bytes using Blob Storage
****************************************************************************************************
SUMMARY OF CHANGES
Date(yyyy-mm-dd)    Author              Comments
------------------- ------------------- ------------------------------------------------------------
2023-01-12          Jacob Kranzler      Initial Release
***************************************************************************************************/

USE ROLE sysadmin;

/*--
 • database, schema and warehouse creation
--*/

-- create frostbyte_tasty_bytes database
CREATE OR REPLACE DATABASE frostbyte_tasty_bytes;

-- create raw_pos schema
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes.raw_pos;

-- create raw_customer schema
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes.raw_customer;


-- create harmonized schema
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes.harmonized;

-- create analytics schema
CREATE OR REPLACE SCHEMA frostbyte_tasty_bytes.analytics;

-- create warehouses
CREATE OR REPLACE WAREHOUSE demo_build_wh
    WAREHOUSE_SIZE = 'xxxlarge'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'demo build warehouse for frostbyte assets';
    
CREATE OR REPLACE WAREHOUSE tasty_de_wh
    WAREHOUSE_SIZE = 'xsmall'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'data engineering warehouse for tasty bytes';

CREATE OR REPLACE WAREHOUSE tasty_ds_wh
    WAREHOUSE_SIZE = 'xsmall'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'data science warehouse for tasty bytes';

CREATE OR REPLACE WAREHOUSE tasty_bi_wh
    WAREHOUSE_SIZE = 'xsmall'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'business intelligence warehouse for tasty bytes';

CREATE OR REPLACE WAREHOUSE tasty_dev_wh
    WAREHOUSE_SIZE = 'xsmall'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'developer warehouse for tasty bytes';

CREATE OR REPLACE WAREHOUSE tasty_data_app_wh
    WAREHOUSE_SIZE = 'xsmall'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'data app warehouse for tasty bytes';

-- create roles
USE ROLE securityadmin;

-- functional roles
CREATE ROLE IF NOT EXISTS tasty_admin
    COMMENT = 'admin for tasty bytes';
    
CREATE ROLE IF NOT EXISTS tasty_data_engineer
    COMMENT = 'data engineer for tasty bytes';
      
CREATE ROLE IF NOT EXISTS tasty_data_scientist
    COMMENT = 'data scientist for tasty bytes';
    
CREATE ROLE IF NOT EXISTS tasty_bi
    COMMENT = 'business intelligence for tasty bytes';
    
CREATE ROLE IF NOT EXISTS tasty_data_app
    COMMENT = 'data application developer for tasty bytes';
    
CREATE ROLE IF NOT EXISTS tasty_dev
    COMMENT = 'developer for tasty bytes';
    

-- role hierarchy
GRANT ROLE tasty_admin TO ROLE sysadmin;
GRANT ROLE tasty_data_engineer TO ROLE tasty_admin;
GRANT ROLE tasty_data_scientist TO ROLE tasty_admin;
GRANT ROLE tasty_bi TO ROLE tasty_admin;
GRANT ROLE tasty_data_app TO ROLE tasty_admin;
GRANT ROLE tasty_dev TO ROLE tasty_data_engineer;

-- privilege grants
USE ROLE accountadmin;

GRANT EXECUTE TASK, EXECUTE MANAGED TASK ON ACCOUNT TO ROLE tasty_data_scientist;
GRANT EXECUTE TASK, EXECUTE MANAGED TASK ON ACCOUNT TO ROLE tasty_data_engineer;

GRANT IMPORTED PRIVILEGES ON DATABASE snowflake TO ROLE tasty_data_engineer;

GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE tasty_admin;

USE ROLE securityadmin;

GRANT USAGE ON DATABASE frostbyte_tasty_bytes TO ROLE tasty_admin;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes TO ROLE tasty_data_engineer;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes TO ROLE tasty_data_scientist;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes TO ROLE tasty_bi;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes TO ROLE tasty_data_app;
GRANT USAGE ON DATABASE frostbyte_tasty_bytes TO ROLE tasty_dev;

GRANT USAGE ON ALL SCHEMAS IN DATABASE frostbyte_tasty_bytes TO ROLE tasty_admin;
GRANT USAGE ON ALL SCHEMAS IN DATABASE frostbyte_tasty_bytes TO ROLE tasty_data_engineer;
GRANT USAGE ON ALL SCHEMAS IN DATABASE frostbyte_tasty_bytes TO ROLE tasty_data_scientist;
GRANT USAGE ON ALL SCHEMAS IN DATABASE frostbyte_tasty_bytes TO ROLE tasty_bi;
GRANT USAGE ON ALL SCHEMAS IN DATABASE frostbyte_tasty_bytes TO ROLE tasty_data_app;
GRANT USAGE ON ALL SCHEMAS IN DATABASE frostbyte_tasty_bytes TO ROLE tasty_dev;

GRANT ALL ON SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_admin;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_data_engineer;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_data_scientist;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_bi;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_data_app;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_dev;


GRANT ALL ON SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_admin;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_engineer;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_scientist;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_bi;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_app;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_dev;

GRANT ALL ON SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_admin;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_engineer;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_scientist;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_bi;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_app;
GRANT ALL ON SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_dev;

-- warehouse grants
GRANT ALL ON WAREHOUSE demo_build_wh TO ROLE sysadmin;

GRANT OWNERSHIP ON WAREHOUSE tasty_de_wh TO ROLE tasty_admin REVOKE CURRENT GRANTS;
GRANT ALL ON WAREHOUSE tasty_de_wh TO ROLE tasty_admin;
GRANT ALL ON WAREHOUSE tasty_de_wh TO ROLE tasty_data_engineer;

GRANT ALL ON WAREHOUSE tasty_ds_wh TO ROLE tasty_admin;
GRANT ALL ON WAREHOUSE tasty_ds_wh TO ROLE tasty_data_scientist;

GRANT ALL ON WAREHOUSE tasty_data_app_wh TO ROLE tasty_admin;
GRANT ALL ON WAREHOUSE tasty_data_app_wh TO ROLE tasty_data_app;

GRANT ALL ON WAREHOUSE tasty_bi_wh TO ROLE tasty_admin;
GRANT ALL ON WAREHOUSE tasty_bi_wh TO ROLE tasty_bi;

GRANT ALL ON WAREHOUSE tasty_dev_wh TO ROLE tasty_admin;
GRANT ALL ON WAREHOUSE tasty_dev_wh TO ROLE tasty_data_engineer;
GRANT ALL ON WAREHOUSE tasty_dev_wh TO ROLE tasty_dev;


-- future grants
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_admin;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_data_engineer;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_data_scientist;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_bi;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_data_app;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_pos TO ROLE tasty_dev;

GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_admin;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_data_engineer;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_data_scientist;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_bi;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_data_app;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_dev;


GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_admin;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_engineer;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_scientist;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_bi;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_app;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_dev;

GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_admin;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_engineer;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_scientist;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_bi;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_data_app;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.harmonized TO ROLE tasty_dev;

GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_admin;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_engineer;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_scientist;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_bi;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_app;
GRANT ALL ON FUTURE TABLES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_dev;

GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_admin;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_engineer;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_scientist;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_bi;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_app;
GRANT ALL ON FUTURE VIEWS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_dev;

GRANT ALL ON FUTURE FUNCTIONS IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_scientist;

GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_admin;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_engineer;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_scientist;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_bi;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_data_app;
GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA frostbyte_tasty_bytes.analytics TO ROLE tasty_dev;

-- Apply Masking Policy Grants
GRANT CREATE TAG ON SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_admin;
GRANT CREATE TAG ON SCHEMA frostbyte_tasty_bytes.raw_customer TO ROLE tasty_data_engineer;

USE ROLE accountadmin;
GRANT APPLY TAG ON ACCOUNT TO ROLE tasty_admin;
GRANT APPLY TAG ON ACCOUNT TO ROLE tasty_data_engineer;
GRANT APPLY MASKING POLICY ON ACCOUNT TO ROLE tasty_admin;
GRANT APPLY MASKING POLICY ON ACCOUNT TO ROLE tasty_data_engineer;
  
-- raw_pos table build
USE ROLE sysadmin;
USE WAREHOUSE demo_build_wh;

/*--
 • file format and stage creation
--*/

CREATE OR REPLACE FILE FORMAT frostbyte_tasty_bytes.public.csv_ff 
type = 'csv';

CREATE OR REPLACE STAGE frostbyte_tasty_bytes.public.s3load
COMMENT = 'Quickstarts S3 Stage Connection'
url = 's3://sfquickstarts/frostbyte_tastybytes/'
file_format = frostbyte_tasty_bytes.public.csv_ff;

/*--
 raw zone table build 
--*/

-- country table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.country
(
    country_id NUMBER(18,0),
    country VARCHAR(16777216),
    iso_currency VARCHAR(3),
    iso_country VARCHAR(2),
    city_id NUMBER(19,0),
    city VARCHAR(16777216),
    city_population VARCHAR(16777216)
);

-- franchise table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.franchise 
(
    franchise_id NUMBER(38,0),
    first_name VARCHAR(16777216),
    last_name VARCHAR(16777216),
    city VARCHAR(16777216),
    country VARCHAR(16777216),
    e_mail VARCHAR(16777216),
    phone_number VARCHAR(16777216) 
);

-- location table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.location
(
    location_id NUMBER(19,0),
    placekey VARCHAR(16777216),
    location VARCHAR(16777216),
    city VARCHAR(16777216),
    region VARCHAR(16777216),
    iso_country_code VARCHAR(16777216),
    country VARCHAR(16777216)
);

-- menu table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.menu
(
    menu_id NUMBER(19,0),
    menu_type_id NUMBER(38,0),
    menu_type VARCHAR(16777216),
    truck_brand_name VARCHAR(16777216),
    menu_item_id NUMBER(38,0),
    menu_item_name VARCHAR(16777216),
    item_category VARCHAR(16777216),
    item_subcategory VARCHAR(16777216),
    cost_of_goods_usd NUMBER(38,4),
    sale_price_usd NUMBER(38,4),
    menu_item_health_metrics_obj VARIANT
);

-- truck table build 
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.truck
(
    truck_id NUMBER(38,0),
    menu_type_id NUMBER(38,0),
    primary_city VARCHAR(16777216),
    region VARCHAR(16777216),
    iso_region VARCHAR(16777216),
    country VARCHAR(16777216),
    iso_country_code VARCHAR(16777216),
    franchise_flag NUMBER(38,0),
    year NUMBER(38,0),
    make VARCHAR(16777216),
    model VARCHAR(16777216),
    ev_flag NUMBER(38,0),
    franchise_id NUMBER(38,0),
    truck_opening_date DATE
);

-- order_header table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.order_header
(
    order_id NUMBER(38,0),
    truck_id NUMBER(38,0),
    location_id FLOAT,
    customer_id NUMBER(38,0),
    discount_id VARCHAR(16777216),
    shift_id NUMBER(38,0),
    shift_start_time TIME(9),
    shift_end_time TIME(9),
    order_channel VARCHAR(16777216),
    order_ts TIMESTAMP_NTZ(9),
    served_ts VARCHAR(16777216),
    order_currency VARCHAR(3),
    order_amount NUMBER(38,4),
    order_tax_amount VARCHAR(16777216),
    order_discount_amount VARCHAR(16777216),
    order_total NUMBER(38,4)
);

-- order_detail table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_pos.order_detail 
(
    order_detail_id NUMBER(38,0),
    order_id NUMBER(38,0),
    menu_item_id NUMBER(38,0),
    discount_id VARCHAR(16777216),
    line_number NUMBER(38,0),
    quantity NUMBER(5,0),
    unit_price NUMBER(38,4),
    price NUMBER(38,4),
    order_item_discount_amount VARCHAR(16777216)
);

-- customer loyalty table build
CREATE OR REPLACE TABLE frostbyte_tasty_bytes.raw_customer.customer_loyalty
(
    customer_id NUMBER(38,0),
    first_name VARCHAR(16777216),
    last_name VARCHAR(16777216),
    city VARCHAR(16777216),
    country VARCHAR(16777216),
    postal_code VARCHAR(16777216),
    preferred_language VARCHAR(16777216),
    gender VARCHAR(16777216),
    favourite_brand VARCHAR(16777216),
    marital_status VARCHAR(16777216),
    children_count VARCHAR(16777216),
    sign_up_date DATE,
    birthday_date DATE,
    e_mail VARCHAR(16777216),
    phone_number VARCHAR(16777216)
);

/*--
 • harmonized view creation
--*/

-- orders_v view
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.harmonized.orders_v
    AS
SELECT 
    oh.order_id,
    oh.truck_id,
    oh.order_ts,
    od.order_detail_id,
    od.line_number,
    m.truck_brand_name,
    m.menu_type,
    t.primary_city,
    t.region,
    t.country,
    t.franchise_flag,
    t.franchise_id,
    f.first_name AS franchisee_first_name,
    f.last_name AS franchisee_last_name,
    l.location_id,
    cl.customer_id,
    cl.first_name,
    cl.last_name,
    cl.e_mail,
    cl.phone_number,
    cl.children_count,
    cl.gender,
    cl.marital_status,
    od.menu_item_id,
    m.menu_item_name,
    od.quantity,
    od.unit_price,
    od.price,
    oh.order_amount,
    oh.order_tax_amount,
    oh.order_discount_amount,
    oh.order_total
FROM frostbyte_tasty_bytes.raw_pos.order_detail od
JOIN frostbyte_tasty_bytes.raw_pos.order_header oh
    ON od.order_id = oh.order_id
JOIN frostbyte_tasty_bytes.raw_pos.truck t
    ON oh.truck_id = t.truck_id
JOIN frostbyte_tasty_bytes.raw_pos.menu m
    ON od.menu_item_id = m.menu_item_id
JOIN frostbyte_tasty_bytes.raw_pos.franchise f
    ON t.franchise_id = f.franchise_id
JOIN frostbyte_tasty_bytes.raw_pos.location l
    ON oh.location_id = l.location_id
LEFT JOIN frostbyte_tasty_bytes.raw_customer.customer_loyalty cl
    ON oh.customer_id = cl.customer_id;

-- loyalty_metrics_v view
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.harmonized.customer_loyalty_metrics_v
    AS
SELECT 
    cl.customer_id,
    cl.city,
    cl.country,
    cl.first_name,
    cl.last_name,
    cl.phone_number,
    cl.e_mail,
    SUM(oh.order_total) AS total_sales,
    ARRAY_AGG(DISTINCT oh.location_id) AS visited_location_ids_array
FROM frostbyte_tasty_bytes.raw_customer.customer_loyalty cl
JOIN frostbyte_tasty_bytes.raw_pos.order_header oh
ON cl.customer_id = oh.customer_id
GROUP BY cl.customer_id, cl.city, cl.country, cl.first_name,
cl.last_name, cl.phone_number, cl.e_mail;


/*-- This is used in Snowpark 101 but not needed in Z2S - removing as this is dependent on Safegraph
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.harmonized.location_detail_v
  AS
WITH _location_point AS
(SELECT 
    cpg.placekey,
    l.location_id,
    cpg.city,
    cpg.country,
    ST_MAKEPOINT(cpg.longitude, cpg.latitude) AS geo_point
FROM frostbyte_tasty_bytes.raw_safegraph.core_poi_geometry cpg
LEFT JOIN frostbyte_tasty_bytes.raw_pos.location l
    ON cpg.placekey = l.placekey),
_distance_between_locations AS
(SELECT 
    a.placekey,
    a.location_id,
    b.placekey AS placekey_2,
    b.location_id AS location_id_2,
    a.city,
    a.country,
    ROUND(ST_DISTANCE(a.geo_point, b.geo_point)/1609,2) AS geography_distance_miles
FROM _location_point a
JOIN _location_point b
    ON a.city = b.city
    AND a.country = b.country
    AND a.placekey <> b.placekey
),
_locations_within_half_mile AS
(
SELECT
    dbl.placekey,
    dbl.location_id,
    COUNT(DISTINCT dbl.placekey_2) AS count_locations_within_half_mile
FROM _distance_between_locations dbl
WHERE dbl.geography_distance_miles <= 0.5
GROUP BY dbl.location_id, dbl.placekey
),
_locations_within_mile AS
(
SELECT
    dbl.placekey,
    dbl.location_id,
    COUNT(DISTINCT dbl.placekey_2) AS count_locations_within_mile
FROM _distance_between_locations dbl
WHERE dbl.geography_distance_miles <= 1
GROUP BY dbl.location_id, dbl.placekey
)
SELECT
    l.location_id,
    ZEROIFNULL(hm.count_locations_within_half_mile) AS count_locations_within_half_mile,
    ZEROIFNULL(m.count_locations_within_mile) AS count_locations_within_mile,
    cpg.placekey,
    cpg.location_name,
    cpg.top_category,
    cpg.sub_category,
    cpg.naics_code,
    cpg.latitude,
    cpg.longitude,
    ST_MAKEPOINT(cpg.longitude, cpg.latitude) AS geo_point,
    cpg.street_address,
    cpg.city,
    c.city_population,
    cpg.region,
    cpg.country,
    cpg.polygon_wkt,
    cpg.geometry_type
FROM frostbyte_tasty_bytes.raw_pos.location l
JOIN frostbyte_tasty_bytes.raw_safegraph.core_poi_geometry cpg
    ON l.placekey = cpg.placekey
JOIN frostbyte_tasty_bytes.raw_pos.country c
    ON l.city = c.city
LEFT JOIN _locations_within_half_mile hm
    ON l.location_id = hm.location_id
LEFT JOIN _locations_within_mile m
    ON l.location_id = m.location_id;

CREATE OR REPLACE VIEW frostbyte_tasty_bytes.analytics.location_detail_v
COMMENT = 'Tasty Bytes Truck Location Details View'
  AS
SELECT * FROM frostbyte_tasty_bytes.harmonized.location_detail_v;
--*/ 


/*--
 • analytics view creation
--*/

-- orders_v view
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.analytics.orders_v
COMMENT = 'Tasty Bytes Order Detail View'
    AS
SELECT DATE(o.order_ts) AS date, * FROM frostbyte_tasty_bytes.harmonized.orders_v o;
-- customer_loyalty_metrics_v view

CREATE OR REPLACE VIEW frostbyte_tasty_bytes.analytics.customer_loyalty_metrics_v
COMMENT = 'Tasty Bytes Customer Loyalty Member Metrics View'
    AS
SELECT * FROM frostbyte_tasty_bytes.harmonized.customer_loyalty_metrics_v;


/*-- Removing as this is not used in Z2S
-- snowpark stored procedure creation 
CREATE OR REPLACE PROCEDURE frostbyte_tasty_bytes.analytics.build_ds_table()
    RETURNS STRING
    LANGUAGE PYTHON
    RUNTIME_VERSION = '3.8'
    PACKAGES = ('snowflake-snowpark-python')
    HANDLER = 'create_table'
AS
$$
def create_table(session):
    import snowflake.snowpark.functions as F
    import snowflake.snowpark.types as T
    df = session.table("frostbyte_tasty_bytes.analytics.orders_v") \
            .select("order_id",
                    "truck_id",
                    "location_id",
                    F.col("primary_city").alias("city"),
                    "latitude",
                    "longitude",
                    F.builtin("DATE")(F.col("order_ts")).alias("date"),
                    F.iff(F.builtin("DATE_PART")("HOUR",F.col("order_ts")) < '15',
                          'AM', 'PM').alias("shift"),
                    F.cast(F.col("order_total"), T.FloatType()).alias("order_total"),
                    ) \
            .distinct() \
            .group_by("truck_id", "location_id", "date", 
            "city", "latitude", "longitude", "shift") \
            .agg(F.sum("order_total").alias('shift_sales')) \
            .select("location_id",
                 "city",
                 "date",
                 "shift_sales",
                 "shift",
                 F.month(F.col("date")).alias("month"),
                 F.dayofweek(F.col("date")).alias("day_of_week"),
                 "latitude",
                 "longitude")
                 
    df_poi = session.table("frostbyte_tasty_bytes.analytics.location_detail_v") \
                .select("location_id",
                        "count_locations_within_half_mile",
                        "city_population")
                        
    df = df.join(df_poi, df.location_id == df_poi.location_id, "LEFT") \
            .rename(df.location_id, "location_id") \
            .drop(df_poi.location_id)
    
    max_date = df.select(F.max(F.col("date"))).collect()[0][0]
    df_future = df.select("LOCATION_ID",
                          "CITY", 
                          F.lit(None).astype(T.DoubleType()).alias("SHIFT_SALES"),
                          "SHIFT",
                          "LATITUDE",
                          "LONGITUDE",
                          "COUNT_LOCATIONS_WITHIN_HALF_MILE",
                          "CITY_POPULATION").distinct()

    df_future_dates = df.select(F.dateadd("day", F.lit(7), F.col("DATE")).alias("NEW_DATE"),
                              F.month(F.dateadd("day", F.lit(7), F.col("DATE"))).alias("month"),
                              F.dayofweek(F.dateadd("day", F.lit(7), F.col("DATE"))).alias("day_of_week"),      
                              ) \
                             .rename(F.col("NEW_DATE"), "DATE") \
                             .where(F.col("DATE") > max_date).distinct()
    df_future = df_future.cross_join(df_future_dates)
    
    df = df_future.union_all_by_name(df).select('LOCATION_ID',
                                                         'CITY',
                                                         'DATE',
                                                         'SHIFT_SALES',
                                                         'SHIFT',
                                                         'MONTH',
                                                         'DAY_OF_WEEK',
                                                         'LATITUDE',
                                                         'LONGITUDE',
                                                         'COUNT_LOCATIONS_WITHIN_HALF_MILE',
                                                         'CITY_POPULATION')  
    df.write.mode("overwrite").save_as_table("frostbyte_tasty_bytes.analytics.shift_sales")
                                                                  
    return "SUCCESS"
$$;


-- call snowpark stored procedure to generate shift_sales table
CALL frostbyte_tasty_bytes.analytics.build_ds_table();

--*/

/*--
 raw zone table load 
--*/

-- country table load
COPY INTO frostbyte_tasty_bytes.raw_pos.country
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/country/;

-- franchise table load
COPY INTO frostbyte_tasty_bytes.raw_pos.franchise
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/franchise/;

-- location table load
COPY INTO frostbyte_tasty_bytes.raw_pos.location
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/location/;

-- menu table load
COPY INTO frostbyte_tasty_bytes.raw_pos.menu
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/menu/;

-- truck table load
COPY INTO frostbyte_tasty_bytes.raw_pos.truck
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/truck/;

-- customer_loyalty table load
COPY INTO frostbyte_tasty_bytes.raw_customer.customer_loyalty
FROM @frostbyte_tasty_bytes.public.s3load/raw_customer/customer_loyalty/;


-- order_header table load
COPY INTO frostbyte_tasty_bytes.raw_pos.order_header
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/order_header/;

-- order_detail table load
COPY INTO frostbyte_tasty_bytes.raw_pos.order_detail
FROM @frostbyte_tasty_bytes.public.s3load/raw_pos/order_detail/;

-- drop demo_build_wh
DROP WAREHOUSE IF EXISTS demo_build_wh;

-- setup completion note
SELECT 'frostbyte_tasty_bytes setup database is now complete' AS note;
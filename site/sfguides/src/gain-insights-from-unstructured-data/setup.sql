USE ROLE sysadmin;

/*--
• database, schema and warehouse creation
--*/

-- create tb_voc database
CREATE OR REPLACE DATABASE tb_voc;

-- create raw_pos schema
CREATE OR REPLACE SCHEMA tb_voc.raw_pos;

-- create raw_customer schema
CREATE OR REPLACE SCHEMA tb_voc.raw_support;

-- create harmonized schema
CREATE OR REPLACE SCHEMA tb_voc.harmonized;

-- create analytics schema
CREATE OR REPLACE SCHEMA tb_voc.analytics;

-- create media schema
CREATE OR REPLACE SCHEMA tb_voc.media;

-- create warehouse for ingestion
CREATE OR REPLACE WAREHOUSE demo_build_wh
    WAREHOUSE_SIZE = 'xlarge'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

/*--
• file format and stage creation
--*/

CREATE OR REPLACE FILE FORMAT tb_voc.public.csv_ff 
type = 'csv';

CREATE OR REPLACE STAGE tb_voc.public.s3load
COMMENT = 'Quickstarts S3 Stage Connection'
url = 's3://sfquickstarts/tastybytes-voc/'
file_format = tb_voc.public.csv_ff;

/*--
raw zone table build 
--*/

-- menu table build
CREATE OR REPLACE TABLE tb_voc.raw_pos.menu
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
CREATE OR REPLACE TABLE tb_voc.raw_pos.truck
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
CREATE OR REPLACE TABLE tb_voc.raw_pos.order_header
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

-- truck_reviews table build
CREATE OR REPLACE TABLE tb_voc.raw_support.truck_reviews
(
    order_id NUMBER(38,0),
    language VARCHAR(16777216),
    source VARCHAR(16777216),
    review VARCHAR(16777216),
    review_id NUMBER(18,0)
);

/*--
• harmonized view creation
--*/

-- truck_reviews_v view
CREATE OR REPLACE VIEW tb_voc.harmonized.truck_reviews_v
    AS
SELECT DISTINCT
    r.review_id,
    r.order_id,
    oh.truck_id,
    r.language,
    source,
    r.review,
    t.primary_city,
    oh.customer_id,
    TO_DATE(oh.order_ts) AS date,
    m.truck_brand_name
FROM tb_voc.raw_support.truck_reviews r
JOIN tb_voc.raw_pos.order_header oh
    ON oh.order_id = r.order_id
JOIN tb_voc.raw_pos.truck t
    ON t.truck_id = oh.truck_id
JOIN tb_voc.raw_pos.menu m
    ON m.menu_type_id = t.menu_type_id;

/*--
• analytics view creation
--*/

-- truck_reviews_v view
CREATE OR REPLACE VIEW tb_voc.analytics.truck_reviews_v
    AS
SELECT * FROM harmonized.truck_reviews_v;

CREATE OR REPLACE VIEW TB_VOC.ANALYTICS.TRUCK_REVIEWS_V_SAMPLE AS
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY TRUCK_BRAND_NAME ORDER BY
                CASE WHEN
                    LANGUAGE = 'en' THEN 0 ELSE 1 END,
            RANDOM()
        ) AS rn
    FROM TB_VOC.ANALYTICS.TRUCK_REVIEWS_V
)
SELECT * EXCLUDE rn
FROM ranked
WHERE rn <= 7;


/*--
raw zone table load 
--*/

USE WAREHOUSE demo_build_wh;

-- menu table load
COPY INTO tb_voc.raw_pos.menu
FROM @tb_voc.public.s3load/raw_pos/menu/;

-- truck table load
COPY INTO tb_voc.raw_pos.truck
FROM @tb_voc.public.s3load/raw_pos/truck/;

-- order_header table load
COPY INTO tb_voc.raw_pos.order_header
FROM @tb_voc.public.s3load/raw_pos/order_header/;

-- truck_reviews table load
COPY INTO tb_voc.raw_support.truck_reviews
FROM @tb_voc.public.s3load/raw_support/truck_reviews/;

USE SCHEMA tb_voc.analytics;

CREATE OR REPLACE TABLE CONCATENATED_REVIEWS AS
WITH RANKED_REVIEWS AS (
    SELECT 
        TRUCK_BRAND_NAME,
        REVIEW,
        ROW_NUMBER() OVER (PARTITION BY TRUCK_BRAND_NAME ORDER BY REVIEW) AS ROW_NUM
    FROM TRUCK_REVIEWS_V
),
FILTERED_REVIEWS AS (
    SELECT *
    FROM RANKED_REVIEWS
    WHERE ROW_NUM <= 20
),
AGGREGATED_REVIEWS AS (
    SELECT 
        TRUCK_BRAND_NAME,
        ARRAY_AGG(REVIEW) AS ALL_REVIEWS
    FROM FILTERED_REVIEWS
    GROUP BY TRUCK_BRAND_NAME
),
CONCATENATED_REVIEWS AS (
    SELECT 
        TRUCK_BRAND_NAME,
        ARRAY_TO_STRING(ALL_REVIEWS, ' ') AS ALL_REVIEWS_TEXT
    FROM AGGREGATED_REVIEWS
)

SELECT * FROM CONCATENATED_REVIEWS;

/*--
• media stage creation (images, audio, video)
--*/

-- Create image storage stage
CREATE STAGE IF NOT EXISTS tb_voc.MEDIA.IMAGES
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = true);

-- Create audio storage stage  
CREATE STAGE IF NOT EXISTS tb_voc.MEDIA.AUDIO
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = true);

-- Create video storage stage
CREATE STAGE IF NOT EXISTS tb_voc.MEDIA.VIDEO
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = true);

-- Create media reference tables
CREATE OR REPLACE TABLE tb_voc.MEDIA.IMAGE_TABLE (
    IMAGE_PATH VARCHAR,
    UPLOAD_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE tb_voc.MEDIA.AUDIO_TABLE (
    AUDIO_PATH VARCHAR,
    UPLOAD_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE tb_voc.MEDIA.VIDEO_TABLE (
    VIDEO_PATH VARCHAR,
    UPLOAD_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

/*--
• AI Function Studio: Evaluation Data
  Labeled dataset for evaluating the EXTRACT_REVIEW_FIELDS custom AI function.
  Contains manually verified extractions for 20 sample reviews.
--*/

USE SCHEMA tb_voc.analytics;

CREATE OR REPLACE TABLE tb_voc.analytics.EXTRACTION_EVAL_DATA (
    REVIEW_TEXT VARCHAR,
    EXPECTED_OUTPUT VARIANT
);

INSERT INTO TB_VOC.ANALYTICS.EXTRACTION_EVAL_DATA (REVIEW_TEXT, EXPECTED_OUTPUT)
SELECT 'I went to Freezing Point and the mango sticky rice ice cream was incredible. Will definitely recommend to friends!',
       PARSE_JSON('{"truck_name": "Freezing Point", "dish_mentioned": "mango sticky rice ice cream", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'The Noodle Neck truck had a 45-minute wait and when we finally got our ramen, it was lukewarm. Disappointing.',
       PARSE_JSON('{"truck_name": "Noodle Neck", "dish_mentioned": "ramen", "issue_type": "wait time", "would_recommend": "no"}')
UNION ALL SELECT 'Kitakata Ramen Bar never disappoints. The tonkotsu was rich and flavorful as always.',
       PARSE_JSON('{"truck_name": "Kitakata Ramen Bar", "dish_mentioned": "tonkotsu", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'The Cheeky Greek gyro was dry and overcooked. Service was rude too. Would not go back.',
       PARSE_JSON('{"truck_name": "The Cheeky Greek", "dish_mentioned": "gyro", "issue_type": "food quality", "would_recommend": "no"}')
UNION ALL SELECT 'Peking Truck makes the best dumplings in the city. Quick service and always fresh.',
       PARSE_JSON('{"truck_name": "Peking Truck", "dish_mentioned": "dumplings", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'I tried the Le Coin des Crepes truck today. The Nutella crepe was good but the truck area was dirty.',
       PARSE_JSON('{"truck_name": "Le Coin des Crepes", "dish_mentioned": "Nutella crepe", "issue_type": "cleanliness", "would_recommend": "unclear"}')
UNION ALL SELECT 'Smoky BBQ Bros brisket sandwich was phenomenal. Perfectly smoked, great sauce.',
       PARSE_JSON('{"truck_name": "Smoky BBQ Bros", "dish_mentioned": "brisket sandwich", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'The Guac n Roll burrito bowl was mediocre. Nothing special about it honestly.',
       PARSE_JSON('{"truck_name": "Guac n Roll", "dish_mentioned": "burrito bowl", "issue_type": "food quality", "would_recommend": "unclear"}')
UNION ALL SELECT 'Plant Palace vegan burger was surprisingly good! Fast service too.',
       PARSE_JSON('{"truck_name": "Plant Palace", "dish_mentioned": "vegan burger", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'Waited 30 minutes at Tasty Tacos only to be told they were out of carnitas. Terrible planning.',
       PARSE_JSON('{"truck_name": "Tasty Tacos", "dish_mentioned": "carnitas", "issue_type": "wait time", "would_recommend": "no"}')
UNION ALL SELECT 'The lobster roll from Lobster Landing was fresh and buttery. A bit pricey but worth it.',
       PARSE_JSON('{"truck_name": "Lobster Landing", "dish_mentioned": "lobster roll", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'Bangkok Bites pad thai was way too sweet. Not authentic at all.',
       PARSE_JSON('{"truck_name": "Bangkok Bites", "dish_mentioned": "pad thai", "issue_type": "food quality", "would_recommend": "no"}')
UNION ALL SELECT 'I love the Freezing Point matcha soft serve. Perfect on a hot day!',
       PARSE_JSON('{"truck_name": "Freezing Point", "dish_mentioned": "matcha soft serve", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'The staff at Noodle Neck were incredibly friendly and helpful despite the long line.',
       PARSE_JSON('{"truck_name": "Noodle Neck", "dish_mentioned": null, "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'Peking Truck spring rolls were soggy and clearly not fresh. Very disappointed.',
       PARSE_JSON('{"truck_name": "Peking Truck", "dish_mentioned": "spring rolls", "issue_type": "food quality", "would_recommend": "no"}')
UNION ALL SELECT 'Had the fish tacos from Baja Fresh Truck. Decent but nothing to write home about.',
       PARSE_JSON('{"truck_name": "Baja Fresh Truck", "dish_mentioned": "fish tacos", "issue_type": "none", "would_recommend": "unclear"}')
UNION ALL SELECT 'Kitakata Ramen Bar miso ramen is my go-to comfort food. Consistent quality every time.',
       PARSE_JSON('{"truck_name": "Kitakata Ramen Bar", "dish_mentioned": "miso ramen", "issue_type": "none", "would_recommend": "yes"}')
UNION ALL SELECT 'The Cheeky Greek falafel wrap had great flavor but the portion was tiny for the price.',
       PARSE_JSON('{"truck_name": "The Cheeky Greek", "dish_mentioned": "falafel wrap", "issue_type": "service", "would_recommend": "unclear"}')
UNION ALL SELECT 'Smoky BBQ Bros pulled pork was dry and tasteless. Major letdown from their usual quality.',
       PARSE_JSON('{"truck_name": "Smoky BBQ Bros", "dish_mentioned": "pulled pork", "issue_type": "food quality", "would_recommend": "no"}')
UNION ALL SELECT 'Le Coin des Crepes savory ham and cheese crepe is the best lunch option downtown. Quick and delicious!',
       PARSE_JSON('{"truck_name": "Le Coin des Crepes", "dish_mentioned": "ham and cheese crepe", "issue_type": "none", "would_recommend": "yes"}');

/*--
• cross-region inference and cleanup
--*/

ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

DROP WAREHOUSE demo_build_wh;

-- setup completion note
SELECT 'Setup is complete. Upload media files to stages, then uncomment and run the post-upload section above.' AS note;

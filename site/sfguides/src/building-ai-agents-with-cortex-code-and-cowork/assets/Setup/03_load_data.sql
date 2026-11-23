/*=============================================================
  HOL_COCO_COWORK - Step 3: Load Data
  Loads CSV data from stage into tables.
  
  Run this in a SQL cell AFTER 02_copy_files.py has completed.
=============================================================*/

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE HOL_WH;
USE DATABASE HOL_COCO_COWORK;
USE SCHEMA DATA;

--------------------------------------------------------------
-- 1. Load Dimension Tables
--    ID columns are omitted; UUID_STRING() default fires.
--------------------------------------------------------------
COPY INTO DIM_STORE (STORE_NAME, ADDRESS, CITY, STATE, ZIP_CODE, LATITUDE, LONGITUDE, OPENED_DATE)
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8
    FROM @HOL_STAGE/dim_store
)
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';

COPY INTO DIM_ITEM (ITEM_NAME, CATEGORY, UNIT_PRICE, COST_PRICE, CALORIES, IS_SPICY)
FROM (
    SELECT $1, $2, $3, $4, $5, $6
    FROM @HOL_STAGE/dim_item
)
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';

--------------------------------------------------------------
-- 2. Load Fact Table via staging table + JOIN on natural keys
--------------------------------------------------------------
CREATE OR REPLACE TEMPORARY TABLE STG_FACT_ITEM_SALES (
    STORE_NAME     VARCHAR(100),
    ITEM_NAME      VARCHAR(200),
    SALE_DATE      DATE,
    QUANTITY_SOLD  INTEGER,
    UNIT_PRICE     NUMBER(10,2),
    DISCOUNT_PCT   INTEGER,
    TOTAL_SALES    NUMBER(12,2)
);

COPY INTO STG_FACT_ITEM_SALES
FROM @HOL_STAGE/fact_item_sales
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'CONTINUE';

INSERT INTO FACT_ITEM_SALES (STORE_ID, ITEM_ID, SALE_DATE, QUANTITY_SOLD, UNIT_PRICE, DISCOUNT_PCT, TOTAL_SALES)
SELECT
    s.STORE_ID,
    i.ITEM_ID,
    stg.SALE_DATE,
    stg.QUANTITY_SOLD,
    stg.UNIT_PRICE,
    stg.DISCOUNT_PCT,
    stg.TOTAL_SALES
FROM STG_FACT_ITEM_SALES stg
JOIN DIM_STORE s ON s.STORE_NAME = stg.STORE_NAME
JOIN DIM_ITEM i ON i.ITEM_NAME = stg.ITEM_NAME;

DROP TABLE IF EXISTS STG_FACT_ITEM_SALES;

--------------------------------------------------------------
-- 3. Verify Load
--------------------------------------------------------------
SELECT 'DIM_STORE' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM DIM_STORE
UNION ALL
SELECT 'DIM_ITEM', COUNT(*) FROM DIM_ITEM
UNION ALL
SELECT 'FACT_ITEM_SALES', COUNT(*) FROM FACT_ITEM_SALES;

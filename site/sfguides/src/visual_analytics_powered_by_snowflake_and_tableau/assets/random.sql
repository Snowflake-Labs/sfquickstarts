USE DATABASE frostbyte_tasty_bytes;
USE SCHEMA raw_pos;

-- SELECT served_ts, dateadd(month,26,served_ts) as new_date FROM ORDER_HEADER order by  new_date desc limit 10;

UPDATE order_header SET order_ts = dateadd(month,26,order_ts); 

USE SCHEMA RAW_CUSTOMER;
SELECT 
       SPLIT_PART(METADATA$FILENAME, '/', 4) as source_name,
       CONCAT(SPLIT_PART(METADATA$FILENAME, '/', 2),'/' ,SPLIT_PART(METADATA$FILENAME, '/', 3)) as quarter,
       $1 as order_id,
       $2 as truck_id,
       $3 as language,
       $5 as review,
       $6 as primary_city, 
       $7 as customer_id,
       $8 as year,
       $9 as month,
       $10 as truck_brand,
      DATEADD(month,-UNIFORM(0,6,RANDOM()),CURRENT_DATE()) as review_date
FROM @stg_truck_reviews 
(FILE_FORMAT => 'FF_CSV',
PATTERN => '.*reviews.*[.]csv') 
WHERE YEAR = '2022'
limit 100;
/*-------------------------------------------------------------------------------------------------------------------
-- </VHOL SQL - this is to be run in the Reader Account>
-- <Visual Analytics  Powered by Snowflake and Tableau>
-- <May 5, 2022 | 11:00am PST>
-- <SQL File |Chandra Nayak>
-- <Sales Engineer | Snowflake>
--  SQL: https://snowflake-workshop-lab.s3.amazonaws.com/citibike-trips/reader_query.sql
-------------------------------------------------------------------------------------------------------------------*/
-- create database from share in the reader account  
create or replace warehouse VHOL_READER WITH 
    WAREHOUSE_SIZE = 'XSMALL' 
    WAREHOUSE_TYPE = 'STANDARD' 
    AUTO_SUSPEND = 60 
    AUTO_RESUME = TRUE 
    MIN_CLUSTER_COUNT = 1 
    MAX_CLUSTER_COUNT = 1 
    SCALING_POLICY = 'STANDARD';
show shares like 'VHOL_SHARE%';
select  "name" FROM table (result_scan(last_query_id()));


-- replace the share name with the name from above query
CREATE OR REPLACE DATABASE TRIPSDB FROM SHARE LKA85298.VHOL_SHARE;


USE DATABASE TRIPSDB;
USE SCHEMA VHOL_SCHEMA; 

SELECT * FROM VHOL_SCHEMA.VHOL_TRIPS_SECURE;
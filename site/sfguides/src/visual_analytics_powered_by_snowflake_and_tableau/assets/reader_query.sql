/*-------------------------------------------------------------------------------------------------------------------
-- </VHOL SQL - this is to be run in the Reader Account>
-------------------------------------------------------------------------------------------------------------------*/
CREATE DATABASE TRIPSDB FROM SHARE 
create or replace warehouse VHOL_READER WITH 
    WAREHOUSE_SIZE = 'XSMALL' 
    WAREHOUSE_TYPE = 'STANDARD' 
    AUTO_SUSPEND = 60 
    AUTO_RESUME = TRUE 
    MIN_CLUSTER_COUNT = 1 
    MAX_CLUSTER_COUNT = 1 
    SCALING_POLICY = 'STANDARD';
    

    

USE DB TRIPSDB
USE SCHEMA VHOL_SCHEMA; 

SELECT * FROM VHOL_SCHEMA.VHOL_TRIPS_SECURE;
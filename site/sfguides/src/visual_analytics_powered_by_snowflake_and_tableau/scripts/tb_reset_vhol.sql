/**********************************************************************/
/*------               Quickstart Reset Scripts                 ------*/
/*------   These can be run to reset your account to a state    ------*/
/*----- that will allow you to run through this Quickstart again -----*/
/**********************************************************************/

USE ROLE accountadmin;

DROP FUNCTION IF EXISTS frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(NUMBER(35,4));
DROP FUNCTION IF EXISTS frostbyte_tasty_bytes.analytics.inch_to_millimeter(NUMBER(35,4));

--USE ROLE sysdmin;
DROP DATABASE IF EXISTS frostbyte_tasty_bytes;   
DROP DATABASE IF EXISTS frostbyte_weathersource;
DROP WAREHOUSE IF EXISTS demo_build_wh; 
DROP WAREHOUSE IF EXISTS tasty_de_wh;
DROP WAREHOUSE IF EXISTS tasty_bi_wh;
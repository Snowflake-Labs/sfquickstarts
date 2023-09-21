USE ROLE accountadmin;

DROP WAREHOUSE IF EXISTS demo_build_wh; 

/**********************************************************************/
/*------               Quickstart Reset Scripts                 ------*/
/*------   These can be run to reset your account to a state    ------*/
/*----- that will allow you to run through this Quickstart again -----*/
/**********************************************************************/

USE ROLE accountadmin;

DROP VIEW IF EXISTS frostbyte_tasty_bytes.harmonized.daily_weather_v;
DROP VIEW IF EXISTS frostbyte_tasty_bytes.analytics.daily_city_metrics_v;

DROP DATABASE IF EXISTS frostbyte_weathersource;

DROP FUNCTION IF EXISTS frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(NUMBER(35,4));
DROP FUNCTION IF EXISTS frostbyte_tasty_bytes.analytics.inch_to_millimeter(NUMBER(35,4));

/**********************************************************************/
/*------               Quickstart Reset Scripts                 ------*/
/*------   These can be ran to reset your account to a state    ------*/
/*----- that will allow you to run through this Quickstart again -----*/
/**********************************************************************/

UNSET center_point;

--USE ROLE sysdmin;


DROP DATABASE IF EXISTS frostbyte_safegraph;
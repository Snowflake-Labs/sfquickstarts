-- Snow Bear Fan Experience Analytics - Initial Setup Script
-- Run this script BEFORE using the notebook
-- This creates the database, schemas, role, warehouse, stage, and grants permissions

USE ROLE accountadmin;

-- Create Snow Bear database and schemas
CREATE DATABASE IF NOT EXISTS CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB;
USE DATABASE CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB;
CREATE SCHEMA IF NOT EXISTS BRONZE_LAYER;
CREATE SCHEMA IF NOT EXISTS GOLD_LAYER;

-- Create role for Snow Bear data scientists
CREATE OR REPLACE ROLE snow_bear_data_scientist;

-- Create warehouse for analytics
CREATE OR REPLACE WAREHOUSE snow_bear_analytics_wh
    WAREHOUSE_SIZE = 'small'
    WAREHOUSE_TYPE = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
COMMENT = 'Analytics warehouse for Snow Bear fan experience analytics';

-- Grant privileges
GRANT USAGE ON WAREHOUSE snow_bear_analytics_wh TO ROLE snow_bear_data_scientist;
GRANT OPERATE ON WAREHOUSE snow_bear_analytics_wh TO ROLE snow_bear_data_scientist;
GRANT ALL ON DATABASE CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB TO ROLE snow_bear_data_scientist;
GRANT ALL ON SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER TO ROLE snow_bear_data_scientist;
GRANT ALL ON SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.GOLD_LAYER TO ROLE snow_bear_data_scientist;

-- Grant Cortex AI privileges (required for AI functions)
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE snow_bear_data_scientist;

-- Grant role to current user
SET my_user_var = (SELECT '"' || CURRENT_USER() || '"');
GRANT ROLE snow_bear_data_scientist TO USER identifier($my_user_var);

-- Switch to Snow Bear role and schema
USE ROLE snow_bear_data_scientist;
USE WAREHOUSE snow_bear_analytics_wh;
USE SCHEMA CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER;

-- Create stage for CSV file upload
CREATE OR REPLACE STAGE snow_bear_data_stage
    COMMENT = 'Stage for Snow Bear fan survey data files';

-- Create the raw data table for basketball fan survey responses
CREATE OR REPLACE TABLE CUSTOMER_MAJOR_LEAGUE_BASKETBALL_DB.BRONZE_LAYER.GENERATED_DATA_MAJOR_LEAGUE_BASKETBALL_STRUCTURED (
	ID VARCHAR(16777216),
	FOOD_OFFERING_COMMENT VARCHAR(16777216),
	FOOD_OFFERING_SCORE VARCHAR(16777216),
	GAME_EXPERIENCE_COMMENT VARCHAR(16777216),
	GAME_EXPERIENCE_SCORE VARCHAR(16777216),
	MERCHANDISE_OFFERING_COMMENT VARCHAR(16777216),
	MERCHANDISE_OFFERING_SCORE VARCHAR(16777216),
	MERCHANDISE_PRICING_COMMENT VARCHAR(16777216),
	MERCHANDISE_PRICING_SCORE VARCHAR(16777216),
	OVERALL_EVENT_COMMENT VARCHAR(16777216),
	OVERALL_EVENT_SCORE VARCHAR(16777216),
	PARKING_COMMENT VARCHAR(16777216),
	PARKING_SCORE VARCHAR(16777216),
	SEAT_LOCATION_COMMENT VARCHAR(16777216),
	SEAT_LOCATION_SCORE VARCHAR(16777216),
	STADIUM_ACCESS_SCORE VARCHAR(16777216),
	STADIUM_COMMENT VARCHAR(16777216),
	TICKET_PRICE_COMMENT VARCHAR(16777216),
	TICKET_PRICE_SCORE VARCHAR(16777216),
	COMPANY_NAME VARCHAR(16777216),
	TOPIC VARCHAR(16777216),
	CREATED_TIMESTAMP TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
);

-- Create file format for CSV loading
CREATE OR REPLACE FILE FORMAT csv_format
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    ESCAPE_UNENCLOSED_FIELD = '\134'
    COMMENT = 'File format for Snow Bear fan survey CSV data';

SELECT 'Snow Bear setup complete! Now upload basketball_fan_survey_data.csv.gz to the snow_bear_data_stage and run the notebook.' AS status;

-- Instructions for next steps:
-- 1. Upload basketball_fan_survey_data.csv.gz to the snow_bear_data_stage
-- 2. Run the Snow Bear notebook (snow_bear_complete_setup.ipynb)

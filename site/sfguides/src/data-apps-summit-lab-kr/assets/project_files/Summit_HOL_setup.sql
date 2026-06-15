-- Go to Marketplace to get the "Cybersyn Financial & Economic Essentials" data product
--   Accept Cybersyn's terms for use of the product
--   Click GET to create a database named CYBERSYN_FINANCIAL__ECONOMIC_ESSENTIALS

-- Setup database, need to be logged in as accountadmin role */ 
-- Set role and warehouse (compute)
USE ROLE accountadmin;
USE WAREHOUSE compute_wh;

--Create database and stage for the Snowpark Python UDF
CREATE DATABASE IF NOT EXISTS summit_hol;
USE DATABASE summit_hol;
CREATE STAGE IF NOT EXISTS udf_stage;

--Test the Cybersyn Essentials data

-- What financial data is available as a time-series from FRED?
SELECT DISTINCT variable_name
FROM CYBERSYN_FINANCIAL__ECONOMIC_ESSENTIALS.CYBERSYN.FINANCIAL_FRED_TIMESERIES;

-- What is the size of the all the time-series data?
SELECT COUNT(*) FROM CYBERSYN_FINANCIAL__ECONOMIC_ESSENTIALS.CYBERSYN.FINANCIAL_FRED_TIMESERIES;

-- What is the US inflation over time (annually)?
SELECT variable_name, date, value, unit
FROM CYBERSYN_FINANCIAL__ECONOMIC_ESSENTIALS.CYBERSYN.FINANCIAL_FRED_TIMESERIES
WHERE 
variable_name = 'Personal Consumption Expenditures: Chain-type Price Index, Seasonally adjusted, Monthly, Index 2012=100'
AND MONTH(date) = 1
ORDER BY date;

-- Now create UDF in VS Code / Notebook
-- Once we created the UDF with the Python Notebook we can test the UDF
SELECT predict_pce_udf(2022);
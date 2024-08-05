author: Swathi Jasti
id: getting-started-with-time-series-analytics-with-pricing-data-on-snowflake
summary: Time Series Analytics with Pricing Data on Snowflake
categories: Getting-Started, Time-Series, Notebooks
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Time Series 

# Time Series Analytics with Pricing Data on Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 2

<img src="assets/time_series_analytics_banner.png"/>

This quickstart explores several time series features using FactSet Tick Data, including TIME_SLICE, ASOF_JOIN, and RANGE BETWEEN for insights into trade data. Aggregating time-series data through downsampling reduces data size and storage needs, using functions like TIME_SLICE and DATE_TRUNC for efficiency. ASOF JOIN simplifies joining time-series tables, matching trades with the closest previous quote, ideal for transaction-cost analysis in financial trading. Windowed aggregate functions, such as moving averages using the RANGE BETWEEN window frame, allow trend analysis over time, accommodating data gaps for flexible rolling calculations.

### Aggregating Time-Series Data
Managing time-series data often requires aggregating fine-grained records into a summarized form, known as downsampling. This process reduces data size and storage needs, and minimizes compute resource requirements during query execution. For example, if a sensor records data every second but changes rarely, data can be aggregated to minute intervals for analysis. 

You can downsample data using the TIME_SLICE function, which groups records into fixed-width "buckets" and applies aggregate functions like SUM and AVG. Similarly, the DATE_TRUNC function reduces the granularity of date or timestamp values. 

[TIME_SLICE](https://docs.snowflake.com/en/sql-reference/functions/time_slice) calculates the beginning or end of a “slice” of time, where the length of the slice is a multiple of a standard unit of time (minute, hour, day, etc.). This function can be used to calculate the start and end times of fixed-width “buckets” into which data can be categorized.

<img src="assets/time_slice.png"/>

### Joining Time-Series Data

The [ASOF JOIN](https://docs.snowflake.com/en/sql-reference/constructs/asof-join) construct simplifies joining tables with time-series data. Commonly used in financial trading analysis, ASOF JOIN enables transaction-cost analysis by matching trades with the closest previous quote. This method is beneficial for analyzing historical data, especially when timestamps from different devices are not perfectly aligned. We will determine transaction costs by joining trades with the closest preceding price data using an ASOF JOIN.

<img src="assets/asof.png"/>

<img src="assets/asof2.png"/>

### Using Windowed Aggregations
Windowed aggregate functions allow you to analyze trends over time by computing rolling calculations (such as moving averages) within defined subsets of a dataset. The [RANGE BETWEEN](https://docs.snowflake.com/en/sql-reference/functions-analytic) window frame, ordered by timestamps or numbers, remains unaffected by gaps in the data, providing flexible rolling aggregations. A range-based window frame consists of a logically computed set of rows rather than a physical number of rows as would be expressed in a row-based frame. In this solution you will explore RANGE BETWEEN to create interesting time series metrics on our data.

<img src="assets/averages.png"/>

### Prerequisites
- Privileges necessary to create a user, database, and warehouse in Snowflake
- Intermediate knowledge of SQL
- Access to run Notebooks in Snowflake

### What You Will Learn 
- Leveraging powerful SQL functions such as TIME_SLICE, ASOF JOIN, RANGE BETWEEN and more
- Analyzing Time Series data using Snowflake Notebooks
- Accessing data from Snowflake Marketplace

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- A [Snowflake](https://app.snowflake.com/) Account

### What You’ll Build 
- Time Series Analytics with Pricing Data on Snowflake

<!-- ------------------------ -->
## Setting up the Data in Snowflake
Duration: 2

We are using FactSet Tick History data from Snowflake Marketplace for this Quickstart. FactSet Provides historical trading information which we will analyze in this Quickstart. 

You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
- Create Snowflake objects (warehouse, database, schema)
- Access FactSet data from Snowflake Marketplace
- Create tables needed

### Access Data from Snowflake Marketplace

Follow below instructions to get the FactSet Tick History data from Snowflake Marketplace.
- Navigate to [Snowsight](https://app.snowflake.com/)
- Click: Data Products
- Click: Marketplace
- Search: FactSet Tick History
- Scroll Down and Click: Tick History
- Click: Get
- Make sure the Database name is: Tick_History
- Which roles, in addition to ACCOUNTADMIN, can access this database? PUBLIC
- Click: Get

### Creating Objects, Loading Data, and Joining Data
Duration: 3

Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".

Paste and run the following SQL in the worksheet to create Snowflake objects (database, schema, tables),

```sql
-- use our accountadmin role
USE ROLE accountadmin;

-- create our database
CREATE OR REPLACE DATABASE time_series_analytics;

-- create schema
CREATE OR REPLACE SCHEMA time_series_analytics.raw;

-- create our virtual warehouse
CREATE OR REPLACE WAREHOUSE time_series_analytics_wh AUTO_SUSPEND = 60;

-- use our time_series_analytics_wh virtual warehouse 
USE WAREHOUSE time_series_analytics_wh;

-- create synthetic data for closing prices from tick history
CREATE OR REPLACE TABLE time_series_analytics.raw.closing_prices AS
WITH filtered_data AS (
    SELECT
        ticker,
        last_date,
        last_time,
        last_price,
        COUNT(DISTINCT date) OVER (PARTITION BY ticker) AS date_count
    FROM
        TICK_HISTORY.PUBLIC.TH_SF_MKTPLACE
    WHERE
        last_price IS NOT NULL  -- Filter out records with NULL last_price
        and msg_type = 0
        and SECURITY_TYPE = 1
),
max_times AS (
    SELECT
        ticker,
        last_date,
        last_time,
        last_price,
        ROW_NUMBER() OVER (PARTITION BY ticker, last_date ORDER BY last_time DESC) AS rn
    FROM
        filtered_data
    WHERE
        date_count > 100
)
SELECT
    ticker,
    last_date as date,
    last_time as time,
    last_price AS closing_price
FROM
    max_times
WHERE
    rn = 1
order by 2 desc;

```

<!-- ------------------------ -->
## Time Series Analytics using Snowflake Notebooks
Duration: 10

This quickstart demonstrates several advanced time series features using FactSet Tick Data on Snowflake. You will learn to leverage powerful SQL functions such as TIME_SLICE, ASOF JOIN, and RANGE BETWEEN to gain deeper insights into time series trade data.

Import the following Snowflake Notebook in Snowsight and run each of the cells: [time_series_analytics_with_pricing_data_on_snowflake.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-time-series-analytics-with-pricing-data-on-snowflake/blob/main/time_series_analytics_with_pricing_data_on_snowflake.ipynb)

<img src="assets/import.png"/>

<img src="assets/create_notebook.png"/>

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

**You did it!** You have successfully completed the Time Series Analytics with Pricing Data on Snowflake Quickstart.

### What you learned
- Leveraged powerful SQL functions such as TIME_SLICE, ASOF JOIN, RANGE BETWEEN and more
- Analyzed Time Series data using Snowflake Notebooks
- Accessed data from Snowflake Marketplace

### Related Resources
- [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-time-series-analytics-with-pricing-data-on-snowflake)
- [Analyzing time-series data on Snowflake](https://docs.snowflake.com/en/user-guide/querying-time-series-data)
- [TIME_SLICE](https://docs.snowflake.com/en/sql-reference/functions/time_slice)
- [ASOF JOIN](https://docs.snowflake.com/en/sql-reference/constructs/asof-join)
- [RANGE BETWEEN](https://docs.snowflake.com/en/sql-reference/functions-analytic)
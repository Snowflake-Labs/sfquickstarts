author: Jacob Kranzler
id: tasty_bytes_zero_to_snowflake_collaboration
summary: Tasty Bytes - Zero to Snowflake - Collaboration Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake


# Tasty Bytes - Zero to Snowflake - Collaboration
<!-- ------------------------ -->

## Data Marketplace Collaboration in Snowflake
Duration: 1
<img src = "assets/collaboration_header.png">

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Collaboration! Within this Quickstart we will highlight the immediately value the Snowflake Marketplace can provide by enriching first party data analysis with Weather data provided by Weather Source.

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- How to Access the Snowflake Marketplace
- How to Acquire Live Weather Source Data in your Account
- How to Create a View
- How to Create a SQL Function
- How to Leverage Snowsight Charts to Explore Visual Insights

### What You Will Build
- The Harmonization of First Party Sales and Third Party Weather Data
- Seamless Convertability from Fahrenheit to Celsius
- Seamless Convertability from Inch to Millimeter
- An Understanding of How to Unlock Additional Insights via the Snowflake Marketplace

## Creating a Worksheet and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming the Worksheet, Copying SQL from GitHub, and Pasting the SQL we will be leveraging within this Quickstart.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account 

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.
    - <img src ="assets/log_into_snowflake.gif" width = "300"/>

### Step 3 - Navigating to Worksheets
- Click on the Worksheets Tab in the left-hand navigation bar.
    - <img src ="assets/worksheet_tab.png" width="250"/>

### Step 4 - Creating a Worksheet
- Within Worksheets, click the "+" button in the top-right corner of Snowsight and choose "SQL Worksheet"
    - <img src = "assets/+_sqlworksheet.png" width ="200">

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Collaboration"
    - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>

### Step 6 - Accessing Quickstart SQL in GitHub
- Click the button below which will direct you to our Tasty Bytes SQL file that is hosted on GitHub.

<button>[tb_zts_collaboration.sql](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/tasty_bytes/tb_zts_collaboration.sql)</button>

### Step 7 - Copying Setup SQL from GitHub
- Within GitHub navigate to the right side and click "Copy raw contents". This will copy all of the required SQL into your clipboard.
    - <img src ="assets/github_copy_raw_contents.png"/>

### Step 8 - Pasting Setup SQL from GitHub into your Snowflake Worksheet
- Path back to Snowsight and your newly created Worksheet and Paste (*CMD + V for Mac or CTRL + V for Windows*) what we just copied from GitHub.

### Step 9 - Click Next -->

## Investigating Zero Sales Days in our First Party Data
Duration: 1

### Overview
Our Tasty Bytes Financial Analysts have brought it to our attention when running year over year analysis that there are unexplainable days in various cities where our truck sales went to 0. One example they have provided was for Hamburg, Germany in February of 2022.


### Step 1 - Querying Point of Sales Data for Trends
Let's start by kicking off this steps three queries to initially set our Role and Warehouse context to `tasty_data_engineer` and `tasty_de_wh`. With the context set, we will then query our Analytics `orders_v` View to provide a result set of sales for Hamburg, Germany in 2022.

```
USE ROLE tasty_data_engineer;
USE WAREHOUSE tasty_de_wh;

SELECT 
    o.date,
    SUM(o.price) AS daily_sales
FROM frostbyte_tasty_bytes.analytics.orders_v o
WHERE 1=1
    AND o.country = 'Germany'
    AND o.primary_city = 'Hamburg'
    AND DATE(o.order_ts) BETWEEN '2022-02-10' AND '2022-02-28'
GROUP BY o.date
ORDER BY o.date ASC;
```

<img src = "assets/3.1.orders_v.png">

Based on what we are seeing above, we can agree with our analysts that we do not have daily sales records for a few days in February so our analysts are definitely on to something. Let's see if we can dig further into why this may have happened in our next section.

### Step 2 - Click Next -->

## Leveraging Weather Source Data from the Snowflake Marketplace
Duration: 2

### Overview
From what we saw in our previous section, it looks like we are missing sales for February 16th through February 21st for Hamburg, Germany.  Within our first party data there is not much else we can use to investigate this but something larger must have been at play here. 
        
One idea we can immediately explore by leveraging the [Snowflake Marketplace](https://www.snowflake.com/en/data-cloud/marketplace/) is extreme weather and a free, public listing provided by Weather Source.

### Step 1 - Acquiring the Weather Source LLC: frostbyte Snowflake Marketplace Listing
The Snowflake Marketplace is the premier location to find, try, and buy the data and applications you need to power innovative business solutions. In this step, we will be acquiring the [Weather Source LLC: frostbyte](https://app.snowflake.com/marketplace/listing/GZSOZ1LLEL/weather-source-llc-weather-source-llc-frostbyte) listing to help drive additional analysis on our Hamburg sales slump.

Please follow the steps and video below to acquire this listing in your Snowflake Account.

- Click -> Home
- Click -> Marketplace
- Search -> frostbyte
- Click -> Weather Source LLC: frostbyte
- Click -> Get
- Rename Database -> FROSTBYTE_WEATHERSOURCE (all capital letters)
- Grant to Additional Roles -> PUBLIC

<img src = "assets/4.1.acquire_weather_source.gif">

>aside positive
>Weather Source is a leading provider of global weather and climate data and our OnPoint Product Suite provides businesses with the necessary weather and climate data to quickly generate meaningful and actionable insights for a wide range of use cases across industries.
>

### Step 2 - Harmonizing First and Third Party Data
With the shared `frostbyte_weathersource` database in place, please execute this steps query to create a `harmonized.daily_weather_v` View joining two Weather Source tables to our country table on the Countries and Cities that Tasty Bytes Food Trucks operate within.

```
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.harmonized.daily_weather_v
    AS
SELECT 
    hd.*,
    TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm,
    pc.city_name AS city,
    c.country AS country_desc
FROM frostbyte_weathersource.onpoint_id.history_day hd
JOIN frostbyte_weathersource.onpoint_id.postal_codes pc
    ON pc.postal_code = hd.postal_code
    AND pc.country = hd.country
JOIN frostbyte_tasty_bytes.raw_pos.country c
    ON c.iso_country = hd.country
    AND c.city = hd.city_name;
```

<img src = "assets/4.2.daily_weather_v.png">

As we see in the View definition above we are joining two of the `frostbyte_weathersource` Tables within the `onpoint_id` Schema and then Harmonizing it with our `country` Table from our `frostbyte_tasty_bytes` Database and `raw_pos` Schema. 

This is the sort of operation we typically find in the Harmonized layer or what others may describe as the Silver zone.s

### Step 3 - Visualizing Daily Temperatures
With the `daily_weather_v` View in our Harmonized Schema in place let's take a look at the Average Daily Weather Temperature for Hamburg in February 2022 by executing our next query.

Along the way we will leverage [AVG](https://docs.snowflake.com/en/sql-reference/functions/avg), [YEAR](https://docs.snowflake.com/en/sql-reference/functions/year) and [MONTH](https://docs.snowflake.com/en/sql-reference/functions/year) functions.

```
SELECT 
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    AVG(dw.avg_temperature_air_2m_f) AS avg_temperature_air_2m_f
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v dw
WHERE 1=1
    AND dw.country_desc = 'Germany'
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = '2022'
    AND MONTH(date_valid_std) = '2'
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;
```

<img src = "assets/4.3.results.png">

To further investigate trends, let's utilize Snowsight Charting to create a Line Graph of the Average Temperature over time.

<img src = "assets/4.3.chart.png">

Based on what we saw above, there is nothing really standing out yet as the obvious reason for zero sales days at our trucks. Let's see what else we can find that might explain things in the next step.

### Step 4 - Bringing in Wind Data
As we saw in our previous step, it does not look like Average Daily Temperature is the reason for our zero sales days in Hamburg. Thankfully, Weather Source provides other weather metrics we can dive into as well. 

Please now execute the next query where we will leverage our Harmonized View to bring in Wind metrics. In this query we will see the usage of our [MAX](https://docs.snowflake.com/en/sql-reference/functions/min) function.

```
SELECT 
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    MAX(dw.max_wind_speed_100m_mph) AS max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v dw
WHERE 1=1
    AND dw.country_desc IN ('Germany')
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = '2022'
    AND MONTH(date_valid_std) = '2'
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;
```

<img src = "assets/4.4.result.png">

Once again this sort of data might better present trends via a quick Snowsight Chart. Please follow the arrows in the screenshots below to move from Results to Charts.

<img src = "assets/4.4.chart.png">

**Ah ha!** The wind for those zero sales days was at hurricane levels. This seems to be a better reason for why our trucks were not able to sell anything on those days. However since we ran this analysis in Harmonized let's now begin on our path to make this accessible in Analytics where our analysts can access these insights on their own.

### Step 5 - Click Next -->

## Democratizing Data Insights
Duration: 3

### Overview
We have now determined that Hurricane level winds were probably at play for the days with zero sales that our Financial Analysts brought to our attention.

Let's now make these sort of research available to anyone in our organization by deploying an Analytics view that all Tasty Bytes employees can access.

### Step 1 - Creating SQL Functions
As we are a global company, let's start our process by first creating two SQL functions to convert Fahrenheit to Celsius and Inches to Millimeters. 

Please execute the two queries within this step one by one to create our `fahrenheit_to_celsius` and `inch_to_millimeter` functions which leverage the [CREATE FUNCTION](https://docs.snowflake.com/en/sql-reference/sql/create-function) command.


```
CREATE OR REPLACE FUNCTION frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(temp_f NUMBER(35,4))
RETURNS NUMBER(35,4)
AS
$$
    (temp_f - 32) * (5/9)
$$;
```

<img src = "assets/5.1.f_to_c.png">

```
CREATE OR REPLACE FUNCTION frostbyte_tasty_bytes.analytics.inch_to_millimeter(inch NUMBER(35,4))
RETURNS NUMBER(35,4)
    AS
$$
    inch * 25.4
$$;
```

<img src = "assets/5.1.inch_to_mm.png">

>aside positive
>When you create a UDF, you specify a handler whose code is written in one of the supported languages. Depending on the handler’s language, you can either include the handler source code in-line with the CREATE FUNCTION statement or reference the handler’s location from CREATE FUNCTION, where the handler is precompiled or source code on a stage.
>

### Step 2 - Creating the SQL for our View
Before deploying our Analytics view, let's create our SQL we will use in the View to combine Daily Sales and Weather together and also leverage our SQL conversion functions. 

Please execute the next query where we filter for Hamburg, Germany and leverage a few functions we have not seen yet being [ZEROIFNULL](https://docs.snowflake.com/en/sql-reference/functions/zeroifnull), [ROUND](https://docs.snowflake.com/en/sql-reference/functions/round) and [DATE](https://docs.snowflake.com/en/sql-reference/functions/to_date).

```
SELECT 
    fd.date_valid_std AS date,
    fd.city_name,
    fd.country_desc,
    ZEROIFNULL(SUM(odv.price)) AS daily_sales,
    ROUND(AVG(fd.avg_temperature_air_2m_f),2) AS avg_temperature_fahrenheit,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(fd.avg_temperature_air_2m_f)),2) AS avg_temperature_celsius,
    ROUND(AVG(fd.tot_precipitation_in),2) AS avg_precipitation_inches,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.inch_to_millimeter(fd.tot_precipitation_in)),2) AS avg_precipitation_millimeters,
    MAX(fd.max_wind_speed_100m_mph) AS max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v fd
LEFT JOIN frostbyte_tasty_bytes.harmonized.orders_v odv
    ON fd.date_valid_std = DATE(odv.order_ts)
    AND fd.city_name = odv.primary_city
    AND fd.country_desc = odv.country
WHERE 1=1
    AND fd.country_desc = 'Germany'
    AND fd.city = 'Hamburg'
    AND fd.yyyy_mm = '2022-02'
GROUP BY fd.date_valid_std, fd.city_name, fd.country_desc
ORDER BY fd.date_valid_std ASC;
```

<img src = "assets/5.2.SQL.png">


The results we have just recieved look great. We can now wrap this SQL within a View in our next step.

### Step 3 - Deploying our Analytics View
Using the same query we just explored, we will need to remove the filters in the WHERE clause, add a [COMMENT](https://docs.snowflake.com/en/sql-reference/sql/comment) and promote this to our `analytics` Schema as the `daily_city_metrics_v` View.

Please now kick off the last query of this section to do just this.

```
CREATE OR REPLACE VIEW frostbyte_tasty_bytes.analytics.daily_city_metrics_v
COMMENT = 'Daily Weather Source Metrics and Orders Data for our Cities'
    AS
SELECT 
    fd.date_valid_std AS date,
    fd.city_name,
    fd.country_desc,
    ZEROIFNULL(SUM(odv.price)) AS daily_sales,
    ROUND(AVG(fd.avg_temperature_air_2m_f),2) AS avg_temperature_fahrenheit,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.fahrenheit_to_celsius(fd.avg_temperature_air_2m_f)),2) AS avg_temperature_celsius,
    ROUND(AVG(fd.tot_precipitation_in),2) AS avg_precipitation_inches,
    ROUND(AVG(frostbyte_tasty_bytes.analytics.inch_to_millimeter(fd.tot_precipitation_in)),2) AS avg_precipitation_millimeters,
    MAX(fd.max_wind_speed_100m_mph) AS max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.harmonized.daily_weather_v fd
LEFT JOIN frostbyte_tasty_bytes.harmonized.orders_v odv
    ON fd.date_valid_std = DATE(odv.order_ts)
    AND fd.city_name = odv.primary_city
    AND fd.country_desc = odv.country
WHERE 1=1
GROUP BY fd.date_valid_std, fd.city_name, fd.country_desc;
```

<img src = "assets/5.3.view.png">

Amazing we have now democratized these sort of insights to the Tasty Bytes organization. Let's bring this all together in our next section and validate our work.

### Step 4 - Click Next -->

## Deriving Insights from Sales and Marketplace Weather Data
Duration: 1

### Overview
With Sales and Weather Data available for all Cities our Food Trucks operate in, let's now take a look at how we have shortened the time to insights our Financial Analysts.

### Step 1 - Simplifying our Analysis
Earlier we had to manually join Point of Sales and Weather Source Data to investigate our Hamburg sales issues, but we greatly simplified that process via our `analytics.daily_city_metrics_v` View. 

Please kick off the next query which shows how much simpler we made this analysis by making it a simple Select statement from a single View.

```
SELECT 
    dcm.date,
    dcm.city_name,
    dcm.country_desc,
    dcm.daily_sales,
    dcm.avg_temperature_fahrenheit,
    dcm.avg_temperature_celsius,
    dcm.avg_precipitation_inches,
    dcm.avg_precipitation_millimeters,
    dcm.max_wind_speed_100m_mph
FROM frostbyte_tasty_bytes.analytics.daily_city_metrics_v dcm
WHERE 1=1
    AND dcm.country_desc = 'Germany'
    AND dcm.city_name = 'Hamburg'
    AND dcm.date BETWEEN '2022-02-01' AND '2022-02-26'
ORDER BY date DESC;
```

<img src = "assets/6.1.results.png">

**Yay!*8 If this was available when our Financial Analysts were initially running their research, they would not have even needed to ping our data teams as the insights are right there. 

By completing this Quickstart we have seen how quickly we are able to derive real world business value by our work and how easy it is to use the Snowflake Marketplace to unlock additional data insights.

### Step 2 - Click Next -->

## Conclusion and Next Steps
Duration: 1

### Conclusion
Fantastic work! You have successfully completed the Tasty Bytes - Zero to Snowflake - Collaboration Quickstart. 

By doing so you have now:
- Accessed the Snowflake Marketplace
- Acquired Live Weather Source Data in your Account
- Created a View
- Created a SQL Function
- Leveraged Snowsight Charts to Explore Visual Insights

If you would like to re-run this Quickstart please leverage the Reset scripts in the bottom of your associated Worksheet.

### Next Steps
To continue your journey in the Snowflake Data Cloud, please now visit the link below to see all other Powered by Taste Bytes - Quickstarts available to you.

- ### [Powered by Tasty Bytes - Quickstarts Table of Contents](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/#3)



author: Cameron Shimmin
id: tasty_bytes_apps_and_collaboration
summary: Tasty Bytes - Zero to Snowflake - Apps & Collaboration Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, Marketplace, Data Sharing, Collaboration, Data Apps

# Tasty Bytes - Zero To Snowflake - Apps & Collaboration
## Apps & Data Collaboration
Duration: 1
<!-- <img src = "assets/collaboration_header.png"> -->

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Apps & Collaboration!

In this Quickstart, we will explore how Snowflake facilitates seamless data collaboration through the Snowflake Marketplace. We will see how easy it is to acquire live, ready-to-query third-party datasets and immediately join them with our own internal data to unlock new insights—all without the need for traditional ETL pipelines.

*Please note: The SQL file provided does not include the "Introduction to Streamlit" section mentioned in its header. This guide will cover all content provided in the SQL file.*

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- How to discover and acquire data from the Snowflake Marketplace.
- How to instantly query live, shared data.
- How to join Marketplace data with your own account data to create enriched views.
- How to leverage third-party Point-of-Interest (POI) data for deeper analysis.
- How to use Common Table Expressions (CTEs) to structure complex queries.

### What You Will Build
- Enriched analytical Views that combine internal sales data with external weather and POI data.


## Creating a Worksheet and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart, we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming the Worksheet, and Pasting the SQL we will be leveraging within this Quickstart.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account.

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.

### Step 3 - Navigating to Worksheets
- Click on the **Projects** Tab in the left-hand navigation bar and click **Worksheets**.

### Step 4 - Creating a Worksheet
- Within Worksheets, click the **"+"** button in the top-right corner of Snowsight.

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Apps & Collaboration".

### Step 6 - Pasting SQL into your Snowflake Worksheet
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** Asset:        Zero to Snowflake v2 - Getting Started with Snowflake
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "apps_and_collaboration"}}';

USE DATABASE tb_101;
USE ROLE accountadmin;
USE WAREHOUSE tb_de_wh;

/* 1. Acquiring weather data from Snowflake Marketplace */
USE ROLE tb_analyst;

/* 2. Integrating Account Data with Weather Source Data */
SELECT 
    DISTINCT city_name,
    AVG(max_wind_speed_100m_mph) AS avg_wind_speed_mph,
    AVG(avg_temperature_air_2m_f) AS avg_temp_f,
    AVG(tot_precipitation_in) AS avg_precipitation_in,
    MAX(tot_snowfall_in) AS max_snowfall_in
FROM zts_weathersource.onpoint_id.history_day
WHERE country = 'US'
GROUP BY city_name;

CREATE OR REPLACE VIEW harmonized.daily_weather_v
COMMENT = 'Weather Source Daily History filtered to Tasty Bytes supported Cities'
    AS
SELECT
    hd.*,
    TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm,
    pc.city_name AS city,
    c.country AS country_desc
FROM zts_weathersource.onpoint_id.history_day hd
JOIN zts_weathersource.onpoint_id.postal_codes pc
    ON pc.postal_code = hd.postal_code
    AND pc.country = hd.country
JOIN raw_pos.country c
    ON c.iso_country = hd.country
    AND c.city = hd.city_name;

SELECT
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    AVG(dw.avg_temperature_air_2m_f) AS average_temp_f
FROM harmonized.daily_weather_v dw
WHERE dw.country_desc = 'Germany'
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = 2022
    AND MONTH(date_valid_std) = 2
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;

CREATE OR REPLACE VIEW analytics.daily_sales_by_weather_v
COMMENT = 'Daily Weather Metrics and Orders Data'
AS
WITH daily_orders_aggregated AS (
    SELECT
        DATE(o.order_ts) AS order_date,
        o.primary_city,
        o.country,
        o.menu_item_name,
        SUM(o.price) AS total_sales
    FROM
        harmonized.orders_v o
    GROUP BY ALL
)
SELECT
    dw.date_valid_std AS date,
    dw.city_name,
    dw.country_desc,
    ZEROIFNULL(doa.total_sales) AS daily_sales,
    doa.menu_item_name,
    ROUND(dw.avg_temperature_air_2m_f, 2) AS avg_temp_fahrenheit,
    ROUND(dw.tot_precipitation_in, 2) AS avg_precipitation_inches,
    ROUND(dw.tot_snowdepth_in, 2) AS avg_snowdepth_inches,
    dw.max_wind_speed_100m_mph AS max_wind_speed_mph
FROM
    harmonized.daily_weather_v dw
LEFT JOIN
    daily_orders_aggregated doa
    ON dw.date_valid_std = doa.order_date
    AND dw.city_name = doa.primary_city
    AND dw.country_desc = doa.country
ORDER BY 
    date ASC;
    
SELECT * EXCLUDE (city_name, country_desc, avg_snowdepth_inches, max_wind_speed_mph)
FROM analytics.daily_sales_by_weather_v
WHERE 
    country_desc = 'United States'
    AND city_name = 'Seattle'
    AND avg_precipitation_inches >= 1.0
ORDER BY date ASC;

/* 3. Explore Safegraph POI data */
CREATE OR REPLACE VIEW harmonized.tastybytes_poi_v
AS 
SELECT 
    l.location_id,
    sg.postal_code,
    sg.country,
    sg.city,
    sg.iso_country_code,
    sg.location_name,
    sg.top_category,
    sg.category_tags,
    sg.includes_parking_lot,
    sg.open_hours
FROM raw_pos.location l
JOIN zts_safegraph.public.frostbyte_tb_safegraph_s sg 
    ON l.location_id = sg.location_id
    AND l.iso_country_code = sg.iso_country_code;
    
SELECT TOP 3
    p.location_id,
    p.city,
    p.postal_code,
    AVG(hd.max_wind_speed_100m_mph) AS average_wind_speed
FROM harmonized.tastybytes_poi_v AS p
JOIN
    zts_weathersource.onpoint_id.history_day AS hd
    ON p.postal_code = hd.postal_code
WHERE
    p.country = 'United States'
    AND YEAR(hd.date_valid_std) = 2022
GROUP BY p.location_id, p.city, p.postal_code
ORDER BY average_wind_speed DESC;

WITH TopWindiestLocations AS (
    SELECT TOP 3
        p.location_id
    FROM harmonized.tastybytes_poi_v AS p
    JOIN
        zts_weathersource.onpoint_id.history_day AS hd
        ON p.postal_code = hd.postal_code
    WHERE
        p.country = 'United States'
        AND YEAR(hd.date_valid_std) = 2022
    GROUP BY p.location_id, p.city, p.postal_code
    ORDER BY AVG(hd.max_wind_speed_100m_mph) DESC
)
SELECT
    o.truck_brand_name,
    ROUND(
        AVG(CASE WHEN hd.max_wind_speed_100m_mph <= 20 THEN o.order_total END),
    2) AS avg_sales_calm_days,
    ZEROIFNULL(ROUND(
        AVG(CASE WHEN hd.max_wind_speed_100m_mph > 20 THEN o.order_total END),
    2)) AS avg_sales_windy_days
FROM analytics.orders_v AS o
JOIN
    zts_weathersource.onpoint_id.history_day AS hd
    ON o.primary_city = hd.city_name
    AND DATE(o.order_ts) = hd.date_valid_std
WHERE o.location_id IN (SELECT location_id FROM TopWindiestLocations)
GROUP BY o.truck_brand_name
ORDER BY o.truck_brand_name;
    
----------------------------------------------------------------------------------
-- Reset Script
----------------------------------------------------------------------------------
USE ROLE accountadmin;

DROP VIEW IF EXISTS harmonized.daily_weather_v;
DROP VIEW IF EXISTS analytics.daily_sales_by_weather_v;
DROP VIEW IF EXISTS harmonized.tastybytes_poi_v;

ALTER WAREHOUSE tb_de_wh SUSPEND;
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Acquiring Data from Snowflake Marketplace

Duration: 2

### Overview

One of our analysts wants to see how weather impacts food truck sales. To do this, he'll use the Snowflake Marketplace to get live weather data from Weather Source, which can then be joined directly with our own sales data. The Marketplace allows us to access live, ready-to-query data from third-party providers without any data duplication or ETL.

> aside positive
> **[Introduction to the Snowflake Marketplace](https://docs.snowflake.com/en/user-guide/data-sharing-intro)**: The Marketplace provides a centralized hub to discover and access a wide variety of third-party data, applications, and AI products.

### Step 1 - Set Initial Context

First, let's set our context to use the `accountadmin` role, which is required to acquire data from the Marketplace.

```sql
USE DATABASE tb_101;
USE ROLE accountadmin;
USE WAREHOUSE tb_de_wh;
```

### Step 2 - Acquire Weather Source Data

Follow these steps in the Snowsight UI to get the Weather Source data:

1.  Make sure you are using the `ACCOUNTADMIN` role.
2.  Navigate to **Data Products** » **Marketplace** from the left-hand navigation menu.
3.  In the search bar, enter: `Weather Source frostbyte`.
4.  Click on the **Weather Source LLC: frostbyte** listing.
5.  Click the **Get** button.
6.  In the options, change the **Database name** to `ZTS_WEATHERSOURCE`.
7.  Grant access to the **PUBLIC** role.
8.  Click **Get**.

<!-- \<img src="assets/marketplace\_listing.png"/\> -->

This process makes the Weather Source data instantly available in our account as a new database, ready to be queried.

### Step 3 - Click Next --\>

## Integrating Account Data with Shared Data

Duration: 3

### Overview

With the Weather Source data now in our account, our analyst can immediately begin joining it with our existing Tasty Bytes data. There's no need to wait for an ETL job to run.

### Step 1 - Explore the Shared Data

Let's switch to the `tb_analyst` role and begin exploring the new weather data. We'll start by getting a list of all distinct US cities available in the share, along with some average weather metrics.

```sql
USE ROLE tb_analyst;

SELECT 
    DISTINCT city_name,
    AVG(max_wind_speed_100m_mph) AS avg_wind_speed_mph,
    AVG(avg_temperature_air_2m_f) AS avg_temp_f,
    AVG(tot_precipitation_in) AS avg_precipitation_in,
    MAX(tot_snowfall_in) AS max_snowfall_in
FROM zts_weathersource.onpoint_id.history_day
WHERE country = 'US'
GROUP BY city_name;
```

### Step 2 - Create an Enriched View

Now, let's create a view that joins our raw `country` data with the historical daily weather data from the Weather Source share. This gives us a unified view of weather metrics for the cities where Tasty Bytes operates.

```sql
CREATE OR REPLACE VIEW harmonized.daily_weather_v
COMMENT = 'Weather Source Daily History filtered to Tasty Bytes supported Cities'
    AS
SELECT
    hd.*,
    TO_VARCHAR(hd.date_valid_std, 'YYYY-MM') AS yyyy_mm,
    pc.city_name AS city,
    c.country AS country_desc
FROM zts_weathersource.onpoint_id.history_day hd
JOIN zts_weathersource.onpoint_id.postal_codes pc
    ON pc.postal_code = hd.postal_code
    AND pc.country = hd.country
JOIN raw_pos.country c
    ON c.iso_country = hd.country
    AND c.city = hd.city_name;
```

### Step 3 - Analyze and Visualize Enriched Data

Using our new view, the analyst can query for the average daily temperature in Hamburg, Germany for February 2022. We can then visualize this as a line chart directly in Snowsight.

1.  Run the query below.
2.  In the **Results** pane, click **Chart**.
3.  Set the **Chart Type** to `Line`.
4.  Set the **X-Axis** to `DATE_VALID_STD`.
5.  Set the **Y-Axis** to `AVERAGE_TEMP_F`.

<!-- end list -->

```sql
SELECT
    dw.country_desc,
    dw.city_name,
    dw.date_valid_std,
    AVG(dw.avg_temperature_air_2m_f) AS average_temp_f
FROM harmonized.daily_weather_v dw
WHERE dw.country_desc = 'Germany'
    AND dw.city_name = 'Hamburg'
    AND YEAR(date_valid_std) = 2022
    AND MONTH(date_valid_std) = 2
GROUP BY dw.country_desc, dw.city_name, dw.date_valid_std
ORDER BY dw.date_valid_std DESC;
```

<!-- \<img src="assets/line\_chart.png"/\> -->

### Step 4 - Create a Sales and Weather View

Let's take it a step further and combine our `orders_v` view with our new `daily_weather_v` to see how sales correlate with weather conditions.

```sql
CREATE OR REPLACE VIEW analytics.daily_sales_by_weather_v
COMMENT = 'Daily Weather Metrics and Orders Data'
AS
WITH daily_orders_aggregated AS (
    SELECT DATE(o.order_ts) AS order_date, o.primary_city, o.country,
        o.menu_item_name, SUM(o.price) AS total_sales
    FROM harmonized.orders_v o
    GROUP BY ALL
)
SELECT
    dw.date_valid_std AS date, dw.city_name, dw.country_desc,
    ZEROIFNULL(doa.total_sales) AS daily_sales, doa.menu_item_name,
    ROUND(dw.avg_temperature_air_2m_f, 2) AS avg_temp_fahrenheit,
    ROUND(dw.tot_precipitation_in, 2) AS avg_precipitation_inches,
    ROUND(dw.tot_snowdepth_in, 2) AS avg_snowdepth_inches,
    dw.max_wind_speed_100m_mph AS max_wind_speed_mph
FROM harmonized.daily_weather_v dw
LEFT JOIN daily_orders_aggregated doa
    ON dw.date_valid_std = doa.order_date
    AND dw.city_name = doa.primary_city
    AND dw.country_desc = doa.country
ORDER BY date ASC;
```

### Step 5 - Answer a Business Question

Our analyst can now answer complex business questions, such as: "How does significant precipitation impact our sales figures in the Seattle market?"

```sql
SELECT * EXCLUDE (city_name, country_desc, avg_snowdepth_inches, max_wind_speed_mph)
FROM analytics.daily_sales_by_weather_v
WHERE 
    country_desc = 'United States'
    AND city_name = 'Seattle'
    AND avg_precipitation_inches >= 1.0
ORDER BY date ASC;
```

### Step 6 - Click Next --\>

## Exploring Point-of-Interest (POI) Data

Duration: 3

### Overview

Our analyst now wants more insight into the specific locations of our food trucks. We can get Point-of-Interest (POI) data from Safegraph, another provider on the Snowflake Marketplace, to enrich our analysis even further.

### Step 1 - Acquire Safegraph POI Data

Follow the same procedure as before to acquire the Safegraph data from the Marketplace.

1.  Ensure you are using the `ACCOUNTADMIN` role.
2.  Navigate to **Data Products** » **Marketplace**.
3.  In the search bar, enter: `safegraph frostbyte`.
4.  Select the **Safegraph: frostbyte** listing and click **Get**.
5.  In the options, set the **Database name** to `ZTS_SAFEGRAPH`.
6.  Grant access to the **PUBLIC** role.
7.  Click **Get**.

### Step 2 - Create a POI View

Let's create a view that joins our internal `location` data with the Safegraph POI data.

```sql
CREATE OR REPLACE VIEW harmonized.tastybytes_poi_v
AS 
SELECT 
    l.location_id, sg.postal_code, sg.country, sg.city, sg.iso_country_code,
    sg.location_name, sg.top_category, sg.category_tags,
    sg.includes_parking_lot, sg.open_hours
FROM raw_pos.location l
JOIN zts_safegraph.public.frostbyte_tb_safegraph_s sg 
    ON l.location_id = sg.location_id
    AND l.iso_country_code = sg.iso_country_code;
```

### Step 3 - Combine POI and Weather Data

Now we can combine all three datasets: our internal data, the weather data, and the POI data. Let's find our top 3 windiest truck locations in the US in 2022.

```sql
SELECT TOP 3
    p.location_id, p.city, p.postal_code,
    AVG(hd.max_wind_speed_100m_mph) AS average_wind_speed
FROM harmonized.tastybytes_poi_v AS p
JOIN zts_weathersource.onpoint_id.history_day AS hd
    ON p.postal_code = hd.postal_code
WHERE
    p.country = 'United States'
    AND YEAR(hd.date_valid_std) = 2022
GROUP BY p.location_id, p.city, p.postal_code
ORDER BY average_wind_speed DESC;
```

### Step 4 - Analyze Brand Resilience to Weather

Finally, let's conduct a more complex analysis to determine brand resilience. We'll use a Common Table Expression (CTE) to first find the windiest locations, and then compare sales on "calm" vs. "windy" days for each truck brand at those locations. This can help inform operational decisions, like offering "Windy Day" promotions for brands that are less resilient.

```sql
WITH TopWindiestLocations AS (
    SELECT TOP 3
        p.location_id
    FROM harmonized.tastybytes_poi_v AS p
    JOIN zts_weathersource.onpoint_id.history_day AS hd ON p.postal_code = hd.postal_code
    WHERE p.country = 'United States' AND YEAR(hd.date_valid_std) = 2022
    GROUP BY p.location_id, p.city, p.postal_code
    ORDER BY AVG(hd.max_wind_speed_100m_mph) DESC
)
SELECT
    o.truck_brand_name,
    ROUND(AVG(CASE WHEN hd.max_wind_speed_100m_mph <= 20 THEN o.order_total END), 2) AS avg_sales_calm_days,
    ZEROIFNULL(ROUND(AVG(CASE WHEN hd.max_wind_speed_100m_mph > 20 THEN o.order_total END), 2)) AS avg_sales_windy_days
FROM analytics.orders_v AS o
JOIN zts_weathersource.onpoint_id.history_day AS hd
    ON o.primary_city = hd.city_name AND DATE(o.order_ts) = hd.date_valid_std
WHERE o.location_id IN (SELECT location_id FROM TopWindiestLocations)
GROUP BY o.truck_brand_name
ORDER BY o.truck_brand_name;
```

### Step 5 - Click Next --\>

## Conclusion and Next Steps

Duration: 1

### Conclusion

Fantastic work\! You have successfully completed the Tasty Bytes - Apps & Collaboration Quickstart.

By doing so you have now explored how to:

  - Discover and acquire live, third-party datasets from the Snowflake Marketplace.
  - Instantly query shared data without performing any ETL.
  - Create enriched analytical views by joining internal data with multiple external datasets.
  - Leverage enriched data to answer complex business questions and drive operational decisions.

If you would like to re-run this Quickstart, please run the `RESET` scripts located at the bottom of your worksheet.

### Next Steps

To continue your journey in the Snowflake AI Data Cloud, please now visit the link below to see all other Powered by Tasty Bytes - Quickstarts available to you.

  - ### [Powered by Tasty Bytes - Quickstarts Table of Contents](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html#3)

<!-- end list -->

```
```
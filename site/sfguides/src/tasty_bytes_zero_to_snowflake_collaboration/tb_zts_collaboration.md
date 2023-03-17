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
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Collaboration!

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- A

### What You Will Build
- B

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
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Setup"
    - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>

### Step 6 - Accessing Quickstart SQL in GitHub
- Click the button below which will direct you to our Tasty Bytes SQL file that is hosted on GitHub.
<button>[tb_zts_financial_governance.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/tasty_bytes_zero_to_snowflake_financial_governance/assets/tb_zts_financial_governance.sql)</button>

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

Based on what we are seeing above, we can agree with our analysts that we do not have `daily_sales` records missing for a few days in February. Let's see if we can dig further into why this may have happened in our next section.

### Step 2 - Click Next -->

## Leveraging Weather Source Data from the Snowflake Marketplace
Duration: 1

### Overview
From what we saw in our previous section, it looks like we are missing sales for February 16th through February 21st for Hamburg, Germany.  Within our first party data there is not much else we can use to investigate this but something larger must have been at play here. 
        
One idea we can immediately explore by leveraging the [Snowflake Marketplace](https://www.snowflake.com/en/data-cloud/marketplace/) is extreme weather and a free, public listing provided by Weather Source.

### Step 1 - Acquiring the Weather Source LLC: frostbyte Snowflake Marketplace Listing
The Snowflake Marketplace is the premier location to find, try, and buy the data and applications you need to power innovative business solutions. In this step, we will be acquiring the [Weather Source LLC: frostbyte](https://app.snowflake.com/marketplace/listing/GZSOZ1LLEL/weather-source-llc-weather-source-llc-frostbyte) listing to help drive additional analysis on our Hamburg sales slump.

Please follow the steps and video below to acquire this listing in your Snowflake Account.

- Click -> Home Icon
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

With the shared `frostbyte_weathersource` database in place, please execute this steps query to create a `harmonized.daily_weather_v` view joining Weather Source Daily History to our `country` dimension table on the Countries and Cities that Tasty Bytes Food Trucks operate within.

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

### Step 3 - Visualizing Daily Temperatures
With the `daily_weather_v` View in our Harmonized schmea in place let's take a look at the Average Daily Weather Temperature for Hamburg in February 2022 by executing our next query.

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

Based on what we saw above, there is nothing really standing out yet as the obvious reason for zero sale days at our trucks. Let's see what else we can find that might explain things in the next step.

##
Duration: 0

### Overview




##
Duration: 0

### Overview



##
Duration: 0

### Overview




### Step X - 
Please follow the steps and video below to access this listing in your Snowflake Account.

    1. Click -> Home Icon
    2. Click -> Marketplace
    3. Search -> frostbyte
    4. Click -> SafeGraph: frostbyte
    5. Click -> Get
    6. Rename Database -> FROSTBYTE_SAFEGRAPH (all capital letters)
    7. Grant to Additional Roles -> PUBLIC


<img src = "assets/acquire_safegraph.gif">
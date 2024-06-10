author: Oleksii Bielov
id: geo-for-machine-learning
summary: Cortex, Geospatial and Streamlit features for Machine Learning use cases 
categories: Getting-Started
environments: web
status: Draft 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Geospatial, Performance, H3, Machine Learning.

# Getting started with Geospatial AI and ML using Snowflake Cortex
<!-- ----------------------------------------- -->
## Overview 

Duration: 6

Snowflake offers a rich toolkit for predictive analytics with a geospatial component. It includes two data types and specialized functions for transformation, prediction, and visualization. This guide is divided into multiple labs, each covering a separate use case that showcases different features for a real-world scenario.

### Prerequisites
* Understanding of [Discrete Global Grid H3](https://www.snowflake.com/blog/getting-started-with-h3-hexagonal-grid/)
* Recommend: Understanding of [Geospatial Data Types](https://docs.snowflake.com/en/sql-reference/data-types-geospatial) and [Geospatial Functions](https://docs.snowflake.com/en/sql-reference/functions-geospatial) in Snowflake
* Recommended: Complete [Geospatial Analysis using Geometry Data Type](https://quickstarts.snowflake.com/guide/geo_analysis_geometry/index.html?index=..%2F..index#0) quickstart
* Recommended: Complete [Performance Optimization Techniques for Geospatial queries](https://quickstarts.snowflake.com/guide/geo_performance/index.html?index=..%2F..index#0) quickstart

### What You’ll Learn
In this quickstart, you will use H3, Time Series, Cortex ML and Streamlit for ML use cases. The quickstart is broken up into separate labs:
* Lab 1: Forecasting time series on a map
* Lab 2: Sentiment analysis of customer reviews

When you complete this quickstart, you will have gained practical experience in several areas:
* Acquiring data from the Snowflake Marketplace
* Loading data from external storage
* Transforming data using H3 and Time Series functions
* Training models and predicting results with Cortex ML
* Using LLM for analysing textual data
* Visualizing data with Streamlit

### What You’ll Need
* A supported Snowflake [Browser](https://docs.snowflake.com/en/user-guide/setup.html)
* Sign-up for a [Snowflake Trial](https://signup.snowflake.com/) OR have access to an existing Snowflake account with the `ACCOUNTADMIN` role or the `IMPORT SHARE `privilege. Select the Enterprise edition, AWS as a cloud provider and US East (Northern Virginia) or EU (Frankfurt) as a region.

<!-- ----------------------------------------- -->

## Setup your Account

Duration: 10

If this is the first time you are logging into the Snowflake UI, you will be prompted to enter your account name or account URL that you were given when you acquired a trial. The account URL contains your [account name](https://docs.snowflake.com/en/user-guide/connecting.html#your-snowflake-account-name) and potentially the region. You can find your account URL in the email that was sent to you after you signed up for the trial.

Click `Sign-in` and you will be prompted for your username and password.

> aside positive
>  If this is not the first time you are logging into the Snowflake UI, you should see a "Select an account to sign into" prompt and a button for your account name listed below it. Click the account you wish to access and you will be prompted for your user name and password (or another authentication mechanism).

### Increase Your Account Permission
The Snowflake web interface has a lot to offer, but for now, switch your current role from the default `SYSADMIN` to `ACCOUNTADMIN`. This increase in permissions will allow you to create shared databases from Snowflake Marketplace listings.

> aside positive
>  If you don't have the `ACCOUNTADMIN` role, switch to a role with `IMPORT SHARE` privileges instead.

<img src ='assets/geo_ml_1.png' width=500>

### Create a Virtual Warehouse

You will need to create a Virtual Warehouse to run queries.

* Navigate to the `Admin > Warehouses` screen using the menu on the left side of the window
* Click the big blue `+ Warehouse` button in the upper right of the window
* Create a LARGE Warehouse as shown in the screen below

<img src ='assets/geo_ml_2.png' width=500>

Be sure to change the `Suspend After (min)` field to 5 min to avoid wasting compute credits.

Navigate to the query editor by clicking on `Worksheets` on the top left navigation bar and choose your warehouse.

- Click the + Worksheet button in the upper right of your browser window. This will open a new window.
- In the new Window, make sure `ACCOUNTADMIN` and `MY_WH` (or whatever your warehouse is named) are selected in the upper right of your browser window.

<img src ='assets/geo_ml_3.png' width=700>

Create a new database and schema where you will store datasets in the `GEOMETRY` data type. Copy & paste the SQL below into your worksheet editor, put your cursor somewhere in the text of the query you want to run (usually the beginning or end), and either click the blue "Play" button in the upper right of your browser window, or press `CTRL+Enter` or `CMD+Enter` (Windows or Mac) to run the query.

```
CREATE DATABASE advanced_analytics;
// Set the working database schema
USE advanced_analytics.public;
USE WAREHOUSE my_wh;
ALTER SESSION SET GEOGRAPHY_OUTPUT_FORMAT='WKT';
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
```
## Forecasting time series on a map

Duration: 40

> aside negative
>  Before starting with this lab, complete preparation steps from `Setup your account` page.

In this lab, we aim to show you how to predict the number of trips in the coming hours in each area of New York. To accomplish this, you will ingest the raw data and then aggregate it by hour and region. For simplicity, you will use [Discrete Global Grid H3](https://www.uber.com/en-DE/blog/h3/). The result will be an hourly time series, each representing the count of trips originating from distinct areas. Before running prediction and visualizing results, you will enrich data with third-party signals, such as information about holidays and offline sports events.

In this lab you will learn how to:
* Work with geospatial data
* Enrich data with new features
* Predict time-series of complex structure

This approach is not unique to trip forecasting but is equally applicable in various scenarios where predictive analysis is required. Examples include forecasting scooter or bike pickups, food delivery orders, sales across multiple retail outlets, or predicting the volume of cash withdrawals across an ATM network. Such models are invaluable for planning and optimization across various industries and services.

### Step 1. Data acquisition

The New York Taxi and Limousine Commission (TLC) has provided detailed, anonymized customer travel data since 2009. Painted yellow cars can pick up passengers in any of the city's five boroughs. Raw data on yellow taxi rides can be found on the [TLC website](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). This data is divided into files by month. Each file contains detailed trip information, you can read about it [here](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf). For our project, you will use an NY Taxi dataset for the 2014-2015 years from the [CARTO Academy](https://app.snowflake.com/marketplace/listing/GZT0Z4CM1E9J2/carto-carto-academy-data-for-tutorials) Marketplace listing.
* Navigate to the `Marketplace` screen using the menu on the left side of the window
* Search for `CARTO Academy` in the search bar
* Find and click the `CARTO Academy - Data for tutorials` tile
* Once in the listing, click the big blue `Get` button

> aside negative
>  On the `Get` screen, you may be prompted to complete your `user profile` if you have not done so before. Click the link as shown in the screenshot below. Enter your name and email address into the profile screen and click the blue `Save` button. You will be returned to the `Get` screen.

change the name of the database from the default to `Carto_Academy`, as all future instructions will assume this name for the database.

<img src ='assets/geo_ml_10.png' width=500>

Another dataset you will use is events data and you can also get it from the Snowflake Marketplace. It is provided by PredictHQ and called [PredictHQ Quickstart Demo](https://app.snowflake.com/marketplace/listing/GZSTZ3TGTNLQM/predicthq-quickstart-demo).
* Search for` PredictHQ Quickstart Demo` in the search bar
* Find and click the `Quickstart Demo` tile

<img src ='assets/geo_ml_4.png' width=700>

* On the `Get Data` screen, change the name of the database from the default to `PredictHQ_Demo`.

<img src ='assets/geo_ml_6.png' width=500>

Congratulations! You have just created a shared database from a listing on the Snowflake Marketplace. 

### Step 2. Data transformation

In this step, you'll divide New York into uniformly sized regions and assign each taxi pick-up location to one of these regions. We aim to get a table with the number of taxi trips per hour for each region.

To achieve this division, you will use the Discrete Global Grid H3. H3 organizes the world into a grid of equal-sized hexagonal cells, with each cell identified by a unique code (either a string or an integer). This hierarchical grid system allows cells to be combined into larger cells or subdivided into smaller ones, facilitating efficient geospatial data processing.

H3 offers 16 different resolutions for dividing areas into hexagons, ranging from resolution 0, where the world is segmented into 122 large hexagons, to resolution 15. At this resolution, each hexagon is less than a square meter, covering the world with approximately 600 trillion hexagons. You can read more about resolutions [here](https://h3geo.org/docs/core-library/restable/). For our task, we will use resolution 8, where the size of each hexagon is about 0.7 sq. km (0.3 sq. miles).

As a source of the trips data you will use `TLC_YELLOW_TRIPS_2014` and `TLC_YELLOW_TRIPS_2015` tables from the CARTO listing. We are interested in the following fields:
* Pickup Time
* Dropoff Time
* Distance
* Pickup Location
* Dropoff Location
* Total Amount

First, specify the default Database, Schema and the Warehouse:
```
USE advanced_analytics.public;
USE WAREHOUSE my_wh;
```

Since CARTO's tables contain raw data you might want to clean it before storing. In the following query you will do a few data cleaning steps:
* Remove rows that are outside of latitude/longitude allowed values
* Keep only trips with a duration longer than one minute and distances more than 10 meters.

And since you are interested in trip data for 2014 and 2015 you need to union `TLC_YELLOW_TRIPS_2014` and `TLC_YELLOW_TRIPS_2015` tables. On average, the execution time on the LARGE warehouse is under 4 minutes.

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides AS
SELECT CONVERT_TIMEZONE('UTC', 'America/New_York', to_timestamp(PICKUP_DATETIME::varchar)) PICKUP_TIME,
       CONVERT_TIMEZONE('UTC', 'America/New_York', to_timestamp(DROPOFF_DATETIME::varchar)) DROPOFF_TIME,
       st_point(PICKUP_LONGITUDE, PICKUP_LATITUDE) AS PICKUP_LOCATION,
       st_point(DROPOFF_LONGITUDE, DROPOFF_LATITUDE) AS DROPOFF_LOCATION,
       trip_distance,
       total_amount
FROM CARTO_ACADEMY.CARTO.TLC_YELLOW_TRIPS_2014
WHERE pickup_latitude BETWEEN -90 AND 90
  AND dropoff_latitude BETWEEN -90 AND 90
  AND pickup_longitude BETWEEN -180 AND 180
  AND dropoff_longitude BETWEEN -180 AND 180
  AND st_distance(st_point(PICKUP_LONGITUDE, PICKUP_LATITUDE), st_point(DROPOFF_LONGITUDE, DROPOFF_LATITUDE)) > 10
  AND TIMEDIFF(MINUTE, to_timestamp(PICKUP_DATETIME::varchar), to_timestamp(DROPOFF_DATETIME::varchar)) > 1
UNION ALL
SELECT CONVERT_TIMEZONE('UTC', 'America/New_York', to_timestamp(PICKUP_DATETIME::varchar)) PICKUP_TIME,
       CONVERT_TIMEZONE('UTC', 'America/New_York', to_timestamp(DROPOFF_DATETIME::varchar)) DROPOFF_TIME,
       st_point(PICKUP_LONGITUDE, PICKUP_LATITUDE) AS PICKUP_LOCATION,
       st_point(DROPOFF_LONGITUDE, DROPOFF_LATITUDE) AS DROPOFF_LOCATION,
       trip_distance,
       total_amount
FROM CARTO_ACADEMY.CARTO.TLC_YELLOW_TRIPS_2015
WHERE pickup_latitude BETWEEN -90 AND 90
  AND dropoff_latitude BETWEEN -90 AND 90
  AND pickup_longitude BETWEEN -180 AND 180
  AND dropoff_longitude BETWEEN -180 AND 180
  AND st_distance(PICKUP_LOCATION, DROPOFF_LOCATION) > 10
  AND TIMEDIFF(MINUTE, PICKUP_TIME, DROPOFF_TIME) > 1;
```

Now you will create a table where, for each pair of timestamp/H3, we calculate the number of trips. You will strip off minutes and seconds and keep only hours.

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_h3 AS
SELECT TIME_SLICE(pickup_time, 60, 'minute', 'START') AS pickup_time,
       H3_POINT_TO_CELL_string(pickup_location, 8) AS h3,
       count(*) AS pickups
FROM advanced_analytics.public.ny_taxi_rides
GROUP BY 1, 2;
```

Since on resolution 8, you might have more than 1000 hexagons for New York, to speed up the training process, you will keep only hexagons that had more than 1M pickups in 2014.  This is shown in the following code block. 

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_h3 
AS WITH all_hexagons AS
  (SELECT h3,
          SUM(pickups) AS total_pickups
   FROM advanced_analytics.public.ny_taxi_rides_h3
   WHERE year(pickup_time) = 2014
   GROUP BY 1)
SELECT t1.*
FROM advanced_analytics.public.ny_taxi_rides_h3 t1
INNER JOIN all_hexagons t2 ON t1.h3 = t2.h3
WHERE total_pickups >= 1000000;
```

It's important to remember that if the raw data lacks records for a specific hour and area combination, the aggregated data for that period should be marked as 0. This step is crucial for accurate time series prediction. Run the following query to add records indicating that there were zero trips for any H3 location and timestamp pair without recorded trips.

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_h3 AS
WITH all_dates_hexagons AS (
    SELECT DATEADD(HOUR, VALUE::int, '2014-01-01'::timestamp) AS pickup_time, h3
    FROM TABLE(FLATTEN(ARRAY_GENERATE_RANGE(0, DATEDIFF('hour', '2014-01-01', '2015-12-31 23:59:00') + 1)))
    CROSS JOIN (SELECT DISTINCT h3 FROM advanced_analytics.public.ny_taxi_rides_h3)
)
SELECT t1.pickup_time, 
t1.h3, IFF(t2.pickups IS NOT NULL, t2.pickups, 0) AS pickups
FROM all_dates_hexagons t1
LEFT JOIN advanced_analytics.public.ny_taxi_rides_h3 t2 
ON t1.pickup_time = t2.pickup_time AND t1.h3 = t2.h3;
```

### Step 4. Data Enrichment

In this step, you will enhance our dataset with extra features that could improve the accuracy of our predictions. Cortex model for time series automatically encodes days of the week as a separate feature, but it makes sense to consider that public or school holidays could affect the demand for taxi services. Likewise, areas hosting sporting events might experience a surge in taxi pickups. To incorporate this insight, you will use data from [PredictHQ - Quickstart Demo](https://app.snowflake.com/marketplace/listing/GZSTZ3TGTNLQM/predicthq-quickstart-demo) listing, which provides information on events in New York for the years 2014-2015.

Run the following query to enrich the data with holiday, and event information. For sports events, you will include only those with a high rank.

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_h3 AS
SELECT t1.*,
       IFF(t2.category = 'school-holidays', 'school-holidays', 'None') AS school_holiday,
       IFF(t3.category = 'public-holidays', ARRAY_TO_STRING(t3.labels, ', '), 'None') AS public_holiday,
       IFF(t4.category = 'sports', t4.labels[0]::string, 'None') AS sport_event
FROM advanced_analytics.public.ny_taxi_rides_h3 t1
LEFT JOIN (SELECT distinct title, category, event_start, event_end, labels 
           FROM PREDICTHQ_DEMO.PREDICTHQ.PREDICTHQ_EVENTS_SNOWFLAKE_SUMMIT_2024 
           WHERE category = 'school-holidays' and title ilike 'New York%') t2 
    ON DATE(t1.pickup_time) between t2.event_start AND t2.event_end
LEFT JOIN (SELECT distinct title, category, event_start, event_end, labels 
           FROM PREDICTHQ_DEMO.PREDICTHQ.PREDICTHQ_EVENTS_SNOWFLAKE_SUMMIT_2024 
           WHERE array_contains('holiday-national'::variant, labels)) t3 
    ON DATE(t1.pickup_time) between t3.event_start AND t3.event_end
LEFT JOIN (SELECT * from PREDICTHQ_DEMO.PREDICTHQ.PREDICTHQ_EVENTS_SNOWFLAKE_SUMMIT_2024 
           WHERE phq_rank > 70 and category = 'sports') t4 
    ON t1.pickup_time = date_trunc('hour', t4.event_start) 
    AND t1.h3 = h3_point_to_cell_string(t4.geo, 8);
```

### Step 5. Training and Prediction

In this step, you'll divide our dataset into two parts: the Training set and the Prediction set. The Training set will be used to train our machine learning model. It will include data from the entirety of 2014 and part of 2015, going up to June 5th, 2015. Run the following query to create the Training set:

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_h3_train AS
SELECT *
FROM advanced_analytics.public.ny_taxi_rides_h3
WHERE date(pickup_time) < date('2015-06-05 12:00:00');
```

The prediction set, on the other hand, will contain data for one week starting June 5th, 2015. This setup allows us to make predictions on data that wasn't used during training.

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_h3_predict AS
SELECT h3,
       pickup_time,
       SCHOOL_HOLIDAY,
       PUBLIC_HOLIDAY,
       SPORT_EVENT
FROM advanced_analytics.public.ny_taxi_rides_h3
WHERE date(pickup_time) >= date('2015-06-05')
AND date(pickup_time) < date('2015-06-12');
```

Now that you have the Training and Prediction sets, you can run your model training step. In this step, you will use Snowflake’s Cortex ML Forecasting function to train your `ny_taxi_rides_model`. You’re telling the function it should train on `ny_taxi_rides_h3_train` – and that this table contains data for multiple distinct time series (`series_colname => ‘h3’`),  one for each h3 in the table. The function will now automatically train one machine learning model for each h3. Note that you are also telling the model which column in our table to use as a timestamp and which column to treat as our “target” (i.e., the column you want to forecast). On average the query below completes in about 7 minutes on the LARGE warehouse.

```
CREATE OR REPLACE snowflake.ml.forecast ny_taxi_rides_model(
  input_data => system$reference('table', 'advanced_analytics.public.ny_taxi_rides_h3_train'), 
  series_colname => 'h3', 
  timestamp_colname => 'pickup_time', 
  target_colname => 'pickups');
```

Now you will predict the "future" demand for one week of test data. Run the following command to forecast demand for each H3 cell ID  and store your results in the "forecasts" table.

Similar to what you did in the training step, you specify the data the model should use to generate its forecasts (`ny_taxi_rides_h3_predict`) and indicate which columns to use for identifying unique H3 and for timestamps. 

```
BEGIN
    CALL ny_taxi_rides_model!FORECAST(
        INPUT_DATA => SYSTEM$REFERENCE('TABLE', 'advanced_analytics.public.ny_taxi_rides_h3_predict'),
        SERIES_COLNAME => 'h3',
        TIMESTAMP_COLNAME => 'pickup_time',
        CONFIG_OBJECT => {'prediction_interval': 0.95}
    );
    -- These steps store your predictions to a table.
    LET x := SQLID;
    CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_model_forecast AS 
    SELECT series::string as h3,
    ts AS pickup_time,
    -- If any forecasts or prediction intervals are negative you need to convert them to zero. 
    CASE WHEN forecast < 0 THEN 0 ELSE forecast END AS forecast,
    CASE WHEN lower_bound < 0 THEN 0 ELSE lower_bound END AS lower_bound,
    CASE WHEN upper_bound < 0 THEN 0 ELSE upper_bound END AS upper_bound
    FROM TABLE(RESULT_SCAN(:x));
END;
```
Create a table with predicted and actual results:
```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_compare AS
SELECT t1.h3, 
       t1.pickup_time, 
       t2.pickups, 
       round(t1.forecast, 0) as forecast
FROM advanced_analytics.public.ny_taxi_rides_model_forecast t1
INNER JOIN advanced_analytics.public.ny_taxi_rides_h3 t2
ON t1.h3 = t2.h3
AND t1.pickup_time = t2.pickup_time;
```

Now you will generate evaluation metrics and store them in the `ny_taxi_rides_metrics` table:

```
BEGIN
    CALL ny_taxi_rides_model!show_evaluation_metrics();
    LET x := SQLID;
    CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_metrics AS 
    SELECT series::string as h3,
           metric_value,
           error_metric
    FROM TABLE(RESULT_SCAN(:x));
END;
```

The table `ny_taxi_rides_metrics` contains various metrics; please review what is available in the table. You should select a metric that allows uniform comparisons across all hexagons to understand the model's performance in each hexagon. Since trip volumes may vary among hexagons, the chosen metric should not be sensitive to absolute values. The Symmetric Mean Absolute Percentage Error ([SMAPE](https://en.wikipedia.org/wiki/Symmetric_mean_absolute_percentage_error)) would be a suitable choice. Create a table with the list of hexagons and the SMAPE value for each:

```
CREATE OR REPLACE TABLE advanced_analytics.public.ny_taxi_rides_metrics AS
SELECT h3, metric_value AS smape 
FROM advanced_analytics.public.ny_taxi_rides_metrics
WHERE error_metric::string = 'SMAPE'
order by 2 asc;
```

### Step 6. Visualization and analysis

In this step, you will visualize the actual and predicted results and think on how you can improve our model. Open `Projects > Streamlit > + Streamlit App`. Give the new app a name, for example `Demand Prediction - model analysis`, and pick `ADVANCED_ANALYTICS.PUBLIC` as an app location.

<img src ='assets/geo_ml_7.png' width = 500>

Click on the packages tab and add `pydeck`, `branca` and `plotly` to the list of packages as our app will be using them. 

<img src ='assets/geo_ml_8.png' width = 450>

Then copy-paste the following code to the editor and click `Run`:

```
import branca.colormap as cm
import datetime
import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st
from snowflake.snowpark.context import get_active_session

@st.cache_data
def get_dataframe_from_raw_sql(query: str) -> pd.DataFrame:
    session = get_active_session()
    pandas_df = session.sql(query).to_pandas()
    return pandas_df

def pydeck_chart_creation(
    chart_df: pd.DataFrame,
    coordinates: tuple = (40.742, -73.984),
    elevation_3d: bool = False,
):
    highest_count_df = 0 if chart_df is None else chart_df["COUNT"].max()
    st.image('https://sfquickstarts.s3.us-west-1.amazonaws.com/hol_geo_spatial_ml_using_snowflake_cortex/gradient.png')
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=coordinates[0],
                longitude=coordinates[1],
                pitch=45,
                zoom=10,
            ),
            tooltip={"html": "<b>{H3}:</b> {COUNT}", "style": {"color": "white"}},
            layers=[
                pdk.Layer(
                    "H3HexagonLayer",
                    chart_df,
                    get_hexagon="H3",
                    get_fill_color="COLOR",
                    get_line_color="COLOR",
                    get_elevation=f"COUNT/{highest_count_df}",
                    auto_highlight=True,
                    elevation_scale=10000 if elevation_3d else 0,
                    pickable=True,
                    elevation_range=[0, 300],
                    extruded=True,
                    coverage=1,
                    opacity=0.3,
                )
            ],
        )
    )

def generate_linear_color_map(colors: list, quantiles):
    return cm.LinearColormap(
        colors,
        vmin=quantiles.min(),
        vmax=quantiles.max(),
        index=quantiles,
    )

def render_plotly_line_chart(chart_df: pd.DataFrame):
    fig = px.line(
        chart_df,
        x="PICKUP_TIME",
        y=["PICKUPS", "FORECAST"],
        color_discrete_sequence=["#D966FF", "#126481"],
        markers=True,
    )

    fig.update_layout(yaxis_title="Pickups", xaxis_title="")
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title("NY Pickup Location App :balloon:")
st.write("""An app that visualizes geo-temporal data from NY taxi pickups using H3 and time series. 
			It can be useful to visualize marketplace signals that are distributed spatially and temporally.""")

AVGLATITUDELONGITUDE = """SELECT
AVG(ST_Y(H3_CELL_TO_POINT(h3))) AS lat,
AVG(ST_X(h3_cell_to_point(h3))) AS lon,
FROM advanced_analytics.public.ny_taxi_rides_compare"""

SQLQUERYTIMESERIES = """SELECT pickup_time, h3, forecast, pickups
FROM advanced_analytics.public.ny_taxi_rides_compare"""

SQLQUERYMETRICS = """SELECT * FROM advanced_analytics.public.ny_taxi_rides_metrics"""

df_avg_lat_long = get_dataframe_from_raw_sql(AVGLATITUDELONGITUDE)
avg_coordinate = (df_avg_lat_long.iloc[0, 0], df_avg_lat_long.iloc[0, 1])
df_metrics = get_dataframe_from_raw_sql(SQLQUERYMETRICS)

with st.sidebar:
    initial_start_date = datetime.date(2015, 6, 6)
    selected_date_range = st.date_input(
        "Date Range:",
        (initial_start_date, initial_start_date + datetime.timedelta(days=7)),
        format="MM.DD.YYYY",)

    tr_col_l, tr_col_r = st.columns(2)
    with tr_col_l:
        selected_start_time_range = st.time_input(
            "Start Time Range",
            datetime.time(0, 0),
            key="selected_start_time_range",
            step=3600,)
    with tr_col_r:
        selected_end_time_range = st.time_input(
            "End Time Range:",
            datetime.time(23, 00),
            key="selected_end_time_range",
            step=3600,)
    h3_options = st.selectbox(
        "H3 cells to display", (["All"] + df_metrics["H3"].to_list()))

    with st.expander(":orange[Expand to see SMAPE metric]"):
        df_metrics_filtered = df_metrics
        if h3_options != "All":
            df_metrics_filtered = df_metrics[df_metrics["H3"] == h3_options]

        st.dataframe(df_metrics_filtered, hide_index=True, width=300)
    chckbox_3d_value = st.checkbox(
        "3D", key="chkbx_forecast", help="Renders H3 Hexagons in 3D")

DF_PICKUPS = None
DF_FORECAST = None

start_end_date_selected = len(selected_date_range) == 2

if start_end_date_selected:
    sql_query_pickups = f"""SELECT h3,
    SUM(pickups) AS COUNT
    FROM advanced_analytics.public.ny_taxi_rides_compare
    WHERE pickup_time BETWEEN DATE('{selected_date_range[0]}') AND DATE('{selected_date_range[1]}')
    AND TIME(pickup_time) BETWEEN '{selected_start_time_range}' AND '{selected_end_time_range}'
    GROUP BY 1"""

    sql_query_forecast = f"""SELECT h3,
    sum(forecast) AS COUNT
    FROM advanced_analytics.public.ny_taxi_rides_compare
    WHERE pickup_time BETWEEN DATE('{selected_date_range[0]}') AND DATE('{selected_date_range[1]}')
    AND TIME(pickup_time) BETWEEN '{selected_start_time_range}' AND '{selected_end_time_range}'
    GROUP BY 1"""

    colors_list = ["gray", "blue", "green", "yellow", "orange", "red"]
    DF_PICKUPS = get_dataframe_from_raw_sql(sql_query_pickups)
    quantiles_pickups = DF_PICKUPS["COUNT"].quantile([0, 0.25, 0.5, 0.75, 1])
    color_map_pickups = generate_linear_color_map(colors_list, quantiles_pickups)
    DF_PICKUPS["COLOR"] = DF_PICKUPS["COUNT"].apply(color_map_pickups.rgb_bytes_tuple)

    DF_FORECAST = get_dataframe_from_raw_sql(sql_query_forecast)
    quantiles_forecast = DF_FORECAST["COUNT"].quantile([0, 0.25, 0.5, 0.75, 1])
    color_map_forecast = generate_linear_color_map(colors_list, quantiles_forecast)
    DF_FORECAST["COLOR"] = DF_FORECAST["COUNT"].apply(
        color_map_forecast.rgb_bytes_tuple)

    if h3_options != "All":
        DF_PICKUPS = DF_PICKUPS[DF_PICKUPS["H3"] == h3_options]
        DF_FORECAST = DF_FORECAST[DF_FORECAST["H3"] == h3_options]

col1, col2 = st.columns(2)
with col1:
    st.write("**Actual Demand**")
    pydeck_chart_creation(DF_PICKUPS, avg_coordinate, chckbox_3d_value)
with col2:
    st.write("**Forecasted Demand**")
    pydeck_chart_creation(DF_FORECAST, avg_coordinate, chckbox_3d_value)

df_time_series = get_dataframe_from_raw_sql(SQLQUERYTIMESERIES)
if DF_FORECAST is None or len(DF_FORECAST) == 0:
    st.stop()

comparision_df_filter = (
    (pd.to_datetime(df_time_series["PICKUP_TIME"]).dt.date >= selected_date_range[0])
    & (pd.to_datetime(df_time_series["PICKUP_TIME"]).dt.date <= selected_date_range[1])
    & (pd.to_datetime(df_time_series["PICKUP_TIME"]).dt.time >= selected_start_time_range)
    & (pd.to_datetime(df_time_series["PICKUP_TIME"]).dt.time <= selected_end_time_range))

if h3_options == "All":
    st.markdown("### Comparison for All Hexagons")
    df_time_series_filtered = (
        df_time_series[comparision_df_filter]
        .groupby(["PICKUP_TIME"], as_index=False)
        .sum()
    )
    df_time_series_filtered = df_time_series_filtered[
        ["PICKUP_TIME", "FORECAST", "PICKUPS"]
    ]
    with st.expander("Raw Data"):
        st.dataframe(df_time_series_filtered, use_container_width=True)
else:
    st.markdown(f"### Comparison for Hexagon ID {h3_options}")
    df_time_series_filtered = (
        df_time_series[(df_time_series["H3"] == h3_options) & comparision_df_filter]
        .groupby(["PICKUP_TIME"], as_index=False)
        .sum()
    )
    with st.expander("Raw Data"):
        st.dataframe(df_time_series_filtered, use_container_width=True)

render_plotly_line_chart(df_time_series_filtered)
```

After clicking `Run` button you will see the following UI:

<img src ='assets/geo_ml_14.png'>

Click `Expand to see SMAPE metric` in the sidebar and find hexagons with good/bad MAPE values. Find them on the map using `H3 cells to display` dropdown.

As you can see, overall, the model is quite good, with SMAPE below 0.3 for most of the hexagons. Even with its current quality, the model can already be used to predict future demand. However, let's still consider how you can improve it.

The worst predictions are for hexagons corresponding to LaGuardia Airport (`882a100e25fffff`, `882a100f57fffff`, `882a100f53fffff`). To address this, you might consider adding information about flight arrivals and departures, which could improve the model's quality. It is a bit surprising to see poor quality at the hexagon `882a100897fffff`, which is close to Central Park. However, it seems that June 7th is the main driver of the poor prediction, as model significantly underpredicted during both day and night hours.

<img src ='assets/geo_ml_9.png' width = 600>

You have information about public and school holidays and sports events among our features. Perhaps adding information about other local events, such as festivals, could improve the overall quality of the model.

> aside positive
>  The code from this quickstart can be reused for other industries, such as food delivery, micro-mobility, retail, finance, etc. You might need to use different time intervals, third-party datasets, or quality metrics, but the idea and toolkit stay the same.

## Customer Reviews Sentiment Analysis

Duration: 40

> aside negative
>  Before starting with this lab, complete the preparation steps from `Setup your account` page.

This lab will show you how to inject AI into your spatial analysis using Cortex Large Language Model (LLM) Functions to help you take your product and marketing strategy to the next level. Specifically, you’re going to build a data application that gives food delivery companies the ability to explore the sentiments of customers in the Greater Bay Area. To do this, you use the Cortex LLM Complete Function to classify customer sentiment and extract the underlying reasons for that sentiment from a customer review. Then you use the Discrete [Global Grid H3](https://www.uber.com/en-DE/blog/h3/) for visualizing and exploring spatial data. 

### Step 1. Data acquisition

To complete the project you will use a synthetic dataset with delivery orders with the feedback for each order. We will simplify the task of data acquisition by putting the dataset in an S3 bucket, which you will connect as an external stage.

First specify the default Database, Schema and the Warehouse and create a file format that corresponds to the format of the trip and holiday data we stored in S3. Run the following queries:
```
USE advanced_analytics.public;
USE WAREHOUSE my_wh;
CREATE OR REPLACE FILE FORMAT csv_format_nocompression TYPE = csv
FIELD_OPTIONALLY_ENCLOSED_BY = '"' FIELD_DELIMITER = ',' skip_header = 1;
```
Now you will create an external stage using S3 with test data:
```
CREATE OR REPLACE STAGE aa_stage URL = 's3://sfquickstarts/hol_geo_spatial_ml_using_snowflake_cortex/';
```
Then create a table where you will store the customer feedback dataset:
```
CREATE OR REPLACE TABLE advanced_analytics.public.orders_reviews AS
SELECT  $1::NUMBER as order_id,
        $2::VARCHAR as customer_id,
        TO_GEOGRAPHY($3) as delivery_location,
        $4::NUMBER as delivery_postcode,
        $5::FLOAT as delivery_distance_miles,
        $6::VARCHAR as restaurant_food_type,
        TO_GEOGRAPHY($7) as restaurant_location,
        $8::NUMBER as restaurant_postcode,
        $9::VARCHAR as restaurant_id,
        $10::VARCHAR as review
FROM @advanced_analytics.public.aa_stage/food_delivery_reviews.csv (file_format => 'csv_format_nocompression');
```

Congratulations!  Now you have `orders_reviews` table containing 100K orders with reviews.

### Step 2. Preparing and running the prompt

In this step, you will prepare the prompt to run the analysis. For the task at hand, you will use the CORTEX.COMPLETE ( ) function because it is purpose-built to power data processing and data generation tasks. First, let's create a cortex role. In the query below change the username AA to the username you used to login to Snowflake.

```
CREATE OR REPLACE ROLE cortex_user_role;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE cortex_user_role;

GRANT ROLE cortex_user_role TO USER AA;
```

You are now ready to provide CORTEX.COMPLETE ( ) functions with the instructions on the analysis that you want to produce. Specifically, using a raw table with reviews you'll create a new table with two additional columns: Overall Sentiment and Sentiment Categories which are composed of two different CORTEX.COMPLETE ( ) prompts. For complex aspect-based sentiment analysis like this, you are going to pick the mixtral-8x7b, a very capable open-source LLM created by Mistral AI. 
* **Overall Sentiment** assigns an overall rating of the delivery: Very Positive, Positive, Neutral, Mixed, Negative, Very Negative, or other. 
* **Sentiment Categories** give us richer insights into why the overall rating is based on Food Cost, Quality, and Delivery Time. 

As a general rule when writing a prompt, the instructions have to be simple, clear, and complete. For example, you will notice that you clearly define the task as classifying customer reviews into specific categories. It’s important to define constraints of the desired output, otherwise the LLM will produce unexpected output. Below, you specifically tell the LLM to categorize anything it is not sure of as Other, and explicitly tell it to respond in JSON format. 


```
CREATE OR REPLACE TABLE advanced_analytics.public.orders_reviews_sentiment_test as
SELECT TOP 10
    order_id
    , customer_id
    , delivery_location
    , delivery_postcode
    , delivery_distance_miles
    , restaurant_food_type
    , restaurant_location
    , restaurant_postcode
    , restaurant_id
    , review
    , snowflake.cortex.complete('mixtral-8x7b'
        , concat('You are a helpful data assistant and your job is to return a JSON formatted response that classifies a customer review (represented in the <review> section) as one of the following seven sentiment categories (represented in the <categories> section). Return your classification exclusively in the JSON format: {classification: <<value>>}, where <<value>> is one of the 7 classification categories in the section <categories>. 
        
        <categories>
        Very Positive
        Positive
        Neutral
        Mixed 
        Negative 
        Very Negative
        Other
        </categories>
        
        "Other" should be used for the classification if you are unsure of what to put. No other classifications apart from these seven in the <categories> section should be used.
        
        Here are some examples: 
            1. If review is: "This place is awesome! The food tastes great, delivery was super fast, and the cost was cheap. Amazing!", then the output should only be {"Classification": "Very Positive"}
            2. If review is: "Tried this new place and it was a good experience. Good food delivered fast.", then the output should only be {"Classification": "Positive"}
            3. If review is: "Got food from this new joint. It was OK. Nothing special but nothing to complain about either", then the output should only be {"Classification": "Neural"}
            4. If review is: "The pizza place we ordered from had the food delivered real quick and it tasted good. It just was pretty expensive for what we got.", then the output should only be {"Classification": "Mixed"}
            5. If review is: "The hamburgers we ordered took a very long time and when they arrived they were just OK.", then the output should only be {"Classification": "Negative"}
            6. If review is: "This food delivery experience was super bad. Overpriced, super slow, and the food was not that great. Disappointed.", then the output should only be {"Classification": "Very Negative"}
            7. If review is: "An experience like none other", then the output should be "{"Classification": Other"}
        
         It is very important that you do not return anything but the JSON formatted response. 
            
        <review>', review, '</review>
        JSON formatted Classification Response: '
                )
    ) as sentiment_assessment   
    , snowflake.cortex.complete(
        'mixtral-8x7b'
        , concat('You are a helpful data assistant. Your job is to classify customer input <review>. If you are unsure, return null. For a given category classify the sentiment for that category as: Very Positive, Positive, Mixed, Neutral, Negative, Very Negative. Respond exclusively in JSON format.

        {
        food_cost:
        food_quality:
        food_delivery_time:
    
        }
      '  
, review 
, 'Return results'
        )) as sentiment_categories
FROM 
    advanced_analytics.public.orders_reviews;
```

  If you look inside of `advanced_analytics.public.orders_reviews_sentiment_test` you'll notice two new columns: `sentiment_assesment` and `sentiment_categories`. `sentiment_assesment` contains overall assessment of the sentiment based on the review and `sentiment_categories` has an evaluation of each of three components individually: cost, quality and delivery time.

  <img src ='assets/geo_ml_11.png'>

  Now when you see that the results stick to the expected format, you can run the query above without the `top 10` limit. This query might take some time to complete, so to save time for this quickstart we've ran it for you in advance and stored results which you can import into new table by running following two queries:


```
CREATE OR REPLACE TABLE ADVANCED_ANALYTICS.PUBLIC.ORDERS_REVIEWS_SENTIMENT (
	ORDER_ID NUMBER(38,0),
	CUSTOMER_ID VARCHAR(16777216),
	DELIVERY_LOCATION GEOGRAPHY,
	DELIVERY_POSTCODE NUMBER(38,0),
	DELIVERY_DISTANCE_MILES FLOAT,
	RESTAURANT_FOOD_TYPE VARCHAR(16777216),
	RESTAURANT_LOCATION GEOGRAPHY,
	RESTAURANT_POSTCODE NUMBER(38,0),
	RESTAURANT_ID VARCHAR(16777216),
	REVIEW VARCHAR(16777216),
	SENTIMENT_ASSESSMENT VARCHAR(16777216),
	SENTIMENT_CATEGORIES VARCHAR(16777216)
);

COPY INTO advanced_analytics.public.orders_reviews_sentiment
FROM @advanced_analytics.public.aa_stage/food_delivery_reviews.csv
FILE_FORMAT = (FORMAT_NAME = csv_format_nocompression);
```

### Step 3. Data transformation

Now when you have a table with sentiment, you need to parse JSONs to store each component of the score into a separate column and convert the scoring provided by the LLM into numeric format, so you can easily visualize it. Run the following query:

```
CREATE OR REPLACE TABLE advanced_analytics.public.orders_reviews_sentiment_analysis AS
SELECT * exclude (food_cost, food_quality, food_delivery_time, sentiment) ,
         CASE
             WHEN sentiment = 'very positive' THEN 5
             WHEN sentiment = 'positive' THEN 4
             WHEN sentiment = 'neutral'
                  OR sentiment = 'mixed' THEN 3
             WHEN sentiment = 'negative' THEN 2
             WHEN sentiment = 'very negative' THEN 1
             ELSE NULL
         END sentiment_score ,
         CASE
             WHEN food_cost = 'very positive' THEN 5
             WHEN food_cost = 'positive' THEN 4
             WHEN food_cost = 'neutral'
                  OR food_cost = 'mixed' THEN 3
             WHEN food_cost = 'negative' THEN 2
             WHEN food_cost = 'very negative' THEN 1
             ELSE NULL
         END cost_score ,
         CASE
             WHEN food_quality = 'very positive' THEN 5
             WHEN food_quality = 'positive' THEN 4
             WHEN food_quality = 'neutral'
                  OR food_quality = 'mixed' THEN 3
             WHEN food_quality = 'negative' THEN 2
             WHEN food_quality = 'very negative' THEN 1
             ELSE NULL
         END food_quality_score ,
         CASE
             WHEN food_delivery_time = 'very positive' THEN 5
             WHEN food_delivery_time = 'positive' THEN 4
             WHEN food_delivery_time = 'neutral'
                  OR food_delivery_time = 'mixed' THEN 3
             WHEN food_delivery_time = 'negative' THEN 2
             WHEN food_delivery_time = 'very negative' THEN 1
             ELSE NULL
         END delivery_time_score
FROM
  (SELECT order_id ,
          customer_id ,
          delivery_location ,
          delivery_postcode ,
          delivery_distance_miles ,
          restaurant_food_type ,
          restaurant_location ,
          restaurant_postcode ,
          restaurant_id ,
          review ,
          try_parse_json(lower(sentiment_assessment)):classification::varchar AS sentiment ,
          try_parse_json(lower(sentiment_categories)):food_cost::varchar AS food_cost ,
          try_parse_json(lower(sentiment_categories)):food_quality::varchar AS food_quality ,
          try_parse_json(lower(sentiment_categories)):food_delivery_time::varchar AS food_delivery_time
   FROM advanced_analytics.public.orders_reviews_sentiment);
```

### Step 4. Data visualization

In this step, you will visualize the scoring results on the map. Open `Projects > Streamlit > + Streamlit App`. Give the new app a name, for example `Sentiment analysis - results`, and pick `ADVANCED_ANALYTICS.PUBLIC` as an app location.

<img src ='assets/geo_ml_12.png' width = 500>

Click on the packages tab and add `pydeck` and `branca` to the list of packages as our app will be using them. 

<img src ='assets/geo_ml_8.png' width = 450>

Then copy-paste the following code to the editor and click `Run`:

```
from snowflake.snowpark.context import get_active_session
from typing import Tuple
import branca.colormap as cm
import pandas as pd
import pydeck as pdk
import streamlit as st

@st.cache_data
def get_dataframe_from_raw_sql(query: str) -> pd.DataFrame:
    session = get_active_session()
    pandas_df = session.sql(query).to_pandas()
    return pandas_df

def get_h3_df_orders_quantiles(resolution: float, type_of_location: str) -> pd.DataFrame:
    df = get_dataframe_from_raw_sql(
        f"""SELECT
        H3_POINT_TO_CELL_STRING(to_geography({ type_of_location }), { resolution }) AS h3,
        round(count(*),2) as count
        FROM advanced_analytics.public.orders_reviews_sentiment_analysis
        GROUP BY 1""")

    quantiles = get_quantile_in_column(df, "COUNT")
    return df, quantiles

def get_h3_df_sentiment_quantiles(
    resolution: float, type_of_sentiment: str, type_of_location: str
) -> Tuple[pd.DataFrame, pd.core.series.Series]:
    df = get_dataframe_from_raw_sql(
        f""" SELECT 
        H3_POINT_TO_CELL_STRING(TO_GEOGRAPHY({ type_of_location }),{ resolution }) AS h3,
        round(AVG({ type_of_sentiment }),2) AS count
        FROM advanced_analytics.public.orders_reviews_sentiment_analysis
        WHERE { type_of_sentiment } IS NOT NULL 
        GROUP BY 1""")

    quantiles = get_quantile_in_column(df, "COUNT")
    df = df[(df["COUNT"] >= values[0]) & (df["COUNT"] <= values[1])]
    return df, quantiles

def get_h3_layer(layer_dataframe: pd.DataFrame, elevation_3d: bool = False,) -> pdk.Layer:
    highest_count_df = 0 if layer_dataframe is None else layer_dataframe["COUNT"].max()
    return pdk.Layer(
        "H3HexagonLayer",
        layer_dataframe,
        get_hexagon="H3",
        get_fill_color="COLOR",
        get_line_color="COLOR",
        auto_highlight=True,
        get_elevation=f"COUNT/{highest_count_df}",
        elevation_scale=10000 if elevation_3d else 0,
        elevation_range=[0, 300],
        pickable=True,
        opacity=0.5,
        extruded=True)

def get_quantile_in_column(
    quantile_dataframe: pd.DataFrame, column_name: str
) -> pd.core.series.Series:
    return quantile_dataframe[column_name].quantile([0, 0.25, 0.5, 0.75, 1])

def render_pydeck_chart(
    chart_quantiles: pd.core.series.Series, 
    chart_dataframe: pd.DataFrame, 
    elevation_3d: bool = False):
    colors = ["gray", "blue", "green", "yellow", "orange", "red"]
    color_map = cm.LinearColormap(
        colors,
        vmin=chart_quantiles.min(),
        vmax=chart_quantiles.max(),
        index=chart_quantiles)
    chart_dataframe["COLOR"] = chart_dataframe["COUNT"].apply(color_map.rgb_bytes_tuple)
    st.pydeck_chart(
        pdk.Deck(
            map_provider="mapbox",
            map_style="light",
            initial_view_state=pdk.ViewState(
                latitude=37.633,
                longitude=-122.284,
                zoom=7,
                pitch=50 if elevation_3d else 0,
                height=430),
            tooltip={"html": "<b>Value:</b> {COUNT}",
            "style": {"color": "white"}},
            layers=get_h3_layer(chart_dataframe, elevation_3d)))

st.set_page_config(layout="centered", initial_sidebar_state="expanded")
st.title("Reviews of Food Delivery Orders")

with st.sidebar:
    h3_resolution = st.slider("H3 resolution", min_value=6, max_value=9, value=7)
    type_of_locations = st.selectbox("Dimensions", ("DELIVERY_LOCATION", "RESTAURANT_LOCATION"), index=0)
    type_of_data = st.selectbox(
        "Measures",("ORDERS","SENTIMENT_SCORE","COST_SCORE","FOOD_QUALITY_SCORE","DELIVERY_TIME_SCORE"), index=0)
    if type_of_data != "ORDERS":
        values = st.slider("Select a range for score values", 0.0, 5.0, (0.0, 5.0))
        chckbox_3d_value = False
    else:
        chckbox_3d_value = st.checkbox("3D", key="chkbx_forecast", help="Renders H3 Hexagons in 3D")

if type_of_data != "ORDERS":
    df, quantiles = get_h3_df_sentiment_quantiles(h3_resolution, type_of_data, type_of_locations)

if type_of_data == "ORDERS":
    df, quantiles = get_h3_df_orders_quantiles(h3_resolution, type_of_locations)

st.image("https://sfquickstarts.s3.us-west-1.amazonaws.com/hol_geo_spatial_ml_using_snowflake_cortex/gradient.png")

render_pydeck_chart(quantiles, df, chckbox_3d_value)
```

After clicking `Run` button you will see the following UI:

<img src ='assets/geo_ml_13.png'>

You can start with the overall analysis of the order density. When you select "DELIVERY_LOCATION" as a Dimension and "ORDERS" as a Measure you'll see what areas correspond to the high number of orders. You can use scale 7 and zoom in to identify clear clusters of where the most deliveries are occurring. In this case you see most deliveries are in Santa Clara, San Jose, and the San Francisco Bay. In particular, the area on the San Francisco peninsula looks to be an area of interest. Zooming in further you can see a dense area of delivery orders. 

<img src ='assets/geo_ml_15.png'>

Using a finer H3 resolution, 8 shows how the delivery densities are distributed more finely. From this resolution, you can see the orders are concentrated in Daly City and proceed down to San Bruno. Additionally, in the North, the majority of the orders are coming from the stretch of the Sunset District to the Mission District.

<img src ='assets/geo_ml_16.png' width=300>

Now that you know where the majority of orders are coming from, let's analyze whether there are interesting differences in customer satisfaction depending on where they are located. Select DELIVERY LOCATION as a dimension and SENTIMENT_SCORE as a Measure to see the overall sentiment score that the Cortex LLM Complete Function generated. You can notice that the customers are mostly satisfied in the areas of Daly City down to San Jose, in the Santa Rosa area, and around Dublin. You also see that the area between these is mostly showing unhappy customers.

<img src ='assets/geo_ml_17.png' width=300>

In order to understand why customers in this area are unhappy, you analyze the aspect based sentiment results of the Cortex LLM Complete Function generated  for the categories of interest: food cost, delivery time, and the food quality. If you focus purely on the customers that were unhappy, you see that the primary reasons are food quality and food cost getting poor scores. Essentially, the food is not worth the cost and delivery time being fast does not make up for this. Check visualizations using the following combinations of parameters:

<img src ='assets/geo_ml_18.png'>

If you look at all H3 cells where food quality was high, the average sentiment score is also generally high. Again, you can see there are no cells where customers felt the food quality was above average in the greater Berkeley area. This could indicate either that high quality delivery food is uncommon or that the customers in these areas have higher expectations for delivery food.

You can also analyze what areas are getting higher scores for each of the categories and how it correlates with the overall sentiment scores for restaurants in each area.

> aside positive
>  The code from this quickstart can be reused for other industries, such as urban mobility, retail, finance, etc. Basically, any industry that involves providing a service with geo components and customer reviews.

## Conclusion And Resources

Duration: 4

Congratulations! You've successfully performed data engineering and data science tasks and trained a model to predict future taxi demand. Additionaly you practiced in creation of the LLM model to analyse sentiment analysis of the textual data. For each of those use cases you created a Streamlit application to analyse results.

We would love your feedback on this QuickStart Guide! Please submit your feedback using this [Feedback Form](https://forms.gle/tGDzTpu41huWFDXi9).

### What You Learned

* How to acquire data from the Snowflake Marketplace
* How to load data from external storage
* How to transform geospatial data using H3 and Time Series functions
* How to train models and predict results with Cortex ML
* How to use LLM for analysing textual data
* How to visualize data with Streamlit

### Related Resources
- [Geospatial Analytics for Retail with Snowflake and CARTO](https://quickstarts.snowflake.com/guide/geospatial_analytics_with_snowflake_and_carto_ny/index.html)
- [Geospatial Analysis using Geometry Data Type quickstart](https://quickstarts.snowflake.com/guide/geo_analysis_geometry/index.html?index=..%2F..index#0) 
- [Performance Optimization Techniques for Geospatial queries](https://quickstarts.snowflake.com/guide/geo_performance/index.html?index=..%2F..index#0)

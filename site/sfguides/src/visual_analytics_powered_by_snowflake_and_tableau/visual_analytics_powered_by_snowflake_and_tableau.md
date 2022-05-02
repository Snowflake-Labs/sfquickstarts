author: Chandra Nayak & Bailey Ferrari 
id: visual_analytics_powered_by_snowflake_and_tableau
summary: Visual Analytics Powered by Snowflake and Tableau
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Visual Analytics powered by Snowflake and Tableau
<!-- ------------------------ -->
## Overview 
Duration: 90

Join Snowflake and Tableau for an instructor-led hands-on lab to build governed, visual, and interactive analytics quickly and easily. 


The rest of this Snowflake Guide explains the steps of writing your own guide. 

### Prerequisites
- Familiarity with Snowflake and Tableau

### What You’ll Learn 
- Load unstructured data from IoT enabled bikes into Snowflake.
- Integrate and deliver multi-tenant tables and views in Snowflake to Tableau for real-time dashboarding.
- Use API integration to load geospatial data into Snowflake. 
- Securely connect to your Snowflake data by leveraging Virtual Connections and Centralized Row Level Security in Tableau.
- Build visual, intuitive, and interactive data visualizations powered by live data in Snowflake.
- Share production-ready Tableau dashboards by embedding the visualizations into your custom application.
- Showcase your data in the Snowflake Data Marketplace


### What You’ll Need 
- A [Snowflake](https://trial.snowflake.com/) Account 
- A [Tabelau Online](https://www.tableau.com/products/online/request-trial) Account


### What You’ll Build 
- Tableau Dashboard to present demand for cycles correlated with Weather

<!-- ------------------------ -->
## Snowflake Configuration
Duration: 5
1. Create a Snowflake Multi-cluster Trial account 

2. Login to your Snowflake Trial account

3. We will be using the new UI to get started but you can also switch over to the Classic Console if you would like. 

Classic UI: 
If you ever want to change from the new UI to the classic one, click on the home button and then Classic Console.


### New Login UI
![Snowflake Login](assets/new_snowflake_ui.png)

<!-- ------------------------ -->
## Tableau Configuration
Duration: 2
1. Login to your Tableau Online Trial account
 

<!-- ------------------------ -->

## Managing Unstructured Data
Duration: 2

### Download Demo SQL Script  
Look at the [Download workload.sql & add to Snowflake worksheet](https://github.com/mcnayak/sfquickstarts/blob/master/site/sfguides/src/visual_analytics_powered_by_snowflake_and_tableau/assets/MakeFinal_Workshop.sql).

![Snowflake Login](assets/Worksheet_1.png)

### Create Snowflake Objects

``` sql 
-- Create Database, Schema and Warehouse
create or replace database VHOL_DATABASE;
use database VHOL_DATABASE;

create or replace schema  VHOL_DATABASE.VHOL_SCHEMA;
use schema  VHOL_SCHEMA;


create or replace warehouse VHOL_WH WITH 
    WAREHOUSE_SIZE = 'MEDIUM' 
    WAREHOUSE_TYPE = 'STANDARD' 
    AUTO_SUSPEND = 60 
    AUTO_RESUME = TRUE 
    MIN_CLUSTER_COUNT = 1 
    MAX_CLUSTER_COUNT = 1 
    SCALING_POLICY = 'STANDARD';
  
-- Change Compute Size Instantly 
alter warehouse VHOL_WH SET WAREHOUSE_SIZE = 'LARGE';

alter warehouse VHOL_WH SET WAREHOUSE_SIZE = 'MEDIUM';

```

### Create Stage for hosting files
```sql
create or replace STAGE VHOL_STAGE;

show stages;

--External Stage on S3
create or replace STAGE VHOL_STAGE
    URL = 's3://snowflake-workshop-lab/citibike-trips/json';

--Lists Files on the S3 Bucket
list @VHOL_STAGE/;

CREATE FILE FORMAT "JSON" TYPE=JSON COMPRESSION=GZIP;

show File Formats;
```

### Query JSON Data
``` sql
-- Query individual columns from first 100 rows 
select $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
from @VHOL_STAGE/2016-08-01/data_01a304b5-0601-4bbe-0045-e8030021523e_005_6_0.json.gz limit 100;

-- Query all columns from a single row
SELECT * FROM @VHOL_STAGE/2016-08-01/data_01a304b5-0601-4bbe-0045-e8030021523e_005_6_0.json.gz (file_format=>JSON)  limit 1;

-- Create a table with Variant column
create or replace table vhol_trips
  (tripid number autoincrement, 
   v variant)
  change_tracking = true;

-- Load JSON data into Variant column
copy into vhol_trips (v) from 
  (SELECT * FROM @VHOL_STAGE/2016-08-01/data_01a304b5-0601-4bbe-0045-e8030021523e_005_6_0.json.gz (file_format=>JSON));
```

### Build Relational Views on JSON
``` sql 

--- Extract JSON data as relational columns
create or replace view vhol_trips_vw 
  as select 
    tripid,
    v:STARTTIME::timestamp_ntz starttime,
    v:ENDTIME::timestamp_ntz endtime,
    datediff('minute', starttime, endtime) duration,
    v:START_STATION_ID::integer start_station_id,
    v:END_STATION_ID::integer end_station_id,
    v:BIKE.BIKEID::string bikeid,
    v:BIKE.BIKE_TYPE::string bike_type,
    v:RIDER.RIDERID::integer riderid,
    v:RIDER.FIRST_NAME::string || ' ' || v:RIDER.LAST_NAME::string rider_name,
    to_date(v:RIDER.DOB::string, 'YYYY-MM-DD') dob,
    v:RIDER.GENDER::string gender,
    v:RIDER.MEMBER_TYPE::string member_type,
    v:RIDER.PAYMENT.TYPE::string payment,
    ifnull(v:RIDER.PAYMENT.CC_TYPE::string, 
      v:RIDER.PAYMENT.PHONE_TYPE::string) payment_type,
    ifnull(v:RIDER.PAYMENT.PHONE_NUM::string,
      v:RIDER.PAYMENT.CC_NUM::string) payment_num
  from vhol_trips;

-- avg trip duration 
select date_trunc('hour', starttime) as "date",
count(*) as "num trips",
avg(duration)/60 as "avg duration (mins)" 
from vhol_trips_vw
group by 1 order by 1;

--trips by day
select
    dayname(starttime) as "day of week",
    count(*) as "num trips"
from vhol_trips_vw
group by 1 order by 2 desc;

``` 

### 
<!-- ------------------------ -->
## DevOps in Snowflake

### Clone Table
``` sql 
create table vhol_trips_dev clone vhol_trips;

select * from vhol_trips_dev limit 1;
```
### Drop and Undrop Table
``` sql
drop table vhol_trips_dev; 

select count(*) from vhol_trips_dev limit 1;

--thank god for resurrection
undrop table vhol_trips_dev;

select count(*) from vhol_trips_dev limit 1;

```
<!-- ------------------------ -->

<!-- ------------------------ -->
## Add Weather Data from Snowflake Marketplace

### Click on Data Marketplace and type WEATHER in Search Snowflake Marketplace toolbar

![Search Dataset](assets/Weather_DM_1.png)

### Set database name to WEATHER, grant access to PUBLIC role

![Add Database and Role](assets/Weather_DM_2.png)

### Data Ready to Query 

![Click Done](assets/Weather_DM_3.png)

### Convert Kelvin to Celcius
``` sql
-- UDF to convert Kelvin to Celcius
create or replace function degFtoC(k float)
returns float
as
$$
  truncate((k - 32) * 5/9, 2)
$$; 

```
###

### Query Weather data
``` sql
desc view weather.standard_tile.history_day;

-- Is there rain in the forecast that may impact cycling in a specific area 
SELECT COUNTRY,DATE_VALID_STD,TOT_PRECIPITATION_IN,tot_snowfall_in AS SNOWFALL,  POSTAL_CODE, DATEDIFF(day,current_date(),DATE_VALID_STD) AS DAY, HOUR(TIME_INIT_UTC) AS HOUR  FROM WEATHER.STANDARD_TILE.FORECAST_DAY WHERE POSTAL_CODE='32333' AND DAY=7;
```
### Is there precipitation or snowfall in NY zipcodes
``` sql
create or replace view vhol_weather_vw as
  select 'New York'                                   state,
    date_valid_std                                    observation_date,
    doy_std                                           day_of_year,
    avg(min_temperature_air_2m_f)                     temp_min_f,
    avg(max_temperature_air_2m_f)                     temp_max_f,
    avg(avg_temperature_air_2m_f)                     temp_avg_f,
    avg(degFtoC(min_temperature_air_2m_f))            temp_min_c,
    avg(degFtoC(max_temperature_air_2m_f))            temp_max_c,
    avg(degFtoC(avg_temperature_air_2m_f))            temp_avg_c,
    avg(tot_precipitation_in)                         tot_precip_in,
    avg(tot_snowfall_in)                              tot_snowfall_in,
    avg(tot_snowdepth_in)                             tot_snowdepth_in,
    avg(avg_wind_direction_100m_deg)                  wind_dir,
    avg(avg_wind_speed_100m_mph)                      wind_speed_mph,
    truncate(avg(avg_wind_speed_100m_mph * 1.61), 1)  wind_speed_kph,
    truncate(avg(tot_precipitation_in * 25.4), 1)     tot_precip_mm,
    truncate(avg(tot_snowfall_in * 25.4), 1)          tot_snowfall_mm,
    truncate(avg(tot_snowdepth_in * 25.4), 1)         tot_snowdepth_mm
  from weather.standard_tile.history_day
  where postal_code in ('10257', '10060', '10128', '07307', '10456')
  group by 1, 2, 3;
  
select * from vhol_weather_vw limit 10;

```
<!-- ------------------------ -->

<!-- ------------------------ -->
## Enrich with Geospatial Station Data 
We just have station_id, so let's get geospatial data to locate those stations on map

###  Access data from AWS API Gateway
``` sql  
-- Integration to AWS API Gateway 
create or replace api integration fetch_http_data
  api_provider = aws_api_gateway
  api_aws_role_arn = 'arn:aws:iam::148887191972:role/ExecuteLambdaFunction'
  enabled = true
  api_allowed_prefixes = ('https://dr14z5kz5d.execute-api.us-east-1.amazonaws.com/prod/fetchhttpdata');

```

``` sql 
-- External Function call to Lambda to download data 

create or replace external function fetch_http_data(v varchar)
    returns variant
    api_integration = fetch_http_data
    as 'https://dr14z5kz5d.execute-api.us-east-1.amazonaws.com/prod/fetchhttpdata';

```
###

### Flatten JSON data received from API's

Geospatial data is available in a nested json array, let's flatten that 

``` sql 
-- use lateral flatten function to flatten nested JSON
create or replace table vhol_spatial_data as
with gbfs as (
  select $1 type, 
     fetch_http_data($2) payload
  from (values
    ('region', 'https://gbfs.citibikenyc.com/gbfs/en/system_regions.json'),
    ('station', 'https://gbfs.citibikenyc.com/gbfs/en/station_information.json'),
    ('neighborhood', 'https://snowflake-demo-stuff.s3.amazonaws.com/neighborhoods.geojson'))
  )
  select type, value v
    from gbfs, lateral flatten (input => payload:response.data.regions)
    where type = 'region'
  union all
  select type, value v
    from gbfs, lateral flatten (input => payload:response.data.stations)
    where type = 'station'
  union all
  select type, value v
    from gbfs, lateral flatten (input => payload:response.features)
    where type = 'neighborhood';
    
    
    select * from vhol_spatial_data;
  ```

###

<!-- ------------------------ -->

<!-- ------------------------ -->
## Correlate Trips, Weather and Geospatial Data

### Combine station data with geospatial data
``` sql 
create or replace table vhol_stations as with 
  -- extract the station data
    s as (select 
        v:station_id::number station_id,
        v:region_id::number region_id,
        v:name::string station_name,
        v:lat::float station_lat,
        v:lon::float station_lon,
        st_point(station_lon, station_lat) station_geo,
        v:station_type::string station_type,
        v:capacity::number station_capacity,
        v:rental_methods rental_methods
    from vhol_spatial_data
    where type = 'station'),
    -- extract the region data
    r as (select
        v:region_id::number region_id,
        v:name::string region_name
    from vhol_spatial_data
    where type = 'region'),
    -- extract the neighborhood data
    n as (select
        v:properties.neighborhood::string nhood_name,
        v:properties.borough::string borough_name,
        to_geography(v:geometry) nhood_geo
    from vhol_spatial_data
    where type = 'neighborhood')   
-- join it all together using a spatial join
select station_id, station_name, station_lat, station_lon, station_geo,
  station_type, station_capacity, rental_methods, region_name,
  nhood_name, borough_name, nhood_geo
from s inner join r on s.region_id = r.region_id
       left outer join n on st_contains(n.nhood_geo, s.station_geo);

-- query station data 
select * from vhol_stations;
``` 

### Combine Trips, Geospatial and Stations 

Let's combine trip data with geospatial to identify popular routes
```sql
create or replace view vhol_trips_stations_vw as (
  with
    t as (select * from vhol_trips_vw),
    ss as (select * from vhol_stations),
    es as (select * from vhol_stations)
  select 
    t.tripid, 
    starttime, endtime, duration, start_station_id,
    ss.station_name start_station, ss.region_name start_region,
    ss.borough_name start_borough, ss.nhood_name start_nhood, 
    ss.station_geo start_geo, ss.station_lat start_lat, ss.station_lon start_lon,
    ss.nhood_geo start_nhood_geo, 
    end_station_id, es.station_name end_station, 
    es.region_name end_region, es.borough_name end_borough, 
    es.nhood_name end_nhood, es.station_geo end_geo, 
    es.station_lat end_lat, es.station_lon end_lon,
    es.nhood_geo end_nhood_geo,
    bikeid, bike_type, dob, gender, member_type, payment, payment_type, payment_num
  from t 
    left outer join ss on start_station_id = ss.station_id
    left outer join es on end_station_id = es.station_id); 

```

###  

### Combine Trip, Geospatial, Stations and Weather data
```sql 
create or replace view vhol_trips_stations_weather_vw as (
  select t.*, temp_avg_c, temp_avg_f,
         wind_dir, wind_speed_mph, wind_speed_kph
  from vhol_trips_stations_vw t 
       left outer join vhol_weather_vw w on date_trunc('day', starttime) = observation_date);


-- let's query the integrated data view
select * from vhol_trips_stations_vw limit 200;
select * from vhol_trips_stations_weather_vw limit 200;

```

###

### 

<!-- ------------------------ -->

<!-- ------------------------ -->
## Secure Data Sharing
```  
create or replace table tenant (
    tenant_id number,
    tenant_description string,
    tenant_account string
);

--add tenant for your account
insert into tenant values (
    1, 'My Account', current_account()
);

--select
select * from tenant;

--map tenant to subscribed station beacons
create or replace table tenant_stations (
    tenant_id number,
    station_id number
);

--values
insert into tenant_stations values
    (1, 212),
  (1, 216),
  (1, 217),
  (1, 218),
  (1, 223),
  (1, 224),
  (1, 225),
  (1, 228),
  (1, 229),
  (1, 232),
  (1, 233),
  (1, 236),
  (1, 237),
  (1, 238),
  (1, 239),
  (1, 241),
  (1, 242),
  (1, 243),
  (1, 244),
  (1, 245),
  (1, 247),
  (1, 248),
  (1, 249),
  (1, 250),
  (1, 251),
  (1, 252),
  (1, 253),
  (1, 254),
  (1, 255),
  (1, 257),
  (1, 258),
  (1, 259),
  (1, 260),
  (1, 261),
  (1, 262),
  (1, 263),
  (1, 264),
  (1, 265),
  (1, 266),
  (1, 267),
  (1, 268),
  (1, 270),
  (1, 271),
  (1, 274),
  (1, 275),
  (1, 276),
  (1, 278),
  (1, 279),
  (1, 280),
  (1, 281),
  (1, 282),
  (1, 284),
  (1, 285),
  (1, 289),
  (1, 290),
  (1, 291),
  (1, 293),
  (1, 294),
  (1, 295),
  (1, 296),
  (1, 297),
  (1, 298)
;

```

### Enabling Row Level Access Policy 
```
--select *
select * from tenant_stations;

--select
set tenant_sv = '1';

select * from vhol_trips_vw
join tenant_stations
    on vhol_trips_vw.start_station_id = tenant_stations.station_id
join tenant
    on tenant_stations.tenant_id = tenant.tenant_id
where
    tenant.tenant_id = $tenant_sv
limit 100;

--select bogus
set tenant_sv = '0';

select * from vhol_trips_vw
join tenant_stations
    on vhol_trips_vw.start_station_id = tenant_stations.station_id
join tenant
    on tenant_stations.tenant_id = tenant.tenant_id
where
    tenant.tenant_id = $tenant_sv
limit 100;

```

### Create Secure Objects to Share 
```
--secure view
create or replace secure view  vhol_trips_secure as
(select --tripduration, 
 starttime, endtime, start_station_id, bikeid, tenant.tenant_id from vhol_trips_vw
join tenant_stations
    on vhol_trips_vw.start_station_id = tenant_stations.station_id
join tenant
    on tenant_stations.tenant_id = tenant.tenant_id
where
    tenant.tenant_account = current_account());

--current account?
select current_account();

--select secure view

select * from vhol_trips_secure limit 100;

```

### Create Reader Account 
```
--create a reader account for your tenant
show managed accounts;
DROP MANAGED ACCOUNT IMP_CLIENT;
CREATE MANAGED ACCOUNT IMP_CLIENT
    admin_name='USER',
    admin_password='P@ssword123',
    type=reader,
    COMMENT='Testing';
-- Take a note of the Account Name and the URL 

--add tenant for your big important client via a reader account
insert into tenant values (
    1, 'Big Important Client, Wink Wink', 'IMP_CLIENT'
);

--simulate your tenant
alter session set simulated_data_sharing_consumer = 'IMP_CLIENT';

--select secure view as your tenant
select * from vhol_trips_secure limit 100;

--unsimulate your tenant
alter session unset simulated_data_sharing_consumer;

--are you sure?
select count(*) from vhol_trips_secure;
```

### Grant Share Access to Reader 
```
--create share and share to reader account
CREATE OR REPLACE SHARE VHOL_SHARE COMMENT='Creating my Share to Share with my Reader';
GRANT USAGE ON DATABASE VHOL_DATABASE TO SHARE VHOL_SHARE;
GRANT USAGE ON SCHEMA VHOL_SCHEMA TO SHARE VHOL_SHARE;
GRANT SELECT ON VIEW VHOL_TRIPS_SECURE TO SHARE VHOL_SHARE;
DESC SHARE VHOL_SHARE;

ALTER SHARE VHOL_SHARE ADD ACCOUNTS = PGA86878;

SHOW SHARES LIKE 'VHOL_SHARE';
show managed accounts;
select  $1 as NAME ,$4 AS LOCATOR,$6 as URL FROM table (result_scan(last_query_id()));

```

###

<!-- ------------------------ -->

<!-- ------------------------ -->
## Data Consumer Access
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

<!-- ------------------------ -->

<!-- ------------------------ -->
## Conclusion
Congratulations! you have completed the lab.

In this lab we captured semi-structured data coming from NewYork Citibikes, enriched that data with geospatial data, and weather data from  Snowflake Data marketplace data to find correlation between demand for bicycles and weather. We visualized the data using Tableau to quickly arrive at relevant insights. 

### Video on the Demo
[Youtube - Video on the Demo](https://www.youtube.com/watch?v=9zMtimcooxo)


### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### 
<button>
  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Video on the Demo](https://www.youtube.com/watch?v=9zMtimcooxo)


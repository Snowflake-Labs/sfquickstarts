

-- This SQL file is for the Hands On Lab Guide for the 30-day free Snowflake trial account
-- The numbers below correspond to the sections of the Lab Guide in which SQL is to be run in a Snowflake worksheet
-- Modules 1 and 2 of the Lab Guide have no SQL to execute


/* *********************************************************************************** */
/* *** MODULE 3  ********************************************************************* */
/* *********************************************************************************** */

-- 3.1.4

create table trips 
(tripduration integer,
  starttime timestamp,
  stoptime timestamp,
  start_station_id integer,
  start_station_name string,
  start_station_latitude float,
  start_station_longitude float,
  end_station_id integer,
  end_station_name string,
  end_station_latitude float,
  end_station_longitude float,
  bikeid integer,
  membership_type string,
  usertype string,
  birth_year integer,
  gender integer);

-- 3.2 

create or replace stage citibike_trips url = 's3://snowflake-workshop-lab/citibike-trips';

-- 3.2.4

list @citibike_trips;

-- 3.3

create or replace file format csv type='csv'
  compression = 'auto' field_delimiter = ',' record_delimiter = '\n'
  skip_header = 0 field_optionally_enclosed_by = '\042' trim_space = false
  error_on_column_count_mismatch = false escape = 'none' escape_unenclosed_field = '\134'
  date_format = 'auto' timestamp_format = 'auto' null_if = ('');

/* *********************************************************************************** */
/* *** MODULE 4  ********************************************************************* */
/* *********************************************************************************** */

-- 4.2.2

copy into trips from @citibike_trips file_format=csv;

-- 4.2.4

truncate table trips;

-- 4.2.7

copy into trips from @citibike_trips file_format=csv;

-- 4.3

create or replace warehouse analytics_wh with warehouse_size = 'large' warehouse_type = 'standard' 
  auto_suspend = 600 auto_resume = true;

/* *********************************************************************************** */
/* *** MODULE 5  ********************************************************************* */
/* *********************************************************************************** */

-- 5.1.1

use role sysadmin;
use warehouse analytics_wh;
use database citibike;
use schema public;

-- 5.1.2

select * from trips limit 20;

-- 5.1.3

select date_trunc('hour', starttime) as "date",
count(*) as "num trips",
avg(tripduration)/60 as "avg duration (mins)", 
avg(haversine(start_station_latitude, start_station_longitude, end_station_latitude, end_station_longitude)) as "avg distance (km)" 
from trips
group by 1 order by 1;

-- 5.1.4

select date_trunc('hour', starttime) as "date",
count(*) as "num trips",
avg(tripduration)/60 as "avg duration (mins)", 
avg(haversine(start_station_latitude, start_station_longitude, end_station_latitude, end_station_longitude)) as "avg distance (km)" 
from trips
group by 1 order by 1;

-- 5.1.5

select monthname(starttime) as "month",
    count(*) as "num trips"
from trips
group by 1 order by 2 desc;
    

-- 5.2.1

create table trips_dev clone trips;

/* *********************************************************************************** */
/* *** MODULE 6  ********************************************************************* */
/* *********************************************************************************** */

-- 6.1.1

create database weather;

-- 6.1.2

use role sysadmin;
use warehouse compute_wh;
use database weather;
use schema public;

-- 6.1.3

create table json_weather_data (v variant);

-- 6.2.1

create stage nyc_weather url = 's3://snowflake-workshop-lab/weather-nyc';

-- 6.2.2 

list @nyc_weather;

-- 6.3.1

copy into json_weather_data 
from @nyc_weather 
file_format = (type=json);

-- 6.3.2

select * from json_weather_data limit 10;

-- 6.4.1

create view json_weather_data_view as
select
  v:time::timestamp as observation_time,
  v:city.id::int as city_id,
  v:city.name::string as city_name,
  v:city.country::string as country,
  v:city.coord.lat::float as city_lat,
  v:city.coord.lon::float as city_lon,
  v:clouds.all::int as clouds,
  (v:main.temp::float)-273.15 as temp_avg,
  (v:main.temp_min::float)-273.15 as temp_min,
  (v:main.temp_max::float)-273.15 as temp_max,
  v:weather[0].main::string as weather,
  v:weather[0].description::string as weather_desc,
  v:weather[0].icon::string as weather_icon,
  v:wind.deg::float as wind_dir,
  v:wind.speed::float as wind_speed
from json_weather_data
where city_id = 5128638;

-- 6.4.4

select * from json_weather_data_view
where date_trunc('month',observation_time) = '2018-01-01' 
limit 20;

-- 6.5.1

select weather as conditions
    ,count(*) as num_trips
from citibike.public.trips 
left outer join json_weather_data_view
    on date_trunc('hour', observation_time) = date_trunc('hour', starttime)
where conditions is not null
group by 1 order by 2 desc;


/* *********************************************************************************** */
/* *** MODULE 7  ********************************************************************* */
/* *********************************************************************************** */

-- 7.1.1

drop table json_weather_data;

-- 7.1.2

select * from json_weather_data limit 10;

-- 7.1.3

undrop table json_weather_data;

-- 7.2.1

use database citibike;
use schema public;

-- 7.2.2

update trips set start_station_name = 'oops';

-- 7.2.3

select start_station_name as station
    ,count(*) as rides
from trips
group by 1
order by 2 desc
limit 20;


-- 7.2.4

set query_id = 
(select query_id from 
table(information_schema.query_history_by_session (result_limit=>5)) 
where query_text like 'update%' order by start_time limit 1);

-- 7.2.5
create or replace table trips as
(select * from trips before (statement => $query_id));
        
-- 7.2.6

select start_station_name as "station"
    ,count(*) as "rides"
from trips
group by 1
order by 2 desc
limit 20;


/* *********************************************************************************** */
/* *** MODULE 8  ********************************************************************* */
/* *********************************************************************************** */

-- 8.1.1

use role accountadmin; 

-- 8.1.3 (NOTE - enter your unique user name into the second row below)

create role junior_dba;
grant role junior_dba to user jeremyp;--YOUR_USER_NAME_GOES HERE;

-- 8.1.4

use role junior_dba;

-- 8.1.6

use role accountadmin;
grant usage on database citibike to role junior_dba;
grant usage on database weather to role junior_dba;

-- 8.1.7

use role junior_dba;


summary: How to Stream data into Snowflake to power Data Apps
id: stream_data_into_snowflake_for_Data_Apps
categories: Data Application
tags: snowpipe
status: Draft
Feedback Link: https://developers.snowflake.com

# How to Stream data into Snowflake to power Data Apps
<!-- ------------------------ -->
## Overview
Duration: 1

### What You will Learn
* Create stages, databases, tables and warehouses
* Create pipe for auto ingestion of data
* Auto Ingest structured and semi-structured datas
* Query data including joins between tables

### Prerequisites
* Access to Snowflake account
* Access to your own AWS account
* Basic knowledge of SQL, database concepts and objects
* Familiarity with CSV comma-delimited files and JSON semi-structured datas

<!-- ------------------------ -->
## Setup & Configuration
Duration: 10

In this Snowlab, we will be using AWS S3 for the files to ingest from and SQS notification for the notification method.

### Configuring Secure Access to AWS S3
Please configure Snowflake secure access to the S3 bucket that will store your data files by following the 5 step instructions in the specified documentation section [HERE](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-s3.html#configuring-secure-access-to-cloud-storage)
**Please note the S3 bucket that you plan to use and have configured along with the Storage Integration Name.

### Creating a New S3 Event Notification to Automate Snowpipe
#### Set context in the Worksheet
```
  use role sysadmin;
  create or replace warehouse pipe_wh with warehouse_size = 'small' warehouse_type = 'standard' auto_suspend = 120 auto_resume = true;
  use warehouse pipe_wh;
  create database if not exists citibike;
  use schema citibike.public;
```

#### Create a Stage
##### Create stage for Structured Trips data (Please create folders '/snowpipe/trips/' in the bucket)
```
  create or replace stage pipe_data_trips
  url = 's3://<your-bucket-name>/snowpipe/trips/'
  storage_integration = <your-storage-integration>
  file_format=(type=csv);
```

##### Create stage for Semi-Structured Weather JSON data (Please create folders '/snowpipe/weather/' in the bucket)
```
  create or replace stage pipe_data_weather
  url = 's3://<your-bucket-name>/snowpipe/weather/'
  storage_integration = <your-storage-integration>
  file_format=(type=json);
```

#### Create the tables
##### Create table trips_stream
```
  create or replace table trips_stream (
    tripduration integer,
    starttime timestamp,
    stoptime timestamp,
    start_station_id integer,
    end_station_id integer,
    bikeid integer,
    usertype string,
    birth_year integer,
    gender integer,
    program_id integer);
```

##### Create table json_weather_stream
```
  create or replace table json_weather_stream (
    v variant,
    t timestamp);
```

#### Create Pipe with Auto-Ingest Enabled
##### Create the trips pipe

```
  create or replace pipe trips_pipe
  auto_ingest=true
  as
  copy into trips_stream from @pipe_data_trips/;
```

##### Create the weather pipe
```
  create or replace pipe weather_pipe
  auto_ingest=true
  as
  copy into json_weather_stream from
  (select $1, convert_timezone('UTC', 'US/Eastern', $1:time::timestamp_ntz)
  from @pipe_data_weather/);
```
#### Configure Event Notifications
- Execute the SHOW PIPES command:
```
  show pipes;
```
Note the ARN of the SQS queue for the stage in the notification_channel column. Copy the ARN to a convenient location.

- Log into the Amazon S3 console

- Configure an event notification for your S3 bucket using the instructions provided in the [Amazon S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/user-guide/enable-event-notifications.html). Complete the fields as follows:

  * Name: Name of the event notification (e.g. Auto-ingest Snowflake).
  * Events: Select the ObjectCreate (All) option.
  * Send to: Select SQS Queue from the dropdown list.
  * SQS: Select Add SQS queue ARN from the dropdown list.
  * SQS queue ARN: Paste the SQS queue name from the SHOW PIPES output.

Snowpipe with auto-ingest is now configured!
When new data files are added to the S3 bucket, the event notification informs Snowpipe to load them into the target table defined in the pipe.

<!-- ------------------------ -->
## Test Snowpipe by uploading sample data files into the bucket folders
Duration: 2

### Now upload the sample trips CSV files into S3 : 's3://<your-bucket-name>/snowpipe/trips/'
[Download Sample Files](assets/trips_stream.zip)
### Now upload the sample weather JSON files into S3 : 's3://<your-bucket-name>/snowpipe/weather/
[Download Sample Files](assets/json_weather_stream.zip)

<!-- ------------------------ -->
## Check pipe status & copy history to confirm data auto-ingest
Duration: 2

Please give Snowpipe couple minutes after upload process to auto-ingest the data files.

###Check pipe status
```
  select system$pipe_status('trips_pipe');
```
```
  select system$pipe_status('weather_pipe');
```

### Check pipe status
```
  select *
  from table(information_schema.copy_history(table_name=>'TRIPS_STREAM', start_time=>dateadd('hour', -1, CURRENT_TIMESTAMP())));
```
```
  select *
  from table(information_schema.copy_history(table_name=>'JSON_WEATHER_STREAM', start_time=>dateadd('hour', -1, CURRENT_TIMESTAMP())));
```

<!-- ------------------------ -->
## Run Query against the loaded table data
Duration: 3
### Let us first check table row count
```
  select count(*) from trips_stream;
```
```  
  select count(*) from json_weather_stream;
```

### Now let us check table data
```
  select * from trips_stream limit 10;
```
```  
  select * from json_weather_stream limit 10;
```

### Now we can Unwrap complex structures such as arrays via FLATTEN to compare the most common weather in different cities
```
  select value:main::string as conditions
    ,sum(iff(v:city.name::string='New York',1,0)) as nyc_freq
    ,sum(iff(v:city.name::string='Seattle',1,0)) as seattle_freq
    ,sum(iff(v:city.name::string='San Francisco',1,0)) as san_fran_freq
    ,sum(iff(v:city.name::string='Miami',1,0)) as miami_freq
    ,sum(iff(v:city.name::string='Washington, D. C.',1,0)) as wash_freq
    from json_weather_stream w,
    lateral flatten (input => w.v:weather) wf
    where v:city.name in ('New York','Seattle','San Francisco','Miami','Washington, D. C.')
    group by 1;
```

### Let us Create a view which joins the structured Trips data with the semi-structured Weather data together & query the View
```
  create or replace view trips_weather_vw as (
    with
      t as (
        select date_trunc(hour, starttime) starttime, date_trunc(hour, stoptime) stoptime,
          tripduration, bikeid, usertype, birth_year, gender
        from trips_stream),
      w as (
        select date_trunc(hour, t)                observation_time
          ,avg(v:wind.deg::float)                 wind_dir
          ,avg(v:wind.speed::float)               wind_speed
        from json_weather_stream
        where v:city.id::int = 5128638
        group by 1)
    select *
    from t left outer join w on t.starttime = w.observation_time);
```
```
    select * from trips_weather_vw where wind_dir is not NULL;
```

<!-- ------------------------ -->
##Conclusion
Duration: 1

This is just the surface of what you can do with Snowflake. For all your specific questions, be sure to check out the [full documentation](https://docs.snowflake.com/en/).

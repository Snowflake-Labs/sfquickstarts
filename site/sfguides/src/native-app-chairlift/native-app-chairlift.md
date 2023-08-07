author: 
id: native-app-chairlift
summary: This Snowflake Native Application sample demonstrates how a ChairLift manufacture can use a native app to share data with their consumers, analyze equipment data collected on the consumer side, and generate warnings based on such analysis.
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Apps 

# Build a Native App for Chairlift Manufacturing
<!-- ------------------------ -->
## Introduction
Duration: 1

In this Quickstart, you'll build a Snowflake Native Application that demonstrates how a chair lift manufacturer can use a Native App to share data with their consumers, analyze equipment data collected from consumers, and generate warnings based on this data.

You'll build the app as if you were the app provider (i.e., the chair lift manufacturer), but you'll also load data into your Snowflake account to mimic a fictional Snowflake environment that a consumer (i.e., an end user) of the app would have in their Snowflake account. Let's get started!

![Sensor data](assets/sensor-data.png)


### What You’ll Learn 

- How to create a native app application package
- How to create a new version of the native app
- How to install and run a Native App in a consumer account

### What You’ll Need

> aside negative
> 
> **Important**
> Native Apps are currently only widely available on AWS.  Ensure your Snowflake deployment or trial account uses AWS as the cloud provider. Native Apps will be available on other major cloud providers soon.

- A Snowflake account ([trial](https://signup.snowflake.com/developers), or otherwise). See note above on AWS as cloud provider for the deployment.

### What You’ll Build 

- A Snowflake Native App

<!-- ------------------------ -->
## Clone repository
Duration: 3

To create the Snowflake Native Application, start by cloning the following GitHub repository:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-native-apps-chairlift.git
```

This repository contains all of the code necessary to build the native app. Recall that for this native app, we'll play the role of the app provider and the app consumer. Let's explore the directory structure:

```plaintext
sfguide-native-apps-chairlift/
├─ consumer/
│  ├─ install-app.sql
├─ prepare/
│  ├─ consumer-data.sql
│  ├─ consumer-roles.sql
│  ├─ provider-data.sql
│  ├─ provider-roles.sql
├─ provider/
│  ├─ create-package.sql
├─ src/
│  ├─ README.md
│  ├─ manifest.yml
│  ├─ setup.sql
│  ├─ ui/
├─ LEGAL.md
├─ LICENSE
├─ README.md
```

Here's an overview of the directory:

**src/** 

- the **src/** directory is used to store all of our various source code, including stored procedures, user-defined functions (UDFs), our Streamlit application (in the **ui/** folder), and our installation script `setup.sql`. It also includes **manifest.yml**, which is a file with metadata about the application and with references to Snowflake objects (tables) that the application will need access to when running.

**prepare/** 

- the **prepare/**  directory contains several scripts to prepare the Snowflake account from the provider side and from the consumer side, specifically creation of roles, granting of privileges, and data loading. We'll execute these scripts before building the native app.

**consumer/** 

- the **consumer/**  directory contains a SQL script to install the native app in the account and grant appropriate privileges.

**provider/** 

- the **provider/**  directory contains a SQL script to create the application package and grant privileges on provider data.
<!-- ------------------------ -->
## Set up account roles
Duration: 2

You'll first need to configure your Snowflake account by creating some roles and granting certain permissions. You'll create provider roles and permissions, as well as consumer roles and permissions. You'll only need to execute these scripts once.

**Execute prepare/provider-role.sql**

Open a SQL worksheet in Snowsight and execute the following script:

```sql
-- create provider role
create role if not exists chairlift_provider;
grant role chairlift_provider to role accountadmin;
grant create application package on account to role chairlift_provider;
grant create database on account to role chairlift_provider;

-- ensure a warehouse is usable by provider
create warehouse if not exists chairlift_wh;
grant usage on warehouse chairlift_wh to role chairlift_provider;
```

**Execute prepare/consumer-roles.sql**

Open a SQL worksheet in Snowsight and execute the following script:

```sql
-- create consumer role
create role if not exists chairlift_admin;
create role if not exists chairlift_viewer;
grant role chairlift_admin to role accountadmin;
grant role chairlift_viewer to role accountadmin;
grant create database on account to role chairlift_admin;
grant create application on account to role chairlift_admin;
grant execute task, execute managed task on account to role chairlift_admin with grant option;
grant role chairlift_viewer to role chairlift_admin;

-- ensure a warehouse is usable by consumer
grant usage on warehouse chairlift_wh to role chairlift_admin;
grant usage on warehouse chairlift_wh to role chairlift_viewer;
```


<!-- ------------------------ -->
## Prepare objects in account
Duration: 2

Next, run the following scripts to setup some databases, schemas, and tables needed to mimic a production environment. We'll create these objects from the perspective of both the provider and the consumer. You'll only need to execute these scripts once.

**Execute prepare/provider-data.sql**

Open a SQL worksheet in Snowsight and execute the following script:

```sql
use role chairlift_provider;
use warehouse chairlift_wh;

create database if not exists chairlift_provider_data;
use database chairlift_provider_data;
create schema if not exists core;
use schema core;

-- Sensor types with reading min range, max ranges, service intervals and lifetime of the sensor.
create or replace table chairlift_provider_data.core.sensor_types (
    id int,
    name varchar,
    min_range int,
    max_range int,
    service_interval_count int,
    service_interval_unit varchar,
    lifetime_count int,
    lifetime_unit varchar,
    primary key (id)
);

insert into chairlift_provider_data.core.sensor_types values
    (1, 'Brake Temperature', -40, 40, 6, 'month', 5, 'year'),
    (2, 'Current Load', 20000, 50000, 3, 'month', 5, 'year'),
    (3, 'Bull-wheel RPM', 4000, 5000, 1, 'month', 1, 'year'),
    (4, 'Motor RPM', 2000, 2500, 1, 'month', 1, 'year'),
    (5, 'Motor Voltage', 110, 130, 2, 'month', 5, 'year'),
    (6, 'Current Temperature', -40, 40, 4, 'month', 5, 'year'),
    (7, 'Rope Tension', 70, 100, 3, 'month', 5, 'year'),
    (8, 'Chairlift Load', 50, 250, 3, 'month', 2, 'year'),
    (9, 'Chairlift Vibration', 30, 100, 3, 'month', 3, 'year');
```

**Execute prepare/consumer-data.sql**

Open a SQL worksheet in Snowsight and execute the following script:

```sql
use role chairlift_admin;
use warehouse chairlift_wh;

-- consumer data: streaming readings from sensors on their ski lift machines.
create database if not exists chairlift_consumer_data;
use database chairlift_consumer_data;
create schema if not exists data;
use schema data;

-- what machines (chairlifts and stations) exist in the consumer's ski resort?
create or replace table machines (
    uuid varchar,
    name varchar,
    latitude double,
    longitude double,
    primary key (uuid)
);

-- what sensors are configured and streaming data from those machines?
create or replace table sensors (
    uuid varchar,
    name varchar,
    sensor_type_id int,
    machine_uuid varchar,
    last_reading int,
    installation_date date,
    last_service_date date,
    primary key (uuid),
    foreign key (machine_uuid) references machines(uuid)
);

-- what readings have we received from the configured sensors?
create table if not exists sensor_readings (
    sensor_uuid varchar,
    reading_time timestamp,
    reading int,
    primary key (sensor_uuid, reading_time),
    foreign key (sensor_uuid) references sensors(uuid)
);

-- Sensor types with reading min range, max ranges, service intervals and lifetime of the sensor.
-- Note that both the consumer and provider have a version of this table; you can think
-- of this version as coming from an imaginary "second app" which is a connector that
-- streams data into the consumer's account from the sensors. Consumer owns their own data!
create or replace table sensor_types (
    id int,
    name varchar,
    min_range int,
    max_range int,
    service_interval_count int,
    service_interval_unit varchar,
    lifetime_count int,
    lifetime_unit varchar,
    primary key (id)
);

insert into sensor_types values
    (1, 'Brake Temperature', -40, 40, 6, 'month', 5, 'year'),
    (2, 'Current Load', 20000, 50000, 3, 'month', 5, 'year'),
    (3, 'Bull-wheel RPM', 4000, 5000, 1, 'month', 1, 'year'),
    (4, 'Motor RPM', 2000, 2500, 1, 'month', 1, 'year'),
    (5, 'Motor Voltage', 110, 130, 2, 'month', 5, 'year'),
    (6, 'Current Temperature', -40, 40, 4, 'month', 5, 'year'),
    (7, 'Rope Tension', 70, 100, 3, 'month', 5, 'year'),
    (8, 'Chairlift Load', 50, 250, 3, 'month', 2, 'year'),
    (9, 'Chairlift Vibration', 30, 100, 3, 'month', 3, 'year');

-- what is the most-recent reading we have from a given sensor?
create view if not exists last_readings as
    select uuid, name, last_reading from sensors;

-- mock data in machines
insert into machines(uuid, name) select uuid_string(), 'Base Station';
insert into machines(uuid, name) select uuid_string(), 'Hilltop Station';
insert into machines(uuid, name) select uuid_string(), 'Chairlift #1';
insert into machines(uuid, name) select uuid_string(), 'Chairlift #2';
insert into machines(uuid, name) select uuid_string(), 'Chairlift #3';

-- mock data in sensors
execute immediate $$
declare
    c1 cursor for
        select uuid from machines where name = 'Base Station' or name = 'Hilltop Station';
    c2 cursor for
        select uuid from machines where name in ('Chairlift #1', 'Chairlift #2', 'Chairlift #3');
begin
    --for base and hilltop stations/machines
    for machine in c1 do
        let machine_uuid varchar default machine.uuid;
        insert into sensors(uuid, name, sensor_type_id, machine_uuid, installation_date, last_service_date)
            select uuid_string(), name, id, :machine_uuid, dateadd(day, -365, getdate()), dateadd(day, -1 * abs(hash(uuid_string()) % 365), getdate())
                from sensor_types where id < 8;
    end for;
    --for chairlifts machines
    for machine in c2 DO
        let machine_uuid varchar default machine.uuid;
        insert into sensors(uuid, name, sensor_type_id, machine_uuid, installation_date,last_service_date)
            select uuid_string(), name, id, :machine_uuid, dateadd(day, -365, getdate()), dateadd(day, -1 * abs(hash(uuid_string()) % 365), getdate())
                from sensor_types where id > 7;
    end for;
end;
$$
;

-- mock data in sensor_readings table
create or replace procedure populate_reading()
  returns varchar
  language sql
  as
  $$
    declare
      starting_ts       timestamp;
      rows_to_produce   integer;
      sensors_cursor cursor for
        select id, uuid, min_range, max_range
          from sensors s join sensor_types sr
                 on s.sensor_type_id = sr.id;
    begin
      --
      -- starting_ts is the time of the last sensor reading we wrong or, if no
      -- readings are available, 10 minutes in the past.
      --
      select coalesce(max(reading_time), dateadd(second, -30*20, current_timestamp()))
               into :starting_ts
        from sensor_readings;

      --
      -- produce one row for every thirty seconds from our starting time to now
      --
      rows_to_produce := datediff(second, starting_ts, current_timestamp()) / 30;

      for sensor in sensors_cursor do
        let sensor_uuid varchar default sensor.uuid;
        let min_range integer default sensor.min_range;
        let max_range integer default sensor.max_range;
  
        insert into sensor_readings(sensor_uuid, reading_time, reading)
          select
              :sensor_uuid,
              dateadd(second, row_id * 30, :starting_ts),
              case
                when rand_value < 10 then
                  :min_range - abs(hash(uuid)) % 10
                when rand_value > 90 then
                  :max_range + abs(hash(uuid)) % 10
                else
                  :min_range + abs(hash(uuid)) % (:max_range - :min_range)
              end case
          from ( 
              select seq4() + 1            as row_id,
                     uuid_string()         as uuid,
                     abs(hash(uuid)) % 100 as rand_value
                from table(generator(rowcount => :rows_to_produce)));
      end for;

      update sensors
         set last_reading = r.reading
        from sensors as s2, sensor_readings as r
       where s2.uuid = sensors.uuid
         and r.sensor_uuid = s2.uuid
         and r.reading_time = 
              (select max(reading_time)  
                 from sensor_readings r2
                where r2.sensor_uuid = s2.uuid);
    end;
  $$
;

-- Task to call the stored procedure to update the readings table every minute
create or replace task populate_reading_every_minute
    warehouse = chairlift_wh
    schedule = '1 minute'
as
    call populate_reading();

-- Get some initial data in the readings table
call populate_reading();

-- If you would like the data to be populated on a schedule, you can run:
-- alter task chairlift_consumer_data.data.populate_reading_every_minute resume;

-- To stop:
-- alter task chairlift_consumer_data.data.populate_reading_every_minute suspend;
```

<!-- ------------------------ -->
## Create application package
Duration: 2

Now that you've created the roles, objects, and granted proper privileges, you can begin constructing the native app. Execute the **prepare/create-package.sql** script. The script does a few key things:

* Creates the application package for the native app

* Marks that the native app will make use of data in the provider's account

* Creates views and grants the setup script reference access to the views

For more details, see the comments in the **prepare/create-package.sql** script.

```sql
use role chairlift_provider;
use warehouse chairlift_wh;

-- create our application package
-- at this point, the package will not be installable because
-- it does not have a version; the version will be uploaded later
create application package if not exists chairlift_pkg;

-- mark that our application package depends on an external database in
-- the provider account. By granting "reference_usage", the proprietary data
-- in the chairlift_provider_data database can be shared through the app
grant reference_usage on database chairlift_provider_data
    to share in application package chairlift_pkg;

-- now that we can reference our proprietary data, let's create some views
-- this "package schema" will be accessible inside of our setup script
create schema if not exists chairlift_pkg.package_shared;
use schema chairlift_pkg.package_shared;

-- View for sensor types full data
create view if not exists package_shared.sensor_types_view
  as select id, name, min_range, max_range, service_interval_count, service_interval_unit, lifetime_count, lifetime_unit
  from chairlift_provider_data.core.sensor_types;

-- View for sensor reading ranges
create view if not exists package_shared.sensor_ranges
  as select id, min_range, max_range
  from chairlift_provider_data.core.sensor_types;

-- View for sensor service scheduling
create view if not exists package_shared.sensor_service_schedules
  as select
    id,
    service_interval_count,
    service_interval_unit,
    lifetime_count,
    lifetime_unit
  from chairlift_provider_data.core.sensor_types;

-- these grants allow our setup script to actually refer to our views
grant usage on schema package_shared
  to share in application package chairlift_pkg;
grant select on view package_shared.sensor_types_view
  to share in application package chairlift_pkg;
grant select on view package_shared.sensor_ranges
  to share in application package chairlift_pkg;
grant select on view package_shared.sensor_service_schedules
  to share in application package chairlift_pkg;
```


<!-- ------------------------ -->
## Upload native app source code
Duration: 2

Now that the application package has been created, you can now upload the source files of the app into the application package. To do this, you'll create a schema within the **chairlift_pkg** application package called **code**, and then create a stage within that schema called **source**. Execute the following commands in a worksheet to create the schema and the stage:

```sql
create schema if not exists chairlift_pkg.code;
create stage if not exists chairlift_pkg.code.source;
```

Next, upload the files into the stage. You can use Snowsight (i.e., the Snowflake UI), the SnowSQL command line tool, or the Snowflake VS Code extension to upload the files. In this step, we'll use Snowsight.

Navigate to the **SOURCE** stage in the Snowsight UI. In the top right, click on the **+ FILES** button. Next, click **Browse** in the modal that appears. The folder structure within the stage should reflect the folder structure in your local repository directory, so be sure to upload the native app source code as follows:

1. Ensure you're in the **sfguide-native-apps-chairlift/src** directory and start by uploading the following files: **README.md**, **manifest.yml**, and **setup.sql**.

2. Next, upload the remaining files. Once again, click on the **+ FILES** button. Note the "Specify the path to an existing folder or create a new one (optional)" field in the modal. In this field, enter **ui**. The modal will automatically prepend a forward slash to your entry, so the value will read as **/ui**. Click **Browse**, navigate to the local **sfguide-native-apps-chairlift/src/ui** folder, select all files, and upload them. The folder structure within this stage should now reflect the folder structure in your local repository directory. 

It is important to make sure the directory structures match so that any references to objects needed by the app do not break. See the screenshots below for reference.

![Upload modal with ui/ in field](assets/upload.png)

![Final directory structure](assets/structure.png)

<!-- ------------------------ -->
## Create the first version of the app
Duration: 2

Let's review what we've covered so far:

* Created necessary account roles and objects, and granted proper privileges

* Created the application package and uploaded the source code the application package

Next, you'll create the first version of the app. Run the following SQL in a worksheet:

```sql
alter application package chairlift_pkg add version develop using '@chairlift_pkg.code.source';
```

This statement will create the first (new) version of the native app using the source code files that you uploaded earlier.

> aside positive
> 
>  **PATCH VERSIONS** Do not run the SQL statement below. It is included here to demonstrate how you can add a patch version of a native app.

In the scenario where you update the source code for the app to roll out a fix (i.e., fixing a bug), you could add the updated source as a patch to the native app using the following SQL statement:

```sql
alter application package chairlift_pkg add patch for version develop using '@chairlift_pkg.code.source';
```

This SQL command returns the new patch number, which will be used when installing the application as the consumer.

<!-- ------------------------ -->
## Install the application
Duration: 2

Recall that we are building the native app from the perspective of the provider (i.e., native app source code) and the consumer (i.e., mock data in the Snowflake account). To install the application in the same account, the provider role needs to grant installation and development permissions to the consumer role. Execute the following script using role **chairlift_provider**:

```sql
grant install, develop on application package chairlift_pkg to role chairlift_admin;
```

Next, execute the **consumer/install-app.sql** script. This script installs the application in the account, and grants appropriate privileges to the **chairlift_viewer** role. Note that the version and/or patch values may need to be updated to install the application using a different version or patch.

```sql
use role chairlift_admin;
use warehouse chairlift_wh;

-- create the actual application from the package in versioned dev mode
create application chairlift_app
    from application package chairlift_pkg
    using version develop;

-- allow our secondary viewer role restricted access to the app
grant application role chairlift_app.app_viewer
    to role chairlift_viewer;
```

<!-- ------------------------ -->
## Run the application
Duration: 2

With the application installed, you can now run the native app in your Snowflake account!

1. Navigate to **Apps** within Snowsight (left hand side).

2. Next, click **Apps** at the top of Snowsight.

3. You should see the app installed under "Installed Apps". Click **CHAIRLIFT_APP**. This will start the app. You'll be prompted to do some first-time setup by granting the app access to certain tables. After completing this setup, you'll have access to the main dashboard within the app. 

You can run the app as either the provider or consumer. To run the app as the provider, exit the app, switch your role to **CHAIRLIFT_ADMIN**, and navigate back to the app. To run the app as a consumer, exit the app, switch your role to **CHAIRLIFT_VIEWER**, and navigate back to the app. These roles have different access rights within the app. In particular, the **CHAIRLIFT_ADMIN** role has access to a "Configuration" tab within the app, while the **CHAIRLIFT_VIEWER** does not.

You should be able to browse the dashboard, configuration, and sensor data, all within the app.

![First time setup](assets/first-time-setup.png)

![Sensor data](assets/sensor-data.png)

> aside negative
> 
>  You may be prompted to accept the Anaconda terms and conditions. Exit the app, set your role to **ORGADMIN**, then navigate to "**Admin** -> **Billing & Terms**". Click **Enable** and then acknowledge and continue in the ensuing modal.

![Anaconda](assets/anaconda.png)

<!-- ------------------------ -->
## Conclusion
Duration: 0

Congratulations! In just a few minutes, you were able to build a Snowflake Native Application that a provider can use to share data with their consumers, analyze equipment data collected from consumers, and generate warnings based on this data. You were also able to interact with the app from the perspective of both the provider and consumer. 

### What we've covered

- How to create a native app application package
- How to add source code to a native app application package
- How to create a new version (or patch) of the native app
- How to install and run the native app in a consumer account

### Related Resources

- [Official Native App documentation](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)
- [Snowflake Demos](https://developers.snowflake.com/demos)
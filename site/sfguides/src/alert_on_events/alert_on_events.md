summary: Getting Started with Event Tables and Alerts
id: alert_on_events 
categories: featured, getting-started, data-engineering, app-development
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering
authors: Brad Culberson

# Getting Started with Event Tables and Alerts

## Overview 
Duration: 2

This guide will show you a real-world example of using event tables and alerts.

Often customers will have a data pipeline that is processing data and ask how to handle bad data. In this guide, we will process JSON data coming in from an untrusted source. This data pipeline will parse the records it can in Python. In the case of bad JSON and invalid records, it will dead letter queue (DLQ) those records by skipping processing and logging those in an event tables. An alert will be added to monitor for bad records and email when found.

The rest of this Snowflake guide walks you through building that data pipeline, logging to event tables, and alerting on bad data.

### Prerequisites 
- Familiarity with SQL and Python

### What you will Learn 
- How to log to event tables
- How to create and schedule tasks and alerts

### What you Need
- A Snowflake Account

### What you will Build
- A task that does data transformation with email alerting on bad data

## Database Setup
Duration: 3

For this guide, we will assume some external system is dropping in json into a table we can read. We are expected to then parse that json and write it into a structured table.

Create the database named ALERT_ON_EVENTS_GUIDE and the table named INGESTED_DATA we will use for the exercise.

```sql
CREATE DATABASE ALERT_ON_EVENTS_GUIDE;
USE SCHEMA PUBLIC;
```

In order to test the schematization to structured data and the error handling, insert some records as expected and some which are invalid. This insert includes 2 bad records, one has invalid json and the other has an invalid date.

```sql
CREATE TABLE INGESTED_DATA (RECORD_CONTENT VARCHAR(8000));
INSERT OVERWRITE INTO INGESTED_DATA 
VALUES 
('{"address":{"city":"Stevensfort","postalcode":"20033","state":"DC","street_address":"7782 Joshua Light Apt. 700"},"days":7,"email":null,"emergency_contact":{"name":"Kenneth Johnson","phone":"4898198640"},"expiration_time":"2023-06-01","name":"Sheri Willis","phone":null,"purchase_time":"2023-05-03T00:39:03.336008","resort":"Keystone","rfid":"0x900c64ee735e0cfb79d6ebe9","txid":"7879eed0-6b7d-4666-9aa4-b621c8700cb0"}'),
('{"address":null,"days":6,"email":null,"emergency_contact":{"name":"Richard Baker","phone":"+1-066-728-0674x58901"},"expiration_time":"2023-06-01","name":"Justin Kline","phone":"427.341.0127x88491","purchase_time":"2023-05-03T00:39:03.337206","resort":"Mt. Brighton","rfid":"0xa89366883c123def28bb5bc2","txid":"7360fb86-d8e5-49f2-84e7-6523a16436d4"}'),
('{"address":{"city":"South Brian","postalcode":"91326","state":"CA","street_address":"29292 Robert Vista"},"days":3,"email":"anorton@example.com","emergency_contact":{"name":"Brandon Bell","phone":"(301)980-2816"},"expiration_time":"2023-06-01","name":"Shawn Odom","phone":null,"purchase_time":"2023-05-03T00:39:03.338081","resort":"Vail","rfid":"0xef842c51f91d222650f2607b","txid":"2c9dc120-7b3e-40a2-b98e-752ef5b846c1"}'),
('{"address":{"city":"Lake Kelliside","postalcode":"89778","state":"NV","street_address":"3538 Stephen Radial Suite 641"},"days":5,"email":null,"emergency_contact":null,"expiration_time":"2023-06-01","name":"Laura Jackson","phone":"(192)056-6335x9992","purchase_time":"2023-05-03T00:39:03.338656","resort":"Beaver Creek","rfid":"0x9c87ef9b5ede02fceb94eba6","txid":"e42b560a-5bb9-44be-880a-70f567c14e32"}'),
('{"address":{"city":"South Michellechester","postalcode":"82973","state":"WY","street_address":"7260 David Course Suite 940"},"days":2,"email":null,"emergency_contact":null,"expiration_time":"2023-06-01","name":"Richard Scott","phone":"(377)858-9835x5216","purchase_time":"2023-05-03T00:39:03.339163","resort":"Hotham","rfid":"0x7cfb5f086e84415cf64e9d2b","txid":"6e9750be-e2cf-4e32-bc53-798e96337485"}'),
('{"address":null,"days":6,"email":null,"emergency_contact":{"name":"Brent Gomez","phone":"264-763-2415x20510"},"expiration_time":"2023-06-01","name":"Eric Strong","phone":"+1-475-801-2535x7782","purchase_time":"2023-05-03T00:39:03.339882","resort":"Wilmot","rfid":"0x4516ff404053dd288171c1b","txid":"af31d533-aa1d-4848-a11e-63d04ef3dfab"}'),
('{"address":{"city":"Williamsmouth","postalcode":"98151","state":"WA","street_address":"699 Samuel Trail Suite 056"},"days":3,"email":"bobby00@example.net","emergency_contact":{"name":"Jordan Sanchez","phone":"001-156-388-8421x98000"},"expiration_time":"2023-06-01","name":"Alexander Miller","phone":null,"purchase_time":"2023-05-03T00:39:03.340469","resort":"Mad River","rfid":"0xfc1c56ce8c455d6d033fe1c3","txid":"9f9452e2-6bee-4fa8-99ae-989bf2fb1c9a"}'),
('{"address":{"city":"Lake Jasonburgh","postalcode":"36522","state":"AL","street_address":"357 Woods Orchard Apt. 959"},"days":7,"email":"devon97@example.org","emergency_contact":{"name":"Michelle Mclean","phone":"+1-435-562-5415x97948"},"expiration_time":"2023-06-01","name":"Adam Moran","phone":"179.550.3610","purchase_time":"2023-05-03T00:39:03.341006","resort":"Vail","rfid":"0x9842c7f98423fa6ea5952d21","txid":"d76e6e16-d229-49e7-a77c-41bf576293a3"}'),
('{"address":{"city":"New Keith","postalcode":"27821","state":"NC","street_address":"70002 Gregory Cliffs"},"days":4,"email":"james21@example.com","emergency_contact":null,"expiration_time":"2023-06-01","name":"Sherri Campbell","phone":"001-253-932-0292","purchase_time":"2023-05-03T00:39:03.341508","resort":"Wildcat","rfid":"0xcbd00a5fb3e9b13e3eaede54","txid":"d916c199-8adf-4954-b73e-3aa87d69a498"}'),
('{"address":null,"days":3,"email":null,"emergency_contact":null,"expiration_time":"2023-06-01","name":"Jose Vasquez","phone":"001-094-284-1277","purchase_time":"2023-05-03T00:39:03.342005","resort":"Roundtop","rfid":"0xc5b3a84179fc30bd890d90a8","txid":"2e74fd7e-cffe-4a05-b81b-5a5fe1c8f86b"}'),
('{\"txid\":\"74553eec-32a7-42f6-8955-22c315b6cce3\",\"rfid\":\"0xf5cf736859282ae92873bab8\",'),
('{\"txid\":\"74553eec-32a7-42f6-8955-22c315b6cce3\",\"rfid\":\"0xf5cf736859282ae92873bab8\",\"resort\":\"Wilmot\",\"purchase_time\":\"2023-02-29T04:55:21.397493\",\"expiration_time\":\"2023-06-01\",\"days\":7,\"name\":\"Thomas Perry\",\"address\":null,\"phone\":\"909-865-2364x00638\",\"email\":null,\"emergency_contact\":{\"name\":\"Amber Sanchez\",\"phone\":\"993.904.9224x55225\"}}\n');
```

Create a table which will be used to store the valid, structured data:

```sql
CREATE OR REPLACE TABLE LIFT_TICKETS (
TXID varchar(255), RFID varchar(255), RESORT varchar(255), 
PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), 
ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);
```

## Schematization
Duration: 5

In order to separate the good and bad records, a python user defined table function will be used to parse and return records. This example will use an exception handler for bad json and some date checks to look for invalid records. We will schematize and store the valid data.

Create the udtf returning only the valid rows:

```python

CREATE OR REPLACE FUNCTION TRY_PARSE_TICKET(data string)
returns table (txid varchar, rfid varchar, resort varchar, purchase_time timestamp, expiration_time timestamp, days int, name varchar, address variant, phone varchar, email varchar, emergency_contact variant)
language python
runtime_version=3.8
handler='Parser'
as $$
import json
from datetime import datetime

class Parser:
    def __init__(self):
        pass

    def process(self, data):
        try:
            d = json.loads(data)
        except json.decoder.JSONDecodeError:
            return
        try:
            purchase_time = datetime.strptime(d['purchase_time'], "%Y-%m-%dT%H:%M:%S.%f")
            expiration_time = datetime.strptime(d['expiration_time'], "%Y-%m-%d")
        except ValueError:
            return

        yield (d['txid'], d['rfid'], d['resort'], purchase_time, expiration_time, d['days'], d['name'], d['address'], d['phone'], d['email'], d['emergency_contact'])

    def end_partition(self):
        pass
$$;
```

This funtion returns only the valid data in the table. Test that it is working as intended from the source table.

```sql
SELECT * FROM INGESTED_DATA;
SELECT t.* FROM INGESTED_DATA, TABLE(TRY_PARSE_TICKET(RECORD_CONTENT)) as t;
```

It is desired to merge this schematized data into the destination table LIFT_TICKETS based on the RFID.

Create a stored procedure to perform the merge tickets from the INGESTED_DATA into LIFT_TICKETS using TRY_PARSE_TICKET and then truncate INGESTED_DATA when complete. The key to perform the merge on is the TXID. This is done in a transaction so this would be a good pattern even for continuous data ingest.

```sql
CREATE OR REPLACE PROCEDURE TRANSFORM_TICKETS()
RETURNS VARCHAR
AS
BEGIN
    BEGIN TRANSACTION;
    MERGE INTO LIFT_TICKETS USING (
    SELECT t.* FROM INGESTED_DATA, TABLE(TRY_PARSE_TICKET(RECORD_CONTENT)) as t
    ) AS 
    DATA_IN ON DATA_IN.TXID = LIFT_TICKETS.TXID
    WHEN MATCHED THEN UPDATE SET 
        LIFT_TICKETS.RFID = DATA_IN.RFID, 
        LIFT_TICKETS.RESORT = DATA_IN.RESORT, 
        LIFT_TICKETS.PURCHASE_TIME = DATA_IN.PURCHASE_TIME, 
        LIFT_TICKETS.EXPIRATION_TIME = DATA_IN.EXPIRATION_TIME, 
        LIFT_TICKETS.DAYS = DATA_IN.DAYS, 
        LIFT_TICKETS.NAME = DATA_IN.NAME,
        LIFT_TICKETS.ADDRESS = DATA_IN.ADDRESS, 
        LIFT_TICKETS.PHONE = DATA_IN.PHONE, 
        LIFT_TICKETS.EMAIL = DATA_IN.EMAIL, 
        LIFT_TICKETS.EMERGENCY_CONTACT = DATA_IN.EMERGENCY_CONTACT
    WHEN NOT MATCHED THEN INSERT (TXID,RFID,RESORT,PURCHASE_TIME,EXPIRATION_TIME,DAYS,NAME,ADDRESS,PHONE,EMAIL,EMERGENCY_CONTACT) 
    VALUES (DATA_IN.TXID,DATA_IN.RFID,DATA_IN.RESORT,DATA_IN.PURCHASE_TIME,DATA_IN.EXPIRATION_TIME,DATA_IN.DAYS,DATA_IN.NAME,DATA_IN.ADDRESS,DATA_IN.PHONE,DATA_IN.EMAIL,DATA_IN.EMERGENCY_CONTACT);
    TRUNCATE TABLE INGESTED_DATA;
    COMMIT;
    RETURN 'ok';
END;
```

Run the stored procedure and verify the results are as expected (10 rows in LIFT_TICKETS and 0 rows in INGESTED_DATA).

```sql
CALL TRANSFORM_TICKETS();
SELECT COUNT(*) FROM LIFT_TICKETS;
SELECT COUNT(*) FROM INGESTED_DATA;
```

After this is working as intended, we have verified the happy path of success. Lets automate this to run when needed in the next step.

## Automating the Task
Duration: 2

Create the warehouse and task to run the schematization as needed. For this use case, it's desired these tickets are ingested within 10 minutes of creation so we will schedule it as such. Set the warehouse to auto suspend after 30 seconds as this is the only workload on that warehouse.

```sql
CREATE OR REPLACE WAREHOUSE transformer AUTO_SUSPEND = 30;

CREATE OR REPLACE TASK TRANSFORM_TICKETS 
    WAREHOUSE=transformer
    SCHEDULE = '10 minute'
    ALLOW_OVERLAPPING_EXECUTION = FALSE
AS
    CALL TRANSFORM_TICKETS();
```

Every time a task is created or modified, it must be resumed. Resume the task so it will run.

```sql
ALTER TASK TRANSFORM_TICKETS RESUME;
```

Verify the task is scheduled.

```sql
SHOW TASKS;
```

You can suspend this now as we do not need it for the rest of the guide, we will be calling the stored procedure manually for testing.

```sql
ALTER TASK TRANSFORM_TICKETS SUSPEND;
```

History of the task can be seen in INFORMATION_SCHEMA.

```sql
SELECT *
  FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
  order by SCHEDULED_TIME DESC;
```

Now that we have created this task, data from that is being dropped into the INGESTED_DATA will automatically be schematized into the LIFT_TICKETS table.

We also want to log the bad records and alert when they occur. We will do that in the following steps.

## Logging to Event Tables
Duration: 5

[Event Tables](https://docs.snowflake.com/developer-guide/logging-tracing/logging) are a good way to log these bad records as it's efficient to store these single records and it will allow us to tune the amount of logging and alerting we would like to do.

Create the event table for your account. Note this will overwrite the current events table if it has been set. If you share the account with others, use the event table that is already set in upcoming sql commands instead of MY_EVENTS.

```sql
SHOW PARAMETERS LIKE 'event_table' IN ACCOUNT;
CREATE OR REPLACE EVENT TABLE ALERT_ON_EVENTS_GUIDE.PUBLIC.MY_EVENTS;
ALTER ACCOUNT SET EVENT_TABLE = ALERT_ON_EVENTS_GUIDE.PUBLIC.MY_EVENTS;
```

Now that an event table is set on the account, modify the TRY_PARSE_TICKET to log the bad records. To do so, you can use the built in Python logging library. These will be set to warnings to make sure it's clear these are not healthy/normal events.

```python
CREATE OR REPLACE FUNCTION TRY_PARSE_TICKET(data string)
returns table (txid varchar, rfid varchar, resort varchar, purchase_time timestamp, expiration_time timestamp, days int, name varchar, address variant, phone varchar, email varchar, emergency_contact variant)
language python
runtime_version=3.8
handler='Parser'
as $$
import json
import logging
from datetime import datetime

class Parser:
    def __init__(self):
        pass

    def process(self, data):
        try:
            d = json.loads(data)
        except json.decoder.JSONDecodeError:
            logging.warning(f"Bad JSON data: {data} in try_parse_ticket")
            return
        try:
            purchase_time = datetime.strptime(d['purchase_time'], "%Y-%m-%dT%H:%M:%S.%f")
            expiration_time = datetime.strptime(d['expiration_time'], "%Y-%m-%d")
        except ValueError:
            logging.warning(f"Bad DATE value in data: {data} in try_parse_ticket")
            return

        yield (d['txid'], d['rfid'], d['resort'], purchase_time, expiration_time, d['days'], d['name'], d['address'], d['phone'], d['email'], d['emergency_contact'])

    def end_partition(self):
        pass
$$;
```

Set the log level to warning on the database so these events will be stored.

```sql
ALTER DATABASE ALERT_ON_EVENTS_GUIDE SET LOG_LEVEL = WARN;
```

Insert bad data and schematize to test the warnings are visible in the event table.

```sql
INSERT OVERWRITE INTO INGESTED_DATA 
VALUES
('{\"txid\":\"74553eec-32a7-42f6-8955-22c315b6cce3\",\"rfid\":\"0xf5cf736859282ae92873bab8\",'),
('{\"txid\":\"74553eec-32a7-42f6-8955-22c315b6cce3\",\"rfid\":\"0xf5cf736859282ae92873bab8\",\"resort\":\"Wilmot\",\"purchase_time\":\"2023-02-29T04:55:21.397493\",\"expiration_time\":\"2023-06-01\",\"days\":7,\"name\":\"Thomas Perry\",\"address\":null,\"phone\":\"909-865-2364x00638\",\"email\":null,\"emergency_contact\":{\"name\":\"Amber Sanchez\",\"phone\":\"993.904.9224x55225\"}}\n');

CALL TRANSFORM_TICKETS();
```

This data is sent asynchronously to reduce performance overhead of logging, so it will not be immediately available. After a few minutes, verify the event data will be in the events table.

```sql
SELECT * FROM ALERT_ON_EVENTS_GUIDE.PUBLIC.MY_EVENTS;
```

The bad data is available in the events table in the VALUE field. Also look at the other data available. We will use the RESOURCE_ATTRIBUTES in the next step.

## Creating an Alert
Duration: 5

In order to notify the team responsible for this process, we can add use an alert and notification integration.

Create an email notification integration, with your email address:

```sql
CREATE OR REPLACE NOTIFICATION INTEGRATION MY_ALERTS
    TYPE=EMAIL
    ENABLED=TRUE
    ALLOWED_RECIPIENTS=('<your email address>');
```

Create an alert (with your email address) when the warnings of interest were seen in the event table. In order to cover both the delay in the alert running after the transformation as well as the latency from the event being published, the query can look for any warnings in the last hour.

```sql
CREATE OR REPLACE ALERT BAD_TICKETS_IN_INGEST
  WAREHOUSE = transformer
  SCHEDULE = '10 minute'
  IF( EXISTS (
    SELECT * from ALERT_ON_EVENTS_GUIDE.PUBLIC.MY_EVENTS WHERE TIMESTAMP
        BETWEEN DATEADD(hour, -1, TO_TIMESTAMP_NTZ(CONVERT_TIMEZONE('UTC', current_timestamp())))
        AND TO_TIMESTAMP_NTZ(CONVERT_TIMEZONE('UTC', current_timestamp()))
        AND STARTSWITH(RESOURCE_ATTRIBUTES['snow.executable.name'], 'TRY_PARSE_TICKET(') 
        AND RECORD['severity_text'] = 'WARN'
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL('MY_ALERTS', '<your email address>', 'WARN: TRY_PARSE_TICKET', 'Some lift tickets had bad data during the last ingest. Check MY_EVENTS table for more details.');
```

Resume the ALERT so it will run, this is needed on creation and updates.

```sql
ALTER ALERT BAD_TICKETS_IN_INGEST RESUME;
```

Verify it is started.

```sql
SHOW ALERTS;
```

Drop in some bad records and run the stored procedure to test the email notification.

```sql
INSERT OVERWRITE INTO INGESTED_DATA 
VALUES
('{\"txid\":\"74553eec-32a7-42f6-8955-22c315b6cce3\",\"rfid\":\"0xf5cf736859282ae92873bab8\",'),
('{\"txid\":\"74553eec-32a7-42f6-8955-22c315b6cce3\",\"rfid\":\"0xf5cf736859282ae92873bab8\",\"resort\":\"Wilmot\",\"purchase_time\":\"2023-02-29T04:55:21.397493\",\"expiration_time\":\"2023-06-01\",\"days\":7,\"name\":\"Thomas Perry\",\"address\":null,\"phone\":\"909-865-2364x00638\",\"email\":null,\"emergency_contact\":{\"name\":\"Amber Sanchez\",\"phone\":\"993.904.9224x55225\"}}\n');

CALL TRANSFORM_TICKETS();
```

Verify the warnings are written to the events table and you received the email.

```
SELECT * FROM ALERT_ON_EVENTS_GUIDE.PUBLIC.MY_EVENTS;
```

History of the alerts can be seen in INFORMATION_SCHEMA.

```sql
SELECT *
FROM
  TABLE(INFORMATION_SCHEMA.ALERT_HISTORY(
    SCHEDULED_TIME_RANGE_START
      =>dateadd('hour',-1,current_timestamp())))
ORDER BY SCHEDULED_TIME DESC;
```

## Cleanup

In order to cleanup, drop the objects that are no longer needed.

```sql
DROP DATABASE ALERT_ON_EVENTS_GUIDE;
DROP WAREHOUSE TRANSFORMER;
DROP INTEGRATION MY_ALERTS;
```

## Conclusion & Next Steps
Duration: 2

Now you know how to use event tables to add more observability into your workloads. You can also create alerts and notify based on any query you can write in your account.

Do you regularly check on the health of some of your workloads that are running on Snowflake? If so, it's worth considering automating this so you can be notified earlier and automate that repeatable work.

### What we Covered
- How to schematize JSON data in a task
- How to add logging to have observability into that process
- How to create alerts and notifications

### Related Resources
- [Alerts and Notification](https://docs.snowflake.com/en/guides-overview-alerts)
- [Create Notification Integration](https://docs.snowflake.com/en/sql-reference/sql/create-notification-integration)
- [Setting up an Event Table](https://docs.snowflake.com/en/developer-guide/logging-tracing/event-table-setting-up)
- [Creating UDTFs](https://docs.snowflake.com/en/developer-guide/snowpark/python/creating-udtfs)


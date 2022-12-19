author: Jim Warner, Rachel Blum
id: secure-crosswalks-for-advertising-measurement
summary: Share ad exposure data without sharing PII for advertising measurement.
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, AdTech

# Secure Crosswalks for Advertising Measurment

## Overview 
Duration: 1

With the loss of historically common advertising identifiers, such as cookies and Mobile Advertising Identifiers (MAIDs), much of the advertising measurement ecosystem has moved to the use of panels. With a panel, an advertiser or publisher can use shared PII to perform measurement. However, because of privacy concerns and legislation such as GDPR and CCPA, many companies want to perform this match without directly sharing PII.

This process, a translation between one company's internal identifier to another company's internal identifier using shared PII, is known as a crosswalk. Snowflake allows this process to take place natively, without requiring a trusted third-party or the movememt of data, and without exposing any PII.

This process can take place within a [Clean Room](https://www.snowflake.com/blog/data-clean-room-explained/) or will soon be made easier with [Projection Constraints](https://medium.com/@alex.lei/embarking-on-the-snowflake-data-clean-room-dcf9fac23c21). However, this can also take place today, using only data sharing.  This Quickstart will walk through an example of this process.

### Prerequisites

- Familiarity with Snowflake and SQL

### What You’ll Learn

- How to set up an example measurement company with test data
- How to set up an example measurement customer with test data
- How to set up a crosswalk between the two parties

### What You’ll Need

- Access to two Snowflake accounts, in the same cloud and region

### What You’ll Build

- A secure crosswalk for sharing ad exposure data

## Measurement company account set-up
Duration: 4

Before we can set up the shares to implement the crosswalk, we need to prepare the measurement company account and generate example data.

<!-- ------------------------ -->
### Account set-up

Run the following to set up a warehouse, database, and schema for use with the example data.

```sql
use role accountadmin;
CREATE WAREHOUSE MEASUREMENT_CO_WH WITH WAREHOUSE_SIZE='XSmall' STATEMENT_TIMEOUT_IN_SECONDS=15    STATEMENT_QUEUED_TIMEOUT_IN_SECONDS=15;
USE WAREHOUSE MEASUREMENT_CO_WH;
CREATE DATABASE CROSSWALK_MEASUREMENT_CO_DEMO;
CREATE SCHEMA CROSSWALK_MEASUREMENT_CO_DEMO.DEMO;
```

### Data generation

Here we generate a table containing the panel data.  In this case, the panel is just a user ID and a random, generated email address.

```sql
USE CROSSWALK_MEASUREMENT_CO_DEMO.DEMO;

CREATE OR REPLACE TABLE my_panel AS
SELECT sha1(seq4()) as user_id,
  'user'||seq4()||'_'||uniform(1, 3, random(1))||'@email.com' as email
  FROM table(generator(rowcount => 100000));
```

We can then verify the generated data with the following.

```sql
SELECT * FROM my_panel;
```

<!-- ------------------------ -->
## Measurement customer account set-up
Duration: 4

In this example, the customer of the measurement company has the ad exposure data.  We start by setting up the account and created the example data.

### Account set-up

Run the following to create the warehouse, database, and schema to hold the example data for the measurement customer.

```sql
use role accountadmin;
CREATE OR REPLACE WAREHOUSE MEASUREMENT_CUST_WH WITH WAREHOUSE_SIZE='XSmall'  STATEMENT_TIMEOUT_IN_SECONDS=15 STATEMENT_QUEUED_TIMEOUT_IN_SECONDS=15;
USE WAREHOUSE MEASUREMENT_CUST_WH;
CREATE DATABASE CROSSWALK_MEASUREMENT_CUST_DEMO;
CREATE SCHEMA CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO;

USE CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO;
```

### Data generation

Now we create the ad impression data that the customer wants to measure.  One table contains the audience we are advertising to. This, like the panel data, contains the user ID for the customer and an email address.  The other table contains the ad impressions served to the audience.

```sql
USE CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO;

CREATE OR REPLACE TABLE my_audience AS
SELECT sha1(seq4()||'cust') as user_id,
  'user'||seq4()||'_'||uniform(1, 3, random(2))||'@email.com' as email
  FROM table(generator(rowcount => 1000000));

CREATE OR REPLACE TABLE impressions AS
SELECT sha1(uniform(1, 1000000, random(3))||'cust')::varchar(40) as user_id
  ,dateadd(second, uniform(1, 2592000, random(4)), ('2022-09-01'::timestamp)) as event_time
  ,'174631' as campaign_id
  ,uniform(200001,202000,random(5))::varchar(10) as placement_id
  ,uniform(300001,301000,random(6))::varchar(10) as creative_id
FROM table(generator(rowcount=>2000000));
```

You can verify the generated data with the following.

```sql
SELECT * FROM impressions i
 INNER JOIN my_audience a on a.user_id=i.user_id;
```

<!-- ------------------------ -->
## Aligning on PII masking or hashing
Duration: 1

In this example, we do not require that the ad measurement company expose even the number of panelists to the customer.  Nor do we require that the customer expose even the total number of impressions nor the size of their audience to the ad measurement company. Even still, because the customer will be calling a secure UDF created by the measurement company, we need the two parties to align on a masking or hashing algorithm.

This could be something like [Python Camouflage](https://quickstarts.snowflake.com/guide/python_camouflage/index.html?index=..%2F..index#3), or it could be something much simpler, like a salted hash.  We would not want to use something like a raw hash, because in theory that could be used to join with hashed PII from another customer of the measurement company.  For this example, and to keep this simple, both the measurement company account and the customer account should run the following.

```sql
CREATE OR REPLACE FUNCTION secure_hashed_email(email varchar)
RETURNS VARCHAR 
as
$$
sha1(email||'our_salt')
$$
;
```

## Measurement company lookup function
Duration: 4

The measurement company provides a function that takes in a hashed email, and returns the measurement company's internal user ID. This function will be used by the customer.

### Function creation

We use the following function to lookup the user ID from the hashed email.  We create it as a secure function to avoid leaking the underlying schema to the customer.

```sql
CREATE OR REPLACE SECURE FUNCTION lookup_hashed_email(hashed_input_email varchar)
RETURNS VARCHAR
AS
$$
select nvl((select any_value(user_id)
                    from my_panel
                    where secure_hashed_email(email) = hashed_input_email),
                    null)
$$
;
```

We can then test the function as follows.  First, we can find a value to test with by running the following.

```sql
SELECT user_id, email, secure_hashed_email(email) FROM my_panel;
```

Taking one of the values, we can run the following.

```sql
select lookup_hashed_email('26a3df1964012d8fb9b1bb9e7f0e189e3adcd74d');
select lookup_hashed_email('foobar');
```

The first statement returns the user ID associate with this hashed email.  The second should return null.

### Sharing the function

The measurement company can be shared with the customer with the following.

```sql
-- create share for secure udf
CREATE SHARE measurement_co_share;
GRANT USAGE ON DATABASE CROSSWALK_MEASUREMENT_CO_DEMO TO SHARE measurement_co_share;
GRANT USAGE ON SCHEMA CROSSWALK_MEASUREMENT_CO_DEMO.DEMO TO SHARE measurement_co_share;
GRANT USAGE ON FUNCTION CROSSWALK_MEASUREMENT_CO_DEMO.DEMO.lookup_hashed_email(varchar) TO SHARE measurement_co_share;
ALTER SHARE measurement_co_share ADD accounts=<account_id>;
```

The final statement needs the customer's Snowflake account ID inserted.

### Customer mounting the share

The customer can mount the share as follows.

```sql
SHOW SHARES;

CREATE DATABASE MEASUREMENT_CO FROM SHARE <account info>.MEASUREMENT_CO_SHARE;
```

First, the customer runs the first statement to get the name of the share.  They then mount it using the second statement. The customer can now call the function provided by the measurement company.

## Table of impressions for customer
Duration: 5

Using the function shared by the measurement company, the customer can now make a table for the impression data that includes only those in the measurement company panel.

### Creating the table

The table to be shared from the customer to the measurement company will be keyed off of the measurement company's internal identifier, using the secure UDF shared from the measurement company.  It also should hold only those impressions for campaignsx that this measurement company is measuring.

```sql
-- create a view of data the measurement company should see
CREATE OR REPLACE TABLE measurement_co_impressions AS
SELECT MEASUREMENT_CO.DEMO.LOOKUP_HASHED_EMAIL(secure_hashed_email(a.email)) as user_id,
 i.event_time, i.campaign_id, i.placement_id, i.creative_id
FROM CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO.impressions i
 INNER JOIN CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO.my_audience a on a.user_id=i.user_id
WHERE MEASUREMENT_CO.DEMO.LOOKUP_HASHED_EMAIL(secure_hashed_email(a.email)) is not null
 and i.campaign_id='174631';
```

We can verify that it includes impressions only for the overlap by running the following.

```sql
SELECT count(1) FROM measurement_co_impressions;
```

### Sharing the table

Now that we have created the table to hold the data, we create the share to share this data back to the measurement company as follows.

```sql
-- create share of impressions to measurement co
CREATE SHARE measurement_cust_share;
GRANT USAGE ON DATABASE CROSSWALK_MEASUREMENT_CUST_DEMO TO SHARE measurement_cust_share;
GRANT USAGE ON SCHEMA CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO TO SHARE measurement_cust_share;
GRANT SELECT ON CROSSWALK_MEASUREMENT_CUST_DEMO.DEMO.measurement_co_impressions TO SHARE measurement_cust_share;
ALTER SHARE measurement_cust_share ADD accounts=<customer snowflake account>;
```

The customer's Snowflake account ID should be placed in the last statement.

### Customer mounting the shared table

Finally, to complete the crosswalk, the measurement company should mount the share.

```sql
-- mount share from customer
SHOW SHARES;

CREATE DATABASE MEASUREMENT_CUST FROM SHARE <account info>.MEASUREMENT_CUST_SHARE;
```

As before, the name of the share should be placed into the final statement.

To test the share, and to show that it is, in fact, keyed off of the measurement company ID, run the following statement.

```sql
SELECT *
FROM MEASUREMENT_CUST.DEMO.MEASUREMENT_CO_IMPRESSIONS i
 INNER JOIN my_panel p on p.user_id=i.user_id;
```

Now, as we can see with the result of this statement, the measurement company can see the impressions, but only for those in the measurement company's panel. In addition, the key of the table is the measurement company's own ID, not the shared PII.  Further, the impression data still sits in the customer's account, and has not been moved to the measurement company's account.  They can now complete their measurement using their panel, and provide the results to their customer.

<!-- ------------------------ -->
## Conclusion
Duration: 1

Advertising measurement companies often need to join data about their panel to the ad exposure data provided by the customer to perform their measurement.  Snowflake, using its unique data sharing capabilities that do not require movement of data nor a trusted third-party, can be used to perform the necessary crosswalk.

### What we've covered

- Set-up of customer and measurement company accounts, with example data
- Set-up of data share and secure functions
- Execution of crosswalk logic and functionality

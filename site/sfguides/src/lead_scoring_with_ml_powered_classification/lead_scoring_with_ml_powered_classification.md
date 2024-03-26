author: Jim Warner
id: lead_scoring_with_ml_powered_classification
summary: Shows how marketers can predict the value of leads and new
customers to make audiences for activation.
categories: data-science-&-ml, solution-examples, marketing
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, AdTech, Machine Learning

# Lead Scoring with ML-Powered Classification
<!-- ------------------------ -->
## Overview 
Duration: 1

Many customers use Snowflake as the basis of their [Customer
360](https://www.snowflake.com/enable-customer-360-with-snowflake/) -
a single source of truth for all data about customers - to power
marketing use cases. Often, it is valuable to use data about existing
customers to make predictions about new customers. When a new customer
comes in, knowing whether they are similar to your best existing
customers is valuable, as that could justify spending additional
marketing dollars targeting these customers across marketing
channels. However, not all marketing teams have had the Machine
Learning and AI expertise to build these models themselves.

Fortunately, Snowflake's [ML-Powered
Analysis](https://docs.snowflake.com/en/guides-overview-analysis)
makes these types of use cases more accessible - even to teams that
just write SQL. The
[classification](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ml-powered/classification) functionality
enables data teams to quickly classify customers so that marketing
teams can build and activate audiences.

### Prerequisites
- Access to a Snowflake account or use of the [Snowflake free 30-day trial](https://trial.snowflake.com)
- Basic knowledge of SQL, database concepts, and objects

### What You’ll Learn 
- How to generate example customer data
- How to build models using Snowflake's ML-Powered classification
- How to use the model to produce audiences for marketing

### What You’ll Build 
- SQL scripts to build the relevant models and define audiences

<!-- ------------------------ -->
## Prepare Your Environment
Duration: 8

If you do not have a Snowflake account, you can register for a [Snowflake free 30-day trial](https://trial.snowflake.com). The cloud provider (AWS, Azure, Google Cloud), and Region (US East, EU, e.g.) do _not_ matter for this lab. However, we suggest you select the region which is physically closest to you.

To easily follow the instructions, resize your browser windows so you can view this Quickstart and your Snowflake environment side-by-side. If possible, even better is to use a secondary display dedicated to the Quickstart.

### Create a Warehouse, Database, Schemas
Create a warehouse, database, and schema that will be used for loading, storing, processing, and querying data for this Quickstart. We will use the UI within the Worksheets tab to run the DDL that creates these objects.

Copy the commands below into your trial environment. To execute a single statement, just position the cursor anywhere within the statement and click the Run button. To execute several statements, they must be highlighted through the final semi-colon prior to clicking the Run button.

```sql
-- create warehouse, database, and schema
use role accountadmin;
CREATE or replace WAREHOUSE lead_scoring_demo_WH WITH WAREHOUSE_SIZE='Small' STATEMENT_QUEUED_TIMEOUT_IN_SECONDS=15;
CREATE DATABASE lead_scoring_demo;
CREATE SCHEMA lead_scoring_demo.DEMO;
```

### Set up an analyst role
The [Snowflake documentation recommends creating a
role](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ml-powered/classification#granting-privileges-to-create-classification-models)
for people who need to create classification models.  As such, we run the following SQL to set up a role and grant the necessary privileges.

```sql
-- set up analyst role
CREATE ROLE analyst;
GRANT USAGE ON DATABASE lead_scoring_demo TO ROLE analyst;
GRANT USAGE ON SCHEMA lead_scoring_demo.DEMO TO ROLE analyst;
GRANT USAGE ON WAREHOUSE lead_scoring_demo_WH TO ROLE analyst;
GRANT CREATE TABLE ON SCHEMA lead_scoring_demo.DEMO TO ROLE analyst;
GRANT CREATE VIEW ON SCHEMA lead_scoring_demo.DEMO TO ROLE analyst;
GRANT CREATE SNOWFLAKE.ML.CLASSIFICATION ON SCHEMA lead_scoring_demo.DEMO TO ROLE analyst;
GRANT ROLE analyst TO USER <your_user_here>;
```

Then you simply use the role, schema, and warehouse to prepare to fun the
rest of the Quickstart.

```sql
-- use the role, warehouse, and schema
use role analyst;
USE WAREHOUSE lead_scoring_demo_WH;
USE lead_scoring_demo.DEMO;
```

### Create the table and generate test data
For the purposes of this Quickstart, we will generate an example table
containing mock customer data. In a real-world system, aggregating
together the data needed to build the model would be an important
step. The data might include information from disparate systems in the
enterprise, as well as 2nd- and 3rd-party data from the [Snowflake Marketplace](https://www.snowflake.com/en/data-cloud/marketplace/).

For this demo, however, we will directly generate mock customer
data. In addition, we will generate the data such that there is an
impact of customer quality that is related to the inputs used to build
the model, instead of using purely random data, so that the model can
find something interesting.

First, we create the base of the table with demographic data (age,
household income, martial status, and household size) email address as the key.  The table also has the date on which the
customer joined the list, so we can distinguish new customers from
customers who have been around longer.  Typically, you want to train
only on customers who have been around long enough to establish
whether they will be a loyal customer or not. Finally, we have a
column for the total value of all orders the customer has made, and it
is zero for now as it will be filled in later.

```sql
-- create table to hold the generated data
create table daily_impressions(day timestamp, impression_count integer);-- create the example customer table
CREATE OR REPLACE TABLE customers AS
SELECT 'user'||seq4()||'_'||uniform(1, 3, random(1))||'@email.com' as email,
dateadd(minute, uniform(1, 525600, random(2)), ('2023-03-11'::timestamp)) as join_date,
round(18+uniform(0,10,random(3))+uniform(0,50,random(4)),-1)+5*uniform(0,1,random(5)) as age_band,
case when uniform(1,6,random(6))=1 then 'Less than $20,000'
       when uniform(1,6,random(6))=2 then '$20,000 to $34,999'
       when uniform(1,6,random(6))=3 then '$35,000 to $49,999'
       when uniform(1,6,random(6))=3 then '$50,000 to $74,999'
       when uniform(1,6,random(6))=3 then '$75,000 to $99,999'
  else 'Over $100,000' end as household_income,
    case when uniform(1,10,random(7))<4 then 'Single'
       when uniform(1,10,random(7))<8 then 'Married'
       when uniform(1,10,random(7))<10 then 'Divorced'
  else 'Widowed' end as marital_status,
  greatest(round(normal(2.6, 1.4, random(8))), 1) as household_size,
  0::float as total_order_value,
  FROM table(generator(rowcount => 100000));
```

Next we will fill the total order value column for customers who have
existed for a long enough time. We use the demographic data to
influence the total order value, so that the model can pick up the effects.

```sql
-- set total order values for longer-term customers
update customers
set total_order_value=round((case when uniform(1,3,random(9))=1 then 0
    else abs(normal(15, 5, random(10)))+
        case when marital_status='Married' then normal(5, 2, random(11)) else 0 end +
        case when household_size>2 then normal(5, 2, random(11)) else 0 end +
        case when household_income in ('$50,000 to $74,999', '$75,000 to $99,999', 'Over $100,000') then normal(5, 2, random(11)) else 0 end
    end), 2)
where join_date<'2024-02-11'::date;
```

Finally, we fill in the total order value for customers who have more
recently signed up. As such, they are more likely to have $0 total
order value, and their totals are lower on average.

```sql
-- set total order value for more recent customers
update customers
set total_order_value=round((case when uniform(1,3,random(9))<3 then 0
    else abs(normal(10, 3, random(10)))+
        case when marital_status='Married' then normal(5, 2, random(11)) else 0 end +
        case when household_size>2 then normal(5, 2, random(11)) else 0 end +
        case when household_income in ('$50,000 to $74,999', '$75,000 to $99,999', 'Over $100,000') then normal(5, 2, random(11)) else 0 end
    end), 2)
where join_date>='2024-02-11'::date;
```

### Verify the data

We can run the following statement to verify our data.

```sql
-- verify the data loading
select * from customers;
```

## Prepare data and create the model
Duration: 4

Now we have data that mimics what we might have after a company has
created a Customer 360. We have demographic data and a total of all
orders the customer has placed, where that total is a function of the
demographic data we have gathered. Next, we will create a view which
will represent the data used to train the value, then we will create
the model.

### Create training data view

We run the following to create a view which limits the columns
selected (we do not use the email address or the join date), and we
limit only to the longer-term customers who will be used to train the
model. Finally, we bucket customers into bronze, silver, and gold
groups using the total order value column.

```sql
-- create a view to train the model
create or replace view customer_training
as select age_band, household_income, marital_status, household_size, case when total_order_value<10 then 'BRONZE'
    when total_order_value<=25 and total_order_value>10 then 'SILVER'
    else 'GOLD' END as segment
from customers
where join_date<'2024-02-11'::date;
```

We can verify that this data is as we expect by checking the contents
of the view.

```sql
-- verify the training view
select * from customer_training;
```

### Build the model

We can create the classification model by running the following statement.

```sql
-- create the classification model
CREATE OR REPLACE SNOWFLAKE.ML.CLASSIFICATION customer_classification_model(
    INPUT_DATA => SYSTEM$REFERENCE('view', 'customer_training'),
    TARGET_COLNAME => 'segment'
);
```

Notice that we point the model at the view we created, and we specify
the column containing the bronze, silver, or gold segmentation. We can
verify that the model is created by running the following.

```sql
SHOW SNOWFLAKE.ML.CLASSIFICATION;
```

Here we should see the `customer_classification_model` we created.

### Save the model predictions to a table

Next, we will run the predictions across our entire `customers` table,
saving the results to a table with the email address, allowing us to
join later, when we use the predictions to build audiences.

```sql
-- run prediction and save results
CREATE OR REPLACE TABLE customer_predictions AS
SELECT email, customer_classification_model!PREDICT(INPUT_DATA => object_construct(*)) as predictions
from customers;
```

Next we can run the following query to verify that our predictions
have been made correctly.

```sql
-- verify the created predictions
SELECT * FROM customer_predictions;
```

## Creating audiences
Duration: 3

Once we have run these predictions, we can use the predictions to
build audiences. In some flows, the audiences could be saved, or a
reverse ETL tool might query for them directly. The email addresses
could be used to activate the audiences across both paid (social, CTV
or programmatic platforms) or owned (email, website) marketing channels.

### High-value new customers

The following query can now be run to create a list of new customers
who are likely to become "GOLD" customers in the future.

```sql
-- new customers likely to be gold
select c.email
from customers c
 inner join customer_predictions p on c.email=p.email
where c.join_date>='2024-02-11'::date and predictions:class='GOLD';
```

If we wanted to customize the confidence at which we want to consider
them likely gold customers, we could use the probabilities saved in
the predictions.

This list of users might be a list we consider worthy of additional
marketing, and we may be willing to pay more to show ads to this
audience. We also might email this group a coupon code, for instance,
to drive to drive additional purchases in the hope that they become
regular, loyal customers.

### Underutilized existing customers

The usage of the model is not limited only to new customers. We can
also use the model to find existing customers who, although they are
not gold, are similar to customers who are. This could indicate an
opportunity to reach out these customers across channels to drive
additional purchases.

```sql
-- old customers who are not gold but should be
select c.email
from customers c
 inner join customer_predictions p on c.email=p.email
where c.join_date<'2024-02-11'::date and predictions:class='GOLD'
 and c.total_order_value<=25;
```

<!-- ------------------------ -->
## Conclusion
Duration: 2

As we have seen in this Quickstart, Snowflake's [ML-Powered
Analysis](https://docs.snowflake.com/en/guides-overview-analysis)
makes it easy to build high-value audiences from a Customer 360.

### What We've Covered
- How to create test customer data.
- How to build a model to classify the customers.
- How to use the model predictions to create audiences.

### Related Resources
- [Snowflake Documentation: ML-Powered Analysis](https://docs.snowflake.com/en/guides-overview-analysis)

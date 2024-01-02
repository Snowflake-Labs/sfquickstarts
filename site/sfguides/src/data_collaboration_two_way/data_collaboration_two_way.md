author: Tim Buchhorn
id: data_collaboration_two_way
summary: This is a Snowflake Guide on how to use Snowflake's Data Collaboration features to share an enrich data. 
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Two Way Data Collaboration
<!-- ------------------------ -->
## Overview 
Duration: 1

This guide will take you through Snowflake's Collaboration features, and highlight how easy it is to share data between two organisations.

It also highlights Snowflakes ability to host a ML Model, score data from shared data, and share the enriched (scored) data back to the original Provider. Hence, it is a 2-way sharing relationship, where both accounts are Providers and Consumers.

### Prerequisites
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
    **Download the git repo here: insert repo**
- [Anaconda](https://www.anaconda.com/) installed
- [Python 3.9](https://www.python.org/downloads/) installed
    - Note that you will be creating a Python environment with 3.9 in the **Setup the Python Environment** step
- Snowflake accounts with [Anaconda Packages enabled by ORGADMIN](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#using-third-party-packages-from-anaconda). If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/).
- A Snowflake account login with a role that has the ability to create database, schema, tables, stages, user-defined functions, and stored procedures. If not, you will need to register for free trials or use a different role.

### What You’ll Learn
- How to become a Provider in Snowflake Marketplace (Private Listings)
- How to Consume a shared private asset in the Snowflake Marketplace
- How to Deploy a ML Model in Snowflake
- How to share seamlessly between two Snowflake Accounts 

### What You’ll Need 
- Two [Snowflake](https://signup.snowflake.com/) Accounts in the same cloud and region 

### What You’ll Build 
- Ingestion of Credit Card Customer Profile Data
- Sharing raw data seamlessly via a private listing
- Consuming shared data via a private listing
- Enriching shared data using a ML model
- Sharing back enriched data to the original Provider account

<!-- ------------------------ -->
## Business Use Case
Duration: 2

In this hands-on-lab, we are playing the role of a bank. The Credit Risk team has noticed a rise in credit card default rates which affects the bottom line of the business. It has employed the help of an external organisation to score the credit card default risk of their existing customers, based on a series of attributes in categories such as spending, balance, delinquency, payment and risk. The data needs to be shared between the two parties.

Both companies have chosen to use Snowflake. The advantages of doing this are:
- Low latency between the Provider and Consumer accounts
- The files stay within the security perimeter of Snowflake, with Role Based Access Control (RBAC)

Below is a schematic of the data share
![Diagram](assets/two_way_data_collaboration.png)

### Dataset Details

The dataset contains aggregated profile features for each customer at each statement date. Features are anonymized and normalized, and fall into the following general categories:

D_* = Delinquency variables
S_* = Spend variables
P_* = Payment variables
B_* = Balance variables
R_* = Risk variables

### Dataset Citation

Addison Howard, AritraAmex, Di Xu, Hossein Vashani, inversion, Negin, Sohier Dane. (2022). American Express - Default Prediction. Kaggle. https://kaggle.com/competitions/amex-default-prediction

<!-- ------------------------ -->
## Set up
Duration: 1

Navigate to the [Snowflake Trial Landing Page](https://signup.snowflake.com/). Follow the prompts to create a Snowflake Account.

Repeat the process above. Be sure to select the same cloud and region as the first account your created. Although it is possible to share accross clouds and regions, this guide will not cover this scenario.

Check your emails and follow the prompts to activate both the accounts. One will be the Provider and one will be the Consumer.

<!-- ------------------------ -->
## Provider Account - Set Up
Duration: 10

In this part of the lab we'll set up our Provider Snowflake account, create database structures to house our data, create a Virtual Warehouse to use for data loading and finally load our credit card default prediction data into our default_prediction_table_train and default_prediction_table_unscored and run a few queries to get familiar with the data.

In our scenrio, this step would be the bank loading the data, and creating a final dataset that will be shared with an external partner which has been taskes with creating a machine learning model to predict defaults on new data (Step X). The default_prediction_table_train dataset would be sent for the partner to train and test the model, and the default_prediction_table_unscored would be new data sent to the partner to be scored and returned.

### Initial Set Up

For this part of the lab we will want to ensure we run all steps as the ACCOUNTADMIN role

```SQL
  -- Change role to accountadmin
  use role accountadmin;
```

First we can create a [Virtual Warehouse](https://docs.snowflake.com/en/user-guide/warehouses-overview) that can be used to load the initial dataset. We'll create this warehouse with a size of XS which is right sized for that use case in this lab.

```SQL
  -- Create a virtual warehouse for data exploration
  create or replace warehouse query_wh with 
    warehouse_size = 'x-small' 
    warehouse_type = 'standard' 
    auto_suspend = 300 
    auto_resume = true 
    min_cluster_count = 1 
    max_cluster_count = 1 
    scaling_policy = 'standard';
```

### Load Data 

Next we will create a database and schema that will house the tables that store our data to be shared.

```SQL
  -- Create the application database and schema
  create or replace database data_sharing_demo;
  create or replace schema data_sharing_demo;
```

Our data is in Parquet format, so we will create a file format object

```SQL
  create or replace file format parquet_format
  type = parquet;
```

Next we set up our [External Stage](https://docs.snowflake.com/en/user-guide/data-load-s3-create-stage#external-stages) to our data. In our business scenario, we would have a secure [Storage Integration](https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration) to the external stage rather than a public s3 bucket.

```SQL
  create or replace stage quickstart_cc_default_training_data
      url = 'insert public url here'
      file_format = parquet_format;

  create or replace stage quickstart_cc_default_unscored_data
      url = 'insert public url here'
      file_format = parquet_format;
```

This DDL will create the structure for the table which is the main source of data for our lab.

```SQL
  CREATE TABLE cc_default_training_table
    USING TEMPLATE (
      SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
        FROM TABLE(
          INFER_SCHEMA(
            LOCATION=>'@quickstart_cc_default_training_data',
            FILE_FORMAT=>'parquet_format'
          )
        ));

  CREATE TABLE cc_default_unscored_table
    USING TEMPLATE (
      SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
        FROM TABLE(
          INFER_SCHEMA(
            LOCATION=>'@quickstart_cc_default_unscored_data',
            FILE_FORMAT=>'parquet_format'
          )
        ));
```

Load the data in the tables

```SQL
  COPY INTO cc_default_training_table 
    FROM @quickstart_cc_default_training_data 
    FILE_FORMAT = (FORMAT_NAME= 'parquet_format') 
    MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;

  COPY INTO cc_default_training_table 
    FROM @quickstart_cc_default_training_data 
    FILE_FORMAT = (FORMAT_NAME= 'parquet_format') 
    MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;
```

You should have loaded over 5 million rows in less than a minute. To check, query the data in the worksheet

```SQL
  select count(*) default_prediction_table 
    FROM default_prediction_table;
```

<!-- ------------------------ -->
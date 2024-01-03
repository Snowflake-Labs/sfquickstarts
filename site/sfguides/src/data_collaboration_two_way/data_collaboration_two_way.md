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
- The [Snowpark ML](https://docs.snowflake.com/developer-guide/snowpark-ml/index#installing-snowpark-ml-from-the-snowflake-conda-channel) package installed

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
  CREATE TABLE cc_default_training_data
    USING TEMPLATE (
      SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
        FROM TABLE(
          INFER_SCHEMA(
            LOCATION=>'@quickstart_cc_default_training_data',
            FILE_FORMAT=>'parquet_format'
          )
        ));

  CREATE TABLE cc_default_unscored_data
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
  COPY INTO cc_default_training_data 
    FROM @quickstart_cc_default_training_data 
    FILE_FORMAT = (FORMAT_NAME= 'parquet_format') 
    MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;

  COPY INTO cc_default_training_data 
    FROM @quickstart_cc_default_training_data 
    FILE_FORMAT = (FORMAT_NAME= 'parquet_format') 
    MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;
```

You should have loaded over 5 million rows in less than a minute. To check, query the data in the worksheet

```SQL
  select count(*) 
    FROM cc_default_training_data;
```

<!-- ------------------------ -->
## Consumer Account - Set Up
Duration: 2

In this step, we set up the consumer account to accept the share. We need to get the account details to share with the bank, so they can set up a private listing with us, as we do not want anyone outside of out partnership to have access to the data.

Log in to the second trial account that was set up, and note the account identifier. Instructions on how to do this can be found [here](https://docs.snowflake.com/en/user-guide/admin-account-identifier). Once you have noted this, return to the Provider account.

A screenshot on how to find your account identifier from the Snowsight UI is shown below 
![Diagram](assets/account_indentifier_navigation.png)

<!-- ------------------------ -->
## Provider Account - Create Private Listing
Duration: 2

In your provider account, open up Snowsight and navigate to Data > Provider Studio on the left hand menu. then click the Listings button in the top right. Screenshot is below: ![Diagram](assets/provider_studio_navigation.png)

In the modal, enter the name of the Private Listing that we wish to share with our external partner. We have named it cc_default_training_data. They will securely access this data from their own Snowflake account, and share back the scored results. We have selected "Only Specified Consumers" in our discovery settings, so that our data can only be seen with the partners we explicitly want to share with. Screenshot is below: ![Diagram](assets/private_listing_navigation.png)

In the next modal, click the "+ Select" option. In this next modal, select the CC_DEFAULT_TRAINING_DATA in the DATA_SHARING_DEMO database and schema. Add it to the listing. Change the Secure Share Identifier to DATA_SHARING_DEMO and update the description of the listing. Lastly, we add the consimer accounts. Since we selected Private Listing, the accounts we specify in this option are the only accounts that will be able to discover and utilise this share. Add the consumer account identifier we noted from the previous section. A screenshow is below: ![Diagram](assets/create_listing_navigation.png)

Click publish, and now your listing is live and readty for the consumer. No movement of data, no SFTP. The data is live and ready to query.

<!-- ------------------------ -->
## Consumer Account - Accept Share and Create Warehouses
Duration: 2

In this section, we assume the role of the consumer of the data. Our data science team will take the data shared with us securely, score it for credit card default risk, and share the results back with the bank (the original data provider).

The first step is to accept the share. Log in to the Consumer Account and ensure you have assumed the ACCOUNTADMIN Role. Navigate to Data > Private Sharing and you should see the cc_default_training_darta waiting for the account admin to accept. Screenshot below
![Diagram](assets/accept_share_navigation.png)

Click Get, and in the next modal, click Get.
![Diagram](assets/accept_share_navigation_2.png)

You should now see CC_DEFAULT_TRAINING_DATA as one of the Databases in your catalog, with the DATA_SHARING_DEMO schema and the CC_DEFAULT_TRAINING_DATA. We did not need to load any data, it is shared live from the Provider. Screenshot below
![Diagram](assets/accept_share_result.png)

Next we will create some warehouses to query the sharted data and to train our model in subsequent steps. We will create a [Snowpark Optimised Warehouse](https://docs.snowflake.com/en/developer-guide/snowpark/python/python-snowpark-training-ml) for our training jobs. Open up a worksheet and run the following commands. 

```SQL
  -- Change role to accountadmin
  use role accountadmin;

  -- Create a virtual warehouse for data exploration
  create or replace warehouse query_wh with 
    warehouse_size = 'x-small' 
    warehouse_type = 'standard' 
    auto_suspend = 300 
    auto_resume = true 
    min_cluster_count = 1 
    max_cluster_count = 1 
    scaling_policy = 'standard';

  -- Create a virtual warehouse for training
  create or replace warehouse training_wh with 
    warehouse_size = 'medium' 
    warehouse_type = 'snowpark-optimized' 
    max_concurrency_level = 1;
```
<!-- ------------------------ -->
## Consumer Account - Create Model
Duration: 2

For this section, make sure you download the corresponding git repo (INSERT LINK) so you have the files referenced in this section.

### Set Up Snowpark for Python and Snowpark ML

The first step is to set up the python environment to develop our model. To do this:

- Download and install the miniconda installer from [https://conda.io/miniconda.html](https://conda.io/miniconda.html). (OR, you may use any other Python environment with Python 3.9, for example, [virtualenv](https://virtualenv.pypa.io/en/latest/)).

- Open a new terminal window and execute the following commands in the same terminal window:

  1. Create the conda environment.
  ```
  conda env create -f conda_env.yml
  ```

  2. Activate the conda environment.
  ```
  conda activate snowpark-ml-hol
  ```

  3. Start notebook server:
  ```
  $ jupyter notebook
  ```  

- Update connection.json with your Snowflake account details and credentials.
  Here's a sample based on the object names we created in the last step:

```
{
  "account"   : "<your_account_identifier_goes_here>",
  "user"      : "<your_username_goes_here>",
  "password"  : "<your_password_goes_here>",
  "role"      : "ACCOUNTADMIN",
  "warehouse" : "QUERY_WH",
  "database"  : "CC_DEFAULT_TRAINING_DATA",
  "schema"    : "DATA_SHARING_DEMO"
}
```

> aside negative
> 
> **Note:** For the account parameter above, specify your account identifier and do not include the snowflakecomputing.com domain name. Snowflake automatically appends this when creating the connection. For more details on that, refer to the documentation.

If you are having some trouble with the steps above, this could be due tohaving different architectures, such as an M1 chip. In that case, follow the instructions [here](https://docs.snowflake.com/developer-guide/snowpark-ml/index#installing-snowpark-ml-from-the-snowflake-conda-channel) and be sure to conda install jupyter notebooks and pyarrow.

### Train Model
Open up the notebook 
<!-- ------------------------ -->
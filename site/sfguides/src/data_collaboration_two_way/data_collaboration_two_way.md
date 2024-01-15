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

  COPY INTO cc_default_unscored_data 
    FROM @quickstart_cc_default_uncscored_data 
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

Click publish, and now your listing is live and ready for the consumer. No movement of data, no SFTP. The data is live and ready to query.

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
## Optional - Create Stored Procedure in Worksheet
Duration: 2

```SQL
CREATE OR REPLACE PROCEDURE cc_profile_processing(rawTable VARCHAR, targetTable VARCHAR)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'feature_transform'
AS
$$
import snowflake.snowpark as snp
import snowflake.snowpark.window as W
import snowflake.snowpark.functions as F

def feature_transform(session, raw_table, target_table):
    training_df = session.table(raw_table)
    # Feature engineer raw input
    #Average
    features_avg = ['B_1', 'B_2', 'B_3', 'B_4', 'B_5', 'B_6', 'B_8', 'B_9', 'B_10', 'B_11', 'B_12', 'B_13', 'B_14', 'B_15', 'B_16', 'B_17', 'B_18', 'B_19', 'B_20', 'B_21', 'B_22', 'B_23', 'B_24', 'B_25', 'B_28', 'B_29', 'B_30', 'B_32', 'B_33', 'B_37', 'B_38', 'B_39', 'B_40', 'B_41', 'B_42', 'D_39', 'D_41', 'D_42', 'D_43', 'D_44', 'D_45', 'D_46', 'D_47', 'D_48', 'D_50', 'D_51', 'D_53', 'D_54', 'D_55', 'D_58', 'D_59', 'D_60', 'D_61', 'D_62', 'D_65', 'D_66', 'D_69', 'D_70', 'D_71', 'D_72', 'D_73', 'D_74', 'D_75', 'D_76', 'D_77', 'D_78', 'D_80', 'D_82', 'D_84', 'D_86', 'D_91', 'D_92', 'D_94', 'D_96', 'D_103', 'D_104', 'D_108', 'D_112', 'D_113', 'D_114', 'D_115', 'D_117', 'D_118', 'D_119', 'D_120', 'D_121', 'D_122', 'D_123', 'D_124', 'D_125', 'D_126', 'D_128', 'D_129', 'D_131', 'D_132', 'D_133', 'D_134', 'D_135', 'D_136', 'D_140', 'D_141', 'D_142', 'D_144', 'D_145', 'P_2', 'P_3', 'P_4', 'R_1', 'R_2', 'R_3', 'R_7', 'R_8', 'R_9', 'R_10', 'R_11', 'R_14', 'R_15', 'R_16', 'R_17', 'R_20', 'R_21', 'R_22', 'R_24', 'R_26', 'R_27', 'S_3', 'S_5', 'S_6', 'S_7', 'S_9', 'S_11', 'S_12', 'S_13', 'S_15', 'S_16', 'S_18', 'S_22', 'S_23', 'S_25', 'S_26']
    feat = [F.col(c) for c in features_avg]
    exprs = {x: "avg" for x in features_avg}
    df_avg = (training_df
          .groupBy('"customer_ID"')
          .agg(exprs)
          .rename({F.col(f"AVG({f})"): f"{f}_avg" for f in features_avg})
         )
    
    # Minimum
    features_min = ['B_2', 'B_4', 'B_5', 'B_9', 'B_13', 'B_14', 'B_15', 'B_16', 'B_17', 'B_19', 'B_20', 'B_28', 'B_29', 'B_33', 'B_36', 'B_42', 'D_39', 'D_41', 'D_42', 'D_45', 'D_46', 'D_48', 'D_50', 'D_51', 'D_53', 'D_55', 'D_56', 'D_58', 'D_59', 'D_60', 'D_62', 'D_70', 'D_71', 'D_74', 'D_75', 'D_78', 'D_83', 'D_102', 'D_112', 'D_113', 'D_115', 'D_118', 'D_119', 'D_121', 'D_122', 'D_128', 'D_132', 'D_140', 'D_141', 'D_144', 'D_145', 'P_2', 'P_3', 'R_1', 'R_27', 'S_3', 'S_5', 'S_7', 'S_9', 'S_11', 'S_12', 'S_23', 'S_25']
    exprs_min = {x: "min" for x in features_min}
    df_min = (training_df
          .groupBy('"customer_ID"')
          .agg(exprs_min)
          .rename({F.col(f"MIN({f})"): f"{f}_min" for f in features_min})
         )
    
    # Maximum
    features_max = ['B_1', 'B_2', 'B_3', 'B_4', 'B_5', 'B_6', 'B_7', 'B_8', 'B_9', 'B_10', 'B_12', 'B_13', 'B_14', 'B_15', 'B_16', 'B_17', 'B_18', 'B_19', 'B_21', 'B_23', 'B_24', 'B_25', 'B_29', 'B_30', 'B_33', 'B_37', 'B_38', 'B_39', 'B_40', 'B_42', 'D_39', 'D_41', 'D_42', 'D_43', 'D_44', 'D_45', 'D_46', 'D_47', 'D_48', 'D_49', 'D_50', 'D_52', 'D_55', 'D_56', 'D_58', 'D_59', 'D_60', 'D_61', 'D_63', 'D_64', 'D_65', 'D_70', 'D_71', 'D_72', 'D_73', 'D_74', 'D_76', 'D_77', 'D_78', 'D_80', 'D_82', 'D_84', 'D_91', 'D_102', 'D_105', 'D_107', 'D_110', 'D_111', 'D_112', 'D_115', 'D_116', 'D_117', 'D_118', 'D_119', 'D_121', 'D_122', 'D_123', 'D_124', 'D_125', 'D_126', 'D_128', 'D_131', 'D_132', 'D_133', 'D_134', 'D_135', 'D_136', 'D_138', 'D_140', 'D_141', 'D_142', 'D_144', 'D_145', 'P_2', 'P_3', 'P_4', 'R_1', 'R_3', 'R_5', 'R_6', 'R_7', 'R_8', 'R_10', 'R_11', 'R_14', 'R_17', 'R_20', 'R_26', 'R_27', 'S_3', 'S_5', 'S_7', 'S_8', 'S_11', 'S_12', 'S_13', 'S_15', 'S_16', 'S_22', 'S_23', 'S_24', 'S_25', 'S_26', 'S_27']
    exprs_max = {x: "max" for x in features_max}
    df_max = (training_df
          .groupBy('"customer_ID"')
          .agg(exprs_max)
          .rename({F.col(f"MAX({f})"): f"{f}_max" for f in features_max})
         )
    
    # Last
    features_last = ['B_1', 'B_2', 'B_3', 'B_4', 'B_5', 'B_6', 'B_7', 'B_8', 'B_9', 'B_10', 'B_11', 'B_12', 'B_13', 'B_14', 'B_15', 'B_16', 'B_17', 'B_18', 'B_19', 'B_20', 'B_21', 'B_22', 'B_23', 'B_24', 'B_25', 'B_26', 'B_28', 'B_29', 'B_30', 'B_32', 'B_33', 'B_36', 'B_37', 'B_38', 'B_39', 'B_40', 'B_41', 'B_42', 'D_39', 'D_41', 'D_42', 'D_43', 'D_44', 'D_45', 'D_46', 'D_47', 'D_48', 'D_49', 'D_50', 'D_51', 'D_52', 'D_53', 'D_54', 'D_55', 'D_56', 'D_58', 'D_59', 'D_60', 'D_61', 'D_62', 'D_63', 'D_64', 'D_65', 'D_69', 'D_70', 'D_71', 'D_72', 'D_73', 'D_75', 'D_76', 'D_77', 'D_78', 'D_79', 'D_80', 'D_81', 'D_82', 'D_83', 'D_86', 'D_91', 'D_96', 'D_105', 'D_106', 'D_112', 'D_114', 'D_119', 'D_120', 'D_121', 'D_122', 'D_124', 'D_125', 'D_126', 'D_127', 'D_130', 'D_131', 'D_132', 'D_133', 'D_134', 'D_138', 'D_140', 'D_141', 'D_142', 'D_145', 'P_2', 'P_3', 'P_4', 'R_1', 'R_2', 'R_3', 'R_4', 'R_5', 'R_6', 'R_7', 'R_8', 'R_9', 'R_10', 'R_11', 'R_12', 'R_13', 'R_14', 'R_15', 'R_19', 'R_20', 'R_26', 'R_27', 'S_3', 'S_5', 'S_6', 'S_7', 'S_8', 'S_9', 'S_11', 'S_12', 'S_13', 'S_16', 'S_19', 'S_20', 'S_22', 'S_23', 'S_24', 'S_25', 'S_26', 'S_27', '"customer_ID"']
    w = snp.Window.partition_by('"customer_ID"').order_by(F.col('S_2').desc())
    df_last = training_df.withColumn("rn", F.row_number().over(w)).filter("rn = 1").select(features_last)
    
    # Join
    feature_df = df_min.natural_join(df_avg)
    feature_df = feature_df.natural_join(df_max)
    feature_df = feature_df.natural_join(df_last)

    feature_df.write.save_as_table(target_table, mode="append")
    
    return "Success"
$$;

CALL cc_profile_processing('CC_DEFAULT_TRAINING_DATA', 'SCORED_DATA');
```

Lets also wrap the UDF in a task so we can automate the scoring as well

```SQL
CREATE OR REPLACE PROCEDURE cc_batch_processing(rawTable VARCHAR, targetTable VARCHAR)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'cc_batch_processing'
AS
$$
from snowflake.snowpark.functions import call_udf
import snowflake.snowpark.functions as F

def cc_batch_processing(session, raw_table, target_table):

    batch_df = session.table(raw_table)
    feature_cols = batch_df.columns
    feature_cols.remove('"customer_ID"')
    
    scored_data = batch_df.select('"customer_ID"', call_udf("batch_predict_cc_default", [F.col(c) for c in feature_cols]).alias('Prediction'))
    
    scored_data.write.save_as_table(target_table, mode="append")

    return "Success"
$$;
```

<!-- ------------------------ -->
## Provider Account - Share New Data
Duration: 2

In this section, we will go back to assuming the role of the bank. We will switch back to our original provider account and create another listing of unscored data to share to our partner to score for default risk. This time however, we will create a [stream on the shared table](https://docs.snowflake.com/en/user-guide/data-sharing-provider#label-data-sharing-streams) so the new data can be shared live (without etl).

The first thing we need to do is to enable change tracking on the table to be shared. This will add a pair of hidden columns automatically to the table and begin storing change tracking metadata.

```SQL
ALTER TABLE DATA_SHARING_DEMO.DATA_SHARING_DEMO.CC_DEFAULT_UNSCORED_TABLE SET CHANGE_TRACKING = TRUE;
```

Next, lets add this data to the listing. Navigate to Data > Private Sharing in Snowsight. Then select "Shared By Your Account" in the top menu, and select "DATA_SHARING_DEMO".

Scroll to the Data section and select "Edit". Screenshot below
![Diagram](assets/update_listing.png)

From this screen, select the "CC_DEFAULT_UNSCORED_TABLE" and click "Done", then in the following screen, click "Save".

Your listing has now been updated, and the Consumer Account will be able to see the new table.

<!-- ------------------------ -->
## Consumer Account - Automate Scoring Pipeline
Duration: 2

Switch over to the Consumer Account, and you should see the newly shared table in the databases tab. If not, click the ellipsis and click "Refresh". Screenshot below.
![Diagram](assets/updated_listing_in_consumer_navigation.png)

Next we will create a pipeline from streams and tasks to automate the feature engineering of the newly shared data, score it, and make it available to the Bank.

First we will create a Stream on the newly shared table with the following code, and check it was created successfully

```SQL
CREATE OR REPLACE STREAM CC_DEFAULT_DATA_STREAM ON TABLE CC_DEFAULT_TRAINING_DATA.DATA_SHARING_DEMO.CC_DEFAULT_UNSCORED_TABLE;

SHOW STREAMS;
```
Next, lets set up a task to transform this data, using the stored procedures and UDFs we created in step 8.

```SQL
CREATE OR REPLACE TASK CDC
    WAREHOUSE = 'QUERY_WH'
    -- We would add a schedule in production, but this is commented out to avoid accidental credit consumption
    -- SCHEDULE = '5 minute'
WHEN
  SYSTEM$STREAM_HAS_DATA('CC_DEFAULT_DATA_STREAM')
AS
  CREATE OR REPLACE TEMPORARY TABLE NEW_CC_DEFAULT_DATA AS (
    SELECT * FROM 'CC_DEFAULT_TRAINING_DATA.DATA_SHARING_DEMO.CC_DEFAULT_UNSCORED_TABLE'
    WHERE METADATA$ACTION = 'INSERT'
  );
```

```SQL
CREATE OR REPLACE TASK FEATURE_ENG
    WAREHOUSE = 'QUERY_WH'
AFTER CDC
AS
    CALL cc_profile_processing('NEW_CC_DEFAULT_DATA', 'TRANSFORMED_TABLE');
```

Then we make a task depndant on the above

```SQL
CREATE TASK score_data 
    WAREHOUSE = 'QUERY_WH'
AFTER FEATURE_ENG
AS 
CALL cc_batch_processing('TRANSFORMED_TABLE', 'SCORED_TABLE');
```
Check the tasks are created

```SQL
SHOW TASKS;
```

And resume the root

```SQL
ALTER TASK CDC RESUME;
```

```SQL
EXECUTE TASK FEATURE_ENG;
```

If you want to see the status of your tasks, you can run the following query

```SQL
select *
  from table(information_schema.task_history())
  order by scheduled_time;
```

Now lets share our scored table back to the Bank. This process is the same as step X in reverse. Navigate to Data > Provider Studio on the left hand menu. then click the Listings button in the top right. Screenshot is below: ![Diagram](assets/provider_studio_navigation.png)

In the modal, enter the name of the Private Listing that we wish to share with our external partner. We have named it SCORED_DATA. Screenshot is below: ![Diagram](assets/private_listing_navigation.png)

In the next modal, click the "+ Select" option. In this next modal, select the SCORED_DATA in the SCORED_MODEL database and schema. Add it to the listing. Change the Secure Share Identifier to SCORED_DATA and update the description of the listing. Lastly, we add the consumer accounts. Since we selected Private Listing, the accounts we specify in this option are the only accounts that will be able to discover and utilise this share. Add the consumer account identifier we noted from the previous section. A screenshow is below: ![Diagram](assets/create_listing_navigation.png)


<!-- ------------------------ -->
## Provider Account - Use Scored Data
Duration: 2

<!-- ------------------------ -->
## Provider Account - Add New Data
Duration: 2

In production, this step would most likely be an automated ingestion pipeline form a source system. However, for illustrative purposes, we will run the following query to update the table.



Test the new data is there by running the following query in a worksheet.

```SQL
SELECT
  *
FROM
  CC_DEFAULT_UNSCORED_TABLE
WHERE "customer_ID" = 'new_data';
```

This updated data has now updated the stream, which would be picked up by the consumer. This will then execute the first task to undertake feature engineering, and then a second dependant task which would invoke our model and score the data. This new scored data would be appended to the shared table, and automatically shared back to the original provider.

<!-- ------------------------ -->
## Wrap Up and Clean Up
Duration: 2
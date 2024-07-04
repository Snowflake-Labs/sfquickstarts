author: Mats Stellwall
id: data_engineering_pipelines_with_snowpark_pandas
summary: This guide will provide step-by-step details for doing data engineering with Snowpark Pandas API
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering 

# Snowpark Pandas API Data Pipeline
<!-- ------------------------ -->
## Overview 

Through this quickstart guide, you will learn how to use the Snowpark Pandas API to create a customer profile based on the using the [Snowflake Sample TPC-H dataset](https://docs.snowflake.com/en/user-guide/sample-data-tpch), save it into a Snowflake table and to create a serverless task to schedule the feature engineering.

### What Is Snowpark?

Snowpark is the set of libraries and code execution environments that run Python and other programming languages next to your data in Snowflake.

* **Client Side Libraries** - Snowpark libraries can be installed and downloaded from any client-side notebook or IDE and are used for code development and deployment. Libraries include the Snowpark Pandas API, which provides Python APIs to run your pandas code directly on your data in Snowflake.
* **Code Execution Environments** - Snowpark provides elastic compute environments for secure execution of your code in Snowflake. Runtime options include Python, Java, and Scala in warehouses, container runtimes for out-of-the-box distributed processing with CPUs or GPUs using any Python framework, or custom runtimes brought in from Snowpark Container Services to execute any language of choice with CPU or GPU compute.

Learn more about [Snowpark](http://www.snowflake.com/snowpark).

### What Is Snowpark Pandas API?
The Snowpark pandas API is a module in the Snowpark library that lets you run your pandas code directly on your data in Snowflake. Just by changing the import statement and a few lines of code, you can get the same pandas-native experience you know and love with the scalability and security benefits of Snowflake. With this API, you can work with much larger datasets so you can avoid the time and expense of porting your pandas pipelines to other big data frameworks or using larger and more expensive machines. It runs workloads natively in Snowflake through translation to SQL, enabling it to take advantage of parallelization and the data governance and security benefits of Snowflake.

#### Benefits Of Using The Snowpark Pandas API
* **Meeting Python developers where they are** – This API offers a familiar interface to Python developers by providing a pandas-compatible layer that can run natively in Snowflake.
* **Scalable distributed pandas** – This API bridges the convenience of pandas with the scalability of mature data infrastructure. pandas can now run at Snowflake speed and scale by leveraging pre-existing query optimization techniques within Snowflake. No code rewrites or complex tuning are required, so you can move from prototype to production seamlessly.
* **Security and governance** – Data does not leave Snowflake’s secure platform. The Snowpark pandas API allows uniformity within data organizations on how data is accessed and allows for easier auditing and governance.
* **No additional compute infrastructure to manage and tune** – This feature leverages the Snowflake engine, and you do not need to set up or manage any additional compute infrastructure.

Learn more about [Snowpark Pandas API](https://docs.snowflake.com/en/developer-guide/snowpark/python/snowpark-pandas).

### What You’ll Learn
* how to create Snowpark Pandas dataframe from a Snowflake table
* how to aggregate data to create new features
* how to Join Snowpark Pandas dataframes
* how to save a Snowpark Pandas dataframe into a Snowflake table
* how to create a serverless task to schedule the feature engineering

### Prerequisites
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
    > aside positive
    >
    >Clone or download the [git repo](https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas)
* A Snowflake account. If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/).
* A Snowflake account login with a role that has the ability to create database, schema and tables. If not, you will need to register for a free trial or use a different role.

### What You’ll Build 
A Customer profile table using the Snowpark Pandas API and a serverless task that will run the feature engineering on a schedule.

<!-- ------------------------ -->
## Setup The Snowflake Environment
Duration: 10

### Overview
This section covers cloning of the GitHub repository and creating the needed Snowflake objects (i.e role, warehouse, database, schema, etc..)

### Clone The Git Repository
The very first step is to clone the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas). This repository contains all the code you will need to successfully complete this QuickStart Guide.

Using HTTPS:

```shell
git clone https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas.git
```

OR, using SSH:

```shell
git clone git@github.com:Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas.git
```

You can also use the Git integration feature of Snowflake Notebooks, in order to do that you need to fork the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas) to be allowed to commit changes. For instructions how to set up Git integration for your Snowflake account see [here](https://docs.snowflake.com/developer-guide/git/git-setting-up) and for using it with Snowflake Notebooks see [this page](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-snowgit).

<!-- ------------------------ -->
## Setup Snowflake

Duration: 10

During this step you will verify that the [Snowflake Sample TPC-H dataset](https://docs.snowflake.com/en/user-guide/sample-data-tpch) is available in your account, and if not add the share.

### Verify that the Snowflake Sample TPC-H Dataset Is Available

1. Log into [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) for your account
2. Navigate to **Databases**
3. Verify that you can see the **SNOWFLAKE_SAMPLE_DATA** database, if it is missing then you can add it folling the instructions in https://docs.snowflake.com/en/user-guide/sample-data-using

### Create Database, Schema And Warehouse To Be Used

```SQL
USE ROLE ACCOUNTADMIN;

CREATE DATABASE SNOW_PANDAS_DE_QS;
CREATE SCHEMA SNOW_PANDAS_DE_QS.NOTEBOOKS;
CREATE SCHEMA SNOW_PANDAS_DE_QS.DATA;

CREATE WAREHOUSE SNOW_PANDAS_DE_QS_WH;
```
### Create Snowflake Notebook

### Navigate To Snowflake Notebooks

1. Navigate to the Notebooks section by clicking **Projects** and then **Notebooks**  
![Navigate to Notebooks](assets/navigate_to_notebooks.png)  
2. Click on the **down arrow* next to **+ Notebook**  
![New notebook drop down](assets/new_notebook_dropdown.png)  
3. If you have set up git integration choose  **Create from repository** if not, then choose **import .ipynb file**.
![New notebook from menu](assets/notebook_from_menu.png)  

### Import .ipynb File
1. Navigate to where you have cloned the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas) and select **Customer Profile Creation Pipeline.ipynb** and click **Open**  
![Select Notebook File](assets/select_notebook_file.png)  
2. Keep the name, select **SNOW_PANDAS_DE_QS** and **NOTEBOOKS** for **Notebook location**, **SNOW_PANDAS_DE_QS_WH** for **Notebook warehouse** and click **Create**  
![Select Notebook File](assets/notebook_dialog.png)  

### Create From Repository

If you have forked the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas) and create a integration to it in Snowflake you can open the notebook directly from the git repository.

1. In the **Create Notebook from Repository** dialog click on **Select .ipynb file**  
![Create Notebook from Repository Dialog](assets/create_from_rep_start.png)  
2 Click on the repository integration you are using and select **Customer Profile Creation Pipeline.ipynb** and click **Select File**, if you do not see the file press **Fetch** to refresh with the latest changes from the repository  
![Select Notebook File from Repository](assets/select_file_from_rep.png)  
3. Name it **Customer Profile Creation Pipeline**, select **SNOW_PANDAS_DE_QS**, **NOTEBOOKS** for **Notebook location** and **SNOW_PANDAS_DE_QS_WH** for **Notebook warehouse** and click **Create**  
![Create Notebook from Repository Dialog](assets/create_from_rep_end.png)  

### Add Required Python Libraries

Before you run the notebook you need to add the following Python libraries:
* modin
* snowflake
* matplotlib
* seaborn

1. In the Notebook click on **Packages**  
2. Search for **modin** and select **modin** in the list  
![Modin search result](assets/modin_result.png)  
3. Do the same for **snowflake**, **matplotlib** and **seaborn**. When done you should have the same packages as the list below (the versions might differ)  
![Added packages](assets/added_packages.png)  


<!-- ------------------------ -->
## Data Engineering With Snowpark Pandas
Duration: 30

During this step you will learn how to use the Snowpark Pandas API to:
* Create datframe from a Snowflake table
* Aggregate data to create new features
* Join dataframes
* Save the result into a Snowflake table
* Create a serverless task to schedule the feature engineering pipeline (Currently in Private Preview)

### Run The Code In The Notebook

Run each of the cells in the Notebook.

Within this Notebook, we will use Snowpark Pandas API to create DataFrames, join them, create new features and create a serverless task to schedule the feature engineering.

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 4

Congratulations, you have successfully completed this quickstart! Through this quickstart, we were able to showcase how you can use the Snowpark Pandas API to create DataFrames, join them, create new features , save the result to a Snowflake table and create a serverless task to schedule the feature engineering.

### What we've covered

* Create datframe from a Snowflake table
* Aggregate data to create new features
* Join dataframes
* Save the result into a Snowflake table
* Create a serverless task to schedule the feature engineering

### Related Resources

* [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-data-engineering-pipelines-with-snowpark-pandas)
* [Snowpark Pandas API Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/snowpark-pandas)
* [Getting Started with Snowpark pandas QuikStart](https://quickstarts.snowflake.com/guide/getting_started_with_snowpark_pandas/index.html)

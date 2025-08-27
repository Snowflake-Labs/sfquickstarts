author: Vino Duraisamy, Kala Govindarajan
id: getting_started_with_snowpark_connect_for_apache_spark
summary: This quickstart guide shows you how to get started with Snowpark Connect for Apache Spark™ categories: Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Apache Spark, Snowpark, Python, Data Engineering

# Getting started with Snowpark Connect for Apache Spark
<!-- ------------------------ -->
Duration:5

## Overview

Through this quickstart, you will learn how to get started with [Snowpark Connect for Apache Spark™](https://www.snowflake.com/en/blog/snowpark-connect-apache-spark-preview/). Using Snowpark Connect for Apache Spark, you can run Spark workloads directly on Snowflake.

### What you’ll learn

By the end of this quickstart, you will learn how to:

* Connect to the Snowpark Connect server
* Execute simple PySpark code
* Create nested table structures in PySpark and write to Snowflake

### What is Snowpark?

Snowpark is the set of libraries and code execution environments that run Python and other programming languages next to your data in Snowflake. Snowpark can be used to build data pipelines, ML models, apps, and other data processing tasks.

### What is Snowpark Connect for Apache Spark?

With Snowpark Connect for Apache Spark, you can connect your existing Spark workloads directly to Snowflake and run them on the Snowflake compute engine. Snowpark Connect for Spark supports using the Spark DataFrame API on Snowflake. All workloads run on Snowflake warehouse. As a result, you can run your PySpark dataframe code with all the benefits of the Snowflake engine.

In Apache Spark™ version 3.4, the Apache Spark community introduced Spark Connect. Its decoupled client-server architecture separates the user’s code from the Spark cluster where the work is done. This new architecture makes it possible for Snowflake to power Spark jobs.

### What You'll Build

* Run simple PySpark code examples from Snowflake

* Create a Spark UDF(User Defined Function), register it and invoke it directly from a Snowflake Notebook

* Create a Snowflake Python Function and invole it with SQL passthrough from Spark

### Pre-requisites

* A Snowflake account. If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/).

<!-- ------------------------ -->
## Setup

Duration:10

This section covers the Snowflake objects creation and other setup needed to run this quickstart successfully.

* Login to your Snowflake free trial account.
* Navigate to Data on the left pane. Click on Databases. Create a database and call it `AVALANCHE_DB`.
* Click on `avalanche_db`, select `create schema` and call it `AVALANCHE_SCHEMA`.  
* Select Admin on the left pane and click on warehouses. Create a new warehouse. Name it `DE_M`. Select type as standard and size as M.  
* On a new browser tab, navigate to this [git repo](https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/intro_to_de_python) and download the `DE_100.ipynb` file.
* On the left pane, select Projects -> Notebooks. Click on the down arrow and select `Import ipynb file` to load a notebook. Call it `AVALANCHE_ANALYTICS_NB`. Select `AVALANCHE_DB` for database and `AVALANCHE_SCHEMA` for schema, Query warehouse as `DE_M` and create notebook.  
* After the notebook is created, at the top right, click on packages. Search and install modin. Pick the package version as 0.30.1 instead of latest.
* On a new browser tab, navigate to this [git repo](https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/intro_to_de_python) and download the `order-history.csv` and `shipping-logs.csv` files to your local.  
* Switch back to the Snowflake UI, On the left panel right below the name of the notebook, there is a `+` sign. Click on `+` to load the `order-history.csv` and `shipping-logs.csv` files to your notebook workspace.

With this, we are ready to run our first data engineering pipeline in Snowflake using Python.

<!-- ------------------------ -->
## Data Engineering using Python

Duration:10

During this step you will learn how to use pandas on Snowflake to:

* Create a pandas dataframe from a local csv data file  
* Clean up and transform data to create new features  
* Join dataframes

You will also learn how to use Snowpark Python to:

* Create a Snowflake table from a csv file stored in AWS S3 bucket  
* Load the Snowflake table as a Snowpark dataframe  
* Aggregate data to derive insights  
* Save the result into a Snowflake table

In addition to the ingestion and transformation steps above, you will learn how to:

* Create a serverless task to schedule the pipeline

Follow along and run each of the cells in the [Notebook](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/intro_to_de_python/DE_100.ipynb).

<!-- ------------------------ -->
## Conclusion & Resources

Duration:2

Congratulations, you have successfully completed this quickstart\! 

### What you learned

* How to install and configure the Snowpark pandas library  
* How to use Snowpark pandas to transform and analyze datasets using the power of Snowflake  
* How to use Snowpark Python to transform and aggregate data

### Related Resources

* [Pandas on Snowflake](https://docs.snowflake.com/developer-guide/snowpark/python/pandas-on-snowflake)  
* [Snowpark Python Dataframe API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)  
* [Source code on GitHub](https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/intro\_to\_de\_python)  

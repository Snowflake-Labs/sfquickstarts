author: Vino Duraisamy, Jacob Prall
id: intro-to-snowpark-connect-for-apache-spark
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/snowpark
language: en
summary: This quickstart guide shows you how to get started with Snowpark Connect for Apache Spark™ categories: Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Intro to Snowpark Connect for Apache Spark
<!-- ------------------------ -->

## Overview

Through this guide, you will learn how to get started with [Snowpark Connect for Apache Spark™](/en/blog/snowpark-connect-apache-spark-preview/). Snowpark Connect allows you to run the **PySpark DataFrame API** on **Snowflake infrastructure**. 

### What You’ll Learn

**In this guide, you will learn:**

- How Snowpark Connect executes PySpark on Snowflake infrastructure
- How to build production pipelines with Snowpark Connect
    - Data ingestion patterns (tables, stages, cloud storage)
    - Transformations, joins, and aggregations
    - Writing data with partitioning and compression
    - Integrating with telemetry and best practices

### What is Snowpark?

Snowpark is the set of libraries and code execution environments that run Python and other programming languages next to your data in Snowflake. Snowpark can be used to build data pipelines, ML models, apps, and other data processing tasks.

### What is Snowpark Connect for Apache Spark™?

With Snowpark Connect for Apache Spark, you can connect your existing Spark workloads directly to Snowflake and run them on the Snowflake compute engine. Snowpark Connect for Spark supports using the Spark DataFrame API on Snowflake. All workloads run on Snowflake warehouse. As a result, you can run your PySpark dataframe code with all the benefits of the Snowflake engine.

In Apache Spark™ version 3.4, the Apache Spark community introduced Spark Connect. Its decoupled client-server architecture separates the user’s code from the Spark cluster where the work is done. This new architecture makes it possible for Snowflake to power Spark jobs.

![Snowpark Connect](assets/snowpark_connect.png)

### Snowpark Connect - Key Concepts

**Execution Model:**
- Your DataFrame operations are translated to Snowflake SQL
- Computation happens in Snowflake warehouses
- Results stream back via Apache Arrow format
- No Spark cluster, driver, or executors

**Query Pushdown:**
- ✅ **Fully Optimized:** DataFrame operations, SQL functions, aggregations push down to Snowflake
- ⚠️ **Performance Impact:** Python UDFs run client-side (fetch data → process → send back)
- 💡 **Better Alternative:** Use built-in SQL functions instead of UDFs

**CLI: Snowpark Submit**
- Run Spark workloads as batch jobs using Snowpark Submit CLI
- To install: ```pip install snowpark-submit```
- To submit a job, run: 

``` 
snowpark-submit \
  --snowflake-workload-name MY_JOB \
  --snowflake-connection-name MY_CONNECTION \
  --compute-pool MY_COMPUTE_POOL \
  app.py
```

[CLI examples](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-submit-examples)


### What You'll Build

In this guide, you will build an end to end demo pipeline for **Tasty Bytes Menu Analytics**

we will cover key aspects of using Snowpark Connect through a production-ready pipeline that analyzes menu profitability for Tasty Bytes, a fictitious global food truck network. 

#### Pipeline Structure

 1. Setup & Configuration
 2. Telemetry Initialization
 3. Data Ingestion
 4. Data Validation
 5. Transformations (profit analysis)
 6. Data Quality Checks
 7. Write Output
 8. Cleanup & Summary

### Prerequisites

* A Snowflake account. If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/).

<!-- ------------------------ -->
## Run PySpark Code

During this step you will learn how to run PySpark code on Snowflake to:

* Connect to the Snowpark Connect server
* Ingest Data & understand data ingestion patterns (tables, stages, cloud storage)
* Run transformations, joins, and aggregations
* Write data with partitioning and compression options enabled
* Integrate with telemetry and other best practices

Sign up for a [Snowflake Free Trial](https://signup.snowflake.com/) account and login to Snowflake home page. 

Download the `intro_to_snowpark_connect.ipynb` from [this git repository](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/intro_to_snowpark_connect.ipynb).

### Import the Notebook with PySpark code into Snowflake

* In the Snowsight UI, navigate to `Projects` and click on `Notebooks`.
* On the top right, click on the down arrow next to `+ Notebook` and select `Import ipynb file`.
* Select the `intro_to_snowpark_connect.ipynb` you had downloaded earlier.
* Select notebook location as `snowflake_learning_db` and `public` schema.
* Select `run on warehouse` option, select `query warehouse` as `compute_wh` and `create`.

Now you have successfully imported the notebook that contains PySpark code.

### Install snowpark-connect Package and run the code

Next up, select the packages drop down at the top right of the notebook. Look for `snowpark-connect` package and install it using the package picker.

After the installation is complete, start or restart the notebook session.

Follow along and run each of the cells in the [Notebook](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/intro_to_snowpark_connect.ipynb).

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations, you have successfully completed this quickstart! 

### What You Learned

* Connect to the Snowpark Connect server
* Ingest Data & understand data ingestion patterns (tables, stages, cloud storage)
* Run transformations, joins, and aggregations
* Write data with partitioning and compression options enabled
* Integrate with telemetry and other best practices

### Related Resources

* [Snowpark Connect](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)   
* [Source code on GitHub](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/intro_to_snowpark_connect.ipynb)
* [Other Snowpark Connect examples](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/snowpark_connect/getting_started_with_snowpark_connect_for_apache_spark.ipynb) 

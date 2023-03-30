id: getting_started_with_dataengineering_ml_using_snowpark_python
summary: Getting Started with Data Engineering and ML using Snowpark for Python
categories: featured,getting-started,data-science-&-ml,data-engineering,app-development
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Snowpark Python, Streamlit, scikit-learn, Data Engineering, Machine Learning
authors: Dash Desai

# Getting Started with Data Engineering and ML using Snowpark for Python
<!-- ------------------------ -->
## Overview

Duration: 5

By completing this guide, you will be able to go from raw data to an interactive application that can help organizations optimize their advertising budget allocation.

Here is a summary of what you will be able to learn in each step by following this quickstart:

- **Setup Environment**: Use stages and tables to ingest and organize raw data from S3 into Snowflake
- **Data Engineering**: Leverage Snowpark for Python DataFrames to perform data transformations such as group by, aggregate, pivot, and join to prep the data for downstream applications.
- **Data Pipelines**: Use Snowflake Tasks to turn your data pipeline code into operational pipelines with integrated monitoring.  
- **Machine Learning**: Prepare data and run ML Training in Snowflake using scikit-learn and deploy the model as a Snowpark User-Defined-Function (UDF) using the integrated Anaconda package repository.
- **Streamlit Application**: Build an interactive application using Python (no web development experience required) to help visualize the ROI of different advertising spend budgets.

In case you are new to some of the technologies mentioned above, here’s a quick summary with links to documentation.

### What is Snowpark?

It allows developers to query data and write data applications in languages other than SQL using a set of APIs and DataFrame-style programming constructs in Python, Java, and Scala. These applications run on and take advantage of the same distributed computation on Snowflake's elastic engine as your SQL workloads. Learn more about [Snowpark](https://www.snowflake.com/snowpark/).

![Snowpark](assets/snowpark_python0.png)

### What is Streamlit?

Streamlit is a pure-Python [open source](https://github.com/streamlit/streamlit) application framework that enables developers to quickly and easily write, share, and deploy data applications. Learn more about [Streamlit](https://streamlit.io/).

### What is scikit-learn?

It is one of the most popular [open source](https://scikit-learn.org/) machine learning libraries for Python that also happens to be pre-installed and available for developers to use in Snowpark for Python via [Snowflake Anaconda](https://snowpark-python-packages.streamlit.app/) channel. This means that you can use it in Snowpark for Python User-Defined Functions and Stored Procedures without having to manually install it and manage all of its dependencies.

### What You’ll Learn

- How to analyze data and perform data engineering tasks using Snowpark DataFrames and APIs
- How to use open-source Python libraries like scikit-learn from curated Snowflake Anaconda channel
- How to deploy ML model training code on Snowflake using Snowpark Python Stored Procedure
- How to create Scalar and Vectorized Snowpark Python User-Defined Functions (UDFs) for online and offline inference respectively
- How to create Snowflake Tasks to automate data pipelines
- How to create Streamlit web application that uses the Scalar UDF for inference based on user input

### Prerequisites

- A Snowflake account with [Anaconda Packages enabled by ORGADMIN](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#using-third-party-packages-from-anaconda). If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/).
- A Snowflake account login with ACCOUNTADMIN role. If you have this role in your environment, you may choose to use it. If not, you will need to 1) Register for a free trial, 2) Use a different role that has the ability to create database, schema, tables, stages, tasks, user-defined functions, and stored procedures OR 3) Use an existing database and schema in which you are able to create the mentioned objects.

<!-- ------------------------ -->
## Setup Environment

Duration: 15

### Create Tables, Load Data and Setup Stages

Log into [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) using your credentials to create tables, load data from Amazon S3, and setup Snowflake internal stages.

> aside positive
> IMPORTANT: If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.

Run the following SQL commands to create the [warehouse](https://docs.snowflake.com/en/sql-reference/sql/create-warehouse.html), [database](https://docs.snowflake.com/en/sql-reference/sql/create-database.html) and [schema](https://docs.snowflake.com/en/sql-reference/sql/create-schema.html).

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE WAREHOUSE DASH_L;
CREATE OR REPLACE DATABASE DASH_DB;
CREATE OR REPLACE SCHEMA DASH_SCHEMA;

USE DASH_DB.DASH_SCHEMA;
```

Run the following SQL commands to create table **CAMPAIGN_SPEND** from data hosted on publicly accessible S3 bucket.

```sql
CREATE or REPLACE file format csvformat
  skip_header = 1
  type = 'CSV';

CREATE or REPLACE stage campaign_data_stage
  file_format = csvformat
  url = 's3://sfquickstarts/ad-spend-roi-snowpark-python-scikit-learn-streamlit/campaign_spend/';

CREATE or REPLACE TABLE CAMPAIGN_SPEND (
  CAMPAIGN VARCHAR(60), 
  CHANNEL VARCHAR(60),
  DATE DATE,
  TOTAL_CLICKS NUMBER(38,0),
  TOTAL_COST NUMBER(38,0),
  ADS_SERVED NUMBER(38,0)
);

COPY into CAMPAIGN_SPEND
  from @campaign_data_stage;
```

Run the following SQL commands to create table **MONTHLY_REVENUE** from data hosted on publicly accessible S3 bucket.

```sql
CREATE or REPLACE stage monthly_revenue_data_stage
  file_format = csvformat
  url = 's3://sfquickstarts/ad-spend-roi-snowpark-python-scikit-learn-streamlit/monthly_revenue/';

CREATE or REPLACE TABLE MONTHLY_REVENUE (
  YEAR NUMBER(38,0),
  MONTH NUMBER(38,0),
  REVENUE FLOAT
);

COPY into MONTHLY_REVENUE
  from @monthly_revenue_data_stage;
```

Run the following SQL commands to create table **BUDGET_ALLOCATIONS_AND_ROI** that holds the last six months of budget allocations and ROI.

```sql
CREATE or REPLACE TABLE BUDGET_ALLOCATIONS_AND_ROI (
  MONTH varchar(30),
  SEARCHENGINE integer,
  SOCIALMEDIA integer,
  VIDEO integer,
  EMAIL integer,
  ROI float
);

INSERT INTO BUDGET_ALLOCATIONS_AND_ROI (MONTH, SEARCHENGINE, SOCIALMEDIA, VIDEO, EMAIL, ROI)
VALUES
('January',35,50,35,85,8.22),
('February',75,50,35,85,13.90),
('March',15,50,35,15,7.34),
('April',25,80,40,90,13.23),
('May',95,95,10,95,6.246),
('June',35,50,35,85,8.22);
```

Run the following commands to create Snowflake [internal stages](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-create-stage) for storing Stored Procedures, UDFs, and ML model files.

```sql
CREATE OR REPLACE STAGE dash_sprocs;
CREATE OR REPLACE STAGE dash_models;
CREATE OR REPLACE STAGE dash_udfs;
```

Optionally, you can also open [setup.sql](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/setup.sql) in Snowsight and run all SQL statements to create the objects and load data from AWS S3.

> aside positive
> IMPORTANT: If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.

<!-- ------------------------ -->
## Clone GitHub Repository

Duration: 8

This section covers cloning of the GitHub repository and creating a Python 3.8 environment.

1) Clone [GitHub repository](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn)

2) Download the miniconda installer from [https://conda.io/miniconda.html](https://conda.io/miniconda.html). *(OR, you may use any other Python environment with Python 3.8)*.

3) From the root folder, create conda environment. Let's name the environment **snowpark-de-ml**.

> aside positive
> IMPORTANT:
> - If you are using a machine wth Apple M1 chip, follow [these instructons](https://docs.snowflake.com/en/developer-guide/snowpark/python/setup) to create the virtual environment and install Snowpark Python instead of what's described below.
> - If you already have an account on [Hex](https://app.hex.tech/login), then Snowpark for Python is built-in so you don't have to install it. In that case, skip to the next section.

```python
conda create --name snowpark-de-ml -c https://repo.anaconda.com/pkgs/snowflake python=3.8
conda activate snowpark-de-ml
```

4) Install Snowpark Python and other libraries including Streamlit

```python
conda install -c https://repo.anaconda.com/pkgs/snowflake snowflake-snowpark-python pandas notebook scikit-learn cachetools
pip install streamlit
```

> aside negative
> Note: The versions at the time of writing this -- **snowflake-snowpark-python 1.0.0, streamlit 1.18.1**.

5) Update [connection.json](https://github.com/Snowflake-Labs/sfguide-ml-model-snowpark-python-scikit-learn-streamlit/blob/main/connection.json) with your Snowflake account details and credentials.

> aside negative
> Note: For the account parameter, specify your [account identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html) and do not include the snowflakecomputing.com domain name. Snowflake automatically appends this when creating the connection.*

---

### Troubleshooting `pyarrow` related issues

- If you have `pyarrow` library already installed, uninstall it before installing Snowpark.
- If you do not have `pyarrow` installed, you do not need to install it yourself; installing Snowpark automatically installs the appropriate version.
- Do not reinstall a different version of `pyarrow` after installing Snowpark.

<!-- ------------------------ -->
## Data Engineering

Duration: 20

The Notebook linked below covers the following data engineering tasks.

1) Establish secure connection from Snowpark Python to Snowflake
2) Load data from Snowflake tables into Snowpark DataFrames
3) Perform Exploratory Data Analysis on Snowpark DataFrames
4) Pivot and Join data from multiple tables using Snowpark DataFrames
5) Automate data pipeline tasks using Snowflake Tasks

### Data Engineering Notebook in Jupyter or Visual Studio Code

To get started, follow these steps:

1) In a terminal window, browse to this folder and run `jupyter notebook` at the command line. (You may also use other tools and IDEs such Visual Studio Code.)

2) Open and run through the cells in [Snowpark_For_Python_DE.ipynb](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_For_Python_DE.ipynb)

> aside positive
> IMPORTANT: Make sure in the Jupyter notebook the (Python) kernel is set to ***snowpark-de-ml***-- which is the name of the environment created in **Clone GitHub Repository** step.

### Data Engineering Notebook in Hex

If you already have an account on [Hex](https://app.hex.tech/login), then Snowpark for Python is built-in so you don't have to install it.

1) Import [Snowpark_For_Python_DE.ipynb](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_For_Python_DE.ipynb) as a Project in your account. For more information on importing, refer to the [docs](https://learn.hex.tech/docs/versioning/import-export).

2) Then, instead of using the [connection.json](https://github.com/Snowflake-Labs/sfguide-ml-model-snowpark-python-scikit-learn-streamlit/blob/main/connection.json) to connect to Snowflake, create a [Data Connection](https://learn.hex.tech/tutorials/connect-to-data/get-your-data#set-up-a-data-connection-to-your-database) and use that in the Data Engineering Notebook as shown below.

![HEX Data Connection](assets/hex_data_connection.png)

> aside negative
> Note: You can also create shared data connections for your projects and users in your workspace. For more details, refer to the [docs](https://learn.hex.tech/docs/administration/workspace_settings/workspace-assets#shared-data-connections).

3) Replace the following code snippet

```python
connection_parameters = json.load(open('connection.json'))
session = Session.builder.configs(connection_parameters).create()
```

**with...**

```python
import hextoolkit
hex_snowflake_conn = hextoolkit.get_data_connection('YOUR_DATA_CONNECTION_NAME')
session = hex_snowflake_conn.get_snowpark_session()
```

<!-- ------------------------ -->
## Data Pipelines

In the [Data Engineering Notebook](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_For_Python_DE.ipynb), there's a section that demonstrates how to build and run data pipelines as [Snowflake Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro).

For reference purposes, here are the code snippets.

### **Root/parent Task**

```python
def campaign_spend_data_pipeline(session: Session) -> str:
  # DATA TRANSFORMATIONS
  # Perform the following actions to transform the data

  # Load the campaign spend data
  snow_df_spend_t = session.table('campaign_spend')

  # Transform the data so we can see total cost per year/month per channel using group_by() and agg() Snowpark DataFrame functions
  snow_df_spend_per_channel_t = snow_df_spend_t.group_by(year('DATE'), month('DATE'),'CHANNEL').agg(sum('TOTAL_COST').as_('TOTAL_COST')).\
      with_column_renamed('"YEAR(DATE)"',"YEAR").with_column_renamed('"MONTH(DATE)"',"MONTH").sort('YEAR','MONTH')

  # Transform the data so that each row will represent total cost across all channels per year/month using pivot() and sum() Snowpark DataFrame functions
  snow_df_spend_per_month_t = snow_df_spend_per_channel_t.pivot('CHANNEL',['search_engine','social_media','video','email']).sum('TOTAL_COST').sort('YEAR','MONTH')
  snow_df_spend_per_month_t = snow_df_spend_per_month_t.select(
      col("YEAR"),
      col("MONTH"),
      col("'search_engine'").as_("SEARCH_ENGINE"),
      col("'social_media'").as_("SOCIAL_MEDIA"),
      col("'video'").as_("VIDEO"),
      col("'email'").as_("EMAIL")
  )

  # Save transformed data
  snow_df_spend_per_month_t.write.mode('overwrite').save_as_table('SPEND_PER_MONTH')

# Register data pipelining function as a Stored Procedure so it can be run as a task
session.sproc.register(
  func=campaign_spend_data_pipeline,
  name="campaign_spend_data_pipeline",
  packages=['snowflake-snowpark-python'],
  is_permanent=True,
  stage_location="@dash_sprocs",
  replace=True)

campaign_spend_data_pipeline_task = """
CREATE OR REPLACE TASK campaign_spend_data_pipeline_task
    WAREHOUSE = 'DASH_L'
    SCHEDULE  = '3 MINUTE'
AS
    CALL campaign_spend_data_pipeline()
"""
session.sql(campaign_spend_data_pipeline_task).collect()
```

### **Child/dependant Task**

```python
def monthly_revenue_data_pipeline(session: Session) -> str:
  # Load revenue table and transform the data into revenue per year/month using group_by and agg() functions
  snow_df_spend_per_month_t = session.table('spend_per_month')
  snow_df_revenue_t = session.table('monthly_revenue')
  snow_df_revenue_per_month_t = snow_df_revenue_t.group_by('YEAR','MONTH').agg(sum('REVENUE')).sort('YEAR','MONTH').with_column_renamed('SUM(REVENUE)','REVENUE')

  # Join revenue data with the transformed campaign spend data so that our input features (i.e. cost per channel) and target variable (i.e. revenue) can be loaded into a single table for model training
  snow_df_spend_and_revenue_per_month_t = snow_df_spend_per_month_t.join(snow_df_revenue_per_month_t, ["YEAR","MONTH"])

  # SAVE in a new table for the next task
  snow_df_spend_and_revenue_per_month_t.write.mode('overwrite').save_as_table('SPEND_AND_REVENUE_PER_MONTH')

# Register data pipelining function as a Stored Procedure so it can be run as a task
session.sproc.register(
  func=monthly_revenue_data_pipeline,
  name="monthly_revenue_data_pipeline",
  packages=['snowflake-snowpark-python'],
  is_permanent=True,
  stage_location="@dash_sprocs",
  replace=True)

monthly_revenue_data_pipeline_task = """
  CREATE OR REPLACE TASK monthly_revenue_data_pipeline_task
      WAREHOUSE = 'DASH_L'
      AFTER campaign_spend_data_pipeline_task
  AS
      CALL monthly_revenue_data_pipeline()
  """
session.sql(monthly_revenue_data_pipeline_task).collect()
```

> aside negative
> Note: In the ***monthly_revenue_data_pipeline_task*** above, notice the **AFTER campaign_spend_data_pipeline_task** clause which makes it a dependant task.

#### Start Tasks

```sql
session.sql("alter task monthly_revenue_data_pipeline_task resume").collect()
session.sql("alter task campaign_spend_data_pipeline_task resume").collect()
```

#### Suspend Tasks

```sql
session.sql("alter task campaign_spend_data_pipeline_task suspend").collect()
session.sql("alter task monthly_revenue_data_pipeline_task suspend").collect()
```

### Tasks Observability

These tasks and their [DAGs](https://docs.snowflake.com/en/user-guide/tasks-intro#label-task-dag) can be viewed in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight-tasks#viewing-individual-task-graphs) as shown below.

---

![Tasks-Observability](assets/snowflake_tasks.png)

---

### Error Notificatons For Tasks

You can also enable push notifications to a cloud messaging service when errors occur while tasks are being executed. For more information, please refer to the [documentation](https://docs.snowflake.com/en/user-guide/tasks-errors).

<!-- ------------------------ -->
## Machine Learning

Duration: 20

> aside negative
> PREREQUISITE: Successful completion of Data Engineering steps outlined in [Snowpark_For_Python_DE.ipynb](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_For_Python_DE.ipynb).

The Notebook linked below covers the following machine learning tasks.

1) Establish secure connection from Snowpark Python to Snowflake
2) Load features and target from Snowflake table into Snowpark DataFrame
3) Prepare features for model training
4) Create a [Python Stored Procedure](https://docs.snowflake.com/en/sql-reference/stored-procedures-python) to deploy model training code on Snowflake
5) Create Scalar and Vectorized (aka Batch) [Python User-Defined Functions (UDFs)](https://docs.snowflake.com/en/developer-guide/snowpark/python/creating-udfs) for inference on new data points for online and offline inference respectively.

---

![End-To-End-ML](assets/snowflake_e2e_ml.png)

---

### Machine Learning Notebook in Jupyter or Visual Studio Code

To get started, follow these steps:

1) In a terminal window, browse to this folder and run `jupyter notebook` at the command line. (You may also use other tools and IDEs such Visual Studio Code.)

2) Open and run through the [Snowpark_For_Python_ML.ipynb](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_For_Python_ML.ipynb)

> aside positive
> IMPORTANT: Make sure in the Jupyter notebook the (Python) kernel is set to ***snowpark-de-ml*** -- which is the name of the environment created in **Clone GitHub Repository** step.

### Machine Learning Notebook in Hex

If you already have an account on [Hex](https://app.hex.tech/login), then Snowpark for Python is built-in so you don't have to install it.

1) Import [Snowpark_For_Python_ML.ipynb](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_For_Python_ML.ipynb) as a Project in your account. For more information on importing, refer to the [docs](https://learn.hex.tech/docs/versioning/import-export).

2) Then, instead of using the [connection.json](https://github.com/Snowflake-Labs/sfguide-ml-model-snowpark-python-scikit-learn-streamlit/blob/main/connection.json) to connect to Snowflake, create a [Data Connection](https://learn.hex.tech/tutorials/connect-to-data/get-your-data#set-up-a-data-connection-to-your-database) and use that in the Machine Learning Notebook as shown below.

![HEX Data Connection](assets/hex_data_connection.png)

> aside negative
> Note: You can also create shared data connections for your projects and users in your workspace. For more details, refer to the [docs](https://learn.hex.tech/docs/administration/workspace_settings/workspace-assets#shared-data-connections).

3) Replace the following code snippet

```python
connection_parameters = json.load(open('connection.json'))
session = Session.builder.configs(connection_parameters).create()
```

**with...**

```python
import hextoolkit
hex_snowflake_conn = hextoolkit.get_data_connection('YOUR_DATA_CONNECTION_NAME')
session = hex_snowflake_conn.get_snowpark_session()
```

<!-- ------------------------ -->
## Streamlit Application

Duration: 10

### Running Streamlit App Locally

In a terminal window, browse to this folder and execute the following command to run the Streamlit application [Snowpark_Streamlit_Revenue_Prediction.py](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_Streamlit_Revenue_Prediction.py) locally on your machine.

```shell
streamlit run Snowpark_Streamlit_Revenue_Prediction.py
```

If all goes well, you should see a browser window open with the app loaded as shown below.

---

![Streamlit-App](assets/app.png)

---

### Running Streamlit App in Snowflake -- Streamlit-in-Snowflake (SiS)

If you have SiS enabled in your account, follow these steps to run the application in Snowsight instead of locally on your machine.

> aside negative
> IMPORTANT: SiS is in Private Preview as of Feburary 2023.***

  1) Click on **Streamlit Apps** on the left navigation menu
  2) Click on **+ Streamlit App** on the top right
  3) Enter **App name**
  4) Select **Warehouse** and **App locaton** (Database and Schema) where you'd like to create the Streamlit applicaton
  5) Click on **Create**
  6) At this point, you will be provided code for an example Streamlit application. Now open [Snowpark_Streamlit_Revenue_Prediction_SiS.py](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn/blob/main/Snowpark_Streamlit_Revenue_Prediction_SiS.py) and copy-paste the code into the example Streamlit application.
  7) Click on **Run** on the top right

If all goes well, you should see the following app in Snowsight as shown below.

---

![Streamlit-in-Snowflake](assets/app_sis.png)

---

### Save Data To Snowflake

In both applications, adjust the advertsing budget sliders to see the predicted ROI for those allocations. You can also click on **Save to Snowflake** button to save the current allocations and predcted ROI into BUDGET_ALLOCATIONS_AND_ROI Snowflake table.

### Differences between two Streamlit Apps

The main difference between running the Streamlit application locally and in Snowflake (SiS) is how you create and access the Session object.

When running locally, you'd create and access the new Session object it like so:

```python
# Function to create Snowflake Session to connect to Snowflake
def create_session():
    if "snowpark_session" not in st.session_state:
        session = Session.builder.configs(json.load(open("connection.json"))).create()
        st.session_state['snowpark_session'] = session
    else:
        session = st.session_state['snowpark_session']
    return session
```

When running in Snowflake (SiS), you'd access the current Session object like so:

```python
session = snowpark.session._get_active_session()
```

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 3

Congratulations! You've successfully performed data engineering tasks and trained a Linear Regression model to predict future ROI (Return On Investment) of variable advertising spend budgets across multiple channels including Search, Video, Social Media, and Email using Snowpark for Python and scikit-learn. And then you created a Streamlit application that uses that model to generate predictions on new budget allocations based on user input.

### What You Learned

- How to analyze data and perform data engineering tasks using Snowpark DataFrames and APIs
- How to use open-source Python libraries like scikit-learn from curated Snowflake Anaconda channel
- How to deploy ML model training code on Snowflake using Snowpark Python Stored Procedure
- How to create Scalar and Vectorized Snowpark Python User-Defined Functions (UDFs) for online and offline inference respectively
- How to create Snowflake Tasks to automate data pipelining and (re)training of the model
- How to create Streamlit web application that uses the Scalar UDF for inference

### Related Resources

- [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-ad-spend-roi-snowpark-python-streamlit-scikit-learn)
- [Advanced: Snowpark for Python Data Engineering Guide](https://quickstarts.snowflake.com/guide/data_engineering_pipelines_with_snowpark_python/index.html)
- [Advanced: Snowpark for Python Machine Learning Guide](https://quickstarts.snowflake.com/guide/getting_started_snowpark_machine_learning/index.html)
- [Snowpark for Python Demos](https://github.com/Snowflake-Labs/snowpark-python-demos/blob/main/README.md)
- [Snowpark for Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index.html)
- [Streamlit Docs](https://docs.streamlit.io/)

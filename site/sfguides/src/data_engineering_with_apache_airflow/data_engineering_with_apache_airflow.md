author: Adrian Lee
id: data_engineering_with_apache_airflow
summary: This is a sample Snowflake Guide
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, dbt, Airflow

# Data Engineering with Apache Airflow, Snowflake & dbt
<!-- ------------------------ -->
## Overview 
Duration: 5

![architecture](assets/data_engineering_with_apache_airflow_0_overall_architecture.png)

Numerous business are looking at modern data strategy built on platforms that could support agility, growth and operational efficiency. Snowflake is Data Cloud, a future proof solution that can simplify data pipelines for all your businesses so you can focus on your data and analytics instead of infrastructure management and maintenance.

Apache Airflow is an open-source workflow management platform that can be used to author and manage data pipelines. Airflow uses worklows made of directed acyclic graphs (DAGs) of tasks. 

[dbt](https://www.getdbt.com/) is a modern data engineering framework maintained by the [Fishtown Analytics](https://www.fishtownanalytics.com/) that is becoming very popular in modern data architectures, leveraging cloud data platforms like Snowflake. [dbt CLI](https://docs.getdbt.com/dbt-cli/cli-overview) is the open-source version of dbtCloud that is providing similar functionality, but as a SaaS.

In this virtual hands-on lab, you will follow a step-by-step guide to using Airflow with dbt to create data transformation job schedulers. 

Let’s get started. 

### What You’ll Learn 
- how to use an opensource tool like Airflow to create a data scheduler
- how do we write a DAG and upload it onto Airflow
- how to build scalable pipelines using dbt, Airflow and Snowflake

### What You’ll Need 
- [VSCode](https://code.visualstudio.com/download) Installed
- [Docker Desktop](https://www.docker.com/products/docker-desktop) Installed
- [dbt CLI](https://docs.getdbt.com/dbt-cli/installation) Installed 

<!-- ------------------------ -->
## Set up of environment
Duration: 2

First, let us create a folder by running the command below

```
mkdir dbt_airflow && cd "$_"
```

Next, we will get our docker-compose file of our airflow. To do so lets do a curl of the file onto our local laptop

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.1.2/docker-compose.yaml'
```

We would now need to create 2 additional files

1. <b>requirements.txt</b>: This is requirements file with the dbt requirements
2. <b>Dockerfile</b>: The Dockerfile will have a custom build of airflow with dbt installed
   
`requirements.txt`
```bash
dbt==0.19.0
```

`Dockerfile`
```bash
FROM apache/airflow:2.1.2
COPY requirements.txt .
RUN pip install -r requirements.txt
```

---
We would now need to create a `dbt` project as well as an `dags` folder. 

For the dbt project, do a ```dbt init dbt``` - this is where we will configure our dbt later in step 4.

For the dags folder, just create the folder by doing mkdir ```dags```

Your tree repository should look like this

![Folderstructure](assets/data_engineering_with_apache_airflow_1_tree_structure.png)

<!-- ------------------------ -->
## Setting up our DBT Project
Duration: 6

Now that we have gotten our repo up, it is time to configure and set up our DBT project. 

First, let's go to the Snowflake console and run the script below. What this does is create a dbt_user and a dbt_dev_role and after which we set up a database for dbt_user.

```sql
USE ROLE SECURITYADMIN;

CREATE OR REPLACE ROLE DBT_DEV_ROLE COMMENT='DBT_DEV_ROLE';
GRANT ROLE DBT_DEV_ROLE TO ROLE SYSADMIN;

CREATE OR REPLACE USER DBT_USER PASSWORD='<PASSWORD>'
	DEFAULT_ROLE=DBT_DEV_ROLE
	DEFAULT_WAREHOUSE=DBT_WH
	COMMENT='DBT User';
    
GRANT ROLE DBT_DEV_ROLE TO USER DBT_USER;

-- Grant privileges to role
USE ROLE ACCOUNTADMIN;

GRANT CREATE DATABASE ON ACCOUNT TO ROLE DBT_DEV_ROLE;

/*---------------------------------------------------------------------------
Next we will create a virtual warehouse that will be used
---------------------------------------------------------------------------*/
USE ROLE SYSADMIN;

--Create Warehouse for DBT work
CREATE OR REPLACE WAREHOUSE DBT_DEV_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 120
  AUTO_RESUME = true
  INITIALLY_SUSPENDED = TRUE;

GRANT ALL ON WAREHOUSE DBT_DEV_WH TO ROLE DBT_DEV_ROLE;

```

Let's login with the ```dbt_user``` and create the database ```DEMO_DBT``` by running the command

```sql

CREATE OR REPLACE DATABASE DEMO_DBT

```
![airflow](assets/data_engineering_with_apache_airflow_2_snowflake_console.png)


Now, let's go back to our project ```dbt_airflow``` > ```dbt```that we set up previously in step 1.

We will set up a few configurations for the respective files below

profiles.yml
```yml
default:
  target: dev
  outputs:
    dev:
      type: snowflake
      ######## Please replace with your Snowflake account name
      account: <account_name>.<regions>

      user: dbt_user
      ######## Please replace with your Snowflake dbt user password
      password: <Password>

      role: dbt_dev_role
      database: demo_dbt
      warehouse: dbt_dev_wh
      schema: public
      threads: 200
```
packages.yml
```yml
packages:
  - package: fishtown-analytics/dbt_utils
    version: 0.6.4
```

dbt_project.yml
```yml
models:
  my_new_project:
      # Applies to all files under models/example/
      transform:
          schema: transform
          materialized: view
      analysis:
          schema: analysis
          materialized: view
```

Next, we will install the ```fishtown-analytics/dbt_utils``` that we had placed inside ```packages.yml```. This can be done by running the command ```dbt debs``` from the ```dbt``` folder. 

We will now create a file called ```call_me_anything_you_want.sql``` under the ```macros``` folder and input the below sql 

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}


{% macro set_query_tag() -%}
  {% set new_query_tag = model.name %} {# always use model name #}
  {% if new_query_tag %}
    {% set original_query_tag = get_current_query_tag() %}
    {{ log("Setting query_tag to '" ~ new_query_tag ~ "'. Will reset to '" ~ original_query_tag ~ "' after materialization.") }}
    {% do run_query("alter session set query_tag = '{}'".format(new_query_tag)) %}
    {{ return(original_query_tag)}}
  {% endif %}
  {{ return(none)}}
{% endmacro %}
```

If everything is done correctly, your folder should look like below. The annotated boxes are what we just went through above. 

![airflow](assets/data_engineering_with_apache_airflow_3_dbt_structure.png)

We are done configuring DBT. Let us proceed on crafting our csv files and our dags in the next section.

<!-- ------------------------ -->
## Creating our CSV data files in DBT
Duration: 10

In this section, we will be prepping our sample csv data files alongside the associated sql models. 

To start, let us first create 3 excel files under the folder ```data``` inside the dbt folder.

bookings_1.csv

```csv
id,booking_reference,hotel,booking_date,cost
1,232323231,Pan Pacific,2021-03-19,100
1,232323232,Fullerton,2021-03-20,200
1,232323233,Fullerton,2021-04-20,300
1,232323234,Jackson Square,2021-03-21,400
1,232323235,Mayflower,2021-06-20,500
1,232323236,Suncity,2021-03-19,600
1,232323237,Fullerton,2021-08-20,700
```

bookings_2.csv

```csv
id,booking_reference,hotel,booking_date,cost
2,332323231,Fullerton,2021-03-19,100
2,332323232,Jackson Square,2021-03-20,300
2,332323233,Suncity,2021-03-20,300
2,332323234,Jackson Square,2021-03-21,300
2,332323235,Fullerton,2021-06-20,300
2,332323236,Suncity,2021-03-19,300
2,332323237,Berkly,2021-05-20,200
```

customers.csv
```csv
id,first_name,last_name,birthdate,membership_no
1,jim,jone,1989-03-19,12334
2,adrian,lee,1990-03-10,12323
```

Our folder structure should be like as below

![airflow](assets/data_engineering_with_apache_airflow_4_csv_files.png)

<!-- ------------------------ -->
## Creating our DBT models in models folder
Duration: 2

Create 2 folders ```analysis``` and ```transform``` in the models folder. 

Inside the ```transform``` folder, we will have 3 SQL files

1) ```combined_bookings.sql```: This will combine the 2 bookings CSV files we had above and create the  ```COMBINED_BOOKINGS``` view in the ```TRANSFORM``` schema. 

combined_bookings.sql
```sql
{{ dbt_utils.union_relations(
    relations=[ref('bookings_1'), ref('bookings_2')]
) }}
```

2) ```customer.sql```: This will create a ```CUSTOMER``` view in the ```TRANSFORM``` schema.

customer.sql
```sql
SELECT ID 
    , FIRST_NAME
    , LAST_NAME
    , birthdate
FROM {{ ref('customers') }}
```

3) ```prepped_data.sql```: This will create a ```PREPPED_DATA``` view in the ```TRANSFORM``` schema in which it will perform an inner join on the ```CUSTOMER``` and ```COMBINED_BOOKINGS``` views from the steps above. 

prepped_data.sql
```sql
SELECT A.ID 
    , FIRST_NAME
    , LAST_NAME
    , birthdate
    , BOOKING_REFERENCE
    , HOTEL
    , BOOKING_DATE
    , COST
FROM {{ref('customer')}}  A
JOIN {{ref('combined_bookings')}} B
on A.ID = B.ID
```
Now let's move on to the ```analysis``` folder. Change to the ```analysis``` folder and create these 2 SQL files

1) ```hotel_count_by_day.sql```: This will create a hotel_count_by_day view in the ```ANALYSIS``` schema in which we will count the number of hotel bookings by day. 

```sql
SELECT
  BOOKING_DATE,
  HOTEL,
  COUNT(ID) as count_bookings
FROM {{ ref('prepped_data') }}
GROUP BY
  BOOKING_DATE,
  HOTEL
```

2) ```thirty_day_avg_cost.sql```: This will create a thirty_day_avg_cost view in the ```ANALYSIS``` schema in which we will do a average cost of booking for the last 30 days. 

```sql
SELECT
  BOOKING_DATE,
  HOTEL,
  COST,
  AVG(COST) OVER (
    ORDER BY BOOKING_DATE ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as "30_DAY_AVG_COST",
  COST -   AVG(COST) OVER (
    ORDER BY BOOKING_DATE ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as "DIFF_BTW_ACTUAL_AVG"
FROM {{ ref('prepped_data') }}
```

Your file structure should be as below. We have already finished our DBT models and can proceed onto working on Airflow. 

![airflow](assets/data_engineering_with_apache_airflow_5_dbt_models.png)

<!-- ------------------------ -->
## Preparing our Airflow DAGs
Duration: 5

In our ```dags``` folder, create 2 files: ```init.py``` and ```transform_and_analysis.py```. The ```init.py``` will initialise and see the CSV data. The ```transform_and_analysis.py``` will perform the transformation and analysis. 

With Airflow, we can then schedule the ```transform_and_analysis``` DAG on a daily basis. However, in this example, we will be triggering the DAG manually.

init.py
```python
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2020,8,1),
    'retries': 0
}


with DAG('1_init_once_seed_data', default_args=default_args, schedule_interval='@once') as dag:
    task_1 = BashOperator(
        task_id='load_seed_data_once',
        bash_command='cd /dbt && dbt seed --profiles-dir .',
        dag=dag
    )

task_1  
```

transform_and_analysis.py
```python
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2020,8,1),
    'retries': 0
}

with DAG('2_daily_transformation_analysis', default_args=default_args, schedule_interval='@once') as dag:
    task_1 = BashOperator(
        task_id='daily_transform',
        bash_command='cd /dbt && dbt run --models transform --profiles-dir .',
        dag=dag
    )

    task_2 = BashOperator(
        task_id='daily_analysis',
        bash_command='cd /dbt && dbt run --models analysis --profiles-dir .',
        dag=dag
    )

    task_1 >> task_2 # Define dependencies
```



<!-- ------------------------ -->
## Adjusting our docker-compose file for Airflow
Duration: 5

We will be now adjusting our docker-compose file. There are 2 parts which we will be adjusting

- We will be commenting out the `image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.1.2}` and include in the `build: .` in the line as below

```bash
version: '3'
x-airflow-common:
  &airflow-common
  build: . # add this in and comment the line below out
  #image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.1.2}
  environment:
```
- We will be add in our 2 folders as volumes. The `dags` is the folder where the Airflow DAGs are placed for Airflow to pick up and analyse. The `dbt` is the folder in which we configured our DBT models and our CSV files. 

```bash
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - ./dbt:/dbt # add this in
    - ./dags:/dags # add this in

```
Let's run our ```docker-compose up``` and go to ```http://localhost:8080/```. The default username is ```airflow``` and password is ```airflow```

![airflow](assets/data_engineering_with_apache_airflow_2_airflow_url.png)


<!-- ------------------------ -->
## Activating and running our DAGs

We will now activate our DAGs. Click on the blue buttons for ```1_init_once_seed_data``` and ```2_daily_transformation_analysis```

![airflow](assets/data_engineering_with_apache_airflow_6_runnig_our_dags.png)

Now, lets run our ```1_init_once_seed_data```  to seed the data

![airflow](assets/data_engineering_with_apache_airflow_7_dag_init_successful.png)

If all goes well when we go back to our Snowflake instance, we should see tree tables that have been successfully created in the ```PUBLIC``` schema. 

![airflow](assets/data_engineering_with_apache_airflow_8_snowflake_successful.png)

We will now run our second DAG ```2_daily_transformation_analysis``` which will run our ```transform``` and ```analysis``` models

![airflow](assets/data_engineering_with_apache_airflow_9_dag_transform_analysis_successful.png)

Our ```Transform``` and ```Analysis``` views have been created successfully!

![airflow](assets/data_engineering_with_apache_airflow_10_snowflake_successful_transform_analysis.png)

<!-- ------------------------ -->
## Conclusion
Duration: 1

Congratulation! You have created your first Apache Airflow with dbt and Snowflake! We encourage you to continue with your free trial by loading your own sample or production data and by using some of the more advanced capabilities of Airflow and Snowflake not covered in this lab. 

### Additional Resources:
- Read the [Definitive Guide to Maximizing Your Free Trial](https://www.snowflake.com/test-driving-snowflake-the-definitive-guide-to-maximizing-your-free-trial/) document
- Attend a [Snowflake virtual or in-person event](https://www.snowflake.com/about/events/) to learn more about our capabilities and customers
- [Join the Snowflake community](https://community.snowflake.com/s/topic/0TO0Z000000wmFQWAY/getting-started-with-snowflake)
- [Sign up for Snowflake University](https://community.snowflake.com/s/article/Getting-Access-to-Snowflake-University)
- [Contact our Sales Team](https://www.snowflake.com/free-trial-contact-sales/) to learn more

### What we've covered:
- How to set up Airflow, dbt & Snowflake
- How to create a DAG and run dbt from our dag
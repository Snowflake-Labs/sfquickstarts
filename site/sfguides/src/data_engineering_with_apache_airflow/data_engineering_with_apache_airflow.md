author: Adrian Lee, George Yates
id: data_engineering_with_apache_airflow
summary: This is a sample Snowflake Guide
categories: data-engineering,architecture-patterns,partner-integrations
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, dbt, Airflow

# Data Engineering with Apache Airflow, Snowflake, dbt & Cosmos
<!-- ------------------------ -->
## Overview 
Duration: 5

![architecture](assets/data_engineering_with_apache_airflow_0_overall_architecture.png)

Numerous business are looking at modern data strategy built on platforms that could support agility, growth and operational efficiency. Snowflake is Data Cloud, a future proof solution that can simplify data pipelines for all your businesses so you can focus on your data and analytics instead of infrastructure management and maintenance.

Apache Airflow is an open-source workflow management platform that can be used to author and manage data pipelines. Airflow uses workflows made of directed acyclic graphs (DAGs) of tasks. The [Astro CLI](https://docs.astronomer.io/astro/cli/overview) is a command line interface for Airflow developed by Astronomer. It's the easiest way to get started with running Apache Airflow locally

[dbt](https://www.getdbt.com/) is a modern data engineering framework maintained by [dbt Labs](https://www.getdbt.com/) that is becoming very popular in modern data architectures, leveraging cloud data platforms like Snowflake. [dbt CLI](https://docs.getdbt.com/dbt-cli/cli-overview) is the command line interface for running dbt projects. The CLI is free to use and open source.

[cosmos](https://astronomer.github.io/astronomer-cosmos/index.html) is an Open-Source project that enables you to run your dbt Core projects as Apache Airflow DAGs and Task Groups with a few lines of code.

In this virtual hands-on lab, you will follow a step-by-step guide to using Airflow with dbt to create data transformation job schedulers. 

Let’s get started. 
### Prerequisites
This guide assumes you have a basic working knowledge of Python and dbt

### What You’ll Learn 
- how to use an opensource tool like Airflow to create a data scheduler
- how do we write a DAG and upload it onto Airflow
- how to build scalable pipelines using dbt, Airflow and Snowflake

### What You’ll Need 
You will need the following things before beginning:

1. Snowflake
  1. **A Snowflake Account.**
  1. **A Snowflake User created with appropriate permissions.** This user will need permission to create objects in the DEMO_DB database.
1. GitHub
  1. **A GitHub Account.** If you don’t already have a GitHub account you can create one for free. Visit the [Join GitHub](https://github.com/join) page to get started.
1. Integrated Development Environment (IDE)
  1. **Your favorite IDE with Git integration.** If you don’t already have a favorite IDE that integrates with Git I would recommend the great, free, open-source [Visual Studio Code](https://code.visualstudio.com/).
1. Docker Desktop
  1. **Docker Desktop on your laptop.**  We will be running Airflow as a container. Please install Docker Desktop on your desired OS by following the [Docker setup instructions](https://docs.docker.com/desktop/).
1. Astro CLI
  1. **The Astro CLI Installed.** We will be using the Astro CLI to create our Airflow environments. Please install the Astro CLI on your desired OS by following the [Astro CLI setup instructions](https://docs.astronomer.io/astro/cli/install-cli)

### What You’ll Build 
- A simple working Airflow pipeline with dbt and Snowflake 

<!-- ------------------------ -->
## Set up of environment
Duration: 2

First, let us create a folder by running the command below

```
mkdir dbt_airflow && cd dbt_airflow
```

Next, we will use the Astro CLI to create a new Astro project by running the following command. An Astro project contains the set of files necessary to run Airflow, including dedicated folders for your DAG files, plugins, and dependencies.

```bash
astro dev init
```

Now, navigate into the DAG's folder that the Astro CLI created, and create a new folder called dbt by running the following command. 

```bash
mkdir dbt && cd dbt
```

Next, run the following command to install dbt and create all the necessary folders for your project. It will prompt you for a name for your project, enter 'cosmosproject'. 

```bash
dbt init
```


Your tree repository should look like this

![Folderstructure](assets/data_engineering_with_apache_airflow_1_tree_structure.png)

<!-- ------------------------ -->
## Setting up our dbt Project
Duration: 6

Now that we have gotten our repo up, it is time to configure and set up our dbt project. 

Before we begin, let's take some time to understand what we are going to do for our dbt project.

As can be seen in the diagram below, we have 3 csv files ```bookings_1```, ```bookings_2``` and ```customers ```. We are going to seed these csv files into Snowflake as tables. This will be detailed later.

Following this, we are going to use dbt to merge ```bookings_1``` and ```bookings_2``` tables into ```combined_bookings```. Then, we are going to join the ```combined_bookings``` and ```customer``` table on customer_id to form the ```prepped_data``` table. 

Finally, we are going to perform our analysis and transformation on the ```prepped_data``` by creating 2 views.  

1) ```hotel_count_by_day.sql```: This will create a hotel_count_by_day view in the ANALYSIS schema in which we will count the number of hotel bookings by day.

2) ```thirty_day_avg_cost.sql```: This will create a thirty_day_avg_cost view in the ANALYSIS schema in which we will do a average cost of booking for the last 30 days.

![dbt_structure](assets/data_engineering_with_apache_airflow_0_dbt_flow.png)

First, let's go to the Snowflake console and run the script below. What this does is create a dbt_user and a dbt_dev_role and after which we set up a database for dbt_user.

```sql
USE ROLE SECURITYADMIN;

CREATE OR REPLACE ROLE dbt_DEV_ROLE COMMENT='dbt_DEV_ROLE';
GRANT ROLE dbt_DEV_ROLE TO ROLE SYSADMIN;

CREATE OR REPLACE USER dbt_USER PASSWORD='<PASSWORD>'
	DEFAULT_ROLE=dbt_DEV_ROLE
	DEFAULT_WAREHOUSE=dbt_WH
	COMMENT='dbt User';
    
GRANT ROLE dbt_DEV_ROLE TO USER dbt_USER;

-- Grant privileges to role
USE ROLE ACCOUNTADMIN;

GRANT CREATE DATABASE ON ACCOUNT TO ROLE dbt_DEV_ROLE;

/*---------------------------------------------------------------------------
Next we will create a virtual warehouse that will be used
---------------------------------------------------------------------------*/
USE ROLE SYSADMIN;

--Create Warehouse for dbt work
CREATE OR REPLACE WAREHOUSE dbt_DEV_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 120
  AUTO_RESUME = true
  INITIALLY_SUSPENDED = TRUE;

GRANT ALL ON WAREHOUSE dbt_DEV_WH TO ROLE dbt_DEV_ROLE;

```

Let's login with the ```dbt_user``` and create the database ```DEMO_dbt``` by running the command

```sql

CREATE OR REPLACE DATABASE DEMO_dbt

```
![airflow](assets/data_engineering_with_apache_airflow_2_snowflake_console.png)

Then, in the new ```Demo_dbt``` database, copy and paste the following sql statements to create our ```bookings_1```, ```bookings_2``` and ```customers ``` tables within Snowflake

```sql

CREATE TABLE bookings_1 (
    id INTEGER,
    booking_reference INTEGER,
    hotel STRING,
    booking_date DATE,
    cost INTEGER
);
CREATE TABLE bookings_2 (
    id INTEGER,
    booking_reference INTEGER,
    hotel STRING,
    booking_date DATE,
    cost INTEGER
);
CREATE TABLE customers (
    id INTEGER,
    first_name STRING,
    last_name STRING,
    birthdate DATE,
    membership_no INTEGER
);

```
Then, run the following statements to insert data into these tables. 

```sql
INSERT INTO bookings_1
  VALUES
  (1, 232323231, 'Pan Pacific', TO_DATE('2021-03-19'), 100),
  (1, 232323232, 'Fullerton', TO_DATE('2021-03-20'), 200),
  (1, 232323233, 'Fullerton', TO_DATE('2021-04-20'), 300),
  (1, 232323234, 'Jackson Square', TO_DATE('2021-03-21'), 400),
  (1, 232323235, 'Mayflower', TO_DATE('2021-06-20'), 500),
  (1, 232323236, 'Suncity', TO_DATE('2021-03-19'), 600),
  (1, 232323237, 'Fullerton', TO_DATE('2021-08-20'), 700);

```
```sql
INSERT INTO bookings_2
  VALUES
  (2, 332323231, 'Fullerton', TO_DATE('2021-03-19'), 100),
  (2, 332323232, 'Jackson Square', TO_DATE('2021-03-20'), 300),
  (2, 332323233, 'Suncity', TO_DATE('2021-03-20'), 300),
  (2, 332323234, 'Jackson Square', TO_DATE('2021-03-21'), 300),
  (2, 332323235, 'Fullerton', TO_DATE('2021-06-20'), 300),
  (2, 332323236, 'Suncity', TO_DATE('2021-03-19'), 300),
  (2, 332323237, 'Berkly', TO_DATE('2021-05-20'), 200);

```
```sql
INSERT INTO customers
  VALUES
  (1, 'george', 'yates', TO_DATE('1989-03-19'), 12334),
  (2, 'rishi','kar', TO_DATE('1990-03-10'), 12323);

```


Now, let's go back to our project ```cosmosproject``` > ```dbt```that we set up previously.

We will set up a couple configurations for the respective files below. Please note for the ```dbt_project.yml``` you just need to replace the models section

packages.yml (Create in ```cosmosproject``` folder if not already present) 
```yml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
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

Next, we will install the ```dbt-labs/dbt_utils``` that we had placed inside ```packages.yml```. This can be done by running the command ```dbt deps``` from the ```cosmosproject``` folder. 

We will now create a file called ```custom_demo_macros.sql``` under the ```macros``` folder and input the below sql 

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

We are done configuring dbt. Let us proceed on crafting our csv files and our dags in the next section.



HOLD FOR SCREENSHOT OF FOLDER STRUCTURE 



<!-- ------------------------ -->
## Creating our dbt models in models folder
Duration: 2

Create 2 folders ```analysis``` and ```transform``` in the models folder. Please follow the sections below for analysis and transform respectively. 

### dbt models for transform folder

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

### dbt models for analysis folder

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

Your file structure should be as below. We have already finished our dbt models and can proceed onto working on Airflow. 

![airflow](assets/data_engineering_with_apache_airflow_5_dbt_models.png)

<!-- ------------------------ -->
## Preparing our Airflow Environment
Duration: 5

Now going back to your Airflow directory, open up the requirements.txt file that the Astro CLI created. Copy and paste the following text block to install the [Cosmos](https://astronomer.github.io/astronomer-cosmos/index.html) and Snowflake libraries for Airflow. Cosmos will be used to turn each dbt model into a task/task group complete with retries, alerting, etc. 
```
astronomer-cosmos
apache-airflow-providers-snowflake
```

Next, open up the Dockerfile in your Airflow folder and copy and paste the following code block to create a virtual environment for dbt along with the adapter to connect to Snowflake. It’s recommended to use a virtual environment because dbt and Airflow can have conflicting dependencies.

```
RUN python -m venv dbt_venv && source dbt_venv/bin/activate && pip install --no-cache-dir dbt-snowflake && deactivate
```

<!-- ------------------------ -->
## Building Our dbt DAG
Duration: 5

Now that our Airflow environment is set up, lets create our DAG! Instead of using the conventional DAG definition methods, we'll be using Cosmos' dbtDAG class to create a DAG based on our dbt models. This allows us to turn our dbt projects into Apache Airflow DAGs and Task Groups with a few lines of code. To do so, create a new file in the ```dags``` folder called ```my_cosmos_dag.py``` and copy and paste the following code block into the file. 

```python
from datetime import datetime
import os
from cosmos import DbtDag, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import PostgresUserPasswordProfileMapping
from cosmos.profiles import SnowflakeUserPasswordProfileMapping


profile_config = ProfileConfig(profile_name="default",
                               target_name="dev",
                               profile_mapping=SnowflakeUserPasswordProfileMapping(conn_id="snowflake_conn", 
                                                    profile_args={
                                                        "database": "demo_dbt",
                                                        "schema": "public"
                                                        },
                                                    ))


dbt_snowflake_dag = DbtDag(project_config=ProjectConfig("/usr/local/airflow/dags/dbt/cosmosproject",),
                    operator_args={"install_deps": True},
                    profile_config=profile_config,
                    execution_config=ExecutionConfig(dbt_executable_path=f"{os.environ['AIRFLOW_HOME']}/dbt_venv/bin/dbt",),
                    schedule_interval="@daily",
                    start_date=datetime(2023, 9, 10),
                    catchup=False,
                    dag_id="dbt_snowflake_dag",)

```
First, we import the various Cosmos libraries

• DbtDag: This is a class that allows you to create an Apache Airflow Directed Acyclic Graph (DAG) for a dbt (Data Build Tool) project. The DAG will execute the dbt project according to the specified configuration.

• ProjectConfig: This class is used to specify the configuration for the dbt project that the DbtDag will execute by pointing it to the path tfor your dbt project.

• ProfileConfig: This class is used to specify the configuration for the database profile that dbt will use when executing the project. This includes the profile name, target name, and any necessary mapping to Airflow connections.

• ExecutionConfig: This class is used to specify any additional configuration for executing the dbt project. We'll be pointing it to the virtual environment we created at `{os.environ['AIRFLOW_HOME']}/dbt_venv/bin/dbt` in our `Dockerfile` to execute in. 

• PostgresUserPasswordProfileMapping and SnowflakeUserPasswordProfileMapping: These classes are used to map Airflow connections to dbt profiles for PostgreSQL and Snowflake databases, respectively. This allows you to manage your database credentials in Airflow and use them in dbt.

After the imports, a ProfileConfig object is created, which is used to define the configuration for the Snowflake connection. The SnowflakeUserPasswordProfileMapping class is used to map the Snowflake connection in Airflow to a dbt profile. The DbtDag object is then created. This object represents an Airflow DAG that will execute a dbt project. It takes several parameters: 

`project_config` specifies the path to the dbt project we created at `/usr/local/airflow/dags/dbt/cosmosproject`
`operator_args` is used to pass arguments to the dbt operator. Here, it's specifying that dependencies should be installed.
`profile_config` is the profile configuration defined earlier, which will be used to execute the dbt models in Snowflake.
`execution_config` specifies the path to our virtual environment to executue our dbt code in. 
`schedule_interval`, `start_date`, `catchup`, and `dag_id` are standard Airflow DAG parameters. You can use any of the standard Airflow DAG parameters in a dbtDAG as well. 


<!-- ------------------------ -->
## Running our docker-compose file for Airflow
Duration: 5

Let's run our ```docker-compose up``` and go to [http://localhost:8080/](http://localhost:8080/). The default username is ```airflow``` and password is ```airflow```

![airflow](assets/data_engineering_with_apache_airflow_2_airflow_url.png)

We are now going to create 2 variables. Go to ```admin > Variables``` and click on the ```+``` icon. 

![airflow](assets/data_engineering_with_apache_airflow_5_airflow_variables.png)

Let us first create key of ```dbt_user``` and value ```dbt_user```. 

![airflow](assets/data_engineering_with_apache_airflow_5_airflow_username.png)

Now let us create our second key of ```dbt_password``` and value ```<ADD IN YOUR PASSWORD>```

![airflow](assets/data_engineering_with_apache_airflow_5_airflow_password.png)

<!-- ------------------------ -->
## Activating and running our DAGs

We will now activate our DAGs. Click on the blue buttons for ```1_init_once_seed_data``` and ```2_daily_transformation_analysis```

![airflow](assets/data_engineering_with_apache_airflow_6_runnig_our_dags.png)

### Running our 1_init_once_seed_data
Now, lets run our ```1_init_once_seed_data```  to seed the data. To run click the play icon under the ```Actions``` on the right of the DAG.

![airflow](assets/data_engineering_with_apache_airflow_7_dag_init_successful.png)

### Viewing Seed data in tables created under public schema
If all goes well when we go back to our Snowflake instance, we should see tree tables that have been successfully created in the ```PUBLIC``` schema. 

![airflow](assets/data_engineering_with_apache_airflow_8_snowflake_successful_seed.png)

### Running our 2_daily_transformation_analysis
We will now run our second DAG ```2_daily_transformation_analysis``` which will run our ```transform``` and ```analysis``` models

![airflow](assets/data_engineering_with_apache_airflow_9_dag_transform_analysis_successful.png)

Our ```Transform``` and ```Analysis``` views have been created successfully!

![airflow](assets/data_engineering_with_apache_airflow_10_snowflake_successful_transform_analysis.png)

<!-- ------------------------ -->
## Conclusion
Duration: 1

Congratulations! You have created your first Apache Airflow with dbt and Snowflake! We encourage you to continue with your free trial by loading your own sample or production data and by using some of the more advanced capabilities of Airflow and Snowflake not covered in this lab. 

### Additional Resources:
- Join our [dbt community Slack](https://www.getdbt.com/community/) which contains more than 18,000 data practitioners today. We have a dedicated slack channel #db-snowflake to Snowflake related content.
- Quick tutorial on how to write a simple [Airflow DAG](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)

### What we've covered:
- How to set up Airflow, dbt & Snowflake
- How to create a DAG and run dbt from our dag

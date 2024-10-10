author: Joviane Bellegarde
id: cdc_data_from_postgres_to_snowflake
summary: CDC data from PostgreSQL to Snowflake
categories: Getting-Started, Connectors, Dynamic Tables, PostgreSQL
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Connectors, Dynamic Tables

# Real-Time Financial Insights with Change Data Capture (CDC) with PostgreSQL, Dynamic Tables, and Streamlit-in-Snowflake
<!-- ------------------------ -->

## Overview
Duration: 10

In this Quickstart, we will investigate how a financial company a builds a BI dashboard using customer transactional data housed on a PostgreSQL database. The data is brought into Snowflake via the Snowflake Connector for PostgreSQL. The main idea is gain insights in how to increase customer engagement using Streamlit-in-Snowflake.

### What You Will Build
- Visualize customer data and gain insights ingesting data from PostgreSQL DB to Snowflake using the Snowflake Connector for PostgreSQL Native App, [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about) and [Streamlit-in-Snowflake (SiS)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

### What You Will Learn
- How to connect PostgreSQL data to Snowflake using the [Snowflake Connector for PostgreSQL](https://other-docs.snowflake.com/en/connectors/postgres6/about)
- Visualize data using [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about) and display visualizations within [Streamlit-in-Snowflake (SiS)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

### Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop/) installed on your local machine
- A tool available for connecting to the PostgreSQL database
  - This can be a database-specific tool or a general-purpose tool such as Visual Studio Code or PyCharm
- Familiarity with basic Python and SQL
- Familiarity with data science notebooks
- Go to the [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) sign-up page and register for a free account. After registration, you will receive an email containing a link that will take you to Snowflake, where you can sign in.

------------------------
## Creating PostgreSQL Source Database
Duration: 5

### Overview
In this section, we will set up a PostgreSQL database and create tables to simulate a financial company's customer transactional data.

#### Starting the Database Instance
To initiate the PostgreSQL database using Docker, you'll need to create a file called `docker-compose.yaml`. This file will contain the configuration for the PostgreSQL database. Open the IDE of your choice to copy and past this file by copy pasting the following:
```
version: '1'
services:
  postgres:
    image: "postgres:11"
    container_name: "postgres11"
    environment:
      POSTGRES_DB: 'financial_data_hub'
      POSTGRES_USER: 'postgres'
      POSTGRES_PASSWORD: 'postgres'
    ports:
      - "5432:5432"
    command:
      - "postgres"
      - "-c"
      - "wal_level=logical"
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
```

Next, open a terminal and navigate to the directory where the `docker-compose.yaml` file is located. Run the following command to start the PostgreSQL database:

```
docker-compose up -d
```
After running this command, you should see one Docker container actively running the source database.

#### Connecting to the Database
To connect to the pre-configured databases using PyCharm’s or Visual Studio Code database connections, perform the following steps with the provided credentials:
1. Open your tool of choice for connecting to the PostgreSQL database
   - For VSCode, you can use the [PostgreSQL extension](https://marketplace.visualstudio.com/items?itemName=cweijan.vscode-postgresql-client2)
   - For PyCharm, you can use the [Database Tools and SQL plugin](https://www.jetbrains.com/help/pycharm/database-tool-window.html)
2. Click the `+` sign or similar to add data source
3. Use these connection parameters:
    - **User:** `postgres`
    - **Password:** `postgres`
    - **URL:** `jdbc:postgresql://localhost:5432`
4. Test the connection and save

#### Loading Data
1. First create the schema and tables to in the financial_data_hub database that was created in the PostgreSQL database. You can use the following SQL script to create the schema and tables:

```
CREATE SCHEMA raw_cdc;
SET search_path TO raw_cdc;

drop table if exists financial_data_hub.raw_cdc.customers;
drop table if exists financial_data_hub.raw_cdc.merchants;
drop table if exists financial_data_hub.raw_cdc.products;
drop table if exists financial_data_hub.raw_cdc.transactions;

CREATE TABLE financial_data_hub.raw_cdc.customers (
    customer_id integer PRIMARY KEY,
    firstname varchar,
    lastname varchar,
    age integer,
    email varchar,
    phone_number varchar
);

create table financial_data_hub.raw_cdc.merchants (
    merchant_id integer PRIMARY KEY,
	merchant_name varchar,
	merchant_category varchar
);

create table financial_data_hub.raw_cdc.products (
    product_id integer PRIMARY KEY,
    product_name varchar,
    product_category varchar,
    price double precision
);

create table financial_data_hub.raw_cdc.transactions (
    transaction_id varchar PRIMARY KEY,
	customer_id integer,
	product_id integer,
	merchant_id integer,
	transaction_date date,
	transaction_time varchar,
	quantity integer,
	total_price double precision,
    transaction_card varchar,
    transaction_category varchar
);
```

2. Download and save these csv files in a directory on your local machine: 
    - [customers.csv](https://github.com/Snowflake-Labs/sfguide-intro-to-cdc-using-snowflake-postgres-connector-dynamic-tables/blob/main/scripts/postgres_csv/customers.csv)
    - [merchants.csv](https://github.com/Snowflake-Labs/sfguide-intro-to-cdc-using-snowflake-postgres-connector-dynamic-tables/blob/main/scripts/postgres_csv/merchants.csv)
    - [products.csv](https://github.com/Snowflake-Labs/sfguide-intro-to-cdc-using-snowflake-postgres-connector-dynamic-tables/blob/main/scripts/postgres_csv/products.csv)
    - [transactions.csv](https://github.com/Snowflake-Labs/sfguide-intro-to-cdc-using-snowflake-postgres-connector-dynamic-tables/blob/main/scripts/postgres_csv/transactions.csv)

3. We'll need to move the files from the local computer to a folder located in the PostgreSQL environment before loading the data into the PostgreSQL database.

4. First, navigate to your terminal to get the Docker container ID with this command:
```
docker ps
```
5. Next, to copy the csv files to the container with these commands, run these commands in your terminal, replacing `<container_id>` with the actual container ID from the previous command: 
```
docker cp customers.csv <container_id>:/tmp/customers.csv
docker cp merchants.csv <container_id>:/tmp/merchants.csv
docker cp products.csv <container_id>:/tmp/products.csv
docker cp transactions.csv <container_id>:/tmp/transactions.csv
```

6. Navigate back to your PostgreSQL console and run these SQL commands to load the files from the container to the PostgreSQL database:
```
copy financial_data_hub.raw_cdc.customers from '/tmp/customers.csv' DELIMITER ',' CSV HEADER;
copy financial_data_hub.raw_cdc.merchants from '/tmp/merchants.csv' DELIMITER ',' CSV HEADER;
copy financial_data_hub.raw_cdc.products from '/tmp/products.csv' DELIMITER ',' CSV HEADER;
copy financial_data_hub.raw_cdc.transactions from '/tmp/transactions.csv' DELIMITER ',' CSV HEADER;
```

7. Next, make sure to run the `CREATE PUBLICATION` command to enable the logical replication for the tables in the `raw_cdc` schema. This will allow the Snowflake Connector for PostgreSQL to capture the changes made to the tables in the PostgreSQL database.:
```
CREATE PUBLICATION agent_postgres_publication FOR ALL TABLES;
```

8. Lastly, check that the tables have been loaded correctly by running the following SQL commands:
```
select * from financial_data_hub.raw_cdc.customers;
select * from financial_data_hub.raw_cdc.merchants;
select * from financial_data_hub.raw_cdc.products;
select * from financial_data_hub.raw_cdc.transactions;
```

<!-- ------------------------ -->

## Install and Configure the Snowflake Connector for PostgreSQL Native App

Duration: 5


### Overview
During this step, you will install and configure the Snowflake Connector for PostgreSQL Native App to capture changes made to the PostgreSQL database tables.

#### Install the Snowflake Connector for PostgreSQL Native App
Navigate to [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) and: 
1. Navigate to the **Data Products** then to the **Marketplace** section
2. Search for the **Snowflake Connector for PostgreSQL** Native App and install the application
3. You should find your installed Native App under **Data Products**, **Apps** section

#### Configure the Snowflake Connector for PostgreSQL Native App
1. On your Snowflake Account, navigate to the **Data Products**, **Apps** section
2. Open the application and do the following
    - Select **Mark all as done** as we will create our source databases from scratch. No additional network configuration is required as its configured later in this tutorial. 
    - Click **Start configuration**
    - On the **Configure Connector** screen, select **Configure**
    - On the **Verify Agent Connection** screen select **Generate file** to download the Agent Configuration file. The downloaded file name should resemble **snowflake.json**. Save this file for use during the Agent configuration section.


[//]: # (### Import Snowflake Notebooks)

[//]: # ()
[//]: # (You will use [Snowsight]&#40;https://docs.snowflake.com/en/user-guide/ui-snowsight.html#&#41;, the Snowflake web interface, to create the Snowflake Notebooks by importing the Notebooks.)

[//]: # ()
[//]: # (1. Navigate to Notebooks in [Snowsight]&#40;https://docs.snowflake.com/en/user-guide/ui-snowsight.html#&#41; by clicking on `Projects` `->` `Notebook`)

[//]: # ()
[//]: # ()
[//]: # (2. Switch Role to `CHURN_DATA_SCIENTIST`)

[//]: # ()
[//]: # ()
[//]: # (3. Download the [1_telco_churn_ingest_data.ipynb]&#40;https://github.com/Snowflake-Labs/sfguide-data-analysis-churn-prediction-in-snowflake-notebooks/blob/main/notebooks/1_telco_churn_ingest_data.ipynb&#41; and [2_telco_churn_ml_feature_engineering.ipynb]&#40;https://github.com/Snowflake-Labs/sfguide-data-analysis-churn-prediction-in-snowflake-notebooks/blob/main/notebooks/2_telco_churn_ml_feature_engineering.ipynb&#41; Notebooks)

[//]: # ()
[//]: # ()
[//]: # (4. Using the `Import .ipynb file`, import the downloaded Notebooks)

[//]: # ()
[//]: # ()
[//]: # (<img src="assets/import_notebook.png"/>)

[//]: # ()
[//]: # ()
[//]: # (5. Select the `CHURN_PROD` database and `ANALYTICS` schema for the Notebook Location and `CHURN_DS_WH` for the Notebook warehouse and click `Create`)

[//]: # ()
[//]: # ()
[//]: # (6. To add Anaconda packages to both Notebooks separately, select the specified Notebook, click the `Packages` button on the package explorer in the top of the page to add the following packages: `altair`, `imbalanced-learn`, `numpy`, `pandas`, and `snowflake-ml-python`)

[//]: # ()
[//]: # ()
[//]: # (<img src="assets/anaconda.png"/>)

[//]: # ()
[//]: # ()
[//]: # (7. At the top of the page, click `Start` to start the Notebook session and run the cells by clicking `Run All`)

[//]: # ()
[//]: # ()
[//]: # (<img src="assets/start.png"/>)

[//]: # ()
[//]: # ()
[//]: # (<!-- ------------------------ -->)

[//]: # ()
[//]: # (## Clean Up)

[//]: # ()
[//]: # (Duration: 2)

[//]: # ()
[//]: # ()
[//]: # (### Remove Snowflake Objects)

[//]: # ()
[//]: # (1. Navigate to Worksheets, click `+` in the top-right corner to create a new Worksheet, and choose `SQL Worksheet`)

[//]: # ()
[//]: # (2. Copy and paste the following SQL statements in the worksheet to drop all Snowflake objects created in this Quickstart)

[//]: # ()
[//]: # (```)

[//]: # ()
[//]: # (USE ROLE securityadmin;)

[//]: # ()
[//]: # (DROP ROLE IF EXISTS churn_data_scientist;)

[//]: # ()
[//]: # (USE ROLE accountadmin;)

[//]: # ()
[//]: # (DROP DATABASE IF EXISTS churn_prod;)

[//]: # ()
[//]: # (DROP WAREHOUSE IF EXISTS churn_ds_wh;)

[//]: # ()
[//]: # (```)

[//]: # ()
[//]: # ()
[//]: # (<!-- ------------------------ -->)

[//]: # ()
[//]: # (## Conclusion and Resources)

[//]: # ()
[//]: # (Duration: 5)

[//]: # ()
[//]: # ()
[//]: # (### Congrats! You're reached the end of this Quickstart!)

[//]: # ()
[//]: # ()
[//]: # (### What You Learned)

[//]: # ()
[//]: # (With the completion of this Quickstart, you have now delved into:)

[//]: # ()
[//]: # (- How to import/load data with Snowflake Notebook)

[//]: # ()
[//]: # (- How to train a Random Forest with Snowpark ML model)

[//]: # ()
[//]: # (- How to visualize the predicted results from the forecasting model)

[//]: # ()
[//]: # (- How to build an interactive web app and make predictions on new users)

[//]: # ()
[//]: # ()
[//]: # (### Resources)

[//]: # ()
[//]: # (- [Snowflake Solutions Center - Data Analysis and Churn Prediction Using Snowflake Notebooks]&#40;https://developers.snowflake.com/solution/data-analysis-and-churn-prediction-using-snowflake-notebooks/&#41;)

[//]: # ()
[//]: # (- [Snowflake Documentation]&#40;https://docs.snowflake.com/&#41;)

[//]: # ()
[//]: # (- [Snowflake Notebooks]&#40;https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks&#41;)

[//]: # ()
[//]: # (- [Snowpark API]&#40;https://docs.snowflake.com/en/developer-guide/snowpark/index&#41;)
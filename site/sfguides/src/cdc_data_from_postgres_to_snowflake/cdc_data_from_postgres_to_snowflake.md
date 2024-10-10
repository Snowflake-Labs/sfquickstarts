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

<!-- ------------------------ -->
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

<!-- ------------------------ -->
## Configure the Agents

Duration: 10
### Overview
During this section, you will configure the Agen that will operate alongside our Source Databases.

### Configure the Agents
The first step is to create the **agent-postgresql** directory. In this directory, you will create 2 directories named **agent-keys** and **configuration**.

#### Creating Configuration Files
In this step, you will fill the configuration files for each agent to operate correctly. The configuration files include:
- **snowflake.json** file to connect to Snowflake
- **datasources.json** file to connect to the Source Databases
- **postgresql.conf** file with additional Agent Environment Variables

1. Navigate to the directory called **agent-postgresql**
2. Create the docker-compose file named **docker-compose2.yaml** with the following content:
```
version: '1'
services:
  postgresql-agent:
    container_name: postgresql-agent
    image: snowflakedb/database-connector-agent:latest
    volumes:
      - ./agent-keys:/home/agent/.ssh
      - ./configuration/snowflake.json:/home/agent/snowflake.json
      - ./configuration/datasources.json:/home/agent/datasources.json
    env_file:
      - configuration/postgresql.conf
    mem_limit: 6g
```

3. Put the previously downloaded **snowflake.json** file in the **configuration** directory folder.
4. Create the file named **datasources.json** with the following content:
```
{
  "PSQLDS1": {
    "url": "jdbc:postgresql://host.docker.internal:5432/postgres",
    "username": "postgres",
    "password": "postgres",
    "publication": "agent_postgres_publication",
    "ssl": false
  }
}
```

5. Create the file named **postgresql.conf** with the following content:
```
JAVA_OPTS=-Xmx5g
```

6. Navigating to the terminal, start the agent using the following command. The agent should generate public/private key for authorization to Snowflake.
```
docker-compose up -d
```

At the end, your directory structure should resemble the following, including the inclusion of the automatically generated private and public keys within the agent-keys directory.

Directory Structure
<ul>
  <li>agent-postgresql
    <ul>
      <li>agent-keys
        <ul>
          <li>database-connector-agent-app-private-key.p8</li>
          <li>database-connector-agent-app-public-key.pub</li>
        </ul>
      </li>
      <li>configuration
        <ul>
          <li>datasources.json</li>
          <li>postgresql.conf</li>
          <li>snowflake.json</li>
        </ul>
      </li>
      <li>docker-compose.yaml</li>
    </ul>
  </li>
</ul>

#### Verifying Connection with Snowflake
Navigate to Snowsight to your previously created Native Apps. Click on the **Refresh** button in the Agent Connection Section.
When successfully configured, you should see the message: Agent is fully set up and connected. To select data ingest Open Worksheet.

<!-- ------------------------ -->
## Configure and Monitor Data Ingestion Process
Duration: 10

### Overview
In this step, we will instruct the Connector to begin replicating the selected tables.

### Configure Data Ingestion
1. Download the [0_start_here.ipynb](https://github.com/Snowflake-Labs/sfguide-intro-to-cdc-using-snowflake-postgres-connector-dynamic-tables/blob/main/notebooks/0_start_here.ipynb) Notebook and import it into Snowflake by navigating to Snowsight and going to **Notebooks** and to using the `Import .ipynb file` button. This Notebook includes the SQL scripts needed to create the sink database, add the data sources for table replication into Snowflake, and monitor the replication process.
2. Run the first 3 cells in the Notebook labeled **create_db_objects**, **table_replication**, and **check_replication_state**.
3. Run the cell labeled **check_replication_state** until the output indicates successful replication, resembling the following:
<table border="1">
  <thead>
    <tr>
      <th>REPLICATION_PHASE</th>
      <th>SCHEMA_INTROSPECTION_STATUS</th>
      <th>SNAPSHOT_REPLICATION_STATUS</th>
      <th>INCREMENTAL_REPLICATION_STATUS</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>INCREMENTAL_LOAD</td>
      <td>DONE</td>
      <td>DONE</td>
      <td>IN PROGRESS</td>
    </tr>
  </tbody>
</table>

4. Once the replication process is complete, you can run the rest of the Notebook.
5. Notice the Dynamic table, **CONNECTORS_DEST_DB."CDC"."CUSTOMER_PURCHASE_SUMMARY"**, is created in the last cell labeled **create_dynamic_table**. This table will be used to visualize the data in the **Customer Spending Dashboard** Streamlit app.

<!-- ------------------------ -->
## Streamlit-in-Snowflake Application
Duration: 10 

### Overview
In this section, we will create a Streamlit-in-Snowflake application to visualize the customer purchase summary data.

### Create the Streamlit-in-Snowflake Application
1. Navigate to Snowsight and go to **Projects** then **Streamlit**. Click on the **+ Streamlit App** to create a new Streamlit application.
2. For the **App Title**, enter `Customer Spending Dashboard`
3. For the **App location**, enter `CONNECTORS_DEST_DB` for the database and `CDC` for the schema
4. For the **App warehouse**, choose an available warehouse, preferably an **X-SMALL** sized warehouse and click **Create**
5. Copy and paste the contents of the [customer_purchase_summary.py](https://github.com/Snowflake-Labs/sfguide-intro-to-cdc-using-snowflake-postgres-connector-dynamic-tables/blob/main/scripts/customer_spending_dashboard.py) file into the Streamlit app code editor
6. Here, we can view the purchase summary for all or selected customers by selecting various filter for dates, customer IDs, and product categories and more

<!-- ------------------------ -->
## Clean Up
Duration: 2

### Overview
In this section, we will clean up the Snowflake objects that were made in this Quickstart.

### Clean Up Script
1. Navigate to Worksheets, click **+** in the top-right corner to create a new Worksheet, and choose **SQL Worksheet**
```
DROP ROLE POSTGRESQL_ADMINISTRATIVE_AGENT_ROLE;
DROP ROLE POSTGRESQL_AGENT_ROLE;
```

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 5
### Congrats! You're reached the end of this Quickstart!

### What You Learned
With the completion of this Quickstart, you have now delved into:
- How to connect PostgreSQL data to Snowflake using the Snowflake Connector for PostgreSQL
- Visualize data using Dynamic Tables and display visualizations within Streamlit-in-Snowflake (SiS)

### Resources
- [Snowflake Solutions Center - Real-Time Financial Insights with Change Data Capture (CDC) with PostgreSQL, Dynamic Tables, and Streamlit-in-Snowflake] - placeholder for link
- [Snowflake Connector for PostgreSQL](https://other-docs.snowflake.com/en/connectors/postgres6/about)
- [Snowflake Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Snowpark API](https://docs.snowflake.com/en/developer-guide/snowpark/index)
- [Streamlit-in-Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
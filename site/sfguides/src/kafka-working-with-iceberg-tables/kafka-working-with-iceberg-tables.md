author: Ashish Kumar
id: kafka-working-with-iceberg-tables
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/ingestion, snowflake-site:taxonomy/snowflake-feature/apache-iceberg
language: en
summary: Through this quickstart guide, you will explore how to ingest data from kafka to Iceberg tables. 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Intro to Kafka and Snowflake Managed Iceberg
<!-- ------------------------ -->
## Overview 

This guide provides a comprehensive walkthrough for establishing a local data streaming pipeline from open-source Apache Kafka to Snowflake-managed Iceberg tables. We will configure the Snowflake Kafka Connector to leverage Snowpipe Streaming, enabling efficient, near real-time data ingestion while seamlessly handling schema evolution. This setup facilitates a robust and adaptable data flow, ensuring that changes in your Kafka topics are automatically reflected in your Snowflake-managed Iceberg tables.


### Prerequisites
Before proceeding, ensure you have the following:

- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=ap-in-en-brand-cloud-phrase&utm_content=go-rsa-evg-ss-free-trial&utm_term=c-g-snowflake%20computing-p&_bt=591408722054&_bk=snowflake%20computing&_bm=p&_bn=g&_bg=133380613608&gclsrc=aw.ds&gad_source=1&gclid=EAIaIQobChMI7fjZvc6ljAMVy-gWBR3CORZMEAAYASAAEgLvMvD_BwE&utm_cta=developer-guides)
- Visual Studio Code (VSCode) installed.
- Cloud Provider Amazon S3 or Azure Blob storage to write with the iceberg files.

### What You’ll Learn 
- Local installation and configuration of Apache Kafka on macOS.
- Configuration of the Snowflake Kafka Connector for Snowpipe Streaming.
- Implementation of data ingestion and schema evolution for Iceberg tables using the Snowflake Kafka Connector.


### What You’ll Build 
- A streaming pipeline through kafka to Snowflake-managed iceberg table

<!-- ------------------------ -->
<!-- ------------------------ -->

## Setup

1. Configure an external volume by following this [Document](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3)
or if you are using Azure Blob you can follow this [Document](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-azure)

```commandline
Example:

USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE EXTERNAL VOLUME iceberg_external_volume_s3
   STORAGE_LOCATIONS =
      (
         (
            NAME = 'my-s3-us-west-2'
            STORAGE_PROVIDER = 'S3'
            STORAGE_BASE_URL = 's3://<s3-bucket>/iceberg'
            STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<aws account>:role/icerberg_table_access_role'
            STORAGE_AWS_EXTERNAL_ID = 'icerberg_table_access_id'
         )
      );
```

2. Login to snowsight and run the sql statements to create database,schema and Iceberg table:

```commandline
SET PWD = 'Test1234567';
SET USER = 'demo_user';
SET DB = 'demo_db';
SET SCHEMA = 'demo_schema'

USE ROLE ACCOUNTADMIN;

-- CREATE USERS
CREATE USER IF NOT EXISTS IDENTIFIER($USER) PASSWORD=$PWD  COMMENT='STREAMING USER';

-- GRANTS
GRANT ROLE SYSADMIN TO USER IDENTIFIER($USER);

-- CREATE DATABASE AND SCHEMA
CREATE DATABASE IDENTIFIER($DB);
CREATE SCHEMA IDENTIFIER($SCHEMA);

-- CREATE ICEBERG TABLE
USE DATABASE IDENTIFIER($DB);
USE SCHEMA IDENTIFIER($SCHEMA);

CREATE OR REPLACE ICEBERG TABLE emp_iceberg_tab (
    record_metadata OBJECT()
  )
  EXTERNAL_VOLUME = 'iceberg_external_volume_s3'
  CATALOG = 'SNOWFLAKE'
  BASE_LOCATION = 'emp_iceberg_tab';
```

3. Enable schema evolution on the table

Snowflake enables seamless handling of evolving semi-structured data. As data sources add new columns, Snowflake automatically updates table structures to reflect these changes, including the addition of new columns. This eliminates the need for manual schema adjustments. More Info [Document](https://docs.snowflake.com/en/user-guide/data-load-schema-evolution)

```commandline
alter ICEBERG table emp_iceberg_tab set ENABLE_SCHEMA_EVOLUTION  =true;
```

4. Create a key-pair to be used for authenticating(We will not used username and password) with Snowflake user by following [Document](https://docs.snowflake.com/en/user-guide/key-pair-auth)

To generate an encrypted version, use the following command, which omits -nocrypt:

```commandline
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 des3 -inform PEM -out rsa_key.p8
```

The commands generate a private key in PEM format.

```commandline
-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIE6T...
-----END ENCRYPTED PRIVATE KEY-----
```

Generate a public key

```commandline
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

The command generates the public key in PEM format.

```commandline
-----BEGIN PUBLIC KEY-----
MIIBIj...
-----END PUBLIC KEY-----
```

Assign the public key to a Snowflake user
```commandline
use role accountadmin;
alter user demo_user set rsa_public_key='< pubKey >';
```

<!-- ------------------------ -->

<!-- ------------------------ -->
## Setup Local Kafka

1. Download kafka in your local mac from [here](https://kafka.apache.org/downloads). This tutorial used kafka version 2.8.1.

2. Start zookeeper in new terminal

```commandline
cd kafka_2.13-2.8.1/bin
./zookeeper-server-start.sh ../config/zookeeper.properties
```

![](assets/zookeper_start.png)


3. Start Kafka server in new terminal

```commandline
cd kafka_2.13-2.8.1/bin
./kafka-server-start.sh ../config/server.properties
```

![](assets/kafka_server.png)

4. Download snowflake-kafka-connector from [here](https://mvnrepository.com/artifact/com.snowflake/snowflake-kafka-connector/3.1.0)

![](assets/kafka_server.png)

- Copy kafka connector jar file into kafka_2.13-2.8.1/libs/ folder

5. Create kafka topic 

```commandline
cd kafka_2.13-2.8.1/bin
./kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 2 --topic demo_topic
```


6. Run kafka producer in console mode and produce some records

```commandline
cd kafka_2.13-2.8.1/bin
./kafka-console-producer.sh --bootstrap-server localhost:9092 --topic demo_topic
```

- Sample Records

```commandline
Sample records:
{"emp_id":100,"first_name":"Keshav","last_name":"Lodhi","designation":"DataEngineer"}
{"emp_id":101,"first_name":"Ashish","last_name":"kumar","designation":"Solution Architect"}
{"emp_id":102,"first_name":"Anup","last_name":"moncy","designation":"Solution Architect"}
```

7. validate records produced in previous step  

```commandline
cd kafka_2.13-2.8.1/bin
./kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic demo_topic --from-beginning
```

- You should be able to see all 3 records from above output.

8. Run snowflake kafka connector in distributed mode in new terminal

- Run this command to start kafka connector on your machine

```commandline
cd kafka_2.13-2.8.1/bin
./connect-distributed.sh <full_path>/kafka_2.13-2.8.1/config/connect-distributed.properties
```

9. create configuration for connector

```commandline
cd kafka_2.13-2.8.1/config/

vi SF_connect1.json

{
    "name":"demoiceberg",
    "config":{
    "snowflake.ingestion.method":"SNOWPIPE_STREAMING",
    "snowflake.streaming.iceberg.enabled":true,
    "snowflake.enable.schematization":true,
    "snowflake.role.name":"sysadmin",
    "key.converter":"org.apache.kafka.connect.json.JsonConverter",
    "value.converter":"org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable":false,
    "value.converter.schemas.enable":false,
    "connector.class":"com.snowflake.kafka.connector.SnowflakeSinkConnector",
    "tasks.max":"8",
    "topics":"demo_topic",
    "snowflake.topic2table.map":" demo_topic:emp_iceberg_tab",
    "buffer.count.records":"10000",
    "buffer.flush.time":"60",
    "buffer.size.bytes":"5000000",
    "snowflake.url.name":"https://xxxxx-nrb47395.snowflakecomputing.com",
    "snowflake.user.name":"demo_user",
    "snowflake.database.name":"demo_db",
    "snowflake.schema.name":"demo_schema",
    "snowflake.private.key":"MIIFDjBABgkqh****",
    "snowflake.private.key.passphrase":"***"
    }
}
```

- Update the following configuration values based on your setup:

```
snowflake.role.name → You can set this to SYSADMIN for demo purposes.
topics → This should be the Kafka topic name created in Step 5.
snowflake.topic2table.map → Map your Kafka topic name to the Iceberg table name created earlier.
snowflake.url.name → Enter the URL of your Snowflake account.
snowflake.user.name → Specify your Snowflake username.
snowflake.database.name → Use the database name created in the "Create Snowflake Managed Iceberg Table" step.
snowflake.schema.name → Use the schema name created in the "Create Snowflake Managed Iceberg Table" step.
snowflake.private.key → Copy the content of the private key generated in the "Create Snowflake Managed Iceberg Table" step.
snowflake.private.key.passphrase → Enter the passphrase for the encrypted private key file created in the same step.
```

10. Execute configuration

```commandline
curl -X POST -H "Content-Type: application/json" --data @<full_path>kafka_2.13-2.8.1/config/SF_connect1.json http://localhost:8083/connectors
```
<!-- ------------------------ -->

<!-- ------------------------ -->

## Schema evolution and Validate data 

1. Check iceberg table by login into snowsight

```commandline
select * from emp_iceberg_tab;
```

![](assets/validation1.png)

- Now you will see 4 columns detected by the connector
```
- EMP_ID	NUMBER(19,0)
- DESIGNATION	VARCHAR(16777216)
- LAST_NAME	VARCHAR(16777216)
- FIRST_NAME	VARCHAR(16777216)
```

2. Producer few more record in kafka topic

```
{"emp_id":102,"first_name":"Anup","last_name":"moncy","designation":"Solution Architect","company":"Snowflake"}
```

3. Validate the data and schema of Iceberg table

```
select * from emp_iceberg_tab;
```

![](assets/validation2.png)

- Now you will see 5 columns detected by the connector
```
EMP_ID	NUMBER(19,0)
DESIGNATION	VARCHAR(16777216)
LAST_NAME	VARCHAR(16777216)
FIRST_NAME	VARCHAR(16777216)
COMPANY	VARCHAR(16777216)
```

<!-- ------------------------ -->

<!-- ------------------------ -->

## Conclusion And Resources

### What You Learned
- Local installation and configuration of Apache Kafka.
- Configuration of the Snowflake Kafka Connector for Snowpipe Streaming in distributed mode.
- Implementation of data ingestion and schema evolution for Iceberg tables using the Snowflake Kafka Connector.

### Related Resources
- [Apache Iceberg™ tables | Snowflake Documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Configuring key-pair authentication | Snowflake Documentation](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Using Snowflake Connector for Kafka with Snowpipe Streaming | Snowflake Documentation](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-kafka)
<!-- ------------------------ -->

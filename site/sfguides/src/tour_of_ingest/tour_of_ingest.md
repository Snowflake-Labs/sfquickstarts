summary: Learn how to ingest data into Snowflake with Python Connector, Streaming SDK, Snowpipe, Snowpark, and Kafka
id: tour_of_ingest 
categories: featured, getting-started, data-engineering
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Data Applications, Ingest
authors: Brad Culberson

# Tour of Ingest

## Overview 
Duration: 3

There are many different ways to get data into Snowflake. Different use cases, requirements, team skillsets, and technology choices all
contribute to making the right decision on how to ingest data. This quickstart will guide you through an example of the same data loaded with different methods:

* SQL Inserts from the Python Connector
* File Upload & Copy (Warehouse) from the Python Connector
* File Upload & Copy (Snowpipe) using Python
* File Upload & Copy (Serverless) from the Python Connector
* Inserting Data from a Dataframe with Snowpark
* From Kafka - in Snowpipe (Batch) mode
* From Kafka - in Snowpipe Streaming mode
* From Java SDK - Using the Snowflake Ingest Service

By the end of this guide you should be familiar with many ways to load data, and be able to choose the right pattern for your goals and needs. Each method of ingest can be done separately and optionally as desired after going through the initial project setup and are not dependent on each other.

### Prerequisites
- Snowflake Account with the ability to create a User, Role, Database, Snowpipe, Serverless Task, Execute Task
- Familiarity with Python, Kafka, and/or Java
- Basic knowledge of Docker, Git
- Ability to run Docker locally or access to an environment to run Kafka and Kafka Connectors

### What You’ll Learn 
- How and when to insert data using connectors
- How and when to insert data from files
- How to load data from Kafka
- How to load data from a stream

### What You’ll Need 
- [GitHub](https://github.com/) Account 
- [Conda](https://conda.io) Installed
- [Snowflake](https://snowflake.com/) Account 

### What You’ll Build 
- A project which can load data many different ways

## Environment Setup
Duration: 3

This guide has a data generator and several examples which need Python 3.8 with the same packages. To set up these dependencies, we will use conda.

```bash
conda create -n sf-ingest-examples python=3.8 -c https://repo.anaconda.com/pkgs/snowflake -c conda-forge
conda activate sf-ingest-examples
conda install openjdk maven
conda install pip
```

To install the Snowflake packages needed for the guide:

```bash
conda install pyarrow=10.0.1 pandas snowflake-connector-python snowflake-snowpark-python snowflake-ingest
```

We will want rapidjson and faker for the json data generator.
```bash
conda install faker python-rapidjson
pip install optional-faker
```

All credentials and configuration will be stored in a .env file so we will also want an easy way to load those with the dotenv package.
```bash
conda install python-dotenv
```

Some Kafka libraries will also be needed for this guide.
```bash
conda install python-confluent-kafka kafka-python
```

Anytime you want to come back to this guide, you can reactivate this environment with:
```bash
conda activate sf-ingest-examples
```

## Test Data Generation
Duration: 5

It is nice to have real-world looking data for testing. This guide will generate fictitious lift tickets for patrons of ski resorts.

You may have your own data you would like to generate, feel free to modify the data generator, the tables, and the code as you go to make it more applicable your use cases.

Most of the ingest patterns we will go through in this guide will actually outperform the faker library so it is best to run the data generation once and reuse that generated data in the different ingest patterns.

Create a director on your computer for this project and add a file called data_generator.py. This code will take the number of tickets to create as an arg and output the json data with one lift ticket (record) per line. The rest of the files in this guide can be put in this same directory.

```python
import sys
import rapidjson as json
import optional_faker as _
import uuid
import random

from dotenv import load_dotenv
from faker import Faker
from datetime import date, datetime

load_dotenv()
fake = Faker()
resorts = ["Vail", "Beaver Creek", "Breckenridge", "Keystone", "Crested Butte", "Park City", "Heavenly", "Northstar",
           "Kirkwood", "Whistler Blackcomb", "Perisher", "Falls Creek", "Hotham", "Stowe", "Mount Snow", "Okemo",
           "Hunter Mountain", "Mount Sunapee", "Attitash", "Wildcat", "Crotched", "Stevens Pass", "Liberty", "Roundtop", 
           "Whitetail", "Jack Frost", "Big Boulder", "Alpine Valley", "Boston Mills", "Brandywine", "Mad River",
           "Hidden Valley", "Snow Creek", "Wilmot", "Afton Alps" , "Mt. Brighton", "Paoli Peaks"]    


def print_lift_ticket():
    global resorts, fake
    state = fake.state_abbr()
    lift_ticket = {'txid': str(uuid.uuid4()),
                   'rfid': hex(random.getrandbits(96)),
                   'resort': fake.random_element(elements=resorts),
                   'purchase_time': datetime.utcnow().isoformat(),
                   'expiration_time': date(2023, 6, 1).isoformat(),
                   'days': fake.random_int(min=1, max=7),
                   'name': fake.name(),
                   'address': fake.optional({'street_address': fake.street_address(), 
                                             'city': fake.city(), 'state': state, 
                                             'postalcode': fake.postalcode_in_state(state)}),
                   'phone': fake.optional(fake.phone_number()),
                   'email': fake.optional(fake.email()),
                   'emergency_contact' : fake.optional({'name': fake.name(), 'phone': fake.phone_number()}),
    }
    d = json.dumps(lift_ticket) + '\n'
    sys.stdout.write(d)


if __name__ == "__main__":
    args = sys.argv[1:]
    total_count = int(args[0])
    for _ in range(total_count):
        print_lift_ticket()
    print('')

```

To test this generator, run:
```bash
python ./data_generator.py 1
```

You should see 1 record written to output.

In order to quickly have data available for the rest of the guide, dump a lot of data to a file for re-use.

```bash
python ./data_generator.py 100000 | gzip > data.json.gz
```

You can increase or decrease the size of records to any number that you would like to use. This will currently output the sample data to your current directory, but you can pick any folder you would like. This file will be used in subsequent steps so note where you stored this data and replace later if needed.

## Database Setup
Duration: 3

Kafka and the Snowpipe API both require the use of key pair authentication. Due to this, I will use keypair for all the ingest solutions so they are all in common. 

Create a database, schema, warehouse, role, and user called INGEST in your Snowflake account.

```sql

CREATE WAREHOUSE INGEST;
CREATE ROLE INGEST;
GRANT USAGE ON WAREHOUSE INGEST TO ROLE INGEST;
GRANT OPERATE ON WAREHOUSE INGEST TO ROLE INGEST;
CREATE DATABASE INGEST;
CREATE SCHEMA INGEST;
GRANT OWNERSHIP ON DATABASE INGEST TO ROLE INGEST;
GRANT OWNERSHIP ON SCHEMA INGEST.INGEST TO ROLE INGEST;

CREATE USER INGEST PASSWORD='<REDACTED>' LOGIN_NAME='INGEST' MUST_CHANGE_PASSWORD=FALSE, DISABLED=FALSE, DEFAULT_WAREHOUSE='INGEST', DEFAULT_NAMESPACE='INGEST.INGEST', DEFAULT_ROLE='INGEST';
GRANT ROLE INGEST TO USER INGEST;
GRANT ROLE INGEST TO USER <YOUR_USERNAME>;
```

To generate a key pair for the INGEST user, run the following:
```bash
openssl genrsa 4096 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
PUBK=`cat ./rsa_key.pub | tail -n 13 | head -n 12 | tr -d '\012'`
echo "ALTER USER INGEST SET RSA_PUBLIC_KEY='$PUBK';"
```

Run the sql from the output to set the RSA_PUBLIC_KEY for the INGEST user.

To get the private key for this user run the following:

```bash
PRVK=`cat ./rsa_key.p8 | tail -n 51 | head -n 50 | tr -d '\012'`
echo "PRIVATE_KEY=$PRVK"
```

Add these variables to a new .env file in your project:

```
SNOWFLAKE_ACCOUNT=<ACCOUNT_HERE>
SNOWFLAKE_USER=INGEST
PRIVATE_KEY=<PRIVATE_KEY_HERE>
```

Make sure you protect your .env and .p8 file as those are credentials directly to the INGEST user.

## SQL Inserts from the Python Connector
Duration: 5

Snowflake has a [Python connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector) which is an easy way to run sql and upload files. One way to get data in would be to do an SQL INSERT statement for each record. While this is a convenient way to insert data, it is not efficient as Snowflake is an OLAP engine and is optimized around writing large batches of data.

Create a table in Snowflake called LIFT_TICKETS_PY_INSERT to recieve this data from the INGEST user.

```sql
USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_PY_INSERT (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);
```

Create a file named py_insert.py. This code will read a line from standard input and insert that record into Snowflake using a SQL INSERT. Change the table names/fields as needed to support your use case.

```python
import os, sys, logging
import json
import snowflake.connector

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

load_dotenv()
logging.basicConfig(level=logging.WARN)
snowflake.connector.paramstyle='qmark'


def connect_snow():
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    p_key = serialization.load_pem_private_key(
        bytes(private_key, 'utf-8'),
        password=None
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role="INGEST",
        database="INGEST",
        schema="INGEST",
        warehouse="INGEST",
        session_parameters={'QUERY_TAG': 'py-insert'}, 
    )


def save_to_snowflake(snow, message):
    record = json.loads(message)
    logging.debug('inserting record to db')
    row = (record['txid'],record['rfid'],record["resort"],record["purchase_time"],record["expiration_time"],record['days'],record['name'],json.dumps(record['address']),record['phone'],record['email'],json.dumps(record['emergency_contact']))
    # this dataset has variant records, so utilizing an executemany() is not possible, must insert 1 record at a time
    snow.cursor().execute("INSERT INTO LIFT_TICKETS_PY_INSERT (\"TXID\",\"RFID\",\"RESORT\",\"PURCHASE_TIME\", \"EXPIRATION_TIME\",\"DAYS\",\"NAME\",\"ADDRESS\",\"PHONE\",\"EMAIL\",\"EMERGENCY_CONTACT\") SELECT ?,?,?,?,?,?,?,PARSE_JSON(?),?,?,PARSE_JSON(?)", row)
    logging.debug(f"inserted ticket {record}")


if __name__ == "__main__":    
    snow = connect_snow()
    for message in sys.stdin:
        if message != '\n':
            save_to_snowflake(snow, message)
        else:
            break
    snow.close()
    logging.info("Ingest complete")
    
```

In order to test this insert, run the following:

```bash
python ./data_generator.py 1 | python py_insert.py
```

Query the table to verify the data was inserted.

```sql
SELECT count(*) FROM LIFT_TICKETS_PY_INSERT;
```

WARNING, this is not a good way to load data and will take a long time. I don't really want you to have to wait for hours to load your example dataset, so lets just load 1000 records.

To send in all your test data, you can run the following:
```bash
cat data.json.gz | zcat | head -n 1000 | python py_insert.py
```

Feel free to take a break and come back in a few minutes.

Do you think this could be faster if we parallelized the work? 

To verify if that is true or not, run 10 of these same loads in multiple terminals and see how long it takes.

```bash
cat data.json.gz | zcat | head -n 100 | python py_insert.py
```

The total time loading in parallel will be the same or worse than before. This is not a good pattern to get to high throughputs of records.

### Tips

* Ingest is billed based on warehouse credits consumed while online.

* The connectors support multi-inserts but data containing a variant field cannot be formatted into a multi-insert.

* Using inserts and multi-inserts will not efficiently use warehouse resources (optimal at 100MB or more with some concurrency). It is better to upload data and COPY into the table.

* Connectors will switch to creating and uploading a file and doing a COPY into when large batches are set. This is not configurable.

* Many assume adding significant concurrency will support higher throughputs of data. The additional concurrent INSERTS will be blocked by other INSERTS, more frequently when small payloads are inserted. You need to move to bigger batches to get more througput.

* Review query history to see what the connector is doing.

In cases where the connector has enough data in the executemany to create a well sized file for COPY and does so, this does become as efficient as the following methods.

The example above could not use executemany as it had VARIANT data.

The next methods will show how to batch into better sized blocks of work which will drive higher throughputs and higher efficiency on Snowflake.


## File Upload & Copy (Warehouse) from the Python Connector
Duration: 5

To get to better sized batches, the client can upload a file and have a warehouse copy the data into the destination. The Python connector can execute the COPY after uploading the file.

Create the table which will be used for landing the data, changing as needed for your use case.

```sql
USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_PY_COPY_INTO (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);
```

Create a file named py_copy_into.py with the following contents. You will need to change this code if you changed the data generator.

```python
import os, sys, logging
import json
import uuid
import snowflake.connector
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

load_dotenv()
logging.basicConfig(level=logging.WARN)


def connect_snow():
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    p_key = serialization.load_pem_private_key(
        bytes(private_key, 'utf-8'),
        password=None
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role="INGEST",
        database="INGEST",
        schema="INGEST",
        warehouse="INGEST",
        session_parameters={'QUERY_TAG': 'py-copy-into'}, 
    )


def save_to_snowflake(snow, batch, temp_dir):
    logging.debug("inserting batch to db")
    pandas_df = pd.DataFrame(
        batch,
        columns=[
            "TXID",
            "RFID",
            "RESORT",
            "PURCHASE_TIME",
            "EXPIRATION_TIME",
            "DAYS",
            "NAME",
            "ADDRESS",
            "PHONE",
            "EMAIL",
            "EMERGENCY_CONTACT",
        ],
    )
    arrow_table = pa.Table.from_pandas(pandas_df)
    out_path = f"{temp_dir.name}/{str(uuid.uuid1())}.parquet"
    pq.write_table(arrow_table, out_path, use_dictionary=False, compression="SNAPPY")
    snow.cursor().execute(
        "PUT 'file://{0}' @%LIFT_TICKETS_PY_COPY_INTO".format(out_path)
    )
    os.unlink(out_path)
    snow.cursor().execute(
        "COPY INTO LIFT_TICKETS_PY_COPY_INTO FILE_FORMAT=(TYPE='PARQUET') MATCH_BY_COLUMN_NAME=CASE_SENSITIVE PURGE=TRUE"
    )
    logging.debug(f"inserted {len(batch)} tickets")


if __name__ == "__main__":
    args = sys.argv[1:]
    batch_size = int(args[0])
    snow = connect_snow()
    batch = []
    temp_dir = tempfile.TemporaryDirectory()
    for message in sys.stdin:
        if message != "\n":
            record = json.loads(message)
            batch.append(
                (
                    record["txid"],
                    record["rfid"],
                    record["resort"],
                    record["purchase_time"],
                    record["expiration_time"],
                    record["days"],
                    record["name"],
                    record["address"],
                    record["phone"],
                    record["email"],
                    record["emergency_contact"],
                )
            )
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir)
                batch = []
        else:
            break
    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir)
    temp_dir.cleanup()
    snow.close()
    logging.info("Ingest complete")


```

You will see a lot of similarity of this pattern with the previous one in that the connection is the same, but instead of doing single record inserts it batches together a set of records. That batch is written into a Parquet file which is PUT to the table stage and COPY is used to insert. This data shows up immediately after the COPY call is made.

In order to test this insert, run the following:

```bash
python ./data_generator.py 1 | python py_copy_into.py 1
```

Query the table to verify the data was inserted.

```sql
SELECT count(*) FROM LIFT_TICKETS_PY_COPY_INTO;
```

To send in all your test data, you can run the following:
```bash
cat data.json.gz | zcat | python py_copy_into.py 10000
```

This last call will batch together 10,000 records into each file for processing. As this file gets larger, up to 100mb, you will see this be more efficient on seconds of compute used in Snowpipe and see higher throughputs. Feel free to generate more test data and increase this to get more understanding of this relationship. Review the query performance in Query History in Snowflake.

### Tips

* Ingest is billed based on warehouse credits consumed while online.

* It is very hard to fully utilize a warehouse with this pattern. Adding some concurrency will help IF the files are already well sized. Even with the best code, very few workloads have fixed data flow volumes that well match a warehouse. This is mostly a wasted effort as serverless and snowpipe solves all use cases w/o constraints.

* Try to get to 100mb files for most efficiency.

* Best warehouses sizes are almost always way smaller than expected, commonly XS.


## File Upload & Copy (Snowpipe) using Python
Duration: 5

Another way to get data into Snowflake is to use a service specifically designed for this task: [Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro). Snowpipe uses serverless infrastructure to ingest data from a file uploaded from a client. In this use case I will upload a file to an internal stage and call the Snowpipe service to ingest the file.

This is not the only way to use Snowpipe. You can use external stages as well as use eventing from those blob stores so Snowflake will automatically ingest files as they land. Kafka also uses Snowpipe internally which you will see in later examples.

Create the table and the snowpipe to handle the ingest. If you changed the data generator for your use case, you will need to change this table to support your data.

```sql
USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_PY_SNOWPIPE (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);

CREATE PIPE LIFT_TICKETS_PIPE AS COPY INTO LIFT_TICKETS_PY_SNOWPIPE
FILE_FORMAT=(TYPE='PARQUET') 
MATCH_BY_COLUMN_NAME=CASE_SENSITIVE;
```

Create a file called py_snowpipe.py. This code will read a batch of lines from standard input, write a file to temporary storage, upload/put that file to LIFT_TICKETS_PY_SNOWPIPE stage, and call the API endpoint to have LIFT_TICKETS_PIPE ingest the file uploaded. Snowpipe will do the COPY INTO the table LIFT_TICKETS_PY_SNOWPIPE.

```python
import os, sys, logging
import json
import uuid
import snowflake.connector
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile

from dotenv import load_dotenv
from snowflake.ingest import SimpleIngestManager
from snowflake.ingest import StagedFile

load_dotenv()
from cryptography.hazmat.primitives import serialization

logging.basicConfig(level=logging.WARN)


def connect_snow():
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    p_key = serialization.load_pem_private_key(
        bytes(private_key, 'utf-8'),
        password=None
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role="INGEST",
        database="INGEST",
        schema="INGEST",
        warehouse="INGEST",
        session_parameters={'QUERY_TAG': 'py-snowpipe'}, 
    )


def save_to_snowflake(snow, batch, temp_dir, ingest_manager):
    logging.debug('inserting batch to db')
    pandas_df = pd.DataFrame(batch, columns=["TXID","RFID","RESORT","PURCHASE_TIME", "EXPIRATION_TIME","DAYS","NAME","ADDRESS","PHONE","EMAIL", "EMERGENCY_CONTACT"])
    arrow_table = pa.Table.from_pandas(pandas_df)
    file_name = f"{str(uuid.uuid1())}.parquet"
    out_path =  f"{temp_dir.name}/{file_name}"
    pq.write_table(arrow_table, out_path, use_dictionary=False,compression='SNAPPY')
    snow.cursor().execute("PUT 'file://{0}' @%LIFT_TICKETS_PY_SNOWPIPE".format(out_path))
    os.unlink(out_path)
    # send the new file to snowpipe to ingest (serverless)
    resp = ingest_manager.ingest_files([StagedFile(file_name, None),])
    logging.info(f"response from snowflake for file {file_name}: {resp['responseCode']}")


if __name__ == "__main__":    
    args = sys.argv[1:]
    batch_size = int(args[0])
    snow = connect_snow()
    batch = []
    temp_dir = tempfile.TemporaryDirectory()
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    host = os.getenv("SNOWFLAKE_ACCOUNT") + ".snowflakecomputing.com"
    ingest_manager = SimpleIngestManager(account=os.getenv("SNOWFLAKE_ACCOUNT"),
                                         host=host,
                                         user=os.getenv("SNOWFLAKE_USER"),
                                         pipe='INGEST.INGEST.LIFT_TICKETS_PIPE',
                                         private_key=private_key)
    for message in sys.stdin:
        if message != '\n':
            record = json.loads(message)
            batch.append((record['txid'],record['rfid'],record["resort"],record["purchase_time"],record["expiration_time"],record['days'],record['name'],record['address'],record['phone'],record['email'], record['emergency_contact']))
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir, ingest_manager)
                batch = []
        else:
            break    
    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir, ingest_manager)
    temp_dir.cleanup()
    snow.close()
    logging.info("Ingest complete")

```

Since this pattern is creating a file, uploading the file, and copying the results of that data it can VERY efficiently load large numbers of records. It is also only charging for the number of seconds of compute used by Snowpipe.

In order to test this insert, run the following:

```bash
python ./data_generator.py 1 | python py_snowpipe.py 1
```

Query the table to verify the data was inserted. You will probably see 0 records for up to a minute while Snowpipe ingests the file.

```sql
SELECT count(*) FROM LIFT_TICKETS_PY_SNOWPIPE;
```

To send in all your test data, you can run the following:
```bash
cat data.json.gz | zcat | python py_snowpipe.py 10000
```

This last call will batch together 10,000 records into each file for processing. As this file gets larger, up to 100mb, you will see this be more efficient on seconds of compute used in Snowpipe and see higher throughputs.

Test this approach with more test data and larger batch sizes. Review INFORMATION_SCHEMA PIPE_USAGE_HISTORY to see how efficient large batches are vs small batches.

### Tips

* Ingest is billed based on seconds of compute used by Snowpipe and number of files ingested.

* This is one of the most efficient and highest throughput ways to ingest data when batches are well sized.

* File size is a huge factor for cost efficiency and throughput. If you have files and batches much smaller than 100mb and cannot change them, this pattern should be avoided.

* Expect delays when Snowpipe has enqueued the request to ingest the data. This process is asynchronous. In most cases these patterns can deliver ~ minute ingest times when including the time to batch, upload, and copy but this varies based on your use case.

## File Upload & Copy (Serverless) from the Python Connector
Duration: 5

It can be useful to leverage a [Serverless Task](https://docs.snowflake.com/en/user-guide/tasks-intro) which is scheduled every minute to ingest the files uploaded by clients over the last minute.

This has several advantages over using Snowpipe for Copy:
* Eliminates the per file costs incurred by Snowpipe.
* Small files can be merged together more efficiently

It is also billed per second of compute so warehouse planning/optimization is not required.

Create the table and task needed for this ingest pattern:

```sql
USE ROLE ACCOUNTADMIN;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE INGEST;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE INGEST;

USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_PY_SERVERLESS (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);

CREATE OR REPLACE TASK LIFT_TICKETS_PY_SERVERLESS 
USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE='XSMALL' 
AS
COPY INTO LIFT_TICKETS_PY_SERVERLESS
FILE_FORMAT=(TYPE='PARQUET') 
MATCH_BY_COLUMN_NAME=CASE_SENSITIVE 
PURGE=TRUE;
```

Create a file names py_serverless.py with the following code:

```python
import os, sys, logging
import json
import uuid
import snowflake.connector
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

load_dotenv()
logging.basicConfig(level=logging.WARN)


def connect_snow():
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    p_key = serialization.load_pem_private_key(
        bytes(private_key, 'utf-8'),
        password=None
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role="INGEST",
        database="INGEST",
        schema="INGEST",
        warehouse="INGEST",
        session_parameters={'QUERY_TAG': 'py-serverless'}, 
    )


def save_to_snowflake(snow, batch, temp_dir):
    logging.debug('inserting batch to db')
    pandas_df = pd.DataFrame(batch, columns=["TXID","RFID","RESORT","PURCHASE_TIME", "EXPIRATION_TIME",
                                            "DAYS","NAME","ADDRESS","PHONE","EMAIL", "EMERGENCY_CONTACT"])
    arrow_table = pa.Table.from_pandas(pandas_df)
    out_path =  f"{temp_dir.name}/{str(uuid.uuid1())}.parquet"
    pq.write_table(arrow_table, out_path, use_dictionary=False,compression='SNAPPY')
    snow.cursor().execute("PUT 'file://{0}' @%LIFT_TICKETS_PY_SERVERLESS".format(out_path))
    os.unlink(out_path)
    # this will be skipped if the task is already scheduled, no warehouse will be used
    # when ran, the task will run as serverless
    snow.cursor().execute("EXECUTE TASK LIFT_TICKETS_PY_SERVERLESS")
    logging.debug(f"{len(batch)} tickets in stage")


if __name__ == "__main__":    
    args = sys.argv[1:]
    batch_size = int(args[0])
    snow = connect_snow()
    batch = []
    temp_dir = tempfile.TemporaryDirectory()
    for message in sys.stdin:
        if message != '\n':
            record = json.loads(message)
            batch.append((record['txid'],record['rfid'],record["resort"],record["purchase_time"],record["expiration_time"],
                        record['days'],record['name'],record['address'],record['phone'],record['email'], record['emergency_contact']))
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir)
                batch = []
        else:
            break    
    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir)
    temp_dir.cleanup()
    snow.close()
    logging.info("Ingest complete")
```

In order to test this insert, run the following:

```bash
python ./data_generator.py 1 | python py_serverless.py 1
```

Query the table to verify the data was inserted.

```sql
SELECT count(*) FROM LIFT_TICKETS_PY_SERVERLESS;
```

To send in all your test data, you can run the following:
```bash
cat data.json.gz | zcat | python py_serverless.py 10000
```

If you run multiple tests with different batch sizes (especially smaller sizes), you will see this can save credit consumption over the previous Snowpipe solution as it combines files into loads.

The code is calling execute task after each file is uploaded. While this may not seem optimimal, it is not running after each file is uploaded. It is leveraging a feature of tasks which does not allow additional tasks to be enqueued when one is already enqueued to run.

It is also common to schedule the task to run every n minutes instead of calling from the clients.

### Tips

* Only run the Task as needed when enough data (> 100mb) has been loaded into stage for most efficiency.

* Use Serverless Tasks to avoid per file charges and resolve small file inefficiencies.

## Inserting Data from a Dataframe with Snowpark
Duration: 5

If data is being processed by Snowpark (data is in a Dataframe) which needs to be inserted into Snowflake, we have built in capabilities to do so!

We will use write_pandas to append data into the destination table. It can also be used to overwrite tables.

First, create the table for the data to be written to.

```sql
USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_PY_SNOWPARK (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);
```

Create a file named py_snowpark.py with this code. This code will need to be modified if you changed your data generator.

```python
import os, sys, logging
import pandas as pd
import json

from snowflake.snowpark import Session
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization


load_dotenv()
logging.basicConfig(level=logging.WARN)


def connect_snow():
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    p_key = serialization.load_pem_private_key(
        bytes(private_key, 'utf-8'),
        password=None
    )
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    
    session = Session.builder.configs({"account":os.getenv("SNOWFLAKE_ACCOUNT"),
                                   "user":os.getenv("SNOWFLAKE_USER"),
                                   "private_key":pkb,
                                   "role":"INGEST",
                                   "database":"INGEST",
                                   "SCHEMA":"INGEST",
                                   "WAREHOUSE":"INGEST"}).create()
    df = session.sql("ALTER SESSION SET QUERY_TAG='py-snowpark'")
    df.collect()
    return session


def save_to_snowflake(snow, batch):
    logging.debug('inserting batch to db')
    pandas_df = pd.DataFrame(batch, columns=["TXID","RFID","RESORT","PURCHASE_TIME", "EXPIRATION_TIME",
                                            "DAYS","NAME","ADDRESS","PHONE","EMAIL", "EMERGENCY_CONTACT"])
    snow.write_pandas(pandas_df, "LIFT_TICKETS_PY_SNOWPARK", auto_create_table=False)
    logging.debug(f"inserted {len(batch)} tickets")


if __name__ == "__main__":    
    args = sys.argv[1:]
    batch_size = int(args[0])
    
    snow = connect_snow()
    batch = []
    for message in sys.stdin:
        if message != '\n':
            record = json.loads(message)
            batch.append((record['txid'],record['rfid'],record["resort"],record["purchase_time"],record["expiration_time"],
                        record['days'],record['name'],record['address'],record['phone'],record['email'], record['emergency_contact']))
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch)
                batch = []
        else:
            break
    if len(batch) > 0:
        save_to_snowflake(snow, batch)    
    snow.close()
    logging.info("Ingest complete")
    
```

The big change in this example is the usage of write_pandas. You can see the DataFrame being loaded as well as it directly appended to the table. In the connector, this data is being serialized to arrow, uploaded to Snowflake for efficient insert.

In order to test this insert, run the following:

```bash
python ./data_generator.py 1 | python py_snowpark.py 1
```

Query the table to verify the data was inserted.

```sql
SELECT count(*) FROM LIFT_TICKETS_PY_SNOWPARK;
```

To send in all your test data, you can run the following:
```bash
cat data.json.gz | zcat | python py_snowpark.py 10000
```

### Tips

* Ingest is billed based on warehouse credits consumed while online.

* Most efficient when batches get closer to 100mb.

* Great for when data has been processed using DataFrames.

## Kafka Setup and Data Publisher
Duration: 5

The following 2 ingest patterns will need Kafka. I will use Redpanda in this example, but you could also use Apache or Confluent Kafka as well as MSK from AWS and Event Hubs from Azure.

To start Kafka locally, create a file called docker-compose.yml with the following contents:

```yaml
version: "3.7"
name: redpanda
networks:
  redpanda_network:
    driver: bridge
volumes:
  redpanda-0: null
services:
  redpanda-0:
    command:
      - redpanda
      - start
      - --kafka-addr internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr internal://redpanda-0:9092,external://localhost:19092
      - --pandaproxy-addr internal://0.0.0.0:8082,external://0.0.0.0:18082
      - --advertise-pandaproxy-addr internal://redpanda-0:8082,external://localhost:18082
      - --schema-registry-addr internal://0.0.0.0:8081,external://0.0.0.0:18081
      - --rpc-addr redpanda-0:33145
      - --advertise-rpc-addr redpanda-0:33145
      - --smp 1
      - --memory 1G
      - --mode dev-container
      - --default-log-level=error
    image: docker.redpanda.com/redpandadata/redpanda:v23.1.3
    container_name: redpanda-0
    volumes:
      - redpanda-0:/var/lib/redpanda/data
    networks:
      - redpanda_network
    ports:
      - 18081:18081
      - 18082:18082
      - 19092:19092
      - 19644:9644  
  console:
    container_name: redpanda-console
    image: docker.redpanda.com/vectorized/console:v2.2.3
    networks:
      - redpanda_network
    entrypoint: /bin/sh
    command: -c 'echo "$$CONSOLE_CONFIG_FILE" > /tmp/config.yml; /app/console'
    environment: 
      CONFIG_FILEPATH: /tmp/config.yml
      CONSOLE_CONFIG_FILE: |
        kafka:
          brokers: ["redpanda-0:9092"]
          schemaRegistry:
            enabled: true
            urls: ["http://redpanda-0:8081"]
        redpanda:
          adminApi:
            enabled: true
            urls: ["http://redpanda-0:9644"]
        connect:
          enabled: true
          clusters:
            - name: local-connect-cluster
              url: http://connect:8083
    ports:
      - 8080:8080
    depends_on:
      - redpanda-0
  connect:
    image: docker.redpanda.com/redpandadata/connectors:1.0.0-dev-e81f871
    hostname: connect
    container_name: connect
    networks:
      - redpanda_network
    depends_on:
      - redpanda-0
    ports:
      - "8083:8083"
    environment:
      CONNECT_CONFIGURATION: |
          key.converter=org.apache.kafka.connect.converters.ByteArrayConverter
          value.converter=com.snowflake.kafka.connector.records.SnowflakeJsonConverter
          group.id=connectors-cluster
          offset.storage.topic=_internal_connectors_offsets
          config.storage.topic=_internal_connectors_configs
          status.storage.topic=_internal_connectors_status
          config.storage.replication.factor=-1
          offset.storage.replication.factor=-1
          status.storage.replication.factor=-1
          offset.flush.interval.ms=1000
          producer.linger.ms=50
          producer.batch.size=131072
      CONNECT_BOOTSTRAP_SERVERS: "redpanda-0:9092"
      CONNECT_GC_LOG_ENABLED: "false"
      CONNECT_HEAP_OPTS: -Xms512M -Xmx512M
      CONNECT_LOG_LEVEL: info

```

Start the containers:

```bash
docker compose up
```

After starting up, you will now have a local Kafka Broker at 127.0.0.1:19092 and the Redpanda Console at [http://localhost:8080/](http://localhost:8080/).

Add the broker information to your .env file.

```
SNOWFLAKE_ACCOUNT=<ACCOUNT_HERE>
SNOWFLAKE_USER=INGEST
PRIVATE_KEY=<PRIVATE_KEY_HERE>
REDPANDA_BROKERS=127.0.0.1:19092
```

The following code will used in following ingest patterns. It is a Python publisher to take data from standard input and write into the Kafka topic. Write this code to a file named publish_data.py

```python
import os
import logging
import sys
import confluent_kafka
from kafka.admin import KafkaAdminClient, NewTopic

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

kafka_brokers = os.getenv("REDPANDA_BROKERS")
topic_name = os.getenv("KAFKA_TOPIC")


def create_topic():
    admin_client = KafkaAdminClient(bootstrap_servers=kafka_brokers, client_id='publish_data')
    topic_metadata = admin_client.list_topics()
    if topic_name not in topic_metadata:
        topic = NewTopic(name=topic_name, num_partitions=10, replication_factor=1)
        admin_client.create_topics(new_topics=[topic], validate_only=False)


def get_kafka_producer():
    logging.info(f"Connecting to kafka")
    config = {'bootstrap.servers': kafka_brokers}
    return confluent_kafka.Producer(**config)


if __name__ == "__main__":  
    producer = get_kafka_producer()
    create_topic()
    for message in sys.stdin:
        if message != '\n':
            failed = True
            while failed:
                try:
                    producer.produce(topic_name, value=bytes(message, encoding='utf8'))
                    failed = False
                except BufferError as e:
                    producer.flush()
                
        else:
            break
    producer.flush()

```

To test the code, you can run the following:

```bash
export KAFKA_TOPIC=TESTING
python ./data_generator.py 1 | python ./publish_data.py
```

This should succeed by creating the topic and inserting the data. You can view the success in the [Redpanda console](http://localhost:8080).

## From Kafka - in Snowpipe (Batch) mode
Duration: 5

The table for the data to be written to will be automatically created by the connector.

Configure and install the connector to load data
```bash
export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_BATCH
eval $(cat .env)

URL="https://$SNOWFLAKE_ACCOUNT.snowflakecomputing.com"
NAME="LIFT_TICKETS_KAFKA_BATCH"

curl -i -X PUT -H "Content-Type:application/json" \
    "http://localhost:8083/connectors/$NAME/config" \
    -d '{
        "connector.class":"com.snowflake.kafka.connector.SnowflakeSinkConnector",
        "errors.log.enable":"true",
        "snowflake.database.name":"INGEST",
        "snowflake.private.key":"'$PRIVATE_KEY'",
        "snowflake.schema.name":"INGEST",
        "snowflake.role.name":"INGEST",
        "snowflake.url.name":"'$URL'",
        "snowflake.user.name":"'$SNOWFLAKE_USER'",
        "topics":"'$KAFKA_TOPIC'",
        "name":"'$NAME'",
        "buffer.size.bytes":"250000000",
        "buffer.flush.time":"60",
        "buffer.count.records":"1000000",
        "snowflake.topic2table.map":"'$KAFKA_TOPIC:$NAME'"
    }'
```

Verify the connector was created and is running in the Redpanda console.

To start, lets push in one message to get the table created and verify the connector is working.

```bash
export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_BATCH
python ./data_generator.py 1 | python ./publish_data.py
```

A table named LIFT_TICKETS_KAFKA_BATCH should be created in your account.

```sql
SELECT get_ddl('table', 'LIFT_TICKETS_KAFKA_BATCH');
```

There should be 1 row of data which was created by the data_generator. Note: This can take a minute or so to the flush times in configuration.

```sql
SELECT count(*) FROM LIFT_TICKETS_KAFKA_BATCH;
```

After this is verified to be successful, send in all your test data:

```bash
export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_BATCH
cat data.json.gz | zcat | python ./publish_data.py
```

### Tips

* Every partition will flush to a file when the bytes, time, or records is hit. This can create a LOT of tiny files if not configured well which will be inefficient.

* Not all workloads can accommodate quick flush times. The more data that is flowing, the quicker data can be visible while being efficient.

* Reducing the number of partitions and increasing the bytes, time, records to get to well sized files is valuable for efficiency.

* If you don't have time or a use case to get to well sized files, move to streaming which will match or be better in all cases.

* Number of tasks, number of nodes in the Kafka Connect cluster, amount of CPU and memory on those nodes, and number of partitions will affect performance and credit consumption.

* Kafka Connector for Snowflake is billed by the second of compute needed to ingest files (Snowpipe).

## From Kafka - in Snowpipe Streaming mode
Duration: 5

Configure and install a new connector to load data in streaming mode:
```bash
export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_STREAMING
eval $(cat .env)

URL="https://$SNOWFLAKE_ACCOUNT.snowflakecomputing.com"
NAME="LIFT_TICKETS_KAFKA_STREAMING"

curl -i -X PUT -H "Content-Type:application/json" \
    "http://localhost:8083/connectors/$NAME/config" \
    -d '{
        "connector.class":"com.snowflake.kafka.connector.SnowflakeSinkConnector",
        "errors.log.enable":"true",
        "snowflake.database.name":"INGEST",
        "snowflake.private.key":"'$PRIVATE_KEY'",
        "snowflake.schema.name":"INGEST",
        "snowflake.role.name":"INGEST",
        "snowflake.url.name":"'$URL'",
        "snowflake.user.name":"'$SNOWFLAKE_USER'",
        "snowflake.enable.schematization": "FALSE",
        "snowflake.ingestion.method": "SNOWPIPE_STREAMING",
        "topics":"'$KAFKA_TOPIC'",
        "name":"'$NAME'",
        "value.converter":"org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable":"false",
        "buffer.count.records":"1000000",
        "buffer.flush.time":"10",
        "buffer.size.bytes":"250000000",
        "snowflake.topic2table.map":"'$KAFKA_TOPIC:LIFT_TICKETS_KAFKA_STREAMING'"
    }'
```

Verify the connector was created and is running in the Redpanda console.

This configuration will allow data flowing through the connector to flush much quicker. The flush time is set to 10 seconds. Previously, it was often discussed how important file sizes were. That was because the files were directly impacting the efficient use of a warehouse. Streaming removes this complexity completely.

Data can be loaded in small pieces and will be merged together in the background efficiently by Snowflake. What is even better is that data is immediately available to query before it's merged. All use cases tested have shown Streaming to be as or MORE efficient than the previous Snowpipe only configuration.

To send in all your test data, you can run the following:
```bash
export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_STREAMING
cat data.json.gz | zcat | python ./publish_data.py
```

Query the table to verify the data was inserted. Data will appear in the table in seconds!
```sql
SELECT count(*) FROM LIFT_TICKETS_KAFKA_STREAMING;
```

### Tips

* Kafka Connector for Snowflake in Streaming mode is billed by the second of compute needed to merge files as well as the clients connected.

* Setting the flush time lower can/will affect query performance as merge happens asynchronously.

* Number of tasks, number of nodes in the Kafka Connect cluster, amount of CPU and memory on those nodes, and number of partitions will affect performance and credit consumption.

* Streaming is the best ingest pattern when using Kafka.

## From Java SDK - Using the Snowflake Ingest Service
Duration: 10

Many developers want to be able to directly stream data into Snowflake (without Kafka). In order to do so, Snowflake has a Java SDK.

First, create a table for data to be insert into:
```sql
USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_JAVA_STREAMING (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);
```

The easiest way to get the sdk working is to use maven for all the dependencies.

Create a file pom.xml with the following contents
```xml
<?xml version="1.0" encoding="UTF-8"?>

<project xmlns="http://maven.apache.org/POM/4.0.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>com.snowflake.streaming.app</groupId>
  <artifactId>java-streaming</artifactId>
  <version>1.0-SNAPSHOT</version>

  <name>java-streaming</name>
  <!-- FIXME change it to the project's website -->
  <url>http://www.example.com</url>

  <properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.source>1.8</maven.compiler.source>
    <maven.compiler.target>1.8</maven.compiler.target>
  </properties>

  <dependencies>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13.1</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>net.snowflake</groupId>
      <artifactId>snowflake-ingest-sdk</artifactId>
      <version>1.1.3</version>
    </dependency>
    <dependency>
      <groupId>io.github.cdimascio</groupId>
      <artifactId>dotenv-java</artifactId>
      <version>2.3.2</version>
    </dependency>
    <dependency>
      <groupId>net.snowflake</groupId>
      <artifactId>snowflake-jdbc</artifactId>
      <version>3.13.30</version>
    </dependency>

    <!-- String collation-->
    <dependency>
      <groupId>com.ibm.icu</groupId>
      <artifactId>icu4j</artifactId>
      <version>70.1</version>
    </dependency>

    <!-- jwt token for key pair authentication with GS -->
    <dependency>
      <groupId>com.nimbusds</groupId>
      <artifactId>nimbus-jose-jwt</artifactId>
      <version>9.9.3</version>
    </dependency>

    <!-- Jackson for marshalling and unmarshalling JSON -->
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-core</artifactId>
      <version>2.13.1</version>
    </dependency>

    <!-- Jackson Databind api -->
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>2.15.0</version>
    </dependency>

    <!-- Apache HTTP Components for actually sending requests over the network -->
    <dependency>
      <groupId>org.apache.httpcomponents</groupId>
      <artifactId>httpclient</artifactId>
      <version>4.5.13</version>
      <exclusions>
        <exclusion>  <!-- declare the exclusion here -->
          <groupId>commons-codec</groupId>
          <artifactId>commons-codec</artifactId>
        </exclusion>
      </exclusions>
    </dependency>

    <dependency>
      <groupId>commons-codec</groupId>
      <artifactId>commons-codec</artifactId>
      <version>1.15</version>
    </dependency>


    <!-- the Async HTTP Client so we can delay execution -->
    <dependency>
      <groupId>org.apache.httpcomponents</groupId>
      <artifactId>httpasyncclient</artifactId>
      <version>4.1.2</version>
    </dependency>


    <!-- SLF4J api that a client can shim in later -->
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>1.7.21</version>
      <scope>provided</scope>
    </dependency>


    <!-- JDK logger backend for logging tests -->
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-simple</artifactId>
      <version>1.7.21</version>
      <scope>test</scope>
    </dependency>

    <!-- java.lang.NoClassDefFoundError: javax/xml/bind/JAXBException -->
    <!-- https://stackoverflow.com/questions/43574426/how-to-resolve-java
        -lang-noclassdeffounderror-javax-xml-bind-jaxbexception-in-j/48404582-->
    <dependency>
      <groupId>javax.xml.bind</groupId>
      <artifactId>jaxb-api</artifactId>
      <version>2.3.1</version>
    </dependency>


    <!-- JUnit so that we can make some basic unit tests -->
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13.1</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.powermock</groupId>
      <artifactId>powermock-module-junit4</artifactId>
      <version>2.0.2</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.mockito</groupId>
      <artifactId>mockito-core</artifactId>
      <version>3.7.7</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.powermock</groupId>
      <artifactId>powermock-api-mockito2</artifactId>
      <version>2.0.2</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.powermock</groupId>
      <artifactId>powermock-core</artifactId>
      <version>2.0.2</version>
      <scope>test</scope>
    </dependency>

    <!-- Apache Arrow -->
    <dependency>
      <groupId>org.apache.arrow</groupId>
      <artifactId>arrow-vector</artifactId>
      <version>8.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.apache.arrow</groupId>
      <artifactId>arrow-memory-netty</artifactId>
      <version>8.0.0</version>
      <scope>runtime</scope>
    </dependency>

    <!-- https://mvnrepository.com/artifact/io.dropwizard.metrics/metrics-core -->
    <dependency>
      <groupId>io.dropwizard.metrics</groupId>
      <artifactId>metrics-core</artifactId>
      <version>4.1.22</version>
    </dependency>

    <!-- https://mvnrepository.com/artifact/io.dropwizard.metrics/metrics-jvm -->
    <dependency>
      <groupId>io.dropwizard.metrics</groupId>
      <artifactId>metrics-jvm</artifactId>
      <version>4.1.22</version>
    </dependency>

    <!-- https://mvnrepository.com/artifact/io.dropwizard.metrics/metrics-jmx -->
    <dependency>
      <groupId>io.dropwizard.metrics</groupId>
      <artifactId>metrics-jmx</artifactId>
      <version>4.2.3</version>
    </dependency>
  </dependencies>

  <build>
    <pluginManagement><!-- lock down plugins versions to avoid using Maven defaults (may be moved to
      parent pom) -->
      <plugins>
        <!-- clean lifecycle, see
        https://maven.apache.org/ref/current/maven-core/lifecycles.html#clean_Lifecycle -->
        <plugin>
          <artifactId>maven-clean-plugin</artifactId>
          <version>3.1.0</version>
        </plugin>
        <!-- default lifecycle, jar packaging: see
        https://maven.apache.org/ref/current/maven-core/default-bindings.html#Plugin_bindings_for_jar_packaging -->
        <plugin>
          <artifactId>maven-resources-plugin</artifactId>
          <version>3.0.2</version>
        </plugin>
        <plugin>
          <artifactId>maven-compiler-plugin</artifactId>
          <version>3.8.0</version>
        </plugin>
        <plugin>
          <artifactId>maven-surefire-plugin</artifactId>
          <version>2.22.1</version>
        </plugin>
        <plugin>
          <artifactId>maven-jar-plugin</artifactId>
          <version>3.0.2</version>
        </plugin>
        <plugin>
          <artifactId>maven-install-plugin</artifactId>
          <version>2.5.2</version>
        </plugin>
        <plugin>
          <artifactId>maven-deploy-plugin</artifactId>
          <version>2.8.2</version>
        </plugin>
        <!-- site lifecycle, see
        https://maven.apache.org/ref/current/maven-core/lifecycles.html#site_Lifecycle -->
        <plugin>
          <artifactId>maven-site-plugin</artifactId>
          <version>3.7.1</version>
        </plugin>
        <plugin>
          <artifactId>maven-project-info-reports-plugin</artifactId>
          <version>3.0.0</version>
        </plugin>
        <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-dependency-plugin</artifactId>
          <version>3.5.0</version>
          <executions>
            <execution>
              <id>copy-dependencies</id>
              <phase>package</phase>
              <goals>
                <goal>copy-dependencies</goal>
              </goals>
              <configuration>
                <outputDirectory>${project.build.directory}/alternateLocation</outputDirectory>
                <overWriteReleases>false</overWriteReleases>
                <overWriteSnapshots>false</overWriteSnapshots>
                <overWriteIfNewer>true</overWriteIfNewer>
              </configuration>
            </execution>
          </executions>
        </plugin>
      </plugins>
    </pluginManagement>
  </build>
</project>
```

Create a directory structure src/main/java/com/snowflake/streaming/app inside your project directory and create a file called App.java inside the app directory.

Add the following code to App.java. This code will take the records from standard in like previous patterns and stream the data to Snowflake.

```java
package com.snowflake.streaming.app;

import java.io.*;
import java.util.Map;
import java.util.Properties;

import io.github.cdimascio.dotenv.Dotenv;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import net.snowflake.ingest.streaming.InsertValidationResponse;
import net.snowflake.ingest.streaming.SnowflakeStreamingIngestChannel;
import net.snowflake.ingest.streaming.SnowflakeStreamingIngestClient;
import net.snowflake.ingest.streaming.SnowflakeStreamingIngestClientFactory;
import net.snowflake.ingest.streaming.OpenChannelRequest;

public class App {
    private static final Logger LOGGER = LoggerFactory.getLogger(App.class.getName());

    public static void main(String[] args) throws Exception {
        Dotenv dotenv = Dotenv.configure().load();
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        Properties props = new Properties();
        props.put("user", dotenv.get("SNOWFLAKE_USER"));
        props.put("url", "https://" + dotenv.get("SNOWFLAKE_ACCOUNT") + ".snowflakecomputing.com:443");
        props.put("private_key", dotenv.get("PRIVATE_KEY"));
        props.put("role", "INGEST");

        try (SnowflakeStreamingIngestClient client = SnowflakeStreamingIngestClientFactory.builder("MY_CLIENT")
                .setProperties(props).build()) {
            OpenChannelRequest request1 = OpenChannelRequest.builder("MY_CHANNEL")
                    .setDBName("INGEST")
                    .setSchemaName("INGEST")
                    .setTableName("LIFT_TICKETS_JAVA_STREAMING")
                    .setOnErrorOption(
                            OpenChannelRequest.OnErrorOption.ABORT)
                    .build();

            SnowflakeStreamingIngestChannel channel1 = client.openChannel(request1);
            String line = br.readLine();
            int val = 0;
            while (line != null && line.length() > 0) {
                ObjectMapper mapper = new ObjectMapper();
                Map<String, Object> map = mapper.readValue(line, Map.class);

                InsertValidationResponse response = channel1.insertRow(map, String.valueOf(val));
                if (response.hasErrors()) {
                    System.out.println(response.getInsertErrors().get(0).getException());
                }

                line = br.readLine();
                val++;
            }
            LOGGER.info("Ingest complete");
            channel1.close().get();
        }
    }
}
```

To build and test this code run the following:
```bash
mvn install
mvn dependency:copy-dependencies
mvn package

python ./data_generator.py 1 | java -cp "target/java-streaming-1.0-SNAPSHOT.jar:target/dependency/*" -Dorg.slf4j.simpleLogger.defaultLogLevel=error com.snowflake.streaming.app.App
```

Query the table to verify the data was inserted. Data will appear in the table in seconds!

```sql
SELECT count(*) FROM LIFT_TICKETS_JAVA_STREAMING;
```

To send in all your test data, you can run the following:
```bash
cat data.json.gz | zcat | java -cp "target/java-streaming-1.0-SNAPSHOT.jar:target/dependency/*" -Dorg.slf4j.simpleLogger.defaultLogLevel=error com.snowflake.streaming.app.App
```

```sql
SELECT count(*) FROM LIFT_TICKETS_JAVA_STREAMING;
```

### Tips

* Ingest with streaming is billed by the second of compute needed to merge files as well as the clients connected.

* Number of nodes/threads running the Java SDK will affect performance and credit consumption

* Best ingest pattern when not using Kafka and are processing streaming data

## Cleanup
Duration: 1

In order to cleanup from all the ingest patterns built, you can drop the USER, ROLE, DATABASE, and WAREHOUSE:

```sql
USE ROLE ACCOUNTADMIN;
DROP USER INGEST;
DROP DATABASE INGEST;
DROP WAREHOUSE INGEST;
DROP ROLE INGEST;
```

Tear down docker

```bash
docker compose down
```

Delete conda env

```bash
conda deactivate
conda remove -n sf-ingest-examples --all
```

## Conclusion & Next Steps
Duration: 1

As you've seen, there are many ways to load data into Snowflake. It is important to understand the benefits and consequenses so you can make the right choice when ingesting data into Snowflake. 

While some examples only focussed on the Python connector, these patterns are often applicable to our other connectors if your language of choice is not Python. Connectors are available for Python, Java, Node.js, Go, .NET, and PHP.

I hope you see based on the load times, that batch size worth tuning.

Serverless Tasks, Snowpipe, and Streaming are all built on Snowflake's serverless compute which make it much simpler to have efficient utilization of infrastructure. Managing warehouses and keeping them fully loaded is not easy or even possible in many cases.

If you're using the Kafka connector for Snowflake, put it in Streaming mode. It will either be the same or less credit consumption AND make the data available more quickly.

When well-sized batches are not possible, leveraging our Streaming ingest will significantly increase efficiency. We will merge those tiny batches together in Snowflake later in a very efficient workflow while making that data available for query quickly.


### What We've Covered
- How to Ingest data with Connectors
- Using Serverless Tasks and Snowpipe to save credit consumption
- How to Use the Kafka Connectors for Snowflake
- How Streaming reduces the time to Ingest AND Increases Efficiency

### Related Resources
- [Snowflake Connector for Python](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [Java SDK for the Snowflake Ingest Service](https://github.com/snowflakedb/snowflake-ingest-java)
- [Python Snowflake Ingest Service SDK](https://github.com/snowflakedb/snowflake-ingest-python)
- [Getting Started with Snowpipe](https://quickstarts.snowflake.com/guide/getting_started_with_snowpipe/index.html)
- [Getting Started with Snowpipe Streaming and Amazon MSK](https://quickstarts.snowflake.com/guide/getting_started_with_snowpipe_streaming_aws_msk/index.html)
- [Streaming Data Integration with Snowflake](https://quickstarts.snowflake.com/guide/data_engineering_streaming_integration/index.html)




id: getting_started_with_snowflake_and_aws_kdf
summary: This guide will walk you through how to apply a data-intensive approach to real-time data using Snowpipe Streaming and Amazon Kinesis Data Firehose (KDF).
categories: getting-started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Kinesis, Firehose, Streaming, Snowpipe Streaming, SnowSQL
authors: James Sun

# Getting Started with Snowflake and Amazon Kinesis Data Firehose
<!---------------------------->
## Overview
Duration: 5

Snowflake's Snowpipe streaming capabilities are designed for rowsets with variable arrival frequency.
It focuses on lower latency and cost for smaller data sets. This helps data workers stream rows into Snowflake
without requiring files with a more attractive cost/latency profile.

Here are some of the use cases that can benefit from this integration:
- IoT time-series data ingestion
- CDC streams from OLTP systems 
- Log ingestion from SIEM systems
- Ingestion into ML feature stores 

In our demo, we will use real-time commercial flight data over the San Francisco Bay Area from the [Opensky Network](https://opensky-network.org) to illustrate the solution leveraging
the [native integration](https://aws.amazon.com/about-aws/whats-new/2024/01/stream-data-snowflake-kinesis-data-firehose-snowpipe-streaming-preview/) between Snowflake and [KDF (Amazon Kinesis Data Firehose)](https://aws.amazon.com/kinesis/data-firehose/).

The architecture diagram below shows the deployment. A Linux 
EC2 instance (jumphost) will be provisioned in the subnet of an AWS VPC. 
The Linux jumphost will host the Kinesis producer that ingests real-time flight data into the Kinesis delivery stream.

The Kinesis producer calls the data sources' REST API and receives time-series data in JSON format. This data is then ingested into the Kinesis delivery stream and delivered to a Snowflake table.
The data in Snowflake table can be visualized in real-time with [AMG (Amazon Managed Grafana)](https://aws.amazon.com/grafana/) and [Streamlit](https://streamlit.io)
The historical data can also be analyzed by BI tools like [Amazon Quicksight](https://aws.amazon.com/quicksight/?trk=56601b48-df3f-4cb4-9ef7-9f52efa1d0b8&sc_channel=ps&ef_id=Cj0KCQiA_bieBhDSARIsADU4zLebWWM6ZmxRODjR9Xlc7ztNm5JGwqEMSi0EjCLZ9CXYa1YvXL3LMYYaAnV_EALw_wcB:G:s&s_kwcid=AL!4422!3!629393324770!!!g!!).
Please note that in the demo, we are not demonstrating the visualization aspect. We will have a future Quickstart demo that focuses on visualization.

![Architecture diagram for the Demo](assets/Overview-2-flight-arch.png)

![Data visualization](assets/Overview-2-dashboarding.png)

### Prerequisites

- Familiarity with Snowflake, basic SQL knowledge, Snowsight UI and Snowflake objects
- Familiarity with AWS Services (e.g. EC2, MSK, etc), Networking and the Management Console
- Basic knowledge of Python and Linux shell scripting

### What You'll Need Before the Lab

To participate in the virtual hands-on lab, attendees need the following resources.

- A [Snowflake Enterprise Account on preferred AWS region](https://signup.snowflake.com/) with `ACCOUNTADMIN` access
- An [AWS Account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) with `Administrator Access`
- Create your own VPC and subnets (This is optional if you have an existing VPC with subnets you can leverage. Please refer
to this [AWS document](https://docs.aws.amazon.com/whitepapers/latest/amazon-msk-migration-guide/amazon-managed-streaming-for-apache-kafka-amazon-msk.html) for the MSK networking topology)
  - In the AWS account, [create a VPC](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-vpcs.html), preferrably in the same region as the Snowflake account
  - In the VPC, [create subnets](https://docs.aws.amazon.com/vpc/latest/userguide/working-with-subnets.html) and attach an [internet gateway](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html) to allow egress traffic to the internet by using a routing table and security group for outbound traffic.
  Note that the subnets can be public or private, for private subnets, you will need to attach a [NAT gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) to allow egress traffic to the internet. Public subnets are sufficient for this lab.
  - If you have decided to create your own VPC/subnets, for your convenience, click [here](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=MSK-Snowflake-VPC&templateURL=https://snowflake-corp-se-workshop.s3.us-west-1.amazonaws.com/VHOL_Snowflake_Snowpipe_Streaming_MSK/MyFullVPC-2pub-2priv.json) to deploy a VPC with a pair of public and private subnets, internet gateway and NAT gateway for you. 
Note that you must have network administrator permissions to deploy these resources. 

### What You'll Learn

- Using [KDF (Amazon Kinesis Data Firehose)](https://aws.amazon.com/kinesis/data-firehose/)
- Connecting to EC2 instances with [Amazon System Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html), this is an alternative
to SSH if your instance is in a private subnet
- Using [SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql.html), the command line client for connecting to Snowflake to execute SQL queries and perform all DDL and DML operations, including loading data into and unloading data out of database tables.
- Using Snowflake to query tables populated with time-series data

### What You'll Build

- [Create a KDF delivery stream](https://docs.aws.amazon.com/firehose/latest/dev/basic-create.html)
- Setup `Direct Put` as the source for the KDF delivery stream
- Setup `Snowflake` as the destination for the KDF delivery stream
- Secure the connection between Snowflake and KDF with [Privatlink](https://aws.amazon.com/privatelink)
- A Snowflake database and table for hosting real-time flight data

<!---------------------------->
## Provision a Linux jumphost in AWS
Duration: 30

#### 1. Create an EC2 instance
First, click [here](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=KDF-Snowflake&templateURL=https://jsnow-us-west-2.s3.us-west-2.amazonaws.com/kdf/kdf-bastion.json)
to launch an EC2 instance(jumphost). Note the default AWS region is `us-west-2 (Oregon)`, at the time of writing this quickstart, three regions are available
for this integration preview: `us-east-1`, `us-west-2`, and `eu-west-1`.

For `Subnet1`, in the drop-down menu, pick an existing subnet, it can be either public or private subnets depending on the network layout of your VPC. 
For `InstanceSecurityGroupId`, we recommend using the default security group in your VPC, if you do not have the default security group, create one on your own before moving forward.

Click Next at the Create stack page. Set the Stack name or modify the default value to customize it to your identity.

See below sample screen capture for reference.

![](assets/ec2-cft-stack-1.png)

Leave everything as default in the `Configure stack options` page and click `Next`.
In the `Review` page, click `Submit`.

In about 5 minutes, the Cloudformation template provisions a Linux EC2 instance in the subnet you selected. We will then use it to run the Kinesis producer for data ingestion.

#### 2. Configure the Linux session for timeout and default shell

In this step we need to connect to the EC2 instance in order to interact with the MSK cluster.

Go to the AWS [Systems Manager](https://us-west-2.console.aws.amazon.com/systems-manager/home) console in the same region where you setup the MSK cluster,
Click `Session Manager` on the left pane.

![](assets/session-mgr-1.png)

Next, we will set the preferred shell as bash.

Click the `Preferences` tab.
![](assets/session-mgr-1.0.png)

Click the `Edit` button.
![](assets/session-mgr-1.1.png)

Go to `General preferences` section, type in 60 minutes for idle session timeout value.

![](assets/session-mgr-1.1.5.png)

Further scroll down to `Linux shell profile` section, and type in `/bin/bash` before clicking `Save` button.

![](assets/session-mgr-1.2.png)


#### 3. Connect to the Linux EC2 instance console
Now go back to the `Session` tab and click the `Start session` button.
![](assets/session-mgr-2.png)

Now you should see the EC2 instance created by the Cloudformation template under `Target instances`.
Its name should be `<Cloudformation stack name>-jumphost`, select it and click `Start session`.

![](assets/session-mgr-3.png)

#### 4. Create a key-pair to be used for authenticating with Snowflake
Create a key pair in AWS Session Manager console by executing the following commands. You will be prompted to give an encryption password, remember 
this phrase, you will need it later.

```commandline
cd $HOME
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8
```
See below example screenshot:

![](assets/key-pair-sessionmgr-1.png)

Next we will create a public key by running following commands. You will be prompted to type in the phrase you used in above step.
```
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```
see below example screenshot:

![](assets/key-pair-sessionmgr-2.png)

Next we will print out the public and private key string in a correct format that we can use for configuration later.
```
grep -v KEY rsa_key.pub | tr -d '\n' | awk '{print $1}' > pub.Key
cat pub.Key

grep -v KEY rsa_key.p8 | tr -d '\n' | awk '{print $1}' > priv.Key
cat priv.Key
```
see below example screenshot:

![](assets/key-pair-sessionmgr-3.png)

<!---------------------------->
## Prepare the Snowflake cluster for streaming
Duration: 10

#### 1. Creating user, role, and database
First login to your Snowflake account as a power user with ACCOUNTADMIN role. 
Then run the following SQL commands in a worksheet to create a user, database and the role that we will use in the lab.

```
-- Set default value for multiple variables
-- For purpose of this workshop, it is recommended to use these defaults during the exercise to avoid errors
-- You should change them after the workshop
SET PWD = 'Test1234567';
SET USER = 'STREAMING_USER';
SET DB = 'KDF_STREAMING_DB';
SET WH = 'KDF_STREAMING_WH';
SET ROLE = 'KDF_STREAMING_RL';

USE ROLE ACCOUNTADMIN;

-- CREATE USERS
CREATE USER IF NOT EXISTS IDENTIFIER($USER) PASSWORD=$PWD  COMMENT='STREAMING USER';

-- CREATE ROLES
CREATE OR REPLACE ROLE IDENTIFIER($ROLE);

-- CREATE DATABASE AND WAREHOUSE
CREATE DATABASE IF NOT EXISTS IDENTIFIER($DB);
USE IDENTIFIER($DB);
CREATE OR REPLACE WAREHOUSE IDENTIFIER($WH) WITH WAREHOUSE_SIZE = 'SMALL';

-- GRANTS
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE IDENTIFIER($ROLE);
GRANT ROLE IDENTIFIER($ROLE) TO USER IDENTIFIER($USER);
GRANT OWNERSHIP ON DATABASE IDENTIFIER($DB) TO ROLE IDENTIFIER($ROLE);
GRANT USAGE ON WAREHOUSE IDENTIFIER($WH) TO ROLE IDENTIFIER($ROLE);

-- SET DEFAULTS
ALTER USER IDENTIFIER($USER) SET DEFAULT_ROLE=$ROLE;
ALTER USER IDENTIFIER($USER) SET DEFAULT_WAREHOUSE=$WH;

-- RUN FOLLOWING COMMANDS TO FIND YOUR ACCOUNT IDENTIFIER, COPY IT DOWN FOR USE LATER
-- IT WILL BE SOMETHING LIKE <organization_name>-<account_name>
-- e.g. ykmxgak-wyb52636

WITH HOSTLIST AS 
(SELECT * FROM TABLE(FLATTEN(INPUT => PARSE_JSON(SYSTEM$allowlist()))))
SELECT REPLACE(VALUE:host,'.snowflakecomputing.com','') AS ACCOUNT_IDENTIFIER
FROM HOSTLIST
WHERE VALUE:type = 'SNOWFLAKE_DEPLOYMENT_REGIONLESS';
```

Please write down the Account Identifier, we will need it later.
![](assets/account-identifier.png)

Next we need to configure the public key for the streaming user to access Snowflake programmatically.

First, in the Snowflake worksheet, replace `<pubKey>` with the content of the file `/home/ssm-user/pub.Key` (see `step 4` by clicking on `section #2 Create a provisioned Kafka cluster and a Linux jumphost in AWS` in the left pane) in the following SQL command and execute.
```commandline
use role accountadmin;
alter user streaming_user set rsa_public_key='<pubKey>';
```
See below example screenshot:

![](assets/key-pair-snowflake.png)

Now logout of Snowflake, sign back in as the default user `streaming_user` we just created with the associated password (default: Test1234567).
Run the following SQL commands in a worksheet to create a schema (e.g. `MSK_STREAMING_SCHEMA`) in the default database (e.g. `MSK_STREAMING_DB`):

```commandline
SET DB = 'KDF_STREAMING_DB';
SET SCHEMA = 'KDF_STREAMING_SCHEMA';

USE IDENTIFIER($DB);
CREATE OR REPLACE SCHEMA IDENTIFIER($SCHEMA);
```

#### 2. Install SnowSQL (optional but highly recommended)

[SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql.html) is the command line client for connecting to Snowflake to execute SQL queries and perform all DDL and DML operations, including loading data into and unloading data out of database tables.

To install SnowSQL. Execute the following commands on the Linux Session Manager console:
```commandline
curl https://sfc-repo.snowflakecomputing.com/snowsql/bootstrap/1.2/linux_x86_64/snowsql-1.2.24-linux_x86_64.bash -o /tmp/snowsql-1.2.24-linux_x86_64.bash
echo -e "~/bin \n y" > /tmp/ans
bash /tmp/snowsql-1.2.24-linux_x86_64.bash < /tmp/ans

```
See below example screenshot:

![](assets/install-snowsql.png)

Next set the environment variable for Snowflake Private Key Phrase:
```commandline
export SNOWSQL_PRIVATE_KEY_PASSPHRASE=<key phrase you set up when running openssl previously>
```
Note that you should add the command above in the ~/.bashrc file to preserve this environment variable across sessions.
```commandline
echo "export SNOWSQL_PRIVATE_KEY_PASSPHRASE=$SNOWSQL_PRIVATE_KEY_PASSPHRASE" >> ~/.bashrc
```

Now you can execute this command to interact with Snowflake:
```commandline
$HOME/bin/snowsql -a <The Account Identifier that you recorded earlier> -u streaming_user --private-key-path $HOME/rsa_key.p8 -d msk_streaming_db -s msk_streaming_schema
```
See below example screenshot:

![](assets/key-pair-snowsql.png)

Type `Ctrl-D` to get out of SnowSQL session.

You can edit the [`~/.snowsql/config`](https://docs.snowflake.com/en/user-guide/snowsql-config.html#snowsql-config-file) file to set default parameters and eliminate the need to specify them every time you run snowsql.

At this point, the Snowflake setup is complete.

<!---------------------------->
## Create a KDF delivery stream
Duration: 10

In this step, we are going to create a KDF delivery stream for data streaming.

Navigate to the [KDF console](https://console.aws.amazon.com/firehose/home?streams) and click `Create delivery stream`.

In the `Source` section, select `Direct PUT` from the drop-down menu.

In the `Destination` section, select `Snowflake` from the drop-down menu.

Type in a name for the delivery stream.

![](assets/kdf-stream-1.png)

For `Snowflake account URL`, run this SQL command in your Snowflake account to obtain the value:
```
with PL as
(SELECT * FROM TABLE(FLATTEN(INPUT => PARSE_JSON(SYSTEM$GET_PRIVATELINK_CONFIG()))) where key = 'privatelink-account-url')
SELECT concat('https://'|| REPLACE(VALUE,'"','')) AS PRIVATE_LINK_VPCE_ID
from PL;
```
Note that we are going to use Amazon PrivateLink to secure the communication between Snowflake and KDF, so the
URL is a private endpoint with `privatelink` as a substring.

e.g. `https://xyz12345.us-west-2.privatelink.snowflakecomputing.com`

For `User`, type in `STREAMING_USER`.

For `Private key`, go back to your EC2 console in Systems Manager and run
```commandline
cat ~/priv.key
```
Copy the output string and paste into the `Private key` field.

For `Passphrase`, type in the phrase you used when generating the public key with openssl earlier.

![](assets/kdf-stream-2.png)

For `Role`, select `Use custom Snowflake role` and type in `KDF_STREAMING_RL`.

For `VPCE ID`, run the following SQL command in your Snowflake account to obtain the value.
```commandline
with PL as
(SELECT * FROM TABLE(FLATTEN(INPUT => PARSE_JSON(SYSTEM$GET_PRIVATELINK_CONFIG()))) where key = 'privatelink-vpce-id')
SELECT REPLACE(VALUE,'"','') AS PRIVATE_LINK_VPCE_ID
from PL;
```

For `Snowflake database`, type in `KDF_STREAMING_DB`.

For `Snowflake Schema`, type in `KDF_STREAMING_SCHEMA`.

For `Snowflake table`, type in `KDF_STREAMING_TBL`.

For `Data loading options for your Snowflake table`, select `Use JSON keys as table column names`.

![](assets/kdf-stream-3.png)

For `S3 backup bucket`, pick an existing S3 bucket where you want to save the logs or error messages. [Create a S3 bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html) if you don't have one.

![](assets/kdf-stream-4.png)

Leave everything else as default and click `Create delivery stream`.

Your delivery stream will be generated in about 5 minutes.

<!---------------------------->
## Query ingested data in Snowflake
Duration: 10

Now, switch back to the Snowflake console and make sure that you signed in as the default user `streaming_user`. 
The data should have been streamed into a table, ready for further processing.

#### 1. Query the raw data
To verify that data has been streamed into Snowflake, execute the following SQL commands.

```sh
use msk_streaming_db;
use schema msk_streaming_schema;
show channels in table msk_streaming_tbl;
```
You should see that there are two channels, corresponding to the two partitions created earlier in the topic.
![](assets/channels.png)

Now run the following query on the table.
```
select * from msk_streaming_tbl;
```
You should see there are two columns in the table: `RECORD_METADATA` and `RECORD_CONTENT` as shown in the screen capture below.

![](assets/raw_data.png)
The `RECORD_CONTENT` column is an JSON array that needs to be flattened.

#### 2. Flatten the raw JSON data
Now execute the following SQL commands to flatten the raw JSONs and create a materialized view with multiple columns based on the key names.

```sh
create or replace view flights_vw
  as select
    f.value:utc::timestamp_ntz ts_utc,
    CONVERT_TIMEZONE('UTC','America/Los_Angeles',ts_utc::timestamp_ntz) as ts_pt,
    f.value:alt::integer alt,
    f.value:dest::string dest,
    f.value:orig::string orig,
    f.value:id::string id,
    f.value:icao::string icao,
    f.value:lat::float lat,
    f.value:lon::float lon,
    st_geohash(to_geography(ST_MAKEPOINT(lon, lat)),12) geohash,
    year(ts_pt) yr,
    month(ts_pt) mo,
    day(ts_pt) dd,
    hour(ts_pt) hr
FROM   msk_streaming_tbl,
       Table(Flatten(msk_streaming_tbl.record_content)) f;
```

The SQL commands create a view, convert timestamps to different time zones, and use Snowflake's [Geohash function](https://docs.snowflake.com/en/sql-reference/functions/st_geohash.html)  to generate geohashes that can be used in time-series visualization tools like Grafana

Let's query the view `flights_vw` now.
```sh
select * from flights_vw;
```

As a result, you will see a nicely structured output with columns derived from the JSONs
![](assets/materialized_view.png)

#### 3. Stream real-time flight data continuously to Snowflake

We can now write a loop to stream the flight data continuously into Snowflake.

Go back to the Linux session and run the following script.

```sh
while true
do
  curl --connect-timeout 5 -k http://ecs-alb-1504531980.us-west-2.elb.amazonaws.com:8502/opensky | $HOME/snowpipe-streaming/kafka_2.12-2.8.1/bin/kafka-console-producer.sh --broker-list $BS --producer.config $HOME/snowpipe-streaming/scripts/client.properties --topic streaming
  sleep 10
done

```
You can now go back to the Snowflake worksheet to run a `select count(1) from flights_vw` query every 10 seconds to verify that the row counts is indeed increasing.

<!---------------------------->
## Use MSK Connect (MSKC) - Optional
Duration: 15

So far we have been hosting the Kafka connector for Snowpipe Streaming on the EC2 instance. You can also use
[Amazon MSK Connect](https://aws.amazon.com/msk/features/msk-connect/) to manage the connector.

*Note that in order to use MSKC, it is suggested to run your MSK cluster in a private subnet with egress to the internet via the [NAT gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) for it to work.
See this [AWS documentation](https://docs.aws.amazon.com/msk/latest/developerguide/msk-connect-internet-access.html) for more information.

#### 1. Create a S3 bucket to store the custom plugins
Follow this [AWS documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/creating-bucket.html) to create a S3 bucket.

#### 2. Upload the libraries to the S3 bucket
On your EC2 session, run the following commands to compress the libraries into a zipped file.

```commandline
cd $HOME/snowpipe-streaming/kafka_2.12-2.8.1/libs
zip -9 /tmp/snowpipeStreaming-mskc-plugins.zip *
aws s3 cp /tmp/snowpipeStreaming-mskc-plugins.zip s3://<your s3 bucket name>/snowpipeStreaming-mskc-plugins.zip
```

#### 3. Create a custom plugin in MSK
Go to the [MSK console](https://console.aws.amazon.com/msk/home), click `Custom plugins` on the left pane.
Click `Create Custom plugin`.
![](assets/custom-plugin.png)

Fill in the s3 path to your uploaded zip file, e.g. `s3://my-mskc-bucket/snowpipeStreaming-mskc-plugins.zip`
Give the custom plugin a name, e.g. `my-mskc-plugin`, click `Create custom plugin`.

![](assets/custom-plugin-2.png)

#### 4. Create a connector
Click `Connectors` on the left pane, then click `Create connector`.
![](assets/mskc-connector.png)

Check the `Use existing custom plugin` button.
Select the custom plugin you just created, click `Next`.
![](assets/mskc-connector-2.png)

Give the connector a name, e.g. `snowpipeStreaming` in the `Basic information` section.
![](assets/mskc-connector-basicinfo.png)

Select the MSK cluster you want to associate this connector with.
Scroll down to `Configuration settings`, copy and paste
the content from the configuration file: `$HOME/snowpipe-streaming/scripts/snowflakeconnectorMSK.properties` in the EC2 instance.
![](assets/mskc-connector-config.png)

Leave all other settings as default, further scroll down to `Access permissions`. In the `Choose service role` drop-down menu, select
the role created by the Cloudformation template in the beginning of this quickstarts. The role name should look something like this
`<CFT stack name>-MSKConnectRole-<random characters>`. Click `Next`.

![](assets/mskc-connector-permission.png)

In the `Security` page, leave everything as default, click `Next`.
Skip the `Logs` page as it is optional, click `Next`.
Review the configurations and click `Create connector`. The connector will be created in about 5-10 minutes.
![](assets/mskc-connector-running.png)

At this point, the Kafka connector for Snowpipestreaming has been configured, it is running and managed by MSKC, all you need to do is to 
run the source connector to ingest live data continuously as shown in Step 3 of Section 6. 

<!---------------------------->
## Schema detection - Optional
Duration: 10

Previously we ingested raw jsons into the table `MSK_STREAMING_TBL` and did a DDL to create a nicely formulated view with 
the column names mapped to the keys in the jsons. You can now skip the DDL step with [schema detection](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-kafka-schema-detection) enabled to detect the schema of the streaming data and load data into tables that automatically match any user-defined schema. 

#### 1. Modify the Snowpipe streaming properties file

Modify the two lines in `$HOME/snowpipe-streaming/scripts/snowflakeconnectorMSK.properties` 

from
```commandline
topics=streaming
snowflake.topic2table.map=streaming:MSK_STREAMING_TBL
```
to
```commandline
topics=streaming,streaming-schematization
snowflake.topic2table.map=streaming:MSK_STREAMING_TBL,streaming-schematization:MSK_STREAMING_SCHEMATIZATION_TBL

#Also enable schematiaztion by adding
snowflake.enable.schematization=true
```
Save the properties file

#### 2. Create a new topic in MSK

We now need to create a new topic `streaming-schematization` in MSK cluster by running the following command:
```
$HOME/snowpipe-streaming/kafka_2.12-2.8.1/bin/kafka-topics.sh --bootstrap-server $BS --command-config $HOME/snowpipe-streaming/scripts/client.properties --create --topic streaming-schematization --partitions 2 --replication-factor 2
```

#### 3. Restart the consumer 

Restart the consumer by issuing the following shell command in a new Session Manager console.
```commandline
kill -9 `ps -ef | grep java | grep -v grep | awk '{print $2}'`
$HOME/snowpipe-streaming/kafka_2.12-2.8.1/bin/connect-standalone.sh $HOME/snowpipe-streaming/scripts/connect-standalone.properties $HOME/snowpipe-streaming/scripts/snowflakeconnectorMSK.properties
```

#### 4. Ingest data 

Now ingest some data into the newly created topic by running the following command in a new Session Manager console.
```commandline
curl --connect-timeout 5 http://ecs-alb-1504531980.us-west-2.elb.amazonaws.com:8502/opensky | \
jq -c '.[]' | \
while read i ; \
do \
echo $i | \
$HOME/snowpipe-streaming/kafka_2.12-2.8.1/bin/kafka-console-producer.sh --broker-list $BS --producer.config $HOME/snowpipe-streaming/scripts/client.properties --topic streaming-schematization ; \
echo $i ; \
done

```

You should see the producer using [jq](https://jqlang.github.io/jq/) to break up the json array and stream in the records one by one.

#### 5. Verify schema detection is working

Now head over to the Snowflake UI, and issue the following SQL command:
```commandline
select * from msk_streaming_schematization_tbl;
```

You should see the table already contains the keys in json records as column names with values populated. There is no need to do DDL as before.

![](assets/schema_detection.png)

Note that using the shell script `connect-standalone.sh` that comes with the Kafka distribution is not the most efficient way of ingesting data into Snowflake as it
opens and closes the topic every single time it calls the Snowpipe streaming SDK as you can see in the script in Step 4 above. We are doing this for the purpose of a quick
demonstration.

Other programing languages like Python or Java are highly recommended as they keep the topic open throughout the ingesting process.

<!---------------------------->
## Cleanup

When you are done with the demo, to tear down the AWS resources, simply go to the [Cloudformation](https://us-west-2.console.aws.amazon.com/cloudformation/home?stacks) console.
Select the Cloudformation template you used to deploy the MSK cluster at the start of the demo, then click the `Delete` tab. All the resources that were deployed previously, such as EC2 instances, MSK clusters, roles, etc., will be cleaned up.

See example screen capture below.

![](assets/cleanup.png)

After the deletion of the MSK cluster, you will also need to delete the Cloudformation template for VPC if you created your own at the very beginning of the lab.

For Snowflake cleanup, execute the following SQL commands.

```commandline
USE ROLE ACCOUNTADMIN;

DROP DATABASE MSK_STREAMING_DB;
DROP WAREHOUSE MSK_STREAMING_WH;
DROP ROLE MSK_STREAMING_RL;

-- Drop the streaming user
DROP USER IF EXISTS STREAMING_USER;
```

<!---------------------------->
## Conclusions
Duration: 5

In this lab, we built a demo to show how to ingest time-series data using Snowpipe streaming and Kafka with low latency. We demonstrated this using a self-managed Kafka 
connector on an EC2 instance. However, for a production environment, we recommend using [Amazon MSK Connect](https://aws.amazon.com/msk/features/msk-connect/), which offers 
scalability and resilience through the AWS infrastructure. Alternatively, if you have infrastructure supported by either [Amazon EKS](https://aws.amazon.com/eks/) or
[Amazon ECS](https://aws.amazon.com/ecs/), you can use them to host your containerized Kafka connectors as well.

For those of you who are interested in learning more about how to build sleek dashboards for monitoring the live flight data, please navigate to this
[quickstart](https://quickstarts.snowflake.com/guide/getting_started_with_amg_and_streamlit_on_real-time_dashboarding/) to continue.

Related Resources

- [Snowpipe Streaming Demystified](https://medium.com/snowflake/snowpipe-streaming-demystified-e1ee385c6d9c)
- [Getting Started with Amazon Managed Service for Grafana and Streamlit On Real-time Dashboarding](https://quickstarts.snowflake.com/guide/getting_started_with_amg_and_streamlit_on_real-time_dashboarding/)
- [Getting started with Snowflake](https://quickstarts.snowflake.com/)
- [Snowflake on AWS Marketplace](https://aws.amazon.com/marketplace/seller-profile?id=18d60ae8-2c99-4881-a31a-e74770d70347)
- [Snowflake for Data Sharing](https://www.snowflake.com/Workloads/data-sharing/)
- [Snowflake Marketplace](https://www.snowflake.com/en/data-cloud/marketplace/)
- [Amazon Managed Streaming for Apache Kafka (MSK)](https://aws.amazon.com/msk/)



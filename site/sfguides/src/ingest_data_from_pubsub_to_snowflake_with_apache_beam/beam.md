author: Kamil Bregula
id: ingest_data_from_pubsub_to_snowflake_with_apache_beam
summary: Ingest data from PubSub to Snowflake with Apache Beam
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Apache Beam, Data Engineering

# Ingest data from PubSub to Snowflake with Apache Beam
<!-- ------------------------ -->

## Overview
Duration: 30


This guide shows you how to set up your Google Cloud project, Snowflake account, create a Java project with Maven by using the Apache Beam SDK and run a streaming pipeline locally and on the Dataflow service. Each step is presented as a console command or an SQL command to reduce the possibility of incorrect execution of a step.

### Prerequisites

This guide assumes you have a basic working knowledge of Java and Google Dataflow.

### What You'll Learn

- how to configure GCP and Snowflake resources needed to run streaming pipelines
- how to compile and run a pipeline written in Java

### What You'll Need

You will need the following things before beginning:
1. Snowflake:
   1. *A Snowflake Account.*
   2. *A Snowflake User created with `ACCOUNTADMIN` Role.* This user will need set up a necessary resources on Snowflake account.
2. Integrated Development Environment (IDE)
   1. *Your favorite IDE with Git integration.* If you don't already have a favorite IDE that integrates with Git I would recommend the great, free, open-source [Visual Studio Code](https://code.visualstudio.com/).
   2. *[SnowSQL (CLI Client)](https://docs.snowflake.com/en/user-guide/snowsql.html) with named connection configured.* To install it, see [installation guide](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html). To configure a named connection, see:  [using the named connection](https://docs.snowflake.com/en/user-guide/snowsql-start.html#using-named-connections).
3. *Google Cloud Platform*:
   1. *Google Cloud project with billing enabled*. If you don't have any, have a look at [Creating a Google Cloud Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects). Learn how to [check if billing is enabled on a project](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled).
   2. Ensure you have one of the following IAM roles to create a Cloud Storage bucket:

      * Owner (roles/owner)
      * Editor (roles/editor)
      * Storage Admin (roles/storage.admin)
    
      The permissions contained in these roles allow you to create, delete, or modify buckets. For information on setting IAM roles, see the [IAM roles for Cloud Storage](https://cloud.google.com/storage/docs/access-control/iam-roles) in the Google Cloud documentation
   3. Ensure you have one of the following IAM roles to create subscription and topics in Pub/Sub service:

      * Owner (roles/owner)
      * Editor (roles/editor)
      * Pub/Sub Admin (roles/storage.admin)
      * Pub/Sub Editor (roles/storage.editor)

      The permissions contained in these roles allow you to create, delete, or modify topics and subscriptions. For information on setting IAM roles, see the [IAM roles for Cloud Pub/Sub]https://cloud.google.com/pubsub/docs/access-control) in the Google Cloud documentation
   4. Ensure you have one of the following IAM roles to execute and manipulate Dataflow jobs:

      * Owner (roles/owner)
      * Editor (roles/editor)
      * Dataflow Developer Admin (roles/dataflow.developer)

      The permissions contained in these roles allow you to execute and manipulate Dataflow jobs. For information on setting IAM roles, see the [IAM roles for Cloud Dataflow]hhttps://cloud.google.com/dataflow/docs/concepts/access-control) in the Google Cloud documentation

4. *[Apache Maven](https://maven.apache.org/download.cgi)*. Please install Apache Maven by following [installation guide](https://maven.apache.org/install.html).
5. *[Google Cloud SDK](https://cloud.google.com/sdk)*. Please install Google Cloud SDK by following [installation guide](https://cloud.google.com/sdk/docs/install-sdk). You must also be logged in and have an active project in Google Cloud SDK.

It is worth getting acquainted with [quickstart for Apache Beam](https://beam.apache.org/get-started/quickstart-java/) as well.

###  What You'll Build

We will run two Dataflow jobs:

- The Data Generator Job used to publish fake JSON messages at a specified rate (measured in messages per second) to a Google Cloud Pub/Sub topic. For details, see: [Synthetic data generation with Dataflow data generator flex template](https://cloud.google.com/blog/products/data-analytics/dataflow-flex-template-streaming-data-generator)

- The Data Receiver Job used to consume messages from a Google Cloud Pub/Sub topic and save all messages to the Snowflake table.

An example message looks like the following:
```json
{
  "id": "a21850b9-3290-4161-b116-2518a615b6c5",
  "name": "A green door",
  "age": 39,
  "price": 12.50
}
```

<!-- ------------------------ -->
## Create a Service User in Snowflake

To execute SQL statements via SnowSQL, you must specify a connection name. For the sake of clarity, it is worth writing it as a variable so that you can later refer to it in commands.

Set a variable that specifies your connection in SnowSQL:
<!-- INSERT path:./.env.example text_id:snowsql lang:bash-->
```bash
SNOWSQL_CONN="XXX"
```
<!-- END -->

This will be used to execute SQL commands as in the example below:
<!-- INSERT path:./setup.sh text_id:snowsql lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "SELECT 1"
```
<!-- END -->

You will now create a user account separate from your own that the application will use to query data in Snowflake database. In keeping with sound security practices, the account will use key-pair authentication and have limited access in Snowflake.

*Note:* Snowflake has a few limitations that you need to know if you are going to configure it yourself:
- The Snowflake Ingest Service only supports a private key authentication, so you have to use this authentication method if you are building streaming pipelines.
- `SnowflakeIO` only supports encrypted private keys, so your private key must have passphrase set.
- Snowflake Ingest Service always uses the default account role. The role passed to Apache Beam is ignored.

Let's start with setting up a few variables.
<!-- INSERT path:./.env.example text_id:user lang:bash -->
```bash
SNOWFLAKE_USERNAME="DEV_XXX_BEAM_USER"
SNOWFLAKE_ROLE="BEAM_ROLE"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_PRIVATE_KEY_PASSPHASE="hard-to-quest-Pa@@phase-42"
```
<!-- END -->
where:
- `SNOWFLAKE_USERNAME` - the name of the new service user to be created
- `SNOWFLAKE_ROLE` - default role used by the service user
- `SNOWFLAKE_WAREHOUSE` - default warehouse used by the service user.
- `SNOWFLAKE_PRIVATE_KEY_PASSPHASE` - passphrase used to encrypt the private key.

To generate a private key, run:
<!-- INSERT path:./setup.sh text_id:gen_private_key lang:bash-->
```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -v1 PBE-SHA1-RC4-128 -out rsa_key.p8 -passout "pass:${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}"
```
<!-- END -->

The commands generate a private key in PEM format in `rsa_key.p8` file. The content of this file will be similar to the one below:
```
-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIE6TAbBgkqhkiG9w0BBQMwDgQILYPyCppzOwECAggABIIEyLiGSpeeGSe3xHP1
wHLjfCYycUPennlX2bd8yX8xOxGSGfvB+99+PmSlex0FmY9ov1J8H1H9Y3lMWXbL
...
-----END ENCRYPTED PRIVATE KEY-----
```

Set a variable with a private key for later use. You should skip the first and last line. To do it, run:
<!-- INSERT path:./setup.sh text_id:set_private_key lang:bash-->
```bash
SNOWFLAKE_PRIVATE_KEY=$(cat rsa_key.p8 | tail -n +2 | tail -r | tail -n +2 | tail -r)
```
<!-- END -->

Based on the private key, you should generate the public key. To do it, run
<!-- INSERT path:./setup.sh text_id:gen_public_key lang:bash-->
```bash
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub -passin "pass:${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}"
```
<!-- END -->

The command generates the public key in PEM format in `rsa_key.pub ` file. The content of this file will be similar to the one below:
```bash
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy+Fw2qv4Roud3l6tjPH4
zxybHjmZ5rhtCz9jppCV8UTWvEXxa88IGRIHbJ/PwKW/mR8LXdfI7l/9vCMXX4mk
...
-----END PUBLIC KEY-----
```

To use it later, set a variable with a public key for later use. You should skip the first and last line. To do it, run:
<!-- INSERT path:./setup.sh text_id:set_public_key lang:bash-->
```bash
SNOWFLAKE_PUB_KEY=$(cat rsa_key.pub | tail -n +2 | tail -r | tail -n +2 | tail -r)
```
<!-- END -->

To make sure that the keys are correct, you can verify them.
<!-- INSERT path:./setup.sh text_id:verify_private_key lang:bash-->
```bash
echo  "It is a secret" > secret.txt
openssl dgst -sha256 -sign rsa_key.p8 -passin "pass:${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}" -out secret.txt.sign secret.txt
openssl dgst -sha256 -verify rsa_key.pub -signature secret.txt.sign secret.txt
rm secret.txt secret.txt.sign
```
<!-- END -->

Finally, to create a new user and role, run:
<!-- INSERT path:./setup.sh text_id:create_user lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  CREATE OR REPLACE ROLE ${SNOWFLAKE_ROLE};
  CREATE OR REPLACE USER ${SNOWFLAKE_USERNAME} DEFAULT_ROLE=${SNOWFLAKE_ROLE}, DEFAULT_WAREHOUSE=${SNOWFLAKE_WAREHOUSE} RSA_PUBLIC_KEY='${SNOWFLAKE_PUB_KEY}';

  GRANT ROLE ${SNOWFLAKE_ROLE} TO USER ${SNOWFLAKE_USERNAME}
"
```
<!-- END -->

You can use SnowSQL to validate the service user's configuration. To do it, run:
<!-- INSERT path:./setup.sh text_id:verify_user lang:bash-->
```bash
SNOWSQL_PRIVATE_KEY_PASSPHRASE="${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}" \
   snowsql \
   --accountname "$(echo "${SNOWFLAKE_SERVER_NAME}" | cut -d "." -f 1-2)" \
   --username "${SNOWFLAKE_USERNAME}" \
   --dbname "${SNOWFLAKE_DATABASE}" \
   --schemaname "${SNOWFLAKE_SCHEMA}" \
   --warehouse "${SNOWFLAKE_WAREHOUSE}" \
   --rolename "${SNOWFLAKE_ROLE}" \
   --private-key-path "rsa_key.p8" \
   --query 'SELECT CURRENT_ROLE(), CURRENT_USER()';
```
<!-- END -->

If you run into difficulties, check out the article [Key Pair Authentication & Key Pair Rotation
](https://docs.snowflake.com/en/user-guide/key-pair-auth.html) in the Snowflake documentation.

<!-- ------------------------ -->
## Setting up database, schema in Snowflake

Set a variables that describe the Snowflake account and tables as in the example below:
<!-- INSERT path:./.env.example text_id:connection lang:bash-->
```bash
SNOWFLAKE_SERVER_NAME="XXX.snowflakecomputing.com"
SNOWFLAKE_DATABASE="DEV_XXX_BEAM"
SNOWFLAKE_SCHEMA="DEV_XXX"
```
<!-- END -->
where:
- `SNOWFLAKE_SERVER_NAME` should specify the name of the server you will connect to. It must to end with `.snowflakecomputing.com`.
- `SNOWFLAKE_DATABASE` - the name of the new database to be created
- `SNOWFLAKE_SCHEMA` - the name of the new schema to be created

To create a new database and schema and grant privilege, run:
<!-- INSERT path:./setup.sh text_id:create_database lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  CREATE OR REPLACE DATABASE ${SNOWFLAKE_DATABASE};
  CREATE OR REPLACE SCHEMA ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA};

  GRANT USAGE ON DATABASE ${SNOWFLAKE_DATABASE} TO ROLE ${SNOWFLAKE_ROLE};
  GRANT USAGE ON SCHEMA ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA} TO ROLE ${SNOWFLAKE_ROLE};
"
```
<!-- END -->

<!-- ------------------------ -->
## Setting up a bucket in GCP, stage and tables in Snowflake

Let's start with setting up a few variables.
<!-- INSERT path:./.env.example text_id:table lang:bash-->
```bash
DATAFLOW_BUCKET="sfc-pubsub-to-snowflake-dataflow"
SNOWFLAKE_STORAGE_INTEGRATION="DEV_XXX_BEAM_STORAGE_INTEGRATION"
SNOWFLAKE_STAGE="DEV_XXX_BEAM_STAGE"
PIPELINE_SNOWFLAKE_OUTPUT_TABLE="PUBSUB_MESSAGES"
```
<!-- END -->

where:
- `DATAFLOW_BUCKET` - the name of the new bucket to be created. It will be used as the staging area. Every bucket name are globally unique, so you will have to update value.
- `SNOWFLAKE_STORAGE_INTEGRATION` - the name of the new storage integration to be created
- `SNOWFLAKE_STAGE` - the name of the new stage to be created.
- `SNOWFLAKE_STORAGE_INTEGRATION` - the name of the new storage integration to be created

To create a GCS bucket, run:
<!-- INSERT path:./setup.sh text_id:create_bucket lang:bash-->
```bash
gsutil mb -c standard "gs://${DATAFLOW_BUCKET}"
```
<!-- END -->

To create a Snowflake storage integration, run:
<!-- INSERT path:./setup.sh text_id:create_integration lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  CREATE OR REPLACE STORAGE INTEGRATION ${SNOWFLAKE_STORAGE_INTEGRATION}
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = GCS
    ENABLED = TRUE
    STORAGE_ALLOWED_LOCATIONS = ('gcs://${DATAFLOW_BUCKET}/');
"
```
<!-- END -->


Now you need to check the name of the service account assigned to the storage integration to give it bucket permissions.
<!-- INSERT path:./setup.sh text_id:assign_bucket lang:bash-->
```bash
SNOWFLAKE_STORAGE_INTEGRATION_SA_EMAIL=$(snowsql -c "${SNOWSQL_CONN}" -q "DESC STORAGE INTEGRATION ${SNOWFLAKE_STORAGE_INTEGRATION};" -o output_format=json -o friendly=false -o timing=false | jq '.[] | select(.property == "STORAGE_GCP_SERVICE_ACCOUNT") | .property_value' -r)
   gsutil iam ch "serviceAccount:${SNOWFLAKE_STORAGE_INTEGRATION_SA_EMAIL}:roles/storage.admin" "gs://${DATAFLOW_BUCKET}"
```
<!-- END -->

Next, you need to create a stage to tell Snowflake where the files will be saved and what integration it should use. To do it, run:
<!-- INSERT path:./setup.sh text_id:create_stage lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  CREATE OR REPLACE STAGE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_STAGE}
  URL='gcs://${DATAFLOW_BUCKET}/staging'
  STORAGE_INTEGRATION = ${SNOWFLAKE_STORAGE_INTEGRATION};

  GRANT USAGE ON STAGE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_STAGE} TO ROLE ${SNOWFLAKE_ROLE};
"
```
<!-- END -->
Next we will deal with the table. These should match the format of the input messages. To create a new table, run:
<!-- INSERT path:./setup.sh text_id:create_table lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  CREATE OR REPLACE TABLE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE} (id TEXT, name TEXT, age INTEGER, price FLOAT);

  GRANT INSERT ON TABLE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE} TO ROLE ${SNOWFLAKE_ROLE};
  GRANT SELECT ON TABLE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE} TO ROLE ${SNOWFLAKE_ROLE};
"
```
<!-- END -->

To verify the configuration, now we can create a file on the bucket and then load it.
<!-- INSERT path:./setup.sh text_id:verify_load lang:bash-->
```bash
FILENAME=test-data-${RANDOM}.csv.gz
echo "'16f0a88b-af94-4707-9f91-c1dd125f271c','A blue door',48,12.5
'df9efd67-67d6-487d-9ad4-92537cf25eaa','A yellow door',16,12.5
'04585e7f-f340-4d2e-8371-ffbc162c4354','A pink door',26,12.5
'd52275c0-d6c6-4331-8248-784255bef654','A purple door',13,12.5" | gzip | gsutil cp - "gs://${DATAFLOW_BUCKET}/staging/${FILENAME}"
snowsql -c "${SNOWSQL_CONN}" -q "
  COPY INTO ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE} FROM @${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_STAGE}/${FILENAME};
"
```
<!-- END -->


And display a content of table:
<!-- INSERT path:./setup.sh text_id:display_table lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  SELECT * FROM ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE} LIMIT 4
"
```
<!-- END -->

When everything works fine, we should clear the tables:
<!-- INSERT path:./setup.sh text_id:truncate_table lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  TRUNCATE TABLE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE}
"
```
<!-- END -->

If you run into difficulties, check out the article: [Configuring an Integration for Google Cloud Storage](https://docs.snowflake.com/en/user-guide/data-load-gcs-config.html#step-3-grant-the-service-account-permissions-to-access-bucket-objects) in the Snowflake documentation.

<!-- ------------------------ -->
## Setting up a Snowpipe

Let's start with setting up a variable with name of new pipe to be created.
<!-- INSERT path:./.env.example text_id:pipe lang:bash-->
```bash
SNOWFLAKE_PIPE="PUSBUS_EXAMPLE_PIPE"
```
<!-- END -->

To create a new pipe, run:
<!-- INSERT path:./setup.sh text_id:create_pipe lang:bash-->
```bash
snowsql -c "${SNOWSQL_CONN}" -q "
  CREATE OR REPLACE PIPE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_PIPE} AS
  COPY INTO ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${PIPELINE_SNOWFLAKE_OUTPUT_TABLE} FROM @${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_STAGE};
  ALTER PIPE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_PIPE} SET PIPE_EXECUTION_PAUSED=true;

  GRANT OWNERSHIP ON PIPE ${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_PIPE} TO ROLE ${SNOWFLAKE_ROLE};
"
```
<!-- END -->

The pipe is automatically paused when the owner is changed. To resume pipe, run:
<!-- INSERT path:./setup.sh text_id:resume_pipe lang:bash-->
```bash
SNOWSQL_PRIVATE_KEY_PASSPHRASE="${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}" \
  snowsql \
  --accountname "$(echo "${SNOWFLAKE_SERVER_NAME}" | cut -d "." -f 1-2)" \
  --username "${SNOWFLAKE_USERNAME}" \
  --private-key-path "rsa_key.p8" \
  --query "
  SELECT SYSTEM\$PIPE_FORCE_RESUME('${SNOWFLAKE_DATABASE}.${SNOWFLAKE_SCHEMA}.${SNOWFLAKE_PIPE}');
"
```
<!-- END -->

If you run into difficulties, check out the articles: [Preparing to Load Data Using the Snowpipe REST API](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-rest-gs.html), [Troubleshooting Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts.html) in the Snowflake documentation.

## Configuring a PubSub service

Let's start with setting up a few variables.
<!-- INSERT path:./.env.example text_id:pubsub lang:bash-->
```bash
PIPELINE_PUBSUB_TOPIC="example-pipeline-pubsub-topic"
PIPELINE_PUBSUB_SUBSCRIPTION="example-pipeline-pubsub-subscription"
```
<!-- END -->
where:
- `PIPELINE_PUBSUB_TOPIC`- - the name of the new Google Pub/Sub topic to be created.
- `PIPELINE_PUBSUB_SUBSCRIPTION` - - the name of the new Google Pub/Sub subscription to be created.

Now we generate a full qualified names:
<!-- INSERT path:./setup.sh text_id:dynamic_variable_pubsub lang:bash-->
```bash
GCP_PROJECT_ID="$(gcloud config get-value core/project)"
PIPELINE_PUBSUB_TOPIC_FQN="projects/${GCP_PROJECT_ID}/topics/${PIPELINE_PUBSUB_TOPIC}"
PIPELINE_PUBSUB_SUBSCRIPTION_FQN="projects/${GCP_PROJECT_ID}/subscriptions/${PIPELINE_PUBSUB_SUBSCRIPTION}"
```
<!-- END -->

Create a new topic and subscription:
<!-- INSERT path:./setup.sh text_id:create_pubsub lang:bash-->
```bash
gcloud pubsub topics create "${PIPELINE_PUBSUB_TOPIC_FQN}"
gcloud pubsub subscriptions create --topic "${PIPELINE_PUBSUB_TOPIC_FQN}" "${PIPELINE_PUBSUB_SUBSCRIPTION_FQN}"
```
<!-- END -->

<!-- ------------------------ -->
## Running a streaming data generator



To generate syntactic data that will be used by our pipeline, we will use [Synthetic data generator](https://cloud.google.com/blog/products/data-analytics/dataflow-flex-template-streaming-data-generator) prepared by Google and available as flex templates.

First, create a schema file.
<!-- INSERT path:./setup.sh text_id:create_schema lang:bash-->
```bash
echo '{
   "id": "{{uuid()}}",
   "name": "A green door",
   "age": {{integer(1,50)}},
   "price": 12.50
}' | gsutil cp - "gs://${DATAFLOW_BUCKET}/stream-schema.json"
```
<!-- END -->
For instructions on how to construct the schema file, see [json-data-generator](https://github.com/vincentrussell/json-data-generator).

Set the name of the Dataflow region where your jobs will be executed.
<!-- INSERT path:./.env.example text_id:dataflow_region lang:bash-->
```bash
DATAFLOW_REGION="us-central1"
```
<!-- END -->

To starts a new Dataflow job, run:
```bash
gcloud beta dataflow flex-template run "streaming-data-generator" \
   --project="${GCP_PROJECT_ID}" \
   --region="${DATAFLOW_REGION}" \
    --template-file-gcs-location=gs://dataflow-templates/latest/flex/Streaming_Data_Generator \
   --parameters \
schemaLocation="gs://${DATAFLOW_BUCKET}/stream-schema.json",\
qps=1,\
topic="${PIPELINE_PUBSUB_TOPIC_FQN}"
```

<!-- ------------------------ -->
## Getting the source code for the project

Pipelines you will be running are written on Java. The source code is available in [GitHub](https://github.com/Snowflake-Labs/sfguide-beam-examples). To checkout repository, run:
```bash
git clone https://github.com/Snowflake-Labs/sfguide-beam-examples.git
```
Now, you can open the project in your favorite IDE.


## Running pipeline on Direct Runner (locally)

To check if our pipeline works well, start by running it locally using Direct Runner.

To compile and prepare a self-container JAR file, run:
<!-- INSERT path:./run_pipeline_on_direct_runner.sh text_id:compile_direct_runner lang:bash-->
```bash
mvn package -P "direct-runner" --batch-mode
```
<!-- END -->
After executing this command, file `target/ingest-pubsub-to-snowflake-bundled-1.0.jar` should be created that you can run. To do ir, run:
<!-- INSERT path:./run_pipeline_on_direct_runner.sh text_id:run_direct_runner lang:bash-->
```bash
java -jar target/ingest-pubsub-to-snowflake-bundled-1.0.jar \
   --runner=DirectRunner \
   --serverName="${SNOWFLAKE_SERVER_NAME}" \
   --username="${SNOWFLAKE_USERNAME}" \
   --database="${SNOWFLAKE_DATABASE}" \
   --schema="${SNOWFLAKE_SCHEMA}" \
   --role="${SNOWFLAKE_ROLE}" \
   --rawPrivateKey="${SNOWFLAKE_PRIVATE_KEY}" \
   --snowPipe="${SNOWFLAKE_PIPE}" \
   --privateKeyPassphrase="${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}" \
   --storageIntegrationName="${SNOWFLAKE_STORAGE_INTEGRATION}" \
   --inputSubscription="${PIPELINE_PUBSUB_SUBSCRIPTION_FQN}" \
   --outputTable="${PIPELINE_SNOWFLAKE_OUTPUT_TABLE}" \
   --gcpTempLocation="gs://${DATAFLOW_BUCKET}/temp" \
   --tempLocation="gs://${DATAFLOW_BUCKET}/temp" \
   --stagingBucketName="gs://${DATAFLOW_BUCKET}/staging"
```
<!-- END -->


## Running pipeline on Dataflow runner

In a production environment, you take advantage of the Google Dataflow service.

To compile and prepare a self-container JAR file, run:
<!-- INSERT path:./run_pipeline_on_dataflow_runner.sh text_id:compile_dataflow_runner lang:bash-->
```bash
mvn package -P "dataflow-runner" --batch-mode
```
<!-- END -->
After executing this command, file `target/ingest-pubsub-to-snowflake-bundled-1.0.jar` should be created that you can run to submit a Google Dataflow job. To do ir, run:
<!-- INSERT path:./run_pipeline_on_dataflow_runner.sh text_id:run_dataflow_runner lang:bash-->
```bash
java -jar target/ingest-pubsub-to-snowflake-bundled-1.0.jar \
   --runner=DataflowRunner \
   --project="${GCP_PROJECT_ID}" \
   --region="${DATAFLOW_REGION}" \
   --appName="${DATAFLOW_APP_NAME}" \
   --serverName="${SNOWFLAKE_SERVER_NAME}" \
   --username="${SNOWFLAKE_USERNAME}" \
   --rawPrivateKey="${SNOWFLAKE_PRIVATE_KEY}" \
   --privateKeyPassphrase="${SNOWFLAKE_PRIVATE_KEY_PASSPHASE}" \
   --database="${SNOWFLAKE_DATABASE}" \
   --schema="${SNOWFLAKE_SCHEMA}" \
   --role="${SNOWFLAKE_ROLE}" \
   --storageIntegrationName="${SNOWFLAKE_STORAGE_INTEGRATION}" \
   --inputSubscription="${PIPELINE_PUBSUB_SUBSCRIPTION_FQN}" \
   --snowPipe="${SNOWFLAKE_PIPE}" \
   --outputTable="${PIPELINE_SNOWFLAKE_OUTPUT_TABLE}" \
   --gcpTempLocation="gs://${DATAFLOW_BUCKET}/temp" \
   --stagingBucketName="gs://${DATAFLOW_BUCKET}/staging"
```
<!-- END -->

## Conclusion

Congratulations on completing this lab!

### What we've covered

- How to configure GCP and Snowflake resources needed to run streaming pipelines
- How to compile and run a pipeline written in Java

author: Dustin Nest
id: streamnative-snowflake-open-catalog-integration
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/lakehouse-analytics, snowflake-site:taxonomy/snowflake-feature/storage, snowflake-site:taxonomy/snowflake-feature/snowpipe-streaming
language: en
summary: Use StreamNative to build a cost-effective Streaming Augmented Lakehouse, streaming Kafka messages directly to object storage in Iceberg format an connect to Snowflake Open Catalog. 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Snowflake Open Catalog Integration with StreamNative and Data Streaming in Apache Iceberg
<!-- ------------------------ -->
## Overview 

StreamNative is partnering with Snowflake to provide you with cost-effective real-time data streaming to Snowflake. This means providing you with best-in-class data ingestion methods tailored to meet your specific needs. This guide focuses on creating a **Streaming Augmented Lakehouse** using **StreamNative's Ursa Engine** with built-in support for **Apache Iceberg&trade; and Snowflake Open Catalog**. Apache Kafka&reg; messages published to the StreamNative Ursa Cluster will be stored in object storage in Iceberg format. Without copying over the data through connectors, you can directly access data from Snowflake Open Catalog and start analyzing the data. To learn more about cost savings when using the StreamNative Ursa Engine to ingest data to Snowflake, visit this [link](https://streamnative.io/blog/leaderless-architecture-and-lakehouse-native-storage-for-reducing-kafka-cost).

StreamNative also supports ingesting data into Snowflake using **Snowpipe or Snowpipe Streaming** with **Kafka or Pulsar Connectors** that will not be discussed in this tutorial. For more information on using Connectors to ingest data into Snowflake, follow this [link](https://courses.streamnative.io/courses/streamnative-snowflake-streaming-augmented-lakehouse-and-connectors/lessons/introduction-to-uniconn-kafka-and-pulsar-io-connectors/).

### What You Will Build 
- A Streaming Augmented Lakehouse powered by a Kafka-compatible StreamNative BYOC Ursa Cluster integrated with Snowflake Open Catalog.

### What You Will Learn 
- How to create a Snowflake Open Catalog
- How to deploy a StreamNative BYOC Ursa Cluster integrated with Snowflake Open Catalog
- How to publish Kafka messages to the StreamNative Ursa Cluster using Kafka Java Client
- How to query tables visible in Snowflake Open Catalog in Snowflake AI Data Cloud

### Prerequisites or What You Will Need
- Familiarity with Terraform and Java.
- Familiarity with creating policies, roles and s3 buckets in AWS.
- A StreamNative account available at [streamnative.io](https://www.streamnative.io). Your account will come with $200 in free credits, sufficient for following this tutorial. No credit card is necessary.
- AWS Account for deploying the StreamNative BYOC Ursa Cluster. BYOC clusters are deployed into your cloud provider. These resources will incur AWS charges that are not covered by StreamNative.
- Permissions to create policies, roles, and s3 buckets in AWS, as well as apply the StreamNative Terraform [vendor access module](https://docs.streamnative.io/docs/byoc-aws-access).
- Access to [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) and ability to create a Snowflake Open Catalog account.
- Environment for executing Terraform modules and Java code.

Apache&reg;, Apache Iceberg&trade;, and Apache Kafka&reg; are either registered trademarks or trademarks of Apache Software Foundation in the United States and/or other countries.

## Setup Catalog and Permissions

Before initiating the integration of Snowflake Open Catalog with StreamNative Cloud, please ensure the following steps are completed. [This video](https://www.youtube.com/watch?v=R0uPsIIVmO8) will also guide you through this process.

### Create a Snowflake AI Data Cloud Account

Create a Snowflake AI Data Cloud Account. The homepage will look as follows.

![Create Snowflake AI Data Cloud Account](assets/create-snowflake-standard-account.png)

### Create Snowflake Open Catalog Account

To access the Snowflake Open Catalog console, a specialized Open Catalog Account must be created. This account type is specifically designed for managing Open Catalog features and functionality.

Enter **Admin → Accounts → Toggle → Create Snowflake Open Catalog Account**.

![Create Snowflake Open Catalog Account](assets/create-snowflake-opencatalog-account.png)

Configure the Snowflake Open Catalog Account.

* Cloud: AWS
* Region: region to place the Snowflake Open Catalog Account
* Edition: any

> 
>
> IMPORTANT: The Snowflake Open Catalog Account, s3 bucket, and StreamNative BYOC Ursa Cluster should be in the same region. Snowflake Open Catalog doesn’t support cross-region buckets. To avoid costs associated with cross-region traffic, we highly recommend your s3 bucket and StreamNative BYOC Ursa Cluster are in the same region.

![Create Snowflake Open Catalog Account Dialog](assets/create-snowflake-open-catalog-account-dialog.png)

Next, input a Snowflake Open Catalog Account Name, User Name, Password, and Email. This will create a new user for use specifically with the Snowflake Open Catalog Account.

![Create Snowflake Open Catalog Account Details](assets/create-snowflake-open-catalog-account-details.png)

Click **Create Account**. You will see the following if account creation is successful. We highly recommend taking a screenshot of this confirmation message. This Account URL and Account Locator URL will be used in later steps.

![Create Snowflake Open Catalog Account Success](assets/create-account-success.png)

Click the **Account URL** and sign into your Open Catalog Account with the User Name and Password you created for this account. You will enter the Snowflake Open Catalog console.

![Snowflake Open Catalog Account Page](assets/click-account-url.png)

If you need the **Account URL** of your Snowflake Open Catalog Account in the future, navigate to **Admin → Accounts → … → Manage URLs** of your Snowflake Open Catalog Account. This page is available in your Snowflake AI Data Cloud Account.

![Snowflake Open Catalog Account URL](assets/manage-snowflake-account-urls.png)

### Setup storage bucket with permissions for StreamNative

Next we must choose the bucket location for the backend of our StreamNative BYOC Ursa Cluster and grant access to StreamNative Cloud. You have two choices to setup a s3 storage bucket for the StreamNative Ursa Cluster backend. This is where data will be stored in Iceberg format and accessed by Snowflake Open Catalog and Snowflake AI Data Cloud.
> 
> 
> IMPORTANT: The Snowflake Open Catalog Account, s3 bucket, and StreamNative BYOC Ursa Cluster should be in the same region. Snowflake Open Catalog doesn’t support cross-region buckets. To avoid costs associated with cross-region traffic, we highly recommend your s3 bucket and StreamNative BYOC Ursa Cluster are in the same region.

**Option 1: Use your own bucket (recommended)**

If you choose this option, you need to create your own storage bucket, with the option to create a bucket path. When using your own bucket, the resulting path you will use for creation of the Snowflake Open Catalog will be as follows. The compaction folder will be created automatically by the StreamNative cluster.

```markdown
s3://<your-bucket-name>/<your-bucket-path>/compaction
```

StreamNative will require access to this storage bucket. To grant access, execute the following Terraform module.
* external_id: StreamNative organization, directions after terraform module for finding your StreamNative organization
* role: the name of the role that will be created in AWS IAM, arn needed when creating cluster
* buckets: bucket name and path
* account_ids: AWS account id
```
module "sn_managed_cloud" {
  source = "github.com/streamnative/terraform-managed-cloud//modules/aws/volume-access?ref=v3.19.0"

  external_id = "<your-organization-name>"
  role = "<your-role-name>"
  buckets = [
    "<your-bucket-name>/<your-bucket-path>",
  ]

  account_ids = [
    "<your-aws-account-id>"
  ]
}
```
You can find your organization name in the StreamNative console, as shown below.

![StreamNative Organization](assets/streamnative-org-name.png)

Before executing the Terraform module, you must define the following environment variables. These variables are used to grant you access to the AWS account where the s3 bucket is located.

```markdown
export AWS_ACCESS_KEY_ID="<YOUR_AWS_ACCESS_KEY_ID>"
export AWS_SECRET_ACCESS_KEY="<YOUR_AWS_SECRET_ACCESS_KEY>"
export AWS_SESSION_TOKEN="<YOUR_AWS_SESSION_TOKEN>"
```

Run the Terraform module

```markdown
terraform init
terraform plan
terraform apply
```

**Option 2: Use StreamNative provided bucket**

This process requires you to deploy the StreamNative BYOC Cloud Connection, Cloud Environment, and beginning the process of deploying the StreamNative BYOC Ursa Cluster to obtain the cluster id before moving forward. StreamNative will automatically assign the necessary permissions to this bucket.

To proceed, you will need to first complete the steps for [granting vendor access, creating a Cloud Connection, and setting up the Cloud Environment](https://docs.streamnative.io/docs/byoc-overview). This process will grant StreamNative permissions into your cloud provider and deploy the required infrastructure before you begin the process of deploying a StreamNative BYOC Ursa Cluster. [This video](https://youtu.be/vsHjaQNKFRk?si=2pUJXE_s0LfzH3At) provides an overview of this process with detailed videos available in this [playlist](https://www.youtube.com/playlist?list=PL7-BmxsE3q4W5QnrusLyYt9_HbX4R7vEN).

Next, begin the process of deploying the StreamNative BYOC Ursa Cluster to obtain the cluster id. This process is outlined in the step **Create StreamNative BYOC Ursa Cluster** with directions on obtaining the cluster id.

When using a StreamNative-provided bucket, the resulting path you will use for creation of the Snowflake Open Catalog will be as follows. The cloud environment id will be created during the deployment of the Cloud Environment. The cluster id is assigned when starting the cluster creation process in the StreamNative Console.

```markdown
s3://<your-cloud-environment-id>/<your-cluster-id>/compaction
```

### Configure AWS Account for Snowflake Open Catalog Access

Next we create an IAM policy and role for Snowflake Open Catalog Access.

In the AWS console, enter **Access management → Policies → Create policy**.

![Create AWS Policy](assets/create-aws-policy.png)

Then choose the JSON format. Enter the rule as follows, replacing your-bucket-name and your-bucket-path based on if you are using a user provided bucket or StreamNative provided bucket. Do not include the compaction folder in the bucket path.

```javascript
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:DeleteObject",
                "s3:DeleteObjectVersion"
            ],
            "Resource": "arn:aws:s3:::<your-bucket-name>/<your-bucket-path>/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::<your-bucket-name>/<your-bucket-path>",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "*"
                    ]
                }
            }
        }
    ]
}
```
Click **Next**.

![Add Snowflake Open Catalog Permissions](assets/add-aws-permissions.png)

Provide a policy name and click **Create policy**.

![Create Policy](assets/review-create-policy.png)

Next we an Create IAM role.

In the AWS console, enter **Access management → Roles → Create role**.

![Create Role](assets/aws-create-role.png)

* Trusted entity type: AWS account
* An AWS account: this account
* Enable External ID
* Set External ID: training_test (will be used when creating catalog)

Click **Next**.

![Set External ID](assets/set-aws-external-id.png)

Select the policy created in the previous step. Then click **Next**

![Select Policy](assets/set-aws-policy-for-snowflake.png)

Input a role name and click **Create role**.

![Create Role](assets/input-role-create-role.png)

View the detailed role information and record the ARN.

![Record ARN](assets/aws-arn-for-snowflake-open-catalog.png)

This policy and role are used for Snowflake Open Catalog access to the s3 bucket.

### Create Snowflake Open Catalog

Next we create the Snowflake Open Catalog. Click **+ Create** next to **Manage Catalogs**.

![Create New Catalog](assets/create-snowflake-open-catalog.png)

* Name: streamnative
* External: disabled
* Storage provider: S3
* Default base location:

```markdown
User provided bucket:
s3://<your-bucket-name>/<your-bucket-path>/compaction

StreamNative provided bucket:
s3://<your-cloud-environment-id>/<your-cluster-id>/compaction
```
* Additional locations: not configured
* S3 role ARN: arn copied from previous step
* External ID: external id created in previous step (training_test)

![Create Catalog Dialog](assets/create-catalog-detailed-filledup.png)

Click **Create** and you will see the catalog streamnative created.

Select the Catalog Details tab and record the value of the IAM user arn. The Snowflake Open Catalog will use this arn to access our s3 bucket.

![Snowflake Open Catalog ARN](assets/snowflake-catalog-arn.png)

Next we trust the Snowflake Open Catalog Iam user arn.

In the AWS console, enter **Access management → Roles**, and search for the role we created before.

![Trust Snowflake Open Catalog ARN](assets/aws-access-management-roles.png)

Then click **Trust relationships → Edit trust policy**.

Change the value of Principal:AWS to the Snowflake Open Catalog IAM user arn

![Change AWS Principal](assets/change-aws-principal.png)

Then click **Update policy** and the Snowflake Open Catalog can access the s3 bucket.

### Provide StreamNative Access to Snowflake Open Catalog

Our StreamNative BYOC Ursa Cluster will need a connection to access the Snowflake Open Catalog. We will also reuse this connection for Snowflake AI Data Cloud to access Snowflake Open Catalog.

Click **+ Create** next to **Set Up Connections**.

![Create Snowflake Open Catalog Connection](assets/get-started-with-snowflake-open-catalog.png)

* Name: streamnativeconnection
* Query Engine: not configured
* Create new principal role: enable
* Principal Role Name: streamnativeprincipal

![Configure Service Connection](assets/configure-service-connection-snowflake-catalog.png)

Then click **Create**, and you will see a pane. Record the Client ID and Client Secret for this connection as **CLIENT ID:SECRET**. The StreamNative BYOC Ursa Cluster needs it to access the Snowflake Open Catalog.

![Service Connection Credential](assets/configure-clientid-secret-snowflake-open-catalog.png)

We now have a Service Connection called **streamnativeconnection** linked to the Principal Role **streamnativeprincipal**.

Next we create a Snowflake Catalog Role and link this to the Principal Role.

Enter **Catalogs → Select streamnative Catalog → Roles → + Catalog Role**.

* Name: streamnativeopencatalog
* Privileges:
```markdown
NAMESPACE_CREATE
NAMESPACE_LIST
TABLE_CREATE
TABLE_LIST
TABLE_READ_DATA
TABLE_WRITE_DATA
TABLE_READ_PROPERTIES
TABLE_WRITE_PROPERTIES
NAMESPACE_READ_PROPERTIES
NAMESPACE_WRITE_PROPERTIES
```
Click **Create**.

![Catalog Role Permissions](assets/create-catalog-role-snowflake.png)

Then click **Grant to Principal Role**.

![Grant Principal Role](assets/snowflake-grant-service-role.png)

* Catalog role to grant: streamnative_open_catalog_role
* Principal role to receive grant: streamnativeprincipal

Then click **Grant**.

![Grant Catalog Role](assets/grant-catalog-role-snowflake-image.png)

The catalog role **streamnative_open_catalog_role** now has the 10 required permissions on catalog streamnative. The catalog role **streamnative_open_catalog_role** is now linked to principal **streamnativeprincipal**.

We will resuse the connection when connecting Snowflake AI Data Cloud to Snowflake Open Catalog.

<!-- ------------------------ -->
## Create StreamNative Cluster

To proceed, you will need to first complete the steps for [granting vendor access, creating a Cloud Connection, and setting up the Cloud Environment](https://docs.streamnative.io/docs/byoc-overview). This process will grant StreamNative permissions into your cloud provider and deploy the required infrastructure before you begin the process of deploying a StreamNative BYOC Ursa Cluster. [This video](https://youtu.be/vsHjaQNKFRk?si=2pUJXE_s0LfzH3At) provides an overview of this process with detailed videos available in this [playlist](https://www.youtube.com/playlist?list=PL7-BmxsE3q4W5QnrusLyYt9_HbX4R7vEN).

Once this process is complete, [this video](https://www.youtube.com/watch?v=UQoyYSSSaDc) will also guide you through the process of deploying the StreamNative BYOC Ursa Cluster following the directions below.


### Create a StreamNative BYOC Ursa Cluster in StreamNative Cloud Console

In this section we create and set up a cluster in StreamNative Cloud. Login to StreamNative Cloud at [streamnative.io](https://streamnative.io) and click on **Create an instance and deploy cluster** or **+ New** in the **Select an instance** pane.

![Create StreamNative Instance](assets/create-new-streamnative-instance.png)

Click on **Deploy BYOC**.

![Deploy BYOC](assets/deploy-byoc.png)

Enter **Instance Name**, select your **Cloud Connection**, select **URSA Engine** and click on **Cluster Location**.

![Enter Instance Name](assets/enter-instance-name.png)

Enter **Cluster Name**, select your **Cloud Environment**, select **Multi AZ** and click on **Lakehouse Storage Configuration**.

![Enter Cluster Name](assets/enter-cluster-details-for-snowflake-catalog.png)

To configure **Storage Location** there are two options as previously discussed.

Option 1: Select **Use Your Own Bucket** (recommended) to choose your own storage bucket by entering the following details.

* AWS role arn (already created with Terraform module, obtain arn from AWS IAM)
* Region
* Bucket name
* Bucket path
* Confirm that StreamNative has been granted the necessary permissions to access your S3 bucket. The required permissions were granted by running a Terraform module.

![Enter Lakehouse Storage Configuration for User Bucket](assets/enter-lakehouse-storage-configuration.png)

Option 2: Select **Use Existing BYOC Bucket** to choose the bucket created by StreamNative.

![Enter Lakehouse Storage Configuration for Default Bucket](assets/use-existing-byoc-bucket.png)

If using the Streamnative povided bucket, the UI will present you with the SN Bucket Location in this format to be used when creating the Snowflake Open Catalog.

```markdown
s3://<your-cloud-environment-id>/<your-cluster-id>/compaction
e.g.
s3://aws-usw2-test-rni68-tiered-storage-snc/o-naa2l-c-vo06zqe-ursa/compaction
```
> 
> 
> IMPORTANT : If you are using the StreamNative provided bucket, do not close the browser while creating the catalog. This will cause StreamNative to create a new cluster id. Once a catalog is created in Snowflake Open Catalog, the base location and additional locations cannot be changed. If the cluster id changes, you would need to create a new catalog.

To integrate with Snowflake Open Catalog, Enable Catalog Integration and select Snowflake Open Catalog.

* **Warehouse:** catalog created in Snowflake Open Catalog
* **URI:** Account URL when creating Snowflake Open Catalog. Append ***'/polaris/api/catalog'*** to the URI. See screenshot below.
* **Select Authentication Type/OAuth2:** create a new secret in StreamNative using Snowflake Open Catalog Service Connection "CLIENT ID:SECRET"

![Enable Snowflake Open Catalog Integration](assets/enable-snowflake-open-catalog.png)

Clicking **Cluster Size** will test the connection to the s3 bucket and the Snowflake Open Catalog.

![Test Connection](assets/click-deploy.png)

Click **Continue** to begin sizing your cluster.

For this example, we deploy using the smallest cluster size. Click **Finish** to start deploying the StreamNative BYOC Ursa Cluster into your Cloud Environment.

![Cluster Sizing](assets/cluster-sizing.png)

When cluster deployment is complete, it will appear on the Organization Dashboard with a green circle.

![View Deployed Cluster](assets/view-organization-dashboard.png)

The Lakehouse Storage configuration can be viewed by clicking on the Instance on the Organization Dashboard and selecting Configuration in the left pane.

![View Lakehouse Storage Configuration](assets/view-lakehouse-storage-configuration.png)

### Produce Kafka Messages to Topic with AVRO Schema

We will use the Kafka Java Client to produce Kafka messages with an AVRO schema to a topic.

To obtain Kafka Java Client code for publishing messages to the server, navigate to **Kafka Clients** page in StreamNative UI. After selecting **Java**, click **Next**.

![Kafka Clients Page](assets/kafkaclient1.png)

Under Select service account, open the dropdown and select **+ Create Service Account** and follow the prompts to create a new service account.

![Create Service Account](assets/kafkaclient2.png)

Under Select authentication type, select **API Key** and click **+ Create API Key**.

![Select Authentication Type](assets/kafkaclient3.png)

Provide a name for the API Key. Be sure to select the Instance of our newly-created StreamNative BYOC Instance. API Keys are associated with a specific Instance.

![Create New API Key](assets/kafkaclient4.png)

Copy the API Key in case you need it for later use. It will be automatically populated in the producer code we obtain from the UI.

![Copy API Key](assets/kafkaclient5.png)

Select the **default** endpoint of our cluster and click **Next**. Most likely you will only have the default endpoint.

![Select default Endpoint](assets/kafkaclient6.png)

**Enable** schema registry and click **Next**.

![Enable Schema Registry](assets/kafkaclient7.png)

Copy the dependencies for your Maven project for use in the pom.xml and click **Next**.

![Copy Maven Dependencies and Repositories](assets/kafkaclient8.png)

Select the **public** tenant and **default** namespace. Select the topic dropdown and click **+ Create topic** to create a new topic.

![Select Tenant, Namepsace, and Topic](assets/kafkaclient9.png)

Provide a topic name and click **New Topic**.

![Create New Topic](assets/kafkaclient10.png)

The producer code is configured to use an AVRO schema, prepopulated with the API key, tenant name, namespace, topic name, and cluster endpoints for the both producing messages and registering the schema. Copy the producer code for use in your Java IDE.

![Copy Producer Code](assets/kafkaclient11.png)

In this example we created a new project in IntelliJ. We have pasted in the dependencies and repositories into the pom.xml and reloaded the project to download the dependencies.

![Edit POM File](assets/kafkaclient12.png)

We created a new class called SNCloudTokenProducer and pasted in the Kafka Java Client code from the StreamNative UI.
After executing the Kafka Java Client code, the terminal prints the following:

```
Send hello to kafkaschematopic4-0@0
```

![Successfully Run Java Code](assets/kafkaclient13.png)

### Review s3 bucket

Navigate to the user provided or StreamNative provided s3 bucket. In this example the user provided bucket is s3://streamnativeopencatalog/test. A storage folder and compaction folder have been created by the cluster.

![Review S3 Bucket](assets/review-s3-bucket.png)

We published messages to multiple topics in the public/default tenant/namespace. We see folders for the tenant, namespace, and each topic inside the compaction folder.

![View Topics in S3 Bucket](assets/view-data-in-s3-bucket.png)

Inside each topic folder, we find partition and metadata folders.

![View Partitions and Metadata](assets/view-partitions-and-metadata-folders.png)

### Verify Tables and Schema are Visible in Snowflake Open Catalog

Once the compaction folder has been created in the s3 bucket, we can verify the tables and schemas are visible in Snowflake Open Catalog. We can see the resulting tables created in streamnative/public/default with a registered schema.

![Verify Tables and Schema](assets/verify-tables-and-schemas.png)

The data is now queryable through Snowflake Open Catalog. In the following step we will configure Snowflake AI Data Cloud to query tables from Snowflake Open Catalog.

## Query Tables with Snowflake

Querying a table in Snowflake Open Catalog using Snowflake AI Data Cloud requires completing the following [from the Snowflake documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg-open-catalog-query).

[This video](https://www.youtube.com/watch?v=658ZV78lyew) shows detailed queries for our example. Exact queries used are also available below. Please refer to Snowflake documentation for any changes in creating an external volume, creating a catalog integration, and creating an externally managed table.


### Create an external volume in Snowflake

Please refer to the [Snowflake documentation here](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3) for the latest code samples for creating an external volume.

The video includes the following details from our example:
* When creating the new policy for Snowflake to access the s3 bucket, use root of the s3 bucket to avoid a list error when verifying storage access.
* When creating an external volume in Snowflake, for STORAGE_BASE_URL use the complete bucket path with s3://<>/<>/compaction.

The following query was used to create the external volume.

```sql
CREATE OR REPLACE EXTERNAL VOLUME streamnative_external_volume
   STORAGE_LOCATIONS =
      (
         (
            NAME = 'my_streamnative_external_volume'
            STORAGE_PROVIDER = 'S3'
            STORAGE_BASE_URL = 's3://streamnativeopencatalog/test/compaction/'
            STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::180941968709:role/streamnativeopencatalogaccessrole3'
            STORAGE_AWS_EXTERNAL_ID = 'training_test'
         )
      );
```

The following query was used to describe the external volume to obtain the IAM role arn used by Snowflake AI Data Cloud to query the s3 bucket.

```sql
DESC EXTERNAL VOLUME streamnative_external_volume;
```

The following query was used to verify Snowflake AI Data Cloud has access to the s3 bucket.

```sql
SELECT SYSTEM$VERIFY_EXTERNAL_VOLUME('streamnative_external_volume');
```

### Create a catalog integration for Open Catalog

Please refer to the [Snowflake documentation here](https://docs.snowflake.com/en/user-guide/tables-iceberg-open-catalog-query) for the latest code samples.

The video includes the following details from our example:
* The CATALOG_NAMESPACE refers to the tenant.namespace in our StreamNative Cluster. Since we published messages to public.default, use public.default as the CATALOG_NAMESPACE.
* We can resuse the CLIENT ID:SECRET for Snowflake Open Catalog to allow access for Snowflake. The CLIENT ID refers to OAUTH_CLIENT_ID and SECRET refers to OAUTH_CLIENT_SECRET.

The following query is used to create a catalog integration for public.default.

```sql
CREATE OR REPLACE CATALOG INTEGRATION oc_int
  CATALOG_SOURCE = POLARIS
  TABLE_FORMAT = ICEBERG
  CATALOG_NAMESPACE= 'public.default'
  REST_CONFIG = (
    CATALOG_URI = 'https://a9727308406271-trainingopencatalog.snowflakecomputing.com/polaris/api/catalog'
    WAREHOUSE = 'streamnative'
  )
  REST_AUTHENTICATION = (
    TYPE = OAUTH
    OAUTH_CLIENT_ID = '<client id>'
    OAUTH_CLIENT_SECRET = '<client secret>'
    OAUTH_ALLOWED_SCOPES = ( 'PRINCIPAL_ROLE:ALL' )
  )
 ENABLED = TRUE;
```

You will need to create a new catalog integration for each tenant.namespace.

### Create an externally managed table

Please refer to the [Snowflake documentation here](https://docs.streamnative.io/docs/integrate-with-snowflake-open-catalog) for the latest code samples.

The video includes the following details from our example:
* A Snowflake Open Catalog warehouse.schema.table (e.g. streamnative.public.default.kafkaschematopic) is mapped to a Snowflake database.schema.table (e.g. training.public.kafkaschematopic)
* Use AUTO_REFRESH = TRUE; in CREATE ICEBERG TABLE to ensure new data is viewable in Snowflake.

The following query was used to create an externally managed table.

```sql
CREATE ICEBERG TABLE kafkaschematopic
CATALOG = 'oc_int'
EXTERNAL_VOLUME = 'streamnative_external_volume'
CATALOG_TABLE_NAME = 'kafkaschematopic'
AUTO_REFRESH = TRUE;
```
You will need to create a new externally managed table for each topic.

Once completing these steps, you will be able to query the Iceberg Table registered in Snowflake Open Catalog through Snowflake AI Data Cloud.

The following are example queries for viewing the data in Snowflake AI Data Cloud.

```sql
select * FROM TRAINING.PUBLIC.kafkaschematopic LIMIT 10

select COUNT(*) FROM TRAINING.PUBLIC.kafkaschematopic
```

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations on creating a Streaming Augmented Lakehouse powered by StreamNative's Ursa Engine with built-in support for Iceberg and Snowflake Open Catalog. [Contact StreamNative](https://streamnative.io/contact) to learn more.

### What You Learned
- How to create a Snowflake Open Catalog
- How to deploy a StreamNative BYOC Ursa Cluster integrated with Snowflake Open Catalog
- How to publish Kafka messages to the StreamNative Ursa Cluster using Kafka Java Client
- How to query tables visible in Snowflake Open Catalog in Snowflake AI Data Cloud

### Resources
- [Streamnative Snowflake Open Catalog Documentation](https://docs.streamnative.io/docs/integrate-with-snowflake-open-catalog)
- [StreamNative Developer Portal](https://streamnative.io/dev-portal)
- [StreamNative Academy YouTube Channel](https://www.youtube.com/@streamnativeacademy8484)
- [StreamNative Academy Courses](https://courses.streamnative.io/)

author: Jake Berkowsky
id: vpc_flow_log_ingestion
summary: This tutorial is a guide for ingestion AWS VPC Flowlogs into Snowflake. It demonstrates configuration of VPC flowlogs on AWS, ingestion using an external stage with Snowpipe and sample queries for CSPM and threat detection.
categories: Cybersecurity
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cybersecurity, SIEM, CSPM, VPC Flow Logs

# AWS VPC Flow Logs Ingestion

## Overview 
Duration: 3

VPC Flow Logs is a feature that enables you to capture information about the IP traffic going to and from network interfaces in your VPC. 
Flow logs can help you with a number of tasks, such as:

- Monitoring the traffic that is reaching your instance
- Determining the direction of the traffic to and from the network interfaces
- Analyzing properties such as IP addresses, ports, protocol and total packets sent without the overhead of taking packet captures

Flow log data is collected outside of the path of your network traffic, and therefore does not affect network throughput or latency. You can create or delete flow logs without any risk of impact to network performance.

This tutorial is a guide for ingestion AWS VPC Flowlogs into Snowflake. It demonstrates configuration of VPC flowlogs on AWS, ingestion using an external stage with Snowpipe and sample queries for CSPM and threat detection.

### Prerequisites
- AWS user with permission to create and manage IAM policies and roles
- Snowflake user with permission to create tables, stages and storage integrations as well as setup snowpipe.
- An S3 Bucket

### Architecture
![A diagram depicting the journey of VPC Flow Logs from an Amazon VPC to a snowflake database. The diagram is split between sections, AWS Cloud and Snowflake Cloud. The diagram begins on the AWS Cloud side at Amazon VPC, an arrow leads to VPC Flow Logs, then to S3 External Stage, then to an SQS Queue with the description “Event Notification”. An arrow leads from the SQS queue to the Snowflake Cloud section of the diagram to an icon named Snowpipe. After Snowpipe the arrow leads back to S3 External stage with a description of “triggers”. Finally the path terminates on the Snowflake Cloud side at an icon named “Snowflake DB” with a description of “copy into”.](assets/vpc-flow-arch.png)

## Enable VPC Flow Logs and Push to S3
Duration: 5

_See [here](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-s3.html#flow-logs-s3-create-flow-log) for more detailed instructions or for more granular VPC flow use cases._

From the VPC page in the AWS console, select the VPC you wish to enable flow logs on. Select the “Flow Logs” tab and press “Create flow log”

![A screenshot of the Amazon VPC console with a VPC selected and the Flow Logs tab open](assets/vpc.png)

Configure VPC flow logs as desired. Ensure the following settings:

- **Destination:** Send to an Amazon S3 Bucket
- **S3 Bucket ARN:**  S3 Bucket ARN and prefix of existing bucket ( or press the “create s3 bucket” link to create a new one)
- **Log Record Format:** The later parts of this tutorial assume the default log format, a full list of available fields can be found here: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html#flow-logs-fields
- **Log file format:** Parquet

![A screenshot of the VPC configuration wizard with the above configuration](assets/vpc-flow-configuration.png)

## Create a storage integration in Snowflake
Duration: 5

*Replace \<RoleName\> with the desired name of the role you’d like snowflake to use ( this role will be created in the next step).  Replace \<BUCKET_NAME\>/path/to/logs/ with the path to your VPC flow logs as set in the previous step*

```sql
create STORAGE INTEGRATION s3_int_vpc_flow
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<AWS_ACCOUNT_NUMBER>:role/<RoleName>'
  STORAGE_ALLOWED_LOCATIONS = ('s3://<BUCKET_NAME>/<PREFIX>/');

DESC INTEGRATION s3_int_vpc_flow;
```
Take note of **STORAGE_AWS_IAM_USER_ARN** and **STORAGE_AWS_EXTERNAL_ID**

![A screenshot showing the result of describing an integration. STORAGE_AWS_IAM_USER_ARN property is in the format of an aws ARN set to arn:aws:iam::123456789012:user/abc10000-a and the STORAGE_AWS_EXTERNAL_ID is in the format of ABC12345_SFCRole=1 ABCDEFGHIJKLMNOPORSTUVWXYZab= ](assets/generic-integration-screenshot.png)

## Create role and policy in AWS
Duration: 5

*The following assumes a user with the ability to create and manage IAM logged into the AWS console or using the CLI.  A full explanation can be found in [this documentation](https://docs.snowflake.com/en/user-guide/data-load-s3-config.html)*

Open up Cloudshell in the AWS console by pressing the ![aws cloudshell icon](assets/generic-aws-cloudshell-icon.png) icon on the right side of the top navigation bar or run the following commands in your terminal once configured to use the AWS CLI.

Export the following variables, replacing the values with your own

```bash
export BUCKET_NAME='<BUCKET_NAME>'
export PREFIX='<PREFIX>' # no leading or trailing slashes
export ROLE_NAME='<ROLE_NAME>'
export STORAGE_AWS_IAM_USER_ARN='<STORAGE_AWS_IAM_USER_ARN>'
export STORAGE_AWS_EXTERNAL_ID='<STORAGE_AWS_EXTERNAL_ID>'
```
Create a role for Snowflake to assume
```bash
aws iam create-role \
    --role-name "${ROLE_NAME}" \
    --assume-role-policy-document \
'{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "AWS": "'${STORAGE_AWS_IAM_USER_ARN}'"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "'${STORAGE_AWS_EXTERNAL_ID}'"
                }
            }
        }
    ]
}'
```
Create an inline-policy to allow snowflake to add and remove files from S3

```bash
aws iam put-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-name "${ROLE_NAME}-inlinepolicy" \
    --policy-document \
'{
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
            "Resource": "arn:aws:s3:::'${BUCKET_NAME}'/'${PREFIX}'/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::'${BUCKET_NAME}'",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "'${PREFIX}'/*"
                    ]
                }
            }
        }
    ]
}'
```
You will now be able to see your role, policy and trust relationship in the console

![Screenshot of snowflake source displayed in AWS IAM](assets/generic-aws-iam.png)

## Prepare Snowflake to receive data
Duration: 10

This quickstart requires a warehouse to perform computation and ingestion. We recommend creating a separate warehouse for security related analytics if one does not exist. The following will create a medium sized single cluster warehouse that suspends after 5 minutes of inactivity. For production workloads a larger warehouse will likely be required.

```sql
create warehouse security_quickstart with 
  WAREHOUSE_SIZE = MEDIUM 
  AUTO_SUSPEND = 300;
```

Create External Stage using the storage integration
```sql
create stage vpc_flow_stage
  url = 's3://<BUCKET_NAME>/<PREFIX>/'
  storage_integration = s3_int_vpc_flow
;
```

Check if snowflake can list S3 files
```sql
list @vpc_flow_stage;
```
![Screenshot of listing files in external stage](assets/generic-list-source-stage-s3.png)

```sql
create table public.vpc_flow(
  record VARIANT
);
```
Test Injection from External Stage
```sql
copy into public.vpc_flow
  from @vpc_flow_stage
  file_format = (type = parquet);
```

![Screenshot showing result of above copy into command, for all files the status column shows "LOADED"](assets/generic-copy-from-s3-stage.png)

Select data
```sql
select * from public.vpc_flow limit 10;
```
![Screenshot showing vpc flowlogs in snowflake](assets/vpc-flow-select.png)

## Setup Snowpipe for continuous loading
Duration: 5




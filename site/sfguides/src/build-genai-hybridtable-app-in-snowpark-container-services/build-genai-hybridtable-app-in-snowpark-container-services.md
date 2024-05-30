id: build-genai-hybridtable-app-in-snowpark-container-services
summary: Build GenAI HybridTable App in Snowpark Container Services
categories: featured,getting-started,app-development,gen-ai,snowpark-container-services,hybrid-table
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Snowpark Container Services,Gen AI,Hybrid Table
authors: Dash Desai

# Build Genai Hybrid Table App In Snowpark Container Services

<!-- ------------------------ -->

## Overview

Duration: 5

By completing this guide, you will be able to build a Gen AI application running in [Snowpark Container Services (SPCS)](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview) and use of [Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid) within the application.

![Demo](assets/demo.mov)

### What You Will Learn

- Build a Gen AI application
- Deploy and Run the application using Snowpark Container Services (SPCS)
- Use Hybrid Tables within the Application

### Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
- [Snowflake](https://signup.snowflake.com) Account with SPCS (+ the ability to create GPU compute pool) and Hybrid Tables enabled. Check [SPCS availability](https://docs.snowflake.com/developer-guide/snowpark-container-services/overview#).
- [Docker for Desktop](https://docs.docker.com/desktop)
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/index) **Optional**

<!-- ------------------------ -->

## Setup Environment

Duration: 5

### Clone Repository

Clone the companion repository on to your local machine,

```shell
git clone https://github.com/Snowflake-Labs/sfguide-build-genai-hybridtable-app-in-snowpark-container-services.git
cd sfguide-build-genai-hybridtable-app-in-snowpark-container-services
```

Let us export the demo source code path to a environment variable `$DEMO_HOME` and refer it with is name for the rest of the guide,

```shell
DEMO_HOME="$PWD"
```

### Create DB, Schema, Warehouse, Tables, Role And Other Objects

Log into your Snowflake account and run the following SQL to create the required objects,

```sql

use role ACCOUNTADMIN;

create database DASH_DB;
create schema DASH_SCHEMA;
create warehouse DASH_WH_S WAREHOUSE_SIZE=SMALL;

use database DASH_DB;
use schema DASH_SCHEMA;
use warehouse DASH_WH_S;

create stage DASH_STAGE;
create image repository DASH_REPO;

create security integration SNOWSERVICES_INGRESS_OAUTH
  type=oauth
  oauth_client=snowservices_ingress
  enabled=true;

create compute pool DASH_GPU3
min_nodes = 1
max_nodes = 2
instance_family = GPU_3
auto_suspend_secs = 7200;

create stage llm_workspace encryption = (type = 'SNOWFLAKE_SSE');

create or replace hybrid table cell_towers_ca (
  tower_id int unique primary key,
  tower_name varchar(255),
  lat float,
  lon float,
  status varchar(30),
  status_message varchar(256),
  last_comm datetime,
  maintenance_due datetime
);

create or alter table images (
    id int autoincrement,
    site_name string,
    city_name string,
    file_name string,
    lat float,
    lon float,
    image_bytes string
);

create role DASH_SPCS;
grant usage on database DASH_DB to role DASH_SPCS;
grant all on schema DASH_SCHEMA to role DASH_SPCS;
grant create service on schema DASH_SCHEMA to role DASH_SPCS;
grant usage on warehouse DASH_WH_S to role DASH_SPCS;
grant READ,WRITE on stage DASH_STAGE to role DASH_SPCS;
grant READ,WRITE on image repository DASH_REPO to role DASH_SPCS;
grant all on compute pool DASH_GPU3 to role DASH_SPCS;
grant bind service endpoint on account to role DASH_SPCS;
grant monitor usage on account to role DASH_SPCS;
grant READ,WRITE on stage llm_workspace to role DASH_SPCS;
grant all on table cell_towers_ca to role DASH_SPCS;
grant all on table images to role DASH_SPCS;

CREATE OR REPLACE NETWORK RULE allow_all_rule
  TYPE = 'HOST_PORT'
  MODE= 'EGRESS'
  VALUE_LIST = ('0.0.0.0:443','0.0.0.0:80');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION ALLOW_ALL_ACCESS_INTEGRATION
  ALLOWED_NETWORK_RULES = (allow_all_rule)
  ENABLED = true;

GRANT USAGE ON INTEGRATION ALLOW_ALL_ACCESS_INTEGRATION TO ROLE DASH_SPCS;
```

> aside positive
> TIP: You can also run the entire script using Snowflake CLI
>
> ```shell
> snow sql sql -c <your connection name> --filename "$DEMO_DIR/setup.sql"
>
> ```

### Load Data

Duration: 15

Log into your Snowflake account and use Snowsight to load data from the `$DEMO_DIR/data` into newly created `cell_towers_ca` and `images` tables.

For both of the tables, select the following in the UI:

- `Header: 'Skip first line'`
- `Field optionally enclosed by: 'Double quotes'`

> **TODO**: Will it be OK to add a local internal stage and load the data form stage?? if not remove the following section

Upload the data to internal stage named `demo_app_data`

```sql
CREATE OR REPLACE STAGE DASH_DB.DASH_SCHEMA.demo_app_data;
PUT file://./data/cell_towers_ca.csv;
PUT file://./data/images.csv;
```

Create a File Format to load the data from CSV,

```sql
CREATE OR REPLACE FILE FORMAT DASH_DB.DASH_SCHEMA.NO_HEADER_QUOTED_CSV
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1;
```

Load the data into `cell_towers_ca` table,

```sql
COPY INTO cell_towers_ca
FROM DASH_DB.DASH_SCHEMA.demo_app_data/cell_towers_ca.csv
FILE_FORMAT = 'DASH_DB.DASH_SCHEMA.NO_HEADER_QUOTED_CSV'
```

Load the data into `images` table,

```sql
COPY INTO cell_towers_ca
FROM DASH_DB.DASH_SCHEMA.demo_app_data/images.csv
FILE_FORMAT = 'DASH_DB.DASH_SCHEMA.NO_HEADER_QUOTED_CSV'
```

## Build Docker Image

Duration: 30

Make sure Docker is running and then in a terminal window, browse to `$DEMO_DIR` and execute the following command to build the Docker image.

> aside negative
> **NOTE**: The first time you build the image it can take about ~45-60mins.

```shell
DOCKER_BUILDKIT=0 docker build --platform linux/amd64 -t genai-spcs .
```

### Tag and Push Docker Image to Snowflake Registry

Set few variables for convenience,

```shell
## TODO:DB Name and Schema will come here??
export SNOWFLAKE_REGISTRY_URL='<account_alias>.registry.snowflakecomputing.com'
# e.g.
# <account_alias>.registry.snowflakecomputing.com/dash_db/dash_schema/dash_repo/genai-spcs
export IMAGE_REPO=<your image name>
export IMAGE_TAG=latest
```

Execute the following command to tag the image,

```shell

docker tag genai-spcs:latest "$IMAGE_REPO:$IMAGE_TAG"
```

Execute the following command to login to your Snowflake account that's enabled for SPCS,

```shell
docker login $SNOWFLAKE_REGISTRY_URL
```

Finally push the image to Snowflake registry.

```shell
docker push "$IMAGE_REPO:$IMAGE_TAG"
```

## Snowpark Container Services (SPCS) Setup

Assuming you were able to successfully push the Docker image just fine, follow the steps below to deploy and run the application in SPCS.

### Update SPCS Specification File

Update the `$DEMO_DIR/genai-spcs.yaml` with the image built during the Docker Setup step,

```yaml
spec:
  container:
    - name: genai-spcs
      # !!!IMPORTANT!!! Replace it with "$IMAGE_REPO:$IMAGE_TAG"
      image: '$IMAGE_REPO:$IMAGE_TAG'
      volumeMounts:
        - name: llm-workspace
          mountPath: /notebooks/llm-workspace
      env:
        SNOWFLAKE_MOUNTED_STAGE_PATH: /notebooks/llm-workspace
      resources:
        requests:
          nvidia.com/gpu: 1
        limits:
          nvidia.com/gpu: 1
  endpoint:
    - name: streamlit
      port: 8080
      public: true
    - name: jupyter
      port: 4200
      public: true
  volume:
    - name: llm-workspace
      source: '@llm_workspace'
      uid: 0
      gid: 0
```

> aside positive
> **TIP**: If you have [envsubst](https://www.man7.org/linux/man-pages/man1/envsubst.1.html) installed(`brew install gettext`) then you can do the following to update the SPCS YAML like,
>
> ```shell
>  envsubst < $DEMO_DIR/genai-spcs.yaml > $DEMO_DIR/genai-spcs-updated.yaml
> ```

### Create Service

In Snowsight, execute the following SQL statements to create and launch the service,

```sql
use role DASH_SPCS;

-- Check compute pool status
show compute pools;
-- If compute pool is not ACTIVE or IDLE, uncomment and run the following alter command
-- alter compute pool DASH_GPU3 resume;

-- NOTE: Do not proceed unless the compute pool is in ACTIVE or IDLE state

-- Create GenAI service in SPCS
create service genai_service
IN COMPUTE POOL DASH_GPU3
FROM @dash_stage
SPECIFICATION_FILE = 'genai-spcs.yaml'
MIN_INSTANCES = 1
MAX_INSTANCES = 1
QUERY_WAREHOUSE = DASH_WH_S
EXTERNAL_ACCESS_INTEGRATIONS = (ALLOW_ALL_ACCESS_INTEGRATION);
```

### Check Service Status

Execute the following SQL statement and check the status of the service to make sure it's in `READY` state before proceeding.

```sql
select
  v.value:containerName::varchar container_name
  ,v.value:status::varchar status
  ,v.value:message::varchar message
from (select parse_json(system$get_service_status('genai_service'))) t,
lateral flatten(input => t.$1) v;
```

> aside negative
> **IMPORTANT**: Do not proceed further unless the service is in `READY` state

### Get the Public Endpoint

Assuming compute pool is in `IDLE` or `ACTIVE` state and the service is in `READY` state, execute the following SQL statement to get the public endpoint of the application(service).

```shell
show endpoints in service genai_service;
```

If everything has gone well, you should see a service named Streamlit with `ingress_url` of the application--something similar to `iapioai5-sfsenorthamerica-build-spcs.snowflakecomputing.app`

<!-- ------------------------ -->

## Run Application

Duration: 5

In a new browser window, copy-paste the ingress_url URL from previous step and you should see the login screen. To launch the application, enter your Snowflake credentials and you should see the application up and running!

### Gen AI Inpainting

On this page, use your mouse to paint the area white where you'd like a cell phone tower to be built.
Then click on Generate Image button -- this will kickoff a inpainting process using open source Gen AI model. In a few seconds the generated image will be displayed on the right-hand side of the selected image!

### Tower Uptime

On this page, update status of one of the towers in the dataframe on the right. This will kickoff a process to updated the hybrid table and also update the map instantaneously.

<!-- ------------------------ -->

## Conclusion And Resources

Duration: 3

Congratulations! You've successfully built a Gen AI application, deployed it using Snowpark Container Services(SPCS) and used Hybrid Table as part of the application.

We would love your feedback on this QuickStart Guide! Please submit your feedback using this [Feedback Form](https://forms.gle/XKd8rXPUNs2G1yM28).

### What You Learned

- How to Build a Gen AI application
- Deploy and run the application using Snowpark Container Services (SPCS)
- Use Hybrid Tables within the Application

### Related Resources

- [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-build-genai-hybridtable-app-in-snowpark-container-services.git)
- [Intro to Snowpark Container Services](https://quickstarts.snowflake.com/guide/intro_to_snowpark_container_services/index.html?index=../..index#0)
- [All about the new Snowflake Hybrid Tables](https://medium.com/snowflake/all-about-the-new-snowflake-hybrid-tables-fe8d09c448e4)
- [Snowflake Cortex LLM](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Snowflake Cortex ML Functions](https://quickstarts.snowflake.com/guide/ml_forecasting_ad/index.html?index=../..index#6)

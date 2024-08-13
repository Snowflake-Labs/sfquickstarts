author: Charlie Hammond
id: notebook-container-runtime
summary: This guide will walk show you how to use Snowflake Notebooks with Container Runtime
categories: data-science, data-science-&-ml, Getting-Started, Notebooks
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science

# Getting Started with Snowflake Notebook Container Runtime
<!-- ------------------------ -->
## Overview 
Duration: 1

You can run Snowflake Notebooks on Snowpark Container Services through Container Runtime. Snowpark Container Services gives you a flexible container infrastructure that supports building and operationalizing a wide variety of workflows entirely within Snowflake. Container Runtime provides software and hardware options to support advanced data science and machine learning workloads on Snowpark Container Services. Compared to Virtual warehouses, Container Runtime provides a more flexible compute environment where you can install packages from multiple sources and select compute resources, including GPU machine types, while still running SQL queries on warehouses for optimal performance.

This Quickstart will take you through the steps of running Snowflake Notebooks with Container Runtime. We will install packages, train a model using pre-installed packages, and view logs.

### Prerequisites
- Access to a Snowflake account with Accountadmin. 
- Access to run Notebooks in Snowflake
- Foundational knowledge of Data Science workflows

### What You Will Learn 
- The key features of Snowflake Notebooks with Container Runtime

### What You’ll Need 
- A [Snowflake](https://app.snowflake.com/) Account

### What You’ll Build 
- A Snowflake Notebook that runs on Snowpark Container Services

<!-- ------------------------ -->
## Setup Your Account
Duration: 2

Complete the following steps to setup your account:
- Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".
- Paste and the following SQL in the worksheet 
- Adjust <YOUR_USER> to your user
- Run all commands to create Snowflake objects

```sql
USE ROLE accountadmin;
CREATE DATABASE container_runtime_lab;
CREATE SCHEMA notebooks;

CREATE OR REPLACE ROLE container_runtime_lab_user;
GRANT ROLE container_runtime_lab_user to USER <YOUR_USER>;

GRANT USAGE ON DATABASE container_runtime_lab TO ROLE container_runtime_lab_user;
GRANT ALL ON SCHEMA container_runtime_lab.notebooks TO ROLE container_runtime_lab_user;
GRANT CREATE STAGE ON SCHEMA container_runtime_lab.notebooks TO ROLE container_runtime_lab_user;
GRANT CREATE NOTEBOOK ON SCHEMA container_runtime_lab.notebooks TO ROLE container_runtime_lab_user;
GRANT CREATE SERVICE ON SCHEMA container_runtime_lab.notebooks TO ROLE container_runtime_lab_user;

CREATE OR REPLACE WAREHOUSE CONTAINER_RUNTIME_WH AUTO_SUSPEND = 60;
GRANT ALL ON WAREHOUSE CONTAINER_RUNTIME_WH TO ROLE container_runtime_lab_user;

-- Create and grant access to compute pools
CREATE COMPUTE POOL cpu_xs_5_nodes
  MIN_NODES = 1
  MAX_NODES = 5
  INSTANCE_FAMILY = CPU_X64_XS;

CREATE COMPUTE POOL gpu_s_5_nodes
  MIN_NODES = 1
  MAX_NODES = 5
  INSTANCE_FAMILY = GPU_NV_S;

GRANT USAGE ON COMPUTE POOL cpu_xs_5_nodes TO ROLE container_runtime_lab_user;
GRANT USAGE ON COMPUTE POOL gpu_s_5_nodes TO ROLE container_runtime_lab_user;

-- Create and grant access to EAIs
-- Substep #1: create network rules (these are schema-level objects; end users do not need direct access to the network rules)

create network rule allow_all_rule
  TYPE = 'HOST_PORT'
  MODE= 'EGRESS'
  VALUE_LIST = ('0.0.0.0:443','0.0.0.0:80');

-- Substep #2: create external access integration (these are account-level objects; end users need access to this to access the public internet with endpoints defined in network rules)

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION allow_all_integration
  ALLOWED_NETWORK_RULES = (allow_all_rule)
  ENABLED = true;

CREATE OR REPLACE NETWORK RULE pypi_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org',  'files.pythonhosted.org');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
  ALLOWED_NETWORK_RULES = (pypi_network_rule)
  ENABLED = true;

GRANT USAGE ON INTEGRATION allow_all_integration TO ROLE container_runtime_lab_user;
GRANT USAGE ON INTEGRATION pypi_access_integration TO ROLE container_runtime_lab_user;

```

<!-- ------------------------ -->
## Import Data
Next, we will upload the diamonds.csv dataset.

- Download diamonds.csv here
- Change role to container_runtime_lab_user
- In Snowsight, navigate to Data >> Databases and select container_runtime_lab.notebooks 
- Select Create >> Table >> From File >> Standard in the top right, and upload the diamonds.csv dataset.
- Update columns `row` to `"ROW"` and `table` to `"TABLE"`

![upload-diamonds](assets/upload-diamonds.png)

<!-- ------------------------ -->
## Run the Notebook
Duration: 15

- Download the notebook from this link
- Change role to CONTAINER_RUNTIME_LAB_USER
- Navigate to Projects > Notebooks in Snowsight
- Click Import .ipynb from the + Notebook dropdown
- Create a new notebok with the following settings
  - Notebook Location: CONTAINER_RUNTIME_LAB, NOTEBOOKS
  - Run On Container
  - Snowflake ML Runtime GPU 1.0
  - GPU_S_5_NODES

![create-notebooks](assets/import-container-notebook.png)

- Click the three dots in the top right > Notebook Settings
- Enable the PYPI_ACCESS_INTEGRATION

![pypi-integration](assets/pypi_access.png)

- Run cells in the notebook!

![container-runtime-preview](assets/container_runtime_overview.png)

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

In conclusion, running Snowflake Notebooks on Snowpark Container Services through Container Runtime offers a robust and flexible infrastructure for managing advanced data science and machine learning workflows directly within Snowflake. With the ability to install external packages and choose optimal compute resources, including GPU machine types, Container Runtime provides a more versatile environment compared to Virtual Warehouses.

Ready to get started? Follow this Quickstart to begin running Snowflake Notebooks with Container Runtime, install essential packages, train your models, and monitor your logs effectively.

### What You Learned
- The key features of Snowflake Notebooks with Container Runtime

### Related Resources
- [Documentation](https://docs.snowflake.com/LIMITEDACCESS/snowsight-notebooks/ui-snowsight-notebooks-runtime)
- [YouTube Tutorials](https://www.youtube.com/playlist?list=PLavJpcg8cl1Efw8x_fBKmfA2AMwjUaeBI)

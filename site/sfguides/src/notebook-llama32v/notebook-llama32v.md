author: Rajiv Shah
id: notebook-llama32v
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/model-development
language: en
summary: This guide will walk show you how to use LLama 3.2 Vision Models on Snowflake Notebooks with Container Runtime with Transformers 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Llama 3.2 Vision Models on Snowflake Notebooks
<!-- ------------------------ -->
## Overview 

Leverage the LLama 3.2 Vision models with Snowflake Notebooks on Snowpark Container Services through Container Runtime. This quickstart will show you how you can:

- Turn an image into text
- Turn an image of a table into a JSON representation.
- Understand an invoice document

This is possible by combining the latest vision language models with Snowpark Container Services, which gives you a flexible container infrastructure for supporting AI/ML workloads. 

This Quickstart will guide you through the steps of running Snowflake Notebooks with Container Runtime. Once you have a GPU enabled runtime, you can then use the attached notebook to start using the Llama 3.2 Vision model using Transformers. Additionally, once you setup your container environment, this notebook will support using other Transformers models with some slight modifications.

### Prerequisites
- Access to a Snowflake account with Accountadmin. 
- Access to run Notebooks in Snowflake
- Foundational knowledge of Data Science workflows
- Requested access to the Meta models at Hugging Face
- Hugging Face User Access Token (Make sure it's _read_ only, not _finegrained_)
- Running the 11b version of the model requires > 30GB of GPU memory
- You make need to get permsissions to access the medium GPU compute pool

### What You Will Learn 
- The key features of Snowflake Notebooks with Container Runtime
- Using models with Hugging Face Transformers

### What You’ll Need 
- A [Snowflake](https://app.snowflake.com/) Account
- A [Hugging Face](https://huggingface.co/) Account

### What You’ll Build 
- A Snowflake Notebook that runs on Snowpark Container Services
- Perform inference or predictions to convert text/images to text using the Llama 3.2 Vision model

<!-- ------------------------ -->
## Setup Your Account

Complete the following steps to setup your account:
- Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".
- Paste the following SQL in the worksheet 
- Adjust <YOUR_USER> to your user
- Run all commands to create Snowflake objects
- Part of this is creating the external integration for installing libraries and downloading models

```sql
USE ROLE accountadmin;
CREATE OR REPLACE DATABASE container_runtime_lab;
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
-- If you get errors about limits, reduce the number of nodes in the compute pools
CREATE COMPUTE POOL IF NOT EXISTS gpu_nv_m_nodes
  MIN_NODES = 1
  MAX_NODES = 3
  INSTANCE_FAMILY = GPU_NV_M;

GRANT USAGE ON COMPUTE POOL gpu_nv_m_nodes TO ROLE container_runtime_lab_user;

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

CREATE OR REPLACE NETWORK RULE HF_NETWORK_RULE
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('huggingface.co', 'cdn-lfs.huggingface.co','cdn-lfs-us-1.huggingface.co', 'cdn-lfs-us-1.hf.co');

CREATE EXTERNAL ACCESS INTEGRATION hf_access_integration
  ALLOWED_NETWORK_RULES = (HF_NETWORK_RULE)
  ENABLED = true;

GRANT USAGE ON INTEGRATION allow_all_integration TO ROLE container_runtime_lab_user;
GRANT USAGE ON INTEGRATION pypi_access_integration TO ROLE container_runtime_lab_user;
GRANT USAGE ON INTEGRATION hf_access_integration TO ROLE container_runtime_lab_user;

```
<!-- ------------------------ -->
## Run the Notebook

### Get the Notebook into Snowflake
- Download the notebook from [https://github.com/rajshah4/snowflake-notebooks/blob/main/Models/Llama3_2_Vision.ipynb](https://github.com/rajshah4/snowflake-notebooks/blob/main/Models/Llama3_2_Vision.ipynb)
- Change role to CONTAINER_RUNTIME_LAB_USER
- Navigate to Projects > Notebooks in Snowsight
- Click Import .ipynb from the + Notebook dropdown
- Create a new notebok with the following settings
  - Notebook Location: CONTAINER_RUNTIME_LAB, NOTEBOOKS
  - Run On Container
  - Snowflake ML Runtime GPU 1.0
  - Select Compute Pool with GPUs: gpu_nv_m_nodes

### Enable External Integrations
- Click the three dots in the top right > Notebook Settings
- Enable the PYPI_ACCESS_INTEGRATION
- Enable the HF_ACCESS_INTEGRATION

### Run the Notebook
- Run cells in the notebook!

<!-- ------------------------ -->
## Conclusion And Resources
You have successfully run a Snowflake Notebook on Snowpark Container Services through Container Runtime. You have also used the Llama 3.2 Vision model with Transformers. Feel free to explore other models available on Hugging Face and run them in your Snowflake Notebook. 

### What You Learned
- The key features of Snowflake Notebooks with Container Runtime
- Using models with Hugging Face Transformers
- Capabilities of Meta's Llama 3.2 Vision model

### Related Resources
- [Documentation](https://docs.snowflake.com/LIMITEDACCESS/snowsight-notebooks/ui-snowsight-notebooks-runtime)
- [Meta's 3.2 11B Vision Model](https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct)
- [Using Container Notebook](/en/developers/guides/notebook-container-runtime/)

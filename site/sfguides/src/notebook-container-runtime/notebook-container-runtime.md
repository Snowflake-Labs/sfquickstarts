author: Charlie Hammond
id: notebook-container-runtime
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/data-engineering
language: en
summary: This guide will walk show you how to use Snowflake Notebooks with Container Runtime 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-notebook-container-runtime


# Getting Started with Snowflake Notebook Container Runtime
<!-- ------------------------ -->
## Overview 

Snowflake Notebooks in the Container Runtime are a powerful IDE option for building ML models at scale in [Snowflake ML](/en/data-cloud/snowflake-ml/). Container Runtime (Public Preview) gives you a flexible container infrastructure that supports building and operationalizing a wide variety of resource-intensive ML workflows entirely within Snowflake. Using Snowflake Notebooks in Container Runtime gives you access to distributed processing on both CPUs and GPUs, optimized data loading from Snowflake, automatic lineage capture and Model Registry integration. Container Runtime also provides flexibility to leverage a set of preinstalled packages or the ability to pip install any open-source package of choice.  

This introductory Quickstart will take you through the steps of running Snowflake Notebooks with Container Runtime. We will install packages, then train a model using pre-installed packages. 

### Prerequisites
- A Snowflake Account. Sign up for a [30-day free trial](notebook-container-runtim) account, if required.
- Foundational knowledge of Data Science workflows

### What You Will Learn 
- The key features of Snowflake Notebooks with Container Runtime

### What You’ll Need 
- A [Snowflake](https://app.snowflake.com/) Account

### What You’ll Build 
- A Snowflake Notebook that runs on scalable CPUs or GPUs using any Python package of choice

<!-- ------------------------ -->
## Setup Your Account

Complete the following steps to setup your account:
- Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".
- Paste and the following SQL in the worksheet 
- Run all commands to create Snowflake objects

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is", "name":"aiml_notebooks_container_runtime", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"sql"}}';
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

USE ROLE container_runtime_lab_user;

CREATE FILE FORMAT IF NOT EXISTS container_runtime_lab.notebooks.csvformat 
    SKIP_HEADER = 1 
    TYPE = 'CSV';

-- create external stage with the csv format to stage the diamonds dataset
CREATE STAGE IF NOT EXISTS container_runtime_lab.notebooks.diamond_assets 
    FILE_FORMAT = container_runtime_lab.notebooks.csvformat 
    URL = 's3://sfquickstarts/intro-to-machine-learning-with-snowpark-ml-for-python/diamonds.csv';

CREATE OR REPLACE TABLE CONTAINER_RUNTIME_LAB.NOTEBOOKS.DIAMONDS (
	CARAT NUMBER(38,2),
	CUT VARCHAR(16777216),
	COLOR VARCHAR(16777216),
	CLARITY VARCHAR(16777216),
	DEPTH NUMBER(38,1),
	"TABLE" NUMBER(38,1),
	PRICE NUMBER(38,0),
	X NUMBER(38,2),
	Y NUMBER(38,2),
	Z NUMBER(38,2)
);

COPY INTO CONTAINER_RUNTIME_LAB.NOTEBOOKS.DIAMONDS
FROM @CONTAINER_RUNTIME_LAB.NOTEBOOKS.DIAMOND_ASSETS;

```

<!-- ------------------------ -->
## Run the Notebook

- Download the notebook from this [link](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-notebook-container-runtime/blob/main/notebooks/0_start_here.ipynb)
- Change role to CONTAINER_RUNTIME_LAB_USER
- Navigate to Projects > Notebooks in Snowsight
- Click Import .ipynb from the + Notebook dropdown
- Create a new notebok with the following settings
  - Notebook Location: CONTAINER_RUNTIME_LAB, NOTEBOOKS
  - Run On Container
  - Snowflake ML Runtime GPU 1.0
  - [SYSTEM_COMPUTE_POOL_GPU](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/working-with-compute-pool#default-compute-pools-for-notebooks)

![create-notebooks](assets/import-container-notebook.png)

- Click the three dots in the top right > Notebook Settings
- Enable the PYPI_ACCESS_INTEGRATION

![pypi-integration](assets/pypi_access.png)

- Run cells in the notebook!

![container-runtime-preview](assets/container_runtime_overview.png)

<!-- ------------------------ -->
## Conclusion And Resources

In conclusion, running Snowflake Notebooks Container Runtime offers a robust and flexible infrastructure for managing large-scale, advanced data science and machine learning workflows directly within Snowflake. With the ability to install external packages and choose optimal compute resources, including GPU machine types, Container Runtime provides a more versatile environment suited to the needs of data science and ML teams. 

Ready for more? After you complete this quickstart, you can try one of the following more advanced quickstarts: 
  - [Getting Started with Running Distributed PyTorch Models on Snowflake](/en/developers/guides/getting-started-with-running-distributed-pytorch-models-on-snowflake/)
  - [Defect Detection Using Distributed PyTorch With Snowflake Notebooks](/en/developers/guides/defect-detection-using-distributed-pytorch-with-snowflake-notebooks/)
  - [Scale Embeddings with Snowflake Notebooks](/en/developers/guides/scale-embeddings-with-snowflake-notebooks-on-container-runtime/)


### What You Learned
- The key features of Snowflake Notebooks with Container Runtime

### Related Quickstarts
- [Train an XGBoost model with GPUs in Snowflake Notebooks](/en/developers/guides/train-an-xgboost-model-with-gpus-using-snowflake-notebooks/)
- [Defect Detection Using Distributed PyTorch With Snowflake Notebooks](/en/developers/guides/defect-detection-using-distributed-pytorch-with-snowflake-notebooks/)
- [Scale Embeddings with Snowflake Notebooks on Container Runtime](/en/developers/guides/scale-embeddings-with-snowflake-notebooks-on-container-runtime/)
- [Getting Started with Running Distributed PyTorch Models on Snowflake](/en/developers/guides/getting-started-with-running-distributed-pytorch-models-on-snowflake/)
- [Getting Started with Snowflake ML](/en/developers/guides/intro-to-machine-learning-with-snowpark-ml-for-python/)

### Related Resources
- [Snowflake ML Webpage](/en/data-cloud/snowflake-ml/)
- [Documentation](https://docs.snowflake.com/LIMITEDACCESS/snowsight-notebooks/ui-snowsight-notebooks-runtime)
- [Fork Repo on GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowflake-notebook-container-runtime/blob/main/notebooks/0_start_here.ipynb?_fsi=EwgOAmF4&_fsi=EwgOAmF4)
- [Download Reference Architecture](https://drive.google.com/file/d/1GA_pt6Pdy76tWkxyPFKL2xH_YG3v5ZRM/view?usp=sharing)
- [Read Engineering Blog](/en/engineering-blog/machine-learning-container-runtime/)
- [Watch the Demo](https://youtu.be/zsMaLixJZpg?list=TLGGy3VbETdGc6wyNDA5MjAyNQ)

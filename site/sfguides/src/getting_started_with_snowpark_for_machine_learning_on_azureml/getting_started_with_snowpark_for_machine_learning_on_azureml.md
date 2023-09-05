author: marzillo-snow
id: example_matt_marzillo
summary: This is a quickstart for using Snowpark for ML on AzureML
categories: Getting-Started, data-science, data-engineering, azure, azureml, snowpark
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering

# Getting Started with Snowpark for Machine Learning on AzureML
<!-- ------------------------ -->
## Overview 
Duration: 15

Python is the language of choice for Data Science and Machine Learning workloads. Snowflake has long supported Python via the Python Connector, allowing data scientists to interact with data stored in Snowflake from their preferred Python environment. This did, however, require data scientists to write verbose SQL queries. To provide a more friendly, expressive, and extensible interface to Snowflake, we built Snowpark Python, a native Python experience with a pandas and PySpark-like API for data manipulation. This includes a client-side API to allow users to write Python code in a Spark-like API without the need to write verbose SQL. Python UDF and Stored Procedure support also provides more general additional capabilities for compute pushdown.

Snowpark includes client-side APIs and server-side runtimes that extends Snowflake to popular programming languages including Scala, Java, and Python. Ultimately, this offering provides a richer set of tools for Snowflake users (e.g. Python's extensibility and expressiveness) while still leveraging all of Snowflake's core features, and the underlying power of SQL, and provides a clear path to production for machine learning products and workflows.

A key component of Snowpark for Python is that you can "Bring Your Own IDE"- anywhere that you can run a Python kernel, you can run client-side Snowpark Python. You can use it in your code development the exact same way as any other Python library or module. In this quickstart, we will be using Jupyter Notebooks, but you could easily replace Jupyter with any IDE of your choosing.

AzureML is a fully managed machine learning service. With AzureML, data scientists and developers can quickly and easily build and train machine learning models, and then directly deploy them into a production-ready hosted environment. It provides an integrated Jupyter authoring notebook instance for easy access to your data sources for exploration and analysis, so you don't have to manage servers. It also provides common machine learning algorithms that are optimized to run efficiently against extremely large data in a distributed environment. With native support for bring-your-own-algorithms and frameworks, AzureML offers flexible distributed training options that adjust to your specific workflows.

MLflow is an open-source platform for managing the end-to-end machine learning lifecycle. It allows data scientists and developers to track experiments, package and share code, and deploy models. MLflow provides a centralized location for tracking experiments, reproducibility, and collaboration across teams. It also supports multiple languages and frameworks, making it a versatile tool for managing machine learning projects. Conveniently, AzureML tracking is built on top of MLFlow.

This quickstart is designed to service as an introduction to using AzureML with Snowpark for model development and deployment to Snowflake. The idea is that users can build off this quickstart or integrate components into their existing Azureml workloads.

[GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpark-for-machine-learning-on-azureml)

### Prerequisites
- Familiarity with [Snowflake](https://quickstarts.snowflake.com/guide/getting_started_with_snowflake/index.html#0) and a Snowflake account
- Familiarity with AzureML, an Azure account with an AzureML workspace
- Familiarity with [Python](https://www.udemy.com/course/draft/579706/)

### You'll Learn
- Using AzureML with Snowpark
- Loading and transforming data via Snowpark
- MLFlow
- Defining User Defined Functions for distributed scoring of machine learning models

### What You’ll Need 
- A free [Snowflake Account](https://signup.snowflake.com/)
- [Azure Account](https://azure.microsoft.com/en-us/free/search/?ef_id=_k_2ba2be3ad9791e57964fda0c62ccd55c_k_&OCID=AIDcmm5edswduu_SEM_k_2ba2be3ad9791e57964fda0c62ccd55c_k_&msclkid=2ba2be3ad9791e57964fda0c62ccd55c)


### What You’ll Build 
You will build an end-to-end data science workflow leveraging Snowpark for Python
- to load, clean and prepare data
- to train a machine learning model using Python in AzureML with ML Flow
- to deploy the trained models in Snowflake using Python User Defined Functions (UDFs)

The end-to-end workflow will look like this:
![](assets/azureml_arch.png)


<!-- ------------------------ -->
## Use Case
Duration: 5

In this use case you will build a binary model based on the 'Machine Predictive Maintenance Classification' dataset from [Kaggle](https://www.kaggle.com/datasets/shivamb/machine-predictive-maintenance-classification). We supplement this dataset with data from the Snowflake [data marketplace](https://www.snowflake.com/en/data-cloud/marketplace/).

The use case uses information related to machine diagnostics (torque, rotational speed) and environmental features (air temperature, humidity) to predict the likelihood of a failure.

<!-- ------------------------ -->
## Set Up Snowflake Environment
Duration: 2

The first thing we will do is create a database and warehouse in your Snowflake environment. Run the below code in a Snowflake worksheet.
```sql
use role accountadmin;

CREATE OR REPLACE WAREHOUSE HOL_WH WITH WAREHOUSE_SIZE='X-SMALL';

CREATE OR REPLACE DATABASE HOL_DB;
```
<!-- ------------------------ -->
## Set Up AzureML Environment
Duration: 15

If you haven't used AzureML before, for first time setup you will need to create an AzureML workspace. You can do so by following this [Link](https://learn.microsoft.com/en-us/azure/machine-learning/quickstart-create-resources?view=azureml-api-2) 

Once you've created your AzureML workspace your first step will be to create a setup.sh file that will be used to create the environment in your compute instance. Head to the "Notebooks" tab, hit the plus sign to create a new file and name it setup.sh.
![](assets/setup_sh.png)

Then copy and paste the code below into the setup.sh file and save it. This will be used as a start up script when creating the Compute Instance in AzureML.
```bash
#!/bin/bash

# Update the system
sudo apt-get update
sudo apt-get upgrade -y

# Install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
export PATH="$HOME/miniconda3/bin:$PATH"

# Create a conda environment and activate it
conda create -y -n my_env
conda activate my_env

# Install the required packages using conda
conda install -y -c snowflake -c conda-forge snowflake-snowpark-python pandas notebook scikit-learn cachetools

# Install MLflow using pip
pip install mlflow azureml-mlflow
```
Go to the "Compute" tab in AzureML, highlight the "Compute Instances" tab at the top and click "New". Provide a name and select the below options and click "Next: Advanced Settings"
![](assets/azureml_ci.png)

Click the radio tab that says "Provision with setup script" then click the blue button "Browse" and find the setup.sh file that we just created. Once selected click "Create" this could take about 10 minutes to create.
![](assets/provision_ci.png)

Once the compute instance is provisioned, head back to the "Notebooks" tab and open a terminal window for your compute instance.
![](assets/activate_terminal.png)

Run the below code in the terminal to activate the environment in the Jupyter kernel
```bash
conda activate my_env
pip install ipykernel
```

```bash
python -m ipykernel install --user --name=my_env
```
Once that's done you can close the terminal window and now open up a blank .ipynb file and check the kernels on the top right to make sure the "my_env" kernel has been created. You may have to refresh the list and wait several seconds.
![](assets/check_env.png)

<!-- ------------------------ -->
## Clone Github Repo
Duration: 5

Open a terminal window the same as the previous step. In the terminal window you will copy the public repo that contains the data and scripts needed for this quickstart.

```bash
git clone https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpark-for-machine-learning-on-azureml
```
> Note: The versions at the time of writing this -- snowflake-snowpark-python 1.0.0


<!-- ------------------------ -->
## Load data into Snowflake
Duration: 5

You should now be able to navigate back to the 'File Browser' tab on the left and see your cloned repo. Open the setup.ipynb notebook (ensure that you select the correct environment), [0_setup_data.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpark-for-machine-learning-on-azureml/0_setup_data.ipynb) and work through the set up script here to load the data. Your chosen role will need to have permissions to create these objects - if you are in a fresh lab account, the `ACCOUNTADMIN` role will work, but note that this wouldn't be used in a production setting.

You will need to enter your user and account credentials, and it is important that your `account` is in the correct format as outlined in the [Snowflake documentation](https://docs.snowflake.com/en/user-guide/admin-account-identifier#non-vps-account-locator-formats-by-cloud-platform-and-region). Your `host` will be your `account` ID followed by `.snowflakecomputing.com`, for example:
```python
connection_parameters = {
    "account": "sn00111",
    "host": "sn00111.central-us.azure.snowflakecomputing.com",
    "user": <your_user>, 
    "password": <your_password>,
    "role": <your_role>, # using "ACCOUNTADMIN" may simplify things in an isolated lab environment
    }
```

> Note: for simplicity in this lab you will need to enter your account and user credentials directly in your notebook. For a production setup, this would be a security risk so Azure Key Vault or a similar tool would be appropriate.

Once complete with the script, check back to your Snowflake environment to make sure that your data has loaded. Review the steps as you go: you just used a little bit of Snowpark to get that data loaded via the `session.write_pandas` function!
![](assets/database_check.png)

### Troubleshooting `pyarrow` related issues

- If you have `pyarrow` library already installed, uninstall it before installing Snowpark.
- If you do not have `pyarrow` installed, you do not need to install it yourself; installing Snowpark automatically installs the appropriate version.
- Do not reinstall a different version of `pyarrow` after installing Snowpark.

<!-- ------------------------ -->
## Build and Deploy Model
Duration: 10

Now open and work through the `1_mfr_mlflow.ipynb` workbook to join together the datasets, bring in the training data then build and deploy the model. Once again, make sure to select the correct python environment.

[1_mfr_mlflow.ipynb](hhttps://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpark-for-machine-learning-on-azureml/1_mfr_mlflow.ipynb)

Once that notebook is complete you will have a udf that you can use to generate predictions in your Snowflake environment! you can do this via Snowpark Python code or Snowflake SQL. Let's generate predictions with this udf with Snowflake SQL. Copy and paste the code below into your snowflake environment to generate inference.

```sql
use role accountadmin;
select predict_failure(AIR_TEMPERATURE_K,
       PROCESS_TEMPERATURE, ROTATIONAL_SPEED_RPM, TORQUE_NM,
       TOOL_WEAR_MIN, HUMIDITY_RELATIVE_AVG) as predicted_failure, * from maintenance_hum;
```

![](assets/snowflake_inference.png)

Head back to AzureML and notice how the training job, data and model are now all captured in your AzureML environment. This highlights how MLFlow is integrated with AzureML!
AzureML Jobs:
![](assets/azureml_jobs.png)


AzureML Model:
![](assets/azureml_model.png)


AzureML Data Registry:
![](assets/azureml_data.png)

<!-- ------------------------ -->
## Conclusion and Additional Considerations
Duration: 5

This quickstart is just that, a quick way to get you started with using AzureML with Snowflake and Snowpark. For enterprise uses, data scientists and developers will want to consider additional details. 


Specifically, you may want to consider the additional details:
1. Using Github and Github actions to automate testing, execution and deployment of the code.
2. You may know that the Snowpark sandbox on Snowflake includes Anaconda supported packages which inludes the scikitlearn package that was used to build the logistic regression model. If you use other packages to build your models that are not supported by Anaconda you will have to install [third party packages in the Snowpark sandbox](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html).

### What We covered
- Using a AzureML with Snowpark
- Loading and transforming data via Snowpark with pushdown compute
- Deploying models to Snowflake via a User Defined Function
- Using MLFlow with AzureML

### Additional Considerations
- There are some great blogs on Medium regarding Snowpark, AzureML and using Snowflake with Azure.

- [Full demo on Snowflake Demo Hub](https://developers.snowflake.com/demos/predictive-maintenance-manufacturing/)

- [Snowpark for python with AzureML](https://medium.com/@michaelgorkow/mlops-with-snowflake-and-mlflow-on-azure-machine-learning-a21a9def693)

- [Operationalizing Snowpark](https://medium.com/snowflake/operationalizing-snowpark-python-part-one-892fcb3abba1)

If you have any questions, reach out to your Snowflake account team!
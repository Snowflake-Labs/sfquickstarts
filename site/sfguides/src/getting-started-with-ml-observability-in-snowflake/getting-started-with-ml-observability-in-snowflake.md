author: Kala Govindarajan
id: getting-started-with-ml-observability-in-snowflake
summary: ML Ops is defined as the core function of ML engineering focused on optimizing the process of deploying, maintaining, and monitoring models in production. Snowflake ML Observability allows to monitor models deployed in production via Snowflake Model Registry to track the quality of the model across multiple dimensions such as performance and drift along with volume. With this ML Ops-driven approach for customer churn monitoring, enterprises can ensure that ML models add real value, minimize the risk of performance decay, and make informed, data-driven decisions that drive customer retention.
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science 

# Getting Started with ML Observability in Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 1

For many large enterprises, extracting tangible value from Machine Learning (ML) initiatives remains a significant challenge. Despite substantial investments, the journey from developing models to realizing their benefits often encounters numerous roadblocks. Models can take excessive time and effort to reach production, or worse, they may never get there at all. Even when they do make it to production, the real-life outcomes can sometimes fall short of expectations.
MLOps is a core function of ML engineering and focuses on streamlining the process of taking machine learning models to production, and then maintaining and monitoring them effectively.  Unlike traditional software, machine learning models can change their behavior over time due to various factors, including input drift, outdated assumptions from model training, issues in data pipelines, and standard challenges like hardware/software environments and traffic. These factors can lead to a decline in model performance and unexpected behavior which needs to be monitored very closely.


Snowflake ML provides organizations with an integrated set of capabilities for end-to-end machine learning in a single platform on top of governed data. Snowpark ML provides capability to create and work with machine learning models in Python that includes Snowflake ML Modeling API which uses familiar Python frameworks for building and training your own models,Python APIs for building and training your own models, Snowflake Feature Store that lets data scientists and ML engineers create, maintain, and use ML features in data science and ML workloads and Model Explainability and Snowflake Model Registry lets you securely manage models and their metadata in Snowflake, Model explainability and Model observability.

<img src="assets/image.png"/>

In this Quickstart guide we will be exploring Model Observability* in Snowflake that enables one to detect Model behavior changes over time due to input drift, stale training assumptions, and data pipeline issues, as well as the usual factors, including changes to the underlying hardware and software and the fluid nature of traffic. ML Observability allows you to track the quality of production models thay has been deployed via the Snowflake Model Registry across multiple dimensions, such as performance, drift, and volume.
For demonstration purposes, let’s consider a multinational financial services firm aiming to understand and mitigate customer churn. Losing customers not only impacts revenue but also incurs additional costs to acquire new ones. Therefore, having an accurate model to predict churn and monitoring it regularly is crucial. The financial firm leverages Snowflake ML for its end to end Machine Learning pipeline and have achieved continuous monitoring for data quality, model quality, bias drift and feature attribution drift data quality, model quality, bias drift and feature attribution drift with ML Observability.


### Prerequisites
- A non-trial Snowflake account with access to a role that has the ACCOUNTADMIN role. If not, you will need to work with your admin to perform the initial environment setup.
- Git installed.

### What You’ll Learn 
- How to build a comprehensive and scalable production-ready MLOps pipeline that manages the entire ML workflow in Snowflake. 
- How to implement model performance tracking across multiple dimensions, such as performance, drift, and volume  via the Snowflake Model Registry.
- How to carry monitoring of customer churn classification model


### What You’ll Need 
- A [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) account.
- Access to the ACCOUNTADMIN role. If not, you will need to work with your admin to perform the initial environment setup.
- Git installed.

### What You’ll Build 
- How to build a comprehensive and scalable production-ready MLOps pipeline that manages the entire ML workflow in Snowflake.  
    - **loads data and prepare data**
    - **performs feature transformations on the data using Snowpark ML Preprocessing functions**
    - **train an XGBoost ML model using Snowpark ML**
    - **log models and execute batch inference in Snowflake using the Snowflake Model Registry**
    - **create a built-in model monitor to detect model and feature drift over time**
    - **implement model performance tracking across multiple dimensions, such as performance, drift, and volume via the Snowflake Model Registry**


<!-- ------------------------ -->
## Setup Environment
Duration: 2

This section will walk you through creating various objects

#### High-Level Workflow

We will leverage Snowflake Notebooks to carry the Data loading, Feature Engineering, Model Training, Model Inference and the Model Monitoring setup.

**Step 1**. Navigate to Worksheets in Snowsight. Create a database and warehouse that is needed for the Notebook execution. The commands are given below :

```
USE ROLE SYSADMIN;
create database customer_db;

CREATE OR REPLACE WAREHOUSE ml_wh WITH 
WAREHOUSE_TYPE = standard WAREHOUSE_SIZE = Medium
AUTO_SUSPEND = 5 AUTO_RESUME = True;

```

**Step 2**. Clone [GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ml-observability-in-snowflake) repository.

Open and download the following [notebook](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ml-observability-in-snowflake/tree/main/notebook) from the cloned repository. Import the notebook into the Snowflake Snowsight under Projects -> Notebooks section. Note that the snowflake-ml-python is a required package and remember to add it in the package selector.

**Step 3**. Notebook Walkthrough. You can choose to run cell by cell or Run All.

- First import essential packages are imported, including snowpark,snowflake ml,snowflake ml modeling and the snowflake ml registry.

- Synthetic data has been generated that will be used to predict customer churn for this hypothetical financial customer churn use case. This data includes features related to both customer demographics and transaction information, which a financial firm might use to make predictions about whether a customer will churn.

- Leverage the generated synthetic data to create new features using the snowflake.ml.modeling.preprocessing functions from the Snowpark ML Preprocessing API. All feature transformations using Snowpark ML are distributed operations in the same way with Snowpark DataFrame operations.

- Train an XGBoost classifier model using the Snowpark ML Modeling API.
  
- Log the trained model to Snowflake Model Registry. 
  
- After logging the model by calling the registry’s log_model method, inference can be carried out using the model operations.
  
- For the purpose of ongoing inference a Stored procedure that leverages the trained model from the Snowflake model registry and the preprocessing pipeline is used.

<img src="assets/workflow.png"/>

- Create a model monitor using the CREATE MODEL MONITOR command. The model monitor must be created in the same schema as the model version that needs to be monitored. 
  
- The monitor object attaches to the specific model version with a source table name

```
CREATE OR REPLACE MODEL MONITOR QS_CHURN_MODEL_MONITOR
WITH
    MODEL=QS_CustomerChurn_classifier
    VERSION=demo
    FUNCTION=predict
    SOURCE=CUSTOMER_CHURN
    BASELINE=CUSTOMERS
    TIMESTAMP_COLUMN=TRANSACTIONTIMESTAMP
    PREDICTION_CLASS_COLUMNS=(PREDICTED_CHURN)  
    ACTUAL_CLASS_COLUMNS=(EXITED)
    ID_COLUMNS=(CUSTOMERID)
    WAREHOUSE=ML_WH
    REFRESH_INTERVAL='1 min'
    AGGREGATION_WINDOW='1 day';
```

In the above case we are creating a NAME: The name of the monitor to be created. Must be unique within the schema.

- MODEL and VERSION: The name and version of the model to be monitored.

- FUNCTION: The name of the inference function that generates predictions.

- SOURCE: The table that contains the data to be used for inference.

- BASELINE(Optional): The table containing a snapshot of recent inference results that will be used as a baseline to detect drift. In this case the CUSTOMERS table had the initial baseline from model training

- TIMESTAMP_COLUMN: The name of the timestamp column.

- ID_COLUMNS: Array of columns that contain record IDs. To ensure the predicted label is for an unique record

- WAREHOUSE: The warehouse used for internal compute operations for the monitor, including dynamic table operations.

- REFRESH_INTERVAL: The interval at which the monitor refreshes from the source data (for example “1 day”). The supported intervals are the same as those available for dynamic table target lag. Modify this as per end requirements

- AGGREGATION_WINDOW: The aggregation window used to compute metrics in days (for example “1 day”). Modify this as per end requirements

<!-- ------------------------ -->
## Monitoring Model Performance in Snowsight

Lets view the monitoring dashboards in Snowsight.

- Navigate to the ML Monitoring dashboard in Snowsight. 

- In the Snowsight navigation menu, select AI & ML and then Models.
- This will list all models in the Snowflake Model Registry across databases and schemas that the current role can access.
- To view details for a specific model, select its row in the Models list. This will open the model's details page, where you can find key information, such as the model's description, tags, versions, and monitors.

In the Monitors section of the details page, a list of model monitors can be found, including the model versions they are linked to, their status, and creation dates.


#### Metrics Monitoring

<img src="assets/actualsvsprediction.png"/>


Prediction Count - Count of non-null values for prediction column.

Actual Count - Count of non-null values for label column.


<img src="assets/metrics.png"/>


Precision - ratio of true positive predictions to the total predicted positives, indicating the accuracy of positive predictions.

Classification accuracy- ratio of correctly predicted instances to the total instances in the dataset.

Recall - ratio of true positive predictions to the total actual positives, measuring the ability to capture all relevant instances.

The F1 Score - the harmonic mean of precision and recall, providing a balance between the two metrics.

Difference of mean - compares the average values between two datasets.

<img src="assets/settings.png"/>

There are other metrics that can be tracked as per the model type. 


<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1
In conclusion, deploying machine learning models to production is crucial for realizing their full value and impact. Historically, many organizations faced challenges in bridging the gap between data science development and production environments, often leaving data scientists without the chance to see their work make a tangible impact. However, with modern data platforms like Snowflake—which supports building end to end ML pipelines making this process much easier, governed and manageable.

In this guide, we explored how financial firms can build end-to-end, production-ready customer churn prediction models using Snowflake ML. With Snowflake's new features supporting MLOps, organizations can now monitor, optimize, and manage models at scale in production. This approach ensures models are deployed in a controlled, reliable manner and continue to evolve, delivering sustained value over time. Ultimately, Snowflake empowers organizations to move confidently from development to production, unlocking the full potential of their machine learning models and driving impactful, large-scale results.


### What You Learned
- How to build a comprehensive and scalable production-ready MLOps pipeline that manages the entire ML workflow in Snowflake. 
- How to implement model performance tracking across multiple dimensions, such as performance, drift, and volume  via the Snowflake Model Registry.


### Related Resources
- #### [Snowpark ML](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)
- #### [Snowpark Model Observability](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/model-observability)
- #### [Getting Started with Snowflake ML](https://quickstarts.snowflake.com/guide/intro_to_machine_learning_with_snowpark_ml_for_python/#0)

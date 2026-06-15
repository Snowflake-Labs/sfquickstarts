author: Allie Fero, James Cha-Earley
id: build-ml-models-for-customer-conversions
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/cortex-analyst
language: en
summary: Build ML models to predict customer conversions in Snowflake for marketing optimization and conversion rate improvement.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-build-ml-models-for-customer-conversions





# Building ML Models to Crack the Code of Customer Conversions

## Overview 

Will they buy? This hands-on lab will guide you through building a custom machine learning model to predict customer purchase likelihood by analyzing the complex relationship between website experience metrics and product reviews. Using Snowflake's advanced gen AI and machine learning capabilities, you'll work with a carefully constructed synthetic dataset that simulates real-world scenarios, allowing for controlled exploration of various factors affecting purchase decisions.

### What You'll Build
- A complete ML pipeline that processes and classifies text data, performs sentiment analysis, and builds a predictive model 
- A horizontally scalable system to extract insights from customer reviews using both custom processing with OSS LLMs directly and Snowflake Cortex AI
- An automated workflow to deploy continuous data processing on a scheduled basis
- A dashboard to visualize the impact of user experience features on purchase decisions

### What You'll Learn
- How to pipeline unstructured data into your Snowflake workflows
- How to use Ray for scalable distributed data processing
- How to process synthetic customer feedback data utilizing open source LLMs for classification and Cortex AI for sentiment analysis
- How to use custom ML models to assess review quality and helpfulness and train across multiple nodes
- How to deploy the end to end pipeline to production using ML Jobs and Snowflake Tasks
- How to evaluate the relative importance of user experience features on purchase decisions
- How to create dynamic visualizations to communicate insights to stakeholders

### Prerequisites
- A Snowflake Account. [Sign up for a 30-day free trial account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides), make sure to select AWS WEST
- Familiarity with Python and ML concepts

## Setup Environment

Before diving into Ray and distributed processing, let's set up our environment with the necessary database objects and sample data.

### Download Setup Files

1. Download these three files to your local machine:
   * [setup.sql](https://github.com/Snowflake-Labs/sfguide-build-ml-models-for-customer-conversions/blob/main/setup.sql)
   * [notebook.ipynb](https://github.com/Snowflake-Labs/sfguide-build-ml-models-for-customer-conversions/blob/main/notebook.ipynb)
   * [streamlit.py](https://github.com/Snowflake-Labs/sfguide-build-ml-models-for-customer-conversions/blob/main/streamlit.py)

### Run the Setup Script

1. Log in to your Snowflake account
2. Navigate to Worksheets:
   * Click on the **Worksheets** tab in the left navigation pane
   * Click on the **+** button to create a new worksheet

3. Execute the setup script:
   * Open the worksheet editor
   * Copy and paste the contents from your downloaded `setup.sql` file
   * Click the **Run All** button to execute the script

The setup script creates the necessary database, schema, tables, and loads sample data for our analysis.

> 
> `CREATE COMPUTE POOL` step is expected to fail on trial accounts 

### Import the Notebook

1. Navigate to Snowflake Notebooks:
   * Click on **Projects** » **Notebooks** in the left navigation menu

2. Import the notebook file:
   * Click on the **...** menu in the top right
   * Select **Import .ipynb file** from the dropdown
   * Select the `notebook.ipynb` file you downloaded earlier

3. Configure the notebook:
   * For **Database**, select `HOL_DB`
   * For **Schema**, select `HOL_SCHEMA`
   * For **Runtime**, select `Run on Container`  
   * For **Runtime version**, Leave as is 
   * For **Compute pool**, Leave as is
   * For **Query warehouse**, select `HOL_WAREHOUSE`
   * Click **Create**

### Enable External Access Integrations

After creating the notebook, you'll need to enable external access for internet connectivity:

1. In your newly created notebook, click on the three dots (**...**) in the top right corner
2. Select **Notebook settings**
3. Select the **External access** pane
4. Toggle on **ALLOW_ALL_ACCESS_INTEGRATION**
5. Click **Save**
6. Restart your notebook session for the changes to take effect

Now you're ready to begin building your ML model with Ray for distributed processing.

## Initialize Ray for Distributed Processing

In this section, we'll set up Ray to enable unstructured data ingestion and distributed processing capabilities in Snowflake.

### Configure Ray Environment
Open a Snowflake Notebook and initialize the environment by importing Ray and configuring logging to suppress verbose output. Set up the Ray data context and disable progress bars for cleaner output. Import required libraries including Streamlit and pandas, and initialize the Snowpark session to interact with your Snowflake data.

### Scale the Cluster
Configure the Ray cluster for better performance by scaling the computing resources. We'll set a scale factor of 2 to allocate adequate resources for our machine learning tasks. This ensures efficient processing of our review data and model training.

## Process Review Text Data

Now we'll implement the data processing pipeline to extract insights from customer reviews and prepare them for analysis.

### Set Up Data Source
Import the SFStageTextDataSource class from snowflake.ml.ray.datasource and configure a data source pointing to review text files in your Snowflake stage. Set up wildcard pattern matching to read all text files and create a Ray dataset by reading from this data source. These files contain synthetic customer feedback across different product categories.

### Parse Review Data
Create a parsing function that extracts UUID and the review text from each record. The function splits each text entry on a comma delimiter and cleans and formats the extracted fields by removing quotes and other characters. We'll return a dictionary with parsed fields and apply this function to the dataset using Ray's map operation. This structured review data will be crucial for understanding customer sentiment across different market segments.

## Predict Review Quality

In this step, we'll predict the quality of reviews using an open-source pre-trained model via a HuggingFace Pipeline to understand how review content impacts purchase decisions.

### Create Model Predictor Class
Define a class for batch processing reviews and initialize a zero-shot classification pipeline using the facebook/bart-large-mnli model. Set up classification labels to categorize reviews by quality:

"Detailed with specific information and experience"
"Basic accurate information"
"Generic brief with no details"

Implement batch processing logic to handle multiple reviews efficiently and extract and format classification results to identify high-quality versus low-quality feedback.

Process the entire dataset using Ray's distributed computing capabilities. Use map_batches to apply the model to groups of reviews, configure concurrency to match the cluster scale factor, set an appropriate batch size to optimize performance, and allocate CPU resources for efficient processing. This analysis helps identify which types of reviews are most influential in purchase decisions.

## Store Processed Data in Snowflake

Now we'll save our processed data back to Snowflake tables for further analysis and model building.

### Create Data Sink
Import SnowflakeTableDatasink from snowflake.ml.ray.datasink and configure the data sink to write to a table named "REVIEWS". Enable auto-create table option to automatically generate the table structure and set override parameter to false to prevent accidental data loss. Write the processed dataset to the configured data sink. This creates a centralized repository of analyzed customer feedback that can be joined with other datasets.

### Verify Results
Examine the first few rows of processed data using a simple SQL query to confirm the data was successfully stored, including the review quality classifications.

## Add Sentiment Analysis

In this step, we use Snowflake Cortex to enhance our reviews with sentiment analysis, providing additional insights for our model.

### Sentiment Analysis Process
The notebook performs these key operations:

Adds a REVIEW_SENTIMENT column to the REVIEWS table to store sentiment scores
Uses the Snowflake Cortex SENTIMENT function to analyze the emotional tone of each review
Updates the table with sentiment scores ranging from -1 (negative) to 1 (positive)

This enriches our dataset with quantified emotional data that serves as a critical feature in predictive modeling. Unlike the review quality assessment (which uses our custom ML model), the sentiment analysis is performed using Snowflake's built-in Cortex capabilities, demonstrating how to combine custom ML processing with Snowflake's native AI functions for comprehensive analysis.

## Prepare Data for Model Training

Now we'll join our review data with website performance metrics to prepare for model training, creating a comprehensive view of the customer journey.

### Join Tables
Import the DataConnector from snowflake.ml.data, load tabular data (containing page load times, product layouts, and other metrics) and review data, and join the tables using UUID and REVIEW_ID as the key. Use an inner join to ensure all records have matching entries. This creates a holistic view of both technical performance and customer sentiment data.

### Examine the Combined Dataset
Check the dataset to ensure it's ready for modeling by counting the total number of rows after joining, listing all available columns to identify features, and confirming that we have both technical metrics (page load time) and sentiment data. This combined dataset allows us to analyze the relative impact of technical performance versus product perception.

### Feature Engineering
Prepare categorical features for model training by importing LabelEncoder from snowflake.ml.modeling.preprocessing, identifying categorical columns that need encoding (REVIEW_QUALITY, PRODUCT_LAYOUT), creating encoders for each target column, and applying the fit and transform pattern to convert categories to numeric values. This ensures all data is in a format suitable for our predictive model.

## Train an XGBoost Model

In this step, we'll use a Snowflake distributed XGBEstimator to train an XGBoost model to predict purchase decisions based on both technical and sentiment factors.

### Configure Model Parameters
Import XGBEstimator and XGBScalingConfig from snowflake.ml.modeling.distributors.xgboost and identify input features from the prepared dataset:

REVIEW_QUALITY_OUT (encoded review quality from our custom model)
PRODUCT_LAYOUT_OUT (encoded layout type)
PAGE_LOAD_TIME (technical performance)
REVIEW_SENTIMENT (customer satisfaction from Cortex AI)
PRODUCT_RATING (product quality)

Specify the target column (PURCHASE_DECISION) and configure hyperparameters for the XGBoost model including learning rate, tree depth, and minimum child weight. Set up scaling configuration without GPU acceleration.

### Initialize and Train Model
Create the XGBEstimator with the configured parameters, convert the training dataframe to a compatible format using DataConnector, and fit the model on the training data using the selected input columns and label. The training process runs distributed across the Ray cluster. This model will help identify which factors have the greatest influence on purchase likelihood.

## Register and Deploy the Model

In this section, we'll register our model in Snowflake's model registry to make it available for business applications.

### Register Model
Import the registry module from snowflake.ml.registry and initialize a Registry object connected to the current session. Log the trained model to the Snowflake Model Registry with the name "deployed_xgb" and include necessary dependencies for runtime execution (scikit-learn, xgboost). Provide sample input data for validation, add descriptive metadata including a comment about the model's purpose, enable explainability features for model interpretation, and configure deployment targets for warehouse execution. This makes the model available for business stakeholders to use in decision-making.

### Generate Model Explanations
Run the model's explain function on input data and review the generated explanations to understand feature importance. This reveals the relative importance of technical metrics versus product perception in driving purchases. These insights can help businesses decide whether to allocate resources to technical optimization or product improvement.

## Create Automated ML Pipeline

> 
> **Note** You will not be able to do these next steps of the Notebook on a Trial Account

Now we'll set up an automated workflow using ML Jobs to run remote code, and Snowflake's DAG framework to process new reviews and retrain models.

### Define Remote Jobs
First, create a job to process new reviews by importing the remote decorator from snowflake.ml.jobs, creating a function that processes new reviews using the pipeline we built, applying the remote decorator to enable Snowflake to run this function as a job, and configuring the compute pool, stage, and access integrations.

Next, create a job for model retraining that reproduces our feature engineering, model training, and model registration steps, with added versioning to track model updates over time.

### Create DAG for Workflow Orchestration
Build an automated workflow using Snowflake's DAG framework by defining the workflow structure, scheduling parameters, and stage locations. Create tasks for each step in the workflow (setup, review processing, sentiment analysis, model training) and connect them in sequence using the directed acyclic graph structure.

### Deploy and Run the DAG
Deploy the defined workflow to your Snowflake account, run the workflow to verify functionality, and monitor execution status to track progress of the deployment. This automation ensures that your ML pipeline runs regularly, keeping your predictions current with the latest data.

## Setting Up the Streamlit App

To create and configure your Streamlit application in Snowflake:

1. Navigate to Streamlit in Snowflake:
   * Click on the **Streamlit** tab in the left navigation pane
   * Click on **+ Streamlit App** button in the top right

2. Configure App Settings:
   * Enter "Purchase Decision Dashboard" as your app name
   * Select **HOL_WAREHOUSE** as your warehouse
   * Choose HOL_DB as your database and HOL_SCHEMA as your schema

3. Create the app:
   * In the editor, paste the complete code from your downloaded `streamlit.py` file
   * Click "Run" to launch your application

Your Streamlit app will create visualizations showing the relationship between review quality, sentiment, and purchase decisions, helping stakeholders understand key factors in the customer journey.

## Conclusion and Resources

### Conclusion
Congratulations! You've successfully built an end-to-end ML workflow in Snowflake ML that processes customer reviews, analyzes sentiment with gen AI, and predicts purchase decisions using XGBoost. You've also created an automated pipeline that handles data processing and model retraining, deployed in the Snowflake ecosystem. This solution shows how to identify which factors have the greatest influence on purchase decisions, helping businesses decide where to allocate resources - whether on improving website performance or enhancing product quality and customer satisfaction.

### What You Learned
- How to pipeline unstructured data into your Snowflake workflows
- How to use Ray for scalable distributed data processing
- How to process synthetic customer feedback data utilizing open source LLMs for classification and Cortex AI for sentiment analysis
- How to use custom ML models to assess review quality and helpfulness and train across multiple nodes
- How to deploy the end to end pipeline to production using MLJobs and Snowflake Tasks
- How to evaluate the relative importance of user experience features on purchase decisions
- How to create dynamic visualizations to communicate insights to stakeholders

### Resources
- [Snowflake ML Webpage](/en/data-cloud/snowflake-ml/)
- [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-ml)
- [Quickstart: Build an End-to-End ML Model in Snowflake](/en/developers/guides/)
- [Other Related Quickstarts](/en/developers/guides/)
- Have a question? Ask in [Snowflake Community](https://community.snowflake.com/)

author: Charlie Hammond
id: intro-to-feature-store
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: This guide give an overview of the key features of Snowflake Feature Store 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-intro-to-feature-store-using-snowflake-notebooks



# Introduction to Snowflake Feature Store with Snowflake Notebooks
<!-- ------------------------ -->
## Overview 

The Snowflake Feature Store offers a comprehensive solution for data scientists and machine learning (ML) engineers to create, manage, and utilize ML features within their data science workflows in [Snowflake ML](/en/data-cloud/snowflake-ml/). Features, which are enriched or transformed data, serve as essential inputs for machine learning models. For instance, a feature might extract the day of the week from a timestamp to help the model identify weekly patterns, such as predicting that sales are typically 20% lower on Wednesdays. Other features often involve data aggregation or time-shifting. The process of defining these features, known as feature engineering, is crucial to developing high-quality ML applications.

This is part 1 of a 3-part introduction quickstart series to Snowflake Feature Store (part 2 [here](/en/developers/guides/overview-of-feature-store-api/) and part 3 [here](/en/developers/guides/develop-and-manage-ml-models-with-feature-store-and-model-registry/)). In this quickstart, you will learn how to build the key components of a feature store workflow, including entities, feature views, and datasets. Entities represent the real-world objects or concepts that your features describe, such as customers or products. Feature views provide a structured way to define and store these features, allowing for consistent and efficient retrieval. Finally, datasets are collections of features that are prepared for model training or inference. By the end of this quickstart, you'll have a solid understanding of how to create and manage these components within the Snowflake Feature Store, setting the foundation for building robust and scalable machine learning pipelines.

### Prerequisites
- Access to a Snowflake account with Accountadmin. 
- Access to run Notebooks in Snowflake
- Foundational knowledge of Data Science workflows

### What You Will Learn 
- The key features of Snowflake Feature Store including [entities](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/entities), [feature views](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/feature-views), and [datasets](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/modeling#generating-datasets-for-training).

### What You’ll Need 
- A [Snowflake](https://app.snowflake.com/) Account

### What You’ll Build 
- An Snowflake Feature Store pipeline that generates a dataset for model training

<!-- ------------------------ -->
## Setup Your Account

Complete the following steps to setup your account:
- Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".
- Paste and the following SQL in the worksheet 
- Run all commands to create Snowflake objects

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE SNOWFLAKE;

-- Using ACCOUNTADMIN, create a new role for this exercise and grant to applicable users
CREATE OR REPLACE ROLE FEATURE_STORE_LAB_USER;
BEGIN
    LET current_user_name := CURRENT_USER();
    EXECUTE IMMEDIATE 'GRANT ROLE FEATURE_STORE_LAB_USER TO USER ' || current_user_name;
END;

-- create our virtual warehouse
CREATE OR REPLACE WAREHOUSE FEATURE_STORE_WH AUTO_SUSPEND = 60;

GRANT ALL ON WAREHOUSE FEATURE_STORE_WH TO ROLE FEATURE_STORE_LAB_USER;

-- use our feature_store_wh virtual warehouse 
USE WAREHOUSE FEATURE_STORE_WH;

-- Next create a new database and schema,
CREATE OR REPLACE DATABASE FEATURE_STORE_DATABASE;
CREATE OR REPLACE SCHEMA FEATURE_STORE_SCHEMA;

GRANT OWNERSHIP ON DATABASE FEATURE_STORE_DATABASE TO ROLE FEATURE_STORE_LAB_USER COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE FEATURE_STORE_DATABASE  TO ROLE FEATURE_STORE_LAB_USER COPY CURRENT GRANTS;

-- Setup is now complete
```

<!-- ------------------------ -->
## Run the Notebook

- Download the notebook from this [link](https://github.com/Snowflake-Labs/sfguide-intro-to-feature-store-using-snowflake-notebooks/blob/main/notebooks/0_start_here.ipynb)
- Change role to FEATURE_STORE_LAB_USER
- Navigate to Projects > Notebooks in Snowsight
- Click Import .ipynb from the + Notebook dropdown
- Create a new notebok with the following settings
  - Notebook Location: FEATURE_STORE_DATABASE, FEATURE_STORE_SCHEMA
  - Run on Warehouse
  - Warehouse: FEATURE_STORE_WH
- Create Notebook
- Click Packages in the top right, add `snowflake-ml-python`
- Run cells in the notebook!

![notebook-preview](assets/feature_store_notebook.png)

<!-- ------------------------ -->
## Conclusion And Resources

The Snowflake Feature Store provides a powerful, all-in-one solution for data scientists and ML engineers to create, manage, and utilize machine learning features effectively.  In this quickstart, you’ve learned the essentials of building a feature store workflow, including entities, feature views, and datasets. Now, take the next step and apply these concepts to build robust, scalable ML pipelines within Snowflake. Check out the links below and start building you Feature Stores today!

### What You Learned
- **Understanding the Snowflake Feature Store**: Gained insight into how the Snowflake Feature Store helps manage and utilize ML features in data science workflows.
- **Building Key Components**:
  - **Entities**: Defined real-world objects or concepts that features describe, such as customers or products.
  - **Feature Views**: Learned how to structure and store features for consistent and efficient retrieval.
  - **Datasets**: Prepared collections of features for model training or inference.
- **Workflow Integration**: Developed an understanding of how these components work together to create a robust and scalable ML pipeline.

### Related Quickstarts
- Part 2: [Getting Started with Snowflake Feature Store API](/en/developers/guides/overview-of-feature-store-api/)
- Part 3: [Develop and Manage ML Models with Feature Store and Model Registry](/en/developers/guides/develop-and-manage-ml-models-with-feature-store-and-model-registry/)

### Related Resources
- [Snowflake Feature Store](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview)
- [Entities](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/entities)
- [Feature Views](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/feature-views)
- [Datasets](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/modeling#generating-datasets-for-training).
- [Snowflake ML Webpage](/en/data-cloud/snowflake-ml/)

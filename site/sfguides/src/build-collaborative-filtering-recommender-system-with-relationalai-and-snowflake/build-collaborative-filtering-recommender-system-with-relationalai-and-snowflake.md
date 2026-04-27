author: Haythem Tellili
id: build-collaborative-filtering-recommender-system-with-relationalai-and-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/partner-solution, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/build, snowflake-site:taxonomy/snowflake-feature/native-apps
language: en
summary: Build collaborative recommendation systems with RelationalAI and Snowflake for personalized user experiences.
environments: web
status: Published 
feedback link: https://github.com/RelationalAI/rai-samples/issues


# Recommender Systems with RelationalAI’s Snowflake Native App

## Overview 

By completing this guide, you will be able to build a collaborative filtering recommender system RelationalAI’s Native App on Snowflake.

### What Is RelationalAI?

RelationalAI is a cloud-native platform that enables organizations to streamline and enhance decisions with intelligence. RelationalAI extends Snowflake with native support for an expanding set of AI workloads (e.g., graph analytics, rule-based reasoning, and optimization), all within your Snowflake account, offering the same ease of use, scalability, security, and governance.

Users can build a knowledge graph using Python, and materialize it on top of their Snowflake data, shared with the RelationalAI app through Snowflake Streams.  Insights can be written to Snowflake tables and shared across the organization.

### What You'll Learn

In this quickstart, you'll learn how to:

- **Set Up Your Environment**: How to run graph algorithms on your data, where it already lives.
- **Prepare Data**: How to load data from a Snowflake table into a RelationalAI model
- **Build a Recommender System**: How to use the graph representation to build a recommendation algorithm


### What You’ll Need 
- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) Account
- Snowflake privileges on your user to [Install a Native Application](https://other-docs.snowflake.com/en/native-apps/consumer-installing#set-up-required-privileges)
- The [RAI Recommendation Jupyter notebook](https://github.com/RelationalAI/rai-samples/tree/main/samples/recommender-system/collaborative_filtering.ipynb) used in this quickstart

### What You’ll Build 
- A recommmender system on the 100k MovieLens database using Snowflake and RelationalAI

> 
> NOTE:  If you do not already have the RelationalAI Native App installed, please follow the instructions [here](https://relational.ai/docs/native_app/installation)

<!-- ------------------------ -->

## Data Preparation


To prepare data needed for this tutorial, follow these steps:

1. **Download Movielens-100K Dataset**: Obtain the [Movielens-100K dataset](https://grouplens.org/datasets/movielens/100k/) locally to use as sample data for your recommender system.

2. **Install Snowflake VS Code Extension**: Install the [Snowflake Visual Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=snowflake-computing.snowflake) for seamless integration with Snowflake in your development environment.

3. **Connect to Snowflake and Prepare Data**: Utilize the Snowflake extension to establish a connection to your Snowflake instance. Once connected, create tables and prepare your data directly from within VS Code by running the commands below:

> 
> IMPORTANT:
>
> - If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.
>
> - For each SQL script block below, select all the statements in the block and execute them top to bottom.

Run the following SQL commands to create the [database](https://docs.snowflake.com/en/sql-reference/sql/create-database.html) and prepare data needed for this tutorial.

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS RECOMMENDATION_DEMO;
USE DATABASE RECOMMENDATION_DEMO;
USE SCHEMA PUBLIC;
```

Run the following SQL commands to create an internal stage and upload files to the stage.

```sql
CREATE OR REPLACE STAGE movielens_stage;
-- Note: Change the file paths to your local paths before running these commands.
PUT file:///path/to/your/local/movielens_demo/ml-100k/u1.base @movielens_stage;
PUT file:///path/to/your/local/movielens_demo/ml-100k/u1.test @movielens_stage;
PUT file:///path/to/your/local/movielens_demo/ml-100k/u.item @movielens_stage;
```

Run the following SQL commands to create file formats.

```sql
CREATE OR REPLACE FILE FORMAT csv_format_pipe
  TYPE = 'CSV'
  RECORD_DELIMITER = '\n'
  SKIP_HEADER = 0
  FIELD_DELIMITER = '|'
  NULL_IF = ('NULL', 'null')
  EMPTY_FIELD_AS_NULL = TRUE
  ENCODING = 'ISO-8859-1' 
  FIELD_OPTIONALLY_ENCLOSED_BY = '0x22';
  
CREATE OR REPLACE FILE FORMAT csv_format_tab
  TYPE = CSV
  RECORD_DELIMITER = '\n'
  FIELD_DELIMITER = '\t'
  SKIP_HEADER = 0
  NULL_IF = ('NULL', 'null')
  EMPTY_FIELD_AS_NULL = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '0x22';
```

Run the following SQL commands to create tables for **TRAIN**, **TEST** and **MOVIE_DETAILS** that we will use during our solution.

```sql
CREATE OR REPLACE TABLE TRAIN (
    USER_ID VARCHAR(255),
    ITEM_ID VARCHAR(255),
    RATING FLOAT,
    TIMESTAMP TIMESTAMP
);

CREATE OR REPLACE TABLE TEST (
    USER_ID VARCHAR(255),
    ITEM_ID VARCHAR(255),
    RATING FLOAT,
    TIMESTAMP TIMESTAMP
);

CREATE OR REPLACE TABLE MOVIE_DETAILS (
    item_id VARCHAR(255),
    title VARCHAR(255),
    date DATE,
    A1 VARCHAR(255),
    A2 VARCHAR(255),
    A3 VARCHAR(255),
    A4 VARCHAR(255),
    A5 VARCHAR(255),
    A6 VARCHAR(255),
    A7 VARCHAR(255),
    A8 VARCHAR(255),
    A9 VARCHAR(255),
    A10 VARCHAR(255),
    A11 VARCHAR(255),
    A12 VARCHAR(255),
    A13 VARCHAR(255),
    A14 VARCHAR(255),
    A15 VARCHAR(255),
    A16 VARCHAR(255),
    A17 VARCHAR(255),
    A18 VARCHAR(255),
    A19 VARCHAR(255),
    A20 VARCHAR(255),
    A21 VARCHAR(255)
);
```

Run the following commands to load data from the stage to tables.

```sql
COPY INTO TRAIN
    FROM @movielens_stage
    FILE_FORMAT = csv_format_tab
    FILES = ('u1.base.gz');

COPY INTO TEST
    FROM @movielens_stage
    FILE_FORMAT = csv_format_tab
    FILES = ('u1.test.gz');

COPY INTO MOVIE_DETAILS
    FROM @movielens_stage
    FILE_FORMAT = csv_format_pipe
    FILES = ('u.item.gz');
```

By following these steps, you'll be ready to build and deploy your Recommender System using Snowflake seamlessly.

> 
> IMPORTANT: If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.

The last step is to stream data from snowflake tables into RelationalAI model:

```bash
rai imports:stream --source RECOMMENDATION_DEMO.PUBLIC.TRAIN --source RECOMMENDATION_DEMO.PUBLIC.TEST --source RECOMMENDATION_DEMO.PUBLIC.MOVIE_DETAILS --model recommendation_demo
```

- `--source`: This flag specifies the fully-qualified name of a Snowflake table or view.
- `--model`: This flag specifies the name of the model to which the data in the Snowflake table or view is streamed.

> 
> IMPORTANT: An import stream utilizes [change data capture](https://docs.snowflake.com/en/user-guide/streams)
to synchronize your Snowflake data with your RelationalAI model at an interval of once per minute. 
<!-- ------------------------ -->
## Building a Recommender System


The Notebook linked below covers the following steps.

1) Convert user-item interactions to a bipartite graph
2) Use user-item interactions to compute item-item by leveraging the functions supported by the graph analytics library
3) Use the similarities to predict the scores for all (user, movie) pairs. Each score is an indication of how likely it is for a user to interact with a movie
4) Sort the scores for every user in order to generate top-k recommendations
5) Evaluate performance using evaluation metrics that are widely used for recommender systems

### Walkthrough Notebook in Jupyter or Visual Studio Code

To get started, follow these steps:

1) If not done already, in a terminal window, browse to this folder and run `jupyter lab` at the command line. (You may also use other tools and IDEs such Visual Studio Code.)

2) Open and run through the cells in [collaborative_filtering.ipynb](https://github.com/RelationalAI/rai-samples/blob/main/samples/recommender-system/collaborative_filtering.ipynb)

> 
> IMPORTANT: Make sure in the Jupyter notebook the (Python) kernel is set to ***rai_recsys***-- which is the name of the environment created in **Setup Environment** step.

<!-- ------------------------ -->
## Conclusion And Resources

Thanks to RelationalAI’s Native App on Snowflake, we built a recommendation system with just a few steps. Although the dataset used was a small graph with thousands of nodes and edges, our solution can scale to real world datasets due to our cloud-native architecture that separates compute from storage.

In this Quickstart you learned

- How to find and install the RelationalAI Native App from the Snowflake Marketplace
- How to build a knowledge graph on top of your Snowflake data without having to extract data from Snowflake
- How to create a recommender system using graph algorithms on the MovieLens 100k dataset.

### Related Resources
- To learn about more about RelationalAI and view full documentation, visit [https://relational.ai](https://relational.ai)
- To see a brief summary of the recommender system you just built, see [Blogpost](https://medium.com/@haythemtellili/recommender-systems-with-relationalais-snowflake-native-app-68d9c76bb07f)
- [Snowflake Marketplace](https://app.snowflake.com/marketplace)
- More info on [Snowflake Native Apps](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)
- [Fork Repo on GitHub](https://github.com/RelationalAI/rai-samples/tree/main/samples/recommender-system)
- [Download Reference Architecture](/content/dam/snowflake-site/developers/2024/05/Community-Detection-using-RelationalAI-and-Snowflake-1.pdf)
- [Read the Blog](https://medium.com/@haythemtellili/recommender-systems-with-relationalais-snowflake-native-app-68d9c76bb07f)
- [Watch the Demo](https://youtu.be/QHlVp21icfg?list=TLGGkrjRtPl_vKMyNDA5MjAyNQ)

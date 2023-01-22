authors: Jeremiah Hansen
id: data_engineering_pipelines_with_snowpark_python
summary: This guide will provide step-by-step details for building data engineering pipelines with Snowpark Python
categories: data-engineering
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, Snowpark, Python

# Data Engineering Pipelines with Snowpark Python
<!-- ------------------------ -->
## Overview 
Duration: 15

> "Data engineers are focused primarily on building and maintaining data pipelines that transport data through different steps and put it into a usable state ... The data engineering process encompasses the overall effort required to create **data pipelines** that automate the transfer of data from place to place and transform that data into a specific format for a certain type of analysis. In that sense, data engineering isn’t something you do once. It’s an ongoing practice that involves collecting, preparing, transforming, and delivering data. A data pipeline helps automate these tasks so they can be reliably repeated. It’s a practice more than a specific technology." (From Cloud Data Engineering for Dummies, Snowflake Special Edition)

Are you interested in unleashing the power of Snowpark Python to build data engineering pipelines? Well then this Quickstart is for you! The focus here will be on building data engineering pipelines with Python, and not on data science. For examples of doing data science with Snowpark Python please check out our [Machine Learning with Snowpark Python: - Credit Card Approval Prediction](https://quickstarts.snowflake.com/guide/getting_started_snowpark_machine_learning/index.html?index=..%2F..index#0) Quickstart.

This Quickstart will cover a lot of ground, and by the end you will have built a robust data engineering pipeline using Snowpark Python stored procedures. That pipeline will process data incrementally, be orchestrated with Snowflake tasks, and be deployed via a CI/CD pipeline. You'll also learn how to use Snowflake's new developer CLI tool and Visual Studio Code extension! Here's a quick visual overview:

<img src="assets/data_pipeline_overview.png" width="800" />


So buckle up and get ready!

**Note**: As of 1/21/2023, the following features/tools used in this Quickstart are still in preview:
* [Snowflake Visual Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=snowflake.snowflake-vsc)
* [snowcli](https://github.com/Snowflake-Labs/snowcli)

### Prerequisites
* Familiarity with Python
* Familiarity with the DataFrame API
* Familiarity with Snowflake
* Familiatity with Git repositories and GitHub

### What You’ll Learn
You will learn about the following Snowflake features during this Quickstart:

* Snowflake Tables (not file-based)
* Data ingestion with COPY
* Schema inference
* Data sharing/marketplace (instead of ETL)
* Streams for incremental processing (CDC)
* Streams on views
* Python UDFs (with third-party packages)
* Python Stored Procedures
* Snowpark DataFrame API
* Snowpark Python programmability
* Warehouse elasticity (dynamic scaling)
* Visual Studio Code Snowflake native extension (PuPr, Git integration)
* SnowCLI (PuPr)
* Tasks (with Stream triggers)
* Task Observability
* GitHub Actions (CI/CD) integration

### What You’ll Need
You will need the following things before beginning:

* Snowflake
    * **A Snowflake Account**
    * **A Snowflake user created with ACCOUNTADMIN permissions**. This user will be used to get things setup in Snowflake.
* Anaconda
    * **Anaconda installed on your computer**. Check out the [Anaconda Installation](https://docs.anaconda.com/anaconda/install/) instructions for the details.
* SnowSQL
    * **SnowSQL installed on your computer**. Go to the [SnowSQL Download page](https://developers.snowflake.com/snowsql/) and see the [Installing SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html) page for more details.
* Visual Studio Code with required extensions
    * **Visual Studio Code installed on your computer**. Check out the [Visual Studio Code](https://code.visualstudio.com/) homepage for a link to the download page.
    * **Python extension installed**. Search for and install the "Python" extension (from Microsoft) in the *Extensions* pane in VS Code.
    * **Snowflake extension installed**. Search for and install the "Snowflake" extension (from Snowflake) in the *Extensions* pane in VS Code.
* GitHub account with lab repository forked and cloned locally
    * **A GitHub account**. If you don't already have a GitHub account you can create one for free. Visit the [Join GitHub](https://github.com/signup) page to get started.

### What You’ll Build
During this Quickstart you will accomplish the following things:

* Load Parquet data to Snowflake using schema inference
* Setup access to Snowflake Martketplace data
* Create a Python UDF to convert temperature
* Create a data engineering pipeline with Python stored procedures to icrementally process data
* Orchestrate the pipelines with tasks
* Monitor the pipelines with Snowsight
* Deploy the Snowpark Python stored procedures via a CI/CD pipeline


<!-- ------------------------ -->
## Quickstart Setup
Duration: 10

### Fork and Clone Repository for Quickstart
You'll need to create a fork of the repository for this Quickstart in your GitHub account. Visit the [tko-data-engineering GitHub Repository](https://github.com/sfc-gh-jhansen/tko-data-engineering) repository and click on the "Fork" button near the top right. Complete any required fields and click "Create Fork".

Next you will need to clone your new forked repository to your local computer. For connection details about your new Git repository, open the Repository, click on the green "Code" icon near the top of the page and copy the "HTTPS" link.

<img src="assets/git_repo_url.png" width="300" />

Use that link in VS Code to clone the repo to your computer. Please follow the instructions at [Clone and use a GitHub repository in Visual Studio Code](https://learn.microsoft.com/en-us/azure/developer/javascript/how-to/with-visual-studio-code/clone-github-repository) for more details. You can also clone the repository from the command line, if that's more comfortable for you, by running the following commands:

```bash
git clone <repo-url>
cd sfquickkstart-data-engineering-pipelines-with-snowpark-python/
```

Once the forked respository has been cloned to your local computer open the folder with VS Code.

### Configure Credentials
We will not be directly using [the SnowSQL command line client](https://docs.snowflake.com/en/user-guide/snowsql.html) for this Quickstart, but we will be storing our Snowflake connection details in the SnowSQL config file located at `~/.snowsql/config`. If that SnowSQL config file does not exist, please create an empty one.

Create a SnowSQL configuration for this lab by adding the following section to your `~/.snowsql/config` file (replacing the account, username, and password with your values):

```
[connections.dev]
account = myaccount
username = myusername
password = mypassword
rolename = HOL_ROLE
warehousename = HOL_WH
dbname = HOL_DB
```

### Create Anaconda Environment
Create and active a conda environment for this lab using the supplied `conda_env.yml` file. Run these commands from a terminal in the root of your local forked repository.

```bash
conda env create -f conda_env.yml
conda activate pysnowpark
```


<!-- ------------------------ -->
## Step 01: Setup Snowflake
Duration: 10

### Snowflake Extensions for VS Code
You can run SQL queries against Snowflake in many different ways (through the Snowsight UI, SnowSQL, etc.) but for this Quickstart we'll be using the Snowflake extension for VS Code. For a brief overview of Snowflake's native extension for VS Code, please check out our [VS Code Marketplace Snowflake extension page](https://marketplace.visualstudio.com/items?itemName=snowflake.snowflake-vsc).

### Run the Script
To set up all the objects we'll need in Snowflake for this Quickstart you'll need to run the `steps/01_setup.sql` script.

Start by clicking on the Snowflake extension in the left navigation bar in VS Code. Then login to your Snowflake account with a user that has ACCOUNTADMIN permissions. Once logged in to Snowflake, open the `steps/01_setup.sql` script in VS Code by going back to the file Explorer in the left navigation bar.

To execute multiple queries, select the ones you want to run and press CMD/CTRL+Enter. You can also use the "Execute All Statements" button in the upper right corner of the editor window to run all queries in the current file.


<!-- ------------------------ -->
## Step 02: Load Raw
Duration: 10

During this step we will be loading the raw Tasty Bytes POS and Customer loyalty data from raw Parquet files in `s3://sfquickstarts/data-engineering-with-snowpark-python/` to our `RAW_POS` and `RAW_CUSTOMER` schemas in Snowflake. And we're going to do this in Python using the Snowpark Python API. To put this in context, we are on step **#2** in our data flow overview:

<img src="assets/data_pipeline_overview.png" width="800" />

### Run the Script
To load the raw data, execute the `steps/02_load_raw.py` script. This can be done a number of ways in VS Code, from a terminal or directly by VS Code. The easiest to start with might be to execute it from the terminal. So open up a terminal in VS Code (Terminal -> New Terminal) in the top menu bar, then run the following commands (which assume that your terminal has the root of your repository open):

```bash
python 02_load_raw.py
```

While that is running, please open the script in VS Code and continue on this page to understand what is happening.

### Running Snowpark Python Locally
In this step you will be running the Snowpark Python code locally from your laptop. At the bottom of the script is a block of code that is used for local debugging (under the `if __name__ == "__main__":` block):

```python
# For local debugging
if __name__ == "__main__":
    # Add the utils package to our path and import the snowpark_utils function
    import os, sys
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

    from utils import snowpark_utils
    session = snowpark_utils.get_snowpark_session()

    load_all_raw_tables(session)
#    validate_raw_tables(session)

    session.close()
```

A few things to point out here. First, the Snowpark session is being created in the `utils/snowpark_utils.py` module. It has multiple methods for obtaining your credentials, and for this Quickstart it pulls them from the SnowSQL config file located at `~/.snowsql/config`. For more details please check out the code for the [utils/snowpark_utils.py module](https://github.com/sfc-gh-jhansen/tko-data-engineering/blob/main/utils/snowpark_utils.py).

Then after getting the Snowpark session it calls the `load_all_raw_tables(session)` method which does the heavy lifting. The next few sections will point out the key parts.

Finally, almost all of the Python scripts in this Quickstart include a local debugging block. Later on we will create Snowpark Python stored procedures and UDFs and those Python scripts will have a similar block. So this pattern is important to understand.

### Schema Inference

One very helpful feature in Snowflake is the ability to infer the schema of files in a stage that you wish to work with. This is accomplished in SQL with the [`INFER_SCHEMA()`](https://docs.snowflake.com/en/sql-reference/functions/infer_schema.html) function. The Snowpark Python API does this for you automatically when you call the `session.read()` method. Here is the code snippet:

```python
    # we can infer schema using the parquet read option
    df = session.read.option("compression", "snappy") \
                            .parquet(location)
```

### Data Ingestion with COPY

In order to load the data into a Snowflake table we will use the `copy_into_table()` method on a dataframe. This method will create the target table in Snoflake use the inferred schema and then call the highly optimized Snowflake [`COPY INTO &lt;table&gt;` Command](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table.html). Here is the code snippet:

```python
    df.copy_into_table("{}".format(tname))
```

### Snowflake Tables (Not File-Based)

One of the major advantages of Snowflake is being able to eliminate the need to manage a file-based data lake. And Snowflake was designed for this purpose from the beginning. In the step we are loading the raw data into a Snowflake managed table. Snowflake tables can natively support structued and semi-structure data and are stored in Snowflake's mature cloud table format.

Once loaded into Snowflake the data will be securely stored and managed, without the need to worry about securing and managing raw files. Additionally the data, whether raw or structured, can be transformed and querying in Snowflake using SQL or the language of your choice, without needing to manage separate compute services like Spark.

This is a huge advantage for Snowflake customers.


### Warehouse Elasticity (Dynamic Scaling)

With Snowflake there is only one type of user defined compute cluster, the [Virtual Warehouse](https://docs.snowflake.com/en/user-guide/warehouses.html), regardless of the language you use to process that data (SQL, Python, Java, Scala, Javascript, etc.). This makes working with data much simpler in Snowflake. And governance of the data is completely separated from the compute cluster, in other words there is no way to get around Snowflake governance regardless of the warehouse settings or language being used.

And these virtual warehouses can be dynamically scaled, in under a second for most sized warehouses! This means that in your code you can dynamically resize the compute environment to increase the amount of capacity to run a section of code in a fraction of the time, and then dynamically resized again to reduce the amount of capacity. And because of our per-second billing (with a sixty second minimum) you won't pay any extra to run that section of code in a fraction of the time!

Let's see how easy that is done. Here is the code snippet:

```python
    _ = session.sql("ALTER WAREHOUSE HOL_WH SET WAREHOUSE_SIZE = XLARGE").collect()

    # Some data processing code

    _ = session.sql("ALTER WAREHOUSE HOL_WH SET WAREHOUSE_SIZE = XSMALL").collect()
```

We will use this pattern a few more times during this Quickstart, so it's important to understand.


<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 


### What we've covered
We've covered a ton in this Quickstart, and here are the highlights:

* Snowflake Tables (not file-based)
* Data ingestion with COPY
* Schema inference
* Data sharing/marketplace (instead of ETL)
* Streams for incremental processing (CDC)
* Streams on views
* Python UDFs (with third-party packages)
* Python Stored Procedures
* Snowpark DataFrame API
* Snowpark Python programmability
* Warehouse elasticity (dynamic scaling)
* Visual Studio Code Snowflake native extension (PuPr, Git integration)
* SnowCLI (PuPr)
* Tasks (with Stream triggers)
* Task Observability
* GitHub Actions (CI/CD) integration


<!-- ------------------------ -->
## Extra
Duration: 2

### Info Boxes
> aside positive
> 
>  This will appear in a positive info box.

> aside negative
> 
>  This will appear in a negative info box.

### Buttons
<button>

  [This is a download button](link.com)
</button>

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

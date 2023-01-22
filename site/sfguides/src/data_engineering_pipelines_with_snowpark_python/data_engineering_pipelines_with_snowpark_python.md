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
* Schema detection
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
    * **A forked lab repository**. You'll need to create a fork of this lab repository in your GitHub account. Visit the [tko-data-engineering GitHub Repository](https://github.com/sfc-gh-jhansen/tko-data-engineering) and click on the "Fork" button near the top right. Complete any required fields and click "Create Fork".
    * **A local clone of the forked lab repository**. For connection details about your Git repository, open the Repository, click on the green "Code" icon near the top of the page and copy the "HTTPS" link. Use that link in VS Code to clone the repo to your computer. Please follow the instructions at [Clone and use a GitHub repository in Visual Studio Code](https://learn.microsoft.com/en-us/azure/developer/javascript/how-to/with-visual-studio-code/clone-github-repository) for more details.

### What You’ll Build
During this Quickstart you will accomplish the following things:

* Load Parquet data to Snowflake using schema detection
* Setup access to Snowflake Martketplace data
* Create a Python UDF to convert temperature
* Create a data engineering pipeline with Python stored procedures to icrementally process data
* Orchestrate the pipelines with tasks
* Monitor the pipelines with Snowsight
* Deploy the Snowpark Python stored procedures via a CI/CD pipeline


<!-- ------------------------ -->
## Environment Setup
Duration: 10

### SnowSQL
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

### Anaconda environment
Create and active a conda environment for this lab using the supplied `conda_env.yml` file. Run these commands from a terminal in the root of your local forked repository.

```bash
conda env create -f conda_env.yml
conda activate pysnowpark
```

### Snowflake
To set up all the objects we'll need in Snowflake for this Quickstart you'll need to run the `steps/01_setup.sql` script. You can execute the contents of the script a number of different ways (through the Snowsight UI, SnowSQL, etc.) but for this Quickstart we'll be using the Snowflake extension for Visual Studio Code (VS Code).

Start by clicking on the Snowflake extension in the left navigation bar in VS Code. Then login to your Snowflake account with a user that has ACCOUNTADMIN permissions. Once logged in to Snowflake, open the `steps/01_setup.sql` script in VS Code by going back to the file Explorer in the left navigation bar.

To execute multiple queries, select the ones you want to run and press CMD/CTRL+Enter. You can also use the "Execute All Statements" button in the upper right corner of the editor window to run all queries in the current file.


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


<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 


### What we've covered
We've covered a ton in this Quickstart, and here are the highlights:

* Snowflake Tables (not file-based)
* Data ingestion with COPY
* Schema detection
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

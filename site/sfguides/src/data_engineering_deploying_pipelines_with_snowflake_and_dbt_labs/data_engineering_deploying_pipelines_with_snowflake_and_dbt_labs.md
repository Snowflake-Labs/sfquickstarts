authors: Dmytro Yaroshenko
id: data_engineering_deploying_pipelines_with_snowflake_and_dbt_labs
summary: This guide will provide step-by-step details for building and deploying data engineering pipelines with Snowflake and dbt labs
categories: featured,data-engineering,notebooks
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, Notebooks, dbt

# Deploying pipelines with Snowflake and dbt labs
<!-- ------------------------ -->
## Overview 
Duration: 10

Notebooks are a very popular tool that are used to do everything from ad-hoc exploration of data to productionalized data engineering pipelines. While Notebooks can contain a mix of both Python and SQL, most of the time they're used for Python coding. In my previous Quickstart I detailed [how to build Python data engineering pipelines in Snowflake](https://quickstarts.snowflake.com/guide/data_engineering_pipelines_with_snowpark_python/index.html?index=..%2F..index#0) using Visual Studio Code, from a lower-level developer perspective.

This Quickstart will focus on how to build Python data engineering pipelines using Snowflake native Notebooks! Additionally, it will provide all the details needed to manage and deploy those Notebooks through an automated CI/CD pipeline from development to production! Here's a quick visual overview of what we'll accomplish in this Quickstart:

<img src="assets/context.png" width="800" />

> aside negative
> 
> **Note** - As of 6/11/2024, the [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks) are in Public Preview.

### What You’ll Learn
* How to ingest custom file formats (like Excel) with Snowpark from an external stage (such as an S3 bucket) into a Snowflake table
* How to access data from Snowflake Marketplace and use it for your analysis
* How to use Snowflake Notebooks and the Snowpark DataFrame API to build data engineering pipelines
* How to add logging to your Python data engineering code and monitor from within Snowsight
* How to execute SQL scripts from your Git repository directly in Snowflake
* How to use open-source Python libraries from curated Snowflake Anaconda channel
* How to use the Snowflake Python Management API to programmatically work with Snowflake objects
* How to use the Python Task DAG API to programatically manage Snowflake Tasks
* How to build CI/CD pipelines using Snowflake's Git Integration, the Snowflake CLI, and GitHub Actions
* How to deploy Snowflake Notebooks from dev to production

### What You'll Build
* A data share from the Snowflake Marketplace to access weather data
* A data engineering pipeline with a Notebook to ingest Excel files into Snowflake
* A data engineering pipeline with a Notebook to transform and aggreggate data
* A DAG (or Directed Acyclic Graph) of Tasks to orchestrate/schedule the pipelines
* A CI/CD pipeline to deploy the Notebooks to production

### Prerequisites
* Familiarity with Python
* Familiarity with the DataFrame API
* Familiarity with Snowflake
* Familiarity with Git repositories and GitHub

### What You’ll Need
You will need the following things before beginning:

* Snowflake account
    * **A Snowflake Account**. Visit the [Snowflake Account Sign In](https://app.snowflake.com/) page to log into your account or to sign up for a trial account.
    * **A Snowflake user created with ACCOUNTADMIN permissions**. This user will be used to get things setup in Snowflake.
    * **Anaconda Terms & Conditions accepted**. See Getting Started section in [Third-Party Packages](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#getting-started).
* GitHub account
    * **A GitHub account**. If you don't already have a GitHub account you can create one for free. Visit the [Join GitHub](https://github.com/signup) page to get started.


<!-- ------------------------ -->
## Quickstart Setup
Duration: 15

### Create a GitHub Personal Access Token
In order for Snowflake to authenticate to your GitHub repository, you will need to generate a personal access token. Please follow the [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) instructions to create your token.

Make sure to save the token before leaving the page, as we will be using it a couple of times during this Quickstart.

### Fork the Quickstart Repository
You'll need to create a fork of the repository for this Quickstart in your GitHub account. Visit the [Data Engineering with Snowflake Notebooks associated GitHub Repository](https://github.com/Snowflake-Labs/sfguide-data-engineering-with-notebooks) and click on the "Fork" button near the top right. Complete any required fields and click "Create Fork".

### Create the dev Branch
During this Quickstart we will do our development work in a `dev` branch of the repository. So let's create the `dev` branch in your forked repository now. To do that begin by clicking on the branch selector just above the list of files in the repository, type the word "dev" (all lowercase) into the "Find or create a branch..." box and then click on "Create branch dev from main" (see screenshot below).

<img src="assets/context.png" width="800" />

Your new branch will be created and you will now be back on the repository code page with your `dev` branch selected (notice the value of the branch selector).

### Configure GitHub Actions
By default GitHub Actions disables any workflows (or CI/CD pipelines) defined in the forked repository. This repository contains a workflow to deploy your Snowpark Notebooks, which we'll use later on. So for now enable this workflow by opening your forked repository in GitHub, clicking on the `Actions` tab near the top middle of the page, and then clicking on the `I understand my workflows, go ahead and enable them` green button.

<img src="assets/context.png" width="800" />

The last step to enable your GitHub Actions workflow is to create the required secrets. In order for your GitHub Actions workflow to be able to connect to your Snowflake account you will need to store your Snowflake credentials in GitHub. Action Secrets in GitHub are used to securely store values/variables which will be used in your CI/CD pipelines. In this step we will create secrets for each of the parameters used by the Snowflake CLI.

From the repository, click on the "Settings" tab near the top of the page. From the Settings page, click on the `Secrets and variables` then `Actions` tab in the left hand navigation. The `Actions` secrets should be selected. For each secret listed below click on `New repository secret` near the top right and enter the name given below along with the appropriate value (adjusting as appropriate).

<table>
    <thead>
        <tr>
            <th>Secret name</th>
            <th>Secret value</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>SNOWFLAKE_ACCOUNT</td>
            <td>myaccount</td>
        </tr>
        <tr>
            <td>SNOWFLAKE_USER</td>
            <td>myusername</td>
        </tr>
        <tr>
            <td>SNOWFLAKE_PASSWORD</td>
            <td>mypassword</td>
        </tr>
        <tr>
            <td>SNOWFLAKE_ROLE</td>
            <td>DEMO_ROLE</td>
        </tr>
        <tr>
            <td>SNOWFLAKE_WAREHOUSE</td>
            <td>DEMO_WH</td>
        </tr>
        <tr>
            <td>SNOWFLAKE_DATABASE</td>
            <td>DEMO_DB</td>
        </tr>
        <tr>
            <td>SNOWFLAKE_SCHEMA</td>
            <td>INTEGRATIONS</td>
        </tr>
    </tbody>
</table>

> aside positive
> 
>  **Tip** - For more details on how to structure the account name in SNOWFLAKE_ACCOUNT, see the account name discussion in [the Snowflake Python Connector install guide](https://docs.snowflake.com/en/user-guide/python-connector-install.html#step-2-verify-your-installation).

When you’re finished adding all the secrets, the page should look like this:

<img src="assets/context.png" width="800" />

> aside positive
> 
>  **Tip** - For an even better solution to managing your secrets, you can leverage [GitHub Actions Environments](https://docs.github.com/en/actions/reference/environments). Environments allow you to group secrets together and define protection rules for each of your environments.


<!-- ------------------------ -->
## Setup Snowflake
Duration: 10

Since the focus of this Quickstart is on Notebooks, we're going to use a Notebook to set up our Snowflake demo environment. 

### Download the 00 Notebook
The Notebook we're going to use to set up our Snowflake demo environment can be found in your forked repository. From the GitHub web UI open the `00_start_here.ipynb` file and then download the raw file (using one of the links near the top right of the page).

### Import the 00 Notebook to Snowflake
Follow these steps to import the Notebook into your Snowflake account:

* Log into Snowsight
* Browse to "Notebooks" in the left navigation (under "Projects")
* Click on arrow next to the blue "+ Notebook" button on top right, then select "Import .ipynb file"
* Select the `00_start_here.ipynb` file you downloaded previously
* Choose a database and schema for the notebook to live in and then a default warehouse for the notebook
* Click "Create"

### Run the 00 Setup Notebook Cells
Before you can run the set up steps in the `00_start_here.ipynb` Notebook you need to first add the `snowflake` package to it. To do that, follow these steps: 

* Open the Notebook
* Click on the "Packages" drop down on the top menu bar, near the right
* Type "snowflake" in the "Find Packages" search box and select it from the drop down

Once you have all the required packages configured, click the "Start" button on the top menu bar, near the right. Once the Notebook session has started you're ready to run cells in the Notebook. And notice how quickly the session starts up, especially compared to starting a Spark cluster!

Scroll down to the "Step 03 Setup Snowflake" section. You'll want to run all the cells in this section. But before doing so make sure and update the 4 `GITHUB_` SQL variables in the first `sql_step03_set_context` cell. Use the value of your GitHub personal access token in the `GITHUB_SECRET_PASSWORD` variable. Then run all the cells in this section. To run a given cell simply click anywhere in the cell to select it and press CMD/CTRL+Enter. You can alternatively click on the Run arrow near the top right of the cell.


<!-- ------------------------ -->
## Deploy to Dev
Duration: 5

During this step we will be deploying the dev versions of our two data engineering Notebooks: `DEV_06_load_excel_files` and `DEV_07_load_daily_city_metrics`. For this Quickstart you will notice that our main data engineering Notebooks will be named with a prefix for the environment label, like `DEV_` for dev and `PROD_` for prod. A full discussion of different approaches for managing multiple environments with Snowflake is out of scope for this Quickstart. For a real world use case, you may or may not need to do the same, depending on your Snowflake set up.

To put this in context, we are on step **#4** in our data flow overview:

<img src="assets/context.png" width="800" />

### Git in Snowsight
When you ran the setup cells in the `00_start_here.ipynb` Notebook in the previous step, you created a Git Integration in Snowflake for your forked GitHub repository! Please see [Using a Git repository in Snowflake](https://docs.snowflake.com/en/developer-guide/git/git-overview) for more details.

You can browse your Git repository in Snowsight, by using our Snowsight Git integration features. To do that, click on "Data" -> "Databases" in the left navigation. Then click on "DEMO_DB" database, then "INTEGRATIONS" schema, then "Git Repositories" and finally "DEMO_GIT_REPO". You will see the details and content of your Git repository in Snowsight. You can change branches and browse the files in the repo by clicking on the folder names to drill down.

### Deploy Notebooks
Scroll down to the "Step 04 Deploy to Dev" section of the `00_start_here.ipynb` Notebook and run the Python cell there. This cell will deploy both the `06_load_excel_files` and `07_load_daily_city_metrics` Notebooks to our `DEV_SCHEMA` schema (and will prefix both workbook names with `DEV_`).

### EXECUTE IMMEDIATE FROM with Jinja Templating
The [EXECUTE IMMEDIATE FROM](https://docs.snowflake.com/en/sql-reference/sql/execute-immediate-from) command is very powerful and allows you to run an entire SQL script directly from Snowflake. And you'll notice here that we executing a SQL script directly from the `main` branch of our Git repo (`@DEMO_GIT_REPO/branches/main`). At this point please review the contents of the `scripts/deploy_notebooks.sql` script in your forked repo to see what we just executed.

Also, please note that the `scripts/deploy_notebooks.sql` script also includes Jinja Templating. Jinja templating allows us to parameterize this script so we can run the same core logic in each environment! You will see later in step 9 that we will call this same script from our GitHub Actions pipeline in order to deploy these Notebooks to production.


<!-- ------------------------ -->
## Teardown
Duration: 2

Once you're finished with the Quickstart and want to clean things up, toggle back to the `00_start_here` Notebook and scroll down to the "Step 10 Teardown" section. Then just run the SQL commands in the `sql_step10` cell to remove all the objects created during the Quickstart.

Finally, you can delete the `00_start_here` Notebook. With the Notebook open click on the ":" button near the top right of the window and click on "Delete".

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 5

Congratulations! You have now built end-to-end data engineering pipelines with Notebooks in Snowflake. You've also seen how to follow a complete Software Development Life Cycle (SDLC) for data engineering with Notebooks, including integration with Git, deploying to multiple environments through a CI/CD pipeline, instrumenting your code for monitoring and debugging, and orchestrating the pipelines with Task DAGs. Here's a quick visual recap:

<img src="assets/context.png" width="800" />

Hopefully you now have the building blocks, and examples, you need to get started building your own data engineering pipelines with Notebooks. So, what will you build now?

### What You Learned
* How to ingest custom file formats (like Excel) with Snowpark from an external stage (such as an S3 bucket) into a Snowflake table
* How to access data from Snowflake Marketplace and use it for your analysis
* How to use Snowflake Notebooks and the Snowpark DataFrame API to build data engineering pipelines
* How to add logging to your Python data engineering code and monitor from within Snowsight
* How to execute SQL scripts from your Git repository directly in Snowflake
* How to use open-source Python libraries from curated Snowflake Anaconda channel
* How to use the Snowflake Python Management API to programmatically work with Snowflake objects
* How to use the Python Task DAG API to programatically manage Snowflake Tasks
* How to build CI/CD pipelines using Snowflake's Git Integration, the Snowflake CLI, and GitHub Actions
* How to deploy Snowflake Notebooks from dev to production

### Related Resources
* [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-data-engineering-with-notebooks)
* [Data Engineering Pipelines with Snowpark Python](https://quickstarts.snowflake.com/guide/data_engineering_pipelines_with_snowpark_python/index.html?index=..%2F..index#0) (Advanced Quickstart)
* [About Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
* [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/index)

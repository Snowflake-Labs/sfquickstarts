author: Jeremiah Hansen
id: data_engineering_with_snowpark_python_and_dbt
summary: This guide will provide step-by-step details for building data engineering pipelines with Snowpark Python and dbt
categories: data-engineering
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, dbt

# Data Engineering with Snowpark Python and dbt
<!-- ------------------------ -->
## Overview 
Duration: 3

<img src="assets/data_engineering_with_snowpark_python_and_dbt-1.png" width="600" />

This guide will provide step-by-step instructions for how to get started with Snowflake Snowpark Python and dbt's new Python-based models.

Add note about preview status of both these features.
Add note about carefully following the dbt install instructions below.

Snowpark Python summary
[Snowpark Developer Guide for Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/index.html)

dbt Python model summary
[dbt Python models](https://docs.getdbt.com/docs/building-a-dbt-project/building-models/python-models)

### Prerequisites

This guide assumes that you have a basic working knowledge of dbt, Python, and Anaconda.

### What You'll Learn

* The basics of Snowpark Python
* How to create Python-based models in dbt
* How to create and use Python UDFs in your dbt Python model
* How the integration between Snowpark Python and dbt's Python models works

### What You'll Need

You will need the following things before beginning:

1. Snowflake
    1. **A Snowflake Account.**
    1. **A Snowflake Database named DEMO_DB.**
    1. **A Snowflake User created with appropriate permissions.** This user will need permission to create objects in the DEMO_DB database.
1. Anaconda
    1. **Anaconda installed on your computer.** Check out the [Anaconda Installation](https://docs.anaconda.com/anaconda/install/) instructions for the details. 
1. dbt
    1. **dbt installed on your computer.** Since Python models in dbt are still in preview, you will need to manually specify the correct beta version of dbt. As of 9/10/2022, please follow these step (where `<env-name>` is any name you want for the Anaconda environment):
        1. `conda create -n <env-name> python=3.8`
        1. `conda activate <env-name>`
        1. `pip install dbt-core==1.3.0b1`
        1. `pip install dbt-snowflake==1.3.0b1`
1. Integrated Development Environment (IDE)
    1. **Your favorite IDE installed on your computer.** If you don’t already have a favorite IDE I would recommend the great, free, open-source [Visual Studio Code](https://code.visualstudio.com/).

The following are optional but will help you debug your Python dbt models:

1. **Python extension installed in your IDE.** For VS Code, install [the Python extension from Microsoft](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

### What You'll Build

* A simple dbt project with Python-based models!


<!-- ------------------------ -->
## Create the dbt Project
Duration: 2

The easiest way to get started with dbt, and ensure you have the most up-to-date dbt configurations, is to the run the `dbt init` command. The `dbt init` process will create two folders in the directory you run it from, a `logs` folder and a folder named the same as your project. So in a terminal change to the directory where you want the new dbt project folder created and execute `dbt init`. Follow the prompts to create your new project. For most of the prompts enter the value appropriate to your environment, but for **database** and **schema** enter the values below:

* Enter a name for your project (letters, digits, underscore): `<project name>`
* Which database would you like to use? ... Enter a number: `[1] snowflake`
* account (https://<this_value>.snowflakecomputing.com): `<snowflake account>`
* user (dev username): `<snowflake username>`
* Desired authentication type option (enter a number): `[1] password`
* password (dev password): `<snowflake password>`
* role (dev role): `<snowflake role>`
* warehouse (warehouse name): `<snowflake warehouse>`
* database (default database that dbt will build objects in): `DEMO_DB`
* schema (default schema that dbt will build objects in): `DEMO_SCHEMA`
* threads (1 or more) [1]: `1`

See [More Details](#more-details-on-dbt-init) below for a summary of what just happened. But after `dbt init` finished you will have a functional dbt project and the following default SQL models in the `models` folder:

```
models
|-- example
|--|-- my_first_dbt_model.sql
|--|-- my_second_dbt_model.sql
|--|-- schema.yml
```

To verify that everything is configured properly, open a terminal and execute `dbt run`. You should now have the following objects created in Snowflake in your `DEMO_DB.DEMO_SCHEMA` schema:

* A table named `my_first_dbt_model`
* A view named `my_second_dbt_model`

### More Details on dbt init
See the [dbt init documentation](https://docs.getdbt.com/reference/commands/init) for more details, but here's how they summary the process:

>If this is your first time ever using the tool, it will:
>
>* ask you to name your project
>* ask you which database adapter you're using (or to [install the one you need](https://docs.getdbt.com/docs/available-adapters))
>* prompt you for each piece of information that dbt needs to connect to that database: things like `account`, `user`, `password`, etc
>
> Then, it will:
>
>* Create a new folder with your project name and sample files, enough to get you started with dbt
>* Create a connection profile on your local machine. The default location is `~/.dbt/profiles.yml`. Read more in [configuring your profile](https://docs.getdbt.com/dbt-cli/configure-your-profile).



<!-- ------------------------ -->
## Create a Simple Python Model
Duration: 2


<!-- ------------------------ -->
## Understand How the Simple dbt Python Model Works
Duration: 2


<!-- ------------------------ -->
## Create a Python Model with a UDF
Duration: 2


<!-- ------------------------ -->
## Understand How the dbt Python Model with a UDF Works
Duration: 2


<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 4

Add closing remarks
Add links to Snowpark docs
Add links to dbt docs

### What We've Covered

* The basics of Snowpark Python
* How to create Python-based models in dbt
* How to create and use Python UDFs in your dbt Python model
* How the integration between Snowpark Python and dbt's Python models works

### Related Resources

* [Snowpark Developer Guide for Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/index.html)
* [dbt Python models](https://docs.getdbt.com/docs/building-a-dbt-project/building-models/python-models)

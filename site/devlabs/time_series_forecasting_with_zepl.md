summary: Time Series Forecasting with Zepl v3
id: time_series_forecasting_zepl 
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/devlabs/issues
tags: Getting Started, Data Science, Data Engineering, Modeling, Financial Services
authors: Zepl

# Time Series Forecasting with Zepl
<!-- ------------------------ -->
## Overview 
Duration: 1

In this guide, we'll be walking you through how to build a time series forecasting model using Zepl's data science notebook with data loaded from Snowflakes Data Marketplace!

### Prerequisites
- Familiarity with Python
- Familiarity with SQL

### What You’ll Learn 
- Using Zepl's fully managed data science notebook
- Cloning data from the Data Marketplace
- Accessing Python libraries in Zepl
- Introduction to [Facebook's Prophet library](https://facebook.github.io/prophet/docs/quick_start.html#python-api) for time series forecasting
- Notebook style reporting with built in data visualizations
- Write forecasted results from Zepl to Snowflake

### What You’ll Need 
- A cup of coffee and your brain
- *there are now downloads required for this guide!*

### What You’ll Build 
- A model to predict 15 days into the future of close values for the AMZN stock ticker

<!-- ------------------------ -->
## Get US Stock Market data in Snowflake
Duration: 10

### Create a Snowflake Account:
[Sign up for free](https://signup.snowflake.com/)

### Clone data from Snowflake's Data Marketplace
1. Login to Snowflake > Open the Data Marketplace 
2. Search for the 'US Stock Market Data for Data Science' 
</br> <img src="./assets/zepl_marketplace_chicklet.png" width="200" height="400" />
3. Select 'Get Data'. This user must have ACCOUNTADMIN privileges
4. Assign a database name and roles for who should have access to this database
5. Select Create Database > View Database
</br> <img src="./assets/zepl_marketplace_get_data.png" />

Positive
: You must have ACCOUNTADMIN privileges to clone this data set

#### *Troubleshooting* 
Check if the database was created properly
```sql
SELECT * FROM "ZEPL_US_STOCKS_DAILY"."PUBLIC"."STOCK_HISTORY" LIMIT 10
```

Check if privileges are set correctly:
This database needs to have `SELECT` privileges for a Role that your user has access to. Setting the `SELECT` privlage for the PUBLIC role will allow all users to read data from this database.
* View privilege: [Doc](https://docs.snowflake.com/en/sql-reference/sql/show-grants.html)
* Assign privileges: [Doc](https://docs.snowflake.com/en/sql-reference/sql/grant-privilege.html)

<!-- ------------------------ -->
## Connect Zepl to Snowflake  
Duration: 5

### Create a Zepl Account:
[Sign up for free using Partner Connect](https://new-docs.zepl.com/docs/getting-started/sign-up-for-zepl#snowflake-partner-connect)

### Connect to the US Stock Market Database
[Zepl Documentation](https://new-docs.zepl.com/docs/connect-to-data/snowflake)
1. Login to Zepl
2. Select _Resources_ > _Data Sources_ > _Snowflake_
</br> <img src="./assets/zepl_create_datasource.png" />
3. Enter the required information below > Select _Add_: </br> 
</br> <img src="./assets/zepl_us_stock_datasource.png" width="600" height="900" />

* __Account Details:__ Account, Warehouse, Database, and Schema should all match the values entered in Step 2
* __Credentials:__ Username, Password, and Role should match the Snowflake user and role with permissions to query this database
* __Credential Type:__ [Learn more here](https://new-docs.zepl.com/docs/connect-to-data/zepl-data-sources#data-source-security)

#### *Troubleshooting* 
Use the _Test Connection_ button to validate the user credentials and ROLE. Below is a table of example outputs:

|__Error Message__ | __Action__  |
|------------------|-------------|
|`Failed: Invalid credentials provided for the datasource` | Your credentials were entered incorrectly |
|`Failed: failed to run the test query: 390189 (08004): Role 'PRIVATE' specified in the connect string does not exist or not authorized. Contact your local system administrator, or attempt to login with another role, e.g. PUBLIC.` | Enter a new Snowflake ROLE |

<!-- ------------------------ -->
## Create a new notebook
Duration: 5

### Creating a blank notebook
[Zepl Documentation](https://new-docs.zepl.com/docs/using-the-zepl-notebook/zepl-notebook-experience/create-new-notebook)

1. From any screen, Select _Add New_ (upper left)
2. Select _+ New Notebook_
3. Enter Notebook Details
</br><img src="./assets/zepl_create_new_notebook.png" width="550" />

### Understanding Zepl's Notebook Options
__Resource Type:__ [Doc](https://new-docs.zepl.com/docs/configure-infrastructure/container-resource)

Zepl Containers are isolated environments that are used to execute code. Paired with an Image, these Containers provide a private runtime for a notebook when it spins up. Each of these Container has a single CPU core and varies in the memory allocated to the notebook session. These Containers can be quickly scaled up or down in the notebook settings for larger or smaller workloads. Each Container has a default time out period of 30 minutes.

__Image:__ [Doc](https://new-docs.zepl.com/docs/configure-infrastructure/images)

Zepl Images can help you and your team save significant time by making creating reproducible environments for all notebooks to access. The Zepl Image builds all of the libaries required to run a notebook so your users dont have to worry about long wait times for installing libraries at the beginning of every notebook and hoping that each notebook environment is configured the same.

__Spaces:__ [Doc](https://new-docs.zepl.com/docs/manage-your-organization/spaces)

A Zepl Space is a collection of notebooks that can be shared with built-in access controls.  The "My Notebooks" space is a private space dedicated to your user only. Typically, new spaces are created for a specific project or working group; it's a place for a group of people who are working together on a set of data science problems.

### Importing an existing notebook
Positive
: Complete notebook code can be found here: [Notebook](https://app.zepl.com/placecholder)

[Zepl Documentation](https://new-docs.zepl.com/docs/using-the-zepl-notebook/zepl-notebook-experience/importing-notebooks)

1. From any screen, Select _Add New_ (upper left)
2. Select _+ Import Notebook_
3. Type: _Fetch From URL_
4. Paste either link in the textfield labeled _Link to your notebook_: 
 * link from Zepl's Published Notebook: `https://app.zepl.com/viewonlynotebook`
 * link from Github repository: `https://github.repo.reponame/viewonlynotebook`
5. Apply

TODO: Insert Picture of final notebook...

<!-- ------------------------ -->
## Query Snowflake
Duration: 5
#### Attach Snowflake Data Source



<!-- ------------------------ -->
## Install and Import Python Libaries
Duration: 5

### Overview
Zepl provides several options for loading libraries. The two most used are Custom Images ([Account Activation Required](https://new-docs.zepl.com/docs/getting-started/trial-and-billing#activate-your-organization)) and install during notebook run time. For this guide we will use the python package manager `pip` to install all of our required libraries

### In the Zepl Notebook:
Add this code to the first paragraph and select run paragraph:
```sh
%python
# Install fbprophet Deendencies
!pip install pystan~=2.14 Cython>=0.22 cmdstanpy==0.9.68 numpy>=1.15.4 pandas>=1.0.4 matplotlib>=2.0.0 LunarCalendar>=0.0.9 convertdate>=2.1.2 holidays>=0.10.2 setuptools-git>=1.2 python-dateutil>=2.8.0 tqdm>=4.36.1
# Install fbprophet Library
!pip install fbprophet==0.7.1
```

Positive
: This code may take several minutes to complete execution. The container must start, download, and install all of the libraries. This is one reason to build your own images using our Custom Image builder so notebooks start up instantly with all of the required libraries!

#### Code Explained
`!pip install pystan~=2.14 Cython>=0.22 cmdstanpy==0.9.68 numpy>=1.15.4 pandas>=1.0.4 matplotlib>=2.0.0 LunarCalendar>=0.0.9 convertdate>=2.1.2 holidays>=0.10.2 setuptools-git>=1.2 python-dateutil>=2.8.0 tqdm>=4.36.1`</br>
<p>This statement uses the `!` to access the container CLI and calls the `pip install` linux command to install the required libraries that support the facebook prophet library. Each version is specified to ensure the notebook runs consistently. </p>

`!pip install fbprophet==0.7.1`</br>
<p>This statement installs the fbprophet library with a specific version.</p>

#### Add new paragraph
Add this code to the first paragraph and select run paragraph:
```python
%python
# Import Libraries
import pandas as pd
from fbprophet import Prophet
```

#### Code Explained
We must also import the libraries that were just installed in the previous paragraph.

#### Full output of code:
<img src="./assets/zepl_install_import_libraries.png" />

### Troubleshooting
* Startup time: This code may take several minutes to complete execution. The container must start, download, and install all of the libraries. This is one reason to build your own images using our Custom Image builder so notebooks start up instantly with all of the required libraries!
* Documentation on Facebook Prophet: [Link](https://facebook.github.io/prophet/)
* Known issue with the install documentation [here](https://facebook.github.io/prophet/docs/installation.html#python): A fix is outlined [here](ttps://github.com/facebook/prophet/issues/1856) and implemented in our code already

<!-- ------------------------ -->
## Visualize Data
Duration 5

<!-- ------------------------ -->
## Create Time Series Model
Duration 5

### Fit 

### Train

### Visualize

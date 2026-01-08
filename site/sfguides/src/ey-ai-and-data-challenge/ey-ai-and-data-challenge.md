author: Mike Johnson
id: ey-ai-and-data-challenge
language: en
summary: Getting Started with Snowflake Notebooks and Workspaces for the EY AI & Data Challenge
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/applied-analytics, snowflake-site:taxonomy/snowflake-feature/model-development 
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/ey-ai-and-data-challenge
open in snowflake: https://app.snowflake.com/templates?template=setup_account_data_challenge_template

# Getting Started with Snowflake Notebooks for the EY AI & Data Challenge
<!-- ------------------------ -->
## The 2026 EY AI & Data Challenge: Optimizing Clean Water Supply

One of the largest annual data challenges in the world with over 45,000 participants across 146 countries, the [EY AI & Data Challenge](https://challenge.ey.com/?utm_medium=institutions&utm_source=snowflake&utm_campaign=quickstart) gives innovators the opportunity to build skills while developing forward-thinking solutions to mitigate global sustainability issues. This year, the global competition invites university students, early career professionals and EY people to use AI and data to tackle one of humanity's most pressing needs: access to clean, safe water.

### What will participants do?
EY has joined forces with one of its key alliances, Snowflake, to empower the next generation of changemakers to turn data into real-world impact. 

Using Snowflake's AI Data Cloud and EY's platform, along with a combination of datasets, participants will develop cutting-edge machine learning models that forecast water quality in inland bodies - creating actionable insights that can transform public health policy and community outcomes.

### Prerequisites
- Experience with Python and Jupyter notebooks
- Passion for using your technical skills for global impact

### What You’ll Learn 
- How to run Python and SQL code in a Snowflake environment
- How to access and analyze geospatial data from Microsoft Planetary Computer
- How to incorporate other data sources to build your own Machine Learning model

### What You’ll Need 
- Register for the [EY AI & Data Challenge](https://challenge.ey.com/?utm_medium=institutions&utm_source=snowflake&utm_campaign=quickstart) 
- Create a Snowlake Trial Account with the custom link provided on the EY Data Challenge Portal - this link will enable special features that are required for the Data Challenge
- Download the Jupyter Notebook files and training data from the EY Data Challenge Portal

### What You’ll Build 
Once you complete this guide, you should be able to setup your own Snowflake Account, configure it to access the Microsoft Planetary Computer API, and run the "Getting Started Notebook" to conduct your own geospatial analysis of water sources and water quality.

## Overview of Snowflake Notebooks and Workspaces
[Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-overview) offer an interactive, cell-based programming environment for Python and SQL. With a Snowflake Notebook, you can perform exploratory data analysis, experiment with feature engineering for machine learning, and perform other data science tasks within Snowflake.

You can write and execute code, visualize results, and tell the story of your analysis all in one place.

* Explore and experiment with data already in Snowflake, or upload new data to Snowflake from local files, external cloud storage, or datasets from the Snowflake Marketplace.
* Write SQL or Python code and quickly compare results with cell-by-cell development and execution.
* Interactively visualize your data using embedded Streamlit visualizations and other libraries like Altair, Matplotlib, or seaborn.

Snowflake Notebooks have been available in Snowflake for a few years, so you might notice some differences in the original user experience (https://docs.snowflake.com/user-guide/ui-snowsight/notebooks) and the Workspaces environment. 

This guide will focus on the Workspaces environment, which is most similar to the experience you might have running Jupyter Notebooks on your local environment. It has enhanced features for CPU/GPU container compute resources, and enhanced collaboration capabilities with [Integrated Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git) and [Shared Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-shared). 

## Setup Snowflake Account
Standard Snowflake Trial accounts last only 30 days, so you will want to get the custom Snowflake Trial link from the EY Challenge website for a trial that lasts 120 days. 

It takes just a few minutes to signup, and you will receive an email link to your new Snowflake Account. 

When you sign in to your account for the first time, you will need to run a setup script in SQL. 

This script creates external network access to install PyPI packages and access Planetary Computer API endpoints. The template to run the SQL script is located in the Snowflake-Labs repo on [Github](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/ey-ai-and-data-challenge).

If you have already created your Snowflake account, the setup script can be accessed directly within Snowflake using this [deeplink](https://app.snowflake.com/templates?template=setup_account_data_challenge_template).

## Open Snowflake Notebook in Workspaces
If you are able to run the "Show Integrations" command and you see "DATA_CHALLENGE_EXTERNAL_ACCESS" listed in the results, then you are ready to start on the Getting Started Notebook.

It can be accessed directly as a Snowflake template [using this deeplink](https://app.snowflake.com/templates?template=getting_started_data_challenge_template)


## Upload Notebooks to your Workspace
If you have any trouble with the template link, the notebook also located in the [Snowflake-Labs repo on Github](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/ey-ai-and-data-challenge/getting_started_notebook.ipynb)

You can upload the notebook into your Workspace by clicking the "Add New" button and choosing "Upload Files".
    ![img](assets/add_new_upload_files.png)

## Start running the notebook

1. Click Connect and choose the External Access Integration "DATA_CHALLENGE_EXTERNAL_ACCESS"
    ![img](assets/connect_your_notebook.jpg)

2. Wait until the container is running and the kernel is connected
    ![img](assets/connected_kernel.jpg)    

3. Run the first few cells to create the requirements.txt file, then refresh the browser tab.

4. Run the "pip install" to load all the required python packages

5. After you install the python packages, restart the kernel. 

6. Run the remaining cells to call the Planetary Computer API, download satellite imagery data, and analyze it directly in your Notebook!

## Next Steps

There are a variety of resources to help you your knowledge about Snowflake's AI/ML features, integrations with Github, and collaboration features. 

Review the resources below and explore all of the things you can do with Snowflake Notebooks and AI/ML tools!


### Resources
- https://challenge.ey.com/?utm_medium=institutions&utm_source=snowflake&utm_campaign=quickstart
- [Workspaces Environment](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces) - a cloud computing environment that integrates with Github for team collaboration
- [Notebooks in Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-overview) - Jupyter Notebook functionality backed by powerful cloud computing resources
- [Integrating Workspaces with a Git repository](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git)
- [ML Modeling](https://docs.snowflake.com/en/developer-guide/snowflake-ml/modeling)
- [Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Snowflake ML Examples and Tutorials](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/examples-and-quickstarts)


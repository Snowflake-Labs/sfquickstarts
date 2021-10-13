summary: Learn how to get started with Jupyter Notebooks on Snowpark and use the DataFrame API.
id: getting_started_with_snowpark_dataframe_api
categories: Getting Started
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Snowpark, Data Engineering
authors: Robert Fehrmann

# Getting Started with Snowpark and the Dataframe API 

<!-- ------------------------ -->
## Overview
Duration: 3

![](assets/stock_small.jpg)

Snowtrek V2 is a project to show how to get started with Jupyter Notebooks on [Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/index.html), a new product feature announced by Snowflake for [public preview](https://www.snowflake.com/blog/welcome-to-snowpark-new-data-programmability-for-the-data-cloud/) during the 2021 Snowflake Summit. With Snowtrek V2 you will learn how to tackle real world business problems as straightforward as ELT processing but also as diverse as math with rational numbers with unbounded precision, sentiment analysis and machine learning.

Snowpark not only works with Jupyter Notebooks but with a variety of IDEs. Instructions on how to set up your favorite development environment can be found in the Snowpark documentation under [Setting Up Your Development Environment for Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/setup.html).

Snowpark is a new developer experience that lets developers interact with data without first having to extract it. It's the glue between different programming languages and Snowflake. 

Snowflake has always provided drivers (Python, Spark, JDBC, and many more) to access data in Snowflake from different programming environments. When accessing Snowflake through these drivers, results have to be passed back and forth for processing, which may raise performance and scalability concerns when processing big datasets. Snowflake also has user-defined functions or UDFs, which execute custom code directly within the Snowflake engine but UDFs did not have access to already existing standard libraries and had limited language support. 

With Snowpark, we remove both issues. The current version of Snowpark introduces support for Scala, a well know language for data piplines, ELT/ETL, ML, big data projects and other use cases. Snowpark enables us to take advantage of standard libraries to bring custom features directly to data to create a scalable and easy to use experience in the Data Cloud.

This repo is structured in multiple parts. Each part has a [notebook](notebook) with specific focus areas. All notebooks in this series require a Jupyter Notebook environment with a Scala kernel.  

All notebooks will be fully self contained, meaning that all you need for processing and analyzing datasets is a Snowflake account.  If you do not have a Snowflake account, you can sign up for a [free trial](https://signup.snowflake.com/). It doesn't even require a credit card.

Versions used in this notebook are up-to-date as of August 2021. Please update them as necessary in the Snowtire setup step.

### Prerequisites:
- Use of the [Snowflake free 30-day trial environment](https://trial.snowflake.com)
- All notebooks in this series require a Jupyter Notebook environment with a Scala kernel.  
  - If you do not already have access to that type of environment, Follow the instructions below to either run Jupyter locally or in the AWS cloud. 
- Instructions on how to set up your favorite development environment can be found in the Snowpark documentation under [Setting Up Your Development Environment for Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/setup.html).


### What you will learn
- [Part 1](https://github.com/snowflakecorp/snowtrek_V2/blob/main/notebook/part1/part1.ipynb)

    The first notebook in this series provides a quick-start guide and an introduction to the Snowpark DataFram API. The notebook explains the steps for setting up the environment (REPL), and how to resolve dependencies to Snowpark. After a simple "Hello World" example you will learn about the Snowflake DataFrame API, projections, filters, and joins.
 

- [Part 2](https://github.com/snowflakecorp/snowtrek_V2/blob/main/notebook/part2/part2.ipynb) 

    The second notebook in the series builds on the quick-start of the first part. Using the TPCH dataset in the sample database, it shows how to use aggregations and pivot functions in the Snowpark DataFrame API. Then it introduces UDFs and how to build a stand-alone UDF: a UDF that only uses standard primitives. From there, we will learn how to use third party Scala libraries to perform much more complex tasks like math for numbers with unbounded (unlimited number of significant digits) precision and how to perform sentiment analysis on an arbitrary string.
    
- [Part 3](https://github.com/snowflakecorp/snowtrek_V2/blob/main/notebook/part3/part3.ipynb) 

    The third notebook combines what you learned in part 1 and 2. It implements an end-to-end ML use case including data ingestion, ETL/ELT transformations, model training, model scoring, and result visualization.

<!-- ------------------------ -->
## Preparing your lab environment 
Duration: 10

### Option 1:  Running Jupyter locally

The following instructions show how to build a Notebook server using a Docker container.

1. Download and install [Docker](https://docs.docker.com/docker-for-mac/install/).
2. Make sure your docker desktop application is up and running.
3. Make sure you have at least 4GB of memory allocated to Docker:
    ![Docker Memory](assets/docker_memory.png)

4. Open your favorite terminal or command line tool / shell.

5. Clone the GitHub Lab repo: 
        cd ~
        mkdir DockerImages

        cd DockerImages
        git clone git@github.com:Snowflake-Labs/sfguide_snowpark_on_jupyter.git

6. Build the Docker container (this may take a minute or two, depending on your network connection speed)

        cd ~/DockerImages/sfguide_snowpark_on_jupyter/docker
        docker build -t snowparklab .

7. Starting your Local Jupyter environment

    Type the following commands to start the Snowtire container and mount the Snowtrek directory to the container. The command below assumes that you have cloned the git repo to ~/DockerImages/sfguide_snowpark_on_jupyter. Adjust the path if necessary. 

        cd ~/DockerImages/sfguide_snowpark_on_jupyter
        docker run -it --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v "$(pwd)":/home/jovyan/snowparklab --name snowparklab snowparklab

    The output should be similar to the following

        To access the server, open this file in a browser:
            file:///home/jovyan/.local/share/jupyter/runtime/jpserver-15-open.html
        Or copy and paste one of these URLs:
            http://162e383e431c:8888/lab?token=bdaead06c9944057a86f9d8a823cebad4ce66799d855be5d
            http://127.0.0.1:8888/lab?token=bdaead06c9944057a86f9d8a823cebad4ce66799d855be5d

8. Start a browser session (Safari, Chrome, ...). Paste the line with the local host address (127.0.0.1) printed in **your shell window** into the browser status bar and update the port (8888) to **your port** in case you have changed the port in the step above.

9. Stopping your Docker lab environment
    
    Type the following command into a new shell window when you want to stop your the tutorial. All changes/work will be saved on your local machine. 

        docker stop snowparklab
        

    This command will stop and then delete the container. When you want to restart the tutorial, just run the commands above in **Starting your Snowtrek environment**.


### Option 2:  Running Jupyter in the AWS cloud

In case you can't install docker on your local machine you could run the tutorial in AWS on an [AWS Notebook Instance](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html).

1. Create a Notebook instance

   ![Create Notebook](assets/create_notebook.png)

2. Create a Lifecycle Policy.

   ![Create Policy](assets/create_lifecycle_policy.png)

   Open the [lifecycle script](https://github.com/snowflakecorp/snowtrek_V2/blob/main/docker/onstart) and paste its content into the editor window.
    
   Creating the Notebook takes about 8 minutes.

3. Upload the tutorial folder (github repo zipfile)

4. Unzip folder

   Open the Launcher, start a termial window and run the command below (substitue <filename> with your filename.

        unzip SageMaker/<filename> -d SageMaker/

After you have set up either your docker or your cloud based notebook environment start with Part1 in the [Tutorial](#Tutorial).

<!-- ------------------------ -->
## Setup Jupyter
Duration: 10


First, we have to set up the Jupyter environment for our notebook. The full instructions for setting up the environment are in the Snowpark documentation [Configure Jupyter](https://docs.snowflake.com/en/developer-guide/snowpark/quickstart-jupyter.html#configuring-the-jupyter-notebook-for-snowpark).

#### Import the part 1 notebook
Open your Jupyter environment and import the ~/DockerImages/sfguide_snowpark_on_jupyter/notebook/part1/part1.ipynb

![Import Part1](assets/jupyter1.png)

#### Setup your credentials file
- Open the folder:  ~/DockerImages/sfguide_snowpark_on_jupyter/creds
- Make a copy of the template_credentials.txt and name it credentials.txt
- Create a folder named 'creds' in Jupyter

![Import Credentials](assets/jupyter2.png)

- Import the credentials.txt file into your Jupyter folder named 'creds'

![Import Credentials](assets/jupyter3.png)

- Double click the credential.txt file to open and edit it in the Jupyter environment
- Update the file to your Snowflake environment connection parameters

![Import Credentials](assets/credentials.png)


<!-- ------------------------ -->
## Introduction to the Snowpark DataFrame API: Hello World 
Duration: 10

This is the first notebook of a series to show how to use Snowpark on Snowflake. This notebook provides a quick-start guide and an introduction to the Snowpark DataFrame API. The notebook explains the steps for setting up the environment (REPL), and how to resolve dependencies to Snowpark. After a simple "Hello World" example you will learn about the Snowflake DataFrame API, projections, filters, and joins.

### Open the Part 1 notebook

Double click on the part1.ipynb to open it

![Import Credentials](assets/part1_open.png)

### Now read through and run each step in the notebook.

Positive
:  Return here once you have finished the notebook so you can read the conclusion & Next steps, and complete the guide.

![Import Credentials](assets/part1_run_step_1.png)

<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 2

Snowpark is a brand new developer experience that brings scalable data processing to the Data Cloud. In Part1 of this series, we learned how to set up a Jupyter Notebook and configure it to use Snowpark to connect to the Data Cloud. Next, we built a simple Hello World! program to test connectivity using embedded SQL. Then we enhanced that program by introducing the Snowpark Dataframe API. Lastly we explored the power of the Snowpark Dataframe API using filter, projection, and join transformations.

In the next post of this series, we will learn how to create custom Scala based functions and execute arbitrary logic directly in Snowflake using user defined functions (UDFs) just by defining the logic in a Jupyter Notebook!

We encourage you to continue with your free trial by loading your own sample or production data and by using some of the more advanced capabilities of Snowflake not covered in this lab. 

### Additional Resources:

- Read the [Definitive Guide to Maximizing Your Free Trial](https://www.snowflake.com/test-driving-snowflake-the-definitive-guide-to-maximizing-your-free-trial/) document
- Attend a [Snowflake virtual or in-person event](https://www.snowflake.com/about/events/) to learn more about our capabilities and customers
- [Join the Snowflake community](https://community.snowflake.com/s/topic/0TO0Z000000wmFQWAY/getting-started-with-snowflake)
- [Sign up for Snowflake University](https://community.snowflake.com/s/article/Getting-Access-to-Snowflake-University)
- [Contact our Sales Team](https://www.snowflake.com/free-trial-contact-sales/) to learn more

### What we've covered:

- Quick Start: Set up the environment
- Hello World: First steps
- Snowflake DataFrame API: Query the Snowflake Sample Datasets via Snowflake DataFrames

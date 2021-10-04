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

This is a project to learn how to get started with Jupyter Notebooks on [Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/index.html), a new product feature announced by Snowflake for [public preview](https://www.snowflake.com/blog/welcome-to-snowpark-new-data-programmability-for-the-data-cloud/) during the 2021 Snowflake Summit. With this guide you will learn how to tackle real world business problems as straightforward as ELT processing but also as diverse as math with rational numbers with unbounded precision, sentiment analysis and machine learning.

Snowpark not only works with Jupyter Notebooks but with a variety of IDEs. 

Snowpark is a new developer experience that lets developers interact with data without first having to extract it. It's the glue between different programming languages and Snowflake. 

Snowflake has always provided drivers (Python, Spark, JDBC, and many more) to access data in Snowflake from different programming environments. When accessing Snowflake through these drivers, results have to be passed back and forth for processing, which may raise performance and scalability concerns when processing big datasets. Snowflake also has user-defined functions or UDFs, which execute custom code directly within the Snowflake engine but UDFs did not have access to already existing standard libraries and had limited language support. 

With Snowpark, we remove both issues. The current version of Snowpark introduces support for Scala, a well know language for data piplines, ELT/ETL, ML, big data projects and other use cases. Snowpark enables us to take advantage of standard libraries to bring custom features directly to data to create a scalable and easy to use experience in the Data Cloud.

 



Versions used in this notebook are up-to-date as of August 2021. Please update them as necessary in the Snowtire setup step.

### Prerequisites:
- Use of the [Snowflake free 30-day trial environment](https://trial.snowflake.com)
- This guide is structured in multiple parts. Each part has a [notebook](notebook) with specific focus areas. All notebooks in this series require a Jupyter Notebook environment with a Scala kernel.  If you do not already have access to that type of environment, I would highly recommend that you use [Snowtire V2](https://github.com/zoharsan/snowtire_v2) and this excellent post [From Zero to Snowpark in 5 minutes](https://medium.com/snowflake/from-zero-to-snowpark-in-5-minutes-72c5f8ec0b55). Please note that Snowtire is not officially supported by Snowflake, and is provided as-is. Additional instructions on how to set up the environment with the latest versions can be found in the next section.
- Instructions on how to set up your favorite development environment can be found in the Snowpark documentation under [Setting Up Your Development Environment for Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/setup.html).


### What you will learn
- [Part 1](notebook/part1/part1.ipynb) 

    The first notebook in this series provides a quick-start guide and an introduction to the Snowpark DataFram API. The notebook explains the steps for setting up the environment (REPL), and how to resolve dependencies to Snowpark. After a simple "Hello World" example you will learn about the Snowflake DataFrame API, projections, filters, and joins.
 

- [Part 2](notebook/part2/part2.ipynb) 

    The second notebook in the series builds on the quick-start of the first part. Using the TPCH dataset in the sample database, it shows how to use aggregations and pivot functions in the Snowpark DataFrame API. Then it introduces UDFs and how to build a stand-alone UDF: a UDF that only uses standard primitives. From there, we will learn how to use third party Scala libraries to perform much more complex tasks like math for numbers with unbounded (unlimited number of significant digits) precision and how to perform sentiment analysis on an arbitrary string.
    
- [Part 3](notebook/part3/part3.ipynb) 

    The third notebook combines what you learned in part 1 and 2. It implements an end-to-end ML use case including data ingestion, ETL/ELT transformations, model training, model scoring, and result visualization.

<!-- ------------------------ -->
## Running Jupyter on Snowtire
Duration: 10

The following instructions show you how to build a Notebook server using a Docker container. After the base install of Snowtire V2, we will a add few parameters for *[nbextensions](https://jupyter-contrib-nbextensions.readthedocs.io/en/latest/install.html)*.

1. Download and install [Docker](https://docs.docker.com/docker-for-mac/install/).

1. Clone the Snowtire repo: 

        cd ~
        mkdir DockerImages
        cd DockerImages
        git clone https://github.com/zoharsan/snowtire_v2.git
        cd snowtire_v2/

1. Build the image and get the latest kernel and drivers:

        docker build --pull -t snowtire . \
        --build-arg odbc_version=2.23.2 \
        --build-arg jdbc_version=3.13.4 \
        --build-arg spark_version=2.9.1-spark_3.1 \
        --build-arg snowsql_version=1.2.14 \
        --build-arg almond_version=0.11.1 \
        --build-arg scala_kernel_version=2.12.12
        
1. Clone the Snowtrek: 

        cd ~/DockerImages
        git clone git@github.com:snowflakecorp/snowtrek_V2.git
        cd snowtrek_V2
        
1. Start the Snowtire container and mount the Snowtrek directory to the container. The command below assumes that you have cloned Snowtrek V2 to ~/DockerImages/snowtrek_V2. Adjust the path if necessary. 

        docker run -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v ~/DockerImages/snowtrek_V2:/home/jovyan/snowtrek_V2 --name snowtrek_v2 snowtire:latest
        
    The output should be similar to the following

        [I 2021-08-09 20:42:43.745 LabApp] JupyterLab extension loaded from /opt/conda/lib/python3.9/site-packages/jupyterlab
        [I 2021-08-09 20:42:43.745 LabApp] JupyterLab application directory is /opt/conda/share/jupyter/lab
        [I 20:42:43.751 NotebookApp] Serving notebooks from local directory: /home/jovyan
        [I 20:42:43.751 NotebookApp] Jupyter Notebook 6.4.0 is running at:
        [I 20:42:43.751 NotebookApp] http://7f4d1922ad40:8888/?token=c3223df0b33e6232bbb06f3e403d481da4bfe515f23873f2
        [I 20:42:43.751 NotebookApp]  or http://127.0.0.1:8888/?token=c3223df0b33e6232bbb06f3e403d481da4bfe515f23873f2
        [I 20:42:43.751 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).

1. Start a browser session (Safari, Chrome, ...). Paste the line with the local host address (127.0.0.1) printed in **your shell window** into the browser status bar and update the port (8888) to **your port** in case you have changed the port in the step above.

1. Use Docker commands to start and stop the container: 

        docker [start/stop/restart] snowtrek_v2
    
    After starting/restaring the container you can get the security token by running this command
    
        docker logs snowflake_v2

<!-- ------------------------ -->
## Configuring the jupyter notebook for Snowpark
Duration: 5

Now, we have to set up the environment for our notebook. The complete instructions for setting up the environment are in the Snowpark documentation: [configuring-the-jupyter-notebook-for-snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/quickstart-jupyter.html#configuring-the-jupyter-notebook-for-snowpark) as a reference.

Below are the basic steps:

### Step 1

Configure the notebook to use a Maven repository for a library that Snowpark depends on.

```
import sys.process._
val osgeoRepo = coursierapi.MavenRepository.of("https://repo.osgeo.org/repository/release")
interp.repositories() ++= Seq(osgeoRepo)
```

### Step 2

Create a directory (if it doesn't exist) for temporary files created by the REPL environment. To avoid any side effects from previous runs, we also delete any files in that directory.

Note: Make sure that you have the operating system permissions to create a directory in that location.

Note: If you are using multiple notebooks, you’ll need to create and configure a separate REPL class directory for each notebook.

```
import ammonite.ops._
import ammonite.ops.ImplicitWd._

// This folder is used to store generated REPL classes, which will later be used in UDFs.
// Please provide an empty folder path. This is essential for Snowpark UDFs to work
val replClassPath = pwd+"/repl_classes"

// Delete any old files in the directory.
import sys.process._
s"rm -rf $replClassPath" !

// Create the REPL class folder.
import sys.process._
s"mkdir -p $replClassPath" !
```

### Step 3

Configure the compiler for the Scala REPL. This does the following:

- Configures the compiler to generate classes for the REPL in the directory that you created earlier.
- Configures the compiler to wrap code entered in the REPL in classes, rather than in objects.
- Adds the directory that you created earlier as a dependency of the REPL interpreter.

Execute the code below:

```
// Generate all repl classes in REPL class folder
interp.configureCompiler(_.settings.outputDirs.setSingleOutput(replClassPath))
interp.configureCompiler(_.settings.Yreplclassbased.value = true)
interp.load.cp(os.Path(replClassPath))
```

#### Step 4

Import the Snowpark library from Maven.

```
import $ivy.`com.snowflake:snowpark:0.8.0`
```

To create a session, we need to authenticate ourselves to the Snowflake instance. Though it might be tempting to just override the authentication variables below with hard coded values, it's not considered best practice to do so.

Negative
: If you share your version of the notebook, you might disclose your credentials by mistake to the recipient. Even worse, if you upload your notebook to a public code repository, you might advertise your credentials to the whole world. To prevent this, you should keep your credentials in an external file (like we are doing here).


Copy the credentials template file [creds/template_credentials.txt](https://) to creds/credentials.txt and update the file with your credentials. Put your key files into the same directory or update the location in your credentials file.

Then, update your credentials in that file and they will be saved on your local machine. Even better would be to switch from user/password authentication to private key authentication.

```
import com.snowflake.snowpark._
import com.snowflake.snowpark.functions._

val session = Session.builder.configFile("creds/credentials.txt").create
```

### Step 5
Add the Ammonite kernel classes as dependencies for your UDF.

```
def addClass(session: Session, className: String): String = {
  var cls1 = Class.forName(className)
  val resourceName = "/" + cls1.getName().replace(".", "/") + ".class"
  val url = cls1.getResource(resourceName)
  val path = url.getPath().split(":").last.split("!").head
  session.addDependency(path)
  path
}
addClass(session, "ammonite.repl.ReplBridge$")
addClass(session, "ammonite.interp.api.APIHolder")
addClass(session, "pprint.TPrintColors")
```

## Hello World
Duration: 3

Congratulations! You have successfully connected from a Jupyter Notebook to a Snowflake instance. Now we are ready to write our first "Hello World" program using Snowpark. That is as easy as the line in the cell below. After you have executed the cell below:
```
session.sql("SELECT 'Hello World!' greeting").show()
```

 You should see an output similar to this: 

```
[scala-interpreter-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
[scala-interpreter-1]  INFO (Logging.scala:22) - Execute query [queryID: 019e28e6-05025203-0000-22410336b00a]  SELECT  *  FROM (SELECT 'Hello World!' greeting) LIMIT 10
----------------
|"GREETING"    |
----------------
|Hello World!  |
----------------
```
Positive
: Note that Snowpark has automatically translated the Scala code into the familiar "Hello World!" SQL statement. This means that we can execute arbitrary SQL by using the sql method of the session class.

However, this doesn't really show the power of the new Snowpark API. At this point it's time to review the Snowpark API documentation. It provides valuable information on how to use the Snowpark API.

Let's now create a new Hello World! cell, that uses the Snowpark API, specifically the DataFrame API. To use the DataFrame API we first create a row and a schema and then a DataFrame based on the row and the schema.

```
import com.snowflake.snowpark.types._

val helloWorldDf=session.createDataFrame(Seq(("Hello World!"))).toDF("Greeting")

helloWorldDf
   .show
```

## Conclusion & Next Steps

Duration: 2

Congratulations on completing this introductory lab exercise! You’ve mastered the Snowflake basics and are ready to apply these fundamentals to your own data. Be sure to reference this guide if you ever need a refresher.

We encourage you to continue with your free trial by loading your own sample or production data and by using some of the more advanced capabilities of Snowflake not covered in this lab. 
### Additional Resources:

- Read the [Definitive Guide to Maximizing Your Free Trial](https://www.snowflake.com/test-driving-snowflake-the-definitive-guide-to-maximizing-your-free-trial/) document
- Attend a [Snowflake virtual or in-person event](https://www.snowflake.com/about/events/) to learn more about our capabilities and customers
- [Join the Snowflake community](https://community.snowflake.com/s/topic/0TO0Z000000wmFQWAY/getting-started-with-snowflake)
- [Sign up for Snowflake University](https://community.snowflake.com/s/article/Getting-Access-to-Snowflake-University)
- [Contact our Sales Team](https://www.snowflake.com/free-trial-contact-sales/) to learn more

### What we've covered:

- how to create stages, databases, tables, views, and warehouses
- how to load structured and semi-structured data
- how to query data including joins between tables
- how to clone objects
- how to undo user errors
- how to create roles and users, and grant them privileges
- how to securely and easily share data with other accounts
id: getting_started_with_snowpark_python
summary: This guide provides the basic instructions for setting up a simple example using Snowpark for Python.
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter

# Getting Started Using Snowpark for Python
<!-- ------------------------ -->
## Overview
Duration: 1

Snowpark is a new developer experience that makes it easy to extend Snowflake by writing code that
uses objects (like DataFrames) rather than SQL statements to query and manipulate data. Snowpark
is designed to make building complex data pipelines easy, allowing developers to interact with
Snowflake directly without moving data. Snowpark uploads and runs your code in Snowflake so that
you don't need to move the data to a separate system for processing.

Snowpark is a [preview feature](https://docs.snowflake.com/en/release-notes/preview-features.html)
and currently provides APIs in Python and Scala.

### Prerequisites
- Familiarity with Python

### What You’ll Need
- A [Snowflake](https://www.snowflake.com/) account hosted on Amazon Web Services (AWS)
- [git](https://git-scm.com/downloads)
- Python 3.8

### What You’ll Learn
- How to create a DataFrame that loads data from a stage
- How to create a user-defined function for your Python code

### What You’ll Build
- A Python application that uses the Snowpark library to process data in a stage

<!-- ------------------------ -->
## Download the repository
Duration: 5

The demo can be found in a Snowflake GitHub repository. After installing git, you can clone the
repository using your terminal.

Open a terminal window, and run the following commands to change to the directory where you want
the repository cloned and clone the repository.

```console
cd {directory_where_you_want_the_repository}
git clone https://github.com/Snowflake-Labs/sfguide-snowpark-python-demo
```

Change to the directory of the repository that you cloned:

```console
cd sfguide-snowpark-python-demo
```

The demo directory includes the following files:

- `snowflake_connection.properties`: The examples read the settings from this file to connect to
  Snowflake. You will edit this file and specify the settings that you use to connect to a
  Snowflake database.

- `src/main/python/HelloWorld.py`: This is a simple example that uses the Snowpark library to
  connect to Snowflake, run the `SHOW TABLES` command, and print out the first 3 tables listed. You
  will run this example to verify that you can connect to Snowflake.

- `src/main/python/UDFDemoSetup.py`: This sets up the data and libraries needed for the
  user-defined function (UDF) for the demo. The UDF relies on a data file and files that need
  to be uploaded to internal named stages. After downloading and extracting the data and files,
  you will run this example to create those stages and upload those files.

- `src/main/python/UDFDemo`: This is a simple example of code that creates and calls a UDF.

<!-- ------------------------ -->
##  Configure the settings for connecting to Snowflake
Duration: 5

The demo directory contains a `snowflake_connection.properties` file used by the examples to
[create a session](https://docs.snowflake.com/en/developer-guide/snowpark/creating-session.html)
to connect to Snowflake.

Edit this file and replace the `<placeholder>` values with the values that you use to connect to
Snowflake. For example:

```console
URL = https://myaccount.snowflakecomputing.com
USER = myusername
PRIVATE_KEY_FILE = /home/username/rsa_key.p8
PRIVATE_KEY_FILE_PWD = my_passphrase_for_my_encrypted_private_key_file
ROLE = my_role
WAREHOUSE = my_warehouse
DB = my_db
SCHEMA = my_schema
```

The role that you choose must have permissions to create stages and write tables in the specified
database and schema.

For the properties in this file, you can use any
[connection parameter supported by the JDBC Driver](https://docs.snowflake.com/en/user-guide/jdbc-configure.html#label-jdbc-connection-parameters).

<!-- ------------------------ -->
##  Connect to Snowflake
Duration: 5

Next, run the `HelloWorld.py` example to verify that you can connect to Snowflake:

```console
todo 
```

Let's walk through the output that the HelloWorld application prints output if the application runs
successfully.

After creating a session, the application code
[Session](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.html#snowflake.snowpark.Session)
object with the settings specified in `snowflake_connection.properties`.

```python
session = Session.builder.configFile("snowflake_connection.properties").create()
```

You should see the following output:

```console
todo

```

Next, the application code
[creates a DataFrame](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark-python.html#working-with-dataframes)
to hold the results from executing the `SHOW TABLES` command:

```python
df = session.sql("show tables")
```

Note that this does not execute the SQL statement. 

A [DataFrame](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.html#snowflake.snowpark.DataFrame)
in Snowpark is lazily evaluated, which means that statements are not executed until you call a
method that performs an action. One such method is `show`, which prints out the first 10 rows in
the DataFrame.

```python
df.show()
```

As you can see in the output, `show` executes the SQL statement. The results are returned to the
DataFrame, and the first 10 rows in the DataFrame are printed out:

```console
todo
... (list of tables) ...

```

Now that you have verified that you can connect to Snowflake, you need to set up the data for the
demo.

<!-- ------------------------ -->
## Download the data file and libraries for the demo
Duration: 10

The demo uses the [sentiment140](https://www.kaggle.com/kazanova/sentiment140) dataset and
libraries from the [CoreNLP project](https://stanfordnlp.github.io/CoreNLP/).

Since the user-defined functions in the demo execute in Snowflake, you'll need to upload the 
files for these libraries to an internal stage to make them available to Snowflake. You'll also
need to upload the dataset to a stage, where your demo will access the data.

1. Go to the [sentiment140](https://www.kaggle.com/kazanova/sentiment140) page and click the
   Download link to download the ZIP archive containing the dataset.

1. Unzip the `training.1600000.processed.noemoticon.csv` from the `archive.zip` file that you downloaded:

1. [Download version 3.6.0 of the CoreNLP libraries](https://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip).

1. Unzip the libraries from the `stanford-corenlp-full-2015-12-09.zip` file that you downloaded.

1. In your `sfguide-snowpark-python-demo` directory, create a `tempfiles` directory for the data and
   files (e.g. `mkdir files_to_upload`).

1. Copy the following file extracted from `archive.zip` to your
   `sfguide-snowpark-python-demo/files_to_upload/` directory.

   - `training.1600000.processed.noemoticon.csv`

1. Copy the following file extracted from `stanford-corenlp-full-2015-12-09.zip` to your
   `sfguide-snowpark-python-demo/files_to_upload/` directory.

   - `stanford-corenlp-3.6.0.jar`
   - `stanford-corenlp-3.6.0-models.jar`
   - `slf4j-api.jar`
   - `ejml-0.23.jar`

In `sfguide-snowpark-python-demo/files_to_upload/`, you should now see the following files:

```console
$ pwd
<path>/sfguide-snowpark-python-demo

$ ls files_to_upload
ejml-0.23.jar					stanford-corenlp-3.6.0.jar
slf4j-api.jar					training.1600000.processed.noemoticon.csv
stanford-corenlp-3.6.0-models.jar
```

Next, you'll run the `UDFDemoSetup.py` example to create the stages for these files and upload
these files to those stages.

<!-- ------------------------ -->
## Upload the data file and libraries to internal stages
Duration: 20

Next, run the `UDFDemoSetup.py` example to create the stages for the data file and libraries
and upload those files to the stages.

```console
todo
```

Let's walk through the output that the UDFDemoSetup application prints output if the application
runs successfully.

After creating a session, the application code calls `uploadDemoFiles` (a utility function for the
purposes of setting up these demo files), which uses the Snowpark library to create the stage:

First, the example executes an SQL statement to create the stage:

```python
session.sql(s"create or replace stage $stageName").collect()
```

`collect` is a method that performs an action on a DataFrame, so calling the `collect` method
executes the SQL statement.

Next, the example uses the
[FileOperation](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.html#snowflake.snowpark.FileOperation)
object to upload files to the stage. You access an instance of this object through the
`Session.file` method.

To upload files (effectively running the PUT command), you call the `put` method of the
FileOperation object:

```python
res = session.file.put(s"${uploadDirUrl}/$filePattern", stageName)
```

The `put` method returns an Array of
[PutResult](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.html#snowflake.snowpark.PutResult),
objects, each of which contains the results for a particular file.

```python
res = session.file.put(s"${uploadDirUrl}/$filePattern", stageName)
res.foreach(r => Console.println(s"  ${r.sourceFileName}: ${r.status}"))
```

The example then executes the `LS` command to list the files in the newly created stage and prints
out the first 10 rows of output:

```python
session.sql(s"ls @$stageName").show()
```

You should see the following output:

```console
todo
```

<!-- ------------------------ -->
##  Run the UDF demo
Duration: 10

Next, run the `UDFDemo.py` example to create and call a UDF:

```console
todo
```

This example:

- loads the data from the demo file into a DataFrame
- creates a user-defined function (UDF) that analyzes a string and determines the sentiment of the
  words in the string
- calls the function on each value in a column in the DataFrame
- creates a new DataFrame that contains the column with the original data and a new column with the
  return value of the UDF
- creates a new DataFrame that just contains the rows where the function determined that the
  sentiment was happy

Let's take a closer look at the example and the output to see how the Snowpark library does this.

<!-- ------------------------ -->
##  Using shorthand notation for columns
Duration: 5

After creating the session, the example imports names from `implicits` in the `session`
***variable*** (which you defined when creating the session):

```python
import session.implicits._
```

This statement allows you to use shorthand to refer to columns (e.g. `'columnName` and
`$"columnName"`) when passing arguments to DataFrame methods.

<!-- ------------------------ -->
##  Load data from a stage
Duration: 5

Next, the example creates a DataFrame that is set up to
[read data from a file in a stage](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark-python.html#working-with-files-in-a-stage).
To do this, the example uses a
[DataFrameReader](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.html#snowflake.snowpark.DataFrameReader)
object.

Because the demo file is a CSV file, you must first define the schema for the file. In Snowpark,
you do this by creating a `Seq` of
[StructField](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.types.html#snowflake.snowpark.types.StructField)
objects that identify the names and types of each column of data. These objects are members of the
[snowflake.snowpark.types](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.types.html#module-snowflake.snowpark.types)
package.

```python
import snowflake.snowpark.types.{StringType, StructField, StructType}
...
schema = Seq(
  StructField("target", StringType),
  StructField("ids", StringType),
  StructField("date", StringType),
  StructField("flag", StringType),
  StructField("user", StringType),
  StructField("text", StringType),
)
```

Next, the example accesses a `DataFrameReader` object through the `Session.read` method. The
`DataFrameReader` object provides methods that you use to specify the schema, options, and type of
the file to load.

These methods for setting the schema and options return a `DataFrameReader` object with the schema
and options set. This allows you to chain these method calls, as shown below. The method for
specifying the type of file (the `csv` method, in this case) returns a DataFrame that is set up to
load the data from the specified file.

```python
origData = session
  .read
  .schema(StructType(schema))
  .option("compression", "gzip")
  .csv(s"@${UDFDemoSetup.dataStageName}/${UDFDemoSetup.dataFilePattern}")
```

In this example, `UDFDemoSetup.dataStageName` and `UDFDemoSetup.dataFilePattern` refer to the name
of the stage and the files that you uploaded to that stage earlier when you ran the `UDFDemoSetup`
example.

The example returns the DataFrame `origData`.

As explained earlier, DataFrames are lazily evaluated, which means that they don't load data until
you call a method to retrieve the data. You can call additional methods to transform the DataFrame
(as the next line of code does) before you can call the method to retrieve the data.

Next, the example returns a new DataFrame (`tweetData`) that just contains the column with the
tweets (the column named `text`) with the first 100 rows of data from the original DataFrame
`origData`.

The `drop` and `limit` methods in the example each returns a new DataFrame that has been
transformed by this method. Because each method returns a new DataFrame that has been transformed
by the method, you can chain the method calls, as shown below:

```python
tweetData = origData.drop('target, 'ids, 'date, 'flag, 'user).limit(100)
```

At this point, the DataFrame `tweetData` does not contain the actual data. In order to load the
data, you must call a method that performs an action (`show`, in this case).

```python
Console.println("Text of the first 10 tweets")
tweetData.show()
```

In the output, the Snowpark library prints an `INFO` level message indicating that the query was
submitted for execution.

```console
todo

Text of the first 10 tweets
------------------------------------------------------
|"TEXT"                                              |
------------------------------------------------------
|"...                                                |
```

<!-- ------------------------ -->
##  Define a UDF
Duration: 5

Next, the example defines a UDF that performs the sentiment analysis. The UDF relies on libraries
that are packaged in separate files, so you'll need to point the Snowpark library to those 
files. You do this by calling the `Session.addDependency` method.

The example adds these files as dependencies:

```python
session.addDependency(s"@${UDFDemoSetup.myStageName}/stanford-corenlp-3.6.0.jar.gz")
session.addDependency(s"@${UDFDemoSetup.myStageName}/stanford-corenlp-3.6.0-models.jar.gz")
session.addDependency(s"@${UDFDemoSetup.myStageName}/slf4j-api.jar.gz")
session.addDependency(s"@${UDFDemoSetup.myStageName}/ejml-0.23.jar.gz")
```

In this example, `UDFDemoSetup.myStageName` refers to the name of the stage where you uploaded
files earlier (when you ran the `UDFDemoSetup` example).

The example calls the `udf` function in the `snowflake.snowpark.functions` object to define
the UDF. The UDF passes in each value in a column of data to the `analyze` method.

```python
import snowflake.snowpark.functions._
...
sentimentFunc = udf(analyze(_))
```

At this point, the Snowpark library adds the files for Snowpark and for your example as
dependencies (like the dependencies that it specified earlier).

Next, the Snowpark library creates a temporary stage for these files and uploads the files for Snowpark and for your application code to the stage. Snowpark also
compiles your UDF and uploads the file to the stage.

Finally, the library defines the UDF in your database:

Next, the example creates a new DataFrame (`analyzed`) that transforms the `tweetData` DataFrame by
adding a column named `sentiment`. `sentiment` contains the results from calling the UDF on the
corresponding value in the `text` column.

```python
analyzed = tweetData.withColumn("sentiment", sentimentFunc('text))
```

The example creates another DataFrame (`happyTweets`) that transforms the `analyzed` DataFrame to
include only the rows where the `sentiment` contains the value `3`.

```python
happyTweets = analyzed.filter('sentiment == 3)
```

Next, the example calls the `show` method to execute the SQL statements (including the UDF),
retrieve the results into the Dataframe, and print the first 10 rows.

```python
happyTweets.show()
```

Finally, the example
[saves the data in the DataFrame to a table](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark-python.html#label-snowpark-python-dataframe-save-table)
named `demo_happy_tweets`.
To do this, the example uses a
[DataFrameWriter](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/_autosummary/snowflake.snowpark.html#snowflake.snowpark.DataFrameWriter) object,
which is retrieved by calling the `DataFrame.write` method.

The example overwrites any existing data in the table by passing `SaveMode.Overwrite` to the `mode`
method of the `DataFrameWriter` object.

```python
import snowflake.snowpark.SaveMode.Overwrite
...
happyTweets.write.mode(Overwrite).saveAsTable("demo_happy_tweets")
```

## Conclusion & Next Steps
Duration: 1

You've now used Snowpark to perform sentiment analysis on tweets. A sample dataset of tweets were provided for this guide. If you want to automatically ingest new tweets as they are written, follow the [Auto Ingest Twitter Data into Snowflake](/guide/auto_ingest_twitter_data/) guide.

### What We've Covered
- Data Loading: Load Twitter streaming data in an event-driven, real-time fashion into Snowflake with Snowpipe
- Semi-structured data: Querying semi-structured data (JSON) without needing transformations
- Secure Views: Create a Secure View to allow data analysts to query the data
- Snowpipe: Overview and configuration

### Related Resources
- [Snowpark Developer Guide for Python](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark-python.html)
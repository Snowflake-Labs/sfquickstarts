id: getting_started_with_snowpark
summary: This guide provides the basic instructions for setting up a simple example using Snowpark.
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter

# Getting Started Using Snowpark
<!-- ------------------------ -->
## Overview
Duration: 1

Snowpark is a new developer experience that makes it easy to extend Snowflake by writing code that
uses objects (like DataFrames) rather than SQL statements to query and manipulate data. Snowpark
is designed to make building complex data pipelines easy, allowing developers to interact with
Snowflake directly without moving data. Snowpark uploads and runs your code in Snowflake so that
you don't need to move the data to a separate system for processing.

Snowpark is a [preview feature](https://docs.snowflake.com/en/release-notes/preview-features.html) and currently provides an API in Scala.

### Prerequisites
- Familiarity with Scala

### What You’ll Need
- A [Snowflake](https://www.snowflake.com/) account hosted on Amazon Web Services (AWS)
- [git](https://git-scm.com/downloads)
- [SBT](https://www.scala-sbt.org/)

You can also use a development tool or environment that supports SBT projects for Scala 2.12
(specifically, version 2.12.9 or later 2.12.x versions). Snowpark does not yet support versions
of Scala after 2.12 (for example, Scala 2.13).

### What You’ll Learn
- How to create a DataFrame that loads data from a stage
- How to create a user-defined function for your Scala code

### What You’ll Build
- A Scala application that uses the Snowpark library to process data in a stage

<!-- ------------------------ -->
## Download the repository
Duration: 5

The demo can be found in a Snowflake GitHub repository. After installing git, you can clone the
repository using your terminal.

Open a terminal window, and run the following commands to change to the directory where you want
the repository cloned, and then clone the repository.

```console
cd {directory_where_you_want_the_repository}
git clone https://github.com/Snowflake-Labs/sfguide-snowpark-demo
```

Change to the directory of the repository that you cloned:

```console
cd sfguide-snowpark-demo
```

The demo directory includes the following files:

- `build.sbt`: This is the SBT build file for this demo project.

- `snowflake_connection.properties`: Examples in this demo read settings from this file to connect to
  Snowflake. You will edit this file and specify the settings that you use to connect to a
  Snowflake database.

- `src/main/scala/HelloWorld.scala`: This is a simple example that uses the Snowpark library. It
  connects to Snowflake, runs the `SHOW TABLES` command, and prints out the first three tables listed. Run this example to verify that you can connect to Snowflake.

- `src/main/scala/UDFDemoSetup.scala`: This sets up the data and libraries needed for the
  user-defined function (UDF) for the demo. The UDF relies on a data file and JAR files that need
  to be uploaded to internal named stages. After downloading and extracting the data and JAR files,
run this example to create those stages and upload those files.

- `src/main/scala/UDFDemo`: This is a simple code example that creates and calls a UDF.

<!-- ------------------------ -->
##  Configure the settings for connecting to Snowflake
Duration: 5

The demo directory contains a `snowflake_connection.properties` file that the examples use to
[create a session](https://docs.snowflake.com/en/developer-guide/snowpark/creating-session.html) to connect to Snowflake.

Edit this file and replace the `&lt;placeholder&gt;` values with the values that you use to connect to
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

For the properties in this file, use any [connection parameter supported by the JDBC Driver](https://docs.snowflake.com/en/user-guide/jdbc-configure.html#label-jdbc-connection-parameters).

<!-- ------------------------ -->
##  Connect to Snowflake
Duration: 5

Next, using the [SBT command-line tool](https://www.scala-sbt.org/1.x/docs/Running.html), build and run the `HelloWorld.scala` example to verify that you can connect to Snowflake:

```console
sbt "runMain HelloWorld"
```

Let's walk through the output that the HelloWorld application prints when it runs successfully.

After creating a session, the application code creates a [Session](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/Session.html) object with the settings specified in `snowflake_connection.properties`.

```scala
val session = Session.builder.configFile("snowflake_connection.properties").create
```

For this part of the example, you should just see the following output:

```console
[info] running HelloWorld

=== Creating the session ===

[run-main-0]  INFO (Logging.scala:22) - Closing stderr and redirecting to stdout
[run-main-0]  INFO (Logging.scala:22) - Done closing stderr and redirecting to stdout
```

Next, the application code [creates a DataFrame](https://docs.snowflake.com/en/developer-guide/snowpark/working-with-dataframes.html) to hold the results from executing the `SHOW TABLES` command:

```scala
val df = session.sql("show tables")
```

Note that this does not execute the SQL statement. The output does not include any `INFO` messages that indicate that the Snowpark library executed the SQL statement:

```console
=== Creating a DataFrame to execute a SQL statement ===

[run-main-0]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
```

A [DataFrame](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrame.html) in Snowpark is lazily evaluated, which means that statements are not executed until you call a
method that performs an action. One such method is `show`, which prints out the first 10 rows in
the DataFrame.

```scala
df.show()
```

As you can see in the output, `show` executes the SQL statement. The results are returned to the
DataFrame, and the first 10 rows in the DataFrame are printed out:

```console
=== Execute the SQL statement and print the output ===

[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] show tables
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
|"created_on"             |"name"             |"database_name"  |"schema_name"  |"kind"  |"comment"  |"cluster_by"  |"rows"  |"bytes"  |"owner"     |"retention_time"  |"automatic_clustering"  |"change_tracking"  |"is_external"  |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
... (list of tables) ...
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

```

Now that you have verified that you can connect to Snowflake, you need to set up the data for the
demo.

<!-- ------------------------ -->
## Download the data file and libraries for the demo
Duration: 10

This demo uses the [sentiment140](https://www.kaggle.com/kazanova/sentiment140) dataset and
libraries from the [CoreNLP project](https://stanfordnlp.github.io/CoreNLP/).

Because the user-defined functions in the demo execute in Snowflake, you have to upload the JAR
files for these libraries to an internal stage to make them available to Snowflake. You  also
need to upload the dataset to a stage, where the demo will access the data.

1. Go to the [sentiment140](https://www.kaggle.com/kazanova/sentiment140) page and click
   **Download** to download the ZIP archive containing the dataset.

1. Unzip `training.1600000.processed.noemoticon.csv` from the `archive.zip` file that you downloaded.

1. [Download version 3.6.0 of the CoreNLP libraries](https://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip).

1. Unzip the libraries from the `stanford-corenlp-full-2015-12-09.zip` file that you downloaded.

1. In your `sfguide-snowpark-demo` directory, create a `tempfiles` directory for the data and JAR
   files (for example: `mkdir files_to_upload`).

1. Copy the following file extracted from `archive.zip` to your
   `sfguide-snowpark-demo/files_to_upload/` directory:

   - `training.1600000.processed.noemoticon.csv`

1. Copy the following files extracted from `stanford-corenlp-full-2015-12-09.zip` to your
   `sfguide-snowpark-demo/files_to_upload/` directory.

   - `stanford-corenlp-3.6.0.jar`
   - `stanford-corenlp-3.6.0-models.jar`
   - `slf4j-api.jar`
   - `ejml-0.23.jar`

In `sfguide-snowpark-demo/files_to_upload/`, you should now see the following files:

```console
$ pwd
<path>/sfguide-snowpark-demo

$ ls files_to_upload
ejml-0.23.jar					stanford-corenlp-3.6.0.jar
slf4j-api.jar					training.1600000.processed.noemoticon.csv
stanford-corenlp-3.6.0-models.jar
```

Next, run the `UDFDemoSetup.scala` example to create the stages for these files, and upload
the files to the stages.

<!-- ------------------------ -->
## Upload the data file and libraries to internal stages
Duration: 20

Next, run the `UDFDemoSetup.scala` example to create the stages for the data file and libraries,
and upload those files to the stages.

```console
sbt "runMain UDFDemoSetup"
```

Let's review the output that the UDFDemoSetup application prints when the application
runs successfully.

After creating a session, the application code calls `uploadDemoFiles` (a utility function that sets up these demo files), which in turn uses the Snowpark library to create the stage.

First, the example executes an SQL statement to create the stage:

```scala
session.sql(s"create or replace stage $stageName").collect()
```

`collect` is a method that performs an action on a DataFrame, so calling the `collect` method
executes the SQL statement.

Next, the example uses the
[FileOperation](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/FileOperation.html)
object to upload files to the stage. You access an instance of this object through the
`Session.file` method.

To upload files (effectively running the PUT command), you call the `put` method of the
FileOperation object:

```scala
val res = session.file.put(s"${uploadDirUrl}/$filePattern", stageName)
```

The `put` method returns an Array of
[PutResult](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/PutResult.html)
objects, each of which contains the results for a particular file.

```scala
val res = session.file.put(s"${uploadDirUrl}/$filePattern", stageName)
res.foreach(r => Console.println(s"  ${r.sourceFileName}: ${r.status}"))
```

The example then executes the `LS` command to list the files in the newly created stage and prints
out the first 10 rows of output:

```scala
session.sql(s"ls @$stageName").show()
```

You should see the following output:

```console
=== Creating the stage @snowpark_demo_data ===

[run-main-0]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
[run-main-0]  INFO (Logging.scala:22) - Actively querying parameter QUERY_TAG from server.
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session set query_tag = 'com.snowflake.snowpark.DataFrame.collect
UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:31)'
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] create or replace stage snowpark_demo_data
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session unset query_tag

=== Uploading files matching training.1600000.processed.noemoticon.csv to @snowpark_demo_data ===

[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session set query_tag = 'com.snowflake.snowpark.FileOperation.put
UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:35)'
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: ]  PUT file:///<path>/files_to_upload/training.1600000.processed.noemoticon.csv @snowpark_demo_data
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session unset query_tag
  training.1600000.processed.noemoticon.csv: UPLOADED

=== Files in @snowpark_demo_data ===

[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] ls @snowpark_demo_data
---------------------------------------------------------------------------------------------------------------------------------------
|"name"                                              |"size"    |"md5"                                |"last_modified"                |
---------------------------------------------------------------------------------------------------------------------------------------
|snowpark_demo_data/training.1600000.processed.n...  |85088032  |0091555c0d67ddf77a74de919a84ec41-17  |Sun, 13 Jun 2021 15:59:08 GMT  |
---------------------------------------------------------------------------------------------------------------------------------------


=== Creating the stage @snowpark_demo_udf_dependency_jars ===

[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session set query_tag = 'com.snowflake.snowpark.DataFrame.collect
UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:31)'
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] create or replace stage snowpark_demo_udf_dependency_jars
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session unset query_tag

=== Uploading files matching *.jar to @snowpark_demo_udf_dependency_jars ===

[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session set query_tag = 'com.snowflake.snowpark.FileOperation.put
UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:35)'
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: ]  PUT file:///<path>/files_to_upload/*.jar @snowpark_demo_udf_dependency_jars
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] alter session unset query_tag
  stanford-corenlp-3.6.0-models.jar: UPLOADED
  slf4j-api.jar: UPLOADED
  ejml-0.23.jar: UPLOADED
  stanford-corenlp-3.6.0.jar: UPLOADED

=== Files in @snowpark_demo_udf_dependency_jars ===

[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] ls @snowpark_demo_udf_dependency_jars
----------------------------------------------------------------------------------------------------------------------------------------
|"name"                                              |"size"     |"md5"                                |"last_modified"                |
----------------------------------------------------------------------------------------------------------------------------------------
|snowpark_demo_udf_dependency_jars/ejml-0.23.jar.gz  |189776     |a6f3fd6181d9b0c216d0f07f57c7ec87     |Sun, 13 Jun 2021 16:01:36 GMT  |
|snowpark_demo_udf_dependency_jars/slf4j-api.jar.gz  |22640      |1ad11d5010549f7e135933a1b4e20ef6     |Sun, 13 Jun 2021 16:01:36 GMT  |
|snowpark_demo_udf_dependency_jars/stanford-core...  |378223264  |6b9be4a95fe50e10ccbf4a811531561a-73  |Sun, 13 Jun 2021 15:59:54 GMT  |
|snowpark_demo_udf_dependency_jars/stanford-core...  |6796432    |2736d40c6e7f5de7c5c5f8089bd23f1d     |Sun, 13 Jun 2021 16:01:36 GMT  |
----------------------------------------------------------------------------------------------------------------------------------------

[success] Total time: 175 s (02:55), completed Jun 13, 2021, 9:01:40 AM
```

<!-- ------------------------ -->
##  Run the UDF demo
Duration: 10

Next, run the `UDFDemo.scala` example to create and call a UDF:

```console
sbt "runMain UDFDemo"
```

This example:

- Loads the data from the demo file into a DataFrame
- Creates a user-defined function (UDF) that analyzes a string and determines the sentiment of the
  words in the string
- Calls the function on each value in a column in the DataFrame
- Creates a new DataFrame that contains the column with the original data, and a new column with the
  return value of the UDF
- Creates a new DataFrame that just contains the rows where the function determined that the
  sentiment was happy

Let's take a closer look at the example and the output to see how the Snowpark library does this.

<!-- ------------------------ -->
##  Using shorthand notation for columns
Duration: 5

After creating the session, the example imports names from `implicits` in the `session`
***variable*** (which you defined when creating the session):

```scala
import session.implicits._
```

This statement allows you to use shorthand to refer to columns (*e.g.* `'columnName` and
`$"columnName"`) when passing arguments to DataFrame methods.

<!-- ------------------------ -->
##  Load data from a stage
Duration: 5

Next, the example creates a DataFrame that is set up to
[read data from a file in a stage](https://docs.snowflake.com/en/developer-guide/snowpark/working-with-dataframes.html#label-snowpark-dataframe-stages).
To do this, the example uses a
[DataFrameReader](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrameReader.html)
object.

Because the demo file is a CSV file, you must first define the schema for the file. In Snowpark,
you do this by creating a `Seq` of
[StructField](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/types/StructField.html)
objects that identify the names and types of each column of data. These objects are members of the
[com.snowflake.snowpark.types](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/types/index.html)
package.

```scala
import com.snowflake.snowpark.types.{StringType, StructField, StructType}
...
val schema = Seq(
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

```scala
val origData = session
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
(as the next line of code does) before you call the method to retrieve the data.

Next, the example returns a new DataFrame (`tweetData`) that just contains the column with the
tweets (the column named `text`) with the first 100 rows of data from the original DataFrame
`origData`.

The `drop` and `limit` methods in the example each returns a new DataFrame that has been
transformed by this method. Because each method returns a new DataFrame that has been transformed
by the method, you can chain the method calls, as shown below:

```scala
val tweetData = origData.drop('target, 'ids, 'date, 'flag, 'user).limit(100)
```

At this point, the DataFrame `tweetData` does not contain the actual data. In order to load the
data, you must call a method that performs an action (`show`, in this case).

```scala
Console.println("Text of the first 10 tweets")
tweetData.show()
```

In the output, the Snowpark library prints an `INFO` level message indicating that the query was
submitted for execution:

```console
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "MY_DB"."MY_SCHEMA".SN_TEMP_OBJECT_{n} TYPE  = csv COMPRESSION  =  'gzip'
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}]  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @demo/training.1600000.processed.noemoticon.csv.gz( FILE_FORMAT  => '"MY_DB"."MY_SCHEMA".SN_TEMP_OBJECT_{n}'))) LIMIT 100) LIMIT 10
```

At this point, the example prints the first 10 tweets:

```console
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
that are packaged in separate JAR files, so you will need to point the Snowpark library to those JAR
files. Do this by calling the `Session.addDependency` method.

The example adds these JAR files as dependencies:

```scala
session.addDependency(s"@${UDFDemoSetup.jarStageName}/stanford-corenlp-3.6.0.jar.gz")
session.addDependency(s"@${UDFDemoSetup.jarStageName}/stanford-corenlp-3.6.0-models.jar.gz")
session.addDependency(s"@${UDFDemoSetup.jarStageName}/slf4j-api.jar.gz")
session.addDependency(s"@${UDFDemoSetup.jarStageName}/ejml-0.23.jar.gz")
```

In this example, `UDFDemoSetup.jarStageName` refers to the name of the stage where you uploaded
JAR files earlier (when you ran the `UDFDemoSetup` example).

The example calls the `udf` function in the `com.snowflake.snowpark.functions` object to define
the UDF. The UDF passes in each value in a column of data to the `analyze` method.

```scala
import com.snowflake.snowpark.functions._
...
val sentimentFunc = udf(analyze(_))
```

At this point, the Snowpark library adds the JAR files for Snowpark and for your example as
dependencies (like the dependencies that it specified earlier):

```console
[run-main-0]  INFO (Logging.scala:22) - Automatically added /<path>/snowpark-0.6.0.jar to session dependencies.
[run-main-0]  INFO (Logging.scala:22) - Adding /<path>/snowparkdemo_2.12-0.1.jar to session dependencies
```

Next, the Snowpark library creates a temporary stage for the JAR files...

```console
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] create temporary stage if not exists "MY_DB"."MY_SCHEMA".snowSession_...
```

and uploads to the stage the JAR files for Snowpark and for your application code. Snowpark also
compiles your UDF and uploads the JAR file to the stage:

```console
[snowpark-2]  INFO (Logging.scala:22) - Uploading file file:/.../snowparkdemo_2.12-0.1.jar to stage @"MY_DB"."MY_SCHEMA".snowSession_...
[snowpark-1]  INFO (Logging.scala:22) - Uploading file file:/.../snowpark-0.6.0.jar to stage @"MY_DB"."MY_SCHEMA".snowSession_...

[snowpark-6]  INFO (Logging.scala:22) - Compiling UDF code
[snowpark-6]  INFO (Logging.scala:22) - Finished Compiling UDF code
[snowpark-6]  INFO (Logging.scala:22) - Uploading UDF jar to stage @"MY_DB"."MY_SCHEMA".snowSession_...
[snowpark-6]  INFO (Logging.scala:22) - Finished Uploading UDF jar to stage @"MY_DB"."MY_SCHEMA".snowSession_...

[snowpark-2]  INFO (Logging.scala:22) - Finished Uploading file file:/.../snowparkdemo_2.12-0.1.jar to stage @"MY_DB"."MY_SCHEMA".snowSession_...
[snowpark-1]  INFO (Logging.scala:22) - Finished Uploading file file:/.../snowpark-0.6.0.jar to stage @"MY_DB"."MY_SCHEMA".snowSession_...
```

Finally, the library defines the UDF in your database:

```console
[run-main-0]  INFO (Logging.scala:22) - Execute query [queryID: {queryID}] CREATE TEMPORARY FUNCTION "MY_DB"."MY_SCHEMA".tempUDF_...(arg1 STRING) RETURNS INT LANGUAGE JAVA IMPORTS = ('@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0-models.jar.gz','@snowpark_demo_udf_dependency_jars/slf4j-api.jar.gz','@"MY_DB"."MY_SCHEMA".snowSession_.../.../snowparkdemo_2.12-0.1.jar','@"MY_DB"."MY_SCHEMA".snowSession_.../.../snowpark-0.6.0.jar','@snowpark_demo_udf_dependency_jars/ejml-0.23.jar.gz','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0.jar.gz','@"MY_DB"."MY_SCHEMA".snowSession_/{prefix}tempUDF_..._.../udfJar_....jar') HANDLER='SnowUDF.compute'
```

Next, the example creates a new DataFrame (`analyzed`) that transforms the `tweetData` DataFrame by
adding a column named `sentiment`. The `sentiment` column contains the results from calling the UDF on the
corresponding value in the `text` column.

```scala
val analyzed = tweetData.withColumn("sentiment", sentimentFunc('text))
```

The example creates another DataFrame (`happyTweets`) that transforms the `analyzed` DataFrame to
include only the rows where the `sentiment` contains the value `3`.

```scala
val happyTweets = analyzed.filter('sentiment === 3)
```

Next, the example calls the `show` method to execute the SQL statements (including the UDF),
retrieve the results into the Dataframe, and print the first 10 rows.

```scala
happyTweets.show()
```

Finally, the example
[saves the data in the DataFrame to a table](https://docs.snowflake.com/en/developer-guide/snowpark/working-with-dataframes.html#label-snowpark-dataframe-save-table)
named `demo_happy_tweets`.
To do this, the example uses a
[DataFrameWriter](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrameWriter.html) object,
which is retrieved by calling the `DataFrame.write` method.

The example overwrites any existing data in the table by passing `SaveMode.Overwrite` to the `mode`
method of the `DataFrameWriter` object.

```scala
import com.snowflake.snowpark.SaveMode.Overwrite
...
happyTweets.write.mode(Overwrite).saveAsTable("demo_happy_tweets")
```

## Conclusion & Next Steps
Duration: 1

Congratulations! You used Snowpark to perform sentiment analysis on tweets. We provided a sample dataset of tweets for this guide. If you want to automatically ingest new tweets as they are written, follow the [Auto Ingest Twitter Data into Snowflake](/guide/auto_ingest_twitter_data/) guide.

### What We Covered
- **Data Loading** – Loading streaming Twitter data into Snowflake with Snowpipe in an event-driven, real-time fashion 
- **Semi-structured data** – Querying semi-structured data (JSON) without needing transformations
- **Secure Views** – Creating a Secure View to allow data analysts to query the data
- **Snowpipe** – Overview and configuration

### Related Resources
- [Snowpark Docs](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark.html)
- [Source code example on Github](https://guides.github.com/introduction/flow/)

id: getting_started_with_snowpark
summary: This guide provides the basic instructions for setting up a simple example using Snowpark.
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter

# Getting Started With Snowpark
<!-- ------------------------ -->
## Overview
Duration: 1

Using the [Snowpark API](https://docs.snowflake.com/en/developer-guide/snowpark/index.html),
you can query and manipulate data by writing code that uses
objects (like a [DataFrame](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrame.html)) rather than SQL statements. Snowpark is designed to make
building complex data pipelines easy, allowing you to interact with
Snowflake directly without moving data. When you use the
Snowpark API, the library uploads and runs your code in Snowflake so that you
don't need to move the data to a separate system for processing.

Currently, Snowpark is generally available on AWS and is a preview feature on Azure and GCP.

### What You’ll Build
- A Scala application that uses the Snowpark library to process data in a stage

### What You’ll Learn
- How to create a DataFrame that loads data from a stage
- How to create a user-defined function for your Scala code
- How to create a stored procedure from your Scala function

### Prerequisites
- Familiarity with Scala
- A [Snowflake](https://www.snowflake.com/) account hosted on Amazon Web Services
  (AWS) or Microsoft Azure. 
- [git](https://git-scm.com/downloads)
- [SBT](https://www.scala-sbt.org/)

You can also use a development tool or environment that supports SBT projects
for Scala 2.12 (specifically, version 2.12.9 or later 2.12.x versions). Snowpark
does not yet support versions of Scala after 2.12 (for example, Scala 2.13).

Snowpark supports code compiled to run on Java 11.

<!-- ------------------------ -->
## Download the repository
Duration: 5

You'll find the demo in a Snowflake GitHub repository. After installing git, you can clone the
repository using your terminal.

### Clone the repository

1. Open a terminal window and run the following commands to change to the directory where you want
   the repository cloned, and then clone the repository.

    ```console
    cd {directory_where_you_want_the_repository}
    git clone https://github.com/Snowflake-Labs/sfguide-snowpark-demo
    ```

1. Change to the directory of the repository that you cloned:

    ```console
    cd sfguide-snowpark-demo
    ```

The repository's demo directory includes the following files:

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

- `src/main/scala/UDFDemo.scala`: This is a simple code example that creates and calls a UDF.

<!-- ------------------------ -->
##  Configure the settings for connecting to Snowflake
Duration: 5

The demo directory contains a `snowflake_connection.properties` file that the
example code uses to
[create a session](https://docs.snowflake.com/en/developer-guide/snowpark/creating-session.html)
to connect to Snowflake. You'll need to edit these properties so the code
connects to your Snowflake account.

### Configure the connection settings

Edit this file and replace the `&lt;placeholder&gt;` values with the values
that you use to connect to Snowflake. For example:

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

- Use a [URL that includes your account identifier](https://docs.snowflake.com/en/user-guide/organizations-connect.html). For more information about the format of the URL,
  see [Account Identifiers](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html).
- The `ROLE` that you choose must have permissions to create stages and write
  tables in the specified database and schema.
- For the other properties, use any [connection parameter supported by the JDBC Driver](https://docs.snowflake.com/en/user-guide/jdbc-parameters.html).

<!-- ------------------------ -->
##  Connect to Snowflake
Duration: 5

In this step, you'll confirm that you can connect to Snowflake with the demo
code and your connection properties.

### Confirm a connection to Snowflake

Using the [SBT command-line tool](https://www.scala-sbt.org/1.x/docs/Running.html),
run the following command to build and run the `HelloWorld.scala` example to
verify that you can connect to Snowflake:

```console
sbt "runMain HelloWorld"
```

### Code walkthrough

When the HelloWorld application runs successfully, take a look at the following
walkthrough of its code and output.

- To establish a session, the application code creates a
  [Session](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/Session.html)
  object with the settings specified in `snowflake_connection.properties`.

    ```scala
    val session = Session.builder.configFile("snowflake_connection.properties").create
    ```

- Next, the application code [creates a DataFrame](https://docs.snowflake.com/en/developer-guide/snowpark/working-with-dataframes.html) to hold the results from executing the `SHOW TABLES` command:

    ```scala
    val df = session.sql("show tables")
    ```

    Note that this does not execute the SQL statement. The output does not include any `INFO` messages that indicate that the Snowpark library executed the SQL statement:

    ```console
    === Creating a DataFrame to execute a SQL statement ===

    [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
    ```

- A [DataFrame](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrame.html) in Snowpark is lazily evaluated, which means that statements are not executed until you call a
    method that performs an action. One such method is `show`, which prints out the first 10 rows in
    the DataFrame.

    ```scala
    df.show()
    ```

    As you can see in the output, `show` executes the SQL statement. The results are returned to the
    DataFrame, and the first 10 rows in the DataFrame are printed out:

    ```console
    === Execute the SQL statement and print the first 10 rows ===

    [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25558-0504-b2b8-0000-438301da121e] show tables
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    |"created_on"             |"name"             |"database_name"     |"schema_name"  |"kind"  |"comment"  |"cluster_by"  |"rows"  |"bytes"  |"owner"       |"retention_time"  |"automatic_clustering"  |"change_tracking"  |"is_external"  |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    |2022-02-15 11:19:20.294  |DEMO_HAPPY_TWEETS  |SNOWPARK_DEMO_DATA  |PUBLIC         |TABLE   |           |              |22      |2560     |ACCOUNTADMIN  |1                 |OFF                     |OFF                |N              |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    ```

Now that you have verified that you can connect to Snowflake, you need to get
the data and libraries to make the UDF work. 

<!-- ------------------------ -->
## Download the data file and libraries for the demo
Duration: 10

In this step, you'll download the sample data file and libraries you need to
run the user-defined function you're going to create. This demo uses the
[sentiment140](https://www.kaggle.com/kazanova/sentiment140) dataset and
libraries from the [CoreNLP project](https://stanfordnlp.github.io/CoreNLP/).

### Download dependency JARs and sample data file

1. Go to the [sentiment140](https://www.kaggle.com/kazanova/sentiment140) page
  and click **Download** to download the ZIP archive containing the dataset.

1. Unzip `training.1600000.processed.noemoticon.csv` from the `archive.zip` file that you downloaded.

1. [Download version 3.6.0 of the CoreNLP libraries](https://nlp.stanford.edu/software/stanford-corenlp-full-2015-12-09.zip).

1. Unzip the libraries from the `stanford-corenlp-full-2015-12-09.zip` file that you downloaded.

1. In your `sfguide-snowpark-demo` directory, create a temporary directory for
  the data and JAR files -- for example, `mkdir files_to_upload`.

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

In this section, you'll run the `UDFDemoSetup.scala` example to create
[internal stages](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-create-stage.html)
to hold the data file and libraries, then upload those files to the stages.

Because the user-defined function in the demo executes in Snowflake, you have to
upload the JAR files for these libraries to an internal stage to make them
available to Snowflake. You also need to upload the dataset to a stage, where
the demo will access the data.

### Upload data file and dependencies

Run the following command to run the code.

```console
sbt "runMain UDFDemoSetup"
```

### Code walkthrough

When the UDFDemoSetup application runs successfully, read the following to
understand what it does.

After creating a session, the application code calls `uploadDemoFiles` twice --
once to upload the sample data CSV file, then again to upload the JAR files that
will be dependencies of the UDF you'll create. The method uses the Snowpark
library to create a stage for the uploaded files.

- The `uploadDemoFiles` method takes the name of the stage to which the files
  should be uploaded, along with a file pattern that matches the names of files
  to upload.

  ```scala
  def uploadDemoFiles(stageName: String, filePattern: String): Unit = {
  ```

  What follows below describes what happens inside `uploadDemoFiles`.

- The code executes an SQL statement to create the stage. The `collect` method
  performs an action on a DataFrame, executing the SQL statement.

  ```scala
  session.sql(s"create or replace stage $stageName").collect()
  ```

  For this part of the example, you should see the following output when the
  method is creating the stage for the data files.

  ```console
  === Creating the stage @snowpark_demo_data ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter QUERY_TAG from server.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b1f7-0000-438301d9f31e] alter session set query_tag = 'com.snowflake.snowpark.DataFrame.collect
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:27)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b2bc-0000-438301da22ba] create or replace stage snowpark_demo_data
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b1f7-0000-438301d9f322] alter session unset query_tag
  ```

  Later, when this method is called again to create the stage for the JAR
  files, you should see the following output.

  ```console
  === Creating the stage @snowpark_demo_udf_dependency_jars ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b1f7-0000-438301d9f326] alter session set query_tag = 'com.snowflake.snowpark.DataFrame.collect
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:27)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2b8-0000-438301da122e] create or replace stage snowpark_demo_udf_dependency_jars
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b1f7-0000-438301d9f32a] alter session unset query_tag
  ```

- Next, the example uses the
  [FileOperation](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/FileOperation.html)
  object to upload files to the stage. You access an instance of this object through the
  `Session.file` method. To upload files (effectively running the `PUT` command), you call the `put` method of the
  FileOperation object. The `put` method returns an Array of
  [PutResult](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/PutResult.html)
  objects, each of which contains the results for a particular file.

  ```scala
  val res = session.file.put(s"$uploadDirUrl/$filePattern", stageName)
  res.foreach(r => Console.println(s"  ${r.sourceFileName}: ${r.status}"))
  ```

  You should see the following when the method is uploading the data file.

  ```console
  === Uploading files matching training.1600000.processed.noemoticon.csv to @snowpark_demo_data ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25576-0504-b2b8-0000-438301da1226] alter session set query_tag = 'com.snowflake.snowpark.FileOperation.put
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:31)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: ]  PUT file:///Users/straut/workfiles/git/sfguide-snowpark-demo/files_to_upload/training.1600000.processed.noemoticon.csv @snowpark_demo_data
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2bc-0000-438301da22be] alter session unset query_tag
    training.1600000.processed.noemoticon.csv: UPLOADED
  ```

  You should see the following when the method is uploading the JAR files.

  ```console
  === Uploading files matching *.jar to @snowpark_demo_udf_dependency_jars ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2b8-0000-438301da1232] alter session set query_tag = 'com.snowflake.snowpark.FileOperation.put
  UDFDemoSetup$.uploadDemoFiles(UDFDemoSetup.scala:31)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: ]  PUT file:///Users/straut/workfiles/git/sfguide-snowpark-demo/files_to_upload/*.jar @snowpark_demo_udf_dependency_jars
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a2557d-0504-b2b8-0000-438301da1236] alter session unset query_tag
    slf4j-api.jar: UPLOADED
    stanford-corenlp-3.6.0.jar: UPLOADED
    ejml-0.23.jar: UPLOADED
    stanford-corenlp-3.6.0-models.jar: UPLOADED
  ```

- The example then executes the `LS` command to list the files in the newly created stage and prints
  out the first 10 rows of output:

  ```scala
  session.sql(s"ls @$stageName").show()
  ```

  You should see the following when the method has uploaded the CSV file.

  ```console
  === Files in @snowpark_demo_data ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a25578-0504-b2bc-0000-438301da22c2] ls @snowpark_demo_data
  ---------------------------------------------------------------------------------------------------------------------------------------
  |"name"                                              |"size"    |"md5"                                |"last_modified"                |
  ---------------------------------------------------------------------------------------------------------------------------------------
  |snowpark_demo_data/training.1600000.processed.n...  |85088032  |da1aae6fe4879f916e740bd80af19685-17  |Tue, 15 Feb 2022 20:06:28 GMT  |
  ---------------------------------------------------------------------------------------------------------------------------------------
  ```

  You should see the following when the method has uploaded the JAR files.


  ```console
  === Files in @snowpark_demo_udf_dependency_jars ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a2557d-0504-b2bc-0000-438301da22ca] ls @snowpark_demo_udf_dependency_jars
  ----------------------------------------------------------------------------------------------------------------------------------------
  |"name"                                              |"size"     |"md5"                                |"last_modified"                |
  ----------------------------------------------------------------------------------------------------------------------------------------
  |snowpark_demo_udf_dependency_jars/ejml-0.23.jar.gz  |189776     |92c4f90ad7fcb8fecbe0be3951f9b8a3     |Tue, 15 Feb 2022 20:13:38 GMT  |
  |snowpark_demo_udf_dependency_jars/slf4j-api.jar.gz  |22640      |b013b6f5f80f95a285e3169c4f0b85ce     |Tue, 15 Feb 2022 20:13:37 GMT  |
  |snowpark_demo_udf_dependency_jars/stanford-core...  |378223264  |e4b4fdfbec76cc7f8fed01e08eec4dc0-73  |Tue, 15 Feb 2022 20:08:39 GMT  |
  |snowpark_demo_udf_dependency_jars/stanford-core...  |6796432    |2c4a458b9a205395409349b56dc64f8d     |Tue, 15 Feb 2022 20:13:38 GMT  |
  ----------------------------------------------------------------------------------------------------------------------------------------
  ```

Next, run the `UDFDemo.scala` example to create the user-defined function.

<!-- ------------------------ -->
##  Run the UDF demo
Duration: 10

In this step, you'll run the `UDFDemo.scala` demo application to create and call
a user-defined function (UDF). Read the topics that follow to take a closer
look at the example and the output to see how the Snowpark library does this.

### Create and call the UDF

Run the following command to run the code:

```console
sbt "runMain UDFDemo"
```

This example does the following:

- Loads the data from the demo file into a DataFrame.
- Creates a user-defined function (UDF) that analyzes a string and determines
  the sentiment of the words in the string.
- Calls the UDF on each value in a column in the DataFrame.
- Creates a new DataFrame that contains:
    - The column with the original data
    - A new column with the return value of the UDF
- Creates a new DataFrame that just contains the rows where the UDF determined
  that the sentiment was happy.

See the topics that follow for more on how this works.

<!-- ------------------------ -->
##  Load data from a stage and create a DataFrame
Duration: 5

The `collectTweetData` method creates a `DataFrame` to [read CSV data from a file in a stage](https://docs.snowflake.com/en/developer-guide/snowpark/working-with-dataframes.html#label-snowpark-dataframe-stages). It does this with a
[DataFrameReader](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrameReader.html) object.

### Code walkthrough

- The method receives a Session object to use for connecting to Snowflake.

  ```scala
  def collectTweetData(session: Session): DataFrame = {
  ```

- Importing names from `implicits` in the `session` ***variable*** allows you
  to use shorthand to refer to columns (for example, `'columnName` and
  `$"columnName"`) when passing arguments to DataFrame methods.

  ```scala
  import session.implicits._
  ```

- Because the demo file is a CSV file, you must first define the schema for the
  file. In Snowpark, you do this by creating a `Seq` of
  [StructField](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/types/StructField.html) objects that identify the names and types of each column of data. These
  objects are members of the
  [com.snowflake.snowpark.types](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/types/index.html) package.

  ```scala
  val schema = Seq(
    StructField("target", StringType),
    StructField("ids", StringType),
    StructField("date", StringType),
    StructField("flag", StringType),
    StructField("user", StringType),
    StructField("text", StringType),
  )
  ```

- Access a `DataFrameReader` object through the `Session.read` method. The
  `DataFrameReader` object provides methods that you use to specify the schema,
  options, and type of the file to load. These methods for setting the schema
  and options return a `DataFrameReader` object with the schema and options set.
  This allows you to chain these method calls, as shown below. The method for
  specifying the type of file (the `csv` method, in this case) returns a
  DataFrame that is set up to load the data from the specified file.

  ```scala
  val origData = session
    .read
    .schema(StructType(schema))
    .option("compression", "gzip")
    .csv(s"@$dataStageName/$dataFilePattern")
  ```

  In this example, `dataStageName` and `dataFilePattern` refer to the name
  of the stage and the files that you uploaded to that stage earlier when you
  ran `UDFDemoSetup`. You might remember that DataFrames are lazily evaluated,
  which means that they don't load data until you call a method to retrieve the
  data. You can call additional methods to transform the DataFrame (as the next
  line of code does) before you call the method to retrieve the data.

- Next, the example returns a new DataFrame (`tweetData`) that just contains the
  column with the tweets (the column named `text`). The Dataframe contains the
  first 100 rows of data from the original DataFrame `origData`. The `drop` and
  `limit` methods in the example each return a new DataFrame that has been
  transformed by these methods. Because each method returns a new DataFrame that
  has been transformed by the method, you can chain the method calls, as shown below:

  ```scala
  val tweetData = origData.drop('target, 'ids, 'date, 'flag, 'user).limit(100)
  ```

- At this point, the DataFrame `tweetData` does not contain the actual data. In
  order to load the data, you must call a method that performs an action (`show`,
  in this case).

  The example returns the DataFrame `tweetData`.

  ```scala
  tweetData.show()
  return tweetData
  ```

### Output

For `collectTweetData`, you'll see output such as the following.

```console
=== Setting up the DataFrame for the data in the stage ===

[sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter snowpark_lazy_analysis from server.

=== Retrieving the data and printing the text of the first 10 tweets
[sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da600a]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406 TYPE  = csv COMPRESSION  =  'gzip'
[sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da600e]  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @snowpark_demo_data/training.1600000.processed.noemoticon.csv( FILE_FORMAT  => '"SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406'))) LIMIT 100) LIMIT 10
------------------------------------------------------
|"TEXT"                                              |
------------------------------------------------------
|"...
```

<!-- ------------------------ -->
##  Define a UDF
Duration: 5

The `createUDF` method sets up dependencies for a UDF that analyzes tweets
for sentiment, then it creates the UDF in Snowflake.

### Code walkthrough

- The method takes a `Session` object that is used to specify the dependencies
  of the UDF.

  ```scala
  def createUDF(session: Session): UserDefinedFunction = {
  ```

- The UDF relies on libraries that are packaged in separate JAR files, so you
  will need to point the Snowpark library to those JAR files. Do this by calling
  the `Session.addDependency` method. The example adds these JAR files as
  dependencies:

  ```scala
  session.addDependency(s"@$jarStageName/stanford-corenlp-3.6.0.jar.gz")
  session.addDependency(s"@$jarStageName/stanford-corenlp-3.6.0-models.jar.gz")
  session.addDependency(s"@$jarStageName/slf4j-api.jar.gz")
  session.addDependency(s"@$jarStageName/ejml-0.23.jar.gz")
  ```

  In this example, `jarStageName` refers to the name of the stage where you
  uploaded JAR files when you ran `UDFDemoSetup`.

- The example calls the `udf` function in the `com.snowflake.snowpark.functions`
  object to define the UDF. The UDF passes in each value in a column of data to
  the `analyze` method.

  ```scala
  val sentimentFunc = udf(analyze(_))
  return sentimentFunc
  ```

### Output

- The Snowpark library adds the JAR files for Snowpark and for your example as
dependencies (like the dependencies that it specified earlier):

  ```console
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Automatically added /Users/straut/workfiles/git/sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/target/cfe3f19b/f74dd7dd/snowpark-0.6.0.jar to session dependencies.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Adding /Users/straut/workfiles/git/sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/job-1/target/6b26a7dc/681a6b89/snowparkdemo_2.12-0.1.jar to session dependencies
  ```

- Next, the Snowpark library creates a temporary stage for the JAR files...

  ```console
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b311-0000-438301da500e] create temporary stage if not exists "SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Actively querying parameter QUERY_TAG from server.
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da6012] alter session set query_tag = 'com.snowflake.snowpark.functions$.udf
  UDFDemo$.createUDF(UDFDemo.scala:108)'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da6016] ls @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da601a]  SELECT "name" FROM ( SELECT  *  FROM  TABLE ( RESULT_SCAN('01a255c9-0504-b313-0000-438301da6016')))
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b311-0000-438301da501a] alter session unset query_tag
  ```

  ... and uploads to the stage the JAR files for Snowpark and for your application code. Snowpark also
compiles your UDF and uploads the JAR file to the stage:

  ```console
  [snowpark-2]  INFO (Logging.scala:22) - Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/job-1/target/6b26a7dc/681a6b89/snowparkdemo_2.12-0.1.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [snowpark-9]  INFO (Logging.scala:22) - Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/target/cfe3f19b/f74dd7dd/snowpark-0.6.0.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [snowpark-11]  INFO (Logging.scala:22) - Compiling UDF code
  [snowpark-11]  INFO (Logging.scala:22) - Finished Compiling UDF code in 765 ms
  [snowpark-11]  INFO (Logging.scala:22) - Uploading UDF jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694
  [snowpark-11]  INFO (Logging.scala:22) - Finished Uploading UDF jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694 in 1413 ms
  [snowpark-2]  INFO (Logging.scala:22) - Finished Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/job-1/target/6b26a7dc/681a6b89/snowparkdemo_2.12-0.1.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694 in 2236 ms
  [snowpark-9]  INFO (Logging.scala:22) - Finished Uploading file file:/.../sfguide-snowpark-demo/target/bg-jobs/sbt_72da5f3e/target/cfe3f19b/f74dd7dd/snowpark-0.6.0.jar to stage @"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694 in 8482 ms
  ```

- Finally, the library defines the UDF in your database:

  ```console
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255c9-0504-b313-0000-438301da6022] CREATE TEMPORARY FUNCTION "SNOWPARK_DEMO_DATA"."PUBLIC".tempUDF_1136829422(arg1 STRING) RETURNS INT LANGUAGE JAVA IMPORTS = ('@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0-models.jar.gz','@snowpark_demo_udf_dependency_jars/slf4j-api.jar.gz','@"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694/f25d6649aab5cfb7a9429be961d73687/snowparkdemo_2.12-0.1.jar','@snowpark_demo_udf_dependency_jars/ejml-0.23.jar.gz','@"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694/85061e2a4c65715009267162d183eec1/snowpark-0.6.0.jar','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0.jar.gz','@"SNOWPARK_DEMO_DATA"."PUBLIC".snowSession_74229942898694/SNOWPARK_DEMO_DATAPUBLICtempUDF_1136829422_126127561/udfJar_591813027.jar') HANDLER='SnowUDF.compute'
  ```

<!-- ------------------------ -->
##  Use the UDF to process the tweets
Duration: 5

The `processHappyTweets` method uses the UDF to analyze tweet text to discover
which tweets are happy. 

### Code walkthrough 

- The method receives:
  - A `Session` for connecting to Snowflake.
  - The UDF you created.
  - A DataFrame representing the tweets.

  ```scala
  def processHappyTweets(session: Session, sentimentFunc: UserDefinedFunction, tweetData: DataFrame): Unit = {
  ```

- Import names from `implicits` in the `session` variable:

  ```scala
  import session.implicits._
  ```

- Next, the example creates a new DataFrame, `analyzed`, that transforms the
  `tweetData` DataFrame by adding a column named `sentiment`. The `sentiment`
  column contains the results from calling the UDF (`sentimentFunc`) with the
  corresponding value in the `text` column. 

  ```scala
  val analyzed = tweetData.withColumn("sentiment", sentimentFunc('text))
  ```

- The example creates another DataFrame, `happyTweets`, that transforms the
  `analyzed` DataFrame to include only the rows where the `sentiment`
  contains the value `3`.

  ```scala
  val happyTweets = analyzed.filter('sentiment === 3)
  ```

- Next, the example calls the `show` method to execute the SQL statements
  (including the UDF), retrieve the results into the Dataframe, and print the
  first 10 rows.

  ```scala
  happyTweets.show()
  ```

  When the `show` method executes, you'll see output such as the following.

  ```console
  === Retrieving the data and printing the first 10 tweets ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b311-0000-438301da5026]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406 TYPE  = csv COMPRESSION  =  'gzip'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b311-0000-438301da502a]  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT", "SNOWPARK_DEMO_DATA"."PUBLIC".tempUDF_1136829422("TEXT") AS "SENTIMENT" FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @snowpark_demo_data/training.1600000.processed.noemoticon.csv( FILE_FORMAT  => '"SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406'))) LIMIT 100)) WHERE ("SENTIMENT" = 3 :: int)) LIMIT 10
  --------------------------------------------------------------------
  |"TEXT"                                              |"SENTIMENT"  |
  --------------------------------------------------------------------
  |"...
  ```

- Finally, the example
  [saves the data in the DataFrame to a table](https://docs.snowflake.com/en/developer-guide/snowpark/working-with-dataframes.html#label-snowpark-dataframe-save-table) named `demo_happy_tweets`. To do
  this, the example uses a [DataFrameWriter](https://docs.snowflake.com/en/developer-guide/snowpark/reference/scala/com/snowflake/snowpark/DataFrameWriter.html) object, which is retrieved by calling the
  `DataFrame.write` method. The example overwrites any existing data in the
  table by passing `SaveMode.Overwrite` to the `mode` method of the
  `DataFrameWriter` object.

  ```scala
  happyTweets.write.mode(Overwrite).saveAsTable("demo_happy_tweets")
  ```
  
  When the `saveAsTable` method executes, you'll see output such as the following.

  ```console
  === Saving the data to the table demo_happy_tweets ===

  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b311-0000-438301da502e]  CREATE  TEMPORARY  FILE  FORMAT  If  NOT  EXISTS "SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406 TYPE  = csv COMPRESSION  =  'gzip'
  [sbt-bg-threads-1]  INFO (Logging.scala:22) - Execute query [queryID: 01a255ca-0504-b313-0000-438301da602a]  CREATE  OR  REPLACE  TABLE demo_happy_tweets AS  SELECT  *  FROM ( SELECT  *  FROM ( SELECT "TEXT", "SNOWPARK_DEMO_DATA"."PUBLIC".tempUDF_1136829422("TEXT") AS "SENTIMENT" FROM ( SELECT  *  FROM ( SELECT "TEXT" FROM ( SELECT $1::STRING AS "TARGET", $2::STRING AS "IDS", $3::STRING AS "DATE", $4::STRING AS "FLAG", $5::STRING AS "USER", $6::STRING AS "TEXT" FROM @snowpark_demo_data/training.1600000.processed.noemoticon.csv( FILE_FORMAT  => '"SNOWPARK_DEMO_DATA"."PUBLIC".SN_TEMP_OBJECT_1879375406'))) LIMIT 100)) WHERE ("SENTIMENT" = 3 :: int))
  ```

That's it for this part! So far, you've uploaded Scala code as a user-defined
function, then run the UDF to analyze tweet data for happy tweets.

In the last step, you'll take the code you've got already and turn it into
a stored procedure in Snowflake.

<!-- ------------------------ -->
##  Create a stored procedure from the Scala code
Duration: 5

In this step, you'll take the code you've just run and create a stored
procedure from it. To do that, you'll copy the Scala code into a Snowflake
worksheet, wrap the code in an SQL statement, and run it to create the
stored procedure.

The following steps use the [new web interface](https://docs.snowflake.com/en/user-guide/ui-web.html).

For related documentation, be sure to read
[Writing Stored Procedures in Snowpark (Scala)](https://docs.snowflake.com/en/sql-reference/stored-procedures-scala.html).

### Create and run the stored procedure

1. In the new web interface, create a new worksheet and call it `discoverHappyTweets`.

1. In the worksheet editor, ensure that the session context matches the settings
  you specified in the snowflake_connection.properties file you edited earlier.
  For example:
    - From the dropdown in the upper left, select the role you specified.
    - From the session context dropdown in the upper-right, select the role
      and warehouse values you specified.
    - From the database dropdown, select the database and schema you specified.

1. Into the `discoverHappyTweets` worksheet, paste the following:

    ```sql
    create or replace procedure discoverHappyTweets()
    returns string
    language scala
    runtime_version=2.12
    packages=('com.snowflake:snowpark:latest')
    imports=('@snowpark_demo_udf_dependency_jars/ejml-0.23.jar','@snowpark_demo_udf_dependency_jars/slf4j-api.jar','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0-models.jar','@snowpark_demo_udf_dependency_jars/stanford-corenlp-3.6.0.jar')
    handler = 'UDFDemo.discoverHappyTweets'
    target_path = '@snowpark_demo_udf_dependency_jars/discoverHappyTweets.jar'
    as
    $$

    /*Paste the UDFDemo object Scala code, including imports. You can optionally
    omit the main function.*/

    $$;
    ```
    
    This code creates a stored procedure called `discoverHappyTweets`. The
    documentation has more, but be sure to note the following:
      - The `packages` parameter specifies the Snowpark version to use.
      - The `imports` parameter specifies JAR files needed as your code's
        dependencies. This is the list of JAR files you uploaded to Snowflake
        earlier.
      - The `handler` parameter specifies the function Snowflake should call
        when executing the stored procedure.
      - The `target_path` parameter specifies the name and location of the JAR
        to create when you run this code. Snowflake compiles the code and packages
        the compiled classes.

1. Into the section between the `$$` delimiters, paste the Scala code from
    `UDFDemo`. Be sure to include the `import` statements. Don't include the
    `main` function; you don't need it. In particular, Snowflake will inject a
    Session object in place of the one you were creating there. Snowflake will
    instead call the method you specified with the `handler` parameter.

1. Run the code in the worksheet. Snowflake compiles the code in the body of
  `CREATE PROCEDURE` and packages it into a JAR file.

1. Create a new worksheet and call it `call discoverHappyTweets`.

1. Into the new worksheet, paste the following code:

    ```sql
    call discoverHappyTweets();
    select * from demo_happy_tweets;
    ```

1. In the worksheet, select both lines, then run the code in the worksheet.
  Beneath the worksheet, you should see messages as Snowflake calls the stored
  procedure. After the procedure call completes, these will be replaced with the
  results of the query -- the list of happy tweets. Calling the stored procedure
  just executes the method or function associated with that stored procedure.
  The execution happens with that JAR file in the classpath.

That's how easy it is to create a stored procedure. For bonus points, you could
call the new stored procedure with a nightly task.

```sql
create or replace task process_tweets_nightly
warehouse = 'small'
schedule = '1440 minute'
as
call discoverHappyTweets();
```

<!-- ------------------------ -->

## Conclusion & Next Steps
Duration: 1

Congratulations! You used Snowpark to perform sentiment analysis on tweets. 
You used a sample dataset of tweets for this guide. If you want to automatically
ingest new tweets as they are written, follow the
[Auto Ingest Twitter Data into Snowflake](/guide/auto_ingest_twitter_data/)
guide.

### What You Covered
- **Data Loading** - Loading Twitter data into Snowflake with Snowpark (Scala)
- **Data** - Creating Dataframes from the CSV file and remove unwanted columns
- **Sentiment Analysis** - Using Scala to perform sentiment analysis on a Dataframe of tweets
- **Snowpark UDF** - Using Scala to write the data frame into a Snowflake table
- **Snowpark stored procedure** - Using Snowflake to create a stored procedure in Scala

### Related Resources
- [Snowpark Docs](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark.html)
- [Source code example on Github](https://github.com/Snowflake-Labs/sfguide-snowpark-demo)

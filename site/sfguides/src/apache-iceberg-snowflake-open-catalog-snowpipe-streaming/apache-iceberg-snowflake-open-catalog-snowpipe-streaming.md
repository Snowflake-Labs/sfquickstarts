id: apache-iceberg-snowflake-open-catalog-snowpipe-streaming
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/lakehouse-analytics, snowflake-site:taxonomy/snowflake-feature/apache-iceberg
language: en
summary: Stream real-time data to Apache Iceberg™ tables with Snowpipe Streaming and Snowflake Open Catalog for governed lakehouse ingestion.
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
authors: Dash Desai


# Apache Iceberg and Snowflake Open Catalog: Unlock Data Lake Interoperability with Apache Polaris
<!-- ------------------------ -->

## Overview


Snowflake’s native integration with Apache Iceberg empowers organizations to build a highly interoperable and open lakehouse architecture. With streamlined support for batch and streaming data ingestion, transformation pipelines, and analytics, Snowflake simplifies complex workflows on Iceberg tables. Additionally, Snowflake Open Catalog, a managed service for Apache Polaris, offers robust role-based access controls, ensuring seamless data governance and secure collaboration across multiple engines.

> NOTE: Apache Polaris™ is currently undergoing Incubation at the Apache Software Foundation.

### What You Will Learn

You will learn how to stream data directly into Apache Iceberg tables for real-time updates and efficient data management. You'll explore how to build incremental data transformation pipelines that process only new or updated data, improving performance and reducing latency. Finally, you'll discover how interoperable role-based access controls enable secure collaboration and robust data governance across platforms, empowering you to create an open and flexible data architecture.

### What You Will Build

* A pipeline that streams data directly into Apache Iceberg tables
* Incremental data transformation pipelines
* Interoperable role-based access controls 
* Snowflake Notebooks to query data using Spark

### Prerequisites

* Ability to create or access an existing S3 bucket
* Ability to create AWS IAM roles, policies, and trust relationships
* Ability to create or access an existing Snowflake Open Catalog account
* Ability to create Iceberg and Dynamic tables in Snowflake
* Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) in the **same AWS region as your S3 bucket**

<!-- ------------------------ -->
## Setup


**Step 1.** Create Snowflake Open Catalog Account, Connections, Roles

- Create a [Snowflake Open Catalog account](https://other-docs.snowflake.com/en/opencatalog/create-open-catalog-account#)
- Create a [catalog](https://other-docs.snowflake.com/en/opencatalog/create-catalog)
    - **NOTE**: Be sure to set the **External** toggle to On as described [here](https://other-docs.snowflake.com/en/opencatalog/create-catalog#step-3-create-a-catalog-in-open-catalog)
- From the Connections page
    - In the Principals tab, create three [service connections](https://other-docs.snowflake.com/en/opencatalog/configure-service-connection) named `spark_analyst`, `spark_engineer`, and `snowflake_engineer`
    - In the Roles tab, create three [principal roles](https://other-docs.snowflake.com/en/opencatalog/create-principal-role) named `spark_analyst_role` and `spark_engineer_role`, and `snowflake_engineer_role`
        - **NOTE**: Save the one-time information of CLIENT_ID and CLIENT_SECRET of `snowflake_engineer_role` for creating catalog integration.
- From the snowflake_catalog page, in the roles tab
    - Create three [catalog roles](https://other-docs.snowflake.com/en/opencatalog/create-catalog-role) named `table_all`,`table_reader_refined`, and `snowflake_catalog_role` with the following privileges
        - **table_all**:
            - Catalog:
                - NAMESPACE_LIST
                - TABLE_LIST
                - TABLE_READ_DATA
                - CATALOG_READ_PROPERTIES
        - **table_reader_refined**:
            - Catalog:
                - NAMESPACE_LIST
            - Namespace BUILD_DB.REFINED
                - NAMESPACE_LIST
                - TABLE_LIST
                - TABLE_READ_DATA
        - **snowflake_catalog_role**:
            - Catalog:
                - CATALOG_MANAGE_CONTENT

    - Assign catalog roles to principal roles:
        - **table_all**: spark_engineer_role
        - **table_reader_refined**: spark_analyst_role
        - **snowflake_catalog_role**: snowflake_engineer_role

- Follow [instructions](https://other-docs.snowflake.com/en/opencatalog/enable-credential-vending-external-catalog#using-open-catalog) to enable credential vending for external catalog

**Step 2.** Create External Volume

Create and configure an external volume for Snowflake Dynamic Iceberg tables to write data and metadata.

  - [Create an IAM policy that grants access to your S3 location](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3#step-1-create-an-iam-policy-that-grants-access-to-your-s3-location)
  - [Create an IAM role](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3#step-2-create-an-iam-role)
  - [Create external volume and Snowflake Open Catalog (Polaris) integrations](https://github.com/Snowflake-Labs/snowflake-build-2024-apache-iceberg-snowflake-open-catalog-demo/blob/main/external_vol_cat_integration_setup.sql)

You will need to replace the following values with your own:

- External Volume
    - STORAGE_BASE_URL
    - STORAGE_AWS_ROLE_ARN 
- Catalog Integration
    - CATALOG_URI
    - OAUTH_CLIENT_ID
    - OAUTH_CLIENT_SECRET


> NOTE: The OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET for creating the catalog integration are of the `snowflake_engineer_role` principal role.

**Step 3.** Create Tables

Execute the statements in [iceberg_dt_setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/iceberg_dt_setup.sql) to create tables and schemas in a dedicated database.

If you choose to use different object names than the provided SQL, you may need to replace the following values with your own:

- EXTERNAL_VOLUME 
- CATALOG 
- BASE_LOCATION 
- CATALOG_SYNC 

**Step 4.** Load Data

Use the following .csv files and load data into respective tables using [Snowsight](https://docs.snowflake.com/en/user-guide/data-load-web-ui#load-a-file-into-an-existing-table).

- [VEHICLE_INFO](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/polaris-iceberg-spark/vehicle_info.csv)

- **(Optional)** [STREAMING_VEHICLE_EVENTS](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/polaris-iceberg-spark/STREAMING_VEHICLE_EVENTS.csv)

- **(Optional)** [VEHICLE_EVENTS_SCD2](sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/polaris-iceberg-spark/VEHICLE_EVENTS_SCD2.csv)

- **(Optional)** [VEHICLE_MODELS_EVENTS](sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/polaris-iceberg-spark/VEHICLE_MODELS_EVENTS.csv)

- **(Optional)** [VEHICLE_MODELS_EVENTS_LAST_MAINTENANCE](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/polaris-iceberg-spark/VEHICLE_MODELS_EVENTS_LAST_MAINTENANCE.csv)


> NOTE: Data in STREAMING_VEHICLE_EVENTS will (also) be inserted via Snowpipe Streaming via Java SDK (see next section) and as that happens the data will (also) get populated in VEHICLE_EVENTS_SCD2, VEHICLE_MODELS_EVENTS, and VEHICLE_MODELS_EVENTS_LAST_MAINTENANCE Dynamic Iceberg tables.

<!-- ------------------------ -->
## Snowpipe Streaming


Follow these instructions to setup Snowpipe Streaming.

**Step 1.** Clone [GitHub repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog).

**Step 2.** Open *snowpipe-streaming-java* folder in your favorite IDE and also open a terminal window and change to *snowpipe-streaming-java* folder

**Step 3.** Configure [key-pair authentication](https://docs.snowflake.com/user-guide/key-pair-auth#configuring-key-pair-authentication) and assign the public key to your user in Snowflake and store/save/copy the private key file (.p8) in the current *snowpipe-streaming-java* folder

**Step 4.** Update [snowflake.properties](https://github.com/Snowflake-Labs/snowflake-build-2024-iceberg-catalog-demo/blob/main/snowpipe-streaming-java/snowflake.properties) as it pertains to your Snowflake account
    - HOST
    - USER
    - ROLE
    - ACCOUNT


> NOTE: You may not alter the following attributes:
>    - ENABLE_ICEBERG_STREAMING: This enables writing directly into STREAMING_VEHICLE_EVENTS iceberg dynamice table  
>    - DATA_FILE: The data in [DATA.csv](https://github.com/Snowflake-Labs/snowflake-build-2024-iceberg-catalog-demo/blob/main/snowpipe-streaming-java/DATA.csv) is used to simulate streaming records. So the records from this file are read and written to the channel and eventually into the STREAMING_VEHICLE_EVENTS table.

### Streaming Data

**Step 1.** In your cloned repo, change to *snowpipe-streaming-java* folder

**Step 2.** Run `./Build.sh` to build the JAR file that will include all the dependencies

**Step 3.** Run `./StreamRecords.sh` to start streaming records

**Step 4.** If all goes well, you should see output similar to the following:

    ```bash
    (base) ddesai@TX5Y99H44W snowpipe-streaming-java % ./StreamRecords.sh 
    [main] INFO net.snowflake.ingest.utils.Utils - [SF_INGEST] Adding security provider net.snowflake.ingest.internal.org.bouncycastle.jce.provider.BouncyCastleProvider
    [main] INFO net.snowflake.ingest.connection.RequestBuilder - Default user agent SnowpipeJavaSDK/2.3.0 (Mac OS X 14.7.1 aarch64) JAVA/21.0.4
    [main] INFO net.snowflake.ingest.connection.SecurityManager - Successfully created new JWT
    [main] INFO net.snowflake.ingest.connection.RequestBuilder - Creating a RequestBuilder with arguments : Account : SFDEVREL_ENTERPRISE, User : DASHDEMO, Scheme : https, Host : sfdevrel_enterprise.snowflakecomputing.com, Port : 443, userAgentSuffix: null
    [main] INFO net.snowflake.ingest.streaming.internal.SnowflakeStreamingIngestClientInternal - [SF_INGEST] Using KEYPAIR_JWT for authorization
    [main] INFO net.snowflake.ingest.streaming.internal.FlushService - [SF_INGEST] Create 36 threads for build/upload blobs for client=CLIENT, total available processors=12
    [main] INFO net.snowflake.ingest.streaming.internal.SnowflakeStreamingIngestClientInternal - [SF_INGEST] Client created, name=CLIENT, account=sfdevrel_enterprise. isTestMode=false, parameters=ParameterProvider{parameterMap={max_client_lag=2000, enable_iceberg_streaming=true}}
    [main] INFO net.snowflake.ingest.streaming.internal.SnowflakeStreamingIngestClientInternal - [SF_INGEST] Open channel request succeeded, channel=channel_1_SLOOOW, table=dash_db.raw.streaming_vehicle_events, clientSequencer=46, rowSequencer=0, client=CLIENT
    [main] INFO net.snowflake.ingest.streaming.internal.SnowflakeStreamingIngestChannelInternal - [SF_INGEST] Channel=CHANNEL_1_SLOOOW created for table=STREAMING_VEHICLE_EVENTS
    1 2 3 4 5 6 7 8 9 10 11 12 [ingest-flush-thread] INFO net.snowflake.ingest.streaming.internal.FlushService - [SF_INGEST] buildAndUpload task added for client=CLIENT, blob=net.snowflake.ingest.streaming.internal.BlobPath@65e73c28, buildUploadWorkers stats=java.util.concurrent.ThreadPoolExecutor@783ec989[Running, pool size = 1, active threads = 1, queued tasks = 0, completed tasks = 0]
    13 [ingest-build-upload-thread-0] INFO net.snowflake.ingest.internal.apache.hadoop.io.compress.CodecPool - Got brand-new compressor [.zstd]
    14 15 16 17 [ingest-build-upload-thread-0] INFO net.snowflake.ingest.streaming.internal.BlobBuilder - [SF_INGEST] Finish building chunk in blob=raw/streaming_vehicle_events/data/streaming_ingest/GAoOLpp0sAA/6c/snow_FC81kWLxOPI_GAoOLpp0sAA_1009_1_0.parquet, table=DASH_DB.RAW.STREAMING_VEHICLE_EVENTS, rowCount=12, startOffset=0, estimatedUncompressedSize=1173.5, chunkLength=4608, compressedSize=4608, encrypt=false, bdecVersion=THREE
    [ingest-build-upload-thread-0] INFO net.snowflake.ingest.streaming.internal.FlushService - [SF_INGEST] Start uploading blob=raw/streaming_vehicle_events/data/streaming_ingest/GAoOLpp0sAA/6c/snow_FC81kWLxOPI_GAoOLpp0sAA_1009_1_0.parquet, size=4608
    18 Nov 21, 2024 10:10:18 AM net.snowflake.client.jdbc.cloud.storage.SnowflakeS3Client upload
    INFO: Starting upload from stream (byte stream) to S3 location: build-2024-keynote-demos/raw/streaming_vehicle_events/data/streaming_ingest/GAoOLpp0sAA/6c/snow_FC81kWLxOPI_GAoOLpp0sAA_1009_1_0.parquet
    19 20 21 22 23 24 Nov 21, 2024 10:10:18 AM net.snowflake.client.jdbc.cloud.storage.SnowflakeS3Client upload
    ```

**NOTE:** You can also run this SQL to make sure the number of records count is going up `SELECT count(*) from DASH_DB.RAW.STREAMING_VEHICLE_EVENTS;`

### Dynamic Iceberg Tables

At this point you should also check refresh history of *VEHICLE_EVENTS_SCD2*, *VEHICLE_MODELS_EVENTS*, and *VEHICLE_MODELS_EVENTS_LAST_MAINTENANCE* Dynamic Iceberg tables to make sure the data is being inserted.

<!-- ------------------------ -->
## Spark in Snowflake Notebooks


Assuming everything has gone smoothly so far, follow instructions below to query data in Spark using Snowflake Notebooks.

**Step 1.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/setup.sql) to execute all statements in order from top to bottom.

**Step 2.** In Snowsight, switch your user role to `DASH_CONTAINER_RUNTIME_ROLE`.

### Query Data as an Engineer 

**Step 1.** Click on [spark_engineer_notebook_app.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/spark_engineer_notebook_app.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)

**Step 2.** In Snowsight:

* On the left hand navigation menu, click on **Projects » Notebooks**
* On the top right, click on **Notebook** down arrow and select **Import .ipynb file** from the dropdown menu
* Select **spark_engineer_notebook_app.ipynb** file you downloaded in the step above
* In the Create Notebook popup
    * For Notebook location, select `DASH_DB` and `DASH_SCHEMA`
    * For SQL warehouse, select `DASH_WH_S`
    * For Python environment, select `Run on container`
    * For Runtime, select `Snowflake ML Runtime CPU 1.0`
    * For Compute pool, select `CPU_X64_XS`
    * Click on **Create** button

**Step 3.** Open Notebook

* Click in the three dots at the very top-right corner and select `Notebook settings` >> `External access`
* Turn on **ALLOW_ALL_ACCESS_INTEGRATION**
* Click on **Save** button
* Click on **Start** button on top right


> NOTE: At this point, the container service will take about 5-7 minutes to start. You will not be able to proceed unless the status changes from **Starting** to **Active**.

**Step 4.** Run Notebook

* **Cell 1**: Run this cell to install libraries including Spark and PySpark

* **Cell 2**: Update POLARIS_ENGINEER_CLIENT_ID, POLARIS_ENGINEER_CLIENT_SECRET, and `spark.sql.catalog.polaris.uri` with your values and run this cell to create Spark context 

* **Cell 3**: Run this cell to see that `spark_engineer_role` role has access to `DASH_DB.RAW`

    ```bash
    spark.sql("SHOW TABLES IN DASH_DB.RAW").show(truncate=False)

    +-----------+------------------------+-----------+
    |namespace  |tableName               |isTemporary|
    +-----------+------------------------+-----------+
    |DASH_DB.RAW|MAINTENANCE_RECORDS     |false      |
    |DASH_DB.RAW|STREAMING_VEHICLE_EVENTS|false      |
    |DASH_DB.RAW|VEHICLE_INFO            |false      |
    +-----------+------------------------+-----------+
    ```

* **Cell 4**: Run this cell to see that `spark_engineer_role` role has access to `DASH_DB.RAW.STREAMING_VEHICLE_EVENTS`

    ```bash
    spark.sql("SELECT * FROM DASH_DB.RAW.STREAMING_VEHICLE_EVENTS").show(truncate=False)

    +----------+--------------------------+--------+---------+-----+---------------------+------------------------+------------------------+---------------------+------------------+--------------------+-----------+-------------+-----------+------------+--------------------+
    |VEHICLE_ID|EVENT_CREATED_AT          |LATITUDE|LONGITUDE|SPEED|ENGINE_STATUS        |FUEL_CONSUMPTION_CURRENT|FUEL_CONSUMPTION_AVERAGE|FUEL_CONSUMPTION_UNIT|HARD_ACCELERATIONS|SMOOTH_ACCELERATIONS|HARD_BRAKES|SMOOTH_BRAKES|SHARP_TURNS|GENTLE_TURNS|MAINTENANCE_REQUIRED|
    +----------+--------------------------+--------+---------+-----+---------------------+------------------------+------------------------+---------------------+------------------+--------------------+-----------+-------------+-----------+------------+--------------------+
    |V105878   |2024-10-07 18:57:04.290931|34.0638 |-98.0939 |59.5 |check_engine_light_on|9.5                     |6.5                     |L/100km              |1                 |10                  |1          |6            |2          |7           |false               |
    |V386893   |2024-10-08 15:40:56.290931|40.0696 |-118.2529|71.4 |normal               |8.6                     |7.4                     |L/100km              |1                 |11                  |1          |8            |3          |8           |true                |
    |V231994   |2024-10-07 22:21:22.290931|39.3836 |-105.377 |70.8 |check_engine_light_on|5.9                     |5.4                     |L/100km              |4                 |19                  |1          |8            |0          |5           |true                |
    +----------+--------------------------+--------+---------+-----+---------------------+------------------------+------------------------+---------------------+------------------+--------------------+-----------+-------------+-----------+------------+--------------------+
    ```

---

### Query Data as an Analyst 

**Step 1.** Click on [spark_analyst_notebook_app.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog/blob/main/spark_analyst_notebook_app.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)

**Step 2.** In Snowsight:

* On the left hand navigation menu, click on **Projects » Notebooks**
* On the top right, click on **Notebook** down arrow and select **Import .ipynb file** from the dropdown menu
* Select **spark_analyst_notebook_app.ipynb** file you downloaded in the step above
* In the Create Notebook popup
    * For Notebook location, select `DASH_DB` and `DASH_SCHEMA`
    * For SQL warehouse, select `DASH_WH_S`
    * For Python environment, select `Run on container`
    * For Runtime, select `Snowflake ML Runtime CPU 1.0`
    * For Compute pool, select `CPU_X64_XS`
    * Click on **Create** button

**Step 3.** Open Notebook

* Click in the three dots at the very top-right corner and select `Notebook settings` >> `External access`
* Turn on **ALLOW_ALL_ACCESS_INTEGRATION**
* Click on **Save** button
* Click on **Start** button on top right


> NOTE: At this point, the container service will take about 5-7 minutes to start. You will not be able to proceed unless the status changes from **Starting** to **Active**.

**Step 4.** Run Notebook

* **Cell 1**: Run this cell to install libraries including Spark and PySpark

* **Cell 2**: Update POLARIS_ANALYST_CLIENT_ID, POLARIS_ANALYST_CLIENT_SECRET and `spark.sql.catalog.polaris.uri` with your values and run this cell to create Spark context. If everything has been setup correctly so far, you will see that `spark_analyst_role` role DOES NOT have access to `DASH_DB.RAW.STREAMING_VEHICLE_EVENTS` as per access control setup in **Create Snowflake Open Catalog Account, Connections, Roles** section under **Setup** step.

    ```bash
    spark.sql("select * from DASH_DB.RAW.STREAMING_VEHICLE_EVENTS").show(10, truncate = False)

    An error occurred while calling o51.sql.
    : org.apache.iceberg.exceptions.ForbiddenException: Forbidden: Principal 'spark_analyst_principal' with activated PrincipalRoles '[spark_analyst_role]' and activated grants via '[table_reader_refined, spark_analyst_role]' is not authorized for op LOAD_TABLE_WITH_READ_DELEGATION
	at org.apache.iceberg.rest.ErrorHandlers$DefaultErrorHandler.accept(ErrorHandlers.java:157)
	at org.apache.iceberg.rest.ErrorHandlers$TableErrorHandler.accept(ErrorHandlers.java:109)
	at org.apache.iceberg.rest.ErrorHandlers$TableErrorHandler.accept(ErrorHandlers.java:93)
	at org.apache.iceberg.rest.HTTPClient.throwFailure(HTTPClient.java:183)
	at org.apache.iceberg.rest.HTTPClient.execute(HTTPClient.java:292)
	at org.apache.iceberg.rest.HTTPClient.execute(HTTPClient.java:226)
	at org.apache.iceberg.rest.HTTPClient.get(HTTPClient.java:327)
	at org.apache.iceberg.rest.RESTClient.get(RESTClient.java:96)
	at org.apache.iceberg.rest.RESTSessionCatalog.loadInternal(RESTSessionCatalog.java:300)
	at org.apache.iceberg.rest.RESTSessionCatalog.loadTable(RESTSessionCatalog.java:316)
	at org.apache.iceberg.catalog.BaseSessionCatalog$AsCatalog.loadTable(BaseSessionCatalog.java:99)
	at org.apache.iceberg.rest.RESTCatalog.loadTable(RESTCatalog.java:96)
    ```

* **Cell 3**: Run this cell to see that `spark_analyst_role` role does have access to `DASH_DB.REFINED.VEHICLE_EVENTS_SCD2`

    ```bash
    spark.sql("SELECT * FROM DASH_DB.REFINED.VEHICLE_EVENTS_SCD2").show(10, truncate=False)

    +----------+----------------+--------------+---------------------+
    |VEHICLE_ID|EVENT_START_DATE|EVENT_END_DATE|ENGINE_STATUS        |
    +----------+----------------+--------------+---------------------+
    |V214746   |2024-10-06      |2024-10-06    |check_engine_light_on|
    |V214746   |2024-10-06      |2024-10-06    |check_engine_light_on|
    |V214746   |2024-10-06      |2024-10-06    |check_engine_light_on|
    |V214746   |2024-10-06      |2024-10-06    |check_engine_light_on|
    |V214773   |2024-10-06      |NULL          |normal               |
    |V214773   |2024-10-06      |2024-10-06    |normal               |
    |V214773   |2024-10-06      |2024-10-06    |normal               |
    |V214773   |2024-10-06      |2024-10-06    |normal               |
    |V214773   |2024-10-06      |2024-10-06    |normal               |
    |V214773   |2024-10-06      |2024-10-06    |normal               |
    +----------+----------------+--------------+---------------------+
    ```

<!-- ------------------------ -->
## Conclusion And Resources


Congratulations! You've successfully completed this guide to discover the key benefits and use cases for modern data architectures using Apache Iceberg and Snowflake Open Catalog.

### What You Learned

You learned how to stream data directly into Apache Iceberg tables for real-time updates and efficient data management. You also explored how to build incremental data transformation pipelines that process only new or updated data, improving performance and reducing latency. Finally, you discovered how interoperable role-based access controls enable secure collaboration and robust data governance across platforms, empowering you to create an open and flexible data architecture.

### Related Resources

- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-snowpipe-streaming-apache-iceberg-snowflake-open-catalog)
- [Snowflake Notebooks on Container Runtime](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs)
- [Demo on YouTube](https://youtu.be/bq0YxaBsYnA?si=pKpeH2JcwcTF1IHa&t=1447)

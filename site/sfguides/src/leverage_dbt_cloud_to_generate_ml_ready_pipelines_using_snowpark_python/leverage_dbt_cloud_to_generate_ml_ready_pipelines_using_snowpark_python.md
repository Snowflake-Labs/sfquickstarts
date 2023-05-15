author: hope-wat
id: leverage_dbt_cloud_to_generate_ml_ready_pipelines_using_snowpark_python
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 


# Leverage dbt Cloud to Generate ML ready pipelines using snowpark python
<!-- ------------------------ -->
## Overview 
Duration: 3

http://localhost:8000/guide/leverage_dbt_cloud_to_generate_ml_ready_pipelines_using_snowpark_python

The focus of this workshop will be to demonstrate how we can use both *SQL and python together* in the same workflow to run *both analytics and machine learning models* on dbt Cloud.

All code in today’s workshop can be found on [GitHub](https://github.com/dbt-labs/python-snowpark-formula1/tree/python-formula1).

### What you'll need to setup for the lab

- A [Snowflake account](https://trial.snowflake.com/) with ACCOUNTADMIN access
- A [GitHub](https://github.com/) Account 

### What you'll learn

- How to use dbt with Snowflake to build scalable transformations using SQL and Python
    - How to use dbt SQL to prepare your data from sources to encoding 
    - How to train a model in dbt python and use it for future prediction 
    - How to deploy your full project 

### What you need to know

- Basic to intermediate SQL and python.
- Basic understanding of dbt fundamentals. We recommend the [dbt Fundamentals course](https://courses.getdbt.com/collections) if you're interested.
- High level machine learning process (encoding, training, testing)
- Simple ML algorithms &mdash; we will use logistic regression to keep the focus on the *workflow*, not algorithms!

- *Bonus: if you have completed [this dbt workshop](https://quickstarts.snowflake.com/guide/accelerating_data_teams_with_snowflake_and_dbt_cloud_hands_on_lab/index.html?index=..%2F..index#0) to have hands on keyboard practice with concepts like the source, ref, tests, and docs in dbt. By having completed that workshop, you will gain the most of this dbt python + snowpark workshop.

### What you'll build

TODO I think this needs to be updated to reflect the importance on the deployment part. 
- A set of data analytics and prediction pipelines using Formula 1 data leveraging dbt and Snowflake, making use of best practices like data quality tests and code promotion between environments. 
- We will create insights for:
    1. Finding the lap time average and rolling average through the years
    2. Predicting the position of each driver based on a decade of data

As inputs, we are going to leverage Formula 1 datasets hosted on a dbt Labs public S3 bucket. We will create a Snowflake Stage for our CSV files then use Snowflake’s `COPY INTO` function to copy the data in from our CSV files into tables. The Formula 1 is available on [Kaggle](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020). The data is originally compiled from the [Ergast Developer API](http://ergast.com/mrd/). We will not be building the full pipeline as part of this workshop. Instead we will leverage an exisitng repo, fork it, and focus on our machine learning pipeline.

<!-- ------------------------ -->
## Configure Snowflake
Duration: 5
In this section we’re going to sign up for a Snowflake trial account and enable Anaconda-provided Python packages.

1. [Sign up for a Snowflake Trial Account using this form](https://signup.snowflake.com/). Ensure that your account is set up using **AWS** in the **US East (N. Virginia)**. We will be copying the data from a public AWS S3 bucket hosted by dbt Labs in the us-east-1 region. By ensuring our Snowflake environment setup matches our bucket region, we avoid any multi-region data copy and retrieval latency issues.


2. After creating your account and verifying it from your sign-up email, Snowflake will direct you back to the UI called Snowsight.

3. When Snowsight first opens, your window should look like the following, with you logged in as the ACCOUNTADMIN with demo worksheets open:


4. Navigate to **Admin > Billing & Terms**. Click **Enable > Acknowledge & Continue** to enable Anaconda Python Packages to run in Snowflake.
    

5. Finally, navigate back to home to create a new SQL Worksheet by selecting **+** then **SQL Worksheet** in the upper right corner.

<!-- ------------------------ -->
## Load data into Snowflake
Duration: 7
We need to obtain our data source by copying our Formula 1 data into Snowflake tables from a public S3 bucket that dbt Labs hosts. 

1. Your new Snowflake account has a preconfigured warehouse named `COMPUTE_WH`. If for some reason you don’t have this warehouse, we can create a warehouse using the following script:

    ```sql
    create or replace warehouse COMPUTE_WH with warehouse_size=XSMALL
    ```
2. Rename the SQL worksheet by clicking the worksheet name (this is automatically set to the current timestamp) using the option **…** and **Rename**. Rename the file  to `data setup script` since we will be placing code in this worksheet to ingest the Formula 1 data. Make sure your role is set as the **ACCOUNTADMIN** and select the **COMPUTE_WH** warehouse.

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/3-connect-to-data-source/1-rename-worksheet-and-select-warehouse.png" title="Rename worksheet and select warehouse"/>

3. Copy the following code into the main body of the Snowflake SQL worksheet. You can also find this setup script under the `setup` folder in the [Git repository](https://github.com/dbt-labs/python-snowpark-formula1/blob/main/setup/setup_script_s3_to_snowflake.sql). The script is long since it's bringing in all of the data we'll need today! Generally during this lab we'll be explaining and breaking down the queries. We won't going line by line, but we will point out important information related to our learning objectives!

4. Ensure all the commands are selected before running the query &mdash; an easy way to do this is to use Ctrl-A to highlight all of the code in the worksheet. Select **run** (blue triangle icon). Notice how the dot next to your **COMPUTE_WH** turns from gray to green as you run the query. The **status** table is the final table of all 14 tables loaded in. 

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/3-connect-to-data-source/2-load-data-from-s3.png" title="Load data from S3 bucket"/>

5. Let’s unpack that pretty long query we ran into component parts. We ran this query to load in our 14 Formula 1 tables from a public S3 bucket. To do this, we:
    - Created a new database called `formula1` and a schema called `raw` to place our raw (untransformed) data into. 
    - Created a stage to locate our data we are going to load in. Snowflake Stages are locations where data files are stored. Stages are used to both load and unload data to and from Snowflake locations. Here we are using an external stage, by referencing an S3 bucket. 
    - Created our tables for our data to be copied into. These are empty tables with the column name and data type. Think of this as creating an empty container that the data will then fill into. 
    - Used the `copy into` statement for each of our tables. We reference our staged location we created and upon loading errors continue to load in the rest of the data. You should not have data loading errors but if you do, those rows will be skipped and Snowflake will tell you which rows caused errors

6. Now let's take a look at some of our cool Formula 1 data we just loaded up!
    1. Create a SQL worksheet by selecting the **+** then **SQL Worksheet**.
        <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/3-connect-to-data-source/3-create-new-worksheet-to-query-data.png" title="Create new worksheet to query data"/>
    2. Navigate to **Database > Formula1 > RAW > Tables**. 
    3. Query the data using the following code. There are only 76 rows in the circuits table, so we don’t need to worry about limiting the amount of data we query.
        ```sql
        select * from formula1.raw.circuits
        ```
    4. Run the query. From here on out, we’ll use the keyboard shortcuts Command-Enter or Control-Enter to run queries and won’t explicitly call out this step. 
    5. Review the query results, you should see information about Formula 1 circuits, starting with Albert Park in Australia! 
    6. Finally, ensure you have all 14 tables starting with `CIRCUITS` and ending with `STATUS`. Now we are ready to connect into dbt Cloud!

        <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/3-connect-to-data-source/4-query-circuits-data.png" title="Query circuits data"/>

<!-- ------------------------ -->
## Setup dbt account 
We are going to be using [Snowflake Partner Connect](https://docs.snowflake.com/en/user-guide/ecosystem-partner-connect.html) to set up a dbt Cloud account. Using this method will allow you to spin up a fully fledged dbt account with your [Snowflake connection](/docs/cloud/connect-data-platform/connect-snowflake) and environments already established.

1. Navigate out of your SQL worksheet back by selecting **home**.
2. In Snowsight, confirm that you are using the **ACCOUNTADMIN** role.
3. Navigate to the **Admin** **> Partner Connect**. Find **dbt** either by using the search bar or navigating the **Data Integration**. Select the **dbt** tile.
    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/4-configure-dbt/1-open-partner-connect.png" title="Open Partner Connect"/>
4. You should now see a new window that says **Connect to dbt**. Select **Optional Grant** and add the `FORMULA1` database. This will grant access for your new dbt user role to the FORMULA1 database.
    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/4-configure-dbt/2-partner-connect-optional-grant.png" title="Partner Connect Optional Grant"/>

5. Ensure the `FORMULA1` is present in your optional grant before clicking **Connect**.  This will create a dedicated dbt user, database, warehouse, and role for your dbt Cloud trial.

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/4-configure-dbt/3-connect-to-dbt.png" title="Connect to dbt"/>

6. When you see the **Your partner account has been created** window, click **Activate**.

7. You should be redirected to a dbt Cloud registration page. Fill out the form. Make sure to save the password somewhere for login in the future. 

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/4-configure-dbt/4-dbt-cloud-sign-up.png" title="dbt Cloud sign up"/>

8. Select **Complete Registration**. You should now be redirected to your dbt Cloud account, complete with a connection to your Snowflake account, a deployment and a development environment, and a sample job.

9. Instead of building an entire version controlled data project from scratch, we'll be forking and connecting to an existing workshop github repository in the next step. dbt Cloud's git integration creates easy to use git guardrails. You won't need to know much Git for this workshop. In the future, if you’re developing your own proof of value project from scratch, [feel free to use dbt's managed  repository](https://docs.getdbt.com/docs/collaborate/git/managed-repository) that is spun up during partner connect. 

<!-- ------------------------ -->
## Development schema and forking repo
In this section we'll be setting up our own personal development schema and forking our workshop repo into dbt Cloud. 

### Schema name
1. First we are going to change the name of our default schema to where our dbt models will build. By default, the name of your development schema might be`dbt_`. We will change this to `dbt_<YOUR_NAME>` to create your own personal development schema. To do this, select **Profile Settings** from the gear icon in the upper right. If this was already setup to your liking based off your dbt Cloud account name feel free to keep it as is. 

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/1-settings-gear-icon.png" title="Settings menu"/>

2. Navigate to the **Credentials** menu and select **Partner Connect Trial**, which will expand the credentials menu.

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/2-credentials-edit-schema-name.png" title="Credentials edit schema name"/>
    
3. Click **Edit** and change the name of your schema from `dbt_` to `dbt_YOUR_NAME` replacing `YOUR_NAME` with your initials and name (`hwatson` is used in the lab screenshots). Be sure to click **Save** for your changes!
    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/3-save-new-schema-name.png" title="Save new schema name"/>

4. We now have our own personal development schema, amazing! When we run our first dbt models they will build into this schema.

### Forking repo and github deploy keys

To keep the focus on dbt python and deployment today, we only want to build a subset of models that would be in an entire data project. To achieve this we need to fork an existing repository into our personal github, copy our forked repo name into dbt cloud, and add the dbt deploy key to our github account. Viola! There will be some back and forth between dbt cloud and GitHub as part of this process, so keep your tabs open, and let's get the setup out of the way!

1. Delete the existing connection to the managed repository. To do this navigate to **Settings > Account Settings > Partner Connect Trial**.
2. This will open the **Project Details**. Navigate to **Repository** and click the existing managed repository GitHub connection setup during partner connect.
3. In the **Respository Details** select **Edit** in the lower right corner. The option to **Disconnect** will appear, select it.
4. Confirm disconnect. 
5. Your repository should now be blank in your **Project Details**.
6. Login to your personal GitHub account. 
7. Using the search bar, find today's demo repo dbt-labs/dbt-snowflake-summit-2023-hands-on-lab-snowpark
8. Fork your own copy of the lab repo.
9. Select the **Code** button. Choose the SSH option and use the copy button shortcut for our repo. 
10. Navigate back to dbt cloud. Input the repository you copied into the **Repository** parameter. 
11. dbt Cloud will generate a deploy key to link the development we do in dbt cloud back to our github repo. Copy the deploy key starting with **ssh-rsa** followed by a long hash key. 
12. Phew almost there! Navigate back to GitHub again. 
13. Ensure you're in your forked repo. Navigate to your repo **Settings**
14. Go to **Deploy keys** and select **Add deploy key**.
15. Give your deploy key a title such as `dbt Cloud Snowflake Summit`. Paste the key we ssh-rsa deploy key we copied from dbt Cloud into the **Key** box. Be sure to enable **Allow write access**. Finally, **Add key**. We won't have to come back to again GitHub until the end of our workshop.
16. Head back over to dbt cloud. Navigate to **Develop**.
17. **Run "dbt deps"**

Alas, now that our setup work is complete, time get a look at our data pipeline! 

<!-- ------------------------ -->
## IDE overview and buidling first dbt models
dbt Cloud's IDE will be our development space for this workshop, so let's get familiar with it. Once we've done that we'll run the pipeline we imported from our forked repo. 

1. There are a couple of key features to point out about the IDE before we get to work. It is a text editor, an SQL and Python runner, and a CLI with Git version control all baked into one package! This allows you to focus on editing your SQL and Python files, previewing the results with the SQL runner (it even runs Jinja!), and building models at the command line without having to move between different applications. The Git workflow in dbt Cloud allows both Git beginners and experts alike to be able to easily version control all of their work with a couple clicks.

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/7-IDE-overview.png" title="IDE overview"/>

2. Let's run the pipeline we imported from our forked repo. Type `dbt build` into the command line and click **Enter** on your keyboard. When the run bar expands you'll be able to see the results of the run, where you should see the run complete successfully.
TODO Update with new pipeline 
    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/8-dbt-run-example-models.png" title="dbt run example models"/>

3. Take a few minutes to poke around our pipeline and viewing the DAG lineage. We'll go more in-depth in next steps about how we brought in raw data and then transformed it, but for now get an overall familiarization. 

4. The run results allow you to see the code that dbt compiles and sends to Snowflake for execution. To view the logs for this run, select one of the model tabs using the  **>** icon and then **Details**. If you scroll down a bit you'll be able to see the compiled code and how dbt interacts with Snowflake. Given that this run took place in our development environment, the models were created in your development schema.

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/9-second-model-details.png" title="Details about the second model"/>

 TODO Update with new pipeline 
5. Now let's switch over to a new browser tab on Snowflake to confirm that the objects were actually created. Click on the three dots **…** above your database objects and then **Refresh**. Expand the **PC_DBT_DB** database and you should see your development schema. Select the schema, then **Tables**  and **Views**. Now you should be able to see many models we created from our forked repo. 
    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/5-development-schema-name/10-confirm-example-models-built-in-snowflake.png" title="Confirm example models are built in Snowflake"/>


<!-- ------------------------ -->
## Understanding our existing pipeline 
We brought a good chunk of our data pipeline in through our forked repo to lay a foundation for machine learning.
In the next couple steps we are taking time to review how this was done. That way when you have your own dbt project you'll be familiar with the setup.


### dbt_project.yml
1. Select the `dbt_project.yml` file from the file tree to open it. What are we looking at here? Every dbt project requires a `dbt_project.yml` file &mdash; this is how dbt knows a directory is a dbt project. The [dbt_project.yml](/reference/dbt_project.yml) file also contains important information that tells dbt how to operate on your project.
2. Your code shoudl like as follows: 
    ```yaml
    name: 'snowflake_python_workshop'
    version: '1.5.0'
    require-dbt-version: '>=1.3.0'
    config-version: 2

    # This setting configures which "profile" dbt uses for this project.
    profile: 'default'

    # These configurations specify where dbt should look for different types of files.
    # The `source-paths` config, for example, states that models in this project can be
    # found in the "models/" directory. You probably won't need to change these!
    model-paths: ["models"]
    analysis-paths: ["analyses"]
    test-paths: ["tests"]
    seed-paths: ["seeds"]
    macro-paths: ["macros"]
    snapshot-paths: ["snapshots"]

    target-path: "target"  # directory which will store compiled SQL files
    clean-targets:         # directories to be removed by `dbt clean`
      - "target"
      - "dbt_packages"

    models:
      snowflake_python_workshop:
        staging:
          +docs:
            node_color: "CadetBlue"

        marts:
          +materialized: table
          aggregates:
            +docs:
              node_color: "Maroon"
            +tags: "bi"

        core:
          +materialized: table
          +docs:
            node_color: "#800080"

        ml:
          +materialized: table
          prep_encoding_splitting:
            +docs:
              node_color: "Indigo"
          training_and_prediction:
            +docs:
              node_color: "Black"
    ```

3. The key configurations to point out in the file with relation to the work that we're going to do are in the `models` section.
    - `require-dbt-version` &mdash; Tells dbt which version of dbt to use for your project. We are requiring 1.3.0 and any newer version to run python models and node colors.
    - `materialized` &mdash; Tells dbt how to materialize models when compiling the code before it pushes it down to Snowflake. All models in the `marts` folder will be built as tables.
    - `tags` &mdash; Applies tags at a directory level to all models. All models in the `aggregates` folder will be tagged as `bi` (abbreviation for business intelligence).
4. [Materializations](/docs/build/materializations) are strategies for persisting dbt models in a warehouse, with `tables` and `views` being the most commonly utilized types. By default, all dbt models are materialized as views and other materialization types can be configured in the `dbt_project.yml` file or in a model itself. It’s very important to note *Python models can only be materialized as tables or incremental models.* Since all our Python models exist under `marts`, the following portion of our `dbt_project.yml` ensures no errors will occur when we run our Python models. Starting with [dbt version 1.4](/guides/migration/versions/upgrading-to-v1.4#updates-to-python-models), Python files will automatically get materialized as tables even if not explicitly specified.

    ```yaml 
    marts:     
      +materialized: table
    ``` 

Cool, now that dbt knows we have a dbt project we can view the folder structure and data modeling.  

### Folder structure 
TODO Update with new folders
dbt Labs has developed a [project structure guide](/guides/best-practices/how-we-structure/1-guide-overview/) that contains a number of recommendations for how to build the folder structure for your project. These apply to our entire project except the machine learning portion - this is still relatively new use case in dbt without the same established best practices. 
Do check out that guide if you want to learn more. Right now we are going to organize our project using the following structure:

- sources &mdash; This is our Formula 1 dataset and it will be defined in a source YAML file. Nested under our Staging folder. 
- staging models &mdash; These models have a 1:1 with their source table and are for light transformation (renaming columns, recasting data types, etc.).
- core models &mdash; Fact and dimension tables available for end user analysis. Since the Formula 1 is pretty clean demo data these look similar to our staging models. 
- marts models &mdash; Here is where we perform our major transformations. It contains the subfolder:
    - aggregates
- ml &mdash; we'll be creating this folder and subfolders:
    - prep_encoding_splitting
    - training_and_prediction

1. In your file tree, use your cursor and hover over the `models` subdirectory, click the three dots **…** that appear to the right of the folder name, then select **Create Folder**. We're going to add two new folders to the file path, `ml` and `prep_encoding_splitting` (in that order) by typing `ml/prep_encoding_splitting` into the file path.

TODO update screeenshots 
    <!-- <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/7-folder-structure/1-create-folder.png" title="Create folder"/>
    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/7-folder-structure/2-file-path.png" title="Set file path"/> -->
    
    - If you click into your `models` directory now, you should see the new `ml` folder nested within `models` and the `prep_encoding_splitting` folder nested within `ml`.

2. We will need to create one more subfolder using the UI, under the `ml` folder create `training_and_prediction`. After you create these folders, your entire folder tree should look like this when it's all done (from what we forked and just created):

    <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/7-folder-structure/3-tree-of-new-folders.png" title="File tree of new folders"/>

Remember you can always reference the entire project in [GitHub](https://github.com/dbt-labs/python-snowpark-formula1) to view the complete folder and file strucutre.  

<!-- ------------------------ -->
## Data modeling -- sources and staging 
In any data project we start with raw data, clean and transform, and gain insights. In this step we'll be showing you how to bring raw data into dbt and create staging models. The steps of setting up sources and staging models were completed when we forked our repo, so we'll only need to preview these files (instead of build them).

Sources allow us to create a dependency between our source database object and our staging models which will help us when we look at [data-lineage](https://docs.getdbt.com/terms/data-lineage)later. Also, if your source changes database or schema, you only have to update it in your `f1_sources.yml` file rather than updating all of the models it might be used in.

Staging models are the base of our project, where we bring all the individual components we're going to use to build our more complex and useful models into the project. Staging models have a 1:1 relationship with their source table and are for light transformation steps such as renaming columns, type casting, basic computations, and categorizing data. 

Since we want to focus on dbt and Python in this workshop, check out our [sources](https://docs.getdbt.com/docs/build/sources) and [staging](https://docs.getdbt.com/guides/best-practices/how-we-structure/2-staging) docs if you want to learn more (or take our [dbt Fundamentals](https://courses.getdbt.com/collections) course which covers all of our core functionality).

### Creating Sources 
1. Open the file called `f1_sources.yml` with the following file path: `models/staging/formula1/f1_sources.yml`.
2. You should see the following code that creates our 14 source tables in our dbt project from Snowflake:

3. dbt makes it really easy to:
  - declare [sources](https://docs.getdbt.com/docs/build/sources)
  - provide [testing](https://docs.getdbt.com/docs/build/tests) for data quality and integrity with support for both generic and singular tests 
  - create [documentation](https://docs.getdbt.com/docs/collaborate/documentation) using descriptions where you write code


### Staging 
1. Let's view two staging models that we'll be using to understand lap time trends through the years. 
2. Open `stg_lap_times`. 
    ```sql
    with

    lap_times as (select * from {{ source('formula1', 'lap_times') }}),

    renamed as (
        select
            race_id as race_id,
            driver_id as driver_id,
            lap,
            "POSITION" as driver_position,
            "TIME" as lap_time_formatted,
            {{ convert_laptime("lap_time_formatted") }} as official_laptime,
            milliseconds as lap_time_milliseconds
        from lap_times
    )
    select
        {{ dbt_utils.generate_surrogate_key(["race_id", "driver_id", "lap"]) }}
        as lap_times_id,
        *
    from renamed
    ```
3. Review the SQL code. We see renaming columns using the alias in addition to reformatting using a jinja code in our project referencing a macro. At a high level a macro is a reusable piece of code and jinja is the way we can bring that code into our SQL model. Datetimes column formatting is usually tricky and repetitive. By using a macro we introduce a way to systematic format times and reduce redunant code in our Formula 1 project. 
4. Click **preview** &mdash; look how pretty and human readable our official_laptime column is!
5. Feel free to view our project macros under the root folder `macros` and look at the code for our convert_laptime macro in the `convert_laptim.sql` file. 
6. We can see the reusable logic we have for splitting apart different components of our lap times from hours to nanoseconds. If you want to learn more about leveraging macros within dbt SQL, check out our [macros documentation](https://docs.getdbt.com/docs/build/jinja-macros). 
7. TODO talk about surrogate_key and dbt_utils


You can see for every source table, we have a staging table. Now that we're done staging our data it's time for transformation.

<!-- ------------------------ -->
## SQL Transformations 
dbt got it's start in being a powerful tool to enhance the way data transformations are done in SQL. Before we jump into python, let's pay homage to SQL. 
SQL is so performant at data cleaning and transformation, that many data science projects "use SQL for everything you can, then hand off to python" and that's exactly what we're going to do. 

### Fact and dimension tables 
[Dimensional modeling](https://docs.getdbt.com/terms/dimensional-modeling) is an important data modeling concept where we break up data into "facts" and "dimensions" to organize and describe data. We won't go into depth here, but think of facts as "skinny and long" transactional tables and dimensions as "wide" referential tables. We'll preview one dimension table and be building one fact table. 

1. Navigate in the file tree to **models > marts > core > dim_races**. 
2. **Preview** the data. We can see we have the `RACE_YEAR` in this table. That's important since we want to understand the changes in lap times over years. So we now know `dim_races` contains the time column we need to make those calculations. 
3. Create a new file within the **core** directory **core > ... > Create file**.
4. Name the file `fct_lap_times.sql`.
5. Copy in the following code and save the file (**Save** or Ctrl+S):
    ```sql
    WITH lap_times AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['race_id', 'driver_id', 'lap']) }}         AS lap_times_id,
        race_id                                                                         AS race_id,
        driver_id                                                                       AS driver_id,
        lap                                                                             AS lap,
        driver_position                                                                 AS driver_position,
        lap_time_formatted                                                              AS lap_time_formatted,
        official_laptime                                                                AS official_laptime,
        lap_time_milliseconds                                                           AS lap_time_milliseconds
    FROM {{ ref('stg_lap_times') }}
    )

    SELECT * FROM lap_times
    ```
6. Our `fct_lap_times` is very similar to our staging file since this is clean demo data. In your real world data project your data will probably be messier and require extra filtering and aggregation prior to becoming a fact table exposed to your business users for utilizing.
7. Use the UI **BUILD** to create the `fct_lap_times` model. 

Now we have both `dim_races` and `fct_lap_times` separately. Next we'll to join these to create lap trend analysis through the years.

### Marts tables
Marts tables are where everything comes together to create our business-defined entities that have an identity and purpose. 
We'll be joining our `dim_races` and `fct_lap_times` together. 

1. Create a new file under your **marts** folder called `mrt_lap_times_years.sql`.
2. Copy and save the following code:
    ```sql
    with lap_times as (
    select * from {{ ref('fct_lap_times') }}
        ),
        races as (
        select * from {{ ref('dim_races') }}
        ),
        expanded_lap_times_by_year as (
            select 
                lap_times.race_id, 
                driver_id, 
                race_year,
                lap,
                lap_time_milliseconds 
            from lap_times
            left join races
                on lap_times.race_id = races.race_id
            where lap_time_milliseconds is not null 
        )
        select * from expanded_lap_times_by_year
    ```
3. Our dataset contains races going back to 1950, but the measurement of lap times begins in 1996. Here we join our datasets together use our `where` clause to filter our races prior to 1996, so they have lap times. 
4. Execute the model using **Build**. 
5. **Preview** your new model. We have race years and lap times together in one joined table so we are ready to create our trend analysis. 

Now that we've joined and denormalized our data we're ready to use it in python development. 

<!-- ------------------------ -->
## Python development in snowflake python worksheets 
Now that we've transformed data using SQL let's write our first python code and get insights about lap time trends.
Snowflake python worksheets are excellent for developing your python code before bringing it into a dbt python model.
Then once we are settled on the code we want, we can drop it into our dbt project. 

1. Head back over to Snowflake.
2. Open up a **Python Worksheet**. 

TODO I think more explanation of python worksheets would go well here. (@snowflake team)
TODO @snowflake team -- feel free to translate this python worksheet into snowpark code and clean up a bit (i.e. final_df isn't really necessary)
3. Use the following code to get a 5 year moving average of Formula 1 laps:
    ```python
    # The Snowpark package is required for Python Worksheets. 
    # You can add more packages by selecting them using the Packages control and then importing them.

    import snowflake.snowpark as snowpark
    import pandas as pd 

    def main(session: snowpark.Session): 
        # Your code goes here, inside the "main" handler.
        tableName = 'MRT_LAP_TIMES_YEARS'
        dataframe = session.table(tableName)
        lap_times = dataframe.to_pandas()

        # print table
        print(lap_times)

        # describe the data
        lap_times["LAP_TIME_SECONDS"] = lap_times["LAP_TIME_MILLISECONDS"]/1000
        lap_time_trends = lap_times.groupby(by="RACE_YEAR")["LAP_TIME_SECONDS"].mean().to_frame()
        lap_time_trends.reset_index(inplace=True)
        lap_time_trends["LAP_MOVING_AVG_5_YEARS"] = lap_time_trends["LAP_TIME_SECONDS"].rolling(5).mean()
        lap_time_trends.columns = lap_time_trends.columns.str.upper()

        final_df = session.create_dataframe(lap_time_trends)
        # Return value will appear in the Results tab.
        return final_df
    ```
4. Ensure you are in your development database and schema (i.e. **PC_DBT_DB** and **DBT_HWATSON**) and run the Python worksheet (Ctrl+A and **Run**). 
5. Your result should have three columns: `race_year`, `lap_time_seconds`, and `lap_moving_avg_5_years`. This dataframe is in great shape for visualization in a downstream BI tool or application. We were able to quickly calculate a 5 year moving average using python instead of having to sort our data and worry about lead and lag SQL commands. At a glance we can see that lap times seem to be trending down with small fluctuations until 2010 and 2011 which coincides with drastic Formula 1 [regulation changes](https://en.wikipedia.org/wiki/History_of_Formula_One_regulations) including cost-cutting measures and in-race refuelling bans. So we can safely ascertain lap times are not consistently decreasing. 

Now that we've created this dataframe and lap time trend insight, what do we do when we want to scale it? In the next section we'll be learning how to do this by leveraging python transformations in dbt Cloud. 
<!-- ------------------------ -->
## Python transfomrations in dbt Cloud 
### Our first dbt python model for lap time trends
Let's get our lap time trends in our data pipeline so we have this data frame to leverage as new data comes in. The syntax of of a dbt python model is a variation of our development code in the python worksheet so we'll be explaining the code and concepts more.

1. Open your dbt Cloud browser tab. 
2. Create a new file under the **models > marts > aggregates** directory called `agg_lap_times_moving_avg.py`. 
3. Copy the following code in and save the file:
    ```python
    import pandas as pd

    def model(dbt, session):
        # dbt configuration
        dbt.config(packages=["pandas"])

        # get upstream data
        lap_times = dbt.ref("mrt_lap_times_years").to_pandas()

        # describe the data
        lap_times["LAP_TIME_SECONDS"] = lap_times["LAP_TIME_MILLISECONDS"]/1000
        lap_time_trends = lap_times.groupby(by="RACE_YEAR")["LAP_TIME_SECONDS"].mean().to_frame()
        lap_time_trends.reset_index(inplace=True)
        lap_time_trends["LAP_MOVING_AVG_5_YEARS"] = lap_time_trends["LAP_TIME_SECONDS"].rolling(5).mean()
        lap_time_trends.columns = lap_time_trends.columns.str.upper()
        
        return lap_time_trends.round(1)
    ```
4. Let’s break down what this code is doing:
    - First, we are importing the Python libraries that we are using. This is similar to a dbt *package*, but our Python libraries do *not* persist across the entire project.
    - Defining a function called `model` with the parameter `dbt` and `session`. We'll define these more in depth later in this section. You can see that all the data transformation happening is within the body of the `model` function that the `return` statement is tied to.
    - Then, within the context of our dbt model library, we are passing in a configuration of which packages we need using `dbt.config(packages=["pandas"])`.
    - Use the `.ref()` function to retrieve the upstream data frame `mrt_lap_times_years` that we created in our last step using SQL. We cast this to a pandas dataframe (by default it's a Snowpark Dataframe).
    - From there we are using python to transform our dataframe to give us a rolling average by using `rolling()` over `RACE_YEAR`. 
    - Convert our Python column names to all uppercase using `.upper()`, so Snowflake recognizes them. **This has been a frequent "gotcha" for folks using dbt python so we call it out here.**
    We won’t go as in depth for our subsequent scripts, but will continue to explain at a high level what new libraries, functions, and methods are doing.
5. Create the model in our warehouse by clicking **Build**.
6. We can't preview Python models directly, so let’s create a new file using the **+** button or the Control-N shortcut to create a new scratchpad:
  ```sql
    select * from {{ ref('agg_lap_times_moving_avg') }}
    ```
    and preview the output:
TODO add screenshot 
7. We can see we have the same results from our python worksheet development as we have in our codified dbt python project. 

### The dbt model, .source(), .ref() and .config() functions

Let’s take a step back before starting machine learning to both review and go more in-depth at the methods that make running dbt python models possible. If you want to know more outside of this lab’s explanation read the documentation [here](https://docs.getdbt.com/docs/building-a-dbt-project/building-models/python-models).

- dbt model(dbt, session). For starters, each Python model lives in a .py file in your models/ folder. It defines a function named `model()`, which takes two parameters:
    - dbt &mdash; A class compiled by dbt Core, unique to each model, enables you to run your Python code in the context of your dbt project and DAG.
    - session &mdash; A class representing your data platform’s connection to the Python backend. The session is needed to read in tables as DataFrames and to write DataFrames back to tables. In PySpark, by convention, the SparkSession is named spark, and available globally. For consistency across platforms, we always pass it into the model function as an explicit argument called session.
- The `model()` function must return a single DataFrame. On Snowpark (Snowflake), this can be a Snowpark or pandas DataFrame.
- `.source()` and `.ref()` functions. Python models participate fully in dbt's directed acyclic graph (DAG) of transformations. If you want to read directly from a raw source table, use `dbt.source()`. We saw this in our earlier section using SQL with the source function. These functions have the same execution, but with different syntax. Use the `dbt.ref()` method within a Python model to read data from other models (SQL or Python). These methods return DataFrames pointing to the upstream source, model, seed, or snapshot.
- `.config()`. Just like SQL models, there are three ways to configure Python models:
    - In a dedicated `.yml` file, within the `models/` directory
    - Within the model's `.py` file, using the `dbt.config()` method
    - Calling the `dbt.config()` method will set configurations for your model within your `.py` file, similar to the `{{ config() }} macro` in `.sql` model files. There's a limit to how complex you can get with the `dbt.config()` method. It accepts only literal values (strings, booleans, and numeric types). Passing another function or a more complex data structure is not possible. The reason is that dbt statically analyzes the arguments to `.config()` while parsing your model without executing your Python code. If you need to set a more complex configuration, we recommend you define it using the config property in a [YAML file](/reference/resource-properties/config). Learn more about configurations [here](/reference/model-configs).
        ```python 
        def model(dbt, session):

        # setting configuration
        dbt.config(materialized="table")
        ```
Now that we understand how to create python transformations we can use them to prepare our data for machine learning!

<!-- ------------------------ -->
## Machine Learning prep -- cleaning and encoding
Now that we’ve gained insights and business intelligence about Formula 1 at a descriptive level, we want to extend our capabilities into prediction. We’re going to take the scenario where we censor the data. This means that we will pretend that we will train a model using earlier data and apply it to future data. In practice, this means we’ll take data from 2010-2019 to train our model and then predict 2020 data.

In this section, we’ll be preparing our data to predict the final race position of a driver.

At a high level we’ll be:

- Creating new prediction features and filtering our dataset to active drivers
- Encoding our data (algorithms like numbers) and simplifying our target variable called `position`
- Splitting our dataset into training, testing, and validation

### ML data prep

1. Take a minute to **Preview** and look at the **Lineage** of the `mrt_results_circuits` which is the foundational dataset we'll be starting our machine leanring on. Get to understand the columns. Some *hierarchial joins were completed to get this nice clean dataset we brought in through our repo forking.
2.  To keep our project organized, we’ll need to create two new subfolders in our `ml` directory. Under the `ml` folder, make the subfolders `prep_encoding_splitting` and `training_and_prediction`.
    *to know the circuit of a result, we first had to join results to races together, then circuits to races. 
3. Create a new file under `ml/prep_encoding_splitting` called `ml_data_prep.py`. Copy the following code into the file and **Save**:
    ```python 
    import pandas as pd

    def model(dbt, session):
        # dbt configuration
        dbt.config(packages=["pandas"])

        # get upstream data
        fct_results = dbt.ref("mrt_results_circuits").to_pandas()

        # provide years so we do not hardcode dates in filter command
        start_year=2010
        end_year=2020

        # describe the data for a full decade
        data =  fct_results.loc[fct_results['RACE_YEAR'].between(start_year, end_year)]

        # convert string to an integer
        # data['POSITION'] = data['POSITION'].astype(float)

        # we cannot have nulls if we want to use total pit stops 
        data['TOTAL_PIT_STOPS_PER_RACE'] = data['TOTAL_PIT_STOPS_PER_RACE'].fillna(0)

        # some of the constructors changed their name over the year so replacing old names with current name
        mapping = {'Force India': 'Racing Point', 'Sauber': 'Alfa Romeo', 'Lotus F1': 'Renault', 'Toro Rosso': 'AlphaTauri'}
        data['CONSTRUCTOR_NAME'].replace(mapping, inplace=True)

        # create confidence metrics for drivers and constructors
        dnf_by_driver = data.groupby('DRIVER').sum()['DNF_FLAG']
        driver_race_entered = data.groupby('DRIVER').count()['DNF_FLAG']
        driver_dnf_ratio = (dnf_by_driver/driver_race_entered)
        driver_confidence = 1-driver_dnf_ratio
        driver_confidence_dict = dict(zip(driver_confidence.index,driver_confidence))

        dnf_by_constructor = data.groupby('CONSTRUCTOR_NAME').sum()['DNF_FLAG']
        constructor_race_entered = data.groupby('CONSTRUCTOR_NAME').count()['DNF_FLAG']
        constructor_dnf_ratio = (dnf_by_constructor/constructor_race_entered)
        constructor_relaiblity = 1-constructor_dnf_ratio
        constructor_relaiblity_dict = dict(zip(constructor_relaiblity.index,constructor_relaiblity))

        data['DRIVER_CONFIDENCE'] = data['DRIVER'].apply(lambda x:driver_confidence_dict[x])
        data['CONSTRUCTOR_RELAIBLITY'] = data['CONSTRUCTOR_NAME'].apply(lambda x:constructor_relaiblity_dict[x])

        #removing retired drivers and constructors
        active_constructors = ['Renault', 'Williams', 'McLaren', 'Ferrari', 'Mercedes',
                            'AlphaTauri', 'Racing Point', 'Alfa Romeo', 'Red Bull',
                            'Haas F1 Team']
        active_drivers = ['Daniel Ricciardo', 'Kevin Magnussen', 'Carlos Sainz',
                        'Valtteri Bottas', 'Lance Stroll', 'George Russell',
                        'Lando Norris', 'Sebastian Vettel', 'Kimi Räikkönen',
                        'Charles Leclerc', 'Lewis Hamilton', 'Daniil Kvyat',
                        'Max Verstappen', 'Pierre Gasly', 'Alexander Albon',
                        'Sergio Pérez', 'Esteban Ocon', 'Antonio Giovinazzi',
                        'Romain Grosjean','Nicholas Latifi']

        # create flags for active drivers and constructors so we can filter downstream              
        data['ACTIVE_DRIVER'] = data['DRIVER'].apply(lambda x: int(x in active_drivers))
        data['ACTIVE_CONSTRUCTOR'] = data['CONSTRUCTOR_NAME'].apply(lambda x: int(x in active_constructors))
        
        return data
    ```
4. As usual, let’s break down what we are doing in this Python model:
    - We’re first referencing our upstream `mrt_results_circuits` table and casting it to a pandas dataframe.
    - Filtering on years 2010-2020 since we’ll need to clean all our data we are using for prediction (both training and testing).
    - Filling in empty data for `total_pit_stops` and making a mapping active constructors and drivers to avoid erroneous predictions
        - ⚠️ You might be wondering why we didn’t do this upstream in our `mrt_results_circuits` table! The reason for this is that we want our machine learning cleanup to reflect the year 2020 for our predictions and give us an up-to-date team name. However, for business intelligence purposes we can keep the historical data at that point in time. Instead of thinking of one table as “one source of truth” we are creating different datasets fit for purpose: one for historical descriptions and reporting and another for relevant predictions.
    - Create new features for driver and constructor confidence. This metric is created as a proxy for understanding consistency and reliability. There are more aspects we could consider for this project, such as normalizing the driver confidence by the number of races entered, but we'll keep it simple.
    - Generate flags for the constructors and drivers that were active in 2020. 
5. **Build** the `ml_data_prep`.
6. Open a scratchpad and preview our clean dataframe after creating our `ml_data_prep` dataframe:
  ```sql
    select * from {{ ref('ml_data_prep') }}
    ```
  <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/11-machine-learning-prep/1-completed-ml-data-prep.png" title="What our clean dataframe fit for machine learning looks like"/>

Now that our data is clean it's time to encode it. 

<!-- ------------------------ -->
### Covariate encoding
In this next part, we’ll be performing covariate encoding. Breaking down this phrase a bit, a *covariate* is a variable that is relevant to the outcome of a study or experiment, and *encoding* refers to the process of converting data (such as text or categorical variables) into a numerical format that can be used as input for a model. This is necessary because most machine learning algorithms can only work with numerical data. Algorithms don’t speak languages, have eyes to see images, etc. so we encode our data into numbers so algorithms can perform tasks by using calculations they otherwise couldn’t.

🧠 We’ll think about this as : “algorithms like numbers”.

1. Create a new file under `ml/prep` called `covariate_encoding.py` copy the code below and save.
    ```python
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler,LabelEncoder,OneHotEncoder
    from sklearn.linear_model import LogisticRegression

    def model(dbt, session):
    # dbt configuration
    dbt.config(packages=["pandas","numpy","scikit-learn"])

    # get upstream data
    data = dbt.ref("ml_data_prep").to_pandas()

    # list out covariates we want to use in addition to outcome variable we are modeling - position
    covariates = data[['RACE_YEAR','CIRCUIT_NAME','GRID','CONSTRUCTOR_NAME','DRIVER','DRIVERS_AGE_YEARS','DRIVER_CONFIDENCE','CONSTRUCTOR_RELAIBLITY','TOTAL_PIT_STOPS_PER_RACE','ACTIVE_DRIVER','ACTIVE_CONSTRUCTOR', 'POSITION']]
    
    # filter covariates on active drivers and constructors
    # use fil_cov as short for "filtered_covariates"
    fil_cov = covariates[(covariates['ACTIVE_DRIVER']==1)&(covariates['ACTIVE_CONSTRUCTOR']==1)]

    # Encode categorical variables using LabelEncoder
    # TODO: we'll update this to both ohe in the future for non-ordinal variables! 
    le = LabelEncoder()
    fil_cov['CIRCUIT_NAME'] = le.fit_transform(fil_cov['CIRCUIT_NAME'])
    fil_cov['CONSTRUCTOR_NAME'] = le.fit_transform(fil_cov['CONSTRUCTOR_NAME'])
    fil_cov['DRIVER'] = le.fit_transform(fil_cov['DRIVER'])
    fil_cov['TOTAL_PIT_STOPS_PER_RACE'] = le.fit_transform(fil_cov['TOTAL_PIT_STOPS_PER_RACE'])

    # Simply target variable "position" to represent 3 meaningful categories in Formula1
    # 1. Podium position 2. Points for team 3. Nothing - no podium or points!
    def position_index(x):
        if x<4:
            return 1
        if x>10:
            return 3
        else :
            return 2

    # we are dropping the columns that we filtered on in addition to our training variable
    encoded_data = fil_cov.drop(['ACTIVE_DRIVER','ACTIVE_CONSTRUCTOR'],1)
    encoded_data['POSITION_LABEL']= encoded_data['POSITION'].apply(lambda x: position_index(x))
    encoded_data_grouped_target = encoded_data.drop(['POSITION'],1)

    return encoded_data_grouped_target
    ```
2. Create the model using **Build**. 
3. In this code we are using [Scikit-learn](https://scikit-learn.org/stable/), “sklearn” for short, is an extremely popular data science library. We’ll be using Sklearn for both preparing our covariates and creating models (our next section). Our dataset is pretty small data so we are good to use pandas and `sklearn`. If you have larger data for your own project in mind, consider Snowpark dataframes, `dask`, or `category_encoders`.
4. Breaking our code down a bit more:
    - We’re selecting a subset of variables that will be used as predictors for a driver’s position.
    - Filter the dataset to only include rows using the active driver and constructor flags we created in the last step.
    - The next step is to use the `LabelEncoder` from scikit-learn to convert the categorical variables `CIRCUIT_NAME`, `CONSTRUCTOR_NAME`, `DRIVER`, and `TOTAL_PIT_STOPS_PER_RACE` into numerical values.
    - To simplify the classification and improve performance, we are creating a new variable called `POSITION_LABEL` from our original position variable with in Formula 1 with 20 total positions. This new variable has a specific meaning: those in the top 3 get a “podium” position, those in the top 10 get points that add to their overall season total, and those below the top 10 get no points. The original position variable is being mapped to position_label in a way that assigns 1, 2, and 3 to the corresponding places.
    - Drop the active driver and constructor flags since they were filter criteria and are now all the same value, which won't increase prediction lift of an algorithm. Finally, drop our original position variable.

<!-- ------------------------ -->
## Splitting into training and testing datasets

In this step, we will create dataframes to use for training and prediction. We’ll be creating two dataframes 1) using data from 2010-2019 for training, and 2) data from 2020 for new prediction inferences. We’ll create variables called `start_year` and `end_year` so we aren’t filtering on hardcasted values (and can more easily swap them out in the future if we want to retrain our model on different timeframes).

TODO @snowflake @DanHunt if you want to redo scripts to show of random functionality here that works. Please note that the temporal split is intentional as to not cause temporal leakage.

1. Create a file called `training_and_testing_dataset.py` copy and save the following code:
    ```python 
    import pandas as pd

    def model(dbt, session):

        # dbt configuration
        dbt.config(packages=["pandas"], tags="train")

        # get upstream data
        encoding = dbt.ref("covariate_encoding").to_pandas()

        # provide years so we do not hardcode dates in filter command
        start_year=2010
        end_year=2019

        # describe the data for a full decade
        train_test_dataset =  encoding.loc[encoding['RACE_YEAR'].between(start_year, end_year)]

        return train_test_dataset
    ```

2. Create a file called `hold_out_dataset_for_prediction.py` copy and save the following code below. Now we’ll have a dataset with only the year 2020 that we’ll keep as a hold out set that we are going to use similar to a deployment use case.
    ```python 
    import pandas as pd

    def model(dbt, session):
        # dbt configuration
        dbt.config(packages=["pandas"], tags="predict")

        # get upstream data
        encoding = dbt.ref("covariate_encoding").to_pandas()
        
        # variable for year instead of hardcoding it 
        year=2020

        # filter the data based on the specified year
        hold_out_dataset =  encoding.loc[encoding['RACE_YEAR'] == year]
        
        return hold_out_dataset
    ```
3. Execute the following in the command bar:
    ```bash
    dbt run --select train_test_dataset hold_out_dataset_for_prediction
    ```
    To run multiple models by name, we can use the *space* syntax [syntax](/reference/node-selection/syntax) between the model names. 
4. **Commit and sync** our changes to keep saving our work as we go using `ml data prep and splits` before moving on.

👏 Now that we’ve finished our machine learning prep work we can move onto the fun part &mdash; training and prediction!

<!-- ------------------------ -->
## Machine Learning: training and prediction
We’re ready to start training a model to predict the driver’s position. During the ML development phase you’ll try multiple algorithms and use an evaluation method such as cross validation to determine which algorithm to use. You can definitely use dbt if you want to save and reproduce dataframes from your ML development and model selection process, but for the content of this lab we’ll have skipped ahead decided on using a logistic regression to predict position (we actually tried some other algorithms using cross validation outside of this lab such as k-nearest neighbors and a support vector classifier but that didn’t perform as well as the logistic regression and a decision tree that overfit). By doing this we won't have to make code changes between development and deployment today. 

There are 3 areas to break down as we go since we are working at the intersection all within one model file:
1. Machine Learning
2. Snowflake and Snowpark
3. dbt Python models

If you haven’t seen code like this before or use joblib files to save machine learning models, we’ll be going over them at a high level and you can explore the links for more technical in-depth along the way! Because Snowflake and dbt have abstracted away a lot of the nitty gritty about serialization and storing our model object to be called again, we won’t go into too much detail here. There’s *a lot* going on here so take it at your pace!

<!-- ------------------------ -->
### Training and saving a machine learning model

1. Project organization remains key, so let’s make a new subfolder called `training_and_prediction.py` under the `ml` folder.
2. Now create a new file called `train_model_to_predict_position.py` and copy and save the following code:

    ```python 
    import snowflake.snowpark.functions as F
    from sklearn.model_selection import train_test_split
    import pandas as pd
    from sklearn.metrics import confusion_matrix, balanced_accuracy_score
    import io
    from sklearn.linear_model import LogisticRegression
    from joblib import dump, load
    import joblib
    import logging
    import sys
    from joblib import dump, load

    logger = logging.getLogger("mylog")

    def save_file(session, model, path, dest_filename):
    input_stream = io.BytesIO()
    joblib.dump(model, input_stream)
    session._conn.upload_stream(input_stream, path, dest_filename)
    return "successfully created file: " + path

    def model(dbt, session):
    dbt.config(
        packages = ['numpy','scikit-learn','pandas','numpy','joblib','cachetools'],
        materialized = "table",
        tags = "train"
    )
    # Create a stage in Snowflake to save our model file
    session.sql('create or replace stage MODELSTAGE').collect()
    
    #session._use_scoped_temp_objects = False
    version = "1.0"
    logger.info('Model training version: ' + version)

    # read in our training and testing upstream dataset
    test_train_df = dbt.ref("train_test_dataset")

    #  cast snowpark df to pandas df
    test_train_pd_df = test_train_df.to_pandas()
    target_col = "POSITION_LABEL"

    # split out covariate predictors, x, from our target column position_label, y.
    split_X = test_train_pd_df.drop([target_col], axis=1)
    split_y = test_train_pd_df[target_col]

    # Split out our training and test data into proportions
    X_train, X_test, y_train, y_test  = train_test_split(split_X, split_y, train_size=0.7, random_state=42)
    train = [X_train, y_train]
    test = [X_test, y_test]
        # now we are only training our one model to deploy
    # we are keeping the focus on the workflows and not algorithms for this lab!
    model = LogisticRegression()
    
    # fit the preprocessing pipeline and the model together 
    model.fit(X_train, y_train)   
    y_pred = model.predict_proba(X_test)[:,1]
    predictions = [round(value) for value in y_pred]
    balanced_accuracy =  balanced_accuracy_score(y_test, predictions)

    # Save the model to a stage
    save_file(session, model, "@MODELSTAGE/driver_position_"+version, "driver_position_"+version+".joblib" )
    logger.info('Model artifact:' + "@MODELSTAGE/driver_position_"+version+".joblib")
    
    # Take our pandas training and testing dataframes and put them back into snowpark dataframes
    snowpark_train_df = session.write_pandas(pd.concat(train, axis=1, join='inner'), "train_table", auto_create_table=True, create_temp_table=True)
    snowpark_test_df = session.write_pandas(pd.concat(test, axis=1, join='inner'), "test_table", auto_create_table=True, create_temp_table=True)
    
    # Union our training and testing data together and add a column indicating train vs test rows
    return  snowpark_train_df.with_column("DATASET_TYPE", F.lit("train")).union(snowpark_test_df.with_column("DATASET_TYPE", F.lit("test")))
    ```

3. Execute the following in the command bar:
    ```bash
    dbt run --select train_test_position
    ```
4. Breaking down our Python script here:
    - We’re importing some helpful libraries.
        - Defining a function called `save_file()` that takes four parameters: `session`, `model`, `path` and `dest_filename` that will save our logistic regression model file.
            - `session` &mdash; an object representing a connection to Snowflake.
            - `model` &mdash; when models are trained they are saved in memory, we will be using the model name to save our in-memory model into a joblib file to retrieve to call new predictions later.
            - `path` &mdash; a string representing the directory or bucket location where the file should be saved.
            - `dest_filename` &mdash; a string representing the desired name of the file.
        - Creating our dbt model
            - Within this model we are creating a stage called `MODELSTAGE` to place our logistic regression `joblib` model file. This is really important since we need a place to keep our model to reuse and want to ensure it's there. When using Snowpark commands, it's common to see the `.collect()` method to ensure the action is performed. Think of the session as our “start” and collect as our “end” when [working with Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes.html) (you can use other ending methods other than collect).
            - Using `.ref()` to connect into our `train_model_to_predict_position` model.
            - Now we see the machine learning part of our analysis:
                - Create new dataframes for our prediction features from our target variable `position_label`.
                - Split our dataset into 70% training (and 30% testing), train_size=0.7 with a `random_state` specified to have repeatable results.
                - Specify our model is a logistic regression.
                - Fit our model. In a logistic regression this means finding the coefficients that will give the least classification error.
                - Round our predictions to the nearest integer since logistic regression creates a probability between for each class and calculate a balanced accuracy to account for imbalances in the target variable.
        - Right now our model is only in memory, so we need to use our nifty function `save_file` to save our model file to our Snowflake stage. We save our model as a joblib file so Snowpark can easily call this model object back to create predictions. We really don’t need to know much else as a data practitioner unless we want to. It’s worth noting that joblib files aren’t able to be queried directly by SQL. To do this, we would need to transform the joblib file to an SQL querable format such as JSON or CSV (out of scope for this workshop).
        - Finally we want to return our dataframe, but create a new column indicating what rows were used for training and those for training.
5. Viewing our output of this model:
  <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/12-machine-learning-training-prediction/1-preview-train-test-position.png" title="Preview which rows of our model were used for training and testing"/>

6. Let’s pop back over to Snowflake and check that our logistic regression model has been stored in our `MODELSTAGE`. Make sure you are in the correct database and development schema to view your stage (this should be `PC_DBT_DB` and your dev schema - for example `dbt_hwatson`):
    ```sql
    list @modelstage
    ```
  <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/12-machine-learning-training-prediction/2-list-snowflake-stage.png" title="List the objects in our Snowflake stage to check for our logistic regression to predict driver position"/>

7. To investigate the commands run as part of `train_model_to_predict_position.py` script, navigate to Snowflake query history to view it **Home button > Activity > Query History**. We can view the portions of query that we wrote such as `create or replace stage MODELSTAGE`, but we also see additional queries that Snowflake uses to interpret python code.
  <Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/12-machine-learning-training-prediction/3-view-snowflake-query-history.png" title="View Snowflake query history to see how python models are run under the hood"/>

Let's use our new trained model to create predictions!

<!-- ------------------------ -->
### Predicting on new data
It's time to use that 2020 data we held out to make predictions on!

1. Create a new file called `apply_prediction_to_position.py` and copy and save the following code:
    ```python
    import logging
    import joblib
    import pandas as pd
    import os
    from snowflake.snowpark import types as T

    DB_STAGE = 'MODELSTAGE'
    version = '1.0'
    # The name of the model file
    model_file_path = 'driver_position_'+version
    model_file_packaged = 'driver_position_'+version+'.joblib'

    # This is a local directory, used for storing the various artifacts locally
    LOCAL_TEMP_DIR = f'/tmp/driver_position'
    DOWNLOAD_DIR = os.path.join(LOCAL_TEMP_DIR, 'download')
    TARGET_MODEL_DIR_PATH = os.path.join(LOCAL_TEMP_DIR, 'ml_model')
    TARGET_LIB_PATH = os.path.join(LOCAL_TEMP_DIR, 'lib')

    # The feature columns that were used during model training
    # and that will be used during prediction
    FEATURE_COLS = [
            "RACE_YEAR"
            ,"CIRCUIT_NAME"
            ,"GRID"
            ,"CONSTRUCTOR_NAME"
            ,"DRIVER"
            ,"DRIVERS_AGE_YEARS"
            ,"DRIVER_CONFIDENCE"
            ,"CONSTRUCTOR_RELAIBLITY"
            ,"TOTAL_PIT_STOPS_PER_RACE"]

    def register_udf_for_prediction(p_predictor ,p_session ,p_dbt):

    # The prediction udf

    def predict_position(p_df: T.PandasDataFrame[int, int, int, int,
                                        int, int, int, int, int]) -> T.PandasSeries[int]:
        # Snowpark currently does not set the column name in the input dataframe
        # The default col names are like 0,1,2,... Hence we need to reset the column
        # names to the features that we initially used for training.
        p_df.columns = [*FEATURE_COLS]
        
        # Perform prediction. this returns an array object
        pred_array = p_predictor.predict(p_df)
        # Convert to series
        df_predicted = pd.Series(pred_array)
        return df_predicted

    # The list of packages that will be used by UDF
    udf_packages = p_dbt.config.get('packages')

    predict_position_udf = p_session.udf.register(
        predict_position
        ,name=f'predict_position'
        ,packages = udf_packages
    )
    return predict_position_udf

    def download_models_and_libs_from_stage(p_session):
    p_session.file.get(f'@{DB_STAGE}/{model_file_path}/{model_file_packaged}', DOWNLOAD_DIR)
    
    def load_model(p_session):
    # Load the model and initialize the predictor
    model_fl_path = os.path.join(DOWNLOAD_DIR, model_file_packaged)
    predictor = joblib.load(model_fl_path)
    return predictor
    
    # -------------------------------
    def model(dbt, session):
    dbt.config(
        packages = ['snowflake-snowpark-python' ,'scipy','scikit-learn' ,'pandas' ,'numpy'],
        materialized = "table",
        tags = "predict"
    )
    session._use_scoped_temp_objects = False
    download_models_and_libs_from_stage(session)
    predictor = load_model(session)
    predict_position_udf = register_udf_for_prediction(predictor, session ,dbt)
    
    # Retrieve the data, and perform the prediction
    hold_out_df = (dbt.ref("hold_out_dataset_for_prediction")
        .select(*FEATURE_COLS)
    )

    # Perform prediction.
    new_predictions_df = hold_out_df.withColumn("position_predicted"
        ,predict_position_udf(*FEATURE_COLS)
    )
    
    return new_predictions_df
    ```
2. Execute the following in the command bar:
    ```bash
    dbt run --select predict_position
    ```
3. **Commit and sync** our changes to keep saving our work as we go using the commit message `logistic regression model training and application` before moving on.
4. At a high level in this script, we are:
    - Retrieving our staged logistic regression model
    - Loading the model in
    - Placing the model within a user defined function (UDF) to call in line predictions on our driver’s position
5. At a more detailed level:
    - Import our libraries.
    - Create variables to reference back to the `MODELSTAGE` we just created and stored our model to.
    - The temporary file paths we created might look intimidating, but all we’re doing here is programmatically using an initial file path and adding to it to create the following directories:
        - LOCAL_TEMP_DIR ➡️ /tmp/driver_position
        - DOWNLOAD_DIR ➡️ /tmp/driver_position/download
        - TARGET_MODEL_DIR_PATH ➡️ /tmp/driver_position/ml_model
        - TARGET_LIB_PATH ➡️ /tmp/driver_position/lib
    - Provide a list of our feature columns that we used for model training and will now be used on new data for prediction.
    - Next, we are creating our main function `register_udf_for_prediction(p_predictor ,p_session ,p_dbt):`. This function is used to register a user-defined function (UDF) that performs the machine learning prediction. It takes three parameters: `p_predictor` is an instance of the machine learning model, `p_session` is an instance of the Snowflake session, and `p_dbt` is an instance of the dbt library. The function creates a UDF named `predict_position` which takes a pandas dataframe with the input features and returns a pandas series with the predictions.
    - ⚠️ Pay close attention to the whitespace here. We are using a function within a function for this script.
    - We have 2 simple functions that are programmatically retrieving our file paths to first get our stored model out of our `MODELSTAGE` and downloaded into the session `download_models_and_libs_from_stage` and then to load the contents of our model in (parameters) in `load_model` to use for prediction.
    - Take the model we loaded in and call it `predictor` and wrap it in a UDF.
    - Return our dataframe with both the features used to predict and the new label.

🧠 Another way to read this script is from the bottom up. This can help us progressively see what is going into our final dbt model and work backwards to see how the other functions are being referenced.

6. Let’s take a look at our predicted position alongside our feature variables. Open a new scratchpad and use the following query. I chose to order by the prediction of who would obtain a podium position:
    ```sql
    select * from {{ ref('apply_prediction_to_position') }} order by position_predicted
    ```
7. We can see that we created predictions in our final dataset, we are ready to move on to deployment!

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: sample 
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-science 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Science, Twitter 
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Daniel Myers 
  - Indicate the author(s) of this specific sfguide.

---

You can see the source metadata for this guide you are reading now, on [the github repo](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md).


<!-- ------------------------ -->
## Creating a Step
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->
## Code Snippets, Info Boxes, and Tables
Duration: 2

Look at the [markdown source for this sfguide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

### Info Boxes
> aside positive
> 
>  This will appear in a positive info box.


> aside negative
> 
>  This will appear in a negative info box.

### Buttons
<button>

  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

<!-- ------------------------ -->
## Images, Videos, and Surveys, and iFrames
Duration: 2

Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
![Puppy](assets/SAMPLE.jpg)

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### Embed an iframe
![https://codepen.io/MarioD/embed/Prgeja](https://en.wikipedia.org/wiki/File:Example.jpg "Try Me Publisher")

<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files
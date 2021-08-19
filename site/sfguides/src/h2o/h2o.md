author: miles.adkins@snowflake.com
id: automl_with_snowflake_and_h2o
summary: This lab will walk you through how to use Snowflake and H2O to perform supervised machine learning.
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: H2O, AutoML, Partner Connect, Databases, Tables, Stages, File Formats

# AutoML with Snowflake and H2O Driverless AI

<!-- ------------------------ -->
# AutoML with Snowflake and H2O Driverless AI
Duration: 5
## Use Case Overview

H2O Driverless AI is a supervised machine learning platform leveraging the concept of automated machine learning. Supervised machine learning is a method that takes historic data where the response or **target** is known and build relationships between the input variables and the target variable. Driverless AI automates most of difficult supervised machine learning workflow such as feature engineering, model validation, model tuning, model selection, and model deployment. Modeling pipelines, which are produced from H2O Driverless AI, can exported as standalone scoring artifacts to power your AI/ML use case.

This tutorial presents a quick introduction to the Driverless AI platform via Snowflake Partner Connect.

We will use a dataset from LendingClub.com to build a classification model to help us predict the likelihood a LendingClub.com borrower will default on their loan. LendingClub.com is an established online loan marketplace that funds personal loans, commercial loans, funding of medical procedures, and other financing needs. The data consist of 25 columns and approximately 39,000 rows, with each row corresponding to a customer. Here is preview of the data:

![](assets/00_intro_01.png)

![](assets/00_intro_02.png)

Note that the dataset consist of numerical columns (`loan_amount`, `installment`, `emp_length`, `dti`, etc.), categorical columns (`term`, `home_ownership`, `verification_status`, `purpose`, etc.), and a text column (`desc`). Our target variable is `bad_loan` which is a Boolean with values `True` and `False`, thus this will be a binary classification problem.

We will use Snowflake and Driverless AI to:

- **Import** the data from Snowflake
- **Explore** the data using summary descriptive statistics and automated visualizations (AutoViz)
- **Build** a predictive model using an evolutionary algorithm for automatic feature engineering and model optimization
- **Measure** the model through diagnostics
- **Understand** the model through MLI (machine learning interpretability)
- **Deploy** the model into production in a Snowflake system

### Prerequisites

* A [Snowflake](https://signup.snowflake.com/) Account deployed in AWS (if you are using an enterprise account through your organization, it is unlikely that you will have the privileges to use the `ACCOUNTADMIN` role, which is required for this lab).
* A [H2O](https://www.h2o.ai/try-driverless-ai/) Account
* [SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html) installed (Snowflake's CLI tool)
* Past experience running and executing queries in Snowflake
* A basic understanding of data science and machine learning concepts.

### What You'll Learn

* How to use Snowflake's "Partner Connect" to create a Driverless AI instance
* How to use Driverless AI to build a supervised learning classification model.
* How to deploy the finished model pipeline as a Snowflake Java UDF.

<!-- ------------------------ -->
## Setting up Snowflake
Duration: 5

The first thing you will need to do is download the following .sql file that contains a series of SQL commands we will execute throughout this lab.

<button>
  [Download .sql File](https://snowflake-workshop-lab.s3.amazonaws.com/h2o/Snowflake_H2o_VHOL_guides.sql)
</button>

At this point, log into your Snowflake account and have a clear screen to start working with. If you have just created a free trial account, feel free to minimize or close any hint boxes that are looking to help guide you. These will not be needed for this lab as most of the hints will be covered throughout the remainder of this exercise.

![](assets/p5.png)

To ingest our script in the Snowflake UI, navigate to the ellipsis button on the top right hand side of a “New Worksheet” and load our script.

![](assets/p2.png)

Snowflake provides "worksheets" as the spot for you to execute your code. This lab assumes you have already run a few queries in Snowflake before. Therefore, we are going to execute a series of commands quickly, so we get the data in tables and continue to the more interesting part of the lab of building and deploying models. The .sql file that you upload should look like this:

```sql
USE ROLE sysadmin;

CREATE OR REPLACE DATABASE lendingclub;

CREATE OR REPLACE WAREHOUSE demo_wh
  WITH WAREHOUSE_SIZE = 'XSMALL';

USE DATABASE h2o_vhol;
USE SCHEMA public;
USE WAREHOUSE compute_wh;

CREATE OR REPLACE TABLE loans (
    id INTEGER,
    loan_amnt INTEGER,
    term String(1024),
    installment Real,
    grade String(1024)
    ...)

...
```

To execute the entire .sql code, which contains 11 different statements, all we need to do is click on the "All Queries" button next to blue "run" button at the top left of the worksheet and then press "run". You should see the "run" button has a "(11)", meaning it will execute all 11 commands in the uploaded file.

<!-- ------------------------ -->
## Launching Driverless AI
Duration: 5

Snowflake's Partner Connect feature allows you to seamlessly get started with partner tools and manages most of the connection details for you to get up and running as quickly as possible.

![](assets/p20.png)

Go ahead and click on the "Partner Connect" application. This should take you to the following screen where you will see many of the Snowflake partners, and through a simple method of setting up an account and integration, allow you to quickly move data into a partner tool. You should see H2O near the bottom.

![](assets/p21.png)

To be able to continue test out partner applications, in our case H2O, we need to promote ourselves to the `ACCOUNTADMIN` role. This is an out of worksheet process, and therefore isn't a command for us to run. We need to do this one manually.

![](assets/p22.png)

Once you have completed this step, go ahead and click on the H2O application. This will present you with a screen to connect to H2O. It will outline a number of Snowflake objects that will be auto-created. For the purposes of this lab, we have already created the snowflake objects that we will need, so you can press "Connect" .

![](assets/p23.png)

You then will be prompted to activate your account now, press the blue "activate" button to do so.

![](assets/p24.png)

![](images/01_startup_01.png)

This creates a partner account which you can immediately `Activate`

![](images/01_startup_02.png)

You next need to accept the H2O Terms and Conditions for the Trial Agreement

![](images/01_startup_03.png)

and wait while your H2O Driverless AI instance is configured and launched.

![](images/01_startup_04.png)

### Driverless AI Interface

Your brand new Driverless AI instance looks like

![](images/01_intro_0.png)

A summary of the information and views we will cover in this tutorial include:

1. H2O.ai information: This displays the version (Driverless AI 1.9.0.2), the license owner and status, and the current user (H2OAI).
2. `DATASETS`: A view for importing, listing, and operating on datasets.
3. `AUTOVIZ`: The Automatic Visualizations of data view.
4. `EXPERIMENTS`: The view where we build and deploy predictive models.
5. `DIAGNOSTICS`: Model diagnostics view.
6. `MLI`: Machine learning interpretability view, information to help us understand our models.
7. `RESOURCES`: A pull-down menu for accessing system information, clients, help, and other resources.

<!-- ------------------------ -->
## Import Data from Snowflake
Duration: 5

From the empty Datasets view, click the `Add Dataset` button and select the `SNOWFLAKE` connector:

![](images/02_data_1.png)

This launches the `Make Snowflake Query` form.

![](assets/02_import_2.png)

Enter into the form:

* **Database** `Lendingclub`,
* **Warehouse** as `demo_wh`,
* **Schema** as `public`,
* **Name** as `loans.csv`,
* **Username** and **Password** with the credentials you used at signup,
* **File Formatting Parameters** as `FIELD_OPTIONALLY_ENCLOSED_BY="'"`,
* **SQL Query** `select * from loans`.

Then click the `CLICK TO MAKE QUERY` button. This imports the data into the Driverless AI system.

![](images/02_import_5.png)

The dataset is now available for next steps in Driverless AI

![](images/02_import_3.png)

<!-- ------------------------ -->
## Dataset Details
Duration: 10

Right click the `loans` dataset to get details.

![](images/03_details_0.png)

The `Dataset Details` view is a quick way to inspect the dataset columns, see their storage type (integer, string, etc.), get summary statistics and distribution plots for each column.

![](images/03_details_1.png)

In more advanced usage, you can edit the data type interactively

![](images/03_details_4.png)

Scrolling to the right, inspect the `bad_loans` column, our target variable.

![](images/03_details_2.png)

The target `bad_loans` is Boolean with 38,980 observations and has a mean value of 0.1592. This means that 15.92% of the customers (rows) in this dataset have a loan that was not paid off.

Clicking the `DATASET ROWS` button on the upper right yields a spreadsheet format.

![](images/03_details_3.png)

This is helpful in understanding the layout of the data. A quick inspection of your dataset using `Details` is a good practice that we always recommended.

<!-- ------------------------ -->
## Visualizing Datasets
Duration: 10

`Autoviz` in Driverless AI automatically creates a variety of informative interactive graphs that are designed for understanding the data to be used in building a predictive model. `Autoviz` is unique in that it only shows the graphs that are applicable for your data based on the information in your data.

Right click the dataset name and select `VISUALIZE` to launch AutoViz

![](images/04_autoviz_00.png)

The available visualizations for the `loans` data are shown below.

![](images/04_autoviz_02.png)

Selecting the `SKEWED HISTOGRAMS` section, for example, yields a series of histograms on only the columns that are sufficiently skewed. We show one below for the `credit_length` column.

![](images/04_autoviz_03.png)

Clicking the left and right navigation arrows allows you to inspect additional variables, ordered by their skewness.

Close the `SKEWED HISTOGRAMS` display and scroll down to see `RECOMMENDATIONS`.

![](images/04_autoviz_01.png)

Selecting `RECOMMENDATIONS` produces

![](images/04_autoviz_05.png)

The philosophy underlying automatic visualizations is to make it easy for the data scientist to quickly understand their data fields, but it does not make decisions for the data scientist.

There are a number of additional useful graphs that can be navigated to fully understand your data prior to modeling.

<!-- ------------------------ -->
## Split Data
Duration: 10

Splitting data into train and test sets allows models to be built with the train set and evaluated on the test data. This protects against overfit and yields more accurate error estimates. To use the Dataset Splitter utility, right click the dataset and select `SPLIT`

![](images/05_split_01.png)

Name your `train` and `test` splits, then select a split ratio (here we use 0.8).

![](images/05_split_02.png)
For a time series use case, enter the time column. If your data have predefined folds for k-fold cross validation, enter the fold column. A seed is available for reproducibility. Select the target column `bad_loan`

![](images/05_split_03.png)

The data type of the target column determines the splitting algorithm. For classification problems, stratefied random sampling is used. For numeric target columns, simple random sampling is used.

Click `SAVE` to create the datasets.

![](images/05_split_04.png)

The `train` dataset has around 31,000 rows and the `test` dataset around 8000 rows.

<!-- ------------------------ -->
## Experiment
Duration: 15

We use the term _Experiment_ in Driverless AI to refer to the entire feature engineering and model evolution process. Instead of fitting one model, we are fitting many and using a "survival of the fittest" approach to optimize features and model hyperparameters. The result is a combination feature engineering-modeling _pipeline_, which can easily be investigated and promoted into production.

### Set up an Experiment

We start an experiment from the `Datasets` view by clicking on the line corresponding to the `train` dataset and selecting `PREDICT` from the dropdown menu

![](images/06_intro_1.png)

This opens the following form for configuring an experiment.

![](images/06_setup_01.png)

The fields are

1. (Optional) Name your experiment. This is especially helpful for leaderboards in `Projects`.
2. The prefilled training dataset.
3. (Optional) Select columns to drop from modeling.
4. (Optional) Select a validation dataset. Setting this option will enforce a train-validate split throughout the experiment.
5. (Recommended) Select the test dataset. You should **always** have a holdout test dataset to evaluate your model!
6. Select the target column. This option is flashing so you will not miss it.
7. (Optional) Select a column containing fold numbers. This is used where folds for k-fold cross validation have already been defined.
8. (Optional) Select weight column.
9. (Optional) Select a time column. This switches Driverless AI into a time-series mode, where specialized data, feature engineering, and model settings are enabled.

For our experiment, enter "Baseline" as the display name (#1). Next select the `TEST DATASET` file `test` (#5). The `desc` column contains a written explanation from the customer describing the reason for requesting a loan. Although Driverless AI has extensive NLP (natural language processing) capabilities, we omit them in this baseline model. Thus using `DROPPED COLUMNS` (#3), select `desc`:

![](images/06_setup_30.png)

Next select `bad_loan` as the `TARGET COLUMN` (#6). You will have to scroll down, since `bad_loan` is the next-to-last variable in the dataset

![](images/06_setup_31.png)

After selecting the target variable, Driverless AI analyzes the data and experimental settings and prefills additional options:  

![](images/06_setup_32.png)

These include

1. Target variable status
2. The `ACCURACY/TIME/INTERPRETABILITY` dials which range from 1 to 10 and largely determine the recipe for the experiment.
3. The `CLASSIFICATION/REPRODUCIBLE/GPUS DISABLED` clickable buttons.
4. The `SCORER` used in model building and evaluation.
5. `EXPERT SETTINGS` for fine control over a vast number of system, model, feature, recipe, and specialty options.  
6. A detailed settings description.
7. `LAUNCH EXPERIMENT` to run the experiment defined by dial settings, scorer, and expert settings.

For our experiment,

* The target variable is `bool` (Boolean) with 31,184 observations, 4963 of which are equal to 1 (#1). The `CLASSIFICATION` button (#3) is enabled by default because the target is Boolean.
* The `ACCURACY` dial is set to 5. Higher values of accuracy are more computationally intensive. The description under (#6) shows that `ACCURACY` impacts how features are evaluated (model & validation strategy) and what form the final pipeline will take (individual models vs. ensembles and validation strategy).
* The `TIME` dial is set to 4. Higher values of `TIME` allow for longer feature evolution. `TIME` levels also include early stopping rules for efficiency.
* Note: Higher values of `ACCURACY` and `TIME` do not always lead to better predictive models. Model performance should always be evaluated using a holdout test data set.
* The `INTERPRETABILITY` dial ranges from 1 (least interpretable = most complex) to 10 (most interpretable = least complex). `INTERPRETABILITY` set to 7 or higher enable monotonicity constraints, which significantly increases model understanding.


Click on the `REPRODUCIBLE` button to enable reproducibility. This may be important for regulatory reasons or, as in our case, for educational purposes. Also select AUC as the scorer (#4)

![](images/06_setup_04.png)

Clicking on `EXPERT SETTINGS` (#5) exposes an immense array of options and settings

![](images/06_setup_06.png)

This gives the expert data scientist complete control over the Driverless AI experience, including the ability to customize models, feature transformers, scorers, and data using `CUSTOM RECIPES`. Select `CANCEL` to exit out of the expert settings screen.

### Run Experiment

Before launching the experiment, your settings should look like the following.

![](images/06_run_10.png)

Click `LAUNCH EXPERIMENT` to commence.
The Driverless AI UI now includes a descriptive rotating dial in the center with live monitoring displays for model evolution, variable importance, resource usage, and model evaluation.

![](images/06_run_11.png)

To get more detailed resource monitoring, go to `RESOURCES` in the menu and select `SYSTEM INFO`.

![](images/06_run_12.png)

The `System Info` view shows hardware usage and live activity monitoring of individual CPU cores.

![](images/06_run_13.png)

Clicking `CLOSE` sends us back to the running `Experiment Baseline` view.

![](images/06_run_14.png)

Note that

1. The central dial shows 7% completion after 1:06 with 9/56 planned iterations completed.
2. The CPU and memory usage monitor is a simplified version of the `System Info` view we just closed.
3. Each dot in the `ITERATION` monitor corresponds to an individual model. The last model evaluated is a LightGBM model with 21 features and an AUC of 0.7316. Moving your mouse over any of the model dots will highlight that model and summary information.
4. The `VARIABLE IMPORTANCE` display shows the features of the latest model (or the model selected in the `ITERATION DATA` display) and their relative importance.
5. By default, the ROC curve for the selected model and AUC are displayed, but other displays are available: P-R (Precision Recall), Lift, Gains, and K-S (Kolmogorov-Smirnov).

#### Notifications

Selecting `Notifications` in the `CPU/MEMORY` section (2) opens important information and discoveries from Driverless AI.

![](images/06_run_16.png)

Ours reports that

* Reproducible mode was enabled, along with its implications.
* Imbalanced data was detected but imbalanced settings were not enabled. Notifications then indicates the expert settings required to account for imbalance in the data.
* An ID column was identified and automatically dropped from data.
* Additional information on scoring during feature and model tuning.

Notification are important to read and understand. The advice in notifications often leads to better models.

#### Technical logs

The technical data scientist might consider selecting `Log` in the `CPU/MEMORY` section. Driverless AI logs its entire process in great detail. Clicking `Log` opens a system logging window for monitoring live. Logs can be downloaded during or after the experiment.

![](images/06_run_15.png)

Nearing the conclusion of the experiment

![](images/06_run_20.png)

we see that the dial is at 100% complete, the elapsed time is approximately 6:30 (while results are reproducible, times are not themselves exactly reproducible), and the experiment is stopping early, needing only 33 of 56 iterations.

### Completed Experiment

Upon completion, the `Experiment Baseline` view replaces the spinning dial in the center with a stack of clickable bars

![](images/06_complete_01.png)

#### Summary

The lower right panel includes an experiment summary, zoomed in below:

![](images/06_complete_00.png)

The summary contains information about the experiment settings, its seed, the train, validation, and test data, system (hardware) specifications, features created, models created, timing, and scores. In particular, note that

* 230 features were created but only 28 were used,
* feature evolution used 35 models,
* feature tuning used 16 models,
* final pipeline training used an additional 8 models.

Importantly, the MOJO latency timing of 0.13 milliseconds indicates the speed of scoring this model in production.

#### Model Performance

Selecting ROC in the lower right replaces the summary with the ROC curve.

![](images/06_complete_02.png)

You can toggle between `VALIDATION METRICS` and `TEST SET METRICS` for this display.

![](images/06_complete_03.png)

Selecting any point along the curve produces a confusion matrix with additional peformance metrics

![](images/06_complete_04.png)

You can view other model performance metrics, including Precision-Recall

![](images/06_complete_05.png)

Lift chart

![](images/06_complete_06.png)

Gains chart

![](images/06_complete_07.png)

and Kolmogorov-Smirnov

![](images/06_complete_08.png)

<!-- ------------------------ -->
## Experiment Inspection
Duration: 10

Once an experiment is completed, it is important to understand the final model's predictive performance, its features, parameters, and how the features and model combine to make a pipeline.

### Diagnostics

The `DIAGNOSE MODEL ON NEW DATASET ...` button is used to create extensive diagnostics for a model built in Driverless AI. After clicking the button,

![](images/07_diagnostics_0.png)

select the dataset used for diagnostics, we will use the `test` dataset.

![](images/07_diagnostics_7.png)

The `Diagnostics` view that is returned is very complete. You can choose from a plethora of `Scores` on the left. And each of the `Metric Plots` on the right is interactive.

![](images/07_diagnostics_2.png)

Selecting the confusion matrix plot yields

![](images/07_diagnostics_3.png)

Likewise, the interactive ROC curve produces

![](images/07_diagnostics_4.png)

### AutoReport

By default, an automated report is created for each experiment that is run. Download the `AutoReport` by

![](images/07_autodoc_0.png)

The document that is created is a very thorough summary of the experiment in the form of a white paper, documenting in detail the data, settings, and methodologies used to create the final pipeline.

![](images/07_autodoc_1.png)

This includes detailed information on the features that were engineered and the process for engineering them.

![](images/07_autodoc_2.png)

It also contains validation and test metrics and plots.

![](images/07_autodoc_3.png)

For this particular experiment, the AutoReport is a 36-page technically detailed document.

### Pipeline Visualization

Selecting the `VISUALIZE SCORING PIPELINE` button

![](images/07_pipeline_1.png)

returns a visual representation of the pipeline

![](images/07_pipeline_2.png)

This pipeline is also available in the AutoReport, along with explanatory notes copied below. The pipeline consists of

* 28 total features, both original and engineered.
* Two LightGBM models created with 4-fold cross validation each.
* A stacked ensemble blending the two LightGBM models.
* The outputs are probabilities for `bad_loan = False` and `bad_loan = True`.

<!-- ------------------------ -->
## Model Interpretability
Duration: 10

One of Driverless AI's most important features is the implementation of a host of cutting-edge techniques and methodologies for interpreting and explaining the results of black-box models. In this tutorial, we just highlight some of the MLI features available in Driverless AI without discussing their theoretical underpinnings.


To launch MLI from a completed experiment, select the `INTERPRET THIS MODEL` button

![](images/08_mli_00.png)

The MLI view allows easy navigation through the various interactive plots.

![](images/08_mli_01.png)

### Dashboard

The `Dashboard` view displays four useful summary plots

![](images/08_mli_02.png)

1. A K-LIME (Local Interpretable Model-agnostic Explanations) surrogate model.
2. A Decision Tree surrogate model.
3. A feature importance plot.
4. A PDP (Partial Dependence Plot).

Each of these plots are available in a larger format from the main MLI view.

### Feature Importance

Other plots include Feature importance on the transformed features

![](images/08_mli_04.png)

and on the original features

![](images/08_mli_05.png)

### Shapley

Shapley values are also available for the transformed and original features

![](images/08_mli_06.png)

### Additional Capabilities

The MLI view provides tools for disparate impact analysis and sensitivity analysis, also called "What If" analysis.

![](images/08_mli_01.png)

<!-- ------------------------ -->
## Deploy the model using Java UDFs
Duration: 5

### Introduction

The final model from a Driverless AI experiment can be exported as either a **MOJO scoring pipeline** or a **Python scoring pipeline**. The MOJO scoring pipeline comes with a `pipeline.mojo` file that can be deployed in any environment that supports Java or C++. There are a myriad of different deployment scenarios for Real-time, Batch or Stream scoring with the `pipeline.mojo` file. In this tutorial, we deploy the final model as a Snowflake Java UDF.  

### Gather Driverless AI artifacts

We need to collect the following components from Driverless AI:

- `pipeline.mojo`
- `mojo2-runtime.jar`
- `H2oDaiScore.jar`
- A valid Driverless AI license file. `license.sig`

The first two files we will download from Driverless AI directly. Select `DOWNLOAD MOJO SCORING PIPELINE` from the `STATUS: COMPLETE` buttons

![](images/09_deploy_01.png)

and then `DOWNLOAD MOJO SCORING PIPELINE` again from the `MOJO Scoring Pipeline instructions` screen

![](images/09_deploy_02.png)

This downloads a file `mojo.zip` which contains the `pipeline.mojo` and `mojo2-runtime.jar` files, along with a number of other files we will not be needing.

The next file, `H2oDaiScore`, is a custom scorer developed by H2O.ai to deploy MOJOs using Snowflake Java UDFs. It can be downloaded from H2O here: [https://s3.amazonaws.com/artifacts.h2o.ai/releases/ai/h2o/dai-snowflake-integration/java-udf/download/index.html](https://s3.amazonaws.com/artifacts.h2o.ai/releases/ai/h2o/dai-snowflake-integration/java-udf/download/index.html). Select the latest release (0.0.3 at the time of this writing). Extract the downloaded `H2oScore-0.0.3.tgz` file to find `H2oDaiScore-0.0.3.jar`.

Last, you will need your Driverless AI license file `license.sig`.

### Setup Snowflake

The first step in creating a Java UDF in Snowflake is to put the 4 Driverless AI artifacts into the table stage, which was created when we created `loans` table and uploaded some data in the very beginning.

In order to do that, we will need to leverage [SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html) (Snowflake's CLI tool), which will need to be installed locally so you can put the artifacts on your local compute into the table stage in your Snowflake Cloud.

Travel to your command line and enter the follow:

```
snowsql
```
You will be asked for your `Account`:

This is a part of the unique URL you were given when creating a trial. Here is how the URL is defined (<Account>.snowflakecomputing.com). Enter only the Account portion.

Next enter your `User`:
and `Password`:

These are the login name  and password you created after navigating to the unique URL of your Snowflake deployment.

Once logged in, you can now execute the following:
```
USE DATABASE lendingclub;
USE SCHEMA public;
USE WAREHOUSE demo_wh;
USE ROLE sysadmin;
```

Finally, we can now upload the 4 artifacts:

```
put file://{path}/pipeline.mojo @%loans auto_compress=false;
put file://{path}/license.sig @%loans auto_compress=false;
put file://{path}/H2oDaiScore-0.0.3.jar @%loans auto_compress=false;
put file://{path}/mojo2-runtime.jar @%loans auto_compress=false;
```

Note, you will need to change where it says `path` in the 'put' commands to path where the files you downloaded are located. This will take 1-2 mins to upload.

### Create a Java UDF in Snowflake

We are now ready to actually create the Java UDF via the `CREATE FUNCTION` statement. To do so, you must provide:

- a name for the function and its parameters,
- the location in the stage of `pipeline.mojo` and all other artifacts,
- the Java method to be invoked when the Java UDF is called.

The code has been prepared for you. At this point, this can either be run in SnowSQL or back in your GUI session.

``` sql
CREATE FUNCTION H2OScore_Java(params STRING, rowData ARRAY)

    returns variant language java

    imports = ('@%loans/pipeline.mojo',
               '@%loans/license.sig',
               '@%loans/mojo2-runtime.jar',
               '@%loans/H2oDaiScore-0.0.3.jar'
               )

    handler = 'H2oDaiScore.h2oDaiScore';
```


### Make predictions using the Java UDF

The syntax for calling a Java UDF in Snowflake is

``` sql
SELECT <JAVA_UDF_FUNCTION_NAME>(<JAVA_UDF_FUNCTION_PARAMS>) FROM <TABLE_NAME>;
```

Using the `H2OScore_Java` UDF defined above, we will now score our table `loans` using `pipeline.mojo` as follows:

``` sql
SELECT
    ID,
    H2OScore_Java(
        'Modelname=pipeline.mojo',
        ARRAY_CONSTRUCT(loan_amnt, term, installment, grade, sub_grade, emp_length,
                        home_ownership, annual_inc, verification_status, issue_d,
                        purpose, addr_state, dti, inq_last_6mths, open_acc,
                        revol_util, total_acc, credit_length)
    ) AS H2OScore
FROM loans;
```

It should take about 7 seconds to score and the results should look like this:

**Results Preview** (first 3 rows)

| Row      | ID | H2OScore |
| ----------- | ----------- | ----------- |
| 1      | 1077501       |0.8469023406505585
| 2   | 1077430        |0.5798575133085251
| 3   | 1077175        |0.5994115248322487

And as they say, that is all folks! We have now scored a model inside Snowflake. What this does is gives you the flexibility of Snowflake's Scale Up and Scale Out capabilities to score as much data as you want.

### (Extra) Easy Deployment using AutoGen

A Snowflake Worksheet template to deploy and score DAI MOJOs using Java UDFs can be automatically generated using the H2O REST Server deployment:

``` sh
curl "<ip>:<port>/autogen?name=<model_name>&notebook=snowflake.udf"
```

For example,

```sh
curl "http://127.0.0.1:8080/autogen?name=pipeline.mojo&notebook=snowflake.udf"
```

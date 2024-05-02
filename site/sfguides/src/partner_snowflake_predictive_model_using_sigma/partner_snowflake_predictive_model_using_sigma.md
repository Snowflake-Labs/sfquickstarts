author: Fran Britschgi
id: partner_snowflake_predictive_model_using_sigma
summary: Building predictive modeling in Snowflake and Sigma
categories: data-science-&-ml,solution-examples, partner-Integrations, connectors
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Predictive Modeling, Machine Learning, BI
lastUpdated: 2024-04-18

# Develop a Predictive Model using Snowflake and Sigma
<!-- Copy of Sigma hosted version, with customized prerequisites based on Snowflake's needs -->

## Overview 
Duration: 1 

This QuickStart will guide you through an end-to-end example of utilizing Snowflake's new machine learning features. 

Our focus will be on creating a machine learning-driven price prediction tool, integrating the perspectives of both a business analyst and a data scientist using Snowflake and Sigma.

We will demonstrate how Sigma enables the execution of complex commands in Snowflake, and displays results in a format similar to a spreadsheet interface. 

This approach not only maintains data security within Snowflake, but also broadens accessibility to users without SQL expertise.

In our example, we'll analyze historic food truck sales data. We aim to develop a model identifying key drivers of high sales in the past and explore how a business analyst can leverage this model for informed decision-making. The analyst will be able to collaborate with the data scientist all from a sigma workbook.

### Target Audience
Anyone who is interested in learning how to easily leverage the power of Snowflakes machine learning features, by using Sigma.

### What You Will Learn

- How to explore and build a dataset for training a model
- How to build a machine learning model using Snowpark ML
- How to register a model in the Snowpark Model Registry
- How to expose the model to business users in Sigma

### Prerequisites
Thanks for signing up for Snowflake & Sigma’s Hands-On Lab, “Develop a Predictive Model Using Snowflake and Sigma”.

To ensure that you can follow along during the lab, please complete the work outlined on the following two pages prior to the start of the lab. 

## Snowflake Prerequisites 
Duration: 5

#### 1: Sign up for a Snowflake Trial:
You can sign up for a 30-day free trial of Snowflake [here.](https://signup.snowflake.com/) Even if you have a login on an existing Snowflake account, you should still create a new Snowflake account, as you’ll be asked to utilize the `ACCOUNTADMIN` role for some steps below.


#### 2: Enable Anaconda Packages in Snowflake:
Follow the directions [here](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages#getting-started) to accept Snowflake’s Third Party Terms. You will need to be an `ACCOUNTADMIN` role in order to complete this step. To select (or change) the current role for a session in Snowsight, click the user context dropdown in the upper-left corner of Snowsight, hover over to `Switch Role` and choose `ACCOUNTADMIN.`



#### 3: Install Python:
If you do not have Python installed on your machine, install Python [here.](https://www.python.org/downloads/) 

<aside class="negative">
<strong>NOTE:</strong><br>Snowpark requires a Python version less than 3.12 and greater than 3.8. 
</aside>

To confirm your installation from a terminal, you can run:

```code
python3 --version
```

You should see the version of Python you chose to install.

#### 4: Install Snowpark ML:
From a terminal, run:

```code
pip3 install snowflake-ml-python
```

This command will install all relevant packages for his lab. 

To confirm your installation from a terminal, you can run:

```code
python3 -c 'from snowflake.ml`.modeling.pipeline import Pipeline
```
You should see no errors. 

For more information on installing Snowpark ML, reference [here.](https://docs.snowflake.com/en/developer-guide/snowpark-ml/index#installing-snowpark-ml)

Alternatively, if you are using Anaconda, you can [download this YAML file](https://sigma-quickstarts-main.s3.us-west-1.amazonaws.com/csv/conda_env.yml) for a conda environment, and install the conda environment from your terminal with the command:

```code
conda env create -f /path/to/conda_env.yml
```

If you are using VSCode and the Jupyter extension for VSCode (see step 9), using Anaconda will be your preferred installation method.

#### 5: Install Jupyter:
From a terminal, run:

```code
pip3 install jupyter 
```

To confirm your installation from a terminal, you can run:

```code
jupyter --version
```

You should see an output similar to the following:

```code
    IPython          : 8.18.1
    ipykernel        : 6.27.1
    ipywidgets       : 8.1.1
    jupyter_client   : 8.6.0
    jupyter_core     : 5.5.0
    jupyter_server   : 2.12.1
    jupyterlab       : 4.0.9
    nbclient         : 0.9.0
    nbconvert        : 7.12.0
    nbformat         : 5.9.2
    notebook         : 7.0.6
    qtconsole        : 5.5.1
    traitlets        : 5.14.0
```

#### 6: Install VSCode (optional):
While you can use any IDE of your choice, for this lab we will be training our model in a Jupyter Notebook within VSCode. You can install VSCode [here](https://code.visualstudio.com/download), and can follow [these instructions](https://code.visualstudio.com/docs/datascience/jupyter-notebooks) to make sure you can open your own Jupyter Notebook in VScode. 

A good way to test this is to run the following imports in a notebook cell and make sure there are no errors:

```code
from snowflake.snowpark import Session
from snowflake.ml.registry import Registry
from snowflake.ml.modeling.linear_model import LinearRegression
```

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Sigma Prerequisites 
Duration: 3

#### 1: Sign Up for a Sigma Trial:
From Snowflake, in Snowsight, navigate to `Admin` > `Partner Connect`, then search for `Sigma` and follow the instructions to sign up for a free trial. 

When signing up for a Sigma trial via Partner Connect, relevant Snowflake objects, such as a database (PC_SIGMA_DB), a compute warehouse (PC_SIGMA_WH), a role (PC_SIGMA_ROLE), and a user (PC_SIGMA_USER) for working with Snowflake data in Sigma. 

Furthermore, Partner Connect will automatically create a Snowflake connection for you in Sigma. (Snowflake PC_SIGMA_WH).

If you already have a Sigma account (or [created a Sigma trial manually](https://www.sigmacomputing.com/free-trial)), and did not use Partner Connect to create these Snowflake objects, you can run the following commands in a [Snowsight Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-in-sf-web-interface):

```code
USE ROLE SYSADMIN;
CREATE DATABASE PC_SIGMA_DB;
CREATE WAREHOUSE PC_SIGMA_WH
    WAREHOUSE_SIZE='XSMALL'
    INITIALLY_SUSPENDED=TRUE
    AUTO_SUSPEND=120;

USE ROLE SECURITYADMIN;
CREATE ROLE PC_SIGMA_ROLE;
GRANT ALL ON DATABASE PC_SIGMA_DB TO ROLE PC_SIGMA_ROLE;
GRANT USAGE ON WAREHOUSE PC_SIGMA_WH TO ROLE PC_SIGMA_ROLE;

GRANT ROLE PC_SIGMA_ROLE TO ROLE SYSADMIN;
GRANT ROLE PC_SIGMA_ROLE TO USER <your-snowflake-user>;
```

#### 2: Create Sigma Writeback DB
Per Sigma best practices, create a dedicated database for writeback functionality. To create this writeback database, you can run the following commands in a [Snowsight Worksheet:](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-in-sf-web-interface)

```code
USE ROLE SYSADMIN;
CREATE DATABASE SIGMA_INTERNAL;
CREATE SCHEMA SIGMA_INTERNAL.WRITEBACK;

USE ROLE SECURITYADMIN;
GRANT ALL ON DATABASE SIGMA_INTERNAL TO ROLE PC_SIGMA_ROLE;
GRANT ALL ON SCHEMA SIGMA_INTERNAL.WRITEBACK TO ROLE PC_SIGMA_ROLE;
```

#### 3: Configure Sigma Connection:
Follow [these instructions](https://help.sigmacomputing.com/hc/en-us/articles/360037430473-Set-up-write-access#h_01FDX02PCDXMKNB4D4139W2KEY) to set the Write DB and Write Schema in your Sigma connection. 

If you set up Sigma via Partner Connect, the connection you will be editing is `Snowflake PC_SIGMA_WH`. 

If you did not set up Sigma via Partner Connect, [follow these instructions](https://help.sigmacomputing.com/hc/en-us/articles/360037429913-Connect-to-Snowflake#h_01EN10KHTFJ9A3S46B5W5NX5M9) for creating a Snowflake connection in Sigma. 

<aside class="negative">
<strong>NOTE:</strong><br> You may not know your Sigma user (PC_SIGMA_USER) password, as via Partner Connect it is generated automatically. 
</aside>

To update your PC_SIGMA_USER password, you can run the following: 

```code
USE ROLE ACCOUNTADMIN;
ALTER USER PC_SIGMA_USER SET PASSWORD='<assign-password-here>';
```

## Setup
Duration: 20

We're starting from scratch with a blank Sigma workbook. I'll first load our sales data from Snowflake. 

If you have sales data in Snowflake, we can directly connect to it from Sigma.  

In this case, we don’t have that data in Snowflake, so we’ll need to upload it. Fortunately, that’s easy to do in Sigma. 

Let's upload a CSV file of shift sales from the city of Seattle.

<button>[Download required CSV file](https://sigma-quickstarts-main.s3.us-west-1.amazonaws.com/csv/SHIFT_SALES.csv)</button>

Log into Sigma.

From the Sigma home page, click the `Create New` button in the top left corner and select `Workbook.`:

<img src="assets/ml1.png" width="800"/>

Now that you are in the Workbook, let's start by saving it with the name `ML Shift Sales` by clicking `Save As` in the top right. 

<img src="assets/ml2.png" width="600"/>

Add a `new table`:

<img src="assets/ml3.png" width="800"/>

Select `Upload CSV` as an option:

<img src="assets/ml4.png" width="800"/>

Make sure your instance is selected in the connection dropdown (**NOT the Sigma Sample Database**), and then drag your the downloaded csv file into the upload area. 

Then click `Save` in the upper right to upload the table to your Snowflake instance and view the table in your sigma workbook:

<img src="assets/ml5.png" width="800"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Sigma Data Exploration
Duration: 20

Shift sales will be of primary importance for this QuickStart, so let’s adjust adjust its format to `currency` at the start of our analysis. 

Select the `Shift Sales` column, and use the buttons next to the formula bar to adjust the format:

<img src="assets/ml6.png" width="800"/>

We don’t know what variables impact sales, but it’s a safe bet to start with time having some kind of impact. 

Let’s make a visual to explore this. 

Create a `Child element` visual: 

<img src="assets/ml7.png" width="600"/>

Drag `Date` and `Shift Sales` columns to the `X` and `Y axis`, respectively:

<img src="assets/ml8.png" width="600"/>

We can see that Sigma automatically aggregates our data to the `Day level` and applies a `Sum`. 

Lets adjust this to a monthly aggregation to "quiet out" some of the noise. 

You can adjust the formula directly in the formula bar:

<img src="assets/ml9.png" width="800"/>

We can see the seasonality of the sales around each January, and we can isolate this further to confirm that suspicion. 

We will switch the formula to a [datepart() function](https://help.sigmacomputing.com/docs/datepart), and see that the first 3 months do indeed have the highest sales:

<img src="assets/ml10.png" width="800"/>

The second factor that we think may play a role in the sales is the shift that the sales took place in. 

We can easily add that to our visual, and then switch to a “No Stacking” bar chart, to see the differences between AM and PM shifts:

<img src="assets/ml11.png" width="800"/>

The third factor that we think may play a role is the weekday that the sales took place on. This is a very similar question to our monthly analysis. 

We can duplicate the table:

<img src="assets/ml12.png" width="600"/>

Drag it next to our first chart: 
 
<img src="assets/ml13.png" width="800"/>

And then adjust the `DatePart() function` to use `weekday`.

Just like in the months, we can see that certain weekdays definitely return greater sales:

<img src="assets/ml14.png" width="800"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Create a Dataset for Modeling
Duration: 20

Now that we have identified Month Number, Weekday, and Shift as potential predictors for shift sales, let’s prepare a dataset with these variables for our data scientist. 

In Sigma, this may be something that a data scientist does in the existing workbook, or the analyst can prepare it with guidance. 

There is lots of room for collaboration through [live edit](https://help.sigmacomputing.com/docs/workbook-collaboration-with-live-edit) and our [comment feature.](https://help.sigmacomputing.com/docs/workbook-comments)

Create a child table of our shift sales table and drag it to the bottom of our workbook:

<img src="assets/ml15.png" width="800"/>

For our training set, we want the data to be filtered before a certain date so that we can then assess shifts after that date in the test set. 

We right click the `Date` column, and then `filter`:

<img src="assets/ml16.png" width="800"/>

Set the filter to `Between` the dates `1/1/2020 and 12/31/2022`, to get 3 years of training data:

<img src="assets/ml17.png" width="800"/>

Then, rename this table to `Train` by double-clicking the title, to edit it.

Now we need to create the columns that we found to drive Sales. 

Add a column: 

<img src="assets/ml18.png" width="800"/>

Define it as `DatePart(“month”, [Date])`, so that we get the month number.

We can easily duplicate this column to make a weekday column as well. 

`Duplicate` the column and then change `month` to `weekday` in the formula:

<img src="assets/ml19.png" width="800"/>

Finally, your data scientist may want you to encode categorical data into numerical values. 

We can easily do this with sigma using a formula definition. 

Add a new column, define it's function as `If([Shift] = "AM", 1, 0)`, and then rename it to `Encoded Shift`.: 

<img src="assets/ml20.png" width="800"/>

Now, we need to repeat all the steps to make a Test table....**Just kidding!!**

All we need to do is `duplicate` the table: 

<img src="assets/ml21.png" width="800"/>

Adjust the `date filter` so that it gives us values `on or after 1/1/2023`, and then rename the new table to `Test`:

<img src="assets/ml22.png" width="800"/>

Finally, we can make all this work available in your Snowflake writeback schema by creating a warehouse view from the Train table. 

We recommend calling it `Train`, but you can name it anything you’d like:

<img src="assets/ml23.png" width="800"/><br>

<img src="assets/ml24.png" width="600"/>
 
<aside class="negative">
<strong>NOTE:</strong><br> Note that this will get us a fully qualified name that our data scientist can use in their programming.
</aside>

Repeat this for `Test` to create a warehouse view for the Test table.

<aside class="positive">
<strong>IMPORTANT:</strong><br> Publish the workbook to create the warehouse views!
</aside>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Visual Studio Code Programming
Duration: 20

We can now let our data scientist know that `TASTY_BITES_TRAIN` is ready for them to train their model on Month, Weekday, and Shift. 

The data scientist can now begin their work in their code editor.

<aside class="negative">
<strong>NOTE:</strong><br> We will give these steps as code chunks in a notebook style, but you can feel free to compile this into a single python script if desired.
</aside>

### 1: Authenticate using the Snowflake module

```python
# Authenticate

from snowflake.snowpark import Session
import snowflake.snowpark.functions as F
import snowflake.snowpark.types as T

# Auth Method: Hard Code Parameters
connection_parameters = {
   "account": "cxa#####",
   "user": "fran",
   "password": "########",
   "role": "sigma_dev",
   "warehouse": "PAPERCRANE",
   "database": "SE_DEMO_DB",
   "schema": "SNOWPARK_UDF",
}

session = Session.builder.configs(connection_parameters).create()
```

### 2: Create a Model Registry

This is created in your database that you will use to store this and future models.

```python
from snowflake.ml.registry import Registry

session.sql("CREATE SCHEMA IF NOT EXISTS ML_REGISTRY").collect()

reg = Registry(session, database_name="SE_DEMO_DB", schema_name="ML_REGISTRY")
```

### 3: Snowpark ML Functions

The new Snowpark ML functions make it super easy to train open-source models on optimized and scalable Snowflake compute. 

We can set up a code block that allows us to easily train a linear regression model with just a few lines. 

You will use the warehouse view locations that you generated in your sigma workbook in the session table calls below:

```python
from snowflake.ml.modeling.linear_model import LinearRegression

# Specify inputs
training_table = session.table("[USE WAREHOUSE VIEW LOCATION FOR TRAIN]")
testing_table = session.table("[USE WAREHOUSE VIEW LOCATION FOR TEST]")

# Input my Analyst's ideas for features
feature_cols = [
    "MONTH_OF_DATE",
    "WEEKDAY_OF_DATE",
    "ENCODED_SHIFT",
]
target_col = "SHIFT_SALES"

my_model = LinearRegression()
my_model.set_input_cols(feature_cols)
my_model.set_label_cols(target_col)
my_model.set_output_cols("PRED_" + target_col)

my_model.fit(training_table)
```

### 4: Create Governed Metrics

Snowflake also offers a large library of metrics that allow us to record the quality of a given model.

```python
from snowflake.ml.modeling.metrics import mean_absolute_error

predictions = my_model.predict(testing_table)
mae_score = mean_absolute_error(
    df=predictions, y_true_col_names="SHIFT_SALES", y_pred_col_names="PRED_SHIFT_SALES"
)
mae_score
```

### 5: Log the Model

Finally, we can log this model, and its version, comments, and metrics into the registry that we created above. 

The final line of this code prints the results, where we see that this model is now deployed to our registry where we can review, improve, and call the model.

```python
# Log the model
model_ver = reg.log_model(
    model_name="SHIFT_SALES_MODEL", version_name="Version_1", model=my_model
)

# Add a description to the model -
model_ver.set_metric(metric_name="MAE Score", value=mae_score)
model_ver.comment = "This linear regression model predicts the Shift Sales for a given Location, using Features discovered through Sigma"

reg.get_model("SHIFT_SALES_MODEL").show_versions()
```

### 6: Give Permissions to Sigma

Thanks to Sigma’s direct to CDW connection, all we have to do is give the Sigma Role access, and the model will be automatically available to Sigma! 

<aside class="positive">
<strong>IMPORTANT:</strong><br> Make sure to update this to your registry and your Sigma role.
</aside>

```python
session.sql("GRANT USAGE ON ALL MODELS IN SCHEMA SE_DEMO_DB.ML_REGISTRY TO ROLE PAPERCRANE").collect()
```

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Using the Model in Sigma
Duration: 5

We’ll now show how we can apply that trained model in sigma, and look at an example application of that method. 

1: Create a child table from our `Test` table, and call it `Deploy Model.` We’ll be calling our model here. 

2: Create a new column, and use the following syntax and your own model location to define a function like this:
```code 
CallVariant(“SE_DEMO_DB.ML_REGISTRY.SHIFT_SALES_MODEL!Predict”) 
```
You should see an error about argument types, as we haven’t provided any input yet. 

If you get an error about the UDF not existing, there is likely a permissions error. 

<aside class="positive">
<strong>IMPORTANT:</strong><br> Make sure you have given usage to the model as described in Section 5. Visual Studio Code Programming, Step 6.
</aside>

<img src="assets/ml25.png" width="800"/>

3: Now let’s add the arguments. These should be provided in the same order as in your code: 
`MONTH_OF_DATE`, `WEEKDAY_OF_DATE`, `ENCODED_SHIFT`. 

Voila, you should now see a JSON output in this column. 

<img src="assets/ml26.png" width="800"/>

4: Finally, we can now extract the prediction from the column. Sigma [reads JSON right out of the box](https://help.sigmacomputing.com/docs/json), so we can just right click and extract the columns. 

For linear regression, there is only one output, `PRED_SHIFT_SALES`, that we care about, but we could imagine other models that would have multiple outputs here. 

Confirm your selection, and we have our final prediction that directly runs the model we defined in Snowflake:

<img src="assets/ml27.png" width="800"/>

<br>

<img src="assets/ml28.png" width="800"/>

5: Now, if we combine the steps of the prediction above, we end up with a final syntax that looks something like this:
```code
Number(CallVariant("SE_DEMO_DB.ML_REGISTRY.SHIFT_SALES_MODEL!PREDICT", [Month of Date], [Weekday of Date], [Encoded Shift]).PRED_SHIFT_SALES)
```

That’s quite a mouthful, and it is clearly unrealistic to expect later business users to invoke the model in this way. Luckily, we can use a [Sigma Custom Function](https://help.sigmacomputing.com/docs/custom-functions) to encode this for future use in a friendlier syntax. 

Open up your `Admin Panel` to access the custom functions:

<img src="assets/ml29.png" width="800"/>

6: Currently, `Custom Functions` are located on the bottom of our `Admin Panel`. 

Scroll down to the bottom of the page, and then select `Add`:

<img src="assets/ml30.png" width="800"/>

7: We can paste the formula from Step 5 into the formula box, and then update to your own model location. 

We can then give the Custom Function an easy-to-find name, `PredictShiftSales` - and let our users know what it does:

<img src="assets/ml31.png" width="800"/>

8: Now, we can define the arguments, again using User-Friendly variable names and descriptions. You don’t need the descriptions, but they are a great way to explain and specify what users should enter here. 

For this QuickStart, you can just use the names `Month Number`, `Weekday Number` and `Shift Number` and save the descriptions for later:

<img src="assets/ml32.png" width="800"/>

9: Once we update the formula bar to use these new friendly names, making sure to maintain the order of the arguments, we can save the Custom Function and it will now be available in our workbook:

<img src="assets/ml33.png" width="800"/>

10: Go back to the `ML Shift Sales` workbook and add a `new column` to our `Deploy Model` table. 

You’ll be able to now run the exact same ML model by entering in `PredictShiftSales` and filling in the arguments! 

This simple format for calling the model will make your Model far more accessible to the end users who stand to benefit from it:

<img src="assets/ml34.png" width="800"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Extended Applications
Duration: 5

This section documents examples of how different personas can benefit from deployed ML functions.

**1: Business Ops: Scoring new data through Input tables**<br>
It’s very common for organizations to have operational steps outside the CDW, in the format of Excel or Google Sheets files. Incorporating those files into a Machine Learning framework has historically involved a fair amount of friction. In Sigma, we can do it very simply using an input table. The input table allows us to paste the values from a Google Sheets table, and then transform the variables for the model, and apply the model all in one step:

<img src="assets/ml35.png" width="800"/>

Our Business Op persona can then quickly identify the shifts with the most predicted earnings and allocate more resources to those shifts! In this example, we use a RankPercentile function to find the top and bottom 10% predicted shifts, and mark those for Boosting and Dropping, respectively ml36.png

**2: Data Apps: Scoring a specific shift**<br>
Suppose you want to build your manager a tool that allows them to know whether a specific shift is expected to perform well or not. We can build that Data App in seconds in Sigma. In our example, we create two controls for the date and the shift. We can then handle the transformation within a Dynamic Text Element, such that the control is properly formatted for the Model Call. As a result, we get a ready-made Scoring App, where any business user can tweak what day or shift they want to get the prediction for:

<img src="assets/ml37.png" width="800"/>

**3: Data Science: Reviewing the quality of a model.**<br>
Sigma can also be an excellent place to check the accuracy and performance of an ML model. In this example, we run the Custom Function against our Test Set and compare the output against the actual observed shift sales we saw for that day. We can create a new column, `Residual`, that measures the difference between the observed and predicted value.

Then, the residuals can be plotted to see if the predictive power of our model is sufficient for our use case, or if further refinements in Snowpark or EDA are needed. Because Sigma is so flexible in the calculations and groupings we can apply, customers use Sigma for all sorts of statistical applications, including Power Analyses, Confusion Matrices, and Lift, ROC, and Gain charts:

<img src="assets/ml38.png" width="800"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 3

Congratulations! You've successfully built a training dataset, trained a model, and exposed it in a easy to use medium through a Sigma front end. This exercise is just scratching the surface of what is possible with Snowflake, Snowpark, and Sigma.


### What You Learned

- How to explore and build a dataset for training a model
- How to build a machine learning model using Snowpark ML
- How to register a model in the Snowpark Model Registry
- How to expose the model to business users in Sigma

### Related Resources

[Blog](https://www.sigmacomputing.com/blog/)<br>
[Community](https://community.sigmacomputing.com/)<br>
[Help Center](https://help.sigmacomputing.com/hc/en-us)<br>
[QuickStarts](https://quickstarts.sigmacomputing.com/)<br>

Be sure to check out all the latest developments at [Sigma's First Friday Feature page!](https://quickstarts.sigmacomputing.com/firstfridayfeatures/)
<br>

[<img src="./assets/twitter.png" width="75"/>](https://twitter.com/sigmacomputing)&emsp;
[<img src="./assets/linkedin.png" width="75"/>](https://www.linkedin.com/company/sigmacomputing)&emsp;
[<img src="./assets/facebook.png" width="75"/>](https://www.facebook.com/sigmacomputing)

![Footer](assets/sigma_footer.png)






<!-- END OF WHAT WE COVERED -->
<!-- END OF QUICKSTART -->

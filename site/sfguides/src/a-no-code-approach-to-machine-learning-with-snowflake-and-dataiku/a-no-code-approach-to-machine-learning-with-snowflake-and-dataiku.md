author: Stephen Franks
id: a-no-code-approach-to-machine-learning-with-snowflake-and-dataiku
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/partner-solution, snowflake-site:taxonomy/product/ai
language: en
summary: Build ML models without code using Dataiku's visual interface connected to Snowflake for rapid experimentation.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# A No Code Approach to Machine Learning with Snowflake and Dataiku
<!-- ------------------------ -->
## Overview 

This Snowflake Quickstart covers the basics of training machine learning models, interpreting them, and deploying them to make predictions. 

With Dataiku’s Visual Snowpark ML plugin - you won’t need to write a single line of code. That’s right!

- Domain experts - you don’t need to fuss around with learning programming to inject ML into your team.
- Data Scientists - we’re all trying to roll our own abstracted ML training and deployment platform - and we think you’ll like this one.



### Use Case
Consumer lending is difficult. What factors about an individual and their loan application could indicate whether they’re likely to pay back the loan? How can our bank optimize the loans approved and rejected based on our risk tolerance? 
We’ll use machine learning to help with this decision making process. Our model will learn patterns between historical loan applications and default, then we can use it to make predictions for a fresh batch of applications. 



### What You’ll Learn
The exercises in this lab will walk you through the steps to: 
- Use Snowflake's "Partner Connect" to create a Dataiku cloud trial
- Create a Snowpark-optimized warehouse (for ML workloads)
- Upload a base project in Dataiku with our data sources in Snowflake
- Look at our loan data, understand trends through correlation matrices
- Train, interpret, and deploy Machine Learning models in Dataiku - powered by Snowpark ML
- Use our trained model to make new predictions
- `(Optional)` Set up an MLOps process to retrain the model, check for accuracy, and make new predictions on a weekly basis


### What You’ll Need 
- Snowflake free 30-day trial environment
- Dataiku free 14-day trial environment (via Snowflake Partner Connect)


<!-- ------------------------ -->
## Create Your Snowflake Lab Environment

If you haven't already, [register for a Snowflake free 30-day trial](https://trial.snowflake.com/) The rest of the sections in this lab assume you are using a new Snowflake account created by registering for a trial.

> 
> 
>  **Note**: Please ensure that you use the **same email address** for both your Snowflake and Dataiku sign up

- **Region**  - Although not a requirement we'd suggest you select the region that is physically closest to you for this lab

- **Cloud Provider**  -  Although not a requirement we'd suggest you select ```AWS``` for this lab

- **Snowflake edition**  -  We suggest you select select the ```Enterprise edition``` so you can leverage some advanced capabilities that are not available in the Standard Edition.



After activation, you will create a ```username```and ```password```. Write down these credentials. **Bookmark this URL for easy, future access**.

> 
> 
>  **About the screen captures, sample code, and environment:** <br> Screen captures in this lab depict examples and results that may slightly vary from what you may see when you complete the exercises.


<!-- ------------------------ -->
## Create Your Dataiku Lab Environment (Via Snowflake Partner Connect)


### Log Into the Snowflake User Interface (UI)

Open a browser window and enter the URL of your Snowflake 30-day trial environment. You should see the login screen below. Enter your unique credentials to log in.

![img](assets/PC1.png)

<br>
<br>
<br>

You may see "welcome" and "helper" boxes in the UI when you log in for the first time. Close them by clicking on Skip for now in the bottom right corner in the screenshot below.

![img](assets/PC2.png)

### Create Dataiku trial via Partner Connect

At the top right of the page, confirm that your current role is `ACCOUNTADMIN`, by clicking on your profile on the top right.

1. Click on `Data Products` on the left-hand menu
2. Click on `Partner Connect`
3. Search for Dataiku
4. Click on the `Dataiku` tile 

![img](assets/PC3.png)

> 
> Depending on which screen you are on you may not see the full menu as above but hovering over 
> the Data Products (Cloud) icon will show the options

This will automatically create the connection parameters required for Dataiku to connect to Snowflake. Snowflake will create a dedicated database, warehouse, system user, system password and system role, with the intention of those being used by the Dataiku account.

For this lab we’d like to use the **PC_DATAIKU_USER** to connect from Dataiku to Snowflake, and use the **PC_DATAIKU_WH** when performing activities within Dataiku that are pushed down into Snowflake.

This is to show that a Data Science team working on Dataiku and by extension on Snowflake can work completely independently from the Data Engineering team that works on loading data into Snowflake using different roles and warehouses.

![img](assets/PC4.png)
<br>
<br>

1. Click `Connect`
2. You will get a pop-ip which tells you your partner account has been created. Click on `Activate`

> 
> 
>  **Informational Note:** <br> If you are using a different Snowflake account than the one created 
> at the start, you may get a screen asking for your email details. Click on ‘Go to Preferences’ and 
> populate with your email details

This will launch a new page that will redirect you to a launch page from Dataiku.

Here, you will have two options:

1. Login with an existing Dataiku username
2. Sign up for a new Dataiku account

* We assume that you’re new to Dataiku, so ensure the `“Sign Up” box is selected`, and sign up with either GitHub, Google or your email address and your new password. 

**Make sure you use the same email address that you used for your Snowflake trial**.

- `Click sign up`.

![img](assets/PC5.png)
<br>
<br>

When using your email address, ensure your password fits the following criteria:

1. At least 8 characters in length
2. Should contain:
   Lower case letters (a-z)
   Upper case letters (A-Z)
   Numbers (i.e. 0-9)

You should have received an email from Dataiku to the email you have signed up with. Activate your Dataiku account via the email sent.

### Review Dataiku Setup

Upon clicking on the activation link, please briefly review the Terms of Service of Dataiku Cloud. In order to do so, please scroll down to the bottom of the page. 
* Click on `I AGREE` and then click on `NEXT`

![img](assets/PC6.png)
<br>
<br>

* Complete your sign up some information about yourself and then click on `Start`.


* You will be redirected to the Dataiku Cloud Launchpad site. Click `GOT IT!` to continue.

![img](assets/PC7.png)
<br>
<br>
This is the Cloud administration console where you can perform tasks such as inviting other users to collaborate, add plugin extensions, install industry solutions to accelerate projects as well as access community and academy resources to help your learning journey. 

> 
>**NOTE:** It may take several minutes for your instance to Dataiku to start up the first time,
> during this time you will not be able to add the extension as described below.
> You can always come back to this task later if time doesn't allow now

### Add the Visual SnowparkML Plugin

It's beyond the scope of this course to cover plugins in depth but for this lab we would like to enable a few the Visual SnowparkML plugin so lets do that now.

1. Click on `Plugins` on the left menu
2. Select `+ ADD A PLUGIN` 
3. Find `Visual SnowparkML`
4. Check `Install on my Dataiku instance`, and click `INSTALL`

![img](assets/PC8.png)


![img](assets/PC9.png)

1. Click on `Code Envs` on the left menu
2. Select `ADD A CODE ENVIRONMENT` 
3. Select  `NEW PYTHON ENV`
4. Name your code env `py_39_snowpark` **NOTE: The name must match exactly** 
5. Click `CREATE`

![img](assets/PC10.png)

![img](assets/PC11.png)

![img](assets/PC12.png)

6. Select `Pandas 1.3 (Python 3.7 and above) from Core Packages menu
7. Add the following packages
```sql
scikit-learn==1.3.2
mlflow==2.9.2
statsmodels==0.12.2
protobuf==3.16.0
xgboost==1.7.3
lightgbm==3.3.5
matplotlib==3.7.1
scipy==1.10.1
snowflake-snowpark-python==1.14.0
snowflake-snowpark-python[pandas]==1.14.0
snowflake-connector-python[pandas]==3.7.0
MarkupSafe==2.0.1
cloudpickle==2.0.0
flask==1.0.4
Jinja2==2.11.3
snowflake-ml-python==1.5.0
```
8. Select `rebuild env` from the menu on the left
9. Click `Save and update`

![img](assets/PC13.png)

You've now successfully set up your Dataiku trial account via Snowflake's Partner Connect. We are now ready to continue with the lab. For this, move back to your Snowflake browser.

<!-- ------------------------ -->
## Create a Snowpark Optimized Warehouse in Snowflake

### Return to the Snowflake UI

We will now create an optimized warehouse

1. Click `Admin` from the bottom of the left hand menu
2. Then `Warehouses`
3. Then click `+ Warehouse` in the top right corner

![img](assets/OWH1.png)

Once in the `New Warehouse` creation screen perform the following steps:

1. Create a new warehouse called `SNOWPARK_WAREHOUSE`
2. For the type select `Snowpark-optimized`
3. Select `Medium` as the size
4. Lastly click `Create Warehouse`

![img](assets/OWH2.png)
<br>
<br>
<br>
<br>

* Select your new Snowflake Warehouse by `clicking on it once`.

![img](assets/OWH3.png)

We need to permission the Dataiku Role that was created by Partner Connect in the earlier chapter for this new warehouse.
- Scroll down to Privileges, and click `+ Privilege`

![img](assets/OWH4.png)

1. For the Role select the role `PC_DATAIKU_ROLE`
2. Under Pivileges grant the `USAGE` privilege
3. Click on `Grant Privileges`

![img](assets/OWH5.png)
<br>
<br>
You should now see your new privileges have been applied 

![img](assets/OWH6.png)



<!-- ------------------------ -->
## Import a Baseline Dataiku Project


Return to the Dataiku trial launchpad in your browser

1. Ensure you are on the `Overview` page
2. Click on `OPEN INSTANCE` to get started.

![img](assets/IMP1.png)


Congratulations you are now using the Dataiku platform! For the remainder of this lab we will be working from this environment which is called the design node, its the pre-production environment where teams collaborate to build data products.

Now lets import our first project.

* Download the project zip file to your computer - **Don’t unzip it!** 

<button>

  [Starter Project](https://dataiku-partnerships.s3.eu-west-1.amazonaws.com/LOANDEFAULTSSNOWPARKML.zip)
</button>

Once you have download the starter project we can create our first project

1. Click `+ NEW PROJECT` 
2. Then `Import project` 

![img](assets/IMP2.png)

<br>
<br>
<br>
<br>

* Choose the .zip file you just downloaded, then click `IMPORT`

![img](assets/IMP3.png)
<br>
<br>
<br>
<br>

You should see a project with 4 dataset - two local CSVs which we’ve then imported into Snowflake

![img](assets/IMP4.png)

Now that we have all our setup done, lets start working with our data.
<!-- ------------------------ -->
## Analyze trends in the data


Before we begin analyzing the data in our new project lets take a minute to understand some of the concepts and terminology of a project in Dataiku.

Here is the project we are going to build along with some annotations to help you understand some key concepts in Dataiku. 

![img](assets/Trends0.png)

* A **dataset** is represented by a blue square with a symbol that depicts the dataset type or connection. The initial datasets (also known as input datasets) are found on the left of the Flow. In this project, the input dataset will be the one we created in the first part of the lab.

* A **recipe** in Dataiku DSS (represented by a circle icon with a symbol that depicts its function) can be either visual or code-based, and it contains the processing logic for transforming datasets. In addition to the core Visual and Code recipes Dataiku can be expanded with the use of plugins which are either from the freely available Dataiku library or developed by users. We will use the Visual SnowparkML plugin today

* **Machine learning processes** are represented by green icons.

* The **Actions Menu** is shown on the right pane and is context sensitive.

* Whatever screen you are currently in you can always return to the main **Flow** by clicking the **Flow** symbol from the top menu (also clicking the project name will take you back to the main Project page).

> 
> You can refer back to this completed project screenshot if you want to check your progress through the lab.

* `Double click` into the `LOAN_REQUESTS_KNOWN_SF` dataset. This is our dataset of historical loan applications, a number of attributes about them, and whether the loan was paid back or defaulted (the DEFAULTED column - 1.0 = default, 0.0 = paid back).

![img](assets/Trends1.png)
<br>
<br>
<br>
<br>

1. Click the `Statistics` tab on the top
2. Next click `+ Create first worksheet`

![img](assets/Trends2.png)
<br>
<br>
<br>
<br>

* Then select `Automatically suggest analyses`

![img](assets/Trends3.png)
<br>
<br>
<br>
<br>

* Choose a few of the suggestions, be sure to include the Correlation Matrix in your selections then click `CREATE SELECTED CARDS`

![img](assets/Trends4.png)
<br>
<br>

**Question:** What trends do you notice in the data? 

Look at the correlation matrix, and the DEFAULTED row. Notice that INTEREST_RATE has the highest correlation with DEFAULTED. We should definitely include this feature in our models!

![img](assets/Trends5.png)

**Positive** correlation means as INTEREST_RATE rises, so does DEFAULTED (higher interest rate -> higher probability of default).
Notice MONTHLY_INCOME has a **negative** correlation to DEBT_TO_INCOME_RATIO. This means that as monthly income goes up, applicants’ debt to income ratio generally goes down.

See if you can identify a few other features we should include in our models.


<!-- ------------------------ -->
## Train Machine Learning Models


### Create a new Visual SnowparkML recipe

Now we will tran an ML model using our plugin. Return to the flow either by clicking on the flow icon or by using the keyboard shortcut `(g+f)`

1. From the Flow click once on the `LOAN_REQUESTS_KNOWN_SF` dataset.
2. From the `Actions menu` on the right scroll down and select the `Visual Snowpark ML plugin`


![img](assets/ML2.png)
<br>
<br>
<br>
<br>

* Click Train ML Models on Snowpark

![img](assets/ML3.png)
<br>
<br>

We now need to set our three `Outputs` 

-  Click on `Set` under the  `Generated Train Dataset`

![img](assets/ML4.png)
<br>
<br>
1. Set the name to `train`
2. Select `PC_DATAIKU_DB` to store into
3. Click `CREATE DATASET`

![img](assets/ML5.png)

We will now repeat this process for the other two outputs

-  Click on `Set` under the  `Generated Test Dataset`
1. Set the name to `test`
2. Select `PC_DATAIKU_DB` to store into
3. Click `CREATE DATASET`


![img](assets/ML6.png)

<br>
<br>

*  Click on `Set` under the  `Models Folder`
1. Set the name to `models`
2. Select `dataiku-managed-storage` to store into
3. Click `CREATE FOLDER`

![img](assets/ML7.png)

<br>
<br>
<br>
<br>

* Your three outputs should now look like the image below. Finally click on `CREATE`


![img](assets/ML8.png)

<br>
<br>
<br>

### Define model training settings

Lets fill out the parameters for our training session.

1. Give your model a name
2. Choose `DEFAULTED` as the target column
3. Select `Two-class classification` as the prediction type
4. Choose `ROC AUC` as our model metric. This is a common machine learning metric for classification problems.

Leave the Train ratio and random seed as is. This will split our input dataset into 80% of records for training, leaving 20% for an unbiased evaluation of the model

![img](assets/ML9.png)

<br>
<br>
<br>
<br>

* Choose the following features to include in our model. Make sure to make a selection for Encoding / Rescaling and Impute Missing Values With - **don’t leave them empty**.


![img](assets/ML13.png)


![img](assets/ML14.png)
<br>
<br>
<br>
<br>

* Choose the following algorithms to start. We’ll go through the basics of these algorithms after we kick off our model training.

![img](assets/ML15.png)

1. Leave the Search space limit as 4
2. Write SNOWPARK_WAREHOUSE to use the Snowpark-optimized warehouse we created earlier.
3. Check the “Deploy to Snowflake ML Model Registry” box. This will deploy our best trained model to Snowflake’s Model Registry - where we can use it to make predictions later on.



* Finally Click the `RUN` button in the bottom left hand corner to start training our models.

![img](assets/ML16.png)


<!-- ------------------------ -->
## Machine Learning - Basic Theory (Optional)


While we’re waiting for our models to train, let’s learn a bit about machine learning. This is an oversimplification of some complicated topics. If you’re interested there are links at the end of the course for the Dataiku Academy and many other free resources online.

### Machine Learning, Classification, and Regression

**Machine learning** - the use and development of computer systems that are able to learn and adapt without following explicit instructions, by using algorithms and statistical models to analyze and draw inferences from patterns in data.

**Oversimplified definition of machine learning** - Fancy pattern matching based on the data you feed into it

The two most common types of machine learning solutions are supervised and unsupervised learning.
<br>
**Supervised learning**
Goal: predict a target variable
- category = classification
- numerical value = regression

Examples:
- Predict the sales price of an apartment (regression)
- Forecast the winner of an election (classification)
<br>
<br>

**Unsupervised learning**
Goal: identify patterns
- Group similar individuals  = **clustering**
- Find anomalies = **anomaly detection**

Examples:
- Segment consumers according to their behavior (clustering)
- Find anomalous opioid shipments from a DEA database (anomaly detection)
<br>
<br>
Our problem - predicting loan defaults, is a **supervised, classification problem**.

We need a structured dataset to train a model, in particular: 
- Rows measuring **individual observations** (one transaction per row)
- **Target column** with real labels of what we want to predict
- **Other columns** (features) that the model can use to predict the target (through fancy pattern matching)

![img](assets/MLB1.png)
<br>
### Train / Test split

Once we have a structured dataset with observations, a target, and features, we split it into train and test sets

We could split it:
- Randomly
- Based on time
- Other criteria

A random split of 80% train / 20% test is common

![img](assets/MLB2.png)
<br>

We train models on the train set, then evaluate them on the test set. This way, we can simulate how the model will perform on data that it hasn’t seen before.

### Feature Handling

Two keys to choosing features to include in our model:
- Only include variables that you know you’ll have at the time you need to make predictions (e.g. at time of sale for future credit card transactions)
- Use your domain knowledge - if you think a variable could be a driver of the target, include it in your model!

Most machine learning models require variables to be a specific format to be able to find patterns in the data.

We can generally break up our variables into two categories:
- **Numeric** - e.g. AMOUNT_REQUESTED, DEBT_TO_INCOME_RATIO
- **Categorical** - e.g. LOAN_PURPOSE, STATE

Here are some ways to transform these types of features:

**Numeric** - e.g. AMOUNT_REQUESTED, DEBT_TO_INCOME_RATIO
<br>

Things you typically want to consider:
- **Impute** a number for rows missing values. Average, median are common
- **Rescale** the variable. Standard rescaling is common (this transforms a value to its Z-score)

![img](assets/MLB3.png)
<br>
<br>
<br>

**Categorical** - e.g. LOAN_PURPOSE, STATE
<br>

Things you typically want to consider:
- **Encode** values with a number. Dummy encoding, ordinal encoding are common
- **Impute** a value for rows missing values. You can treat a missing value as its own category, or impute with the most common value.
![img](assets/MLB4.png)

<br>

### Machine Learning Algorithms 
<br>

Let’s go through a few common machine learning algorithms.

**Linear Regression**

For linear regression (predicting a number), we find the line of best fit, plotting our feature variables and our target

`y = b0 + b1 * x`

If we were training a model to predict exam scores based on # hours of study, we would solve for this equation

`exam_score = b0 + b1 * (num_hours_study)`

![img](assets/MLB5.png)
<br>

We use math (specifically a technique called Ordinary Least Squares[1]) to find the b0 and b1 of our best fit line

`exam_score = b0 + b1 * (num_hours_study)`

`exam_score = 32 + 8 * (num_hours_study)`

![img](assets/MLB6.png)
<br>


**Logistic Regression**

Logistic regression is similar to linear regression - except built for a classification problem (e.g. loan default prediction).

`log(p/1-p) = b0 + b1 * (num_hours_study)`

`log(p/1-p) = 32 + 8 * (num_hours_study)`

`p = probability of exam success`

![img](assets/MLB7.png)

<br>

**Decision Trees**

Imagine our exam pass/fail model with more variables.

Decision trees will smartly create if / then statements, sending each row along a branch until it makes a prediction of your target variable

![img](assets/MLB8.png)
<br>
<br>

**Random Forest**

A Random Forest model trains many decision trees, introduces randomness into each one, so they behave differently, then averages their predictions for a final prediction

![img](assets/MLB9.png)
<br>
<br>

**Overfitting**

We want our ML model to be able to understand true patterns in the data - uncover the signal, and ignore the noise (random, unexplained variation in the data)

 Overfitting is an undesirable machine learning behavior that occurs when the machine learning model gives accurate predictions for training data but not for new data

 ![img](assets/MLB10.png)
 <br>
 ![img](assets/MLB11.png)
<br>

**How to control for overfitting**

Logistic Regression
- Increasing C shrinks your equation coefficients
- Increase C to control more for overfitting

Example

`C = 0.01:  log(p/1-p) = 32 + 8 * (num_hours_study) + 6 * (num_hours_sleep)`
 
`C = 0.1:  log(p/1-p) = 32 + 5 * (num_hours_study) + 4 * (num_hours_sleep) `

`C = 1:  log(p/1-p) = 32 + 3 * (num_hours_study) + 2 * (num_hours_sleep) `

`C = 10:  log(p/1-p) = 32 + 2 * (num_hours_study) + 0 * (num_hours_sleep) `

`C = 100:  log(p/1-p) = 32 + 1 * (num_hours_study) + 0 * (num_hours_sleep)` 
<br>
<br>

Random Forest
<br>

- **Maximum depth of tree**  how far down can each decision tree go?
- Decrease this to control more for overfitting

For more in-depth tutorials and self-paced machine learning courses see the links to Dataiku's freely available Academy in the last chapter of this course

<!-- ------------------------ -->
## Model Evaluation


Once we’ve trained our models, we’ll want to take a deeper dive deep into how they’re performing, what features they’re considering, and whether they may be biased. Dataiku has a number of tools for evaluating models.

- `Double click` on your model (Green diamond) from the flow

![img](assets/Eval1.png)

* You’ll see your best trained model here. `Click` into it.

![img](assets/Eval2.png)
<br>
<br>
<br>

1. Select `Feature Importance` from the menu on the left side
2. Then click `COMPUTE NOW`

![img](assets/Eval3.png)
<br>
<br>
<br>
<br>
Here we can see that the top 3 features impacting the model are applicants’ FICO scores, the interest rate of the loan, and the amount requested. This makes sense!
<br>
<br>

![img](assets/Eval4.png)
<br>
<br>
<br>
<br>

Scroll down on this page - you’ll see the directional effect of each feature on default predictions. You can see that the higher FICO scores generally mean lower probability of default.


![img](assets/Eval5.png)
<br>
<br>
<br>
<br>

* Click on the `Confusion matrix` tab from the menu on the left. 

Here we can see how the model would have performed on the hold-out test set of loan applicants. Notice that my model is very good at catching defaulters (83 Predicted 1.0 out of 84 Actually 1.0), at the expense of mistakenly rejecting 124 applicants that would have paid back their loan. 

Try moving the threshold bar back and forth. It will cause the model to be more or less sensitive. Based on your business problem, you may want a higher or lower threshold.

![img](assets/Eval6.png)



<!-- ------------------------ -->

## Make Predictions (Scoring)


Using a machine learning model to make predictions is called `scoring` or `inference`

### Score the unknown loan applications using the trained model

1. Go to the project Flow, click once on the ``LOAN_REQUESTS_UNKNOWN_SF`` dataset
2. Then click on the ``Visual Snowpark ML`` plugin from the right hand Actions menu.

![img](assets/Score1.png)
<br>
<br>
<br>
<br>

* Click `Score New Records using Snowpark`

![img](assets/Score2.png)
<br>
<br>
<br>
<br>

We need to add our model as an input and set an output dataset for the results of the scoring.

1. In the `Inputs` under the `Saved Model` option click on `SET` to add your saved model
2. In the `Outputs` section under `Scored Dataset Option` click on `SET` and give your output dataset a name
3. For `Store into` use the `PC_DATAIKU_DB** connection
4. Click on `CREATE DATASET`

![img](assets/Score5.png)
<br>
<br>

* Your screen should now look like this. Go ahead and `click on CREATE`


![img](assets/Score6.png)
<br>
<br>
<br>
<br>

* Make sure the warehouse you created earlier `SNOWPARK_WAREHOUSE` is selected then click on `RUN`

![img](assets/Score7.png)
<br>
<br>
<br>
<br>
When it finishes, your flow should look like this

![img](assets/Score8.png)

* `Double click` into the output scored dataset - scroll to the right, and you should see predictions of whether someone is likely to pay back their loan or not!


![img](assets/Score9.png)


<!-- ------------------------ -->

## MLOps (optional)


Let’s say we want to automatically run new loan applications through our model every week on Sunday night.

Assume that `LOAN_REQUESTS_UNKNOWN` is a live dataset of new loan applications that is updated throughout the week.

We want to rerun all the recipes leading up to unknown_loans_scored, where our model makes predictions.

### Build a weekly scoring scenario

- Click into the Scenarios tab

![img](assets/mlops1.png)

- Click `+ CREATE YOUR FIRST SCENARIO`

![img](assets/mlops2.png)

- Name your scenario something like `“Weekly Loan Application Scoring”`


![img](assets/mlops3.png)
<br>
<br>
<br>
<br>

- Add a time-based trigger

![img](assets/mlops4.png)
<br>
<br>
<br>
<br>

- Set the trigger to run `every week on Sunday at 9pm`

![img](assets/mlops5.png)
<br>
<br>
<br>
<br>

- In the `Steps` tab, click `Add Step`, then `Build / Train`

![img](assets/mlops6.png)
<br>
<br>
<br>
<br>

- Add a dataset to build

![img](assets/mlops7.png)
<br>
<br>
<br>
<br>

- Then choose the `unknown_loans_scored` dataset

![img](assets/mlops8.png)
<br>
<br>
<br>
<br>

- Check the `Force-build` button to recursively build all datasets leading up to `unknown_loans_scored`, then click the `run` button to test it out.

![img](assets/mlops9.png)
<br>
<br>
<br>
<br>

You’ll be able to see scenario run details in the “Last runs” tab

![img](assets/mlops10.png)

### Build a monthly model retraining scenario (optional)

It’s good practice to retrain machine learning models on a regular basis with more up-to-date data. The world changes around us; the patterns of loan applicant attributes affecting default probability are likely to change too.

If you have time you can assume that LOAN_REQUESTS_KNOWN is a live dataset of historical loan applications that is updated with new loan payback and default data on an ongoing basis.

You can automatically retrain your model every month with scenarios, and put in a AUC check to make sure that the model is performing and build the scored dataset


<!-- ------------------------ -->
## Conclusion & Resources

Congratulations on completing this introductory lab exercise! Congratulations! You've mastered the Snowflake basics and you’ve taken your first steps toward a no-code approach to training machine learning models with Dataiku.

You have seen how Dataiku's deep integrations with Snowflake can allow teams with different skill sets get the most out of their data at every stage of the machine learning lifecycle.

We encourage you to continue with your free trial and continue to refine your models and by using some of the more advanced capabilities not covered in this lab.

### What You Learned:

- Use Snowflake's "Partner Connect" to create a Dataiku cloud trial
- Create a Snowpark-optimized warehouse (for ML workloads)
- Upload a base project in Dataiku with our data sources in Snowflake
- Look at our loan data, understand trends through correlation matrices
- Train, interpret, and deploy Machine Learning models in Dataiku - powered by Snowpark ML
- Use our trained model to make new predictions
- `(Optional)` Set up an MLOps process to retrain the model, check for accuracy, and make new predictions on a weekly basis

### Related Resources

- Join the [Snowflake Community](https://community.snowflake.com/s/)
- Join the [Dataiku Community](https://community.dataiku.com/)
- Sign up for [Snowflake University](http://https://community.snowflake.com/s/snowflake-university)
- Join the [Dataiku Academy](https://academy.dataiku.com/)

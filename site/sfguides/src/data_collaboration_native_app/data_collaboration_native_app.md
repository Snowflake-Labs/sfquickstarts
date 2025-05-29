author: Tim Buchhorn
id: data_collaboration_native_app
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Sharing an ML Model via Native Apps
<!-- ------------------------ -->
## Overview 
Duration: 1

This Quickstart guide is the second in a series of Collaboration & Applications in Snowflake. Part One of the series can be found [here](https://quickstarts.snowflake.com/guide/data_collaboration_two_way/index.html?index=..%2F..index#0)

In Part One, we showed how using Snowflake's unique collaboration features, we could:
- share data from an organisation to another
- score that data using an ML model
- share it back with the original provider
all in an automated pipeline

In this Quickstart, we will show how we can leverage the Native Apps Framework to simplify this process even further.

The Native App Framework is a collaboration framework that allows providers to share data and/or related business logic to other Snowflake customers. In the previous Quickstart guide, we set up a bi-directional share between two organisations. With the Native App framework, we can simplify this relationship by allowing one party to share its logic in the form of an application to the other. Therefore, we have brought the app to the data, as opposed to bringing the data to the app

![Diagram](assets/native_app_overview.png)

There are numerous benefits to leveraging the Native App framework for our Use Case. For example:
- Data Sovereignty and Security for the Consumer. In the previous quickstart, it was necessary for the provider to share data with another entity. This could be potentially sensitive information, and therefore a bigger hurdle for security and governance teams to approve. With Native Apps, the app logic is brought to the consumers dataset, so no customer data is leaving their security perimeter
- Compliance Risk Reduction for the Provider. Similar to the above, the provider of the model way not want to have access to customer data. This requires extra consideration with how to securely handle this data, which is not necessary if the model is shared to their customers to run against their own data.
- Increased Margin. By sharing the model to the consumer, the infrastructure cost to execute the model are now with the consumer. This means the provider can monetise the model, without worrying about infrastructure costs. Similarly the consumer can set warehouse sizes appropriate to the SLAs and budgets of the consumer organisation.
- Faster Onboarding. By having a replicable model, the provider can simple leverage the Snowflake Marketplace for distribution. They no longer need to go through a lengthy process of approvals to set up a data pipeline with their customers.

### What You Will Learn 
- How to train an ML model in Snowflake
- How to package the ML Model in an Application Package
- How to privately list a Native Application 
- How to Consume a Native Application 

### What You Will Build 
- A Native Application that contains an ML Model shared via a Private Listing 

### Prerequisites
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
    **Download the git repo here: https://github.com/Snowflake-Labs/sfguide-data-collaboration-native-app**
- [Anaconda](https://www.anaconda.com/) installed
- [Python 3.10](https://www.python.org/downloads/) installed
    - Note that you will be creating a Python environment with 3.10 in the **Consumer Account - Create Model** step
- Snowflake accounts with [Anaconda Packages enabled by ORGADMIN](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#using-third-party-packages-from-anaconda). If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/?utm_cta=quickstarts_).
- Snowflake accounts with the Snowflake Marketplace T&C's accepted. This will allow you to create Listings.
- A Snowflake account login with a role that has the ability to create Listings, Databases, Schemas, Tables, Stages, User-Defined Functions, and Stored Procedures. If not, you will need to register for free trials or use a different role.
- The [Snowpark ML](https://docs.snowflake.com/developer-guide/snowpark-ml/index#installing-snowpark-ml-from-the-snowflake-conda-channel) package installed

<!-- ------------------------ -->
## Business Use Case and Context
Duration: 5

The Business Use case follows a similar scenario as Part One.

In this guide, we are playing the role of Zamboni and Snowbank. The Credit Risk team at Snowbank has noticed a rise in credit card default rates which affects the bottom line of the business. Previously, it has shared data with an external organisation (Zamoboni) who assist with analysing the data and scoring which customers are most likely to default.

This time, the compliance team has said that it is too risky to share this customer data with an external party without proper procedures being followed, which could take a few months to complete. Zamboni have propsed a solution that utilises the Native Application Framework.

Since both companies use Snowflake, Zamboni has proposed sharing their proprietary Credit Default Scoring Model via the Native Application Framework. The advantages of doing this for Snowbank are:
- No customer data leaves Snowbank's Snowflake Account
- The Native App runs within the Snowbank Account. Since Snowflake has been approved for use internally, it is not subject to longer onboarding and cybersecurity checks

The advantages for Zamboni are:
- Simple deployment. Zamboni can simply share the model using a similar listing paradigm as sharing a dataset.
- Reduced compliance risk. Zamboni's security and compliance team are similarly pleased in being able to satisfy the business needs without needing Snowbanks data hosted on their servers
- Increased Margin. Zamboni are now able to share their proprietary logic safely, without having to provision infrastructure to run the model on behalf of Snowbank.
- Speed to Market. Zamboni can simply distribute the model via the Native App framework in a private listing. They no longer need to set up data pipelines. They can also build once, and distribute to lots of different customers by leveraging Snowflake's multitenancy framework.

What is different in this scenario compared to Part One, is that it is no longer a bi-directional share of data. Now Zamboni becomes the provider of an Application, and Snowbank becomes the consumer.

### Dataset Details

We will use a publicly available dataset to train our ML model for the purposes of this demo. The dataset contains aggregated profile features for each customer at each statement date. Features are anonymized and normalized, and fall into the following general categories:

D_* = Delinquency variables
S_* = Spend variables
P_* = Payment variables
B_* = Balance variables
R_* = Risk variables

### Dataset Citation

Addison Howard, AritraAmex, Di Xu, Hossein Vashani, inversion, Negin, Sohier Dane. (2022). American Express - Default Prediction. Kaggle. https://kaggle.com/competitions/amex-default-prediction

<!-- ------------------------ -->
## Set up
Duration: 10

Navigate to the [Snowflake Trial Landing Page](https://signup.snowflake.com/?utm_cta=quickstarts_). Follow the prompts to create a Snowflake Account. You should recieve an email to activate your trial account.

Navigate to a new worksheet and execute the following commands to create a second account in the Organisation. The second account will be the account we share the model to (Snowbank). In trial accounts we cannot share the Native App externally, although the same process can be followed to share the app externally if you have a non-trial account.

```SQL
USE ROLE ORGADMIN;

CREATE ACCOUNT SNOWBANK
  ADMIN_NAME = ADMIN
  ADMIN_PASSWORD = 'ENTER PASSWORD HERE'
  EMAIL = 'ENTER YOU EMAIL HERE'
  EDITION = ENTERPRISE;
```
Note down the account locator and the url from the output of the command above for use in later steps

<!-- ------------------------ -->

## Provider Account (Zamboni) - Set Up
Duration: 20

In this part of the lab we'll set up our Provider Snowflake account. In our business scenario, this step represents Zamboni developing their proprietry Credit Card Default model from their own datasets. Stay in the same account from the previous section.

### Initial Set Up (Zamboni)

Next, open up a new worksheet and run all following steps as the ACCOUNTADMIN role

```SQL
  -- Change role to accountadmin
  USE ROLE ACCOUNTADMIN;
```

First we can create a [Virtual Warehouse](https://docs.snowflake.com/en/user-guide/warehouses-overview) that can be used to load the initial dataset. We'll create this warehouse with a size of XS which is right sized for that use case in this lab.

```SQL
-- Create a virtual warehouse for training
CREATE OR REPLACE WAREHOUSE training_wh with 
  WAREHOUSE_SIZE = 'MEDIUM' 
  WAREHOUSE_TYPE = 'snowpark-optimized' 
  MAX_CONCURRENCY_LEVEL = 1
  AUTO_SUSPEND = 300 
  AUTO_RESUME = TRUE;
```

-- Create a virtual warehouse for data exploration
CREATE OR REPLACE WAREHOUSE QUERY_WH WITH 
  WAREHOUSE_SIZE = 'X-SMALL' 
  WAREHOUSE_TYPE = 'STANDARD' 
  AUTO_SUSPEND = 300 
  AUTO_RESUME = TRUE 
  MIN_CLUSTER_COUNT = 1 
  MAX_CLUSTER_COUNT = 1;

### Load Data 

Next we will create a database and schema that will house the tables to train our model.

```SQL
-- Create the application database and schema
CREATE OR REPLACE DATABASE NATIVE_APP_DEMO;
CREATE OR REPLACE SCHEMA NATIVE_APP_DEMO;
USE SCHEMA NATIVE_APP_DEMO.NATIVE_APP_DEMO;
```

Our data is in Parquet format, so we will create a file format object

```SQL
CREATE OR REPLACE FILE FORMAT parquet_format
TYPE = PARQUET;
```

Next we set up our [External Stage](https://docs.snowflake.com/en/user-guide/data-load-s3-create-stage#external-stages) to our data. In our business scenario, we would have a secure [Storage Integration](https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration) to the external stage rather than a public s3 bucket.

```SQL
CREATE OR REPLACE STAGE quickstart_cc_default_training_data
    URL = 's3://sfquickstarts/two_way_data_share/train/'
    FILE_FORMAT = parquet_format;

CREATE OR REPLACE STAGE quickstart_cc_default_unscored_data
    URL = 's3://sfquickstarts/two_way_data_share/unscored/'
    FILE_FORMAT = parquet_format;
```

This DDL will create the structure for the table which is the main source of data for our lab.

```SQL
CREATE OR REPLACE TABLE cc_default_training_data
  USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
      FROM TABLE(
        INFER_SCHEMA(
          LOCATION=>'@quickstart_cc_default_training_data',
          FILE_FORMAT=>'parquet_format'
        )
      ));

-- Create below to be the template of the above (without the target column)
CREATE OR REPLACE TABLE cc_default_unscored_data LIKE cc_default_training_data;
ALTER TABLE cc_default_unscored_data DROP COLUMN "target";

-- Create below to be the template of the above
CREATE OR REPLACE TABLE cc_default_new_data LIKE cc_default_unscored_data;
```

Now we will load the data in the tables. We can scale up the warehouse temporarily so we do not have to wait as long

```SQL
ALTER WAREHOUSE query_wh SET warehouse_size=MEDIUM;
```

The code below loads the data in to the tables.

```SQL
COPY INTO cc_default_training_data 
  FROM @quickstart_cc_default_training_data 
  FILE_FORMAT = (FORMAT_NAME= 'parquet_format') 
  MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;

COPY INTO cc_default_unscored_data 
  FROM @quickstart_cc_default_unscored_data 
  FILE_FORMAT = (FORMAT_NAME= 'parquet_format') 
  MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;
```
We can now scale down the warehouse since we have finished loading data for the lab

```SQL
ALTER WAREHOUSE query_wh SET warehouse_size=XSMALL;
```

You should have loaded over 5 million and 7 million rows in a few minutes. To check, query the data in the worksheet

```SQL
SELECT COUNT(*) 
  FROM CC_DEFAULT_TRAINING_DATA;

SELECT COUNT(*) 
  FROM CC_DEFAULT_UNSCORED_DATA;
```

We have loaded all the data in Zamboni. We can now proceed with training the model

<!-- ------------------------ -->
## Provider Account (Zamboni) - Create Model
Duration: 45

For this section, make sure you download the corresponding [git repo](https://github.com/Snowflake-Labs/sfguide-data-collaboration-native-app) so you have the files referenced in this section.

### Set Up Snowpark for Python and Snowpark ML

The first step is to set up the python environment to develop our model. To do this:

- Download and install the miniconda installer from [https://conda.io/miniconda.html](https://conda.io/miniconda.html). (OR, you may use any other Python environment with Python 3.10, for example, [virtualenv](https://virtualenv.pypa.io/en/latest/)).

- Open a new terminal window in the downloaded directory with the conda_env.yml file and execute the following commands in the same terminal window:

  1. Create the conda environment.
  ```
  conda env create -f conda_env.yml
  ```

  2. Activate the conda environment.
  ```
  conda activate data-collaboration-native-app
  ```

  3. Start notebook server:
  ```
  jupyter notebook
  ```
  Open the jupyter notebook Credit Card Default Native App Notebook

- Update connection.json with your Snowflake account details and credentials.
  Here's a sample based on the object names we created in the last step:

```
{
  "account"   : "<your_account_identifier_goes_here>",
  "user"      : "<your_username_goes_here>",
  "password"  : "<your_password_goes_here>",
  "role"      : "ACCOUNTADMIN",
  "warehouse" : "QUERY_WH",
  "database"  : "NATIVE_APP_DEMO",
  "schema"    : "NATIVE_APP_DEMO"
}
```

> aside negative
> 
> **Note:** For the account parameter above, specify your account identifier and do not include the snowflakecomputing.com domain name. Snowflake automatically appends this when creating the connection. For more details on that, refer to the documentation.

If you are having some trouble with the steps above, this could be due to having different architectures, such as an M1 chip. In that case, follow the instructions [here](https://docs.snowflake.com/developer-guide/snowpark-ml/index#installing-snowpark-ml-from-the-snowflake-conda-channel) and be sure to conda install jupyter notebooks and pyarrow.

### Train and Register Model
Open up the notebook and follow the steps. Once you have completed those, you will have trained and deployed a ML Model in Snowflake that predicts credit card default risk. You will also have registered the model in the Snowflake Model Registry.

Stay in the Zamboni account for the next step.

<!-- ------------------------ -->
## Provider Account (Zamboni) - Build Native App
Duration: 2

Now we have trained the model, we want to encapsulate it in an Application Package, so we can distribute it via the Native App Framework. More information on the Native Application framework can be found in the documentation [here](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about). We will be working through the [Native App Development Workflow](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-workflow#development-workflow).

Continue to work through the notebook.

The first step is to create an Application Package object that will hold the assets we wish to distribute to Snowbank. An application package encapsulates the data content, application logic, metadata, and setup script required by an application. An application package also contains information about versions and patch levels defined for the application. We do this by running the following SQL.

```SQL
CREATE APPLICATION PACKAGE IF NOT EXISTS CREDIT_CARD_PREDICTION_APP_PACKAGE;
```

Next, we need to create a stage within the Application package for us to put our model assets. We run the following SQL commands

```SQL
USE APPLICATION PACKAGE CREDIT_CARD_PREDICTION_APP_PACKAGE;
CREATE SCHEMA IF NOT EXISTS MODEL_ASSETS;
CREATE OR REPLACE STAGE CREDIT_CARD_PREDICTION_APP_PACKAGE.MODEL_ASSETS.MODEL_STAGE FILE_FORMAT = (TYPE = 'csv' FIELD_DELIMITER = '|' SKIP_HEADER = 1);
```

So we share a model that is consistent with what is in the model registry, we are going to export the model from the registry, and put it in the Application package. We do this in the following code block

```python
# Retrieve the model from the degistry
m = registry.get_model("NATIVE_APP_DEMO.NATIVE_APP_DEMO.CREDIT_CARD_DEFAULT_MODEL")
mv = m.version("default")

# Create a temp directory to export the model
import tempfile, pathlib, shutil, os
local_dir = pathlib.Path(tempfile.mkdtemp(prefix="model_export_"))

# export the full artefact set into that folder
mv.export(local_dir.as_posix(), export_mode=ExportMode.FULL)

# Upload the files and folder structure to the Application Package Stage
stage_root = "@CREDIT_CARD_PREDICTION_PACKAGE.MODEL_ASSETS.MODEL_STAGE/models"

for file_path in pathlib.Path(local_dir).rglob('*'):
    if file_path.is_file():
        rel_path = file_path.relative_to(local_dir).as_posix()   # e.g. runtimes/env.yml or manifest.yml
        subdir   = os.path.dirname(rel_path)                     # '' or 'runtimes'

        # remote prefix **must end with a slash** and contain no file-name
        remote_prefix = f"{stage_root}/{subdir}/" if subdir else f"{stage_root}/"

        session.file.put(
            file_path.as_posix(),
            remote_prefix,
            overwrite=True,
            auto_compress=False
        )

# Check that all our artefacts have been uploaded
session.sql("LIST @CREDIT_CARD_PREDICTION_PACKAGE.MODEL_ASSETS.MODEL_STAGE/models;").collect()
```

An application requires a manifest file, and a setup script (as outlined in the Native App Development Workflow). We upload them to our Application Package in the following commands

```SQL
PUT file://scripts/setup.sql @CREDIT_CARD_PREDICTION_APP_PACKAGE.MODEL_ASSETS.MODEL_STAGE/scripts overwrite=true auto_compress=false;

PUT file://manifest.yml @CREDIT_CARD_PREDICTION_APP_PACKAGE.MODEL_ASSETS.MODEL_STAGE overwrite=true auto_compress=false;
```

The setup script contains the SQL statements that define the components created when a consumer installs your application. For us, this will include creating stored procedures to perform feature engineering, as well as registering our model for the app to use on the consumer side (doecumentation [here](https://docs.snowflake.com/LIMITEDACCESS/native-apps/models)). This is done in the following lines:

```SQL
create or replace model APP_CODE.CREDIT_CARD_DEFAULT_MODEL from @CREDIT_CARD_PREDICTION_PACKAGE.MODEL_ASSETS.MODEL_STAGE/models/;

grant usage on model APP_CODE.CREDIT_CARD_DEFAULT_MODEL to application role app_user;
```



<!-- ------------------------ -->
## Provider Account (Zamboni) - Perform Local Testing
Duration: 15

Now the Application has been created fromt he Application Package in our Provider Account, we can perform some testing to ensure it behaves as expected. In this Quickstart, we have exposed more views and functions than what is necessary, so we can follow along and see how the app in functioning.

You will need a SQL worksheet for this part of the Quickstart.

This app requires the consumer to explicitly provide a reference to a table in the Snowflake instance it is installed as an input. We can acieve this through the UI, or running the following SQL.

```SQL
-- Bind the refernce to a table in our own Snowflake Account. This can be done via SQL or the UI
CALL credit_card_prediction_app.app_code.register_single_reference('RAW_TABLE' , 'ADD', SYSTEM$REFERENCE('TABLE', 'NATIVE_APP_DEMO.NATIVE_APP_DEMO.CC_DEFAULT_UNSCORED_DATA', 'PERSISTENT', 'SELECT'));

-- Check that the reference worked
SHOW REFERENCES IN APPLICATION credit_card_prediction_app;
```

Next lets run through the commands and see if they are working as expected.

```SQL
-- This should be empty, as we have not called the procedure to populate the table yet
SELECT * FROM CREDIT_CARD_PREDICTION_APP.APP.RAW_TABLE_VIEW;

-- Now we call the procedure
CALL CREDIT_CARD_PREDICTION_APP.CONFIG.CREATE_TABLE_FROM_REFERENCE_RAW();

-- And the table should now be populated
SELECT * FROM CREDIT_CARD_PREDICTION_APP.APP.RAW_TABLE_VIEW LIMIT 10;
SELECT COUNT(*) FROM CREDIT_CARD_PREDICTION_APP.APP_CODE.RAW_TABLE_VIEW;

-- Next we cal the procedure to do the feature engineering
CALL credit_card_prediction_app.app_code.cc_profile_processing();

-- The feature table should now be populated
SELECT * FROM CREDIT_CARD_PREDICTION_APP.APP_CODE.TRANSFORMED_TABLE_VIEW LIMIT 10;

-- Next we call the procedure that infers our model
CALL CREDIT_CARD_PREDICTION_APP.APP_CODE.CC_BATCH_PROCESSING();

-- And we can now see the scored table
SELECT * FROM CREDIT_CARD_PREDICTION_APP.APP_CODE.SCORED_TABLE_VIEW LIMIT 10;
```

Once this is done, we need to create a version before we can share. We can do this in the manifest file, or with the code below

```SQL

ALTER APPLICATION PACKAGE CREDIT_CARD_PREDICTION_PACKAGE
  ADD VERSION v1
  USING '@credit_card_prediction_package.stage_content.credit_card_prediction_stage'
  LABEL = 'MyApp Version 1.0';

ALTER APPLICATION PACKAGE CREDIT_CARD_PREDICTION_PACKAGE
 ADD PATCH FOR VERSION V1
 USING '@credit_card_prediction_package.stage_content.credit_card_prediction_stage';

SHOW VERSIONS IN APPLICATION PACKAGE CREDIT_CARD_PREDICTION_PACKAGE;
```

We need to set the release directive

```SQL
ALTER APPLICATION PACKAGE CREDIT_CARD_PREDICTION_PACKAGE
  SET DEFAULT RELEASE DIRECTIVE
  VERSION = v1
  PATCH = 1;
```



<!-- ------------------------ -->
## Consume Model via Native App
Duration: 2

In this next step, we will log in to our consumer account. We first need to load data that we want the shared model to run against.

### Load Data 

### Accept Shared Model

Log in to your second acccount and navigate through to Data Products > Private Sharing. You should see your app ready to be installed

<!-- ------------------------ -->
## Create another version of the app
Duration: 2

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
## Conclusion And Resources
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What You Learned
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files

### Resources
- <link to github code repo>
- <link to documentation>

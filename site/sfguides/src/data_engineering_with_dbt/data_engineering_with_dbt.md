id: data_engineering_with_dbt
summary: Build your data pipeline with Snowflake & dbt
categories: data-engineering
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, dbt, Data Sharing
authors: Dmytro Yaroshenko

# Accellerating Data Engineering with Snowflake & dbt
<!-- ------------------------ -->
## Overview 
Duration: 5

Modern Businesses need modern data strategy built on platforms that could support agility, growth and operational efficiency. Snowflake is Data Cloud, a future proof solution that can simplify data pipelines for all your businesses so you can focus on your data and analytics instead of infrastructure management and maintenance.

[dbt](https://www.getdbt.com/) is a modern data engineering framework maintained by the [Fishtown Analytics](https://www.fishtownanalytics.com/) that is becoming very popular in modern data architectures, leveraging cloud data platforms like Snowflake. [dbt CLI](https://docs.getdbt.com/dbt-cli/cli-overview) is the open-source version of dbtCloud that is providing similar functionality, but as a SaaS.
In this virtual hands-on lab, you will follow a step-by-step guide to Snowflake and dbt to see some of the benefits this tandem brings. 

Let’s get started. 

### Prerequisites
To participate in the virtual hands-on lab, attendees need the following:

* A [Snowflake account](https://trial.snowflake.com/) with `ACCOUNTADMIN` access

* Familiarity with Snowflake, and Snowflake objects


### What You'll Need During the Lab

* [dbt CLI](https://docs.getdbt.com/dbt-cli/installation) installed 

* Text editor of your choice


### What You'll Learn

* How to leverage data in Snowflake's Data Marketplace 

* How to set up a dbt project for Snowflake

* How to build scalable pipelines using dbt & Snowflake


### What You'll Build
* A set of data analytics pipelines for Financial Services data leveraging dbt, and Snowflake

* Implement data quality tests

* Promote code between the environments

<!-- ------------------------ -->
## Snowflake Configuration 
Duration: 5

1. Login to your Snowflake trial account.  
![Snowflake Log In Screen](assets/image124.png)  

2. UI Tour (SE will walk through this live). For post-workshop participants, click [here](https://docs.snowflake.com/en/user-guide/snowflake-manager.html#quick-tour-of-the-web-interface) for a quick tour of the UI.  
![Snowflake Worksheets](assets/image29.png)  

3. Lets now create a database and a service accounts for dbt.

```SQL
-------------------------------------------
-- dbt credentials
-------------------------------------------
USE ROLE securityadmin;
-- dbt roles
CREATE OR REPLACE ROLE dbt_dev_role;
CREATE OR REPLACE ROLE dbt_prod_role;
------------------------------------------- Please replace with your dbt user password
CREATE OR REPLACE USER dbt_user PASSWORD = "<mysecretpassword>";

GRANT ROLE dbt_dev_role,dbt_prod_role TO USER dbt_user;

-------------------------------------------
-- dbt objects
-------------------------------------------
USE ROLE sysadmin;

CREATE OR REPLACE WAREHOUSE dbt_dev_wh  WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 1 INITIALLY_SUSPENDED = TRUE;
CREATE OR REPLACE WAREHOUSE dbt_prod_wh WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 1 INITIALLY_SUSPENDED = TRUE;
GRANT ALL ON WAREHOUSE dbt_dev_wh  TO ROLE dbt_dev_role;
GRANT ALL ON WAREHOUSE dbt_dev_heavy_wh  TO ROLE dbt_dev_role;
GRANT ALL ON WAREHOUSE dbt_prod_wh TO ROLE dbt_prod_role;
GRANT ALL ON WAREHOUSE dbt_prod_heavy_wh  TO ROLE dbt_prod_role;

CREATE OR REPLACE DATABASE dbt_hol_dev; 
CREATE OR REPLACE DATABASE dbt_hol_prod; 
GRANT ALL ON DATABASE dbt_hol_dev  TO ROLE dbt_dev_role;
GRANT ALL ON DATABASE dbt_hol_prod TO ROLE dbt_prod_role;
GRANT ALL ON ALL SCHEMAS IN DATABASE dbt_hol_dev   TO ROLE dbt_dev_role;
GRANT ALL ON ALL SCHEMAS IN DATABASE dbt_hol_prod  TO ROLE dbt_prod_role;
```

As result of these steps, we should have:
-  two empty databases: PROD, DEV
-  two separate virtual warehouses: one for prod, one for dev workloads
-  a pair of separate roles and one user

Please note, this set up is simplified for the purpose of the lab. 
There are many ways environments, roles, credentials could be modelled to fit your final requirements. 

We would suggest having a look at these articles for inspiration: [How we configure Snowflake by Fishtown Team](https://blog.getdbt.com/how-we-configure-snowflake/), [Model Structure by GitLab team](https://about.gitlab.com/handbook/business-technology/data-team/platform/dbt-guide/#model-structure)

<!-- ------------------------ -->
## dbt Configuration 
Duration: 10

### Initialise dbt project

Create a new dbt project in any local folder by running the following commands:

```Shell
$ dbt init dbt_hol
$ cd dbt_hol
```

### Configure dbt/Snowflake profiles 

1. Open  `~/.dbt/profiles.yml` in text editor and add the following section

```yml
dbt_hol:
  target: dev
  outputs:
    dev:
      type: snowflake
      ######## Please replace with your Snowflake account name
      account: <your_snowflake_trial_account>
      
      user: dbt_user
      ######## Please replace with your Snowflake dbt user password
      password: <mysecretpassword>
      
      role: dbt_dev_role
      database: dbt_hol_dev
      warehouse: dbt_dev_wh
      schema: public
      threads: 200
    prod:
      type: snowflake
      ######## Please replace with your Snowflake account name
      account: <your_snowflake_trial_account>
      
      user: dbt_user
      ######## Please replace with your Snowflake dbt user password
      password: <mysecretpassword>
      
      role: dbt_prod_role
      database: dbt_hol_prod
      warehouse: dbt_prod_wh
      schema: public
      threads: 200
```

2. Open `dbt_project.yml` (in dbt_hol folder) and update the following sections:

![dbt_project.yml](assets/image3.png)  

### Validate the configuration
Run the following command (in dbt_hol folder): 

```Shell
$ dbt debug
```
The expected output should look like this, confirming that dbt was able to access the database: 
![dbt debug output](assets/image4.png)  

### Test run
Finally, lets run the sample models that comes with dbt templates by default to validate everything is set up correctly. 
For this, please run the following command (in dbt_hol folder):
```Shell
$ dbt debug
```
The expected output should look like this, confirming dbt was able to connect and successfully run sample models: 
![dbt run output](assets/image5.png)  
Please note, this operation is completely rerunable and does not provide any harm to our next steps in the lab.

You can use Snowflake worksheets to validate that the sample view and the table are now availble in DEV database: 
![Snowflake UI](assets/image6.png)  


Congratulations! You just run your first dbt models on Snowflake! 

<!-- ------------------------ -->
## Architecture and Use Case Overview
Duration: 2

In this lab, we are going to analyse historical trading performance of a company that has trading desks spread across different regions. As inputs, we are going to leverage datasets available in Knoema Economy Data Atlas that is available in Snowflake Data Marketplace, plus few manual uploads. 

We are going to set up the environments from scratch, build scalable pipelines in dbt, establish data tests, and Snowflake and promote code to production.  Finally we will use Snowsight to build a simple dashboard to visualize the results. 

![Architecture ](assets/image7.png)  

Just to give you a sneak peek, this is where we are going to be in just 30 minutes.

Stay tuned!

![dbt target view ](assets/image21.png)  

<!-- ------------------------ -->
## Connect to Data Sources
Duration: 10

Let's go to the Snowflake Data Marketplace and find what we need. The Data Marketplace lives in the new UI called Snowsight (currently in Preview mode but feel free to test drive after the lab). Click on Preview App at the top of the UI

![Preview App](assets/image9.png)  

Click Sign in to continue. You will need to use the same user and pw that you used to login to your Snowflake account the first time.

![Preview App](assets/image11.png)  

You're now in the new UI - Snowsight. It's pretty cool - with charting and dashboards and context-sensitivity - but today we're just focused on getting to the Data Marketplace. Click on Data...

![Preview App](assets/image14.png)  

...and then Marketplace...

![Preview App](assets/image12.png)  

..and now you're in! Hundreds of providers have made datasets available for you to enrich your data. Today we're going to grab a Knoema Economy Atlas Data. Click the Ready to Query checkbox and then find the Knoema Economy Atlas Data tile. Once you find it, click on it.

![Preview App](assets/image13.png)  
Here you'll find a description of the data, example queries, and other useful information. Let's get this data into our Snowflake account. You'll be amazed at how fast and easy this is. Click the "Get Data" button

![Preview App](assets/image15.png)  

In the pop-up, leave the database name as proposed by default (important!), check the "I accept..." box and then add PUBLIC role to the additional roles 

![Preview App](assets/image16.png)  

What is happening here? Knoema has granted access to this data from their Snowflake account to yours. You're creating a new database in your account for this data to live - but the best part is that no data is going to move between accounts! When you query you'll really be querying the data that lives in the Knoema account. If they change the data you'll automatically see those changes. No need to define schemas, move data, or create a data pipeline either. Isn't that slick?

![Preview App](assets/image17.png)  

Now lets go back to worksheets and after refreshing the database browser and notice you have a new shared database, ready to query and join with your data. Click on it and you'll see views under the ECONOMY schema. We'll use one of these next.

![Preview App](assets/image18.png) 

As you would see, this Economy Atlas comes with more than 300 datasets. In order to improve navigation, provider kindly supplied a table called DATASETS. Lets find the ones related to the stock history and currency exchange rates that we are going to use in the next step.

```SQL
SELECT * 
  FROM "KNOEMA_ECONOMY_DATA_ATLAS"."ECONOMY"."DATASETS"
 WHERE "DatasetName" ILIKE 'US Stock%'
    OR "DatasetName" ILIKE 'Exchange%Rates%';
```

![Preview App](assets/image19.png) 

Finally, lets try to query one of the datasets: 
```
SELECT * 
  FROM KNOEMA_ECONOMY_DATA_ATLAS.ECONOMY.USINDSSP2020
 WHERE "Date" = current_date();
```
![Preview App](assets/image20.png) 

Congratulations! You successfully tapped into live data feed of Trade and FX rates data with NO ETL involved. As we promissed. Isn't it cool? 
Now lets start building our pipelines. 

<!-- ------------------------ -->
## Building dbt Data Pipelines
Duration: 30

In this section, we are going to start building our dbt pipelines:

- Stock trading history
- Currency exchange rates
- Trading books
- Profit & Loss calculation

### Configuration
We are going to start by adding few more things to our dbt project configuration in order to improve maintainability. 
1. **Model folders/layers**. From our dbt project folder location, lets run few command line commands to create separate folders for models, representing different logical levels in the pipeline: 

```cmd
mkdir models\l10_staging
mkdir models\l20_transform
mkdir models\l30_mart
mkdir models\tests
```

Then lets open our dbt_profile.yml and modify the section below to reflect the model structure. As you can see, this is allowing you to set multiple parameters on the layer level (like materialization in this example). Also, you would notice that we added ***+enabled: false*** to the ***examples*** section as we won't need to run those sample models in the final state.

![Preview App](assets/image22.png) 

2. **Custom schema naming macros.**
By default, dbt is [generating a schema name](https://docs.getdbt.com/docs/building-a-dbt-project/building-models/using-custom-schemas) by appending it to the target schema environment name(dev, prod). In this lab we are going to show you a quick way to override this macro, making our schema names to look exactly the same between dev and prod databases. For this, lets create a file **macros\call_me_anything_you_want.sql** with the following content:

```YAML
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}


{% macro set_query_tag() -%}
  {% set new_query_tag = model.name %} {# always use model name #}
  {% if new_query_tag %}
    {% set original_query_tag = get_current_query_tag() %}
    {{ log("Setting query_tag to '" ~ new_query_tag ~ "'. Will reset to '" ~ original_query_tag ~ "' after materialization.") }}
    {% do run_query("alter session set query_tag = '{}'".format(new_query_tag)) %}
    {{ return(original_query_tag)}}
  {% endif %}
  {{ return(none)}}
{% endmacro %}
```

![Preview App](assets/image23.png) 

3. **Query Tag**. As you might notice, in the screenshot above there is another macro overriden in the file: **set_query_tag()**. This one provides the ability to add additional level of transparency by automatically setting Snowflake query_tag to the name of the model it associated with. 

So if you go in Snowflake UI and click 'History' icon on top, you are going to see all SQL queries run on Snowflake account(successfull, failed, running etc) and clearly see what dbt model this particular query is related to: 

![Query Tag](assets/image24.png) 

### Stock trading history
1. 
- generated data
- dbt seed

<!-- ------------------------ -->
## Establish Data Testing, Documentaion
Duration: 10
- dbt tests overview
- basic tests
- custom tests

<!-- ------------------------ -->
## Deploying models, materialization options
Duration: 10
- different targets
- view, table, table incremental
- hooks
- snowflake scale up/out

<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 2

Congratulations on completing this lab using dbt and Snowflake for building data pipelines to drive analytics! You’ve mastered the dbt and Snowflake basics and are ready to apply these fundamentals to your own data. Be sure to reference this guide if you ever need a refresher.

We encourage you to continue with your free trial by loading your own sample or production data and by using some of the more advanced capabilities of dbt and Snowflake not covered in this lab. 
### Additional Resources:

- Read the [Definitive Guide to Maximizing Your Free Trial](https://www.snowflake.com/test-driving-snowflake-the-definitive-guide-to-maximizing-your-free-trial/) document
- Attend a [Snowflake virtual or in-person event](https://www.snowflake.com/about/events/) to learn more about our capabilities and customers
- [Join the Snowflake community](https://community.snowflake.com/s/topic/0TO0Z000000wmFQWAY/getting-started-with-snowflake)
- [Sign up for Snowflake University](https://community.snowflake.com/s/article/Getting-Access-to-Snowflake-University)
- [Contact our Sales Team](https://www.snowflake.com/free-trial-contact-sales/) to learn more
- [Join dbt community slack](https://community.getdbt.com/) where thousands of dbt on Snowflake users discussing their best practices

### What we've covered:

- How to set up dbt & Snowflake

- How to leverage data in Snowflake's Data Marketplace 

- How to run a dbt project and develop pipelines

- How to create data tests

- How to leverage Snowflake elasticity and scalability to support dbt calculations at scale


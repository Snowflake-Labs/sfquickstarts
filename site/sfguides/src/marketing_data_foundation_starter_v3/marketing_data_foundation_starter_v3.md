author: Manuel Figueroa, Joviane Bellegarde
id: marketing_data_foundation_starter_v3
summary: Marketing Data Foundation Starter Guide V3
categories: Marketing
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Marketing, Data Engineering, Native Application

# Marketing Data Foundation Starter Guide V3
<!-- ------------------------ -->
## Overview 

Duration: 15

Customers looking to use Snowflake for marketing use cases initially face a significant challenge: it is difficult to import all relevant marketing data into Snowflake and structure it in a unified format that downstream applications can easily utilize to power data-driven marketing. This starter solution tackles this challenge by offering an integrated application that unifies data sets from different Connectors and Marketing Data providers.

In this example we are adding support for 
- Fivetran / Facebook Ads
- Omnata / LinkedIn Ads

This solution was inspired by how Snowflake runs its own end-to-end Marketing workflows entirely on top of the Snowflake Marketing Data Cloud.

In the fast-evolving marketing landscape, the emphasis on data-driven strategies has become more pronounced than ever. A significant trend is the increase in Martech investments, with 63% of Chief Marketing Officers (CMOs) planning to increase their spending within the next 12 months. Such investments are crucial for enhancing customer engagement, refining marketing strategies, and driving sales through advanced data analysis. The high ROI that businesses achieve from data-driven personalization also highlights its importance. Reports indicate that enterprises see returns of 5 to 8 times on their marketing budgets, which demonstrates the value of personalized marketing in boosting conversion rates, enhancing customer loyalty, and increasing revenue.

Additionally, the industry is shifting towards first-party data ownership, a move propelled by the deprecation of third-party cookies. This shift is essential for maintaining direct customer relationships and adapting to changing privacy norms. The promise of generative AI and the understanding that an effective AI strategy requires a robust data strategy have spurred efforts to centralize marketing data within Snowflake. Organizations aim to organize data into standard schemas that Large Language Models (LLMs) can understand, employing these models in innovative ways to personalize content and predict customer behavior. Two types of first-party data are pivotal in these efforts: Customer 360 Data and Campaign Intelligence. The former strives to provide a holistic view of the customer by integrating and managing comprehensive data. In contrast, Campaign Intelligence focuses on data related to marketing campaigns, aiming to optimize performance and strategy. These elements are fundamental to successful data-driven marketing, underscoring the need for sophisticated data management and analytics capabilities.

## Context
As described in the diagram below, the two Data Foundation use cases in this starter lay the groundwork to support the two Marketing Execution use cases: Planning & Activation, and Measurement.

As described in the diagram below, the two Data Foundation use cases in this starter lay the groundwork to support the two Marketing Execution use cases: Planning & Activation, and Measurement.
![overview](assets/context.png)

More specifically, this solution covers Data Ingestion, Semantic Unification, and based Analytics use cases for Customer 360 and Campaign Intelligence data.
![overview](assets/context2.png)

## What You Will Build
- A Native Application that ingests data from different sources and unifies it into a single source of truth for Marketing Data.

## What You Will Learn
- How to build a native application in Snowflake and how to deploy the same to your account using Snow CLI quickly.
- How to use Snowpark Python to build a data pipeline that ingests data from different sources and unifies it into a single source of truth for Marketing Data.

## Prerequisites
- A [GitHub](https://github.com/) Account
- [VSCode](https://code.visualstudio.com/download) Installed
- [Snow CLI](https://docs.snowflake.com/developer-guide/snowflake-cli/index) Installed
- [Python](https://www.python.org/downloads/) Installed

<!-- ------------------------ -->
## The App Architecture

This solution consists of 2 individual solutions.

### Data Foundation Starter for Customer 360

![C360 Architecture](assets/Detailed_Arch-Customer72.png)

### Data Foundation Starter for Campaign Intelligence

![C360 Architecture](assets/Detailed-Arch-Marketing72.png)


<!-- ------------------------ -->
## Setup

### Clone GitHub repository
Duration: 2

Clone the git repo to your local

```console
git clone https://github.com/Snowflake-Labs/sfguide-marketing-data-foundation-starter.git
```

### Create a connection

Run the below command and provide your account details.

```console
snow connection add
```


Test your connection by running the below command

```console
snow connection test --connection="marketing_demo_conn"
```

Refer to the screenshot below for more info.


![Alt text](assets/Snowconnection-create-test.png)


## Create Database objects

Duration: 2

Navigate to the repo folder in your local machine and run the below command to create your database, schema and stage objects

First lets export the connection name to the default connection

```console
export SNOWFLAKE_DEFAULT_CONNECTION_NAME=marketing_demo_conn
```

```console
cd sfguide-marketing-data-foundation-starter
```

```console
snow sql -f sql_scripts/setup.sql
```

![Alt text](assets/run-setup-script.png)

## Upload sample data to stage

Duration: 4

Upload all the sample data files in the folder data to the stage created in step 1


```console
snow stage copy data/worldcities.csv @MARKETING_DATA_FOUNDATION.demo.data_stg/data
```

```console
snow stage copy data/sf_data/ @MARKETING_DATA_FOUNDATION.demo.data_stg/data/sf_data/ --parallel 10
```

```console
snow stage copy data/ga_data/ @MARKETING_DATA_FOUNDATION.demo.data_stg/data/ga_data/ --parallel 20
```

```console
snow stage copy data/sample_data.gz @MARKETING_DATA_FOUNDATION.demo.data_stg/data/
```

![Alt text](assets/Upload-to-Stage.png)


If the upload fails due to an access issue then, please follow the instructions in this [document](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-stage-ui) to upload the files directly to Snowflake Stage.


## Load Sample data to the table and Create a Native Application

Duration: 2

### Load data and create views

Run the below command to create the views that will be bundled along with the native app

```console
snow sql -f sql_scripts/build_views.sql
```

### Build NativeApp

```console
snow app run
```

![Alt text](assets/Appcreation.png)


## [Quick-deploy] Build and Deploy App in one go

Duration: 2

Please **DO NOT** run this step if you have completed individual steps above. This step is for users to quickly run all the snow cli commands in one go.

```sh
bash ./sfguide-marketing-data-foundation-starter/build_deploy_app.sh
```

![Alt text](assets/Appcreation.png)

## Conclusion and Resources
Duration: 1

Congratulations! You have successfully learned how to easily build an end-to-end Native Application loading sample data. 

### What you learned

* How to build a native application in Snowflake and how to deploy the same to your account using Snow CLI quickly.

### Related Resources

Want to learn more about the tools and technologies used by your app? Check out the following resources:

* [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-marketing-data-foundation-starter)
* [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
* [Snowpark Guide for Data Engineers](https://www.snowflake.com/resource/the-data-engineers-guide-to-python-for-snowflake/)
* [Getting Started with Snow CLI](https://quickstarts.snowflake.com/guide/getting-started-with-snowflake-cli/index.html#0)

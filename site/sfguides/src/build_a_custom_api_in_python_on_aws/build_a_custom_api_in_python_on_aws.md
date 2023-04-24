author: Brad Culberson
id: build_a_custom_api_in_python_on_aws
summary: A guide to building and running a custom API (in Python) Powered by Snowflake and AWS
categories: getting-started,app-development,architecture-patterns,solution-examples
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, API

# Build a Custom API in Python on AWS

## Overview 
Duration: 5

Many builders want to share some of the data stored in Snowflake over an http API. Modern mobile and web applications often want to retrieve that data through http APIs. This tutorial will go through how to build, deploy, and host a custom API Powered by Snowflake.

This API consists of reporting endpoints from data stored in Snowflake. [Serverless Framework](https://www.serverless.com/) was used to build and deploy the application for simplicity of operation and ease of scaling.

After completing this guide, you will have built, tested, and deployed a custom API built with [Python Flask](https://flask.palletsprojects.com/en/2.0.x/), [Serverless Framework](https://www.serverless.com/), and [AWS](https://aws.amazon.com/) Lambda/API Gateway. 

The dataset is the same as used in the [Building a Data Application](https://quickstarts.snowflake.com/guide/data_app/index.html) guide.

### Prerequisites
- Privileges necessary to create a user, database, and warehouse in Snowflake
- Privileges necessary to create an API Gateway and Lambda in Amazon Web Services
- Ability to install and run software on your computer
- Basic experience using git and editing yml
- Intermediate knowledge of Python

### What You’ll Learn 
- How to configure and build a custom API Powered by Snowflake
- How to deploy a custom API on AWS serverless technologies
- How to test and monitor the API

### What You’ll Need 
- [AWS](https://aws.amazon.com) Account
- [GitHub](https://github.com/) Account
- [Serverless.com](https://serverless.com) Account 
- [Docker](https://docs.docker.com/get-docker/) Installed
- [VSCode](https://code.visualstudio.com/download) Installed
- DATA_APPS_DEMO database and key pair for service user DATA_APPS_DEMO from first 4 steps of [Building a Data Application](https://quickstarts.snowflake.com/guide/data_app/index.html)
- [NodeJS](https://nodejs.org/en/download/) Installed
- [Serverless Framework](https://www.serverless.com/framework/docs/providers/aws/guide/installation) Installed
- [Python 3](https://www.python.org/) Installed
- [Virtualenv](https://virtualenv.pypa.io/en/latest/installation.html) Installed
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) Installed and [Configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
- [jq](https://stedolan.github.io/jq/) Installed

### What You’ll Build 
- API Powered by Snowflake

## Downloading the Code
Duration: 3

The code used in this guide is hosted in github. You can download the code as a ZIP from [GitHub](https://github.com/Snowflake-Labs/sfguide-snowflake-python-api) or use the following git command to clone the repository.

```bash
git clone https://github.com/Snowflake-Labs/sfguide-snowflake-python-api.git
```

After downloading you will have a folder sfguide-snowflake-python containing all the code needed for the API. Open the folder in VSCode to review the project.

The connector.py contains all the entrypoints for the API endpoints using the Snowflake Python connector. The get_trips_monthly function is one of the API endpoints we needed
for this API which pulls the trips completed aggregated by month. Review the code and the SQL needed to retrieve the data from Snowflake and serialize it to JSON for the response. This endpoint also takes 2 optional query string parameters start_range and end_range.

```python
@connector.route("/trips/monthly")
@api_response
def get_trips_monthly():
    start_range = request.args.get('start_range')
    end_range = request.args.get('end_range')
    if start_range and end_range and params_valid(start_range, end_range):
        sql = f"select COUNT(*) as trip_count, MONTHNAME(starttime) as month from demo.trips where starttime between '{start_range}' and '{end_range}' group by MONTH(starttime), MONTHNAME(starttime) order by MONTH(starttime);"
        return exec_and_fetch(sql)
    sql = "select COUNT(*) as trip_count, MONTHNAME(starttime) as month from demo.trips group by MONTH(starttime), MONTHNAME(starttime) order by MONTH(starttime);"
    return exec_and_fetch(sql)
```

You can also review the other endpoints in [connector.py](https://github.com/Snowflake-Labs/sfguide-snowflake-python-api/blob/main/connector.py) to see how simple it is to host multiple endpoints.

If you would also like to see how to build endpoints using the Snowflake SQL API, review [sqlapi.py](https://github.com/Snowflake-Labs/sfguide-snowflake-python-api/blob/main/sqlapi.py).

## Configuring the Application
Duration: 3

The config.py file is setup to configure the application from environment variables. These environment variables will be set for the lambda in AWS by the Serverless Framework automatically.

Copy the serverless-template.yml to serverless.yml. Update the serverless.yml to name your service by replacing <NAME_OF_YOUR_SERVICE> and update your Snowflake account in both places that have <ACCOUNT> (SNOWFLAKE_ACCOUNT and SNOWFLAKE_PRIVATE_KEY). This Snowflake account must be the same one used for the [Building a Data Application](https://quickstarts.snowflake.com/guide/data_app/index.html) guide as we will be using the same database and user. If you haven't completed the first 4 steps of that guide, do so before continuing.

Modify the region in the serverless.yml (line 17) to the same region as your credentials.

```bash
aws configure get region
```

This project expects the private key to be stored in SSM. To upload the private key, run the following replacing <ACCOUNT> with the same Snowflake account used in serverless.yml:

```bash
aws ssm put-parameter --name <ACCOUNT>.DATA_APPS_DEMO --type "String" --value "`cat ~/.ssh/snowflake_demo_key`"
```

Verify the private key was uploaded correctly:

```bash
aws ssm get-parameter --name <ACCOUNT>.DATA_APPS_DEMO
```

## Configuring, Packaging, and Testing
Duration: 5

Serverless login will open a browser to authenticate the serverless tool. When running serverless, it will ask you what org to add it to. You can choose the default or any org you have setup in serverless.com. You can also keep the original snowflake-python-api name for the application or give it a new name. When asked to deploy the application, choose No.

```bash
npm install
serverless login
serverless
```

After this is complete, Serverless Framework is configured for use.

Before we deploy the application, we should test locally. For local development, we will isolate the python dependencies in user space using virtualenv. 

Create a virtualenv locally and install python packages.

```bash
virtualenv venv --python=python3
source ./venv/bin/activate
pip install -r requirements.txt
```

You can now start the local serverless server which hosts the API.

```bash
sls wsgi serve
```

To verify the API is working properly you can hit the 3 API endpoints:

```bash 
curl "http://localhost:5000/trips/monthly" | jq
curl "http://localhost:5000/trips/day_of_week" | jq
curl "http://localhost:5000/trips/temperature" | jq
```

If these endpoints are not working and you are on macOS, make sure [port 5000 is not in use](https://www.reddit.com/r/webdev/comments/qg8yt9/apple_took_over_port_5000_in_the_latest_macos/). 

To test the query string parameters you can use the following:

```bash
curl "http://localhost:5000/trips/monthly?start_range=2013-06-01&end_range=2013-07-31" | jq
```

These curl commands will return data in JSON format which was pulled from Snowflake using the SQL queries in app.py.

You can also open these uris in a browser if that's preferred.

## Deploying the API
Duration: 3

Now that the application and configuration is verfied to be working, you can deploy it to AWS by running the following command:

```bash
serverless deploy
```

After the completion of deployment, serverless info will give you the URI where your API is now hosted.

```bash
serverless info
```

You can now do the same tests you did locally on the now publicly available API. Replace the server uri with your API location.

```bash 
curl "http://<DEPLOYMENT>.execute-api.<REGION>/dev/trips/monthly" | jq
curl "http://<DEPLOYMENT>.execute-api.<REGION>/dev/trips/day_of_week" | jq
curl "http://<DEPLOYMENT>.execute-api.<REGION>/dev/trips/temperature" | jq
```

To test the query string parameters you can use the following:

```bash
curl "http://<DEPLOYMENT>.execute-api.<REGION>/dev/trips/monthly?start_range=2013-06-01&end_range=2013-07-31" | jq
```

Your api is now available for use by your mobile and web applications.

## Monitoring your API with Serverless Framework
Duration: 3

You can monitor your application directly by logging into serverless.

```bash
sls login
```

The serverless console allows you to easily view requests to the API as well as errors. The overview and api endpoints tabs allow you to view requests, errors, and latencies for your API. The explorer is useful to look at logs of each request.

If you are more familiar with the AWS Console this same information is available in Cloudwatch Metrics and Logs.


## Cleanup
Duration: 1

If you are done with this exercise you can remove all aws resources by having Serverless Framework cleanup.

```bash
serverless remove
```

## Conclusion
Duration: 1

You've successfully built, tested, and deployed a custom API on AWS Powered by Snowflake. The serverless stack from AWS is a great way to quickly and easily build a powerful API with little operational overhead. It's also very cost effective for most uses.

Right now this is a public API and is accessible to anyone on the internet. If you have a need to authenticate your users you should check out [Amazon Cognito](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html). You can also use [custom authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html) in lambda or [AWS IAM](https://docs.aws.amazon.com/apigateway/latest/developerguide/permissions.html) to restrict access.

To get more comfortable with this solution, implement new endpoints pointing to the sample dataset provided or other datasets.

We will be posting more guides in the future on building custom APIs, Powered by Snowflake, in other languages and other cloud providers. Please check back for more guides.

Code for this project is available at [https://github.com/Snowflake-Labs/sfguide-snowflake-python-api](https://github.com/Snowflake-Labs/sfguide-snowflake-python-api).

### What we've covered
- How to build, configure and package a custom API Powered by Snowflake
- How to test the API locally
- How to deploy a custom API on AWS serverless technologies
- How to test and monitor the API in AWS

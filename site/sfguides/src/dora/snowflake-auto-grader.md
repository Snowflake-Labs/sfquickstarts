author: Gilberto Hernandez
id: snowflake-auto-grader
summary: In this guide, you'll set up Snowflake's Auto-Grader.
categories: Getting-Started
environments: web
status: Hidden 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# How to Setup the Snowflake Auto-Grader
<!-- ------------------------ -->
## Overview 
Duration: 0

In this guide, you'll learn how to setup Snowflake's auto-grader.

The auto-grader runs in your Snowflake account and can be used to check successful completion of tasks within a Snowflake account.


### What You’ll Learn 
- How to setup the auto-grader


### What You’ll Need 
- A Snowflake account

<!-- ------------------------ -->
## Create the API integration
Duration: 2

In your Snowflake account, open a new SQL worksheet and run the following code:

```sql
use role accountadmin;

create or replace api integration dora_api_integration 
api_provider = aws_api_gateway 
api_aws_role_arn = 'arn:aws:iam::321463406630:role/snowflakeLearnerAssumedRole' 
enabled = true 
api_allowed_prefixes = ('https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora');
```

This code will create an API integration in your Snowflake account under the `ACCOUNTADMIN` role. To confirm that the integration was created, you can run the following:

```sql
show integrations;
```

If the integration was successfully created, you should see output similar to the following:

| **name**             | **type**     | **category** | **enabled** | **comment** | **created_on**                |
|----------------------|--------------|--------------|-------------|-------------|-------------------------------|
| _API_INTEGRATION | EXTERNAL_API | API          | true        |             | 2023-02-03 12:36:22.470 -0700 |



<!-- ------------------------ -->
## Create the `grader` function
Duration: 2

Next, create the `grader` function. This function will be used for grading (i.e., validating the successful completion of steps or tasks in the account).

Run the following code in new SQL worksheet:

```sql
use role accountadmin;

create database util_db;

create or replace external function util_db.public.grader(        
 step varchar     
 , passed boolean     
 , actual integer     
 , expected integer    
 , description varchar) 
 returns variant 
 api_integration = dora_api_integration 
 context_headers = (current_timestamp,current_account, current_statement) 
 as 'https://awy6hshxy4.execute-api.us-west-2.amazonaws.com/dev/edu_dora/grader'  
;  
```

The `grader` function will be located in the `UTIL_DB.PUBLIC` schema in your account. If you don't see the function, please refresh the objects in the **Databases** section of your account. In addition, ensure you are using the `ACCOUNTADMIN` role.

![refresh picker](./assets/picker-refresh.png)

<!-- ------------------------ -->
## Confirm that the auto-grader is provisioned correctly
Duration: 1

To confirm that the auto-grader is functioning as intended, open a new SQL worksheet and run the following code:

```sql
use role accountadmin;
use database util_db;
use schema public;

select grader(step, (actual = expected), actual, expected, description) as graded_results from (SELECT
 'DORA_IS_WORKING' as step
 ,(select 123) as actual
 ,123 as expected
 ,'Dora is working!' as description
);
```

If the auto-grader is correctly provisioned, you should see a **GRADED_RESULTS** column with several pieces of information, including a checkbox and a message `"description": "Dora is working!"`.
<!-- ------------------------ -->
## Conclusion
Duration: 1

That's it! You should now have the auto-grader correctly provisioned in your account. When grading Quickstarts, you'll need to invoke the auto-grader via steps specific to that Quickstart. Be sure to follow any specific steps corresponding to the Quickstart.

Resources:

- [Snowflake Auto-Grader](https://learn.snowflake.com/news)

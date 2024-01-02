author: Tim Buchhorn
id: data_collaboration_two_way
summary: This is a Snowflake Guide on how to use Snowflake's Data Collaboration features to share an enrich data. 
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Two Way Data Collaboration
<!-- ------------------------ -->
## Overview 
Duration: 1

This guide will take you through Snowflake's Collaboration features, and highlight how easy it is to share data between two organisations.

It also highlights Snowflakes ability to host a ML Model, score data from shared data, and share the enriched (scored) data back to the original Provider. Hence, it is a 2-way sharing relationship, where both accounts are Providers and Consumers.

### Prerequisites
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
    **Download the git repo here: insert repo**
- [Anaconda](https://www.anaconda.com/) installed
- [Python 3.9](https://www.python.org/downloads/) installed
    - Note that you will be creating a Python environment with 3.9 in the **Setup the Python Environment** step
- Snowflake accounts with [Anaconda Packages enabled by ORGADMIN](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#using-third-party-packages-from-anaconda). If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/).
- A Snowflake account login with a role that has the ability to create database, schema, tables, stages, user-defined functions, and stored procedures. If not, you will need to register for free trials or use a different role.

### What You’ll Learn
- How to become a Provider in Snowflake Marketplace (Private Listings)
- How to Consume a shared private asset in the Snowflake Marketplace
- How to Deploy a ML Model in Snowflake
- How to share seamlessly between two Snowflake Accounts 

### What You’ll Need 
- Two [Snowflake](https://signup.snowflake.com/) Accounts in the same cloud and region 

### What You’ll Build 
- Ingestion of Credit Card Customer Profile Data
- Sharing raw data seamlessly via a private listing
- Consuming shared data via a private listing
- Enriching shared data using a ML model
- Sharing back enriched data to the original Provider account

<!-- ------------------------ -->
## Business Use Case
Duration: 2

In this hands-on-lab, we are playing the role of a bank. The Credit Risk team has noticed a rise in credit card default rates which affects the bottom line of the business. It has employed the help of an external organisation to score the credit card default risk of their existing customers, based on a series of attributes in categories such as spending, balance, delinquency, payment and risk. The data needs to be shared between the two parties.

Both companies have chosen to use Snowflake. The advantages of doing this are:
- Low latency between the Provider and Consumer accounts
- The files stay within the security perimeter of Snowflake, with Role Based Access Control (RBAC)

Below is a schematic of the data share
![Diagram](assets/two_way_data_collaboration.png)

### Dataset Details

The dataset contains aggregated profile features for each customer at each statement date. Features are anonymized and normalized, and fall into the following general categories:

D_* = Delinquency variables
S_* = Spend variables
P_* = Payment variables
B_* = Balance variables
R_* = Risk variables

### Dataset Citation

Addison Howard, AritraAmex, Di Xu, Hossein Vashani, inversion, Negin, Sohier Dane. (2022). American Express - Default Prediction. Kaggle. https://kaggle.com/competitions/amex-default-prediction

<!-- ------------------------ -->
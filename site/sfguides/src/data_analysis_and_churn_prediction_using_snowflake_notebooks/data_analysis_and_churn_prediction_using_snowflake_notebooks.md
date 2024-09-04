author: Joviane Bellegarde
id: data_analysis_and_churn_prediction_using_snowflake_notebooks
summary: Data Analysis and Churn Prediction Using Snowflake Notebooks
categories: Churn, Prediction, Getting-Started
environments: web
status: Unpublished
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Churn, Prediction, Notebooks

# Data Analysis and Churn Prediction Using Snowflake Notebooks
<!-- ------------------------ -->

## Overview
Duration: 2
<img src="assets/banner.png"/>

Churn prediction relies on data analysis to be effective. Through data analysis, businesses gather, clean, and model customer data to uncover patterns and trends. This understanding of customer behavior is key for building accurate churn prediction models. By applying data analysis techniques, businesses can identify at-risk customers and take targeted actions to retain them. Essentially, data analysis provides the necessary foundation for effective churn prediction, helping businesses reduce churn and boost customer loyalty.

In this Quickstart, we will play the role of a data scientist at a telecom company that wants to identify users who are at high risk of churning. To accomplish this, we need to build a model that can learn how to identify such users. We will demonstrate how to use Snowflake Notebooks in conjunction with Snowflake/Snowpark to build a Random Forest Classifier to help us with this task.

This Quickstart uses Snowflake Notebooks to import and load data, train a Random Forest with Snowpark ML model, visualize the predicted results from the forcasting model by building an interactive web application and make predictions on new users.

### What You Will Learn
We will implement price optimization for their diversified food-truck brands to inform their pricing and promotions by utilizing **Snowflake Notebooks** and **Streamlit** to:
- Train & deploy an ML model to understand how menu-item demand changes with varying price
- Create a user-friendly application to use deployed ML-model to inform pricing strategies

### Prerequisites
- A Supported Snowflake [Browser](https://docs.snowflake.com/en/user-guide/setup#browser-requirements)
- A Snowflake Account
    - If you do not have a Snowflake Account, please [**sign up for a Free 30 Day Trial Account**](https://signup.snowflake.com/). When signing up, please make sure to select **Enterprise** edition. You can choose any AWS or Azure [Snowflake Region](https://docs.snowflake.com/en/user-guide/intro-regions).
    - After registering, you will receive an email with an activation link and your Snowflake Account URL

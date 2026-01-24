summary: PLEASE SHOW MY QUICKSTART
author: Hartland-Snowflake
id: alert-hub
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Snowflake Guide Template
<!-- ------------------------ -->
## Overview 
Duration: 1

This guide is an introduction to Snowflake SIT's Alert Hub. 

The Alert Hub is a rule-based meta-data driven framework for alerts and notifications. It enhances Snowflake's native alerting capabilities by adding a rich GUI and support for Jinja templating. The framework can be tailored through custom condition/action queries or applying query templates that monitor the account objects or any type of events within the account and send out multi-channel notifications.

All sample code is provided for reference purposes only. Please note that this code is provided “AS IS” and without warranty. Snowflake will not offer any support for use of the sample code.

Copyright (c) 2024 Snowflake Inc. All Rights Reserved.

Please see TAGGING.md for details on object comments.

### Prerequisites
- Familiarity with Jinja Templates

### What You’ll Learn 
- How to setup and use the Alert Hub framework made by the SIT team

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- A [Snowflake](https://www.snowflake.com/en/) Account


<!-- ------------------------ -->
## Download
Duration: 2

Please navigate to the github https://github.com/Snowflake-Labs/sfguide-alert-hub/tree/main
and download the code.

<!-- ------------------------ -->
## Install
Duration: 2

Once you have downloaded the code, we need to do a little setup in your snowflake account.
- Open a worksheet in your snowflake account
- Set your role to ACCOUNTADMIN
- Run all of the code inside alert_hub_setup.sql in the worksheet
- If running in SiS copy and paste the code from alert_hub_streamlit.py into a new Streamlit Project, otherwise specify your credentials in the .streamlit/secrets.toml and run 
```
streamlit run alert_hub_streamlit.py
```

<!-- ------------------------ -->
## Make your first Condition
Duration: 2

Now we'll make our first condition! 
- Navigate to the Conditions Page
- Create a New Condition Template and save it
- Create new Conditions by Template and save them
- Check the generated preview and confirm its accuracy!
(examples available in demo.sql and demo.md)
<!-- ------------------------ -->
## Make a Notification Integration
Duration: 2

In order to send out an email on alert, we need an email integration
- Navigate to Notification Integrations
- Choose an Integration type (Email or Queue)
- Enter JSON and save integration!
(example integrations available in demo.sql and demo.md)
<!-- ------------------------ -->
## Specify an Action
Duration: 2

The action that an alert takes is specified next
- Navigate to Actions
- Specify an Action
- Set the parameters for your action template
- Check the generated preview and save!
(example actions available in demo.sql and demo.md)
<!-- ------------------------ -->
## Create your Alert
Duration: 2

All thats left is to make the alert!
- Navigate to Alerts
- Select warehouse, Schedule, Condition, and Action
- Save the Alert!!

Congratulations! Your Alert hub is up and running and you've got your first alert!!
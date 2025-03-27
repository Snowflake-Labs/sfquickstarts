author: 
id: trigger-servicenow-worflow-from-snowflake
summary: Trigger-servicenow-worflow-from-snowflake
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Trigger ServiceNow workflow from Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 1

ServiceNow Workflows automate business processes by defining a series of tasks, approvals, and conditions within the platform. They help streamline IT service management (ITSM), HR, customer service, and other enterprise functions by reducing manual effort and enforcing consistency. Worflows can be triggered manually or automatically based on certains events. In this guide you will learn how to automatically trigger ServiceNow Workflows from Snowflake. 

 

It is important to include on the first page of your guide the following sections: Prerequisites, What you'll learn, What you'll need, and What you'll build. Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial; this means that actual code needs to be included (not just pseudo-code).

The rest of this Snowflake Guide explains the steps of writing your own guide. 

### Prerequisites
- Familiarity with SQL and REST API

### What You’ll Learn 
- how to create a ServiceNow workflow  
- how to define a REST input for the workflow 
- how to securely connect to the ServiceNow Instance from Snowflake
- how to trigger the workflow from Snowflake   


### What You’ll Need 
- A [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) Account 
- A [ServiceNow](https://developer.servicenow.com/dev.do) Personal Developer Instance. 
- In order to create a trigger of type REST API you will need to enable Integration Hub Enterprise Pack Plugin as per this [link](https://developer.servicenow.com/dev.do#!/learn/learning-plans/washingtondc/servicenow_application_developer/app_store_learnv2_rest_washingtondc_exercise_activate_integrationhub)

### What You’ll Build 
- A procedure to trigger workflow in ServiceNow from Snowflake   


### How can you use the solution  
- Customers can seamlessly take action in ServiceNow based on insights from Snowflake.
- For example,
  1. Teams can aggregate infosec data from tools like Bugcrowd, classify CVEs in Snowflake, and automatically create ServiceNow incidents for critical vulnerabilities.
  2. Additionally, Snowflake Cortex ML models can predict component failures based on machine data and create service requests in ServiceNow.   


<!-- ------------------------ -->
## Create the ServiceNow Workflow   
Duration: 3

A  serviceNow workflow consists of a trigger and action. The trigger is used to start the workflow and action defines what the workflow does. In our sample tutorial we will be creating a trigger with an inbound REST request and the action will be creation of an incident record. Let's start with defining a ServiceNow workflow.

1. Go to your  ServiceNow Personal Developer Instance -> All -> Workflow Studio -> Homepage 

2. Select New -> Flow. Define a name for the flow "snowflake-demo". Leave the rest as default. 

![step1-new-flow](assets/step1-new-flow.png)

3. Select a trigger for the flow. Go to Application -> REST API - Asynchronous 

![step1-create-trigger](assets/step1-create-trigger.png)

Select the HTTP Method as "POST" 

Check the box "Requires Authentication" so that only authenticated users can trigger the workflow. 

Go to Body of Request Content and create three new variable 

Category - This will be the category for the incident record 
Description - This will be the description for the incident record 
Work_notes - This will be the work notes section for the incident record

You can optinally add headers section and roles for the REST Request but we will skip that for this tutorial. 

Hit "Done". 

Eventually your Trigger definition should look like this 
![step1-snowflake-trigger](assets/step1-snowflake-trigger.png)

<!-- ------------------------ -->
## Create the Workflow Action    
Duration: 2

Now that we have defined the trigger the next step is to define action for the workflow (create incident record). 
Select Action-> Create Record -> Table (incident)

Add three fields corresponding to the three inputs we defined in the inbound REST Request 
Category, Description & Work notes

For the values of these fields we will use the Data Pill Picker for each field. 
![step2-data-pill-picker](assets/step2-data-pill-picker.png)

Go to data Pill Picker -> Trigger - REST API - Asynchronous -> Request Body ->  Field Name

Once you complete this for all three fields your action definition will look like this.  
![step2-incident-record](assets/step2-incident-record.png)

Hit Done. This completes our workflow definition in ServiceNow. 
The next step will be to create the UDF in Snowflake to call this workflow. 

<!-- ------------------------ -->
## Define the Snowflake function to trigger workflow in ServiceNow 
Duration: 4

In order to connect to the ServiceNow instance from Snowflake we need to define a couple of snowflake primitives. 
Snowflake secret to store the authentication details for ServiceNow instance ie. username/password 
Snowflake external access integration to securely connect to Servicenow from snowflake 
Let's start by creating a snowflake secret followed by creating external access integration 

```sql
CREATE OR REPLACE  SECRET servicenowkey
   TYPE = PASSWORD
  USERNAME = 'admin'
  PASSWORD = '****'
 COMMENT = 'secret for servicenow api access' ;

```

Now we need to define a network rule to based on host to identify the servicenow instance. This network rule will be used in the external access integration definition. 

```sql

  CREATE OR REPLACE NETWORK RULE servicenow_apis_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('dev201625.service-now.com');


  CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION servicenow_apis_access_integration
  ALLOWED_NETWORK_RULES = (servicenow_apis_network_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (servicenowkey)
  ENABLED = true;

```

This completes our connection path to servicenow. Now we need to create a udf that uses this external access integration and calls the REST API to trigger the workflow we defined earlier. The payload of the REST request will include the three parameters for Category, Description and Work Notes to create an incident record. 

```sql 

CREATE OR REPLACE FUNCTION servicenow_action(category String,description String,worknotes String)
RETURNS String
LANGUAGE PYTHON
EXTERNAL_ACCESS_INTEGRATIONS = (servicenow_apis_access_integration)
SECRETS = ('cred' = servicenowkey)
RUNTIME_VERSION = 3.9
HANDLER = 'call_servicenow_flow'
PACKAGES = ('pandas', 'requests')
AS $$

import json
import requests
import _snowflake
from requests.auth import HTTPBasicAuth

session = requests.Session()


def call_servicenow_flow(category,description,worknotes,assignment_group):
    payload={}
# The full path for the REST api endpoint we created in Step 1 
    url = "https://dev201625.service-now.com/api/1551828/snowflake-trigger"

# Optional Headers for the API call if you have defined them in the REST API 
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
        }

# Payload for the POST request
    data = {
        "Category"  : category,
        "Description": description,
        "Work_notes": worknotes 
        }


    # username_password_object = _snowflake.get_username_password('cred');
    username_password_object = _snowflake.get_username_password('cred');
    basic = HTTPBasicAuth(username_password_object.username, username_password_object.password)



    response = session.post(url,headers=headers,json=data,auth=basic)

    if response.status_code == 202:
        json_result=response.json()
        executionId=json_result["result"]["executionId"]
        return executionId
    else:
        error_string="Rest call failed. Please check Servicenow endpoint"
        return (error_string)
$$

```
This completes all the data pipeline we need to put in place to trigger the workflow from snowflake.

<!-- ------------------------ -->
## Execute the workflow 
Duration: 2

The last step is to test our integration. Since we have a UDF defined earlier we can use a simple select statement to call it with input values for the three variables. This will call the function we defined earlier and trigger the workflow on servicenow side to eventually create an incident record. 
The condition to execute the function can be varied depending on the use case and vertical
for eg. In manufacturing we can have a cortex monitor machine data for various metrics such as pressure, temperature, RPM,motor load etc. and if  say the pressure exceeds a certain value -> call the function to trigger a workflow -> creates an incident in ServiceNow, essentially driving insights to action. 


```sql 
select   servicenow_action('Hardware','Triggered by snowflake with exteranl access','Machine pressure too high'); 
```

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

With this quickstart you learned how to automatically trigger a workflow in ServiceNow from Snowflake. Snowflake and ServiceNow offer a powerful opportunity to streamline and enhance business operations by transforming raw data insights into actionable outcomes.  


### What You Learned
- Create a workflow in ServiceNow
- Trigger the workflow from Snowflake 
- Define a reference condition to execute the trigger 

### Related Resources
- [ServiceNow Trigger](https://www.servicenow.com/docs/bundle/xanadu-integrate-applications/page/administer/integrationhub/concept/rest-trigger.html)
- [Snowflake External Access Integration](https://docs.snowflake.com/en/sql-reference/sql/create-external-access-integration)
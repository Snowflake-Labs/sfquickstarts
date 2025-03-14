author: seanyse
id: max_my_cloud
summary: This is a Max My Cloud Installation Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Max-My-Cloud, Data Engineering 
# Max My Cloud Installation Guide
<!-- ------------------------ -->
## Overview 
Duration: 3

MaxMyCloud is a free Snowflake Native App which monitor, analyze, and optimize your Snowflake spending. Our mission is simple: to enable our customers to do more with less in the Snowflake Data Cloud

### Capacity Monitoring

At MaxMyCloud, we believe the first step in cost optimization is proactive monitoring. It’s not just about understanding past expenditures, but also anticipating future costs by the end of the contract. This foresight allows us to take early, proactive measures, preventing budget overruns and avoiding premature contract renewals with Snowflake. Our Contract Monitor page is designed with this goal in mind.

![monitor](assets/capacity_monitoring.png)

### Estabish Departmental Fiscal Responsibility

Many organizations have taken the right step by internally charging back Snowflake costs to various departments. However, because Snowflake billing is at the warehouse level, most organizations are forced to allocate different sizes of warehouses per department. This often leads to workloads being spread too thin, losing the benefits of economies of scale and resulting in higher overall costs for the same workload. MaxMyCloud's proprietary algorithm provides the lowest granular billing at the query level, enabling departmental billing without sacrificing the benefits of economies of scale.

### Anomaly Detection and Root Cause Analysis

​MaxMyCloud can detect pattern changes in Snowflake spending and identify the causes with just a few clicks, thanks to its highly interactive design. It quickly pinpoints which application or user has caused a sudden increase in spending, enabling you to take immediate action to stop monetary leakage.

![anomaly](assets/anomaly_detection.png)

### Warehouse Utilization and Idle Cost Analysis

IDLE Cost occurs when a Snowflake warehouse is running without any active workload. Effective cost management should minimize idle costs without sacrificing performance. MaxMyCloud’s unique design allows our customers to pinpoint exactly where idle costs occur and effortlessly minimize them.

![warehouse](assets/warehouse_utilization.png)

### Excessive Storage Cost

While storage costs are relatively inexpensive compared to compute costs, it's not uncommon for storage usage to exceed actual data size by 100X or even 1,000X. MaxMyCloud identifies these cost-saving opportunities and enforces Snowflake best practices in storage usage.

![storage](assets/storage_costs.png)

### Serverless Cost

In addition to compute and storage costs, MaxMyCloud also monitors serverless costs, including auto-clustering, materialized views, Snowpipe, and search optimization, among others.

### Data Processing/ETL Cost
In many organizations, data processing is the largest Snowflake cost driver. At MaxMyCloud, we closely monitor data processing costs using a two-pronged approach:
1. Identify top tables and focus on their most costly operations for performance tuning.
2. Rationalize data processing patterns by aligning data processing with data retrieval and seeking opportunities to reduce data processing frequency.

### Unused Resources

In today’s world, data democratization allows everyone in an organization to work with data and create their own tables and processes. However, some of these tables may become obsolete over time, while their associated data processes continue running and consuming credits. MaxMyCloud automatically identifies these opportunities for cost savings.

### Optimization Recommendation

MaxMyCloud recommends actionable steps from various areas to optimize your cost.

![optimization](assets/optimization.png)


## Get the Native App
Duration: 3
### Install Native App

MaxMyCloud Native App is a free application available in the [Snowflake Marketplace](https://app.snowflake.com/marketplace). To install it, search for MaxMyCloud and click the blue "Get" button to begin the installation process. 

Once the installation is complete, navigate to Data Products → Apps → Installed Apps, where you will find the MaxMyCloud app. Click on the MaxMyCloud icon → Snowflake_insight to launch the Native App.

![navigate](assets/navigate.png)

During the setup, two Snowflake authorization dialogs will appear, requesting permissions for the Native App. Click "Grant Privileges" to proceed to begin the installation process.

![dialouge](assets/dialouge.png)

The Installation should take approximately 30 seconds, and a green checkmark will confirm a successful install.  Shortly after, the Data Refresh process will start in the backend.

If needed, you can click "Check Status" to monitor the process. The backend process runs independently of the Native App, so you can safely close the app and proceed to the next step.

![installation](assets/installation_success.png)


## Complete Setup
Duration: 10

### Create Snowflake User

Before running the MaxMyCloud web application, you need to set up a role and user in your Snowflake account. Copy the code snippet below and execute it in Snowflake.

### TERMINAL
```terminal 
create role maxmycloud_role;
GRANT APPLICATION ROLE app_maxmycloud TO ROLE maxmycloud_role;
GRANT USAGE ON WAREHOUSE your_warehouse TO ROLE maxmycloud_role;
GRANT USAGE ON INTEGRATION MAXMYCLOUD_API_INTEGRATION TO maxmycloud_role; 
```
Create MaxMyCloud User:

There are two options for creating a MaxMyCloud user:

a. Username and Password – Recommended for initial testing.

b. Key-Pair Authentication – Strongly recommended for production.

Follow the steps below:

### 1. Generate a Key (For Key-Pair Authentication)

This step should be performed on a device within your organization.

a. Generate private key in command line:

### TERMINAL
```terminal 
  openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
```

b.Generate public key in command line:

### TERMINAL 
```
  openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

### 2. Create User

### TERMINAL
```terminal 
CREATE OR REPLACE USER maxmycloud
PASSWORD = ''  -- Ensure no password is allowed
LOGIN_NAME = 'maxmycloud'
DISPLAY_NAME = 'maxmycloud'
DEFAULT_WAREHOUSE = 'your_warehouse'
DEFAULT_ROLE = 'maxmycloud_role'
DISABLED = FALSE;
GRANT ROLE maxmycloud_role TO USER maxmycloud;
```

### 3. Assign User the Public key in Snowflake. 

Replace with your Public key


### TERMINAL
```terminal 
ALTER USER maxmycloud  SET RSA_PUBLIC_KEY='MIIBIjANBgkqh...';

```

This concludes the step inside Snowflake.  Save your key files and move on to the next step

### Configure Connection

### Sign Up

To sign up, visit https://app.maxmycloud.com/signup.  Follow the on-screen instructions. If you choose the email/password method, you may need to verify your email.

### Choose Subscription Plan

For first-time users, you will be directed to the Get Started page, where you can select a subscription plan and set up your Snowflake connection. If you're unsure which plan to choose, you can start with the free Limited plan and [upgrade](https://app.maxmycloud.com/subscription) later if needed.

### Setup Snowflake Connection

After selecting your subscription plan, you will be redirected to Step 2: Connect to Snowflake. Fill in the required fields as follows:

  ・ Account Name: Choose a meaningful name, preferably the same as your Snowflake account name.

  ・ URL: This is the connection string used by MaxMyCloud to connect to your Snowflake account. You can derive it from your Snowflake URL by taking everything before .snowflakecomputing.com.

Example: If your Snowflake URL is https://<orgname>-<account_name>.snowflakecomputing.com, enter <orgname>-<account_name> here.

If you’re unsure of your Snowflake URL, refer to the section below: How to Get Your Snowflake URL.

  ・ Warehouse: Enter the warehouse name that MaxMyCloud is authorized to use (refer to the previous section on granting warehouse to MaxmyCloud roles).

  ・ Authentication Mode: We strongly recommend using the KeyPair method for enhanced security. Paste your private key in its entirety. Refer to the previous section for instructions on obtaining the security key.

  ・ Username: Enter the MaxMyCloud username you created in the previous section.

  ・ User Role: Enter the MaxMyCloud role name you created in the previous section.

Once all fields are filled, click "Test Connection" to verify your setup.

![verify_1](assets/verify_1.png)
![verify_2](assets/verify_2.png)

### Locate Snowflake URL

Log in to Snowsight. Navigate to your name at the bottom left, then click on Connect a tool to Snowflake. On the right side, locate the Account/Server URL and copy it.

![url](assets/url.png)




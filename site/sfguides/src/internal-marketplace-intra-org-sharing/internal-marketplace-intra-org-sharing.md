authors: Matthias Nicola, Henrik Nielsen
id: internal-marketplace-intra-org-sharing
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/internal-marketplace
language: en
summary: INTRA-COMPANY DATA SHARING WITH THE SNOWFLAKE INTERNAL MARKETPLACE 
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>


# Intra-Company Data Sharing With The Snowflake Internal Marketplace 
<!-- ------------------------ -->
## Overview


Sharing information between departments or business units ("domains") of a company is critical for success. Sharing and consuming data assets is more successful if data is shared as a product. A data product is a collection of related data objects plus metadata, such as a business description, ownership and contact information, service level objectives, data dictionary, and more. In a Data Mesh, data products are typically also subject to various data management and organizational principles.  

**Snowflake Internal Marketplace** enables companies to publish documented and governed data products, so they are discoverable and understandable for data consumers. Optionally, data quality metrics and SLOs can be included to make the product more trustworthy. The marketplace also offers rich capabilities to manage access to data products and wrap detailed governance around them to control which consumers can use which data products or which parts of a data product.

![Snowflake Horizon Diagram](assets/overview.png)


### What You’ll Learn

- How to publish, share, discover, and consume data product with the Snowflake Internal Marketplace
- How to setup profiles for different business units that own the data products
- How to manage access to data products, including request & approval workflows 
- How to configure governance polices for fine-grained access control of data products across business units


### What You’ll Need

- Basic knowledge of SQL, Database Concepts
- A Snowflake Trial Account. Signup link can be found in next section (Setup)
- Familiarity with using SQL in [Snowsight Worksheets](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs)

### What You’ll Build

- Data products based on simple TPC-H data
- Organizational Listings comprised of data and metadata
- Governance policies to manage your data products


## Setup


The setup instructions for this lab describe all the steps for you to create the 3 accounts, domain profiles, and roles shown in the diagram below.

The internal marketplace exists by default. It does not need to be created. But, you will configure it with provider profiles for the different business units via the [organization account](https://docs.snowflake.com/en/user-guide/organization-accounts). The organization account is a recent Snowflake capability to optionally monitor and manage a set of regular accounts.

![LabScenario](assets/demoscenario_and_accounts.png)

The setup follows these steps:
- Step 1: Create a Snowflake trial account in a region of your choice
- Step 2: Configure the first account and create two more accounts _in the same org_
- Step 3: Configure the second account
- Step 4: Configure the organization account, and rename the first account 
- Step 5: Create profiles for the Sales, Marketing, and Supply Chain domains
- Step 6: Setup of a TPC-H sample database
- Step 7: Pre-populate the Internal Marketplace with Sample Listings

For Steps 2 through 7 you can download [scripts here](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/tree/main/sql) and execute them in different accounts as per the instructions below. In the Snowflake UI you can easily import these scripts like this:

![Import](assets/importscript.png)

### Step 1: Create a Snowflake trial account

Sign up for a trial account [here](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)

- Choose a Cloud and Region. We recommend choosing one of these regions where this Quickstart and the very latest features have been tested:
  - **Microsoft Azure:** North Europe (Ireland), Central US (Iowa), Canada Central (Toronto)
  - **Amazon Web Services**: EU (Frankfurt), Canada (Central), Asia Pacific (Tokyo)
  - **Google Cloud Platform**: Europe West (London), US Central (Iowa)

- Choose **Enterprise Edition** or higher. (Standard Edition does not support the Internal Marketplace)
- Activate the account with an admin user name such as `admin`
  
  - <mark>Note!</mark> Step 2 creates a `sales_admin` that will be used throughout this lab.


### Step 2: Configure the first account and create two more accounts _in the same org_
- Login as `admin` to your Primary Account from Step 1 and execute the following commands in a worksheet. 
- In the first four commands, enter your own email, first name, last name and password - this variable will be reused in the code for creating users and accounts.
- You can also download this SQL file and import it into Snowsight - [`STEP2_setup_primary_account.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP2_setup_primary_account.sql)

```sql
-- Run this code in your PRIMARY Account
-- Make sure you update the four variables below (email_var, firstname_var, lastname_var, and pwd_var)

USE ROLE accountadmin;

-- Use the same name and email for all accounts
set email_var = 'FILL_IN_YOUR_EMAIL';
set firstname_var  = 'FILL_IN_YOUR_FIRST_NAME';
set lastname_var  = 'FILL_IN_YOUR_LAST_NAME';

-- Use the same password for users in all accounts
set pwd_var = 'FILL_IN_YOUR_PASSWORD';

CREATE OR REPLACE WAREHOUSE compute_wh WAREHOUSE_SIZE=xsmall INITIALLY_SUSPENDED=TRUE;
GRANT ALL ON WAREHOUSE compute_wh TO ROLE public;

--  Create a user and role for the sales domain:
USE ROLE accountadmin;
CREATE OR REPLACE ROLE sales_data_scientist_role;

SET my_user_var = CURRENT_USER();
ALTER USER identifier($my_user_var) SET DEFAULT_ROLE = sales_data_scientist_role;

CREATE OR REPLACE USER sales_admin
  PASSWORD = $pwd_var
  LOGIN_NAME = sales_admin
  DISPLAY_NAME = sales_admin
  FIRST_NAME = $firstname_var
  LAST_NAME = $lastname_var
  EMAIL = $email_var
  MUST_CHANGE_PASSWORD = FALSE
  DEFAULT_WAREHOUSE = compute_wh
  DEFAULT_ROLE = sales_data_scientist_role
  COMMENT = 'Sales domain admin';

GRANT ROLE sales_data_scientist_role TO USER sales_admin;
GRANT ROLE accountadmin              TO USER sales_admin;  -- for simplicity in this lab
GRANT CREATE SHARE ON ACCOUNT                    TO ROLE sales_data_scientist_role;
GRANT CREATE ORGANIZATION LISTING ON ACCOUNT     TO ROLE sales_data_scientist_role;


-- Next, create a user and role for the marketing domain:
USE ROLE accountadmin;
CREATE OR REPLACE ROLE marketing_analyst_role;

CREATE OR REPLACE USER marketing_admin
  PASSWORD = $pwd_var
  LOGIN_NAME = marketing_admin
  DISPLAY_NAME = marketing_admin
  FIRST_NAME = $firstname_var
  LAST_NAME = $lastname_var
  EMAIL = $email_var
  MUST_CHANGE_PASSWORD = FALSE
  DEFAULT_WAREHOUSE = compute_wh
  DEFAULT_ROLE = marketing_analyst_role
  COMMENT = 'Marketing domain admin';

GRANT ROLE marketing_analyst_role TO USER marketing_admin;
GRANT CREATE SHARE ON ACCOUNT                    TO ROLE marketing_analyst_role;
GRANT CREATE ORGANIZATION LISTING ON ACCOUNT     TO ROLE marketing_analyst_role;

USE ROLE orgadmin;
GRANT MANAGE LISTING AUTO FULFILLMENT ON ACCOUNT TO ROLE sales_data_scientist_role;
GRANT MANAGE LISTING AUTO FULFILLMENT ON ACCOUNT TO ROLE marketing_analyst_role;
```

> 
> IMPORTANT: You **may** receive an email asking for verification of your email address, if you have not done so before. Check your email inbox for a message from "Snowflake Computing" and validate the email for the `marketing_admin` user. 

While waiting for the email, you can go ahead and run the following parts.

Now, run the following commands to create the next two accounts that you need. 

> 
> IMPORTANT: For the commands below, you **have to use the same worksheet** as above, as the variables created are reused (email_var, firstname_var, lastname_var, and pwd_var).

```sql
-- Run this code in your PRIMARY account
-- Create a secondary account in the same region (default!):
USE ROLE orgadmin;

CREATE ACCOUNT hol_account2
  admin_name = supply_chain_admin
  admin_password = $pwd_var
  first_name = $firstname_var
  last_name = $lastname_var 
  email = $email_var
  must_change_password = false
  edition = enterprise;

-- Create an organization account for admin purposes:
CREATE ORGANIZATION ACCOUNT hol_org_account
  admin_name = org_admin
  admin_password = $pwd_var
  first_name = $firstname_var
  last_name = $lastname_var 
  email = $email_var
  must_change_password = false
  edition = enterprise; 

-- Get an overview of all the accounts in the organization.
-- This SHOW command should return 3 rows:

SHOW ACCOUNTS;
```

- Make a note of your account names, URLs, and passwords!
- Copy or bookmark the account URLs returned by `SHOW ACCOUNTS'. 
- When you click on one of these URLs you are automatically directed to the respective account for login.



### Step 3: Configure the second account `HOL_ACCOUNT2`
In a separate browser tab, log in to the account you created in step 1 (`HOL_ACCOUNT2`) and set up this account.

- Login as `supply_chain_admin` user to your account `HOL_ACCOUNT2` from Step 2 and execute the following commands in a worksheet (Use the code below or download it from the file [`STEP3(HOL_ACCOUNT2)_setup_hol_account2.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP3(HOL_ACCOUNT2)_setup_hol_account2.sql))


```sql
-- Run this in hol_account2, logged in as supply_chain_admin user
-- Make sure you run this as ACCOUNTADMIN

USE ROLE accountadmin;

CREATE OR REPLACE WAREHOUSE compute_wh WAREHOUSE_SIZE=xsmall INITIALLY_SUSPENDED=TRUE;
GRANT ALL ON WAREHOUSE compute_wh TO ROLE public;

CREATE ROLE supply_chain_admin_role;
GRANT ROLE accountadmin TO ROLE supply_chain_admin_role; -- for simplicity in this lab
GRANT ROLE supply_chain_admin_role TO USER supply_chain_admin;

ALTER USER supply_chain_admin 
  SET DEFAULT_ROLE = supply_chain_admin_role;

USE ROLE supply_chain_admin_role;
CREATE DATABASE supply_chain_db;
```


### Step 4: Configure the organization account and rename your primary account 
Login to the Organization Account `HOL_ORG_ACCOUNT` as the `org_admin` user and execute the following commands in a worksheet.

You can also download code below from the file [`STEP4(HOL_ORG_ACCOUNT)_configure_org_account.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP4(HOL_ORG_ACCOUNT)_configure_org_account.sql) from the repository: 

```sql
-- Login to the Organization Account HOL_ORG_ACCOUNT and execute the following commands in a worksheet.

USE ROLE accountadmin;

CREATE OR REPLACE WAREHOUSE compute_wh WAREHOUSE_SIZE=xsmall INITIALLY_SUSPENDED=TRUE;
GRANT ALL ON WAREHOUSE compute_wh TO ROLE public;

-- Rename the Primary Account:
USE ROLE globalorgadmin;


-- execute the following two commands together, 
-- no other commands in between:

  show accounts;
  SET my_curr_account = (SELECT "account_name" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())) order by "created_on" ASC LIMIT 1);

-- View and rename the account:
SELECT $my_curr_account;

ALTER ACCOUNT identifier($my_curr_account) 
  RENAME TO hol_account1 SAVE_OLD_URL = true;

-- Enable users with the ACCOUNTADMIN role to set up Cross-Cloud Auto-Fulfillment
SELECT SYSTEM$ENABLE_GLOBAL_DATA_SHARING_FOR_ACCOUNT('hol_account1');
SELECT SYSTEM$ENABLE_GLOBAL_DATA_SHARING_FOR_ACCOUNT('hol_account2');

SHOW ACCOUNTS;

-- You should see 3 rows similar to the image below.
-- Make a note of your account names, URLs, and passwords!
```

![Import](assets/show_accounts.png)


### Step 5: Create profiles for the Sales, Marketing, and Supply Chain domains
Continue working as the `org_admin` user in your Organization Account `HOL_ORG_ACCOUNT` to create data provider profiles. You will set up profiles for 3 business domains: **Sales**, **Marketing**, and **Supply chain**.

- Download the script [`STEP5(HOL_ORG_ACCOUNT)_create_org_profiles.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP5(HOL_ORG_ACCOUNT)_create_org_profiles.sql)
- In that script, replace the dummy email **youremail@whatever.com** with your actual email address so that you  receive access request notifications for your data product. See the image below for more details.
  - Don't worry: it's only a couple of emails and only during this lab.

- Run the downloaded script `STEP5(HOL_ORG_ACCOUNT)_create_org_profiles.sql` in a worksheet.

![Import](assets/replaceemail.png)

### Step 6: Setup of a TPC-H sample database
- Download the script [`STEP6(HOL_ACCOUNT1)_create_lab_database.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP6(HOL_ACCOUNT1)_create_lab_database.sql) 
  
- Login to your primary account `HOL_ACCOUNT1` as the `sales_admin` user  and run the downloaded script `STEP6(HOL_ACCOUNT1)_create_lab_database.sql` script in a worksheet


### Step 7: Pre-populate the Internal Marketplace with Sample Listings

- Download the script [`STEP7a(HOL_ACCOUNT1)_create_sample_listing.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP7a(HOL_ACCOUNT1)_create_sample_listing.sql) 
  - Login into `hol_account1` as `marketing_admin` and run the script **STEP7a**.

- Download the script [`STEP7b(HOL_ACCOUNT2)_create_sample_listing.sql`](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/blob/main/sql/STEP7b(HOL_ACCOUNT2)_create_sample_listing.sql) 
  - Login into `hol_account2` as `supply_chain_admin` and run the script **STEP7b**.

###
**Setup is now complete!**

---

## Create / Publish Org Listing


In this section you will work in `HOL_ACCOUNT1` to create and publish an [organizational listing](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-about). 

The publishing flow consists of 5 steps:

1. Listing Title and Ownership
2. Selecting Data Objects to Share
3. Configure Access Control and the Approval Process
4. Add Optional Metadata and SLOs
5. Publish your listing to the internal marketplace

Login in to `HOL_ACCOUNT1` as user `sales_admin`.

### Publishing Flow (Step 1 of 5): Listing Title and Ownership

1. Navigate to the Provider Studio and click the blue **+Create Listing** button in the top right. 
2. Select **"Internal Marketplace"**.

![IM](assets/publish09_providerstudio.png)

3. Click on **“Untitled Listing”** and give your data product a meaningful title. Let's use **Order Insights** in this lab. Click "Save".

> 
> IMPORTANT: some code later in this lab will reference the listing by the name **Order Insights**. 

![](assets/publish01_title.png)

4. Click on the **+Profile** button and select the **Sales** profile as the owner of this data product. 

![](assets/publish02_profile.png)

- When you save the profile selection, note that the contact email from the Sales profile is automatically entered as the default support contact for this listing. You can change this on a per listing basis if you want. 

### Publishing Flow Step (2 of 5): Selecting Data Objects to Share

Now let's select the data objects that we want to share in this data product. 
- Click on the blue **Add Data Product** button to open the object explorer. 

- Then, click **+ Select**, navigate to the SF1 schema of the TPCH database, and select all tables except *Region* and *Part*. Also select the ORDER_SUMMARY view and the  function ORDERS_PER_CUSTOMER. Click **Done** and **Save**.

![](assets/publish03_objectselection.png)

### Publishing Flow (Step 3 of 5): Configure Access Control and the Approval Process

Next you set the access control for the data product. Click on the gray **+Access Control** button. 
- *Discovery* determines who can see the listing and all its metadata in the internal marketplace without having access to the shared data objects.
- *Access* specifies who can discover the listing *and* access the shared data objects. 

For this first data product we keep it simple and stick with the defaults:

- *Grant Access*: No accounts or roles are pre-approved
- *Allow Discovery*: Entire Organization

As a result, every data consumer will need to request access to obtain approval to use the data product. Click on **Set up request approval flow** to proceed.

![](assets/publish04_accesscontrol.png)

You could configure an external workflow engine for the request approval process. But for this lab we choose to **Manage requests in Snowflake**. The email address for notifications defaults to the one from the *Sales* profile but could be changed.

![](assets/publish05_requestconfig.png)

After you confirm the approval flow settings, Snowflake prompts you for one more configuration. Here is why: this listing is configured to be discoverable by the entire organization. What if you add another account to the organization but in a different cloud region? Then Snowflake would transparently perform incremental replication to that region to minimize egress cost. As the data provider you can choose the frequency of this replication.

So lets (1) **Review** the settings, (2) Change the replication interval to daily (1 Days), and then (3) **Save** the settings for this listing:

![](assets/publish06_laf.png)

### Publishing Flow (Step 4 of 5): Add Optional Metadata and SLOs
Data products should be understandable and trustworthy for data consumers so let's add additional metadata to describe the product (see screenshot below).

- Add a business **description** to document your listing.
  - For example: "This data product contains transactional records of customer orders, linking individual order details with specific items purchased. It includes information such as order IDs, customer identifiers, order dates, item names, quantities, and prices. This data can be leveraged to analyze customer purchasing patterns, identify popular products, understand order frequency, and gain insights into sales trends."

- **Add documentation** by providing a URL to additional information. (You can enter any URL for now, such as http://www.snowflake.com/data-mesh)
- **Add terms & conditions** by providing a URL to where the T&Cs can be found.
- **Add attributes** that indicate **service level objectives** from the data product owner to data consumers. You can specify:
  - **Update Frequency**: How often you will refresh the data product, e.g. adding new or updated records to the shared tables. 
  - **Geographic Coverage**: The regions you will share this data product to, if your company uses Snowflake in multiple regions.
  - **Time Range**: Amount of history data included.
  - **Timestamp Granularity**: The interval between data points. For example, "*Event-based*" if there is one record for each incoming order, or "*Daily*" if order volumes are aggregated by date, and so on.
  
  ![](assets/publish07_metadata.png)


- Add at least two **Usage examples** such as the following two queries.
  - Note: Queries reference objects in a data product via the [Uniform Listing Locator (ULL)](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-query).
  - The ULL of your **Order Insights** listing is `ORGDATACLOUD$SALES$ORDER_INSIGHTS`.
  - The ULL contains the domain profile name and listing name. Schema name and object name can be appended to reference objects within the listing, as in the two queries below.
  - The ULL can be copied from the top of the listing page, right under the listing name.
  
  
  ```sql
    -- Title: Explore the Order Summary View:

    SELECT * 
    FROM ORGDATACLOUD$SALES$ORDER_INSIGHTS.SF1.ORDER_SUMMARY 
    LIMIT 100;


    -- Title: Use the UDF to obtain order details for one customer:

    SELECT customer_name, country, orderkey, orderdate, AMOUNT
    FROM TABLE(ORGDATACLOUD$SALES$ORDER_INSIGHTS.sf1.orders_per_customer(60001));
    ```



- Generate a **Data dictionary**. Snowflake will automatically compile column information and sample data for *all* objects in the data product.

    Select at least one (and up to 5) data objects and click **+Add to Featured**. These are the objects that consumers will see first in the dictionary.
    Suggestion: Select `customer`, `orders`, and `order_summary` to be featured.

![](assets/publish08_datadictionary.png)

### Publishing Flow (Step 5 of 5): Publish your listing to the internal marketplace

Click the blue **Publish** button in the top right corner.

Your data product is now live! You can see it when you navigate to the Internal Marketplace.

- In the old UI, choose **Data Products** in the menu on the left, then **Marketplace**, then **Internal Marketplace** at the top.
- In the new UI, choose **Catalog** in the menu on the left, then **Internal Marketplace** (see below).
- Use the *Provider* filter to show listings for specific domains only.

![](assets/publish10_done_newui.png)

## Request and Grant Access


In this section you will request access to the new data product for the **Marketing** domain and the **Supply chain** domain.

### Request Access

- Open a new browser tab and log in to the `HOL_ACCOUNT1` a s the `marketing_admin` user.
- Navigate to the Internal Marketplace
- Click on the **Order Insights** listing
- Review all the listing elements from the data consumer point of view
- Click on the blue **Request Access** button
    - If you haven't previously validated your email of the `marketing_admin` user, Snowflake will now prompt you to do so, and you can follow the dialog to resend the verification email.
- The **Request access** dialog comes up. Enter a business justification such as "*We need access to this data for our next marketing campaign.*" Then submit the request. 
- After submitting the access request click the grey **View request** button to review or even withdraw your request. 
    - If you withdraw the request, please submit it again.

![](assets/RAW01.png)

Now let's also request access for the  **Supply chain** team.
- In a separate browser tab log into `HOL_ACCOUNT2` as the `supply_chain_admin` user.
- Navigate to the Internal Marketplace, open the **Order Insights** listing, and **Request Access**
- Specify a reason for access such as "*We want to analyze order patterns to optimize our supply chain operations.*"

### Review and Grant Access 

Let's switch back to the perspective of the data product owner to review and grant the access requests.
- Log into your account `HOL_ACCOUNT1` as the `sales_admin` user.
- Navigate to the **Provider Studio** as shown in the screenshot below and open the tab **Internal Requests**.
- Click on each of the two requests to review the details and use the green **Grant** button to approve.

![](assets/raw02_newui.png)

Switch from **Needs Review** to **Resolved Requests** to see the history of requests. 

![](assets/raw03.png)

---
###


## Consume Org Listing


Now that access has been granted, let's go back to the consumer roles:

- In a separate browser tab log into `HOL_ACCOUNT2` as the `supply_chain_admin` user. *(Keep this tab alive for the rest of the lab.)*
- In the Internal Marketplace open the **Order Insights** listing again
- The blue **Request Access** button has now changed to **Query in Worksheet**. Reload the browser tab if needed to see the new button.
- Click **Query in Worksheet**. Review and run the data product sample queries. *(Keep this tab alive for the rest of the lab.)*
- Note the list of all available internal data products in the left-hand side of the UI.
- In the SQL, note the ULL (Uniform Listing Locator) that references the data product.
  - The ULL contains the domain name, i.e. the name of the profile under which the listing was published.
  - The ULL also contains the listing name. 
  - Schema and object names are appended to access specific objects in the data product.
- **Optional**: Log into account `HOL_ACCOUNT1` as the `marketing_admin` user and perform the same steps.

![](assets/consumelisting.png)

---
## Live Data Sharing


What happens when the data owner decides to update the data product?

- Switch back to the data provider side, ie. `sales_admin` user
in `HOL_ACCOUNT1`
- Review the order details for customer 60001. 
  ```sql
  use schema tpch.sf1;
  use role sales_data_scientist_role;

  SELECT customer_name, country, orderkey, orderdate, AMOUNT
  FROM TABLE(orders_per_customer(60001));
  ```
- Note that customer 60001 lives in Kenya. But, the customer has now moved to Mozambique, which requires the following update to the customer's nationkey:

  ```sql
  -- Customer 60001 moves from Kenya to Mozambique !
  UPDATE customer SET c_nationkey = 16 WHERE c_custkey = 60001;
  ```
- Now switch to your browser tab where you are logged into `HOL_ACCOUNT2` as `supply_chain_admin`. In the worksheet "**Order Insights - Examples**" run the second sample query again:

  ```sql
  -- Use the UDF to obtain the order details for one customer

  SELECT customer_name, country, orderkey, orderdate, AMOUNT
  FROM TABLE(ORGDATACLOUD$SALES$ORDER_INSIGHTS.sf1.orders_per_customer(60001));
  ```
- Note that the updated country information,  inferred from the updated nationkey, is instantly visible to data consumers!
- Other data product changes such as adding a column to a table would also be immediately reflected on the consumer side. 
- **Best practice:** inform your data consumers of structural data product changes ahead of time.  In case of a breaking change consider creating a new listing "v2.0" and give data consumers time to migrate from the old to the new listing.


---

## Data Governance Policies


Let's examine some simple techniques for row- and column-level access control across domains.

- Switch back to the data provider side, ie. `sales_admin` user
in `HOL_ACCOUNT1`
- Review the order summary view. Note that it returns data for customers in many different countries:
  
  ```sql
  use schema tpch.sf1;
  use role sales_data_scientist_role;

  SELECT *
  FROM order_summary 
  LIMIT 100;
  ```
### Row-level Access Control across Domains
The data steward of the Sales domain has requested the following access restrictions:
- ❗The marketing team may only see data for customers in Canada.
- ❗The supply chain team may only see data for customers in the US.
  
Implement the following policy to make your data product compliant:

```sql
use schema tpch.sf1;
use role sales_data_scientist_role;

CREATE OR REPLACE ROW ACCESS POLICY country_filter AS (country INTEGER) 
RETURNS boolean ->
  CASE
    WHEN current_account_name() = 'HOL_ACCOUNT1' 
     AND current_role()         = 'SALES_DATA_SCIENTIST_ROLE'
     THEN true
    WHEN current_account_name() = 'HOL_ACCOUNT1' 
     AND current_role()         = 'MARKETING_ANALYST_ROLE'
     AND country                = 3 /* Canada */
     THEN true
    WHEN current_account_name() = 'HOL_ACCOUNT2' 
     AND country                = 24 /* USA */
     THEN true
   ELSE false
  END;

 ALTER TABLE nation ADD ROW ACCESS POLICY country_filter ON (n_nationkey); 
```
Before we review the impact of this policy on the data consumers, let's look at a different governance requirement that requires column masking.
 
### Data Masking across Domains

The data steward of the Sales domain has requested the following data masking to be enforced:
- ❗The marketing and supply chain teams are not allowed to see order pricing or item pricing for orders placed before 1996.

Implement the following policy to make your data product compliant:

```sql
 CREATE OR REPLACE MASKING POLICY order_mask AS (value INT, cutoff_date DATE) RETURNS INT ->
  CASE
    WHEN current_account_name() = 'HOL_ACCOUNT1' 
     AND current_role()         = 'SALES_DATA_SCIENTIST_ROLE'
     THEN value
    WHEN current_account_name() = 'HOL_ACCOUNT1' 
     AND current_role()         = 'MARKETING_ANALYST_ROLE'
     AND cutoff_date            >= '1996-01-01'
     THEN value
    WHEN current_account_name() = 'HOL_ACCOUNT2' 
     AND cutoff_date            >= '1996-01-01'
     THEN value
   ELSE null
  END;

ALTER VIEW order_summary ALTER COLUMN order_amount 
  SET MASKING POLICY order_mask USING (order_amount, o_orderdate); 

ALTER TABLE orders       ALTER COLUMN o_totalprice 
  SET MASKING POLICY order_mask USING (o_totalprice, o_orderdate);

ALTER TABLE lineitem     ALTER COLUMN l_extendedprice 
  SET MASKING POLICY order_mask USING (l_extendedprice, l_commitdate);
```
### Effect of the Policies on Data Consumers
Let's see how the Supply Chain and Marketing teams are affected by the new policies.

- Switch to your browser tab where you are logged into `HOL_ACCOUNT2` as `supply_chain_admin`. 
- In the worksheet "**Order Insights - Examples**" run the first sample query again:

  ```sql
  SELECT *
  FROM ORGDATACLOUD$SALES$ORDER_INSIGHTS.SF1.ORDER_SUMMARY 
  LIMIT 100;
  ```

- Confirm that governance policies are applied:
  - You should only see data where the nation name is United States.
  - The Order_Amount column should be masked for orders before 1996.


- Log into account `HOL_ACCOUNT1` as the `marketing_admin` user and execute the same query. 
  - You should see data for Canadian customers only.
  - The Order_Amount column should be masked for orders before 1996.  

As soon as you remove roles or accounts, the listing is no longer accessible for this role and/or account.


## Basic Listing Management


In this section we will review further capabilities for managing and monitoring listings as a data product owner or as an organization data steward:

- How to change/revoke access or discoverability for a listing
- How to grant listing management privileges
- How to audit access to organizational listing ([organization_usage.access_history](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-governance))


### Change/Revoke Access or Discoverability for a Listing

- Log into account `HOL_ACCOUNT1` as the `sales_admin` user
- Navigate to the Provider Studio and open the **Order Insights** listing

    ![](assets/managelistings_01.png)

- In the top right, click on the Access definition of the listing.

    ![](assets/managelistings_02.png)

- You can now add or remove roles or entire accounts that access the data product. Same for discoverability.

    ![](assets/managelistings_03.png)

---
### How to Grant Listing Management Privileges

- Navigate to the Provider Studio and open the **Order Insights** listing, if it is not still open from the previous exercise.
- Click on the three dots and **Open Settings** in the top right corner.
- In the side panel you can now edit listing settings and privileges.
- For example, you can authorize additional roles to *Modify* this listing and respond to access requests from data consumers:

    ![](assets/managelistings_04.png)

---
### How to Audit Access to Organizational Listing 

As an organization admin you can query the [organization_usage.access_history](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-governance) view to audit the access to all data products on the internal marketplace.

- Login to your Organization Account `HOL_ORG_ACCOUNT` and run the following query to obtain a list of all queries against the **ORDER_INSIGHTS** data product including the user, role, timestamp, and SQL text of the access as well as the set of provider policies that have governed the access at that point in time.
- Note: There is some delay in updating the [organization_usage.access_history](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-governance). If you don't see the entries that you expect, check back again later!
  - You can come back to this lab for as long as your trial accounts are active!


```sql
use role globalorgadmin;
use warehouse compute_wh;

select q.account_name, 
    q.user_name, 
    q.role_name, 
    q.query_text, 
    q.start_time, 
    q.end_time, 
    a.direct_objects_accessed, 
    a.provider_base_objects_accessed,
    a.provider_policies_referenced
from SNOWFLAKE.ORGANIZATION_USAGE.ACCESS_HISTORY a, 
    SNOWFLAKE.ORGANIZATION_USAGE.QUERY_HISTORY q
where a.query_id = q.query_id
and q.query_text ilike '%ORDER_INSIGHTS%'
order by query_start_time desc;
```


---

## Programmatic Listings


So far this lab has managed listings mainly through the Snowflake UI. But, [data owners](https://docs.snowflake.com/en/progaccess/listing-progaccess-about) and [data consumers](https://other-docs.snowflake.com/en/collaboration/consumer-listings-progaccess-examples) can also work with listings programmatically through the [Listing API](https://docs.snowflake.com/en/sql-reference/commands-listings). 

In this section we point you to some of the most commonly used commands. These are not end-to-end exercises to create or alter listings, but we encourage you to experiment with some of these commands.

### As a Listing Owner

- Run [`SHOW LISTINGS;`](https://other-docs.snowflake.com/en/sql-reference/sql/show-listings) to list the listings that you own or have permission to manage.
  
- Run [`DESCRIBE LISTING listing-name;`](https://other-docs.snowflake.com/en/sql-reference/sql/desc-listing) to obtain additional details for one specific listing. 
  - The listing name can be obtained from the output of  [`SHOW LISTINGS;`](https://other-docs.snowflake.com/en/sql-reference/sql/show-listings);
  - Note: If that listing name contains special characters other than the underscore, then the name must be in double quotes and is case-sensitive.

- In the result of [`DESCRIBE LISTING`](https://other-docs.snowflake.com/en/sql-reference/sql/desc-listing)  scroll to the right to the column [MANIFEST_YAML](https://other-docs.snowflake.com/en/progaccess/listing-manifest-reference) and copy its column value to a worksheets. 
  - This YAML file is a complete representation of the listing and enables programmatic management of listings.

- Run [`CREATE ORGANIZATION LISTING`](https://other-docs.snowflake.com/en/sql-reference/sql/create-organization-listing) with a YAML file and SHARE name to create a new listing programmatically.

- Run [`ALTER LISTING`](https://other-docs.snowflake.com/en/sql-reference/sql/alter-listing) to make changes to a listing such as:
  - Unpublish and publish a listing
  - Rename a listing
  - Change any of the listing metadata by using a modified YAML file in the  [`ALTER LISTING`](https://other-docs.snowflake.com/en/sql-reference/sql/alter-listing) command
  - Change who can discover or access a listing, e.g. by providing a modified YAML file


### As a Listing Consumer

- Run [`SHOW AVAILABLE LISTINGS IS_ORGANIZATION = TRUE;`](https://other-docs.snowflake.com/en/sql-reference/sql/show-available-listings) to list all the internal marketplace listings that your current role is allowed to discover.

- Run [`DESCRIBE AVAILABLE LISTING listing_global_name`](https://other-docs.snowflake.com/en/sql-reference/sql/desc-available-listing) to get more details on one particular listing.
  - The listing global name can be found in the output of the  [`SHOW AVAILABLE LISTINGS`](https://other-docs.snowflake.com/en/sql-reference/sql/show-available-listings) command.
  - Note: The `listing global name` is a different kind of listing identifier than the `listing name`.

- Run [`CREATE DATABASE name FROM LISTING listing_global_name;`](https://other-docs.snowflake.com/en/collaboration/consumer-listings-progaccess-examples#create-a-database-from-a-listing) if you operate as a data consumer in a different account and you want to mount the listing as a local database. 
  - This does not create a local copy of the shared data but it makes the listing appear in your local list of databases.
  - Mounting an organizational listing as a local database enables you to work with database roles for additional governance options.
---

<!--
## Enable Change Tracking for Data Products
<mark> !!! do we want to keep this section and adjust it to our TPC-H scenario ??? </mark>

The provider of a listing can choose to enable [change tracking](https://docs.snowflake.com/en/user-guide/streams) on the some or all of the tables or views that are shared in a listing. This enables the consumer to track the data changes. Let's do that with the view DAILY_WEATHER_V:

```sql
-- in the provider account:
ALTER VIEW FROSTBYTE_TASTY_BYTES.HARMONIZED.DAILY_WEATHER_V 
      SET CHANGE_TRACKING = TRUE;
```

The consumer can now [define a Stream](https://docs.snowflake.com/en/sql-reference/sql/create-stream) to capture the data changes in this view:

```sql
-- in the consumer account:
CREATE DATABASE tasty_bytes_local;
USE DATABASE tasty_bytes_local;

CREATE STREAM stream_daily_weather_changes ON VIEW tasty_bytes_analytics.HARMONIZED.DAILY_WEATHER_V;
```

To see the change tracking in action you can now insert, update, or delete some of the weather related data in the AWS Provider account. For example:

```sql
-- in the provider account:
INSERT INTO FROSTBYTE_TASTY_BYTES.WEATHER.HISTORY_DAY
  SELECT * REPLACE  (current_date AS DATE_VALID_STD) 
  FROM FROSTBYTE_TASTY_BYTES.WEATHER.HISTORY_DAY
  WHERE city_name = 'San Mateo'
  ORDER BY date_valid_std DESC;
  ```

Now switch to the consumer account and query the stream:

```sql
-- in the consumer account:
USE DATABASE tasty_bytes_local;

SELECT METADATA$ACTION, METADATA$ISUPDATE, * 
FROM stream_daily_weather_changes;
```
----------->



<!----------- maybe we add database roles later


## Govern Data Products with Database Roles
### Database Roles - Provider Side

Just when we thought we had all the necessary governance controls in place, Frosty has a new requirement for us.

![503_DataSteward_3](assets/503_datasteward_3.png)

So far we have been using the context function **CURRENT_ACCOUNT_NAME()** in our governance policies to control which consumer account can see which data. Now Frosty is telling us, that this needs to be more fine-grained down to indivudal roles on the consumer side.

We will be using roles and [database roles](https://docs.snowflake.com/en/sql-reference/sql/create-database-role) for 3 different continents. Let's check that we have the correct roles in place.

On the AWS Provider account, use **show database roles** to confirm that you have 4 database roles in place. Else create them now.

```sql
show database roles in database FROSTBYTE_TASTY_BYTES;

USE DATABASE frostbyte_tasty_bytes;
CREATE OR REPLACE DATABASE ROLE tastybytes_emea_role;
CREATE OR REPLACE DATABASE ROLE tastybytes_americas_role;
CREATE OR REPLACE DATABASE ROLE tastybytes_apj_role;
CREATE OR REPLACE DATABASE ROLE tastybytes_manager_role;
```

We can use these roles to define more granular and role-based access control for the data consumers. First, we need to give these roles access to the providers's schema and objects that we want to govern, in this case ANALYTICS.CUSTOMER_LOYALTY_METRICS_V:

```sql
use database FROSTBYTE_TASTY_BYTES;

grant usage  on schema ANALYTICS to database role tastybytes_emea_role;
grant usage  on schema ANALYTICS to database role tastybytes_americas_role;
grant usage  on schema ANALYTICS to database role tastybytes_apj_role;
grant usage  on schema ANALYTICS to database role tastybytes_manager_role;

grant select on view ANALYTICS.CUSTOMER_LOYALTY_METRICS_V 
             to database role tastybytes_emea_role; 
grant select on view  ANALYTICS.CUSTOMER_LOYALTY_METRICS_V 
             to database role tastybytes_americas_role; 
grant select on view  ANALYTICS.CUSTOMER_LOYALTY_METRICS_V 
             to database role tastybytes_apj_role; 
grant select on view  ANALYTICS.CUSTOMER_LOYALTY_METRICS_V 
             to database role tastybytes_manager_role; 
```

Next, use the context function [**IS_DATABASE_ROLE_IN_SESSION()**](https://docs.snowflake.com/en/sql-reference/functions/is_database_role_in_session) to recreate our row-level access policy to define which role can see customer loyality data from which country.


```sql
use database frostbyte_tasty_bytes;
use schema analytics;

ALTER VIEW CUSTOMER_LOYALTY_METRICS_V DROP ROW ACCESS POLICY country_filter;


CREATE OR REPLACE ROW ACCESS POLICY country_filter AS (country string) 
RETURNS boolean ->
  CASE
    -- users with the AMERICAS role can see data from the US, Canada, and Brazil
    WHEN IS_DATABASE_ROLE_IN_SESSION('TASTYBYTES_AMERICAS_ROLE') 
     AND country IN ('United States', 'Canada', 'Brazil') 
    THEN true
    -- users with the EMEA role can see data from these EMEA countries
    WHEN IS_DATABASE_ROLE_IN_SESSION('TASTYBYTES_EMEA_ROLE')         
     AND country IN ('France', 'Germany', 'Poland', 'Sweden', 
                     'Spain' , 'South Africa', 'Egypt') 
    THEN true
    -- users with the APJ role can see data from these APJ countries
    WHEN IS_DATABASE_ROLE_IN_SESSION('TASTYBYTES_APJ_ROLE')         
     AND country IN ('Japan', 'Australia', 'India', 'South Korea') 
    THEN true
    -- users with the manager role can see all data
    WHEN IS_DATABASE_ROLE_IN_SESSION('TASTYBYTES_MANAGER_ROLE')         
    THEN true
    -- the account admin in the provider account can see all data
    WHEN current_account_name() IN ('*** FILL IN AWS Provider Account Name ***') 
     AND current_role() = 'ACCOUNTADMIN'
    THEN true
    ELSE false
  END;

ALTER VIEW CUSTOMER_LOYALTY_METRICS_V 
      ADD ROW ACCESS POLICY country_filter ON (country);
```

For a larger number of roles and countries you can certainly use a mapping table from role to country so that the policy simply performs a lookup in the mapping table.

The final step in the provider account is to share the database roles to the consumer accounts along with the data product.  This is achieved by [granting the database roles to the share](https://docs.snowflake.com/en/sql-reference/sql/grant-database-role-share):

```sql
-- Use your share name in these commands.
-- See below for hints on how to find your share name.
GRANT DATABASE ROLE tastybytes_emea_role     TO SHARE <share_name>;
GRANT DATABASE ROLE tastybytes_americas_role TO SHARE <share_name>;
GRANT DATABASE ROLE tastybytes_apj_role      TO SHARE <share_name>;
GRANT DATABASE ROLE tastybytes_manager_role  TO SHARE <share_name>;
```

Here are two options how to find the share name for your listing:

**Option 1:**

In the provider account, navigate to the Provider Studio, select "Listings" from the horizontal menu at the top, and open your listing. In the section "Data Product" you find the name of the Secure Share that bundles the shared data objects.
![602_DMF_AddTableToShare_1](assets/602_dmf_addtabletoshare_1.png)

**Option 2:**

Use the SHOW SHARES command:

![504_ShowShares](assets/504_shares.png)

Copy the share name to a text file or worksheet because you will need it again later.

### Database Roles - Consumer Side

To complete the configuration of cross-account role-based access control you need to assign the shared database roles to local account roles in the consumer roles.

Switch to your consumer accounts.  

In each of your consumer accounts you should already have the following 4 roles that you created during the account setup. Verify that these roles are in place. Else, create them now.

```sql
SHOW ROLES LIKE 'SALES%';

CREATE OR REPLACE ROLE sales_emea_role     COMMENT = 'EMEA Sales role';
CREATE OR REPLACE ROLE sales_americas_role COMMENT = 'Americas Sales role ';
CREATE OR REPLACE ROLE sales_apj_role      COMMENT = 'APJ Sales role ';
CREATE OR REPLACE ROLE sales_manager_role  COMMENT = 'Manager (all-access) role';
```

In a real-world scenario you would now assign each of these roles to different users. For simplicity in this lab, grant all of these roles to yourself:

```sql
SET my_user_var  = CURRENT_USER();
GRANT ROLE sales_emea_role     TO USER identifier($my_user_var);
GRANT ROLE sales_americas_role TO USER identifier($my_user_var);
GRANT ROLE sales_apj_role      TO USER identifier($my_user_var);
GRANT ROLE sales_manager_role  TO USER identifier($my_user_var);
```

And finally, grant the shared database roles to the local account roles. This connects these local consumers roles to the row-access policy that you create on the provider side.

```sql
use database TASTY_BYTES_ANALYTICS;
grant database role tastybytes_emea_role     to role sales_emea_role; 
grant database role tastybytes_americas_role to role sales_americas_role;
grant database role tastybytes_apj_role      to role sales_apj_role; 
grant database role tastybytes_manager_role  to role sales_manager_role;
```

The following picture illustrates the use of our database roles in this data sharing scenario.

![505_Database_Roles_Sharing](assets/505_database_roles_sharing.png)

Now switch to the different local roles (sales_emea_role, sales_apj_role, etc) in each of your consumer accounts to verify that each local role can only see those rows in the CUSTOMER_LOYALTY_METRICS_V view that are permitted by the row-level access policy in the provider account.
 -->


## Conclusion And Resources


Congratulations, you completed this **Snowflake Internal Marketplace** journey! You have seen how data products can be authored, published, requested, consumed, and governed. These are key capabilities for sharing documented and understandable data products across business units with governance and compliance control controls.

### What you Learned

- How to create data products that consist of multiple data objects.
- How to document a data product with a broad range of metadata such as description, data dictionary, ownership, sample queries, and service-level objectives. 
- How to use provider profiles that represent different domains or business units as owners of data products on the internal marketplace. 
- How to request and approve or deny access to data products
- How to apply data product governance controls across domains


### Related Resources

- [Lab Source Code on Github](https://github.com/Snowflake-Labs/sfguide-intra-company-data-sharing-with-the-snowflake-internal-marketplace/tree/main/sql)

- [Organization Accounts](https://docs.snowflake.com/en/user-guide/organization-accounts) 
  
- [Organization Profiles](https://docs.snowflake.com/en/user-guide/collaboration/organization-profiles/org-profile-manage)

- Organizational Listings
  - [Create an organizational listing](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-create)
  - [Manage organizational listings](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-manage)

- [Managing Listings via API](https://other-docs.snowflake.com/progaccess/listing-progaccess-about)

- White Paper: [How to Knit Your Data Mesh on Snowflake](/resource/how-to-knit-your-data-mesh-on-snowflake/) (March 2025)

- Webinar Recording with a demo of the Snowflake Internal Marketplace:
[How to Build and Govern Your Data Products in Snowflake](/webinars/product-demo/data-mesh-demo-how-to-build-and-govern-your-data-products-in-snowflake-2025-04-29/) (April 2025)


author: Jim Warner
id: suppress_existing_customers_from_youtube_campaign_with_hightouch_and_snowflake
summary: Build and sync an audience of existing customers to Youtube to suppress from future prospecting campaigns, using Hightouch and Snowflake.
categories: Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, AdTech

# Suppress existing customers from a Youtube campaign with Hightouch and Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 1

Hightouch helps marketers activate their customer data from Snowflake to over 125 different applications.  The [Data Activation](https://hightouch.com/blog/what-is-data-activation) platform, powered by Reverse ETL, provides both a SQL-based UI as well as a no-code [audience builder](https://hightouch.com/platform/audiences) to help teams across an organization complete what is now being called the "last mile" of the [Modern Data Stack](https://hightouch.com/blog/reverse-etl-bringing-the-modern-data-stack-full-circle).

![Snowflake and Hightouch stack](assets/Snowflake_Template_The_Modern_Data_Stack_e80de39d33.jpg)

Audience targeting strategies have become increasingly important in modern marketing due to the rising cost of advertising and the increasing expectations of consumers. While there are [many ways](https://hightouch.com/blog/driving-paid-media-roas-through-audience-activation) organizations can target customers, one of the simplest strategies to optimize advertising spend is suppression audiences.

A suppression audience is a group of customers who are excluded from a marketing campaign to ensure that they do not see irrelevant ads. Suppression audiences can be created using various segments, such as current customers, churned customers, or those with low purchasing propensity. The idea behind suppression audiences is simple: you define who you do not want to target with your ads. By excluding certain groups from your campaign, you can focus on delivering relevant marketing to your desired audience.
There are several reasons a company might want to suppress or exclude existing purchasers from their ad campaign. Firstly, it may be a product, like a subscription, that can only be purchased once. Another reason is that you may simply want to use different messaging for different audiences. Existing customers may be excluded in one campaign and exclusively targeted in another. Finally, it may be a product with a long replenishment cycle, so that purchasers are excluded from messaging for a certain amount of time after their purchase.

In this Quickstart, we will cover this last example, a suppression audience use-case where recent purchasers are added as an excluded (suppression) audience segment in a Youtube campaign run through Google Ads. Leveraging existing customer data in Snowflake, we will build a purchaser audience with Hightouch's no-code audience builder and sync an audience of users who recently made a purchase to Google Ads.

### Prerequisites

- Basic experience with Snowflake and SQL
- Access to [Hightouch](https://hightouch.com/get-started) with the [Audiences](https://hightouch.com/docs/audiences/overview) feature enabled. Reach out for a [demo](https://hightouch.com/demo) if needed.

### What You’ll Learn

- How to create test data in Snowflake
- How to connect Hightouch to Snowflake
- How to create an audience in Hightouch and Sync it to Google Ads
- How to suppress audiences in Google Ads for Youtube campaigns

### What You’ll Build

- An audience for suppression within Google Ads

<!-- ------------------------ -->
## Prepare your audience within Snowflake & connect Hightouch
Duration: 4

First, you need to have the data that you want to push prepared within Snowflake.

### Log in to Snowflake

If you already have a Snowflake account, you can use your credentials to log in.  If you do not already have an account, you can visit [https://signup.snowflake.com/]https://signup.snowflake.com/ to sign up for a 30-day free trial.  You will want to make sure that the account you use in Snowflake has the permissions to create a new database, schema, and warehouse to be used by Hightouch.

### Set-up Hightouch through Partner Connect

You can set up a database, schema, and warehouse for use with Hightouch by setting up Hightouch through Partner Connect in Snowsight.  See the [https://hightouch.com/blog/hightouch-snowflake-partner-connect](detailed instructions) on the Hightouch Blog for more details.

1. Click the **Partner Connect** tab under **Admin**.

![Partner Connect](assets/hightouch-setup-step1.png)

2. Search for Hightouch (or scroll to the **Data Integration** section), and select it.

![Select Hightouch](assets/hightouch-setup-step2.png)

3. View the Database, Warehouse, User, and Role that will be created for the integration, and click **Launch**.

![Click Launch](assets/hightouch-setup-step3.png)

4. When the creation is complete, you will see a pop-up telling you that the creation has finished.  Click **Activate** to be taken to Hightouch to log in.

![Click Activate](assets/hightouch-setup-step4.png)

5. Log in to Hightouch using your Hightouch credentials, and you will have a Data Source from Snowflake created in Hightouch.

### Create test data

First, we need to create a database and schema to hold the data.

```sql
CREATE DATABASE HIGHTOUCH_QUICKSTART;
CREATE SCHEMA HIGHTOUCH_QUICKSTART.DEMO;

USE HIGHTOUCH_QUICKSTART.DEMO;
```

Next, we create the customers and sales data, and a view to unify them to make the audience.

```sql
-- create customer list
CREATE OR REPLACE TABLE customers AS
SELECT sha1(seq4()) as user_id,
  'user'||seq4()||'_'||uniform(1, 3, random(1))||'@email.com' as email,
    case when uniform(1,6,random(2))=1 then 'Less than $20,000'
       when uniform(1,6,random(2))=2 then '$20,000 to $34,999'
       when uniform(1,6,random(2))=3 then '$35,000 to $49,999'
       when uniform(1,6,random(2))=3 then '$50,000 to $74,999'
       when uniform(1,6,random(2))=3 then '$75,000 to $99,999'
  else 'Over $100,000' end as household_income,
  round(18+uniform(0,10,random(3))+uniform(0,50,random(4)),-1)+5*uniform(0,1,random(5)) as age_band,
    case when uniform(1,10,random(6))<4 then 'Single'
       when uniform(1,10,random(6))<8 then 'Married'
       when uniform(1,10,random(6))<10 then 'Divorced'
  else 'Widowed' end as marital_status
  FROM table(generator(rowcount => 100000));

-- verify the data
select * from customers;

-- create random sales for those customers
CREATE OR REPLACE TABLE sales AS
select sha1(uniform(1, 100000, random(3)))::varchar(40) as user_id
  ,dateadd(second, uniform(1, 5256576, random(4)), ('2022-09-01'::timestamp)) as sale_timestamp
  ,uniform(10000,20000,random(5)) as cost_cents
from table(generator(rowcount=>50000));

-- verify the data
select * from sales;

-- create a view for easy lookup
create or replace view PC_HIGHTOUCH_DB.public.customer_sales as
select c.user_id, c.email, c.household_income, c.age_band, c.marital_status,
 max(s.sale_timestamp) as latest_sale, sum(cost_cents)/100 as ltv_dollars
from HIGHTOUCH_QUICKSTART.DEMO.customers c
 inner join HIGHTOUCH_QUICKSTART.DEMO.sales s on s.user_id=c.user_id
group by c.user_id, c.email, c.household_income, c.age_band, c.marital_status;

-- verify the data
select * from customer_sales;
```

Now we need to grant access to the view to Hightouch.

```sql
GRANT SELECT ON VIEW PC_HIGHTOUCH_DB.public.customer_sales TO ROLE PC_HIGHTOUCH_ROLE;
```

## Create audience and configure destination in Hightouch
Duration: 8

Now that we have our test data, we can create the audience in Hightouch and push it to Google Ads.  Connecting to Hightouch from Snowflake via Partner Connect already created the data source within Hightouch.

### Creating a Google Ads destination

To push data to Google Ads for use with a Youtube campaign, we need to create a destination.

1. Navigate to destinations and click **Add Destination**.

![Add destination](assets/create-destination-step-1.png)

2. Search for Google Ads, select it, and click **Continue**.

![Select Google Ads](assets/create-destination-step-2.png)

3. Log in to Google Ads to authorize the connection. Once authorized, click **Continue**.

![Login to Google Ads](assets/create-destination-step-3a.png)
![Continue after login](assets/create-destination-step-3b.png)

4. Name the destination (ex. Sample Google Ads Destination) and then click **Finish**.

![Name destination](assets/create-destination-step-4.png)

### Create a Parent Model

A parent model must first be defined for Hightouch to understand what Snowflake data to query. *The creation of a parent model is a one time setup that can be ignored if already completed.*

1. Navigate to Audiences and click **Configure parent model**.

![Configure parent model](assets/parent-model-step-1.png)

2. Select your Snowflake data source.

![Select data source](assets/parent-model-step-2.png)

3. You will be presented with multiple options for setting up your parent model. For this Quickstart, select the **Select a Table or View option**.

![Select Table or View](assets/parent-model-step-3.png)

4. Define your customer table by selecting the table that you’d like to build the model off of - in this case, the Customer Sales Table we created earlier in the Quickstart. Once selected, click **Preview** to ensure the data is available, and then click **Continue**.

![Select Customer Sales](assets/parent-model-step-4.png)

5. Finalize the parent model settings by naming the model (Customer Sales), and defining your Primary Key (User_ID). Additionally, select your Content Label Fields which will display when previewing members of this audience (Email and UserId) and then click **Finish**.

![Finalize parent model](assets/parent-model-step-5.png)

*Note: Hightouch supports a number of entity relationships like [Related Models](https://hightouch.com/blog/audience-builder-upgrade) and Event Models to enable more complex targeting, however we are going to just leverage a parent model in this Quickstart. For more information, visit: [https://hightouch.com/docs/audiences/schema](https://hightouch.com/docs/audiences/schema)*.

### Create Purchaser Audience

With the parent model defined, users can now leverage Hightouch’s no-code audience builder to create any audience of customers.

1. Navigate to the **Audiences** tab and click on **Add audience**.

![Add audience](assets/create-audience-step-1.png)

2. Select the parent model of interest (in this case Customer Sales).

![Select parent model](assets/create-audience-step-2.png)

3. Add the segmentation logic to identify those who have purchased within the last two months by clicking **Add condition**, then **Have a property**.

![Add condition](assets/create-audience-step-3.png)

4. Click **Select property**, **Latest Sale**.

![Select property](assets/create-audience-step-4.png)

5. Set the date criteria to be **after previous 2 months**.

![After previous 2 months](assets/create-audience-step-5.png)

6. Click **Preview results** to see the users who will be included in the audience.

![Preview results](assets/create-audience-step-6.png)

7. Once previewed, click **Continue**.

![Continue after preview](assets/create-audience-step-7.png)

8. Name the audience "Recent Purchasers," and then click **Finish**.

![Finish audience](assets/create-audience-step-8.png)

### Sync Audience to Google Ads

With the audience now created, we need to configure how often it is pushed to Google Ads for use with the Youtube campaign.

1. Click on the recent-purchasers audience we just created and then click **Add a sync**.

![Add sync](assets/create-sync-step-1.png)

2. Select the Google Ads destination that we set up previously.

![Select Google destination](assets/create-sync-step-2.png)

3. Select the Google Ads account you would like to sync the audience to.
4. Select **Customer match user list** as the sync type.

![Customer match user list](assets/create-sync-step-4.png)

5. Set your user list type as “Contact_Info”.
6. Map the email column in the audience to the destination.

![Map email](assets/create-sync-step-6.png)

7. Select **Create a new user list**.
8. Under "Would you like Hightouch to automatically hash your PII data?" select "Yes, automatically hash PII for me." Then click **Continue**.
9. Select the type of schedule for sending data. It should be set depending on how often the data changes and the cadence of your campaign. For this example, we can select "Interval" and select every 12 hours to sync the data twice daily.

![Map email](assets/create-sync-step-9.png)

6. Click **Finish**.

## Suppressing audience within YouTube campaign

This section will tell you how to exclude the audience from your Youtube campaign using Google Ads.  For more details, see the [Google documentation](https://support.google.com/google-ads/answer/2549058?hl=en).

1. Click on the **Audiences** tab.
2. Click **Edit Exclusions**.
3. Under the "Exclude from" drop-down menu, select the campaign you want this audience excluded from.
4. Click the checkmark next to the audience that has synced from Hightouch.
5. Click **Save Audience Segment Exclusions**.

<!-- ------------------------ -->
## Conclusion
Duration: 1

Especially in challenging macroeconomic environments, it is important that ad campaigns are targeted to the right people. In this example, we showed how we could use Snowflake and Hightouch to suppress recent purchasers from an ad campaign running with YouTube.

### What we've covered

- How to create test data in Snowflake
- How to connect Hightouch to Snowflake
- How to create an audience in Hightouch and Sync it to Google Ads
- How to suppress audiences in Google Ads for Youtube campaigns

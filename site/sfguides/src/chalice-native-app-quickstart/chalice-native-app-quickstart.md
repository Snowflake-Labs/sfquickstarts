summary: "A concise guide to demonstrate the use of the Chalice TVB Native App to detect overbidding in programmatic auctions."
id: "Getting Started With Chalice Native App in Snowflake"
categories: data-science, native-app
environments: "web"
status: "Published"
feedback_link: "https://github.com/Snowflake-Labs/sfguides/issues"
tags: Getting Started, Data Science, Chalice, Native App 
authors: Tylynn Pettrey, Tucker Ward 

# Chalice Native App Guide
<!-- ------------------------ -->
## Overview 
Duration: 1

Chalice True Value Bidding is a tool that learns from your historical spend
what the right price to pay for your inventory is. 

### Prerequisites
- Familiarity with Snowflake Data Loading Best Practices
- Access to the Trade Desk UI for Simulation Campaign
### What You’ll Learn 
- How to download a winrate report from The Trade Desk 
- How to load the resulting reports in a snowflake table  
- How to permission the table for the Chalice TVB Simulation App
- How to run the Chalice TVB Simulation App and reveal potential savings for your programmatic campaigns

### What You’ll Need 
- [A Snowflake Account](https://signup.snowflake.com/) 
- [Active Trade Desk Campaign UI Access](https://www.thetradedesk.com/us)

-[Familiarity with Python](https://www.python.org/) 

### What You’ll Build 
- Load relevant reporting data to generate a simulation report to detect overbidding in programmatic auctions

<!-- ------------------------ -->
## Generate win-rate reports from The Trade Desk My Reports
Duration: 10

This will teach you how to create and download win-rate reports using the Trade Desk My Reports tools. Win-rate reporting allows the TVB Native App to approximate how much you are overpaying for programmatic advertising impressions. 

1. Sign in to the Trade Desk UI
2. Go to “Reports” and select the tsv/csv button in the upper right-hand corner.
3. Create report template `Chalice TrueValueBidding Simulation Report` and add the following:

    Required Fields  
    - Hour of Week
    - Metro
    - Supply Vendor
    - Inventory Contracts
    
    Required Metrics
    - Advertiser Cost
    - Media Cost
    - Impressions
    - Bids

4. Save this template
5. Find the template you just saved in the list of report templates below.
6. Enter `<Advertiser> TVB <Channel Name> <Ad Group ID>` as the schedule name. Replace the values as needed
7. Set FilterBy to Ad Group
8. Select the ad group indicated in the schedule name for filtering **Note: Results will be skewed if multiple channel 
types are present in the selected ad group due to the drastic differences in price range for each channel
You will also need to include
9. TVB needs 8 separate reports to gather enough data. Please schedule reports with the following custom date ranges:

```javascript
dates = ''
    for i in range(8):
        sd = (dt.datetime.today() - dt.timedelta(days=7 * (i + 1))).date()
        ed = (sd + dt.timedelta(days=6))
        dates += f'\t**{sd}** - **{ed}**\n\n'
```

**Important Notes**

Due to reporting constraints (file size) MyReports is limited to roughly one million rows of data. To avoid any execution errors, apply the outlined Filtering & Fields when building the template to successfully generate the report. Applying additional fields outside of what is outlined can create reports that are too big for export. 
- Add to Conversions - this section can remain blank 
Select 8 separate weekly reports from a single channel. These reports should be scheduled from Sunday-Saturday in succession for a specific campaign or ad group. If multiple channels are present in a campaign or ad group, reports must be further broken out by channel. 
Select Custom Date range and select from Sunday to Saturday for each of the last 8 weeks. Time Zone can be in the time zone that is set at the advertiser level in the UI


## Load Winrate Reports to Snowflake 
Duration: 10

```
1. Copy the following code into a snowpark SQL worksheet and run it. This will allow the app to view your win rate reports. You will be able to select which report to use in the app

```sql
EXECUTE IMMEDIATE $$

DECLARE
    -- Update this section with the appropriate variables. 
    -- This should be where you win rate reports are located
    
    chalice_db_name varchar default 'CHALICE_INPUTS';
    tvb_schema_name varchar default 'TVB';
    
BEGIN
    LET tvb_schema_path := concat($customer_db_name, '.', $tvb_schema_name);

    -- If the Database and Schema do not exist yet this will create them. Make sure that you have permission to create
    CREATE DATABASE IF NOT EXISTS identifier($chalice_db_name);
    CREATE SCHEMA IF NOT EXISTS identifier(tvb_schema_path);
    
    -- This will grant permissions to the app to use all tables in the schema with the Win Rate Reports. 
    grant usage on database identifier ($chalice_db_name) to application role TVB_SNOWFLAKE_APP.USER;
    grant usage on schema identifier ($tvb_schema_path) to application role TVB_SNOWFLAKE_APP.USER;
    grant select on all tables in schema identifier ($tvb_schema_path) to application role TVB_SNOWFLAKE_APP.USER;
    grant select on future tables in schema identifier ($tvb_schema_path) to application role TVB_SNOWFLAKE_APP.USER;
END
$$
```

## Run the Chalice TVB Native Application

Navigate to the "TVB" page in the Chalice Native Application. Select your designated database, schema, and table name. You are now ready to detect overbidding in your campaign!
<!-- ------------------------ -->

## Conclusions and Resources
Duration: 1


Overbidding is systemic in programmatic auctions. By following these steps and running your first TVB simulation, you can now detect overbidding and take steps to combat it. 

### What You Learned

- How to generate and download The Trade Desk Winrate Reports
- How to load reports into a snowflake table
- How to use the Chalice TVB Native Application to detect overbidding in programmatic advertising campaigns

### Related Resources

-[True Value Bidding White Paper](https://docsend.com/view/hxwp8j7qmud6kz8i)

-[Chalice Native Applications](https://app.snowflake.com/marketplace/providers/GZT0Z9XTXTP/Chalice%20Custom%20Algorithms?search=chalice)

-[Chalice Website](https://www.chalice.ai/)



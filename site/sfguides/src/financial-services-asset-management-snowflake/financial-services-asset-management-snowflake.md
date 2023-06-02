author: 
id: financial-services-asset-management-snowflake
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Financial Services Asset Management
<!-- ------------------------ -->
## Overview 
Duration: 1

**Summary**
- What would a Single Version of the Truth (SVOT) for Asset Managers on Snowflake look like?

**Youtube Demo**
<video id="3vBfZ_9d41Q"></video>

**Github**
- The code is [open-sourced on github](https://github.com/Snowflake-Labs/sfguide-financial-asset-management).

**Problem Statement:**
- Asset managers (big banks, insurance companies, and hedge funds) have spent hundreds of millions of dollars on systems to quickly and accurately give a SVOT in real-time.   These systems are critical especially in times of market stress like the Great Financial Crisis or any unexpected market change. 

**Why Snowflake**
- SnowSight allows you to create and share dashboards for executives, portfolio managers, risk managers, and traders.
- Significantly high performance and less cost of maintaining one SVOT    
- Near-Unlimited Compute and Concurrency enable quick data-driven decisions

### Snowsight dashboard
![Puppy](assets/SAMPLE.jpg)

**What we will see**
- Use Data Marketplace to instantly get free stock price history from the Zepl data share
- Query trade, cash, positions, and PnL (Profit and Loss) on Snowflake
- Use Window Functions to automate cash, position, and PnL reporting


### Prerequisites
- Snowflake Account or [Trial Account](https://signup.snowflake.com/) with accountadmin privileges.  

### You'll learn how to
- Query free stock market history data instantly with zero learning curve and time
- Run a Python faker function to create 100 synthetic traders
- Size up compute to create 3 billion synthetic trades
- Insert those trades ordered by trader, symbol, and date so any queries on that data are signficantly faster
- Create a cluster key to future proof that trade table from any data that has been inserted without being sorted
- Create a window function to calcluate real time trades, cash, and Profit and Loss (PnL)
- Query 3 billion rows with only small compute and 3 second run-time
- See Snowflake's 3 caches
- Zero Copy Clone for DevOps and instant sandboxes
- Time Travel to see and roll back up to 90 days of data
- Drop and Undrop Tables


<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: Financial Services Asset Management
  - Query 3 billion rows with small compute in 3 seconds
- **id**: financial-services-asset-management-snowflake 
- **categories**: Solution-Examples 
- **environments**: web 
- **status**: Published
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Financial Services, Asset Management, SnowSight
- **authors**: Allen Wong


<!-- ------------------------ -->
## 10 Setup
Duration: 2

We setup
- Role Based Access Control RBAC
- Virtual Warehouses (compute)
- Database
- Objects

Run the <button>[finserv demo 10 setup](https://github.com/Snowflake-Labs/sfguide-financial-asset-management/blob/master/setup/finserv%20demo%2010%20setup.sql)</button> script.

Each script is **idempotent** meaning that you can rerun it without issues.

<!-- ------------------------ -->
## 20 Marketplace
Duration: 3

We:
- "mount" and verify the Knoema economy_data_atlas share
- ensure data quality, ie no duplicates and positive share prices
- Python Faker function (credit to [James Weakley's Flaker 2.0 - Fake Snowflake data the easy way](https://medium.com/snowflake/flaker-2-0-fake-snowflake-data-the-easy-way-dc5e65225a13))

### Knoema Economy Data Atlas
![Puppy](assets/SAMPLE.jpg)

"Mount" the free <button>[[Knoema Economy Data Atlas](https://app.snowflake.com/marketplace/listing/GZSTZ491VXQ/knoema-economy-data-atlas)</button> share.  Click "Get" then name the database **economy_data_atlas** and grant access to the **public** role.

```markdown
## Verify Data Marketplace Share
    select top 1 *
    from economy_data_atlas.economy.usindssp2020;
```
Run the <button>[finserv demo 20 Marketplace](https://github.com/Snowflake-Labs/sfguide-financial-asset-management/blob/master/setup/finserv%20demo%2010%20setup.sql)</button> script.


<!-- ------------------------ -->
## 30 DDL
Duration: 2

We:
- Size up compute to create 3 billion synthetic trades
- Insert those trades ordered by trader, symbol, and date so any queries on that data are signficantly faster
- Create a cluster key to future proof that trade table from any data that has been inserted without being sorted
- Create a window function to calculate real time trades, cash, and Profit and Loss (PnL)

Run the <button>[finserv demo 30 DDL](https://github.com/Snowflake-Labs/sfguide-financial-asset-management/blob/master/setup/finserv%20demo%2030%20DDL.sql)</button> script.

<!-- ------------------------ -->
## 40 Queries
Duration: 2

We:
- Query 3 billion rows with only small compute and 3 second run-time
- See Snowflake's 3 caches
- Zero Copy Clone for DevOps and instant sandboxes
- Time Travel to see and roll back up to 90 days of data
- Drop and Undrop Tables

Run the <button>[finserv demo 40 queries](https://github.com/Snowflake-Labs/sfguide-financial-asset-management/blob/master/setup/finserv%20demo%2040%20queries.sql)</button> script.


<!-- ------------------------ -->
## 90 Optional Reset
Duration: 2

Optional Script to reset / remove all objects created during this demo

We:
- Query 3 billion rows with only small compute and 3 second run-time
- See Snowflake's 3 caches
- Zero Copy Clone for DevOps and instant sandboxes
- Time Travel to see and roll back up to 90 days of data
- Drop and Undrop Tables

Run the <button>[finserv demo 40 queries](https://github.com/Snowflake-Labs/sfguide-financial-asset-management/blob/master/optional/finserv%20demo%2090%20reset.sql)</button> script.

<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- Query free stock market history data instantly with zero learning curve and time
- Run a Python faker function to create 100 synthetic traders
- Size up compute to create 3 billion synthetic trades
- Insert those trades ordered by trader, symbol, and date so any queries on that data are signficantly faster
- Create a cluster key to future proof that trade table from any data that has been inserted without being sorted
- Create a window function to calcluate real time trades, cash, and Profit and Loss (PnL)
- Query 3 billion rows with only small compute and 3 second run-time
- See Snowflake's 3 caches
- Zero Copy Clone for DevOps and instant sandboxes
- Time Travel to see and roll back up to 90 days of data
- Drop and Undrop Tables

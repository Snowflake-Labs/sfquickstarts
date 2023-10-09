author: Kelsey Hammock
id: secure_your_organization_with_security_analytics_using_snowflake_and_Sigma
summary: Learn how to monitor your Snowflake security posture using Sigma
categories: cybersecurity, data-warehousing
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Cybersecurity, 

# Secure Your Organization with Security Analytics Using Snowflake and Sigma
<!-- ------------------------ -->
## Overview 

### Prerequisites
- Familiarity with Snowflake's [unique DCR architecture](https://www.snowflake.com/blog/distributed-data-clean-rooms-powered-by-snowflake/)
- Working knowledge with Snowflake database objects and the [Snowflake Web UI](https://docs.snowflake.com/en/user-guide/ui-web.html)
- Clear understanding of how Snowflake [Secure Data Sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro.html) works
- Experience going through the [two-party Data Clean Room Quickstart](https://quickstarts.snowflake.com/guide/build_a_data_clean_room_in_snowflake_advanced/index.html?index=..%2F..index#0)


### What you’ll learn 
- How to create and deploy a DCR environment between three Snowflake accounts
- How the two-party clean room can be extended to a third account (a second provider)

### What you’ll build 
This Quickstart lab will walk you through the process of deploying a Snowflake **v5.5** DCR environment, which is our latest General Availability (GA) release. 
- Shows a multi-party DCR environment
- Leverages Jinja SQL templating language tags and logic
- Includes example query templates for some common advertising scenarios

### What you’ll need 
- **Three** Snowflake accounts - either [Enterprise or Business Critical edition](https://docs.snowflake.com/en/user-guide/intro-editions.html) - that are deployed in the **same** [cloud provider and region](https://docs.snowflake.com/en/user-guide/intro-regions.html). You may procure these as [Snowflake 30-day free trial accounts](https://docs.snowflake.com/en/user-guide/admin-trial-account.html) to make things easier for you - Simply go through the signup process three times on [signup.snowflake.com](https://signup.snowflake.com), making certain to select the **same cloud provider and region** for each. You may reuse the two accounts created for the [two-party Data Clean Room Quickstart](https://quickstarts.snowflake.com/guide/build_a_data_clean_room_in_snowflake_advanced/index.html?index=..%2F..index#0), if they are still available, and simply add a third.
- Logins to **all** of the Snowflake accounts should have [ACCOUNTADMIN role access](https://docs.snowflake.com/en/user-guide/security-access-control-considerations.html) (note that [Snowflake free trial accounts](https://docs.snowflake.com/en/user-guide/admin-trial-account.html) provide this automatically, which is why I suggest using them for this Quickstart).


<!-- ------------------------ -->
## Getting started
Duration: 10

### Log into all Snowflake accounts

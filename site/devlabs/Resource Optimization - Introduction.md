summary: This is a guide that can be used to introduce customers to the best practices for optimizing their  resource consumption at Snowflake.  This is accompanied by four other guides that go into greater detail around each category: Setup & Configuration, Usage Monitoring, Billing Metrics, and Performance Optimizations.
id: resourceoptimization-introduction
categories: resource-optimization
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/devlabs/issues
tags: Resource Optimization, Cost Optimization, Consumption, Monitoring, Optimization
authors: Matt Meredith

#Introduction to Snowflake Resource Optimization

<!-- -------------->

##Introduction

This guide is to serve as the introduction to a series of Snowflake Resource Optimization guides to help our customers better optimize their credit consumption within Snowflake.  It is in the mutual interest of both Snowflake and our customers to ensure an efficient process when it comes to monitoring and consuming credits within Snowflake.  This set of Snowflake Guides focused on Resource Optimization are just one key asset helping with this process.  The following Snowflake Guides are available to assist you in your journey of optimizing how you consume credits on Snowflake.

###Snowflake Guides for Resource Optimization

####Setup & Configuration Guide to Resource Optimization
This guide is designed to enable Snowflake customers to better understand and identify focal points around how their warehouses, users, and other factors are setup and configured to control consumption.  These queries are critical to preventing and limiting excess-consumption against your Snowflake account.

####Usage Monitoring Guide to Resource Optimization
These queries are designed to identify the warehouses, queries, tools, and users that are responsible for consuming the most credits over a specified period of time. These queries can be used to determine which of those resources are consuming more credits than anticipated and take the necessary steps to reduce their consumption.

####Billing Metrics Guide to Resource Optimization
Billing queries are responsible for identifying total costs associated with the high level functions of the Snowflake Cloud Data Platform, which includes warehouse compute, snowpipe compute, and storage costs. If costs are noticeably higher in one category versus the others, you may want to evaluate what might be causing that.

These metrics also seek to identify those queries that are consuming the most amount of credits. From there, each of these queries can be analyze for their importance (do they need to be run as frequently, if at all) and explore if additional controls need to be in place to prevent excessive consumption (i.e. resource monitors, statement timeouts, etc.).

####Performance Optimization Guide to Resource Optimization
The queries provided in this guide are intended to help you identify areas in which poor performance might be causing excess consumption, driven by a variety of factors.

###Query Tiers
Each query within the Resource Optimization Snowflake Guides will have a tier designation just below its name.  The following tier descriptions should help to better understand those designations.

####Tier 1 Queries
At its core, Tier 1 queries are essential to Resource Optimization at Snowflake and should be used by each customer to help with their consumption monitoring - regardless of size, industry, location, etc.

####Tier 2 Queries
Tier 2 queries, while still playing a vital role in the process, offer an extra level of depth around Resource Optimization and while they may not be essential to all customers and their workloads, it can offer further explanation as to any additional areas in which over-consumption may be identified.

####Tier 3 Queries
Finally, Tier 3 queries are designed to be used by customers that are looking to leave no stone unturned when it comes to optimizing their consumption of Snowflake.  While these queries are still very helpful in this process, they are not as critical as the queries in Tier 1 & 2.
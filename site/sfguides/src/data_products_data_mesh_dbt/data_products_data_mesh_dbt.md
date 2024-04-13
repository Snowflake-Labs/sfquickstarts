author: Sean McIntyre
id: data-product-data-mesh-dbt
summary: This is a sample Snowflake Guide
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Build Data Products and Data Mesh with dbt Cloud
<!-- ------------------------ -->
## Overview 
Duration: 1

Please use [this markdown file](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) as a template for writing your own Snowflake Quickstarts. This example guide has elements that you will use when writing your own guides, including: code snippet highlighting, downloading files, inserting photos, and more. 

It is important to include on the first page of your guide the following sections: Prerequisites, What you'll learn, What you'll need, and What you'll build. Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial; this means that actual code needs to be included (not just pseudo-code).

The rest of this Snowflake Guide explains the steps of writing your own guide. 

### Prerequisites
- Requires intermediate dbt familiarity
  - If you're not familiar with dbt, please do dbt Fundamentals first
  - Or if you are not a developer, please see such and such blog post / slides

### What You’ll Learn 
- how to set the metadata for a guide (category, author, id, etc)
- how to set the amount of time each slide will take to finish 
- how to include code snippets 
- how to hyperlink items 
- how to include images 

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed
- [NodeJS](https://nodejs.org/en/download/) Installed
- [GoLang](https://golang.org/doc/install) Installed

### What You’ll Build 
- A Snowflake Guide

<!-- ------------------------ -->
## Setup
Duration: 2
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step
- Get a dbt Cloud account
  - has to be able to create 2 projects for x-project ref... or does it? :thinkingface:
- Get a Snowflake account
  - Access to TPCH

### PROD: Content

Empty

<!-- ------------------------ -->
## The story / background
Duration: 2
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

- I'm thinking we need to set the stage for the people going through the QS guide. Might be a major hurdle, how do we get this effective without losing busy people?
  - Maybe a video format as well?
  - Nice graphic to explain what we're building?

### PROD: Content

We have sales and customer data in our source systems (TPCH)

There’s a team that builds the foundational data marts for the company off the ERP system. They are seasoned data engineers, with average experience 10 years. 2 years ago, they migrated their on-premise systems to Snowflake and dbt, and will never go back. The efficiency gained in dbt over their previous tools: SPs and graphical drag & drop tools is considerate.

The other teams in the company (marketing, sales) are excited to get their hands on data, and build their own transformations on top of the data that’s been built. They are thinking of doing some of their own reporting, and their own ML/AI, and want consistency of their data, so that‘s why they don’t build directly in the BI tool. More and more people are getting involved, there’s a new roadmap. A lot of these people have never been called “data engineers”, but more and more their jobs are looking like “analytics engineers” — people who do make business logic in Excel and BI tools,

The CDO’s main initiative this year is to get more people involved in data, because the initiatives are to increase usage of data in decisions, to have more accuracy and to save money

The data platform team as a result looks to enable more and more people to own data pipelines on top of Snowflake. They’ve selected dbt Cloud to do this, because of the dbt Mesh capabilities

The data platform team is interested in the FAIR principles of Data Mesh: Findable, Accessible, Interoperable, Repeatable. Since a lot of the data in the organization ends up in Snowflake, Snowflake is a natural place to center their data mesh around (even though not all the data is in Snowflake).

Additionally, the data platform team wants to stop thinking in terms of team-based work, they would rather think in terms of data products: datasets should be created by teams, and be reliable, useful, secure, and well-governed, following DAUTNIVS principles. Then, Data Products can be composed in the mesh, giving modularity, reducing silos, and decreasing overall operating expenditures of the data program at their company.

Here’s how they can do it

<!-- ------------------------ -->
## Building out the dbt models
Duration: 2
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

> aside positive
> 
> Ready for dev!

- From TPCH, get to a `fct_orders` and a `dim_customers`
- Includes a `models.yml` with good documentation
- Commit and deploy -> run a job

Side-thought, would it make sense to link out to a reference base git repo?

### PROD: Content

Empty

<!-- ------------------------ -->
## Securing the data with Snowflake governance features
Duration: 2
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

- Demonstrate how to use dbt to do Snowflake:
  - Tagging
  - Masking
  - Grants / access controls
  - (bonus points) column or row level security
- Simple idea could be to do this on `dim_customers`, as there's PII: name, address, etc.
- Commit and deploy -> run a job

Side-thought, would it make sense to link out to a reference base git repo?

### PROD: Content

Empty

<!-- ------------------------ -->
## Making the data available to other dbt users with dbt Mesh model governance features
Duration: 1
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

- Demonstrate how to add:
  - Model contracts
  - Model access
  - model versions -> oh, requirements changed, we need to break out tier_name to low/mid/high_tier boolean
- Commit and deploy -> run a job

### PROD: Content

Empty

<!-- ------------------------ -->
## Create downstream dbt project that accesses base project
Duration: 1
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

- Demonstrate how to add:
  - Create new project
  - Link to first project
  - Cross-project ref
- Commit and deploy -> run a job (?)

### PROD: Content

Empty

<!-- ------------------------ -->
## Other stuff I don't know where it fits
Duration: 1
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

- dbt Cloud RBAC
- dbt Explorer
- Snowflake Private Listings

### PROD: Content

Empty


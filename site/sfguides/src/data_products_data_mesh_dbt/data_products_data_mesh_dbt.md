summary: Data mesh with Snowflake and dbt Cloud
id: data_products_data_mesh_dbt
categories: featured, getting-started, data-engineering
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Data Mesh
authors: Sean McIntyre

# Build Data Products and Data Mesh with dbt Cloud

## Overview 
Duration: 2

Data mesh is gaining traction as a transformative approach to data architecture within large organizations, emphasizing decentralized domain-specific data ownership coupled with federated governance and a robust self-service data infrastructure. By aligning dbt Cloud with Snowflake's capabilities, organizations can adopt these principles more effectively, leveraging domain-oriented design to manage and organize data as interconnected products rather than isolated datasets. This hands-on lab will demonstrate how dbt Cloud can be utilized to not only facilitate the development and maintenance of these data products on Snowflake but also to enhance the speed and quality with which these products are delivered.

In this guide, participants will explore how dbt Cloud's integration with Snowflake supports a data mesh by enabling better management of data dependencies, automation of data transformations, and continuous integration and delivery of data products. Through practical examples and guided exercises, you will learn how to set up your dbt Cloud environment to interact seamlessly with Snowflake, creating a scalable and efficient data infrastructure. By the end of this lab, you will understand how dbt Cloud enhances data visibility and accessibility in Snowflake, allowing platform teams to govern the mesh effectively and validate compliance of data products. Additionally, the session will cover strategies to make these data products discoverable and accessible to authorized users, ensuring that the right data is available to the right people at the right time.

### Prerequisites
- Requires intermediate dbt familiarity
  - If you're not familiar with dbt, please do [dbt Fundamentals](https://courses.getdbt.com/courses/fundamentals) first
  - Or if you are not a developer, please see such and such blog post / slides

- dbt Cloud
    - You must have a dbt Cloud Enterprise account
    - Set your development and deployment [environments](https://docs.getdbt.com/docs/dbt-cloud-environments) to use dbt version 1.6 or later. You can also opt Keep on latest version of to always use the latest version of dbt.

- Snowflake
    - Access to a Snowflake account
    - Access to the TPCH dataset, specifically in the `SNOWFLAKE_SAMPLE_DATA` database and the `TPCH_SF1` schema.

### What You’ll Learn
* How to understand when data mesh is the right solution for your organization

* How to ensure proper governance of your Snowflake environment

* How to properly set up a dbt Cloud account with dbt Mesh

* How to utilize dbt's model governance features to increase the resiliency of your data mesh landscape

### What You’ll Build 

* A dbt Cloud account containing multiple projects that showcase the governance features of Snowflake (Object tagging, masking, grants) alongside dbt Cloud's dbt Mesh framework

## The story / background
Duration: 5
<!-- TODO: Fix this ^^ -->

### DEV: Guideline to this step

- I'm thinking we need to set the stage for the people going through the QS guide. Might be a major hurdle, how do we get this effective without losing busy people?
  - Maybe a video format as well?
  - Nice graphic to explain what we're building?

### PROD: Content

We have sales and customer data in our source systems (TPCH)

There’s a team that builds the foundational data marts for the company off the ERP system. They are seasoned data engineers, with average experience 10 years. 2 years ago, they migrated their on-premise systems to Snowflake and dbt, and will never go back. The efficiency gained in dbt over their previous tools: SPs and graphical drag & drop tools is considerate.

The other teams in the company (finance, marketing, sales) are excited to get their hands on data, and build their own transformations on top of the data that’s been built. They are thinking of doing some of their own reporting, and their own ML/AI, and want consistency of their data, so that‘s why they don’t build directly in the BI tool. More and more people are getting involved, there’s a new roadmap. A lot of these people have never been called “data engineers”, but more and more their jobs are looking like “analytics engineers” — people who do make business logic in Excel and BI tools,

The CDO’s main initiative this year is to get more people involved in data, because the initiatives are to increase usage of data in decisions, to have more accuracy and to save money

The data platform team as a result looks to enable more and more people to own data pipelines on top of Snowflake. They’ve selected dbt Cloud to do this, because of the dbt Mesh capabilities

The data platform team is interested in the FAIR principles of Data Mesh: Findable, Accessible, Interoperable, Repeatable. Since a lot of the data in the organization ends up in Snowflake, Snowflake is a natural place to center their data mesh around (even though not all the data is in Snowflake).

Additionally, the data platform team wants to stop thinking in terms of team-based work, they would rather think in terms of data products: datasets should be created by teams, and be reliable, useful, secure, and well-governed, following DAUTNIVS principles. Then, Data Products can be composed in the mesh, giving modularity, reducing silos, and decreasing overall operating expenditures of the data program at their company.

Here’s how they can do it

<!-- ------------------------ -->
## dbt Cloud Account Setup
Duration: 10
<!-- TODO: Fix this ^^ -->

### Create and configure two projects

In this section, you'll create two new, empty projects in dbt Cloud to serve as your foundational and downstream projects:

- **Foundational projects** (or upstream projects) typically contain core models and datasets that serve as the base for further analysis and reporting.
- **Downstream projects** build on these foundations, often adding more specific transformations or business logic for dedicated teams or purposes. 

Insert image here showing picture of project setup

To [create](/docs/cloud/about-cloud-setup) a new project in dbt Cloud:

1. From **Account settings**, click **+ New Project**.
2. Enter a project name and click **Continue**.
   - Use "Jaffle | Data Platform" for one project
   - Use "Jaffle | Finance" for the other project
3. Select your data platform, then **Next** to set up your connection.
4. In the **Configure your environment** section, enter the **Settings** for your new project.
5. Click **Test Connection**. This verifies that dbt Cloud can access your data platform account.
6. Click **Next** if the test succeeded. If it fails, you might need to go back and double-check your settings.
   - For this guide, make sure you create a single [development](/docs/dbt-cloud-environments#create-a-development-environment) and [Deployment](/docs/deploy/deploy-environments) per project.
     - For "Jaffle | Data Platform", set the default database to `jaffle_da`.
     - For "Jaffle | Finance", set the default database to `jaffle_finance`

**TODO** - Insert gif here of going through the project setup process

7. Select managed 

7. Continue the prompts to complete the project setup. Once configured, each project should have:
    - A data platform connection
    - New git repo
    - One or more [environments](/docs/deploy/deploy-environments) (such as development, deployment)

## Build Foundational Project
Duration: 10

This upstream project is where you build your core data assets. This project will contain the raw data sources, staging models, and core business logic.

dbt Cloud enables data practitioners to develop in their tool of choice and comes equipped with a local [dbt Cloud CLI](/docs/cloud/cloud-cli-installation) or in-browser [dbt Cloud IDE](/docs/cloud/dbt-cloud-ide/develop-in-the-cloud).

In this section of the guide, you will set the "Jaffle | Data Platform" project as your foundational project using the dbt Cloud IDE.

1. First, navigate to the **Develop** page to verify your setup.
2. Click **Initialize dbt project** if you’ve started with an empty repo:

3. Delete the `models/example` folder.  
4. Navigate to the `dbt_project.yml` file and rename the project (line 5) from `my_new_project` to `platform`.
5. In your `dbt_project.yml` file, remove lines 39-42 (the `my_new_project` model reference).
6. In the **File Explorer**, hover over the project directory and click the **...**, then select **Create file**.
7. Create two new folders: `models/staging` and `models/core`.


### Staging layer
Now that you've set up the foundational project, let's start building the data assets. Set up the staging layer as follows:

1. Create a new YAML file `models/staging/sources.yml`.
2. Declare the sources by copying the following into the file and clicking **Save**.

```yaml
sources:
  - name: tpch
    description: TPCH data source from Snowflake Sample Data
    database: snowflake_sample_data
    schema: tpch_sf1
    tables:
      - name: orders
        description: One record per order
      - name: customer
        description: One record per customer
      - name: lineitem
        description: One record per line item within a single order (1 -> n)
```

3. Create a `models/staging/stg_customers.sql` file to select from the `customers` table in the `tpch` source.

```sql
with source as (

    select * from {{ source('tpch', 'customer') }}

),

cleanup as (

    select
    
        c_custkey as customer_key,
        c_name as name,
        c_address as address, 
        c_nationkey as nation_key,
        c_phone as phone_number,
        c_acctbal as account_balance,
        c_mktsegment as market_segment,
        c_comment as comment

    from source

)

select * from cleanup
```

4. Create a `models/staging/stg_orders.sql` file to select from the `orders` table in the `tpch` source.

```sql
with source as (

    select * from {{ source('tpch', 'orders') }}

),

renamed as (

    select
    
        o_orderkey as order_key,
        o_custkey as customer_key,
        o_orderstatus as status_code,
        o_totalprice as total_price,
        o_orderdate as order_date,
        o_clerk as clerk_name,
        o_orderpriority as priority_code,
        o_shippriority as ship_priority,
        o_comment as comment

    from source

)

select * from renamed
```

5. Create a `models/staging/stg_line_items.sql` file to select from the `line_items` table in the `tpch` source.

```sql
with source as (

    select * from {{ source('tpch', 'lineitem') }}

),

renamed as (

    select
    
        l_orderkey as order_key,
        l_partkey as part_key,
        l_suppkey as supplier_key,
        l_linenumber as line_number,
        l_quantity as quantity,
        l_extendedprice as gross_item_sales_amount,
        l_discount as discount_percentage,
        l_tax as tax_rate,
        l_returnflag as return_flag,
        l_linestatus as status_code,
        l_shipdate as ship_date,
        l_commitdate as commit_date,
        l_receiptdate as receipt_date,
        l_shipinstruct as ship_instructions,
        l_shipmode as ship_mode,
        l_comment as comment,

        -- extended_price is actually the line item total,
        -- so we back out the extended price per item
        (gross_item_sales_amount/nullif(quantity, 0))::decimal(16,4) as base_price,
        (base_price * (1 - discount_percentage))::decimal(16,4) as discounted_price,
        (gross_item_sales_amount * (1 - discount_percentage))::decimal(16,4) as discounted_item_sales_amount,

        -- We model discounts as negative amounts
        (-1 * gross_item_sales_amount * discount_percentage)::decimal(16,4) as item_discount_amount,
        ((gross_item_sales_amount + item_discount_amount) * tax_rate)::decimal(16,4) as item_tax_amount,
        (
            gross_item_sales_amount + 
            item_discount_amount + 
            item_tax_amount
        )::decimal(16,4) as net_item_sales_amount

    from source

)

select * from renamed
```

### Core Layer

Now set up the core layer as follows:

1. Create a `models/core/fct_orders.sql` to build a fact table with order details

```sql
{{
    config(
        materialized = 'table',
        tags=['finance']
    )
}}


with orders as (
    
    select * from {{ ref('stg_orders') }}

),

line_items as (
    
    select * from {{ ref('stg_line_items') }}

),

order_item_summary as (

    select 
        order_key,
        sum(gross_item_sales_amount) as gross_item_sales_amount,
        sum(item_discount_amount) as item_discount_amount,
        sum(item_tax_amount) as item_tax_amount,
        sum(net_item_sales_amount) as net_item_sales_amount
    from line_items
    group by
        1
),
final as (

    select 

        orders.order_key, 
        orders.order_date,
        orders.customer_key,
        orders.status_code,
        orders.priority_code,
        orders.ship_priority,
        orders.clerk_name,
        1 as order_count,
        order_item_summary.gross_item_sales_amount,
        order_item_summary.item_discount_amount,
        order_item_summary.item_tax_amount,
        order_item_summary.net_item_sales_amount
    from orders
    inner join order_item_summary
      on orders.order_key = order_item_summary.order_key
)
select *
from final
order by order_date
```

2. Create a `models/core/dim_customers.sql` to build a dimensional table with customer details

```sql
{{
    config(
        materialized = 'table',
    )
}}

with customer as (

    select * from {{ ref('stg_customers') }}

),

final as (
    select 
        customer_key,
        name,
        address,
        nation_key,
        phone_number,
        account_balance,
        market_segment
    from customer
)
select *
from final
order by customer_key
```

### Execute

Navigate to the [Command bar](https://arc.net/l/quote/kfovefjk) and execute a `dbt run`.  This will both validate the work you've done thus far and build out the requisite models into your sandbox within Snowflake.

## Mesh Components:  Snowflake
Duration: 10

The goal of this section is to apply some of the functionality offered from Snowflake, like [object tagging](https://docs.snowflake.com/en/user-guide/object-tagging#label-object-tags-ddl-privilege-summary) and [dynamic data masking](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro), to strengthen the governance around the data mesh architecture we want to architect.

The first thing we'll need to do is set up a role specifically for applying these governance practices to the Snowflake environment.  The code below will:

- Create a `DATA_GOVERNOR` role for administering data governance responsibilities and grant appropriate permissions for masking and tagging
- Create a `PII_ROLE` for users who can access PII data unmasked

```sql
use role accountadmin;

-- data governor role setup
create role if not exists data_governor;
grant role data_governor to user doug_g2;

-- grants for data governor
grant usage on database snowflake_sample_data to role data_governor;
grant usage on schema snowflake_sample_data.tpch_sf1 to role data_governor;
grant create tag on schema snowflake_sample_data.tpch_sf1 to role data_governor;
grant create masking policy on schema snowflake_sample_data.tpch_sf1 to role data_governor;
grant apply masking policy on account to role data_governor;
grant apply tag on account to role data_governor;

-- pii_allowed role setup
create role if not exists pii_allowed;
grant role pii_allowed to user doug_g2;

-- grant appropriate access on the table to the pii_allowed role and public
grant usage on database snowflake_sample_data to role pii_allowed;
grant usage on schema snowflake_sample_data.tpch_sf1 to role pii_allowed;
grant select on all tables in schema snowflake_sample_data.tpch_sf1 to role pii_allowed;
```

Next, we'll use the `DATA_GOVERNOR` role to perform the following:

- Create a tag for PII data
- Create a masking policy for string data
- Assign the masking policy to the tag
- Assign the tag to the `name` column in the `customers` table

```sql
use role data_governor;
use database snowflake_sample_data;

-- create the tag
create tag if not exists snowflake_sample_data.tpch_sf1.pii_data;

-- create the policy
create masking policy snowflake_sample_data.tpch_sf1.pii_mask_string as (val string) returns string ->
  case
    when is_role_in_session('PII_ALLOWED') then val
    else '****'
  end;

-- assign masking policy to tag
alter tag snowflake_sample_data.tpch_sf1.pii_data set masking policy snowflake_sample_data.tpch_sf1.pii_mask_string;

-- assign tag to sensitive columns
use role data_governor;
alter table snowflake_sample_data.tpch_sf1.customer modify column c_name set tag snowflake_sample_data.tpch_sf1.pii_data = 'C_NAME';
```

Now, test to ensure that only users with `PII_ALLOWED` role are authorized to view the columns tagged as `PII_DATA` unmasked.

```sql
-- role authorized to view pii_data unmasked
use role pii_allowed;

-- NAME column is unmasked
select * from snowflake_sample_data.tpch_sf1.customer;

-- role unauthorized to view pii_data
use role public;

-- NAME column is masked
select * from snowflake_sample_data.tpch_sf1.customer;
```

Now that we've set up the appropriate roles, tags, and masking policies in Snowflake, it's time to jump into dbt Cloud and use some of the features there to further strengthen our data mesh architecture.

## Mesh Components:  dbt Cloud

<!-- ------------------------ -->
## Securing the data with Snowflake governance features


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


author: Chanin Nantasenamat
id: snowflake-semantic-view-business-ready-queries
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/product/ai
language: en
summary: Learn how to create Semantic Views in Snowflake to abstract complex SQL, centralize business logic, and expose consistent, reusable data models for analytics and BI.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Build Business-Ready Queries with Snowflake Semantic Views
<!-- ------------------------ -->
## Overview

Data practitioners often face a frustrating reality: to answer even simple business questions, they must write complex SQL queries that span multiple tables, require intricate `JOIN` logic, and repeat the same aggregation formulas across different reports. A question like *"What were our sales by store manager last year?"* might require 20+ lines of SQL, knowledge of the exact table schema, and the correct `JOIN` conditions. This complexity creates barriers: business analysts depend on data engineers for every query, metrics become inconsistent across teams, and onboarding new team members takes weeks instead of days.

Snowflake Semantic Views solve this by creating a business-friendly abstraction layer over complex database schemas. You define relationships between tables once, create reusable metrics with consistent definitions, and enable anyone to write simpler, more intuitive queries. The same 20 line query becomes 5 lines of Semantic SQL that reads like a business question.

In this tutorial, you'll learn how to transform complex SQL queries into simple, business-friendly Semantic SQL using Snowflake's Semantic Views. We'll use the industry-standard TPC-DS benchmark dataset to demonstrate how Semantic Views can dramatically simplify your data analytics workflow.

### What You'll Learn
- How to create Semantic Views in Snowflake
- The difference between Traditional SQL and Semantic SQL
- How to define table relationships, dimensions, facts, and metrics
- Query patterns for varying complexity levels
- Best practices for building business-ready analytics

### What You'll Build
A comprehensive Semantic View over the TPC-DS dataset that enables simplified querying across multiple sales channels (store, web, catalog), customer demographics, and inventory data.

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Access to `SNOWFLAKE_SAMPLE_DATA` database
- Access to `ACCOUNTADMIN` role (required for creating semantic views)
- Basic SQL knowledge
- Familiarity with data modeling concepts

<!-- ------------------------ -->
## About the TPC-DS Dataset

The **TPC-DS (Transaction Processing Performance Council - Decision Support)** benchmark is the industry-standard dataset for modeling complex decision support systems. It simulates a global retail empire with multiple sales channels including:

- **Store sales**: Traditional brick-and-mortar retail transactions
- **Web sales**: E-commerce transactions
- **Catalog sales**: Mail-order catalog purchases
- **Store returns**: Product returns and exchanges

The dataset includes:
- **Dimension tables**: Store, Item, Customer, Date, Warehouse, Ship Mode, and more
- **Fact tables**: Store Sales, Web Sales, Catalog Sales, Inventory, and Returns
- **Scale Factor**: We're using the SF10TCL scale (10TB scale factor) from Snowflake's sample data

### Traditional SQL vs Semantic SQL

We'll compare two approaches to querying the data:

- **Traditional SQL**: Requires explicit `JOIN` clauses, fully-qualified table references, and manual aggregation logic
- **Semantic SQL**: Uses the semantic view to abstract complexity, making queries shorter and more business-focused

### Query Complexity Framework

To systematically explore how Semantic Views simplify queries, we organize examples by complexity level:

| Complexity Level | Description | What It Means |
|-----------------|-------------|---------------|
| **Simple Questions** | Simple filters on 1-2 tables | Basic `SELECT` with `WHERE` clauses |
| **Simple Questions with Aggregations** | Aggregations and metrics on 1-2 tables | `GROUP BY`, `SUM()`, `COUNT()` on simple schemas |
| **Advanced Questions** | Simple filters across 3+ tables | Easy question, but complex table relationships |
| **Advanced Questions with Aggregations** | Aggregations across 3+ tables | Complex calculations across many tables |

**Key Insight:** Semantic Views provide progressively more value as query complexity increases. Simple queries remain simple, but complex multi-table aggregations see dramatic improvements, reducing from 25+ lines of Traditional SQL to 10-12 lines of Semantic SQL.

<!-- ------------------------ -->
## Setup

### Notebook

You can follow along this quickstart using the [build-business-ready-queries-with-snowflake-semantic-views.ipynb](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Snowflake_Semantic_View_Business_Ready_Queries/build-business-ready-queries-with-snowflake-semantic-views.ipynb) notebook file.

### Create Semantic Views

Semantic Views are created using the `CREATE SEMANTIC VIEW` statement, which defines five key components:

| Component | Purpose | Example |
|-----------|---------|---------|
| `TABLES` | Register source tables with their primary keys | `store AS SNOWFLAKE_SAMPLE_DATA...store PRIMARY KEY (s_store_sk)` |
| `RELATIONSHIPS` | Define foreign key relationships between tables | `sales_to_store AS store_sales (ss_store_sk) REFERENCES store` |
| `FACTS` | Define row-level expressions and computed columns (non-aggregated) | `f_net_profit_tier AS CASE WHEN ss_net_profit > 25000 THEN...` |
| `DIMENSIONS` | Define categorical attributes for grouping and filtering | `store.s_city AS store.s_city comment='City where store is located'` |
| `METRICS` | Define reusable aggregate expressions (`SUM`, `COUNT`, `AVG`) | `total_sales AS SUM(ss_sales_price * ss_quantity)` |

For more details, see the [Snowflake Semantic Views documentation](https://docs.snowflake.com/en/user-guide/views-semantic/sql).

Run the following SQL to create the Semantic View for the TPC-DS dataset:

```sql
USE DATABASE SNOWFLAKE_LEARNING_DB;
USE SCHEMA PUBLIC;

CREATE OR REPLACE SEMANTIC VIEW tpcds_nlq_view
  TABLES (
    store AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.store PRIMARY KEY (s_store_sk),
    store_sales AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.store_sales PRIMARY KEY (ss_item_sk, ss_ticket_number),
    web_sales AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.web_sales PRIMARY KEY (ws_item_sk, ws_order_number),
    catalog_sales AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.catalog_sales PRIMARY KEY (cs_item_sk, cs_order_number),
    store_returns AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.store_returns PRIMARY KEY (sr_item_sk, sr_ticket_number),
    item AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.item PRIMARY KEY (i_item_sk),
    returned_item AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.item PRIMARY KEY (i_item_sk) COMMENT = 'Dimension for returned items',
    customer AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.customer PRIMARY KEY (c_customer_sk),
    customer_address AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.customer_address PRIMARY KEY (ca_address_sk),
    current_customer_demographics AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.customer_demographics PRIMARY KEY (cd_demo_sk) COMMENT = 'Dimension for Current customer demographics',
    customer_demographics AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.customer_demographics PRIMARY KEY (cd_demo_sk) COMMENT = 'Dimension for Customer demographics at the time of sale',
    date_dim AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.date_dim PRIMARY KEY (d_date_sk),
    hd AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.household_demographics PRIMARY KEY (hd_demo_sk),
    income_band AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.income_band PRIMARY KEY (ib_income_band_sk),
    web_site AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.web_site PRIMARY KEY (web_site_sk),
    inventory AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.inventory PRIMARY KEY (inv_date_sk, inv_item_sk, inv_warehouse_sk),
    ship_mode AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.ship_mode PRIMARY KEY (sm_ship_mode_sk),
    warehouse AS SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.warehouse PRIMARY KEY (w_warehouse_sk)
  )
  RELATIONSHIPS (
    sales_to_store AS store_sales (ss_store_sk) REFERENCES store,
    sales_to_customer AS store_sales (ss_customer_sk) REFERENCES customer,
    sales_to_date AS store_sales (ss_sold_date_sk) REFERENCES date_dim,
    sales_to_customer_demo AS store_sales (ss_cdemo_sk) REFERENCES customer_demographics,
    sales_to_item AS store_sales (ss_item_sk) REFERENCES item,
    web_sales_to_bill_customer AS web_sales (ws_bill_customer_sk) REFERENCES customer,
    web_sales_to_sold_date AS web_sales (ws_sold_date_sk) REFERENCES date_dim,
    web_sales_to_bill_customer_demo AS web_sales (ws_bill_cdemo_sk) REFERENCES customer_demographics,
    web_sales_to_item AS web_sales (ws_item_sk) REFERENCES item (i_item_sk),
    web_sales_to_web_site AS web_sales (ws_web_site_sk) REFERENCES web_site,
    catalog_sales_to_bill_customer AS catalog_sales (cs_bill_customer_sk) REFERENCES customer,
    catalog_sales_to_sold_date AS catalog_sales (cs_sold_date_sk) REFERENCES date_dim,
    catalog_sales_to_bill_customer_demo AS catalog_sales (cs_bill_cdemo_sk) REFERENCES customer_demographics,
    catalog_sales_to_item AS catalog_sales (cs_item_sk) REFERENCES item,
    sales_returns_to_item AS store_returns (sr_item_sk) REFERENCES returned_item (i_item_sk),
    sales_returns_to_sales AS store_returns (sr_ticket_number, sr_item_sk, sr_customer_sk) REFERENCES store_sales (ss_ticket_number, ss_item_sk, ss_customer_sk),
    customer_to_customer_address AS customer (c_current_addr_sk) REFERENCES customer_address (ca_address_sk),
    customer_to_household_demo AS customer (c_current_hdemo_sk) REFERENCES hd,
    customer_to_customer_demo AS customer (c_current_cdemo_sk) REFERENCES current_customer_demographics (cd_demo_sk),
    household_demo_to_income_band AS hd (hd_income_band_sk) REFERENCES income_band,
    inventory_to_item AS inventory (inv_item_sk) REFERENCES item,
    inventory_to_date AS inventory (inv_date_sk) REFERENCES date_dim,
    catalog_sales_to_ship_mode AS catalog_sales (cs_ship_mode_sk) REFERENCES ship_mode,
    web_sales_to_ship_mode AS web_sales (ws_ship_mode_sk) REFERENCES ship_mode
  )
  FACTS (
    store_sales.f_ss_item_sk AS ss_item_sk
      COMMENT = 'Item SKU (Stock Keeping Unit) for each sale',
    store_sales.f_net_profit_tier AS CASE
      WHEN store_sales.ss_net_profit > 25000 THEN 'More than 25000'
      WHEN store_sales.ss_net_profit BETWEEN 3000 AND 25000 THEN '3000-25000'
      WHEN store_sales.ss_net_profit BETWEEN 2000 AND 3000 THEN '2000-3000'
      WHEN store_sales.ss_net_profit BETWEEN 300 AND 2000 THEN '300-2000'
      WHEN store_sales.ss_net_profit BETWEEN 250 AND 300 THEN '250-300'
      WHEN store_sales.ss_net_profit BETWEEN 200 AND 250 THEN '200-250'
      WHEN store_sales.ss_net_profit BETWEEN 150 AND 200 THEN '150-200'
      WHEN store_sales.ss_net_profit BETWEEN 100 AND 150 THEN '100-150'
      WHEN store_sales.ss_net_profit BETWEEN 50 AND 100 THEN ' 50-100'
      WHEN store_sales.ss_net_profit BETWEEN 0 AND 50 THEN '  0- 50'
      ELSE ' 50 or Less'
    END
      COMMENT = 'Tier labels for net profit from store sales',
    date_dim.f_year AS date_dim.d_year
      COMMENT = 'Year of Date',
    store_returns.f_ss_has_sales AS IFF(store_sales.f_ss_item_sk IS NOT NULL, TRUE, FALSE)
      COMMENT = 'Boolean indicating whether valid store sales item was returned'
  )
  DIMENSIONS (
    store.s_store_sk AS store.s_store_sk
      COMMENT = 'Store SKU (Stock Keeping Unit)',
    store.s_city AS store.s_city
      COMMENT = 'City where the store is located',
    date_dim.d_year AS date_dim.d_year
      COMMENT = 'Year of Date',
    date_dim.d_date AS date_dim.d_date
      COMMENT = 'Date of the day',
    customer.c_first_name AS customer.c_first_name
      COMMENT = 'First name of the customer',
    customer.c_last_name AS customer.c_last_name
      COMMENT = 'Last name of the customer',
    current_customer_demographics.cd_dep_count AS current_customer_demographics.cd_dep_count
      COMMENT = 'Current number of dependents for the customer',
    customer_demographics.cd_dep_count AS customer_demographics.cd_dep_count
      COMMENT = 'Number of dependents for the customer at the time of sale',
    store.s_store_name AS store.s_store_name
      COMMENT = 'the names of stores, likely a list of store names in a retail or commercial setting',
    store_sales.ss_sale_year AS date_dim.d_year
      COMMENT = 'Year of store sale',
    store.s_manager AS store.s_manager
      COMMENT = 'Store manager',
    store.s_floor_space AS store.s_floor_space
      COMMENT = 'Total floor space in square feet',
    store.s_store_id AS store.s_store_id
      COMMENT = 'Unique identifier for each store',
    item.i_brand AS item.i_brand
      COMMENT = 'Brands of export items',
    item.i_product_name AS item.i_product_name
      COMMENT = 'Product names',
    item.i_manufact AS item.i_manufact
      COMMENT = 'Manufacturing items, including antibarable, n stbarpri, and barationese',
    customer_address.ca_state AS ca_state
      COMMENT = 'State where the customer address is located',
    item.i_item_id AS item.i_item_id
      COMMENT = 'Unique item identifiers',
    item.i_item_sk AS i_item_sk
      COMMENT = 'Item identifier SKU (Stock Keeping Unit)',
    customer.c_state AS customer_address.ca_state
      COMMENT = 'Customer state abbreviation',
    hd.hd_vehicle_count AS hd.hd_vehicle_count
      COMMENT = 'Number of vehicles owned by the household',
    customer.c_customer_id AS customer.c_customer_id
      COMMENT = 'Customer identifier',
    income_band.ib_income_band_sk AS income_band.ib_income_band_sk
      COMMENT = 'Income Band Identifier',
    customer_demographics.gender AS customer_demographics.cd_gender
      COMMENT = 'Gender of the customer at the time of sale',
    current_customer_demographics.gender AS current_customer_demographics.cd_gender
      COMMENT = 'Gender of the customer',
    store_sales.ss_net_profit_tier AS f_net_profit_tier
      COMMENT = 'Tier labels for net profit from store sales',
    store_sales.ss_customer_sk AS store_sales.ss_customer_sk
      COMMENT = 'Customer ID',
    store_sales.ss_store_sk AS store_sales.ss_store_sk
      COMMENT = 'Store''s SKU (Stock Keeping Unit) where sales happened',
    income_band.ib_lower_bound AS income_band.ib_lower_bound
      COMMENT = 'Lower bound of income bands',
    income_band.ib_upper_bound AS income_band.ib_upper_bound
      COMMENT = 'Upper bound of income bands',
    hd.hd_buy_potential AS hd.hd_buy_potential
      COMMENT = 'Household buying potential',
    customer_address.ca_city AS ca_city
      COMMENT = 'City where the customer address is located',
    customer.c_city AS customer_address.ca_city
      COMMENT = 'City where the customer is located',
    item.i_item_size AS i_size
      COMMENT = 'Item size',
    store_sales.ss_item_id AS item.i_item_sk
      COMMENT = 'Identifier of item that was sold through store',
    store_sales.ss_product_name AS item.i_product_name
      COMMENT = 'Product name of item that was sold through store',
    store_sales.ss_item_size AS item.i_item_size
      COMMENT = 'Size of item that was sold through store',
    web_sales.ws_item_id AS item.i_item_sk
      COMMENT = 'Identifier of item that was sold through web',
    web_sales.ws_product_name AS item.i_product_name
      COMMENT = 'Product name of item that was sold through web',
    web_sales.ws_item_size AS item.i_item_size
      COMMENT = 'Size of item that was sold through web',
    catalog_sales.cs_item_id AS item.i_item_sk
      COMMENT = 'Identifier of item that was sold through catalog',
    catalog_sales.cs_product_name AS item.i_product_name
      COMMENT = 'Product name of item that was sold through catalog',
    catalog_sales.cs_item_size AS item.i_item_size
      COMMENT = 'Size of item that was sold through catalog',
    customer.c_customer_sk AS c_customer_sk
      COMMENT = 'Customer unique identifier',
    web_site.web_site_sk AS web_site.web_site_sk
      COMMENT = 'Unique identifier for each web site',
    web_site.web_name AS web_site.web_name
      COMMENT = 'Web site name',
    item.i_brand_id AS i_brand_id
      COMMENT = 'Brand ID for items',
    item.i_category AS item.i_category
      COMMENT = 'Product categories',
    item.i_color AS i_color
      COMMENT = 'Color options',
    store.s_hours AS s_hours
      COMMENT = 'Store hours',
    store.s_state AS s_state
      COMMENT = 'Store state',
    customer_address.ca_zip AS ca_zip
      COMMENT = 'Customer zip code',
    customer.ca_zip AS customer_address.ca_zip
      COMMENT = 'Customer zip code',
    customer.ca_state AS customer_address.ca_state
      COMMENT = 'State where the customer address is located',
    ship_mode.sm_type AS sm_type
      COMMENT = 'Shipping mode type',
    ship_mode.sm_carrier AS sm_carrier
      COMMENT = 'Shipping mode carrier',
    warehouse.w_warehouse_name AS w_warehouse_name
      COMMENT = 'Warehouse name',
    warehouse.w_city AS w_city
      COMMENT = 'Warehouse city',
    warehouse.w_warehouse_sq_ft AS w_warehouse_sq_ft
      COMMENT = 'Warehouse square footage',
    item.i_current_price AS i_current_price
      COMMENT = 'Current price of the item',
    store.s_number_employees AS s_number_employees
      COMMENT = 'Number of employees in the store',
    customer.c_birth_country AS c_birth_country
      COMMENT = 'Country where the customer was born',
    catalog_sales.cs_ship_mode_sk AS catalog_sales.cs_ship_mode_sk
      COMMENT = 'Unique Identifier for Shipping mode  for catalog sales',
    web_sales.ws_ship_mode_sk AS web_sales.ws_ship_mode_sk
      COMMENT = 'Unique Identifier for Shipping mode for web sales',
    hd.hd_income_band_sk AS hd.hd_income_band_sk
      COMMENT = 'Unique Identifier for Household income band ',
    catalog_sales.cs_item_sk AS catalog_sales.cs_item_sk
      COMMENT = 'Unique Identifier for catalog sales item',
    store_sales.ss_item_sk AS store_sales.ss_item_sk
      COMMENT = 'Unique Identifier for store sales item',
    web_sales.ws_item_sk AS web_sales.ws_item_sk
      COMMENT = 'Unique Identifier for web sales item'
  )
  METRICS (
    customer.customer_count AS COUNT(DISTINCT c_customer_sk)
      COMMENT = 'Count of distinct customer identifiers',
    item.product_count AS (COUNT(DISTINCT i_item_sk))
      COMMENT = 'Count of distinct products',
    store_returns.ss_store_returns AS COUNT_IF(f_ss_has_sales)
      COMMENT = 'Count of records that have a valid store sales item returned',
    web_sales.total_sales AS SUM(CAST(ws_ext_sales_price * ws_quantity AS DECIMAL(38, 2)))
      COMMENT = 'Sum of the revenue (sales price multiplied by quantity) from web sales',
    store_sales.start_date AS MIN(date_dim.d_date)
      COMMENT = 'Min date (start date) of the store sales',
    store_sales.end_date AS MAX(date_dim.d_date)
      COMMENT = 'Max date (end date) of the store sales',
    web_sales.w_net_profit AS SUM(ws_net_profit)
      COMMENT = 'Sum of net profit through web sales',
    catalog_sales.c_net_profit AS SUM(cs_net_profit)
      COMMENT = 'Sum of net profit through catalog sales',
    store_sales.s_net_profit AS SUM(ss_net_profit)
      COMMENT = 'Sum of net profit through store sales',
    catalog_sales.total_sales AS SUM(CAST(cs_sales_price * cs_quantity AS DECIMAL(38, 2)))
      COMMENT = 'Sum of revenue (sales price multiplied by quantity) from catalog sales',
    store_sales.ss_customer_count AS COUNT(ss_customer_sk)
      COMMENT = 'Count of customers who purchased through store sales',
    store_sales.ss_average_sale_quantity AS CASE
      WHEN COUNT(ss_quantity) = 0 THEN NULL
      ELSE CAST((SUM(ss_quantity) / COUNT(ss_quantity)) AS DOUBLE)
    END
      COMMENT = 'Average store sale quantity calculated as sum of sold quantity divided by number of rows',
    store_sales.total_sales AS SUM(ss_sales_price * ss_quantity)
      COMMENT = 'Sum of the revenue (sales price multiplied by quantity) from store sales',
    web_sales.total_quantity_sold AS COALESCE(SUM(ws_quantity), 0)
      COMMENT = 'Sum of number of items sold through web sales',
    web_sales.total_shipping_cost AS SUM(ws_ext_ship_cost)
      COMMENT = 'Sum of the shipping cost',
    store_sales.ss_average_store_net_profit AS CASE
      WHEN (SUM(ss_quantity) = 0) THEN NULL
      ELSE CAST(CAST(SUM(ss_net_profit) AS DECIMAL(17, 2)) / SUM(ss_quantity) AS DECIMAL(37, 22))
    END
      COMMENT = 'Average profit sold through store',
    inventory.total_inventory_on_hand AS SUM(inv_quantity_on_hand)
      COMMENT = 'Total inventory on hand for a given item',
    store_sales.total_quantity_sold AS COALESCE(SUM(ss_quantity), 0)
      COMMENT = 'Total quantity sold for a given item in a store',
    store_returns.total_quantity_returned AS COALESCE(SUM(sr_return_quantity), 0)
      COMMENT = 'Total quantity returned for a given item in a store',
    catalog_sales.start_date AS MIN(date_dim.d_date)
      COMMENT = 'Min date for catalog sales',
    catalog_sales.end_date AS MAX(date_dim.d_date)
      COMMENT = 'Max date for catalog sales',
    catalog_sales.unique_catalog_customers AS COUNT(DISTINCT cs_bill_customer_sk)
      COMMENT = 'Unique customers who made a purchase through catalog sales',
    catalog_sales.total_quantity_sold AS COALESCE(SUM(cs_quantity), 0)
      COMMENT = 'Sum of number of items sold through catalog sales'
  );
```

After running the above SQL, you should see the following output confirming the semantic view was created successfully:

```
+----------------------------------------------------+
|                       status                       |
+----------------------------------------------------+
| Semantic view TPCDS_NLQ_VIEW successfully created. |
+----------------------------------------------------+
```

<!-- ------------------------ -->
## Traditional vs Semantic SQL

Now that we've created our semantic view, let's compare how traditional SQL and semantic SQL handle queries of varying complexity.

We'll use the TPC-DS benchmark to demonstrate queries ranging from simple filters to complex multi-table aggregations. Each example will show:
1. **Traditional SQL**: The standard approach with explicit `JOIN`s and aggregations
2. **Semantic SQL**: The simplified approach using our semantic view

<!-- ------------------------ -->
## Simple Questions

These queries demonstrate simple filtering and selection operations on single tables or simple joins. They represent straightforward business questions that can be answered with basic SQL operations like `WHERE` clauses and simple aggregations.

### What are all of the unique store numbers in Tennessee?

**Traditional SQL:** Queries the store table directly with a `WHERE` filter on state.

```sql
SELECT
    DISTINCT s_store_sk
FROM
    snowflake_sample_data.tpcds_sf10tcl.store
WHERE
    s_state = 'TN'
    AND s_store_sk IS NOT NULL
ORDER BY s_store_sk;
```

**Semantic SQL:** Uses `DIMENSIONS` to select the store identifier directly. No need to specify the full table path, the semantic view knows where `s_store_sk` lives.

```sql
SELECT * FROM SEMANTIC_VIEW (
    tpcds_nlq_view
    DIMENSIONS store.s_store_sk
    WHERE s_state='TN'
)
ORDER BY s_store_sk;
```

**Expected Output:** Returns unique store IDs for Tennessee stores, ordered by store number.

```
+------------+
| S_STORE_SK |
+------------+
|          1 |
|         22 |
|         52 |
|         76 |
|         96 |
|        102 |
|        112 |
|        140 |
|        ... |
+------------+
```

### What are the first and last names of all customers that have more than 5 dependents?

**Traditional SQL:** Uses `JOIN` on customer and customer_demographics tables with a `WHERE` filter on dependent count.

```sql
SELECT
    customer.c_first_name,
    customer.c_last_name
FROM
    snowflake_sample_data.tpcds_sf10tcl.customer
JOIN
    snowflake_sample_data.tpcds_sf10tcl.customer_demographics AS current_customer_demographics
    ON customer.c_current_cdemo_sk = current_customer_demographics.cd_demo_sk
WHERE
    current_customer_demographics.cd_dep_count > 5
ORDER BY
    c_first_name ASC, c_last_name ASC
LIMIT 100;
```

**Semantic SQL:** Uses `FACTS` to retrieve customer attributes. The semantic view handles the `JOIN` between `customer` and `customer_demographics` automatically, so no explicit `JOIN` is needed.

```sql
SELECT * FROM SEMANTIC_VIEW (
    tpcds_nlq_view
    FACTS customer.c_first_name first_name, customer.c_last_name last_name
    WHERE current_customer_demographics.cd_dep_count > 5
)
ORDER BY first_name ASC, last_name ASC
LIMIT 100;
```

**Expected Output:** Returns customer names sorted alphabetically, filtered to those with more than 5 dependents.

```
+------------+------------+
| FIRST_NAME | LAST_NAME  |
+------------+------------+
| Aaron      | Aaron      |
| Aaron      | Aaron      |
| Aaron      | Abbott     |
| Aaron      | Abbott     |
| Aaron      | Abbott     |
| Aaron      | Abbott     |
| Aaron      | Abbott     |
| Aaron      | Abel       |
| Aaron      | Abel       |
| Aaron      | Abel       |
| ...        | ...        |
+------------+------------+
```

### What is the name, manager and floor space of each store in the city of Midway?

**Traditional SQL:** Uses `SELECT` on multiple columns from the store table with a `WHERE` city filter.

```sql
SELECT
    s_store_name,
    s_manager,
    s_floor_space
FROM
    snowflake_sample_data.tpcds_sf10tcl.store
WHERE
    s_city = 'Midway'
ORDER BY s_store_name;
```

**Semantic SQL:** Uses `FACTS` to select multiple store attributes in one call. Clean, readable syntax without needing to reference the full table path.

```sql
SELECT * FROM SEMANTIC_VIEW (
    tpcds_nlq_view
    FACTS s_store_name, s_manager, s_floor_space
    WHERE s_city = 'Midway'
)
ORDER BY s_store_name;
```

**Expected Output:** Returns store details for all stores located in Midway, sorted by store name.

```
+--------------+-------------------+--------------+
| S_STORE_NAME | S_MANAGER         | S_FLOOR_SPACE|
+--------------+-------------------+--------------+
| ation        | Harry Harkins     |      6849804 |
| bar          | Christopher Garris|      7610137 |
| eing         | Stephen Garcia    |      6101180 |
| eing         | Brian Strickland  |      6396268 |
| eing         | Robert Tyson      |      5903931 |
| ese          | Dean Patel        |      9875948 |
| ought        | Robert Yost       |      5945154 |
+--------------+-------------------+--------------+
```

<!-- ------------------------ -->
## Simple Questions with Aggregations

These queries introduce aggregations, grouping, and metrics while maintaining relatively simple table relationships. The semantic view's pre-defined metrics significantly reduce query complexity.

### What is the total count of customers for each customer home state?

**Traditional SQL:** Uses `JOIN` on customer and address tables, then `GROUP BY` state with `COUNT(DISTINCT ...)`.

```sql
SELECT
    ca_state,
    COUNT(DISTINCT c_customer_sk) AS customer_count
FROM
    snowflake_sample_data.tpcds_sf10tcl.customer
JOIN
    snowflake_sample_data.tpcds_sf10tcl.customer_address
    ON customer.c_current_addr_sk = customer_address.ca_address_sk
GROUP BY
    ca_state
ORDER BY
    customer_count DESC, ca_state
LIMIT 100;
```

**Semantic SQL:** Uses `DIMENSIONS` for grouping and `METRICS` for the pre-defined `customer_count` aggregation. The `JOIN` between `customer` and `customer_address` is handled automatically by the semantic view's relationships.

```sql
SELECT * FROM SEMANTIC_VIEW (
    tpcds_nlq_view
    DIMENSIONS customer_address.ca_state AS ca_state
    METRICS customer.customer_count
)
ORDER BY customer_count DESC
LIMIT 100;
```

**Expected Output:** Returns customer counts by state, with Texas (TX) having the most customers at over 5 million.

```
+----------+----------------+
| CA_STATE | CUSTOMER_COUNT |
+----------+----------------+
| TX       |        5154196 |
| GA       |        3225083 |
| VA       |        2735265 |
| KY       |        2431364 |
| MO       |        2213416 |
| KS       |        2131894 |
| IL       |        2048115 |
| NC       |        2034567 |
| ...      |            ... |
+----------+----------------+
```

### What was the overall web sales for the year 2002?

**Traditional SQL:** Uses `JOIN` on web_sales with date_dim and calculates total revenue using `SUM()` with `CAST()`.

```sql
SELECT
    SUM(CAST(ws_ext_sales_price * ws_quantity AS DECIMAL(38, 2))) AS total_sales
FROM
    snowflake_sample_data.tpcds_sf10tcl.web_sales
JOIN
    snowflake_sample_data.tpcds_sf10tcl.date_dim
    ON web_sales.ws_sold_date_sk = date_dim.d_date_sk
WHERE
    date_dim.d_year = 2002;
```

**Semantic SQL:** Uses `METRICS` to call the pre-defined `total_sales` calculation. No need to write the complex `SUM(CAST(...))` formula since it's already defined in the semantic view. The `JOIN` to `date_dim` is automatic.

```sql
SELECT * FROM SEMANTIC_VIEW (
    tpcds_nlq_view
    METRICS web_sales.total_sales
    WHERE date_dim.d_year = 2002
)
LIMIT 100;
```

**Expected Output:** Returns total web sales for 2002: approximately $2.46 quadrillion (TPC-DS scale factor).

```
+----------------------+
|     TOTAL_SALES      |
+----------------------+
| 2458971149461555.79  |
+----------------------+
```

### What is the count of products in each product category?

**Traditional SQL:** Uses `GROUP BY` category and `COUNT(DISTINCT ...)` to count products per category.

```sql
SELECT
    i_category AS product_category,
    COUNT(DISTINCT i_item_sk) AS product_count
FROM
    snowflake_sample_data.tpcds_sf10tcl.item
WHERE
    i_category IS NOT NULL
    AND i_item_sk IS NOT NULL
GROUP BY
    i_category
ORDER BY
    i_category
LIMIT 5000;
```

**Semantic SQL:** Combines `DIMENSIONS` for grouping by category and `METRICS` for the pre-defined `product_count`. The aggregation logic (`COUNT(DISTINCT i_item_sk)`) is encapsulated in the metric definition.

```sql
SELECT * FROM semantic_view(tpcds_nlq_view
    DIMENSIONS item.i_category
    METRICS item.product_count
)
ORDER BY i_category
limit 100;
```

**Expected Output:** Returns all 10 product categories with approximately 40,000 products each.

```
+------------------+---------------+
| PRODUCT_CATEGORY | PRODUCT_COUNT |
+------------------+---------------+
| Books            |         39643 |
| Children         |         40406 |
| Electronics      |         40172 |
| Home             |         40124 |
| Jewelry          |         40114 |
| Men              |         39892 |
| Music            |         40342 |
| Shoes            |         40158 |
| Sports           |         40315 |
| Women            |         39871 |
+------------------+---------------+
```

<!-- ------------------------ -->
## Advanced Questions

These queries involve simple filters but require joining multiple tables across complex relationships. The semantic view dramatically simplifies these queries by hiding the complex join logic.

### What is the customer id and vehicle count for every customer in income band 9?

**Traditional SQL:** Uses multiple `JOIN` clauses across customer, household_demographics, and income_band tables with a `WHERE` filter on income band.

```sql
SELECT DISTINCT
    customer.c_customer_id,
    hd.hd_vehicle_count
FROM
    snowflake_sample_data.tpcds_sf10tcl.customer
JOIN
    snowflake_sample_data.tpcds_sf10tcl.household_demographics hd
    ON customer.c_current_hdemo_sk = hd.hd_demo_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.income_band
    ON hd.hd_income_band_sk = income_band.ib_income_band_sk
WHERE
    income_band.ib_income_band_sk = 9
    AND customer.c_customer_id IS NOT NULL
ORDER BY
    customer.c_customer_id
LIMIT 100;
```

**Semantic SQL:** Uses `FACTS` to access attributes across 3 related tables (`customer`, `household_demographics`, `income_band`). The semantic view's pre-defined relationships handle all the `JOIN`s automatically. What was 3 `JOIN`s becomes a single semantic query.

```sql
SELECT DISTINCT c_customer_id, hd_vehicle_count FROM (
    SELECT * FROM SEMANTIC_VIEW (
        tpcds_nlq_view
        FACTS customer.c_customer_id, hd.hd_vehicle_count
        WHERE ib_income_band_sk = 9 AND c_customer_id IS NOT NULL
    )
)
ORDER BY c_customer_id
LIMIT 5000;
```

**Expected Output:** Returns customer IDs and their vehicle counts for income band 9, with vehicle counts ranging from 0-4.

```
+------------------+------------------+
| C_CUSTOMER_ID    | HD_VEHICLE_COUNT |
+------------------+------------------+
| AAAAAAAAAAAALAA  |                2 |
| AAAAAAAAAAAAMAA  |                0 |
| AAAAAAAAAAAPCA   |                3 |
| AAAAAAAAAABCBA   |                4 |
| AAAAAAAAAABDBA   |                4 |
| AAAAAAAAABJDA    |                2 |
| AAAAAAAAAACJDA   |                3 |
| AAAAAAAAAACKAA   |                4 |
| AAAAAAAAAACKBA   |                0 |
| AAAAAAAAAACMDA   |                1 |
| ...              |              ... |
+------------------+------------------+
```

### What is the net profit tier for each store name and gender in the 2002 sales year?

**Traditional SQL:** Uses 4 `JOIN` clauses and a complex `CASE` statement to categorize profit into tiers.

```sql
SELECT DISTINCT
    store.s_store_name,
    customer_demographics.cd_gender,
    CASE
        WHEN store_sales.ss_net_profit > 25000 THEN 'More than 25000'
        WHEN store_sales.ss_net_profit BETWEEN 3000 AND 25000 THEN '3000-25000'
        WHEN store_sales.ss_net_profit BETWEEN 2000 AND 3000 THEN '2000-3000'
        WHEN store_sales.ss_net_profit BETWEEN 300 AND 2000 THEN '300-2000'
        WHEN store_sales.ss_net_profit BETWEEN 250 AND 300 THEN '250-300'
        WHEN store_sales.ss_net_profit BETWEEN 200 AND 250 THEN '200-250'
        WHEN store_sales.ss_net_profit BETWEEN 150 AND 200 THEN '150-200'
        WHEN store_sales.ss_net_profit BETWEEN 100 AND 150 THEN '100-150'
        WHEN store_sales.ss_net_profit BETWEEN 50 AND 100 THEN ' 50-100'
        WHEN store_sales.ss_net_profit BETWEEN 0 AND 50 THEN '  0- 50'
        ELSE ' 50 or Less'
    END AS net_profit_tier
FROM
    snowflake_sample_data.tpcds_sf10tcl.store_sales
JOIN
    snowflake_sample_data.tpcds_sf10tcl.store
    ON store_sales.ss_store_sk = store.s_store_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.customer_demographics
    ON store_sales.ss_cdemo_sk = customer_demographics.cd_demo_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.date_dim
    ON store_sales.ss_sold_date_sk = date_dim.d_date_sk
WHERE
    date_dim.d_year = 2002
ORDER BY
    s_store_name, cd_gender, net_profit_tier
LIMIT 100;
```

**Semantic SQL:** Uses `FACTS` with the pre-defined `f_net_profit_tier` calculation. The complex `CASE` statement is encapsulated in the semantic view, so there's no need to rewrite the tiering logic. `JOIN`s across 4 tables are automatic.

```sql
SELECT DISTINCT s_store_name, gender, f_net_profit_tier FROM (
    SELECT * FROM SEMANTIC_VIEW (
        tpcds_nlq_view
        FACTS store_sales.f_net_profit_tier, 
              store.s_store_name, 
              customer_demographics.gender,
              date_dim.d_year
    )
)
WHERE d_year = 2002
      AND NOT gender IS NULL
ORDER BY s_store_name, gender, f_net_profit_tier
LIMIT 100;
```

**Expected Output:** Returns distinct store/gender/tier combinations, showing profit tiers from "$0-50" up to "$3000-25000".

```
+--------------+-----------+-----------------+
| S_STORE_NAME | CD_GENDER | NET_PROFIT_TIER |
+--------------+-----------+-----------------+
| able         | F         | 0- 50           |
| able         | F         | 50 or Less      |
| able         | F         | 50-100          |
| able         | F         | 100-150         |
| able         | F         | 150-200         |
| able         | F         | 200-250         |
| able         | F         | 2000-3000       |
| able         | F         | 250-300         |
| able         | F         | 300-2000        |
| able         | F         | 3000-25000      |
| ...          | ...       | ...             |
+--------------+-----------+-----------------+
```

### What was the first name and gender of each customer that shopped in the store named 'ese' in 2001?

**Traditional SQL:** Uses 5 `JOIN` clauses to link store_sales to customer details with `WHERE` filters on store name and year.

```sql
SELECT DISTINCT
    customer.c_first_name,
    customer_demographics.cd_gender
FROM
    snowflake_sample_data.tpcds_sf10tcl.store_sales
JOIN
    snowflake_sample_data.tpcds_sf10tcl.customer
    ON store_sales.ss_customer_sk = customer.c_customer_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.customer_demographics
    ON store_sales.ss_cdemo_sk = customer_demographics.cd_demo_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.store
    ON store_sales.ss_store_sk = store.s_store_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.date_dim
    ON store_sales.ss_sold_date_sk = date_dim.d_date_sk
WHERE
    store.s_store_name = 'ese'
    AND date_dim.d_year = 2001
ORDER BY
    c_first_name, cd_gender
LIMIT 5000;
```

**Semantic SQL:** Uses `FACTS` to access attributes from 5 related tables (`store_sales`, `customer`, `customer_demographics`, `store`, `date_dim`). The semantic view handles all `JOIN`s through pre-defined relationships. What was 4 explicit `JOIN`s becomes implicit.

```sql
SELECT DISTINCT c_first_name, gender FROM (
    SELECT * FROM SEMANTIC_VIEW (
        tpcds_nlq_view
        FACTS store_sales.ss_customer_sk,
              customer.c_first_name,
              customer_demographics.gender,
              date_dim.d_year,
              store.s_store_name
    )
)
WHERE s_store_name = 'ese'
    AND d_year = 2001
    AND NOT gender IS NULL
ORDER BY c_first_name, gender
LIMIT 5000;
```

**Expected Output:** Returns unique first name and gender combinations for customers who shopped at store 'ese' in 2001.

```
+--------------+-----------+
| C_FIRST_NAME | CD_GENDER |
+--------------+-----------+
| Aaron        | F         |
| Aaron        | M         |
| Abbey        | F         |
| Abbey        | M         |
| Abbie        | F         |
| Abbie        | M         |
| Abby         | F         |
| Abby         | M         |
| Abdul        | F         |
| Abdul        | M         |
| ...          | ...       |
+--------------+-----------+
```

<!-- ------------------------ -->
## Advanced Questions with Aggregations

These queries represent the most challenging scenarios, combining complex aggregations with intricate multi-table joins. The semantic view provides the greatest value here by abstracting both the complex relationships and pre-computing metrics.

### For each store state in the year 2002, what was the count of store customers and the average sales quantity?

**Traditional SQL:** Uses `JOIN` on store_sales with store and date_dim, then `GROUP BY` with `COUNT()` and `CASE` for null-safe average calculation.

```sql
SELECT
    store.s_state,
    COUNT(store_sales.ss_customer_sk) AS store_customer_count,
    CASE 
        WHEN COUNT(store_sales.ss_quantity) = 0 THEN NULL 
        ELSE CAST((SUM(store_sales.ss_quantity) / COUNT(store_sales.ss_quantity)) AS DOUBLE) 
    END AS average_store_sales_quantity
FROM
    snowflake_sample_data.tpcds_sf10tcl.store_sales
JOIN
    snowflake_sample_data.tpcds_sf10tcl.store
    ON store_sales.ss_store_sk = store.s_store_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.date_dim
    ON store_sales.ss_sold_date_sk = date_dim.d_date_sk
WHERE
    date_dim.d_year = 2002
    AND store.s_state IS NOT NULL
GROUP BY
    store.s_state
ORDER BY
    store.s_state
LIMIT 5000;
```

**Semantic SQL:** Uses `DIMENSIONS` for grouping and multiple `METRICS` (`ss_customer_count`, `ss_average_sale_quantity`). The complex `CASE` statement for average calculation and all `JOIN`s are encapsulated in the semantic view.

```sql
SELECT * FROM SEMANTIC_VIEW (
    tpcds_nlq_view
    DIMENSIONS store.s_state
    METRICS
        store_sales.ss_customer_count,
        store_sales.ss_average_sale_quantity
    WHERE date_dim.d_year = 2002
) AS R(store_state, store_customer_count, average_store_sales_quantity)
WHERE store_state IS NOT NULL
ORDER BY store_state
LIMIT 5000;
```

**Expected Output:** Returns metrics per state for 2002. Georgia (GA) leads with over 500 million customers, average quantity ~50 units.

```
+---------+----------------------+------------------------------+
| S_STATE | STORE_CUSTOMER_COUNT | AVERAGE_STORE_SALES_QUANTITY |
+---------+----------------------+------------------------------+
| AL      |            148448445 |                    50.508838 |
| CA      |            176854713 |                    50.503677 |
| CO      |             63727493 |                     50.49999 |
| FL      |             49548871 |                     50.51083 |
| GA      |            502313211 |                    50.504699 |
| IA      |             99133835 |                    50.491451 |
| IL      |             77971044 |                     50.50326 |
| IN      |            198222807 |                    50.500988 |
| KS      |            155749285 |                    50.494168 |
| KY      |            141595491 |                    50.503138 |
| ...     |                  ... |                          ... |
+---------+----------------------+------------------------------+
```

### What were the store sales in 2002 for each store manager in the state of Tennessee?

**Traditional SQL:** Uses `JOIN` on store_sales with store and date_dim, `GROUP BY` manager with `SUM()` and `WHERE` filters on state/year.

```sql
SELECT
    store.s_manager,
    SUM(store_sales.ss_sales_price * store_sales.ss_quantity) AS total_sales
FROM
    snowflake_sample_data.tpcds_sf10tcl.store_sales
JOIN
    snowflake_sample_data.tpcds_sf10tcl.store
    ON store_sales.ss_store_sk = store.s_store_sk
JOIN
    snowflake_sample_data.tpcds_sf10tcl.date_dim
    ON store_sales.ss_sold_date_sk = date_dim.d_date_sk
WHERE
    store.s_state = 'TN'
    AND date_dim.d_year = 2002
    AND store.s_manager IS NOT NULL
GROUP BY
    store.s_manager
ORDER BY
    total_sales DESC NULLS LAST
LIMIT 5000;
```

**Semantic SQL:** Combines `DIMENSIONS` for grouping by manager and `METRICS` for the pre-defined `total_sales` calculation. The `SUM` formula and all table `JOIN`s are handled by the semantic view.

```sql
SELECT s_manager, total_sales FROM (
    SELECT * FROM SEMANTIC_VIEW (
        tpcds_nlq_view
        DIMENSIONS store.s_manager
        METRICS store_sales.total_sales
        WHERE store.s_state = 'TN' AND d_year = 2002 
              AND store.s_manager IS NOT NULL
    )
)
ORDER BY total_sales DESC NULLS LAST
LIMIT 5000;
```

**Expected Output:** Returns sales per TN manager in 2002. Top performer Robert Young at ~$13.5 billion, all managers close in performance.

```
+------------------+----------------+
| S_MANAGER        | TOTAL_SALES    |
+------------------+----------------+
| Robert Young     | 13540376902.13 |
| Donald Dodson    | 13531825145.25 |
| Jesus Dickinson  | 13520973098.82 |
| Russell Pedigo   | 13506626925.90 |
| Norman Gould     | 13503720972.50 |
| Jesse Nielson    | 13493375137.32 |
| Armando Vasquez  | 13489216257.07 |
| John Fogle       | 13482056094.88 |
| Daniel Slaton    | 13479913604.98 |
| Frederick Bunn   | 13479143024.52 |
| ...              |            ... |
+------------------+----------------+
```

### What were the web sales by site in New Jersey?

**Question:** For each website, what is the quantity sold and total shipping cost for customers with a shipping address in the state of New Jersey?

**Traditional SQL:** Uses `JOIN` on web_sales with web_site and customer_address, `GROUP BY` site with `SUM()` for NJ shipments.

```sql
SELECT
  ws.ws_web_site_sk AS "web_site_sk",
  web.web_name AS "web_name",
  SUM(ws.ws_quantity) AS "total_quantity_sold",
  SUM(ws.ws_ext_ship_cost) AS "total_shipping_cost"
FROM
  snowflake_sample_data.tpcds_sf10tcl.web_sales AS ws
  JOIN snowflake_sample_data.tpcds_sf10tcl.web_site AS web ON ws.ws_web_site_sk = web.web_site_sk
  JOIN snowflake_sample_data.tpcds_sf10tcl.customer_address AS ca ON ws.ws_ship_addr_sk = ca.ca_address_sk
WHERE
  ca.ca_state='NJ'
  AND web.web_name IS NOT NULL
  AND ws.ws_quantity IS NOT NULL
  AND ws.ws_ext_ship_cost IS NOT NULL
GROUP BY
  ws.ws_web_site_sk,
  web.web_name
ORDER BY
  ws.ws_web_site_sk;
```

**Semantic SQL:** Uses `DIMENSIONS` for grouping by website and `METRICS` for pre-defined `total_quantity_sold` and `total_shipping_cost`. The `JOIN`s between `web_sales`, `web_site`, and `customer_address` are handled automatically.

```sql
SELECT * FROM SEMANTIC_VIEW(
    tpcds_nlq_view
    DIMENSIONS web_site.web_site_sk, web_site.web_name
    METRICS web_sales.total_quantity_sold, web_sales.total_shipping_cost
    WHERE customer_address.ca_state='NJ'
)
WHERE web_name IS NOT NULL
    AND total_quantity_sold IS NOT NULL
    AND total_shipping_cost IS NOT NULL
ORDER BY web_site_sk;
```

**Expected Output:** Returns web sales metrics for NJ shipments. Site_0 (ID 1) leads with ~61M items sold and ~$1.5B in shipping.

```
+-------------+----------+---------------------+---------------------+
| WEB_SITE_SK | WEB_NAME | TOTAL_QUANTITY_SOLD | TOTAL_SHIPPING_COST |
+-------------+----------+---------------------+---------------------+
|           1 | site_0   |            61028703 |       1542231372.61 |
|           2 | site_0   |            36583068 |        924147129.20 |
|           3 | site_0   |            24539919 |        618876530.14 |
|           4 | site_0   |            24398128 |        614892075.27 |
|           5 | site_0   |            24353870 |        614586576.94 |
|           6 | site_0   |            12364943 |        312510257.79 |
|           7 | site_1   |            61102675 |       1538701306.86 |
|           8 | site_1   |            36505051 |        923039800.32 |
|           9 | site_1   |            24509946 |        619652299.83 |
|          10 | site_1   |            24399101 |        616355076.94 |
|         ... | ...      |                 ... |                 ... |
+-------------+----------+---------------------+---------------------+
```

<!-- ------------------------ -->
## Lessons Learned

Throughout this tutorial, we discovered key patterns for simplifying queries with Semantic Views:

| Semantic Parameter | What It Does | When to Use |
|--------------------|--------------|-------------|
| `DIMENSIONS` | Selects categorical attributes for grouping | When you need to `GROUP BY` or select descriptive data |
| `METRICS` | Calls pre-defined aggregations (`SUM`, `COUNT`, `AVG`) | When you need calculated measures without writing formulas |
| `FACTS` | Retrieves row-level computed values | When you need detailed or derived data from the semantic model |
| `WHERE` | Filters data using any attribute | Same as traditional SQL `WHERE` clause |

### Complexity Comparison: Key Findings

We explored queries across four complexity levels:

| Complexity Level | Traditional SQL | Semantic SQL | Improvement |
|------------------|----------------|--------------|-------------|
| **Simple Questions** | 8-13 lines | 6-7 lines | Modest: simpler syntax |
| **Simple Questions with Aggregations** | 9-13 lines | 6-7 lines | Moderate: metrics eliminate formulas |
| **Advanced Questions** | 17-23 lines | 9-15 lines | Significant: auto `JOIN`s |
| **Advanced Questions with Aggregations** | 19-32 lines | 10-13 lines | **Dramatic: biggest ROI** |

**Bottom Line:** Semantic Views provide the greatest value for advanced questions with aggregations. These are exactly the queries that cause the most pain in traditional SQL development.

### Key Takeaways

1. **`JOIN`s become automatic.** Define relationships once in the semantic view, and Snowflake handles the joins. What was 4-5 explicit `JOIN`s becomes implicit.

2. **Metrics are reusable.** Complex calculations (like `SUM(price * quantity)` or `CASE` statements) are defined once and called by name. No copy-pasting formulas.

3. **Business-friendly naming.** Use semantic aliases that make sense to analysts (e.g., `total_sales` instead of `SUM(ss_sales_price * ss_quantity)`).

4. **Query complexity scales.** Simple queries stay simple, but complex multi-table aggregations see the biggest improvement (from 20+ lines to 5-10 lines).

5. **Same results, less code.** Semantic SQL produces identical results to traditional SQL with significantly less code to write and maintain.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built a comprehensive Semantic View over the TPC-DS dataset and learned how to transform complex SQL queries into simple, business-friendly Semantic SQL. You've seen how Semantic Views can dramatically reduce query complexity while maintaining full analytical power.

Happy querying!

### What You Learned
- How to create Semantic Views with tables, relationships, dimensions, facts, and metrics
- The difference between Traditional SQL and Semantic SQL approaches
- How Semantic Views abstract complex join logic and pre-define reusable metrics
- Query patterns across different complexity levels

### Related Resources

Documentation:
- [Semantic Views Overview](https://docs.snowflake.com/en/user-guide/views-semantic/overview) - Comprehensive overview of semantic views in Snowflake
- [CREATE SEMANTIC VIEW Reference](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view) - SQL command reference for creating semantic views
- [Querying Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/querying) - How to query semantic views using SEMANTIC_VIEW construct
- [Best practices for semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-dev) - Best practices for working with semantic models
- [Cortex Analyst Getting Started](https://quickstarts.snowflake.com/guide/getting_started_with_cortex_analyst/) - Step-by-step tutorial for building semantic models

TPC-DS Resources:
- [TPC-DS Benchmark Specification](https://www.tpc.org/tpcds/) - Official TPC-DS specification and documentation
- [TPCDS NLQ Benchmark](https://github.com/NLQBenchmarks/TPCDS_Benchmark) - Open benchmark for evaluating Text-to-SQL solutions with 40 questions
- [Snowflake Sample Data: TPC-DS](https://docs.snowflake.com/en/user-guide/sample-data-tpcds) - Information about the TPC-DS sample data available in Snowflake

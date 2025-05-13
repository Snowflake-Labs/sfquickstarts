author: corydon baylor
id: finding-fraudulent-communities-with-neo4j
summary: How to find communities affected by fraud using louvain in Neo4j Graph Analytics for Snowflake
categories: getting-started,partner-integrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter

# Finding Fraudulent Communities with Neo4j
<!-- ------------------------ -->
## Overview
Duration: 2

### What is Neo4j Graph Analytics for Snowflake? 

Neo4j helps organizations find hidden relationships and patterns across billions of data connections deeply, easily, and quickly. **Neo4j Graph Analytics for Snowflake** brings to the power of graph directly to Snowflake, allowing users to run 65+ ready-to-use algorithms on their data, all without leaving Snowflake! 

### Discovering Communities in P2P Fraud
P2P Fraud Losses are Skyrocketing. 8% of banking customers reported being victims of P2P Scams in the past year, and the average loss to these scams was $176.

Finding different communities within P2P transactions is the first step towards identifying and ultimately ending P2P fraud. 

### Prerequisites
- The Native App [Neo4j Graph Analytics](https://app.snowflake.com/marketplace/listing/GZTDZH40B6/neo4j-neo4j-graph-analytics) for Snowflake
  
### What You Will Need
- Active Snowflake account with appropriate access to databases and schemas.
- Neo4j Graph Analytics application installed from the Snowflake marketplace. Access the marketplace via the menu bar on the left hand side of your screen, as seen below:
![image](assets/marketplace.png)

### What You Will Build
- A method to identify communities that are at high risk of fraud in P2P networks
  
### What You Will Learn
- How to prepare and project your data for graph analytics
- How to use community detection to identify fraud
- How to read and write directly from and to your snowflake tables

### Import the Notebook
- We’ve provided a Colab notebook to walk you through each SQL and Python step—no local setup required!
- Download the .ipynb found [here](https://github.com/neo4j-product-examples/snowflake-graph-analytics/tree/main/QuickStarts/Python%20Notebooks), and import the notebook into snowflake.
  ![image](assets/followalong.png)
- Don't forget to install streamlit and python package before you run. 

<!-- ------------------------ -->
## Loading the Data
Duration: 5

Dataset overview : This dataset is modelled to design and analyze a peer to peer transaction network to identify fraudulent activity using graph analytics. 
![image](assets/datamodel.png)


Let's name our database `P2P_DEMO`. Using the CSVs found [here](https://drive.google.com/drive/u/1/folders/1BnAnRSEfuwDvc4eQH8IRvy3tUkwOeaNf), We are going to add two new tables:

- One called `P2P_TRANSACTIONS` based on the p2p_transactions.csv
- One called `P2P_USERS based` on p2p_users.csv

Follow the steps found [here](https://docs.snowflake.com/en/user-guide/data-load-web-ui) to load in your data.

<!-- ------------------------ -->
## Setting Up
Before we run our algorithms, we need to set the proper permissions. But before we get started granting different roles, we need to ensure that you are using `accountadmin` to grant and create roles. Lets do that now:

```sql
-- you must be accountadmin to create role and grant permissions
use role accountadmin;
```

Next let's set up the necessary roles, permissions, and resource access to enable Graph Analytics to operate on data within the `p2p_demo.public schema`. It creates a consumer role (gds_role) for users and administrators, grants the GDS application access to read from and write to tables and views, and ensures that future tables are accessible. 

It also provides the application with access to the required compute pool and warehouse resources needed to run graph algorithms at scale.

```sql
USE SCHEMA P2P_DEMO.PUBLIC;

-- Create a consumer role for users and admins of the GDS application
CREATE ROLE IF NOT EXISTS gds_user_role;
CREATE ROLE IF NOT EXISTS gds_admin_role;
GRANT APPLICATION ROLE neo4j_graph_analytics.app_user TO ROLE gds_user_role;
GRANT APPLICATION ROLE neo4j_graph_analytics.app_admin TO ROLE gds_admin_role;

CREATE DATABASE ROLE IF NOT EXISTS gds_db_role;
GRANT DATABASE ROLE gds_db_role TO ROLE gds_user_role;
GRANT DATABASE ROLE gds_db_role TO APPLICATION neo4j_graph_analytics;

-- Grant access to consumer data
GRANT USAGE ON DATABASE P2P_DEMO TO ROLE gds_user_role;
GRANT USAGE ON SCHEMA P2P_DEMO.PUBLIC TO ROLE gds_user_role;

-- Required to read tabular data into a graph
GRANT SELECT ON ALL TABLES IN DATABASE P2P_DEMO TO DATABASE ROLE gds_db_role;

-- Ensure the consumer role has access to created tables/views
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA P2P_DEMO.PUBLIC TO DATABASE ROLE gds_db_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA P2P_DEMO.PUBLIC TO DATABASE ROLE gds_db_role;
GRANT CREATE TABLE ON SCHEMA P2P_DEMO.PUBLIC TO DATABASE ROLE gds_db_role;
GRANT CREATE VIEW ON SCHEMA P2P_DEMO.PUBLIC TO DATABASE ROLE gds_db_role;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA P2P_DEMO.PUBLIC TO DATABASE ROLE gds_db_role;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA P2P_DEMO.PUBLIC TO DATABASE ROLE gds_db_role;

-- Compute and warehouse access
GRANT USAGE ON WAREHOUSE GDSONSNOWFLAKE TO APPLICATION neo4j_graph_analytics;
```

Now we will switch to the role we just created:

```sql
use role gds_role;
```


<!-- ------------------------ -->
## Cleaning Our Data
Duration: 5

We need our data to be in a particular format in order to work with Graph Analytics. In general it should be like so:

### For the table representing nodes:

The first column should be called `nodeId`, which represents the ids for the each node in our graph

### For the table representing relationships:

We need to have columns called `sourceNodeId` and `targetNodeId`. These will tell Graph Analytics the direction of the transaction, which in this case means:
- Who sent the money (sourceNodeId) and
- Who received it (targetNodeId)
- We also include a total_amount column that acts as the weights in the relationship

We are going to use aggregated transactions for our relationships. Let's create that table now:

```sql
CREATE OR REPLACE TABLE p2p_demo.public.P2P_AGG_TRANSACTIONS (
  SOURCENODEID NUMBER(38,0),
  TARGETNODEID NUMBER(38,0),
  TOTAL_AMOUNT FLOAT
) AS
SELECT sourceNodeId, targetNodeId, SUM(transaction_amount) AS total_amount
FROM p2p_demo.public.P2P_TRANSACTIONS
GROUP BY sourceNodeId, targetNodeId;
SELECT * FROM p2p_demo.public.P2P_AGG_TRANSACTIONS;
```


We are also going to create a view that just has the unique `nodeId`s from the `p2p_demo` table and use that as the nodes when we project the graph in the next step:

```sql
CREATE OR REPLACE VIEW p2p_users_vw (nodeId) AS
    SELECT DISTINCT p2p_demo.public.p2p_users.NODEID as nodeid
    FROM p2p_users;
```
<!-- ------------------------ -->

## Running your Algorithms
Duration: 10

Now we are finally at the step where we create a projection, run our algorithms, and write back to snowflake. We will run louvain to determine communities within our data. Louvain identifies communities by grouping together nodes that have more connections to each other than to nodes outside the group.

You can find more information about writing this function in our [documentation](https://neo4j.com/docs/snowflake-graph-analytics/current/getting-started/).

You can use this code block as an outline of what you need to fill in:

```
CALL Neo4j_GDS_app.graph.louvain('COMPUTE_POOL', {
    'project': {
        'nodeTables': ['EXAMPLE_DB.DATA_SCHEMA.NODES'],
        'relationshipTables': {
            'EXAMPLE_DB.DATA_SCHEMA.RELATIONSHIPS': {
                'sourceTable': 'EXAMPLE_DB.DATA_SCHEMA.NODES',
                'targetTable': 'EXAMPLE_DB.DATA_SCHEMA.NODES',
                'orientation': 'NATURAL'
            }
        }
    },
    'compute': { 'consecutiveIds': true },
    'write': [{
        'nodeLabel': 'NODES',
        'outputTable': 'EXAMPLE_DB.DATA_SCHEMA.NODES_COMPONENTS'
    }]
});
```

But broadly, you will need a few things:
| Name                                      | Description                                                 | Our Value                                      |
|-------------------------------------------|-------------------------------------------------------------|------------------------------------------------|
| `EXAMPLE_DB.DATA_SCHEMA.NODES`           | A table for nodes                             | `p2p_demo.public.p2p_users_vw`                 |
| `EXAMPLE_DB.DATA_SCHEMA.RELATIONSHIPS`   | A table for relationships                   | `p2p_demo.public.P2P_AGG_TRANSACTIONS`         |
| `COMPUTE_POOL`                            | The size of the compute pool you would like to use| `CPU_X64_XS`                              |
| `EXAMPLE_DB.DATA_SCHEMA.NODES_COMPONENTS`| A table to output results                    | `p2p_demo.public.p2p_users_vw_lou`             |
| `NODES`                                   | A node label for our nodes                   | `p2p_users_vw`                                 |


```sql
CALL neo4j_graph_analytics.graph.louvain('CPU_X64_XS', {
    'project': {
        'nodeTables': ['p2p_demo.public.p2p_users_vw'],
        'relationshipTables': {
            'p2p_demo.public.P2P_AGG_TRANSACTIONS': {
                'sourceTable': 'p2p_demo.public.p2p_users_vw',
                'targetTable': 'p2p_demo.public.p2p_users_vw',
                'orientation': 'NATURAL'
            }
        }
    },
    'compute': { 'consecutiveIds': true, 'relationshipWeightProperty':'TOTAL_AMOUNT'},
    'write': [{
        'nodeLabel': 'p2p_users_vw',
        'outputTable': 'p2p_demo.public.p2p_users_vw_lou'
    }]
});
```
Our resulting table assigns a community id to each node based on their connections to other nodes in the graph.

```sql
SELECT community, COUNT(*) AS community_size, 
FROM p2p_demo.public.p2p_users_vw_lou
GROUP BY community
ORDER BY community_size DESC;
```

We can then use then add in the `fraud_transfer_flag` (which was provided by the vendor) to our communities to see if users in that community are at greater risk for fraud:

```sql
SELECT
  l.community,
  COUNT(*) AS community_size,
  SUM(n.fraud_transfer_flag) AS fraud_count
FROM
  p2p_users_vw_lou l
JOIN
  p2p_users n
ON
  l.nodeId = n.nodeId
GROUP BY
  l.community
ORDER BY
  community_size DESC, fraud_count DESC;
```
You can use plotly as a visualization package and explore more. Nodes that cluster closely represent communities of highly interconnected users. You can immediately spot the tight clusters (possible fraud rings) versus the loosely connected periphery. Find more on exploratory analysis and demos [here](https://github.com/neo4j-product-examples/snowflake-graph-analytics).
![image](assets/communities_visualization.png)

##  Conclusions and Resources
Duration: 2

In this quickstart, you learned how to bring the power of graph insights into Snowflake using Neo4j Graph Analytics. 

### What you learned
By working with a P2P transaction dataset, you were able to:

1. Set up the [Neo4j Graph Analytics](https://app.snowflake.com/marketplace/listing/GZTDZH40CN) application within Snowflake.
2. Prepare and project your data into a graph model (users as nodes, transactions as relationships).
3. Ran Louvain community detection to identify clusters of users with high internal interaction.

### Resources

- [Neo4j GDS Documentation](https://neo4j.com/docs/snowflake-graph-analytics/)
- [Installing Neo4j GDS on SPCS](https://neo4j.com/docs/snowflake-graph-analytics/installation/)
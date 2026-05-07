author: Neo4j
id: practical-graph-analytics-neo4j-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/partner/technology/data-integration, snowflake-site:taxonomy/industry/manufacturing
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
language: en
summary: Learn how to apply Neo4j Graph Analytics algorithms directly in Snowflake to model a manufacturing workflow, identify structural risks, detect operational bottlenecks and surface machine similarity -- all without leaving Snowflake.

# Integrating Snowflake and Neo4j: Practical Graph Analytics for your Data

## Overview
Duration: 2

### What Is Neo4j Graph Analytics For Snowflake?

Neo4j helps organizations find hidden relationships and patterns across billions of data connections deeply, easily and quickly. **Neo4j Graph Analytics for Snowflake** brings the power of graphs directly to Snowflake, allowing users to run 65+ ready-to-use algorithms on their data, all without leaving Snowflake!

### Managing Risk in a Manufacturing Plant with Neo4j Graph Analytics

This guide shows how to model a manufacturing workflow in Neo4j and apply Graph Analytics algorithms to find structural risks, operational bottlenecks and machine similarities.

### Prerequisites

- A Snowflake account
- The Native App [Neo4j Graph Analytics](https://app.snowflake.com/marketplace/listing/GZTDZH40CN) installed from the Snowflake Marketplace

### What You Will Learn

- How to create a **graph projection**, which combines the nodes and their relationships into a single in-memory graph.
- How to conduct a **connectivity analysis**, which utilizes Weakly Connected Components (WCC) to identify any isolated subsystem.
- How to conduct a **criticality ranking** by using PageRank to find influential machines and Betweenness Centrality to identify bridges that control workflow.
- How to calculate **structural embeddings and similarity** by generating FastRP embeddings and then running K-Nearest Neighbor (KNN) to group machines with similar roles or dependencies.
- *(Optional)* How to run a **failure simulation** by removing a machine from the graph and measuring how structural importance shifts across the remaining machines.
- *(Optional)* How to apply **community detection** using Louvain to discover natural operational groupings and identify which clusters carry the most concentrated risk.

## Creating our Database
Duration: 7

We are going to create a simple database with some sample data. Start by setting the role and creating the database:

```sql
USE ROLE accountadmin;
CREATE DATABASE IF NOT EXISTS m_demo;
USE SCHEMA m_demo.public;
```

Then let's add some tables to that database:

```sql
CREATE OR REPLACE TABLE nodes (
    machine_id NUMBER(38, 0),
    machine_type VARCHAR(16777216),
    current_status VARCHAR(16777216),
    risk_level VARCHAR(16777216)
);

CREATE OR REPLACE TABLE rels (
    src_machine_id NUMBER(38, 0),
    dst_machine_id NUMBER(38, 0),
    throughput_rate NUMBER(38, 0)
);
```

Next, we are going to populate the nodes table with 20 machines, including cutters, welders, presses, assemblers and painters:

```sql
DELETE FROM nodes;

INSERT INTO nodes (machine_id, machine_type, current_status, risk_level) VALUES
(1, 'Cutter', 'active', 'low'),
(2, 'Welder', 'active', 'low'),
(3, 'Press', 'active', 'medium'),
(4, 'Assembler', 'active', 'medium'),
(5, 'Paint', 'active', 'low'),
(6, 'Cutter', 'active', 'low'),
(7, 'Welder', 'active', 'medium'),
(8, 'Press', 'active', 'medium'),
(9, 'Assembler', 'active', 'low'),
(10, 'Paint', 'active', 'low'),
(11, 'Cutter', 'active', 'medium'),
(12, 'Welder', 'active', 'high'),
(13, 'Press', 'active', 'medium'),
(14, 'Assembler', 'active', 'high'),
(15, 'Paint', 'active', 'medium'),
(16, 'Cutter', 'active', 'low'),
(17, 'Welder', 'active', 'medium'),
(18, 'Press', 'active', 'low'),
(19, 'Assembler', 'active', 'medium'),
(20, 'Assembler', 'active', 'high');
```

Next, we will create a table that reflects how those machines connect to each other:

```sql
DELETE FROM rels;

INSERT INTO rels (src_machine_id, dst_machine_id, throughput_rate) VALUES
(1, 2, 50),
(2, 3, 50),
(3, 4, 50),
(4, 5, 50),
(5, 6, 50),
(6, 7, 50),
(7, 8, 50),
(8, 9, 50),
(9, 10, 50),
(1, 20, 200),
(2, 20, 180),
(3, 20, 160),
(4, 20, 140),
(11, 12, 20),
(12, 13, 20),
(13, 14, 20),
(14, 15, 20),
(15, 16, 20),
(16, 17, 20),
(17, 18, 20),
(18, 19, 20),
(19, 20, 20),
(3, 11, 120),
(10, 19, 19);
```

Before we run our algorithms, we need to set the proper permissions. First ensure you are using `accountadmin` to grant and create roles:

```sql
-- Must be accountadmin to create role and grant permissions
USE ROLE accountadmin;
USE WAREHOUSE neo4j_graph_analytics_app_warehouse;
```

Next, we can set up the necessary roles, permissions and resource access to enable Graph Analytics to operate on data within the `m_demo.public` schema. It creates a consumer role (gds_role) for users and administrators, grants the GDS application access to read from and write to tables and views and ensures that future tables are accessible.

It also provides the application with access to the required compute pool and warehouse resources needed to run graph algorithms at scale:

```sql
-- 1. Create the Account Role
CREATE ROLE IF NOT EXISTS gds_role;

-- 2. Grant permissions to the Account Role
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA m_demo.public TO ROLE gds_role;
GRANT CREATE VIEW ON SCHEMA m_demo.public TO ROLE gds_role;

-- 3. Grant permissions for the application
GRANT USAGE ON DATABASE m_demo TO APPLICATION neo4j_graph_analytics;
GRANT USAGE ON SCHEMA m_demo.public TO APPLICATION neo4j_graph_analytics;

-- 4. Create and configure the Database Role
CREATE DATABASE ROLE IF NOT EXISTS gds_db_role;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA m_demo.public TO DATABASE ROLE gds_db_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA m_demo.public TO DATABASE ROLE gds_db_role;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA m_demo.public TO DATABASE ROLE gds_db_role;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA m_demo.public TO DATABASE ROLE gds_db_role;
GRANT CREATE TABLE ON SCHEMA m_demo.public TO DATABASE ROLE gds_db_role;

-- 5. Grant the Database Role to the Application and the Account Role
GRANT DATABASE ROLE gds_db_role TO APPLICATION neo4j_graph_analytics;
GRANT DATABASE ROLE gds_db_role TO ROLE gds_role;

-- 6. Grant additional usage and management to the Account Role
GRANT USAGE ON DATABASE m_demo TO ROLE gds_role;
GRANT USAGE ON SCHEMA m_demo.public TO ROLE gds_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA m_demo.public TO ROLE gds_role;
GRANT CREATE TABLE ON SCHEMA m_demo.public TO ROLE gds_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA m_demo.public TO ROLE gds_role;
```

Then switch to the role we created:

```sql
USE WAREHOUSE neo4j_graph_analytics_app_warehouse;
USE ROLE gds_role;
USE DATABASE m_demo;
USE SCHEMA public;
```

Next, clean up the nodes table so it contains just the node ids, as required by the graph projection:

```sql
CREATE OR REPLACE TABLE nodes_vw AS
SELECT machine_id AS nodeId
FROM nodes;
```

Our relationship table might have more than one row per machine-pair, but we need to have exactly one `throughput_rate` per (source, target). To be safe, we aggregate the data:

```sql
CREATE OR REPLACE TABLE rels_vw AS
SELECT
    src_machine_id AS sourceNodeId,
    dst_machine_id AS targetNodeId,
    CAST(SUM(throughput_rate) AS FLOAT) AS total_amount
FROM rels
GROUP BY src_machine_id, dst_machine_id;
```

## Visualizing our Graph
Duration: 5

At this point, we may want to visualize our graph to get a better understanding of how everything fits together. First create a simplified view that we will use to build the visualization:

```sql
CREATE OR REPLACE VIEW plant_viz (nodeId, machine_type) AS
SELECT machine_id AS nodeId, machine_type
FROM nodes;
```

Next, in a Python cell, create the visualization. Similar to how we project graphs for our graph algorithms, we need to specify the node and relationship tables. We also add code to specify the color and caption for each node:

```python
import networkx as nx
import matplotlib.pyplot as plt
from snowflake.snowpark.context import get_active_session

session = get_active_session()

nodes_df = session.table('M_DEMO.PUBLIC.PLANT_VIZ').to_pandas()
rels_df = session.table('M_DEMO.PUBLIC.RELS_VW').to_pandas()

G = nx.Graph()

color_map = {}
colors_palette = plt.cm.Set3.colors
machine_types = nodes_df['MACHINE_TYPE'].unique()
for i, mt in enumerate(machine_types):
    color_map[mt] = colors_palette[i % len(colors_palette)]

for _, row in nodes_df.iterrows():
    G.add_node(row['NODEID'], machine_type = row['MACHINE_TYPE'])

src_col = [c for c in rels_df.columns if 'SOURCE' in c.upper() or 'SRC' in c.upper() or 'FROM' in c.upper()]
dst_col = [c for c in rels_df.columns if 'TARGET' in c.upper() or 'DST' in c.upper() or 'TO' in c.upper()]

if src_col and dst_col:
    for _, row in rels_df.iterrows():
        G.add_edge(row[src_col[0]], row[dst_col[0]])

node_colors = [color_map.get(G.nodes[n].get('machine_type', ''), 'grey') for n in G.nodes()]

fig, ax = plt.subplots(figsize = (12, 8))
pos = nx.spring_layout(G, seed = 42)
nx.draw(G, pos, ax = ax, node_color = node_colors, with_labels = False, node_size = 80, edge_color = 'lightgray', alpha = 0.9)

legend_handles = [plt.Line2D([0], [0], marker = 'o', color = 'w', markerfacecolor = color_map[mt], markersize = 10, label = mt) for mt in machine_types]
ax.legend(handles = legend_handles, title = 'Machine Type', loc = 'best')
ax.set_title('Plant Equipment Graph')
plt.tight_layout()
plt.show()
```

## Structural Connectivity Analysis
Duration: 5

Structural connectivity helps verify whether our production line is truly integrated or split into isolated sections. We use **Weakly Connected Components (WCC)** to evaluate this.

### Weakly Connected Components (WCC)

WCC treats the graph as undirected and groups machines that can reach each other without considering direction. If the graph splits into multiple components, it may signal siloed operations or disconnected subsystems -- both of which could introduce coordination challenges or unmonitored risks.

WCC gives a high-level view of connectivity, highlighting whether our plant functions as one unified system.

**How to Interpret WCC Results**

A single connected component is ideal -- it suggests an integrated production network. Multiple smaller components imply isolated lines or equipment clusters that may need integration or review.

**Expected Result**

The simulated data are designed to form a single significant component, reflecting a unified workflow.

Before running the first algorithm, we can check which algorithms are available in the Neo4j Graph Analytics app and also check the status of the compute pool. Neo4j uses Snowpark Container Services rather than a standard Snowflake warehouse, so if the pool status shows as SUSPENDED or STARTING, the first algorithm call will be slow while the containers spin up. Subsequent calls will be faster:

```sql
-- List all graph algorithms available in the Neo4j Graph Analytics app.
-- SHOW PROCEDURES returns the full procedure list for the app.
-- RESULT_SCAN then filters that output to the GRAPH schema only,
-- which contains the algorithms we will use in this notebook.
SHOW PROCEDURES IN APPLICATION neo4j_graph_analytics;

SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "schema_name" = 'GRAPH';
```

```sql
-- Show the status of the compute pool that Neo4j Graph Analytics runs on.
-- If the pool status shows as SUSPENDED or STARTING, the first algorithm call
-- will be slow while the containers spin up. Subsequent calls will be faster.
SHOW COMPUTE POOLS;
```

Now run WCC:

```sql
CALL neo4j_graph_analytics.graph.wcc('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_vw'],
    'relationshipTables': {
      'rels_vw': {
        'sourceTable': 'nodes_vw',
        'targetTable': 'nodes_vw'
      }
    }
  },
  'compute': {},
  'write': [
    {
      'nodeLabel': 'nodes_vw',
      'outputTable': 'm_demo.public.nodes_vw_wcc'
    }
  ]
});
```

Query the results:

```sql
SELECT component, COUNT(*) AS count
FROM m_demo.public.nodes_vw_wcc
GROUP BY component
ORDER BY count DESC
LIMIT 5;
```

## Criticality Analysis
Duration: 10

Identifying the most critical machines in our workflow can help avoid shutdowns. If these machines slow down or fail, downstream operations halt. We use centrality algorithms to surface high-impact nodes -- both machines that concentrate flow (PageRank) and machines that connect key sections of the graph (Betweenness). This gives us a fuller picture of how risk and workload are distributed. With these analyses, we can:

- Prioritize monitoring of the machines whose disruption would ripple through the entire line.
- Allocate maintenance resources where they'll have the most significant effect.
- Design redundancy or backup processes around our process hubs.
- Plan capacity expansions by understanding which machines handle the most "traffic."

### PageRank Centrality

Designed initially to rank web pages, PageRank measures a node's importance by the "quality and quantity" of incoming edges. In our graph, an edge **A FEEDS_INTO B** means "Machine A feeds into Machine B." A high PageRank score indicates a machine that receives material from many other well-connected machines.

**How to Interpret PageRank Results**

The highest-scoring machines manage the most critical data flow.

**Expected Result**

Machine 20 has been set up as the processing hub for the simulated data, so it should be at the very top of the list.

```sql
CALL neo4j_graph_analytics.graph.page_rank('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_vw'],
    'relationshipTables': {
      'rels_vw': {
        'sourceTable': 'nodes_vw',
        'targetTable': 'nodes_vw'
      }
    }
  },
  'compute': {
    'mutateProperty': 'score'
  },
  'write': [
    {
      'nodeLabel': 'nodes_vw',
      'outputTable': 'm_demo.public.nodes_vw_pagerank',
      'nodeProperty': 'score'
    }
  ]
});
```

```sql
SELECT nodeid, score
FROM m_demo.public.nodes_vw_pagerank
ORDER BY score DESC
LIMIT 5;
```

**Interpretation**

As expected, Machine 20 ranks highest, confirming its role as a central assembler in the workflow. Its high-risk status makes it a critical point of failure that should be closely monitored.

### Betweenness Centrality

PageRank highlights machines with the most influence based on incoming flow, but it doesn't capture which machines sit between major areas of the workflow. Betweenness Centrality fills that gap by identifying machines that appear frequently on the shortest paths between others, often acting as bridges or single points of failure.

**How to Interpret Betweenness Results**

Machines with high scores connect upstream and downstream sections of the plant. For example, Machine 3 ranks highest not because it handles the most volume but because it links multiple parts of the workflow. If it goes down, it risks disrupting connections across the system.

**Expected Result**

Machines positioned between major steps, especially those that route material across different sections, should have the highest betweenness scores.

```sql
CALL neo4j_graph_analytics.graph.betweenness('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_vw'],
    'relationshipTables': {
      'rels_vw': {
        'sourceTable': 'nodes_vw',
        'targetTable': 'nodes_vw'
      }
    }
  },
  'compute': {
    'mutateProperty': 'score'
  },
  'write': [{
    'nodeLabel': 'nodes_vw',
    'outputTable': 'm_demo.public.nodes_vw_btwn',
    'nodeProperty': 'score'
  }]
});
```

```sql
SELECT nodeid, score
FROM m_demo.public.nodes_vw_btwn
ORDER BY score DESC
LIMIT 5;
```

**Interpretation**

Machines 3, 14, 13 and 15 act as structural bridges in the workflow. Their high scores suggest they connect otherwise separate paths, making them key points of potential disruption if taken offline.

## Structural Embeddings & Similarity
Duration: 10

Getting an even deeper understanding of each machine's workflow requires more than looking at direct connections. Structural embeddings capture broader patterns by summarizing each machine's position in the overall operation into a numeric vector. This allows us to:

- Group machines with similar roles or dependencies.
- Identify candidates for backup or load-balancing.
- Spot unusual machines that behave differently from the rest of the plant.

We will use two GDS algorithms together. First, **Fast Random Projection (FastRP)** generates a compact 16-dimensional vector for each machine by sampling the graph around each node, so two machines with similar surroundings will end up with similar embeddings. Second, **K-Nearest Neighbor (KNN)** finds, for each machine, the top K most similar peers based on cosine similarity of their embeddings.

### Fast Random Projection (FastRP) Embeddings

The results for FastRP are not immediately interpretable. However, machines with nearly identical embeddings have similar upstream and downstream relationships and likely play the same role in the plant. These embeddings are numerical representations that enable downstream clustering, similarity search or anomaly detection.

```sql
CALL neo4j_graph_analytics.graph.fast_rp('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_vw'],
    'relationshipTables': {
      'rels_vw': {
        'sourceTable': 'nodes_vw',
        'targetTable': 'nodes_vw'
      }
    }
  },
  'compute': {
    'mutateProperty': 'embedding',
    'embeddingDimension': 16
  },
  'write': [
    {
      'nodeLabel': 'nodes_vw',
      'outputTable': 'm_demo.public.nodes_vw_fast_rp',
      'nodeProperty': 'embedding'
    }
  ]
});
```

```sql
SELECT nodeid AS machine, embedding
FROM m_demo.public.nodes_vw_fast_rp
LIMIT 5;
```

Our initial graph projection does not include any property information, so we will create a new graph projection that includes the new `embedding` property we created for any future downstream algorithms.

### K-Nearest Neighbor (KNN)

Once we have embeddings for every machine, we can use KNN to find the most structurally similar machines based on their vector representations. KNN compares the cosine similarity between embeddings to pull out the top matches for each machine.

**How to Interpret KNN Results**

Machines with similarity scores close to 1.0 share almost identical structural patterns in the graph. These often appear in mirrored parts of the workflow or play equivalent roles in different lines. They're good candidates for backup coverage, shared scheduling or synchronized maintenance.

**Expected Result**

Machines that serve in parallel sections, especially those feeding into similar downstream equipment, should appear as near-duplicates. In this dataset, pairs like (17 and 9) were intentionally structured this way and are expected to rank near the top.

```sql
-- KNN operates on node embedding properties, not graph edges,
-- so no relationship table is needed in this projection.
CALL neo4j_graph_analytics.graph.knn('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': [ 'nodes_vw_fast_rp' ],
    'relationshipTables': {}
  },
  'compute': {
    'nodeProperties': ['EMBEDDING'],
    'topK': 1,
    'mutateProperty': 'score',
    'mutateRelationshipType': 'SIMILAR'
  },
  'write': [
    {
      'outputTable': 'm_demo.public.nodes_vw_knn',
      'sourceLabel': 'nodes_vw_fast_rp',
      'targetLabel': 'nodes_vw_fast_rp',
      'relationshipType': 'SIMILAR',
      'relationshipProperty': 'score'
    }
  ]
});
```

```sql
SELECT sourcenodeid, targetnodeid, score
FROM m_demo.public.nodes_vw_knn
ORDER BY score DESC
LIMIT 5;
```

**Interpretation**

Even though machines like 10 and 18 do different things (Painter vs Press), their positions in the workflow are nearly identical. They both act as mid-line feeders into multiple downstream machines and that structural role is what the algorithm captures.

This doesn't mean they're functionally interchangeable, but it suggests they share similar dependencies, bottleneck risks or monitoring needs. In a real plant, this insight could inform maintenance alignment or shared spares, redundancy planning and risk modeling and load distribution.

Structural similarity gives us a way to surface these patterns automatically, even across machines that don't look related on paper.

## (Optional) Failure Simulation: What Happens When a Machine Goes Offline?
Duration: 10

So far we have identified which machines are the most critical based on their position in the workflow. But what actually happens to the rest of the plant if one of those machines goes offline?

In this section we simulate a failure by removing a machine and all its connections from the graph, then re-running PageRank and Betweenness Centrality to see how scores shift across the remaining machines. This turns our static risk analysis into a dynamic "what-if" tool.

### What You Will Do

- Pick a high-impact machine to take offline (Machine 3, our highest Betweenness scorer).
- Create filtered node and relationship views that exclude it.
- Re-run PageRank and Betweenness on the degraded graph.
- Compare before and after scores to surface which machines absorb the most additional risk.

Simulate Machine 3 going offline by excluding it from nodes and relationships. We create new views rather than modifying the original tables so the base data stays intact and we can easily swap in a different machine later:

```sql
CREATE OR REPLACE VIEW m_demo.public.nodes_failure_vw AS
SELECT machine_id AS nodeId
FROM nodes
WHERE machine_id != 3;

CREATE OR REPLACE VIEW m_demo.public.rels_failure_vw AS
SELECT
    src_machine_id AS sourceNodeId,
    dst_machine_id AS targetNodeId,
    CAST(SUM(throughput_rate) AS FLOAT) AS total_amount
FROM rels
WHERE src_machine_id != 3 AND dst_machine_id != 3
GROUP BY src_machine_id, dst_machine_id;
```

Re-run PageRank using the failure views:

```sql
-- Re-run PageRank using the failure views instead of the original tables.
-- Results are written to a new output table so we can compare with the baseline.
CALL neo4j_graph_analytics.graph.page_rank('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_failure_vw'],
    'relationshipTables': {
      'rels_failure_vw': {
        'sourceTable': 'nodes_failure_vw',
        'targetTable': 'nodes_failure_vw'
      }
    }
  },
  'compute': {
    'mutateProperty': 'score'
  },
  'write': [
    {
      'nodeLabel': 'nodes_failure_vw',
      'outputTable': 'm_demo.public.nodes_failure_pagerank',
      'nodeProperty': 'score'
    }
  ]
});
```

Compare PageRank before and after. Raw scores shrink after failure because the graph is smaller, so we normalize each score by the sum of all scores in that run to compare relative importance within each graph, not absolutes:

```sql
SELECT
    b.nodeid,
    n.machine_type,
    n.risk_level,
    ROUND(b.score / SUM(b.score) OVER (), 4) AS baseline_pct,
    ROUND(f.score / SUM(f.score) OVER (), 4) AS failure_pct,
    ROUND((f.score / SUM(f.score) OVER ()) - (b.score / SUM(b.score) OVER ()), 4) AS delta
FROM m_demo.public.nodes_vw_pagerank b
JOIN m_demo.public.nodes_failure_pagerank f ON b.nodeid = f.nodeid
JOIN m_demo.public.nodes n ON b.nodeid = n.machine_id
ORDER BY delta DESC
LIMIT 10;
```

**Interpretation**

Machine 20 gains the most relative importance after Machine 3 goes offline, which makes sense. Machine 3 was feeding directly into Machine 20 with a throughput of 160, so Machine 20 now relies more heavily on the remaining upstream sources, making it proportionally more dominant.

Machines 19 and 10 also rise as these sit in the secondary chain (the `11 -> 12 -> ... -> 19 -> 20` path) that Machine 3 was bridging into via the `3 -> 11` connection. With that bridge gone, flow through that chain becomes relatively more significant.

The deltas are small but meaningful and all positive, which is correct. Every remaining machine absorbs a small share of the relative importance that Machine 3 held. No machine dominates dramatically, which reflects that Machine 3 was primarily a *bridge* (high Betweenness) rather than a *flow hub* (high PageRank).

Re-run Betweenness Centrality on the degraded graph:

```sql
CALL neo4j_graph_analytics.graph.betweenness('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_failure_vw'],
    'relationshipTables': {
      'rels_failure_vw': {
        'sourceTable': 'nodes_failure_vw',
        'targetTable': 'nodes_failure_vw'
      }
    }
  },
  'compute': {
    'mutateProperty': 'score'
  },
  'write': [
    {
      'nodeLabel': 'nodes_failure_vw',
      'outputTable': 'm_demo.public.nodes_failure_btwn',
      'nodeProperty': 'score'
    }
  ]
});
```

Compare Betweenness before and after. A positive delta means a machine has become relatively more central after Machine 3 was removed -- a genuine emergent risk signal:

```sql
SELECT
    b.nodeid,
    n.machine_type,
    n.risk_level,
    ROUND(b.score / NULLIF(SUM(b.score) OVER (), 0), 4) AS baseline_pct,
    ROUND(f.score / NULLIF(SUM(f.score) OVER (), 0), 4) AS failure_pct,
    ROUND((f.score / NULLIF(SUM(f.score) OVER (), 0)) - (b.score / NULLIF(SUM(b.score) OVER (), 0)), 4) AS delta
FROM m_demo.public.nodes_vw_btwn b
JOIN m_demo.public.nodes_failure_btwn f ON b.nodeid = f.nodeid
JOIN m_demo.public.nodes n ON b.nodeid = n.machine_id
ORDER BY delta DESC
LIMIT 10;
```

**Interpretation**

These results tell us a much more interesting story than the PageRank ones. The deltas here are an order of magnitude larger than PageRank, which is exactly what we'd expect. Machine 3 was the top Betweenness scorer, so its removal genuinely reshuffles structural importance across the plant.

Machines 17, 18 and 19 gain the most as these sit deep in the secondary chain (the `11 -> ... -> 19 -> 20` path). Machine 3 was the only entry point into that chain via `3 -> 11`, so with it gone, machines further along that chain now become the primary bridges between the two halves of the plant.

Machine 14 (high risk, Assembler) gains less than we might expect as it was already a high Betweenness scorer in its own right. But combined with its existing high baseline and high risk level, it's arguably the most concerning machine in the post-failure graph.

The machines that gain the most Betweenness are not necessarily the ones already flagged as high risk. Machine 18 (low risk, Press) jumps to second place. That's the point of the simulation -- it surfaces hidden risk that static analysis misses.

Visualize the Betweenness delta scores as a bar chart:

```python
# Bar chart comparing Betweenness delta scores after Machine 3 failure.
import pandas as pd
import matplotlib.pyplot as plt
from snowflake.snowpark.context import get_active_session

session = get_active_session()

baseline = session.table('M_DEMO.PUBLIC.NODES_VW_BTWN').to_pandas()
failure  = session.table('M_DEMO.PUBLIC.NODES_FAILURE_BTWN').to_pandas()
nodes    = session.table('M_DEMO.PUBLIC.NODES').to_pandas()

merged = baseline.merge(failure, on = 'NODEID', suffixes = ('_base', '_fail'))
merged = merged.merge(nodes[['MACHINE_ID', 'MACHINE_TYPE', 'RISK_LEVEL']],
                      left_on = 'NODEID', right_on = 'MACHINE_ID')
merged['DELTA'] = (merged['SCORE_fail'] / merged['SCORE_fail'].sum()) - (merged['SCORE_base'] / merged['SCORE_base'].sum())
merged = merged.sort_values('DELTA', ascending = False).head(10)

colors = {'low': 'steelblue', 'medium': 'orange', 'high': 'crimson'}
bar_colors = merged['RISK_LEVEL'].str.lower().map(colors).fillna('grey')

fig, ax = plt.subplots(figsize = (12, 6))
bars = ax.bar(merged['NODEID'].astype(str), merged['DELTA'], color = bar_colors)
ax.set_xlabel('Machine ID')
ax.set_ylabel('Betweenness Delta')
ax.set_title('Change in Betweenness Centrality After Machine 3 Failure')

legend_handles = [plt.Rectangle((0,0),1,1, color = c, label = l.capitalize())
                  for l, c in colors.items()]
ax.legend(handles = legend_handles, title = 'Risk Level')
plt.tight_layout()
plt.show()
```

**Interpretation**

The machines with the largest positive delta are the ones that have absorbed the most structural importance following Machine 3's failure. Even if they had low baseline scores, they may now be acting as the primary bridges in the workflow.

Pay particular attention to any machine that combines a **large delta** with a **high risk level** -- these are the emergent failure points that would not have been visible without the simulation. The colour coding instantly draws the eye to Machine 14 (the only high-risk bar sitting towards the right) -- the machine you should be most worried about isn't necessarily the one that changed the most.

> **Try it yourself:** Change `machine_id != 3` in the filtered views to a different machine and re-run to explore other failure scenarios.

## (Optional) Community Detection: Finding Natural Machine Groupings with Louvain
Duration: 10

So far, our analysis has focused on individual machines -- which ones are most critical, most similar or most affected by failure. Louvain Community Detection takes a different perspective by asking: **does the plant naturally organize itself into clusters?**

Louvain is a graph partitioning algorithm that finds groups of machines that are more densely connected to each other than to the rest of the plant. These communities often correspond to real operational sub-units -- parallel production lines, shared workflow stages or tightly coupled machine groups.

### What You Will Do

- Run Louvain on the full plant graph to detect natural communities.
- Join the results back to our machine metadata to see what each community looks like.
- Visualize the communities to see if they map to meaningful operational groupings.
- Cross-reference with our criticality results to identify which communities carry the most risk.

Run Louvain. The algorithm assigns each machine a community ID based on connection density:

```sql
-- Louvain assigns each machine a community ID based on connection density.
-- Machines in the same community are more tightly connected to each other
-- than to the rest of the plant, which often reflects natural operational groupings.
CALL neo4j_graph_analytics.graph.louvain('CPU_X64_XS', {
  'project': {
    'defaultTablePrefix': 'm_demo.public',
    'nodeTables': ['nodes_vw'],
    'relationshipTables': {
      'rels_vw': {
        'sourceTable': 'nodes_vw',
        'targetTable': 'nodes_vw'
      }
    }
  },
  'compute': {
    'mutateProperty': 'community'
  },
  'write': [
    {
      'nodeLabel': 'nodes_vw',
      'outputTable': 'm_demo.public.nodes_vw_louvain',
      'nodeProperty': 'community'
    }
  ]
});
```

> **Note:** The community IDs assigned by Louvain are not sequential labels -- they reflect the node ID of the first member assigned to that community internally. So "Community 16" simply means the community that node 16 was seeded into. What matters is the membership, not the ID number.

Summarize the communities. Join Louvain results back to our machine metadata to see what each community contains:

```sql
SELECT
    l.community,
    COUNT(*) AS machine_count,
    LISTAGG(n.machine_id, ', ') WITHIN GROUP (ORDER BY n.machine_id) AS machines,
    SUM(CASE WHEN n.risk_level = 'high'   THEN 1 ELSE 0 END) AS high_risk_count,
    SUM(CASE WHEN n.risk_level = 'medium' THEN 1 ELSE 0 END) AS medium_risk_count,
    SUM(CASE WHEN n.risk_level = 'low'    THEN 1 ELSE 0 END) AS low_risk_count
FROM m_demo.public.nodes_vw_louvain l
JOIN m_demo.public.nodes n ON l.nodeid = n.machine_id
GROUP BY l.community
ORDER BY machine_count DESC;
```

Cross-reference with PageRank and Betweenness scores to identify which community contains the most influential machines. A community with both high PageRank scores and high risk machines is a priority area for maintenance planning:

```sql
SELECT
    l.community,
    n.machine_id,
    n.machine_type,
    n.risk_level,
    ROUND(p.score, 4) AS pagerank_score,
    ROUND(b.score, 4) AS betweenness_score
FROM m_demo.public.nodes_vw_louvain l
JOIN m_demo.public.nodes n ON l.nodeid = n.machine_id
JOIN m_demo.public.nodes_vw_pagerank p ON l.nodeid = p.nodeid
JOIN m_demo.public.nodes_vw_btwn b ON l.nodeid = b.nodeid
ORDER BY l.community, p.score DESC;
```

**Interpretation**

- **Community 16 (12 machines) is the main production hub.** This is the larger, more influential cluster. It contains Machine 20 (the top PageRank node and the ultimate assembly hub) and most of the machines that feed directly into it. The high PageRank scores throughout confirm this community handles the dominant flow of the plant.
- **Community 19 (8 machines) is the secondary line.** This maps almost perfectly to the `11 -> 12 -> 13 -> 14 -> 15` chain that Machine 3 bridges into from the main line. Notably this community contains two high-risk machines (12 and 14) in a group of only 8 -- a higher risk concentration than Community 16 which has just one high-risk machine (20) across 12.

The really interesting insight is that Machine 3, our top Betweenness scorer and the machine we simulated failing, lands in Community 19, not Community 16. It's the bridge *between* these two communities -- which perfectly validates why its failure was so disruptive in the simulation.

Visualize the communities on the graph:

```python
# Visualise the plant graph with nodes coloured by Louvain community.
# Compare this to the original type-coloured graph to see whether
# communities align with machine types or cut across them.
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from snowflake.snowpark.context import get_active_session

session = get_active_session()

louvain_df = session.table('M_DEMO.PUBLIC.NODES_VW_LOUVAIN').to_pandas()
rels_df    = session.table('M_DEMO.PUBLIC.RELS_VW').to_pandas()
nodes_df   = session.table('M_DEMO.PUBLIC.NODES').to_pandas()

G = nx.Graph()

for _, row in louvain_df.iterrows():
    G.add_node(row['NODEID'], community = row['COMMUNITY'])

src_col = [c for c in rels_df.columns if 'SOURCE' in c.upper() or 'SRC' in c.upper()]
dst_col = [c for c in rels_df.columns if 'TARGET' in c.upper() or 'DST' in c.upper()]

if src_col and dst_col:
    for _, row in rels_df.iterrows():
        G.add_edge(row[src_col[0]], row[dst_col[0]])

communities = sorted(louvain_df['COMMUNITY'].unique())
palette     = cm.Set2.colors
color_map   = {c: palette[i % len(palette)] for i, c in enumerate(communities)}
node_colors = [color_map[G.nodes[n]['community']] for n in G.nodes()]

# Use the same layout seed as the original graph so positions are comparable
pos = nx.spring_layout(G, seed = 42)

fig, ax = plt.subplots(figsize = (12, 8))
nx.draw(G, pos, ax = ax, node_color = node_colors, with_labels = True,
        node_size = 500, edge_color = 'lightgray', font_size = 8, alpha = 0.9)

legend_handles = [plt.Line2D([0], [0], marker = 'o', color = 'w',
                              markerfacecolor = color_map[c], markersize = 12,
                              label = f'Community {c}')
                  for c in communities]
ax.legend(handles=legend_handles, title = 'Community', loc = 'best')
ax.set_title('Plant Equipment Graph -- Louvain Communities')
plt.tight_layout()
plt.show()
```

**Interpretation**

Each color in the graph represents a community of machines that are more densely connected to each other than to the rest of the plant. A few things to look for:

- **Do communities align with machine types?** If they cut across types, it suggests the workflow topology matters more than machine function.
- **Check the summary table for risk concentration.** A community with a high `high_risk_count` relative to its size is a priority area -- multiple vulnerable machines clustered together amplify each other's failure risk.
- **Cross-reference with PageRank and Betweenness.** A community that contains both the top PageRank and top Betweenness nodes is both the most influential and the most structurally sensitive cluster in the plant.

Communities give maintenance teams a natural unit for planning -- rather than monitoring machines individually, teams can be assigned to communities that reflect how the plant actually flows.

> **Try it yourself:** Re-run Louvain after the Machine 3 failure simulation to see whether the community structure changes. Losing a bridge node can cause communities to merge or split.

## Conclusions and Resources
Duration: 2

In this guide, we learned how to bring the power of graph insights into Snowflake using Neo4j Graph Analytics.

### What You Learned

By working with a simulated manufacturing database, we were able to:

1. Set up the [Neo4j Graph Analytics](https://app.snowflake.com/marketplace/listing/GZTDZH40CN/neo4j-neo4j-graph-analytics) application within Snowflake.
2. Prepare and project our data into a graph model (machines as nodes, connections as relationships).
3. Ran connectivity analysis using Weakly Connected Components to verify the plant operates as a single integrated system.
4. Identify critical machines using PageRank and Betweenness Centrality to surface flow hubs and structural bridges.
5. Generate structural embeddings with FastRP and used KNN to find machines with similar roles or dependencies.
6. *(Optional)* Simulate a machine failure and measured how structural importance redistributes across the remaining plant -- surfacing hidden risk that static analysis alone would miss.
7. *(Optional)* Detect natural machine communities using Louvain, revealing that the plant splits into two operationally distinct clusters with different risk profiles.

### Related Resources

- [Neo4j Graph Analytics Documentation](https://neo4j.com/docs/snowflake-graph-analytics/)
- [Neo4j Graph Academy](https://graphacademy.neo4j.com/)
- [Neo4j Graph Analytics on Snowflake Marketplace](https://app.snowflake.com/marketplace/listing/GZTDZH40CN)

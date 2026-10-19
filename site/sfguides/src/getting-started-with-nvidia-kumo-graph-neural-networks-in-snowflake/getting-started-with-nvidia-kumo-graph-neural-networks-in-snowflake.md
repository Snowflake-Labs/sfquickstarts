author: Akhil Ramasagaram
id: getting-started-with-nvidia-kumo-graph-neural-networks-in-snowflake
summary: Build, train, and run an NVIDIA Kumo graph neural network on your relational data, entirely inside Snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/model-development
environments: web
language: en
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with NVIDIA Kumo Graph Neural Networks in Snowflake

## Overview

Kumo turns your relational tables into a graph and trains a graph neural network on it, so you can predict outcomes without hand building features. In this guide you will train a model on customer, order, and product tables and write a 30 day reorder prediction for every active customer back to a Snowflake table.

### What You'll Learn

* How to install Kumo in a Snowflake Notebook on Container Runtime
* How to describe relational tables as a Kumo graph
* How to write a predictive query, train a graph neural network, and write predictions to Snowflake

### What You'll Build

* A Kumo graph over four sales tables
* A predictive query: will this customer order again in the next 30 days?
* A trained model and a predictions table in Snowflake

### What You'll Need

* A [Snowflake account](https://signup.snowflake.com/) with access to a GPU compute pool and Snowflake Notebooks on Container Runtime
* Cortex Code (CoCo) Desktop or CLI connected to that account
* The [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) to load the sample data
* A database and schema you can write to (referred to below as `<DB>.<SCHEMA>`)
* The Kumo wheel and the Kumo skill (links in [Get Kumo](#get-kumo))

## Get Kumo

Kumo Engine is published by NVIDIA as the [`kumo-engine`](https://pypi.org/project/kumo-engine/) package on PyPI. Download the wheel from the **Download files** tab; it is a single `.whl` for Linux x86_64 and Python 3.11 or later.

Source code, examples, and agent skills are in the [NVIDIA Kumo Engine repository](https://github.com/NVIDIA/kumo-engine), and the full reference is in the [Kumo Engine documentation](https://docs.nvidia.com/sdgm/kumo-engine/get-started-with-kumo-engine/overview).

## One Time Setup

Do these steps once per account. You do not repeat them for each session.

### Step 1: Load the sample data

This guide uses the `Customer`, `SalesOrderHeader`, `SalesOrderDetail`, and `Product` tables from the [Microsoft SQL Server sample OLTP database](https://github.com/Microsoft/sql-server-samples/tree/master/samples/databases/adventure-works/oltp-install-script). The [loader script](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-nvidia-kumo-graph-neural-networks-in-snowflake/assets/load_sample_data.sql) creates the four tables and loads them. Download the data files and the script, then run it:

```bash
BASE=https://raw.githubusercontent.com/microsoft/sql-server-samples/master/samples/databases/adventure-works/oltp-install-script
for t in Customer Product SalesOrderHeader SalesOrderDetail; do curl -sLO "$BASE/$t.csv"; done
curl -sLO https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/getting-started-with-nvidia-kumo-graph-neural-networks-in-snowflake/assets/load_sample_data.sql

snow sql -f load_sample_data.sql -D "db=<DB>" -D "schema=<SCHEMA>" -D "wh=<WAREHOUSE>"
```

The script ends with a row count check: 19,820 customers, 504 products, 31,465 orders, and 121,317 order lines.

### Step 2: Publish the wheel to a Snowflake Workspace with CoCo

The wheel is too large to upload through the Snowsight UI, and several of its pinned dependencies need adjusting for the Snowflake Container Runtime image. Let CoCo handle both. Open CoCo and paste this prompt, replacing the path:

```text
I downloaded the Kumo wheel to <LOCAL_PATH_TO_WHEEL>.
Publish it to my Snowflake Workspace so a Snowflake Notebook on Container Runtime (Python 3.12, GPU) can pip install it.

1. Inspect the wheel METADATA and compare every Requires-Dist pin against the packages already present in the Container Runtime GPU py312 image.
2. Where a pin conflicts with the base image (for example torch, fsspec, cryptography, faiss) or names a package that does not exist on PyPI, relax or rename that pin in METADATA, rebuild the RECORD hashes, and keep the PEP 427 filename valid. Do not downgrade packages the base image depends on.
3. Write a requirements.txt containing only the third party packages the base image is missing, with versions that satisfy pip check.
4. Upload the patched wheel and requirements.txt to my Workspace under kumo/ using the cortex ws CLI, not the UI.
5. Print the final Workspace paths and a summary of every pin you changed and why.
```

CoCo uploads through the CLI, so the UI size limit does not apply.

### Step 3: Install the Kumo skill in CoCo

The skill teaches CoCo the Kumo SDK so it can help you build graphs and queries on your own data. It lives in the [Kumo agent skills repository](https://github.com/NVIDIA/kumo-engine/tree/main/agent-skills). Clone it and copy the skills into your CoCo skills folder:

```bash
git clone --depth 1 https://github.com/NVIDIA/kumo-engine.git
cp -r kumo-engine/agent-skills/* ~/.snowflake/cortex/skills/
```

**Restart CoCo** after copying so it picks up the new skill.

## Each Session Setup

Do these steps every time you start a new notebook session, since Container Runtime sessions do not persist installed packages.

### Step 4: Install the wheel in the notebook

Create a Snowflake Notebook on Container Runtime with a GPU compute pool, then run:

```python
!pip install -q -r kumo/requirements.txt
!pip install -q --no-deps kumo/<KUMO_WHEEL_FILENAME>.whl
```

**Restart the kernel** now. Kumo will not import until you do.

## Import Libraries

```python
import kumoai as kumo
from kumoapi.graph import Edge
from kumoapi.typing import Stype
from kumoapi.model_plan import RunMode
from kumoapi.jobs import PredictionArtifactType, WriteMode
from datetime import datetime

kumo.configure(scratch_dir="/tmp/kumo")
```

## Connect to Your Tables

`kumo.SnowflakeConnector` reads the notebook session identity, so no credentials are needed.

```python
TARGET = dict(warehouse="<WAREHOUSE>", database="<DB>", schema_name="<SCHEMA>")
connector = kumo.SnowflakeConnector.from_spcs_env(**TARGET)
connector.table_names()
```

## Define Tables

`kumo.Table` wraps each source table with its primary key and time column. Foreign keys are often inferred as numbers, so mark them as IDs.

```python
customer = kumo.Table.from_source_table(connector["Customer"], primary_key="CustomerID")

orders = kumo.Table.from_source_table(
    connector["SalesOrderHeader"], primary_key="SalesOrderID", time_column="OrderDate"
).with_column("CustomerID", stype=Stype.ID)

order_lines = kumo.Table.from_source_table(
    connector["SalesOrderDetail"], primary_key="SalesOrderDetailID", time_column="ModifiedDate"
).with_column("SalesOrderID", stype=Stype.ID).with_column("ProductID", stype=Stype.ID)

product = kumo.Table.from_source_table(
    connector["Product"], primary_key="ProductID", time_column="SellStartDate"
)
```

## Build the Graph

`kumo.Graph` links the tables through their foreign keys.

```python
graph = kumo.Graph(
    tables=[customer, orders, order_lines, product],
    edges=[
        Edge(src_table="SalesOrderHeader", fkey="CustomerID", dst_table="Customer"),
        Edge(src_table="SalesOrderDetail", fkey="SalesOrderID", dst_table="SalesOrderHeader"),
        Edge(src_table="SalesOrderDetail", fkey="ProductID", dst_table="Product"),
    ],
)
graph.validate()
```

## Write the Predictive Query

The query reads like SQL: for each customer who ordered in the last 30 days, predict whether they order again in the next 30.

```python
pquery = kumo.PredictiveQuery(graph=graph, query="""
PREDICT COUNT(SalesOrderHeader.*, 0, 30, days) > 0
FOR EACH Customer.CustomerID
WHERE COUNT(SalesOrderHeader.*, -30, 0, days) > 0
""")
pquery.validate()

snapshot = graph.snapshot()
training_table = pquery.generate_training_table(snapshot)
# Pick the date you want to predict from. 2025-06-30 is the day after the last order in the sample data.
prediction_table = pquery.generate_prediction_table(snapshot, prediction_time=datetime(2025, 6, 30))
```

`prediction_time` is the date predictions are made from. The value above fits the sample data; for your own tables, pick a date for prediction, usually the day after your most recent record.

## Train with fit

```python
plan = pquery.suggest_model_plan(snapshot, run_mode=RunMode.FAST)
trainer = kumo.Trainer(plan)
result = trainer.fit(training_table, snapshot=snapshot)
result.metrics
```

## Predict

`predict` writes scores straight to a Snowflake table.

```python
trainer.predict(
    prediction_table,
    snapshot=snapshot,
    output_config=kumo.PredictionOutputConfig(
        connector=connector,
        artifact_type=PredictionArtifactType.PREDICTIONS,
        table_name="<PREDICTIONS_TABLE_NAME>",
        write_mode=WriteMode.OVERWRITE,
    ),
)
```

Check the results:

```sql
SELECT * FROM <DB>.<SCHEMA>.<PREDICTIONS_TABLE_NAME> LIMIT 10;
```

The predictions table is the artifact your downstream applications read from, so keep it.

## Save GPU Cost

When you finish, stop the notebook session and suspend the GPU compute pool so it stops consuming credits:

```sql
ALTER COMPUTE POOL <GPU_COMPUTE_POOL_NAME> SUSPEND;
```

Resume it the next time you need it with `ALTER COMPUTE POOL <GPU_COMPUTE_POOL_NAME> RESUME;`.

## Conclusion And Resources

You connected Kumo to Snowflake, built a graph over four tables, and predicted 30 day reorders without writing a single feature. Try changing the query to predict revenue, churn, or the next product a customer buys.

### What You Learned

* How to publish the Kumo wheel to a Snowflake Workspace and install it in a notebook
* How to connect Kumo to Snowflake tables and describe them as a graph
* How to write a predictive query, train a graph neural network with `fit`, and score with `predict`
* How to write predictions to a Snowflake table and suspend GPU compute when done

### Resources

* [Snowflake ML documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)

* [Snowflake and NVIDIA Kumo launch blog](https://www.snowflake.com/en/blog/nvidia-kumo-graph-ml-snowflake/)
* [Kumo Engine documentation](https://docs.nvidia.com/sdgm/kumo-engine/get-started-with-kumo-engine/overview)
* [NVIDIA Kumo Engine on GitHub](https://github.com/NVIDIA/kumo-engine)
* [kumo-engine on PyPI](https://pypi.org/project/kumo-engine/)
* Sample dataset: [Microsoft SQL Server sample OLTP install script](https://github.com/Microsoft/sql-server-samples/tree/master/samples/databases/adventure-works/oltp-install-script)
* Kumo skill for CoCo: [Kumo agent skills](https://github.com/NVIDIA/kumo-engine/tree/main/agent-skills)
* Sample data loader: [load_sample_data.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-nvidia-kumo-graph-neural-networks-in-snowflake/assets/load_sample_data.sql)

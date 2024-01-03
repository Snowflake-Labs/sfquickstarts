author: Gilberto Hernandez
id: getting-started-snowflake-python-api
summary: Learn how to get started with Snowflake's Python API to manage Snowflake objects and tasks.
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Getting Started with the Snowflake Python API

<!-- ------------------------ -->
## Overview 
Duration: 1

The Snowflake Python API allows you to manage Snowflake using Python. Using the API, you're able to create, delete, and modify tables, schemas, warehouses, tasks, and much more, in many cases without needing to write SQL or use the Snowflake Connector for Python. In this Quickstart, you'll learn how to get started with the Snowflake Python API for object and task management with Snowflake.


### Prerequisites
- Familiarity with Python
- Familiarity with Jupyter Notebooks

### What You’ll Learn 
- How to install the Snowflake Python API library
- How to create a Root object to use the API
- How to create tables, schemas, and warehouses using the API
- (Coming Soon) How to create and manage tasks using the API
- (Coming Soon) How to use Snowpark Container Services with the Snowflake Python API

### What You’ll Need 
- A Snowflake account ([trial](https://signup.snowflake.com/), or otherwise)
- A code editor that supports Jupyter notebooks, or ability to run notebooks in your browser using `jupyter notebook`

### What You’ll Build 
- Multiple objects within Snowflake

<!-- ------------------------ -->
## Install the Snowflake Python API
Duration: 8

> aside negative
> 
> **Important**
> The Snowflake Python API is currently supported in Python versions 3.8, 3.9., and 3.10.

Before installing the Snowflake Python API, we'll start by activating a Python environment.

**Conda**

If you're using conda, you can create and activate a conda environment using the following commands:

```bash
conda create -n <env_name> python==3.10
```

```bash
conda activate <env_name>
```

**venv**

If you're using venv, you can create and activate a virtual environment using the following commands:

```bash
python3 -m venv '.venv'
```

```bash
source '.venv/bin/activate'
```

The Snowflake Python API is available via PyPi. Install it by running the following command:

```bash
pip install snowflake
```


<!-- ------------------------ -->
## Overview of the Snowflake Python API
Duration: 5

Let's quickly take a look at how the Snowflake Python API is organized:


| **Module**  | **Description**  |
|---|---|
| `snowflake.core`  | Defines an Iterator to represent a certain resource instances fetched from the Snowflake database  |
| `snowflake.core.paging`  |   |
| `snowflake.core.exceptions`  |   |
| `snowflake.core.database`  |  Manages Snowflake databases |
| `snowflake.core.schema`  | Manages Snowflake schemas  |
| `snowflake.core.task`  | Manages Snowflake Tasks  |
| `snowflake.core.task.context`  | Manage the context in a Snowflake Task  |
| `snowflake.core.task.dagv1`  | A set of higher-level APIs than the lower-level Task APIs in snowflake.core.task to more conveniently manage DAGs|
| `snowflake.core.compute_pool`  |  Manages Snowpark Container Compute Pools |
| `snowflake.core.image_repository`  | Manages Snowpark Container Image Repositories  |
| `snowflake.core.service`  | Manages Snowpark Container Services  |


`snowflake.core` represents the entry point to the core Snowflake Python APIs that manage Snowflake objects. To use the Snowflake Python API, you'll follow a common pattern:

1. Establish a session using Snowpark, representing your connection to Snowflake.

2. Import and instantiate the `Root` class from `snowflake.core`, and pass in the Snowpark session object as an argument. You'll use the resulting `Root` object to use the rest of the methods and types in the Snowflake Python API.

Here's an example of what this pattern typically looks like:

```py
from snowflake.snowpark import Session
from snowflake.core import Root

connection_params = {
    "account": "ACCOUNT-IDENTIFIER",
    "user": "USERNAME",
    "password": "PASSWORD"
}
session = Session.builder.configs(connection_params).create()
root = Root(session)
```

The `connection_params` dictionary shown above is included for the purposes of demonstration only, specifying only the required connection parameters. In practice, consider using a configuration file with named connections that can be passed into `Session.builder.configs()`. For more information, see [Connecting to Snowflake with the Snowflake Python API](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-python-api/snowflake-python-connecting-snowflake).

Let's get started!

<!-- ------------------------ -->
## Set up your development environment
Duration: 10

In this Quickstart, we'll walk through a Jupyter notebook to incrementally showcase the capabilities of the Snowflake Python API. Let's start by setting up your development environment so that you can run the notebook.

1. First, download the [
Quickstart: Getting Started with the Snowflake Python API](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/sfguide-getting-started-snowflake-python-api/getting_started_snowflake_python_api.ipynb) notebook from the accompanying repo for this Quickstart.

2. Next, open the notebook in a code editor that supports Jupyter notebooks. Alternatively, open the notebook in your browser by starting the notebook server with `jupyter notebook` and navigating to the notebook.

Now, run the first cell within the notebook, the one containing the import statements.

```py
from snowflake.snowpark import Session
from snowflake.core import Root
from snowflake.core.database import Database
from snowflake.core.schema import Schema
from snowflake.core.table import Table, TableColumn, PrimaryKey
from snowflake.core.warehouse import Warehouse
```

> aside negative
> 
> **Note**
> Upon running this cell, you may be prompted to set your Python kernel. We activated a conda environment earlier, so we'll select conda as our Python kernel (i.e., something like `~/miniconda3/bin/python`).

In this cell, we import Snowpark and the core Snowflake Python APIs that manage Snowflake objects.

Next, configure the `connection_params` dictionary with your account credentials and run the cell.

```py
connection_params = {
    "account": "YOUR-ACCOUNT-IDENTIFIER",
    "user": "USERNAME",
    "password": "PASSWORD"
}
```

Create a Snowpark session and pass in your connection parameters to establish a connection to Snowflake.

```py
session = Session.builder.configs(connection_params).create()
```

Finally, create a `Root` object by passing in your `session` object to the `Root` constructor. Run the cell.

```py
root = Root(session)
```

And that's it! By running these four cells, we're now ready to use the Snowflake Python API.

<!-- ------------------------ -->
## Create a database, schema, and table
Duration: 5

Let's use our `root` object to create a database, schema, and table in your Snowflake account.

Create a database by running the following cell in the notebook:

```py
database = root.databases.create(Database(name="PYTHON_API_DB"), mode="orreplace")
```

This line of code creates a database in your account called `PYTHON_API_DB`, and is functionally equivalent to the SQL command `CREATE OR REPLACE DATABASE PYTHON_API_DB;`. This line of code follows a common pattern for managing objects in Snowflake. Let's examine this line of code in a bit more detail:

* `root.databases.create()` is used to create a database in Snowflake. It accepts two arguments, a `Database` object and a mode.

* We pass in a `Database` object with `Database(name="PYTHON_API_DB")`, and set the name of the database using the `name` argument. Recall that we imported `Database` on line 3 of the notebook.

* We specify the creation mode by passing in the `mode` argument. In this case, we set it to `orreplace`, but other valid values are `ifnotexists` (functionally equivalent to `CREATE IF NOT EXISTS` in SQL). If a mode is not specified, the default value will be `errorifexists`, which means an exception will be raised if the object already exists in Snowflake.

* We'll manage the database programmatically by storing a reference to the database in an object we created called `database`.

Navigate back to the databases section of your Snowflake account. If successful, you should see the **PYTHON_API_DB** database.

![database](./assets/python_api_db.png)

Next, create a schema and table in that schema by running the following cells:

```py
schema = database.schemas.create(Schema(name="PYTHON_API_SCHEMA"), mode="orreplace")
```

```py
table = schema.tables.create(Table(
        name="PYTHON_API_TABLE", 
        columns=[TableColumn("TEMPERATURE", "int", nullable=False), TableColumn("LOCATION", "string")],
    ), 
    mode="orreplace")
```

The code in both of these cells should look and feel familiar. They follow the pattern you saw in the cell that created the `PYTHON_API_DB` database. The first cell creates a schema in the database created earlier (note `.schemas.create()` is called on the `database` object from earlier). The next cell creates a table in that schema, with two columns and their data types specified - `TEMPERATURE` as `int` and `LOCATION` as `string`.

After running these two cells, navigate back to your Snowflake account and confirm that the objects were created.

![schema and table](./assets/db_schema_table.png)


<!-- ------------------------ -->
## Retrieve object data
Duration: 5

Let's cover a couple of ways to retrieve metadata about an object in Snowflake. Run the following cell:

```py
table_details = table.fetch()
```

`fetch()` returns a `TableModel` object. We can then call `.to_dict()` on the resulting object to view information about the object. Run the next cell:

```py
table_details.to_dict()
```

In the notebook, you should see a dictionary printed that contains metadata about the **PYTHON_API_TABLE**  table.

```py
{'name': 'PYTHON_API_TABLE',
 'kind': 'TABLE',
 'enable_schema_evolution': False,
 'change_tracking': False,
 'comment': '',
 'created_on': datetime.datetime(2023, 12, 1, 19, 37, 29, 766000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600))),
 'database_name': 'PYTHON_API_DB',
 'schema_name': 'PYTHON_API_SCHEMA',
 'rows': 0,
 'bytes': 0,
 'owner': 'ACCOUNTADMIN',
 'automatic_clustering': False,
 'search_optimization': False,
 'owner_role_type': 'ROLE'}
```

Note, however, that some information about the table isn't included, namely column information. To include column information, we'll pass in the `deep` argument to the `fetch()` method and set it to `True`. Run the following cells:

```py
table_details_full = table.fetch(deep=True)
```

```py
table_details_full.to_dict()
```

Take a took at the dictionary:

```py
{'name': 'PYTHON_API_TABLE',
 'kind': 'TABLE',
 'enable_schema_evolution': False,
 'change_tracking': False,
 'comment': '',
 'created_on': datetime.datetime(2023, 12, 1, 19, 37, 29, 766000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600))),
 'database_name': 'PYTHON_API_DB',
 'schema_name': 'PYTHON_API_SCHEMA',
 'rows': 0,
 'bytes': 0,
 'owner': 'ACCOUNTADMIN',
 'automatic_clustering': False,
 'search_optimization': False,
 'owner_role_type': 'ROLE'}
{'name': 'PYTHON_API_TABLE',
 'kind': 'TABLE',
 'enable_schema_evolution': False,
 'change_tracking': False,
 'columns': [{'name': 'TEMPERATURE',
   'datatype': 'NUMBER',
   'nullable': False,
   'identity': False},
  {'name': 'LOCATION',
   'datatype': 'TEXT',
   'nullable': True,
   'identity': False}],
 'constraints': [],
 'comment': '',
 'created_on': datetime.datetime(2023, 12, 4, 19, 22, 11, 576000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600))),
 'database_name': 'PYTHON_API_DB',
 'schema_name': 'PYTHON_API_SCHEMA',
 'rows': 0,
 'bytes': 0,
 'owner': 'ACCOUNTADMIN',
 'automatic_clustering': False,
 'search_optimization': False,
 'owner_role_type': 'ROLE'}
```

Note how the dictionary now contains column information in `columns`, as well as constraints on the table (in this case, there are no constraints on the table, so the value of `constraints` is an empty array).

Object metadata is useful when building business logic in your application. For example, you could imagine building logic that executes depending on certain information about an object. `fetch()` would be helpful in retrieving object metadata in such scenarios.

<!-- ------------------------ -->
## Programmatically add a column to a table
Duration: 5

Let's take a look at how you might programmatically add a column to a table. Let's add a new column to the **PYTHON_API_TABLE** table. Currently, it has two columns, `TEMPERATURE` and `LOCATION`.

Run the following cell:

```py
table_details_full.columns.append(TableColumn(name="ELEVATION", datatype="int", nullable=False, constraints=[PrimaryKey()]))
```

In this line of code, we define a new column (called `ELEVATION`), the column's data type, indicates that it is not nullable, and define it as the table's primary key. 

Note, however, that this line of code does not create the column (you can confirm this by navigating to Snowflake and inspecting the table after running the cell). Instead, this column definition is appended to the array that represents the table's columns in the TableModel. To view this array, take a look at the value of `columns` in the previous step.

To modify the table and add the column, run the next cell:

```py
table.create_or_update(table_details_full)
```

In this line, we call `create_or_update()` on the object representing **PYTHON_API_TABLE**  and pass in the  updated value of `table_details_full`. This line adds the `ELEVATION` column to **PYTHON_API_TABLE**. To quickly confirm, run the following cell:

```py
table.fetch(deep=True).to_dict()
```

This should be the output:

```py
{'name': 'PYTHON_API_TABLE',
 'kind': 'TABLE',
 'enable_schema_evolution': False,
 'change_tracking': False,
 'comment': '',
 'created_on': datetime.datetime(2023, 12, 1, 19, 37, 29, 766000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600))),
 'database_name': 'PYTHON_API_DB',
 'schema_name': 'PYTHON_API_SCHEMA',
 'rows': 0,
 'bytes': 0,
 'owner': 'ACCOUNTADMIN',
 'automatic_clustering': False,
 'search_optimization': False,
 'owner_role_type': 'ROLE'}
{'name': 'PYTHON_API_TABLE',
 'kind': 'TABLE',
 'enable_schema_evolution': False,
 'change_tracking': False,
 'columns': [{'name': 'TEMPERATURE',
   'datatype': 'NUMBER',
   'nullable': False,
   'identity': False},
  {'name': 'LOCATION',
   'datatype': 'TEXT',
   'nullable': True,
   'identity': False}],
 'constraints': [],
 'comment': '',
 'created_on': datetime.datetime(2023, 12, 4, 19, 22, 11, 576000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600))),
 'database_name': 'PYTHON_API_DB',
 'schema_name': 'PYTHON_API_SCHEMA',
 'rows': 0,
 'bytes': 0,
 'owner': 'ACCOUNTADMIN',
 'automatic_clustering': False,
 'search_optimization': False,
 'owner_role_type': 'ROLE'}
{'name': 'PYTHON_API_TABLE',
 'kind': 'TABLE',
 'enable_schema_evolution': False,
 'change_tracking': False,
 'columns': [{'name': 'TEMPERATURE',
   'datatype': 'NUMBER',
   'nullable': False,
   'identity': False},
  {'name': 'LOCATION',
   'datatype': 'TEXT',
   'nullable': True,
   'identity': False},
  {'name': 'ELEVATION',
   'datatype': 'NUMBER',
   'nullable': False,
   'identity': False}],
 'constraints': [{'name': 'SYS_CONSTRAINT_e9b4b75b-a336-4616-8d94-3266e5846562',
   'column_names': ['ELEVATION'],
   'constraint_type': 'PRIMARY KEY'}],
 'comment': '',
 'created_on': datetime.datetime(2023, 12, 4, 19, 22, 11, 576000, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=57600))),
 'database_name': 'PYTHON_API_DB',
 'schema_name': 'PYTHON_API_SCHEMA',
 'rows': 0,
 'bytes': 0,
 'owner': 'ACCOUNTADMIN',
 'automatic_clustering': False,
 'search_optimization': False,
 'owner_role_type': 'ROLE'}
```

Take a look at the value of `columns`, as well as the value of `constraints`, which now includes the `ELEVATION` column.

Finally, visually confirm by navigating to your Snowflake account and inspecting the table.

![add_column](./assets/add_column.png)



<!-- ------------------------ -->
## Create, suspend, and delete a warehouse
Duration: 5

You can also manage warehouses with the Snowflake Python API. Let's use the API to create, suspend, and delete a warehouse.

Run the following cell:

```py
warehouses = root.warehouses
```

Calling the `.warehouses` property on our `root` returns the collection of warehouses associated with our session. We'll manage warehouses in our session using the resulting `warehouses` object.

Run the next cell:

```py
python_api_wh = Warehouse(
    name="PYTHON_API_WH",
    warehouse_size="SMALL",
    auto_suspend=500,
)

warehouse = warehouses.create(python_api_wh)
```

In this cell, we define a new warehouse by instantiating `Warehouse` and specifying the warehouse's name, size, and auto suspend policy. The auto suspend timeout is in units of seconds. In this case, the warehouse will suspend after 8.33 minutes of inactivity. 

We then create the warehouse by calling `create()` on our warehouse collection. We store the reference in the resulting `warehouse_ref` object. Navigate to your Snowflake account and confirm that the warehouse was created.

![create warehouse](./assets/create_wh.png)

To retrieve information about the warehouse, run the next cell:

```py
warehouse_details = warehouse.fetch()
warehouse_details.to_dict()
```

The code in this cell should look familiar, as it follows the same patterns we used to fetch table data in a previous step. The output should be:

```py
{'name': 'PYTHON_API_WH',
 'max_cluster_count': 1,
 'min_cluster_count': 1,
 'scaling_policy': 'STANDARD',
 'auto_suspend': 500,
 'auto_resume': 'false',
 'resource_monitor': 'null',
 'comment': '',
 'enable_query_acceleration': 'false',
 'query_acceleration_max_scale_factor': 8,
 'type': 'STANDARD',
 'size': 'Small',
 'tag': None}
```

If we had several warehouses in our session, we could use the API to iterate through them or to search for a specific warehouse. Run the next cell:

```py
warehouse_list = warehouses.iter(like="PYTHON_API_WH")
result = next(warehouse_list)
result.to_dict()
```

In this cell, we call `iter()` on the warehouse collection and pass in the `like` argument, which is used to return any warehouses that has a name matching the string we pass in. In this case, we passed in the name of the warehouse we defined earlier, but this argument is generally a case-insensitive string that functions as a filter, with support for SQL wildcard characters like `%` and `_`. You should see the following output after running the cell, which shows that we successfully returned a matching warehouse:

```py
{'name': 'PYTHON_API_WH',
 'max_cluster_count': 1,
 'min_cluster_count': 1,
 'scaling_policy': 'STANDARD',
 'auto_suspend': 500,
 'auto_resume': 'false',
 'resource_monitor': 'null',
 'comment': '',
 'enable_query_acceleration': 'false',
 'query_acceleration_max_scale_factor': 8,
 'type': 'STANDARD',
 'size': 'Small',
 'tag': None}
```

Let's programmatically modify the warehouse. Run the following cell, which changes the warehouse size to `LARGE`:

```py
warehouse.create_or_update(Warehouse(
    name="PYTHON_API_WH",
    warehouse_size="LARGE",
    auto_suspend=500,
))
```

Confirm that the warehouse size was indeed updated to `LARGE` by running the next cell:

```py
warehouse.fetch().size
```

Navigate to your Snowflake account and confirm the change in warehouse size.

![large warw](./assets/large_wh.png)

Finally, delete the warehouse and close your Snowflake session by running the final cell:

```py
warehouse.delete()
session.close()
```

Navigate once again to your Snowflake account and confirm the deletion of the warehouse.

![delete wh close session](./assets/delete_wh_close_session.png)


<!-- ------------------------ -->
## Conclusion
Duration: 1

Congratulations! In this Quickstart, you learned the fundamentals for managing Snowflake objects using the Snowflake Python API. Bookmark this Quickstart and be sure to come back soon, when the Quickstart will be expanded to include Task, DAG, and Snowpark Container Services management using the Snowflake Python API.

### What we've covered

* Installing the Snowflake Python API
* Creating databases, schemas, and tables
* Retrieving object information
* Programmatically updating an object
* Creating, suspending, and deleting warehouses

### Additional resources

* [Snowflake Documentation: Snowflake Python API](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-python-api/snowflake-python-overview)

* [Snowflake Python API Reference Documentation](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-python-api/reference/0.1.0/index.html)
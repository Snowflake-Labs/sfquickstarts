author: Tomasz Urbaszek, Gilberto Hernandez
summary: Getting Started with Snowflake CLI
id:getting-started-with-snowflake-cli
categories: getting-started
environments: web
status: Draft 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, SQL, Data Engineering, SnowSQL

# Getting Started with Snowflake CLI
<!-- ------------------------ -->
## Overview 
Duration: 2

Snowflake CLI is a command-line interface designed for developers building apps on Snowflake. Using Snowflake CLI, you can manage Snowflake Native Applications, Snowpark functions, stored procedures, and Snowpark Container Services. This guide will show you
how to configure and efficiently use Snowflake CLI.
 

### Prerequisites
- [Video: Introduction to Snowflake](https://www.youtube.com/watch?v=gGPKYGN0VQM)
- [Video: Snowflake Data Loading Basics](https://youtu.be/htLsbrJDUqk?si=vfTjL6JaCdEFdiSG)
- Python 3.8 or later installed on your machine
- Basic knowledge of Snowflake concepts
- You'll need a Snowflake account. You can sign up for a free 30-day trial account here: [https://signup.snowflake.com/](https://signup.snowflake.com/).

### What You’ll Learn
- How to install Snowflake CLI
- How to configure Snowflake CLI
- How to switch between different connections
- How to download and upload files using Snowflake CLI
- How to execute SQL using Snowflake CLI

Ensure your development environment meets the following requirements before proceeding:

[//]: # (### What You’ll Need )

[//]: # (- Local [Browser and OS Requirements]&#40;https://docs.snowflake.com/en/user-guide/setup.html&#41;)

[//]: # (- Download the [Sample Data Files]&#40;https://docs.snowflake.com/en/user-guide/getting-started-tutorial-prerequisites.html#sample-data-files-for-loading&#41;)

[//]: # (### What You’ll Build )

[//]: # (- A connection to cloud host and manage data with SnowSQL.)

<!-- ------------------------ -->
## Install Snowflake CLI
Duration: 6
First, you’ll install the Snowflake CLI, and later you'll configure it to connect to your Snowflake account.

### Create a Snowflake Account

You'll need a Snowflake account. You can sign up for a free 30-day trial account here: [https://signup.snowflake.com/](https://signup.snowflake.com/).

### Access Snowflake’s Web Interface

Navigate to [https://app.snowflake.com/](https://app.snowflake.com/) and log into your Snowflake account.


### Install the Snowflake CLI 

Snowflake CLI can be installed on Linux, Windows, or Mac. To install it, run the following command in a terminal:

```console
pip install snowflake-cli-labs
```

Once it's been successfully installed, run the following command to verify that it was successfully installed:

```bash
snow --help
```

If Snowflake CLI was installed successfully, you should see output similar to the following:

```basb
Usage: snow [OPTIONS] COMMAND [ARGS]...                                                        
                                                                                                
 Snowflake CLI tool for developers.                                                             
                                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────────────────────╮
│ --version                    Shows version of the Snowflake CLI                              │
│ --info                       Shows information about the Snowflake CLI                       │
│ --config-file          FILE  Specifies Snowflake CLI configuration file that should be used  │
│                              [default: None]                                                 │
│ --help         -h            Show this message and exit.                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────╮
│ app         Manages a Snowflake Native App                                                   │
│ connection  Manages connections to Snowflake.                                                │
│ object      Manages Snowflake objects like warehouses and stages                             │
│ snowpark    Manages procedures and functions.                                                │
│ spcs        Manages Snowpark Container Services compute pools, services, image registries,   │
│             and image repositories.                                                          │
│ sql         Executes Snowflake query.                                                        │
│ streamlit   Manages Streamlit in Snowflake.                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```

You may encounter an error like the following:

```bash
╭─ Error ──────────────────────────────────────────────────────────────────────────────────────╮
│ Configuration file /Users/yourusername/.snowflake/config.toml has too wide permissions, run    │
│ `chmod 0600 "/Users/yourusername/.snowflake/config.toml"`                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```

In this case, run `chmod 0600 "/Users/yourusername/.snowflake/config.toml"` in the terminal to update the permissions on the file. After running this command, run `snow --help` again. You should see the output shown earlier in this section.

### Configure connection to Snowflake

Snowflake CLI uses a [configuration file named **config.toml** for storing your Snowflake connections](placeholder) . This file is created automatically when
you run Snowflake CLI for the first time.

You can add your connection details within **config.toml** either manually or by using Snowflake CLI. Let's add a connection using Snowflake CLI.

To add a new connection, run the following:

```bash
snow connection add
```

The command will guide you through defining a connection. You can omit all fields denoted by `[optional]` by pressing "Enter" or "return" on your keyboard.

Here's an example:

```console
Name for this connection: my_connection
Snowflake account name: my_account
Snowflake username: jdoe
Snowflake password [optional]: 
Role for the connection [optional]: 
Warehouse for the connection [optional]: 
Database for the connection [optional]: 
Schema for the connection [optional]: 
Connection host [optional]: 
Connection port [optional]: 
Snowflake region [optional]: 
Authentication method [optional]: 
Path to private key file [optional]: 
```
For more detailed information about configuring connections see DOCS LINK.

### Test connection to Snowflake

To test a connection to Snowflake, run the following command

```bash
snow connection tests --connection my_connection
```

In the example above, we use `my_connection` as the connection name, as it corresponds to the prior example connection. To test your connection, replace `my_connection` with the name of the connection you defined during the connection definition process.

<!-- ------------------------ -->
## Working with connections

Connections are crucial to using Snowflake CLI. In the next step, you'll learn how to efficiently work with connections.

### Default connection

You can define a default Snowflake connection by adding the following at the top of **config.toml**:

```toml
default_connection_name = "my_connection"
```

This is the connection that will be used by default if you do not specify a connection name when using the `-c` or `--connection` flag with Snowflake CLI.

You can also set a default connection directly from the terminal:

```bash
snow connection set-default <connection-name>
```

Running `set-default` will update your `config.toml` file to use the specified connection as the default connection. This command is incredibly convenient if you work across multiple Snowflake accounts.

### Using multiple connections

By default, Snowflake CLI commands operate within context of a specified connection. The only required fields in a named connection in **config.toml** are `user` and `account`, however, many Snowflake CLI commands require `database`, `schema`, or `warehouse` to be set in order for a command to be successful. For this reason, it's convenient to set these fields in your named connections:

```toml
[connections.my_connection]
user = "jdoe"
account = "my_account"
database = "jdoe_db"
warehouse = "xs"
```

This is especially recommended if you usually work with a particular context (i.e., a single database, dedicated warehouse, or role).

If you switch your Snowflake context often(for example, when using different roles), it's good practice to define several connections that each correspond to a specific context, like so:

```toml
[connections.admin_connection]
user = "jdoe"
account = "my_account"
role = "accountadmin"

[connections.eng_connection]
user = "jdoe"
account = "my_account"
role = "eng_ops_rl"
```

In such cases, switching between multiple connections can be easily done by using the `snow connection set-default` command shown previously.

### Overriding connection details

There are plenty of use cases where you may want to override connection details without editing **config.toml**. You can do this in one of the following ways:

1. Using connection flags in CLI commands
2. Using environment variables

#### Using CLI flags

All commands that require an established connection to Snowflake support the following flags:

```console
╭─ Connection configuration ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --connection,--environment  -c      TEXT  Name of the connection, as defined in your `config.toml`. Default: `default`.                                                                                 │
│ --account,--accountname             TEXT  Name assigned to your Snowflake account. Overrides the value specified for the connection.                                                                    │
│ --user,--username                   TEXT  Username to connect to Snowflake. Overrides the value specified for the connection.                                                                           │
│ --password                          TEXT  Snowflake password. Overrides the value specified for the connection.                                                                                         │
│ --authenticator                     TEXT  Snowflake authenticator. Overrides the value specified for the connection.                                                                                    │
│ --private-key-path                  TEXT  Snowflake private key path. Overrides the value specified for the connection.                                                                                 │
│ --database,--dbname                 TEXT  Database to use. Overrides the value specified for the connection.                                                                                            │
│ --schema,--schemaname               TEXT  Database schema to use. Overrides the value specified for the connection.                                                                                     │
│ --role,--rolename                   TEXT  Role to use. Overrides the value specified for the connection.                                                                                                │
│ --warehouse                         TEXT  Warehouse to use. Overrides the value specified for the connection.                                                                                           │
│ --temporary-connection      -x            Uses connection defined with command line parameters, instead of one defined in config                                                                        │
│ --mfa-passcode                      TEXT  Token to use for multi-factor authentication (MFA)                                                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

You can access this list by running any Snowflake CLI command with `--help`.

Specifying a connection detail using cli flag always take precedence over any other source. (?)

#### Using environment variables

Another option for overriding connection details is to use environment variables. This option is recommended for passwords or any other sensitive information, especially if you use Snowflake CLI with external systems (e.g., CI/CD pipelines, etc.)

For every connection field, there are two flags:

1. A generic flag in form of `SNOWFLAKE_[KEY]`

2. A connection-specific flag in form of `SNOWFLAKE_CONNECTIONS_[CONNECTION_NAME]_[KEY]`

Connection specific flags take precedence over generic flags. Let's take a look at an example, where we test a connection with a role that doesn't exist in that Snowflake environment:

```bash
SNOWFLAKE_ROLE=funny_role snow connection test
```

If the role does not exist, you should see error similar the one below:

```console
╭─ Error ───────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Invalid connection configuration. 250001 (08001): None: Failed to connect to DB: myacc.snowflakecomputing.com:443.    │
│ Role 'FUNNY_ROLE' specified in the connect string does not exist or not authorized. Contact your local system         │
│ administrator, or attempt to login with another role, e.g. PUBLIC.                                                    │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Using temporary connection

In situations where you are unable to add a new connection to **config.toml**, you may specify a temporary connection directly from the command line using the `-x` or `--temporary-connection` flags. These flags allow you to specify connection details inline, like so:


```bash
snow sql -q "SELECT r_value FROM my_table LIMIT 10" -x --account=<account_name> --user=<user_name> --password=<your_password>
```

In the example above, we establish a temporary connection to Snowflake and execute the `SELECT r_value FROM my_table LIMIT 10` SQL statement.

**Note:** If your account does not allow password authentication, use proper authentication using `--authenticator`.

## Using Snowflake CLI to execute SQL commands

Snowflake CLI enables basic execution of SQL. In this step you will learn how to execute ad-hoc queries or
whole SQL files.

**Note:** For advanced SQL use cases it's recommend to use [SnowSQL](LINK).

### The `sql` command

To execute SQL queries using Snowflake CLI you use `snow sql` command. 

**Tip:** Whenever working with a new Snowflake CLI command consider running it first with `--help` to learn 
more about possible usages.

The `snow sql` command allows the following usages:
```console
snow sql --help                
                                                                                                                         
 Usage: snow sql [OPTIONS]                                                                                               
                                                                                                                         
 Executes Snowflake query.                                                                                               
 Query to execute can be specified using query option, filename option (all queries from file will be executed) or via   
 stdin by piping output from other command. For example `cat my.sql | snow sql -i`.                                      
                                                                                                                         
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --query     -q      TEXT  Query to execute. [default: None]                                                           │
│ --filename  -f      FILE  File to execute. [default: None]                                                            │
│ --stdin     -i            Read the query from standard input. Use it when piping input to this command.               │
│ --help      -h            Show this message and exit.                                                                 │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Executing ad-hoc query

To execute an ad-hoc query run the following command:
```bash
snow sql --query "select 1 as a, 2 as b, 3 as c"
```
it will return the following output
```
+-----------+
| A | B | C |
|---+---+---|
| 1 | 2 | 3 |
+-----------+

```

You can execute multiple queries using `--query` parameter. For example run:
```bash
snow sql --query "select 42 as a; select 2 as b"
```

This will return result for each query separately:
```
select 42 as a;
+----+
| A  |
|----|
| 42 |
+----+

select 2 as b
+---+
| B |
|---|
| 2 |
+---+
```

#### Changing output format

There can be situations where you may want to process the query output programmatically. Currently Snowflake CLI 
support only `JSON` output. To get data in the `JSON` format you need to add `--format=JSON` to your commands.

Let's re-run the above examples using JSON format. To do so run the following command:
```bash
snow sql --query "select 1 as a, 2 as b, 3 as c" --format=JSON
```
This will return data as single array (because there's only single query) with rows:
```json
[
  {
    "A": 1,
    "B": 2,
    "C": 3
  }
]
```

Next run the other example with JSON format:
```bash
snow sql --query "select 42 as a; select 2 as b" --format=JSON
```
In this case data will be returned as array of arrays due to executing multiple queries:
```json
[
  [
    {
      "A"  :   42
    }
  ],
  [
    {
      "B"  :   2
    }
  ]
]

```

### Executing query from file

Snowflake CLI allows you also to execute an SQL file. To learn how to do it first let's prepare simple SQL file
by running the following script:

```bash
echo "select 1;" >> test.sql
```

This will create `test.sql` file in you current working directory. To execute this file against Snowflake run:
```bash
snow sql --filename test.sql
```

As a result you should see the following output:
```console
+---+
| 1 |
|---|
| 1 |
+---+
```

## The `snow object` commands

Snowflake CLI offers commands for generic operations like `SHOW`, `DROP` and `DESCRIBE`. Those commands are available
under `snow object` sub-group.

### Prerequisites
For purpose of this tutorial we will create a new database. To do so, you can use `snow sql` command.

To create a new database run the following command:
```bash
snow sql -q "create database snowflake_cli_test"
```

### Listing objects
Snowflake CLI allows you to list existing objects of given type. In this example we will use database as the type.

To list database available to you run:
```bash
snow object list database
```

You can limit the result by specifying `--like` flag, for example running the following command should return only one database:
```bash
snow object list database --like=snowflake_cli_test
```

To check for list of supported objects run `snow object list --help`.


### Describing objects

TODO

### Dropping objects

TODO

## Using Snowflake CLI to work with stages

Snowflake CLI can help you when working with stages. In this step you will learn how to use `snow object stage` commands.

### Prerequisites

Commands in this section requires a `database` and `schema` to be specified in your connection details. If you skipped
creating `snowflake_cli_test` database in previous steps you should create it now by running the following command:
```bash
snow sql -q "create database snowflake_cli_test"
```

After running the command you should see output similar ot this one:
```console
+---------------------------------------------------+
| status                                            |
|---------------------------------------------------|
| Database SNOWFLAKE_CLI_TEST successfully created. |
+---------------------------------------------------+
```

### Creating a stage

You can create a new stage using Snowflake CLI. To do so you run the following command:
```bash
snow object stage create snowflake_cli_test.public.my_stage
```

If the command succeeds you should see the following output:
```console
+----------------------------------------------------+
| key    | value                                     |
|--------+-------------------------------------------|
| status | Stage area MY_STAGE successfully created. |
+----------------------------------------------------+
```

### Uploading file to stage

Now the stage is created you can upload some files from local file system to the stage. First you will have to create
such a file. For purpose of this tutorial run the following command to create an empty file:
```bash
touch data.csv
```

Next, to upload this file to stage run the following commands:
```bash
snow object stage copy data.csv @snowflake_cli_test.public.my_stage
```
Running it should return the following output:
```console
+----------------------------------------------------------------------------------------------------------------+
| source   | target   | source_size | target_size | source_compression | target_compression | status   | message |
|----------+----------+-------------+-------------+--------------------+--------------------+----------+---------|
| data.csv | data.csv | 0           | 16          | NONE               | NONE               | UPLOADED |         |
+----------------------------------------------------------------------------------------------------------------+
```

### Listing stage contents

At this point you should have a stage with a single file on it. To check it you can list the contents of a stage. To do so run:
```bash
snow object stage list @snowflake_cli_test.public.my_stage 
```
After running this command you should see the output like this:
```console
+--------------------------------------------------------------------------------------------+
| name              | size | md5                              | last_modified                |
|-------------------+------+----------------------------------+------------------------------|
| my_stage/data.csv | 16   | beb79a90840ec142a6586b03c2893c77 | Fri, 1 Mar 2024 20:56:24 GMT |
+--------------------------------------------------------------------------------------------+
```

### Downloading a file from stage

Now that you are sure you have at least one file on stage you can download. Downloading of files is done by using 
the same `snow object stage copy` command. Only this time you will replace the order of arguments.

To download the file from stage to current working directory run the following command:
```bash
snow object stage copy @snowflake_cli_test.public.my_stage/data.csv .
```
This command should complete with output similar to this one:
```console
+----------------------------------------+
| file     | size | status     | message |
|----------+------+------------+---------|
| data.csv | 0    | DOWNLOADED |         |
+----------------------------------------+
```

### Removing stage

Lastly, you can use Snowflake CLI to remove a stage. This is possible by using `snow object drop` command.

To remove the stage you created for this tutorial run:
```bash
snow object drop stage snowflake_cli_test.public.my_stage
```
In result, you should see message like this one:
```console
+--------------------------------+
| status                         |
|--------------------------------|
| MY_STAGE successfully dropped. |
+--------------------------------+
```





<!-- ------------------------ -->
## Conclusion
Duration: 1

### Use Snowflake CLI for Your Application

### What we've covered
- Snowflake CLI setup
- Connection management in Snowflake CLI
- Uploading data using Snowflake CLI
- Executing SQL using Snowflake CLI
- Managing Snowflake objects using the CLI

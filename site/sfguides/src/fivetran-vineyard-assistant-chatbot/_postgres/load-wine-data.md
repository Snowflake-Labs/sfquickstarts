# Load the wine dataset into your PostgreSQL database

This page is part of the [Build a RAG-based, GenAI chatbot using Structured Data with Snowflake and Fivetran](https://www.snowflake.com/en/developers/guides/fivetran-vineyard-assistant-chatbot/) guide.

The guide uses a dataset of 743 California wineries. The dataset is stored as a single JSON file in a public Amazon S3 bucket owned by Fivetran:

```
s3://ft-s3-lab-bkt/winedata/california_wine_country_visits_202409021224.json
```

The script `load_wine_data_to_postgres.py` in this folder reads that file over HTTPS (no AWS account or credentials needed) and loads it into a table in your own PostgreSQL database. The SQL file `load_wine_data_to_postgres.sql` does the same with `psql` and no Python, using a copy of the JSON file you download yourself. Both work with any PostgreSQL 12 or later server, including Amazon RDS for PostgreSQL, Cloud SQL for PostgreSQL and Azure Database for PostgreSQL flexible server.

## What the script creates

- Schema `agriculture` (change it with `--schema`)
- Table `agriculture.california_wine_country_visits` with 27 columns. `id` is an integer primary key and every other column is text. Column names are the JSON keys with spaces replaced by underscores, for example `winery_or_vineyard`.
- 743 rows. The script drops and recreates the table each time, so it is safe to run again.

## Before you run it

You need Python 3.8 or later and network access from the machine running the script to your database. A cloud shell (AWS CloudShell, Google Cloud Shell, Azure Cloud Shell) or your laptop both work, as long as that machine's IP address is allowed by your database firewall.

```bash
pip install psycopg2-binary

export PGHOST=<your database host name>
export PGPORT=5432
export PGDATABASE=industry
export PGUSER=<your admin user>
export PGPASSWORD=<your admin password>
export PGSSLMODE=require

python3 load_wine_data_to_postgres.py
```

Expected output:

```
Downloading https://ft-s3-lab-bkt.s3.amazonaws.com/winedata/california_wine_country_visits_202409021224.json
Downloaded 743 records, 27 columns
Loaded 743 rows into agriculture.california_wine_country_visits
```

## Create the read-only user for Fivetran

Fivetran only needs to read the table. Connect to the `industry` database with `psql` (or any SQL client) as your admin user and run the following. Replace the password with your own.

```sql
CREATE USER fivetran WITH PASSWORD '<choose a strong password>';
GRANT CONNECT ON DATABASE industry TO fivetran;
GRANT USAGE ON SCHEMA agriculture TO fivetran;
GRANT SELECT ON ALL TABLES IN SCHEMA agriculture TO fivetran;
```

Check that it worked:

```sql
SELECT count(*) FROM agriculture.california_wine_country_visits;
```

The result should be 743. Now go back to the [PostgreSQL source setup page](postgresql-source.md) and continue with the Fivetran connector steps. Use your own host name, user `fivetran`, your password and database `industry` in Fivetran.

## Clean up

When you finish the guide, delete the database instance in your cloud account so you stop paying for it. 

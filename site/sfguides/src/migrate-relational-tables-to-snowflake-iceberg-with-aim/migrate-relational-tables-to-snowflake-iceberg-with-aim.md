author: Diego Babb Jimenez
id: migrate-relational-tables-to-snowflake-iceberg-with-aim
language: en
summary: Migrate a relational table to a new Snowflake-managed Iceberg table with AIM Data Migration and Validation.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/migrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Migrate Relational Tables to Snowflake Iceberg with AIM
<!-- ------------------------ -->
## Overview

This guide loads a relational SQL Server table into a **new Snowflake-managed Iceberg table** with AIM Data Migration and Validation. Snowflake owns the catalog. The extract writes Parquet to a stage, and the orchestrator creates the Iceberg table and registers those files.

The worked path is SQL Server, spec **v2**, storage mode **compatible**, and load mode **ADD_FILES_COPY**. The same wizard covers Redshift and Teradata. v3 is a format-version choice on this path. With `ADD_FILES_COPY`, v2 and v3 use the same column types.

This guide creates a new table from a relational source. Adopting an existing Iceberg table, `storageMode` values other than `compatible`, and incremental sync are outside this guide.

### Prerequisites

- Familiarity with Snowflake SQL.
- A SQL Server database you can read, or a Redshift or Teradata warehouse if you follow the source table later in the guide.
- Permission to create an external stage in Snowflake, and either a commercial AWS or Azure account (for Snowflake-managed storage) or an external volume you can grant.

### What You'll Learn

- The answers the AIM plugin expects for a Snowflake-managed Iceberg target.
- Which extract each source offers, and which extracts can use `FULL_INGEST`.
- Why clocks and semi-structured values land as `VARCHAR` on `ADD_FILES_COPY`.
- How to confirm the table, the row count, and the column types after the run.

### What You'll Need

- A Snowflake account. [Sign up](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) if you need one.
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/introduction/introduction), [SnowConvert AI CLI](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README), and [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).
- The SQL in this guide's `assets/` folder.

### What You'll Build

A three-row `Sales.Orders` table in SQL Server, loaded into `ICEBERG_LAB.PUBLIC.ORDERS` as a Snowflake-managed Iceberg table. `OrderId` and `Amount` stay numeric. `OrderTs` lands as `VARCHAR`.

## Prepare the Source

On the SQL Server instance you will register with SnowConvert AI, create `IcebergLab.Sales.Orders`. The same script is in [`assets/sqlserver-orders.sql`](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/migrate-relational-tables-to-snowflake-iceberg-with-aim/assets/sqlserver-orders.sql).

```sql
CREATE DATABASE IcebergLab;
GO
USE IcebergLab;
GO
CREATE SCHEMA Sales;
GO
IF OBJECT_ID('Sales.Orders') IS NOT NULL
    DROP TABLE Sales.Orders;
GO
CREATE TABLE Sales.Orders (
    OrderId INT NOT NULL PRIMARY KEY,
    OrderTs DATETIME2(6) NOT NULL,
    Amount  DECIMAL(10, 2) NOT NULL,
    Notes   NVARCHAR(200) NULL
);
GO
INSERT INTO Sales.Orders (OrderId, OrderTs, Amount, Notes) VALUES
    (1, '2024-03-15T14:30:00', 19.50, 'first order'),
    (2, '2024-06-01T09:00:00', 42.00, NULL),
    (3, '2024-11-20T18:45:00',  7.25, 'gift wrap');
GO
```

The table has three rows:

| OrderId | OrderTs | Amount | Notes |
| --- | --- | --- | --- |
| 1 | 2024-03-15 14:30:00 | 19.50 | first order |
| 2 | 2024-06-01 09:00:00 | 42.00 | |
| 3 | 2024-11-20 18:45:00 | 7.25 | gift wrap |

`OrderTs` is `DATETIME2`. On this load mode it becomes text in Snowflake, which is the check at the end of the guide.

Register the instance and confirm the connection:

```bash
scai connection add-sql-server
scai connection test -l sqlserver -s <YOUR_SQL_SERVER_CONNECTION_NAME>
```

A `Status: Success` row means the plugin can read the table. This guide uses the connection name `iceberglab`.

## Prepare Snowflake

Create `ICEBERG_LAB` and an external stage named `ICEBERG_LAB.PUBLIC.EXTRACT_STAGE`. Replace the placeholders. The same script, including the optional customer-volume block, is in [`assets/snowflake-setup.sql`](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/migrate-relational-tables-to-snowflake-iceberg-with-aim/assets/snowflake-setup.sql).

```sql
CREATE DATABASE IF NOT EXISTS ICEBERG_LAB;
CREATE SCHEMA IF NOT EXISTS ICEBERG_LAB.PUBLIC;

CREATE STORAGE INTEGRATION IF NOT EXISTS ICEBERG_LAB_EXTRACT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = '<IAM_ROLE_ARN>'
  STORAGE_ALLOWED_LOCATIONS = ('<EXTRACT_URL>');

CREATE STAGE IF NOT EXISTS ICEBERG_LAB.PUBLIC.EXTRACT_STAGE
  URL = '<EXTRACT_URL>'
  STORAGE_INTEGRATION = ICEBERG_LAB_EXTRACT;
```

After `DESCRIBE STORAGE INTEGRATION ICEBERG_LAB_EXTRACT`, put `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID` on the IAM trust policy. Use `STORAGE_PROVIDER = 'AZURE'` and the Azure storage parameters when the extract lands in Blob.

The stage URL and the path the extract writes must be the same bucket or container and the same prefix. A stage that points somewhere else can finish the workflow with **zero rows**. The status still says finished, because the orchestrator listed the stage and found no files.

Add the Snowflake connection the CLI will use, with a warehouse on it. The orchestrator uses that warehouse for the load.

```bash
snow connection test --connection <YOUR_SNOWFLAKE_CONNECTION_NAME>
```

### Where the Iceberg Table Lives

Pick one. The extract stage is required either way.

| | Customer volume | Snowflake storage |
| --- | --- | --- |
| `externalVolume` | The volume name | `SNOWFLAKE_MANAGED` |
| `baseLocationPrefix` | Required. Each table is placed under this prefix. | Omit it. |
| Accounts | Any account that can use an external volume | AWS and Azure commercial |

For a customer volume, create the volume, read `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID` from `DESCRIBE EXTERNAL VOLUME`, put both on the IAM trust policy, then grant usage:

```sql
GRANT USAGE ON EXTERNAL VOLUME <VOLUME_NAME> TO ROLE <MIGRATION_ROLE>;
GRANT CREATE ICEBERG TABLE ON SCHEMA ICEBERG_LAB.PUBLIC TO ROLE <MIGRATION_ROLE>;
```

`SELECT SYSTEM$VERIFY_EXTERNAL_VOLUME('<VOLUME_NAME>');` should succeed before you start the load. Volume setup is documented in [CREATE EXTERNAL VOLUME](https://docs.snowflake.com/en/sql-reference/sql/create-external-volume).

This lab uses `SNOWFLAKE_MANAGED` so there is no volume to grant. Skip that grant, and leave `baseLocationPrefix` unset.

## Drive the Load from Cortex Code

From an empty project directory:

```bash
cortex
```

Send one prompt. Name the connection, the stage, the spec, and the load mode so the wizard does not have to guess.

> ```
> Migrate IcebergLab.Sales.Orders from the SQL Server connection `iceberglab`
> to a new Snowflake-managed Iceberg table in ICEBERG_LAB.PUBLIC.
> Use a full load. Target type Iceberg, spec v2, storage mode compatible,
> load mode ADD_FILES_COPY, external volume SNOWFLAKE_MANAGED.
> Extract with CETAS. The external stage is ICEBERG_LAB.PUBLIC.EXTRACT_STAGE
> and it is the same path CETAS writes. Do not deploy this table as a native
> table first. After the load, show me the row count and stop before dependents.
> ```

Answer the plugin in this order.

| Question | Answer |
| --- | --- |
| Migration type inside the table? | **Full**. Preliminary loads a subset and is useful on a large source. Iceberg runs are full loads, so choose Full even when Incremental is listed. |
| Target table type? | **Iceberg** |
| Iceberg spec? | **v2**. Choose v3 only when the table must be format version 3. |
| SQL Server extraction? | **CETAS to Azure Blob**. Cloud-direct object storage is the other Iceberg option. BCP and ODBC are not offered. |
| Load mechanism? | **ADD_FILES_COPY** |

When the workflow is shown, confirm three things before you proceed:

- `tableType` is `iceberg` and `catalog` is `SNOWFLAKE`.
- `storageMode` is `compatible`, `icebergSpec` is `v2`, `loadMode` is `ADD_FILES_COPY`, and `externalVolume` is `SNOWFLAKE_MANAGED`. There is no `baseLocationPrefix`.
- `extraction.strategy` is `cet_as` and `extraction.externalStage` is `ICEBERG_LAB.PUBLIC.EXTRACT_STAGE`.

`columnNamesToPartitionBy` is the column the extract uses to split work, often `OrderId`. That split is the extract. The Iceberg table is created without a `PARTITION BY` clause.

The shape the plugin writes looks like this:

```yaml
defaultTableConfiguration:
  source:
    databaseName: IcebergLab
    schemaName: Sales
  target:
    databaseName: ICEBERG_LAB
    schemaName: PUBLIC
    tableType: iceberg
    icebergConfig:
      catalog: SNOWFLAKE
      externalVolume: SNOWFLAKE_MANAGED
      icebergSpec: v2
      storageMode: compatible
      loadMode: ADD_FILES_COPY
  extraction:
    strategy: cet_as
    externalStage: ICEBERG_LAB.PUBLIC.EXTRACT_STAGE
tables:
  - source: { tableName: Orders }
    target: { tableName: ORDERS }
    columnNamesToPartitionBy: ["OrderId"]
```

Leave these keys off the Iceberg config: `sourceDataStage`, `catalogTableName`, `catalogSync`, `externalEngineAccess`, and `postLoadOptimize`. A customer volume uses the same block with `externalVolume` set to the volume name and `baseLocationPrefix` set, for example `migrations/sqlserver`.

Proceed. The orchestrator creates `ICEBERG_LAB.PUBLIC.ORDERS` during the load. If that name already exists, the run stops. Drop the table before you run again.

## Confirm the Table

When the workflow status is finished, check the rows and the types.

```sql
SELECT COUNT(*) FROM ICEBERG_LAB.PUBLIC.ORDERS;

SELECT COLUMN_NAME, DATA_TYPE
FROM ICEBERG_LAB.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'PUBLIC'
  AND TABLE_NAME = 'ORDERS'
ORDER BY ORDINAL_POSITION;

SELECT GET_DDL('TABLE', 'ICEBERG_LAB.PUBLIC.ORDERS');
```

You want:

- `COUNT(*)` = 3. Zero means the stage URL and the CETAS path differ.
- `ORDERID` numeric, `AMOUNT` numeric, `ORDER_TS` (or `ORDERTS`) as `VARCHAR` or `TEXT`.
- `GET_DDL` shows a Snowflake-managed Iceberg table, `CATALOG = 'SNOWFLAKE'`, `EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'`, and no `PARTITION BY`.

A zero-row finish is a miss, even when the workflow says finished. Compare the stage URL with the path CETAS wrote, then drop the empty table and run again.

Deploy views, functions, and procedures that depend on this table only after the count matches.

## What Lands as What

`ADD_FILES_COPY` registers the Parquet as it was written. A column whose file type does not match the table is rejected. The compatible profile keeps the types the files can carry, and stores the rest as text.

| Source type | Iceberg column on ADD_FILES_COPY, v2 or v3 |
| --- | --- |
| Integer, decimal, boolean, float, date, string, binary | Stays typed |
| `TIME`, `TIMESTAMP`, `DATETIME`, `DATETIME2` | `VARCHAR` |
| JSON, `SUPER`, array, XML, geography, geometry | `VARCHAR` |

Redshift timestamp columns are unloaded as UTC ISO text on this path. A native timestamp UNLOAD can wrap values outside about 1677–2262, so the compatible profile does not load them as timestamps.

`FULL_INGEST` rewrites the files. On **v3** only, clocks and geo become real types at scale 6 (`TIMESTAMP_NTZ(6)`, `TIMESTAMP_LTZ(6)` for timestamps with an offset, `TIME(6)`, `GEOGRAPHY`, `GEOMETRY`). Scale 9 cannot represent years before 1677. JSON, `SUPER`, arrays, and XML stay `VARCHAR`. A v2 `FULL_INGEST` does not retype clocks.

`FULL_INGEST` is accepted for these extracts:

| Source | Extracts that allow FULL_INGEST | Extracts that stay on ADD_FILES_COPY |
| --- | --- | --- |
| Redshift | UNLOAD to S3 | Cloud-direct |
| SQL Server | CETAS, cloud-direct | BCP is not offered for Iceberg |
| Teradata | WRITE_NOS | Cloud-direct. UNLOAD is not the Teradata extract. |

## Other Sources

The wizard asks for the target type before the extract, and only for Redshift, SQL Server, and Teradata. The stage rule is the same on all three: the stage is the path the extract writes.

| Source | Extract to choose | Load modes |
| --- | --- | --- |
| Redshift | UNLOAD to S3 | `ADD_FILES_COPY`, or `FULL_INGEST` on UNLOAD |
| SQL Server | CETAS to Azure Blob | Both modes. Cloud-direct also allows both. |
| Teradata | WRITE_NOS to cloud | `ADD_FILES_COPY`, or `FULL_INGEST` on WRITE_NOS |

## What Stops a Run

Fix the config. Running the same workflow again does not clear these.

- The target name already exists.
- The Parquet footer does not match the DDL, or the column-name case does not match. `ADD_FILES_COPY` is case-sensitive.
- `FULL_INGEST` is paired with Redshift or Teradata cloud-direct.
- The external volume trust policy is missing Snowflake's IAM user or external ID. `SNOWFLAKE_MANAGED` skips this check. It fails on GCP, government, and China regions.
- SQL Server BCP was selected. Iceberg does not offer it.

A stage that does not match the extract path is the zero-row case in [Confirm the Table](#confirm-the-table).

## After the Load

The table is created without a `PARTITION BY` clause. `columnNamesToPartitionBy` only splits the extract. To partition the Iceberg table, copy it into a new table and use an Iceberg transform such as `MONTH` or `DAY` on a timestamp column. A raw timestamp creates one partition per distinct value.

On this lab the clock is `VARCHAR`, so give the new table a real timestamp column before you partition it. On a v3 `FULL_INGEST` load the clock is already a timestamp, and `PARTITION BY (MONTH(order_ts))` applies directly. Syntax: [CREATE ICEBERG TABLE](https://docs.snowflake.com/en/sql-reference/sql/create-iceberg-table-snowflake).

## Conclusion

You loaded a relational SQL Server table into a new Snowflake-managed Iceberg table with AIM. The plugin kept the catalog as `SNOWFLAKE`, the storage mode as `compatible`, and the files as they were written. The timestamp landed as `VARCHAR` because this was `ADD_FILES_COPY`.

### What You Learned

- How to answer the AIM data-migration wizard for an Iceberg target: full load, spec v2 or v3, a cloud extract, and `ADD_FILES_COPY` or `FULL_INGEST`.
- How Snowflake-managed storage differs from a customer external volume, and why the extract stage still has to match the write path.
- Which types stay typed, and which become `VARCHAR`, on the compatible profile.
- How to read a finished workflow that loaded zero rows.

### Related Resources

- [SnowConvert AI CLI](https://docs.snowflake.com/en/migrations/snowconvert-docs/general/user-guide/snowconvert/command-line-interface/README)
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [CREATE EXTERNAL VOLUME](https://docs.snowflake.com/en/sql-reference/sql/create-external-volume)
- [CREATE ICEBERG TABLE (Snowflake as the catalog)](https://docs.snowflake.com/en/sql-reference/sql/create-iceberg-table-snowflake)
- [Snowflake AIM end-to-end SQL Server and SSIS migration](/en/developers/guides/snowflake-aim-e2e-ssis-migration/) — the same plugin, with native tables and an SSIS package.

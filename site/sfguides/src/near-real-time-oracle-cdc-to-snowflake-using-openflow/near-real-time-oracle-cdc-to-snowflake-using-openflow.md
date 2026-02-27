author: Vino Duraisamy, Sharvan Kumar
id: near-real-time-oracle-cdc-to-snowflake-using-openflow
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Learn how to set up near real-time Change Data Capture (CDC) replication from Oracle Database to Snowflake using the Snowflake Openflow Connector for Oracle.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Set Up Near Real-Time Oracle CDC to Snowflake Using Openflow
<!-- ------------------------ -->
## Overview

The Snowflake Openflow Connector for Oracle uses Oracle's native XStream API to capture committed inserts, updates, and deletes directly from the database's redo logs. Changes are streamed into Snowflake target tables using Snowpipe Streaming, delivering end-to-end latency in seconds with minimal impact on the source OLTP system.

This guide walks you through the complete setup process, from configuring the Oracle database for XStream to deploying the Openflow connector in Snowflake.

### What You'll Learn
- How to configure Oracle Database for XStream-based CDC
- How to create XStream users, privileges, and outbound servers
- How to set up an Openflow deployment in Snowflake
- How to configure and start the Oracle CDC connector
- How to verify and monitor the replication pipeline

### What You'll Build
By the end of this guide, you'll have a working near real-time CDC pipeline that streams changes from Oracle Database into Snowflake using Openflow.

### Prerequisites
- A [Snowflake account](https://signup.snowflake.com/) in an AWS or Azure commercial region
- An Oracle Database (12c R2, 18c, 19c, 21c, 23ai, or 26ai) with SYSDBA access
- Network connectivity between Snowflake (SPCS) and the Oracle database (port 1521)
- Snowflake `ACCOUNTADMIN` or a role with Openflow admin privileges

<!-- ------------------------ -->
## Architecture

The Openflow Connector reads logical change records (LCRs) directly from the XStream outbound server queue in near real time. These change events are then streamed into Snowflake target tables using Snowpipe Streaming.

```
Oracle DB (XStream Outbound Server)
    |
    | Logical Change Records (LCRs)
    v
Openflow (Apache NiFi-based runtime on SPCS)
    |
    | Snowpipe Streaming
    v
Snowflake Target Tables
```

| Component | Description |
|-----------|-------------|
| **XStream Outbound Server** | Captures committed changes from Oracle redo logs |
| **Openflow Runtime** | Apache NiFi-based service running on Snowpark Container Services |
| **Snowpipe Streaming** | Low-latency ingestion into Snowflake target tables |

### Supported Environments

The connector supports Oracle Database running on-premises, on Oracle Exadata, in OCI (VM/Bare Metal), and on AWS RDS Custom for Oracle.

<!-- ------------------------ -->
## Enable ARCHIVELOG Mode

Connect to Oracle as SYSDBA and verify that the database is in `ARCHIVELOG` mode. XStream requires this to read the redo logs.

```sql
sqlplus -L / as sysdba

SELECT log_mode FROM v$database;
```

If the database is not in `ARCHIVELOG` mode, enable it:

```sql
SHUTDOWN IMMEDIATE;
STARTUP MOUNT;
ALTER DATABASE ARCHIVELOG;
ALTER DATABASE OPEN;

SELECT log_mode FROM v$database;
```

> **Note:** Enabling `ARCHIVELOG` mode requires a database restart. Plan accordingly for production systems.

<!-- ------------------------ -->
## Enable GoldenGate and Logging

### Enable GoldenGate Replication

XStream requires GoldenGate replication to be enabled:

```sql
ALTER SYSTEM SET enable_goldengate_replication=TRUE SCOPE=BOTH;
```

### Enable Supplemental Logging

Switch to the root container and enable supplemental logging for all columns:

```sql
ALTER SESSION SET CONTAINER = CDB$ROOT;
ALTER DATABASE ADD SUPPLEMENTAL LOG DATA (ALL) COLUMNS;
```

<!-- ------------------------ -->
## Create XStream Tablespaces

Create tablespaces in both the root container and the pluggable database for the XStream administrator:

```sql
CREATE TABLESPACE xstream_adm_tbs
  DATAFILE '/opt/oracle/oradata/FREE/xstream_adm_tbs.dbf'
  SIZE 25M REUSE AUTOEXTEND ON MAXSIZE UNLIMITED;

ALTER SESSION SET CONTAINER = FREEPDB1;

CREATE TABLESPACE xstream_adm_tbs
  DATAFILE '/opt/oracle/oradata/FREE/FREEPDB1/xstream_adm_tbs.dbf'
  SIZE 25M REUSE AUTOEXTEND ON MAXSIZE UNLIMITED;

ALTER SESSION SET CONTAINER = CDB$ROOT;
```

> **Note:** Replace `FREEPDB1` and file paths with your actual PDB name and Oracle data directory.

<!-- ------------------------ -->
## Create XStream Users

### XStream Administrator

Create a common user (prefixed with `c##`) that will administer XStream:

```sql
CREATE USER c##xstreamadmin IDENTIFIED BY "XStreamAdmin123!"
  DEFAULT TABLESPACE xstream_adm_tbs
  QUOTA UNLIMITED ON xstream_adm_tbs
  CONTAINER=ALL;
```

Grant the required privileges:

```sql
GRANT CREATE SESSION, SET CONTAINER, EXECUTE ANY PROCEDURE, LOGMINING
  TO c##xstreamadmin CONTAINER=ALL;

GRANT XSTREAM_CAPTURE TO c##xstreamadmin CONTAINER=ALL;

GRANT SELECT ANY TABLE TO c##xstreamadmin CONTAINER=ALL;
GRANT FLASHBACK ANY TABLE TO c##xstreamadmin CONTAINER=ALL;
GRANT SELECT ANY TRANSACTION TO c##xstreamadmin CONTAINER=ALL;

BEGIN
    EXECUTE IMMEDIATE 'GRANT XSTREAM_ADMIN TO c##xstreamadmin CONTAINER=ALL';
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('XSTREAM_ADMIN role not available, continuing with XSTREAM_CAPTURE');
END;
/
```

### XStream Connect User

Create the user that the Openflow connector will use to connect:

```sql
CREATE USER c##connectuser IDENTIFIED BY "ConnectUser123!"
  CONTAINER=ALL;

GRANT CREATE SESSION, SELECT_CATALOG_ROLE TO c##connectuser CONTAINER=ALL;
GRANT SELECT ANY TABLE TO c##connectuser CONTAINER=ALL;
GRANT LOCK ANY TABLE TO c##connectuser CONTAINER=ALL;
GRANT SELECT ANY DICTIONARY TO c##connectuser CONTAINER=ALL;
```

<!-- ------------------------ -->
## Create XStream Outbound Server

Create an XStream outbound server that captures changes from the schemas you want to replicate:

```sql
SET SERVEROUTPUT ON;

DECLARE
    tables  DBMS_UTILITY.UNCL_ARRAY;
    schemas DBMS_UTILITY.UNCL_ARRAY;
BEGIN
    tables(1)  := NULL;
    schemas(1) := 'HR';
    schemas(2) := 'CO';

    DBMS_XSTREAM_ADM.CREATE_OUTBOUND(
        server_name           => 'XOUT1',
        table_names           => tables,
        schema_names          => schemas,
        source_container_name => 'FREEPDB1'
    );
END;
/
```

> **Note:** Replace `HR` and `CO` with the schemas you want to replicate.

### Assign Users to the Outbound Server

```sql
BEGIN
    DBMS_XSTREAM_ADM.ALTER_OUTBOUND(
        server_name  => 'XOUT1',
        connect_user => 'c##connectuser');
END;
/

BEGIN
    DBMS_XSTREAM_ADM.ALTER_OUTBOUND(
        server_name  => 'XOUT1',
        capture_user => 'c##xstreamadmin');
END;
/
```

<!-- ------------------------ -->
## Verify Oracle Configuration

Run the following queries to confirm the Oracle database is correctly configured:

```sql
SELECT server_name, status, connect_user, capture_user
FROM dba_xstream_outbound;

SELECT supplemental_log_data_min, supplemental_log_data_pk, supplemental_log_data_all
FROM v$database;

SELECT con_id, username, account_status
FROM cdb_users
WHERE username IN ('C##XSTREAMADMIN', 'C##CONNECTUSER')
ORDER BY con_id;

SELECT name, value FROM v$parameter
WHERE name = 'enable_goldengate_replication';

SELECT CAPTURE_NAME, STATE, TOTAL_MESSAGES_CAPTURED, TOTAL_MESSAGES_ENQUEUED
FROM V$XSTREAM_CAPTURE;
```

| Check | Expected Value |
|-------|---------------|
| Outbound server `status` | `ENABLED` or `ATTACHED` |
| `supplemental_log_data_all` | `YES` |
| User `account_status` | `OPEN` |
| `enable_goldengate_replication` | `TRUE` |

### Connection Parameters

Record these values for use when configuring the Openflow connector:

| Parameter | Value |
|-----------|-------|
| **Host** | `<InstancePublicIp>` or `<InstancePrivateIp>` |
| **Port** | `1521` |
| **Service** | `FREEPDB1` |
| **Username** | `c##connectuser` |
| **Password** | `ConnectUser123!` |
| **XStream Server** | `XOUT1` |

<!-- ------------------------ -->
## Set Up Openflow in Snowflake

### Create the Openflow Admin Role

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS openflow_admin_role;
GRANT ROLE openflow_admin_role TO ROLE ACCOUNTADMIN;

GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE openflow_admin_role;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE openflow_admin_role;
GRANT CREATE DATABASE ON ACCOUNT TO ROLE openflow_admin_role;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE openflow_admin_role;
```

### Create an Openflow Deployment

Navigate to **Snowsight > Data > Openflow** and create a new Openflow - Snowflake Deployment. This provisions the Openflow runtime (NiFi-based) on Snowpark Container Services (SPCS).

For detailed deployment steps, refer to the [Set up Openflow - Snowflake Deployment](https://docs.snowflake.com/en/user-guide/data-integration/openflow/setup-openflow-spcs) documentation.

### Create a Snowflake Role for the Connector

```sql
CREATE ROLE IF NOT EXISTS openflow_oracle_role;

GRANT USAGE ON DATABASE <target_db> TO ROLE openflow_oracle_role;
GRANT USAGE ON SCHEMA <target_db>.<target_schema> TO ROLE openflow_oracle_role;
GRANT CREATE TABLE ON SCHEMA <target_db>.<target_schema> TO ROLE openflow_oracle_role;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA <target_db>.<target_schema>
  TO ROLE openflow_oracle_role;
```

### Configure Network Access

Create a network rule to allow the Openflow runtime to reach the Oracle database:

```sql
CREATE OR REPLACE NETWORK RULE oracle_network_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('<oracle_host>:1521');
```

<!-- ------------------------ -->
## Configure the Oracle Connector

### Open the Openflow UI

Navigate to **Snowsight > Data > Openflow**, select your deployment, and open the Openflow runtime UI.

### Deploy the Connector

1. In the Openflow UI, select **Add Connector**
2. Choose **Openflow Connector for Oracle**

### Configure the Connection

Provide the Oracle connection parameters recorded during the verification step:

| Parameter | Value |
|-----------|-------|
| Host | `<oracle_host_ip_or_dns>` |
| Port | `1521` |
| Service Name | `FREEPDB1` |
| Username | `c##connectuser` |
| Password | `ConnectUser123!` |
| XStream Outbound Server | `XOUT1` |

### Configure the Replication Scope

Select which schemas and tables to replicate:

- **Schemas:** `HR`, `CO` (or whichever schemas you configured in the XStream outbound server)
- **Tables:** Select specific tables or replicate all tables within the selected schemas

### Configure the Snowflake Target

| Parameter | Value |
|-----------|-------|
| Target Database | `<your_target_database>` |
| Target Schema | `<your_target_schema>` |
| Table Naming | Match source table names (default) |

### Start the Connector

1. Enable the connector in the Openflow UI
2. The connector performs an **initial snapshot** (full load) of the selected tables
3. After the snapshot completes, the connector switches to **CDC mode** and streams ongoing changes

<!-- ------------------------ -->
## Verify and Monitor

### Verify Data in Snowflake

```sql
SHOW TABLES IN SCHEMA <target_db>.<target_schema>;

SELECT * FROM <target_db>.<target_schema>.<table_name> LIMIT 10;

SELECT COUNT(*) FROM <target_db>.<target_schema>.<table_name>;
```

### Test CDC Replication

On the Oracle source, insert a test row and verify it appears in Snowflake:

```sql
-- On Oracle
INSERT INTO hr.employees (employee_id, first_name, last_name, email)
VALUES (9999, 'Test', 'User', 'test@example.com');
COMMIT;
```

```sql
-- On Snowflake (should appear within seconds)
SELECT * FROM <target_db>.<target_schema>.employees
WHERE employee_id = 9999;
```

### Monitor the Pipeline

Use the Openflow UI to check connector status, throughput, and error counts. On the Oracle side, verify the capture process:

```sql
SELECT CAPTURE_NAME, STATE, TOTAL_MESSAGES_CAPTURED, TOTAL_MESSAGES_ENQUEUED
FROM V$XSTREAM_CAPTURE;

SELECT server_name, status, connect_user, capture_user
FROM dba_xstream_outbound;
```

<!-- ------------------------ -->
## Troubleshooting

### XStream Outbound Server Not Running

```sql
SELECT server_name, status FROM dba_xstream_outbound;

BEGIN
    DBMS_XSTREAM_ADM.ALTER_OUTBOUND(
        server_name => 'XOUT1',
        status      => 'ENABLED'
    );
END;
/
```

### Capture Process Not Starting

```sql
SELECT capture_name, status FROM dba_capture;

BEGIN
    DBMS_CAPTURE_ADM.START_CAPTURE('XSTREAM_CAPTURE');
END;
/
```

### Supplemental Logging Issues

```sql
SELECT supplemental_log_data_min, supplemental_log_data_pk, supplemental_log_data_all
FROM v$database;

ALTER DATABASE ADD SUPPLEMENTAL LOG DATA;
ALTER DATABASE ADD SUPPLEMENTAL LOG DATA (ALL) COLUMNS;
ALTER DATABASE ADD SUPPLEMENTAL LOG DATA (PRIMARY KEY) COLUMNS;
```

### Network Connectivity

- Ensure the Oracle host and port (1521) are accessible from the Snowflake SPCS compute pool
- Verify the external access integration and network rules are correctly configured
- Test connectivity using the Openflow UI's connection test feature

<!-- ------------------------ -->
## Cleanup

To remove the XStream configuration from Oracle:

```sql
BEGIN
    DBMS_XSTREAM_ADM.DROP_OUTBOUND('XOUT1');
END;
/

DROP USER c##xstreamadmin CASCADE;
DROP USER c##connectuser CASCADE;

ALTER DATABASE DROP SUPPLEMENTAL LOG DATA (ALL) COLUMNS;

ALTER SYSTEM SET enable_goldengate_replication=FALSE SCOPE=BOTH;
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully set up a near real-time CDC pipeline from Oracle Database to Snowflake using the Openflow Connector for Oracle. Changes made in your Oracle source are now captured via XStream and streamed into Snowflake within seconds.

### What You Learned
- **Oracle XStream configuration** - Enabling ARCHIVELOG mode, GoldenGate replication, supplemental logging, and creating XStream users and outbound servers
- **Openflow deployment** - Setting up the Openflow runtime in Snowflake on Snowpark Container Services
- **Connector configuration** - Connecting the Oracle CDC connector to the XStream outbound server and configuring replication scope
- **Verification and monitoring** - Validating data replication and monitoring pipeline health

### Related Resources

Snowflake Documentation:
- [Openflow Overview](https://docs.snowflake.com/en/user-guide/data-integration/openflow/about)
- [Openflow Connectors](https://docs.snowflake.com/en/user-guide/data-integration/openflow/connectors/about-openflow-connectors)
- [Set up Openflow - Snowflake Deployment](https://docs.snowflake.com/en/user-guide/data-integration/openflow/setup-openflow-spcs)
- [Manage Openflow](https://docs.snowflake.com/en/user-guide/data-integration/openflow/manage)
- [Monitor Openflow](https://docs.snowflake.com/en/user-guide/data-integration/openflow/monitor)

Video:
- [How-to Set Up Near Real-Time Oracle CDC to Snowflake using Openflow](https://www.youtube.com/watch?v=nLGnb1VoJuc)

GitHub:
- [Oracle Free 23ai Snowflake Openflow Setup](https://github.com/sharvankumar/oracle-free23-snowflake-openflow) - Oracle XStream setup script and configuration reference

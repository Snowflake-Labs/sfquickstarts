author: Rick Radewagen
id: ask-snowflake-questions-in-slack-with-dot
language: en
summary: Give Dot read-only access to Snowflake with a key-pair service user, describe your tables with comments, and answer data questions in Slack.
categories: snowflake-site:taxonomy/solution-center/certification/community-sourced, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/business-intelligence
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
tags: Business Intelligence, Natural Language Query, Key-Pair Authentication, Service Users, Slack

# Ask Questions About Your Snowflake Data in Slack with Dot
<!-- ------------------------ -->
## Overview

[Dot](https://www.getdot.ai) is an AI data analyst. Business teams ask questions in Slack, Microsoft Teams or the Dot web app. Dot writes the SQL, runs it in your Snowflake account and answers with tables and charts.

In this guide you load a small sales dataset, describe it with Snowflake comments, and give Dot read-only access through a key-pair service user. Then you ask a question in Slack and check Dot's answer with your own SQL.

### Prerequisites
- Basic SQL
- Access to Snowsight with the ACCOUNTADMIN role, or with SYSADMIN and SECURITYADMIN

### What You'll Learn
- How to give an outside tool read-only access with a `TYPE = SERVICE` user and key-pair authentication
- How table and column comments give an AI analyst business context
- How to see and limit the queries and credits a tool uses

### What You'll Need
- A Snowflake account. A [free trial](https://signup.snowflake.com/) works.
- A Dot account where you are an admin. You can [sign up for free](https://app.getdot.ai/register).
- OpenSSL on your computer. It comes with macOS and most Linux distributions.
- Optional: a Slack workspace where you can install apps. Without Slack you can ask in the Dot web app.

### What You'll Build
- A sales dataset in Snowflake with business descriptions
- A read-only Dot connection that answers your team's questions in Slack

<!-- ------------------------ -->
## Load Sample Data

Copy four tables from the TPC-H sample data into a new database and give the columns readable names. Dot skips the shared SNOWFLAKE_SAMPLE_DATA database when it syncs, so you work on a copy.

Open a SQL worksheet in Snowsight and run:

```sql
USE ROLE SYSADMIN;
USE WAREHOUSE COMPUTE_WH; -- or any warehouse you can use

CREATE DATABASE IF NOT EXISTS DOT_DEMO;
CREATE SCHEMA IF NOT EXISTS DOT_DEMO.SALES;
USE SCHEMA DOT_DEMO.SALES;

CREATE OR REPLACE TABLE REGIONS AS
SELECT R_REGIONKEY AS REGION_ID, R_NAME AS REGION_NAME
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION;

CREATE OR REPLACE TABLE NATIONS AS
SELECT N_NATIONKEY AS NATION_ID, N_NAME AS NATION_NAME, N_REGIONKEY AS REGION_ID
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION;

CREATE OR REPLACE TABLE CUSTOMERS AS
SELECT C_CUSTKEY AS CUSTOMER_ID, C_NATIONKEY AS NATION_ID, C_MKTSEGMENT AS MARKET_SEGMENT
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER;

CREATE OR REPLACE TABLE ORDERS AS
SELECT O_ORDERKEY AS ORDER_ID, O_CUSTKEY AS CUSTOMER_ID, O_ORDERDATE AS ORDER_DATE,
       O_ORDERSTATUS AS ORDER_STATUS, O_TOTALPRICE AS ORDER_AMOUNT
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS;
```

If your account has no SNOWFLAKE_SAMPLE_DATA database, create it with ACCOUNTADMIN and run the block above again:

```sql
USE ROLE ACCOUNTADMIN;
CREATE DATABASE SNOWFLAKE_SAMPLE_DATA FROM SHARE SFC_SAMPLES.SAMPLE_DATA;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE PUBLIC;
```

Check the row counts:

```sql
SELECT 'ORDERS' AS table_name, COUNT(*) AS row_count FROM DOT_DEMO.SALES.ORDERS
UNION ALL SELECT 'CUSTOMERS', COUNT(*) FROM DOT_DEMO.SALES.CUSTOMERS
UNION ALL SELECT 'NATIONS', COUNT(*) FROM DOT_DEMO.SALES.NATIONS
UNION ALL SELECT 'REGIONS', COUNT(*) FROM DOT_DEMO.SALES.REGIONS;
```

You should see 1,500,000 orders, 150,000 customers, 25 nations and 5 regions.

<!-- ------------------------ -->
## Describe the Tables

Dot reads table and column comments when it syncs. A comment is the quickest way to tell Dot what a column means and which business rules apply.

```sql
USE ROLE SYSADMIN;
USE SCHEMA DOT_DEMO.SALES;

COMMENT ON TABLE ORDERS IS 'One row per customer order. Revenue is the sum of ORDER_AMOUNT.';
COMMENT ON COLUMN ORDERS.ORDER_AMOUNT IS 'Total value of the order in US dollars';
COMMENT ON COLUMN ORDERS.ORDER_STATUS IS 'F = fulfilled, O = open, P = partially shipped';
COMMENT ON COLUMN ORDERS.CUSTOMER_ID IS 'Joins to CUSTOMERS.CUSTOMER_ID';

COMMENT ON TABLE CUSTOMERS IS 'One row per customer';
COMMENT ON COLUMN CUSTOMERS.NATION_ID IS 'Joins to NATIONS.NATION_ID';
COMMENT ON COLUMN CUSTOMERS.MARKET_SEGMENT IS 'Industry of the customer, for example AUTOMOBILE or BUILDING';

COMMENT ON TABLE NATIONS IS 'Countries where customers are based';
COMMENT ON COLUMN NATIONS.REGION_ID IS 'Joins to REGIONS.REGION_ID';

COMMENT ON TABLE REGIONS IS 'Sales regions: AFRICA, AMERICA, ASIA, EUROPE and MIDDLE EAST';
```

The same works for your own tables. When Dot gets a question wrong, a missing definition is often the cause. Add it as a comment and sync again.

<!-- ------------------------ -->
## Create Warehouse and Role

Give Dot its own warehouse, so you can see and cap what it costs. Then create a role that can only read the SALES schema.

```sql
USE ROLE SYSADMIN;
CREATE WAREHOUSE IF NOT EXISTS DOT_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  STATEMENT_TIMEOUT_IN_SECONDS = 600;

USE ROLE SECURITYADMIN;
CREATE ROLE IF NOT EXISTS DOT_ROLE;
GRANT ROLE DOT_ROLE TO ROLE SYSADMIN; -- keeps the role hierarchy tidy

GRANT USAGE ON WAREHOUSE DOT_WH TO ROLE DOT_ROLE;
GRANT USAGE ON DATABASE DOT_DEMO TO ROLE DOT_ROLE;
GRANT USAGE ON SCHEMA DOT_DEMO.SALES TO ROLE DOT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA DOT_DEMO.SALES TO ROLE DOT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DOT_DEMO.SALES TO ROLE DOT_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA DOT_DEMO.SALES TO ROLE DOT_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA DOT_DEMO.SALES TO ROLE DOT_ROLE;
```

DOT_ROLE gets no privilege to create, change or delete data. Snowflake enforces that, whatever SQL a tool sends.

An X-Small warehouse is enough for most teams. It suspends after a minute without queries. The warehouse timeout stops any single query after 10 minutes, because Snowflake applies the lower of the warehouse and session timeouts. For a monthly credit limit, add a [resource monitor](https://docs.snowflake.com/en/user-guide/resource-monitors) to DOT_WH.

<!-- ------------------------ -->
## Create a Service User

A user with `TYPE = SERVICE` cannot sign in with a password or SAML SSO, so Dot signs in with a key pair. Create one on your computer:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out dot_rsa_key.p8 -nocrypt
openssl rsa -in dot_rsa_key.p8 -pubout -out dot_rsa_key.pub
```

`dot_rsa_key.p8` is the private key. Keep it secret. You paste it into Dot in the next step.

Print the public key on one line, without the BEGIN and END lines:

```bash
grep -v "PUBLIC KEY" dot_rsa_key.pub | tr -d '\n'
```

Create the user with that public key:

```sql
USE ROLE SECURITYADMIN;
CREATE USER IF NOT EXISTS DOT_USER
  TYPE = SERVICE
  DEFAULT_ROLE = DOT_ROLE
  DEFAULT_WAREHOUSE = DOT_WH
  RSA_PUBLIC_KEY = 'MIIBIjANBgkqh...' -- paste your one-line public key
  COMMENT = 'Service user for Dot';

GRANT ROLE DOT_ROLE TO USER DOT_USER;
```

Check that Snowflake stored the right key. This query returns the fingerprint of the stored key:

```sql
DESC USER DOT_USER
  ->> SELECT SUBSTR(
        (SELECT "value" FROM $1
           WHERE "property" = 'RSA_PUBLIC_KEY_FP'),
        LEN('SHA256:') + 1) AS key;
```

It must match the fingerprint of your key file:

```bash
openssl rsa -pubin -in dot_rsa_key.pub -outform DER | openssl dgst -sha256 -binary | openssl enc -base64
```

If your account restricts sign-ins with network policies, allow the IP addresses listed in the [Dot Snowflake docs](https://docs.getdot.ai/integrations/databases/snowflake).

<!-- ------------------------ -->
## Connect Dot to Snowflake

Find your account identifier:

```sql
SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS account_identifier;
```

Then in Dot:

1. Open **Settings**, go to **Connections** and click **Snowflake**.
2. Enter the account identifier and the username `DOT_USER`.
3. Turn on **Key-pair**. Paste the full contents of `dot_rsa_key.p8` into **Private Key**, including the BEGIN and END lines. Leave **Passphrase** empty, because the key is not encrypted.
4. Enter the role `DOT_ROLE` and the warehouse `DOT_WH`.
5. Click **Connect**.

Dot checks the connection and syncs the tables that DOT_ROLE can see. It reads table and column names, your comments and a small sample of values.

When the sync is done, open **Model** in the left navigation. Make sure all four DOT_DEMO.SALES tables are active, and activate any that are not.

Store `dot_rsa_key.p8` in your password manager, then delete the local copy.

<!-- ------------------------ -->
## Ask Your First Question

Start in the Dot web app, so you can compare the answer with your own SQL. Open a new chat and ask:

> What was revenue by region in 1997?

Dot finds the tables, joins them and answers with a table or a chart. Open the **Query** tab under the result to see the SQL it ran.

Now run your own query in Snowsight:

```sql
SELECT r.REGION_NAME, ROUND(SUM(o.ORDER_AMOUNT), 2) AS REVENUE
FROM DOT_DEMO.SALES.ORDERS o
JOIN DOT_DEMO.SALES.CUSTOMERS c ON c.CUSTOMER_ID = o.CUSTOMER_ID
JOIN DOT_DEMO.SALES.NATIONS n ON n.NATION_ID = c.NATION_ID
JOIN DOT_DEMO.SALES.REGIONS r ON r.REGION_ID = n.REGION_ID
WHERE YEAR(o.ORDER_DATE) = 1997
GROUP BY r.REGION_NAME
ORDER BY REVENUE DESC;
```

The numbers should match. If they do not, compare the two queries. The difference usually points to a business rule that Dot did not know. Add it as a comment, sync the connection and ask again.

<!-- ------------------------ -->
## Ask in Slack

1. In Dot, open **Settings**, go to **Connections** and click **Slack**.
2. Click **Add Dot to Slack** and allow the app in your Slack workspace.
3. Reload the Connections page in Dot and check the **Slack Team ID** field. Dot fills it in when your Slack workspace uses the same email domain as your Dot account. If it is empty, copy the ID that starts with `T` from your Slack URL in the browser, after `/client/`. Paste it and click **Save**.
4. In a Slack channel, invite Dot with `/invite @Dot`.
5. Start a thread with your question: `@Dot what was revenue by region in 1997?`
6. Reply in the same thread to ask a follow-up, such as `split Europe by market segment`. Dot uses the whole thread as context, so you don't need to mention it again.

Each answer in Slack has an **Access Online** link. It opens the answer in Dot, where you can see the SQL.

Dot also answers in Microsoft Teams. See [Dot in Microsoft Teams](https://docs.getdot.ai/integrations/slack-and-teams/microsoft-teams) for the setup.

<!-- ------------------------ -->
## Review Dot's Queries

Every query from Dot carries the query tag `dot`, runs as DOT_USER and uses DOT_WH. SYSADMIN owns DOT_WH, so it can list them:

```sql
USE ROLE SYSADMIN;
SELECT start_time, execution_status, total_elapsed_time, query_text
FROM TABLE(DOT_DEMO.INFORMATION_SCHEMA.QUERY_HISTORY_BY_USER(
       USER_NAME => 'DOT_USER', RESULT_LIMIT => 1000))
WHERE query_tag = 'dot'
ORDER BY start_time DESC;
```

To see the credits DOT_WH uses per day, query the account usage views with ACCOUNTADMIN. New usage can take a few hours to appear there.

```sql
USE ROLE ACCOUNTADMIN;
SELECT DATE_TRUNC('day', start_time) AS usage_day, SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE warehouse_name = 'DOT_WH'
GROUP BY usage_day
ORDER BY usage_day DESC;
```

<!-- ------------------------ -->
## Clean Up

In Dot, open **Settings**, go to **Connections**, click **Edit** on the Snowflake connection, click **Remove** and confirm. If you installed the Slack app only for this guide, remove it from your Slack workspace.

Then drop the Snowflake objects:

```sql
USE ROLE SECURITYADMIN;
DROP USER IF EXISTS DOT_USER;
DROP ROLE IF EXISTS DOT_ROLE;

USE ROLE SYSADMIN;
DROP WAREHOUSE IF EXISTS DOT_WH;
DROP DATABASE IF EXISTS DOT_DEMO;
```

Delete the key files if you still have them:

```bash
rm -f dot_rsa_key.p8 dot_rsa_key.pub
```

<!-- ------------------------ -->
## Conclusion And Resources

You gave an AI analyst read-only access to Snowflake through a key-pair service user, described your data with comments, and answered a question in Slack. The same setup works for your own data: grant DOT_ROLE read access to the schemas your teams ask about, and add comments as new questions come in.

### What You Learned
- How to create a `TYPE = SERVICE` user with key-pair authentication and a read-only role
- How Snowflake comments give an AI analyst business context
- How to check an AI answer against your own SQL
- How to see and cap the queries and credits a tool uses

### Related Resources
- [Dot](https://www.getdot.ai)
- [Dot Snowflake docs](https://docs.getdot.ai/integrations/databases/snowflake)
- [Dot in Slack](https://docs.getdot.ai/integrations/slack-and-teams/slack)
- [Snowflake key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Snowflake user types](https://docs.snowflake.com/en/user-guide/admin-user-management)
- [Snowflake resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)

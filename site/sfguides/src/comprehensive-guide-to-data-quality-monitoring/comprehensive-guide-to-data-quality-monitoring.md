author: Yoav Ostrinsky
id: comprehensive-guide-to-data-quality-monitoring
summary: A cookbook of runnable examples for Snowflake data quality — system and custom DMFs, expectations, scoping, AI-suggested checks, anomaly detection, notifications, and quality as code.
categories: snowflake-site:taxonomy/product/data-engineering,snowflake-site:taxonomy/snowflake-feature/transformation
environments: web
status: Draft
language: en
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Quality, Data Metric Functions, DMF, Data Engineering, Governance

# Comprehensive Guide to Snowflake Data Quality Monitoring
<!-- ------------------------ -->
## Overview

Data quality problems rarely announce themselves. A device clock drifts and starts stamping readings two days into the future. An upstream system swaps a missing battery level for `-1`. A firmware release starts emitting truncated JSON. Nothing errors, nothing fails, and the dashboards keep rendering — on data that is quietly wrong.

Snowflake checks for these conditions natively, on a schedule, without moving data or standing up another tool. This guide is a **cookbook** for doing that.

### How to use this guide

Each section from *Catch NULLs in a required column* onward is an **independent example**. Run one section on its own, in any order, without having done the others. The only shared prerequisite is the setup step, which creates one database and three small tables.

Every example that can be done both ways shows both: the SQL, and the Snowsight path. Neither is an afterthought. Some things are only available in one place — AI-suggested checks and the monitoring dashboards are Snowsight-only, and quality-as-code is SQL-only — and each example says which applies.

### What you will learn

- How a data quality check is assembled from a metric, an expectation, and a schedule
- Which of the ~39 system data metric functions to reach for, given a column's shape
- How to scope a check to a subset of rows, or compute it per group
- How to write a custom metric, and when the system already has one
- How to have Snowflake suggest checks for you, and how to have it learn what normal looks like
- How to find the offending rows, get notified, and stop a pipeline before bad data spreads
- How to keep all of it in version control

### Prerequisites

- A Snowflake account on **Enterprise Edition or higher**. Data Quality Monitoring is not available on Standard, and not on trial accounts.
- A role that can create a database, and that holds the account-level privileges for creating and attaching data metric functions. The setup step covers what is needed.
- Familiarity with running SQL in a Snowsight worksheet.

### A word on cost

Scheduled metric evaluations run on serverless compute and appear on your bill under the **Data Quality Monitoring** category. You are not billed for creating a metric, and you are not billed for calling one directly in a `SELECT` — only for evaluations that run on a schedule. The examples here use deliberately long schedules for that reason. The final section covers tracking the spend.

If you have Cortex Code available, the `/data-quality` skill can run these workflows against your own tables — recommending metrics, scoring schema health, and investigating violations.

<!-- ------------------------ -->
## Set Up the Example Data

This is the only step the other examples depend on. It creates a database, three tables of sensor telemetry, and a set of **deliberate defects** for the checks to find.

The scenario: refrigerated sites report temperature and humidity from battery-powered sensors. Readings land in a raw table, keyed to a device inventory.

```sql
CREATE DATABASE IF NOT EXISTS DQ_EXAMPLES;
USE DATABASE DQ_EXAMPLES;
USE SCHEMA PUBLIC;

CREATE OR REPLACE TABLE SITES (
    SITE_ID   VARCHAR(10),
    SITE_NAME VARCHAR(100),
    REGION    VARCHAR(50)
);

CREATE OR REPLACE TABLE DEVICES (
    DEVICE_ID    VARCHAR(20),
    SITE_ID      VARCHAR(10),
    MODEL        VARCHAR(50),
    INSTALLED_ON DATE,
    LABEL        VARCHAR(100)
);

CREATE OR REPLACE TABLE SENSOR_READINGS (
    READING_ID    NUMBER(10,0),
    DEVICE_ID     VARCHAR(20),
    READING_TS    TIMESTAMP_LTZ,
    INGESTED_AT   TIMESTAMP_LTZ,
    TEMPERATURE_C NUMBER(5,2),
    HUMIDITY_PCT  NUMBER(5,2),
    BATTERY_PCT   NUMBER(5,2),
    PAYLOAD       VARCHAR(500),
    STATUS_CODE   VARCHAR(20)
);
```

The timestamp columns are `TIMESTAMP_LTZ` on purpose. Metrics that compare a value against the time an evaluation runs — freshness, and future-dated detection — accept `DATE`, `TIMESTAMP_LTZ` and `TIMESTAMP_TZ`, but **not `TIMESTAMP_NTZ`**, which is Snowflake's default timestamp type. A column declared as plain `TIMESTAMP` will be rejected by those metrics. Metrics that only inspect values, such as null and duplicate counts, accept `TIMESTAMP_NTZ` without complaint. The *Anatomy of a check* section returns to this.

Load the reference data:

```sql
INSERT INTO SITES (SITE_ID, SITE_NAME, REGION) VALUES
    ('SITE-01', 'Rotterdam Cold Store',  'EMEA'),
    ('SITE-02', 'Dublin Distribution',   'EMEA'),
    ('SITE-03', 'Singapore Transit Hub', 'APAC');

INSERT INTO DEVICES (DEVICE_ID, SITE_ID, MODEL, INSTALLED_ON, LABEL) VALUES
    ('DEV-1001', 'SITE-01', 'TH-200',  '2025-03-14', 'Cold aisle A'),
    ('DEV-1002', 'SITE-01', 'TH-200',  '2025-03-14', 'Cold aisle B'),
    ('DEV-1003', 'SITE-02', 'TH-350',  '2025-07-02', '  Loading bay 1  '),
    ('DEV-1004', 'SITE-02', 'TH-350',  '2025-07-02', 'Loading bay 2'),
    ('DEV-1005', 'SITE-03', 'TH-350X', '2026-01-20', 'Transit chiller');
```

Now the readings. Timestamps are relative to when you run this, so the examples behave the same whenever you work through them:

```sql
INSERT INTO SENSOR_READINGS
    (READING_ID, DEVICE_ID, READING_TS, INGESTED_AT, TEMPERATURE_C, HUMIDITY_PCT, BATTERY_PCT, PAYLOAD, STATUS_CODE)
SELECT 1001, 'DEV-1001', DATEADD(HOUR, -9, CURRENT_TIMESTAMP()), DATEADD(HOUR, -9, CURRENT_TIMESTAMP()),  3.90, 61.20, 98.00, '{"rssi":-71,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1002, 'DEV-1001', DATEADD(HOUR, -8, CURRENT_TIMESTAMP()), DATEADD(HOUR, -8, CURRENT_TIMESTAMP()),  4.10, 60.80, 97.50, '{"rssi":-70,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1003, 'DEV-1002', DATEADD(HOUR, -8, CURRENT_TIMESTAMP()), DATEADD(HOUR, -8, CURRENT_TIMESTAMP()),  3.40, 63.10, 91.00, '{"rssi":-77,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1004, 'DEV-1002', DATEADD(HOUR, -7, CURRENT_TIMESTAMP()), DATEADD(HOUR, -7, CURRENT_TIMESTAMP()),  3.60, 62.40, 90.50, '{"rssi":-76,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1005, 'DEV-1003', DATEADD(HOUR, -7, CURRENT_TIMESTAMP()), DATEADD(HOUR, -7, CURRENT_TIMESTAMP()), 12.80, 48.90, 76.00, '{"rssi":-65,"fw":"2.4.0"}', 'OK'
UNION ALL SELECT 1006, 'DEV-1003', DATEADD(HOUR, -6, CURRENT_TIMESTAMP()), DATEADD(HOUR, -6, CURRENT_TIMESTAMP()), 13.10, 47.60, 75.50, '{"rssi":-66,"fw":"2.4.0"}', 'OK'
UNION ALL SELECT 1007, 'DEV-1004', DATEADD(HOUR, -6, CURRENT_TIMESTAMP()), DATEADD(HOUR, -6, CURRENT_TIMESTAMP()), 11.90, 50.20, 88.00, '{"rssi":-69,"fw":"2.4.0"}', 'OK'
UNION ALL SELECT 1008, 'DEV-1004', DATEADD(HOUR, -5, CURRENT_TIMESTAMP()), DATEADD(HOUR, -5, CURRENT_TIMESTAMP()), 12.20, 49.70, 87.50, '{"rssi":-68,"fw":"2.4.0"}', 'OK'
UNION ALL SELECT 1009, 'DEV-1005', DATEADD(HOUR, -5, CURRENT_TIMESTAMP()), DATEADD(HOUR, -5, CURRENT_TIMESTAMP()), -2.40, 55.30, 64.00, '{"rssi":-81,"fw":"2.4.1"}', 'OK'
UNION ALL SELECT 1010, 'DEV-1005', DATEADD(HOUR, -4, CURRENT_TIMESTAMP()), DATEADD(HOUR, -4, CURRENT_TIMESTAMP()), -2.10, 54.80, 63.50, '{"rssi":-80,"fw":"2.4.1"}', 'OK'
UNION ALL SELECT 1011, 'DEV-1001', DATEADD(HOUR, -4, CURRENT_TIMESTAMP()), DATEADD(HOUR, -4, CURRENT_TIMESTAMP()),  4.30, 60.10, 96.00, '{"rssi":-72,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1012, 'DEV-1002', DATEADD(HOUR, -3, CURRENT_TIMESTAMP()), DATEADD(HOUR, -3, CURRENT_TIMESTAMP()),  3.80, 61.90, 89.00, '{"rssi":-75,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1013, 'DEV-1003', DATEADD(HOUR, -3, CURRENT_TIMESTAMP()), DATEADD(HOUR, -3, CURRENT_TIMESTAMP()), 13.40, 46.80, 74.00, '{"rssi":-64,"fw":"2.4.0"}', 'OK'
UNION ALL SELECT 1014, 'DEV-1004', DATEADD(HOUR, -2, CURRENT_TIMESTAMP()), DATEADD(HOUR, -2, CURRENT_TIMESTAMP()), 12.50, 49.10, 86.50, '{"rssi":-67,"fw":"2.4.0"}', 'OK'
UNION ALL SELECT 1015, 'DEV-1005', DATEADD(HOUR, -2, CURRENT_TIMESTAMP()), DATEADD(HOUR, -2, CURRENT_TIMESTAMP()), -1.90, 54.20, 62.50, '{"rssi":-79,"fw":"2.4.1"}', 'OK'
UNION ALL SELECT 1015, 'DEV-1005', DATEADD(HOUR, -2, CURRENT_TIMESTAMP()), DATEADD(HOUR, -2, CURRENT_TIMESTAMP()), -1.90, 54.20, 62.50, '{"rssi":-79,"fw":"2.4.1"}', 'OK'
UNION ALL SELECT 1016, 'DEV-1001', DATEADD(HOUR, -1, CURRENT_TIMESTAMP()), DATEADD(HOUR, -1, CURRENT_TIMESTAMP()), NULL,  59.70, 95.50, '{"rssi":-73,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1017, 'DEV-9999', DATEADD(HOUR, -1, CURRENT_TIMESTAMP()), DATEADD(HOUR, -1, CURRENT_TIMESTAMP()),  5.20, 58.30, 80.00, '{"rssi":-74,"fw":"2.3.1"}', 'OK'
UNION ALL SELECT 1018, 'DEV-1003', DATEADD(MINUTE, -30, CURRENT_TIMESTAMP()), DATEADD(MINUTE, -30, CURRENT_TIMESTAMP()), 13.00, 47.10, -1.00, '{"rssi":-63,"fw":"2.4.0"}', 'BATT_UNKNOWN'
UNION ALL SELECT 1019, 'DEV-1004', DATEADD(MINUTE, -20, CURRENT_TIMESTAMP()), DATEADD(MINUTE, -20, CURRENT_TIMESTAMP()), 12.10, 49.40, 86.00, '{"rssi":-67,"fw":', 'OK'
UNION ALL SELECT 1020, 'DEV-1002', DATEADD(DAY, 2, CURRENT_TIMESTAMP()), DATEADD(MINUTE, -10, CURRENT_TIMESTAMP()),  3.70, 62.00, 88.50, '{"rssi":-75,"fw":"2.3.1"}', 'OK';
```

That is 21 rows across 5 devices and 3 sites.

### The defects, named openly

Seven problems are planted in that data. Knowing them in advance makes each example verifiable — you can see the check find the thing you know is there.

| Reading | Problem | The check that finds it |
|:--------|:--------|:------------------------|
| 1016 | `TEMPERATURE_C` is NULL | `NULL_COUNT` |
| 1020 | `READING_TS` is two days in the future — device clock skew | `FUTURE_TIMESTAMP_COUNT` |
| 1019 | `PAYLOAD` is truncated and not valid JSON | `INVALID_JSON_COUNT` |
| 1018 | `BATTERY_PCT` is `-1`, a sentinel for "unknown" | `NEGATIVE_COUNT` |
| 1015 | Appears twice — duplicated on ingest | `DUPLICATE_COUNT` |
| 1017 | `DEVICE_ID` is `DEV-9999`, which is not in `DEVICES` | `REFERENTIAL_INTEGRITY_COUNT` |
| `DEVICES` `DEV-1003` | `LABEL` has leading and trailing spaces | `UNTRIMMED_STRING_COUNT` |

Note that `TEMPERATURE_C` legitimately goes negative here — `DEV-1005` is a freezer. That is why the negative-value check targets `BATTERY_PCT` and not temperature. Choosing the column a rule applies to is part of designing the rule.

<!-- ------------------------ -->
## Profile Before You Check

Before writing rules, look at the data. Snowsight's profiling view summarises a column's distribution, null share, and distinct values, which is usually what tells you which rules are worth writing. This one is Snowsight-only; there is no SQL equivalent that produces the same view.

1. In Snowsight, open **Data » Databases** and expand **DQ_EXAMPLES » PUBLIC » Tables**.
2. Select **SENSOR_READINGS**, then open the **Data Preview** tab.
3. Open the **Profile** tab to see per-column statistics.

<!-- TODO: screenshot of the Profile tab for SENSOR_READINGS, showing the TEMPERATURE_C null share and the BATTERY_PCT minimum of -1 -->

Two things stand out without writing a single rule. `TEMPERATURE_C` has a non-zero null share. `BATTERY_PCT` has a minimum of `-1`, which is impossible for a percentage. Each points at a check worth adding.

The same reasoning works in SQL when you want it scripted rather than eyeballed:

```sql
SELECT COUNT(*)                                            AS TOTAL_ROWS,
       COUNT(*) - COUNT(TEMPERATURE_C)                      AS MISSING_TEMPERATURE,
       MIN(BATTERY_PCT)                                     AS LOWEST_BATTERY,
       COUNT(DISTINCT DEVICE_ID)                            AS DEVICES_REPORTING,
       MAX(READING_TS)                                      AS LATEST_READING
FROM SENSOR_READINGS;
```

Profiling tells you what is unusual. It does not tell you what is *wrong* — that judgement is yours, and expressing it is what the rest of this guide is about.

<!-- ------------------------ -->
## Anatomy of a Check

A data quality check in Snowflake has three parts.

A **data metric function (DMF)** measures something and returns a number. `NULL_COUNT` returns how many NULLs are in a column. A DMF makes no judgement — it reports.

An **expectation** turns that number into a verdict. `EXPECT value = 0` says a non-zero null count is a failure. Without an expectation you have a measurement; with one you have a check.

A **schedule** decides how often the measurement runs. Set it on the table, and it governs every metric attached to that table.

### Attaching your first check

Attach a metric with `ALTER TABLE`, and set the schedule before the metric so the first evaluation has a cadence to follow:

```sql
ALTER TABLE SENSOR_READINGS SET DATA_METRIC_SCHEDULE = '1440 MINUTE';

ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    ON (TEMPERATURE_C)
    EXPECTATION MUST_HAVE_TEMPERATURE (VALUE = 0);
```

On a new table, declare the check in `CREATE TABLE` instead, so the table and its guarantees arrive together. This is the habit worth forming — it keeps quality rules in the same definition your deployment tooling already manages. The clause follows the closing parenthesis of the column list, not an individual column:

```sql
CREATE OR REPLACE TABLE SENSOR_READINGS_V2 (
    READING_ID    NUMBER(10,0),
    TEMPERATURE_C NUMBER(5,2)
)
WITH DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    ON (TEMPERATURE_C)
    EXPECTATION MUST_HAVE_TEMPERATURE (VALUE = 0);
```

Attach several at once by separating the bindings with commas. After the first one, the `WITH DATA METRIC FUNCTION` keywords are not repeated:

```sql
CREATE OR REPLACE TABLE SENSOR_READINGS_V3 (
    READING_ID    NUMBER(10,0),
    TEMPERATURE_C NUMBER(5,2)
)
WITH DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    ON (TEMPERATURE_C)
    EXPECTATION MUST_HAVE_TEMPERATURE (VALUE = 0),
  SNOWFLAKE.CORE.DUPLICATE_COUNT
    ON (READING_ID)
    EXPECTATION NO_DUPLICATE_READINGS (VALUE = 0);
```

### The one distinction that shapes everything else

Metrics come in two shapes, and the difference decides how you can test them.

Metrics that **take a column argument** can be called directly in a `SELECT`. You get an answer immediately, with no schedule, no attachment, and no cost. This is the fastest feedback loop Snowflake gives you:

```sql
SELECT SNOWFLAKE.CORE.NULL_COUNT(SELECT TEMPERATURE_C FROM SENSOR_READINGS) AS MISSING_TEMPERATURE;
```

```
+---------------------+
| MISSING_TEMPERATURE |
+---------------------+
|                   1 |
+---------------------+
```

Metrics that **take no column argument** — because they measure the table as a whole — cannot be called this way. `ROW_COUNT`, `SCHEMA_CHANGE_COUNT`, `REFERENTIAL_INTEGRITY_COUNT`, the multi-column form of `DUPLICATE_COUNT`, and `FRESHNESS` without a column all work only once attached. Calling `ROW_COUNT` directly returns an argument-count error rather than a number.

| Shape | Examples | Direct `SELECT`? | How to see a result |
|:------|:---------|:-----------------|:--------------------|
| Takes a column | `NULL_COUNT`, `DUPLICATE_COUNT`, `INVALID_JSON_COUNT`, `NEGATIVE_COUNT`, `FUTURE_TIMESTAMP_COUNT`, `FRESHNESS(<ts_col>)` | Yes | Call it in a `SELECT` |
| Takes no column | `ROW_COUNT`, `SCHEMA_CHANGE_COUNT`, `REFERENTIAL_INTEGRITY_COUNT`, `FRESHNESS()`, multi-column `DUPLICATE_COUNT` | No | Attach it, then scan or read results |

Keep this in mind as you work through the examples. Where a direct call is possible, each example ends with one, because it is immediate and free. Where it is not, the example attaches the metric and reads the result instead.

### Checking an expectation without waiting

Attached checks run on their schedule, which is rarely convenient when you are still writing them. Evaluate every expectation on a table immediately:

```sql
SELECT METRIC_NAME, EXPECTATION_NAME, EXPECTATION_EXPRESSION, VALUE, EXPECTATION_VIOLATED
FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS('SENSOR_READINGS'));
```

| METRIC_NAME | EXPECTATION_NAME | EXPECTATION_EXPRESSION | VALUE | EXPECTATION_VIOLATED |
|:------------|:-----------------|:-----------------------|------:|:---------------------|
| NULL_COUNT | MUST_HAVE_TEMPERATURE | VALUE = 0 | 1 | TRUE |

The check found reading 1016 and reported the violation, with no waiting. This is the difference between authoring a check confidently and hoping you got it right.

Note what is *not* in that result. Only metrics that have an expectation appear — a metric attached without one is measured but never judged, so there is nothing for this function to report on. If a check you expect to see is missing here, the usual reason is a missing expectation rather than a missing metric.

### The same thing in Snowsight

Snowsight builds the metric and the expectation together in one flow.

1. Open **Data » Databases**, then **DQ_EXAMPLES » PUBLIC » SENSOR_READINGS**.
2. Open the **Data Quality** tab.
3. Select **Add quality check**, pick the metric, choose the column, and set the expected values.

<!-- TODO: screenshot of the Data Quality tab on SENSOR_READINGS with the Add quality check panel open, NULL_COUNT selected on TEMPERATURE_C -->

The result is the same object either way — a check created in Snowsight is visible to SQL, and one created in SQL appears in the Snowsight tab. Use whichever suits the moment: the UI for exploring and for one-off checks, SQL for anything you intend to keep.

### Turning a schedule off, and the trap in doing it

To stop evaluations while leaving the checks attached, set the schedule to an empty string:

```sql
ALTER TABLE SENSOR_READINGS SET DATA_METRIC_SCHEDULE = '';
```

Reach for `SET ... = ''` and not `UNSET`. Unsetting the property does not stop anything — it removes your schedule and the table reverts to the **default hourly** cadence, `0 */1 * * * UTC`. On a table you had running daily, `UNSET` therefore multiplies the evaluations by twenty-four while looking like the statement that switches monitoring off. Confirm which you have with:

```sql
SELECT METRIC_NAME, SCHEDULE, SCHEDULE_STATUS
FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
    REF_ENTITY_NAME   => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
    REF_ENTITY_DOMAIN => 'table'));
```

A blank `SCHEDULE` means suspended. A cron expression you did not write means you are on the default.

Suspend the example table whenever you pause partway through this guide.

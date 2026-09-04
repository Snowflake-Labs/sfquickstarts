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
## Choosing a Check

Snowflake ships **39 system metrics** in `SNOWFLAKE.CORE`, across six families. You will use perhaps eight of them regularly. This section is the index to come back to — the rest of the guide is worked examples of the rows in these tables.

List what your account actually has, rather than trusting any published list including this one:

```sql
SHOW DATA METRIC FUNCTIONS IN SCHEMA SNOWFLAKE.CORE;
```

That returns roughly 90 rows, not 39, because most metrics have one signature per data type — `NULL_COUNT` alone has seven. Count distinct names, not rows.

### Start from the column, not the catalog

| What you have | Reach for | Catches |
|:--------------|:----------|:--------|
| A column that must always be populated | `NULL_COUNT`, `NULL_PERCENT` | Missing values |
| A text column that must not be empty or padded | `BLANK_COUNT`, `UNTRIMMED_STRING_COUNT` | Empty strings, stray whitespace |
| A natural key or ID | `DUPLICATE_COUNT`, `UNIQUE_COUNT` | Double ingestion, broken grain |
| A foreign key into another table | `REFERENTIAL_INTEGRITY_COUNT` | Orphaned rows |
| A column with a known set of valid values | `ACCEPTED_VALUES` | Unexpected status codes, bad enums |
| A numeric measure that cannot be negative or zero | `NEGATIVE_COUNT`, `ZERO_COUNT` | Sentinel values, unit errors |
| A text column holding JSON | `INVALID_JSON_COUNT` | Malformed payloads |
| Numbers stored as text | `INVALID_NUMERIC_TYPE_CAST_COUNT` | Values that will break a cast |
| A timestamp that should never be in the future | `FUTURE_TIMESTAMP_COUNT` | Clock skew, bad backfills |
| A table that must keep receiving data | `FRESHNESS`, `ROW_COUNT` | Stalled pipelines, volume collapse |
| A numeric column whose *distribution* matters | `AVG`, `STDDEV`, `MEDIAN`, `VARIANCE`, `APPROX_QUANTILE_25/50/99` | Drift that no single row reveals |
| Text whose length or casing should be stable | `STRING_LENGTH_MIN/AVG/MAX`, `CASE_FORMAT_VIOLATION_COUNT`, `SPECIAL_CHARACTER_COUNT` | Truncation, format regressions |
| A table whose shape should not change unnoticed | `SCHEMA_CHANGE_COUNT` | Columns added, dropped, renamed, retyped |

### The six families

**Accuracy** is the largest family — 20 metrics, mostly in `_COUNT` and `_PERCENT` pairs: blanks, case-format violations, future timestamps, invalid JSON, failed numeric casts, negatives, nulls, special characters, untrimmed strings, zeros. Prefer `_COUNT` when any occurrence is a defect, and `_PERCENT` when you care about proportion in a table whose size varies.

**Freshness** has `FRESHNESS`, which returns the seconds between your data's latest timestamp and the moment the evaluation ran.

**Volume** has `ROW_COUNT`.

**Uniqueness** has `ACCEPTED_VALUES`, `DUPLICATE_COUNT` and `UNIQUE_COUNT`.

**Statistics** has 12 metrics for tracking a distribution rather than asserting a rule.

**Schema** has `SCHEMA_CHANGE_COUNT`.

Referential integrity sits slightly outside this scheme: `REFERENTIAL_INTEGRITY_COUNT` is a system metric that takes a second table as an argument, which no other system metric does.

One name to be careful with. `DATA_METRIC_SCHEDULE_TIME` appears alongside these in some listings, but it is **not a metric you can attach** — it is a helper that returns the scheduled evaluation time, for use inside a custom metric you write yourself. Attempting to attach it will fail. The custom-metric section uses it properly.

### When nothing fits

Write your own. Before you do, check the catalog twice: hand-rolled foreign-key checks and hand-rolled value-in-list checks are the two most commonly rewritten custom metrics, and `REFERENTIAL_INTEGRITY_COUNT` and `ACCEPTED_VALUES` already do both.

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

There are two variants, and the difference matters as soon as anything downstream reads the results:

| Function | Returns a result | Records it |
|:---------|:-----------------|:-----------|
| `SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS` | Yes | No |
| `SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS_PERSIST_RESULT` | Yes | Yes |

The plain form is for looking. The `_PERSIST_RESULT` form also writes the measurement into monitoring history, which is what anything reading `DATA_QUALITY_MONITORING_EXPECTATION_STATUS` depends on — a dashboard, a notification, or the circuit breaker later in this guide. If you attach a check, evaluate it on demand, and then find the status surface still empty, this is why.

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

<!-- ------------------------ -->
## Catch NULLs in a Required Column

Every reading should carry a temperature. Reading 1016 does not.

```sql
SELECT SNOWFLAKE.CORE.NULL_COUNT(SELECT TEMPERATURE_C FROM SENSOR_READINGS) AS MISSING;
```

Returns `1`. Use the percentage form when the table's size varies and a proportion is more meaningful than a count:

```sql
SELECT SNOWFLAKE.CORE.NULL_PERCENT(SELECT TEMPERATURE_C FROM SENSOR_READINGS) AS MISSING_PCT;
```

Returns `4.761900` — one row in twenty-one.

Attach it with an expectation that no reading may be missing a temperature:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    ON (TEMPERATURE_C)
    EXPECTATION MUST_HAVE_TEMPERATURE (VALUE = 0);
```

Choose the count form for a rule ("never") and the percentage form for a tolerance ("under 1%"). A tolerance is honest for sensor data, where the odd dropped reading is normal and a spike is the real signal.

**In Snowsight:** open the table, go to the **Data Quality** tab, select **Add quality check**, pick **NULL_COUNT**, choose `TEMPERATURE_C`, and set the expected value to 0.

<!-- TODO: screenshot of the Add quality check panel with NULL_COUNT on TEMPERATURE_C and expectation VALUE = 0 -->

<!-- ------------------------ -->
## Enforce a Freshness SLA

`FRESHNESS` returns the seconds between the newest value in a timestamp column and the moment the check ran. Small is good.

```sql
SELECT SNOWFLAKE.CORE.FRESHNESS(SELECT READING_TS FROM SENSOR_READINGS) AS STALENESS_SECONDS;
```

On the example data this returns something like `-165869`. **Negative** — and that is the lesson of this section.

Freshness reports on the *newest* timestamp it can find. Reading 1020 is stamped two days ahead by a drifting device clock, so Snowflake dutifully reports data that has not happened yet. The number looks better than perfect, and a freshness check with an expectation like `VALUE < 3600` would pass happily while the pipeline behind it was dead.

This is the most instructive failure in the guide: **a freshness check alone can be defeated by one bad timestamp.** Pair it with the clock-skew check in the next section and the pair cannot be fooled — one catches staleness, the other catches the row that would mask it.

With the misdated row excluded, freshness reflects reality:

```sql
SELECT SNOWFLAKE.CORE.FRESHNESS(
    SELECT READING_TS FROM SENSOR_READINGS WHERE READING_TS <= CURRENT_TIMESTAMP()
) AS STALENESS_SECONDS;
```

Attach a ten-minute SLA. `FRESHNESS` needs the column named at attach time:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS
    ON (READING_TS)
    EXPECTATION READINGS_ARE_RECENT (VALUE < 600);
```

`FRESHNESS` also has a zero-argument form, `ON ()`, which measures the last DML against the table rather than a column. Reach for that when you care whether the *pipeline* ran, and the column form when you care whether the *data* is current. They answer different questions: a job that writes nothing still updates the table.

The timestamp-type rule from *Anatomy of a check* applies here — `READING_TS` is `TIMESTAMP_LTZ` because `FRESHNESS` rejects `TIMESTAMP_NTZ`.

For freshness logic the built-in cannot express — business hours, per-source SLAs — write a custom metric using the `SNOWFLAKE.CORE.DATA_METRIC_SCHEDULE_TIME` helper, which returns the scheduled evaluation time. The custom-metric section shows the pattern.

<!-- ------------------------ -->
## Detect Device Clock Skew

A reading timestamped ahead of the clock is always wrong, and as the previous section showed, it corrupts every freshness measurement taken alongside it.

```sql
SELECT SNOWFLAKE.CORE.FUTURE_TIMESTAMP_COUNT(SELECT READING_TS FROM SENSOR_READINGS) AS SKEWED_ROWS;
```

Returns `1` — reading 1020.

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.FUTURE_TIMESTAMP_COUNT
    ON (READING_TS)
    EXPECTATION NO_SKEWED_READINGS (VALUE = 0);
```

The metric compares each value against the moment the evaluation runs, so the check is inherently time-relative: a row that passes today can fail if you rerun history. That is correct behaviour, not a quirk — a backfill dated next Tuesday is wrong on both days.

`FUTURE_TIMESTAMP_PERCENT` exists for the same tolerance reason as the null pair. For clock skew, prefer the count: one skewed row is a defect, not a rate.

<!-- ------------------------ -->
## Find Orphaned Rows

Reading 1017 reports device `DEV-9999`, which is not in `DEVICES`. Joins will silently drop it, so anything aggregated downstream is quietly short.

`REFERENTIAL_INTEGRITY_COUNT` is the system metric for this, and it replaces the hand-written `NOT IN` check people usually reach for. It cannot be called directly, so attach it first:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.REFERENTIAL_INTEGRITY_COUNT
    ON (DEVICE_ID, TABLE(DEVICES(DEVICE_ID)))
    EXPECTATION NO_ORPHAN_READINGS (VALUE = 0);
```

The second argument names the parent table and its matching column. Once attached, retrieve the offending rows:

```sql
SELECT * FROM TABLE(SYSTEM$DATA_METRIC_SCAN(
    REF_ENTITY_NAME => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
    METRIC_NAME     => 'SNOWFLAKE.CORE.REFERENTIAL_INTEGRITY_COUNT',
    ARGUMENT_NAME   => 'DEVICE_ID'));
```

| READING_ID | DEVICE_ID | TEMPERATURE_C | STATUS_CODE |
|-----------:|:----------|--------------:|:------------|
| 1017 | DEV-9999 | 5.20 | OK |

Not a count — the actual row, ready to route to a quarantine table or send back to the source team.

Compound keys work the same way, with columns listed in matching order on both sides:

```sql
-- Illustrative: matching a two-column key
-- ON (SITE_ID, DEVICE_ID, TABLE(DEVICE_REGISTRY(SITE_ID, DEVICE_ID)))
```

<!-- ------------------------ -->
## Validate JSON Payloads

Devices send a JSON blob in a `VARCHAR` column, and firmware bugs truncate it. Reading 1019's payload is `{"rssi":-67,"fw":` — unparseable, and every downstream `PARSE_JSON` on it returns NULL rather than failing loudly.

```sql
SELECT SNOWFLAKE.CORE.INVALID_JSON_COUNT(SELECT PAYLOAD FROM SENSOR_READINGS) AS BAD_PAYLOADS;
```

Returns `1`.

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.INVALID_JSON_COUNT
    ON (PAYLOAD)
    EXPECTATION PAYLOAD_IS_JSON (VALUE = 0);
```

The metric tests whether `TRY_PARSE_JSON` succeeds, and NULLs are not counted as invalid — an absent payload is a null-check concern, not a format one. If both matter, attach both metrics to the column.

`INVALID_NUMERIC_TYPE_CAST_COUNT` is the sibling for numbers stored as text, and is worth attaching to any staging column you plan to cast. It tells you the cast will fail before the cast does.

<!-- ------------------------ -->
## Reject Impossible and Sentinel Values

Reading 1018 reports `BATTERY_PCT = -1`. Nothing is wrong with the value as a number — it is a sentinel the firmware uses for "battery unknown". Averaged into a fleet health dashboard, it silently drags the mean down.

```sql
SELECT SNOWFLAKE.CORE.NEGATIVE_COUNT(SELECT BATTERY_PCT FROM SENSOR_READINGS) AS IMPOSSIBLE_BATTERY,
       SNOWFLAKE.CORE.ZERO_COUNT(SELECT BATTERY_PCT FROM SENSOR_READINGS)     AS ZERO_BATTERY;
```

Returns `1` and `0`.

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NEGATIVE_COUNT
    ON (BATTERY_PCT)
    EXPECTATION BATTERY_NOT_NEGATIVE (VALUE = 0);
```

Apply these to the right column. `TEMPERATURE_C` is legitimately negative in this dataset — `DEV-1005` is a freezer — so a negative check there would fire constantly and teach the team to ignore alerts. A check that cries wolf is worse than no check.

For a column with a known set of valid values, `ACCEPTED_VALUES` takes a lambda and counts the rows that fail it:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ACCEPTED_VALUES
    ON (STATUS_CODE, STATUS_CODE -> STATUS_CODE IN ('OK', 'WARN'))
    EXPECTATION STATUS_IS_KNOWN (VALUE = 0);
```

That fires on reading 1018, whose `STATUS_CODE` is `BATT_UNKNOWN`. Reach for `ACCEPTED_VALUES` before writing a custom metric for a value-in-list rule — it is the most commonly reinvented custom metric there is.

Unlike the counting metrics, `ACCEPTED_VALUES` cannot be called directly in a `SELECT`. Attach it, then use `SYSTEM$DATA_METRIC_SCAN` with `ARGUMENT_EXPRESSION` to see the failing rows.

<!-- ------------------------ -->
## Catch Duplicates on a Natural Key

Reading 1015 was ingested twice. Counts double, averages do not — the sort of inconsistency that gets noticed in a meeting rather than by a pipeline.

```sql
SELECT SNOWFLAKE.CORE.DUPLICATE_COUNT(SELECT READING_ID FROM SENSOR_READINGS) AS DUPLICATED_VALUES,
       SNOWFLAKE.CORE.UNIQUE_COUNT(SELECT READING_ID FROM SENSOR_READINGS)    AS DISTINCT_VALUES;
```

Returns `1` and `20`.

Read those two carefully, because the names invite a wrong reading. There are 21 rows and 20 distinct IDs. `DUPLICATE_COUNT` returns 1 — the number of *values that have duplicates*, not the number of excess rows. `UNIQUE_COUNT` returns 20 — the number of *distinct* values, not the number appearing exactly once. If you expected 19, you were reading it as "values that occur once".

For a uniqueness rule, `DUPLICATE_COUNT = 0` is the check you want:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT
    ON (READING_ID)
    EXPECTATION READING_ID_IS_UNIQUE (VALUE = 0);
```

When the grain is a column combination rather than a single key, list the columns. That form takes no single column argument, so it cannot be called directly:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT
    ON (DEVICE_ID, READING_TS)
    EXPECTATION ONE_READING_PER_DEVICE_PER_TIMESTAMP (VALUE = 0);
```

NULLs count as a value here, so a nullable key column reports duplicates once two rows are both NULL. That is usually what you want from a grain check.

<!-- ------------------------ -->
## Watch for Volume Collapse

The failure that catches teams out is not bad data arriving — it is good data stopping. A source drops a partition, the pipeline succeeds, and yesterday's numbers merely look quiet.

`ROW_COUNT` measures the table as a whole and takes no column, so **it cannot be called directly**. Calling it in a `SELECT` returns an argument-count error. Attach it:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT
    ON ()
    EXPECTATION ENOUGH_READINGS (VALUE > 15);
```

Then read the measurement once an evaluation has run:

```sql
SELECT MEASUREMENT_TIME, TABLE_NAME, METRIC_NAME, VALUE
FROM TABLE(SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS(
    REF_ENTITY_NAME   => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
    REF_ENTITY_DOMAIN => 'TABLE'))
WHERE METRIC_NAME = 'ROW_COUNT'
ORDER BY MEASUREMENT_TIME DESC;
```

A fixed floor like `VALUE > 15` is crude — it needs revisiting as the table grows, and it cannot express "less than usual". For volume, the better tool is anomaly detection, which learns the normal range instead of asking you to assert one.

<!-- ------------------------ -->
## Check Only the Rows You Care About

Rules rarely apply to a whole table. Readings flagged `BATT_UNKNOWN` are *expected* to carry a sentinel battery value, so including them in the battery check guarantees a permanent violation.

`FILTER` scopes a check to a subset of rows:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NEGATIVE_COUNT
    ON (BATTERY_PCT)
    FILTER (STATUS_CODE = 'OK')
    EXPECTATION HEALTHY_DEVICES_REPORT_BATTERY (VALUE = 0);
```

Now the check says something precise: *devices reporting OK must report a real battery level.* The sentinel rows are out of scope by definition rather than by tolerance. On the example data this check measures 0 and passes, where the unfiltered version would fail forever.

Filters take multiple conditions:

```sql
-- Illustrative
-- FILTER (STATUS_CODE = 'OK' AND READING_TS >= '2026-01-01')
```

Note the clause order — `FILTER` comes after the column and before the expectation.

Prefer a filter over a loosened threshold. `VALUE = 0` on the rows that matter is a statement about your data; `VALUE < 5` on all rows is a statement about your tolerance for not knowing which five.

<!-- ------------------------ -->
## Per-Site Metrics from One Association

Fleet-wide averages hide site-level failures. If one site of three goes dark, the account-wide null rate barely moves.

`WITHIN GROUP` computes the same metric separately for each value of a grouping column, from a single association:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    ON (TEMPERATURE_C)
    WITHIN GROUP (DEVICE_ID)
    EXPECTATION EVERY_DEVICE_REPORTS_TEMPERATURE (VALUE = 0);
```

One attachment, one schedule, one expectation — evaluated per device. Do not create one association per group value, and do not build dynamic tables or `GROUP BY` queries to imitate this; the clause exists for exactly this purpose.

Group by more than one column, and raise the cap when the grouping is wide:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    ON (TEMPERATURE_C)
    WITHIN GROUP (DEVICE_ID, STATUS_CODE)
    GROUP LIMIT 500
    EXPECTATION EVERY_DEVICE_AND_STATUS_REPORTS (VALUE = 0);
```

Grouped results carry a `GROUP_BY_INFO` column in `DATA_QUALITY_MONITORING_RESULTS` identifying which group each measurement belongs to, and `SYSTEM$DATA_METRIC_SCAN` accepts a `WITHIN_GROUP_VALUES` argument to fetch the failing rows for one group.

Choose the grouping column carefully. High cardinality means many measurements per evaluation, which is why the group cap exists. Group by site or status, not by reading ID.

<!-- ------------------------ -->
## Detect Schema Drift

An upstream team renames a column. Nothing errors immediately — a view resolves, a cast starts returning NULL, and the damage surfaces weeks later.

`SCHEMA_CHANGE_COUNT` counts column additions, drops, renames and type changes. It takes no column argument, so it must be attached:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.SCHEMA_CHANGE_COUNT
    ON ()
    EXPECTATION SCHEMA_IS_STABLE (VALUE = 0);
```

This one measures change **since the previous evaluation**, which makes it different from every other metric here in two ways. It needs two evaluations before it reports anything meaningful, and its result is a delta rather than a state — a value of 0 means "nothing changed since last time", not "the schema is as originally designed". It will not tell you about a column dropped before you attached the check.

Use it as a change detector feeding a notification, not as a structural assertion.

<!-- ------------------------ -->
## Track a Distribution, Not a Rule

Some problems are invisible row by row. A sensor recalibrated to Fahrenheit produces no nulls, no duplicates and no impossible values — every reading is individually plausible, and the distribution has moved.

The statistics metrics measure shape rather than validity:

```sql
SELECT SNOWFLAKE.CORE.AVG(SELECT TEMPERATURE_C FROM SENSOR_READINGS)                AS MEAN_TEMP,
       SNOWFLAKE.CORE.MEDIAN(SELECT TEMPERATURE_C FROM SENSOR_READINGS)             AS MEDIAN_TEMP,
       SNOWFLAKE.CORE.STDDEV(SELECT TEMPERATURE_C FROM SENSOR_READINGS)             AS SPREAD_TEMP,
       SNOWFLAKE.CORE.APPROX_QUANTILE_99(SELECT TEMPERATURE_C FROM SENSOR_READINGS) AS P99_TEMP;
```

| MEAN_TEMP | MEDIAN_TEMP | SPREAD_TEMP | P99_TEMP |
|----------:|------------:|------------:|---------:|
| 6.235 | 4.2 | 5.836 | 13.343 |

Mean well above median, and a spread as large as the mean, is the signature of a mixed population — which is exactly right here, because chilled sites and a freezer are pooled in one table. That is a modelling observation the profiling view would also have shown you.

Attaching a statistics metric records the value over time. There is usually no threshold worth asserting:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.AVG
    ON (TEMPERATURE_C);
```

A metric with no expectation is measured but never judged. That is a legitimate way to build history before you know what normal looks like — but it will not appear in `SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS` output, because there is no expectation to evaluate.

For distributions, resist inventing thresholds. `AVG` between 2 and 8 is a guess that will either miss real drift or page someone during a heatwave. Record the metric, then let anomaly detection learn the range.

`MEDIAN` is exact while `APPROX_QUANTILE_50` is estimated, and the approximate forms are cheaper on large tables. `STRING_LENGTH_MIN`, `_AVG` and `_MAX` do the same job for text, and are the quickest way to catch a truncation regression.

<!-- ------------------------ -->
## Write Your Own Check

When no system metric fits, write one. A data metric function is a SQL function that takes a table argument and returns a number.

This one counts readings whose humidity is outside a plausible range — a cross-column rule no single system metric expresses:

```sql
CREATE OR REPLACE DATA METRIC FUNCTION IMPLAUSIBLE_HUMIDITY(
    ARG_T TABLE (ARG_HUMIDITY NUMBER)
)
RETURNS NUMBER
AS
$$
    SELECT COUNT(*) FROM ARG_T WHERE ARG_HUMIDITY < 0 OR ARG_HUMIDITY > 100
$$;
```

Attach it exactly like a system metric:

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION IMPLAUSIBLE_HUMIDITY
    ON (HUMIDITY_PCT)
    EXPECTATION HUMIDITY_IN_RANGE (VALUE = 0);
```

Custom metrics can take more than one table argument, which is how you express a rule spanning two tables. They can also use `SNOWFLAKE.CORE.DATA_METRIC_SCHEDULE_TIME()` to compare data against the evaluation time, which is the supported way to build a freshness rule the built-in cannot express — business hours, per-source SLAs, a grace period on weekends.

### Check the catalog first

Two custom metrics get written over and over when a system metric already exists:

- A `NOT IN` subquery against a parent table. Use `REFERENTIAL_INTEGRITY_COUNT`.
- A `WHERE col NOT IN ('A','B','C')` count. Use `ACCEPTED_VALUES` with a lambda.

Both system versions are maintained, optimised and understood by the Snowsight monitoring surfaces. A hand-rolled equivalent is code you own forever.

One practical constraint worth knowing before you design a multi-table custom metric: validation of columns passed inside a `TABLE(...)` argument is weaker than for single-column metrics, so a mistake in a two-table signature can surface at evaluation time rather than at attach time. Test a custom metric by calling it directly before attaching it — that way you find the error immediately:

```sql
SELECT IMPLAUSIBLE_HUMIDITY(SELECT HUMIDITY_PCT FROM SENSOR_READINGS) AS OUT_OF_RANGE;
```

<!-- ------------------------ -->
## Cover a Whole Schema in One Statement

Attaching metrics table by table does not scale past a handful of tables. Volume and freshness are generic enough to apply everywhere, so attach them at the schema level:

```sql
ALTER SCHEMA PUBLIC
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON ();

ALTER SCHEMA PUBLIC
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS ON ();
```

Snowflake creates an object-level association for every supported table-like object in the schema, including ones added later. Only `ROW_COUNT` and `FRESHNESS` work this way — they are the two metrics that need no column argument and apply to any table. Column-level checks stay per table, because they depend on what the columns mean.

Exclude object types you do not want covered:

```sql
ALTER SCHEMA PUBLIC
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON ()
    EXCLUDE_TABLE_TYPES = ('VIEW', 'MATERIALIZED_VIEW');
```

Zero-argument `FRESHNESS` skips views and external tables on its own, since those need a column argument.

Tell schema-level from table-level associations by inspecting the references:

```sql
SELECT REF_ENTITY_NAME, METRIC_NAME, LEVEL, EXCLUDE_TABLE_TYPES
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES
WHERE REF_DATABASE_NAME = 'DQ_EXAMPLES';
```

`LEVEL` reads `SCHEMA` for associations created by a schema-level statement and `TABLE` for ones you attached directly. This matters when you try to remove a check: an association created at the schema level is detached at the schema level.

The cost consequence is worth thinking about before you run this. One statement across a schema of two hundred tables creates two hundred scheduled evaluations. That is usually the right trade for volume and freshness, and it is why the schema's schedule deserves more thought than a single table's.

<!-- ------------------------ -->
## Let Snowflake Propose the Checks

Cortex Data Quality reads a table's metadata and usage patterns and suggests checks, so you can start from a proposal rather than a blank page. It runs inside Snowflake using `AI_COMPLETE`, so the data and metadata do not leave your account, and it respects the access control of whoever is asking.

This one is Snowsight-only.

**Prerequisites, which are the usual reason it does not appear:**

- The `CORTEX_MODELS_ALLOWLIST` account parameter must permit `mistral-7b`. Many accounts do not by default, and this is the most common cause of the feature being unavailable.
- The user needs the `SNOWFLAKE.CORTEX_USER` database role. It is granted to `PUBLIC` by default, so this is usually already true — unless your account has deliberately revoked it.

```sql
-- Run as an account administrator if suggestions are unavailable
ALTER ACCOUNT SET CORTEX_MODELS_ALLOWLIST = 'mistral-7b';
```

Then:

1. Open **Data » Databases » DQ_EXAMPLES » PUBLIC » SENSOR_READINGS**.
2. Open the **Data Quality** tab.
3. Select **Add quality check**, then **Suggested quality checks**.
4. Review each suggestion and edit the expected values before accepting. Accepting a suggestion creates a real, billed, scheduled check.

<!-- TODO: screenshot of the Suggested quality checks panel listing AI-proposed checks for SENSOR_READINGS, with the expectation values editable -->

Treat the suggestions as a first draft. The model is working from metadata and usage, not from your business rules — it can see that `BATTERY_PCT` is numeric and mostly between 60 and 100, but not that `-1` means "unknown". The judgement about what counts as a defect stays yours; what this saves is the blank page.

To stop anyone in the account using it:

```sql
REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_USER FROM ROLE PUBLIC;
```

<!-- ------------------------ -->
## Let Snowflake Learn Normal

Every check so far required you to name a threshold. For volume and freshness that is genuinely hard: the right row count for a Tuesday is not the right row count for a bank holiday, and any number you pick is wrong somewhere.

Anomaly detection learns the pattern from history and flags departures from it.

```sql
ALTER TABLE SENSOR_READINGS
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON ()
    ANOMALY_DETECTION = TRUE;
```

Enable it on an association that already exists:

```sql
ALTER TABLE SENSOR_READINGS
    MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON ()
    SET ANOMALY_DETECTION = TRUE;
```

Anomaly detection is a **preview feature**, open to all Enterprise accounts. Four things to know before relying on it:

- It supports **volume and freshness only** — `ROW_COUNT` and `FRESHNESS`. There is no anomaly detection for null rates or distributions.
- It needs a **training period**. Until enough history accumulates it has no basis for a prediction, so a table you created this morning will not produce anomaly results this afternoon.
- `SENSITIVITY` tunes how far outside the predicted range a value must fall before it is flagged. Start loose and tighten; a sensitive detector on a noisy pipeline is another alert people learn to ignore.
- The anomaly check runs on its own cadence, independent of the table's metric schedule.

Anomaly detection can also be enabled across a whole schema in one statement, which is the natural pairing with the previous section:

```sql
ALTER SCHEMA PUBLIC
    ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON ()
    ANOMALY_DETECTION = TRUE;
```

Use expectations for rules that are true by definition — a key is unique, a required field is populated. Use anomaly detection for quantities that have a normal range you would struggle to write down.

<!-- ------------------------ -->
## Find the Bad Rows

A count tells you something is wrong. Fixing it needs the rows.

`SYSTEM$DATA_METRIC_SCAN` returns the records that fail a check:

```sql
SELECT * FROM TABLE(SYSTEM$DATA_METRIC_SCAN(
    REF_ENTITY_NAME => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
    METRIC_NAME     => 'SNOWFLAKE.CORE.NULL_COUNT',
    ARGUMENT_NAME   => 'TEMPERATURE_C'));
```

Returns reading 1016 — the row itself, which you can insert into a quarantine table, hand to the source team, or correct in place.

For `ACCEPTED_VALUES` the scan needs the same Boolean expression, passed as `ARGUMENT_EXPRESSION`:

```sql
SELECT * FROM TABLE(SYSTEM$DATA_METRIC_SCAN(
    REF_ENTITY_NAME      => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
    METRIC_NAME          => 'SNOWFLAKE.CORE.ACCEPTED_VALUES',
    ARGUMENT_NAME        => 'STATUS_CODE',
    ARGUMENT_EXPRESSION  => 'STATUS_CODE IN (''OK'', ''WARN'')'));
```

Add `AT_TIMESTAMP` to scan the table as it was at a point in time, and `WITHIN_GROUP_VALUES` to narrow a grouped association to one group.

### Reading the two result surfaces

Measurements — every metric value, whether or not it has an expectation:

```sql
SELECT MEASUREMENT_TIME, METRIC_NAME, VALUE
FROM TABLE(SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS(
    REF_ENTITY_NAME   => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
    REF_ENTITY_DOMAIN => 'TABLE'))
ORDER BY MEASUREMENT_TIME DESC;
```

Verdicts — pass or fail per expectation:

```sql
SELECT MEASUREMENT_TIME, METRIC_NAME, EXPECTATION_NAME, VALUE, EXPECTATION_VIOLATED
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
WHERE TABLE_NAME = 'SENSOR_READINGS'
ORDER BY MEASUREMENT_TIME DESC;
```

Use the second for "what is failing". Do not reconstruct pass and fail by joining measurements to expectation definitions yourself — the status surface exists for it, and it already knows how each expression was evaluated.

Note there is no `SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_RESULTS`. Measurements live in `SNOWFLAKE.LOCAL`, and reaching for the `ACCOUNT_USAGE` name is a common false start.

**In Snowsight**, the same information is on the table's **Data Quality** tab, and the account-wide monitoring dashboard rolls it up across databases. The dashboard is in preview.

<!-- TODO: screenshot of the account-wide data quality monitoring dashboard showing failing checks across databases -->

For blast radius, pair a violation with lineage: **Impacted Assets** on the table's page shows what reads from it, which tells you who is consuming the bad rows while you fix them.

<!-- ------------------------ -->
## Get Told, Don't Watch

A dashboard only works if someone looks at it. Notifications invert that.

Create the destination — email:

```sql
CREATE NOTIFICATION INTEGRATION DQ_EMAIL_INT
    TYPE = EMAIL
    ENABLED = TRUE
    ALLOWED_RECIPIENTS = ('you@example.com');
```

Or a webhook, for Slack and similar:

```sql
CREATE OR REPLACE SECRET SLACK_WEBHOOK_SECRET
    TYPE = GENERIC_STRING
    SECRET_STRING = 'T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX';

CREATE OR REPLACE NOTIFICATION INTEGRATION DQ_SLACK_INT
    TYPE = WEBHOOK
    ENABLED = TRUE
    WEBHOOK_URL = 'https://hooks.slack.com/services/SNOWFLAKE_WEBHOOK_SECRET'
    WEBHOOK_SECRET = DQ_EXAMPLES.PUBLIC.SLACK_WEBHOOK_SECRET
    WEBHOOK_BODY_TEMPLATE = '{"text": "SNOWFLAKE_WEBHOOK_MESSAGE"}'
    WEBHOOK_HEADERS = ('Content-Type' = 'application/json');
```

Then switch notifications on for the database. The settings are YAML in a dollar-quoted string:

```sql
ALTER DATABASE DQ_EXAMPLES SET DATA_QUALITY_MONITORING_SETTINGS =
$$
notification:
  enabled: TRUE
  email_recipients: [ 'you@example.com' ]
  integrations:
    - DQ_SLACK_INT
  cooldown_hours: 24
  metadata_included: TRUE
$$;
```

`cooldown_hours` is the setting that decides whether anyone keeps reading these. A check evaluating hourly against a violation that takes a week to fix sends 168 identical messages without it. `metadata_included` adds the table, metric and measured value to the message, which is the difference between a useful alert and one that only says something is wrong.

This is configured **per database**, not per check — so it applies to every violation in `DQ_EXAMPLES`. Opt a single noisy association out:

```sql
ALTER TABLE SENSOR_READINGS
    MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.AVG ON (TEMPERATURE_C)
    SET DATA_QUALITY_NOTIFICATION = FALSE;
```

Notify on checks that assert rules. Statistics metrics you are recording to build history should not be paging anyone.

<!-- ------------------------ -->
## Stop the Pipeline

Notifications tell a person. Sometimes you want the pipeline itself to stop, so bad data does not propagate while everyone sleeps.

The native notification settings cannot do this — they send messages, and have no action hook. For an action you need a Snowflake **alert**: a scheduled condition with a `THEN` clause. The condition reads expectation status; the action suspends whatever consumes the table.

Given a downstream consumer:

```sql
CREATE OR REPLACE TASK PUBLISH_READINGS
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '60 MINUTE'
AS
    SELECT COUNT(*) FROM SENSOR_READINGS;

ALTER TASK PUBLISH_READINGS RESUME;
```

The breaker:

```sql
CREATE OR REPLACE ALERT READINGS_CIRCUIT_BREAKER
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '5 MINUTE'
    IF (EXISTS (
        SELECT 1
        FROM TABLE(SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS(
            REF_ENTITY_NAME   => 'DQ_EXAMPLES.PUBLIC.SENSOR_READINGS',
            REF_ENTITY_DOMAIN => 'TABLE'))
        WHERE EXPECTATION_VIOLATED = TRUE
          AND MEASUREMENT_TIME >= DATEADD('HOUR', -24, CURRENT_TIMESTAMP())
    ))
    THEN
        ALTER TASK PUBLISH_READINGS SUSPEND;

ALTER ALERT READINGS_CIRCUIT_BREAKER RESUME;
```

The condition is deliberately not a threshold of its own. It asks whether any expectation you already defined has been violated, so the rules stay in one place and the breaker inherits them.

### Testing it without waiting

An alert is created suspended, and you do not want to wait for its schedule to find out whether it works. Three steps prove it:

```sql
-- 1. Record a violation, so there is something to react to
SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS_PERSIST_RESULT('SENSOR_READINGS'));

-- 2. Fire the alert immediately, bypassing its schedule
EXECUTE ALERT READINGS_CIRCUIT_BREAKER;

-- 3. Confirm the consumer stopped
SHOW TASKS LIKE 'PUBLISH_READINGS';
```

The task's `state` reads `suspended`, and `last_suspended_on` carries the moment the breaker fired. Check the alert's own outcome too:

```sql
SELECT SCHEDULED_TIME, STATE, SQL_ERROR_CODE, SQL_ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.ALERT_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('HOUR', -1, CURRENT_TIMESTAMP())))
WHERE NAME = 'READINGS_CIRCUIT_BREAKER'
ORDER BY SCHEDULED_TIME DESC;
```

`STATE` of `TRIGGERED` means the condition matched and the action ran. `ACTION_FAILED` means the condition matched and the `THEN` clause did not — the error column tells you why, and this is the failure worth checking for, because an alert whose action fails looks like an alert that fired.

Step 1 matters more than it appears. The plain `SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS` returns a result without recording it, so the status surface stays empty and the breaker has nothing to see. Use the `_PERSIST_RESULT` form when testing anything that reads monitoring history.

### Restarting after a fix

The breaker has no automatic reset, by design — a human decides the data is good again:

```sql
ALTER TASK PUBLISH_READINGS RESUME;
```

### What this pattern is and is not

It is **asynchronous**. The alert runs on a schedule, so a downstream task can run once more between the violation and the suspension. It reduces exposure rather than eliminating it, and Snowflake has no native "block the refresh until expectations pass". For a hard gate, run the quality check as a step inside the pipeline before the load, and branch on the result.

Three practical requirements: the alert's owner role needs `EXECUTE ALERT` on the account and `OPERATE` on whatever it suspends, and the alert must be resumed after creation or it never evaluates.

Point a breaker at checks that mean "the data is unusable", not at every check you have. Suspending a pipeline because a statistics metric drifted is worse than the drift.

<!-- ------------------------ -->
## Where to Put Your Checks

Given a bronze, silver and gold pipeline, the temptation is to check gold — it is what people see.

That is the layer where checks are least effective, and the reason is worth understanding. Suppose a reading arrives with an unknown device, like reading 1017. Silver joins readings to devices to enrich them; an inner join drops the orphan. Gold aggregates silver. So gold is *clean* — every row present is valid — and the check passes while data has been silently lost. **Gold passes precisely because the bad row was discarded.**

A layered approach:

| Layer | Check for | Why here |
|:------|:----------|:---------|
| Bronze (raw) | Nulls, formats, duplicates, orphans, clock skew, volume, freshness | The only place the defect still exists. Cheapest to fix, closest to the source. |
| Silver (conformed) | Referential integrity, grain uniqueness, row counts against bronze | Where joins and dedup happen, so where rows go missing |
| Gold (serving) | Business invariants and totals | Catches logic errors your row-level checks cannot see |

The general rule: **check where the defect exists, not where it hurts.** Bronze checks tell you what arrived broken; gold checks tell you your logic is wrong. Both are useful and they are not substitutes.

For the guide's dataset, that means the orphan check belongs on `SENSOR_READINGS`, not on any dashboard built over it.

<!-- ------------------------ -->
## Checks as Code

Everything so far has been imperative. For anything you intend to keep, put the checks in the same version-controlled definition as the table, so a quality rule arrives and changes through the same review as the schema.

Snowflake's declarative deployment model (DCM Projects) supports data metric functions and their expectations as first-class definitions, so a custom metric and its attachment live in the project file alongside the table they protect.

Two capabilities matter when you get there. Attaching a metric to a table you do not own requires the attachment to run with rights over the target, so the project needs an explicit executing role. And the deployment tooling can run every expectation as a **test step**, which turns quality from a dashboard into a release condition: the deployment fails when the data does not satisfy its own rules.

For the definition syntax, see the [DCM Projects file reference](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-files), which is the authority on what a project file supports.

The payoff is that a check becomes reviewable. A threshold change shows up as a diff, with an author and a reason, instead of being an `ALTER` someone ran once.

<!-- ------------------------ -->
## What It Costs and How to Watch It

Scheduled evaluations run on serverless compute and bill under the **Data Quality Monitoring** category. Three things are free: creating a metric, calling a metric directly in a `SELECT`, and any metric whose schedule is suspended.

What drives the bill is straightforward — number of associations, multiplied by evaluation frequency, multiplied by the work each evaluation does. A schema-level attachment across two hundred tables on an hourly schedule is 4,800 evaluations a day.

Track it:

```sql
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY
ORDER BY START_TIME DESC;
```

Across an organisation, `METERING_DAILY_HISTORY` carries the same spend with `SERVICE_TYPE = 'DATA_QUALITY_MONITORING'`.

Three habits keep it proportionate:

- **Match cadence to how fast you would act.** An hourly check on a table loaded daily buys nothing but twenty-three extra evaluations.
- **`TRIGGER_ON_CHANGES` instead of a clock**, where it fits — evaluate when data actually lands rather than on a timer.
- **Suspend rather than detach** while iterating: `SET DATA_METRIC_SCHEDULE = ''` keeps the checks and stops the spend. As covered earlier, `UNSET` does the opposite of what it looks like.

The account-wide monitoring dashboard is the fastest way to spot associations that fire constantly or never — both are candidates for removal, for opposite reasons.

<!-- ------------------------ -->
## Cleanup

One statement removes everything this guide created:

```sql
DROP DATABASE IF EXISTS DQ_EXAMPLES;
```

Dropping the database removes its tables, their associations, and any custom metrics defined in it. If you created notification integrations, they live at account level and outlive the database:

```sql
DROP INTEGRATION IF EXISTS DQ_EMAIL_INT;
DROP INTEGRATION IF EXISTS DQ_SLACK_INT;
```

To keep the data but stop the billing, suspend instead:

```sql
ALTER TABLE DQ_EXAMPLES.PUBLIC.SENSOR_READINGS SET DATA_METRIC_SCHEDULE = '';
```

<!-- ------------------------ -->
## Conclusion and Resources

Data quality monitoring in Snowflake is a small vocabulary applied with judgement. A metric measures, an expectation judges, a schedule decides how often, and everything else is choosing well.

### What to take away

- **Pick the metric from the column's shape.** The decision table near the front of this guide is the whole method.
- **Know which metrics can be called directly.** Column-argument metrics give an instant answer in a `SELECT`; zero-argument ones must be attached first.
- **One check is rarely enough.** Freshness alone was defeated by a single future-dated row. Checks that cover each other's blind spots are worth more than more checks.
- **Check where the defect exists**, not where it hurts. Gold passing is not evidence.
- **Scope with `FILTER`, don't loosen thresholds.** A rule that is exactly true on the rows that matter beats a tolerance that hides which rows failed.
- **Assert rules; learn ranges.** Expectations for what is true by definition, anomaly detection for quantities with a normal range you could not write down.
- **Notify with a cooldown**, or people will filter the alerts.
- **Keep checks in code**, so a threshold change is reviewable.

### Resources

- [Introduction to data quality checks](https://docs.snowflake.com/en/user-guide/data-quality-intro)
- [System data metric functions](https://docs.snowflake.com/en/user-guide/data-quality-system-dmfs)
- [Custom data metric functions](https://docs.snowflake.com/en/user-guide/data-quality-custom-dmfs)
- [Use SQL to work with expectations](https://docs.snowflake.com/en/user-guide/data-quality-expectations)
- [Apply data quality checks to a subset of rows](https://docs.snowflake.com/en/user-guide/data-quality-filter)
- [Apply data quality checks by group](https://docs.snowflake.com/en/user-guide/data-quality-group-by)
- [Monitor the data quality of a schema](https://docs.snowflake.com/en/user-guide/data-quality-schema-level)
- [Detecting anomalies in data quality](https://docs.snowflake.com/en/user-guide/data-quality-anomaly)
- [Sending notifications for data quality issues](https://docs.snowflake.com/en/user-guide/data-quality-notifications)
- [Remediation of data quality issues](https://docs.snowflake.com/en/user-guide/data-quality-fixing)
- [Use Snowsight to set up data quality checks](https://docs.snowflake.com/en/user-guide/data-quality-ui-setup)
- [Using the data quality monitoring dashboard](https://docs.snowflake.com/en/user-guide/data-quality-centralized-dashboard)
- [Access control for data quality](https://docs.snowflake.com/en/user-guide/data-quality-access-control)

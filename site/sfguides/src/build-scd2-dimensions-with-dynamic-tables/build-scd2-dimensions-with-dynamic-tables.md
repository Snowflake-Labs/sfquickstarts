author: Yoav Ostrinsky
id: build-scd2-dimensions-with-dynamic-tables
summary: Build a Slowly Changing Dimension Type 2 model on Dynamic Tables — stable surrogate keys without hashing, stored validity intervals, and dimensions that arrive after the facts.
categories: snowflake-site:taxonomy/product/data-engineering,snowflake-site:taxonomy/snowflake-feature/dynamic-tables
environments: web
status: Draft
language: en
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Dynamic Tables, Dimensional Modeling, SCD2, Data Engineering, Custom Incrementalization

# Build SCD Type 2 Dimensions with Dynamic Tables
<!-- ------------------------ -->
## Overview

A Type 2 dimension keeps history. When a customer moves from `SILVER` to `GOLD`, you do not overwrite the row — you close the old version and open a new one, so a fact recorded last quarter still points at who that customer was last quarter.

Doing this on Dynamic Tables runs into three problems that are not obvious until you hit them, and all three fail *quietly*. Snowflake accepts the definition, reports success, and then does something other than what you intended.

This guide builds the model, and deliberately builds the broken versions alongside it so you can see each failure rather than take it on trust.

### What you will learn

- Why `UUID_STRING()` churns keys in one kind of dynamic table and is perfectly stable in another — and why the refresh mode is not the real problem
- What `dbt_utils.generate_surrogate_key` does, in plain SQL, and when you do not need it
- How to assign a stable surrogate key without hashing and without a sequence
- How to perform an SCD2 close-and-open in a single DML statement
- How to store `valid_to` rather than derive it, and how to prove the stored value is right
- How to bind facts to a dimension version at load time or at event time, and why one of those belongs inside the refresh
- How to handle a fact that arrives before its dimension row exists, without orphaning it
- How to read `refresh_mode`, `refresh_mode_reason` and refresh statistics as an instrument panel

### What you will need

- A Snowflake account, and a role that can create databases
- A warehouse. The SQL below uses `COMPUTE_WH`; substitute your own name throughout if it differs
- Familiarity with dimensional modelling vocabulary — surrogate key, business key, fact, dimension

### How to use this guide

The sections build on each other, so run them in order the first time. Everything is inline SQL; there is no repository to clone. The three deliberately-broken objects live in their own schema and are labelled, so you can skip them without breaking the working model.

<!-- ------------------------ -->
## Set Up the Example Data

One database, three schemas, three source tables. No sequences and no key
generators of any kind — the reason why is the subject of the next two sections.

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;

CREATE OR REPLACE DATABASE SCD2_DEMO
    COMMENT = 'Worked example: SCD Type 2 dimensions on Dynamic Tables. Drop when finished.';
CREATE OR REPLACE SCHEMA SCD2_DEMO.RAW
    COMMENT = 'Source tables, updated in place. SCD2 history is derived downstream.';
CREATE OR REPLACE SCHEMA SCD2_DEMO.CORE
    COMMENT = 'The working model: SCD2 dimensions and fact tables.';
CREATE OR REPLACE SCHEMA SCD2_DEMO.CONTROL
    COMMENT = 'Deliberately broken objects, kept apart from the working model so they are never mistaken for it.';
```

Any role that can create a database will do; `ACCOUNTADMIN` is used here only so the guide runs without further setup. Setting the role explicitly matters — without it the first statement fails for anyone whose default role cannot create databases.

The source tables need `CHANGE_TRACKING = TRUE`, because the dimensions read them through `CHANGES()`.

`DATA_RETENTION_TIME_IN_DAYS` is set to 14 deliberately. A dynamic table suspended for longer than its base tables' retention window cannot resume — the change history it needs has aged out, and the only remedy is to recreate it, which for a Type 2 dimension means losing every version you accumulated.

Pick that number by how long the pipeline might realistically sit idle, not by the shortest pause you can imagine. The default of 1 day does not survive a weekend, and 3 does not survive a public holiday or a paused project — this example was itself parked for five days during development and survived only because retention had been raised beforehand.

```sql
USE SCHEMA SCD2_DEMO.RAW;

CREATE OR REPLACE TABLE CUSTOMER_SRC (
    CUST_CODE     STRING NOT NULL,
    CUST_NAME     STRING,
    TIER          STRING,
    COUNTRY       STRING,
    SRC_LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP())
    CHANGE_TRACKING = TRUE
    DATA_RETENTION_TIME_IN_DAYS = 14
    COMMENT = 'Customer dimension source. Updated in place; SCD2 history is derived downstream.';

CREATE OR REPLACE TABLE PRODUCT_SRC (
    PROD_CODE     STRING NOT NULL,
    PROD_NAME     STRING,
    CATEGORY      STRING,
    LIST_PRICE    NUMBER(12,2),
    SRC_LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP())
    CHANGE_TRACKING = TRUE
    DATA_RETENTION_TIME_IN_DAYS = 14
    COMMENT = 'Product dimension source. Updated in place; SCD2 history is derived downstream.';

CREATE OR REPLACE TABLE SALES_SRC (
    SALE_ID       NUMBER NOT NULL,
    CUST_CODE     STRING NOT NULL,
    PROD_CODE     STRING NOT NULL,
    QTY           NUMBER,
    AMOUNT        NUMBER(12,2),
    EVENT_TS      TIMESTAMP_NTZ,
    SRC_LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP())
    CHANGE_TRACKING = TRUE
    DATA_RETENTION_TIME_IN_DAYS = 14
    COMMENT = 'Sales fact source, append-only. May reference dimension members that do not exist yet.';
```

Seed four customers and three products. Keep it small — version history is only legible on screen if the tables are tiny.

```sql
INSERT INTO CUSTOMER_SRC (CUST_CODE, CUST_NAME, TIER, COUNTRY) VALUES
    ('ACME-JP-001','Acme Interactive KK','PLATINUM','JP'),
    ('ACME-JP-002','Acme Media Japan','GOLD','JP'),
    ('ACME-UK-010','Acme Europe BV','SILVER','GB'),
    ('ACME-US-020','Acme Studios Inc','GOLD','US');

INSERT INTO PRODUCT_SRC (PROD_CODE, PROD_NAME, CATEGORY, LIST_PRICE) VALUES
    ('HDPH-100','Wireless Headphones','AUDIO',379.00),
    ('CONS-200','Games Console','CONSOLE',479.00),
    ('CAM-300','Mirrorless Camera','IMAGING',3899.00);
```

Note there is no customer in Germany. A later section lands a sale for one, before that customer exists.

<!-- ------------------------ -->
## Why UUID_STRING() Churns Keys — and Where It Does Not

This is where most people start, so it is worth seeing fail. Keep the failure in
mind, though, because later in this guide the working dimension calls **this exact
function** and its keys never move. The difference is not the function. It is
where the function sits.

```sql
CREATE OR REPLACE DYNAMIC TABLE SCD2_DEMO.CONTROL.DT_UUID_KEY
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'NEGATIVE CONTROL: UUID_STRING in a standard dynamic table SELECT. Deliberately broken -- downgrades to FULL and churns every key.'
    AS
SELECT UUID_STRING() AS CUST_SK, CUST_CODE, CUST_NAME, TIER
FROM SCD2_DEMO.RAW.CUSTOMER_SRC;
```

Read the success message, not just the fact that it succeeded:

```
Dynamic table DT_UUID_KEY successfully created. FULL refresh mode was selected
because: Query contains the function 'UUID_STRING', but change tracking is not
supported on queries with non-deterministic functions.
```

It did not fail. It was accepted and quietly downgraded, and that sentence is the only place Snowflake says so. A team can ship this and never read it.

The refresh mode is not the real damage, though. Capture the keys, then change **one unrelated row**:

```sql
CREATE OR REPLACE TABLE SCD2_DEMO.CONTROL.UUID_SNAPSHOT
    COMMENT = 'Before-snapshot of DT_UUID_KEY keys, used to prove they churn.'
    AS
SELECT CUST_CODE, CUST_SK FROM SCD2_DEMO.CONTROL.DT_UUID_KEY;

INSERT INTO SCD2_DEMO.RAW.CUSTOMER_SRC (CUST_CODE, CUST_NAME, TIER, COUNTRY)
    VALUES ('ACME-CTRL-99','Control Row Ltd','BRONZE','XX');

ALTER DYNAMIC TABLE SCD2_DEMO.CONTROL.DT_UUID_KEY REFRESH;
```

```sql
SELECT S.CUST_CODE, S.CUST_SK AS SK_BEFORE, D.CUST_SK AS SK_AFTER,
       IFF(S.CUST_SK = D.CUST_SK, 'stable', 'CHURNED') AS VERDICT
FROM SCD2_DEMO.CONTROL.UUID_SNAPSHOT S
JOIN SCD2_DEMO.CONTROL.DT_UUID_KEY D ON D.CUST_CODE = S.CUST_CODE
ORDER BY S.CUST_CODE;
```

| CUST_CODE | SK_BEFORE | SK_AFTER | VERDICT |
|:---|:---|:---|:---|
| ACME-JP-001 | eac0f5e9-... | 4145edaf-... | CHURNED |
| ACME-JP-002 | edda74e1-... | 539017c4-... | CHURNED |
| ACME-UK-010 | 2b237fc5-... | 0945ac66-... | CHURNED |
| ACME-US-020 | 7cd0dde3-... | 4caf97ab-... | CHURNED |

Every pre-existing key changed, because a FULL refresh recomputes the whole table and `UUID_STRING()` returns something different each time it is evaluated. Every fact foreign key pointing into this dimension is now dangling — and it will happen again on the next refresh, and the one after.

For a Type 2 dimension this is fatal rather than untidy. Version identity *is* the pattern. If the key that identifies a version is not stable, there is no history, only a table that changes shape.

The conclusion to draw is narrower than "do not use `UUID_STRING()`". The correct
conclusion is **do not put a non-deterministic function anywhere that gets
recomputed.** A standard dynamic table's `SELECT` list is recomputed. Hold that
thought.

One piece of bookkeeping before moving on. This section inserted `ACME-CTRL-99` into the *real* source table, so if you are working through the guide in order it will appear in the working dimension you build next, alongside the four business customers. It is harmless — every query below filters by a specific business key, and the validation checks treat it as a legitimate member because structurally it is one. If you would rather keep the working model clean, delete it now:

```sql
DELETE FROM SCD2_DEMO.RAW.CUSTOMER_SRC WHERE CUST_CODE = 'ACME-CTRL-99';
```

Do that before creating `DIM_CUSTOMER`, not after — once the dimension has minted a version for it, removing the source row leaves the version behind, which is the whole point of a Type 2 dimension.

<!-- ------------------------ -->
## What generate_surrogate_key Actually Does

The usual answer to the churn above is `dbt_utils.generate_surrogate_key`. It is worth knowing what it expands to, because it is short and it explains itself:

```sql
MD5(CONCAT_WS('-',
    COALESCE(CAST(CUST_CODE AS VARCHAR), '_dbt_utils_surrogate_key_null_'),
    COALESCE(CAST(COUNTRY   AS VARCHAR), '_dbt_utils_surrogate_key_null_')))
```

Three details in there are doing real work. Casting everything to text makes the hash type-independent. The NULL sentinel stops a genuine `NULL` colliding with the literal string `'NULL'`. The separator stops `('a','bc')` and `('ab','c')` hashing to the same value.

The important property is that it is a **pure function of the business columns**. The same inputs always produce the same key, so it survives a FULL refresh where `UUID_STRING()` cannot. That is the whole reason it works, and it has nothing to do with dbt — it is one SQL expression you can paste into any query.

This guide takes a third road: it keeps `UUID_STRING()` but moves it somewhere it
is only ever evaluated once. That avoids hashing entirely, for teams that would
rather not have a hash-collision conversation, and needs no sequence object. The
cost of that choice is real and is spelled out in the late-arriving section.

<!-- ------------------------ -->
## The One-DML Problem

Choosing where the key is generated only solves the churn in the right kind of dynamic table. Consider what an SCD2 change actually requires:

1. **Close** the outgoing version — set its `VALID_TO` and clear `IS_CURRENT`
2. **Open** the incoming version — insert a new row with a new surrogate key

That is two actions against one target, driven by one source row. A plain `MERGE` cannot do it: a given source row either matches a target row and updates it, or does not match and inserts. Not both.

Custom incrementalization permits **exactly one** DML statement in `REFRESH USING`. So the naive "SCD2 is just a MERGE" instinct is structurally blocked.

The way through is to stop asking the `MERGE` to decide anything. Let the `USING` subquery work out what *should* happen and emit **one row per intended action**, then let the `MERGE` do nothing but apply them:

| Emitted op | Matches an existing row? | Effect |
|:---|:---|:---|
| `CLOSE` | yes | Stamp `VALID_TO`, set `IS_CURRENT = FALSE` |
| `OPEN` | never | Insert a new version with a fresh key |
| `FIXUP` | yes | Correct attributes in place, keep the key |

This is also the reason `UUID_STRING()` is safe here at all. Custom incremental dynamic tables are **imperative**: rows persist in `SELF` and are never recomputed. A value that is non-deterministic — `UUID_STRING()`, `CURRENT_TIMESTAMP()` — is evaluated once when the row is inserted and then frozen. Non-determinism only causes trouble where recomputation happens, which is exactly why the same expression that destroys the standard dynamic table above is safe here.

So stability comes from **write-once placement, not from determinism.** A hash key
is stable because it is a pure function of its inputs; a key minted inside
`REFRESH USING` is stable because nothing ever recomputes it. Both work. They are
different mechanisms, and only the second one lets you keep a random key.

<!-- ------------------------ -->
## Build the SCD2 Dimension

Start with the product dimension, which has no late-arriving complication.

```sql
USE SCHEMA SCD2_DEMO.CORE;

CREATE OR REPLACE DYNAMIC TABLE CORE.DIM_PRODUCT (
    PROD_SK    STRING,
    PROD_CODE  STRING,
    PROD_NAME  STRING,
    CATEGORY   STRING,
    LIST_PRICE NUMBER(12,2),
    VALID_FROM TIMESTAMP_NTZ,
    VALID_TO   TIMESTAMP_NTZ,
    IS_CURRENT BOOLEAN)
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'SCD2 product dimension. Random surrogate key minted once per version, stored valid_to. No inferred-member path -- see the late-arriving section.'
    REFRESH USING (
        MERGE INTO SELF AS TGT
        USING (
            WITH DIM_CHG AS (
                SELECT PROD_CODE, PROD_NAME, CATEGORY, LIST_PRICE
                FROM SCD2_DEMO.RAW.PRODUCT_SRC CHANGES(INFORMATION => DEFAULT)
                WHERE METADATA$ACTION = 'INSERT'
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY PROD_CODE ORDER BY SRC_LOADED_AT DESC NULLS LAST) = 1),
            CUR AS (
                SELECT PROD_CODE, PROD_NAME, CATEGORY, LIST_PRICE
                FROM SELF WHERE IS_CURRENT),
            DECIDED AS (
                SELECT D.PROD_CODE, D.PROD_NAME, D.CATEGORY, D.LIST_PRICE,
                       CASE WHEN C.PROD_CODE IS NULL THEN 'NEW'
                            WHEN C.PROD_NAME  IS DISTINCT FROM D.PROD_NAME
                              OR C.CATEGORY   IS DISTINCT FROM D.CATEGORY
                              OR C.LIST_PRICE IS DISTINCT FROM D.LIST_PRICE THEN 'VERSION'
                            ELSE 'NOCHANGE' END AS ACTION
                FROM DIM_CHG D LEFT JOIN CUR C ON C.PROD_CODE = D.PROD_CODE)
            SELECT 'CLOSE' AS OP, PROD_CODE, PROD_NAME, CATEGORY, LIST_PRICE,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS CHANGE_AT,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS VF
            FROM DECIDED WHERE ACTION = 'VERSION'
            UNION ALL
            SELECT 'OPEN', PROD_CODE, PROD_NAME, CATEGORY, LIST_PRICE,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
                   CASE WHEN ACTION = 'NEW' THEN '1900-01-01'::TIMESTAMP_NTZ
                        ELSE CURRENT_TIMESTAMP()::TIMESTAMP_NTZ END
            FROM DECIDED WHERE ACTION IN ('VERSION','NEW')) AS SRC
        ON  TGT.PROD_CODE = SRC.PROD_CODE
        AND TGT.IS_CURRENT = TRUE
        AND SRC.OP = 'CLOSE'
        WHEN MATCHED THEN
            UPDATE SET TGT.VALID_TO = SRC.CHANGE_AT, TGT.IS_CURRENT = FALSE
        WHEN NOT MATCHED AND SRC.OP = 'OPEN' THEN
            INSERT (PROD_SK, PROD_CODE, PROD_NAME, CATEGORY, LIST_PRICE,
                    VALID_FROM, VALID_TO, IS_CURRENT)
            VALUES (UUID_STRING(), SRC.PROD_CODE, SRC.PROD_NAME,
                    SRC.CATEGORY, SRC.LIST_PRICE, SRC.VF, NULL, TRUE));
```

Four things in that statement are load-bearing. Changing any of them silently breaks the model rather than raising an error, which is why they are worth reading rather than copying.

**`SRC.OP = 'CLOSE'` sits in the `ON` clause, not in a `WHEN` clause.** This is the pivot the whole pattern turns on. In the `ON` clause it prevents an `OPEN` row from ever matching, so `OPEN` rows are guaranteed to reach the `INSERT` branch. Moved into a `WHEN`, the `OPEN` row can match the current version, the close and the open collapse into one another, and you get a dimension that updates in place — Type 1 behaviour wearing a Type 2 schema.

**`WHEN NOT MATCHED AND SRC.OP = 'OPEN'` needs its guard.** A brand-new business key has no current row, so its `CLOSE` row does not match either. Without the guard it falls into the `INSERT` branch and writes a duplicate version.

**`QUALIFY ROW_NUMBER()` deduplicates the change set.** If several source rows match one target row, `MERGE` results are non-deterministic. Reducing the changes to one row per business key per refresh is what makes the outcome defined. `SRC_LOADED_AT` is the ordering column; a real CDC feed always carries one, and without it there is no defensible notion of which change came last.

**A member's first version opens at `1900-01-01`, not at load time.** Any fact whose event timestamp predates the dimension's initial load would otherwise find no covering version and bind to `NULL` — orphaning every fact older than the day you built the warehouse. This is the standard treatment for an initial load, and it is easy to miss because it only shows up when you test with backdated data.

Confirm the resolved mode:

```sql
SHOW DYNAMIC TABLES LIKE 'DIM_PRODUCT' IN SCHEMA SCD2_DEMO.CORE;
```

`REFRESH_MODE` reads `CUSTOM_INCREMENTAL` and `REFRESH_MODE_REASON` is empty. No downgrade — from a definition that calls the same `UUID_STRING()` which downgraded the standard dynamic table earlier. Compare the two `CREATE` messages directly; that contrast is the single most useful thing in this guide.

<!-- ------------------------ -->
## See a Version Open and Close

Change a price. Set `SRC_LOADED_AT` explicitly — it is the ordering column the deduplication depends on.

```sql
UPDATE SCD2_DEMO.RAW.PRODUCT_SRC
    SET LIST_PRICE = 429.00, SRC_LOADED_AT = CURRENT_TIMESTAMP()
    WHERE PROD_CODE = 'HDPH-100';

ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_PRODUCT REFRESH;
```

The refresh statistics are the first place to look, before the data:

```
{"insertedRows":1,"copiedRows":2,"deletedRows":0,"updatedRows":1}
```

One row inserted (the new version), one updated (the old one being closed), nothing deleted, and the two products the change did not concern **copied** rather than rewritten. Compare that with the UUID control earlier, where an unrelated change deleted and recreated everything. `copiedRows` is what identity stability looks like in the statistics, and `deletedRows` staying at zero is what you want to see on a change that only affects one member.

```sql
SELECT PROD_SK, PROD_CODE, LIST_PRICE, VALID_FROM, VALID_TO, IS_CURRENT
FROM SCD2_DEMO.CORE.DIM_PRODUCT WHERE PROD_CODE = 'HDPH-100' ORDER BY VALID_FROM;
```

| PROD_SK | PROD_CODE | LIST_PRICE | VALID_FROM | VALID_TO | IS_CURRENT |
|:---|:---|:---|:---|:---|:---|
| 7540aa7f-527e-4c66-ad61-7af4fbe37cc5 | HDPH-100 | 379.00 | 1900-01-01 00:00:00 | 2026-09-11 05:02:55.122 | FALSE |
| 40763a2a-d028-412a-8e2f-0370918816e7 | HDPH-100 | 429.00 | 2026-09-11 05:02:55.122 | NULL | TRUE |

The old version's `VALID_TO` and the new version's `VALID_FROM` are the same instant. The intervals abut exactly — no gap that loses a fact, no overlap that double-counts one.

**On the keys:** both versions carry a random UUID, and yours will differ from any
value printed here — that is the nature of the key, not an inconsistency. Nothing
in this model depends on keys being adjacent, ordered, or meaningful; the integrity
checks later in this guide assert that they are **unique**, never that they are
sequential. If you want narrower keys for a large fact table, `UUID_STRING()::BINARY(16)`
is the usual compromise — it prunes and clusters better at the cost of legibility.

### What happens to changes inside one refresh window

Change the same key twice before a refresh and you get **one** version carrying the final value, not two versions.

It is worth being precise about *why*, because the obvious explanation is wrong. It is not the deduplication choosing a winner. For a source updated in place, `CHANGES()` returns the **net** change over the window, exactly like a stream. Update a key `BRONZE → SILVER → GOLD` inside one window and `CHANGES()` returns only two rows:

```
C1 | BRONZE | DELETE | METADATA$ISUPDATE = TRUE     <- pre-window value
C1 | GOLD   | INSERT | METADATA$ISUPDATE = TRUE     <- final value
```

`SILVER` is absent. Be precise about what that means, though: the value has **not** been destroyed. Time Travel still holds it for the whole retention window. This one is not copy-pasteable — substitute an actual timestamp from between your two updates, since `AT()` will not accept an expression:

```sql
-- Substitute a real timestamp; this will not run as written.
SELECT TIER FROM SCD2_DEMO.RAW.CUSTOMER_SRC
    AT(TIMESTAMP => '2026-01-01 12:00:00 +0000'::TIMESTAMP_TZ);
-- returns the intermediate value that CHANGES() did not show you
```

It is simply **unreachable from a dynamic table**. `CHANGES()` reports net change, and `AT()` requires a *constant* timestamp (`argument TIMESTAMP to function AT needs to be constant`). A dynamic table has no loops and no procedural logic, so it can neither derive nor enumerate the intermediate timestamps. The `QUALIFY` in the dimension is a defensive guard, not the mechanism that drops the value.

The practical consequence: from a source updated in place, a dynamic table observes exactly **one transition** per key per window — old value to new value — and one transition justifies exactly one new version. A shorter `TARGET_LAG` shrinks the window but never closes it: two updates inside the one-minute floor still collapse. Your history granularity is bounded by `TARGET_LAG`, and that is a property of net-change semantics rather than a defect in the model.

If you need every intermediate state, the change has to be captured as **its own row** before it reaches a table that is updated in place — an append-only feed. Given such a source, a single `MERGE` can insert a complete version chain in one refresh: `LEAD()` over the incoming changes supplies each version's `VALID_TO`, so intermediate versions land already closed and only the newest stays open.

It is worth asking where the collapse actually happens in your own pipeline. If changes arrive by CDC and are then `MERGE`d into a snapshot table, the intermediate states are being discarded upstream — before any dynamic table is involved. That is a change to the **source contract**, not to the dimension.

<!-- ------------------------ -->
## Handle Dimensions That Arrive After the Facts

A sale references a customer that is not in the dimension yet. The fact cannot be dropped, and it cannot carry a `NULL` key without disappearing from every report that joins on the dimension.

With a hash key this problem largely evaporates: the fact computes the dimension's key *itself* from the business columns it already carries, and binds before the dimension row exists. Any **minted** key — random or sequential — removes that option, because the key is only knowable by looking it up.

So the dimension has to mint it. `DIM_CUSTOMER` reads `CHANGES()` from **both** its own source **and the sales table**. An unknown business key seen on a fact causes the dimension to create an **inferred member** for it, which gives the fact something real to point at immediately.

```sql
CREATE OR REPLACE DYNAMIC TABLE CORE.DIM_CUSTOMER (
    CUST_SK     STRING,
    CUST_CODE   STRING,
    CUST_NAME   STRING,
    TIER        STRING,
    COUNTRY     STRING,
    IS_INFERRED BOOLEAN,
    VALID_FROM  TIMESTAMP_NTZ,
    VALID_TO    TIMESTAMP_NTZ,
    IS_CURRENT  BOOLEAN)
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'SCD2 customer dimension. Random surrogate key minted once per version, stored valid_to, plus inferred members so a fact never binds to NULL.'
    REFRESH USING (
        MERGE INTO SELF AS TGT
        USING (
            WITH DIM_CHG AS (
                SELECT CUST_CODE, CUST_NAME, TIER, COUNTRY
                FROM SCD2_DEMO.RAW.CUSTOMER_SRC CHANGES(INFORMATION => DEFAULT)
                WHERE METADATA$ACTION = 'INSERT'
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY CUST_CODE ORDER BY SRC_LOADED_AT DESC NULLS LAST) = 1),
            FACT_KEYS AS (
                SELECT DISTINCT CUST_CODE
                FROM SCD2_DEMO.RAW.SALES_SRC CHANGES(INFORMATION => DEFAULT)
                WHERE METADATA$ACTION = 'INSERT'),
            CUR AS (
                SELECT CUST_CODE, CUST_SK, CUST_NAME, TIER, COUNTRY, IS_INFERRED
                FROM SELF WHERE IS_CURRENT),
            DECIDED AS (
                SELECT D.CUST_CODE, D.CUST_NAME, D.TIER, D.COUNTRY,
                       CASE WHEN C.CUST_CODE IS NULL THEN 'NEW'
                            WHEN C.IS_INFERRED       THEN 'FIXUP'
                            WHEN C.CUST_NAME IS DISTINCT FROM D.CUST_NAME
                              OR C.TIER      IS DISTINCT FROM D.TIER
                              OR C.COUNTRY   IS DISTINCT FROM D.COUNTRY THEN 'VERSION'
                            ELSE 'NOCHANGE' END AS ACTION
                FROM DIM_CHG D LEFT JOIN CUR C ON C.CUST_CODE = D.CUST_CODE),
            INFERRED AS (
                SELECT F.CUST_CODE
                FROM FACT_KEYS F
                LEFT JOIN CUR     C ON C.CUST_CODE = F.CUST_CODE
                LEFT JOIN DIM_CHG D ON D.CUST_CODE = F.CUST_CODE
                WHERE C.CUST_CODE IS NULL AND D.CUST_CODE IS NULL)
            SELECT 'CLOSE' AS OP, CUST_CODE, CUST_NAME, TIER, COUNTRY,
                   FALSE AS MK_INFERRED,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS CHANGE_AT,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS VF
            FROM DECIDED WHERE ACTION = 'VERSION'
            UNION ALL
            SELECT 'OPEN', CUST_CODE, CUST_NAME, TIER, COUNTRY, FALSE,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
                   CASE WHEN ACTION = 'NEW' THEN '1900-01-01'::TIMESTAMP_NTZ
                        ELSE CURRENT_TIMESTAMP()::TIMESTAMP_NTZ END
            FROM DECIDED WHERE ACTION IN ('VERSION','NEW')
            UNION ALL
            SELECT 'FIXUP', CUST_CODE, CUST_NAME, TIER, COUNTRY, FALSE,
                   CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
            FROM DECIDED WHERE ACTION = 'FIXUP'
            UNION ALL
            SELECT 'OPEN', CUST_CODE, '(inferred - awaiting dimension)', 'UNKNOWN', '??',
                   TRUE, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, '1900-01-01'::TIMESTAMP_NTZ
            FROM INFERRED) AS SRC
        ON  TGT.CUST_CODE = SRC.CUST_CODE
        AND TGT.IS_CURRENT = TRUE
        AND SRC.OP IN ('CLOSE','FIXUP')
        WHEN MATCHED AND SRC.OP = 'CLOSE' THEN
            UPDATE SET TGT.VALID_TO = SRC.CHANGE_AT, TGT.IS_CURRENT = FALSE
        WHEN MATCHED AND SRC.OP = 'FIXUP' THEN
            UPDATE SET TGT.CUST_NAME = SRC.CUST_NAME, TGT.TIER = SRC.TIER,
                       TGT.COUNTRY = SRC.COUNTRY, TGT.IS_INFERRED = FALSE
        WHEN NOT MATCHED AND SRC.OP = 'OPEN' THEN
            INSERT (CUST_SK, CUST_CODE, CUST_NAME, TIER, COUNTRY,
                    IS_INFERRED, VALID_FROM, VALID_TO, IS_CURRENT)
            VALUES (UUID_STRING(), SRC.CUST_CODE, SRC.CUST_NAME,
                    SRC.TIER, SRC.COUNTRY, SRC.MK_INFERRED, SRC.VF, NULL, TRUE));
```

The `FIXUP` branch is the part that makes this work. When the real customer row eventually arrives for a member that is currently inferred, it is **not** treated as a new version — the placeholder is corrected in place and keeps its key. That is deliberate: the placeholder never described reality, so superseding it would create a version representing nothing. Correcting it means the key the fact bound to stays valid, and **no fact is ever rebound**.

<!-- ------------------------ -->
## Bind Facts to a Dimension Version

Two different questions get conflated here, so build both answers.

**Load-time binding** asks *who is this customer now*. **Event-time binding** asks *who were they when this happened*. Neither is wrong; shipping one while believing you have the other is.

```sql
CREATE OR REPLACE DYNAMIC TABLE CORE.FACT_SALES_LOADTIME (
    SALE_ID NUMBER, CUST_SK STRING, PROD_SK STRING,
    CUST_CODE STRING, PROD_CODE STRING,
    QTY NUMBER, AMOUNT NUMBER(12,2), EVENT_TS TIMESTAMP_NTZ,
    BOUND_AT TIMESTAMP_NTZ)
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'Sales fact, LOAD-TIME binding: each fact takes the dimension version current when the fact loaded.'
    REFRESH USING (
        INSERT INTO SELF
        SELECT S.SALE_ID, C.CUST_SK, P.PROD_SK, S.CUST_CODE, S.PROD_CODE,
               S.QTY, S.AMOUNT, S.EVENT_TS,
               CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
        FROM SCD2_DEMO.RAW.SALES_SRC CHANGES(INFORMATION => APPEND_ONLY) AS S
        LEFT JOIN SCD2_DEMO.CORE.DIM_CUSTOMER C
               ON C.CUST_CODE = S.CUST_CODE AND C.IS_CURRENT
        LEFT JOIN SCD2_DEMO.CORE.DIM_PRODUCT P
               ON P.PROD_CODE = S.PROD_CODE AND P.IS_CURRENT);

CREATE OR REPLACE DYNAMIC TABLE CORE.FACT_SALES_EVENTTIME (
    SALE_ID NUMBER, CUST_SK STRING, PROD_SK STRING,
    CUST_CODE STRING, PROD_CODE STRING,
    QTY NUMBER, AMOUNT NUMBER(12,2), EVENT_TS TIMESTAMP_NTZ,
    BOUND_AT TIMESTAMP_NTZ)
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'Sales fact, EVENT-TIME binding: each fact takes the dimension version in force at its own event_ts, via ASOF JOIN.'
    REFRESH USING (
        INSERT INTO SELF
        SELECT S.SALE_ID, C.CUST_SK, P.PROD_SK, S.CUST_CODE, S.PROD_CODE,
               S.QTY, S.AMOUNT, S.EVENT_TS,
               CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
        FROM SCD2_DEMO.RAW.SALES_SRC CHANGES(INFORMATION => APPEND_ONLY) AS S
        ASOF JOIN SCD2_DEMO.CORE.DIM_CUSTOMER C
          MATCH_CONDITION(S.EVENT_TS >= C.VALID_FROM)
          ON S.CUST_CODE = C.CUST_CODE
        ASOF JOIN SCD2_DEMO.CORE.DIM_PRODUCT P
          MATCH_CONDITION(S.EVENT_TS >= P.VALID_FROM)
          ON S.PROD_CODE = P.PROD_CODE);
```

`ASOF JOIN` is the construct built for this exact question: for each fact, find the one dimension row whose `VALID_FROM` is the closest preceding value to the fact's `EVENT_TS`. That is the definition of "which version was in force when this happened", stated directly rather than assembled out of inequalities.

Notice what it does not reference: `VALID_TO`. "Closest preceding" already implies the row's interval covers the event, so ASOF needs only `VALID_FROM`. Two consequences worth knowing:

- A missing match is **null-padded**, exactly like a left outer join, so a fact for an unknown member still survives rather than being dropped.
- Each ASOF join needs its **own** `MATCH_CONDITION` — you cannot share one across two joins, which is why it appears twice above.

And one caveat. ASOF and the range predicate agree only because the version chain is **contiguous** — which is what the "intervals contiguous" check asserts later in this guide. If a gap ever opened, the range form would return `NULL` for a fact inside it, whereas ASOF binds to the preceding version regardless. ASOF is the more forgiving of the two, and would therefore mask precisely the defect that check exists to catch. Keep it.

Because the fact tables read the dimensions, Snowflake places them downstream in the graph and refreshes the dimensions first. That ordering is not incidental — it is what allows an inferred member to exist by the time a fact needs it.

**On `APPEND_ONLY` here:** this is the correct use of it. Sales are genuinely append-only, so restricting the change set to inserts is both accurate and cheaper. A later section shows the same clause quietly destroying a dimension, and the difference between the two cases is the whole point.

<!-- ------------------------ -->
## Why the Temporal Join Belongs Inside the Refresh

Event-time binding is a temporal match, and a temporal match is a *non-equality* join however you spell it. Try expressing one declaratively and Snowflake tells you what it costs — here in its range-predicate form:

```sql
CREATE OR REPLACE DYNAMIC TABLE SCD2_DEMO.CONTROL.DT_EVENTTIME_RANGE_JOIN
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'NEGATIVE CONTROL: temporal range join in a standard dynamic table. Deliberately broken -- downgrades to FULL.'
    AS
SELECT S.SALE_ID, S.CUST_CODE, C.CUST_SK, C.TIER, S.AMOUNT, S.EVENT_TS
FROM SCD2_DEMO.RAW.SALES_SRC S
LEFT JOIN SCD2_DEMO.CORE.DIM_CUSTOMER C
       ON C.CUST_CODE = S.CUST_CODE
      AND S.EVENT_TS >= C.VALID_FROM
      AND (C.VALID_TO IS NULL OR S.EVENT_TS < C.VALID_TO);
```

```
FULL refresh mode was selected because: Change tracking is not supported on
queries containing outer joins with non-equality predicates.
```

A range predicate is a non-equality join, and that blocks incremental refresh. In practice it means every new sale recomputes the entire fact table against the entire dimension history.

Inside a custom incremental dynamic table the same predicate is free of that problem, because the binding is computed **once**, when the fact arrives, and then stored. There is no recomputation, so there is no incrementalization to lose. This is the strongest single argument for reaching for custom incrementalization here rather than a declarative dynamic table.

<!-- ------------------------ -->
## Make the Two Bindings Disagree

Both fact tables have been built, and so far they hold identical keys — which proves nothing, because every sale so far arrived while the dimension version it belongs to was still current. The difference only becomes visible when a fact arrives *late*.

Land a sale that happened before the price change but arrives after it:

```sql
INSERT INTO SCD2_DEMO.RAW.SALES_SRC (SALE_ID, CUST_CODE, PROD_CODE, QTY, AMOUNT, EVENT_TS)
    VALUES (99, 'ACME-US-020', 'HDPH-100', 1, 379.00,
            '2026-09-11 05:00:00'::TIMESTAMP_NTZ);   -- before the 429.00 version began

ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_PRODUCT REFRESH;
ALTER DYNAMIC TABLE SCD2_DEMO.CORE.FACT_SALES_LOADTIME REFRESH;
ALTER DYNAMIC TABLE SCD2_DEMO.CORE.FACT_SALES_EVENTTIME REFRESH;
```

Dimensions before facts, as always — a fact bound against a stale dimension is exactly the defect this section exists to expose.

Use a timestamp that genuinely falls inside the *old* product version's interval — take the `VALID_FROM`/`VALID_TO` values you saw earlier and pick a moment between them. Then ask both tables what that sale cost:

```sql
SELECT 'LOADTIME' AS BINDING, F.SALE_ID, F.EVENT_TS, F.AMOUNT, P.LIST_PRICE
FROM SCD2_DEMO.CORE.FACT_SALES_LOADTIME F
JOIN SCD2_DEMO.CORE.DIM_PRODUCT P ON P.PROD_SK = F.PROD_SK
WHERE F.SALE_ID = 99
UNION ALL
SELECT 'EVENTTIME', F.SALE_ID, F.EVENT_TS, F.AMOUNT, P.LIST_PRICE
FROM SCD2_DEMO.CORE.FACT_SALES_EVENTTIME F
JOIN SCD2_DEMO.CORE.DIM_PRODUCT P ON P.PROD_SK = F.PROD_SK
WHERE F.SALE_ID = 99;
```

| BINDING | SALE_ID | EVENT_TS | AMOUNT | LIST_PRICE |
|:---|:---|:---|:---|:---|
| LOADTIME | 99 | 2026-09-11 05:00:00 | 379.00 | 429.00 |
| EVENTTIME | 99 | 2026-09-11 05:00:00 | 379.00 | 379.00 |

The same sale, two different product versions, two different list prices. Note which one is defensible: the sale was recorded at `379.00`, and only the event-time binding produces a row where the amount and the list price agree. The load-time row claims a 379.00 sale of a 429.00 product, and any margin or price-variance calculation built on it is wrong — not by a rounding error, but by the entire price change.

This is the failure that stays hidden in most warehouses, because it requires three things to coincide: a dimension that versions, a fact that arrives late, and someone who compares. The first two are normal. The third is the one you have to build in deliberately, which is what the earlier validation section is for.

It also shows why this had to be a custom incremental dynamic table. The binding was computed once, from `event_ts`, at the moment the fact arrived — and it will never be recomputed. If it were recomputed later by a declarative refresh, the "correct" answer would silently drift as the dimension gained versions.

<!-- ------------------------ -->
## Watch a Fact Bind to a Dimension That Does Not Exist

Land a sale for a German customer. There is no such customer.

```sql
INSERT INTO SCD2_DEMO.RAW.SALES_SRC (SALE_ID, CUST_CODE, PROD_CODE, QTY, AMOUNT, EVENT_TS)
    VALUES (4, 'ACME-DE-030', 'HDPH-100', 5, 1895.00, CURRENT_TIMESTAMP());

ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_CUSTOMER REFRESH;
ALTER DYNAMIC TABLE SCD2_DEMO.CORE.FACT_SALES_LOADTIME REFRESH;
```

```sql
SELECT CUST_SK, CUST_CODE, CUST_NAME, TIER, IS_INFERRED
FROM SCD2_DEMO.CORE.DIM_CUSTOMER WHERE CUST_CODE = 'ACME-DE-030';
```

| CUST_SK | CUST_CODE | CUST_NAME | TIER | IS_INFERRED |
|:---|:---|:---|:---|:---|
| d1b283ab-c505-4ac0-8113-bfe9ff69c232 | ACME-DE-030 | (inferred - awaiting dimension) | UNKNOWN | TRUE |

The dimension invented a member because a fact needed one, and flagged it honestly. The sale carries that same `CUST_SK` — a real key, not a `NULL`. (Your key value will differ every time you build this; it is a random UUID.)

**Write that key down.** Now let the real customer arrive:

```sql
INSERT INTO SCD2_DEMO.RAW.CUSTOMER_SRC (CUST_CODE, CUST_NAME, TIER, COUNTRY)
    VALUES ('ACME-DE-030', 'Acme Semiconductor GmbH', 'BRONZE', 'DE');

ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_CUSTOMER REFRESH;
```

```sql
SELECT CUST_SK, CUST_CODE, CUST_NAME, TIER, COUNTRY, IS_INFERRED, IS_CURRENT
FROM SCD2_DEMO.CORE.DIM_CUSTOMER WHERE CUST_CODE = 'ACME-DE-030';
```

| CUST_SK | CUST_CODE | CUST_NAME | TIER | COUNTRY | IS_INFERRED | IS_CURRENT |
|:---|:---|:---|:---|:---|:---|:---|
| d1b283ab-c505-4ac0-8113-bfe9ff69c232 | ACME-DE-030 | Acme Semiconductor GmbH | BRONZE | DE | FALSE | TRUE |

Same key as before. Still one version. The attributes filled in and the flag cleared, and the fact that bound to that key before the customer existed is still correctly joined without anything having touched the fact table.

The refresh statistics confirm it was a correction and not a new version: `updatedRows` is 1 and `insertedRows` is 0.

### This protection is deliberately one-sided

Only `DIM_CUSTOMER` carries the inferred-member path. `DIM_PRODUCT` does not, and that is a teaching choice rather than an oversight — both dimensions run the same close/open mechanism, so holding them side by side lets you attribute the extra machinery to the extra problem instead of to SCD2 in general.

State the consequence plainly rather than letting a reader infer a blanket guarantee. A sale for an unknown *product* with a known customer lands with `CUST_SK` populated and **`PROD_SK` NULL** — and because facts are insert-only and never rebound, that NULL is permanent. The "no orphaned facts" check catches it, and "fact product keys resolve" covers the narrower case of a product key that is present but does not resolve. Both are in the validation section below.

So "no fact is ever orphaned" holds for the **customer** dimension. If your dimensions can all receive late members — the normal case — the pattern generalises by copying three things onto the other dimension: the `fact_keys` CTE, the `inferred` CTE, and the `FIXUP` branch of the `MERGE`. Nothing in it is customer-specific.

### The trade-off, stated plainly

This machinery exists because the key is **minted** rather than derived. A hash key would make foreign-key assignment coordination-free and none of the above would be necessary. That is true of a sequence key too — the cost belongs to minting, not to randomness.

What a minted key costs: an extra dependency edge in the graph, a dimension that has to read the fact stream, and a stale-lookup failure mode if that ordering is ever wrong. What it buys: no hash-collision discussion, and — for a random key specifically — no shared generator object and global uniqueness without coordination across accounts or regions. What it costs against a sequence is width and the loss of insertion order as a debugging signal. Decide which side of that you want before building, because retrofitting either direction means rewriting the dimension.

<!-- ------------------------ -->
## The APPEND_ONLY Trap

This is the most dangerous object in the guide, because nothing about it looks wrong. The refresh mode resolves to `CUSTOM_INCREMENTAL`, no warning is issued, and the surrogate keys are perfectly stable.

```sql
CREATE OR REPLACE DYNAMIC TABLE SCD2_DEMO.CONTROL.CIDT_APPEND_ONLY_TRAP (
    CUST_SK STRING, CUST_CODE STRING, TIER STRING)
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'NEGATIVE CONTROL: APPEND_ONLY against a source updated in place. Deliberately broken -- silently discards every UPDATE.'
    REFRESH USING (
        INSERT INTO SELF
        SELECT UUID_STRING(), C.CUST_CODE, C.TIER
        FROM SCD2_DEMO.RAW.CUSTOMER_SRC CHANGES(INFORMATION => APPEND_ONLY) AS C);
```

Change a tier and refresh both this and the correctly-built dimension:

```sql
UPDATE SCD2_DEMO.RAW.CUSTOMER_SRC
    SET TIER = 'CONTROL_CHANGED', SRC_LOADED_AT = CURRENT_TIMESTAMP()
    WHERE CUST_CODE = 'ACME-UK-010';

ALTER DYNAMIC TABLE SCD2_DEMO.CONTROL.CIDT_APPEND_ONLY_TRAP REFRESH;
ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_CUSTOMER REFRESH;
```

```sql
SELECT 'source' AS WHENCE, CUST_CODE, TIER FROM SCD2_DEMO.RAW.CUSTOMER_SRC
    WHERE CUST_CODE = 'ACME-UK-010'
UNION ALL
SELECT 'append_only_dt', CUST_CODE, TIER FROM SCD2_DEMO.CONTROL.CIDT_APPEND_ONLY_TRAP
    WHERE CUST_CODE = 'ACME-UK-010';
```

| WHENCE | CUST_CODE | TIER |
|:---|:---|:---|
| source | ACME-UK-010 | CONTROL_CHANGED |
| append_only_dt | ACME-UK-010 | SILVER |

No error. No new row. No warning. The change is simply gone, and for a Type 2 dimension that means history is being lost while the pipeline reports success.

`CHANGES(INFORMATION => APPEND_ONLY)` returns **inserts only**, and an `UPDATE` does not arrive as an insert — it surfaces as a `DELETE` and `INSERT` pair. Filtering to inserts is right for a genuinely append-only feed like the sales table. On a dimension whose rows are updated in place it discards precisely the changes you built the dimension to record.

The correct clause is `CHANGES(INFORMATION => DEFAULT)` filtered to `METADATA$ACTION = 'INSERT'`, which yields the **new** values of updated rows. `DIM_CUSTOMER` captured the same change as a proper new version.

<!-- ------------------------ -->
## Prove the Model Is Right

Storing `VALID_TO` means the pipeline *asserts* an interval rather than deriving it, and nothing stops an assertion being wrong. So derive it a second way and demand the two agree.

Window functions are compatible with incremental refresh, so a standard dynamic table can recompute the intervals with `LEAD()`:

```sql
CREATE OR REPLACE DYNAMIC TABLE SCD2_DEMO.CORE.DIM_CUSTOMER_INTERVAL_CHECK
    TARGET_LAG = '10 minutes'
    WAREHOUSE = COMPUTE_WH
    COMMENT = 'Independent check: recomputes the SCD2 intervals with LEAD() so the stored valid_to can be compared against a separately derived value.'
    AS
SELECT CUST_SK, CUST_CODE, VALID_FROM,
       VALID_TO AS STORED_VALID_TO,
       LEAD(VALID_FROM) OVER (PARTITION BY CUST_CODE ORDER BY VALID_FROM) AS DERIVED_VALID_TO
FROM SCD2_DEMO.CORE.DIM_CUSTOMER;
```

That resolves to `INCREMENTAL`. Now the checks — every one must return zero.

```sql
SELECT 'one current version per key' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM (SELECT CUST_CODE FROM SCD2_DEMO.CORE.DIM_CUSTOMER
      WHERE IS_CURRENT GROUP BY CUST_CODE HAVING COUNT(*) <> 1);

SELECT 'is_current agrees with null valid_to' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM SCD2_DEMO.CORE.DIM_CUSTOMER WHERE IS_CURRENT <> (VALID_TO IS NULL);

SELECT 'intervals contiguous' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM SCD2_DEMO.CORE.DIM_CUSTOMER_INTERVAL_CHECK
WHERE STORED_VALID_TO IS DISTINCT FROM DERIVED_VALID_TO;

SELECT 'surrogate keys unique' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM (SELECT CUST_SK FROM SCD2_DEMO.CORE.DIM_CUSTOMER
      GROUP BY CUST_SK HAVING COUNT(*) > 1);

SELECT 'no orphaned facts' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM SCD2_DEMO.CORE.FACT_SALES_LOADTIME WHERE CUST_SK IS NULL OR PROD_SK IS NULL;

SELECT 'fact customer keys resolve' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM SCD2_DEMO.CORE.FACT_SALES_LOADTIME F
LEFT JOIN SCD2_DEMO.CORE.DIM_CUSTOMER D ON D.CUST_SK = F.CUST_SK
WHERE D.CUST_SK IS NULL;

SELECT 'fact product keys resolve' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM SCD2_DEMO.CORE.FACT_SALES_LOADTIME F
LEFT JOIN SCD2_DEMO.CORE.DIM_PRODUCT P ON P.PROD_SK = F.PROD_SK
WHERE P.PROD_SK IS NULL;

SELECT 'product: one current version per key' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM (SELECT PROD_CODE FROM SCD2_DEMO.CORE.DIM_PRODUCT
      WHERE IS_CURRENT GROUP BY PROD_CODE HAVING COUNT(*) <> 1);

SELECT 'no duplicate facts' AS CHECK_NAME, COUNT(*) AS VIOLATIONS
FROM (SELECT SALE_ID FROM SCD2_DEMO.CORE.FACT_SALES_LOADTIME
      GROUP BY SALE_ID HAVING COUNT(*) > 1);
```

The second check earns its place. `IS_CURRENT` and `VALID_TO IS NULL` encode the same fact twice, and if they ever disagree, two analysts writing two reasonable predicates get two different answers and neither has any reason to suspect a problem.

The third is the one that makes the stored interval trustworthy rather than merely present.

The two "keys resolve" checks are doing different jobs, which is worth noticing. On the customer side the inferred-member path guarantees a key exists, so that check is really asking whether the payoff worked. On the product side there is no such path, so it is the only structural guard on that foreign key beyond the NULL test — the asymmetry in the model shows up as an asymmetry in what the same-looking check is actually proving.

<!-- ------------------------ -->
## Read the Instrument Panel

Every failure in this guide was silent. Snowflake accepted the definition, reported success, and did something other than what was intended. So the habit worth forming is not memorising which constructs are safe — it is checking what actually happened.

```sql
SHOW DYNAMIC TABLES IN DATABASE SCD2_DEMO;

SELECT "schema_name" || '.' || "name" AS OBJECT_NAME,
       "refresh_mode", "refresh_mode_reason", "rows", "scheduling_state"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
ORDER BY 1;
```

Three readings tell you almost everything:

**`refresh_mode`** — is it what you intended? An unexpected `FULL` on an object you designed to be incremental means something in the definition blocked change tracking.

**`refresh_mode_reason`** — when Snowflake downgrades, it says why, naming the function or the join shape. This field answers the question directly; guessing is unnecessary.

**Refresh statistics** — returned by `ALTER DYNAMIC TABLE ... REFRESH`, and also recorded in `DYNAMIC_TABLE_REFRESH_HISTORY`. `copiedRows` means rows were preserved. `deletedRows` climbing on a change that should not have touched those rows means identity is churning.

Note that `INFORMATION_SCHEMA.DYNAMIC_TABLES()` does **not** expose `refresh_mode` — it carries lag and health columns, and it is account-scoped rather than restricted to the database you qualify it with. Use `SHOW DYNAMIC TABLES` with `RESULT_SCAN` for refresh mode, and the table function for lag and refresh state.

One more thing that reads as a failure and is not: a manual `ALTER DYNAMIC TABLE ... REFRESH` frequently reports `No new data` because the scheduled refresh already consumed the change. Check `data_timestamp` and the row contents before concluding anything is broken.

<!-- ------------------------ -->
## Stop It or Tear It Down

A custom incremental refresh runs on schedule **even when there are no changes to process**, and a no-op refresh still consumes credits. Leave this demo running and it will refresh every few minutes indefinitely, doing nothing.

To stop the refreshes while keeping everything in place:

```sql
ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_CUSTOMER SUSPEND;
```

Before you suspend anything you intend to come back to, raise retention on the source tables. A dynamic table suspended for longer than its base tables' `DATA_RETENTION_TIME_IN_DAYS` **cannot resume** — the change history it needs has aged out, and recreating a Type 2 dimension means losing every version it accumulated:

```sql
ALTER TABLE SCD2_DEMO.RAW.CUSTOMER_SRC SET DATA_RETENTION_TIME_IN_DAYS = 14;
ALTER TABLE SCD2_DEMO.RAW.PRODUCT_SRC  SET DATA_RETENTION_TIME_IN_DAYS = 14;
ALTER TABLE SCD2_DEMO.RAW.SALES_SRC    SET DATA_RETENTION_TIME_IN_DAYS = 14;
```

Resume when you want to carry on:

```sql
ALTER DYNAMIC TABLE SCD2_DEMO.CORE.DIM_CUSTOMER RESUME;
```

Or remove everything:

```sql
DROP DATABASE IF EXISTS SCD2_DEMO;
SHOW DATABASES LIKE 'SCD2_DEMO';
```

<!-- ------------------------ -->
## Conclusion and Resources

You built a Type 2 dimension on Dynamic Tables with stable random surrogate keys, stored validity intervals, and dimensions that tolerate arriving after the facts that reference them — and you saw the three ways this goes silently wrong.

### What to take away

- `UUID_STRING()` in a dynamic table downgrades the refresh to FULL, and the resulting key churn breaks every foreign key pointing at the dimension on every refresh. The downgrade is reported only in the `CREATE` success message.
- `dbt_utils.generate_surrogate_key` is a deterministic MD5 over coalesced, cast, concatenated business columns. It works because it is a pure function of its inputs, and it needs no dbt to use.
- A random key is stable in a custom incremental dynamic table because such tables are imperative — rows persist and are never recomputed, so a value evaluated once stays put. Stability comes from write-once placement, not from determinism.
- SCD2 close-and-open fits in one DML when the `USING` subquery emits one row per intended action, with the op filter in the `ON` clause.
- A member's first version must open at the beginning of time, or facts older than the initial load bind to `NULL`.
- Bind facts at load time or at event time deliberately. Event-time binding needs a range predicate, which blocks incremental refresh declaratively but is free inside a custom incremental refresh.
- An inferred member minted from the fact stream keeps late-arriving dimensions from orphaning facts, and a stable key means the correction never touches the fact table.
- `CHANGES(INFORMATION => APPEND_ONLY)` discards updates in silence. Correct for an append-only feed, destructive on a dimension.
- Your history granularity is bounded by `TARGET_LAG`. Change capture at a lag records the net change per window, not every intermediate state.

### Related resources

- [Dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview)
- [Custom incrementalization](https://docs.snowflake.com/en/user-guide/dynamic-tables/custom-incrementalization)
- [Supported queries for dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/supported-queries)
- [Design patterns for dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/design-patterns)
- [Manage dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/manage)
- [Dynamic table refresh modes](https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes)

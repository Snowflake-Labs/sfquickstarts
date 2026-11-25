author: James Cha-Earley
id: merge-two-order-systems-with-cortex-code
language: en
summary: A coffee chain just bought a rival, and the two order systems disagree on everything. Use CoCo in Snowsight to reconcile them, build a Dynamic Table pipeline, fix it live when an upstream change breaks it, and ship a Streamlit revenue dashboard.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/snowflake-feature/transformation, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/industry/retail-and-cpg
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/sfc-gh-JCHAEARLEY/sfguide-merge-two-order-systems-with-cortex-code

# The Merger: Two Order Systems, One Revenue Number with CoCo
<!-- ------------------------ -->
## Overview

Northbound Coffee just bought Daily Grind. The CEO wants one revenue dashboard by Friday. The problem: the two companies' order systems disagree on almost everything.

In this guide you play the data engineer who has to make the numbers agree. You'll use **CoCo** (Cortex Code), the AI coding agent built into Snowsight, to compare the two sources, build a pipeline with Dynamic Tables, survive a surprise schema change upstream, and build the CEO's dashboard as a Streamlit app from scratch.

Every step ends with a check query and the exact numbers you should see, so you always know whether you're on track.

> **Important:** CoCo is powered by LLMs and is non-deterministic. The SQL and code it writes may differ from what you see here. That's fine. The check queries read your tables, not CoCo's chat, so they tell you whether the result is right.

### Prerequisites
- Basic SQL: you can read a `SELECT` with a join and a `GROUP BY`
- Familiarity with Snowsight. No Python, Streamlit, or Dynamic Tables experience needed; CoCo writes that code.

### What You'll Learn
- How to use CoCo to compare two messy sources and write a mapping between them
- How to build a raw → unified → daily-metrics pipeline with Dynamic Tables using CoCo's Plan mode
- How to diagnose a failed pipeline with Dynamic Table refresh history, and fix it with CoCo
- How to build a Streamlit app from scratch with CoCo and run it in Snowflake

### What You'll Need
- A Snowflake account with access to CoCo in Snowsight. A [free trial](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) works.
- The `ACCOUNTADMIN` role for the one-time setup. Setup creates a lab role, `MERGER_ROLE`, that you use for everything after that.
- The companion GitHub repo, which you'll open as a workspace: [sfc-gh-JCHAEARLEY/sfguide-merge-two-order-systems-with-cortex-code](https://github.com/sfc-gh-JCHAEARLEY/sfguide-merge-two-order-systems-with-cortex-code)
- Nothing to install. Everything runs in your browser.

> **Using a trial account?** AI features, including CoCo, are disabled by default on self-service trial accounts. To turn them on, go to **Admin** » **Billing**, open the **Snowflake billing** tab, and add a credit card. Adding a card doesn't upgrade the trial to a paid account or end the trial period.

### What You'll Build
- Two Dynamic Tables, `ORDERS_UNIFIED` and `DAILY_REVENUE`, that merge both companies' orders into one trustworthy revenue number
- A Streamlit dashboard, running in Snowflake, that the CEO can open on Friday

### Run sheet

| Step | What happens | Time |
|------|--------------|------|
| 1 | Set up: open the repo as a workspace and run the setup script | 5 min |
| 2 | Discover the data: CoCo compares the sources and writes a mapping | 10 min |
| 3 | Build the pipeline: CoCo plans and builds the Dynamic Tables | 12 min |
| 4 | The break: an upstream change fails the pipeline, and CoCo fixes it | 5 min |
| 5 | Build the dashboard: CoCo writes the Streamlit app | 13 min |

<!-- ------------------------ -->
## The Scenario

Two companies, two order systems, one board meeting.

| | **Northbound Coffee** (the acquirer) | **Daily Grind** (just acquired) |
|---|---|---|
| Channel | In-store registers (POS) | Web and app pickup orders |
| Format | CSV export, loaded into typed columns | One JSON document per order |
| Table | `MERGER_DB.RAW.STORE_SALES` | `MERGER_DB.RAW.WEB_ORDERS` |
| Amounts | Dollars (`TOTAL_USD`) | Cents (`amount_cents`) |
| Timestamps | Store-local wall-clock time | UTC (`created_at` ends in `Z`) |
| Store IDs | Register number, like `101` | Location code, like `DG-SF-01` |
| Gotcha | None, yet | The order API retried requests, so some orders arrived twice |

The one table both companies agree on is `MERGER_DB.RAW.STORE_CROSSWALK`. It maps each source's store key to a unified `STORE_ID`, along with each store's name, city, and time zone.

Each of those differences is a way to get the wrong revenue number:
- Add cents to dollars and Daily Grind looks 100 times bigger than it is.
- Count orders by UTC date and evening web orders on the West Coast land on the next day.
- Keep the retried orders and you count revenue that never happened.

Your job is to make the number right, and keep it right.

<!-- ------------------------ -->
## Set Up Your Environment

### Sign in as ACCOUNTADMIN

Sign in to Snowsight. In the user menu in the lower-left corner, switch your role to **ACCOUNTADMIN**. You need it only for setup.

### Create a Git-backed workspace

The companion repo holds every file you'll run in this lab. Open it as a workspace so the files are already in Snowsight.

First, allow Snowflake to clone from the repo's GitHub account. In the navigation menu, select **Projects** » **Workspaces**. In **My Workspace**, select **+ Add new** » **SQL File**, paste the statements below, and select **Run all**:

```sql
USE ROLE ACCOUNTADMIN;

CREATE API INTEGRATION IF NOT EXISTS GITHUB_MERGER_LAB
  API_PROVIDER = GIT_HTTPS_API
  API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-JCHAEARLEY')
  ENABLED = TRUE;
```

Then create the workspace:

1. In the **Workspaces** menu, select **From Git repository**.
2. For **Repository URL**, enter `https://github.com/sfc-gh-JCHAEARLEY/sfguide-merge-two-order-systems-with-cortex-code`.
3. Optional: rename the workspace, for example to `the-merger`.
4. In the **API Integration** menu, select `GITHUB_MERGER_LAB`.
5. Select **Public repository**.
6. Select **Create**.

The workspace opens with the repo's files in the file explorer on the left:

| File | What it's for |
|------|---------------|
| `setup.sql` | Creates the lab role, warehouse, database, and source data |
| `checks.sql` | One check block per step, with the expected answers |
| `break_batch.sql` | The surprise schema change in step 4 |
| `solutions/` | Reference answers, if you fall behind |

### Run the setup script

Open **`setup.sql`** and select **Run all**. The script:
- creates `MERGER_ROLE` and grants it to you, along with the Cortex access CoCo needs
- creates `MERGER_WH`, an X-Small warehouse that suspends after 60 seconds
- creates `MERGER_DB` and makes `MERGER_ROLE` its owner
- switches to `MERGER_ROLE` and builds the `RAW` and `ANALYTICS` schemas and three source tables with 28 days of orders (Sept 1–28, 2026)

The data is generated deterministically, so everyone gets exactly the same rows. If you need to start over, run `setup.sql` again: it resets the lab.

### Switch to the lab role

In the user menu in the lower-left corner, switch your role to **MERGER_ROLE**. CoCo starts its session with whatever role is active in Snowsight, so the objects it creates from here on are owned by the lab role. `MERGER_ROLE` is granted only one warehouse, `MERGER_WH`, so use that wherever you're asked to choose a warehouse.

### CHECK 1

Open **`checks.sql`**. You'll run one block from it after each step. Select and run the **CHECK 1** block. Every row should say **PASS**:

| check_name | expected |
|---|---|
| STORE_CROSSWALK rows | 10 |
| STORE_SALES rows | 4,216 |
| WEB_ORDERS documents | 3,106 |

### Open CoCo

Select the **CoCo** icon in the lower-right corner of the workspace. You'll use one CoCo conversation for the discovery, pipeline, and break steps, so CoCo can reuse what it learns.

> **Tip:** Type `@` in the CoCo message box to add a table as context, for example `@MERGER_DB.RAW.WEB_ORDERS`.

<!-- ------------------------ -->
## Discover the Data

Before writing any pipeline, have CoCo study both sources and tell you where they disagree.

### Prompt

```
We just merged two coffee companies and I need one revenue number. Compare the
tables in MERGER_DB.RAW: STORE_SALES (Northbound Coffee in-store POS),
WEB_ORDERS (Daily Grind web and app orders, one JSON document per row in the
RAW column), and STORE_CROSSWALK.

For each source, tell me how it records the order ID, the store, the timestamp
and its time zone, and the amount and its unit. Find anything that would make a
combined revenue number wrong, including duplicate orders. Then write a
column-by-column mapping from both sources into one unified order shape.
Use warehouse MERGER_WH, and don't create any objects yet.
```

### What CoCo should find

CoCo runs a few exploratory queries, such as sampling rows, flattening the JSON, and counting distinct order IDs, then summarizes. Check that its answer covers all five differences:

1. **Format:** `STORE_SALES` has typed columns, while `WEB_ORDERS` stores each order as JSON in a `VARIANT` column.
2. **Units:** `TOTAL_USD` is in dollars, while `amount_cents` is in cents.
3. **Time zones:** `SALE_TIMESTAMP` is store-local time, while `created_at` is a UTC string. Each store's time zone is in `STORE_CROSSWALK.TIMEZONE`.
4. **Store IDs:** POS uses register numbers (`101`–`105`), web uses location codes (`DG-SF-01` and so on), and both map to a `STORE_ID` through `STORE_CROSSWALK`.
5. **Duplicates:** `WEB_ORDERS` has **3,106** documents but only **3,040** distinct `order_id` values. The retried copies share an `order_id` and have a later `LOADED_AT`.

If CoCo misses one, ask about it directly, for example: *"Are there duplicate order IDs in WEB_ORDERS? What unit is amount_cents in?"*

### CHECK 2

Run the **CHECK 2** block in `checks.sql`. These numbers should match what CoCo reported:

| check_name | expected |
|---|---|
| Unique web orders | 3,040 |
| Duplicate web documents | 66 |
| Web store codes missing from crosswalk | 0 |

<!-- ------------------------ -->
## Build the Pipeline in Plan Mode

Now turn the mapping into a pipeline. You'll build two Dynamic Tables:

```
RAW.STORE_SALES ──┐
RAW.WEB_ORDERS  ──┼──► ANALYTICS.ORDERS_UNIFIED ──► ANALYTICS.DAILY_REVENUE ──► dashboard
RAW.STORE_CROSSWALK ┘     (one row per order)        (one row per store per day)
```

A Dynamic Table is defined by a `SELECT`. Snowflake keeps it up to date as the source tables change, within the `TARGET_LAG` you set, and works out the refresh order from the dependency graph. `TARGET_LAG = DOWNSTREAM` means "refresh only when a table downstream needs fresh data."

### Turn on Plan mode

Creating core tables is a good time to review before anything runs. In the CoCo message box, select **+**, and then select **Plan mode**. You can also press **Cmd+Shift+P** (macOS) or **Ctrl+Shift+P** (Windows). A **Plan** label appears in the message box.

In Plan mode, CoCo researches the task and proposes a plan instead of making changes. When you confirm the plan, CoCo turns Plan mode off and starts the work.

> **Don't see Plan mode?** Start the prompt below with: *"Make a plan first and wait for my approval before you create anything."*

### Prompt

In the **same CoCo conversation**, send:

```
Using that mapping, build a Dynamic Table pipeline in MERGER_DB.ANALYTICS that
uses warehouse MERGER_WH. Read from the RAW tables directly.

1. ORDERS_UNIFIED, TARGET_LAG = DOWNSTREAM. One row per order from both sources,
   with exactly these columns: ORDER_ID, STORE_ID, BRAND, CHANNEL ('In-store' or
   'Web'), STORE_NAME, CITY, ORDER_TS_LOCAL, BUSINESS_DATE, ITEM_NAME, QTY,
   AMOUNT_USD.
2. DAILY_REVENUE, TARGET_LAG = '1 hour'. One row per BUSINESS_DATE, STORE_ID,
   BRAND, CHANNEL, STORE_NAME, CITY, with ORDER_COUNT, REVENUE_USD and
   AVG_ORDER_USD.

Business rules:
- All amounts in dollars.
- BUSINESS_DATE is the store's LOCAL date. POS SALE_TIMESTAMP is already local,
  so use its date as-is. Convert web UTC timestamps using the store's TIMEZONE
  from STORE_CROSSWALK.
- Count each web order once: keep the copy with the earliest LOADED_AT.
- Get STORE_ID, STORE_NAME and CITY from STORE_CROSSWALK for both sources.
```

### Review the plan, then approve

Before you approve, check that the plan:
- divides `amount_cents` by 100
- uses `CONVERT_TIMEZONE` with the crosswalk's `TIMEZONE` to compute the web `BUSINESS_DATE`
- deduplicates web orders on `order_id`, for example with `QUALIFY ROW_NUMBER() ... = 1`
- creates `ORDERS_UNIFIED` before `DAILY_REVENUE`

If something is off, tell CoCo in plain language before approving. When the plan looks right, approve it and let CoCo create the tables.

> **Note:** Snowflake may set the refresh mode to `FULL` for both tables: `ORDERS_UNIFIED` because its query unions two sources and deduplicates with a window function, and `DAILY_REVENUE` because it reads from a `FULL` table. At a few thousand rows, a full refresh takes seconds, so that's expected and fine.

### CHECK 3

Run the **CHECK 3** block in `checks.sql`:

| check_name | expected |
|---|---|
| ORDERS_UNIFIED rows | 7,256 |
| Orders with no STORE_ID | 0 |
| DAILY_REVENUE rows (10 stores x 28 days) | 280 |
| Total revenue (USD) | 72,702.55 |
| Revenue on Sat Sept 19 (store-local day) | 3,372.30 |

That's 4,216 in-store orders plus 3,040 web orders. Northbound brings in $41,789.95 and Daily Grind $30,912.60.

If a number doesn't match, the wrong value usually tells you which rule was missed:

| What you see | What went wrong | Ask CoCo |
|---|---|---|
| ORDERS_UNIFIED = 7,322 or total = 73,390.65 | Retried web orders were counted twice | *"Deduplicate WEB_ORDERS on order_id, keeping the earliest LOADED_AT."* |
| Total in the millions | Cents were added to dollars | *"amount_cents is in cents. Convert it to dollars."* |
| Sept 19 = 3,115.70 | Web orders were dated by UTC instead of store-local time | *"BUSINESS_DATE must be the store's local date. Convert created_at from UTC with STORE_CROSSWALK.TIMEZONE."* |
| Orders with no STORE_ID above 0 | A source wasn't joined to the crosswalk correctly | *"Which orders in ORDERS_UNIFIED have no STORE_ID? Fix the crosswalk join."* |

Ask CoCo to fix the Dynamic Table rather than editing the SQL yourself, then run CHECK 3 again.

> **Short on time?** Open **`solutions/solution.sql`** and select **Run all** to create the reference version of both tables, then continue.

<!-- ------------------------ -->
## The Morning-After Break

It's Wednesday morning. Northbound's POS vendor shipped a "minor" update: the export now calls the dollar column `SALE_AMOUNT_USD` instead of `TOTAL_USD`. The first batch in the new format, Tuesday Sept 29, landed overnight. Then the CEO asks for fresh numbers.

### Run the break

Open **`break_batch.sql`** and select **Run all**. The script:
1. renames `TOTAL_USD` to `SALE_AMOUNT_USD` on `RAW.STORE_SALES`
2. inserts 150 sales for Sept 29 using the new column name
3. asks `DAILY_REVENUE` for a refresh

**The last statement fails.** That's the point. You'll see an error like:

```
Failed to refresh dynamic table ... Some inputs failed to refresh:
[MERGER_DB.ANALYTICS.ORDERS_UNIFIED]. To see the full list of failed DTs,
please query refresh history.
```

### Prompt

Don't go looking for the cause yourself. CoCo needs to make changes here, so Plan mode should be off. It turns off when you confirm a plan; if the **Plan** label is still showing in the message box, select the **x** on it. In the same CoCo conversation, send:

```
MERGER_DB.ANALYTICS.DAILY_REVENUE failed to refresh after this morning's POS
batch landed. Use today's dynamic table refresh history and the pipeline's
upstream dependencies to find which table failed and why. Then fix the pipeline so it
refreshes again and includes the new batch. Don't change the raw data.
```

### What CoCo should do

1. Query `INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY` for `MERGER_DB.ANALYTICS` and find two problems:
   - `ORDERS_UNIFIED` is **FAILED** with an `invalid identifier` error on `TOTAL_USD`.
   - `DAILY_REVENUE` is **UPSTREAM_FAILED**: it was skipped because its input failed. The root cause is upstream.
2. Inspect `RAW.STORE_SALES` and see that `TOTAL_USD` is gone and `SALE_AMOUNT_USD` has replaced it.
3. Update `ORDERS_UNIFIED` to read `SALE_AMOUNT_USD`, then refresh `DAILY_REVENUE`.

CoCo may use `CREATE OR ALTER DYNAMIC TABLE` or `CREATE OR REPLACE DYNAMIC TABLE` for the fix. Both work here. `CREATE OR ALTER` keeps the existing table and its grants, and updates its definition. `CREATE OR REPLACE` drops and recreates it. Either way, changing the query makes `ORDERS_UNIFIED` reinitialize on its next refresh, which takes seconds at this size.

> **Tip:** You can see the same story in the UI. Go to **Transformation** » **Dynamic tables**, open `ORDERS_UNIFIED`, and look at the **Refresh History** and **Graph** tabs.

### CHECK 4

Run the **CHECK 4** block in `checks.sql`. Before the fix, every row fails, and the last one shows `UPSTREAM_FAILED`. After the fix, every row should say **PASS**:

| check_name | expected |
|---|---|
| ORDERS_UNIFIED rows | 7,406 |
| Orders on Tue Sept 29 (new batch) | 150 |
| Revenue on Tue Sept 29 (USD) | 1,667.75 |
| Total revenue (USD) | 74,370.30 |
| Latest DAILY_REVENUE refresh state | SUCCEEDED |

> **Short on time?** Open **`solutions/fix_after_break.sql`** and select **Run all**, then continue.

<!-- ------------------------ -->
## Build the Dashboard

The numbers agree, and the pipeline survives upstream changes. Now give the CEO something to look at.

### Create a Streamlit app in your workspace

1. In the workspace file explorer, select **+ Add new** » **Streamlit app**. Name it `merger_dashboard`.
2. Snowflake creates a folder with starter files, including `streamlit_app.py`. Open `streamlit_app.py`.
3. Point the app at the lab warehouse. In the project pane toolbar, select **Settings**. On the **Targets** tab, open **Preview in workspace**, set the query warehouse under **Execution** to `MERGER_WH`, and select **Save settings**. The warehouse list shows only warehouses the app's role can use on its own, and `MERGER_ROLE` is granted only `MERGER_WH`.
4. Open the **CoCo** panel. Start a new conversation so CoCo focuses on the app.

### Prompt

```
Replace this starter app with a revenue dashboard for our CEO. Read
MERGER_DB.ANALYTICS.DAILY_REVENUE with st.connection("snowflake") and cache the
query result. Include:
- a business-day date range filter and a brand filter
- KPI cards for total revenue, orders, average order value, and number of stores
- a line chart of daily revenue by brand
- a store leaderboard table sorted by revenue
- revenue by channel (In-store vs Web)
Use only streamlit, pandas, and altair, and don't add new packages.
```

CoCo rewrites `streamlit_app.py`. Review the changes and accept them.

### Run it

Select **Run** in the action bar at the top of the file. This starts a private preview only you can see. With the full date range and both brands selected, the KPIs should read:

| KPI | expected |
|---|---|
| Revenue | $74,370.30 |
| Orders | 7,406 |
| Average order | $10.04 |
| Stores | 10 |

Change the filters to explore. Saturdays are busier than weekdays, and Daily Grind's web orders skew toward the evening.

If the app shows an error, paste the error into CoCo and ask it to fix the app. If you're stuck, copy the contents of **`solutions/streamlit_app.py`** into your `streamlit_app.py`.

### Optional: deploy it

The preview is private. To share the dashboard, deploy it to a *deploy target*: a copy of the app that runs outside the workspace as a Streamlit object.

1. In the project pane toolbar, select **Settings**.
2. On the **Targets** tab, select the existing deploy target if there is one, or select **Add deploy target**. Set:
   - **Owner role of deployed app:** `MERGER_ROLE`
   - **App location:** `MERGER_DB.ANALYTICS`
   - **Execution:** `MERGER_WH` as the query warehouse, and the default compute pool. Unless your account has changed it, the default pool is the Snowflake-created `SYSTEM_COMPUTE_POOL_CPU`.
3. Select **Save settings**.
4. In the project pane toolbar, select **Deploy**, select your target, and then select **Deploy**.

To let teammates open it, share the deployed app with their roles or users. See [Create and run a Streamlit app in a workspace](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-create-run) for the sharing steps.

To open the deployed app, go to **Projects** » **Streamlit** and select it. That's the dashboard the CEO gets on Friday: one revenue number, from two systems that didn't agree on anything.

<!-- ------------------------ -->
## Clean Up

To stop all credit consumption from this guide:

1. Open the SQL file you created in **My Workspace** for the API integration, replace its contents with the statements below, and select **Run all**:

```sql
USE ROLE ACCOUNTADMIN;

-- Drops the raw tables, both Dynamic Tables, and the deployed Streamlit app
DROP DATABASE IF EXISTS MERGER_DB;

DROP WAREHOUSE IF EXISTS MERGER_WH;
DROP ROLE IF EXISTS MERGER_ROLE;

-- The Git API integration you created for this lab
DROP API INTEGRATION IF EXISTS GITHUB_MERGER_LAB;
```

2. In **Projects** » **Workspaces**, delete your lab workspace. Then delete the SQL file in **My Workspace**.

<!-- ------------------------ -->
## Conclusion and Resources

You merged two order systems that disagreed on format, units, time zones, store IDs, and duplicates, and turned them into one revenue number that holds up. Then you kept it right when an upstream change broke the pipeline, and built a dashboard on top of it, without writing the code by hand.

### What You Learned
- Using CoCo to compare messy sources and produce a mapping before you build
- Building a Dynamic Table pipeline with CoCo's Plan mode, with business rules stated up front
- Diagnosing `FAILED` and `UPSTREAM_FAILED` refreshes from Dynamic Table refresh history, and fixing the root cause with CoCo
- Building a Streamlit app from scratch with CoCo and running it in a workspace
- Using check queries with known answers to verify AI-generated work

### Related Resources

Code:
- [Companion repo: sfguide-merge-two-order-systems-with-cortex-code](https://github.com/sfc-gh-JCHAEARLEY/sfguide-merge-two-order-systems-with-cortex-code)

Guides:
- [Build Autonomous SQL Pipelines for AI Agents](https://www.snowflake.com/en/developers/guides/snowflake-dynamic-tables-data-pipeline/)
- [Campaign Planning, Simplified: Build It with CoCo, Ask It with CoWork](https://www.snowflake.com/en/developers/guides/campaign-planning-with-coco-and-cowork/)

Documentation:
- [CoCo in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview)
- [Troubleshoot dynamic table refresh issues](https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshoot-refreshes)
- [Create and run a Streamlit app in a workspace](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-create-run)

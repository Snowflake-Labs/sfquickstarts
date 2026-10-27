id: identity-resolution-eligibility
author: Cole Tindall
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/industry/public-sector, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/snowflake-feature/cortex-analyst
language: en
summary: Build an identity resolution and benefits eligibility platform with Snowflake Dynamic Tables, Cortex AI, governed sharing, and a caseworker app on Snowflake App Runtime.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# Build an Identity Resolution and Eligibility Platform for Public Sector with Cortex AI

Resolve residents across disconnected program systems into one trusted
record, automate eligibility checks, and share governed data with
partner agencies.

## Overview

State benefits agencies often run separate systems for SNAP, Medicaid,
childcare, workforce, and tax, and none of them share a resident ID.
Caseworkers cross-reference systems by hand, eligible residents wait,
and duplicate cases slip through. This guide builds a reference
platform for Keystone Benefits Administration, a fictional state
agency. All data in this tutorial is synthetic.

### What You'll Learn

-   Generate realistic synthetic data across five program systems.
-   Match records in two passes: exact SSN, then fuzzy names with
    Jaro-Winkler similarity.
-   Build a master resident record that stays current with Dynamic
    Tables.
-   Apply an eligibility rule and score new applications automatically.
-   Mask sensitive data by role and share a governed view with a
    partner agency.
-   Create a Cortex Agent that answers caseworker questions in plain
    English.
-   Deploy a caseworker console on Snowflake App Runtime.

### What You'll Build

-   About 913,000 synthetic source records from five program systems
    resolving to about 400,000 residents.
-   A two-pass identity resolution pipeline (deterministic + probabilistic).
-   A SNAP eligibility view with outreach and duplicate-case flags.
-   A live intake pipeline built on incremental Dynamic Tables.
-   Masking policies, a secure partner view, and a zero-copy share.
-   A semantic view and a Cortex Agent.
-   A caseworker web application deployed on Snowflake App Runtime with
    tabs for Live Overview, Constituent & Eligibility, Ask Data + SQL,
    Duplicate Watchlist, Match Review, and Partner Sharing.

### What You'll Need

-   A Snowflake account with Cortex AI, Cortex Agents, and Snowflake
    App Runtime enabled. `SYSADMIN` for the build scripts,
    `ACCOUNTADMIN` for the share.
-   [Snowflake CLI](https://docs.snowflake.com/developer-guide/snowflake-cli/installation/installation) 3.26.0+ for deploying the app.
-   [Node.js](https://nodejs.org/) 20+ (optional, for local preview
    before deploying).
-   Familiarity with SQL and basic JavaScript/React.

## Setup and Data Foundation

Download `scripts/Lab_Script.sql` from the
[companion GitHub repository](COMPANION_REPO_URL). Open it
in a Snowsight SQL worksheet, select **Run All**, and wait about 5
minutes on a Medium warehouse. The script creates the `KEYSTONE_DEMO`
database and everything inside it.

The first section of the script creates the warehouse, database, and
four schemas:

| Schema | Purpose |
|--------|---------|
| `RAW` | Source system extracts and the live intake table |
| `CORE` | Identity resolution output and the master constituent record |
| `MART` | Eligibility views, Dynamic Tables, the semantic view, and the agent |
| `GOVERNANCE` | Masking policies and the shared secure view |

### Synthetic Population

Step 1.2 generates a 500,000-person ground truth table using
`GENERATOR`. Each person gets a name, date of birth, a fake SSN
starting with 9 (never issued), address, monthly income, and household
size.

### Five Source Systems

Step 1.3 creates five program tables, each with its own ID prefix,
name format, and column layout:

| Table | ID format | Name format | Rows |
|-------|-----------|-------------|------|
| `SNAP_FOOD_ASSISTANCE` | SNP-000123 | LAST, FIRST | ~153,000 |
| `MEDICAID_ENROLLMENT` | MCD-000123 | LAST, FIRST | ~210,000 |
| `CHILDCARE_SUBSIDY` | CCS-000123 | FIRST LAST | ~80,000 |
| `WORKFORCE_TRAINING` | WFD-000123 | First LAST | ~120,000 |
| `STATE_TAX_RECORDS` | TXR-000123 | LAST, FIRST | ~350,000 |

Simple `MOD()` rules inject the errors that break exact matching: a
dropped letter in a last name, a maiden name, an SSN typo, or a date
of birth off by one day. SNAP also gets about 3,000 planted duplicate
cases for the duplicate watchlist.

### Standardize

Step 2.1 parses every source into the same columns (first name, last
name, DOB, SSN, city, ZIP, income, household size) so the systems can
be compared.

## Identity Resolution

### Deterministic Match (Step 2.2)

Records that share an SSN are clustered together. This resolves most
of the 913,000 records.

### Probabilistic Match (Step 2.3)

Records whose SSN matched nothing are compared with existing clusters
in the same ZIP code with a date of birth within one day. If
`JAROWINKLER_SIMILARITY` scores the names 85 or higher (out of 100),
the record joins that cluster. Comparing only within the same ZIP and
DOB window, called blocking, keeps the work small at scale.

``` sql
-- Simplified excerpt from the lab script
WITH singles AS (SELECT * FROM ER_DETERMINISTIC_CLUSTERS WHERE CLUSTER_SIZE = 1),
anchors AS (SELECT * FROM ER_DETERMINISTIC_CLUSTERS WHERE CLUSTER_SIZE > 1)
SELECT s.DET_CLUSTER_NO AS S_C, a.DET_CLUSTER_NO AS A_C,
  JAROWINKLER_SIMILARITY(
    UPPER(s.FIRST_NAME) || ' ' || UPPER(s.LAST_NAME),
    UPPER(a.FIRST_NAME) || ' ' || UPPER(a.LAST_NAME)
  ) AS MATCH_SCORE
FROM singles s
JOIN anchors a ON a.ZIP = s.ZIP
WHERE ABS(DATEDIFF(day, a.DOB, s.DOB)) <= 1 AND MATCH_SCORE >= 85
QUALIFY ROW_NUMBER() OVER (PARTITION BY S_C ORDER BY MATCH_SCORE DESC) = 1;
```

### Master Record (Step 2.4)

`MATCH_LINK` maps every source record to a master ID (`KM-000123`)
and records how it matched: `DETERMINISTIC` (score 100),
`PROBABILISTIC` (its score), or `UNRESOLVED`. `CONSTITUENT_MASTER`
rolls those up to one row per resident.

### Verify

``` sql
SELECT MATCH_TYPE, COUNT(*) AS RECORDS
FROM KEYSTONE_DEMO.CORE.MATCH_LINK GROUP BY MATCH_TYPE;

SELECT COUNT(*) AS CONSTITUENTS, COUNT_IF(SYSTEMS_FOUND_IN >= 2) AS MULTI_SYSTEM
FROM KEYSTONE_DEMO.CORE.CONSTITUENT_MASTER;
```

Expect about 400,000–410,000 residents, roughly half found in two or
more systems. The data is random, so counts vary between builds.

## Eligibility Automation

### Eligibility Rule (Step 3.1)

`V_SNAP_ELIGIBILITY` applies an example rule: monthly income at or
below $1,579 plus $550 for each additional household member is a
`PASS`. Missing income goes to `MANUAL_REVIEW`, never to an automatic
pass. This is an illustrative rule, not an official program threshold.

``` sql
CASE WHEN cm.MONTHLY_INCOME IS NULL THEN 'MANUAL_REVIEW'
     WHEN cm.MONTHLY_INCOME <= 1579 + 550 * (COALESCE(cm.HOUSEHOLD_SIZE, 1) - 1) THEN 'PASS'
     ELSE 'FAIL' END AS ELIGIBILITY_RESULT
```

### Caseworker Views (Step 3.2)

| View | Answers |
|------|---------|
| `V_CROSS_PROGRAM_ENROLLMENT` | Which programs is this resident enrolled in? |
| `V_ELIGIBLE_NOT_ENROLLED` | Who qualifies for SNAP but isn't enrolled? (outreach) |
| `V_DUPLICATE_ENROLLMENT` | Who has two cases in the same program? (integrity) |
| `V_MATCH_REVIEW_QUEUE` | Which unmatched records may be the same person? |
| `V_CASEWORKER_CONTEXT` | Everything about one resident on one row |

### Live Intake Pipeline (Step 3.3)

New applications land in `RAW.LIVE_INTAKE`. Incremental Dynamic
Tables chain off it:

| Dynamic Table | Target Lag | Does |
|---------------|-----------|------|
| `CORE.LIVE_INTAKE_RESOLVED` | DOWNSTREAM | Joins each application to its master record |
| `MART.LIVE_INTAKE_ELIGIBILITY` | 1 minute | Scores each application |
| `MART.LIVE_INTAKE_METRICS` | 5 minutes | Totals by source and result |

Only the new rows are processed, not the whole population.

### Dashboard Views (Step 3.4)

`V_LIVE_PIPELINE_STATUS` and `V_LIVE_DASHBOARD` aggregate everything
the console's Live Overview tab reads.

### Verify

``` sql
SELECT * FROM KEYSTONE_DEMO.MART.V_LIVE_DASHBOARD;
```

## Governance and Secure Sharing

### Tag Sensitive Columns (Step 4.1)

A `SENSITIVITY` tag marks SSN and name columns as `PII` and income as
`CONFIDENTIAL`.

### Masking Policies (Step 4.2)

Three masking policies are attached to `CONSTITUENT_MASTER`. Roles
outside the allowlist (`SYSADMIN`, `KEYSTONE_CASEWORKER`,
`KEYSTONE_IDENTITY_ADMIN`) see masked values:

| Column | Unauthorized roles see |
|--------|-----------------------|
| SSN | Last four digits only |
| Date of birth | Year shifted by 60 |
| Monthly income | `NULL` |

### Secure View (Step 4.3)

`PUBLIC_HEALTH_SHARE_V` exposes master ID, name, location, and
program enrollment, but no SSN and no income.

### Zero-Copy Share (Step 4.4)

`KEYSTONE_PUBLIC_HEALTH_SHARE` publishes that view. The partner
agency queries live data, and nothing is copied. To deliver it, run
`ALTER SHARE KEYSTONE_PUBLIC_HEALTH_SHARE ADD ACCOUNTS = <org>.<account>;`.

## Cortex Agent

### Semantic View (Step 5.1)

`KEYSTONE_CASEWORKER` describes six MART views in business terms
(dimensions, facts, primary keys) and includes five verified queries.
Cortex Analyst uses it to write SQL from plain-English questions.

### Agent (Step 5.2)

`KEYSTONE_CASEWORKER_AGENT` is a permanent Cortex Agent that uses
Cortex Analyst as its tool:

``` sql
CREATE OR REPLACE AGENT KEYSTONE_DEMO.MART.KEYSTONE_CASEWORKER_AGENT
  FROM SPECIFICATION
$$
models:
  orchestration: auto
instructions:
  system: "Answer read-only questions about fictional Keystone data using the semantic view. ..."
tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "keystone_analyst"
tool_resources:
  keystone_analyst:
    semantic_view: "KEYSTONE_DEMO.MART.KEYSTONE_CASEWORKER"
    execution_environment:
      type: "warehouse"
      warehouse: "COMPUTE_WH"
$$;
```

The console's Ask Data tab calls the agent through
`SNOWFLAKE.CORTEX.DATA_AGENT_RUN`, parses the tool results, and
displays the answer alongside the SQL that produced it.

### Verify

In Snowsight, navigate to **AI & ML » Agents** and open
`KEYSTONE_CASEWORKER_AGENT`. Ask:

-   "How many eligible residents are not enrolled in SNAP?"
-   "Recap the matching evidence and SNAP eligibility for KM-000013."

## Caseworker Application

The caseworker console is a Next.js app deployed on Snowflake App
Runtime. It runs entirely in Snowflake as an `APPLICATION SERVICE`.
There is no local backend to manage and no credentials in the browser.

### Deploy

Clone the [companion GitHub repository](COMPANION_REPO_URL), add a
Snowflake CLI connection, and deploy the `keystone-console` app:

``` bash
# Get the app
git clone COMPANION_REPO_URL.git
cd <repo-name>/keystone-console

# Add a connection (one time)
snow connection add --connection-name keystone \
  --account <your_account> --user <your_user> \
  --role SYSADMIN --warehouse COMPUTE_WH \
  --authenticator 'OAUTH_AUTHORIZATION_CODE' \
  --client-store-temporary-credential --no-interactive

# Generate the deployment manifest and deploy
snow app setup --app-name="keystone_caseworker_console" \
  --database KEYSTONE_DEMO --schema APP --warehouse COMPUTE_WH \
  --connection keystone
snow app deploy --verbose --connection keystone
```

The deploy builds the app, uploads it, and prints the endpoint URL
(a `.snowflakecomputing.app` address). The first deploy takes about
3 minutes; redeployments are faster.

### What You Get

| Tab | What It Shows | Built In |
|-----|---------------|----------|
| **Live Overview** | Totals, records by source and match type, live intake pipeline, Dynamic Table refreshes, **Insert 10 synthetic arrivals** button | Sections 1–3 |
| **Constituent & Eligibility** | Search by name or master ID, linked source records, match scores, PASS/FAIL reason | Section 2–3 |
| **Ask Data + SQL** | Chat with the Cortex Agent; shows the SQL it ran and the query ID | Section 5 |
| **Duplicate Watchlist** | SNAP cases with multiple enrollments for the same resident | Section 3 |
| **Match Review Queue** | Unmatched records that may be the same person, with approve/reject | Section 2 |
| **Partner Sharing** | Preview of the secure view and the share | Section 4 |

### How It Works

The app is a standard Next.js project using the Snowflake App Runtime
SDK (`lib/snowflake.ts`). API routes in `app/api/` run parameterized
SQL against `KEYSTONE_DEMO` using `querySnowflake`. The Ask Data
route calls the Cortex Agent via `DATA_AGENT_RUN`. The React UI in
`ui/` is the client, rendered in the browser.

### Local Preview (Optional)

For development before deploying:

``` bash
cd keystone-console   # the cloned folder from the deploy step
npm install
SNOWFLAKE_CONNECTION_NAME=keystone npm run dev
```

Open `http://localhost:3000`. Queries authenticate through your `snow`
CLI connection.

## Best Practices

-   **Start with deterministic matching.** Exact keys such as SSN
    resolve most records before any fuzzy scoring.
-   **Use blocking keys.** Limit fuzzy comparisons, for example to the
    same ZIP and birth date window, so you don't compare every record
    to every other record.
-   **Send uncertain cases to people.** Route missing income and weak
    matches to manual review, never to an automatic pass.
-   **A duplicate flag is a lead, not proof of fraud.** Route it to
    review.
-   **Mask by default.** Apply masking policies when you create tables
    that hold PII. Share secure views, not base tables.
-   **Tune refresh cadence to business need.** Set Dynamic Table target
    lag based on how quickly caseworkers need new data, and monitor
    compute cost.
-   **Validate AI output.** Review agent answers and verify them against
    the SQL the agent ran.
-   **Audit access.** Use `ACCESS_HISTORY` to see who queried resident
    data.
-   **Start with a pilot.** Validate matching thresholds and the
    eligibility rule for one program before expanding.

## Clean Up

Remove the application service, the share, and the database. The
warehouse is left in place.

``` sql
-- From a Snowsight worksheet:
USE ROLE SYSADMIN;
DROP APPLICATION SERVICE IF EXISTS KEYSTONE_DEMO.APP.KEYSTONE_CASEWORKER_CONSOLE;

USE ROLE ACCOUNTADMIN;
DROP SHARE IF EXISTS KEYSTONE_PUBLIC_HEALTH_SHARE;
DROP DATABASE IF EXISTS KEYSTONE_DEMO;
```

Or from the CLI:

``` bash
cd keystone-console   # the cloned folder from the deploy step
snow app teardown --force --connection keystone
```

> The Dynamic Tables refresh every 1–5 minutes and the application
> service runs continuously; both use credits. Run the cleanup when
> you are done.

## Conclusion And Resources

This reference guide demonstrates how Snowflake can bring records from
disconnected program systems into a governed data foundation, resolve
them to one trusted record per resident, automate eligibility checks,
share data safely with partner agencies, and support caseworkers with
a Cortex Agent and a full web application deployed on Snowflake. The
included data is synthetic; adapt schemas, matching rules, policies,
and eligibility logic to your environment.

Useful documentation:

-   [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
-   [JAROWINKLER_SIMILARITY](https://docs.snowflake.com/en/sql-reference/functions/jarowinkler_similarity)
-   [Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
-   [Dynamic Data Masking](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro)
-   [Secure Data Sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro)
-   [Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
-   [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
-   [Snowflake App Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/about-snowflake-app-runtime)

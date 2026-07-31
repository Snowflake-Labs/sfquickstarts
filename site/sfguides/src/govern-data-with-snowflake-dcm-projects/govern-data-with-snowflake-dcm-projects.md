author: Yoav Ostrinsky
id: govern-data-with-snowflake-dcm-projects
summary: Learn how to manage Snowflake security and governance objects — tags, masking policies, a row access policy, and network/authentication policies — as code with DCM Projects.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/data-engineering
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/snowflake-dcm-projects
tags: Getting Started, DCM, Governance, Data Engineering

# Govern Data with Snowflake DCM Projects

<!-- ------------------------ -->
## Overview

Duration: 3

Security and governance objects — tags, masking policies, row access policies, network and authentication policies — are some of the most important objects in a Snowflake account, and some of the easiest to let drift when they're created by hand. In this quickstart you'll manage them **as code** with Snowflake DCM Projects, so their full lifecycle (create, alter, drop) is version-controlled and reproducible across environments.

You'll build a small customer dataset containing PII, define governance objects declaratively, and then prove that a restricted role sees **masked columns** and a **filtered set of rows** — all driven by DCM-defined policies.

### What You'll Learn
- How to define Snowflake tags and attach them to columns and tables with DCM (`DEFINE TAG`, `ATTACH TAG`)
- How to define a masking policy and apply it through **tag-based masking**
- How to define a **row access policy** (Early Access) for row-level security
- How to define network and authentication policies as code
- Why some policy *associations* are applied in a post-deploy script (current DCM limits)

### Prerequisites
- A Snowflake account with `ACCOUNTADMIN` access (to create roles and enable a preview parameter)
- Familiarity with DCM Projects basics — see [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/)
- Row access policy support in DCM is an Early Access capability; the rest are in Public Preview

<!-- ------------------------ -->
## Create a Workspace from Git

Duration: 3

In this step, you'll create a Snowsight Workspace linked to the sample DCM Projects repository on GitHub.

1. Navigate to **Projects > Workspaces** in Snowsight.
2. Click **Create** and select **From Git repository**.
3. Enter the repository URL: `https://github.com/snowflake-labs/snowflake-dcm-projects`
4. Select an API Integration for GitHub ([create one if needed](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git#label-create-a-git-workspace)).
5. Select **Public repository**.

Once the workspace is created, navigate to **Quickstarts/govern-data-with-snowflake-dcm-projects** to find the project files.

The `scripts/` folder contains numbered SQL files you'll run at different stages:

| File | When to Run |
|:-----|:------------|
| `01_pre_deploy.sql` | Before the first DCM Plan & Deploy |
| `02_post_deploy.sql` | After the first successful deployment |
| `03_cleanup.sql` | When you're done and want to tear everything down |

Open `scripts/01_pre_deploy.sql` in a Snowsight worksheet — you'll use it in the next step.

<!-- ------------------------ -->
## Set Up Roles, Grants, and Inherited Grants

Duration: 3

Run `scripts/01_pre_deploy.sql`. It creates a `DCM_DEVELOPER` role, grants the privileges DCM needs, enables inherited grants, and creates the DCM Project object the manifest references.

### 1. Create a DCM Developer Role

```sql
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS dcm_developer;
SET user_name = (SELECT CURRENT_USER());
GRANT ROLE dcm_developer TO USER IDENTIFIER($user_name);
```

### 2. Grant Infrastructure Privileges

```sql
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE dcm_developer;
GRANT CREATE ROLE ON ACCOUNT TO ROLE dcm_developer;
GRANT CREATE DATABASE ON ACCOUNT TO ROLE dcm_developer;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE dcm_developer;
-- Network policies are account-level objects, so the deploy role needs this:
GRANT CREATE NETWORK POLICY ON ACCOUNT TO ROLE dcm_developer;
```

The access definitions use `GRANT INHERITED` (a Public Preview feature), which requires a one-time account-level opt-in — independent of DCM:

```sql
ALTER ACCOUNT SET FEATURE_RBAC_INHERITED_GRANTS = 'ENABLED';
```

### 3. Create the DCM Project Object

```sql
USE ROLE dcm_developer;

CREATE DATABASE IF NOT EXISTS dcm_demo;
CREATE SCHEMA IF NOT EXISTS dcm_demo.projects;

CREATE OR REPLACE DCM PROJECT dcm_demo.projects.dcm_gov_project_dev
    COMMENT = 'for the Security & Governance Quickstart';
```

The last query in the script returns your `account_identifier` and `user_name` — paste the account identifier into the `DCM_DEV` target of `manifest.yml`.

> **Note:** After running this script, refresh your browser so Snowsight picks up the newly created DCM Project object.

<!-- ------------------------ -->
## Explore the Project Files

Duration: 5

Open the `DCM_Projects_Governance/sources/definitions/` folder:

| File | Contents |
|:-----|:---------|
| `infrastructure.sql` | Warehouse, the `DCM_DEMO_5` database, `RAW`/`GOV`/`SERVE` schemas, a restricted `ANALYST` role, and inherited grants |
| `raw.sql` | A `CUSTOMER` table with PII columns (email, phone, city) |
| `governance.sql` | Tags, a masking policy, a row access policy, network rule/policy, and an authentication policy — plus `ATTACH TAG` |

The heart of the demo is `governance.sql`. Note that DCM manages the **definitions** of every object below; a few *associations* are applied later in the post-deploy script (see the note at the end of this section).

Tags and a masking policy:

```sql
DEFINE TAG DCM_DEMO_5{{env_suffix}}.GOV.PII
    ALLOWED_VALUES 'PII';

DEFINE MASKING POLICY DCM_DEMO_5{{env_suffix}}.GOV.EMAIL_MASK
    AS (VAL STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'DCM_DEVELOPER') THEN VAL
        ELSE REGEXP_REPLACE(VAL, '.+\\@', '*****@')
    END
    COMMENT = 'Masks the local-part of an email for non-privileged roles';
```

A row access policy (Early Access) for row-level security:

```sql
DEFINE ROW ACCESS POLICY DCM_DEMO_5{{env_suffix}}.GOV.CUSTOMER_COUNTRY_FILTER
    AS (COUNTRY VARCHAR) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'DCM_DEVELOPER') THEN TRUE
        WHEN CURRENT_ROLE() = 'DCM_DEMO_5{{env_suffix}}_ANALYST' AND COUNTRY = 'USA' THEN TRUE
        ELSE FALSE
    END
    COMMENT = 'Privileged roles see all rows; the analyst role sees only USA customers';
```

The `EMAIL` column is tagged as PII with `ATTACH TAG`, which DCM reconciles on every deploy:

```sql
ATTACH TAG DCM_DEMO_5{{env_suffix}}.GOV.PII = 'PII'
    TO TABLE DCM_DEMO_5{{env_suffix}}.RAW.CUSTOMER
        COLUMN EMAIL;
```

`governance.sql` also defines a network rule + policy and an authentication policy. These are **created but never activated** in this demo — they show that account-security objects can be version-controlled with DCM.

> **Note (current DCM limits):** Attaching a masking policy to a column, associating a masking policy with a tag, and attaching a row access policy to a table are not yet expressible as DCM `DEFINE` statements. Those *associations* are applied in `02_post_deploy.sql`. DCM still owns the policy and tag **definitions**.

<!-- ------------------------ -->
## Plan and Deploy

Duration: 3

Select the `DCM_Projects_Governance` project and the `DCM_DEV` target in the DCM control panel, then run **Plan**. You should see the governance objects being created: the database, schemas, `CUSTOMER` table, both tags, the masking policy, the row access policy, the network rule/policy, and the authentication policy.

Once the plan looks correct, set the operation to **Deploy** and run it.

> **CLI Alternative:**
> ```
> snow dcm plan DCM_DEMO.PROJECTS.DCM_GOV_PROJECT_DEV --target DCM_DEV --save-output
> snow dcm deploy DCM_DEMO.PROJECTS.DCM_GOV_PROJECT_DEV --target DCM_DEV --alias "initial"
> ```

<!-- ------------------------ -->
## Apply Governance and Load Data

Duration: 4

Open `scripts/02_post_deploy.sql`. It seeds sample PII data, wires up the policy associations that DCM can't yet express, and grants you the restricted analyst role.

### 1. Seed sample customer data

The script inserts five customers across the USA, UK, and Italy.

### 2. Tag-based masking

```sql
ALTER TAG dcm_demo_5_dev.gov.pii SET MASKING POLICY dcm_demo_5_dev.gov.email_mask;
```

Any column tagged `GOV.PII` (here, `EMAIL`) is now masked by `EMAIL_MASK` for non-privileged roles.

> **Note:** If this statement runs immediately after deploy and returns a transient error, wait a few seconds and re-run it — the masking policy metadata may still be propagating.

### 3. Row-level security

```sql
ALTER TABLE dcm_demo_5_dev.raw.customer
    ADD ROW ACCESS POLICY dcm_demo_5_dev.gov.customer_country_filter ON (COUNTRY);
```

### 4. Grant the analyst role

```sql
GRANT ROLE dcm_demo_5_dev_analyst TO USER IDENTIFIER($user_name);
```

<!-- ------------------------ -->
## Prove It: Masking and Row-Level Security by Role

Duration: 3

Run the final two queries in the script. As the privileged `DCM_DEVELOPER` role, you see every row with clear emails:

```sql
USE ROLE dcm_developer;
SELECT customer_id, first_name, email, country FROM dcm_demo_5_dev.raw.customer ORDER BY customer_id;
```

| CUSTOMER_ID | FIRST_NAME | EMAIL | COUNTRY |
|:--|:--|:--|:--|
| 1 | Alice | alice.johnson@example.com | USA |
| 2 | Bob | bob.smith@example.com | USA |
| 3 | Chloe | chloe.martin@example.co.uk | UK |
| 4 | David | david.nguyen@example.com | USA |
| 5 | Elena | elena.rossi@example.it | Italy |

Now switch to the restricted analyst role:

```sql
USE ROLE dcm_demo_5_dev_analyst;
SELECT customer_id, first_name, email, country FROM dcm_demo_5_dev.raw.customer ORDER BY customer_id;
```

| CUSTOMER_ID | FIRST_NAME | EMAIL | COUNTRY |
|:--|:--|:--|:--|
| 1 | Alice | *****@example.com | USA |
| 2 | Bob | *****@example.com | USA |
| 4 | David | *****@example.com | USA |

The analyst sees **only USA rows** (the row access policy filtered out the UK and Italy customers) **and** a **masked email** (the tag-based masking policy) — both enforced by policies DCM manages as code.

<!-- ------------------------ -->
## Cleanup

Duration: 2

Run `scripts/03_cleanup.sql` to tear everything down. It first removes the policy associations that were applied outside DCM, then purges the project:

```sql
ALTER TAG IF EXISTS dcm_demo_5_dev.gov.pii UNSET MASKING POLICY dcm_demo_5_dev.gov.email_mask;
ALTER TABLE IF EXISTS dcm_demo_5_dev.raw.customer DROP ROW ACCESS POLICY dcm_demo_5_dev.gov.customer_country_filter;

EXECUTE DCM PROJECT dcm_demo.projects.dcm_gov_project_dev PURGE;
DROP DCM PROJECT IF EXISTS dcm_demo.projects.dcm_gov_project_dev;
```

<!-- ------------------------ -->
## Conclusion and Resources

Duration: 1

You managed a full set of Snowflake governance objects as code with DCM Projects, and proved that a restricted role is protected by both column masking and row-level security — all reproducible across environments.

### What You Learned
- Defining tags, masking policies, a row access policy, and network/authentication policies with DCM
- Applying tag-based masking and row-level security, and where policy associations live today
- Enabling inherited grants and using a least-privilege analyst role

### Related Resources
- [Managing DCM Projects](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-overview)
- [Column-level security (masking policies)](https://docs.snowflake.com/en/user-guide/security-column-intro)
- [Row access policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Object tagging](https://docs.snowflake.com/en/user-guide/object-tagging)

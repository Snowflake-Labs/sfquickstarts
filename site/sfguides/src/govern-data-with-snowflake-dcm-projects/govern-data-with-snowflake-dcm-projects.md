author: Yoav Ostrinsky
id: govern-data-with-snowflake-dcm-projects
summary: Learn how to manage Snowflake security and governance objects — tags, masking policies, a row access policy, and network/authentication policies — as code with DCM Projects.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/data-engineering
environments: web
status: Draft
language: en
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
- How to define a masking policy and attach it to a column with DCM (DEFINE MASKING POLICY, ATTACH MASKING POLICY)
- How to define a row access policy and attach it to a table with DCM (DEFINE ROW ACCESS POLICY, ATTACH ROW ACCESS POLICY)
- How to define network and authentication policies as code, and activate them on a dedicated demo user
- Which policy *associations* still run in a post-deploy script (current DCM limits)

### Prerequisites
- A Snowflake account with ACCOUNTADMIN access (to create roles and a service user, and to enable inherited grants)
- Familiarity with DCM Projects basics — see [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/)
- Check the product docs for the current availability of the DCM governance statements used in this guide

<!-- ------------------------ -->
## Create a Workspace from Git

Duration: 3

In this step, you'll create a Snowsight Workspace linked to the sample DCM Projects repository on GitHub.

1. Navigate to **Projects > Workspaces** in Snowsight.
2. Click **Create** and select **From Git repository**.
3. Enter the repository URL: https://github.com/snowflake-labs/snowflake-dcm-projects
4. Select an API Integration for GitHub ([create one if needed](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git#label-create-a-git-workspace)).
5. Select **Public repository**.

Once the workspace is created, navigate to **Quickstarts/govern-data-with-snowflake-dcm-projects** to find the project files.

The `scripts/` folder contains numbered SQL files you'll run at different stages:

| File | When to Run |
|:-----|:------------|
| 01_pre_deploy.sql | Before the first DCM Plan & Deploy |
| 02_post_deploy.sql | After the first successful deployment |
| 03_cleanup.sql | When you're done and want to tear everything down |

Open `scripts/01_pre_deploy.sql` in a Snowsight worksheet — you'll use it in the next step.

<!-- ------------------------ -->
## Set Up Roles, Grants, and the Demo Service User

Duration: 3

Before deploying, you need a dedicated DCM developer role, a DCM Project object, and a service user to activate the demo network and authentication policies on.

Open `scripts/01_pre_deploy.sql` in a Snowsight worksheet and run each section in order. This script lives outside the DCM project directory, so it won't be picked up by Plan or Deploy.

### 1. Create a DCM Developer Role

```sql
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS dcm_developer;
SET user_name = (SELECT CURRENT_USER());
GRANT ROLE dcm_developer TO USER IDENTIFIER($user_name);
```

### 2. Enable Inherited Grants

> **Inherited grants.** An `INHERITED` grant covers current *and* future objects of a type inside a container, as one grant rather than one per object. This project's analyst-role grants use them. They require a one-time, account-level opt-in that is independent of DCM, and cannot be combined with WITH GRANT OPTION, `CASCADE` or `RESTRICT`.

```sql
ALTER ACCOUNT SET FEATURE_RBAC_INHERITED_GRANTS = 'ENABLED';
```

### 3. Grant Account-Level Privileges

Account-level privileges cannot be granted by a project on itself, so they all happen here, before the first plan. The script grants DCM_DEVELOPER a **superset**: every guide in this series shares this role, so one run of any guide's pre-deploy script prepares you for all of them, and each grant carries a comment saying what capability it buys. The ones this guide relies on are the network and authentication policy privileges:

```sql
GRANT CREATE NETWORK POLICY       ON ACCOUNT TO ROLE dcm_developer;
GRANT APPLY AUTHENTICATION POLICY ON ACCOUNT TO ROLE dcm_developer;
```

Network policies are account-level objects, so creating one needs an account-level privilege, and setting an authentication policy on a user needs APPLY AUTHENTICATION POLICY. DCM_DEVELOPER owns the masking and row access policies it deploys, which is enough to attach them to its own objects; the script also grants the APPLY privileges for tags and policies, which cover the case where the target object is owned by another role.

### 4. Create the DCM Project Object

```sql
USE ROLE dcm_developer;

CREATE DATABASE IF NOT EXISTS dcm_demo;
CREATE SCHEMA IF NOT EXISTS dcm_demo.projects;

CREATE DCM PROJECT IF NOT EXISTS dcm_demo.projects.dcm_gov_project_dev
    COMMENT = 'for the Security & Governance Quickstart';
```

### 5. Create the Demo Service User

Users are account-level objects — they live outside any DCM Project. The post-deploy script activates the network and authentication policies on this user. Owning the user is what lets DCM_DEVELOPER set its network policy:

```sql
USE ROLE ACCOUNTADMIN;

CREATE USER IF NOT EXISTS dcm_demo_5_dev_svc
    TYPE = SERVICE
    COMMENT = 'Demo service user for the Security & Governance Quickstart; target of the demo network and authentication policies';
GRANT OWNERSHIP ON USER dcm_demo_5_dev_svc TO ROLE dcm_developer COPY CURRENT GRANTS;
```

> **Caution:** Activate the demo policies only on this service user. Don't set them on your own user or on the account — a network policy activated at the account level applies to every user and can lock you out.

The last query in the script returns your account_identifier and user_name — paste the account identifier into the DCM_DEV target of `manifest.yml`.

> **Note:** After running this script, refresh your browser so Snowsight picks up the newly created DCM Project object.

<!-- ------------------------ -->
---
## Explore the Project Files

Duration: 5

Open the `DCM_Projects_Governance/sources/definitions/` folder:

| File | Contents |
|:-----|:---------|
| infrastructure.sql | Warehouse, the DCM_DEMO_5 database, RAW/GOV/SERVE schemas, a restricted ANALYST role, and inherited grants |
| raw.sql | A CUSTOMER table with PII columns (email, phone, city) |
| governance.sql | Tags, a masking policy, a row access policy, network rule/policy, and an authentication policy — plus ATTACH TAG, ATTACH MASKING POLICY, and ATTACH ROW ACCESS POLICY |

The heart of the demo is `governance.sql`. DCM manages the **definitions** of every object below and attaches the tags, the masking policy, and the row access policy; a few other *associations* are applied later in the post-deploy script (see the note at the end of this section).

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

A row access policy for row-level security:

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

The row access policy is attached to CUSTOMER with ATTACH ROW ACCESS POLICY:

```sql
ATTACH ROW ACCESS POLICY DCM_DEMO_5{{env_suffix}}.GOV.CUSTOMER_COUNTRY_FILTER
    TO TABLE DCM_DEMO_5{{env_suffix}}.RAW.CUSTOMER ON (COUNTRY);
```

DCM replaces a row access policy that was attached to the table outside DCM. If you remove the ATTACH ROW ACCESS POLICY statement, DCM detaches the policy from the table on the next deployment. If another DCM project already manages the attachment on that table, the deployment fails.

The EMAIL column is tagged as PII with `ATTACH TAG`, which DCM reconciles on every deploy:

```sql
ATTACH TAG DCM_DEMO_5{{env_suffix}}.GOV.PII = 'PII'
    TO TABLE DCM_DEMO_5{{env_suffix}}.RAW.CUSTOMER
        COLUMN EMAIL;
```

The masking policy is attached to the same column with ATTACH MASKING POLICY:

```sql
ATTACH MASKING POLICY DCM_DEMO_5{{env_suffix}}.GOV.EMAIL_MASK
    TO TABLE DCM_DEMO_5{{env_suffix}}.RAW.CUSTOMER
        COLUMN EMAIL;
```

DCM applies the declared policy with the FORCE option, so it replaces a masking policy that was attached to the column outside DCM. If you remove the ATTACH MASKING POLICY statement, DCM detaches the policy from the column on the next deployment. If another DCM project already manages the attachment on that column, the deployment fails.

`governance.sql` also defines a network rule + policy and an authentication policy. DCM creates them, and the post-deploy script activates both on the demo service user — showing that account-security objects can be version-controlled with DCM.

> **Note (current DCM limits):** These associations aren't yet expressible in DCM and are applied in `02_post_deploy.sql`: associating a masking policy with a tag (tag-based masking), and assigning network and authentication policies to a user or the account (ALTER USER / ALTER ACCOUNT). DCM still owns the policy and tag **definitions**.

<!-- ------------------------ -->
## Plan and Deploy

Duration: 3

Select the DCM_Projects_Governance project and the DCM_DEV target in the DCM control panel, then run **Plan**. You should see the governance objects being created: the database, schemas, CUSTOMER table, both tags, the masking policy, the row access policy, the network rule/policy, and the authentication policy. The CUSTOMER table shows the row access policy being set, and the EMAIL column shows the masking policy being set.

Once the plan looks correct, set the operation to **Deploy** and run it.

> **CLI Alternative:**
> ```
> snow dcm plan DCM_DEMO.PROJECTS.DCM_GOV_PROJECT_DEV --target DCM_DEV --save-output
> snow dcm deploy DCM_DEMO.PROJECTS.DCM_GOV_PROJECT_DEV --target DCM_DEV --alias "initial"
> ```

<!-- ------------------------ -->
## Apply Governance and Load Data

Duration: 4

Open `scripts/02_post_deploy.sql`. It seeds sample PII data, wires up the remaining policy associations that DCM can't yet express, and grants you the restricted analyst role. The EMAIL column is already masked, and the CUSTOMER table is already filtered by role: DCM already attached the masking and row access policies during deployment.

### 1. Seed sample customer data

The script inserts five customers across the USA, UK, and Italy.

### 2. Tag-based masking

```sql
ALTER TAG dcm_demo_5_dev.gov.pii SET MASKING POLICY dcm_demo_5_dev.gov.email_mask;
```

Any column you tag GOV.PII later is now masked by EMAIL_MASK too. On EMAIL, the policy that DCM attached directly takes precedence over the tag-based one.

> **Note:** If this statement runs immediately after deploy and returns a transient error, wait a few seconds and re-run it — the masking policy metadata may still be propagating.

### 3. Activate the network and authentication policies

```sql
ALTER USER dcm_demo_5_dev_svc SET NETWORK_POLICY = dcm_demo_5_dev_policy;
ALTER USER dcm_demo_5_dev_svc SET AUTHENTICATION POLICY dcm_demo_5_dev.gov.pat_policy;
```

The script then confirms that both policies are assigned to the service user:

```sql
SELECT policy_name, policy_kind, ref_entity_name
    FROM TABLE(dcm_demo_5_dev.INFORMATION_SCHEMA.POLICY_REFERENCES(
        REF_ENTITY_NAME => 'dcm_demo_5_dev_svc', REF_ENTITY_DOMAIN => 'user'));
```

| POLICY_NAME | POLICY_KIND | REF_ENTITY_NAME |
|:--|:--|:--|
| PAT_POLICY | AUTHENTICATION_POLICY | DCM_DEMO_5_DEV_SVC |
| DCM_DEMO_5_DEV_POLICY | NETWORK_POLICY | DCM_DEMO_5_DEV_SVC |

> **Note:** To enforce a network policy for every user, a role with the global ATTACH POLICY privilege runs ALTER ACCOUNT SET NETWORK_POLICY = ...; the same applies to ALTER ACCOUNT SET AUTHENTICATION POLICY ... with APPLY AUTHENTICATION POLICY. This quickstart doesn't do that, because an account-level network policy can lock users out of the account.

### 4. Grant the analyst role

```sql
GRANT ROLE dcm_demo_5_dev_analyst TO USER IDENTIFIER($user_name);
```

<!-- ------------------------ -->
## Prove It: Masking and Row-Level Security by Role

Duration: 3

Run the final two queries in the script. As the privileged DCM_DEVELOPER role, you see every row with clear emails:

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

The analyst sees **only USA rows** (the row access policy DCM attached filtered out the UK and Italy customers) **and** a **masked email** (the masking policy DCM attached with ATTACH MASKING POLICY) — both enforced by policies DCM manages as code.

<!-- ------------------------ -->
## Cleanup

Duration: 2

When you're done, open `scripts/03_cleanup.sql` in a Snowsight worksheet and run it. It first removes the policy associations that `02_post_deploy.sql` applied outside DCM — a network policy can't be dropped while it's assigned to a user, and `PURGE` fails on a masking policy that is still set on a tag:

```sql
ALTER USER IF EXISTS dcm_demo_5_dev_svc UNSET NETWORK_POLICY;
ALTER USER IF EXISTS dcm_demo_5_dev_svc UNSET AUTHENTICATION POLICY;
ALTER TAG IF EXISTS dcm_demo_5_dev.gov.pii UNSET MASKING POLICY dcm_demo_5_dev.gov.email_mask;
```

Then it purges everything the project manages, drops the now-empty project object, and drops the service user this guide created:

```sql
EXECUTE DCM PROJECT dcm_demo.projects.dcm_gov_project_dev PURGE;

DROP DCM PROJECT IF EXISTS dcm_demo.projects.dcm_gov_project_dev;
DROP USER IF EXISTS dcm_demo_5_dev_svc;
```

`PURGE` drops every object the project created — database, schemas, table, tag, masking and row access policies, network rule and policy, authentication policy, warehouse, the analyst role, and all their data — and detaches the masking and row access policies DCM attached. It is irreversible, and it leaves the project object behind, which is why the `DROP` follows.

The dcm_demo database, its projects schema and the dcm_developer role are shared across every guide in this series, so the script leaves them in place, commented out. The dcm_demo.projects schema holds the project objects for every DCM guide in this series, so only drop it once you have finished with all of them. Check what it contains first:

```sql
SHOW DCM PROJECTS IN SCHEMA dcm_demo.projects;
```

The inherited-grants account parameter enabled during setup also stays on. It is account-wide and the other guides in this series need it; the script carries the commented-out line to turn it off:

```sql
-- ALTER ACCOUNT SET FEATURE_RBAC_INHERITED_GRANTS = 'DISABLED';
```

If `PURGE` ever fails, note that it is not transactional, so some objects may already be gone. The known cause in this guide is a masking policy still set on a tag: re-run the ALTER TAG statement above, then re-run `PURGE`.

<!-- ------------------------ -->
## Conclusion and Resources

Duration: 1

You managed a full set of Snowflake governance objects as code with DCM Projects, and proved that a restricted role is protected by both column masking and row-level security — all reproducible across environments.

### What You Learned
- Defining tags, masking policies, a row access policy, and network/authentication policies with DCM
- Attaching a masking policy and a row access policy with ATTACH MASKING POLICY / ATTACH ROW ACCESS POLICY, and where the remaining associations live today
- Activating network and authentication policies on a dedicated user instead of the account
- Enabling inherited grants and using a least-privilege analyst role

### Related Resources
- [Managing DCM Projects](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-overview)
- [Column-level security (masking policies)](https://docs.snowflake.com/en/user-guide/security-column-intro)
- [Row access policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Object tagging](https://docs.snowflake.com/en/user-guide/object-tagging)

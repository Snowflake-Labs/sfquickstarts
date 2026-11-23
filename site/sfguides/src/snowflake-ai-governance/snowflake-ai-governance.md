---
authors: Wondi Wolde
id: snowflake-ai-governance
language: en
summary: Learn to build a production-grade autonomous governance system in Snowflake using stored procedures, tasks, and Streamlit.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/wondisha/snowflake-ai-governance
open in snowflake:
---

# Build an Autonomous AI Governance System in Snowflake

## Overview

This hands-on guide walks you through building a complete, production-grade governance system in Snowflake from scratch. You will implement automated user lifecycle management, scheduled cleanup tasks, comprehensive audit logging, and a real-time Streamlit monitoring dashboard.

**Estimated Duration:** 4–6 hours  
**Difficulty Level:** Intermediate  

### Prerequisites
* A Snowflake account with `ACCOUNTADMIN` role privileges
* Basic familiarity with SQL and Python
* Familiarity with Snowsight

### What You'll Learn
* How to design relational database schemas for Snowflake governance and compliance
* How to implement Snowflake Scripting stored procedures for automated user lifecycle management
* How to schedule and monitor autonomous workflows using Snowflake Tasks and CRON
* How to maintain complete audit trails and archived user records
* How to deploy a multi-page Streamlit in Snowflake dashboard for real-time governance monitoring

### What You'll Need
* Snowsight access with an active warehouse (e.g., `COMPUTE_WH`)
* Git installed locally to clone the source repository
* Python 3.8+ (optional, for running local deployment scripts)

### What You'll Build
* A dedicated `GOVERNANCE` database and schema with 20+ governance, policy, and audit tables
* Four modular Snowflake SQL stored procedures (`IDENTIFY_INACTIVE_USERS`, `REVOKE_INACTIVE_USER_ROLES`, `DISABLE_INACTIVE_USER`, and `REMOVE_INACTIVE_USER_COMPLETE`)
* An automated weekly Snowflake Task (`INACTIVE_USER_CLEANUP_TASK_AUTO`) to enforce inactivity policies
* An 8-page Streamlit in Snowflake dashboard for real-time observability and manual governance actions

## Environment Setup

Before building the governance system, verify your Snowflake permissions and clone the companion repository containing the table DDL and Streamlit dashboard code.

### Step 1: Verify Your Snowflake Access

Open a SQL worksheet in Snowsight and run the following query to confirm your active user, role, and warehouse:

```sql
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
```

**Expected output:**
* **User:** Your admin username
* **Role:** `ACCOUNTADMIN`
* **Warehouse:** Any active warehouse (e.g., `COMPUTE_WH`)

### Step 2: Clone the Repository

Clone the [Snowflake AI Governance repository](https://github.com/wondisha/snowflake-ai-governance) to access the schema definitions and dashboard source code:

```bash
git clone https://github.com/wondisha/snowflake-ai-governance.git
cd snowflake-ai-governance
```

## Database Schema Foundation

In this step, you will create the `GOVERNANCE` database and schema and deploy the core tables required to track policies, user activity, incidents, and audit events.

### Exercise 1.1: Create Database and Schema

Run the following SQL in Snowsight to initialize your governance environment:

```sql
CREATE DATABASE IF NOT EXISTS GOVERNANCE;
USE DATABASE GOVERNANCE;

CREATE SCHEMA IF NOT EXISTS GOVERNANCE;
USE SCHEMA GOVERNANCE;

-- Verify database and schema creation
SELECT DATABASE_NAME, SCHEMA_NAME 
FROM INFORMATION_SCHEMA.SCHEMATA 
WHERE DATABASE_NAME = 'GOVERNANCE';
```

**Checkpoint:** Confirm that the query returns the `GOVERNANCE` database and `GOVERNANCE` schema.

### Exercise 1.2: Deploy Governance Tables

Execute the DDL script located at [`src/database/schema.sql`](https://github.com/wondisha/snowflake-ai-governance/blob/main/src/database/schema.sql) in Snowsight to create the 20+ governance tables.

**Key tables created:**
* `POLICIES` – Stores active governance rules and thresholds
* `AUDIT_LOGS` – Tracks all automated and manual system actions
* `USER_ACTIVITY_LOG` – Tracks user login timestamps, inactivity duration, and lifecycle status
* `ARCHIVED_USERS` – Retains historical records of removed users for compliance
* `INCIDENTS` – Logs detected governance violations

Verify that all tables were created:

```sql
SHOW TABLES IN GOVERNANCE.GOVERNANCE;
```

**Checkpoint:** You should see 20+ tables listed in `GOVERNANCE.GOVERNANCE`.

## Stored Procedures

Next, you will build the core automation engine using Snowflake Scripting stored procedures to detect, disable, revoke access from, and archive inactive users.

### Exercise 2.1: Create IDENTIFY_INACTIVE_USERS Procedure

This procedure scans `INFORMATION_SCHEMA.USERS`, calculates days since each user's last login (or creation date if they have never logged in), and upserts the results into `USER_ACTIVITY_LOG`:

```sql
USE DATABASE GOVERNANCE;
USE SCHEMA GOVERNANCE;

CREATE OR REPLACE PROCEDURE IDENTIFY_INACTIVE_USERS()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
  MERGE INTO USER_ACTIVITY_LOG target
  USING (
    SELECT
      USER_NAME,
      CREATED_ON,
      LAST_LOGIN,
      EMAIL,
      DATEDIFF(DAY,
        CASE WHEN LAST_LOGIN IS NULL THEN CREATED_ON ELSE LAST_LOGIN END,
        CURRENT_TIMESTAMP()
      ) AS DAYS_INACTIVE
    FROM INFORMATION_SCHEMA.USERS
    WHERE DELETED_ON IS NULL
  ) source
  ON target.USER_NAME = source.USER_NAME
  WHEN MATCHED THEN
    UPDATE SET
      target.DAYS_INACTIVE = source.DAYS_INACTIVE,
      target.LAST_LOGIN = source.LAST_LOGIN,
      target.UPDATED_AT = CURRENT_TIMESTAMP()
  WHEN NOT MATCHED THEN
    INSERT (
      ACTIVITY_ID,
      USER_NAME,
      USER_EMAIL,
      LAST_LOGIN,
      DAYS_INACTIVE,
      STATUS,
      CREATED_AT
    )
    VALUES (
      SUBSTRING(UUID_STRING(), 0, 36),
      source.USER_NAME,
      COALESCE(source.EMAIL, 'N/A'),
      source.LAST_LOGIN,
      source.DAYS_INACTIVE,
      'active',
      CURRENT_TIMESTAMP()
    );

  RETURN 'Scanned users and updated activity log';
END;
```

Test the procedure and inspect the populated log:

```sql
CALL IDENTIFY_INACTIVE_USERS();
SELECT USER_NAME, DAYS_INACTIVE FROM USER_ACTIVITY_LOG LIMIT 10;
```

**Checkpoint:** The procedure completes without errors and `USER_ACTIVITY_LOG` is populated.

### Exercise 2.2: Create REVOKE_INACTIVE_USER_ROLES Procedure

This procedure iterates through all roles granted to a target user, revokes them dynamically, and writes an entry to `AUDIT_LOGS`. Note the `:PARAM_NAME` bind syntax required for Snowflake Scripting variables:

```sql
CREATE OR REPLACE PROCEDURE REVOKE_INACTIVE_USER_ROLES(USER_NAME_TO_REVOKE VARCHAR)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
  DECLARE
    role_cursor CURSOR FOR
      SELECT DISTINCT ROLE
      FROM INFORMATION_SCHEMA.GRANTED_ROLES_IN_HIERARCHY
      WHERE GRANTEE_NAME = :USER_NAME_TO_REVOKE
      AND GRANTEE_TYPE = 'USER';

    role_name VARCHAR;
    revoked_count INT := 0;
  BEGIN
    FOR role IN role_cursor DO
      BEGIN
        EXECUTE IMMEDIATE 'REVOKE ROLE "' || role.ROLE || '" FROM USER "' || :USER_NAME_TO_REVOKE || '"';
        revoked_count := revoked_count + 1;
      EXCEPTION WHEN OTHER THEN
        NULL;
      END;
    END FOR;

    INSERT INTO AUDIT_LOGS (
      AUDIT_LOG_ID, EVENT_TYPE, EVENT_CATEGORY, RESOURCE_NAME,
      ACTOR_EMAIL, ACTION_DESCRIPTION, STATUS, CREATED_AT, UPDATED_AT, IS_AUTOMATED
    ) VALUES (
      SUBSTRING(UUID_STRING(), 0, 36),
      'roles_revoked',
      'security',
      :USER_NAME_TO_REVOKE,
      'system@governance',
      'All roles revoked from user: ' || :USER_NAME_TO_REVOKE,
      'success',
      CURRENT_TIMESTAMP(),
      CURRENT_TIMESTAMP(),
      TRUE
    );

    RETURN 'Revoked roles from ' || :USER_NAME_TO_REVOKE;
  END;
END;
```

**Checkpoint:** The procedure compiles cleanly with no invalid identifier errors.

### Exercise 2.3: Create DISABLE_INACTIVE_USER Procedure

This procedure marks a user's status as `disabled` in `USER_ACTIVITY_LOG`. Note that `"STATUS"` is enclosed in double quotes because `STATUS` is a reserved keyword in Snowflake:

```sql
CREATE OR REPLACE PROCEDURE DISABLE_INACTIVE_USER(USR VARCHAR, REASON VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
  UPDATE USER_ACTIVITY_LOG 
  SET "STATUS" = 'disabled', UPDATED_AT = CURRENT_TIMESTAMP()
  WHERE USER_NAME = :USR;
  
  RETURN 'Disabled: ' || :USR;
END;
```

Test the procedure:

```sql
CALL DISABLE_INACTIVE_USER('TEST_USER', 'Lab test');
```

**Checkpoint:** The procedure returns `Disabled: TEST_USER`.

### Exercise 2.4: Create REMOVE_INACTIVE_USER_COMPLETE Procedure

This orchestrator procedure executes the full offboarding workflow: revoking roles, updating the user's status to `removed`, copying the record into `ARCHIVED_USERS`, and recording the completion event in `AUDIT_LOGS`:

```sql
CREATE OR REPLACE PROCEDURE REMOVE_INACTIVE_USER_COMPLETE(USR VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
  -- Step 1: Revoke roles
  CALL REVOKE_INACTIVE_USER_ROLES(:USR);

  -- Step 2: Update status
  UPDATE USER_ACTIVITY_LOG
  SET "STATUS" = 'removed', UPDATED_AT = CURRENT_TIMESTAMP()
  WHERE USER_NAME = :USR;

  -- Step 3: Archive
  INSERT INTO ARCHIVED_USERS (ARCHIVE_ID, USER_NAME, USER_EMAIL, ARCHIVED_ON)
  SELECT
    SUBSTRING(UUID_STRING(), 0, 36),
    USER_NAME,
    USER_EMAIL,
    CURRENT_TIMESTAMP()
  FROM USER_ACTIVITY_LOG
  WHERE USER_NAME = :USR;

  -- Step 4: Log
  INSERT INTO AUDIT_LOGS (
    AUDIT_LOG_ID, EVENT_TYPE, EVENT_CATEGORY, RESOURCE_NAME,
    ACTOR_EMAIL, ACTION_DESCRIPTION, STATUS, CREATED_AT, UPDATED_AT, IS_AUTOMATED
  ) VALUES (
    SUBSTRING(UUID_STRING(), 0, 36),
    'user_removal_complete',
    'security',
    :USR,
    'system@governance',
    'User removed: ' || :USR,
    'success',
    CURRENT_TIMESTAMP(),
    CURRENT_TIMESTAMP(),
    TRUE
  );

  RETURN 'User ' || :USR || ' removed successfully';
END;
```

**Checkpoint:** All four stored procedures are created in `GOVERNANCE.GOVERNANCE`.

## Task Scheduling

In this step, you will automate the inactive user cleanup workflow using a scheduled Snowflake Task.

### Exercise 3.1: Create the Automatic Cleanup Task

Create a task scheduled to run every Monday at midnight UTC (`0 0 * * 1 UTC`) that identifies inactive users and automatically removes any user inactive for 90 or more days:

```sql
USE DATABASE GOVERNANCE;
USE SCHEMA GOVERNANCE;

CREATE OR REPLACE TASK INACTIVE_USER_CLEANUP_TASK_AUTO
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 0 * * 1 UTC'  -- Weekly Monday midnight UTC
AS
BEGIN
  -- Identify inactive users
  CALL IDENTIFY_INACTIVE_USERS();

  -- Remove each qualifying user
  FOR record IN (
    SELECT USER_NAME, DAYS_INACTIVE
    FROM USER_ACTIVITY_LOG
    WHERE DAYS_INACTIVE >= 90
      AND "STATUS" IN ('active', 'flagged')
  )
  DO
    BEGIN
      CALL REMOVE_INACTIVE_USER_COMPLETE(record.USER_NAME);
    EXCEPTION WHEN OTHER THEN
      NULL;
    END;
  END FOR;
END;

-- Enable the task
ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO RESUME;
```

Verify the task state and next scheduled run time:

```sql
SHOW TASKS LIKE 'INACTIVE_USER_CLEANUP_TASK_AUTO' IN SCHEMA GOVERNANCE.GOVERNANCE;
```

**Checkpoint:** Confirm that the task `state` column displays `started`.

## Testing and Validation

Before deploying the dashboard, validate the end-to-end lifecycle workflow using synthetic test records.

### Exercise 4.1: Create Test Users

Insert three simulated inactive users into `USER_ACTIVITY_LOG`:

```sql
INSERT INTO USER_ACTIVITY_LOG (
  ACTIVITY_ID, USER_NAME, USER_EMAIL, LAST_LOGIN, 
  DAYS_INACTIVE, STATUS, CREATED_AT
)
VALUES
  (SUBSTRING(UUID_STRING(), 0, 36), 'LAB_TEST_USER_1', 'lab1@test.com', 
   DATEADD(day, -120, CURRENT_TIMESTAMP()), 120, 'active', CURRENT_TIMESTAMP()),
  
  (SUBSTRING(UUID_STRING(), 0, 36), 'LAB_TEST_USER_2', 'lab2@test.com', 
   DATEADD(day, -105, CURRENT_TIMESTAMP()), 105, 'active', CURRENT_TIMESTAMP()),
  
  (SUBSTRING(UUID_STRING(), 0, 36), 'LAB_TEST_USER_3', 'lab3@test.com', 
   DATEADD(day, -95, CURRENT_TIMESTAMP()), 95, 'active', CURRENT_TIMESTAMP());

-- Verify insertion
SELECT USER_NAME, DAYS_INACTIVE, "STATUS" 
FROM USER_ACTIVITY_LOG 
WHERE USER_NAME LIKE 'LAB_TEST_%'
ORDER BY DAYS_INACTIVE DESC;
```

**Expected output:** 3 rows returned, all with `STATUS = 'active'`.

### Exercise 4.2: Run Procedures Manually

Execute the full offboarding sequence on `LAB_TEST_USER_1`:

```sql
CALL IDENTIFY_INACTIVE_USERS();
CALL DISABLE_INACTIVE_USER('LAB_TEST_USER_1', 'Lab testing');
CALL REVOKE_INACTIVE_USER_ROLES('LAB_TEST_USER_1');
CALL REMOVE_INACTIVE_USER_COMPLETE('LAB_TEST_USER_1');

-- Verify status transitions
SELECT USER_NAME, "STATUS" 
FROM USER_ACTIVITY_LOG 
WHERE USER_NAME LIKE 'LAB_TEST_%'
ORDER BY USER_NAME;
```

**Expected output:**
* `LAB_TEST_USER_1` → `removed`
* `LAB_TEST_USER_2` → `active`
* `LAB_TEST_USER_3` → `active`

### Exercise 4.3: Check Audit Trail

Verify that each lifecycle action generated an audit record:

```sql
SELECT 
  EVENT_TYPE, 
  RESOURCE_NAME, 
  ACTION_DESCRIPTION, 
  CREATED_AT
FROM AUDIT_LOGS
WHERE RESOURCE_NAME LIKE 'LAB_TEST_%'
ORDER BY CREATED_AT DESC;
```

**Expected output:** Multiple audit log entries showing role revocation and user removal completion.

### Exercise 4.4: Verify Archived Users

Confirm that `LAB_TEST_USER_1` was written to `ARCHIVED_USERS`:

```sql
SELECT USER_NAME, ARCHIVED_ON 
FROM ARCHIVED_USERS
WHERE USER_NAME LIKE 'LAB_TEST_%';
```

**Checkpoint:** `LAB_TEST_USER_1` appears in `ARCHIVED_USERS` with a complete audit trail in `AUDIT_LOGS`.

## Deploy Monitoring Dashboard

In this step, you will deploy the 8-page Streamlit in Snowflake application to visualize governance metrics and trigger manual actions.

### Exercise 5.1: Deploy Streamlit Dashboard

1. In Snowsight, navigate to **Projects** → **Streamlit** and click **+ Streamlit App**.
2. Name the app **Governance Dashboard**, select the `GOVERNANCE` database and `GOVERNANCE` schema, and choose your warehouse (e.g., `COMPUTE_WH`).
3. Copy the entire contents of [`streamlit_governance_dashboard.py`](https://github.com/wondisha/snowflake-ai-governance/blob/main/streamlit_governance_dashboard.py) from the cloned repository and paste it into the Snowsight Streamlit editor.
4. Click **Run** in the upper-right corner.

**Checkpoint:** The Streamlit dashboard loads without errors and displays all 8 navigation pages.

### Exercise 5.2: Navigate Dashboard Pages

Explore the core views in your deployed application:
* **Overview Page:** Review top-level system health metrics and recent `AUDIT_LOGS` entries, including your test user removals.
* **Inactive Users Page:** View `LAB_TEST_USER_2` and `LAB_TEST_USER_3`, and test interactive governance actions (**Disable**, **Revoke Roles**, **Archive & Remove**).
* **Agents Page:** Inspect the operational status of the 5 autonomous governance agents.

**Checkpoint:** All 8 dashboard pages render live data from `GOVERNANCE.GOVERNANCE`.

## Scale and Customize

Adapt the governance framework to match your organization's compliance policies and operational schedules.

### Exercise 6.1: Change Task Schedule

To modify a Snowflake Task schedule, you must first suspend the task, apply the new CRON expression, and resume it. For example, to run every Tuesday at 2:00 PM UTC:

```sql
ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO SUSPEND;

ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO 
SET SCHEDULE = 'USING CRON 0 14 * * 2 UTC';

ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO RESUME;
```

### Exercise 6.2: Customize Inactivity Threshold

Update the task definition to enforce a stricter 60-day inactivity policy instead of 90 days by modifying the `WHERE` filter:

```sql
-- Update inside INACTIVE_USER_CLEANUP_TASK_AUTO
WHERE DAYS_INACTIVE >= 60
  AND "STATUS" IN ('active', 'flagged')
```

### Exercise 6.3: Enable Email Notifications

Configure alert notifications by updating [`deployment_config.json`](https://github.com/wondisha/snowflake-ai-governance/blob/main/deployment_config.json) in your repository:

```json
{
  "email_alerts": true,
  "notification_email": "your_email@company.com"
}
```

**Checkpoint:** Your task schedule, inactivity threshold, and alert settings reflect your target production configuration.

## Monitoring and Troubleshooting

Use the following operational queries and troubleshooting tips to maintain your governance system in production.

### Operational Monitoring Queries

Run these queries in Snowsight to monitor overall system health, task execution history, and agent activity:

```sql
-- Overall system health summary
SELECT 
  (SELECT COUNT(*) FROM USER_ACTIVITY_LOG) AS total_users,
  (SELECT COUNT(*) FROM USER_ACTIVITY_LOG WHERE DAYS_INACTIVE >= 90) AS inactive_90plus,
  (SELECT COUNT(*) FROM ARCHIVED_USERS) AS removed_users,
  (SELECT COUNT(*) FROM AUDIT_LOGS) AS total_events;

-- Task execution history
SELECT NAME, COMPLETED_TIME, RETURN_VALUE, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE NAME = 'INACTIVE_USER_CLEANUP_TASK_AUTO'
ORDER BY COMPLETED_TIME DESC
LIMIT 10;

-- Audit event breakdown
SELECT 
  EVENT_TYPE, 
  COUNT(*) AS event_count,
  MAX(CREATED_AT) AS last_event
FROM AUDIT_LOGS
GROUP BY EVENT_TYPE
ORDER BY last_event DESC;
```

### Common Troubleshooting Issues

* **Error: `Invalid identifier 'USR'` inside stored procedures**
  * **Cause:** Omitting the `:` prefix when referencing Snowflake Scripting input parameters or local variables inside SQL statements.
  * **Fix:** Always prefix parameter names with a colon (e.g., `WHERE USER_NAME = :USR;`).
* **Error: Syntax error referencing `STATUS` or `STATE`**
  * **Cause:** `STATUS` and `STATE` are reserved keywords in Snowflake SQL.
  * **Fix:** Enclose reserved identifiers in double quotes (e.g., `SET "STATUS" = 'removed';`).
* **Issue: Scheduled task is not executing**
  * **Cause:** Newly created or altered tasks default to the `SUSPENDED` state.
  * **Fix:** Run `ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO RESUME;` and verify via `SHOW TASKS`.

## Conclusion And Resources

Congratulations! You have built and validated an autonomous governance system in Snowflake capable of tracking user activity, enforcing inactivity policies on a schedule, maintaining immutable audit trails, and surfacing real-time insights in Streamlit.

Explore the full source code—including Slack integrations, daily email reporting, approval workflows, and additional governance agents—in the [Snowflake AI Governance GitHub Repository](https://github.com/wondisha/snowflake-ai-governance).

### What You Learned
* How to structure a Snowflake governance schema for user lifecycle tracking and compliance auditing
* How to write parameterized Snowflake Scripting stored procedures using `:PARAM` bind syntax and `MERGE` statements
* How to automate governance enforcement using CRON-scheduled Snowflake Tasks
* How to build and deploy a multi-page Streamlit in Snowflake monitoring application

### Related Resources
* [Snowflake AI Governance GitHub Repository](https://github.com/wondisha/snowflake-ai-governance)
* [Snowflake Scripting Developer Guide](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/index)
* [Introduction to Snowflake Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)
* [Streamlit in Snowflake Documentation](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
* [Snowflake Information Schema Reference](https://docs.snowflake.com/en/sql-reference/info-schema)

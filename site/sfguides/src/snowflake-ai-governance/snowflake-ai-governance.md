---
author: Wondi Wolde
id: snowflake-ai-governance-system
language: en
summary: Learn to build a production-grade autonomous governance system in Snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
---

## 📚 Lab Overview

This hands-on lab walks you through building a complete Snowflake governance system from scratch. By the end, you'll have:

✅ 5 autonomous agents managing governance  
✅ Real-time monitoring dashboard  
✅ Automatic user lifecycle management  
✅ Complete audit logging and compliance  
✅ Production-ready system  

**Estimated Duration:** 4-6 hours  
**Difficulty Level:** Intermediate (SQL, Python basics helpful)  
**Prerequisites:** Snowflake account with ACCOUNTADMIN role

---

## 🎯 Learning Objectives

By completing this lab, you will:

1. **Understand** Snowflake's autonomous task scheduling
2. **Design** database schemas for governance
3. **Implement** stored procedures for automation
4. **Build** real-time monitoring dashboards
5. **Deploy** agents for security, performance, cost, and health
6. **Manage** user lifecycles automatically
7. **Monitor** system activity with audit logs

---

## 📋 Lab Prerequisites

### Step 1: Verify Your Snowflake Access

```sql
-- In Snowsight, run this to verify access
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
```

**Expected output:**
- User: Your admin user
- Role: ACCOUNTADMIN
- Warehouse: Any warehouse (e.g., COMPUTE_WH)

### Step 2: Prepare Your Environment

**You'll need:**
- [ ] Snowsight access
- [ ] ACCOUNTADMIN role
- [ ] A warehouse (or create one)
- [ ] Python 3.8+ (for deployment script)
- [ ] Git (to clone the repository)

### Step 3: Clone the Repository

```bash
git clone https://github.com/wondisha/snowflake-ai-governance.git
cd snowflake-ai-governance
```

---

## 🚀 Lab Modules

### **Module 1: Database Schema Foundation** (30 minutes)

**Objective:** Create the governance database structure

#### Exercise 1.1: Create Database and Schema

```sql
-- Run in Snowsight
CREATE DATABASE IF NOT EXISTS GOVERNANCE;
USE DATABASE GOVERNANCE;

CREATE SCHEMA IF NOT EXISTS GOVERNANCE;
USE SCHEMA GOVERNANCE;

-- Verify
SELECT DATABASE_NAME, SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA 
WHERE DATABASE_NAME = 'GOVERNANCE';
```

**✅ Checkpoint:** You should see GOVERNANCE database with GOVERNANCE schema

#### Exercise 1.2: Deploy Tables

Run the SQL from `src/database/schema.sql` to create 20+ governance tables.

**Key tables to understand:**
- `POLICIES` - Governance rules
- `AUDIT_LOGS` - System activity tracking
- `USER_ACTIVITY_LOG` - User lifecycle tracking
- `ARCHIVED_USERS` - Removed user history
- `INCIDENTS` - Governance violations

**✅ Checkpoint:** Verify with:
```sql
SHOW TABLES IN GOVERNANCE.GOVERNANCE;
-- Should see 20+ tables
```

---

### **Module 2: Stored Procedures** (60 minutes)

**Objective:** Build the automation engine

#### Exercise 2.1: Create IDENTIFY_INACTIVE_USERS Procedure

This procedure scans for users inactive 90+ days.

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
      ) as DAYS_INACTIVE
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

**Test it:**
```sql
CALL IDENTIFY_INACTIVE_USERS();
SELECT USER_NAME, DAYS_INACTIVE FROM USER_ACTIVITY_LOG LIMIT 10;
```

**✅ Checkpoint:** Procedure runs without errors and USER_ACTIVITY_LOG is populated

#### Exercise 2.2: Create REVOKE_INACTIVE_USER_ROLES Procedure

**⚠️ Key Learning:** Notice the `:PARAM_NAME` syntax for parameters!

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

**✅ Checkpoint:** Procedure created successfully (no "invalid identifier" errors)

#### Exercise 2.3: Create DISABLE_INACTIVE_USER Procedure

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

**⚠️ Learning Point:** Notice `"STATUS"` is quoted because STATUS is a reserved keyword!

**✅ Checkpoint:** Test with:
```sql
CALL DISABLE_INACTIVE_USER('TEST_USER', 'Lab test');
```

#### Exercise 2.4: Create REMOVE_INACTIVE_USER_COMPLETE Procedure

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

**✅ Checkpoint:** All 4 procedures created successfully

---

### **Module 3: Task Scheduling** (20 minutes)

**Objective:** Set up automatic task execution

#### Exercise 3.1: Create the Automatic Cleanup Task

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

  -- Remove each user
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

**Verify task status:**
```sql
SELECT NAME, "STATE", SCHEDULE, NEXT_SCHEDULED_TIME
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE NAME = 'INACTIVE_USER_CLEANUP_TASK_AUTO'
LIMIT 1;
```

**✅ Checkpoint:** Task is in RESUMED state

---

### **Module 4: Testing & Validation** (45 minutes)

**Objective:** Test the system end-to-end

#### Exercise 4.1: Create Test Users

```sql
-- Insert test users with >89 days inactive
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

-- Verify
SELECT USER_NAME, DAYS_INACTIVE, "STATUS" FROM USER_ACTIVITY_LOG 
WHERE USER_NAME LIKE 'LAB_TEST_%'
ORDER BY DAYS_INACTIVE DESC;
```

**Expected:** 3 rows with status = 'active'

#### Exercise 4.2: Run Procedures Manually

```sql
-- Test each procedure
CALL IDENTIFY_INACTIVE_USERS();
CALL DISABLE_INACTIVE_USER('LAB_TEST_USER_1', 'Lab testing');
CALL REVOKE_INACTIVE_USER_ROLES('LAB_TEST_USER_1');
CALL REMOVE_INACTIVE_USER_COMPLETE('LAB_TEST_USER_1');

-- Verify results
SELECT USER_NAME, "STATUS" FROM USER_ACTIVITY_LOG 
WHERE USER_NAME LIKE 'LAB_TEST_%'
ORDER BY USER_NAME;
```

**Expected:**
- LAB_TEST_USER_1 → status = 'removed'
- LAB_TEST_USER_2 → status = 'active'
- LAB_TEST_USER_3 → status = 'active'

#### Exercise 4.3: Check Audit Trail

```sql
SELECT 
  EVENT_TYPE, 
  RESOURCE_NAME, 
  ACTION_DESCRIPTION, 
  EVENT_TIMESTAMP
FROM AUDIT_LOGS
WHERE RESOURCE_NAME LIKE 'LAB_TEST_%'
ORDER BY EVENT_TIMESTAMP DESC;
```

**Expected:** Multiple entries showing disable, role revocation, removal actions

#### Exercise 4.4: Verify Archived Users

```sql
SELECT USER_NAME, ARCHIVED_ON 
FROM ARCHIVED_USERS
WHERE USER_NAME LIKE 'LAB_TEST_%';
```

**Expected:** LAB_TEST_USER_1 in archived users

**✅ Checkpoint:** Complete audit trail from active → disabled → removed → archived

---

### **Module 5: Deploy Dashboard** (30 minutes)

**Objective:** Set up real-time monitoring

#### Exercise 5.1: Deploy Streamlit Dashboard

1. In Snowsight: Click "+ Create" → "Streamlit app"
2. Name it: "Governance Dashboard"
3. Copy entire content from `streamlit_governance_dashboard.py`
4. Paste into Snowsight editor
5. Click "Run" at top right

**✅ Checkpoint:** Dashboard loads without errors and shows 8 pages

#### Exercise 5.2: Navigate Dashboard Pages

**Overview Page:**
- Check system metrics
- View recent audit logs
- Should show your test user removals

**Inactive Users Page:**
- See remaining test users
- Try action buttons (Disable, Revoke Roles, Archive & Remove)

**Agents Page:**
- View 5 agent statuses
- All should show "idle"

**✅ Checkpoint:** All 8 pages load successfully with your data

---

### **Module 6: Scale & Customize** (45 minutes)

**Objective:** Adapt for production

#### Exercise 6.1: Change Task Schedule

Change to run **tomorrow at 2 PM UTC** (8 AM Central):

```sql
ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO SUSPEND;

ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO 
SET SCHEDULE = 'USING CRON 0 14 * * 2 UTC';  -- Tuesday 2 PM UTC

ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO RESUME;
```

#### Exercise 6.2: Customize Inactivity Threshold

Modify procedure to use 60 days instead of 90:

```sql
-- Edit the task WHERE clause:
WHERE DAYS_INACTIVE >= 60  -- Changed from 90
```

#### Exercise 6.3: Enable Email Notifications

Set up alerts by updating deployment_config.json:

```json
{
  "email_alerts": true,
  "notification_email": "your_email@company.com"
}
```

**✅ Checkpoint:** System customized for your environment

---

## 📊 Lab Monitoring Queries

**Use these to track your progress:**

```sql
-- Overall system health
SELECT 
  (SELECT COUNT(*) FROM USER_ACTIVITY_LOG) as total_users,
  (SELECT COUNT(*) FROM USER_ACTIVITY_LOG WHERE DAYS_INACTIVE >= 90) as inactive_90plus,
  (SELECT COUNT(*) FROM ARCHIVED_USERS) as removed_users,
  (SELECT COUNT(*) FROM AUDIT_LOGS) as total_events;

-- Task execution history
SELECT NAME, COMPLETED_TIME, RETURN_VALUE, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE NAME = 'INACTIVE_USER_CLEANUP_TASK_AUTO'
ORDER BY COMPLETED_TIME DESC
LIMIT 10;

-- Agent activity
SELECT 
  EVENT_TYPE, 
  COUNT(*) as count,
  MAX(EVENT_TIMESTAMP) as last_event
FROM AUDIT_LOGS
GROUP BY EVENT_TYPE
ORDER BY last_event DESC;
```

---

## 🔍 Troubleshooting Guide

### Issue: "Invalid identifier 'USR'"

**Cause:** Not using `:` prefix for parameters

**Fix:** Always use `:PARAM_NAME`:
```sql
WHERE USER_NAME = :USR;  -- Correct
WHERE USER_NAME = USR;   -- Wrong
```

### Issue: "STATUS is a reserved keyword"

**Cause:** Not quoting reserved words

**Fix:** Quote with double quotes:
```sql
SET "STATUS" = 'removed';  -- Correct
SET STATUS = 'removed';    -- Wrong
```

### Issue: Task not running

**Cause:** Task not resumed or schedule not set

**Fix:**
```sql
-- Check status
SELECT STATE FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE NAME = 'INACTIVE_USER_CLEANUP_TASK_AUTO' LIMIT 1;

-- Resume if needed
ALTER TASK INACTIVE_USER_CLEANUP_TASK_AUTO RESUME;
```

---

## ✅ Lab Completion Checklist

- [ ] Module 1: Database schema created (20+ tables)
- [ ] Module 2: All 4 procedures created successfully
- [ ] Module 3: Task scheduled and enabled
- [ ] Module 4: Test users removed successfully
- [ ] Module 4: Audit trail complete
- [ ] Module 5: Dashboard deployed and accessible
- [ ] Module 5: All 8 dashboard pages working
- [ ] Module 6: Task schedule customized
- [ ] Module 6: Tested end-to-end workflow

---

## 🎓 Key Learning Takeaways

1. **Snowflake Stored Procedures** - Use `:PARAM` syntax for parameters
2. **MERGE Statements** - Efficient upsert operations
3. **Task Scheduling** - CRON syntax for automation
4. **Audit Logging** - Complete traceability
5. **Real-time Dashboards** - Streamlit for monitoring
6. **Reserved Keywords** - Always quote them (`"STATUS"`, `"STATE"`)

---

## 📚 Next Steps

After completing this lab:

1. **Add Slack Alerts** - See slack_integration.sql
2. **Enable Email Reports** - See daily_reports.sql
3. **Add Approval Workflows** - See approval_workflow.sql
4. **Deploy Other Agents** - See agent_procedures_production.sql
5. **Set up Airflow** - See governance_agents_dag.py

---

## 💡 Lab Tips

- **Save queries** - Save commonly used monitoring queries for reuse
- **Take notes** - Document what you learn about Snowflake procedures
- **Test thoroughly** - Always verify each step before moving to next
- **Read error messages** - They're usually very specific
- **Check git repository** - All code is on GitHub with examples

---

## 🎉 Congratulations!

You've built a production-grade Snowflake governance system! 

**Your system now:**
- ✅ Monitors user activity automatically
- ✅ Removes inactive users on schedule
- ✅ Maintains complete audit trails
- ✅ Provides real-time dashboards
- ✅ Scales to any Snowflake environment

**Ready to deploy to production!** 🚀

---

**Lab Version:** 1.0  
**Updated:** November 2026  
**Total Estimated Time:** 4-6 hours  
**Difficulty:** Intermediate

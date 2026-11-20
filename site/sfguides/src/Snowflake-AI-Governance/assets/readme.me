# ❄️ Snowflake AI Governance System

**Complete autonomous governance, security, performance, and health management for Snowflake**

---

## 🎯 Overview

An **enterprise-grade autonomous governance system** for Snowflake that automatically:

✅ Monitors & Optimizes - Real-time performance, cost, and health tracking  
✅ Enforces Security - Access control, PII detection, spillage prevention  
✅ Manages Resources - Auto-scale warehouses, suspend idle, abort runaway queries  
✅ Prevents Breaches - Data spillage detection, user access monitoring  
✅ Cleans Up Users - Auto-remove inactive users (90+ days)  
✅ Alerts & Reports - Slack alerts, daily email reports, approval workflows  

**Zero manual intervention required!** 🤖

---

## 📊 Features

### 5 Autonomous Agents

- **Security Agent** - Access control & compliance
- **Performance Agent** - Query & warehouse optimization
- **Cost Agent** - Spending optimization
- **Health Agent** - System monitoring
- **Spillage Agent** - Data protection & PII detection

### 8-Page Real-Time Dashboard

- Overview - System metrics & audit logs
- Security - PII detection, security events
- Performance - Query analysis, warehouse metrics
- Cost - Credit tracking, cost per warehouse
- Health - Warehouse health status
- Incidents - Active incidents & remediation
- Agents - Agent status & performance
- Inactive Users - User lifecycle management (NEW!)

### Integrations

- Slack alerts for critical incidents
- Daily email governance reports
- Risk-based approval workflows with SLA
- Multi-environment configs (Dev/Staging/Prod)
- Airflow DAG orchestration
- dbt Cloud integration

### User Lifecycle Management

- Auto-detection of 90+ day inactive users
- Flexible removal: Approval-based OR Automatic
- Auto-remediation: Revoke roles, disable, archive
- Complete audit trail

---

## 🧪 Learn with Hands-On Lab (NEW!)

**Want to learn how to build this system?** 📚

Start with our **Hands-On Lab Guide**: `HANDS_ON_LAB.md`
- 6 comprehensive modules (4-6 hours)
- Step-by-step exercises with checkpoints
- Copy-paste ready SQL code
- Troubleshooting guide included
- Perfect for learning Snowflake automation

**[Start the Lab →](HANDS_ON_LAB.md)**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Prerequisites

- Snowflake account (Pro/Business Critical)
- Python 3.8+
- Git (optional)
- Snowsight access

### Step 2: Clone

```bash
git clone https://github.com/wondisha/snowflake-ai-governance.git
cd snowflake-ai-governance
```

### Step 3: Configure

Edit deployment_config.json:

```json
{
  "account_id": "YOUR_ACCOUNT_ID",
  "user": "YOUR_ADMIN_USER",
  "password": "YOUR_PASSWORD",
  "warehouse": "COMPUTE_WH",
  "database": "GOVERNANCE",
  "schema": "PUBLIC",
  "role": "ACCOUNTADMIN"
}
```

### Step 4: Deploy

```bash
python deploy.py deployment_config.json
```

### Step 5: Verify

```bash
python validate_deployment.py
```

### Step 6: Launch Dashboard

In Snowsight: Create App → Streamlit → Upload streamlit_governance_dashboard.py

---

## 📋 Full Deployment Steps

### 1. Pre-Deployment Check

```bash
python verify_setup.py
```

### 2. Deploy Database

```bash
python deploy.py deployment_config.json
```

### 3. Create User Activity Tables

Run in Snowsight:

```sql
USE DATABASE GOVERNANCE;
USE SCHEMA GOVERNANCE;

CREATE TABLE IF NOT EXISTS USER_ACTIVITY_LOG (
    ACTIVITY_ID STRING PRIMARY KEY,
    USER_NAME STRING NOT NULL,
    USER_EMAIL STRING,
    LAST_LOGIN TIMESTAMP,
    DAYS_INACTIVE INT,
    STATUS STRING DEFAULT 'active',
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS ARCHIVED_USERS (
    ARCHIVE_ID STRING PRIMARY KEY,
    USER_NAME STRING NOT NULL,
    USER_EMAIL STRING,
    ARCHIVED_ON TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### 4. Deploy Agent Procedures

```sql
-- Production (with auto-remediation)
@file = 'agent_procedures_production.sql'
```

### 5. Setup User Removal

**Option A: Approval-Based (Safer)**
```sql
@file = 'inactive_user_removal.sql'
```

**Option B: Automatic (Faster)**
```sql
@file = 'inactive_user_removal_automatic.sql'
```

### 6. Create RBAC Roles

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE GOVERNANCE;

CREATE ROLE IF NOT EXISTS governance_admin;
CREATE ROLE IF NOT EXISTS governance_agent;
CREATE ROLE IF NOT EXISTS governance_viewer;

GRANT USAGE ON DATABASE GOVERNANCE TO ROLE governance_admin;
GRANT USAGE ON SCHEMA GOVERNANCE TO ROLE governance_admin;
GRANT ALL ON ALL TABLES IN SCHEMA GOVERNANCE TO ROLE governance_admin;

GRANT ROLE governance_admin TO USER "your_email@company.com";
```

### 7. Schedule Agents

```sql
USE DATABASE GOVERNANCE;
USE SCHEMA GOVERNANCE;

-- Performance Agent (every 2 hours)
CREATE TASK performance_agent_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 */2 * * * UTC'
AS CALL GOVERNANCE.GOVERNANCE.PERFORMANCE_AGENT();

-- Cost Agent (daily 6 AM)
CREATE TASK cost_agent_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 6 * * * UTC'
AS CALL GOVERNANCE.GOVERNANCE.COST_AGENT();

-- Security Agent (every 4 hours)
CREATE TASK security_agent_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 */4 * * * UTC'
AS CALL GOVERNANCE.GOVERNANCE.SECURITY_AGENT();

-- Health Agent (every hour)
CREATE TASK health_agent_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 * * * * UTC'
AS CALL GOVERNANCE.GOVERNANCE.HEALTH_AGENT();

-- Spillage Agent (every 4 hours)
CREATE TASK spillage_agent_task
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 */4 * * * UTC'
AS CALL GOVERNANCE.GOVERNANCE.SPILLAGE_AGENT();

-- Enable all tasks
ALTER TASK performance_agent_task RESUME;
ALTER TASK cost_agent_task RESUME;
ALTER TASK security_agent_task RESUME;
ALTER TASK health_agent_task RESUME;
ALTER TASK spillage_agent_task RESUME;
```

### 8. Optional: Setup Integrations

**Slack Alerts:**
```sql
@file = 'slack_integration.sql'
```

**Email Reports:**
```sql
@file = 'daily_reports.sql'
```

**Approval Workflows:**
```sql
@file = 'approval_workflow.sql'
```

### 9. Deploy Dashboard

1. In Snowsight: Click "+ Create" → "Streamlit app"
2. Paste content from streamlit_governance_dashboard.py
3. Save
4. Navigate to "Inactive Users" tab

### 10. Load Sample Data (Optional)

```bash
python populate_sample_data.py
```

---

## 📊 Dashboard Pages

**Overview** - System metrics & audit logs  
**Security** - PII detection, security events  
**Performance** - Query analysis, warehouse metrics  
**Cost** - Credit tracking, cost per warehouse  
**Health** - Warehouse health status  
**Incidents** - Active incidents & remediation  
**Agents** - Agent status & performance  
**Inactive Users** - User management with action buttons:
  - Disable User
  - Revoke Roles
  - Archive & Remove

---

## 🔐 User Lifecycle Management

### Automatic Detection (Weekly Monday Midnight)

Scans for users inactive 90+ days and removes them

### Approval-Based Removal

```sql
@file = 'inactive_user_removal.sql'
```

Process: Flag → Approval Request → Admin Review → Auto-Remove

### Automatic Removal (No Approval)

```sql
@file = 'inactive_user_removal_automatic.sql'
```

Each Monday: Scan → Revoke Roles → Disable → Archive → Log

---

## 🔗 Integration & Setup Guides

- **Airflow:** See AIRFLOW_INTEGRATION_GUIDE.md
- **dbt Cloud:** See DBT_CLOUD_INTEGRATION_GUIDE.md
- **Inactive User Management:** See INACTIVE_USER_MANAGEMENT_SETUP.md (Complete setup guide with procedures)
- **Slack:** Update webhook URL in slack_integration.sql
- **Email:** Configure service in daily_reports.sql

---

## 📈 Monitoring

### Check Agent Status

```sql
SELECT * FROM GOVERNANCE.GOVERNANCE.AGENT_STATE
ORDER BY LAST_SUCCESSFUL_EXECUTION DESC;
```

### View Audit Logs

```sql
SELECT * FROM GOVERNANCE.GOVERNANCE.AUDIT_LOGS
ORDER BY EVENT_TIMESTAMP DESC LIMIT 50;
```

### Monitor Tasks

```sql
SELECT NAME, STATE, NEXT_SCHEDULED_TIME
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE SCHEMA_NAME = 'GOVERNANCE'
ORDER BY QUERY_START_TIME DESC;
```

---

## 📁 File Structure

```
deploy.py                           # Main deployment
validate_deployment.py              # Validation
verify_setup.py                     # Pre-checks
populate_sample_data.py             # Sample data
streamlit_governance_dashboard.py   # Dashboard
governance_agents_dag.py            # Airflow DAG
src/database/schema.sql             # Schema
agent_procedures.sql                # Mock agents
agent_procedures_production.sql     # Prod agents
inactive_user_removal.sql           # Approval-based
inactive_user_removal_automatic.sql # Automatic
create_inactive_users_tables.sql    # User tables
slack_integration.sql               # Slack
approval_workflow.sql               # Approvals
daily_reports.sql                   # Reports
environment_deployment.sql          # Multi-env
IMPLEMENTATION_GUIDE.md
AIRFLOW_INTEGRATION_GUIDE.md
DBT_CLOUD_INTEGRATION_GUIDE.md
README.md
```

---

## ✅ What You Get

✅ 5 Autonomous Agents  
✅ 8-Page Real-Time Dashboard  
✅ Slack Alerts  
✅ Daily Email Reports  
✅ Approval Workflows  
✅ Automatic User Removal  
✅ Complete RBAC  
✅ Multi-Environment Support  
✅ Full Audit Logging  
✅ Production-Ready  

---

## 🚀 Deployment Timeline

| Stage | Time | What Happens |
|-------|------|--------------|
| Verify Setup | 1 min | Check dependencies |
| Deploy DB | 2 min | Create schema, tables, views |
| Deploy Agents | 1 min | Create procedures |
| Setup RBAC | 1 min | Create roles & permissions |
| Schedule Tasks | 1 min | Create Snowflake tasks |
| Deploy Dashboard | 2 min | Upload Streamlit app |
| **Total** | **~8 min** | **Complete System Live** |

---

## 📞 Support

- Documentation: See IMPLEMENTATION_GUIDE.md
- Issues: GitHub Issues
- Questions: Check troubleshooting section

---

## 🎯 Ready to Deploy?

```bash
# 1. Clone
git clone https://github.com/wondisha/snowflake-ai-governance.git

# 2. Configure
# Edit deployment_config.json

# 3. Deploy
python deploy.py deployment_config.json

# 4. Done! 🎉
```

**Your autonomous governance system is now LIVE!** 🚀

---

Made with ❤️ for Snowflake

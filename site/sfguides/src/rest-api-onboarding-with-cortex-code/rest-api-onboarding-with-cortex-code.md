author: Priya Joseph
id: rest-api-onboarding-with-cortex-code
language: en
summary: Build a complete REST API onboarding system with admin and user portals using Snowflake Cortex REST API and Programmatic Access Tokens (PATs)
categories: snowflake-site:taxonomy/solution-center/partners/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# REST API Onboarding with Cortex Code
<!-- ------------------------ -->
## Overview

This guide walks you through building a complete REST API onboarding system for Snowflake Cortex. You'll create two applications:

- **AdminApp (Server-side)**: An administrative dashboard for managing user onboarding, tracking progress, and provisioning Programmatic Access Tokens (PATs)
- **UserApp (Client-side)**: A self-service portal where users complete onboarding steps and configure their Cortex Code environment

The system leverages Snowflake's REST API (`/api/v2/cortex/inference:complete`) for AI-powered features and PAT-based authentication for secure, scriptable access.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Snowflake Account                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Cortex REST    │  │  PAT Lifecycle  │  │  User/Role      │ │
│  │  API Endpoint   │  │  Management     │  │  Management     │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼────────────────────┼────────────────────┼──────────┘
            │                    │                    │
     ┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
     │  AdminApp   │      │   UserApp   │      │  Flask API  │
     │  (Port 8521)│      │ (Port 8522) │      │ (Port 8525) │
     │  Streamlit  │      │  Streamlit  │      │  REST API   │
     └─────────────┘      └─────────────┘      └─────────────┘
```

### Prerequisites
- Snowflake account with ACCOUNTADMIN or SECURITYADMIN role
- Python 3.9+ installed
- Basic familiarity with Streamlit and Flask
- Understanding of REST APIs and authentication

### What You'll Learn
- How to use Snowflake's Cortex REST API for AI inference
- PAT (Programmatic Access Token) lifecycle management
- Building admin dashboards with Streamlit
- Creating self-service onboarding portals
- Implementing bulk user provisioning via CSV

### What You'll Need
- A [Snowflake Account](https://signup.snowflake.com/)
- [Python 3.9+](https://www.python.org/downloads/)
- [Streamlit](https://streamlit.io/) (`pip install streamlit`)
- [Flask](https://flask.palletsprojects.com/) (`pip install flask`)

### What You'll Build
- AdminApp: Server-side dashboard for managing onboarding
- UserApp: Client-side portal for user self-service
- REST API endpoints for programmatic access
- Bulk user import system with CSV support

<!-- ------------------------ -->
## Environment Setup

### Step 1: Install Dependencies

Create a virtual environment and install the required packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install streamlit flask requests pandas snowflake-connector-python
```

### Step 2: Configure Snowflake Connection

Create or update your Snowflake configuration file at `~/.snowflake/config.toml`:

```toml
[connections.myaccount]
account = "YOUR_ACCOUNT_ID"
user = "YOUR_USERNAME"
password = "YOUR_PAT_TOKEN"  # Use PAT for programmatic access
warehouse = "COMPUTE_WH"
database = "YOUR_DATABASE"
schema = "PUBLIC"
```

### Step 3: Verify Cortex REST API Access

Test your connection to the Cortex REST API:

```python
import requests

account_url = "https://YOUR_ACCOUNT_ID.snowflakecomputing.com"
pat_token = "YOUR_PAT_TOKEN"

response = requests.post(
    f"{account_url}/api/v2/cortex/inference:complete",
    headers={
        "Authorization": f"Bearer {pat_token}",
        "Content-Type": "application/json"
    },
    json={
        "model": "claude-sonnet-4-5",
        "messages": [{"role": "user", "content": "Hello!"}],
        "max_tokens": 100
    }
)

print(response.json())
```

<!-- ------------------------ -->
## AdminApp - Server-Side Dashboard

The AdminApp provides administrators with tools to manage user onboarding, track progress, and provision PATs.

### Core Features

1. **User Management**: View, add, and manage onboarding users
2. **Progress Tracking**: Monitor onboarding step completion
3. **PAT Provisioning**: Generate and rotate Programmatic Access Tokens
4. **Bulk Import**: Import users from CSV files
5. **Activity Logging**: Track all admin and user actions

### Snowflake Schema Setup

All onboarding state is stored in Snowflake tables, accessed via REST API. Create the schema:

```sql
-- Create database and schema for onboarding state
CREATE DATABASE IF NOT EXISTS ONBOARDING_DB;
CREATE SCHEMA IF NOT EXISTS ONBOARDING_DB.STATE;

USE SCHEMA ONBOARDING_DB.STATE;

-- Users table
CREATE TABLE IF NOT EXISTS USERS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    EMAIL VARCHAR(255) UNIQUE NOT NULL,
    NAME VARCHAR(255) NOT NULL,
    ROLE VARCHAR(50) DEFAULT 'user',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    SNOWFLAKE_USERNAME VARCHAR(255),
    TAGS VARCHAR(1000)
);

-- Onboarding progress table
CREATE TABLE IF NOT EXISTS ONBOARDING_PROGRESS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    USER_ID NUMBER NOT NULL REFERENCES USERS(ID),
    STEP_NAME VARCHAR(100) NOT NULL,
    COMPLETED BOOLEAN DEFAULT FALSE,
    COMPLETED_AT TIMESTAMP_NTZ,
    DETAILS VARCHAR(2000),
    UNIQUE(USER_ID, STEP_NAME)
);

-- Activity log table
CREATE TABLE IF NOT EXISTS ACTIVITY_LOG (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    USER_ID NUMBER,
    ACTION VARCHAR(100) NOT NULL,
    DETAILS VARCHAR(2000),
    TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

### Snowflake REST API Client

Use the Snowflake REST API (`/api/v2/statements`) to execute SQL:

```python
import os
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class SnowflakeConfig:
    """Snowflake connection configuration."""
    account_locator: str
    region: str
    admin_user: str
    admin_password: Optional[str] = None
    warehouse: str = "COMPUTE_WH"
    database: str = "ONBOARDING_DB"
    schema: str = "STATE"
    
    @property
    def base_url(self) -> str:
        return f"https://{self.account_locator}.{self.region}.snowflakecomputing.com"
    
    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api/v2"


class SnowflakeClient:
    """Client for Snowflake REST API operations."""
    
    def __init__(self, config: SnowflakeConfig):
        self.config = config
        self.session = requests.Session()
        self._token: Optional[str] = None
    
    def authenticate(self) -> bool:
        """Authenticate and get session token."""
        auth_url = f"{self.config.base_url}/session/v1/login-request"
        payload = {
            "data": {
                "ACCOUNT_NAME": self.config.account_locator,
                "LOGIN_NAME": self.config.admin_user,
                "PASSWORD": self.config.admin_password,
            }
        }
        
        response = self.session.post(auth_url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self._token = data.get("data", {}).get("token")
            return True
        return False
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL via REST API."""
        url = f"{self.config.api_url}/statements"
        payload = {
            "statement": sql,
            "timeout": 60,
            "warehouse": self.config.warehouse,
            "database": self.config.database,
            "schema": self.config.schema,
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}"
        }
        
        response = self.session.post(url, json=payload, headers=headers)
        return {
            "success": response.status_code in [200, 202],
            "status_code": response.status_code,
            "data": response.json() if response.text else None
        }
    
    def query(self, sql: str) -> List[Dict]:
        """Execute query and return rows as dicts."""
        result = self.execute_sql(sql)
        if not result.get("success"):
            return []
        
        data = result.get("data", {})
        rows = data.get("data", [])
        columns = [col.get("name") for col in data.get("resultSetMetaData", {}).get("rowType", [])]
        
        return [dict(zip(columns, row)) for row in rows]
```

### Onboarding Steps

Define the required onboarding steps:

```python
ONBOARDING_STEPS = [
    {
        "name": "account_setup",
        "title": "Account Setup",
        "description": "Snowflake account access verified"
    },
    {
        "name": "pat_created",
        "title": "PAT Created",
        "description": "Programmatic Access Token generated"
    },
    {
        "name": "network_policy",
        "title": "Network Policy",
        "description": "Network policy configured for IP allowlist"
    },
    {
        "name": "cortex_access",
        "title": "Cortex Access",
        "description": "Cortex REST API access verified"
    },
    {
        "name": "first_inference",
        "title": "First Inference",
        "description": "Successfully completed first AI inference"
    }
]
```

### AdminApp Main Code

```python
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Initialize Snowflake client
config = SnowflakeConfig(
    account_locator=os.getenv("SNOWFLAKE_ACCOUNT_LOCATOR"),
    region=os.getenv("SNOWFLAKE_REGION", "us-west-2"),
    admin_user=os.getenv("SNOWFLAKE_ADMIN_USER"),
    admin_password=os.getenv("SNOWFLAKE_ADMIN_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
)

@st.cache_resource
def get_sf_client():
    client = SnowflakeClient(config)
    client.authenticate()
    return client

sf = get_sf_client()

# Page config
st.set_page_config(
    page_title="Cortex Code Onboarding Admin",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Cortex Code Onboarding Admin")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "User Management", "Bulk Import", "Activity Log"]
)

if page == "Dashboard":
    st.header("Onboarding Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        result = sf.query("SELECT COUNT(*) as CNT FROM USERS")
        st.metric("Total Users", result[0]['CNT'] if result else 0)
    
    with col2:
        # Users with all steps complete
        result = sf.query("""
            SELECT COUNT(DISTINCT u.ID) as CNT 
            FROM USERS u
            WHERE (SELECT COUNT(*) FROM ONBOARDING_PROGRESS op 
                   WHERE op.USER_ID = u.ID AND op.COMPLETED = TRUE) = 5
        """)
        st.metric("Fully Onboarded", result[0]['CNT'] if result else 0)
    
    with col3:
        result = sf.query("""
            SELECT COUNT(DISTINCT USER_ID) as CNT 
            FROM ONBOARDING_PROGRESS 
            WHERE COMPLETED = TRUE
        """)
        st.metric("In Progress", result[0]['CNT'] if result else 0)
    
    with col4:
        result = sf.query("""
            SELECT COUNT(*) as CNT FROM ACTIVITY_LOG 
            WHERE TIMESTAMP > DATEADD(hour, -24, CURRENT_TIMESTAMP())
        """)
        st.metric("24h Activity", result[0]['CNT'] if result else 0)
    
    # Progress chart
    st.subheader("Step Completion Rates")
    step_stats = sf.query("""
        SELECT STEP_NAME, 
               COUNT(*) as TOTAL,
               SUM(CASE WHEN COMPLETED THEN 1 ELSE 0 END) as COMPLETED_COUNT
        FROM ONBOARDING_PROGRESS
        GROUP BY STEP_NAME
    """)
    if step_stats:
        df = pd.DataFrame(step_stats)
        df['COMPLETION_RATE'] = df['COMPLETED_COUNT'] / df['TOTAL'] * 100
        st.bar_chart(df.set_index('STEP_NAME')['COMPLETION_RATE'])

elif page == "User Management":
    st.header("User Management")
    
    # Add new user form
    with st.expander("Add New User"):
        with st.form("add_user"):
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email")
                name = st.text_input("Full Name")
            with col2:
                role = st.selectbox("Role", ["user", "admin", "developer"])
                tags = st.text_input("Tags (comma-separated)")
            
            if st.form_submit_button("Add User"):
                # Insert user via Snowflake REST API
                sf.execute_sql(f"""
                    INSERT INTO USERS (EMAIL, NAME, ROLE, TAGS) 
                    VALUES ('{email}', '{name}', '{role}', '{tags}')
                """)
                
                # Get the new user ID
                result = sf.query(f"SELECT ID FROM USERS WHERE EMAIL = '{email}'")
                if result:
                    user_id = result[0]['ID']
                    
                    # Initialize onboarding steps
                    for step in ONBOARDING_STEPS:
                        sf.execute_sql(f"""
                            INSERT INTO ONBOARDING_PROGRESS (USER_ID, STEP_NAME) 
                            VALUES ({user_id}, '{step['name']}')
                        """)
                    
                    st.success(f"User {email} added successfully!")

elif page == "Bulk Import":
    st.header("Bulk User Import")
    st.markdown("""
    Upload a CSV file with the following columns:
    - `userfirstname` (required)
    - `userlastname` (required)
    - `useremail` (required)
    - `additionalTags` (optional)
    - `roletype` (optional: user, admin, developer)
    - `associatePrimaryPAT` (optional)
    - `associateSecondaryPAT` (optional)
    """)
    
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
        
        if st.button("Import Users"):
            # Process bulk import
            pass

elif page == "Activity Log":
    st.header("Activity Log")
    
    logs = sf.query("""
        SELECT al.*, u.EMAIL 
        FROM ACTIVITY_LOG al
        LEFT JOIN USERS u ON al.USER_ID = u.ID
        ORDER BY TIMESTAMP DESC
        LIMIT 100
    """)
    
    if logs:
        st.dataframe(pd.DataFrame(logs))
    else:
        st.info("No activity logged yet.")
```

<!-- ------------------------ -->
## UserApp - Client-Side Portal

The UserApp provides users with a self-service portal to complete their onboarding steps.

### Core Features

1. **Progress Tracker**: Visual progress through onboarding steps
2. **PAT Registration**: Register and validate PAT tokens
3. **Connection Testing**: Test Snowflake and Cortex API connectivity
4. **AI Playground**: Interactive area to test Cortex AI models
5. **Documentation**: Embedded guides and help resources

### UserApp Main Code

```python
import streamlit as st
import requests
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Cortex Code Onboarding",
    page_icon="🎯",
    layout="wide"
)

# Session state for user
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
    st.session_state.authenticated = False

def login_page():
    st.title("🎯 Cortex Code Onboarding Portal")
    
    with st.form("login"):
        email = st.text_input("Email Address")
        if st.form_submit_button("Continue"):
            # Verify user exists
            response = requests.get(
                f"http://localhost:8525/api/user/lookup?email={email}"
            )
            if response.status_code == 200:
                st.session_state.user_email = email
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("User not found. Contact your administrator.")

def onboarding_page():
    st.title("🎯 Your Onboarding Journey")
    
    # Fetch user progress
    response = requests.get(
        f"http://localhost:8525/api/user/progress?email={st.session_state.user_email}"
    )
    progress = response.json()
    
    # Progress bar
    completed = sum(1 for step in progress['steps'] if step['completed'])
    total = len(progress['steps'])
    st.progress(completed / total)
    st.caption(f"{completed}/{total} steps completed")
    
    # Step cards
    for i, step in enumerate(progress['steps']):
        with st.expander(
            f"{'✅' if step['completed'] else '⏳'} Step {i+1}: {step['title']}",
            expanded=not step['completed']
        ):
            st.markdown(step['description'])
            
            if step['name'] == 'pat_created' and not step['completed']:
                st.markdown("### Register Your PAT")
                pat = st.text_input("Enter your PAT token", type="password")
                if st.button("Register PAT"):
                    # Send PAT to admin API
                    resp = requests.post(
                        "http://localhost:8525/api/register_pat",
                        json={
                            "email": st.session_state.user_email,
                            "pat_token": pat
                        }
                    )
                    if resp.status_code == 200:
                        st.success("PAT registered successfully!")
                        st.rerun()
            
            elif step['name'] == 'first_inference' and not step['completed']:
                st.markdown("### Test Cortex AI")
                prompt = st.text_area("Enter a test prompt")
                if st.button("Run Inference"):
                    # Call Cortex API
                    st.info("Running inference...")
                    # Add inference code here

# Main app logic
if not st.session_state.authenticated:
    login_page()
else:
    onboarding_page()
```

<!-- ------------------------ -->
## REST API Endpoints

The Flask API serves as the backend for both AdminApp and UserApp, providing programmatic access to onboarding functions.

### API Server Setup

```python
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ============== User Endpoints ==============

@app.route('/api/user/lookup', methods=['GET'])
def user_lookup():
    """Look up a user by email."""
    email = request.args.get('email')
    
    conn = sqlite3.connect('onboarding.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "id": user[0],
            "email": user[1],
            "name": user[2],
            "role": user[3]
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/api/user/progress', methods=['GET'])
def user_progress():
    """Get onboarding progress for a user."""
    email = request.args.get('email')
    
    conn = sqlite3.connect('onboarding.db')
    cursor = conn.cursor()
    
    # Get user
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    # Get progress
    cursor.execute("""
        SELECT step_name, completed, completed_at, details
        FROM onboarding_progress
        WHERE user_id = ?
    """, (user[0],))
    
    steps = []
    for row in cursor.fetchall():
        step_info = next(
            (s for s in ONBOARDING_STEPS if s['name'] == row[0]), 
            {}
        )
        steps.append({
            "name": row[0],
            "title": step_info.get('title', row[0]),
            "description": step_info.get('description', ''),
            "completed": bool(row[1]),
            "completed_at": row[2],
            "details": row[3]
        })
    
    conn.close()
    return jsonify({"steps": steps})

# ============== Admin Endpoints ==============

@app.route('/api/register_pat', methods=['POST'])
def register_pat():
    """Register a PAT for a user."""
    data = request.get_json()
    email = data.get('email')
    pat_token = data.get('pat_token')
    
    # Validate PAT by testing Cortex API
    # Then update onboarding progress
    
    return jsonify({"success": True})

@app.route('/api/service-admin/users', methods=['GET'])
def list_users():
    """List all users with onboarding status."""
    conn = sqlite3.connect('onboarding.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.*, 
               (SELECT COUNT(*) FROM onboarding_progress op 
                WHERE op.user_id = u.id AND op.completed = 1) as completed_steps
        FROM users u
        ORDER BY u.created_at DESC
    """)
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row[0],
            "email": row[1],
            "name": row[2],
            "role": row[3],
            "created_at": row[4],
            "completed_steps": row[6],
            "onboarding_complete": row[6] == 5
        })
    
    conn.close()
    return jsonify({"users": users})

@app.route('/api/service-admin/stats', methods=['GET'])
def admin_stats():
    """Get onboarding statistics."""
    conn = sqlite3.connect('onboarding.db')
    
    stats = {
        "total_users": 0,
        "fully_onboarded": 0,
        "step_completion": {},
        "recent_activity": 0
    }
    
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    stats["total_users"] = cursor.fetchone()[0]
    
    # Fully onboarded
    cursor.execute("""
        SELECT COUNT(DISTINCT u.id) FROM users u
        WHERE (SELECT COUNT(*) FROM onboarding_progress op 
               WHERE op.user_id = u.id AND op.completed = 1) = 5
    """)
    stats["fully_onboarded"] = cursor.fetchone()[0]
    
    conn.close()
    return jsonify(stats)

# ============== Bulk Import Endpoint ==============

@app.route('/api/person-users/bulk', methods=['POST'])
def bulk_import():
    """Bulk import users from CSV data."""
    import csv
    import io
    
    # Handle CSV data from request
    if 'file' in request.files:
        file = request.files['file']
        content = file.read().decode('utf-8')
    else:
        data = request.get_json()
        content = data.get('csv_data', '')
    
    reader = csv.DictReader(io.StringIO(content))
    
    results = {"created": [], "skipped": [], "errors": []}
    
    conn = sqlite3.connect('onboarding.db')
    cursor = conn.cursor()
    
    for row in reader:
        try:
            firstname = row.get('userfirstname', '').strip()
            lastname = row.get('userlastname', '').strip()
            email = row.get('useremail', '').strip()
            tags = row.get('additionalTags', '').strip()
            role = row.get('roletype', 'user').strip()
            
            if not all([firstname, lastname, email]):
                results["errors"].append({
                    "email": email or "unknown",
                    "error": "Missing required fields"
                })
                continue
            
            name = f"{firstname} {lastname}"
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                results["skipped"].append({"email": email, "reason": "Already exists"})
                continue
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (email, name, role, tags) VALUES (?, ?, ?, ?)",
                (email, name, role, tags)
            )
            user_id = cursor.lastrowid
            
            # Initialize onboarding steps
            for step in ONBOARDING_STEPS:
                cursor.execute(
                    "INSERT INTO onboarding_progress (user_id, step_name) VALUES (?, ?)",
                    (user_id, step['name'])
                )
            
            results["created"].append({"email": email, "id": user_id})
            
        except Exception as e:
            results["errors"].append({
                "email": row.get('useremail', 'unknown'),
                "error": str(e)
            })
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "summary": {
            "created": len(results["created"]),
            "skipped": len(results["skipped"]),
            "errors": len(results["errors"])
        },
        "details": results
    })

@app.route('/api/person-users/template', methods=['GET'])
def csv_template():
    """Return CSV template for bulk import."""
    template = """userfirstname,userlastname,useremail,additionalTags,roletype,associatePrimaryPAT,associateSecondaryPAT
John,Doe,john.doe@company.com,"team:engineering,level:senior",developer,john_primary_pat,john_backup_pat
Jane,Smith,jane.smith@company.com,team:data-science,user,jane_pat,
Bob,Johnson,bob.j@company.com,,admin,,"""
    
    return template, 200, {'Content-Type': 'text/csv'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8525, debug=True)
```

<!-- ------------------------ -->
## PAT Lifecycle Management

Programmatic Access Tokens (PATs) are essential for secure, scriptable access to Snowflake.

### Creating a PAT

Generate PATs using Snowflake SQL:

```sql
-- Create a PAT for a user
ALTER USER john_doe 
ADD PROGRAMMATIC ACCESS TOKEN john_primary_pat 
DAYS_TO_EXPIRY = 90;

-- View existing PATs
DESCRIBE USER john_doe;

-- Rotate a PAT
ALTER USER john_doe 
DROP PROGRAMMATIC ACCESS TOKEN john_primary_pat;

ALTER USER john_doe 
ADD PROGRAMMATIC ACCESS TOKEN john_primary_pat_v2 
DAYS_TO_EXPIRY = 90;
```

### PAT Best Practices

1. **Expiration**: Set appropriate expiration (30-90 days)
2. **Rotation**: Implement automated rotation before expiry
3. **Storage**: Never commit PATs to source control
4. **Monitoring**: Track PAT usage in activity logs
5. **Least Privilege**: Grant minimal required permissions

### Generating PAT SQL from Admin Dashboard

```python
def generate_pat_sql(username: str, pat_name: str, days: int = 90) -> str:
    """Generate SQL for creating a PAT."""
    return f"""
-- Create PAT for {username}
ALTER USER {username} 
ADD PROGRAMMATIC ACCESS TOKEN {pat_name} 
DAYS_TO_EXPIRY = {days};

-- Verify PAT creation
DESCRIBE USER {username};
"""
```

<!-- ------------------------ -->
## Running the Applications

### Start the Flask API

```bash
python api_server.py
# API running on http://localhost:8525
```

### Start AdminApp

```bash
streamlit run admin_app.py --server.port 8521
# Admin dashboard at http://localhost:8521
```

### Start UserApp

```bash
streamlit run user_app.py --server.port 8522
# User portal at http://localhost:8522
```

### Combined Launcher Script

```bash
#!/bin/bash
# launcher.sh - Start all services

# Start Flask API in background
python api_server.py &
API_PID=$!

# Start AdminApp
streamlit run admin_app.py --server.port 8521 --server.headless true &
ADMIN_PID=$!

# Start UserApp
streamlit run user_app.py --server.port 8522 --server.headless true &
USER_PID=$!

echo "Services started:"
echo "  API Server: http://localhost:8525 (PID: $API_PID)"
echo "  AdminApp:   http://localhost:8521 (PID: $ADMIN_PID)"
echo "  UserApp:    http://localhost:8522 (PID: $USER_PID)"

# Wait for all processes
wait
```

<!-- ------------------------ -->
## Testing the System

### Test API Endpoints

```bash
# Get onboarding stats
curl http://localhost:8525/api/service-admin/stats

# List users
curl http://localhost:8525/api/service-admin/users

# Get CSV template
curl http://localhost:8525/api/person-users/template

# Bulk import users
curl -X POST http://localhost:8525/api/person-users/bulk \
  -H "Content-Type: application/json" \
  -d '{"csv_data": "userfirstname,userlastname,useremail\nTest,User,test@example.com"}'
```

### Verify Cortex API Integration

```python
import requests

def test_cortex_inference(pat_token: str, account_url: str):
    """Test Cortex REST API inference."""
    response = requests.post(
        f"{account_url}/api/v2/cortex/inference:complete",
        headers={
            "Authorization": f"Bearer {pat_token}",
            "Content-Type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-5",
            "messages": [
                {"role": "user", "content": "Say 'Hello from Cortex!' in exactly those words."}
            ],
            "max_tokens": 50
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Cortex API working!")
        print(f"Response: {result['choices'][0]['message']['content']}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False
```

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've built a complete REST API onboarding system for Snowflake Cortex with:

- **AdminApp**: Server-side dashboard for managing users and tracking progress
- **UserApp**: Client-side portal for self-service onboarding
- **REST API**: Programmatic endpoints for automation and integration
- **PAT Management**: Secure token lifecycle handling
- **Bulk Import**: CSV-based user provisioning

### What You Learned
- Building Streamlit dashboards for admin and user interfaces
- Creating Flask REST APIs for backend services
- Managing Snowflake PAT lifecycle programmatically
- Implementing bulk user import with CSV parsing
- Integrating with Snowflake Cortex REST API

### Related Resources
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Programmatic Access Tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Next Steps
- Add SSO integration for enterprise authentication
- Implement email notifications for onboarding reminders
- Create monitoring dashboards for API usage
- Add role-based access control (RBAC) to AdminApp

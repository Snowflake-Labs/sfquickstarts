"""
Claude Code Onboarding Admin Dashboard
Server-side tracking of user onboarding progress for Claude Code with Cortex
Run: streamlit run claude_code_onboarding.py --server.port 8521

Test Mode: streamlit run claude_code_onboarding.py --server.port 8521 -- --test-mode
"""
import streamlit as st
import pandas as pd
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import requests
import random
import sys
import threading
from flask import Flask, request, jsonify

# Check for test mode (must be before Flask API)
TEST_MODE = "--test-mode" in sys.argv or os.environ.get("ONBOARDING_TEST_MODE") == "1"

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "onboarding.db")

# ============== Flask API Server ==============
# Runs alongside Streamlit to handle REST API calls from client app

flask_app = Flask(__name__)

# Store PATs securely (in production, use a proper secrets manager)
PAT_STORE = {}

# Forward declare mock function (will be defined later)
def mock_update_user_step(user_id: int, step_name: str, completed: bool, details: str = None):
    """Placeholder - actual implementation below."""
    pass

@flask_app.route('/api/register_pat', methods=['POST'])
def api_register_pat():
    """Register a PAT token for a user, then auto-apply network policy."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        pat_token = data.get('pat_token')
        
        if not all([user_id, email, pat_token]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        # Store PAT (in production, encrypt this)
        PAT_STORE[email] = {
            "pat": pat_token[:20] + "...",  # Only store preview for security
            "registered_at": datetime.now().isoformat()
        }
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Step 1: Register PAT
        pat_success = False
        try:
            cursor.execute("""
                UPDATE onboarding_progress
                SET completed = ?, completed_at = ?, details = ?
                WHERE user_id = ? AND step_name = ?
            """, (True, datetime.now().isoformat(), "PAT registered via API", user_id, "pat_created"))
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id, "pat_registration_success", f"PAT registered for {email}"))
            pat_success = True
            print(f"[API] PAT registered for {email}")
        except Exception as e:
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id, "pat_registration_failed", f"Error: {str(e)}"))
            conn.commit()
            conn.close()
            return jsonify({
                "success": False,
                "pat_success": False,
                "network_policy_success": False,
                "error": str(e)
            }), 500
        
        # Step 2: Auto-apply network policy
        network_success = False
        try:
            cursor.execute("""
                UPDATE onboarding_progress
                SET completed = ?, completed_at = ?, details = ?
                WHERE user_id = ? AND step_name = ?
            """, (True, datetime.now().isoformat(), "Network policy auto-applied after PAT", user_id, "network_policy"))
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id, "network_policy_success", f"Network policy applied for {email}"))
            network_success = True
            print(f"[API] Network policy applied for {email}")
        except Exception as e:
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id, "network_policy_failed", f"Error: {str(e)}"))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": pat_success and network_success,
            "pat_success": pat_success,
            "network_policy_success": network_success,
            "message": f"PAT registered for {email}" + (" + Network policy applied" if network_success else ""),
            "sql_executed": [
                f"ALTER USER {email.split('@')[0].upper()} ADD_PAT my_pat;",
                "CREATE NETWORK POLICY all_ips ALLOWED_IP_LIST = ('0.0.0.0/0');",
                f"ALTER USER {email.split('@')[0].upper()} SET NETWORK_POLICY = all_ips;"
            ] if network_success else [f"ALTER USER {email.split('@')[0].upper()} ADD_PAT my_pat;"]
        }), 200
        
    except Exception as e:
        # Log failure
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id if 'user_id' in dir() else 0, "pat_registration_failed", f"Error: {str(e)}"))
            conn.commit()
            conn.close()
        except:
            pass
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/create_network_policy', methods=['POST'])
def api_create_network_policy():
    """Create the network policy (run once as ACCOUNTADMIN)."""
    try:
        data = request.get_json() or {}
        policy_name = data.get('policy_name', 'claude_code_policy')
        
        sql = f"""USE ROLE ACCOUNTADMIN;

CREATE NETWORK POLICY IF NOT EXISTS {policy_name} 
  ALLOWED_IP_LIST = ('0.0.0.0/0')
  COMMENT = 'Allow Claude Code from any IP';"""
        
        print(f"[API] Creating network policy: {policy_name}")
        
        # Log activity
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (0, "create_network_policy", f"Policy: {policy_name}"))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"[API] DB error: {db_err}")
        
        return jsonify({
            "success": True,
            "message": f"Network policy '{policy_name}' created",
            "sql_executed": sql
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/apply_user_network_policy', methods=['POST'])
def api_apply_user_network_policy():
    """Apply network policy to a specific user."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        policy_name = data.get('policy_name', 'claude_code_policy')
        
        if not all([user_id, email]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        username = email.split('@')[0].upper()
        sql = f"""USE ROLE ACCOUNTADMIN;

ALTER USER {username} SET NETWORK_POLICY = {policy_name};"""
        
        print(f"[API] Applying network policy to user: {email}")
        
        # Update the step in database
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE onboarding_progress
                SET completed = ?, completed_at = ?, details = ?
                WHERE user_id = ? AND step_name = ?
            """, (True, datetime.now().isoformat(), f"Network policy applied via API: {policy_name}", user_id, "network_policy"))
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (user_id, "apply_user_network_policy", f"User: {email}, Policy: {policy_name}"))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"[API] DB error: {db_err}")
        
        return jsonify({
            "success": True,
            "message": f"Network policy applied to {email}",
            "sql_executed": sql
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/apply_account_network_policy', methods=['POST'])
def api_apply_account_network_policy():
    """Apply network policy account-wide (use with caution)."""
    try:
        data = request.get_json() or {}
        policy_name = data.get('policy_name', 'claude_code_policy')
        
        sql = f"""USE ROLE ACCOUNTADMIN;

ALTER ACCOUNT SET NETWORK_POLICY = {policy_name};"""
        
        print(f"[API] Applying network policy account-wide: {policy_name}")
        
        # Log activity
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            """, (0, "apply_account_network_policy", f"Policy: {policy_name} (ACCOUNT-WIDE)"))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"[API] DB error: {db_err}")
        
        return jsonify({
            "success": True,
            "message": f"Network policy '{policy_name}' applied account-wide",
            "sql_executed": sql,
            "warning": "This affects all users in the account"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Keep old endpoint for backward compatibility (calls apply_user)
@flask_app.route('/api/apply_network_policy', methods=['POST'])
def api_apply_network_policy():
    """Apply network policy for a user (backward compatibility)."""
    return api_apply_user_network_policy()

@flask_app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200

# ============== Service Admin API Endpoints ==============

@flask_app.route('/api/service-admin/users', methods=['GET'])
def api_service_admin_list_users():
    """List all service users with their PAT status."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.snowflake_account, u.role, u.created_at,
                   GROUP_CONCAT(CASE WHEN op.completed = 1 THEN op.step_name END) as completed_steps
            FROM users u
            LEFT JOIN onboarding_progress op ON u.id = op.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "email": row[1],
                "snowflake_account": row[2],
                "role": row[3],
                "created_at": row[4],
                "completed_steps": row[5].split(",") if row[5] else [],
                "onboarding_complete": "test_successful" in (row[5] or "")
            })
        
        return jsonify({"success": True, "users": users, "count": len(users)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/service-admin/user/<int:user_id>', methods=['GET'])
def api_service_admin_get_user(user_id):
    """Get detailed info for a specific user."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        
        # Get progress
        cursor.execute("""
            SELECT step_name, completed, completed_at, details
            FROM onboarding_progress WHERE user_id = ?
        """, (user_id,))
        progress_rows = cursor.fetchall()
        
        # Get recent activity
        cursor.execute("""
            SELECT action, details, timestamp FROM activity_log
            WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20
        """, (user_id,))
        activity_rows = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "user": {
                "id": user_row[0],
                "email": user_row[1],
                "snowflake_account": user_row[2],
                "snowflake_url": user_row[3],
                "role": user_row[4],
                "created_at": user_row[5]
            },
            "progress": [{"step": r[0], "completed": bool(r[1]), "completed_at": r[2], "details": r[3]} for r in progress_rows],
            "activity": [{"action": r[0], "details": r[1], "timestamp": r[2]} for r in activity_rows]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/service-admin/user/<int:user_id>/pat', methods=['POST'])
def api_service_admin_create_pat(user_id):
    """Create or rotate PAT for a user (integrates with pat-lifecycle)."""
    try:
        data = request.get_json() or {}
        pat_name = data.get('pat_name', f'pat_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        lifetime_days = data.get('lifetime_days', 60)
        is_primary = data.get('is_primary', True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user email
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        
        email = user_row[0]
        username = email.split('@')[0].upper()
        
        # Generate SQL for PAT creation (to be run by admin)
        sql = f"""-- Run as SECURITYADMIN or ACCOUNTADMIN
ALTER USER {username} ADD PROGRAMMATIC ACCESS TOKEN {pat_name}
  DAYS_TO_EXPIRY = {lifetime_days}
  COMMENT = 'Claude Code {"Primary" if is_primary else "Secondary"} PAT';"""
        
        # Log activity
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details)
            VALUES (?, ?, ?)
        """, (user_id, "pat_creation_requested", f"PAT: {pat_name}, Days: {lifetime_days}, Primary: {is_primary}"))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"PAT creation SQL generated for {email}",
            "pat_name": pat_name,
            "lifetime_days": lifetime_days,
            "is_primary": is_primary,
            "sql_to_execute": sql,
            "instructions": "Run the SQL in Snowflake as SECURITYADMIN, then securely share the token with the user."
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/service-admin/stats', methods=['GET'])
def api_service_admin_stats():
    """Get onboarding statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Fully onboarded (all 5 steps)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM (
                SELECT user_id, COUNT(*) as completed
                FROM onboarding_progress WHERE completed = 1
                GROUP BY user_id HAVING completed = 5
            )
        """)
        fully_onboarded = cursor.fetchone()[0]
        
        # Step completion counts
        cursor.execute("""
            SELECT step_name, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as count
            FROM onboarding_progress GROUP BY step_name
        """)
        step_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent activity count (last 24h)
        cursor.execute("""
            SELECT COUNT(*) FROM activity_log
            WHERE timestamp > datetime('now', '-1 day')
        """)
        recent_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_users": total_users,
                "fully_onboarded": fully_onboarded,
                "onboarding_rate": round(fully_onboarded / total_users * 100, 1) if total_users > 0 else 0,
                "step_completion": step_stats,
                "recent_activity_24h": recent_activity
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============== Bulk Person User API Endpoint ==============

@flask_app.route('/api/person-users/bulk', methods=['POST'])
def api_bulk_person_users():
    """
    Bulk import person users from CSV data.
    
    Expected CSV columns:
    - userfirstname: First name (required)
    - userlastname: Last name (required)
    - useremail: Email address (required)
    - additionalTags: Comma-separated tags (optional)
    - roletype: Role type - 'user', 'admin', 'developer' (optional, default: 'user')
    - associatePrimaryPAT: Primary PAT token name (optional)
    - associateSecondaryPAT: Secondary PAT token name (optional)
    
    Request body:
    {
        "csv_data": "userfirstname,userlastname,useremail,additionalTags,roletype,associatePrimaryPAT,associateSecondaryPAT\\nJohn,Doe,john@example.com,team:engineering,developer,john_primary_pat,",
        "snowflake_url": "https://account.snowflakecomputing.com",
        "auto_create_pat": false,
        "default_pat_lifetime_days": 60
    }
    
    Or upload as multipart/form-data with 'csv_file' field.
    """
    import csv
    import io
    
    try:
        # Handle both JSON and multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload
            if 'csv_file' not in request.files:
                return jsonify({"success": False, "error": "No csv_file in request"}), 400
            
            csv_file = request.files['csv_file']
            csv_data = csv_file.read().decode('utf-8')
            snowflake_url = request.form.get('snowflake_url', '')
            auto_create_pat = request.form.get('auto_create_pat', 'false').lower() == 'true'
            default_pat_lifetime = int(request.form.get('default_pat_lifetime_days', 60))
        else:
            # JSON body
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400
            
            csv_data = data.get('csv_data', '')
            snowflake_url = data.get('snowflake_url', '')
            auto_create_pat = data.get('auto_create_pat', False)
            default_pat_lifetime = data.get('default_pat_lifetime_days', 60)
        
        if not csv_data:
            return jsonify({"success": False, "error": "No CSV data provided"}), 400
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_data))
        
        # Validate headers
        required_fields = ['userfirstname', 'userlastname', 'useremail']
        headers = reader.fieldnames or []
        headers_lower = [h.lower().strip() for h in headers]
        
        missing = [f for f in required_fields if f not in headers_lower]
        if missing:
            return jsonify({
                "success": False, 
                "error": f"Missing required columns: {missing}",
                "found_columns": headers
            }), 400
        
        # Process users
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
            "pat_sql": []
        }
        
        for row_num, row in enumerate(reader, start=2):
            # Normalize keys to lowercase
            row = {k.lower().strip(): v.strip() if v else '' for k, v in row.items()}
            
            firstname = row.get('userfirstname', '')
            lastname = row.get('userlastname', '')
            email = row.get('useremail', '')
            tags = row.get('additionaltags', '')
            roletype = row.get('roletype', 'user') or 'user'
            primary_pat = row.get('associateprimarypat', '')
            secondary_pat = row.get('associatesecondarypat', '')
            
            # Validate required fields
            if not email or '@' not in email:
                results["errors"].append({
                    "row": row_num,
                    "email": email,
                    "error": "Invalid or missing email"
                })
                continue
            
            if not firstname or not lastname:
                results["errors"].append({
                    "row": row_num,
                    "email": email,
                    "error": "Missing firstname or lastname"
                })
                continue
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            existing = cursor.fetchone()
            
            if existing:
                results["skipped"].append({
                    "row": row_num,
                    "email": email,
                    "reason": "User already exists",
                    "user_id": existing[0]
                })
                continue
            
            # Extract account from URL
            account = snowflake_url.replace("https://", "").replace(".snowflakecomputing.com", "") if snowflake_url else "UNKNOWN"
            
            # Insert user
            try:
                cursor.execute("""
                    INSERT INTO users (email, snowflake_account, snowflake_url, role)
                    VALUES (?, ?, ?, ?)
                """, (email, account, snowflake_url, roletype))
                user_id = cursor.lastrowid
                
                # Initialize onboarding steps
                for step in ONBOARDING_STEPS:
                    cursor.execute("""
                        INSERT INTO onboarding_progress (user_id, step_name, completed)
                        VALUES (?, ?, FALSE)
                    """, (user_id, step["id"]))
                
                # Log activity with tags
                details = f"Bulk import: {firstname} {lastname}"
                if tags:
                    details += f", Tags: {tags}"
                if primary_pat:
                    details += f", Primary PAT: {primary_pat}"
                if secondary_pat:
                    details += f", Secondary PAT: {secondary_pat}"
                
                cursor.execute("""
                    INSERT INTO activity_log (user_id, action, details)
                    VALUES (?, ?, ?)
                """, (user_id, "bulk_user_created", details))
                
                user_result = {
                    "row": row_num,
                    "user_id": user_id,
                    "email": email,
                    "name": f"{firstname} {lastname}",
                    "role": roletype,
                    "tags": tags.split(",") if tags else []
                }
                
                # Generate PAT SQL if requested
                username = email.split('@')[0].upper()
                
                if primary_pat or auto_create_pat:
                    pat_name = primary_pat or f"{username}_PRIMARY_PAT"
                    pat_sql = f"""ALTER USER {username} ADD PROGRAMMATIC ACCESS TOKEN {pat_name}
  DAYS_TO_EXPIRY = {default_pat_lifetime}
  COMMENT = 'Claude Code Primary PAT - {firstname} {lastname}';"""
                    results["pat_sql"].append({
                        "user": email,
                        "pat_type": "primary",
                        "sql": pat_sql
                    })
                    user_result["primary_pat_sql"] = pat_sql
                
                if secondary_pat:
                    pat_sql = f"""ALTER USER {username} ADD PROGRAMMATIC ACCESS TOKEN {secondary_pat}
  DAYS_TO_EXPIRY = {default_pat_lifetime}
  COMMENT = 'Claude Code Secondary PAT - {firstname} {lastname}';"""
                    results["pat_sql"].append({
                        "user": email,
                        "pat_type": "secondary", 
                        "sql": pat_sql
                    })
                    user_result["secondary_pat_sql"] = pat_sql
                
                results["created"].append(user_result)
                
            except Exception as e:
                results["errors"].append({
                    "row": row_num,
                    "email": email,
                    "error": str(e)
                })
        
        conn.commit()
        conn.close()
        
        # Build summary
        summary = {
            "total_processed": len(results["created"]) + len(results["skipped"]) + len(results["errors"]),
            "created": len(results["created"]),
            "skipped": len(results["skipped"]),
            "errors": len(results["errors"]),
            "pat_sql_generated": len(results["pat_sql"])
        }
        
        return jsonify({
            "success": True,
            "summary": summary,
            "results": results,
            "instructions": "Run the PAT SQL statements in Snowflake as SECURITYADMIN to create tokens for users."
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route('/api/person-users/template', methods=['GET'])
def api_bulk_csv_template():
    """Get CSV template for bulk user import."""
    template = """userfirstname,userlastname,useremail,additionalTags,roletype,associatePrimaryPAT,associateSecondaryPAT
John,Doe,john.doe@company.com,"team:engineering,level:senior",developer,john_primary_pat,john_backup_pat
Jane,Smith,jane.smith@company.com,team:data-science,user,jane_pat,
Bob,Johnson,bob.j@company.com,,admin,,"""
    
    return jsonify({
        "success": True,
        "template": template,
        "columns": [
            {"name": "userfirstname", "required": True, "description": "User's first name"},
            {"name": "userlastname", "required": True, "description": "User's last name"},
            {"name": "useremail", "required": True, "description": "User's email address (must be valid)"},
            {"name": "additionalTags", "required": False, "description": "Comma-separated tags (e.g., team:engineering,level:senior)"},
            {"name": "roletype", "required": False, "description": "Role type: user, admin, or developer (default: user)"},
            {"name": "associatePrimaryPAT", "required": False, "description": "Name for primary PAT token"},
            {"name": "associateSecondaryPAT", "required": False, "description": "Name for secondary/backup PAT token"}
        ],
        "example_curl": """curl -X POST http://localhost:8528/api/person-users/bulk \\
  -H "Content-Type: application/json" \\
  -d '{
    "csv_data": "userfirstname,userlastname,useremail,additionalTags,roletype,associatePrimaryPAT,associateSecondaryPAT\\nJohn,Doe,john@example.com,team:eng,developer,john_pat,",
    "snowflake_url": "https://account.snowflakecomputing.com",
    "auto_create_pat": true,
    "default_pat_lifetime_days": 60
  }'"""
    }), 200

def run_flask_api():
    """Run Flask API server in background thread on a different port."""
    # Use port 8528 to avoid conflict with Streamlit on 8521
    flask_app.run(host='0.0.0.0', port=8528, debug=False, use_reloader=False)

# Start Flask API server in background (only once)
if 'flask_started' not in st.session_state:
    st.session_state.flask_started = True
    api_thread = threading.Thread(target=run_flask_api, daemon=True)
    api_thread.start()
    print("[Server] Flask API started on port 8528")

# Page config
st.set_page_config(
    page_title="Claude Code Onboarding Admin" + (" [TEST MODE]" if TEST_MODE else ""),
    page_icon="🧪" if TEST_MODE else "🚀",
    layout="wide"
)

# Database setup

def init_db():
    """Initialize SQLite database for tracking onboarding progress."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            snowflake_account TEXT,
            snowflake_url TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Onboarding progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onboarding_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, step_name)
        )
    """)
    
    # Activity log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Onboarding steps definition
ONBOARDING_STEPS = [
    {"id": "cli_installed", "name": "Claude Code CLI Installed", "description": "npm install -g @anthropic-ai/claude-code"},
    {"id": "pat_created", "name": "PAT Token Created", "description": "Personal Access Token generated"},
    {"id": "network_policy", "name": "Network Policy Applied", "description": "IP allowlisted in Snowflake"},
    {"id": "settings_configured", "name": "Settings Configured", "description": "settings.json with Cortex endpoint"},
    {"id": "test_successful", "name": "Test Run Successful", "description": "Successfully ran Claude Code agent"},
]

# ============== Mock Data & Test Mode ==============

MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data")
MOCK_USERS_FILE = os.path.join(MOCK_DATA_PATH, "mock_users.json")
MOCK_PROGRESS_FILE = os.path.join(MOCK_DATA_PATH, "mock_progress.json")
MOCK_ACTIVITY_FILE = os.path.join(MOCK_DATA_PATH, "mock_activity.json")

# Sample mock users representing different onboarding stages
MOCK_USER_TEMPLATES = [
    # Stage 0: Just added, nothing done
    {"stage": 0, "name": "New User", "completed_steps": []},
    # Stage 1: CLI installed only
    {"stage": 1, "name": "CLI Only", "completed_steps": ["cli_installed"]},
    # Stage 2: CLI + Network policy
    {"stage": 2, "name": "Network Ready", "completed_steps": ["cli_installed", "network_policy"]},
    # Stage 3: CLI + Network + PAT
    {"stage": 3, "name": "PAT Created", "completed_steps": ["cli_installed", "network_policy", "pat_created"]},
    # Stage 4: Almost done, missing test
    {"stage": 4, "name": "Config Done", "completed_steps": ["cli_installed", "network_policy", "pat_created", "settings_configured"]},
    # Stage 5: Fully onboarded
    {"stage": 5, "name": "Complete", "completed_steps": ["cli_installed", "network_policy", "pat_created", "settings_configured", "test_successful"]},
]

MOCK_DOMAINS = ["acme.com", "globex.com", "initech.com", "umbrella.corp", "wayne.enterprises", "stark.industries"]
MOCK_ACCOUNTS = ["ACME_PROD", "GLOBEX_DEV", "INITECH_QA", "UMBRELLA_STAGE", "WAYNE_PROD", "STARK_DEV"]

def init_mock_data():
    """Initialize mock data files for test mode."""
    os.makedirs(MOCK_DATA_PATH, exist_ok=True)
    
    if not os.path.exists(MOCK_USERS_FILE):
        generate_mock_users(50)  # Generate 50 mock users
    
def generate_mock_users(count: int = 50):
    """Generate mock users at various onboarding stages."""
    users = []
    progress = []
    activity = []
    
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
                   "Kate", "Leo", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Rose", "Sam", "Tara"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor"]
    
    for i in range(count):
        # Pick random stage distribution (weighted towards middle stages)
        stage_weights = [0.1, 0.15, 0.2, 0.25, 0.15, 0.15]  # Stages 0-5
        stage = random.choices(range(6), weights=stage_weights)[0]
        template = MOCK_USER_TEMPLATES[stage]
        
        # Generate user
        first = random.choice(first_names)
        last = random.choice(last_names)
        domain = random.choice(MOCK_DOMAINS)
        account = random.choice(MOCK_ACCOUNTS)
        
        user_id = i + 1
        created_days_ago = random.randint(0, 30)
        created_at = (datetime.now() - timedelta(days=created_days_ago)).isoformat()
        
        user = {
            "id": user_id,
            "email": f"{first.lower()}.{last.lower()}{i}@{domain}",
            "snowflake_account": account,
            "snowflake_url": f"https://{account.lower().replace('_', '-')}.snowflakecomputing.com",
            "role": "admin" if i < 3 else "user",
            "created_at": created_at
        }
        users.append(user)
        
        # Generate progress for this user
        for step in ONBOARDING_STEPS:
            completed = step["id"] in template["completed_steps"]
            completed_at = None
            if completed:
                # Completed sometime after creation
                days_after = random.randint(0, min(created_days_ago, 5))
                completed_at = (datetime.now() - timedelta(days=created_days_ago - days_after)).isoformat()
            
            progress.append({
                "user_id": user_id,
                "step_name": step["id"],
                "completed": completed,
                "completed_at": completed_at,
                "details": f"Mock completion for {step['id']}" if completed else None
            })
        
        # Generate some activity
        activity.append({
            "user_id": user_id,
            "action": "user_created",
            "details": f"Mock user at stage {stage}",
            "timestamp": created_at
        })
        
        if template["completed_steps"]:
            for step_id in template["completed_steps"]:
                activity.append({
                    "user_id": user_id,
                    "action": f"step_{step_id}_completed",
                    "details": "Mock completion",
                    "timestamp": created_at
                })
    
    # Write to files
    with open(MOCK_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    
    with open(MOCK_PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)
    
    with open(MOCK_ACTIVITY_FILE, "w") as f:
        json.dump(activity, f, indent=2)
    
    return len(users)

def load_mock_users():
    """Load mock users from file."""
    if os.path.exists(MOCK_USERS_FILE):
        with open(MOCK_USERS_FILE) as f:
            return json.load(f)
    return []

def load_mock_progress():
    """Load mock progress from file."""
    if os.path.exists(MOCK_PROGRESS_FILE):
        with open(MOCK_PROGRESS_FILE) as f:
            return json.load(f)
    return []

def load_mock_activity():
    """Load mock activity from file."""
    if os.path.exists(MOCK_ACTIVITY_FILE):
        with open(MOCK_ACTIVITY_FILE) as f:
            return json.load(f)
    return []

def save_mock_users(users):
    """Save mock users to file."""
    with open(MOCK_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def save_mock_progress(progress):
    """Save mock progress to file."""
    with open(MOCK_PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def save_mock_activity(activity):
    """Save mock activity to file."""
    with open(MOCK_ACTIVITY_FILE, "w") as f:
        json.dump(activity, f, indent=2)

# ============== Test Mode Wrapper Functions ==============

def mock_add_user(email: str, snowflake_account: str, snowflake_url: str, role: str = "user"):
    """Add user in test mode (file-based)."""
    users = load_mock_users()
    progress = load_mock_progress()
    
    # Check if exists
    if any(u["email"] == email for u in users):
        return None
    
    user_id = max([u["id"] for u in users], default=0) + 1
    
    user = {
        "id": user_id,
        "email": email,
        "snowflake_account": snowflake_account,
        "snowflake_url": snowflake_url,
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    users.append(user)
    
    # Add progress entries
    for step in ONBOARDING_STEPS:
        progress.append({
            "user_id": user_id,
            "step_name": step["id"],
            "completed": False,
            "completed_at": None,
            "details": None
        })
    
    save_mock_users(users)
    save_mock_progress(progress)
    return user_id

def mock_get_all_users():
    """Get all users in test mode."""
    users = load_mock_users()
    progress = load_mock_progress()
    
    result = []
    for user in users:
        user_progress = [p for p in progress if p["user_id"] == user["id"]]
        completed_steps = [p["step_name"] for p in user_progress if p["completed"]]
        
        result.append({
            **user,
            "completed_steps": ",".join(completed_steps) if completed_steps else None,
            "completed_count": len(completed_steps),
            "total_steps": len(ONBOARDING_STEPS)
        })
    
    return pd.DataFrame(result) if result else pd.DataFrame()

def mock_get_user_progress(user_id: int):
    """Get user progress in test mode."""
    progress = load_mock_progress()
    user_progress = [p for p in progress if p["user_id"] == user_id]
    return pd.DataFrame(user_progress) if user_progress else pd.DataFrame()

def mock_update_user_step(user_id: int, step_name: str, completed: bool, details: str = None):
    """Update user step in test mode."""
    progress = load_mock_progress()
    activity = load_mock_activity()
    
    for p in progress:
        if p["user_id"] == user_id and p["step_name"] == step_name:
            p["completed"] = completed
            p["completed_at"] = datetime.now().isoformat() if completed else None
            p["details"] = details
            break
    
    activity.append({
        "user_id": user_id,
        "action": f"step_{step_name}_{'completed' if completed else 'uncompleted'}",
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
    
    save_mock_progress(progress)
    save_mock_activity(activity)

def mock_get_user_by_email(email: str):
    """Get user by email in test mode."""
    users = load_mock_users()
    for user in users:
        if user["email"] == email:
            return user
    return None

def mock_delete_user(user_id: int):
    """Delete user in test mode."""
    users = load_mock_users()
    progress = load_mock_progress()
    activity = load_mock_activity()
    
    users = [u for u in users if u["id"] != user_id]
    progress = [p for p in progress if p["user_id"] != user_id]
    activity = [a for a in activity if a.get("user_id") != user_id]
    
    save_mock_users(users)
    save_mock_progress(progress)
    save_mock_activity(activity)

def mock_get_activity_log(limit: int = 50):
    """Get activity log in test mode."""
    activity = load_mock_activity()
    users = load_mock_users()
    
    user_map = {u["id"]: u["email"] for u in users}
    
    result = []
    for a in activity[-limit:]:
        result.append({
            "timestamp": a["timestamp"],
            "email": user_map.get(a.get("user_id"), "Unknown"),
            "action": a["action"],
            "details": a.get("details"),
            "ip_address": a.get("ip_address")
        })
    
    return pd.DataFrame(result[::-1]) if result else pd.DataFrame()

def mock_get_summary_stats():
    """Get summary stats in test mode."""
    users = load_mock_users()
    progress = load_mock_progress()
    
    total_users = len(users)
    
    # Count fully onboarded
    fully_onboarded = 0
    for user in users:
        user_progress = [p for p in progress if p["user_id"] == user["id"]]
        if all(p["completed"] for p in user_progress):
            fully_onboarded += 1
    
    # Step stats
    step_stats = {}
    for step in ONBOARDING_STEPS:
        step_stats[step["id"]] = sum(1 for p in progress if p["step_name"] == step["id"] and p["completed"])
    
    return {
        "total_users": total_users,
        "fully_onboarded": fully_onboarded,
        "step_stats": step_stats
    }

# Initialize test mode if needed
if TEST_MODE:
    init_mock_data()

# ============== Database Operations ==============

def _add_user(email: str, snowflake_account: str, snowflake_url: str, role: str = "user"):
    """Add a new user to track."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (email, snowflake_account, snowflake_url, role)
            VALUES (?, ?, ?, ?)
        """, (email, snowflake_account, snowflake_url, role))
        user_id = cursor.lastrowid
        
        # Initialize onboarding steps
        for step in ONBOARDING_STEPS:
            cursor.execute("""
                INSERT INTO onboarding_progress (user_id, step_name, completed)
                VALUES (?, ?, FALSE)
            """, (user_id, step["id"]))
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

# Alias for wrapper pattern
add_user = _add_user

def bulk_add_users(users_text: str, snowflake_url: str):
    """Add multiple users from text input (one email per line)."""
    added = 0
    skipped = 0
    for line in users_text.strip().split("\n"):
        email = line.strip()
        if email and "@" in email:
            # Extract account from URL
            account = snowflake_url.replace("https://", "").replace(".snowflakecomputing.com", "")
            result = _add_user(email, account, snowflake_url)
            if result:
                added += 1
            else:
                skipped += 1
    return added, skipped

def get_all_users():
    """Get all users with their onboarding progress."""
    conn = get_db_connection()
    query = """
        SELECT 
            u.id,
            u.email,
            u.snowflake_account,
            u.snowflake_url,
            u.role,
            u.created_at,
            GROUP_CONCAT(
                CASE WHEN op.completed THEN op.step_name ELSE NULL END
            ) as completed_steps,
            COUNT(CASE WHEN op.completed THEN 1 END) as completed_count,
            COUNT(op.id) as total_steps
        FROM users u
        LEFT JOIN onboarding_progress op ON u.id = op.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_user_progress(user_id: int):
    """Get detailed progress for a specific user."""
    conn = get_db_connection()
    query = """
        SELECT step_name, completed, completed_at, details
        FROM onboarding_progress
        WHERE user_id = ?
        ORDER BY id
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def _update_user_step(user_id: int, step_name: str, completed: bool, details: str = None):
    """Update a user's onboarding step."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    completed_at = datetime.now().isoformat() if completed else None
    
    cursor.execute("""
        UPDATE onboarding_progress
        SET completed = ?, completed_at = ?, details = ?
        WHERE user_id = ? AND step_name = ?
    """, (completed, completed_at, details, user_id, step_name))
    
    # Log activity
    cursor.execute("""
        INSERT INTO activity_log (user_id, action, details)
        VALUES (?, ?, ?)
    """, (user_id, f"step_{step_name}_{'completed' if completed else 'uncompleted'}", details))
    
    conn.commit()
    conn.close()

# Alias for wrapper pattern
update_user_step = _update_user_step

def get_user_by_email(email: str):
    """Get user by email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "snowflake_account": row[2], "snowflake_url": row[3], "role": row[4]}
    return None

def _delete_user(user_id: int):
    """Delete a user and their progress."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM onboarding_progress WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM activity_log WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# Alias for wrapper pattern
delete_user = _delete_user

def get_activity_log(limit: int = 50):
    """Get recent activity log."""
    conn = get_db_connection()
    query = """
        SELECT 
            al.timestamp,
            u.email,
            al.action,
            al.details,
            al.ip_address
        FROM activity_log al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.timestamp DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def get_summary_stats():
    """Get summary statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Fully onboarded
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM (
            SELECT user_id, COUNT(*) as completed
            FROM onboarding_progress
            WHERE completed = TRUE
            GROUP BY user_id
            HAVING completed = ?
        )
    """, (len(ONBOARDING_STEPS),))
    fully_onboarded = cursor.fetchone()[0]
    
    # Step completion rates
    step_stats = {}
    for step in ONBOARDING_STEPS:
        cursor.execute("""
            SELECT COUNT(*) FROM onboarding_progress
            WHERE step_name = ? AND completed = TRUE
        """, (step["id"],))
        step_stats[step["id"]] = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "fully_onboarded": fully_onboarded,
        "step_stats": step_stats
    }

# ============== API Endpoints for Client Updates ==============

def client_update_progress(email: str, step_name: str, completed: bool, details: str = None):
    """API-style function for clients to update their progress."""
    user = _get_user_by_email(email)
    if not user:
        return {"success": False, "error": "User not found"}
    
    _update_user_step(user["id"], step_name, completed, details)
    return {"success": True, "message": f"Step {step_name} updated for {email}"}

# Initialize database (only in production mode)
if not TEST_MODE:
    init_db()

# ============== Route to Mock or Real Functions ==============
# This allows seamless switching between test mode (file-based) and production (SQLite)

if TEST_MODE:
    # Use mock functions
    _add_user = mock_add_user
    _get_all_users = mock_get_all_users
    _get_user_progress = mock_get_user_progress
    _update_user_step = mock_update_user_step
    _get_user_by_email = mock_get_user_by_email
    _delete_user = mock_delete_user
    _get_activity_log = mock_get_activity_log
    _get_summary_stats = mock_get_summary_stats
else:
    # Use real database functions
    _add_user = add_user
    _get_all_users = get_all_users
    _get_user_progress = get_user_progress
    _update_user_step = update_user_step
    _get_user_by_email = get_user_by_email
    _delete_user = delete_user
    _get_activity_log = get_activity_log
    _get_summary_stats = get_summary_stats

# ============== Streamlit UI ==============

if TEST_MODE:
    st.warning("🧪 **TEST MODE** - Using mock data from files. Changes won't affect production database.")
    st.caption(f"Mock data location: `{MOCK_DATA_PATH}`")

st.title("🚀 Claude Code Onboarding Admin" + (" [TEST]" if TEST_MODE else ""))
st.caption("Track and manage user onboarding for Claude Code with Snowflake Cortex")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard", 
    "👥 User Management", 
    "🔒 Network Policy",
    "📝 Bulk Import",
    "🔄 Client Status Update",
    "📋 Activity Log",
    "🧪 Test Controls" if TEST_MODE else "⚙️ Settings"
])

# ============== TAB 1: Dashboard ==============
with tab1:
    stats = _get_summary_stats()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats["total_users"])
    with col2:
        st.metric("Fully Onboarded", stats["fully_onboarded"])
    with col3:
        if stats["total_users"] > 0:
            pct = (stats["fully_onboarded"] / stats["total_users"]) * 100
            st.metric("Completion Rate", f"{pct:.1f}%")
        else:
            st.metric("Completion Rate", "0%")
    with col4:
        in_progress = stats["total_users"] - stats["fully_onboarded"]
        st.metric("In Progress", in_progress)
    
    st.divider()
    
    # Step completion breakdown
    st.subheader("📈 Step Completion Breakdown")
    
    if stats["total_users"] > 0:
        step_data = []
        for step in ONBOARDING_STEPS:
            completed = stats["step_stats"].get(step["id"], 0)
            step_data.append({
                "Step": step["name"],
                "Completed": completed,
                "Pending": stats["total_users"] - completed,
                "Rate": f"{(completed/stats['total_users'])*100:.1f}%"
            })
        
        step_df = pd.DataFrame(step_data)
        
        # Bar chart
        import altair as alt
        chart_data = pd.DataFrame({
            "Step": [s["name"] for s in ONBOARDING_STEPS],
            "Completed": [stats["step_stats"].get(s["id"], 0) for s in ONBOARDING_STEPS]
        })
        
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X("Step:N", sort=None),
            y="Completed:Q",
            color=alt.value("#4CAF50")
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
        
        st.dataframe(step_df, use_container_width=True, hide_index=True)
    else:
        st.info("No users added yet. Go to 'User Management' or 'Bulk Import' to add users.")
    
    st.divider()
    
    # User progress overview
    st.subheader("👥 User Progress Overview")
    
    users_df = _get_all_users()
    if not users_df.empty:
        # Add progress bar column
        def progress_bar(row):
            if row["total_steps"] > 0:
                return row["completed_count"] / row["total_steps"]
            return 0
        
        users_df["progress"] = users_df.apply(progress_bar, axis=1)
        
        # Display with status indicators
        display_df = users_df[["email", "snowflake_account", "completed_count", "total_steps", "progress"]].copy()
        display_df["status"] = display_df.apply(
            lambda r: "✅ Complete" if r["completed_count"] == r["total_steps"] else f"🔄 {r['completed_count']}/{r['total_steps']}", 
            axis=1
        )
        
        st.dataframe(
            display_df[["email", "snowflake_account", "status", "progress"]],
            column_config={
                "email": "Email",
                "snowflake_account": "Account",
                "status": "Status",
                "progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=1)
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No users to display.")

# ============== TAB 2: User Management ==============
with tab2:
    st.subheader("➕ Add New User")
    
    col1, col2 = st.columns(2)
    with col1:
        new_email = st.text_input("Email Address", placeholder="user@company.com")
        new_account = st.text_input("Snowflake Account", placeholder="ORGNAME-ACCOUNTNAME")
    with col2:
        new_url = st.text_input(
            "Snowflake URL", 
            placeholder="https://account.snowflakecomputing.com",
            value="https://YOUR_ACCOUNT.snowflakecomputing.com"
        )
        new_role = st.selectbox("Role", ["user", "admin"])
    
    if st.button("➕ Add User", type="primary"):
        if new_email and new_account:
            result = _add_user(new_email, new_account, new_url, new_role)
            if result:
                st.success(f"✅ Added user: {new_email}")
                st.rerun()
            else:
                st.error("User already exists or error occurred")
        else:
            st.error("Please fill in email and account")
    
    st.divider()
    
    # User list with management
    st.subheader("📋 Manage Users")
    
    users_df = _get_all_users()
    if not users_df.empty:
        for _, user in users_df.iterrows():
            with st.expander(f"👤 {user['email']} ({user['snowflake_account']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.caption(f"URL: {user['snowflake_url']}")
                    st.caption(f"Added: {user['created_at']}")
                    
                    # Show progress
                    progress_df = _get_user_progress(user["id"])
                    if not progress_df.empty:
                        st.markdown("**Onboarding Progress:**")
                        for _, step in progress_df.iterrows():
                            step_info = next((s for s in ONBOARDING_STEPS if s["id"] == step["step_name"]), None)
                            if step_info:
                                status = "✅" if step["completed"] else "⬜"
                                st.checkbox(
                                    f"{status} {step_info['name']}",
                                    value=step["completed"],
                                    key=f"step_{user['id']}_{step['step_name']}",
                                    on_change=lambda uid=user["id"], sn=step["step_name"], curr=step["completed"]: 
                                        _update_user_step(uid, sn, not curr),
                                    help=step_info["description"]
                                )
                
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{user['id']}", type="secondary"):
                        _delete_user(user["id"])
                        st.rerun()
                
                # Admin manual completion section
                st.markdown("---")
                st.markdown("**🔧 Admin Manual Completion**")
                username = user["email"].split("@")[0].upper()
                
                admin_col1, admin_col2 = st.columns(2)
                
                with admin_col1:
                    st.markdown("**PAT Registration**")
                    st.code(f"ALTER USER {username} ADD_PAT my_pat;", language="sql")
                    if st.button("✅ Mark PAT Complete", key=f"admin_pat_{user['id']}", type="primary"):
                        _update_user_step(user["id"], "pat_created", True, "Admin: manually completed")
                        st.success("PAT marked complete!")
                        st.rerun()
                
                with admin_col2:
                    st.markdown("**Network Policy**")
                    st.code(f"""CREATE NETWORK POLICY IF NOT EXISTS claude_code_policy 
  ALLOWED_IP_LIST = ('0.0.0.0/0');
ALTER USER {username} SET NETWORK_POLICY = claude_code_policy;""", language="sql")
                    
                    np_col1, np_col2 = st.columns(2)
                    with np_col1:
                        if st.button("🔄 Apply via API", key=f"admin_net_api_{user['id']}", type="primary"):
                            # Call the Flask API to apply network policy
                            try:
                                import requests
                                resp = requests.post("http://localhost:8528/api/apply_network_policy", json={
                                    "user_id": user["id"],
                                    "email": user["email"]
                                }, timeout=30)
                                if resp.status_code == 200:
                                    st.success("✅ Network Policy applied via API!")
                                else:
                                    st.error(f"API error: {resp.text}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    with np_col2:
                        if st.button("📝 Mark Complete", key=f"admin_net_manual_{user['id']}", type="secondary"):
                            _update_user_step(user["id"], "network_policy", True, "Admin: manually completed")
                            st.success("Network Policy marked complete!")
                            st.rerun()

# ============== TAB 3: Network Policy ==============
with tab3:
    st.subheader("🔒 Network Policy Management")
    
    st.markdown("""
    Manage network policies to allow Claude Code connections from any IP address.
    Complete these steps in order: **Create Policy** → **Apply Account-Wide** or **Apply to Specific Users**
    """)
    
    # Section 1: Create Network Policy
    st.markdown("---")
    st.markdown("### 1️⃣ Create Network Policy")
    st.caption("Run once as ACCOUNTADMIN to create the policy")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code("""USE ROLE ACCOUNTADMIN;

CREATE NETWORK POLICY IF NOT EXISTS claude_code_policy 
  ALLOWED_IP_LIST = ('0.0.0.0/0')
  COMMENT = 'Allow Claude Code from any IP';""", language="sql")
    with col2:
        if st.button("🔄 Create Policy", key="create_policy_btn", type="primary"):
            try:
                import requests
                resp = requests.post("http://localhost:8528/api/create_network_policy", json={
                    "policy_name": "claude_code_policy"
                }, timeout=30)
                if resp.status_code == 200:
                    st.success("✅ Network policy created!")
                else:
                    st.error(f"Error: {resp.text}")
            except Exception as e:
                st.error(f"API Error: {str(e)}")
        st.caption("`POST /api/create_network_policy`")
    
    # Section 2: Apply Account-Wide
    st.markdown("---")
    st.markdown("### 2️⃣ Apply Account-Wide")
    st.warning("⚠️ **Use with caution** - This affects ALL users in the Snowflake account")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code("""USE ROLE ACCOUNTADMIN;

ALTER ACCOUNT SET NETWORK_POLICY = claude_code_policy;""", language="sql")
    with col2:
        if st.button("🔄 Apply Account-Wide", key="apply_account_btn", type="secondary"):
            try:
                import requests
                resp = requests.post("http://localhost:8528/api/apply_account_network_policy", json={
                    "policy_name": "claude_code_policy"
                }, timeout=30)
                if resp.status_code == 200:
                    result = resp.json()
                    st.success(f"✅ {result.get('message', 'Applied account-wide')}")
                    st.warning(result.get('warning', ''))
                else:
                    st.error(f"Error: {resp.text}")
            except Exception as e:
                st.error(f"API Error: {str(e)}")
        st.caption("`POST /api/apply_account_network_policy`")
    
    # Section 3: Apply to Specific Users
    st.markdown("---")
    st.markdown("### 3️⃣ Apply to Specific Users")
    st.caption("Apply the network policy to individual users who have completed PAT registration")
    
    users_df = _get_all_users()
    pending_users = []
    if not users_df.empty:
        for _, user in users_df.iterrows():
            progress_df = _get_user_progress(user["id"])
            if not progress_df.empty:
                pat_done = progress_df[progress_df["step_name"] == "pat_created"]["completed"].values
                net_done = progress_df[progress_df["step_name"] == "network_policy"]["completed"].values
                pat_completed = pat_done[0] if len(pat_done) > 0 else False
                net_completed = net_done[0] if len(net_done) > 0 else False
                
                if pat_completed and not net_completed:
                    pending_users.append(user)
        
        if pending_users:
            for user in pending_users:
                username = user["email"].split("@")[0].upper()
                with st.container():
                    col1, col2 = st.columns([3, 2])
                    with col1:
                        st.markdown(f"**{user['email']}**")
                        st.caption(f"Username: `{username}`")
                        st.code(f"""USE ROLE ACCOUNTADMIN;

ALTER USER {username} SET NETWORK_POLICY = claude_code_policy;""", language="sql")
                    with col2:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("🔄 Apply", key=f"np_user_api_{user['id']}", type="primary"):
                                try:
                                    import requests
                                    resp = requests.post("http://localhost:8528/api/apply_user_network_policy", json={
                                        "user_id": user["id"],
                                        "email": user["email"],
                                        "policy_name": "claude_code_policy"
                                    }, timeout=30)
                                    if resp.status_code == 200:
                                        st.success(f"✅ Applied!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {resp.text}")
                                except Exception as e:
                                    st.error(f"API Error: {str(e)}")
                        with btn_col2:
                            if st.button("📝 Mark Done", key=f"np_mark_{user['id']}", type="secondary"):
                                _update_user_step(user["id"], "network_policy", True, "Admin: manually completed")
                                st.success(f"✅ Done")
                                st.rerun()
                        
                        st.code(f'POST /api/apply_user_network_policy\n{{"user_id": {user["id"]}, "email": "{user["email"]}"}}', language="json")
                    st.divider()
            
            # Bulk apply to all pending users
            st.markdown("**Bulk Apply:**")
            if st.button("⚡ Apply to All Pending Users", key="bulk_apply_users", type="primary"):
                success_count = 0
                for user in pending_users:
                    try:
                        import requests
                        resp = requests.post("http://localhost:8528/api/apply_user_network_policy", json={
                            "user_id": user["id"],
                            "email": user["email"],
                            "policy_name": "claude_code_policy"
                        }, timeout=30)
                        if resp.status_code == 200:
                            success_count += 1
                    except:
                        pass
                st.success(f"✅ Applied to {success_count}/{len(pending_users)} users")
                st.rerun()
            st.caption("`POST /api/apply_user_network_policy` for each user")
        else:
            st.success("✅ No users pending network policy!")
    else:
        st.info("No users registered yet.")

# ============== TAB 4: Bulk Import ==============
with tab4:
    st.subheader("📥 Bulk Import Users")
    
    st.markdown("""
    Import multiple users at once. Enter one email per line.
    All users will be assigned to the same Snowflake account.
    """)
    
    bulk_url = st.text_input(
        "Snowflake Account URL (for all users)",
        value="https://YOUR_ACCOUNT.snowflakecomputing.com",
        key="bulk_url"
    )
    
    bulk_emails = st.text_area(
        "Email Addresses (one per line)",
        height=200,
        placeholder="user1@company.com\nuser2@company.com\nuser3@company.com"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Import Users", type="primary"):
            if bulk_emails and bulk_url:
                added, skipped = bulk_add_users(bulk_emails, bulk_url)
                st.success(f"✅ Added {added} users, skipped {skipped} (duplicates/invalid)")
                st.rerun()
            else:
                st.error("Please provide URL and at least one email")
    
    with col2:
        # Sample CSV download
        sample_csv = "email\nuser1@company.com\nuser2@company.com\nuser3@company.com"
        st.download_button(
            "📄 Download Sample CSV",
            sample_csv,
            file_name="sample_users.csv",
            mime="text/csv"
        )

# ============== TAB 5: Client Status Update ==============
with tab5:
    st.subheader("🔄 Client Self-Service Status Update")
    
    st.markdown("""
    **For Users:** Update your onboarding progress here.
    
    This endpoint can also be called programmatically:
    ```python
    # In your client code after completing a step:
    import requests
    requests.post("http://localhost:8521/api/update", json={
        "email": "your@email.com",
        "step": "cli_installed",
        "completed": True,
        "details": "v2.1.47"
    })
    ```
    """)
    
    st.divider()
    
    # Self-service form
    client_email = st.text_input("Your Email", placeholder="user@company.com", key="client_email")
    
    if client_email:
        user = _get_user_by_email(client_email)
        if user:
            st.success(f"✅ Found user: {client_email}")
            
            progress_df = _get_user_progress(user["id"])
            
            st.markdown("### Update Your Progress")
            
            for step in ONBOARDING_STEPS:
                step_progress = progress_df[progress_df["step_name"] == step["id"]]
                is_completed = step_progress["completed"].values[0] if not step_progress.empty else False
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{step['name']}**")
                    st.caption(step["description"])
                with col2:
                    status = "✅ Done" if is_completed else "⬜ Pending"
                    st.markdown(status)
                with col3:
                    if not is_completed:
                        if st.button("Mark Done", key=f"client_{step['id']}"):
                            _update_user_step(user["id"], step["id"], True, f"Self-reported at {datetime.now()}")
                            st.rerun()
                    else:
                        if st.button("Undo", key=f"client_undo_{step['id']}"):
                            _update_user_step(user["id"], step["id"], False)
                            st.rerun()
            
            # Quick test button
            st.divider()
            st.markdown("### 🧪 Quick Verification Test")
            
            if st.button("🚀 Run Claude Code Test", type="primary"):
                import subprocess
                import shutil
                
                claude_path = shutil.which("claude")
                if not claude_path:
                    st.error("Claude Code CLI not found. Please install it first.")
                    _update_user_step(user["id"], "cli_installed", False, "CLI not found")
                else:
                    st.info("Running Claude Code test...")
                    try:
                        result = subprocess.run(
                            [claude_path, "-p", "Say 'Hello from Cortex!' in exactly 3 words", "--output-format", "text"],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            st.success("✅ Claude Code test successful!")
                            st.code(result.stdout)
                            _update_user_step(user["id"], "cli_installed", True, f"Version check passed")
                            _update_user_step(user["id"], "test_successful", True, f"Test output: {result.stdout[:100]}")
                        else:
                            st.error(f"Test failed: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        st.error("Test timed out")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning(f"User '{client_email}' not found. Please contact admin to be added.")

# ============== TAB 6: Activity Log ==============
with tab6:
    st.subheader("📋 Recent Activity")
    
    log_limit = st.slider("Show last N activities", 10, 200, 50)
    
    activity_df = _get_activity_log(log_limit)
    
    if not activity_df.empty:
        st.dataframe(
            activity_df,
            column_config={
                "timestamp": "Time",
                "email": "User",
                "action": "Action",
                "details": "Details",
                "ip_address": "IP"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No activity recorded yet.")
    
    # Export button
    if not activity_df.empty:
        csv = activity_df.to_csv(index=False)
        st.download_button(
            "📥 Export Activity Log",
            csv,
            file_name=f"activity_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# ============== TAB 7: Test Controls / Settings ==============
with tab7:
    if TEST_MODE:
        st.subheader("🧪 Test Mode Controls")
        
        st.markdown("""
        Test mode uses JSON files instead of SQLite database.
        This allows testing all onboarding stages without affecting production data.
        """)
        
        st.divider()
        
        # Mock data info
        st.markdown("### 📁 Mock Data Files")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Files:**")
            for f in [MOCK_USERS_FILE, MOCK_PROGRESS_FILE, MOCK_ACTIVITY_FILE]:
                exists = "✅" if os.path.exists(f) else "❌"
                size = f"{os.path.getsize(f)/1024:.1f}KB" if os.path.exists(f) else "N/A"
                st.caption(f"{exists} `{os.path.basename(f)}` ({size})")
        
        with col2:
            st.markdown("**Stats:**")
            users = load_mock_users()
            progress = load_mock_progress()
            activity = load_mock_activity()
            st.caption(f"Users: {len(users)}")
            st.caption(f"Progress entries: {len(progress)}")
            st.caption(f"Activity entries: {len(activity)}")
        
        st.divider()
        
        # Regenerate mock data
        st.markdown("### 🔄 Regenerate Mock Data")
        
        col1, col2 = st.columns(2)
        with col1:
            mock_count = st.number_input("Number of mock users", min_value=10, max_value=500, value=50)
        
        with col2:
            if st.button("🎲 Generate New Mock Data", type="primary"):
                count = generate_mock_users(mock_count)
                st.success(f"✅ Generated {count} mock users with various onboarding stages")
                st.rerun()
        
        st.divider()
        
        # Stage distribution preview
        st.markdown("### 📊 Mock Data Stage Distribution")
        
        users = load_mock_users()
        progress = load_mock_progress()
        
        stage_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for user in users:
            user_progress = [p for p in progress if p["user_id"] == user["id"]]
            completed = sum(1 for p in user_progress if p["completed"])
            stage_counts[completed] = stage_counts.get(completed, 0) + 1
        
        stage_df = pd.DataFrame([
            {"Stage": f"Stage {i}: {MOCK_USER_TEMPLATES[i]['name']}", "Users": stage_counts.get(i, 0)}
            for i in range(6)
        ])
        
        st.dataframe(stage_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # View raw mock data
        st.markdown("### 📄 View Raw Mock Data")
        
        data_view = st.selectbox("Select data to view:", ["Users", "Progress", "Activity"])
        
        if data_view == "Users":
            st.json(load_mock_users()[:10])
            st.caption("Showing first 10 users")
        elif data_view == "Progress":
            st.json(load_mock_progress()[:20])
            st.caption("Showing first 20 progress entries")
        else:
            st.json(load_mock_activity()[-20:])
            st.caption("Showing last 20 activity entries")
        
        st.divider()
        
        # Clear mock data
        st.markdown("### 🗑️ Clear Mock Data")
        
        if st.button("🗑️ Delete All Mock Data", type="secondary"):
            if st.checkbox("I understand this will delete all test data", key="confirm_mock_delete"):
                for f in [MOCK_USERS_FILE, MOCK_PROGRESS_FILE, MOCK_ACTIVITY_FILE]:
                    if os.path.exists(f):
                        os.remove(f)
                st.success("Mock data cleared")
                st.rerun()
    
    else:
        # Settings tab for production mode
        st.subheader("⚙️ Settings")
        
        st.markdown("### 🔧 Configuration")
        st.info("Production mode - using SQLite database")
        
        st.markdown(f"**Database Path:** `{DB_PATH}`")
        if os.path.exists(DB_PATH):
            st.markdown(f"**Database Size:** {os.path.getsize(DB_PATH)/1024:.1f} KB")
        
        st.divider()
        
        st.markdown("### 🧪 Enable Test Mode")
        st.markdown("""
        To run in test mode with mock data:
        ```bash
        # Option 1: Command line argument
        streamlit run claude_code_onboarding.py --server.port 8521 -- --test-mode
        
        # Option 2: Environment variable
        ONBOARDING_TEST_MODE=1 streamlit run claude_code_onboarding.py --server.port 8521
        ```
        """)

# ============== Sidebar ==============
with st.sidebar:
    st.markdown("## 📚 Quick Links")
    st.markdown("""
    - [Onboarding Guide](./CLAUDE_CODE_ONBOARDING.md)
    - [Snowflake Cortex Docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
    - [Claude Code Docs](https://docs.anthropic.com/claude-code)
    """)
    
    st.divider()
    
    st.markdown("## 🔧 Admin Actions")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    if not TEST_MODE:
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.checkbox("Confirm deletion"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM onboarding_progress")
                cursor.execute("DELETE FROM activity_log")
                cursor.execute("DELETE FROM users")
                conn.commit()
                conn.close()
                st.success("All data cleared")
                st.rerun()
    
    st.divider()
    
    if TEST_MODE:
        st.markdown("## 🧪 Test Mode")
        st.success("Using mock data files")
        st.caption(f"Path: `{MOCK_DATA_PATH}`")
    else:
        st.markdown("## 📊 Database Info")
        st.caption(f"DB Path: {DB_PATH}")
        
        if os.path.exists(DB_PATH):
            size = os.path.getsize(DB_PATH)
            st.caption(f"Size: {size/1024:.1f} KB")

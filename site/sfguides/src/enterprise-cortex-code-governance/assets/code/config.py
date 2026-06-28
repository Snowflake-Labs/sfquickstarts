"""
Cortex Code Credit Manager - Configuration
============================================
Single source of truth. Deployment-specific values (DB, schema, admin roles)
live in config.yaml beside this file. Everything else is here.
"""

import os
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import yaml

APP_NAME = "CoCo Control Hub"
APP_VERSION = "3.0.0"
APP_ICON = "⚡"

SNOWFLAKE_LOGO_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/"
    "Snowflake_Logo.svg/2560px-Snowflake_Logo.svg.png"
)

TABLE_CREDIT_CONFIG = "CC_CREDIT_CONFIG"
TABLE_AUDIT_LOG = "CC_AUDIT_LOG"
TABLE_USAGE_DAILY = "CC_USAGE_DAILY_SUMMARY"
TABLE_USAGE_HOURLY = "CC_USAGE_HOURLY_SUMMARY"
TABLE_CREDIT_REQUESTS = "CC_CREDIT_REQUESTS"
TABLE_APP_CONFIG = "CC_APP_CONFIG"
TABLE_MODEL_CONFIG = "CC_MODEL_CONFIG"
TABLE_MODEL_ROLE_MAPPING = "CC_MODEL_ROLE_MAPPING"
TABLE_USER_COHORT_RESOLVED = "CC_USER_COHORT_RESOLVED"

SURFACES = ["CLI", "SNOWSIGHT", "DESKTOP"]
SURFACE_PARAMS = {
    "CLI":      "CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER",
    "SNOWSIGHT":"CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER",
    "DESKTOP":  "CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER",
}
SURFACE_USAGE_VIEWS = {
    "CLI": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY",
    "SNOWSIGHT": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY",
    "DESKTOP": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_DESKTOP_USAGE_HISTORY",
}

MODEL_CATEGORIES = {
    "TIER_1": {
        "description": "Extended reasoning, multi-step agentic tasks, complex architecture design",
        "tokens_per_credit": "~7K output tokens/credit",
        "best_for": "Data Architects, ML Engineers, Platform Engineers — complex migrations, system design, multi-file refactoring",
    },
    "TIER_2": {
        "description": "General development, code review, analysis, daily coding workflows",
        "tokens_per_credit": "~25K output tokens/credit",
        "best_for": "Data Engineers, Analytics Engineers, Software Developers — daily coding, pipeline development, dbt models, code review",
    },
    "TIER_3": {
        "description": "Quick completions, formatting, simple lookups, autocomplete suggestions",
        "tokens_per_credit": "~100K output tokens/credit",
        "best_for": "Business Analysts, Report Builders, Lite Users — SQL formatting, simple queries, documentation lookup",
    },
}

KNOWN_MODELS = {
    "claude-opus-4-6": {
        "category": ["TIER_1"],
        "description": "Most capable model. Extended thinking with chain-of-thought. Best for architecture reviews, complex debugging, multi-step planning.",
        "popular_for": "System design, security audits, large codebase refactoring, agentic workflows",
    },
    "claude-opus-4-5": {
        "category": ["TIER_1"],
        "description": "Deep reasoning with broad context window. Excels at complex analysis requiring synthesis across many inputs.",
        "popular_for": "Data modeling, migration planning, compliance analysis, long-document processing",
    },
    "claude-sonnet-4-5": {
        "category": ["TIER_1", "TIER_2"],
        "description": "High quality with fast response. Best balance of capability and speed for iterative development.",
        "popular_for": "Code generation, PR reviews, pipeline debugging, dbt model authoring, Streamlit development",
    },
    "claude-sonnet-4-0": {
        "category": ["TIER_2", "TIER_3"],
        "description": "Fast and efficient. Good for straightforward tasks where speed matters more than depth.",
        "popular_for": "SQL formatting, quick fixes, autocomplete, boilerplate generation, documentation",
    },
}

SP_SET_ACCOUNT_CREDIT_LIMIT = "SP_CC_SET_ACCOUNT_CREDIT_LIMIT"
SP_SET_USER_CREDIT_LIMIT = "SP_CC_SET_USER_CREDIT_LIMIT"
SP_UNSET_USER_CREDIT_LIMIT = "SP_CC_UNSET_USER_CREDIT_LIMIT"
SP_GRANT_CORTEX_ACCESS = "SP_CC_GRANT_CORTEX_ACCESS"
SP_REVOKE_CORTEX_ACCESS = "SP_CC_REVOKE_CORTEX_ACCESS"
SP_REBALANCE_CREDITS = "SP_CC_REBALANCE_CREDITS"
# Bulk SPs — avoid O(N) Python round-trips for cohort and grant operations
SP_BULK_GRANT_ACCESS = "SP_CC_BULK_GRANT_ACCESS"
SP_BULK_SET_COHORT_LIMITS = "SP_CC_BULK_SET_COHORT_LIMITS"
# Bridge rebalance SP — server-side EWMA + lock, replaces O(N) Python loop
SP_COMPUTE_REBALANCE = "SP_CC_COMPUTE_REBALANCE"

DATE_PRESETS = {
    "1 Day": 1,
    "7 Days": 7,
    "30 Days": 30,
    "90 Days": 90,
    "365 Days": 365,
}

COMMON_TIMEZONES = [
    ("UTC", "UTC", 0),
    ("Pacific (PT)", "America/Los_Angeles", -8),
    ("Mountain (MT)", "America/Denver", -7),
    ("Central (CT)", "America/Chicago", -6),
    ("Eastern (ET)", "America/New_York", -5),
    ("London (GMT/BST)", "Europe/London", 0),
    ("Paris (CET/CEST)", "Europe/Paris", 1),
    ("India (IST)", "Asia/Kolkata", 5),
    ("Singapore (SGT)", "Asia/Singapore", 8),
    ("Tokyo (JST)", "Asia/Tokyo", 9),
    ("Sydney (AEST)", "Australia/Sydney", 10),
]
DEFAULT_TZ = "UTC"


def get_tz_offset(tz_label: str) -> int:
    """Return UTC offset hours for a given timezone label."""
    for label, _, offset in COMMON_TIMEZONES:
        if label == tz_label:
            return offset
    return 0

REBALANCE_DEFAULT_BUFFER_PCT = 20
REBALANCE_DEFAULT_MAX_TRANSFER_PCT = 50
REBALANCE_DEFAULT_LOOKBACK_DAYS = 14

USAGE_REFRESH_TASK_NAME = "CC_REFRESH_USAGE_SUMMARIES"
RESET_LIMITS_TASK_NAME = "CC_DAILY_RESET_LIMITS"

AUDIT_PREVIEW_LIMIT = 50
USAGE_CACHE_TTL = 300
USER_LIST_CACHE_TTL = 300
CONFIG_CACHE_TTL = 120

PAGE_HOME = "Home"
PAGE_ACCESS_MGMT = "Access Management"
PAGE_CREDIT_CONFIG = "Credit Configuration"
PAGE_USAGE_TRENDS = "Usage Trends"
PAGE_BUDGET_FORECAST = "Budget Forecast"
PAGE_MODEL_ACCESS = "Model Access"
PAGE_CREDIT_REQUESTS = "Credit Requests"
PAGE_SETTINGS = "Settings"
PAGE_AUDIT_LOG = "Audit Log"
PAGE_SETUP = "Setup"

ADMIN_PAGES = [
    PAGE_SETUP,
    PAGE_ACCESS_MGMT,
    PAGE_CREDIT_CONFIG,
    PAGE_USAGE_TRENDS,
    PAGE_BUDGET_FORECAST,
    PAGE_MODEL_ACCESS,
    PAGE_SETTINGS,
    PAGE_AUDIT_LOG,
]
USER_PAGES = [PAGE_HOME, PAGE_CREDIT_REQUESTS]
ALL_PAGES = [PAGE_HOME, PAGE_SETUP, PAGE_ACCESS_MGMT, PAGE_CREDIT_CONFIG,
             PAGE_USAGE_TRENDS, PAGE_BUDGET_FORECAST, PAGE_MODEL_ACCESS,
             PAGE_CREDIT_REQUESTS, PAGE_SETTINGS, PAGE_AUDIT_LOG]

GLOBAL_CSS = """
<style>
/* Dark theme override */
html, body, [class*="css"], .main, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"] {
    font-size: 14px;
    font-family: 'Inter', -apple-system, sans-serif;
    background-color: #0e1117 !important;
    color: #fafafa !important;
}

/* Sidebar dark */
[data-testid="stSidebar"] {
    background: #161b22 !important;
}
[data-testid="stSidebar"] * { color: #e6edf3 !important; }
[data-testid="stSidebar"] .stRadio label { color: #e6edf3 !important; }

/* Typography scale */
h1 { font-size: 1.4rem !important; font-weight: 600 !important; color: #f0f6fc !important; }
h2 { font-size: 1.15rem !important; font-weight: 600 !important; color: #e6edf3 !important; }
h3 { font-size: 1rem !important; font-weight: 500 !important; color: #d2dce6 !important; }

/* Form labels */
.stSelectbox label, .stTextInput label, .stTextArea label,
.stMultiSelect label, .stRadio label, .stCheckbox label,
.stNumberInput label {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #9ca3af !important;
}

/* Metrics - tighter sizing so "Unlimited" doesn't look huge */
[data-testid="stMetricValue"] { font-size: 1.1rem !important; font-weight: 600 !important; color: #f0f6fc !important; }
[data-testid="stMetricLabel"] { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.03em; color: #8b949e !important; }

/* Buttons */
.stButton > button {
    font-size: 0.82rem !important;
    padding: 0.45rem 1rem !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    background-color: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1f6feb, #388bfd) !important;
    border: none !important;
    color: #fff !important;
}
.stButton > button:hover {
    border-color: #58a6ff !important;
}

/* Cards / containers - only show border when explicitly using border=True */
[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 8px !important;
}

/* Expanders */
.streamlit-expanderHeader { font-size: 0.85rem !important; font-weight: 500 !important; color: #e6edf3 !important; }

/* Captions and alerts */
.stCaption { font-size: 0.72rem !important; color: #c9d1d9 !important; }
.stAlert { font-size: 0.82rem !important; border-radius: 6px !important; }

/* Page container */
.block-container { padding-top: 1.5rem !important; max-width: 1200px !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { font-size: 0.82rem !important; font-weight: 500 !important; padding: 0.5rem 1rem !important; color: #8b949e !important; }
.stTabs [aria-selected="true"] { color: #f0f6fc !important; }

/* Data tables */
[data-testid="stDataFrame"] { border-radius: 6px !important; }

/* Progress bars */
[data-testid="stProgress"] > div { border-radius: 4px !important; }

/* Dividers */
hr { border-color: #21262d !important; }

/* Inputs dark */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
.stTextArea textarea {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border-color: #30363d !important;
}

/* Selectbox dropdown */
[data-baseweb="select"] { background-color: #0d1117 !important; }
[data-baseweb="select"] * { color: #e6edf3 !important; }
</style>
"""

_CONFIG_DIR = pathlib.Path(__file__).resolve().parent


def _load_yaml_config() -> Dict[str, Any]:
    path = _CONFIG_DIR / "config.yaml"
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8").lstrip("\ufeff")
        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


_YAML = _load_yaml_config()

DEPLOYMENT_DATABASE: Optional[str] = _YAML.get("deployment", {}).get("database")
DEPLOYMENT_SCHEMA: Optional[str] = _YAML.get("deployment", {}).get("schema")
ADMIN_ROLES_WHITELIST: List[str] = _YAML.get("admin", {}).get("roles", ["ACCOUNTADMIN"])

# Configurable role names — override in config.yaml under roles:
# Defaults to CC_* naming for fresh deployments.
# Accounts with existing roles can point to them instead.
_ROLES_YAML = _YAML.get("roles", {})
ROLE_SP_OWNER = _ROLES_YAML.get("sp_owner",   "CC_SP_OWNER_ROLE")
ROLE_APP      = _ROLES_YAML.get("app_role",   "CC_APP_ROLE")
ROLE_ADMIN    = _ROLES_YAML.get("admin_role", "CC_ADMIN_ROLE")
ROLE_USER     = _ROLES_YAML.get("user_role",  "CC_USER_ROLE")


def get_app_database(session) -> str:
    # 1. Runtime override from sidebar (admin picked a different DB)
    try:
        import streamlit as st
        if "override_db" in st.session_state and st.session_state["override_db"]:
            return st.session_state["override_db"].upper()
    except Exception:
        pass
    # 2. config.yaml
    if DEPLOYMENT_DATABASE:
        return DEPLOYMENT_DATABASE.upper()
    # 3. Current session database
    try:
        return session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
    except Exception:
        return "TEMP"


def get_app_schema(session) -> str:
    # 1. Runtime override from sidebar
    try:
        import streamlit as st
        if "override_schema" in st.session_state and st.session_state["override_schema"]:
            return st.session_state["override_schema"].upper()
    except Exception:
        pass
    # 2. config.yaml
    if DEPLOYMENT_SCHEMA:
        return DEPLOYMENT_SCHEMA.upper()
    # 3. Current session schema
    try:
        return session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
    except Exception:
        return "PUBLIC"


def fq_table(session, table_name: str) -> str:
    return f"{get_app_database(session)}.{get_app_schema(session)}.{table_name}"


def fq_sp(session, sp_name: str) -> str:
    return f"{get_app_database(session)}.{get_app_schema(session)}.{sp_name}"


def sanitize_identifier(identifier: str) -> str:
    """
    Validate a Snowflake identifier (username, role name, database, schema).

    Allows: letters, digits, underscore, dollar, hyphen, dot, at-sign, double-quote.
    These cover all realistic Snowflake identifier characters including:
      - Email-style usernames:  john.doe@company.com
      - Double-underscore roles: CC__DATA_SCIENCE
      - Quoted identifiers with embedded dots or hyphens
      - The `"` character itself (escaped as "" in SQL)

    Does NOT uppercase — caller is responsible for casing to match
    how the identifier was created (quoted identifiers are case-sensitive).
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty")
    if len(identifier) > 255:
        raise ValueError("Identifier too long (max 255)")
    # Block only truly dangerous chars: semicolons, line breaks, null bytes
    if re.search(r'[;\n\r\x00]', identifier):
        raise ValueError(f"Identifier contains disallowed characters: {identifier}")
    return identifier


def sql_identifier(identifier: str) -> str:
    """
    Return a safely double-quoted SQL identifier.
    Escapes embedded double-quotes by doubling them.

    Usage: session.sql(f'ALTER USER {sql_identifier(username)} SET ...')

    This handles: dots, hyphens, spaces, double-quotes, and any other
    characters that are valid in Snowflake quoted identifiers.
    """
    return '"' + identifier.replace('"', '""') + '"'


def escape_sql_literal(value) -> str:
    if value is None:
        return "NULL"
    try:
        import pandas as pd
        if isinstance(value, float) and pd.isna(value):
            return "NULL"
    except ImportError:
        pass
    return str(value).replace("'", "''")


def validate_credit_limit(value) -> int:
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f"Credit limit must be a number, got: {value}")
    if v < -1:
        raise ValueError("Credit limit must be -1 (unlimited), 0 (blocked), or a positive number")
    return v


@st.cache_data(ttl=600, show_spinner=False)
def get_current_user(_session) -> str:
    """Cached — user identity doesn't change within a session."""
    try:
        return _session.sql("SELECT CURRENT_USER()").collect()[0][0]
    except Exception:
        return "UNKNOWN"


@st.cache_data(ttl=600, show_spinner=False)
def get_current_role(_session) -> str:
    """Cached — role doesn't change within a session."""
    try:
        return _session.sql("SELECT CURRENT_ROLE()").collect()[0][0]
    except Exception:
        return "UNKNOWN"


@st.cache_data(ttl=600, show_spinner=False)
def user_is_admin(_session) -> bool:
    try:
        roles_row = _session.sql("SELECT CURRENT_AVAILABLE_ROLES()").collect()[0][0]
        if isinstance(roles_row, str):
            import json
            available = json.loads(roles_row)
        else:
            available = list(roles_row)
        available_upper = [r.upper().strip('"') for r in available]
        for admin_role in ADMIN_ROLES_WHITELIST:
            if admin_role.upper() in available_upper:
                return True
        return False
    except Exception:
        return False

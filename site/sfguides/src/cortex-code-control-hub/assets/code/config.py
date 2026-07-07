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
TABLE_POLICY_RULES = "CC_POLICY_RULES"
TABLE_PROMPT_VIOLATIONS = "CC_PROMPT_VIOLATIONS"
TABLE_PROMPT_ANALYSIS_DAILY = "CC_PROMPT_ANALYSIS_DAILY"
TABLE_PROMPT_EVENTS = "CC_PROMPT_EVENTS"
TABLE_ALERT_CONFIG = "CC_ALERT_CONFIG"
TABLE_ALERT_HISTORY = "CC_ALERT_HISTORY"
TABLE_RESPONSE_QUALITY = "CC_RESPONSE_QUALITY"

# Column names — v1 schema (aligned with Snowflake AI Observability terminology)
COL_ANSWER_RELEVANCE  = "ANSWER_RELEVANCE_SCORE"   # did the LLM answer the query?
COL_GROUNDEDNESS      = "GROUNDEDNESS_SCORE"        # factually grounded, no hallucination
COL_COHERENCE         = "COHERENCE_SCORE"           # logically structured response
COL_SAFETY            = "SAFETY_SCORE"              # free of harmful content
# Token Economics columns on CC_PROMPT_EVENTS
COL_INPUT_TOKENS      = "INPUT_TOKENS"
COL_OUTPUT_TOKENS     = "OUTPUT_TOKENS"
COL_CACHE_READ_TOKENS = "CACHE_READ_TOKENS"
COL_CACHE_WRITE_TOKENS= "CACHE_WRITE_TOKENS"
COL_STEP_NUMBER       = "STEP_NUMBER"
COL_ENTRYPOINT        = "ENTRYPOINT"

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
    # ── Claude Opus — TIER_1 (highest capability) ─────────────────────────────
    "claude-opus-4-5": {
        "category": ["TIER_1"],
        "description": "Deep reasoning with broad context window. Excels at complex analysis requiring synthesis across many inputs.",
        "popular_for": "Data modeling, migration planning, compliance analysis, long-document processing",
    },
    "claude-opus-4-6": {
        "category": ["TIER_1"],
        "description": "Most capable model. Extended thinking with chain-of-thought. Best for architecture reviews, complex debugging, multi-step planning.",
        "popular_for": "System design, security audits, large codebase refactoring, agentic workflows",
    },
    "claude-opus-4-7": {
        "category": ["TIER_1"],
        "description": "Latest Opus generation. Extended reasoning, multi-step agentic tasks, complex architecture design.",
        "popular_for": "Architecture reviews, complex migrations, multi-file refactoring, security analysis",
    },
    "claude-opus-4-8": {
        "category": ["TIER_1"],
        "description": "Latest Opus generation. Extended reasoning and deep analysis for complex enterprise tasks.",
        "popular_for": "System design, compliance analysis, large codebase refactoring, agentic workflows",
    },
    # ── Claude Sonnet — TIER_1/TIER_2 (balanced) ─────────────────────────────
    "claude-sonnet-4-0": {
        "category": ["TIER_2", "TIER_3"],
        "description": "Fast and efficient. Good for straightforward tasks where speed matters more than depth.",
        "popular_for": "SQL formatting, quick fixes, autocomplete, boilerplate generation, documentation",
    },
    "claude-sonnet-4-5": {
        "category": ["TIER_1", "TIER_2"],
        "description": "High quality with fast response. Best balance of capability and speed for iterative development.",
        "popular_for": "Code generation, PR reviews, pipeline debugging, dbt model authoring, Streamlit development",
    },
    "claude-sonnet-4-6": {
        "category": ["TIER_1", "TIER_2"],
        "description": "Latest Sonnet generation. High quality responses with fast latency for iterative workflows.",
        "popular_for": "Code generation, PR reviews, data pipeline development, API integrations",
    },
    "claude-4-sonnet": {
        "category": ["TIER_1", "TIER_2"],
        "description": "Claude Sonnet — balanced capability and speed for general development tasks.",
        "popular_for": "Code generation, code review, debugging, documentation",
    },
    # ── OpenAI GPT ── TIER_1/TIER_2 ─────────────────────────────────────────
    "openai-gpt-5.2": {
        "category": ["TIER_1", "TIER_2"],
        "description": "OpenAI GPT-5 series. Strong general-purpose reasoning and code generation.",
        "popular_for": "Code generation, analysis, documentation, general development tasks",
    },
    "openai-gpt-5.4": {
        "category": ["TIER_1", "TIER_2"],
        "description": "OpenAI GPT-5 series. Strong reasoning with broad knowledge for enterprise tasks.",
        "popular_for": "Code generation, analysis, SQL authoring, documentation",
    },
    "openai-gpt-5.5": {
        "category": ["TIER_1"],
        "description": "Latest OpenAI GPT-5 series. Highest capability for complex enterprise reasoning.",
        "popular_for": "Architecture design, complex debugging, multi-step analysis, agentic workflows",
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
SP_ENFORCE_MODEL_ACCESS = "SP_CC_ENFORCE_MODEL_ACCESS"
SP_REVOKE_MODEL_ACCESS  = "SP_CC_REVOKE_MODEL_ACCESS"
# Bridge rebalance SP — server-side EWMA + lock, replaces O(N) Python loop
SP_COMPUTE_REBALANCE = "SP_CC_COMPUTE_REBALANCE"
# Alerting + quality evaluation SPs
SP_CHECK_ALERTS = "SP_CC_CHECK_ALERTS"
SP_EVALUATE_RESPONSES = "SP_CC_EVALUATE_RESPONSES"

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
PAGE_MODEL_ACCESS = "Model Access"
PAGE_CREDIT_REQUESTS = "Credit Requests"
PAGE_SETTINGS = "Settings"
PAGE_AUDIT_LOG = "Audit Log"
PAGE_SETUP = "Setup"
PAGE_OBSERVABILITY = "AI Observability"
PAGE_COST_ATTRIBUTION = "Cost Attribution"
PAGE_PROMPT_ANALYSIS = "Prompt Insights"
PAGE_USER_INTEL = "User Intelligence"
PAGE_POLICY_RULES = "Policy Rules"
PAGE_ALERTS = "Alerts"
PAGE_MODEL_INTEL = "Model Intelligence"

ADMIN_PAGES = [
    PAGE_SETUP,
    PAGE_ACCESS_MGMT,
    PAGE_CREDIT_CONFIG,
    PAGE_USAGE_TRENDS,
    PAGE_MODEL_ACCESS,
    PAGE_MODEL_INTEL,
    PAGE_SETTINGS,
    PAGE_AUDIT_LOG,
    PAGE_OBSERVABILITY,
    PAGE_COST_ATTRIBUTION,
    PAGE_PROMPT_ANALYSIS,
    PAGE_USER_INTEL,
    PAGE_POLICY_RULES,
    PAGE_ALERTS,
]

USER_PAGES = [PAGE_HOME, PAGE_CREDIT_REQUESTS]
ALL_PAGES = [
    PAGE_HOME,
    PAGE_SETUP, PAGE_SETTINGS, PAGE_AUDIT_LOG,
    PAGE_ACCESS_MGMT, PAGE_CREDIT_CONFIG, PAGE_MODEL_ACCESS, PAGE_CREDIT_REQUESTS,
    PAGE_USAGE_TRENDS, PAGE_COST_ATTRIBUTION,
    PAGE_OBSERVABILITY, PAGE_USER_INTEL,
    PAGE_PROMPT_ANALYSIS, PAGE_POLICY_RULES, PAGE_ALERTS,
    PAGE_MODEL_INTEL,
]

GLOBAL_CSS = """
<style>
/* ── Base — aggressive dark override for all Streamlit/enterprise accounts ── */
html, body, .stApp,
[class*="css"], .main,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMainBlockContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"],
.stMainBlockContainer, .main > div,
section[data-testid="stSidebar"] ~ section {
    font-size: 14px;
    font-family: 'Inter', -apple-system, sans-serif;
    background-color: #0e1117 !important;
    color: #e5e7eb !important;
}

/* ── All form elements — force dark background explicitly ────────────────── */
[data-baseweb="input"],
[data-baseweb="input"] > div,
[data-baseweb="base-input"],
[data-baseweb="select"],
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div,
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stNumberInput"] > div > div,
[data-testid="stTextArea"] > div > div,
[data-baseweb="textarea"],
input, textarea {
    background-color: #111827 !important;
    color: #e5e7eb !important;
    border-color: #374151 !important;
}

/* Selected value text inside a select box */
[data-baseweb="select"] [class*="singleValue"],
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #e5e7eb !important;
    background-color: transparent !important;
}

/* Placeholder text */
[data-baseweb="select"] [class*="placeholder"],
input::placeholder, textarea::placeholder {
    color: #6b7280 !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%) !important;
    border-right: 1px solid #1f2937 !important;
    min-width: 240px !important;
    max-width: 240px !important;
    width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child {
    min-width: 240px !important;
    max-width: 240px !important;
    width: 240px !important;
}
/* Hide the collapse/expand toggle — prevents sidebar disappearing accidentally
   and in Snowflake reader mode where the toggle may auto-collapse it */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarUserContent"] + div button,
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
.st-emotion-cache-1dp5vir,
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}
[data-testid="stSidebar"] * { color: #d1d5db !important; }

/* Nav labels */
[data-testid="stSidebar"] .stRadio label span p,
[data-testid="stSidebar"] .stRadio label div p {
    font-size: 0.9rem !important;
    letter-spacing: 0.005em !important;
    font-weight: 600 !important;
    color: #f0f6fc !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 0.28rem 0.4rem !important;
    border-radius: 4px !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] caption {
    font-size: 0.78rem !important;
    color: #6b7280 !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stMarkdownContainer p {
    font-size: 0.83rem !important;
    color: #9ca3af !important;
}

/* ── Typography ──────────────────────────────────────────────────────────── */
h1 { font-size: 1.45rem !important; font-weight: 700 !important; color: #f9fafb !important; letter-spacing: -0.02em; }
h2 { font-size: 1.2rem  !important; font-weight: 600 !important; color: #e5e7eb !important; }
h3 { font-size: 1.05rem !important; font-weight: 500 !important; color: #d1d5db !important; }

/* ── Form labels ─────────────────────────────────────────────────────────── */
.stSelectbox label, .stTextInput label, .stTextArea label,
.stMultiSelect label, .stRadio > label, .stCheckbox label,
.stNumberInput label {
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    color: #9ca3af !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* ── Metrics ─────────────────────────────────────────────────────────────── */
[data-testid="stMetricValue"]  { font-size: 1.4rem !important; font-weight: 700 !important; color: #f9fafb !important; }
[data-testid="stMetricLabel"]  { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280 !important; }
[data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button {
    font-size: 0.85rem !important;
    padding: 0.4rem 0.9rem !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    background-color: #1f2937 !important;
    color: #d1d5db !important;
    border: 1px solid #374151 !important;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background-color: #374151 !important;
    border-color: #4b5563 !important;
    color: #f9fafb !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.4);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid #1f2937; }
.stTabs [data-baseweb="tab"] {
    font-size: 0.85rem !important; font-weight: 500 !important;
    padding: 0.5rem 1rem !important; color: #6b7280 !important;
    border-radius: 6px 6px 0 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #f9fafb !important;
    background: #1f2937 !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* ── Cards / containers ──────────────────────────────────────────────────── */
[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 8px !important;
    border-color: #1f2937 !important;
    background: #111827 !important;
}

/* ── Expanders ───────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-size: 0.88rem !important; font-weight: 500 !important;
    color: #d1d5db !important; background: #111827 !important;
    border-radius: 6px !important;
}

/* ── Text / captions ─────────────────────────────────────────────────────── */
.stCaption { font-size: 0.75rem !important; color: #6b7280 !important; }
.stAlert   { font-size: 0.85rem !important; border-radius: 6px !important; }
.stMarkdownContainer p { font-size: 0.88rem; line-height: 1.6; font-weight: 400; color: #e5e7eb; }

/* ── Main content horizontal radio (section nav) — match sidebar feel ─────── */
[data-testid="stMainBlockContainer"] .stRadio label span p,
[data-testid="stMainBlockContainer"] .stRadio label div p {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #d1d5db !important;
}

/* ── Layout ──────────────────────────────────────────────────────────────── */
.block-container { padding-top: 1.2rem !important; max-width: 1280px !important; }
hr { border-color: #1f2937 !important; margin: 0.8rem 0 !important; }

/* ── Inputs ──────────────────────────────────────────────────────────────── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
.stTextArea textarea {
    background-color: #111827 !important;
    color: #e5e7eb !important;
    border-color: #374151 !important;
    font-size: 0.88rem !important;
}
/* Select font size (background/color handled in base block above) */
[data-baseweb="select"] * { font-size: 0.88rem !important; }

/* ── Dropdown popup portal (renders outside main container) ──────────────── */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-baseweb="menu-list"] {
    background-color: #111827 !important;
    border: 1px solid #374151 !important;
    border-radius: 6px !important;
}
[data-baseweb="option"] {
    background-color: #111827 !important;
    color: #e5e7eb !important;
}
[data-baseweb="option"]:hover,
[data-baseweb="option"][aria-selected="true"] {
    background-color: #1f2937 !important;
    color: #f9fafb !important;
}
/* Multiselect tags */
[data-baseweb="tag"] {
    background-color: #1f2937 !important;
    color: #d1d5db !important;
}

/* ── Tables ──────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 6px !important; font-size: 0.83rem !important; }

/* ── Progress ────────────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div { border-radius: 4px !important; }

/* ── Status indicator chips ──────────────────────────────────────────────── */
.coco-chip {
    display: inline-block; padding: 0.18rem 0.6rem;
    border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    margin: 0.1rem 0.15rem; vertical-align: middle;
}
.chip-green { background: rgba(34,197,94,0.15); color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
.chip-blue  { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }
.chip-amber { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.chip-red   { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.chip-gray  { background: rgba(107,114,128,0.15); color: #9ca3af; border: 1px solid rgba(107,114,128,0.3); }

/* ── Section cards ───────────────────────────────────────────────────────── */
.coco-section {
    background: linear-gradient(90deg, rgba(59,130,246,0.08) 0%, rgba(59,130,246,0.03) 100%);
    border-left: 3px solid #3b82f6; border-radius: 0 6px 6px 0;
    padding: 0.4rem 0.75rem; margin: 0.6rem 0 0.5rem 0;
}
.coco-section h4 { margin: 0; font-size: 0.88rem; font-weight: 600; color: #60a5fa; }
.coco-section-amber {
    background: linear-gradient(90deg, rgba(245,158,11,0.08) 0%, rgba(245,158,11,0.03) 100%);
    border-left: 3px solid #f59e0b; border-radius: 0 6px 6px 0;
    padding: 0.4rem 0.75rem; margin: 0.6rem 0 0.5rem 0;
}
.coco-section-amber h4 { margin: 0; font-size: 0.88rem; font-weight: 600; color: #fbbf24; }
.coco-section-green {
    background: linear-gradient(90deg, rgba(34,197,94,0.08) 0%, rgba(34,197,94,0.03) 100%);
    border-left: 3px solid #22c55e; border-radius: 0 6px 6px 0;
    padding: 0.4rem 0.75rem; margin: 0.6rem 0 0.5rem 0;
}
.coco-section-green h4 { margin: 0; font-size: 0.88rem; font-weight: 600; color: #4ade80; }

/* ── Stat row ────────────────────────────────────────────────────────────── */
.coco-stat-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
.coco-stat { background: #111827; border: 1px solid #1f2937; border-radius: 8px;
             padding: 0.6rem 1rem; min-width: 120px; flex: 1; }
.coco-stat .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; }
.coco-stat .value { font-size: 1.2rem; font-weight: 700; color: #f9fafb; margin-top: 0.15rem; }
.coco-stat .delta { font-size: 0.73rem; margin-top: 0.1rem; }
.coco-stat .delta-pos { color: #22c55e; }
.coco-stat .delta-neg { color: #f87171; }
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
    """Cached — user identity doesn't change within a session.
    Uses st.user.user_name when running on SPCS container runtime
    (where CURRENT_USER() returns the internal service account).
    Falls back to CURRENT_USER() for warehouse-based SiS.
    """
    try:
        import streamlit as st
        user = getattr(st, 'user', None)
        if user and hasattr(user, 'user_name') and user.user_name:
            name = user.user_name
            # Ignore internal SPCS service accounts (STPLAT* pattern)
            if not str(name).upper().startswith('STPLAT'):
                return str(name).upper()
    except Exception:
        pass
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

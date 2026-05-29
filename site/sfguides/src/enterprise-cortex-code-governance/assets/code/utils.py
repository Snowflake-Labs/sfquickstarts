"""
Cortex Code Credit Manager - Utilities & Data Access
======================================================
Snowflake helpers, cached data access, pre-aggregated table queries.
All read queries go through here. Write operations go through SPs or audit.py.
"""

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from config import (
    CONFIG_CACHE_TTL,
    SURFACE_PARAMS,
    SURFACE_USAGE_VIEWS,
    TABLE_APP_CONFIG,
    TABLE_AUDIT_LOG,
    TABLE_CREDIT_CONFIG,
    TABLE_CREDIT_REQUESTS,
    TABLE_USAGE_DAILY,
    TABLE_USAGE_HOURLY,
    USAGE_CACHE_TTL,
    USER_LIST_CACHE_TTL,
    escape_sql_literal,
    fq_sp,
    fq_table,
    sanitize_identifier,
)


@st.cache_resource
def get_session():
    from snowflake.snowpark.context import get_active_session
    return get_active_session()


@st.cache_data(ttl=USER_LIST_CACHE_TTL)
def list_users(_session) -> pd.DataFrame:
    sql = """
        SELECT NAME, LOGIN_NAME, DISPLAY_NAME, EMAIL, DEFAULT_ROLE,
               DISABLED, CREATED_ON, LAST_SUCCESS_LOGIN
        FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
        WHERE DELETED_ON IS NULL
        ORDER BY NAME
    """
    try:
        return _session.sql(sql).to_pandas()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=USER_LIST_CACHE_TTL)
def list_roles(_session) -> List[str]:
    try:
        df = _session.sql("""
            SELECT NAME FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES
            WHERE DELETED_ON IS NULL
            ORDER BY NAME
        """).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            return df["NAME"].dropna().tolist()
        return []
    except Exception:
        # Fallback to SHOW ROLES if ACCOUNT_USAGE not accessible
        try:
            df = _session.sql("SHOW ROLES").to_pandas()
            if not df.empty:
                df.columns = [c.strip('"').upper() for c in df.columns]
                col = "NAME" if "NAME" in df.columns else df.columns[1]
                return sorted(df[col].dropna().tolist())
            return []
        except Exception:
            return []


@st.cache_data(ttl=USER_LIST_CACHE_TTL)
def get_role_members(_session, role_name: str) -> List[str]:
    safe_role = sanitize_identifier(role_name)
    try:
        df = _session.sql(f'SHOW GRANTS OF ROLE "{safe_role}"').to_pandas()
        if df.empty:
            return []
        df.columns = [c.strip('"').upper() for c in df.columns]
        if "GRANTED_TO" in df.columns and "GRANTEE_NAME" in df.columns:
            user_grants = df[df["GRANTED_TO"].str.upper() == "USER"]
            names = user_grants["GRANTEE_NAME"].dropna().unique().tolist()
            # Filter out UUID-style managed accounts (OAuth, Cortex Code sessions,
            # SPCS, etc.) and known service account prefixes.
            # These appear in GRANTS but not in SHOW USERS — they're not humans.
            import re
            _UUID = re.compile(r"^[0-9a-fA-F]{8}-", re.IGNORECASE)
            _SVC  = re.compile(r"^(SVC_|MANAGED_|SYSTEM\$|APP_|SNOWFLAKE)", re.IGNORECASE)
            names = [n for n in names if n and not _UUID.match(n) and not _SVC.match(n)]
            return sorted(names)
        return []
    except Exception:
        return []


def get_account_param(_session, param_name: str) -> Optional[str]:
    try:
        safe_param = escape_sql_literal(param_name)
        df = _session.sql(
            f"SHOW PARAMETERS LIKE '{safe_param}' IN ACCOUNT"
        ).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            if "VALUE" in df.columns:
                return df["VALUE"].iloc[0]
    except Exception:
        pass
    return None


def get_user_param(_session, username: str, param_name: str) -> Tuple[Optional[str], str]:
    safe_user = sanitize_identifier(username)
    safe_param = escape_sql_literal(param_name)
    try:
        df = _session.sql(
            f'SHOW PARAMETERS LIKE \'{safe_param}\' IN USER "{safe_user}"'
        ).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            val = df["VALUE"].iloc[0] if "VALUE" in df.columns else None
            level = df["LEVEL"].iloc[0] if "LEVEL" in df.columns else "DEFAULT"
            return val, level
    except Exception:
        pass
    return None, "ERROR"


@st.cache_data(ttl=CONFIG_CACHE_TTL)
def get_credit_configs(_session) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_CREDIT_CONFIG)
    try:
        return _session.sql(
            f"SELECT * FROM {tbl} WHERE IS_ACTIVE = TRUE ORDER BY CONFIG_TYPE, ROLE_NAME, USER_NAME"
        ).to_pandas()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=CONFIG_CACHE_TTL)
def get_cohort_config(_session, role_name: str) -> Optional[Dict[str, Any]]:
    tbl = fq_table(_session, TABLE_CREDIT_CONFIG)
    safe_role = escape_sql_literal(role_name)
    try:
        rows = _session.sql(
            f"SELECT * FROM {tbl} WHERE CONFIG_TYPE = 'COHORT' "
            f"AND ROLE_NAME = '{safe_role}' AND IS_ACTIVE = TRUE LIMIT 1"
        ).collect()
        if rows:
            return rows[0].as_dict()
    except Exception:
        pass
    return None


def get_app_setting(_session, key: str, default: str = "") -> str:
    tbl = fq_table(_session, TABLE_APP_CONFIG)
    safe_key = escape_sql_literal(key)
    try:
        rows = _session.sql(
            f"SELECT CONFIG_VALUE FROM {tbl} WHERE CONFIG_KEY = '{safe_key}' LIMIT 1"
        ).collect()
        if rows:
            return rows[0]["CONFIG_VALUE"]
    except Exception:
        pass
    return default


def get_tier_config(_session) -> dict:
    """
    Load tier definitions from CC_APP_CONFIG['TIER_CONFIG'].
    Falls back to MODEL_CATEGORIES from config.py if not yet persisted.
    Returns: {tier_name: {description, tokens_per_credit, best_for}, ...}
    """
    from config import MODEL_CATEGORIES
    raw = get_app_setting(_session, "TIER_CONFIG", "")
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict) and loaded:
                return loaded
        except (json.JSONDecodeError, TypeError):
            pass
    # Fallback: hardcoded defaults
    return {k: dict(v) for k, v in MODEL_CATEGORIES.items()}


def save_tier_config(_session, tiers: dict, actor: str) -> bool:
    """Persist tier definitions to CC_APP_CONFIG['TIER_CONFIG'] as JSON."""
    return set_app_setting(_session, "TIER_CONFIG", json.dumps(tiers), actor)


def get_model_tier_assignments(_session) -> dict:
    """
    Load model→tier assignments from CC_MODEL_CONFIG.
    Falls back to KNOWN_MODELS from config.py if table is empty.
    Returns: {model_name: [tier1, tier2, ...], ...}
    """
    from config import KNOWN_MODELS, TABLE_MODEL_CONFIG, fq_table
    tbl = fq_table(_session, TABLE_MODEL_CONFIG)
    try:
        df = _session.sql(
            f"SELECT MODEL_NAME, CATEGORY FROM {tbl} WHERE MODEL_NAME IS NOT NULL"
        ).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            result = {}
            for _, row in df.iterrows():
                name = row["MODEL_NAME"]
                cat = row["CATEGORY"]
                # CATEGORY may be stored as comma-separated or as a single tier
                if cat and "," in str(cat):
                    result[name] = [t.strip() for t in str(cat).split(",")]
                elif cat:
                    result[name] = [str(cat).strip()]
                else:
                    result[name] = []
            return result
    except Exception:
        pass
    # Fallback: config defaults
    return {k: (v["category"] if isinstance(v["category"], list) else [v["category"]])
            for k, v in KNOWN_MODELS.items()}


def save_model_tier_assignment(_session, model_name: str, tiers: list, actor: str) -> bool:
    """
    Persist a model's tier assignment(s) to CC_MODEL_CONFIG.
    Upserts the row for model_name with CATEGORY = comma-joined tiers.
    """
    from config import TABLE_MODEL_CONFIG, fq_table, escape_sql_literal
    tbl = fq_table(_session, TABLE_MODEL_CONFIG)
    safe_model = escape_sql_literal(model_name)
    safe_tier = escape_sql_literal(",".join(tiers))
    safe_actor = escape_sql_literal(actor)
    try:
        _session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT '{safe_model}' AS M) s ON t.MODEL_NAME = s.M
            WHEN MATCHED THEN UPDATE SET
                CATEGORY = '{safe_tier}', CREATED_BY = '{safe_actor}',
                CREATED_AT = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT (MODEL_NAME, CATEGORY, CREATED_BY, CREATED_AT)
                VALUES ('{safe_model}', '{safe_tier}', '{safe_actor}', CURRENT_TIMESTAMP())
        """).collect()
        return True
    except Exception:
        return False


def set_app_setting(_session, key: str, value: str, actor: str) -> bool:
    tbl = fq_table(_session, TABLE_APP_CONFIG)
    safe_key = escape_sql_literal(key)
    safe_val = escape_sql_literal(value)
    safe_actor = escape_sql_literal(actor)
    try:
        _session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT '{safe_key}' AS K) s ON t.CONFIG_KEY = s.K
            WHEN MATCHED THEN UPDATE SET
                CONFIG_VALUE = '{safe_val}',
                UPDATED_BY = '{safe_actor}',
                UPDATED_AT = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT
                (CONFIG_KEY, CONFIG_VALUE, UPDATED_BY, UPDATED_AT)
            VALUES ('{safe_key}', '{safe_val}', '{safe_actor}', CURRENT_TIMESTAMP())
        """).collect()
        return True
    except Exception:
        return False


@st.cache_data(ttl=USAGE_CACHE_TTL)
def get_daily_usage(_session, days: int = 30, cohort_role: Optional[str] = None,
                    user_name: Optional[str] = None) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    where = f"WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())"
    if cohort_role:
        where += f" AND COHORT_ROLE = '{escape_sql_literal(cohort_role)}'"
    if user_name:
        where += f" AND USER_NAME = '{escape_sql_literal(user_name)}'"
    try:
        return _session.sql(
            f"SELECT * FROM {tbl} {where} ORDER BY USAGE_DATE, USER_NAME"
        ).to_pandas()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=USAGE_CACHE_TTL)
def get_hourly_usage(_session, days: int = 14, cohort_role: Optional[str] = None,
                     user_name: Optional[str] = None) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_USAGE_HOURLY)
    where = f"WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())"
    if cohort_role:
        where += f" AND COHORT_ROLE = '{escape_sql_literal(cohort_role)}'"
    if user_name:
        where += f" AND USER_NAME = '{escape_sql_literal(user_name)}'"
    try:
        return _session.sql(
            f"SELECT * FROM {tbl} {where} ORDER BY USAGE_DATE, USAGE_HOUR, USER_NAME"
        ).to_pandas()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=USAGE_CACHE_TTL)
def get_usage_summary_metrics(_session, days: int = 30,
                              cohort_role: Optional[str] = None) -> Dict[str, Any]:
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    where = f"WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())"
    if cohort_role:
        where += f" AND COHORT_ROLE = '{escape_sql_literal(cohort_role)}'"
    try:
        rows = _session.sql(f"""
            SELECT
                COALESCE(SUM(TOTAL_CREDITS), 0) AS TOTAL_CREDITS,
                COUNT(DISTINCT USER_NAME) AS ACTIVE_USERS,
                COALESCE(SUM(QUERY_COUNT), 0) AS TOTAL_REQUESTS,
                COALESCE(SUM(TOTAL_TOKENS), 0) AS TOTAL_TOKENS
            FROM {tbl} {where}
        """).collect()
        if rows:
            r = rows[0]
            total_cr = float(r["TOTAL_CREDITS"] or 0)
            active = int(r["ACTIVE_USERS"] or 0)
            return {
                "total_credits": total_cr,
                "active_users": active,
                "avg_per_user": round(total_cr / active, 2) if active else 0,
                "total_requests": int(r["TOTAL_REQUESTS"] or 0),
                "total_tokens": int(r["TOTAL_TOKENS"] or 0),
            }
    except Exception:
        pass
    return {"total_credits": 0, "active_users": 0, "avg_per_user": 0,
            "total_requests": 0, "total_tokens": 0}


@st.cache_data(ttl=USAGE_CACHE_TTL)
def get_model_breakdown(_session, days: int = 30,
                        cohort_role: Optional[str] = None) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    where = f"WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())"
    if cohort_role:
        where += f" AND COHORT_ROLE = '{escape_sql_literal(cohort_role)}'"
    try:
        return _session.sql(f"""
            SELECT MODEL_NAME,
                   SUM(TOTAL_CREDITS) AS CREDITS,
                   SUM(TOTAL_TOKENS) AS TOKENS,
                   SUM(QUERY_COUNT) AS REQUESTS
            FROM {tbl} {where}
            GROUP BY MODEL_NAME
            ORDER BY CREDITS DESC
        """).to_pandas()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=USAGE_CACHE_TTL)
def get_top_users(_session, days: int = 30, cohort_role: Optional[str] = None,
                  limit: int = 20) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    where = f"WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())"
    if cohort_role:
        where += f" AND COHORT_ROLE = '{escape_sql_literal(cohort_role)}'"
    try:
        return _session.sql(f"""
            SELECT USER_NAME,
                   SUM(TOTAL_CREDITS) AS CREDITS,
                   SUM(TOTAL_TOKENS) AS TOKENS,
                   SUM(QUERY_COUNT) AS REQUESTS
            FROM {tbl} {where}
            GROUP BY USER_NAME
            ORDER BY CREDITS DESC
            LIMIT {int(limit)}
        """).to_pandas()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=USAGE_CACHE_TTL)
def get_daily_trend(_session, days: int = 30,
                    cohort_role: Optional[str] = None) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    where = f"WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())"
    if cohort_role:
        where += f" AND COHORT_ROLE = '{escape_sql_literal(cohort_role)}'"
    try:
        return _session.sql(f"""
            SELECT USAGE_DATE, SURFACE,
                   SUM(TOTAL_CREDITS) AS CREDITS,
                   COUNT(DISTINCT USER_NAME) AS USERS,
                   SUM(QUERY_COUNT) AS REQUESTS
            FROM {tbl} {where}
            GROUP BY USAGE_DATE, SURFACE
            ORDER BY USAGE_DATE
        """).to_pandas()
    except Exception:
        return pd.DataFrame()


def get_pending_requests(_session) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_CREDIT_REQUESTS)
    try:
        return _session.sql(
            f"SELECT * FROM {tbl} WHERE STATUS = 'PENDING' ORDER BY REQUEST_TIMESTAMP"
        ).to_pandas()
    except Exception:
        return pd.DataFrame()


def get_user_requests(_session, username: str) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_CREDIT_REQUESTS)
    safe_user = escape_sql_literal(username)
    try:
        return _session.sql(
            f"SELECT * FROM {tbl} WHERE REQUESTER = '{safe_user}' "
            f"ORDER BY REQUEST_TIMESTAMP DESC LIMIT 20"
        ).to_pandas()
    except Exception:
        return pd.DataFrame()


def get_audit_logs(_session, days: int = 7, action_type: Optional[str] = None,
                   limit: int = 100) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_AUDIT_LOG)
    where = f"WHERE TIMESTAMP >= DATEADD('day', -{int(days)}, CURRENT_TIMESTAMP())"
    if action_type:
        where += f" AND ACTION_TYPE = '{escape_sql_literal(action_type)}'"
    try:
        return _session.sql(
            f"SELECT * FROM {tbl} {where} ORDER BY TIMESTAMP DESC LIMIT {int(limit)}"
        ).to_pandas()
    except Exception:
        return pd.DataFrame()


def get_user_today_usage(_session, username: str) -> Dict[str, float]:
    from config import SURFACES
    result = {s: 0.0 for s in SURFACES}
    tbl = fq_table(_session, TABLE_USAGE_HOURLY)
    safe_user = escape_sql_literal(username)
    try:
        rows = _session.sql(f"""
            SELECT SURFACE, SUM(TOTAL_CREDITS) AS CR
            FROM {tbl}
            WHERE USAGE_DATE = CURRENT_DATE()
              AND USER_NAME = '{safe_user}'
            GROUP BY SURFACE
        """).collect()
        for r in rows:
            surf = r["SURFACE"]
            if surf in result:
                result[surf] = float(r["CR"] or 0)
    except Exception:
        pass
    return result


def call_sp(_session, sp_name: str, *args) -> Tuple[bool, str]:
    fq = fq_sp(_session, sp_name)
    arg_list = ", ".join([f"'{escape_sql_literal(str(a))}'" for a in args])
    try:
        rows = _session.sql(f"CALL {fq}({arg_list})").collect()
        msg = str(rows[0][0]) if rows else "OK"
        if msg.upper().startswith("ERROR"):
            return False, msg
        return True, msg
    except Exception as e:
        return False, str(e)


def call_bulk_sp(_session, sp_name: str, *args) -> Tuple[bool, str]:
    """
    Call a SP that accepts VARIANT (JSON array/object) and scalar args.
    - list/dict args → PARSE_JSON('...json...')
    - bool args → TRUE / FALSE
    - int/float args → numeric literal
    - None → NULL
    - str → escaped string literal
    Returns (success, message_or_json_str).
    The message is the raw SP return value; parse JSON for {"success":N,...} results.
    """
    fq = fq_sp(_session, sp_name)
    parts = []
    for arg in args:
        if isinstance(arg, (list, dict)):
            safe = escape_sql_literal(json.dumps(arg))
            parts.append(f"PARSE_JSON('{safe}')")
        elif isinstance(arg, bool):
            parts.append("TRUE" if arg else "FALSE")
        elif isinstance(arg, (int, float)) and not isinstance(arg, bool):
            parts.append(str(arg))
        elif arg is None:
            parts.append("NULL")
        else:
            parts.append(f"'{escape_sql_literal(str(arg))}'")

    sql = f"CALL {fq}({', '.join(parts)})"
    try:
        rows = _session.sql(sql).collect()
        raw = str(rows[0][0]) if rows else "OK"
        # If the SP returned a JSON result dict, interpret success/failure from it
        try:
            result = json.loads(raw)
            if isinstance(result, dict) and "failed" in result:
                failed = result.get("failed", 0)
                return (failed == 0), raw
        except (json.JSONDecodeError, TypeError):
            pass
        if raw.upper().startswith("ERROR"):
            return False, raw
        return True, raw
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def get_database_list(_session) -> List[str]:
    """Cached SHOW DATABASES — used by sidebar deployment picker."""
    try:
        df = _session.sql("SHOW DATABASES").to_pandas()
        df.columns = [c.strip('"').upper() for c in df.columns]
        return df["NAME"].tolist() if "NAME" in df.columns else []
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def search_users(_session, query: str, limit: int = 50) -> List[str]:
    """
    Server-side user search — never loads all 50K users into Python.
    Searches NAME, LOGIN_NAME, and EMAIL with ILIKE.
    Minimum 2 characters required (enforced in callers).
    Filters out service/system accounts automatically.
    """
    safe_q = escape_sql_literal(query.upper().strip())
    try:
        df = _session.sql(f"""
            SELECT NAME
            FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
            WHERE DELETED_ON IS NULL
              AND (
                  UPPER(NAME)       LIKE '%{safe_q}%'
                  OR UPPER(LOGIN_NAME) LIKE '%{safe_q}%'
                  OR UPPER(EMAIL)      LIKE '%{safe_q}%'
              )
              AND NAME NOT RLIKE '^[0-9a-fA-F]{{8}}-'
              AND NAME NOT RLIKE '^(SVC_|MANAGED_|SYSTEM\\$|APP_)'
            ORDER BY NAME
            LIMIT {int(limit)}
        """).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            return df["NAME"].dropna().tolist()
    except Exception:
        pass
    return []

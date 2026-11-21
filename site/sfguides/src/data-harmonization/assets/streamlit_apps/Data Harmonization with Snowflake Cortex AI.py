import json
import os
from typing import Any, Dict, List, Optional, Tuple
import datetime

import pandas as pd
import streamlit as st


try:
    import snowflake.connector as sf
except Exception:  # pragma: no cover
    sf = None  # Streamlit UI will warn if connector is missing

try:
    from snowflake.snowpark.context import get_active_session as sp_get_active_session  # type: ignore
except Exception:
    sp_get_active_session = None  # Not running inside Snowflake Python runtime


###############################################################################
# Streamlit Page Config
###############################################################################
st.set_page_config(
    page_title="Snowflake Data Harmonization",
    page_icon=None,
    layout="wide",
)

st.markdown(
    """
    <div class="sf-page-header">
      <h1>Data Harmonization with Snowflake Cortex AI</h1>
      <p>Select two source tables, analyze and get AI recommendations for semantic mappings, edit as needed, and load a harmonized table.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Global Styling: Snowflake blue background, text coloring, and card components
st.markdown(
    """
    <style>
      /* App background */
      [data-testid="stAppViewContainer"] {
        background: #29B5E8;
      }

      /* Default text color for non-bold text */
      [data-testid="stAppViewContainer"] p,
      [data-testid="stAppViewContainer"] span,
      [data-testid="stAppViewContainer"] label,
      [data-testid="stAppViewContainer"] div,
      [data-testid="stAppViewContainer"] li,
      [data-testid="stAppViewContainer"] h1,
      [data-testid="stAppViewContainer"] h2,
      [data-testid="stAppViewContainer"] h3,
      [data-testid="stAppViewContainer"] h4,
      [data-testid="stAppViewContainer"] h5,
      [data-testid="stAppViewContainer"] h6 {
        color: #333333;
      }

      /* Page header (title + caption) */
      .sf-page-header h1 { color: #FFFFFF; margin-bottom: 6px; font-weight: 800; }
      .sf-page-header p { color: #FFFFFF; opacity: 0.95; margin-top: 0; }

      /* Bold/strong text is white */
      [data-testid="stAppViewContainer"] strong,
      [data-testid="stAppViewContainer"] b {
        color: #FFFFFF !important;
      }

      /* Card styling */
      .sf-card {
        background: #F0F2F6 !important; /* match sidebar gray */
        border: 2px dotted #29B5E8;
        border-radius: 12px;
        padding: 18px 20px;
        margin: 16px 0;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
      }

      .sf-card-title {
        margin: 0 0 12px 0;
        font-size: 1.2rem;
        font-weight: 700;
        color: #333333;
      }

      /* Buttons - subtle tweak to fit theme */
      div.stButton > button[kind="primary"], div.stButton > button {
        border-radius: 8px;
      }
      /* Primary (blue) buttons: bold, white text */
      div.stButton > button[kind="primary"],
      div.stButton > button[data-testid="baseButton-primary"],
      button[kind="primary"],
      button[data-testid="baseButton-primary"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }
      /* Ensure inner spans/icons inherit */
      div.stButton > button[kind="primary"] *,
      div.stButton > button[data-testid="baseButton-primary"] *,
      button[kind="primary"] *,
      button[data-testid="baseButton-primary"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }
      /* Hover/active states */
      div.stButton > button[kind="primary"]:hover,
      div.stButton > button[data-testid="baseButton-primary"]:hover,
      button[kind="primary"]:hover,
      button[data-testid="baseButton-primary"]:hover,
      div.stButton > button[kind="primary"]:focus,
      div.stButton > button[data-testid="baseButton-primary"]:focus,
      button[kind="primary"]:focus,
      button[data-testid="baseButton-primary"]:focus {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }

      /* Expander as card wrapper */
      details[data-testid="st-expander"] {
        background: #F0F2F6 !important; /* match sidebar gray */
        border: 2px dotted #29B5E8;
        border-radius: 14px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        margin: 16px 0;
        padding: 0;
        overflow: hidden; /* clip inner content to rounded corners */
      }
      details[data-testid="st-expander"] > summary {
        font-weight: 800 !important; /* bold titles */
        color: #333333;
        padding: 10px 14px;
        border-radius: 14px 14px 0 0; /* rounded header */
      }
      /* Stronger, more specific selectors to override Streamlit defaults */
      [data-testid="stAppViewContainer"] details[data-testid="st-expander"] > summary,
      [data-testid="stAppViewContainer"] details[data-testid="st-expander"] > summary *,
      [data-testid="stAppViewContainer"] details[data-testid="st-expander"] > summary p,
      [data-testid="stAppViewContainer"] details[data-testid="st-expander"] > summary span,
      [data-testid="stAppViewContainer"] [data-testid="stExpander"] summary,
      [data-testid="stAppViewContainer"] [data-testid="stExpander"] summary * {
        font-weight: 800 !important;
        color: #333333 !important;
      }
      details[data-testid="st-expander"] > summary svg {
        display: none; /* hide caret icon */
      }
      /* Ensure content region inside expander is also gray and rounded */
      details[data-testid="st-expander"] > div {
        background: #F0F2F6 !important;
        border-radius: 0 0 14px 14px;
        padding: 12px 16px;
      }
      /* Some Streamlit versions use stExpander instead */
      [data-testid="stExpander"] {
        background: #F0F2F6 !important;
        border-radius: 14px !important;
        overflow: hidden;
      }
      /* Selected values in multiselect chips: make text white */
      div[data-baseweb="select"] div[data-baseweb="tag"] span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }
      /* Selected option in dropdown list: make text white */
      ul[role="listbox"] li[aria-selected="true"],
      ul[role="listbox"] li[aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }
      /* Stronger specificity: inside app container */
      [data-testid="stAppViewContainer"] div[data-baseweb="select"] div[data-baseweb="tag"],
      [data-testid="stAppViewContainer"] div[data-baseweb="select"] div[data-baseweb="tag"] *,
      [data-testid="stAppViewContainer"] div[data-baseweb="select"] div[data-baseweb="tag"] svg {
        color: #FFFFFF !important;
      }
      /* BaseWeb popover menu holds the options list */
      div[data-baseweb="popover"] [role="listbox"] [aria-selected="true"],
      div[data-baseweb="popover"] [role="listbox"] [aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }
      /* Removed targeted styles for deprecated concatenation multiselect */
    </style>
    <script>
      (function() {
        function applyWhiteForSelected() {
          try {
            // Selected chips in multiselect input
            document.querySelectorAll('div[data-baseweb="select"] div[data-baseweb="tag"]').forEach(function(el){
              el.style.setProperty('color', '#FFFFFF', 'important');
              el.style.setProperty('-webkit-text-fill-color', '#FFFFFF', 'important');
              el.querySelectorAll('*').forEach(function(k){
                k.style.setProperty('color', '#FFFFFF', 'important');
                k.style.setProperty('-webkit-text-fill-color', '#FFFFFF', 'important');
              });
            });
            // Selected option(s) inside the dropdown popover
            document.querySelectorAll('div[data-baseweb="popover"] [role="listbox"] [aria-selected="true"]').forEach(function(el){
              el.style.setProperty('color', '#FFFFFF', 'important');
              el.style.setProperty('-webkit-text-fill-color', '#FFFFFF', 'important');
              el.querySelectorAll('*').forEach(function(k){
                k.style.setProperty('color', '#FFFFFF', 'important');
                k.style.setProperty('-webkit-text-fill-color', '#FFFFFF', 'important');
              });
            });
          } catch (e) {}
        }
        // Initial apply and observe DOM changes to re-apply
        applyWhiteForSelected();
        const observer = new MutationObserver(function(){ applyWhiteForSelected(); });
        observer.observe(document.body, { subtree: true, childList: true, attributes: true });
      })();
    </script>
    """,
    unsafe_allow_html=True,
)


def ui_card(title: str):
    return st.expander(title, expanded=True)


###############################################################################
# Constants & Helpers
###############################################################################

CORTEX_MODEL_NAME = "mistral-large"
TARGET_TABLE_NAME = "HARMONIZATION_TESTING"
EMBEDDING_MODEL_NAME = "e5-base-v2"


def get_env_or_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    # Prefer Streamlit secrets, then env vars, then default
    try:
        return st.secrets.get(key, os.environ.get(key, default))  # type: ignore[arg-type]
    except Exception:
        return os.environ.get(key, default)


def quote_ident(ident: str) -> str:
    if ident is None:
        return ident
    # If already quoted, assume user provided correctly
    if ident.startswith('"') and ident.endswith('"'):
        return ident
    # Quote any identifier that is not all-uppercase alnum+underscore or contains spaces/specials
    needs_quotes = not ident.isupper() or any(ch in ident for ch in " -./\t\n\r\"'")
    if needs_quotes:
        escaped = ident.replace('"', '""')
        return f'"{escaped}"'
    return ident


def fq_name(database: str, schema: str, table: str) -> str:
    return f"{quote_ident(database)}.{quote_ident(schema)}.{quote_ident(table)}"


def parse_fq_table_name(fq_table: str) -> Tuple[str, str, str]:
    # Accept DB.SCHEMA.TABLE, with or without quotes
    parts: List[str] = []
    current = []
    in_quotes = False
    i = 0
    while i < len(fq_table):
        ch = fq_table[i]
        if ch == '"':
            if in_quotes and i + 1 < len(fq_table) and fq_table[i + 1] == '"':
                current.append('"')
                i += 2
                continue
            in_quotes = not in_quotes
            i += 1
            continue
        if ch == '.' and not in_quotes:
            parts.append(''.join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    if current:
        parts.append(''.join(current))
    if len(parts) != 3:
        raise ValueError("Expected fully-qualified name DB.SCHEMA.TABLE")
    return parts[0], parts[1], parts[2]


###############################################################################
# Snowflake Connectivity
###############################################################################


@st.cache_resource(show_spinner=False)
def get_connection(
    account: str,
    user: str,
    password: str,
    role: Optional[str],
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
):
    if sf is None:
        raise RuntimeError(
            "snowflake-connector-python is not installed. Please `pip install snowflake-connector-python`."
        )
    conn = sf.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database=database,
        schema=schema,
        client_session_keep_alive=True,
    )
    return conn


def run_query_df(conn, sql: str, params: Optional[Tuple[Any, ...]] = None) -> pd.DataFrame:
    # Support both Snowflake connector and Snowpark session
    if hasattr(conn, "cursor"):
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols)
    if hasattr(conn, "sql"):
        # Snowpark Session
        sp_df = conn.sql(sql)
        try:
            return sp_df.to_pandas()
        except Exception:
            rows = sp_df.collect()
            # Derive column names from schema
            try:
                col_names = [f.name for f in sp_df.schema.fields]
            except Exception:
                # Fallback: use keys of first row
                col_names = list(rows[0].asDict().keys()) if rows else []
            data = [list(r) for r in rows]
            return pd.DataFrame(data, columns=col_names)
    raise RuntimeError("Unknown connection type for run_query_df")


def run_exec(conn, sql: str) -> None:
    if hasattr(conn, "cursor"):
        with conn.cursor() as cur:
            cur.execute(sql)
        return
    if hasattr(conn, "sql"):
        conn.sql(sql).collect()
        return
    raise RuntimeError("Unknown connection type for run_exec")


###############################################################################
# Metadata Listing
###############################################################################


@st.cache_data(show_spinner=False)
def list_databases(_conn) -> List[str]:
    df = run_query_df(_conn, "show databases")
    return [row[1] for _, row in df.iterrows()]  # name at index 1


@st.cache_data(show_spinner=False)
def list_warehouses(_conn) -> List[str]:
    df = run_query_df(_conn, "show warehouses")
    # Similar to SHOW TABLES, stabilize on detected name column
    col_name = None
    for candidate in ["name", "NAME", "warehouse_name", "WAREHOUSE_NAME"]:
        if candidate in df.columns:
            col_name = candidate
            break
    if col_name is None and len(df.columns) > 1:
        col_name = df.columns[1]
    return df[col_name].tolist() if col_name else []


@st.cache_data(show_spinner=False)
def list_schemas(_conn, database: str) -> List[str]:
    df = run_query_df(_conn, f"show schemas in {quote_ident(database)}")
    return [row[1] for _, row in df.iterrows()]


@st.cache_data(show_spinner=False)
def list_tables(_conn, database: str, schema: str) -> List[str]:
    df = run_query_df(_conn, f"show tables in {quote_ident(database)}.{quote_ident(schema)}")
    # SHOW returns many columns; the second column is often NAME, but be resilient
    col_name = None
    for candidate in ["name", "NAME", "table_name", "TABLE_NAME"]:
        if candidate in df.columns:
            col_name = candidate
            break
    if col_name is None and len(df.columns) > 1:
        col_name = df.columns[1]
    return df[col_name].tolist() if col_name else []


@st.cache_data(show_spinner=False)
def list_columns(_conn, database: str, schema: str, table: str) -> List[Tuple[str, str]]:
    sql = (
        f"select column_name, data_type from {quote_ident(database)}.information_schema.columns "
        f"where table_schema = {sql_string_literal(schema)} and table_name = {sql_string_literal(table)} "
        f"order by ordinal_position"
    )
    df = run_query_df(_conn, sql)
    results: List[Tuple[str, str]] = []
    for _, row in df.iterrows():
        results.append((str(row["COLUMN_NAME"]) if "COLUMN_NAME" in df.columns else str(row["column_name"]), str(row["DATA_TYPE"]) if "DATA_TYPE" in df.columns else str(row["data_type"])))
    return results


###############################################################################
# Profiling
###############################################################################


def sql_string_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


@st.cache_data(show_spinner=False)
def profile_table(_conn, database: str, schema: str, table: str) -> pd.DataFrame:
    cols = list_columns(_conn, database, schema, table)
    if not cols:
        return pd.DataFrame(
            columns=[
                "COLUMN_NAME",
                "DATA_TYPE",
                "ROW_COUNT",
                "NULL_COUNT",
                "DISTINCT_COUNT",
                "AVG_LENGTH",
                "FRACTION_NUMERIC",
                "SAMPLE_VALUES",
            ]
        )
    qualified = f"{quote_ident(database)}.{quote_ident(schema)}.{quote_ident(table)}"
    union_sqls: List[str] = []
    for col_name, data_type in cols:
        qcol = f"{qualified}.{quote_ident(col_name)}"
        union_sqls.append(
            """
select
    {col_name_lit} as COLUMN_NAME,
    {data_type_lit} as DATA_TYPE,
    count(*) as ROW_COUNT,
    sum(iff({qcol} is null, 1, 0)) as NULL_COUNT,
    approx_count_distinct({qcol}) as DISTINCT_COUNT,
    cast(avg(len(cast({qcol} as string))) as double) as AVG_LENGTH,
    cast(avg(iff(regexp_like(cast({qcol} as string), '^[0-9]+$'), 1, 0)) as double) as FRACTION_NUMERIC,
    (
        select array_agg(sample_value)
        from (
            select any_value(cast({qcol} as string)) as sample_value
            from {qualified} sample (5 rows)
        ) s
    ) as SAMPLE_VALUES
from {qualified}
            """.strip().format(
                col_name_lit=sql_string_literal(col_name),
                data_type_lit=sql_string_literal(data_type),
                qcol=qcol,
                qualified=qualified,
            )
        )
    sql = "\nunion all\n".join(union_sqls)
    return run_query_df(_conn, sql)


###############################################################################
# Cortex AI Suggestion
###############################################################################


def cortex_complete(conn, prompt: str) -> str:
    # Supports both connector (cursor) and Snowpark session (sql)
    # Different accounts may return a plain string or a VARIANT object with a response field.
    if hasattr(conn, "cursor"):
        q = "select snowflake.cortex.complete(%s, %s) as result"
        with conn.cursor() as cur:
            cur.execute(q, (CORTEX_MODEL_NAME, prompt))
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Empty response from Cortex AI")
            result = row[0]
    elif hasattr(conn, "sql"):
        q = (
            "select snowflake.cortex.complete("
            + sql_string_literal(CORTEX_MODEL_NAME)
            + ", "
            + sql_string_literal(prompt)
            + ") as result"
        )
        try:
            pdf = conn.sql(q).to_pandas()
            result = pdf.iloc[0, 0] if not pdf.empty else None
        except Exception:
            rows = conn.sql(q).collect()
            result = rows[0][0] if rows else None
        if result is None:
            raise RuntimeError("Empty response from Cortex AI")
    else:
        raise RuntimeError("Unknown connection type for Cortex call")

    try:
        if isinstance(result, dict) and "response" in result:
            return str(result["response"]).strip()
        return str(result).strip()
    except Exception:
        return str(result)


def build_mapping_prompt(
    table_a_fqn: str,
    table_b_fqn: str,
    profile_a: pd.DataFrame,
    profile_b: pd.DataFrame,
) -> str:
    def minimize(df: pd.DataFrame) -> List[Dict[str, Any]]:
        return [
            {
                "column": str(row["COLUMN_NAME"]),
                "data_type": str(row["DATA_TYPE"]),
                "distinct_count": int(row["DISTINCT_COUNT"]) if pd.notna(row["DISTINCT_COUNT"]) else None,
                "null_ratio": (float(row["NULL_COUNT"]) / float(row["ROW_COUNT"]) if row["ROW_COUNT"] else None),
                "avg_length": float(row["AVG_LENGTH"]) if pd.notna(row["AVG_LENGTH"]) else None,
                "fraction_numeric": float(row["FRACTION_NUMERIC"]) if pd.notna(row["FRACTION_NUMERIC"]) else None,
                "samples": row["SAMPLE_VALUES"] if isinstance(row["SAMPLE_VALUES"], list) else None,
            }
            for _, row in df.iterrows()
        ]

    payload = {
        "instruction": "You are a data integration expert. Infer semantic mappings across two tables. Only match dimension fields, not facts (e.g., omit price).",
        "tables": {
            "table_a": {"name": table_a_fqn, "columns": minimize(profile_a)},
            "table_b": {"name": table_b_fqn, "columns": minimize(profile_b)},
        },
        "harmonized_fields": [
            "product_id",
            "product_name",
            "product_description",
            "manufacturer"
        ],
        "requirements": [
            "Identify which columns contain product identifiers and descriptions.",
            "Suggest joinable attribute pairs (join keys) across the two tables.",
            "Return STRICT JSON only, matching the provided schema.",
        ],
        "json_schema": {
            "type": "object",
            "properties": {
                "mappings": {
                    "type": "object",
                    "properties": {
                        "table_a": {"type": "object"},
                        "table_b": {"type": "object"},
                    },
                    "required": ["table_a", "table_b"],
                },
                "join_key": {
                    "type": ["object", "null"],
                    "properties": {
                        "table_a_column": {"type": "string"},
                        "table_b_column": {"type": "string"},
                        "confidence": {"type": ["number", "null"]},
                    },
                },
                "notes": {"type": ["string", "null"]},
            },
            "required": ["mappings"],
        },
        "output_format": {
            "mappings": {
                "table_a": {
                    "product_id": "<column_name_or_null>",
                    "product_name": "<column_name_or_null>",
                    "product_description": "<column_name_or_null>",
                    "manufacturer": "<column_name_or_null>"
                },
                "table_b": {
                    "product_id": "<column_name_or_null>",
                    "product_name": "<column_name_or_null>",
                    "product_description": "<column_name_or_null>",
                    "manufacturer": "<column_name_or_null>"
                },
            },
            "join_key": {
                "table_a_column": "<column_name_or_null>",
                "table_b_column": "<column_name_or_null>",
                "confidence": 0.0,
            },
            "notes": "<any_notes>"
        },
        "instructions": [
            "Only output JSON, no prose.",
            "If unsure, set a field to null.",
            "Prefer high-cardinality columns with few nulls as product_id.",
            "Prefer long text columns as product_description.",
        ],
    }
    return (
        "Return ONLY valid JSON matching this schema and format.\nPayload:" + json.dumps(payload, ensure_ascii=False)
    )


def get_ai_mappings(
    conn,
    table_a_fqn: str,
    table_b_fqn: str,
    profile_a: pd.DataFrame,
    profile_b: pd.DataFrame,
) -> Dict[str, Any]:
    prompt = build_mapping_prompt(table_a_fqn, table_b_fqn, profile_a, profile_b)
    try:
        raw = cortex_complete(conn, prompt)
        # Some models may wrap JSON in code fences; try to strip
        raw_str = raw.strip()
        if raw_str.startswith("```"):
            raw_str = raw_str.strip("`\n ")
            if raw_str.lower().startswith("json"):
                raw_str = raw_str[4:].lstrip("\n")
        data = json.loads(raw_str)
        if not isinstance(data, dict):
            raise ValueError("AI did not return a JSON object")
        return data
    except Exception as e:
        st.warning(f"Cortex AI mapping failed, falling back to heuristic suggestions: {e}")
        return heuristic_mapping(profile_a, profile_b)


def heuristic_mapping(profile_a: pd.DataFrame, profile_b: pd.DataFrame) -> Dict[str, Any]:
    def guess_pid(df: pd.DataFrame) -> Optional[str]:
        # Prefer columns with high distinct_count close to row_count and numeric-ish names like ID, SKU
        candidates = []
        for _, r in df.iterrows():
            name = str(r["COLUMN_NAME"]).upper()
            distinct_count = r["DISTINCT_COUNT"] if pd.notna(r["DISTINCT_COUNT"]) else 0
            row_count = r["ROW_COUNT"] if pd.notna(r["ROW_COUNT"]) else 0
            score = 0
            if any(k in name for k in ["ID", "SKU", "UPC", "EAN", "PRODUCT_ID"]):
                score += 2
            if row_count and distinct_count and distinct_count / max(row_count, 1) > 0.8:
                score += 1
            if score > 0:
                candidates.append((score, name))
        if candidates:
            return max(candidates)[1]
        # else fallback to first numeric-ish
        for _, r in df.iterrows():
            name = str(r["COLUMN_NAME"]).upper()
            if r["FRACTION_NUMERIC"] and r["FRACTION_NUMERIC"] > 0.9:
                return name
        return None

    def guess_desc(df: pd.DataFrame) -> Optional[str]:
        best = None
        best_len = 0.0
        for _, r in df.iterrows():
            avg_len = float(r["AVG_LENGTH"]) if pd.notna(r["AVG_LENGTH"]) else 0.0
            name = str(r["COLUMN_NAME"]).upper()
            if any(k in name for k in ["DESC", "DESCRIPTION", "DETAIL", "PRODUCT_LABEL", "NAME"]):
                avg_len += 20
            if avg_len > best_len:
                best_len = avg_len
                best = name
        return best

    a_pid = guess_pid(profile_a)
    b_pid = guess_pid(profile_b)
    a_desc = guess_desc(profile_a)
    b_desc = guess_desc(profile_b)

    def norm(name: Optional[str]) -> Optional[str]:
        return None if name is None else name

    return {
        "mappings": {
            "table_a": {
                "product_id": norm(a_pid),
                "product_name": None,
                "product_description": norm(a_desc),
                "manufacturer": None,
            },
            "table_b": {
                "product_id": norm(b_pid),
                "product_name": None,
                "product_description": norm(b_desc),
                "manufacturer": None,
            },
        },
        "join_key": {
            "table_a_column": norm(a_pid),
            "table_b_column": norm(b_pid),
            "confidence": 0.4,
        },
        "notes": "Heuristic fallback used due to AI unavailability.",
    }


###############################################################################
# UI Components
###############################################################################


def connection_sidebar() -> Optional[Any]:
    def ensure_connection() -> Optional[Any]:
        if st.session_state.get("conn") is not None:
            return st.session_state.get("conn")
        # First, try to use an active Snowpark session (e.g., Streamlit in Snowflake)
        try:
            if sp_get_active_session is not None:
                sp_sess = sp_get_active_session()
                if sp_sess is not None:
                    st.session_state["conn"] = sp_sess
                    return sp_sess
        except Exception:
            pass
        # Fallback to secrets-based connector
        account = get_env_or_secret("SNOWFLAKE_ACCOUNT")
        user = get_env_or_secret("SNOWFLAKE_USER")
        password = get_env_or_secret("SNOWFLAKE_PASSWORD")
        role = get_env_or_secret("SNOWFLAKE_ROLE")
        warehouse = get_env_or_secret("SNOWFLAKE_WAREHOUSE")
        database = get_env_or_secret("SNOWFLAKE_DATABASE")
        schema = get_env_or_secret("SNOWFLAKE_SCHEMA")
        if not (account and user and password):
            st.sidebar.info("Using current Snowflake session if available. If running locally, add secrets.")
            return None
        try:
            conn_local = get_connection(account, user, password, role, warehouse, database, schema)
            st.session_state["conn"] = conn_local
            return conn_local
        except Exception as e:
            st.sidebar.error(f"Failed to connect: {e}")
            return None

    def fetch_current_context(conn) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            df = run_query_df(conn, "select current_warehouse(), current_database(), current_schema()")
            row = df.iloc[0]
            return (row[0], row[1], row[2])
        except Exception:
            return (None, None, None)

    with st.sidebar:
        st.subheader("Snowflake Session")
        conn = ensure_connection()
        if not conn:
            return None

        # Establish default context if not in session
        if "current_warehouse" not in st.session_state or "current_database" not in st.session_state or "current_schema" not in st.session_state:
            wh, db, sch = fetch_current_context(conn)
            st.session_state["current_warehouse"] = wh
            st.session_state["current_database"] = db
            st.session_state["current_schema"] = sch

        # Context: keep current warehouse; allow switching Database/Schema only
        databases = list_databases(conn)
        selected_db = st.selectbox(
            "Database",
            databases,
            index=(databases.index(st.session_state["current_database"]) if st.session_state.get("current_database") in databases else 0),
        ) if databases else None
        if selected_db and selected_db != st.session_state.get("current_database"):
            # Do not execute USE. Just update state and reset schema selection.
            st.session_state["current_database"] = selected_db
            st.session_state["current_schema"] = None

        # Build schema options with a blank placeholder; do not execute USE statements
        schemas = list_schemas(conn, st.session_state.get("current_database") or (selected_db or databases[0])) if databases else []
        schema_options = [""] + schemas
        current_schema_val = st.session_state.get("current_schema") or ""
        selected_schema = st.selectbox(
            "Schema",
            schema_options,
            index=(schema_options.index(current_schema_val) if current_schema_val in schema_options else 0),
        ) if schemas else None
        if selected_schema is not None:
            st.session_state["current_schema"] = selected_schema or None

    return st.session_state.get("conn")


def table_picker(conn) -> Optional[Tuple[str, str]]:
    with ui_card("1) Choose two source tables"):
        current_db = st.session_state.get("current_database")
        current_schema = st.session_state.get("current_schema")
        if not current_db or not current_schema:
            st.warning("Select a database and schema in the sidebar.")
            return None
        tables = list_tables(conn, current_db, current_schema)
        if not tables:
            st.info("No tables found in selected schema.")
            return None
        cols = st.columns(2)
        with cols[0]:
            t1 = st.selectbox("Reference Table", tables, key="table_0")
        with cols[1]:
            t2 = st.selectbox("Input Table", tables, key="table_1")
        if not t1 or not t2:
            return None
        return fq_name(current_db, current_schema, t1), fq_name(current_db, current_schema, t2)


def harmonization_workflow(conn, table_a_fqn: str, table_b_fqn: str):
    with ui_card("2) Profile & Analyze"):
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"Profiling Reference Table: {table_a_fqn}")
        with c2:
            st.caption(f"Profiling Input Table: {table_b_fqn}")

        db_a, schema_a, tbl_a = parse_fq_table_name(table_a_fqn)
        db_b, schema_b, tbl_b = parse_fq_table_name(table_b_fqn)

        prof_a = profile_table(conn, db_a, schema_a, tbl_a)
        prof_b = profile_table(conn, db_b, schema_b, tbl_b)

        with c1:
            st.dataframe(prof_a, use_container_width=True, hide_index=True)
        with c2:
            st.dataframe(prof_b, use_container_width=True, hide_index=True)

    with ui_card("3) Cortex AI Recommendations"):
        if st.button("Run AI Analysis", type="primary"):
            with st.spinner("Calling Cortex AI for mapping suggestions..."):
                ai = get_ai_mappings(conn, table_a_fqn, table_b_fqn, prof_a, prof_b)
                st.session_state["ai_mapping"] = ai

        ai_data = st.session_state.get("ai_mapping")
        if not ai_data:
            st.info("Click Run AI Analysis to get suggestions.")
            return


        with ui_card("4) Review and Edit Mappings"):
            mappings = ai_data.get("mappings", {}) if isinstance(ai_data, dict) else {}
            defaults_a = mappings.get("table_a", {})
            defaults_b = mappings.get("table_b", {})

            options_a = [str(c) for c in prof_a["COLUMN_NAME"].tolist()]
            options_b = [str(c) for c in prof_b["COLUMN_NAME"].tolist()]

            st.markdown("Select source columns for each harmonized field (dimension fields only). Use the checkbox to include the field in the datasets.")
            fields = ["product_id", "product_name", "product_description", "manufacturer"]

            # Render rows: [checkbox] [field name] [Reference select] [Input select]
            header = st.columns([1, 4, 8, 8])
            with header[1]:
                st.caption("Field")
            with header[2]:
                st.caption("Reference column")
            with header[3]:
                st.caption("Input column")

            map_a: Dict[str, Optional[str]] = {}
            map_b: Dict[str, Optional[str]] = {}
            include_cols: Dict[str, bool] = {}
            for field in fields:
                row = st.columns([1, 4, 8, 8])
                # Recommendation based on AI defaults existing in both lists
                recommended = bool(defaults_a.get(field) in options_a and defaults_b.get(field) in options_b)
                with row[0]:
                    include_cols[field] = st.checkbox("", value=recommended, key=f"include_{field}")
                with row[1]:
                    st.markdown(f"<span style='color:#000000'>{field}</span>", unsafe_allow_html=True)
                with row[2]:
                    map_a[field] = st.selectbox(
                        f"Reference {field}",
                        [None] + options_a,
                        index=(1 + options_a.index(defaults_a.get(field))) if defaults_a.get(field) in options_a else 0,
                        key=f"map_a_{field}",
                        label_visibility="collapsed",
                    )
                with row[3]:
                    map_b[field] = st.selectbox(
                        f"Input {field}",
                        [None] + options_b,
                        index=(1 + options_b.index(defaults_b.get(field))) if defaults_b.get(field) in options_b else 0,
                        key=f"map_b_{field}",
                        label_visibility="collapsed",
                    )

            st.markdown("Suggested join key pair (optional):")
            join_defaults = ai_data.get("join_key", {}) if isinstance(ai_data, dict) else {}
            join_col_a = st.selectbox(
                "Join key in Reference Table",
                [None] + options_a,
                index=(1 + options_a.index(join_defaults.get("table_a_column"))) if join_defaults.get("table_a_column") in options_a else 0,
                key="join_key_a",
            )
            join_col_b = st.selectbox(
                "Join key in Input Table",
                [None] + options_b,
                index=(1 + options_b.index(join_defaults.get("table_b_column"))) if join_defaults.get("table_b_column") in options_b else 0,
                key="join_key_b",
            )

            st.session_state["final_mapping"] = {
                "table_a": map_a,
                "table_b": map_b,
                "join_key": {"table_a_column": join_col_a, "table_b_column": join_col_b},
                "include_fields": [f for f in fields if include_cols.get(f)],
            }

        # Commented out per request: Fuzzy matching and semantic views
        if False:
            with ui_card("5) Fuzzy Matching (Cortex)"):
                st.caption("Use embeddings to align semantically similar values across tables (e.g., product names, manufacturers).")
                candidate_fields = [f for f in ["product_name", "product_description", "manufacturer"] if map_a.get(f) and map_b.get(f)]
                fuzzy_fields = st.multiselect("Fields to fuzzy-match", candidate_fields, default=[f for f in ["product_name", "manufacturer"] if f in candidate_fields])
                col_fm = st.columns(3)
                with col_fm[0]:
                    top_k = st.selectbox("Top matches per value", [1, 2, 3, 5], index=0)
                with col_fm[1]:
                    threshold = st.slider("Min similarity (0-1)", min_value=0.0, max_value=1.0, value=0.75, step=0.01)
                with col_fm[2]:
                    run_fuzzy = st.button("Run Fuzzy Matching")

                if run_fuzzy and fuzzy_fields:
                    with st.spinner("Computing embeddings and matches..."):
                        previews: Dict[str, pd.DataFrame] = {}
                        for field in fuzzy_fields:
                            col_a = map_a.get(field)
                            col_b = map_b.get(field)
                            if not col_a or not col_b:
                                continue
                            try:
                                compute_fuzzy_mapping_table(
                                    conn,
                                    table_a_fqn,
                                    col_a,
                                    table_b_fqn,
                                    col_b,
                                    field,
                                    top_k,
                                    float(threshold),
                                )
                                prev = preview_fuzzy_mapping_table(conn, field, limit=100)
                                previews[field] = prev
                            except Exception as e:
                                st.warning(f"Fuzzy matching for {field} failed: {e}")
                        st.session_state["fuzzy_selected_fields"] = fuzzy_fields
                        if previews:
                            for f_name, df_prev in previews.items():
                                st.markdown(f"Preview for {f_name} matches:")
                                st.dataframe(df_prev, use_container_width=True, hide_index=True)

            with ui_card("6) Create Semantic Views"):
                if st.button("Create/Replace Semantic Views"):
                    try:
                        create_semantic_view(conn, db_a, schema_a, tbl_a, map_a)
                        create_semantic_view(conn, db_b, schema_b, tbl_b, map_b)
                        st.success("Semantic views created.")
                    except Exception as e:
                        st.error(f"Failed to create views: {e}")

        # New step: build model input datasets and audit table based on selected fields
        with ui_card("5) Create Datasets for Matching Algorithm"):
            # Determine fields present in both mappings (auto-included)
            include_fields = [f for f in ["product_id", "product_name", "product_description", "manufacturer"] if (map_a.get(f) and map_b.get(f) and st.session_state.get("final_mapping", {}).get("include_fields", []) and f in st.session_state.get("final_mapping", {}).get("include_fields", []))]
            # Fallback: if no explicit includes from step 4, include all that are mapped in both tables
            if not include_fields:
                include_fields = [f for f in ["product_id", "product_name", "product_description", "manufacturer"] if (map_a.get(f) and map_b.get(f))]

            if not include_fields:
                st.info("Map at least one field in step 4 to enable dataset creation.")
            current_db = st.session_state.get("current_database") or db_a
            current_schema = st.session_state.get("current_schema") or schema_a
            target_db = st.selectbox("Target database for model inputs", list_databases(conn), index=(list_databases(conn).index(current_db) if current_db in list_databases(conn) else 0), key="mi_target_db")
            target_schema = st.text_input("Target schema for model inputs", value=current_schema, key="mi_target_schema")
            # Predict output table names for tooltip
            _today_tag = datetime.date.today().strftime("%Y_%m_%d")
            _pred_ref = f"{tbl_a}_Harmonization_{_today_tag}"
            _pred_inp = f"{tbl_b}_Harmonization_{_today_tag}"
            run_build = st.button(
                "Create Datasets",
                type="primary",
                disabled=not include_fields,
                help=(
                    f"Creates {st.session_state.get('mi_target_db', '') or (st.session_state.get('current_database') or db_a)}."
                    f"{st.session_state.get('mi_target_schema', '') or (st.session_state.get('current_schema') or schema_a)}."
                    f"{_pred_ref} and "
                    f"{st.session_state.get('mi_target_db', '') or (st.session_state.get('current_database') or db_a)}."
                    f"{st.session_state.get('mi_target_schema', '') or (st.session_state.get('current_schema') or schema_a)}."
                    f"{_pred_inp}. Also writes audit table AUDIT_HARMONIZATION_{_today_tag}."
                ),
            )
            if run_build:
                with st.spinner("Creating Input & Reference Models and writing audit table..."):
                    try:
                        ref_out, inp_out, audit_out = create_model_inputs_and_audit(
                            conn,
                            target_db,
                            target_schema,
                            table_a_fqn,
                            table_b_fqn,
                            map_a,
                            map_b,
                            include_fields,
                        )
                        # Save for preview dropdown
                        st.session_state["mi_ref_out"] = ref_out
                        st.session_state["mi_inp_out"] = inp_out
                        st.success(f"Created reference output: {ref_out}\nCreated input output: {inp_out}\nCreated audit table: {audit_out}")
                    except Exception as e:
                        st.error(f"Failed to create model inputs/audit: {e}")

            # Optional preview dropdown (10 rows) for created datasets
            ref_created = st.session_state.get("mi_ref_out")
            inp_created = st.session_state.get("mi_inp_out")
            if ref_created and inp_created:
                preview_choice = st.selectbox(
                    "Preview 10 rows from:",
                    ["Reference Output", "Input Output"],
                    index=0,
                    key="mi_preview_choice",
                )
                # Parse and quote chosen table
                chosen_fqn = ref_created if preview_choice == "Reference Output" else inp_created
                try:
                    db_p, sch_p, tbl_p = parse_fq_table_name(chosen_fqn)
                    chosen_quoted = f"{quote_ident(db_p)}.{quote_ident(sch_p)}.{quote_ident(tbl_p)}"
                except Exception:
                    chosen_quoted = chosen_fqn
                try:
                    df_preview = run_query_df(conn, f"select * from {chosen_quoted} limit 10")
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.warning(f"Failed to preview {preview_choice}: {e}")

        # Commented out per request: Create Harmonized Table section
        if False:
            with ui_card("7) Create Harmonized Table"):
                # Default to current session context for target
                current_db = st.session_state.get("current_database") or db_a
                current_schema = st.session_state.get("current_schema") or schema_a
                target_db = st.selectbox("Target database for table", list_databases(conn), index=(list_databases(conn).index(current_db) if current_db in list_databases(conn) else 0))
                target_schema = st.text_input("Target schema", value=current_schema)
                apply_fuzzy = False
                if st.button(f"Create/Replace {TARGET_TABLE_NAME}", type="primary"):
                    try:
                        create_harmonized_table(
                            conn,
                            target_db,
                            target_schema,
                            table_a_fqn,
                            table_b_fqn,
                            map_a,
                            map_b,
                            join_col_a,
                            join_col_b,
                            None,
                        )
                        st.success(f"Table {quote_ident(target_db)}.{quote_ident(target_schema)}.{quote_ident(TARGET_TABLE_NAME)} created.")
                    except Exception as e:
                        st.error(f"Failed to create harmonized table: {e}")


def create_semantic_view(conn, database: str, schema: str, table: str, mapping: Dict[str, Optional[str]]):
    view_name = f"SEMANTIC_{table}"
    selected_cols = []
    aliases = {
        "product_id": "PRODUCT_ID",
        "product_name": "PRODUCT_NAME",
        "product_description": "PRODUCT_DESCRIPTION",
        "manufacturer": "MANUFACTURER",
    }
    for field, alias in aliases.items():
        src_col = mapping.get(field)
        if src_col:
            selected_cols.append(f"{quote_ident(table)}.{quote_ident(src_col)} as {quote_ident(alias)}")
        else:
            selected_cols.append(f"cast(null as string) as {quote_ident(alias)}")
    joined_cols = ",\n    ".join(selected_cols)
    sql = f"""
create or replace view {quote_ident(database)}.{quote_ident(schema)}.{quote_ident(view_name)} as
select
    {joined_cols}
from {quote_ident(database)}.{quote_ident(schema)}.{quote_ident(table)} {quote_ident(table)}
"""
    run_exec(conn, sql)


def create_harmonized_table(
    conn,
    target_db: str,
    target_schema: str,
    table_a_fqn: str,
    table_b_fqn: str,
    map_a: Dict[str, Optional[str]],
    map_b: Dict[str, Optional[str]],
    join_col_a: Optional[str],
    join_col_b: Optional[str],
    fuzzy_fields: Optional[List[str]] = None,
):
    db_a, schema_a, tbl_a = parse_fq_table_name(table_a_fqn)
    db_b, schema_b, tbl_b = parse_fq_table_name(table_b_fqn)

    unified_cols = [
        ("PRODUCT_ID", "product_id"),
        ("PRODUCT_NAME", "product_name"),
        ("PRODUCT_DESCRIPTION", "product_description"),
        ("MANUFACTURER", "manufacturer"),
    ]

    def select_list(db: str, schema: str, table: str, mapping: Dict[str, Optional[str]], source_label: str, is_table_a: bool) -> Tuple[str, List[str]]:
        exprs = [
            ""  # placeholder to be built below
        ]
        joins: List[str] = []
        for idx, (alias, col_key) in enumerate(unified_cols):
            if mapping.get(col_key):
                base_expr = f"{quote_ident(db)}.{quote_ident(schema)}.{quote_ident(table)}.{quote_ident(mapping[col_key])}"
            else:
                base_expr = "cast(null as string)"
            # Apply fuzzy mapping for Table A only, if requested and available for this field
            if is_table_a and fuzzy_fields and col_key in fuzzy_fields and mapping.get(col_key):
                map_alias = f"m_{col_key}"
                map_table = f"TMP_FUZZY_MAP_{col_key.upper()}"
                joins.append(
                    f"left join {quote_ident(map_table)} {quote_ident(map_alias)} on cast({base_expr} as string) = {quote_ident(map_alias)}.A_VALUE"
                )
                exprs[idx] = f"coalesce({quote_ident(map_alias)}.B_VALUE, {base_expr}) as {quote_ident(alias)}"
            else:
                exprs[idx] = f"{base_expr} as {quote_ident(alias)}"
        # join key as generic column if provided
        exprs.append(
            (
                f"{quote_ident(db)}.{quote_ident(schema)}.{quote_ident(table)}.{quote_ident(mapping.get('product_id'))}"
                if mapping.get("product_id")
                else "cast(null as string)"
            )
            + " as "
            + quote_ident("JOIN_KEY")
        )
        exprs.append(f"{repr(source_label)} as {quote_ident('SOURCE_TABLE')}")
        return ",\n        ".join(exprs), joins

    select_a_exprs, select_a_joins = select_list(db_a, schema_a, tbl_a, map_a, f"{db_a}.{schema_a}.{tbl_a}", True)
    select_b_exprs, select_b_joins = select_list(db_b, schema_b, tbl_b, map_b, f"{db_b}.{schema_b}.{tbl_b}", False)

    select_a_join_str = "\n".join(select_a_joins) if select_a_joins else ""
    select_b_join_str = "\n".join(select_b_joins) if select_b_joins else ""

    select_a = f"""
select
        {select_a_exprs}
from {quote_ident(db_a)}.{quote_ident(schema_a)}.{quote_ident(tbl_a)}
{select_a_join_str}
"""
    select_b = f"""
select
        {select_b_exprs}
from {quote_ident(db_b)}.{quote_ident(schema_b)}.{quote_ident(tbl_b)}
{select_b_join_str}
"""

    create_sql = f"""
create or replace table {quote_ident(target_db)}.{quote_ident(target_schema)}.{quote_ident(TARGET_TABLE_NAME)} as
{select_a}
union all
{select_b}
"""
    run_exec(conn, create_sql)


def create_model_inputs_and_audit(
    conn,
    target_db: str,
    target_schema: str,
    ref_fqn: str,
    inp_fqn: str,
    map_a: Dict[str, Optional[str]],
    map_b: Dict[str, Optional[str]],
    include_fields: List[str],
) -> Tuple[str, str, str]:
    # Parse table names
    db_a, schema_a, tbl_a = parse_fq_table_name(ref_fqn)
    db_b, schema_b, tbl_b = parse_fq_table_name(inp_fqn)

    # Build output table names
    today = datetime.date.today()
    date_tag = today.strftime("%Y_%m_%d")
    ref_out_table = f"{tbl_a}_Harmonization_{date_tag}"
    inp_out_table = f"{tbl_b}_Harmonization_{date_tag}"
    ref_out_fqn = f"{quote_ident(target_db)}.{quote_ident(target_schema)}.{quote_ident(ref_out_table)}"
    inp_out_fqn = f"{quote_ident(target_db)}.{quote_ident(target_schema)}.{quote_ident(inp_out_table)}"

    # Use original column names (no aliases) in outputs

    # Helper to build SELECT list for a side (no concatenated column)
    def build_side_select(db: str, schema: str, table: str, mapping: Dict[str, Optional[str]], original_label: str) -> str:
        qtbl = f"{quote_ident(db)}.{quote_ident(schema)}.{quote_ident(table)}"
        select_exprs: List[str] = [f"{repr(f'{db}.{schema}.{table}')} as {quote_ident(original_label.upper())}"]
        for field in ["product_id", "product_name", "product_description", "manufacturer"]:
            if field not in include_fields:
                continue
            src = mapping.get(field)
            if not src:
                continue
            cleaned = f"regexp_replace(cast({qtbl}.{quote_ident(src)} as string), '[^a-zA-Z0-9 ]', '')"
            select_exprs.append(f"{cleaned} as {quote_ident(src.upper())}")
        return ",\n        ".join(select_exprs)

    ref_select_list = build_side_select(db_a, schema_a, tbl_a, map_a, "ORIGINAL_REFERENCE_TABLE")
    inp_select_list = build_side_select(db_b, schema_b, tbl_b, map_b, "ORIGINAL_INPUT_TABLE")

    # Create reference output table
    create_ref_sql = f"""
create or replace table {ref_out_fqn} as
select
        {ref_select_list}
from {quote_ident(db_a)}.{quote_ident(schema_a)}.{quote_ident(tbl_a)}
"""
    run_exec(conn, create_ref_sql)

    # Create input output table
    create_inp_sql = f"""
create or replace table {inp_out_fqn} as
select
        {inp_select_list}
from {quote_ident(db_b)}.{quote_ident(schema_b)}.{quote_ident(tbl_b)}
"""
    run_exec(conn, create_inp_sql)

    # Build audit table
    audit_table = f"AUDIT_HARMONIZATION_{date_tag}"
    audit_fqn = f"{quote_ident(target_db)}.{quote_ident(target_schema)}.{quote_ident(audit_table)}"
    run_exec(
        conn,
        f"create or replace table {audit_fqn} (\n"
        "    Date_of_Run string,\n"
        "    User string,\n"
        "    Role string,\n"
        "    Session string,\n"
        "    Reference_Dataset string,\n"
        "    Input_Dataset string,\n"
        "    Reference_Dataset_Column string,\n"
        "    Input_Dataset_Column string,\n"
        "    Matched_in_output string,\n"
        "    Reference_Output_Table string,\n"
        "    Input_Dataset_Table string\n"
        ")",
    )

    # Get current context
    ctx = run_query_df(conn, "select current_user(), current_role(), current_session()")
    cur_user = str(ctx.iloc[0, 0]) if not ctx.empty else ""
    cur_role = str(ctx.iloc[0, 1]) if not ctx.empty else ""
    cur_session = str(ctx.iloc[0, 2]) if not ctx.empty else ""
    date_of_run = today.strftime("%m/%d/%Y")

    # Insert rows
    values_rows: List[str] = []
    for field in ["product_id", "product_name", "product_description", "manufacturer"]:
        ref_col = map_a.get(field)
        inp_col = map_b.get(field)
        ref_alias = ref_col if ref_col else "null"
        inp_alias = inp_col if inp_col else "null"
        matched = "Yes" if (ref_col and inp_col and field in include_fields) else "No"
        values_rows.append(
            "("
            + ", ".join([
                sql_string_literal(date_of_run),
                sql_string_literal(cur_user),
                sql_string_literal(cur_role),
                sql_string_literal(cur_session),
                sql_string_literal(f"{db_a}.{schema_a}.{tbl_a}"),
                sql_string_literal(f"{db_b}.{schema_b}.{tbl_b}"),
                sql_string_literal(ref_alias if ref_col else "null"),
                sql_string_literal(inp_alias if inp_col else "null"),
                sql_string_literal(matched),
                sql_string_literal(f"{target_db}.{target_schema}.{ref_out_table}"),
                sql_string_literal(f"{target_db}.{target_schema}.{inp_out_table}"),
            ])
            + ")"
        )
    insert_sql = f"insert into {audit_fqn} (Date_of_Run, User, Role, Session, Reference_Dataset, Input_Dataset, Reference_Dataset_Column, Input_Dataset_Column, Matched_in_output, Reference_Output_Table, Input_Dataset_Table) values \n" + ",\n".join(values_rows)
    run_exec(conn, insert_sql)

    return (f"{target_db}.{target_schema}.{ref_out_table}", f"{target_db}.{target_schema}.{inp_out_table}", f"{target_db}.{target_schema}.{audit_table}")


def compute_fuzzy_mapping_table(
    conn,
    table_a_fqn: str,
    col_a: str,
    table_b_fqn: str,
    col_b: str,
    field_name: str,
    top_k: int,
    threshold: float,
) -> None:
    db_a, schema_a, tbl_a = parse_fq_table_name(table_a_fqn)
    db_b, schema_b, tbl_b = parse_fq_table_name(table_b_fqn)
    qa = f"{quote_ident(db_a)}.{quote_ident(schema_a)}.{quote_ident(tbl_a)}.{quote_ident(col_a)}"
    qb = f"{quote_ident(db_b)}.{quote_ident(schema_b)}.{quote_ident(tbl_b)}.{quote_ident(col_b)}"
    tmp_table = f"TMP_FUZZY_MAP_{field_name.upper()}"
    sql = f"""
create or replace table {quote_ident(tmp_table)} as
with A as (
  select distinct cast({qa} as string) as A_VALUE
  from {quote_ident(db_a)}.{quote_ident(schema_a)}.{quote_ident(tbl_a)}
  where {qa} is not null
),
B as (
  select distinct cast({qb} as string) as B_VALUE
  from {quote_ident(db_b)}.{quote_ident(schema_b)}.{quote_ident(tbl_b)}
  where {qb} is not null
),
pairs as (
  select A.A_VALUE, B.B_VALUE,
         JAROWINKLER_SIMILARITY(A.A_VALUE, B.B_VALUE) as SIMILARITY,
         row_number() over (partition by A.A_VALUE order by JAROWINKLER_SIMILARITY(A.A_VALUE, B.B_VALUE) desc) as RN
  from A join B
)
select A_VALUE, B_VALUE, SIMILARITY
from pairs
where RN <= {int(top_k)} and SIMILARITY >= {threshold}
"""
    run_exec(conn, sql)


def preview_fuzzy_mapping_table(conn, field_name: str, limit: int = 100) -> pd.DataFrame:
    tmp_table = f"TMP_FUZZY_MAP_{field_name.upper()}"
    q = f"select A_VALUE, B_VALUE, SIMILARITY from {quote_ident(tmp_table)} order by SIMILARITY desc limit {int(limit)}"
    return run_query_df(conn, q)


###############################################################################
# App Execution
###############################################################################


conn = connection_sidebar()
if conn:
    picked = table_picker(conn)
    if picked:
        table_a, table_b = picked
        harmonization_workflow(conn, table_a, table_b)
else:
    st.info("Connect to Snowflake to begin.")



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
    page_title="Unmatched Records Reviewer",
    page_icon=None,
    layout="wide",
)

st.markdown(
    """
    <div class="sf-page-header">
      <h1>Unmatched Records Reviewer</h1>
      <p>Review and manage unmatched records from harmonization processes. Select records to keep as matches or choose alternative candidates.</p>
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
      
       /* --- SIMPLIFIED DROPDOWN SIZING (REMOVED HARDCODED WIDTH) --- */
       
       /* Target the review section to scope the styles */
       .review-section {
         width: 100%;
       }

       /* Only apply the width fixes to the POPUP/LISTBOX not the selectbox itself */
       .review-section div[data-baseweb="popover"] [role="listbox"] {
         width: auto !important;
         min-width: 400px !important; /* Ensure minimum size for the list options */
         max-width: 800px !important; /* Allow options to be very wide */
       }

       .review-section div[data-baseweb="popover"] [role="listbox"] li {
         white-space: normal !important;
         word-wrap: break-word !important;
         overflow: visible !important;
         min-width: 100% !important;
       }
      
      /* Target the specific multiselect by its aria-label for chips */
      [data-testid="stAppViewContainer"] div[aria-label="Select fields to concatenate and include in model inputs (from mapped fields present in both tables)"] div[data-baseweb="tag"],
      [data-testid="stAppViewContainer"] div[aria-label="Select fields to concatenate and include in model inputs (from mapped fields present in both tables)"] div[data-baseweb="tag"] * {
        color: #FFFFFF !important;
      }
      /* Ensure selected option text in that dropdown is white */
      div[data-baseweb="popover"] [role="listbox"] li[aria-selected="true"],
      div[data-baseweb="popover"] [role="listbox"] div[role="option"][aria-selected="true"],
      div[data-baseweb="popover"] [role="listbox"] li[aria-selected="true"] *,
      div[data-baseweb="popover"] [role="listbox"] div[role="option"][aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
      }
      
      
      /* Ensure all text in the app is dark, not white */
      [data-testid="stAppViewContainer"] .stMarkdown,
      [data-testid="stAppViewContainer"] .stMarkdown p,
      [data-testid="stAppViewContainer"] .stMarkdown div,
      [data-testid="stAppViewContainer"] .stMarkdown span,
      [data-testid="stAppViewContainer"] .stMarkdown strong,
      [data-testid="stAppViewContainer"] .stMarkdown b {
        color: #333333 !important;
      }
      
      /* Specific styling for table headers */
      .table-header {
        color: #333333 !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        min-width: fit-content !important;
      }
      
      /* Table cell content styling */
      .table-cell {
        white-space: nowrap !important;
        color: #333333 !important;
        min-width: fit-content !important;
      }
      
      /* Ensure table container allows horizontal scrolling */
      .table-container {
        overflow-x: auto !important;
        overflow-y: auto !important;
        max-height: 400px !important;
        border: 1px solid #ddd !important;
        padding: 10px !important;
        border-radius: 5px !important;
      }
      
      /* Ensure columns don't shrink */
      .stColumn {
        min-width: fit-content !important;
        flex-shrink: 0 !important;
      }
    </style>
    <script>
      (function() {
        // Only keep the function to ensure selected text is white/bold
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
            
            // NEW: Ensure all selectbox elements get the title attribute for native tooltips
            // This relies on the new row-based layout giving the dropdown enough space.
            document.querySelectorAll('.review-section div[data-baseweb="select"]').forEach(function(selectbox) {
              const combobox = selectbox.querySelector('div[role="combobox"]');
              if (combobox) {
                const displayedText = combobox.textContent || combobox.innerText;
                const match = displayedText.match(/^\d+:\s*(.+)$/);
                const titleText = match ? match[1].trim() : displayedText.trim();
                
                // Set title on the main input elements for native tooltip
                if (titleText) {
                  selectbox.setAttribute('title', titleText);
                  combobox.setAttribute('title', titleText);
                  selectbox.querySelector('input')?.setAttribute('title', titleText);
                }
              }
            });
            
          } catch (e) {}
        }
        
        // Initial apply and observe DOM changes to re-apply
        applyWhiteForSelected();
        
        // Use a single MutationObserver to handle DOM changes
        const observer = new MutationObserver(function() {
          applyWhiteForSelected();
        });
        observer.observe(document.body, { 
          subtree: true, 
          childList: true, 
          attributes: true,
          characterData: true
        });
        
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
def list_schemas(_conn, database: str) -> List[str]:
    df = run_query_df(_conn, f"show schemas in {quote_ident(database)}")
    return [row[1] for _, row in df.iterrows()]


@st.cache_data(show_spinner=False)
def get_audit_table_mappings(_conn, database: str, schema: str) -> List[Dict[str, str]]:
    """
    Query the AUDIT_HARMONIZATION_HYBRID_AUDIT table to get unmatched/matched table pairs.
    Returns a list of dicts with 'unmatched' and 'matched' table names.
    """
    try:
        audit_table_fqn = fq_name(database, schema, "AUDIT_HARMONIZATION_HYBRID_AUDIT")
        query = f"""
        SELECT 
            UNMATCHED_TABLE_NAME,
            MATCHED_TABLE_NAME
        FROM {audit_table_fqn}
        WHERE UNMATCHED_TABLE_NAME IS NOT NULL 
          AND MATCHED_TABLE_NAME IS NOT NULL
        ORDER BY UNMATCHED_TABLE_NAME
        """
        df = run_query_df(_conn, query)
        
        # Convert to list of dicts
        mappings = []
        for _, row in df.iterrows():
            mappings.append({
                'unmatched': row['UNMATCHED_TABLE_NAME'],
                'matched': row['MATCHED_TABLE_NAME']
            })
        
        return mappings
    except Exception as e:
        st.error(f"Error querying audit table: {str(e)}")
        return []


def sql_string_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


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


def table_picker(conn) -> Optional[str]:
    with ui_card("1) Select Unmatched Records Table"):
        current_db = st.session_state.get("current_database")
        current_schema = st.session_state.get("current_schema")
        if not current_db or not current_schema:
            st.warning("Select a database and schema in the sidebar.")
            return None
        
        # Get unmatched/matched table pairs from audit table
        audit_mappings = get_audit_table_mappings(conn, current_db, current_schema)
        if not audit_mappings:
            st.info("No unmatched records tables found in audit table (AUDIT_HARMONIZATION_HYBRID_AUDIT).")
            return None
        
        # Extract just the unmatched table names for the dropdown
        unmatched_table_names = [mapping['unmatched'] for mapping in audit_mappings]
        
        selected_table = st.selectbox(
            "Unmatched Records Table", 
            unmatched_table_names, 
            key="unmatched_table_selector",
            help="Select a table containing unmatched records to review (from audit table)"
        )
        
        if selected_table:
            # Find the corresponding matched table name from the audit mappings
            matched_table = None
            for mapping in audit_mappings:
                if mapping['unmatched'] == selected_table:
                    matched_table = mapping['matched']
                    break
            
            # Add Process button
            if st.button("Process", type="primary"):
                st.session_state['selected_table_fqn'] = fq_name(current_db, current_schema, selected_table)
                st.session_state['matched_table_fqn'] = fq_name(current_db, current_schema, matched_table) if matched_table else None
                st.session_state['table_selected'] = True
                # Initialize search query state
                st.session_state['search_query'] = ""
                st.rerun()
            
            # Return the selected table if it's already been processed
            if st.session_state.get('table_selected') and st.session_state.get('selected_table_fqn'):
                return st.session_state['selected_table_fqn']
        
        return None


def get_matched_table_name(unmatched_table_name: str) -> str:
    """Convert unmatched table name to matched table name"""
    if unmatched_table_name.endswith("_UNMATCHED_RECORDS"):
        return unmatched_table_name.replace("_UNMATCHED_RECORDS", "_MATCHED_RECORDS")
    elif unmatched_table_name.endswith("_HYBRID_UNMATCHED"):
        return unmatched_table_name.replace("_HYBRID_UNMATCHED", "_HYBRID_MATCHED")
    elif "_UNMATCHED" in unmatched_table_name:
        return unmatched_table_name.replace("_UNMATCHED", "_MATCHED")
    return unmatched_table_name


def load_unmatched_data(conn, table_fqn: str, page: int = 1, page_size: int = 25) -> Tuple[pd.DataFrame, int]:
    """Load paginated unmatched records data with top 20 candidates and their similarities from hybrid_features"""
    offset = (page - 1) * page_size
    
    # Extract database and schema from table_fqn for hybrid_features lookup
    parts = table_fqn.replace('"', '').split('.')
    if len(parts) >= 3:
        db_schema_prefix = f'"{parts[0]}"."{parts[1]}".'
    else:
        db_schema_prefix = ""
    
    # Get total count
    count_sql = f"SELECT COUNT(*) as total FROM {table_fqn}"
    count_df = run_query_df(conn, count_sql)
    # Ensure total is a standard int
    total_records = int(count_df.iloc[0]['TOTAL']) if not count_df.empty else 0
    
    # Updated SQL to fetch candidate names AND their vector similarities as an array of objects
    data_sql = f"""
    WITH unmatched_page AS (
        SELECT 
            REFERENCE_ENTITY_NAME,
            FINAL_MATCH,
            ENHANCED_CONFIDENCE,
            VECTOR_SIMILARITY,
            REFERENCE_DETAIL_COLUMN,
            INPUT_DETAIL_COLUMN,
            ROW_NUMBER() OVER (ORDER BY ENHANCED_CONFIDENCE DESC) as rn
        FROM {table_fqn}
        ORDER BY ENHANCED_CONFIDENCE DESC
        LIMIT {page_size} OFFSET {offset}
    ),
    top_candidates AS (
        SELECT 
            hf.REF_RAW_NAME as REFERENCE_ENTITY_NAME,
            ARRAY_AGG(
                OBJECT_CONSTRUCT(
                    'name', hf.INP_RAW_NAME, 
                    'similarity', hf.vector_similarity
                )
            ) WITHIN GROUP (ORDER BY hf.vector_similarity DESC) as CANDIDATE_PAIRS
        FROM {db_schema_prefix}hybrid_features hf
        WHERE EXISTS (
            SELECT 1 FROM unmatched_page up 
            WHERE up.REFERENCE_ENTITY_NAME = hf.REF_RAW_NAME
            AND up.rn >= 1 AND up.rn <= {page_size}
        )
        GROUP BY hf.REF_RAW_NAME
        QUALIFY ROW_NUMBER() OVER (PARTITION BY hf.REF_RAW_NAME ORDER BY COUNT(*) DESC) = 1
    )
    SELECT 
        up.REFERENCE_ENTITY_NAME,
        up.FINAL_MATCH,
        up.ENHANCED_CONFIDENCE,
        up.VECTOR_SIMILARITY,
        up.REFERENCE_DETAIL_COLUMN,
        up.INPUT_DETAIL_COLUMN,
        ARRAY_SLICE(tc.CANDIDATE_PAIRS, 0, 20) as CANDIDATE_PAIRS  -- Slice the array of objects
    FROM unmatched_page up
    LEFT JOIN top_candidates tc ON up.REFERENCE_ENTITY_NAME = tc.REFERENCE_ENTITY_NAME
    ORDER BY up.rn ASC
    """
    
    data_df = run_query_df(conn, data_sql)
    return data_df, total_records


def process_keep_matches(conn, unmatched_table_fqn: str, selected_indices: List[int], page: int = 1, page_size: int = 25):
    """Process selected records to move from unmatched to matched table"""
    if not selected_indices:
        st.warning("No records selected to keep as matches.")
        return
    
    # Calculate the actual row indices in the database
    offset = (page - 1) * page_size
    actual_indices = [idx + offset for idx in selected_indices]
    
    # Get the selected records
    indices_str = ','.join(map(str, actual_indices))
    select_sql = f"""
    SELECT *
    FROM {unmatched_table_fqn}
    WHERE ROW_NUMBER() OVER (ORDER BY ENHANCED_CONFIDENCE DESC) IN ({indices_str})
    """
    
    selected_records = run_query_df(conn, select_sql)
    
    if selected_records.empty:
        st.error("No records found to process.")
        return
    
    # Get matched table FQN from session state (set in table_picker from audit table)
    matched_table_fqn = st.session_state.get('matched_table_fqn')
    
    if not matched_table_fqn:
        st.error("Matched table not found. Please re-select the unmatched table.")
        return
    
    try:
        # Insert into matched table
        insert_sql = f"""
        INSERT INTO {matched_table_fqn}
        SELECT * FROM ({select_sql})
        """
        run_exec(conn, insert_sql)
        
        # Delete from unmatched table
        delete_sql = f"""
        DELETE FROM {unmatched_table_fqn}
        WHERE ROW_NUMBER() OVER (ORDER BY ENHANCED_CONFIDENCE DESC) IN ({indices_str})
        """
        run_exec(conn, delete_sql)
        
        st.success(f"Successfully moved {len(selected_records)} records to matched table.")
        
        # Clear session state to refresh data
        if 'unmatched_data' in st.session_state:
            del st.session_state['unmatched_data']
        if 'total_records' in st.session_state:
            del st.session_state['total_records']
            
    except Exception as e:
        st.error(f"Error processing records: {str(e)}")


def get_candidate_similarities(conn, reference_entity_name: str, candidate_names: List[str]) -> List[Tuple[str, float]]:
    """Get vector similarity scores for candidates against reference name"""
    if not candidate_names or not reference_entity_name:
        return []
    
    # Limit to first 20 candidates to avoid query size issues
    limited_candidates = candidate_names[:20]
    
    # Create a temporary table with candidates and calculate similarities
    candidates_str = "', '".join([name.replace("'", "''") for name in limited_candidates])
    
    similarity_sql = f"""
    WITH candidates AS (
        SELECT VALUE as candidate_name
        FROM TABLE(FLATTEN(ARRAY_CONSTRUCT('{candidates_str}')))
    )
    SELECT 
        candidate_name,
        VECTOR_COSINE_SIMILARITY(
            SNOWFLAKE.CORTEX.EMBED_TEXT_1024('voyage-multilingual-2', '{reference_entity_name.replace("'", "''")}'),
            SNOWFLAKE.CORTEX.EMBED_TEXT_1024('voyage-multilingual-2', candidate_name)
        ) as similarity_score
    FROM candidates
    ORDER BY similarity_score DESC
    LIMIT 10
    """
    
    try:
        similarity_df = run_query_df(conn, similarity_sql)
        return [(row['CANDIDATE_NAME'], row['SIMILARITY_SCORE']) for _, row in similarity_df.iterrows()]
    except Exception as e:
        st.warning(f"Error calculating similarities: {str(e)}")
        return [(name, 0.0) for name in limited_candidates[:10]]


def process_review_submissions(conn, table_fqn: str):
    """Process all review submissions and move records from unmatched to matched tables using SQL operations"""
    try:
        # Get all review selections from all pages
        all_selections = st.session_state.get('review_selections', {})
        
        # Get the matched table FQN from session state (set in table_picker from audit table)
        matched_table_fqn = st.session_state.get('matched_table_fqn')
        
        if not matched_table_fqn:
            st.error("❌ Matched table not found. Please re-select the unmatched table.")
            return
        
        # Extract just the table name for display purposes
        matched_table_name = matched_table_fqn.split('.')[-1].replace('"', '')
        unmatched_table_name = table_fqn.split('.')[-1].replace('"', '')
        
        # Collect records to move (those NOT marked as "match not found")
        records_to_move = []
        page_size = 10  # Must match the page size used in load_unmatched_data and review_workflow

        # Iterate over all stored selections
        for page_key, page_selections in all_selections.items():
            # Safely extract page number
            try:
                page_num = int(page_key.split('_')[1])
            except (IndexError, ValueError):
                continue
            
            # Load the specific page data to map index back to REFERENCE_ENTITY_NAME
            page_data, _ = load_unmatched_data(conn, table_fqn, page_num, page_size) 

            for key, value in page_selections.items():
                if key.startswith('match_approved_'):
                    record_key_parts = key.split('_')
                    # The index is the last part of the key
                    try:
                        idx = int(record_key_parts[-1])
                    except (IndexError, ValueError):
                         continue
                    
                    # Check if this record is approved
                    if value:
                        # This record is approved for moving
                        selected_match_key = f'selected_match_{page_num}_{idx}'
                        
                        if selected_match_key in page_selections:
                            selected_match = page_selections[selected_match_key]
                            
                            if not page_data.empty and idx < len(page_data):
                                ref_name = page_data.iloc[idx]['REFERENCE_ENTITY_NAME']
                                ref_detail = page_data.iloc[idx]['REFERENCE_DETAIL_COLUMN']
                                
                                # Store the reference name, detail column, and the selected match
                                records_to_move.append({
                                    'reference_entity_name': ref_name,
                                    'reference_detail_column': ref_detail,
                                    'selected_match': selected_match
                                })
        
        if not records_to_move:
            st.warning("⚠️ No records approved for moving to matched table. Please check the '✅ Match Approved' box for records you want to move.")
            return

        # Create mapping for SQL updates
        ref_name_to_selected_match = {r['reference_entity_name']: r['selected_match'] for r in records_to_move}
        ref_names_to_move = [r['reference_entity_name'] for r in records_to_move]
        
        # Build SQL-safe list of reference names for WHERE IN clause
        ref_names_sql_list = ', '.join([sql_string_literal(name) for name in ref_names_to_move])
        
        # Step 1: Ensure matched table exists with same structure as unmatched table
        try:
            # Check if matched table exists
            db, schema, table = parse_fq_table_name(matched_table_fqn)
            unquoted_db = db.strip('"')
            unquoted_schema = schema.strip('"')
            unquoted_table = table.strip('"')
            
            table_exists_sql = f"""
            SELECT COUNT(*) as table_count 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = {sql_string_literal(unquoted_schema)} 
            AND TABLE_NAME = {sql_string_literal(unquoted_table)}
            AND TABLE_CATALOG = {sql_string_literal(unquoted_db)}
            """
            
            result_df = run_query_df(conn, table_exists_sql)
            table_exists = int(result_df.iloc[0, 0]) > 0 if not result_df.empty else False
            
            if not table_exists:
                # Create matched table with same structure as unmatched
                create_matched_sql = f"CREATE TABLE {matched_table_fqn} LIKE {table_fqn}"
                run_exec(conn, create_matched_sql)
                st.info(f"Created matched table: {matched_table_name}")
        except Exception as e:
            st.error(f"Error creating matched table: {str(e)}")
            return
        
        # Step 2: Get column list from unmatched table to preserve structure
        try:
            columns_query = f"SELECT * FROM {table_fqn} LIMIT 0"
            columns_df = run_query_df(conn, columns_query)
            all_columns = list(columns_df.columns)
        except Exception as e:
            st.error(f"Error getting table structure: {str(e)}")
            return
        
        # Step 3: Build UPDATE cases for FINAL_MATCH column
        update_cases = []
        for ref_name, selected_match in ref_name_to_selected_match.items():
            escaped_ref_name = ref_name.replace("'", "''")
            escaped_selected_match = selected_match.replace("'", "''")
            update_cases.append(f"WHEN '{escaped_ref_name}' THEN '{escaped_selected_match}'")
        
        update_case_statement = '\n'.join(update_cases)
        
        # Step 4: Build SELECT list with FINAL_MATCH updated
        select_columns = []
        for col in all_columns:
            if col.upper() == 'FINAL_MATCH':
                select_columns.append(f"""
                    CASE REFERENCE_ENTITY_NAME
                        {update_case_statement}
                    END as {quote_ident(col)}
                """)
            else:
                select_columns.append(quote_ident(col))
        
        select_list = ',\n            '.join(select_columns)
        
        # Step 5: Insert records into matched table with updated FINAL_MATCH
        insert_matched_sql = f"""
        INSERT INTO {matched_table_fqn}
        SELECT 
            {select_list}
        FROM {table_fqn}
        WHERE REFERENCE_ENTITY_NAME IN ({ref_names_sql_list})
        """
        
        try:
            run_exec(conn, insert_matched_sql)
            records_moved = len(records_to_move)
        except Exception as e:
            st.error(f"❌ Error inserting into matched table: {str(e)}")
            return
        
        # Step 4: Delete moved records from unmatched table
        delete_unmatched_sql = f"""
        DELETE FROM {table_fqn}
        WHERE REFERENCE_ENTITY_NAME IN ({ref_names_sql_list})
        """
        
        try:
            run_exec(conn, delete_unmatched_sql)
            
            # Get remaining count
            count_df = run_query_df(conn, f"SELECT COUNT(*) as cnt FROM {table_fqn}")
            # Handle case-insensitive column names
            count_col = [col for col in count_df.columns if col.upper() == 'CNT'][0]
            remaining_count = int(count_df.iloc[0][count_col])
            
        except Exception as e:
            st.error(f"❌ Error deleting from unmatched table: {str(e)}")
            return
        
        # Store summary in session state instead of immediately rerunning
        st.session_state['submission_complete'] = True
        st.session_state['submission_summary'] = {
            'records_moved': records_moved,
            'remaining_count': remaining_count,
            'matched_table_name': matched_table_name,
            'unmatched_table_name': unmatched_table_name,
            'moved_records': records_to_move  # Store details for summary display
        }
        
        # Don't rerun yet - let the UI show the summary first
        
    except Exception as e:
        st.error(f"❌ Error processing review submissions: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")


def load_all_unmatched_data(conn, table_fqn: str) -> pd.DataFrame:
    """
    DEPRECATED: Replaced by calling load_unmatched_data(conn, table_fqn, 1, page_size=large_number).
    This function is kept for consistency but not used in the final version's processing logic.
    """
    try:
        # Load all records, sorted by confidence to match the pagination order
        sql = f"SELECT * FROM {table_fqn} ORDER BY ENHANCED_CONFIDENCE DESC"
        
        # Use run_query_df to handle both connector and Snowpark session
        return run_query_df(conn, sql)
        
    except Exception as e:
        st.error(f"Error loading all unmatched data: {str(e)}")
        return pd.DataFrame()


def create_or_append_matched_table(conn, matched_table_fqn: str, df_matched: pd.DataFrame):
    """Create or append to matched table with the updated records"""
    if df_matched.empty:
        return
        
    try:
        # Check if matched table exists
        db, schema, table = parse_fq_table_name(matched_table_fqn)
        
        # Remove surrounding quotes from the name parts for INFORMATION_SCHEMA lookup
        unquoted_db = db.strip('"')
        unquoted_schema = schema.strip('"')
        unquoted_table = table.strip('"')

        table_exists_sql = f"""
        SELECT COUNT(*) as table_count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = {sql_string_literal(unquoted_schema)} 
        AND TABLE_NAME = {sql_string_literal(unquoted_table)}
        AND TABLE_CATALOG = {sql_string_literal(unquoted_db)}
        """
        
        result_df = run_query_df(conn, table_exists_sql)
        table_exists = int(result_df.iloc[0, 0]) > 0 if not result_df.empty else False
        
        values_string = build_values_string(df_matched)

        if table_exists:
            # Append to existing table
            # Need to specify columns for INSERT to ensure column order matches
            columns = ', '.join([quote_ident(c) for c in df_matched.columns])
            append_sql = f"INSERT INTO {matched_table_fqn} ({columns}) SELECT * FROM VALUES {values_string}"
            run_exec(conn, append_sql)
        else:
            # Create new table
            # This relies on the VALUES being correctly mapped to columns
            create_sql = f"CREATE TABLE {matched_table_fqn} AS SELECT * FROM VALUES {values_string}"
            run_exec(conn, create_sql)
            
    except Exception as e:
        st.error(f"Error creating/updating matched table: {str(e)}")


def update_unmatched_table(conn, unmatched_table_fqn: str, df_unmatched: pd.DataFrame):
    """Update unmatched table by replacing it with remaining records"""
    try:
        # Create temporary table name
        db, schema, table = parse_fq_table_name(unmatched_table_fqn)
        temp_table = f"{db}.{schema}.{table}_TEMP_{os.getpid()}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # If no records remain, create an empty table with the correct schema
        if df_unmatched.empty:
            create_temp_sql = f"CREATE OR REPLACE TABLE {temp_table} LIKE {unmatched_table_fqn}"
        else:
            values_string = build_values_string(df_unmatched)
            create_temp_sql = f"CREATE OR REPLACE TABLE {temp_table} AS SELECT * FROM VALUES {values_string}"
        
        run_exec(conn, create_temp_sql)
        
        # Replace original table
        replace_sql = f"CREATE OR REPLACE TABLE {unmatched_table_fqn} AS SELECT * FROM {temp_table}"
        run_exec(conn, replace_sql)
        
        # Drop temp table
        drop_temp_sql = f"DROP TABLE {temp_table}"
        run_exec(conn, drop_temp_sql)
        
    except Exception as e:
        st.error(f"Error updating unmatched table: {str(e)}")


def build_values_string(df: pd.DataFrame) -> str:
    """
    Build VALUES string for SQL INSERT/CREATE statements.
    
    Fixed the Python SyntaxError by using triple quotes for the f-string
    containing the complex PARSE_JSON call.
    """
    values_list = []
    
    # Get column names for the SQL VALUES format header
    column_names = df.columns
    
    for _, row in df.iterrows():
        row_values = []
        for i, value in enumerate(row):
            if pd.isna(value) or value is None:
                row_values.append("NULL")
            elif isinstance(value, (str, bytes)):
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                escaped_value = value.replace("'", "''")
                # Use double quotes for the f-string
                row_values.append(f"'{escaped_value}'") 
            elif isinstance(value, datetime.datetime):
                 # Use double quotes for the f-string
                 row_values.append(f"'{value.isoformat()}'")
            # Handle Snowflake ARRAY types (represented as lists/tuples/arrays in pandas when loaded)
            elif isinstance(value, (list, tuple, set, pd.Series)) or (isinstance(value, str) and value.startswith('[')):
                try:
                    # Attempt to dump to JSON for ARRAY type in Snowflake
                    json_dump = json.dumps(list(value))
                    
                    # FIX: Use TRIPLE single quotes for the OUTER f-string to safely contain 
                    # both double quotes ("") and the inner single quote (') for the SQL string literal.
                    row_values.append(f'''PARSE_JSON('{json_dump.replace("'", "''")}')''')
                except TypeError:
                    # Fallback for complex/non-serializable types
                    row_values.append("NULL")
            else:
                row_values.append(str(value))
        values_list.append(f"({', '.join(row_values)})")
    
    # Return the format (col1 type, col2 type) (val1, val2), (val3, val4)
    cols_string = ", ".join([f"{quote_ident(c)} VARIANT" for c in column_names]) # Use VARIANT as a generic type hint
    
    return f"({cols_string}) {', '.join(values_list)}"


def review_workflow(conn, table_fqn: str):
    # Initialize search state if not present
    if 'search_query' not in st.session_state:
        st.session_state['search_query'] = ""
    
    # Check if submission is complete and show summary
    if st.session_state.get('submission_complete', False):
        with ui_card("✅ Submission Complete - Review Summary"):
            summary = st.session_state.get('submission_summary', {})
            
            st.success("**Records Successfully Processed!**")
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Records Moved to Matched", summary.get('records_moved', 0))
            with col2:
                st.metric("Records Remaining", summary.get('remaining_count', 0))
            with col3:
                completion_pct = 100 if summary.get('remaining_count', 0) == 0 else round(
                    (summary.get('records_moved', 0) / (summary.get('records_moved', 0) + summary.get('remaining_count', 0))) * 100, 1
                )
                st.metric("Completion %", f"{completion_pct}%")
            
            st.markdown("---")
            
            # Show details of moved records
            st.subheader("📋 Moved Records Details")
            moved_records = summary.get('moved_records', [])
            
            if moved_records:
                # Create a nice display of moved records
                moved_df = pd.DataFrame([
                    {
                        'Reference Entity': r['reference_entity_name'][:50] + '...' if len(r['reference_entity_name']) > 50 else r['reference_entity_name'],
                        'Selected Match': r['selected_match'][:50] + '...' if len(r['selected_match']) > 50 else r['selected_match'],
                    }
                    for r in moved_records[:20]  # Show first 20
                ])
                
                st.dataframe(moved_df, use_container_width=True, hide_index=True)
                
                if len(moved_records) > 20:
                    st.info(f"Showing first 20 of {len(moved_records)} moved records")
            
            st.markdown("---")
            
            # Show table information
            st.subheader("📊 Table Information")
            st.markdown(f"""
            - **Matched Table**: `{summary.get('matched_table_name', 'N/A')}`
            - **Unmatched Table**: `{summary.get('unmatched_table_name', 'N/A')}`
            """)
            
            if summary.get('remaining_count', 0) == 0:
                st.success("**All records have been processed!** The unmatched table is now empty.")
            else:
                st.info(f"💡 **{summary.get('remaining_count', 0)} records remain** in the unmatched table for further review.")
            
            st.markdown("---")
            
            # "Continue with Analysis" button
            st.markdown("### 🔄 Ready to Continue?")
            st.markdown("Click the button below to continue reviewing remaining records or refresh the view.")
            
            if st.button("📑 Continue with Analysis", type="primary", use_container_width=True):
                # Clear submission state
                st.session_state['submission_complete'] = False
                st.session_state['submission_summary'] = {}
                st.session_state['review_selections'] = {}
                st.session_state['current_page'] = 1
                st.rerun()
            
        return  # Exit early to show summary instead of review interface
    
    with ui_card("2) Review Unmatched Records"):
        # Add CSS class for styling
        st.markdown('<div class="review-section">', unsafe_allow_html=True)
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 1
        if 'review_selections' not in st.session_state:
            st.session_state['review_selections'] = {}  # Store user selections across pages
        
        page_size = 10
        current_page = st.session_state['current_page']
        
        # Load ALL data for the current table (needed for client-side filtering/search)
        with st.spinner("Loading all unmatched records for search/pagination..."):
            all_data_df, total_records = load_unmatched_data(conn, table_fqn, 1, page_size=1000000) 
        
        # Filter data based on search query (Client-side filtering for simplicity)
        st.session_state['search_query'] = st.text_input(
            "Search Reference Records for a Specific Text", 
            value=st.session_state['search_query'],
            placeholder="Filter by Reference Record (space-specific)...",
            key="record_search_input"
        )
        
        search_query = st.session_state['search_query'].strip()  # Keep original case and spaces
        filtered_df = all_data_df
        
        if search_query:
            # Space-specific exact substring search (case-insensitive) on Reference Record only
            search_query_lower = search_query.lower()
            filtered_df = all_data_df[
                all_data_df['REFERENCE_ENTITY_NAME'].str.lower().str.contains(search_query_lower, regex=False, na=False)
            ]
        
        total_filtered_records = len(filtered_df)
        total_pages = (total_filtered_records + page_size - 1) // page_size
        
        # Ensure current page is valid after filtering/search
        if current_page > total_pages and total_pages > 0:
            st.session_state['current_page'] = total_pages
            current_page = total_pages
        elif total_pages == 0 and total_filtered_records > 0: # Should not happen if filtered_records > 0
            st.session_state['current_page'] = 1
            current_page = 1
        elif total_pages == 0:
            st.info("No records match the current search criteria.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Apply pagination to the filtered data
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        data_df = filtered_df.iloc[start_idx:end_idx].reset_index(drop=True)
        
        # --- Pagination Controls ---
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("← Previous", disabled=bool(current_page <= 1), key="prev_page"):
                st.session_state['current_page'] = current_page - 1
                st.rerun()
        
        with col2:
            st.write(f"Page **{current_page}** of **{total_pages}**")
        
        with col3:
            if st.button("Next →", disabled=bool(current_page >= total_pages), key="next_page"):
                st.session_state['current_page'] = current_page + 1
                st.rerun()
        
        with col4:
            st.write(f"Total Records: **{total_filtered_records}**")
        
        st.markdown("**Review unmatched records and check '✅ Match Approved' for records to move to the matched table.**")
        
        # Initialize selections for this page if not exists
        page_key = f"page_{current_page}"
        if page_key not in st.session_state['review_selections']:
            st.session_state['review_selections'][page_key] = {}
        # Display each record as a set of rows
        for idx, row in data_df.iterrows():
            st.markdown("---") # Visual separator between records
            
            record_key = f"{current_page}_{idx + start_idx}" # Use global index for unique state key
            
            # --- Checkbox and Reference Row ---
            with st.container():
                ref_cols = st.columns([1, 9])
                
                # Get current state
                default_match_approved = st.session_state['review_selections'][page_key].get(f"match_approved_{record_key}", False)
                
                # Match Approved Checkbox
                with ref_cols[0]:
                    match_approved = st.checkbox(
                        "✅ Match Approved", 
                        value=default_match_approved,
                        key=f"match_approved_{record_key}",
                        label_visibility="visible",
                        help="Check this box to approve and move this match to the matched table."
                    )
                    st.session_state['review_selections'][page_key][f"match_approved_{record_key}"] = match_approved
                
                # Reference Name (Remaining Width)
                with ref_cols[1]:
                    ref_text = row['REFERENCE_ENTITY_NAME']
                    st.markdown(f'**Reference Record:** {ref_text}')
                    
                # Store dynamic metrics for display below
                current_match_name = st.session_state['review_selections'][page_key].get(f"selected_match_{record_key}")
                
                # Default metrics are the original metrics
                original_similarity = row['VECTOR_SIMILARITY']
                current_detail = row['INPUT_DETAIL_COLUMN']
            
            # --- Selected Match Dropdown Row ---
            st.markdown('**Select Match Candidate:**')
            
            try:
                candidate_pairs = []
                if row['CANDIDATE_PAIRS']:
                    try:
                        # CANDIDATE_PAIRS is a list of objects (dicts) if loaded via snowpark/connector
                        if isinstance(row['CANDIDATE_PAIRS'], str):
                            candidate_pairs = json.loads(row['CANDIDATE_PAIRS'])
                        elif isinstance(row['CANDIDATE_PAIRS'], list):
                            candidate_pairs = row['CANDIDATE_PAIRS']
                    except:
                        # Fallback might be needed if complex objects fail to load
                        st.warning(f"Failed to parse candidate pairs for record {record_key}.")
                        candidate_pairs = []

                # Create lookup maps and lists
                candidate_scores = {}
                candidate_names = []
                for pair in candidate_pairs:
                    name = pair.get('name') or pair.get('NAME') # Handle potential capitalization inconsistency
                    sim = pair.get('similarity') or pair.get('SIMILARITY')
                    if name and sim is not None:
                        candidate_names.append(name)
                        candidate_scores[name] = sim
                
                top_20_candidates = candidate_names[:20]

                if top_20_candidates:
                    
                    # 1. Build candidates list with current match included
                    candidates_with_current = list(top_20_candidates)
                    is_current_match_candidate = row['FINAL_MATCH'] in top_20_candidates
                    
                    # Also check if the current match score is in the score map (should be)
                    if not is_current_match_candidate and row['FINAL_MATCH'] is not None:
                        candidates_with_current.insert(0, row['FINAL_MATCH'])
                        # Add original similarity to the lookup map if not present
                        if row['FINAL_MATCH'] not in candidate_scores:
                             candidate_scores[row['FINAL_MATCH']] = original_similarity

                    # 2. Determine default index based on current state
                    previous_selection_name = st.session_state['review_selections'][page_key].get(f"selected_match_{record_key}")
                    default_idx = 0
                    
                    if previous_selection_name in candidates_with_current:
                        default_idx = candidates_with_current.index(previous_selection_name)
                    elif row['FINAL_MATCH'] in candidates_with_current:
                        default_idx = candidates_with_current.index(row['FINAL_MATCH'])
                    
                    # 3. Create options for display
                    options = []
                    for i, candidate in enumerate(candidates_with_current):
                        prefix = str(i + 1)
                        if candidate == row['FINAL_MATCH'] and not is_current_match_candidate:
                             prefix = "0"
                        options.append(f"{prefix}: {candidate}")

                    # 4. Render the Selectbox
                    selected_option = st.selectbox(
                        f"Selected Match Dropdown {record_key}",
                        options,
                        index=default_idx,
                        key=f"selectbox_{record_key}",
                        label_visibility="collapsed",
                        help=candidates_with_current[default_idx] if candidates_with_current else ""
                    )
                    
                    # 5. Extract and store the full selected candidate name
                    # The index from the option string is reliable for looking up the score
                    option_prefix = selected_option.split(':')[0]
                    
                    if option_prefix == "0":
                        selected_candidate = row['FINAL_MATCH']
                        selected_score = candidate_scores.get(selected_candidate, original_similarity)
                    else:
                        selected_idx = int(option_prefix) - 1
                        selected_candidate = candidates_with_current[selected_idx]
                        selected_score = candidate_scores.get(selected_candidate)
                            
                    st.session_state['review_selections'][page_key][f"selected_match_{record_key}"] = selected_candidate
                    
                    # Use the dynamically selected score
                    display_similarity = f"{selected_score:.8f}" if selected_score is not None else "N/A (No Score)"

                else:
                    st.markdown(f'<span style="color:#000000">No candidates available</span>', unsafe_allow_html=True)
                    st.session_state['review_selections'][page_key][f"selected_match_{record_key}"] = row['FINAL_MATCH']
                    display_similarity = f"{original_similarity:.8f}"

            except Exception as e:
                st.error(f"Error loading candidates: {str(e)}")
                st.session_state['review_selections'][page_key][f"selected_match_{record_key}"] = row['FINAL_MATCH']
                display_similarity = f"{original_similarity:.8f}"


            # --- Dynamic Metrics Row ---
            st.markdown(
                f"""
                <div style="padding: 10px 0 5px 0; border: 1px dashed #DDD; border-radius: 6px; background-color: #FAFAFA; margin-top: 10px;">
                    <p style="margin: 0 10px; font-size: 0.9em; font-weight: 600; display: flex; justify-content: space-between; align-items: center;">
                        <span>Vector Similarity:</span>
                        <span style="font-size: 1.0em; color: #333; font-weight: 800;">{display_similarity}</span>
                    </p>                    
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Add navigation and summary section
        st.markdown("---")
        
        # Navigation buttons
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
        
        with nav_col1:
            if st.button("⏪ Jump to First Page", key="jump_to_first", type="primary"):
                st.session_state['current_page'] = 1
                st.rerun()
        
        with nav_col2:
            if st.button("⏩ Jump to Last Page", key="jump_to_last", type="primary"):
                st.session_state['current_page'] = total_pages
                st.rerun()
        
        with nav_col3:
            if current_page < total_pages:
                st.info(f"Page {current_page} of {total_pages}")
            else:
                st.success(f"Last page ({total_pages})")
        
        with nav_col4:
            st.write(f"Total Records: {total_filtered_records} (Filtered)")
        
        # Show summary of selections if we're on the last page
        if current_page >= total_pages:
            # Display summary of all selections
            st.markdown("### 📋 Review Summary")
            
            total_approved = 0
            
            # Recalculate based on current session state for all pages
            for page_key, page_selections in st.session_state['review_selections'].items():
                for key, value in page_selections.items():
                    if key.startswith('match_approved_'):
                        if value:  # Checkbox is checked = approved
                            total_approved += 1
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Records Approved to Move", total_approved)
            with col2:
                st.metric("Records Not Approved", total_filtered_records - total_approved)
        
        # Submit button (only on last page)
        if current_page >= total_pages:
            if st.button("Submit All Reviews", type="primary", key="submit_all_reviews"):
                with st.spinner("Processing all reviews..."):
                    try:
                        process_review_submissions(conn, table_fqn)
                        st.success("Reviews processed successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing reviews: {str(e)}")
        
        # Close the review-section div
        st.markdown('</div>', unsafe_allow_html=True)


###############################################################################
# App Execution
###############################################################################

conn = connection_sidebar()
if conn:
    selected_table = table_picker(conn)
    if selected_table and st.session_state.get('table_selected'):
        review_workflow(conn, selected_table)
    elif not st.session_state.get('table_selected'):
        st.info("Select an unmatched records table and click 'Process' to begin review.")
else:
    st.info("Connect to Snowflake to begin.")

"""
Cortex REST API Usage — Superset MCP Visualization (Streamlit companion app)

Standalone Streamlit app that:
  1. Queries SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
  2. Renders 5 interactive Vega-Lite charts locally (scatter, density, circle,
     trellis, multi-line) — parity with the original Vega-Lite quickstart
  3. Optionally calls Superset MCP tools to mirror the dashboard in Superset
  4. Optionally calls Cortex REST API (/api/v2/cortex/v1/chat/completions)
     to LLM-generate a Superset chart `params` JSON from a natural-language prompt

Runs in Streamlit in Snowflake (SiS) or locally with a Snowpark session.
"""

from __future__ import annotations

import json
import os
import pathlib
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


# ---------------------------------------------------------------------------
# Read the PAT (and host) straight from ~/.snowflake/config.toml so the app
# works out-of-the-box locally. SiS ignores this — session auth comes from
# get_active_session() and no PAT is needed for SQL.
# ---------------------------------------------------------------------------
def _load_connection(name: str) -> dict:
    cfg_path = pathlib.Path.home() / ".snowflake" / "config.toml"
    if not cfg_path.exists():
        return {}
    try:
        cfg = tomllib.loads(cfg_path.read_text())
        return cfg.get("connections", {}).get(name, {})
    except Exception:
        return {}


CONN_NAME = os.environ.get("SNOWFLAKE_CONNECTION_NAME", "myaccount")
CONN = _load_connection(CONN_NAME)

# ---------------------------------------------------------------------------
# Snowpark session — works in SiS (get_active_session) and locally (config)
# ---------------------------------------------------------------------------
try:
    from snowflake.snowpark.context import get_active_session
    SESSION = get_active_session()
    IN_SIS = True
except Exception:
    from snowflake.snowpark import Session
    SESSION = Session.builder.configs({
        "connection_name": os.environ.get("SNOWFLAKE_CONNECTION_NAME", "myaccount")
    }).create()
    IN_SIS = False

st.set_page_config(page_title="Cortex REST API Usage — Superset MCP", layout="wide")

st.title("Cortex REST API Usage Dashboard")
st.caption(
    "Data: `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY` "
    "(2h latency). Charts render locally via Vega-Lite and can be mirrored "
    "to Superset via MCP."
)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    days_back = st.slider("Days back", 1, 90, 30)
    max_rows = st.number_input("Row cap", 100, 100_000, 5_000, step=500)

    st.divider()
    st.header("Superset MCP")
    superset_url = st.text_input(
        "Superset URL",
        value=os.environ.get("SUPERSET_URL", "https://superset.example.com"),
    )
    superset_db_id = st.number_input("Superset database_id (Snowflake)", 1, 9999, 1)
    enable_mcp = st.checkbox("Enable Superset MCP actions", value=False)

    st.divider()
    st.header("Cortex REST API")
    # Show the connection name (not the raw host). The app resolves the real
    # host from the TOML connection's `account` field at request time.
    conn_label = st.text_input("Snowflake connection", value=CONN_NAME, disabled=True)
    cortex_model = st.selectbox(
        "Model",
        ["claude-sonnet-4-6", "openai-gpt-5.2", "openai-gpt-5.4", "openai-gpt-5-mini"],
        index=0,
    )
    pat_status = "loaded from config.toml" if CONN.get("password") else "NOT FOUND — set SNOWFLAKE_PAT"
    st.caption(f"PAT: {pat_status}")

# Derive the actual host from the named connection (account field in TOML).
# Users don't see this — only the connection label above.
CORTEX_HOST = (
    os.environ.get("SNOWFLAKE_HOST")
    or (f"{CONN['account']}.snowflakecomputing.com" if CONN.get("account") else None)
)

# ---------------------------------------------------------------------------
# Data load
# ---------------------------------------------------------------------------
# Ensure a warehouse is active. SiS already has one; local Snowpark sessions
# may not, so default to the user's account default.
WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "CORTEX_USAGE_WH")
try:
    SESSION.sql(f"USE WAREHOUSE {WAREHOUSE}").collect()
except Exception as e:
    st.sidebar.warning(f"Could not USE WAREHOUSE {WAREHOUSE}: {e}")

@st.cache_data(ttl=600)
def load_usage(days: int, cap: int) -> pd.DataFrame:
    sql = f"""
        SELECT
          START_TIME,
          DATE_TRUNC('day', START_TIME)::DATE  AS DAY,
          USER_ID,
          MODEL_NAME,
          TOKENS,
          REQUEST_ID
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
        WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
        ORDER BY START_TIME
        LIMIT {cap}
    """
    df = SESSION.sql(sql).to_pandas()
    df.columns = [c.lower() for c in df.columns]
    df["day"] = pd.to_datetime(df["day"]).dt.date
    return df

df = load_usage(days_back, int(max_rows))

if df.empty:
    st.warning("No rows in CORTEX_REST_API_USAGE_HISTORY for the selected window.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Requests", f"{len(df):,}")
col2.metric("Unique models", df["model_name"].nunique())
col3.metric("Total tokens", f"{int(df['tokens'].sum()):,}")

st.divider()

# ---------------------------------------------------------------------------
# Chart 1 — Scatter: tokens per request, colored by model
# ---------------------------------------------------------------------------
st.subheader("1. Tokens per request (scatter)")
scatter_df = df.reset_index().rename(columns={"index": "request_seq"})
st.vega_lite_chart(
    scatter_df,
    {
        "mark": {"type": "circle", "opacity": 0.7, "size": 60},
        "encoding": {
            "x": {"field": "request_seq", "type": "quantitative", "title": "Request #"},
            "y": {"field": "tokens", "type": "quantitative", "scale": {"type": "sqrt"}},
            "color": {"field": "model_name", "type": "nominal", "title": "Model"},
            "tooltip": [
                {"field": "day", "title": "Date"},
                {"field": "model_name", "title": "Model"},
                {"field": "tokens", "title": "Tokens", "format": ","},
                {"field": "request_id", "title": "Request ID"},
            ],
        },
        "height": 320,
    },
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Chart 2 — Stacked density / histogram of token sizes by model
# ---------------------------------------------------------------------------
st.subheader("2. Token-size distribution by model")
density_df = df[df["tokens"] <= 1000].copy()
st.vega_lite_chart(
    density_df,
    {
        "mark": {"type": "area", "opacity": 0.6, "interpolate": "monotone"},
        "transform": [
            {"density": "tokens", "groupby": ["model_name"], "as": ["value", "density"]},
        ],
        "encoding": {
            "x": {"field": "value", "type": "quantitative", "title": "Tokens per request (≤1K)"},
            "y": {"field": "density", "type": "quantitative", "stack": "zero"},
            "color": {"field": "model_name", "type": "nominal", "title": "Model"},
        },
        "height": 320,
    },
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Chart 3 — Circle plot: day × model, sized by total tokens
# ---------------------------------------------------------------------------
st.subheader("3. Daily usage by model (circle plot)")
circle_df = (
    df.groupby(["day", "model_name"], as_index=False)
      .agg(total_tokens=("tokens", "sum"), requests=("request_id", "count"))
)
st.vega_lite_chart(
    circle_df,
    {
        "mark": {"type": "circle", "opacity": 0.85},
        "encoding": {
            "x": {"field": "day", "type": "ordinal", "title": "Date"},
            "y": {"field": "model_name", "type": "nominal", "title": None},
            "size": {
                "field": "total_tokens",
                "type": "quantitative",
                "scale": {"range": [50, 1500]},
                "title": "Total tokens",
            },
            "color": {"field": "model_name", "type": "nominal", "legend": None},
            "tooltip": [
                {"field": "day", "title": "Date"},
                {"field": "model_name", "title": "Model"},
                {"field": "total_tokens", "title": "Total tokens", "format": ","},
                {"field": "requests", "title": "Requests"},
            ],
        },
        "height": 300,
    },
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Chart 4 — Trellis dot plot: one row per model
# ---------------------------------------------------------------------------
st.subheader("4. Per-request tokens, faceted by model (trellis dot plot)")
st.vega_lite_chart(
    df,
    {
        "mark": {"type": "circle", "opacity": 0.7, "size": 45},
        "encoding": {
            "row": {"field": "model_name", "type": "nominal", "title": None,
                    "header": {"labelAngle": 0, "labelAlign": "left"}},
            "x": {"field": "tokens", "type": "quantitative", "scale": {"type": "sqrt"}},
            "y": {"field": "day", "type": "ordinal", "title": None},
            "color": {"field": "model_name", "type": "nominal", "legend": None},
            "tooltip": [
                {"field": "day", "title": "Date"},
                {"field": "tokens", "title": "Tokens", "format": ","},
                {"field": "request_id", "title": "Request ID"},
            ],
        },
        "height": 90,
    },
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Chart 5 — Interactive multi-line: cumulative tokens per model
# ---------------------------------------------------------------------------
st.subheader("5. Cumulative tokens over time (interactive)")
cum_df = (
    df.groupby(["day", "model_name"], as_index=False)
      .agg(daily_tokens=("tokens", "sum"))
      .sort_values(["model_name", "day"])
)
cum_df["cumulative_tokens"] = cum_df.groupby("model_name")["daily_tokens"].cumsum()
st.vega_lite_chart(
    cum_df,
    {
        "mark": {"type": "line", "point": True, "interpolate": "monotone"},
        "encoding": {
            "x": {"field": "day", "type": "temporal", "title": "Date"},
            "y": {"field": "cumulative_tokens", "type": "quantitative", "title": "Cumulative tokens"},
            "color": {"field": "model_name", "type": "nominal", "title": "Model"},
            "tooltip": [
                {"field": "day", "type": "temporal", "title": "Date", "format": "%b %d"},
                {"field": "model_name", "title": "Model"},
                {"field": "cumulative_tokens", "title": "Cumulative", "format": ","},
            ],
        },
        "height": 360,
    },
    use_container_width=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Superset MCP mirror — illustrative payloads (tool names depend on your MCP)
# ---------------------------------------------------------------------------
st.header("Mirror to Superset via MCP")
st.caption(
    "These payloads show the shape of `superset_create_chart` / "
    "`superset_create_dashboard` calls that a Cortex Code session (or any MCP "
    "client) would make. The exact tool names depend on your Superset MCP "
    "server implementation."
)

chart_payloads = [
    {"slice_name": "Tokens per Request", "viz_type": "scatter",
     "params": {"x": "index", "y": "tokens", "color": "model_name"}},
    {"slice_name": "Token Size Distribution", "viz_type": "dist_bar",
     "params": {"metrics": ["count"], "groupby": ["model_name"], "columns": ["tokens"]}},
    {"slice_name": "Daily Usage by Model", "viz_type": "heatmap",
     "params": {"all_columns_x": "day", "all_columns_y": "model_name",
                "metric": "sum__tokens"}},
    {"slice_name": "Per-Request Tokens by Model", "viz_type": "dot_plot",
     "params": {"x": "tokens", "facet": "model_name", "y": "day"}},
    {"slice_name": "Cumulative Tokens", "viz_type": "line",
     "params": {"x": "day", "metrics": ["cum_sum__tokens"], "groupby": ["model_name"]}},
]

for p in chart_payloads:
    with st.expander(f"superset_create_chart — {p['slice_name']}"):
        st.code(json.dumps({
            "datasource_id": "<CORTEX_REST_API_USAGE_HISTORY dataset id>",
            "slice_name": p["slice_name"],
            "viz_type": p["viz_type"],
            "params": p["params"],
        }, indent=2), language="json")

if enable_mcp:
    st.info(
        "Register your Superset MCP server with:\n\n"
        "`cortex mcp add superset {url}/api/v1/mcp --transport http`\n\n"
        "Then run this app inside a Cortex Code session that has the Superset "
        "MCP tools loaded. The session can iterate over `chart_payloads` and "
        "call `superset_create_chart` for each one, then "
        "`superset_create_dashboard` to assemble them.".format(url=superset_url)
    )

st.divider()

# ---------------------------------------------------------------------------
# Cortex REST API — LLM-generated Superset chart config
# ---------------------------------------------------------------------------
st.header("LLM-generate a Superset chart config")
st.caption(
    "Describe a chart in natural language. Cortex REST API returns a JSON "
    "`params` object you can paste into `superset_create_chart`."
)

prompt_text = st.text_input(
    "Describe the chart",
    value="Stacked bar of daily tokens per model for the last 14 days.",
)

if st.button("Generate Superset params"):
    system = (
        "You are a Superset chart generator. Return ONLY a JSON object "
        "suitable for superset_create_chart's `params` field (no commentary, "
        "no code fences). Dataset columns: day (date), model_name (string), "
        "tokens (number), user_id (string), request_id (string). "
        "Required keys: viz_type, metrics, groupby, time_range."
    )
    if not CORTEX_HOST:
        st.error(
            f"Could not resolve a host for connection `{CONN_NAME}`. "
            "Set `account` under `[connections.<name>]` in ~/.snowflake/config.toml, "
            "or export SNOWFLAKE_HOST."
        )
        st.stop()
    url = f"https://{CORTEX_HOST}/api/v2/cortex/v1/chat/completions"
    # Prefer PAT from TOML; fall back to env var for CI/container runs.
    pat = CONN.get("password") or os.environ.get("SNOWFLAKE_PAT", "")
    if not pat:
        st.error(
            "No PAT available. Add one under "
            f"`[connections.{CONN_NAME}]` in ~/.snowflake/config.toml, or "
            "export SNOWFLAKE_PAT."
        )
        st.stop()
    headers = {
        "Authorization": f"Bearer {pat}",
        "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "model": cortex_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt_text},
        ],
        "max_completion_tokens": 800,
        "temperature": 0.0,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
            st.success("Valid JSON returned.")
            st.code(json.dumps(parsed, indent=2), language="json")
        except json.JSONDecodeError:
            st.warning("Model returned non-JSON. Raw:")
            st.code(content)
    except Exception as e:
        st.error(f"Cortex REST API call failed: {e}")

st.divider()
st.caption(
    "Next steps: wire `superset_create_chart` calls via MCP, then embed the "
    "resulting dashboard with `superset_get_dashboard_embed_token` and an "
    "iframe in Snowflake Intelligence, Slack, or a custom web app."
)

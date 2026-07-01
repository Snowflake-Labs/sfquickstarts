"""
CoCo Control Hub — Model Intelligence
======================================
Model health, drift detection, quality scoring, and usage trends.
Cross-model comparison: latency, quality scores, Prompt Insights, credit share.
Token Economics: input/output/cache token analysis by LLM.
"""

import altair as alt
import pandas as pd
import streamlit as st

from config import (
    TABLE_PROMPT_EVENTS,
    TABLE_PROMPT_VIOLATIONS,
    TABLE_RESPONSE_QUALITY,
    TABLE_USAGE_DAILY,
    TABLE_MODEL_CONFIG,
    SP_EVALUATE_RESPONSES,
    escape_sql_literal,
    fq_table,
    fq_sp,
    get_current_user,
)
from utils import get_app_setting, get_session

_BG = "#0e1117"
_P  = "#7dd3fc"
_G  = "#6ee7b7"
_A  = "#fcd34d"
_R  = "#fca5a5"
_W  = "#e2e8f0"

_EVAL_MODELS = [
    "claude-sonnet-4-5",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "snowflake-arctic-instruct",
]


def _fmt_tokens(n: int) -> str:
    """Abbreviated token count: 2.1M, 245K, etc."""
    if not n: return "0"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.0f}K"
    return f"{n:,}"


def _sec(title, help_text=None):
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def _load_latency_by_model(_session, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            SELECT
                EVENT_DATE,
                MODEL,
                ROUND(MEDIAN(LATENCY_MS) / 1000.0, 2)       AS P50_S,
                ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY LATENCY_MS) / 1000.0, 2) AS P95_S,
                ROUND(MAX(LATENCY_MS) / 1000.0, 2)           AS MAX_S,
                COUNT(*) AS PROMPT_COUNT
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND LATENCY_MS IS NOT NULL AND LATENCY_MS > 0
              AND MODEL IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 2
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            for _score_col in ["AVG_ANSWER_RELEVANCE","AVG_GROUNDEDNESS","AVG_COHERENCE","AVG_SAFETY"]:
                if _score_col in df.columns:
                    df[_score_col] = pd.to_numeric(df[_score_col], errors="coerce").fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_quality_by_model(_session, days: int):
    tbl = fq_table(_session, TABLE_RESPONSE_QUALITY)
    try:
        df = _session.sql(f"""
            SELECT
                MODEL,
                ROUND(AVG(ANSWER_RELEVANCE_SCORE), 3)  AS AVG_ANSWER_RELEVANCE,
                ROUND(AVG(GROUNDEDNESS_SCORE), 3)       AS AVG_GROUNDEDNESS,
                ROUND(AVG(COHERENCE_SCORE), 3)          AS AVG_COHERENCE,
                ROUND(AVG(SAFETY_SCORE), 3)             AS AVG_SAFETY,
                COUNT(*) AS EVALUATED_COUNT,
                MIN(EVALUATED_AT) AS FIRST_EVAL,
                MAX(EVALUATED_AT) AS LAST_EVAL
            FROM {tbl}
            WHERE RESPONSE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND MODEL IS NOT NULL
            GROUP BY 1
            ORDER BY AVG_ANSWER_RELEVANCE DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            for _sc in ["AVG_ANSWER_RELEVANCE","AVG_GROUNDEDNESS","AVG_COHERENCE","AVG_SAFETY"]:
                if _sc in df.columns:
                    df[_sc] = pd.to_numeric(df[_sc], errors="coerce").fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_quality_trend(_session, days: int):
    tbl = fq_table(_session, TABLE_RESPONSE_QUALITY)
    try:
        df = _session.sql(f"""
            SELECT
                RESPONSE_DATE,
                MODEL,
                ROUND(AVG(ANSWER_RELEVANCE_SCORE), 3) AS AVG_ANSWER_RELEVANCE,
                ROUND(AVG(GROUNDEDNESS_SCORE), 3)     AS AVG_GROUNDEDNESS,
                ROUND(AVG(COHERENCE_SCORE), 3)        AS AVG_COHERENCE,
                ROUND(AVG(SAFETY_SCORE), 3)           AS AVG_SAFETY,
                COUNT(*) AS EVALUATED_COUNT
            FROM {tbl}
            WHERE RESPONSE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND MODEL IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["RESPONSE_DATE"] = pd.to_datetime(df["RESPONSE_DATE"]).dt.date
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_violation_rate_by_model(_session, days: int):
    tv = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    te = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            -- Join violations to prompts via PROMPT_HASH for accurate model attribution.
            -- This avoids cross-model inflation where the same user+date violations
            -- are attributed to every model used that day.
            WITH viol_with_model AS (
                SELECT v.VIOLATION_ID, v.RISK_LEVEL, e.MODEL
                FROM {tv} v
                JOIN {te} e
                    ON  SHA2(e.PROMPT, 256) = v.PROMPT_HASH
                    AND v.USER_NAME         = e.USER_NAME
                    AND v.VIOLATION_DATE    = e.EVENT_DATE
                WHERE v.VIOLATION_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
                  AND e.MODEL IS NOT NULL
                  AND e.PROMPT IS NOT NULL
            ),
            viol_agg AS (
                SELECT MODEL,
                       COUNT(DISTINCT VIOLATION_ID)                                        AS VIOLATIONS,
                       COUNT(DISTINCT CASE WHEN RISK_LEVEL='HIGH'   THEN VIOLATION_ID END) AS HIGH_RISK,
                       COUNT(DISTINCT CASE WHEN RISK_LEVEL='MEDIUM' THEN VIOLATION_ID END) AS MED_RISK
                FROM viol_with_model
                GROUP BY 1
            ),
            prompt_agg AS (
                SELECT MODEL,
                       COUNT(DISTINCT REQUEST_ID) AS TOTAL_PROMPTS
                FROM {te}
                WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
                  AND MODEL IS NOT NULL
                GROUP BY 1
            )
            SELECT p.MODEL,
                   p.TOTAL_PROMPTS,
                   COALESCE(v.VIOLATIONS, 0)  AS VIOLATIONS,
                   ROUND(COALESCE(v.VIOLATIONS, 0) * 1000.0 /
                         NULLIF(p.TOTAL_PROMPTS, 0), 2)  AS VIOLATIONS_PER_1K,
                   COALESCE(v.HIGH_RISK, 0)   AS HIGH_RISK,
                   COALESCE(v.MED_RISK, 0)    AS MED_RISK
            FROM prompt_agg p
            LEFT JOIN viol_agg v ON v.MODEL = p.MODEL
            ORDER BY VIOLATIONS_PER_1K DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_violation_by_category(_session, days: int):
    """Insights per 1K prompts split by model AND category — via PROMPT_HASH join."""
    tv = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    te = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            WITH viol_with_model AS (
                SELECT v.VIOLATION_ID, v.RISK_LEVEL,
                       COALESCE(v.CATEGORY, 'UNKNOWN') AS CATEGORY,
                       e.MODEL
                FROM {tv} v
                JOIN {te} e
                    ON  SHA2(e.PROMPT, 256) = v.PROMPT_HASH
                    AND v.USER_NAME         = e.USER_NAME
                    AND v.VIOLATION_DATE    = e.EVENT_DATE
                WHERE v.VIOLATION_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
                  AND e.MODEL IS NOT NULL
                  AND e.PROMPT IS NOT NULL
                  AND v.CATEGORY IS NOT NULL
            ),
            prompt_agg AS (
                SELECT MODEL, COUNT(DISTINCT REQUEST_ID) AS PROMPT_COUNT
                FROM {te}
                WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
                  AND MODEL IS NOT NULL
                GROUP BY 1
            )
            SELECT vm.MODEL, vm.CATEGORY, vm.RISK_LEVEL,
                   COUNT(DISTINCT vm.VIOLATION_ID) AS VIOLATIONS,
                   p.PROMPT_COUNT                  AS TOTAL_PROMPTS,
                   ROUND(COUNT(DISTINCT vm.VIOLATION_ID) * 1000.0 /
                         NULLIF(p.PROMPT_COUNT, 0), 2) AS VIOLATIONS_PER_1K
            FROM viol_with_model vm
            JOIN prompt_agg p ON p.MODEL = vm.MODEL
            GROUP BY 1, 2, 3, p.PROMPT_COUNT
            ORDER BY vm.MODEL, VIOLATIONS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_usage_share(_session, days: int):
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    try:
        df = _session.sql(f"""
            SELECT USAGE_DATE, MODEL_NAME AS MODEL,
                   SUM(TOTAL_CREDITS) AS CREDITS,
                   SUM(QUERY_COUNT) AS QUERIES
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND MODEL_NAME IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"]).dt.date
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def _load_quality_stats(_session):
    tbl = fq_table(_session, TABLE_RESPONSE_QUALITY)
    try:
        r = _session.sql(f"SELECT COUNT(*) AS N, MAX(EVALUATED_AT) AS LAST FROM {tbl}").collect()
        return int(r[0][0] or 0), str(r[0][1] or "")[:19]
    except Exception:
        return 0, ""


@st.cache_data(ttl=300, show_spinner=False)
def _load_token_econ_by_model(_session, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            SELECT MODEL,
                   SUM(INPUT_TOKENS)       AS INPUT_T,
                   SUM(OUTPUT_TOKENS)      AS OUTPUT_T,
                   SUM(CACHE_READ_TOKENS)  AS CACHE_READ_T,
                   SUM(CACHE_WRITE_TOKENS) AS CACHE_WRITE_T,
                   SUM(TOTAL_TOKENS)       AS TOTAL_T,
                   COUNT(*)                AS QUERIES
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND MODEL IS NOT NULL
            GROUP BY 1 ORDER BY TOTAL_T DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def render(session):
    import json as _json
    st.header("Model Intelligence",
              help="Cross-model comparison: latency trends, quality scores, Prompt Insights, usage share. "
                   "Detect model drift, identify underperforming models, and track adoption.")

    # ── Data status + refresh panel ───────────────────────────────────────────
    with st.expander("Data sources & refresh", expanded=False):
        st.markdown("""
| Tab | Source table | Populated by | Schedule |
|-----|-------------|-------------|---------|
| LLM Latency | `CC_PROMPT_EVENTS` | `SP_CC_CLASSIFY_PROMPTS` | Nightly 2am UTC |
| Token Economics | `CC_PROMPT_EVENTS` | `SP_CC_CLASSIFY_PROMPTS` | Nightly 2am UTC |
| Violation Rates | `CC_PROMPT_VIOLATIONS` | `SP_CC_CLASSIFY_PROMPTS` | Nightly 2am UTC |
| Usage Share | `CC_USAGE_DAILY_SUMMARY` | `SP_CC_REFRESH_USAGE_SUMMARIES` | Every 30 min |
| LLM-as-Judge Evaluation | `CC_RESPONSE_QUALITY` | `SP_CC_EVALUATE_RESPONSES` | Manual / on demand |
""")
        st.caption("Run the buttons below to populate data immediately without waiting for scheduled tasks.")

        mi_backfill_days = st.selectbox(
            "Backfill window for Classify Prompts",
            options=[7, 14, 30, 60, 90, 180],
            index=2,
            format_func=lambda d: f"{d} days",
            key="mi_backfill_days",
            help="How far back SP_CC_CLASSIFY_PROMPTS will look for AI observability events. "
                 "SP uses a watermark so re-runs only process new data."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Run Classify Prompts", key="mi_run_classify",
                         help=f"Populates CC_PROMPT_EVENTS and CC_PROMPT_VIOLATIONS for the last {mi_backfill_days} days."):
                sp = fq_sp(session, "SP_CC_CLASSIFY_PROMPTS")
                lookback_h = mi_backfill_days * 24
                with st.spinner(f"Running SP_CC_CLASSIFY_PROMPTS({lookback_h})…"):
                    try:
                        r = session.sql(f"CALL {sp}({lookback_h})").collect()
                        res = _json.loads(r[0][0]) if r else {}
                        st.success(f"✓ {res.get('events_loaded',0)} events loaded, "
                                   f"{res.get('violations_found',0)} prompt insights found.")
                        for fn in [_load_latency_by_model, _load_violation_rate_by_model,
                                   _load_quality_by_model, _load_quality_trend, _load_usage_share,
                                   _load_quality_stats, _load_token_econ_by_model]:
                            fn.clear()
                    except Exception as e:
                        st.error(f"✗ {e}")

        with col2:
            if st.button("Refresh Usage Summaries", key="mi_run_usage",
                         help="Populates CC_USAGE_DAILY_SUMMARY for Usage Share tab."):
                sp = fq_sp(session, "SP_CC_REFRESH_USAGE_SUMMARIES")
                with st.spinner("Running SP_CC_REFRESH_USAGE_SUMMARIES…"):
                    try:
                        r = session.sql(f"CALL {sp}()").collect()
                        st.success(f"✓ {r[0][0] if r else 'OK'}")
                        _load_usage_share.clear()
                    except Exception as e:
                        st.error(f"✗ {e}")

        with col3:
            eval_model = get_app_setting(session, "EVAL_MODEL", "claude-sonnet-4-5")
            batch_size = int(get_app_setting(session, "EVAL_BATCH_SIZE", "200"))
            if st.button("Run Quality Evaluation", key="mi_run_eval",
                         help=f"Scores AI responses using {eval_model}. "
                              f"~{batch_size * 0.00005:.3f} credits for {batch_size} responses."):
                sp = fq_sp(session, SP_EVALUATE_RESPONSES)
                safe_model = escape_sql_literal(eval_model)
                with st.spinner(f"Evaluating up to {batch_size} responses…"):
                    try:
                        r = session.sql(f"CALL {sp}({batch_size}, '{safe_model}')").collect()
                        res = _json.loads(r[0][0]) if r else {}
                        evaluated = res.get("evaluated", 0)
                        if evaluated:
                            st.success(f"✓ {evaluated} responses scored.")
                        else:
                            st.info(res.get("message", "No new responses to evaluate. "
                                            "Run Classify Prompts first to load response data."))
                        for fn in [_load_quality_by_model, _load_quality_trend, _load_quality_stats]:
                            fn.clear()
                    except Exception as e:
                        st.error(f"✗ {e}")

    st.divider()

    days = st.selectbox("Lookback", [7, 14, 30, 90], index=2,
                        key="mi_days", label_visibility="collapsed",
                        help="Days of history for all charts.")

    tab_latency, tab_token_econ, tab_quality, tab_violations, tab_usage = st.tabs([
        "LLM Latency", "Token Economics (Experimental)", "Custom Quality (Experimental)", "Prompt Insights", "Usage Share"
    ])

    active_days = days

    # ── LLM Latency ─────────────────────────────────────────────────────────────
    with tab_latency:
        st.caption("LLM response time per model, computed from CC_PROMPT_EVENTS. P50 = typical user experience; P95 = worst-case for 1 in 20 calls. Spikes in P95 often indicate model load or token-limit events.")
        lat = _load_latency_by_model(session, active_days)
        if lat.empty:
            st.info("No latency data available. CC_PROMPT_EVENTS must be populated (run SP_CC_CLASSIFY_PROMPTS).")
        else:
            overall_p50 = round(lat["P50_S"].mean(), 2)
            overall_p95 = round(lat["P95_S"].mean(), 2)
            worst_model = lat.groupby("MODEL")["P95_S"].mean().idxmax()
            worst_p95   = round(lat.groupby("MODEL")["P95_S"].mean().max(), 2)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("LLM Avg P50 Latency", f"{overall_p50}s", help="Median LLM latency across all models.")
            k2.metric("LLM Avg P95 Latency", f"{overall_p95}s", help="95th percentile LLM latency across all models.")
            k3.metric("Slowest LLM (P95)", worst_model, help="LLM model with highest P95 latency.")
            k4.metric("Slowest P95", f"{worst_p95}s", help="P95 latency for the slowest LLM model.")

            st.divider()

            _sec("LLM P50 Latency by Model Over Time")
            p50_melt = lat[["EVENT_DATE","MODEL","P50_S"]].copy()
            p50_melt["EVENT_DATE"] = p50_melt["EVENT_DATE"].astype(str)
            ch = (alt.Chart(p50_melt).mark_line(point=True)
                  .encode(
                      x=alt.X("EVENT_DATE:T", title=""),
                      y=alt.Y("P50_S:Q", title="P50 Latency (s)"),
                      color=alt.Color("MODEL:N", legend=alt.Legend(title="")),
                      tooltip=["EVENT_DATE:T","MODEL:N",
                               alt.Tooltip("P50_S:Q", title="P50 (s)", format=".2f")])
                  .properties(height=240)
                  .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch, use_container_width=True)

            _sec("LLM P95 Latency by Model (Spike Detection)")
            p95_melt = lat[["EVENT_DATE","MODEL","P95_S"]].copy()
            p95_melt["EVENT_DATE"] = p95_melt["EVENT_DATE"].astype(str)
            ch2 = (alt.Chart(p95_melt).mark_area(opacity=0.5)
                   .encode(
                       x=alt.X("EVENT_DATE:T", title=""),
                       y=alt.Y("P95_S:Q", title="P95 Latency (s)", stack=None),
                       color=alt.Color("MODEL:N", legend=alt.Legend(title="")),
                       tooltip=["EVENT_DATE:T","MODEL:N",
                                alt.Tooltip("P95_S:Q", title="P95 (s)", format=".2f")])
                   .properties(height=200)
                   .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch2, use_container_width=True)

            _sec("LLM Per-Model Summary Table")
            st.caption("P50 = median response time for that model — what a typical user experiences. "
                       "P95 = slowest 5% of responses — worst-case performance. "
                       "High P95 vs P50 means occasional severe slowdowns. Total Prompts = all LLM calls in this period.")
            summary = (lat.groupby("MODEL")
                         .agg(P50=("P50_S","mean"), P95=("P95_S","mean"),
                              MAX=("MAX_S","max"), PROMPTS=("PROMPT_COUNT","sum"))
                         .round(2).reset_index().sort_values("P95", ascending=False))
            st.dataframe(summary, use_container_width=True, hide_index=True,
                         column_config={
                             "MODEL":   st.column_config.TextColumn("Model"),
                             "P50":     st.column_config.NumberColumn("P50 (s)", format="%.2f"),
                             "P95":     st.column_config.NumberColumn("P95 (s)", format="%.2f"),
                             "MAX":     st.column_config.NumberColumn("Max (s)", format="%.2f"),
                             "PROMPTS": st.column_config.NumberColumn("Total Prompts", format="%.0f"),
                         })

    # ── Token Economics ─────────────────────────────────────────────────────────
    with tab_token_econ:
        st.warning(
            "⚗️ **Experimental — Token Economics.** Token counts are extracted from "
            "`AI_OBSERVABILITY_EVENTS` via `SP_CC_CLASSIFY_PROMPTS` and cover `CodingAgent.Step-0` "
            "planning spans only. Cache Hit Rate is approximate — field semantics may vary by account. "
            "Use as a directional signal, not as official Snowflake billing data."
        )
        with st.expander("What do these token metrics mean?", expanded=False):
            st.markdown("""
| Metric | What it is | What to expect for Cortex Code |
|---|---|---|
| **Input tokens** | Fresh prompt tokens processed from scratch — your question, conversation history, open files, tool definitions | Largest share (~50%). Cortex Code sends large context windows per step. |
| **Output tokens** | Tokens the LLM *generated* in its response | Appears very small (~0.1–2%). Each `Step-0` span is a planning step — most output is short tool-selection decisions, not full responses. |
| **Cache Read** | Tokens your prompt contained that were served from Snowflake's prompt cache — NOT re-processed | High is good (>20% = significant credit savings). System prompts, skill instructions, and file context get cached after first call. |
| **Cache Write** | Tokens being written INTO the cache for the first time | Expected 10–15%. These cost slightly more on first call but save credits on future cache reads. |

**Cache Hit Rate** = `cache_read / (cache_read + cache_write)` × 100. This is the standard cache hit ratio: hits ÷ (hits + misses). `cache_write` = cache miss (had to write fresh), `cache_read` = cache hit (served from cache at 10× lower cost). Fresh `input_tokens` are not part of the cache system and are excluded from this ratio.

> **Note on 100% cache hit rate:** Some models (e.g. OpenAI GPT) may not report `cache_write` tokens separately in the observability events. When `cache_write = 0`, the formula gives 100% — this is a data reporting artifact, not a true 100% hit rate. Treat such values as "cache data not available" for that model.

**Why is output so tiny?** Cortex Code runs a multi-step agent loop. Each `Step-0` span output = the planning decision for that step ("use sql_execute tool" ≈ 15 tokens). The full response text spans multiple steps. When averaged, output looks very small but this is expected and normal.

**Data source:** `CC_PROMPT_EVENTS` — populated nightly by `SP_CC_CLASSIFY_PROMPTS` which extracts `token_count.*` attributes from `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` (`CodingAgent.Step-0` spans).
            """)
        df_econ = _load_token_econ_by_model(session, active_days)
        if df_econ.empty:
            st.info("No token data available. CC_PROMPT_EVENTS must be populated (run SP_CC_CLASSIFY_PROMPTS).")
        else:
            total_tokens   = int(df_econ["TOTAL_T"].sum())
            total_input    = int(df_econ["INPUT_T"].sum())
            total_cache_r  = int(df_econ["CACHE_READ_T"].sum())
            total_cache_w  = int(df_econ["CACHE_WRITE_T"].sum())
            # Correct formula: hits / (hits + misses) — cache_write = miss, cache_read = hit
            # input_tokens are NOT part of the cache system and excluded from this ratio
            cache_hit_rate = round(total_cache_r / max(total_cache_r + total_cache_w, 1) * 100, 1)
            credits_saved  = round(total_cache_r * 0.9 * 0.000025, 4)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Tokens", _fmt_tokens(total_tokens),
                      help="Sum of all input, output, cache read, and cache write tokens across all LLMs.")
            k2.metric("Cache Hit Rate *(approx)*", f"{cache_hit_rate}%",
                      help="cache_read ÷ (cache_read + cache_write). Approximate — field semantics in AI_OBSERVABILITY_EVENTS may vary by account. Use as a directional signal.")
            k3.metric("Est. Credits Saved", f"{credits_saved:,.4f}",
                      help="Cache reads cost ~10x less than fresh input tokens. Savings = cache_read × (input_rate - cache_rate).")
            k4.metric("Cache Read Tokens", _fmt_tokens(total_cache_r),
                      help="Total tokens served from the prompt cache — these cost significantly less than fresh input tokens.")

            st.divider()

            # 100% stacked bar — Token Composition per LLM
            _sec("Token Composition per LLM (100% Stacked)")
            df_long = df_econ.copy()
            for _col in ["INPUT_T", "OUTPUT_T", "CACHE_READ_T", "CACHE_WRITE_T", "TOTAL_T"]:
                df_long[_col] = pd.to_numeric(df_long[_col], errors="coerce").fillna(0)
            df_long = df_long.melt(
                id_vars=["MODEL"],
                value_vars=["INPUT_T", "OUTPUT_T", "CACHE_READ_T", "CACHE_WRITE_T"],
                var_name="TOKEN_TYPE", value_name="TOKENS"
            )
            df_long["TOKEN_TYPE"] = df_long["TOKEN_TYPE"].map({
                "INPUT_T":       "Input",
                "OUTPUT_T":      "Output",
                "CACHE_READ_T":  "Cache Read",
                "CACHE_WRITE_T": "Cache Write",
            })
            model_totals_econ = df_long.groupby("MODEL")["TOKENS"].sum().reset_index(name="MODEL_TOTAL")
            df_long = df_long.merge(model_totals_econ, on="MODEL")
            # Ensure numeric after melt + merge (Snowflake may return object dtype)
            df_long["TOKENS"]      = pd.to_numeric(df_long["TOKENS"],      errors="coerce").fillna(0)
            df_long["MODEL_TOTAL"] = pd.to_numeric(df_long["MODEL_TOTAL"], errors="coerce").fillna(0)
            df_long["PCT"] = (df_long["TOKENS"] / df_long["MODEL_TOTAL"].replace(0, float("nan")) * 100).round(1).fillna(0)
            # Explicit stack order so bars align with legend
            type_order = ["Input", "Output", "Cache Read", "Cache Write"]
            order_map  = {t: i for i, t in enumerate(type_order)}
            df_long["STACK_ORDER"] = df_long["TOKEN_TYPE"].map(order_map).fillna(99)

            color_scale = alt.Scale(
                domain=type_order,
                range=["#7dd3fc", "#6ee7b7", "#fcd34d", "#94a3b8"]
            )
            model_order = df_econ["MODEL"].tolist()

            ch_stacked = (alt.Chart(df_long).mark_bar()
                          .encode(
                              x=alt.X("PCT:Q", title="% of Total Tokens",
                                      scale=alt.Scale(domain=[0, 100])),
                              y=alt.Y("MODEL:N", sort=model_order, title=""),
                              color=alt.Color("TOKEN_TYPE:N", scale=color_scale,
                                              legend=alt.Legend(title="Token Type"),
                                              sort=type_order),
                              order=alt.Order("STACK_ORDER:O", sort="ascending"),
                              tooltip=["MODEL:N", "TOKEN_TYPE:N",
                                       alt.Tooltip("TOKENS:Q", title="Tokens", format=","),
                                       alt.Tooltip("PCT:Q", title="%", format=".1f")]
                          )
                          .properties(height=max(200, len(df_econ) * 40))
                          .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch_stacked, use_container_width=True)

            # Cache Hit Rate bar — hide models where cache_write=0 (GPT artifact)
            _sec("Cache Hit Rate by LLM")
            df_econ_ch = df_econ.copy()
            df_econ_ch["CACHE_HIT_RATE"] = df_econ_ch.apply(
                lambda r: round(r["CACHE_READ_T"] / (r["CACHE_READ_T"] + r["CACHE_WRITE_T"]) * 100, 1)
                          if r["CACHE_WRITE_T"] > 0 else None,
                axis=1
            )
            df_hit_valid = df_econ_ch[df_econ_ch["CACHE_HIT_RATE"].notna()].copy()
            df_hit_na    = df_econ_ch[df_econ_ch["CACHE_HIT_RATE"].isna()]["MODEL"].tolist()
            if df_hit_na:
                st.caption(f"ℹ️ **{', '.join(df_hit_na)}** — cache write tokens not reported by this model's API. Cache Hit Rate not calculable (shown as N/A).")
            if not df_hit_valid.empty:
                ch_hit = (alt.Chart(df_hit_valid).mark_bar(color=_A)
                          .encode(
                              x=alt.X("CACHE_HIT_RATE:Q", title="Cache Hit Rate %"),
                              y=alt.Y("MODEL:N", sort="-x", title="",
                                      axis=alt.Axis(labelLimit=200)),
                              tooltip=["MODEL:N",
                                       alt.Tooltip("CACHE_HIT_RATE:Q", title="Cache Hit %", format=".1f")]
                          )
                          .properties(height=max(150, len(df_hit_valid) * 35))
                          .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_hit, use_container_width=True)

            # Cache Write Efficiency table — abbreviated token counts
            _sec("Cache Write Efficiency")
            econ_tbl = df_econ.copy()
            econ_tbl["CACHE_HIT_PCT"] = econ_tbl.apply(
                lambda r: round(r["CACHE_READ_T"] / (r["CACHE_READ_T"] + r["CACHE_WRITE_T"]) * 100, 1)
                          if r["CACHE_WRITE_T"] > 0 else None,
                axis=1
            )
            econ_tbl["CACHE_WRITE_PCT"] = (
                econ_tbl["CACHE_WRITE_T"] / econ_tbl["TOTAL_T"].replace(0, float("nan")) * 100
            ).round(1).fillna(0)
            # Format large token counts as abbreviated strings
            for col in ["TOTAL_T", "INPUT_T", "OUTPUT_T", "CACHE_READ_T", "CACHE_WRITE_T"]:
                econ_tbl[col] = econ_tbl[col].apply(_fmt_tokens)
            econ_tbl["CACHE_HIT_PCT"] = econ_tbl["CACHE_HIT_PCT"].apply(
                lambda v: f"{v:.1f}%" if pd.notna(v) else "N/A")
            display_cols = ["MODEL", "TOTAL_T", "INPUT_T", "OUTPUT_T",
                            "CACHE_READ_T", "CACHE_WRITE_T", "CACHE_HIT_PCT", "CACHE_WRITE_PCT"]
            st.dataframe(
                econ_tbl[display_cols],
                use_container_width=True, hide_index=True,
                column_config={
                    "MODEL":           st.column_config.TextColumn("Model"),
                    "TOTAL_T":         st.column_config.TextColumn("Total Tokens"),
                    "INPUT_T":         st.column_config.TextColumn("Input"),
                    "OUTPUT_T":        st.column_config.TextColumn("Output"),
                    "CACHE_READ_T":    st.column_config.TextColumn("Cache Read"),
                    "CACHE_WRITE_T":   st.column_config.TextColumn("Cache Write"),
                    "CACHE_HIT_PCT":   st.column_config.TextColumn("Cache Hit %",
                                        help="N/A = model does not report cache_write tokens (e.g. GPT). Hits÷(hits+misses) formula requires both."),
                    "CACHE_WRITE_PCT": st.column_config.NumberColumn("Cache Write %", format="%.1f",
                                        help="Cache writes as % of total tokens. Write % >> Hit % = inefficient caching."),
                }
            )

            st.caption(
                "High Cache Hit Rate means users send repetitive context (system prompts, file contents) "
                "and the cache is working. Cache Write % >> Cache Read % indicates writes that never get "
                "read back — consider shorter cache windows."
            )

    # ── LLM-as-Judge Evaluation ─────────────────────────────────────────────────
    with tab_quality:
        st.warning(
            "⚗️ **Experimental — Custom Evaluation.** These scores are computed using the "
            "LLM judge model configured in **Settings → Alerting & Evaluation** "
            "(default: `llama3.1-70b`), via `SP_CC_EVALUATE_RESPONSES`. They are **not** "
            "Snowflake's built-in quality measurement and "
            "should not be interpreted as an official assessment of Cortex Code's output quality. "
            "Use as a directional signal only.",
            icon=None
        )
        st.caption(
            "A second LLM evaluates sampled agent responses across 4 custom dimensions. "
            "Scores 0.0–1.0 — higher is better. Powered by `SP_CC_EVALUATE_RESPONSES`."
        )
        with st.expander("What do these scores mean — and their limitations?", expanded=False):
            st.markdown("""
| Metric | What it measures | Known limitation |
|---|---|---|
| **Answer Relevance** | Did the response address what the user asked? | Evaluated on agent *planning* output, not the final user-facing reply. Planning steps are short tool-selection decisions, not full answers. |
| **Groundedness** | Is the response factually grounded without hallucination? | Designed for RAG systems. Cortex Code doesn't retrieve documents — this metric may not apply meaningfully to a coding assistant context. |
| **Coherence** | Is the response logically structured and easy to follow? | Most applicable of the four for planning output, but still subject to judge model variability. |
| **Safety** | Is the output free of harmful content? | Most reliable metric — does catch harmful or inappropriate content in responses. |

> **Important:** These scores reflect our custom evaluation using `SNOWFLAKE.CORTEX.COMPLETE` with a manually crafted judge prompt.
> They are **not** derived from Snowflake's native AI Observability telemetry.
> The judge model (configurable in **Settings → Alerting & Evaluation**) affects all scores.
> Low scores may indicate the judge is evaluating short intermediate planning steps rather than full responses.
            """)
        total_evals, last_eval = _load_quality_stats(session)
        qual = _load_quality_by_model(session, active_days)
        trend = _load_quality_trend(session, active_days)

        if total_evals == 0:
            st.info("No quality scores yet. Quality scoring is optional and costs Cortex credits.")
            st.markdown("""
**To enable quality scoring:**
1. Go to **Settings → Alerting & Evaluation** — set `EVAL_ENABLED = TRUE` and choose an eval model
2. Or run manually:
   ```sql
   CALL SP_CC_EVALUATE_RESPONSES(200, 'claude-sonnet-4-5');
   ```
3. Schedule it by adding a task — or use the Run button below.
""")
            col_run, _ = st.columns([1, 3])
            with col_run:
                eval_model_setting = get_app_setting(session, "EVAL_MODEL", "claude-sonnet-4-5")
                batch = int(get_app_setting(session, "EVAL_BATCH_SIZE", "200"))
                if st.button("Run Quality Evaluation Now", type="primary", key="btn_eval_now",
                             help=f"Calls SP_CC_EVALUATE_RESPONSES({batch}, '{eval_model_setting}'). "
                                  f"Costs ~{batch * 0.00005:.4f} Cortex credits."):
                    sp = fq_sp(session, SP_EVALUATE_RESPONSES)
                    safe_model = escape_sql_literal(eval_model_setting)
                    with st.spinner(f"Evaluating up to {batch} responses with {eval_model_setting}…"):
                        try:
                            result = session.sql(f"CALL {sp}({batch}, '{safe_model}')").collect()
                            import json as _json2
                            raw = result[0][0] if result else "{}"
                            res = _json2.loads(raw) if isinstance(raw, str) else raw
                            evaluated = res.get("evaluated", 0)
                            st.success(f"✓ Evaluated {evaluated} responses. Reload to see scores.")
                            _load_quality_by_model.clear()
                            _load_quality_trend.clear()
                            _load_quality_stats.clear()
                        except Exception as e:
                            st.error(f"Evaluation failed: {e}")
        else:
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Evaluated", f"{total_evals:,}",
                      help="Total responses scored in CC_RESPONSE_QUALITY.")
            if not qual.empty:
                k2.metric("Answer Relevance _(exp)_",
                          f"{qual['AVG_ANSWER_RELEVANCE'].mean():.2f}",
                          help="Experimental custom score. Evaluated on agent planning output, not final user-facing responses.")
                k3.metric("Groundedness _(exp)_",
                          f"{qual['AVG_GROUNDEDNESS'].mean():.2f}",
                          help="Experimental custom score. Groundedness is a RAG metric — may not apply directly to a coding assistant context.")
                k4.metric("Coherence _(exp)_",
                          f"{qual['AVG_COHERENCE'].mean():.2f}",
                          help="Experimental custom score. 1.0 = logically clear and structured.")
                k5.metric("Safety _(exp)_",
                          f"{qual['AVG_SAFETY'].mean():.2f}",
                          help="Experimental custom score. Most reliable of the four — 1.0 = no harmful content detected.")

            st.divider()

            if not qual.empty:
                _sec("LLM-as-Judge Scores by Model")
                st.caption("Each panel shows one evaluation dimension. Bars represent per-model average score (0.0–1.0). Higher is better.")
                qual_melt = qual.melt(
                    id_vars="MODEL",
                    value_vars=["AVG_ANSWER_RELEVANCE","AVG_GROUNDEDNESS","AVG_COHERENCE","AVG_SAFETY"],
                    var_name="METRIC", value_name="SCORE"
                )
                qual_melt["METRIC"] = qual_melt["METRIC"].map({
                    "AVG_ANSWER_RELEVANCE": "Answer Relevance",
                    "AVG_GROUNDEDNESS":     "Groundedness",
                    "AVG_COHERENCE":        "Coherence",
                    "AVG_SAFETY":           "Safety",
                })
                _metric_colors = {
                    "Answer Relevance": _P,
                    "Groundedness":     _G,
                    "Coherence":        _A,
                    "Safety":           _R,
                }
                qual_melt["COLOR"] = qual_melt["METRIC"].map(_metric_colors)

                # 2×2 faceted chart — one panel per metric, no overlapping legend
                base = (alt.Chart(qual_melt).mark_bar()
                        .encode(
                            x=alt.X("SCORE:Q", title="Score (0–1)",
                                    scale=alt.Scale(domain=[0, 1]),
                                    axis=alt.Axis(orient="top", grid=True)),
                            y=alt.Y("MODEL:N", sort="-x", title="",
                                    axis=alt.Axis(labelLimit=200)),
                            color=alt.Color("METRIC:N",
                                scale=alt.Scale(
                                    domain=list(_metric_colors.keys()),
                                    range=list(_metric_colors.values())),
                                legend=None),
                            tooltip=["MODEL:N", "METRIC:N",
                                     alt.Tooltip("SCORE:Q", title="Score", format=".3f")])
                        .properties(width=280, height=max(80, len(qual) * 30)))
                ch = (base
                      .facet(facet=alt.Facet("METRIC:N", title="", header=alt.Header(labelFontSize=13, labelFontWeight="bold")), columns=2)
                      .configure_view(strokeWidth=1, stroke="#1f2937")
                      .configure(background=_BG))
                st.altair_chart(ch, use_container_width=True)

                st.dataframe(qual, use_container_width=True, hide_index=True,
                             column_config={
                                 "MODEL":                st.column_config.TextColumn("Model"),
                                 "AVG_ANSWER_RELEVANCE": st.column_config.NumberColumn(
                                     "Answer Relevance", format="%.3f",
                                     help="1.0 = fully answers the question"),
                                 "AVG_GROUNDEDNESS":     st.column_config.NumberColumn(
                                     "Groundedness", format="%.3f",
                                     help="Factually grounded without hallucination. 1.0 = no hallucination detected."),
                                 "AVG_COHERENCE":        st.column_config.NumberColumn(
                                     "Coherence", format="%.3f",
                                     help="1.0 = logically clear"),
                                 "AVG_SAFETY":           st.column_config.NumberColumn(
                                     "Safety", format="%.3f",
                                     help="1.0 = fully safe"),
                                 "EVALUATED_COUNT":      st.column_config.NumberColumn("Evaluated"),
                                 "LAST_EVAL":            st.column_config.DatetimeColumn("Last Eval"),
                             })

            if not trend.empty:
                _sec("Quality Trend Over Time")
                trend["RESPONSE_DATE"] = trend["RESPONSE_DATE"].astype(str)
                trend_melt = trend.melt(
                    id_vars=["RESPONSE_DATE","MODEL"],
                    value_vars=["AVG_ANSWER_RELEVANCE","AVG_GROUNDEDNESS","AVG_COHERENCE","AVG_SAFETY"],
                    var_name="METRIC", value_name="SCORE"
                )
                trend_melt["METRIC"] = trend_melt["METRIC"].map({
                    "AVG_ANSWER_RELEVANCE": "Answer Relevance",
                    "AVG_GROUNDEDNESS":     "Groundedness",
                    "AVG_COHERENCE":        "Coherence",
                    "AVG_SAFETY":           "Safety",
                })
                ch2 = (alt.Chart(trend_melt).mark_line(point=True)
                       .encode(
                           x=alt.X("RESPONSE_DATE:T", title=""),
                           y=alt.Y("SCORE:Q", title="Score",
                                   scale=alt.Scale(domain=[0, 1])),
                           color=alt.Color("METRIC:N",
                               scale=alt.Scale(
                                   domain=["Answer Relevance","Groundedness","Coherence","Safety"],
                                   range=[_P, _G, _A, _R]),
                               legend=alt.Legend(title="")),
                           strokeDash=alt.StrokeDash("MODEL:N"),
                           tooltip=["RESPONSE_DATE:T","MODEL:N","METRIC:N",
                                    alt.Tooltip("SCORE:Q", format=".3f")])
                       .properties(height=220)
                       .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch2, use_container_width=True)

            # Manual run button
            st.divider()
            st.caption(f"Last evaluated: {last_eval} UTC. "
                       "Scores update when SP_CC_EVALUATE_RESPONSES runs.")
            eval_model_s = get_app_setting(session, "EVAL_MODEL", "claude-sonnet-4-5")
            batch_s = int(get_app_setting(session, "EVAL_BATCH_SIZE", "200"))
            if st.button("Run Quality Evaluation", key="btn_eval_quality",
                         help=f"Evaluates up to {batch_s} unevaluated responses. "
                              f"~{batch_s * 0.00005:.4f} credits."):
                sp = fq_sp(session, SP_EVALUATE_RESPONSES)
                safe_m = escape_sql_literal(eval_model_s)
                with st.spinner("Evaluating…"):
                    try:
                        import json as _json2
                        res2 = session.sql(f"CALL {sp}({batch_s}, '{safe_m}')").collect()
                        raw2 = res2[0][0] if res2 else "{}"
                        r2 = _json2.loads(raw2) if isinstance(raw2, str) else raw2
                        st.success(f"✓ Evaluated {r2.get('evaluated', 0)} new responses.")
                        _load_quality_by_model.clear()
                        _load_quality_trend.clear()
                        _load_quality_stats.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

    # ── Prompt Insights ─────────────────────────────────────────────────────────
    with tab_violations:
        st.caption("Policy insights per 1,000 prompts by model — sourced from `CC_PROMPT_VIOLATIONS`. "
                   "Categories reflect the responsible AI rules defined in **Policy Rules**.")

        # Legend — collapsible, same pattern as LLM-as-Judge and Token Economics
        with st.expander("What do these insight categories mean?", expanded=False):
            st.markdown("""
| Category | What triggers it | Severity |
|---|---|---|
| `PII_RISK` | Prompts containing or requesting personal data — SSN, credit cards, passport, bank account numbers | 🔴 HIGH |
| `SECURITY` | API keys, passwords, credentials, prompt injection / jailbreak attempts, data exfiltration requests | 🔴 HIGH |
| `COMPETITOR` | Prompts referencing Snowflake competitors — Databricks, BigQuery, Redshift, Synapse, etc. | 🟡 MEDIUM |
| `USAGE_ANOMALY` | Sessions with unusually high prompt depth (may indicate automation or runaway agents) | 🟡 MEDIUM |
| `PERSONAL_USE` | Prompts unrelated to work — entertainment, personal errands, social content | 🟢 LOW |

These categories are set per rule in **Policy Rules → Active Rules**. Custom rules you create appear here with their assigned category.
            """)
        st.caption("Data source: `CC_PROMPT_VIOLATIONS` — prompt insights written nightly by `SP_CC_CLASSIFY_PROMPTS`.")

        viol    = _load_violation_rate_by_model(session, active_days)
        viol_cat = _load_violation_by_category(session, active_days)

        if viol.empty:
            st.info("No prompt insight data available. Run SP_CC_CLASSIFY_PROMPTS to populate CC_PROMPT_VIOLATIONS.")
        else:
            _sec("Insights per 1,000 Prompts — Split by Category")

            if not viol_cat.empty:
                # Category colour map — consistent with severity levels
                _cat_colors = {
                    "PII_RISK":       "#fca5a5",   # red
                    "SECURITY":       "#fcd34d",   # amber
                    "COMPETITOR":     "#7dd3fc",   # blue
                    "USAGE_ANOMALY":  "#c4b5fd",   # violet
                    "PERSONAL_USE":   "#6ee7b7",   # green
                }
                viol_cat["CAT_LABEL"] = viol_cat["CATEGORY"].map({
                    "PII_RISK":      "PII Risk",
                    "SECURITY":      "Security",
                    "COMPETITOR":    "Competitor",
                    "USAGE_ANOMALY": "Usage Anomaly",
                    "PERSONAL_USE":  "Personal Use",
                    "CUSTOM":        "Custom",
                }).fillna(viol_cat["CATEGORY"].str.replace("_", " ").str.title())
                all_cats   = viol_cat["CAT_LABEL"].unique().tolist()
                all_colors = [_cat_colors.get(c, "#94a3b8")
                              for c in viol_cat["CATEGORY"].unique().tolist()]

                ch_split = (alt.Chart(viol_cat).mark_bar()
                            .encode(
                                x=alt.X("VIOLATIONS_PER_1K:Q", title="Insights per 1,000 Prompts",
                                        axis=alt.Axis(orient="top")),
                                y=alt.Y("MODEL:N", sort="-x", title="",
                                        axis=alt.Axis(labelLimit=200)),
                                color=alt.Color("CAT_LABEL:N",
                                    scale=alt.Scale(
                                        domain=all_cats,
                                        range=all_colors),
                                    legend=alt.Legend(title="Category", orient="bottom")),
                                tooltip=["MODEL:N", "CAT_LABEL:N",
                                         alt.Tooltip("VIOLATIONS_PER_1K:Q", title="Insights/1K", format=".2f"),
                                         alt.Tooltip("VIOLATIONS:Q", title="Insights"), "RISK_LEVEL:N"])
                            .properties(height=max(180, len(viol)*45))
                            .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_split, use_container_width=True)
            else:
                # Fallback to simple chart if no category data
                ch = (alt.Chart(viol).mark_bar(color=_A)
                      .encode(
                          x=alt.X("VIOLATIONS_PER_1K:Q", title="Insights per 1,000 Prompts",
                                  axis=alt.Axis(orient="top")),
                          y=alt.Y("MODEL:N", sort="-x", title="",
                                  axis=alt.Axis(labelLimit=200)),
                          tooltip=["MODEL:N",
                                   alt.Tooltip("VIOLATIONS_PER_1K:Q", title="Insights/1K", format=".2f"),
                                   alt.Tooltip("VIOLATIONS:Q", title="Insights")])
                      .properties(height=max(180, len(viol)*40))
                      .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch, use_container_width=True)

            # Summary table
            st.dataframe(viol, use_container_width=True, hide_index=True,
                         column_config={
                             "MODEL":              st.column_config.TextColumn("Model"),
                             "TOTAL_PROMPTS":      st.column_config.NumberColumn("Prompts",    format="%.0f"),
                             "VIOLATIONS":         st.column_config.NumberColumn("Insights", format="%.0f"),
                             "VIOLATIONS_PER_1K":  st.column_config.NumberColumn("Per 1K",
                                                    format="%.2f",
                                                    help="Insights per 1,000 prompts"),
                             "HIGH_RISK":          st.column_config.NumberColumn("🔴 High",    format="%.0f"),
                             "MED_RISK":           st.column_config.NumberColumn("🟡 Medium",  format="%.0f"),
                         })
            st.caption("insight counts are linked to user+date, not the specific model call that triggered the rule. "
                       "For per-rule and per-user drill-down → **Prompt Analysis** page.")

    # ── Usage Share ─────────────────────────────────────────────────────────────
    with tab_usage:
        st.caption("Credit consumption by model over time, sourced from CC_USAGE_DAILY_SUMMARY. Credits reflect actual Snowflake AI credit billing. Stacked area shows how model mix shifts day-to-day.")
        usage = _load_usage_share(session, active_days)
        if usage.empty:
            st.info("No model usage data. CC_USAGE_DAILY_SUMMARY must be populated (run SP_CC_REFRESH_USAGE_SUMMARIES).")
        else:
            total_credits = usage["CREDITS"].sum()
            model_totals = (usage.groupby("MODEL")["CREDITS"].sum()
                               .reset_index().sort_values("CREDITS", ascending=False))
            top_model = model_totals.iloc[0]["MODEL"] if not model_totals.empty else "—"
            top_pct = round(model_totals.iloc[0]["CREDITS"] / total_credits * 100, 1) if total_credits > 0 else 0

            k1, k2, k3 = st.columns(3)
            k1.metric("Total Credits", f"{total_credits:,.1f}",
                      help=f"Sum of credits across all models in the last {active_days} days.")
            k2.metric("Top Model", top_model, help="Model with highest credit consumption.")
            k3.metric("Top Model Share", f"{top_pct}%",
                      help=f"{top_model} accounts for {top_pct}% of all model credits.")

            st.divider()

            _sec("Credits by Model Over Time")
            usage["USAGE_DATE"] = usage["USAGE_DATE"].astype(str)
            ch = (alt.Chart(usage).mark_area(opacity=0.75)
                  .encode(
                      x=alt.X("USAGE_DATE:T", title=""),
                      y=alt.Y("CREDITS:Q", title="Credits", stack="zero"),
                      color=alt.Color("MODEL:N", legend=alt.Legend(title="")),
                      tooltip=["USAGE_DATE:T","MODEL:N",
                               alt.Tooltip("CREDITS:Q", format=",.2f")])
                  .properties(height=260)
                  .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch, use_container_width=True)

            _sec("Total Credits by Model")
            ch2 = (alt.Chart(model_totals).mark_bar()
                   .encode(
                       x=alt.X("CREDITS:Q", title="Credits"),
                       y=alt.Y("MODEL:N", sort="-x", title="",
                               axis=alt.Axis(labelLimit=200)),
                       color=alt.value(_P),
                       tooltip=["MODEL:N", alt.Tooltip("CREDITS:Q", format=",.2f")])
                   .properties(height=max(180, len(model_totals)*40))
                   .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch2, use_container_width=True)

            st.dataframe(model_totals, use_container_width=True, hide_index=True,
                         column_config={
                             "MODEL":   st.column_config.TextColumn("Model"),
                             "CREDITS": st.column_config.NumberColumn("Credits", format="%.2f"),
                         })

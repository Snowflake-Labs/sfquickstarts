"""
CoCo Control Hub — Model Bake-off / Optimization
===================================================
Fuses cost + accuracy into an optimization recommendation.

  • Historical Optimization — per-model credit spend + token efficiency from
      CC_USAGE_DAILY_SUMMARY joined to model tiers (CC_MODEL_CONFIG), with
      downgrade recommendations for expensive tiers carrying heavy volume.
  • Interactive Bake-off    — run one prompt across several models, measure
      latency, tokens, estimated credits, and an optional LLM-judged quality
      score; plot cost-vs-accuracy and recommend the best value model.

Interactive runs call SNOWFLAKE.CORTEX.COMPLETE and CONSUME CREDITS — gated
behind an explicit button.
"""

import time

import altair as alt
import pandas as pd
import streamlit as st

from config import TABLE_USAGE_DAILY, TABLE_MODEL_CONFIG, escape_sql_literal, fq_table

_BG = "#0e1117"
_P  = "#7dd3fc"
_G  = "#6ee7b7"
_O  = "#fcd34d"
_R  = "#fca5a5"

# Fallback list — used only if live discovery (SHOW CORTEX BASE MODELS) returns
# nothing. Unavailable models are also skipped at run time (per-model try/except).
_CANDIDATE_MODELS = [
    "llama3.1-8b", "llama3.1-70b", "llama3.3-70b",
    "claude-3-5-sonnet", "mistral-large2", "snowflake-arctic",
]
_DEFAULT_MODELS = ["llama3.1-8b", "llama3.1-70b", "claude-3-5-sonnet"]
_JUDGE_MODEL = "llama3.1-70b"

# Model families returned by SHOW CORTEX BASE MODELS that CORTEX.COMPLETE does
# not accept (embeddings, doc/audio/utility, guard). Excluded from the picker.
_NON_CHAT_MARKERS = (
    "EMBED", "VOYAGE", "NV-EMBED", "E5-", "ARCTIC-PARSE", "PARSE-DOCUMENT",
    "TRANSCRIBE", "TRANSLATE", "SENTIMENT", "EXTRACT-ANSWER", "TEXT2SQL",
    "MARENGO", "PEGASUS", "GUARD", "ARCTIC-EXTRACT",
)
_LIVE_LIFECYCLES = ("GA", "PUPR")  # PUPR = Public Preview


@st.cache_data(ttl=3600, show_spinner=False)
def _available_chat_models(_session):
    """Discover chat-capable Cortex base models via SHOW CORTEX BASE MODELS.

    Returns [{"id": <lowercase model id>, "preview": bool}, ...] filtered to GA /
    Public-Preview text-generation models, sorted and de-duplicated. Returns an
    empty list on any failure so the caller can fall back to _CANDIDATE_MODELS.
    """
    try:
        _session.sql("SHOW CORTEX BASE MODELS IN SCHEMA SNOWFLAKE.MODELS").collect()
        df = _session.sql(
            'SELECT "name" AS NAME, "lifecycle_status" AS LIFECYCLE '
            "FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))"
        ).to_pandas()
    except Exception:
        return []
    if df.empty:
        return []
    df.columns = [c.upper() for c in df.columns]
    seen, out = set(), []
    for _, r in df.iterrows():
        name = str(r.get("NAME") or "").strip()
        life = str(r.get("LIFECYCLE") or "").strip().upper()
        if not name or life not in _LIVE_LIFECYCLES:
            continue
        if any(mark in name.upper() for mark in _NON_CHAT_MARKERS):
            continue
        mid = name.lower()
        if mid not in seen:
            seen.add(mid)
            out.append({"id": mid, "preview": life == "PUPR"})
    return sorted(out, key=lambda x: x["id"])


def _sec(title):
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner=False)
def _credit_rates(_session) -> dict:
    """Effective credits-per-token per model, derived from usage history."""
    try:
        df = _session.sql("""
            SELECT MODEL_NAME,
                   SUM(TOKEN_CREDITS) / NULLIF(SUM(TOKENS),0) AS CR_PER_TOKEN
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
            WHERE MODEL_NAME IS NOT NULL AND TOKENS > 0
            GROUP BY 1
        """).to_pandas()
        if df.empty:
            return {}
        df.columns = [c.upper() for c in df.columns]
        return {str(r["MODEL_NAME"]).strip('"'): float(r["CR_PER_TOKEN"] or 0)
                for _, r in df.iterrows() if r["CR_PER_TOKEN"]}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def _historical_models(_session, days: int) -> pd.DataFrame:
    """Per-model Cortex Code spend + tier + token efficiency."""
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    mcfg = fq_table(_session, TABLE_MODEL_CONFIG)
    try:
        df = _session.sql(f"""
            SELECT u.MODEL_NAME,
                   COALESCE(m.CATEGORY, 'UNCLASSIFIED') AS TIER,
                   ROUND(SUM(u.TOTAL_CREDITS),4)        AS CREDITS,
                   SUM(u.TOTAL_TOKENS)                  AS TOKENS,
                   SUM(u.QUERY_COUNT)                   AS REQUESTS
            FROM {tbl} u
            LEFT JOIN (
                SELECT UPPER(MODEL_NAME) AS MODEL_NAME, MAX(CATEGORY) AS CATEGORY
                FROM {mcfg} GROUP BY 1
            ) m ON m.MODEL_NAME = UPPER(u.MODEL_NAME)
            WHERE u.USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())
              AND u.MODEL_NAME IS NOT NULL AND u.MODEL_NAME <> ''
            GROUP BY 1, 2
            HAVING COALESCE(SUM(u.TOTAL_CREDITS),0) > 0
            ORDER BY CREDITS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def _run_one_model(session, model: str, prompt: str, rate_map: dict, default_rate: float):
    """Run COMPLETE for one model, then count tokens best-effort.

    COMPLETE and COUNT_TOKENS are issued as SEPARATE statements so a COUNT_TOKENS
    failure (some models COMPLETE supports are unknown to the tokenizer -> 400
    'unknown model') does not discard a successful completion. On token-count
    failure we fall back to a rough char/4 estimate and flag est_tokens=True.
    """
    p = escape_sql_literal(prompt)
    m = escape_sql_literal(model)

    # Step 1 — completion (the only call whose failure is a genuine skip).
    t0 = time.time()
    try:
        resp = str(session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{m}', '{p}') AS RESP"
        ).collect()[0]["RESP"] or "")
    except Exception as e:
        return {"model": model, "error": str(e)[:150]}
    latency_ms = (time.time() - t0) * 1000.0

    # Step 2 — token counts (best-effort; estimate if the tokenizer rejects model).
    est_tokens = False
    try:
        r = escape_sql_literal(resp)
        trow = session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COUNT_TOKENS('{m}', '{p}') AS IN_TOK, "
            f"SNOWFLAKE.CORTEX.COUNT_TOKENS('{m}', '{r}') AS OUT_TOK"
        ).collect()[0]
        in_tok = int(trow["IN_TOK"] or 0)
        out_tok = int(trow["OUT_TOK"] or 0)
    except Exception:
        est_tokens = True
        in_tok = max(1, len(prompt) // 4)
        out_tok = max(1, len(resp) // 4)

    rate = rate_map.get(model, default_rate)
    est_credits = (in_tok + out_tok) * rate
    return {
        "model": model, "response": resp,
        "in_tok": in_tok, "out_tok": out_tok, "total_tok": in_tok + out_tok,
        "latency_ms": round(latency_ms, 1),
        "est_credits": round(est_credits, 6),
        "est_tokens": est_tokens,
    }


def _judge(session, prompt: str, response: str) -> float:
    """LLM-as-judge quality score 0.0–1.0 (single judge model)."""
    jp = escape_sql_literal(
        "You are grading an AI answer for quality (correctness, relevance, "
        "clarity) to the user prompt. Reply with ONLY a number between 0 and 1.\n\n"
        f"PROMPT:\n{prompt[:1500]}\n\nANSWER:\n{response[:2500]}\n\nScore:"
    )
    try:
        raw = session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{_JUDGE_MODEL}', '{jp}')"
        ).collect()[0][0]
        import re
        m = re.search(r"(\d*\.?\d+)", str(raw))
        if m:
            return max(0.0, min(1.0, float(m.group(1))))
    except Exception:
        pass
    return None


def render(session):
    st.header("Model Bake-off",
              help="Compare model cost vs quality and get optimization / downgrade "
                   "recommendations. Interactive runs consume Cortex credits.")

    tab_opt, tab_bakeoff = st.tabs(["Historical Optimization", "Interactive Bake-off"])

    # ─────────────────────── HISTORICAL OPTIMIZATION ───────────────────────
    with tab_opt:
        days = st.selectbox("Lookback", [7, 14, 30, 60, 90], index=2, key="mb_days")
        hist = _historical_models(session, days)
        if hist.empty:
            st.info("No per-model Cortex Code usage for this period.")
        else:
            hist["TOK_PER_CREDIT"] = (hist["TOKENS"] /
                                      hist["CREDITS"].replace(0, pd.NA)).round(0)
            total = float(hist["CREDITS"].sum())
            hist["SHARE_PCT"] = (hist["CREDITS"] / total * 100).round(1) if total else 0

            k1, k2, k3 = st.columns(3)
            k1.metric("Models In Use", f"{len(hist)}")
            k2.metric("Total Credits", f"{total:,.2f}")
            k3.metric("Top Model Share", f"{hist.iloc[0]['SHARE_PCT']:.0f}%")

            st.divider()
            _sec("Credit Spend by Model (colored by tier)")
            ch = (alt.Chart(hist).mark_bar()
                  .encode(x=alt.X("CREDITS:Q", title="Credits"),
                          y=alt.Y("MODEL_NAME:N", sort="-x", title=""),
                          color=alt.Color("TIER:N", title="Tier"),
                          tooltip=["MODEL_NAME:N", "TIER:N",
                                   alt.Tooltip("CREDITS:Q", format=".4f"),
                                   alt.Tooltip("SHARE_PCT:Q", format=".1f"),
                                   "TOK_PER_CREDIT:Q"])
                  .properties(height=max(160, len(hist) * 32))
                  .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch, use_container_width=True)

            # Downgrade recommendations
            _sec("Optimization Recommendations")
            recs = []
            for _, r in hist.iterrows():
                tier = str(r["TIER"]).upper()
                share = float(r["SHARE_PCT"] or 0)
                if tier == "TIER_1" and share >= 15:
                    recs.append(f"**{r['MODEL_NAME']}** (TIER_1) drives {share:.0f}% of "
                                f"credits — route simple/deterministic prompts to a TIER_2/3 "
                                f"model to cut cost.")
                elif tier == "UNCLASSIFIED" and share >= 10:
                    recs.append(f"**{r['MODEL_NAME']}** is unclassified with {share:.0f}% "
                                f"share — assign it a tier in Model Access to enable routing policy.")
            if recs:
                for rc in recs:
                    st.markdown(f"- {rc}")
            else:
                st.success("No high-cost tier concentration detected — model mix looks efficient.")

            st.dataframe(
                hist[["MODEL_NAME", "TIER", "REQUESTS", "TOKENS", "CREDITS",
                      "SHARE_PCT", "TOK_PER_CREDIT"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "MODEL_NAME":     st.column_config.TextColumn("Model"),
                    "TIER":           st.column_config.TextColumn("Tier"),
                    "REQUESTS":       st.column_config.NumberColumn("Requests"),
                    "TOKENS":         st.column_config.NumberColumn("Tokens"),
                    "CREDITS":        st.column_config.NumberColumn("Credits", format="%.4f"),
                    "SHARE_PCT":      st.column_config.NumberColumn("Share %", format="%.1f"),
                    "TOK_PER_CREDIT": st.column_config.NumberColumn("Tokens/Credit", format="%.0f"),
                })

    # ─────────────────────────── INTERACTIVE BAKE-OFF ───────────────────────────
    with tab_bakeoff:
        st.warning("Running a bake-off calls SNOWFLAKE.CORTEX.COMPLETE for each selected "
                   "model and **consumes Cortex credits**.", icon="⚠️")
        prompt = st.text_area("Prompt to test", height=120,
                              value="Write a SQL query to find the top 5 customers by total order value.",
                              key="mb_prompt")
        _discovered = _available_chat_models(session)
        if _discovered:
            _preview_ids = {m["id"] for m in _discovered if m["preview"]}
            _option_ids = [m["id"] for m in _discovered]
        else:
            _preview_ids = set()
            _option_ids = list(_CANDIDATE_MODELS)
        _default_ids = [m for m in _DEFAULT_MODELS if m in _option_ids] or _option_ids[:3]
        models = st.multiselect(
            "Models to compare", _option_ids, default=_default_ids, key="mb_models",
            format_func=lambda mid: f"{mid} (Preview)" if mid in _preview_ids else mid)
        st.caption("Models discovered live via SHOW CORTEX BASE MODELS; "
                   "unavailable models are skipped at run time.")
        judge = st.checkbox("Score quality with LLM-as-judge (extra credits)",
                            value=True, key="mb_judge",
                            help=f"Uses {_JUDGE_MODEL} to rate each response 0–1.")

        if st.button("Run Bake-off", type="primary", key="mb_run"):
            if not prompt.strip() or not models:
                st.error("Enter a prompt and select at least one model.")
            else:
                rate_map = _credit_rates(session)
                default_rate = (sum(rate_map.values()) / len(rate_map)) if rate_map else 5e-7
                results, errors = [], []
                prog = st.progress(0.0)
                for i, m in enumerate(models):
                    res = _run_one_model(session, m, prompt, rate_map, default_rate)
                    if res.get("error"):
                        errors.append(f"{m}: {res['error']}")
                    else:
                        if judge:
                            res["quality"] = _judge(session, prompt, res["response"])
                        results.append(res)
                    prog.progress((i + 1) / len(models))
                st.session_state["mb_results"] = results
                st.session_state["mb_errors"] = errors

        results = st.session_state.get("mb_results")
        errors = st.session_state.get("mb_errors", [])
        if errors:
            for e in errors:
                st.caption(f"⚠️ skipped {e}")

        if results:
            df = pd.DataFrame(results)
            has_q = "quality" in df.columns and df["quality"].notna().any()
            if "est_tokens" in df.columns and df["est_tokens"].any():
                st.caption("~ Token counts and credits are estimated for some models "
                           "(COUNT_TOKENS does not support them).")

            # Recommendation
            _sec("Recommendation")
            if has_q:
                dfq = df[df["quality"].notna()].copy()
                # value = quality per credit (avoid div by zero)
                dfq["value"] = dfq["quality"] / dfq["est_credits"].replace(0, pd.NA)
                best_val = dfq.sort_values("value", ascending=False).iloc[0]
                top_q = dfq.sort_values("quality", ascending=False).iloc[0]
                cheapest = df.sort_values("est_credits").iloc[0]
                c1, c2, c3 = st.columns(3)
                c1.metric("Best Value", best_val["model"],
                          help="Highest quality per estimated credit.")
                c2.metric("Highest Quality", f"{top_q['model']} ({top_q['quality']:.2f})")
                c3.metric("Cheapest", f"{cheapest['model']}",
                          help=f"~{cheapest['est_credits']:.6f} credits")
            else:
                cheapest = df.sort_values("est_credits").iloc[0]
                fastest = df.sort_values("latency_ms").iloc[0]
                c1, c2 = st.columns(2)
                c1.metric("Cheapest", cheapest["model"],
                          help=f"~{cheapest['est_credits']:.6f} credits")
                c2.metric("Fastest", f"{fastest['model']} ({fastest['latency_ms']:.0f} ms)")

            st.divider()

            # Cost vs quality (or latency) scatter
            if has_q:
                _sec("Cost vs Quality")
                scat = (alt.Chart(df[df["quality"].notna()]).mark_circle(size=180)
                        .encode(x=alt.X("est_credits:Q", title="Est. Credits (lower is cheaper)"),
                                y=alt.Y("quality:Q", title="Quality (0–1)",
                                        scale=alt.Scale(domain=[0, 1])),
                                color=alt.Color("model:N", title="Model"),
                                tooltip=["model:N", alt.Tooltip("est_credits:Q", format=".6f"),
                                         alt.Tooltip("quality:Q", format=".2f"),
                                         "latency_ms:Q", "total_tok:Q"])
                        .properties(height=300)
                        .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(scat, use_container_width=True)
            else:
                _sec("Cost vs Latency")
                scat = (alt.Chart(df).mark_circle(size=180)
                        .encode(x=alt.X("est_credits:Q", title="Est. Credits"),
                                y=alt.Y("latency_ms:Q", title="Latency (ms)"),
                                color=alt.Color("model:N", title="Model"),
                                tooltip=["model:N", alt.Tooltip("est_credits:Q", format=".6f"),
                                         "latency_ms:Q", "total_tok:Q"])
                        .properties(height=300)
                        .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(scat, use_container_width=True)

            # Detail table
            _sec("Per-Model Detail")
            cols = ["model", "latency_ms", "in_tok", "out_tok", "total_tok", "est_credits"]
            if has_q:
                cols.append("quality")
            st.dataframe(df[cols], use_container_width=True, hide_index=True,
                         column_config={
                             "model":       st.column_config.TextColumn("Model"),
                             "latency_ms":  st.column_config.NumberColumn("Latency (ms)", format="%.0f"),
                             "in_tok":      st.column_config.NumberColumn("Input Tok"),
                             "out_tok":     st.column_config.NumberColumn("Output Tok"),
                             "total_tok":   st.column_config.NumberColumn("Total Tok"),
                             "est_credits": st.column_config.NumberColumn("Est. Credits", format="%.6f"),
                             "quality":     st.column_config.NumberColumn("Quality", format="%.2f"),
                         })

            # Responses
            with st.expander("Model responses", expanded=False):
                for r in results:
                    st.markdown(f"**{r['model']}**")
                    st.code(r.get("response", ""))

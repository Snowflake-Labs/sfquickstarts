"""
CoCo Control Hub — Attribution & Tags
=====================================
The confidence-labeled waterfall that assigns CoCo usage (LLM tokens + warehouse
compute) to a billing entity, the three identity levers that feed it, the queue
for anything unidentified, and a DIY blueprint for going a grain deeper.

Honest model: attribution needs the platform owner to enforce ONE clean identity.
Query-level tags don't survive CoCo, so identity (user tag / service account /
role) is the reliable signal. Levels, in precedence order (first match wins):

  L3 · Service account   (CC_SERVICE_USER_MAPPING)  -> HIGH   — best for M2/M3
  L4 · User tag          (CC_COST_TAGS)             -> MEDIUM — best for M1
  L5 · Role mapping      (CC_ROLE_MAPPING)          -> MEDIUM
  Unattributed           -> queue, never billed blindly
"""

import io
import zipfile

import altair as alt
import pandas as pd
import streamlit as st

import tagging
from config import (
    TABLE_ATTRIBUTION_DAILY, TABLE_UNATTRIBUTED, TABLE_SERVICE_USER_MAPPING,
    TABLE_ROLE_MAPPING, WATERFALL_LEVELS, SP_ATTRIBUTE_USAGE,
    fq_table, fq_sp, escape_sql_literal, get_current_user,
)
from utils import get_app_setting
from audit import log_activity

_BG = "#0e1117"
_P  = "#7dd3fc"
_G  = "#6ee7b7"
_O  = "#fcd34d"
_R  = "#f87171"

_ENTITY_TYPES = ["CUSTOMER", "PARTNER", "PROJECT", "VERTICAL", "INTERNAL"]
_CONF_COLOR = {"HIGH": _G, "MEDIUM": _O, "NONE": _R}


def _ensure_tables(session):
    """Self-heal the mapping + queue tables for deployments predating the DDL."""
    stmts = [
        f"""CREATE TABLE IF NOT EXISTS {fq_table(session, TABLE_SERVICE_USER_MAPPING)} (
                USER_NAME VARCHAR(255) NOT NULL PRIMARY KEY, ENTITY VARCHAR(255) NOT NULL,
                ENTITY_TYPE VARCHAR(50) DEFAULT 'CUSTOMER', UPDATED_BY VARCHAR(255),
                UPDATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
        f"""CREATE TABLE IF NOT EXISTS {fq_table(session, TABLE_ROLE_MAPPING)} (
                ROLE_NAME VARCHAR(255) NOT NULL PRIMARY KEY, ENTITY VARCHAR(255) NOT NULL,
                ENTITY_TYPE VARCHAR(50) DEFAULT 'CUSTOMER', UPDATED_BY VARCHAR(255),
                UPDATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
    ]
    for s in stmts:
        try:
            session.sql(s).collect()
        except Exception:
            pass


@st.cache_data(ttl=300, show_spinner=False)
def _load_attr(_session, days: int) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_ATTRIBUTION_DAILY)
    try:
        df = _session.sql(f"""
            SELECT USAGE_DATE, USER_NAME, SURFACE, ENTITY, ENTITY_TYPE, ATTR_METHOD,
                   CONFIDENCE, TOKEN_CREDITS, WAREHOUSE_CREDITS
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["TOTAL_CREDITS"] = df["TOKEN_CREDITS"] + df["WAREHOUSE_CREDITS"]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=180, show_spinner=False)
def _load_queue(_session) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_UNATTRIBUTED)
    try:
        df = _session.sql(f"""
            SELECT USER_NAME, TOKEN_CREDITS, WAREHOUSE_CREDITS,
                   (TOKEN_CREDITS + WAREHOUSE_CREDITS) AS TOTAL_CREDITS,
                   LAST_SEEN, STATUS
            FROM {tbl} WHERE STATUS = 'PENDING'
            ORDER BY TOTAL_CREDITS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_mapping(_session, table: str) -> pd.DataFrame:
    tbl = fq_table(_session, table)
    key = "USER_NAME" if table == TABLE_SERVICE_USER_MAPPING else "ROLE_NAME"
    try:
        df = _session.sql(f"SELECT {key}, ENTITY, ENTITY_TYPE FROM {tbl} ORDER BY 1").to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        else:
            df = pd.DataFrame(columns=[key, "ENTITY", "ENTITY_TYPE"])
        return df
    except Exception:
        return pd.DataFrame(columns=[key, "ENTITY", "ENTITY_TYPE"])


def _save_mapping(session, table: str, edited: pd.DataFrame):
    key = "USER_NAME" if table == TABLE_SERVICE_USER_MAPPING else "ROLE_NAME"
    tbl = fq_table(session, table)
    actor = get_current_user(session)
    rows = []
    for _, r in edited.iterrows():
        k = str(r.get(key) or "").strip()
        ent = str(r.get("ENTITY") or "").strip()
        if not k or not ent:
            continue
        et = str(r.get("ENTITY_TYPE") or "CUSTOMER").strip().upper()
        rows.append(f"('{escape_sql_literal(k)}', '{escape_sql_literal(ent)}', "
                    f"'{escape_sql_literal(et)}')")
    if not rows:
        st.warning("Nothing to save — enter an identity and an entity.")
        return
    values = ",\n".join(rows)
    try:
        session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT * FROM VALUES {values} AS v({key}, ENTITY, ENTITY_TYPE)) s
            ON t.{key} = s.{key}
            WHEN MATCHED THEN UPDATE SET
                ENTITY = s.ENTITY, ENTITY_TYPE = s.ENTITY_TYPE,
                UPDATED_BY = '{escape_sql_literal(actor)}', UPDATED_AT = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT ({key}, ENTITY, ENTITY_TYPE, UPDATED_BY, UPDATED_AT)
                VALUES (s.{key}, s.ENTITY, s.ENTITY_TYPE,
                        '{escape_sql_literal(actor)}', CURRENT_TIMESTAMP())
        """).collect()
        log_activity(session, "ATTRIBUTION_MAPPING_SAVED",
                     details={"table": table, "rows": len(rows)})
        st.cache_data.clear()
        st.success(f"Saved {len(rows)} mapping(s). Re-run attribution to apply.")
        st.rerun()
    except Exception as e:
        st.error(f"Save failed: {str(e)[:180]}")


def _rerun_attribution(session, days: int):
    try:
        with st.spinner("Running attribution waterfall…"):
            r = session.sql(
                f"CALL {fq_sp(session, SP_ATTRIBUTE_USAGE)}({int(days)})").collect()
        st.cache_data.clear()
        st.success(str(r[0][0]) if r else "Attribution refreshed.")
    except Exception as e:
        st.error(f"Attribution failed: {str(e)[:180]}")


# ─────────────────────────── Styled explainer helpers ────────────────────────
def _flow_cards():
    """The end-to-end tagging flow as four styled step cards."""
    steps = [
        ("1", "Set identity",
         "Tag users, or map service accounts / roles to a billing entity. The app "
         "<b>reads</b> this — it never writes to your users, roles, or grants."),
        ("2", "Run attribution",
         "The waterfall assigns each user's CoCo usage (tokens + warehouse) to an "
         "entity — the single best signal, first-match-wins, with a confidence label."),
        ("3", "Land or queue",
         "Matched usage lands on an entity; anything with no identity goes to the "
         "<b>Unattributed queue</b> — reviewed, never billed blindly."),
        ("4", "Feed the bill",
         "Attributed credits flow into <b>Generate Bill</b>, split by your chosen "
         "dimension (vertical, partner, service account, role)."),
    ]
    cols = st.columns(len(steps))
    for c, (n, t, d) in zip(cols, steps):
        with c:
            st.markdown(
                f"<div class='cc-step'><div><span class='cc-step-num'>{n}</span>"
                f"<span class='cc-step-title'>{t}</span></div>"
                f"<div class='cc-step-desc'>{d}</div></div>",
                unsafe_allow_html=True)


def _responsibility_callout():
    st.markdown(
        "<div class='cc-callout'><div class='h'>Tagging is yours to set — the app only reads it</div>"
        "<p>Attribution is only as good as your <b>identity hygiene</b>. The recommended, "
        "lowest-effort path is tagging at the <b>user / role</b> level (an ACCOUNTADMIN sets it "
        "once in Snowflake; it applies to everyone and CoCo can't overwrite it).</p>"
        "<p>Query-level tags don't survive CoCo — so per-query business context isn't reliable. "
        "That's why identity (below) is the signal we attribute on. Want project/engagement grain? "
        "See <i>Go a grain deeper</i> at the bottom.</p></div>",
        unsafe_allow_html=True)


def _waterfall_ladder():
    """Render the identity waterfall as a styled ladder, highest-confidence first.
    Levels 1-2 (per-query / session tags) are shown greyed because CoCo overwrites
    the query tag, so attribution starts at the identity levels (L3+)."""
    # Friendly, business-facing labels (display only — internal method codes unchanged).
    friendly = {
        "L3_SERVICE_USER": "L3 · Service account",
        "L4_USER_TAG":     "L4 · User tag",
        "L5_ROLE":         "L5 · Role",
        "UNATTRIBUTED":    "Unattributed",
    }
    # Greyed, non-actionable rows so the L1/L2 -> L3 story is complete.
    st.markdown(
        "<div class='cc-wf-row cc-wf-skip'>"
        "<span class='cc-wf-badge'>L1 · Per-query tag</span>"
        "<div class='cc-wf-main'><div class='cc-wf-sig'>A business tag on each query</div>"
        "<div class='cc-wf-set'>Not used for CoCo — CoCo stamps its own query tag, so a "
        "per-query business tag doesn't stick.</div></div>"
        "<span class='cc-chip cc-chip-skip'>n/a</span></div>"
        "<div class='cc-wf-row cc-wf-skip'>"
        "<span class='cc-wf-badge'>L2 · Session tag</span>"
        "<div class='cc-wf-main'><div class='cc-wf-sig'>A project chosen at the start of a session</div>"
        "<div class='cc-wf-set'>Not available out of the box — see <i>Advanced</i> below for a "
        "session-based option you can add.</div></div>"
        "<span class='cc-chip cc-chip-skip'>n/a</span></div>",
        unsafe_allow_html=True)

    row_cls = {"HIGH": "cc-wf-hi", "MEDIUM": "cc-wf-med", "MED": "cc-wf-med", "NONE": "cc-wf-none"}
    chip_cls = {"HIGH": "cc-chip-hi", "MEDIUM": "cc-chip-med", "MED": "cc-chip-med",
                "NONE": "cc-chip-none"}
    for lv in sorted(WATERFALL_LEVELS, key=lambda x: x["order"]):
        conf = str(lv.get("confidence", "MEDIUM")).upper()
        rc = row_cls.get(conf, "cc-wf-med")
        cc = chip_cls.get(conf, "cc-chip-med")
        badge = friendly.get(lv.get("method", ""), lv.get("method", ""))
        setup = lv.get("you_set_up", "")
        setup_html = (f"<div class='cc-wf-set'>Set up: {setup}</div>"
                      if setup and setup != "—" else "")
        st.markdown(
            f"<div class='cc-wf-row {rc}'>"
            f"<span class='cc-wf-badge'>{badge}</span>"
            f"<div class='cc-wf-main'><div class='cc-wf-sig'>{lv.get('signal', '')}</div>"
            f"{setup_html}</div>"
            f"<span class='cc-chip {cc}'>{conf}</span></div>",
            unsafe_allow_html=True)


def _reattr_callout():
    st.markdown(
        "<div class='cc-callout'><div class='h'>What \"Re-run attribution\" does</div>"
        "<p><b>Reads</b> (read-only): your identity mappings and tags, the usage rollups, and "
        "your role grants.</p>"
        "<p><b>Writes only</b> the app's own attribution records — never your users, roles, grants, "
        "credit limits, or warehouses. It's safe to run anytime and idempotent; run it right after "
        "editing a lever below. (Refreshing warehouse usage is a separate step on CoCo Warehouse "
        "Activity.)</p></div>",
        unsafe_allow_html=True)


def _render_levers(session):
    """Unify the three identity levers on one page: L4 user tags, L3 service, L5 role."""
    st.markdown("#### Set up identity & tags — the three levers")
    st.caption("Attribution uses the single best signal per user (first-match-wins). Set any of "
               "these; the app writes only its own tables, never your account objects.")
    tabs = st.tabs(["L4 · User tags (M1)", "L3 · Service accounts (M2 / M3)", "L5 · Roles (M3)"])

    with tabs[0]:
        st.markdown(
            "<div class='cc-lever-title'>L4 · User tags</div>"
            "<div class='cc-lever-sub'>What team / vertical a person is, plus a partner flag. "
            "Best for internal cross-charge (M1). Confidence: Medium.</div>",
            unsafe_allow_html=True)
        tagging.render_tag_editor(session, key_prefix="attr", as_expander=False)

    with tabs[1]:
        st.markdown(
            "<div class='cc-lever-title'>L3 · Service accounts</div>"
            "<div class='cc-lever-sub'>Map a dedicated service / partner username to a billing "
            "entity — highest confidence. Best for M2 (build &amp; deploy) and M3.</div>",
            unsafe_allow_html=True)
        su = _load_mapping(session, TABLE_SERVICE_USER_MAPPING)
        edited = st.data_editor(
            su, key="attr_su_editor", use_container_width=True, hide_index=True,
            num_rows="dynamic",
            column_config={
                "USER_NAME": st.column_config.TextColumn("Service username", required=True),
                "ENTITY": st.column_config.TextColumn("Billing entity", required=True),
                "ENTITY_TYPE": st.column_config.SelectboxColumn(
                    "Type", options=_ENTITY_TYPES, default="CUSTOMER"),
            })
        if st.button("Save service-account mappings", key="attr_save_su", type="primary"):
            _save_mapping(session, TABLE_SERVICE_USER_MAPPING, edited)

    with tabs[2]:
        st.markdown(
            "<div class='cc-lever-title'>L5 · Roles</div>"
            "<div class='cc-lever-sub'>Map a Snowflake role to a billing entity — used when a "
            "partner's staff share a role (common in M3). Confidence: Medium.</div>",
            unsafe_allow_html=True)
        rl = _load_mapping(session, TABLE_ROLE_MAPPING)
        edited_r = st.data_editor(
            rl, key="attr_role_editor", use_container_width=True, hide_index=True,
            num_rows="dynamic",
            column_config={
                "ROLE_NAME": st.column_config.TextColumn("Role name", required=True),
                "ENTITY": st.column_config.TextColumn("Billing entity", required=True),
                "ENTITY_TYPE": st.column_config.SelectboxColumn(
                    "Type", options=_ENTITY_TYPES, default="CUSTOMER"),
            })
        if st.button("Save role mappings", key="attr_save_role", type="primary"):
            _save_mapping(session, TABLE_ROLE_MAPPING, edited_r)


# ── DIY deeper-grain (project/engagement) starter kit — reconstructed template ──
_DIY_SQL = """-- Project-level attribution setup. Adds project/engagement grain by
-- joining CoCo usage to a project via the session id CoCo emits in its query tag.
--
-- Replace <YOUR_DB>.<YOUR_SCHEMA> below with the database.schema where this app
-- is installed (the same target you set in snowflake.yml).

-- 1) A small map the beacon populates: session -> project.
CREATE TABLE IF NOT EXISTS <YOUR_DB>.<YOUR_SCHEMA>.CC_SESSION_PROJECT_MAP (
    SESSION_ID  VARCHAR PRIMARY KEY,
    PROJECT     VARCHAR,
    CUSTOMER    VARCHAR,
    USER_NAME   VARCHAR,
    TAGGED_AT   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2) Join CoCo warehouse usage to the project via the emitted session id.
CREATE OR REPLACE VIEW <YOUR_DB>.<YOUR_SCHEMA>.V_SESSION_PROJECT_USAGE AS
SELECT qh.START_TIME::DATE AS USAGE_DATE,
       qh.USER_NAME,
       COALESCE(TRY_PARSE_JSON(qh.QUERY_TAG):desktop_session_id::string,
                TRY_PARSE_JSON(qh.QUERY_TAG):agent_session_id::string) AS SESSION_ID,
       m.PROJECT, m.CUSTOMER
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
LEFT JOIN <YOUR_DB>.<YOUR_SCHEMA>.CC_SESSION_PROJECT_MAP m
  ON m.SESSION_ID = COALESCE(
        TRY_PARSE_JSON(qh.QUERY_TAG):desktop_session_id::string,
        TRY_PARSE_JSON(qh.QUERY_TAG):agent_session_id::string)
WHERE TRY_PARSE_JSON(qh.QUERY_TAG):app::string ILIKE 'cortex_code%';
"""

_DIY_HOOKS = """{
  "SessionStart": [
    { "hooks": [ { "type": "command",
        "command": "python3 ~/.snowflake/cortex/hooks/coco_project_beacon.py" } ] }
  ]
}
"""

_DIY_BEACON = """#!/usr/bin/env python3
# coco_project_beacon.py — runs at CoCo SessionStart (non-blocking). Prompts for a
# project, then fires a beacon query whose query tag carries the session id +
# project, and upserts the session->project map.
import json, os, sys, subprocess

def main():
    session_id = os.environ.get("CORTEX_SESSION_ID", "")  # or parse hook stdin
    project = input("Project / engagement for this session (blank = UNTAGGED): ").strip() or "UNTAGGED"
    tag = json.dumps({"project": project, "coco_session_id": session_id})
    # Fire a beacon query + upsert the map (uses the 'snow' CLI connection).
    sql = (
        f"ALTER SESSION SET QUERY_TAG = '{tag}'; SELECT 1;"
        f"MERGE INTO <YOUR_DB>.<YOUR_SCHEMA>.CC_SESSION_PROJECT_MAP t "
        f"USING (SELECT '{session_id}' AS SESSION_ID, '{project}' AS PROJECT) s "
        f"ON t.SESSION_ID = s.SESSION_ID "
        f"WHEN NOT MATCHED THEN INSERT (SESSION_ID, PROJECT) VALUES (s.SESSION_ID, s.PROJECT);"
    )
    subprocess.run(["snow", "sql", "-q", sql], check=False)

if __name__ == "__main__":
    main()
"""

_DIY_README = """CoCo project-level attribution — setup kit
==========================================
Adds project/engagement-grain attribution on top of the user/role tagging the app
already supports.

HONEST CAVEATS (read first)
- Client-side: the hook lives on each user's machine (~/.snowflake/cortex/hooks/).
  Deploy it per-device via MDM (Jamf/Intune/SCCM). It CANNOT be enforced from
  Snowflake or via managed-settings.json (managed settings has no hooks section).
- Non-blocking: SessionStart cannot force a project choice; users can skip it
  (default to UNTAGGED). It is a best-effort nudge, not a hard gate.
- Query tags don't survive CoCo: this works by a SEPARATE beacon query + a join
  on the session id CoCo emits — not by tagging CoCo's own queries.
- Latency: ACCOUNT_USAGE.QUERY_HISTORY lags; expect a delay before rows appear.

FILES
- setup.sql       Creates CC_SESSION_PROJECT_MAP + V_SESSION_PROJECT_USAGE.
- hooks.json      SessionStart hook -> runs the beacon. Place in
                  ~/.snowflake/cortex/hooks.json (or merge into the existing one).
- coco_project_beacon.py  The beacon script. Place in ~/.snowflake/cortex/hooks/.

STEPS
1. Run setup.sql once (ACCOUNTADMIN or the app owner role).
2. Distribute hooks.json + coco_project_beacon.py to each user's machine.
3. Verify V_SESSION_PROJECT_USAGE returns rows after some tagged sessions, then
   group your bill by PROJECT / CUSTOMER from that view.
"""


def _diy_starter_kit_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("coco_project_attribution/setup.sql", _DIY_SQL)
        z.writestr("coco_project_attribution/hooks.json", _DIY_HOOKS)
        z.writestr("coco_project_attribution/coco_project_beacon.py", _DIY_BEACON)
        z.writestr("coco_project_attribution/README.txt", _DIY_README)
    return buf.getvalue()


def _render_diy(session):
    with st.expander("Go a grain deeper: project / engagement attribution (advanced, optional)",
                     expanded=False):
        st.markdown(
            "User / role tagging (above) covers most chargeback. If you also need "
            "**project- or engagement-level** grain, you can add a lightweight session overlay. "
            "Here's the design — the downloadable kit has everything to set it up.")
        st.markdown(
            "- At the **start of each CoCo session**, the user is asked which project / engagement "
            "they're working on.\n"
            "- That choice is **tagged to the session** (via a tiny beacon query) — no change to "
            "your users or roles.\n"
            "- The app then **joins CoCo usage to the project** using the session id CoCo emits, "
            "so bills can be split by project or customer.")
        st.warning(
            "Before you commit: this runs **on each user's machine** (deployed by your IT / MDM), "
            "the project prompt is a **best-effort nudge** (users can skip it), and newly tagged "
            "usage appears after the usual reporting lag. It's an add-on you operate, not a "
            "built-in toggle.")
        st.download_button(
            "Download setup kit (.zip)", data=_diy_starter_kit_bytes(),
            file_name="coco_project_attribution_kit.zip",
            mime="application/zip", key="attr_diy_dl")
        st.caption("The kit includes the SQL to run, the CoCo session hook, the beacon script, "
                   "and a step-by-step README.")


def render(session):
    st.header("Attribution & Tags",
              help="How CoCo usage is assigned to a billing entity — the three identity levers, "
                   "the waterfall, and the queue for anything unidentified.")

    _ensure_tables(session)
    tagging.ensure_tags_table(session)
    usd_rate = float(get_app_setting(session, "USD_PER_CREDIT", "2.00"))

    # ── Zone 1 · Guidance (collapsible) — how attribution works ──────────────
    with st.expander("How attribution works", expanded=True):
        _flow_cards()
        st.write("")
        _responsibility_callout()
        st.markdown("**How the waterfall resolves** — for each user we take the single best "
                    "identity signal available (first match wins). The more you set up, the more "
                    "of your spend is attributed, and at higher confidence. Anything with no "
                    "signal goes to the Unattributed queue.")
        _waterfall_ladder()
        _reattr_callout()

    st.divider()

    # ── Zone 2 · Set up identity & tags (actions) ────────────────────────────
    _render_levers(session)

    st.divider()

    # ── Zone 3 · Run & review (your data) ────────────────────────────────────
    st.markdown("#### Run & review")
    rc1, rc2 = st.columns([1, 3])
    with rc1:
        days = st.selectbox("Lookback (days)", [7, 14, 30, 60, 90], index=2, key="attr_days")
    with rc2:
        st.write(""); st.write("")
        if st.button("Re-run attribution", key="attr_rerun", type="primary",
                     help="Recompute attribution for the window using your current mappings and "
                          "tags, and refresh the unattributed queue."):
            _rerun_attribution(session, days)

    df = _load_attr(session, days)
    if df.empty:
        st.info("No attribution yet. Set up a lever above and click **Re-run attribution** "
                "(or wait for the daily refresh) once usage exists in the window.")
    else:
        total = float(df["TOTAL_CREDITS"].sum())
        attributed = float(df[df["ATTR_METHOD"] != "UNATTRIBUTED"]["TOTAL_CREDITS"].sum())
        rate = (attributed / total * 100.0) if total > 0 else 0.0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Credits", f"{total:,.4f}")
        k2.metric("Attributed", f"{attributed:,.4f}")
        k3.metric("Attribution Rate", f"{rate:.1f}%")
        k4.metric("Est. Cost (USD)", f"${total * usd_rate:,.2f}")

        c1b, c2b = st.columns(2)
        with c1b:
            st.markdown("**Credits by confidence**")
            by_c = (df.groupby("CONFIDENCE", as_index=False)
                      .agg(CREDITS=("TOTAL_CREDITS", "sum")))
            by_c["CREDITS"] = by_c["CREDITS"].round(4)
            ch = (alt.Chart(by_c).mark_bar()
                  .encode(x=alt.X("CREDITS:Q", title="Credits"),
                          y=alt.Y("CONFIDENCE:N", sort="-x", title=""),
                          color=alt.Color("CONFIDENCE:N",
                              scale=alt.Scale(domain=list(_CONF_COLOR.keys()),
                                              range=list(_CONF_COLOR.values())),
                              legend=None),
                          tooltip=["CONFIDENCE:N", alt.Tooltip("CREDITS:Q", format=".4f")])
                  .properties(height=max(120, len(by_c) * 44))
                  .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch, use_container_width=True)
        with c2b:
            st.markdown("**Credits by entity** (attributed only)")
            att = df[df["ENTITY"].notna()]
            if att.empty:
                st.caption("Nothing attributed yet — add a mapping or tag above, then re-run.")
            else:
                by_e = (att.groupby("ENTITY", as_index=False)
                           .agg(CREDITS=("TOTAL_CREDITS", "sum"))
                           .sort_values("CREDITS", ascending=False).head(15))
                by_e["CREDITS"] = by_e["CREDITS"].round(4)
                ch = (alt.Chart(by_e).mark_bar()
                      .encode(x=alt.X("CREDITS:Q", title="Credits"),
                              y=alt.Y("ENTITY:N", sort="-x", title=""),
                              color=alt.value(_P),
                              tooltip=["ENTITY:N", alt.Tooltip("CREDITS:Q", format=".4f")])
                      .properties(height=max(120, len(by_e) * 32))
                      .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch, use_container_width=True)

    st.markdown("##### Unattributed queue")
    queue = _load_queue(session)
    if queue.empty:
        st.success("Queue is clear — all usage in the window is attributed.")
    else:
        q_cr = float(queue["TOTAL_CREDITS"].sum())
        st.caption(f"{len(queue)} user(s) with **{q_cr:,.4f} credits** "
                   f"(~${q_cr * usd_rate:,.2f}) unattributed. Map them above, then re-run.")
        st.dataframe(queue, use_container_width=True, hide_index=True,
                     column_config={
                         "USER_NAME": st.column_config.TextColumn("User"),
                         "TOKEN_CREDITS": st.column_config.NumberColumn("Token cr", format="%.4f"),
                         "WAREHOUSE_CREDITS": st.column_config.NumberColumn("WH cr", format="%.4f"),
                         "TOTAL_CREDITS": st.column_config.NumberColumn("Total cr", format="%.4f"),
                         "LAST_SEEN": st.column_config.DateColumn("Last seen"),
                         "STATUS": st.column_config.TextColumn("Status"),
                     })

    st.divider()

    # ── Zone 4 · Advanced (optional) ─────────────────────────────────────────
    st.markdown("#### Advanced (optional)")
    _render_diy(session)

"""
Shared cost-tag (L4) editor + read-only tag sync.
=================================================
Used by both the Chargeback (Generate Bill) page and the Attribution & Tags page
so the L4 user-tag lever has ONE implementation writing CC_COST_TAGS. All logic is
read-only against the account (it reads ACCOUNT_USAGE + the app's own tables and
MERGEs only into CC_COST_TAGS — it never alters users, roles, or grants).
"""

import pandas as pd
import streamlit as st

from config import (
    TABLE_COST_TAGS, TABLE_USAGE_DAILY, SP_SYNC_COST_TAGS,
    fq_table, fq_sp, escape_sql_literal, get_current_user,
)
from audit import log_activity


def ensure_tags_table(session):
    """Self-heal: create CC_COST_TAGS if a live deployment predates the DDL."""
    try:
        session.sql(f"""
            CREATE TABLE IF NOT EXISTS {fq_table(session, TABLE_COST_TAGS)} (
                USER_NAME   VARCHAR(255) NOT NULL PRIMARY KEY,
                VERTICAL    VARCHAR(255),
                IS_PARTNER  BOOLEAN DEFAULT FALSE,
                UPDATED_BY  VARCHAR(255),
                UPDATED_AT  TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """).collect()
    except Exception:
        pass


@st.cache_data(ttl=120, show_spinner=False)
def tags_populated(_session) -> bool:
    try:
        tbl = fq_table(_session, TABLE_COST_TAGS)
        r = _session.sql(
            f"SELECT COUNT(*) AS N FROM {tbl} "
            f"WHERE VERTICAL IS NOT NULL OR IS_PARTNER = TRUE"
        ).collect()
        return int(r[0]["N"]) > 0
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def load_tag_grid(_session) -> pd.DataFrame:
    """Current tags LEFT-joined onto the active CoCo-user roster (seed on empty)."""
    tags = fq_table(_session, TABLE_COST_TAGS)
    usage = fq_table(_session, TABLE_USAGE_DAILY)
    try:
        df = _session.sql(f"""
            SELECT r.USER_NAME,
                   t.VERTICAL,
                   COALESCE(t.IS_PARTNER, FALSE) AS IS_PARTNER
            FROM (SELECT DISTINCT USER_NAME FROM {usage}
                  WHERE USAGE_DATE >= DATEADD('day', -365, CURRENT_DATE())) r
            LEFT JOIN {tags} t ON r.USER_NAME = t.USER_NAME
            ORDER BY r.USER_NAME
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame(columns=["USER_NAME", "VERTICAL", "IS_PARTNER"])


def sync_tags_from_account(session):
    """Read-only snapshot of user object tags -> CC_COST_TAGS via the SP."""
    try:
        with st.spinner("Reading user tags from ACCOUNT_USAGE.TAG_REFERENCES…"):
            r = session.sql(f"CALL {fq_sp(session, SP_SYNC_COST_TAGS)}()").collect()
        st.cache_data.clear()
        msg = str(r[0][0]) if r else "Sync complete."
        log_activity(session, "CHARGEBACK_TAGS_SYNCED", details={"result": msg[:200]})
        st.success(msg)
        st.rerun()
    except Exception as e:
        st.error(f"Sync failed: {str(e)[:200]}. The sync reads ACCOUNT_USAGE and needs the "
                 "app owner role to have IMPORTED PRIVILEGES on SNOWFLAKE.")


def save_tags(session, edited: pd.DataFrame):
    tbl = fq_table(session, TABLE_COST_TAGS)
    actor = get_current_user(session)
    rows = []
    for _, r in edited.iterrows():
        user = str(r["USER_NAME"]).strip()
        if not user:
            continue
        vert = r.get("VERTICAL")
        vert_sql = "NULL" if (vert is None or str(vert).strip() == "" or pd.isna(vert)) \
            else f"'{escape_sql_literal(str(vert).strip())}'"
        is_partner = "TRUE" if bool(r.get("IS_PARTNER")) else "FALSE"
        rows.append(f"('{escape_sql_literal(user)}', {vert_sql}, {is_partner})")
    if not rows:
        st.warning("Nothing to save.")
        return
    values = ",\n".join(rows)
    try:
        session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT * FROM VALUES {values}
                   AS v(USER_NAME, VERTICAL, IS_PARTNER)) s
            ON t.USER_NAME = s.USER_NAME
            WHEN MATCHED THEN UPDATE SET
                VERTICAL = s.VERTICAL, IS_PARTNER = s.IS_PARTNER,
                UPDATED_BY = '{escape_sql_literal(actor)}', UPDATED_AT = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT
                (USER_NAME, VERTICAL, IS_PARTNER, UPDATED_BY, UPDATED_AT)
                VALUES (s.USER_NAME, s.VERTICAL, s.IS_PARTNER,
                        '{escape_sql_literal(actor)}', CURRENT_TIMESTAMP())
        """).collect()
        tagged = sum(1 for _, r in edited.iterrows()
                     if (str(r.get("VERTICAL") or "").strip()) or bool(r.get("IS_PARTNER")))
        log_activity(session, "CHARGEBACK_TAGS_SAVED",
                     details={"rows": len(rows), "tagged": tagged})
        st.cache_data.clear()
        st.success(f"Saved {len(rows)} tag rows.")
        st.rerun()
    except Exception as e:
        st.error(f"Save failed: {str(e)[:160]}")


def _tag_editor_body(session, key_prefix: str, show_guidance: bool):
    if show_guidance:
        st.markdown(
            "**What to tag, and how.** Attribution by vertical or partner needs each user "
            "identified. Two low-effort paths, both **read-only** for the app — it never "
            "alters users, roles, or grants in your account:")
        st.markdown(
            "- **Set Snowflake tags on your users** (recommended), then click *Sync tags from "
            "account* below. The app reads these tag keys (case-insensitive):\n"
            "    - **Vertical / team** → tag `VERTICAL` (or `COST_CENTER`, `TEAM`, `BUSINESS_UNIT`)\n"
            "    - **Partner flag** → tag `COCO_PARTNER` (or `IS_PARTNER`, `PARTNER`) with a "
            "truthy value (`TRUE`/`YES`/`1`)\n"
            "- **Or edit the grid below** manually for a handful of users.")
        with st.popover("How to set the tags (SQL / SCIM)"):
            st.code(
                "-- One-time: create the tags (any schema you own)\n"
                "CREATE TAG IF NOT EXISTS VERTICAL;\n"
                "CREATE TAG IF NOT EXISTS COCO_PARTNER;\n\n"
                "-- Assign to users (the customer/platform owner does this, not the app)\n"
                "ALTER USER jdoe   SET TAG VERTICAL = 'Retail_BI';\n"
                "ALTER USER svc_ph SET TAG COCO_PARTNER = 'TRUE';",
                language="sql")
            st.caption("Enterprises usually push these via SCIM (Okta `costCenter` / Entra "
                       "`department` → a Snowflake tag). Tag reads can lag up to ~2h, so the "
                       "nightly sync (or the button) picks changes up then. Historical usage is "
                       "attributed automatically once the tag exists — billing is keyed at the "
                       "user level from day 0.")
        st.caption("Saved for billing; the vertical / partner group-by options unlock once any "
                   "tag is set. The sync is non-destructive — it fills blanks and never erases a "
                   "manually-entered tag.")

    grid = load_tag_grid(session)
    if grid.empty:
        st.info("No active Cortex Code users found to tag yet.")
        if st.button("Sync tags from account", key=f"{key_prefix}_sync_tags_empty",
                     help="Read your users' Snowflake tags (read-only) into the app for billing."):
            sync_tags_from_account(session)
        return
    edited = st.data_editor(
        grid, key=f"{key_prefix}_tag_editor", use_container_width=True, hide_index=True,
        num_rows="fixed",
        column_config={
            "USER_NAME":  st.column_config.TextColumn("User", disabled=True),
            "VERTICAL":   st.column_config.TextColumn(
                "Vertical / Team", help="e.g. Team_BI, Project_A"),
            "IS_PARTNER": st.column_config.CheckboxColumn("Partner?"),
        })
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("Save tags", key=f"{key_prefix}_save_tags", type="primary",
                     use_container_width=True):
            save_tags(session, edited)
    with bcol2:
        if st.button("Sync tags from account", key=f"{key_prefix}_sync_tags",
                     use_container_width=True,
                     help="Read your users' Snowflake tags (read-only) into the app for billing. "
                          "Fills blanks; keeps manual edits."):
            sync_tags_from_account(session)


def render_tag_editor(session, key_prefix: str = "cb", as_expander: bool = True,
                      expanded: bool = False, show_guidance: bool = True):
    """L4 user-tag editor. as_expander=True wraps it in an expander (Chargeback);
    False renders inline (Attribution lever card)."""
    ensure_tags_table(session)
    if as_expander:
        with st.expander("Set up cost tags  ·  enables By Vertical / By Partner-flag",
                         expanded=expanded):
            _tag_editor_body(session, key_prefix, show_guidance)
        st.divider()
    else:
        _tag_editor_body(session, key_prefix, show_guidance)

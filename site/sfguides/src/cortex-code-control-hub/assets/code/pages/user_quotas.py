"""
CoCo Control Hub — Native Per-User Quotas (Preview)
=====================================================
Hard monthly/daily credit enforcement via Snowflake SNOWFLAKE.CORE.QUOTA objects.
Distinct from CoCo's soft daily limits (ALTER USER) — these are Snowflake-native
blocks that fire within minutes of a user breaching their quota.

Docs: https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas
"""

import json
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from audit import log_activity
from config import (
    TABLE_NATIVE_QUOTAS,
    SP_MANAGE_QUOTA,
    AI_BUDGET_DOMAINS,
    escape_sql_literal,
    fq_table,
    fq_sp,
    get_current_user,
)
from utils import get_session, list_roles

_BG = "#0e1117"
_DOCS_URL = "https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas"


def _sec(title):
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=False)
def _load_quotas(_session):
    tbl = fq_table(_session, TABLE_NATIVE_QUOTAS)
    try:
        df = _session.sql(f"""
            SELECT QUOTA_NAME, QUOTA_LABEL, COHORT_ROLE, MONTHLY_LIMIT, DAILY_LIMIT,
                   DOMAINS, BLOCK_ENFORCEMENT, NOTIFY_80_PCT, NOTIFY_100_PCT,
                   TAGGED_USERS, LAST_SYNCED_AT, CREATED_AT
            FROM {tbl}
            WHERE IS_ACTIVE = TRUE
            ORDER BY CREATED_AT DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def _call_sp(session, action, quota_name, params=None):
    sp = fq_sp(session, SP_MANAGE_QUOTA)
    params_sql = f"PARSE_JSON('{json.dumps(params or {}).replace(chr(39), chr(39)+chr(39))}')"
    try:
        r = session.sql(f"CALL {sp}('{action}', '{quota_name}', {params_sql})").collect()
        raw = r[0][0] if r else "{}"
        return json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


def _quota_name_from_label(label: str) -> str:
    import re
    safe = re.sub(r"[^A-Z0-9_]", "_", label.upper().strip())
    return f"CC_QUOTA_{safe}"[:128]


def render(session):
    st.header(
        "Native Per-User Quotas",
        help="Hard monthly/daily credit enforcement via Snowflake's built-in quota objects. "
             "Blocks fire within minutes when a user breaches their limit and auto-release "
             "at cycle reset. Preview feature — requires SNOWFLAKE.QUOTA_CREATOR on CC_SP_OWNER_ROLE.",
    )

    # ── Preview banner ────────────────────────────────────────────────────────
    st.warning(
        f"⚗️ **Preview feature** — Per-user quotas use Snowflake's `SNOWFLAKE.CORE.QUOTA` objects "
        f"which are currently in public preview. Setup Phase A must be re-run to grant "
        f"`SNOWFLAKE.QUOTA_CREATOR` to `CC_SP_OWNER_ROLE` and create the `CC_COHORT_TAG`. "
        f"Phase C must be re-run to create `SP_CC_MANAGE_QUOTA`.  "
        f"[Read the Snowflake docs]({_DOCS_URL})",
    )

    # ── Prerequisites check ───────────────────────────────────────────────────
    with st.expander("Prerequisites check", expanded=False):
        st.caption("Run these checks before creating your first quota.")
        prereqs_ok = True
        try:
            sp = fq_sp(session, SP_MANAGE_QUOTA)
            session.sql(f"DESCRIBE PROCEDURE {sp}(VARCHAR, VARCHAR, VARIANT)").collect()
            st.success("✓ SP_CC_MANAGE_QUOTA exists")
        except Exception:
            st.error("✗ SP_CC_MANAGE_QUOTA missing — run Setup → Phase C")
            prereqs_ok = False

        try:
            db, schema = session.get_current_database(), session.get_current_schema()
            rows = session.sql(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TAGS
                WHERE TAG_NAME = 'CC_COHORT_TAG' AND TAG_SCHEMA = '{schema}'
            """).collect()
            if rows and int(rows[0][0]) > 0:
                st.success("✓ CC_COHORT_TAG exists")
            else:
                st.warning("⚠ CC_COHORT_TAG not found — re-run Setup Phase A to create it")
        except Exception:
            st.warning("⚠ Could not check CC_COHORT_TAG — re-run Setup Phase A")

        try:
            rows = session.sql("""
                SELECT GRANTEE_NAME FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
                WHERE PRIVILEGE = 'EXECUTE'
                  AND GRANTED_ON = 'DATABASE ROLE'
                  AND NAME = 'SNOWFLAKE.QUOTA_CREATOR'
                  AND GRANTEE_NAME LIKE 'CC_SP_OWNER%'
                  AND DELETED_ON IS NULL
                LIMIT 1
            """).collect()
            if rows:
                st.success(f"✓ SNOWFLAKE.QUOTA_CREATOR granted to {rows[0][0]}")
            else:
                st.warning("⚠ SNOWFLAKE.QUOTA_CREATOR not granted — re-run Setup Phase A or "
                           "run: `GRANT DATABASE ROLE SNOWFLAKE.QUOTA_CREATOR TO ROLE CC_SP_OWNER_ROLE`")
        except Exception:
            st.info("ℹ Could not verify QUOTA_CREATOR — ACCOUNT_USAGE may have latency")

    # ── How it differs from daily limits ─────────────────────────────────────
    with st.expander("How this differs from CoCo's existing daily limits", expanded=False):
        st.markdown("""
| | **CoCo Daily Limits** (existing) | **Native Per-User Quotas** (this page) |
|---|---|---|
| **Mechanism** | `ALTER USER SET CORTEX_CODE_*_DAILY_EST_CREDIT_LIMIT_PER_USER` | `SNOWFLAKE.CORE.QUOTA` object |
| **Granularity** | Per-surface (CLI / Snowsight / Desktop) per day | Monthly + optional daily, across selected domains |
| **Enforcement** | Snowflake blocks at midnight UTC daily | Snowflake blocks within **minutes** of breach |
| **Limit type** | Different limit per surface | Same limit per user in the quota scope |
| **Reset** | Midnight UTC each day | Monthly (1st UTC) or daily |
| **Scope** | Per-user override or cohort default | All users or tag-scoped cohort |
| **User notification** | None | Email to user at threshold % |
| **Overshoot** | Exact | Up to ~minutes of spend past the limit |

Use **daily limits** for precise per-surface control. Use **native quotas** for a hard monthly cap with user notifications.
        """)

    st.divider()

    actor = get_current_user(session)

    # ── Existing quotas ───────────────────────────────────────────────────────
    _sec("Active Quotas")
    quotas_df = _load_quotas(session)

    if quotas_df.empty:
        st.info("No native quotas configured yet. Create one below.")
    else:
        for _, row in quotas_df.iterrows():
            qname  = str(row["QUOTA_NAME"])
            qlabel = str(row["QUOTA_LABEL"])
            # Handle NaN/None from pandas for nullable columns
            def _notnull(v):
                try:
                    return v is not None and not pd.isna(v) and str(v) not in ("", "None", "nan")
                except Exception:
                    return v is not None
            cohort = str(row["COHORT_ROLE"]) if _notnull(row["COHORT_ROLE"]) else "All Users"
            mlimit = float(row["MONTHLY_LIMIT"] or 0)
            dlimit = float(row["DAILY_LIMIT"]) if _notnull(row["DAILY_LIMIT"]) else None
            block  = bool(row["BLOCK_ENFORCEMENT"])
            tagged = int(row["TAGGED_USERS"] or 0)
            synced = str(row["LAST_SYNCED_AT"])[:19] if _notnull(row["LAST_SYNCED_AT"]) else "never"

            with st.container(border=True):
                hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 3])
                hcol1.markdown(f"**{qlabel}**  \n`{qname}`")
                hcol2.metric("Monthly Limit", f"{mlimit:,.0f} cr/user")
                hcol3.metric("Cohort Scope", cohort)
                hcol4.markdown(
                    f"Block enforcement: {'🔴 ON' if block else '⚫ OFF'}  \n"
                    f"Tagged users: {tagged}  \n"
                    f"Last synced: {synced}"
                )

                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

                with btn_col1:
                    if st.button("🔍 View Active Blocks", key=f"blocks_{qname}", use_container_width=True):
                        with st.spinner("Loading active blocks…"):
                            result = _call_sp(session, "GET_ACTIVE_BLOCKS", qname)
                        if result.get("ok"):
                            blocks = result.get("blocks", [])
                            if blocks:
                                st.dataframe(pd.DataFrame(blocks), use_container_width=True, hide_index=True)
                            else:
                                st.success("No users currently blocked.")
                        else:
                            st.error(f"✗ {result.get('error')}")

                with btn_col2:
                    if st.button("⚙ View Config", key=f"cfg_{qname}", use_container_width=True,
                                 help="Shows the live configuration from the Snowflake quota object."):
                        with st.spinner("Loading config…"):
                            result = _call_sp(session, "GET_CONFIG", qname)
                        if result.get("ok"):
                            cfg = result.get("config", {})
                            c1, c2 = st.columns(2)
                            c1.metric("Monthly Limit (live)", cfg.get("PER_USER_LIMIT", "—") + " cr")
                            c2.metric("Daily Limit (live)", cfg.get("PER_USER_LIMIT_DAILY", "None") + " cr")
                            c1.metric("Block Enforcement", cfg.get("BLOCK_ENFORCEMENT_ENABLED", "—"))
                            c2.metric("Refresh Tier", cfg.get("REFRESH_TIER", "—"))
                        else:
                            st.error(f"✗ {result.get('error')}")

                with btn_col3:
                    if cohort != "All Users" and st.button(
                        "🔄 Sync Members", key=f"sync_{qname}", use_container_width=True,
                        help="Re-tag all current cohort members. Run after membership changes."
                    ):
                        with st.spinner(f"Tagging members of {cohort}…"):
                            result = _call_sp(session, "TAG_USERS", qname, {"cohort_role": cohort})
                        if result.get("ok") is not False:
                            n = result.get("tagged", 0)
                            st.success(f"✓ Tagged {n} user(s)")
                            _load_quotas.clear()
                            log_activity(session, "SYNC_QUOTA_MEMBERS",
                                         details={"quota": qname, "cohort": cohort, "tagged": n})
                        else:
                            st.error(f"✗ {result.get('error')}")

                with btn_col4:
                    confirm_key = f"confirm_del_{qname}"
                    if st.session_state.get(confirm_key):
                        if st.button("✓ Confirm Delete", key=f"del_ok_{qname}",
                                     use_container_width=True, type="primary"):
                            with st.spinner(f"Deleting {qname}…"):
                                result = _call_sp(session, "DELETE", qname,
                                                  {"cohort_role": cohort if cohort != "All Users" else None})
                            if result.get("ok"):
                                st.session_state.pop(confirm_key, None)
                                _load_quotas.clear()
                                log_activity(session, "DELETE_QUOTA", details={"quota": qname})
                                st.rerun()
                            else:
                                errs = result.get("errors", [])
                                st.error(f"✗ {'; '.join(errs) if errs else result.get('error')}")
                        if st.button("✗ Cancel", key=f"del_cancel_{qname}", use_container_width=True):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                    else:
                        if st.button("🗑 Delete", key=f"del_{qname}", use_container_width=True,
                                     type="secondary", help="Drop the quota object and untag all users."):
                            st.session_state[confirm_key] = True
                            st.rerun()

    st.divider()

    # ── Create new quota ──────────────────────────────────────────────────────
    with st.expander("➕ Create New Quota", expanded=quotas_df.empty):
        st.caption(
            "Creates a `SNOWFLAKE.CORE.QUOTA` object, adds the selected domain(s), sets the "
            "per-user limit, and (if cohort-scoped) tags all current cohort members. "
            "All users in the same quota get the **same** monthly limit — use separate quotas "
            "for different tiers (standard vs high-usage teams)."
        )

        c1, c2 = st.columns(2)
        with c1:
            quota_label = st.text_input(
                "Quota name", placeholder="e.g. Standard Users",
                key="nq_label",
                help="Display name. The Snowflake object will be named CC_QUOTA_<UPPER_LABEL>."
            )
        with c2:
            roles = ["All Users"] + list_roles(session)
            cohort_sel = st.selectbox(
                "Cohort scope", roles, key="nq_cohort",
                help="'All Users' = quota applies to everyone in the account. "
                     "Selecting a role tags all current members and scopes the quota to that tag."
            )

        c3, c4 = st.columns(2)
        with c3:
            monthly_limit = st.number_input(
                "Monthly credit limit per user", min_value=1, value=100, step=10,
                key="nq_monthly",
                help="Credits/month per user. Same limit applies to all users in scope."
            )
        with c4:
            daily_limit_raw = st.number_input(
                "Daily credit limit per user (0 = none)", min_value=0, value=0, step=5,
                key="nq_daily",
                help="Optional. Additional daily cap within the monthly limit. 0 = no daily limit."
            )

        st.markdown("**Domains to monitor**")
        domain_cols = st.columns(len(AI_BUDGET_DOMAINS))
        selected_domains = []
        for i, domain in enumerate(AI_BUDGET_DOMAINS):
            with domain_cols[i]:
                default = domain == "CORTEX CODE"
                if st.checkbox(domain, value=default, key=f"nq_dom_{i}"):
                    selected_domains.append(domain)

        st.markdown("**Enforcement & notifications**")
        ecol1, ecol2, ecol3 = st.columns(3)
        with ecol1:
            block_enforce = st.toggle(
                "Block enforcement", value=True, key="nq_block",
                help="Snowflake automatically blocks the user within minutes of hitting the limit. "
                     "Blocks auto-release at cycle reset."
            )
        with ecol2:
            notify_80 = st.checkbox(
                "Notify at 80% (projected)", value=True, key="nq_n80",
                help="Send email to user when projected spend will exceed 80% of monthly limit."
            )
        with ecol3:
            notify_100 = st.checkbox(
                "Notify at 100% (actual)", value=True, key="nq_n100",
                help="Send email to user when actual spend reaches 100% of monthly limit."
            )

        if not selected_domains:
            st.warning("Select at least one domain.")

        if st.button("Create Quota", type="primary", key="btn_create_quota",
                     disabled=(not quota_label.strip() or not selected_domains)):
            qname = _quota_name_from_label(quota_label)
            params = {
                "quota_label":      quota_label.strip(),
                "monthly_limit":    int(monthly_limit),
                "daily_limit":      int(daily_limit_raw) if daily_limit_raw > 0 else None,
                "domains":          selected_domains,
                "block_enforcement": block_enforce,
                "notify_80":        notify_80,
                "notify_100":       notify_100,
                "cohort_role":      cohort_sel if cohort_sel != "All Users" else None,
            }
            with st.spinner(f"Creating quota {qname}…"):
                result = _call_sp(session, "CREATE", qname, params)

            if result.get("ok"):
                tagged = result.get("tagged_users", 0)
                errs   = result.get("errors", [])
                msg    = f"✓ Quota **{qname}** created — monthly limit {monthly_limit} cr/user"
                if cohort_sel != "All Users":
                    msg += f", {tagged} user(s) tagged"
                st.success(msg)
                if errs:
                    st.warning("Some steps had warnings: " + "; ".join(errs[:5]))
                _load_quotas.clear()
                log_activity(session, "CREATE_QUOTA",
                             details={"quota": qname, "monthly_limit": monthly_limit,
                                      "cohort": cohort_sel, "block": block_enforce,
                                      "tagged": tagged})
                st.rerun()
            else:
                st.error(f"✗ {result.get('error', 'Unknown error')}")

    st.divider()

    # ── Enforcement history ───────────────────────────────────────────────────
    if not quotas_df.empty:
        _sec("Enforcement History")
        st.caption("Block and unblock events for a selected quota over a date range.")

        h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
        with h_col1:
            hist_quota = st.selectbox(
                "Select quota", quotas_df["QUOTA_NAME"].tolist(), key="hist_quota"
            )
        with h_col2:
            hist_start = st.date_input("From", value=date.today() - timedelta(days=30),
                                       key="hist_start")
        with h_col3:
            hist_end = st.date_input("To", value=date.today(), key="hist_end")

        if st.button("Load History", key="btn_hist"):
            with st.spinner("Loading enforcement history…"):
                result = _call_sp(session, "GET_ENFORCEMENT_HISTORY", hist_quota, {
                    "start": str(hist_start),
                    "end":   str(hist_end),
                })
            if result.get("ok"):
                history = result.get("history", [])
                if history:
                    st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
                else:
                    st.info("No enforcement events in this date range.")
            else:
                st.error(f"✗ {result.get('error')}")

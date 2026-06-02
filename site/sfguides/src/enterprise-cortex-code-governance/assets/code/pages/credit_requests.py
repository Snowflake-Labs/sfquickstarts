"""
Cortex Code Credit Manager - Credit Requests v3
=================================================
User self-service: request credits OR model access upgrade.
Admin approval queue below.
"""

import json
import streamlit as st
import pandas as pd

from audit import log_activity
from config import (
    KNOWN_MODELS,
    MODEL_CATEGORIES,
    SP_COMPUTE_REBALANCE,
    SP_REBALANCE_CREDITS,
    SP_SET_USER_CREDIT_LIMIT,
    SURFACE_PARAMS,
    SURFACES,
    TABLE_CREDIT_CONFIG,
    TABLE_CREDIT_REQUESTS,
    TABLE_MODEL_ROLE_MAPPING,
    escape_sql_literal,
    fq_table,
    get_app_database,
    get_app_schema,
    get_current_user,
    user_is_admin,
    validate_credit_limit,
)
from intelligence import recommend_rebalance
from utils import (
    call_sp,
    call_bulk_sp,
    get_app_setting,
    get_cohort_config,
    get_credit_configs,
    get_hourly_usage,
    get_pending_requests,
    get_role_members,
    get_session,
    get_user_param,
    get_user_requests,
    get_user_today_usage,
)


def render(session):
    st.header("Credit Requests", help="Users request additional credits or model access upgrades. Admins see a pending approval queue below.")

    _render_user_section(session)

    if user_is_admin(session):
        st.divider()
        _render_admin_section(session)


def _render_user_section(session):
    username = get_current_user(session)
    today_usage = get_user_today_usage(session, username)

    st.subheader("Your Status", help="Your current daily credit limits and how much you've used today on each surface.")
    st.caption(f"Signed in as: **{username}**")

    # Current limits display
    with st.container(border=True):
        cols = st.columns(len(SURFACES))
        for i, surface in enumerate(SURFACES):
            param = SURFACE_PARAMS[surface]
            try:
                val, level = get_user_param(session, username, param)
            except Exception:
                val, level = None, "N/A"
            used = today_usage.get(surface, 0.0)
            limit_str = val if val and val != "-1" else "No limit"
            with cols[i]:
                st.metric(f"{surface}", f"{used:.1f} / {limit_str}",
                          help=f"Source: {level}")
                if val and val != "-1" and float(val) > 0:
                    pct = min(used / float(val) * 100, 100)
                    st.progress(pct / 100)

    st.divider()

    # --- Check request controls before showing form ---
    blocked, block_reason, controls = _check_request_controls(session, username)

    if blocked:
        st.warning(f"⛔ {block_reason}")
        st.caption("Contact your domain lead if you need an exception.")
    else:
        # Show remaining quota
        if controls:
            today_count = controls.get("today_count", 0)
            max_daily = controls.get("max_daily", 2)
            week_used = controls.get("week_used", 0)
            max_weekly = controls.get("max_weekly", 20)
            cooldown_remaining = controls.get("cooldown_remaining", 0)

            col1, col2, col3 = st.columns(3)
            col1.metric("Requests today", f"{today_count}/{max_daily}",
                        help=f"Max {max_daily} requests per day.")
            col2.metric("Extra credits this week", f"{week_used:.0f}/{max_weekly}",
                        help=f"Rolling 7-day extra credit cap: {max_weekly}.")
            if cooldown_remaining > 0:
                col3.metric("Cooldown", f"{cooldown_remaining} min",
                            help="Wait before submitting another request.")
            st.divider()

        # Two request types: Credits or Model Access
        request_type = st.radio(
            "What do you need?",
            ["Additional Credits", "Model Access Upgrade"],
            horizontal=True, key="request_type",
            help="Credits: request more daily credits. Model Access: request access to a higher-tier model."
        )

        if request_type == "Additional Credits":
            _render_credit_request_form(session, username)
        else:
            _render_model_request_form(session, username)

    st.divider()
    st.subheader("My Request History", help="All credit and model access requests you've submitted, with their current status.")
    history = get_user_requests(session, username)
    if not history.empty:
        display_cols = [c for c in ["REQUEST_TIMESTAMP", "SURFACE", "AMOUNT_REQUESTED",
                                    "STATUS", "APPROVED_BY"] if c in history.columns]
        st.dataframe(history[display_cols] if display_cols else history,
                     use_container_width=True, hide_index=True)
    else:
        st.caption("No requests yet.")


def _render_credit_request_form(session, username):
    st.subheader("Request Additional Credits", help="Ask for extra credits for the rest of today. The system automatically finds surplus from teammates in your cohort.")
    with st.form("credit_request_form", clear_on_submit=True):
        surface = st.radio("Surface", SURFACES, horizontal=True, key="req_surface",
                           help="Which surface do you need more credits for?")
        amount = st.number_input("Additional credits needed", min_value=1, max_value=50,
                                 value=5, step=1, key="req_amount",
                                 help="How many extra credits for the rest of today.")
        reason = st.text_area("Reason", max_chars=500, key="req_reason",
                              placeholder="e.g., Working on urgent pipeline fix",
                              help="Helps admins prioritize your request.")
        submitted = st.form_submit_button("Submit Credit Request", type="primary")

    if submitted:
        _process_credit_request(session, username, surface, amount, reason)


def _render_model_request_form(session, username):
    st.subheader("Request Model Access Upgrade", help="Request access to a higher-tier model (e.g. Opus) if your role only has Sonnet access today.")
    st.caption("Request access to a model tier you don't currently have.")

    # Show available models and their tiers
    all_models = list(KNOWN_MODELS.keys())
    tier_info = []
    for m, info in KNOWN_MODELS.items():
        cat = info.get("category", "UNKNOWN")
        desc = info.get("description", "")
        tier_info.append({"Model": m, "Tier": cat, "Description": desc})

    if tier_info:
        st.dataframe(pd.DataFrame(tier_info), use_container_width=True, hide_index=True)

    with st.form("model_request_form", clear_on_submit=True):
        requested_model = st.selectbox("Model requested", all_models, key="req_model",
                                       help="Which model do you need access to?")
        reason = st.text_area("Business justification", max_chars=500, key="model_req_reason",
                              placeholder="e.g., Need Opus for complex architecture review",
                              help="Explain why this model is needed for your work.")
        submitted = st.form_submit_button("Submit Model Access Request", type="primary")

    if submitted and requested_model and reason:
        _process_model_request(session, username, requested_model, reason)


def _process_credit_request(session, username, surface, amount, reason):
    """
    Submit a credit request via SP_CC_COMPUTE_REBALANCE — all data gathering,
    EWMA computation, donor selection, ALTER USER calls, and locking happen
    server-side inside Snowflake. No O(N) Python round-trips, no CLIENT_ABORT.
    """
    cohort_role = _find_user_cohort(session, username)

    if not cohort_role:
        _insert_request(session, username, surface, amount, reason, None, "PENDING")
        st.info("Request submitted. No cohort assigned — awaiting admin approval.")
        return

    # Load settings (fast single-row reads from CC_APP_CONFIG)
    approval_mode     = get_app_setting(session, "APPROVAL_MODE", "ADMIN")
    donor_strategy    = get_app_setting(session, "DONOR_STRATEGY", "WEIGHTED_RANDOM")
    buffer_pct        = int(get_app_setting(session, "REBALANCE_BUFFER_PCT", "20"))
    max_transfer_pct  = int(get_app_setting(session, "REBALANCE_MAX_TRANSFER_PCT", "50"))
    lookback_days     = int(get_app_setting(session, "REBALANCE_LOOKBACK_DAYS", "14"))
    protection_hours  = int(get_app_setting(session, "DONOR_PROTECTION_HOURS", "4"))
    db_schema         = f"{get_app_database(session)}.{get_app_schema(session)}"

    with st.spinner("Analysing cohort surplus — this runs server-side and may take a moment..."):
        ok, raw = call_bulk_sp(
            session,
            SP_COMPUTE_REBALANCE,
            username,          # REQUESTER VARCHAR
            cohort_role,       # COHORT_ROLE VARCHAR
            surface,           # SURFACE VARCHAR
            amount,            # AMOUNT NUMBER
            reason or "",      # REASON VARCHAR
            approval_mode,     # APPROVAL_MODE VARCHAR
            donor_strategy,    # DONOR_STRATEGY VARCHAR
            buffer_pct,        # BUFFER_PCT NUMBER
            max_transfer_pct,  # MAX_TRANSFER_PCT NUMBER
            lookback_days,     # LOOKBACK_DAYS NUMBER
            protection_hours,  # PROTECTION_HOURS NUMBER
            db_schema,         # DB_SCHEMA VARCHAR  e.g. 'CORTEX_CODE_MGMT.APP'
        )

    # Parse SP result
    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        result = {"status": "ERROR", "message": str(raw)}

    status  = result.get("status", "ERROR")
    message = result.get("message", "")

    if status == "APPROVED":
        new_limit = result.get("new_limit", amount)
        donors    = result.get("donors", [])
        # Log to audit (SP already wrote REBALANCE_REDUCE entries per donor)
        log_activity(session, "REBALANCE_INCREASE", target_user=username,
                     details={"surface": surface, "cohort": cohort_role,
                              "donors": [d["user"] for d in donors],
                              "amount": amount, "new_limit": new_limit})
        st.success(f"✓ {message}")

    elif status == "PENDING":
        st.info(message)

    elif status == "LOCKED":
        st.warning(f"⏳ {message}")

    elif status == "ERROR":
        # Graceful fallback: if SP doesn't exist yet (needs Setup → Create Objects),
        # fall back to PENDING with a helpful hint
        if "SP_CC_COMPUTE_REBALANCE" in str(raw) or "does not exist" in str(raw).lower():
            _insert_request(session, username, surface, amount, reason, cohort_role, "PENDING")
            st.info("Request submitted for admin review.")
            st.caption("Tip: Run Setup → Create Missing Objects to enable auto-rebalancing.")
        else:
            st.error(f"✗ Rebalancing error: {message}")
    else:
        st.warning(f"Unexpected status '{status}'. Request may not have been saved.")


def _process_model_request(session, username, model, reason):
    """Insert a model access request into the requests table."""
    tbl = fq_table(session, TABLE_CREDIT_REQUESTS)
    safe_req = escape_sql_literal(username)
    safe_reason = escape_sql_literal(reason)
    safe_model = escape_sql_literal(model)
    try:
        session.sql(f"""
            INSERT INTO {tbl}
                (REQUEST_TIMESTAMP, REQUESTER, SURFACE, AMOUNT_REQUESTED, REASON, STATUS)
            SELECT CURRENT_TIMESTAMP(), '{safe_req}', 'MODEL:{safe_model}', 0, '{safe_reason}', 'PENDING'
        """).collect()
        log_activity(session, "MODEL_ACCESS_REQUEST", target_user=username,
                     details={"model": model, "reason": reason})
        st.success(f"✓ Model access request for **{model}** submitted.")
    except Exception as e:
        st.error(f"✗ Failed to submit: {e}")


def _find_user_cohort(session, username):
    configs = get_credit_configs(session)
    if configs.empty:
        return None
    configs.columns = [c.upper() for c in configs.columns]
    if "CONFIG_TYPE" not in configs.columns:
        return None
    cohorts = configs[configs["CONFIG_TYPE"] == "COHORT"]
    for _, row in cohorts.iterrows():
        role = row.get("ROLE_NAME") if hasattr(row, 'get') else row["ROLE_NAME"] if "ROLE_NAME" in row.index else None
        if role:
            members = get_role_members(session, role)
            if username in members:
                return role
    return None


def _insert_request(session, requester, surface, amount, reason, cohort_role, status,
                    amount_approved=None, approved_by=None, donor_user=None):
    tbl = fq_table(session, TABLE_CREDIT_REQUESTS)
    safe_req = escape_sql_literal(requester)
    safe_reason = escape_sql_literal(reason or "")
    safe_cohort = f"'{escape_sql_literal(cohort_role)}'" if cohort_role else "NULL"
    safe_donor = f"'{escape_sql_literal(donor_user)}'" if donor_user else "NULL"
    safe_approved_by = f"'{escape_sql_literal(approved_by)}'" if approved_by else "NULL"
    amt_approved_sql = str(amount_approved) if amount_approved is not None else "NULL"
    approved_at_sql = "CURRENT_TIMESTAMP()" if approved_by else "NULL"

    try:
        session.sql(f"""
            INSERT INTO {tbl}
                (REQUEST_TIMESTAMP, REQUESTER, COHORT_ROLE, SURFACE, AMOUNT_REQUESTED,
                 AMOUNT_APPROVED, REASON, DONOR_USER, STATUS, APPROVED_BY, APPROVED_AT)
            SELECT CURRENT_TIMESTAMP(), '{safe_req}', {safe_cohort}, '{escape_sql_literal(surface)}',
                 {amount}, {amt_approved_sql}, '{safe_reason}', {safe_donor},
                 '{escape_sql_literal(status)}', {safe_approved_by}, {approved_at_sql}
        """).collect()
    except Exception as e:
        st.error(f"✗ Failed to save request: {e}")


def _render_admin_section(session):
    st.subheader("Pending Approval Queue", help="Credit and model access requests waiting for admin action. Approve to apply the change immediately, Reject to deny.")

    pending = get_pending_requests(session)
    if pending.empty:
        st.caption("No pending requests.")
        return

    pending.columns = [c.upper() for c in pending.columns]

    for idx, row in pending.iterrows():
        req_id = row.get("REQUEST_ID", idx) if hasattr(row, 'get') else row["REQUEST_ID"] if "REQUEST_ID" in row.index else idx
        requester = row.get("REQUESTER", "?") if hasattr(row, 'get') else row["REQUESTER"] if "REQUESTER" in row.index else "?"
        surface = row.get("SURFACE", "?") if hasattr(row, 'get') else row["SURFACE"] if "SURFACE" in row.index else "?"
        amount = row.get("AMOUNT_REQUESTED", 0) if hasattr(row, 'get') else row["AMOUNT_REQUESTED"] if "AMOUNT_REQUESTED" in row.index else 0
        reason = row.get("REASON", "") if hasattr(row, 'get') else row["REASON"] if "REASON" in row.index else ""

        is_model_request = str(surface).startswith("MODEL:")

        with st.container(border=True):
            if is_model_request:
                model_name = str(surface).replace("MODEL:", "")
                st.markdown(f"**{requester}** requests access to model **{model_name}**")
            else:
                st.markdown(f"**{requester}** requests **+{amount} {surface}** credits")
            if reason:
                st.caption(f"Reason: {reason}")

            col_a, col_r = st.columns(2)
            with col_a:
                if st.button("Approve", key=f"approve_{req_id}", type="primary",
                             help="Approves and applies the change."):
                    if is_model_request:
                        _approve_model_request(session, req_id, requester, surface)
                    else:
                        _approve_credit_request(session, row)
                    st.rerun()
            with col_r:
                if st.button("Reject", key=f"reject_{req_id}",
                             help="Denies the request."):
                    _reject_request(session, req_id)
                    st.rerun()


def _approve_credit_request(session, row):
    req_id = row["REQUEST_ID"]
    requester = row["REQUESTER"]
    surface = row["SURFACE"]
    amount = float(row["AMOUNT_REQUESTED"])
    admin = get_current_user(session)

    try:
        val, _ = get_user_param(session, requester, SURFACE_PARAMS[surface])
    except Exception:
        val = None
    current = float(val) if val and val != "-1" else 0
    new_limit = current + amount
    call_sp(session, SP_SET_USER_CREDIT_LIMIT, requester, surface, str(int(new_limit)))

    tbl = fq_table(session, TABLE_CREDIT_REQUESTS)
    safe_admin = escape_sql_literal(admin)
    try:
        session.sql(f"""
            UPDATE {tbl} SET STATUS = 'APPROVED', APPROVED_BY = '{safe_admin}',
                APPROVED_AT = CURRENT_TIMESTAMP(), AMOUNT_APPROVED = {amount}
            WHERE REQUEST_ID = {int(req_id)}
        """).collect()
    except Exception:
        pass

    log_activity(session, "APPROVE_REQUEST", target_user=requester,
                 details={"request_id": int(req_id), "surface": surface, "amount": amount},
                 old_value=str(current), new_value=str(new_limit))
    st.success(f"✓ Approved +{amount} for {requester}")


def _approve_model_request(session, req_id, requester, surface):
    """Approve a model access request."""
    admin = get_current_user(session)
    model_name = str(surface).replace("MODEL:", "")

    tbl = fq_table(session, TABLE_CREDIT_REQUESTS)
    safe_admin = escape_sql_literal(admin)
    try:
        session.sql(f"""
            UPDATE {tbl} SET STATUS = 'APPROVED', APPROVED_BY = '{safe_admin}',
                APPROVED_AT = CURRENT_TIMESTAMP()
            WHERE REQUEST_ID = {int(req_id)}
        """).collect()
    except Exception:
        pass

    log_activity(session, "APPROVE_MODEL_REQUEST", target_user=requester,
                 details={"model": model_name, "approved_by": admin})
    st.success(f"✓ Approved model access to {model_name} for {requester}")


def _reject_request(session, req_id):
    tbl = fq_table(session, TABLE_CREDIT_REQUESTS)
    admin = get_current_user(session)
    safe_admin = escape_sql_literal(admin)
    try:
        session.sql(f"""
            UPDATE {tbl} SET STATUS = 'REJECTED', APPROVED_BY = '{safe_admin}',
                APPROVED_AT = CURRENT_TIMESTAMP()
            WHERE REQUEST_ID = {int(req_id)}
        """).collect()
    except Exception:
        pass
    log_activity(session, "REJECT_REQUEST", details={"request_id": int(req_id)})


def _check_request_controls(session, username):
    """
    Check if user is allowed to submit a request.
    Returns: (blocked: bool, reason: str, controls: dict)
    """
    from config import fq_table, escape_sql_literal, TABLE_CREDIT_REQUESTS
    from utils import get_app_setting
    from datetime import datetime, timedelta

    try:
        max_daily = int(get_app_setting(session, "MAX_REQUESTS_PER_USER_PER_DAY", "2"))
        cooldown_mins = int(get_app_setting(session, "REQUEST_COOLDOWN_MINUTES", "60"))
        max_weekly = int(get_app_setting(session, "MAX_EXTRA_CREDITS_PER_WEEK", "20"))

        tbl = fq_table(session, TABLE_CREDIT_REQUESTS)
        safe_user = escape_sql_literal(username)

        # Today's request count
        df_today = session.sql(f"""
            SELECT COUNT(*) AS CNT,
                   MAX(REQUEST_TIMESTAMP) AS LAST_REQUEST,
                   COALESCE(SUM(AMOUNT_REQUESTED), 0) AS TODAY_CREDITS
            FROM {tbl}
            WHERE REQUESTER = '{safe_user}'
              AND DATE(REQUEST_TIMESTAMP) = CURRENT_DATE()
              AND SURFACE NOT LIKE 'MODEL:%'
        """).to_pandas()

        df_today.columns = [c.strip('"').upper() for c in df_today.columns]
        today_count = int(df_today["CNT"].iloc[0]) if not df_today.empty else 0
        last_request = df_today["LAST_REQUEST"].iloc[0] if not df_today.empty else None

        # Weekly extra credits requested
        df_week = session.sql(f"""
            SELECT COALESCE(SUM(AMOUNT_REQUESTED), 0) AS WEEK_CREDITS
            FROM {tbl}
            WHERE REQUESTER = '{safe_user}'
              AND REQUEST_TIMESTAMP >= DATEADD('day', -7, CURRENT_TIMESTAMP())
              AND STATUS IN ('APPROVED', 'PENDING')
              AND SURFACE NOT LIKE 'MODEL:%'
        """).to_pandas()
        df_week.columns = [c.strip('"').upper() for c in df_week.columns]
        week_used = float(df_week["WEEK_CREDITS"].iloc[0]) if not df_week.empty else 0.0

        # Cooldown check
        cooldown_remaining = 0
        if last_request is not None and str(last_request) not in ("None", "NaT", ""):
            try:
                last_dt = pd.to_datetime(last_request)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.tz_localize("UTC")
                now_utc = pd.Timestamp.now(tz="UTC")
                elapsed_mins = (now_utc - last_dt).total_seconds() / 60
                cooldown_remaining = max(0, int(cooldown_mins - elapsed_mins))
            except Exception:
                cooldown_remaining = 0

        controls = {
            "today_count": today_count,
            "max_daily": max_daily,
            "week_used": week_used,
            "max_weekly": max_weekly,
            "cooldown_remaining": cooldown_remaining,
        }

        # Check blocks
        if today_count >= max_daily:
            return True, f"You've already made {today_count} requests today (daily limit: {max_daily}). Resets at midnight UTC.", controls
        if cooldown_remaining > 0:
            return True, f"Please wait {cooldown_remaining} more minutes before your next request (cooldown: {cooldown_mins} min).", controls
        if week_used >= max_weekly:
            return True, f"You've requested {week_used:.0f} extra credits this week (weekly cap: {max_weekly}). Cap resets on a rolling 7-day basis.", controls

        return False, "", controls

    except Exception:
        # If controls check fails, allow the request
        return False, "", {}


def _get_recent_donors(session, cohort_role: str, protection_hours: int) -> list:
    """Get users who recently donated credits (used by ROUND_ROBIN strategy)."""
    if protection_hours <= 0:
        return []
    try:
        from config import TABLE_AUDIT_LOG, fq_table, escape_sql_literal
        tbl = fq_table(session, TABLE_AUDIT_LOG)
        safe_cohort = escape_sql_literal(cohort_role)
        df = session.sql(f"""
            SELECT DISTINCT TARGET_USER
            FROM {tbl}
            WHERE ACTION_TYPE = 'REBALANCE_REDUCE'
              AND TIMESTAMP >= DATEADD('hour', -{int(protection_hours)}, CURRENT_TIMESTAMP())
              AND TARGET_USER IS NOT NULL
        """).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            return df["TARGET_USER"].tolist()
    except Exception:
        pass
    return []

"""
Cortex Code Credit Manager - Settings (Admin) v3
=================================================
Elaborate admin configuration with clear explanations.
"""

import streamlit as st

from audit import log_activity
from config import get_current_user
from utils import get_app_setting, get_session, set_app_setting


def render(session):
    st.header("Settings", help="Configure how the Credit Manager behaves: approval mode, rebalance parameters, rate limits, and domain lead assignments.")
    st.caption("Configure how the Credit Manager behaves. Changes take effect immediately.")
    actor = get_current_user(session)

    # --- Donor Selection Strategy ---
    with st.container(border=True):
        st.subheader("Donor Selection Strategy", help="Controls which cohort members donate surplus credits when a rebalance request is fulfilled.")
        st.markdown("""
        When credits are redistributed within a cohort, this controls **which users donate first**.
        """)

        strategy_options = {
            "WEIGHTED_RANDOM": "Weighted Random — donors chosen by probability proportional to surplus. Distributes load fairly over time. **Recommended.**",
            "HIGHEST_SURPLUS": "Highest Surplus First — always take from whoever has the most available. Safest, but same users always donate.",
            "MINIMUM_DONORS": "Minimum Donors — use fewest donors possible to fulfill request. Protects most of the cohort from being affected.",
            "ROUND_ROBIN": "Round Robin — prioritize donors who haven't donated recently. Most equitable rotation.",
        }

        current_strategy = get_app_setting(session, "DONOR_STRATEGY", "WEIGHTED_RANDOM")
        strategy = st.selectbox(
            "Donor selection strategy", list(strategy_options.keys()),
            index=list(strategy_options.keys()).index(current_strategy) if current_strategy in strategy_options else 0,
            format_func=lambda x: x.replace("_", " ").title(),
            key="setting_strategy",
            help="Controls which cohort members donate credits when a rebalancing request is fulfilled."
        )
        st.caption(strategy_options.get(strategy, ""))

        current_protection = get_app_setting(session, "DONOR_PROTECTION_HOURS", "4")
        protection_hours = st.number_input(
            "Donor protection window (hours)", min_value=0, max_value=24, value=int(current_protection),
            key="setting_protection", step=1,
            help="Skip users who donated within this many hours (used by Round Robin strategy). "
                 "Set 0 to disable protection."
        )

    # --- Request Controls ---
    with st.container(border=True):
        st.subheader("Credit Request Controls", help="Rate-limiting rules that prevent users from gaming the system by submitting requests repeatedly.")
        st.markdown("""
        Prevent users from gaming the system by requesting credits repeatedly.
        These limits apply per user, per day (UTC).
        """)

        col1, col2, col3 = st.columns(3)
        with col1:
            current_max_req = get_app_setting(session, "MAX_REQUESTS_PER_USER_PER_DAY", "2")
            max_daily_req = st.number_input(
                "Max requests per day", min_value=1, max_value=10, value=int(current_max_req),
                key="setting_max_req", step=1,
                help="A user can only submit this many credit requests per UTC day. After this, the form is blocked until midnight."
            )
        with col2:
            current_cooldown = get_app_setting(session, "REQUEST_COOLDOWN_MINUTES", "60")
            cooldown_mins = st.number_input(
                "Cooldown (minutes)", min_value=0, max_value=480, value=int(current_cooldown),
                key="setting_cooldown", step=15,
                help="After an approved or pending request, the user must wait this many minutes before submitting another. Set 0 to disable."
            )
        with col3:
            current_weekly = get_app_setting(session, "MAX_EXTRA_CREDITS_PER_WEEK", "20")
            max_weekly = st.number_input(
                "Max extra credits/week", min_value=5, max_value=200, value=int(current_weekly),
                key="setting_weekly", step=5,
                help="Rolling 7-day cap on total extra credits a user can request. Prevents users from consistently bypassing their daily limit."
            )

    # --- Approval Mode ---
    with st.container(border=True):
        st.subheader("Credit Request Approval Mode", help="AUTO: rebalance happens instantly when surplus exists. ADMIN: every request is queued for manual review.")
        st.markdown("""
        When a user requests additional credits, the system can either:
        - **AUTO**: Immediately analyze cohort usage patterns, identify a donor with surplus credits,
          and transfer credits automatically. The donor's limit decreases, the requester's increases.
          No human approval needed.
        - **ADMIN**: Queue the request for manual review. An admin sees the system's recommendation
          but decides whether to approve, modify, or reject.
        """)
        current_mode = get_app_setting(session, "APPROVAL_MODE", "ADMIN")
        mode = st.radio(
            "Approval mode",
            ["AUTO", "ADMIN"],
            index=0 if current_mode == "AUTO" else 1,
            horizontal=True,
            key="setting_mode",
            help="AUTO = instant rebalancing within cohort. ADMIN = requests queued for manual review."
        )

    # --- Rebalance Safety ---
    with st.container(border=True):
        st.subheader("Rebalance Safety Parameters", help="How aggressively the EWMA prediction engine can redistribute credits. Higher buffer = more conservative.")
        st.markdown("""
        These control how aggressively the intelligence engine can redistribute credits.
        The system uses EWMA (Exponentially Weighted Moving Average) on hourly usage data
        to predict each user's remaining consumption for the day.
        """)

        col1, col2, col3 = st.columns(3)

        with col1:
            current_buffer = get_app_setting(session, "REBALANCE_BUFFER_PCT", "20")
            buffer_pct = st.number_input(
                "Donor buffer %", min_value=0, max_value=50, value=int(current_buffer),
                key="setting_buffer",
                help="After predicting a donor's remaining usage, add this % as safety margin. "
                     "E.g., 20% means if the system predicts a donor will use 5 more credits, "
                     "it keeps 6 credits reserved (5 + 20% buffer) and only transfers the rest."
            )

        with col2:
            current_max = get_app_setting(session, "REBALANCE_MAX_TRANSFER_PCT", "50")
            max_transfer = st.number_input(
                "Max transfer cap %", min_value=10, max_value=100, value=int(current_max),
                key="setting_max_transfer",
                help="Maximum % of a donor's original daily limit that can be transferred away. "
                     "E.g., 50% means a user with a 20-credit limit can never have more than "
                     "10 credits taken, even if they're predicted to use 0."
            )

        with col3:
            current_lookback = get_app_setting(session, "REBALANCE_LOOKBACK_DAYS", "14")
            lookback = st.number_input(
                "Trend lookback days", min_value=7, max_value=90, value=int(current_lookback),
                key="setting_lookback",
                help="How many days of hourly data the prediction engine uses. "
                     "Longer = smoother predictions (less reactive to spikes). "
                     "Shorter = more reactive to recent behavior changes."
            )

    # --- Daily Reset ---
    with st.container(border=True):
        st.subheader("Daily Limit Reset", help="When enabled, a task runs at midnight UTC and restores all rebalanced limits back to cohort defaults.")
        st.markdown("""
        When enabled, a scheduled task runs at **midnight UTC** and restores all user limits
        to their cohort defaults. This undoes any rebalancing that happened during the day.
        User-level overrides (set explicitly by an admin) are **not** affected by the reset.
        """)
        current_reset = get_app_setting(session, "DAILY_RESET_ENABLED", "TRUE")
        reset_enabled = st.checkbox(
            "Enable nightly reset to cohort defaults",
            value=current_reset == "TRUE",
            key="setting_reset",
            help="Disable this only if you want rebalanced limits to persist across days. "
                 "Not recommended for most deployments."
        )

    # --- Temporary Credits ---
    with st.container(border=True):
        st.subheader("Temporary Credit Behavior", help="Temporary overrides auto-revert at midnight UTC on their expiry date via the daily reset task.")
        st.markdown("""
        When temporary credits are assigned (with an end date), the system checks during
        the daily reset task whether any temporary assignments have expired. Expired assignments
        revert the user's limit to their previous value automatically.
        
        **How it works:**
        1. Admin sets a temporary override with an end date
        2. The override is stored with `IS_TEMPORARY = TRUE` and `EXPIRES_AT` timestamp
        3. The daily reset task checks for expired temporaries and reverts them
        4. An audit log entry is created for both the assignment and the revert
        """)
        st.info("Temporary credit assignments are configured in the Credit Configuration page.")

    # --- Example Scenario ---
    with st.expander("Example: How Rebalancing Works", expanded=False):
        st.markdown("""
**Scenario:** Team "Data Engineering" — 100 users, each with 10 credits/day (CLI).

At **11 AM**, 10 users hit their limit and request 5 more credits each.

**Step 1: Identify Donors**

The system looks at the other 90 users in the cohort:

| User | Limit | Used (by 11AM) | Predicted Rest-of-Day | Buffer (20%) | Safe Surplus | Transferable (max 50%) |
|------|-------|----------------|----------------------|--------------|--------------|----------------------|
| User_42 | 10 | 1 | 2 | 2.0 | **5.0** | 5.0 |
| User_67 | 10 | 2 | 3 | 2.0 | **3.0** | 3.0 |
| User_88 | 10 | 0 | 4 | 2.0 | **4.0** | 4.0 |
| User_15 | 10 | 5 | 4 | 2.0 | **-1.0** | 0 (skip) |

Formula: `surplus = limit - used - predicted - (limit × buffer%)`

**Step 2: Rank & Assign**

Donors ranked by surplus (highest first): User_42 (5.0) → User_88 (4.0) → User_67 (3.0)

For requester needing 5 credits:
- Take 5 from User_42 → User_42's new limit: 5
- Requester's new limit: 15
- Done.

**Step 3: Predict "rest of day" — how?**

Uses EWMA on 14 days of hourly data:
```
For each hour remaining (12, 13, 14, ... 23):
    avg_usage_at_that_hour = mean of last 14 days at that hour
    same_weekday_avg = mean of same day-of-week at that hour
    prediction = (0.4 × avg) + (0.6 × same_weekday_avg)
```
Monday patterns differ from Friday. The system knows this.

**Step 4: Safety Checks**
- ✅ Buffer: 20% of donor's limit always reserved (configurable above)
- ✅ Cap: Never take more than 50% of donor's original limit
- ✅ Reset: At midnight UTC, all limits restore to 10 (cohort default)
- ✅ Override protection: Users with admin-set overrides are never donors

**What if not enough surplus?**
Request queues for admin approval with message: "Only 12 credits available across cohort (50 requested)."
        """)

    # --- Domain Leads ---
    with st.container(border=True):
        st.subheader("Domain / Cohort Leads", help="Assign a lead user per cohort who can approve credit requests for their team without involving a platform admin.")
        st.markdown("""
        Assign a **domain lead** to each cohort. Domain leads can:
        - Approve/reject credit requests for their cohort members
        - Set credit limits within their cohort
        - Approve model access upgrades for their team

        This enables **delegated administration** — platform admins don't need to approve every request.
        Each domain (Supply Chain, Trading, Customer, etc.) manages their own budget autonomously.
        """)

        # Show current leads
        try:
            leads_df = session.sql(f"""
                SELECT COHORT_ROLE, LEAD_USER, CAN_APPROVE_CREDITS, CAN_APPROVE_MODELS, CAN_SET_LIMITS
                FROM {_get_leads_table(session)}
                ORDER BY COHORT_ROLE
            """).to_pandas()
            if not leads_df.empty:
                leads_df.columns = [c.strip('"').upper() for c in leads_df.columns]
                st.dataframe(leads_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No domain leads configured yet.")
        except Exception:
            st.caption("Cohort leads table not available.")

        # Add lead form
        col1, col2 = st.columns(2)
        with col1:
            from utils import list_roles
            roles = list_roles(session)
            lead_cohort = st.selectbox("Cohort", roles, key="lead_cohort",
                                       help="Which cohort this lead manages.")
        with col2:
            lead_user = st.text_input("Lead Username", key="lead_user",
                                      help="Snowflake username of the domain lead.")

        if lead_cohort and lead_user:
            if st.button("Assign Domain Lead", type="primary", key="btn_assign_lead",
                         help="Gives this user approval authority for their cohort."):
                _assign_lead(session, lead_cohort, lead_user, actor)

    # --- Save ---
    st.divider()
    if st.button(
        "Save Settings", type="primary", key="btn_save_settings",
        help="Writes all settings to CC_APP_CONFIG table. Takes effect on next page load."
    ):
        settings = {
            "APPROVAL_MODE": mode,
            "REBALANCE_BUFFER_PCT": str(buffer_pct),
            "REBALANCE_MAX_TRANSFER_PCT": str(max_transfer),
            "REBALANCE_LOOKBACK_DAYS": str(lookback),
            "DAILY_RESET_ENABLED": "TRUE" if reset_enabled else "FALSE",
            "MAX_REQUESTS_PER_USER_PER_DAY": str(max_daily_req),
            "REQUEST_COOLDOWN_MINUTES": str(cooldown_mins),
            "MAX_EXTRA_CREDITS_PER_WEEK": str(max_weekly),
            "DONOR_STRATEGY": strategy,
            "DONOR_PROTECTION_HOURS": str(protection_hours),
        }
        all_ok = True
        for key, val in settings.items():
            if not set_app_setting(session, key, val, actor):
                all_ok = False
                st.error(f"✗ Failed to save {key}")
        if all_ok:
            log_activity(session, "UPDATE_SETTINGS", details=settings)
            st.success("✓ All settings saved")


def _get_leads_table(session):
    from config import fq_table
    return fq_table(session, "CC_COHORT_LEADS")


def _assign_lead(session, cohort_role, lead_user, actor):
    from config import escape_sql_literal, fq_table
    tbl = _get_leads_table(session)
    safe_cohort = escape_sql_literal(cohort_role)
    safe_user = escape_sql_literal(lead_user)
    safe_actor = escape_sql_literal(actor)
    try:
        session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT '{safe_cohort}' AS C, '{safe_user}' AS U) s
                ON t.COHORT_ROLE = s.C AND t.LEAD_USER = s.U
            WHEN NOT MATCHED THEN INSERT
                (COHORT_ROLE, LEAD_USER, CAN_APPROVE_CREDITS, CAN_APPROVE_MODELS, CAN_SET_LIMITS, ASSIGNED_BY)
            VALUES ('{safe_cohort}', '{safe_user}', TRUE, TRUE, TRUE, '{safe_actor}')
        """).collect()
        log_activity(session, "ASSIGN_DOMAIN_LEAD", target_user=lead_user,
                     target_role=cohort_role, details={"assigned_by": actor})
        st.success(f"✓ {lead_user} assigned as lead for {cohort_role}")
    except Exception as e:
        st.error(f"✗ Failed: {e}")

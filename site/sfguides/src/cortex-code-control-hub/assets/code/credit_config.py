"""
Cortex Code Credit Manager - Credit Configuration (Admin) v3
==============================================================
Account defaults, cohort (by Role OR Tag), user overrides.
Supports temporary assignments with end date + auto-revert.
"""

import re
import json
from datetime import date, timedelta

import streamlit as st
import pandas as pd

from audit import log_activity
from config import (
    SP_SET_ACCOUNT_CREDIT_LIMIT,
    SP_SET_USER_CREDIT_LIMIT,
    SP_UNSET_USER_CREDIT_LIMIT,
    SP_BULK_SET_COHORT_LIMITS,
    SURFACE_PARAMS,
    SURFACES,
    TABLE_CREDIT_CONFIG,
    escape_sql_literal,
    fq_table,
    get_current_user,
    sanitize_identifier,
    validate_credit_limit,
)
from utils import (
    call_sp,
    call_bulk_sp,
    get_account_param,
    get_cohort_config,
    get_credit_configs,
    get_role_members,
    get_session,
    get_user_param,
    list_roles,
    list_users,
)


def _filter_human_users(users_df: pd.DataFrame) -> list:
    if users_df.empty:
        return []
    names = users_df["NAME"].tolist()
    uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-")
    svc_pattern = re.compile(r"^(SVC_|MANAGED_|SYSTEM\$|APP_)")
    return [n for n in names if n and not uuid_pattern.match(str(n)) and not svc_pattern.match(str(n))]


def render(session):
    st.header("Credit Configuration", help="Set daily credit limits at three levels: Account (default for everyone), Cohort (by role or tag), or User (individual override).")
    st.caption("Set daily credit limits. Hierarchy: Account → Cohort → User override (highest precedence).")

    tab_acct, tab_cohort, tab_user = st.tabs([
        "⚙️ Account Defaults", "👥 Cohort (Role or Tag)", "👤 User Override"
    ])

    with tab_acct:
        _render_account(session)
    with tab_cohort:
        _render_cohort(session)
    with tab_user:
        _render_user_override(session)


def _render_account(session):
    st.subheader("Account-Level Defaults", help="Baseline daily limit applied to all users who don't have a cohort or user-level override.")
    st.caption("Baseline limit for all users. Overridden by cohort or user-level settings.")

    with st.container(border=True):
        cols = st.columns(len(SURFACES))
        for i, surface in enumerate(SURFACES):
            param = SURFACE_PARAMS[surface]
            current = get_account_param(session, param)
            display = current if current and current != "-1" else "Unlimited"
            with cols[i]:
                st.metric(f"{surface}", display, help=f"Current account-level {surface} limit.")

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        cli_limit = st.number_input("CLI Daily Limit", min_value=-1, value=20, step=1,
                                    key="acct_cli", help="Set -1 for unlimited, 0 to block.")
    with col2:
        ss_limit = st.number_input("Snowsight Daily Limit", min_value=-1, value=20, step=1,
                                   key="acct_ss", help="Set -1 for unlimited, 0 to block.")
    with col3:
        dt_limit = st.number_input("Desktop Daily Limit", min_value=-1, value=20, step=1,
                                   key="acct_dt", help="Set -1 for unlimited, 0 to block.")

    if st.button("Apply Account Defaults", type="primary", key="btn_acct_defaults",
                 help="ALTER ACCOUNT SET for CLI, Snowsight, and Desktop parameters."):
        actor = get_current_user(session)
        for surface, val in [("CLI", cli_limit), ("SNOWSIGHT", ss_limit), ("DESKTOP", dt_limit)]:
            validated = int(validate_credit_limit(val))
            ok, msg = call_sp(session, SP_SET_ACCOUNT_CREDIT_LIMIT, surface, str(validated))
            if ok:
                log_activity(session, "SET_ACCOUNT_LIMIT", details={"surface": surface},
                             new_value=str(validated))
                st.success(f"✓ {surface} → {validated}")
            else:
                st.error(f"✗ {surface}: {msg}")


def _render_cohort(session):
    st.subheader("Cohort Configuration", help="Apply a daily limit to a group of users identified by a Snowflake role or user tag.")
    st.caption("Apply limits to a group of users. Select by **Role** or by **User Tag**.")

    # Cohort source selection
    cohort_source = st.radio(
        "Identify cohort by", ["Role", "User Tag"], horizontal=True,
        key="cohort_source",
        help="Role: all users granted a specific role. Tag: all users with a specific tag value."
    )

    members = []
    cohort_identifier = None

    if cohort_source == "Role":
        roles = list_roles(session)
        if not roles:
            st.warning("No roles accessible.")
            return
        chosen_role = st.selectbox("Select Role", roles, key="cohort_role",
                                   help="All members of this role get the configured limit.")
        if chosen_role:
            cohort_identifier = chosen_role
            # Try resolved members first (includes inherited hierarchy); fall back to direct grants
            try:
                resolved_rows = session.sql(f"""
                    SELECT USER_NAME FROM {fq_table('CC_USER_COHORT_RESOLVED')}
                    WHERE UPPER(COHORT_ROLE) = UPPER('{chosen_role.replace("'","''")}')
                """).collect()
                if resolved_rows:
                    members = [str(r[0]) for r in resolved_rows]
                    st.info(f"**{len(members)}** members in `{chosen_role}` (including inherited roles)")
                else:
                    members = get_role_members(session, chosen_role)
                    if members:
                        st.info(f"**{len(members)}** direct members in `{chosen_role}`")
                    else:
                        st.info(f"**0** members found. Click Apply — the SP will resolve members including inherited roles.")
            except Exception:
                members = get_role_members(session, chosen_role)
                st.info(f"**{len(members)}** members in `{chosen_role}`")
    else:
        # Tag-based cohort
        tag_name = st.text_input("Tag Name", value="DEPARTMENT", key="cohort_tag_name",
                                 help="The Snowflake object tag name (e.g., DEPARTMENT, TEAM, COST_CENTER).")
        tag_value = st.text_input("Tag Value", placeholder="e.g., Engineering", key="cohort_tag_value",
                                  help="Users with this tag value will be in the cohort.")
        if tag_name and tag_value:
            cohort_identifier = f"TAG:{tag_name}={tag_value}"
            members = _get_users_by_tag(session, tag_name, tag_value)
            st.info(f"**{len(members)}** users with tag `{tag_name}` = `{tag_value}`")

    if not cohort_identifier:
        return

    st.divider()

    # Limit configuration
    col1, col2, col3 = st.columns(3)
    with col1:
        cli_limit = st.number_input("CLI Daily Limit", min_value=0, value=10, step=1,
                                    key="cohort_cli", help="Per-user daily CLI credit budget.")
    with col2:
        ss_limit = st.number_input("Snowsight Daily Limit", min_value=0, value=10, step=1,
                                   key="cohort_ss", help="Per-user daily Snowsight credit budget.")
    with col3:
        dt_limit = st.number_input("Desktop Daily Limit", min_value=0, value=10, step=1,
                                   key="cohort_dt", help="Per-user daily Desktop (VS Code/Cursor) credit budget.")

    # Temporary vs Permanent
    st.divider()
    duration_type = st.radio("Duration", ["Permanent", "Temporary"], horizontal=True,
                            key="cohort_duration",
                            help="Permanent: stays until manually changed. Temporary: auto-reverts after end date.")
    expires_at = None
    if duration_type == "Temporary":
        expires_at = st.date_input("Expires on", value=date.today() + timedelta(days=7),
                                   min_value=date.today() + timedelta(days=1),
                                   key="cohort_expires",
                                   help="Limit reverts to previous value after this date (midnight UTC).")

    # Apply button
    if members:
        if st.button(f"Apply to Cohort ({len(members)} members)", type="primary", key="btn_cohort_apply",
                     help=f"Sets limits on {len(members)} users. {'Reverts on ' + str(expires_at) if expires_at else 'Permanent.'}"):
            _apply_cohort(session, cohort_identifier, members, cli_limit, ss_limit, dt_limit,
                         is_temporary=(duration_type == "Temporary"), expires_at=expires_at)
    else:
        if st.button("Apply to Cohort", type="primary", key="btn_cohort_apply",
                     help="Saves config and triggers SP to resolve members via full role hierarchy."):
            _apply_cohort(session, cohort_identifier, members, cli_limit, ss_limit, dt_limit,
                         is_temporary=(duration_type == "Temporary"), expires_at=expires_at)


def _render_user_override(session):
    st.subheader("User Override", help="Set or remove an individual daily limit that takes precedence over cohort and account defaults.")
    st.caption("Override cohort defaults for a specific user.")

    all_users = list_users(session)
    if all_users.empty:
        st.warning("Could not load user list.")
        return

    human_users = _filter_human_users(all_users)
    if not human_users:
        st.warning("No human users found.")
        return

    chosen_user = st.selectbox("Select User", human_users, key="override_user",
                               help="Search by typing. System accounts filtered out.")
    if not chosen_user:
        return

    # Current values
    with st.container(border=True):
        cols = st.columns(len(SURFACES))
        for i, surface in enumerate(SURFACES):
            param = SURFACE_PARAMS[surface]
            try:
                val, level = get_user_param(session, chosen_user, param)
                display = val if val and val != "-1" else "No override"
            except Exception:
                display, level = "Error", "N/A"
            with cols[i]:
                st.metric(f"{surface}", display, help=f"Source: {level}")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        cli_val = st.number_input("CLI Override", min_value=-1, value=10, step=1,
                                  key="override_cli", help="Set -1 for unlimited.")
    with col2:
        ss_val = st.number_input("Snowsight Override", min_value=-1, value=10, step=1,
                                 key="override_ss", help="Set -1 for unlimited.")
    with col3:
        dt_val = st.number_input("Desktop Override", min_value=-1, value=10, step=1,
                                 key="override_dt", help="Set -1 for unlimited.")

    # Temporary vs Permanent
    duration_type = st.radio("Duration", ["Permanent", "Temporary"], horizontal=True,
                            key="user_duration",
                            help="Temporary overrides auto-revert after the specified date.")
    expires_at = None
    if duration_type == "Temporary":
        expires_at = st.date_input("Expires on", value=date.today() + timedelta(days=7),
                                   min_value=date.today() + timedelta(days=1),
                                   key="user_expires",
                                   help="Override reverts after this date.")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Apply Override", type="primary", key="btn_override_apply",
                     help="ALTER USER SET for this user."):
            all_ok = True
            for surface, val in [("CLI", cli_val), ("SNOWSIGHT", ss_val), ("DESKTOP", dt_val)]:
                validated = int(validate_credit_limit(val))
                ok, msg = call_sp(session, SP_SET_USER_CREDIT_LIMIT, chosen_user, surface, str(validated))
                if ok:
                    log_activity(session, "SET_USER_OVERRIDE", target_user=chosen_user,
                                 details={"surface": surface, "temporary": duration_type == "Temporary",
                                          "expires_at": str(expires_at) if expires_at else None},
                                 new_value=str(validated))
                    st.success(f"✓ {surface} → {validated}")
                else:
                    all_ok = False
                    st.error(f"✗ {surface}: {msg}")

            if all_ok:
                _save_user_config(session, chosen_user, cli_val, ss_val,
                                 is_temporary=(duration_type == "Temporary"), expires_at=expires_at)

    with col_b:
        if st.button("Remove Override", key="btn_override_remove",
                     help="Unsets user-level parameter. Falls back to cohort/account default."):
            for surface in SURFACES:
                call_sp(session, SP_UNSET_USER_CREDIT_LIMIT, chosen_user, surface)
            log_activity(session, "REMOVE_USER_OVERRIDE", target_user=chosen_user)
            tbl = fq_table(session, TABLE_CREDIT_CONFIG)
            safe_user = escape_sql_literal(chosen_user)
            try:
                session.sql(f"""
                    UPDATE {tbl} SET IS_ACTIVE = FALSE, UPDATED_AT = CURRENT_TIMESTAMP()
                    WHERE CONFIG_TYPE = 'USER_OVERRIDE' AND USER_NAME = '{safe_user}'
                """).collect()
            except Exception:
                pass
            st.success(f"✓ Override removed for {chosen_user}")


# --- Helper Functions ---

def _get_users_by_tag(session, tag_name: str, tag_value: str) -> list:
    """Get users with a specific tag value from ACCOUNT_USAGE."""
    safe_tag = escape_sql_literal(tag_name)
    safe_val = escape_sql_literal(tag_value)
    try:
        df = session.sql(f"""
            SELECT DISTINCT OBJECT_NAME AS USER_NAME
            FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
            WHERE TAG_NAME = '{safe_tag}'
              AND TAG_VALUE = '{safe_val}'
              AND DOMAIN = 'USER'
              AND OBJECT_DELETED IS NULL
            ORDER BY USER_NAME
        """).to_pandas()
        if not df.empty:
            return df["USER_NAME"].tolist()
    except Exception:
        pass
    return []


def _apply_cohort(session, cohort_id, members, cli_limit, ss_limit, dt_limit, is_temporary=False, expires_at=None):
    """
    Apply credit limits to all cohort members via a single bulk SP call.
    Previously O(N) round-trips → now 1 SP call that loops inside Snowflake.
    """
    tbl = fq_table(session, TABLE_CREDIT_CONFIG)
    actor = get_current_user(session)
    safe_actor = escape_sql_literal(actor)
    safe_cohort = escape_sql_literal(cohort_id)

    # --- 1. Save cohort config record ---
    try:
        session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT '{safe_cohort}' AS RN) s ON t.ROLE_NAME = s.RN AND t.CONFIG_TYPE = 'COHORT'
            WHEN MATCHED THEN UPDATE SET
                CLI_DAILY_LIMIT = {cli_limit}, SNOWSIGHT_DAILY_LIMIT = {ss_limit}, DESKTOP_DAILY_LIMIT = {dt_limit},
                UPDATED_BY = '{safe_actor}', UPDATED_AT = CURRENT_TIMESTAMP(), IS_ACTIVE = TRUE
            WHEN NOT MATCHED THEN INSERT
                (CONFIG_TYPE, ROLE_NAME, CLI_DAILY_LIMIT, SNOWSIGHT_DAILY_LIMIT, DESKTOP_DAILY_LIMIT, CREATED_BY, UPDATED_BY, IS_ACTIVE)
            VALUES ('COHORT', '{safe_cohort}', {cli_limit}, {ss_limit}, {dt_limit}, '{safe_actor}', '{safe_actor}', TRUE)
        """).collect()
    except Exception as e:
        st.error(f"✗ Config save failed: {e}")
        return

    if not members:
        # No direct members — call resolve SP first to populate via role hierarchy
        try:
            with st.spinner("Resolving cohort members via role hierarchy..."):
                session.sql(f"CALL {fq_table(session, 'SP_CC_RESOLVE_USER_COHORTS')}()").collect()
            resolved_rows = session.sql(f"""
                SELECT USER_NAME FROM {fq_table(session, 'CC_USER_COHORT_RESOLVED')}
                WHERE UPPER(COHORT_ROLE) = UPPER('{safe_cohort}')
            """).collect()
            members = [str(r[0]) for r in resolved_rows]
        except Exception as e:
            st.warning(f"Config saved but could not resolve members: {e}")
            return
        if not members:
            st.warning("Config saved but no members found — check that the role has users assigned (directly or via inherited roles).")
            return

    # --- 2. Single bulk SP call — server-side loop, no CLIENT_ABORT risk ---
    expires_str = str(expires_at) if expires_at else ""
    with st.spinner(f"Applying limits to {len(members)} users via bulk SP..."):
        ok, raw_msg = call_bulk_sp(
            session,
            SP_BULK_SET_COHORT_LIMITS,
            members,          # list → PARSE_JSON
            cli_limit,        # int
            ss_limit,         # int
            dt_limit,         # int (NEW — Desktop)
            is_temporary,     # bool
            expires_str,      # str
        )

    # --- 3. Parse result ---
    success_count = 0
    fail_count = 0
    errors = []
    try:
        result = json.loads(raw_msg)
        success_count = result.get("success", 0)
        fail_count = result.get("failed", 0)
        errors = result.get("errors", [])
    except (json.JSONDecodeError, TypeError):
        if ok:
            success_count = len(members)
        else:
            fail_count = len(members)
            errors = [raw_msg]

    log_activity(session, "SET_COHORT_LIMIT", target_role=cohort_id,
                 details={"cli": cli_limit, "snowsight": ss_limit,
                          "members": len(members),
                          "successes": success_count, "failures": fail_count,
                          "temporary": is_temporary,
                          "expires_at": str(expires_at) if expires_at else None},
                 new_value=f"CLI={cli_limit}, SS={ss_limit}")

    # --- 4. Feedback ---
    if fail_count == 0:
        st.success(f"✓ Applied to all **{success_count}** users.")
    else:
        st.warning(f"Completed: **{success_count}** succeeded, **{fail_count}** failed.")
        if ok is False and "SP_CC_BULK_SET_COHORT_LIMITS" in raw_msg:
            st.info("Tip: Bulk SP not found. Run Setup → Create Missing Objects first.")

    if errors:
        with st.expander(f"Errors ({len(errors)})"):
            for err in errors[:20]:
                st.text(f"✗ {err}")
            if len(errors) > 20:
                st.caption(f"... and {len(errors) - 20} more")

    if st.button("Reset / Start Over", key="btn_reset_cohort",
                 help="Clears selections and starts fresh."):
        for key in list(st.session_state.keys()):
            if key.startswith("cohort_") or key.startswith("trend_"):
                del st.session_state[key]
        st.rerun()

    # ── Native AI Budgets (Snowflake Preview) ───────────────────────────────────
    st.divider()
    with st.expander("🏦 Native AI Budgets _(Snowflake Preview)_ — hard enforcement layer", expanded=False):
        st.info(
            "**Snowflake is rolling out native AI Budgets for Cortex Agents (Preview).** "
            "This is a platform-level enforcement feature that complements CoCo's governance layer. "
            "When it becomes GA, consider using both together.",
            icon="ℹ️"
        )

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("""
**CoCo Credit Management** _(this app)_
- Per-user daily limits tracked in `CC_CREDIT_CONFIG`
- Soft controls — enforced by SP + task checks
- CLI / Snowsight / Desktop split
- Governance, audit trail, request workflow
- Works today on any account tier
""")
        with col_r:
            st.markdown("""
**Native AI Budgets** _(Snowflake Preview)_
- Tag-based monthly budget on Cortex Agent objects
- Hard enforcement — automated REVOKE USAGE at threshold
- Supports 80% alert + 100% block + up to 500% exceptions
- Enforced by Snowflake platform directly
- Requires Enterprise Edition · Preview feature
""")

        st.caption(
            "⚠️ **Scope:** Native AI Budgets apply to **Cortex Agent objects only** — not to general "
            "Cortex Code CLI/Snowsight usage. CoCo's per-user limits remain the right tool for "
            "controlling individual developer usage. Use native budgets to cap spend at the agent/service level."
        )

        st.divider()
        st.markdown("#### How to set up (run as ACCOUNTADMIN)")

        st.code("""\
-- Step 1: Create a cost center tag
CREATE TAG my_db.tags.cost_center
  ALLOWED_VALUES 'cortex-code-agent'
  COMMENT = 'AI budget cost center tag';

-- Step 2: Apply tag to the Cortex Agent object
ALTER AGENT IF EXISTS my_agent
  SET TAG my_db.tags.cost_center = 'cortex-code-agent';

-- Step 3: Create the budget (in the schema where you manage budgets)
USE SCHEMA budgets_db.budgets_schema;
CREATE SNOWFLAKE.CORE.BUDGET ai_agent_budget();

-- Step 4: Set monthly credit limit
CALL ai_agent_budget!SET_SPENDING_LIMIT(1000);

-- Step 5: Associate the tag with the budget
CALL budgets_db.budgets_schema.ai_agent_budget!SET_RESOURCE_TAGS(
  [[(SELECT SYSTEM$REFERENCE('TAG',
      'my_db.tags.cost_center', 'SESSION', 'applybudget')),
    'cortex-code-agent']],
  'UNION'
);

-- Step 6: Set email notification at 80%
CALL ai_agent_budget!SET_EMAIL_NOTIFICATIONS(
  'CC_EMAIL_INTEGRATION', 'admin@example.com'
);
CALL ai_agent_budget!SET_NOTIFICATION_THRESHOLD(80);

-- Step 7 (optional): Hard block at 100% — revoke role via SP
-- See: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-resource-budgets""",
        language="sql")

        st.caption(
            "Enforcement lag: up to **8 hours** (standard) or **~2 hours** (low-latency budget option). "
            "Budget resets monthly. Thresholds up to 500% supported for exception handling "
            "(e.g. re-grant access during peak periods, re-revoke at 200%)."
        )


def _save_user_config(session, username, cli_val, ss_val, is_temporary=False, expires_at=None):
    """Save user override to config table."""
    tbl = fq_table(session, TABLE_CREDIT_CONFIG)
    safe_user = escape_sql_literal(username)
    actor = escape_sql_literal(get_current_user(session))
    try:
        session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT '{safe_user}' AS UN) s
                ON t.USER_NAME = s.UN AND t.CONFIG_TYPE = 'USER_OVERRIDE'
            WHEN MATCHED THEN UPDATE SET
                CLI_DAILY_LIMIT = {cli_val}, SNOWSIGHT_DAILY_LIMIT = {ss_val}, DESKTOP_DAILY_LIMIT = {dt_val},
                UPDATED_BY = '{actor}', UPDATED_AT = CURRENT_TIMESTAMP(), IS_ACTIVE = TRUE
            WHEN NOT MATCHED THEN INSERT
                (CONFIG_TYPE, USER_NAME, CLI_DAILY_LIMIT, SNOWSIGHT_DAILY_LIMIT, DESKTOP_DAILY_LIMIT, CREATED_BY, UPDATED_BY, IS_ACTIVE)
            VALUES ('USER_OVERRIDE', '{safe_user}', {cli_val}, {ss_val}, {dt_val}, '{actor}', '{actor}', TRUE)
        """).collect()
    except Exception as e:
        st.error(f"✗ Config save failed: {e}")

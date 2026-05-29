"""
Cortex Code Credit Manager - Access Management (Admin) v4
==========================================================
Enterprise-grade: handles inherited roles, database role grants,
grant-to-role-then-to-user pattern.
v4: server-side user search (no full-user-list dropdown at 50K scale),
    bulk grant SP replaces O(N) per-user SP calls.
"""

import json
import re

import streamlit as st
import pandas as pd

from audit import log_activity
from config import (
    SP_GRANT_CORTEX_ACCESS,
    SP_REVOKE_CORTEX_ACCESS,
    SP_BULK_GRANT_ACCESS,
    escape_sql_literal,
    get_current_user,
    sanitize_identifier,
)
from utils import call_sp, call_bulk_sp, get_role_members, get_session, list_roles, search_users


def _filter_human_users(users_df: pd.DataFrame) -> list:
    """Filter out system/service accounts with UUID-style names."""
    if users_df.empty:
        return []
    names = users_df["NAME"].tolist()
    uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-")
    svc_pattern = re.compile(r"^(SVC_|MANAGED_|SYSTEM\$|APP_)")
    return [n for n in names
            if n and not uuid_pattern.match(str(n)) and not svc_pattern.match(str(n))]


def render(session):
    st.header("Access Management", help="Grant or revoke Cortex Code access for users, roles, or user tag groups.")
    st.caption("Control who can use Cortex Code. Grant the required database roles to users or account roles.")

    tab_grant, tab_current, tab_inheritance = st.tabs([
        "🔑 Grant Access", "📋 Current Access", "🔗 Role Inheritance"
    ])

    with tab_grant:
        _render_grant(session)
    with tab_current:
        _render_current(session)
    with tab_inheritance:
        _render_inheritance(session)


def _render_grant(session):
    st.subheader("Grant Cortex Code Access", help="Assign the CORTEX_USER and COPILOT_USER database roles needed to use Cortex Code.")

    grant_target = st.radio(
        "Grant to", ["Individual Users", "Account Role (recommended for scale)", "By User Tag"],
        horizontal=True, key="grant_target",
        help="Role: one statement covers all members. Tag: find users by tag value. Individual: search by username."
    )

    selected_users = []
    target_role = None

    if grant_target == "Individual Users":
        mode = st.radio(
            "Find users by", ["Search", "By Role Membership"], horizontal=True,
            key="access_mode",
            help="Search: type a username (server-side, works at 50K+ users). By Role: pick a role and see its members."
        )

        if mode == "Search":
            st.caption("Type at least 2 characters to search. Results limited to 50 matches.")
            query = st.text_input(
                "Search username / login / email", key="user_search_query",
                placeholder="e.g. john.doe or @acme.com",
                help="Searches NAME, LOGIN_NAME, and EMAIL in ACCOUNT_USAGE.USERS."
            )
            if len(query.strip()) >= 2:
                with st.spinner("Searching..."):
                    matches = search_users(session, query.strip())
                if matches:
                    selected_users = st.multiselect(
                        f"{len(matches)} match(es) — select to grant",
                        matches, key="access_user_select",
                        help="Showing up to 50 matches. Refine search if needed."
                    )
                else:
                    st.info("No users found. Try a different search term.")
            else:
                st.caption("↑ Type to search.")
        else:
            roles = list_roles(session)
            if roles:
                chosen_role = st.selectbox("Select role", roles, key="access_role_select",
                                           help="Shows all user members of this role.")
                if chosen_role:
                    members = get_role_members(session, chosen_role)
                    if members:
                        st.info(f"**{len(members)}** human members in `{chosen_role}` (managed service accounts filtered out)")
                        selected_users = st.multiselect(
                            "Select members", members, default=members,
                            key="access_role_members",
                            help="Direct human users of this role. UUID-style managed accounts are excluded. Users who inherit the role via a nested role won't appear here — use 'Account Role' to cover them."
                        )
                    else:
                        st.info(f"No human members found in {chosen_role}")

    elif grant_target == "By User Tag":
        col1, col2 = st.columns(2)
        with col1:
            tag_name = st.text_input("Tag Name", value="DEPARTMENT", key="access_tag_name",
                                     help="e.g., DEPARTMENT, COST_CENTER, AI_TIER")
        with col2:
            tag_value = st.text_input("Tag Value", placeholder="e.g., PLATFORM", key="access_tag_value",
                                      help="Users with this tag value will be selected.")
        if tag_name and tag_value:
            tagged_users = _get_users_by_tag(session, tag_name, tag_value)
            if tagged_users:
                st.info(f"**{len(tagged_users)}** users with `{tag_name}` = `{tag_value}`")
                selected_users = st.multiselect(
                    "Select users", tagged_users, default=tagged_users,
                    key="access_tag_members",
                    help="All tagged users pre-selected."
                )
            else:
                st.warning(f"No users found with tag `{tag_name}` = `{tag_value}`")

    else:
        # Grant to an account role (enterprise pattern)
        roles = list_roles(session)
        if roles:
            target_role = st.selectbox(
                "Select target role", roles, key="grant_role_target",
                help="All users who have this role (directly or inherited) will get Cortex Code access."
            )
            if target_role:
                members = get_role_members(session, target_role)
                st.info(f"Granting to role `{target_role}` affects **{len(members)}** current members (plus future members).")

    # Database roles to grant
    grant_options = st.multiselect(
        "Database roles to grant",
        ["SNOWFLAKE.COPILOT_USER", "SNOWFLAKE.CORTEX_USER"],
        default=["SNOWFLAKE.COPILOT_USER", "SNOWFLAKE.CORTEX_USER"],
        key="access_grant_roles",
        help="Both COPILOT_USER and CORTEX_USER are required for Cortex Code. Grant both."
    )

    # Execute
    if selected_users and grant_options:
        st.caption(f"Will grant **{', '.join(grant_options)}** to **{len(selected_users)}** users")
        if st.button("Apply Grants", type="primary", key="btn_apply_grants",
                     help="Bulk grant via SP — single round-trip regardless of user count."):
            _execute_grants_to_users(session, selected_users, grant_options)

    elif target_role and grant_options:
        st.caption(f"Will grant **{', '.join(grant_options)}** to role **{target_role}**")
        if st.button("Grant to Role", type="primary", key="btn_grant_role",
                     help="Executes GRANT DATABASE ROLE TO ROLE. All current and future role members get access."):
            _execute_grants_to_role(session, target_role, grant_options)


def _execute_grants_to_users(session, users, db_roles):
    """
    Grant DB roles to users via a single bulk SP call.
    Previously O(users × roles) round-trips — now 1 SP call server-side.
    """
    with st.spinner(f"Granting to {len(users)} users via bulk SP..."):
        ok, raw_msg = call_bulk_sp(
            session,
            SP_BULK_GRANT_ACCESS,
            users,      # list → PARSE_JSON VARIANT
            db_roles,   # list → PARSE_JSON VARIANT
        )

    # Parse JSON result from SP
    success_count, fail_count, errors = 0, 0, []
    try:
        result = json.loads(raw_msg)
        success_count = result.get("success", 0)
        fail_count = result.get("failed", 0)
        errors = result.get("errors", [])
    except (json.JSONDecodeError, TypeError):
        if ok:
            success_count = len(users) * len(db_roles)
        else:
            fail_count = len(users) * len(db_roles)
            errors = [raw_msg]

    # Log each grant in audit (log once per user, not per DB role)
    for user in users:
        status = "SUCCESS" if ok else "FAILED"
        log_activity(session, "GRANT_ACCESS", target_user=user,
                     details={"database_roles": db_roles, "bulk": True},
                     status=status)

    if fail_count == 0:
        st.success(f"✓ {success_count} grants applied to {len(users)} users.")
    else:
        st.warning(f"{success_count} ✓, {fail_count} ✗")
        if ok is False and "SP_CC_BULK_GRANT_ACCESS" in raw_msg:
            st.info("Tip: Bulk SP not found. Run Setup → Create Missing Objects first.")
        if errors:
            with st.expander(f"Errors ({len(errors)})"):
                for err in errors[:20]:
                    st.text(f"✗ {err}")
                if len(errors) > 20:
                    st.caption(f"... and {len(errors) - 20} more")


def _execute_grants_to_role(session, role_name, db_roles):
    """Grant database roles to an account role (not individual users)."""
    safe_role = sanitize_identifier(role_name)
    successes, failures = 0, 0
    for db_role in db_roles:
        try:
            session.sql(f'GRANT DATABASE ROLE {db_role} TO ROLE "{safe_role}"').collect()
            successes += 1
            log_activity(session, "GRANT_ACCESS_TO_ROLE", target_role=role_name,
                         details={"database_role": db_role})
        except Exception as e:
            failures += 1
            st.error(f"✗ Failed to grant {db_role} to {role_name}: {e}")
            log_activity(session, "GRANT_ACCESS_TO_ROLE", target_role=role_name,
                         details={"database_role": db_role, "error": str(e)}, status="FAILED")

    if failures == 0:
        st.success(f"✓ Granted {', '.join(db_roles)} to role {role_name}")


def _render_current(session):
    st.subheader("Current Cortex Code Access", help="Shows which roles currently have SNOWFLAKE.CORTEX_USER granted. Users inherit access through these roles.")
    st.caption(
        "Shows which **roles** have SNOWFLAKE.CORTEX_USER granted. "
        "Users inherit access through these roles — not granted directly."
    )

    try:
        # Get roles that have CORTEX_USER database role
        df = session.sql("SHOW GRANTS OF DATABASE ROLE SNOWFLAKE.CORTEX_USER").to_pandas()
        if df.empty:
            st.info("No grants found for SNOWFLAKE.CORTEX_USER.")
            return

        # Normalize column names - strip quotes and uppercase
        df.columns = [c.strip('"').upper() for c in df.columns]

        # The columns from SHOW GRANTS OF DATABASE ROLE are:
        # CREATED_ON, ROLE, GRANTED_TO, GRANTEE_NAME, GRANTED_BY
        if "GRANTEE_NAME" not in df.columns:
            st.error(f"Unexpected columns: {list(df.columns)}")
            return

        # Filter to only ROLE grants (not APPLICATION grants)
        role_grants = df[df["GRANTED_TO"] == "ROLE"].copy()

        if not role_grants.empty:
            st.markdown(f"**{len(role_grants)}** roles have `SNOWFLAKE.CORTEX_USER`:")
            display_df = role_grants[["GRANTEE_NAME", "CREATED_ON"]].rename(
                columns={"GRANTEE_NAME": "Role Name", "CREATED_ON": "Granted On"}
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Revoke option
            revoke_targets = st.multiselect(
                "Select roles to revoke CORTEX_USER from",
                role_grants["GRANTEE_NAME"].tolist(),
                key="revoke_select",
                help="Removing CORTEX_USER from a role removes Cortex Code access for all its members."
            )
            if revoke_targets and st.button("Revoke Selected", type="secondary", key="btn_revoke",
                                            help="Executes REVOKE DATABASE ROLE from selected roles."):
                for target in revoke_targets:
                    try:
                        safe_target = sanitize_identifier(target)
                        session.sql(f'REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_USER FROM ROLE "{safe_target}"').collect()
                        log_activity(session, "REVOKE_ACCESS", target_role=target,
                                     details={"database_role": "SNOWFLAKE.CORTEX_USER"})
                        st.success(f"✓ Revoked from {target}")
                    except Exception as e:
                        st.error(f"✗ Failed to revoke from {target}: {e}")
        else:
            st.info("No role-level grants found.")

    except Exception as e:
        st.error(f"✗ Could not query grants: {e}")
        st.caption("This requires MANAGE GRANTS or ACCOUNTADMIN privilege.")


def _render_inheritance(session):
    st.subheader("Role Inheritance Viewer", help="Inspect a role's privilege chain — what it inherits and who has it. Useful for debugging unexpected access.")
    st.caption(
        "Understand how access flows. Pick a role to see what it inherits and who has it."
    )

    roles = list_roles(session)
    if not roles:
        st.warning("No roles available.")
        return

    chosen = st.selectbox("Select role to inspect", roles, key="inspect_role",
                          help="Shows role grants hierarchy — what this role has, and who has this role.")
    if not chosen:
        return

    safe_role = sanitize_identifier(chosen)

    # What does this role have?
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Grants TO this role** (what it inherits):")
        try:
            df = session.sql(f'SHOW GRANTS TO ROLE "{safe_role}"').to_pandas()
            if not df.empty:
                df.columns = [c.strip('"').upper() for c in df.columns]
                display_cols = []
                if "PRIVILEGE" in df.columns:
                    display_cols.append("PRIVILEGE")
                if "NAME" in df.columns:
                    display_cols.append("NAME")
                if "GRANTED_ON" in df.columns:
                    display_cols.append("GRANTED_ON")
                if display_cols:
                    st.dataframe(df[display_cols].head(30), use_container_width=True, hide_index=True, height=300)
                else:
                    st.dataframe(df.head(30), use_container_width=True, hide_index=True, height=300)
            else:
                st.caption("No grants found.")
        except Exception as e:
            st.error(f"Error: {e}")

    with col2:
        st.markdown("**Grants OF this role** (who has it):")
        try:
            members = get_role_members(session, chosen)
            if members:
                st.dataframe(pd.DataFrame({"User": members}),
                            use_container_width=True, hide_index=True, height=300)
            else:
                st.caption("No user members.")
        except Exception as e:
            st.error(f"Error: {e}")


def _get_users_by_tag(session, tag_name: str, tag_value: str) -> list:
    """Get users with a specific tag value from ACCOUNT_USAGE."""
    from config import escape_sql_literal
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
            df.columns = [c.strip('"').upper() for c in df.columns]
            return df["USER_NAME"].tolist()
    except Exception:
        pass
    return []

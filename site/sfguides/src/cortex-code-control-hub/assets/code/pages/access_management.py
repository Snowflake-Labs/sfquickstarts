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
    SP_MANAGE_ROLE_GRANT,
    escape_sql_literal,
    get_current_user,
    sanitize_identifier,
    sql_identifier,
)
from utils import call_sp, call_bulk_sp, get_role_members, get_session, list_roles, list_users, search_users
from utils import (
    PATTERN_HELP as _PATTERN_HELP,
    match_pattern as _match,
    match_roles as _match_roles,
    pick_matches as _pick_matches,
)

_BG = "#0e1117"


def _sec(title):
    """Consistent section header — muted slate style."""
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def _load_cortex_user_grants(_session):
    """Return DataFrame of SHOW GRANTS OF DATABASE ROLE SNOWFLAKE.CORTEX_USER."""
    try:
        return _session.sql("SHOW GRANTS OF DATABASE ROLE SNOWFLAKE.CORTEX_USER").to_pandas()
    except Exception:
        return pd.DataFrame()



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

    tab_grant, tab_current = st.tabs([
        "🔑 Grant Access", "📋 Current Access"
    ])

    with tab_grant:
        _render_grant(session)
    with tab_current:
        _render_current(session)


def _render_grant(session):
    st.subheader("Grant Cortex Code Access", help="Assign CORTEX_USER or CORTEX_AGENT_USER (plus transitional COPILOT_USER) needed to use Cortex Code.")

    grant_target = st.radio(
        "Grant to", [
            "Individual Users",
            "Account Role (DB role → role)",
            "Role → Role (AI role → domain role)",
            "By User Tag",
        ],
        horizontal=True, key="grant_target",
        help=(
            "Individual Users: search by username. "
            "Account Role: grant Cortex DB roles (CORTEX_USER or CORTEX_AGENT_USER, plus transitional COPILOT_USER) to a role. "
            "Role → Role: grant a generic AI role to domain roles (enterprise pattern). "
            "By User Tag: find users by tag value."
        )
    )

    selected_users = []
    target_roles = []
    source_role = None
    target_roles_r2r = []

    if grant_target == "Individual Users":
        mode = st.radio(
            "Find users by", ["Search", "Pattern", "By Role Membership"], horizontal=True,
            key="access_mode",
            help="Search: type a username (server-side, works at 50K+ users). "
                 "Pattern: wildcard match on username, no result cap. "
                 "By Role: pick a role (or role pattern) and see its members."
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
        elif mode == "Pattern":
            pattern = st.text_input(
                "Username pattern", key="user_pattern",
                placeholder="e.g. JOHN* or *_ANALYST",
                help=_PATTERN_HELP + " Service and managed accounts are excluded."
            )
            if pattern.strip():
                with st.spinner("Matching users..."):
                    users = _filter_human_users(list_users(session))
                selected_users = _pick_matches("Users", _match(users, pattern),
                                               "user_pattern_sel", pattern)
        else:
            roles = list_roles(session)
            if roles:
                role_pattern = st.text_input(
                    "Role pattern (optional)", key="member_role_pattern",
                    placeholder="e.g. ENG_*  — leave blank to pick one role",
                    help=_PATTERN_HELP + " Members of every matching role are combined."
                )
                if role_pattern.strip():
                    chosen_roles, excluded = _match_roles(roles, role_pattern)
                    if excluded:
                        st.caption(f"Not auto-selected: {', '.join(excluded)}.")
                    if not chosen_roles:
                        st.info(f"No roles match `{role_pattern}`.")
                    else:
                        st.caption(f"{len(chosen_roles)} matching role(s): {', '.join(chosen_roles)}")
                        with st.spinner(f"Resolving members of {len(chosen_roles)} role(s)..."):
                            members = sorted({m for r in chosen_roles
                                              for m in get_role_members(session, r)})
                        selected_users = _pick_matches("Users", members, "access_pattern_members",
                                                       role_pattern)
                else:
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

    elif grant_target == "Role → Role (AI role → domain role)":
        st.caption(
            "Enterprise pattern: select a generic AI role (e.g. `CORTEX_ACCESS_ROLE`) that already has "
            "CORTEX_USER or CORTEX_AGENT_USER (plus transitional COPILOT_USER), then grant it to one or more domain roles. "
            "Runs: `GRANT ROLE <source> TO ROLE <target>`"
        )
        roles = list_roles(session)
        if roles:
            col_src, col_tgt = st.columns(2)
            with col_src:
                source_role = st.selectbox(
                    "Source AI role", roles, key="r2r_source_role",
                    help="The generic AI/access role that already has CORTEX_USER or CORTEX_AGENT_USER (plus transitional COPILOT_USER)."
                )
            with col_tgt:
                target_pattern = st.text_input(
                    "Target roles pattern (optional)", key="r2r_target_pattern",
                    placeholder="e.g. *_ANALYST  — leave blank to pick roles",
                    help=_PATTERN_HELP
                )
                if not target_pattern.strip():
                    target_roles_r2r = st.multiselect(
                        "Target domain roles", roles, key="r2r_target_roles",
                        help="Domain roles that should inherit access from the source AI role."
                    )
            if target_pattern.strip():
                candidates = [r for r in roles if r != source_role]
                matches, excluded = _match_roles(candidates, target_pattern)
                target_roles_r2r = _pick_matches("Roles", matches, "r2r_pattern_sel",
                                                 target_pattern, excluded)
            if source_role and target_roles_r2r:
                st.caption(
                    f"Will run `GRANT ROLE {source_role} TO ROLE ...` for "
                    f"**{len(target_roles_r2r)}** role(s)"
                )
                if st.button("Grant Role to Roles", type="primary", key="btn_r2r_grant",
                             help="Executes GRANT ROLE <source> TO ROLE <target> for each selected target."):
                    _execute_role_to_role_grants(session, source_role, target_roles_r2r)
        # Skip DB role multiselect for this mode — fall through to execute at bottom
        return

    elif grant_target == "By User Tag":
        col1, col2 = st.columns(2)
        with col1:
            tag_name = st.text_input("Tag Name", value="DEPARTMENT", key="access_tag_name",
                                     help="e.g., DEPARTMENT, COST_CENTER, AI_TIER")
        with col2:
            tag_value = st.text_input("Tag Value", placeholder="e.g., PLATFORM or ENG*", key="access_tag_value",
                                      help="Users with a matching tag value will be selected. " + _PATTERN_HELP)
        if tag_name and tag_value:
            tagged = _get_user_tag_values(session, tag_name)
            hit_values = set(_match(sorted(tagged), tag_value))
            tagged_users = sorted({u for v in hit_values for u in tagged[v]})
            if tagged_users:
                st.info(f"**{len(tagged_users)}** users with `{tag_name}` matching `{tag_value}` "
                        f"(values: {', '.join(sorted(hit_values))})")
                selected_users = _pick_matches("Users", tagged_users, "access_tag_members", tag_value)
            else:
                st.warning(f"No users found with tag `{tag_name}` matching `{tag_value}`")

    else:
        # Grant to an account role (enterprise pattern)
        roles = list_roles(session)
        if roles:
            role_pattern = st.text_input(
                "Target roles pattern (optional)", key="grant_role_pattern",
                placeholder="e.g. ENG_*  — leave blank to pick one role",
                help=_PATTERN_HELP
            )
            if role_pattern.strip():
                matches, excluded = _match_roles(roles, role_pattern)
                target_roles = _pick_matches("Roles", matches, "grant_role_pattern_sel",
                                             role_pattern, excluded)
            else:
                target_role = st.selectbox(
                    "Select target role", roles, key="grant_role_target",
                    help="All users who have this role (directly or inherited) will get Cortex Code access."
                )
                if target_role:
                    target_roles = [target_role]
                    members = get_role_members(session, target_role)
                    st.info(f"Granting to role `{target_role}` affects **{len(members)}** current members (plus future members).")

    # Database roles to grant
    grant_options = st.multiselect(
        "Database roles to grant",
        ["SNOWFLAKE.CORTEX_USER", "SNOWFLAKE.CORTEX_AGENT_USER", "SNOWFLAKE.COPILOT_USER"],
        default=["SNOWFLAKE.CORTEX_USER", "SNOWFLAKE.COPILOT_USER"],
        key="access_grant_roles",
        help="Cortex Code needs CORTEX_USER or CORTEX_AGENT_USER (least privilege: agent features only). "
             "COPILOT_USER is transitional: CoCo in Snowsight needs it only until BCR-2445 reaches your "
             "account, after which granting it has no effect."
    )
    st.caption("COPILOT_USER is **transitional** (BCR-2445, rolling out from October 2026). "
               "Keep it until the change reaches your account; it is harmless afterwards.")

    # Execute
    if selected_users and grant_options:
        st.caption(f"Will grant **{', '.join(grant_options)}** to **{len(selected_users)}** users")
        if st.button("Apply Grants", type="primary", key="btn_apply_grants",
                     help="Bulk grant via SP — single round-trip regardless of user count."):
            _execute_grants_to_users(session, selected_users, grant_options)

    elif target_roles and grant_options:
        if len(target_roles) == 1:
            st.caption(f"Will grant **{', '.join(grant_options)}** to role **{target_roles[0]}**")
        else:
            st.caption(f"Will grant **{', '.join(grant_options)}** to **{len(target_roles)}** roles")
        if st.button("Grant to Role", type="primary", key="btn_grant_role",
                     help="Executes GRANT DATABASE ROLE TO ROLE. All current and future role members get access."):
            for role in target_roles:
                _execute_grants_to_role(session, role, grant_options)


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


def _role_grant(session, action, grant_type, source, target):
    """
    Run a role-level GRANT/REVOKE via SP_CC_MANAGE_ROLE_GRANT (owner's rights).
    The app role lacks MANAGE GRANTS, so these must not run directly.
    Raises on failure so callers keep their existing try/except handling.
    """
    ok, msg = call_sp(session, SP_MANAGE_ROLE_GRANT, action, grant_type, source, target)
    if not ok:
        raise RuntimeError(msg)


def _execute_grants_to_role(session, role_name, db_roles):
    """Grant database roles to an account role (not individual users)."""
    safe_role = sql_identifier(role_name)
    successes, failures = 0, 0
    for db_role in db_roles:
        try:
            _role_grant(session, "GRANT", "DATABASE_ROLE", db_role, role_name)
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


def _execute_role_to_role_grants(session, source_role, target_roles):
    """
    Grant an account role (e.g. AI_ACCESS_ROLE) to one or more domain roles.
    Runs: GRANT ROLE <source> TO ROLE <target>
    Enterprise pattern: the AI role carries the Cortex DB roles and
    domain roles inherit access without direct DB-role grants.
    """
    safe_src = sql_identifier(source_role)
    successes, failures = 0, 0
    for target in target_roles:
        safe_tgt = sql_identifier(target)
        try:
            _role_grant(session, "GRANT", "ROLE", source_role, target)
            successes += 1
            log_activity(session, "GRANT_ROLE_TO_ROLE",
                         details={"source_role": source_role, "target_role": target})
        except Exception as e:
            failures += 1
            st.error(f"✗ Failed to grant {source_role} → {target}: {e}")
            log_activity(session, "GRANT_ROLE_TO_ROLE",
                         details={"source_role": source_role, "target_role": target,
                                  "error": str(e)}, status="FAILED")
    if failures == 0 and successes > 0:
        st.success(f"✓ Granted role `{source_role}` to {successes} domain role(s)")


def _render_current(session):
    st.subheader("Current Cortex Code Access", help="Shows which roles currently have SNOWFLAKE.CORTEX_USER granted. Users inherit access through these roles.")
    st.caption(
        "Shows which **roles** have SNOWFLAKE.CORTEX_USER granted. "
        "Users inherit access through these roles — not granted directly."
    )

    try:
        # Get roles that have CORTEX_USER database role
        df = _load_cortex_user_grants(session)
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
            grantees = role_grants["GRANTEE_NAME"].tolist()
            revoke_pattern = st.text_input(
                "Roles pattern (optional)", key="revoke_pattern",
                placeholder="e.g. TEMP_*  — leave blank to pick roles", help=_PATTERN_HELP
            )
            if revoke_pattern.strip():
                matches, excluded = _match_roles(grantees, revoke_pattern)
                revoke_targets = _pick_matches("Roles", matches, "revoke_pattern_sel",
                                               revoke_pattern, excluded)
            else:
                revoke_targets = st.multiselect(
                    "Select roles to revoke CORTEX_USER from", grantees,
                    key="revoke_select",
                    help="Removing CORTEX_USER from a role removes Cortex Code access for all its members."
                )
            if revoke_targets and st.button("Revoke Selected", type="secondary", key="btn_revoke",
                                            help="Executes REVOKE DATABASE ROLE from selected roles."):
                for target in revoke_targets:
                    try:
                        safe_target = sql_identifier(target)
                        _role_grant(session, "REVOKE", "DATABASE_ROLE", "SNOWFLAKE.CORTEX_USER", target)
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

    # ── Role-to-Role grant inspection & revoke ────────────────────────────────
    st.divider()
    _sec("Role → Role Grants (enterprise AI role pattern)")
    st.caption(
        "Inspect which domain roles have a generic AI role granted to them. "
        "Use this to revoke access granted via `GRANT ROLE <ai_role> TO ROLE <domain_role>`."
    )
    roles = list_roles(session)
    if roles:
        inspect_src = st.selectbox(
            "Select AI/source role to inspect", roles, key="r2r_inspect_src",
            help="Shows all roles that have this role granted to them."
        )
        if inspect_src:
            try:
                safe_src = sql_identifier(inspect_src)
                gdf = session.sql(f'SHOW GRANTS OF ROLE {safe_src}').to_pandas()
                if not gdf.empty:
                    gdf.columns = [c.strip('"').upper() for c in gdf.columns]
                    # Filter to ROLE grantees only (exclude USER grants)
                    role_col = "GRANTEE_NAME" if "GRANTEE_NAME" in gdf.columns else gdf.columns[3]
                    type_col = "GRANTED_TO" if "GRANTED_TO" in gdf.columns else None
                    if type_col:
                        role_grantees = gdf[gdf[type_col] == "ROLE"][role_col].tolist()
                    else:
                        role_grantees = gdf[role_col].tolist()

                    if role_grantees:
                        st.caption(f"`{inspect_src}` is granted to **{len(role_grantees)}** role(s)")
                        st.dataframe(
                            gdf[[role_col]].rename(columns={role_col: "Role with access"}),
                            use_container_width=True, hide_index=True
                        )
                        r2r_revoke_pattern = st.text_input(
                            "Roles pattern (optional)", key="r2r_revoke_pattern",
                            placeholder="e.g. *_ANALYST  — leave blank to pick roles",
                            help=_PATTERN_HELP
                        )
                        if r2r_revoke_pattern.strip():
                            matches, excluded = _match_roles(role_grantees, r2r_revoke_pattern)
                            revoke_r2r = _pick_matches("Roles", matches, "r2r_revoke_pattern_sel",
                                                       r2r_revoke_pattern, excluded)
                        else:
                            revoke_r2r = st.multiselect(
                                "Select roles to revoke from", role_grantees,
                                key="r2r_revoke_select",
                                help=f"Will run: REVOKE ROLE {inspect_src} FROM ROLE <target>"
                            )
                        if revoke_r2r and st.button(
                            "Revoke Role Grants", type="secondary", key="btn_r2r_revoke",
                            help="Executes REVOKE ROLE <source> FROM ROLE <target>."
                        ):
                            for tgt in revoke_r2r:
                                safe_tgt = sql_identifier(tgt)
                                try:
                                    _role_grant(session, "REVOKE", "ROLE", inspect_src, tgt)
                                    log_activity(
                                        session, "REVOKE_ROLE_FROM_ROLE",
                                        details={"source_role": inspect_src, "target_role": tgt}
                                    )
                                    st.success(f"✓ Revoked {inspect_src} from {tgt}")
                                except Exception as e:
                                    st.error(f"✗ Failed to revoke from {tgt}: {e}")
                    else:
                        st.info(f"`{inspect_src}` is not currently granted to any role.")
                else:
                    st.info(f"`{inspect_src}` has no grants.")
            except Exception as e:
                st.error(f"✗ Could not inspect role grants: {e}")


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
        _sec("Grants TO this role (what it inherits)")
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
        _sec("Grants OF this role (who has it)")
        try:
            members = get_role_members(session, chosen)
            if members:
                st.dataframe(pd.DataFrame({"User": members}),
                            use_container_width=True, hide_index=True, height=300)
            else:
                st.caption("No user members.")
        except Exception as e:
            st.error(f"Error: {e}")


def _get_user_tag_values(session, tag_name: str) -> dict:
    """Map each value of a user tag to the users carrying it (ACCOUNT_USAGE)."""
    from config import escape_sql_literal
    safe_tag = escape_sql_literal(tag_name)
    result = {}
    try:
        df = session.sql(f"""
            SELECT DISTINCT OBJECT_NAME AS USER_NAME, TAG_VALUE
            FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
            WHERE TAG_NAME = '{safe_tag}'
              AND DOMAIN = 'USER'
              AND OBJECT_DELETED IS NULL
            ORDER BY USER_NAME
        """).to_pandas()
        if not df.empty:
            df.columns = [c.strip('"').upper() for c in df.columns]
            for user, value in zip(df["USER_NAME"], df["TAG_VALUE"]):
                if value is not None:
                    result.setdefault(str(value), []).append(user)
    except Exception:
        pass
    return result

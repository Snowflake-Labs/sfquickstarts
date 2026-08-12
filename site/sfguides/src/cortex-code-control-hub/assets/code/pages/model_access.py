"""
CoCo Control Hub - Model Access (Admin) v4
===========================================
Interactive tier management — create, edit, delete tiers, assign models.
All config persisted to DB (CC_APP_CONFIG + CC_MODEL_CONFIG).
Falls back to config.py defaults on cold start.
"""

import json

import pandas as pd
import streamlit as st

from audit import log_activity
from config import (
    KNOWN_MODELS,
    MODEL_CATEGORIES,
    SP_ENFORCE_MODEL_ACCESS,
    SP_REVOKE_MODEL_ACCESS,
    TABLE_MODEL_CONFIG,
    TABLE_MODEL_ROLE_MAPPING,
    TABLE_USAGE_DAILY,
    escape_sql_literal,
    fq_table,
    get_current_user,
    sanitize_identifier,
    sql_identifier,
)
from utils import (
    call_bulk_sp,
    get_model_tier_assignments,
    get_role_members,
    get_tier_config,
    list_roles,
    save_model_tier_assignment,
    save_tier_config,
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



# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def render(session):
    st.header("Model Access", help="Manage model tiers, control which roles access which models, and see effective access across your account.")
    st.caption("Define tiers, assign models, map tiers to roles, and enforce access policies.")

    tab_tiers, tab_models, tab_mapping, tab_effective = st.tabs([
        "⚙️ Tier Management", "🧠 Available Models", "🔗 Role-Model Mapping", "👁️ Effective Access"
    ])

    with tab_tiers:
        _render_tier_management(session)
    with tab_models:
        _render_models(session)
    with tab_mapping:
        _render_mapping(session)
    with tab_effective:
        _render_effective_access(session)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1: Tier Management
# ─────────────────────────────────────────────────────────────────────────────

def _render_tier_management(session):
    st.subheader("Tier Management",
                 help="Create and manage model tiers. Each tier groups models by capability level. Assign roles to tiers to control access.")
    st.caption("Tiers group models by capability and cost. Roles are then mapped to tiers to control access.")

    actor = get_current_user(session)
    tiers = get_tier_config(session)                      # {tier_name: {description, tokens_per_credit, best_for}}
    assignments = get_model_tier_assignments(session)     # {model_name: [tier1, ...]}
    all_models = _discover_all_models(session)

    # Ensure discovered models appear in assignments (as unassigned if not already tracked)
    for m in all_models:
        if m not in assignments:
            assignments[m] = []

    # Build reverse map: tier → list of models
    tier_models: dict = {t: [] for t in tiers}
    for model, model_tiers in assignments.items():
        for t in model_tiers:
            if t in tier_models:
                tier_models[t].append(model)
            else:
                tier_models[t] = [model]

    # ── Create New Tier ────────────────────────────────────────────────────
    with st.expander("＋ Create New Tier", expanded=False):
        _render_create_tier_form(session, tiers, all_models, assignments, actor)

    st.divider()

    # ── Existing Tier Cards ────────────────────────────────────────────────
    if not tiers:
        st.info("No tiers configured. Create one above.")
        return

    for tier_name, tier_info in tiers.items():
        _render_tier_card(session, tier_name, tier_info, tier_models.get(tier_name, []),
                          all_models, tiers, assignments, actor)


def _render_tier_card(session, tier_name, tier_info, models_in_tier,
                      all_models, all_tiers, assignments, actor):
    """Render a single tier card with inline edit and model management."""
    with st.container(border=True):
        # Header row
        col_title, col_actions = st.columns([4, 1])
        with col_title:
            st.markdown(f"### {tier_name}")
            st.caption(tier_info.get("description", ""))
        with col_actions:
            st.write("")  # vertical spacing
            if st.button("🗑 Delete", key=f"del_{tier_name}",
                         help=f"Remove {tier_name}. Affected models become unassigned."):
                st.session_state[f"_confirm_delete_{tier_name}"] = True

        # Delete confirmation
        if st.session_state.get(f"_confirm_delete_{tier_name}"):
            st.warning(f"Delete **{tier_name}**? Models assigned here will become unassigned.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete", key=f"confirm_del_{tier_name}", type="primary"):
                    new_tiers = {k: v for k, v in all_tiers.items() if k != tier_name}
                    save_tier_config(session, new_tiers, actor)
                    # Remove tier from all model assignments
                    for model, model_tiers in assignments.items():
                        if tier_name in model_tiers:
                            save_model_tier_assignment(
                                session, model,
                                [t for t in model_tiers if t != tier_name], actor
                            )
                    log_activity(session, "DELETE_TIER", details={"tier": tier_name})
                    st.cache_data.clear()
                    st.rerun()
            with c2:
                if st.button("Cancel", key=f"cancel_del_{tier_name}"):
                    del st.session_state[f"_confirm_delete_{tier_name}"]
                    st.rerun()
            return

        # Metadata row
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption(f"**Token efficiency:** {tier_info.get('tokens_per_credit', 'Not set')}")
        with col_b:
            st.caption(f"**Best for:** {tier_info.get('best_for', 'Not set')}")

        # Models in tier
        st.markdown(f"**Models in {tier_name}** ({len(models_in_tier)})")
        if models_in_tier:
            cols = st.columns(min(len(models_in_tier), 3))
            for i, model in enumerate(sorted(models_in_tier)):
                with cols[i % 3]:
                    known = KNOWN_MODELS.get(model, {})
                    st.markdown(
                        f'<div style="background:#161b22;border-radius:6px;padding:0.5rem 0.7rem;'
                        f'margin:2px 0;font-size:0.78rem;color:#c9d1d9;">'
                        f'<span style="color:#3fb950;font-size:0.8rem;">●</span> '
                        f'<b>{model}</b>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        else:
            st.caption("No models assigned.")

        # Inline edit / model management
        with st.expander(f"✏️ Edit {tier_name}",
                         expanded=st.session_state.get(f"_edit_open_{tier_name}", False)):
            _render_edit_tier_form(session, tier_name, tier_info, models_in_tier,
                                   all_models, all_tiers, assignments, actor)


def _render_edit_tier_form(session, tier_name, tier_info, current_models,
                            all_models, all_tiers, assignments, actor):
    """Inline form to edit tier metadata and manage its model assignments."""
    st.caption("Edit tier details and assign/remove models.")

    # ── Tier metadata ──────────────────────────────────────────────────────
    with st.container():
        _sec("Tier Details")
        col1, col2 = st.columns(2)
        with col1:
            new_desc = st.text_input(
                "Description", value=tier_info.get("description", ""),
                key=f"edit_desc_{tier_name}",
                help="What kind of tasks is this tier best for?"
            )
            new_tokens = st.text_input(
                "Token efficiency", value=tier_info.get("tokens_per_credit", ""),
                key=f"edit_tokens_{tier_name}",
                placeholder="e.g. ~25K output tokens/credit",
                help="Approximate output tokens per credit — for admin reference."
            )
        with col2:
            new_best_for = st.text_area(
                "Best for", value=tier_info.get("best_for", ""),
                key=f"edit_bestfor_{tier_name}", height=100,
                help="Describe which user personas or job roles should use this tier."
            )

        if st.button(f"Save Tier Details", key=f"save_meta_{tier_name}", type="primary",
                     help="Save description, token efficiency, and best-for text."):
            new_tiers = dict(all_tiers)
            new_tiers[tier_name] = {
                "description": new_desc,
                "tokens_per_credit": new_tokens,
                "best_for": new_best_for,
            }
            save_tier_config(session, new_tiers, actor)
            log_activity(session, "EDIT_TIER", details={"tier": tier_name})
            st.session_state[f"_edit_open_{tier_name}"] = True   # keep expander open
            st.cache_data.clear()
            st.success(f"✓ {tier_name} details saved.")

    st.divider()

    # ── Model assignment ───────────────────────────────────────────────────
    _sec("Assign / Remove Models")

    # Show current models in tier with remove buttons
    if current_models:
        st.markdown(f"**Currently in {tier_name}** ({len(current_models)}):")
        # Compact removable chips — 3 per row
        cols = st.columns(3)
        for i, model in enumerate(sorted(current_models)):
            with cols[i % 3]:
                if st.button(f"✕ {model}", key=f"rm_{tier_name}_{model}",
                             help=f"Remove {model} from {tier_name}"):
                    new_model_tiers = [t for t in assignments.get(model, []) if t != tier_name]
                    save_model_tier_assignment(session, model, new_model_tiers, actor)
                    log_activity(session, "REMOVE_MODEL_FROM_TIER",
                                 details={"model": model, "tier": tier_name})
                    st.session_state[f"_edit_open_{tier_name}"] = True
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.caption("No models assigned to this tier yet.")

    # Add models via searchable multiselect
    available_to_add = [m for m in sorted(all_models) if m not in current_models]
    st.markdown("**Add models:**")
    models_to_add = st.multiselect(
        f"Search and select models to add to {tier_name}",
        available_to_add,
        key=f"add_models_{tier_name}",
        placeholder="Type to search (e.g. claude, mistral, llama)...",
        label_visibility="collapsed",
    )
    if models_to_add and st.button(f"Add {len(models_to_add)} model(s) to {tier_name}",
                                    type="primary", key=f"btn_add_models_{tier_name}"):
        for model in models_to_add:
            new_model_tiers = list(set(assignments.get(model, []) + [tier_name]))
            save_model_tier_assignment(session, model, new_model_tiers, actor)
        log_activity(session, "ADD_MODELS_TO_TIER",
                     details={"models": models_to_add, "tier": tier_name, "count": len(models_to_add)})
        st.session_state[f"_edit_open_{tier_name}"] = True
        st.cache_data.clear()
        st.rerun()


def _render_create_tier_form(session, existing_tiers, all_models, assignments, actor):
    """Form for creating a brand-new tier."""
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input(
            "Tier name", placeholder="e.g. TIER_4 or POWER_USER",
            key="new_tier_name",
            help="Uppercase letters, numbers, and underscores only. e.g. TIER_1, ENTERPRISE."
        )
        new_desc = st.text_input(
            "Description", key="new_tier_desc",
            placeholder="e.g. High-frequency completions and autocomplete",
            help="What kinds of tasks this tier covers."
        )
    with col2:
        new_tokens = st.text_input(
            "Token efficiency", key="new_tier_tokens",
            placeholder="e.g. ~200K output tokens/credit",
            help="Approximate output tokens per credit for admin reference."
        )
        new_best_for = st.text_input(
            "Best for", key="new_tier_bestfor",
            placeholder="e.g. Business analysts, lite users",
            help="Which personas or job functions should use this tier."
        )

    # Initial model selection
    initial_models = st.multiselect(
        "Initial models (optional)", all_models, key="new_tier_models",
        help="You can add/remove models later from the tier card."
    )

    if st.button("Create Tier", type="primary", key="btn_create_tier",
                 help="Saves the new tier definition and assigns selected models."):
        if not new_name:
            st.error("Tier name is required.")
            return
        import re
        if not re.match(r'^[A-Z0-9_]+$', new_name.strip().upper()):
            st.error("Name must be uppercase letters, numbers, and underscores only.")
            return
        tier_key = new_name.strip().upper()
        if tier_key in existing_tiers:
            st.error(f"{tier_key} already exists.")
            return

        new_tiers = dict(existing_tiers)
        new_tiers[tier_key] = {
            "description": new_desc,
            "tokens_per_credit": new_tokens,
            "best_for": new_best_for,
        }
        save_tier_config(session, new_tiers, actor)

        # Assign initial models
        for model in initial_models:
            new_model_tiers = list(set(assignments.get(model, []) + [tier_key]))
            save_model_tier_assignment(session, model, new_model_tiers, actor)

        log_activity(session, "CREATE_TIER",
                     details={"tier": tier_key, "initial_models": initial_models})
        st.cache_data.clear()
        st.success(f"✓ Tier **{tier_key}** created with {len(initial_models)} model(s).")
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2: Available Models
# ─────────────────────────────────────────────────────────────────────────────

def _render_models(session):
    st.subheader("Models Discovered in Your Account",
                 help="Auto-detected from SHOW CORTEX BASE MODELS. Shows all models available in this account/region.")
    st.caption("Auto-detected via `SHOW CORTEX BASE MODELS IN SCHEMA SNOWFLAKE.MODELS`.")
    st.info(
        "**Note:** Not all models below are used by Cortex Code. "
        "Models marked 🟢 have been **actively used by CoCo in your account** (last 90 days). "
        "Snowflake manages the CoCo model subset internally — it may change over time. "
        "[Regional model availability →](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-regional-availability)"
    )

    discovered = _discover_all_models(session)

    if not discovered:
        st.warning("No models found. SHOW CORTEX BASE MODELS may require IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE.")
        return

    # Load current tier assignments for display
    assignments = get_model_tier_assignments(session)

    # Filter UI
    _sec("Filter Models")
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("🔍 Search models", placeholder="Type to filter (e.g. claude, mistral, llama)...",
                                    key="model_search", label_visibility="collapsed")
    with col_filter:
        filter_opt = st.selectbox("Show", ["All models", "CoCo-compatible only", "Unassigned only"],
                                  key="model_filter_type", label_visibility="collapsed")

    # Apply filters
    filtered = discovered
    if search_term:
        filtered = [m for m in filtered if search_term.lower() in m.lower()]
    if filter_opt == "CoCo-compatible only":
        # Will be filtered after coco_used_models is fetched below
        pass  # handled after the query
    elif filter_opt == "Unassigned only":
        filtered = [m for m in filtered if not assignments.get(m)]

    st.caption(f"Showing {len(filtered)} of {len(discovered)} models")
    st.divider()

    _sec("Model Registry")

    # Build case-insensitive lookup for KNOWN_MODELS (keys are lowercase, discovered are uppercase)
    _known_lower = {k.lower(): v for k, v in KNOWN_MODELS.items()}

    # Get models ACTUALLY used by CoCo (from usage history) for the green badge
    coco_used_models = set()
    try:
        coco_df = session.sql("""
            SELECT DISTINCT LOWER(f.KEY) AS M
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY h,
                 LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR) f
            WHERE h.USAGE_TIME >= DATEADD('day', -90, CURRENT_TIMESTAMP())
            UNION
            SELECT DISTINCT LOWER(f.KEY)
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY h,
                 LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR) f
            WHERE h.USAGE_TIME >= DATEADD('day', -90, CURRENT_TIMESTAMP())
            UNION
            SELECT DISTINCT LOWER(f.KEY)
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_DESKTOP_USAGE_HISTORY h,
                 LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR) f
            WHERE h.USAGE_TIME >= DATEADD('day', -90, CURRENT_TIMESTAMP())
        """).to_pandas()
        if not coco_df.empty:
            coco_used_models = set(coco_df.iloc[:, 0].str.lower().tolist())
            coco_used_models.discard("unknown")
    except Exception:
        pass

    # Apply CoCo filter now that we have usage data
    if filter_opt == "CoCo-compatible only":
        filtered = [m for m in filtered if m.lower() in coco_used_models]

    for model in filtered:
        known_info = _known_lower.get(model.lower(), {})
        is_coco = model.lower() in coco_used_models
        db_tiers = assignments.get(model, [])
        if isinstance(db_tiers, str):
            db_tiers = [db_tiers]
        description = known_info.get("description", "")
        tier_str = ", ".join(db_tiers) if db_tiers else "Unassigned"
        coco_badge = "🟢 Used by CoCo" if is_coco else "⚪ General"

        with st.container(border=True):
            st.markdown(f"**{model}** — `{tier_str}` — {coco_badge}")
            if description:
                st.caption(description)

    st.divider()

    # Tier reference (reads from DB)
    tiers = get_tier_config(session)
    _sec("Tier Reference")
    ref_data = [
        {
            "Tier": t,
            "Description": info.get("description", ""),
            "Token Efficiency": info.get("tokens_per_credit", ""),
            "Best For": info.get("best_for", ""),
        }
        for t, info in tiers.items()
    ]
    if ref_data:
        st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3: Role-Model Mapping
# ─────────────────────────────────────────────────────────────────────────────

def _render_mapping(session):
    st.subheader("Role → Model Mapping",
                 help="Choose which models each role's members can access. Enforced via CORTEX_MODELS_ALLOWLIST on each user.")
    st.caption("Control which models each role can access. Users inherit model access through their roles.")

    roles = list_roles(session)
    if not roles:
        st.warning("No roles available.")
        return

    discovered = _discover_all_models(session)
    if not discovered:
        st.info("No models discovered yet.")
        return

    tbl = fq_table(session, TABLE_MODEL_ROLE_MAPPING)
    try:
        existing = session.sql(f"SELECT * FROM {tbl} ORDER BY ROLE_NAME, MODEL_NAME").to_pandas()
    except Exception:
        existing = pd.DataFrame()

    chosen_role = st.selectbox("Select Role", roles, key="model_role_select",
                               help="Configure which models this role's members can use.")
    if not chosen_role:
        return

    # Reset multiselect when role changes
    if st.session_state.get("_prev_model_role") != chosen_role:
        st.session_state["_prev_model_role"] = chosen_role
        st.session_state.pop("model_assign_select", None)

    role_models = []
    if not existing.empty:
        existing.columns = [c.upper() for c in existing.columns]
        if "ROLE_NAME" in existing.columns and "MODEL_NAME" in existing.columns:
            role_models = existing[existing["ROLE_NAME"] == chosen_role]["MODEL_NAME"].tolist()

    if role_models:
        st.info(f"Currently assigned: **{', '.join(role_models)}**")
    else:
        st.caption("No model restrictions — all models accessible.")

    # Quick-assign by tier (reads tiers from DB)
    tiers = get_tier_config(session)
    assignments = get_model_tier_assignments(session)

    st.caption("Quick assign by tier:")
    tier_cols = st.columns(min(len(tiers) + 1, 4))
    for i, tier_name in enumerate(tiers):
        with tier_cols[i % len(tier_cols)]:
            if st.button(tier_name, key=f"preset_{tier_name}",
                         help=f"Add all {tier_name} models to current selection."):
                tier_models = [m for m, m_tiers in assignments.items() if tier_name in m_tiers]
                current = st.session_state.get("_model_preset", role_models if role_models else [])
                st.session_state["_model_preset"] = sorted(set(current) | set(tier_models))
                st.rerun()
    with tier_cols[len(tiers) % len(tier_cols)]:
        if st.button("All models", key="btn_all",
                     help="No model restrictions — assign all discovered models."):
            st.session_state["_model_preset"] = discovered
            st.rerun()

    # Fix: set session state directly — Streamlit ignores `default=` after first interaction
    if "_model_preset" in st.session_state:
        st.session_state["model_assign_select"] = st.session_state.pop("_model_preset")
    elif "model_assign_select" not in st.session_state:
        st.session_state["model_assign_select"] = role_models if role_models else discovered

    selected_models = st.multiselect(
        "Assign models to this role", discovered,
        key="model_assign_select",
        help="Only selected models will be accessible to this role's members."
    )

    # Warning about revoke behavior
    if role_models:
        removed = [m for m in role_models if m not in selected_models]
        if removed:
            st.warning(
                f"⚠️ **{len(removed)} model(s) will be revoked** from this role on save: "
                f"`{', '.join(removed[:5])}`{'...' if len(removed) > 5 else ''}. "
                "All previously assigned models not in the current selection will be removed. "
                "This may take a moment if the role has many existing grants."
            )
    else:
        st.info(
            "ℹ️ **First-time configuration for this role.** Only the selected models will be granted. "
            "No existing access will be revoked. Future changes will revoke models you remove from this list."
        )

    st.divider()

    enforcement = st.radio(
        "Enforcement method",
        [
            "Apply to Role Members (grant model app roles to each user)",
            "Apply to Role Directly (GRANT APPLICATION ROLE TO ROLE)",
            "Apply to Account (affects ALL users — ACCOUNTADMIN only)",
            "Save mapping only (enforce later)",
        ],
        index=0, key="enforcement_method",
        help=(
            "Role Members: iterates members and grants TO USER. "
            "Role Directly: single GRANT APPLICATION ROLE TO ROLE — inherits to all current and future members. "
            "Account: blanket ALTER ACCOUNT allowlist."
        )
    )

    if st.button("Save & Apply", type="primary", key="btn_save_model_map",
                 help="Saves the mapping and applies based on selected enforcement method."):
        # Revoke ALL existing model grants on this role/members first (full replace mode)
        # Then grant only the selected models
        _save_model_mapping(session, chosen_role, selected_models)
        if "Role Members" in enforcement:
            members = get_role_members(session, chosen_role)
            if members:
                st.caption(f"Revoking existing model access from {len(members)} member(s) — this may take a moment for large teams...")
                # Revoke all currently granted models (from app-tracked mapping)
                if role_models:
                    _revoke_from_role_members(session, chosen_role, role_models)
                _enforce_to_role_rbac(session, chosen_role, selected_models)
            else:
                st.warning(f"No members found in {chosen_role}.")
        elif "Role Directly" in enforcement:
            st.caption("Revoking existing model access from role — this may take a moment...")
            # Revoke all previously mapped models from the role
            if role_models:
                _revoke_model_app_role_from_role(session, chosen_role, role_models)
            _enforce_model_app_role_to_role(session, chosen_role, selected_models)
        elif "Account" in enforcement:
            _enforce_to_account(session, selected_models)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 4: Effective Access Matrix
# ─────────────────────────────────────────────────────────────────────────────

def _render_effective_access(session):
    st.subheader("Effective Access Matrix",
                 help="Cross-reference of which roles have access to which models, based on saved mappings.")
    st.caption("Which roles have access to which models (based on saved mappings).")

    tbl = fq_table(session, TABLE_MODEL_ROLE_MAPPING)
    try:
        mappings = session.sql(f"SELECT * FROM {tbl} ORDER BY ROLE_NAME").to_pandas()
    except Exception:
        mappings = pd.DataFrame()

    if mappings.empty:
        st.info("No mappings configured yet. Go to 'Role-Model Mapping' tab to set up.")
        return

    mappings.columns = [c.upper() for c in mappings.columns]
    roles_with_mappings = mappings["ROLE_NAME"].unique().tolist()
    models = sorted(mappings["MODEL_NAME"].unique().tolist())

    matrix_data = []
    for role in roles_with_mappings:
        row = {"Role": role}
        role_models = mappings[mappings["ROLE_NAME"] == role]["MODEL_NAME"].tolist()
        for model in models:
            row[model] = "✓" if model in role_models else "—"
        matrix_data.append(row)

    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _discover_all_models(session):
    """
    Discover ALL available models from SHOW CORTEX BASE MODELS.
    Falls back to usage history + KNOWN_MODELS if SHOW command unavailable.
    """
    models = set()

    # Primary: SHOW CORTEX BASE MODELS (returns all available models in account)
    try:
        df = session.sql("SHOW CORTEX BASE MODELS IN SCHEMA SNOWFLAKE.MODELS").to_pandas()
        if not df.empty:
            # Column is typically 'name' or 'MODEL_NAME'
            name_col = [c for c in df.columns if 'name' in c.lower()]
            if name_col:
                models.update(df[name_col[0]].tolist())
    except Exception:
        pass

    # Fallback 1: Usage summary (models actually used in last 30d)
    if not models:
        tbl = fq_table(session, TABLE_USAGE_DAILY)
        try:
            df = session.sql(f"""
                SELECT DISTINCT MODEL_NAME FROM {tbl}
                WHERE MODEL_NAME IS NOT NULL AND MODEL_NAME != 'UNKNOWN'
            """).to_pandas()
            if not df.empty:
                models.update(df["MODEL_NAME"].tolist())
        except Exception:
            pass

    # Fallback 2: ACCOUNT_USAGE granular usage
    if not models:
        try:
            df = session.sql("""
                SELECT DISTINCT f.KEY AS MODEL_NAME
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY h,
                     LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR) f
                WHERE h.USAGE_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
                UNION
                SELECT DISTINCT f.KEY AS MODEL_NAME
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY h,
                     LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR) f
                WHERE h.USAGE_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
            """).to_pandas()
            if not df.empty:
                models.update(df["MODEL_NAME"].tolist())
        except Exception:
            pass

    # Fallback 3: hardcoded KNOWN_MODELS (last resort)
    if not models:
        models.update(KNOWN_MODELS.keys())

    return sorted(list(models))


def _save_model_mapping(session, role_name, models):
    tbl = fq_table(session, TABLE_MODEL_ROLE_MAPPING)
    safe_role = escape_sql_literal(role_name)
    actor = escape_sql_literal(get_current_user(session))
    try:
        # Step 1: Upsert all new models first — no window where role has zero models
        for model in models:
            safe_model = escape_sql_literal(model)
            session.sql(f"""
                INSERT INTO {tbl} (ROLE_NAME, MODEL_NAME, GRANTED_BY, GRANTED_AT)
                SELECT '{safe_role}', '{safe_model}', '{actor}', CURRENT_TIMESTAMP()
                WHERE NOT EXISTS (
                    SELECT 1 FROM {tbl}
                    WHERE ROLE_NAME = '{safe_role}' AND MODEL_NAME = '{safe_model}'
                )
            """).collect()
        # Step 2: Remove models no longer in the list (only runs after all inserts succeed)
        if models:
            placeholders = ",".join(f"'{escape_sql_literal(m)}'" for m in models)
            session.sql(f"DELETE FROM {tbl} WHERE ROLE_NAME = '{safe_role}' AND MODEL_NAME NOT IN ({placeholders})").collect()
        else:
            session.sql(f"DELETE FROM {tbl} WHERE ROLE_NAME = '{safe_role}'").collect()
        log_activity(session, "SET_MODEL_MAPPING", target_role=role_name,
                     details={"models": models, "count": len(models)})
        st.success(f"✓ Saved {len(models)} model(s) for {role_name}")
    except Exception as e:
        st.error(f"✗ Failed: {e}")


def _enforce_to_role_rbac(session, role_name, models):
    """Grant SNOWFLAKE model application roles to each member of the role via owner-rights SP."""
    if not models:
        st.warning("No models selected.")
        return

    members = get_role_members(session, role_name)
    if not members:
        st.warning(f"No direct members found in {role_name}. No grants applied.")
        return

    model_list = ",".join(models)
    with st.spinner(f"Granting model access to {len(members)} member(s) of {role_name}…"):
        ok, raw = call_bulk_sp(session, SP_ENFORCE_MODEL_ACCESS, members, model_list)

    try:
        result = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        result = {"success": 0, "failed": 0, "errors": [str(raw)]}

    successes = result.get("success", 0)
    failures  = result.get("failed", 0)
    errors    = result.get("errors", [])

    log_activity(session, "ENFORCE_MODEL_ACCESS", target_role=role_name,
                 details={"method": "RBAC_PER_USER", "models": models,
                          "members": len(members), "successes": successes, "failures": failures})
    if failures == 0 and successes > 0:
        st.success(f"✓ Granted model access to {successes} grant(s) across {len(members)} user(s) in {role_name}")
    elif successes == 0:
        st.error(f"✗ Failed to grant model access")
        if errors:
            with st.expander("Errors"):
                for e in errors[:10]:
                    st.caption(e)
    else:
        st.warning(f"Granted {successes}, {failures} failed.")
        if errors:
            with st.expander("Errors"):
                for e in errors[:10]:
                    st.caption(e)


def _enforce_to_role_members(session, role_name, models):
    """Kept for backwards compatibility — now redirects to RBAC."""
    _enforce_to_role_rbac(session, role_name, models)


def _enforce_model_app_role_to_role(session, role_name, models):
    """
    Grant SNOWFLAKE model application roles TO a role via owner-rights SP.
    The SP runs as ACCOUNTADMIN (EXECUTE AS OWNER) so the Streamlit app role
    doesn't need MANAGE GRANTS.
    """
    if not models:
        st.warning("No models selected.")
        return
    model_list = ",".join(models)
    with st.spinner(f"Granting model application roles to role {role_name}…"):
        ok, raw = call_bulk_sp(session, SP_ENFORCE_MODEL_ACCESS,
                               [role_name], model_list)
    try:
        result = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        result = {"success": 0, "failed": 0, "errors": [str(raw)]}

    successes = result.get("success", 0)
    failures = result.get("failed", 0)
    errors = result.get("errors", [])

    log_activity(session, "ENFORCE_MODEL_ACCESS", target_role=role_name,
                 details={"method": "RBAC_TO_ROLE", "models": models,
                          "successes": successes, "failures": failures})
    if failures == 0 and successes > 0:
        st.success(
            f"✓ Granted {successes} model application role(s) to `{role_name}`. "
            "All current and future role members inherit this access."
        )
    elif successes == 0:
        st.error("✗ Failed to grant model access to role.")
        if errors:
            with st.expander("Errors"):
                for e in errors[:10]:
                    st.caption(e)
    else:
        st.warning(f"Granted {successes}, {failures} failed.")
        if errors:
            with st.expander("Errors"):
                for e in errors[:10]:
                    st.caption(e)


def _enforce_to_account(session, models):
    """Account-level allowlist — requires ACCOUNTADMIN on the Streamlit owner role."""
    model_list = ",".join(models)
    try:
        session.sql(f"ALTER ACCOUNT SET CORTEX_MODELS_ALLOWLIST = '{model_list}'").collect()
        log_activity(session, "ENFORCE_MODEL_ACCESS_ACCOUNT",
                     details={"method": "ACCOUNT", "models": models})
        st.success(f"✓ Account-level allowlist set to: {model_list}")
    except Exception as e:
        st.error(f"✗ Failed: {e}")
        st.caption("ALTER ACCOUNT requires ACCOUNTADMIN on the Streamlit owner role.")


def _revoke_model_app_role_from_role(session, role_name, models):
    """Revoke SNOWFLAKE model application roles FROM a role via owner-rights SP."""
    if not models:
        return
    model_list = ",".join(models)
    with st.spinner(f"Revoking {len(models)} model role(s) from {role_name}…"):
        ok, raw = call_bulk_sp(session, SP_REVOKE_MODEL_ACCESS,
                               [role_name], model_list)
    try:
        result = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        result = {"success": 0, "failed": 0}
    revoked = result.get("success", 0)
    errors = result.get("errors", [])
    if errors:
        st.warning(f"Revoked {revoked}, {len(errors)} failed: {'; '.join(errors[:3])}")
    elif revoked:
        st.success(f"✓ Revoked {revoked} model role(s) from `{role_name}`.")
        log_activity(session, "REVOKE_MODEL_ACCESS", target_role=role_name,
                     details={"method": "RBAC_TO_ROLE", "models": models, "revoked": revoked})


def _revoke_from_role_members(session, role_name, models):
    """Revoke model application roles from each member of the role via owner-rights SP."""
    members = get_role_members(session, role_name)
    if not members:
        return
    model_list = ",".join(models)
    with st.spinner(f"Revoking model access from {len(members)} member(s) of {role_name}…"):
        ok, raw = call_bulk_sp(session, SP_REVOKE_MODEL_ACCESS, members, model_list)
    try:
        result = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        result = {"success": 0, "failed": 0}
    log_activity(session, "REVOKE_MODEL_ACCESS", target_role=role_name,
                 details={"method": "RBAC_PER_USER", "models": models,
                          "revoked": result.get("success", 0)})

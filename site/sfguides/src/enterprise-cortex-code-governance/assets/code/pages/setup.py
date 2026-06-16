"""
Cortex Code Credit Manager - Setup & Verification
===================================================
In-app setup wizard. Verifies prerequisites, creates
missing objects, explains owner's rights architecture.

IMPORTANT: This page runs DDL as the Streamlit owner's role.
The app must be owned by ACCOUNTADMIN for setup to succeed.
"""

import streamlit as st
import pandas as pd
from config import (
    escape_sql_literal,
    get_current_role,
    get_current_user,
    ROLE_SP_OWNER,
    ROLE_APP,
    ROLE_ADMIN,
    ROLE_USER,
)
from audit import log_activity


# Objects to verify
REQUIRED_TABLES = [
    "CC_CREDIT_CONFIG",
    "CC_AUDIT_LOG",
    "CC_USAGE_DAILY_SUMMARY",
    "CC_USAGE_HOURLY_SUMMARY",
    "CC_CREDIT_REQUESTS",
    "CC_APP_CONFIG",
    "CC_MODEL_CONFIG",
    "CC_MODEL_ROLE_MAPPING",
    "CC_USER_COHORT_RESOLVED",
    "CC_COHORT_LEADS",
    "CC_SP_JOB_LOG",
    "CC_COHORT_REBALANCE_LOCK",    # TTL-based concurrency lock for rebalancing
]

REQUIRED_PROCEDURES = [
    "SP_CC_SET_ACCOUNT_CREDIT_LIMIT",
    "SP_CC_SET_USER_CREDIT_LIMIT",
    "SP_CC_UNSET_USER_CREDIT_LIMIT",
    "SP_CC_GRANT_CORTEX_ACCESS",
    "SP_CC_REVOKE_CORTEX_ACCESS",
    "SP_CC_REBALANCE_CREDITS",
    "SP_CC_ENFORCE_MODEL_ACCESS",
    "SP_CC_RESOLVE_USER_COHORTS",
    "SP_CC_REFRESH_USAGE_SUMMARIES",
    "SP_CC_EXPIRE_TEMPORARY_CREDITS",
    "SP_CC_DAILY_RESET_LIMITS",
    # Bulk operation SPs (created by this Setup page)
    "SP_CC_BULK_GRANT_ACCESS",
    "SP_CC_BULK_SET_COHORT_LIMITS",
    # Bridge rebalance SP — server-side EWMA + concurrency lock
    "SP_CC_COMPUTE_REBALANCE",
]

REQUIRED_TASKS = [
    "CC_REFRESH_USAGE_SUMMARIES",
    "CC_DAILY_RESET_LIMITS",
]

REQUIRED_ROLES = [
    ROLE_SP_OWNER,
    ROLE_APP,
    ROLE_ADMIN,
    ROLE_USER,
]


def render(session):
    st.header("Setup & Verification", help="One-time setup wizard. Creates all required Snowflake objects and seeds default configuration.")
    st.caption("Initialize required objects, verify prerequisites, and seed defaults.")

    current_role = get_current_role(session)
    is_accountadmin = "ACCOUNTADMIN" in current_role.upper()

    # --- Owner's Rights (collapsed by default — don't front-load new admins) ---
    with st.expander("How owner's rights execution works", expanded=False):
        st.markdown("""
All SQL in this app — including `ALTER USER`, `GRANT`, and `CREATE TABLE` — runs as the role
that **owns this Streamlit object**, not your login role.

- End users never need elevated privileges
- `CC_APP_ROLE` cannot `ALTER USER` directly — only the SPs (owned by ACCOUNTADMIN) can
- All elevated actions are validated inside stored procedures

**For setup to work, this Streamlit must be owned by ACCOUNTADMIN.**

```sql
-- Verify ownership:
SHOW STREAMLITS IN SCHEMA <db>.<schema>;

-- Transfer if needed:
GRANT OWNERSHIP ON STREAMLIT <db>.<schema>.<name> TO ROLE ACCOUNTADMIN;
```
        """)

    if is_accountadmin:
        st.success(f"Session role: **{current_role}** — setup can proceed.")
    else:
        st.warning(f"Session role: **{current_role}** — some steps require ACCOUNTADMIN.")

    st.divider()

    # --- Verification ---
    st.subheader("Prerequisite Check", help="Scans the target database/schema for all required tables, stored procedures, tasks, and roles.")
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_check = st.button("Run Check", type="primary", key="btn_verify",
                              help="Verifies all tables, SPs, tasks, and roles exist.")
    with col_info:
        st.caption("Checks tables, stored procedures, scheduled tasks, and roles.")

    if run_check:
        _run_verification(session)

    if "verification_results" in st.session_state:
        _display_verification(st.session_state["verification_results"])

    st.divider()

    # --- Create Objects ---
    st.subheader("Create Missing Objects", help="Runs prerequisites.sql and creates the two bulk SPs. Safe to re-run — uses IF NOT EXISTS and CREATE OR REPLACE.")

    with st.expander("What gets created", expanded=False):
        st.markdown("""
- **4 roles**: `CC_SP_OWNER_ROLE`, `CC_APP_ROLE`, `CC_ADMIN_ROLE`, `CC_USER_ROLE`
- **11 tables**: credit config, usage summaries, audit log, credit requests, model config, cohort mapping, job log
- **13 stored procedures**: set limits, bulk limits, grant access, bulk grant, rebalance, refresh, expire temporaries, daily reset
- **2 scheduled tasks**: 30-min usage refresh, midnight limit reset

Safe to run multiple times — all statements use `IF NOT EXISTS` or `CREATE OR REPLACE`.
        """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Missing Objects", type="primary", key="btn_setup",
                     help="Runs prerequisites.sql + creates bulk SPs. Safe to re-run."):
            _run_setup(session)
    with col2:
        if st.button("Grant App Roles to Me", key="btn_grants",
                     help="Grants CC_ADMIN_ROLE + CC_USER_ROLE to your user."):
            _grant_roles_to_current_user(session)

    st.divider()

    # --- Post-Setup ---
    st.subheader("Post-Setup Actions", help="Run these once after creating objects: seed the 10 default settings in CC_APP_CONFIG, then backfill 30 days of usage data.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Seed Default Settings", key="btn_seed",
                     help="Populates CC_APP_CONFIG with defaults for all 10 settings."):
            _seed_defaults(session)
    with col2:
        if st.button("Run Initial Data Refresh", key="btn_refresh",
                     help="Backfills 30 days of usage data from ACCOUNT_USAGE."):
            with st.spinner("Running usage refresh — this may take 1-2 minutes."):
                try:
                    from config import fq_sp
                    fq = fq_sp(session, "SP_CC_REFRESH_USAGE_SUMMARIES")
                    result = session.sql(f"CALL {fq}()").collect()
                    msg = str(result[0][0]) if result else "OK"
                    st.success(f"✓ {msg}")
                except Exception as e:
                    st.error(f"✗ {e}")

def _run_verification(session):
    """Check all required objects exist."""
    from config import get_app_database, get_app_schema

    db = get_app_database(session)
    schema = get_app_schema(session)
    results = {}

    progress = st.progress(0)
    total = len(REQUIRED_TABLES) + len(REQUIRED_PROCEDURES) + len(REQUIRED_TASKS) + len(REQUIRED_ROLES)
    checked = 0

    # Check tables
    for tbl in REQUIRED_TABLES:
        try:
            session.sql(f"SELECT 1 FROM {db}.{schema}.{tbl} LIMIT 0").collect()
            results[f"TABLE: {tbl}"] = ("✓", "exists")
        except Exception:
            results[f"TABLE: {tbl}"] = ("✗", "missing")
        checked += 1
        progress.progress(checked / total)

    # Check SPs
    for sp in REQUIRED_PROCEDURES:
        try:
            rows = session.sql(f"SHOW PROCEDURES LIKE '{sp}' IN SCHEMA {db}.{schema}").to_pandas()
            if not rows.empty:
                results[f"SP: {sp}"] = ("✓", "exists")
            else:
                results[f"SP: {sp}"] = ("✗", "missing")
        except Exception:
            results[f"SP: {sp}"] = ("✗", "missing")
        checked += 1
        progress.progress(checked / total)

    # Check tasks
    for task in REQUIRED_TASKS:
        try:
            rows = session.sql(f"SHOW TASKS LIKE '{task}' IN SCHEMA {db}.{schema}").to_pandas()
            rows.columns = [c.strip('"').upper() for c in rows.columns]
            if not rows.empty:
                state = rows["STATE"].iloc[0] if "STATE" in rows.columns else "unknown"
                results[f"TASK: {task}"] = ("✓", f"exists ({state})")
            else:
                results[f"TASK: {task}"] = ("✗", "missing")
        except Exception:
            results[f"TASK: {task}"] = ("✗", "missing")
        checked += 1
        progress.progress(checked / total)

    # Check roles
    for role in REQUIRED_ROLES:
        try:
            rows = session.sql(f"SHOW ROLES LIKE '{role}'").to_pandas()
            if not rows.empty:
                results[f"ROLE: {role}"] = ("✓", "exists")
            else:
                results[f"ROLE: {role}"] = ("✗", "missing")
        except Exception:
            results[f"ROLE: {role}"] = ("✗", "missing")
        checked += 1
        progress.progress(checked / total)

    st.session_state["verification_results"] = results


def _display_verification(results):
    """
    Display verification results as colour-coded chips in a 3-column grid.
    Green = exists, Red = missing.
    """
    exists = {k: d for k, (v, d) in results.items() if v == "✓"}
    missing = {k: d for k, (v, d) in results.items() if v == "✗"}

    total = len(results)
    ok_count = len(exists)
    miss_count = len(missing)

    # Summary bar
    if miss_count == 0:
        st.success(f"All {total} objects verified — ready to use.")
    else:
        st.warning(f"{ok_count} of {total} objects exist — **{miss_count} missing**. Run 'Create Missing Objects' to fix.")

    # Build HTML chips
    def chip(label, detail, green: bool) -> str:
        bg     = "#1a4731" if green else "#3d1616"
        color  = "#3fb950" if green else "#f85149"
        icon   = "✓" if green else "✗"
        tip    = f" ({detail})" if detail and detail not in ("exists", "missing") else ""
        return (
            f'<div style="background:{bg};color:{color};border-radius:5px;'
            f'padding:0.35rem 0.6rem;margin:2px 0;font-size:0.78rem;'
            f'font-family:monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
            f'{icon} {label}{tip}</div>'
        )

    # Separate by category
    categories = {"TABLE": [], "SP": [], "TASK": [], "ROLE": []}
    for key, (status, detail) in results.items():
        cat = key.split(":")[0].strip()
        name = key.split(":", 1)[1].strip()
        categories.get(cat, categories["TABLE"]).append((name, detail, status == "✓"))

    col1, col2, col3, col4 = st.columns(4)
    for col, (cat, items) in zip([col1, col2, col3, col4], categories.items()):
        with col:
            st.caption(f"**{cat}S** ({sum(1 for _,_,ok in items if ok)}/{len(items)})")
            html = "".join(chip(name, detail, ok) for name, detail, ok in items)
            st.markdown(html, unsafe_allow_html=True)


def _split_sql_statements(sql: str) -> list:
    """
    Split SQL content into executable statements.

    Handles:
    - $$ dollar-quoting (SP bodies) — semicolons inside ignored
    - -- single-line comments — semicolons inside ignored
    - SET APP_* variable declarations — skipped (SiS doesn't support session vars)
    - USE DATABASE/SCHEMA/WAREHOUSE/ROLE — skipped (context set by session)
    """
    statements = []
    buf = []
    in_dollar_quote = False
    i = 0
    n = len(sql)

    while i < n:
        # Detect $$ delimiter (toggle dollar-quote state)
        if sql[i:i + 2] == '$$':
            in_dollar_quote = not in_dollar_quote
            buf.append('$$')
            i += 2
            continue

        # Single-line comment: skip everything to end of line
        if sql[i:i + 2] == '--' and not in_dollar_quote:
            # Consume to end of line (don't split on any `;` in this comment)
            while i < n and sql[i] != '\n':
                i += 1
            continue  # don't add comment text to buf

        # Semicolon outside a $$ block = statement boundary
        if sql[i] == ';' and not in_dollar_quote:
            stmt = ''.join(buf).strip()
            if stmt and len(stmt) > 8:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(sql[i])
        i += 1

    # Trailing content without terminating semicolon
    remaining = ''.join(buf).strip()
    if remaining and len(remaining) > 8:
        statements.append(remaining)

    return statements


def _run_setup(session):
    """Create all missing objects by running DDL statements."""
    from config import get_app_database, get_app_schema

    db = get_app_database(session)
    schema = get_app_schema(session)
    warehouse = "COMPUTE_WH"

    try:
        wh_rows = session.sql("SELECT CURRENT_WAREHOUSE()").collect()
        if wh_rows:
            warehouse = str(wh_rows[0][0])
    except Exception:
        pass

    # ---- Step A: Run prerequisites.sql (tables, roles, tasks, core SPs) ----
    import pathlib
    # Try app root (pages/setup.py → parent → pages/ → parent → app root)
    # Also try same directory and one level up as fallbacks
    here = pathlib.Path(__file__).resolve().parent
    candidates = [
        here.parent / "prerequisites.sql",   # app root (primary)
        here / "prerequisites.sql",           # same dir
        pathlib.Path("prerequisites.sql"),    # CWD
    ]
    sql_file = next((p for p in candidates if p.exists()), None)

    if sql_file is None:
        st.error(
            "prerequisites.sql not found. "
            "Ensure it is listed in `artifacts` in `snowflake.yml` and re-deploy."
        )
        st.caption(f"Searched: {[str(p) for p in candidates]}")
        return

    sql_content = sql_file.read_text(encoding="utf-8")

    # --- Substitute deployment-target placeholders ---
    # prerequisites.sql uses __DB__, __SCHEMA__, __WH__ for all references.
    # Replace compound first (__DB__.__SCHEMA__) before simple (__DB__) to
    # avoid partial substitution.
    sql_content = sql_content.replace("__DB__.__SCHEMA__", f"{db}.{schema}")
    sql_content = sql_content.replace("__DB__", db)
    sql_content = sql_content.replace("__SCHEMA__", schema)
    sql_content = sql_content.replace("__WH__", warehouse)

    # --- Substitute configurable role names ---
    # Accounts can override these in config.yaml under roles:
    # Defaults are CC_SP_OWNER_ROLE, CC_APP_ROLE, CC_ADMIN_ROLE, CC_USER_ROLE
    sql_content = sql_content.replace("__SP_OWNER_ROLE__", ROLE_SP_OWNER)
    sql_content = sql_content.replace("__APP_ROLE__",      ROLE_APP)
    sql_content = sql_content.replace("__ADMIN_ROLE__",    ROLE_ADMIN)
    sql_content = sql_content.replace("__USER_ROLE__",     ROLE_USER)

    # Use the SP-aware splitter instead of naive split(";")
    raw_statements = _split_sql_statements(sql_content)

    # Filter statements that can't run in SiS owner-rights context:
    # - USE DATABASE/SCHEMA/WAREHOUSE/ROLE  → session context already set
    # - SET APP_* variables                 → SiS doesn't support session variables
    # - SHOW * (verification queries)       → not needed at setup time
    _SKIP_PREFIXES = ("USE DATABASE", "USE SCHEMA", "USE WAREHOUSE", "USE ROLE",
                      "SET APP_", "SHOW TABLES", "SHOW PROCEDURES", "SHOW TASKS",
                      "SHOW GRANTS", "SHOW ROLES", "SHOW WAREHOUSES")

    statements = [
        s for s in raw_statements
        if not s.strip().upper().startswith(_SKIP_PREFIXES)
    ]
    skipped = len(raw_statements) - len(statements)

    # Detect managed schema — GRANT OWNERSHIP fails in managed schemas
    # (managed schemas restrict ownership transfer to schema owner only)
    is_managed = False
    try:
        rows = session.sql(
            f"SHOW SCHEMAS LIKE '{schema}' IN DATABASE {db}"
        ).to_pandas()
        if not rows.empty:
            rows.columns = [c.strip('"').upper() for c in rows.columns]
            if "IS_MANAGED_ACCESS" in rows.columns:
                is_managed = str(rows["IS_MANAGED_ACCESS"].iloc[0]).upper() in ("Y", "YES", "TRUE", "1")
    except Exception:
        pass

    if is_managed:
        st.caption(f"Managed schema detected — GRANT OWNERSHIP steps will be skipped (not required for app function).")

    progress = st.progress(0)
    successes, failures, failed_list = 0, 0, []
    status_ph = st.empty()
    total = len(statements)

    for i, stmt in enumerate(statements):
        # Skip GRANT OWNERSHIP in managed schemas — ownership transfer is blocked
        # by the managed schema policy. The app works without it.
        stmt_upper = stmt.strip().upper()
        if is_managed and stmt_upper.startswith("GRANT OWNERSHIP ON"):
            skipped += 1
            progress.progress(min((i + 1) / max(total, 1), 1.0))
            continue

        try:
            session.sql(stmt).collect()
            successes += 1
        except Exception as e:
            err = str(e)
            # Silently skip: object already exists, managed schema restriction
            _ignorable = (
                "already exists",
                "managed access schema",
                "insufficient privileges to transfer ownership",
            )
            if any(ig in err.lower() for ig in _ignorable):
                successes += 1   # treat as success — object is there
            else:
                failures += 1
                failed_list.append(f"{stmt[:60]}... → {err[:100]}")
        progress.progress(min((i + 1) / max(total, 1), 1.0))
        status_ph.caption(f"prerequisites.sql: statement {i + 1}/{total} ({skipped} skipped)...")

    status_ph.empty()

    # ---- Step B: Create bulk SPs + rebalance SP from sp_definitions.py ----
    st.caption("Creating bulk operation and rebalance SPs...")
    from sp_definitions import get_bulk_sp_ddl, get_rebalance_sp_ddl
    bulk_ddls = get_bulk_sp_ddl(db, schema) + [get_rebalance_sp_ddl(db, schema)]
    bulk_ok, bulk_fail = 0, 0

    for ddl in bulk_ddls:
        try:
            session.sql(ddl).collect()
            bulk_ok += 1
        except Exception as e:
            bulk_fail += 1
            failed_list.append(f"Bulk SP: {str(e)[:120]}")

    total_success = successes + bulk_ok
    total_fail = failures + bulk_fail

    with st.expander(
        f"Setup complete — {total_success} succeeded, {total_fail} failed",
        expanded=(total_fail > 0),
    ):
        if failed_list:
            for f in failed_list[:20]:
                st.text(f"✗ {f}")
        else:
            st.caption("All statements executed successfully.")

    if total_fail == 0:
        st.success("✓ Setup complete. Run verification to confirm all objects exist.")
        log_activity(session, "SETUP_COMPLETE",
                     details={"db": db, "schema": schema,
                              "statements": total_success})
    else:
        st.warning(f"Setup completed with {total_fail} errors. Check details above.")


def _grant_roles_to_current_user(session):
    """Grant the configured admin and user roles to the current user."""
    from config import sql_identifier
    try:
        current_user = session.sql("SELECT CURRENT_USER()").collect()[0][0]
        uid = sql_identifier(current_user)
        session.sql(f'GRANT ROLE {ROLE_ADMIN} TO USER {uid}').collect()
        session.sql(f'GRANT ROLE {ROLE_USER}  TO USER {uid}').collect()
        st.success(f"✓ Granted {ROLE_ADMIN} + {ROLE_USER} to {current_user}")
    except Exception as e:
        st.error(f"✗ {e}")


def _seed_defaults(session):
    """Seed CC_APP_CONFIG with default values."""
    from config import fq_table
    tbl = fq_table(session, "CC_APP_CONFIG")
    defaults = [
        ("APPROVAL_MODE", "ADMIN"),
        ("REBALANCE_BUFFER_PCT", "20"),
        ("REBALANCE_MAX_TRANSFER_PCT", "50"),
        ("REBALANCE_LOOKBACK_DAYS", "14"),
        ("DAILY_RESET_ENABLED", "TRUE"),
        ("MAX_REQUESTS_PER_USER_PER_DAY", "2"),
        ("REQUEST_COOLDOWN_MINUTES", "60"),
        ("MAX_EXTRA_CREDITS_PER_WEEK", "20"),
        ("DONOR_STRATEGY", "WEIGHTED_RANDOM"),
        ("DONOR_PROTECTION_HOURS", "4"),
    ]
    try:
        values = ", ".join([f"('{k}', '{v}', 'SYSTEM')" for k, v in defaults])
        session.sql(f"""
            MERGE INTO {tbl} t
            USING (SELECT * FROM VALUES {values} AS v(K, V, U)) s ON t.CONFIG_KEY = s.K
            WHEN NOT MATCHED THEN INSERT (CONFIG_KEY, CONFIG_VALUE, UPDATED_BY) VALUES (s.K, s.V, s.U)
        """).collect()
        st.success(f"✓ Seeded {len(defaults)} default settings.")
    except Exception as e:
        st.error(f"✗ {e}")

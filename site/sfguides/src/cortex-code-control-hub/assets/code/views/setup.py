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
    "CC_COHORT_REBALANCE_LOCK",
    # Responsible AI governance tables
    "CC_POLICY_RULES",
    "CC_PROMPT_VIOLATIONS",
    "CC_PROMPT_ANALYSIS_DAILY",
    "CC_PROMPT_EVENTS",
    # Alerting tables
    "CC_ALERT_CONFIG",
    "CC_ALERT_HISTORY",
    # Response quality scoring
    "CC_RESPONSE_QUALITY",
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
    # Bulk operation SPs
    "SP_CC_BULK_GRANT_ACCESS",
    "SP_CC_BULK_SET_COHORT_LIMITS",
    # Bridge rebalance SP
    "SP_CC_COMPUTE_REBALANCE",
    # Responsible AI classification SP
    "SP_CC_CLASSIFY_PROMPTS",
    # Alerting + quality SPs
    "SP_CC_CHECK_ALERTS",
    "SP_CC_EVALUATE_RESPONSES",
]

REQUIRED_TASKS = [
    "CC_REFRESH_USAGE_SUMMARIES",
    "CC_DAILY_RESET_LIMITS",
    "CC_CLASSIFY_PROMPTS_TASK",
    "CC_ALERT_CHECK",
    "CC_REALTIME_VIOLATION_ALERT",
]

REQUIRED_INTEGRATIONS = [
    "CC_EMAIL_INTEGRATION",
]

REQUIRED_STREAMS = [
    "CC_VIOLATION_STREAM",
]

REQUIRED_STAGES = []  # Stage is auto-managed by snow streamlit deploy — not a prereq check

REQUIRED_ROLES = [
    ROLE_SP_OWNER,
    ROLE_APP,
    ROLE_ADMIN,
    ROLE_USER,
]


def render(session):
    import time
    from config import fq_sp, KNOWN_MODELS

    st.header("Setup", help="One-time installation and data bootstrap for CoCo Control Hub.")
    st.caption("Run each phase in order on first install. All phases are idempotent — safe to re-run.")

    current_role = get_current_role(session)
    is_accountadmin = "ACCOUNTADMIN" in current_role.upper()

    if is_accountadmin:
        st.success(f"Role: **{current_role}** — full setup access available.")
    else:
        st.warning(f"Role: **{current_role}** — some steps (ALTER USER, GRANT) require ACCOUNTADMIN.")

    with st.expander("How owner's rights execution works", expanded=False):
        st.markdown("""
All SQL runs as the role that **owns this Streamlit**, not your login role.
`CC_SP_OWNER_ROLE` owns all SPs and can `ALTER USER` / `GRANT` without end-users needing elevated access.

```sql
-- Verify ownership:
SHOW STREAMLITS IN SCHEMA <db>.<schema>;
-- Transfer if needed:
GRANT OWNERSHIP ON STREAMLIT <db>.<schema>.<name> TO ROLE ACCOUNTADMIN;
```
        """)

    st.divider()

    # ── Account Prerequisites ───────────────────────────────────────────────────
    with st.expander("⚡ Account Prerequisites — ACCOUNTADMIN or Custom Admin", expanded=False):
        st.caption(
            "One-time account configuration needed before CoCo can track credits and AI activity. "
            "Some steps require ACCOUNTADMIN; others can be done by a custom admin role with the right grants."
        )

        # Two-column role path selector (informational only)
        col_aa, col_ca = st.columns(2)
        with col_aa:
            st.markdown("""
**🔐 ACCOUNTADMIN path**

You have full account admin. Run all 5 steps below directly.
All steps are available to you.
            """)
        with col_ca:
            st.markdown(f"""
**🛠 Custom Admin path**

You have a custom role (e.g. `SYSADMIN`, `DBA_ROLE`).
Steps 1, 3, 5 require a one-time assist from ACCOUNTADMIN.
Steps 2, 4 and all Phase A–E DDL you can run yourself.

→ Expand *"Custom Admin Role Setup"* below for the exact grants.
            """)
        st.divider()

        # Try to check current state (best-effort — may fail on lower privileges)
        prereq_status = {}
        try:
            rows = session.sql("SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT").collect()
            if rows:
                val = str(rows[0]["value"]).upper().strip()
                if val in ("ANY", "ANY_REGION", "AWS_US", "AWS_GLOBAL"):
                    prereq_status["cross_region"] = True
                elif val in ("", "DISABLED", "NONE"):
                    prereq_status["cross_region"] = None   # not configured — amber, not red
                else:
                    prereq_status["cross_region"] = False  # explicitly wrong value
            else:
                prereq_status["cross_region"] = None
        except Exception:
            prereq_status["cross_region"] = None

        try:
            from config import get_app_database, get_app_schema
            sp_role = ROLE_SP_OWNER
            grant_rows = session.sql(f"SHOW GRANTS TO ROLE {sp_role}").collect()
            granted_privs = {f"{str(r.get('privilege',''))}::{str(r.get('granted_on',''))}::{str(r.get('name',''))}".upper()
                             for r in grant_rows}
            # confirmed not granted = None (amber) not False (red) — these are setup tasks not failures
            prereq_status["observability"] = True if any("AI_OBSERVABILITY_READER" in g for g in granted_privs) else None
            prereq_status["account_usage"] = True if any("IMPORTED PRIVILEGES" in g and "SNOWFLAKE" in g for g in granted_privs) else None
            prereq_status["cortex_user"]   = True if any("CORTEX_USER" in g for g in granted_privs) else None
        except Exception:
            prereq_status["observability"]  = None
            prereq_status["account_usage"]  = None
            prereq_status["cortex_user"]    = None

        def _status_chip(val, label):
            if val is True:
                return f'<span style="background:#1a4731;color:#3fb950;border-radius:4px;padding:2px 8px;font-size:0.78rem;font-family:monospace;">✓ {label}</span>'
            elif val is False:
                # Only used when a value is explicitly wrong (not just unset)
                return f'<span style="background:#3d1616;color:#f85149;border-radius:4px;padding:2px 8px;font-size:0.78rem;font-family:monospace;">✗ {label}</span>'
            else:
                # None = not yet configured or unknown — amber, not red
                return f'<span style="background:#2a2a1a;color:#d4a017;border-radius:4px;padding:2px 8px;font-size:0.78rem;font-family:monospace;">⚠ {label}</span>'

        chips_html = " &nbsp; ".join([
            _status_chip(prereq_status["cross_region"],   "Cross-Region Inference"),
            _status_chip(prereq_status["observability"],  "AI Observability Access"),
            _status_chip(prereq_status["account_usage"],  "ACCOUNT_USAGE Access"),
            _status_chip(prereq_status["cortex_user"],    "CORTEX_USER Role"),
        ])
        st.markdown(chips_html + "<br/>", unsafe_allow_html=True)

        st.divider()

        # ── 1. Cross-Region Inference ─────────────────────────────────────────
        st.markdown("#### 1 · Cross-Region Inference &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            "Cortex Code and Cortex LLM models (claude-sonnet, GPT, llama, etc.) may not be "
            "available natively in your account's home region. This parameter allows Snowflake "
            "to route inference requests to the nearest region where the model is available — "
            "required for most non-US accounts and for newer models everywhere."
        )
        st.code("ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY';", language="sql")

        st.divider()

        # ── 2. AI Observability Access ────────────────────────────────────────
        st.markdown("#### 2 · AI Observability Access &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            f"`SP_CC_CLASSIFY_PROMPTS` reads `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` to backfill "
            f"prompt events, token economics, and latency data. The SP runs as `{ROLE_SP_OWNER}` "
            f"(owner's rights) — that role needs the `AI_OBSERVABILITY_READER` database role to access the view."
        )
        st.code(f"""\
-- Grant AI Observability read access to the CoCo SP owner role
GRANT DATABASE ROLE SNOWFLAKE.AI_OBSERVABILITY_READER
  TO ROLE {ROLE_SP_OWNER};""", language="sql")

        st.divider()

        # ── 3. ACCOUNT_USAGE Access (Credits) ────────────────────────────────
        st.markdown("#### 3 · ACCOUNT_USAGE Access — Credits & Usage Data &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            f"`SP_CC_REFRESH_USAGE_SUMMARIES` reads credit and model usage data from "
            f"`SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` and `METERING_HISTORY`. "
            f"`{ROLE_SP_OWNER}` needs `IMPORTED PRIVILEGES` on the `SNOWFLAKE` database to access these views."
        )
        st.code(f"""\
-- Grant ACCOUNT_USAGE read access to the CoCo SP owner role
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE
  TO ROLE {ROLE_SP_OWNER};""", language="sql")

        st.divider()

        # ── 4. Model Access for Users ─────────────────────────────────────────
        st.markdown("#### 4 · Model Access for Users &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            f"Users need two things to call Cortex AI functions (AI_COMPLETE, AI_CLASSIFY, etc.): "
            f"the `CORTEX_USER` database role **and** the `USE AI FUNCTIONS` account privilege. "
            f"Grant both to `{ROLE_USER}` so all CoCo users can interact with models. "
            f"To restrict specific models per role, use `CORTEX_MODELS_ALLOWLIST = 'None'` + model RBAC "
            f"(see Model Access page for per-role model grants)."
        )
        st.code(f"""\
-- Step 1: Grant Cortex model access to CoCo user role
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER
  TO ROLE {ROLE_USER};

-- Step 2: Grant AI function execution privilege
GRANT USE AI FUNCTIONS ON ACCOUNT
  TO ROLE {ROLE_USER};

-- Optional: restrict models account-wide, then grant specific models per role
-- ALTER ACCOUNT SET CORTEX_MODELS_ALLOWLIST = 'None';
-- GRANT APPLICATION ROLE SNOWFLAKE."CORTEX-MODEL-ROLE-CLAUDE-SONNET-4-5" TO ROLE {ROLE_USER};""",
        language="sql")

        st.divider()

        # ── 5. Cortex Code Credit Limits (Optional) ───────────────────────────
        st.markdown("#### 5 · Cortex Code Native Credit Limits _(optional)_ &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            "Set per-user or account-wide Cortex Code credit budgets. These are enforced natively "
            "by Snowflake — separate from CoCo's own credit management tables. "
            "CoCo's credit tracking in CC_USAGE_DAILY_SUMMARY is a governance layer on top of these."
        )
        st.code("""\
-- Account-wide monthly credit limit for Cortex Code
ALTER ACCOUNT SET CORTEX_CODE_CREDIT_LIMIT = 1000;

-- Per-user monthly limit
ALTER USER <username> SET CORTEX_CODE_CREDIT_LIMIT = 50;

-- Check current limits
SHOW PARAMETERS LIKE 'CORTEX_CODE_CREDIT_LIMIT' IN ACCOUNT;""", language="sql")

        st.divider()

        # ── 6. Cortex AI Guardrails ───────────────────────────────────────────
        st.markdown("#### 6 · Cortex AI Guardrails _(Enterprise Edition)_ &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            "Provides runtime protection against **prompt injection** and **jailbreak attacks** on Cortex Code, "
            "Cortex Agents, and Snowflake Intelligence. Part of Snowflake Horizon Catalog. "
            "Requires Enterprise Edition and cross-region inference (step 1) to be enabled first. "
            "Billed per token scanned — see Snowflake Service Consumption Table."
        )
        st.code("""\
-- Enable Cortex AI Guardrails (prompt injection + jailbreak protection)
ALTER ACCOUNT SET AI_SETTINGS = $$
  guardrails:
    advanced_prompt_injection:
      - enabled: true
$$;

-- Verify
SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT;

-- Disable if needed
ALTER ACCOUNT UNSET AI_SETTINGS;""", language="sql")

        st.divider()

        # ── 7. Native AI Budgets ──────────────────────────────────────────────
        st.markdown("#### 7 · Native AI Budgets _(Snowflake Preview — optional)_ &nbsp; `🔐 ACCOUNTADMIN only`")
        st.caption(
            "Snowflake's tag-based budget enforcement for **Cortex Agent objects**. "
            "Complements CoCo's per-user credit governance with a **hard platform-level stop** — "
            "automated REVOKE USAGE when monthly spend hits 100%. Preview feature, Enterprise Edition. "
            "See **Credit Configuration → Native AI Budgets** for full setup SQL and comparison with CoCo's approach."
        )
        st.code("""\
-- Quick-start: tag agent → create budget → set limit → notify at 80%
CREATE TAG my_db.tags.cost_center ALLOWED_VALUES 'cortex-code-agent';
ALTER AGENT IF EXISTS my_agent SET TAG my_db.tags.cost_center = 'cortex-code-agent';

USE SCHEMA budgets_db.budgets_schema;
CREATE SNOWFLAKE.CORE.BUDGET ai_agent_budget();
CALL ai_agent_budget!SET_SPENDING_LIMIT(1000);  -- monthly credit cap
CALL ai_agent_budget!SET_NOTIFICATION_THRESHOLD(80);
-- Full setup with revoke-at-100% SP:
-- https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-resource-budgets""",
        language="sql")

        st.divider()

        # ── Custom Admin Role Setup ───────────────────────────────────────────
        with st.expander("🛠 Custom Admin Role Setup — delegate setup to a non-ACCOUNTADMIN role", expanded=False):
            st.caption(
                "If your organisation policy restricts ACCOUNTADMIN usage, run the block below once "
                "as ACCOUNTADMIN to elevate a custom role. That role can then self-serve all of "
                "Phase A–E (create tables, SPs, tasks) without further ACCOUNTADMIN involvement. "
                "Steps 1, 2, 3, 4 above must still be executed by ACCOUNTADMIN once — they grant "
                "access to Snowflake-owned objects that cannot be delegated."
            )
            st.code(f"""\
-- ─────────────────────────────────────────────────────────────
-- Run ONCE as ACCOUNTADMIN to bootstrap a custom admin role
-- Replace MY_CUSTOM_ADMIN_ROLE / MY_DB / MY_SCHEMA / MY_WH
-- ─────────────────────────────────────────────────────────────

USE ROLE ACCOUNTADMIN;

-- 1. Grant database and schema creation rights (if DB/schema don't exist yet)
GRANT CREATE DATABASE ON ACCOUNT          TO ROLE MY_CUSTOM_ADMIN_ROLE;
-- OR if the database already exists:
GRANT CREATE SCHEMA   ON DATABASE MY_DB   TO ROLE MY_CUSTOM_ADMIN_ROLE;

-- 2. Grant object creation in the target schema
GRANT CREATE TABLE          ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE VIEW           ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE PROCEDURE      ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE TASK           ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE STREAM         ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE ALERT          ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE STAGE          ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT CREATE STREAMLIT      ON SCHEMA MY_DB.MY_SCHEMA TO ROLE MY_CUSTOM_ADMIN_ROLE;

-- 3. Grant warehouse usage
GRANT USAGE, OPERATE ON WAREHOUSE MY_WH TO ROLE MY_CUSTOM_ADMIN_ROLE;

-- 4. Allow custom admin to grant CoCo roles to other users
GRANT ROLE {ROLE_SP_OWNER} TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT ROLE {ROLE_APP}      TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT ROLE {ROLE_ADMIN}    TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT ROLE {ROLE_USER}     TO ROLE MY_CUSTOM_ADMIN_ROLE;

-- 5. Allow custom admin to execute tasks (needed for Phase A scheduled tasks)
GRANT EXECUTE TASK   ON ACCOUNT TO ROLE MY_CUSTOM_ADMIN_ROLE;
GRANT EXECUTE ALERT  ON ACCOUNT TO ROLE MY_CUSTOM_ADMIN_ROLE;

-- 6. Allow the Streamlit to run as owner's rights under custom role
GRANT OWNERSHIP ON STREAMLIT MY_DB.MY_SCHEMA.CORTEX_CODE_CREDIT_MANAGER
  TO ROLE MY_CUSTOM_ADMIN_ROLE COPY CURRENT GRANTS;

-- ─────────────────────────────────────────────────────────────
-- Steps below still require ACCOUNTADMIN — run them separately
-- ─────────────────────────────────────────────────────────────
-- ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY';
-- GRANT DATABASE ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE {ROLE_SP_OWNER};
-- GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE {ROLE_SP_OWNER};
-- GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE {ROLE_USER};
-- GRANT USE AI FUNCTIONS ON ACCOUNT TO ROLE {ROLE_USER};
-- CREATE NOTIFICATION INTEGRATION CC_EMAIL_INTEGRATION ...;""", language="sql")

    # ── Phase A: Create Objects ─────────────────────────────────────────────────
    with st.expander("Phase A — Create Objects", expanded=True):
        st.caption("Runs prerequisites.sql — creates all roles, tables, tasks, stream, alerts, and notification integration. Safe to re-run (IF NOT EXISTS / CREATE OR REPLACE).")
        with st.expander("What gets created", expanded=False):
            st.markdown("""
- **4 roles**: CC_SP_OWNER_ROLE, CC_APP_ROLE, CC_ADMIN_ROLE, CC_USER_ROLE
- **20+ tables**: credit config, usage summaries, prompt events, insights, quality scores, alert config/history, policy rules, model config, cohort mapping, audit log
- **2 scheduled tasks**: 30-min usage refresh, nightly classify (suspended — resume after Phase C)
- **1 stream**: CC_VIOLATION_STREAM (real-time high-severity detection)
- **2 alerts**: CC_ALERT_CHECK (5-min batch), CC_REALTIME_VIOLATION_ALERT (1-min)
- **1 notification integration**: CC_EMAIL_INTEGRATION
- **8 default policy rules** seeded via MERGE (PII, Security, Prompt Injection, Data Exfiltration, Competitor, Personal Use, Session Anomaly, Semantic Injection)
            """)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run Phase A — Create Objects", type="primary", key="btn_setup_a",
                         help="Runs prerequisites.sql. Safe to re-run."):
                _run_setup(session)
        with col2:
            if st.button("Grant App Roles to Me", key="btn_grants_a",
                         help="Grants CC_ADMIN_ROLE + CC_USER_ROLE to your user so you can use the app."):
                _grant_roles_to_current_user(session)

    # ── Phase B: Seed Defaults ──────────────────────────────────────────────────
    with st.expander("Phase B — Seed Defaults", expanded=False):
        st.caption("Populates CC_APP_CONFIG with 15+ default settings: credit limits, model tiers, alert config, evaluation settings, backfill period, and pricing.")
        if st.button("Run Phase B — Seed Defaults", type="primary", key="btn_seed_b",
                     help="Inserts default settings into CC_APP_CONFIG. Safe to re-run — uses INSERT WHERE NOT EXISTS."):
            _seed_defaults(session)

    # ── Phase C: Create Stored Procedures ──────────────────────────────────────
    with st.expander("Phase C — Create Stored Procedures", expanded=False):
        st.caption("Creates 3 stored procedures via `sp_definitions.py`. "
                   "`SP_CC_REFRESH_USAGE_SUMMARIES` is created by Phase A (from `prerequisites.sql`).")
        st.markdown("""
| SP | Created by | Purpose |
|---|---|---|
| `SP_CC_REFRESH_USAGE_SUMMARIES` | **Phase A** | Incremental usage/credit aggregation from ACCOUNT_USAGE |
| `SP_CC_CLASSIFY_PROMPTS` | **Phase C** | SQL KEYWORD + REGEX + SEMANTIC classification, categories, cost |
| `SP_CC_CHECK_ALERTS` | **Phase C** | Batch + real-time alert evaluation with HTML email |
| `SP_CC_EVALUATE_RESPONSES` | **Phase C** | LLM-as-Judge: Answer Relevance, Groundedness, Coherence, Safety |
        """)
        if st.button("Run Phase C — Create Stored Procedures", type="primary", key="btn_sps_c",
                     help="Creates 3 SPs (SP_CC_REFRESH_USAGE_SUMMARIES is already created by Phase A). Uses CREATE OR REPLACE — safe to re-run."):
            from sp_definitions import (
                get_classify_sp_ddl,
                get_check_alerts_sp_ddl,
                get_evaluate_responses_sp_ddl,
            )
            from config import get_app_database, get_app_schema
            db = get_app_database(session)
            schema = get_app_schema(session)
            sp_results = []
            for sp_name, get_ddl_fn in [
                ("SP_CC_CLASSIFY_PROMPTS",        lambda: get_classify_sp_ddl(db, schema)),
                ("SP_CC_CHECK_ALERTS",             lambda: get_check_alerts_sp_ddl(db, schema)),
                ("SP_CC_EVALUATE_RESPONSES",       lambda: get_evaluate_responses_sp_ddl(db, schema)),
            ]:
                try:
                    ddl = get_ddl_fn()
                    session.sql(ddl).collect()
                    sp_results.append((sp_name, True, None))
                except Exception as e:
                    sp_results.append((sp_name, False, str(e)[:120]))
            # Also create SP_CC_REFRESH_USAGE_SUMMARIES from _run_setup step B
            for name, ok, err in sp_results:
                if ok:
                    st.success(f"✓ {name}")
                else:
                    st.error(f"✗ {name}: {err}")

    # ── Phase D: Initial Data Load ──────────────────────────────────────────────
    with st.expander("Phase D — Initial Data Load", expanded=False):
        st.caption("Run each component independently. All SPs use watermark logic — safe to re-run, only fetches new data.")

        # ── D1: Usage Summaries ───────────────────────────────────────────────
        st.markdown("#### D1 — Credit & Usage History")
        st.caption("Backfills CC_USAGE_DAILY_SUMMARY from ACCOUNT_USAGE. Shows credits by user, surface, and model.")
        d1_days = st.selectbox("Backfill period", [7,14,30,60,90,180], index=4,
                               format_func=lambda d: f"{d} days", key="d1_days")
        if st.button("Run D1 — Backfill Usage Summaries", type="primary", key="btn_d1"):
            with st.spinner("Running SP_CC_REFRESH_USAGE_SUMMARIES…"):
                try:
                    r = session.sql(f"CALL {fq_sp(session,'SP_CC_REFRESH_USAGE_SUMMARIES')}()").collect()
                    st.success(f"✓ {str(r[0][0]) if r else 'OK'}")
                except Exception as e:
                    st.error(f"✗ D1: {e}")

        st.divider()

        # ── D2: Prompt Events + Classification ───────────────────────────────
        st.markdown("#### D2 — Prompt Events, Insights & Prompt Patterns")
        st.caption("Loads CC_PROMPT_EVENTS from AI_OBSERVABILITY_EVENTS, runs policy classification, "
                   "and classifies prompt categories (sql_data_engineering, agent_automation, etc.).")
        d2_days = st.selectbox("Backfill period", [7,14,30,60,90,180], index=4,
                               format_func=lambda d: f"{d} days", key="d2_days")
        if st.button("Run D2 — Backfill Prompt Events", type="primary", key="btn_d2"):
            lookback_h = d2_days * 24
            with st.spinner(f"Running SP_CC_CLASSIFY_PROMPTS({lookback_h}) — may take several minutes…"):
                try:
                    import json as _dj
                    r = session.sql(f"CALL {fq_sp(session,'SP_CC_CLASSIFY_PROMPTS')}({lookback_h})").collect()
                    res = _dj.loads(r[0][0]) if r and isinstance(r[0][0], str) else {}
                    st.success(f"✓ {res.get('events_loaded',0):,} events · "
                               f"{res.get('violations_found',0):,} prompt insights · "
                               f"{res.get('categories_classified',0):,} categories classified")
                    if res.get('errors'):
                        st.warning(f"Non-fatal errors: {res['errors'][:3]}")
                except Exception as e:
                    st.error(f"✗ D2: {e}")

        st.divider()

        # ── D3: Model Config ──────────────────────────────────────────────────
        st.markdown("#### D3 — Model Configuration")
        st.caption("Seeds CC_MODEL_CONFIG with model tier assignments from KNOWN_MODELS. Skipped if already populated.")
        if st.button("Run D3 — Seed Model Config", key="btn_d3"):
            try:
                from config import fq_table
                tbl = fq_table(session, "CC_MODEL_CONFIG")
                cnt = session.sql(f"SELECT COUNT(*) FROM {tbl}").collect()[0][0]
                if int(cnt) == 0:
                    seeded = 0
                    for model_name, info in KNOWN_MODELS.items():
                        category = info['category'][0] if info.get('category') else 'TIER_2'
                        desc = str(info.get('description', '')).replace("'", "''")[:500]
                        safe_name = model_name.replace("'", "''")
                        session.sql(f"""
                            INSERT INTO {tbl} (MODEL_NAME, CATEGORY, DESCRIPTION, CREATED_BY)
                            SELECT '{safe_name}', '{category}', '{desc}', 'SYSTEM'
                            WHERE NOT EXISTS (SELECT 1 FROM {tbl} WHERE MODEL_NAME = '{safe_name}')
                        """).collect()
                        seeded += 1
                    st.success(f"✓ Seeded {seeded} models.")
                else:
                    st.info(f"✓ CC_MODEL_CONFIG already has {int(cnt)} models — skipped.")
            except Exception as e:
                st.error(f"✗ D3: {e}")

        st.divider()

        # ── D4: Quality Evaluation ────────────────────────────────────────────
        st.markdown("#### D4 — LLM-as-Judge Evaluation _(optional — costs Cortex credits)_")
        st.caption("Evaluates AI responses for Answer Relevance, Groundedness, Coherence, Safety. "
                   "Existing scores are preserved — only unevaluated responses are processed.")
        try:
            from config import fq_table
            q_tbl = fq_table(session, "CC_RESPONSE_QUALITY")
            q_cnt = session.sql(f"SELECT COUNT(*) FROM {q_tbl}").collect()[0][0]
            st.caption(f"CC_RESPONSE_QUALITY currently has **{int(q_cnt):,}** evaluated responses.")
        except Exception:
            pass
        d4_batch = st.selectbox("Batch size", [50, 100, 200, 500], index=2,
                                format_func=lambda n: f"{n} responses", key="d4_batch",
                                help="Number of unevaluated responses to score in this run.")
        d4_model = st.selectbox("Judge model", ["llama3.1-70b","claude-sonnet-4-5","llama3.1-8b"], index=0,
                                key="d4_model",
                                help="llama3.1-70b is the Snowflake default — low cost, good quality.")
        if st.button("Run D4 — LLM-as-Judge Evaluation", key="btn_d4"):
            safe_model = d4_model.replace("'", "''")
            with st.spinner(f"Evaluating {d4_batch} responses with {d4_model}…"):
                try:
                    import json as _ej
                    r = session.sql(f"CALL {fq_sp(session,'SP_CC_EVALUATE_RESPONSES')}({d4_batch}, '{safe_model}')").collect()
                    res = _ej.loads(r[0][0]) if r and isinstance(r[0][0], str) else {}
                    st.success(f"✓ {res.get('evaluated',0)} responses evaluated. "
                               "Results visible in Model Intelligence → LLM-as-Judge Evaluation.")
                except Exception as e:
                    st.error(f"✗ D4: {e}")

    # ── Phase E: Verify ─────────────────────────────────────────────────────────
    with st.expander("Phase E — Verify Installation", expanded=False):
        st.caption("Checks that all required objects exist. Run after Phase A + C to confirm successful installation.")
        if st.button("Run Phase E — Verify", type="primary", key="btn_verify_e",
                     help="Runs 7 batched queries to check tables, SPs, tasks, roles, integrations, streams, and stages."):
            _run_verification(session)

        if "verification_results" in st.session_state:
            _display_verification(st.session_state["verification_results"])


def _run_verification(session):
    """Check all required objects exist — batched for speed (7 queries total)."""
    from config import get_app_database, get_app_schema

    db = get_app_database(session)
    schema = get_app_schema(session)
    results = {}
    progress = st.progress(0)

    # ── 1. Tables — one INFORMATION_SCHEMA query ──────────────────────────────
    try:
        existing_tables = set()
        rows = session.sql(f"""
            SELECT TABLE_NAME FROM {db}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = UPPER('{schema}')
        """).collect()
        existing_tables = {r[0].upper() for r in rows}
    except Exception:
        existing_tables = set()
    for tbl in REQUIRED_TABLES:
        results[f"TABLE: {tbl}"] = ("✓", "exists") if tbl.upper() in existing_tables else ("✗", "missing")
    progress.progress(1/7)

    # ── 2. SPs — single SHOW PROCEDURES IN SCHEMA ────────────────────────────
    try:
        existing_sps = set()
        rows = session.sql(f"SHOW PROCEDURES LIKE 'SP_CC_%' IN SCHEMA {db}.{schema}").collect()
        existing_sps = {str(r["name"]).upper() for r in rows}
    except Exception:
        existing_sps = set()
    for sp in REQUIRED_PROCEDURES:
        results[f"SP: {sp}"] = ("✓", "exists") if sp.upper() in existing_sps else ("✗", "missing")
    progress.progress(2/7)

    # ── 3. Tasks — single SHOW TASKS IN SCHEMA ───────────────────────────────
    try:
        existing_tasks = {}
        rows = session.sql(f"SHOW TASKS LIKE 'CC_%' IN SCHEMA {db}.{schema}").collect()
        for r in rows:
            try:
                existing_tasks[str(r["name"]).upper()] = str(r["state"])
            except Exception:
                existing_tasks[str(r[1]).upper()] = "unknown"
    except Exception:
        existing_tasks = {}
    # Also check alerts as tasks (scoped to schema — IN ACCOUNT is very slow on large accounts)
    try:
        alert_rows = session.sql(f"SHOW ALERTS LIKE 'CC_%' IN SCHEMA {db}.{schema}").collect()
        for r in alert_rows:
            try:
                existing_tasks[str(r["name"]).upper()] = str(r["state"])
            except Exception:
                pass
    except Exception:
        pass
    for task in REQUIRED_TASKS:
        if task.upper() in existing_tasks:
            state = existing_tasks[task.upper()]
            results[f"TASK: {task}"] = ("✓", f"exists ({state})")
        else:
            results[f"TASK: {task}"] = ("✗", "missing")
    progress.progress(3/7)

    # ── 4. Roles — single SHOW ROLES ─────────────────────────────────────────
    try:
        existing_roles = set()
        rows = session.sql("SHOW ROLES LIKE 'CC_%'").collect()
        existing_roles = {str(r["name"]).upper() for r in rows}
    except Exception:
        existing_roles = set()
    for role in REQUIRED_ROLES:
        results[f"ROLE: {role}"] = ("✓", "exists") if role.upper() in existing_roles else ("✗", "missing")
    progress.progress(4/7)

    # ── 5. Integrations — single SHOW INTEGRATIONS ───────────────────────────
    try:
        existing_intgs = set()
        rows = session.sql("SHOW INTEGRATIONS LIKE 'CC_%'").collect()
        existing_intgs = {str(r["name"]).upper() for r in rows}
    except Exception:
        existing_intgs = set()
    for intg in REQUIRED_INTEGRATIONS:
        results[f"INTEGRATION: {intg}"] = ("✓", "exists") if intg.upper() in existing_intgs else ("✗", "missing")
    progress.progress(5/7)

    # ── 6. Streams — single SHOW STREAMS IN SCHEMA ───────────────────────────
    try:
        existing_streams = set()
        rows = session.sql(f"SHOW STREAMS LIKE 'CC_%' IN SCHEMA {db}.{schema}").collect()
        existing_streams = {str(r["name"]).upper() for r in rows}
    except Exception:
        existing_streams = set()
    for stream in REQUIRED_STREAMS:
        results[f"STREAM: {stream}"] = ("✓", "exists") if stream.upper() in existing_streams else ("✗", "missing")
    progress.progress(6/7)

    # ── 7. Stages — single SHOW STAGES IN SCHEMA ────────────────────────────
    try:
        existing_stages = set()
        rows = session.sql(f"SHOW STAGES LIKE '%' IN SCHEMA {db}.{schema}").collect()
        existing_stages = {str(r["name"]).upper() for r in rows}
    except Exception:
        existing_stages = set()
    for stage in REQUIRED_STAGES:
        results[f"STAGE: {stage}"] = ("✓", "exists") if stage.upper() in existing_stages else ("✗", "missing")
    progress.progress(7/7)

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
    categories = {"TABLE": [], "SP": [], "TASK": [], "ROLE": [],
                  "INTEGRATION": [], "STREAM": [], "STAGE": []}
    for key, (status, detail) in results.items():
        cat = key.split(":")[0].strip()
        name = key.split(":", 1)[1].strip()
        categories.get(cat, categories["TABLE"]).append((name, detail, status == "✓"))

    # Render in rows of 4 columns max
    cats = [(cat, items) for cat, items in categories.items() if items]
    for row_start in range(0, len(cats), 4):
        row_cats = cats[row_start:row_start+4]
        cols = st.columns(len(row_cats))
        for col, (cat, items) in zip(cols, row_cats):
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

    # Grant USAGE on SP_CC_ENFORCE_MODEL_ACCESS to app role
    # (stays ACCOUNTADMIN-owned — GRANT APPLICATION ROLE requires ACCOUNTADMIN)
    try:
        from config import sql_identifier
        app_role = sql_identifier(ROLE_APP)
        session.sql(
            f"GRANT USAGE ON PROCEDURE {db}.{schema}.SP_CC_ENFORCE_MODEL_ACCESS(VARIANT, VARCHAR)"
            f" TO ROLE {app_role}"
        ).collect()
    except Exception:
        pass  # non-fatal — may already exist

    # ---- Step C: Create SP_CC_CLASSIFY_PROMPTS (ACCOUNTADMIN-owned) -----------
    # This SP is EXECUTE AS OWNER (ACCOUNTADMIN) because it reads
    # SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS which requires AI_OBSERVABILITY_READER.
    st.caption("Creating SP_CC_CLASSIFY_PROMPTS (responsible AI classification)...")
    try:
        from sp_definitions import get_classify_sp_ddl
        session.sql(get_classify_sp_ddl(db, schema)).collect()
        bulk_ok += 1
    except Exception as e:
        bulk_fail += 1
        failed_list.append(f"SP_CC_CLASSIFY_PROMPTS: {str(e)[:120]}")

    # ---- Step D: Create alerting + quality evaluation SPs ----------------------
    st.caption("Creating SP_CC_CHECK_ALERTS (alerting)...")
    try:
        from sp_definitions import get_check_alerts_sp_ddl
        session.sql(get_check_alerts_sp_ddl(db, schema)).collect()
        bulk_ok += 1
    except Exception as e:
        bulk_fail += 1
        failed_list.append(f"SP_CC_CHECK_ALERTS: {str(e)[:120]}")

    st.caption("Creating SP_CC_EVALUATE_RESPONSES (quality scoring)...")
    try:
        from sp_definitions import get_evaluate_responses_sp_ddl
        session.sql(get_evaluate_responses_sp_ddl(db, schema)).collect()
        bulk_ok += 1
    except Exception as e:
        bulk_fail += 1
        failed_list.append(f"SP_CC_EVALUATE_RESPONSES: {str(e)[:120]}")

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
        ("USD_PER_CREDIT", "3.00"),
        ("ALERT_EMAIL_RECIPIENTS", ""),
        ("NOTIFICATION_INTEGRATION", "CC_EMAIL_INTEGRATION"),
        ("EVAL_MODEL", "claude-sonnet-4-5"),
        ("EVAL_BATCH_SIZE", "200"),
        ("EVAL_ENABLED", "FALSE"),
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

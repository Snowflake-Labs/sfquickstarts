"""
CoCo Control Hub — Policy Rules
=================================
Admin-configurable responsible AI governance rules.
Rules are evaluated overnight by SP_CC_CLASSIFY_PROMPTS.

Rule types:
  KEYWORD  — simple keyword list (free, instant)
  REGEX    — pattern matching (free, instant)
  SEMANTIC — Snowflake Cortex AI_CLASSIFY (LLM evaluates each unique prompt;
             runs only on prompts not caught by KEYWORD/REGEX; ~0.00005 credits per unique prompt)
"""

import json
import altair as alt
import pandas as pd
import streamlit as st

from audit import log_activity
from config import (
    TABLE_POLICY_RULES,
    TABLE_PROMPT_VIOLATIONS,
    escape_sql_literal,
    fq_table,
    get_current_user,
)

_BG = "#0e1117"
_R  = "#fca5a5"   # rose-300     (muted)
_A  = "#fcd34d"   # amber-300    (muted)
_G  = "#6ee7b7"   # emerald-300  (muted)

_RISK_COLOR = {"HIGH": _R, "MEDIUM": _A, "LOW": _G}
_CATEGORIES = ["PII_RISK", "SECURITY", "PERSONAL_USE", "COMPETITOR", "USAGE_ANOMALY", "CUSTOM"]
_RISK_LEVELS = ["HIGH", "MEDIUM", "LOW"]
_RULE_TYPES  = ["KEYWORD", "REGEX", "SEMANTIC"]
_TARGETS     = ["PROMPT", "RESPONSE", "BOTH"]
_TARGET_HELP = {
    "PROMPT":   "Classify the user's message to the AI. Catches what users are asking.",
    "RESPONSE": "Classify the AI's reply. Catches sensitive data or policy issues in outputs. Requires PRIVATE_MODE=OFF.",
    "BOTH":     "Classify both the user prompt and the AI response independently.",
}

_CSS = """<style>
.rule-card{background:linear-gradient(90deg,rgba(239,68,68,0.06),rgba(239,68,68,0.02));
  border-left:3px solid #ef4444;border-radius:0 6px 6px 0;padding:0.4rem 0.75rem;margin:0.4rem 0}
.rule-card.medium{border-left-color:#f59e0b;background:linear-gradient(90deg,rgba(245,158,11,0.06),rgba(245,158,11,0.02))}
.rule-card.low{border-left-color:#22c55e;background:linear-gradient(90deg,rgba(34,197,94,0.06),rgba(34,197,94,0.02))}
.rule-card h5{margin:0;font-size:0.82rem;font-weight:600;color:#f9fafb}
.rule-card .meta{font-size:0.68rem;color:#6b7280;margin-top:0.1rem}
</style>"""


def _sec(title):
    """Section header — consistent muted slate across all pages."""
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=False)
def _load_rules(_session):
    tbl = fq_table(_session, TABLE_POLICY_RULES)
    tv  = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    try:
        df = _session.sql(f"""
            SELECT r.*,
                   COUNT(v.VIOLATION_ID) AS VIOLATION_COUNT,
                   MAX(v.VIOLATION_DATE) AS LAST_TRIGGERED
            FROM {tbl} r
            LEFT JOIN {tv} v ON v.RULE_ID = r.RULE_ID
            GROUP BY r.RULE_ID, r.RULE_NAME, r.DESCRIPTION, r.RULE_TYPE,
                     r.CONDITIONS, r.RISK_LEVEL, r.CATEGORY, r.IS_ACTIVE,
                     r.CREATED_BY, r.CREATED_AT, r.TARGET
            ORDER BY r.RISK_LEVEL, r.RULE_NAME
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception as e:
        st.warning(f"Could not load policy rules: {e}")
        return pd.DataFrame()


def _save_rule(session, name, desc, rtype, conditions, risk, category, target="PROMPT"):
    tbl   = fq_table(session, TABLE_POLICY_RULES)
    actor = escape_sql_literal(get_current_user(session))
    cond_json = escape_sql_literal(json.dumps(conditions))
    try:
        session.sql(f"""
            INSERT INTO {tbl} (RULE_NAME, DESCRIPTION, RULE_TYPE, CONDITIONS, RISK_LEVEL, CATEGORY, TARGET, CREATED_BY)
            SELECT '{escape_sql_literal(name)}', '{escape_sql_literal(desc)}',
                   '{rtype}', PARSE_JSON('{cond_json}'), '{risk}', '{category}', '{target}', '{actor}'
        """).collect()
        log_activity(session, "CREATE_POLICY_RULE",
                     details={"name": name, "type": rtype, "risk": risk, "category": category, "target": target})
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def _update_rule(session, rule_id: int, name: str, desc: str, rtype: str,
                 conditions: dict, risk: str, category: str, target: str = "PROMPT") -> tuple:
    tbl   = fq_table(session, TABLE_POLICY_RULES)
    actor = escape_sql_literal(get_current_user(session))
    cond_json = escape_sql_literal(json.dumps(conditions))
    safe_name = escape_sql_literal(name)
    safe_desc = escape_sql_literal(desc)
    try:
        session.sql(f"""
            UPDATE {tbl}
            SET RULE_NAME   = '{safe_name}',
                DESCRIPTION = '{safe_desc}',
                RULE_TYPE   = '{rtype}',
                CONDITIONS  = PARSE_JSON('{cond_json}'),
                RISK_LEVEL  = '{risk}',
                CATEGORY    = '{category}',
                TARGET      = '{target}',
                CREATED_BY  = '{actor}'
            WHERE RULE_ID = {rule_id}
        """).collect()
        log_activity(session, "UPDATE_POLICY_RULE",
                     details={"rule_id": rule_id, "name": name, "risk": risk, "target": target})
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)


def _toggle_rule(session, rule_id: int, active: bool):
    tbl = fq_table(session, TABLE_POLICY_RULES)
    try:
        session.sql(f"UPDATE {tbl} SET IS_ACTIVE = {active} WHERE RULE_ID = {rule_id}").collect()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Could not update rule: {e}")


def _delete_rule(session, rule_id: int):
    tbl = fq_table(session, TABLE_POLICY_RULES)
    tv  = fq_table(session, TABLE_PROMPT_VIOLATIONS)
    try:
        session.sql(f"DELETE FROM {tv} WHERE RULE_ID = {rule_id}").collect()
        session.sql(f"DELETE FROM {tbl} WHERE RULE_ID = {rule_id}").collect()
        st.cache_data.clear()
        log_activity(session, "DELETE_POLICY_RULE", details={"rule_id": rule_id})
    except Exception as e:
        st.error(f"Could not delete rule: {e}")


def render(session):
    st.markdown(_CSS, unsafe_allow_html=True)
    st.header("Policy Rules",
              help="Define responsible AI governance rules. Rules are evaluated nightly against all Cortex Code prompts.")
    st.caption("Rules run overnight via SP_CC_CLASSIFY_PROMPTS. Insights appear in Prompt Insights by next morning.")

    tab_rules, tab_create, tab_run = st.tabs(["Active Rules", "Create Rule", "Run Analysis"])

    # ── Active Rules ─────────────────────────────────────────────────────────
    with tab_rules:
        rules = _load_rules(session)

        if rules.empty:
            st.info("No rules yet. Create your first rule in the 'Create Rule' tab.")
        else:
            # Summary KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Rules",   f"{len(rules):,}")
            k2.metric("Active",        f"{rules['IS_ACTIVE'].sum():,}")
            k3.metric("High Risk",     f"{(rules['RISK_LEVEL']=='HIGH').sum():,}")
            k4.metric("Total Insights", f"{int(rules['VIOLATION_COUNT'].sum()):,}")

            st.divider()

            for _, row in rules.iterrows():
                card_cls = row["RISK_LEVEL"].lower() if row["RISK_LEVEL"] in ("MEDIUM","LOW") else ""
                last = str(row["LAST_TRIGGERED"])[:10] if pd.notna(row.get("LAST_TRIGGERED")) else "Never"
                active = bool(row["IS_ACTIVE"])

                with st.container(border=True):
                    col_info, col_actions = st.columns([5, 2])
                    with col_info:
                        risk_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(row["RISK_LEVEL"], "⚪")
                        target_val = str(row.get("TARGET", "PROMPT") or "PROMPT")
                        target_badge = {"PROMPT": "📥 Prompt", "RESPONSE": "📤 Response", "BOTH": "↕️ Both"}.get(target_val, "📥 Prompt")
                        st.markdown(
                            f"**{risk_color} {row['RULE_NAME']}** "
                            f"<span style='font-size:0.7rem;color:#6b7280;margin-left:0.5rem'>"
                            f"{row['RULE_TYPE']} · {row['CATEGORY']} · {target_badge} · Last triggered: {last}</span>",
                            unsafe_allow_html=True
                        )
                        st.caption(row["DESCRIPTION"] or "")
                        cond = row.get("CONDITIONS", {})
                        if isinstance(cond, str):
                            try:
                                cond = json.loads(cond)
                            except Exception:
                                cond = {}
                        if isinstance(cond, dict):
                            kws = cond.get("keywords", cond.get("patterns", []))
                            if kws:
                                st.caption("Keywords: " + " · ".join(f"`{k}`" for k in kws[:8]) +
                                           (" …" if len(kws) > 8 else ""))
                    with col_actions:
                        vcol, ecol, acol, dcol = st.columns([2, 1, 2, 1])
                        vcol.metric("Insights", int(row["VIOLATION_COUNT"]))
                        if ecol.button("✏️", key=f"edit_btn_{row['RULE_ID']}",
                                       help="Edit this rule's name, description, keywords, severity level"):
                            edit_key = f"editing_{row['RULE_ID']}"
                            st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                            st.rerun()
                        if acol.button("Disable" if active else "Enable", key=f"toggle_{row['RULE_ID']}",
                                       help="Disable this rule (skip in next analysis)" if active else "Enable this rule"):
                            _toggle_rule(session, int(row["RULE_ID"]), not active)
                            st.rerun()
                        if dcol.button("🗑", key=f"del_{row['RULE_ID']}",
                                       help="Delete this rule permanently"):
                            if st.session_state.get(f"confirm_del_{row['RULE_ID']}"):
                                _delete_rule(session, int(row["RULE_ID"]))
                                st.rerun()
                            else:
                                st.session_state[f"confirm_del_{row['RULE_ID']}"] = True
                                st.warning("Click 🗑 again to confirm deletion.")

                    # ── Inline edit form (toggled by ✏️ button) ──────────────
                    if st.session_state.get(f"editing_{row['RULE_ID']}", False):
                        st.divider()
                        with st.form(key=f"edit_form_{row['RULE_ID']}"):
                            st.caption("Edit Rule")
                            e_name = st.text_input("Rule Name *", value=row["RULE_NAME"],
                                                   key=f"e_name_{row['RULE_ID']}")
                            e_desc = st.text_area("Description", value=row["DESCRIPTION"] or "",
                                                  height=70, key=f"e_desc_{row['RULE_ID']}")
                            ec1, ec2, ec3, ec4 = st.columns(4)
                            with ec1:
                                e_rtype = st.selectbox("Rule Type", _RULE_TYPES,
                                                       index=_RULE_TYPES.index(row["RULE_TYPE"]) if row["RULE_TYPE"] in _RULE_TYPES else 0,
                                                       key=f"e_rtype_{row['RULE_ID']}")
                            with ec2:
                                e_risk = st.selectbox("Risk Level", _RISK_LEVELS,
                                                      index=_RISK_LEVELS.index(row["RISK_LEVEL"]) if row["RISK_LEVEL"] in _RISK_LEVELS else 0,
                                                      key=f"e_risk_{row['RULE_ID']}")
                            with ec3:
                                e_cat = st.selectbox("Category", _CATEGORIES,
                                                     index=_CATEGORIES.index(row["CATEGORY"]) if row["CATEGORY"] in _CATEGORIES else 0,
                                                     key=f"e_cat_{row['RULE_ID']}")
                            with ec4:
                                cur_tgt = str(row.get("TARGET","PROMPT") or "PROMPT")
                                e_tgt = st.selectbox("Applies to", _TARGETS,
                                                     index=_TARGETS.index(cur_tgt) if cur_tgt in _TARGETS else 0,
                                                     key=f"e_tgt_{row['RULE_ID']}",
                                                     help=_TARGET_HELP.get(cur_tgt,""))

                            # Pre-populate keywords/patterns/examples from existing conditions
                            existing_cond = row.get("CONDITIONS", {})
                            if isinstance(existing_cond, str):
                                try:
                                    existing_cond = json.loads(existing_cond)
                                except Exception:
                                    existing_cond = {}
                            if not isinstance(existing_cond, dict):
                                existing_cond = {}
                            kw_default = "\n".join(existing_cond.get("keywords", existing_cond.get("patterns", existing_cond.get("examples", []))))

                            if e_rtype == "KEYWORD":
                                e_kw = st.text_area("Keywords (one per line) *", value=kw_default,
                                                    height=110, key=f"e_kw_{row['RULE_ID']}",
                                                    help="Case-insensitive. Any matching keyword triggers this rule.")
                            elif e_rtype == "REGEX":
                                e_kw = st.text_area("Regex Patterns (one per line) *", value=kw_default,
                                                    height=110, key=f"e_kw_{row['RULE_ID']}",
                                                    help="Python regex, case-insensitive.")
                            else:
                                e_kw = st.text_area("Example Prompts (optional)", value=kw_default,
                                                    height=110, key=f"e_kw_{row['RULE_ID']}",
                                                    help="Optional context — AI_CLASSIFY uses Rule Name + Description.")

                            save_col, cancel_col = st.columns([1, 1])
                            with save_col:
                                save_edit = st.form_submit_button("Save Changes", type="primary")
                            with cancel_col:
                                cancel_edit = st.form_submit_button("Cancel")

                        if save_edit:
                            if not e_name.strip():
                                st.error("Rule Name is required.")
                            else:
                                items = [k.strip() for k in e_kw.strip().splitlines() if k.strip()]
                                if e_rtype == "KEYWORD":
                                    new_cond = {"keywords": items}
                                elif e_rtype == "REGEX":
                                    new_cond = {"patterns": items}
                                else:
                                    new_cond = {"examples": items}
                                ok, err = _update_rule(session, int(row["RULE_ID"]),
                                                       e_name.strip(), e_desc.strip(),
                                                       e_rtype, new_cond, e_risk, e_cat, e_tgt)
                                if ok:
                                    st.session_state[f"editing_{row['RULE_ID']}"] = False
                                    st.success(f"✓ Rule updated.")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to update: {err}")
                        elif cancel_edit:
                            st.session_state[f"editing_{row['RULE_ID']}"] = False
                            st.rerun()

    # ── Create Rule ──────────────────────────────────────────────────────────
    with tab_create:
        _sec("New Policy Rule")
        st.caption("Rules are evaluated every night at 2am UTC via CC_CLASSIFY_PROMPTS_TASK.")

        with st.expander("How classification works — read before creating a rule", expanded=False):
            st.markdown("""
Every night (or when you click **Run Analysis**), the system reads all Cortex Code
prompts from the last analysis window and runs them through three tiers in order:

| Tier | Type | How it works | Cost |
|------|------|-------------|------|
| **1** | KEYWORD | Literal substring match — `"api key" in prompt.lower()` | Free |
| **2** | REGEX | Python `re.search(pattern, prompt)` — supports wildcards, word boundaries | Free |
| **3** | SEMANTIC | Snowflake `AI_CLASSIFY(prompt, [your_rule_labels, 'benign'])` — LLM classifies intent | ~$0.00005 / unique prompt |

**Tiers run in order. A prompt caught by Tier 1 or 2 is never sent to Tier 3.**
This keeps semantic costs low — only ambiguous prompts reach the LLM.

---

**KEYWORD** — best for known, exact phrases:
```
api key · password · social security · export to s3
```
Catches `"my api_key is abc123"` or `"what is my social security number"`.
Does **not** catch `"authentication token"` if `token` isn't in your keyword list.

---

**REGEX** — best for patterns with variable structure:
```
\\b\\d{3}-\\d{2}-\\d{4}\\b     → matches SSN format  123-45-6789
\\bsk-[a-z0-9]{32,}\\b         → matches OpenAI API key format
```
More powerful than keywords, still free. Requires Python regex syntax.

---

**SEMANTIC (AI_CLASSIFY)** — best for intent-based detection:

Your SEMANTIC rule names get normalized into classification labels:
```
Rule Name "Data Exfiltration Attempt"  →  label: "data_exfiltration_attempt"
Rule Name "Competitor Research"        →  label: "competitor_research"
```
The LLM receives:
```sql
AI_CLASSIFY(prompt, ['data_exfiltration_attempt', 'competitor_research', 'benign'])
```
It reads the prompt and returns whichever label best matches the **intent** — not just keywords.

> ✏️ **Write a precise Rule Name + Description.** The label name *and* description are what
> the LLM uses to understand what to detect. "Data Exfiltration Attempt" works.
> "Rule 7" does not.

Deduplication: identical prompts (same SHA-256 hash) are classified **once** and the
result applied to all users who sent the same prompt. Cap: 5,000 unique prompts/run.

---

**RESPONSE monitoring (new)**

In addition to classifying what users *ask*, the system can classify what the AI *answers*.
The `CodingAgentRun` span in Snowflake's AI Observability logs contains the AI's final reply.
This is joined automatically during Step 0 event loading.

Use the **"Applies to"** dropdown when creating or editing a rule:

| Option | What gets classified |
|--------|---------------------|
| **📥 Prompt** (default) | The user's message to the AI |
| **📤 Response** | The AI's reply (skipped if user has Private Mode ON) |
| **↕️ Both** | Runs the rule independently on both — can trigger two prompt insights |

> **Note on Private Mode:** When a user enables Private Mode in Cortex Code,
> Snowflake does not log the AI response. Response rules cannot fire for those sessions.
> Prompt rules are unaffected.

Response classification uses the same 3-tier logic with adjusted caps:
- KEYWORD/REGEX on responses: free, no limit
- SEMANTIC on responses: 2,000 unique responses/run (responses are longer than prompts)
""")

        with st.form("create_rule_form"):
            name = st.text_input("Rule Name *", placeholder="e.g. PII in Prompts",
                                 help="Short, unique name. For SEMANTIC rules this becomes the classification label — make it descriptive.")
            desc = st.text_area("Description", placeholder="What does this rule catch and why?",
                                height=80,
                                help="For SEMANTIC rules: the LLM reads this description to understand what intent to detect. Be specific.")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                rtype = st.selectbox("Rule Type", _RULE_TYPES,
                                     help=(
                                         "KEYWORD: free, instant substring match. "
                                         "REGEX: free, Python regex pattern. "
                                         "SEMANTIC: Cortex AI_CLASSIFY — LLM intent detection. "
                                         "Runs only on prompts not caught by KEYWORD/REGEX. "
                                         "~0.00005 credits per unique prompt, cap 5,000/run."
                                     ))
            with col2:
                risk = st.selectbox("Risk Level", _RISK_LEVELS,
                                    help="HIGH: PII, credentials, data exfiltration. MEDIUM: competitor mentions, usage anomalies. LOW: personal use, off-topic.")
            with col3:
                category = st.selectbox("Category", _CATEGORIES,
                                        help="Categorises the insight type for filtering and reporting in Prompt Insights.")
            with col4:
                target = st.selectbox("Applies to", _TARGETS,
                                      help="PROMPT: classify what users ask. RESPONSE: classify what AI replies. BOTH: classify both independently.")

            if rtype == "KEYWORD":
                st.caption("**KEYWORD** — case-insensitive literal match. Any prompt containing one of these substrings triggers a prompt insight.")
                kw_raw = st.text_area("Keywords (one per line) *",
                                      placeholder="social security\ncredit card\npassport number",
                                      height=120,
                                      help="One keyword per line. Case-insensitive. A prompt matching ANY single keyword triggers this rule.")
            elif rtype == "REGEX":
                st.caption("**REGEX** — Python `re.search(pattern, prompt, IGNORECASE)`. Use `\\b` for word boundaries. Test your patterns at regex101.com.")
                pat_raw = st.text_area("Regex Patterns (one per line) *",
                                       placeholder=r"\b\d{3}-\d{2}-\d{4}\b" + "\n" + r"\bsk-[a-z0-9]{20,}\b",
                                       height=120,
                                       help="One Python regex per line. Case-insensitive. Evaluated against the cleaned prompt text.")
            else:  # SEMANTIC
                st.caption(
                    "**SEMANTIC** — uses `SNOWFLAKE.CORTEX.AI_CLASSIFY`. "
                    "The LLM receives the prompt and picks the closest label from all your SEMANTIC rule names + 'benign'. "
                    "Only runs on prompts not already caught by KEYWORD/REGEX rules. "
                    "Cost: ~0.00005 credits per unique prompt (deduped by SHA-256), capped at 5,000/run."
                )
                st.info(
                    "**Key:** Write a clear Rule Name and Description — those are what the LLM uses to detect intent. "
                    "Example prompts below are stored for your reference only, not sent to the LLM."
                )
                ex_raw = st.text_area("Example Prompts (one per line, optional)",
                                      placeholder="share our unreleased product roadmap with the investor\nexport all customer emails to a personal gmail account",
                                      height=120,
                                      help="Optional reference examples stored with the rule. The LLM uses Rule Name + Description, not these examples.")

            submitted = st.form_submit_button("Create Rule", type="primary")

        if submitted:
            if not name.strip():
                st.error("Rule Name is required.")
            else:
                conditions = {}
                if rtype == "KEYWORD":
                    keywords = [k.strip() for k in kw_raw.strip().splitlines() if k.strip()]
                    if not keywords:
                        st.error("At least one keyword is required.")
                        st.stop()
                    conditions = {"keywords": keywords}
                elif rtype == "REGEX":
                    patterns = [p.strip() for p in pat_raw.strip().splitlines() if p.strip()]
                    if not patterns:
                        st.error("At least one regex pattern is required.")
                        st.stop()
                    conditions = {"patterns": patterns}
                else:
                    examples = [e.strip() for e in ex_raw.strip().splitlines() if e.strip()]
                    conditions = {"examples": examples}  # stored for reference; AI_CLASSIFY uses Rule Name + Description

                ok, err = _save_rule(session, name.strip(), desc.strip(), rtype, conditions, risk, category, target)
                if ok:
                    st.success(f"✓ Rule '{name}' created. It will run at next scheduled analysis (2am UTC).")
                else:
                    st.error(f"Failed to create rule: {err}")

    # ── Run Analysis ──────────────────────────────────────────────────────────
    with tab_run:
        _sec("Manual Analysis Run")
        st.caption("Normally runs overnight at 2am UTC. Use this to trigger immediately for testing.")

        st.info(
            "**Scheduled:** Every night at 2am UTC via `CC_CLASSIFY_PROMPTS_TASK`.\n\n"
            "**Manual run:** Scans the last 26 hours of prompts against all active rules. "
            "Results appear in Prompt Analysis within seconds."
        )

        col_l, col_r = st.columns(2)
        with col_l:
            hours = st.number_input("Lookback hours", min_value=1, max_value=168,
                                    value=26, step=1,
                                    help="How many hours of prompts to re-analyze.")
        with col_r:
            st.write("")
            st.write("")
            run_btn = st.button("Run Analysis Now", type="primary", key="btn_run_analysis",
                                help="Calls SP_CC_CLASSIFY_PROMPTS immediately.")

        if run_btn:
            from config import fq_sp
            sp = fq_sp(session, "SP_CC_CLASSIFY_PROMPTS")
            with st.spinner(f"Scanning last {int(hours)} hours of prompts…"):
                try:
                    result = session.sql(f"CALL {sp}({int(hours)})").collect()
                    raw = result[0][0] if result else "{}"
                    res = json.loads(raw) if isinstance(raw, str) else raw
                    st.session_state["last_analysis_result"] = res
                    st.session_state["last_analysis_status"] = "ok"
                    st.cache_data.clear()
                except Exception as e:
                    st.session_state["last_analysis_result"] = {}
                    st.session_state["last_analysis_status"] = str(e)

        if "last_analysis_status" in st.session_state:
            status = st.session_state["last_analysis_status"]
            r = st.session_state.get("last_analysis_result", {})

            if status == "ok":
                st.markdown(
                    '<div style="background:rgba(34,197,94,0.1);border-left:3px solid #22c55e;'
                    'border-radius:0 6px 6px 0;padding:0.5rem 0.75rem;margin:0.5rem 0">'
                    '<span style="color:#4ade80;font-weight:700">✓ Analysis completed</span>'
                    '</div>',
                    unsafe_allow_html=True)
                if isinstance(r, dict) and not r.get("error"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Prompts Scanned",    r.get("prompts_scanned", 0),
                              help="Total prompts evaluated across all 3 tiers.")
                    c2.metric("prompt insights found",   r.get("violations_found", 0),
                              help="Total violations written to CC_PROMPT_VIOLATIONS.")
                    c3.metric("Users Flagged",      r.get("users_analyzed", 0),
                              help="Distinct users with at least one prompt insight.")
                    c4.metric("AI Classified",      r.get("semantic_classified", 0),
                              help="Unique prompts evaluated by AI_CLASSIFY (Tier 3 SEMANTIC). "
                                   f"~{r.get('semantic_classified', 0) * 0.00005:.4f} credits used.")
                    sem_v = r.get("semantic_violations", 0)
                    if sem_v:
                        st.caption(f"🔬 Semantic tier caught **{sem_v}** additional insight(s) not found by keyword/regex.")
                    if r.get("errors"):
                        st.warning(f"Warnings: {r['errors'][:3]}")
                elif isinstance(r, dict) and r.get("error"):
                    st.error(r["error"])
            else:
                st.markdown(
                    f'<div style="background:rgba(239,68,68,0.1);border-left:3px solid #ef4444;'
                    f'border-radius:0 6px 6px 0;padding:0.5rem 0.75rem;margin:0.5rem 0">'
                    f'<span style="color:#f87171;font-weight:700">✗ Analysis failed:</span> '
                    f'<span style="color:#d1d5db;font-size:0.82rem">{status[:200]}</span>'
                    f'</div>',
                    unsafe_allow_html=True)

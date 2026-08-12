"""
CoCo Control Hub — Chargeback / Guided Bill Generation
======================================================
One configurable flow for cross-charging Cortex + compute spend.

  ▸ Set up cost tags   — app-owned USER→{Vertical, Partner-flag} mapping
                         (CC_COST_TAGS). Unlocks the gated group-by dimensions.
  Start from a model   — three prominent preset cards that pre-fill (dimension +
                         audience): M1 Internal cross-charge · M2 Build & deploy
                         (partner-run) · M3 Partner on customer account.
  ① Bill by            — attribution dimension → drives the GROUP BY
                         (user / role / surface / model / service / vertical / partner).
  ② Scope              — period + which values to include.
  ③ Audience           — Internal (at-cost showback) vs External (invoice + margin).
  ④ Generate           — KPIs + itemized table + CSV / PDF export.

The 3 adoption models are presets of (dimension + audience), not separate code
paths — the "one configurable app" decision made real. USD/credit rate comes
from Settings (USD_PER_CREDIT).
"""

import altair as alt
import pandas as pd
import streamlit as st

from config import (
    TABLE_USAGE_DAILY, TABLE_COST_TAGS, TABLE_WAREHOUSE_USAGE_DAILY,
    ATTRIBUTION_DIMENSIONS, MODEL_PRESETS, SP_SYNC_COST_TAGS,
    get_dimension, fq_table, fq_sp, escape_sql_literal, get_current_user,
)
from utils import get_app_setting
from audit import log_activity
from tagging import ensure_tags_table, tags_populated, render_tag_editor

_BG = "#0e1117"
_P  = "#7dd3fc"
_G  = "#6ee7b7"
_O  = "#fcd34d"

# Map raw SERVICE_TYPE → billing category for grouped invoice lines (service dim).
_CATEGORY = {
    "WAREHOUSE_METERING": "Compute", "SERVERLESS_TASK": "Compute",
    "SNOWWORK": "Compute", "POSTGRES_COMPUTE": "Compute",
    "QUERY_ACCELERATION": "Compute", "SNOWPARK_CONTAINER_SERVICES": "Compute",
    "CORTEX_CODE_CLI": "AI Services", "CORTEX_CODE_SNOWSIGHT": "AI Services",
    "CORTEX_CODE_DESKTOP": "AI Services", "CORTEX_SEARCH": "AI Services",
    "AI_SERVICES": "AI Services", "CORTEX_FUNCTIONS": "AI Services",
    "TABLE_OPTIMIZATION": "Cloud Services", "AUTO_CLUSTERING": "Cloud Services",
    "AUTOMATED_REFRESH_AND_DATA_REGISTRATION": "Cloud Services",
    "MATERIALIZED_VIEW": "Cloud Services", "PIPE": "Cloud Services",
    "TELEMETRY_DATA_INGEST": "Cloud Services",
}


def _lat(s) -> str:
    """Core PDF fonts are latin-1 only — sanitize any unsupported chars."""
    return str(s).encode("latin-1", "replace").decode("latin-1")


def _sec(title):
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


# ─────────────────────────────── PDF (branded invoice) ───────────────────────
_NAVY   = (17, 86, 127)     # #11567F header band
_ACCENT = (41, 181, 232)    # #29B5E8 Snowflake blue accent
_INK    = (31, 41, 55)      # body text
_MUT    = (110, 116, 128)   # muted labels
_ZEB    = (244, 246, 249)   # zebra row
_AISEG  = (41, 181, 232)    # AI / LLM proportion segment
_WHSEG  = (110, 198, 158)   # warehouse proportion segment


def _build_invoice_pdf(bill_df, meta) -> bytes:
    """Render a one-page, executive-friendly bill as PDF bytes (fpdf2).

    `meta` drives everything (external flag, totals, labels). The line-item table
    shows business columns only (entity / usage / cost / billed); the deeper
    per-user, per-query token+compute detail is deferred to CSV export.
    """
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    ext = bool(meta.get("external"))

    class _InvoicePDF(FPDF):
        def header(self):
            self.set_fill_color(*_NAVY)
            self.rect(0, 0, 210, 24, style="F")
            self.set_fill_color(*_ACCENT)
            self.rect(0, 24, 210, 1.6, style="F")
            self.set_xy(15, 5.5)
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 17)
            self.cell(120, 8, "CoCo Control Hub & Chargeback")
            self.set_xy(15, 14.5)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(205, 228, 242)
            self.cell(120, 5, "Cortex Code Cost Report")
            chip = "INVOICE" if ext else "SHOWBACK"
            cw = 34
            cx = 195 - cw
            self.set_fill_color(255, 255, 255)
            self.set_text_color(*_NAVY)
            self.set_font("Helvetica", "B", 9)
            self.set_xy(cx, 6)
            self.cell(cw, 7, chip, align="C", fill=True)
            self.set_xy(cx - 30, 15)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(205, 228, 242)
            self.cell(cw + 30, 5, _lat("Issued " + str(meta.get("issued", ""))), align="R")
            self.set_xy(15, 32)
            self.set_text_color(*_INK)

        def footer(self):
            self.set_y(-13)
            self.set_draw_color(214, 218, 224)
            self.set_line_width(0.2)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(1.5)
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(*_MUT)
            self.cell(150, 5, _lat(meta.get("footer_note", "Confidential - chargeback use.")))
            self.cell(30, 5, f"Page {self.page_no()} of {{nb}}", align="R")

    rate     = float(meta.get("usd_rate", 2.0))
    wh_rate  = float(meta.get("wh_rate", rate))
    subtotal = float(meta.get("subtotal_usd", 0.0))
    billed   = float(meta.get("billed_usd", 0.0))
    up_pct   = float(meta.get("upcharge_pct", 0.0))
    t_cr     = float(meta.get("total_credits", 0.0))
    t_tok    = float(meta.get("total_token_credits", 0.0))
    t_wh     = float(meta.get("total_wh_credits", 0.0))
    is_svc   = bool(meta.get("is_service"))
    key_title = meta.get("dimension_key_title", "Group")

    pdf = _InvoicePDF(orientation="P", unit="mm", format="A4")
    pdf.meta = meta
    pdf.set_margins(15, 32, 15)
    pdf.set_auto_page_break(True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Meta: two columns ─────────────────────────────────────────────────────
    top = 33
    pdf.set_xy(15, top); pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*_ACCENT)
    pdf.cell(90, 5, "BILL TO" if ext else "PREPARED FOR")
    pdf.set_xy(112, top); pdf.cell(83, 5, "INVOICE DETAILS" if ext else "STATEMENT DETAILS")

    ly = top + 6
    pdf.set_xy(15, ly); pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*_INK)
    pdf.cell(92, 5, _lat((meta.get("bill_to") or "-") if ext else (meta.get("prepared_by") or "-")))
    ly += 5.6
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(15, ly); pdf.cell(92, 5, _lat("Attribution: " + meta.get("attribution", "-"))); ly += 5
    if meta.get("adoption_model"):
        pdf.set_xy(15, ly); pdf.cell(92, 5, _lat("Model: " + meta["adoption_model"])); ly += 5

    def _rrow(y, label, val):
        pdf.set_xy(112, y); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*_MUT)
        pdf.cell(22, 5, _lat(label))
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*_INK)
        pdf.cell(61, 5, _lat(str(val)))

    ry = top + 6
    _rrow(ry, "Period", meta.get("period_label", "-")); ry += 5.2
    _rrow(ry, "Issued", meta.get("issued", "-")); ry += 5.2
    if ext:
        _rrow(ry, "Invoice #", meta.get("invoice_no", "-")); ry += 5.2
        _rrow(ry, "Prepared", meta.get("prepared_by") or "-"); ry += 5.2
    if is_svc:
        _rrow(ry, "Rate", f"${wh_rate:.2f} / credit"); ry += 5.2
    else:
        _rrow(ry, "AI rate", f"${rate:.2f} / credit"); ry += 5.2
        if t_wh > 0:
            _rrow(ry, "WH rate", f"${wh_rate:.2f} / credit"); ry += 5.2

    cy = max(ly, ry) + 3

    # ── Summary of charges card ───────────────────────────────────────────────
    pdf.set_draw_color(*_ACCENT); pdf.set_line_width(0.4)
    pdf.rect(15, cy, 180, 30); pdf.set_line_width(0.2)
    pdf.set_xy(19, cy + 2.5); pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*_ACCENT)
    pdf.cell(100, 5, "SUMMARY OF CHARGES")
    pdf.set_xy(19, cy + 8); pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*_MUT)
    pdf.cell(85, 4, "TOTAL USAGE")
    pdf.set_xy(112, cy + 8); pdf.cell(80, 4, "TOTAL BILLED")
    pdf.set_xy(19, cy + 12); pdf.set_font("Helvetica", "B", 15); pdf.set_text_color(*_INK)
    pdf.cell(90, 7, _lat(f"{t_cr:,.2f} credits"))
    pdf.set_xy(112, cy + 12); pdf.set_text_color(*_NAVY)
    pdf.cell(80, 7, _lat(f"${billed:,.2f}"))
    if (not is_svc) and t_wh > 0 and t_cr > 0:
        ai_pct = t_tok / t_cr * 100.0
        pdf.set_xy(19, cy + 21); pdf.set_font("Helvetica", "", 7.5); pdf.set_text_color(*_MUT)
        pdf.cell(120, 4, "WHAT YOU'RE PAYING FOR")
        bx, by, bw = 19, cy + 25, 118
        aw = bw * ai_pct / 100.0
        pdf.set_fill_color(*_AISEG); pdf.rect(bx, by, aw, 3.2, style="F")
        pdf.set_fill_color(*_WHSEG); pdf.rect(bx + aw, by, bw - aw, 3.2, style="F")
        pdf.set_xy(bx + bw + 4, by - 0.6); pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*_INK)
        pdf.cell(55, 4, _lat(f"AI/LLM {ai_pct:.0f}%   WH {100 - ai_pct:.0f}%"))
    else:
        pdf.set_xy(19, cy + 22); pdf.set_font("Helvetica", "I", 8); pdf.set_text_color(*_MUT)
        msg = ("Whole-account metering (already includes compute)." if is_svc
               else "LLM token credits.")
        pdf.cell(160, 4, _lat(msg))
    pdf.set_y(cy + 35)

    # ── Charges table (business columns only) ─────────────────────────────────
    if is_svc and "CATEGORY" in bill_df.columns:
        disp = (bill_df.groupby("CATEGORY", as_index=False)
                .agg(USAGE=("CREDITS", "sum"), COST=("USD", "sum"), BILLED=("BILLED_USD", "sum")))
        disp = disp.rename(columns={"CATEGORY": "KEY"})
    else:
        disp = bill_df.rename(columns={"GROUP_KEY": "KEY", "CREDITS": "USAGE",
                                       "USD": "COST", "BILLED_USD": "BILLED"})[
            ["KEY", "USAGE", "COST", "BILLED"]]
    disp = disp.sort_values("BILLED", ascending=False).reset_index(drop=True)
    TOPN = 12
    if len(disp) > TOPN:
        head = disp.head(TOPN)
        rest = disp.iloc[TOPN:]
        other = pd.DataFrame([{"KEY": f"All other ({len(rest)} groups)",
                               "USAGE": rest["USAGE"].sum(), "COST": rest["COST"].sum(),
                               "BILLED": rest["BILLED"].sum()}])
        rows_df = pd.concat([head, other], ignore_index=True)
    else:
        rows_df = disp

    pdf.set_x(15); pdf.set_font("Helvetica", "B", 8); pdf.set_text_color(*_ACCENT)
    pdf.cell(0, 5, "CHARGES", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    w = [84, 30, 33, 33]
    hdr = [key_title, "Usage cr", "Cost USD", "Billed USD"]
    pdf.set_x(15); pdf.set_fill_color(*_NAVY); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    for i, (ww, hh) in enumerate(zip(w, hdr)):
        pdf.cell(ww, 7, _lat(hh), align=("L" if i == 0 else "R"), fill=True)
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 8.5)
    zeb = False
    for _, r in rows_df.iterrows():
        pdf.set_x(15)
        pdf.set_fill_color(*_ZEB) if zeb else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*_INK)
        pdf.cell(w[0], 6, _lat(str(r["KEY"]))[:52], fill=True)
        pdf.cell(w[1], 6, f"{float(r['USAGE']):,.2f}", align="R", fill=True)
        pdf.cell(w[2], 6, f"${float(r['COST']):,.2f}", align="R", fill=True)
        pdf.cell(w[3], 6, f"${float(r['BILLED']):,.2f}", align="R", fill=True)
        pdf.ln(6); zeb = not zeb

    pdf.ln(1.5)
    lw = w[0] + w[1]
    pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*_INK)
    if ext:
        pdf.set_x(15); pdf.cell(lw, 6, ""); pdf.cell(w[2], 6, "Subtotal", align="R")
        pdf.cell(w[3], 6, _lat(f"${subtotal:,.2f}"), align="R"); pdf.ln(6)
        pdf.set_x(15); pdf.cell(lw, 6, ""); pdf.cell(w[2], 6, _lat(f"Margin {up_pct:.0f}%"), align="R")
        pdf.cell(w[3], 6, _lat(f"${billed - subtotal:,.2f}"), align="R"); pdf.ln(6)
    pdf.set_x(15); pdf.set_font("Helvetica", "B", 10)
    pdf.cell(lw, 8, "")
    pdf.set_fill_color(*_NAVY); pdf.set_text_color(255, 255, 255)
    pdf.cell(w[2], 8, _lat("TOTAL" if ext else "TOTAL (at cost)"), align="R", fill=True)
    pdf.cell(w[3], 8, _lat(f"${billed:,.2f}"), align="R", fill=True)
    pdf.ln(12)

    # ── Cost by component + depth pointer ─────────────────────────────────────
    pdf.set_text_color(*_INK)
    if (not is_svc) and t_wh > 0:
        pdf.set_x(15); pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(0, 5, "Cost by component", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(15); pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(0, 4.6, _lat(
            f"AI / LLM tokens:  {t_tok:,.2f} cr  -  ${t_tok * rate:,.2f}          "
            f"Warehouse compute:  {t_wh:,.2f} cr  -  ${t_wh * wh_rate:,.2f}"))
        pdf.ln(1.5)
    pdf.set_x(15); pdf.set_font("Helvetica", "I", 8); pdf.set_text_color(*_MUT)
    pdf.multi_cell(0, 4.6, _lat(
        "A detailed per-user, per-query token & compute breakdown is available on "
        "request (CSV export in CoCo Control Hub & Chargeback)."))

    return bytes(pdf.output())


# ─────────────────────────────── Loaders ─────────────────────────────────────
# Cost-tag (L4) helpers live in tagging.py now (shared with Attribution & Tags).


@st.cache_data(ttl=600, show_spinner=False)
def _load_months(_session) -> list:
    """Distinct billing months in METERING_DAILY_HISTORY (most recent first)."""
    try:
        df = _session.sql("""
            SELECT DISTINCT TO_CHAR(DATE_TRUNC('month', USAGE_DATE),'YYYY-MM') AS MONTH
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
            WHERE USAGE_DATE >= DATEADD('month', -12, CURRENT_DATE())
            ORDER BY MONTH DESC
        """).to_pandas()
        return df["MONTH"].tolist() if not df.empty else []
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def _load_month_trend(_session) -> pd.DataFrame:
    try:
        df = _session.sql("""
            SELECT TO_CHAR(DATE_TRUNC('month', USAGE_DATE),'YYYY-MM') AS MONTH,
                   ROUND(SUM(CREDITS_USED),4) AS CREDITS
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
            WHERE USAGE_DATE >= DATEADD('month', -6, CURRENT_DATE())
            GROUP BY 1 ORDER BY MONTH
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_distinct_values(_session, dim_key: str) -> list:
    """Distinct values for the scope multiselect, per dimension."""
    d = get_dimension(dim_key)
    col = d["column"]
    if col == "IS_PARTNER":
        return ["Partner", "Non-partner"]
    try:
        if d["source"] == "metering":
            df = _session.sql("""
                SELECT DISTINCT SERVICE_TYPE AS V
                FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
                WHERE USAGE_DATE >= DATEADD('month', -12, CURRENT_DATE())
                  AND CREDITS_USED > 0 ORDER BY 1
            """).to_pandas()
        elif d["source"] == "usage_tagged":
            tags = fq_table(_session, TABLE_COST_TAGS)
            df = _session.sql(
                f"SELECT DISTINCT {col} AS V FROM {tags} "
                f"WHERE {col} IS NOT NULL ORDER BY 1"
            ).to_pandas()
        else:  # usage
            usage = fq_table(_session, TABLE_USAGE_DAILY)
            df = _session.sql(f"""
                SELECT DISTINCT {col} AS V FROM {usage}
                WHERE {col} IS NOT NULL
                  AND USAGE_DATE >= DATEADD('day', -365, CURRENT_DATE())
                ORDER BY 1
            """).to_pandas()
        vals = [str(x) for x in df["V"].tolist()] if not df.empty else []
        if d["source"] == "usage_tagged":
            vals.append("Untagged")
        return vals
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def _load_attributed_bill(_session, dim_key: str, period, include: tuple) -> pd.DataFrame:
    """Generic grouped bill. Returns GROUP_KEY, CREDITS (+ TOKENS/REQUESTS for
    usage dimensions, + CATEGORY for the service dimension).

    The GROUP BY column is chosen from the whitelisted registry entry (never
    interpolated from user input); the optional `include` filter is applied by
    wrapping the grouped result, so it works uniformly across all sources.
    """
    d = get_dimension(dim_key)
    col = d["column"]

    if d["source"] == "metering":
        where = (f"TO_CHAR(DATE_TRUNC('month', USAGE_DATE),'YYYY-MM') "
                 f"= '{escape_sql_literal(str(period))}'")
        inner = f"""
            SELECT SERVICE_TYPE AS GROUP_KEY,
                   ROUND(SUM(CREDITS_USED),4) AS CREDITS
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
            WHERE {where}
            GROUP BY 1 HAVING SUM(CREDITS_USED) > 0
        """
    elif d["source"] == "usage_tagged":
        usage = fq_table(_session, TABLE_USAGE_DAILY)
        tags = fq_table(_session, TABLE_COST_TAGS)
        days = int(period)
        if col == "IS_PARTNER":
            key_expr = "CASE WHEN t.IS_PARTNER THEN 'Partner' ELSE 'Non-partner' END"
        else:
            key_expr = f"COALESCE(t.{col}, 'Untagged')"
        inner = f"""
            SELECT {key_expr} AS GROUP_KEY,
                   ROUND(SUM(u.TOTAL_CREDITS),4) AS CREDITS,
                   SUM(u.TOTAL_TOKENS)           AS TOKENS,
                   SUM(u.QUERY_COUNT)            AS REQUESTS
            FROM {usage} u
            LEFT JOIN {tags} t ON u.USER_NAME = t.USER_NAME
            WHERE u.USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 HAVING SUM(u.TOTAL_CREDITS) > 0
        """
    else:  # usage
        usage = fq_table(_session, TABLE_USAGE_DAILY)
        days = int(period)
        inner = f"""
            SELECT COALESCE({col}, '(none)') AS GROUP_KEY,
                   ROUND(SUM(TOTAL_CREDITS),4) AS CREDITS,
                   SUM(TOTAL_TOKENS)           AS TOKENS,
                   SUM(QUERY_COUNT)            AS REQUESTS
            FROM {usage}
            WHERE USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 HAVING SUM(TOTAL_CREDITS) > 0
        """

    inc = [v for v in (include or ()) if v]
    if inc:
        vals = ",".join(f"'{escape_sql_literal(v)}'" for v in inc)
        sql = f"SELECT * FROM ({inner}) WHERE GROUP_KEY IN ({vals}) ORDER BY CREDITS DESC"
    else:
        sql = f"SELECT * FROM ({inner}) ORDER BY CREDITS DESC"

    try:
        df = _session.sql(sql).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


# Dimensions whose group key is derivable from a user identity, so warehouse
# compute credits (keyed by user x surface) can be rolled up alongside tokens.
# 'model' has no warehouse split; 'service' already includes compute account-wide.
_WH_DIMS = {"user", "surface", "cohort", "vertical", "partner"}


@st.cache_data(ttl=600, show_spinner=False)
def _load_warehouse_by_dim(_session, dim_key: str, days: int) -> dict:
    """Warehouse compute credits grouped by the same key as the token bill.

    Returns {GROUP_KEY: WAREHOUSE_CREDITS}. All joins are 1:1 on USER_NAME (tags
    PK, one cohort per user) so there is no fanout. Empty for unsupported dims.
    """
    if dim_key not in _WH_DIMS:
        return {}
    wh = fq_table(_session, TABLE_WAREHOUSE_USAGE_DAILY)
    usage = fq_table(_session, TABLE_USAGE_DAILY)
    tags = fq_table(_session, TABLE_COST_TAGS)
    d = int(days)
    win = f"w.USAGE_DATE >= DATEADD('day', -{d}, CURRENT_DATE())"
    if dim_key == "user":
        sql = (f"SELECT w.USER_NAME AS GROUP_KEY, SUM(w.WAREHOUSE_CREDITS) AS WH "
               f"FROM {wh} w WHERE {win} GROUP BY 1")
    elif dim_key == "surface":
        sql = (f"SELECT w.SURFACE AS GROUP_KEY, SUM(w.WAREHOUSE_CREDITS) AS WH "
               f"FROM {wh} w WHERE {win} GROUP BY 1")
    elif dim_key == "cohort":
        sql = (f"WITH uc AS (SELECT USER_NAME, MAX(COHORT_ROLE) AS COHORT_ROLE "
               f"FROM {usage} GROUP BY USER_NAME) "
               f"SELECT COALESCE(uc.COHORT_ROLE, '(none)') AS GROUP_KEY, "
               f"SUM(w.WAREHOUSE_CREDITS) AS WH FROM {wh} w "
               f"LEFT JOIN uc ON uc.USER_NAME = w.USER_NAME WHERE {win} GROUP BY 1")
    elif dim_key == "vertical":
        sql = (f"SELECT COALESCE(t.VERTICAL, 'Untagged') AS GROUP_KEY, "
               f"SUM(w.WAREHOUSE_CREDITS) AS WH FROM {wh} w "
               f"LEFT JOIN {tags} t ON t.USER_NAME = w.USER_NAME WHERE {win} GROUP BY 1")
    else:  # partner
        sql = (f"SELECT CASE WHEN t.IS_PARTNER THEN 'Partner' ELSE 'Non-partner' END "
               f"AS GROUP_KEY, SUM(w.WAREHOUSE_CREDITS) AS WH FROM {wh} w "
               f"LEFT JOIN {tags} t ON t.USER_NAME = w.USER_NAME WHERE {win} GROUP BY 1")
    try:
        df = _session.sql(sql).to_pandas()
        if df.empty:
            return {}
        df.columns = [c.upper() for c in df.columns]
        return {str(k): float(v or 0) for k, v in zip(df["GROUP_KEY"], df["WH"])}
    except Exception:
        return {}


# Cost-tag sync + editor + save live in tagging.py now (shared with Attribution & Tags).





# ─────────────────────────────── Preset helper ───────────────────────────────
def _select_model(key):
    """Preset click → set the selected model + pre-fill dimension/audience knobs."""
    m = MODEL_PRESETS.get(key)
    if not m:
        return
    st.session_state["cb_model"] = key
    st.session_state["cb_dim"] = m["dimension"]
    st.session_state["cb_audience_label"] = (
        "External · invoice" if m["audience"] == "external" else "Internal · showback")


# ─────────────────────────────── Render ──────────────────────────────────────
def render(session):
    st.header("Chargeback",
              help="Guided, exportable bill for cross-charging Cortex + compute spend "
                   "to a customer, business unit, or partner engagement.")

    ai_rate = float(get_app_setting(session, "USD_PER_CREDIT", "2.00"))
    wh_rate = float(get_app_setting(session, "WAREHOUSE_USD_PER_CREDIT", "3.00"))
    ensure_tags_table(session)
    tags_ready = tags_populated(session)

    # ── Tag editor ────────────────────────────────────────────────────────────
    render_tag_editor(session, key_prefix="cb")
    st.caption("New to tagging? The **Attribution & Tags** page has the full guide — how the "
               "waterfall works, all three identity levers, and an advanced project-level option.")

    # ── Presets (start from a model) ─────────────────────────────────────────
    if "cb_model" not in st.session_state:
        _select_model("M1")  # default; also pre-fills dimension + audience
    sel_model = st.session_state.get("cb_model", "M1")
    with st.container(border=True):
        st.markdown("#### Choose your chargeback model")
        st.caption("Pick the scenario that matches how CoCo is being used — this pre-fills the "
                   "bill; every knob below stays editable. Customer- and partner-agnostic.")
        pcols = st.columns(len(MODEL_PRESETS))
        for col, key in zip(pcols, MODEL_PRESETS):
            m = MODEL_PRESETS[key]
            selected = sel_model == key
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"<div class='cc-model{' cc-model-sel' if selected else ''}'>"
                        f"<span class='cc-model-badge'>{m['badge']}</span>"
                        f"<span class='cc-model-title'>{m['title']}</span></div>"
                        f"<div class='cc-model-tag'>{m['tagline']}</div>"
                        f"<div class='cc-model-desc'>{m['description']}</div>",
                        unsafe_allow_html=True)
                    with st.popover("When to use this", use_container_width=True):
                        st.markdown(f"**{m['badge']} · {m['title']}**")
                        st.write(m["description"])
                        st.markdown(f"<div class='cc-flow'>{m['flow']}</div>",
                                    unsafe_allow_html=True)
                        aud = ("External invoice (margin allowed)"
                               if m["audience"] == "external" else "Internal showback (at cost)")
                        st.caption(f"Default grain: {get_dimension(m['dimension'])['label']}"
                                   f"  ·  {aud}")
                        if m.get("caveat"):
                            st.info(m["caveat"])
                    st.button("✓ Selected" if selected else "Select",
                              key=f"cb_model_{key}",
                              type=("primary" if selected else "secondary"),
                              use_container_width=True,
                              on_click=_select_model, args=(key,))

    # ── ① Bill by ───────────────────────────────────────────────────────────
    dim_keys = [d["key"] for d in ATTRIBUTION_DIMENSIONS]

    def _fmt(k):
        d = get_dimension(k)
        return d["label"] + ("   ·  needs tags" if d["gated"] and not tags_ready else "")

    c1, c2 = st.columns([1.4, 2])
    with c1:
        dim_key = st.selectbox("① Bill by", dim_keys, format_func=_fmt, key="cb_dim",
                               help="Adjust any knob below to customize the selected model.")
    d = get_dimension(dim_key)

    # ── ② Scope ───────────────────────────────────────────────────────────────
    is_service = d["source"] == "metering"
    if is_service:
        months = _load_months(session)
        if not months:
            st.info("No metering data available (METERING_DAILY_HISTORY empty or inaccessible).")
            return
        with c2:
            sc1, sc2 = st.columns(2)
            with sc1:
                period = st.selectbox("② Billing month", months, index=0, key="cb_month")
            with sc2:
                opts = _load_distinct_values(session, dim_key)
                include = st.multiselect("Include services (blank = all)", opts, key="cb_inc_svc")
    else:
        with c2:
            sc1, sc2 = st.columns(2)
            with sc1:
                period = st.selectbox("② Lookback (days)", [7, 14, 30, 60, 90],
                                      index=2, key="cb_days")
            with sc2:
                opts = _load_distinct_values(session, dim_key) if not (d["gated"] and not tags_ready) else []
                include = st.multiselect("Include (blank = all)", opts, key="cb_inc_gen")

    # ── ③ Audience ──────────────────────────────────────────────────────────
    # M1 (Internal Cross-Charge) is always at-cost showback — no external invoice
    # or margin, since teams don't upcharge each other internally.
    if sel_model == "M1":
        audience = "internal"
        upcharge = 0.0
        st.radio("③ Audience", ["Internal · showback"], index=0,
                 key="cb_audience_m1", horizontal=True, disabled=True,
                 help="Internal Cross-Charge is always at-cost showback — no margin.")
    else:
        a1, a2 = st.columns([1.5, 1])
        with a1:
            aud_label = st.radio("③ Audience", ["Internal · showback", "External · invoice"],
                                 key="cb_audience_label", horizontal=True)
        audience = "external" if aud_label.startswith("External") else "internal"
        with a2:
            upcharge = st.number_input("Margin %", min_value=0.0, max_value=100.0,
                                       value=0.0, step=5.0, key="cb_upcharge",
                                       disabled=(audience != "external"),
                                       help="Partner/SI margin — external only.")
        if audience != "external":
            upcharge = 0.0

    # ── Rates + what's billed ─────────────────────────────────────────────────
    wh_applicable = (not is_service) and dim_key != "model"
    include_wh = False
    r1, r2, r3 = st.columns([1, 1.15, 1])
    with r1:
        ai_rate = st.number_input(
            "AI credit rate ($/credit)", min_value=0.01, max_value=20.0,
            value=round(ai_rate, 2), step=0.05, format="%.2f", key="cb_ai_rate",
            help="April 2025 flat AI list price: $2.00 global / $2.20 in-region. Edit for a "
                 "negotiated rate. Default comes from Settings.")
    with r2:
        if wh_applicable:
            include_wh = st.checkbox(
                "Include SQL / warehouse cost", value=False, key="cb_include_wh",
                help="OFF (default): bill LLM token credits only — the norm for delivery "
                     "engagements. ON: also bill the warehouse/compute credits CoCo consumed, "
                     "priced at your contract credit rate.")
        elif is_service:
            st.write(""); st.caption("Service metering already includes compute.")
        else:
            st.write(""); st.caption("Model dimension: token credits only.")
    with r3:
        if include_wh:
            wh_rate = st.number_input(
                "Warehouse credit rate ($/credit)", min_value=0.01, max_value=20.0,
                value=round(wh_rate, 2), step=0.25, format="%.2f", key="cb_wh_rate",
                help="Your contract credit rate (list $3.00). Applied to warehouse/compute "
                     "credits only.")

    bill_to = invoice_no = prepared_by = ""
    if audience == "external":
        e1, e2, e3 = st.columns([1.6, 1, 1])
        with e1:
            bill_to = st.text_input("Bill to (entity)", value="",
                                    placeholder="Customer / business unit / engagement",
                                    key="cb_bill_to")
        with e2:
            invoice_no = st.text_input("Invoice #", value=f"CC-{period}", key="cb_invoice_no")
        with e3:
            prepared_by = st.text_input("Prepared by", value="", key="cb_prepared_by",
                                        placeholder="Your name / team")
    else:
        # Internal showback (M1, or any model switched to Internal) still names a
        # recipient — feeds the PDF's "PREPARED FOR" header via meta["prepared_by"].
        prepared_by = st.text_input(
            "Prepared for (team / business unit)", value="",
            placeholder="e.g., Data Platform team, Finance BU", key="cb_prepared_for",
            help="Who this internal showback is for — appears as 'Prepared for' on the PDF.")

    # Gated dimension without tags → stop before generating.
    if d["gated"] and not tags_ready:
        st.warning("**" + d["label"] + "** needs cost tags. Open *Set up cost tags* above, "
                   "add at least one vertical/partner-flag, and save — then this dimension "
                   "generates a bill.")
        return

    # Phase-2 caveat for the selected model (e.g. M2 engagement proxy).
    _caveat = MODEL_PRESETS.get(st.session_state.get("cb_model", ""), {}).get("caveat")
    if _caveat:
        st.info(_caveat)

    st.divider()

    # ── ④ Generate ────────────────────────────────────────────────────────────
    bill = _load_attributed_bill(session, dim_key, period, tuple(include))
    if bill.empty:
        st.info(f"No billable usage found for this scope.")
        return

    # Combine LLM token credits with warehouse/SQL compute credits so the bill is
    # the FULL cost of CoCo (tokens + compute), not tokens alone. Warehouse credits
    # are rolled up by the same group key (user-derivable dims only). 'service' is
    # already compute-inclusive; 'model' has no warehouse split.
    wh_map = {} if is_service else _load_warehouse_by_dim(session, dim_key, int(period))
    bill["TOKEN_CREDITS"] = bill["CREDITS"].astype(float)
    bill["WH_CREDITS"] = (bill["GROUP_KEY"].astype(str).map(wh_map)
                          .fillna(0.0).astype(float).round(6))
    # Billed credit total: tokens always; warehouse only when the user opts in.
    # WH_CREDITS is retained for transparency display regardless of the toggle.
    _wh_bill = bill["WH_CREDITS"] if include_wh else 0.0
    bill["CREDITS"] = (bill["TOKEN_CREDITS"] + _wh_bill).round(6)

    # Two-rate pricing: AI credits flat-priced, warehouse at contract rate. Service
    # (metering) is a single whole-account pool priced at the contract credit rate.
    if is_service:
        bill["USD"] = (bill["TOKEN_CREDITS"] * wh_rate).round(2)
    else:
        bill["USD"] = (bill["TOKEN_CREDITS"] * ai_rate
                       + (bill["WH_CREDITS"] * wh_rate if include_wh else 0.0)).round(2)
    mult = 1.0 + upcharge / 100.0
    bill["BILLED_USD"] = (bill["USD"] * mult).round(2)

    total_cr   = float(bill["CREDITS"].sum())
    total_tok  = float(bill["TOKEN_CREDITS"].sum())
    total_wh   = float(bill["WH_CREDITS"].sum())
    total_usd  = float(bill["USD"].sum())
    billed     = float(bill["BILLED_USD"].sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Credits", f"{total_cr:,.2f}",
              help="LLM tokens + warehouse/SQL compute")
    k2.metric("Cost (USD)", f"${total_usd:,.2f}")
    if audience == "external":
        k3.metric(f"Billed (+{upcharge:.0f}%)", f"${billed:,.2f}")
    else:
        k3.metric("Showback (at cost)", f"${billed:,.2f}")
    k4.metric("Line Items", f"{len(bill)}")

    _wh_usd = total_wh * wh_rate
    if include_wh and total_wh > 0:
        st.caption(f"Composition: **{total_tok:,.2f}** token cr (${total_tok * ai_rate:,.2f}) + "
                   f"**{total_wh:,.4f}** warehouse cr (${_wh_usd:,.2f}) = **${total_usd:,.2f}**.")
    elif wh_applicable and total_wh > 0:
        st.caption(f"Billing **token credits only**. Warehouse/SQL compute of "
                   f"**{total_wh:,.4f}** cr (~${_wh_usd:,.2f}) is shown for transparency but "
                   f"**not billed** — enable *Include SQL / warehouse cost* above to add it.")
    elif is_service:
        st.caption("Service dimension bills whole-account metering at your contract "
                   "credit rate (already includes warehouse compute).")
    elif dim_key == "model":
        st.caption("Model dimension: token credits only (no per-model warehouse split). "
                   "Use By User / Surface / Vertical to include compute.")

    st.divider()

    # Service dimension keeps the richer category + MoM visuals.
    if is_service:
        bill["CATEGORY"] = bill["GROUP_KEY"].map(_CATEGORY).fillna("Other")
        _sec("By Category")
        cat = (bill.groupby("CATEGORY", as_index=False)
                  .agg(CREDITS=("CREDITS", "sum"), BILLED_USD=("BILLED_USD", "sum")))
        cat["CREDITS"] = cat["CREDITS"].round(2)
        ch = (alt.Chart(cat).mark_bar()
              .encode(x=alt.X("BILLED_USD:Q", title="Billed USD"),
                      y=alt.Y("CATEGORY:N", sort="-x", title=""),
                      color=alt.value(_O),
                      tooltip=["CATEGORY:N", alt.Tooltip("CREDITS:Q", format=".2f"),
                               alt.Tooltip("BILLED_USD:Q", format="$.2f")])
              .properties(height=max(140, len(cat) * 40))
              .configure_view(strokeWidth=0).configure(background=_BG))
        st.altair_chart(ch, use_container_width=True)

        trend = _load_month_trend(session)
        if not trend.empty:
            _sec("Month-over-Month Total Credits")
            ch2 = (alt.Chart(trend).mark_line(point=True)
                   .encode(x=alt.X("MONTH:N", title=""),
                           y=alt.Y("CREDITS:Q", title="Credits"),
                           color=alt.value(_P),
                           tooltip=["MONTH:N", alt.Tooltip("CREDITS:Q", format=".2f")])
                   .properties(height=240)
                   .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch2, use_container_width=True)
    else:
        _sec(f"Top by Cost — {d['label']}")
        top = bill.sort_values("BILLED_USD", ascending=False).head(20)
        ch = (alt.Chart(top).mark_bar()
              .encode(x=alt.X("BILLED_USD:Q", title="Billed USD"),
                      y=alt.Y("GROUP_KEY:N", sort="-x", title=""),
                      color=alt.value(_G),
                      tooltip=["GROUP_KEY:N", alt.Tooltip("CREDITS:Q", format=".4f"),
                               alt.Tooltip("BILLED_USD:Q", format="$.2f")])
              .properties(height=max(160, len(top) * 30))
              .configure_view(strokeWidth=0).configure(background=_BG))
        st.altair_chart(ch, use_container_width=True)

    # Itemized table
    _sec(f"Itemized {'Invoice' if audience == 'external' else 'Showback'} — {d['label']}")
    key_title = d["label"].replace("By ", "")
    cols = ["GROUP_KEY"]
    colcfg = {"GROUP_KEY": st.column_config.TextColumn(key_title)}
    if "REQUESTS" in bill.columns:
        cols += ["REQUESTS", "TOKENS"]
        colcfg["REQUESTS"] = st.column_config.NumberColumn("Requests")
        colcfg["TOKENS"] = st.column_config.NumberColumn("Tokens")
    if include_wh and total_wh > 0:
        cols += ["TOKEN_CREDITS", "WH_CREDITS"]
        colcfg["TOKEN_CREDITS"] = st.column_config.NumberColumn("Token cr", format="%.4f")
        colcfg["WH_CREDITS"] = st.column_config.NumberColumn("WH cr", format="%.4f")
    cols += ["CREDITS", "USD", "BILLED_USD"]
    colcfg["CREDITS"] = st.column_config.NumberColumn("Total cr", format="%.4f")
    colcfg["USD"] = st.column_config.NumberColumn("Cost USD", format="$%.2f")
    colcfg["BILLED_USD"] = st.column_config.NumberColumn(
        "Billed USD" if audience == "external" else "Amount USD", format="$%.2f")
    inv = bill[cols].copy()
    st.dataframe(inv, use_container_width=True, hide_index=True, column_config=colcfg)

    # Export
    csv = inv.to_csv(index=False).encode("utf-8")
    dl1, dl2 = st.columns(2)
    with dl1:
        if st.download_button("Download CSV", data=csv,
                              file_name=f"coco_chargeback_{dim_key}_{period}.csv",
                              mime="text/csv", key="cb_dl_csv", use_container_width=True):
            log_activity(session, "CHARGEBACK_EXPORT",
                         details={"dimension": dim_key, "audience": audience,
                                  "format": "csv", "period": str(period),
                                  "billed_usd": round(billed, 2)})
    with dl2:
        from datetime import date, timedelta
        pdf_bytes = None
        pdf_err = None
        try:
            if is_service:
                period_label = str(period)
            else:
                _end = date.today()
                _start = _end - timedelta(days=int(period))
                period_label = (f"{_start.strftime('%b %d')} - "
                                f"{_end.strftime('%b %d, %Y')}  ({int(period)}d)")
            _model = MODEL_PRESETS.get(
                st.session_state.get("cb_model", ""), {}).get("title", "")
            _src = ("SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY" if is_service
                    else "Cortex Code usage + warehouse attribution")
            meta = {
                "external": audience == "external",
                "dimension_key_title": d["label"].replace("By ", ""),
                "attribution": d["label"],
                "adoption_model": _model,
                "is_service": is_service,
                "period_label": period_label,
                "issued": date.today().isoformat(),
                "invoice_no": (invoice_no or f"CC-{period}"),
                "bill_to": bill_to,
                "prepared_by": prepared_by,
                "usd_rate": ai_rate,
                "wh_rate": wh_rate,
                "upcharge_pct": upcharge,
                "subtotal_usd": total_usd,
                "billed_usd": billed,
                "total_credits": total_cr,
                "total_token_credits": total_tok,
                "total_wh_credits": (total_wh if include_wh else 0.0),
                "footer_note": f"Confidential - chargeback use.   Source: {_src}.",
            }
            # Sanitize bill for PDF: coerce numerics + drop NaN so fpdf2 formatting
            # (`f"{x:,.2f}"`) never sees a NaN which prints "nan" and can trip newer
            # fpdf2 versions when combined with cell width calculations.
            _bill_pdf = bill.copy()
            for _c in ("CREDITS", "USD", "BILLED_USD", "TOKEN_CREDITS", "WH_CREDITS"):
                if _c in _bill_pdf.columns:
                    _bill_pdf[_c] = pd.to_numeric(_bill_pdf[_c], errors="coerce").fillna(0.0)
            pdf_bytes = _build_invoice_pdf(_bill_pdf, meta)
        except Exception as e:
            import traceback
            pdf_err = f"{type(e).__name__}: {e}"
            _tb = traceback.format_exc()

        fname = (f"coco_invoice_{(invoice_no or period)}.pdf" if audience == "external"
                 else f"coco_showback_{dim_key}_{period}.pdf").replace("/", "-")
        btn_label = "Download Chargeback PDF"
        if pdf_bytes is not None:
            if st.download_button(btn_label, data=pdf_bytes, file_name=fname,
                                  mime="application/pdf", key="cb_dl_pdf",
                                  type="primary", use_container_width=True):
                log_activity(session, "CHARGEBACK_EXPORT",
                             details={"dimension": dim_key, "audience": audience,
                                      "format": "pdf", "period": str(period),
                                      "invoice_no": invoice_no, "bill_to": bill_to,
                                      "upcharge_pct": upcharge, "billed_usd": round(billed, 2)})
        else:
            st.button(btn_label, key="cb_dl_pdf_disabled", disabled=True,
                      use_container_width=True)
            st.error(f"PDF generation failed — {pdf_err}")
            with st.expander("Traceback"):
                st.code(_tb, language="text")

import streamlit as st
from snowflake.snowpark import Session
from cryptography.hazmat.primitives import serialization
from datetime import datetime
from zoneinfo import ZoneInfo
import plotly.express as px

# ── Connection ────────────────────────────────────────────────────────────────
# Key-pair auth
# Reuses the same RSA key pair already registered for the Firehose→Snowflake
# fast path (the key pair you generated for Firehose) — no separate key needed.
#
# Cached so the session is created once and reused across all fragment reruns.
# Without @st.cache_resource every 10-second fragment refresh would open a new
# connection, which would be wasteful 
@st.cache_resource
def get_session() -> Session:
    cfg = dict(st.secrets["snowflake"])
    key_path = cfg.pop("private_key_path")

    with open(key_path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(key_file.read(), password=None)

    cfg["private_key"] = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return Session.builder.configs(cfg).create()

session = get_session()

# ── Colour constants ──────────────────────────────────────────────────────────
TIER_COLORS = {
    "FLOOR": "#D4AF37",   # gold border
    "LOWER": "#4A90D9",   # blue border
    "UPPER": "#9B59B6",   # purple border
}
AVAILABLE_COLOR = "#2ECC71"   # green seat
SOLD_COLOR      = "#4a4a4a"   # dark gray seat

# Section → tier lookup, mirrors producer.py's PRICE_TIERS layout. Lets the
# "Revenue by Section" chart color each bar to match the seat map's tier
# borders, instead of one flat default color.
SECTION_TIER = {}
for _s in "ABCD":     SECTION_TIER[_s] = "FLOOR"
for _s in "EFGHIJKL": SECTION_TIER[_s] = "LOWER"
for _s in "MNOP":     SECTION_TIER[_s] = "UPPER"

# ── Section layout: horseshoe around a stage ──────────────────────────────────
# Plain CSS grid, no curves/SVG — sections keep their existing rectangular
# shape, just repositioned so FLOOR (closest/priciest) flanks the stage,
# LOWER forms two side rings, and UPPER sits at the back — same price
# geography as a real venue, without any wedge/coordinate geometry.
# (row, col_start, col_span) on an 8-column grid.
SECTION_LAYOUT = {
    "M": (1, 1, 2), "N": (1, 3, 2), "O": (1, 5, 2), "P": (1, 7, 2),   # UPPER · back row
    "E": (2, 1, 1), "F": (2, 2, 1),                 "G": (2, 7, 1), "H": (2, 8, 1),  # LOWER · outer side ring
    "I": (3, 1, 1), "J": (3, 2, 1),                 "K": (3, 7, 1), "L": (3, 8, 1),  # LOWER · inner side ring
    "A": (4, 1, 1), "B": (4, 2, 1),                 "C": (4, 7, 1), "D": (4, 8, 1),  # FLOOR · flanks the stage
}
STAGE_ROW, STAGE_COL_START, STAGE_COL_SPAN = 4, 3, 4

# ── Seat map renderer ─────────────────────────────────────────────────────────
def render_seat_map(seats_df, pulse_class=""):
    # Built entirely from single-line f-strings — no embedded newlines. A
    # multi-line triple-quoted block ending in trailing whitespace once left
    # a whitespace-only line between fragments, which Markdown treats as a
    # blank line that terminates the raw-HTML block early (everything after
    # got re-parsed as an indented code block instead of HTML). Keeping this
    # all on one line per fragment makes that class of bug impossible.
    html = f"<div class='{pulse_class}' style='display:grid; grid-template-columns:repeat(8, 1fr); gap:10px; border-radius:8px;'>"

    html += (
        f"<div style='grid-row:{STAGE_ROW}; grid-column:{STAGE_COL_START} / span {STAGE_COL_SPAN}; "
        f"display:flex; align-items:center; justify-content:center; "
        f"background:#000; border:2px solid #555; border-radius:8px; "
        f"color:#ccc; font-weight:bold; letter-spacing:2px;'>STAGE</div>"
    )

    for section, (row, col_start, col_span) in SECTION_LAYOUT.items():
        if section not in seats_df["SECTION"].unique():
            continue
        sec_df = (
            seats_df[seats_df["SECTION"] == section]
            .sort_values(["ROW_NUMBER", "SEAT_NUMBER"])
        )
        tier         = sec_df["PRICE_TIER"].iloc[0]
        border_color = TIER_COLORS.get(tier, "#888")
        html += (
            f"<div style='grid-row:{row}; grid-column:{col_start} / span {col_span}; "
            f"border:2px solid {border_color}; border-radius:8px; padding:8px; background:#111;'>"
            f"<div style='text-align:center; color:{border_color}; font-weight:bold; "
            f"font-size:13px; margin-bottom:6px;'>Section {section} · {tier}</div>"
            f"<div style='display:grid; grid-template-columns:repeat(10, 1fr); gap:2px;'>"
        )
        for _, seat in sec_df.iterrows():
            color = AVAILABLE_COLOR if seat["STATUS"] == "AVAILABLE" else SOLD_COLOR
            html += (
                f"<div style='aspect-ratio:1; background:{color}; "
                f"border-radius:2px;'></div>"
            )
        html += "</div></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ── Global styling: pulsing "live" indicator dot ────────────────────────────────
# CSS-only animation — no custom component needed, no repeated toast spam.
st.markdown("""
<style>
@keyframes pulse { 0% {opacity:1;} 50% {opacity:0.25;} 100% {opacity:1;} }
.live-dot {
    display:inline-block; width:8px; height:8px; border-radius:50%;
    background:#2ECC71; margin-right:6px; animation:pulse 1.5s infinite;
}
/* Metrics status line: square, darker green, and static (no pulse) — a
   deliberately calmer indicator than the seat map's live-dot, since this
   panel refreshes far less often and isn't a real-time signal the same way. */
.metrics-dot {
    display:inline-block; width:8px; height:8px; border-radius:2px;
    background:#1B5E20; margin-right:6px;
}

/* Seat map: brief green glow around the whole grid, only fired when the
   sold count actually changes between polls (see pulse= param below) —
   not on every 10s refresh, most of which see no change.
   Two identical keyframes/classes, alternated each time a change fires
   (see pulse_toggle below) — reusing the exact same class string on back
   -to-back triggers can get deduped by the browser/React and silently
   skip the replay, so every real change gets a genuinely different
   class name instead of relying on remove-then-reapply of the same one. */
@keyframes seatmap-glow-a {
    0%   { box-shadow: 0 0 0 0 rgba(46,204,113,0.6); }
    100% { box-shadow: 0 0 0 14px rgba(46,204,113,0); }
}
@keyframes seatmap-glow-b {
    0%   { box-shadow: 0 0 0 0 rgba(46,204,113,0.6); }
    100% { box-shadow: 0 0 0 14px rgba(46,204,113,0); }
}
.seatmap-pulse-a { animation: seatmap-glow-a 0.9s ease-out; }
.seatmap-pulse-b { animation: seatmap-glow-b 0.9s ease-out; }

/* KPI cards: quick white flash, only fired when that specific value changed
   since the last poll (see changed= param on render_kpi_card below). */
@keyframes kpi-flash { 0% { background-color: rgba(255,255,255,0.35); } 100% { background-color: rgba(255,255,255,0); } }
.kpi-card {
    border: 1px solid rgba(250,250,250,0.2); border-radius:8px;
    padding:14px 16px; margin-bottom:10px;
}
.kpi-flash { animation: kpi-flash 0.8s ease-out; }
.kpi-label { font-size:13px; color:#a0a0a0; margin-bottom:4px; }
.kpi-value { font-size:28px; font-weight:600; color:#fafafa; }
.kpi-delta-up   { font-size:13px; color:#2ECC71; margin-top:2px; }
.kpi-delta-down { font-size:13px; color:#E74C3C; margin-top:2px; }
.kpi-delta-flat { font-size:13px; color:#888; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

# ── KPI card renderer ─────────────────────────────────────────────────────────
# Renders one KPI as plain HTML (instead of st.metric) so we can attach the
# .kpi-flash class conditionally — only when this specific value changed
# since the last poll, not on every fragment rerun.
def render_kpi_card(label, value, delta=None, changed=False):
    flash_class = "kpi-flash" if changed else ""
    delta_html = ""
    if delta is not None:
        if delta > 0:
            delta_html = f"<div class='kpi-delta-up'>▲ {delta}</div>"
        elif delta < 0:
            delta_html = f"<div class='kpi-delta-down'>▼ {delta}</div>"
        else:
            # Gold has a 60s TARGET_LAG but this panel polls every 20s, so
            # most polls land before Gold has actually refreshed — a flat
            # delta usually means "no new data yet," not "confirmed stable."
            delta_html = "<div class='kpi-delta-flat'>· awaiting refresh</div>"
    st.markdown(
        f"""
        <div class='kpi-card {flash_class}'>
          <div class='kpi-label'>{label}</div>
          <div class='kpi-value'>{value}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Ticketing Pipeline — Live")
st.title("The Rolling Queries | Frisco Arena")
st.caption("Live ticket sellout · AWS × Snowflake real-time pipeline demo")

# ── Row 1: Seat map, full width — the biggest element on the page ──────────────
@st.fragment(run_every="10s")
def seat_map_fragment():
    local_time = datetime.now(ZoneInfo("America/Chicago")).strftime("%I:%M:%S %p")
    st.markdown(
        # ~10s: matches the Task's 10s trigger floor and this panel's
        # 10s polling interval.
        f"~10s latency <span class='live-dot'></span>Seat map · refreshed {local_time} CT",
        unsafe_allow_html=True,
    )

    seats_df   = session.table("ticketing_db.pipeline.seats").to_pandas()
    sold_count = (seats_df["STATUS"] == "SOLD").sum()

    # Pulse only if sold_count actually moved since the last 10s poll —
    # most polls during a lull see no change, so no pulse should fire.
    prev_sold_count = st.session_state.get("prev_sold_count", sold_count)
    seats_changed   = sold_count != prev_sold_count
    st.session_state["prev_sold_count"] = sold_count

    # Alternate class name on every real change (a/b) rather than
    # reapplying the same "seatmap-pulse" string each time — see the
    # comment above the keyframes for why that was silently no-op'ing
    # after the first pulse.
    pulse_class = ""
    if seats_changed:
        toggle = not st.session_state.get("pulse_toggle", False)
        st.session_state["pulse_toggle"] = toggle
        pulse_class = "seatmap-pulse-a" if toggle else "seatmap-pulse-b"

    st.metric("Seats Sold", f"{sold_count} / 320")
    with st.container(border=True):
        render_seat_map(seats_df, pulse_class=pulse_class)

seat_map_fragment()

# Single horizontal divider, full width, separating the seat map from the
# metrics section below — no vertical divider anymore, clean stacked layout.
st.markdown(
    "<div style='border-top:1px solid rgba(250,250,250,0.35); margin:20px 0;'></div>",
    unsafe_allow_html=True,
)

# ── Row 2: KPI cards, three across ──────────────────────────────────────────────
@st.fragment(run_every="30s")
def kpi_fragment():
    local_time = datetime.now(ZoneInfo("America/Chicago")).strftime("%I:%M:%S %p")
    st.markdown(
        # ~60s: matches Gold's 60-second TARGET_LAG, the Dynamic Tables'
        # minimum. This panel polls every 30s, but data only changes when
        # Gold refreshes.
        f"~60s latency <span class='metrics-dot'></span>Metrics · refreshed {local_time} CT",
        unsafe_allow_html=True,
    )

    gold_df = session.table(
        "ticketing_db.pipeline.gold_section_metrics"
    ).to_pandas()

    # Gold is grouped by (section, channel) — sum across both for venue-wide
    # totals. Empty right after reset_demo() (no rows until the first sale);
    # .sum() on an empty column is 0, guarded by the ternaries below.
    total_revenue = gold_df["TOTAL_REVENUE"].sum()
    total_sold    = gold_df["TICKETS_SOLD"].sum()
    sellout_pct   = round((total_sold / 320) * 100, 1) if total_sold else 0
    avg_price     = round(total_revenue / total_sold, 2) if total_sold else 0

    # Deltas + flash triggers vs. the previous poll, stored in
    # session_state. Defaults to the current value on first load so
    # there's no false initial spike/flash.
    prev_revenue   = st.session_state.get("prev_revenue", total_revenue)
    prev_sellout   = st.session_state.get("prev_sellout", sellout_pct)
    prev_avg_price = st.session_state.get("prev_avg_price", avg_price)
    st.session_state["prev_revenue"]   = total_revenue
    st.session_state["prev_sellout"]   = sellout_pct
    st.session_state["prev_avg_price"] = avg_price

    # Each card flashes independently — only the KPIs that actually
    # moved this poll get the white flash, not all three every time.
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        render_kpi_card(
            "Total Revenue", f"${total_revenue:,.2f}",
            delta=round(total_revenue - prev_revenue, 2),
            changed=(total_revenue != prev_revenue),
        )
    with col_kpi2:
        render_kpi_card(
            "Sellout %", f"{sellout_pct}%",
            delta=round(sellout_pct - prev_sellout, 1),
            changed=(sellout_pct != prev_sellout),
        )
    with col_kpi3:
        render_kpi_card(
            "Avg Ticket Price", f"${avg_price:,.2f}",
            changed=(avg_price != prev_avg_price),
        )

kpi_fragment()

# ── Row 3: charts, two across, sitting directly below the KPI row ──────────────
@st.fragment(run_every="30s")
def charts_fragment():
    gold_df = session.table("ticketing_db.pipeline.gold_section_metrics").to_pandas()

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Revenue by Section")
        if gold_df.empty:
            st.info("No sales yet.")
        else:
            section_df = gold_df.groupby("SECTION", as_index=False)["TOTAL_REVENUE"].sum()
            section_df["TIER"] = section_df["SECTION"].map(SECTION_TIER)
            fig = px.bar(
                section_df, x="SECTION", y="TOTAL_REVENUE", color="TIER",
                color_discrete_map=TIER_COLORS,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="white", showlegend=False, margin=dict(t=10, b=10),
                transition={"duration": 500, "easing": "cubic-in-out"},
            )
            # Stable key so Streamlit reuses this same chart instance across
            # fragment reruns instead of tearing it down and remounting a
            # fresh one — without that, Plotly's transition has no "before"
            # state to animate from and just snaps instead.
            st.plotly_chart(fig, use_container_width=True, key="revenue_chart")

    with col_chart2:
        st.subheader("Sales by Channel")
        if gold_df.empty:
            st.info("No sales yet.")
        else:
            channel_df    = gold_df.groupby("CHANNEL", as_index=False)["TICKETS_SOLD"].sum()
            total_tickets = channel_df["TICKETS_SOLD"].sum()
            fig2 = px.pie(channel_df, names="CHANNEL", values="TICKETS_SOLD", hole=0.5)
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                margin=dict(t=10, b=10),
                annotations=[dict(
                    text=f"{total_tickets}<br>tickets", x=0.5, y=0.5,
                    showarrow=False, font_size=14,
                )],
                transition={"duration": 500, "easing": "cubic-in-out"},
            )
            st.plotly_chart(fig2, use_container_width=True, key="channel_chart")

charts_fragment()
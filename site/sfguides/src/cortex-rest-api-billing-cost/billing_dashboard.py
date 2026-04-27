import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Cortex REST API Billing & Cost", layout="wide")

session = get_active_session()

# Example fallback rates (USD per 1M tokens). For actual current pricing,
# consult the Snowflake Service Consumption Table:
# https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf
FALLBACK_PRICING = {"input": 2.00, "cached_input": 0.20, "output": 8.00}

@st.cache_data(ttl=3600)
def load_pricing_from_table():
    pricing = {}
    try:
        df = session.sql("""
            SELECT MODEL_NAME, SOURCE_TABLE,
                   INPUT_PRICE_PER_1M_TOKENS, OUTPUT_PRICE_PER_1M_TOKENS,
                   CACHE_READ_PRICE_PER_1M_TOKENS
            FROM SNOW_INTELLIGENCE_DEMO.CREDIT_CONSUMPTION.CORTEX_AI_PRICING
            WHERE SOURCE_TABLE IN ('6b', '6c')
        """).to_pandas()
        for _, row in df.iterrows():
            model = row["MODEL_NAME"].lower()
            inp = float(row["INPUT_PRICE_PER_1M_TOKENS"] or 0)
            out = float(row["OUTPUT_PRICE_PER_1M_TOKENS"] or 0)
            cache = float(row["CACHE_READ_PRICE_PER_1M_TOKENS"] or 0)
            pricing[model] = {"input": inp, "cached_input": cache, "output": out}
    except Exception:
        pass
    return pricing

# Example default rates loaded from CORTEX_AI_PRICING table. For actual current
# pricing, consult the Snowflake Service Consumption Table:
# https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf
DEFAULT_PRICING = load_pricing_from_table()

def run_query(sql):
    try:
        return session.sql(sql).to_pandas()
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

def get_pricing(model_name, overrides):
    key = model_name.lower()
    if key in overrides:
        return overrides[key]
    if key in DEFAULT_PRICING:
        return DEFAULT_PRICING[key]
    return FALLBACK_PRICING

st.title("Cortex REST API Billing & Cost Analysis")
st.caption(
    "Estimates based on TOKENS_GRANULAR from "
    "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY. "
    f"Pricing loaded from CORTEX_AI_PRICING table ({len(DEFAULT_PRICING)} models). "
    "Override rates in the sidebar as needed."
)

with st.sidebar:
    st.header("Pricing (USD / 1M tokens)")
    st.caption("Edit rates below. Changes apply on next query run.")

    if "pricing_overrides" not in st.session_state:
        st.session_state["pricing_overrides"] = {}

    pricing_rows = []
    for model, rates in DEFAULT_PRICING.items():
        pricing_rows.append({
            "Model": model,
            "Input": rates["input"],
            "Cached Input": rates["cached_input"],
            "Output": rates["output"],
        })
    pricing_edit_df = pd.DataFrame(pricing_rows)

    edited_pricing = st.data_editor(
        pricing_edit_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="pricing_editor",
    )

    overrides = {}
    for _, row in edited_pricing.iterrows():
        m = str(row["Model"]).strip().lower()
        if m:
            overrides[m] = {
                "input": float(row.get("Input", 0) or 0),
                "cached_input": float(row.get("Cached Input", 0) or 0),
                "output": float(row.get("Output", 0) or 0),
            }
    st.session_state["pricing_overrides"] = overrides

    st.divider()
    st.markdown(
        "**Fallback rate** for unlisted models: "
        f"${FALLBACK_PRICING['input']:.2f} / "
        f"${FALLBACK_PRICING['cached_input']:.2f} / "
        f"${FALLBACK_PRICING['output']:.2f}"
    )

months_back = st.slider("Lookback (months)", 1, 12, 6, key="months_back")

if st.button("Run Cost Analysis", type="primary"):
    with st.spinner("Querying TOKENS_GRANULAR..."):
        monthly_df = run_query(f"""
            SELECT
                DATE_TRUNC('MONTH', START_TIME)::DATE AS MONTH,
                MODEL_NAME,
                SUM(TOKENS_GRANULAR:"input"::NUMBER) AS INPUT_TOKENS,
                SUM(
                    CASE
                        WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) >= 1024
                            THEN TOKENS_GRANULAR:"cache_read_input"::NUMBER
                        ELSE 0
                    END
                ) AS CACHED_INPUT_TOKENS,
                SUM(
                    CASE
                        WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) < 1024
                            THEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0)
                        ELSE 0
                    END
                ) AS NON_CACHED_INPUT_TOKENS,
                SUM(TOKENS_GRANULAR:"output"::NUMBER) AS OUTPUT_TOKENS,
                COUNT(*) AS REQUEST_COUNT
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
            WHERE START_TIME >= DATEADD(month, -{months_back}, CURRENT_TIMESTAMP())
            GROUP BY 1, 2
            ORDER BY 1, 2
        """)

        daily_df = run_query(f"""
            SELECT
                DATE_TRUNC('DAY', START_TIME)::DATE AS DAY,
                MODEL_NAME,
                SUM(TOKENS_GRANULAR:"input"::NUMBER) AS INPUT_TOKENS,
                SUM(
                    CASE
                        WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) >= 1024
                            THEN TOKENS_GRANULAR:"cache_read_input"::NUMBER
                        ELSE 0
                    END
                ) AS CACHED_INPUT_TOKENS,
                SUM(
                    CASE
                        WHEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0) < 1024
                            THEN COALESCE(TOKENS_GRANULAR:"cache_read_input"::NUMBER, 0)
                        ELSE 0
                    END
                ) AS NON_CACHED_INPUT_TOKENS,
                SUM(TOKENS_GRANULAR:"output"::NUMBER) AS OUTPUT_TOKENS
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
            WHERE START_TIME >= DATEADD(month, -{months_back}, CURRENT_TIMESTAMP())
            GROUP BY 1, 2
            ORDER BY 1, 2
        """)

        st.session_state["billing_monthly"] = monthly_df
        st.session_state["billing_daily"] = daily_df

if "billing_monthly" in st.session_state:
    monthly_df = st.session_state["billing_monthly"]
    daily_df = st.session_state["billing_daily"]
    overrides = st.session_state.get("pricing_overrides", {})

    if not monthly_df.empty:
        def compute_costs(df):
            rows = []
            for _, r in df.iterrows():
                p = get_pricing(r["MODEL_NAME"], overrides)
                inp = float(r.get("INPUT_TOKENS") or 0)
                cached = float(r.get("CACHED_INPUT_TOKENS") or 0)
                non_cached = float(r.get("NON_CACHED_INPUT_TOKENS") or 0)
                out = float(r.get("OUTPUT_TOKENS") or 0)

                input_cost = (inp + non_cached) / 1e6 * p["input"]
                cached_cost = cached / 1e6 * p["cached_input"]
                output_cost = out / 1e6 * p["output"]
                cache_savings = cached / 1e6 * (p["input"] - p["cached_input"])

                rows.append({
                    **r.to_dict(),
                    "INPUT_COST": round(input_cost, 4),
                    "CACHED_INPUT_COST": round(cached_cost, 4),
                    "OUTPUT_COST": round(output_cost, 4),
                    "TOTAL_COST": round(input_cost + cached_cost + output_cost, 4),
                    "CACHE_SAVINGS": round(cache_savings, 4),
                })
            return pd.DataFrame(rows)

        costed = compute_costs(monthly_df)

        st.markdown("---")
        st.subheader("Cost Summary")

        total_cost = costed["TOTAL_COST"].sum()
        total_input_cost = costed["INPUT_COST"].sum()
        total_cached_cost = costed["CACHED_INPUT_COST"].sum()
        total_output_cost = costed["OUTPUT_COST"].sum()
        total_savings = costed["CACHE_SAVINGS"].sum()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Est. Cost", f"${total_cost:,.2f}")
        c2.metric("Input Cost", f"${total_input_cost:,.2f}")
        c3.metric("Cached Input Cost", f"${total_cached_cost:,.2f}")
        c4.metric("Output Cost", f"${total_output_cost:,.2f}")
        c5.metric("Cache Savings", f"${total_savings:,.2f}", delta=f"-${total_savings:,.2f}" if total_savings > 0 else None, delta_color="inverse")

        st.divider()

        st.subheader("Monthly Cost Trend")
        monthly_agg = (
            costed.groupby("MONTH")
            .agg(
                INPUT_COST=("INPUT_COST", "sum"),
                CACHED_INPUT_COST=("CACHED_INPUT_COST", "sum"),
                OUTPUT_COST=("OUTPUT_COST", "sum"),
                TOTAL_COST=("TOTAL_COST", "sum"),
            )
            .reset_index()
        )

        melted = monthly_agg.melt(
            id_vars="MONTH",
            value_vars=["INPUT_COST", "CACHED_INPUT_COST", "OUTPUT_COST"],
            var_name="Cost Type",
            value_name="USD",
        )
        chart = (
            alt.Chart(melted)
            .mark_bar()
            .encode(
                x=alt.X("MONTH:T", title="Month"),
                y=alt.Y("USD:Q", title="Estimated Cost (USD)"),
                color=alt.Color("Cost Type:N", scale=alt.Scale(
                    domain=["INPUT_COST", "CACHED_INPUT_COST", "OUTPUT_COST"],
                    range=["#4C78A8", "#72B7B2", "#F58518"],
                )),
                tooltip=["MONTH:T", "Cost Type:N", alt.Tooltip("USD:Q", format="$,.2f")],
            )
            .properties(height=350)
        )
        st.altair_chart(chart, use_container_width=True)

        st.divider()

        st.subheader("Cost by Model")
        model_agg = (
            costed.groupby("MODEL_NAME")
            .agg(
                INPUT_TOKENS=("INPUT_TOKENS", "sum"),
                CACHED_INPUT_TOKENS=("CACHED_INPUT_TOKENS", "sum"),
                OUTPUT_TOKENS=("OUTPUT_TOKENS", "sum"),
                INPUT_COST=("INPUT_COST", "sum"),
                CACHED_INPUT_COST=("CACHED_INPUT_COST", "sum"),
                OUTPUT_COST=("OUTPUT_COST", "sum"),
                TOTAL_COST=("TOTAL_COST", "sum"),
                CACHE_SAVINGS=("CACHE_SAVINGS", "sum"),
                REQUESTS=("REQUEST_COUNT", "sum"),
            )
            .reset_index()
            .sort_values("TOTAL_COST", ascending=False)
        )

        for col in ["INPUT_COST", "CACHED_INPUT_COST", "OUTPUT_COST", "TOTAL_COST", "CACHE_SAVINGS"]:
            model_agg[col] = model_agg[col].apply(lambda x: round(x, 2))
        for col in ["INPUT_TOKENS", "CACHED_INPUT_TOKENS", "OUTPUT_TOKENS", "REQUESTS"]:
            model_agg[col] = model_agg[col].apply(lambda x: int(x))

        st.dataframe(model_agg, use_container_width=True, hide_index=True)

        model_bar = (
            alt.Chart(model_agg)
            .mark_bar()
            .encode(
                x=alt.X("TOTAL_COST:Q", title="Estimated Cost (USD)"),
                y=alt.Y("MODEL_NAME:N", sort="-x", title="Model"),
                color=alt.value("#4C78A8"),
                tooltip=["MODEL_NAME:N", alt.Tooltip("TOTAL_COST:Q", format="$,.2f")],
            )
            .properties(height=max(200, len(model_agg) * 35))
        )
        st.altair_chart(model_bar, use_container_width=True)

        st.divider()

        st.subheader("Daily Cost Drill-Down")
        models = sorted(daily_df["MODEL_NAME"].unique().tolist()) if not daily_df.empty else []
        selected_model = st.selectbox("Select model", ["All Models"] + models, key="daily_model")

        if not daily_df.empty:
            daily_costed = compute_costs(daily_df)
            if selected_model != "All Models":
                daily_costed = daily_costed[daily_costed["MODEL_NAME"] == selected_model]

            daily_agg = (
                daily_costed.groupby("DAY")
                .agg(
                    INPUT_COST=("INPUT_COST", "sum"),
                    CACHED_INPUT_COST=("CACHED_INPUT_COST", "sum"),
                    OUTPUT_COST=("OUTPUT_COST", "sum"),
                    TOTAL_COST=("TOTAL_COST", "sum"),
                )
                .reset_index()
            )

            daily_melted = daily_agg.melt(
                id_vars="DAY",
                value_vars=["INPUT_COST", "CACHED_INPUT_COST", "OUTPUT_COST"],
                var_name="Cost Type",
                value_name="USD",
            )
            daily_chart = (
                alt.Chart(daily_melted)
                .mark_bar()
                .encode(
                    x=alt.X("DAY:T", title="Date"),
                    y=alt.Y("USD:Q", title="Estimated Cost (USD)"),
                    color=alt.Color("Cost Type:N", scale=alt.Scale(
                        domain=["INPUT_COST", "CACHED_INPUT_COST", "OUTPUT_COST"],
                        range=["#4C78A8", "#72B7B2", "#F58518"],
                    )),
                    tooltip=["DAY:T", "Cost Type:N", alt.Tooltip("USD:Q", format="$,.2f")],
                )
                .properties(height=350)
            )
            st.altair_chart(daily_chart, use_container_width=True)
    else:
        st.info("No data found in the selected time range.")

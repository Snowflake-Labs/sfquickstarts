id: liquidity-risk-agent
language: en
summary: Cortex-powered liquidity risk management and LCR forecasting in Snowflake
categories: snowflake-site:taxonomy/industry/financial-services, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/snowflake-notebooks, snowflake-site:taxonomy/snowflake-feature/streamlit
environments: web
status: Published
authors: Nick Windridge, Suraj Rajan, Constantin Stanca, Cameron Shimmin
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-liquidity-risk-agent

# Liquidity Risk Agent: AI-Powered LCR Forecasting with Snowflake

## Overview

This solution provides a comprehensive Cortex-powered system for liquidity risk management, featuring Basel III compliant Liquidity Coverage Ratio (LCR) calculations, 150-day forecasting, what-if scenario analysis, and an AI-powered agent for natural language querying. It demonstrates how financial institutions can transform their liquidity risk workflows by integrating structured position data with intelligent analytics—all powered by Snowflake's native AI capabilities.

The solution implements a complete liquidity risk management system that calculates High-Quality Liquid Assets (HQLA), projects cash flows, and derives daily LCR values to ensure regulatory compliance.

## Key Features

**Basel III Compliant LCR Calculations**: Implements the regulatory Liquidity Coverage Ratio formula (HQLA / Total Net Cash Outflows ≥ 100%) with proper HQLA classifications (Level 1, 2A, 2B assets) and appropriate haircuts.

**150-Day Liquidity Forecasting**: Daily projections of HQLA, cash inflows, cash outflows, and resulting LCR values with maturity decay factors and stress considerations.

**What-If Scenario Analysis**: Run pre-defined or custom stress scenarios to analyze the impact of market events, counterparty defaults, and regional stress on liquidity positions.

**AI-Powered Natural Language Querying**: Ask questions about liquidity positions, LCR forecasts, HQLA composition, and more using plain English through Cortex Analyst and a semantic view.

**Real-Time Streamlit Dashboard**: Interactive visualization of LCR metrics, compliance monitoring, trend analysis, and scenario comparison—all within Snowflake.

**Interactive Notebooks**: Execute LCR calculations on-demand and perform detailed scenario analysis using Snowflake Notebooks.

## How It Works

![How It Works](assets/howitworks.png)

**Data Foundation**: The solution creates a comprehensive data model with position tables (580K+ records), cash flow tables (200K+ inflows and outflows), market data (3.6M+ records), and counterparty information (2K+ records) across multiple business units and regions.

**HQLA Projection**: Positions are classified according to Basel III HQLA levels with appropriate haircuts applied:
- Level 1 Assets: 0% haircut (cash, government bonds)
- Level 2A Assets: 15% haircut (corporate bonds AA+)
- Level 2B Assets: 25-50% haircut (corporate bonds BBB, equities)

**Cash Flow Modeling**: Inflows and outflows are projected forward with maturity considerations, creating a 150-day net cash flow forecast that feeds into the LCR calculation.

**Cortex Analyst Semantic View**: A semantic view defines the relationships and metrics within liquidity data, enabling the AI to understand and respond to analytical questions about LCR, HQLA, cash flows, and compliance.

**Streamlit Application**: A three-page dashboard provides:
- LCR Dashboard: Real-time metrics, trend visualization, and compliance indicators
- What-If Scenarios: Stress testing and scenario comparison
- Ask the Agent: Natural language data querying with intelligent chart generation

**Notebook Execution**: Snowflake Notebooks calculate baseline LCR and what-if scenarios, triggered directly from the Streamlit dashboard or executed independently.

## Business Impact

This solution helps financial institutions transform their liquidity risk management:

**Regulatory Compliance**: Ensure Basel III LCR requirements are met with accurate, auditable calculations and 150-day forward projections that identify potential compliance breaches before they occur.

**Proactive Risk Management**: Identify days where LCR may fall below the 100% threshold and take corrective action through what-if scenario analysis to understand the impact of potential stress events.

**Operational Efficiency**: Replace manual spreadsheet-based calculations with automated, on-demand LCR computation that runs in seconds and provides consistent, reproducible results.

**Faster Decision Making**: Treasury teams get immediate answers to complex liquidity questions through natural language queries, eliminating the need to wait for data teams or build custom reports.

**Scenario Planning**: Stress test the impact of market events, counterparty failures, and regional crises before they happen, enabling proactive liquidity buffer management.

**Simplified Infrastructure**: Eliminate external data movement, separate BI tools, and manual data pipelines. Everything runs natively within Snowflake.

## Use Cases and Applications

This solution serves as a comprehensive blueprint for AI-powered liquidity risk management:

**Daily LCR Monitoring**: Calculate and track daily LCR values with compliance threshold monitoring and automatic alerting when values approach regulatory minimums.

**Stress Testing**: Run predefined scenarios (European market stress, multi-regional impact) or create custom scenarios to understand portfolio sensitivity to various risk factors.

**HQLA Optimization**: Analyze HQLA composition by asset level, security type, and business unit to optimize the liquidity buffer while minimizing carrying costs.

**Cash Flow Forecasting**: Project inflows and outflows with maturity considerations to understand future liquidity needs and potential funding gaps.

**Regulatory Reporting**: Generate audit-ready LCR calculations with full traceability from source data through final metrics.

**What-If Analysis**: Answer questions like "What happens to LCR if we lose 20% of government bonds?" or "How does a European counterparty stress impact our liquidity position?"

## Components Included

| Component | Type | Key Capabilities |
|-----------|------|------------------|
| **LIQUIDITY_FORECAST** | Notebook | Baseline LCR calculation, HQLA projection, cash flow modeling |
| **LIQUIDITY_WHAT_IF_FORECAST_SANDBOX** | Notebook | Scenario-based LCR calculation with configurable stress factors |
| **LIQUIDITY_STREAMLIT** | Streamlit App | Dashboard, what-if scenarios, AI agent interface |
| **LIQUIDITY_SV** | Semantic View | Natural language query support for liquidity data |
| **POSITIONS** | Table | 580K+ investment positions with HQLA classifications |
| **CASH_INFLOWS/OUTFLOWS** | Tables | 200K+ cash flow transactions |
| **LCR/WHAT_IF_LCR** | Tables | Calculated LCR results for baseline and scenarios |

## Sample Data

The demo includes realistic financial data:

- **580,000+ positions** across multiple business units and security types
- **200,000+ cash flow transactions** (inflows and outflows)
- **3.6M+ market data points** with historical pricing
- **2,000+ counterparties** across different regions and credit ratings
- **Multiple business units**: US Treasury, EU Treasury, Asia Treasury, Trading desks

## Sample Questions for the AI Agent

The natural language agent can answer questions like:

- "What is the current LCR forecast trend over the next 150 days?"
- "Show me the breakdown of HQLA by asset level"
- "Which days in the forecast have LCR below 100%?"
- "Compare baseline LCR with what-if scenario 1"
- "What's LCR today and headroom vs floor?"
- "Why did LCR move? What are top 3 causes?"

## Getting Started

**Repository**: [https://github.com/Snowflake-Labs/sfguide-liquidity-risk-agent](https://github.com/Snowflake-Labs/sfguide-liquidity-risk-agent)

1. Clone the repo and open `scripts/setup.sql` in Snowsight
2. Run **Sections 1-9** to create roles, warehouses, database, stages, and sample data
3. Upload files from `notebooks/` and `streamlit/` folders to their respective stages (use Section 10 PUT commands)
4. Run **Sections 11-13** to create notebooks, Streamlit app, and semantic view
5. Open `LIQUIDITY_STREAMLIT` in Snowsight and run the `LIQUIDITY_FORECAST` notebook to generate LCR data

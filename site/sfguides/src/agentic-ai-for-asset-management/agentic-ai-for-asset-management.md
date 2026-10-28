id: agentic-ai-for-asset-management
language: en
summary: Cortex-powered asset management agents in Snowflake CoWork
categories: snowflake-site:taxonomy/industry/financial-services, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/snowflake-feature/snowflake-intelligence, snowflake-site:taxonomy/snowflake-feature/marketplace-and-integrations, snowflake-site:taxonomy/snowflake-feature/snowpark
environments: web
status: Published
authors: Mats Stellwall, Dureti Shemsi
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management

# Agentic AI for Asset Management using Snowflake Public Data

## Overview

This solution builds a complete AI-powered asset management platform inside Snowflake, featuring specialised Cortex Agents that serve different roles across front, middle, and back office functions. It demonstrates how financial firms can transform investment workflows by integrating structured portfolio data with unstructured research documents — all powered by Snowflake CoWork.

The solution creates a fictional firm called **Simulated Asset Management (SAM)** with:
- Real securities data from SEC filings via **Snowflake Public Data (Free)**
- 11 investment strategies across equity, multi-asset, ESG, and alternatives
- Synthetic broker research, earnings transcripts, policy documents, and client data
- 8 specialised Cortex Agents with 36 runtime skills
- 2 ML models trained and registered during the build (market regime, credit risk), plus 3 ML workflow notebooks

## Prerequisites

- A Snowflake account with Cortex AI enabled and CORTEX_ENABLED_CROSS_REGION set to ANY_REGION
- **Snowflake Public Data (Free)** Marketplace listing installed (auto-installed by setup script)
- ACCOUNTADMIN role access (for initial setup only — the build runs as `FSI_DEMO_BUILD_ROLE` and the demo as `SAM_DEMO_USER_ROLE`)

## Architecture

The solution runs entirely within Snowflake using native AI features — no external infrastructure, APIs, or data movement required.

**Data Foundation**: A dimensional model with more than 100 tables and views — dimensions (securities, issuers, portfolios, benchmarks, clients) and facts (positions, transactions, prices, ESG scores, attribution, private markets). Real securities sourced from Snowflake Public Data across a 503-instrument universe, with broker recommendations grounded in real prices and SEC fundamentals.

**Document Corpus**: Synthetic documents (broker research, press releases, NGO reports, policy documents, regulatory texts) generated via a template hydration engine. Real SEC filings (10-K, 10-Q) and earnings transcripts loaded from the marketplace share.

**Cortex Search Services**: 12 search services indexing documents by type with filterable attributes (ticker, company, document type, jurisdiction, severity). Enables semantic search across thousands of documents.

**Cortex Analyst Semantic Views**: 17 semantic views defining relationships and metrics across portfolio, market, attribution, research, operational, private markets and ML data. Translates natural language into SQL for instant analytical answers.

**Cortex Agents**: 8 agents with role-specific instructions, tool access, and orchestration skills. Each agent intelligently combines Cortex Analyst, Cortex Search, and stored procedure tools to answer complex multi-source questions.

**Snowflake CoWork**: The conversational interface where users interact with agents via natural language. Agents orchestrate tools, produce visualisations, and generate PDF reports — all within a chat experience.

**ML Models**: The build trains a market regime model and a credit risk model, registers them in the Snowflake Model Registry with a `PRODUCTION` alias, and scores them in SQL. Training data comes from Feature Store feature views, so each model version has lineage back to its data. Three notebooks walk through the same workflows interactively, plus a factor model.

**Code Bundles**: The build itself runs inside Snowflake as a Code Bundle created from your Git workspace, so there is nothing to install locally.

## Agents

| Agent | Role | Key Capabilities |
|-------|------|------------------|
| **Portfolio Copilot** | Portfolio Manager | Holdings analysis, multi-level attribution, stress testing, supply chain exposure, Monte Carlo simulation, portfolio construction and optimisation, historical backtesting, investment memos |
| **Research Copilot** | Research Analyst | Multi-source synthesis (SEC + transcripts + broker research), investment memo generation, PDF reports |
| **Risk & Compliance Copilot** | ESG / Compliance Officer | Controversy monitoring, mandate compliance, concentration limits, engagement tracking, regulatory disclosure |
| **Sales Advisor** | Client Relations | Quarterly letters, RFP response preparation, client meeting prep, performance narratives, regulatory disclosures |
| **Operations Copilot** | Middle Office | Settlement monitoring, reconciliation, NAV calculation, corporate actions |
| **Executive Copilot** | C-Suite | Firm KPIs, client analytics, competitor intelligence, M&A simulation, board briefings |
| **Private Equity Copilot** | PE Deal Team | Deal pipeline screening, due diligence search, expert network insights, value creation tracking |
| **Private Credit Copilot** | Credit Analyst | Credit portfolio monitoring, covenant tracking, rate sensitivity, deal pipeline, ML credit scoring |

## ML Models and Notebooks

| Model / notebook | Technique | Output | Built by |
|----------|-----------|--------|----------|
| **Market Regime Detection** (`MARKET_REGIME_GMM`) | Gaussian mixture model on volatility, momentum and dispersion features | RISK_ON / TRANSITIONAL / RISK_OFF regime per day | Build and `market_regime_detection.ipynb` |
| **Credit Risk Scoring** (`CREDIT_RISK_XGBOOST`) | XGBoost classifier with SHAP explanations | Probability of next-quarter covenant stress per borrower | Build and `credit_risk_model.ipynb` |
| **Factor Model Workflow** | Multi-factor model with SHAP explanations | Factor scores, factor returns, predicted returns, optimal weights | `factor_discovery.ipynb` |

The Private Credit Copilot calls the credit risk model directly through a what-if tool, so a user can ask how a borrower's default risk changes if, for example, leverage rises by 20%.

## Key Features

**Skill-Driven Workflows**: 36 runtime skills provide structured multi-step guidance for complex tasks (investment memos, RFP responses, client letters, attribution reports). Skills include verification checkpoints and cross-references.

**Multi-Tool Orchestration**: A single question can trigger 5+ tools — verify a market event, calculate portfolio exposure, check policy thresholds, search research documents, and generate a committee memo.

**Custom Analytical Tools**: Agents have access to purpose-built stored procedures that execute complex quantitative workflows:

| Tool | Agent(s) | Capability |
|------|----------|------------|
| **Historical Stress Backtest** | Portfolio Copilot | Replay portfolio against historical crises (GFC, COVID, 2022 rates) |
| **Monte Carlo Simulation** | Portfolio Copilot | 10,000-path simulation with block bootstrap for VaR and drawdown analysis |
| **Scenario Sensitivity** | Portfolio Copilot | What-if shock analysis (rate moves, vol spikes, growth shocks) |
| **Counterfactual Attribution** | Portfolio Copilot | "What if we had held different weights?" alternative history analysis |
| **Historical Backtest** | Portfolio Copilot | Backtest custom portfolio weights over a chosen period and rebalancing frequency |
| **Brinson Attribution** | Portfolio Copilot | On-demand attribution of any portfolio against a benchmark over any period |
| **M&A Simulation** | Executive Copilot | Model AUM impact, revenue synergies, and integration scenarios |
| **Default Risk What-If** | Private Credit Copilot | Score a borrower with the registered credit risk model under changed financials, with SHAP drivers |
| **Thesis Tracker** | Research Copilot | Create and update investment theses |
| **PDF Report Generator** | Six agents | Branded PDF reports with presigned download URLs |
| **Data Origin** | Portfolio and Executive Copilots | Explain data lineage for any semantic field (source table, transformation, refresh) |

**Portfolio Construction and Backtesting**: Guided by its portfolio construction and optimiser skills, the Portfolio Copilot can construct model portfolios, optimise allocations (max Sharpe, min variance, risk parity), run full historical backtests with custom weights, and validate with Monte Carlo simulation — enabling a complete "build, test, validate" workflow in conversation.

**Real Data Integration**: SEC financials, stock prices, institutional holdings (13F), insider trading, dividends, and economic indicators — all from Snowflake Public Data (Free).

**Performance Attribution**: Full Brinson-Fachler decomposition (sector, country, industry), factor attribution, currency effects, and linked multi-period analysis.

**Proactive Insights**: AI-generated morning briefings and signal extraction with urgency scoring — surfaced to agents for context-aware responses.

## Setup

### Step 1: Create Git Workspace

1. Navigate to **Projects > Workspaces**
2. Click **+** then **From Git repository**
3. Repository URL: `https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git`
4. Authentication: Public repository (no auth needed)
5. Name the workspace (eg SAM_DEMO_WORKSPACE) or use the default name

### Step 2: Run Setup (45-60 minutes)

1. Open [`https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management/blob/main/scripts/setup.sql`](scripts/setup.sql) in the workspace.
2. Set `$ws_name` in Section 0, at the top of the script, to the name of the workspace you created in Step 1. Run `SHOW WORKSPACES IN ACCOUNT` if you need to check the name. This is the only value you need to edit.
3. Execute the whole script as `ACCOUNTADMIN`.

Sections 1-8 create the infrastructure:
- `SAM_DEMO` and `FSI_DEMO_CONFIG` databases with all schemas
- `SAM_DEMO_EXECUTION_WH` and `SAM_DEMO_CORTEX_WH` warehouses
- `FSI_DEMO_BUILD_ROLE` (build) and `SAM_DEMO_USER_ROLE` (demo use) with the required privileges
- Compute pools for the Code Bundle and the ML notebooks
- Marketplace data share (Snowflake Public Data - Free)
- Cortex AI enablement for the`FSI_DEMO_BUILD_ROLE` (build) and `SAM_DEMO_USER_ROLE` (demo use) roles

Section 9 creates a Code Bundle from your workspace and runs the build inside Snowflake. The build creates all tables, documents, search services, semantic views, ML models, agents, skills, tools, signals and evaluation datasets.

If the `CREATE OR REPLACE CODE BUNDLE` result says the source directory does not exist or contains no files, `$ws_name` does not match your workspace. Fix it and re-run that statement before continuing.

The build leaves the demo data frozen at the build date. To keep it current, install the weekly refresh task afterwards, which advances prices, documents and briefings every Monday:

```sql
EXECUTE CODE BUNDLE SAM_DEMO.AI.SAM_BUILD_BUNDLE
    ENTRYPOINT = 'python/workspace_main.py'
    ARGUMENTS  = ('--scope', 'automation');
```

### Step 3: Use the Agents

1. Navigate to **AI & ML > Snowflake CoWork**
2. Select any agent
3. Start asking questions. The repository's [`https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management/blob/main/demo_scripts/`](demo_scripts/) folder has a step-by-step script for each demo scenario.

### Clean-Up

Run the [`https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management/blob/main/scripts/teardown.sql`](scripts/teardown.sql) to remove all the objects that is created by this setup.


## Business Impact

**Faster Insights**: Multi-dimensional risk assessments completed in minutes instead of days. Event-driven analysis that previously required multiple analysts happens in a single conversation.

**Reduced Manual Effort**: Eliminates time spent searching across systems, compiling reports, and waiting for data teams. Every question gets an immediate, comprehensive answer.

**Better Risk Management**: Real-time monitoring of concentration limits, ESG controversies, and mandate breaches with automated policy checking.

**Enhanced Client Service**: Instant access to performance data, philosophy documents, and regulatory disclosures for quarterly presentations, RFP responses, and client inquiries.

**Informed Decisions**: Executives get firm-wide visibility with the ability to run M&A simulations, stress tests, and scenario analyses on demand.

## Get Started

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management)**

The repository contains the setup script, build code, reference data, semantic view definitions, agent skills, ML notebooks, demo scenario scripts, and data model and lineage documentation.

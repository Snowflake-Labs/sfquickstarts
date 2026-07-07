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
- 8 specialised Cortex Agents with 36+ runtime skills
- 3 ML workflow notebooks (market regime, factor models, credit risk)

## Prerequisites

- A Snowflake account with Cortex AI enabled
- **Snowflake Public Data (Free)** Marketplace listing installed (auto-installed by setup script)
- ACCOUNTADMIN role access (for initial setup only — runtime uses a dedicated SAM_DEMO_ROLE)

## Architecture

The solution runs entirely within Snowflake using native AI features — no external infrastructure, APIs, or data movement required.

**Data Foundation**: A dimensional model with 48+ tables — dimensions (securities, issuers, portfolios, benchmarks, clients) and facts (positions, transactions, prices, ESG scores, attribution). Real securities sourced from 14,000+ instruments via Snowflake Public Data.

**Document Corpus**: Synthetic documents (broker research, press releases, NGO reports, policy documents, regulatory texts) generated via a template hydration engine. Real SEC filings (10-K, 10-Q) and earnings transcripts loaded from the marketplace share.

**Cortex Search Services**: 16 search services indexing documents by type with filterable attributes (ticker, company, document type, jurisdiction, severity). Enables semantic search across thousands of documents.

**Cortex Analyst Semantic Views**: 10+ semantic views defining relationships and metrics across portfolio, market, attribution, research, and operational data. Translates natural language into SQL for instant analytical answers.

**Cortex Agents**: 8 agents with role-specific instructions, tool access, and orchestration skills. Each agent intelligently combines Cortex Analyst, Cortex Search, and stored procedure tools to answer complex multi-source questions.

**Snowflake CoWork**: The conversational interface where users interact with agents via natural language. Agents orchestrate tools, produce visualisations, and generate PDF reports — all within a chat experience.

**ML Workflows**: 3 notebook-based ML demonstrations using Snowflake Feature Store, Model Registry, and Cortex ML functions for market regime detection, factor model training, and credit risk scoring.

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

## ML Notebooks

| Notebook | Technique | Output |
|----------|-----------|--------|
| **Market Regime Detection** | XGBoost classification on macro indicators | RISK_ON / TRANSITIONAL / RISK_OFF regime labels |
| **Factor Model Workflow** | Multi-factor model with SHAP explanations | Factor loadings, IC scores, Fama-French decomposition |
| **Credit Risk Scoring** | Gradient boosted PD model | Probability of default scores per borrower |

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
| **Portfolio Optimizer** | Portfolio Copilot | Max Sharpe, min variance, risk parity, and efficient frontier construction |
| **M&A Simulation** | Executive Copilot | Model AUM impact, revenue synergies, and integration scenarios |
| **PDF Report Generator** | All agents | Branded PDF reports with presigned download URLs |
| **Data Origin** | All agents | Explain data lineage for any semantic field (source table, transformation, refresh) |

**Portfolio Construction and Backtesting**: The Portfolio Copilot can construct model portfolios, optimise allocations (max Sharpe, min variance, risk parity), run full historical backtests with custom weights, and validate with Monte Carlo simulation — enabling a complete "build, test, validate" workflow in conversation.

**Real Data Integration**: SEC financials, stock prices, institutional holdings (13F), insider trading, dividends, and economic indicators — all from Snowflake Public Data (Free).

**Performance Attribution**: Full Brinson-Fachler decomposition (sector, country, industry), factor attribution, currency effects, and linked multi-period analysis.

**Proactive Insights**: AI-generated morning briefings and signal extraction with urgency scoring — surfaced to agents for context-aware responses.

## Setup

### Step 1: Create Git Workspace

1. Navigate to **Projects > Workspaces**
2. Click **+** then **From Git repository**
3. Repository URL: `https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git`
4. Authentication: Public repository (no auth needed)
5. Name the workspace (e.g., "SAM Demo")

### Step 2: Run Infrastructure Setup (2 minutes)

Open [`scripts/setup.sql`](scripts/setup.sql) in the workspace and execute it. This creates:
- `SAM_DEMO` database with all schemas
- `SAM_DEMO_ROLE` with required privileges (including task execution)
- `SAM_DEMO_EXECUTION_WH` and `SAM_DEMO_CORTEX_WH` warehouses
- Marketplace data share (Snowflake Public Data - Free)
- Cortex AI enablement and Snowflake CoWork

### Step 3: Run Data and AI Build (15-20 minutes)

1. Open `python/workspace_main.py` in the workspace
2. Connect a **notebook service** when prompted:
   - Python version: 3.11+
   - Compute pool: any available pool
   - Artifact repositories (optional): SNOWFLAKE.SNOWPARK.PYPI_SHARED_REPOSITORY
3. Open the Terminal and run:
   `pip install -r "$PWD/requirements.txt"`
4. Restart the kernel
5. Click **Run**

The build creates all tables, documents, search services, semantic views, agents, skills, tools, signals, and evaluation datasets.

## Business Impact

**Faster Insights**: Multi-dimensional risk assessments completed in minutes instead of days. Event-driven analysis that previously required multiple analysts happens in a single conversation.

**Reduced Manual Effort**: Eliminates time spent searching across systems, compiling reports, and waiting for data teams. Every question gets an immediate, comprehensive answer.

**Better Risk Management**: Real-time monitoring of concentration limits, ESG controversies, and mandate breaches with automated policy checking.

**Enhanced Client Service**: Instant access to performance data, philosophy documents, and regulatory disclosures for quarterly presentations, RFP responses, and client inquiries.

**Informed Decisions**: Executives get firm-wide visibility with the ability to run M&A simulations, stress tests, and scenario analyses on demand.

## Get Started

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management)**

The repository contains setup scripts, sample data, semantic model definitions, agent skills, ML notebooks, and step-by-step instructions for deploying the complete solution.

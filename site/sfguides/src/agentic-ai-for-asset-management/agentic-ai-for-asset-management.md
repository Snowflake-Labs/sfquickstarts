id: agentic-ai-for-asset-management
language: en
summary: Cortex-powered asset management agents in Snowflake Intelligence
categories: snowflake-site:taxonomy/industry/financial-services, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/snowflake-feature/snowflake-intelligence, snowflake-site:taxonomy/snowflake-feature/marketplace-and-integrations, snowflake-site:taxonomy/snowflake-feature/snowpark
environments: web
status: Published
authors: Mats Stellwall, Constantin Stanca, Dureti Shemsi
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management

# Agentic AI for Asset Management using Snowflake Public Data

## Overview

This solution provides a comprehensive Cortex-powered system for asset management, featuring multiple specialized Cortex agents that serve different roles across front, middle, and back office functions. It demonstrates how financial firms can transform their investment workflows by integrating structured portfolio data with unstructured research documents—all powered by Snowflake Intelligence.

The solution creates a fictional asset management firm called **Simulated Asset Management (SAM)** with real securities data from SEC filings, synthetic broker research, earnings transcripts, policy documents, and portfolio holdings across multiple investment strategies.

## Key Features

**Multi-Agent Architecture**: Nine specialized Cortex agents serve different business roles—from Portfolio Managers to Compliance Officers to Executives. Each agent has role-specific tools, instructions, and access to relevant data sources.

**Intelligent Document Search**: Use natural language to search through broker research reports, earnings transcripts, press releases, NGO reports, policy documents, and more. Powered by Snowflake's Cortex Search, analysts can find key insights across thousands of documents in seconds.

**Conversational Portfolio Analysis**: Analyze portfolio holdings, risk exposures, factor scores, and ESG metrics using simple conversational queries. The system leverages Cortex Analyst to translate natural language into SQL, providing instant, data-driven answers.

**Real SEC Filing Integration**: The solution integrates real SEC filing data from the Snowflake Marketplace, including 10-K, 10-Q, and 8-K filings with full-text search capabilities across risk factors, MD&A sections, and financial disclosures.

**Professional Report Generation**: Agents can generate branded PDF reports for investment committees, client presentations, compliance documentation, and executive briefings—complete with proper formatting and regulatory disclaimers.

**Multi-Tool Orchestration**: Each agent intelligently combines multiple tools in a single conversation. A Portfolio Manager can verify a market event, calculate portfolio exposure, check policy thresholds, and generate a committee memo—all from one comprehensive question.

## How It Works

This solution leverages Snowflake's native AI features to create a seamless, end-to-end workflow without the need for external tools or data movement.

**Data Foundation**: The solution creates a complete dimensional data model with dimension tables (securities, issuers, portfolios, benchmarks) and fact tables (positions, transactions, stock prices, ESG scores). Real securities are sourced from SEC filings via the Snowflake Marketplace.

**Document Generation**: Synthetic documents (broker research, press releases, NGO reports, policy documents) are generated using a template hydration engine that fills placeholders with contextually appropriate content, creating realistic research materials.

**Cortex Search Services**: Documents are chunked and indexed into Cortex Search services, enabling semantic search across different document types. Each service has specific searchable attributes (ticker, company name, severity level, etc.) for precise filtering.

**Cortex Analyst Semantic Views**: Semantic views define the relationships and metrics within portfolio and market data, making it easy for the AI to understand and respond to analytical questions about holdings, performance, risk, and more.

**Cortex Agents**: Nine Cortex Agents are created with role-specific instructions, tool access, and business context. Each agent can intelligently route queries to the appropriate combination of Cortex Analyst and Cortex Search tools.

**Snowflake Intelligence**: The conversational interface where users interact with Cortex Agents. Users can ask natural language questions, and the agents orchestrate the appropriate tools to provide comprehensive answers, all within a chat-based experience.

**PDF Generation**: A custom stored procedure enables agents to generate professional branded PDF reports, stored in Snowflake stages with presigned URLs for easy access.

## Business Impact

This solution helps financial firms transition from fragmented, manual workflows to an integrated, AI-driven process:

**Faster Insights**: Portfolio managers get answers to complex multi-source questions in seconds instead of hours. Event-driven risk assessments that previously required multiple analysts can be completed in a single conversation.

**Increased Efficiency**: Reduces time spent searching across systems, compiling reports, and waiting for data teams to build dashboards. Every question gets an immediate, comprehensive answer.

**Better Risk Management**: Compliance officers can monitor concentration limits, ESG controversies, and mandate breaches in real-time. Automated policy checking ensures issues are identified before they become problems.

**Enhanced Client Service**: Client relationship managers can prepare quarterly presentations, respond to RFPs, and answer client questions with instant access to performance data, philosophy documents, and regulatory disclosures.

**Informed Decision Making**: Executives get firm-wide visibility across all strategies, client flows, and competitive intelligence—with the ability to run M&A simulations and generate board-ready briefings on demand.

**Simplified Operations**: Eliminates the need for external infrastructure, data movement, or custom application development. Everything runs natively within Snowflake.

## Use Cases and Applications

This solution serves as a comprehensive blueprint for AI-powered asset management:

**Portfolio Management**: Analyze holdings, assess concentration risk, evaluate event impacts, and generate investment committee memos with multi-tool orchestration.

**Investment Research**: Synthesize insights from broker research, earnings transcripts, and SEC filings to build comprehensive investment theses and generate formal research reports.

**ESG & Sustainability**: Monitor NGO reports for controversies, track engagement history, verify policy compliance, and prepare ESG committee documentation.

**Compliance & Risk**: Run daily concentration checks, verify mandate compliance, track breach remediation, and generate regulatory reports with full audit trails.

**Client Relations**: Prepare quarterly client presentations, generate customized reports, and respond to client inquiries with instant access to performance and philosophy content.

**Operations**: Monitor settlement failures, reconciliation breaks, NAV calculations, and corporate actions with a unified operational dashboard.

**Executive Decision Support**: Access firm-wide KPIs, analyze competitor intelligence, run M&A simulations, and generate board briefings with comprehensive data coverage.

## Agents Included

| Agent | Role | Key Capabilities |
|-------|------|------------------|
| **Portfolio Copilot** | Portfolio Manager | Holdings analysis, event impact, supply chain exposure, investment memos |
| **Research Copilot** | Research Analyst | Multi-source research synthesis, investment reports, PDF generation |
| **ESG Guardian** | ESG Officer | Controversy monitoring, engagement tracking, policy compliance |
| **Compliance Advisor** | Compliance Officer | Concentration limits, mandate monitoring, breach detection |
| **Sales Advisor** | Client Relations | Client reporting, philosophy integration, regulatory disclosures |
| **Quant Analyst** | Quantitative Analyst | Factor screening, fundamental validation, statistical analysis |
| **Middle Office Copilot** | Operations Manager | Settlement, reconciliation, NAV, corporate actions |
| **Executive Copilot** | C-Suite Executive | Firm KPIs, competitor intel, M&A simulation |
| **Thematic Macro Advisor** | Thematic PM | Theme positioning, macro events, cross-portfolio analysis |

## Get Started

Ready to transform your asset management workflows? This solution includes everything you need to get up and running quickly.

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management)**

The repository contains complete setup scripts, sample data, semantic model definitions, and step-by-step instructions for configuring Snowflake Intelligence with Cortex Agents.


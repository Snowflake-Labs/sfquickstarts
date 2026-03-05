id: hotel-personalization-picknstays
language: en
summary: Executive intelligence platform for multi-property hotel portfolios built on Snowflake
categories: snowflake-site:taxonomy/industry/travel-and-hospitality, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/applied-analytics, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/snowflake-feature/snowflake-intelligence, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/snowflake-ml-functions, snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
status: Published
authors: Sri Subramanian, Dureti Shemsi
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex AI, Snowflake Intelligence, Cortex Analyst, Cortex Search, Snowpark ML, Hotel Analytics, Executive Intelligence, Hospitality, Streamlit, Customer Experience, Loyalty Programs, Portfolio Management
fork repo link: https://github.com/Snowflake-Labs/sfguide-hotel-personalization-picknstays


# Hotel Personalization Pick'N Stays

## Overview

This guide delivers a comprehensive executive intelligence platform for multi-property hotel portfolios built entirely on Snowflake. Designed specifically for C-suite leaders, regional executives, and strategic decision-makers, this platform transforms raw operational data into actionable insights through natural language AI agents, real-time analytics, and proactive intelligence across portfolio performance, loyalty optimization, and guest experience excellence.

The platform demonstrates how hospitality organizations can modernize executive decision-making by unifying data across properties, automating performance monitoring, and enabling conversational analytics through Snowflake Intelligence Agents. This demonstration features **Summit Hospitality Group's 100 global properties** (50 AMER, 30 EMEA, 20 APAC) as a fictitious portfolio showcasing enterprise-scale capabilities.

## The Business Challenge

**Information Overload Without Actionable Insights**: 87% of hotel executives report data overload but insight scarcity. Critical signals like performance outliers and at-risk segments are buried in operational noise, with no unified view across brands, regions, and performance dimensions. Issues are discovered reactively, after guest impact and revenue loss.

**Loyalty Program ROI Uncertainty**: $2.5B+ spent annually on hotel loyalty programs in North America alone, yet limited visibility exists into which segments deliver strongest repeat rates. The correlation between loyalty tier and actual guest value remains unclear, and identifying at-risk high-value members before churn is difficult.

**Service Quality Blind Spots**: Guest satisfaction is tracked but not acted upon proactively. VIP arrivals with past service issues aren't flagged to operations teams. Systemic problems like regional trends and brand-wide issues remain invisible, and service recovery effectiveness isn't measured by segment or property.

**Portfolio Complexity at Scale**: Inconsistent performance across geographies and brands, with no standard for identifying "outlier" properties requiring intervention. Executive teams lack tools for portfolio-wide exception management, and regional leaders cannot benchmark their markets objectively.

## The Solution: Executive Intelligence Platform

This platform transforms raw operational data into executive-ready strategic intelligence through Snowflake's unified data cloud.

![Architecture Overview](assets/architecture_overview.png)

The platform implements a modern **Medallion Architecture** across Snowflake:

**BRONZE Layer**: Raw data ingestion from 100 properties including guest profiles, bookings, stays, loyalty membership, and service cases.

**SILVER Layer**: Cleaned and standardized data with enrichment including VIP flags, repeat issue detection, sentiment correlation, and churn risk scoring.

**GOLD Layer**: Executive analytics-ready aggregations providing Portfolio Performance KPIs, Loyalty Segment Intelligence, and CX & Service Signals.

**SEMANTIC Layer**: 9 semantic views enabling natural language AI access to all metrics, plus Hotel Intelligence Master Agent for conversational querying with 48+ pre-configured sample questions.

**CONSUMPTION Layer**: 3 executive dashboards (Portfolio Overview, Loyalty Intelligence, CX & Service Signals) with sub-second query performance from pre-aggregated Gold tables.

## Business Value & ROI

**Decision Velocity**: From 8 hours to 15 minutes for executive performance review preparation. 90% reduction in time spent on manual data compilation and analysis. Real-time insights available on-demand, not quarterly cycles.

**Revenue Protection & Growth**: $6.5M annual impact across three use cases: Portfolio Oversight ($2.5M from rapid outlier intervention), Loyalty Optimization ($1.5M from retention improvement), and Service Excellence ($2.5M from VIP churn prevention). Platform ROI: 850%—pays for itself in 1.4 months for typical 100-property portfolios.

**Operational Excellence**: 35% reduction in repeat service issues through root cause analysis. Guest satisfaction +0.8 points average from proactive VIP management. NPS improvement +12 points from service recovery effectiveness.

**Loyalty & Retention**: 18% reduction in high-value guest churn. 25% improvement in repeat booking rates for targeted segments. Cross-sell success 42% for loyalty campaigns vs. 12% baseline through affinity-based targeting.

> Industry benchmarks compiled from Cornell Center for Hospitality Research, HSMAI, AHLA, McKinsey, Accenture, and Forrester Research studies. Actual results vary by portfolio size, data quality, and implementation approach.

## Snowflake Features & Technologies

This solution leverages the following Snowflake platform capabilities:

**Data Engineering**: Medallion Architecture (Bronze, Silver, Gold layers) for structured data transformation, data quality enrichment, and pre-aggregated analytics tables for sub-second query performance.

**Streamlit in Snowflake**: Native application framework delivering three executive dashboards (Portfolio Overview, Loyalty Intelligence, CX & Service Signals) with no external BI tools required. Fully integrated with Snowpark for data access.

**Snowflake Intelligence**: Conversational AI platform enabling natural language queries across all portfolio data through the Hotel Intelligence Master Agent with 48+ pre-configured business questions.

**Cortex Analyst**: Text-to-SQL conversion layer with 9 semantic views providing natural language access to portfolio metrics, loyalty segments, guest sentiment, VIP arrivals, preferences, and service intelligence.

**Cortex Agents**: Five specialized AI agents for domain-specific analysis (Guest Analytics, Personalization, Amenities Intelligence, Experience Optimizer) plus the Hotel Intelligence Master Agent orchestrating comprehensive strategic analysis across all 9 semantic views.

## Technical Capabilities

**Portfolio Overview Dashboard**: Real-time portfolio health monitoring with 5 executive KPIs (Occupancy %, ADR, RevPAR, Repeat Stay Rate, Guest Satisfaction), performance visualizations by brand and region, 30-day trend analysis, experience health heatmap, and prioritized outliers & exceptions table with color-coded indicators.

![Portfolio Overview](assets/portfolio_overview_dashboard.png)

**Loyalty Intelligence Dashboard**: Understanding loyalty segment behavior across 5 tiers (Diamond, Gold, Silver, Blue, Non-Member) with 4 loyalty KPIs, repeat stay rate hierarchy, average spend per stay analysis, revenue mix breakdown by tier, at-risk segments table with strategic focus recommendations, and experience drivers correlation.

![Loyalty Intelligence](assets/loyalty_intelligence_dashboard.png)

**CX & Service Signals Dashboard**: Service quality monitoring with 4 service KPIs (Service Case Rate, Avg Resolution Time, Negative Sentiment Rate, Service Recovery Success), top service issue drivers ranking, service cases by priority distribution, sentiment breakdown, VIP arrivals watchlist with 7-day lookahead and churn risk scoring.

![CX & Service Signals](assets/cx_service_signals_dashboard.png)

## Key Differentiators

**Executive-Optimized KPIs**: Self-explanatory metrics with industry benchmarks and tooltips requiring zero training. Dashboard-native guidance for interpretation and action thresholds.

**Unified Data Platform**: Breaks down silos between PMS, booking engines, service systems, and feedback platforms with a single source of truth for all portfolio data across 100-1,000 properties.

**AI-Powered Natural Language Access**: Snowflake Intelligence Agents enable business users to ask sophisticated questions directly, extracting value through conversational interaction without SQL knowledge.

**Rapid Deployment**: Deploy entire platform in under 1 hour with pre-built semantic views, intelligence agents providing immediate value, and complete 100-property synthetic dataset.

**Scalability**: Handles 100-1,000 properties with 100K+ guest profiles, scaling to millions of records without performance degradation. Sub-second query response for pre-aggregated Gold tables.

## Use Cases & Demos

**Portfolio Outlier Intervention**: Identify 12+ properties with performance issues (RevPAR 15%+ below brand average, satisfaction <3.8, service case rate >100) requiring immediate executive attention. Query "What's driving RevPAR changes across brands this month?" to diagnose root causes and prioritize leadership intervention.

**Loyalty Segment Optimization**: Query "Which loyalty segment is growing fastest—and what's driving it?" to reallocate $800K loyalty budget from low-ROI segments to high-potential segments, delivering 3.2x campaign ROI and +13 point repeat rate improvement.

**Proactive VIP Churn Prevention**: Query "Show me Diamond guests arriving tomorrow with 2+ past service issues" via VIP Watchlist to enable pre-arrival GM outreach, room upgrades, and service team briefings, preventing $43K revenue loss per high-value guest.

**Root Cause Analysis**: Query "What are the top 2 issues driving dissatisfaction for high-value guests?" to aggregate insights across service cases, identifying operational quality problems (HVAC, room service delays) requiring portfolio-wide training and process improvements.

## Get Started

Ready to build executive intelligence for your hotel portfolio? This guide includes everything you need to get up and running quickly.

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-hotel-personalization-picknstays)**

The repository contains complete setup scripts, SQL deployment files, synthetic data generators, semantic model definitions, Streamlit dashboard code, and step-by-step instructions for deploying the full solution.

## Resources

- [Snowflake CLI Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Snowflake Intelligence Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-intelligence)
- [Streamlit in Snowflake Documentation](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Snowflake ML Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)

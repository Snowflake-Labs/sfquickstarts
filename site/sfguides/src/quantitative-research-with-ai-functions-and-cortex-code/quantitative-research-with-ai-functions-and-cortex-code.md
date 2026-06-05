id: quantitative-research-with-ai-functions-and-cortex-code
language: en
summary: Build an AI-powered quantitative research pipeline using Cortex Code, Cortex AI Functions, ML Model Registry, and Snowflake Intelligence to transform earnings call transcripts into actionable investment insights.
categories: snowflake-site:taxonomy/industry/financial-services, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/snowflake-feature/snowflake-intelligence, snowflake-site:taxonomy/snowflake-feature/marketplace-and-integrations, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/cortex-code
environments: web
status: Published
authors: Harry Yu, Serena Zou, Constantin Stanca, Dureti Shemsi
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-quantitative-research-aisql-cortex

# Quant Research and Data Science with Cortex Code and AI Functions using Snowflake Public Data

## Overview 

### Driving Alpha and Efficiency with Native AI

This guide demonstrates how to build an end-to-end AI-powered quantitative research pipeline using Snowflake's native AI capabilities—with **Cortex Code** as your AI coding assistant throughout the journey.

Financial analysts spend countless hours manually reviewing earnings call transcripts to gauge market sentiment and identify investment opportunities. This guide shows you how to **systematically process unstructured earnings transcript data using AI Functions**, automating sentiment extraction at scale while using **Cortex Code** to build, understand, and extend the solution through natural language conversation.

By leveraging Snowflake, you are building your AI solutions directly where your data resides—pushing application compute to the data, not data to the application. This eliminates the security risks, governance headaches, and latency associated with moving sensitive financial data to external environments. This entire solution is built seamlessly within the Snowflake Data Cloud, ensuring the highest standards of enterprise security, governance (RBAC), and ease of use.

This guide uses publicly available earnings call data from Dow Jones 30 companies (via Snowflake Marketplace) to show you how to:
- **Systematically extract consistent sentiment from unstructured earnings transcripts at scale with Cortex AI Functions**.
- Build and deploy predictive Machine Learning (ML) models in minutes with the conversational power of Cortex Code.
- Create an intelligent, unified conversational agent accessible through Snowflake Intelligence.

**Snowflake Public Data Products**: Provides the entirety of the broad suite of public domain datasets, curated and maintained by Snowflake to ensure long-term stability and access. The data product provides a foundational layer of financial market, economic, and demographic data published by reliable sources, saving organizations countless hours of data preparation and pipeline management.

## Architecture

![Research Pipeline Architecture](assets/architecture-diagram.png)

The architecture shows how Cortex Code serves as the central AI coding assistant throughout the pipeline—from data ingestion using **Snowflake Public Data (Free)** from Snowflake Marketplace, to sentiment extraction with Cortex AI Functions, ML model training and registry, and finally the unified agent experience in Snowflake Intelligence.

## How It Works

This guide leverages Snowflake's native AI features to create a seamless, end-to-end workflow without the need for external tools or data movement.

**Data Foundation**: Earnings call transcripts from DOW 30 companies are sourced from Snowflake Marketplace's free public data. Stock price data is pre-computed into momentum features for ML training.

**Sentiment Extraction**: The `AI_COMPLETE()` function processes each transcript with Claude, extracting structured JSON responses containing sentiment scores, analyst counts, and reasoning explanations.

**Model Training**: LightGBM regressors are trained on momentum ratios to predict forward stock returns. Models are versioned and deployed through Snowflake's ML Model Registry, making predictions available as SQL functions.

**Cortex Search Services**: Sentiment reasons are indexed into Cortex Search, enabling semantic retrieval across all analyzed transcripts. Analysts can find relevant insights using natural language queries.

**Cortex Analyst**: A semantic view defines the relationships and metrics within sentiment data, making it easy for the AI to understand and respond to analytical questions about sentiment trends and distributions.

**Cortex Agents**: A single agent is created with role-specific instructions that orchestrate multiple tools—ML predictions, text-to-SQL queries, semantic search, and email notifications—based on user intent.

**Snowflake Intelligence**: The conversational interface where users interact with the Cortex Agent. Users can ask complex multi-step questions, and the agent coordinates the appropriate tools to provide comprehensive answers.

## Build with Cortex Code

**Cortex Code** is an AI-driven intelligent agent integrated into the Snowflake platform, optimized for complex data engineering, analytics, machine learning, and agent-building tasks. It uses an autonomous agent framework to interact directly with your Snowflake environment, with deep understanding of Snowflake's Role-Based Access Control (RBAC), schemas, and best practices.

**Available in two interfaces, enabling different personas:**
- **Snowsight (Analyst/Data Scientist)** - Click the Cortex Code icon in Notebooks or Workspaces. Cortex Code allows subject matter experts (Quants, Analysts) to rapidly generate complex code from natural language, explain existing queries, and review AI-suggested changes, saving significant time otherwise spent on boilerplate coding.
- **CLI (Developer/Engineer)** - Provides an agentic shell for power users, bridging the local development environment and your Snowflake account. It can read/write local files, execute SQL, run bash commands, and manage dbt projects or Streamlit apps, accelerating the developer workflow.

**What makes this guide unique:** Rather than just running pre-built notebooks, you can use Cortex Code to build the entire ML pipeline through conversation—from feature engineering to model training, backtesting, and registration in the Snowflake ML Registry.

## Key Features

**Earnings Transcript Analysis with AI Functions**: Use Cortex AI Functions's `AI_COMPLETE()` function with Claude (`claude-4-sonnet`) to systematically process unstructured earnings call transcripts and extract structured sentiment scores (1-10 scale), analyst participation counts, and human-readable reasoning—transforming thousands of pages of text into actionable intelligence.

**AI-Native Workflow for Unstructured Financial Data**: Demonstrate how AI Functions enable systematic processing of unstructured data at scale—a major capability for hedge funds and asset managers dealing with earnings calls, analyst reports, SEC filings, and other text-heavy financial documents.

**Momentum-Based ML Predictions**: Train LightGBM models on technical momentum features using walk-forward quarterly validation, then register them in Snowflake's ML Model Registry for production inference.

**Semantic Search Over Sentiment**: Create Cortex Search services that enable natural language queries like "find companies with margin concerns" or "show bullish analyst sentiment"—without managing embeddings or vector databases.

**Natural Language Analytics**: Build semantic views for Cortex Analyst that allow business users to query sentiment data with plain English questions like "Which companies have the highest analyst sentiment?"

**Unified Conversational Interface**: Deploy a Cortex Agent that combines text-to-SQL (Cortex Analyst), semantic search (Cortex Search), ML predictions (stored procedures), and email notifications into a single chat experience via Snowflake Intelligence.

## Business Impact

This guide helps quantitative research teams transition from manual transcript analysis to automated, AI-driven insights:

**Faster Analysis**: Extract sentiment from dozens of earnings calls in minutes instead of days. What previously required reading thousands of pages can now be summarized with a single query.

**Scalable Coverage**: Expand coverage from a handful of companies to the entire DOW 30 (or beyond) without adding headcount. AI handles the extraction while analysts focus on interpretation.

**Consistent Methodology**: Apply the same sentiment scoring criteria across all transcripts, eliminating analyst-to-analyst variation and enabling apples-to-apples comparisons.

**Predictive Insights**: Combine qualitative sentiment with quantitative momentum factors to identify potential alpha opportunities before they're priced in.

**Instant Access**: Any team member can query sentiment data or run predictions through natural language, democratizing access to research insights.

## Beneficiary Key Personas

| Benefiting Party | Value / Saved Cost | Revenue Potential / Risk Mitigation |
|------------------|-------------------|------------------------------------|
| **Quantitative Analysts** | Faster Analysis: Extract sentiment from dozens of calls in minutes (vs. days/weeks). Time Saved: Hundreds of man-hours per quarter on transcript analysis. | Increased Alpha Generation: Faster insight-to-trade cycle allows analysts to identify and act on market anomalies sooner, directly increasing potential trading revenue. |
| **Data Scientists / ML Engineers** | Accelerated Development: Use Cortex Code to build the ML pipeline in conversation, cutting feature engineering and model deployment time by up to 50%. | Reduced Complexity & Governance Risk: By hosting the LLM and the entire pipeline securely within Snowflake, they mitigate the risk of data leakage and reduce the complexity and cost of maintaining multiple security tools. |
| **Portfolio Managers / Leadership** | Scalable Coverage: Expand coverage from a handful of companies to the entire DOW 30+ without adding headcount (a massive saving on labor costs). | Consistent Methodology: Applied, uniform sentiment scoring leads to more reliable model performance, reducing model risk and increasing confidence in investment decisions. |
| **Enterprise IT/Security** | Simplified Architecture: Eliminates the need to move data out of Snowflake, drastically simplifying data governance, auditing, and security protocols. | Security Assurance: Guarantees that sensitive data never leaves the governed Data Cloud, ensuring compliance with global data residency and security standards. |

## Use Cases and Applications

This guide serves as a blueprint for AI-powered quantitative research:

**Sentiment Analysis**: Extract structured sentiment scores from unstructured earnings call transcripts, tracking analyst reactions and management tone over time.

**Stock Screening**: Use ML predictions to rank stocks by expected returns, combining technical momentum with fundamental sentiment signals.

**Event-Driven Research**: Quickly assess how analyst sentiment shifted after specific corporate events, earnings surprises, or market moves.

**Thematic Discovery**: Search across all transcripts for mentions of specific themes—supply chain issues, margin pressures, competitive threats—using semantic search.

**Automated Reporting**: Generate email summaries of top stock picks, sentiment changes, and notable transcript excerpts without manual compilation.

**Cross-Sectional Analysis**: Compare sentiment across sectors, market caps, or time periods using natural language queries against the semantic view.

## Agent Capabilities

| Tool | Type | Description |
|------|------|-------------|
| **StockPerformancePredictor** | Stored Procedure | Generates ranked stock predictions using the registered LightGBM model |
| **AnalystSentiments** | Cortex Analyst | Natural language queries over sentiment data via semantic view |
| **SentimentSearch** | Cortex Search | Semantic search over sentiment reasons and qualitative insights |
| **SendEmail** | Stored Procedure | Sends HTML-formatted email summaries of findings |
| **data_to_chart** | Built-in | Generates visualizations from query results |

## Get Started

Ready to transform your quantitative research workflow? This guide includes everything you need to get up and running quickly.

**[GitHub Repository →](https://github.com/Snowflake-Labs/sfguide-quantitative-research-aisql-cortex)**

## Related Resources

### Related Guides
- [Agentic AI for Asset Management](https://www.snowflake.com/en/developers/guides/agentic-ai-for-asset-management/)
- [Financial Advisor for Wealth Management](https://www.snowflake.com/en/developers/guides/financial-advisor-for-wealth-management/)
- [Investment Portfolio Analytics with Snowflake Cortex](https://www.snowflake.com/en/developers/guides/investment-portfolio-analytics-with-snowflake-cortex/)

### Cortex Code
- [Snowflake Unveils Cortex Code](https://www.snowflake.com/en/news/press-releases/snowflake-unveils-cortex-code-an-ai-coding-agent-that-drastically-increases-productivity-by-understanding-your-enterprise-data-context/)
- [Cortex Code Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)

### Documentation
- [Cortex AI Functions Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql)
- [Cortex Search Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Intelligence Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- [Snowflake ML Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)


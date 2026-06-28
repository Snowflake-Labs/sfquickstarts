author: Constantin Stanca, Craig LeBlanc and Charlie Hammond
id: investment-portfolio-analytics-with-snowflake-cortex
summary: This solution provides a comprehensive AI-powered system for asset management, integrating document search, portfolio analytics, and a conversational AI assistant.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-Snowflake-Asset-Management-with-Cortex-AI/tree/main

# Investment Portfolio Analytics with Snowflake Cortex
<!-- ------------------------ -->
## Overview

This solution provides a comprehensive AI-powered system for asset management, integrating document search, portfolio analytics, and a conversational AI assistant. It demonstrates how financial firms can transform their research and analysis workflows by centralizing all data and AI capabilities within Snowflake.

### Key Features

* Intelligent Document Search: Use natural language to search through thousands of research documents and reports. This feature, powered by Snowflake's Cortex Search, helps analysts find key insights in seconds.
* Conversational Portfolio Analysis: Analyze portfolio data using simple, conversational queries. The system leverages Snowflake Intelligence with Cortex Analyst and Cortex Search to interpret questions about holdings, risk levels, and sector performance, providing instant, data-driven answers.
* AI Research Assistant: A single AI agent combines both document search and portfolio analysis. Analysts can ask complex questions that require insights from both research documents and live portfolio data, enabling rapid, strategic decision-making.
* Interactive Web Application: A fully functional Streamlit application provides an intuitive dashboard for accessing all the solution's capabilities. It allows for an interactive user experience directly within the Snowflake environment.

### How It Works

This solution leverages Snowflake's native AI features to create a seamless, end-to-end workflow without the need for external tools or data movement.

* Data Ingestion: Research documents (PDFs) and portfolio data are loaded directly into Snowflake.
* Cortex Search: The PDFs are processed, and their content is vectorized to enable semantic search, allowing the system to understand the meaning behind your queries, not just keywords.
* Cortex Analyst: A semantic model is configured to define the relationships and metrics within the portfolio data, making it easy for the AI to understand and respond to analytical questions.
* Snowflake Intelligence: An AI agent is created and equipped with the Cortex Search and Cortex Analyst tools. This allows it to act as an expert research assistant, intelligently routing queries to the appropriate tool to provide comprehensive answers.
* Streamlit: A Streamlit application is deployed on Snowflake to create a user-friendly interface that brings all the components together, providing a single point of access for all AI-powered insights.

### Business Impact

This solution helps financial firms transition from time-consuming, manual research to a more efficient, AI-driven process, resulting in:

* Faster Insights: Analysts can get answers to complex questions in seconds, accelerating the decision-making process.
* Increased Efficiency: Reduces the time spent on manual tasks like organizing and searching through documents.
* Smarter Decisions: Combining portfolio data with external research provides a holistic view, enabling more informed investment strategies.
* Simplified Operations: Eliminates the need for external infrastructure, reducing operational overhead and IT complexity.

### Use Cases and Applications

This solution is a powerful starting point for various applications within the financial sector:

* Investment Research: Instantly find and analyze key information from internal and external research reports.
* Portfolio Management: Get real-time, AI-powered insights into portfolio health, risk, and performance.
* Due Diligence: Accelerate the due diligence process by quickly extracting critical information from SEC filings and company reports.
* Market Analysis: Combine live market data with historical research to identify emerging trends and opportunities.

<!-- ------------------------ -->
## Get Started

- [fork notebook](https://github.com/Snowflake-Labs/sfguide-Snowflake-Asset-Management-with-Cortex-AI/tree/main)

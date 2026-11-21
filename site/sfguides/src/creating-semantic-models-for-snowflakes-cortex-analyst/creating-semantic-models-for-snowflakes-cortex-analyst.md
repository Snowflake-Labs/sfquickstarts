author: Julian Forero, Rachel Blum, Chris Nivera, Jason Summer
id: creating-semantic-models-for-snowflakes-cortex-analyst
summary: Through this guide, you will explore how to get started with Cortex Analyst, which is a fully managed service in Snowflake that provides a conversational interface to interact with structured data in Snowflake.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
heroButtonOverrideLabel: View Quickstart
heroButtonOverrideLink: https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-analyst/#0

# Building AI-powered BI apps using Snowflake Cortex Analyst
<!-- ------------------------ -->
## Overview

Through this guide, you will explore how to get started with [Cortex Analyst](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-analyst), which is a fully managed service in Snowflake that provides a conversational interface to interact with structured data in Snowflake.

**What is Cortex Analyst?**

Cortex Analyst is a fully managed service in [Cortex AI](https://www.snowflake.com/en/data-cloud/cortex) that provides a conversational interface to interact with structured data in Snowflake. It streamlines the development of intuitive, self-service analytics applications for business users, while providing industry-leading accuracy. To deliver high text-to-SQL accuracy, Cortex Analyst uses an agentic AI setup powered by state-of-the-art LLMs. Available as a convenient REST API, Cortex Analyst can seamlessly integrate into any application. This empowers developers to customize how and where business users interact with results, while still benefiting from Snowflake's integrated security and governance features, including role-based access controls (RBAC), to protect valuable data.

**Why use Cortex Analyst?**

Historically, business users have primarily relied on BI dashboards and reports to answer their data questions. However, these resources often lack the flexibility needed, leaving users dependent on overburdened data analysts for updates or answers, which can take days. Cortex Analyst disrupts this cycle by providing a natural language interface with high text-to-SQL accuracy. With Cortex Analyst organizations can streamline the development of intuitive, conversational applications that can enable business users to ask questions using natural language and receive more accurate answers in near real time.

This solution will focus on getting started with Cortex Analyst, teaching the mechanics of how to interact with the Cortex Analyst service and how to define the Semantic Model definitions that enhance the precision of results from this conversational interface over your Snowflake data.

**What you will learn**

* How to construct and configure a Semantic Model for your data
* How to call the Cortex Analyst REST API to use your Semantic Model to enable natural-language question-asking on top of your structured data in Snowflake via Streamlit in Snowflake (SiS) application
* How to integrate Cortex Analyst with Cortex Search to enhance SQL queries generated
* How to enable Join support for Star Schemas
* How to enable multi-turn conversations

<!-- ------------------------ -->
## Get Started

- [view quickstart](https://quickstarts.snowflake.com/guide/getting_started_with_cortex_analyst/index.html#0)
- [fork repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-analyst?_fsi=pU0VIAsc&_fsi=pU0VIAsc)

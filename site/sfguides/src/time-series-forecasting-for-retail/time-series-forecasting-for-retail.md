author: Jim Warner and Charlie Hammond
id: time-series-forecasting-for-retail
summary: This solution demonstrates how retailers can leverage Snowflake's native time series functions and ML.FORECAST capability to predict sales using competitor pricing data.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-time-series-in-retail

# Time Series Forecasting for Retail
<!-- ------------------------ -->
## Overview

This solution demonstrates how retailers can leverage Snowflake's native time series functions and ML.FORECAST capability to predict sales using competitor pricing data. Built around an athletic shoe retailer scenario, the solution shows how to combine irregular competitor pricing updates with daily sales data to create accurate forecasts.

### What's Included

#### Complete Working Example

Athletic shoe retailer sales forecasting scenario

Three core data tables: purchases, product sales by day, and competitor pricing

Sample data generation for realistic retail transaction patterns

#### Ready-to-Deploy Components

* SQL setup script that creates database, schema, tables, and sample data
* Interactive Snowflake notebook with step-by-step analysis
* Complete data pipeline from raw transactions to ML forecasts

#### Time Series Analytics

* TIME\_SLICE function for aggregating sales by day/week/month
* ASOF JOIN to incorporate competitor pricing at correct time points
* Rolling window calculations (7-day average sales)
* LAG functions for previous day sales data

#### Native ML Forecasting

* ML.FORECAST model creation using Snowflake's built-in capabilities
* Multi-product forecasting across different athletic shoe lines
* Scenario planning with different competitor pricing assumptions

### Key Business Benefits

#### Competitor-Aware Forecasting

The solution demonstrates how to incorporate irregular competitor pricing data into sales forecasts—addressing a real retail challenge where competitor prices change at unpredictable intervals.

#### Time Series Data Processing

Shows practical application of Snowflake's TIME\_SLICE, ASOF JOIN, and windowed aggregation functions for retail analytics scenarios.

#### No External Tools Required

All analytics and ML forecasting happen within Snowflake using native functions—no data movement or external ML platforms needed.

#### Production-Ready Pattern

Provides a complete framework that can be adapted for different retail categories, time periods, and external data sources.

#### Technical Capabilities Demonstrated

* **Data** **Aggregation**: TIME\_SLICE for daily/weekly sales summaries
* **Point-in-Time** **Analysis**: ASOF JOIN for competitor pricing alignment
* **Feature** **Engineering**: Rolling averages and lag variables
* **ML** **Forecasting**: Native Snowflake ML.FORECAST functionality
* **Visualization**: Integrated Python charts using Snowpark and matplotlib

### Use Cases

* **Demand Planning**: Predict sales impact of competitor pricing changes
* **Inventory Optimization**: Forecast demand for procurement planning
* **Competitive** **Intelligence**: Model sales response to market dynamics
* **Scenario** **Analysis**: Test different pricing and market conditions

This solution provides a practical foundation for retailers looking to implement time series forecasting within their existing Snowflake environment, with specific focus on incorporating competitive market factors into sales predictions.

<!-- ------------------------ -->
## Get Started

- [fork notebook](https://github.com/Snowflake-Labs/sfguide-time-series-in-retail)

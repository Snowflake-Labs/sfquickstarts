author: Jim Warner, Cameron Shimmin
id: intervention-detection-for-retail-support
summary: It centralizes data preparation, statistical modeling, and visualization in Snowsight Notebooks with Snowpark, enabling teams to measure ROI without running randomized controlled trials.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-Intervention-detection-for-retail-support

# Intervention Detection for Retail Support
<!-- ------------------------ -->
## Overview

It centralizes data preparation, statistical modeling, and visualization in Snowsight Notebooks with Snowpark, enabling teams to measure ROI without running randomized controlled trials.

### Key Features

* Causal Impact Measurement: Estimate the lift in customer spending following support interactions, isolating causation from correlation.
* Counterfactual Analysis & Visualization: Generate and plot “what would have happened without intervention” using regression-based counterfactuals and confidence intervals.
* End-to-End in Snowflake: Use SQL for data prep and Snowpark Python with statsmodels for modeling in a single Snowsight Notebook—no data movement.
* Rapid, Reproducible Setup: A single setup.sql script creates roles, warehouse, database/schema, and loads realistic sample retail data.

### How It Works

* Environment Setup: Execute scripts/setup.sql to create the role, virtual warehouse, database/schema, and populate purchases and support\_tickets via stored procedures.
* Data Preparation: Join purchases to support tickets by customer; compute time deltas (days/weeks) around the intervention; aggregate into a modeling table (support\_purchase\_analysis) with features like WEEK, INTERVENTION, and INTERVENTION\_WEEK.
* Modeling (Snowpark Python): Pull the prepared table into a pandas DataFrame with Snowpark and fit an OLS model in statsmodels to estimate intervention effects.
* Counterfactuals & Plots: Set treatment variables to zero to compute counterfactual predictions; visualize actual vs. predicted and counterfactual with a marked intervention point and 95% confidence bands using matplotlib.
* Execution in Snowsight Notebooks: Import notebooks/0\_start\_here.ipynb, select the created database/schema and warehouse, add statsmodels and matplotlib, and run cells top to bottom.

### Business Impact

* Quantified Support ROI: Puts a measurable dollar value on support interactions with statistical confidence.
* Faster, Defensible Decisions: Provides an RCT alternative for production settings where experiments are impractical.
* Operational Visibility: Reveals effect size and decay over time to optimize staffing, channels, and follow-up strategy.
* Platform Simplicity: Consolidates data, modeling, and visualization within Snowflake to reduce complexity and cost.

### Use Cases and Applications

* Retail & CPG: Measure the impact of service recovery, returns assistance, and concierge programs on subsequent spend.
* Marketing & CX: Quantify lift from outreach after negative experiences; prioritize cohorts for proactive support.
* Subscription/Technology: Assess how support or success calls influence retention, upsell, and expansion.
* Operations & Strategy: Compare alternative support workflows or org changes using causal analysis instead of full RCTs.

<!-- ------------------------ -->
## Get Started

- [fork notebook](https://github.com/Snowflake-Labs/sfguide-Intervention-detection-for-retail-support)

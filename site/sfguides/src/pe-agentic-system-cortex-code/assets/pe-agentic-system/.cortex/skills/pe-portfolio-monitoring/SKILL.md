---
name: pe-portfolio-monitoring
description: "Review portfolio-company performance against an investment case. Use for operating metrics, KPI variance, portfolio reporting or period-over-period monitoring."
---
# Private-Equity Portfolio Monitoring

## Workflow
1. Identify companies, reporting period, fiscal calendar, currency and approved metric definitions. Record denominator, aggregation grain and consolidation perimeter.
2. Use authorized data sources and read-only tools to retrieve actuals, budget and investment-case baselines. Align comparable periods and currency conversions before calculating differences.
3. Check completeness, duplicate reporting, late adjustments and acquisition-related perimeter changes. A missing company or period is not a zero.
4. Apply approved variance thresholds with a deterministic query or calculator. Keep operational movement separate from restatements and definition changes.
5. Retain source query IDs, metric definitions and exceptions. Escalate incomplete coverage before generating investor-facing conclusions.

## Stopping Points
Stop if no governed metric source/tool is configured, definitions conflict or required periods are missing. No monitoring pipeline or scheduled alert is installed by this package. Do not change company records or release reporting automatically.

## Output
Period-scoped metrics, coverage, explained and unexplained variances, query evidence, and review actions.
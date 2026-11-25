---
name: pe-financial-modeling
description: "Review private-equity financial models. Use for DCF, leveraged buyouts, comparable companies, capitalization tables, or exit distributions."
---
# Private-Equity Financial Modeling

## Workflow
1. Establish deal, valuation date, currency, capital structure, model type, and approved assumptions. Do not infer firm discount rates from model output.
2. Read `assurance/contracts.py` and use valuation-input-review for supported extraction contracts. Require evidence review and sign-off for warnings before any computation.
3. Locate and inspect the relevant existing implementation under `integrations/rust/src/` and its tests. Treat README claims as unverified until supported by recorded execution.
4. Use only an approved, tested kernel interface. For DCF record cash-flow formulation, reinvestment, discounting and terminal assumptions; for buyouts record debt mechanics, exit assumptions and dilution. For comparables record selection/date and normalization. For distributions verify entitlement priority and conservation separately.
5. Preserve input, code, configuration and evidence versions. Compare scenarios without changing approved assumptions silently.

## Stopping Points
Stop for missing approved assumptions, unsupported model interfaces, validation failures, missing entitlement terms or unresolved evidence. No executable end-to-end CoCo valuation adapter is supplied by this package. Do not substitute model-generated arithmetic. Investment and distribution approvals remain independent.

## Output
Model scope, supported inputs, validation findings, scenario results only if actually computed, source references, revisions, and unresolved approval requirements. Do not label a boundary check as a completed valuation.
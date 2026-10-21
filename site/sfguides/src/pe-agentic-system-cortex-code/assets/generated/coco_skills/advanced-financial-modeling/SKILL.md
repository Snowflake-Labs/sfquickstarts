---
name: advanced-financial-modeling
description: "Scope advanced financial models. Use for real options, physics-informed neural models, or financial trajectory optimization and model validation."
---
# Advanced Financial Modeling

## Workflow
1. Define the financial question and justify the method against a simpler baseline. Specify objective, states, constraints, horizon and economic interpretation.
2. For real options specify exercise rights and stopping decisions; for physics-informed models identify the governing equations and boundary conditions; for trajectory optimization specify admissible controls and constraints.
3. Identify an approved model implementation, calibration dataset, numerical solver and validation owner before execution. None is supplied by this instruction package.
4. Use quant-model-validation to assess convergence, limiting cases, sensitivity and independent-reference agreement. Separate calibration fit from out-of-sample evidence.
5. Retain parameter, solver, dataset and code revisions and clearly describe model limitations.

## Stopping Points
Stop if the formulation, economic constraints or model implementation are missing. Do not present an illustrative model as approved or improvise a new model in response to a validation failure. Production use requires independent review.

## Output
Model specification, baseline rationale, validation plan, actual results if available, and explicit implementation gaps.
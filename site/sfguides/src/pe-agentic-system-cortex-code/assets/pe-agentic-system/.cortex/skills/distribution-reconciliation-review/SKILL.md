---
name: distribution-reconciliation-review
description: "Review distribution conservation and completeness. Use for missing allocations, shortfalls, over-allocation, duplicate recipients or waterfall result reconciliation."
---
# Distribution Reconciliation Review

## Workflow
1. Confirm account, standard database/schema, distribution date, currency and approved tolerance. Distinguish expected cases from returned allocations so absent outputs cannot disappear.
2. Inspect `examples/live_verification_demo/setup.sql` and `checks.sql`. Their original personal-database namespace is not deployable; use the retargeted notebook bundle and obtain setup approval first.
3. Invoke the configured read-only reconciliation function and applicable DMFs using permitted SQL tools. Keep missing rows, null amounts, duplicates, orphan allocations and negative amounts distinct from net differences.
4. For the five synthetic fixtures, expect one balanced case and four blocked cases. The known shortfall is 63000000 USD; incomplete cases must not certify a total or gap. This is a fixture, not a rerun of the financial kernel.
5. Retain query IDs, actual stored metric values, measurement timestamps and case-level evidence. Clearly distinguish direct invocation from scheduled DMF monitoring. Use built-in data-quality/lineage workflows if available, without inventing their results.

## Stopping Points
The SQL demo is authored but not deployed. Stop if tools, permissions or complete evidence are unavailable. Do not substitute agent arithmetic. Balanced totals do not establish correct investor entitlements. No approval, repair, payment or publishing authority.

## Output
Case, source, status, available proceeds, verified allocated total/gap when complete, completeness findings and escalation. Runtime Cortex Agent skill invocation requires its own recorded trace.
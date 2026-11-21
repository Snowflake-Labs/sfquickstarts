---
name: financial-evaluation-review
description: "Review financial agent evaluation evidence. Use for managed evaluation results, dataset adequacy, failed cases, tool/skill traces or configuration promotion review."
---
# Financial Evaluation Review

## Workflow
1. Confirm agent version, skill content hash, dataset version, metric versions, resolved models and run identifier. Treat missing evidence as unverified, not passed.
2. Inspect the notebook bundle and existing evaluation records. Before any new run require explicit billable approval, a bounded dataset and orchestration budget; additional judge, tool and warehouse consumption is not capped by that budget.
3. Compare expected and actual responses, deterministic findings, failures and errors per record. Do not average away blocked financial checks.
4. Inspect actual traces for skill selection and tool arguments/results. A configured skill, displayed SKILL.md or high judge score is not proof of invocation.
5. Assemble evidence for review. If Experiment Tracking is available, log parameters, metrics and artifacts explicitly; this package does not automatically integrate it.

## Stopping Points
No evaluation has been executed by installing this package. Stop for missing runs, unapproved spending or inaccessible traces. Do not rerun merely to cherry-pick scores or promote a configuration automatically. LLM scores cannot override deterministic failures.

## Output
Run comparison, per-case failures, verified invocation evidence or explicit gaps, deterministic check status, and independent release decision required.
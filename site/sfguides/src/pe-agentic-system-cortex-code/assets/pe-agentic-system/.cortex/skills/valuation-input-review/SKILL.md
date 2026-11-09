---
name: valuation-input-review
description: "Check valuation extraction contracts with the implemented assurance boundary. Use for missing evidence, malformed extraction, ratio errors or incompatible discount and terminal-growth assumptions."
---
# Valuation Input Review

## Workflow
1. Confirm extracted inputs and separately approved discount rate, terminal growth and projection horizon. Do not choose firm assumptions on the user's behalf.
2. For a synthetic demonstration run `python3 examples/coco_skill_demo.py` from the project root. The script uses `assurance.contracts.cross_boundary(strict=True)` and requires Pydantic 2. It does not connect to Snowflake or call a model.
3. For user data use the script's `review_inputs` function only after validating caller configuration. Preserve the extraction hash and findings. Record approved assumptions separately because the hash covers the extraction only.
4. Report `blocked` for failed validation and `review_required` for warnings. `checks_passed` permits further evidence/approval review, not publication or computation by the agent.
5. Retain exact script output and source hashes. Label direct notebook execution as supporting-code evidence; retain a CoCo transcript separately when this skill is actually invoked.

## Stopping Points
Stop for missing Pydantic, unavailable code, malformed configuration or unexpected exceptions. No silent repairs. This boundary does not authenticate documents or establish that quotes support values; required evidence review and kernel execution remain separate.

## Output
Status, extraction hash, findings, configuration, synthetic-data indicator when relevant, and required next review. No valuation or payment authorization.
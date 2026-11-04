# Adapting this to your own agent

The quickstart is a worked example. This guide maps each part to the decisions you make for your own agent, whatever the domain. Use the templates in `templates/` as starting points.

## 1. Start from how your data fails, not from the questions

An evaluation measures only what its dataset makes difficult. Before writing questions, list the ways a plausible answer could be wrong in your data, and make sure the data contains them.

| Northbank trap | The general pattern | Where to find yours |
|---|---|---|
| Duplicate submissions | Two defensible counts, only one right | Dedup rules, soft deletes, test accounts, restated records |
| Decision date vs received date | The wrong date column gives a close but wrong number | Any table with several date columns |
| Superseded credit policy in the index | Old and new versions of a document are both searchable | Policies, price lists, product terms, runbooks |
| Subtle vulnerability notes | The signal is implied, not stated | Free-text notes, tickets, call summaries |
| Distractor notes | The right keywords about the wrong subject | Notes that mention third parties, hypotheticals, negations |
| 2025-Q3 arrears spike | A real anomaly the agent should surface, not smooth over | Known incidents, launches, data outages |

## 2. Compute ground truth independently

- Write the SQL that answers each question against the **source tables**, not through the agent or the semantic view. Put that SQL and its result in `tool_output`, so tool execution accuracy can compare against it.
- In `ground_truth_output`, state the answer **and** the plausible wrong answer you want rejected: "20,001 unique applications. An answer of 20,311 counts duplicates and is incorrect."
- Use absolute dates ("between 1 April and 30 June 2026"), never "last quarter", so the answers don't drift.

## 3. List the expected tools on every row

- `ground_truth_invocations` drives tool selection and tool execution accuracy. A row without it silently drops out of both.
- Use `[]` where calling any tool is wrong (out-of-scope questions). This catches agents that search before declining.
- Decide deliberately whether a lookup is required. In Northbank, the vulnerability questions require the case record as an audit trail. That's a policy choice, and it changes the scores.

## 4. Cover the tiers your users depend on

Northbank's 40 questions span core metrics, cross-tool reasoning, policy change, affordability (custom tool), data quality, vulnerability with non-vulnerable controls, and refusals. For your agent:

- include **controls**: cases that look like the hard case but aren't, so a judge can't score well by always flagging;
- start with 20–40 questions drawn from real user queries;
- add a question every time you find a failure in production.

## 5. Version the agent and change one thing at a time

- Commit a version for every change you want to measure (`ALTER AGENT ... COMMIT`), and evaluate the committed `VERSION$N`, not `LIVE` or `DEFAULT`.
- Committing moves the default. Treat a change of default as a release event.
- Change instructions **or** model **or** tools in one version, never several at once. Northbank's VERSION$2 shows why: richer instructions fixed the targeted failures and broke retrieval elsewhere.

## 6. Pin the judge

- Pin every system metric to an exact metric version (`version: v3_0`) and keep it across runs. Scores from different versions aren't comparable.
- Upgrade deliberately when a judge model deprecation is announced. A pinned version whose judge is retired fails only after the agent has already run.
- Don't use your agent's orchestration model as the judge.

## 7. Write custom metrics in your regulator's or owner's terms

- Phrase the rubric as a short list of yes/no checks, and score it on a coarse 0/5/10 scale. Say what earns each score.
- Use `{{tool_info}}` when the metric is about what the agent retrieved (grounding, citations, using the current document).
- Set `model` explicitly.
- Before trusting the metric, check that scores spread across the range, and read the low-score explanations. A judge that scores everything 10 agrees with everything and flags nothing.
- If you compare two judges, compare them per metric. Neither is uniformly stricter.

Template: `templates/eval_config_template.yaml`.

## 8. Measure variance, then gate

- Run the final version at least three times on the same dataset.
- Set each floor at roughly the lowest run minus one run-to-run range. `07_ci_gate.sql` computes this for you.
- For harm, gate on a per-row rule (any single score of 0 fails), not on an average.
- Fail closed: a run with a missing metric fails, and `PARTIALLY_COMPLETED` counts as a final status.
- Look at which questions change tool path between identical runs. They are the ones to fix first, and the average hides them.

## 9. Budget for it

- Logical consistency is usually the most expensive metric, because it sends the whole trace to its judge. Run it on release candidates, and run the cheaper metrics nightly.
- Tool selection uses no judge, so it costs nothing beyond the agent invocations you're already paying for.
- Use a small probe dataset for judge and config experiments.

`08_cost.sql` attributes cost per run and metric.

## 10. Know what evaluations don't cover yet

- Evaluations don't pass session attributes, so row access policies keyed on session variables aren't exercised.
- MCP tools aren't called during an evaluation.
- Files written by the code execution tool aren't kept.

Cover these with other tests.

## Checklist

- [ ] Traps in the data that match how your data really fails
- [ ] Ground truth computed in SQL, with the wrong-but-plausible answer named
- [ ] `ground_truth_invocations` on every row, `[]` for refusals
- [ ] Controls alongside every hard case
- [ ] Committed agent versions, one change each
- [ ] System metrics pinned to an exact version; judge differs from the orchestration model
- [ ] Custom metrics with a calibrated judge, checked for spread
- [ ] Three runs before setting floors; per-row rule for harm
- [ ] Gate Tasks pinned to a committed version and config
- [ ] Cost per run known before scheduling

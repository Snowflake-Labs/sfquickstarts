sidebar: true
sidebar_json: ai-cookbook
author: Parker Erickson
id: ai-cookbook-agent-feedback-to-evals
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Mine thumbs-down feedback and user rephrases from agent traces, confirm each with one LLM call, and write a deduplicated eval dataset.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/ai-observability/agent-feedback-to-evals

# Turn agent feedback and rephrased questions into an evaluation dataset

## Overview

Real users tell you where an agent falls short in two ways: they click thumbs down, or they ask the same thing again in different words. This recipe reads both signals from the agent's observability events, confirms each candidate with a single LLM call, drafts a self-contained test question with ground-truth criteria, drops near-duplicates, and writes `EVAL_DATASET` in the `INPUT_QUERY` / `GROUND_TRUTH` shape that [agent evaluations](/en/developers/guides/ai-cookbook/agent-evaluations/) runs against.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Evaluate, Operate |
| Topics | AI Observability, Cortex Agents |
| Time | 40 min |
| Edition | Enterprise |
| Regions | Any region with Cortex Agents and AI_COMPLETE, AI_SIMILARITY, and AI_EMBED for the chosen models |
| Privileges | ACCOUNTADMIN for 01_setup.sql and 02_grant_unredacted.sql; everything else runs as a COOKBOOK_* role. A programmatic access token for the optional feedback notebook |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/ai-observability/agent-feedback-to-evals) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/ai-observability/agent-feedback-to-evals/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bagent-feedback-to-evals%5D%20&recipe=recipes%2Fai-observability%2Fagent-feedback-to-evals) |

## When to use this

- You have an agent in use and want evaluation questions that reflect where it actually fails, not only questions you thought of in advance.
- You want the mining to be a rerunnable SQL job with every stage inspectable.

When not to use this:

- You need to score answers: that is `EXECUTE_AI_EVALUATION`; see [agent evaluations](/en/developers/guides/ai-cookbook/agent-evaluations/).
- You need latency or per-request debugging: see [diagnose-agent-requests](/en/developers/guides/ai-cookbook/diagnose-agent-requests/).
- You cannot grant a role access to conversation text. Without `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE`, questions and feedback text read as NULL and there is nothing to mine.

## How it works

![How it works: Turn agent feedback and rephrased questions into an evaluation dataset](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/agent-feedback-to-evals/assets/agent-feedback-to-evals-01.png)

1. **Two signals.** Explicit: a `CORTEX_AGENT_FEEDBACK` event with `positive = false`, linked to the turn it rates. Implicit: a follow-up turn in a thread whose question re-asks the previous one. A turn's `parent_message_id` equals the previous turn's `message_id`, so pairs join exactly.
2. **Similarity is a pre-filter, not the decision.** `AI_SIMILARITY` runs once per pair and is stored. A real rephrase ("How is Tofu doing?" then "I meant total Tofu revenue by region...") scores about 0.59 and a genuine follow-up ("What was total revenue in the North region?" then "And how does that compare to the South?") about 0.42, so no single threshold separates them. The floor only limits how many pairs reach the LLM.
3. **One LLM call per candidate.** A single `AI_COMPLETE` with a JSON schema returns whether the pair is dissatisfaction, a self-contained `eval_question`, an `intent`, `ground_truth_output` criteria, and `expected_tools`. Rows the model answers badly stay in `EVAL_CANDIDATES` as `invalid_llm_output` instead of disappearing. That depends on `AI_SQL_ERROR_HANDLING_USE_FAIL_ON_ERROR = FALSE`: with `TRUE`, one failed call aborts the whole `CREATE TABLE AS`, so `05_mine_signals.sql` sets it to `FALSE` for its own session.
4. **Dedupe by meaning.** `AI_EMBED` embeds each kept question once; a candidate whose cosine similarity to a higher-priority one is at or above 0.92 is dropped.
5. **Drafts, not truth.** Ground truth is written as criteria ("must filter to Tofu, cover July 2025 to June 2026, one figure per region"), and every row carries `review_status: draft` for a human to check before the dataset is used.

## Prerequisites

| Requirement | Notes |
|---|---|
| Cortex Agents, `AI_COMPLETE`, `AI_SIMILARITY`, `AI_EMBED` | Models: `claude-sonnet-4-6` and `snowflake-arctic-embed-l-v2.0`, set at the top of `05_mine_signals.sql` |
| `SNOWFLAKE.CORTEX_USER` | Granted to the recipe role by `01_setup.sql` |
| `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE` | Account-level privilege, granted to the recipe role only by `02_grant_unredacted.sql` and removed when teardown drops the role |
| Programmatic access token (optional) | Only for `notebooks/01_submit_feedback.ipynb`, exported as `SNOWFLAKE_PAT`. Without it, the recipe mines rephrases only. You create the token yourself for your own user. A `TYPE = PERSON` user can generate a token without a network policy but cannot sign in with it unless the user, or the whole account, is subject to a network policy that allows the address the notebook runs from (or an authentication policy relaxes the requirement) |
| Python | `snowflake-snowpark-python` and `requests` for the notebook |

## Quickstart

1. `sql/01_setup.sql` as `ACCOUNTADMIN`: role (granted to you), warehouse, database.
2. `sql/02_grant_unredacted.sql` as `ACCOUNTADMIN`: lets the recipe role read conversation text.
3. `sql/03_agent.sql`: 800 synthetic Northwind orders, a semantic view, and `ORDERS_ASSISTANT`.
4. `sql/04_simulate_traffic.sql`: replays 8 scripted conversations (13 turns) through `DATA_AGENT_RUN`, one thread per conversation, logging every call in `RUN_LOG`.
5. Optional: `notebooks/01_submit_feedback.ipynb` sends the thumbs up or down in `FEEDBACK_SCRIPT` through the Feedback REST API.
6. `sql/05_mine_signals.sql`: builds `AGENT_TURNS`, `FEEDBACK_EVENTS`, `TURN_PAIRS`, `EVAL_CANDIDATES`, `CANDIDATE_EMBEDDINGS`, and `EVAL_DATASET`, then prints a funnel.
7. Review `EVAL_CANDIDATES`, then run the dataset with [agent evaluations](/en/developers/guides/ai-cookbook/agent-evaluations/).
8. `sql/99_teardown.sql` when done.

## Walkthrough

### Traffic with threads, in SQL

```sql
body := TO_JSON(OBJECT_CONSTRUCT(
    'thread_id', thread_id,                 -- NULL on the first turn, so OBJECT_CONSTRUCT omits it
    'parent_message_id', parent_id,
    'messages', ARRAY_CONSTRUCT(OBJECT_CONSTRUCT('role', 'user',
        'content', ARRAY_CONSTRUCT(OBJECT_CONSTRUCT('type', 'text', 'text', question))))));
SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(:AGENT_FQN, :body, TRUE)) INTO :resp;
thread_id := resp:metadata:thread_id::NUMBER;
parent_id := resp:metadata:assistant_message_id::NUMBER;
```

The third argument creates a thread when the body has none. The response metadata carries the thread id and assistant message id for the next turn. Each call is in its own exception block that writes the error to `RUN_LOG` and skips the rest of that conversation.

### Explicit feedback

The Feedback REST API body has `orig_request_id`, `positive`, `feedback_message`, `categories`, and `thread_id`. The notebook finds each turn's request id in the trace (the trace's `message_id` equals the assistant message id returned by `DATA_AGENT_RUN`), posts the feedback, and records every HTTP status in `FEEDBACK_LOG`.

On the read side, the documented filter is `RECORD:name = 'CORTEX_AGENT_FEEDBACK'`; the documentation does not specify where inside the event the fields live. `05_mine_signals.sql` therefore matches them by name across both `VALUE` and `RECORD_ATTRIBUTES`, links by request id, and falls back to the latest earlier turn in the same thread. The funnel reports feedback it could not link.

### Rephrase pairs

```sql
SELECT cur.request_id, prev.question AS prev_question, cur.question,
       AI_SIMILARITY(prev.question, cur.question) AS similarity
FROM AGENT_TURNS cur
JOIN AGENT_TURNS prev ON prev.thread_id = cur.thread_id AND prev.message_id = cur.parent_message_id
WHERE cur.parent_message_id > 0;
```

### One call per candidate

```sql
AI_COMPLETE($model,
    '<instructions> ... SIGNAL:\n' || TO_JSON(OBJECT_CONSTRUCT('source', s.source,
        'previous_question', s.prev_question, 'previous_answer', LEFT(s.prev_answer, 2000),
        'question', s.question, 'answer', LEFT(s.answer, 2000), 'feedback_message', s.feedback_message)),
    model_parameters => {'temperature': 0, 'max_tokens': 800},
    response_format  => {'type': 'json', 'schema': {...is_dissatisfaction, reason, eval_question,
                                                     intent, ground_truth_output, expected_tools...}})
```

The conversation goes in as a JSON document and the instructions tell the model to treat it as data. The output is stored, never executed.

### Using the dataset

`EVAL_DATASET` has the two columns an evaluation config maps:

```yaml
dataset:
  dataset_type: "CORTEX AGENT"
  table_name: "COOKBOOK_AGENT_FEEDBACK_TO_EVALS.APP.EVAL_DATASET"
  dataset_name: "ORDERS_MINED_DATASET"
  column_mapping:
    query_text: "INPUT_QUERY"
    ground_truth: "GROUND_TRUTH"
```

`GROUND_TRUTH` contains `ground_truth_output` (read by `answer_correctness`) and `expected_tools`, plus `intent`, `source`, `source_request_id`, and `review_status` for your own filtering. Staging the config and running `EXECUTE_AI_EVALUATION` is covered in [agent evaluations](/en/developers/guides/ai-cookbook/agent-evaluations/).

## Verify

The funnel at the end of `05_mine_signals.sql`, for the scripted traffic without the notebook, looks like:

| Stage | Expected |
|---|---|
| agent turns / turns with question text | 13 or more, equal counts (unequal means the unredacted grant is missing) |
| follow-up pairs | 5 (conversations 3, 4, 5, 6, 8), more if you rerun 04 |
| pairs above similarity floor | most of them; "Break that down by channel" usually falls below 0.40 |
| confirmed dissatisfaction | the Tofu and Online-share rephrases; the North vs South follow-up is judged not dissatisfaction |
| invalid LLM output | 0 |
| eval dataset rows | one per distinct confirmed question after dedupe |

If you ran the notebook, `FEEDBACK_LOG` has three rows with their HTTP status, `feedback events` counts what arrived, and each linked thumbs-down becomes an `explicit_negative` candidate. Check `feedback not linked to a turn`: it should be 0.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `turns with question text` is 0 | The role lacks `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE`, so text reads as NULL | Run `02_grant_unredacted.sql` |
| A rephrase you expected is missing | Its similarity fell below the floor | Lower `similarity_floor`; the LLM step still filters follow-ups |
| Borderline pairs judged differently between runs | "Best month?" then a fully specified version of the same question can read as either a rephrase or a clarification | Keep humans in the loop through `review_status`; tune the instructions if your users' patterns differ |
| Duplicate questions after rerunning 04 | Each rerun adds new traffic with the same questions | Dedupe removes near-identical ones; truncate old traffic by filtering `AGENT_TURNS` on `started_at` if needed |
| Notebook raises `Set SNOWFLAKE_PAT` | No token in the environment | Export a programmatic access token for a user that can use the recipe role |
| Every row in `FEEDBACK_LOG` shows an authentication error, although the token is current | The token's user is not subject to a network policy, so Snowflake rejects sign-in with a programmatic access token | Activate a network policy for that user (or the account) that allows the notebook's address, or an authentication policy with `PAT_POLICY = (NETWORK_POLICY_EVALUATION = ENFORCED_NOT_REQUIRED)`; then rerun the submit cell |
| Notebook raises `feedback submission(s) failed` | HTTP error from the Feedback API (auth, role, or network) | Read `RESPONSE_BODY` in `FEEDBACK_LOG` |
| `feedback not linked to a turn` above 0 | The event carried neither a request id nor a thread id that matches a turn | Submit feedback with `orig_request_id` (the notebook does) |
| Draft ground truth contains figures | The model can copy numbers from the agent's own answer, which may be the wrong answer being tested | The prompt tells it not to; still treat every draft as unverified and have a reviewer check or add exact values from the data |
| Some traces missing | Observability telemetry is best-effort; a span can be dropped or arrive late | Rerun `05` later; treat the dataset as a sample, not a census |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It drops the role (which removes the unredacted grant), the database (agent, semantic view, data, and every mined table), and the warehouse. Events already written stay in `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`, which can't be modified.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Install or enable the bundled agent-studio and cortex-ai-function-studio skills if they are not
already available; use agent-studio for evaluation follow-ups and cortex-ai-function-studio for
AI function cost or model questions. Then, from recipes/ai-observability/agent-feedback-to-evals:
1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(); and show me the result.
   Stop if it is not the account I expect.
2. Run sql/01_setup.sql with snow sql -f (it switches to ACCOUNTADMIN).
3. sql/02_grant_unredacted.sql grants READ UNREDACTED AI OBSERVABILITY EVENTS TABLE ON ACCOUNT,
   an account-level privilege that lets the recipe role read conversation text. Show me the
   statement and wait for my yes before running it.
4. Run sql/03_agent.sql and sql/04_simulate_traffic.sql. Report any RUN_LOG rows whose
   RUN_STATUS is not 'completed'.
5. Ask me whether I want explicit feedback. If I do, I create a programmatic access token for
   my own user and export SNOWFLAKE_PAT myself; never create, print, read, or store the token.
   Then run notebooks/01_submit_feedback.ipynb and report the HTTP status of each row in
   FEEDBACK_LOG. Otherwise skip the notebook.
6. Run sql/05_mine_signals.sql and show me the funnel and the rows of EVAL_CANDIDATES with
   llm_status, is_dissatisfaction, reason, and eval_question.
7. When I say so, run sql/99_teardown.sql and confirm SHOW DATABASES, SHOW WAREHOUSES and
   SHOW ROLES LIKE 'COOKBOOK_AGENT_FEEDBACK_TO_EVALS%' return nothing.
Never drop or alter objects that do not start with COOKBOOK_.
```

## Related skills

- `agent-studio` (bundled with Cortex Code): building and running agent evaluations and the `agent-observability-report` for aggregate monitoring. Use it with the dataset this recipe writes.
- `cortex-ai-function-studio` (bundled): choosing, testing, and estimating the cost of the AI functions used here (`AI_COMPLETE`, `AI_SIMILARITY`, `AI_EMBED`).

## References

- [Monitor Cortex Agent requests](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-monitor)
- [Feedback REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-feedback-rest-api)
- [Use threads with the Cortex Agent REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-threads)
- [DATA_AGENT_RUN](https://docs.snowflake.com/en/sql-reference/functions/data_agent_run-snowflake-cortex)
- [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete)
- [AI_SIMILARITY](https://docs.snowflake.com/en/sql-reference/functions/ai_similarity)
- [AI_EMBED](https://docs.snowflake.com/en/sql-reference/functions/ai_embed)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)

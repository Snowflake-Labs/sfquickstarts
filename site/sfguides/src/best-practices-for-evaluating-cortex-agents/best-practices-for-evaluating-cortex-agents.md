
id: best-practices-for-evaluating-cortex-agents
language: en
summary: Learn how to evaluate, version, deploy, and monitor Cortex Agents in production using Snowflake's built-in evaluation framework, CI/CD pipelines, and observability tools.
author: Josh Reini, Elliott Botwick, Larry Orimoloye
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Published

# Best Practices for Evaluating Cortex Agents

### Overview

This guide assumes you have already read [Best Practices for Building Cortex Agents](https://quickstarts.snowflake.com/guide/best-practices-to-building-cortex-agents). The scope here is the evaluation cycle in detail, from early prototyping to production observability.

Evaluation helps you understand how agents perform across a variety of scenarios so you can systematically improve their quality.

### What you'll learn
- How to define a representative evaluation dataset from real user interactions
- How to choose and create evaluation metrics (built-in and custom)
- How to iterate on your agent using versioning and evaluation results
- How to set up CI/CD pipelines for automated agent quality gates
- How to deploy agents safely using versioning and aliases
- How to monitor agents in production with observability and alerts

### Prerequisites
- A Snowflake account with access to [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence/getting-started)
- A Cortex Agent you want to evaluate
- Familiarity with the [Best Practices for Building Cortex Agents](https://quickstarts.snowflake.com/guide/best-practices-to-building-cortex-agents) guide

<!-- ------------------------ -->
## Defining Your Evaluation Set

There are several ways to construct your evaluation set depending on the resources available and your familiarity with the end use case. The best approach is to ask a willing set of end users what they hope to get out of your agent.

You can do this by having future users draft queries, or better yet, let them try out a prototype of your agent in a trial period. By allowing future users to try your agent, you get a more accurate sense of how they would actually use it. This also builds excitement around your agent to improve adoption when it is deployed in production.

### Building from user logs with Cortex Code

Once users have had a chance to try your agent, you can query the logs to build a representative dataset using Cortex Code. Cortex Code will create the dataset from the logs and let you edit and define the ideal tool execution sequence for each query if it differs from what happened in the logs.

If it prompts you to select metrics, choose all of the metrics available so Cortex Code will add the expected tool uses to the dataset. This will be useful later.

Try it out by asking Cortex Code:

> _"Help me create an evaluation dataset for my agent DATABASE.SCHEMA.AGENT_NAME"_

Once the dataset is generated, you can validate the expected responses in the dataset-curation skill. The skill walks you through each response one-by-one to validate.

### Without user logs

If you can't find willing users to test your agent, you can still use Cortex Code to build your eval set. The resulting dataset will not be as representative as one produced from end users, which should affect your deployment strategy.

Once you have created your evaluation dataset, validate that the responses are what you expect.


### Ground Truth Considerations

Ground truth responses should be specific enough to meaningfully validate your agent's answers, but not so specific that non-determinism in LLM-generated responses causes false negatives. For example, for an input query like "How can I decrease my support time to resolution?", a ground truth of "Follow known best practices related to technical support" may be too generic and match partially correct answers. On the other hand, a ground truth that names specific entities, ticket counts, or resolution time targets risks penalizing correct answers that surface different but equally valid details from the underlying data. Aim for ground truth that captures the key facts and constraints of a correct answer without over-indexing on specific entities or figures that may vary between valid responses.

Be mindful of ground truth staleness - questions tied to real-time or frequently changing data (e.g., "what is the current stock price of Snowflake?") will produce ground truth that becomes incorrect over time. To avoid this, consider using input queries anchored to fixed points in time ("what was the closing price of Snowflake stock on January 31st, 2025?"), use ground truth that validates qualitative behavior rather than specific numeric values, or generate ground truth programmatically at evaluation run time so it reflects the current state of the data immediately before the eval executes.


<!-- ------------------------ -->
## Choosing Metrics

### Built-in metrics

If you have ground truth expected responses available (or can create them using the dataset-curation skill), **answer correctness** is the best single metric to evaluate response accuracy.

**Logical consistency** is a reference-free metric available out of the box that understands the entire execution trace of your agent. Because it does not rely on ground truth responses, it is easy to use. It can also catch agent mistakes that would be missed by looking at the response alone, such as an incorrect tool call or the agent not adhering to system instructions.

### Creating custom metrics

Custom evaluation metrics can be created by uploading a run configuration YAML to a Snowflake stage. Custom metrics are configured with a name, score ranges, and prompt:

```yaml
metrics:
  - name: groundedness
    score_ranges:
      min_score: [0, 0.33]
      median_score: [0.34, 0.66]
      max_score: [0.67, 1]
    prompt: |
      You are evaluating the groundedness of an AI agent's response.

      User Query: {{input}}
      Agent Response: {{output}}
      Expected Answer: {{ground_truth}}

      Rate whether each statement in the response is supported
      by the tool outputs and retrieved data in the execution trace...
```

Custom metric prompts can use template variables including `input`, `output`, `ground_truth`, tool information and more that are automatically populated from the evaluation run. These let you explicitly reference specific fields in your prompt.

The complete agent execution trace is always provided to the LLM judge as context, regardless of which template variables you use in your prompt. Template variables give you a way to explicitly call out specific fields in your scoring rubric, but the judge has access to the full trace — including all tool calls, tool outputs, intermediate reasoning steps, and span details — even if you don't reference them via variables.

See the [documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) for all available template variables.

<!-- ------------------------ -->
## Improving the Agent

Once your evaluation metrics are well aligned with your human annotations, you can start improving your agent. This can be a much faster process because you get quick, automated feedback for each change.

### Use versioning to structure iteration

> **Preview Feature — Private:** Agent versioning is available to select accounts.

Every improvement cycle should map cleanly to the agent version lifecycle:

- **Live version** → where you make changes
- **Named versions** → checkpoints you evaluate and compare

For each iteration:
1. Make changes on the live version (`ALTER AGENT`)
2. Run evals against the live version or a committed candidate
3. Commit when you want a stable snapshot to compare against prior runs

```sql
ALTER AGENT my_agent COMMIT
COMMENT = 'Improved tool selection logic';
```

For each new version of your agent, use `ALTER AGENT`. This ensures that evaluation runs are preserved. Avoid using `CREATE OR REPLACE AGENT` — it is destructive to past evaluation runs and monitoring traces.

### Determining what to change

To determine what changes to make, you can:

- Read the evaluation explanations from LLM judges to determine what's going wrong
- Examine production failures with negative feedback or unclosed conversations
- Use the agent optimization flow in Cortex Code, which uses evaluation results to suggest and test changes

Try it out by asking Cortex Code:

> _"Help me optimize my agent DATABASE.SCHEMA.AGENT_NAME"_

Make one change at a time, and create a new agent evaluation run with each change. This ensures the effect of each change is properly isolated so you can measure its impact precisely. Be sure to not only look at overall results but understand trace-level regressions as well.

Continue to iterate through `ALTER AGENT` until reaching the pre-decided production threshold for all metrics.

### Choosing the orchestration LLM

To find the optimal performance for your use case, start with a powerful SOTA LLM such as the latest Claude Opus. Then, using the performance with Opus as a benchmark, create an evaluation run with a cheaper, less powerful LLM. Inspect the results and determine if the less powerful LLM can achieve similar performance.

By starting with a SOTA LLM, you determine the maximum performance of your agent given the tools available.

<!-- ------------------------ -->
## Setting Up CI/CD

With programmatic evaluations, you can integrate agent quality checks directly into CI/CD pipelines. This brings LLMOps closer to traditional software development best practices.

Cortex Agent versioning offers the ability to create agent snapshots, allowing you to test, promote, and roll back across multiple versions.

### Source-controlling your agent configuration

Before setting up CI/CD, store your agent artifacts in version control:

- Agent specification YAML (instructions, tool descriptions, orchestration configs)
- Semantic View YAML (tables, metrics, relationships, verified queries)
- Evaluation configuration YAML (metrics, dataset references, custom metric prompts)
- Evaluation dataset definitions (or references to registered Snowflake datasets)

Git history provides an audit trail of every agent change, and pull requests provide code review before any modification reaches a shared environment.

### Automating agent evaluations

A typical GitHub Actions pipeline:

1. A developer opens a PR that modifies the agent spec
2. The CI workflow deploys the candidate spec to a staging agent
3. The workflow uploads the eval config YAML to a Snowflake stage and starts an evaluation run
4. The workflow polls until the evaluation completes, then retrieves results
5. A quality gate checks whether metrics meet your thresholds (e.g., `answer_correctness >= 0.75`)
6. If the gate passes, the PR is allowed to merge. If it fails, the PR is blocked and the developer can inspect the evaluation results to understand what regressed

Consider using progressive thresholds across environments: lenient and advisory in dev to avoid blocking experimentation, stricter hard gates in QA, and the highest thresholds in production paired with automatic rollback on failure. Set thresholds based on observed baselines from multiple eval runs rather than aspirational targets — thresholds set too aggressively create flaky gates that erode trust in the pipeline.


### Tips for CI/CD with agent evaluations

- **Pin the orchestration LLM:** Use a specific model (e.g., `claude-4-sonnet`) rather than `auto`. This ensures CI results are reproducible and not affected by model rotation.
- **Use a dedicated warehouse and role:** Run CI evaluation jobs under a service role with a dedicated warehouse to avoid contention and simplify cost tracking.
- **Version your eval datasets:** Keep evaluation datasets in version control alongside the agent spec, or reference a registered Snowflake dataset by name. This ensures the same dataset is used across all pipeline runs.
- **Budget for LLM judge costs:** Each evaluation run invokes `CORTEX.COMPLETE` for every metric on every question in your dataset. For a 20-question dataset with 3 metrics, that is 60 LLM judge calls per run.
- **Combine CI/CD with scheduled testing:** CI/CD evaluations guard against regressions from agent configuration changes. Cadence-based scheduled testing (covered next) catches regressions from external factors such as model updates, data changes, or tool configuration drift. Both are necessary for comprehensive quality assurance.

<!-- ------------------------ -->
## Deploying to Production

Depending on your confidence in your eval set and the stakes of your use case, you can choose a deployment strategy. In all cases, agent versioning is what makes safe deployment possible.

### Versioning model

Cortex Agent versioning gives you a clean separation between development and production:

- **Live version** → where you iterate, test, and break things
- **Named versions** → immutable snapshots you can safely deploy
- **Aliases** (e.g. `production`, `staging`) → how you route traffic

### Deployment flow

**1. Develop on the live version**

Iterate on prompts, tools, and configs. Test interactively or against evals.

**2. Commit to create a production candidate**

This creates a new immutable version (e.g. `VERSION$4`):

```sql
ALTER AGENT my_agent COMMIT
COMMENT = 'Improved retrieval + tool usage';
```

**3. Test the new version explicitly**

Run evals against `VERSION$4`. Optionally route internal traffic to it via a staging alias.

**4. Promote the agent to production**

All traffic pointing at `production` now uses the new version:

```sql
ALTER AGENT my_agent
MODIFY VERSION VERSION$4 SET ALIAS = production;
```

**5. Rollback instantly if needed**

```sql
ALTER AGENT my_agent
MODIFY VERSION VERSION$3 SET ALIAS = production;
```

This alias-based routing is what enables safe, reversible deployments.

### Regular agent testing

At a defined cadence (hourly or daily), test your eval set with the production version of your agent to detect changes in performance. Choose the cadence based on your use case and your willingness to absorb the cost of running evaluations. We recommend testing no less than daily.

Your agent can change in unexpected ways due to changes in the underlying LLM, tools, or data. Regular evals give you a proactive signal before users notice degradation. While CI/CD evaluations protect against agent configuration changes, cadence-based testing catches issues from outside the agent configuration including model degradation, data changes, or tool configuration drift.

### Scheduled evaluation task

Store your eval dataset (YAML config) in a stage, call your evaluation procedure, and schedule it:

```sql
CREATE OR REPLACE TASK AI_OBSERVABILITY_RUN_TASK_1
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '10 MINUTE'
AS
CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT(
    'run_name', 'run_test_yaml_prog_' || UUID_STRING()
  ),
  '@<database>.<schema>.<stage>/<eval_config>.yaml'
);
```

Start the task:

```sql
EXECUTE TASK AI_OBSERVABILITY_RUN_TASK_1;
```

> To help avoid unexpected regressions due to LLM changes, pin a specific model for orchestration rather than choosing `auto`. This ensures the LLM used is the one you have determined best for your use case.
>

### Goal Setting

When setting goals for your evaluation metrics, it can be beneficial to focus on consistency over perfection. Evaluations should be run at a regular cadence, and metric score results should be monitored for variance. This can be achieved via the the compare tab in the Agent Evaluations UI or by directly querying the results from the event table. In many cases - a stable score can be more meaningful than a high one. An aggregate score of 100% on a given metric typically signals that your dataset is too easy and risks overfitting to cases your agent already handles well - the dataset should include challenging questions that stress the boundaries of your agent's capabilities. Additionally - metric scores jumping from 80% -> 65% -> 90% with minimal changes to the evaluation set or agent instructions suggest that your agent may be failing to answer queries in a consistent manner - which can often be addressed by adding more explicit instructions, better tool descriptions, verified queries etc. 

<!-- ------------------------ -->
## Production Observability

Once your agent is in production, all usage lands in Snowflake's agent observability event logs. To analyze it, you can use the Cortex Code skill `agent-observability-report`. It pulls 110 metrics from Snowflake agent observability event logs: usage, latency percentiles, token economics, tool execution stats, user feedback breakdowns, and conversation depth.

### What you can monitor

- Usage and adoption
- Performance and latency
- Token costs
- Reliability
- Tool execution patterns
- Conversation metadata (completion rate, conversation depth)
- User feedback

Analyzing these metrics helps you deeply understand how your agent is being used and how well it is working. You can identify cases where your agent struggles by looking for low usage, high latency or token costs, reliability issues, low completion rates, or negative feedback.

Then, add these queries to your evaluation dataset and improve your agent by iterating either manually or by using agent optimization in Cortex Code.

### Setting up alerts

Alerts can monitor metrics of interest from Snowflake agent observability event logs. Below are examples for evaluation accuracy, latency, reliability, and user feedback thresholds.

First, create a notification integration (one-time setup):

```sql
CREATE OR REPLACE NOTIFICATION INTEGRATION my_email_int
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ('admin@example.com');
```

**Agent evaluation threshold alert**

```sql
CREATE OR REPLACE ALERT agent_eval_threshold_alert
  WAREHOUSE = my_warehouse
  SCHEDULE = '1 HOUR'
  IF (EXISTS (
    SELECT *
    FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
      'my_db',        -- database
      'my_schema',    -- schema
      'my_agent',     -- agent name
      'CORTEX AGENT', -- agent type
      'my_run'        -- evaluation run name
    ))
    WHERE METRIC_NAME = 'answer_correctness'
      AND EVAL_AGG_SCORE < 0.7  -- threshold: 70% accuracy
  ))
  THEN
    CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
      SNOWFLAKE.NOTIFICATION.TEXT_PLAIN(
        'Agent evaluation accuracy dropped below 70% threshold.'
      ),
      '{"my_email_int": {"toAddress": ["admin@example.com"]}}'
    );
```

**Agent latency threshold alert**

```sql
CREATE OR REPLACE ALERT agent_latency_alert
  WAREHOUSE = my_warehouse
  SCHEDULE = '1 HOUR'
  IF (EXISTS (
    SELECT *
    FROM my_db.my_schema.my_event_table
    WHERE TIMESTAMP > DATEADD('HOUR', -1, CURRENT_TIMESTAMP())
      AND RESOURCE_ATTRIBUTES['snow.executable.type'] = 'AGENT'
      AND RECORD_TYPE = 'SPAN'
      AND RECORD['status']['code'] = 'STATUS_CODE_OK'
      AND TIMESTAMPDIFF('MILLISECOND',
            TIMESTAMP,
            RECORD['end_time']::TIMESTAMP_NTZ
          ) > 5000  -- latency threshold: 5000ms (5 seconds)
  ))
  THEN
    CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
      SNOWFLAKE.NOTIFICATION.TEXT_PLAIN(
        'Agent latency exceeded 5s threshold in the last hour.'
      ),
      '{"my_email_int": {"toAddress": ["admin@example.com"]}}'
    );
```

**Agent reliability threshold alert**

```sql
CREATE OR REPLACE ALERT agent_reliability_alert
  WAREHOUSE = my_warehouse
  SCHEDULE = '1 HOUR'
  IF (EXISTS (
    SELECT *
    FROM (
      SELECT
        COUNT_IF(RECORD['status']['code'] = 'STATUS_CODE_ERROR') AS error_count,
        COUNT(*) AS total_count,
        ROUND(1 - (error_count / NULLIF(total_count, 0)), 4) AS reliability_score
      FROM my_db.my_schema.my_event_table
      WHERE TIMESTAMP > DATEADD('HOUR', -1, CURRENT_TIMESTAMP())
        AND RESOURCE_ATTRIBUTES['snow.executable.type'] = 'AGENT'
        AND RECORD_TYPE = 'SPAN'
    )
    WHERE reliability_score < 0.95  -- threshold: 95% reliability
  ))
  THEN
    CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
      SNOWFLAKE.NOTIFICATION.TEXT_PLAIN(
        'Agent reliability dropped below 95% threshold in the last hour.'
      ),
      '{"my_email_int": {"toAddress": ["admin@example.com"]}}'
    );
```

**User feedback threshold alert**

```sql
CREATE OR REPLACE ALERT agent_user_feedback_alert
  WAREHOUSE = my_warehouse
  SCHEDULE = '1 HOUR'
  IF (EXISTS (
    SELECT *
    FROM (
      SELECT
        COUNT_IF(FEEDBACK = 'negative') AS negative_count,
        COUNT_IF(FEEDBACK = 'positive') AS positive_count,
        COUNT(*) AS total_count,
        ROUND(positive_count / NULLIF(total_count, 0), 4) AS satisfaction_score
      FROM my_db.my_schema.my_event_table
      WHERE TIMESTAMP > DATEADD('HOUR', -24, CURRENT_TIMESTAMP())
        AND RESOURCE_ATTRIBUTES['snow.executable.type'] = 'AGENT'
        AND RECORD_TYPE = 'SPAN'
        AND RECORD['name'] = 'user_feedback'
    )
    WHERE satisfaction_score < 0.80  -- threshold: 80% positive feedback
      AND total_count >= 5           -- minimum sample size to avoid false alarms
  ))
  THEN
    CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
      SNOWFLAKE.NOTIFICATION.TEXT_PLAIN(
        'Agent user satisfaction dropped below 80% in the last 24 hours.'
      ),
      '{"my_email_int": {"toAddress": ["admin@example.com"]}}'
    );
```

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You now have a comprehensive understanding of how to evaluate, version, deploy, and monitor Cortex Agents in production.

### What you learned
- How to build representative evaluation datasets from real user interactions
- How to choose and create evaluation metrics (built-in and custom)
- How to iterate on agents using versioning and evaluation results
- How to set up CI/CD pipelines with automated quality gates
- How to deploy agents safely using versioning and aliases
- How to monitor agents in production with observability and alerts

### Key takeaways
1. Start with real user queries for your evaluation dataset — synthetic data is a fallback, not a default
2. Use `ALTER AGENT` and versioning instead of `CREATE OR REPLACE AGENT` to preserve evaluation history
3. Make one change at a time and evaluate after each change to isolate impact
4. Combine CI/CD evaluations with scheduled cadence-based testing for comprehensive coverage
5. Pin your orchestration LLM to ensure reproducible results
6. Set up production alerts for evaluation accuracy, latency, reliability, and user feedback to catch issues before users do

### Related resources
- [Best Practices for Building Cortex Agents](https://quickstarts.snowflake.com/guide/best-practices-to-building-cortex-agents)
- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Snowflake Intelligence](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence/getting-started)

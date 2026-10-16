author: Andrew Shih
id: evaluate-and-optimize-ai-functions
language: en
summary: Evaluate AI-generated sentiment labels, compare models, and optimize a custom AI function in Snowflake.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# Evaluate and Optimize AI Functions in Snowflake

## Overview

Evaluate an AI call against labeled support tickets, compare models, then wrap the prompt in a
custom AI function and optimize its quality/cost tradeoff. This guide uses
[AI_FUNCTION_EVALUATION](https://docs.snowflake.com/en/sql-reference/functions/ai_function_evaluation)
and [AI_FUNCTION_OPTIMIZATION](https://docs.snowflake.com/en/sql-reference/functions/ai_function_optimization)
experiments. You choose whether to promote an optimized implementation; optimization does not
change your original function automatically.

### Prerequisites

- Familiarity with SQL and running SQL in Snowflake.
- An existing database and a dedicated tutorial schema, with `USAGE` on both.
- `CREATE TABLE`, `CREATE STAGE`, `CREATE FILE FORMAT`, `CREATE DATASET`, `CREATE FUNCTION`,
  and `CREATE EXPERIMENT` privileges on that schema.
- Access to Cortex AI functions, for example through the `SNOWFLAKE.CORTEX_USER` or
  `SNOWFLAKE.AI_FUNCTIONS_USER` database role. See
  [AI function access requirements](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-privileges-and-access).
- Access to a running warehouse for loading data and standalone SQL queries.
- Access to `claude-sonnet-4-5` and `claude-haiku-4-5`. Candidate and reflection models must
  also be authorized for optimization in your account and region. See
  [model availability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-regional-availability).

> Evaluation and optimization run asynchronously on serverless compute, billed as
> `SERVERLESS_EXPERIMENTS`, plus Cortex inference tokens. Loading and standalone queries use
> your selected warehouse; direct AI function calls also incur inference charges. Optimization
> applies its budget to each candidate model, so adding models increases work and cost.
> This guide starts with 50 rows and an `ultra-light` optimization budget. It does not guarantee
> an accuracy improvement or a particular cost reduction.

### What You'll Learn

- Prepare a versioned, labeled dataset for evaluation.
- Measure output quality across repeated runs and different models.
- Define and test a custom format-compliance metric.
- Compare optimized candidates by quality and relative cost, then promote a selected run.

### What You'll Need

- A Snowflake account with the prerequisites above. The optimization documentation currently
  lists public-preview rollout limitations; confirm availability before starting.
- A Snowsight SQL worksheet or Workspace SQL file. Snowflake CLI or SnowSQL is optional for
  uploading the CSV with `PUT`; do not run a local-file `PUT` in a Snowsight worksheet.
- [Download ticket_sentiment_eval.csv](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/evaluate-and-optimize-ai-functions/assets/ticket_sentiment_eval.csv).
  Save the linked content as `ticket_sentiment_eval.csv`.

The CSV has two columns, `TICKET_TEXT` and `EXPECTED_SENTIMENT`, with 16 negative, 18 neutral,
and 16 positive examples. The tickets and illustrative sentiment labels were AI-generated for
this tutorial, not sourced from customer records. They demonstrate the workflow; they are not
an independently annotated benchmark or evidence of production accuracy.

### What You'll Build

A reusable `classify_sentiment` AI function, a versioned dataset, baseline and comparison
evaluations, a custom scoring function, and a multi-model optimization experiment.

## Set Up Session

Replace every `MY_DB.MY_SCHEMA` in the SQL and YAML below with your existing tutorial database
and schema. Replace `MY_WAREHOUSE` with a warehouse you can use, and select your authorized role
in the SQL editor. Use ordinary, unquoted identifiers for these substitutions.

```sql
USE WAREHOUSE MY_WAREHOUSE;
USE SCHEMA MY_DB.MY_SCHEMA;
```

Use a dedicated schema with no existing objects bearing the names in this guide. Initial object
creation deliberately uses `CREATE`, not `CREATE OR REPLACE`, to avoid overwriting existing work.
If a name already exists, use another tutorial schema or deliberately clean up only objects you
created for this guide. The promotion step is the sole intentional function replacement.

Run the code blocks in order, but wait for each asynchronous experiment to finish before reading
its final results. A selected warehouse does not make experiment execution synchronous.

## Load Sample Data

Create a table, file format, and internal stage. The table stores labels in an object; the dataset
created in the next section exposes them as plain strings for evaluation.

```sql
CREATE TABLE ticket_sentiment_eval_data (
  ID          NUMBER AUTOINCREMENT START 1 INCREMENT 1 ORDER,
  TICKET_TEXT VARCHAR,
  EXPECTED    VARIANT
);

CREATE FILE FORMAT csv_quoted
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ENCODING = 'UTF8';

CREATE STAGE eval_stage FILE_FORMAT = csv_quoted;
```

Upload the downloaded CSV using **one** of these methods:

- In Snowsight, locate your tutorial schema's `EVAL_STAGE` in the database object browser and
  use its file-upload control to upload `ticket_sentiment_eval.csv`.
- In Snowflake CLI or SnowSQL, replace the local path and run:

```sql
PUT file:///path/to/ticket_sentiment_eval.csv @eval_stage AUTO_COMPRESS = TRUE;
```

Then run the following load in your SQL editor. The pattern accepts the uncompressed file or
its `.gz` form. The two CSV columns become `TICKET_TEXT` and an `EXPECTED` label object.

```sql
COPY INTO ticket_sentiment_eval_data (TICKET_TEXT, EXPECTED)
  FROM (
    SELECT $1, OBJECT_CONSTRUCT('SENTIMENT', $2)
    FROM @eval_stage
  )
  PATTERN = '.*ticket_sentiment_eval[.]csv([.]gz)?'
  FILE_FORMAT = (FORMAT_NAME = csv_quoted);

SELECT EXPECTED:SENTIMENT::VARCHAR AS sentiment, COUNT(*) AS ticket_count
FROM ticket_sentiment_eval_data
GROUP BY 1
ORDER BY 1;
```

Confirm **negative = 16, neutral = 18, positive = 16**, totaling 50 rows, before continuing.

## Create Labeled Dataset

Evaluation uses a versioned Snowflake dataset (`SNOWFLAKE.ML.DATASET`), not a plain table or
view. Map the object's `SENTIMENT` key to a lowercase string named `EXPECTED_SENTIMENT`.

```sql
CREATE DATASET ticket_sentiment_ds;
ALTER DATASET ticket_sentiment_ds ADD VERSION 'v1' FROM (
  SELECT TICKET_TEXT, LOWER(EXPECTED:SENTIMENT::STRING) AS EXPECTED_SENTIMENT
  FROM ticket_sentiment_eval_data
);
```

## Evaluate the Baseline

The prompt requests one lowercase label. `TRIM(LOWER(...))` normalizes the output before
`exact_match` compares it with the expected string. Three runs let you observe variation across
repeated evaluations; identical scores are also possible.

```sql
CREATE EXPERIMENT sentiment_eval_baseline
  TYPE = 'AI_FUNCTION_EVALUATION'
  FROM SPECIFICATION $$
query_text: "TRIM(LOWER(AI_COMPLETE('claude-sonnet-4-5',
  'Reply with exactly one lowercase word - positive, negative, or neutral - '
  || 'for the sentiment of this support ticket: ' || TICKET_TEXT)::VARCHAR))"
metrics:
  - name: exact_match
dataset:
  name: MY_DB.MY_SCHEMA.ticket_sentiment_ds
  version: v1
  ground_truth: EXPECTED_SENTIMENT
evaluation:
  num_eval_runs: 3
$$;

EXECUTE EXPERIMENT sentiment_eval_baseline;
```

`EXECUTE EXPERIMENT` returns immediately. Inspect the `metadata` JSON column for each run's
`RUNNING`, `FINISHED`, or `FAILED` status:

```sql
SHOW RUNS IN EXPERIMENT sentiment_eval_baseline;
```

Wait until all three runs are `FINISHED`. If a run is `FAILED`, inspect its reported error and
resolve the cause before continuing. Create a newly named experiment for another execution
rather than overwriting results you want to compare.

```sql
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_baseline RUN EVAL_1;
SHOW RUN PARAMETERS IN EXPERIMENT sentiment_eval_baseline RUN EVAL_1;
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_baseline RUN EVAL_2;
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_baseline RUN EVAL_3;
```

The `score` metric is between 0 and 1. Parameters include the model and number of rows evaluated.
Record the three scores to compare with the next experiment.

For a visual view, open **AI & ML > AI Functions** in Snowsight and find the evaluation listing.
Select `SENTIMENT_EVAL_BASELINE` to inspect its runs. Navigation labels can vary as the UI evolves;
the SQL statements above provide the results without depending on that navigation.

## Compare Two Models

Evaluate Haiku with the same prompt, normalization, dataset, metric, and number of runs. Only
the model and experiment name change. Do not replace the baseline experiment.

```sql
CREATE EXPERIMENT sentiment_eval_haiku
  TYPE = 'AI_FUNCTION_EVALUATION'
  FROM SPECIFICATION $$
query_text: "TRIM(LOWER(AI_COMPLETE('claude-haiku-4-5',
  'Reply with exactly one lowercase word - positive, negative, or neutral - '
  || 'for the sentiment of this support ticket: ' || TICKET_TEXT)::VARCHAR))"
metrics:
  - name: exact_match
dataset:
  name: MY_DB.MY_SCHEMA.ticket_sentiment_ds
  version: v1
  ground_truth: EXPECTED_SENTIMENT
evaluation:
  num_eval_runs: 3
$$;

EXECUTE EXPERIMENT sentiment_eval_haiku;
```

Poll status until all three runs are `FINISHED`, then read their scores:

```sql
SHOW RUNS IN EXPERIMENT sentiment_eval_haiku;
```

```sql
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_haiku RUN EVAL_1;
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_haiku RUN EVAL_2;
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_haiku RUN EVAL_3;
```

Compare the range of scores with the baseline. A small difference on this 50-row illustrative
dataset is not sufficient evidence that one model is universally better.

## Test Custom Scoring

A custom metric is a scalar UDF called as `custom_udf(EXPECTED, PREDICTED)`, with two VARCHAR
arguments: ground truth first, model output second. It returns an object with a numeric `score`
in 0-1 and optional `feedback`.

This metric measures **label correctness and strict output formatting**:

- `1.0`: the output exactly equals the expected lowercase label.
- `0.5`: the output is only that label, but differs in case, surrounding whitespace, or one
  trailing period.
- `0.0`: anything else, including explanations, negation, multiple labels, empty values, and nulls.

It intentionally does not interpret natural-language explanations. For example, when the expected
label is `negative`, `Negative.` earns 0.5, but `Negative. The customer is upset.` earns 0.
Returning all three labels cannot earn partial credit.

```sql
CREATE FUNCTION MY_DB.MY_SCHEMA.format_metric(EXPECTED VARCHAR, PREDICTED VARCHAR)
  RETURNS OBJECT
  AS $$
    OBJECT_CONSTRUCT(
      'score',
        CASE
          WHEN EXPECTED IS NULL OR PREDICTED IS NULL
            OR EXPECTED NOT IN ('positive', 'negative', 'neutral') THEN 0.0
          WHEN PREDICTED = EXPECTED THEN 1.0
          WHEN REGEXP_LIKE(LOWER(PREDICTED),
                 '[[:space:]]*' || EXPECTED || '[.]?[[:space:]]*') THEN 0.5
          ELSE 0.0
        END,
      'feedback', 'expected=' || COALESCE(EXPECTED, '<NULL>')
        || ' got=' || LEFT(COALESCE(PREDICTED, '<NULL>'), 100))
  $$;
```

Test the UDF before paying for an evaluation. Every row below should have `passed = TRUE`.

```sql
SELECT expected_label, predicted, expected_score,
       MY_DB.MY_SCHEMA.format_metric(expected_label, predicted):score::FLOAT AS actual_score,
       actual_score = expected_score AS passed
FROM VALUES
  ('negative', 'negative', 1.0),
  ('negative', 'Negative', 0.5),
  ('negative', ' negative ', 0.5),
  ('negative', 'Negative.', 0.5),
  ('negative', 'Negative. The customer is upset.', 0.0),
  ('negative', 'not negative; positive', 0.0),
  ('negative', 'positive negative neutral', 0.0),
  ('negative', 'not negative', 0.0),
  ('negative', 'negative..', 0.0),
  ('positive', 'negative', 0.0),
  ('positive', 'positively', 0.0),
  ('positive', '', 0.0),
  ('positive', NULL, 0.0),
  (NULL, 'positive', 0.0),
  ('unknown', 'unknown', 0.0)
  AS cases(expected_label, predicted, expected_score);
```

Evaluate raw model output without trimming or lowercasing it first, so the metric can observe
formatting differences. The explicit `evaluation` section requests one run.

```sql
CREATE EXPERIMENT sentiment_eval_format
  TYPE = 'AI_FUNCTION_EVALUATION'
  FROM SPECIFICATION $$
query_text: "AI_COMPLETE('claude-sonnet-4-5',
  'Reply with exactly one lowercase word - positive, negative, or neutral - '
  || 'for the sentiment of this support ticket: ' || TICKET_TEXT)::VARCHAR"
metrics:
  - name: custom
    custom_udf: MY_DB.MY_SCHEMA.format_metric
dataset:
  name: MY_DB.MY_SCHEMA.ticket_sentiment_ds
  version: v1
  ground_truth: EXPECTED_SENTIMENT
evaluation:
  num_eval_runs: 1
$$;

EXECUTE EXPERIMENT sentiment_eval_format;
```

Check for `FINISHED` before inspecting the score:

```sql
SHOW RUNS IN EXPERIMENT sentiment_eval_format;
```

```sql
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_format RUN EVAL_1;
```

This custom score has different semantics from the normalized exact-match baseline. Compare
implementations using the same metric; do not treat the two scores as interchangeable accuracies.

## Optimize the Function

Optimization searches for better implementations and model choices. For this guide, return to
`exact_match`, the metric used in the baseline and model comparison, rather than the custom metric.

### Create the Function

Wrap the baseline expression in a reusable AI function. When referencing a named function in an
optimization specification, it must be created with `CREATE AI FUNCTION`, not plain
`CREATE FUNCTION`. The optimization documentation requires exactly one `AI_COMPLETE` call.
The explicit VARCHAR cast makes the declared return type clear.

```sql
CREATE AI FUNCTION MY_DB.MY_SCHEMA.classify_sentiment(ticket VARCHAR)
  RETURNS VARCHAR
  AS $$
    TRIM(LOWER(AI_COMPLETE('claude-sonnet-4-5',
      'Reply with exactly one lowercase word - positive, negative, or neutral - '
      || 'for the sentiment of this support ticket: ' || ticket)::VARCHAR))
  $$;

SELECT TICKET_TEXT, MY_DB.MY_SCHEMA.classify_sentiment(TICKET_TEXT) AS predicted
FROM ticket_sentiment_eval_data
ORDER BY ID
LIMIT 5;
```

### Run the Optimization

Map the function argument `ticket` to the dataset column `TICKET_TEXT`. Unlike evaluation,
optimization places `ground_truth` under `dataset.column_mapping`.

```sql
CREATE EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt
  TYPE = 'AI_FUNCTION_OPTIMIZATION'
  FROM SPECIFICATION $$
function:
  function_name: "MY_DB.MY_SCHEMA.classify_sentiment(VARCHAR)"
metrics:
  - name: exact_match
dataset:
  name: MY_DB.MY_SCHEMA.ticket_sentiment_ds
  version: v1
  column_mapping:
    argument_mapping:
      ticket: TICKET_TEXT
    ground_truth: EXPECTED_SENTIMENT
optimization:
  models:
    - claude-sonnet-4-5
    - claude-haiku-4-5
  reflection_model: claude-sonnet-4-5
  strategy: balanced
  budget: ultra-light
$$;

EXECUTE EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt;
```

Both candidate models are optimized within this one experiment. The reflection model proposes
improvements. A model that is unavailable or unauthorized for optimization can fail the experiment.

### Inspect Completed Runs

```sql
SHOW RUNS IN EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt;
```

The experiment produces a `SEED` run for the original function and `ITER_<N>` candidate runs.
Wait for optimization to finish before selecting a winner; intermediate results may be incomplete.
Inspect the reported error if a run fails.

```sql
SHOW RUN METRICS IN EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt RUN SEED;

SHOW RUN METRICS IN EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt
  ->> SELECT "run_name", "value"
      FROM $1
      WHERE "name" = 'is_frontier' AND "value" = 1.0;
```

Use an actual completed candidate from these results. In the next two statements and the promotion
statement, replace `CHOSEN_RUN` with its exact run name. `CHOSEN_RUN` is a placeholder, not a run
created by the guide; do not assume a particular `ITER_<N>` exists or is on the frontier.

```sql
SHOW RUN METRICS IN EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt RUN CHOSEN_RUN;
SHOW RUN PARAMETERS IN EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt RUN CHOSEN_RUN;
```

| Field | Kind | Meaning |
|---|---|---|
| `val_score` | Metric | Quality on the validation split (0-1) |
| `test_score` | Metric | Quality on the held-out test split, reported for frontier runs |
| `cost_compared_to_seed` | Metric | Below 1 is cheaper than the seed; above 1 is pricier |
| `is_frontier` | Metric | 1 identifies a candidate on the quality/cost frontier |
| `run_type` | Parameter | `seed`, `accepted`, or `rejected` |
| `model` | Parameter | Candidate model |
| `function_impl` | Parameter | Candidate implementation |

Compare frontier candidates using `test_score` and `cost_compared_to_seed`, not validation score
alone. Prefer the original function if no candidate offers a useful tradeoff. An optimized
candidate is not guaranteed to outperform the seed on this small, simple dataset.

You can also inspect `SENTIMENT_OPT` in the Snowsight **AI Functions** optimization listing to
compare candidate quality and cost visually.

### Promote Your Selection

Only run this step if you want to adopt a completed candidate. After replacing `CHOSEN_RUN`, this
statement intentionally replaces the tutorial's original function in place. Its signature and
return type remain unchanged, so existing calls use the selected implementation. Do not run it
against a production function as part of this exercise.

```sql
CREATE OR REPLACE AI FUNCTION MY_DB.MY_SCHEMA.classify_sentiment(ticket VARCHAR)
  RETURNS VARCHAR
  FROM EXPERIMENT MY_DB.MY_SCHEMA.sentiment_opt RUN CHOSEN_RUN;

SELECT TICKET_TEXT, MY_DB.MY_SCHEMA.classify_sentiment(TICKET_TEXT) AS predicted
FROM ticket_sentiment_eval_data
ORDER BY ID
LIMIT 5;
```

## Check After Promotion

Create a separate evaluation so the original baseline remains available. This is a **regression
check on reused data**, not independent validation: optimization has already used this dataset.
For an independent assessment, collect separately labeled examples that were not used for tuning
or selecting the winner, and evaluate on a new dataset.

```sql
CREATE EXPERIMENT sentiment_eval_promoted
  TYPE = 'AI_FUNCTION_EVALUATION'
  FROM SPECIFICATION $$
query_text: "MY_DB.MY_SCHEMA.classify_sentiment(TICKET_TEXT)"
metrics:
  - name: exact_match
dataset:
  name: MY_DB.MY_SCHEMA.ticket_sentiment_ds
  version: v1
  ground_truth: EXPECTED_SENTIMENT
evaluation:
  num_eval_runs: 3
$$;

EXECUTE EXPERIMENT sentiment_eval_promoted;
```

Wait for the three runs to finish before comparing their scores with the saved baseline:

```sql
SHOW RUNS IN EXPERIMENT sentiment_eval_promoted;
```

```sql
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_promoted RUN EVAL_1;
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_promoted RUN EVAL_2;
SHOW RUN METRICS IN EXPERIMENT sentiment_eval_promoted RUN EVAL_3;
```

## Clean Up

Wait for all experiments to stop running. Save any results you want to keep before dropping the
objects. Run this only in the dedicated tutorial schema; it removes the uploaded stage file too.
The warehouse, database, and schema are not dropped because they existed before the tutorial.

```sql
USE SCHEMA MY_DB.MY_SCHEMA;

DROP EXPERIMENT IF EXISTS sentiment_eval_baseline;
DROP EXPERIMENT IF EXISTS sentiment_eval_haiku;
DROP EXPERIMENT IF EXISTS sentiment_eval_format;
DROP EXPERIMENT IF EXISTS sentiment_opt;
DROP EXPERIMENT IF EXISTS sentiment_eval_promoted;
DROP FUNCTION IF EXISTS classify_sentiment(VARCHAR);
DROP FUNCTION IF EXISTS format_metric(VARCHAR, VARCHAR);
DROP DATASET IF EXISTS ticket_sentiment_ds;
DROP TABLE IF EXISTS ticket_sentiment_eval_data;
DROP STAGE IF EXISTS eval_stage;
DROP FILE FORMAT IF EXISTS csv_quoted;
```

## Conclusion and Resources

### What You Learned

You loaded a synthetic labeled dataset, evaluated an AI call repeatedly, compared two models,
implemented a custom metric, and explored automated optimization of a reusable AI function.
You also learned to select a quality/cost tradeoff explicitly and distinguish a regression check
from independent validation.

### Continue with Cortex Code

[Cortex AI Function Studio](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-function-studio)
is a Cortex Code skill for the create, evaluate, and optimize workflow. This guide performs the
steps explicitly in SQL; Cortex Code is not required to complete it. With Cortex Code available,
you can ask it to help create a custom AI function, evaluate an existing function, or optimize
an implementation against labeled data.

For a production use case, start by defining your label policy and assembling a representative,
independently reviewed dataset with separate examples reserved for final evaluation.

### Related Resources

- [Evaluate an AI function](https://docs.snowflake.com/en/sql-reference/functions/ai_function_evaluation)
- [Optimize an AI function](https://docs.snowflake.com/en/sql-reference/functions/ai_function_optimization)
- [CREATE AI FUNCTION](https://docs.snowflake.com/en/sql-reference/sql/create-ai-function)
- [Experiment SQL commands](https://docs.snowflake.com/en/sql-reference/sql/experiment)
- [AI function access requirements](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql-privileges-and-access)

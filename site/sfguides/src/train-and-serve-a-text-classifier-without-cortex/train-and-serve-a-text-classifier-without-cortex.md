author: Yusuf Budunoğlu
id: train-and-serve-a-text-classifier-without-cortex
language: en
summary: Train a scikit-learn text classifier inside Snowflake, serve it as a SQL function, and route only the hard reviews to an LLM. Works on a trial account, no Cortex needed.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/community-sourced, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/snowpark
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/yusuf-budunoglu/review-routing

# Train and Serve a Text Classifier in Snowflake Without Cortex
<!-- ------------------------ -->
## Overview

Cortex AI functions such as `AI_SENTIMENT` or `AI_CLASSIFY` are the fastest way to label text in Snowflake, but they are not available on trial accounts. This guide shows a path that works everywhere: you train your own model inside Snowflake with a Python stored procedure, save it to a stage, and serve it as a SQL function that any query can call.

Then you go one step further. A small model is cheap but less accurate than a large language model (LLM). You will measure, in SQL, how many reviews the small model can answer on its own when it is confident, and how much money that saves compared to sending every review to an LLM.

The data is 11,149 Polish product reviews from [Allegro](https://allegro.pl) (the Allegro Reviews dataset from the [KLEJ benchmark](https://klejbenchmark.com), CC BY-SA 4.0). Each review has a 1–5 star rating, which we turn into three labels: negative (1–2 stars), neutral (3) and positive (4–5). Polish is a good test: it is highly inflected, and general-purpose models often do worse on it than on English.

### Prerequisites
- Basic SQL
- Basic Python (the training code is short and commented)

### What You'll Learn
- How to train a scikit-learn model inside a Python stored procedure
- How to save a fitted model to a stage and serve it as a Python UDF
- How to label thousands of rows with one SQL query through that UDF
- How to compute macro-F1 and a cost/quality routing curve in plain SQL
- Which trial-account limits you will hit and how to work around them

### What You'll Need
- A Snowflake account. A free [trial account](https://signup.snowflake.com/) is enough.
- The two data files from the [companion repository](https://github.com/yusuf-budunoglu/review-routing/tree/main/guide/data):
  - `reviews_pl.jsonl` (6.7 MB): the reviews with their split and label
  - `claude_predictions_pl.jsonl` (0.1 MB): labels and real per-review API costs from three Claude models on a balanced 300-review sample

### What You'll Build
- A `PREDICT_REVIEW_PROBA(text)` SQL function backed by a model you trained in Snowflake
- A table with a prediction for every review
- A routing curve that shows, for each confidence threshold, how many reviews still go to the LLM, the resulting quality and the cost per 1,000 reviews

<!-- ------------------------ -->
## Set Up the Environment

Open a SQL worksheet in Snowsight (**Projects > Workspaces**, or **Worksheets** on older accounts) and run:

```sql
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS REVIEW_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

CREATE DATABASE IF NOT EXISTS REVIEW_INTEL;
CREATE SCHEMA IF NOT EXISTS REVIEW_INTEL.EVAL;

USE WAREHOUSE REVIEW_WH;
USE SCHEMA REVIEW_INTEL.EVAL;

CREATE OR REPLACE FILE FORMAT JSONL_FORMAT TYPE = 'JSON';
CREATE OR REPLACE STAGE REVIEW_FILES
  FILE_FORMAT = JSONL_FORMAT
  DIRECTORY = (ENABLE = TRUE);

CREATE STAGE IF NOT EXISTS MODEL_FILES;
```

`REVIEW_FILES` holds the input data. `MODEL_FILES` will hold the trained model.

Before you continue, check that Python stored procedures and the packages we need are available on your account:

```sql
CREATE OR REPLACE PROCEDURE CHECK_PYTHON()
  RETURNS STRING
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('snowflake-snowpark-python', 'scikit-learn', 'numpy')
  HANDLER = 'run'
AS $$
import numpy, sklearn
def run(session):
    return f"python ok | numpy {numpy.__version__} | sklearn {sklearn.__version__}"
$$;

CALL CHECK_PYTHON();
```

You should see something like `python ok | numpy 2.x | sklearn 1.x`.

<!-- ------------------------ -->
## Load the Data

Download `reviews_pl.jsonl` and `claude_predictions_pl.jsonl` from the [companion repository](https://github.com/yusuf-budunoglu/review-routing/tree/main/guide/data).

Upload both to the stage in Snowsight: **Catalog > Database Explorer > REVIEW_INTEL > EVAL > Stages > REVIEW_FILES**, then **+ Files**. Run `LIST @REVIEW_FILES;` and you should see both files.

Now load them into tables:

```sql
CREATE OR REPLACE TABLE REVIEWS_ALL (
  ID     STRING,
  SPLIT  STRING,      -- train / valid / test (the dataset's own split)
  TEXT   STRING,
  STARS  NUMBER(1),
  LABEL  STRING       -- negative (1-2 stars) / neutral (3) / positive (4-5)
);

COPY INTO REVIEWS_ALL (ID, SPLIT, TEXT, STARS, LABEL)
FROM (
  SELECT $1:id::STRING, $1:split::STRING, $1:text::STRING, $1:stars::NUMBER, $1:label::STRING
  FROM @REVIEW_FILES
)
FILES = ('reviews_pl.jsonl');

-- One row per review per Claude model, with the real cost and latency of that API call.
CREATE OR REPLACE TABLE CLAUDE_PREDICTIONS (
  ID              STRING,
  MODEL           STRING,
  PRED            STRING,
  COST_USD        FLOAT,
  LATENCY_S       FLOAT,
  IN_EVAL_SAMPLE  BOOLEAN
);

COPY INTO CLAUDE_PREDICTIONS (ID, MODEL, PRED, COST_USD, LATENCY_S, IN_EVAL_SAMPLE)
FROM (
  SELECT $1:id::STRING, $1:model::STRING, $1:pred::STRING, $1:cost_usd::FLOAT,
         $1:latency_s::FLOAT, $1:in_eval_sample::BOOLEAN
  FROM @REVIEW_FILES
)
FILES = ('claude_predictions_pl.jsonl');

SELECT 'reviews: ' || SPLIT AS WHAT, COUNT(*) AS N FROM REVIEWS_ALL GROUP BY SPLIT
UNION ALL
SELECT 'claude: ' || MODEL, COUNT(*) FROM CLAUDE_PREDICTIONS GROUP BY MODEL
ORDER BY WHAT;
```

Expected counts: train 9,180, valid 977, test 992, and 300 rows for each of the three Claude models.

> aside positive
> The Claude predictions were produced outside Snowflake with the Anthropic API, using a short prompt that asks for one of the three labels. The script is in the companion repository (`src/llm_eval.py`) if you want to regenerate them with other models. You do not need an API key to follow this guide.

<!-- ------------------------ -->
## Train the Model in Snowflake

The model is a classic, strong baseline for text: TF-IDF features fed into logistic regression. It uses two kinds of features:

- **Word unigrams and bigrams**, such as `szybka wysyłka` ("fast shipping").
- **Character 2–5 grams**. Polish changes word endings a lot (`polecam`, `polecamy`, `polecany`). Character n-grams let the model treat these forms as related even when it never saw a particular form during training.

The stored procedure below does everything in one call:

1. Reads the reviews into pandas.
2. Tries five regularization strengths (`C`) and keeps the one with the best macro-F1 on the validation split.
3. Retrains on train + validation and scores the test split once.
4. Saves the model with joblib, uploads it to `@MODEL_FILES`, and creates the `PREDICT_REVIEW_PROBA` SQL function from it.
5. Labels every review through that function and writes the results to a table.

```sql
CREATE OR REPLACE PROCEDURE TRAIN_REVIEW_MODEL()
  RETURNS VARIANT
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('snowflake-snowpark-python', 'scikit-learn', 'pandas', 'pyarrow', 'numpy', 'joblib')
  HANDLER = 'run'
  EXECUTE AS CALLER
AS $$
import os
import tempfile
import time

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

MODEL_FILE = "review_sentiment.joblib"
# The UDF body below needs a double-dollar delimiter. It is built from two pieces so
# the SQL parser does not read it as the end of this procedure's own body.
DQ = "$" + "$"


def build(c):
    features = ColumnTransformer([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                 max_features=200_000), "TEXT"),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3,
                                 sublinear_tf=True, max_features=300_000), "TEXT"),
    ])
    clf = LogisticRegression(C=c, max_iter=3000, class_weight="balanced")
    return Pipeline([("features", features), ("clf", clf)])


def run(session):
    df = session.table("REVIEWS_ALL").select("ID", "SPLIT", "TEXT", "LABEL").to_pandas()
    train, valid, test = (df[df.SPLIT == s] for s in ("train", "valid", "test"))

    # Pick the regularization strength on the validation split.
    search = {}
    for c in (0.5, 1.0, 2.0, 4.0, 8.0):
        model = build(c).fit(train[["TEXT"]], train.LABEL)
        search[c] = f1_score(valid.LABEL, model.predict(valid[["TEXT"]]), average="macro")
    best_c = max(search, key=search.get)

    # Final model on train + valid, scored once on test.
    fit_df = pd.concat([train, valid])
    model = build(best_c).fit(fit_df[["TEXT"]], fit_df.LABEL)
    test_pred = model.predict(test[["TEXT"]])
    result = {
        "best_C": best_c,
        "valid_macro_f1_by_C": {str(k): round(v, 4) for k, v in search.items()},
        "test_accuracy": round(accuracy_score(test.LABEL, test_pred), 4),
        "test_macro_f1": round(f1_score(test.LABEL, test_pred, average="macro"), 4),
        "classes": list(model.classes_),
        "sklearn_version": sklearn.__version__,
    }

    # TfidfVectorizer keeps every pruned n-gram in stop_words_ (millions of character
    # n-grams here). It is not used for prediction, and dropping it keeps the file small.
    for _, vectorizer, _ in model.named_steps["features"].transformers_:
        if hasattr(vectorizer, "stop_words_"):
            delattr(vectorizer, "stop_words_")

    # Save the model to a stage.
    path = os.path.join(tempfile.gettempdir(), MODEL_FILE)
    joblib.dump(model, path)
    result["model_file_mb"] = round(os.path.getsize(path) / 1e6, 1)
    session.file.put(path, "@MODEL_FILES", auto_compress=False, overwrite=True)

    # Serve it as a SQL function. The model is loaded once per Python process.
    udf_sql = """
CREATE OR REPLACE FUNCTION PREDICT_REVIEW_PROBA(TEXT STRING)
  RETURNS ARRAY
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('{SKLEARN}', 'pandas', 'joblib')
  IMPORTS = ('@MODEL_FILES/{MODEL_FILE}')
  HANDLER = 'predict'
  COMMENT = 'Probabilities for [negative, neutral, positive]'
AS {DQ}
import os
import sys

import joblib
import pandas as pd

_model = joblib.load(os.path.join(sys._xoptions["snowflake_import_directory"], "{MODEL_FILE}"))

def predict(text):
    proba = _model.predict_proba(pd.DataFrame({{"TEXT": [text or ""]}}))[0]
    return [float(p) for p in proba]
{DQ}
"""
    # Pin the sklearn version used for training (pickled models are version-sensitive).
    try:
        session.sql(udf_sql.format(SKLEARN=f"scikit-learn=={sklearn.__version__}",
                                   MODEL_FILE=MODEL_FILE, DQ=DQ)).collect()
        result["serving_sklearn"] = f"pinned {sklearn.__version__}"
    except Exception:
        session.sql(udf_sql.format(SKLEARN="scikit-learn", MODEL_FILE=MODEL_FILE, DQ=DQ)).collect()
        result["serving_sklearn"] = "unpinned (pin was not available)"

    # Label every review with one SQL query through the served function.
    t0 = time.time()
    session.sql("""
CREATE OR REPLACE TABLE SNOWFLAKE_MODEL_PREDICTIONS AS
SELECT ID, P[0]::FLOAT AS P_NEGATIVE, P[1]::FLOAT AS P_NEUTRAL, P[2]::FLOAT AS P_POSITIVE
FROM (SELECT ID, PREDICT_REVIEW_PROBA(TEXT) AS P FROM REVIEWS_ALL)
""").collect()
    result["inference_rows"] = session.table("SNOWFLAKE_MODEL_PREDICTIONS").count()
    result["inference_seconds"] = round(time.time() - t0, 1)
    return result
$$;

CALL TRAIN_REVIEW_MODEL();
```

On an XSMALL warehouse this takes a few minutes. The result is a JSON object with the chosen `C`, the test scores, the model file size and the number of labelled rows (11,149).

Now call your model from plain SQL:

```sql
SELECT PREDICT_REVIEW_PROBA('Produkt zgodny z opisem, szybka wysyłka, polecam!') AS P_NEG_NEU_POS;
```

The answer is three probabilities in the order negative, neutral, positive. "Product as described, fast shipping, I recommend it!" should come out strongly positive.

> aside positive
> **Why `classes_` matters.** scikit-learn sorts class labels alphabetically, so the order is `negative, neutral, positive`. The procedure returns `classes` in its result so you can confirm the order the SQL code below relies on.

<!-- ------------------------ -->
## Measure the Model in SQL

First, a view that turns the three probabilities into a label and a confidence (the highest probability):

```sql
CREATE OR REPLACE VIEW SF_MODEL AS
SELECT ID, P_NEGATIVE, P_NEUTRAL, P_POSITIVE,
       GREATEST(P_NEGATIVE, P_NEUTRAL, P_POSITIVE) AS CONFIDENCE,
       CASE GREATEST(P_NEGATIVE, P_NEUTRAL, P_POSITIVE)
            WHEN P_NEGATIVE THEN 'negative'
            WHEN P_NEUTRAL  THEN 'neutral'
            ELSE 'positive' END AS PRED
FROM SNOWFLAKE_MODEL_PREDICTIONS;
```

Accuracy alone is misleading here: most reviews are positive, so a model that always says "positive" already scores well. We use **macro-F1**, the average of the F1 score of each class, so the rare neutral class counts as much as the others. For one class, F1 = 2·TP / (2·TP + FP + FN).

```sql
WITH scored AS (
  SELECT r.LABEL, m.PRED
  FROM REVIEWS_ALL r JOIN SF_MODEL m USING (ID)
  WHERE r.SPLIT = 'test'
),
per_class AS (
  SELECT cls.L,
         SUM(IFF(PRED = cls.L AND LABEL = cls.L, 1, 0))  AS TP,
         SUM(IFF(PRED = cls.L AND LABEL <> cls.L, 1, 0)) AS FP,
         SUM(IFF(PRED <> cls.L AND LABEL = cls.L, 1, 0)) AS FN
  FROM scored
  CROSS JOIN (SELECT COLUMN1 AS L FROM VALUES ('negative'), ('neutral'), ('positive')) cls
  GROUP BY cls.L
)
SELECT ROUND(AVG(2 * TP / NULLIF(2 * TP + FP + FN, 0)), 3) AS MACRO_F1,
       (SELECT ROUND(AVG(IFF(PRED = LABEL, 1, 0)), 3) FROM scored) AS ACCURACY
FROM per_class;
```

In our run the test split gave accuracy 0.737 and macro-F1 0.643.

<!-- ------------------------ -->
## Route Hard Reviews

The idea: the model is confident about most reviews ("polecam!" is easy), and those it can answer on its own for free. Only reviews where its top probability is below a threshold T go to the LLM. The question is which T keeps quality close to "LLM for everything" while saving the most money.

`CLAUDE_PREDICTIONS` contains the label and the real cost of each API call for three Claude models on a balanced sample of 300 reviews (100 per class). The query below tries 34 thresholds from 0.34 to 1.00. At T = 1.00 every review goes to the LLM.

```sql
CREATE OR REPLACE TABLE ROUTER_CURVE AS
WITH thresholds AS (
  SELECT ROUND(0.34 + 0.02 * SEQ4(), 2) AS T FROM TABLE(GENERATOR(ROWCOUNT => 34))
),
joined AS (
  SELECT c.MODEL, r.ID, r.LABEL, m.PRED AS SF_PRED, m.CONFIDENCE, c.PRED AS LLM_PRED, c.COST_USD
  FROM CLAUDE_PREDICTIONS c
  JOIN SF_MODEL m USING (ID)
  JOIN REVIEWS_ALL r USING (ID)
  WHERE c.IN_EVAL_SAMPLE
),
routed AS (
  SELECT t.T, j.MODEL, j.LABEL,
         j.CONFIDENCE < t.T AS TO_LLM,
         IFF(j.CONFIDENCE < t.T, j.LLM_PRED, j.SF_PRED) AS FINAL_PRED,
         IFF(j.CONFIDENCE < t.T, j.COST_USD, 0) AS COST_USD
  FROM thresholds t CROSS JOIN joined j
),
per_class AS (
  SELECT T, MODEL, cls.L AS CLASS,
         SUM(IFF(FINAL_PRED = cls.L AND LABEL = cls.L, 1, 0)) AS TP,
         SUM(IFF(FINAL_PRED = cls.L AND LABEL <> cls.L, 1, 0)) AS FP,
         SUM(IFF(FINAL_PRED IS DISTINCT FROM cls.L AND LABEL = cls.L, 1, 0)) AS FN
  FROM routed
  CROSS JOIN (SELECT COLUMN1 AS L FROM VALUES ('negative'), ('neutral'), ('positive')) cls
  GROUP BY T, MODEL, cls.L
)
SELECT r.T, r.MODEL,
       ROUND(AVG(IFF(r.TO_LLM, 1, 0)), 3)               AS SHARE_TO_LLM,
       ROUND(AVG(IFF(r.FINAL_PRED = r.LABEL, 1, 0)), 3) AS ACCURACY,
       ROUND(f.MACRO_F1, 3)                             AS MACRO_F1,
       ROUND(1000 * SUM(r.COST_USD) / COUNT(*), 4)      AS COST_PER_1K_USD
FROM routed r
JOIN (SELECT T, MODEL, AVG(2 * TP / NULLIF(2 * TP + FP + FN, 0)) AS MACRO_F1
      FROM per_class GROUP BY T, MODEL) f
  ON f.T = r.T AND f.MODEL = r.MODEL
GROUP BY r.T, r.MODEL, f.MACRO_F1;
```

Now pick, for each LLM, the cheapest threshold whose macro-F1 is within one point (0.01) of sending everything to that LLM:

```sql
WITH full_llm AS (
  SELECT MODEL, MACRO_F1 AS FULL_F1, COST_PER_1K_USD AS FULL_COST
  FROM ROUTER_CURVE WHERE T = 1.00
),
best AS (
  SELECT c.*, f.FULL_F1, f.FULL_COST,
         ROW_NUMBER() OVER (PARTITION BY c.MODEL ORDER BY c.COST_PER_1K_USD, c.T) AS RN
  FROM ROUTER_CURVE c JOIN full_llm f USING (MODEL)
  WHERE c.MACRO_F1 >= f.FULL_F1 - 0.01
)
SELECT MODEL, T, SHARE_TO_LLM,
       MACRO_F1, FULL_F1 AS ALL_LLM_MACRO_F1,
       COST_PER_1K_USD, FULL_COST AS ALL_LLM_COST_PER_1K_USD,
       ROUND(100 * (1 - COST_PER_1K_USD / NULLIF(FULL_COST, 0))) AS PCT_CHEAPER
FROM best WHERE RN = 1
ORDER BY MODEL;
```

Our results on the 300-review sample:

| LLM | T | Sent to LLM | Macro-F1 (router vs all-LLM) | Cost per 1k reviews (router vs all-LLM) | Saving |
|---|---|---|---|---|---|
| claude-haiku-4-5 | 0.58 | 53% | 0.728 vs 0.729 | $0.264 vs $0.492 | 46% |
| claude-haiku-5-5 | 0.54 | 43% | 0.681 vs 0.675 | $0.029 vs $0.066 | 56% |
| claude-sonnet-5-5 | 0.70 | 74% | 0.771 vs 0.780 | $0.978 vs $1.312 | 25% |

With the cheapest LLM, more than half of the reviews never leave Snowflake, and quality is unchanged. With the strongest LLM the saving is smaller: its labels are better than the small model's on more reviews, so more of them have to go to it.

> aside negative
> The 300-review sample is small. A difference of 0.01 macro-F1 is within noise, so treat the "within one point" rule as a practical choice, not a precise one. In production, choose T on one sample and confirm it on another.

<!-- ------------------------ -->
## Trial Account Notes

These are the walls we hit while building this on a trial account, and what worked instead.

- **Cortex AI functions are unavailable.** `AI_SENTIMENT`, `AI_CLASSIFY`, `AI_COMPLETE`, `AI_TRANSLATE` and `AI_EMBED` return "not available for trial accounts". That is why this guide trains its own model.
- **Model Registry may fail.** `Registry.log_model` returned "Cannot create a Python function with the specified packages" for this pipeline. Saving with joblib to a stage and creating the UDF yourself, as above, works.
- **`to_pandas()` needs `pyarrow`.** Listing `pandas` in `PACKAGES` is not enough: without `pyarrow` the procedure fails with "Optional dependency: 'pandas' is not installed". Add `pyarrow` explicitly, as above.
- **Only plain `$$` works as a body delimiter.** Tagged forms like `$udf$` are a syntax error. To create a UDF from inside a procedure whose body is already in `$$`, build the delimiter as `"$" + "$"` in Python, and do not write a literal `$$` anywhere in the procedure body, not even in a comment.
- **Session variables are limited to 256 bytes**, so long text cannot be passed through `SET`. Use tables or inline literals.
- **Snowsight "Run All" shows only the last result.** If you run a whole worksheet at once, put the numbers you want to see into the final query.

<!-- ------------------------ -->
## Clean Up

```sql
DROP DATABASE IF EXISTS REVIEW_INTEL;
DROP WAREHOUSE IF EXISTS REVIEW_WH;
```

<!-- ------------------------ -->
## Conclusion and Resources

You trained a text classifier inside Snowflake, served it as a SQL function, labelled 11,149 reviews with one query, and measured in SQL how much an LLM bill shrinks when a cheap model handles the reviews it is sure about. None of it needed Cortex, so it runs on a trial account.

### What You Learned
- Training scikit-learn models in a Python stored procedure
- Serving a staged model file through a Python UDF
- Computing macro-F1 and a routing curve in SQL
- Working around trial-account limits

### Related Resources
- [Companion repository](https://github.com/yusuf-budunoglu/review-routing): the full project, with a from-scratch NumPy baseline, the Claude evaluation script and charts
- [Python UDFs](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-introduction)
- [Python stored procedures](https://docs.snowflake.com/en/developer-guide/stored-procedure/python/procedure-python-overview)
- [Allegro Reviews / KLEJ benchmark](https://klejbenchmark.com)

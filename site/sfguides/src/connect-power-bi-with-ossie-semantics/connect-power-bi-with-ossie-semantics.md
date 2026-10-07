author: Eric Tolotti
id: connect-power-bi-with-ossie-semantics
summary: Use Apache Ossie to convert semantic models between Snowflake and Power BI, enabling a bi-directional semantic pipeline with git as the source of truth
title: Connect Power BI with OSSIE Semantics
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Connect Power BI with OSSIE Semantics

<!-- ------------------------ -->
## Overview

Duration: 5

Semantic model definitions fragment across tools. Revenue gets defined one way in Snowflake, another in Power BI, and a third in a notebook. Apache Ossie (incubating) is a vendor-neutral YAML standard that solves this: define your metrics, dimensions, and joins once, then convert to platform-specific formats using built-in Snowflake functions and open-source CLI converters.

This quickstart walks through the full round-trip: starting with a TPCDS semantic model in Snowflake, exporting it to Apache Ossie format, converting it to a Power BI semantic model, making a change in DAX, and pushing that change back through Ossie to Snowflake. The final section establishes the best practice: store the Ossie YAML in git as the single source of truth.

The flow looks like this:

```
              ┌──────────────────────────┐
              │   Git Repository         │
              │   (Ossie YAML =          │
              │    source of truth)      │
              └────┬──────────┬──────────┘
                   │          │
  CALL SYSTEM$     │          │ ossie-microsoft
  CREATE_SEMANTIC_ │          │ export
  VIEW_FROM_OSSIE  │          │
                   ▼          ▼
          ┌──────────┐  ┌──────────┐
          │ Snowflake│  │ Power BI │
          │ Semantic │  │ model.bim│
          │ View     │  │          │
          └────┬─────┘  └────┬─────┘
               │              │
  SELECT       │              │ ossie-microsoft
  SYSTEM$READ_ │              │ import
  OSSIE_YAML   │              │
               └──────┬───────┘
                      ▼
              ┌──────────────────────────┐
              │   Commit updated Ossie   │
              │   YAML back to git       │
              └──────────────────────────┘
```


### Prerequisites
- Familiarity with [Snowflake](https://docs.snowflake.com/) and semantic views
- Familiarity with [Power BI](https://learn.microsoft.com/en-us/power-bi/) semantic models
- Basic command-line comfort

### What You Will Learn
- How Apache Ossie serves as a vendor-neutral hub for semantic model interchange
- Exporting a Snowflake Semantic View to Ossie format using `SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW`
- Creating a Snowflake Semantic View from Ossie YAML using `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML`
- Converting between Ossie and Power BI formats using the `ossie-microsoft` CLI converter
- Round-tripping changes between Snowflake and Power BI through Ossie
- Establishing a git-based pipeline as the source of truth for semantic model governance

### What You Will Build
- A TPCDS-based semantic model that lives in Snowflake and Power BI, governed through a git-based Ossie YAML pipeline

### What You Will Need
- A free [Snowflake Account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Power BI Desktop (optional, for viewing/editing the .bim file)
- Python 3.11+ and [uv](https://docs.astral.sh/uv/) installed locally
- Git installed locally


<!-- ------------------------ -->
## Part 1 - Setup: Create a Semantic View and Export to Ossie

Duration: 15

### Install the Microsoft converter

The Apache Ossie repository contains CLI converters for platform-specific formats. You only need the Microsoft converter for the Power BI leg of the round-trip. The Snowflake leg uses built-in SQL functions, so no Snowflake converter is needed.

```bash
git clone https://github.com/apache/ossie.git
cd ossie/converters/microsoft
uv sync
cd ../../..
```

Verify the converter is available:

```bash
cd ossie/converters/microsoft
uv run ossie-microsoft --help
cd ../../..
```

### Load TPCDS sample data in Snowflake

Snowflake provides TPCDS sample data out of the box. Create a database with views over the relevant tables:

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS TPCDS;
CREATE SCHEMA IF NOT EXISTS TPCDS.PUBLIC;

-- Create views over the shared sample data
-- LIMIT on STORE_SALES keeps the sample manageable; adjust or remove for real workloads
CREATE OR REPLACE VIEW TPCDS.PUBLIC.STORE_SALES AS
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE_SALES LIMIT 1000000;

CREATE OR REPLACE VIEW TPCDS.PUBLIC.DATE_DIM AS
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.DATE_DIM;

CREATE OR REPLACE VIEW TPCDS.PUBLIC.CUSTOMER AS
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.CUSTOMER;

CREATE OR REPLACE VIEW TPCDS.PUBLIC.ITEM AS
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.ITEM;

CREATE OR REPLACE VIEW TPCDS.PUBLIC.STORE AS
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE;
```

### Create the Semantic View

The Ossie repository includes a pre-built TPCDS retail semantic model in Snowflake format at `converters/snowflake/tests/example_converted_tpcds_semantic_model.yaml`. This model defines five tables (store_sales, date_dim, customer, item, store), their relationships, and metrics like total_sales, total_profit, and customer_lifetime_value.

Upload the YAML to a stage and create the semantic view:

```sql
-- Create a stage for semantic model files
CREATE STAGE IF NOT EXISTS TPCDS.PUBLIC.SEMANTIC_MODELS;

-- Upload the YAML file (run from SnowSQL or Snowsight)
PUT file://ossie/converters/snowflake/tests/example_converted_tpcds_semantic_model.yaml
    @TPCDS.PUBLIC.SEMANTIC_MODELS AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Create the semantic view from the YAML
CREATE OR REPLACE SEMANTIC VIEW TPCDS.PUBLIC.TPCDS_RETAIL_MODEL
    YAML = (SELECT $1 FROM @TPCDS.PUBLIC.SEMANTIC_MODELS/example_converted_tpcds_semantic_model.yaml);
```

> **Verify**: The TPCDS YAML in the Ossie repo is in Cortex Analyst semantic model format. Confirm that `CREATE SEMANTIC VIEW ... YAML =` accepts this format, or whether it needs to be converted to semantic view YAML first. Also verify the `SELECT $1 FROM @stage/file` syntax works for loading YAML from a stage.

### Export the Semantic View to Ossie format

Use Snowflake's built-in function to export the semantic view as Ossie YAML:

```sql
SELECT SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW(
    'TPCDS.PUBLIC.TPCDS_RETAIL_MODEL'
);
```

This returns the full Ossie YAML document. Copy the output and save it locally as `tpcds_retail_model.ossie.yaml`. This is the vendor-neutral Ossie representation of your Snowflake semantic view.

Review the output. You will see the Ossie structure: `version`, `semantic_model`, `datasets` with `fields` and `dimension` markers, `relationships`, and `metrics` — all with `SNOWFLAKE` dialect expressions. Snowflake-specific features that have no Ossie equivalent are preserved in `SNOWFLAKE` vendor `custom_extensions` so they survive a round-trip.


<!-- ------------------------ -->
## Part 2 - Forward Flow: Ossie to Power BI

Duration: 10

This section converts the Ossie YAML you exported from Snowflake into a Power BI semantic model.

### Convert Ossie to Power BI

Run the Microsoft converter to produce a TMSL `model.bim` file:

```bash
cd ossie/converters/microsoft
uv run ossie-microsoft export -i /path/to/tpcds_retail_model.ossie.yaml -o model.bim
```

This produces a standard Power BI semantic model definition that can be opened in Power BI Desktop, Tabular Editor, or any tool that reads TMSL.

### What gets converted

| Ossie Concept | Power BI Equivalent |
|---|---|
| datasets | tables |
| fields | columns |
| metrics (SQL aggregates) | DAX measures (auto-translated) |
| relationships | relationships |
| ai_context | stored in annotations |
| custom_extensions (non-Power-BI) | preserved for round-trip |

Simple SQL aggregates like `SUM(column)`, `COUNT(DISTINCT column)`, and `AVG(column)` are automatically translated to their DAX equivalents. Complex SQL expressions that cannot be safely converted get a `BLANK()` placeholder and a warning — the converter will never silently produce wrong numbers.

### Review converter warnings

The converter reports anything it could not convert faithfully on stderr. This is expected — not an error:

```
[model] ai_context has no Power BI counterpart; preserved in annotations
3 construct(s) could not be converted faithfully; see the messages above.
```

Anything stored in `custom_extensions` with vendor `POWER_BI` or `SNOWFLAKE` will round-trip back when you convert the model back to Ossie.


<!-- ------------------------ -->
## Part 3 - Reverse Flow: Power BI to Snowflake

Duration: 10

This section demonstrates the reverse direction: making a change in Power BI's native language (DAX) and pushing that change back through Ossie to Snowflake.

### Modify a measure in the Power BI model

Open `model.bim` in a text editor, Tabular Editor, or Power BI Desktop. Find the `total_sales` measure and modify its DAX expression. For example, add a year filter:

Before:
```
SUM('store_sales'[ss_ext_sales_price])
```

After:
```
CALCULATE(SUM('store_sales'[ss_ext_sales_price]), 'date_dim'[d_year] = 2002)
```

This simulates a business user or analyst making changes in Power BI's native language.

### Convert Power BI back to Ossie

```bash
cd ossie/converters/microsoft
uv run ossie-microsoft import -i model.bim -o tpcds_retail_model_updated.ossie.yaml
```

The modified DAX expression is preserved as-is in a `DAX` dialect entry in the Ossie YAML. The converter intentionally does not rewrite DAX to SQL — the two languages have fundamentally different evaluation models. A partial rewrite would produce a model that returns numbers, just the wrong numbers.

### Push updated Ossie back to Snowflake

Use the Snowflake stored procedure to create or replace the semantic view from the updated Ossie YAML:

```sql
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML(
    'TPCDS.PUBLIC',
    $$
    <paste the contents of tpcds_retail_model_updated.ossie.yaml here>
    $$
);
```

The semantic view is now updated with the changes that originated in Power BI.

**Important**: DAX-dialect metrics are preserved in the semantic view's Ossie representation, but Snowflake Cortex Analyst evaluates SQL, not DAX. Review any metrics with `DAX` dialect entries and author the SQL equivalent before using the semantic view with Cortex Analyst.


<!-- ------------------------ -->
## Part 4 - Pipeline: Git as the Source of Truth

Duration: 10

The manual steps from Parts 1-3 demonstrate the mechanics. In practice, you need a governed process to keep models in sync. The best practice is to store the Ossie YAML in git as the single source of truth.

### Why git

Without a single source of truth, semantic models drift. Someone changes a metric in Snowflake. Someone else changes a metric in Power BI. The two definitions diverge and nobody notices until the numbers don't match.

Git solves this:

- **One canonical file**: the Ossie YAML in the repository is the definition
- **Change review**: all changes go through pull requests, whether they originated in Snowflake or Power BI
- **Audit trail**: git log shows who changed what, when, and why
- **Merge conflicts**: if two people change the same metric in different platforms, git surfaces the conflict instead of silently overwriting

### Repository structure

```
semantic-models/
├── models/
│   └── tpcds_retail_model.ossie.yaml    # Source of truth
├── scripts/
│   ├── deploy.sh                         # Ossie -> Snowflake + Power BI
│   ├── sync_from_snowflake.sh            # Snowflake -> Ossie
│   └── sync_from_powerbi.sh              # Power BI -> Ossie
└── README.md
```

### Deploy script: Ossie to Snowflake and Power BI

```bash
#!/bin/bash
# deploy.sh — Deploy the Ossie model to Snowflake and Power BI
set -e

MODEL_PATH=$1
if [ -z "$MODEL_PATH" ]; then
    echo "Usage: ./deploy.sh <path_to_ossie_model.yaml>"
    exit 1
fi

MODEL_NAME=$(basename "$MODEL_PATH" .ossie.yaml)

# Deploy to Power BI
echo "Converting to Power BI..."
cd ossie/converters/microsoft
uv run ossie-microsoft export --strict -i "$MODEL_PATH" -o "${MODEL_NAME}.bim"
cd ../../..

# Deploy to Snowflake
# NOTE: Verify shell escaping works in your environment before using in CI/CD
echo "Deploying to Snowflake semantic view..."
snow sql -q "CALL SYSTEM\$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML('TPCDS.PUBLIC', \$\$$(cat "$MODEL_PATH")\$\$);"

echo "Deployed to Snowflake and Power BI."
```

The `--strict` flag on the Microsoft converter causes the script to fail if anything could not be converted faithfully. This is the mode you want in a pipeline that must not silently degrade a model.

### Sync script: pull changes back from Snowflake

When someone makes a change in Snowflake, export it back to Ossie and commit:

```bash
#!/bin/bash
# sync_from_snowflake.sh — Export Snowflake semantic view changes back to Ossie
set -e

SEMANTIC_VIEW=$1   # e.g., TPCDS.PUBLIC.TPCDS_RETAIL_MODEL
OUTPUT_PATH=$2     # e.g., models/tpcds_retail_model.ossie.yaml

if [ -z "$SEMANTIC_VIEW" ] || [ -z "$OUTPUT_PATH" ]; then
    echo "Usage: ./sync_from_snowflake.sh <SEMANTIC_VIEW> <output_path>"
    exit 1
fi

echo "Exporting Snowflake semantic view to Ossie..."
# NOTE: Verify the snow sql output format and parsing work in your environment
snow sql -q "SELECT SYSTEM\$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW('${SEMANTIC_VIEW}');" -o tsv | tail -1 > "$OUTPUT_PATH"

echo "Exported to $OUTPUT_PATH"
echo "Review the diff, then commit:"
echo "  git diff $OUTPUT_PATH"
echo "  git add $OUTPUT_PATH && git commit -m 'Sync changes from Snowflake'"
```

### Sync script: pull changes back from Power BI

When someone makes a change in Power BI, import it back to Ossie and commit:

```bash
#!/bin/bash
# sync_from_powerbi.sh — Import Power BI model changes back to Ossie
set -e

BIM_PATH=$1        # e.g., tpcds_retail_model.bim
OUTPUT_PATH=$2     # e.g., models/tpcds_retail_model.ossie.yaml

if [ -z "$BIM_PATH" ] || [ -z "$OUTPUT_PATH" ]; then
    echo "Usage: ./sync_from_powerbi.sh <model.bim> <output_path>"
    exit 1
fi

echo "Importing Power BI model to Ossie..."
cd ossie/converters/microsoft
uv run ossie-microsoft import -i "$BIM_PATH" -o "$OUTPUT_PATH"

echo "Exported to $OUTPUT_PATH"
echo "Review the diff, then commit:"
echo "  git diff $OUTPUT_PATH"
echo "  git add $OUTPUT_PATH && git commit -m 'Sync changes from Power BI'"
```

### The workflow

1. **All changes go through git.** Whether a metric was edited in Snowflake, Power BI, or directly in the Ossie YAML, the change gets exported back to Ossie and committed to the repository.
2. **Pull requests for review.** The Ossie YAML diff shows exactly what changed in a human-readable format. Reviewers can approve or reject before it reaches any platform.
3. **CI/CD deploys on merge.** When a PR is merged to main, `deploy.sh` runs to push the updated model to both Snowflake and Power BI.
4. **Conflicts are visible.** If someone changes a metric in Snowflake while someone else changes the same metric in Power BI, git shows the merge conflict when both changes are committed — instead of one silently overwriting the other.


<!-- ------------------------ -->
## Conclusion and Resources

Duration: 2

You have walked through the complete Ossie interchange flow: exporting a Snowflake semantic view to Ossie format, converting it to a Power BI semantic model, making changes in DAX, and pushing those changes back to Snowflake. The pipeline section established the best practice: store the Ossie YAML in git as the single source of truth, and use automation to deploy to both platforms.

Ossie is the hub, not a one-time migration tool. By governing semantic models through git and deploying through automation, you eliminate metric drift between platforms and get review, audit trail, and conflict resolution for free.

### What You Learned
- How Apache Ossie serves as a vendor-neutral hub for semantic model interchange
- Exporting a Snowflake Semantic View to Ossie format with `SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW`
- Creating a Snowflake Semantic View from Ossie YAML with `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML`
- Converting between Ossie and Power BI formats with the `ossie-microsoft` CLI converter
- Round-tripping changes between Snowflake and Power BI through Ossie
- Establishing a git-based pipeline for semantic model governance

### Resources
- [Apache Ossie (incubating)](https://ossie.apache.org/)
- [Apache Ossie GitHub Repository](https://github.com/apache/ossie)
- [Apache Ossie Core Specification](https://github.com/apache/ossie/blob/main/core-spec/spec.md)
- [SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW](https://docs.snowflake.com/en/sql-reference/functions/system_read_ossie_yaml_from_semantic_view)
- [SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML](https://docs.snowflake.com/en/sql-reference/stored-procedures/system_create_semantic_view_from_ossie_yaml)
- [Snowflake Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic)
- [Power BI Semantic Models](https://learn.microsoft.com/en-us/power-bi/connect-data/service-datasets-understand)

If you have any questions, reach out to your Snowflake account team!

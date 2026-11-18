author: Chanin Nantasenamat
id: build-r-python-drug-discovery-apps-and-agents
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search, snowflake-site:taxonomy/industry/healthcare-and-life-sciences
language: en
summary: Train an R QSAR model for aromatase inhibition, serve it with R Plumber on Snowpark Container Services, and expose it through Streamlit, MCP, and Cortex Agents.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# Build R and Python Powered Drug Discovery Apps and Agents on Snowflake

## Overview

Drug discovery teams rely heavily on R for molecular modeling and cheminformatics, yet a gap often separates where R models are built from where bench scientists use them. Consider human aromatase (`CYP19A1`), the cytochrome P450 enzyme that converts androgens (androstenedione and testosterone) into estrogens (estrone and estradiol). Because hormone-receptor-positive breast cancers depend on estrogen to grow, blocking aromatase with inhibitors such as letrozole, anastrozole, and exemestane is a major therapeutic strategy.

Building on published quantitative structure-activity relationship (QSAR) and proteochemometric studies of aromatase inhibitors ([Worachartcheewan et al., 2014](https://www.sciencedirect.com/science/article/abs/pii/S0169743914001646); [Shoombuatong et al., 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4614109/); [Simeon et al., 2016](https://peerj.com/articles/1979/); [Shoombuatong et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6123608/)), the workflow we build in this tutorial trains and deploys an R QSAR model to estimate a molecule's inhibitory potency (`pIC50`, the negative base-10 logarithm of the molar `IC50` concentration, where `pIC50 >= 6.5` indicates an Active inhibitor) directly from its chemical structure. The figure below shows the estrogen biosynthesis pathway and QSAR inhibition target on the left (Panel A) with the experimental X-ray crystal structure of human placental aromatase on the right (Panel B, RCSB Protein Data Bank entry [3EQM](https://www.rcsb.org/structure/3EQM) at 2.90 angstrom resolution, showing `CYP19A1` complexed with bound androstenedione and its heme cofactor).

![Two-panel diagram showing (A) the estrogen biosynthesis pathway from androgens via aromatase CYP19A1 to estrogens and its blockade by aromatase inhibitors, and (B) the experimental X-ray crystal structure of human placental aromatase RCSB PDB 3EQM at 2.90 angstrom resolution with bound androstenedione and heme cofactor](assets/aromatase-pathway-structure.png)

In most labs, a working R model stays trapped on a laptop reading local CSV files or on an on-premises high-performance computing (HPC) rack, and teams often assume that moving to production requires rewriting the pipeline in another language. Instead, this guide combines R and Python on Snowflake into reproducible, testable stages ([Schaduangrat et al., 2020](https://link.springer.com/article/10.1186/s13321-020-0408-x)): in R, `rcdk` computes 1,024-bit Extended-Connectivity Fingerprints (ECFP4) with the Chemistry Development Kit (CDK), `caret` filters near-zero-variance bits, `ranger` trains a 500-tree quantile random forest, and an R Plumber API serves the model on Snowpark Container Services. Python and Snowflake handle ChEMBL data curation in Snowflake Notebooks, SQL service functions, an interactive Streamlit in Snowflake app, a Model Context Protocol (MCP) server, and a Cortex Agent.

In practice, you curate 7,040 raw ChEMBL activity records down to 2,751 unique compounds and trace letrozole (`CHEMBL1444`, measured `pIC50` of `9.15`) from its Simplified Molecular Input Line Entry System (SMILES) string to a live R prediction (`7.89`, with uncalibrated 5th to 95th percentile model quantiles of `5.79` to `9.22`) across SQL, Streamlit, MCP, and Cortex Agents. The next section summarizes the specific skills you will gain along this journey.

### What You'll Learn
- How to curate and standardize ChEMBL bioactivity records for human aromatase in a Snowflake Notebook
- How to encode SMILES strings as 1,024-bit ECFP4 circular fingerprints with `rcdk` and train a quantile random forest with `ranger` in R
- How to prevent feature-selection leakage by splitting training and test sets before filtering near-zero-variance fingerprint bits
- How to package an R model, its ordered feature list, and a Plumber API as a container service on Snowpark Container Services
- How to authenticate to a public Snowpark Container Services endpoint using a programmatic access token (PAT)
- How to connect the R service to SQL service functions, a multipage Streamlit in Snowflake app, an external MCP client, and a Cortex Agent
- Which statistical, operational, and governance limitations to check before another scientist depends on the service

Now that you know the skills covered in this tutorial, review the prerequisites required to run the workflow in your own environment.

### What You'll Need
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with `ACCOUNTADMIN` access for the one-time setup
- [Docker](https://www.docker.com/) with `linux/amd64` build support
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) configured with a connection to your account
- Python 3.11 or later with `requests`, `pandas`, `pyyaml`, `toml`, `rdkit`, and `snowflake-connector-python`
- Basic familiarity with R, Python, and SQL

With those prerequisites in place, let us look at the architecture and components you will assemble.

### What You'll Build
You will build an end-to-end R and Python drug discovery application for predicting human aromatase inhibition:

- A biological target and curation workflow in a Snowflake Notebook that transforms raw ChEMBL records for human aromatase (`CHEMBL1978`) into 2,751 deduplicated compounds with exploratory analysis and Lipinski Rule-of-Five descriptors
- An R training script that computes CDK ECFP4 fingerprints, selects informative bits, fits a 500-tree `ranger` quantile random forest, and exports paired model and feature artifacts
- An R Plumber container service on Snowpark Container Services exposing `/health`, `/predict`, `/sf/*` SQL service-function routes, and `/mcp`, connected directly to external AI chat clients over MCP
- Shared SQL functions (`PREDICT_PIC50`, `ECFP4`, `SIMILAR_COMPOUNDS`, `EXPLAIN_PREDICTION`, and RDKit `RO5`) and a second Snowflake Notebook that batch-scores the 2,751 compounds
- A multipage Streamlit in Snowflake app with Dashboard, Single Prediction, Batch Prediction, About, and Ask an Agent pages
- A Cortex Agent (`AROMATASE_AGENT`) backed by an Apache Ossie semantic view (`AROMATASE_SV`), a Cortex Search service (`ASSAY_SEARCH`), and a candidate triage procedure (`TRIAGE_COMPOUNDS`)

The four-lane architecture diagram below maps every data handoff and calling route across the system, and the tutorial sections follow these four lanes in order.

![Architecture of the R and Python drug discovery app across four lanes: data preparation and model training, model serving and compound scoring, exploring results in Streamlit, and research Q&A and candidate triage with Cortex Agents](assets/methodology-architecture.png)

1. **Data Preparation + Model Training.** Notebook 01 (`01_PREPARE_TRAINING_DATA`) fetches ChEMBL bioactivity records for `CHEMBL1978`, curates 2,751 non-redundant compounds into `CHEMBL1978_COMPOUNDS`, and exports `chembl1978_cleaned.csv` to `@QSAR_STAGE`. The R training script (`docker/train_rcdk.R`) reads that CSV, computes 1,024-bit CDK ECFP4 fingerprints, selects informative bits, and trains the 500-tree `ranger` quantile random forest (`R MODEL ARTIFACTS`).
2. **Serve Model + Score Compounds.** The saved `.rds` model, ordered `kept_bits.csv` list, and measured fingerprints are packaged into the R Plumber service (`QSAR_PLUMBER_SVC`) on Snowpark Container Services. External AI chat clients (`MCP CLIENT`) connect to `/mcp` over HTTPS using a PAT to invoke the six R tools directly, while shared SQL functions (`sql/functions.sql`) wrap `/sf/*` so Notebook 02 (`02_SCORE_COMPOUNDS`) can batch-score all 2,751 compounds.
3. **Explore Results.** Notebook 02 writes scored tables (`PREDICTIONS + DESCRIPTORS`) and exports stage summaries (`dashboard_eda.csv`, `dashboard_ro5.csv`, `dashboard_predictions.csv`, `top_features.csv`, and `training_metrics.json`) to `@QSAR_STAGE`. The Streamlit in Snowflake app (`QSAR_AROMATASE_APP`) reads `@QSAR_STAGE` for the Dashboard and About pages and calls `/predict` on `QSAR_PLUMBER_SVC` for Single and Batch Prediction.
4. **Research Q&A + Candidate Triage.** `AROMATASE_AGENT` orchestrates Cortex Analyst (`AROMATASE_SV`), Cortex Search (`ASSAY_SEARCH`), the candidate triage procedure (`TRIAGE_COMPOUNDS`, capped at 20 SMILES), and the shared SQL functions to power conversational Q&A and candidate prioritization (`ASK AN AGENT`). Solid arrows denote steps within a lane, while dashed arrows denote cross-lane artifact and service calls.

Now that you have a clear map of the architecture, you can clone the companion repository and provision the Snowflake environment.

## Setup

Before running any notebooks or container builds, you need a local copy of the project files and the Snowflake role, warehouse, database, compute pools, and external access integrations that host the workflow.

### Create Working Directory

The setup script creates all 38 project files (`data/`, `docker/`, `streamlit/`, `notebooks/`, `native_app/`, `scripts/`, `sql/`, `agent/`, and `docs/`) directly on your computer inside `bioinformatics/r-python-drug-discovery`. All file contents (including the bundled `.rds` model and `CHEMBL1978` snapshot) are included in the script, so folder setup works offline without cloning a separate repository.

Open [setup_r_python_drug_discovery.sh](https://github.com/sfc-gh-cnantasenamat/sfguide-build-r-python-drug-discovery-apps-and-agents/blob/main/quickstart/build-r-python-drug-discovery-apps-and-agents/src/setup_r_python_drug_discovery.sh) and use GitHub's **Download raw file** button to save it in your chosen local working directory. The script is bundled in this guide's `src/` folder, alongside `assets/`. If you already downloaded the guide files, copy `src/setup_r_python_drug_discovery.sh` into your chosen working directory instead.

**Run this step:** Open a terminal in the directory containing `setup_r_python_drug_discovery.sh` and run the setup script, then change into `bioinformatics/r-python-drug-discovery`.

```bash
bash setup_r_python_drug_discovery.sh
cd bioinformatics/r-python-drug-discovery
pwd
```

**Expected output:** Review the expected setup output below (no action required; no Snowflake statements or container builds have run yet, and all subsequent relative file paths in this guide run from `bioinformatics/r-python-drug-discovery`):

```text
Created 38 project files in bioinformatics/r-python-drug-discovery.
No Snowflake statements or container builds were executed.
```

The `r-python-drug-discovery` directory is organized by architectural layer:

| Folder | Contents |
|---|---|
| `data/` | Snapshot of the cleaned `CHEMBL1978` dataset (2,751 compounds) used for the bundled model |
| `docker/` | R training script (`train_rcdk.R`), Plumber API (`plumber_api.R`), `Dockerfile.plumber`, SPCS specification, and bundled model artifacts |
| `streamlit/` | Multipage Streamlit app (`app.py`, `_shared.py`, and page modules) |
| `notebooks/` | `01_prepare_training_data.ipynb` (curation and EDA) and `02_score_compounds.ipynb` (batch scoring and agent tables) |
| `native_app/` | Optional Snowflake Native App package for per-consumer MCP deployment |
| `scripts/` | Endpoint smoke test (`test_endpoint.py`), dashboard data generator, and agent deployment script (`deploy_agent.py`) |
| `sql/` | Snowflake setup (`setup.sql`), shared SQL functions (`functions.sql`), and agent DDL (`agent.sql`) |
| `agent/` | Cortex Agent specification (`aromatase_agent.yaml`), Apache Ossie semantic specification (`aromatase_sv_ossie.yaml`), and 15-case evaluation fixtures |
| `docs/` | Standalone MCP client walkthrough (`mcp-walkthrough.md`) |

With the repository on disk, the next step is creating the Snowflake objects that own and run the pipeline.

### Create Snowflake Objects

**Run this step:** Open `sql/setup.sql` in a Snowsight SQL worksheet, replace `<your_user>` with your Snowflake username, and run steps 1 through 4. The script provisions:

- `QSAR_ROLE`, a dedicated role that owns all project objects and is granted to `SYSADMIN`
- `QSAR_WH`, an extra-small warehouse for SQL queries
- `QSAR_DB` with stage `QSAR_STAGE`, image repository `QSAR_REPO`, and audit table `QSAR_PREDICTIONS_LOG`
- `QSAR_CPU_POOL`, a single-node `CPU_X64_S` compute pool for the R Plumber service
- `QSAR_ST_POOL`, a small `CPU_X64_XS` compute pool for the Streamlit container runtime and notebook runs
- `QSAR_APP_EAI`, an external access integration allowing the app to install packages from PyPI and optionally query PubChem
- `QSAR_NB_EAI`, an external access integration allowing the notebooks to fetch ChEMBL bioactivity data and install `rdkit`

Review the core role, compute pool, and privilege grants from **sql/setup.sql** below (run the full `sql/setup.sql` script in Snowsight):

```sql
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS QSAR_ROLE;
GRANT ROLE QSAR_ROLE TO USER <your_user>;
-- SYSADMIN (and so ACCOUNTADMIN) inherits QSAR_ROLE, so admin CLI connections can use its objects
GRANT ROLE QSAR_ROLE TO ROLE SYSADMIN;

CREATE COMPUTE POOL IF NOT EXISTS QSAR_CPU_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 3600
    COMMENT = 'QSAR aromatase SPCS inference';
GRANT USAGE, MONITOR ON COMPUTE POOL QSAR_CPU_POOL TO ROLE QSAR_ROLE;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE QSAR_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.PYPI_REPOSITORY_USER TO ROLE QSAR_ROLE;
```

`QSAR_ROLE` owns everything created in this guide. Because `sql/setup.sql` grants `QSAR_ROLE` to `SYSADMIN`, Snowflake CLI commands also work from a connection whose default role is `SYSADMIN` or `ACCOUNTADMIN`.

**Check:** Run the verification query below in a Snowsight worksheet to confirm that `QSAR_ROLE` holds the required warehouse, compute pool, integration, and endpoint privileges.

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
SHOW GRANTS TO ROLE QSAR_ROLE;
SELECT "privilege", "granted_on", "name"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "granted_on" IN ('WAREHOUSE', 'COMPUTE_POOL', 'INTEGRATION', 'ACCOUNT')
ORDER BY 2, 3, 1;
```

You should see eight rows in this filtered result: `BIND SERVICE ENDPOINT` on the account, `USAGE` and `MONITOR` on `QSAR_CPU_POOL` and `QSAR_ST_POOL`, `USAGE` on `QSAR_APP_EAI` and `QSAR_NB_EAI`, and `USAGE` on `QSAR_WH`. The `SNOWFLAKE.PYPI_REPOSITORY_USER` database role is a separate grant that lets `RO5()` pin the notebook's RDKit version. Record the `repository_url` returned by `SHOW IMAGE REPOSITORIES` at the end of `sql/setup.sql`, as you will push the R container image to that URL.

With the Snowflake role, pools, stage, and external access integrations ready, you can now curate the experimental ChEMBL bioactivity records that ground the R model.

## 1. Data Preparation + Model Training

This stage curates raw ChEMBL bioactivity records for human aromatase into a clean modeling table and trains the 500-tree `ranger` quantile random forest in R.

### 1.1. Prepare Training Data

Before training any model, you must decide which experimental measurements count and standardize them into a single, non-redundant table. An `IC50` value is the concentration associated with 50% inhibition in an assay, whereas a model prediction is an estimate rather than a new measurement.

#### Curate the Cohort

`notebooks/01_prepare_training_data.ipynb` applies a four-stage curation funnel to public ChEMBL records for human aromatase (`CHEMBL1978`):

1. **Source (`7,040` activity records):** Queries the ChEMBL REST API for all bioactivity records associated with target `CHEMBL1978`.
2. **Select (`3,960` `IC50` records):** Filters for binding assays (`assay_type = 'B'`) with exact potency measurements (`standard_type = 'IC50'` and `standard_relation = '='`), leaving out `Ki`, `Kd`, `EC50`, and censored inequalities, and saves them to `CHEMBL1978_RAW_ACTIVITIES` alongside 313 assay descriptions (`CHEMBL1978_ASSAYS`) and 198 publication records (`CHEMBL1978_DOCUMENTS`).
3. **Standardize (`pIC50`):** Retains nanomolar (`nM`) records that have both a valid canonical SMILES string and a `pChEMBL` value (`-log10` of molar potency, which equals `pIC50` here because only `IC50` records were selected).
4. **Remove redundancy (`2,751` compounds):** Deduplicates repeat measurements per `molecule_chembl_id` by keeping the highest measured `pIC50` and labels compounds Active (`1`) at `pIC50 >= 6.5` (about `316 nM` or lower) and Inactive (`0`) below `6.5`, saving `1,061` active and `1,690` inactive molecules to `CHEMBL1978_COMPOUNDS`.

> **Note:** Keeping the highest measured `pIC50` per molecule is this tutorial's modeling choice and can overrepresent stronger reported activity across heterogeneous cell-based and recombinant enzyme assays. It is not a universal assay-reconciliation rule.

Now that you understand the four curation decisions, upload and execute Notebook 01 in Snowflake.

#### Run the Notebook

**Run this step:** In a Snowsight SQL worksheet, create a stage to hold the notebook files.

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
USE SCHEMA QSAR_DB.PUBLIC;
CREATE STAGE IF NOT EXISTS NB_PROJECT_STAGE;
```

**Run this step:** From the cloned repository root in your local terminal, upload both notebooks to `@QSAR_DB.PUBLIC.NB_PROJECT_STAGE` (`PUT` reads local files, so run it from the terminal rather than a Snowsight worksheet).

```bash
snow sql -q "PUT file://notebooks/*.ipynb @QSAR_DB.PUBLIC.NB_PROJECT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
```

**Run this step:** Back in the Snowsight SQL worksheet, create the notebook project from `@NB_PROJECT_STAGE` and execute `01_prepare_training_data.ipynb` on `QSAR_ST_POOL` with `QSAR_NB_EAI` attached.

```sql
CREATE OR REPLACE NOTEBOOK PROJECT QSAR_NOTEBOOKS FROM '@NB_PROJECT_STAGE';

EXECUTE NOTEBOOK PROJECT QSAR_NOTEBOOKS
    MAIN_FILE = '01_prepare_training_data.ipynb'
    COMPUTE_POOL = 'QSAR_ST_POOL'
    QUERY_WAREHOUSE = 'QSAR_WH'
    RUNTIME = 'V2-CPU-PY3.12'
    EXTERNAL_ACCESS_INTEGRATIONS = (QSAR_NB_EAI);
```

The execution takes about three minutes and writes `chembl1978_cleaned.csv`, `dashboard_eda.csv`, and `dashboard_ro5.csv` to `@QSAR_STAGE`. You can also open the notebook interactively in Snowsight Workspaces on a Container Runtime (`V2-CPU-PY3.12`) with `QSAR_NB_EAI` enabled to inspect the exploratory plots cell by cell.

Once the notebook run finishes, verify the curated table counts and stage outputs.

#### Check the Result

**Check:** Run the query below in Snowsight to confirm that the Notebook 01 curation pipeline populated `3,960` raw `IC50` records, `2,751` deduplicated compounds, `1,061` active molecules, `313` assays, and `198` publications (from ChEMBL 37; a newer ChEMBL release can change these counts).

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
SELECT
    (SELECT COUNT(*) FROM QSAR_DB.PUBLIC.CHEMBL1978_RAW_ACTIVITIES)      AS RAW_RECORDS,
    (SELECT COUNT(*) FROM QSAR_DB.PUBLIC.CHEMBL1978_COMPOUNDS)           AS COMPOUNDS,
    (SELECT SUM(ACTIVITY_CLASS) FROM QSAR_DB.PUBLIC.CHEMBL1978_COMPOUNDS) AS ACTIVE,
    (SELECT COUNT(*) FROM QSAR_DB.PUBLIC.CHEMBL1978_ASSAYS)              AS ASSAYS,
    (SELECT COUNT(*) FROM QSAR_DB.PUBLIC.CHEMBL1978_DOCUMENTS)           AS PUBLICATIONS;
```

**Expected output:** Review the expected query output below (no action required):

```text
RAW_RECORDS  COMPOUNDS  ACTIVE  ASSAYS  PUBLICATIONS
-----------  ---------  ------  ------  ------------
       3960       2751    1061     313           198
```

Notebook 01 also computes Lipinski Rule-of-Five physicochemical properties (`MW <= 500 Da`, `LogP <= 5`, `HBD <= 5`, `HBA <= 10`) using RDKit and exports `dashboard_eda.csv` and `dashboard_ro5.csv` to `@QSAR_STAGE` so the Streamlit Dashboard (in Section 3) can render the activity and descriptor distributions without re-querying ChEMBL.

With `2,751` curated aromatase compounds and `chembl1978_cleaned.csv` staged in Snowflake, you are ready to encode the molecular structures and train the quantile random forest in R.

### 1.2. Train the R Model

A random forest cannot consume raw SMILES text directly. In this section, you inspect how `docker/train_rcdk.R` converts each molecule into a binary fingerprint, splits the dataset before feature selection to avoid test-set leakage, and fits a 500-tree `ranger` quantile random forest.

#### Get the Training Data

**Run this step:** Download `chembl1978_cleaned.csv` from `@QSAR_DB.PUBLIC.QSAR_STAGE` to `/tmp/chembl1978_stage.csv` to confirm the staged export, while keeping `data/chembl1978_cleaned.csv` intact so your training run uses the reference snapshot's exact row order.

```bash
snow sql -q "GET @QSAR_DB.PUBLIC.QSAR_STAGE/chembl1978_cleaned.csv file:///tmp/"
head -n 2 data/chembl1978_cleaned.csv
```

Review the first row of **data/chembl1978_cleaned.csv** below (no action required) to see the schema consumed by R:

```text
molecule_chembl_id,canonical_smiles,standard_value,pchembl_value,activity_class
CHEMBL4632445,CCC#CCOc1ccc2c(=O)c3ccc(Cn4ccnc4)cc3oc2c1,0.01,11.0,1
```

Next, examine how `rcdk` turns each `canonical_smiles` string into model features.

#### Compute Fingerprints

> **Note:** The R snippets in this subsection and the next are already in `docker/train_rcdk.R` on disk. Review them to understand the feature contract before running the training container.

Review the fingerprint calculation in **docker/train_rcdk.R** below (no action required) to see how CDK parses each SMILES string and hashes circular atom neighborhoods up to bond depth 2 (`ECFP4`) into a 1,024-position vector of `1`s and `0`s:

```r
fps <- lapply(mols, function(mol) {
  fp <- get.fingerprint(mol, type = "circular", circular.type = "ECFP4",
                        depth = 2, size = 1024)
  v  <- integer(1024)
  v[fp@bits] <- 1L
  v
})
```

Because circular substructures are folded into 1,024 fixed positions by hashing, a bit indicates the presence of one or more local atom patterns (and hash collisions can occur). To prevent data leakage from the test set into feature selection, `docker/train_rcdk.R` splits the molecules 80/20 (`2,203` training rows and `548` test rows) first and then runs `caret::nearZeroVar()` on the training matrix only, saving the ordered list of kept bit names (`kept_bits_rcdk.csv`) and selecting those exact columns in the test matrix.

Review the split-first feature filter in **docker/train_rcdk.R** below (no action required):

```r
train_idx <- as.vector(createDataPartition(df$pchembl_value, p = 0.8, list = FALSE))
train_x   <- fp_matrix[ train_idx, , drop = FALSE]
test_x    <- fp_matrix[-train_idx, , drop = FALSE]

nzv_idx <- nearZeroVar(train_x, saveMetrics = FALSE)
if (length(nzv_idx) > 0) train_x <- train_x[, -nzv_idx, drop = FALSE]
kept <- colnames(train_x)
test_x <- test_x[, kept, drop = FALSE]
stopifnot(identical(colnames(train_x), colnames(test_x)))
```

With the training matrix filtered to its informative bits, the script fits the quantile random forest.

#### Train a Quantile Forest

Review the `ranger` call in **docker/train_rcdk.R** below (no action required) to see how the 500-tree regression forest is trained with `quantreg = TRUE` and regression impurity (`variance`) feature importance:

```r
model <- ranger(
  target ~ .,
  data       = train_df,
  num.trees  = 500,
  importance = "impurity",
  quantreg   = TRUE,
  seed       = 42
)
```

Notice that this is a regression model over continuous `pIC50`, not a separate binary classifier: the `Active` (`pIC50 >= 6.5`) and `Inactive` (`< 6.5`) labels are derived by thresholding the predicted median `pIC50`. Setting `quantreg = TRUE` allows the serving API to output the 5th, 50th (median), and 95th percentiles across the forest for each query molecule.

Now let us run the training script inside the same Docker image used for serving so that Java, CDK, `rcdk`, and `ranger` versions match byte for byte.

#### Run Training in Docker

**Run this step:** From the repository root, build the local R Plumber image and execute `docker/train_rcdk.R` inside a container with `data/`, `output/`, and `docker/` mounted.

```bash
docker build --platform linux/amd64 -f docker/Dockerfile.plumber -t r-qsar-plumber:local docker
mkdir -p output
docker run --rm --platform linux/amd64 \
  -v "$PWD/data:/data" -v "$PWD/output:/output" -v "$PWD/docker:/work" \
  r-qsar-plumber:local Rscript /work/train_rcdk.R
```

**Check:** Inspect `output/training_metrics.json` after the container finishes. When trained on the repository's `data/chembl1978_cleaned.csv` snapshot with the split-first `nearZeroVar()` filter, the script retains `180` bits and writes the following metrics to **output/training_metrics.json**:

```json
{
  "oob_r2": 0.6505,
  "test_r2": 0.6843,
  "test_rmse": 0.7721,
  "n_compounds": 2751,
  "n_active": 1061,
  "n_train": 2203,
  "n_test": 548,
  "n_bits": 180,
  "n_trees": 500,
  "fingerprint": "CDK ECFP4 (rcdk 3.8.2)",
  "model": "ranger quantile RF"
}
```

> **Note:** Always deploy `qsar_aromatase_model.rds` and `kept_bits.csv` as a matched pair, never mixing a model file from one run with the bit list from another. The repository's pre-bundled `docker/` artifacts (`178` bits, `test_r2: 0.6855`, `test_rmse: 0.7708`) are already in place and match the exact expected predictions (`7.89` for letrozole) used across Sections 2, 3, and 4, including the 15-question agent evaluation in Section 4.3. Keep the pre-bundled `docker/` files for this walkthrough, or if you later want to promote your freshly trained `output/` artifacts into `docker/`, copy all five files together (`cp output/qsar_aromatase_model_rcdk.rds docker/qsar_aromatase_model.rds && cp output/kept_bits_rcdk.csv docker/kept_bits.csv && cp output/top_features_rcdk.csv output/training_metrics.json output/train_fingerprints.csv docker/`).

Having trained the quantile random forest and inspected how it pairs with its ordered bit list, you can now package and serve the R model as an API on Snowpark Container Services.

## 2. Serve Model + Score Compounds

With the trained model artifacts in `docker/`, this stage packages the R model into an R Plumber service on Snowpark Container Services, connects external AI assistants via MCP, and batch-scores all `2,751` curated compounds through shared SQL functions.

### 2.1. Serve With R Plumber

To make the saved R model callable by colleagues, SQL queries, apps, and AI assistants without requiring anyone to install R or Java locally, `docker/plumber_api.R` wraps the model in an HTTP service on Snowpark Container Services.

#### Inspect the API

`docker/plumber_api.R` loads `qsar_aromatase_model.rds`, `kept_bits.csv`, `training_metrics.json`, and `train_fingerprints.csv` once at container startup and warms up the `rcdk` Java Virtual Machine (JVM). Its primary endpoints are:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Container readiness probe returning status, tree count, and feature count |
| `POST /predict` | Direct batch prediction endpoint used by the Streamlit app and smoke test |
| `POST /sf/predict`, `/sf/fingerprint`, `/sf/similar`, `/sf/explain` | Snowflake service-function routes for calling R from SQL |
| `POST /mcp` | Standalone MCP server over JSON-RPC 2.0 exposing six R tools |

When a SMILES string arrives, the service executes a four-stage inference contract:

1. **Parse:** CDK parses the SMILES string into a molecular graph and returns an explicit error if the syntax is invalid.
2. **Encode:** `get.fingerprint()` computes the 1,024-bit ECFP4 vector, and `fp_df[, kept_bits, drop = FALSE]` selects the exact ordered columns expected by the forest.
3. **Predict:** `predict(model, data = fp_df, type = "quantiles", quantiles = c(0.05, 0.5, 0.95))` returns the 5th percentile, median (`pIC50`), and 95th percentile across the 500 trees.
4. **Label:** A predicted median `pIC50 >= 6.5` is labeled `Active`, and `< 6.5` is labeled `Inactive`.

Review the feature-parity and quantile prediction lines from **docker/plumber_api.R** below (no action required):

```r
fp_obj <- get.fingerprint(mol, type = "circular",
  circular.type = "ECFP4", depth = 2, size = 1024)
fp_vec <- integer(1024)
fp_vec[fp_obj@bits] <- 1L
fp_df  <- as.data.frame(t(fp_vec))
colnames(fp_df) <- paste0("bit_", seq_len(1024))
fp_df  <- fp_df[, kept_bits, drop = FALSE]
pred   <- predict(model, data = fp_df, type = "quantiles",
                  quantiles = c(0.05, 0.5, 0.95))
```

Now build the container image and push it to your Snowflake image repository.

#### Build and Push

**Run this step:** Authenticate Docker to your Snowflake image registry, build `Dockerfile.plumber` for `linux/amd64`, and push the image to `<repository_url>/r-qsar-plumber:v1` (replace `<repository_url>` with the URL from `SHOW IMAGE REPOSITORIES`).

```bash
cd docker
snow spcs image-registry login
docker build --platform linux/amd64 -f Dockerfile.plumber \
  -t <repository_url>/r-qsar-plumber:v1 .
docker push <repository_url>/r-qsar-plumber:v1
cd ..
```

Once the image is pushed to `QSAR_REPO`, you can launch the Snowpark Container Services service.

#### Create the Service

**Run this step:** In a Snowsight SQL worksheet, create `QSAR_PLUMBER_SVC` on `QSAR_CPU_POOL` from the inline specification (matching `docker/plumber_spec.yaml`).

```sql
USE ROLE QSAR_ROLE;
USE SCHEMA QSAR_DB.PUBLIC;

CREATE SERVICE QSAR_PLUMBER_SVC
    IN COMPUTE POOL QSAR_CPU_POOL
    FROM SPECIFICATION $$
spec:
  containers:
    - name: qsar-r-plumber
      image: /qsar_db/public/qsar_repo/r-qsar-plumber:v1
      env:
        PORT: "5000"
      readinessProbe:
        port: 5000
        path: /health
      resources:
        requests:
          memory: 0.5Gi
          cpu: 0.5
        limits:
          memory: 13Gi
          cpu: 3
  endpoints:
    - name: api
      port: 5000
      public: true
    $$
    MIN_INSTANCES = 1
    MAX_INSTANCES = 1;
```

> **Note:** Baking the 4 MB `.rds` model and `kept_bits.csv` into the image is the simplest setup. If you later retrain and want to swap model versions without rebuilding the Docker image, Snowpark Container Services also supports mounting a versioned internal stage folder (such as `@QSAR_DB.PUBLIC.QSAR_STAGE/v180/`) at `/model` in the service specification, which masks the baked-in `/model` directory on container startup.

**Check:** Wait for the container status to report `READY` and retrieve the public `ingress_url`.

```sql
USE ROLE QSAR_ROLE;
SHOW SERVICE CONTAINERS IN SERVICE QSAR_DB.PUBLIC.QSAR_PLUMBER_SVC;
SHOW ENDPOINTS IN SERVICE QSAR_DB.PUBLIC.QSAR_PLUMBER_SVC;
```

**Check:** Inspect the container startup logs to confirm that the `ranger` model, feature list (`178` features for the bundled artifacts or `180` if you copied retrained artifacts), and `rcdk` JVM loaded cleanly.

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
SELECT SYSTEM$GET_SERVICE_LOGS('QSAR_DB.PUBLIC.QSAR_PLUMBER_SVC', 0, 'qsar-r-plumber', 20);
```

**Expected output:** Review the expected log output below (no action required):

```text
Loading model artifacts...
  ranger model: 500 trees, 178 features
  training fingerprints: 2751 compounds
Warming up rcdk JVM...
  rcdk JVM ready
Plumber API ready — listening on port 5000
```

With the service running and its public ingress URL available, verify external HTTPS access with the smoke test script.

#### Call the Endpoint

Public Snowpark Container Services endpoints require Snowflake authentication. For programmatic clients, generate a PAT in Snowsight under your user profile scoped to `QSAR_ROLE`, and pass it in the `Authorization` header using the exact `Snowflake Token` format shown below (sending `Bearer <your-PAT>` redirects to the browser login page instead):

```text
Authorization: Snowflake Token="<your-PAT>"
```

`/predict` expects a JSON payload of rows formatted as `{"data": [[row_index, smiles]]}`. Sending an unindexed body such as `{"smiles": "..."}` returns `{"data": []}` with HTTP 200.

**Run this step:** Export your `ingress_url` and PAT in the terminal and run `scripts/test_endpoint.py`.

```bash
export QSAR_ENDPOINT="<ingress_url from SHOW ENDPOINTS>"
export SNOWFLAKE_PAT="<your-PAT>"
python scripts/test_endpoint.py
```

**Check:** Review the expected terminal output below. When serving the bundled `docker/` model, the five test rows return:

```text
health: 200 {"status":"ok","trees":500,"features":178}

compound      pIC50  class        q05   q95
letrozole      7.89  Active      5.79  9.22
anastrozole    8.64  Active      7.03 10.00
exemestane     7.00  Active      5.42  7.82
ethanol        5.11  Inactive    4.22  6.92
invalid           -  Invalid SMILES: not_a_smiles     -     -
```

Letrozole (`N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1`) returns `7.89` (`Active`, quantiles `5.79` to `9.22`, corresponding to an approximate `IC50` of `12.9 nM`, compared with its selected measured `pIC50` of `9.15` in `CHEMBL1978_COMPOUNDS`) and exemestane returns `7.00` (if you instead promoted a model trained on Notebook 01's row order, letrozole returns `8.26` and exemestane returns `6.21`). In either case, all four valid molecules return numeric predictions and `not_a_smiles` returns an explicit CDK validation error.

Now that `QSAR_PLUMBER_SVC` is running, you can connect external MCP clients to `/mcp` using the same ingress URL and PAT, then create the shared SQL functions and batch-score the cohort.

### 2.2. Connect AI Assistants

Alongside `/predict` and `/sf/*`, `QSAR_PLUMBER_SVC` exposes a standalone MCP server at `/mcp` over JSON-RPC 2.0 so AI assistants (such as Cortex Code or Claude Desktop) can invoke R model tools directly from natural-language prompts.

#### Inspect the MCP Tools

The `/mcp` route exposes six tools backed by the running R container:

| Tool | Purpose | Example Prompt |
|---|---|---|
| `predict_pic50` | Predict `pIC50`, activity class (`>= 6.5`), uncalibrated 5th to 95th quantiles, and approximate `IC50` in `nM` for a SMILES string | "Predict the aromatase pIC50 for letrozole: `N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1`" |
| `validate_smiles` | Validate a SMILES string with the CDK parser and return heavy-atom count | "Is `c1ccccc1` a valid SMILES?" |
| `get_dataset_stats` | Summarize total compounds (`2,751`), active/inactive counts, and split sizes | "How many compounds are in the training data, and how many are active?" |
| `get_model_info` | Return estimator metadata (`500` trees, kept bits, held-out `test_r2`, and `test_rmse`) | "What model is this and how well does it do on the test set?" |
| `get_feature_importance` | Return the top `N` ECFP4 fingerprint bits ranked by regression impurity importance | "Which fingerprint bits matter most?" |
| `get_ro5_stats` | Report Lipinski Rule-of-Five compliance by activity class and median property values | "How do Active and Inactive compounds compare on Lipinski's Rule of Five?" |

Because MCP returns structured tool data directly from the R service, the AI client reports exact model and dataset values rather than guessing descriptors or inventing potency numbers. Next, register the `/mcp` endpoint in your client configuration.

#### Register the Client

Add the `qsar-aromatase` server entry to `~/.snowflake/cortex/mcp.json` (or your MCP client's configuration file), replacing `<your-ingress-url>` with the host from `SHOW ENDPOINTS IN SERVICE QSAR_DB.PUBLIC.QSAR_PLUMBER_SVC` and `<your-PAT>` with a PAT restricted to `QSAR_ROLE`:

```json
{
  "mcpServers": {
    "qsar-aromatase": {
      "transport": "http",
      "url": "https://<your-ingress-url>/mcp",
      "headers": {
        "Authorization": "Snowflake Token=\"<your-PAT>\""
      }
    }
  }
}
```

Once the server configuration is saved, you can reconnect your MCP client and invoke the R tools directly from chat.

#### Running the MCP Tool

Reconnect the server (`cortex mcp reconnect qsar-aromatase` in Cortex Code, confirming 6 tools load) and submit the following prompt to your AI assistant:

```text
Predict the aromatase activity of letrozole, SMILES N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1
```

**Expected output:** Review the expected `predict_pic50` tool output below (from the bundled model; a model trained on Notebook 01's row order returns `8.26`):

```text
SMILES: N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1
pIC50:  7.89  (Active)
90% CI: [5.79, 9.22]
IC50 ~  12.9 nM
```

See `docs/mcp-walkthrough.md` in the companion repository for additional client examples and an optional Snowflake Native App packaging pattern (`native_app/`). Next, expose `QSAR_PLUMBER_SVC` through shared SQL functions and batch-score the `2,751` curated compounds.

### 2.3. Score Compounds

While `/mcp` serves interactive AI clients, Snowflake SQL service functions let notebooks, SQL queries, and Cortex Agents call the same R container inside Snowflake and batch-score the entire `CHEMBL1978_COMPOUNDS` cohort.

#### Create SQL Functions

Review the `PREDICT_PIC50` declaration from **sql/functions.sql** below (no action required) to see how a Snowflake service function binds SQL calls to `/sf/predict` on `QSAR_PLUMBER_SVC`:

```sql
CREATE OR REPLACE FUNCTION PREDICT_PIC50(smiles VARCHAR)
  RETURNS VARIANT STRICT SERVICE = QSAR_PLUMBER_SVC
  ENDPOINT = api MAX_BATCH_ROWS = 50 AS '/sf/predict';
```

**Run this step:** Open `sql/functions.sql` in a Snowsight SQL worksheet and run the entire script under `QSAR_ROLE`. It creates four R-backed service functions (`PREDICT_PIC50`, `ECFP4`, `SIMILAR_COMPOUNDS`, and `EXPLAIN_PREDICTION`) plus an RDKit Python user-defined function (`RO5`, pinned to `rdkit==2025.09.3` via Snowflake's PyPI artifact repository).

**Check:** Run the query below in Snowsight to verify that `PREDICT_PIC50` and `EXPLAIN_PREDICTION` return letrozole's predicted `pIC50`, quantile interval, and top ECFP4 bit explanation from the R container service.

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
SELECT
    PREDICT_PIC50('N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1'):pIC50::FLOAT             AS PIC50,
    PREDICT_PIC50('N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1'):activity::STRING          AS CLASS,
    PREDICT_PIC50('N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1'):q05::FLOAT                AS Q05,
    PREDICT_PIC50('N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1'):q95::FLOAT                AS Q95,
    EXPLAIN_PREDICTION('N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1', 3):top_features[0]:bit::STRING      AS TOP_FEATURE,
    EXPLAIN_PREDICTION('N#Cc1ccc(cc1)C(n1cncn1)c1ccc(C#N)cc1', 3):top_features[0]:fragment::STRING AS FRAGMENT;
```

**Expected output:** Review the expected query output below when serving the bundled model (no action required):

```text
PIC50  CLASS   Q05   Q95   TOP_FEATURE  FRAGMENT
-----  ------  ----  ----  -----------  --------
 7.89  Active  5.79  9.22  bit_319      [N]C=[N]
```

With the shared SQL functions verified, run Notebook 02 to batch-score all `2,751` molecules.

#### Run Scoring Notebook

**Run this step:** Execute `02_score_compounds.ipynb` in Snowsight to score all `2,751` compounds in `CHEMBL1978_COMPOUNDS` using the SQL functions, populate `CHEMBL1978_PREDICTIONS`, `CHEMBL1978_FINGERPRINTS`, and `CHEMBL1978_DESCRIPTORS`, and write `dashboard_predictions.csv` to `@QSAR_STAGE`.

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
EXECUTE NOTEBOOK PROJECT QSAR_DB.PUBLIC.QSAR_NOTEBOOKS
    MAIN_FILE = '02_score_compounds.ipynb'
    COMPUTE_POOL = 'QSAR_ST_POOL'
    QUERY_WAREHOUSE = 'QSAR_WH'
    RUNTIME = 'V2-CPU-PY3.12'
    EXTERNAL_ACCESS_INTEGRATIONS = (QSAR_NB_EAI);
```

**Check:** Run the verification query below in Snowsight to confirm that all `2,751` compounds scored with zero null predictions and `2,652` Lipinski Rule-of-Five passes.

```sql
SELECT
    COUNT(*) AS SCORED,
    COUNT_IF(PRED_PIC50 IS NULL) AS FAILED,
    ROUND(SQRT(AVG(SQUARE(ERROR))), 3) AS RMSE_ALL,
    (SELECT COUNT(*) FROM QSAR_DB.PUBLIC.CHEMBL1978_FINGERPRINTS) AS FINGERPRINTS,
    (SELECT COUNT_IF(RO5_PASS) FROM QSAR_DB.PUBLIC.CHEMBL1978_DESCRIPTORS) AS RO5_PASS
FROM QSAR_DB.PUBLIC.CHEMBL1978_PREDICTIONS;
```

**Expected output:** Review the expected query output below (no action required; `RMSE_ALL` combines training and test rows across all `2,751` molecules and is not a held-out test metric):

```text
SCORED  FAILED  RMSE_ALL  FINGERPRINTS  RO5_PASS
------  ------  --------  ------------  --------
  2751       0     0.469          2751      2652
```

Now that `CHEMBL1978_PREDICTIONS`, `CHEMBL1978_FINGERPRINTS`, and `CHEMBL1978_DESCRIPTORS` are populated, you can stage the remaining dashboard files and deploy `QSAR_AROMATASE_APP` so bench scientists can explore the results interactively.

## 3. Explore Results

The Streamlit app (`QSAR_AROMATASE_APP`) gives lab colleagues a browser interface where they can explore the curated and scored ChEMBL cohort first and then submit single or batch SMILES strings on demand without running R scripts locally.

### 3.1. Stage Dashboard Files

Notebooks 01 and 02 already exported `dashboard_eda.csv`, `dashboard_ro5.csv`, and `dashboard_predictions.csv` to `@QSAR_STAGE`. Upload the remaining model artifacts so the Dashboard and About pages can display feature importances and held-out training metrics alongside the scored predictions.

**Run this step:** From your local terminal, upload `top_features.csv` and `training_metrics.json` to `@QSAR_DB.PUBLIC.QSAR_STAGE`.

```bash
cp docker/top_features_rcdk.csv /tmp/top_features.csv
snow sql -q "PUT file:///tmp/top_features.csv @QSAR_DB.PUBLIC.QSAR_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
snow sql -q "PUT file://docker/training_metrics.json @QSAR_DB.PUBLIC.QSAR_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
```

> **Note:** Remember that a stage is a static file handoff, not an automatic refresh pipeline. Whenever you retrain and promote a new R model, re-run Notebook 02 and re-upload `top_features.csv` and `training_metrics.json` so the dashboard summaries match the live model. If you skipped both notebooks and served the bundled model, you can generate the stage CSVs from your laptop with `scripts/generate_dashboard_data.py` as documented in `README.md`.

With `@QSAR_STAGE` populated, review how the Streamlit application connects stage summaries and live R predictions.

### 3.2. Review the App

> **Note:** The Streamlit application files in `streamlit/` are already included in the cloned repository. Review how the app separates prepared stage summaries from live R predictions before deploying it.

The `streamlit/` directory contains a multipage app designed to run in Streamlit in Snowflake on the container runtime:

- **Dashboard** (`streamlit/pages/dashboard.py`) reads prepared stage summaries (`dashboard_eda.csv`, `dashboard_ro5.csv`, `dashboard_predictions.csv`, `top_features.csv`, and `training_metrics.json`) to display class balance, Lipinski Rule-of-Five compliance, and model evaluation metrics.
- **Single Prediction** (`streamlit/pages/single_prediction.py`) sends a SMILES string (or one of five preset molecules: letrozole, anastrozole, exemestane, aspirin, or caffeine) to the R service's `/predict` endpoint, renders the 2D structure with RDKit, displays predicted `pIC50` and model quantiles, and logs the call to `QSAR_PREDICTIONS_LOG`.
- **Batch Prediction** (`streamlit/pages/batch_prediction.py`) scores multiple SMILES strings side by side in a table and downloadable CSV.
- **About** (`streamlit/pages/about.py`) documents the biological target (`CYP19A1` / `CHEMBL1978`), dataset curation, ECFP4 features, `ranger` estimator, and Snowpark Container Services deployment so scientists can inspect model provenance before trusting a score.
- **Ask an Agent** (`streamlit/pages/ask_agent.py`) connects to `QSAR_DB.PUBLIC.AROMATASE_AGENT` (created in the next section) for conversational Q&A and candidate triage inside the app.

Review the request call in **streamlit/_shared.py** below (no action required) to see how Python forwards SMILES strings to the R service over internal Snowpark Container Services DNS and unpacks the response without reimplementing the model in Python:

```python
resp = requests.post(
    get_predict_url(),
    headers=headers,
    json={"data": [[0, smiles]]},
    timeout=60,
)
resp.raise_for_status()
rows = resp.json().get("data", [])
if not rows:
    st.error("Service returned no results.")
    return None
_, pic50, activity, ci_lo, ci_hi = rows[0]
```

When running in Snowflake, `streamlit/_shared.py` discovers the service's internal DNS name automatically via `SHOW SERVICES`, so no hardcoded URL is needed. Next, deploy the Streamlit application.

### 3.3. Deploy the App

Review the runtime configuration in **streamlit/snowflake.yml** below (no action required) to see how the app specifies the container runtime, `QSAR_ST_POOL`, and `QSAR_APP_EAI`:

```yaml
    runtime_name: SYSTEM$ST_CONTAINER_RUNTIME_PY3_11
    compute_pool: QSAR_ST_POOL
    external_access_integrations:
      - QSAR_APP_EAI
```

**Run this step:** From the `streamlit/` directory in your terminal, deploy the app to Snowflake using the Snowflake CLI.

```bash
cd streamlit
snow streamlit deploy --replace
cd ..
```

**Check:** Open the URL printed by `snow streamlit deploy` (the first load takes one to two minutes while container dependencies install) and verify each page:

1. **Dashboard:** Inspect the measured activity distribution and class balance (`2,751` compounds, `1,061` active vs `1,690` inactive), Lipinski Rule-of-Five descriptor compliance (`MW <= 500 Da`, `LogP <= 5`, `HBD <= 5`, `HBA <= 10`), and the random forest's evaluation metrics, residual distribution, and top ECFP4 fingerprint bits ranked by regression impurity importance.

![Dataset Overview section on the Dashboard showing 2,751 compounds, 1,061 active, pIC50 distribution, and activity class breakdown](assets/dataset-overview-local-preview.png)

![Lipinski Rule of Five section on the Dashboard showing median physicochemical descriptors and compliance by activity class](assets/rule-of-five-local-preview.png)

![Model Performance and Feature Importance sections on the Dashboard showing R2, RMSE, predicted-versus-actual scatter, residual distribution, and top ECFP4 bits](assets/model-performance-local-preview.png)

2. **Single Prediction:** Select an example molecule such as **letrozole** or **aspirin** (or paste a SMILES string) and click **Predict pIC50**. The first image below shows letrozole (`CHEMBL1444`) scored at `7.89` (`Active`, uncalibrated quantiles `5.79` to `9.22`), followed by aspirin scored at `5.21` (`Inactive`, uncalibrated quantiles `4.26` to `6.92`).

![Local preview of a bundled-model letrozole pIC50 prediction, molecular structure and uncalibrated quantiles](assets/single-prediction-local-preview.png)

![Single Prediction view showing aspirin at predicted pIC50 5.21 with its 2D structure and uncalibrated quantiles](assets/app-single.png)

3. **Batch Prediction:** Submit multiple SMILES strings at once to compare predicted `pIC50`, activity labels, and quantile ranges in a single table. Below are the five-compound batch run and a two-compound run comparing aspirin (`5.21`) and caffeine (`5.96`).

![Local preview of five batch predictions from bundled-model examples](assets/batch-prediction-local-preview.png)

![Batch Prediction view comparing aspirin and caffeine](assets/app-batch.png)

4. **About:** Review the target biology (`CYP19A1` / `CHEMBL1978`), dataset summary, 1,024-bit ECFP4 fingerprint encoding, `ranger` quantile forest parameters, and Snowpark Container Services architecture on the About page.

![About page showing target, dataset, fingerprint, and model details](assets/app-about.png)

> **Note:** On Single Prediction, optional PubChem compound-name and fallback-image lookups are unchecked by default because enabling them sends a SMILES-derived InChIKey (and potentially the SMILES string) outside Snowflake. Keep that option off when evaluating proprietary structures.

With the Streamlit app running, you can now deploy the Cortex Agent that powers conversational research Q&A and multi-compound triage.

## 4. Research Q&A + Candidate Triage

> **Note:** This section builds on the Snowflake tables created by **both** Notebook 01 (`CHEMBL1978_RAW_ACTIVITIES`, `CHEMBL1978_COMPOUNDS`, `CHEMBL1978_ASSAYS`, and `CHEMBL1978_DOCUMENTS`) and Notebook 02 (`CHEMBL1978_PREDICTIONS`, `CHEMBL1978_FINGERPRINTS`, and `CHEMBL1978_DESCRIPTORS`), plus `sql/functions.sql`. Generating dashboard CSVs from a laptop alone does not create these tables.

When a model score raises follow-up questions such as "How many compounds in the cohort were measured active?", "What assay conditions were used to measure letrozole (`CHEMBL1444`)?", or "Rank letrozole, caffeine, and aspirin for review", an in-platform Cortex Agent (`AROMATASE_AGENT`) can route each question to the right evidence source rather than mixing predictions with measurements.

### 4.1. Create Agent Tools

`sql/agent.sql` builds three governed capabilities that complement the R-backed SQL functions:

1. **Measured Cohort Analytics (`AROMATASE_SV`):** Uses [Apache Ossie](https://github.com/apache/ossie) (`version: 0.1.1`, stored in `agent/aromatase_sv_ossie.yaml`) and Snowflake's built-in `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML` loader to create a Snowflake Semantic View over `CHEMBL1978_COMPOUNDS`, `CHEMBL1978_PREDICTIONS`, `CHEMBL1978_DESCRIPTORS`, `CHEMBL1978_ASSAYS`, `CHEMBL1978_DOCUMENTS`, `CHEMBL1978_FINGERPRINTS`, and `QSAR_PREDICTIONS_LOG`. Defining `AROMATASE_SV` as an open Apache Ossie specification lets Cortex Analyst answer measured active/inactive counts and potency statistics with deterministic SQL instead of estimating them from model calls.
2. **Assay and Literature Context (`ASSAY_SEARCH`):** Creates a Cortex Search service indexing assay descriptions and linked publication abstracts so the agent can retrieve experimental conditions and cite specific `ASSAY_CHEMBL_ID` and `DOCUMENT_CHEMBL_ID` identifiers (for example, showing that letrozole `CHEMBL1444` appears in cell-based assay `CHEMBL988317` as well as fluorimetric enzyme assays `CHEMBL1828368` and `CHEMBL1958525`).
3. **Candidate Triage (`TRIAGE_COMPOUNDS`):** Creates a stored procedure that accepts up to 20 newline-separated SMILES strings, combines each molecule's predicted `pIC50`, Tanimoto similarity to the nearest measured compound (`SIMILAR_COMPOUNDS`), and Lipinski Rule-of-Five compliance (`RO5`), and returns a ranked review table with an explicit rationale per row (flagging low similarity as uncertain extrapolation).

Review the Apache Ossie semantic-view creation and verification query excerpt from **sql/agent.sql** below (no action required) to see how `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML` registers `AROMATASE_SV` and how measured cohort counts are queried separately from `PREDICT_PIC50`:

```sql
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML('QSAR_DB.PUBLIC', $$
version: 0.1.1
semantic_model:
  - name: AROMATASE_SV
...
$$);

SELECT * FROM SEMANTIC_VIEW(QSAR_DB.PUBLIC.AROMATASE_SV
  METRICS compound_count, active_count);
```

**Run this step:** Open `sql/agent.sql` in a Snowsight SQL worksheet and execute it under `QSAR_ROLE` to create `AROMATASE_SV`, `ASSAY_SEARCH`, and `TRIAGE_COMPOUNDS`.

With the semantic view, search index, and triage procedure ready, deploy the Cortex Agent.

### 4.2. Deploy the Agent

**Run this step:** From the repository root in your terminal, run `scripts/deploy_agent.py` to create `QSAR_DB.PUBLIC.AROMATASE_AGENT` from `agent/aromatase_agent.yaml` and register it with Snowflake Intelligence (pass `--connection <your_connection>` with a connection name from `~/.snowflake/config.toml`, or omit `--connection` to use your `default_connection_name`).

```bash
python scripts/deploy_agent.py --connection <your_connection>
```

**Check:** Reload the Streamlit app tab in your browser so the **Ask an Agent** page appears in the sidebar, and ask: "How many measured aromatase compounds are active and inactive?" Cortex Analyst queries `AROMATASE_SV` and returns `1,061` measured active and `1,690` measured inactive compounds out of `2,751` total.

The screenshot below shows the **Ask an Agent** page answering the measured active and inactive compound count question.

![Ask an Agent page showing AROMATASE_AGENT answering the measured active and inactive compound count question](assets/agent-answer-local-preview.png)

You can also test candidate triage by asking the agent to rank letrozole (`7.89 Active`, similarity `1.00` to `CHEMBL1444`, passes Rule of Five), caffeine (`5.96 Inactive`, similarity `0.24`, flagged for low similarity), and aspirin (`5.21 Inactive`, similarity `0.35`, flagged for low similarity). Next, run the 15-case evaluation suite to measure the agent's routing and answer quality.

### 4.3. Evaluate the Agent

To evaluate `AROMATASE_AGENT` systematically, the repository provides 15 benchmark questions in `agent/eval_questions.sql` and an evaluation configuration in `agent/eval_config.yaml` (note that the expected prediction numbers in `agent/eval_questions.sql` match the bundled model, so adjust them if you trained on Notebook 01's row order).

**Run this step:** As `ACCOUNTADMIN` in Snowsight, grant `QSAR_ROLE` the Cortex Agent database role and `EXECUTE TASK` privilege required by `EXECUTE_AI_EVALUATION`.

```sql
USE ROLE ACCOUNTADMIN;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE QSAR_ROLE;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE QSAR_ROLE;
```

**Run this step:** Run `agent/eval_questions.sql` in a Snowsight worksheet to populate `AGENT_EVAL_QUESTIONS`, then upload `agent/eval_config.yaml` to `@QSAR_DB.PUBLIC.QSAR_STAGE` from your terminal.

```bash
snow sql -q "PUT file://agent/eval_config.yaml @QSAR_DB.PUBLIC.QSAR_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
```

**Run this step:** Start the evaluation run and poll its status from your Snowsight worksheet.

```sql
USE ROLE QSAR_ROLE;
USE WAREHOUSE QSAR_WH;
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'aromatase-guide-eval'),
  '@QSAR_DB.PUBLIC.QSAR_STAGE/eval_config.yaml');
CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', 'aromatase-guide-eval'),
  '@QSAR_DB.PUBLIC.QSAR_STAGE/eval_config.yaml');
```

**Check:** Once `STATUS` reports `COMPLETED`, query the evaluation metrics in SQL (for repeat runs on the same dataset, remove the `dataset` block from `eval_config.yaml` and pick a new `run_name`).

```sql
SELECT
    METRIC_NAME,
    COUNT(*) AS SCORED,
    ROUND(AVG(EVAL_AGG_SCORE), 3) AS MEAN_SCORE
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
  'QSAR_DB', 'PUBLIC', 'AROMATASE_AGENT', 'CORTEX AGENT', 'aromatase-guide-eval'))
WHERE METRIC_NAME IS NOT NULL
GROUP BY METRIC_NAME
ORDER BY METRIC_NAME;
```

**Expected output:** Review the expected summary output below from a completed 15-case evaluation run (no action required; these scores measure agent tool routing and response fidelity rather than the chemical accuracy of the underlying QSAR forest):

```text
METRIC_NAME              SCORED  MEAN_SCORE
-----------------------  ------  ----------
answer_correctness           15       0.956
logical_consistency          15       0.956
tool_selection_accuracy      15       0.967
```

Before sharing the app, MCP server, or agent with other scientists, review the statistical, operational, and governance boundaries of this system.

## Review Model Limitations

A demo only needs to succeed once, whereas a system that other scientists depend on must disclose its statistical limitations, protect sensitive chemical structures, and stay observable over time.

### Scientific and Statistical Limits

Disclose these modeling caveats wherever predictions are displayed or shared:

- **Paired model and feature contract:** The `docker/train_rcdk.R` script splits the dataset 80/20 before running `nearZeroVar()` on training molecules only (retaining `180` bits on `data/chembl1978_cleaned.csv` with held-out `test_r2: 0.6843` and `test_rmse: 0.7721`). The pre-bundled `docker/` model was trained with `nearZeroVar()` before the split (`178` bits, `test_r2: 0.6855`, `test_rmse: 0.7708`). Never mix a `.rds` model file from one run with the `kept_bits.csv` list from another.
- **Single row-order-dependent split:** The 80/20 split is drawn by row position with a fixed seed (`42`). The same `2,751` compounds ordered by Notebook 01 produce `test_r2: 0.6537` and `test_rmse: 0.7949`. A single random split does not validate generalization to new chemical scaffolds; use scaffold splitting and cross-validation for release-grade evaluation.
- **Reported R2 is squared correlation:** `test_r2` is computed as `cor(pred, y)^2`, not the conventional coefficient of determination `1 - SSE/SST`.
- **Uncalibrated model quantiles:** The 5th to 95th percentile range from the quantile forest (labeled `90% CI` in the API response) reflects empirical tree spread and has not been calibrated for statistical coverage on held-out molecules.
- **No formal applicability domain gate:** Out-of-domain molecules such as ethanol receive a numeric `pIC50` prediction (`5.21`) rather than being rejected. Nearest-measured-compound Tanimoto similarity in `SIMILAR_COMPOUNDS` and `TRIAGE_COMPOUNDS` is a review heuristic, not a validated applicability-domain boundary.
- **Held-out misses on steroidal inhibitors:** Steroids make up `682` of the `2,751` compounds (`31%` active vs `39%` overall). Exemestane (`CHEMBL1200374`, measured `pIC50` `7.82`) lands in the held-out test split when trained on Notebook 01's output and is predicted at `6.21` (`Inactive`), whereas the bundled split includes exemestane in training and predicts `7.00`. Always cross-check predictions against measured ChEMBL records.

Alongside these statistical boundaries, apply five operational and governance checks before inviting broader use.

### Governance and Release Checks

Shipping AI in a regulated drug discovery environment requires addressing procurement and platform constraints, keeping proprietary chemistry inside governed boundaries, and planning for ongoing operations and cost. Use these five checks as a repeatable blueprint to move from a teaching prototype to a production system that real scientists can depend on daily:

1. **Data and Reproducibility:** Version the governed enterprise tables, the ChEMBL snapshot, curation rules (such as highest-`pIC50` deduplication), activity cutoff (`6.5`), and assay/document provenance so every stage from preprocessing to scoring can be reproduced and audited later.
2. **Science and Validation:** Freeze the ordered feature bit list (`kept_bits.csv`), calibrate uncertainty intervals, and evaluate on untouched chemical scaffolds rather than relying on a single row-order-dependent split.
3. **Artifact and Architectural Tradeoffs:** Pin R package repositories, container digests, and model files together, and regenerate stage CSVs (`dashboard_predictions.csv`, `top_features.csv`, `training_metrics.json`) whenever the model changes. Rather than rewriting the R model in Python or building an R Shiny frontend from scratch, containerizing R Plumber behind a Python Streamlit UI and an MCP endpoint preserves exact `rcdk` and `ranger` parity while meeting enterprise platform constraints (and if per-consumer isolation is needed across accounts, `native_app/` provides a Snowflake Native App packaging path).
4. **Access, Guardrails, and Private Chemistry:** Keep external PubChem lookups opt-in (off by default) and enforce network rules so proprietary chemical structures stay inside your enterprise data platform and private or managed models; cap batch and triage inputs (such as 20 SMILES per `TRIAGE_COMPOUNDS` call); and note that `QSAR_PREDICTIONS_LOG.USER_NAME` in Streamlit in Snowflake records the service identity rather than the individual viewer unless caller identity is captured explicitly.
5. **Ownership, Monitoring, and Cost Control:** Assign owners to monitor container readiness, API latency, and model or pipeline drift against new wet-lab assays (`/health` confirms container liveness, not chemical validity), and control compute spend as usage grows by right-sizing compute pools (`CPU_X64_S` and `CPU_X64_XS`), configuring auto-suspend (`AUTO_SUSPEND_SECS = 3600`), and tracking warehouse and Cortex Search credit consumption.

Once you finish exploring the application and its evaluation checks, tear down the Snowflake resources to stop compute pool billing.

## Clean Up

Compute pools bill while they have active nodes. Run the statements below to remove all objects created in this guide.

**Run this step:** First remove `AROMATASE_AGENT` from Snowflake Intelligence and drop the agent, search service, and evaluation objects.

```sql
USE ROLE QSAR_ROLE;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  DROP AGENT QSAR_DB.PUBLIC.AROMATASE_AGENT;
DROP AGENT IF EXISTS QSAR_DB.PUBLIC.AROMATASE_AGENT;
DROP CORTEX SEARCH SERVICE IF EXISTS QSAR_DB.PUBLIC.ASSAY_SEARCH;
DROP DATASET IF EXISTS QSAR_DB.PUBLIC.AROMATASE_EVAL_DATASET;
DROP TABLE IF EXISTS QSAR_DB.PUBLIC.AGENT_EVAL_QUESTIONS;
```

**Run this step:** Drop the Streamlit app, the R Plumber service, the notebook project, the compute pools, the integrations, the database, the warehouse, and `QSAR_ROLE`.

```sql
USE ROLE QSAR_ROLE;
DROP STREAMLIT IF EXISTS QSAR_DB.PUBLIC.QSAR_AROMATASE_APP;
DROP SERVICE IF EXISTS QSAR_DB.PUBLIC.QSAR_PLUMBER_SVC;
DROP NOTEBOOK PROJECT IF EXISTS QSAR_DB.PUBLIC.QSAR_NOTEBOOKS;
DROP STAGE IF EXISTS QSAR_DB.PUBLIC.NB_PROJECT_STAGE;

USE ROLE ACCOUNTADMIN;
DROP COMPUTE POOL IF EXISTS QSAR_CPU_POOL;
DROP COMPUTE POOL IF EXISTS QSAR_ST_POOL;
DROP INTEGRATION IF EXISTS QSAR_APP_EAI;
DROP INTEGRATION IF EXISTS QSAR_NB_EAI;
DROP DATABASE IF EXISTS QSAR_DB;
DROP WAREHOUSE IF EXISTS QSAR_WH;
DROP ROLE IF EXISTS QSAR_ROLE;
```

If you ran a notebook interactively in Snowsight Workspaces, stop its notebook service before dropping `QSAR_ST_POOL`. Also revoke any PAT you created for this tutorial under your user profile in Snowsight.

With your environment cleaned up, review the key takeaways and reference materials below.

## Conclusion And Resources

Congratulations! You've successfully taken an R-based drug discovery model from exploratory lab code to a governed, containerized application on Snowflake, combining a reproducible R pipeline (`rcdk` ECFP4 fingerprints, `ranger` quantile random forest, and R Plumber on Snowpark Container Services) with Python data curation, a Streamlit frontend, a six-tool MCP server, and a Cortex Agent so bench scientists and AI assistants can query interpretable predictions without touching code.

### What You Learned
- How to structure an R machine learning pipeline into deterministic, testable stages (data preprocessing, molecular feature engineering, model training, and scoring) against governed enterprise tables rather than local CSVs
- How to combine R and Python harmoniously so R remains first-class for cheminformatics and modeling while Python and Streamlit provide an intuitive web interface
- How to containerize an R model, its pinned dependencies, and its ordered feature bit list on Snowpark Container Services and authenticate external requests with a PAT
- How to surface the same containerized R pipeline through SQL service functions, a multipage Streamlit app, a conversational MCP endpoint, and a Cortex Agent that separates measured cohort data, retrieved assay literature, and model predictions
- How to apply a repeatable production blueprint for regulated domains: keeping proprietary chemistry in-house, monitoring model and pipeline health, controlling compute cost, and disclosing statistical limitations so R pipelines remain reproducible, auditable, and trusted

Next, explore the companion source code, Snowflake documentation, and published aromatase QSAR literature below to build on this workflow.

### Related Resources

**Project and Biological Data**
- [Companion GitHub Repository: bioinformatics/r-python-drug-discovery](https://github.com/sfc-gh-cnantasenamat/bioinformatics/tree/main/r-python-drug-discovery)
- [ChEMBL Bioactivity Database (Target CHEMBL1978)](https://www.ebi.ac.uk/chembl/)
- [RCSB Protein Data Bank Structure 3EQM: Human Placental Aromatase](https://www.rcsb.org/structure/3EQM)

**Snowflake Documentation**
- [Snowpark Container Services Overview](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Access a Public Endpoint Programmatically](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/tutorials/advanced/tutorial-8-access-public-endpoint-programmatically)
- [Programmatic Access Tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- [Streamlit in Snowflake Documentation](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Analyst Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- [Create Semantics Anywhere with Apache Ossie (Incubating)](https://www.snowflake.com/en/blog/engineering/dbt-snowflake-semantic-views-apache-ossie/)
- [Apache Ossie Repository](https://github.com/apache/ossie)
- [Cortex Search Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)

**Research Papers**
- [Schaduangrat N, Lampa S, Simeon S, Gleeson MP, Spjuth O, Nantasenamat C. Towards reproducible computational drug discovery. J Cheminform (2020)](https://link.springer.com/article/10.1186/s13321-020-0408-x)
- [Shoombuatong W, Schaduangrat N, Nantasenamat C. Towards understanding aromatase inhibitory activity via QSAR modeling. EXCLI J (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6123608/)
- [Simeon S, et al. Origin of aromatase inhibitory activity via proteochemometric modeling. PeerJ (2016)](https://peerj.com/articles/1979/)
- [Shoombuatong W, et al. Prediction of aromatase inhibitory activity using the efficient linear method (ELM). EXCLI J (2015)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4614109/)
- [Worachartcheewan A, et al. Large-scale QSAR study of aromatase inhibitors using SMILES-based descriptors. Chemom Intell Lab Syst (2014)](https://www.sciencedirect.com/science/article/abs/pii/S0169743914001646)

author: Gilberto Hernandez, Snowflake CoCo
id: get-started-with-remote-development-snowflake-vscode-extension
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/snowflake-ml, snowflake-site:taxonomy/product/platform
language: en
summary: Connect VS Code or Cursor to a Snowflake-managed dev environment over Remote-SSH, ingest ~1B rows of Tasty Bytes data, enrich with Marketplace weather, and train + log an XGBoost sales-forecasting model – all on Snowflake compute, from your local editor.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-remote-development-vscode-extension

# Getting Started with Remote Development in the Snowflake VS Code Extension

<!-- ------------------------ -->
## Overview

Duration: 3

Every ML engineer eventually hits the same wall: your data is in Snowflake, your editor is VS Code (or Cursor), and between the two you've got a local Python environment you're constantly tending – the right Snowpark version, the right numpy, the right XGBoost – plus a laptop that can't fit the tables you actually want to analyze. Half the time you give up and open Snowsight in a browser tab, leaving your editor, your extensions, and CoCo behind.

**Remote Development** for the Snowflake Extension for Visual Studio Code closes that gap. It gives you a Snowflake-backed development environment you connect to over Remote-SSH, straight from VS Code or Cursor. There are no SSH keys to manage, no VMs to provision, and no local dependencies to babysit. The environment is a Snowflake Notebook service running on Snowpark Container Services, preloaded with Python, Jupyter, XGBoost, scikit-learn, and the Snowflake libraries, reachable from your editor as if it were localhost.

In this Quickstart, we'll build an end-to-end ML workflow against Snowflake compute, entirely from a local editor. You're an ML engineer on the Tasty Bytes team. Tasty Bytes runs food trucks in cities across the globe, and you've been asked to forecast daily sales per truck location. Weather clearly moves food-truck sales – so we'll enrich internal orders with a Marketplace weather share, feature-engineer with help from CoCo, train an XGBoost regressor, and log it to the Snowflake Model Registry. All from VS Code, without moving 1B rows of orders to your laptop.

Let's get started!

### What You'll Learn

- How to create a Snowflake-backed remote development environment and connect to it over Remote-SSH from VS Code or Cursor.
- How to load ~1B rows of public Tasty Bytes CSV data into Snowflake tables in a couple of minutes on a Large warehouse.
- How to enrich internal data with a Snowflake Marketplace weather dataset – the real DS/ML pattern of "internal facts joined to external reference data."
- How to run a Jupyter notebook that mixes Python and SQL cells using the Snowflake Kernel (Python + SQL) – the same kernel that powers Notebooks in Workspaces.
- How to use **Cortex Code (CoCo)** inside the remote SSH session to accelerate feature engineering and analysis.
- How to run a plain Python script (`.py` file) against the remote environment, beyond notebook cells.
- How to train an XGBoost sales-forecasting model and log it to the **Snowflake Model Registry**.
- How to clone a private GitHub repository into persistent storage using a **Snowflake secret** as the Git credential helper – so your personal access token never touches disk.
- How to suspend and resume the remote environment while preserving cloned repos, installed packages, and trained artifacts.

### What You'll Need

- A **Snowflake account** with a role that can create and run notebook services (`USAGE` on a compute pool that allows the `NOTEBOOK` workload type; permission to use external access integrations and secrets). If you don't have one, [sign up for a free 30-day trial](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides). Select **Enterprise** edition.
- The account parameter `ENABLE_NOTEBOOK_SERVICE_REMOTE_VS_CODE_ACCESS` set to `TRUE`. It's on by default; an account admin can confirm.
- Access to the **Snowflake Marketplace** so you can acquire the free **Weather Source LLC: frostbyte** share.
- **VS Code** or **Cursor** installed locally.
- The Microsoft **Remote - SSH** extension: [`ms-vscode-remote.remote-ssh`](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh).
- The **Snowflake Extension for Visual Studio Code**, version **1.39 or later** (persistent storage and Git require v1.39+): [Marketplace listing](https://marketplace.visualstudio.com/items?itemName=snowflake.snowflake-vsc).
- Local `nc` (netcat) on your `PATH`. Preinstalled on macOS and most Linux distributions. On Windows you'll need to install a `netcat`-compatible executable and add it to `PATH`.
- A **GitHub account**. You'll create a small private repo in step 8 to practice the Snowflake-secret-based Git flow.
- Comfort with Python, Jupyter notebooks, Git, and basic SQL. Familiarity with a gradient-boosted tree model (XGBoost or similar) is helpful for step 7.

### What You'll Build

By the end of this guide, you'll have:

- A running Snowflake **remote development environment**, reachable from VS Code or Cursor over Remote-SSH.
- **~1B rows** of Tasty Bytes orders and their supporting dimensions ingested into a Snowflake database.
- A **Marketplace weather share** acquired and joined into a daily-per-location feature table.
- A trained **XGBoost sales-forecasting model** logged to the **Snowflake Model Registry**.
- A **private Git repo** cloned into `/mnt/pd0` (persistent storage) using a **Snowflake secret** as the credential helper – no PATs on disk.
- An **actual vs. predicted sales chart** for a held-out week, rendered inline in the remote notebook.

<!-- ------------------------ -->
## Set up your Snowflake account

Duration: 6

Let's set up everything you'll need on the Snowflake side: a warehouse for the bulk load, the Tasty Bytes database and schemas, an external stage against the public S3 bucket, all the raw tables, a compute pool for the notebook service, an external access integration for outbound GitHub and PyPI, and a Snowflake Workspace to mount into the remote environment.

We'll do it all with one copy-paste SQL block, run in a Snowsight worksheet.

### Step 2a – Run the setup script

Open Snowsight, create a new SQL worksheet, and paste in the contents of **setup.sql** from the [companion repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-remote-development-vscode-extension/blob/main/setup.sql). Then run the whole worksheet.

Here's what the script does:

- Creates a **Large** warehouse (`tb_de_wh`). Large lets the `COPY INTO` finish in ~1-2 minutes across all raw tables. It gets sized back down to XSmall at the end.
- Creates the `tb_101` database plus the `raw_pos`, `raw_customer`, `harmonized`, `analytics`, and `ml` schemas.
- Creates a CSV file format and an **external stage** against `s3://sfquickstarts/frostbyte_tastybytes/` – the canonical public Tasty Bytes bucket.
- Creates all eight raw tables: `country`, `franchise`, `location`, `menu`, `truck`, `order_header`, `order_detail`, and `customer_loyalty`.
- Creates the `harmonized.orders_v` and `analytics.orders_v` views that stitch orders, trucks, menus, franchises, locations, and customers into one queryable surface.
- Runs `COPY INTO` for every raw table. When this completes you'll have close to a billion rows across the fact tables.
- Creates a **compute pool** (`tb_remote_dev_pool`, `CPU_X64_S`) and allows the `NOTEBOOK` workload type on it.
- Creates a **network rule** (`egress_github_pypi`) and an **external access integration** (`tb_remote_dev_eai`) so the remote notebook service can reach `github.com` and `pypi.org` for cloning and `pip install`.
- Creates a **Snowflake Workspace** (`tb_forecast_ws`) – we'll mount this into the remote environment in step 4.
- Confirms `ENABLE_NOTEBOOK_SERVICE_REMOTE_VS_CODE_ACCESS` is on.

You should see a final `note` row that reads: `Remote-dev quickstart setup complete...`.

> **Note:** the Tasty Bytes S3 bucket is public, so it does NOT need to be in the external access integration. `COPY INTO` runs on Snowflake compute against the stage – the EAI governs outbound traffic from the notebook container, not stage access.

### Step 2b – Acquire the weather data from the Marketplace

Weather is one of the strongest predictors of food-truck sales. We'll enrich Tasty Bytes orders with the free **Weather Source LLC: frostbyte** share from the Snowflake Marketplace.

1. In Snowsight, go to **Data Products** → **Marketplace**.
2. Search for **Weather Source LLC: frostbyte**.
3. Click **Get**, then confirm. The share lands in your account as a database (typically `FROSTBYTE_WEATHERSOURCE`).

Once the share is available, you can query it directly:

```sql
SHOW DATABASES LIKE 'FROSTBYTE_WEATHERSOURCE%';

SELECT date_valid_std, city_name, avg_temperature_air_2m_f, tot_precipitation_in
FROM frostbyte_weathersource.onpoint_id.history_day
LIMIT 10;
```

You should see a mix of weather observations across US cities and dates. That's the data we'll join to daily orders in step 6.

Great job – the Snowflake side is ready. Now let's get your editor set up.

<!-- ------------------------ -->
## Install the extension and sign in

Duration: 3

Now we'll install the Snowflake Extension for VS Code (or Cursor) plus the companion **Remote - SSH** extension, and sign in to your Snowflake account.

### VS Code

1. Open VS Code.
2. In the Extensions view, search for **Snowflake** and install the extension published by **Snowflake Inc.** – make sure the version is **1.39.0 or later**.
3. In the Extensions view again, search for **Remote - SSH** and install `ms-vscode-remote.remote-ssh`.
4. Open the Snowflake extension from the Activity Bar. Sign in to your Snowflake account.

### Cursor

The Snowflake extension works identically in Cursor – Cursor is built on the same VS Code extension model.

1. Open Cursor.
2. Open the Extensions view and search for **Snowflake**. Install v1.39.0 or later.
3. Also install `ms-vscode-remote.remote-ssh` from the same view.
4. Sign in from the Snowflake extension.

The rest of this guide uses VS Code screenshots, but the steps are the same in Cursor unless called out.

> **Note:** if you had an older Snowflake extension installed, reload your editor after upgrading. The **Remote Environments** panel that we'll use next only appears in v1.38+.

<!-- ------------------------ -->
## Create your remote environment

Duration: 5

We're ready to spin up the remote environment. From the Snowflake extension in your local editor, we'll create a notebook service running on the compute pool we provisioned earlier, and enable persistent storage so cloned Git repos and installed packages survive suspend/resume.

1. In the Snowflake extension sidebar, expand the **Remote Environments** panel.
2. Click **Create Remote Development Environment**.
3. Fill in the form:
   - **Service name:** `tb_forecast_env` (or any Snowflake identifier; avoid collisions with existing SSH aliases in your `~/.ssh/config`).
   - **Workspaces:** select `tb_forecast_ws`.
   - **External access integrations:** select `tb_remote_dev_eai`.
   - **Compute pool:** select `tb_remote_dev_pool`.
   - **Service settings** → expand this section:
     - **Compute type:** CPU
     - **Enable persistent storage:** **check this box**.
4. Click **Create**.

> **Important:** **Enable persistent storage** can only be set at create time – you cannot add it to an existing service. If you skip it now, you'll have to delete this service and create a new one. Persistent storage mounts SPCS block storage at `/mnt/pd0` in the remote container. Cloned repos and pip installs live there across suspend and resume.

The service enters `PENDING` status while Snowflake provisions the container. This takes a few minutes. The panel refreshes every 30 seconds; you can also refresh manually. When the status flips to `RUNNING`, you're ready to connect.

<!-- ------------------------ -->
## Connect over SSH and open a notebook

Duration: 8

Let's connect over SSH. Click one button and you're in, without SSH keys to generate or ports to configure.

1. In the **Remote Environments** panel, find your `tb_forecast_env` service.
2. Click **Setup SSH** on the service.
3. When prompted, select the `tb_forecast_ws` workspace to mount into the remote environment. Press Enter.
4. A new editor window opens, connected over SSH to the remote container at `/root`.

Behind the scenes, the extension started a local proxy on `127.0.0.1` that forwards SSH traffic to Snowflake over a secure WebSocket, wrote a `Host <service-name>` entry to your `~/.ssh/config`, installed the required extensions on the remote host, and opened the folder. You didn't have to do any of it.

> **Note (first-connect):** the very first connection installs the Python, Jupyter, and Snowflake extensions on the remote host. This can take a couple of minutes. If the Snowflake Kernel option doesn't appear when you try to run a cell, wait for the installs to finish and reload the remote window (`Developer: Reload Window` from the Command Palette).

> **Note (extension icons):** if the Snowflake extension's left-nav icons look blank in the remote window, the extension is installed – its icon assets failed to load. Reload the remote window and they'll come back.

### Clone the companion repo into persistent storage

Let's pull the notebook and helper Python modules we'll be using. In the remote window, open a terminal (**Terminal** → **New Terminal**) and clone the repo into `/mnt/pd0`:

```bash
cd /mnt/pd0
git clone https://github.com/Snowflake-Labs/sfguide-getting-started-with-remote-development-vscode-extension.git
cd sfguide-getting-started-with-remote-development-vscode-extension
```

Add the folder to your workspace: **File → Add Folder to Workspace...** and pick `/mnt/pd0/sfguide-getting-started-with-remote-development-vscode-extension`. You should see `README.md`, `setup.sql`, `cleanup.sql`, `forecast.ipynb`, and `train.py` in the Explorer.

### Open the notebook

Open **forecast.ipynb**. In the notebook's action bar, click **Snowflake: Start Notebook Kernel**, then select **Snowflake Kernel (Python + SQL)** from the kernel picker.

This is the same kernel that powers Snowflake Notebooks in Snowsight Workspaces. Python and SQL cells run side by side without switching kernels – Python cells run in the container's Python interpreter, and SQL cells run against your Snowflake account.

Run the first SQL cell to confirm the raw tables loaded:

```sql
SELECT 'order_header' AS tbl, COUNT(*) AS rows FROM tb_101.raw_pos.order_header
UNION ALL SELECT 'order_detail', COUNT(*) FROM tb_101.raw_pos.order_detail
UNION ALL SELECT 'location',     COUNT(*) FROM tb_101.raw_pos.location
UNION ALL SELECT 'truck',        COUNT(*) FROM tb_101.raw_pos.truck
UNION ALL SELECT 'menu',         COUNT(*) FROM tb_101.raw_pos.menu
UNION ALL SELECT 'customer_loyalty', COUNT(*) FROM tb_101.raw_customer.customer_loyalty
ORDER BY 2 DESC;
```

You should see `order_detail` at the top with the largest row count – hundreds of millions of line items. Together with `order_header` this is close to a billion rows. **This is the "compute goes to data" moment**: you're querying that volume from your local editor, and the query runs on Snowflake compute. Moving those rows to your laptop wouldn't be feasible; you don't have to.

### A quick word on `.py` files

The remote environment isn't limited to notebooks – you can open and run plain Python files against the same remote interpreter. Open `train.py`, click the ▶ **Run Python File** button in the top-right (or right-click → **Run Python File in Terminal**), and it executes against the remote environment. We'll use `train.py` in step 7.

Great job. You're now running Snowflake-backed compute from your local editor. Let's put it to work.

<!-- ------------------------ -->
## Enrich with Marketplace weather and feature-engineer with CoCo

Duration: 8

We have 1B rows of raw orders on one side and a weather share on the other. Let's turn them into a modeling-ready feature table – and let CoCo do most of the writing.

### Aggregate orders to daily-per-location grain

Run the next cell in the notebook:

```sql
CREATE OR REPLACE TABLE tb_101.ml.daily_sales AS
SELECT
    DATE(order_ts)             AS date,
    location_id,
    ANY_VALUE(location_city)   AS city,
    ANY_VALUE(location_region) AS region,
    ANY_VALUE(country)         AS country,
    SUM(price)                 AS daily_sales,
    COUNT(DISTINCT order_id)   AS order_count
FROM tb_101.harmonized.orders_v
GROUP BY 1, 2;

SELECT COUNT(*) AS rows_in_daily_sales FROM tb_101.ml.daily_sales;
```

Here's what the code does:

- Reads from `harmonized.orders_v`, the view that joins orders, line items, trucks, menus, and locations.
- Groups by `(date, location_id)` to get one row per truck location per day.
- Materializes the result to `tb_101.ml.daily_sales` – this is now a small table (tens of thousands of rows) that we can work with in memory.

### Join the Marketplace weather

Now let's bring in weather. Run the next cell:

```sql
CREATE OR REPLACE TABLE tb_101.ml.daily_sales_weather AS
SELECT
    ds.date,
    ds.location_id,
    ds.city,
    ds.daily_sales,
    ds.order_count,
    w.avg_temperature_air_2m_f      AS temp_f,
    (w.avg_temperature_air_2m_f - 32.0) * 5.0/9.0 AS temp_c,
    w.tot_precipitation_in * 25.4   AS precip_mm,
    w.avg_wind_speed_100m_mph * 1.60934 AS wind_kph
FROM tb_101.ml.daily_sales ds
JOIN frostbyte_weathersource.onpoint_id.history_day w
  ON w.date_valid_std = ds.date
 AND UPPER(w.city_name) = UPPER(ds.city)
WHERE ds.daily_sales IS NOT NULL;

SELECT COUNT(*) AS joined_rows FROM tb_101.ml.daily_sales_weather;
```

Here's what the code does:

- Joins `daily_sales` to the Weather Source share on `date` + `city`.
- Converts imperial units to metric so the features are easier to reason about.
- Drops rows where the join failed or sales are null.
- Materializes `tb_101.ml.daily_sales_weather` – this is the base for feature engineering.

> **Note:** if the weather share landed under a different database name in your account, run `SHOW DATABASES LIKE 'FROSTBYTE_WEATHERSOURCE%';` first and adjust the FROM clause accordingly.

### Feature-engineer with CoCo

Now for the fun part. Open the **CoCo** panel in the remote window from the Activity Bar. You're going to prompt CoCo to add calendar, lag, and rolling features to the DataFrame – the exact patterns you'd use for any time-series forecasting problem.

Try prompts like:

- *"Add day-of-week, month, and is_weekend features to a daily sales DataFrame."*
- *"Add lag-1 and lag-7 daily-sales features per location_id."*
- *"Add a 7-day rolling mean of precip_mm per location_id."*

CoCo running inside the remote SSH session has full access to the Snowflake compute and data plane. It writes cells, you accept or edit, and everything executes on Snowflake. In practice, CoCo produces something close to the two cells below: one that defines the transforms, one that applies them.

The first cell defines three small pandas transforms:

```python
import pandas as pd

def add_calendar_features(df, date_col='date'):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['day_of_week'] = df[date_col].dt.dayofweek
    df['month'] = df[date_col].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    return df

def add_lag_features(df, group_cols, target_col='daily_sales', lags=(1, 7)):
    df = df.copy().sort_values(group_cols + ['date'])
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df.groupby(group_cols)[target_col].shift(lag)
    return df

def add_rolling_precip(df, group_cols, precip_col='precip_mm', window=7):
    df = df.copy().sort_values(group_cols + ['date'])
    df[f'{precip_col}_roll_{window}'] = (
        df.groupby(group_cols)[precip_col]
        .rolling(window=window, min_periods=1)
        .mean()
        .reset_index(level=list(range(len(group_cols))), drop=True)
    )
    return df
```

The second cell loads the joined table and chains the transforms via `.pipe()`:

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
raw = session.table('tb_101.ml.daily_sales_weather').to_pandas()
raw.columns = [c.lower() for c in raw.columns]

features_df = (
    raw
    .pipe(add_calendar_features)
    .pipe(add_rolling_precip, group_cols=['location_id'])
    .pipe(add_lag_features, group_cols=['location_id'])
    .dropna()
    .reset_index(drop=True)
)
features_df.head()
```

Here's what the code does:

- Gets the active Snowflake session; the remote container is already authenticated.
- Materializes the joined table to a pandas DataFrame in the container.
- Chains the three transforms with `.pipe()`: calendar features first, then a 7-day rolling precipitation feature, then lag-1 and lag-7 sales features.
- Drops the initial rows containing NaN lag values.

### Land the feature table back in Snowflake

Push the DataFrame back to Snowflake so `train.py` can consume it:

```python
session.write_pandas(
    features_df,
    table_name='FEATURE_TABLE',
    database='TB_101',
    schema='ML',
    auto_create_table=True,
    overwrite=True,
)
session.table('tb_101.ml.feature_table').count()
```

Now the feature table lives in Snowflake, ready for training.

<!-- ------------------------ -->
## Train an XGBoost model and log it to the Model Registry

Duration: 6

This is the step where we ship a model beyond a notebook. We'll train an XGBoost regressor on the feature table, evaluate it on the last week of data, chart actual vs predicted, and log the model to the **Snowflake Model Registry** – where it becomes discoverable by other teammates and downstream jobs.

### Train from a `.py` file

`train.py` in the repo is a plain Python script – no notebook required. Let's run it against the remote environment. In the notebook, execute this cell:

```python
!python train.py \
    --source-table tb_101.ml.feature_table \
    --database tb_101 \
    --schema ml \
    --model-name tb_sales_forecaster \
    --version v1
```

You can also run it directly in the remote terminal (`python train.py --source-table ...`). Either way, it executes on the Snowflake-hosted container against the active Snowflake session – same interpreter, same environment.

Here's what `train.py` does:

- Loads the feature table into a pandas DataFrame using `session.table(...).to_pandas()`.
- Does a **time-based** train/test split – the last 7 days are held out. Never a random split for forecasting.
- Fits an `XGBRegressor` with sensible defaults (400 trees, depth 6, learning rate 0.05).
- Evaluates on the holdout: **MAPE** and **RMSE**.
- Logs the fitted model to the Snowflake Model Registry via `Registry.log_model()`, along with a sample input, the version, and a comment carrying the holdout metrics.

You should see output ending in something like:

```
Holdout MAPE: 0.14x  |  RMSE: xxxxx
Logging model to registry: tb_101.ml.tb_sales_forecaster (v1) ...
Done. The model is now discoverable from the Model Registry.
```

Your model is now live in the Model Registry. You can list it from any session:

```sql
SHOW MODELS IN SCHEMA tb_101.ml;
```

> **Great job – you shipped a model.** From here, other teammates can retrieve it, run predictions, or promote it to a downstream inference job – all without ever seeing your notebook.

### Chart actual vs predicted

Let's visualize the holdout. Run the final cell of the notebook:

```python
import pandas as pd
import matplotlib.pyplot as plt
from snowflake.ml.registry import Registry

registry = Registry(session=session, database_name='TB_101', schema_name='ML')
model_ref = registry.get_model('tb_sales_forecaster').version('v1')

holdout = features_df[features_df['date'] > features_df['date'].max() - pd.Timedelta(days=7)].copy()
one_loc = holdout[holdout['location_id'] == holdout['location_id'].value_counts().idxmax()].copy()

FEATURE_COLS = [
    'day_of_week', 'month', 'is_weekend',
    'temp_c', 'precip_mm', 'wind_kph',
    'precip_mm_roll_7', 'daily_sales_lag_1', 'daily_sales_lag_7',
]
one_loc['predicted'] = model_ref.run(one_loc[FEATURE_COLS])

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(one_loc['date'], one_loc['daily_sales'], marker='o', label='Actual')
ax.plot(one_loc['date'], one_loc['predicted'], marker='x', label='Predicted')
ax.set_title(f"Location {int(one_loc['location_id'].iloc[0])} – actual vs predicted (holdout week)")
ax.set_ylabel('Daily sales (USD)')
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

Here's what the code does:

- Retrieves the model from the registry – we don't reload the Python object, we ask Snowflake for it.
- Picks the single location with the most rows in the holdout.
- Runs inference through the registered model via `model_ref.run(...)`.
- Charts actual vs predicted sales for that location across the holdout week.

You should see the two lines tracking each other reasonably closely. The fit has room to tune, and you've built a working forecaster end to end in a fraction of an hour.

<!-- ------------------------ -->
## Clone a private repo using a Snowflake secret

Duration: 5

Real DS/ML work involves private repos. In this step you'll clone one into `/mnt/pd0` without ever writing your personal access token (PAT) to disk. The mechanism: mount a **Snowflake secret** into the container, and point `git` at it via a custom credential helper.

This is the officially recommended path – Snowflake's internal security review specifically recommends **against** storing a PAT in plaintext on `/mnt/pd0`, because that file would persist across suspend/resume alongside your repo.

### Create a private repo and a PAT

1. Create a small **private** GitHub repository. An empty one is fine. Call it `tb-forecast-private` or anything you like.
2. Generate a **classic personal access token** at [https://github.com/settings/tokens](https://github.com/settings/tokens). Give it the `repo` scope so it can read and push to private repositories. Copy the token – you'll only see it once.

### Create a Snowflake secret

Back in Snowsight, run this in a SQL worksheet, substituting your GitHub username and the PAT you generated a moment ago:

```sql
CREATE OR REPLACE SECRET tb_101.ml.git_pat
  TYPE = PASSWORD
  USERNAME = '<your_github_username>'
  PASSWORD = '<your_github_pat>';
```

### Attach the secret to the remote service

Back in VS Code, open the **Info** or **Manage** action on your remote service in the Remote Environments panel and add `tb_101.ml.git_pat` under Secrets. The secret will be mounted into the container at a path under `/secrets/...`.

> **Note:** if the extension version you're on requires a service recreate to attach a secret, delete `tb_forecast_env` and create it again with the secret attached at create time. Persistent storage will be lost – but nothing in this guide depends on data currently in `/mnt/pd0`.

Reconnect over SSH (Setup SSH again), then list `/secrets/` in the remote terminal to find the exact mount path for your secret:

```bash
ls /secrets/
```

You should see a directory named after the secret. The username and password each land as a file inside – e.g. `/secrets/<prefix>/<mount_name>/git_pat/username` and `/secrets/<prefix>/<mount_name>/git_pat/password`.

### Clone the private repo

Clone your private repo into `/mnt/pd0`, passing a credential helper that reads from the mount path:

```bash
cd /mnt/pd0
git -c credential.helper='!f() {
    echo "username=$(cat /secrets/<prefix>/<mount_name>/git_pat/username)";
    echo "password=$(cat /secrets/<prefix>/<mount_name>/git_pat/password)";
  }; f' \
  clone https://github.com/<your_github_username>/tb-forecast-private.git
```

Replace `<prefix>/<mount_name>` with what you saw under `/secrets/`. That single command clones the private repo using the mounted secret – the PAT is never written to a file, never in your shell history, never in the repo config.

### Persist the credential helper for future pulls and pushes

You want future `git pull` and `git push` calls to reuse the same credential helper. Set it as **repository-local** config so it survives suspend/resume alongside the repo itself:

```bash
cd /mnt/pd0/tb-forecast-private
git config --local credential.helper \
  '!f() {
     echo "username=$(cat /secrets/<prefix>/<mount_name>/git_pat/username)";
     echo "password=$(cat /secrets/<prefix>/<mount_name>/git_pat/password)";
   }; f'
```

> **Important:** use `git config --local`, not `git config --global`. Global git config lives outside `/mnt/pd0` and is wiped when the service suspends. Repository-local config lives inside the cloned repo on the persistent drive, so it persists.

Try a `git pull` – it should authenticate silently against the mounted secret.

<!-- ------------------------ -->
## Suspend, resume, and confirm state persists

Duration: 4

Time to prove that persistent storage really persists. We'll suspend the service, resume it, reconnect, and confirm that the private repo, our pip installs, and the registered model all survive.

1. In the remote editor window, save any unsaved files. Then close the window.
2. In your local editor's Remote Environments panel, click **Stop Proxy** on `tb_forecast_env`.
3. Click **Stop** on the service. Status flips to `SUSPENDED`.

> **Callout:** always click **Stop Proxy** before closing the remote window. If you skip it, reconnecting later can open the remote window without prompting the workspace picker and error out. Stop Proxy first, then Setup SSH cleanly reconnects.

Take a break, grab a coffee, and come back later.

4. Back in the Remote Environments panel, click **Resume** on `tb_forecast_env`. Wait until status is `RUNNING`.
5. Click **Setup SSH**. Pick the same workspace as before. A new remote window opens.
6. In a terminal on the remote, run:

```bash
ls /mnt/pd0
ls /mnt/pd0/sfguide-getting-started-with-remote-development-vscode-extension
ls /mnt/pd0/tb-forecast-private
```

Everything is still there. Any additional packages you `pip install`ed are still installed. The registered model is still queryable from Snowsight or from a new notebook cell:

```sql
SHOW MODELS IN SCHEMA tb_101.ml;
```

Contrast this with the ephemeral filesystem: try `ls /root` – anything you wrote at `/root` is gone.

That's the persistent-storage story in one experiment. `/mnt/pd0` survives; `/root` doesn't.

<!-- ------------------------ -->
## Clean up

Duration: 2

When you're done, drop everything the guide created. Open a Snowsight worksheet and paste in the contents of **cleanup.sql** from the companion repo. That script:

- Drops the `tb_101` database (which cascades to every table, view, feature table, and model registry entry).
- Drops the compute pool and external access integration.
- Drops the Large warehouse.
- Drops the Snowflake Workspace.

Then, back in VS Code, in the Remote Environments panel: click **Stop Proxy** if it's active, click **Delete** on `tb_forecast_env`, and finally remove the `Host tb_forecast_env` entry from `~/.ssh/config` if the extension didn't. Optionally revoke the Weather Source share from **Data Products** → **Private Sharing** in Snowsight.

<!-- ------------------------ -->
## Conclusion and Resources

Duration: 1

Congratulations! You built and shipped an end-to-end ML workflow – data ingest, feature engineering, model training, and registry logging – entirely against Snowflake compute, from your local editor, without provisioning a VM, managing an SSH key, or moving a single row down to your laptop.

The value here compounds. The same remote environment that ran this notebook can host your team's other ML projects. The same Model Registry entry can be picked up by inference services, scheduled tasks, or downstream teammates. And the same editor you already work in – VS Code or Cursor – is now a first-class interface to Snowflake's compute plane.

### What You Learned

- How to create a Snowflake-backed remote development environment and connect over Remote-SSH from VS Code or Cursor.
- How to ingest ~1B rows of Tasty Bytes data from a public S3 stage into Snowflake in a couple of minutes on a Large warehouse.
- How to enrich internal data with a Marketplace weather share – internal facts + external reference data, the way real DS/ML work looks.
- How to use the **Snowflake Kernel (Python + SQL)** in a Jupyter notebook, with Python and SQL cells side by side.
- How to work with **CoCo** inside the remote SSH session to accelerate feature engineering.
- How to run plain `.py` files against the remote environment.
- How to train an **XGBoost** model and log it to the **Snowflake Model Registry**.
- How to clone a private Git repo using a **Snowflake secret** as the credential helper – no PATs on disk.
- How persistent storage at `/mnt/pd0` survives suspend and resume, while `/root` doesn't.

### Related Resources

- [Remote Development with the Snowflake Extension for Visual Studio Code](https://docs.snowflake.com/en/user-guide/vscode-ext-remote-development)
- [Snowflake Extension for Visual Studio Code](https://docs.snowflake.com/en/user-guide/vscode-ext)
- [Snowflake Notebooks (Container Runtime)](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-container-runtime)
- [Snowflake ML – Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Cortex Code (CoCo) in your code editor](https://docs.snowflake.com/en/user-guide/cortex-code)
- [Companion repo: sfguide-getting-started-with-remote-development-vscode-extension](https://github.com/Snowflake-Labs/sfguide-getting-started-with-remote-development-vscode-extension)
- [Weather Source LLC: frostbyte – Snowflake Marketplace](https://app.snowflake.com/marketplace)
- Related Quickstart: [Getting Started with CoCo in the Snowflake VS Code Extension](https://quickstarts.snowflake.com/guide/get-started-coco-vscode-extension/)

<!--
AUTHOR NOTES (remove before publish):

Hands-on validation items:
- Confirm the exact FROSTBYTE_WEATHERSOURCE share DB/schema/table names in your account. Adjust the join in step 6 if they differ.
- Confirm the weather join succeeds on TB city names – some may need a normalization / lookup table.
- Verify the CoCo panel opens cleanly on first-connect in the remote window (sign-in behavior, extension config). Update the step 6 opening prose if the UX differs.
- Verify the extension left-nav-icons issue still reproduces at draft time; if fixed, remove the note in step 5.
- Verify the reconnect-workspace-picker bug still reproduces; if fixed, remove the callout in step 9.
- Confirm secret-attach-to-existing-service UX; update step 8 wording (recreate vs. manage) accordingly.
- Pin a specific Container Runtime version in setup.sql or in step 4 once verified against the Model Registry API.
- Capture screenshots for assets/: (1) Remote Environments panel with a running service, (2) Setup SSH click, (3) Snowflake Kernel (Python + SQL) picker, (4) COPY INTO cell result, (5) CoCo panel in remote window, (6) Model Registry entry in Snowsight, (7) Actual-vs-predicted chart (end-state), (8) /secrets/ ls output.
- Placeholders in step 8 use <prefix>/<mount_name> – replace with the real prefix from your account when you validate.
-->

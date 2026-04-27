author: Marie Coolsaet
id: hpo-with-experiment-tracking
summary: Learn how to combine distributed hyperparameter optimization with experiment tracking in Snowflake to build scalable, reproducible ML workflows.
categories: snowflake-site:taxonomy/snowflake-feature/ai-ml,snowflake-site:taxonomy/snowflake-feature/snowflake-ml-functions,snowflake-site:taxonomy/snowflake-feature/snowpark-container-services
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Science, Machine Learning, Hyperparameter Optimization, Experiment Tracking, XGBoost, SPCS
language: en

# Distributed Hyperparameter Optimization with Experiment Tracking
<!-- ------------------------ -->
## Overview
This quickstart demonstrates how to combine two powerful Snowflake ML capabilities:

- **Distributed Hyperparameter Optimization (HPO)** – Run model tuning in parallel on Snowpark Container Runtime  
- **Experiment Tracking** – Automatically log parameters, metrics, and model artifacts for every run  

Together, these tools let you move from one-off experiments to scalable, reproducible ML workflows — all within Snowflake.

### Challenges Addressed
- Sequential hyperparameter tuning is slow  
- Manual experiment tracking is error-prone  
- Distributed infrastructure setup is complex  
- Reproducing past experiments requires detailed documentation

### Prerequisites
- A Snowflake account with a database and schema
- CREATE EXPERIMENT privilege on your schema
- Familiarity with Python and ML concepts

### What You'll Learn
- How to set up experiment tracking for ML runs
- How to run distributed HPO across multiple nodes
- How to log and compare experiment results
- How to view experiment history in Snowsight

### What You'll Need
- snowflake-ml-python >= 1.9.1
- Notebook configured for Container Runtime on SPCS (Compute Pool with instance type `CPU_X64_S`)

### What You'll Build
- A complete ML pipeline with distributed hyperparameter optimization
- An XGBoost classification model optimized for wine quality prediction
- A tracked experiment with logged parameters, metrics, and models

<button>[Download Notebook](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/hpo-with-experiment-tracking/assets/hpo_example.ipynb)</button>

<!-- ------------------------ -->
## Setup and Data

First, let's import the necessary libraries and set up our Snowflake session.

```python
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn import metrics
from xgboost import XGBClassifier

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
from snowflake.ml.experiment.experiment_tracking import ExperimentTracking
from snowflake.ml.modeling import tune
from snowflake.ml.modeling.tune.search import RandomSearch, BayesOpt
from snowflake.ml.data.data_connector import DataConnector
from snowflake.ml.runtime_cluster import scale_cluster

# Get active Snowflake session
session = get_active_session()
print(f"Connected to Snowflake: {session.get_current_database()}.{session.get_current_schema()}")

# Create dated experiment name for tracking runs over time
experiment_date = datetime.now().strftime("%Y%m%d")
experiment_name = f"Wine_Quality_Classification_{experiment_date}"
print(f"\nExperiment Name: {experiment_name}")
```

### Generate Wine Quality Classification Dataset

We'll create a synthetic dataset inspired by wine quality prediction. The goal is to classify wines as high quality (1) or standard quality (0) based on chemical properties.

```python
# Generate synthetic wine quality dataset
np.random.seed(42)
n_samples = 20000

# Feature generation with realistic correlations
data = {
    "FIXED_ACIDITY": np.random.normal(7.0, 1.5, n_samples),
    "VOLATILE_ACIDITY": np.random.gamma(2, 0.2, n_samples),
    "CITRIC_ACID": np.random.beta(2, 5, n_samples),
    "RESIDUAL_SUGAR": np.random.lognormal(1, 0.8, n_samples),
    "CHLORIDES": np.random.gamma(3, 0.02, n_samples),
    "FREE_SULFUR_DIOXIDE": np.random.normal(30, 15, n_samples),
    "TOTAL_SULFUR_DIOXIDE": np.random.normal(120, 40, n_samples),
    "DENSITY": np.random.normal(0.997, 0.003, n_samples),
    "PH": np.random.normal(3.2, 0.3, n_samples),
    "SULPHATES": np.random.gamma(4, 0.15, n_samples),
    "ALCOHOL": np.random.normal(10.5, 1.5, n_samples)
}

df = pd.DataFrame(data)

# Create quality target based on feature combinations
quality_score = (
    0.3 * (df["ALCOHOL"] - df["ALCOHOL"].mean()) / df["ALCOHOL"].std() +
    0.2 * (df["CITRIC_ACID"] - df["CITRIC_ACID"].mean()) / df["CITRIC_ACID"].std() -
    0.25 * (df["VOLATILE_ACIDITY"] - df["VOLATILE_ACIDITY"].mean()) / df["VOLATILE_ACIDITY"].std() +
    0.15 * (df["SULPHATES"] - df["SULPHATES"].mean()) / df["SULPHATES"].std() +
    np.random.normal(0, 0.3, n_samples)  # Add noise
)

# Binary classification: 1 = high quality, 0 = standard quality
df["QUALITY"] = (quality_score > quality_score.quantile(0.6)).astype(int)

print(f"Dataset shape: {df.shape}")
print(f"\nClass distribution:\n{df['QUALITY'].value_counts()}")
```

### Prepare Train/Validation/Test Splits

```python
# Separate features and target
X = df.drop('QUALITY', axis=1)
y = df['QUALITY']

# Create train/val/test splits
X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.18, random_state=42, stratify=y_temp)

# Scale features
scaler = StandardScaler()
X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
X_val_scaled = pd.DataFrame(scaler.transform(X_val), columns=X_val.columns)
X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

print(f"Training set: {X_train_scaled.shape[0]} samples")
print(f"Validation set: {X_val_scaled.shape[0]} samples")
print(f"Test set: {X_test_scaled.shape[0]} samples")
```

<!-- ------------------------ -->
## Baseline Model

Before running distributed HPO, let's train a baseline model and log it to Snowflake Experiment Tracking.

```python
# Initialize Experiment Tracking
exp = ExperimentTracking(session=session)
exp.set_experiment(experiment_name)

# Train baseline model
with exp.start_run(run_name="baseline_xgboost") as run:
    # Define baseline parameters
    baseline_params = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'gamma': 0.1,
        'min_child_weight': 8,
        'random_state': 42,
    }
    
    # Log parameters
    exp.log_params(baseline_params)
    
    # Train model
    baseline_model = XGBClassifier(**baseline_params)
    baseline_model.fit(X_train_scaled, y_train)
    
    # Evaluate on validation set
    y_val_pred = baseline_model.predict(X_val_scaled)
    y_val_proba = baseline_model.predict_proba(X_val_scaled)[:, 1]
    
    # Calculate metrics
    val_metrics = {
        'val_accuracy': metrics.accuracy_score(y_val, y_val_pred),
        'val_precision': metrics.precision_score(y_val, y_val_pred),
        'val_recall': metrics.recall_score(y_val, y_val_pred),
        'val_f1': metrics.f1_score(y_val, y_val_pred),
        'val_roc_auc': metrics.roc_auc_score(y_val, y_val_proba)
    }
    
    # Log metrics
    exp.log_metrics(val_metrics)
    
    print("Baseline Model Performance:")
    for metric, value in val_metrics.items():
        print(f"  {metric}: {value:.4f}")
```

<!-- ------------------------ -->
## Data Connectors

Convert pandas DataFrames to Snowflake DataConnectors for distributed processing.

```python
# Combine features and target for each split
train_df = pd.concat([X_train_scaled, y_train.reset_index(drop=True)], axis=1)
val_df = pd.concat([X_val_scaled, y_val.reset_index(drop=True)], axis=1)

# Create DataConnectors
dataset_map = {
    "train": DataConnector.from_dataframe(session.create_dataframe(train_df)),
    "val": DataConnector.from_dataframe(session.create_dataframe(val_df)),
}

print("Data connectors created successfully")
```

<!-- ------------------------ -->
## Training Function

The training function will be executed for each HPO trial. It integrates both HPO and Experiment Tracking.

```python
def train_function():
    """
    Training function executed for each HPO trial.
    Integrates with both TunerContext and ExperimentTracking.
    """    
    trial_session = Session.builder.getOrCreate()
    
    # Get tuner context
    tuner_context = tune.get_tuner_context()
    params = tuner_context.get_hyper_params()
    dm = tuner_context.get_dataset_map()
    
    # Initialize experiment tracking for this trial
    exp = ExperimentTracking(session=trial_session)
    exp.set_experiment(experiment_name)
    with exp.start_run():
        # Log hyperparameters
        exp.log_params(params)
        
        # Load data
        train_data = dm["train"].to_pandas()
        val_data = dm["val"].to_pandas()
        
        # Separate features and target
        X_train = train_data.drop('QUALITY', axis=1)
        y_train = train_data['QUALITY']
        X_val = val_data.drop('QUALITY', axis=1)
        y_val = val_data['QUALITY']
        
        # Train model with hyperparameters from HPO
        model = XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        # Evaluate on validation set
        y_val_pred = model.predict(X_val)
        y_val_proba = model.predict_proba(X_val)[:, 1]
        
        # Calculate validation metrics
        val_metrics = {
            'val_accuracy': metrics.accuracy_score(y_val, y_val_pred),
            'val_precision': metrics.precision_score(y_val, y_val_pred),
            'val_recall': metrics.recall_score(y_val, y_val_pred),
            'val_f1': metrics.f1_score(y_val, y_val_pred),
            'val_roc_auc': metrics.roc_auc_score(y_val, y_val_proba)
        }
      
        # Log metrics to experiment tracking
        exp.log_metrics(val_metrics)
        
        # Report to HPO framework (optimize on validation F1)
        tuner_context.report(metrics=val_metrics, model=model)
```

<!-- ------------------------ -->
## Configure the Search Space

Define the hyperparameter search space using Snowflake's sampling functions.

```python
# Define search space for XGBoost
search_space = {
    'n_estimators': tune.randint(50, 300),
    'max_depth': tune.randint(3, 15),
    'learning_rate': tune.loguniform(0.01, 0.3),
    'subsample': tune.uniform(0.5, 1.0),
    'colsample_bytree': tune.uniform(0.5, 1.0),
    'gamma': tune.uniform(0.0, 0.5),
    'min_child_weight': tune.randint(1, 10),
    'random_state': 42,
}

print("Search space defined:")
for param, space in search_space.items():
    print(f"  {param}: {space}")
```

<!-- ------------------------ -->
## Run Distributed HPO

Configure the tuner to maximize F1 score, run 50 trials with random search, and execute trials in parallel across available nodes.

### Monitor Node Activity with the Ray Dashboard

Use the output URL to access the dashboard and monitor your distributed HPO jobs:

```python
from snowflake.ml.runtime_cluster import get_ray_dashboard_url
get_ray_dashboard_url()
```

### Run HPO

```python
# Scale cluster for distributed processing
print("Scaling cluster for distributed HPO...")
scale_cluster(10)  # Scale up nodes

# Configure tuner
tuner_config = tune.TunerConfig(
    metric='val_f1',
    mode='max',
    search_alg=RandomSearch(),
    num_trials=50
)

# Create tuner
tuner = tune.Tuner(
    train_func=train_function,
    search_space=search_space,
    tuner_config=tuner_config
)

print("Starting distributed hyperparameter optimization...")

# Run HPO
try:
    results = tuner.run(dataset_map=dataset_map)
    print("\nHPO completed successfully")
except Exception as e:
    print(f"\nError during HPO: {e}")
    raise
finally:
    # Scale cluster back down
    scale_cluster(1)
    print("Cluster scaled back to 1 node")
```

**Note:** Remember to scale your cluster back down after HPO completes to avoid unnecessary compute costs.

<!-- ------------------------ -->
## Analyze Results

Let's examine the best model found during hyperparameter optimization.

```python
# Display all results
print("BEST MODEL FOUND")
print("="*60)

# Extract best hyperparameters
print(f"\nBest Parameters:")
best_model = results.best_model
params = best_model.get_xgb_params()
print(params)

# Compare with baseline
best_f1 = results.best_result['val_f1'][0]
baseline_f1 = val_metrics['val_f1']  # From baseline model
improvement = ((best_f1 - baseline_f1) / baseline_f1) * 100

print(f"\nPerformance Comparison:")
print(f"  Baseline F1: {baseline_f1:.4f}")
print(f"  Best HPO F1: {best_f1:.4f}")
print(f"  Improvement: {improvement:+.2f}%")

# Get test set f1 score
y_test_pred = best_model.predict(X_test_scaled)
test_f1 = metrics.f1_score(y_test, y_test_pred)
print(f"\n\nBest HPO Test Set F1: {test_f1:.4f}")

results.best_result
```

<!-- ------------------------ -->
## View in Snowsight

All experiment runs are now available in the Snowflake UI:

1. Navigate to **AI & ML → Experiments** in the left sidebar
2. Find the `Wine_Quality_Classification_YYYYMMDD` experiment (with today's date)
3. Compare runs, view metrics, and analyze results

The Snowsight UI provides:
- Side-by-side run comparisons
- Metric visualizations
- Parameter distributions
- Model artifacts and metadata

<!-- ------------------------ -->
## Conclusion & Next Steps

Congratulations! You've successfully built a distributed hyperparameter optimization pipeline with integrated experiment tracking in Snowflake.

### What We've Covered
- Setting up Snowflake Experiment Tracking for ML runs
- Creating a baseline model with logged parameters and metrics
- Defining a hyperparameter search space for XGBoost
- Running distributed HPO across multiple SPCS nodes
- Analyzing and comparing experiment results in Snowsight

### Next Steps

1. **Adjust the search space** - Modify hyperparameter ranges based on your problem domain and data size
2. **Increase trial count** - Scale to 100-200 trials for more thorough optimization
3. **Scale compute clusters** - Adjust `scale_cluster()` to increase or decrease parallelism
4. **Deploy the winning model** - Register to Snowflake Model Registry

### Related Resources
- [Blog post: Experiment Tracking with Distributed HPO in Snowflake](https://mariesoehlcoolsaet.medium.com/experiment-tracking-with-distributed-hpo-in-snowflake-cdf5ff41ba16)
- [Snowpark ML Overview](https://docs.snowflake.com/en/developer-guide/snowpark-ml/overview)
- [Experiment Tracking Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/experiments)
- [Parallel HPO Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/container-hpo)


author: Sheena Nasim 
id: ml-champion-challenger-model-deployment language: en 
summary: Learn how to implement an automated model retraining and deployment pipeline in Snowflake using the Champion-Challenger strategy with ML Registry, DAGs, and Tasks. 
categories: snowflake-site:taxonomy/product/ai 
environments: web status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues 
fork repo link: https://github.com/sheena-n/Snowflake-Champion-Challenger.git

# Automated Model Retraining & Deployment in Snowflake
<!-- ------------------------ -->

## Overview
Duration: 5

In the realm of production machine learning, maintaining model performance through automated retraining and seamless deployment is crucial. This guide explores a robust solution utilizing the **Champion-Challenger strategy**, implementing a comprehensive model deployment pipeline powered by the Snowflake ML Registry. The pipeline features automated retraining, evaluation, and promotion processes.

### Prerequisites
- Familiarity with machine learning concepts and the Champion-Challenger model strategy
- Basic understanding of Snowflake's ML capabilities and Model Registry
- Python programming experience with scikit-learn

### What You'll Learn
- How to generate a synthetic dataset for model training and evaluation
- Steps to train and register a Champion model in Snowflake ML Registry
- Process for training a Challenger model and comparing its performance against the Champion
- Automating the model training and promotion pipeline using Snowflake's DAGs and Tasks

### What You'll Need
- Access to a Snowflake account with appropriate permissions
- Python environment with necessary libraries (scikit-learn, Snowflake ML Registry)
- Snowflake Notebooks enabled in your account

### What You'll Build
- A fully automated model retraining and deployment pipeline in Snowflake implementing the Champion-Challenger strategy

<!-- ------------------------ -->

## Generate Dataset
Duration: 10

Create a synthetic credit approval dataset comprising 8,000 loan applications over 20 weeks (400 applications per week). Each application includes nine financial features:

- Applicant age
- Annual income
- Credit score
- Debt-to-income ratio
- Employment years
- Credit cards count
- Mortgage status
- Education score
- Location risk

The target variable indicates loan approval (approved/denied) based on weighted business logic combining creditworthiness factors. Concept drift is simulated through gradual changes in approval patterns over time, and seasonal effects reflect real-world lending cycles.

### Data Split Strategy

**Champion Model:**
- **Train:** 10 Weeks (week 0–9 → 4,000 samples) — Historical data
- **Test:** 2 Weeks (Week 10–12 → 1,200 samples)

**Challenger Model:**
- **Train:** 10 Weeks (week 3–12 → 4,000 samples) — More recent data
- **Test:** 3 Weeks (week 13–15 → 1,200 samples)

**Evaluation Data:** Weeks 16–19 (1,600 samples) — To compare Champion and Challenger performance.

<!-- ------------------------ -->

## Train a Champion Model
Duration: 15

Train an initial Champion model—a Random Forest classifier built with scikit-learn using the first 10 weeks of data. Finalize the model, push it into the Snowflake Model Registry, and establish the inference pipeline.

### Register Champion in Model Registry

# Register champion in model registry
sample_input = X_train.head(100)
model_name = "CREDIT_APPROVAL"

champion_ref = registry.log_model(
    model=champion_pipeline,
    model_name=model_name,
    sample_input_data=sample_input,
    target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
    comment=f"Champion model trained on weeks 0-9, AUC: {champion_auc:.2f}",
    metrics={
        "test_auc": champion_auc,
        "train_weeks": "0-9",
        "model_type": "champion",
        "training_samples": len(X_train)
    },
    task=type_hints.Task.TABULAR_BINARY_CLASSIFICATION
)### Set Model Alias

# Set the model alias as CHAMPION
champion_ref.set_alias("CHAMPION")### Set Live Version Tag

# Get the model from the registry
model = registry.get_model(model_name)

# Set Live version tag
model.set_tag("LIVE_VERSION", champion_ref.version_name)### Establish Inference Pipeline

The inference pipeline remains unchanged regardless of model updates, as all Champion model switching is managed internally within the Snowflake Model Registry:

# Get the live version of the model
live_version = model.get_tag("live_version")

# Run prediction function
remote_prediction = model.version(live_version).run(test_data, function_name="predict")<!-- ------------------------ -->

## Challenger Model Training
Duration: 10

Train a Challenger model—a Random Forest classifier using scikit-learn on the 3–12 recent weeks of data. Log this new iteration into the Snowflake Model Registry as the Challenger model.

### Register Challenger in Model Registry

# Register challenger in model registry
challenger_ref = registry.log_model(
    model=challenger_pipeline,
    model_name=model_name,
    sample_input_data=sample_input,
    target_platforms=["WAREHOUSE", "SNOWPARK_CONTAINER_SERVICES"],
    comment=f"Challenger model trained on weeks 3-12, AUC: {challenger_auc:.2f}",
    metrics={
        "test_auc": challenger_auc,
        "train_weeks": "3-12",
        "model_type": "challenger",
        "training_samples": len(X_train)
    },
    task=type_hints.Task.TABULAR_BINARY_CLASSIFICATION
)### Set Challenger Alias and Tag

# Set the model alias as CHALLENGER
challenger_ref.set_alias("CHALLENGER")

# Get the model from the registry
model = registry.get_model(model_name)

# Set Challenger version tag
model.set_tag("CHALLENGER_VERSION", challenger_ref.version_name)<!-- ------------------------ -->

## Model Performance Check & Swap
Duration: 10

Perform a basic performance check by comparing the AUC scores of the Champion and Challenger models on the evaluation holdout dataset. If the Challenger's AUC is higher, demote the Champion and promote the Challenger as the new Champion, marking it as Live.

### Performance Comparison Logic

if challenger_metrics['auc'] > champion_metrics['auc']:
    # Promote Challenger to Champion
    print(f"🎉 Challenger outperformed Champion!")
    print(f"📊 Champion AUC: {champion_metrics['auc']:.4f}")
    print(f"📊 Challenger AUC: {challenger_metrics['auc']:.4f}")
    
    # Update aliases and tags
    challenger_ref.set_alias("CHAMPION")
    model.set_tag("LIVE_VERSION", challenger_ref.version_name)
else:
    print(f"📝 Reason: Challenger performance not better than Champion")
    print(f"🏆 Current Champion Remains Active: {live_version}")<!-- ------------------------ -->

## Automating Model Training and Promotion
Duration: 15

To productionalize this workflow, automate the Challenger training and model promotion pipeline to run weekly (e.g., every Monday at 1 AM). Snowflake's DAGs (Directed Acyclic Graphs) and Tasks features allow scheduling these steps to execute in an orderly fashion.

### Define and Deploy the DAG

# Define the DAG - run every weekly Monday 1 AM
with DAG(dag_name, schedule=Cron("1 1 * * 1", "Asia/Singapore"), warehouse=warehouse_name) as dag:
    
    dag_task1 = DAGTask(
        "WEEKLY_RETRAINING", 
        definition="EXECUTE NOTEBOOK DEV_AUTOMATION_DEMO.CHAMPION_CHALLENGER.CC_3_CHALLENGER_TRAINING()", 
        warehouse=warehouse_name
    )
    dag_task2 = DAGTask(
        "AUTO_DEPLOY_BEST_MODEL", 
        definition="EXECUTE NOTEBOOK DEV_AUTOMATION_DEMO.CHAMPION_CHALLENGER.CC_4_SWAP_MODELS()", 
        warehouse=warehouse_name
    )
    
    # Define the dependencies between the tasks
    dag_task1 >> dag_task2  # dag_task1 is a predecessor of dag_task2

# Create the DAG in Snowflake
dag_op.deploy(dag, mode="orreplace")This automation ensures:
- Weekly retraining of the Challenger model with the latest data
- Automatic performance comparison between Champion and Challenger
- Seamless promotion of the best-performing model to production

<!-- ------------------------ -->

## Conclusion and Resources
Duration: 2

Congratulations! You have successfully implemented an automated model retraining and deployment pipeline in Snowflake using the Champion-Challenger strategy.

Snowflake simplifies model lifecycle management by leveraging its ML Registry to store and govern models. Furthermore, Snowflake DAGs and Tasks automate the entire model retraining and deployment strategies, ensuring a seamless MLOps workflow.

### What You Learned
- How to generate synthetic datasets with concept drift for model training
- Training and registering Champion models in Snowflake ML Registry
- Implementing the Challenger model training and evaluation process
- Automating model promotion using Snowflake DAGs and Tasks
- Best practices for production ML model lifecycle management

### Related Resources
- [Snowflake ML Registry Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Snowflake Tasks and DAGs Documentation](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Snowflake Notebooks Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Understanding Customer Reviews using Snowflake Cortex](https://quickstarts.snowflake.com/guide/understanding_customer_reviews_using_snowflake_cortex)
- [Getting Started with Snowflake Intelligence](https://quickstarts.snowflake.com/guide/getting_started_with_snowflake_intelligence)

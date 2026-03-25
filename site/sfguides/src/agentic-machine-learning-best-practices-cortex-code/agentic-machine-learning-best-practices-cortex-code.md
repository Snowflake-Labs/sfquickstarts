author: Snowflake
id: agentic-machine-learning-best-practices-cortex-code
language: en
summary: Learn best practices for building end-to-end ML pipelines with Cortex Code, Snowflake's AI coding agent, using natural language prompts — from feature engineering to model deployment and monitoring.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web
status: Published

# Agentic Machine Learning Best Practices with Cortex Code

Agents are redefining workflows everywhere. And getting started for ML has never been easier.

Traditionally, building ML models has been slow and manual, involving tedious troubleshooting cycles. Snowflake is now an agentic-first ML platform. With [**Cortex Code**](https://docs.snowflake.com/en/user-guide/cortex-code/overview), Snowflake's native AI coding agent, data science teams can develop production-ready ML pipelines using simple natural language prompts, from the CLI or Snowsight.

By automating everything from feature engineering to model training to deployment, you can experiment and iterate faster and focus on higher-impact initiatives for your business.

<!-- VIDEO PLACEHOLDER: Agentic ML overview video (Coco for ML video series) -->

## Get started with Cortex Code

- [Cortex Code enabled](https://docs.snowflake.com/en/user-guide/cortex-code/overview#enabling-cortex-code) with appropriate permissions on your account


### In Snowsight

Cortex Code is built directly into [Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight), Snowflake's web UI. No installation required — open a Workspace in Snowsight and start a Cortex Code conversation to generate fully functional ML pipelines that run directly inside a Snowflake Notebook.

### In CLI

To use Cortex Code from your terminal, VS Code, or Cursor, install the CLI:

```
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

For more details on setup, connections, supported models, or CLI reference, see the [Cortex Code CLI documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).

> **If you don't have Cortex Code** [start your 30-day Cortex Code CLI trial](https://signup.snowflake.com/cortex-code).

## Terminology

- **[Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/overview)** is Snowflake's AI-powered coding agent for building, debugging, and deploying ML pipelines through natural language conversations — available in the CLI and in Snowsight.
- **[Skills](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility)**: reusable instruction packs (playbooks) that guide Cortex Code through specific ML workflows (for example, feature engineering, model training, and deployment).
- **[Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs)**: Jupyter-based, container runtime environments purpose-built for large-scale AI/ML production workflows. In Snowsight, Cortex Code delivers verified ML solutions as fully functional pipelines that run directly inside a Notebook.
- **[Snowflake Feature Store](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview)**: a centralized repository for creating, storing, and serving ML features — enabling reuse across models and consistent training/serving definitions.
- **[Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)**: a governed catalog for logging, versioning, and managing trained models along with their metadata, metrics, and lineage.
- **[Model Monitor](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/model-monitor)**: a Snowflake-native service for tracking model performance in production, including data drift, prediction drift, and accuracy degradation over time.

## Best practices

> **Always ensure you're on the latest CLI version.** Run `cortex --version` and update with `cortex update` if needed.

### Communicate naturally

- Use plain language to describe what you want, not how to do it
- Iterate conversationally — just say what you'd like changed
- If you feel stuck, ask "What steps are available to me?"
- New skills are always being added. Ask "what skills are available?" to see the latest.
- Check if specialized skills should be loaded for ML workflows such as feature engineering, model training, or deployment

### Review before accepting

- Understand proposed changes before they're executed, especially DDL/DML operations and compute pool provisioning
- Verify file modifications — what will be created, edited, or deleted
- Use caution with production environments and destructive operations (DROP, DELETE, etc.)
- Ask for explanations if unsure: "Why are you doing this?" or "What will this change?"

### Work effectively

- Start small and test frequently — build one ML pipeline stage at a time
- Use `/plan` for complex tasks to see the full approach before starting
- Run Cortex Code in a VS Code/Cursor terminal to view generated notebooks and code side-by-side
- Write complex requirements in `.md` files and reference them in the conversation
- If you hit unexpected behavior, confirm you're on the latest CLI version (for example: run `cortex --version` and update with `cortex update` if needed)

### Security & governance

- Never commit secrets — keep credentials out of code and version control
- Review privilege grants and RBAC changes carefully
- Leverage built-in help — ask "How does this work?" or check Snowflake documentation

### Prompting best practices

Getting the most out of Cortex Code for ML comes down to how you structure your prompts. These patterns will help you get faster, higher-quality results across the full ML lifecycle.

#### 1. Front-load context, focus tasks on a goal

Give Cortex Code comprehensive background information and constraints upfront, but focus each turn on one primary objective. This maximizes Cortex Code's reasoning capacity for your main goal while ensuring it has the context needed for intelligent decision-making.

✅ **Rich context and clear goal**

```
I have a customer churn dataset for a telecom company where retention is critical
for revenue. The data includes usage patterns, support tickets, and billing history.
Our target is binary churn within 30 days. Build me an end-to-end ML pipeline
focusing on interpretable features that our business team can act on.
```

❌ **Minimal context**

```
Build me a churn model using this customer data.
```

❌ **Context overload and vague goal**

```
I work at a telecom company with 2M customers across 50 states. We have 15 different
data sources including call logs, billing systems, support tickets, network usage,
device information, demographic data, promotional history, and payment records.
Our churn rate varies by region from 2-8% monthly. The business team needs
interpretable models because of regulatory requirements. Marketing wants to target
high-risk customers. Finance cares about CLV impact. IT wants scalable solutions.
Customer service wants actionable insights. Please help me with machine learning.
```

#### 2. Build iteratively on the baseline solution

Once Cortex Code delivers your initial solution, use follow-up prompts to refine and improve it systematically. Each subsequent turn should build on previous results while maintaining focus on a single improvement area.

✅ **Build on results with more context or specifying improvements**

```
Suggest feature engineering techniques that are common for imbalanced tabular datasets.
```

✅ **Build on results with more context or specifying improvements**

```
Use hyperparameter tuning strategies beyond grid search for XGBoost to optimize
F1-score given class imbalance.
```

❌ **Multiple disconnected changes**

```
Try different algorithms, add new features, fix the data quality issues, and also
make it faster and more interpretable.
```

#### 3. Be specific and prescriptive

The more specific you are about your requirements, methods, and constraints, the better Cortex Code's output will be.

✅ **Clear, specific instructions**

```
Convert the feature strings in the 'FEATURE' column to embeddings using sentence
transformers, then apply K-means clustering with k=5.
```

❌ **Vague prompt with little context**

```
Cluster my feature strings.
```

#### 4. Reiterate critical information to remind the agent of its discoveries

In long, iterative conversations, the agent focuses on your initial request and the most recent turn, which can cause it to forget earlier instructions or findings. Use these techniques to keep your analysis on track:

- **Reiterate critical instructions** — e.g. *"Let's try a Gradient Boosting model now, and remember to continue using MAPE for the evaluation."*
- **Remind the agent of its discoveries** — e.g. *"You found that COLUMN_X was the most important feature. Using that insight, let's now engineer two new features based on it."*
- **Correct a confused context** — e.g. *"That's not the right dataset. Please perform the next step on the PROD.SALES.FORECAST_DATA table."*

## Create features for recency, frequency, and monetary value per customer, plus rolling 7/30/90-day aggregations on spend and register them as feature views

Feature engineering is often the most time-consuming step in ML development. Cortex Code can generate RFM (Recency, Frequency, Monetary) features and rolling aggregations in a single prompt, and register them directly as versioned feature views in the Snowflake Feature Store — ready for reuse across multiple models.

```
Create features for recency, frequency, and monetary value per customer, plus
rolling 7/30/90-day aggregations on spend and register them as feature views.
```

Once your baseline features are registered, keep iterating:

```
Which of the RFM features have the highest correlation with the target variable?
Drop any that are redundant or have near-zero variance.
```

```
Add a feature that captures the ratio of spend in the last 7 days versus the
30-day rolling average, and register it as a new version of the feature view.
```

## Explore multiple model architectures to train a fraud detection model and evaluate the model versions, suggesting the best one to deploy. Use 20% of the training set to validate against. Log each run as an experiment.

Rather than committing to a single model type upfront, Cortex Code can systematically explore multiple architectures, evaluate them against a consistent validation split, and surface the best candidate — with every run tracked as a named experiment for full reproducibility.

```
Explore multiple model architectures to train a fraud detection model and evaluate
the model versions, suggesting the best one to deploy. Use 20% of the training set
to validate against. Log each run as an experiment.
```

Build on the results to dig deeper into the winning model:

```
The XGBoost model had the best F1-score. Explain which features drove that result
using SHAP values, and flag any features that might introduce data leakage.
```

```
Use hyperparameter tuning strategies beyond grid search for XGBoost to optimize
F1-score given class imbalance in the fraud labels.
```

## Log this model to the registry and include performance metrics from the evaluation step as attributes

Logging models with rich metadata — precision, recall, F1, AUC, and dataset version — creates a governed audit trail and makes it easy to compare versions and roll back if needed. Cortex Code handles the registry API calls automatically.

```
Log this model to the registry and include performance metrics from the evaluation
step as attributes.
```

Extend the registry entry with additional context:

```
Add the training dataset version, feature view version, and the hyperparameter
configuration as additional metadata attributes on the logged model.
```

```
Show me all versions of this model in the registry, sorted by F1-score, and
recommend which version should be promoted to production.
```

## Deploy this model as a real-time inference endpoint using a GPU compute pool. Set up a model monitor for this deployment and track both drift and accuracy.

Taking a model from registry to a live inference endpoint — with monitoring already configured — is often where ML projects stall. Cortex Code provisions the compute pool, deploys the endpoint, and configures the model monitor in one conversation.

```
Deploy this model as a real-time inference endpoint using a GPU compute pool.
Set up a model monitor for this deployment and track both drift and accuracy.
```

Refine your deployment and monitoring configuration:

```
Set alert thresholds on the model monitor so that I get notified if prediction
drift exceeds 10% or accuracy drops more than 5% from the baseline.
```

```
Show me the current drift and accuracy metrics for the deployed model and
summarize whether any thresholds have been breached.
```

## Conclusion and resources

The key to success with agentic ML in Snowflake is to start with a focused goal, iterate one step at a time, and let Cortex Code handle the boilerplate while you apply your domain expertise. Use the prompting best practices above to get faster, higher-quality results — and take advantage of Snowflake's integrated Feature Store, Model Registry, and Model Monitor to build pipelines that are reproducible, governed, and production-ready.

- [Cortex Code documentation](https://docs.snowflake.com/en/user-guide/cortex-code/overview)
- Start your [30-day Cortex Code CLI trial](https://signup.snowflake.com/cortex-code)
- [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
- [Snowflake Feature Store](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview)
- [Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Best Practices for Cortex Code CLI](https://www.snowflake.com/en/developers/guides/best-practices-cortex-code-cli/)

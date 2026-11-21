# Instructions
Create a ground truth dataset and run evaluations for HOL_COCO_COWORK.AGENTS.HOT_FOOD_SALES_AGENT.

## Specifications
- **Role**: Use role ACCOUNTADMIN
- **Agent**: HOL_COCO_COWORK.AGENTS.HOT_FOOD_SALES_AGENT
- **Dataset Location**: HOL_COCO_COWORK.AGENTS.EVAL_DATASET_HOT_FOOD_SALES_AGENT
- **Metrics**: answer_correctness, logical_consistency
- **Question Count**: 10 ground truth questions covering basic metrics, dimensional analysis, trends, rankings, and filter analysis
- **Ground Truth**: Real answers derived from querying the underlying data tables

## Evaluation Config
- **Stage**: HOL_COCO_COWORK.AGENTS.EVAL_CONFIG_STAGE
- **Config filename**: HOT_FOOD_SALES_AGENT_eval_config.yaml
- **Run via**:
```sql
CALL EXECUTE_AI_EVALUATION(
    'START',
    OBJECT_CONSTRUCT('run_name', '<run_name>'),
    '@HOL_COCO_COWORK.AGENTS.EVAL_CONFIG_STAGE/HOT_FOOD_SALES_AGENT_eval_config.yaml'
);
```

## Deploy

After creating the dataset, register it with `SYSTEM$CREATE_EVALUATION_DATASET` and run the evaluation. Present results.

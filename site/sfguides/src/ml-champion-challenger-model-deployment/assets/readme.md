# Champion Challenger Modelling In Snowflake

This repository implements a complete **Champion-Challenger model deployment strategy** using Snowflake ML Registry.
More details can be found in the medium blog.

## 🎯 What is Champion-Challenger Modeling?

Champion-Challenger is a production MLOps pattern where:
- **Champion**: The current production model serving predictions
- **Challenger**: A newly trained model that competes with the champion
- **Evaluation**: Both models are tested on the same holdout dataset
- **Promotion**: If the challenger performs significantly better, it becomes the new champion

## 🚀 Quick Start
Run all the notebooks in the numbered order under notebooks folder. These are code to be run in Snowflake inbuilt container notebooks.
You can load the code directly from the repository in SF notebooks.
If you want to run it from external IDE establish connection with Snowflake and refactor the code.

## Order of execution of notebooks
1. CC_1_Data_generation.ipynb
2. CC_2_Champion_training.ipynb
3. CC_3_Challenger_training.ipynb
4. CC_4_Swap_models.ipynb
5. CC_5_Automation.ipynb  

## 🏗️ Architecture

### Data Flow
```
📊 Historical Data (Training) → 🏆 Champion Model
                ↓
📥 New Weekly Data → 🥊 Challenger Model
                ↓
📋 Evaluation Dataset → 📊 Performance Comparison
                ↓
🔄 Model Promotion Decision → 🏷️ Registry Updates
```

### Time-Based Data Splits
```
Weeks 0-9  : Training Data (Champion)
Weeks 10-12: Test Data (Champion)
Weeks 3-12 : Training Data (Challenger)
Weeks 13-15: Test Data (Challenger)
Weeks 16-19: Evaluation Data (Hold-out for comparison)
```
## 📊 Dataset Structure
```
The framework creates realistic temporal datasets with:
- **Time-based splits** (no data leakage)
- **Concept drift** simulation (models degrade over time)
- **Seasonal patterns** (business seasonality)
- **Realistic business features** (finance domain)

### Features for Credit Approval Model:
- `applicant_age`: Applicant age (18-80)
- `annual_income`: Yearly income ($20K-$200K)
- `credit_score`: Credit score (300-850)
- `debt_to_income`: Debt-to-income ratio (0-1)
- `years_employed`: Employment history (0-40 years)
- `num_credit_cards`: Number of credit cards (0-8)
- `has_mortgage`: Mortgage status (0/1)
- `education_score`: Education level (1-5)
- `location_risk_score`: Geographic risk (0-1)
- `approved`: Target variable (0=denied, 1=approved)
```
## 🔍 Troubleshooting

### Common Issues

1. **No Champion Found**
   ```
   ❌ No current champion found
   Solution: Run initial champion training first
   ```

2. **Data Format Errors**
   ```
   ❌ Feature mismatch between models
   Solution: Ensure consistent feature engineering
   ```

3. **Registry Permission Issues**
   ```
   ❌ Access denied to model registry
   Solution: Check Snowflake role permissions
   ```

# Insurance Claims Feature Engineering - Spark Job

## Overview
This Spark job uses **Snowpark Connect for Apache Spark** to perform complex feature engineering on insurance claims data. It reads raw claims data, joins with historical fraud and policy information, generates ML-ready features including a **Fraud Risk Score from a pre-trained Python model**, and writes the enriched dataset to a **Snowflake Native Table** optimized for reporting and AI/ML consumption.

## Pre-trained Fraud Detection Model

The pipeline uses a serialized fraud detection model (`fraud_model.py`) that simulates a production ML model trained on historical fraud data.

### Model Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                  FraudDetectionModel                        │
├─────────────────────────────────────────────────────────────┤
│  Input Features:                                            │
│  ├── Loss Type → Embedding Layer (4-dim learned vectors)   │
│  ├── Estimate Amount → Log Normalization                    │
│  ├── SIU Referral → Binary Flag (with 1.4x multiplier)     │
│  ├── Investigation Status → Status Embeddings              │
│  ├── Prior Claims → Linear Factor (capped)                 │
│  ├── Policy Age → Risk Buckets (30/90/180 days)            │
│  ├── Injury Flag → Binary Signal                           │
│  ├── Reporting Delay → Time-based Risk                     │
│  ├── Premium Ratio → Anomaly Detection                     │
│  └── Text Keywords → Fraud Indicator Flags                 │
├─────────────────────────────────────────────────────────────┤
│  Cross-Feature Interactions:                                │
│  └── loss_embedding × estimate × siu × policy_age          │
├─────────────────────────────────────────────────────────────┤
│  Output:                                                    │
│  ├── Weighted Sum → Sigmoid Activation → Score (0-100)     │
│  └── Threshold Classification → Risk Category              │
└─────────────────────────────────────────────────────────────┘
```

### Model Features & Learned Weights
| Feature | Weight | Description |
|---------|--------|-------------|
| `siu_referral_flag` | 0.25 | Special Investigations Unit referral |
| `loss_type_risk` | 0.20 | Learned embedding for loss type |
| `investigation_active` | 0.18 | Current investigation status |
| `text_fraud_indicators` | 0.15 | Fraud keywords in notes |
| `estimate_amount_normalized` | 0.15 | Log-normalized claim amount |
| `prior_claims_factor` | 0.12 | Historical claims count |
| `historical_risk_score` | 0.10 | Previous fraud scores |
| `premium_ratio_anomaly` | 0.10 | Claim vs premium ratio |
| `policy_age_risk` | 0.08 | New policy risk factor |
| `reporting_delay_risk` | 0.07 | Late reporting indicator |
| `injury_flag` | 0.05 | Injury involvement |
| `cross_feature_interaction` | 0.05 | Multi-feature signals |

### Risk Categories
| Score Range | Category |
|-------------|----------|
| 70-100 | High Risk |
| 50-69 | Medium Risk |
| 30-49 | Low Risk |
| 0-29 | Minimal Risk |

## Features Engineered

### Duration Metrics
- `days_to_report` - Days between loss and report
- `days_since_loss` - Days from loss to current date
- `days_to_estimate` - Days from loss to estimate creation
- `policy_age_at_loss` - Policy age when claim occurred
- `reporting_delay_category` - Categorical: Same Day, Next Day, Within 3 Days, etc.

### Risk Features
- `loss_type_category` - High/Medium/Standard Risk based on loss type
- `estimate_to_premium_ratio` - Claim amount vs annual premium
- `complexity_score` - Weighted score based on injuries, parties, police reports
- `risk_tier_numeric` - Numeric encoding of policy risk tier

### Text Features (from Adjuster Notes)
- `normalized_content` - Cleaned, lowercase text
- `notes_word_count` - Total words in notes
- `has_attorney_mention` - Boolean flag for attorney involvement
- `has_fraud_keywords` - Boolean flag for suspicious terms

### ML Fraud Risk Score (Pre-trained Model)
- `ml_fraud_risk_score` - 0-100 score from pre-trained model
- `fraud_risk_category` - High/Medium/Low/Minimal Risk

## Data Sources

### Snowflake Tables (Default)
The pipeline reads directly from tables:

| Table | Description |
|-------|-------------|
| `FNOL_REPORTS` | First Notice of Loss reports |
| `ADJUSTER_NOTES` | Adjuster investigation notes |
| `INITIAL_ESTIMATES` | Repair/total loss estimates |
| `FRAUD_FLAGS` | Historical fraud indicators |
| `POLICY_DETAILS` | Policy coverage information |


## Project Structure
```
spark_jobs/
├── Insurance-Claims-Feature-Engineering.ipynb   # Main Spark Notebook
├── fraud_model.py                  # Pre-trained model definition
├── models/
│   └── fraud_detection_model.pkl   # Serialized model file
├── requirements.txt                # Dependencies
└── README.md                       # This file
```

## Setup

### Prerequisites
- Python 3.10+
- Snowflake account with Snowpark Connect enabled

### Create Pre-trained Model
```bash
# Generate and save the pre-trained model
python fraud_model.py
```

## Model Retraining
To retrain the fraud model with new data:
1. Update the weights in `fraud_model.py` based on new training results
2. Run `python fraud_model.py` to regenerate the serialized model
3. The Spark job will automatically use the updated model

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
The pipeline reads directly from Snowflake tables:

| Table | Description |
|-------|-------------|
| `FNOL_REPORTS` | First Notice of Loss reports |
| `ADJUSTER_NOTES` | Adjuster investigation notes |
| `INITIAL_ESTIMATES` | Repair/total loss estimates |
| `FRAUD_FLAGS` | Historical fraud indicators |
| `POLICY_DETAILS` | Policy coverage information |

### CSV Files (Fallback)
If Snowflake is unavailable or `USE_SNOWFLAKE_SOURCE=false`:

| File | Description |
|------|-------------|
| `fnol_reports.csv` | First Notice of Loss reports |
| `adjuster_notes.csv` | Adjuster investigation notes |
| `initial_estimates.csv` | Repair/total loss estimates |
| `fraud_flags.csv` | Historical fraud indicators |
| `policy_details.csv` | Policy coverage information |

## Project Structure
```
spark_jobs/
├── claims_feature_engineering.py   # Main Spark pipeline
├── fraud_model.py                  # Pre-trained model definition
├── models/
│   └── fraud_detection_model.pkl   # Serialized model file
├── requirements.txt                # Dependencies
└── README.md                       # This file
```

## Setup

### Prerequisites
- Python 3.10+
- Java 8+ (same architecture as Python)
- Snowflake account with Snowpark Connect enabled

### Installation
```bash
cd spark_jobs
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Create Pre-trained Model
```bash
# Generate and save the pre-trained model
python fraud_model.py
```

### Configure Snowflake Connection
Create `~/.snowflake/connections.toml`:
```toml
[spark-connect]
host="your_account.snowflakecomputing.com"
account="your_account"
user="your_user"
password="your_password"
warehouse="COMPUTE_WH"
database="INSURANCE_CLAIMS_DB"
schema="CLAIMS_ANALYTICS"
```

## Usage

### Run with Snowpark Connect
```bash
python claims_feature_engineering.py
```

### Run with Custom Paths
```bash
DATA_PATH=/path/to/data \
OUTPUT_PATH=/path/to/output \
FRAUD_MODEL_PATH=/path/to/model.pkl \
SNOWFLAKE_DATABASE=MY_DB \
SNOWFLAKE_SCHEMA=MY_SCHEMA \
SNOWFLAKE_TABLE=MY_FEATURES_TABLE \
python claims_feature_engineering.py
```

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| USE_SNOWFLAKE_SOURCE | true | Read from Snowflake tables (false=CSV) |
| DATA_PATH | ./data | CSV files location (when not using Snowflake) |
| OUTPUT_PATH | ./output | CSV backup location |
| FRAUD_MODEL_PATH | ./models/fraud_detection_model.pkl | Pre-trained model |
| SNOWFLAKE_DATABASE | INSURANCE_CLAIMS_DB | Target database |
| SNOWFLAKE_SCHEMA | CLAIMS_ANALYTICS | Target schema |
| SNOWFLAKE_OUTPUT_TABLE | CLAIMS_PROCESSED_FEATURES | Output table name |
| FNOL_TABLE | FNOL_REPORTS | Source FNOL table name |
| ADJUSTER_NOTES_TABLE | ADJUSTER_NOTES | Source adjuster notes table |
| INITIAL_ESTIMATES_TABLE | INITIAL_ESTIMATES | Source estimates table |
| FRAUD_FLAGS_TABLE | FRAUD_FLAGS | Source fraud flags table |
| POLICY_DETAILS_TABLE | POLICY_DETAILS | Source policy details table |

### Run via Snowpark Submit (Production)
```bash
snow spark submit claims_feature_engineering.py \
    --warehouse COMPUTE_WH \
    --database INSURANCE_CLAIMS_DB \
    --schema CLAIMS_ANALYTICS \
    --py-files fraud_model.py
```

## Output

### Snowflake Native Table
The pipeline writes enriched data to:
```
INSURANCE_CLAIMS_DB.CLAIMS_ANALYTICS.CLAIMS_PROCESSED_FEATURES
```

This table is optimized for:
- **Reporting**: Clean column names, categorized fields, pre-computed metrics
- **AI/ML Consumption**: Numeric features, normalized scores, embeddings-ready
- **Analytics**: Timestamp tracking, full audit trail

### Table Schema (50+ columns)
| Column | Type | Description |
|--------|------|-------------|
| CLAIM_ID | VARCHAR | Primary key |
| ML_FRAUD_RISK_SCORE | FLOAT | Pre-trained model score (0-100) |
| FRAUD_RISK_CATEGORY | VARCHAR | High/Medium/Low/Minimal Risk |
| COMPLEXITY_SCORE | INT | Claim complexity metric |
| ESTIMATE_TO_PREMIUM_RATIO | FLOAT | Anomaly detection feature |
| PROCESSED_AT | TIMESTAMP | Pipeline execution time |
| ... | ... | 45+ additional features |

### CSV Backup
Also writes to `output/enriched_claims_features/` as CSV backup.

## Model Retraining
To retrain the fraud model with new data:
1. Update the weights in `fraud_model.py` based on new training results
2. Run `python fraud_model.py` to regenerate the serialized model
3. The Spark job will automatically use the updated model

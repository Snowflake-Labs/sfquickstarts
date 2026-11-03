"""
Credit Risk PD Model — Python/XGBoost on Snowflake
Converted from SAS PROC HPFOREST by Cortex Code (CoCo)

SAS Source:  sas_pd_model.sas (PROC HPFOREST, maxtrees=200, maxdepth=6)
Python Target: XGBClassifier with Snowflake ML platform integration

Conversion mapping:
    PROC HPFOREST (maxtrees=200, maxdepth=6)  →  XGBClassifier(n_estimators=200, max_depth=6)
    PROC SQL joins + SAS macros                →  Feature Store (Feature Views + Dynamic Tables)
    Manual dataset freezes                     →  fs.generate_dataset() — versioned, immutable
    ODS OUTPUT + Excel tracker                 →  Experiment Tracking (log_params, log_metrics)
    .bin file on shared filesystem             →  Model Registry (versions, aliases, RBAC)
    PROC HP4SCORE                              →  model.run() on warehouse compute
"""

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
from snowflake.ml.feature_store import FeatureStore, Entity, FeatureView
from snowflake.ml.registry import Registry
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from scipy.stats import ks_2samp

session = get_active_session()

# ---------------------------------------------------------------
# Step 1: Feature Engineering via Feature Store
# Replaces: SAS %let macros + PROC SQL joins
# ---------------------------------------------------------------

fs = FeatureStore(
    session=session,
    database="CREDIT_RISK_ML",
    name="PD_MODEL",
    default_warehouse="CREDIT_RISK_WH"
)

loan_entity = Entity(name="LOAN", join_keys=["TRADE_ID"])
fs.register_entity(loan_entity)

# Behavioral Feature View (replaces SAS macro-generated datasets)
behavioral_fv = FeatureView(
    name="LOAN_BEHAVIORAL_FEATURES",
    entities=[loan_entity],
    feature_df=session.sql("""
        SELECT TRADE_ID, ARCHIVE_DATE,
               VANTAGE_SCORE_3, NUMBER_OF_ACCOUNTS, NUMBER_ACCOUNTS_PAST_DUE,
               NUMBER_ACCOUNTS_MAJOR_DEROGATORY, HIGH_UTIL_ACCTS,
               AGE_OLDEST_ACCOUNT, TOTAL_PAST_DUE_AMOUNT, BALANCE
        FROM CREDIT_RISK_ML.PD_MODEL.LOAN_DATA
    """),
    timestamp_col="ARCHIVE_DATE",
    refresh_freq="1 day",
    desc="Loan-level behavioral features from Equifax"
)
behavioral_fv = fs.register_feature_view(feature_view=behavioral_fv, version="V1")

# Macro Feature View (replaces SAS PROC SQL join to FRED)
macro_fv = FeatureView(
    name="LOAN_MACRO_FEATURES",
    entities=[loan_entity],
    feature_df=session.sql("""
        SELECT l.TRADE_ID, l.ARCHIVE_DATE,
               m.UNEMPLOYMENT_RATE, m.FED_FUNDS_RATE, m.CPI_INDEX
        FROM CREDIT_RISK_ML.PD_MODEL.LOAN_DATA l
        JOIN CREDIT_RISK_ML.PD_MODEL.MACRO_INDICATORS m
            ON DATE_TRUNC('MONTH', l.ARCHIVE_DATE) = m.OBSERVATION_MONTH
    """),
    timestamp_col="ARCHIVE_DATE",
    refresh_freq="1 day",
    desc="Macroeconomic indicators from FRED"
)
macro_fv = fs.register_feature_view(feature_view=macro_fv, version="V1")

# ---------------------------------------------------------------
# Step 2: Versioned Training Dataset
# Replaces: PROC SURVEYSELECT + manual dataset freezes
# ---------------------------------------------------------------

spine_df = session.table("CREDIT_RISK_ML.PD_MODEL.LOAN_DATA").select(
    col("TRADE_ID"), col("ARCHIVE_DATE"), col("DEFAULT_FLAG")
)

dataset = fs.generate_dataset(
    name="PD_TRAINING_DS",
    spine_df=spine_df,
    features=[behavioral_fv, macro_fv],
    spine_timestamp_col="ARCHIVE_DATE",
    spine_label_cols=["DEFAULT_FLAG"],
    output_type="dataset"
)

# ---------------------------------------------------------------
# Step 3: Train XGBoost
# Replaces: PROC HPFOREST maxtrees=200 maxdepth=6 vars_to_try=5
# ---------------------------------------------------------------

train_pdf = dataset.read.to_snowpark_dataframe().to_pandas()

FEATURE_COLS = [
    "VANTAGE_SCORE_3", "NUMBER_OF_ACCOUNTS", "NUMBER_ACCOUNTS_PAST_DUE",
    "NUMBER_ACCOUNTS_MAJOR_DEROGATORY", "HIGH_UTIL_ACCTS",
    "AGE_OLDEST_ACCOUNT", "TOTAL_PAST_DUE_AMOUNT", "BALANCE",
    "UNEMPLOYMENT_RATE", "FED_FUNDS_RATE", "CPI_INDEX"
]

X = train_pdf[FEATURE_COLS].fillna(0)
y = train_pdf["DEFAULT_FLAG"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# XGBoost hyperparameters mapped from SAS PROC HPFOREST:
#   maxtrees=200  →  n_estimators=200
#   maxdepth=6    →  max_depth=6
#   vars_to_try=5 →  colsample_bytree ≈ 5/11 features
#   leafsize=20   →  min_child_weight (approx)
model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    colsample_bytree=5 / len(FEATURE_COLS),
    min_child_weight=20,
    objective="binary:logistic",
    eval_metric="auc",
    random_state=42,
    use_label_encoder=False
)
model.fit(X_train, y_train)

# ---------------------------------------------------------------
# Step 4: Evaluate
# Replaces: PROC LOGISTIC ROC + manual Excel logging
# ---------------------------------------------------------------

y_pred_proba = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
gini = 2 * auc - 1
ks_stat = ks_2samp(y_pred_proba[y_test == 0], y_pred_proba[y_test == 1]).statistic

print(f"AUC:  {auc:.4f}")
print(f"Gini: {gini:.4f}")
print(f"KS:   {ks_stat:.4f}")

# ---------------------------------------------------------------
# Step 5: Register in Model Registry
# Replaces: save file="/models/pd_hpforest_model.bin" + filesystem
# ---------------------------------------------------------------

reg = Registry(session=session, database_name="CREDIT_RISK_ML", schema_name="PD_MODEL")

mv = reg.log_model(
    model=model,
    model_name="PD_XGB_MODEL",
    version_name="V1",
    sample_input_data=X_test.head(5),
    comment="PD model — XGBoost migrated from SAS PROC HPFOREST",
    metrics={"auc": auc, "gini": gini, "ks": ks_stat}
)
mv.set_alias("champion")

# ---------------------------------------------------------------
# Step 6: Batch Scoring
# Replaces: PROC HP4SCORE
# ---------------------------------------------------------------

champion = reg.get_model("PD_XGB_MODEL").default
scoring_df = session.sql("""
    SELECT l.TRADE_ID, l.ARCHIVE_DATE, l.DEFAULT_FLAG,
           l.VANTAGE_SCORE_3, l.NUMBER_OF_ACCOUNTS, l.NUMBER_ACCOUNTS_PAST_DUE,
           l.NUMBER_ACCOUNTS_MAJOR_DEROGATORY, l.HIGH_UTIL_ACCTS,
           l.AGE_OLDEST_ACCOUNT, l.TOTAL_PAST_DUE_AMOUNT, l.BALANCE,
           m.UNEMPLOYMENT_RATE, m.FED_FUNDS_RATE, m.CPI_INDEX
    FROM CREDIT_RISK_ML.PD_MODEL.LOAN_DATA l
    JOIN CREDIT_RISK_ML.PD_MODEL.MACRO_INDICATORS m
        ON DATE_TRUNC('MONTH', l.ARCHIVE_DATE) = m.OBSERVATION_MONTH
""")

predictions = champion.run(scoring_df)
predictions.write.save_as_table("CREDIT_RISK_ML.PD_MODEL.PD_SCORES_CURRENT", mode="overwrite")
print(f"Scored {predictions.count():,} loans")

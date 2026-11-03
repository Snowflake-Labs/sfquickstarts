/*==============================================================================
  Credit Risk PD Model — SAS PROC HPFOREST
  
  Purpose: Train a Probability of Default model using Random Forest
           on loan-level behavioral and macroeconomic features.
  
  Target:  DEFAULT_FLAG (1 = 90+ DPD, 0 = Current/30/60 DPD)
  
  Data:    WORK.PD_TRAINING — loan-level features joined with macro indicators
==============================================================================*/

/* -----------------------------------------------------------------
   Step 1: Data Preparation — Feature Engineering via SAS Macros
   ----------------------------------------------------------------- */

%let EQUIFAX_LIB  = EQFX;
%let FRED_LIB     = MACRO;
%let OUT_LIB      = WORK;
%let OBS_START    = '01JAN2022'd;
%let OBS_END      = '31DEC2025'd;

/* Join loan-level features with monthly macro indicators */
proc sql;
    create table &OUT_LIB..PD_TRAINING as
    select
        /* Entity keys */
        l.TRADE_ID,
        l.ARCHIVE_DATE,

        /* Target */
        case when l.STATUS_CATEGORY >= 4 then 1 else 0 end as DEFAULT_FLAG,

        /* Behavioral features (Equifax) */
        l.VANTAGE_SCORE_3,
        l.NUMBER_OF_ACCOUNTS,
        l.NUMBER_ACCOUNTS_PAST_DUE,
        l.NUMBER_ACCOUNTS_MAJOR_DEROGATORY,
        l.BANKCARD_ACCTS_OVER_75_PERCENT_UTILIZATION as HIGH_UTIL_ACCTS,
        l.AGE_OLDEST_ACCOUNT,
        l.TOTAL_PAST_DUE_AMOUNT,
        l.BALANCE,

        /* Macro features (FRED) */
        m.UNEMPLOYMENT_RATE,
        m.FED_FUNDS_RATE,
        m.CPI_INDEX

    from &EQUIFAX_LIB..ANALYTIC_SAMPLE as l
    inner join &FRED_LIB..MACRO_INDICATORS as m
        on intnx('month', l.ARCHIVE_DATE, 0, 'beginning') = m.OBSERVATION_MONTH
    where l.ARCHIVE_DATE between &OBS_START and &OBS_END;
quit;

/* Impute missing values with 0 */
data &OUT_LIB..PD_TRAINING;
    set &OUT_LIB..PD_TRAINING;
    array nums _numeric_;
    do over nums;
        if nums = . then nums = 0;
    end;
run;

/* -----------------------------------------------------------------
   Step 2: Train/Test Split
   ----------------------------------------------------------------- */

proc surveyselect data=&OUT_LIB..PD_TRAINING
    out=&OUT_LIB..PD_SPLIT
    method=srs
    samprate=0.8
    seed=42
    outall;
run;

data &OUT_LIB..PD_TRAIN &OUT_LIB..PD_TEST;
    set &OUT_LIB..PD_SPLIT;
    if selected then output &OUT_LIB..PD_TRAIN;
    else output &OUT_LIB..PD_TEST;
run;

/* -----------------------------------------------------------------
   Step 3: Train PROC HPFOREST — Random Forest PD Model
   ----------------------------------------------------------------- */

proc hpforest data=&OUT_LIB..PD_TRAIN
    maxtrees=200
    vars_to_try=5
    maxdepth=6
    leafsize=20
    seed=42;

    /* Target variable */
    target DEFAULT_FLAG / level=binary;

    /* Behavioral features (interval = continuous) */
    input VANTAGE_SCORE_3
          NUMBER_OF_ACCOUNTS
          NUMBER_ACCOUNTS_PAST_DUE
          NUMBER_ACCOUNTS_MAJOR_DEROGATORY
          HIGH_UTIL_ACCTS
          AGE_OLDEST_ACCOUNT
          TOTAL_PAST_DUE_AMOUNT
          BALANCE
          / level=interval;

    /* Macro features (interval = continuous) */
    input UNEMPLOYMENT_RATE
          FED_FUNDS_RATE
          CPI_INDEX
          / level=interval;

    /* Save model for scoring */
    save file="/models/pd_hpforest_model.bin";

    /* Output variable importance */
    ods output VariableImportance = &OUT_LIB..PD_IMPORTANCE;
    ods output FitStatistics      = &OUT_LIB..PD_FITSTATS;
run;

/* -----------------------------------------------------------------
   Step 4: Score Test Set
   ----------------------------------------------------------------- */

proc hp4score data=&OUT_LIB..PD_TEST;
    id TRADE_ID ARCHIVE_DATE DEFAULT_FLAG;
    score file="/models/pd_hpforest_model.bin"
          out=&OUT_LIB..PD_SCORED;
run;

/* -----------------------------------------------------------------
   Step 5: Model Evaluation — Discrimination Metrics
   ----------------------------------------------------------------- */

/* AUC via PROC LOGISTIC on predicted probabilities */
proc logistic data=&OUT_LIB..PD_SCORED;
    model DEFAULT_FLAG(event='1') = P_DEFAULT_FLAG1 / nofit;
    roc pred=P_DEFAULT_FLAG1;
    ods output ROCAssociation = &OUT_LIB..PD_AUC;
run;

/* Print results */
proc print data=&OUT_LIB..PD_AUC noobs;
    var Area;
    title "PD Model — AUC on Test Set";
run;

proc print data=&OUT_LIB..PD_IMPORTANCE(obs=11);
    title "PD Model — Variable Importance (Top Features)";
run;

/* -----------------------------------------------------------------
   Step 6: Export Metrics to Tracking Spreadsheet (manual process)
   ----------------------------------------------------------------- */

/* 
   NOTE: In the SAS environment, model metrics are manually recorded
   in an Excel tracker. There is no native experiment tracking, model
   registry, or automated monitoring. The model binary (.bin) is stored
   on a shared filesystem with version-named directories.
   
   This entire workflow — from feature generation through monitoring —
   is replaced by Snowflake ML's integrated platform:
   
   SAS PROC HPFOREST  →  XGBClassifier on Snowflake
   SAS macros          →  Feature Store (Feature Views + Dynamic Tables)
   Manual freezes      →  Versioned Datasets
   Excel tracking      →  Experiment Tracking
   .bin files          →  Model Registry (versions, aliases, RBAC)
   Quarterly reports   →  Model Monitors (continuous drift detection)
   Cron scripts        →  Task DAGs
*/

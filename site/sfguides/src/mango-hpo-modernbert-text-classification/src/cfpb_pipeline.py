"""
Distributed CFPB Text Classification Pipeline
==============================================

Uses Mango HPO + TF-IDF + MLP + Snowflake DPF for distributed 
hyperparameter optimization and text classification.

Author: Priya Joseph
Date: January 2026
"""

import json
import time
import tempfile
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# =============================================================================
# SNOWFLAKE IMPORTS
# =============================================================================
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session
from snowflake.ml.data.data_connector import DataConnector
from snowflake.ml.processing import distributed_hpo

# =============================================================================
# ML IMPORTS
# =============================================================================
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from mango import Tuner, scheduler


# =============================================================================
# CONFIGURATION
# =============================================================================
@dataclass
class PipelineConfig:
    """Configuration for the text classification pipeline."""
    database: str = 'CFPB_ML_DB'
    schema: str = 'TEXT_ANALYTICS'
    source_table: str = 'CFPB_COMPLAINTS'
    results_table: str = 'CLASSIFICATION_RESULTS'
    stage: str = 'ML_ARTIFACTS_STAGE'
    partition_column: str = 'PRODUCT'
    text_column: str = 'CONSUMER_COMPLAINT_NARRATIVE'
    label_column: str = 'ISSUE'
    max_features: int = 5000
    hpo_iterations: int = 15
    test_size: float = 0.2
    random_state: int = 42
    min_samples_per_partition: int = 100


# Default configuration
CONFIG = PipelineConfig()

# Mango HPO search space for MLP hyperparameters
PARAM_SPACE = {
    'hidden_layer_sizes': [
        (64,), 
        (128,), 
        (64, 32), 
        (128, 64), 
        (256, 128),
        (128, 64, 32)
    ],
    'alpha': [0.0001, 0.001, 0.01, 0.1],
    'learning_rate_init': [0.001, 0.01, 0.1],
    'activation': ['relu', 'tanh'],
    'max_iter': [200, 500, 1000]
}


# =============================================================================
# DPF WORKER FUNCTION
# =============================================================================
def process_text_partition(
    session: Session,
    partition_data: pd.DataFrame,
    partition_key: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a single partition of text data with Mango HPO.
    
    This function runs on each DPF worker node and performs:
    1. Text preprocessing and TF-IDF vectorization
    2. Bayesian hyperparameter optimization with Mango
    3. Final model training with best parameters
    4. Results storage to Snowflake stage
    
    Args:
        session: Snowflake session
        partition_data: DataFrame containing partition data
        partition_key: Unique identifier for this partition
        config: Pipeline configuration dictionary
        
    Returns:
        Dictionary containing training results and metrics
    """
    start_time = time.time()
    
    # Extract config values
    text_col = config.get('text_column', 'CONSUMER_COMPLAINT_NARRATIVE')
    label_col = config.get('label_column', 'ISSUE')
    max_features = config.get('max_features', 5000)
    test_size = config.get('test_size', 0.2)
    random_state = config.get('random_state', 42)
    hpo_iterations = config.get('hpo_iterations', 15)
    min_samples = config.get('min_samples_per_partition', 100)
    stage = config.get('stage', 'ML_ARTIFACTS_STAGE')
    
    # Filter valid records (must have text and label)
    df = partition_data.dropna(subset=[text_col, label_col])
    
    # Skip partitions with insufficient data
    if len(df) < min_samples:
        return {
            'partition': partition_key,
            'status': 'skipped',
            'reason': f'insufficient_data (need {min_samples}, have {len(df)})',
            'records': len(df)
        }
    
    # Prepare text and labels
    texts = df[text_col].astype(str).tolist()
    labels = df[label_col].astype(str).tolist()
    
    # Encode labels to integers
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)
    num_classes = len(label_encoder.classes_)
    
    # Skip if only one class (can't do classification)
    if num_classes < 2:
        return {
            'partition': partition_key,
            'status': 'skipped',
            'reason': f'single_class (only {num_classes} class)',
            'records': len(df)
        }
    
    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95
    )
    X = vectorizer.fit_transform(texts)
    
    # Train/test split with stratification
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y
        )
    except ValueError:
        # Fall back to non-stratified split if stratification fails
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state
        )
    
    # Define Mango objective function
    @scheduler.serial
    def objective(**params):
        """Objective function for Mango HPO - returns F1 score to maximize."""
        clf = MLPClassifier(
            hidden_layer_sizes=params['hidden_layer_sizes'],
            alpha=params['alpha'],
            learning_rate_init=params['learning_rate_init'],
            activation=params['activation'],
            max_iter=params['max_iter'],
            random_state=random_state,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        return f1_score(y_test, y_pred, average='weighted')
    
    # Run Mango HPO
    tuner = Tuner(
        param_dict=PARAM_SPACE,
        objective=objective,
        conf_dict={
            'num_iteration': hpo_iterations,
            'initial_random': min(5, hpo_iterations)
        }
    )
    hpo_results = tuner.maximize()
    
    # Extract best parameters
    best_params = hpo_results['best_params']
    best_hpo_score = hpo_results['best_objective']
    
    # Train final model with best parameters
    final_clf = MLPClassifier(
        hidden_layer_sizes=best_params['hidden_layer_sizes'],
        alpha=best_params['alpha'],
        learning_rate_init=best_params['learning_rate_init'],
        activation=best_params['activation'],
        max_iter=best_params['max_iter'],
        random_state=random_state,
        early_stopping=True
    )
    final_clf.fit(X_train, y_train)
    y_pred = final_clf.predict(X_test)
    
    # Calculate final metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    training_time = time.time() - start_time
    
    # Prepare comprehensive results
    result = {
        'partition': partition_key,
        'status': 'success',
        'records_processed': len(df),
        'train_records': X_train.shape[0],
        'test_records': X_test.shape[0],
        'num_features': X.shape[1],
        'num_classes': num_classes,
        'class_names': label_encoder.classes_.tolist()[:20],  # First 20 classes
        'best_accuracy': float(accuracy),
        'best_f1_score': float(f1),
        'best_hpo_score': float(best_hpo_score),
        'best_params': {
            'hidden_layer_sizes': str(best_params['hidden_layer_sizes']),
            'alpha': best_params['alpha'],
            'learning_rate_init': best_params['learning_rate_init'],
            'activation': best_params['activation'],
            'max_iter': best_params['max_iter']
        },
        'training_time_seconds': round(training_time, 2),
        'hpo_iterations': hpo_iterations
    }
    
    # Save results to Snowflake stage
    try:
        stage_path = f"@{stage}/text_classification/{partition_key.replace(' ', '_')}/"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(result, f, indent=2)
            temp_path = f.name
        
        session.file.put(temp_path, stage_path, auto_compress=False, overwrite=True)
    except Exception as e:
        result['stage_save_error'] = str(e)
    
    return result


# =============================================================================
# MAIN EXECUTION FUNCTIONS
# =============================================================================
def run_distributed_text_classification(
    session: Optional[Session] = None,
    config: Optional[PipelineConfig] = None
) -> List[Dict[str, Any]]:
    """
    Main function to run distributed text classification with DPF.
    
    Args:
        session: Optional Snowflake session (uses active session if not provided)
        config: Optional pipeline configuration
        
    Returns:
        List of result dictionaries from each partition
    """
    # Get session
    if session is None:
        session = get_active_session()
    
    # Use default config if not provided
    if config is None:
        config = CONFIG
    
    # Convert config to dict for worker function
    config_dict = {
        'text_column': config.text_column,
        'label_column': config.label_column,
        'max_features': config.max_features,
        'test_size': config.test_size,
        'random_state': config.random_state,
        'hpo_iterations': config.hpo_iterations,
        'min_samples_per_partition': config.min_samples_per_partition,
        'stage': config.stage
    }
    
    print("=" * 70)
    print("DISTRIBUTED TEXT CLASSIFICATION WITH MANGO HPO + DPF")
    print("=" * 70)
    print(f"Database: {config.database}")
    print(f"Schema: {config.schema}")
    print(f"Source Table: {config.source_table}")
    print(f"Partition Column: {config.partition_column}")
    print(f"Text Column: {config.text_column}")
    print(f"Label Column: {config.label_column}")
    print()
    
    # Load data
    table_path = f"{config.database}.{config.schema}.{config.source_table}"
    df = session.table(table_path).to_pandas()
    
    print(f"Total records loaded: {len(df):,}")
    
    # Filter records with text narratives
    df = df.dropna(subset=[config.text_column])
    df = df[df[config.text_column].str.len() > 10]  # Filter very short texts
    print(f"Records with valid text: {len(df):,}")
    
    # Get unique partitions
    partitions = df[config.partition_column].dropna().unique().tolist()
    print(f"Unique partitions: {len(partitions)}")
    for i, p in enumerate(partitions[:5]):
        count = len(df[df[config.partition_column] == p])
        print(f"   - {p}: {count:,} records")
    if len(partitions) > 5:
        print(f"   ... and {len(partitions) - 5} more")
    
    # Create data connector
    data_connector = DataConnector.from_dataframe(df)
    
    # Run DPF
    print("\n Starting distributed HPO across partitions...")
    print("   This may take several minutes depending on data size...")
    
    start_time = time.time()
    
    dpf_results = distributed_hpo.run(
        session=session,
        data_connector=data_connector,
        partition_column=config.partition_column,
        worker_func=process_text_partition,
        worker_func_kwargs={'config': config_dict},
        num_workers=-1,  # Auto-scale based on available nodes
        timeout_seconds=7200  # 2 hour timeout
    )
    
    total_time = time.time() - start_time
    
    # Collect and display results
    print("\n" + "=" * 70)
    print("RESULTS BY PARTITION")
    print("=" * 70)
    
    all_results = []
    skipped_results = []
    
    for partition, result in dpf_results.items():
        if result.get('status') == 'success':
            print(f"\n {partition}")
            print(f"   Records: {result['records_processed']:,}")
            print(f"   Classes: {result['num_classes']}")
            print(f"   Accuracy: {result['best_accuracy']:.2%}")
            print(f"   F1 Score: {result['best_f1_score']:.4f}")
            print(f"   Time: {result['training_time_seconds']:.1f}s")
            print(f"   Best Params: hidden={result['best_params']['hidden_layer_sizes']}, "
                  f"alpha={result['best_params']['alpha']}")
            all_results.append(result)
        else:
            skipped_results.append(result)
            print(f"\n⏭  {partition} - SKIPPED: {result.get('reason', 'unknown')}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if all_results:
        avg_accuracy = np.mean([r['best_accuracy'] for r in all_results])
        avg_f1 = np.mean([r['best_f1_score'] for r in all_results])
        total_records = sum([r['records_processed'] for r in all_results])
        sum_partition_times = sum([r['training_time_seconds'] for r in all_results])
        
        print(f" Partitions Processed: {len(all_results)}")
        print(f" Partitions Skipped: {len(skipped_results)}")
        print(f" Total Records Processed: {total_records:,}")
        print(f" Average Accuracy: {avg_accuracy:.2%}")
        print(f" Average F1 Score: {avg_f1:.4f}")
        print(f" Total Wall Time: {total_time:.1f}s")
        print(f" Sum of Partition Times: {sum_partition_times:.1f}s")
        print(f" Parallel Speedup: {sum_partition_times/total_time:.1f}x")
    else:
        print(" No partitions were successfully processed.")
    
    # Save summary to results table
    try:
        save_results_to_table(session, all_results, config)
        print(f"\n Results saved to {config.database}.{config.schema}.{config.results_table}")
    except Exception as e:
        print(f"\n Could not save to results table: {e}")
    
    return all_results


def save_results_to_table(
    session: Session,
    results: List[Dict[str, Any]],
    config: PipelineConfig
) -> None:
    """Save classification results to Snowflake table."""
    import uuid
    
    run_id = str(uuid.uuid4())[:8]
    
    for result in results:
        session.sql(f"""
            INSERT INTO {config.database}.{config.schema}.{config.results_table}
            (RUN_ID, PARTITION_KEY, RECORDS_PROCESSED, TRAIN_RECORDS, TEST_RECORDS,
             NUM_CLASSES, BEST_ACCURACY, BEST_F1_SCORE, BEST_PARAMS, 
             TRAINING_TIME_SECONDS, HPO_ITERATIONS, STATUS)
            SELECT 
                '{run_id}',
                '{result['partition']}',
                {result['records_processed']},
                {result['train_records']},
                {result['test_records']},
                {result['num_classes']},
                {result['best_accuracy']},
                {result['best_f1_score']},
                PARSE_JSON('{json.dumps(result['best_params'])}'),
                {result['training_time_seconds']},
                {result['hpo_iterations']},
                '{result['status']}'
        """).collect()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Run the pipeline
    results = run_distributed_text_classification()

author: Ranjeeta Pegu
id: getting-started-with-e2e-customer-targeting-with-snowflake-ml
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform
language: en
summary: Learn how to leverage Snowflake ML to build and deploy propensity-based targeting models, enabling businesses to predict customer behaviors, segment audiences, and deliver personalized marketing campaigns at scale for maximum impact 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with End-to-End Customer Targeting Using Snowflake ML


<!-- ------------------------ -->
## Overview 

Companies use machine learning for targeted customer campaigns to improve engagement and conversions. The intent of this notebook is to demonstrate how you can implement propensity-based targeting directly in Snowflake, where your data resides. This approach eliminates the need for data movement and ensures faster, more efficient turnarounds.

In this guide, we will walk through the end-to-end machine learning workflow within Snowflake, covering key stages such as feature engineering, managing a feature store, model training, and model registry. We will also cover inferencing using the trained models and demonstrate how to integrate these steps within a Snowflake Notebook. By leveraging Snowpark for scalable data processing, the Feature Store for centralized feature management, and the Model Registry for model deployment and version control, all data and processes remain within Snowflake, ensuring faster and more efficient workflows.

Learn about Snowflake ML [here](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)

You can get more information [here](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/README.md)



### Prerequisites
-  Access to [snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN role


### What You’ll Learn 
-  **How to Generate Synthetic Data**:
  Create realistic, structured datasets using Snowpark with numeric, categorical, and time-based features.

-  **How to Build a Feature Store**:
Define entities, register feature views, and manage versioned features in Snowflake.

-  **How to do Feature Reduction**: Slice datasets and apply correlation/variance thresholding for dimensionality reduction.

-  **How to do Model Training and Tuning**: Use Snowflake ML to train XGBoost, Random Forest, etc., and optimize with Grid Search.

-  **How to Register and Deploy Models**: Log models with versioning and run scalable in-database predictions from feature views.




### What You’ll Build 

- Build a Feature Store: Create and manage feature entries for model training within Snowflake.
- Train Classification Models: Use techniques like XGBoost, Random Forest, and Grid Search for model training and hyperparameter tuning.
- Deploy & Predict: Log, register models in Snowflake ML, and run predictions directly using feature views.

<!-- ------------------------ -->
## Setup

**Step 1.** To set up the environment, download the [sqlsetup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/Setup.sql) script from GitHub and execute all the statements in a [Snowflake worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file).

The script includes the following SQL operations
```
USE ROLE ACCOUNTADMIN;
--create database
create database if  not exists ML_MODELS;
--create schema
create schema   if  not exists  ML_MODELS.DS;
create schema if not exists ML_MODELS.FEATURE_STORE;
create schema if not exists ML_MODELS.ML_REGISTRY;

--warehouse 
create warehouse if not exists  DS_W WAREHOUSE_SIZE = MEDIUM;
--snowpark optimized warehouse
CREATE OR REPLACE WAREHOUSE SNOWPARK_OPT_WH  WITH
  WAREHOUSE_SIZE = 'MEDIUM'
  WAREHOUSE_TYPE = 'SNOWPARK-OPTIMIZED';

-- snowflake internal stage
create stage if not exists ML_MODELS.DS.MODEL_OBJECT   ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

--create role 
CREATE ROLE if not exists FR_SCIENTIST;
--access to role 
grant usage on database ML_MODELS to role FR_SCIENTIST;
grant role FR_SCIENTIST to current_users();
grant all on schema ML_MODELS.DS to role FR_SCIENTIST;
grant all on schema ML_MODELS.FEATURE_STORE to role FR_SCIENTIST;
grant all on schema ML_MODELS.ML_REGISTRY to role FR_SCIENTIST;
grant usage on warehouse ML_FS_WH to role FR_SCIENTIST;
grant read on stage  ML_MODELS.DS.MODEL_STAGE  to role FR_SCIENTIST;
grant write on stage  ML_MODELS.DS.MODEL_STAGE  to role FR_SCIENTIST;

```

**Step 2.** Download the all the [ipynb files](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/tree/main) from the git repository to your local machine
 


<!-- ------------------------ -->
## Generate Realistic Synthetic Data 

We will generate a synthetic dataset consisting of 100,000 rows and 508 columns, including member_id, a binary target variable, and a mix of numerical and categorical features. Using Scikit-Learn's make_classification, we will create 150 base features, then augment the dataset with 200 low-variance features, 150 highly correlated features, 5 categorical columns, and introduce missing values in selected fields.

To reproduce this in your environment, import the notebook [DATA_CREATOR.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/DATA_CREATOR.ipynb), run all cells, and ensure you are using the FR_SCIENTIST role in Snowflake.

Snippet to generate the Pandas Dataframe

```
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification

# Parameters
n_samples = 100000
base_features = 150
low_variance_features = 200
correlated_features = 150
total_numeric_features = base_features + low_variance_features + correlated_features

# Step 1: Generate base numerical features and target
X, y = make_classification(
    n_samples=n_samples,
    n_features=base_features,
    n_informative=60,
    n_redundant=60,
    n_repeated=0,
    n_classes=2,
    random_state=42,
    shuffle=False
)

# Create DataFrame for base features
df = pd.DataFrame(X, columns=[f'FEATURE_{i}' for i in range(base_features)])
df['TARGET'] = y

# Step 2: Add 200 Low-Variance Features
for i in range(1, low_variance_features + 1):
    if i == 1:
        df[f'FEATURE_LOW_VAR_{i}'] = 1  # Constant column
    else:
        df[f'FEATURE_LOW_VAR_{i}'] = np.random.choice([0, 1], size=n_samples, p=[0.98, 0.02])

# Step 3: Add 150 Highly Correlated Features
for i in range(1, correlated_features + 1):
    source_feature = f'FEATURE_{(i - 1) % base_features}'  # Cycle through base features
    df[f'FEATURE_CORR_{i}'] = df[source_feature] * 0.95 + np.random.normal(0, 0.01, n_samples)

# Step 4: Add 5 Specific Categorical Columns with realistic values
df['CAT_1'] = np.random.choice(['Male', 'Female'], size=n_samples)
df['CAT_2'] = np.random.choice(['online', 'retail'], size=n_samples)
df['CAT_3'] = np.random.choice(['tier_1', 'tier_2', 'tier_3'], size=n_samples)
df['CAT_4'] = np.random.choice(['credit', 'debit'], size=n_samples)
df['CAT_5'] = np.random.choice(['single', 'family'], size=n_samples)

# Step 5: Add Missing Values
def add_missing_values(df, cols, fraction=0.05):
    for col in cols:
        missing_indices = df.sample(frac=fraction, random_state=42).index
        df.loc[missing_indices, col] = np.nan
    return df

# Introduce missing values in numeric and categorical columns
numeric_missing = ['FEATURE_0', 'FEATURE_10', 'FEATURE_50', 'FEATURE_LOW_VAR_2', 'FEATURE_CORR_1']
categorical_missing = ['CAT_1', 'CAT_3', 'CAT_5']

df = add_missing_values(df, numeric_missing)
df = add_missing_values(df, categorical_missing)

# Step 6: Add MEMBER_ID Column
df['MEMBER_ID'] = [f'member_{i}' for i in range(len(df))]

# Step 7: Add REF_MMYY Column with random assignment of '042025' or '052025'
df['REF_MMYY'] = np.random.choice(['042025', '052025'], size=n_samples)

# Final shape check
print(f"Final Data Shape: {df.shape}")  # Should be (100000, ~507)

# Optional: Preview the data
# print(df.head())

)

```
Next, we split the full dataset into five DataFrames, evenly distributing the 508 features across them. Each DataFrame includes key columns like member_id and ref_mmyy, and is saved as a Snowflake table to serve as an input source for building the Feature Store.



<!-- ------------------------ -->
## Feature Store Creation in Snowflake

The [Snowflake Feature Store](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview) enables data scientists and ML engineers to create, manage, and reuse machine learning features entirely within Snowflake. It simplifies the end-to-end workflow by keeping features close to the data. In this example, we'll demonstrate how to define entities and create feature views directly from existing Snowflake tables, making your features accessible for both training and inference tasks.

To complete this step, download the notebook [01_FeatureStore_Creation.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/01_FeatureStore_Creation.ipynb) and import it into your Snowflake environment. Once imported, run all cells to execute the setup. 

Let's now walk through the key steps covered in the notebook.

- **Create or Connect to Feature Store**

This code registers a new feature store or connects to an existing one in your Snowflake environment.  
**Note**: Ensure the feature store schema (`fs_schema`) is created beforehand to organize all objects under the correct schema.


```
# Create/Reference Snowflake Feature Store for Training (Development) Environment
try: 
    fs = FeatureStore(
        session=session,        
        database=working_database, 
        name=fs_schema,
        default_warehouse=warehouse
    )
except:
    # need privs to create fs if not exists
    fs = FeatureStore(
        session=session,        
        database=working_database, 
        name=fs_schema, 
        default_warehouse=warehouse,
        creation_mode=CreationMode.CREATE_IF_NOT_EXIST
    )
## define the primary or join keys 
join_keys = ["MEMBER_ID", "REF_MMYY"]
```


- **Register the Feature Views**

This snippet shows how to define entities, which are used to register feature views in the Feature Store.


```
def register_feature(fs, entity_nm, fv_version, feature_df, join_keys):
    """
    Registers an entity and a feature view in the feature store if they do not already exist.

    Parameters:
        fs (FeatureStore): Feature store client instance
        entity_nm (str): Name of the entity
        fv_version (str): Version of the feature view
        feature_df (DataFrame):  DataFrame containing feature data
        join_keys (list): List of join keys for the entity

    Returns:
        FeatureView: The registered or retrieved FeatureView instance
    """

    fv_name = f"FV_FEATURE_{entity_nm}"

    # Check if entity exists
    entity_names_json = fs.list_entities().select(F.to_json(F.array_agg("NAME", True))).collect()[0][0]
    existing_entities = json.loads(entity_names_json)

    if entity_nm not in existing_entities:
        entity_instance = Entity(name=entity_nm, join_keys=join_keys, desc=f"Primary Keys for {entity_nm}")
        fs.register_entity(entity_instance)
    else:
        entity_instance = fs.get_entity(entity_nm)

    # Try to get the FeatureView; register it if it doesn't exist
    try:
        fv_feature_instance = fs.get_feature_view(fv_name, fv_version)
    except:
        fv_feature_instance = FeatureView(
            name=fv_name,
            entities=[entity_instance],
            feature_df=feature_df
        )
        fs.register_feature_view(fv_feature_instance, version=fv_version, block=True)

    return fv_feature_instance
```
- **Snowflake Dataset Creation**

To proceed with feature engineering and dimensionality reduction, we first prepare our dataset.  
[Datasets](https://docs.snowflake.com/en/developer-guide/snowflake-ml/dataset) are new Snowflake schema-level objects specifically designed for machine learning workflows.  
Snowflake Datasets hold collections of data organized into versions.


```
#retrieve the entity views

fv_feature_ent1_instance  = fs.get_feature_view("FV_FEATURE_ENT_1", "V_1")
fv_feature_ent2_instance  = fs.get_feature_view("FV_FEATURE_ENT_2", "V_1")
fv_feature_ent3_instance  = fs.get_feature_view("FV_FEATURE_ENT_3", "V_1")
fv_feature_ent4_instance  = fs.get_feature_view("FV_FEATURE_ENT_4", "V_1")


fv_list = [fv_feature_ent1_instance, 
           fv_feature_ent2_instance, 
           fv_feature_ent3_instance,
           fv_feature_ent4_instance] 

ds_cols = []
slice_list = []
for fv in fv_list:
    fv_cols = list(fv._feature_desc)
    slice_cols = [col for col in fv_cols if col not in ds_cols]
    #fv = fv.slice(slice_cols)
    slice_list.append(fv.slice(slice_cols))
    ds_cols += fv_cols

 ## create DS   
dataset = fs.generate_dataset(
    name=f"{working_database}.{working_schema}.POC_DATASET",
    spine_df=universe_sdf,
    features = slice_list,
    version="V_1",
    output_type="table",
    spine_label_cols=["TARGET"],
    desc="training dataset for ml poc"
) 
```
- **Check the Dataset Table**

You can check the contents of the dataset table **POC_DATASET** using the query below:


```
select * from POC_DATASET;
```

<!-- ------------------------ -->
## Feature Reduction 

In this step, we preprocess the dataset by performing feature reduction, removing redundant or irrelevant features before model training. For feature reduction, we will employ techniques such as Variance Threshold and Correlation Analysis. There are numerous other dimensionality reduction techniques available, which you can explore further [here](https://en.wikipedia.org/wiki/Dimensionality_reduction)

### **Why to do Feature Reduction ?** 

Feature reduction simplifies models, reduces overfitting, and improves computational efficiency.

To complete this step, import the notebook [02_Feature_Reduction.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/02_Feature_Reduction.ipynb) into your Snowflake environment. Once imported, run all cells to execute the setup. 


### **Variance Threshold:**

Removes features with low variance that offer little predictive value, such as those with near-constant values across samples. Here's a code snippet from the notebook

```
from snowflake.snowpark import DataFrame
#from snowflake.snowpark.functions import var_pop

## get all columns with stringType= type
excluded = ['MEMBER_ID', 'TARGET','REF_MMYYYY','CAT_1','CAT_2','CAT_3','CAT_4','CAT_5']
num_cols = [col for col in sdf.columns if col not in excluded]

session.use_warehouse('SNOWPARK_OPT_W')
print(f'number of features before the variance threshold {len(num_cols)}')

# get the
variance_df = sdf.select([F.var_pop(F.col(c)).alias(c) for c in num_cols])

variance_df = variance_df.to_pandas()
cols_below_threshold  = variance_df.columns[(variance_df  < 0.1).all()]
print( f" total cols having variance threshold less than 0.1  is {len(cols_below_threshold)}")

sdf=sdf.drop(*cols_below_threshold )

print(f'number of features after applying the variance threshold  {len(cols_below_threshold)}')

```

### **Correlation Analysis:**
 
Identifies and removes highly correlated features (e.g., correlation > 0.8), which provide redundant information and may lead to instability. Here's a code snippet from the notebook

```
from snowflake.ml.modeling.metrics.correlation import correlation


def snf_correlation_thresholder(df, features, corr_threshold: float):
    assert 0 < corr_threshold <= 1, "Correlation threshold must be in range (0, 1]."
    
    corr_features = set()
    corr_matrix = correlation(df=sdf)

    # Compute pairwise correlations directly in Snowpark
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            if (abs(corr_matrix.iloc[i][j])) >=  corr_threshold:
            #col1, col2 = features[i], features[j]
            #corr_value = df.select(corr(col(col1), col(col2)).alias('corr')).collect()[0]['CORR']
            
           # if corr_value is not None and abs(corr_value) >= corr_threshold:
                # Mark the second feature for removal to avoid keeping highly correlated pairs
                #corr_features.add(col2)
                corr_features.add(features[j])
    
    # Drop correlated features if any
    if corr_features:
        df = df.drop(*corr_features)
        
    return df
```

Finally, we reduce the total number of columns in the dataset from 508 to 150. This refined dataset now serves as the input for the next step: model training. 

<!-- ------------------------ -->
## Model Training 

In this step, we will train the model using Snowflake ML, beginning by creating a preprocessing pipeline that will convert categorical variables into numerical format through one-hot encoding and apply Min-Max scaling to standardize numerical features.

After preprocessing, we will experiment with several modeling techniques, including XGBoost and Random Forest. Model tuning will be conducted using GridSearch, and all training will be executed within Snowflake ML.

To complete this step, import the notebook [03_Model_Training.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/03_Model_Training.ipynb) into your Snowflake environment. Once imported, run all cells to execute the setup. 


### **Preprocessor Pipeline**

Here’s the code snippet for the preprocessing pipeline.  
The pipeline saves the model as a `.joblib` file in a Snowflake stage for reusability.


```
from snowflake.ml.modeling.pipeline import Pipeline 
from snowflake.ml.modeling.preprocessing import MinMaxScaler , OneHotEncoder

preprocessing_pipeline = Pipeline(
    steps=[
        
        ("OHE",
         OneHotEncoder(input_cols=cat_cols,
                       output_cols=cat_cols,
                       drop_input_cols=True,
                       drop="first",
                       handle_unknown="ignore",)
         ),
        ("MMS",MinMaxScaler(clip=True, 
                            input_cols=num_cols,
                            output_cols=num_cols,))
    ]

)

joblib.dump(preprocessing_pipeline, 'preprocessing_pipeline.joblib')
#upload
session.file.put('preprocessing_pipeline.joblib',
                 stage,auto_compress=False)
```
### **XGBoost Classifier in Snowflake ML**

Snippet for training an XGBoost Classifier using Snowflake ML:

```
from snowflake.ml.modeling.xgboost import XGBClassifier
XGB_Classifier= XGBClassifier(
    input_cols=FEATURE_COLS ,
    label_cols=label_col,
    output_cols=OUTPUT_COLUMNS
)
# Train
XGB_Classifier.fit(train_df)

#  evaluation 
predict_on_training_data = XGB_Classifier.predict(train_df)

training_accuracy = accuracy_score(df=predict_on_training_data, 
                                   y_true_col_names=["TARGET"],
                                   y_pred_col_names=["PREDICTED_TARGET"])


result = XGB_Classifier.predict(test_df)
```

### **Random Forest Classifier in Snowflake ML**

Snippet for training a Random Forest Classifier using Snowflake ML:
```
from snowflake.ml.modeling.ensemble import RandomForestClassifier

FEATURE_COLS = get_features(train_df, label_col)
OUTPUT_COLUMNS="PREDICTED_TARGET"
label_col='TARGET'


RandomForest= RandomForestClassifier(
    input_cols=FEATURE_COLS ,
    label_cols=label_col,
    output_cols=OUTPUT_COLUMNS
)
# Train
RandomForest.fit(train_df)
```
### **Model Evaluation**

Run predictions on the training dataset using the trained Random Forest model:

```
predict_on_training_data = RandomForest.predict(train_df)

```
### **Grid Search in Snowflake ML**

Snippet for performing Grid Search hyperparameter tuning using Snowflake ML:

```
## parameter grid 
FEATURE_COLS = get_features(train_df, label_col)
OUTPUT_COLUMNS="PREDICTED_TARGET"
label_col='TARGET'



parameters = {
        "n_estimators": [100, 300, 500],
        "learning_rate": [0.1, 0.3, 0.5],
        "max_depth": list(range(3, 5, 1)),
        "min_child_weight": list(range(3, 5, 1)),
    }
    
n_folds = 5

estimator = XGBClassifier()

GridSearch_clf = GridSearchCV(estimator= estimator,
                   param_grid=parameters ,
                   cv = n_folds,
                   input_cols=FEATURE_COLS ,
                   label_cols=label_col,
                   output_cols=OUTPUT_COLUMNS
                   )
GridSearch_clf.fit(train_df)

result = GridSearch_clf.predict(test_df )
print(GridSearch_clf.to_sklearn().best_estimator_)
```

** Model Metrics **
Snippet showing how to get the model metrics natively using Snowflake ML

```
# snowpark ML metrics
from snowflake.ml.modeling.metrics import accuracy_score,f1_score,precision_score,roc_auc_score,roc_curve,recall_score

metrics = {
"accuracy":accuracy_score(df=result ,
                          y_true_col_names="TARGET", 
                          y_pred_col_names="PREDICTED_TARGET"),

"precision":precision_score(df=result,
                            y_true_col_names="TARGET", 
                            y_pred_col_names="PREDICTED_TARGET"),


"recall": recall_score(df=result, 
                       y_true_col_names="TARGET",
                       y_pred_col_names="PREDICTED_TARGET"),



"f1_score":f1_score(df=result,
                   y_true_col_names="TARGET",
                   y_pred_col_names="PREDICTED_TARGET"),
"confusion_matrix":confusion_matrix(df=result, 
                                    y_true_col_name="TARGET",
                                    y_pred_col_name="PREDICTED_TARGET").tolist()
}

```

**Loging Model into Model registry**
Snippet to register a model in Snowflake ML

```
# Get sample input data to pass into the registry logging function
X = train_df.select(FEATURE_COLS).limit(100)
db = working_database 
schema =model_registry_schema 

# Create a registry and log the model
reg = Registry(session=session, database_name=db, schema_name=schema)


model_name = "ML_XGBOOST_MODEL"
version_name = "v1"

# Let's first log the very first model we trained
mv = reg.log_model(
    model_name=model_name,
    version_name=version_name,
    model= XGB_Classifier,
    metrics=metrics ,
    sample_input_data=X, # to provide the feature schema
)


# Add a description
mv.comment = """This is the first iteration of our ml poc  model. 
It is used for demo purposes and it is simple xgboost model."""


# Let's confirm they were added
reg.get_model(model_name).show_versions()
```

<!-- ------------------------ -->
## Model Inferencing and Scheduling

In this section, you'll learn how to perform batch inferencing using Snowflake ML by:
* Leveraging features stored in the Feature Store 
* Loading the model signature from the Snowflake Model Registry 
* Running predictions at scale within Snowflake 

This approach enables efficient generation of model predictions for large datasets, all within the Snowflake platform. Additionally, the notebook can be [scheduled](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-schedule) to run at regular intervals, facilitating fully automated and production-grade batch scoring workflows.

To proceed, please import the notebook [04_Batch_Inferencing.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/blob/main/04_Batch_Inferencing.ipynb) and run all the cells. Let’s now dive into the code details.

### 1. Retrieve Features from the Feature Store

Retrieve features from the Feature Store using the model signature of the selected model from the Model Registry.

Below is the code snippet from the notebook:

```
fv_feature_ent1_instance  = fs.get_feature_view("FV_FEATURE_ENT_1", "V_1")
fv_feature_ent2_instance  = fs.get_feature_view("FV_FEATURE_ENT_2", "V_1")
fv_feature_ent3_instance  = fs.get_feature_view("FV_FEATURE_ENT_3", "V_1")
fv_feature_ent4_instance  = fs.get_feature_view("FV_FEATURE_ENT_4", "V_1")


fv_list = [fv_feature_ent1_instance, 
           fv_feature_ent2_instance, 
           fv_feature_ent3_instance,
           fv_feature_ent4_instance] 


universe_tbl = '.'.join([input_database, input_schema, 'DEMO_TARGETS_TBL'])
universe_sdf            = session.table(universe_tbl).filter(F.col("REF_MMYY") == ref_mmyyyy)


#get the input signature from the desired model from the model registr

reg = Registry(session, database_name = working_database,schema_name = model_registry_schema)
reg.show_models()
mv = reg.get_model(model_name).version("v1")
# the input signature of model
input_signature = mv.show_functions()[0].get("signature").inputs
input_cols = [c.name for c in input_signature]
```
### 2 Create Dataset for Inference

Snippet of code to generate the dataset used for inference:
```
dataset = fs.generate_dataset(
    name=f"{working_database}.{working_schema}.INFERENCE_DATASET",
    spine_df=universe_sdf,
    features = slice_list,
    version=dataset_version,
    #output_type="table",
    spine_label_cols=["TARGET"],
    desc="training dataset for ml demo"
)    
```
### 3. Run Preprocessing

Snippet of code to run preprocessing on unseen or inference data:
```
session.file.get(f'{stage}/preprocessing_pipeline.joblib', '/tmp')
PIPELINE_FILE = '/tmp/preprocessing_pipeline.joblib'

preprocessing_pipeline = joblib.load(PIPELINE_FILE)

df=preprocessing_pipeline.fit(df).transform(df)
```
### 3. Run Prediction

Snippet of code to run prediction on an unseen or prediction dataset:
```
prediction_result = mv.run(df, function_name ="PREDICT")
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You’ve successfully built an end-to-end customer targeting model in a Snowflake Notebook and logged the trained model to the Snowflake ML Registry, making it ready for inference and future use.

### What You Learned
- How to generate realistic synthetic data in Snowpark and save it as Snowflake tables.
- How to define entities and register feature views in the Feature Store.
- How to perform feature engineering and feature reduction.
- How to train and tune models within Snowflake ML.
- How to log and register models in the Snowflake ML registry.
- How to run predictions on new data using the registered model within Snowflake.



### Related Resources
- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-end-to-end-customer-targeting-on-snowflake-ml/tree/main)
- [Snowflake Logging Custom Models](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/bring-your-own-model-types)
- [Snowflake ML](/en/data-cloud/snowflake-ml/)
- [classification Model](https://en.wikipedia.org/wiki/Category:Classification_algorithms)


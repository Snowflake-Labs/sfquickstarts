author: Avni Jain, Sarathi Balakrishnan, and Avinash Joshi
id: ml-batch-inference-with-vision-models
language: en
summary: Learn how to run batch inference on images using Vision Models in Snowflake
categories: snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/ml-functions
environments: web
status: Published
fork repo link: https://github.com/sfc-gh-avjain/sfquickstarts/tree/ajain-ml-batch-inference-with-vision-models/site/sfguides/src/ml-batch-inference-with-vision-models


# ML Batch Inference with Vision Models in Snowflake
<!-- ------------------------ -->
## Overview 

Snowflake Batch Inference enables efficient, large-scale model inference on static or periodically updated datasets by using Snowpark Container Services (SPCS) to provide high throughput and cost-efficiency. The API is designed to handle massive workloads, such as executing inference over millions or billions of rows or processing unstructured data like images, audio, and video files. Batch jobs are executed as discrete, asynchronous stages in a pipeline that can be easily integrated into orchestration tools like Airflow DAGs or Snowflake Tasks. Some common use cases include processing large scales of medical images, insurance claims, financial reports, video/audio files, and more!

In this quickstart, you'll learn how to import a Vision Model from HuggingFace into Snowflake's Model Registry directly through the UI and run batch inference on an image dataset. We'll use the OCR-VQA dataset to demonstrate how VLMs can answer questions about images. The evaluation dataset consists of book cover images paired with corresponding question-answer sets, enabling the model to perform batch inference by analyzing visual features to generate contextual responses

### Prerequisites
- A Snowflake account with necessary access
- Access to Snowpark Container Services (for GPU compute)
- Basic familiarity with Python and SQL

### What You'll Learn 
- How to set up Snowflake resources for ML workloads (compute pools, stages)
- How to import a HuggingFace model into Snowflake's Model Registry through the UI
- How to prepare image data for batch inference
- How to run batch inference using the Model Registry API
- How to evaluate model predictions

### What You'll Need 
- A Snowflake account with Snowpark Container Services enabled
- A GPU compute pool (GPU_NV_M or similar)

### What You'll Build 
- A complete pipeline for visual question answering using batch inference
- An evaluation framework for measuring model accuracy

<!-- ------------------------ -->
## Environment Setup

First, let's create the necessary Snowflake objects for our ML workflow.

### Create Database and Schema

```sql
CREATE DATABASE IF NOT EXISTS VQA_DEMO_DB;
CREATE SCHEMA IF NOT EXISTS VQA_DEMO_DB.VQA;

USE DATABASE VQA_DEMO_DB;
USE SCHEMA VQA;
```

### Create External Stage for S3 Data

The dataset (images and CSV) is hosted in a public S3 bucket. We'll create an external stage pointing to it:

```sql
CREATE OR REPLACE STAGE VQA_DEMO_DB.VQA.S3_DATA_STAGE
    URL = 's3://sfquickstarts/sfguide_ml_batch_inference_with_vision_models/'
    DIRECTORY = (ENABLE = TRUE AUTO_REFRESH = FALSE);
```

### Create Stages for Data Storage

```sql
-- Internal stage for images (copied from S3)
CREATE STAGE IF NOT EXISTS VQA_DEMO_DB.VQA.IMAGES_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- Stage for inference outputs
CREATE STAGE IF NOT EXISTS VQA_DEMO_DB.VQA.DATA_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

### Create GPU Compute Pool

```sql
CREATE COMPUTE POOL IF NOT EXISTS GPU_INFERENCE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = GPU_NV_M
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 300;
```

### Create File Format and Tables

```sql
CREATE FILE FORMAT IF NOT EXISTS VQA_DEMO_DB.VQA.PARQUET_FORMAT
    TYPE = 'PARQUET';

CREATE FILE FORMAT IF NOT EXISTS VQA_DEMO_DB.VQA.CSV_FORMAT
    TYPE = 'CSV'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    ESCAPE_UNENCLOSED_FIELD = NONE;

CREATE TABLE IF NOT EXISTS VQA_DEMO_DB.VQA.INFERENCE_RESULTS (
    ID INT,
    QUESTION VARCHAR,
    EXPECTED_ANSWER VARCHAR,
    PREDICTED_ANSWER VARCHAR,
    QUESTION_TYPE VARCHAR,
    IS_CORRECT BOOLEAN
);
```

<!-- ------------------------ -->
## Import Model from HuggingFace

Now we'll import a Vision Model from HuggingFace. We'll use **LLaVA-v1.6-Mistral-7B**, a powerful model for visual understanding tasks.

### Option 1: Import via Snowsight UI

1. Navigate to **AI & ML** → **Models** in Snowsight
2. Click **+ Import Model**
3. Select **HuggingFace** as the source
4. Configure the import:
   - **Model ID**: `llava-hf/llava-v1.6-mistral-7b-hf`
   - **Task**: `Image Text to Text`
   - **Model Name**: `LLAVA_V1_6_MISTRAL_7B_HF`
   - **Version Name**: `v1`
   - **Database**: `VQA_DEMO_DB`
   - **Schema**: `VQA`
5. Click **Import** and wait for completion (~15-30 minutes)

<img src="import_model.png" width="30%">

### Verify the Model

```sql
SHOW MODELS IN SCHEMA VQA_DEMO_DB.VQA;
SHOW VERSIONS IN MODEL VQA_DEMO_DB.VQA.LLAVA_V1_6_MISTRAL_7B_HF;
```
<img src="show_models.png" width="50%">
<!-- ------------------------ -->

## Prepare the Dataset

We'll use the OCR-VQA dataset, which contains images of book covers with questions about the text on them. The images and a pre-built CSV of Q&A records are hosted in a public S3 bucket.

### Copy Images from S3 to Internal Stage

```python
session.sql("COPY FILES INTO @IMAGES_STAGE/ FROM @S3_DATA_STAGE/IMAGES/").collect()

print("Copied images from S3 to internal stage")
result = session.sql("LS @IMAGES_STAGE").collect()
print(f"Total images in stage: {len(result)}")
```

### Load Q&A Records from S3 CSV

```python
import json
import pandas as pd

df_vqa = session.sql("""
SELECT 
    $1::INT AS ID,
    $2::INT AS IMAGE_IDX,
    $3::STRING AS IMAGE_PATH,
    $4::STRING AS QUESTION,
    $5::STRING AS ANSWER,
    $6::STRING AS QUESTION_TYPE
FROM @S3_DATA_STAGE/vqa_dataset.csv (FILE_FORMAT => 'CSV_FORMAT')
""").to_pandas()

print(f"Loaded {len(df_vqa)} Q&A records from S3")
```
<img src="q_and_a.png" width="30%">

### Format for Batch Inference

```python
def create_chat_message(row):
    return json.dumps([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{row['QUESTION']} Answer briefly in a few words."},
                {"type": "image_url", "image_url": {"url": row['IMAGE_PATH']}}
            ]
        }
    ])

df_vqa['MESSAGES'] = df_vqa.apply(create_chat_message, axis=1)

input_df = session.create_dataframe(df_vqa[['ID', 'MESSAGES', 'QUESTION', 'ANSWER', 'QUESTION_TYPE']])
input_df.write.mode("overwrite").save_as_table("VQA_DEMO_DB.VQA.INFERENCE_INPUT")
```
<img src="sample_format.png" width="30%">

<!-- ------------------------ -->
## Run Batch Inference

Now let's run batch inference using the imported model.

### Load the Model

```python
from snowflake.snowpark.context import get_active_session
from snowflake.ml.registry import Registry

session = get_active_session()
session.sql("USE DATABASE VQA_DEMO_DB").collect()
session.sql("USE SCHEMA VQA").collect()

reg = Registry(session=session, database_name="VQA_DEMO_DB", schema_name="VQA")
model = reg.get_model("LLAVA_V1_6_MISTRAL_7B_HF")
mv = model.default

print(f"Model loaded: {model.name}")
```

### Run Batch Inference

```python
from snowflake.ml.model.batch import JobSpec, OutputSpec, SaveMode, InputSpec
import time

OUTPUT_STAGE = "@VQA_DEMO_DB.VQA.DATA_STAGE/inference_output/"
COMPUTE_POOL = "GPU_INFERENCE_POOL"

# Load test data
test_data = session.table("VQA_DEMO_DB.VQA.INFERENCE_INPUT").to_pandas()
test_data_subset = test_data.head(10)  # Start with 10 samples
input_df = session.create_dataframe(test_data_subset[['MESSAGES']])

print(f"Starting batch inference on {input_df.count()} samples...")
start_time = time.time()

job = mv.run_batch(
    compute_pool=COMPUTE_POOL,
    X=input_df,
    input_spec=InputSpec(params={"temperature": 0.1, "max_completion_tokens": 100}),
    output_spec=OutputSpec(stage_location=OUTPUT_STAGE, mode=SaveMode.OVERWRITE),
    job_spec=JobSpec(gpu_requests="1")
)

print("Job submitted. Waiting for completion...")
job.wait()

elapsed = time.time() - start_time
print(f"Completed in {elapsed:.1f}s")
```

<!-- ------------------------ -->
## Evaluate Results

Let's evaluate how well the model performed on our test questions.

### Load and Parse Results

```python
import json

results_df = session.read.option("pattern", ".*\\.parquet").parquet(OUTPUT_STAGE)
results_pd = results_df.to_pandas()

def extract_prediction(row):
    try:
        for col in results_pd.columns:
            data = row.get(col)
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    pass
            if isinstance(data, dict) and 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict) and 'message' in data[0]:
                    return data[0]['message']['content'].strip()
    except:
        pass
    return None

results_pd['PREDICTION'] = results_pd.apply(extract_prediction, axis=1)
```

### Calculate Accuracy

```python
import re

def normalize(text):
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def is_correct(predicted, expected, q_type):
    if not predicted:
        return False
    
    pred = normalize(predicted)
    exp = normalize(expected)
    
    if exp in pred:
        return True
    for word in exp.split():
        if len(word) > 3 and word in pred:
            return True
    return False

eval_data = test_data_subset.copy()
eval_data['PREDICTED'] = results_pd['PREDICTION'].values
eval_data['IS_CORRECT'] = eval_data.apply(
    lambda r: is_correct(r['PREDICTED'], r['ANSWER'], r['QUESTION_TYPE']), axis=1
)

accuracy = eval_data['IS_CORRECT'].mean() * 100

print("=" * 50)
print("EVALUATION RESULTS")
print("=" * 50)
print(f"Overall Accuracy: {accuracy:.1f}%")
print(f"Correct: {eval_data['IS_CORRECT'].sum()}/{len(eval_data)}")
print("=" * 50)
```

### View Detailed Results

```python
for _, row in eval_data.iterrows():
    status = "✓" if row['IS_CORRECT'] else "✗"
    print(f"\n{status} Q: {row['QUESTION']}")
    print(f"   Expected: {row['ANSWER']}")
    print(f"   Got: {str(row['PREDICTED'])[:100]}")
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully built a batch inference pipeline for visual question answering using Snowflake's Model Registry and a Vision Model from HuggingFace.

### What You Learned
- How to set up Snowflake resources (compute pools, stages) for ML workloads
- How to import HuggingFace models into Snowflake's Model Registry
- How to prepare image datasets for batch inference
- How to run and evaluate batch inference jobs

### Related Resources
- [Batch Inference Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/inference/batch-inference-jobs)
- [Snowflake Model Registry UI Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/snowsight-ui)
- [Snowflake ML Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)

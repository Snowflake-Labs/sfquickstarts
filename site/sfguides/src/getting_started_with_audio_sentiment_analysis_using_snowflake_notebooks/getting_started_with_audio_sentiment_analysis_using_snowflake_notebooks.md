id: getting\_started\_with\_audio\_sentiment\_analysis   
summary: Getting Started with Audio Sentiment Analysis using Snowflake Notebooks   
categories: featured,getting-started,data-science-&-ml,app-development   
environments: web   
status: Published feedback link: [https://github.com/Snowflake-Labs/sfguides/issues](https://github.com/Snowflake-Labs/sfguides/issues)   
tags: Getting Started, Snowflake Notebooks, Machine Learning, Audio Processing   
authors: James Cha-Earley

# Getting Started with Audio Sentiment Analysis using Snowflake Notebooks 

## Overview

Duration: 5

In this quickstart, you'll learn how to build an end-to-end application that analyzes audio files for emotional tone and sentiment using [Snowflake Notebooks on Container Runtime](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs). The application combines audio processing, speech recognition, and sentiment analysis to create comprehensive insights from audio data.

### What You'll Learn

- Setting up audio processing in [Snowflake ML](https://www.snowflake.com/en/data-cloud/snowflake-ml/) using PyTorch and Hugging Face  
- Extracting emotional tone from audio using wav2vec2  
- Transcribing audio with Whisper model  
- Performing sentiment analysis using [Snowflake Cortex AI](https://www.snowflake.com/en/data-cloud/cortex/)  
- Comparing emotional tone with sentiment scores

### What You'll Build

A full-stack application that enables users to:

- Process audio files for emotional tone analysis  
- Generate text transcripts from audio  
- Analyze sentiment in transcribed text  
- Compare emotional tone with sentiment scores  
- View comprehensive analysis results

### Prerequisites

- Snowflake account (non-trial) with:  
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs)  
  - [Anaconda Packages](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages)  
  - [Cortex Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)

## Setting Up Notebook with Container Runtime 

Duration: 10

Before we begin processing audio files, we need to set up our notebook to use container runtime for [building ML models](https://www.snowflake.com/en/data-cloud/snowflake-ml/).

### Create a New Notebook with Container Runtime

1. Sign in to Snowsight  
2. Select Notebooks  
3. Click "+ Notebook"  
4. Fill in the details:  
   - Enter a name for your notebook  
   - Select database and schema to store the notebook  
   - For Python environment, select "Run on container"  
   - Choose Runtime type: For audio processing, select "GPU" runtime  
   - Select a Compute pool  
   - Choose a warehouse for SQL and Snowpark queries  
5. Click "Create"

aside positive Note: Database and schema selections are only for storing your notebook. You can query any database/schema you have access to from within the notebook.

### Configure External Access

To install additional packages like `transformers` and `torchaudio`, we need to set up external access:

1. Click the "Notebook actions" menu (top right)  
2. Select "Notebook settings"  
3. Go to "External access" tab  
4. Enable required external access integrations  
5. Restart notebook when prompted

### Install Required Packages

Once external access is configured, install needed packages:

```py
!pip install transformers torch torchaudio librosa
```

## Setup Environment

Duration: 10

Now we'll set up our Python environment with all necessary imports and configurations.

```py
import torch
import torchaudio
import random
import librosa
import pandas as pd

from transformers import pipeline

from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
from snowflake.cortex import Sentiment 

session = get_active_session()
root = Root(session)

database_name = session.get_current_database()
schema_name = session.get_current_schema()
stage_name = 'SUPPORT_CALLS'
database = root.databases[database_name]
```

## Create Stage and Upload Audio Files

Duration: 10

First, let's create a stage to store our audio files:

```
-- Create stage for audio files
CREATE STAGE IF NOT EXISTS audio_files
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = true);
```

Upload your audio files:

1. Navigate to Data \> Databases \> \[Your Database\] \> audio\_files \> Stages  
2. Click "Upload Files" button  
3. Select your audio files  
4. Verify upload:

```
ls @audio_files;
```

## Audio Processing Pipeline

Duration: 15

Set up the main processing function that combines multiple models:

```py
def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

#For consistent output for demo
set_seed(1280)

# Create empty lists to store the results
results = []

# Initialize both pipelines
audio_pipeline = pipeline("audio-classification", 
    model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition", 
    device="cuda")
whisper_pipeline = pipeline("automatic-speech-recognition", 
    model="openai/whisper-base", 
    device="cuda")
```

## Process Audio Files

Duration: 15

Now let's process our audio files:

```py
files = session.sql(f"LIST @{stage_name}").collect()
file_names = [file['name'].split('/')[-1] for file in files]

for file_name in file_names:
    session.file.get(f'@{stage_name}/{file_name}', "downloads/")
    audio, rate = librosa.load(f'downloads/{file_name}', sr=16000, mono=True)
    
    # Get emotional tone
    result = audio_pipeline(audio)
    emotion = sorted(result, key=lambda x: x['score'], reverse=True)[0]
    
    # Get transcript and sentiment
    transcript = whisper_pipeline(audio)
    sentiment_score = Sentiment(transcript['text'])
    
    # Determine if emotion and sentiment match
    match = "Unknown"
    if emotion['label'] == "angry":
        match = "Match" if sentiment_score < 0 else "Do Not Match"
    elif emotion['label'] == "happy":
        match = "Match" if sentiment_score > 0 else "Do Not Match"
    
    # Store results
    results.append({
        'File': file_name,
        'Emotion': emotion['label'],
        'Emotion_Score': round(emotion['score'], 3),
        'Transcript': transcript['text'],
        'Sentiment_Score': sentiment_score,
        'Tone_Sentiment_Match': match
    })

# Create DataFrame
df = pd.DataFrame(results)
print(df)
```

## Important Considerations

Duration: 5

When using Snowflake Notebooks on Container Runtime:

### Resource Management

- Each compute node is limited to running one notebook per user at a time  
- Set MAX\_NODES \> 1 when creating compute pools  
- Shut down notebook when not in use via "End session" to free resources  
- Default idle timeout is 1 hour (configurable up to 72 hours)

### Cost Considerations

- Both warehouse compute and SPCS compute costs may apply  
- SQL cells run on warehouse  
- Python compute runs on container runtime

### Best Practices

- Monitor resource usage  
- Clean up resources after use  
- Use appropriate compute pool sizes  
- Install packages at notebook startup  
- Handle errors gracefully

## Conclusion and Resources

Duration: 5

Congratulations\! You've successfully built an end-to-end audio analysis application in Snowflake that combines emotional tone detection, speech recognition, and sentiment analysis. Using Snowflake Notebooks with Container Runtime, you've implemented a solution that processes audio files and provides deep insights into both spoken tone and textual sentiment.

### What You Learned

- How to set up Container Runtime in Snowflake Notebooks  
- How to implement audio processing using PyTorch and Hugging Face with [Snowflake ML](https://www.snowflake.com/en/data-cloud/snowflake-ml/)  
- How to use pre-trained models for emotion recognition and speech-to-text  
- How to perform sentiment analysis using [Snowflake Cortex](https://www.snowflake.com/en/data-cloud/cortex/)  
- How to compare and analyze multiple aspects of audio communication

### Related Resources

Webpages

* [Snowflake ML](https://www.snowflake.com/en/data-cloud/snowflake-ml/)  
* [Snowflake Cortex AI](https://www.snowflake.com/en/data-cloud/cortex/)

Documentation:

- [Snowflake Notebooks on Container Runtime Overview](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs)  
- [Cortex AI Documentation](https://docs.snowflake.com/en/guides-overview-ai-features)  
- [PyTorch Audio Processing Guide](https://pytorch.org/audio/stable/index.html)

Sample Code & Guides:

- [Container Runtime Best Practices](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)  
- [External Access Setup Guide](https://docs.snowflake.com/en/developer-guide/external-network-access/external-network-access-overview)  
- [Hugging Face Transformers Documentation](https://huggingface.co/docs/transformers/index)  
- [Snowpark Python Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)

Related Quickstarts

* [Getting Started with Snowflake Notebook Container Runtime](https://quickstarts.snowflake.com/guide/notebook-container-runtime/index.html#4)  
* [Train an XGBoost Model with GPUs using Snowflake Notebooks](https://quickstarts.snowflake.com/guide/train-an-xgboost-model-with-gpus-using-snowflake-notebooks/index.html#0)  
* [Scale Embeddings with Snowflake Notebooks on Container Runtime](https://quickstarts.snowflake.com/guide/scale-embeddings-with-snowflake-notebooks-on-container-runtime/index.html?index=..%2F..index#0)  
* [Getting Started with Running Distributed PyTorch Models on Snowflake](https://quickstarts.snowflake.com/guide/getting-started-with-running-distributed-pytorch-models-on-snowflake/#0)  
* [Defect Detection Using Distributed PyTorch With Snowflake Notebooks](https://quickstarts.snowflake.com/guide/defect_detection_using_distributed_pyTorch_with_snowflake_notebooks/index.html?index=..%2F..index#0)

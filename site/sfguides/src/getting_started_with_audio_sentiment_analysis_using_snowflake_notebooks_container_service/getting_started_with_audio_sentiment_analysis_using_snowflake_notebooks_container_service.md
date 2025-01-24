author: James Cha-Earley
id: getting_started_with_audio_sentiment_analysis_using_snowflake_notebooks_container_service
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Getting Started with 🎤 Audio Sentiment Analysis using Snowflake Notebooks Container Services 📊

Transform audio files into actionable insights by analyzing emotional tone and sentiment using Snowflake Notebooks! ⚡️

This notebook demonstrates how to build an end-to-end application that:
1. Processes audio files using PyTorch and Hugging Face pipelines
2. Extracts emotional tone and transcripts from audio
3. Performs sentiment analysis on transcribed text
4. Compares emotional tone with sentiment scores

## Setting Up Your Environment 🎒

First, we'll install required packages and import dependencies:
- `torch`, `torchaudio`: For audio processing
- `librosa`: For loading and manipulating audio files
- `transformers`: For accessing pre-trained models
- Snowpark packages for interacting with Snowflake

```python
!pip install librosa transformers torch torchaudio
```

## Configuring the Environment 🔧

Set up Snowflake session and import required packages:

```python
import torch
import torchaudio
import random
import librosa
import pandas as pd

from transformers import pipeline

from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
from snowflake.ml.python import Sentiment 

session = get_active_session()
root = Root(session)

database_name = session.get_current_database()
schema_name = session.get_current_schema()
stage_name = 'SUPPORT_CALLS'
database = root.databases[database_name]
```

## Processing Audio Files 🎧

The main processing function:
1. Loads audio files from Snowflake stage
2. Analyzes emotional tone using wav2vec2 model
3. Transcribes audio using Whisper model
4. Performs sentiment analysis on transcripts
5. Compares emotional tone with sentiment scores

Key components:
- Audio classification pipeline using `wav2vec2-lg-xlsr-en-speech-emotion-recognition`
- Speech recognition using `whisper-base`
- Sentiment analysis using Snowflake ML

```python
def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(1280)

results = []

audio_pipeline = pipeline("audio-classification", 
                        model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition", 
                        device="cuda")
whisper_pipeline = pipeline("automatic-speech-recognition", 
                          model="openai/whisper-base", 
                          device="cuda")

# Process files and generate insights
[Additional processing code...]
```

The output DataFrame includes:
- File name
- Detected emotion and confidence score
- Transcribed text
- Sentiment score
- Tone-sentiment match indicator

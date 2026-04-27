id: getting-started-with-audio-sentiment-analysis-using-snowflake-notebooks
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/build, snowflake-site:taxonomy/snowflake-feature/ml-functions
language: en
summary: Analyze audio sentiment in Snowflake Notebooks for call center analytics, voice-of-customer insights, and emotion detection.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
author: James Cha-Earley

# Getting Started with Audio Sentiment Analysis using Snowflake Notebooks 

## Overview


In this quickstart, you'll learn how to build an end-to-end application that analyzes audio files for emotional tone and sentiment using [Snowflake Notebooks on Container Runtime](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs). The application combines audio processing, speech recognition, and sentiment analysis to create comprehensive insights from audio data.

### What is Container Runtime? 

Snowflake Notebooks on Container Runtime enable advanced data science and machine learning workflows directly within Snowflake. Powered by Snowpark Container Services, it provides a flexible environment to build and operationalize various workloads, especially those requiring Python packages from multiple sources and powerful compute resources, including CPUs and GPUs. With this Snowflake-native experience, you can process audio, perform speech recognition, and execute sentiment analysis while seamlessly running SQL queries. ***NOTE: This feature is currently in Public Preview.***

Learn more about [Container Runtime](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs).

### What is wav2vec2?

Wav2vec2 is a state-of-the-art framework for self-supervised learning of speech representations. Developed by Facebook AI, it's specifically designed for speech recognition tasks but has been adapted for various audio analysis tasks including emotion recognition. The model we use in this guide, "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition", is fine-tuned for detecting emotions in speech, capable of identifying emotions like happiness, sadness, anger, and neutral tones from audio input.

Learn more about [wav2vec2](https://huggingface.co/facebook/wav2vec2-base).

### What is Snowflake Cortex?

Snowflake Cortex is a suite of AI features that use large language models (LLMs) to understand unstructured data, answer freeform questions, and provide intelligent assistance. In this guide, we use Cortex's sentiment analysis capabilities to analyze the emotional content of transcribed speech.

Learn more about [Snowflake Cortex](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview).

### What is Whisper?

OpenAI's Whisper is an open-source automatic speech recognition (ASR) model designed for high-quality transcription and translation of spoken language. Trained on diverse multilingual data, it handles various languages, accents, and challenging audio conditions like background noise. Whisper supports transcription, language detection, and translation to English, making it versatile for applications such as subtitles, accessibility tools, and voice interfaces.

Learn more about [Whisper](https://openai.com/research/whisper).

### What You'll Learn

- Setting up audio processing in [Snowflake ML](/en/data-cloud/snowflake-ml/) using PyTorch and Hugging Face  
- Extracting emotional tone from audio using wav2vec2
- Transcribing audio with Whisper model
- Performing sentiment analysis using [Snowflake Cortex AI](/en/data-cloud/cortex/)
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

## Setup Workspace

**Step 1.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-audio-sentiment-analysis-using-snowflake-notebooks/blob/main/setup.sql) to execute all statements in order from top to bottom.

**Step 2.** In Snowsight, switch your user role to `AUDIO_CONTAINER_RUNTIME_ROLE`.

**Step 3.** Click on [sfguide_getting_started_with_audio_sentiment_analysis_using_snowflake_notebooksipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-audio-sentiment-analysis-using-snowflake-notebooks/blob/main/sfguide_getting_started_with_audio_sentiment_analysis_using_snowflake_notebooks.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)

**Step 4.** In Snowsight:

* On the left hand navigation menu, click on **Projects » Notebooks**
* On the top right, click on **Notebook** down arrow and select **Import .ipynb file** from the dropdown menu
* Select *sfguide_getting_started_with_audio_sentiment_analysis_using_snowflake_notebooks.ipynb** file you downloaded in the step above
* In the Create Notebook popup:
    * For Notebook location, select `AUDIO_SENTIMENT_DB` and `AUDIO_SCHEMA`
    * For SQL warehouse, select `AUDIO_WH_S`
    * For Python environment, select `Run on container`
    * For Runtime, select `GPU Runtime`
    * For Compute pool, select `GPU_POOL`
* Click on **Create** button

**Step 5.** Open Notebook

* Click in the three dots at the very top-right corner and select `Notebook settings` >> `External access`
* Turn on **ALLOW_ALL_ACCESS_INTEGRATION** and **HUGGINGFACE_ACCESS_INTEGRATION**
* Click on **Save** button
* Click on **Start** button on top right

> 
> NOTE: At this point, the container service will take about 5-7 minutes to start. You will not be able to proceed unless the status changes from **Starting** to **Active**.

## Audio File Requirements


### Supported Audio Formats
- WAV (recommended)
- MP3
- FLAC
- OGG
- M4A

### Audio Specifications
For best results, your audio files should have:
- Sample rate: 16kHz or higher
- Bit depth: 16-bit or higher
- Channels: Mono (stereo will be converted to mono)
- File size: Up to 25MB

### Best Practices
For optimal analysis:
- Use clear recordings with minimal background noise
- Ensure speech is clearly audible
- Avoid multiple speakers talking simultaneously
- Record in a quiet environment
- Use lossless formats (WAV/FLAC) when possible

### Common Use Cases
This system works well for analyzing:
- Customer service calls
- Meeting recordings
- Voice messages
- Interview recordings
- Support interactions
- Training materials

> 
> TIP: If your audio files don't meet these specifications, consider using audio processing tools like ffmpeg to convert them to the recommended format before analysis.

## Run Notebook


> 
> PREREQUISITE: Successful completion of steps outlined under **Setup**.

Here's the walkthrough of the notebook cells and their functions:

**Cell 1: Package Installation**
* Installs required packages:
  - `torch`: For deep learning and neural network operations
  - `librosa`: For loading and manipulating audio files
  - `transformers`: For accessing pre-trained models

**Cell 2: Environment Setup**
* Imports required Python libraries
* Sets up Snowflake session
* Configures stage name and device (GPU/CPU)
* Initializes connection to Snowflake services

**Cell 3: Audio Processing Configuration**
* Sets up the main processing function that:
  1. Loads audio files from Snowflake stage
  2. Analyzes emotional tone using wav2vec2 model
  3. Transcribes audio using Whisper model
  4. Performs sentiment analysis on transcripts
  5. Compares emotional tone with sentiment scores

Key components:
- Audio classification pipeline using `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition`
- Speech to text with `whisper`
- Sentiment analysis using `Snowflake Cortex`

**Cell 4: Process Files**
* Sets random seed for reproducibility
* Initializes audio classification and speech recognition pipelines
* Processes each audio file to:
  - Extract emotional tone
  - Generate transcript
  - Analyze sentiment
  - Compare tone and sentiment
* Creates a DataFrame with results

Example output:
```
                    File    Emotion  Emotion_Score                                          Transcript  Sentiment_Score Tone_Sentiment_Match
0  customer_call1.wav      happy         0.892    Thank you so much for your help today! You've...            0.8            Match
1  customer_call2.wav      angry         0.945    I've been waiting for hours and nobody has...             -0.7            Match
2  customer_call3.wav    neutral         0.756    I would like to inquire about the status...              0.1          Unknown
3  customer_call4.wav       happy         0.834    This service has exceeded my expectations...              0.9            Match
```

> 
> The DataFrame shows the complete analysis for each audio file, including the detected emotion, confidence scores, and whether the emotional tone matches the sentiment of the transcribed text.

The notebook outputs results showing the file name, detected emotion, emotion confidence score, transcript, sentiment score, and whether the tone matches the sentiment analysis.

## Understanding Results


The analysis provides multiple metrics that work together to give a comprehensive view of the audio:

### Sentiment Analysis
- Sentiment Score Range: [-1 to 1]
  - Negative values indicate negative sentiment
  - Positive values indicate positive sentiment
  - Values near 0 indicate neutral sentiment

### Emotional Classification
- Emotion Score: [0 to 1]
  - Represents the confidence level of the emotional classification
  - Higher values indicate stronger confidence in the detected emotion
  - Primary emotions detected: happy, angry, neutral, sad

### Tone-Sentiment Matching
The system compares emotional tone with sentiment scores to verify consistency:
- Happy emotion should correspond with positive sentiment (> 0)
  - Match example: Happy emotion (0.85) with sentiment score (0.6)
  - Mismatch example: Happy emotion (0.75) with sentiment score (-0.2)
- Angry emotion should correspond with negative sentiment (< 0)
  - Match example: Angry emotion (0.92) with sentiment score (-0.7)
  - Mismatch example: Angry emotion (0.88) with sentiment score (0.3)

The 'Tone_Sentiment_Match' field in the results indicates:
- "Match": Emotion and sentiment align (e.g., happy with positive sentiment)
- "Do Not Match": Emotion and sentiment conflict (e.g., angry with positive sentiment)
- "Unknown": For neutral or other emotional states

## Conclusion and Resources


Congratulations! You've successfully built an end-to-end audio analysis application in Snowflake that combines emotional tone detection, speech recognition, and sentiment analysis using Container Runtime for ML.

### What You Learned
- How to set up Container Runtime in Snowflake Notebooks
- How to implement audio processing using PyTorch and Hugging Face with [Snowflake ML](/en/data-cloud/snowflake-ml/)
- How to use pre-trained models for emotion recognition and speech-to-text
- How to perform sentiment analysis using [Snowflake Cortex](/en/data-cloud/cortex/)
- How to compare and analyze multiple aspects of audio communication

### Related Resources

Webpages:
- [Snowflake ML](/en/data-cloud/snowflake-ml/)
- [Snowflake Cortex AI](/en/data-cloud/cortex/)

Documentation:
- [Snowflake Notebooks on Container Runtime Overview](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs)
- [Cortex AI Documentation](https://docs.snowflake.com/en/guides-overview-ai-features)
- [PyTorch Audio Processing Guide](https://pytorch.org/audio/stable/index.html)

Sample Code & Guides:
- [Container Runtime Best Practices](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [External Access Setup Guide](https://docs.snowflake.com/en/developer-guide/external-network-access/external-network-access-overview)
- [Hugging Face Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [Snowpark Python Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)

Related Quickstarts:
- [Getting Started with Snowflake Notebook Container Runtime](/en/developers/guides/notebook-container-runtime/)
- [Train an XGBoost Model with GPUs using Snowflake Notebooks](/en/developers/guides/train-an-xgboost-model-with-gpus-using-snowflake-notebooks/)
- [Scale Embeddings with Snowflake Notebooks on Container Runtime](/en/developers/guides/scale-embeddings-with-snowflake-notebooks-on-container-runtime/)
- [Getting Started with Running Distributed PyTorch Models on Snowflake](/en/developers/guides/getting-started-with-running-distributed-pytorch-models-on-snowflake/)
- [Defect Detection Using Distributed PyTorch With Snowflake Notebooks](/en/developers/guides/defect-detection-using-distributed-pytorch-with-snowflake-notebooks/)

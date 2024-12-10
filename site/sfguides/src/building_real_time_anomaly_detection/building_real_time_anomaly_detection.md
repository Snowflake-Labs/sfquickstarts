author: James Cha-Earley
id: build_a_custom_model_to_detect_anomolies
summary: Building Real-Time Anomaly Detection on the Production Floor
categories: Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering,

# Building Real-Time Anomaly Detection for the Production Floor

## Overview

This guide follows the **AD_PRODUCTION_FLOOR** notebook to simulate production data, analyze it, and detect anomalies using Snowflake and machine learning. By the end, you will have a registered anomaly detection model in Snowflake's Model Registry.

### What You Will Learn

- Simulate production data with normal and anomalous patterns.
- Store and preprocess data using Snowpark.
- Train an LSTM-based anomaly detection model.
- Register and retrieve models from Snowflake's Model Registry.

---

## Step 1: Set Up the Environment

### Install and Import Required Packages

```bash
!pip install tensorflow==2.12.0
```

```python
# Import required libraries
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session
from numpy.random import seed
import tensorflow as tf

# Initialize Snowpark session
session = get_active_session()

# Set random seeds
seed(10)
tf.random.set_seed(10)
```

---

## Step 2: Generate Normal and Anomalous Data

### Generate Normal Data

```python
# Parameters
num_records = 1000
start_time = pd.Timestamp("2024-06-12 10:52:00")
interval = pd.Timedelta(minutes=10)

# Generate timestamps
timestamps = [start_time + i * interval for i in range(num_records)]

# Generate normal sensor data
np.random.seed(42)
temperature = np.random.normal(loc=0.06, scale=0.002, size=num_records)
vibration = np.random.normal(loc=0.075, scale=0.002, size=num_records)
motor_rpm = np.random.normal(loc=0.045, scale=0.001, size=num_records)
motor_amps = np.random.normal(loc=0.084, scale=0.002, size=num_records)
```

### Add Anomalies

```python
# Add anomalies
anomaly_start_index = num_records - 200
temperature[anomaly_start_index:] += np.random.uniform(0.005, 0.01, size=200)
vibration[anomaly_start_index:] += np.random.uniform(0.003, 0.007, size=200)
motor_rpm[anomaly_start_index:] -= np.random.uniform(0.002, 0.005, size=200)
motor_amps[anomaly_start_index:] += np.random.uniform(0.005, 0.01, size=200)

# Combine data into a DataFrame
data = {
    "TEMPERATURE": temperature,
    "VIBRATION": vibration,
    "MOTOR_RPM": motor_rpm,
    "MOTOR_AMPS": motor_amps,
    "MEASURE_TS": timestamps,
}
snow_pd = pd.DataFrame(data)
```

---

## Step 3: Store Data in Snowflake

```python
# Convert to Snowpark DataFrame
spdf = session.create_dataframe(snow_pd)

# Save data to Snowflake
spdf.write.save_as_table("SENSOR_PREPARED", mode="overwrite")
```

---

## Step 4: Explore the Data

### Display the Data

```python
spdf.show()
```

---

## Step 5: Create and Register the Anomaly Detection Model

### Define the Custom Model

```python
from snowflake.ml.model import custom_model
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class AnomalyDetectionModel(custom_model.CustomModel):
    def __init__(self, context: custom_model.ModelContext) -> None:
        super().__init__(context)
        
    @custom_model.inference_api
    def predict(self, train_data: pd.DataFrame) -> pd.DataFrame:
        cols = train_data.columns
        scaler = MinMaxScaler()
        
        # Prepare the data
        X_train_pd = train_data.to_numpy()
        X = X_train_pd.reshape(X_train_pd.shape[0], 1, X_train_pd.shape[1])
        
        # Perform predictions
        X_pred = self.context.model_ref('lstm').predict(X)
        X_pred = X_pred.reshape(X_pred.shape[0], X_pred.shape[2])
        
        # Calculate anomaly scores
        scored = np.abs(X_pred - X_train_pd)
        return pd.DataFrame(scored, columns=[f"feature_{i}" for i in range(scored.shape[1])])

# Create the custom model instance
ad = AnomalyDetectionModel(
    context=custom_model.ModelContext(models={'lstm': model})
)
```

### Register the Model in Snowflake

```python
from snowflake.ml.registry import Registry

# Initialize the registry
ml_reg = Registry(session=session)

# Log the model
mv = ml_reg.log_model(
    ad,
    model_name="ANOMALYDETECTION_MODEL_1",
    version_name='v1',
    sample_input_data=train_data,
    conda_dependencies=["scikit-learn", "keras==2.9", "tensorflow==2.9"],
    options={
        "relax_version": True,
        "embed_local_ml_library": True
    }
)
```

### Retrieve the Registered Model

```python
# Retrieve the model from the registry
reg = Registry(session=session) 
model_ref = reg.show_models()

# Access the specific model version
m = reg.get_model("ANOMALYDETECTION_MODEL_1")
mv = m.version("v1")
```

### Build a Streamlit App with Chat Interface for Data Insights

This Streamlit application serves as a Manufacturing Floor Q&A Assistant. It enables users to interact with the production floor data, leveraging Snowflake Cortex for conversational insights.

---

#### Overview

This chatbot provides the following features:
- Answers user queries based on data from sensors monitoring machine performance.
- Uses historical chat context to enhance conversational insights.
- Integrates Snowflake Cortex Search for retrieving relevant data.

---

#### Key Components of the App

##### Streamlit Setup and Configuration

The app initializes the Streamlit environment and provides a sidebar for configuration.

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.title(":gear: Manufacturing Floor Q&A Assistant  :gear:")
st.caption(
    "Welcome! This application suggests answers to questions based on the available data and previous agent responses in support chats."
)

# Initialize Snowflake session
session = get_active_session()
```

---

##### Chat Interface and Message Management

The app manages chat history and user interactions, storing previous conversations in the session state.

```python
def init_messages():
    if st.session_state.clear_conversation or "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.suggestions = []
        st.session_state.active_suggestion = None

# Display chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
```

---

##### Cortex Search Integration

The app connects to Snowflake Cortex Search for retrieving context-specific data based on user queries.

```python
def query_cortex_search_service(query):
    db, schema = session.get_current_database(), session.get_current_schema()

    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services[st.session_state.selected_cortex_search_service]
    )

    context_documents = cortex_search_service.search(
        query, columns=[], limit=st.session_state.num_retrieved_chunks
    )
    results = context_documents.results

    service_metadata = st.session_state.service_metadata
    search_col = [s["search_column"] for s in service_metadata
                  if s["name"] == st.session_state.selected_cortex_search_service][0]

    context_str = ""
    for i, r in enumerate(results):
        context_str += f"Context {i+1}: {r[search_col]} \n\n"

    if st.session_state.debug:
        st.sidebar.text_area("Context", context_str, height=500)

    return context_str
```

---

##### Prompt Generation

The app generates prompts for the selected AI model, combining context data and chat history.

```python
def create_prompt(user_question):
    if st.session_state.use_chat_history:
        chat_history = get_chat_history()
        question_summary = make_chat_history_summary(chat_history, user_question)
        prompt_context = query_cortex_search_service(question_summary)
    else:
        prompt_context = query_cortex_search_service(user_question)

    prompt = f"""
        You are an AI assistant. Analyze the sensor data and provide insights.
        <chat_history>
        {chat_history}
        </chat_history>
        <context>
        {prompt_context}
        </context>
        <question>
        {user_question}
        </question>
        Answer:
    """
    return prompt
```

---

##### Main Functionality

The `main()` function ties all components together, enabling user interactions and responses.

```python
def main():
    st.title(f":speech_balloon: Chatbot with Snowflake Cortex")

    init_service_metadata()
    init_config_options()
    init_messages()

    if question := st.chat_input("Ask a question...", disabled=disable_chat):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."):
                generated_response = complete(
                    st.session_state.model_name, create_prompt(question)
                )
                message_placeholder.markdown(generated_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": generated_response}
        )
```

---

## Summary

You’ve successfully followed the **AD_PRODUCTION_FLOOR** notebook to:

- Simulate production data with normal and anomalous patterns.
- Train and register an LSTM-based anomaly detection model in Snowflake.
- Retrieve and prepare the model for inference.

This workflow provides a foundation for real-time anomaly detection in production systems.

---

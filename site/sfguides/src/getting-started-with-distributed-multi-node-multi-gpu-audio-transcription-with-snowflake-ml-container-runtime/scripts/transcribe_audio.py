# Import python packages
import logging
import os
import tempfile
from typing import NamedTuple

import pandas as pd
import ray
import torch
from snowflake.ml.ray.datasink import SnowflakeTableDatasink
from snowflake.ml.ray.datasource import SFStageBinaryFileDataSource
from snowflake.snowpark import Session
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

BATCH_SIZE = 30
STAGE_LOCATION = "@AUDIO_FILES_STAGE"
TABLE_NAME = "WHISPER_DEMO_OUTPUT"
AUDIO_FILE_EXTENSION = "flac"


class ModelConfig(NamedTuple):
    model_id: str
    batch_size: int
    device: torch.device
    torch_dtype: torch.dtype


class AudioTranscriber:
    def __init__(self):
        # Get model configuration
        config = self._get_model_config()
        
        # initialize model here so that model can be put into correct GPU/node
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            config.model_id, torch_dtype=config.torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(config.device)
        processor = AutoProcessor.from_pretrained(config.model_id)
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=config.batch_size,
            return_timestamps=True,
            torch_dtype=config.torch_dtype,
            device=config.device,
            generate_kwargs={"language": "english"}
        )

    def __call__(self, batch: pd.DataFrame) -> pd.DataFrame:
        temp_files = []
        try:
            # Write each binary to a temporary file.
            for binary_content in batch["file_binary"]:
                # Use an appropriate suffix (e.g., .wav or .flac) based on your audio format.
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".flac")
                tmp_file.write(binary_content)
                tmp_file.close()
                temp_files.append(tmp_file.name)
            
            # Use the temporary file paths for inference.
            predictions = self.pipe(temp_files)
            assert len(predictions) == len(batch)
            outputs = [str(generated_audio["text"]).strip() for generated_audio in predictions]
            batch['outputs'] = outputs
            batch.drop(columns=['file_binary'], inplace=True)
        finally:
            # Clean up temporary files.
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        return batch

    def _get_model_config(self) -> ModelConfig:
        is_cuda_available = torch.cuda.is_available()
        return ModelConfig(
            model_id="openai/whisper-large-v3",
            batch_size=BATCH_SIZE,
            device=torch.device("cuda" if is_cuda_available else "cpu"),
            torch_dtype=torch.float16 if is_cuda_available else torch.float32,
        )


def configure_ray_logger() -> None:
    # Configure Ray logging
    ray_logger = logging.getLogger("ray")
    ray_logger.setLevel(logging.CRITICAL)

    data_logger = logging.getLogger("ray.data")
    data_logger.setLevel(logging.CRITICAL)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.CRITICAL)

    # Configure Ray's data context
    context = ray.data.DataContext.get_current()
    context.execution_options.verbose_progress = False
    context.enable_operator_progress_bars = False


def main():
    ray.init(ignore_reinit_error=True)
    num_nodes = len([node for node in ray.nodes() if node["Alive"]==True])
    max_nodes = int(os.getenv("SNOWFLAKE_JOBS_COUNT", num_nodes))
    print(f"Number of nodes: {num_nodes}, max nodes: {max_nodes}", flush=True)

    configure_ray_logger()

    # Create Snowflake session
    session = Session.builder.getOrCreate()

    # Check if there are any audio files in the stage
    num_files = session.sql(rf"list {STAGE_LOCATION} PATTERN = '.*\.{AUDIO_FILE_EXTENSION}'").count()
    if num_files == 0:
        raise ValueError(
            f"No audio files found in the stage with extension: {AUDIO_FILE_EXTENSION}. "
            "Did you run the audio processing step?"
        )
    print(f"Found {num_files} audio files to process", flush=True)

    # Load audio files into a ray dataset
    audio_source = SFStageBinaryFileDataSource(
        stage_location = STAGE_LOCATION,
        database = session.get_current_database(),
        schema = session.get_current_schema(),
        file_pattern = f"*.{AUDIO_FILE_EXTENSION}"
    )
    audio_dataset = ray.data.read_datasource(audio_source)

    # Create transcribed ray dataset (lazily evaluated)
    transcribed_ds = audio_dataset.map_batches(
        AudioTranscriber,
        batch_size=BATCH_SIZE,
        batch_format='pandas',
        concurrency=(num_nodes, max_nodes),
        num_gpus=1,
    )

    # Create datasink to write transcribed dataset to Snowflake table
    datasink = SnowflakeTableDatasink(
        table_name=TABLE_NAME,
        database=session.get_current_database(),
        schema=session.get_current_schema(),
        auto_create_table=True,  # Create table if it doesn't exist
        override=True,  # Replace table if it already exists
    )

    # Trigger the transcribed dataset to be evaluated and written to Snowflake table
    transcribed_ds.write_datasink(datasink)

    # Show some of the transcribed data
    session.table(TABLE_NAME).show()


if __name__ == "__main__":
    main()
#!/bin/bash

set -e  # Exit on any error

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Download and unpack the audio files
wget -qO- https://us.openslr.org/resources/12/dev-clean.tar.gz | tar -xz -C $SCRIPT_DIR

# Create a stage to store the audio files
snow stage create AUDIO_FILES_STAGE \
     --encryption SNOWFLAKE_SSE \
     --enable-directory \
     --database MULTINODE_MULTIGPU_MYDB \
     --schema AUDIO_TRANSCRIPTION_SCH \
     --warehouse ML_MODEL_WH \
     --role SYSADMIN

# Copy the audio files to the stage
snow stage copy "$SCRIPT_DIR/LibriSpeech/dev-clean/*/*/*.flac" @AUDIO_FILES_STAGE \
     --recursive \
     --overwrite \
     --no-auto-compress \
     --parallel 99 \
     --database MULTINODE_MULTIGPU_MYDB \
     --schema AUDIO_TRANSCRIPTION_SCH \
     --warehouse ML_MODEL_WH \
     --role SYSADMIN

# List the files in the stage
snow stage list-files @AUDIO_FILES_STAGE \
     --database MULTINODE_MULTIGPU_MYDB \
     --schema AUDIO_TRANSCRIPTION_SCH \
     --warehouse ML_MODEL_WH \
     --role SYSADMIN
#!/bin/bash
# Starts LiteLLM proxy that translates OpenAI -> Snowflake Cortex REST API.
# Cursor points at http://localhost:4000/v1 with the LITELLM_MASTER_KEY.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
source "$DIR/.env"
set +a
exec /Users/priyajoseph/cursor-cortex/.venv/bin/litellm \
  --config "$DIR/litellm_config.yaml" \
  --port 4000 \
  --host 127.0.0.1

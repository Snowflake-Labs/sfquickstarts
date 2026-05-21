#!/bin/bash
set -euo pipefail

# Upload a file to AEM DAM via Direct Binary Upload (3-step API)
# Usage: upload-dam-asset.sh <file-path> <dam-folder>
# Example: upload-dam-asset.sh ./sidebar.json snowflake-site/developers/technical/guides-navigation
#
# Required env vars: AEM_URL, AEM_USERNAME, AEM_PASSWORD
# Optional env vars: MAX_RETRIES (default: 3), RETRY_DELAY (default: 5)

FILE_PATH="$1"
DAM_FOLDER="$2"
FILE_NAME=$(basename "$FILE_PATH")
FILE_SIZE=$(wc -c < "$FILE_PATH" | tr -d ' ')
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"

if [ ! -f "$FILE_PATH" ]; then
  echo "❌ File not found: $FILE_PATH" >&2
  exit 1
fi

echo "📤 Uploading: $FILE_NAME ($FILE_SIZE bytes) → /content/dam/${DAM_FOLDER}/"

for attempt in $(seq 1 "$MAX_RETRIES"); do
  echo "🔄 Attempt $attempt of $MAX_RETRIES"

  INIT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "${AEM_URL}/content/dam/${DAM_FOLDER}.initiateUpload.json" \
    -u "${AEM_USERNAME}:${AEM_PASSWORD}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "fileName=${FILE_NAME}" \
    -d "fileSize=${FILE_SIZE}")

  INIT_HTTP=$(echo "$INIT_RESPONSE" | tail -n1)
  INIT_BODY=$(echo "$INIT_RESPONSE" | sed '$d')

  if [ "$INIT_HTTP" -lt 200 ] || [ "$INIT_HTTP" -ge 300 ]; then
    echo "⚠️ Initiate upload failed (HTTP $INIT_HTTP)"
    if [ "$INIT_HTTP" -ge 500 ] && [ "$attempt" -lt "$MAX_RETRIES" ]; then
      wait_time=$((RETRY_DELAY * attempt * 2))
      echo "   Retrying in ${wait_time}s..."
      sleep "$wait_time"
      continue
    fi
    echo "$INIT_BODY" >&2
    exit 1
  fi

  UPLOAD_URI=$(echo "$INIT_BODY" | jq -r '.files[0].uploadURIs[0]')
  UPLOAD_TOKEN=$(echo "$INIT_BODY" | jq -r '.files[0].uploadToken')
  MIME_TYPE=$(echo "$INIT_BODY" | jq -r '.files[0].mimeType')
  COMPLETE_URI=$(echo "$INIT_BODY" | jq -r '.completeURI')

  if [ "$UPLOAD_URI" = "null" ] || [ -z "$UPLOAD_URI" ]; then
    echo "❌ Failed to get upload URI from response" >&2
    echo "$INIT_BODY" >&2
    exit 1
  fi

  sleep 2

  PUT_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URI" \
    -H "Content-Type: ${MIME_TYPE}" \
    --data-binary "@${FILE_PATH}")

  if [ "$PUT_HTTP" != "201" ] && [ "$PUT_HTTP" != "200" ]; then
    echo "⚠️ Binary upload failed (HTTP $PUT_HTTP)"
    if [ "$PUT_HTTP" -ge 500 ] && [ "$attempt" -lt "$MAX_RETRIES" ]; then
      wait_time=$((RETRY_DELAY * attempt * 2))
      echo "   Retrying in ${wait_time}s..."
      sleep "$wait_time"
      continue
    fi
    exit 1
  fi

  sleep 2

  COMPLETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "${AEM_URL}${COMPLETE_URI}" \
    -u "${AEM_USERNAME}:${AEM_PASSWORD}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "fileName=${FILE_NAME}" \
    -d "uploadToken=${UPLOAD_TOKEN}" \
    -d "mimeType=${MIME_TYPE}" \
    -d "createVersion=true")

  COMPLETE_HTTP=$(echo "$COMPLETE_RESPONSE" | tail -n1)

  if [ "$COMPLETE_HTTP" -ge 200 ] && [ "$COMPLETE_HTTP" -lt 300 ]; then
    echo "✅ Uploaded to /content/dam/${DAM_FOLDER}/${FILE_NAME}"
    exit 0
  fi

  echo "⚠️ Complete upload failed (HTTP $COMPLETE_HTTP)"
  if [ "$COMPLETE_HTTP" -ge 500 ] && [ "$attempt" -lt "$MAX_RETRIES" ]; then
    wait_time=$((RETRY_DELAY * attempt * 2))
    echo "   Retrying in ${wait_time}s..."
    sleep "$wait_time"
    continue
  fi

  echo "$COMPLETE_RESPONSE" | sed '$d' >&2
  exit 1
done

echo "❌ Upload failed after $MAX_RETRIES attempts" >&2
exit 1

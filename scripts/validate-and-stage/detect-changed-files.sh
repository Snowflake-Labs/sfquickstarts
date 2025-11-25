#!/bin/bash

# Determine changed files in quickstarts from PR
# Processes changed files to extract markdown files and images for validation
#
# Usage: detect-changed-files.sh <changed_files.txt> <downloaded_files.txt>
#
# Outputs (to stdout in GitHub Actions format):
#   - changed_markdown_json: JSON array of changed markdown files (with pr/ prefix)
#   - all_changed_files_json: JSON array of all changed files (markdown + images)
#   - md_file_count: Number of changed markdown files
#
# Exit codes:
#   0 - Success

set -e

if [ $# -lt 2 ]; then
  echo "Usage: $0 <changed_files.txt> <downloaded_files.txt>" >&2
  exit 1
fi

CHANGED_FILES_TXT="$1"
DOWNLOADED_FILES_TXT="$2"

if [ ! -f "$CHANGED_FILES_TXT" ]; then
  echo "Error: File not found: $CHANGED_FILES_TXT" >&2
  exit 1
fi

if [ ! -f "$DOWNLOADED_FILES_TXT" ]; then
  echo "Error: File not found: $DOWNLOADED_FILES_TXT" >&2
  exit 1
fi

# Read the list of changed files (modified in PR)
changed_files=$(cat "$CHANGED_FILES_TXT")

# Read the list of all downloaded files (changed + additional markdown files)
downloaded_files=$(cat "$DOWNLOADED_FILES_TXT")

# Filter out non-image files from assets folders for changed files
# Keep: markdown files outside assets, image files from assets
# Exclude: non-image files from assets (like .md, .txt, etc.)
all_changed_files=$(echo "$changed_files" | grep -v '/assets/' || true)
assets_images=$(echo "$changed_files" | grep '/assets/' | grep -E '\.(jpg|jpeg|png|gif|svg|webp|bmp|ico)$' || true)
if [ -n "$assets_images" ]; then
  all_changed_files=$(printf '%s\n%s\n' "$all_changed_files" "$assets_images")
fi

# Extract changed markdown files (for validation)
changed_md_files=$(echo "$all_changed_files" | grep '\.md$' || true)

# Extract all downloaded markdown files (for multiple markdown check)
all_md_files=$(echo "$downloaded_files" | grep '\.md$' | grep -v '/assets/' || true)

if [ -z "$all_changed_files" ]; then 
  all_changed_files_json='[]'
else
  all_changed_files_json=$(printf '%s\n' "$all_changed_files" | jq -R -s -c 'split("\n") | map(select(length>0))')
fi

# Prepare markdown files for validation (only changed)
if [ -z "$changed_md_files" ]; then
  changed_markdown_json='[]'
  md_file_count=0
else
  # Build changed_markdown_json with only changed markdown files (for validations)
  changed_markdown_json=$(printf '%s\n' "$changed_md_files" | awk '{print "pr/" $0}' | jq -R -s -c 'split("\n") | map(select(length>0))')
  md_file_count=$(echo "$changed_md_files" | wc -l | tr -d ' ')
fi

# Print debug information
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "All changed files:"
echo "$all_changed_files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Changed markdown files (for validation):"
echo "$changed_markdown_json" | jq -r '.[]' 2>/dev/null || echo "$changed_markdown_json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Output results in GitHub Actions format (if GITHUB_OUTPUT is set)
# Otherwise just print to stdout for testing
if [ -n "$GITHUB_OUTPUT" ]; then
  echo "changed_markdown_json=$changed_markdown_json" >> "$GITHUB_OUTPUT"
  echo "all_changed_files_json=$all_changed_files_json" >> "$GITHUB_OUTPUT"
  echo "md_file_count=$md_file_count" >> "$GITHUB_OUTPUT"
else
  # For local testing, output as shell variables
  echo "changed_markdown_json=$changed_markdown_json"
  echo "all_changed_files_json=$all_changed_files_json"
  echo "md_file_count=$md_file_count"
fi

exit 0


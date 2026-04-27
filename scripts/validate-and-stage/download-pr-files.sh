#!/bin/bash

# Download changed files from a GitHub Pull Request
# Downloads files to the pr/ directory and creates metadata files for validation
#
# Usage: download-pr-files.sh <repo> <pr_number> <head_repo> <head_ref>
#
# Required environment variables:
#   GITHUB_TOKEN - GitHub token for API authentication
#
# Outputs:
#   - pr_files.json: JSON metadata about all files in the PR
#   - changed_files.txt: List of changed files (excluding deleted)
#   - downloaded_files.txt: List of all downloaded files (changed + additional)
#   - pr/: Directory containing downloaded file contents
#
# Exit codes:
#   0 - Success

set -e

if [ $# -lt 4 ]; then
  echo "Usage: $0 <repo> <pr_number> <head_repo> <head_ref>" >&2
  echo "Example: $0 owner/repo 123 fork_owner/repo branch-name" >&2
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is required" >&2
  exit 1
fi

REPO="$1"
PR_NUMBER="$2"
HEAD_REPO="$3"
HEAD_REF="$4"

# Fetch changed files from PR (excluding deleted files)
files_json=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$REPO/pulls/$PR_NUMBER/files?per_page=100")

# Save files_json to a file for reuse in subsequent steps
echo "$files_json" > pr_files.json

# Filter for changed files (excluding folders starting with _)
changed_files=$(echo "$files_json" | jq -r '.[] 
  | select(.status != "removed") 
  | .filename 
  | select(startswith("site/sfguides/src/")) 
  | select(test("/_") | not)')

# Early exit if no files to download
if [ -z "$changed_files" ]; then
  echo "No relevant files to download for validation"
  echo "" > downloaded_files.txt
  echo "" > changed_files.txt
  exit 0
fi

# Download all changed files
echo "Downloading changed files..."
while IFS= read -r file; do
  [ -z "$file" ] && continue
  
  # Create directory structure
  mkdir -p "pr/$(dirname "$file")"
  
  # Download raw file content
  url="https://raw.githubusercontent.com/$HEAD_REPO/$HEAD_REF/$file"
  echo "Downloading: $file"
  
  if ! curl -sS -f -H "Authorization: Bearer $GITHUB_TOKEN" "$url" -o "pr/$file"; then
    echo "Warning: Failed to download $file" >&2
  fi
done <<< "$changed_files"

# Save changed files to separate lists
echo "$changed_files" > changed_files.txt
echo "$changed_files" > downloaded_files.txt

# Extract folders that have changes
modified_folders=$(echo "$changed_files" | sed -E 's|^site/sfguides/src/([^/]+)/.*|\1|' | sort -u)

# Download ALL markdown files from modified folders (even if not changed)
# This allows us to validate that each folder has only one markdown file
if [ -n "$modified_folders" ]; then
  echo "Downloading all markdown files from modified folders..."
  
  while IFS= read -r folder; do
    [ -z "$folder" ] && continue
    
    # Use GitHub API to list all files in the folder
    folder_path="site/sfguides/src/$folder"
    tree_url="https://api.github.com/repos/$HEAD_REPO/contents/$folder_path?ref=$HEAD_REF"
    
    # Get all .md files in the folder (excluding README.md)
    folder_files=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "$tree_url" | jq -r '.[] | select(.type=="file") | select(.name | endswith(".md")) | select(.name | test("^README\\.md$"; "i") | not) | .name')
    
    while IFS= read -r filename; do
      [ -z "$filename" ] && continue
      
      file_path="$folder_path/$filename"
      
      # Skip if already downloaded
      if [ -f "pr/$file_path" ]; then
        continue
      fi
      
      # Create directory structure
      mkdir -p "pr/$folder_path"
      
      # Download the file
      url="https://raw.githubusercontent.com/$HEAD_REPO/$HEAD_REF/$file_path"
      echo "Downloading additional markdown: $file_path"
      
      if curl -sS -f -H "Authorization: Bearer $GITHUB_TOKEN" "$url" -o "pr/$file_path"; then
        # Add to downloaded files list
        echo "$file_path" >> downloaded_files.txt
      else
        echo "Warning: Failed to download $file_path" >&2
      fi
    done <<< "$folder_files"
  done <<< "$modified_folders"
fi

echo "Download complete"

exit 0


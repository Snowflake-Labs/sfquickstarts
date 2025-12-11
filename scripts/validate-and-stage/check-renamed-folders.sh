#!/bin/bash

# Check if any top-level folders inside site/sfguides/src (not starting with _) have been renamed
# Only checks the immediate child directory of /src/, ignoring nested subdirectories
#
# Usage: check-renamed-folders.sh <pr_files.json>
#
# Exit codes:
#   0 - No renames detected or only allowed renames (underscore folders, round-trips)
#   1 - Blocked renames detected

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 <pr_files.json>" >&2
  exit 1
fi

PR_FILES_JSON="$1"

if [ ! -f "$PR_FILES_JSON" ]; then
  echo "Error: File not found: $PR_FILES_JSON" >&2
  exit 1
fi

files_json=$(cat "$PR_FILES_JSON")

renamed_folders='[]'
seen_renames=()
all_folder_renames='[]'

# Method 1: Check for explicit file renames (status == "renamed")
renamed_files=$(echo "$files_json" | jq -r '.[] | select(.status == "renamed") | "\(.previous_filename)|\(.filename)"')

if [ -n "$renamed_files" ]; then
  echo "Checking for renamed files..."
  
  while IFS='|' read -r old_path new_path; do
    [ -z "$old_path" ] || [ -z "$new_path" ] && continue
    
    # Skip if paths are identical (no actual rename)
    [ "$old_path" = "$new_path" ] && continue
    
    # Extract only the first-level directory after site/sfguides/src/
    # Pattern: site/sfguides/src/{folder}/...
    # Must extract old_folder BEFORE checking new_path to avoid BASH_REMATCH being overwritten
    if [[ "$old_path" =~ ^site/sfguides/src/([^/]+)/ ]]; then
      old_folder="${BASH_REMATCH[1]}"
    else
      continue
    fi
    
    if [[ "$new_path" =~ ^site/sfguides/src/([^/]+)/ ]]; then
      new_folder="${BASH_REMATCH[1]}"
    else
      continue
    fi
    
    # Check if the top-level folder name changed
    if [ "$old_folder" != "$new_folder" ]; then
      # Track this rename (we'll check for round-trips later)
      rename_key="${old_folder}→${new_folder}"
      if [[ ! " ${seen_renames[@]} " =~ " ${rename_key} " ]]; then
        all_folder_renames=$(echo "$all_folder_renames" | jq -c --arg old "$old_folder" --arg new "$new_folder" '. + [{from:$old, to:$new}]')
        seen_renames+=("$rename_key")
      fi
    fi
  done <<< "$renamed_files"
fi

# Method 2: Check for directory renames via removed + added pattern
# Git doesn't always detect directory renames, so files may show as removed + added
echo "Checking for removed/added file patterns..."

# Get all removed files from site/sfguides/src/ (excluding _ folders)
removed_files=$(echo "$files_json" | jq -r '.[] | select(.status == "removed") | .filename | select(startswith("site/sfguides/src/")) | select(test("^site/sfguides/src/_") | not)')

# Get all added files from site/sfguides/src/ (excluding _ folders)
added_files=$(echo "$files_json" | jq -r '.[] | select(.status == "added") | .filename | select(startswith("site/sfguides/src/")) | select(test("^site/sfguides/src/_") | not)')

if [ -n "$removed_files" ] && [ -n "$added_files" ]; then
  # Extract unique folder names from removed files
  removed_folders=$(echo "$removed_files" | sed -E 's|^site/sfguides/src/([^/]+)/.*|\1|' | sort -u)
  
  # Extract unique folder names from added files
  added_folders=$(echo "$added_files" | sed -E 's|^site/sfguides/src/([^/]+)/.*|\1|' | sort -u)
  
  # Check if any removed folder has all its files removed AND similar files added to a new folder
  while IFS= read -r removed_folder; do
    [ -z "$removed_folder" ] && continue
    
    # Get all files removed from this folder
    removed_folder_files=$(echo "$removed_files" | grep "^site/sfguides/src/$removed_folder/" | sed "s|^site/sfguides/src/$removed_folder/||" || true)
    [ -z "$removed_folder_files" ] && continue
    
    # For each added folder, check if it has matching file structure
    while IFS= read -r added_folder; do
      [ -z "$added_folder" ] && continue
      
      # Skip if we've already detected this rename
      rename_key="${removed_folder}→${added_folder}"
      [[ " ${seen_renames[@]} " =~ " ${rename_key} " ]] && continue
      
      # Get all files added to this folder
      added_folder_files=$(echo "$added_files" | grep "^site/sfguides/src/$added_folder/" | sed "s|^site/sfguides/src/$added_folder/||" || true)
      [ -z "$added_folder_files" ] && continue
      
      # Count matching relative paths
      matching_files=0
      total_removed=0
      while IFS= read -r rel_path; do
        [ -z "$rel_path" ] && continue
        total_removed=$((total_removed + 1))
        if echo "$added_folder_files" | grep -Fxq "$rel_path"; then
          matching_files=$((matching_files + 1))
        fi
      done <<< "$removed_folder_files"
      
      # If at least 50% of removed files match added files, consider it a folder rename
      if [ "$total_removed" -gt 0 ] && [ "$matching_files" -gt 0 ]; then
        match_percentage=$((matching_files * 100 / total_removed))
        
        if [ "$match_percentage" -ge 50 ]; then
          # Track this rename (we'll check for round-trips later)
          all_folder_renames=$(echo "$all_folder_renames" | jq -c --arg old "$removed_folder" --arg new "$added_folder" '. + [{from:$old, to:$new}]')
          seen_renames+=("$rename_key")
        fi
      fi
    done <<< "$added_folders"
  done <<< "$removed_folders"
fi

# Analyze all detected renames and filter out round-trips
echo "Analyzing folder renames..."

# Deduplicate renames (same rename may appear multiple times for different files)
all_renames_json=$(echo "$all_folder_renames" | jq 'unique_by({from: .from, to: .to})')

rename_count=$(echo "$all_renames_json" | jq 'length')
if [ "$rename_count" -eq 0 ]; then
  echo "✅ No folder renames detected"
else
  echo "Detected $rename_count unique folder rename(s):"
  echo "$all_renames_json" | jq -r '.[] | "  \(.from) → \(.to)"'
fi

while IFS= read -r rename; do
  [ -z "$rename" ] && continue
  
  from=$(echo "$rename" | jq -r '.from')
  to=$(echo "$rename" | jq -r '.to')
  
  # Check if there's a reverse rename (to → from)
  reverse_exists=$(echo "$all_renames_json" | jq --arg from "$to" --arg to "$from" '[.[] | select(.from == $from and .to == $to)] | length')
  
  if [ "$reverse_exists" -gt 0 ]; then
    echo "ℹ️  Round-trip rename detected (allowed): $from ↔ $to"
    # This is a round-trip, skip it
    continue
  fi
  
  # Check if original folder started with underscore (allowed)
  if [[ "$from" =~ ^_ ]]; then
    echo "ℹ️  Underscore folder rename (allowed): $from → $to"
    continue
  fi
  
  # This is a real rename that should be blocked
  echo "❌ Top-level folder rename detected: $from → $to"
  example_file="site/sfguides/src/$from/... → site/sfguides/src/$to/..."
  renamed_folders=$(echo "$renamed_folders" | jq -c --arg old "$from" --arg new "$to" --arg file "$example_file" '. + [{old_folder:$old, new_folder:$new, example_file:$file}]')
  
done < <(echo "$all_renames_json" | jq -c '.[]')

# Check if any folder renames found
rename_count=$(echo "$renamed_folders" | jq 'length')
if [ "$rename_count" -ne 0 ]; then
  echo "" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "❌ ERROR: Guide rename(s) detected" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "$renamed_folders" | jq -r '.[] | "  - \(.old_folder) → \(.new_folder)"' >&2
  echo "" >&2
  echo "Renaming guide URLs is not supported." >&2
  echo "Please revert the name change." >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  
  # Save error details for PR comment
  jq -n --argjson renames "$renamed_folders" '{type:"folder_rename", message:"Renaming guide URLs is not currently supported. Please revert the name change.", renames:$renames}' > folder-rename-error.json
  exit 1
else
  echo "✅ No top-level guide folder renames detected"
  exit 0
fi


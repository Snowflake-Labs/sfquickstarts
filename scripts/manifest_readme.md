# Manifest Generator - How to Run

This README explains how to generate the quickstart manifest consumed by other teams.

## Prerequisites
- Python 3.8+ installed (`python3 --version`)
- Git available and the repo is a valid Git clone (for lastUpdatedAt)

## Generate the manifest (from repo root)

```bash
cd "/Users/kanwal.komailsnowflake.com/Documents/GitHub/sfquickstarts_main"

# Preferred: canonical script name
python3 site/sfguides/SCRIPTS/generate_quickstart_manifest.py

# Alternate: same logic, alternate filename
python3 "site/sfguides/SCRIPTS/manifest generator.py"
```

This writes:

```
site/sfguides/src/quickstart-manifest.json
```

## What the script does
- Scans `site/sfguides/src/*/` for the primary `.md` guide in each folder
- Parses top-of-file front matter (`summary`, `categories`, optional `duration`)
- Extracts first `#` H1 if present (fallbacks to folder name)
- Uses `git log -1 --format=%cs` to populate `lastUpdatedAt`
- Emits JSON at `site/sfguides/src/quickstart-manifest.json` with:
  - `title`, `categories`, `contentType`, `url`, `summary`, `lastUpdatedAt`, and optional `duration`

## Verify output

```bash
# Basic check
ls -lh site/sfguides/src/quickstart-manifest.json

# Count entries (titles)
grep -c '\"title\":' site/sfguides/src/quickstart-manifest.json

# Quick peek
head -n 40 site/sfguides/src/quickstart-manifest.json
```

## Troubleshooting
- Blank `lastUpdatedAt` values: ensure the repo has git history locally
  ```bash
  git fetch --all --prune
  ```
- Categories look verbose (taxonomy paths): the script preserves what’s in `categories` front matter.
  If you want a simplified mapping, open an issue and we can add a mapper.

## Notes
- Re-running the script overwrites `quickstart-manifest.json`.
- The URL for each entry is built from the folder name after `/src/`:
  `https://www.snowflake.com/en/developers/guides/<folder-name>/`.
*** End Patch```} />


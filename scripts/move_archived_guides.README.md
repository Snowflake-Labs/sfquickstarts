# move_archived_guides.py — README

This README explains how to run the `move_archived_guides.py` script located in this folder.

Purpose
-------
Moves guide directories or markdown files under `site/sfguides/src` whose mapping row has
`Status` == `Archived` (case-insensitive) into `site/sfguides/src/_archived`.

Important: the script is safe by default and runs in dry-run mode unless you pass `--apply`.

Location
--------
Script: `site/sfguides/scripts/move_archived_guides.py`

Report: `site/sfguides/scripts/archived_move_report.csv` (written after each run)

Requirements
------------
- Python 3.8+ (the script uses standard library features and pandas)
- Python packages: `pandas` (and `openpyxl` when reading/writing .xlsx). Install with pip:

```bash
python3 -m pip install pandas openpyxl
```

Basic usage
-----------
Dry-run (recommended first):

```bash
python3 site/sfguides/scripts/move_archived_guides.py
```

This will detect archived ids from the default mapping file
`site/sfguides/src/_SCRIPTS/language_data.xlsx`, look for matching
files/directories in `site/sfguides/src`, and print actions. A CSV report will be written to
`site/sfguides/scripts/archived_move_report.csv`.

To actually perform the moves, add `--apply`:

```bash
python3 site/sfguides/scripts/move_archived_guides.py --apply
```

Options
-------
- `--apply` : Actually move matching files/directories. Without this flag the script only simulates moves.
- `--mapping PATH` : Path to the mapping file (XLSX or CSV). Default:
  `site/sfguides/src/_SCRIPTS/language_data.xlsx`.
- `--src-root PATH` : Path to the `site/sfguides/src` folder. Default is detected relative to the script.
- `--report PATH` : Path to write the CSV report. Default:
  `site/sfguides/scripts/archived_move_report.csv`.

What the script matches
-----------------------
For each archived id, the script tries these locations (in this order):

- `site/sfguides/src/<id>` (directory)
- `site/sfguides/src/<id>/<id>.md` (markdown inside directory)
- `site/sfguides/src/<id>.md` (top-level markdown file)
- A relaxed alternate where spaces in the id are replaced with underscores (and vice versa)

If it finds multiple candidates, it will attempt to move them. If the destination path already exists
the script will append a timestamp to the target directory name to avoid overwriting.

Safety and recommendations
--------------------------
- Always run a dry-run first (no `--apply`) and inspect `archived_move_report.csv`.
- Verify `site/firebase.json` redirects (some archived guide ids may be referenced there). You may
  want to update redirects before or after moving files.
- If you want to keep a git history of the move, run the script with `--apply`, then commit the
  moves with `git add -A` and `git commit -m "Move archived sfguides to _archived"`.
- The script will not modify `language_data.xlsx`. It only moves filesystem items.

Report format
-------------
The CSV report contains these columns:

- `archived_id` — the id from the mapping marked Archived
- `found_path` — the matched path that would be moved (or empty if not found)
- `action` — one of `dry-run`, `moved`, `failed`, or `not-found`
- `note` — additional info (target path, error messages, etc.)

Troubleshooting
---------------
- "No 'Status' column found": make sure your mapping file has a column named `Status` (case-insensitive).
- If the script doesn't find a file for a known id, confirm the `id:` front-matter in the guide matches
  the ID in the mapping exactly (or consider localized variants).

Next steps
----------
- Run a dry-run and inspect the CSV report. If the results look correct, re-run with `--apply`.
- If you want, I can run a dry-run for you now and paste the summary.

Contact
-------
If you need changes to the heuristics (for example, to treat trailing slashes or localized suffixes),
edit `move_archived_guides.py` or ask for an update.

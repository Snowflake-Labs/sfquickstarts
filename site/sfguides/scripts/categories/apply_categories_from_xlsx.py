#!/usr/bin/env python3
"""Apply categories from CSV mapping and remove categories/tags lines from markdown files.

Reads CSV at site/sfguides/src/_SCRIPTS/language_data.csv and for each row maps the id (col A)
to the category values located in columns G, H, I, L, O, P, S, T, W, and X (Excel 1-based).
Then walks site/sfguides/src and for every .md file removes existing lines that start
with "categories:" or "tags:" and inserts a new "categories: <values>" line immediately
after the file's "id:" header line. Generates a CSV report at
site/sfguides/scripts/categories_update_report.csv with per-file details.

Idempotent: running multiple times will not duplicate categories lines.
"""

import csv
import os
from pathlib import Path
import sys

try:
    import pandas as pd
except Exception:
    print("pandas not found. Please install pandas: pip3 install pandas")
    sys.exit(1)


def find_repo_root():
    p = Path(__file__).resolve()
    for parent in p.parents:
        # prefer a folder named sfquickstarts
        if parent.name == 'sfquickstarts':
            return parent
        # fallback: folder that contains site/sfguides
        if (parent / 'site' / 'sfguides').exists():
            return parent
    # fallback to two levels up from this script
    return p.parents[3]


REPO_ROOT = find_repo_root()
SRC_ROOT = REPO_ROOT / 'site' / 'sfguides' / 'src'
SCRIPTS_DIR = REPO_ROOT / 'site' / 'sfguides' / 'scripts'
# --- UPDATED to point to .csv file ---
DATA_PATH = REPO_ROOT / 'site' / 'sfguides' / 'src' / '_SCRIPTS' / 'language_data.csv'
REPORT_PATH = SCRIPTS_DIR / 'categories_update_report.csv'


def load_mapping(csv_path: Path):
    # --- UPDATED to read a CSV file ---
    try:
        df = pd.read_csv(csv_path, header=0)
    except Exception as e:
        print(f"Error reading CSV file at {csv_path}: {e}")
        print("Please ensure the file is a valid CSV and the path is correct.")
        sys.exit(1)

    # The ID column is expected to be the first column (column A). We'll take its name.
    if df.shape[1] == 0:
        raise RuntimeError('CSV file appears empty')

    id_col = df.columns[0]

    # --- UPDATED LOGIC HERE ---
    # Excel columns G,H,I,L,O,P,S,T,W,X are 7,8,9,12,15,16,19,20,23,24 (1-based).
    # Convert to 0-based indexes: 6, 7, 8, 11, 14, 15, 18, 19, 22, 23.
    desired_idx = [6, 7, 8, 11, 14, 15, 18, 19, 22, 23]
    # --- END UPDATED LOGIC ---

    # Build mapping id -> list(categories)
    mapping = {}
    for _, row in df.iterrows():
        raw_id = row[id_col]
        if pd.isna(raw_id):
            continue
        guide_id = str(raw_id).strip()
        cats = []
        for idx in desired_idx:
            if idx < len(df.columns):
                col_name = df.columns[idx]
                val = row[col_name]
                if pd.notna(val):
                    text = str(val).strip()
                    if text:
                        cats.append(text)
        # Normalize and deduplicate while preserving order
        seen = set()
        uniq = []
        for c in cats:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        mapping[guide_id] = uniq

    return mapping

# --- REMOVED the two duplicate/incorrect definitions of load_mapping ---

def process_markdown_files(mapping):
    rows = []
    md_files = list(SRC_ROOT.rglob('*.md'))
    for md in md_files:
        # Skip scripts and _SCRIPTS folders
        if '/_SCRIPTS/' in str(md) or '/scripts/' in str(md):
            continue

        rel_path = md.relative_to(REPO_ROOT)
        try:
            text = md.read_text(encoding='utf-8')
        except Exception as e:
            rows.append([str(rel_path), '', '', '', '', 'read-error', str(e)])
            continue

        lines = text.splitlines()

        # find id line
        id_idx = None
        file_id = ''
        for i, ln in enumerate(lines[:60]):
            if ln.strip().lower().startswith('id:'):
                id_idx = i
                # extract after 'id:'
                file_id = ln.split(':', 1)[1].strip()
                break

        # capture old categories and tags (all occurrences)
        old_categories = []
        old_tags = []
        for ln in lines[:80]:
            l = ln.strip()
            if l.lower().startswith('categories:'):
                old_categories.append(l.split(':', 1)[1].strip())
            if l.lower().startswith('tags:'):
                old_tags.append(l.split(':', 1)[1].strip())

        if not file_id:
            rows.append([str(rel_path), '', '|'.join(old_categories), '|'.join(old_tags), '', 'no-id', 'no-change'])
            continue

        # Determine new categories from mapping
        new_cats_list = mapping.get(file_id)
        if not new_cats_list:
            rows.append([str(rel_path), file_id, '|'.join(old_categories), '|'.join(old_tags), '', 'unknown-id', 'no-change'])
            continue

        new_cats = ', '.join(new_cats_list)

        # Remove existing categories/tags lines from the file header (we'll remove anywhere in file to be safe)
        changed = False
        new_lines = []
        for ln in lines:
            lstr = ln.lstrip()
            if lstr.lower().startswith('categories:') or lstr.lower().startswith('tags:'):
                changed = True
                continue
            new_lines.append(ln)

        # After removal, insert new categories line immediately after the id line
        # Find id line index in new_lines
        insert_idx = None
        for i, ln in enumerate(new_lines[:80]):
            if ln.strip().lower().startswith('id:'):
                insert_idx = i + 1
                break

        if insert_idx is None:
            # shouldn't happen since we had file_id earlier, but guard
            rows.append([str(rel_path), file_id, '|'.join(old_categories), '|'.join(old_tags), new_cats, 'id-line-missing-after-cleanup', 'no-change'])
            continue

        # Check if the next line is already categories: with same value
        existing_next = ''
        if insert_idx < len(new_lines):
            existing_next = new_lines[insert_idx].strip()

        desired_line = f'categories: {new_cats}'
        if existing_next.lower().startswith('categories:'):
            if existing_next.strip() == desired_line:
                # nothing to do
                rows.append([str(rel_path), file_id, '|'.join(old_categories), '|'.join(old_tags), new_cats, 'mapped', 'no-change'])
                continue
            else:
                # replace existing
                new_lines[insert_idx] = desired_line
                changed = True
        else:
            # insert
            new_lines.insert(insert_idx, desired_line)
            changed = True

        if changed:
            md.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
            rows.append([str(rel_path), file_id, '|'.join(old_categories), '|'.join(old_tags), new_cats, 'mapped', 'updated'])
        else:
            rows.append([str(rel_path), file_id, '|'.join(old_categories), '|'.join(old_tags), new_cats, 'mapped', 'no-change'])

    return rows


def write_report(rows, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['path', 'id_in_file', 'old_categories', 'old_tags', 'new_categories', 'status', 'updated'])
        for r in rows:
            w.writerow(r)


def main():
    # --- UPDATED to check for the .csv file path ---
    if not DATA_PATH.exists():
        print(f'Data mapping file not found at {DATA_PATH}')
        sys.exit(1)

    print(f'Loading mapping from {DATA_PATH}...')
    mapping = load_mapping(DATA_PATH)
    print(f'Loaded {len(mapping)} mappings')

    print('Scanning markdown files and applying categories...')
    rows = process_markdown_files(mapping)

    print(f'Writing report to {REPORT_PATH}')
    write_report(rows, REPORT_PATH)
    updated = sum(1 for r in rows if r[6] == 'updated')
    print(f'Scanned {len(rows)} files. Updated {updated} files. Report written.')


if __name__ == '__main__':
    main()
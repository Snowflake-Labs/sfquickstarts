#!/usr/bin/env python3
"""
Scan site/sfguides/src for markdown files containing an `id:` line and insert a
`language: <lang>` line immediately after the `id:` line when a mapping exists
in site/sfguides/src/_SCRIPTS/language_data.csv.

Prints a report of updated files to stdout.
"""
import csv
import os
import sys

ROOT = os.path.join("site", "sfguides", "src")
CSV = os.path.join(ROOT, "_SCRIPTS", "language_data.csv")

if not os.path.exists(CSV):
    print(f"CSV mapping not found at {CSV}")
    sys.exit(1)

# Build id -> language mapping
id_to_lang = {}
with open(CSV, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        header = []

    # find the index of the Language column (case-insensitive), and id is column 0
    lang_idx = None
    for i, h in enumerate(header):
        if h and h.strip().lower() == 'language':
            lang_idx = i
            break
    if lang_idx is None:
        # fallback: try to find header containing 'Language' substring
        for i, h in enumerate(header):
            if h and 'language' in h.lower():
                lang_idx = i
                break

    for row in reader:
        if not row:
            continue
        id_val = row[0].strip() if len(row) > 0 else ''
        lang = ''
        if lang_idx is not None and lang_idx < len(row):
            lang = row[lang_idx].strip()
        # ensure non-empty id and lang
        if id_val and lang:
            id_to_lang[id_val] = lang

print(f"Loaded {len(id_to_lang)} id->language mappings from {CSV}")

# Walk markdown files and update
updated = []
scanned = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip the scripts/_SCRIPTS folder itself
    if '_SCRIPTS' in dirpath.split(os.sep):
        continue
    for fn in filenames:
        if not fn.endswith('.md'):
            continue
        path = os.path.join(dirpath, fn)
        scanned += 1
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Failed to read {path}: {e}")
            continue

        changed = False
        # find first occurrence of a line that starts with 'id:' (ignoring leading spaces)
        for i, line in enumerate(lines):
            if line.lstrip().startswith('id:'):
                # extract id value
                parts = line.split(':', 1)
                if len(parts) < 2:
                    file_id = ''
                else:
                    file_id = parts[1].strip()
                if not file_id:
                    break
                lang = id_to_lang.get(file_id)
                if not lang:
                    break
                # determine next non-empty line index (we'll just check immediate next line as requested)
                next_idx = i + 1
                # if next line already language: update it
                if next_idx < len(lines) and lines[next_idx].lstrip().startswith('language:'):
                    existing = lines[next_idx].split(':', 1)[1].strip()
                    if existing != lang:
                        lines[next_idx] = f'language: {lang}\n'
                        changed = True
                else:
                    # insert language after id line
                    lines.insert(next_idx, f'language: {lang}\n')
                    changed = True
                break

        if changed:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                updated.append((path, file_id, lang))
            except Exception as e:
                print(f"Failed to write {path}: {e}")

# Print report
for p, fid, lang in updated:
    print(f"Updated: {p} | ID: {fid} | Language: {lang}")

print(f"Scanned {scanned} markdown files under {ROOT}; updated {len(updated)} files.")

if len(updated) == 0:
    print("No changes made.")
else:
    print("Done.")

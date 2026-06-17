#!/usr/bin/env python3
"""Generate a CSV report of markdown files under site/sfguides/src showing:
path,id_in_file,language_in_file,expected_language,language_matches_expected
"""
import csv
import os
ROOT = os.path.join("site", "sfguides", "src")
CSV = os.path.join(ROOT, "_SCRIPTS", "language_data.csv")
OUT = os.path.join("site", "sfguides", "scripts", "language_update_final_report.csv")

id_to_lang = {}
if os.path.exists(CSV):
    with open(CSV, newline='') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            header = []
        lang_idx = None
        for i,h in enumerate(header):
            if h and h.strip().lower() == 'language':
                lang_idx = i
                break
        if lang_idx is None:
            for i,h in enumerate(header):
                if h and 'language' in h.lower():
                    lang_idx = i
                    break
        for row in reader:
            if not row:
                continue
            idv = row[0].strip() if len(row)>0 else ''
            lang = ''
            if lang_idx is not None and lang_idx < len(row):
                lang = row[lang_idx].strip()
            if idv:
                id_to_lang[idv] = lang

rows = []
scanned = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    if '_SCRIPTS' in dirpath.split(os.sep):
        continue
    for fn in sorted(filenames):
        if not fn.endswith('.md'):
            continue
        path = os.path.join(dirpath, fn)
        scanned += 1
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            rows.append((path, '', '', '', 'read-error'))
            continue
        fid = ''
        lang_in_file = ''
        for line in lines:
            if not fid and line.lstrip().startswith('id:'):
                parts = line.split(':',1)
                if len(parts)>1:
                    fid = parts[1].strip()
            elif fid and not lang_in_file and line.lstrip().startswith('language:'):
                parts = line.split(':',1)
                if len(parts)>1:
                    lang_in_file = parts[1].strip()
            if fid and lang_in_file:
                break
        expected = id_to_lang.get(fid,'') if fid else ''
        match = ''
        if lang_in_file and expected:
            match = 'yes' if lang_in_file==expected else 'no'
        elif lang_in_file and not expected:
            match = 'unknown-id'
        elif not lang_in_file and expected:
            match = 'missing'
        else:
            match = 'no-id'
        rows.append((path, fid, lang_in_file, expected, match))

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['path','id_in_file','language_in_file','expected_language','match'])
    for r in rows:
        w.writerow(r)

print(f"Scanned {scanned} markdown files; wrote report to {OUT}")

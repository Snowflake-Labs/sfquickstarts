#!/usr/bin/env python3
"""
move_archived_guides.py

Move guide directories or markdown files whose mapping row has Status == 'Archived'
into the folder site/sfguides/src/_archived.

Safe by default: runs in dry-run mode unless --apply is passed.

Usage:
  python3 move_archived_guides.py        # dry-run, prints report
  python3 move_archived_guides.py --apply   # actually move files

The script writes a CSV report to site/sfguides/scripts/archived_move_report.csv
which lists each archived id, found path (if any), and action taken.
"""

from __future__ import annotations

import argparse
import csv
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


def detect_repo_root() -> Path:
    # script is located at site/sfguides/scripts
    return Path(__file__).resolve().parents[3]


def load_mapping(mapping_xlsx: Path) -> Tuple[List[str], List[str]]:
    if not mapping_xlsx.exists():
        raise FileNotFoundError(f"mapping file not found: {mapping_xlsx}")
    # try excel, fall back to csv
    try:
        df = pd.read_excel(mapping_xlsx, dtype=str, header=0).fillna("")
    except Exception:
        df = pd.read_csv(mapping_xlsx, dtype=str, header=0).fillna("")

    # find status column case-insensitively
    cols = {c.lower(): c for c in df.columns}
    status_col = None
    for k, v in cols.items():
        if k == "status":
            status_col = v
            break
    if status_col is None:
        raise KeyError("No 'Status' column found in mapping")

    id_col = df.columns[0]

    archived_mask = df[status_col].astype(str).str.strip().str.lower() == "archived"
    archived_ids = df.loc[archived_mask, id_col].astype(str).str.strip().tolist()
    # filter out empties
    archived_ids = [s for s in archived_ids if s]
    return archived_ids, df.columns.tolist()


def find_candidate_paths(src_root: Path, guide_id: str) -> List[Path]:
    """Return a list of existing paths matching this guide id inside src_root.

    Heuristics tried (in order):
      - src_root / guide_id  (directory)
      - src_root / guide_id / (guide_id + .md)
      - src_root / (guide_id + .md) (top-level file)
    """
    candidates: List[Path] = []
    # directory
    dir_path = src_root / guide_id
    if dir_path.exists():
        candidates.append(dir_path)

    # md inside directory
    md_in_dir = dir_path / f"{guide_id}.md"
    if md_in_dir.exists() and md_in_dir not in candidates:
        candidates.append(md_in_dir)

    # top-level md
    top_md = src_root / f"{guide_id}.md"
    if top_md.exists() and top_md not in candidates:
        candidates.append(top_md)

    # try relaxed match: some ids in mapping may contain characters that were used as dir names
    # try replacing spaces with underscores and vice versa
    alt_id = guide_id.replace(" ", "_")
    if alt_id != guide_id:
        alt_dir = src_root / alt_id
        if alt_dir.exists() and alt_dir not in candidates:
            candidates.append(alt_dir)
        alt_md = src_root / f"{alt_id}.md"
        if alt_md.exists() and alt_md not in candidates:
            candidates.append(alt_md)

    return candidates


def safe_move(src: Path, dst_dir: Path, apply: bool) -> Tuple[Path, str]:
    """Move src (file or directory) into dst_dir.

    If a target with the same name exists, append a timestamp. Returns the final target path and action.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / src.name
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        target = dst_dir / f"{src.name}-{stamp}"

    if apply:
        shutil.move(str(src), str(target))
        return target, "moved"
    else:
        return target, "dry-run"


def write_report(report_path: Path, rows: List[dict]):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["archived_id", "found_path", "action", "note"])
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "archived_id": r.get("archived_id", ""),
                "found_path": r.get("found_path", ""),
                "action": r.get("action", ""),
                "note": r.get("note", ""),
            })


def main(argv: Optional[List[str]] = None):
    p = argparse.ArgumentParser(description="Move archived sfguides into _archived")
    p.add_argument("--apply", action="store_true", help="Actually move files (default: dry-run)")
    p.add_argument("--mapping", type=Path, default=None, help="Path to language_data.xlsx or CSV")
    p.add_argument("--src-root", type=Path, default=None, help="Path to site/sfguides/src (optional)")
    p.add_argument("--report", type=Path, default=None, help="CSV report output path")
    args = p.parse_args(argv)

    repo_root = detect_repo_root()
    src_root = args.src_root or (repo_root / "site" / "sfguides" / "src")
    scripts_dir = repo_root / "site" / "sfguides" / "scripts"
    mapping_path = args.mapping or (repo_root / "site" / "sfguides" / "src" / "_SCRIPTS" / "language_data.xlsx")
    report_path = args.report or (scripts_dir / "archived_move_report.csv")
    archive_dir = src_root / "_archived"

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("Repo root: %s", repo_root)
    logging.info("Source root: %s", src_root)
    logging.info("Mapping: %s", mapping_path)
    logging.info("Archive destination: %s", archive_dir)
    logging.info("Apply mode: %s", args.apply)

    archived_ids, _ = load_mapping(mapping_path)
    rows = []

    for aid in archived_ids:
        candidates = find_candidate_paths(src_root, aid)
        if not candidates:
            rows.append({
                "archived_id": aid,
                "found_path": "",
                "action": "not-found",
                "note": "no matching file or directory under src",
            })
            logging.info("NOT FOUND: %s", aid)
            continue

        # Prefer moving the directory if present
        moved_any = False
        for cand in candidates:
            # If candidate is a file inside a directory with same name, allow moving the file only
            try:
                target, action = safe_move(cand, archive_dir, args.apply)
                rows.append({
                    "archived_id": aid,
                    "found_path": str(cand),
                    "action": action,
                    "note": f"target={target}"
                })
                logging.info("%s -> %s  (%s)", cand, target, action)
                moved_any = True
                # If we moved the directory, don't attempt to move other candidates
                if cand.is_dir():
                    break
            except Exception as e:
                rows.append({
                    "archived_id": aid,
                    "found_path": str(cand),
                    "action": "failed",
                    "note": str(e),
                })
                logging.info("FAILED moving %s: %s", cand, e)

        if not moved_any:
            # already recorded each candidate as failed above; nothing more to do
            pass

    write_report(report_path, rows)
    logging.info("Wrote report to %s", report_path)
    # summary
    from collections import Counter

    counts = Counter(r["action"] for r in rows)
    logging.info("Summary: %s", dict(counts))


if __name__ == "__main__":
    main()

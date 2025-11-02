#!/usr/bin/env python3
"""
Update crosslinks in markdown files based on mappings in links.csv.

- Matches old quickstarts links and common variants:
  - trailing slash
  - "/index.html"
  - query strings and/or fragments (e.g., ?q=...#section)
  - drops any query/fragment suffix from the new URL

Outputs:
  - Progress logs to stdout
  - CSV summary report with counts per mapping and files modified
  - Optional detailed report with per-file counts
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


QUICKSTARTS_DOMAIN = "quickstarts.snowflake.com"


@dataclass
class Mapping:
    old_url: str
    new_url: str
    base_path: str  # e.g., "/guide/data_engineering_pipelines_with_snowpark_python"
    pattern_abs: re.Pattern[str]
    pattern_rel: re.Pattern[str]


def normalize_old_base(old_url: str) -> Optional[str]:
    """Return canonical base old URL without trailing slash or /index.html.

    Example:
      https://quickstarts.snowflake.com/guide/foo/ -> https://quickstarts.snowflake.com/guide/foo
      https://quickstarts.snowflake.com/guide/foo/index.html -> https://quickstarts.snowflake.com/guide/foo
    """
    if not old_url:
        return None
    parsed = urlparse(old_url.strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    if parsed.netloc.lower() != QUICKSTARTS_DOMAIN:
        return None
    path = parsed.path or "/"
    if path.endswith("/index.html"):
        path = path[: -len("/index.html")]
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def ensure_trailing_slash(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    return url if url.endswith("/") else url + "/"


def build_pattern_for_base(base_path: str) -> re.Pattern[str]:
    """Build a regex pattern that matches variants of the old base URL.

    Variants handled:
      - with or without trailing slash
      - optional /index.html
      - optional trailing slash before suffix
      - optional suffix starting with ? or # (query/fragment)
    """
    escaped_path = re.escape(base_path)
    # Full pattern matches http(s)://quickstarts.snowflake.com{base}(optional index.html)(optional /)(optional suffix)
    pattern_str = (
        rf"https?://{re.escape(QUICKSTARTS_DOMAIN)}{escaped_path}"
        rf"(?:/index\.html)?/?"
        rf"(?P<suffix>(?:[?#][^\s)\]]*)?)"
        # Require a boundary after the URL so we don't match partial paths
        rf"(?=$|[\s)\]\"'])"
    )
    return re.compile(pattern_str)


def build_relative_pattern_for_base(base_path: str) -> re.Pattern[str]:
    """Regex for relative path variants like /guide/foo, /guide/foo/index.html, optional suffix.

    Requires a boundary after the URL to avoid partial matches; similar to absolute pattern.
    """
    escaped_path = re.escape(base_path)
    pattern_str = (
        rf"{escaped_path}"
        rf"(?:/index\.html)?/?"
        rf"(?P<suffix>(?:[?#][^\s)\]]*)?)"
        rf"(?=$|[\s)\]\"'])"
    )
    return re.compile(pattern_str)


def read_mappings(csv_path: Path) -> List[Mapping]:
    mappings: List[Mapping] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Normalize headers to lower-case for robustness
        headers = {h.lower(): h for h in reader.fieldnames or []}
        old_key = next((k for k in headers if k.strip() == "old url"), None)
        new_key = next((k for k in headers if k.strip() == "new url"), None)
        if old_key is None or new_key is None:
            print(
                "ERROR: links.csv must contain 'old url' and 'new url' columns.",
                file=sys.stderr,
            )
            sys.exit(1)
        for row in reader:
            old_url_raw = row[headers[old_key]].strip() if row.get(headers[old_key]) else ""
            new_url_raw = row[headers[new_key]].strip() if row.get(headers[new_key]) else ""
            if not old_url_raw or not new_url_raw:
                # Skip incomplete mappings
                continue
            old_base = normalize_old_base(old_url_raw)
            if not old_base:
                continue
            parsed = urlparse(old_base)
            base_path = parsed.path or "/"
            pattern_abs = build_pattern_for_base(base_path)
            pattern_rel = build_relative_pattern_for_base(base_path)
            mappings.append(
                Mapping(
                    old_url=old_base,
                    new_url=new_url_raw,
                    base_path=base_path,
                    pattern_abs=pattern_abs,
                    pattern_rel=pattern_rel,
                )
            )
    return mappings


def sanitize_source_path(source: str) -> Optional[str]:
    """Normalize a firebase.json redirect source to a path under /guide.

    - Accepts absolute URLs or paths
    - Strips firebase pattern suffixes like `{,/**}`
    - Returns a path starting with '/'
    """
    if not source:
        return None
    src = source.strip()
    # Remove firebase pattern suffix like {,/**}
    if '{' in src:
        src = src.split('{', 1)[0].strip()
    # Convert full URL to path
    if src.startswith('http://') or src.startswith('https://'):
        parsed = urlparse(src)
        if parsed.netloc.lower() != QUICKSTARTS_DOMAIN:
            return None
        path = parsed.path or '/'
    else:
        path = src if src.startswith('/') else f'/{src}'
    # Collapse any repeated slashes
    path = re.sub(r'/+', '/', path)
    # Remove trailing slash except root
    if path != '/' and path.endswith('/'):
        path = path[:-1]
    return path


def read_firebase_redirects(firebase_path: Path) -> List[Mapping]:
    mappings: List[Mapping] = []
    try:
        data = json.loads(firebase_path.read_text(encoding='utf-8'))
    except Exception:
        return mappings
    redirects = (
        data.get('hosting', {}).get('redirects', [])
        if isinstance(data, dict) else []
    )
    for r in redirects:
        if not isinstance(r, dict):
            continue
        source = r.get('source')
        dest = r.get('destination')
        if not source or not dest:
            continue
        base_path = sanitize_source_path(source)
        if not base_path:
            continue
        old_base_url = f"https://{QUICKSTARTS_DOMAIN}{base_path}"
        pattern_abs = build_pattern_for_base(base_path)
        pattern_rel = build_relative_pattern_for_base(base_path)
        mappings.append(Mapping(
            old_url=old_base_url,
            new_url=dest.strip(),
            base_path=base_path,
            pattern_abs=pattern_abs,
            pattern_rel=pattern_rel,
        ))
    return mappings


def find_markdown_files(root: Path, include_globs: List[str]) -> Iterable[Path]:
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            lower = name.lower()
            if any(lower.endswith(g) for g in include_globs):
                yield p


def replace_in_text(text: str, mappings: List[Mapping]) -> Tuple[str, Dict[str, int]]:
    counts: Dict[str, int] = defaultdict(int)

    def normalized_replacement(new_base_url: str) -> str:
        url = new_base_url.strip()
        if not url:
            return url
        parsed = urlparse(url)
        # Drop any suffixes from the new URL; ensure trailing slash
        if parsed.scheme and parsed.netloc:
            path = parsed.path or "/"
            if path.endswith("/index.html"):
                path = path[: -len("/index.html")]
            if path != "/" and path.endswith("/") is False:
                path = path + "/"
            host = parsed.netloc.lower()
            if host in ("www.snowflake.com", "snowflake.com"):
                return path
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        # Already relative
        path = url
        if path.endswith("/index.html"):
            path = path[: -len("/index.html")]
        return ensure_trailing_slash(path)

    def make_replacer(new_base_url: str):
        target_base = normalized_replacement(new_base_url)

        def _repl(match: re.Match[str]) -> str:
            # Do not carry over old query/fragment suffixes to the new URL
            return f"{target_base}"

        return _repl

    new_text = text
    # Replace absolute quickstarts URLs first (safe anywhere)
    for m in sorted(mappings, key=lambda x: len(x.base_path), reverse=True):
        repl = make_replacer(m.new_url)
        new_text, n_abs = m.pattern_abs.subn(repl, new_text)
        if n_abs:
            counts[m.old_url] += n_abs

    # Relativize any snowflake.com developer guide links in standard link contexts
    def path_only(url: str) -> str:
        p = urlparse(url)
        path = p.path or "/"
        if path.endswith("/index.html"):
            path = path[: -len("/index.html")]
        return ensure_trailing_slash(path)

    md_abs = re.compile(r"(\]\(\s*)(?P<url>https?://(?:www\.)?snowflake\.com(?P<path>/[^)\s]+))(\s*\))", re.IGNORECASE)
    html_abs = re.compile(r"(href\s*=\s*['\"])(?P<url>https?://(?:www\.)?snowflake\.com(?P<path>/[^'\"\s>]+))(['\"])", re.IGNORECASE)

    def md_abs_repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{path_only(match.group('url'))}{match.group(4)}"

    def html_abs_repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{path_only(match.group('url'))}{match.group(4)}"

    new_text = md_abs.sub(md_abs_repl, new_text)
    new_text = html_abs.sub(html_abs_repl, new_text)

    # Replace ONLY relative links that start with /guide inside href= or markdown link syntax
    base_to_new: Dict[str, str] = {m.base_path: normalized_replacement(m.new_url) for m in mappings}
    base_to_old: Dict[str, str] = {m.base_path: m.old_url for m in mappings}

    md_link = re.compile(r"(\]\(\s*)(?P<url>/guide/[^)\s]+)(\s*\))")
    html_href = re.compile(r"(href\s*=\s*['\"])(?P<url>/guide/[^'\"\s>]+)(['\"])", re.IGNORECASE)

    def canonicalize_base(path: str) -> str:
        # strip query/fragment
        path_only = path.split('#', 1)[0].split('?', 1)[0]
        if path_only.endswith('/index.html'):
            path_only = path_only[:-len('/index.html')]
        if path_only != '/' and path_only.endswith('/'):
            path_only = path_only[:-1]
        return path_only

    def md_repl(match: re.Match[str]) -> str:
        prefix, url, suffix = match.group(1), match.group('url'), match.group(3)
        base = canonicalize_base(url)
        new_target = base_to_new.get(base)
        if not new_target:
            return match.group(0)
        old_key = base_to_old.get(base)
        if old_key:
            counts[old_key] += 1
        return f"{prefix}{new_target}{suffix}"

    def href_repl(match: re.Match[str]) -> str:
        prefix, url, suffix = match.group(1), match.group('url'), match.group(3)
        base = canonicalize_base(url)
        new_target = base_to_new.get(base)
        if not new_target:
            return match.group(0)
        old_key = base_to_old.get(base)
        if old_key:
            counts[old_key] += 1
        return f"{prefix}{new_target}{suffix}"

    new_text = md_link.sub(md_repl, new_text)
    new_text = html_href.sub(href_repl, new_text)
    return new_text, counts


def mask_images(
    text: str, mappings: List[Mapping]
) -> Tuple[str, Dict[str, str], Dict[str, int]]:
    """Mask image URLs so they are not modified, while counting matches per mapping.

    Supports:
      - Markdown images: ![alt](url)
      - HTML images: <img src="url" ...>
    """
    placeholders: Dict[str, str] = {}
    image_counts: Dict[str, int] = defaultdict(int)

    # Match quickstarts absolute or /guide relative URLs inside markdown image syntax
    md_img = re.compile(
        r"!\[[^\]]*\]\(\s*(?P<url>(?:https?://" + re.escape(QUICKSTARTS_DOMAIN) + r"|/guide/)[^)\s]+)\s*\)"
    )
    # Match quickstarts absolute or /guide relative URLs inside HTML <img src="...">
    html_img = re.compile(
        r"<img[^>]*\s+src\s*=\s*['\"](?P<url>(?:https?://" + re.escape(QUICKSTARTS_DOMAIN) + r"|/guide/)[^'\"\s>]+)['\"][^>]*>",
        re.IGNORECASE,
    )

    def match_mapping(url: str) -> Optional[Mapping]:
        for m in mappings:
            if m.pattern_abs.fullmatch(url) or m.pattern_rel.fullmatch(url):
                return m
        return None

    def md_img_repl(match: re.Match[str]) -> str:
        url = match.group("url")
        m = match_mapping(url)
        if m is None:
            return match.group(0)
        token = f"__QS_IMG__{len(placeholders)}__"
        placeholders[token] = url
        image_counts[m.old_url] += 1
        return match.group(0).replace(url, token, 1)

    def html_img_repl(match: re.Match[str]) -> str:
        url = match.group("url")
        m = match_mapping(url)
        if m is None:
            return match.group(0)
        token = f"__QS_IMG__{len(placeholders)}__"
        placeholders[token] = url
        image_counts[m.old_url] += 1
        return match.group(0).replace(url, token, 1)

    masked = md_img.sub(md_img_repl, text)
    masked = html_img.sub(html_img_repl, masked)

    return masked, placeholders, image_counts


def write_reports(
    summary_counts: Dict[str, int],
    old_to_new: Dict[str, str],
    summary_files: Dict[str, int],
    detailed_rows: List[Tuple[str, str, str, str, int]],
    report_dir: Path,
    detailed: bool,
    summary_image_counts: Dict[str, int],
    summary_image_files: Dict[str, int],
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / "crosslink_update_report_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["old_url", "new_url", "total_replacements", "files_modified", "image_matches", "files_with_image_matches"])
        for old_url, total in sorted(summary_counts.items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([
                old_url,
                old_to_new.get(old_url, ""),
                total,
                summary_files.get(old_url, 0),
                summary_image_counts.get(old_url, 0),
                summary_image_files.get(old_url, 0),
            ])
    if detailed:
        detailed_path = report_dir / "crosslink_update_report_detailed.csv"
        with detailed_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "old_url", "new_url", "kind", "count"])
            for row in detailed_rows:
                writer.writerow(list(row))
        print(f"Detailed report: {detailed_path}")
    print(f"Summary report:  {summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update crosslinks in markdown files using links.csv")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan for markdown files (default: current directory)",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        type=Path,
        default=None,
        help="Path to links.csv (default: <root>/links.csv)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Directory to write CSV report(s) (default: <root>)",
    )
    parser.add_argument(
        "--firebase",
        dest="firebase_path",
        type=Path,
        default=None,
        help="Path to firebase.json for extra redirects (default: <root>/site/firebase.json if present)",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=".md",
        help="Comma-separated list of file extensions to include (default: .md)",
    )
    parser.add_argument(
        "--include-detailed",
        action="store_true",
        help="Also write a detailed per-file report",
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()
    csv_path: Path = (args.csv_path or (root / "links.csv")).resolve()
    report_dir: Path = (args.report_dir or root).resolve()
    include_exts = [e.strip().lower() for e in args.extensions.split(",") if e.strip()]

    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Root: {root}")
    print(f"CSV:  {csv_path}")
    print(f"Report dir: {report_dir}")
    print("Reading mappings...")
    mappings = read_mappings(csv_path)
    # Optionally augment mappings from firebase.json redirects
    fb_path = args.firebase_path or (root / "site" / "firebase.json")
    if fb_path.exists():
        fb_maps = read_firebase_redirects(fb_path)
        # Prefer CSV mappings when duplicates (by old_url) exist
        existing = {m.old_url for m in mappings}
        extra = [m for m in fb_maps if m.old_url not in existing]
        if extra:
            mappings.extend(extra)
            print(f"Augmented with {len(extra)} firebase redirects (from {len(fb_maps)} total)")
    if not mappings:
        print("No valid mappings found. Exiting.")
        return
    print(f"Loaded {len(mappings)} mappings.")

    # For reporting, show the normalized replacement string that will be used
    def normalized_replacement_for_report(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc and parsed.netloc.lower() in ("www.snowflake.com", "snowflake.com"):
            path = parsed.path or "/"
            if path.endswith("/index.html"):
                path = path[: -len("/index.html")]
            return ensure_trailing_slash(path)
        return ensure_trailing_slash(url)

    old_to_new: Dict[str, str] = {m.old_url: normalized_replacement_for_report(m.new_url) for m in mappings}

    # Aggregation structures
    summary_counts: Dict[str, int] = defaultdict(int)
    summary_files: Dict[str, int] = defaultdict(int)
    detailed_rows: List[Tuple[str, str, str, str, int]] = []
    summary_image_counts: Dict[str, int] = defaultdict(int)
    summary_image_files: Dict[str, int] = defaultdict(int)

    files_processed = 0
    files_modified = 0

    for file_path in find_markdown_files(root, include_exts):
        if file_path.resolve() == csv_path:
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Skipping unreadable file: {file_path} ({e})")
            continue
        files_processed += 1

        masked_text, placeholders, image_counts_file = mask_images(text, mappings)
        new_text, counts = replace_in_text(masked_text, mappings)
        # Restore masked image URLs (unchanged)
        for token, original in placeholders.items():
            new_text = new_text.replace(token, original)

        # Aggregate image counts (no modifications made)
        if image_counts_file:
            for old_url, n_img in image_counts_file.items():
                summary_image_counts[old_url] += n_img
                summary_image_files[old_url] += 1
                if args.include_detailed:
                    detailed_rows.append((
                        str(file_path),
                        old_url,
                        old_to_new.get(old_url, ""),
                        "image_match",
                        n_img,
                    ))

        if not counts:
            if image_counts_file:
                print(f"Images noted (no change): {file_path} (+{sum(image_counts_file.values())} matches)")
            elif files_processed % 200 == 0:
                print(f"Processed {files_processed} files...")
            # Only continue; file not modified unless counts > 0
            if not counts:
                continue

        # File had replacements
        per_file_total = sum(counts.values())
        files_modified += 1
        print(f"Updated: {file_path}  (+{per_file_total} replacements)")

        # Update aggregates
        for old_url, n in counts.items():
            summary_counts[old_url] += n
            summary_files[old_url] += 1
            if args.include_detailed:
                detailed_rows.append((
                    str(file_path),
                    old_url,
                    old_to_new.get(old_url, ""),
                    "link_replacement",
                    n,
                ))

        # Write file back
        try:
            file_path.write_text(new_text, encoding="utf-8")
        except Exception as e:
            print(f"ERROR writing file: {file_path} ({e})", file=sys.stderr)

    print("")
    print(f"Files processed: {files_processed}")
    print(f"Files modified:  {files_modified}")
    print(f"Total replacements: {sum(summary_counts.values())}")

    write_reports(
        summary_counts=summary_counts,
        old_to_new=old_to_new,
        summary_files=summary_files,
        detailed_rows=detailed_rows,
        report_dir=report_dir,
        detailed=args.include_detailed,
        summary_image_counts=summary_image_counts,
        summary_image_files=summary_image_files,
    )


if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""Run every content check and record the verdict.

Checks are split into blocking and informational. Profanity is deliberately
informational: a flagged word is reported on the pull request but does not block it,
because the wordlist matches too much ordinary technical prose.

Environment:
    BASE_SHA  base commit of the pull request, recorded for debugging
    PROFANITY_BLOCKLIST         extra words from a repository variable
    PROFANITY_BLOCKLIST_SECRET  extra words from a repository secret
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import checks
import renames
from lib import gha

CHANGES_FILE = Path("pr-changes.json")
RESULTS_FILE = Path("validation-results.json")
CONTENT_DIR = Path("pr")
WORDLIST = Path(__file__).resolve().parent.parent / "data" / "profanity.txt"

Check = Callable[[checks.Content], dict[str, Any] | None]

BLOCKING: list[tuple[str, str, Check]] = [
    (
        "Renamed folders check",
        "folder-rename-error.json",
        lambda content: renames.check(content.entries),
    ),
    (
        "Single markdown file per folder",
        "multiple-md-error.json",
        checks.check_multiple_markdown,
    ),
    ("Large files check (>1MB)", "large-files-error.json", checks.check_large_files),
    ("Categories syntax validation", "categories-error.json", checks.check_categories),
    (
        "Frontmatter validation (id must match folder name)",
        "frontmatter-error.json",
        checks.check_frontmatter,
    ),
    (
        "Language validation (allowed: en, es, it, fr, de, ja, ko, pt_br)",
        "validation-error.json",
        checks.check_language,
    ),
]


def _profanity(content: checks.Content) -> dict[str, Any] | None:
    words = checks.load_wordlist(WORDLIST)
    words |= checks.parse_blocklist(
        os.environ.get("PROFANITY_BLOCKLIST"),
        os.environ.get("PROFANITY_BLOCKLIST_SECRET"),
    )
    return checks.check_profanity(content, words)


INFORMATIONAL: list[tuple[str, Check]] = [
    ("profanity-report.json", _profanity),
    ("non-image-assets-warning.json", checks.check_non_image_assets),
    ("non-markdown-root-info.json", checks.check_non_markdown_root),
]


def load_changes() -> dict[str, Any]:
    """Return the state collect_pr_changes.py recorded."""
    if not CHANGES_FILE.is_file():
        return {}
    data = json.loads(CHANGES_FILE.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_report(name: str, payload: dict[str, Any]) -> None:
    """Write one check's report for the deploy workflow to render."""
    Path(name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {name}")


def run(content: checks.Content) -> list[str]:
    """Run every check, writing reports, and return the blocking failures."""
    failed = []
    for label, report_name, check in BLOCKING:
        payload = check(content)
        if payload is None:
            print(f"PASS  {label}")
            continue
        write_report(report_name, payload)
        failed.append(label)
        print(f"FAIL  {label}")

    for report_name, check in INFORMATIONAL:
        payload = check(content)
        if payload is not None:
            write_report(report_name, payload)

    return failed


def write_results(changes: dict[str, Any], passed: bool) -> None:
    """Record the verdict the deploy workflow reads back out of the artifact."""
    results = {
        "pr_number": changes.get("pr_number", 0),
        "head_sha": changes.get("head_sha", ""),
        "base_sha": os.environ.get("BASE_SHA", ""),
        "has_relevant_changes": bool(changes.get("has_relevant_changes")),
        "all_validations_passed": passed,
        # stage_payloads.py fills this in once it knows each guide's language.
        "quickstart_names_json": [],
        "md_file_count": changes.get("md_file_count", 0),
        "has_sidebar_changes": bool(changes.get("sidebar_files")),
        "sidebar_json_files": changes.get("sidebar_files", []),
        "has_journey_guides": bool(changes.get("journey_guides")),
        "journey_guides_json": changes.get("journey_guides", []),
    }
    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


def main() -> int:
    """Validate the collected changes and fail the job if a blocking check failed."""
    changes = load_changes()

    if not changes.get("has_relevant_changes"):
        print("No relevant changes; nothing to validate")
        gha.set_output("all_passed", True)
        write_results(changes, True)
        return 0

    failed = run(checks.Content(changes=changes, root=CONTENT_DIR))
    passed = not failed

    gha.set_output("all_passed", passed)
    write_results(changes, passed)

    if passed:
        print("All validations passed")
        return 0

    print("\nVALIDATION FAILURES:")
    for label in failed:
        print(f"  - {label}")
    print("\nPR comments with error details will be posted by the deploy workflow.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

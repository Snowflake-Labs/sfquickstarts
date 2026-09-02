#!/usr/bin/env python3
"""Stage validated pull request content to AEM.

Runs on a job holding staging credentials, so it treats everything upstream as
untrusted: every name is re-validated here even though resolve_context.py already
validated it, and artifact lookups must resolve inside a fixed directory.

The AEM calls themselves are placeholders in this repository.

Usage:
    stage_to_aem.py {quickstart,sidebars,journey}

Environment:
    ARTIFACT_DIR     directory the validation artifact was downloaded into
    HEAD_SHA         commit being staged (quickstart and journey)
    QUICKSTART_NAME  quickstart only
    LANGUAGE         quickstart only
    GUIDE_NAME       journey only
    SOURCE_PATH      journey only
    SIDEBAR_FILES    sidebars only, a JSON array of repository paths
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from lib import validate

CF_ROOT = "/content/dam/snowflake-site"
JOURNEY_PAGE_ROOT = "/content/snowflake-site/global/en/developers/guides"
SIDEBAR_DAM_FOLDER = "snowflake-site/developers/technical/guides-navigation"


def placeholder(message: str) -> None:
    """Record an AEM call this repository deliberately does not make."""
    print(f"[PLACEHOLDER] {message}")


def artifact_dir() -> Path:
    """Return the directory the validation artifact was downloaded into."""
    return Path(os.environ.get("ARTIFACT_DIR", "artifact")).resolve()


def within(root: Path, *parts: str) -> Path | None:
    """Return a path under `root`, or None if it would escape or is a symlink."""
    candidate = root.joinpath(*parts)
    if candidate.is_symlink():
        return None
    resolved = candidate.resolve()
    return resolved if resolved.is_relative_to(root) else None


def stage_quickstart() -> None:
    """Report what staging one quickstart would upload."""
    name = validate.guide_name(os.environ.get("QUICKSTART_NAME"))
    language = validate.language(os.environ.get("LANGUAGE") or validate.DEFAULT_LANGUAGE)
    head_sha = validate.sha40(os.environ.get("HEAD_SHA"))
    root = artifact_dir()

    placeholder("Would stage quickstart to AEM:")
    print(f"  Name:             {name}")
    print(f"  Language:         {language}")
    fragment = f"{CF_ROOT}/{language}/content-fragments/quickstarts/{name}-{head_sha}"
    print(f"  Content fragment: {fragment}")

    for prefix in ("parsed_content", "aem_payload"):
        payload = within(root, f"{prefix}_{name}.json")
        if payload is not None and payload.is_file():
            print(f"  Available:        {payload.name}")

    images = within(root, "images", name)
    if images is not None and images.is_dir():
        count = sum(1 for path in images.rglob("*") if path.is_file())
        print(f"  Images:           {count} file(s)")

    placeholder("AEM staging skipped in test environment")


def stage_sidebars() -> None:
    """Report what uploading the changed sidebar files would do."""
    try:
        entries = json.loads(os.environ.get("SIDEBAR_FILES") or "[]")
    except json.JSONDecodeError as exc:
        print(f"::warning::SIDEBAR_FILES is not valid JSON: {exc}")
        entries = []
    root = artifact_dir()

    placeholder(f"Would upload sidebar JSON files to AEM DAM ({SIDEBAR_DAM_FOLDER}):")
    for entry in entries if isinstance(entries, list) else []:
        try:
            name = Path(validate.repo_path(entry)).name
        except validate.ValidationError as exc:
            print(f"::warning::skipping sidebar file: {exc}")
            continue
        staged = within(root, "sidebar-files", name)
        available = staged is not None and staged.is_file()
        print(f"  - {name} ({'available in artifact' if available else 'not in artifact'})")

    placeholder("Sidebar JSON upload skipped in test environment")


def stage_journey() -> None:
    """Report what staging one journey guide would upload."""
    name = validate.guide_name(os.environ.get("GUIDE_NAME"))
    source_path = validate.repo_path(os.environ.get("SOURCE_PATH"))
    head_sha = validate.sha40(os.environ.get("HEAD_SHA"))

    placeholder("Would stage journey guide to AEM:")
    print(f"  Name:         {name}")
    print(f"  Source:       {source_path}")
    print(f"  Staging page: {JOURNEY_PAGE_ROOT}/{name}-{head_sha}")
    placeholder("AEM journey guide staging skipped in test environment")


def main() -> int:
    """Run the requested staging step."""
    parser = argparse.ArgumentParser(description="Stage validated content to AEM.")
    parser.add_argument("kind", choices=["quickstart", "sidebars", "journey"])
    kind = parser.parse_args().kind

    {"quickstart": stage_quickstart, "sidebars": stage_sidebars, "journey": stage_journey}[kind]()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except validate.ValidationError as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

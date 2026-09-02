#!/usr/bin/env python3
"""Upload the journey sidebar JSON files to the AEM DAM.

Standard library only, so the job holding production credentials installs nothing.
The AEM calls are placeholders in this repository.

Environment:
    SIDEBAR_FILES  JSON array of repository-relative sidebar paths
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from lib import validate

DAM_FOLDER = "snowflake-site/developers/technical/guides-navigation"
DAM_PATH = f"/content/dam/{DAM_FOLDER}"


def placeholder(message: str) -> None:
    """Record an AEM call this repository deliberately does not make."""
    print(f"[PLACEHOLDER] {message}")


def sidebar_paths(raw: str | None) -> list[Path]:
    """Return the sidebar files to upload, dropping anything that fails validation."""
    try:
        entries = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        print(f"::warning::SIDEBAR_FILES is not valid JSON: {exc}")
        return []
    if not isinstance(entries, list):
        return []

    paths = []
    for entry in entries:
        try:
            path = Path(validate.repo_path(entry))
        except validate.ValidationError as exc:
            print(f"::warning::skipping sidebar file: {exc}")
            continue
        if not path.is_file() or path.is_symlink():
            print(f"::warning::sidebar file not present in the checkout: {path}")
            continue
        paths.append(path)
    return paths


def main() -> int:
    """Upload and publish every changed sidebar file."""
    paths = sidebar_paths(os.environ.get("SIDEBAR_FILES"))
    if not paths:
        print("No sidebar files to upload")
        return 0

    placeholder(f"Would ensure DAM folder hierarchy exists: {DAM_PATH}")
    for path in paths:
        # The real call is upload_dam_asset.upload(path, DAM_FOLDER).
        placeholder(f"Would upload {path} to {DAM_PATH}/{path.name}")
    for path in paths:
        placeholder(f"Would publish {DAM_PATH}/{path.name}")

    print(f"Handled {len(paths)} sidebar file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

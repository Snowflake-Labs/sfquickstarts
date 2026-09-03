#!/usr/bin/env python3
"""Upload the journey sidebar JSON files to the AEM DAM.

Standard library only, so the job holding production credentials installs nothing.

Environment:
    SIDEBAR_FILES  JSON array of repository-relative sidebar paths
    AEM_URL, AEM_USERNAME, AEM_PASSWORD  target instance and credentials
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from lib import aem, validate
from publish import upload_dam_asset

DAM_ROOT = "snowflake-site"
DAM_FOLDER = f"{DAM_ROOT}/developers/technical/guides-navigation"
DAM_PATH = f"/content/dam/{DAM_FOLDER}"

# Each level has to exist before the next one can be created.
DAM_LEVELS = ("developers", "developers/technical", "developers/technical/guides-navigation")


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


def ensure_hierarchy(client: aem.Client) -> None:
    """Create each level of the sidebar folder path that is missing."""
    for level in DAM_LEVELS:
        client.ensure_asset_folder(f"/content/dam/{DAM_ROOT}/{level}")

    if not client.exists(DAM_PATH):
        msg = f"DAM folder could not be created: {DAM_PATH}"
        raise aem.AemError(msg)
    print(f"DAM folder ready: {DAM_PATH}")


def main() -> int:
    """Upload and publish every changed sidebar file."""
    paths = sidebar_paths(os.environ.get("SIDEBAR_FILES"))
    if not paths:
        print("No sidebar files to upload")
        return 0

    client = aem.Client.from_env()
    ensure_hierarchy(client)

    for path in paths:
        upload_dam_asset.upload(path, DAM_FOLDER)

    # A sidebar that uploaded but did not activate is recoverable by republishing,
    # so one failure here does not abandon the rest.
    for path in paths:
        try:
            client.replicate(f"{DAM_PATH}/{path.name}", f"publish {path.name}")
        except aem.AemError as exc:
            print(f"::warning::publish failed for {path.name}: {exc}")

    print(f"Handled {len(paths)} sidebar file(s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (aem.AemError, upload_dam_asset.UploadError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

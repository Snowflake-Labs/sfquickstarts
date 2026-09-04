#!/usr/bin/env python3
"""Stage validated pull request content to AEM.

Runs on a job holding staging credentials, so it treats everything upstream as
untrusted: every name is re-validated here even though resolve_context.py already
validated it, and artifact lookups must resolve inside a fixed directory.

Staged content is suffixed with the head commit, so each pull request gets its own
content fragment and page rather than overwriting the published one.

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
import time
from pathlib import Path

from lib import aem, validate
from publish import upload_dam_asset

CF_ROOT = "/content/dam/snowflake-site"
PAGE_ROOT = "/content/snowflake-site/global"
DAM_GUIDES_PATH = "/content/dam/snowflake-site/developers/guides"
BASE_CF_PATH = f"{CF_ROOT}/en/content-fragments/base-fragments/base-quickstart-cf"
PAGE_BASE_PATH_DEFAULT = f"{PAGE_ROOT}/en/developers/guides/quickstart-base"

SIDEBAR_DAM_ROOT = "snowflake-site"
SIDEBAR_DAM_FOLDER = f"{SIDEBAR_DAM_ROOT}/developers/technical/guides-navigation"
SIDEBAR_DAM_PATH = f"/content/dam/{SIDEBAR_DAM_FOLDER}"
SIDEBAR_LEVELS = ("developers", "developers/technical", "developers/technical/guides-navigation")

# AEM finishes each of these asynchronously. The durations are the ones the shell
# used; a staged page needs longer than a published one because the copy is fresh.
CF_COPY_SETTLE_SECONDS = 3
PAGE_COPY_SETTLE_SECONDS = 8
IMAGE_PROCESSING_SECONDS = 15
PAGE_PROCESSING_SECONDS = 60


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


def payload_field(root: Path, name: str, field: str) -> str:
    """Read one pre-encoded form body out of the artifact's payload file.

    The file is opened by a name re-derived from validated inputs, never by a name
    taken from the artifact, and is treated purely as data.
    """
    path = within(root, f"aem_payload_{name}.json")
    if path is None or not path.is_file():
        msg = f"aem_payload_{name}.json is missing from the artifact"
        raise aem.AemError(msg)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"aem_payload_{name}.json could not be read: {exc}"
        raise aem.AemError(msg) from exc

    value = payload.get(field) if isinstance(payload, dict) else None
    if not isinstance(value, str) or not value:
        msg = f"aem_payload_{name}.json has no {field}"
        raise aem.AemError(msg)
    return value


def stage_images(client: aem.Client, root: Path, name: str) -> int:
    """Upload the guide's images from the artifact to the staging DAM folder."""
    images = within(root, "images", name)
    if images is None or not images.is_dir():
        return 0

    files = sorted(p for p in images.iterdir() if p.is_file() and not p.is_symlink())
    if not files:
        return 0

    dam_folder = f"{DAM_GUIDES_PATH}/{name}"
    client.ensure_asset_folder(dam_folder)
    for image in files:
        client.upload_asset(image, dam_folder)
    return len(files)


def stage_content_fragment(
    client: aem.Client, root: Path, name: str, language: str, sha: str
) -> str:
    """Copy the base fragment to a commit-specific path and fill it in."""
    parent = f"{CF_ROOT}/{language}/content-fragments/quickstarts"
    client.ensure_asset_folder(parent)

    cf_path = f"{parent}/{name}-{sha}"
    print(f"Copying base fragment to {cf_path}")
    client.copy(BASE_CF_PATH, cf_path, "copy base content fragment", deep=True)
    time.sleep(CF_COPY_SETTLE_SECONDS)

    body = payload_field(root, name, "content_fragment_payload")
    client.post(f"{cf_path}/jcr:content", body, "update content fragment")
    return cf_path


def stage_page(client: aem.Client, root: Path, name: str, language: str, sha: str) -> str:
    """Copy the base page to a commit-specific path and point it at the fragment."""
    base = os.environ.get("PAGE_BASE_PATH") or PAGE_BASE_PATH_DEFAULT
    if not client.exists(base):
        msg = f"base page does not exist: {base}"
        raise aem.AemError(msg)

    page_path = f"{PAGE_ROOT}/{language}/developers/guides/{name}-{sha}"
    print(f"Creating staging page {page_path}")
    client.copy(base, page_path, "create staging page")
    time.sleep(PAGE_COPY_SETTLE_SECONDS)

    client.post(page_path, payload_field(root, name, "page_payload"), "update staging page")
    return page_path


def stage_guide(name: str, language: str) -> None:
    """Stage one guide: its content fragment, its images, then its page."""
    sha = validate.sha40(os.environ.get("HEAD_SHA"))
    root = artifact_dir()
    client = aem.Client.from_env()

    cf_path = stage_content_fragment(client, root, name, language, sha)
    count = stage_images(client, root, name)
    print(f"Uploaded {count} image(s)")
    if count:
        time.sleep(IMAGE_PROCESSING_SECONDS)
    client.replicate(cf_path, "publish content fragment")

    page_path = stage_page(client, root, name, language, sha)
    time.sleep(PAGE_PROCESSING_SECONDS)
    client.replicate(page_path, "publish staging page")
    print(f"Staged {name} at {page_path}")


def stage_quickstart() -> None:
    """Stage one quickstart."""
    stage_guide(
        validate.guide_name(os.environ.get("QUICKSTART_NAME")),
        validate.language(os.environ.get("LANGUAGE") or validate.DEFAULT_LANGUAGE),
    )


def stage_journey() -> None:
    """Stage one journey guide.

    Journeys go through the same staging path as quickstarts and are always English;
    SOURCE_PATH is validated because it is what selected this guide upstream.
    """
    name = validate.guide_name(os.environ.get("GUIDE_NAME"))
    print(f"Journey source: {validate.repo_path(os.environ.get('SOURCE_PATH'))}")
    stage_guide(name, validate.DEFAULT_LANGUAGE)


def sidebar_names(raw: str | None) -> list[str]:
    """Return the validated base names of the sidebar files to upload."""
    try:
        entries = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        print(f"::warning::SIDEBAR_FILES is not valid JSON: {exc}")
        return []

    names = []
    for entry in entries if isinstance(entries, list) else []:
        try:
            names.append(Path(validate.repo_path(entry)).name)
        except validate.ValidationError as exc:
            print(f"::warning::skipping sidebar file: {exc}")
    return names


def stage_sidebars() -> None:
    """Upload and publish the changed sidebar files from the artifact."""
    root = artifact_dir()
    client = aem.Client.from_env()

    staged = []
    for name in sidebar_names(os.environ.get("SIDEBAR_FILES")):
        path = within(root, "sidebar-files", name)
        if path is None or not path.is_file():
            print(f"::warning::sidebar file not in the artifact: {name}")
            continue
        staged.append(path)

    if not staged:
        print("No sidebar files to upload")
        return

    for level in SIDEBAR_LEVELS:
        client.ensure_asset_folder(f"/content/dam/{SIDEBAR_DAM_ROOT}/{level}")

    for path in staged:
        upload_dam_asset.upload(path, SIDEBAR_DAM_FOLDER)

    for path in staged:
        try:
            client.replicate(f"{SIDEBAR_DAM_PATH}/{path.name}", f"publish {path.name}")
        except aem.AemError as exc:
            print(f"::warning::publish failed for {path.name}: {exc}")


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
    except (validate.ValidationError, aem.AemError, upload_dam_asset.UploadError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Build the artifact the deploy workflow stages from.

Guide names and paths are validated here, where the work list is generated, as well
as on the deploy side. Duplicating the check is intentional: the deploy job
holds the write token and cannot trust anything this job produced, but catching a
bad name here turns a silently skipped guide into a visible warning.

Environment:
    GITHUB_REPOSITORY  owner/repo, used to build the image base URL
    PR_HEAD_SHA        head commit of the pull request
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import checks
from lib import gha, md, validate

CHANGES_FILE = Path("pr-changes.json")
RESULTS_FILE = Path("validation-results.json")
CONTENT_DIR = Path("pr")
IMAGES_DIR = Path("images")
SIDEBAR_DIR = Path("sidebar-files")

AEM_STAGING = Path(__file__).resolve().parent.parent / "aem-staging"
PARSE_MARKDOWN = AEM_STAGING / "parse_markdown.py"
PREPARE_PAYLOAD = AEM_STAGING / "prepare_aem_payload.py"

QUICKSTART_PREFIX = "site/sfguides/src/"
CF_ROOT = "/content/dam/snowflake-site"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff")

# Names that are safe to use as a file name in the artifact.
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _warn(message: str) -> None:
    print(f"::warning::{message}")


def load_changes() -> dict[str, Any]:
    """Return the state collect_pr_changes.py recorded."""
    if not CHANGES_FILE.is_file():
        return {}
    data = json.loads(CHANGES_FILE.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def markdown_for(name: str) -> Path | None:
    """Return the quickstart's markdown file on disk.

    Any folder holding more than one root markdown file fails a blocking check, so
    by the time this runs the choice is unambiguous.
    """
    return markdown_in(CONTENT_DIR / QUICKSTART_PREFIX / name, name)


def markdown_in(folder: Path, name: str) -> Path | None:
    """Return the markdown named after the folder, else the first one in it."""
    if not folder.is_dir():
        return None
    preferred = folder / f"{name}.md"
    if preferred.is_file():
        return preferred
    return next((path for path in sorted(folder.glob("*.md")) if path.is_file()), None)


def quickstart_names(changes: dict[str, Any]) -> list[str]:
    """Return the guides this pull request touched, in a stable order."""
    names = set()
    for prefixed in changes.get("changed_markdown", []):
        if not isinstance(prefixed, str):
            continue
        folder = checks.folder_of(checks.display(prefixed))
        if folder is None:
            continue
        try:
            names.add(validate.guide_name(folder))
        except validate.ValidationError as exc:
            _warn(f"skipping quickstart: {exc}")
    return sorted(names)


def language_of(md_path: Path | None) -> str:
    """Return the guide's declared language, defaulting when it cannot be read."""
    if md_path is None:
        return validate.DEFAULT_LANGUAGE
    try:
        return validate.language(checks.read_language(md.read(md_path)))
    except validate.ValidationError:
        return validate.DEFAULT_LANGUAGE


def _run(command: list[str], description: str) -> bool:
    result = subprocess.run(command, check=False)  # noqa: S603
    if result.returncode != 0:
        _warn(f"{description} failed with exit code {result.returncode}")
        return False
    return True


def parse_guide(
    name: str, md_path: Path, repo: str, head_sha: str, source_path: str
) -> Path | None:
    """Turn one guide's markdown into the JSON the deploy job uploads.

    parse_markdown.py points images at {base}/{folder}/assets/, so the base is the
    guide folder's parent at the head commit and the folder name is passed as the
    quickstart name. `name` only names the output file.
    """
    parsed = Path(f"parsed_content_{name}.json")
    parent_dir, folder = source_path.rsplit("/", 1)
    base_image_url = f"https://raw.githubusercontent.com/{repo}/{head_sha}/{parent_dir}"
    ok = _run(
        [
            sys.executable,
            str(PARSE_MARKDOWN),
            str(md_path),
            "--commit-sha",
            head_sha,
            "--quickstart-name",
            folder,
            "--base-image-url",
            base_image_url,
            "--output-json",
            str(parsed),
        ],
        f"parse of {name}",
    )
    return parsed if ok and parsed.is_file() else None


def prepare_payload(name: str, parsed: Path, lang: str, head_sha: str) -> None:
    """Turn parsed markdown into an AEM content fragment payload."""
    cf_path = f"{CF_ROOT}/{lang}/content-fragments/quickstarts/{name}-{head_sha}"
    _run(
        [
            sys.executable,
            str(PREPARE_PAYLOAD),
            str(parsed),
            "--content-fragment-path",
            cf_path,
            "--language",
            lang,
            "--output-json",
            f"aem_payload_{name}.json",
        ],
        f"payload preparation for {name}",
    )


def collect_images(name: str, source_path: str) -> int:
    """Copy a guide's downloaded images into the artifact under `name`."""
    assets = CONTENT_DIR / source_path / "assets"
    if not assets.is_dir():
        return 0

    destination = IMAGES_DIR / name
    copied = 0
    for entry in sorted(assets.iterdir()):
        if not entry.is_file() or entry.is_symlink():
            continue
        if entry.suffix.lower() not in IMAGE_SUFFIXES or not SAFE_NAME_RE.match(entry.name):
            continue
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry, destination / entry.name)
        copied += 1
    return copied


def collect_sidebars(changes: dict[str, Any]) -> int:
    """Copy the changed journey sidebar files into the artifact."""
    copied = 0
    for path in changes.get("sidebar_files", []):
        if not isinstance(path, str):
            continue
        source = CONTENT_DIR / path
        name = Path(path).name
        if not source.is_file() or source.is_symlink() or not SAFE_NAME_RE.match(name):
            continue
        SIDEBAR_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, SIDEBAR_DIR / name)
        copied += 1
        print(f"Collected sidebar file: {name}")
    return copied


def stage(changes: dict[str, Any], repo: str, head_sha: str) -> list[dict[str, str]]:
    """Parse, prepare and collect every touched guide."""
    staged = []
    for name in quickstart_names(changes):
        md_path = markdown_for(name)
        lang = language_of(md_path)
        staged.append({"name": name, "language": lang})

        if md_path is None:
            _warn(f"no markdown found for {name}; staging metadata only")
            continue

        print(f"Parsing {name} ({md_path}, language {lang})")
        source_path = f"{QUICKSTART_PREFIX}{name}"
        parsed = parse_guide(name, md_path, repo, head_sha, source_path)
        if parsed is not None:
            prepare_payload(name, parsed, lang, head_sha)
        print(f"  collected {collect_images(name, source_path)} image(s)")
    return staged


def stage_journeys(changes: dict[str, Any], repo: str, head_sha: str) -> None:
    """Build the preview payload for each changed journey topic.

    The deploy job looks for aem_payload_<topic folder>.json and, for now, stages
    journey topics in English only, so the payload is named and built to match.
    """
    for guide in changes.get("journey_guides", []):
        if not isinstance(guide, dict):
            continue
        try:
            name = validate.guide_name(guide.get("name"))
            source_path = validate.repo_path(guide.get("source_path"))
        except validate.ValidationError as exc:
            _warn(f"skipping journey topic: {exc}")
            continue

        md_path = markdown_in(CONTENT_DIR / source_path, name)
        if md_path is None:
            _warn(f"no markdown downloaded for journey topic {source_path}")
            continue

        print(f"Parsing journey topic {name} ({md_path})")
        parsed = parse_guide(name, md_path, repo, head_sha, source_path)
        if parsed is not None:
            prepare_payload(name, parsed, validate.DEFAULT_LANGUAGE, head_sha)
        print(f"  collected {collect_images(name, source_path)} image(s)")


def record(staged: list[dict[str, str]]) -> None:
    """Add the guide list to the results file the deploy workflow reads."""
    gha.set_json_output("quickstart_names_json", staged)
    if not RESULTS_FILE.is_file():
        _warn(f"{RESULTS_FILE} missing; deploy will find no guides to stage")
        return
    results = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    results["quickstart_names_json"] = staged
    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Recorded {len(staged)} quickstart(s) in {RESULTS_FILE}")


def main() -> int:
    """Build the staging artifact for everything this pull request touched."""
    changes = load_changes()
    if not changes.get("has_relevant_changes"):
        print("No relevant changes; nothing to stage")
        record([])
        return 0

    repo = validate.repo_full_name(os.environ.get("GITHUB_REPOSITORY"))
    head_sha = validate.sha40(os.environ.get("PR_HEAD_SHA"))

    staged = stage(changes, repo, head_sha)
    stage_journeys(changes, repo, head_sha)
    collect_sidebars(changes)
    record(staged)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except validate.ValidationError as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

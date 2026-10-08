#!/usr/bin/env python3
"""Work out what a pull request changed and fetch the content to validate.

Branch names and file paths here are contributor-chosen, so every path is checked
against lib.validate before use, each write is asserted to land inside `pr/`, and
content is fetched by git object name through the API. No contributor-chosen string
ever reaches a URL.

Environment:
    GITHUB_TOKEN       token used for the API calls
    GITHUB_REPOSITORY  owner/repo of the base repository
    PR_NUMBER          pull request to inspect
    PR_HEAD_SHA        head commit of the pull request
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lib import gh, gha, validate

CONTENT_DIR = Path("pr")
CHANGES_FILE = Path("pr-changes.json")

QUICKSTART_PREFIX = "site/sfguides/src/"
JOURNEY_PREFIX = "journeys/"
ASSETS_SEGMENT = "/assets/"
UNDERSCORE_MARKER = "/_"

# Matched case-sensitively, as the grep -E in detect-changed-files.sh was.
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico")


class CollectError(RuntimeError):
    """The pull request's changes could not be collected."""


def _warn(message: str) -> None:
    print(f"::warning::{message}")


@dataclass
class Changes:
    """Everything the later validate steps need to know about this pull request."""

    files: list[dict[str, Any]] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    downloaded_files: list[str] = field(default_factory=list)
    sidebar_files: list[str] = field(default_factory=list)
    journey_guides: list[dict[str, str]] = field(default_factory=list)
    has_quickstart_changes: bool = False

    @property
    def all_changed_files(self) -> list[str]:
        """Changed files, dropping assets that are not images."""
        return [
            path
            for path in self.changed_files
            if ASSETS_SEGMENT not in path or path.endswith(IMAGE_SUFFIXES)
        ]

    @property
    def changed_markdown(self) -> list[str]:
        """Changed markdown files, prefixed to point at the downloaded copies."""
        return [f"pr/{path}" for path in self.all_changed_files if path.endswith(".md")]

    @property
    def relevant(self) -> bool:
        return bool(self.has_quickstart_changes or self.sidebar_files or self.journey_guides)


def _is_quickstart(path: str) -> bool:
    return path.startswith(QUICKSTART_PREFIX) and UNDERSCORE_MARKER not in path


def _journey_guide(path: str) -> dict[str, str] | None:
    """Return the guide a journey markdown file belongs to, or None if unusable."""
    source_path = path.rsplit("/", 1)[0]
    if source_path == JOURNEY_PREFIX.rstrip("/"):
        _warn(f"skipping journey markdown outside a guide folder: {path}")
        return None
    try:
        return {
            "name": validate.guide_name(source_path.rsplit("/", 1)[-1]),
            "source_path": validate.repo_path(source_path),
        }
    except validate.ValidationError as exc:
        _warn(f"skipping journey guide: {exc}")
        return None


def classify(entries: list[dict[str, Any]]) -> Changes:
    """Group the pull request's files into the buckets each check needs."""
    changes = Changes(files=entries)
    guides: dict[str, str] = {}

    for entry in entries:
        path = entry.get("filename")
        if not isinstance(path, str):
            continue
        if _is_quickstart(path):
            changes.has_quickstart_changes = True
            if entry.get("status") != "removed":
                changes.changed_files.append(path)
        elif path.startswith(JOURNEY_PREFIX) and path.endswith(".json"):
            changes.sidebar_files.append(path)
        elif path.startswith(JOURNEY_PREFIX) and path.endswith(".md"):
            guide = _journey_guide(path)
            if guide is not None:
                guides[guide["source_path"]] = guide["name"]

    changes.journey_guides = [
        {"name": name, "source_path": source} for source, name in sorted(guides.items())
    ]
    return changes


def _target(path: str) -> Path:
    """Return where `path` may be written, refusing anything outside pr/."""
    validate.repo_path(path)
    root = CONTENT_DIR.resolve()
    resolved = (CONTENT_DIR / path).resolve()
    if not resolved.is_relative_to(root):
        msg = f"refusing to write outside {CONTENT_DIR}/: {path!r}"
        raise CollectError(msg)
    return resolved


def _save(client: gh.GitHub, repo: str, blob_sha: str, path: str) -> bool:
    """Fetch one blob into pr/, returning whether it landed."""
    try:
        target = _target(path)
        content = client.blob(repo, blob_sha)
    except (gh.GitHubError, validate.ValidationError, CollectError) as exc:
        _warn(f"skipping {path}: {exc}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return True


def download(client: gh.GitHub, repo: str, changes: Changes) -> None:
    """Fetch every changed quickstart file into pr/."""
    by_path = {
        entry["filename"]: entry.get("sha")
        for entry in changes.files
        if isinstance(entry.get("filename"), str)
    }
    for path in changes.changed_files:
        blob_sha = by_path.get(path)
        if not isinstance(blob_sha, str):
            _warn(f"no blob recorded for {path}")
            continue
        if _save(client, repo, blob_sha, path):
            changes.downloaded_files.append(path)
            print(f"Downloaded: {path}")


def _folder_markdown(client: gh.GitHub, repo: str, head_sha: str, folder: str) -> list[Any]:
    try:
        listing = client.get(f"/repos/{repo}/contents/{folder}", {"ref": head_sha})
    except gh.GitHubError as exc:
        _warn(f"could not list {folder}: {exc}")
        return []
    return listing if isinstance(listing, list) else []


def download_sibling_markdown(
    client: gh.GitHub, repo: str, head_sha: str, changes: Changes
) -> None:
    """Fetch the markdown already sitting in each touched folder.

    The single-markdown-per-folder check has to see files the pull request did not
    touch, otherwise adding a second guide to an existing folder would pass.
    """
    folders = {
        path[: len(QUICKSTART_PREFIX)] + path[len(QUICKSTART_PREFIX) :].split("/", 1)[0]
        for path in changes.changed_files
        if "/" in path[len(QUICKSTART_PREFIX) :]
    }
    already = set(changes.downloaded_files)

    for folder in sorted(folders):
        for item in _folder_markdown(client, repo, head_sha, folder):
            if not isinstance(item, dict) or item.get("type") != "file":
                continue
            name = item.get("name")
            if not isinstance(name, str) or not name.endswith(".md"):
                continue
            if name.lower() == "readme.md":
                continue
            path = f"{folder}/{name}"
            if path in already or not isinstance(item.get("sha"), str):
                continue
            if _save(client, repo, item["sha"], path):
                changes.downloaded_files.append(path)
                already.add(path)
                print(f"Downloaded sibling markdown: {path}")


def write_changes(changes: Changes, context: dict[str, Any]) -> None:
    """Record the collected state for run_validations.py and stage_payloads.py."""
    payload = {
        **context,
        "files": changes.files,
        "changed_files": changes.changed_files,
        "downloaded_files": changes.downloaded_files,
        "all_changed_files": changes.all_changed_files,
        "changed_markdown": changes.changed_markdown,
        "md_file_count": len(changes.changed_markdown),
        "sidebar_files": changes.sidebar_files,
        "journey_guides": changes.journey_guides,
        "has_relevant_changes": changes.relevant,
    }
    CHANGES_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def emit(changes: Changes) -> None:
    """Publish the step outputs the workflow branches on."""
    gha.set_output("has_relevant_changes", changes.relevant)
    gha.set_output("has_sidebar_changes", bool(changes.sidebar_files))
    gha.set_output("has_journey_guides", bool(changes.journey_guides))
    gha.set_output("md_file_count", len(changes.changed_markdown))
    gha.set_json_output("sidebar_json_files", changes.sidebar_files)
    gha.set_json_output("journey_guides_json", changes.journey_guides)
    gha.set_json_output("changed_markdown_json", changes.changed_markdown)
    gha.set_json_output("all_changed_files_json", changes.all_changed_files)

    print(f"relevant changes: {changes.relevant}")
    print(f"changed markdown: {len(changes.changed_markdown)}")
    print(f"downloaded files: {len(changes.downloaded_files)}")
    print(f"sidebar files:    {changes.sidebar_files}")
    print(f"journey guides:   {[guide['name'] for guide in changes.journey_guides]}")


def main() -> int:
    """Collect the changes, download what needs validating, and publish the state."""
    repo = validate.repo_full_name(os.environ.get("GITHUB_REPOSITORY"))
    number = validate.pr_number(os.environ.get("PR_NUMBER"))
    head_sha = validate.sha40(os.environ.get("PR_HEAD_SHA"))

    client = gh.GitHub(os.environ.get("GITHUB_TOKEN", ""))
    entries = client.paginate(f"/repos/{repo}/pulls/{number}/files", {"per_page": 100})
    changes = classify([entry for entry in entries if isinstance(entry, dict)])

    context = {"pr_number": number, "head_sha": head_sha, "repo": repo}
    if not changes.relevant:
        print("No changes in site/sfguides/src/ or journeys/, skipping")
        write_changes(changes, context)
        emit(changes)
        return 0

    download(client, repo, changes)
    download_sibling_markdown(client, repo, head_sha, changes)

    if changes.changed_files and not changes.downloaded_files:
        msg = "every download failed; refusing to validate an empty checkout"
        raise CollectError(msg)

    write_changes(changes, context)
    emit(changes)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (CollectError, gh.GitHubError, validate.ValidationError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

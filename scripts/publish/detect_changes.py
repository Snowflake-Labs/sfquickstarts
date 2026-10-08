#!/usr/bin/env python3
"""Work out what a push to master should publish.

`BEFORE_SHA` is forty zeros on the first push to a branch and after some force
pushes. Comparing against it returns an error rather than a file list, which would
publish nothing at all, so that case falls back to the pushed commit's own files.

Environment:
    GITHUB_TOKEN       token used for the API calls
    GITHUB_REPOSITORY  owner/repo being pushed to
    BEFORE_SHA         github.event.before
    AFTER_SHA          github.sha
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from lib import gh, gha, md, validate

QUICKSTART_ROOT = Path("site/sfguides/src")
QUICKSTART_PREFIX = "site/sfguides/src/"
JOURNEY_PREFIX = "journeys/"
UNDERSCORE_MARKER = "/_"

EMPTY_SHA = "0" * 40
MAX_COMPARE_PAGES = 20

# The compare endpoint's maximum. A short page means there is no page after it.
COMPARE_PAGE_SIZE = 100

# A push publishes a guide when its markdown or one of its images changed.
PUBLISHABLE_RE = re.compile(
    r"^site/sfguides/src/[^/]+/(?:[^/]+\.md|assets/[^/]+\.(?:jpg|jpeg|png|gif|svg|webp|bmp|ico))$"
)


def _warn(message: str) -> None:
    print(f"::warning::{message}")


def _files_of(payload: gh.Json) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    files = payload.get("files")
    return [item for item in files if isinstance(item, dict)] if isinstance(files, list) else []


def changed_files(client: gh.GitHub, repo: str, before: str, after: str) -> list[dict[str, Any]]:
    """Return the files a push touched.

    The compare endpoint caps `files` per page, so pages are followed explicitly;
    it returns an object rather than an array, which `paginate` cannot handle.
    """
    if before == EMPTY_SHA:
        _warn("github.event.before is empty; using the pushed commit's own file list")
        return _files_of(client.get(f"/repos/{repo}/commits/{after}"))

    collected: list[dict[str, Any]] = []
    for page in range(1, MAX_COMPARE_PAGES + 1):
        payload = client.get(
            f"/repos/{repo}/compare/{before}...{after}",
            {"per_page": COMPARE_PAGE_SIZE, "page": page},
        )
        batch = _files_of(payload)
        collected.extend(batch)
        if len(batch) < COMPARE_PAGE_SIZE:
            return collected
    _warn(f"compare exceeded {MAX_COMPARE_PAGES} pages; the file list may be truncated")
    return collected


def live_paths(entries: list[dict[str, Any]]) -> list[str]:
    """Return the paths a push added or modified, dropping deletions."""
    return [
        entry["filename"]
        for entry in entries
        if entry.get("status") != "removed" and isinstance(entry.get("filename"), str)
    ]


def markdown_for(name: str) -> Path | None:
    """Pick the markdown file that describes a guide.

    Preference order is inherited from the shell: the file named after the folder,
    then the first file that declares a language, then the first that is not a
    README, then simply the first.
    """
    folder = QUICKSTART_ROOT / name
    preferred = folder / f"{name}.md"
    if preferred.is_file():
        return preferred

    candidates = sorted(path for path in folder.glob("*.md") if path.is_file())
    if not candidates:
        return None
    with_language = next((p for p in candidates if md.language_tag(md.read(p))), None)
    non_readme = next((p for p in candidates if p.name.lower() != "readme.md"), None)
    return with_language or non_readme or candidates[0]


def language_of(path: Path | None) -> str:
    """Return a guide's language, defaulting when it is missing or unsupported."""
    if path is None:
        return validate.DEFAULT_LANGUAGE
    try:
        return validate.language(md.language_tag(md.read(path)))
    except validate.ValidationError:
        return validate.DEFAULT_LANGUAGE


def quickstarts(paths: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    """Return the publishable files and the guides they belong to."""
    publishable = [
        path for path in paths if UNDERSCORE_MARKER not in path and PUBLISHABLE_RE.match(path)
    ]

    names = set()
    for path in publishable:
        folder = path[len(QUICKSTART_PREFIX) :].split("/", 1)[0]
        try:
            names.add(validate.guide_name(folder))
        except validate.ValidationError as exc:
            _warn(f"skipping quickstart: {exc}")

    guides = [{"name": name, "language": language_of(markdown_for(name))} for name in sorted(names)]
    return publishable, guides


def journeys(paths: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    """Return the changed sidebar files and journey guides."""
    sidebars = [
        path for path in paths if path.startswith(JOURNEY_PREFIX) and path.endswith(".json")
    ]

    guides: dict[str, dict[str, str]] = {}
    for path in paths:
        if not path.startswith(JOURNEY_PREFIX) or not path.endswith(".md"):
            continue
        source = path.rsplit("/", 1)[0]
        if source == JOURNEY_PREFIX.rstrip("/"):
            _warn(f"skipping journey markdown outside a guide folder: {path}")
            continue
        try:
            guides[source] = {
                "name": validate.guide_name(source.rsplit("/", 1)[-1]),
                "language": language_of(Path(path) if Path(path).is_file() else None),
                "source_path": validate.repo_path(source),
            }
        except validate.ValidationError as exc:
            _warn(f"skipping journey guide: {exc}")

    return sidebars, [guides[key] for key in sorted(guides)]


def emit(
    publishable: list[str],
    guides: list[dict[str, str]],
    sidebars: list[str],
    journey_guides: list[dict[str, str]],
) -> None:
    """Publish the step outputs the publish jobs branch on."""
    relevant = bool(guides or sidebars or journey_guides)

    gha.set_output("has_relevant_changes", relevant)
    gha.set_output("has_sidebar_changes", bool(sidebars))
    gha.set_output("has_journey_guides", bool(journey_guides))
    gha.set_json_output("quickstart_names_json", guides)
    gha.set_json_output("relevant_changed_files_json", publishable)
    gha.set_json_output("sidebar_json_files", sidebars)
    gha.set_json_output("journey_guides_json", journey_guides)

    print(f"relevant changes: {relevant}")
    print(f"quickstarts:      {[guide['name'] for guide in guides]}")
    print(f"sidebar files:    {sidebars}")
    print(f"journey guides:   {[guide['name'] for guide in journey_guides]}")


def main() -> int:
    """Detect what this push changed and publish the result as step outputs."""
    repo = validate.repo_full_name(os.environ.get("GITHUB_REPOSITORY"))
    after = validate.sha40(os.environ.get("AFTER_SHA"))
    before = os.environ.get("BEFORE_SHA") or EMPTY_SHA
    if before != EMPTY_SHA:
        before = validate.sha40(before)

    client = gh.GitHub(os.environ.get("GITHUB_TOKEN", ""))
    paths = live_paths(changed_files(client, repo, before, after))

    publishable, guides = quickstarts(paths)
    sidebars, journey_guides = journeys(paths)
    emit(publishable, guides, sidebars, journey_guides)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (gh.GitHubError, validate.ValidationError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

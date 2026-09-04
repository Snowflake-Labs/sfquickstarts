#!/usr/bin/env python3
"""Derive the deploy context from the workflow_run event and the GitHub API.

The validate workflow runs against pull request code, so every file it uploads is
attacker-controlled. Nothing here takes an identifier from that artifact: the head
SHA comes from the event payload, the pull request number from an API lookup of
that SHA, and the work list from the pull request's own file list. The artifact is
consulted only for the language annotation and the validation verdict, neither of
which can introduce a name the API did not already return.

Environment:
    GITHUB_TOKEN        token used for the API lookups
    GITHUB_REPOSITORY   owner/repo of the base repository
    GITHUB_EVENT_PATH   path to the workflow_run event payload
    ARTIFACT_DIR        directory the validation artifact was downloaded into
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from lib import gh, gha, validate

QUICKSTART_PREFIX = "site/sfguides/src/"
JOURNEY_PREFIX = "journeys/"
IMAGE_ASSETS_SEGMENT = "/assets/"
RESULTS_FILENAME = "validation-results.json"

# journeys/<area>/<guide>/<file>: fewer separators than this and there is no
# guide folder to name, so the path is not a journey guide we can stage.
MIN_JOURNEY_DEPTH = 2


class ContextError(RuntimeError):
    """The deploy context could not be established."""


def _warn(message: str) -> None:
    print(f"::warning::{message}")


def load_event() -> dict[str, Any]:
    """Return the workflow_run event payload."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        msg = "GITHUB_EVENT_PATH is not set"
        raise ContextError(msg)
    data = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = "event payload is not a JSON object"
        raise ContextError(msg)
    return data


def read_head_sha(event: dict[str, Any]) -> str:
    """Return the head SHA of the triggering run, asserting it came from a PR."""
    run = event.get("workflow_run")
    if not isinstance(run, dict):
        msg = "event payload has no workflow_run object"
        raise ContextError(msg)
    if run.get("event") != "pull_request":
        msg = f"triggering run was not a pull_request: {run.get('event')!r}"
        raise ContextError(msg)
    return validate.sha40(run.get("head_sha"))


def find_pull_request(client: gh.GitHub, repo: str, head_sha: str) -> int | None:
    """Return the number of the single open PR whose head is `head_sha`.

    `workflow_run.pull_requests` is empty for forks, so the commit has to be looked
    up instead. A commit that heads no open PR, or heads more than one, yields None
    so the caller skips rather than guesses.
    """
    candidates = client.get(f"/repos/{repo}/commits/{head_sha}/pulls", {"per_page": 100})
    if not isinstance(candidates, list):
        msg = "commit pulls lookup did not return a list"
        raise ContextError(msg)

    matches = {
        validate.pr_number(entry["number"])
        for entry in candidates
        if isinstance(entry, dict)
        and entry.get("state") == "open"
        and isinstance(entry.get("head"), dict)
        and entry["head"].get("sha") == head_sha
    }
    if len(matches) != 1:
        _warn(f"expected exactly one open PR for {head_sha}, found {len(matches)}")
        return None
    return matches.pop()


def changed_paths(client: gh.GitHub, repo: str, number: int) -> list[str]:
    """Return every path touched by the pull request."""
    entries = client.paginate(f"/repos/{repo}/pulls/{number}/files", {"per_page": 100})
    return [
        entry["filename"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("filename"), str)
    ]


def _accept(path: str) -> str | None:
    """Return the path if it is a content path we are willing to act on.

    Paths outside the content directories are ordinary unrelated edits, so they are
    dropped quietly. Only a path that looks like content but fails the allowlist is
    worth surfacing.
    """
    if not path.startswith(validate.CONTENT_PREFIXES) or "/_" in path:
        return None
    try:
        return validate.repo_path(path)
    except validate.ValidationError as exc:
        _warn(f"skipping path: {exc}")
        return None


def _quickstart_name(path: str) -> str | None:
    remainder = path[len(QUICKSTART_PREFIX) :]
    if "/" not in remainder:
        return None
    try:
        return validate.guide_name(remainder.split("/", 1)[0])
    except validate.ValidationError as exc:
        _warn(f"skipping quickstart: {exc}")
        return None


def _journey_guide(path: str) -> dict[str, str] | None:
    if path.count("/") < MIN_JOURNEY_DEPTH:
        _warn(f"skipping journey guide at unexpected depth: {path}")
        return None
    source_path = path.rsplit("/", 1)[0]
    try:
        return {
            "name": validate.guide_name(source_path.rsplit("/", 1)[-1]),
            "source_path": validate.repo_path(source_path),
        }
    except validate.ValidationError as exc:
        _warn(f"skipping journey guide: {exc}")
        return None


def classify(paths: list[str]) -> dict[str, Any]:
    """Group the changed paths into the units of work the deploy jobs act on."""
    quickstarts: set[str] = set()
    sidebar_files: set[str] = set()
    journey_guides: dict[str, str] = {}
    markdown_count = 0

    for raw in paths:
        path = _accept(raw)
        if path is None:
            continue
        if path.startswith(QUICKSTART_PREFIX):
            name = _quickstart_name(path)
            if name is None:
                continue
            quickstarts.add(name)
            if path.endswith(".md") and IMAGE_ASSETS_SEGMENT not in path:
                markdown_count += 1
        elif path.startswith(JOURNEY_PREFIX) and path.endswith(".json"):
            sidebar_files.add(path)
        elif path.startswith(JOURNEY_PREFIX) and path.endswith(".md"):
            guide = _journey_guide(path)
            if guide is not None:
                journey_guides[guide["source_path"]] = guide["name"]

    return {
        "quickstarts": sorted(quickstarts),
        "sidebar_files": sorted(sidebar_files),
        "journey_guides": [
            {"name": name, "source_path": source} for source, name in sorted(journey_guides.items())
        ],
        "markdown_count": markdown_count,
    }


def _language_map(data: dict[str, Any]) -> dict[str, str]:
    languages: dict[str, str] = {}
    entries = data.get("quickstart_names_json")
    if not isinstance(entries, list):
        return languages
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            languages[validate.guide_name(entry.get("name"))] = validate.language(
                entry.get("language")
            )
        except validate.ValidationError:
            continue
    return languages


def _read_json(path: Path) -> gh.Json:
    """Return the parsed contents of `path`, or None if it cannot be read."""
    if not path.is_file():
        _warn(f"{path.name} missing from the artifact")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"{path.name} could not be read: {exc}")
        return None


def _load_results(artifact_dir: Path, head_sha: str) -> dict[str, Any] | None:
    """Return the artifact's results object, or None if it is unusable."""
    data = _read_json(artifact_dir / RESULTS_FILENAME)
    if not isinstance(data, dict):
        if data is not None:
            _warn(f"{RESULTS_FILENAME} is not a JSON object")
        return None
    if data.get("head_sha") != head_sha:
        _warn(f"{RESULTS_FILENAME} describes a different commit; discarding it")
        return None
    return data


def read_artifact(artifact_dir: Path, head_sha: str) -> tuple[bool, dict[str, str]]:
    """Return the validation verdict and language annotations from the artifact.

    Anything missing, malformed, or describing a different commit is discarded and
    reported as a failed verdict, so staging is skipped rather than run blind.
    """
    data = _load_results(artifact_dir, head_sha)
    if data is None:
        return False, {}
    return data.get("all_validations_passed") is True, _language_map(data)


def emit(
    number: int | None, head_sha: str, work: dict[str, Any], passed: bool, languages: dict[str, str]
) -> None:
    """Publish the resolved context as step outputs."""
    quickstarts = [
        {"name": name, "language": languages.get(name, validate.DEFAULT_LANGUAGE)}
        for name in work["quickstarts"]
    ]
    relevant = bool(quickstarts or work["sidebar_files"] or work["journey_guides"])

    gha.set_output("pr_number", number or 0)
    gha.set_output("head_sha", head_sha)
    gha.set_output("has_relevant_changes", relevant)
    gha.set_output("all_validations_passed", passed)
    gha.set_output("md_file_count", work["markdown_count"])
    gha.set_output("has_sidebar_changes", bool(work["sidebar_files"]))
    gha.set_output("has_journey_guides", bool(work["journey_guides"]))
    gha.set_json_output("quickstart_names_json", quickstarts)
    gha.set_json_output("sidebar_json_files", work["sidebar_files"])
    gha.set_json_output("journey_guides_json", work["journey_guides"])

    print(f"PR:                     {f'#{number}' if number else 'none (skipping)'}")
    print(f"head_sha:               {head_sha}")
    print(f"all_validations_passed: {passed}")
    print(f"quickstarts:            {[q['name'] for q in quickstarts]}")
    print(f"sidebar files:          {work['sidebar_files']}")
    print(f"journey guides:         {[g['name'] for g in work['journey_guides']]}")


def main() -> int:
    """Resolve the context, or emit an empty one so every deploy job skips."""
    empty: dict[str, Any] = {
        "quickstarts": [],
        "sidebar_files": [],
        "journey_guides": [],
        "markdown_count": 0,
    }

    repo = validate.repo_full_name(os.environ.get("GITHUB_REPOSITORY"))
    artifact_dir = Path(os.environ.get("ARTIFACT_DIR", "artifact"))
    head_sha = read_head_sha(load_event())

    client = gh.GitHub(os.environ.get("GITHUB_TOKEN", ""))
    number = find_pull_request(client, repo, head_sha)
    if number is None:
        emit(None, head_sha, empty, passed=False, languages={})
        return 0

    work = classify(changed_paths(client, repo, number))
    passed, languages = read_artifact(artifact_dir, head_sha)
    emit(number, head_sha, work, passed=passed, languages=languages)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ContextError, gh.GitHubError, validate.ValidationError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Report the staging deployment as a commit status on the pull request.

A workflow_run run produces no pull request check, so branch protection cannot see
whether staging deployed. This writes one status against the head commit, which can
then be required before merging.

The status is always written, including for pull requests that stage nothing: a
required check that never reports leaves the merge button disabled forever.

Usage:
    report_status.py {pending,report}

Environment:
    GITHUB_TOKEN        token with statuses: write
    GITHUB_REPOSITORY   owner/repo of the base repository
    HEAD_SHA            commit the status is attached to
    RUN_URL             run the status links to
    VALIDATIONS_PASSED  report only; the validate workflow's verdict
    STAGE_RESULTS       report only; the staging jobs' results, space separated
"""

from __future__ import annotations

import argparse
import os
import sys

from lib import gh, validate

# Also the name to require in branch protection. Changing it orphans the old status
# and silently unblocks every open pull request, so it is not a free rename.
CONTEXT = "AEM staging deploy"

# GitHub truncates a longer description in the merge box.
MAX_DESCRIPTION = 140

# A job that failed or was cancelled leaves the preview incomplete. A skipped one
# means there was nothing for it to do, which is not a failure.
BLOCKING_RESULTS = {
    "failure": "Staging deployment failed",
    "cancelled": "Staging deployment was cancelled",
}


def verdict() -> tuple[str, str]:
    """Return the state and description for a finished run."""
    if (os.environ.get("VALIDATIONS_PASSED") or "").strip() == "false":
        return "failure", "Validation failed; nothing was staged"

    results = (os.environ.get("STAGE_RESULTS") or "").split()
    for result, description in BLOCKING_RESULTS.items():
        if result in results:
            return "failure", description
    if "success" in results:
        return "success", "Staged to AEM"
    return "success", "No guide content to stage"


def payload(state: str, description: str) -> gh.Json:
    """Build the status body, linking back to the run when it is safe to."""
    body = {
        "state": state,
        "context": CONTEXT,
        "description": description[:MAX_DESCRIPTION],
    }
    url = (os.environ.get("RUN_URL") or "").strip()
    if url.startswith("https://"):
        body["target_url"] = url
    return body


def main() -> int:
    """Write the commit status the branch protection rule reads."""
    parser = argparse.ArgumentParser(description="Report the staging deployment status.")
    parser.add_argument("kind", choices=["pending", "report"])
    kind = parser.parse_args().kind

    if kind == "pending":
        state, description = "pending", "Staging deployment in progress"
    else:
        state, description = verdict()

    repo = validate.repo_full_name(os.environ.get("GITHUB_REPOSITORY"))
    head_sha = validate.sha40(os.environ.get("HEAD_SHA"))

    client = gh.GitHub(os.environ.get("GITHUB_TOKEN", ""))
    client.post(f"/repos/{repo}/statuses/{head_sha}", payload(state, description))
    print(f"{CONTEXT} on {head_sha}: {state} ({description})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (gh.GitHubError, validate.ValidationError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)

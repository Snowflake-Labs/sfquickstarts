#!/usr/bin/env python3
"""Fail the build when a workflow drifts back toward the shapes that caused injections.

These are structural rules, not taste. Each one removes a class of bug rather than an
instance of it, so they are checked mechanically instead of at review time:

  interpolation  `${{ }}` inside `run:` splices attacker-controlled text into a shell
                 before the shell ever sees it. Context has to arrive through `env:`.
  run-length     A `run:` block longer than three lines is logic, and logic in YAML is
                 untested and unlintable. It belongs in a script.
  pin            Removed. Which actions may run here is now enforced by the GitHub
                 enterprise actions allowlist, which cannot be bypassed by editing
                 this repository, and which permits only a mutable tag for some
                 actions (actions/download-artifact, actions/upload-artifact) --
                 making a SHA-only rule here unsatisfiable.
  permissions    A job holding an environment or a secret with no `permissions:` block
                 inherits the repository default, which is usually far too much.
  top-level      A workflow with no top-level `permissions:` grants every job the
                 default token scope by omission.

Usage:
    lint_workflows.py [workflow_dir]
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_DIR = Path(".github/workflows")
MAX_RUN_LINES = 3


@dataclass(frozen=True)
class Finding:
    """One rule violation, located precisely enough to fix without searching."""

    location: str
    rule: str
    message: str

    def render(self) -> str:
        """Return the one-line form printed to the log."""
        return f"{self.location}\n    [{self.rule}] {self.message}"


def code_lines(block: str) -> int:
    """Count the lines of a `run:` block that actually do something."""
    return sum(1 for line in block.splitlines() if line.strip())


def check_run(run: str, location: str) -> Iterator[Finding]:
    """Check one `run:` block for interpolation and for length."""
    if "${{" in run:
        yield Finding(
            location,
            "interpolation",
            "`${{ }}` inside run:. Pass the value through env: and read it in the script.",
        )
    lines = code_lines(run)
    if lines > MAX_RUN_LINES:
        yield Finding(
            location,
            "run-length",
            f"run: block is {lines} lines, over the {MAX_RUN_LINES} line limit. "
            "Move it into a script under scripts/.",
        )


def check_step(step: dict[str, Any], location: str) -> Iterator[Finding]:
    """Check one step's `run:` value."""
    run = step.get("run")
    if isinstance(run, str):
        yield from check_run(run, location)


def needs_permissions(job: dict[str, Any]) -> str | None:
    """Return why a job must declare `permissions:`, or None if it need not."""
    if "environment" in job:
        return "declares an environment"
    if "secrets." in yaml.safe_dump(job, default_flow_style=False):
        return "reads a secret"
    return None


def check_job(name: str, job: dict[str, Any], workflow: str) -> Iterator[Finding]:
    """Check one job and every step inside it."""
    location = f"{workflow}: job `{name}`"

    reason = needs_permissions(job)
    if reason is not None and "permissions" not in job:
        yield Finding(
            location,
            "permissions",
            f"job {reason} but has no explicit permissions: block, "
            "so it inherits the repository default.",
        )

    steps = job.get("steps")
    if not isinstance(steps, list):
        return
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        label = step.get("name") or step.get("uses") or "unnamed"
        yield from check_step(step, f"{location} > step {index + 1} `{label}`")


def lint_workflow(path: Path) -> list[Finding]:
    """Check one workflow file and return every violation it contains."""
    workflow = path.name
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [Finding(workflow, "parse", f"could not be parsed: {exc}")]

    if not isinstance(data, dict):
        return [Finding(workflow, "parse", "workflow is not a mapping")]

    findings: list[Finding] = []
    if "permissions" not in data:
        findings.append(
            Finding(
                workflow,
                "top-level",
                "no top-level permissions: block. Start from `permissions: {}` and let "
                "each job grant what it needs.",
            )
        )

    jobs = data.get("jobs")
    if isinstance(jobs, dict):
        for name, job in jobs.items():
            if isinstance(job, dict):
                findings.extend(check_job(str(name), job, workflow))
    return findings


def main() -> int:
    """Lint every workflow and return 1 if any rule was broken."""
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    paths = sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml"))
    if not paths:
        print(f"::error::no workflows found under {root}")
        return 1

    findings = [finding for path in paths for finding in lint_workflow(path)]
    for finding in findings:
        print(f"::error::{finding.location} [{finding.rule}] {finding.message}")
        print(finding.render())

    print(f"\nChecked {len(paths)} workflow(s); {len(findings)} violation(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

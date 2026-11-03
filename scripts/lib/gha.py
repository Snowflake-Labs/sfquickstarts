"""Write GitHub Actions step outputs safely.

The `echo "name=$value" >> $GITHUB_OUTPUT` idiom lets any newline inside a value
forge additional outputs, which is enough to flip a downstream `if:` condition.
Every write here uses a heredoc with a random delimiter instead, so a value can
only ever be a value.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, TypeAlias

from lib import validate

# Anything json.dumps can encode. Narrowing it would only push the same
# unavoidable cast out to every caller that builds an output structure.
Json: TypeAlias = Any


class OutputError(RuntimeError):
    """A value could not be written to a GitHub Actions file."""


def _render(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    msg = f"unsupported output value type: {type(value).__name__}"
    raise OutputError(msg)


def _append(file_var: str, name: str, value: object) -> None:
    validate.output_name(name)
    text = _render(value)

    destination = os.environ.get(file_var)
    if not destination:
        print(f"[{file_var} unset] {name}={text}", file=sys.stderr)
        return

    delimiter = f"gha{secrets.token_hex(16)}"
    if delimiter in text:
        msg = f"value for {name} collides with its heredoc delimiter"
        raise OutputError(msg)

    with Path(destination).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{delimiter}\n{text}\n{delimiter}\n")


def set_output(name: str, value: object) -> None:
    """Set a step output."""
    _append("GITHUB_OUTPUT", name, value)


def set_env(name: str, value: object) -> None:
    """Set an environment variable for later steps in the same job."""
    _append("GITHUB_ENV", name, value)


def set_json_output(name: str, value: Json) -> None:
    """Set a step output to the compact JSON encoding of `value`."""
    _append("GITHUB_OUTPUT", name, json.dumps(value, separators=(",", ":")))


def summary(text: str) -> None:
    """Append a line to the job summary, or to stdout when running outside Actions."""
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if not destination:
        print(text)
        return
    with Path(destination).open("a", encoding="utf-8") as handle:
        handle.write(f"{text}\n")

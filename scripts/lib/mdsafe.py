"""Render untrusted strings into markdown comment bodies.

Everything a comment displays - file names, offending words, validator messages -
is read out of an artifact produced by a run over pull request code, so all of it
is attacker-chosen. Rendering it verbatim would let a pull request inject links,
images, HTML, or `@team` mentions into a comment posted by the base repository.

Two defences here. Identifiers go through `code`, which puts them in a code span
where markdown is not parsed. Prose goes through `text`, which escapes the
markdown specials and defuses mentions. Both truncate, and `cap_body` bounds the
finished comment, so a large artifact cannot produce an unbounded API request.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from typing import Any

MAX_FIELD_CHARS = 200
MAX_ITEMS = 20
MAX_LIST = 500
# GitHub rejects comment bodies over 65536 characters.
MAX_BODY_CHARS = 60000

_WHITESPACE = re.compile(r"\s+")
_MD_SPECIAL = re.compile(r"[\\`*_\[\]()#+\-.!|~{}>]")
_PLACEHOLDER = "(empty)"


def _clean(value: object, limit: int) -> str:
    """Collapse to a single printable line, truncated to `limit`."""
    raw = value if isinstance(value, str) else str(value)
    raw = _WHITESPACE.sub(" ", raw).strip()
    raw = "".join(char for char in raw if char.isprintable())
    if not raw:
        return _PLACEHOLDER
    if len(raw) > limit:
        return raw[:limit] + "…"
    return raw


def code(value: object, limit: int = MAX_FIELD_CHARS) -> str:
    """Render a value as an inline code span, where markdown is not parsed."""
    return f"`{_clean(value, limit).replace('`', chr(39))}`"


def text(value: object, limit: int = MAX_FIELD_CHARS) -> str:
    """Render a value as prose, with markdown, HTML, and mentions defused."""
    raw = _clean(value, limit)
    raw = raw.replace("&", "&amp;").replace("<", "&lt;")
    raw = _MD_SPECIAL.sub(lambda match: "\\" + match.group(0), raw)
    return raw.replace("@", "&#64;")


def as_list(value: object) -> list[Any]:
    """Return `value` if it is a list, bounded so a huge artifact stays cheap."""
    if not isinstance(value, list):
        return []
    return value[:MAX_LIST]


def bullets(items: Sequence[Any], render: Callable[[Any], str], limit: int = MAX_ITEMS) -> str:
    """Render a bullet list, noting how many entries were withheld."""
    lines = [f"- {render(item)}" for item in items[:limit]]
    withheld = len(items) - limit
    if withheld > 0:
        lines.append(f"- _…and {withheld} more_")
    return "\n".join(lines)


def join_inline(values: Iterable[Any], limit: int = MAX_ITEMS) -> str:
    """Render values as a comma-separated run of code spans."""
    shown = list(values)[:limit]
    rendered = ", ".join(code(value) for value in shown)
    return rendered or _PLACEHOLDER


def cap_body(body: str, limit: int = MAX_BODY_CHARS) -> str:
    """Bound a finished comment body."""
    if len(body) <= limit:
        return body
    return body[:limit] + "\n\n_This comment was truncated._"

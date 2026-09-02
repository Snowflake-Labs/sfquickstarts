"""Read YAML frontmatter out of quickstart markdown.

Always `yaml.safe_load`: this parses pull request content, and a loader that can
construct arbitrary objects would be remote code execution on that job.

Two passes: a strict `---` delimited block first, then a loose scan of the opening
lines for a bare `key:` when the block is missing or unparseable. Almost every guide
in this repository uses the unfenced form, so the loose scan is the common path, not
the fallback its name suggests.

PyYAML is imported lazily. Callers that only need `language_tag` - the publish
workflow's change detection - stay standard-library only that way, which keeps the
credentialed jobs free of installed dependencies.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

FRONTMATTER_RE = re.compile(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)

# The language line is read from the opening lines only, as the sed pipeline did.
LANGUAGE_HEAD_LINES = 50
LANGUAGE_LINE_RE = re.compile(r"^\s*language\s*:\s*(.*)$", re.IGNORECASE)

# How far the loose scan looks before giving up.
HEAD_LINES = 120

# Real frontmatter is a few hundred bytes. The cap stops a pull request from
# handing the YAML parser a megabyte of nested aliases.
MAX_FRONTMATTER_CHARS = 64 * 1024

_QUOTED_RE = re.compile(r"""^(["'])(.*)\1$""", re.DOTALL)
_LIST_ITEM_RE = re.compile(r"^\s*-\s+")
_NEW_KEY_RE = re.compile(r"^\s*\w[\w\- ]*\s*:")
_BLANK_RE = re.compile(r"^\s*$")


def _key_re(key: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*{re.escape(key)}\s*:", re.IGNORECASE)


def strip_quotes(value: str) -> str:
    """Remove one layer of matching surrounding quotes."""
    trimmed = value.strip()
    match = _QUOTED_RE.match(trimmed)
    return match.group(2) if match else trimmed


def to_list(value: object) -> list[str]:
    """Coerce a frontmatter value to a list of strings.

    Mirrors the Node `toArray`: a YAML list is taken as-is, anything else is split
    on commas and newlines, so `categories: a, b` and a `-` list both work.
    """
    if value is None or value is False or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[,\n]", str(value)) if part.strip()]


def extract(text: str) -> tuple[dict[str, Any], str]:
    """Return the frontmatter mapping and the body below it.

    Yields an empty mapping when there is no `---` block or it does not parse,
    matching gray-matter, which returns empty data rather than raising.
    """
    stripped = text.lstrip("\ufeff")
    match = FRONTMATTER_RE.match(stripped)
    if not match:
        return {}, stripped

    block = match.group(1)
    body = stripped[match.end() :]
    if len(block) > MAX_FRONTMATTER_CHARS:
        return {}, body

    import yaml  # noqa: PLC0415

    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}, body
    return (data if isinstance(data, dict) else {}), body


def language_tag(text: str) -> str:
    """Return the declared language, or an empty string when none is present."""
    for line in text.split("\n")[:LANGUAGE_HEAD_LINES]:
        match = LANGUAGE_LINE_RE.match(line)
        if match:
            return strip_quotes(match.group(1))
    return ""


def head_value(text: str, key: str) -> str | None:
    """Return `key`'s scalar value from a loose scan of the opening lines.

    The Node validators fell back to this when the `---` block was absent, so a
    file with an unfenced `id:` at the top still produced a verdict.
    """
    pattern = _key_re(key)
    for line in text.lstrip("\ufeff").split("\n")[:HEAD_LINES]:
        if pattern.match(line):
            return strip_quotes(line.split(":", 1)[1])
    return None


def head_list(text: str, key: str) -> list[str]:
    """Return `key`'s list value from a loose scan of the opening lines.

    Handles both `key: a, b` on one line and a following block of `- item` lines,
    which is how categories are written in practice.
    """
    lines = text.lstrip("\ufeff").split("\n")[:HEAD_LINES]
    pattern = _key_re(key)
    index = next((i for i, line in enumerate(lines) if pattern.match(line)), -1)
    if index == -1:
        return []

    inline = lines[index].split(":", 1)[1].strip()
    if inline:
        return to_list(inline)

    items: list[str] = []
    for line in lines[index + 1 :]:
        if _LIST_ITEM_RE.match(line):
            items.append(_LIST_ITEM_RE.sub("", line).strip())
            continue
        if items and (_BLANK_RE.match(line) or _NEW_KEY_RE.match(line)):
            break
    return [item for item in items if item]


def read(path: Path) -> str:
    """Return a markdown file's text, tolerating undecodable bytes."""
    return path.read_text(encoding="utf-8", errors="replace")


def field(text: str, key: str) -> str | None:
    """Return a scalar frontmatter field, falling back to the loose head scan."""
    data, _ = extract(text)
    value = data.get(key)
    if isinstance(value, (str, int, float)) and str(value).strip():
        return str(value).strip()
    return head_value(text, key)


def field_list(text: str, key: str) -> list[str]:
    """Return a list frontmatter field, falling back to the loose head scan."""
    data, _ = extract(text)
    values = to_list(data.get(key))
    return values or head_list(text, key)

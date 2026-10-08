"""The individual content checks run against a pull request.

Each function takes the collected changes and returns a report payload, or None when
the check is satisfied.

Report shapes are a contract: scripts/deploy/post_comments.py reads these objects by
key to build the pull request comment, so field names here are load-bearing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib import md, validate

QUICKSTART_PREFIX = "site/sfguides/src/"
ASSETS_SEGMENT = "/assets/"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico")

LARGE_FILE_BYTES = 1_000_000

CATEGORY_RE = re.compile(r"^snowflake-site:taxonomy/[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*$")
SLUG_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Runs of letters, digits and apostrophes. [^\W_] is a word character that is not
# an underscore.
TOKEN_RE = re.compile(r"(?:[^\W_]|')+")

MULTIPLE_MD_MESSAGE = (
    "Each quickstart folder should contain only one markdown file in the root. "
    "Did you mean to add this additional .md file to the /assets folder?"
)
NON_MARKDOWN_ROOT_MESSAGE = (
    "Only markdown files (.md) are typically placed in the root of quickstart folders. "
    "Other file types should be placed in the /assets folder for better organization."
)
NON_IMAGE_ASSETS_MESSAGE = (
    "Non-image files found in /assets folders will **NOT** be uploaded to snowflake.com. "
    "If you are referencing them in your guide, you should link to them directly "
    "(e.g. [using permanent GitHub links](https://docs.github.com/en/repositories/"
    "working-with-files/using-files/getting-permanent-links-to-files))."
)
LANGUAGE_MESSAGE = (
    "Invalid or missing language detected. Allowed: en, es, it, fr, de, ja, ko, pt_br"
)
NON_MARKDOWN_ROOT_RE = re.compile(r"^site/sfguides/src/[^/]+/[^/]+$")


@dataclass
class Content:
    """The collected pull request state every check reads from."""

    changes: dict[str, Any]
    root: Path

    def _list(self, key: str) -> list[str]:
        value = self.changes.get(key)
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    @property
    def downloaded_files(self) -> list[str]:
        return self._list("downloaded_files")

    @property
    def all_changed_files(self) -> list[str]:
        return self._list("all_changed_files")

    @property
    def changed_markdown(self) -> list[str]:
        return self._list("changed_markdown")

    @property
    def entries(self) -> list[dict[str, Any]]:
        value = self.changes.get("files")
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    def path_for(self, prefixed: str) -> Path:
        """Return the on-disk location of a `pr/`-prefixed path."""
        return self.root / display(prefixed)

    def text(self, prefixed: str) -> str | None:
        """Return a downloaded file's text, or None when it is not on disk."""
        target = self.path_for(prefixed)
        if not target.is_file() or target.is_symlink():
            return None
        return md.read(target)


def display(path: str) -> str:
    """Strip the `pr/` working-copy prefix so reports name repository paths."""
    return path[3:] if path.startswith("pr/") else path


def folder_of(path: str) -> str | None:
    """Return the top-level quickstart folder a path sits in."""
    if not path.startswith(QUICKSTART_PREFIX):
        return None
    remainder = path[len(QUICKSTART_PREFIX) :]
    return remainder.split("/", 1)[0] if "/" in remainder else None


def check_multiple_markdown(content: Content) -> dict[str, Any] | None:
    """Fail when a quickstart folder holds more than one root markdown file."""
    folders = {
        folder
        for path in content.downloaded_files
        if path.endswith(".md") and ASSETS_SEGMENT not in path
        for folder in [folder_of(path)]
        if folder
    }

    errors = []
    for folder in sorted(folders):
        directory = content.root / QUICKSTART_PREFIX / folder
        if not directory.is_dir():
            continue
        found = sorted(
            f"{QUICKSTART_PREFIX}{folder}/{entry.name}"
            for entry in directory.iterdir()
            if entry.is_file() and entry.suffix == ".md"
        )
        if len(found) > 1:
            errors.append({"folder": folder, "files": found})

    if not errors:
        return None
    return {
        "type": "multiple_markdown_files",
        "message": MULTIPLE_MD_MESSAGE,
        "errors": errors,
    }


def check_non_markdown_root(content: Content) -> dict[str, Any] | None:
    """Note non-markdown files sitting in a quickstart's root folder."""
    files = [
        path
        for path in content.downloaded_files
        if NON_MARKDOWN_ROOT_RE.match(path) and not path.endswith(".md")
    ]
    if not files:
        return None
    return {"type": "non_markdown_root", "message": NON_MARKDOWN_ROOT_MESSAGE, "files": files}


def check_non_image_assets(content: Content) -> dict[str, Any] | None:
    """Note files in an assets folder that will never be uploaded."""
    files = [
        path
        for path in content.downloaded_files
        if ASSETS_SEGMENT in path and not path.endswith(IMAGE_SUFFIXES)
    ]
    if not files:
        return None
    return {"type": "non_image_assets", "message": NON_IMAGE_ASSETS_MESSAGE, "files": files}


def check_large_files(content: Content) -> dict[str, Any] | None:
    """Fail when a committed image is too large to serve."""
    oversized = []
    for path in content.all_changed_files:
        if ASSETS_SEGMENT not in path or not path.endswith(IMAGE_SUFFIXES):
            continue
        target = content.root / path
        if target.is_symlink() or not target.is_file():
            continue
        if target.stat().st_size > LARGE_FILE_BYTES:
            oversized.append(path)

    if not oversized:
        return None
    return {"type": "large_files", "files": oversized}


def check_language(content: Content) -> dict[str, Any] | None:
    """Fail when a guide declares no language, or one we do not publish."""
    invalid = []
    for prefixed in content.changed_markdown:
        text = content.text(prefixed)
        raw = read_language(text) if text is not None else ""
        try:
            validate.language(raw)
        except validate.ValidationError:
            invalid.append({"file": display(prefixed), "language": raw})

    if not invalid:
        return None
    return {"type": "language", "message": LANGUAGE_MESSAGE, "files": invalid}


def read_language(text: str) -> str:
    """Return the declared language, scanning only the opening lines as sed did."""
    return md.language_tag(text)


def check_categories(content: Content) -> dict[str, Any] | None:
    """Fail when a declared category is not a taxonomy path."""
    issues = []
    for prefixed in content.changed_markdown:
        text = content.text(prefixed)
        if text is None:
            continue
        categories = md.field_list(text, "categories")
        if not categories:
            continue
        bad = [item for item in categories if not CATEGORY_RE.match(item.strip().lower())]
        if bad:
            issues.append({"file": display(prefixed), "invalid": bad})

    return {"issues": issues} if issues else None


def _id_errors(guide_id: str | None, prefixed: str) -> list[str]:
    stem = Path(prefixed).stem
    folder = Path(prefixed).parent.name
    if not guide_id:
        return ["frontmatter id is missing"]

    errors = []
    if not SLUG_ID_RE.match(guide_id):
        errors.append("id must be slugified (lowercase letters/digits, single dashes)")
    if guide_id != stem:
        errors.append(f"id must match filename ('{stem}')")
    if guide_id != folder:
        errors.append(f"id must match folder name ('{folder}')")
    return errors


def check_frontmatter(content: Content) -> dict[str, Any] | None:
    """Fail when a guide's frontmatter id disagrees with its filename or folder."""
    issues = []
    for prefixed in content.changed_markdown:
        text = content.text(prefixed)
        if text is None:
            continue
        errors = _id_errors(md.field(text, "id"), prefixed)
        if errors:
            issues.append({"file": display(prefixed), "errors": errors})

    return {"issues": issues} if issues else None


def load_wordlist(path: Path) -> set[str]:
    """Return the vendored profanity words, ignoring comments and blanks."""
    if not path.is_file():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {line.strip().lower() for line in lines if line.strip() and not line.startswith("#")}


def parse_blocklist(*sources: str | None) -> set[str]:
    """Return the extra words configured on the repository."""
    words: set[str] = set()
    for source in sources:
        if not source:
            continue
        for part in re.split(r"\r?\n|,", source):
            entry = part.strip()
            if entry and not entry.startswith("#"):
                words.add(entry.lower())
    return words


def check_profanity(content: Content, words: set[str]) -> dict[str, Any] | None:
    """Fail when a guide contains a word from the blocklist."""
    if not words:
        return {"issues": [], "error": "Profanity wordlist unavailable."}

    issues = []
    for prefixed in content.changed_markdown:
        text = content.text(prefixed)
        if text is None:
            continue
        found = {token for token in TOKEN_RE.findall(text.lower()) if token in words}
        if found:
            issues.append({"file": display(prefixed), "words": sorted(found)})

    return {"issues": issues} if issues else None

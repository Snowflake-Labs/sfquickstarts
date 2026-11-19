"""The individual content checks run against a pull request.

Each function takes the collected changes and returns a report payload, or None when
the check is satisfied.

Report shapes are a contract: scripts/deploy/post_comments.py reads these objects by
key to build the pull request comment, so field names here are load-bearing.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib import dedupe, md, validate

QUICKSTART_PREFIX = "site/sfguides/src/"
JOURNEY_PREFIX = "journeys/"
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
# A quickstart folder ending in one of these is a translation, and must declare the
# language it is written in. Otherwise it publishes under /en/ beside the original.
LANGUAGE_SUFFIXES = {
    "es": "es",
    "it": "it",
    "fr": "fr",
    "de": "de",
    "ja": "ja",
    "ko": "ko",
    "kr": "ko",
    "ptbr": "pt_br",
}
# The publisher activates a page only when status is exactly "Published", so any
# other spelling silently leaves the guide unpublished.
STATUSES = ("Published", "Draft", "Hidden", "Archived")
# Above this estimated overlap two guides are the same content under two URLs, which
# splits search ranking between them. The gap in the corpus is wide: the closest
# unrelated same-language pair sits near 0.59, so the threshold is not marginal.
DUPLICATE_BLOCK = 0.80
# The repository as checked out beside the pull request's files: the base commit's
# guides, which the changed guides are compared against.
CORPUS_ROOT = Path()
# Pairs whose overlap is intended and has been reviewed. Keep this short: each entry
# is a standing exemption from a blocking check, so give every one a reason.
ALLOWED_DUPLICATES: dict[str, str] = {}
STATUS_FIXES = {"pubblicato": "Published", "pubblished": "Published", "public": "Published"}
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
    # Journey topic folders are short sidebar slugs, so their ids match the file only.
    if guide_id != folder and not display(prefixed).startswith(JOURNEY_PREFIX):
        errors.append(f"id must match folder name ('{folder}')")
    return errors


def _journey_errors(text: str) -> list[str]:
    """A journey topic must declare the sidebar it renders with."""
    errors = []
    if (md.field(text, "sidebar") or "").strip().lower() != "true":
        errors.append("journey topics must set 'sidebar: true'")
    sidebar_json = md.field(text, "sidebar_json")
    if not sidebar_json or not SLUG_ID_RE.match(sidebar_json):
        errors.append("journey topics must set 'sidebar_json' to their sidebar file's name")
    return errors


def _language_suffix_errors(text: str, prefixed: str) -> list[str]:
    """A translated quickstart's folder suffix must agree with its declared language."""
    if not display(prefixed).startswith(QUICKSTART_PREFIX):
        return []
    folder = Path(prefixed).parent.name
    suffix = folder.rsplit("-", 1)[-1] if "-" in folder else ""
    expected = LANGUAGE_SUFFIXES.get(suffix)
    if expected is None:
        return []
    declared = read_language(text).strip().lower()
    if declared == expected:
        return []
    return [
        f"folder ends in '-{suffix}', so language must be '{expected}' "
        f"(found '{declared or 'missing'}')"
    ]


def _status_errors(text: str) -> list[str]:
    """A declared status must be one the publisher recognises, spelled exactly."""
    status = md.field(text, "status")
    if status is None or status in STATUSES:
        return []
    if not status:
        return ["status is empty, so the guide will not publish (use 'Published' or remove it)"]
    key = status.strip().lower()
    hint = STATUS_FIXES.get(key) or next((s for s in STATUSES if s.lower() == key), None)
    allowed = ", ".join(STATUSES)
    fix = f"; did you mean '{hint}'?" if hint else ""
    return [f"status '{status}' is not recognised (allowed: {allowed}){fix}"]


def guide_markdown(content: Content) -> list[str]:
    """Return the changed markdown plus each touched quickstart's own guide file.

    A pull request that only changes an image still republishes the whole guide,
    so its markdown must be checked even though the pull request did not edit it.
    """
    seen = {display(path) for path in content.changed_markdown}
    paths = list(content.changed_markdown)
    for path in content.downloaded_files:
        name = display(path)
        if name in seen or not NON_MARKDOWN_ROOT_RE.match(name):
            continue
        if not name.endswith(".md") or Path(name).name.lower() == "readme.md":
            continue
        seen.add(name)
        paths.append(f"pr/{name}")
    return paths


def check_frontmatter(content: Content) -> dict[str, Any] | None:
    """Fail on a bad id, a translation filed as the wrong language, or an unknown status."""
    issues = []
    for prefixed in guide_markdown(content):
        text = content.text(prefixed)
        if text is None:
            continue
        errors = _id_errors(md.field(text, "id"), prefixed)
        errors += _language_suffix_errors(text, prefixed)
        errors += _status_errors(text)
        if display(prefixed).startswith(JOURNEY_PREFIX):
            errors += _journey_errors(text)
        if errors:
            issues.append({"file": display(prefixed), "errors": errors})

    return {"issues": issues} if issues else None


def corpus_markdown(root: Path) -> list[tuple[str, Path]]:
    """Return (name, path) for every guide and journey topic in the checked-out repo."""
    found = []
    quickstarts = root / QUICKSTART_PREFIX
    if quickstarts.is_dir():
        for folder in sorted(quickstarts.iterdir()):
            if not folder.is_dir() or folder.name.startswith("_"):
                continue
            markdown = folder / f"{folder.name}.md"
            if markdown.is_file():
                found.append((folder.name, markdown))

    journeys = root / JOURNEY_PREFIX
    if journeys.is_dir():
        for markdown in sorted(journeys.glob("*/*/*.md")):
            if markdown.name.lower() != "readme.md":
                found.append((f"{JOURNEY_PREFIX}{markdown.parent.name}", markdown))

    return found


def _guide_name(prefixed: str) -> str:
    """Return the comparison name for a changed path: its folder, or journeys/<topic>."""
    shown = display(prefixed)
    parent = Path(shown).parent
    return f"{JOURNEY_PREFIX}{parent.name}" if shown.startswith(JOURNEY_PREFIX) else parent.name


@dataclass
class Candidate:
    """A guide being checked, reduced to what the comparison needs."""

    name: str
    language: str
    file: str
    sketch: tuple[int, ...]


def _candidates(content: Content) -> list[Candidate]:
    found = []
    for prefixed in guide_markdown(content):
        text = content.text(prefixed)
        if text is None:
            continue
        fingerprint = dedupe.sketch(text)
        if not fingerprint:
            continue
        found.append(
            Candidate(
                name=_guide_name(prefixed),
                language=(read_language(text) or "en").strip().lower(),
                file=display(prefixed),
                sketch=fingerprint,
            )
        )
    return found


def check_duplicate_content(
    content: Content,
    root: Path | None = None,
    allowed: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Fail when a changed guide's body closely matches a guide already in the repository.

    Comparison is within a language, so a translation never matches its original, and a
    guide is never compared against itself.
    """
    candidates = _candidates(content)
    if not candidates:
        return None

    permitted = allowed if allowed is not None else ALLOWED_DUPLICATES
    changed = {candidate.name for candidate in candidates}
    corpus = [
        Candidate(name=name, language="", file=str(path), sketch=())
        for name, path in corpus_markdown(root if root is not None else CORPUS_ROOT)
        if name not in changed
    ]

    issues = []
    for candidate in candidates:
        # Other guides from this same pull request are compared too: two copies added
        # together are not in the base checkout and would otherwise miss each other.
        others = [other for other in candidates if other.name != candidate.name]
        matches = _duplicate_matches(candidate, others, permitted)
        matches += _corpus_matches(candidate, corpus, permitted)
        matches.sort(reverse=True)
        blocking = [match for match in matches if match[0] >= DUPLICATE_BLOCK * 100]
        if blocking:
            issues.append(
                {
                    "file": candidate.file,
                    "errors": [
                        f"body is {percent}% the same as '{other}'"
                        for percent, other in blocking[:3]
                    ],
                }
            )

    return {"issues": issues} if issues else None


def _permits(allowed: dict[str, str], left: str, right: str) -> bool:
    return bool(allowed.get(f"{min(left, right)}|{max(left, right)}"))


def _duplicate_matches(
    candidate: Candidate, others: list[Candidate], allowed: dict[str, str]
) -> list[tuple[int, str]]:
    matches = []
    for other in others:
        if other.language != candidate.language or _permits(allowed, candidate.name, other.name):
            continue
        score = dedupe.similarity(candidate.sketch, other.sketch)
        if score >= DUPLICATE_BLOCK:
            matches.append((round(score * 100), other.name))
    return matches


def _corpus_matches(
    candidate: Candidate, corpus: list[Candidate], allowed: dict[str, str]
) -> list[tuple[int, str]]:
    matches = []
    for other in corpus:
        if _permits(allowed, candidate.name, other.name):
            continue
        text = md.read(Path(other.file))
        if (read_language(text) or "en").strip().lower() != candidate.language:
            continue
        score = dedupe.similarity(candidate.sketch, dedupe.sketch(text))
        if score >= DUPLICATE_BLOCK:
            matches.append((round(score * 100), other.name))
    return matches


def check_sidebars(content: Content) -> dict[str, Any] | None:
    """Fail when a changed journey sidebar file is not valid JSON."""
    issues = []
    for path in content.all_changed_files:
        if not path.startswith(JOURNEY_PREFIX) or not path.endswith(".json"):
            continue
        target = content.root / path
        if target.is_symlink() or not target.is_file():
            continue
        try:
            json.loads(target.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            issues.append({"file": path, "errors": [str(exc)]})

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

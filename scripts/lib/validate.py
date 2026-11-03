"""The single allowlist for untrusted identifiers.

Every value that originates outside the repository - from a pull request, from an
uploaded artifact, or from an API response about either - passes through here before
it reaches a path, a URL, or a shell. Each function returns the validated value or
raises; none of them substitute a default, because a rejected value must stop the
caller rather than quietly become something else.
"""

from __future__ import annotations

import re

# Guide folder names are lowercase slugs. The length cap is deliberately generous:
# the upstream repository has names up to 109 characters.
GUIDE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
PATH_CHARS_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
REPO_FULL_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
OUTPUT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

LANGUAGES = frozenset({"en", "es", "it", "fr", "de", "ja", "ko", "pt_br"})
DEFAULT_LANGUAGE = "en"

CONTENT_PREFIXES = ("site/sfguides/src/", "journeys/")

# GitHub caps issue and PR numbers well below this; it exists to bound the value,
# not to model a real limit.
MAX_PR_NUMBER = 10_000_000


class ValidationError(ValueError):
    """An untrusted value failed its allowlist."""


def guide_name(value: object) -> str:
    """Return a quickstart or journey guide folder name."""
    if not isinstance(value, str):
        msg = f"guide name must be a string, got {type(value).__name__}"
        raise ValidationError(msg)
    if ".." in value:
        msg = f"guide name contains a parent-directory reference: {value!r}"
        raise ValidationError(msg)
    if not GUIDE_NAME_RE.fullmatch(value):
        msg = f"guide name is not an allowed slug: {value!r}"
        raise ValidationError(msg)
    return value


def language(value: object) -> str:
    """Return a supported content language tag."""
    if not isinstance(value, str):
        msg = f"language must be a string, got {type(value).__name__}"
        raise ValidationError(msg)
    normalized = value.strip().lower()
    if normalized not in LANGUAGES:
        msg = f"language is not supported: {value!r}"
        raise ValidationError(msg)
    return normalized


def repo_path(value: object) -> str:
    """Return a repository-relative path inside the content directories."""
    if not isinstance(value, str):
        msg = f"path must be a string, got {type(value).__name__}"
        raise ValidationError(msg)
    if not value.startswith(CONTENT_PREFIXES):
        msg = f"path is outside the content directories: {value!r}"
        raise ValidationError(msg)
    if not PATH_CHARS_RE.fullmatch(value):
        msg = f"path contains disallowed characters: {value!r}"
        raise ValidationError(msg)
    segments = value.split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        msg = f"path has an empty or relative segment: {value!r}"
        raise ValidationError(msg)
    return value


def sha40(value: object) -> str:
    """Return a full 40-character git object name."""
    if not isinstance(value, str):
        msg = f"sha must be a string, got {type(value).__name__}"
        raise ValidationError(msg)
    if not SHA40_RE.fullmatch(value):
        msg = f"sha is not 40 lowercase hex characters: {value!r}"
        raise ValidationError(msg)
    return value


def pr_number(value: object) -> int:
    """Return a pull request number."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        msg = f"pr number must be an int or string, got {type(value).__name__}"
        raise ValidationError(msg)
    try:
        number = int(value)
    except ValueError as exc:
        msg = f"pr number is not an integer: {value!r}"
        raise ValidationError(msg) from exc
    if not 0 < number <= MAX_PR_NUMBER:
        msg = f"pr number is out of range: {number}"
        raise ValidationError(msg)
    return number


def repo_full_name(value: object) -> str:
    """Return an owner/repo slug."""
    if not isinstance(value, str):
        msg = f"repository must be a string, got {type(value).__name__}"
        raise ValidationError(msg)
    if ".." in value or not REPO_FULL_NAME_RE.fullmatch(value):
        msg = f"repository is not a valid owner/name slug: {value!r}"
        raise ValidationError(msg)
    return value


def output_name(value: object) -> str:
    """Return a GitHub Actions output or environment variable name."""
    if not isinstance(value, str) or not OUTPUT_NAME_RE.fullmatch(value):
        msg = f"output name is not a valid identifier: {value!r}"
        raise ValidationError(msg)
    return value

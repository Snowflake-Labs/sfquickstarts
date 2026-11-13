"""Near-duplicate detection for guide content.

Two guides holding the same body compete for the same searches, and only one of them
can rank. This module reduces a guide to a small sketch of its wording so a changed
guide can be compared against every other guide cheaply.

A sketch is the `SKETCH_SIZE` smallest hashes of the guide's overlapping word runs (a
"bottom-k" sketch). The fraction of the combined bottom-k that both sketches hold
estimates how much of their wording is shared, within about three points of an exact
comparison on this corpus. Sketching all ~840 guides takes under two seconds, so no
precomputed index has to be stored or kept up to date.
"""

from __future__ import annotations

import hashlib
import re

SHINGLE_WORDS = 10
SKETCH_SIZE = 256

# Keep letters, digits and spaces; punctuation and markdown syntax should not change
# the verdict.
_NOISE_RE = re.compile(r"[^a-z0-9 ]+")
_BODY_RE = re.compile(r"^#\s", re.MULTILINE)


def body_text(text: str) -> str:
    """Return a guide's prose from its first heading on, normalised for comparison.

    Frontmatter is dropped: it carries the id, title and categories, which differ
    between two copies of the same content and would hide the duplication.
    """
    match = _BODY_RE.search(text)
    start = match.start() if match else 0
    return " ".join(_NOISE_RE.sub(" ", text[start:].lower()).split())


def sketch(text: str) -> tuple[int, ...]:
    """Return a guide's sketch, or an empty tuple when it is too short to compare."""
    words = body_text(text).split()
    if len(words) < SHINGLE_WORDS:
        return ()
    hashes = {
        int.from_bytes(
            hashlib.blake2b(
                " ".join(words[index : index + SHINGLE_WORDS]).encode(), digest_size=8
            ).digest(),
            "big",
        )
        for index in range(len(words) - SHINGLE_WORDS + 1)
    }
    return tuple(sorted(hashes)[:SKETCH_SIZE])


def similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    """Return the estimated share of wording the two sketches have in common."""
    if not left or not right:
        return 0.0
    first, second = set(left), set(right)
    combined = sorted(first | second)[:SKETCH_SIZE]
    shared = sum(1 for value in combined if value in first and value in second)
    return shared / len(combined)

"""Detect renames of top-level guide folders.

Renaming a guide folder changes its published URL, so it is blocked. The allowances
below exist because several innocent edits look like a rename in a diff.

Git only reports a rename when it recognises one, so there are two passes: explicit
`renamed` entries, and folders whose files were removed while a similar set appeared
elsewhere. The second pass is a heuristic, which is why the allowances below matter
more than they look.
"""

from __future__ import annotations

from typing import Any

from checks import QUICKSTART_PREFIX, folder_of

# Share of a folder's removed files that must reappear elsewhere before the pair is
# treated as a rename rather than two unrelated edits.
MATCH_PERCENT = 50

RENAME_MESSAGE = "Renaming guide URLs is not currently supported. Please revert the name change."

Rename = tuple[str, str]


def _paths(entries: list[dict[str, Any]], status: str) -> list[str]:
    return [
        entry["filename"]
        for entry in entries
        if entry.get("status") == status and isinstance(entry.get("filename"), str)
    ]


def _grouped(paths: list[str]) -> dict[str, set[str]]:
    """Map each top-level folder to the folder-relative paths seen under it."""
    groups: dict[str, set[str]] = {}
    for path in paths:
        # Underscore folders are staging areas; the shell pass skipped them here.
        if path.startswith(f"{QUICKSTART_PREFIX}_"):
            continue
        folder = folder_of(path)
        if folder is None:
            continue
        relative = path[len(QUICKSTART_PREFIX) + len(folder) + 1 :]
        groups.setdefault(folder, set()).add(relative)
    return groups


def explicit(entries: list[dict[str, Any]]) -> list[Rename]:
    """Renames git reported outright."""
    found = []
    for entry in entries:
        if entry.get("status") != "renamed":
            continue
        old, new = entry.get("previous_filename"), entry.get("filename")
        if not isinstance(old, str) or not isinstance(new, str) or old == new:
            continue
        old_folder, new_folder = folder_of(old), folder_of(new)
        if old_folder and new_folder and old_folder != new_folder:
            found.append((old_folder, new_folder))
    return found


def inferred(entries: list[dict[str, Any]]) -> list[Rename]:
    """Renames implied by a folder's files disappearing and reappearing."""
    removed = _grouped(_paths(entries, "removed"))
    added = _grouped(_paths(entries, "added"))

    found = []
    for old_folder, old_files in sorted(removed.items()):
        if not old_files:
            continue
        for new_folder, new_files in sorted(added.items()):
            matched = len(old_files & new_files)
            if matched and matched * 100 // len(old_files) >= MATCH_PERCENT:
                found.append((old_folder, new_folder))
    return found


def _active_folders(entries: list[dict[str, Any]]) -> set[str]:
    """Folders that still gain or keep content in this pull request."""
    folders = set()
    for entry in entries:
        if entry.get("status") not in ("added", "modified"):
            continue
        folder = folder_of(entry.get("filename", ""))
        if folder:
            folders.add(folder)
    return folders


def _allowed(pair: Rename, all_renames: set[Rename], active: set[str]) -> bool:
    """Whether a detected rename is one of the shapes we deliberately permit."""
    old_folder, new_folder = pair
    if (new_folder, old_folder) in all_renames:
        print(f"Round-trip rename detected (allowed): {old_folder} <-> {new_folder}")
        return True
    if old_folder.startswith("_"):
        print(f"Underscore folder rename (allowed): {old_folder} -> {new_folder}")
        return True
    if old_folder in active:
        print(f"Source folder '{old_folder}' still has active files; not a rename")
        return True
    return False


def check(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return a report of blocked folder renames, or None when there are none."""
    ordered = list(dict.fromkeys(explicit(entries) + inferred(entries)))
    if not ordered:
        print("No folder renames detected")
        return None

    print(f"Detected {len(ordered)} unique folder rename(s):")
    for old_folder, new_folder in ordered:
        print(f"  {old_folder} -> {new_folder}")

    all_renames = set(ordered)
    active = _active_folders(entries)
    blocked = [
        {
            "old_folder": old_folder,
            "new_folder": new_folder,
            "example_file": (
                f"{QUICKSTART_PREFIX}{old_folder}/... -> {QUICKSTART_PREFIX}{new_folder}/..."
            ),
        }
        for old_folder, new_folder in ordered
        if not _allowed((old_folder, new_folder), all_renames, active)
    ]

    if not blocked:
        return None
    return {"type": "folder_rename", "message": RENAME_MESSAGE, "renames": blocked}

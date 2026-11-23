"""Tests for the frontmatter check's language-suffix and status rules.

Run from the repository root with: python -m unittest discover -s scripts/validate/tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SCRIPTS), str(SCRIPTS / "validate")]

import checks  # noqa: E402

SRC = "site/sfguides/src"


def guide(folder: str, language: str = "en", status: str = "Published") -> str:
    lines = ["---", f"id: {folder}", f"language: {language}"]
    if status:
        lines.append(f"status: {status}")
    return "\n".join([*lines, "---", "# Title", ""])


class FrontmatterTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, path: str, text: str = "") -> str:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return path

    def errors(self, changed: list[str], downloaded: list[str]) -> list[str]:
        changes = {
            "changed_markdown": [f"pr/{p}" for p in changed if p.endswith(".md")],
            "downloaded_files": downloaded,
        }
        report = checks.check_frontmatter(checks.Content(changes, self.root))
        return [e for issue in (report or {}).get("issues", []) for e in issue["errors"]]

    def guide_file(self, folder: str, **fields: str) -> str:
        return self.write(f"{SRC}/{folder}/{folder}.md", guide(folder, **fields))

    def test_image_only_change_still_checks_wrong_language(self) -> None:
        md = self.guide_file("intro-it", language="en")
        image = self.write(f"{SRC}/intro-it/assets/image.png")
        errors = self.errors(changed=[image], downloaded=[image, md])
        self.assertTrue(any("language must be 'it'" in e for e in errors), errors)

    def test_image_only_change_still_checks_status(self) -> None:
        md = self.guide_file("intro", status="Pubblicato")
        image = self.write(f"{SRC}/intro/assets/image.png")
        errors = self.errors(changed=[image], downloaded=[image, md])
        self.assertTrue(any("did you mean 'Published'" in e for e in errors), errors)

    def test_correct_translation_passes(self) -> None:
        md = self.guide_file("intro-kr", language="ko")
        self.assertEqual(self.errors(changed=[md], downloaded=[md]), [])

    def test_kr_folder_requires_ko(self) -> None:
        md = self.guide_file("intro-kr", language="kr")
        self.assertTrue(self.errors(changed=[md], downloaded=[md]))

    def test_english_folder_without_suffix_passes(self) -> None:
        md = self.guide_file("ship-commit")
        self.assertEqual(self.errors(changed=[md], downloaded=[md]), [])

    def test_lowercase_status_fails(self) -> None:
        md = self.guide_file("intro", status="published")
        self.assertTrue(self.errors(changed=[md], downloaded=[md]))

    def test_missing_status_is_unchanged(self) -> None:
        md = self.guide_file("intro", status="")
        self.assertEqual(self.errors(changed=[md], downloaded=[md]), [])

    def test_readme_and_assets_markdown_are_ignored(self) -> None:
        readme = self.write(f"{SRC}/intro-it/README.md", "language: en\n")
        notes = self.write(f"{SRC}/intro-it/assets/notes.md", "language: en\n")
        image = self.write(f"{SRC}/intro-it/assets/image.png")
        self.assertEqual(self.errors(changed=[image], downloaded=[image, readme, notes]), [])


if __name__ == "__main__":
    unittest.main()

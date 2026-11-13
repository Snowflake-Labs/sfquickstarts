"""Tests for the duplicate-content check and its sketching.

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
from lib import dedupe  # noqa: E402

SRC = "site/sfguides/src"
LOREM = (
    "load the sample orders table into a stage and then query it with a warehouse "
    "so that the totals per region can be charted for the finance team each month "
)
OTHER = (
    "train a forecasting model on the sensor readings and register it in the model "
    "registry before serving predictions to the maintenance dashboard every hour "
)


def guide(folder: str, body: str, language: str = "en", repeats: int = 12) -> str:
    head = ["---", f"id: {folder}", f"language: {language}", "status: Published", "---"]
    return "\n".join([*head, "# Title", "", body * repeats, ""])


class SketchTest(unittest.TestCase):
    def test_identical_bodies_match(self) -> None:
        self.assertEqual(
            dedupe.similarity(dedupe.sketch(guide("a", LOREM)), dedupe.sketch(guide("b", LOREM))),
            1.0,
        )

    def test_frontmatter_differences_are_ignored(self) -> None:
        left = dedupe.sketch(guide("one-name", LOREM))
        right = dedupe.sketch(guide("a-totally-different-id", LOREM, language="de"))
        self.assertEqual(dedupe.similarity(left, right), 1.0)

    def test_unrelated_bodies_do_not_match(self) -> None:
        left = dedupe.sketch(guide("a", LOREM))
        right = dedupe.sketch(guide("b", OTHER))
        self.assertLess(dedupe.similarity(left, right), 0.2)

    def test_short_guide_has_no_sketch(self) -> None:
        self.assertEqual(dedupe.sketch("---\nid: a\n---\n# T\n\ntoo short\n"), ())

    def test_empty_sketch_scores_zero(self) -> None:
        self.assertEqual(dedupe.similarity(dedupe.sketch(guide("a", LOREM)), ()), 0.0)


class DuplicateContentTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.corpus = self.root / "base"
        self.pr = self.root / "pr"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add_existing(self, folder: str, body: str, language: str = "en") -> None:
        """Write a guide into the simulated base checkout."""
        target = self.corpus / SRC / folder / f"{folder}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(guide(folder, body, language), encoding="utf-8")

    def add_journey(self, topic: str, body: str) -> None:
        target = self.corpus / "journeys" / "waf" / topic / f"{topic}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(guide(topic, body), encoding="utf-8")

    def add_changed(self, folder: str, body: str, language: str = "en") -> str:
        path = f"{SRC}/{folder}/{folder}.md"
        target = self.pr / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(guide(folder, body, language), encoding="utf-8")
        return path

    def errors(self, paths: list[str]) -> list[str]:
        changes = {
            "changed_markdown": [f"pr/{p}" for p in paths],
            "downloaded_files": list(paths),
        }
        content = checks.Content(changes, self.pr)
        report = checks.check_duplicate_content(content, self.corpus)
        return [e for issue in (report or {}).get("issues", []) for e in issue["errors"]]

    def test_blocks_a_copy_of_an_existing_guide(self) -> None:
        self.add_existing("existing-guide", LOREM)
        path = self.add_changed("new-guide", LOREM)
        self.assertTrue(any("existing-guide" in e for e in self.errors([path])))

    def test_blocks_a_copy_of_a_journey_topic(self) -> None:
        self.add_journey("performance", LOREM)
        path = self.add_changed("framework-performance", LOREM)
        self.assertTrue(any("journeys/performance" in e for e in self.errors([path])))

    def test_allows_an_unrelated_guide(self) -> None:
        self.add_existing("existing-guide", LOREM)
        path = self.add_changed("new-guide", OTHER)
        self.assertEqual(self.errors([path]), [])

    def test_editing_a_guide_does_not_match_itself(self) -> None:
        self.add_existing("same-guide", LOREM)
        path = self.add_changed("same-guide", LOREM)
        self.assertEqual(self.errors([path]), [])

    def test_translations_do_not_match_their_original(self) -> None:
        self.add_existing("guide", LOREM)
        path = self.add_changed("guide-it", LOREM, language="it")
        self.assertEqual(self.errors([path]), [])

    def test_two_copies_in_the_same_pull_request_match_each_other(self) -> None:
        first = self.add_changed("guide-one", LOREM)
        second = self.add_changed("guide-two", LOREM)
        self.assertEqual(len(self.errors([first, second])), 2)

    def test_allowlisted_pair_is_not_blocked(self) -> None:
        self.add_existing("existing-guide", LOREM)
        path = self.add_changed("new-guide", LOREM)
        changes = {"changed_markdown": [f"pr/{path}"], "downloaded_files": [path]}
        content = checks.Content(changes, self.pr)
        allowed = {"existing-guide|new-guide": "reviewed: intentionally parallel"}
        self.assertIsNone(checks.check_duplicate_content(content, self.corpus, allowed))

    def test_missing_corpus_is_not_an_error(self) -> None:
        path = self.add_changed("new-guide", LOREM)
        changes = {"changed_markdown": [f"pr/{path}"], "downloaded_files": [path]}
        content = checks.Content(changes, self.pr)
        absent = self.root / "nowhere"
        self.assertIsNone(checks.check_duplicate_content(content, absent))


if __name__ == "__main__":
    unittest.main()

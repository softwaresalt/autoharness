"""217.002-T: the release.yml changelog extraction yields every 1.6.0 entry."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.6.0"
REQUIRED_ENTRIES = (
    "211-F / 218-S",
    "208-F / 215-S",
    "209-F / 216-S",
    "205-F / 212-S",
    "206-F / 213-S",
    "207-F / 214-S",
    "212-F / 219-S",
    "213-F / 220-S",
    "214-F / 221-S",
    "215-F / 222-S",
    "216-F / 223-S",
)


def extract_release_notes(changelog: str, version: str) -> str:
    """Mirror the awk program in .github/workflows/release.yml."""
    heading = re.compile(r"^##[ \t\r\n\f\v]+\[?" + re.escape(version) + r"\]?([ \t\r\n\f\v]|$|-)")
    found = False
    body: list[str] = []
    for line in changelog.splitlines():
        if line.startswith("## "):
            if found:
                break
            if heading.match(line):
                found = True
            continue
        if found:
            body.append(line)
    return "\n".join(body) + "\n" if body else ""


class ReleaseChangelogExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        cls.notes = extract_release_notes(cls.changelog, VERSION)

    def test_release_workflow_still_uses_the_mirrored_extraction(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn('/^## / {', workflow)
        self.assertIn('ver_re "\\\\]?([[:space:]]|$|-)")', workflow)

    def test_extracted_body_is_non_empty(self) -> None:
        self.assertTrue(self.notes.strip())

    def test_extracted_body_contains_every_entry(self) -> None:
        for entry in REQUIRED_ENTRIES:
            self.assertIn(entry, self.notes, entry)

    def test_no_unreleased_heading_with_content(self) -> None:
        self.assertEqual(extract_release_notes(self.changelog, "Unreleased").strip(), "")

    def test_extraction_stops_at_previous_release(self) -> None:
        self.assertNotIn("## 1.5.0", self.notes)
        self.assertNotIn("1.5.0 - 2026-08-30", self.notes)


if __name__ == "__main__":
    unittest.main()

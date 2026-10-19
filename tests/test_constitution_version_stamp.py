"""The foundation AGENTS template must cite the current constitution version."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_VERSION = re.compile(r"\*\*Version\*\*: (\d+\.\d+\.\d+)")
_STAMP = re.compile(r"Constitution version: (\d+\.\d+\.\d+)")


def _read(relative: str) -> str:
    return (_ROOT / relative).read_text(encoding="utf-8")


class ConstitutionVersionStampTests(unittest.TestCase):
    def test_agents_template_stamp_matches_constitution_template_and_mirror(self) -> None:
        template_version = _VERSION.search(_read("templates/foundation/constitution.instructions.md.tmpl"))
        mirror_version = _VERSION.search(_read(".github/instructions/constitution.instructions.md"))
        stamp = _STAMP.search(_read("templates/foundation/AGENTS.md.tmpl"))
        self.assertIsNotNone(template_version)
        self.assertIsNotNone(mirror_version)
        self.assertIsNotNone(stamp)
        self.assertEqual(template_version.group(1), mirror_version.group(1))
        self.assertEqual(stamp.group(1), template_version.group(1))


if __name__ == "__main__":
    unittest.main()

"""Contract tests for 216.003-T: P-002/P-004 verification-gated docs-only route (policy 1.39.0)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_MIRROR = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"

CODE_LABEL = "harness-ready"
DOCS_LABEL = "harness-verification-gated"
EXCLUSIVITY = re.compile(r"never|exclusive|not both|\bnot\b|neither|either|instead of|without", re.IGNORECASE)


def lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


def p002(text: str) -> str:
    return section(text, "## P-002: TDD Gate", "<!-- P-002.7:BEGIN")


def p004(text: str) -> str:
    return section(text, "## P-004: Red Phase Before Implementation", "\n## P-005")


def coexistence_violations(text: str) -> list[str]:
    """Lines that mention both route labels without exclusivity wording."""
    return [
        line for line in text.splitlines()
        if CODE_LABEL in line and DOCS_LABEL in line and not EXCLUSIVITY.search(line)
    ]


class DocsRoutePolicyTests(unittest.TestCase):
    def each(self):
        for path in (_TEMPLATE, _MIRROR):
            yield path.name, lf_text(path)

    def test_p002_describes_both_routes_and_code_route_unchanged(self) -> None:
        for name, text in self.each():
            body = p002(text)
            with self.subTest(file=name):
                self.assertIn("**Precondition** (ship): The task carries the `harness-ready` label.", body)
                self.assertIn("**Enforcement** (ship): Filter ready queue to only tasks carrying the `harness-ready` label.", body)
                self.assertIn("**Violation Action**: Halt and suggest running the harness-architect.", body)
                self.assertIn("The task has `harness-ready` label, the harness compiles", body)
                for field in ("Precondition", "Postcondition", "Enforcement"):
                    docs_marker = re.search(rf"\*\*{field}\*\*[^\n]*\n?[^\n]*\*\*Docs route", body)
                    self.assertIsNotNone(docs_marker, field)
                self.assertIn("The code route is unchanged", body)

    def test_p002_qualification_and_record_and_anti_loophole(self) -> None:
        for name, text in self.each():
            body = p002(text).lower()
            with self.subTest(file=name):
                for needle in (
                    "explicit owned paths", "prose `.md`", "deny list", "mixed scope disqualifies",
                    "markdown lint", "executable gate", "manual gate", "`harness-surface:none`",
                    "start-sha baseline", "autoharness harness docs-only-check", "--phase baseline",
                    "--phase completion", "p-005", "no route change after implementation starts",
                ):
                    self.assertIn(needle, body)

    def test_p004_describes_both_routes(self) -> None:
        for name, text in self.each():
            body = p004(text)
            with self.subTest(file=name):
                self.assertIn("Per P-002, only the harness-architect skill applies `harness-ready`; ship never bypasses this gate.", body)
                self.assertIn("**Postcondition**: The harness manifest records `Compilation: PASS` and `Red Phase: CONFIRMED`.", body)
                self.assertIn("**Violation Action**: Do NOT apply `harness-ready` label. Halt and report the failure.", body)
                self.assertIn(DOCS_LABEL, body)
                self.assertIn("no stub, test or RED evidence", body)
                self.assertRegex(body, r"\*\*Precondition\*\* \(docs route\)")
                self.assertRegex(body, r"\*\*Postcondition\*\* \(docs route\)")

    def test_labels_never_coexist(self) -> None:
        for name, text in self.each():
            with self.subTest(file=name):
                self.assertEqual(coexistence_violations(text), [])
                self.assertIn("never carries both", p002(text))
                self.assertIn("mutually exclusive", p002(text))

    def test_version_row_1_39_0(self) -> None:
        for name, text in self.each():
            with self.subTest(file=name):
                row = next(line for line in text.splitlines() if line.startswith("| 1.39.0"))
                self.assertIn("Amended P-002", row)
                self.assertIn("P-004", row)
                self.assertIn("216-F", row)
        self.assertIn("| 1.39.0  | {{DATE}}", lf_text(_TEMPLATE))
        self.assertRegex(lf_text(_MIRROR), r"\| 1\.39\.0  \| 20\d\d-\d\d-\d\d")


if __name__ == "__main__":
    unittest.main()

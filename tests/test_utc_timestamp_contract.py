"""P7 UTC contract for recorded dates and times.

Contract: every recorded date and time uses UTC. Times are written with a ``Z``
suffix, and ISO-8601 date-time literals carrying a numeric offset (for example
``-07:00``) are forbidden in templates and installed mirrors. Each of the four
P7 targets (the output-timestamp instruction, the two foundation documents, and
the compact-context skill) must carry the UTC rule in both its template and its
installed mirror.

Scope: the offset scan covers every text file under ``templates/`` plus every
installed artifact recorded in ``.autoharness/harness-manifest.yaml`` that has a
``template:`` key, excluding anything under ``.autoharness/``. That state is
operator-owned generated state; plan decision D4 in
``docs/plans/2026-10-08-backlogit-carryover-first-cut-plan.md`` defers it out of
scope for this cut.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST_RELPATH = ".autoharness/harness-manifest.yaml"
_OPERATOR_STATE_PREFIX = ".autoharness/"
_OFFSET_LITERAL = re.compile(r"T\d{2}:\d{2}(:\d{2})?(\.\d+)?[+-]\d{2}:?\d{2}")

# (name, template relpath, installed mirror relpath, markers one line must contain)
_P7_TARGETS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "output-timestamps",
        "templates/instructions/output-timestamps.instructions.md.tmpl",
        ".github/instructions/output-timestamps.instructions.md",
        ("## UTC for Recorded Dates and Times",),
    ),
    (
        "copilot-instructions",
        "templates/foundation/copilot-instructions.md.tmpl",
        ".github/copilot-instructions.md",
        ("UTC", "output-timestamps.instructions.md", "YYYY-MM-DD"),
    ),
    (
        "AGENTS",
        "templates/foundation/AGENTS.md.tmpl",
        "AGENTS.md",
        ("UTC", "output-timestamps.instructions.md", "YYYY-MM-DD"),
    ),
    (
        "compact-context",
        "templates/skills/compact-context/SKILL.md.tmpl",
        ".github/skills/compact-context/SKILL.md",
        ("UTC", "output-timestamps.instructions.md", "{YYYY-MM-DD}"),
    ),
)


def scan_targets(root: Path) -> list[str]:
    """Return sorted POSIX relpaths of text files under ``templates/`` plus the
    manifest-recorded installed mirrors that sit outside ``.autoharness/``."""
    manifest = yaml.safe_load((root / _MANIFEST_RELPATH).read_text(encoding="utf-8"))
    mirrors = {
        artifact["path"]
        for artifact in manifest["artifacts"]
        if "template" in artifact and not artifact["path"].startswith(_OPERATOR_STATE_PREFIX)
    }
    templates: set[str] = set()
    for path in (root / "templates").rglob("*"):
        relpath = path.relative_to(root)
        if not path.is_file() or "__pycache__" in relpath.parts:
            continue
        if b"\x00" in path.read_bytes():
            continue
        templates.add(relpath.as_posix())
    return sorted(templates | mirrors)


def scan_offset_literals(root: Path, relpaths: Iterable[str]) -> list[tuple[str, int, str]]:
    """Return ``(relpath, line_number, matched_text)`` for every offset-bearing literal."""
    findings: list[tuple[str, int, str]] = []
    for relpath in relpaths:
        # read_text applies universal newline translation, so split("\n") yields editor line numbers.
        text = (root / relpath).read_text(encoding="utf-8")
        for line_number, line in enumerate(text.split("\n"), start=1):
            findings.extend(
                (relpath, line_number, match.group(0)) for match in _OFFSET_LITERAL.finditer(line)
            )
    return findings


class P7UtcContractTest(unittest.TestCase):
    def test_scanner_reports_file_line_for_planted_offset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fixture.md").write_text(
                "# Fixture\n"
                "Recorded 2026-07-02T18:49:41Z in UTC.\n"
                "Local 2026-07-02T18:49:41-07:00 must be reported.\n",
                encoding="utf-8",
            )
            report = scan_offset_literals(root, ["fixture.md"])

        self.assertEqual(report, [("fixture.md", 3, "T18:49:41-07:00")])

    def test_templates_and_installed_mirrors_carry_no_offset_literals(self) -> None:
        targets = scan_targets(_ROOT)
        self.assertTrue(targets, "no scan targets discovered")
        self.assertFalse(
            [t for t in targets if t.startswith(_OPERATOR_STATE_PREFIX)],
            "operator-owned .autoharness/ state must not be a scan target",
        )

        findings = scan_offset_literals(_ROOT, targets)
        if findings:
            self.fail(
                f"{len(findings)} offset-bearing ISO-8601 literal(s) found; "
                "record times in UTC with a Z suffix:\n"
                + "\n".join(f"{rel}:{line}: {match}" for rel, line, match in findings)
            )

    def test_p7_targets_and_mirrors_carry_utc_rule(self) -> None:
        for name, template, mirror, markers in _P7_TARGETS:
            for relpath in (template, mirror):
                with self.subTest(target=name, path=relpath):
                    lines = (_ROOT / relpath).read_text(encoding="utf-8").split("\n")
                    self.assertTrue(
                        any(all(marker in line for marker in markers) for line in lines),
                        f"no single line in {relpath} contains all of {markers!r}",
                    )


if __name__ == "__main__":
    unittest.main()

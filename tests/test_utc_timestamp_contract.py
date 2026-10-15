"""P7 UTC contract for recorded dates and times.

Contract: every recorded date and time uses UTC. Times are written with a ``Z``
suffix, and ISO-8601 date-time literals carrying a numeric offset (for example
``-07:00``) are forbidden in templates and installed mirrors. Each of the four
P7 targets (the output-timestamp instruction, the two foundation documents, and
the compact-context skill) must carry the UTC rule in both its template and its
installed mirror.

Scope: the offset scan covers every file under ``templates/`` plus every
installed artifact recorded in ``.autoharness/harness-manifest.yaml`` that has a
``template:`` key, excluding anything under ``.autoharness/``. Template-tree files
must decode as UTF-8 with no NUL bytes; any that do not fail the scan. That state is
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

# Exact substrings each template and installed mirror must contain verbatim.
_MEMORY_UTC_ANCHOR = (
    "use the UTC date, and all recorded dates and times are UTC (`Z`); "
    "see `.github/instructions/output-timestamps.instructions.md`."
)

# (name, template relpath, installed mirror relpath, exact anchors)
_P7_TARGETS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "output-timestamps",
        "templates/instructions/output-timestamps.instructions.md.tmpl",
        ".github/instructions/output-timestamps.instructions.md",
        (
            "## UTC for Recorded Dates and Times",
            "Local-offset values (for example `-07:00`) are forbidden in recorded output.",
        ),
    ),
    (
        "copilot-instructions",
        "templates/foundation/copilot-instructions.md.tmpl",
        ".github/copilot-instructions.md",
        (_MEMORY_UTC_ANCHOR,),
    ),
    (
        "AGENTS",
        "templates/foundation/AGENTS.md.tmpl",
        "AGENTS.md",
        (_MEMORY_UTC_ANCHOR,),
    ),
    (
        "compact-context",
        "templates/skills/compact-context/SKILL.md.tmpl",
        ".github/skills/compact-context/SKILL.md",
        (
            "in every compacted, decided-plan, and closure-summary filename below is the UTC date; "
            "see `.github/instructions/output-timestamps.instructions.md` for the full rule.",
        ),
    ),
)


def _missing_anchors(text: str, anchors: Iterable[str]) -> list[str]:
    """Return the anchors that do not occur verbatim in ``text`` (CRLF normalized to LF)."""
    normalized = text.replace("\r\n", "\n")
    return [anchor for anchor in anchors if anchor not in normalized]


def _manifest_mirror_set(root: Path) -> set[str]:
    """Return the installed-mirror paths the manifest records with a ``template:`` key,
    excluding operator-owned ``.autoharness/`` state. Malformed manifests fail the test."""
    try:
        manifest = yaml.safe_load((root / _MANIFEST_RELPATH).read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AssertionError(f"{_MANIFEST_RELPATH} is not valid YAML: {exc}") from exc
    if not isinstance(manifest, dict):
        raise AssertionError(
            f"{_MANIFEST_RELPATH} must load to a mapping, got {type(manifest).__name__}"
        )
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise AssertionError(
            f"{_MANIFEST_RELPATH} must contain a list under 'artifacts', "
            f"got {type(artifacts).__name__}"
        )
    mirrors: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise AssertionError(
                f"{_MANIFEST_RELPATH} artifacts[{index}] must be a mapping, "
                f"got {type(artifact).__name__}"
            )
        if "template" not in artifact:
            continue
        path = artifact.get("path")
        if not isinstance(path, str):
            raise AssertionError(
                f"{_MANIFEST_RELPATH} artifacts[{index}] has a 'template' key but no "
                f"string 'path' (got {path!r})"
            )
        if not path.startswith(_OPERATOR_STATE_PREFIX):
            mirrors.add(path)
    return mirrors


def _template_files(root: Path) -> set[str]:
    """Return POSIX relpaths of every file under ``templates/``; fail closed on any
    file that contains a NUL byte or is not valid UTF-8."""
    templates_dir = root / "templates"
    if not templates_dir.is_dir():
        raise AssertionError(f"templates/ must be a directory under {root}")
    relpaths: set[str] = set()
    for path in templates_dir.rglob("*"):
        relpath = path.relative_to(root)
        if not path.is_file() or "__pycache__" in relpath.parts:
            continue
        data = path.read_bytes()
        if b"\x00" in data:
            raise AssertionError(
                f"{relpath.as_posix()} contains NUL bytes; templates must be UTF-8 text"
            )
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(f"{relpath.as_posix()} is not valid UTF-8: {exc}") from exc
        relpaths.add(relpath.as_posix())
    return relpaths


def scan_targets(root: Path) -> list[str]:
    """Return sorted POSIX relpaths of every file under ``templates/`` plus the
    manifest-recorded installed mirrors outside ``.autoharness/``."""
    return sorted(_template_files(root) | _manifest_mirror_set(root))


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
                "Local 2026-07-02T18:49:41-07:00 must be reported.\n"
                "Offset 2026-07-02T18:49:41+00:00 must be reported.\n"
                "Millis 2026-07-02T18:49:41.123+0000 must be reported.\n"
                "Date only 2026-07-02 is not a date-time literal.\n",
                encoding="utf-8",
            )
            report = scan_offset_literals(root, ["fixture.md"])

        self.assertEqual(
            report,
            [
                ("fixture.md", 3, "T18:49:41-07:00"),
                ("fixture.md", 4, "T18:49:41+00:00"),
                ("fixture.md", 5, "T18:49:41.123+0000"),
            ],
        )

    def test_templates_and_installed_mirrors_carry_no_offset_literals(self) -> None:
        self.assertTrue(
            (_ROOT / "templates").is_dir(),
            "templates/ must exist as a directory at the repository root",
        )
        mirrors = _manifest_mirror_set(_ROOT)
        self.assertTrue(mirrors, "manifest-derived mirror set is empty")

        targets = scan_targets(_ROOT)
        self.assertTrue(targets, "no scan targets discovered")
        for name, template, mirror, _ in _P7_TARGETS:
            with self.subTest(target=name, path=mirror):
                self.assertIn(mirror, mirrors, "P7 mirror is not recorded in the manifest")
            for relpath in (template, mirror):
                with self.subTest(target=name, path=relpath):
                    self.assertIn(relpath, targets, "P7 path is not in the scan target list")
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

    def test_p7_targets_and_mirrors_carry_exact_utc_anchors(self) -> None:
        for name, template, mirror, anchors in _P7_TARGETS:
            for relpath in (template, mirror):
                with self.subTest(target=name, path=relpath):
                    text = (_ROOT / relpath).read_text(encoding="utf-8")
                    missing = _missing_anchors(text, anchors)
                    self.assertFalse(
                        missing,
                        f"{relpath} lacks exact UTC anchor(s): {missing!r}",
                    )

    def test_manifest_and_template_tree_fail_closed(self) -> None:
        cases: tuple[tuple[str, str, dict[str, bytes], str], ...] = (
            ("no artifacts list", "schema_version: '1.0.0'\n", {}, "'artifacts'"),
            ("invalid YAML", "artifacts: [unclosed\n", {}, "not valid YAML"),
            ("artifact not a mapping", "artifacts:\n  - just-a-string\n", {}, "artifacts[0]"),
            (
                "template entry without path",
                "artifacts:\n  - path: a.md\n  - template: x.tmpl\n",
                {},
                "artifacts[1]",
            ),
            (
                "template entry with non-string path",
                "artifacts:\n  - path: 42\n    template: x.tmpl\n",
                {},
                "artifacts[0]",
            ),
            (
                "NUL byte in templates/",
                "artifacts: []\n",
                {"templates/bad.md": b"ok\x00bad\n"},
                "templates/bad.md",
            ),
            (
                "undecodable bytes in templates/",
                "artifacts: []\n",
                {"templates/bad.md": b"\xff\xfe\n"},
                "templates/bad.md",
            ),
        )
        for label, manifest_text, files, needle in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".autoharness").mkdir()
                (root / _MANIFEST_RELPATH).write_text(manifest_text, encoding="utf-8")
                (root / "templates").mkdir()
                for relpath, data in files.items():
                    (root / relpath).write_bytes(data)
                with self.assertRaises(AssertionError) as ctx:
                    scan_targets(root)
                self.assertIn(needle, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

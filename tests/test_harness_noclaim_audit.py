"""Unit C, task C5 (187.005-T): the IM-14 / PE-SAFETY-06 non-claim text audit.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "Non-Claim Audit Inventory" (P2-critical).

* FLOOR: a closed list of repo-relative POSIX paths read from the working tree
  (no git, no skip path). A listed file that is missing fails.
* Reading: strict UTF-8 (invalid bytes fail), CR removed; each line lowercased,
  ``_`` and ``-`` become spaces, whitespace runs collapse (leading and trailing
  whitespace dropped). Each adjacent pair of lines is joined raw with a space;
  if that join has no spanning match and the first line, after its trailing
  whitespace is stripped, ends in ``-``, the pair is joined again with that
  hyphen and all whitespace at the join dropped. Only matches spanning the
  join count. A unit (line or join) hashes as SHA-256 of its normalized UTF-8.
* Clearing: a line hit clears when the line has no hit once the normalized
  required sentence is replaced with nothing; any hit clears when its
  ``(path, SHA-256)`` is a ``LEDGER`` non-claim entry. Any other hit fails, as
  does a LEDGER entry unused on the run. The LEDGER path key is the same
  repo-relative POSIX string used in FLOOR.
* camelCase claims (for example ``raceFree``) are not caught by the detector;
  they fall to the recorded residue audit (IM-14-F35).

This module and the case-coverage module are structural tests: they reach no
RED-phase stub and are recorded outside any roster.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import unittest
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FLOOR: tuple[str, ...] = (
    "src/autoharness/harness_read.py",
    "src/autoharness/harness_surfaces.py",
)

# (repo-relative POSIX path, SHA-256 of the normalized unit) -> "non-claim".
# C5 adds no entry: harness_read.py has no detector hit outside the required
# sentence (confirmed by local review). B1-B3 (188.001-T..188.003-T) add no
# entry: harness_surfaces.py has no detector hit (confirmed by 194-S local review).
# B4a-B5 (189.001-T..189.003-T) add no entry (confirmed by 195-S local review).
LEDGER: dict[tuple[str, str], str] = {}

# IM-14-F51 (B5, 189.003-T): the S(B-entry) residue units. They are not FLOOR
# entries (FLOOR grows only by B1 and D1). Each falls to the recorded agent text
# audit (the shipment closure note), once, and is re-opened only when a later
# commit modifies its lines. The captured help text is checked against DETECTOR
# by tests/test_harness_resolve_cli.py.
RESIDUE_UNITS: tuple[str, ...] = (
    "src/autoharness/cli.py",
    "tests/test_harness_surfaces_digest.py",
    "tests/test_harness_surfaces_reducer.py",
    "tests/test_harness_resolve_cli.py",
    "tests/test_harness_noclaim_audit.py",
    "captured text: autoharness harness resolve --help",
)

REQUIRED_SENTENCE = (
    "This reader makes no race, TOCTOU or hardlink-alias resistance claim."
)

DETECTOR = re.compile(
    r"\b(?:rac(?:e[sd]?|ing|y)|toctt?ous?|time of check|hard ?link\w*|symlink ?swap\w*)\b"
)


def normalize_mapped(raw: str) -> tuple[str, list[int]]:
    """Normalize ``raw`` and map each normalized character to its source index."""
    out: list[str] = []
    source: list[int] = []
    pending_space = -1
    for index, character in enumerate(raw):
        for lowered in character.lower():
            if lowered in "_-":
                lowered = " "
            if lowered.isspace():
                if pending_space < 0:
                    pending_space = index
                continue
            if pending_space >= 0 and out:
                out.append(" ")
                source.append(pending_space)
            pending_space = -1
            out.append(lowered)
            source.append(index)
    return "".join(out), source


def normalize(raw: str) -> str:
    return normalize_mapped(raw)[0]


NORMALIZED_SENTENCE = normalize(REQUIRED_SENTENCE)


def unit_hash(normalized: str) -> str:
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class AuditReport:
    failures: list[str] = field(default_factory=list)
    cleared_by_sentence: int = 0
    cleared_by_ledger: int = 0
    unit_hashes: dict[str, list[str]] = field(default_factory=dict)


def _spanning(raw: str, boundary_left: int, boundary_right: int) -> tuple[str, bool]:
    normalized, source = normalize_mapped(raw)
    for match in DETECTOR.finditer(normalized):
        if source[match.start()] < boundary_left and source[match.end() - 1] >= boundary_right:
            return normalized, True
    return normalized, False


def audit(
    root: Path, floor: Sequence[str], ledger: Collection[tuple[str, str]]
) -> AuditReport:
    """Run the non-claim audit over ``floor`` (paths relative to ``root``)."""
    report = AuditReport()
    used: set[tuple[str, str]] = set()

    def ledger_clears(path: str, normalized: str) -> bool:
        key = (path, unit_hash(normalized))
        if key in ledger:
            used.add(key)
            report.cleared_by_ledger += 1
            return True
        return False

    for path in floor:
        file_path = root / path
        if not file_path.is_file():
            report.failures.append(f"{path}: listed FLOOR file is missing")
            continue
        try:
            text = file_path.read_bytes().decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            report.failures.append(f"{path}: not valid UTF-8 ({error.reason})")
            continue
        lines = text.replace("\r", "").split("\n")
        hashes = report.unit_hashes.setdefault(path, [])
        for number, line in enumerate(lines, start=1):
            normalized = normalize(line)
            hashes.append(unit_hash(normalized))
            if not DETECTOR.search(normalized):
                continue
            if not DETECTOR.search(normalized.replace(NORMALIZED_SENTENCE, "")):
                report.cleared_by_sentence += 1
                continue
            if not ledger_clears(path, normalized):
                report.failures.append(f"{path}:{number}: claim-form hit: {normalized!r}")
        for number in range(1, len(lines)):
            first, second = lines[number - 1], lines[number]
            joined, spans = _spanning(first + " " + second, len(first), len(first) + 1)
            if not spans:
                stripped = first.rstrip()
                if not stripped.endswith("-"):
                    continue
                left = stripped[:-1]
                joined, spans = _spanning(left + second.lstrip(), len(left), len(left))
                if not spans:
                    continue
            hashes.append(unit_hash(joined))
            if not ledger_clears(path, joined):
                report.failures.append(
                    f"{path}:{number}-{number + 1}: claim-form hit across the join: {joined!r}"
                )
    for key in sorted(set(ledger) - used):
        report.failures.append(f"LEDGER entry unused on this run: {key[0]} {key[1]}")
    return report


class FloorAuditTests(unittest.TestCase):
    def test_structural_floor_is_closed_repo_relative_posix(self) -> None:
        # Deliberate tripwire: B1 and D1 extend FLOOR (IM-14-F51) and must edit this
        # assertion with it. B1 (188.001-T) added harness_surfaces.py.
        self.assertEqual(
            FLOOR,
            ("src/autoharness/harness_read.py", "src/autoharness/harness_surfaces.py"),
        )
        for path in FLOOR:
            self.assertNotIn("\\", path)
            self.assertFalse(path.startswith("/"))
        for path, _digest in LEDGER:
            self.assertIn(path, FLOOR)
        self.assertTrue(all(value == "non-claim" for value in LEDGER.values()))

    def test_structural_residue_units_are_not_floor_entries(self) -> None:
        # IM-14-F51: B-entry adds residue units, never FLOOR entries.
        self.assertEqual(len(set(RESIDUE_UNITS)), len(RESIDUE_UNITS))
        for unit in RESIDUE_UNITS:
            self.assertNotIn(unit, FLOOR)
            if unit.startswith("captured text: "):
                continue
            self.assertNotIn("\\", unit)
            self.assertTrue((REPO_ROOT / unit).is_file(), unit)

    def test_structural_floor_audit_passes(self) -> None:
        report = audit(REPO_ROOT, FLOOR, LEDGER)
        self.assertEqual(report.failures, [])

    def test_structural_required_sentence_on_one_physical_line(self) -> None:
        source = (REPO_ROOT / "src/autoharness/harness_read.py").read_text(encoding="utf-8")
        self.assertTrue(any(REQUIRED_SENTENCE in line for line in source.splitlines()))
        report = audit(REPO_ROOT, FLOOR, LEDGER)
        self.assertGreaterEqual(report.cleared_by_sentence, 1)


class AuditControlTests(unittest.TestCase):
    """The plan's must-fail and must-not-hit controls, over temporary files."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ahlc-c5-audit-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def run_audit(self, content: str | bytes, ledger: Collection[tuple[str, str]] = ()) -> AuditReport:
        data = content.encode("utf-8") if isinstance(content, str) else content
        (self.root / "f.py").write_bytes(data)
        return audit(self.root, ["f.py"], ledger)

    def assert_fails(self, content: str | bytes) -> None:
        self.assertNotEqual(self.run_audit(content).failures, [], repr(content))

    def assert_clean(self, content: str) -> None:
        self.assertEqual(self.run_audit(content).failures, [], repr(content))

    def test_structural_control_claim_forms_fail(self) -> None:
        for claim in (
            # IM-14-F05
            "resistant to race",
            "protects against TOCTOU",
            # IM-14-F10 and IM-14-F11
            "race-condition-free",
            "race condition safe",
            "guards against a TOCTOU race",
            "protects against the race",
            "prevents a race",
            "free of race conditions",
            "safe from TOCTOU",
            "provides TOCTOU resistance",
            # identifier and spelling forms
            "race_free",
            "test_toctou_safe",
            "TOCTTOU",
            "hard-linked",
            "racy reads",
            "symlink-swap safe",
            "time-of-check safe",
        ):
            with self.subTest(claim=claim):
                self.assert_fails(f"x = 1  # {claim}\n")

    def test_structural_control_split_claims_fail(self) -> None:
        for first, second in (
            ("race-", "free"),  # fails on the first line alone; the join cannot match
            ("hard-", "link"),
            ("TOC-", "TOU"),
            ("TOC- ", "TOU"),  # IM-14-F57: trailing whitespace after the hyphen
            (REQUIRED_SENTENCE + " TOC-", "TOU resistance"),
        ):
            with self.subTest(first=first, second=second):
                self.assert_fails(f"{first}\n{second}\n")

    def test_structural_control_sentence_removal_replaces_with_nothing(self) -> None:
        # IM-14-F47: removal leaves "TOC" + "TOU" adjacent, which must still hit.
        self.assert_fails(f"TOC{REQUIRED_SENTENCE}TOU\n")

    def test_structural_control_required_sentence_hits_and_clears(self) -> None:
        self.assertIsNotNone(DETECTOR.search(normalize(REQUIRED_SENTENCE)))
        report = self.run_audit(f'"""Doc.\n\n{REQUIRED_SENTENCE}\n"""\n')
        self.assertEqual(report.failures, [])
        self.assertEqual(report.cleared_by_sentence, 1)

    def test_structural_control_must_not_hit(self) -> None:
        for text in ("trace-free", "embrace-safe", "grace period"):
            with self.subTest(text=text):
                self.assertIsNone(DETECTOR.search(normalize(text)))
                self.assert_clean(f"# {text}\n")

    def test_structural_control_ledger_entry_for_another_path_fails(self) -> None:
        line = "# documented non-claim about a race window"
        digest = unit_hash(normalize(line))
        self.assertEqual(self.run_audit(line + "\n", {("f.py", digest)}).failures, [])
        failures = self.run_audit(line + "\n", {("other.py", digest)}).failures
        self.assertTrue(any("claim-form hit" in failure for failure in failures))
        self.assertTrue(any("unused" in failure for failure in failures))

    def test_structural_control_unused_ledger_entry_fails(self) -> None:
        failures = self.run_audit("x = 1\n", {("f.py", "0" * 64)}).failures
        self.assertTrue(any("unused" in failure for failure in failures))

    def test_structural_control_missing_floor_file_fails(self) -> None:
        failures = audit(self.root, ["absent.py"], ()).failures
        self.assertTrue(any("missing" in failure for failure in failures))

    def test_structural_control_invalid_utf8_fails(self) -> None:
        self.assert_fails(b"x = 1\n# \xff\xfe\n")

    def test_structural_control_crlf_copy_hashes_as_lf(self) -> None:
        text = f"a = 1\n# {REQUIRED_SENTENCE}\nb = 2\n"
        lf = self.run_audit(text).unit_hashes["f.py"]
        crlf = self.run_audit(text.replace("\n", "\r\n")).unit_hashes["f.py"]
        self.assertEqual(lf, crlf)


if __name__ == "__main__":
    unittest.main()

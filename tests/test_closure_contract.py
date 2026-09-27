"""Closure-evidence naming contract module tests (167.001-T, plan unit U1).

Normative source: docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
(revision 5), section "Contract Specification", items C1-C3 and C5.

Every fixture lives in a temporary scratch directory; no test in this module
reads, globs, or stats the committed ``docs/closure/`` corpus (C6).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _closure_legacy_names import legacy_closure_filename
from autoharness.gates import closure_contract
from autoharness.gates.closure_contract import (
    CLOSURE_FEATURE_ID_PATTERN,
    CLOSURE_SHIPMENT_ID_PATTERN,
    RECOGNIZED_CLOSURE_PATTERNS,
    ClosureDiscovery,
    attribute_closure_candidate,
    build_closure_path,
    classify_closure_candidates,
)

_R1, _R2 = RECOGNIZED_CLOSURE_PATTERNS


def _touch(directory: Path, name: str) -> Path:
    path = directory / name
    path.write_text("---\nclosure_status: READY\ncompaction_status: done\n---\n", encoding="utf-8")
    return path


def _closure_dir(workspace: Path) -> Path:
    closure_dir = workspace / "docs" / "closure"
    closure_dir.mkdir(parents=True)
    return closure_dir


def _canonical_name(workspace: Path, shipment_id: str, feature_id: str) -> str:
    """C6: canonical fixture names on disk always come from the builder."""
    return build_closure_path("docs/closure", shipment_id, feature_id, workspace_root=workspace).name


class ClosureNameClassificationMatrixTests(unittest.TestCase):
    """Scenario 1 -- classification matrix (canonical / legacy / both / neither)."""

    def test_classification_matrix(self) -> None:
        # (filename, matches R1, matches R2)
        rows = (
            ("162-S-154-F-post-merge-closure.md", True, False),
            ("2026-09-11-162-s-154-f-closure.md", False, True),
            ("2026-09-11-162-S-154-F-closure.md", False, True),
            ("2026-09-14-173-s-165-f-closure.md", False, True),
            # Neither: foreign shapes.
            ("138-S-129-F-cancellation-closure.md", False, False),
            ("2026-09-11-162-s-154-f-runtime-verification.md", False, False),
            ("2026-07-26-088f-compression-closure-summary.md", False, False),
            ("162-S-notes.md", False, False),
            # Uppercase-only canonical rejects (RQ-17).
            ("162-S-15-4-F-post-merge-closure.md", False, False),  # internal-hyphen feature
            ("162-S-154-T-post-merge-closure.md", False, False),  # wrong kind letter
            ("162-S-some-slug-post-merge-closure.md", False, False),  # free-form slug
            ("162-s-154-f-post-merge-closure.md", False, False),  # lowercase kind letters
            ("162-S-154-f-post-merge-closure.md", False, False),  # lowercase feature kind
            ("162-S-154-F-post-merge-closure.md.bak", False, False),  # trailing suffix
            ("x162-S-154-F-post-merge-closure", False, False),  # missing extension
        )
        for filename, want_r1, want_r2 in rows:
            with self.subTest(filename=filename):
                self.assertEqual(bool(_R1.match(filename)), want_r1, "R1")
                self.assertEqual(bool(_R2.match(filename)), want_r2, "R2")

    def test_classifier_partitions_both_and_neither(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            closure_dir = _closure_dir(workspace)
            # C6: canonical fixture names come from the builder, legacy names
            # from the single test-only legacy helper.
            canonical = _touch(closure_dir, _canonical_name(workspace, "162-S", "154-F"))
            legacy = _touch(closure_dir, legacy_closure_filename("162-s", "154-f"))
            unrecognized = _touch(closure_dir, "2026-09-11-162-s-154-f-runtime-verification.md")
            _touch(closure_dir, _canonical_name(workspace, "161-S", "153-F"))  # foreign, not attributed
            discovery = classify_closure_candidates(closure_dir, "162-S")
            self.assertIsInstance(discovery, ClosureDiscovery)
            self.assertEqual(discovery.canonical_matches, (canonical,))
            self.assertEqual(discovery.legacy_matches, (legacy,))
            self.assertEqual(discovery.unrecognized_candidates, (unrecognized,))
            self.assertEqual(discovery.outcome, "recognized")

            for path in (canonical, legacy):
                path.unlink()
            discovery = classify_closure_candidates(closure_dir, "162-S")
            self.assertEqual(discovery.outcome, "unrecognized")
            self.assertEqual(discovery.unrecognized_candidates, (unrecognized,))

    def test_missing_directory_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            discovery = classify_closure_candidates(Path(tmp) / "missing", "162-S")
            self.assertEqual(discovery.outcome, "absent")
            self.assertEqual(discovery.canonical_matches, ())
            self.assertEqual(discovery.legacy_matches, ())
            self.assertEqual(discovery.unrecognized_candidates, ())

    def test_identifier_grammars_are_uppercase_only(self) -> None:
        self.assertTrue(CLOSURE_SHIPMENT_ID_PATTERN.match("162-S"))
        self.assertTrue(CLOSURE_FEATURE_ID_PATTERN.match("154-F"))
        for bad in ("162-s", "162-F", "16-2-S", "-162-S", "162-S\n", ""):
            with self.subTest(shipment_id=bad):
                self.assertIsNone(CLOSURE_SHIPMENT_ID_PATTERN.match(bad))
        for bad in ("154-f", "154-S", "15-4-F", "154-F "):
            with self.subTest(feature_id=bad):
                self.assertIsNone(CLOSURE_FEATURE_ID_PATTERN.match(bad))


class ClosureAttributionMatrixTests(unittest.TestCase):
    """Scenario 2 -- designated-position attribution (C3), never a token search."""

    def test_attribution_matrix(self) -> None:
        rows = (
            # Designated primary position, both grammars, both directions.
            ("16-S-154-F-post-merge-closure.md", "162-S", False),
            ("162-S-154-F-post-merge-closure.md", "16-S", False),
            ("162-S-154-F-post-merge-closure.md", "162-S", True),
            ("2026-09-11-16-s-154-f-closure.md", "162-S", False),
            ("2026-09-11-162-s-154-f-closure.md", "16-S", False),
            ("2026-09-11-162-s-154-f-closure.md", "162-S", True),
            # Requested token appears ONLY in a free-form suffix.
            ("2026-09-11-16-S-supersedes-162-S-closure.md", "162-S", False),
            ("2026-09-11-16-S-supersedes-162-S-closure.md", "16-S", True),
            ("16-S-162-S-post-merge-closure.md", "162-S", False),
            # Canonical position requested under a differently-cased token:
            # casefold tolerance must not leak onto the canonical position.
            ("162-S-167-F-post-merge-closure.md", "162-s", False),
            # Legacy position is case-folded.
            ("2026-09-11-162-S-154-F-closure.md", "162-s", True),
            # Unparseable names are never attributed.
            (".gitkeep", "162-S", False),
            ("pr342-pr339-review-remediation-closure.md", "162-S", False),
            ("2026-08-05-pipeline-topology-gates-abc-closure-summary.md", "162-S", False),
            ("162-S.md", "162-S", False),
        )
        for filename, requested, expected in rows:
            with self.subTest(filename=filename, requested=requested):
                self.assertIs(attribute_closure_candidate(filename, requested), expected)

    def test_absent_shipment_in_non_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            closure_dir = _closure_dir(workspace)
            for name in (
                _canonical_name(workspace, "161-S", "153-F"),
                _canonical_name(workspace, "16-S", "154-F"),
                legacy_closure_filename("16-S", "supersedes-162-S"),
                "2026-09-11-16-s-154-f-runtime-verification.md",
                "138-S-129-F-cancellation-closure.md",
                "pr411-p020-context-compaction-closure.md",
            ):
                _touch(closure_dir, name)
            discovery = classify_closure_candidates(closure_dir, "162-S")
            self.assertEqual(discovery.outcome, "absent")
            self.assertEqual(discovery.unrecognized_candidates, ())
            self.assertEqual(discovery.canonical_matches, ())
            self.assertEqual(discovery.legacy_matches, ())


class ClosureDeterministicOrderingTests(unittest.TestCase):
    """Scenario 3 -- deterministic sorted ordering under multiple matches."""

    def test_multiple_matches_are_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            closure_dir = _closure_dir(workspace)
            names_canonical = (
                _canonical_name(workspace, "162-S", "200-F"),
                _canonical_name(workspace, "162-S", "154-F"),
                _canonical_name(workspace, "162-S", "17-F"),
            )
            names_legacy = (
                legacy_closure_filename("162-s", "b", date="2026-09-12"),
                legacy_closure_filename("162-s", "a", date="2026-09-11"),
            )
            for name in names_canonical + names_legacy:
                _touch(closure_dir, name)
            first = classify_closure_candidates(closure_dir, "162-S")
            second = classify_closure_candidates(closure_dir, "162-S")
            self.assertEqual(first, second)
            self.assertEqual(
                tuple(p.name for p in first.canonical_matches), tuple(sorted(names_canonical))
            )
            self.assertEqual(
                tuple(p.name for p in first.legacy_matches), tuple(sorted(names_legacy))
            )


class ClosureRecognizedSetCardinalityTests(unittest.TestCase):
    """Scenario 4 -- the recognized read set is closed at exactly two members."""

    def test_recognized_set_has_exactly_two_members(self) -> None:
        self.assertIsInstance(RECOGNIZED_CLOSURE_PATTERNS, tuple)
        self.assertEqual(len(RECOGNIZED_CLOSURE_PATTERNS), 2)

    def test_contract_module_reads_no_frontmatter(self) -> None:
        source = Path(closure_contract.__file__).read_text(encoding="utf-8")
        for forbidden in ("import yaml", "safe_load", "_frontmatter(", "read_text("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

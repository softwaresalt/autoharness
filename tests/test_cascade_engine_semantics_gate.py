"""Tests for the P-015 cascade engine-semantics gate and close-path composition.

Covers plan unit U1a (``docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md``):
``assess_cascade_engine_semantics`` (tasks 196.001-T and 196.002-T) and
``select_close_path`` plus the flat module docstring (task 196.003-T) in
``src/autoharness/gates/shipment_closure.py``.
"""

from __future__ import annotations

import dataclasses
import re
import unittest
from pathlib import Path

from autoharness.gates import shipment_closure
from autoharness.gates.shipment_closure import (
    VERIFIED_CASCADE_ENGINE_MINOR_LINES,
    ClosePath,
    ClosePathDecision,
    EngineSemanticsDecision,
    EngineSemanticsVerdict,
    assess_cascade_engine_semantics,
    select_close_path,
)

_PREFIX = "ENGINE_SEMANTICS_UNVERIFIED:"

_ROOT = Path(__file__).resolve().parents[1]
_POLICY_TEXTS = (
    _ROOT / "templates" / "policies" / "workflow-policies.md.tmpl",
    _ROOT / ".github" / "policies" / "workflow-policies.md",
)
_SKILL_TEXTS = (
    _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl",
    _ROOT / ".github" / "skills" / "shipment-reconcile" / "SKILL.md",
)
_ENGINE_LINE_TOKEN_RE = re.compile(r"Verified engine-semantics lines:\s*`([^`]+)`")
_RELEASE_EXAMPLE_RE = re.compile(r"`(v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)`")


def _assess(version: object, surface: object = "cli", invocation: object = "cli", **kwargs):
    return assess_cascade_engine_semantics(
        version, probe_surface=surface, invocation_surface=invocation, **kwargs
    )


def _content(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _minor_lines_from_token(text: str) -> frozenset[tuple[int, int]]:
    match = _ENGINE_LINE_TOKEN_RE.search(text)
    if match is None:
        raise AssertionError("Verified engine-semantics lines token missing")
    lines: set[tuple[int, int]] = set()
    for raw_line in match.group(1).split(","):
        line = raw_line.strip()
        parts = line.split(".")
        if len(parts) != 2 or not all(part.isascii() and part.isdigit() for part in parts):
            raise AssertionError(f"invalid engine-semantics line token: {line!r}")
        lines.add((int(parts[0]), int(parts[1])))
    return frozenset(lines)


def _policy_engine_region(text: str) -> str:
    token = text.index("Verified engine-semantics lines:")
    start = text.rindex("**Evidence-class note.**", 0, token)
    end = text.index("**SAFE_CLOSE reliance.**", token)
    return text[start:end]


def _skill_engine_region(text: str) -> str:
    start = text.index("**Engine-semantics gate (P-015 engine-semantics precondition).**")
    end = text.index("**Close-path selection.**", start)
    return text[start:end]


class _StrSubclass(str):
    """A ``str`` subclass: only an exact ``str`` is an acceptable probe value."""


class EngineSemanticsVerdictCoreTests(unittest.TestCase):
    """196.001-T scenarios E1-E3."""

    def test_e1_released_verified_line_is_verified_on_matching_surfaces(self) -> None:
        for surface in ("mcp", "cli"):
            for version in ("1.11.0", "v1.11.0", "1.11.7"):
                with self.subTest(surface=surface, version=version):
                    decision = _assess(version, surface, surface, probed_commit="abc123")
                    self.assertIs(decision.verdict, EngineSemanticsVerdict.VERIFIED)
                    self.assertEqual(decision.minor_line, (1, 11))
                    self.assertEqual(decision.probed_version, version)
                    self.assertEqual(decision.probe_surface, surface)
                    self.assertEqual(decision.probed_commit, "abc123")
                    self.assertFalse(decision.reason.startswith(_PREFIX))

    def test_e2_prerelease_or_build_metadata_is_unreleased_build(self) -> None:
        for version in (
            "1.11.1-0.20261001000000-abcdef123456",
            "1.11.0+dirty",
            "1.11.1-0.20261001000000-abcdef123456+dirty",
            "1.11.1-rc1",
        ):
            with self.subTest(version=version):
                decision = _assess(version)
                self.assertIs(decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertTrue(decision.reason.startswith(_PREFIX), decision.reason)
                self.assertIn("unreleased build", decision.reason)
                self.assertEqual(decision.probed_version, version)

    def test_e3_unverified_minor_lines_name_the_line(self) -> None:
        for version, line in (
            ("1.10.0", "1.10"),
            ("1.10.1", "1.10"),
            ("1.12.0", "1.12"),
            ("2.11.0", "2.11"),
        ):
            with self.subTest(version=version):
                decision = _assess(version)
                self.assertIs(decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertTrue(decision.reason.startswith(_PREFIX), decision.reason)
                self.assertIn(f"minor line {line} not verified", decision.reason)

        decision = _assess("1.12.0-rc1")
        self.assertIs(decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
        self.assertTrue(decision.reason.startswith(_PREFIX), decision.reason)

    def test_e3_verified_minor_line_constant_is_single_line(self) -> None:
        self.assertEqual(VERIFIED_CASCADE_ENGINE_MINOR_LINES, frozenset({(1, 11)}))
        self.assertIsInstance(VERIFIED_CASCADE_ENGINE_MINOR_LINES, frozenset)

    def test_decision_is_frozen(self) -> None:
        decision = _assess("1.11.0")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            decision.verdict = EngineSemanticsVerdict.UNVERIFIED  # type: ignore[misc]

    def test_unreleased_build_is_reported_before_surface_checks(self) -> None:
        decision = _assess("1.11.0+dirty", "mcp", "cli")
        self.assertIn("unreleased build", decision.reason)
        self.assertEqual(decision.minor_line, (1, 11))

    def test_new_names_are_not_exported_from_gates_package(self) -> None:
        import autoharness.gates as gates_pkg

        for name in (
            "assess_cascade_engine_semantics",
            "select_close_path",
            "EngineSemanticsDecision",
            "VERIFIED_CASCADE_ENGINE_MINOR_LINES",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(gates_pkg, name))
                self.assertNotIn(name, getattr(gates_pkg, "__all__", ()))


class EngineSemanticsInputStrictnessTests(unittest.TestCase):
    """196.002-T scenarios E4-E5."""

    def test_e4_non_string_or_unparseable_versions_are_unverified(self) -> None:
        cases: list[object] = [
            None,
            "",
            " 1.11.0",
            "1.11.0 ",
            "1.11.0\n",
            "1.11",
            "dev",
            "(devel)",
            "\uff11.\uff11\uff11.\uff10",  # full-width digits
            "\u0661.\u0661\u0661.\u0660",  # Arabic-Indic digits
            1.11,
            b"1.11.0",
            _StrSubclass("1.11.0"),
            "1" * 5000 + ".11.0",  # int() digit-limit must not raise
        ]
        for version in cases:
            with self.subTest(version=repr(version)[:40]):
                decision = _assess(version)
                self.assertIs(decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertTrue(decision.reason.startswith(_PREFIX), decision.reason)
                self.assertTrue(
                    "non-string" in decision.reason or "unparseable" in decision.reason,
                    decision.reason,
                )
                self.assertIsNone(decision.minor_line)

    def test_e4_non_string_version_is_not_recorded(self) -> None:
        for version in (None, 1.11, b"1.11.0", _StrSubclass("1.11.0")):
            with self.subTest(version=repr(version)):
                decision = _assess(version)
                self.assertIn("non-string", decision.reason)
                self.assertIsNone(decision.probed_version)

    def test_e5_probe_surface_mismatch_and_unknown_surfaces(self) -> None:
        mismatch = _assess("1.11.0", "mcp", "cli")
        self.assertIs(mismatch.verdict, EngineSemanticsVerdict.UNVERIFIED)
        self.assertTrue(mismatch.reason.startswith(_PREFIX))
        self.assertIn("probe surface mismatch", mismatch.reason)

        for surface, invocation in ((None, "cli"), ("cli", None), ("MCP", "MCP"), ("mcp", "MCP")):
            with self.subTest(surface=surface, invocation=invocation):
                decision = _assess("1.11.0", surface, invocation)
                self.assertIs(decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertTrue(decision.reason.startswith(_PREFIX))
                self.assertIn("unknown probe surface", decision.reason)

    def test_probed_commit_recorded_verbatim_only_for_exact_str(self) -> None:
        self.assertEqual(_assess("1.11.0", probed_commit=" abc\n").probed_commit, " abc\n")
        self.assertIsNone(_assess("1.11.0", probed_commit=123).probed_commit)
        self.assertIsNone(_assess("1.11.0", probed_commit=_StrSubclass("abc")).probed_commit)

    def test_never_raises_on_hostile_inputs(self) -> None:
        class Hostile:
            def __eq__(self, other: object) -> bool:
                raise RuntimeError("boom")

            def __hash__(self) -> int:
                raise RuntimeError("boom")

            def __repr__(self) -> str:
                raise RuntimeError("boom")

        decision = assess_cascade_engine_semantics(
            Hostile(), probe_surface=Hostile(), invocation_surface=Hostile(), probed_commit=Hostile()
        )
        self.assertIs(decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
        self.assertTrue(decision.reason.startswith(_PREFIX))


class EngineSemanticsProseConsistencyTests(unittest.TestCase):
    """199.002-T scenarios L1-L3: policy/skill prose matches the code gate."""

    def test_l1_policy_verified_engine_semantics_token_matches_constant(self) -> None:
        for path in _POLICY_TEXTS:
            with self.subTest(path=str(path.relative_to(_ROOT))):
                self.assertEqual(
                    _minor_lines_from_token(_content(path)),
                    VERIFIED_CASCADE_ENGINE_MINOR_LINES,
                )

    def test_l2_skill_verified_engine_semantics_token_matches_constant(self) -> None:
        for path in _SKILL_TEXTS:
            with self.subTest(path=str(path.relative_to(_ROOT))):
                self.assertEqual(
                    _minor_lines_from_token(_content(path)),
                    VERIFIED_CASCADE_ENGINE_MINOR_LINES,
                )

    def test_l3_quoted_prose_version_examples_have_stated_verdicts(self) -> None:
        examples: list[tuple[Path, str, EngineSemanticsVerdict]] = []
        for path in _POLICY_TEXTS:
            region = _policy_engine_region(_content(path))
            self.assertIn("Under the verified engine-semantics line", region)
            for version in _RELEASE_EXAMPLE_RE.findall(region):
                examples.append((path, version, EngineSemanticsVerdict.VERIFIED))
        for path in _SKILL_TEXTS:
            region = _skill_engine_region(_content(path))
            self.assertIn("Anything else", region)
            self.assertIn("is `UNVERIFIED`", region)
            for version in _RELEASE_EXAMPLE_RE.findall(region):
                expected = (
                    EngineSemanticsVerdict.VERIFIED
                    if tuple(map(int, version.removeprefix("v").split(".")[:2]))
                    in VERIFIED_CASCADE_ENGINE_MINOR_LINES
                    else EngineSemanticsVerdict.UNVERIFIED
                )
                examples.append((path, version, expected))
        self.assertTrue(examples, "expected at least one quoted concrete release-version example")
        for path, version, expected in examples:
            with self.subTest(path=str(path.relative_to(_ROOT)), version=version):
                decision = _assess(version, "cli", "cli", probed_commit="5a4b70dd")
                self.assertIs(decision.verdict, expected)


class SelectClosePathTests(unittest.TestCase):
    """196.003-T scenario E6: the 2x2 matrix plus invalid input."""

    def setUp(self) -> None:
        self.cascade = ClosePathDecision(close_path=ClosePath.CASCADE, reason="classifier-cascade")
        self.safe = ClosePathDecision(close_path=ClosePath.SAFE_CLOSE, reason="classifier-safe")
        self.verified = _assess("1.11.0")
        self.unverified = _assess("1.12.0")

    def test_e6_cascade_requires_both_classifier_cascade_and_verified_engine(self) -> None:
        path, reason = select_close_path(self.cascade, self.verified)
        self.assertIs(path, ClosePath.CASCADE)
        self.assertIn("classifier-cascade", reason)

    def test_e6_classifier_safe_close_wins_regardless_of_engine(self) -> None:
        for engine in (self.verified, self.unverified):
            with self.subTest(engine=engine.verdict):
                path, reason = select_close_path(self.safe, engine)
                self.assertIs(path, ClosePath.SAFE_CLOSE)
                self.assertEqual(reason, "classifier-safe")

    def test_e6_unverified_engine_downgrades_cascade_with_engine_reason(self) -> None:
        path, reason = select_close_path(self.cascade, self.unverified)
        self.assertIs(path, ClosePath.SAFE_CLOSE)
        self.assertEqual(reason, self.unverified.reason)
        self.assertTrue(reason.startswith(_PREFIX))

    def test_e6_wrong_typed_input_is_safe_close_invalid_input(self) -> None:
        malformed_classifier = ClosePathDecision(close_path="cascade", reason="x")  # type: ignore[arg-type]
        malformed_engine = EngineSemanticsDecision(
            verdict="VERIFIED",  # type: ignore[arg-type]
            reason="x",
            probed_version="1.11.0",
            minor_line=(1, 11),
            probe_surface="cli",
            probed_commit=None,
        )
        for classifier, engine in (
            (None, self.verified),
            (self.cascade, None),
            ("cascade", self.verified),
            (self.cascade, "VERIFIED"),
            (self.verified, self.cascade),
            (malformed_classifier, self.verified),
            (self.cascade, malformed_engine),
        ):
            with self.subTest(classifier=classifier, engine=engine):
                path, reason = select_close_path(classifier, engine)  # type: ignore[arg-type]
                self.assertIs(path, ClosePath.SAFE_CLOSE)
                self.assertTrue(
                    reason.startswith("CLOSE_PATH_SELECTION_INVALID_INPUT"), reason
                )


class FlatModuleDocstringTests(unittest.TestCase):
    """196.003-T scenario E8: the module docstring states the flat sets."""

    def test_e8_docstring_states_flat_sets_without_linked_deliberation_union(self) -> None:
        doc = shipment_closure.__doc__ or ""
        self.assertIn("``allowed_ids(S)`` — ``closure_scope(S)``", doc)
        self.assertIn("``required_ids(S)``", doc)
        self.assertIn("x not truly archived pre-close", doc)
        self.assertNotIn("∪ validated_linked_deliberations(S)", doc)
        for pointer in (
            "assess_cascade_engine_semantics",
            "select_close_path",
            "compute_linked_deliberation_disposition",
        ):
            with self.subTest(pointer=pointer):
                self.assertIn(pointer, doc)


if __name__ == "__main__":
    unittest.main()

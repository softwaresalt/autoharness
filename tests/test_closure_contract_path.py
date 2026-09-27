"""Closure path builder: ID validation and workspace containment (167.010-T, U10).

Normative source: plan revision 5, "Contract Specification" item C4 and
requirements RQ-15 / RQ-17. Every fixture lives in a temporary scratch
workspace; ``docs/closure/`` in the committed tree is never touched (C6).
"""

from __future__ import annotations

import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from autoharness.gates.closure_contract import (
    CLOSURE_FEATURE_ID_PATTERN,
    CLOSURE_SHIPMENT_ID_PATTERN,
    RECOGNIZED_CLOSURE_PATTERNS,
    ClosureContractError,
    assert_path_within_workspace,
    build_closure_path,
    classify_closure_candidates,
    validate_closure_id,
)

_R1 = RECOGNIZED_CLOSURE_PATTERNS[0]

_ACCEPTED_PAIRS = (
    ("162-S", "154-F"),  # numeric ordinal
    ("A1b2-S", "Zz9-F"),  # alphanumeric ordinal
    ("7-S", "x-F"),  # single-character ordinal
    ("1234567890abcdefXYZ-S", "0987654321ABCDEFxyz-F"),  # long ordinal
)


@contextmanager
def _chdir(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _make_dir_link(link: Path, target: Path) -> str | None:
    """Create a directory symlink (or Windows junction). Return a skip reason on failure."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return None
    except (OSError, NotImplementedError) as exc:
        symlink_error = exc
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return None
        except (OSError, ImportError, AttributeError) as exc:  # pragma: no cover - platform
            return f"cannot create symlink ({symlink_error}) or junction ({exc})"
    return f"cannot create directory symlink: {symlink_error}"


class AcceptedDomainRoundTripTests(unittest.TestCase):
    """Scenario 1 -- accepted domain round-trip, both directions (RQ-17)."""

    def test_forward_builder_output_classifies_canonical_with_exact_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            closure_dir = root / "docs" / "closure"
            closure_dir.mkdir(parents=True)
            for shipment_id, feature_id in _ACCEPTED_PAIRS:
                with self.subTest(shipment_id=shipment_id, feature_id=feature_id):
                    path = build_closure_path(
                        "docs/closure", shipment_id, feature_id, workspace_root=root
                    )
                    path.write_text("", encoding="utf-8")
                    try:
                        match = _R1.match(path.name)
                        self.assertIsNotNone(match)
                        self.assertEqual(match.group("shipment_id"), shipment_id)
                        self.assertEqual(match.group("feature_id"), feature_id)
                        discovery = classify_closure_candidates(closure_dir, shipment_id)
                        self.assertEqual(discovery.canonical_matches, (path,))
                        self.assertEqual(discovery.outcome, "recognized")
                        # No builder output can ever match R2.
                        self.assertIsNone(RECOGNIZED_CLOSURE_PATTERNS[1].match(path.name))
                    finally:
                        path.unlink()

    def test_reverse_every_r1_capture_is_accepted_by_validator(self) -> None:
        names = [f"{s}-{f}-post-merge-closure.md" for s, f in _ACCEPTED_PAIRS]
        for name in names:
            with self.subTest(name=name):
                match = _R1.match(name)
                self.assertIsNotNone(match)
                self.assertEqual(
                    validate_closure_id(match.group("shipment_id"), field="shipment_id"),
                    match.group("shipment_id"),
                )
                self.assertEqual(
                    validate_closure_id(match.group("feature_id"), field="feature_id"),
                    match.group("feature_id"),
                )

    def test_accepted_domains_coincide(self) -> None:
        # Probe identifiers across the boundary: the validator's accepted set
        # and R1's captured set must be the same set.
        probes = (
            "162-S", "162-s", "16-2-S", "-162-S", "162-S-", "S", "162-", "１６２-S",
            "154-F", "154-f", "15-4-F", "a-F", "a b-F", "162-T",
        )
        for probe in probes:
            with self.subTest(probe=probe):
                for field, pattern, other in (
                    ("shipment_id", CLOSURE_SHIPMENT_ID_PATTERN, "154-F"),
                    ("feature_id", CLOSURE_FEATURE_ID_PATTERN, "162-S"),
                ):
                    try:
                        validate_closure_id(probe, field=field)
                        validator_accepts = True
                    except ClosureContractError:
                        validator_accepts = False
                    name = (
                        f"{probe}-{other}-post-merge-closure.md"
                        if field == "shipment_id"
                        else f"{other}-{probe}-post-merge-closure.md"
                    )
                    match = _R1.match(name)
                    r1_accepts = match is not None and match.group(field) == probe
                    self.assertEqual(validator_accepts, r1_accepts, field)
                    self.assertEqual(validator_accepts, bool(pattern.match(probe)), field)


class PathEscapeInputRejectionTests(unittest.TestCase):
    """Scenario 2 -- path-escape inputs are rejected, naming the field."""

    def test_path_escape_inputs_rejected(self) -> None:
        escapes = ("a/b", "a\\b", "..", ".", "../x", "/162-S", "C:162-S", "\\\\srv\\share")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for value in escapes:
                for field in ("shipment_id", "feature_id"):
                    with self.subTest(value=value, field=field):
                        with self.assertRaises(ClosureContractError) as ctx:
                            validate_closure_id(value, field=field)
                        self.assertIn(field, str(ctx.exception))
                        kwargs = {"shipment_id": "162-S", "feature_id": "154-F"}
                        kwargs[field] = value
                        with self.assertRaises(ClosureContractError) as build_ctx:
                            build_closure_path(
                                "docs/closure",
                                kwargs["shipment_id"],
                                kwargs["feature_id"],
                                workspace_root=root,
                            )
                        self.assertIn(field, str(build_ctx.exception))


class GrammarRejectTests(unittest.TestCase):
    """Scenario 3 -- grammar rejects name the field and the value."""

    def test_grammar_rejects(self) -> None:
        rows = (
            ("shipment_id", ""),
            ("shipment_id", "   "),
            ("shipment_id", "162\x00-S"),
            ("shipment_id", "162-S\n"),
            ("shipment_id", "-162-S"),
            ("shipment_id", "162-S-"),
            ("shipment_id", "162--S"),
            ("shipment_id", "16-2-S"),
            ("shipment_id", "162-s"),
            ("shipment_id", "162-F"),
            ("feature_id", "154-S"),
            ("feature_id", "154-f"),
            ("feature_id", "１５４-F"),
            ("shipment_id", "ü62-S"),
        )
        for field, value in rows:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ClosureContractError) as ctx:
                    validate_closure_id(value, field=field)
                message = str(ctx.exception)
                self.assertIn(field, message)
                self.assertIn(repr(value), message)

    def test_non_string_and_unknown_field_rejected(self) -> None:
        with self.assertRaises(ClosureContractError):
            validate_closure_id(162, field="shipment_id")  # type: ignore[arg-type]
        with self.assertRaises(ClosureContractError):
            validate_closure_id("162-S", field="task_id")


class WorkspaceAnchoringContainmentTests(unittest.TestCase):
    """Scenario 4 -- workspace anchoring and containment matrix (RQ-15).

    The whole scenario runs with the process CWD set to a directory OUTSIDE
    the workspace root, which is what makes the anchoring assertions meaningful.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "workspace"
        self.outside = base / "outside"
        self.cwd = base / "cwd"
        for directory in (self.root / "docs" / "closure", self.outside, self.cwd / "docs" / "closure"):
            directory.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _assert_rejected(self, closure_dir) -> None:
        with self.assertRaises(ClosureContractError) as ctx:
            build_closure_path(closure_dir, "162-S", "154-F", workspace_root=self.root)
        message = str(ctx.exception)
        self.assertIn(str(self.root), message)

    def test_relative_closure_dir_anchors_to_root_not_cwd(self) -> None:
        with _chdir(self.cwd):
            path = build_closure_path("docs/closure", "162-S", "154-F", workspace_root=self.root)
        self.assertTrue(path.is_relative_to(self.root))
        self.assertFalse(path.is_relative_to(self.cwd))
        self.assertEqual(path, self.root / "docs" / "closure" / "162-S-154-F-post-merge-closure.md")

    def test_absolute_in_root_accepted(self) -> None:
        with _chdir(self.cwd):
            path = build_closure_path(
                self.root / "docs" / "closure", "162-S", "154-F", workspace_root=self.root
            )
        self.assertEqual(path.parent, self.root / "docs" / "closure")

    def test_absolute_out_of_root_rejected(self) -> None:
        with _chdir(self.cwd):
            self._assert_rejected(self.outside)

    def test_relative_traversal_out_of_root_rejected(self) -> None:
        with _chdir(self.cwd):
            self._assert_rejected("../outside")
            self._assert_rejected("docs/../../outside")

    def test_in_root_symlink_staying_inside_accepted(self) -> None:
        link = self.root / "closure-link"
        reason = _make_dir_link(link, self.root / "docs" / "closure")
        if reason:
            self.skipTest(reason)
        with _chdir(self.cwd):
            path = build_closure_path("closure-link", "162-S", "154-F", workspace_root=self.root)
        self.assertTrue(path.is_relative_to(self.root))
        self.assertEqual(path.parent, (self.root / "docs" / "closure").resolve())

    def test_in_root_symlink_escaping_root_rejected(self) -> None:
        link = self.root / "escape-link"
        reason = _make_dir_link(link, self.outside)
        if reason:
            self.skipTest(reason)
        with _chdir(self.cwd):
            self._assert_rejected("escape-link")

    def test_output_path_outside_root_rejected(self) -> None:
        # A symlink occupying the canonical output name, pointing outside the
        # root, makes the resolved output land outside the root.
        closure_dir = self.root / "docs" / "closure"
        link = closure_dir / "162-S-154-F-post-merge-closure.md"
        reason = _make_dir_link(link, self.outside)
        if reason:
            self.skipTest(reason)
        with _chdir(self.cwd):
            self._assert_rejected("docs/closure")

    def test_assert_path_within_workspace_primitive(self) -> None:
        with _chdir(self.cwd):
            inside = assert_path_within_workspace("docs/closure", workspace_root=self.root)
            self.assertEqual(inside, (self.root / "docs" / "closure").resolve())
            with self.assertRaises(ClosureContractError) as ctx:
                assert_path_within_workspace(self.outside / "x.md", workspace_root=self.root)
            self.assertIn(str(self.root), str(ctx.exception))
            self.assertIn("x.md", str(ctx.exception))

    def test_builder_never_creates_directories(self) -> None:
        with _chdir(self.cwd):
            path = build_closure_path("not-yet/closure", "162-S", "154-F", workspace_root=self.root)
        self.assertFalse(path.parent.exists())
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()

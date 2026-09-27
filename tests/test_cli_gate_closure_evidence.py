"""CLI tests for `autoharness gate closure-evidence` (167.004-T U4, 167.011-T U11).

Write-time validation of a post-merge closure artifact against the
closure-evidence naming contract. Every fixture lives in a temporary scratch
workspace; canonical names come from ``build_closure_path`` and legacy names
from ``tests/_closure_legacy_names.py`` (plan C6).
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from _closure_legacy_names import legacy_closure_filename
from autoharness.cli import main
from autoharness.gates.closure_contract import (
    CANONICAL_CLOSURE_PATTERN_DOC,
    build_closure_path,
)

_READY = "---\ncompaction_status: done\nclosure_status: READY\n---\n"


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


def _run_json(*argv: str) -> tuple[dict, int | None]:
    out, _err, code = _run(*argv, "--json")
    return json.loads(out), code


def _make_dir_link(link: Path, target: Path) -> str | None:
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


class _ClosureWorkspaceMixin:
    def setUp(self) -> None:  # noqa: D401 - unittest hook
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "workspace"
        self.outside = base / "outside"
        self.closure_dir = self.root / "docs" / "closure"
        self.closure_dir.mkdir(parents=True)
        self.outside.mkdir()

    def tearDown(self) -> None:  # noqa: D401 - unittest hook
        self._tmp.cleanup()

    def _canonical(self, shipment_id: str = "175-S", feature_id: str = "167-F", body: str = _READY) -> Path:
        path = build_closure_path("docs/closure", shipment_id, feature_id, workspace_root=self.root)
        path.write_text(body, encoding="utf-8")
        return path

    def _gate(self, path: Path | str, *extra: str) -> tuple[dict, int | None]:
        return _run_json(
            "gate", "closure-evidence", "--path", str(path), "--workspace", str(self.root), *extra
        )


class ClosureEvidenceCliTests(_ClosureWorkspaceMixin, unittest.TestCase):
    def test_help_lists_closure_evidence(self) -> None:
        out, _, _ = _run("gate", "--help")
        self.assertIn("closure-evidence", out)
        out, _, code = _run("gate", "closure-evidence", "--help")
        self.assertIn("--path", out)
        self.assertIn(code, (0, None))

    def test_canonical_acceptable_artifact_passes(self) -> None:
        path = self._canonical()
        payload, code = self._gate(path, "--shipment", "175-S")
        self.assertIn(code, (0, None))
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["exit_code"], 0)
        self.assertIsNone(payload["failed_check"])
        self.assertEqual(payload["shipment_id"], "175-S")
        # Human-readable form also passes.
        out, _, human_code = _run(
            "gate", "closure-evidence", "--path", str(path), "--workspace", str(self.root)
        )
        self.assertIn(human_code, (0, None))
        self.assertIn("PASS", out)

    def test_legacy_filename_fails_write_time_with_canonical_pattern(self) -> None:
        legacy = self.closure_dir / legacy_closure_filename("175-s", "167-f")
        legacy.write_text(_READY, encoding="utf-8")
        payload, code = self._gate(legacy)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "filename")
        self.assertIn(CANONICAL_CLOSURE_PATTERN_DOC, payload["message"])
        self.assertIn(legacy.name, payload["message"])

    def test_absent_or_unparseable_path_is_invalid_input(self) -> None:
        missing = self.closure_dir / "175-S-167-F-post-merge-closure.md"
        payload, code = self._gate(missing)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn(str(missing), payload["message"])

        unparseable = self._canonical(body="---\nclosure_status: [unterminated\n---\n")
        payload, code = self._gate(unparseable)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")
        self.assertIn(str(unparseable), payload["message"])

        no_frontmatter = self._canonical(shipment_id="176-S", body="no frontmatter here\n")
        payload, code = self._gate(no_frontmatter)
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")

    def test_path_outside_workspace_is_rejected_before_other_checks(self) -> None:
        outside_file = self.outside / "175-S-167-F-post-merge-closure.md"
        outside_file.write_text(_READY, encoding="utf-8")
        rows = [
            ("absolute out-of-root", str(outside_file)),
            ("traversal", "../outside/175-S-167-F-post-merge-closure.md"),
        ]
        link = self.root / "docs" / "escape-link"
        reason = _make_dir_link(link, self.outside)
        for label, path in rows:
            with self.subTest(row=label):
                payload, code = self._gate(path)
                self.assertEqual(code, 2)
                self.assertEqual(payload["failed_check"], "workspace")
                self.assertIn(str(self.root), payload["message"])
                self.assertIn("175-S-167-F-post-merge-closure.md", payload["message"])
        with self.subTest(row="symlink/junction escaping root"):
            if reason:
                self.skipTest(reason)
            payload, code = self._gate(link / "175-S-167-F-post-merge-closure.md")
            self.assertEqual(code, 2)
            self.assertEqual(payload["failed_check"], "workspace")
            self.assertIn(str(self.root), payload["message"])

    def test_json_failed_check_discriminator(self) -> None:
        legacy = self.closure_dir / legacy_closure_filename("175-s", "167-f")
        legacy.write_text(_READY, encoding="utf-8")
        rejected = self._canonical(
            shipment_id="177-S", body="---\ncompaction_status: done\nclosure_status: BLOCKED\n---\n"
        )
        foreign = self._canonical(shipment_id="178-S")
        rows = (
            ("workspace", self.outside / "x.md", (), 2),
            ("input", self.closure_dir / "missing.md", (), 2),
            ("filename", legacy, (), 1),
            ("frontmatter_predicate", rejected, (), 1),
            ("discoverability", foreign, ("--shipment", "179-S"), 1),
            (None, self._canonical(), (), 0),
        )
        for failed_check, path, extra, exit_code in rows:
            with self.subTest(failed_check=failed_check):
                payload, code = self._gate(path, *extra)
                self.assertEqual(payload["failed_check"], failed_check)
                self.assertEqual(payload["exit_code"], exit_code)
                self.assertEqual(code if code is not None else 0, exit_code)
                self.assertIn("path", payload)

    def test_missing_path_argument_is_invalid(self) -> None:
        _out, err, code = _run("gate", "closure-evidence", "--workspace", str(self.root))
        self.assertEqual(code, 2)
        self.assertIn("--path", err)
        _out, err, code = _run("gate", "closure-evidence", "--path", "x", "--bogus")
        self.assertEqual(code, 2)

    def test_invalid_declared_shipment_is_invalid_input(self) -> None:
        payload, code = self._gate(self._canonical(), "--shipment", "175-s")
        self.assertEqual(code, 2)
        self.assertEqual(payload["failed_check"], "input")

    def test_artifact_outside_consumer_closure_dir_is_not_discoverable(self) -> None:
        elsewhere = self.root / "other"
        elsewhere.mkdir()
        path = build_closure_path("other", "175-S", "167-F", workspace_root=self.root)
        path.write_text(_READY, encoding="utf-8")
        payload, code = self._gate(path)
        self.assertEqual(code, 1)
        self.assertEqual(payload["failed_check"], "discoverability")


if __name__ == "__main__":
    unittest.main()

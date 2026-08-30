"""Report-emitter tests for pre-review detector results (149.007-T / 149.014-T)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from autoharness.detectors.contract import NodeResult
from autoharness.detectors.report import (
    InvalidCommitShaError,
    emit_pre_review_report,
    report_path_for,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"


class ReportTests(unittest.TestCase):
    def _result(self) -> NodeResult:
        return NodeResult(name="det:D-ART/ART-01@1", status="passed", details={"artifact_count": 1})

    def test_report_is_flat_list_without_topology_data(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            emission = emit_pre_review_report(
                [self._result()],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:00Z",
            )

            payload = json.loads(emission.path.read_text(encoding="utf-8"))
            self.assertIsInstance(payload, list)
            self.assertEqual(payload[0]["name"], "det:D-ART/ART-01@1")
            self.assertNotIn("edges", payload[0])
            self.assertNotIn("depends_on", payload[0])

    def test_same_epoch_key_write_is_no_clobber(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            first = emit_pre_review_report(
                [self._result()],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:00Z",
            )
            before_bytes = first.path.read_bytes()
            before_mtime = first.path.stat().st_mtime_ns

            second = emit_pre_review_report(
                [self._result()],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:01Z",
            )
            self.assertFalse(second.wrote_new)
            self.assertEqual(before_bytes, first.path.read_bytes())
            self.assertEqual(before_mtime, first.path.stat().st_mtime_ns)

    def test_stale_head_sha_is_structurally_rejected_by_key_mismatch(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            old_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
            )
            current_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="c" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
            )
            self.assertNotEqual(old_path, current_path)
            self.assertFalse(current_path.exists())

    def test_changed_tool_version_is_structurally_rejected_by_key_mismatch(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            old_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
            )
            current_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.13.0"},
            )
            self.assertNotEqual(old_path, current_path)
            self.assertFalse(current_path.exists())

    def test_changed_base_sha_is_structurally_rejected_by_key_mismatch(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            old_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
            )
            current_path = report_path_for(
                workspace,
                base_sha="d" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
            )
            self.assertNotEqual(
                old_path,
                current_path,
                "a different --base (changing modified_paths/applicability) must mint a fresh epoch key",
            )
            self.assertFalse(current_path.exists())

    def test_changed_autoharness_version_is_structurally_rejected_by_key_mismatch(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            old_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                autoharness_version="1.9.0",
            )
            current_path = report_path_for(
                workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                autoharness_version="1.9.1",
            )
            self.assertNotEqual(
                old_path,
                current_path,
                "an upgraded installed autoharness version must mint a fresh epoch key even at a fixed HEAD",
            )
            self.assertFalse(current_path.exists())

    def test_publication_failure_is_reported_not_raised_on_temp_write_error(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            # A file occupying the parent directory path makes mkdir(parents=True) raise
            # NotADirectoryError/FileExistsError (both OSError subclasses) rather than the
            # narrower FileExistsError previously handled only around os.link.
            blocker = workspace / ".autoharness" / "gates"
            blocker.parent.mkdir(parents=True, exist_ok=True)
            blocker.write_text("not a directory", encoding="utf-8")

            emission = emit_pre_review_report(
                [self._result()],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:00Z",
            )
            self.assertTrue(emission.publication_failed)
            self.assertFalse(emission.wrote_new)
            self.assertIn("pre-review report publish unavailable", emission.message)

    def test_head_sha_path_traversal_is_rejected(self) -> None:
        # Copilot review finding (PR #420): `head_sha` becomes part of a
        # filesystem path without validation in `compute_epoch_key`, so a
        # direct SDK caller (not only the CLI, which already resolves refs
        # through `git rev-parse`) could supply `../` traversal or an
        # absolute-path-like string and redirect the report write outside
        # `workspace`. Both public path helpers route through
        # `compute_epoch_key`, so validating there contains both.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            for unsafe_head_sha in ("../../etc/passwd", "/absolute/escape", "b" * 40 + "/../evil"):
                with self.assertRaises(InvalidCommitShaError):
                    report_path_for(
                        workspace,
                        base_sha="a" * 40,
                        head_sha=unsafe_head_sha,
                        registry_version="registry-v1",
                        schema_version="1.0.0",
                        tool_versions={"python": "3.12.10"},
                    )
                with self.assertRaises(InvalidCommitShaError):
                    emit_pre_review_report(
                        [self._result()],
                        workspace=workspace,
                        base_sha="a" * 40,
                        head_sha=unsafe_head_sha,
                        registry_version="registry-v1",
                        schema_version="1.0.0",
                        tool_versions={"python": "3.12.10"},
                        touches_reviewable_paths=True,
                        produced_at="2026-08-29T00:00:00Z",
                    )
            # Confirm nothing escaped workspace: only the tempdir itself exists.
            self.assertEqual(list(workspace.iterdir()), [])

    def test_publish_refuses_symlinked_publication_directory_escape(self) -> None:
        # Copilot review finding (PR #420): the writer follows existing
        # directories without checking their resolved location. A target
        # repository can make `.autoharness` (or `gates`) a symlink to an
        # external directory, causing this report-only command to create
        # the temp and final files outside `workspace`. Resolve and
        # validate the publication directory against `workspace.resolve()`
        # before creating or opening files, rejecting the symlink escape.
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as outside_tmp, tempfile.TemporaryDirectory(
            dir=_TEMP_ROOT
        ) as workspace_tmp:
            outside = Path(outside_tmp)
            workspace = Path(workspace_tmp)
            os.symlink(str(outside), str(workspace / ".autoharness"), target_is_directory=True)

            emission = emit_pre_review_report(
                [self._result()],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:00Z",
            )
            self.assertTrue(emission.publication_failed)
            self.assertFalse(emission.wrote_new)
            self.assertIn("resolves outside workspace", emission.message)
            # Nothing must have been written into the symlink target.
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()

"""Epoch-key determinism and concurrency tests for detector reports (149.015-T)."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from autoharness.detectors.contract import NodeResult
from autoharness.detectors.report import (
    build_freshness_fingerprint,
    emit_pre_review_report,
    report_path_for,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"


class ReportEpochTests(unittest.TestCase):
    def _result(self, produced_at: str) -> NodeResult:
        return NodeResult(
            name="det:D-ART/ART-01@1",
            status="passed",
            provenance={"produced_at_marker": produced_at},
        )

    def test_fingerprint_is_deterministic_across_input_orderings(self) -> None:
        first = build_freshness_fingerprint(
            registry_version="registry-v1",
            schema_version="1.0.0",
            tool_versions={"python": "3.12.10", "git": "2.49.0"},
        )
        second = build_freshness_fingerprint(
            registry_version="registry-v1",
            schema_version="1.0.0",
            tool_versions={"git": "2.49.0", "python": "3.12.10"},
        )
        third = build_freshness_fingerprint(
            registry_version="registry-v1",
            schema_version="1.0.0",
            tool_versions={"git": "2.50.0", "python": "3.12.10"},
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_rerun_at_same_head_with_tool_version_change_writes_new_file(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            first = emit_pre_review_report(
                [self._result("first")],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:00Z",
            )
            second = emit_pre_review_report(
                [self._result("second")],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.13.0"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:01Z",
            )
            self.assertNotEqual(first.path, second.path)
            self.assertTrue(first.path.exists())
            self.assertTrue(second.path.exists())

    def test_stale_sibling_is_never_selected_as_current_report(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            stale = emit_pre_review_report(
                [self._result("stale")],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:00Z",
            )
            current = report_path_for(
                workspace,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.13.0"},
            )
            self.assertTrue(stale.path.exists())
            self.assertNotEqual(stale.path, current)
            self.assertFalse(current.exists())

    def test_concurrent_same_key_writes_publish_one_whole_payload_and_never_clobber(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            barrier = threading.Barrier(3)
            emissions = []
            errors = []

            def writer(label: str, produced_at: str) -> None:
                try:
                    barrier.wait(timeout=5)
                    emission = emit_pre_review_report(
                        [self._result(label)],
                        workspace=workspace,
                        base_sha="a" * 40,
                        head_sha="b" * 40,
                        registry_version="registry-v1",
                        schema_version="1.0.0",
                        tool_versions={"python": "3.12.10"},
                        touches_reviewable_paths=True,
                        produced_at=produced_at,
                    )
                    emissions.append(emission)
                except Exception as exc:  # pragma: no cover - failure path assertion below
                    errors.append(exc)

            first_thread = threading.Thread(target=writer, args=("first", "2026-08-29T00:00:00Z"))
            second_thread = threading.Thread(target=writer, args=("second", "2026-08-29T00:00:01Z"))
            first_thread.start()
            second_thread.start()
            barrier.wait(timeout=5)
            first_thread.join(timeout=5)
            second_thread.join(timeout=5)

            self.assertEqual(errors, [])
            self.assertEqual(len(emissions), 2)
            published = report_path_for(
                workspace,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
            )
            published_bytes = published.read_bytes()
            self.assertIn(published_bytes, {emissions[0].payload_bytes, emissions[1].payload_bytes})

            before_bytes = published_bytes
            before_mtime = published.stat().st_mtime_ns
            third = emit_pre_review_report(
                [self._result("third")],
                workspace=workspace,
                base_sha="a" * 40,
                head_sha="b" * 40,
                registry_version="registry-v1",
                schema_version="1.0.0",
                tool_versions={"python": "3.12.10"},
                touches_reviewable_paths=True,
                produced_at="2026-08-29T00:00:02Z",
            )
            self.assertFalse(third.wrote_new)
            self.assertEqual(before_bytes, published.read_bytes())
            self.assertEqual(before_mtime, published.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()

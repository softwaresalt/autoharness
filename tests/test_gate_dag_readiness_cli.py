"""CLI tests for `autoharness gate dag-readiness` (110.003-T, 117-S).

Mirrors the pipeline-topology CLI wiring pattern: parse -> reader ->
evaluate -> render (human/--json). Read-only; existence-guarded; degrades
non-fatally (advisory) when backlogit is unreachable.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from autoharness.cli import main
from autoharness.gates.topology import BacklogUnavailableError, ShipmentState


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


def _shipment(shipment_id: str, status: str | None, *, archived_status: str | None = None, deps=()) -> ShipmentState:
    return ShipmentState(
        shipment_id=shipment_id,
        title=shipment_id,
        live_status=status,
        archived_status=archived_status,
        archived_record_present=archived_status is not None,
        manifest_item_ids=(),
        blocking_predecessor_ids=tuple(deps),
    )


class _FakeReaders:
    def __init__(self, shipments=()):
        self._shipments = tuple(shipments)

    def list_shipments(self):
        return self._shipments


class _UnavailableReaders:
    def list_shipments(self):
        raise BacklogUnavailableError(__import__("pathlib").Path(".backlogit"), "backlog directory is unavailable")


class DagReadinessHelpTests(unittest.TestCase):
    def test_gate_help_lists_dag_readiness(self) -> None:
        out, _, _ = _run("gate", "--help")
        self.assertIn("dag-readiness", out)

    def test_dag_readiness_help(self) -> None:
        out, _, _ = _run("gate", "dag-readiness", "--help")
        self.assertIn("dag-readiness", out)
        self.assertIn("--json", out)


class DagReadinessArgTests(unittest.TestCase):
    def test_unknown_flag_exits_2(self) -> None:
        _, _, code = _run("gate", "dag-readiness", "--bogus")
        self.assertEqual(code, 2)


class DagReadinessExistenceGuardTests(unittest.TestCase):
    def test_zero_shipments_yields_empty_report_exit_0(self) -> None:
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(())
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["ready_set"], [])
        self.assertEqual(payload["critical_path"], [])
        self.assertEqual(payload["downstream_dependents"], {})
        self.assertEqual(payload["status"], "empty")


class DagReadinessHumanAndJsonRenderTests(unittest.TestCase):
    def test_human_report_renders_ready_set_and_critical_path(self) -> None:
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness")
        self.assertEqual(code, 0)
        self.assertIn("002-S", out)
        self.assertIn("001-S", out)

    def test_json_report_matches_a1_reader_shape(self) -> None:
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["ready_set"], ["002-S"])
        self.assertEqual(payload["critical_path"], ["001-S", "002-S"])
        self.assertEqual(payload["status"], "ok")

    def test_render_regression_active_predecessor_blocks_queued_dependent(self) -> None:
        # REGRESSION (matches A1/110.001-T): a LIVE queued dependent with an
        # active predecessor must NOT be rendered as ready.
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["ready_set"], [])
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            human_out, _, human_code = _run("gate", "dag-readiness")
        self.assertEqual(human_code, 0)
        self.assertIn("ready-set: (none)", human_out)

    def test_cycle_detected_degrades_render_without_fabricating_ready_set(self) -> None:
        shipments = (
            _shipment("001-S", "queued", deps=("002-S",)),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["cycle_detected"])
        self.assertEqual(payload["ready_set"], [])
        self.assertEqual(payload["critical_path"], [])


class DagReadinessDegradedTests(unittest.TestCase):
    def test_backlog_unavailable_reports_degraded_and_exits_non_fatally(self) -> None:
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_UnavailableReaders()
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "degraded")
        self.assertIn("degraded_reason", payload)
        self.assertIsNotNone(payload["degraded_reason"])

    def test_backlog_unavailable_human_report_says_degraded(self) -> None:
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_UnavailableReaders()
        ):
            out, _, code = _run("gate", "dag-readiness")
        self.assertEqual(code, 0)
        self.assertIn("DEGRADED", out)


class DagReadinessStorageRootResolutionTests(unittest.TestCase):
    def _write_minimal_backlog_root(self, root: Path) -> None:
        (root / "queue").mkdir(parents=True)
        (root / "archive").mkdir(parents=True)

    def test_backlog_only_workspace_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / ".backlog")

            out, err, code = _run("gate", "dag-readiness", "--workspace", str(workspace), "--json")

        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(payload["status"], "empty")
        self.assertIsNone(payload["degraded_reason"])

    def test_both_roots_present_reports_degraded_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / ".backlog")
            self._write_minimal_backlog_root(workspace / ".backlogit")

            out, err, code = _run("gate", "dag-readiness", "--workspace", str(workspace), "--json")

        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "degraded")
        self.assertIn("multiple backlog directories are present", payload["degraded_reason"])

    def test_missing_override_reports_degraded_without_fallthrough(self) -> None:
        # ".backlogit" is a valid literal candidate name (accepted by the strict
        # override validator) that simply does not exist as a directory here --
        # this exercises the missing-directory-after-a-valid-override path,
        # distinct from a non-literal override value (covered elsewhere).
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / ".backlog")
            with mock.patch.dict(os.environ, {"BACKLOGIT_WORKSPACE_DIR": ".backlogit"}):
                out, err, code = _run("gate", "dag-readiness", "--workspace", str(workspace), "--json")

        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "degraded")
        self.assertIn("configured backlog directory is unavailable", payload["degraded_reason"])


class DagReadinessNextEligibleFieldsTests(unittest.TestCase):
    """AC1/AC10 (115.002-T): the three next_eligible* fields are emitted
    unconditionally, identically shaped across ok/empty/cycle/degraded
    paths, and on non-degraded paths are taken verbatim from
    compute_next_eligible(...).to_dict()."""

    def test_ok_path_includes_next_eligible_fields_from_analyzer(self) -> None:
        shipments = (_shipment("001-S", "queued"),)
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["next_eligible"], "001-S")
        self.assertEqual(payload["next_eligible_reason"], "ready_set_head")
        self.assertEqual(
            payload["next_eligible_detail"], {"candidate_ids": ["001-S"], "offending_ids": []}
        )

    def test_empty_path_includes_no_candidates_reason(self) -> None:
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(())
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertIsNone(payload["next_eligible"])
        self.assertEqual(payload["next_eligible_reason"], "no_candidates")
        self.assertEqual(
            payload["next_eligible_detail"], {"candidate_ids": [], "offending_ids": []}
        )

    def test_cycle_path_includes_cycle_detected_reason_with_empty_detail(self) -> None:
        shipments = (
            _shipment("001-S", "queued", deps=("002-S",)),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertIsNone(payload["next_eligible"])
        self.assertEqual(payload["next_eligible_reason"], "cycle_detected")
        self.assertEqual(payload["next_eligible_detail"]["candidate_ids"], [])
        # offending_ids is populated ONLY for multi_active_anomaly and
        # ambiguous_provenance per the normative detail-shape contract; the
        # cycle's participating nodes are already surfaced via the Phase 1
        # cycle_nodes field.
        self.assertEqual(payload["next_eligible_detail"]["offending_ids"], [])

    def test_multi_active_anomaly_reported_but_exit_code_still_zero(self) -> None:
        shipments = (
            _shipment("001-S", "active"),
            _shipment("002-S", "active"),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertIsNone(payload["next_eligible"])
        self.assertEqual(payload["next_eligible_reason"], "multi_active_anomaly")
        self.assertEqual(payload["next_eligible_detail"]["offending_ids"], ["001-S", "002-S"])

    def test_ok_path_preserves_existing_phase1_fields_unchanged(self) -> None:
        # H6: a consumer that ignores the three new fields still parses the
        # payload unchanged. Every Phase 1 field keeps its exact name, type,
        # and meaning.
        shipments = (
            _shipment("001-S", "shipped"),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        payload = json.loads(out)
        self.assertEqual(payload["ready_set"], ["002-S"])
        self.assertEqual(payload["critical_path"], ["001-S", "002-S"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["cycle_detected"], False)
        self.assertEqual(payload["cycle_nodes"], [])
        self.assertIn("downstream_dependents", payload)
        self.assertIn("degraded_reason", payload)

    def test_human_report_adds_at_most_one_next_eligible_line(self) -> None:
        shipments = (_shipment("001-S", "queued"),)
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness")
        self.assertEqual(code, 0)
        next_eligible_lines = [line for line in out.splitlines() if "next eligible" in line]
        self.assertEqual(len(next_eligible_lines), 1)
        self.assertIn("001-S", next_eligible_lines[0])
        self.assertIn("ready_set_head", next_eligible_lines[0])

    def test_human_report_renders_next_eligible_line_on_cycle_path(self) -> None:
        shipments = (
            _shipment("001-S", "queued", deps=("002-S",)),
            _shipment("002-S", "queued", deps=("001-S",)),
        )
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_FakeReaders(shipments)
        ):
            out, _, code = _run("gate", "dag-readiness")
        self.assertEqual(code, 0)
        next_eligible_lines = [line for line in out.splitlines() if "next eligible" in line]
        self.assertEqual(len(next_eligible_lines), 1)
        self.assertIn("cycle_detected", next_eligible_lines[0])
        self.assertIn("(none)", next_eligible_lines[0])


class DagReadinessDegradedNextEligibleTests(unittest.TestCase):
    """AC5/AC9 (115.002-T): degraded outcome is CLI-exclusive, synthesized
    literally WITHOUT invoking compute_next_eligible, with the exact
    two-empty-array detail shape."""

    def test_degraded_next_eligible_detail_is_exactly_two_empty_arrays(self) -> None:
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_UnavailableReaders()
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertIsNone(payload["next_eligible"])
        self.assertEqual(payload["next_eligible_reason"], "degraded")
        self.assertEqual(
            payload["next_eligible_detail"], {"candidate_ids": [], "offending_ids": []}
        )

    def test_degraded_path_never_invokes_the_analyzer(self) -> None:
        with (
            mock.patch(
                "autoharness.gates.topology.FilesystemTopologyReaders",
                return_value=_UnavailableReaders(),
            ),
            mock.patch("autoharness.gates.topology.compute_next_eligible") as mocked_analyzer,
        ):
            out, _, code = _run("gate", "dag-readiness", "--json")
        self.assertEqual(code, 0)
        mocked_analyzer.assert_not_called()
        payload = json.loads(out)
        self.assertEqual(payload["next_eligible_reason"], "degraded")

    def test_degraded_human_report_renders_next_eligible_none_degraded(self) -> None:
        with mock.patch(
            "autoharness.gates.topology.FilesystemTopologyReaders", return_value=_UnavailableReaders()
        ):
            out, _, code = _run("gate", "dag-readiness")
        self.assertEqual(code, 0)
        self.assertIn("DEGRADED", out)
        next_eligible_lines = [line for line in out.splitlines() if "next eligible" in line]
        self.assertEqual(len(next_eligible_lines), 1)
        self.assertIn("(none)", next_eligible_lines[0])
        self.assertIn("degraded", next_eligible_lines[0])


if __name__ == "__main__":
    unittest.main()

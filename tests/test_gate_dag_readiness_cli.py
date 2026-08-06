"""CLI tests for `autoharness gate dag-readiness` (110.003-T, 117-S).

Mirrors the pipeline-topology CLI wiring pattern: parse -> reader ->
evaluate -> render (human/--json). Read-only; existence-guarded; degrades
non-fatally (advisory) when backlogit is unreachable.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
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


if __name__ == "__main__":
    unittest.main()

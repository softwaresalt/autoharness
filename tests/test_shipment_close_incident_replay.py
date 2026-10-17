"""Incident replay for ``cascade-close`` (211.016-T, plan unit T16; hardening H1).

The wrapper (the detached supervisor and its engine child) is really killed mid-``shipment ship``, after the fake engine
archived the closure scope and before anything was reported. The test then walks the operator path the incident needed:
the journal survived, ``--poll`` reports the orphan, ``--recover --dry-run`` and ``--recover`` produce a record that
passes the pass-only validator and the closure-evidence gate, the stale lock leaves a tombstone, and a second recovery
is refused as already finalized.
"""

from __future__ import annotations

import io
import json
import os
import signal
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from test_cli_gate_closure_evidence import (
    _READY,
    evidence_relpath,
    with_close_keys,
)
from test_shipment_cascade_close_detach import _DetachHarness
from test_shipment_cascade_close_invoke import _FEATURE, _SHA, _SHIPMENT, _VERIFIED
from test_shipment_close_recover_reconstruct import _Recovery

from autoharness import cli
from autoharness.gates.cascade_evidence import validate_evidence_record
from autoharness.gates.closure_contract import build_closure_path
from autoharness.gates.topology import FilesystemTopologyReaders
from autoharness.shipment_close import EXIT_INPUT, EXIT_LOCKED, EXIT_OK, EXIT_STARTED
from autoharness.shipment_close.poll import poll_cascade_close
from autoharness.shipment_close.recover import (
    RecoverOptions,
    list_processes,
    recover_cascade_close,
)

# The re-probe is slow enough that captured_at precedes started_at by a whole second (the validator's strict ordering).
_PROBES = [_VERIFIED, {**_VERIFIED, "sleep": 1.2}]


def _workspace_processes(root: Path) -> list[int]:
    return [
        pid
        for pid, command_line in (list_processes() or [])
        if str(root) in command_line and pid != os.getpid()
    ]


def _kill(pids: list[int]) -> None:
    for pid in pids:
        try:
            os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
        except (ProcessLookupError, PermissionError, OSError):
            pass


class IncidentReplayTests(unittest.TestCase):
    def _wait(self, predicate, message: str, timeout: float = 60.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.1)
        self.fail(message)

    def _kill_wrapper_mid_ship(self) -> _DetachHarness:
        harness = _DetachHarness(self, sleep=300.0)
        harness.set_control(probes=_PROBES)
        self.addCleanup(lambda: _kill(_workspace_processes(harness.root)))
        started = harness.detach()
        self.assertEqual(started.exit_code, EXIT_STARTED, started.message)
        self._wait(
            lambda: harness.shipped, "the fake engine never started the ship call"
        )
        self._wait(
            lambda: (harness.directory / "child_started.json").exists(),
            "the child-start marker was never written",
        )
        _kill(_workspace_processes(harness.root))
        self._wait(
            lambda: not _workspace_processes(harness.root),
            "the killed wrapper is still running",
        )
        return harness

    def _gate(self, harness: _DetachHarness) -> tuple[dict, int | None]:
        (harness.root / "docs" / "closure").mkdir(parents=True, exist_ok=True)
        body = with_close_keys(
            _READY, "cascade", evidence_relpath(_SHIPMENT, _FEATURE), merge_commit=_SHA
        )
        path = build_closure_path(
            "docs/closure", _SHIPMENT, _FEATURE, workspace_root=harness.root
        )
        path.write_text(body, encoding="utf-8")
        argv = [
            "gate",
            "closure-evidence",
            "--path",
            str(path),
            "--workspace",
            str(harness.root),
            "--json",
        ]
        out, err = io.StringIO(), io.StringIO()
        code: int | None = 0
        committed = datetime(2026, 10, 1, 23, 0, tzinfo=timezone.utc)
        with mock.patch.object(cli, "_merge_committer_time", return_value=committed):
            try:
                with redirect_stdout(out), redirect_stderr(err):
                    cli.main(argv)
            except SystemExit as exc:
                code = exc.code
        return json.loads(out.getvalue()), code

    def test_a_wrapper_killed_mid_ship_is_recovered_to_gate_valid_evidence(
        self,
    ) -> None:
        harness = self._kill_wrapper_mid_ship()
        self.assertTrue(harness.directory.is_dir(), "the journal survived the kill")
        self.assertFalse((harness.directory / "outcome.json").exists())
        self.assertEqual(harness.record()["phase"], "invoking")
        self.assertTrue(
            harness.lock_path.exists(), "the killed wrapper left its pair lock behind"
        )

        polled = poll_cascade_close(harness.root, _SHIPMENT, _FEATURE)
        self.assertEqual(polled.exit_code, EXIT_LOCKED, polled.message)
        self.assertTrue(polled.recovery_available)

        _Recovery.write_logs(
            harness
        )  # engine event log provenance for the archived footprint
        options: dict[str, float] = {}
        before = (harness.evidence.read_bytes(), harness.lock_path.read_bytes())
        dry = recover_cascade_close(
            harness.root,
            _SHIPMENT,
            _FEATURE,
            options=RecoverOptions(dry_run=True, **options),
        )
        self.assertEqual(dry.exit_code, EXIT_OK, dry.message)
        self.assertTrue(dry.dry_run)
        self.assertFalse(dry.recovered)
        self.assertEqual(
            (harness.evidence.read_bytes(), harness.lock_path.read_bytes()),
            before,
            "--dry-run writes nothing",
        )

        ship_calls = len([argv for argv in harness.argv_log() if "ship" in argv])
        outcome = recover_cascade_close(
            harness.root, _SHIPMENT, _FEATURE, options=RecoverOptions(**options)
        )
        self.assertEqual(
            outcome.exit_code, EXIT_OK, (outcome.message, outcome.failures)
        )
        self.assertTrue(outcome.recovered)
        self.assertIn(outcome.recovery_mode, ("journal_partial", "postconditions_only"))
        self.assertEqual(
            len([argv for argv in harness.argv_log() if "ship" in argv]),
            ship_calls,
            "recovery never re-runs the engine",
        )

        record = harness.record()
        self.assertEqual(record["phase"], "post_close")
        self.assertEqual(record["recovery"]["recovered"], True)
        self.assertEqual(
            validate_evidence_record(
                record, shipment_id=_SHIPMENT, feature_id=_FEATURE, close_path="cascade"
            ),
            [],
        )
        self.assertFalse(harness.lock_path.exists())
        tombstones = [
            name for name in os.listdir(harness.lock_path.parent) if ".stale-" in name
        ]
        self.assertEqual(
            len(tombstones), 1, "the stale lock leaves exactly one tombstone"
        )

        payload, code = self._gate(harness)
        self.assertIn(code, (0, None), payload)
        self.assertIs(payload["evidence_recovered"], True)
        self.assertTrue(
            FilesystemTopologyReaders(harness.root).closure_complete(_SHIPMENT) is True
        )

        again = recover_cascade_close(
            harness.root, _SHIPMENT, _FEATURE, options=RecoverOptions(**options)
        )
        self.assertEqual(again.exit_code, EXIT_INPUT, again.message)
        self.assertIn("already finalized", again.message)


if __name__ == "__main__":
    unittest.main()

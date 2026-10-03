"""Composed producer/consumer state-machine tests (167.007-T, plan U7 / D7).

Binding construction rule: every canonical closure filename is obtained from
``build_closure_path(...)`` -- exactly as the producer documentation directs --
and every legacy (R2) filename from the single test-only helper
``tests/_closure_legacy_names.py::legacy_closure_filename`` (plan C6). A
hand-written canonical literal here would be a defect: such a fixture would
have passed throughout all six historical occurrences of the drift this
feature repairs.

Each scenario drives the REAL write-time gate (``autoharness gate
closure-evidence``) where the producer would, and the REAL consumer
(``FilesystemTopologyReaders.closure_complete``), against a temporary scratch
workspace. ``docs/closure/`` of this repository is never read or written.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from _closure_legacy_names import legacy_closure_filename
from test_cli_gate_closure_evidence import (
    evidence_record,
    evidence_relpath,
    with_close_keys,
    write_evidence,
)

from autoharness.cli import main
from autoharness.gates.closure_contract import DEFAULT_CLOSURE_DIR, build_closure_path
from autoharness.gates.topology import FilesystemTopologyReaders

_ACCEPTABLE = "---\ncompaction_status: done\nclosure_status: READY\n---\n"
_UNSATISFIED_CONDITIONS = (
    "---\n"
    "compaction_status: done\n"
    "closure_status: READY_WITH_CONDITIONS\n"
    "conditions:\n"
    "  - name: monitoring window elapsed\n"
    "    satisfied: false\n"
    "    evidence: docs/closure/evidence.md\n"
    "---\n"
)

_SHIPMENT = "901-S"
_FEATURE = "903-F"
_FOREIGN_SHIPMENT = "902-S"
_FOREIGN_FEATURE = "904-F"


def _gate_exit(path: Path, shipment_id: str, workspace: Path) -> int | None:
    """Run the real write-time gate in-process and return its exit code."""
    code: int | None = 0
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        try:
            main(
                [
                    "gate",
                    "closure-evidence",
                    "--path",
                    str(path),
                    "--shipment",
                    shipment_id,
                    "--workspace",
                    str(workspace),
                ]
            )
        except SystemExit as exc:  # noqa: PERF203 - CLI harness
            code = exc.code
    return code


class ComposedClosureStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:  # noqa: D401 - unittest hook
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name).resolve() / "workspace"
        self.closure_dir = self.workspace / DEFAULT_CLOSURE_DIR
        self.closure_dir.mkdir(parents=True)
        self.reader = FilesystemTopologyReaders(self.workspace)

    def tearDown(self) -> None:  # noqa: D401 - unittest hook
        self._tmp.cleanup()

    def _produce(self, shipment_id: str, feature_id: str, body: str) -> Path:
        path = build_closure_path(
            DEFAULT_CLOSURE_DIR.as_posix(), shipment_id, feature_id, workspace_root=self.workspace
        )
        path.write_text(body, encoding="utf-8")
        return path

    def _produce_legacy(self, shipment_id: str, suffix: str, body: str) -> Path:
        path = self.closure_dir / legacy_closure_filename(shipment_id, suffix)
        path.write_text(body, encoding="utf-8")
        return path

    def test_composed_round_trip_producer_to_real_consumer(self) -> None:
        # 192-F (A4): the producer also declares close_path and cites a valid close-evidence record.
        write_evidence(self.workspace, _SHIPMENT, _FEATURE, evidence_record("safe_close", _SHIPMENT, _FEATURE))
        body = with_close_keys(_ACCEPTABLE, "safe_close", evidence_relpath(_SHIPMENT, _FEATURE))
        artifact = self._produce(_SHIPMENT, _FEATURE, body)
        # Producer side: the write-time gate the producer spec mandates accepts it.
        self.assertEqual(_gate_exit(artifact, _SHIPMENT, self.workspace), 0)
        # Consumer side: the real topology reader recognizes and accepts it.
        discovery = self.reader.closure_discovery(_SHIPMENT)
        self.assertEqual(discovery.outcome, "recognized")
        self.assertEqual(discovery.canonical_matches, (artifact,))
        self.assertIs(self.reader.closure_complete(_SHIPMENT), True)

    def test_composed_precedence_canonical_partition_decides(self) -> None:
        # The 173-S shape: canonical and legacy artifacts coexist for one shipment.
        canonical = self._produce(_SHIPMENT, _FEATURE, _ACCEPTABLE)
        legacy = self._produce_legacy(_SHIPMENT.lower(), _FEATURE.lower(), _UNSATISFIED_CONDITIONS)
        self.assertIs(self.reader.closure_complete(_SHIPMENT), True)
        discovery = self.reader.closure_discovery(_SHIPMENT)
        self.assertEqual(discovery.legacy_matches, (legacy,))
        self.assertEqual(discovery.evaluation_order, (canonical,))
        # Swap validity: the canonical artifact alone still decides the verdict,
        # so an acceptable legacy artifact cannot rescue an unacceptable canonical one.
        canonical.write_text(_UNSATISFIED_CONDITIONS, encoding="utf-8")
        legacy.write_text(_ACCEPTABLE, encoding="utf-8")
        self.assertIs(self.reader.closure_complete(_SHIPMENT), False)

    def test_composed_legacy_only_acceptance(self) -> None:
        # The 162-S / 174-S shape: only a legacy date-prefixed artifact exists.
        legacy = self._produce_legacy(_SHIPMENT.lower(), _FEATURE.lower(), _ACCEPTABLE)
        discovery = self.reader.closure_discovery(_SHIPMENT)
        self.assertEqual(discovery.outcome, "recognized")
        self.assertEqual(discovery.canonical_matches, ())
        self.assertEqual(discovery.evaluation_order, (legacy,))
        self.assertIs(self.reader.closure_complete(_SHIPMENT), True)
        # Readable is not writable: the write-time gate still rejects the legacy name.
        self.assertNotEqual(_gate_exit(legacy, _SHIPMENT, self.workspace), 0)

    def test_composed_validity_and_attribution_coupling(self) -> None:
        artifact = self._produce(_SHIPMENT, _FEATURE, _UNSATISFIED_CONDITIONS)
        # Recognition never implies acceptance, at either end of the composed path.
        self.assertEqual(self.reader.closure_discovery(_SHIPMENT).outcome, "recognized")
        self.assertIs(self.reader.closure_complete(_SHIPMENT), False)
        self.assertNotEqual(_gate_exit(artifact, _SHIPMENT, self.workspace), 0)
        # Attribution never admits a neighbour: only a foreign shipment's
        # acceptable artifact present yields None (absent) for the requested one.
        artifact.unlink()
        self._produce(_FOREIGN_SHIPMENT, _FOREIGN_FEATURE, _ACCEPTABLE)
        self.assertEqual(self.reader.closure_discovery(_SHIPMENT).outcome, "absent")
        self.assertIsNone(self.reader.closure_complete(_SHIPMENT))
        self.assertIs(self.reader.closure_complete(_FOREIGN_SHIPMENT), True)


if __name__ == "__main__":
    unittest.main()

"""CLI smoke tests for `autoharness gate pipeline-topology`."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from autoharness.cli import main


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


class PipelineTopologyHelpTests(unittest.TestCase):
    def test_gate_help_lists_pipeline_topology(self) -> None:
        out, _, _ = _run('gate', '--help')
        self.assertIn('pipeline-topology', out)
        self.assertIn('--shipment', out)
        self.assertIn('--phase', out)

    def test_pipeline_topology_help(self) -> None:
        out, _, _ = _run('gate', 'pipeline-topology', '--help')
        self.assertIn('pipeline-topology', out)
        self.assertIn('--shipment', out)
        self.assertIn('--phase', out)


class PipelineTopologyArgTests(unittest.TestCase):
    def test_unknown_flag_exits_2(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--bogus')
        self.assertEqual(code, 2)

    def test_agent_mode_requires_shipment(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--phase', 'pre_claim')
        self.assertEqual(code, 2)

    def test_agent_mode_requires_non_ambient_phase(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--shipment', '114-S', '--phase', 'ambient')
        self.assertEqual(code, 2)

    def test_manual_mode_defaults_to_ambient(self) -> None:
        class FakeReaders:
            def list_shipments(self):
                return ()

            def read_artifact(self, artifact_id: str):
                return None

            def current_branch(self) -> str:
                return 'topic/misc'

            def default_branch(self) -> str:
                return 'main'

            def worktree_porcelain(self) -> str:
                return 'worktree C:/repo\nHEAD 0\nbranch refs/heads/topic/misc\n\n'

            def closure_complete(self, shipment_id: str):
                return None

        with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=FakeReaders()):
            out, _, code = _run('gate', 'pipeline-topology', '--json')
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload['phase'], 'ambient')
        self.assertIsNone(payload['target_shipment_id'])

    def test_agent_mode_echoes_target_and_phase(self) -> None:
        class FakeReaders:
            def list_shipments(self):
                from autoharness.gates.topology import ShipmentState
                return (ShipmentState(shipment_id='114-S', title='114-S', live_status='queued'),)

            def read_artifact(self, artifact_id: str):
                return None

            def current_branch(self) -> str:
                return 'main'

            def default_branch(self) -> str:
                return 'main'

            def worktree_porcelain(self) -> str:
                return 'worktree C:/repo\nHEAD 0\nbranch refs/heads/main\n\n'

            def closure_complete(self, shipment_id: str):
                return None

        with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=FakeReaders()):
            out, _, code = _run(
                'gate', 'pipeline-topology',
                '--mode', 'agent',
                '--shipment', '114-S',
                '--phase', 'pre_claim',
                '--json',
            )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload['mode'], 'agent')
        self.assertEqual(payload['phase'], 'pre_claim')
        self.assertEqual(payload['target_shipment_id'], '114-S')



class PipelineTopologyForceTests(unittest.TestCase):
    def test_force_overrides_block_and_emits_audit_and_telemetry(self) -> None:
        class FakeReaders:
            def list_shipments(self):
                from autoharness.gates.topology import ShipmentState
                return (ShipmentState(shipment_id='114-S', title='114-S', live_status='active'),)

            def read_artifact(self, artifact_id: str):
                return None

            def current_branch(self) -> str:
                return 'main'

            def default_branch(self) -> str:
                return 'main'

            def worktree_porcelain(self) -> str:
                return 'worktree C:/repo\nHEAD 0\nbranch refs/heads/main\n\n'

            def closure_complete(self, shipment_id: str):
                return None

        with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=FakeReaders()):
            with mock.patch('autoharness.cli._audit_pipeline_topology_force', return_value='audit.log') as audit_fn:
                with mock.patch('autoharness.cli._emit_pipeline_topology_telemetry', return_value='telemetry.jsonl') as telemetry_fn:
                    out, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--shipment', '114-S', '--phase', 'pre_claim', '--force', '--json')
        self.assertEqual(code, 0)
        self.assertTrue(audit_fn.called)
        self.assertTrue(telemetry_fn.called)
        payload = json.loads(out)
        self.assertTrue(payload['forced'])
        self.assertEqual(payload['force_audit_log'], 'audit.log')
        self.assertEqual(payload['telemetry_log'], 'telemetry.jsonl')

if __name__ == '__main__':
    unittest.main()

"""CLI smoke tests for `autoharness gate pipeline-topology`."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from autoharness.cli import _emit_pipeline_topology_telemetry, main


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

    def test_agent_mode_requires_phase(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--shipment', '114-S')
        self.assertEqual(code, 2)

    def test_agent_mode_rejects_empty_shipment(self) -> None:
        _, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--shipment', '', '--phase', 'pre_claim')
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

            def read_worktree_marker(self, worktree_path: str):
                return None

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

            def read_worktree_marker(self, worktree_path: str):
                return None

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

    def test_detached_head_blocks_in_agent_mode(self) -> None:
        class FakeReaders:
            def list_shipments(self):
                from autoharness.gates.topology import ShipmentState
                return (ShipmentState(shipment_id='114-S', title='114-S', live_status='queued'),)

            def read_artifact(self, artifact_id: str):
                return None

            def current_branch(self) -> str:
                return ''

            def default_branch(self) -> str:
                return 'main'

            def worktree_porcelain(self) -> str:
                return 'worktree C:/repo\nHEAD 0\n\n'

            def read_worktree_marker(self, worktree_path: str):
                return None

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
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload['token'], 'BRANCH_MISMATCH')

    def test_post_claim_queued_zero_active_reports_retry_required_not_invalid(self) -> None:
        # 109.021-T / 109.022-T / 109.015-T: a post-claim read of a still-queued
        # target with zero active shipments is CLAIM_NOT_OBSERVED (exit 3), a
        # distinct retry-required outcome -- never silently reported as PASS,
        # BLOCK, or a bare "INVALID" (which would wrongly suggest a caller
        # argument error rather than a legitimate read-only retry signal).
        class FakeReaders:
            def list_shipments(self):
                from autoharness.gates.topology import ShipmentState
                return (ShipmentState(shipment_id='114-S', title='114-S', live_status='queued'),)

            def read_artifact(self, artifact_id: str):
                return None

            def current_branch(self) -> str:
                return 'feat/114-s'

            def default_branch(self) -> str:
                return 'main'

            def worktree_porcelain(self) -> str:
                return 'worktree C:/repo\nHEAD 0\nbranch refs/heads/feat/114-s\n\n'

            def read_worktree_marker(self, worktree_path: str):
                return None

            def closure_complete(self, shipment_id: str):
                return None

        with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=FakeReaders()):
            json_out, _, json_code = _run(
                'gate', 'pipeline-topology',
                '--mode', 'agent',
                '--shipment', '114-S',
                '--phase', 'post_claim',
                '--json',
            )
            text_out, _, text_code = _run(
                'gate', 'pipeline-topology',
                '--mode', 'agent',
                '--shipment', '114-S',
                '--phase', 'post_claim',
            )

        self.assertEqual(json_code, 3)
        payload = json.loads(json_out)
        self.assertEqual(payload['token'], 'CLAIM_NOT_OBSERVED')
        self.assertEqual(payload['exit_code'], 3)

        self.assertEqual(text_code, 3)
        self.assertIn('RETRY_REQUIRED', text_out)
        self.assertNotIn('INVALID', text_out)


class PipelineTopologyStorageRootResolutionTests(unittest.TestCase):
    def _write_minimal_backlog_root(self, root: Path) -> None:
        (root / 'queue').mkdir(parents=True)
        (root / 'archive').mkdir(parents=True)

    def test_backlog_only_workspace_succeeds(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / '.backlog')
            with mock.patch(
                'autoharness.gates.topology.FilesystemTopologyReaders',
                side_effect=lambda _workspace: FilesystemTopologyReaders(workspace),
            ):
                out, err, code = _run('gate', 'pipeline-topology', '--mode', 'ci', '--json')

        self.assertEqual(code, 0)
        self.assertEqual(err, '')
        payload = json.loads(out)
        self.assertEqual(payload['message'], 'topology gate pass')
        self.assertEqual(payload['token'], None)

    def test_both_roots_present_returns_structured_block_without_traceback(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / '.backlog')
            self._write_minimal_backlog_root(workspace / '.backlogit')
            with mock.patch(
                'autoharness.gates.topology.FilesystemTopologyReaders',
                side_effect=lambda _workspace: FilesystemTopologyReaders(workspace),
            ):
                out, err, code = _run('gate', 'pipeline-topology', '--mode', 'ci', '--json')

        self.assertEqual(code, 1)
        self.assertNotIn('Traceback', err)
        payload = json.loads(out)
        self.assertEqual(payload['token'], 'BACKLOG_UNAVAILABLE')
        self.assertIn('multiple backlog directories are present', payload['message'])

    def test_missing_override_returns_structured_block_without_fallthrough(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        # '.backlogit' is a valid literal candidate name (accepted by the strict
        # override validator) that simply does not exist as a directory here --
        # this exercises the missing-directory-after-a-valid-override path,
        # distinct from a non-literal override value (covered elsewhere).
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / '.backlog')
            with mock.patch.dict(os.environ, {'BACKLOGIT_WORKSPACE_DIR': '.backlogit'}):
                with mock.patch(
                    'autoharness.gates.topology.FilesystemTopologyReaders',
                    side_effect=lambda _workspace: FilesystemTopologyReaders(workspace),
                ):
                    out, err, code = _run('gate', 'pipeline-topology', '--mode', 'ci', '--json')

        self.assertEqual(code, 1)
        self.assertNotIn('Traceback', err)
        payload = json.loads(out)
        self.assertEqual(payload['token'], 'BACKLOG_UNAVAILABLE')
        self.assertIn('configured backlog directory is unavailable', payload['message'])


class PipelineTopologyTelemetryTests(unittest.TestCase):
    _ENABLED_CONFIG = """
schema_version: "1.0.0"
telemetry:
  mode: "sqlite"
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true
"""

    _DISABLED_CONFIG = """
schema_version: "1.0.0"
telemetry:
  mode: "none"
"""

    def _write_config(self, workspace: Path, text: str) -> None:
        (workspace / '.autoharness').mkdir(parents=True, exist_ok=True)
        (workspace / '.autoharness' / 'config.yaml').write_text(text, encoding='utf-8')

    def _result(self, *, exit_code: int = 0, forced: bool = False):
        from autoharness.gates.topology import CheckResult, TopologyResult

        checks = ()
        if exit_code == 1 or forced:
            checks = (
                CheckResult(
                    name='worktree_topology',
                    status='blocked',
                    token='MULTIPLE_IMPLEMENTATION_WORKTREES',
                    message='blocked',
                ),
            )
        return TopologyResult(
            mode='agent',
            phase='pre_claim',
            resolved_target_shipment_id='114-S',
            checks=checks,
            exit_code=exit_code,
            message='topology gate pass' if exit_code == 0 and not forced else 'topology gate blocked',
            forced=forced,
        )

    def test_telemetry_disabled_writes_no_journal(self) -> None:
        from autoharness.telemetry.record import load_workspace_telemetry_config
        from autoharness.telemetry.tool_event_jsonl import journal_path_for_config

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            self._write_config(workspace, self._DISABLED_CONFIG)
            telemetry_path, warnings = _emit_pipeline_topology_telemetry(workspace, self._result())
            self.assertIsNone(telemetry_path)
            self.assertEqual(warnings, ())
            config = load_workspace_telemetry_config(workspace)
            self.assertIsNone(journal_path_for_config(config))
            self.assertFalse((workspace / '.autoharness' / 'gates' / 'pipeline-topology-telemetry.jsonl').exists())

    def test_telemetry_enabled_writes_tool_event_journal_for_pass_blocked_and_forced(self) -> None:
        from autoharness.telemetry.record import load_workspace_telemetry_config
        from autoharness.telemetry.tool_event_jsonl import journal_path_for_config

        cases = (
            ('success', self._result(exit_code=0, forced=False), None),
            ('blocked', self._result(exit_code=1, forced=False), None),
            ('operator_required', self._result(exit_code=0, forced=True), '.autoharness/gates/pipeline-topology-force-audit.log'),
            # 109.022-T (114-S closure pre-activation fix, Defect 2): any
            # other non-zero, non-blocked, non-forced result -- an invalid
            # gate evaluation (exit_code == 2) or the CLAIM_NOT_OBSERVED
            # retry-required outcome (exit_code == 3, 109.021-T) -- must
            # map to `failed`, never silently default to `success`.
            ('failed', self._result(exit_code=2, forced=False), None),
            ('failed', self._result(exit_code=3, forced=False), None),
        )
        for expected_status, result, audit_path in cases:
            with self.subTest(status=expected_status):
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
                    workspace = Path(tmp)
                    self._write_config(workspace, self._ENABLED_CONFIG)
                    telemetry_path, warnings = _emit_pipeline_topology_telemetry(workspace, result, audit_path)
                    self.assertEqual(warnings, ())
                    config = load_workspace_telemetry_config(workspace)
                    journal_path = journal_path_for_config(config)
                    self.assertEqual(telemetry_path, str(journal_path))
                    self.assertIsNotNone(journal_path)
                    self.assertTrue(journal_path.exists())
                    self.assertFalse((workspace / '.autoharness' / 'gates' / 'pipeline-topology-telemetry.jsonl').exists())
                    record = json.loads(journal_path.read_text(encoding='utf-8').splitlines()[0])
                    self.assertEqual(record['tool_surface'], 'cli')
                    self.assertEqual(record['tool_name'], 'autoharness')
                    self.assertEqual(record['operation'], 'gate pipeline-topology')
                    self.assertEqual(record['status'], expected_status)
                    self.assertEqual(record['phase'], 'pre_claim')
                    self.assertEqual(record['shipment_id'], '114-S')
                    self.assertEqual(record['exit_code'], result.exit_code)
                    if audit_path is None:
                        self.assertIsNone(record['evidence_path'])
                        self.assertEqual(record['artifact_refs'], [])
                    else:
                        self.assertEqual(record['evidence_path'], audit_path)
                        self.assertEqual(record['artifact_refs'], [audit_path])
                    # The free-text `result.message` field can carry raw
                    # backlog frontmatter values and filesystem paths from
                    # fail-closed diagnostics and must never be serialized
                    # into telemetry; only bounded, structured fields belong
                    # in the fingerprint payload.
                    fingerprint = json.loads(record['argv_fingerprint'])
                    self.assertNotIn('message', fingerprint)
                    self.assertEqual(set(fingerprint), {'mode', 'forced', 'token', 'audit_log'})


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

            def read_worktree_marker(self, worktree_path: str):
                return None

            def closure_complete(self, shipment_id: str):
                return None

        with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=FakeReaders()):
            with mock.patch('autoharness.cli._audit_pipeline_topology_force', return_value='audit.log') as audit_fn:
                with mock.patch('autoharness.cli._emit_pipeline_topology_telemetry', return_value=('telemetry.jsonl', ())) as telemetry_fn:
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

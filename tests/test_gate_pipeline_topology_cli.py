"""CLI smoke tests for `autoharness gate pipeline-topology`."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from _env_patch import patched_environ
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


def _check(payload: dict, name: str) -> dict:
    for check in payload['checks']:
        if check['name'] == name:
            return check
    raise AssertionError(f'missing check: {name}')


def _shipment(
    shipment_id: str,
    status: str | None,
    *,
    archived_status: str | None = None,
    labels: tuple[str, ...] = (),
    deps: tuple[str, ...] = (),
    manifest_items: tuple[str, ...] = (),
    archived_record_present: bool | None = None,
):
    from autoharness.gates.topology import ShipmentState

    return ShipmentState(
        shipment_id=shipment_id,
        title=shipment_id,
        live_status=status,
        archived_status=archived_status,
        archived_record_present=(archived_status is not None if archived_record_present is None else archived_record_present),
        manifest_item_ids=manifest_items,
        blocking_predecessor_ids=deps,
        labels=labels,
    )


class _FakeTopologyReaders:
    def __init__(
        self,
        shipments,
        *,
        branch: str = 'main',
        closure_complete_ids: tuple[str, ...] = (),
    ) -> None:
        self._shipments = tuple(shipments)
        self._branch = branch
        self._closure_complete_ids = set(closure_complete_ids)

    def list_shipments(self):
        return self._shipments

    def read_artifact(self, artifact_id: str):
        return None

    def current_branch(self) -> str:
        return self._branch

    def default_branch(self) -> str:
        return 'main'

    def worktree_porcelain(self) -> str:
        return f'worktree C:/repo\nHEAD 0\nbranch refs/heads/{self._branch}\n\n'

    def read_worktree_marker(self, worktree_path: str):
        return None

    def closure_complete(self, shipment_id: str):
        return shipment_id in self._closure_complete_ids


class _PipelineTopologyCliMixin:
    def _run_with_readers(self, readers, *argv: str) -> tuple[str, str, int | None]:
        with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=readers):
            with mock.patch('autoharness.cli._emit_pipeline_topology_telemetry', return_value=(None, ())):
                return _run(*argv)

    def _run_in_workspace(self, workspace: Path, *argv: str) -> tuple[str, str, int | None]:
        previous = Path.cwd()
        try:
            os.chdir(workspace)
            return _run(*argv)
        finally:
            os.chdir(previous)

    def _write_shipment_record(
        self,
        workspace: Path,
        shipment_id: str,
        *,
        folder: str = 'queue',
        status: str | None = None,
        archived_status: str | None = None,
        labels: tuple[str, ...] = (),
        dependencies: tuple[str, ...] = (),
    ) -> None:
        target = workspace / '.backlog' / folder
        target.mkdir(parents=True, exist_ok=True)
        lines = [
            '---',
            f'id: {shipment_id}',
            'artifact_type: shipment',
            f'title: {shipment_id}',
        ]
        if status is not None:
            lines.append(f'status: {status}')
        if archived_status is not None:
            lines.append(f'archived_status: {archived_status}')
        if labels:
            lines.append('labels:')
            lines.extend(f'  - {label}' for label in labels)
        if dependencies:
            lines.append('dependencies:')
            lines.extend(f'  - {dependency}' for dependency in dependencies)
        lines.extend(['---', '', shipment_id])
        (target / f'{shipment_id}.md').write_text('\n'.join(lines), encoding='utf-8')

    def _snapshot_backlog(self, workspace: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        backlog_root = workspace / '.backlog'
        for candidate in sorted(backlog_root.rglob('*')):
            if candidate.is_file():
                relative = str(candidate.relative_to(workspace)).replace('\\', '/')
                result[relative] = candidate.read_text(encoding='utf-8')
        return result

    def _snapshot_files(self, workspace: Path, *, exclude: tuple[str, ...] = ()) -> dict[str, str]:
        excluded = set(exclude)
        result: dict[str, str] = {}
        for candidate in sorted(workspace.rglob('*')):
            if not candidate.is_file():
                continue
            relative = str(candidate.relative_to(workspace)).replace('\\', '/')
            if relative in excluded:
                continue
            result[relative] = candidate.read_text(encoding='utf-8')
        return result


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


class PipelineTopologyRenderingTests(_PipelineTopologyCliMixin, unittest.TestCase):
    def test_json_output_surfaces_predecessor_provenance_and_selected_ids(self) -> None:
        cases = (
            (
                'explicit',
                _FakeTopologyReaders(
                    (
                        _shipment('113-S', 'shipped'),
                        _shipment('114-S', 'queued', deps=('113-S',)),
                    ),
                    closure_complete_ids=('113-S',),
                ),
                '114-S',
                0,
                ['113-S'],
            ),
            (
                'declared_root',
                _FakeTopologyReaders((_shipment('173-S', 'queued', labels=('dag-root',)),)),
                '173-S',
                0,
                [],
            ),
            (
                'genesis',
                _FakeTopologyReaders((_shipment('200-S', 'queued'),)),
                '200-S',
                0,
                [],
            ),
            (
                'unsequenced',
                _FakeTopologyReaders(
                    (
                        _shipment('199-S', 'blocked'),
                        _shipment('200-S', 'queued'),
                    )
                ),
                '200-S',
                1,
                [],
            ),
        )
        for source, readers, shipment_id, expected_code, expected_ids in cases:
            with self.subTest(source=source):
                out, _, code = self._run_with_readers(
                    readers,
                    'gate', 'pipeline-topology',
                    '--mode', 'agent',
                    '--shipment', shipment_id,
                    '--phase', 'pre_claim',
                    '--json',
                )
                self.assertEqual(code, expected_code)
                payload = json.loads(out)
                check = _check(payload, 'shipment_readiness')
                self.assertEqual(check['details']['predecessor_source'], source)
                self.assertEqual(check['details']['predecessor_ids'], expected_ids)
                self.assertEqual(check['details']['selected_predecessor_ids'], expected_ids)

    def test_human_output_states_provenance_alongside_outcome(self) -> None:
        cases = (
            (
                'explicit',
                _FakeTopologyReaders(
                    (
                        _shipment('113-S', 'shipped'),
                        _shipment('114-S', 'queued', deps=('113-S',)),
                    ),
                    closure_complete_ids=('113-S',),
                ),
                '114-S',
                0,
                'shipment_readiness: PASSED — predecessor provenance=explicit; selected predecessor ids=113-S',
            ),
            (
                'declared_root',
                _FakeTopologyReaders((_shipment('173-S', 'queued', labels=('dag-root',)),)),
                '173-S',
                0,
                'shipment_readiness: PASSED — predecessor provenance=declared_root; selected predecessor ids=(none)',
            ),
            (
                'genesis',
                _FakeTopologyReaders((_shipment('200-S', 'queued'),)),
                '200-S',
                0,
                'shipment_readiness: PASSED — predecessor provenance=genesis; selected predecessor ids=(none)',
            ),
            (
                'unsequenced',
                _FakeTopologyReaders(
                    (
                        _shipment('199-S', 'blocked'),
                        _shipment('200-S', 'queued'),
                    )
                ),
                '200-S',
                1,
                'shipment_readiness: BLOCKED (UNSEQUENCED_SHIPMENT) — predecessor provenance=unsequenced; selected predecessor ids=(none)',
            ),
        )
        for source, readers, shipment_id, expected_code, expected_line in cases:
            with self.subTest(source=source):
                out, _, code = self._run_with_readers(
                    readers,
                    'gate', 'pipeline-topology',
                    '--mode', 'agent',
                    '--shipment', shipment_id,
                    '--phase', 'pre_claim',
                )
                self.assertEqual(code, expected_code)
                self.assertIn(expected_line, out)

    def test_unsequenced_rendering_names_both_remedies_and_disqualifying_records(self) -> None:
        readers = _FakeTopologyReaders(
            (
                _shipment('197-S', None, archived_status='mystery', archived_record_present=True),
                _shipment('198-S', None, archived_status=None, archived_record_present=True),
                _shipment('199-S', 'blocked'),
                _shipment('200-S', 'queued'),
            )
        )
        out, _, code = self._run_with_readers(
            readers,
            'gate', 'pipeline-topology',
            '--mode', 'agent',
            '--shipment', '200-S',
            '--phase', 'pre_claim',
        )
        self.assertEqual(code, 1)
        self.assertIn('record the real blocks edge', out)
        self.assertIn('declare the shipment a root', out)
        self.assertIn('genesis did not apply: another shipment record exists in this workspace', out)
        self.assertIn('197-S (archived, status: mystery)', out)
        self.assertIn('198-S (archived, status: missing)', out)
        self.assertIn('199-S (live, status: blocked)', out)


class PipelineTopologyAuditRenderingTests(_PipelineTopologyCliMixin, unittest.TestCase):
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

    def test_audit_phase_json_output_surfaces_read_only_report(self) -> None:
        readers = _FakeTopologyReaders(
            (
                _shipment('199-S', None, archived_status='shipped', archived_record_present=True),
                _shipment('200-S', 'queued'),
            )
        )
        out, _, code = self._run_with_readers(
            readers,
            'gate', 'pipeline-topology',
            '--phase', 'audit_sequencing',
            '--json',
        )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload['phase'], 'audit_sequencing')
        check = _check(payload, 'sequencing_audit')
        self.assertEqual(check['status'], 'passed')
        self.assertFalse(check['details']['blocking'])
        self.assertFalse(check['details']['authorizes_claim'])
        self.assertEqual(check['details']['edge_less_shipments'][0]['derived_state'], 'unsequenced')
        self.assertEqual(
            check['details']['edge_less_shipments'][0]['genesis_disqualifier'],
            'another shipment record exists in this workspace',
        )

    def test_audit_phase_human_output_renders_current_run_audit_details(self) -> None:
        readers = _FakeTopologyReaders(
            (
                _shipment('199-S', None, archived_status='shipped', archived_record_present=True),
                _shipment('200-S', 'queued'),
            )
        )
        out, _, code = self._run_with_readers(
            readers,
            'gate', 'pipeline-topology',
            '--phase', 'audit_sequencing',
        )
        self.assertEqual(code, 0)
        self.assertIn('sequencing_audit: PASSED — current run examined 2 edge-less shipments', out)
        self.assertIn('200-S — derived state=unsequenced; raw numeric candidate ids=199-S', out)
        self.assertIn('genesis did not apply: another shipment record exists in this workspace', out)
        self.assertIn('199-S (archived, status: shipped)', out)
        self.assertNotIn('ledger', out.lower())
        self.assertNotIn('persisted audit artifact', out.lower())

    def test_audit_render_preserves_output_when_telemetry_is_enabled_or_fails_open(self) -> None:
        from autoharness.telemetry.record import load_workspace_telemetry_config
        from autoharness.telemetry.tool_event_jsonl import journal_path_for_config

        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
            workspace = Path(tmp)
            (workspace / '.backlog' / 'queue').mkdir(parents=True)
            (workspace / '.backlog' / 'archive').mkdir(parents=True)
            self._write_shipment_record(workspace, '199-S', folder='archive', archived_status='shipped')
            self._write_shipment_record(workspace, '200-S', status='queued')
            backlog_before = self._snapshot_backlog(workspace)

            self._write_config(workspace, self._DISABLED_CONFIG)
            disabled_out, disabled_err, disabled_code = self._run_in_workspace(
                workspace,
                'gate', 'pipeline-topology',
                '--phase', 'audit_sequencing',
            )
            self.assertEqual(disabled_code, 0)
            self.assertEqual(disabled_err, '')
            self.assertEqual(self._snapshot_backlog(workspace), backlog_before)

            self._write_config(workspace, self._ENABLED_CONFIG)
            config = load_workspace_telemetry_config(workspace)
            journal_path = journal_path_for_config(config)
            self.assertIsNotNone(journal_path)
            before_enabled = self._snapshot_files(
                workspace,
                exclude=(str(journal_path.relative_to(workspace)).replace('\\', '/'),),
            )
            enabled_out, enabled_err, enabled_code = self._run_in_workspace(
                workspace,
                'gate', 'pipeline-topology',
                '--phase', 'audit_sequencing',
            )
            self.assertEqual(enabled_code, disabled_code)
            self.assertEqual(enabled_out, disabled_out)
            self.assertEqual(enabled_err, '')
            self.assertEqual(self._snapshot_backlog(workspace), backlog_before)
            self.assertTrue(journal_path.exists())
            event = json.loads(journal_path.read_text(encoding='utf-8').splitlines()[0])
            self.assertEqual(event['operation'], 'gate pipeline-topology')
            self.assertEqual(event['phase'], 'audit_sequencing')
            self.assertEqual(event['status'], 'success')
            after_enabled = self._snapshot_files(
                workspace,
                exclude=(str(journal_path.relative_to(workspace)).replace('\\', '/'),),
            )
            self.assertEqual(after_enabled, before_enabled)
            self.assertFalse((workspace / '.autoharness' / 'gates').exists())

            with mock.patch(
                'autoharness.telemetry.record.load_workspace_telemetry_config',
                side_effect=RuntimeError('telemetry boom'),
            ):
                failure_out, failure_err, failure_code = self._run_in_workspace(
                    workspace,
                    'gate', 'pipeline-topology',
                    '--phase', 'audit_sequencing',
                )
            self.assertEqual(failure_code, disabled_code)
            self.assertEqual(failure_out, disabled_out)
            self.assertIn('pipeline-topology telemetry warning: telemetry boom', failure_err)
            self.assertEqual(self._snapshot_backlog(workspace), backlog_before)


class PipelineTopologyStorageRootResolutionTests(unittest.TestCase):
    def _write_minimal_backlog_root(self, root: Path) -> None:
        (root / 'queue').mkdir(parents=True)
        (root / 'archive').mkdir(parents=True)

    def test_backlog_only_workspace_succeeds(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
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

        with tempfile.TemporaryDirectory() as tmp:
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
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self._write_minimal_backlog_root(workspace / '.backlog')
            with patched_environ(BACKLOGIT_WORKSPACE_DIR='.backlogit'):
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

        with tempfile.TemporaryDirectory() as tmp:
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
                with tempfile.TemporaryDirectory() as tmp:
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
                    self.assertEqual(
                        set(fingerprint),
                        {
                            'mode',
                            'forced',
                            'token',
                            'audit_log',
                            'invocation',
                            'authorization_source',
                            'inferred_predecessor_id',
                        },
                    )


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
            with mock.patch('autoharness.cli._audit_pipeline_topology_force', return_value=('audit.log', {'path': 'audit.log', 'record_digest': 'x'})) as audit_fn:
                with mock.patch('autoharness.cli._emit_pipeline_topology_telemetry', return_value=('telemetry.jsonl', ())) as telemetry_fn:
                    out, _, code = _run('gate', 'pipeline-topology', '--mode', 'agent', '--shipment', '114-S', '--phase', 'pre_claim', '--force', '--json')
        self.assertEqual(code, 0)
        self.assertTrue(audit_fn.called)
        self.assertTrue(telemetry_fn.called)
        payload = json.loads(out)
        self.assertTrue(payload['forced'])
        self.assertEqual(payload['force_audit_log'], 'audit.log')
        self.assertEqual(payload['telemetry_log'], 'telemetry.jsonl')



class PipelineTopologyBootstrapGrantCliTests(_PipelineTopologyCliMixin, unittest.TestCase):
    def _grant_path(self, workspace: Path, shipment_id: str = '173-S') -> Path:
        return workspace / '.autoharness' / 'bootstrap-grants' / f'{shipment_id}.yaml'

    def _write_grant(
        self,
        workspace: Path,
        *,
        shipment_id: str = '173-S',
        authorized_invocations: tuple[str, ...] = ('orchestrator_pre_route', 'ship_pre_branch', 'ship_pre_claim'),
        expected_token: str = 'PREDECESSOR_NOT_SHIPPED',
        expected_predecessor_id: str = '172-S',
        manifest_items: tuple[str, ...] = ('165.011-T', '165.012-T'),
        manifest_digest: str | None = None,
        authorizing_decision: str = 'D6',
        operator: str = 'Casey',
        raw_text: str | None = None,
    ) -> Path:
        from autoharness.gates.bootstrap_grant import compute_manifest_digest

        grant_path = self._grant_path(workspace, shipment_id)
        grant_path.parent.mkdir(parents=True, exist_ok=True)
        if raw_text is not None:
            grant_path.write_text(raw_text, encoding='utf-8')
            return grant_path
        digest = manifest_digest or compute_manifest_digest(list(manifest_items))
        lines = [
            'schema_version: 1',
            f'shipment_id: {shipment_id}',
            'authorized_invocations:',
            *[f'  - {label}' for label in authorized_invocations],
            f'expected_token: {expected_token}',
            f'expected_predecessor_id: {expected_predecessor_id}',
            f'manifest_digest: {digest}',
            f'authorizing_decision: {authorizing_decision}',
            f'operator: {operator}',
            'expires_on_claim: true',
        ]
        grant_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return grant_path

    def _blocked_readers(self) -> _FakeTopologyReaders:
        return _FakeTopologyReaders(
            (
                _shipment('172-S', 'queued'),
                _shipment('173-S', 'queued', deps=('172-S',), manifest_items=('165.011-T', '165.012-T')),
            ),
            branch='main',
        )

    def _pass_readers(self) -> _FakeTopologyReaders:
        return _FakeTopologyReaders(
            (_shipment('173-S', 'queued', labels=('dag-root',), manifest_items=('165.011-T', '165.012-T')),),
            branch='main',
        )

    def test_no_grant_present_is_byte_identical_with_and_without_bootstrap_flag(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
            workspace = Path(tmp)
            previous = Path.cwd()
            try:
                os.chdir(workspace)
                with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=self._blocked_readers()):
                    with mock.patch('autoharness.cli._pipeline_topology_head_sha', return_value='deadbeef'):
                        without_flag = _run(
                            'gate', 'pipeline-topology',
                            '--mode', 'agent',
                            '--shipment', '173-S',
                            '--phase', 'pre_claim',
                            '--json',
                        )
                        with_flag = _run(
                            'gate', 'pipeline-topology',
                            '--mode', 'agent',
                            '--shipment', '173-S',
                            '--phase', 'pre_claim',
                            '--bootstrap-grant-invocation', 'ship_pre_claim',
                            '--json',
                        )
                with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=self._pass_readers()):
                    pass_without_flag = _run(
                        'gate', 'pipeline-topology',
                        '--mode', 'agent',
                        '--shipment', '173-S',
                        '--phase', 'pre_claim',
                        '--json',
                    )
                    pass_with_flag = _run(
                        'gate', 'pipeline-topology',
                        '--mode', 'agent',
                        '--shipment', '173-S',
                        '--phase', 'pre_claim',
                        '--bootstrap-grant-invocation', 'ship_pre_claim',
                        '--json',
                    )
            finally:
                os.chdir(previous)

            self.assertEqual(without_flag, with_flag)
            self.assertEqual(pass_without_flag, pass_with_flag)
            self.assertFalse((workspace / '.autoharness' / 'gates').exists())

    def test_exact_match_grant_forces_pass_and_emits_full_provenance_audit(self) -> None:
        from autoharness.gates.bootstrap_grant import load_consumption_record

        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
            workspace = Path(tmp)
            self._write_grant(workspace)
            previous = Path.cwd()
            try:
                os.chdir(workspace)
                with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=self._blocked_readers()):
                    with mock.patch('autoharness.cli._pipeline_topology_head_sha', return_value='deadbeef'):
                        out, err, code = _run(
                            'gate', 'pipeline-topology',
                            '--mode', 'agent',
                            '--shipment', '173-S',
                            '--phase', 'pre_claim',
                            '--bootstrap-grant-invocation', 'ship_pre_claim',
                            '--json',
                        )
            finally:
                os.chdir(previous)

            self.assertEqual(code, 0)
            self.assertEqual(err, '')
            payload = json.loads(out)
            self.assertTrue(payload['forced'])
            audit_path = workspace / '.autoharness' / 'gates' / 'pipeline-topology-force-audit.log'
            self.assertTrue(audit_path.exists())
            audit_record = json.loads(audit_path.read_text(encoding='utf-8').splitlines()[0])
            self.assertEqual(audit_record['invocation'], 'ship_pre_claim')
            self.assertEqual(audit_record['head_sha'], 'deadbeef')
            self.assertEqual(audit_record['blocking_token'], 'PREDECESSOR_NOT_SHIPPED')
            self.assertEqual(audit_record['inferred_predecessor_id'], '172-S')
            self.assertEqual(audit_record['manifest']['shipment_id'], '173-S')
            self.assertEqual(audit_record['manifest']['items'], ['165.011-T', '165.012-T'])
            self.assertEqual(audit_record['authorization']['source'], 'grant')
            self.assertEqual(audit_record['authorization']['decision'], 'D6')
            self.assertEqual(audit_record['authorization']['grant_path'], '.autoharness/bootstrap-grants/173-S.yaml')
            record_path = workspace / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / '173-S' / 'ship_pre_claim.json'
            record = load_consumption_record(record_path, workspace=workspace)
            self.assertEqual(record.status, 'consumed')
            self.assertEqual(audit_record['head_sha'], record.head_sha)
            self.assertEqual(audit_record['manifest']['digest'], record.manifest_digest)
            self.assertEqual(audit_record['authorization']['consumption_record_path'], record.relative_path)
            self.assertEqual(audit_record['authorization']['grant_digest'], record.grant_digest)
            self.assertEqual(audit_record['observed_payload']['exit_code'], 1)

    def test_cli_mismatch_dimensions_remain_blocked(self) -> None:
        from autoharness.gates.bootstrap_grant import compute_manifest_digest

        repo_root = Path(__file__).resolve().parents[1]
        cases = (
            ('wrong_shipment', {'shipment_id': '999-S'}, None),
            ('unlisted_invocation', {'authorized_invocations': ('ship_pre_branch',)}, None),
            ('already_consumed', {}, 'preconsume'),
            ('wrong_token', {'expected_token': 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'}, None),
            ('wrong_predecessor', {'expected_predecessor_id': '171-S'}, None),
            ('stale_manifest', {'manifest_digest': compute_manifest_digest(['999.001-T'])}, None),
            ('second_blocking_check', {}, 'double_block'),
        )
        for name, grant_kwargs, mode in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
                    workspace = Path(tmp)
                    self._write_grant(workspace, **grant_kwargs)
                    if mode == 'preconsume':
                        consumed = workspace / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / '173-S' / 'ship_pre_claim.json'
                        consumed.parent.mkdir(parents=True, exist_ok=True)
                        consumed.write_text(
                            json.dumps(
                                {
                                    'schema_version': 1,
                                    'grant_digest': hashlib.sha256(self._grant_path(workspace).read_bytes()).hexdigest(),
                                    'grant_path': '.autoharness/bootstrap-grants/173-S.yaml',
                                    'shipment_id': '173-S',
                                    'label': 'ship_pre_claim',
                                    'phase': 'pre_claim',
                                    'actor': 'agent',
                                    'session_id': 'session-1',
                                    'head_sha': 'deadbeef',
                                    'manifest_digest': compute_manifest_digest(['165.011-T', '165.012-T']),
                                    'manifest_items': ['165.011-T', '165.012-T'],
                                    'blocking_token': 'PREDECESSOR_NOT_SHIPPED',
                                    'inferred_predecessor_id': '172-S',
                                    'claimed_at': '2026-09-14T00:00:00+00:00',
                                    'status': 'consumed',
                                    'audit_ref': {'path': 'audit.log', 'record_digest': 'x'},
                                    'authorizing_decision': 'D6',
                                    'operator': 'Casey',
                                    'observed_payload': {'exit_code': 1},
                                }
                            ),
                            encoding='utf-8',
                        )
                    previous = Path.cwd()
                    try:
                        os.chdir(workspace)
                        readers = self._blocked_readers()
                        if mode == 'double_block':
                            from autoharness.gates.topology import CheckResult, TopologyResult

                            patched_result = TopologyResult(
                                mode='agent',
                                phase='pre_claim',
                                resolved_target_shipment_id='173-S',
                                checks=(
                                    CheckResult(
                                        name='shipment_readiness',
                                        status='blocked',
                                        token='PREDECESSOR_NOT_SHIPPED',
                                        message='PREDECESSOR_NOT_SHIPPED: predecessor 172-S is not in a shipped terminal state',
                                        details={
                                            'predecessor_id': '172-S',
                                            'predecessor_ids': ['172-S'],
                                            'selected_predecessor_ids': ['172-S'],
                                            'predecessor_source': 'explicit',
                                            'target_shipment_id': '173-S',
                                        },
                                    ),
                                    CheckResult(
                                        name='active_shipment_invariant',
                                        status='blocked',
                                        token='PRECLAIM_ACTIVE_SHIPMENT_PRESENT',
                                        message='PRECLAIM_ACTIVE_SHIPMENT_PRESENT: pre-claim requires zero active shipments',
                                        details={'active_shipment_ids': ['170-S']},
                                    ),
                                ),
                                exit_code=1,
                                message='topology gate blocked',
                            )
                            patches = [
                                mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=readers),
                                mock.patch('autoharness.gates.topology.evaluate', return_value=patched_result),
                                mock.patch('autoharness.cli._pipeline_topology_head_sha', return_value='deadbeef'),
                            ]
                        else:
                            patches = [
                                mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=readers),
                                mock.patch('autoharness.cli._pipeline_topology_head_sha', return_value='deadbeef'),
                            ]
                        with patches[0]:
                            with patches[1]:
                                context = patches[2] if len(patches) > 2 else mock.patch('builtins.id')
                                with context:
                                    out, err, code = _run(
                                        'gate', 'pipeline-topology',
                                        '--mode', 'agent',
                                        '--shipment', '173-S',
                                        '--phase', 'pre_claim',
                                        '--bootstrap-grant-invocation', 'ship_pre_claim',
                                        '--json',
                                    )
                    finally:
                        os.chdir(previous)

                    self.assertEqual(code, 1)
                    self.assertFalse(json.loads(out)['forced'])
                    if mode != 'preconsume':
                        self.assertFalse((workspace / '.autoharness' / 'gates' / 'bootstrap-grant-consumption' / '173-S' / 'ship_pre_claim.json').exists())

    def test_malformed_grant_warns_and_remains_blocked(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
            workspace = Path(tmp)
            self._write_grant(workspace, raw_text='schema_version: [')
            previous = Path.cwd()
            try:
                os.chdir(workspace)
                with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=self._blocked_readers()):
                    with mock.patch('autoharness.cli._pipeline_topology_head_sha', return_value='deadbeef'):
                        out, err, code = _run(
                            'gate', 'pipeline-topology',
                            '--mode', 'agent',
                            '--shipment', '173-S',
                            '--phase', 'pre_claim',
                            '--bootstrap-grant-invocation', 'ship_pre_claim',
                            '--json',
                        )
            finally:
                os.chdir(previous)

        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)['forced'])
        self.assertIn('bootstrap grant warning:', err)

    def test_bootstrap_grant_invocation_and_force_together_exit_2(self) -> None:
        _, _, code = _run(
            'gate', 'pipeline-topology',
            '--mode', 'agent',
            '--shipment', '173-S',
            '--phase', 'pre_claim',
            '--bootstrap-grant-invocation', 'ship_pre_claim',
            '--force',
        )
        self.assertEqual(code, 2)

    def test_telemetry_failure_during_forced_grant_run_is_fail_open(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=repo_root) as tmp:
            workspace = Path(tmp)
            self._write_grant(workspace)
            previous = Path.cwd()
            try:
                os.chdir(workspace)
                with mock.patch('autoharness.gates.topology.FilesystemTopologyReaders', return_value=self._blocked_readers()):
                    with mock.patch('autoharness.cli._pipeline_topology_head_sha', return_value='deadbeef'):
                        with mock.patch('autoharness.telemetry.record.load_workspace_telemetry_config', side_effect=RuntimeError('telemetry boom')):
                            out, err, code = _run(
                                'gate', 'pipeline-topology',
                                '--mode', 'agent',
                                '--shipment', '173-S',
                                '--phase', 'pre_claim',
                                '--bootstrap-grant-invocation', 'ship_pre_claim',
                                '--json',
                            )
            finally:
                os.chdir(previous)

        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)['forced'])
        self.assertIn('pipeline-topology telemetry warning: telemetry boom', err)

if __name__ == '__main__':
    unittest.main()

"""Deterministic tests for the pipeline-topology gate core."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.gates.topology import (
    ArtifactState,
    ShipmentState,
    TopologyInput,
    _active_invariant_check,
    _shipment_readiness_check,
    evaluate,
)


class _FakeReaders:
    def __init__(self, shipments=(), artifacts=None, branch='main', default_branch='main', worktrees=None, worktree_markers=None):
        if shipments and isinstance(shipments[0], (list, tuple)):
            self._snapshots = [tuple(snapshot) for snapshot in shipments]
        else:
            self._snapshots = [tuple(shipments)]
        self._artifacts = dict(artifacts or {})
        self._branch = branch
        self._default_branch = default_branch
        self._worktrees = worktrees or (
            'worktree C:/repo\n'
            'HEAD 0000000000000000000000000000000000000000\n'
            f'branch refs/heads/{branch}\n\n'
        )
        self._worktree_markers = dict(worktree_markers or {})
        self._calls = 0

    def list_shipments(self):
        index = min(self._calls, len(self._snapshots) - 1)
        self._calls += 1
        return self._snapshots[index]

    def read_artifact(self, artifact_id: str):
        return self._artifacts.get(artifact_id)

    def current_branch(self) -> str:
        return self._branch

    def default_branch(self) -> str:
        return self._default_branch

    def worktree_porcelain(self) -> str:
        return self._worktrees

    def read_worktree_marker(self, worktree_path: str):
        return self._worktree_markers.get(worktree_path)

    def closure_complete(self, shipment_id: str):
        return None


def _shipment(shipment_id: str, status: str, *items: str, title: str | None = None, archived_status: str | None = None, deps=()) -> ShipmentState:
    return ShipmentState(
        shipment_id=shipment_id,
        title=title or shipment_id,
        live_status=status,
        archived_status=archived_status,
        manifest_item_ids=tuple(items),
        blocking_predecessor_ids=tuple(deps),
    )


def _check(result, name: str):
    for check in result.checks:
        if check.name == name:
            return check
    raise AssertionError(f'missing check: {name}')


def _task(task_id: str, status: str) -> ArtifactState:
    return ArtifactState(artifact_id=task_id, artifact_type='task', live_status=status)


class FilesystemTopologyReadersTests(unittest.TestCase):
    def test_missing_backlog_dir_blocks_in_agent_and_ci_modes(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            reader = FilesystemTopologyReaders(workspace)
            cases = (
                ('agent', 'pre_claim', '114-S'),
                ('ci', None, None),
            )
            for mode, phase, target in cases:
                with self.subTest(mode=mode):
                    result = evaluate(
                        TopologyInput(mode=mode, phase=phase, target_shipment_id=target),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_empty_queue_and_archive_dirs_pass_as_zero_shipments(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            (workspace / '.backlogit' / 'queue').mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir(parents=True)
            reader = FilesystemTopologyReaders(workspace)

            self.assertEqual(tuple(reader.list_shipments()), ())
            result = evaluate(
                TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                readers=reader,
            )
            self.assertEqual(result.exit_code, 0)

    def test_missing_queue_or_archive_dir_blocks(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        for missing_folder in ('queue', 'archive'):
            with self.subTest(missing_folder=missing_folder):
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
                    workspace = Path(tmp)
                    backlog_dir = workspace / '.backlogit'
                    backlog_dir.mkdir(parents=True)
                    (backlog_dir / ('archive' if missing_folder == 'queue' else 'queue')).mkdir()
                    reader = FilesystemTopologyReaders(workspace)

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_closure_complete_accepts_done_or_degraded_only(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            closure_dir = workspace / 'docs' / 'closure'
            closure_dir.mkdir(parents=True)
            cases = (
                ('done', True),
                ('degraded', True),
                ('ready', False),
                ('pending', False),
            )
            for status, expected in cases:
                with self.subTest(status=status):
                    for existing in closure_dir.glob('*.md'):
                        existing.unlink()
                    (closure_dir / '114-S-2026-08-05-post-merge-closure.md').write_text(
                        f"---\ncompaction_status: {status}\n---\n",
                        encoding='utf-8',
                    )
                    reader = FilesystemTopologyReaders(workspace)
                    self.assertIs(reader.closure_complete('114-S'), expected)

    def test_malformed_shipment_frontmatter_blocks_as_backlog_unavailable(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        cases = {
            'invalid_yaml': "---\nid: [unterminated\n---\n",
            'missing_delimiter': "id: 114-S\nartifact_type: shipment\n",
            'non_mapping_body': "---\n- just\n- a\n- list\n---\n",
        }
        for label, content in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
                    workspace = Path(tmp)
                    queue = workspace / '.backlogit' / 'queue'
                    queue.mkdir(parents=True)
                    (workspace / '.backlogit' / 'archive').mkdir()
                    (queue / '114-S.md').write_text(content, encoding='utf-8')
                    reader = FilesystemTopologyReaders(workspace)

                    with self.assertRaises(Exception):
                        reader.list_shipments()

                    result = evaluate(
                        TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                        readers=reader,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_malformed_task_frontmatter_blocks_via_detect_before_consistency(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            queue = workspace / '.backlogit' / 'queue'
            queue.mkdir(parents=True)
            (workspace / '.backlogit' / 'archive').mkdir()
            (queue / '114-S.md').write_text(
                "---\nid: 114-S\nartifact_type: shipment\nstatus: queued\n"
                "custom_fields:\n  items:\n  - 109.001-T\n---\n",
                encoding='utf-8',
            )
            # Malformed task artifact frontmatter: valid delimiters but invalid YAML body.
            (queue / '109.001-T.md').write_text("---\nstatus: [unterminated\n---\n", encoding='utf-8')
            reader = FilesystemTopologyReaders(workspace)

            result = evaluate(
                TopologyInput(mode='ci', phase=None, target_shipment_id=None),
                readers=reader,
            )
            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.primary_token, 'BACKLOG_UNAVAILABLE')

    def test_read_worktree_marker_reads_repo_local_marker(self) -> None:
        from autoharness.gates.topology import FilesystemTopologyReaders

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            workspace = Path(tmp)
            worktree = workspace / 'spike-research'
            marker_dir = worktree / '.autoharness'
            marker_dir.mkdir(parents=True)
            marker = marker_dir / 'stage-worktree-marker.yaml'
            marker.write_text('role: spike-research\nexpires_at: "2999-01-01T00:00:00Z"\n', encoding='utf-8')
            reader = FilesystemTopologyReaders(workspace)
            self.assertEqual(reader.read_worktree_marker(str(worktree)), marker.read_text(encoding='utf-8'))
            self.assertIsNone(reader.read_worktree_marker(str(worktree / 'missing')))


class ActiveInvariantTests(unittest.TestCase):
    def test_phase_matrix(self) -> None:
        cases = (
            ('pre_claim', (), None, 'passed', None),
            ('pre_claim', (_shipment('114-S', 'active'),), '114-S', 'blocked', 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            ('pre_claim', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            ('post_claim', (), '114-S', 'blocked', 'LIFECYCLE_NO_ACTIVE_SHIPMENT'),
            ('post_claim', (_shipment('114-S', 'active'),), '114-S', 'passed', None),
            ('post_claim', (_shipment('115-S', 'active'),), '114-S', 'blocked', 'LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH'),
            ('post_claim', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS'),
            ('lifecycle', (), '114-S', 'blocked', 'LIFECYCLE_NO_ACTIVE_SHIPMENT'),
            ('lifecycle', (_shipment('114-S', 'active'),), '114-S', 'passed', None),
            ('lifecycle', (_shipment('115-S', 'active'),), '114-S', 'blocked', 'LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH'),
            ('lifecycle', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS'),
            ('ambient', (), None, 'passed', None),
            ('ambient', (_shipment('114-S', 'active'),), '114-S', 'passed', None),
            ('ambient', (_shipment('115-S', 'active'),), '114-S', 'blocked', 'AMBIENT_ACTIVE_SHIPMENT_MISMATCH'),
            ('ambient', (_shipment('115-S', 'active'),), None, 'blocked', 'AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT'),
            ('ambient', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 'blocked', 'AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS'),
        )
        for phase, shipments, target, status, token in cases:
            with self.subTest(phase=phase, shipments=[s.shipment_id for s in shipments], target=target):
                check = _active_invariant_check(phase, target, shipments)
                self.assertEqual(check.status, status)
                self.assertEqual(check.token, token)

    def test_ambient_zero_active_differs_from_lifecycle(self) -> None:
        ambient = _active_invariant_check('ambient', None, ())
        lifecycle = _active_invariant_check('lifecycle', '114-S', ())
        self.assertEqual(ambient.status, 'passed')
        self.assertEqual(lifecycle.token, 'LIFECYCLE_NO_ACTIVE_SHIPMENT')


class DetectBeforeConsistencyTests(unittest.TestCase):
    def test_detect_before_runs_before_active_invariant(self) -> None:
        readers = _FakeReaders(
            shipments=(
                _shipment('114-S', 'queued', '109.002-T', '109-F'),
                _shipment('115-S', 'active'),
            ),
            artifacts={
                '109.002-T': _task('109.002-T', 'done'),
                '109-F': ArtifactState(artifact_id='109-F', artifact_type='feature', live_status='active'),
            },
        )
        result = evaluate(
            TopologyInput(mode='manual', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.primary_token, 'SHIPMENT_STATE_INCONSISTENT')
        self.assertIn('109.002-T', result.message)


if __name__ == '__main__':
    unittest.main()


class BranchOwnershipTests(unittest.TestCase):
    def test_matching_target_branch_passes(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'),),
            branch='feat/114-s',
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').token, 'BRANCH_OK')

    def test_default_branch_is_create_eligible(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').token, 'BRANCH_CREATE_ELIGIBLE')

    def test_detached_head_blocks(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 1)
        check = _check(result, 'branch_ownership')
        self.assertEqual(check.token, 'BRANCH_MISMATCH')
        self.assertTrue(check.details['detached_head'])

    def test_non_target_branch_blocks(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued'), _shipment('115-S', 'queued')),
            branch='feat/115-s',
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.primary_token, 'BRANCH_MISMATCH')

    def test_agent_target_must_resolve(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='999-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 2)

    def test_agent_target_must_resolve_even_with_empty_shipment_map(self) -> None:
        # Regression: an explicit --shipment target naming an unknown/nonexistent
        # shipment must be rejected (exit 2) even when list_shipments() returns
        # zero records (e.g. an empty/uninitialized backlog). A vacuous
        # shipment_map must never short-circuit target validation to a silent
        # pass-through.
        readers = _FakeReaders(shipments=(), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='999-S-DOES-NOT-EXIST'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 2)

    def test_ambient_uses_active_target_before_branch(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'active'), _shipment('115-S', 'queued')),
            branch='feat/115-s',
        )
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.resolved_target_shipment_id, '114-S')
        self.assertEqual(result.primary_token, 'BRANCH_MISMATCH')

    def test_ambient_without_target_skips_only_ownership(self) -> None:
        readers = _FakeReaders(shipments=(), branch='topic/misc')
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').status, 'skipped')


class WorktreeTopologyTests(unittest.TestCase):
    def test_stage_spike_research_exception_does_not_count(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: spike-research\nexpires_at: "2999-01-01T00:00:00Z"\n',
                },
            ),
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'worktree_topology').token, 'WORKTREE_TOPOLOGY_OK')

    def test_stage_spike_missing_marker_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s', worktrees=worktrees),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_stage_spike_expired_marker_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: spike-research\nexpires_at: "2000-01-01T00:00:00Z"\n',
                },
            ),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_stage_spike_wrong_role_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: implementation\nexpires_at: "2999-01-01T00:00:00Z"\n',
                },
            ),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_stage_spike_unparseable_marker_counts_as_implementation(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-stage-spike-001\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/spike/topology\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(
                shipments=(_shipment('114-S', 'queued'),),
                branch='feat/114-s',
                worktrees=worktrees,
                worktree_markers={
                    'C:/repo-stage-spike-001': 'role: [unterminated',
                },
            ),
        )
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')

    def test_multiple_implementation_worktrees_block(self) -> None:
        worktrees = (
            'worktree C:/repo\n'
            'HEAD 1111111111111111111111111111111111111111\n'
            'branch refs/heads/feat/114-s\n\n'
            'worktree C:/repo-2\n'
            'HEAD 2222222222222222222222222222222222222222\n'
            'branch refs/heads/feat/115-s\n\n'
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s', worktrees=worktrees),
        )
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.primary_token, 'MULTIPLE_IMPLEMENTATION_WORKTREES')


class TargetShipmentReadinessTests(unittest.TestCase):
    def test_pre_claim_target_must_be_queued(self) -> None:
        cases = (
            _shipment('114-S', 'shipped'),
            _shipment('114-S', 'abandoned'),
            _shipment('114-S', '', archived_status='shipped'),
        )
        for shipment in cases:
            with self.subTest(shipment=shipment):
                check = _shipment_readiness_check('pre_claim', '114-S', (shipment,), _FakeReaders())
                self.assertEqual(check.status, 'blocked')
                self.assertEqual(check.token, 'TARGET_NOT_CLAIMABLE')

    def test_pre_claim_queued_target_still_passes(self) -> None:
        check = _shipment_readiness_check('pre_claim', '114-S', (_shipment('114-S', 'queued'),), _FakeReaders())
        self.assertEqual((check.status, check.token), ('passed', None))

    def test_post_claim_and_lifecycle_target_must_be_active(self) -> None:
        for phase in ('post_claim', 'lifecycle'):
            with self.subTest(phase=phase, state='queued'):
                check = _shipment_readiness_check(phase, '114-S', (_shipment('114-S', 'queued'),), _FakeReaders())
                self.assertEqual(check.status, 'blocked')
                self.assertEqual(check.token, 'TARGET_NOT_ACTIVE')
            with self.subTest(phase=phase, state='active'):
                check = _shipment_readiness_check(phase, '114-S', (_shipment('114-S', 'active'),), _FakeReaders())
                self.assertEqual((check.status, check.token), ('passed', None))

    def test_ambient_target_status_check_remains_permissive(self) -> None:
        for shipment in (
            _shipment('114-S', 'queued'),
            _shipment('114-S', 'active'),
            _shipment('114-S', 'shipped'),
        ):
            with self.subTest(shipment=shipment):
                check = _shipment_readiness_check('ambient', '114-S', (shipment,), _FakeReaders())
                self.assertEqual((check.status, check.token), ('passed', None))


class ShipmentReadinessTests(unittest.TestCase):
    def test_live_shipped_with_complete_closure_passes(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        readers = Readers(shipments=(
            _shipment('113-S', 'shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_archived_done_with_complete_closure_passes(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        readers = Readers(shipments=(
            _shipment('113-S', '', archived_status='done'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_non_terminal_predecessor_blocks(self) -> None:
        readers = _FakeReaders(shipments=(
            _shipment('113-S', 'queued'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_NOT_SHIPPED')

    def test_ambiguous_live_and_archived_predecessor_blocks(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return True

        readers = Readers(shipments=(
            _shipment('113-S', 'queued', archived_status='shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_STATE_AMBIGUOUS')

    def test_live_shipped_duplicate_archive_predecessor_blocks(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return True

        readers = Readers(shipments=(
            _shipment('113-S', 'shipped', archived_status='shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_STATE_AMBIGUOUS')

    def test_incomplete_closure_blocks_even_when_terminal(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return False

        readers = Readers(shipments=(
            _shipment('113-S', 'shipped'),
            _shipment('114-S', 'queued', deps=('113-S',)),
        ))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'PREDECESSOR_CLOSURE_INCOMPLETE')


class PostClaimVerifyTests(unittest.TestCase):
    def test_target_sole_active_passes(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'active'),))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_target_queued_retries_after_full_revalidation(self) -> None:
        snapshots = [
            (_shipment('114-S', 'queued'),),
            (_shipment('114-S', 'queued'),),
            (_shipment('114-S', 'queued'),),
            (_shipment('114-S', 'active'),),
        ]
        readers = _FakeReaders(shipments=snapshots)
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)

    def test_other_active_blocks_with_claim_verify_failed(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('115-S', 'active'), _shipment('114-S', 'queued')))
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'CLAIM_VERIFY_FAILED')

    def test_inconsistent_state_blocks_with_claim_verify_failed(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'queued', '109.002-T'),),
            artifacts={'109.002-T': _task('109.002-T', 'done')},
        )
        result = evaluate(
            TopologyInput(mode='agent', phase='post_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.primary_token, 'CLAIM_VERIFY_FAILED')


class AgentInputValidationTests(unittest.TestCase):
    def test_missing_phase_in_agent_mode_is_invalid(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase=None, target_shipment_id='114-S'),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),)),
        )
        self.assertEqual(result.exit_code, 2)

    def test_empty_shipment_in_agent_mode_is_invalid(self) -> None:
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id=''),
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),)),
        )
        self.assertEqual(result.exit_code, 2)


class ReadinessMatrixTests(unittest.TestCase):
    def _result(self, predecessor: ShipmentState, closure_complete: bool | None) -> tuple[int, str | None]:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return closure_complete

        readers = Readers(shipments=(predecessor, _shipment('114-S', 'queued', deps=('113-S',))))
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        return result.exit_code, result.primary_token

    def test_terminal_states_require_complete_closure(self) -> None:
        pass_cases = (
            _shipment('113-S', 'shipped'),
            _shipment('113-S', '', archived_status='shipped'),
            _shipment('113-S', '', archived_status='done'),
        )
        for predecessor in pass_cases:
            with self.subTest(predecessor=predecessor):
                exit_code, token = self._result(predecessor, True)
                self.assertEqual((exit_code, token), (0, None))
                exit_code, token = self._result(predecessor, False)
                self.assertEqual(token, 'PREDECESSOR_CLOSURE_INCOMPLETE')

    def test_non_terminal_or_ambiguous_states_block(self) -> None:
        block_cases = (
            (_shipment('113-S', 'queued'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', 'active'), 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            (_shipment('113-S', 'abandoned'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='queued'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='active'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='blocked'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status='abandoned'), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', '', archived_status=None), 'PREDECESSOR_NOT_SHIPPED'),
            (_shipment('113-S', 'queued', archived_status='shipped'), 'PREDECESSOR_STATE_AMBIGUOUS'),
        )
        for predecessor, expected_token in block_cases:
            with self.subTest(predecessor=predecessor):
                exit_code, token = self._result(predecessor, True)
                self.assertEqual(token, expected_token)


class SuppliedTargetTests(unittest.TestCase):
    def test_branch_and_readiness_use_supplied_target(self) -> None:
        class Readers(_FakeReaders):
            def closure_complete(self, shipment_id: str):
                return shipment_id == '113-S'

        readers = Readers(
            shipments=(
                _shipment('113-S', 'shipped'),
                _shipment('114-S', 'queued', deps=('113-S',)),
                _shipment('115-S', 'queued', deps=('114-S',)),
            ),
            branch='feat/114-s',
        )
        pass_result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(pass_result.exit_code, 0)

        block_result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='115-S'),
            readers=readers,
        )
        self.assertEqual(block_result.primary_token, 'BRANCH_MISMATCH')


class AmbientResolutionTests(unittest.TestCase):
    def test_currently_claimed_target_is_used(self) -> None:
        readers = _FakeReaders(
            shipments=(_shipment('114-S', 'active'), _shipment('115-S', 'queued')),
            branch='feat/114-s',
        )
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.resolved_target_shipment_id, '114-S')

    def test_no_target_ambient_still_runs_ambient_invariants(self) -> None:
        readers = _FakeReaders(shipments=(), branch='topic/misc')
        result = evaluate(
            TopologyInput(mode='manual', phase='ambient', target_shipment_id=None),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'branch_ownership').status, 'skipped')
        self.assertEqual(_check(result, 'shipment_readiness').status, 'skipped')
        self.assertEqual(_check(result, 'worktree_topology').token, 'WORKTREE_TOPOLOGY_OK')


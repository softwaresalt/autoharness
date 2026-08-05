"""Deterministic tests for the pipeline-topology gate core."""

from __future__ import annotations

import unittest

from autoharness.gates.topology import (
    ArtifactState,
    ShipmentState,
    TopologyInput,
    _active_invariant_check,
    evaluate,
)


class _FakeReaders:
    def __init__(self, shipments=(), artifacts=None, branch='main', default_branch='main', worktrees=None):
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
            readers=_FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='feat/114-s', worktrees=worktrees),
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(_check(result, 'worktree_topology').token, 'WORKTREE_TOPOLOGY_OK')

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

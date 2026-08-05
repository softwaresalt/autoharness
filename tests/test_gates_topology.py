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
    def __init__(self, shipments=(), artifacts=None, branch='main', default_branch='main'):
        self._shipments = tuple(shipments)
        self._artifacts = dict(artifacts or {})
        self._branch = branch
        self._default_branch = default_branch

    def list_shipments(self):
        return self._shipments

    def read_artifact(self, artifact_id: str):
        return self._artifacts.get(artifact_id)

    def current_branch(self) -> str:
        return self._branch

    def default_branch(self) -> str:
        return self._default_branch

    def worktree_porcelain(self) -> str:
        return ''

    def closure_complete(self, shipment_id: str):
        return None


def _shipment(shipment_id: str, status: str, *items: str) -> ShipmentState:
    return ShipmentState(
        shipment_id=shipment_id,
        title=shipment_id,
        live_status=status,
        manifest_item_ids=tuple(items),
    )


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
        self.assertEqual(result.checks[-1].token, 'BRANCH_OK')

    def test_default_branch_is_create_eligible(self) -> None:
        readers = _FakeReaders(shipments=(_shipment('114-S', 'queued'),), branch='main')
        result = evaluate(
            TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='114-S'),
            readers=readers,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.checks[-1].token, 'BRANCH_CREATE_ELIGIBLE')

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
        self.assertEqual(result.checks[-1].status, 'skipped')

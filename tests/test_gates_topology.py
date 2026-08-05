"""Deterministic tests for the pipeline-topology gate core."""

from __future__ import annotations

import unittest

from autoharness.gates.topology import (
    ArtifactState,
    ShipmentState,
    TopologyInput,
    evaluate,
)


class _FakeReaders:
    def __init__(self, shipments=(), artifacts=None):
        self._shipments = tuple(shipments)
        self._artifacts = dict(artifacts or {})

    def list_shipments(self):
        return self._shipments

    def read_artifact(self, artifact_id: str):
        return self._artifacts.get(artifact_id)

    def current_branch(self) -> str:
        return 'main'

    def default_branch(self) -> str:
        return 'main'

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
            ('pre_claim', (), None, 0, None),
            ('pre_claim', (_shipment('114-S', 'active'),), '114-S', 1, 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            ('pre_claim', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 1, 'PRECLAIM_ACTIVE_SHIPMENT_PRESENT'),
            ('post_claim', (), '114-S', 1, 'LIFECYCLE_NO_ACTIVE_SHIPMENT'),
            ('post_claim', (_shipment('114-S', 'active'),), '114-S', 0, None),
            ('post_claim', (_shipment('115-S', 'active'),), '114-S', 1, 'LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH'),
            ('post_claim', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 1, 'LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS'),
            ('lifecycle', (), '114-S', 1, 'LIFECYCLE_NO_ACTIVE_SHIPMENT'),
            ('lifecycle', (_shipment('114-S', 'active'),), '114-S', 0, None),
            ('lifecycle', (_shipment('115-S', 'active'),), '114-S', 1, 'LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH'),
            ('lifecycle', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 1, 'LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS'),
            ('ambient', (), None, 0, None),
            ('ambient', (_shipment('114-S', 'active'),), '114-S', 0, None),
            ('ambient', (_shipment('115-S', 'active'),), '114-S', 1, 'AMBIENT_ACTIVE_SHIPMENT_MISMATCH'),
            ('ambient', (_shipment('115-S', 'active'),), None, 1, 'AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT'),
            ('ambient', (_shipment('114-S', 'active'), _shipment('115-S', 'active')), '114-S', 1, 'AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS'),
        )
        for phase, shipments, target, exit_code, token in cases:
            with self.subTest(phase=phase, shipments=[s.shipment_id for s in shipments], target=target):
                result = evaluate(
                    TopologyInput(mode='manual', phase=phase, target_shipment_id=target),
                    readers=_FakeReaders(shipments),
                )
                self.assertEqual(result.exit_code, exit_code)
                self.assertEqual(result.primary_token, token)

    def test_ambient_zero_active_differs_from_lifecycle(self) -> None:
        ambient = evaluate(TopologyInput(mode='manual', phase='ambient', target_shipment_id=None), readers=_FakeReaders())
        lifecycle = evaluate(TopologyInput(mode='manual', phase='lifecycle', target_shipment_id='114-S'), readers=_FakeReaders())
        self.assertEqual(ambient.exit_code, 0)
        self.assertEqual(lifecycle.primary_token, 'LIFECYCLE_NO_ACTIVE_SHIPMENT')


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

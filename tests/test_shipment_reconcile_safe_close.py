"""Shipment-reconcile safe-close contract tests for the canonical template."""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _ROOT / 'templates' / 'skills' / 'shipment-reconcile' / 'SKILL.md.tmpl'


def _content() -> str:
    return _TEMPLATE.read_text(encoding='utf-8')


class ShipmentReconcileSafeCloseTests(unittest.TestCase):
    def test_shipment_record_close_uses_non_cascading_ordered_sequence(self) -> None:
        content = _content()
        move_idx = content.index('backlogit move <shipment_id> --status shipped')
        live_verify_idx = content.index('status: shipped', move_idx)
        archive_idx = content.index('backlogit archive <shipment_id>', move_idx)
        archived_verify_idx = content.index('archived_status: shipped', archive_idx)
        self.assertLess(move_idx, archive_idx)
        self.assertLess(move_idx, live_verify_idx)
        self.assertLess(archive_idx, archived_verify_idx)

    def test_sequence_aware_protected_set_requires_verified_predecessor_provenance(self) -> None:
        content = _content()
        self.assertIn('Sequence-aware exclusion', content)
        self.assertIn('archived_status: shipped', content)
        self.assertIn('normalized legacy', content)
        self.assertIn('`done`', content)
        self.assertIn('Mere archive-file presence', content)

    def test_fail_closed_tokens_cover_live_status_and_provenance_failures(self) -> None:
        content = _content()
        self.assertIn('RECONCILE_FAIL_SHIPMENT_RECORD_LIVE_STATUS', content)
        self.assertIn('RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE', content)
        self.assertIn('live+archived duplication', content)

    def test_fail_closed_tokens_cover_pre_close_snapshot_ambiguity_and_absence(self) -> None:
        # 141-S / 132.001-T: Step 0(b)'s pre-close parent_id snapshot now
        # reads from whichever of queue/ or archive/ currently holds a
        # manifest task item (a task item may already be pre-archived when
        # the snapshot runs) and halts fail-closed on an ambiguous or
        # missing record rather than assuming queue/ only.
        content = _content()
        self.assertIn('RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS', content)
        self.assertIn('RECONCILE_FAIL_SNAPSHOT_MISSING', content)
        self.assertIn('already be\n      pre-archived', content)

    def test_scenario_matrix_covers_serial_success_and_negatives(self) -> None:
        content = _content()
        self.assertIn('114-S -> 115-S -> 116-S serial-close success chain', content)
        expected = {
            'archive-while-active': 'archive-while-active',
            'non-shipped-live-before-archive': 'non-shipped-live-before-archive',
            'missing archive': 'missing archive',
            'archived abandoned': 'archived abandoned',
            'missing provenance': 'missing provenance',
        }
        normalized = content.replace('—', ' ')
        for label, phrase in expected.items():
            with self.subTest(phrase=label):
                self.assertIn(phrase, normalized)


if __name__ == '__main__':
    unittest.main()

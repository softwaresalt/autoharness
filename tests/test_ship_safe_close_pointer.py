"""Ship safe-close summary should stay a thin pointer to shipment-reconcile."""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _ROOT / 'templates' / 'agents' / '_ship.agent.md.tmpl'
_MIRROR = _ROOT / '.github' / 'agents' / '_ship.agent.md'


def _template_text() -> str:
    return _TEMPLATE.read_text(encoding='utf-8')


def _mirror_text() -> str:
    return _MIRROR.read_text(encoding='utf-8')


def _files():
    return (('template', _template_text()), ('mirror', _mirror_text()))


class ShipSafeClosePointerTests(unittest.TestCase):
    def test_safe_close_points_to_shipment_reconcile(self) -> None:
        for label, content in _files():
            with self.subTest(file=label):
                self.assertIn('shipment-reconcile', content)
                self.assertIn('thin pointer', content)
                self.assertIn('step-by-step safe-close algorithm lives in the `shipment-reconcile` skill', content)

    def test_self_hosting_note_is_dogfood_only_in_installed_mirror(self) -> None:
        normalized = ' '.join(_mirror_text().split())
        self.assertIn('self-hosting repository', normalized)
        self.assertIn('templates/skills/shipment-reconcile/SKILL.md.tmpl', normalized)
        self.assertIn('not installed as resolved `.github/skills/` copies', normalized)
        self.assertIn('dogfood-only addition', normalized)
        self.assertIn('PR #297 Copilot review', normalized)

    def test_generic_template_does_not_name_dogfood_templates_tree(self) -> None:
        self.assertNotIn('templates/skills/', _template_text())

    def test_summary_names_non_cascading_shipment_record_sequence(self) -> None:
        for label, content in _files():
            with self.subTest(file=label):
                self.assertIn('backlogit move', content)
                self.assertIn('status: shipped', content)
                self.assertIn('backlogit archive <shipment_id>', content)
                self.assertIn('archived_status: shipped', content)

    def test_forbidden_cascade_behavior_is_described_accurately(self) -> None:
        for label, content in _files():
            normalized = ' '.join(content.split())
            with self.subTest(file=label):
                self.assertIn('requeues + detaches unshipped descendant tasks', normalized)
                self.assertIn('`parent_id` cleared', normalized)
                self.assertIn('preserves/restores a non-member covering feature via snapshot', normalized)
                self.assertIn('P-015-forbidden', normalized)


if __name__ == '__main__':
    unittest.main()

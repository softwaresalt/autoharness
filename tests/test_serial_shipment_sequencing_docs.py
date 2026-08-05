"""Serial shipment sequencing docs should reflect queued-from-start semantics."""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_FILES = {
    'orchestrator_template': _ROOT / 'templates' / 'agents' / '_orchestrator.agent.md.tmpl',
    'orchestrator_mirror': _ROOT / '.github' / 'agents' / '_orchestrator.agent.md',
    'ship_template': _ROOT / 'templates' / 'agents' / '_ship.agent.md.tmpl',
    'ship_mirror': _ROOT / '.github' / 'agents' / '_ship.agent.md',
}


def _read(name: str) -> str:
    return _FILES[name].read_text(encoding='utf-8')


class SerialShipmentSequencingDocTests(unittest.TestCase):
    def test_orchestrator_uses_queued_from_start_blocks_model(self) -> None:
        for name in ('orchestrator_template', 'orchestrator_mirror'):
            content = ' '.join(_read(name).split())
            with self.subTest(file=name):
                self.assertIn('Successors stay', content)
                self.assertIn('from creation', content)
                self.assertIn('`blocks` edges', content)
                self.assertIn('never attempt a `blocked ->', content)

    def test_orchestrator_requires_post_predecessor_reload(self) -> None:
        for name in ('orchestrator_template', 'orchestrator_mirror'):
            content = ' '.join(_read(name).split())
            with self.subTest(file=name):
                self.assertIn('reload current `main` agent instructions', content)
                self.assertIn('before advancing the cursor or selecting the next successor shipment', content)
                self.assertIn('P-020 post-merge closure completes', content)

    def test_ship_requires_pre_self_close_reload(self) -> None:
        for name in ('ship_template', 'ship_mirror'):
            content = ' '.join(_read(name).split())
            with self.subTest(file=name):
                self.assertIn('Mandatory pre-self-close context reload', content)
                self.assertIn('re-read the freshly merged `main` Ship agent instructions and the `shipment-reconcile` skill', content)
                self.assertIn('not a stale in-context copy', content)

    def test_valid_transition_rule_is_cited(self) -> None:
        for name in _FILES:
            content = ' '.join(_read(name).split())
            with self.subTest(file=name):
                self.assertIn('2026-05-07-backlogit-shipment-status-constraints.md', content)
                self.assertIn('-> shipped', content)
                self.assertIn('-> abandoned', content)
                self.assertIn('there is no shipment `blocked` lifecycle', content)


if __name__ == '__main__':
    unittest.main()

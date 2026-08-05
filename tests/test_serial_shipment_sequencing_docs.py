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
    'backlogit_template': _ROOT / 'templates' / 'instructions' / 'backlogit.instructions.md.tmpl',
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
                self.assertIn('no shipment-status un-gating transition is performed or required', content)

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
        for name in ('orchestrator_template', 'orchestrator_mirror', 'ship_template', 'ship_mirror'):
            content = ' '.join(_read(name).split())
            with self.subTest(file=name):
                self.assertIn('2026-05-07-backlogit-shipment-status-constraints.md', content)
                self.assertIn('-> shipped', content)
                self.assertIn('-> abandoned', content)
                self.assertIn('there is no shipment `blocked` lifecycle', content)


    def test_ship_and_backlogit_live_guidance_do_not_instruct_blocked_to_queued_transition(self) -> None:
        for name in ('ship_template', 'ship_mirror', 'backlogit_template'):
            content = _read(name)
            with self.subTest(file=name):
                self.assertNotIn('blocked -> queued', content)
                self.assertNotIn('blocked → queued', content)
                self.assertNotIn('blocked to queued', content)

    def test_backlogit_protocol_uses_dependency_gating_not_blocked_status(self) -> None:
        content = ' '.join(_read('backlogit_template').split())
        self.assertIn('there is no separate shipment `blocked` status in backlogit 1.8.0.', content)
        self.assertIn('queued shipment is only ELIGIBLE for claim once every `blocks`-type predecessor', content)
        self.assertIn('no shipment-status mutation is performed or required', content)


if __name__ == '__main__':
    unittest.main()

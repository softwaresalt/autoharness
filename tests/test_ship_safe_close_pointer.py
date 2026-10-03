"""Ship safe-close summary should stay a thin pointer to shipment-reconcile."""

from __future__ import annotations

import re
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

    def test_installed_mirror_directs_to_installed_skills_not_templates(self) -> None:
        """The dogfood mirror must point Ship at the installed, manifest-tracked skills.

        This workspace originally lacked resolved `.github/skills/` copies of
        `shipment-reconcile` and Ship's other referenced skills, so the mirror carried a
        dogfood-only fallback telling the reader to read `templates/skills/...tmpl`
        instead. Those copies are now installed and manifest-tracked, which makes the old
        fallback actively harmful: following it would bypass the installed artifacts and
        their checksum verification. This test pins the corrected direction and guards
        against the stale "not installed" wording being reintroduced.
        """
        normalized = ' '.join(_mirror_text().split())

        # Context and provenance are still explained.
        self.assertIn('self-hosting repository', normalized)
        self.assertIn('PR #297 Copilot review', normalized)

        # The skills are stated as installed, and the reader is sent to them.
        self.assertIn('installed as resolved, manifest-tracked', normalized)
        self.assertIn('manifest-tracked artifacts and their checksum verification', normalized)

        # The stale claims and the misdirection must not come back.
        self.assertNotIn('not installed as resolved `.github/skills/` copies', normalized)
        self.assertNotIn('is not installed as a resolved `.github/skills/` copy', normalized)
        self.assertNotIn('read the authored template at', normalized)

    def test_generic_template_does_not_name_dogfood_templates_tree(self) -> None:
        self.assertNotIn('templates/skills/', _template_text())

    def test_summary_names_non_cascading_shipment_record_sequence(self) -> None:
        for label, content in _files():
            with self.subTest(file=label):
                self.assertIn('backlogit move', content)
                self.assertIn('status: shipped', content)
                self.assertIn('backlogit archive <shipment_id>', content)
                self.assertIn('archived_status: shipped', content)

    def test_cascade_path_is_gated_by_classification_not_prose(self) -> None:
        """The Ship agent's cascade-path summary must reflect the P-015
        flat-manifest/engine-inertness gate: cascade is selected only by the
        classifier, verified against postconditions, and never invoked
        directly from prose judgment."""

        for label, content in _files():
            normalized = ' '.join(content.split())
            with self.subTest(file=label):
                self.assertIn('classif', normalized)
                self.assertIn('engine-inert', normalized)
                self.assertIn('Do NOT call', normalized)
                self.assertIn('only the skill', normalized)
                self.assertIn('returned_ids', normalized)
                self.assertIn('parent_id', normalized)
                self.assertIn('baseline-fingerprint', normalized)
                self.assertIn('halts fail-closed', normalized)
                self.assertNotIn('requeues + detaches unshipped descendant tasks', normalized)
                self.assertNotIn('VERIFIED FULLY-COVERED-ROOT EXCEPTION', normalized)


def _normalized_files():
    return tuple((label, ' '.join(content.split())) for label, content in _files())


class ShipFlatCascadePhraseParityTests(unittest.TestCase):
    """195.013-T: phrase-level parity (never byte parity) between the Ship
    template and its dogfood mirror for the 195.006-T flat-cascade realignment."""

    def test_j1_cascade_bullet_uses_flat_wording(self) -> None:
        for label, normalized in _normalized_files():
            with self.subTest(file=label):
                self.assertIn(
                    'never `validated_linked_deliberations(S)`: the engine leaves '
                    'validated linked deliberations independent, so they are never in '
                    '`allowed_ids(S)` / `required_ids(S)`',
                    normalized,
                )
                self.assertIn(
                    "CASCADE also requires the skill's engine-semantics gate to return "
                    '`VERIFIED` (via `select_close_path`); otherwise the skill selects '
                    '`SAFE_CLOSE`',
                    normalized,
                )
                self.assertNotIn('may be live/required', normalized)
                self.assertNotIn('separate linked-deliberation expansion', normalized)

    def test_j2_safe_close_hands_off_to_disposition_step(self) -> None:
        for label, normalized in _normalized_files():
            with self.subTest(file=label):
                self.assertIn(
                    'out-of-manifest artifacts is still baseline-invariant, then the '
                    "skill's Linked-Deliberation Disposition step.",
                    normalized,
                )
                self.assertIn(
                    'after either close path returns `CLOSED`, runs the path-independent '
                    'Linked-Deliberation Disposition step (P-015 INV-12) before post-mode',
                    normalized,
                )
                self.assertIn(
                    'Ship never proceeds to post-mode directly after `CLOSED`',
                    normalized,
                )
                self.assertIn("the skill's own halt handling governs any rollback", normalized)

    def test_j3_commit_gate_requires_closed_disposition_complete_and_proceed(self) -> None:
        gate = (
            '**only after** safe-close returned `CLOSED`, the Linked-Deliberation '
            'Disposition step returned `DISPOSITION_COMPLETE` (never after a '
            'disposition `HALT`), and post-mode returned `PROCEED`'
        )
        for label, normalized in _normalized_files():
            with self.subTest(file=label):
                self.assertIn(gate, normalized)
                self.assertNotIn(
                    'safe-close returned `CLOSED` and post-mode returned `PROCEED`',
                    normalized,
                )

    def test_j4_role_boundary_carries_inv12_archival_exception(self) -> None:
        row = (
            '| Planning | Read plans and deliberation artifacts for execution context | '
            'Create or modify deliberation, spike, plan, or review artifacts '
            '(P-015 INV-12 archival transitions of validated linked deliberations excepted) |'
        )
        allowed = (
            'archive a validated linked deliberation only through the `shipment-reconcile` '
            'Linked-Deliberation Disposition step (P-015 INV-12), never independently'
        )
        for label, content in _files():
            with self.subTest(file=label):
                self.assertIn(row, content.splitlines())
                backlog_rows = [
                    line for line in content.splitlines() if line.startswith('| Backlog |')
                ]
                self.assertEqual(len(backlog_rows), 1)
                allowed_cell = backlog_rows[0].split(' | ')[1]
                self.assertIn(allowed, allowed_cell)

    def test_k6_mirror_archives_no_deliberation_outside_inv12(self) -> None:
        """The dogfood mirror has no Step 7 deliberation retirement: it never
        calls an item-archive operation, and every line that pairs archival
        with deliberations is scoped to P-015 INV-12."""

        mirror = _mirror_text()
        self.assertNotIn('7. **Source artifact cleanup**', mirror)
        sentences = re.split(r'(?<=[.;!?])\s+', ' '.join(mirror.split()))
        for sentence in sentences:
            if 'backlogit_archive_item' in sentence:
                with self.subTest(sentence=sentence[:80]):
                    self.assertRegex(sentence, r'\bnever\b|INV-12')
        # An archival verb with "deliberation" as its object within a few words
        # (a hard-wrapped sentence is flattened first, so wrapping cannot hide it).
        archival_of_deliberation = re.compile(
            r'\barchiv\w*\s+(?:[\w`-]+\s+){0,4}deliberations?\b', re.IGNORECASE
        )
        paired = [s for s in sentences if archival_of_deliberation.search(s)]
        self.assertTrue(paired, 'expected at least the Role Boundary INV-12 sentences')
        for sentence in paired:
            with self.subTest(sentence=sentence[:80]):
                self.assertIn('INV-12', sentence)

    def test_k5_ship_pair_parity_for_step7_disposition_wording(self) -> None:
        """195.012-T wording: in both files deliberation archival is routed
        only through the INV-12 disposition step, and the withdrawn
        independent archive call is absent; the template's Step 7 consumes
        the report (the mirror has no Step 7 by design, see K-6)."""

        for label, normalized in _normalized_files():
            with self.subTest(file=label):
                self.assertIn(
                    'Linked-Deliberation Disposition step (P-015 INV-12)', normalized
                )
                self.assertNotIn(
                    'If it exists and is not already archived, call `backlogit_archive_item`',
                    normalized,
                )
        template = ' '.join(_template_text().split())
        for phrase in (
            "read the shipment's `linked_deliberation_disposition` report",
            '**never archive**',
            '`skipped_not_in_disposition_report`',
            'copied from the disposition report, never re-derived',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, template)


# 192.022-T (plan A6b): the Ship P-015 post-merge step 2c pointer to
# `autoharness shipment cascade-close` (template step 1.b, mirror step 2.c).
_ROUTING_START = '**Command routing (192-F, pointer only)**'
_ROUTING_END = 'At the summary level, the skill:'
_CASCADE_START = '**`CASCADE` (the narrow P-015 exception)**'
_CASCADE_END = 'invariance (captured before invocation, re-verified after).'
_CONTRACT_MARKER = '**Closure-evidence contract**'
# The only template -> mirror substitutions inside the pinned sections; the
# mirror pins this workspace's rendered values.
_RENDERED_VALUES = {
    '{{OP_SHIP_SHIPMENT_MCP}}': 'backlogit_ship_shipment',
    '{{DOCS_CLOSURE}}': 'docs/closure',
}


def _rendered(text: str) -> str:
    for placeholder, value in _RENDERED_VALUES.items():
        text = text.replace(placeholder, value)
    return text


def _between(normalized: str, start: str, end: str, *, label: str) -> str:
    begin = normalized.find(start)
    if begin < 0:
        raise AssertionError(f'{label}: missing section start {start!r}')
    finish = normalized.find(end, begin)
    if finish < 0:
        raise AssertionError(f'{label}: missing section end {end!r}')
    return normalized[begin:finish + len(end)]


class ShipCascadeClosePointerTests(unittest.TestCase):
    """192.022-T: step 2c routes every close through `cascade-close`."""

    def test_step_2c_pointer_routes_through_cascade_close(self) -> None:
        routing_phrases = (
            ('every close, on either path, starts with '
            '`autoharness shipment cascade-close --classify-only --shipment {shipment_id} '
            '--feature {feature_id} --sha {merge_commit_sha} --json`'),
            '`docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json`',
            ("The command's engine-semantics gate runs no cascade unless "
            '`select_close_path` selects `CASCADE` on a `VERIFIED` engine probed on the '
            'CLI surface the command invokes; otherwise the command exits 3'),
            ('an engine re-probe difference, or any difference from the '
            '`cascade`-selected `--classify-only` record, exits 4 with nothing mutated'),
            ('CASCADE is executed only through the mutating '
            '`autoharness shipment cascade-close` (no `--classify-only`), which needs the '
            'same destructive-command approval as a direct `backlogit shipment ship` call'),
            'is a P-005 deviation whose closure the closure-evidence gate refuses',
            ("the skill's Linked-Deliberation Disposition step (P-015 INV-12) runs with "
            'its inputs from the evidence record and remains the only archiver of a '
            'linked deliberation; the command never archives one'),
            ('The closure artifact records `close_path` (`cascade` or `safe_close`) and '
            '`close_evidence` (the evidence record path)'),
            'The exit-code routing table lives in the `shipment-reconcile` skill, not here.',
        )
        for label, normalized in _normalized_files():
            routing = _between(normalized, _ROUTING_START, _ROUTING_END, label=label)
            cascade = _between(normalized, _CASCADE_START, _CASCADE_END, label=label)
            for phrase in routing_phrases:
                with self.subTest(file=label, phrase=phrase[:60]):
                    self.assertIn(phrase, routing)
            with self.subTest(file=label, section='CASCADE bullet'):
                self.assertIn(
                    'the skill invokes the cascade only through the mutating '
                    '`autoharness shipment cascade-close`, which independently verifies '
                    '`returned_ids` is empty',
                    cascade,
                )
                self.assertNotIn('invokes the cascade operation and', cascade)
            # The routing block precedes the close-path summary it governs.
            with self.subTest(file=label, check='ordering'):
                self.assertLess(normalized.find(_ROUTING_START), normalized.find(_CASCADE_START))

    def test_step_2c_rendered_parity_and_single_line_contract(self) -> None:
        template = ' '.join(_template_text().split())
        mirror = ' '.join(_mirror_text().split())
        for start, end in ((_ROUTING_START, _ROUTING_END), (_CASCADE_START, _CASCADE_END)):
            with self.subTest(section=start):
                self.assertEqual(
                    _rendered(_between(template, start, end, label='template')),
                    _between(mirror, start, end, label='mirror'),
                )
        paragraphs = {}
        for label, content in _files():
            lines = [line.strip() for line in content.splitlines() if _CONTRACT_MARKER in line]
            with self.subTest(file=label, check='single contract line'):
                self.assertEqual(len(lines), 1)
            paragraphs[label] = lines[0]
            for key in (
                '`closure_status`',
                '`compaction_status`',
                '`close_path` (`cascade` or `safe_close`)',
                ('`close_evidence` (the '
                '`docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json` '
                'record path written by `autoharness shipment cascade-close`'),
            ):
                with self.subTest(file=label, key=key[:40]):
                    self.assertIn(key, lines[0])
        self.assertEqual(_rendered(paragraphs['template']), paragraphs['mirror'])


if __name__ == '__main__':
    unittest.main()

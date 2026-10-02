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
        for label, content in _files():
            with self.subTest(file=label):
                self.assertIn(row, content.splitlines())

    def test_k6_mirror_archives_no_deliberation_outside_inv12(self) -> None:
        """The dogfood mirror has no Step 7 deliberation retirement: it never
        calls an item-archive operation, and every line that pairs archival
        with deliberations is scoped to P-015 INV-12."""

        mirror = _mirror_text()
        self.assertNotIn('backlogit_archive_item', mirror)
        self.assertNotIn('7. **Source artifact cleanup**', mirror)
        for line in mirror.splitlines():
            lowered = line.casefold()
            if 'archiv' in lowered and 'deliberation' in lowered:
                with self.subTest(line=line[:80]):
                    self.assertIn('INV-12', line)

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


if __name__ == '__main__':
    unittest.main()

"""Ship claim-integrity guard contract tests (102-F / 106-S).

Covers the two in-repo mitigations for the backlogit
"queued-with-active-work" inconsistency, both authored into the Ship agent
template and its installed dogfood mirror:

* Unit A (102.001-T) -- post-claim shipment-status verification: after the
  claim, re-read the shipment record's own status and assert it reached
  ``active``. Retry the claim exactly once ONLY when the re-read status is
  ``queued``; on any other unexpected shipment status halt immediately with
  ``CLAIM_VERIFY_FAILED`` and NO retry / NO claim. The verify step is sequenced
  AFTER the claim and BEFORE the task-claim step that first moves any task to
  ``active``.

* Unit B (102.002-T) -- queued-with-active-work early-warning: a scan that
  runs immediately after the shipment record is loaded and BEFORE both the
  status/scope validation and the claim, halting with
  ``SHIPMENT_STATE_INCONSISTENT`` when the loaded record is ``queued`` while a
  manifest task is already ``active``/``done``. The scan
  filters ``custom_fields.items`` to task artifacts first so a covering-feature
  entry from a fallback manifest cannot trigger a false halt.

The template form uses ``{{STATUS_*}}`` / ``{{OP_*}}`` placeholders; the
resolved dogfood mirror must carry resolved literal values (no unresolved
``{{VARIABLE}}`` placeholders introduced by these guards). Because shipment
`blocked` is no longer a valid lifecycle state, the template must not carry a
`{{STATUS_BLOCKED}}` branch for these guards.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_MIRROR = _ROOT / ".github" / "agents" / "_ship.agent.md"

# Per-file anchor marking the primary-path shipment claim call. Unit B guards
# must precede it; Unit A guards must follow it.
_CLAIM_ANCHORS = {
    "template": "claim it using",
    "mirror": "backlogit_claim_shipment",
}

# Per-file anchor for the status/scope validation the Unit B early-warning must
# precede (in addition to the claim). Template = the explicit queued/active
# status validation; mirror = the generic scope/status validation step. Without
# this bound the installed mirror could omit validation entirely and stay green.
_VALIDATION_ANCHORS = {
    "template": "Confirm the loaded shipment is in",
    "mirror": "Verify all tasks have clear scope",
}

# Per-file upper bound: the task-claim step that first moves a task to active.
# Unit A's post-claim verify (and its blocked-branch halt) must precede it, so a
# guard cannot be relocated below the task loop and still pass.
_TASKLOOP_ANCHORS = {
    "template": "Step 4.1: Claim Task",
    "mirror": "Move the task to active",
}

# Per-file marker beginning the queued branch of the post-claim verify
# (the retry-once branch).
_QUEUED_BRANCH = {
    "template": "If the re-read status is `{{STATUS_QUEUED}}`",
    "mirror": "If the re-read status is `queued`",
}

# Per-file marker beginning the unexpected-status branch of the post-claim
# verify (the immediate-halt / no-retry branch).
_UNEXPECTED_BRANCH = {
    "template": "If the re-read status is anything other than `{{STATUS_ACTIVE}}` or `{{STATUS_QUEUED}}`",
    "mirror": "If the re-read status is anything other than `active` or `queued`",
}

_CITATION = "docs/compound/2026-05-07-backlogit-shipment-status-constraints.md"


def _files():
    return (
        ("template", _TEMPLATE.read_text(encoding="utf-8"), _CLAIM_ANCHORS["template"]),
        ("mirror", _MIRROR.read_text(encoding="utf-8"), _CLAIM_ANCHORS["mirror"]),
    )


def _indices(haystack: str, needle: str) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        i = haystack.find(needle, start)
        if i == -1:
            return out
        out.append(i)
        start = i + 1


class ShipClaimIntegrityGuardTests(unittest.TestCase):
    def test_claim_verify_token_present_after_claim_before_task_loop(self) -> None:
        """Unit A: CLAIM_VERIFY_FAILED is sequenced AFTER the claim and BEFORE
        the task-claim step that first moves a task to active."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertIn("CLAIM_VERIFY_FAILED", content)
                self.assertIn(anchor, content)
                verify_idx = content.index("CLAIM_VERIFY_FAILED")
                self.assertGreater(
                    verify_idx,
                    content.index(anchor),
                    "post-claim verify must be sequenced AFTER the claim call",
                )
                taskloop = _TASKLOOP_ANCHORS[label]
                self.assertIn(taskloop, content)
                self.assertLess(
                    verify_idx,
                    content.index(taskloop),
                    "post-claim verify must precede the task-claim step that moves a task active",
                )

    def test_unexpected_status_halts_with_no_retry_no_claim(self) -> None:
        """Unit A: the unexpected-status branch halts immediately with no retry /
        no claim, and that guidance stays inside the post-claim verify region."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertIn("no retry, no claim", content)
                unexpected = _UNEXPECTED_BRANCH[label]
                self.assertIn(unexpected, content)
                no_retry_idx = content.index("no retry, no claim")
                self.assertGreater(
                    no_retry_idx,
                    content.index(unexpected),
                    "no-retry/no-claim guidance must live inside the unexpected-status branch",
                )
                self.assertLess(
                    no_retry_idx,
                    content.index(_TASKLOOP_ANCHORS[label]),
                    "no-retry/no-claim guidance must stay within the post-claim verify region",
                )

    def test_retry_only_on_queued(self) -> None:
        """Unit A: retry-once occurs exactly once and is bound to the queued
        branch -- after the queued marker and before the unexpected-status
        branch -- so a regression that widened retry beyond queued would fail."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertEqual(
                    content.count("retry the claim exactly once"),
                    1,
                    "retry instruction must appear exactly once",
                )
                retry_idx = content.index("retry the claim exactly once")
                queued = _QUEUED_BRANCH[label]
                unexpected = _UNEXPECTED_BRANCH[label]
                self.assertIn(queued, content)
                self.assertIn(unexpected, content)
                self.assertGreater(
                    retry_idx,
                    content.index(queued),
                    "retry must be inside the queued branch",
                )
                self.assertLess(
                    retry_idx,
                    content.index(unexpected),
                    "retry must precede the unexpected-status branch (retry only on queued)",
                )

    def test_inconsistency_token_precedes_validation_and_claim(self) -> None:
        """Unit B: SHIPMENT_STATE_INCONSISTENT precedes BOTH the status/scope
        validation and the claim."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertIn("SHIPMENT_STATE_INCONSISTENT", content)
                warn_idx = content.index("SHIPMENT_STATE_INCONSISTENT")
                self.assertLess(
                    warn_idx,
                    content.index(anchor),
                    "intake early-warning must run BEFORE the claim",
                )
                validation = _VALIDATION_ANCHORS[label]
                self.assertIn(validation, content)
                self.assertLess(
                    warn_idx,
                    content.index(validation),
                    "intake early-warning must run BEFORE the status/scope validation",
                )

    def test_early_warning_filters_to_task_artifacts(self) -> None:
        """Unit B: the scan filters items to task artifacts before evaluating
        status, so a covering feature seeded into a fallback manifest cannot
        trigger a false SHIPMENT_STATE_INCONSISTENT halt."""
        for label, content, _ in _files():
            with self.subTest(file=label):
                self.assertIn("task artifacts", content)
                filter_idx = content.index("task artifacts")
                warn_idx = content.index("SHIPMENT_STATE_INCONSISTENT")
                self.assertLess(
                    filter_idx,
                    warn_idx,
                    "the task-artifact filter must be described before the halt condition",
                )

    def test_early_warning_precedes_post_claim_verify(self) -> None:
        """Unit B runs before Unit A (scan at intake, verify after claim)."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertLess(
                    content.index("SHIPMENT_STATE_INCONSISTENT"),
                    content.index("CLAIM_VERIFY_FAILED"),
                    "early-warning (B) must precede post-claim verify (A)",
                )

    def test_guards_cite_shipment_status_constraints_learning(self) -> None:
        """Both guards cite the learning: at least one occurrence in the Unit B
        region (before the claim) and one in the Unit A region (after the claim),
        so removing either guard's citation fails the contract."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                indices = _indices(content, _CITATION)
                self.assertGreaterEqual(
                    len(indices),
                    2,
                    "each guard (Unit A and Unit B) must carry its own citation",
                )
                anchor_idx = content.index(anchor)
                self.assertTrue(
                    any(i < anchor_idx for i in indices),
                    "Unit B guard (before the claim) must cite the learning",
                )
                self.assertTrue(
                    any(i > anchor_idx for i in indices),
                    "Unit A guard (after the claim) must cite the learning",
                )

    def test_template_drops_blocked_status_branches(self) -> None:
        """Unit A/B in the template now model shipment gating without a blocked
        lifecycle state: queued-only early warning plus an unexpected-status halt."""
        content = _TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn("{{STATUS_BLOCKED}}", content)
        self.assertIn("If the loaded shipment record status is `{{STATUS_QUEUED}}` while any manifest task", content)
        self.assertIn("If the re-read status is anything other than `{{STATUS_ACTIVE}}` or `{{STATUS_QUEUED}}`", content)

    def test_mirror_guards_conditioned_on_shipment_exists(self) -> None:
        """The dogfood mirror's generic Work Intake allows a no-shipment path,
        so both new guards must be conditioned on shipment existence (skipped
        when shipment_id is unset) to avoid dereferencing an unset shipment."""
        content = _MIRROR.read_text(encoding="utf-8")
        # Unit B early-warning is guarded before it dereferences the shipment.
        self.assertIn("applies only when a shipment exists", content)
        self.assertLess(
            content.index("applies only when a shipment exists"),
            content.index("SHIPMENT_STATE_INCONSISTENT"),
            "shipment-exists guard must precede the Unit B scan/halt",
        )
        # Unit A post-claim verify is guarded to the claimed-shipment path.
        self.assertIn("applies only when a shipment was claimed", content)
        self.assertLess(
            content.index("applies only when a shipment was claimed"),
            content.index("CLAIM_VERIFY_FAILED"),
            "claimed-shipment guard must precede the Unit A verify/halt",
        )

    def test_mirror_has_no_template_placeholder_carryover(self) -> None:
        """The installed dogfood mirror must resolve all template placeholders.

        The guards use ``{{STATUS_*}}`` / ``{{OP_*}}`` placeholders in the
        template form; the resolved dogfood mirror must never carry them over
        (the literal ``{{VARIABLE}}`` doc example elsewhere in the file is not a
        template variable and is intentionally excluded). ``{{STATUS_BLOCKED}}``
        is included because blocked is a registered status customization.
        """
        content = _MIRROR.read_text(encoding="utf-8")
        for placeholder in (
            "{{STATUS_QUEUED}}",
            "{{STATUS_ACTIVE}}",
            "{{STATUS_DONE}}",
            "{{OP_CLAIM_SHIPMENT_MCP}}",
            "{{OP_GET_SHIPMENT_MCP}}",
        ):
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(placeholder, content)


if __name__ == "__main__":
    unittest.main()

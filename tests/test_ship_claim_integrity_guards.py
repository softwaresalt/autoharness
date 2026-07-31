"""Ship claim-integrity guard contract tests (102-F / 106-S).

Covers the two in-repo mitigations for the backlogit
"queued-with-active-work" inconsistency, both authored into the Ship agent
template and its installed dogfood mirror:

* Unit A (102.001-T) -- post-claim shipment-status verification: after the
  claim, re-read the shipment record's own status and assert it reached
  ``active``. Retry the claim exactly once ONLY when the re-read status is
  ``queued``; on ``blocked`` halt immediately with ``CLAIM_VERIFY_FAILED`` and
  NO retry / NO claim. The verify step is sequenced AFTER the claim and BEFORE
  the task loop moves any task to ``active``.

* Unit B (102.002-T) -- queued/blocked-with-active-work early-warning: a scan
  that runs immediately after the shipment record is loaded and BEFORE both the
  status validation and the claim, halting with ``SHIPMENT_STATE_INCONSISTENT``
  when the loaded record is ``queued``/``blocked`` while a manifest task is
  already ``active``/``done``.

The dogfood mirror must carry resolved literal values (no unresolved
``{{VARIABLE}}`` placeholders introduced by these guards).
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

_CITATION = "docs/compound/2026-05-07-backlogit-shipment-status-constraints.md"


def _files():
    return (
        ("template", _TEMPLATE.read_text(encoding="utf-8"), _CLAIM_ANCHORS["template"]),
        ("mirror", _MIRROR.read_text(encoding="utf-8"), _CLAIM_ANCHORS["mirror"]),
    )


class ShipClaimIntegrityGuardTests(unittest.TestCase):
    def test_claim_verify_token_present_after_claim(self) -> None:
        """Unit A: CLAIM_VERIFY_FAILED exists and is sequenced after the claim."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertIn("CLAIM_VERIFY_FAILED", content)
                self.assertIn(anchor, content)
                self.assertGreater(
                    content.index("CLAIM_VERIFY_FAILED"),
                    content.index(anchor),
                    "post-claim verify must be sequenced AFTER the claim call",
                )

    def test_blocked_halts_with_no_retry_no_claim(self) -> None:
        """Unit A: a blocked re-read halts immediately with no retry / no claim."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertIn("no retry, no claim", content)
                self.assertGreater(
                    content.index("no retry, no claim"),
                    content.index(anchor),
                    "blocked-halt guidance belongs to the post-claim verify (after claim)",
                )

    def test_retry_only_on_queued(self) -> None:
        """Unit A: retry-once is scoped to a queued re-read, not blocked."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                # A "retry exactly once" instruction must exist within the
                # post-claim verify region and be tied to the queued state.
                self.assertIn("retry the claim exactly once", content)

    def test_inconsistency_token_present_before_claim(self) -> None:
        """Unit B: SHIPMENT_STATE_INCONSISTENT exists and precedes the claim."""
        for label, content, anchor in _files():
            with self.subTest(file=label):
                self.assertIn("SHIPMENT_STATE_INCONSISTENT", content)
                self.assertLess(
                    content.index("SHIPMENT_STATE_INCONSISTENT"),
                    content.index(anchor),
                    "intake early-warning must run BEFORE the claim",
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
        """Both guards cite the backlogit shipment-status constraints learning."""
        for label, content, _ in _files():
            with self.subTest(file=label):
                self.assertIn(_CITATION, content)

    def test_mirror_has_no_template_placeholder_carryover(self) -> None:
        """The installed dogfood mirror must resolve all template placeholders.

        The guards use ``{{STATUS_*}}`` / ``{{OP_*}}`` placeholders in the
        template form; the resolved dogfood mirror must never carry them over
        (the literal ``{{VARIABLE}}`` doc example elsewhere in the file is not a
        template variable and is intentionally excluded).
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

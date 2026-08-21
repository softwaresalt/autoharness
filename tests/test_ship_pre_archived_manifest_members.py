"""Discriminating regression coverage for the Ship pre-archived
manifest-member execution-exclusion contract (139-F / 139.002-T, stash
B19E9662, deliberation 022-DL).

This module pins the EXECUTION-side contract added to both Ship agent files
by 139.001-T: the shipment manifest (`custom_fields.items`) is the closure
membership record, never the executable task set, and Ship must derive the
executable task set by filtering to task artifacts (`-T`, covering feature
resolved via `parent_id`) BEFORE reading status, then applying an exhaustive
positive status rule -- keep `queued`/`active`; skip-and-report `archived` as
`pre_archived_skipped`; report an already-`done` member separately as
`already_done`; any other/missing/unreadable status is a fail-closed halt --
while never suppressing the pre-existing Step 0.5 item 1a
`SHIPMENT_STATE_INCONSISTENT` early-warning, and halting (never advancing to
build/PR/closure) when the derived executable set is empty over a non-empty
manifest.

Assertion A2 is a NEGATIVE CONTROL and is written to be discriminating rather
than vacuous: it asserts the installed mirror no longer contains the pre-fix
unconditional loop-header formulation "each task in the shipment/feature"
(with no derivation preamble), which is the exact text that was live in
`.github/agents/_ship.agent.md` Step 2 at HEAD `e88a8d62` (PR #375) before
this task's fix landed. Run against that pre-fix HEAD, A2 FAILS -- proving the
guard actually discriminates the fixed contract from the broken one, not just
restates prose that was already present.

CLOSURE-SIDE INVARIANT (explicitly NOT re-tested here, per plan amendment
A3.1 / review finding P1-1): the closure-classifier invariant that
`classify_shipment_close_path` still returns the CASCADE verdict for a
manifest containing pre-archived members is ALREADY pinned and green in
`tests/test_shipment_closure_classification.py`, specifically:

* `test_mixed_pre_archived_and_queued_manifest_members_still_selects_cascade`
  (queued feature + mixed queued/pre-archived children -> CASCADE; the exact
  144-S shape)
* `test_feature_queued_children_pre_archived_still_selects_cascade`
* `test_feature_pre_archived_children_queued_still_selects_cascade`
* `test_all_manifest_members_pre_archived_still_selects_cascade`
* `test_pre_archived_out_of_manifest_child_falls_back_to_safe_close`

Those tests shipped with feature 132-F / shipment 141-S out of archived stash
`EDE3CC2D`. This module adds NO new `classify_shipment_close_path` test and
must never be "simplified" into doing so. The execution-side exclusion added
here must never be "fixed" later by stripping pre-archived members back out
of a manifest -- the manifest keeps them for closure; only the executable-set
derivation excludes them from execution.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_MIRROR = _ROOT / ".github" / "agents" / "_ship.agent.md"


def _template_text() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def _mirror_text() -> str:
    return _MIRROR.read_text(encoding="utf-8")


def _files():
    return (("template", _template_text()), ("mirror", _mirror_text()))


def _norm(text: str) -> str:
    return " ".join(text.split())


class ShipPreArchivedExecutionExclusionContractTests(unittest.TestCase):
    def test_a1_contract_present_both_files(self) -> None:
        """A1: both files declare the executable-task-set derivation, the
        explicit pre-archived exclusion, the exhaustive status rule, the -T
        artifact-type filter preceding status reads with the covering feature
        resolved via parent_id, and that the manifest is the closure
        membership record rather than the executable set."""
        for label, content in _files():
            normalized = _norm(content)
            with self.subTest(file=label):
                self.assertIn("closure membership record", normalized)
                self.assertIn("executable task set", normalized)
                self.assertIn("pre_archived_skipped", normalized)
                self.assertIn("already_done", normalized)
                self.assertIn(
                    "artifact-type filtering always precedes any status read",
                    normalized.lower(),
                )
                self.assertIn("resolved through `parent_id`", normalized)
                self.assertIn("097-S task-only-manifest precedent", normalized)
                self.assertIn("ANY OTHER, MISSING, OR UNREADABLE", normalized)
                self.assertIn("FAIL-CLOSED HALT", normalized)

    def test_a2_negative_control_mirror_no_longer_unconditional(self) -> None:
        """A2 (NEGATIVE CONTROL, mirror only): the pre-fix unconditional loop
        header "each task in the shipment/feature" with no derivation
        preamble is no longer present in the installed mirror. Run against
        the pre-fix HEAD e88a8d62 text, this assertion FAILS -- that is what
        makes it discriminating rather than vacuous."""
        mirror = _mirror_text()
        self.assertNotIn("each task in the shipment/feature", mirror)
        # The fixed contract must still iterate *something* -- prove the loop
        # header was reworded to the derived set, not simply deleted.
        self.assertIn("For each task in the derived executable task set", mirror)

    def test_a3_pre_archived_tolerated_not_fatal_both_files(self) -> None:
        """A3: both files state a pre-archived member is expected and
        tolerated and does not halt the run."""
        for label, content in _files():
            normalized = _norm(content)
            with self.subTest(file=label):
                self.assertIn("EXPECTED AND TOLERATED", normalized)
                self.assertIn("must not halt the run", normalized)
                self.assertIn("never claimed", normalized)
                self.assertIn("never unarchived", normalized)
                self.assertIn("never removed from the manifest", normalized)

    def test_a4_empty_executable_set_halts_both_files(self) -> None:
        """A4: an empty executable set over a non-empty manifest halts and
        reports, never advances to build/PR, and never triggers a closure
        path."""
        for label, content in _files():
            normalized = _norm(content)
            with self.subTest(file=label):
                self.assertIn("EMPTY while the manifest is non-empty", normalized)
                self.assertIn("do NOT advance to build or PR", normalized)
                self.assertIn("do NOT trigger any closure path", normalized)
                self.assertIn("operator-disposition case only", normalized)

    def test_a6_unchanged_ordering_and_distinct_reporting_both_files(self) -> None:
        """A6: the Step 0.5 item 1a early-warning is stated to be unchanged
        and to run strictly before the derivation, and already_done is
        reported distinctly from pre_archived_skipped."""
        for label, content in _files():
            normalized = _norm(content)
            with self.subTest(file=label):
                self.assertIn("item 1a queued-with-active-work early-warning is", normalized)
                self.assertIn("strictly BEFORE this derivation", normalized)
                self.assertIn(
                    "never suppresses, replaces, softens, or pre-empts item 1a's",
                    normalized,
                )
                self.assertIn(
                    "`already_done` and `pre_archived_skipped` are distinct reported outcomes",
                    normalized,
                )
                self.assertIn(
                    "must never be laundered as a tolerated pre-archived skip",
                    normalized,
                )

    def test_a7_template_introduces_no_status_archived_variable(self) -> None:
        """A7: the template contains no `{{STATUS_ARCHIVED}}` token (and no
        other newly introduced unresolved variable for the archived state)."""
        content = _template_text()
        self.assertNotIn("{{STATUS_ARCHIVED}}", content)


if __name__ == "__main__":
    unittest.main()

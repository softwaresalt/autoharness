"""Pipeline-topology gate wiring contract tests for the Ship and Orchestrator
agents (115-S / 109.017-T + 109.018-T).

These tests prove that ``autoharness gate pipeline-topology`` is wired into
Ship's own lifecycle (branch/worktree creation, claim, build, PR creation,
closure/safe-close) and into Orchestrator's route-to-Ship eligibility check and
multi-shipment cursor-advance, with the exact ordering and bounded-retry
contract described in the 109.017-T / 109.018-T acceptance criteria:

* Branch/worktree creation is always ``pre_claim`` -- it precedes the claim
  and is never ``post_claim``.
* A second ``pre_claim`` re-check narrows the TOCTOU window immediately before
  the claim.
* The claim is immediately followed by a GLOBAL ``post_claim`` verification
  (all shipments, not just target-status).
* A ``CLAIM_NOT_OBSERVED`` verdict at that immediate post-claim point is the
  ONLY retry-required outcome, handled by a bounded, double-claim-guarded
  reclaim-and-reverify cycle that reuses the pre-existing backlogit
  re-read/retry-once logic rather than introducing a new claim primitive,
  CAS, or lease -- and runs at most once.
* Every OTHER non-zero verdict (any phase, any invocation point) is terminal
  -- no retry, no reclaim.
* Build, PR creation, and closure/safe-close each get their own preceding
  ``lifecycle`` gate call.
* A bootstrap exemption is documented so the shipments that build this gate
  are not blocked by an as-yet-uninstalled gate.
* Orchestrator gates the route-to-Ship eligibility check and the
  multi-shipment cursor-advance with their own ``pre_claim`` calls against the
  candidate/successor shipment ID.

Both the installed dogfood mirror (``.github/agents/_ship.agent.md`` /
``.github/agents/_orchestrator.agent.md``) and the generic exportable
templates (``templates/agents/_ship.agent.md.tmpl`` /
``templates/agents/_orchestrator.agent.md.tmpl``) are covered -- the template
form gates its wiring on gate installation ("if the `pipeline-topology` gate
is installed for this workspace"), since other consuming workspaces may not
have adopted the gate.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

_SHIP_MIRROR = _ROOT / ".github" / "agents" / "_ship.agent.md"
_SHIP_TEMPLATE = _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_ORCH_MIRROR = _ROOT / ".github" / "agents" / "_orchestrator.agent.md"
_ORCH_TEMPLATE = _ROOT / "templates" / "agents" / "_orchestrator.agent.md.tmpl"

_PRE_CLAIM_BEFORE_BRANCH = "TOPOLOGY_GATE: pre_claim (before branch/worktree creation)"
_PRE_CLAIM_BEFORE_CLAIM = "TOPOLOGY_GATE: pre_claim (immediately before claim)"
_POST_CLAIM_GLOBAL = "TOPOLOGY_GATE: post_claim (immediately after claim, GLOBAL verification)"
_LIFECYCLE_BEFORE_BUILD = "TOPOLOGY_GATE: lifecycle (before build)"
_LIFECYCLE_BEFORE_PR = "TOPOLOGY_GATE: lifecycle (before PR creation)"
_LIFECYCLE_BEFORE_CLOSURE = "TOPOLOGY_GATE: lifecycle (before closure/safe-close)"

# Per-file anchor for the actual claim mutation call, and the branch-created
# marker, used to bound the pre_claim ordering.
_CLAIM_ANCHORS = {
    "ship_mirror": "backlogit_claim_shipment",
    "ship_template": "claim it using",
}
_BRANCH_CREATED = "BRANCH_CREATED"


def _ship_files():
    return (
        ("ship_mirror", _SHIP_MIRROR.read_text(encoding="utf-8")),
        ("ship_template", _SHIP_TEMPLATE.read_text(encoding="utf-8")),
    )


def _orch_files():
    return (
        ("orch_mirror", _ORCH_MIRROR.read_text(encoding="utf-8")),
        ("orch_template", _ORCH_TEMPLATE.read_text(encoding="utf-8")),
    )


class ShipTopologyGateWiringOrderingTests(unittest.TestCase):
    """Proves the full topology-gate invocation chain is present, in order, in
    both the installed Ship mirror and the generic Ship template."""

    def test_all_gate_markers_present(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                for marker in (
                    _PRE_CLAIM_BEFORE_BRANCH,
                    _PRE_CLAIM_BEFORE_CLAIM,
                    _POST_CLAIM_GLOBAL,
                    _LIFECYCLE_BEFORE_BUILD,
                    _LIFECYCLE_BEFORE_PR,
                    _LIFECYCLE_BEFORE_CLOSURE,
                ):
                    self.assertIn(marker, content, f"missing marker: {marker}")

    def test_pre_claim_gate_precedes_branch_created_precedes_second_pre_claim(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                first_pre_claim_idx = content.index(_PRE_CLAIM_BEFORE_BRANCH)
                branch_created_idx = content.index(_BRANCH_CREATED)
                second_pre_claim_idx = content.index(_PRE_CLAIM_BEFORE_CLAIM)
                self.assertLess(
                    first_pre_claim_idx,
                    branch_created_idx,
                    "pre_claim (before branch/worktree) must precede BRANCH_CREATED",
                )
                self.assertLess(
                    branch_created_idx,
                    second_pre_claim_idx,
                    "BRANCH_CREATED must precede the second pre_claim re-check",
                )

    def test_second_pre_claim_precedes_claim_precedes_post_claim(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                key = "ship_mirror" if label == "ship_mirror" else "ship_template"
                claim_anchor = _CLAIM_ANCHORS[key]
                second_pre_claim_idx = content.index(_PRE_CLAIM_BEFORE_CLAIM)
                claim_idx = content.index(claim_anchor)
                post_claim_idx = content.index(_POST_CLAIM_GLOBAL)
                self.assertLess(
                    second_pre_claim_idx,
                    claim_idx,
                    "second pre_claim re-check must precede the claim call",
                )
                self.assertLess(
                    claim_idx,
                    post_claim_idx,
                    "the claim call must precede the immediate GLOBAL post_claim verification",
                )

    def test_post_claim_precedes_lifecycle_build_pr_closure_in_order(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                post_claim_idx = content.index(_POST_CLAIM_GLOBAL)
                build_idx = content.index(_LIFECYCLE_BEFORE_BUILD)
                pr_idx = content.index(_LIFECYCLE_BEFORE_PR)
                closure_idx = content.index(_LIFECYCLE_BEFORE_CLOSURE)
                self.assertLess(post_claim_idx, build_idx)
                self.assertLess(build_idx, pr_idx)
                self.assertLess(pr_idx, closure_idx)

    def test_branch_worktree_creation_never_labeled_post_claim(self) -> None:
        """Branch/worktree creation is pre_claim -- it must never precede the
        immediate post_claim GLOBAL verification while being itself labeled
        post_claim, and BRANCH_CREATED must not appear after post_claim."""
        for label, content in _ship_files():
            with self.subTest(file=label):
                branch_created_idx = content.index(_BRANCH_CREATED)
                post_claim_idx = content.index(_POST_CLAIM_GLOBAL)
                self.assertLess(
                    branch_created_idx,
                    post_claim_idx,
                    "branch/worktree creation (BRANCH_CREATED) must precede post_claim, never follow it",
                )


class ShipClaimNotObservedReclaimContractTests(unittest.TestCase):
    """Proves the bounded, double-claim-guarded CLAIM_NOT_OBSERVED reclaim
    sequence is present, ordered, reuses the existing retry-once logic, is
    confined to the immediate post-claim point, and never applies to any
    other verdict."""

    def test_claim_not_observed_is_the_only_retry_required_token(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                self.assertIn("CLAIM_NOT_OBSERVED", content)
                self.assertIn("retry_required", content)
                self.assertIn("not** `blocked`", content)

    def test_double_claim_guard_present_and_reuses_retry_once_logic(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                self.assertIn("double-claim guard".casefold(), content.casefold())
                self.assertIn("retry the claim exactly once", content)
                self.assertIn("new claim primitive", content)

    def test_reclaim_sequence_is_bounded_to_one_cycle(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                self.assertIn("at most once", content)
                # A second CLAIM_NOT_OBSERVED (or ambiguity) is terminal -- the
                # bound is exhausted, never a further retry.
                self.assertIn("bound exhausted", content)

    def test_other_verdicts_remain_terminal_no_retry_no_reclaim(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                self.assertIn("no retry, no reclaim", content)
                self.assertIn("no retry, no claim", content)

    def test_reclaim_sequence_confined_between_post_claim_and_lifecycle_build(self) -> None:
        """The reclaim mechanics (double-claim guard, bound exhaustion) live
        inside item 5 (post_claim), strictly before the lifecycle-before-build
        gate -- they must not leak into pre_claim, lifecycle, build, PR, or
        closure sections."""
        for label, content in _ship_files():
            with self.subTest(file=label):
                post_claim_idx = content.index(_POST_CLAIM_GLOBAL)
                build_idx = content.index(_LIFECYCLE_BEFORE_BUILD)
                folded = content.casefold()
                guard_idx = folded.index("double-claim guard")
                bound_idx = folded.index("bound exhausted")
                self.assertGreater(guard_idx, post_claim_idx)
                self.assertLess(guard_idx, build_idx)
                self.assertGreater(bound_idx, post_claim_idx)
                self.assertLess(bound_idx, build_idx)

    def test_bootstrap_exemption_documented(self) -> None:
        for label, content in _ship_files():
            with self.subTest(file=label):
                self.assertIn("Bootstrap exemption", content)
                self.assertIn("as-yet-uninstalled gate", content)

    def test_queued_branch_reruns_pre_claim_before_reclaim_no_dangling_reference(self) -> None:
        """Regression test for code-review Issue 2: the reclaim sequence must
        re-verify the full pre_claim GLOBAL check before retrying the claim
        (never reclaim into an invalidated topology), and must not reference
        a post_claim re-check that is only defined inside the
        mutually-exclusive 'active' branch."""
        for label, content in _ship_files():
            with self.subTest(file=label):
                collapsed = " ".join(content.split())
                self.assertIn("re-run the full `--phase pre_claim`", collapsed)
                self.assertIn("GLOBAL", collapsed)
                self.assertIn("never reclaim into", collapsed)
                self.assertNotIn(
                    "first `--phase post_claim` re-check (above)", collapsed
                )


class OrchestratorTopologyGateWiringTests(unittest.TestCase):
    """Proves the Orchestrator's route-to-Ship eligibility check and
    multi-shipment cursor-advance are each gated by their own pre_claim call
    against the candidate/successor shipment ID, ordered correctly, and
    confined to Step 2/Step 3 (before Step E1)."""

    _ROUTE_MARKER = "TOPOLOGY_GATE: pre_claim (route-to-Ship eligibility, before invocation)"
    _CURSOR_MARKER = "TOPOLOGY_GATE: pre_claim (cursor-advance eligibility check)"

    def test_markers_present(self) -> None:
        for label, content in _orch_files():
            with self.subTest(file=label):
                self.assertIn(self._ROUTE_MARKER, content)
                self.assertIn(self._CURSOR_MARKER, content)

    def test_route_gate_precedes_ship_invocation(self) -> None:
        for label, content in _orch_files():
            with self.subTest(file=label):
                route_idx = content.index(self._ROUTE_MARKER)
                invoke_idx = content.index("Invoke the **Ship** subagent")
                self.assertLess(
                    route_idx,
                    invoke_idx,
                    "route-to-Ship pre_claim gate must precede Ship invocation",
                )

    def test_route_gate_targets_candidate_not_ambient(self) -> None:
        for label, content in _orch_files():
            with self.subTest(file=label):
                route_idx = content.index(self._ROUTE_MARKER)
                snippet = content[route_idx : route_idx + 700]
                self.assertIn("candidate_shipment_id", snippet)
                self.assertIn("not a bare ambient/no-shipment call", snippet)

    def test_cursor_gate_follows_cursor_advance_and_precedes_step_e1(self) -> None:
        for label, content in _orch_files():
            with self.subTest(file=label):
                cursor_advance_idx = content.index("Advance the multi-shipment cursor")
                cursor_gate_idx = content.index(self._CURSOR_MARKER)
                step_e1_heading_idx = content.index("### Step E1", cursor_gate_idx)
                self.assertLess(
                    cursor_advance_idx,
                    cursor_gate_idx,
                    "cursor-advance pre_claim gate must follow the cursor-advance description",
                )
                self.assertLess(
                    cursor_gate_idx,
                    step_e1_heading_idx,
                    "cursor-advance pre_claim gate must stay within Step 3, before the Step E1 heading",
                )

    def test_cursor_gate_targets_next_shipment_not_ambient(self) -> None:
        for label, content in _orch_files():
            with self.subTest(file=label):
                cursor_gate_idx = content.index(self._CURSOR_MARKER)
                snippet = content[cursor_gate_idx : cursor_gate_idx + 700]
                self.assertIn("next_shipment_id", snippet)

    def test_bootstrap_exemption_documented(self) -> None:
        for label, content in _orch_files():
            with self.subTest(file=label):
                self.assertIn("Bootstrap exemption", content)


if __name__ == "__main__":
    unittest.main()

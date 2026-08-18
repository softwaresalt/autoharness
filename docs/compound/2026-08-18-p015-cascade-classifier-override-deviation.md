---
title: "140-S closure overrode a CASCADE classifier verdict with manual safe-close — a P-005 process deviation, not a permitted fallback"
description: "The shipment-reconcile contract requires close-path selection to be made only from the machine-checkable classifier result; a CASCADE verdict must skip directly to the Cascade Close Sub-Procedure with no documented exception for pre-archived manifest items. 140-S's closure deviated from this by substituting manual safe-close, an undocumented judgment call that is disclosed here as a tracked residual rather than left as an unrecorded precedent."
problem_type: "process-deviation"
category: "shipment-reconcile-close-path-contract"
component: "ship-agent-post-merge-closure"
root_cause: "The Cascade Close Sub-Procedure (templates/skills/shipment-reconcile/SKILL.md.tmpl) has no documented handling for manifest items that are already individually archived before the shipment-level closure step runs, unlike safe-close's explicit `pre-archived` classification (step 4). Faced with that gap, the 140-S closure session chose to substitute manual safe-close for the classifier-selected CASCADE path rather than halting on the unresolved contract gap, contradicting the contract's own 'close-path selection is made only from the classifier result, never inferred from prose' rule."
resolution_type: "residual-risk-disclosure"
severity: "medium"
tags:
  - "ship"
  - "P-015"
  - "P-005"
  - "shipment-reconcile"
  - "close-path-contract"
  - "140-S"
  - "131-F"
citations:
  - "PR #361 (140-S/131-F post-merge closure), Copilot review thread on docs/closure/140-S-131-F-post-merge-closure.md line 70"
  - "templates/skills/shipment-reconcile/SKILL.md.tmpl:403-410,736-738"
  - "templates/policies/workflow-policies.md.tmpl:445"
  - "src/autoharness/gates/shipment_closure.py: classify_shipment_close_path, _read_artifact_record"
---

# 140-S Closure Overrode a CASCADE Classifier Verdict — Tracked Residual

## Context

During shipment 140-S's post-merge closure, `classify_shipment_close_path`
was run over the manifest (`131-F` + `131.001-T`) and returned **CASCADE**:
the covering feature `131-F` is a root member with its only child
(`131.001-T`) also present in the manifest, satisfying the P-015 verified
fully-covered-root exception's structural preconditions.

However, at the time closure ran, both manifest items had already been
individually archived via the standard Step 2 task-completion sequence
(`backlogit move --status done`, auto-relocated to `archive/` by the
registry's routing rules) — this happened *during task execution*, before
the shipment-level closure step began. The closure session judged this
pre-archived state to be an "unresolved precondition" that permitted a
fallback to manual safe-close instead of the classifier-selected cascade
path, and executed manual safe-close.

**This was incorrect.** The canonical contract is explicit and leaves no
room for this substitution:

* `templates/skills/shipment-reconcile/SKILL.md.tmpl:737`: "Close-path
  selection is made **only** from the machine-checkable classification
  result (Step 0), never inferred from prose or manifest shape alone; any
  classifier error, ambiguity, or unresolved precondition falls back to
  safe-close" — but the classifier itself returned a clean `CASCADE`
  result with **no** error, ambiguity, or precondition failure. The
  "unresolved precondition" language in the contract governs the
  classifier's own inputs (e.g. a malformed manifest item, an unreadable
  backlog record), not a downstream human second-guessing of a clean
  verdict based on an unrelated runtime detail.
* `_read_artifact_record` (`src/autoharness/gates/shipment_closure.py`),
  the classifier's own record lookup, already reads from **both**
  `queue/` and `archive/` — so a manifest item already being archived does
  not, by itself, create any classifier-level ambiguity. The classifier's
  `CASCADE` verdict already accounted for the archived state of its inputs.
* `templates/skills/shipment-reconcile/SKILL.md.tmpl:403-406`: "CASCADE
  selected → skip directly to the Cascade Close Sub-Procedure ... in place
  of steps 1–10" — unconditional, with no carve-out for pre-archived
  manifest items.

The real gap is narrower than the closure session assumed: the **Cascade
Close Sub-Procedure itself** (unlike safe-close) has no documented
tolerance for a manifest item that is already archived before
`{{OP_SHIP_SHIPMENT_MCP}}` runs — its step 3 post-condition
(`archived_ids` must match the manifest exactly) is written assuming the
cascade operation performs the archival itself. Whether the underlying
`backlogit shipment ship` operation is idempotent/tolerant of already-
archived manifest members was not verified before manual safe-close was
substituted.

## The rule (corrected)

When `classify_shipment_close_path` returns `CASCADE` and one or more
manifest items are already archived before the closure step runs:

1. **Do not silently substitute safe-close.** This is a process deviation
   from the close-path contract, not a permitted fallback, regardless of
   how defensible the judgment feels in the moment.
2. **Halt and disclose the gap** instead: the correct response to an
   unresolved tension between the classifier's clean verdict and an
   undocumented Cascade Close Sub-Procedure behavior is to treat it as an
   **open contract question**, not to resolve it unilaterally by picking
   the other path. Record a P-005-style process-deviation note the moment
   this tension is discovered, before proceeding either direction.
3. **Escalate a contract fix**: the `shipment-reconcile` skill's Cascade
   Close Sub-Procedure should be extended (a Stage-sized template/contract
   change) to explicitly classify pre-archived manifest items the same way
   safe-close's step 4 already does — tolerate them without re-archiving,
   and adjust the `archived_ids` exact-match post-condition to account for
   items that were already archived before the cascade operation ran.
4. If, after that contract extension exists, a genuine ambiguity remains
   (e.g. the cascade operation errors on an already-archived item with no
   graceful handling), *that* is a legitimate "unresolved precondition"
   the existing contract language already routes to safe-close — but only
   once the contract itself documents this case, not as an ad hoc judgment
   call made without updating the contract.

## Disposition for 140-S

No corrective action is required for shipment 140-S itself: the final
archived backlog state was independently verified against the safe-close
data-integrity invariants (protected set intact — trivially, since it was
empty — live-status verification before archive, and `archived_status:
shipped` provenance confirmed). The **process**, not the **outcome**, was
non-compliant. `docs/closure/140-S-131-F-post-merge-closure.md` has been
updated (in this same PR, #361) to disclose this deviation explicitly and
to stop claiming P-015-compliant reconciliation for the close path as
executed.

## Follow-up (Stage-owned, not opened by Ship)

A concrete backlog item is recommended for a future Stage triage/planning
session to size and schedule: extend the `shipment-reconcile` skill's
Cascade Close Sub-Procedure to explicitly handle pre-archived manifest
items (mirroring safe-close's `pre-archived` classification), so that a
future `CASCADE` verdict with pre-archived manifest items has a documented,
contract-compliant path rather than requiring an ad hoc deviation. Ship's
Role Boundary forbids creating backlog items or editing plan/skill
contract templates directly (P-010); this note is the tracked residual-risk
record until a Stage session opens and sizes the actual follow-up item. No
specific backlog ID exists yet — none is invented here.

## Applicability

Any Ship session running `shipment-reconcile` in `mode: safe-close` whose
Step 0 classification returns `CASCADE` must follow the Cascade Close
Sub-Procedure as written, even when manifest items are already archived.
If that produces an unhandled error or ambiguity, halt and disclose rather
than silently falling back to manual safe-close.


## Update (141-S / 132-F closure, stash EDE3CC2D): follow-up implemented, one prior speculation disproven

The "Follow-up (Stage-owned, not opened by Ship)" section above recommended
extending the Cascade Close Sub-Procedure to explicitly handle pre-archived
manifest items. Shipment **141-S** (feature **132-F**, stash **EDE3CC2D**)
implemented exactly this:

* `templates/skills/shipment-reconcile/SKILL.md.tmpl` now carries an
  **unnumbered preamble** before the Cascade Close Sub-Procedure's step 1
  that: classifies each manifest member `queued` vs `pre-archived`; states a
  `pre-archived` member is expected/tolerated and does not disqualify
  `CASCADE` or authorize a safe-close fallback; cites empirical spike
  evidence for the cascade operation's idempotency over pre-archived
  members; and restates the no-substitution rule (a `CASCADE` verdict is
  final once selected — manual safe-close substitution before invocation is
  a P-005 deviation, symmetric with step 2's existing post-execution rule).
* `templates/policies/workflow-policies.md.tmpl`'s P-015 "VERIFIED
  FULLY-COVERED-ROOT EXCEPTION" block gained a mirrored item 7 stating the
  same tolerance and no-substitution rule at the policy level.
* `tests/test_shipment_closure_classification.py` gained 9 regression tests
  (7 from 132.003-T's original commit + 2 Copilot-review-driven additions)
  proving `classify_shipment_close_path` already returns `CASCADE`
  correctly regardless of which manifest members (feature, children, or
  both) are pre-archived, and correctly still falls back to `SAFE_CLOSE`
  when a real out-of-manifest child exists even if the feature record
  itself is pre-archived.

**One prior speculation in this document is corrected, not merely
implemented as originally worded.** Point 3 under "The rule (corrected)"
above speculated the fix might need to "adjust the `archived_ids`
exact-match post-condition to account for items that were already archived
before the cascade operation ran" — implying the exact-match check itself
might need to be relaxed or made conditional. **This is disproven.** The
141-S spike (`docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`)
found that `backlogit shipment ship` is already idempotent over
pre-archived manifest members across all three tested arms (control,
partial-pre-archive, full-pre-archive): `archived_ids` in every arm already
includes members archived before the call, `returned_ids` is empty, and
`parent_id` is preserved. No engine behavior change and no relaxation of
the `archived_ids` exact-match invariant was needed or made — the existing
post-condition wording in the Cascade Close Sub-Procedure's step 3 applies
**unchanged**, evaluated against the full manifest as it always has been.
`src/autoharness/gates/shipment_closure.py` (the classifier) was likewise
left unchanged: it already scans both `queue/` and `archive/` for every
manifest member and every child-enumeration, so a manifest member's
archival state at classification time never altered its `CASCADE`/
`SAFE_CLOSE` verdict in the first place. The gap this document identified
was a **contract/documentation gap**, never a gate-code or engine defect.

**141-S's own closure is a live confirmation of the corrected contract.**
141-S's manifest (`132-F`, `132.001-T`, `132.002-T`, `132.003-T`) is itself
a fully-covered-root shipment: `132-F` is a root feature whose only
children are the three manifest tasks. Running
`classify_shipment_close_path` against 141-S's own manifest at closure time
returned `CASCADE`. The Cascade Close Sub-Procedure was followed as
written: `backlogit shipment ship 141-S --sha 01c1735b... --message ...
--author ...` returned `archived_ids: ["132.001-T", "132.002-T",
"132.003-T", "132-F", "141-S"]` (exact manifest + shipment record match),
`returned_ids: []`, and every task's `parent_id` (`132-F`) was confirmed
unchanged post-archive against the Step 0(b) pre-close snapshot. Gate
decision: `CLOSED`.

**Follow-up status**: implemented and closed. No further Stage-owned
backlog item is needed for the recommendation in the original "Follow-up"
section above.

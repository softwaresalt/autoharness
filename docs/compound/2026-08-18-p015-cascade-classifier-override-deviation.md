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

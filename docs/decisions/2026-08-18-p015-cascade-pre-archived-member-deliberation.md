# Deliberation — P-015 cascade close path and pre-archived manifest members

Date: 2026-08-18
Agent: Stage
Stash source: `EDE3CC2D` (medium, bug, reliability / P-015 correctness)
Evidence: `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`
Spike: `docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`

## Problem statement

`shipment-reconcile`'s Cascade Close Sub-Procedure has no explicit handling for
manifest members that were already individually archived before shipment-level
closure runs. Safe-close has an explicit `pre-archived` classification (step 4);
cascade has no equivalent. During 140-S closure this absence led the session to
substitute manual safe-close for a classifier-selected `CASCADE` verdict —
violating the contract rule that close-path selection comes only from the
machine-checkable classifier result, never from prose judgment (P-015 / P-005).

## What the evidence actually establishes

The spike (three isolated arms, `backlogit v1.9.0`) establishes decisively:

1. The classifier returns clean `CASCADE` for fully **and** partially
   pre-archived manifests — no error, no ambiguity.
2. `backlogit shipment ship` is **idempotent** over pre-archived members:
   `archived_ids` includes them, `returned_ids` is empty, `parent_id` is
   preserved, merge SHA is stamped.
3. Every verification step the Cascade Close Sub-Procedure performs (steps 2, 3,
   4, 6) **passes unchanged** in the pre-archived case.

So the sub-procedure is already *behaviourally* correct. It is only *silent*.

## Options considered

### Option A — Relax step 3's `archived_ids` exact-match post-condition

This is what the compound doc recommends. **Rejected.**

The spike proves the engine already returns pre-archived IDs inside
`archived_ids`, so the exact-match check passes today. Relaxing it would widen a
live P-005 out-of-scope-mutation detector — the single check that catches the
cascade archiving an artifact outside the manifest — in exchange for nothing.
This option trades away real safety to fix an imaginary failure.

This is the key place where the proposed compound remedy is wrong, and the
reason the instruction to not assume it was correct mattered.

### Option B — Change the classifier to detect and route pre-archived manifests

**Rejected.** The classifier is already correct (`_read_artifact_record` reads
queue *and* archive by design, with an explicit ambiguity guard). Adding a
pre-archive branch would add a code path with no behavioural difference, and
would risk re-introducing the "archived means ambiguous" confusion that caused
the deviation in the first place. Evidence does not prove code behaviour needs
to change, so per scope discipline the gate code is left untouched.

### Option C — Add an explicit halt-and-escalate rule for pre-archived members

**Rejected.** This would institutionalise the 140-S failure: it makes a
perfectly valid, verified-safe cascade close into a stop. It converts a
documentation gap into a permanent operational tax, and would fire on the
*normal* case, since members reaching closure already archived is the ordinary
consequence of the standard Step 2 task-completion sequence.

### Option D — Add an explicit pre-archived-member branch to the sub-procedure that documents tolerance, changing no invariant (SELECTED)

State plainly in the Cascade Close Sub-Procedure that manifest members already
archived before the cascade call are **expected and tolerated**, do not
disqualify the `CASCADE` verdict, and are still expected to appear in
`archived_ids` — so step 3's exact-match post-condition applies unchanged.
Pair it with an explicit prohibition on substituting safe-close after a clean
`CASCADE` verdict, naming the 140-S deviation as the precedent being closed.

Mirror the same tolerance statement into P-015's exception clause, since P-015
is the authoritative policy the skill implements.

Lock it with regression tests over the classifier for pre-archived manifests.

## Decision

**Option D.** Surgical, contract-only, invariant-preserving.

Rationale: the failure was a *contract silence* failure, so the fix belongs in
the contract. Every option that changed behaviour (A, B, C) either weakened a
safety invariant or penalised the normal case. Option D closes the exact hole
that produced the deviation — a session facing pre-archived members now has an
unambiguous, machine-checkable, contract-legal route — while leaving all live
safety checks and the verified-correct gate code untouched.

## Scope boundary

* **In scope**: `templates/skills/shipment-reconcile/SKILL.md.tmpl`,
  `templates/policies/workflow-policies.md.tmpl`,
  `tests/test_shipment_closure_classification.py`.
* **Explicitly out of scope**: `src/autoharness/gates/shipment_closure.py`
  (evidence proves no change needed);
  `templates/agents/_ship.agent.md.tmpl` and its checksum-tracked mirror — its
  close-path section already carries the classifier-authority rule verbatim
  ("select the close path from the verified check, never from prose alone"), so
  no agent-template or `harness-manifest.yaml` checksum churn is required.
* Stash entry `1EFDA8EE` and all other stash/queue work are untouched.

---
problem_type: cascade_close_archived_ids_incomplete_on_pre_archived_tasks
category: backlogit
root_cause: "backlogit 1.10.1's `shipment ship` (cascade close) omits already-archived TASK manifest members from its returned `archived_ids` list, even though it still correctly leaves them archived in the final workspace state. This contradicts the byte-identical-shape invariant recorded by the 2026-08-18 spike against backlogit 1.9.0, where `archived_ids` included every pre-archived member regardless of artifact type."
tags: [backlogit, shipment, cascade-close, p-015, archived_ids, regression]
shipment: 154-S
date: 2026-08-23
source: "docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md"
doc_type: learning
title: "Cascade close `archived_ids` omits pre-archived TASK members on backlogit 1.10.1 (spike invariant partially stale)"
---

# Cascade close `archived_ids` omits pre-archived TASK members on backlogit 1.10.1

## Problem

`docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md` verified
against `backlogit v1.9.0-39-g17530fe3` that `shipment ship`'s `archived_ids`
response always includes **every** manifest member — task, feature, and
shipment — even when some were archived before the call. The
`shipment-reconcile` Cascade Close Sub-Procedure's step 3 relies on this: it
evaluates the exact-match post-condition "against the manifest's full item
set, never against 'members newly archived by this call'" specifically
because the spike proved those two framings were equivalent.

During 154-S/146-F closure on `backlogit 1.10.1-0.20260823032255-b07729386a31`,
the manifest was `[146-F, 146.001-T, 146.002-T, 146.003-T]` (146-F itself is
the covering feature; the other three are its manifest-member task children).
All four manifest members were hard-archived individually via `backlogit
archive <id>` (to correct a separate pre-existing anomaly — see below) before
`backlogit shipment ship 154-S --sha ...` ran. The call succeeded
(`returned_ids: []`, `shipment_status: shipped`), but its `archived_ids`
response was `["146-F", "154-S"]` — the three pre-archived **task** items were
silently omitted from the returned list, even though `146-F` (also
pre-archived at call time) was still included.

A literal, unmodified reading of the sub-procedure's step 3 ("`archived_ids`
contains exactly the manifest's task items, every qualifying feature member,
and the shipment record itself — nothing more, nothing less") would have
forced an incorrect `HALT — cascade archived unexpected artifact` or missing-ID
halt here, on a call that was in fact fully correct.

## Root cause (observed, not confirmed against backlogit source)

Between `v1.9.0-39-g17530fe3` (spike baseline) and `1.10.1-...-b07729386a31`
(this session), the engine's `archived_ids` reporting changed for pre-archived
**task**-type members specifically — it appears to report only artifacts it
actually mutated during this call (features and the shipment record are
always touched for status/provenance stamping purposes; tasks that were
already fully archived with no pending stamp needed are treated as no-ops and
excluded from the response). This is an observed behavior difference, not a
confirmed code-level diagnosis — backlogit's Go source was not inspected in
this session.

## What actually stayed correct

Physical verification (not the JSON response) confirmed the operation was
fully correct:

* All 5 artifacts (`146-F`, `146.001-T`, `146.002-T`, `146.003-T`, `154-S`)
  ended up in `.backlogit/archive/`, none remained in `.backlogit/queue/`.
* `parent_id: 146-F` was unchanged on all three tasks (re-read post-call).
* `154-S` carried `archived_status: shipped` and the correct `commit` SHA.
* `returned_ids` was empty (no unreleased descendant surfaced).

## This is an open anomaly, not a resolved operating rule (P-021 deferred, `5CFA8198`)

**The currently documented Cascade Close Sub-Procedure contract is
unchanged and remains fully in force.** `templates/skills/shipment-reconcile/SKILL.md.tmpl:600-622`
and P-015 (`templates/policies/workflow-policies.md.tmpl:444`) state the
`archived_ids` exact-match post-condition "must never be relaxed," and a
verification failure against it is a documented halt condition. This
document does **not** amend that contract, and no future closure session
should treat this document as license to proceed past an `archived_ids`
mismatch on its own authority. Amending the contract text, or
re-verifying/reconciling backlogit's engine behavior via a fresh spike, is
out of scope for the 154-S/146-F shipment (P-021 C1) and has been captured
as deferred scope expansion `5CFA8198` (`requires_deliberation: true`) for
Stage to triage.

What this document records is a **fact pattern for that future
deliberation**, not a rule to apply unilaterally today:

1. This specific closure independently re-read the **live workspace state**
   (queue/ vs archive/ presence) for every manifest member plus the shipment
   record, and re-read `parent_id` on every task against the Step 0(b)
   pre-close snapshot, as additional corroborating evidence alongside the
   (incomplete) `archived_ids` response.
2. That live-state check showed no artifact outside the manifest set was
   touched and no protected-set member was moved — i.e., no cascade defect
   occurred in this specific instance.
3. This does **not** establish a general rule that live-state verification
   may substitute for the documented `archived_ids` exact-match gate on
   future closures. Whether the contract should be updated to formally
   allow that substitution, whether the engine regression should be fixed
   upstream instead, or whether the spike's original invariant needs
   re-verification, is exactly the open question handed to `5CFA8198`.
4. Until that deliberation resolves, a future closure session facing the
   same `archived_ids` shortfall should treat it as the fail-closed halt the
   current contract already specifies, and reference `5CFA8198` rather than
   re-deriving a new ad hoc justification to proceed.

## Separate anomaly this session also corrected

Independently of the above: the three task items and the feature had been
moved to `status: done` via `backlogit move --status done` by an **earlier**
commit in this same PR (`42d8a7b2`), which the workspace's `registry.yaml`
routes directly into `.backlogit/archive/` by directory rule. That relocation
alone does **not** invoke the single-artifact `archive` command, so the
resulting files carried `status: done` with no `archived_from` /
`archived_status` / `commit` stamp — physically archived by directory but not
"hard-archived" by provenance. `backlogit archive <id>` was run individually
on all four (`146-F`, `146.001-T`, `146.002-T`, `146.003-T`) to add the
missing stamps before the cascade `shipment ship` call. This is unrelated to
the `archived_ids` reporting gap above but explains why this closure had
pre-archived members to test against in the first place.

## Consequence

This is an **open, deliberation-pending anomaly** (`5CFA8198`), not a settled
reinterpretation of the Cascade Close Sub-Procedure. The documented
`archived_ids` exact-match gate in `shipment-reconcile` remains fail-closed
and unmodified. This document exists to preserve the observed fact pattern
(engine response discrepancy vs. confirmed-correct live-workspace state) for
that deliberation, and explicitly to prevent a future session from citing it
as authority to bypass the current contract without an actual, reviewed
contract or engine-behavior fix.

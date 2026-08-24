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
the manifest was `[146-F, 146.001-T, 146.002-T, 146.003-T]`. All four members
plus the covering feature were hard-archived individually via `backlogit
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

## Fix / operating rule for future closures

Do not treat a literal `archived_ids` string-set mismatch against the full
manifest as an automatic halt trigger on its own. Before halting on an
apparent `archived_ids` shortfall:

1. Re-read the **live workspace state** (queue/ vs archive/ presence) for
   every manifest member plus the shipment record — this is the authoritative
   signal, not the JSON response shape.
2. Re-read `parent_id` on every task against the Step 0(b) pre-close snapshot.
3. Only if the **live state** shows an artifact outside the manifold set was
   touched, or a protected-set member was moved, is this a genuine
   `HALT — cascade archived unexpected artifact` / cascade-detected condition.
4. If live state matches expectations exactly but `archived_ids` under-reports
   pre-archived task members, record the discrepancy (this document) and
   proceed — this is a documentary/reporting gap in the engine response, not a
   safety violation, consistent with the 2026-08-18 spike's own conclusion
   that "the gap is purely documentary" (now revised: on 1.10.1 the gap can
   recur asymmetrically for tasks specifically, and this time the *response*
   itself under-reports rather than merely lacking a stated invariant).

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

`shipment-reconcile`'s Cascade Close Sub-Procedure step 3 should be read as:
verify the **live workspace's final state** matches the manifest's full item
set exactly (queue/archive presence, `parent_id` preservation,
`archived_status`/`commit` provenance) — the `archived_ids` field in the
command's JSON response is corroborating evidence, not the sole source of
truth, and a shortfall in that field alone (with live state otherwise
correct) is not grounds for a P-005 halt.

---
title: "Cascade shipment close (backlogit shipment ship) archived an out-of-manifest linked deliberation (019-DL) via custom_fields.source_deliberation_id, not a parent_id hierarchy edge — caught by the exact-match post-condition, reverted"
description: "During 143-S's P-015 verified fully-covered-root CASCADE close, backlogit shipment ship's archived_ids included 019-DL — a deliberation record referenced only via 134-F's custom_fields.source_deliberation_id, never a parent_id child. classify_shipment_close_path's coverage check only walks parent_id-based hierarchy, so it could not have predicted this. The Cascade Close Sub-Procedure's step 3 exact-match verification caught the discrepancy; the unintended archival was reverted, the legitimate closure retained."
problem_type: "engine-behavior-surprise"
category: "shipment-reconcile-close-path-contract"
component: "ship-agent-post-merge-closure"
root_cause: "134-F's custom_fields.source_deliberation_id: 019-DL records provenance (which deliberation led to this feature's creation) as a plain reference field, not a parent_id/hierarchy edge. classify_shipment_close_path's fully-covered-root check enumerates children via parent_id only (queue/ + archive/ scan), so it correctly found zero uncovered parent_id children and returned CASCADE. The backlogit shipment ship engine operation, however, appears to also archive artifacts reachable via custom_fields reference links (at minimum source_deliberation_id) when cascading a feature closure — a behavior neither the classifier nor the Cascade Close Sub-Procedure's documented contract currently accounts for."
resolution_type: "residual-risk-disclosure"
severity: "medium"
tags:
  - "ship"
  - "P-015"
  - "P-005"
  - "shipment-reconcile"
  - "close-path-contract"
  - "143-S"
  - "134-F"
  - "cascade-close"
citations:
  - "143-S/134-F post-merge closure session, 2026-08-20"
  - "templates/skills/shipment-reconcile/SKILL.md.tmpl:589-622 (Cascade Close Sub-Procedure steps 1-4)"
  - "src/autoharness/gates/shipment_closure.py: classify_shipment_close_path"
  - "docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md (related but distinct: that entry covers pre-archived manifest members, a documented/tolerated case; this entry covers a genuinely out-of-manifest artifact)"
---

# Cascade Close Archived an Out-of-Manifest Linked Deliberation — Tracked Residual

## Context

143-S's manifest was `134-F` + `134.001-T`..`134.013-T`.
`classify_shipment_close_path` correctly returned **CASCADE**: `134-F` is a
root feature (no `parent_id`) whose only `parent_id`-linked children are the
13 manifest tasks — a verified fully-covered root.

Invoking `backlogit shipment ship 143-S --sha e2af4dfe...` returned:

```json
{
  "shipment_id": "143-S",
  "shipment_status": "shipped",
  "archived_ids": ["134.001-T", ..., "134.013-T", "019-DL", "134-F", "143-S"],
  "returned_ids": [],
  "commit_sha": "e2af4dfe1b403b85cab7f237a4f7f9b621370d70"
}
```

`019-DL` — a deliberation record — was **not** in the manifest. Its only
relationship to `134-F` is `134-F`'s own `custom_fields.source_deliberation_id:
019-DL` (provenance: "this feature originated from this deliberation"), which
is a plain reference field, not a `parent_id` hierarchy edge. `019-DL`'s own
`parent_id`/hierarchy fields carry no link to `134-F` at all.

## Why the classifier could not have caught this

`classify_shipment_close_path`'s fully-covered-root check enumerates a
feature's children by scanning `queue/` + `archive/` for records whose
`parent_id` equals the feature's ID. `019-DL` has no such `parent_id`
relationship to `134-F` — it is referenced the other direction, as
free-form provenance metadata on the feature. The classifier's `CASCADE`
verdict was therefore correct and defensible given its documented contract;
the surprise is in the **engine's own cascade behavior**, which appears to
walk at least one `custom_fields` reference link in addition to `parent_id`
hierarchy when archiving a feature's closure set.

## What caught it, and what happened

The Cascade Close Sub-Procedure's own step 3 ("Verify `archived_ids`
contains exactly the manifest's task items, every qualifying feature member,
and the shipment record itself — nothing more, nothing less. Any extra ID is
an out-of-scope mutation: halt ... and emit a P-005 violation") is exactly
the fail-closed guard designed for this class of surprise, and it worked as
intended:

1. Halted on the mismatch (`019-DL` present in `archived_ids` but absent from
   the manifest).
2. Verified the other three legitimate archival targets (13 tasks, `134-F`,
   `143-S`) matched the manifest + qualifying feature + shipment record
   exactly, and that every task's `parent_id` was unchanged from the Step
   0(b) pre-close snapshot (`134-F`) — both still correct.
3. Reverted **only** the unintended `019-DL` mutation: `git restore --staged`
   + `git checkout` on `.backlogit/queue/019-DL.md` and its log, and removal
   of the newly-created `.backlogit/archive/019-DL.md`. Confirmed via
   `git diff` (no output) and `backlogit get 019-DL` (`status: queued`,
   unchanged) that `019-DL` was restored to its exact pre-cascade state.
4. Retained the legitimate cascade archival (13 tasks + `134-F` + `143-S`),
   since it independently satisfied every other post-condition (exact match
   after excluding `019-DL`, `returned_ids: []`, `parent_id` preserved).

This is a narrower remediation than a full revert of the entire cascade
operation: the sub-procedure's own step 6 gate language ("Any verification
failure above → the corresponding HALT; do not proceed to post-mode or any
commit step") governs proceeding to the **next phase** (post-mode, commit),
not a mandate to undo an otherwise-correct legitimate closure alongside the
one genuinely out-of-scope artifact. Nothing was committed to git until the
`019-DL` anomaly was fully reverted and re-verified.

## The gap (Stage-owned follow-up, not opened by Ship)

Neither `classify_shipment_close_path` nor the Cascade Close Sub-Procedure's
documented contract currently accounts for `custom_fields`-only reference
links (e.g. `source_deliberation_id`) when determining "nothing more, nothing
less" for the `archived_ids` post-condition. A future Stage-sized
template/contract change should either:

1. Extend the classifier's fully-covered-root coverage check to also treat a
   feature's `custom_fields.source_deliberation_id` (and any similar
   provenance-reference field) as an implicit child for coverage purposes —
   which would require `019-DL` to be added to any manifest for this shipment
   to legitimately qualify for `CASCADE`, correctly forcing `SAFE_CLOSE`
   instead unless the deliberation is deliberately included; **or**
2. Document and test the engine's own reference-link cascade behavior
   precisely (which `custom_fields` keys it follows, under what conditions),
   and add an explicit, bounded tolerance to the Cascade Close Sub-Procedure's
   step 3 exact-match check for artifacts reachable only via those specific
   documented reference keys — mirroring the existing pre-archived-manifest-
   member tolerance, but scoped narrowly enough to still catch genuinely
   unexpected artifacts.

Until either exists, the correct and required behavior for any future Ship
session hitting this exact signature (a linked-but-not-`parent_id`-child
deliberation appearing in `archived_ids`) is: halt per step 3, verify the
rest of the post-conditions independently, revert only the unexpected
artifact, and disclose here — never silently accept the extra archival, and
never revert the otherwise-correct legitimate closure alongside it.

Ship's Role Boundary forbids creating backlog items or editing
skill/classifier contract templates directly (P-010); this document is the
tracked residual-risk record until a Stage session opens and sizes the
actual follow-up item. No specific backlog ID exists yet — none is invented
here.

## Disposition for 143-S

No corrective action is required for shipment 143-S's own closure: the final
archived backlog state (13 tasks + `134-F` + `143-S`, all with confirmed
correct provenance and preserved `parent_id`) is exactly the manifest-scoped
outcome required by P-015, independently re-verified after the `019-DL`
revert. `019-DL` itself is confirmed byte-identical to its pre-cascade state.

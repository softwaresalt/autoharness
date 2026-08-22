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
  - "148-S"
  - "140-F"
  - "149-S"
  - "141-F"
  - "151-S"
  - "143-F"
  - "150-S"
  - "142-F"
citations:
  - "143-S/134-F post-merge closure session, 2026-08-20"
  - "148-S/140-F post-merge closure session, 2026-08-21 (recurrence via a plain `references` list entry, not `custom_fields.source_deliberation_id`)"
  - "149-S/141-F post-merge closure session, 2026-08-21 (third occurrence, same `references`-list mechanism, different feature/deliberation pair -- 024-DL)"
  - "151-S/143-F post-merge closure session, 2026-08-21 (fourth occurrence, same 024-DL deliberation as the third occurrence but a different sibling feature -- 143-F, not 141-F -- both derived from the same E8158860 deliberation)"
  - "150-S/142-F post-merge closure session, 2026-08-22 (fifth occurrence, a fourth distinct deliberation ID -- 023-DL -- confirming the defect is per-feature/per-cascade-close, not tied to any one deliberation record)"
  - "templates/skills/shipment-reconcile/SKILL.md.tmpl:589-622 (Cascade Close Sub-Procedure steps 1-4)"
  - "src/autoharness/gates/shipment_closure.py: classify_shipment_close_path"
  - "docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md (related but distinct: that entry covers pre-archived manifest members, a documented/tolerated case; this entry covers a genuinely out-of-manifest artifact)"
source: docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md
doc_type: learning
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

## Recurrence: 148-S / 140-F / 025-DL

The identical signature recurred during 148-S's post-merge closure
(2026-08-21). Manifest: `140-F`, `140.001-T`, `140.002-T`.
`classify_shipment_close_path` again correctly returned `CASCADE` (`140-F` is
a root feature whose only `parent_id`-linked children, `140.001-T` and
`140.002-T`, are both manifest members).

`backlogit shipment ship 148-S --sha 291dafd8...` returned:

```json
{
  "shipment_id": "148-S",
  "shipment_status": "shipped",
  "archived_ids": ["140.001-T", "140.002-T", "025-DL", "140-F", "148-S"],
  "returned_ids": [],
  "commit_sha": "291dafd8cd5c1ff937c6499476161ae450fb2f0a"
}
```

`025-DL` — the deliberation `140-F` originated from — was again swept in via a
plain `references` list entry (`.backlogit/queue/025-DL.md`), never a
`parent_id` edge; `025-DL` itself carries no `parent_id` pointing at `140-F`.
Same root cause, different feature/deliberation pair.

Applied the exact documented remediation: reverted only `025-DL` (`git
restore --staged` + `git checkout` on `.backlogit/queue/025-DL.md`, removed
the newly-created `.backlogit/archive/025-DL.md` and
`.backlogit/logs/025-DL.jsonl`, unstaged the resulting `AD` archive entry),
confirmed `git diff` empty and `backlogit get 025-DL` reports `status: queued`
unchanged. Independently re-verified the remaining post-conditions: exact
`archived_ids` match ({`140.001-T`, `140.002-T`, `140-F`, `148-S`}) after
excluding `025-DL`; `returned_ids: []`; `parent_id: 140-F` preserved on both
tasks against the Step 0(b) pre-close snapshot; shipment `archived_status:
shipped`. No corrective action required for 148-S's own closure beyond the
`025-DL` revert.

This second occurrence reinforces that the gap is the engine's own
reference-link cascade behavior (not specific to `custom_fields.
source_deliberation_id` — this time the link was a plain `references` list
entry), strengthening the case for the Stage-owned follow-up option 2 above
(a bounded, documented tolerance in the Cascade Close Sub-Procedure's step 3
exact-match check) over option 1 (extending the classifier's coverage
check), since the reference shape varies across features and is not limited
to one specific field name.

## Recurrence: 149-S / 141-F / 024-DL (third occurrence)

A third occurrence, again during Ship's own post-merge closure (2026-08-21,
same session as the 148-S recurrence above). Manifest: `141-F`, `141.001-T`
.. `141.005-T` (the last a pre-archived/superseded member, tolerated per the
established precedent — absent from `archived_ids` this time since it
required no action, unlike a freshly-archived member).
`classify_shipment_close_path` again correctly returned `CASCADE`.

`backlogit shipment ship 149-S --sha ca9059bf...` returned:

```json
{
  "shipment_id": "149-S",
  "shipment_status": "shipped",
  "archived_ids": ["141.001-T", "141.002-T", "141.003-T", "141.004-T", "024-DL", "141-F", "149-S"],
  "returned_ids": [],
  "commit_sha": "ca9059bf9c651b61c9d0a458568ffc798ff4cf91"
}
```

`024-DL` — the deliberation `141-F` originated from — was again swept in via
a plain `references` list entry (`.backlogit/queue/024-DL.md`), never a
`parent_id` edge; `024-DL` itself carries no `parent_id` pointing at `141-F`.
Same root cause, third feature/deliberation pair, same `references`-list
mechanism as the 148-S/140-F/025-DL recurrence (not
`custom_fields.source_deliberation_id`, the original 143-S/134-F/019-DL
mechanism).

Applied the identical documented remediation: reverted only `024-DL` (`git
restore --staged` + `git checkout` on `.backlogit/queue/024-DL.md`, removed
the newly-created `.backlogit/archive/024-DL.md` and
`.backlogit/logs/024-DL.jsonl`, unstaged the resulting `AD` archive entry),
confirmed `git diff` empty and `backlogit get 024-DL` reports `status:
queued` unchanged. Independently re-verified the remaining post-conditions:
exact `archived_ids` match ({`141.001-T`, `141.002-T`, `141.003-T`,
`141.004-T`, `141-F`, `149-S`}) after excluding `024-DL`; `returned_ids: []`;
`parent_id: 141-F` preserved on all four freshly-archived tasks against the
Step 0(b) pre-close snapshot; shipment `archived_status: shipped`; feature
`archived_status: done`. No corrective action required for 149-S's own
closure beyond the `024-DL` revert.

This third occurrence, spanning three different shipments, three different
features, and three different deliberation records over two calendar days,
further confirms this is a systematic engine behavior (walking a plain
`references` list, not merely a `custom_fields.source_deliberation_id`
edge) rather than an isolated fluke — the Stage-owned follow-up (a bounded,
documented tolerance in the Cascade Close Sub-Procedure's step 3 exact-match
check for artifacts reachable only via a feature's own `references` list)
remains open and is now reinforced by three independent, consistent
observations.

## Recurrence: 151-S / 143-F / 024-DL (fourth occurrence)

A fourth occurrence, again during Ship's own post-merge closure
(2026-08-21, same day as the third occurrence above). Manifest: `143-F`,
`143.001-T`, `143.002-T`. `classify_shipment_close_path` again correctly
returned `CASCADE` (`143-F` is a root, fully covered by both manifest-member
children).

`backlogit shipment ship 151-S --sha f389fd59...` returned:

```json
{
  "shipment_id": "151-S",
  "shipment_status": "shipped",
  "archived_ids": ["143.001-T", "143.002-T", "024-DL", "143-F", "151-S"],
  "returned_ids": [],
  "commit_sha": "f389fd59d9d196d9ce8cf28cc75c5a1d1e6378ab"
}
```

Notably, this is the **same deliberation ID** (`024-DL`) as the third
occurrence, not a new one — `143-F` is a sibling feature to `141-F` (both
split from the same original `E8158860` stash entry via the same `024-DL`
deliberation), and `143-F`'s own `references` list independently carries
`.backlogit/queue/024-DL.md`, exactly like `141-F`'s did. This confirms the
engine walks each closing feature's OWN `references` list independently at
cascade time — it is not a one-time quirk tied to a single deliberation
record, but a per-feature, per-cascade-close behavior that recurs for
every feature referencing an as-yet-unarchived deliberation, even when that
deliberation was already reverted-and-restored once in an unrelated
shipment's closure earlier the same day.

Applied the identical documented remediation: reverted only `024-DL` (`git
restore --staged` + `git checkout` on `.backlogit/queue/024-DL.md`, removed
the newly-created `.backlogit/archive/024-DL.md` and
`.backlogit/logs/024-DL.jsonl`, unstaged the resulting `AD` archive entry),
confirmed `git diff` empty and `backlogit get 024-DL` reports `status:
queued` unchanged. Independently re-verified the remaining post-conditions:
exact `archived_ids` match ({`143.001-T`, `143.002-T`, `143-F`, `151-S`})
after excluding `024-DL`; `returned_ids: []`; `parent_id: 143-F` preserved
on both tasks against the Step 0(b) pre-close snapshot; shipment
`archived_status: shipped`; feature `archived_status: done`. No corrective
action required for 151-S's own closure beyond the `024-DL` revert.

This fourth occurrence, spanning FOUR shipments and FOUR features over two
calendar days (two of which share the same deliberation record), makes the
Stage-owned follow-up (a bounded, documented tolerance in the Cascade Close
Sub-Procedure's step 3 exact-match check for artifacts reachable only via a
feature's own `references` list) an increasingly urgent priority rather
than a low-frequency edge case.

## Recurrence: 150-S / 142-F / 023-DL (fifth occurrence)

A fifth occurrence, again during Ship's own post-merge closure (2026-08-22).
Manifest: `142-F`, `142.001-T` through `142.007-T`.
`classify_shipment_close_path` again correctly returned `CASCADE` (`142-F`
is a root, fully covered by all seven manifest-member children).

`backlogit shipment ship 150-S --sha 927272da...` returned:

```json
{
  "shipment_id": "150-S",
  "shipment_status": "shipped",
  "archived_ids": [
    "142.001-T", "142.002-T", "142.003-T", "142.004-T", "142.005-T",
    "142.006-T", "142.007-T", "023-DL", "142-F", "150-S"
  ],
  "returned_ids": [],
  "commit_sha": "927272da2cca01d43ccc109eb31fdf59c88db5dd"
}
```

This is a FOURTH distinct deliberation ID (`023-DL`, distinct from the
`019-DL`/`025-DL`/`024-DL` seen in the first four occurrences), confirming
again that the defect is a per-feature, per-cascade-close behavior driven
purely by whatever `references` a closing feature happens to carry, not
tied to any specific deliberation record or shipment. `142-F`'s own
`references` list independently carries `.backlogit/queue/023-DL.md`
(142-F's own originating deliberation, per its description's "Deliberation:
023-DL" line) alongside two plan documents and a review document — the
cascade walked that list and archived the one entry that happened to still
be a live `.backlogit` artifact.

Applied the identical documented remediation: reverted only `023-DL` (`git
restore --staged` + `git checkout` on `.backlogit/queue/023-DL.md`, removed
the newly-created `.backlogit/archive/023-DL.md` and
`.backlogit/logs/023-DL.jsonl`), confirmed `git diff` empty and `backlogit
get 023-DL` reports `status: queued` unchanged. Independently re-verified
the remaining post-conditions: exact `archived_ids` match (all seven tasks
plus `142-F` plus `150-S`) after excluding `023-DL`; `returned_ids: []`;
`parent_id: 142-F` preserved on all seven tasks; shipment
`archived_status: shipped`; feature `archived_status: done`. No corrective
action required for 150-S's own closure beyond the `023-DL` revert.

This fifth occurrence, spanning FIVE shipments and FIVE features across
FOUR distinct deliberation records over two calendar days, further
confirms the defect is systemic to the cascade-close engine's own
`references`-list traversal rather than an artifact of any one
deliberation's lifecycle state, and reinforces the priority of the
Stage-owned follow-up recorded above.


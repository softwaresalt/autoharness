---
title: "backlogit 1.11.0 flat cascade leaves linked deliberations live — the fourth closure-time engine-behavior drift, and a re-verification runbook"
description: "On backlogit 1.11.0 `backlogit shipment ship` archives only the shipment, terminal explicit release-scope members, and explicit feature members; a feature's linked deliberations stay independent. The 1.10-era autoharness contract still required them in `archived_ids`, so the 190-S CASCADE close halted. The contract was realigned to the flat engine semantics, CASCADE and linked-deliberation disposition mutation now fail closed outside a verified engine-semantics line, and this learning carries the runbook for re-verifying a new backlogit minor line."
problem_type: tool_version_behavior_drift
category: backlogit
component: "shipment-reconcile Cascade Close Sub-Procedure, P-015, Ship post-merge closure, src/autoharness/gates/shipment_closure.py"
root_cause: "backlogit commit 5a4b70dd (first released in tag v1.11.0, which points at commit 131577c) flattened `collectArchiveCandidateIDs`: its candidates are the shipment, each terminal not-yet-archived release-scope item, and each explicit-member feature that is not yet archived, and its descendants and linked deliberations remain independent unless their own IDs are explicit members. autoharness had encoded the 1.10.x behavior (the `linkedDeliberationIDs` helper appended linked deliberations to the candidates) as an unversioned contract, so its two-set gate put the description-linked deliberation 034-DL in `required_ids` and halted when the engine correctly left it live."
resolution_type: design_change
severity: high
citations:
  - "190-S / 184-F post-merge closure HALT (docs/closure/190-S-184-F-post-merge-closure.md)"
  - "PR #464 (190-S, merge ef661e90)"
  - "PR #465 (190-S post-merge closure, operator-approved deviation archiving 034-DL)"
  - "backlogit commit 5a4b70dd, first released in tag v1.11.0 (commit 131577c); line numbers verified at the tag: internal/core/shipment_lifecycle.go collectArchiveCandidateIDs L716-751, comment L734-735"
  - "backlogit test TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched"
  - "deliberation 038-DL (docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md)"
  - "deliberation 034-DL (the description-linked deliberation left live by the 190-S cascade)"
  - "deliberation 027-DL (the 1.10.1 archived_ids correction)"
  - "docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md"
tags: [backlogit, backlogit-1.11.0, shipment, cascade-close, p-015, linked-deliberation, engine-behavior-drift, runbook]
shipment: 201-S
feature: 195-F
date: 2026-09-29
source: docs/compound/2026-09-29-backlogit-1-11-flat-cascade-leaves-linked-deliberations.md
doc_type: learning
---

# backlogit 1.11.0 flat cascade leaves linked deliberations live

## What happened

During the 190-S post-merge closure (PR #464, merge `ef661e90`), backlogit
1.11.0 `backlogit shipment ship 190-S` archived `[184.001-T, 184-F, 190-S]` and
returned `returned_ids: []`. It did not archive deliberation `034-DL`, which is
linked from the description of the qualifying root feature `184-F`. The
`shipment-reconcile` two-set gate had placed `034-DL` in `required_ids`, so
`required_ids - archived_ids = [034-DL]` and the close halted with a P-005. The
operator approved a one-off standalone `backlogit archive 034-DL`, recorded as
an operator-approved deviation in the
[190-S closure record](../closure/190-S-184-F-post-merge-closure.md) and
landed through closure PR #465. The SHA-256 of `034-DL` was unchanged across the
cascade: the engine never touched it.

The [decision](../decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md)
and [plan](../plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md)
realigned P-015, the `shipment-reconcile` skill, the Ship agent, and the
`operational-closure` skill to the flat engine semantics across the six-slice
partition of umbrella feature 195-F (terminal slice: shipment 201-S).

## Engine root cause

At tag `v1.11.0` (commit `131577c`), which first released fix commit
`5a4b70dd` ("fix(core): flatten shipment member projection and closure"), `internal/core/shipment_lifecycle.go`
`collectArchiveCandidateIDs` (L716-751) builds its candidates from three
sources only: the shipment, each release-scope item that is terminal and not
yet archived, and each explicit-member feature that is not yet archived. Its
comment at L734-735 states the rule: "Its descendants and linked deliberations
remain independent unless their own IDs are explicit members." The engine's
own regression test `TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched`
pins it. At `v1.10.0` the `linkedDeliberationIDs` helper appended linked
deliberations to the candidates, so the old autoharness contract was correct
for 1.10.x and wrong for 1.11.x.

## Four closure-time drift occurrences

This was the fourth time autoharness discovered a backlogit engine-behavior
change during a live shipment operation rather than before mutation (three
at closure; the 2026-08-21 claim cascade at claim time):

1. **2026-08-20 — 143-S linked-deliberation cascade.** A 1.10-era cascade
   archived the out-of-manifest deliberation `019-DL` through
   `custom_fields.source_deliberation_id`
   ([learning](2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md)).
2. **2026-08-21 — the 1.10.0 claim cascade.** Claiming a shipment also flipped
   its covering feature and queued tasks to `active`
   ([learning](2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md)).
3. **2026-08-23 — 1.10.1 `archived_ids` omitting pre-archived tasks.** The
   precedent: the autoharness expectation, not the engine, was wrong
   ([learning](2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md)).
4. **2026-09-29 — 1.11.0 linked deliberations.** The flat cascade leaves a
   feature's linked deliberations live (this learning).

The recurrence, not the single defect, is the lesson.

## The rule

Every engine-behavior assumption carries a verified backlogit version line.
CASCADE and linked-deliberation disposition mutation fail closed outside that
line: an unverified engine selects SAFE_CLOSE with `ENGINE_SEMANTICS_UNVERIFIED`
and disposition records `retained_engine_unverified` without mutating anything.
The single source of truth for the verified lines is
`VERIFIED_CASCADE_ENGINE_MINOR_LINES` in
`src/autoharness/gates/shipment_closure.py`, mirrored by
the "Verified engine-semantics lines" tokens in P-015 and the
`shipment-reconcile` skill. Linked deliberations are now handled only by the
path-independent Linked-Deliberation Disposition step (P-015 INV-12), never by
the cascade.

## Re-verification runbook for a new backlogit minor line

Run this before adopting a new backlogit minor line (for example 1.12). It
requires the engine-behavior registry deliberation (stash `8928EC67`) first;
do not bump anything until that deliberation is decided.

1. **Re-read the engine at the new tag.**
   * `collectArchiveCandidateIDs` and `archiveItems` in
     `internal/core/shipment_lifecycle.go`.
   * `ArchiveItem` in `internal/core/archive.go`, including the set of
     frontmatter keys it reads and writes and its `ArchiveLinkedStashEntries`
     call (`internal/core/stash.go`), the stash-link side effect the
     Linked-Deliberation Disposition step's engine stash-link guard depends on.
2. **Confirm the engine tests.** The `TestUArchiveCandidateFlat_*` tests still
   exist and still pass at the new tag, with the same assertions.
3. **Bump together, in one change.**
   * the `VERIFIED_CASCADE_ENGINE_MINOR_LINES` constant;
   * the P-015 and `shipment-reconcile` "Verified engine-semantics lines"
     tokens (template and mirror);
   * this learning (append a dated verification note).
4. **If any behavior changed,** stop: realign the contract through Stage
   deliberation first, exactly as 038-DL did for 1.11.0.

## Pointers

* Stash `8928EC67` — the general backlogit engine-behavior compatibility
  registry. It must be deliberated before changing the verified lines or
  adopting backlogit 1.12, and it absorbs `62C1E11E` and the `archive_item`
  semantics.
* Stash `62C1E11E` — the claim-time version/behavior gate on P-002.7.

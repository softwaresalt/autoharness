---
title: "Ship 205-S / 199-F post-merge closure session"
description: "Session memory for the 205-S / 199-F (195-F slice 4 of 6) post-merge closure: PR #475 merge facts, CASCADE close under the now-consistent skill and P-015, retirement of interim rule A, and archival of stash 26D90B0F."
doc_type: memory
date: 2026-10-01
agent: ship
session_id: ship-2026-10-01-205s-closure
---

# Ship 205-S / 199-F Post-Merge Closure Session

## Merge facts

* PR #475 merged as `4303e2c3` (`--merge`, operator-approved). Reviewed HEAD
  `978dffee`, `READY_WITH_FOLLOWUPS`, P0=0, P1=0. 2585 tests OK, CI green,
  P-018 `SATISFIED`.
* Review-fix cycles 4 and 5 ran under operator authorization (option B). The
  hash finding was deferred to stash `54DDA2A6`.
* Slice content: the skill's all-member linked-deliberation disposition
  snapshot and the Cascade Close flat sets (`allowed_ids` =
  `closure_scope(S)`), realigned with P-015.

## Close

* Lifecycle topology gate: exit 0 on `chore/205-s-closure` (predecessor
  `204-S`, explicit).
* Pre-mode `PROCEED`. 199-F was `active` in the queue, and the 11 tasks were
  `done` in the archive (pre-archived by location, not truly archived).
* Step 0(c): CLI probe `1.11.0` / `131577c`, `VERIFIED`. The classifier and
  `select_close_path` both returned `CASCADE`. The root was `199-F`, with no
  descendants. The disposition snapshot was empty.
* Revalidation had no drift (classifier, disposition snapshot, exact engine
  re-probe). The baseline covered 1503 records.
* `backlogit shipment ship 205-S --sha 4303e2c3…` exited 0 after about 8.3
  minutes. `archived_ids` covered the 11 tasks, `199-F` and `205-S`, and
  `returned_ids` was `[]`. All flat-set, `parent_id`, baseline, disposition
  byte-identity and tree-diff checks passed. Post-mode `PROCEED`.
* `linked_deliberation_disposition: step-not-yet-on-main (transition window); all retained`.

## Stash

* Interim rule A was retired as of `4303e2c3`.
* `26D90B0F` got a resolution comment and was archived with
  `backlogit stash archive`.
* The other 14 listed entries stay active.

## Learnings

* The 204-S proof script carried over with three changes: flat
  `allowed_ids`, required set built from manifest items only, and the
  disposition snapshot taken through the read-only planner
  `compute_linked_deliberation_disposition`, projected without outcome and
  referrer fields.
* `backlogit stash archive` has no note flag. Record the resolution with
  `backlogit comment add` first, then archive.

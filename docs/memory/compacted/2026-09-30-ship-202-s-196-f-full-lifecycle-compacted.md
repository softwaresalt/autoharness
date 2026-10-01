---
title: "Ship 202-S / 196-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 202-S / 196-F (195-F slice 1 of 6: P-015 engine-semantics gate, close-path composition, INV-12 disposition-planner core; inert on main). Covers PR #468 merge facts, the contemporaneous CASCADE close, and closure learnings (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-09-30-ship-202-s-196-f-full-lifecycle-compacted.md
date: 2026-09-30
agent: ship
session_id: ship-2026-09-30-202s-closure
compacted_from:
  - docs/archive/memory/2026-09-30-ship-202-s-196-f-closure-session.md
---

# Ship 202-S / 196-F Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/202-S-196-F-post-merge-closure.md`. Close evidence:
`.backlogit/reconcile/202-S-cascade-close-20261001-021546.md`. Plan:
`docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md`. Decision:
`docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md`.

## Delivery

* PR #468 merged as `f45086f2` (`--merge`, operator-approved). Reviewed HEAD
  was `a287ab9f`, with `READY_WITH_FOLLOWUPS` and P0=0, P1=0.
* 2527 tests OK (54 skipped). CI was green and P-018 was `SATISFIED`.
* U1a added `assess_cascade_engine_semantics` and `select_close_path`. U1b
  added the read-only INV-12 planner `compute_linked_deliberation_disposition`.
* Neither has a runtime caller until slice 6 (206-S), so the slice is inert on
  `main`.

## Close

* The classifier returned `CASCADE`. The qualifying feature is `196-F`, with
  no out-of-manifest descendants and no linked deliberations (T2
  deliberation-clean). Revalidation showed no drift.
* `backlogit shipment ship` (1.11.0) archived the 9 manifest items and
  `202-S`, with `returned_ids: []`. Both two-set checks passed, `parent_id`
  was preserved, and a whole-tree diff found no out-of-scope change.
* The record is `archived_status: shipped`. Pre-mode and post-mode both
  returned `PROCEED`.
* One scripted pass ran under the `202-S` file lock, and the lock token stayed
  in-process only.

## Learnings

* The `backlogit shipment ship` cascade took about 8 minutes of CPU-bound
  engine time for 10 artifacts. Allow for that time; it is not a hang.
* The global `autoharness.exe` is stale and lacks `gate closure-evidence`. Use
  `uv run autoharness gate closure-evidence` from the repo.
* Closures run on a `chore/` branch plus a PR, because rulesets reject direct
  pushes to `main`.

## Open Items

* P-021 deferred entries `D6CCDE2C`, `3C09D9D0`, `6F2C4BFD`, `013363F5`, and
  `492FB413` are still active. Stage owns them.
* The next shipment is `203-S` (slice 2, 197-F). It is queued and its blocker,
  202-S, has shipped.

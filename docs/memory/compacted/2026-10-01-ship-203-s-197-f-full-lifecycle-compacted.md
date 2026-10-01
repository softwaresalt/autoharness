---
title: "Ship 203-S / 197-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 203-S / 197-F (195-F slice 2 of 6: planner fail-closed hardening, P-015 flat sets, engine-gate precondition and INV-12). Covers PR #470 merge facts, interim rule A (stash 26D90B0F), the contemporaneous CASCADE close, and closure learnings (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-01-ship-203-s-197-f-full-lifecycle-compacted.md
date: 2026-10-01
agent: ship
session_id: ship-2026-10-01-203s-closure
compacted_from:
  - docs/archive/memory/2026-10-01-ship-203-s-197-f-closure-session.md
---

# Ship 203-S / 197-F Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/203-S-197-F-post-merge-closure.md`. Close evidence:
`.backlogit/reconcile/203-S-cascade-close-20261001-174255.md`. Plan:
`docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md`.

## Delivery

* PR #470 merged as `61e2ffea` (`--merge`, operator-approved). Reviewed HEAD
  was `b79fe20d`, with `READY_WITH_FOLLOWUPS` and P0=0, P1=0.
* 2563 tests OK. CI was green and P-018 was `SATISFIED`.

## Interim rule A

The operator decided on 2026-10-01 (stash 26D90B0F) that the
`shipment-reconcile` skill stays authoritative for closure execution until
slice 4 (199-F) merges. Where the slice-2 P-015 text conflicts with the skill,
the skill wins. Ship applied this rule to 203-S. The engine gate (1.11.0, CLI)
was `VERIFIED` and `select_close_path` returned `CASCADE`, so the skill and
P-015 agreed. The 197-F T3 SAFE_CLOSE prediction was superseded by interim
rule A.

## Close

`CASCADE` on root `197-F`, with no descendants and no linked deliberations.
`archived_ids` covered 197.001-T … 197.010-T, 197-F and 203-S, and
`returned_ids` was `[]`. All checks passed, and 203-S is
`archived_status: shipped`.

## Learnings

* Reuse the lock-held scripted run plus a renderer from `evidence.json`.
* Stash comments land in the git-ignored `.backlogit/logs/`, so record the
  decision in the closure doc.
* Next: 195-F slice 3. Interim rule A holds until slice 4 (199-F) merges.

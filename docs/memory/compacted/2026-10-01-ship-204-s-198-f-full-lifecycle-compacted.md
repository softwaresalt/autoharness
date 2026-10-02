---
title: "Ship 204-S / 198-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 204-S / 198-F (195-F slice 3 of 6: P-015 close-path gate vs INV-12 split, skill engine-semantics gate). Covers PR #472 merge facts, interim rule A (stash 26D90B0F), the first authoritative Step 0(c) engine-gated CASCADE close, and closure learnings (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-01-ship-204-s-198-f-full-lifecycle-compacted.md
date: 2026-10-01
agent: ship
session_id: ship-2026-10-01-204s-closure
compacted_from:
  - docs/archive/memory/2026-10-01-ship-204-s-198-f-closure-session.md
---

# Ship 204-S / 198-F Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/204-S-198-F-post-merge-closure.md`. Close evidence:
`.backlogit/reconcile/204-S-cascade-close-20261002-003433.md`. Plan:
`docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md`.

## Delivery

* PR #472 merged as `2770128a` (`--merge`, operator-approved). Reviewed HEAD
  was `1b605e8a`, with `READY_WITH_FOLLOWUPS` and P0=0, P1=0.
* 2573 tests OK. CI was green and P-018 was `SATISFIED`.
* Slice content: the P-015 gate vs INV-12 split (U2b) and the skill
  engine-semantics gate (U3a: all-member Step 0(b) snapshot, Step 0(c) probe
  plus `select_close_path`, and the re-probe drift HALT).

## Interim rule A

The skill stays authoritative for closure execution until slice 4 (199-F,
205-S) merges. Where P-015 and the skill conflict, the skill wins. Ship
applied the rule and appended a comment to `26D90B0F`.

## Close

`CASCADE`. The classifier found root `198-F` with no descendants and no linked
deliberations. The Step 0(c) engine gate on the CLI returned `1.11.0` /
`131577c`, `VERIFIED`, and `select_close_path` selected `CASCADE`. The
pre-invocation re-probe matched exactly. `archived_ids` covered the 8 tasks,
`198-F` and `204-S`, and `returned_ids` was `[]`. All checks passed. 198-F T4
held: every deliberation was retained, with no mutation.

## Learnings

* Step 0(c) is now the authoritative selector. Branch on `select_close_path`,
  record the raw probe, and re-probe it during revalidation.
* Next: 195-F slice 4 (199-F / 205-S). Interim rule A holds until slice 4
  merges.

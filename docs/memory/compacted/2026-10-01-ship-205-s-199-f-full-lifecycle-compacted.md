---
title: "Ship 205-S / 199-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 205-S / 199-F (195-F slice 4 of 6: skill disposition snapshot and Cascade Close flat sets). Covers PR #475 merge facts, the CASCADE close under the now-consistent skill and P-015, the retirement of interim rule A, and the archival of stash 26D90B0F (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-01-ship-205-s-199-f-full-lifecycle-compacted.md
date: 2026-10-01
agent: ship
session_id: ship-2026-10-01-205s-closure
compacted_from:
  - docs/archive/memory/2026-10-01-ship-205-s-199-f-closure-session.md
---

# Ship 205-S / 199-F Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/205-S-199-F-post-merge-closure.md`. Close evidence:
`.backlogit/reconcile/205-S-cascade-close-20261002-051236.md`.

## Delivery

* PR #475 merged as `4303e2c3` (`--merge`, operator-approved). Reviewed HEAD
  was `978dffee`, with `READY_WITH_FOLLOWUPS` and P0=0, P1=0.
* 2585 tests OK. CI was green and P-018 was `SATISFIED`.
* Review-fix cycles 4 and 5 were operator-authorized (option B). The hash
  finding was deferred to `54DDA2A6`.
* Slice content: the all-member disposition snapshot and the Cascade Close
  flat `allowed_ids` = `closure_scope(S)`, realigned with P-015.

## Close

`CASCADE`. The classifier found root `199-F` with no descendants, and the
disposition snapshot was empty. The engine gate on the CLI returned `1.11.0` /
`131577c`, `VERIFIED`, and the re-probe matched exactly. `archived_ids`
covered the 11 tasks, `199-F` and `205-S`, and `returned_ids` was `[]`. All
checks passed. The disposition step is not on main yet, so every deliberation
was retained.

## Interim rule A

Retired as of `4303e2c3`. The skill and P-015 now agree. Stash `26D90B0F` was
resolved and archived.

## Learnings

* Use the read-only planner `compute_linked_deliberation_disposition` for the
  Step 0(c), revalidation and post-cascade snapshots.
* Add the resolution note with `backlogit comment add` before
  `backlogit stash archive`, because the archive command takes no note.
* Next: 195-F slice 5 (206-S), which adds the Linked-Deliberation Disposition
  step.

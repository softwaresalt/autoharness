---
title: "Ship 175-S / 167-F full lifecycle (compacted)"
description: "Compacted Tier-1 release-unit memory for 175-S / 167-F (P-020). Covers local review cycles 1-3, P-021 captures, PR #458 with its Copilot iterations and merge, CASCADE close, and closure artifacts."
doc_type: memory
source: docs/memory/compacted/2026-09-27-ship-175-s-167-f-full-lifecycle-compacted.md
date: 2026-09-27
agent: ship
session_id: ship-2026-09-27-175-S-dark
compacted_from:
  - docs/archive/memory/2026-09-27-ship-175-s-167-f-session.md
---

# Ship 175-S / 167-F Full Lifecycle (Compacted)

Verbose original: `docs/archive/memory/2026-09-27-ship-175-s-167-f-session.md`.
Closure: `docs/closure/175-S-167-F-post-merge-closure.md`. Learning:
`docs/compound/2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`.

## Outcome

* PR #458 merged as `985e3990` (`--merge`, reviewed HEAD `34d88829`).
* 175-S archived via P-015 `CASCADE` (`archived_status: shipped`).
* Closure artifact: `docs/closure/175-S-167-F-post-merge-closure.md`.

## Timeline

1. Resumed from checkpoint `checkpoint-20260927-080155.json` and committed the
   round-1 review fixes (`3743c5cf`), with manifest checksums refreshed.
2. Review cycle 2 found P2s, fixed in `bf4b2ebe`: gate-timing contradiction,
   APFS casing, symlinked closure-dir alias, UNC resolved before containment.
3. Review cycle 3 found a P2 regression (resolved-root-only textual check),
   fixed in `650d442f`.
4. P-021 C2 captures went into `10ff43d1`: C1CAE343, 352AF87E, 40134A08,
   27F44BCE, 04B98FC2, DEEAE9F1, 9DF8BC43, 30B8411A.
5. Copilot round 1 raised 2 in-scope threads, fixed in `34d88829`: workspace
   `RuntimeError`, and `is_dir()` masking errors. Both were replied to and
   resolved. Round 2 was clean. P-018 `SATISFIED`, CI green, merged.
6. Post-merge: CASCADE close, closure artifact, compound learning
   `docs/compound/2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`.

## Notes for Successors

* Source stash FD0CCB42 was already archived at Stage harvest.
* The cascade close rewrites each task's `commit` field to the merge SHA.
* The canonical test gate needs `PYTHONPATH=src` for discovery; targeted
  module runs also need `tests` on `PYTHONPATH`.

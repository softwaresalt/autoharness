---
title: "Ship 195-S / 189-F full lifecycle (compacted)"
date: 2026-10-06
shipment: 195-S
feature: 189-F
doc_type: memory
compacted_from: docs/archive/memory/2026-10-06-ship-195-s-189-f-session.md
---

# Ship 195-S / 189-F: full lifecycle (compacted)

**Outcome.** S(B-entry), Unit B-entry of the ship lifecycle resolver
(`src/autoharness/harness_surfaces.py`: observation ledger, recheck and
`inputs_sha256`; the `_reduce` selector with FI-5 early return and the public
`resolve_shipment` entry; and `autoharness harness resolve` in
`src/autoharness/cli.py`), shipped in PR #500 and merged as `c68d6465` with
`--merge`. It closed by cascade (classifier `CASCADE`, engine `VERIFIED`).
The closure artifact is `docs/closure/195-S-189-F-post-merge-closure.md`,
with the `harness resolve` transcript for one fixture per state.

## Decisions

* **Tooling.** `uv run` could not build offline and the global
  `autoharness.exe` was a stale 1.5.0, so every `autoharness` command ran the
  checkout's CLI through a git-ignored `src` wrapper (`C4D5B676`). Every
  test, hook and push rerouted `TEMP`/`TMP`/`TMPDIR` and
  `GIT_CEILING_DIRECTORIES` to `.proof-scratch/195-S/tmp` (Principle IV).
* **Operator-local files.** `.github/copilot/settings*.json` were treated as
  out-of-scope operator state and never staged; stash line `A34432A2` from a
  prior Orchestrator run was carried unchanged into the claim commit.
* **Design.** Surfaces are classified even when class 2/3 facts exist (no
  short-circuit); `_Recheck.changed_stage` is the one class-1 source; a
  recheck that does not complete gives the original stage's code; the
  digest binds root-relative paths and raw bytes only, so it is the same in
  any location and on Linux CI; declarations after a class 1/1b result are
  best-effort.
* **Stash `672A3F27`** (B-entry design inputs) stayed untriaged; it was read
  only as non-binding guidance (`task_id_sort_key` reused, no `read_` prefix
  in non-1b diagnostics, `_reduce` the only result selector).

## Evidence

* IM-14 harvest audit before the claim: `90f23361`, `d633cd58`, `7ca13f66`:
  6 hits, all the IM-14 disclaimer. Merge-diff audit at closure: 2286 added
  lines, 5 hits, all non-claims, `LEDGER` count 0.
* RED per task (canonical command): B4a 13/13 `9b395203`, B4b 11/11
  `68033fe5`, B5 `76df115c` (7 ERROR, roster of record 4 after the review).
  GREEN `e929dae5` 3367, `99c496d0` 3381, `83b57e87` 3391, all OK.
* Local review: nine personas, first pass `BLOCKED` (Constitution P1, preamble
  RED), fixed `e38eb58f`; delta re-review clean of P0/P1, P2/P3 fixed
  `56a239c5`; `READY_WITH_FOLLOWUPS` at `ee96ebc2`. Full local build 3396 OK.
* Copilot iteration 1: no findings; P-018 `SATISFIED`. CI green; IM-01 Linux
  evidence in run 37432720612.

## Learnings

* A roster test must reach its stub through its own specified behavior;
  argparse-only and already-green tests are characterization
  (`docs/compound/2026-10-06-red-roster-attribution-preamble-calls.md`).
* Never `open(p, "wb")` and read `p` in the same expression: the truncating
  open runs first. A scratch normalization did this once and emptied two
  uncommitted test files, which were recreated before their RED run.
* Mutating backlogit CLI commands wrote and then hung on this host; confirm
  the write on disk and in `.backlogit/logs/<id>.jsonl`, then stop the
  process (`DF404895`).

## Follow-ups

`8BB8CCD9`, `B868F321`, `09ECA5E2`, `7E1BC498` (P-021 deferred from the local
review), `DF404895`, `C4D5B676` (closure), and the existing `DB2E092B`
(stale `harness_status` on `189-F`).

---
title: "Ship 193-S / 187-F full lifecycle (compacted)"
date: 2026-10-05
shipment: 193-S
feature: 187-F
doc_type: memory
compacted_from: docs/archive/memory/2026-10-05-ship-193-s-187-f-session.md
---

# Ship 193-S / 187-F: full lifecycle (compacted)

**Outcome.** S(C), Unit C's portable ordinary-containment reader
(`src/autoharness/harness_read.py`), shipped in PR #496 and merged as
`0a6052f9` with `--merge`. It closed by cascade, with classifier `CASCADE` and
engine `VERIFIED`. The closure artifact is
`docs/closure/193-S-187-F-post-merge-closure.md`.

## Decisions

* **TDD.** P-002/P-004 TDD ran per task with the canonical command. RED
  stubs took `<t>` from the test method name by stack inspection. This is a
  recorded deviation; the stubs existed only in the RED commits.
* **Proof G mapping.**
  * G30 is in C4.
  * G32 is in C2 (roster) and C4 (characterization).
  * The Linux-only G31 class is G31a (the FIFO row) plus G31b and G31c (the
    device-node checks).
  * The G21 case is probed rather than assumed.
* **Containment.**
  * `realpath` is used, plus canonicalization of the deepest existing
    ancestor when the target is missing (8.3 short names).
  * The comparison is `commonpath` over `normcase` plus an exact-case
    component match (the Copilot finding on case-sensitive directories).
  * `.autoharness` must be the workspace's own directory, never a link.
* **IM-01 evidence.** It comes from the PR's CI step. The job URL is
  printed from `job.check_run_id`. The result: kernel 6.17 azure, ext4 for
  both the checkout and the fixture root, 94 tests OK with 0 skips.
* **IM-02 evidence.** Windows, NTFS, symlink privilege held, 95 tests OK with
  3 skips (all in the G31 class).

## Gates and evidence

* The IM-14 harvest audit covered `45c85206` (non-claims only) and merge
  `e38ac305` (conflict-free).
* The merge-diff residue audit found 24 hits, all non-claims. LEDGER count is
  0.
* Copilot: round 1 left 1 thread, which was fixed (`55e62581`), replied to and
  resolved. Round 2 found nothing. The P-018 gate returned `SATISFIED`.

## Learnings

See `docs/compound/2026-10-05-windows-realpath-containment-short-names-and-case-sensitive-dirs.md`.

## Deviations (P-005)

* **Principle IV.** Ship wrote WSL2 home scratch outside the worktree
  (`~/ahlc*`, `~/rt*`). The operator needs to clean it up.
* **187.005-T.** Its `harness-ready` label was recorded after its commit.

## Follow-ups

Stash entries:

* `AC437919`: lexical and resolution extensions
* `62FBC9A3`: Unit B notes, including the `workspace_root` existence decision
* `8F4D8A21`: move the IM-01 bash into `scripts/`

The release hold continues (EC980E56, 21CDBC0A).

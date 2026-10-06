---
title: "Ship 194-S / 188-F full lifecycle (compacted)"
date: 2026-10-06
shipment: 194-S
feature: 188-F
doc_type: memory
compacted_from: docs/archive/memory/2026-10-06-ship-194-s-188-f-session.md
---

# Ship 194-S / 188-F: full lifecycle (compacted)

**Outcome.** S(B-core), Unit B-core of the ship lifecycle resolver
(`src/autoharness/harness_surfaces.py`: the `harness-resolution` 1.0.0 result
contract with its 47-code registry and schema mirrors, records and membership,
and manifest classification), shipped in PR #498 and merged as `5be0fd31` with
`--merge`. It closed by cascade, with classifier `CASCADE` and engine
`VERIFIED`. The closure artifact is
`docs/closure/194-S-188-F-post-merge-closure.md`.

## Decisions

* **Halt and resume.** The first session halted before PR creation, because the
  pre-push hook ran tests under the default Windows `%TEMP%` (Principle IV). The
  operator accepted that instance and approved the resume. Every later test, hook
  or push command rerouted `TEMP`/`TMP`/`TMPDIR` to `.proof-scratch/194-S/tmp`.
* **`GIT_CEILING_DIRECTORIES`** must be the temp dir itself. The repository's
  parent is not enough: three "outside git" tests fail.
* **Copilot round 1:** `ResolutionResult` accepted integral floats for
  `exit_code`. In scope (P-021 C1). Fixed test-first in `ffdd58cc` with
  `type(exit_code) is int`. Round 2 found nothing.
* **CLI without network.** `uv run` could not resolve `hatchling`, so the CLI ran
  from `src/` through `autoharness.cli.main`.
* **Lock token.** The close ran as one scripted invocation (acquire, pre-mode,
  classify-only, mutating close, post-mode, release) so the lock token stayed in
  memory.

## Gates and evidence

* Local review `READY_WITH_FOLLOWUPS`, P0=0, P1=0 at `ffdd58cc`; full suite 3352 OK
  (57 skipped).
* IM-01 (job 112045733872): Linux, ext4, 94 tests OK, 0 skips.
* P-018 `SATISFIED: PASS`, including the re-run just before merge. CI green.
* IM-14 merge-diff audit: 3 hits, all task-AC non-claims; LEDGER 0.
* Checkpoint `checkpoint-20261005-190641.json` restored on operator confirmation
  and resolved after merge.

## Learnings

See `docs/compound/2026-10-06-in-repo-temp-containment-and-git-ceiling-directories.md`.

Gotchas:

* A `git add` that names a path already staged as a rename fails the whole add.
  Stage the remaining paths and the renamed file's content separately.
* `wsl -d X -- sh -c '...'` is expanded by the outer login shell first. Use
  `--exec`.

## Follow-ups

Stash entries:

* `672A3F27`: B-entry design inputs
* `DFDC3852`: D1 consumer inputs
* `8B8B7744`: residual P3 coverage and maintainability
* `B99B661D`: pre-push TEMP containment and ceiling-sensitive tests
* `DB2E092B`: stale `harness_status`

Cleanup: the WSL scratch of `15B29E66` was deleted under operator approval, and
`15B29E66` was archived. The release hold continues: no tag may include S(B-core)
before S(B-entry) closes (EC980E56, 21CDBC0A).

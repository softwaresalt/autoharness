---
shipment: 193-S
feature: 187-F
pr: 496
prs: [496]
merge_commit: 0a6052f94a3d29733bf71cefd757ee686838b1b7
reviewed_head: 55e62581
date: 2026-10-05
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
    - description: "Consumer release hold continues from 192-S: no release tag or publish may include S(C) while stash entries EC980E56 and 21CDBC0A stay open. S(C) itself has no tag, publish or release-record obligation. The reader has no caller until Unit B (S(B-core)), so it stays inert."
      satisfied: true
      evidence: "No tag was created. The hold is recorded in PR #496's body and in this artifact's Releasability Evidence."
close_path: cascade
close_evidence: docs/closure/evidence/193-S-187-F-close-evidence.json
---

# 193-S / 187-F Post-Merge Closure: Ship Lifecycle Unit C, Portable Ordinary-Containment Reader

## Summary

Shipment 193-S is release unit S(C) of the plan
`docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md` (revision 9,
blob `b7a77c76`, Unit C). Its position in the release chain is
S(A) -> **S(C)** -> S(B-core) -> S(B-entry) -> S(D). It delivers feature 187-F
through five tasks:

* **187.001-T (C1): contracts and lexical rejection.** Adds the closed public
  surface of `src/autoharness/harness_read.py`. There is no adapter, opener or
  callback parameter. Lexical rejection uses no filesystem access and makes no
  file claim. The module docstring carries the required non-claim sentence.
* **187.002-T (C2): static roots and resolved-path containment.**
  * Containment is resolved with `realpath` and checked by the private
    `_is_contained`, which compares `commonpath` over `normcase` forms and
    also requires an exact-case match of the root's components.
  * Containment is judged before existence.
  * A `.autoharness` that is itself a link is never a trust root.
* **187.003-T (C3): bounded reads and read budget.** Files are opened
  unbuffered and binary, and every read goes through the private
  `_read_chunk`. The size is checked from `fstat` before any read. The read
  loop is bounded by `min(max_file_bytes, remaining) + 1` bytes. Bytes beyond
  the reservation are charged. There is no truncated or partial success.
* **187.004-T (C4): non-regular targets.** Any target that is not a regular
  file returns `NOT_REGULAR_FILE`. The check runs after containment (`stat`)
  and again after open (`fstat`).
* **187.005-T (C5).** Three parts:
  * the Linux-native CI step, `Linux-native containment gate (IM-01)`;
  * the Proof G case-coverage test;
  * the non-claim audit test. FLOOR is `harness_read.py` and the LEDGER is
    empty.

Review authority is the E5 Verdict (`PASS`) in
`docs/reviews/2026-09-25-ship-lifecycle-release-units-plan-review.md`, read
under OP-5. That PASS gave no claim authority (IM-15); the ordinary P-001,
P-002/P-004, review, CI and P-020 gates were applied.

**PR #496** (`feat(harness_read): S(C) ship lifecycle Unit C ...`) merged as
`0a6052f9` at `2026-10-05T16:13:54Z`, using `--merge` (two parents). The
reviewed HEAD was `55e62581`. The PR ran under dark mode (P-017).

## Gates

| Gate | Result |
|---|---|
| Startup | **Tools:** backlogit MCP was not exposed, so the CLI fallback was used (`INDEX_SYNC_OK (CLI fallback)`). Intercom, engram and graphtor were not exposed (degraded). **Checkpoints:** an unfiltered scan of 98 records found 0 anomalies and 0 active `ship` candidates |
| IM-14 harvest audit (before claim) | Harvest commit `45c85206` (own diff): every hit is a non-claim. Its merge `e38ac305` is conflict-free (the remerge-diff is empty; IM-14-F67). Details are in the session note |
| Claim | `pre_claim` exited 0 twice (`forced: false`, predecessor 192-S `explicit`). After the claim, every member was `active` (P-002.7 T1). `post_claim` exited 0 (`CLAIM_VERIFY_OK`) |
| TDD (P-002/P-004) | Per task, the canonical command produced a roster RED with each test's own marker: C1 27/27, C2 19/19, C3 16/16, C4 2/2 on Windows and 4/4 on Linux. C5 is `harness-surface:none` |
| Local review (P-014) | Personas: Correctness, Python, Maintainability, Constitution, Learnings, Security, Concurrency, plus an adversarial design pass and two delta re-reviews. Result: `READY_WITH_FOLLOWUPS` with P0=0 and P1=0 at `55e62581` |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests` returned `Ran 3267 tests ... OK (skipped=57)` at `55e62581` (the pre-push gate) |
| Copilot review (P-018, elevated to required) | **Round 1 (`82e63cab`):** 1 thread, a containment escape through Windows case-sensitive directories. Fixed in `55e62581`, replied to and resolved. **Round 2 (`55e62581`):** no findings. `autoharness gate copilot-review 496 --enforcement required` returned `SATISFIED: PASS`, including the re-run just before merge |
| CI | Every check passed at `55e62581`: `detect code changes`, `pipeline-topology (ambient)`, `test` and `ci gate` |
| P-009 / P-016 | Only merge commits are allowed, and the merge commit has two parents. There is one worktree |
| Merge confirmation | `MERGE_CONFIRMED`: PR #496 merged at 2026-10-05T16:13:54Z as SHA `0a6052f9`, which is an ancestor of `origin/main` |

## Validator Evidence / Runtime Verification

There are no runtime surfaces: the reader is internal and has no caller until
Unit B. The validator evidence consists of the IM-01 and IM-02 runs.

**IM-01 (Linux-native, from PR #496 CI log; evidence of record at `55e62581`).**

* Job: <https://github.com/softwaresalt/autoharness/actions/runs/37337749449/job/111856789610>
* Host: runner OS Linux, `platform.system()` Linux, kernel `6.17.0-1022-azure`
* Fixture root: `/home/runner/work/_temp`, which equals `RUNNER_TEMP`
* Filesystems: checkout and fixture root are both `ext2/ext3` (ext4)
* Result: `Ran 94 tests`, `OK`, exit code 0, 94 passed and 0 skipped. G31a,
  G31b and G31c ran natively.
* The earlier HEAD `82e63cab` (job `111847222748`) shows the same facts with
  93 tests.

**IM-02 (Windows, Ship local run at `e0d563ab`).**

* Host: Windows `10.0.26300`, Python 3.14.3
* Filesystems: the checkout and `TMP`/`TEMP` (`.proof-scratch/tmp`, which is
  Git-ignored per NOROW-F18) are both NTFS
* Symlink privilege was held
* Result: 95 tests `OK (skipped=3)`. The three skips are the Linux-only G31
  class: G31a is the Proof G FIFO row; G31b and G31c are the C4 device-node
  checks. Skip accounting holds.

## IM-14 Incremental Residue Text Audit (merge diff)

The plan's detector ran over every added line of the merge diff
`6ac3d486..0a6052f9` (1817 added lines), including joins of adjacent lines. It
found 24 hits, all non-claims:

* `src/autoharness/harness_read.py`: 1 hit, the required sentence, which clears.
* `tests/test_harness_noclaim_audit.py`: 21 hits:
  * the required sentence
  * the detector regex
  * the must-fail control fixtures
  * a LEDGER control fixture
* `tests/test_harness_read_lexical.py`: 2 hits, the required sentence and the
  dropped `RACE` code name, asserted absent.

A camelCase scan (IM-14-F35) found 1 line: the audit docstring that documents
the camelCase residue rule, which is a non-claim. **`LEDGER` count: 0.** The
FLOOR file has no hit outside the required sentence. The closure PR's own diff
is audited in its PR body.

## Closure Path

`close_path: cascade`. The `close_evidence` record is
`docs/closure/evidence/193-S-187-F-close-evidence.json` (phase `post_close`,
run `7a58b02770244d9cb213991de068c04a`, `merge_commit_sha` `0a6052f9…`).

* **Lock.** `.backlogit/queue/193-S.md` was held from pre-mode
  (`2026-10-05T16:16:04Z`) through post-mode.
* **Classification.** Classify-only returned `CASCADE` with qualifying root
  `187-F`, no out-of-manifest descendants and engine `VERIFIED`. It was
  committed in `61b566b0`.
* **Timeout.** N = 7, so B = 567 s. The default `--timeout` (1800 s) applied.
  The run was supervised attached until it exited 0 (16:17:21Z to 16:22:01Z).
* **Approval.** The operator's dark-mode instruction directed closure with the
  classifier-selected close path (P-015).
* **Postconditions:**
  * `archived_ids` = `required_ids` = `allowed_ids` = {`187-F`, `187.001-T`
    to `187.005-T`, `193-S`}
  * `returned_ids` `[]`
  * `parent_id_preserved` and `baseline_invariant` are both `true`
  * the shipment is `status: archived`, `archived_status: shipped`
* **Commits.** `03300489` and `3bb71371`. The first captured only the staged
  shipment-record rename, because one pathspec was already staged; the second
  completes the set.

Reports:

* Pre-mode: `.backlogit/reconcile/193-S-pre-20261005-161630.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/193-S-cascade-close-20261005-162201.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/193-S-post-20261005-162227.md` (`PROCEED`)

## Linked-Deliberation Disposition (P-015 INV-12)

The planner snapshot was empty, and `linked_deliberation_drift` is `[]`. No
deliberation was mutated. **`recommendation: DISPOSITION_COMPLETE`**.

## Source Artifact Cleanup

| Item | Field | Value | Outcome |
|---|---|---|---|
| `187-F` | `source_stash_id` | (absent) | `none` |

## Releasability Evidence

* **Status.** `READY_WITH_CONDITIONS`. The only condition is the consumer
  release hold carried over from 192-S (EC980E56, 21CDBC0A). It is recorded,
  and no tag was created.
* **Monitoring.** None is required. The module has no caller until S(B-core),
  so it is inert.
* **Rollback.** Revert C's commits, which needs operator approval, while
  S(B-core) has not merged. If B has merged, B is reverted first.
* **Owner and validation window.** Ship owns rollback, with operator approval.
  The validation window lasts until S(B-core) merges.
* **Plan coverage note.** C2's verification list names G30 and G32. G30 is
  verified by C4's module, because a directory read is `IO` before C4. G32 is
  verified in both modules.

## Follow-Up Items

* `AC437919`: Unit C lexical and resolution extensions (empty components,
  Windows-invalid characters, `\\?\` long-path forms). Needs deliberation.
* `62FBC9A3`: Unit B consumption notes, including the decision on whether a
  `workspace_root` must exist. Needs deliberation.
* `8F4D8A21`: move the IM-01 bash into `scripts/`.

## Residual Risks

* **`\\?\` path prefix.** For targets beyond `MAX_PATH`, `realpath` can keep a
  `\\?\` prefix. Such targets fail closed as `OUTSIDE_TRUST_ROOT` (`AC437919`).
* **`.AutoHarness` spelling.** On Windows, an on-disk `.AutoHarness` spelled in
  a different case fails the exact-root check, and every AUTOHARNESS read is
  `OUTSIDE_TRUST_ROOT`. This fails closed.
* **Principle IV deviation (P-005).** Ship left disposable scratch outside the
  worktree, in the WSL2 home directory: `~/ahlc`, `~/ahlc-tmp`, `~/ahlc-full`,
  `~/ahlc-full-tmp`, `~/rt`, `~/rt-bin` and `~/rt-python`. Operator cleanup is
  pending; removing them needs approval.
* **Marker derivation.** RED-phase marker suffixes came from the calling test
  method name, which is a recorded deviation. These stubs existed only in the
  RED commits.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment.** `docs/memory` held 182 files (about 1325 KB). That is
  above the generic thresholds in aggregate.
* **Candidates.** This was a bounded, per-merge Tier-1 pass: the P-020 floor
  for the release unit just closed. The single 193-S session memory was
  consolidated into
  `docs/memory/compacted/2026-10-05-ship-193-s-187-f-full-lifecycle-compacted.md`.
  The verbose original, which holds the IM-14 harvest-commit audit, is in
  `docs/archive/memory/`.
* **Not processed in this run.** The reasons are real limits, not freshness:
  * **Other release units' memories.** These are not owned by this shipment
    (P-021 C1). The aggregate backlog predates it, as recorded in 192-S.
  * **Closure records.** They serve as predecessor-closure evidence at their
    canonical paths.
  * **Plans.** Stage owns them (P-010).
* **Report.** 1 file compacted and 1 compacted summary written. 0 plans were
  consolidated, 0 closure records compacted, and 0 active checkpoints
  touched. Nothing was deleted.

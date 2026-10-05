---
shipment: 189-S
feature: 183-F
pr: 492
prs: [492]
merge_commit: a28fb79767612f49f113657444c209a21fd82dd0
reviewed_head: 4e8ad8bb
date: 2026-10-05
closure_status: READY
compaction_status: pending
close_path: cascade
close_evidence: docs/closure/evidence/189-S-183-F-close-evidence.json
---

# 189-S / 183-F Post-Merge Closure: Graphtor MCP Shim Test Synchronization Repair

## Summary

Shipment 189-S (SHIP-23) delivers feature 183-F. It repaired a timing defect
in `tests/test_graphtor_mcp_shim.py`. The test
`GraphtorMcpShimHandshakeTests.test_child_stdin_write_error_fails_requests_without_crashing`
used to wait a fixed 300 ms. It now waits until the fake child process
reports that it has closed its stdin, then sends the first write. Production
`scripts/graphtor-mcp-shim.cjs` was not changed.

The manifest is `183-F` plus one task, `183.001-T` (size S). The sources are
stash entries `24A85BF8` (the survivor) and `AD3D41FA` (a merged duplicate),
and the decision record
`docs/decisions/2026-09-20-graphtor-shim-test-synchronization-defect-family-deliberation.md`.

This shipment closed work that was already merged. The implementation commit
`622a41a1` ("test: deterministic child-stdin-close sync in graphtor-mcp-shim
stdin write error test") reached `main` through PR #457 (merge `e38ac305`).
At that time, on operator instruction, the backlog lifecycle was left at
`queued`.

**PR #492** (`chore(backlog): 189-S lifecycle closure — re-verify and
complete 183-F/183.001-T (impl merged via #457)`) changed only backlog files.
It claimed 189-S, linked `622a41a1` to 183.001-T, and moved 183.001-T and
183-F to `done`. It merged as `a28fb797` at `2026-10-05T03:28:57Z`, with
reviewed HEAD `4e8ad8bb`.

## Gates

| Gate | Result |
|---|---|
| Pre-claim topology gate | `pipeline-topology --phase pre_claim`: exit 0 from `main` and again from the shipment branch. `forced: false`. Predecessor `190-S` was `explicit`. No bootstrap grant was used |
| Claim | `backlogit shipment claim 189-S`: `queued` → `active`; members `active` (P-002.7). `post_claim`: exit 0 (`CLAIM_VERIFY_OK`) |
| Feature PR merge | #492 `a28fb797`, `MERGED` by merge commit (P-009). `a28fb797` has two parents (`c23c8bd3`, `4e8ad8bb`) and is an ancestor of `origin/main` |
| Merge authority | Explicit operator approval (not dark mode). The Orchestrator re-ran the P-018 gate and merged with `--merge --match-head-commit 4e8ad8bb…` |
| Local review | Correctness and Constitution reviewers at `4e8ad8bb`: P0 = 0, P1 = 0, P2 = 0, P3 = 4 (advisory). Outcome `READY_WITH_FOLLOWUPS`, with residual-risk notes and no new stash entries |
| Copilot review | One review on `4e8ad8bb` ("Approval recommended", no findings, 0 threads). `autoharness gate copilot-review 492`: `SATISFIED: PASS` |
| CI | Green on `4e8ad8bb`. `test` was skipped because the PR changed no code |
| Pre-merge full build | Not applicable (backlog-only PR). The pre-push hook ran the full suite anyway: `Ran 3143 tests`, `OK (skipped=54)` |
| Closure lifecycle topology gate | `autoharness gate pipeline-topology --mode agent --shipment 189-S --phase lifecycle --json`: exit 0 on `chore/189-s-closure` (`BRANCH_OK`, `WORKTREE_TOPOLOGY_OK`, sole active shipment `189-S`, predecessor `190-S` explicit) |
| Pre-mode reconcile | `PROCEED`. 2 items, both `done` in archive (`pre-archived`); no orphans; `record-consistent` |
| `--classify-only` | Exit 0: `CASCADE`, engine `VERIFIED` (`1.11.0` / `131577c`, cli) |
| Mutating `cascade-close` | Exit 0, `postcondition_verdict: pass`. The `backlogit shipment ship` child took about 156 s |
| INV-12 disposition | `DISPOSITION_COMPLETE` (empty disposition set) |
| Post-mode reconcile | `PROCEED` |
| Closure index resync | Pending (final step) |
| Closure-evidence gate | Pending (run before each commit of this record) |

## Validator Evidence / Runtime Verification

183-F is a change to test code only. Its runtime proof is the targeted test,
run repeatedly on Windows and Node to show the race is closed rather than
just lost less often. Order of runs, required by 183.001-T:

1. Targeted test
   `python -m unittest tests.test_graphtor_mcp_shim.GraphtorMcpShimHandshakeTests.test_child_stdin_write_error_fails_requests_without_crashing`
   (`PYTHONPATH=src`) on current `main` content (`c23c8bd3`): **OK**
   (0.86 s).
2. The same test 10 times in a row (Windows, Node v24.12.0): **10/10
   green**.
3. Canonical suite `PYTHONPATH=src python -m unittest discover -s tests`,
   run by the normal pre-push hook without `--no-verify`: `Ran 3143 tests`,
   `OK (skipped=54)`. All local quality gates passed.

`tests/test_graphtor_mcp_shim.py` and `scripts/graphtor-mcp-shim.cjs` are
unchanged since `622a41a1`, and `622a41a1` is an ancestor of `origin/main`.
Runtime verification: **PASSED**. `RUNTIME_VERIFICATION_BLOCKED` does not
apply.

## Closure Path

`close_path: cascade`. `close_evidence`:
`docs/closure/evidence/189-S-183-F-close-evidence.json` (phase `post_close`,
run `546cca9f17004117b0fd9f22e427bffe`, `merge_commit_sha` `a28fb797…`).

* **Lock**: `.backlogit/queue/189-S.md` was held from pre-mode
  (`2026-10-05T03:31:49Z`) through post-mode (released
  `2026-10-05T03:38:37Z`).
* **Classification**: classifier `CASCADE`, with qualifying root `183-F` and
  no descendants outside the manifest. The disposition snapshot is empty.
  The classify-only record (run `78d619c0e420430a850c87913b11d130`) was
  committed in `a8a8edb2`. The mutating run re-captured `pre_close` with
  identical member hashes, so it did not exit 4.
* **Timeout sizing**: N = 2 + 1 = 3. B = ceil(1.5 × (133 + 35 × 3)) =
  357 s, which is at most 1800 s, so the default `--timeout` (1800 s) was
  used. The Orchestrator ran the command attached and waited until it
  exited.
* **Mutating run** (Orchestrator):

  ```text
  autoharness shipment cascade-close --shipment 189-S --feature 183-F --sha a28fb797… --message "Merge pull request #492 …" --author "Derek Williams <…>" --json
  ```

  It exited 0 in under 5 minutes. The `backlogit shipment ship` child ran
  `03:34:15Z` → `03:36:52Z` (about 156 s), with `timed_out: false` and
  `mutation_state: completed`.
* **Postconditions** (from the `post_close` record):
  * `archived_ids`: `183-F`, `183.001-T`, `189-S`
  * `returned_ids`: `[]`
  * `allowed_ids` and `required_ids` are the same 3 IDs
  * `unexpected_archived` and `missing_required` are both `[]`
  * `parent_id_preserved`, `baseline_invariant`, and
    `disposition_byte_identical` are all `true`
  * shipment record `status: archived`, `archived_status: shipped`
* **Whole-tree guard**: before the run, the Orchestrator fingerprinted 1896
  files: every file under `.backlogit/queue/` and `.backlogit/archive/`, plus
  `.backlogit/stash*`, lock files included. After the run there were still
  1896 files, and exactly 4 paths had changed:
  * `archive/183-F.md` and `archive/183.001-T.md` were rewritten.
  * `archive/189-S.md` was added.
  * `queue/189-S.md` was removed.

  All 4 are in `closure_scope(S)`; 0 changes were out of scope.
* Cascade gate: **`CLOSED`**. No P-005 event. Nobody made a direct
  `backlogit shipment ship` call, and `SAFE_CLOSE` was not substituted.

## Linked-Deliberation Disposition (P-015 INV-12)

The step ran under the same lock, after `CLOSED` and before post-mode, with
all inputs taken from the evidence record. The planner result was empty, and
so was the `pre_close` snapshot, so they were equal. There was no planned
`archive`, so Ship made no deliberation mutation. The final invariance check
found no fingerprint diff (1756 non-exempt paths) and no porcelain diff.

| id | link_kinds | linking_members | outcome | reason_code | referrers |
|---|---|---|---|---|---|
| (none) | — | — | — | — | — |

There were no unresolved references and no read failures. Neither
`ENGINE_SEMANTICS_UNVERIFIED` nor `ENGINE_LINE_UNVERIFIED_ADVISORY` applies.
`stranded_linked_deliberation`: `[]`.
**`recommendation: DISPOSITION_COMPLETE`**.

Reports:

* Pre-mode: `.backlogit/reconcile/189-S-pre-20261005-033213.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/189-S-cascade-close-20261005-033820.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/189-S-post-20261005-033836.md` (`PROCEED`)

## Source Artifact Cleanup

The only shipped top-level item is `183-F`. Neither `183-F` nor `183.001-T`
has a `source_stash_id` or `source_deliberation_id` field. The sources are
named only in the description text.

| Item | Field | Value | Outcome | reason_code |
|---|---|---|---|---|
| `183-F` | `source_stash_id` | (absent) | skipped: no manifest-derived source stash to retire. Description-only sources `24A85BF8` and `AD3D41FA` stay active; follow-up `C9E87CE9` asks Stage to retire them | `no_source_stash_id` |
| `183-F` | `source_deliberation_id` | (absent) | skipped: no linked deliberation (the disposition set was empty). The decision record is unchanged (P-010) | `no_source_deliberation_id` |

Archived source artifacts: 0 stash entries and 0 deliberations. Ship made no
change to plan, decision, review, or spike artifacts (P-010).

## Releasability Evidence

* **Status**: READY. The change (`622a41a1`) has been on `main` since PR #457.
  PR #492 only records the backlog lifecycle.
* **Invariants to preserve**:
  * `test_child_stdin_write_error_fails_requests_without_crashing` waits for
    the fake child to report that stdin is closed. It must never go back to
    a fixed sleep.
  * The test still separates the `child.stdin` stream-error path from the
    ChildProcess `close` path.
  * `scripts/graphtor-mcp-shim.cjs` keeps routing `child.stdin.on('error')`
    to `handleChildTermination`.
* **Deployment path**: merge-only. This is a test-only change with no impact
  on installed consumers.
* **Monitoring**: the canonical unit suite (pre-push hook and the CI `test`
  job) on Windows and Node.
* **Healthy signals**: the targeted test passes on every full-suite run.
* **Failure signals**: any failure or timeout in the targeted test
  (`messages seen: []`), or the universal circuit breaker
  `graphtor-mcp-shim-child-stdin-write-error-no-response` tripping again.
* **Rollback trigger**: the targeted test failing again in a way traceable
  to the synchronization change.
* **Rollback procedure**: `git revert 622a41a1`, or `git revert -m 1
  e38ac305` for the PR #457 merge. The backlog state committed by this
  closure stays valid either way. Individual archived records can be
  restored with `backlogit restore`.
* **Owner**: operator (softwaresalt). The Ship agent owns closure mechanics.
* **Validation window**: the next 10 full-suite runs (pre-push or CI) on
  Windows.
* **Risky action record**: the mutating `cascade-close` is destructive and
  archived 3 artifacts (ActionRisk high). It was approved by the operator's
  merge approval plus the classify-only `CASCADE` / `VERIFIED` routing, and
  the Orchestrator ran it attached with a whole-tree fingerprint before and
  after. Result: exit 0, postconditions pass.

## Verification

The feature PR's pre-push hook ran the full suite at `4e8ad8bb`:
`Ran 3143 tests in 552.248s`, `OK (skipped=54)`. The closure branch's own
pre-push run is recorded in the closure PR's readiness block.

## Follow-Up Items

All follow-ups are active stash entries, and Stage owns their triage.

* `D15F6A93` (new, task/medium): the operator asked, for deliberation,
  whether compound learning should run automatically at every shipment
  closure. The proposed rule is a mandatory per-closure compound
  evaluation, recorded as `compound_status` in closure frontmatter, with
  capture required by named criteria. It also covers periodic
  compound-refresh and installing the compound and compound-refresh skills
  in the dogfood harness. The text was captured verbatim, without triage.
* `C9E87CE9` (new, task/low): source stash entries `24A85BF8` and `AD3D41FA`
  are still active, although their work shipped (`622a41a1`, closed by
  189-S). Stage should retire them, and could have harvest stamp
  `source_stash_id` so this retirement happens automatically.

## Residual Risks

* The cascade rewrote the `commit` field on `183-F` and `183.001-T` to the
  closure merge `a28fb797`. The implementing commit `622a41a1` remains in
  git history (#457) and in the 183.001-T commit link and comments.
* `183-F` still has `custom_fields.harness_status: pending` after archival.
  This is cosmetic, and archived `184-F` has the same mismatch.
* Before closure, 183-F and 183.001-T were relocated to `archive/` as
  `status: done` rather than archived. The cascade handled them as required
  members and the postconditions passed, so nothing is outstanding.

## Compaction Status (P-020)

`pending`. `compact-context` (`target: all`) runs after this closure's
session memory is written.

---
shipment: 195-S
feature: 189-F
pr: 500
prs: [500]
merge_commit: c68d6465d2a36075fef959bf75e6e3a3f8825771
reviewed_head: ee96ebc2
date: 2026-10-06
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
    - description: "Release hold: the shipment body and plan say no release tag includes S(B-core) before S(B-entry) closes; with 195-S closed, the 192-S consumer hold (stash EC980E56, 21CDBC0A) and the CHANGELOG/contract note before the first tag that includes Unit B (stash 09ECA5E2) still apply. S(B-entry) itself has no tag, publish or release-record obligation, and harness resolve has no Ship caller until D3, so it stays inert."
      satisfied: true
      evidence: "No tag was created. The hold is recorded in PR #500's body and in this artifact's Releasability Evidence."
close_path: cascade
close_evidence: docs/closure/evidence/195-S-189-F-close-evidence.json
---

# 195-S / 189-F Post-Merge Closure: Ship Lifecycle Unit B-entry, Ledger and Digest, Reducer, resolve_shipment and harness resolve CLI

## Summary

Shipment 195-S is release unit S(B-entry) of the plan
`docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md` (revision 9,
blob `b7a77c76`, Unit B). Its position in the release chain is
S(A) -> S(C) -> S(B-core) -> **S(B-entry)** -> S(D). It completes feature
189-F through three serial tasks in `src/autoharness/harness_surfaces.py` and
`src/autoharness/cli.py`:

* **189.001-T (B4a): observation ledger, recheck and digest.** Every present
  or absent candidate and every surface read is ledgered and, unless a
  read-limit error stopped the run, re-observed through the same reader with
  new claims. A completed disagreeing recheck gives
  `INPUT_CHANGED_DURING_RESOLUTION`; a recheck that does not complete gives
  the original stage's code. `inputs_sha256` binds a domain-separated,
  length-framed preimage of every input and the result projection.
* **189.002-T (B4b): reducer, early return and entry.** `_reduce` selects
  class 1, then 1b, then the first applicable listed code; keyword-only
  `resolve_shipment(*, workspace_root, shipment_id)` with the FI-2 defaults;
  `_resolve(..., limits)` is the only B patch point (IM-06).
* **189.003-T (B5): `autoharness harness resolve --workspace <path> --shipment <id> --json`.**
  One UTF-8 document plus one LF on stdout, nothing on stderr after the
  parse, exit equal to the document's `exit_code`.

Review authority is the E5 Verdict (`PASS`) in
`docs/reviews/2026-09-25-ship-lifecycle-release-units-plan-review.md`, read
under OP-5. That PASS gave no claim authority (IM-15); the ordinary P-001,
P-002/P-004, review, CI and P-020 gates were applied.

**PR #500** (`feat(195-S): ship lifecycle Unit B-entry, ...`) merged as
`c68d6465` at `2026-10-06T08:01:25Z`, using `--merge` (two parents:
`1a6648de`, `ee96ebc2`). The reviewed HEAD was `ee96ebc2`. The PR ran under
dark mode (P-017).

## Gates

| Gate | Result |
|---|---|
| Startup | **Tools:** backlogit 1.11.0 CLI (MCP not exposed; index synced by the Orchestrator, then `backlogit sync` on the closure branch, `Indexed 1732 artifacts`). Intercom, engram and graphtor not exposed (degraded visibility; UTC milestones reported). `uv run` cannot build offline and the global `autoharness.exe` is a stale 1.5.0, so every `autoharness` command ran the checkout's own CLI through a git-ignored `src` wrapper (follow-up `C4D5B676`). **Checkpoints:** 99, 0 active, 0 quarantined; no recovery. **P-016:** one worktree throughout |
| IM-14 harvest audit (before claim) | Non-merge harvest commits `90f23361` (231 added lines, 3 hits), `d633cd58` (0 hits) and `7ca13f66` (3 hits); all 6 hits are the IM-14 disclaimer. Harvest merge `e38ac305` is conflict-free (audited at 193-S). Recorded in the session note before the claim |
| Claim | `pre_claim` on `main` and on the feature branch: exit 0 (predecessor `194-S`, `explicit`); claim written; `post_claim` exit 0; CLI re-read `active`: `CLAIM_VERIFY_OK`. Intake reconcile `PROCEED` |
| TDD (P-002/P-004) | Per task, the canonical command produced a roster RED with each test's own marker: B4a 13/13 (`9b395203`), B4b 11/11 (`68033fe5`), B5 7 ERROR (`76df115c`), of which the local review kept 4 in the roster and reclassified 3 as characterization; the captured-help structural test failed as gap characterization (CONST-II-F01). GREEN `e929dae5` (3367 OK), `99c496d0` (3381 OK), `83b57e87` (3391 OK). Every roster test and marker is listed in the session record |
| Task budgets | B4a 32 of 85 min, B4b 26 of 110 min, B5 25 of 80 min; no overrun stop |
| Local review (P-014) | Nine read-only personas over `1a6648de..83b57e87`: `BLOCKED` (Constitution P1: three B5 roster tests were RED only through a discarded preamble call). Fixed in `e38eb58f`; a delta re-review (Constitution, Correctness) found P0=0, P1=0 and P2/P3 items fixed in `56a239c5`/`ee96ebc2`. Result: `READY_WITH_FOLLOWUPS` at `ee96ebc2` |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests` -> `Ran 3396 tests ... OK (skipped=57)` at `ee96ebc2` through the pre-push hook (with `markdownlint '**/*.md'` clean), with the temp reroute |
| Copilot review (P-018) | **Iteration 1 (`ee96ebc2`, 2026-10-06T07:59:17Z):** Findings: None, 0 threads. Its overview flagged the documented filesystem and parsing resource-consumption risks for human sign-off; they are deferred captures `8BB8CCD9` and `B868F321`, and sign-off is the operator's P-017 pre-authorization. `autoharness gate copilot-review 500 --enforcement auto` (and `required`) returned `SATISFIED: PASS`, including the re-run just before merge |
| CI | Every check passed at `ee96ebc2`: `detect code changes`, `pipeline-topology (ambient)`, `test` (2m53s) and `ci gate` |
| P-009 / P-016 | The repository allows only merge commits; the merge commit has two parents. One worktree |
| Pre-PR / pre-close topology | `pipeline-topology --phase lifecycle` exited 0 before the build, before PR creation and on the closure branch before the close (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`) |
| Merge confirmation | `MERGE_CONFIRMED`: PR #500 merged at 2026-10-06T08:01:25Z as SHA `c68d6465`, an ancestor of `origin/main` |
| Dark-mode merge authorization (P-017) | `DARK_MODE_MERGE_AUTHORIZED` at 2026-10-06T08:01:21Z. Source: the activation record (`merge_approval_pre_authorized`). Strategy `--merge` with `--match-head-commit ee96ebc2`. No admin fallback (`admin_fallback_pre_authorized` false) |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/195-S-189-F-post-merge-closure.md --shipment 195-S`: while compaction was pending, only `frontmatter_predicate` failed; after compaction it exited 0 |
| Index resync | `backlogit sync` after the close, the stash captures and compaction: `CLOSURE_INDEX_SYNC_OK` |

## Validator Evidence / Runtime Verification

**Runtime surface: CLI `harness resolve` (plan Runtime Verification row
B-entry).** Recorded transcript, one fixture per state, at `c68d6465` (the
merged `main`). Each fixture is the shared test fixture (`ResolverFixture`:
shipment `7-S` with members `7-F`, `7.001-T` declaring `harness-architect`,
`7.002-T` declaring `none`) built in a git-ignored scratch directory; the
NO_HARNESS fixture removes the installed file and the UNRESOLVED fixture
removes the shipment record. The command ran in a child process as
`python -c "from autoharness.cli import main; main()" harness resolve --workspace <fixture> --shipment 7-S --json`
with `PYTHONPATH=src`, from the repository root.

| State | Exit status | stdout bytes | stdout SHA-256 | stderr bytes |
|---|---:|---:|---|---:|
| HARNESS_READY (`ALL_SURFACES_PRESENT`) | 0 | 584 | `276fabffb71f0029c614e348db134c12f3a9dbc9c12a3b1cc28ea094eb0a4477` | 0 |
| NO_HARNESS (`INSTALLED_NOT_FOUND`) | 1 | 579 | `073a15bc67fdd84bb00acb0de952bc40cd6d9dbd8ff3d399d397ecd81e9a8476` | 0 |
| UNRESOLVED (`SHIPMENT_NOT_FOUND`) | 2 | 277 | `71be2325ef8766eb7b0cfbbb141beb135ca5139293a1af2c15b94b0a1d565684` | 0 |

stdout, verbatim (each is one line followed by one LF):

```text
{"schema_version":"1.0.0","state":"HARNESS_READY","reason_code":"ALL_SURFACES_PRESENT","exit_code":0,"shipment_id":"7-S","backlog_root":".backlogit","surfaces":[{"surface_id":"harness-architect","installed_path":".github/skills/harness-architect/SKILL.md","template":"skills/harness-architect/SKILL.md.tmpl","state":"PRESENT","reason_code":"ALL_SURFACES_PRESENT"}],"declarations":[{"member_id":"7.001-T","surface_id":"harness-architect"},{"member_id":"7.002-T","surface_id":"none"}],"inputs_sha256":"37671c73e26cb3963be3b5c33e9d254f894e519e12d32e8e829c9bdaa4dd8606","diagnostics":[]}
{"schema_version":"1.0.0","state":"NO_HARNESS","reason_code":"INSTALLED_NOT_FOUND","exit_code":1,"shipment_id":"7-S","backlog_root":".backlogit","surfaces":[{"surface_id":"harness-architect","installed_path":".github/skills/harness-architect/SKILL.md","template":"skills/harness-architect/SKILL.md.tmpl","state":"MISSING","reason_code":"INSTALLED_NOT_FOUND"}],"declarations":[{"member_id":"7.001-T","surface_id":"harness-architect"},{"member_id":"7.002-T","surface_id":"none"}],"inputs_sha256":"1a36676f16ef3a88bfa0659242796ac57c60bbf4b327a26488c9429f88b5ef76","diagnostics":[]}
{"schema_version":"1.0.0","state":"UNRESOLVED","reason_code":"SHIPMENT_NOT_FOUND","exit_code":2,"shipment_id":"7-S","backlog_root":".backlogit","surfaces":[],"declarations":[],"inputs_sha256":"9ef74f0199bed483c24192c5e9abf1d8133b6c233a0efcd7786b92f2a27e769c","diagnostics":[]}
```

The three recorded documents were validated against
`schemas/harness-resolution/1.0.0.schema.json` (Draft 2020-12): all valid,
and each `exit_code` equals its exit status. The HARNESS_READY digest equals
the pinned golden `inputs_sha256`.

**IM-01 (Linux-native, PR #500 CI, evidence of record at `ee96ebc2`).**

* Job: <https://github.com/softwaresalt/autoharness/actions/runs/37432720612/job/112167224441>
* Host: `platform.system()` Linux, kernel `6.17.0-1022-azure`
* Fixture root: `/home/runner/work/_temp`, which equals `RUNNER_TEMP`
* Filesystems: checkout and fixture root are both `ext2/ext3` (ext4)
* Containment modules: `Ran 95 tests`, OK; the same job's full suite:
  `Ran 3396 tests`, `OK (skipped=13)`, including the golden digest test
  (digest stability across platforms over LF bytes).

**Windows (Ship local run at `ee96ebc2`).** Windows, NTFS, Python 3.14,
`TEMP` at the git-ignored `.proof-scratch/195-S/tmp`: 3396 tests,
`OK (skipped=57)`.

## IM-14 Incremental Residue Text Audit (merge diff)

The plan's detector (`DETECTOR`, `normalize` and the join rule from
`tests/test_harness_noclaim_audit.py`) ran over every added line of the merge
diff `1a6648de..c68d6465`, including adjacent-line joins, with rename
detection off: 2286 added lines in 13 files, 5 hits, all non-claims:

* `.backlogit/archive/189.001-T.md`, `189.002-T.md`, `189.003-T.md`: 1 hit
  each, the acceptance criterion "IM-14: no added text claims race, TOCTOU or
  hardlink-alias resistance."
* `.backlogit/stash.jsonl`: stash entry `B868F321`, whose text instructs that a
  future fix carry "no race/TOCTOU claim (IM-14)".
* `docs/memory/2026-10-06/ship-195-s-189-f-session.md` (moved by compaction
  to `docs/archive/memory/2026-10-06-ship-195-s-189-f-session.md`): the
  harvest-audit table quoting the same acceptance criterion.

`src/` and `tests/` have no hit; no join hit; a camelCase scan found 0 lines.
**`LEDGER` count: 0.** The FLOOR audit (`harness_read.py`,
`harness_surfaces.py`) is green with the LEDGER empty, and the captured
`harness resolve --help` text passes the same audit at a fixed width. The
B-entry residue units (`cli.py`, the three new test modules, the audit test
and the captured help) were each audited once in this diff and are listed in
`RESIDUE_UNITS`. The closure PR's own diff is audited in its PR body.

## Closure Path

`close_path: cascade`. The `close_evidence` record is
`docs/closure/evidence/195-S-189-F-close-evidence.json` (phase `post_close`,
run `be765dcaf9034f98bd799ef8a29daaca`, `merge_commit_sha` `c68d6465…`).

* **Context reload.** The merged `main` changed neither
  `.github/agents/_ship.agent.md` nor the `shipment-reconcile` skill; the
  close used those contracts as merged.
* **Lock.** `.backlogit/queue/195-S.md` was held from pre-mode
  (`2026-10-06T08:03:09Z`) through post-mode (released `08:09:46Z`).
* **Classification.** Classify-only returned `CASCADE` with qualifying root
  `189-F`, no out-of-manifest descendants and engine `VERIFIED` (backlogit
  1.11.0, CLI surface).
* **Timeout.** N = 5, so B = 462 s; the default `--timeout` (1800 s) applied.
  The run was supervised attached until it exited 0 (08:04:08Z to 08:09:00Z).
* **Approval.** The operator's dark-mode instruction directed closure with the
  classifier-selected close path (P-015).
* **Postconditions:**
  * `archived_ids` = `required_ids` = `allowed_ids` = {`189-F`, `189.001-T`
    to `189.003-T`, `195-S`}
  * `returned_ids` `[]`
  * `parent_id_preserved` and `baseline_invariant` are both `true`
  * the shipment is `status: archived`, `archived_status: shipped`
* **Commit.** `5b937fb6`.

Reports:

* Pre-mode: `.backlogit/reconcile/195-S-pre-20261006-080310.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/195-S-cascade-close-20261006-080900.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/195-S-post-20261006-080926.md` (`PROCEED`)

## Linked-Deliberation Disposition (P-015 INV-12)

The planner snapshot was empty, and `linked_deliberation_drift` is `[]`. No
deliberation was mutated. **`recommendation: DISPOSITION_COMPLETE`**.

## Source Artifact Cleanup

| Item | Field | Value | Outcome |
|---|---|---|---|
| `189-F` | `source_stash_id` | (absent) | `none` |
| `189-F` | `source_deliberation_id` | (absent) | `none` |

## Releasability Evidence

* **Status.** `READY_WITH_CONDITIONS`. The only condition is the release hold
  above; it is recorded, and no tag was created.
* **Monitoring.** None is required: `harness resolve` has no Ship caller until
  D3, so it is inert.
* **Rollback.** Revert merge `c68d6465` (`git revert -m 1`), then B-core's
  `5be0fd31`, with operator approval, while S(D) has not merged and no release
  tag includes Unit B.
* **Owner and validation window.** Ship owns rollback, with operator approval.
  The validation window lasts until D3 merges or a release is tagged.

## Follow-Up Items

* `8BB8CCD9`: bound PyYAML composer cost for records and the manifest (P-021
  deferred, from the local review). Needs deliberation.
* `B868F321`: Windows link targets on UNC/device paths followed before the
  containment check (P-021 deferred). Needs deliberation.
* `09ECA5E2`: S(D) D1/D3 inputs (pinned invocation, no-document rule),
  operator reference doc and CHANGELOG before the first tag (P-021 deferred).
  Needs deliberation.
* `7E1BC498`: resolver and test maintainability (P-021 deferred).
* `DF404895`: mutating backlogit CLI commands write and then do not exit on
  this host.
* `C4D5B676`: `uv run autoharness` offline failure and the stale global
  install. Needs deliberation.
* Existing `DB2E092B` also covers `189-F`'s stale `harness_status: pending`.

## Residual Risks

* **CLI internal failure.** An unexpected failure after the parse prints a
  traceback and exits 1 (the NO_HARNESS code) with no document; D1 must treat
  any output without a valid document as resolver-not-observed (`09ECA5E2`).
* **Resource cost of hostile YAML** and **Windows UNC link targets**: ordinary
  hazards reachable through the new public command, deferred as `8BB8CCD9`
  and `B868F321`; Copilot's overview flagged them for human sign-off. Ship
  merged under the operator's general P-017 pre-authorization; the operator
  should acknowledge these two risks explicitly when triaging those entries.
* **Stale `harness_status`.** `189-F` keeps `harness_status: pending` in its
  archived custom fields (`DB2E092B`).
* **backlogit hang.** Mutating backlogit CLI calls had to be stopped after
  their writes were confirmed (`DF404895`); every transition was verified on
  disk and in the item logs.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment.** `docs/memory` held 185 files (about 1340 KB), above the
  generic thresholds in aggregate.
* **Candidates.** This was the bounded, per-merge Tier-1 pass: the P-020 floor
  for the release unit just closed. The single 195-S session memory was
  consolidated into
  `docs/memory/compacted/2026-10-06-ship-195-s-189-f-full-lifecycle-compacted.md`;
  the verbose original is in `docs/archive/memory/`.
* **Not processed in this run:**
  * **Other release units' memories**, including the Orchestrator's
    `docs/memory/2026-10-05/circuit-break-backlogit-workspace-open-sandbox.md`.
    They are not owned by this shipment (P-021 C1).
  * **Closure records.** They serve as predecessor-closure evidence at their
    canonical paths.
  * **Plans.** The ship lifecycle plan still governs S(D), and Stage owns
    plans (P-010).
* **Checkpoints.** This session created no checkpoint; none is active for this
  work.
* **Report.** 1 file compacted and 1 compacted summary written; 0 plans
  consolidated; 0 closure records compacted; nothing deleted.

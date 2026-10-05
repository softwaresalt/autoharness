---
shipment: 192-S
feature: 186-F
pr: 494
prs: [494]
merge_commit: bf43cc0bfc8f8c440ab71cf15da818d5378ad92a
reviewed_head: 7c051fe9
date: 2026-10-05
closure_status: READY_WITH_CONDITIONS
compaction_status: done
conditions:
    - description: "Consumer release hold for the S(A) product templates is recorded and tracked: no release tag may publish templates/policies/workflow-policies.md.tmpl and templates/skills/harness-architect/SKILL.md.tmpl to consumers until EC980E56 (template portability of the Python-unittest RED vocabulary, AGENTS.md Core Rule 2) and 21CDBC0A (template Ship batch caller vs the single-task actor) are dispositioned. 192-S itself carries no tag, publish or release-record obligation."
      satisfied: true
      evidence: "Hold recorded in PR #494 body (Residual risk) and in this artifact's Releasability Evidence; tracked by active stash entries EC980E56 and 21CDBC0A (captured in e14a2154); Copilot threads PRRT_kwDORzpWpM6o8nZ4 and PRRT_kwDORzpWpM6o8nZV replied with these IDs and resolved."
close_path: cascade
close_evidence: docs/closure/evidence/192-S-186-F-close-evidence.json
---

# 192-S / 186-F Post-Merge Closure: Ship Lifecycle Unit A, Evidence Contract Conformance

## Summary

Shipment 192-S is release unit S(A) of the plan
`docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md` (revision 9,
blob `b7a77c76`, Unit A). It is the DAG root of S(A) -> S(C) -> S(B-core) ->
S(B-entry) -> S(D). It delivers feature 186-F through two tasks:

* **186.001-T (A1).** P-002 and P-004 now scope the red-phase (RED)
  obligation to the current task's expected-RED roster. The roster excludes
  characterization tests and structural tests that reach no stub. RED is an
  `ERROR` carrying the test's own unique `NotImplementedError` marker,
  attributed roster-relatively (R2). A marker-bearing `AssertionError` is
  refused. A `harness-surface:none` task has no roster and no RED obligation,
  and may use that label only when its file budget has no Python production
  module under `src/`. The Marker Convention is stated verbatim. History row
  `1.32.0` is added.
* **186.002-T (A2).** The harness-architect actor takes exactly one current
  task, supplied by the caller, and never claims backlog work. In a
  characterization-first posture its characterization tests sit outside the
  roster. Step 5.2 restates the A1 rules, with a refused list scoped to the
  roster. Step 6 records a per-task harness-ready evidence record. The edits
  are parallel hunks; the installed file was not re-rendered (IM-10).

Review authority is the E5 Verdict (`PASS`) in
`docs/reviews/2026-09-25-ship-lifecycle-release-units-plan-review.md`, read
under OP-5. A review or proof PASS confers no claim authority (IM-15). The
ordinary P-001, P-002/P-004, review, CI and P-020 gates were applied.

**PR #494** (`docs: 192-S ship lifecycle Unit A - ...`) merged as
`bf43cc0b` at `2026-10-05T08:02:26Z`. Reviewed HEAD was `7c051fe9`. The PR
ran under dark mode (P-017).

## Gates

| Gate | Result |
|---|---|
| Startup | Tools: backlogit MCP not exposed, so the CLI fallback was used (`DEGRADED_MODE: backlogit MCP`; `INDEX_SYNC_OK (CLI fallback)`). Intercom, engram and graphtor were not exposed (`INTERCOM_DEGRADED`, `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`). Checkpoints: an unfiltered scan of 98 records found 0 anomalies and 0 active `ship` candidates, so startup was normal |
| IM-14 harvest audit (before claim) | Ship audited the own diff of each non-merge harvest commit: `2b678b4d`, `45c85206`, `e5334864`, `90f23361`, `c70e72d0`, plus the IM-10 harvest `7ca13f66`. Every detector hit was a non-claim (see the session memory) |
| Pre-claim topology gate | `pipeline-topology --phase pre_claim` exited 0 from `main` (`BRANCH_CREATE_ELIGIBLE`) and again from the shipment branch (`BRANCH_OK`). `forced: false`, predecessor `declared_root` (`dag-root`), no bootstrap grant |
| Claim | `backlogit shipment claim 192-S` moved the shipment `queued` -> `active` and the members to `active` (P-002.7). `post_claim` exited 0, so `CLAIM_VERIFY_OK`. Intake reconcile: 3 items `active`, no orphans |
| P-002/P-004 posture | Both tasks are `harness-surface:none`, so they have no roster and no RED obligation. Work was characterization-first. Pre-edit runs of the new structural tests were recorded as gap characterization: A1 had 15 subtest failures across 9 methods, A2 had 22 across 11 |
| IM-12 | Before every refresh, the recorded checksum equaled `SHA-256(HEAD:path)`. Each refreshed value equals the SHA-256 of the raw staged blob, captured as binary through a Python subprocess. Policy: `f8e2a2d1` -> `23077e1d` -> `54108e1d` -> `c8781195`. Actor: `39089629` -> `3fb73113` -> `2d549907`. Replayed at HEAD after each commit |
| Local review | Multi-persona adversarial review covering Constitution, Python, Correctness, Maintainability, Learnings, Template Integrity, Scope Boundary and an Architecture Strategist rubber-duck pass on decisions D1–D8. All in-scope P1s were fixed in `294c30ac`. A delta re-review found 0 P0 and 0 P1, and its 2 P3s were fixed in `7c051fe9`. Outcome `READY_WITH_FOLLOWUPS`, P0=0, P1=0 |
| Lifecycle topology gate (before PR) | exit 0 |
| Copilot review (hosted, elevated to required) | Round 1 on `7c051fe9` was `COMMENTED` with 2 threads. Both were out of scope under P-021 C1: each was declined with a rationale citing its deferred ID (`21CDBC0A`, `EC980E56`), then resolved through GraphQL (`PRRT_kwDORzpWpM6o8nZV`, `PRRT_kwDORzpWpM6o8nZ4`). No code change followed, so HEAD did not move |
| P-018 | `autoharness gate copilot-review 494 --repo softwaresalt/autoharness --enforcement required` returned `SATISFIED: PASS`. It was re-run unconditionally just before merge, again `SATISFIED`, and again with the repo `.venv` CLI, again `SATISFIED` |
| §1.9 / P-014 | Reviewed HEAD matched `headRefOid` `7c051fe9`. `READY_WITH_FOLLOWUPS` with follow-up IDs. Full build evidence present. 0 unresolved threads. `mergeStateStatus: CLEAN` |
| CI | Green on `7c051fe9`: `detect code changes`, `test`, `pipeline-topology (ambient)` and `ci gate` all SUCCESS |
| Merge | `DARK_MODE_MERGE_AUTHORIZED` at `2026-10-05T08:01Z`. Approval source: the `DARK_MODE_ACTIVE` record (`merge_approval_pre_authorized: true`, scope item 192-S). Merged with `gh pr merge 494 --merge` (P-009). The ruleset allows only `merge`. No admin fallback was used, and none was authorized |
| Merge confirmation | `MERGED`. `bf43cc0b` has two parents (`e4d49a7a`, `7c051fe9`) and is an ancestor of `origin/main` |
| Closure lifecycle topology gate | exit 0 on `post-merge/186-f-ship-lifecycle-unit-a` (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`) |
| Pre-mode reconcile | `PROCEED`: 186-F `matched` (`active`), both tasks `pre-archived` (`done`), no orphans, `record-consistent` |
| `--classify-only` | exit 0: `CASCADE`, engine `VERIFIED` (`1.11.0` / `131577c`, cli) |
| Mutating `cascade-close` | exit 0, `postcondition_verdict: pass`. The `backlogit shipment ship` child took about 196 s |
| INV-12 disposition | `DISPOSITION_COMPLETE` (empty disposition set) |
| Post-mode reconcile | `PROCEED`; lock released |
| Closure index resync | `CLOSURE_INDEX_SYNC_OK`. `backlogit sync` ran after the last backlog mutation (follow-up `808BAB5E`) and reported `Indexed 1719 artifacts` |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/192-S-186-F-post-merge-closure.md --shipment 192-S --json`. With `compaction_status: pending`, the run failed only `frontmatter_predicate`, as expected. With the finalized status it must exit 0; that run is recorded in the closure PR |

## Validator Evidence / Runtime Verification

Unit A has no runtime surface; it changes text only. The plan's
"Runtime Verification and Closure" row for A requires structural tests and
checksum replay, and treats the unit as code-affecting for closure because it
changes procedure text. Both checks passed:

1. **Structural tests.** `tests/test_harness_architect_p004_contract.py`
   (`PolicyQuantifierCoherenceTests` extended for A1,
   `HarnessArchitectPerTaskSemanticsTests` for A2,
   `NonClaimDetectorControlTests`) passed. The canonical full suite
   `PYTHONPATH=src python -m unittest discover -s tests` reported
   `Ran 3170 tests`, `OK (skipped=54)` at `7c051fe9` on Windows, and CI
   `test` was green on Linux.
2. **Checksum replays.** Both manifest checksums equal `SHA-256(HEAD:path)`
   at `bf43cc0b`:
   * `.github/policies/workflow-policies.md`: `c8781195…`
   * `.github/skills/harness-architect/SKILL.md`: `2d549907…`

   The two tests `test_installed_policy_bytes_match_manifest_checksum` and
   `test_installed_actor_bytes_match_manifest_checksum` replay these checks
   on every run.

Runtime verification: **PASSED**. `RUNTIME_VERIFICATION_BLOCKED` does not
apply.

## IM-14 Incremental Residue Text Audit (merge diff)

The plan's detector was run over every added line of the merge diff
`e4d49a7a..bf43cc0b` (726 added lines), including joins of adjacent lines. It
produced 25 hits, all in `tests/test_harness_architect_p004_contract.py`. Every
hit is a non-claim:

* the detector regex itself
* test names and docstrings that assert the absence of claims
* the detector's positive-control fixtures

The policy, actor, manifest and backlog changes produced 0 hits. `LEDGER` count
is not applicable: the closed `LEDGER` and `tests/test_harness_noclaim_audit.py`
do not exist until C5 (S(C)). The closure PR's own diff is audited in its PR
body.

## Closure Path

`close_path: cascade`. The `close_evidence` record is
`docs/closure/evidence/192-S-186-F-close-evidence.json` (phase `post_close`,
run `4a56014a57ab492cabd6c3dcaf74d8f3`, `merge_commit_sha` `bf43cc0b…`).

* **Lock.** `.backlogit/queue/192-S.md` was held from pre-mode
  (`2026-10-05T08:04:21Z`) through post-mode.
* **CLI.** The global `autoharness` install (site-packages 1.5.0) predates
  the `shipment` command and exited 1, which the skill routes to HALT with
  nothing mutated. All close commands were then run with the repo `.venv`
  CLI, an editable install of `src/`.
* **Classification.** The classifier returned `CASCADE` with qualifying root
  `186-F` and no out-of-manifest descendants. The disposition snapshot was
  empty. The classify-only record was committed in `71f8a95a`.
* **Timeout sizing.** N = 4, so B = ceil(1.5 × (133 + 35 × 4)) = 410 s. That
  is under the 1800 s default, so the default `--timeout` was used. The
  command ran attached in async mode and was polled until it exited.
* **Approval.** The operator's dark-mode instruction directed full
  post-merge closure with the classifier-selected close path (P-015) for
  192-S. Together with the `CASCADE` / `VERIFIED` routing, that instruction is
  the clearance for this destructive close.
* **Postconditions.**
  * `archived_ids` = `required_ids` = `allowed_ids` =
    {`186-F`, `186.001-T`, `186.002-T`, `192-S`}
  * `returned_ids` `[]`, `unexpected_archived` `[]`, `missing_required` `[]`
  * `parent_id_preserved`, `baseline_invariant` and
    `disposition_byte_identical` are all `true`
  * shipment `status: archived`, `archived_status: shipped`
* **Change set.** The working tree changed in exactly the four
  closure-scope paths plus the evidence record.
* Cascade gate: **`CLOSED`**. No direct `backlogit shipment ship` call was
  made, and `SAFE_CLOSE` was not substituted.

Reports:

* Pre-mode: `.backlogit/reconcile/192-S-pre-20261005-080440.md` (`PROCEED`)
* Cascade close and disposition:
  `.backlogit/reconcile/192-S-cascade-close-20261005-081010.md` (`CLOSED`,
  `DISPOSITION_COMPLETE`)
* Post-mode: `.backlogit/reconcile/192-S-post-20261005-081130.md` (`PROCEED`)

## Linked-Deliberation Disposition (P-015 INV-12)

The planner snapshot was empty: no dispositions, no unresolved references, no
read failures, and `planning_error: null`. `linked_deliberation_drift` was
`[]`. No deliberation was mutated, and `stranded_linked_deliberation` is `[]`.
**`recommendation: DISPOSITION_COMPLETE`**.

## Source Artifact Cleanup

| Item | Field | Value | Outcome | reason_code |
|---|---|---|---|---|
| `186-F` | `source_stash_id` | (absent) | skipped: no manifest-derived source stash to retire | `no_source_stash_id` |
| `186-F` | `source_deliberation_id` | (absent) | skipped: no linked deliberation (empty disposition set) | `no_source_deliberation_id` |

Archived source artifacts: 0 stash entries, 0 deliberations. Ship made no
change to any plan, decision, review or spike artifact (P-010).

## Releasability Evidence

* **Status: READY_WITH_CONDITIONS.** The self-hosted harness is ready: the
  installed policy and actor text are live and inert until D3 activates Ship
  harness generation. The single frontmatter condition is satisfied: a
  consumer release hold is recorded and tracked. The hold itself stays in
  force until `EC980E56` and `21CDBC0A` are dispositioned:
  * `EC980E56`: the product templates carry the plan's Python-unittest RED
    vocabulary. That falls short of the `AGENTS.md` Core Rule 2
    (technology-agnostic templates) for non-Python consumers.
  * `21CDBC0A`: the template Ship still calls the now single-task actor "for
    the batch".
* **Invariants to preserve.**
  * Template and installed P-002/P-004 stay identical after placeholder
    substitution.
  * The actor's edited Steps 1, 2, 3 and 6 stay identical between the
    template and the installed file.
  * The Marker Convention stays verbatim.
  * No race, TOCTOU or hardlink-alias claim appears.
  * The installed actor is never re-rendered outside the IM-10 unit.
* **Deployment path.** Merge-only for the self-hosted harness. Consumer
  propagation goes through the next release tag, which is subject to the
  hold above.
* **Monitoring.** `tests/test_harness_architect_p004_contract.py` runs in
  the canonical suite (pre-push hook and the CI `test` job).
* **Healthy signals.** The contract tests stay green, and C/B/D tasks record
  their RED evidence per the roster and Marker Convention.
* **Failure signals.** A contract-test regression, or a C/B/D task unable to
  record RED under this wording.
* **Rollback trigger and procedure (plan Unit A).** The trigger is the
  operator rejecting the merged wording, or a structural test regressing.
  The procedure:
  1. Revert `7c051fe9`, then `294c30ac`, then `ab4137c5`, with operator
     approval, since this is a policy change.
  2. Replay both manifest checksums.

  This is allowed only while no C, B or D task has recorded RED evidence
  under A's wording. After that, return to Stage.
* **Owner.** The operator; the Ship agent owns closure mechanics.
* **Validation window.** Until the first C task records RED.
* **Risky action record.** The mutating `cascade-close` archived 4
  artifacts (high ActionRisk). It ran attached, its postconditions passed,
  and the change set was confined to closure scope.

## Follow-Up Items

All of these are active stash entries; Stage owns triage. Except for
`808BAB5E`, each is a P-021 C2 capture-only entry.

| ID | Priority | Expansion | Notes |
|---|---|---|---|
| `EC980E56` | high | Template portability of the Python-unittest RED vocabulary | `AGENTS.md` Core Rule 2; Copilot thread `PRRT_kwDORzpWpM6o8nZ4` |
| `21CDBC0A` | high | Template Ship batch caller vs the single-task actor | Unit D; Copilot thread `PRRT_kwDORzpWpM6o8nZV` |
| `E0136957` | medium | How a `harness-surface:none` task passes the `harness-ready` label gate | — |
| `8BE38096` | low | Step 4 per-test marker stubs | IM-10 render region |
| `4D600C75` | low | P-004 evidence-record hardening | P-004 observation-gate plan |
| `808BAB5E` | medium | Plan D3 preflight (1) FI-12 blob drift | New closure observation. The Ship template is at `51646556` and the mirror at `2fbf169e`, not the FI-12 values `4ccd7fdc` / `66933efa`, so D3 as written would halt |

The pre-existing MD001 in P-015 remains tracked by `24BA1B8F`.

## Residual Risks

* The cascade rewrote the `commit` field on `186-F`, `186.001-T` and
  `186.002-T` to the merge commit `bf43cc0b`. The implementing commits
  (`ab4137c5`, `294c30ac`, `7c051fe9`) are in git history and in each task's
  commit link.
* `186-F` keeps `custom_fields.harness_status: pending` after archival. This
  is cosmetic; `183-F` has the same leftover.
* OP-3 (operator approval of the A1 wording at its PR) was satisfied by the
  dark-mode `merge_approval_pre_authorized` record for 192-S, as recorded in
  the PR body. If the operator rejects the wording, the Unit A rollback above
  applies.

## Compaction Status (P-020)

`done`. `compact-context` ran with `target: all` after this closure's
session memory was written.

* **Assessment**: `docs/memory` held 180 files (about 1317 KB), which is
  above the generic thresholds in aggregate.
* **Candidates**: the run was a bounded Tier-1 pass over this release unit
  only. The single 192-S memory (the 2026-10-05 execution and closure
  session) was consolidated into
  `docs/memory/compacted/2026-10-05-ship-192-s-186-f-full-lifecycle-compacted.md`.
  The verbose original, which holds the full IM-14 harvest-commit audit
  table, is under `docs/archive/memory/`.
* **Excluded**:
  * other release units' memories, which are out of scope for this bounded
    run
  * plans, because Stage owns that work (P-010)
  * closure records, which are fresh (under `threshold_days`)
* **Report**: 1 file compacted, 1 compacted summary written, 0 plans
  consolidated, 0 closure records compacted, and 0 active task checkpoints
  touched. Nothing was deleted.

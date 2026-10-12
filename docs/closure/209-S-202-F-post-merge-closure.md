---
shipment: 209-S
feature: 202-F
pr: 514
merge_commit: e8693423d0a472745ee67cbfa7da21079c9bb963
reviewed_head: 8faa1f86
date: 2026-10-12
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/209-S-202-F-close-evidence.json
---

# 209-S / 202-F Post-Merge Closure: Gate-aware Orchestrator Eligibility and Dark-Mode Activation Preflight

## Summary

Shipment 209-S (covering feature 202-F; manifest `202-F`, `202.001-T` through
`202.004-T`) merged through PR #514 as merge commit `e8693423` (`--merge`, merged
2026-10-12T23:20:10Z). The merge has two parents: `6227fc09` (base) and `8faa1f86`
(reviewed PR head). The change adds a read-only, advisory per-candidate
`pipeline-topology --phase pre_claim` eligibility probe to Orchestrator Step 0 (with a
Step 2 gate-blocked first-pass skip) and a scope-head activation preflight before
`DARK_MODE_ACTIVE` is recorded, plus the `feature-flow-dark` prompt wording and a
four-scenario contract test. It is agent-instruction text only; no `src/` change.

This closure ran in the post-merge closure branch
`post-merge/s-gate-aware-orchestrator-eligibility-dark-mode-activation-preflight`. It
archived the manifest through the P-015 CASCADE path; the close is verified.

## Close Path and Evidence (P-015)

| Check | Result |
|---|---|
| Pre-Mode report | `.backlogit/reconcile/209-S-pre-20261012-232312.md`, `PROCEED` |
| Classifier | `CASCADE`; qualifying feature `202-F`; out-of-manifest descendants none |
| Engine semantics | `VERIFIED`, backlogit `1.11.0` on the CLI surface (commit `131577c`) |
| Selected close path | `cascade` |
| Agreement check (Pre-Mode report vs record) | agreed: verdict `CASCADE`, qualifying set `['202-F']` |
| Mutating `cascade-close` | exit `0`; `postcondition_verdict: pass`; `failures: []` |
| `returned_ids` | empty |
| `archived_ids` | `202-F`, `202.001-T` to `202.004-T`, `209-S` (6 of 6 required) |
| Shipment record | `shipment_status: shipped`, archived with `archived_status: shipped` |
| Baseline invariant and deliberation byte-identity | both true; `linked_deliberation_drift: []` |
| Post-Mode report | `.backlogit/reconcile/209-S-post-20261012-233553.md`, `PROCEED` |
| Evidence record | `docs/closure/evidence/209-S-202-F-close-evidence.json` (phases `pre_close` and `post_close`) |

Timeout sizing: `B = ceil(1.5 * (133 + 35 * 6))` = 515 s, within the 1800 s default; the run
was started attached and async with the 2400 s supervision budget and completed (about
15 minutes) without being killed. Lock: acquired and released (token-matched) through the
workspace-root `scripts/acquire_lock.ps1` / `release_lock.ps1`; no substitution.

## Linked-Deliberation Disposition (P-015 INV-12)

The disposition snapshot is empty: `dispositions: []`, `unresolved_references: []`,
`read_failures: []`, `planning_error: null`. Outcome: `DISPOSITION_COMPLETE`. No
deliberation was archived by hand.

## Source Artifact Cleanup

| Item | `source_stash_id` outcome | `source_deliberation_id` outcome |
|---|---|---|
| 202-F | `none` (field not declared; provenance labels `source-stash-50DCCBED`, `-8675D546`, `-F2D11D61`) | `none` |
| 209-S | `none` (same labels) | `none` |

* `50DCCBED` (P1) and `8675D546` (P3) were already archived by Stage's harvest
  (`.backlogit/archive/stash.jsonl`). No retirement action was needed.
* `F2D11D61` (the paired carryover requirements doc) was deliberately NOT retired. It is a
  living pairing entry: Stage's own triage note on it says to keep it until R1 and the
  deferred rows P2/P4/P5/P6 are staged, and shipments 210-S and 211-S (Features B and C of the
  same carryover cut) are still open. Retiring it now would drop tracking for unshipped work.

## Decisions

* **Dark-mode authority.** `DARK_MODE_ACTIVE` (P-017) scoped to exactly 209-S;
  `merge_approval_pre_authorized: true`; `admin_fallback_pre_authorized: false`. Emitted
  `DARK_MODE_MERGE_AUTHORIZED` (PR #514, head `8faa1f86`, checks green, merge-commit strategy,
  approval source the activation record, scope match).
* **Destructive-close authority.** Intercom was unavailable (no intercom tool reachable in
  this session), so the recorded authority for the mutating `cascade-close` is the
  operator's explicit task directive for this session ("archive 209-S and members correctly"
  via the shipment-reconcile safe-close/CASCADE rules), not a Ship self-clearance. `--classify-only`
  ran first (CASCADE, engine VERIFIED); the mutating run executed once, attached and async,
  with no retry and no substitution.
* **Preflight on a grant-annotated head fails closed.** The preflight never applies a bootstrap
  grant (only Step 2a can). The operator can route that shipment through a non-dark
  `ship {id}`.
* **P-017 policy text not amended here.** Out of scope for A1-A4 (P-021 C1); captured as stash
  `635D7BAC`.

## Review History (PR #514)

Local multi-persona review (report-only, single reviewed code state `825f5489`, later
`8faa1f86`): round 1 Constitution, Correctness, Maintainability, Template Integrity, Scope Boundary
Auditor, Python, Learnings Researcher; round 2 Correctness and Template Integrity. No P0/P1 at
any round; all P2 findings fixed in-branch (`e7d41b30`, `825f5489`). Model routing: reviewer
subagents ran on the harness default routing; `TOOL_DEGRADED: model-specific-review-routing —
declared fallback: same-model rubric pass`. The Copilot-round-1 fix delta (`8faa1f86`) was
re-reviewed locally by the Ship agent (single-agent pass).

| Round | Review ID | Reviewed commit | Reviewer | Findings and disposition |
|---|---|---|---|---|
| 1 | 5496867234 | `428336c6` | copilot-pull-request-reviewer | 4 inline findings (activation terminal condition omitted `head: active (resume)` and `skipped`; prompt scope head and resume path), all valid, fixed in `8faa1f86`, replied and resolved |
| 2 | 5496969771 | `8faa1f86` | copilot-pull-request-reviewer | "Approval recommended", 0 open findings, 4 resolved since last review; no threadless body findings |

All 4 review threads on PR #514 are resolved (4/4). Final P-018 gate on `8faa1f86`:
`SATISFIED`.

## Gates and Evidence

| Gate | Command or source | Result |
|---|---|---|
| Merge confirmation | `gh pr view 514`; `git merge-base --is-ancestor e8693423 origin/main` | `MERGED`, ancestor of `origin/main` (exit 0) |
| Two-parent proof | `git cat-file -p e8693423` | parents `6227fc09`, `8faa1f86` |
| CI on PR head `8faa1f86` | `gh pr checks 514` | `detect code changes`, `pipeline-topology (ambient)`, `test`, `ci gate` all pass |
| CI on merge commit | `gh run list --branch main` (run `38321588635`) | `success` |
| Local readiness (P-014) | PR body `## Local Review Readiness`, reviewed HEAD `8faa1f86` | `READY_WITH_FOLLOWUPS`, `P0=0, P1=0` |
| Copilot gate (P-018) | `autoharness gate copilot-review 514 --repo softwaresalt/autoharness` (before and again immediately before merge) | `SATISFIED`, exit 0 |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests` (pre-push hook) | Ran 3513 tests, OK (skipped=57); markdownlint on all markdown passed |
| Topology gates | `pre_claim` (x2), `post_claim`, `lifecycle` (several) | all exit 0 |
| Crash-resumption scan | `backlogit checkpoint list` | 112 records; 0 quarantined; 0 ship-owned `active`; normal startup |
| Single worktree (P-016) | `git worktree list` | one worktree: this checkout |
| Closure index resync | `backlogit sync` after all backlog mutations | `CLOSURE_INDEX_SYNC_OK`: `Indexed 1851 artifacts` |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/209-S-202-F-post-merge-closure.md --shipment 209-S` | run before each commit of this artifact; see the PR for the final result |

## Runtime Verification

* Validator contract: `runtime_validation.validator_manifest` surface `cli`, probe
  `cli-help` (required). Verdict `PASS`: `uv run autoharness --help` exit `0`, CLI usage text
  printed. The change touches only agent-instruction surfaces, so runtime exposure is
  nil; no tag or publish step applies. The `## Unreleased` section of `CHANGELOG.md` does not
  yet carry a 209-S entry (see Follow-up Items).

## Operational Closure

* `closure_status`: `READY` is the releasability verdict for PR #514's change and this
  docs-and-backlog-only closure. Closure completion is determined by the merge of the closure
  PR, whose live status is recorded in that PR.
* Invariants to preserve: Step 2a stays the only Orchestrator bootstrap-grant consumption site;
  the Step 0 probe and the dark preflight never pass `--bootstrap-grant-invocation` or `--force`;
  `DARK_MODE_ACTIVE` is recorded only after the scope-head preflight.
* Healthy signal: the next Orchestrator Step 0 reports gate-blocked candidates as
  `INELIGIBLE: {token}` (or `GLOBAL_GATE_BLOCK`) instead of reporting them ready; a dark activation on a
  gate-blocked head halts with `DARK_MODE_PREFLIGHT_BLOCKED`.
* Failure signal: a candidate reported `ELIGIBLE` that `pre_claim` later blocks, a Step 2 skip of a
  grant-annotated candidate, or a dark run recorded `DARK_MODE_ACTIVE` on a gate-blocked head.
* Rollback trigger: either failure signal. Rollback: revert merge `e8693423` through a new reviewed
  PR (template, mirror, prompt, test, manifest checksums revert together). Do not force or rewrite `main`.
* Validation window: the first two Orchestrator Step 0 passes and the first dark-mode activation
  after this closure.
* Owner: the repository operator (`softwaresalt`).

## Residual Risks

* The P-017 policy registry and `docs/pipeline-topology-gate.md` do not yet describe the preflight
  (stash `635D7BAC`).
* `verify-workspace` contract checks do not assert the new preflight tokens for other installs
  (advisory local-review note; not captured as a separate entry, to avoid duplicating `635D7BAC`'s
  parity theme; Stage may fold it into the same triage).
* `backlog_state` (BACKLOG_UNAVAILABLE) can be candidate-specific when one predecessor's
  closure artifact is malformed; the text states this in prose only.
* Archived features keep a stale `custom_fields.harness_status: pending` (202-F shows it). Already
  tracked by `DB2E092B` per the 208-S closure.
* Tool degradation: backlog MCP, GitHub MCP, and intercom tools were not available; the backlogit CLI
  and `gh` were used (`TOOL_DEGRADED`).

## Follow-up Items

* P-021 C2 capture: stash `635D7BAC` (extend P-017 policy text and `docs/pipeline-topology-gate.md`
  with the activation-preflight clause; kind task; provisional priority medium; requires deliberation: no).
* CHANGELOG `## Unreleased` entry for the 209-S behaviour change: left to the carryover release cut
  (shipments 210-S and 211-S are the remaining cut members; the plan's closure note lists
  P1/P3/P7/FB6F9FE0 for the release note).
* Existing entries referenced and not duplicated: `F2D11D61` (living pairing entry), `DB2E092B`.

## Merge and Fallback Status

* Merge: `--merge` (P-009), no `--squash` or `--rebase`, `--match-head-commit` pinned to the
  reviewed head. Parents `6227fc09` and `8faa1f86`.
* Admin fallback: not used (`admin_fallback_pre_authorized: false`). No `--force`.
* Tools: Copilot review was requested through the GraphQL `requestReviews` mutation with `botIds`
  (`gh pr edit --add-reviewer` and REST did not register it); see
  `docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md`.

## Compaction Status (P-020)

`done`. The mandatory compact-context run (target `all`, P-020) was invoked as a bounded,
threshold-gated scan after the session memory summary was written:

* Session record: `docs/memory/2026-10-12-ship-209-s-post-merge-closure.md`.
* Candidates compacted: none. The only memory that mentions this unit,
  `docs/memory/2026-10-08/stage-backlogit-carryover-first-cut-memory.md`, covers the whole carryover
  cut (Features B and C, shipments 210-S and 211-S, are not complete), so it does not qualify under
  the completed-work rule and was left in place. Active checkpoints preserved: 0 needed.
* Deferred: the legacy `docs/memory` backlog is above the 40-file and 500 KB thresholds (79 files,
  about 818 KB), already tracked by `3A3C72D0`; bulk compaction of unrelated older memory is outside
  this release unit's bounded closure.
* compact-context did not fail, so `degraded` does not apply.

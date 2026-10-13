---
shipment: 210-S
feature: 203-F
pr: 516
merge_commit: 1f8958c97f22026a15f3b14672406eb36be40627
reviewed_head: 1fcdbee7
date: 2026-10-13
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/210-S-203-F-close-evidence.json
---

# 210-S / 203-F Post-Merge Closure: Stash-Referenced Companion-Document Carry-Forward

## Summary

Shipment 210-S (covering feature 203-F; manifest `203-F`, `203.001-T` through `203.007-T`,
operator stash FB6F9FE0) merged through PR #516 as merge commit `1f8958c9` (`--merge`, merged
2026-10-13T14:15:14Z). The merge has two parents: `acff0052` (base) and `1fcdbee7` (reviewed PR
head). The change lets an uncommitted NEW file under `docs/` whose exact repo-relative path is a
whole token in an active entry of the working-copy `stash.jsonl` of the resolved backlog root be
`CARRY_FORWARD_ELIGIBLE` in the `pipeline-topology` `pre_claim` `worktree_cleanliness` check
(intake only: no triage, no scope change), with full path containment, fail-closed stash reads, new
`details.stash_referenced_paths` and `details.stash_reference_warning`, P-011 (registry 1.34.0) and
P-010 text, Ship carry-forward and task-boundary mid-cycle intake, Stage companion-document guidance,
docs, CHANGELOG, a contract test, and manifest checksum refreshes.

This closure ran in the post-merge closure branch
`post-merge/s-stash-referenced-companion-doc-carry-forward-203-f`. It archived the manifest through
the P-015 CASCADE path; the close is verified.

## Close Path and Evidence (P-015)

| Check | Result |
|---|---|
| Pre-Mode report | `.backlogit/reconcile/210-S-pre-20261013-141822.md`, `PROCEED` |
| Classifier | `CASCADE`; qualifying feature `203-F`; out-of-manifest descendants none |
| Engine semantics | `VERIFIED`, backlogit `1.11.0` on the CLI surface (commit `131577c`) |
| Selected close path | `cascade` |
| Agreement check (Pre-Mode report vs record) | agreed: verdict `CASCADE`, qualifying set `['203-F']` |
| Mutating `cascade-close` | exit `0`; `postcondition_verdict: pass`; `failures: []` |
| `returned_ids` | empty |
| `archived_ids` | `203-F`, `203.001-T` to `203.007-T`, `210-S` (9 of 9 required) |
| Shipment record | `shipment_status: shipped`, archived with `archived_status: shipped` |
| Baseline invariant and deliberation byte-identity | both true; `linked_deliberation_drift: []` |
| Post-Mode report | `.backlogit/reconcile/210-S-post-20261013-142808.md`, `PROCEED` |
| Evidence record | `docs/closure/evidence/210-S-203-F-close-evidence.json` (phases `pre_close` and `post_close`) |

Timeout sizing: `B = ceil(1.5 * (133 + 35 * 9))` = 672 s, so the 1800 s default `--timeout` applied.
The run was started attached and async with the 2400 s supervision budget and completed in about
12 minutes; it was not killed. Lock: acquired and released (token-matched) through the workspace-root
`scripts/acquire_lock.ps1` / `release_lock.ps1`; no substitution.

## Linked-Deliberation Disposition (P-015 INV-12)

The disposition snapshot is empty: `dispositions: []`, `unresolved_references: []`,
`read_failures: []`, `planning_error: null`. Outcome: `DISPOSITION_COMPLETE`. No deliberation was
archived by hand.

## Source Artifact Cleanup

| Item | `source_stash_id` outcome | `source_deliberation_id` outcome |
|---|---|---|
| 203-F | `none` (field not declared; provenance label `source-stash-FB6F9FE0`) | `none` |
| 210-S | `none` (same label) | `none` |

* `FB6F9FE0` was already archived by Stage's harvest (`.backlogit/archive/stash.jsonl`). No
  retirement action was needed.
* `F2D11D61` (the paired carryover requirements doc) was deliberately NOT retired: it is a living
  pairing entry and shipment 211-S (Feature C of the same carryover cut) is still open.

## Decisions

* **Dark-mode authority.** `DARK_MODE_ACTIVE` (P-017) scoped to exactly 210-S;
  `merge_approval_pre_authorized: true`; `admin_fallback_pre_authorized: false`. Emitted
  `DARK_MODE_MERGE_AUTHORIZED` (PR #516, head `1fcdbee7`, checks green, merge-commit strategy,
  approval source the activation record, scope match).
* **Destructive-close authority.** Intercom was unavailable (no intercom tool in this session), so
  the recorded authority for the mutating `cascade-close` is the operator's explicit task directive
  for this session (complete post-merge closure and archive the shipment items per the
  shipment-reconcile procedure), not a Ship self-clearance. `--classify-only` ran first (CASCADE,
  engine VERIFIED); the mutating run executed once, attached and async, with no retry and no
  substitution.
* **Mid-cycle intake scope.** Restricted to task boundaries with Ship-confirmed documents, because
  `pre_claim` classification is unavailable once a shipment is active.
* **Later-blocked `pre_claim`.** The backlog-only fallback halts on a stash-referenced document
  (fail closed, plan unit B6); exposing the cleanliness result on later-blocked results is a
  separate gate-output change (stash `A851D81B`).
* **Qualification semantics.** The shipped contract is the operator-specified FB6F9FE0 rule (any
  exact whole-token prose mention); narrowing is deferred for deliberation (stash `E148C09C`).

## Review History (PR #516)

Local multi-persona review (report-only, 9 personas: Constitution, Python, Correctness,
Maintainability, Learnings Researcher, Security, Template Integrity, Schema-CLI-Docs Coupling, Scope
Boundary Auditor) on `a6772078`. No P0/P1; in-scope P2/P3 fixed in `49ea96e1`; out-of-scope findings
captured as stash entries. Model routing: reviewer subagents ran on the harness default routing;
`TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`. Each later
fix delta was re-reviewed locally by the Ship agent (single-agent pass).

| Round | Review ID | Reviewed commit | Findings and disposition |
|---|---|---|---|
| 1 | 5499300196 | `a6772078` | 4 inline findings: FIFO stash read (fixed `b80ad14f`), later-blocked Ship fallback (x2, partially addressed: text and docs fixed, gate-output change deferred to `A851D81B`), CHANGELOG `stash_referenced_paths` claim (fixed). Replied and resolved |
| 2 | 5499440780 | `b80ad14f` | 1 inline finding: validate reader answer fields (fixed `2d4b8e50`). Replied and resolved |
| 3 | 5499554954 | `2d4b8e50` | 0 open; 1 threadless "Previously missed" body finding: reader warning discarded paths (fixed `c5823d09`); disposition comment with `Copilot-Review-Body-Disposition: 5499554954` posted |
| 4 | 5499678567 | `c5823d09` | 6 inline findings: full containment predicate missing in policy, Ship, and Stage text (fixed `1fcdbee7`). Replied and resolved |
| 5 | 5499790728 | `1fcdbee7` | "Approval recommended", 0 open findings, 6 resolved since last review |

All 11 review threads on PR #516 are resolved (11/11). Final P-018 gate on `1fcdbee7`: `SATISFIED`
(run before the merge, and again immediately before it).

## Gates and Evidence

| Gate | Command or source | Result |
|---|---|---|
| Merge confirmation | `gh pr view 516`; `git merge-base --is-ancestor 1f8958c9 origin/main` | `MERGED`, ancestor of `origin/main` (exit 0) |
| Two-parent proof | `git cat-file -p 1f8958c9` | parents `acff0052`, `1fcdbee7` |
| CI on PR head `1fcdbee7` | `gh pr view 516` | `detect code changes`, `pipeline-topology (ambient)`, `test`, `ci gate` all success |
| CI on merge commit | `gh run list --branch main` (run `38411769361`) | `success` |
| Local readiness (P-014) | PR body `## Local Review Readiness`, reviewed HEAD `1fcdbee7` | `READY_WITH_FOLLOWUPS`, `P0=0, P1=0` |
| Copilot gate (P-018) | `autoharness gate copilot-review 516 --repo softwaresalt/autoharness` | `SATISFIED`, exit 0 |
| Full local build | `PYTHONPATH=src python -m unittest discover -s tests` (and the pre-push hook on each push) | Ran 3556 tests, OK (skipped=57) before the first push; markdownlint on all markdown passed on every push |
| Topology gates | `pre_claim` (x2), `post_claim`, `lifecycle` (several) | all exit 0 |
| Crash-resumption scan | `backlogit checkpoint list` | 0 quarantined; 0 ship-owned `active`; normal startup |
| Single worktree (P-016) | `git worktree list` | one worktree: this checkout |
| Closure index resync | `backlogit sync --no-update-check` after all archival, evidence, and report writes (2026-10-13T14:30Z) | `CLOSURE_INDEX_SYNC_OK`: `Indexed 1858 artifacts`; re-run after the review-fix commit on this branch |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/210-S-203-F-post-merge-closure.md --shipment 210-S --json` | `passed: true`, exit 0, `failed_check: null`, `warnings: []` (run before each commit of this artifact, including the final content on this branch) |

## Runtime Verification

* Validator contract: `runtime_validation.validator_manifest` surface `cli`, probe `cli-help`
  (required). Verdict `PASS`: `uv run autoharness --help` exit `0`, CLI usage text printed.
* Manual runtime check of the changed gate (plan unit B1): `autoharness gate pipeline-topology
  --phase pre_claim --json` in a scratch repo with an untracked stash-referenced `docs/` file
  returned `CARRY_FORWARD_ELIGIBLE` with `details.stash_referenced_paths`; an unreferenced `docs/`
  file returned `WORKTREE_DIRTY`. The real claim of 210-S itself ran the new gate code path only after
  merge, so the next Ship claim is the live validation. No tag or publish step applies.

## Operational Closure

* `closure_status`: `READY` is the releasability verdict for PR #516's change and this
  docs-and-backlog-only closure. Closure completion is determined by the merge of the closure PR,
  whose live status is recorded in that PR.
* Invariants to preserve: stash-referenced documents are carried forward only as exact whole-token,
  new `docs/` files satisfying the full containment predicate; an unreadable, malformed, symlinked, or
  non-regular stash qualifies nothing; carry-forward stays intake only (no triage, no scope change);
  fail-closed divergent-staged and status-unavailable rules are unchanged.
* Healthy signal: `WORKTREE_DIRTY` halts citing a `docs/` path that an active stash entry names
  should stop occurring; a stash-referenced new `docs/` file appears in
  `details.stash_referenced_paths` and is committed in the carry-forward commit.
* Failure signal: a `docs/` file not named by an active stash entry, a modified tracked document, a
  link, or a path outside the workspace reported as `CARRY_FORWARD_ELIGIBLE`; or a gate crash on a
  malformed stash.
* Rollback trigger: either failure signal. Rollback: revert merge `1f8958c9` through a new reviewed PR
  (gate code, tests, docs, policy, agent templates, mirrors, and manifest checksums revert together;
  prefix-only carry-forward returns). Do not force or rewrite `main`.
* Validation window: the first two Ship claims after this closure merges.
* Owner: the repository operator (`softwaresalt`).

## Residual Risks

* Any exact whole-token prose mention of a new `docs/` path in any active stash entry (including
  long-lived tracker entries) admits that file; narrowing needs deliberation (stash `E148C09C`).
* A `pre_claim` result blocked by a later check (for example a bootstrap-grant shipment at
  `shipment_readiness`) omits cleanliness details, so the backlog-only fallback halts on a
  stash-referenced document (stash `A851D81B`).
* A local TOCTOU between the gate and `git add` is mitigated by Ship's reclassification and the
  byte-exact `git show` check, not eliminated.
* Archived features keep a stale `custom_fields.harness_status: pending` (203-F shows it); already
  tracked by `DB2E092B` per the 208-S closure.
* Tool degradation: backlog MCP, GitHub MCP, and intercom tools were not available; the backlogit CLI
  and `gh` were used (`TOOL_DEGRADED`).

## Follow-up Items

* P-021 C2 captures: `E148C09C` (narrow stash-reference qualification; feature; medium; requires
  deliberation: yes), `325FF702` (gate-output presentation and force-audit bounds; task; low),
  `44321776` (deduplicate carry-forward rule text; task; low), `E04BEC17` (public reparse-point helper
  and hermetic git env in tests; task; low), `86AE78EA` (Orchestrator Step 1.5 companion-document
  note; task; low), `A851D81B` (expose cleanliness on later-blocked `pre_claim`; task; medium).
* Remaining carryover cut member: shipment 211-S (Feature C, UTC mandatory for recorded dates and
  times). The R1 external-scheduler row stays out of this cut.
* Existing entries referenced and not duplicated: `F2D11D61` (living pairing entry), `1AD61D32`
  (decide whether to adopt the GraphQL `requestReviews` technique as a configured Copilot-request
  fallback; this session used it on the operator's explicit direction).

## Merge and Fallback Status

* Merge: `--merge` (P-009), no `--squash` or `--rebase`, `--match-head-commit` pinned to the reviewed
  head. Parents `acff0052` and `1fcdbee7`.
* Admin fallback: not used (`admin_fallback_pre_authorized: false`). No `--force`.
* Tools: Copilot review was requested through the GraphQL `requestReviews` mutation with `botIds`
  because the operator's dark-mode brief explicitly required a Copilot review. This is an observed
  technique, not a configured fallback (section 1.1); the policy decision is stash `1AD61D32`. See
  `docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md`.

## Compaction Status (P-020)

`done`. The mandatory compact-context run (target `all`, P-020) was invoked after the session memory
summary was written, and performed its bounded Tier-1 consolidation of the just-closed release unit's
fresh memory:

* Compacted: the session record `docs/memory/2026-10-13-ship-210-s-post-merge-closure.md` into
  `docs/memory/compacted/2026-10-13-210-s-203-f-compacted.md`. The verbose original was moved, not
  deleted, to `docs/archive/memory/2026-10-13-ship-210-s-post-merge-closure.md`.
* Not compacted: `docs/memory/2026-10-08/stage-backlogit-carryover-first-cut-memory.md` covers the
  whole carryover cut (Feature C, shipment 211-S, is not complete), so it does not qualify under the
  completed-work rule; the carryover plan is likewise left for the cut's final closure. Active
  checkpoints preserved: 0 needed.
* Deferred: the legacy `docs/memory` backlog is above the 40-file and 500 KB thresholds (195 files,
  about 1.4 MB counting archives under the tree), already tracked by `3A3C72D0`; bulk compaction of
  unrelated older memory is outside this release unit's bounded closure.
* compact-context did not fail, so `degraded` does not apply.

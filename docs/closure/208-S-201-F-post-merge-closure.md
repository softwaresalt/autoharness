---
shipment: 208-S
feature: 201-F
pr: 511
merge_commit: bc46110539a0434b8284ac32fa9df7b0f7540b62
reviewed_head: 3ef04bac
date: 2026-10-10
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/208-S-201-F-close-evidence.json
---

# 208-S / 201-F Post-Merge Closure: P-018 Copilot Review-Body Findings Gate

## Summary

Shipment 208-S (covering feature 201-F; manifest `201-F`, `201.001-T` through
`201.009-T`) merged through PR #511 as merge commit `bc461105` (`--merge`,
merged 2026-10-10T23:36:59Z). The merge has two parents: `26446a68` (base)
and `3ef04bac` (reviewed PR head). The change makes the P-018 Copilot
completion gate fail closed on Copilot review-body findings that have no
review thread. It adds the `UNDISPOSITIONED_BODY_FINDINGS` BLOCK verdict and
the trusted disposition-marker rule (`Copilot-Review-Body-Disposition:
<review databaseId>` comments from an association-trusted author).

This closure ran in the post-merge closure branch
`post-merge/201-f-p018-copilot-review-body-findings`. It archived the
manifest through the P-015 CASCADE path. The close is verified: the
postconditions passed and the shipment record is `shipped`.

## Close Path and Evidence (P-015)

| Check | Result |
|---|---|
| Pre-Mode report | `.backlogit/reconcile/208-S-pre-20261010-234607.md`, `PROCEED` |
| Classifier (`classify_shipment_close_path`) | `CASCADE`; qualifying feature `201-F`; out-of-manifest descendants none |
| Engine semantics | `VERIFIED`, backlogit `1.11.0` on the CLI surface (commit `131577c`) |
| Selected close path | `cascade` |
| Agreement check (Pre-Mode report vs record) | agreed: verdict `CASCADE`, qualifying set `['201-F']` |
| Mutating `cascade-close` | wrapper exit `0` (JSON `exit_code: 0`); child `backlogit shipment ship` `invocation.exit_code: 0`; `postcondition_verdict: pass`; `failures: []` |
| `returned_ids` | empty |
| `archived_ids` | `201-F`, `201.001-T` to `201.009-T`, `208-S` (11 of 11 required) |
| Shipment record | `shipment_status: shipped`, archived with `archived_status: shipped` |
| Baseline invariant and deliberation byte-identity | both true; `linked_deliberation_drift: []` |
| Post-Mode report | `.backlogit/reconcile/208-S-post-20261010-235639.md`, `PROCEED` |
| Evidence record | `docs/closure/evidence/208-S-201-F-close-evidence.json` (phases `pre_close` and `post_close`) |

The mutating run was launched attached and async, with the default
`--timeout 1800`. The reference budget B is `ceil(1.5 * (133 + 35 * 11))` =
777 s, which is within the default. The supervision budget was 2400 s. The
run completed within it and was not killed.

## Linked-Deliberation Disposition (P-015 INV-12)

The disposition snapshot is empty: `dispositions: []`,
`unresolved_references: []`, `read_failures: []`, `planning_error: null`.
Outcome: `DISPOSITION_COMPLETE`. The planner matcher recognizes `DL`-form
deliberation IDs and `source_deliberation_id`. The deliberation file
`docs/decisions/2026-10-08-copilot-review-body-findings-gate-deliberation.md`
is cited by path in 201-F and its members, but it is not a backlogit
deliberation record. No deliberation was archived by hand.

## Source Artifact Cleanup

| Item | `source_stash_id` outcome | `source_deliberation_id` outcome |
|---|---|---|
| 201-F | `none` (field not declared; provenance is the label `source-stash-38D29192`) | `none` |
| 208-S | `none` (field not declared; same label) | `none` |

Stash `38D29192` (the source of the shipped scope) was already archived before
this closure. The archive record is `reason: archived` with
`archived_at 2026-10-08T20:57:17Z`. That is after 201-F was created
(`2026-10-08T20:40:37Z`) and after 208-S was created (`2026-10-08T20:56:35Z`),
during the 2026-10-08 Stage harvest. No retirement action was taken, and none
was needed. Re-archiving it would have
been wrong. Stash `3FC709F9` (operator-accepted hardening follow-up) was not
edited, archived, or harvested. Stash `F373C349` was left for Stage.

## Decisions

* **(a) Association-only disposition-marker rule.** The operator decided, at
  2026-10-10T08:09:29Z, to accept the association-only disposition-marker rule
  for 208-S, keep `3FC709F9` as the hardening follow-up, and proceed to merge.
  The verbatim decision record is PR #511 comment 6095553824 (created
  2026-10-10T08:11:21Z, posted by Ship under DARK_MODE_ACTIVE).
  **Process deviation (disclosed, P-005 for operator review):** hold
  `3FC709F9` required that acceptance, or a Stage triage, come before the claim.
  An earlier Ship session claimed 208-S and implemented its tasks before that
  acceptance, under the operator's run-end-to-end directive. The halt
  checkpoint records this. No P-005 telemetry event was emitted from this
  session.
* **(b) Operator-directed config carry-forward.** `.autoharness/config.yaml`
  (blob `6c22c19e`) was carried forward once, as commit `7b34ba47`, with
  coupled mirror, manifest, and pin updates in `d89125d0`. This used the
  exception in
  `docs/compound/2026-10-10-operator-staged-config-carry-forward-and-route-pin-cascade.md`.
  The route is tier1 `claude-haiku-5.5`; tier2, tier3, orchestrator, and stage
  are `claude-sonnet-5.5`; ship is `claude-haiku-5.5` / `xhigh` /
  `long_context`, with nested `ship.escalation` `claude-sonnet-5.5` /
  `medium`; the flat `escalation` block was removed; anchor_review is
  `gpt-6.1-sol`. This was an operator-authorized one-time deviation. P-011 has
  no exception clause, and it is not presented as one. This closure branch
  touches no `.autoharness/` or config path (see the diff scope under Gates).
* **(c) Review-fix cycle bound.** The Orchestrator extended the PR #511 bound
  from 8 to cycle 9. The reason was an in-scope cp1252 decode defect in the
  new gate, which was fixed. The closure PR bound is 6, and no extension is
  needed for it.
* **(d) Stage same-route escalation.** Stage's escalation resolves to the same
  route as its own tier3 route, so it is an `ESCALATION_DEGRADED` no-op. This
  is tracked as follow-up `3C19FA0F`.
* **Lock tool deviation (disclosed).** The Pre-Mode lock was acquired with
  `.autoharness/staging/scripts/acquire_lock.ps1`, passing `-WorkspaceRoot`
  explicitly. The skill-relative path `.github/skills/file-lock/scripts/` does
  not exist. The workspace-root `scripts/acquire_lock.ps1` differs in SHA-256
  from the staged copy. The lock was released with its token. Follow-up
  `31A1FEAC` tracks the drift.
* **Destructive-close authority.** The operator's closure directive for this
  session, quoted in substance: run the post-merge closure for 208-S, and use
  `autoharness shipment cascade-close` only when the classifier and engine
  gates machine-verify CASCADE per P-015. Ship ran `--classify-only` first
  (CASCADE, engine VERIFIED), then the mutating run under that directive.
  Intercom was unavailable, so the recorded authority is the operator
  directive, not a Ship self-clearance.

## Review History (PR #511)

Copilot review IDs were verified against the GitHub reviews API.

| Round | Review ID | Reviewed commit | Reviewer | Findings and disposition |
|---|---|---|---|---|
| 4 | none (hold thread only; no review record) | none | Copilot | Hold thread, resolved after operator acceptance (decision a) |
| 5 | 5478359604 | `665b6ffa` | copilot-pull-request-reviewer | 3 body findings, fixed in `1b53b384` |
| 6 | 5478657799 | `a88f83bd` | copilot-pull-request-reviewer | 1 thread and 1 body finding, fixed in `8eaa53e6` |
| 7 | 5481051637 | `8eaa53e6` | copilot-pull-request-reviewer | 3 body findings, fixed in `31d85220` |
| 8 | 5481121878 | `31d85220` | copilot-pull-request-reviewer | clean |
| 9 | 5481197441 | `3ef04bac` | copilot-pull-request-reviewer | 1 thread (readiness refresh), resolved; clean |

All 13 review threads on PR #511 are resolved (`13/13`). The final P-018 gate
on `3ef04bac` returned `SATISFIED`.

## Gates and Evidence

| Gate | Command or source | Result |
|---|---|---|
| Merge confirmation | `gh pr view 511`; `git merge-base --is-ancestor bc461105 origin/main` | `MERGED`, ancestor of `origin/main` (exit 0) |
| CI on merge commit | `gh run list --branch main` (run `38095646788`) | `success` |
| CI on PR head `3ef04bac` | `gh pr view 511 --json statusCheckRollup` | `detect code changes`, `pipeline-topology (ambient)`, `test`, and `ci gate` all `SUCCESS` |
| Two-parent proof | `git rev-list --parents -n 1 bc461105` | `bc461105 26446a68 3ef04bac` |
| Single worktree (P-016) | `git worktree list` | one worktree: this checkout |
| Copilot threads on PR 511 | GraphQL `reviewThreads` | 13 total, 13 resolved |
| Lifecycle topology | `autoharness gate pipeline-topology --phase lifecycle` | pass; `BRANCH_POST_MERGE_CLOSURE_ELIGIBLE` |
| Crash-resumption scan | `backlogit checkpoint list` | 110 records; 0 quarantined; 0 ship-owned `active`; normal startup |
| P-018 acceptance, default locale | `autoharness gate copilot-review 511 --enforcement auto` | `SATISFIED`, exit 0, head `3ef04bac` |
| P-018 detection, real bodies | `gate copilot-review 506` and `509` | `UNDISPOSITIONED_BODY_FINDINGS` (BLOCK). PR 506 merged 2026-10-08T04:48:32Z and PR 509 merged 2026-10-09T20:46:02Z, both before the disposition-marker rule was live. PR 509 carries a body-only finding (stash `19FA25D8`). No action is taken on the merged PRs; the verdicts show the gate detects undispositioned body findings |
| Runtime probe `cli-help` | `uv run autoharness --help` | not runnable here: PyPI TLS handshake failed on 2 identical attempts (network). Equivalent: `autoharness --help` through the installed entrypoint (`autoharness home` = this workspace), exit 0 with help text |
| Closure-evidence gate | `autoharness gate closure-evidence --path docs/closure/208-S-201-F-post-merge-closure.md --shipment 208-S` | exit `0` on the final run (`passed: true`, `failed_check: null`, no warnings), with `compaction_status: done` |
| Full local build | source diff | not applicable: the closure diff (20 files) touches only `.backlogit/`, `docs/closure/`, `docs/memory/`, and `docs/archive/memory/`. No source, test, template, or config changed |
| Full canonical suite | CI `test` job on PR head | not applicable to this docs-and-backlog diff (no source change). The CI `test` job on PR head `3ef04bac` is `SUCCESS` (see the CI row above) |

## Runtime Verification

* Validator contract: `runtime_validation.validator_manifest` surface `cli`,
  probe `cli-help` (required, minimum verdict PASS). Releasability is not
  required.
* Verdict: `PASS_WITH_FOLLOW_UP`. The declared `uv run autoharness --help` form
  was NOT observed: two identical attempts failed on a PyPI TLS handshake
  (network). Substitute: the installed `autoharness --help` entrypoint, exit 0
  with CLI help text. `autoharness home` resolves to this workspace, and
  `autoharness version` reports `1.5.0`, matching `pyproject.toml`. Because the
  declared minimum verdict is PASS, the substitution is recorded as a launcher
  deviation. Re-running the `uv run` form is a follow-up. Releasability is not
  required, and this change has no release or publish obligation (no tag; the
  `CHANGELOG.md` `## Unreleased` entry from 201.005-T is the only release-facing
  note).
* Post-merge smoke on `main` runs after the closure merge. Its result is
  recorded in the closure PR and in the final report.

## Operational Closure

* `closure_status`: `READY` is the releasability verdict for this
  docs-and-backlog-only closure. The post-merge smoke on `main` is an
  observation after the closure merge, not a releasability condition.
* Invariants to preserve: P-018 fails closed on undispositioned Copilot
  review-body findings, and `--admin` does not bypass a P-018 BLOCK. The
  disposition marker is trusted only from an association-trusted author
  (decision a).
* Healthy signal: Copilot review on the next engaged PRs returns `SATISFIED`
  or `NOT_APPLICABLE` only with every body finding dispositioned.
* Failure signal: a `SATISFIED` verdict on a PR with an undispositioned body
  finding, or a BLOCK on a clean PR.
* Rollback trigger: either failure signal above. Rollback procedure: revert
  the gate commits (merge `bc461105`) through a new reviewed PR. Do not force
  or rewrite `main`.
* Validation window: the first three PRs merged after this closure that engage
  Copilot review.
* Owner: the repository operator (`softwaresalt`).

## Residual Risks

* The association-only trust rule (decision a). Effective-permission hardening
  is tracked as `3FC709F9`, which is the operator-accepted hardening follow-up.
* Stage same-route escalation resolves to a no-op. Tracked as `3C19FA0F`.
* The P-018 fail-closed claim holds for the body-findings path, subject to these
  open risks. `F15933A0` (high) covers the pre-existing copilot-review surface,
  where `--enforcement disabled` and a caller-chosen `--gh` binary can return
  `NOT_APPLICABLE` or a substituted GraphQL result with no force-audit record.
  `ED0AE060` (high) covers the `--force` override authority, which needs explicit
  operator authorization. `BE43E5F1` (high) covers enforcement: the gate runs
  only when invoked, CI does not run it, and `main` has no branch protection, so
  the merge gate is a convention rather than an enforced control.
* Mirror and route staleness are tracked as `1F13DF5E`.
* Archived features keep a stale `custom_fields.harness_status: pending`. This
  is already tracked as `DB2E092B`. 201-F shows it.
* The source-stash retirement step keys on `custom_fields.source_stash_id`,
  which features do not declare. Already tracked as `C9E87CE9` and `FD85BC61`.
* The `--force` override print can raise `UnicodeEncodeError` on a cp1252
  console after the audit line is written. Captured as `5A51B5F9`.
* The file-lock staged and installed script copies differ. Captured as
  `31A1FEAC`.
* `backlogit stash get` does not resolve archived entries. Captured as
  `674BA1FE`.
* The `uv run` launcher probe is blocked by the network. Follow-up: re-run
  when the network is available.

## Follow-up Items

* P-021 C2 capture: `5A51B5F9` (cp1252 `--force` print; kind bug; provisional
  priority low). Ship recorded its requires-deliberation flag as `no`. That is
  a capture-time judgement, and Ship cannot edit a captured entry. Stage's C6
  triage decides whether deliberation is needed.
* Non-P-021 follow-ups (Step 6, stash only): `31A1FEAC` (file-lock script
  drift; kind bug; low) and `674BA1FE` (`stash get` does not resolve archived
  entries; kind bug; low).
* Existing entries referenced and not duplicated: `3FC709F9`, `F373C349`
  (left for Stage), `3C19FA0F`, `1F13DF5E`, `DB2E092B`, `C9E87CE9`,
  `FD85BC61`, `F15933A0`, `ED0AE060`.

## Merge and Fallback Status

* Merge: `--merge` (P-009). No `--squash` or `--rebase`. Parents
  `26446a68` and `3ef04bac`.
* Admin fallback: not used (`admin_fallback_pre_authorized: false`). No
  `--force`.
* Authority: the DARK_MODE_ACTIVE activation record (P-017) for the 208-S
  closure PR, as stated in the operator's closure brief for this session:
  scope 208-S only; `merge_approval_pre_authorized: true` for the closure PR;
  `admin_fallback_pre_authorized: false`. Closure PR readiness (head, §1.9
  outcome, Copilot gate result, approval source) is recorded in the closure PR
  body and the final report.
* Tools: `TOOL_DEGRADED`. Backlog MCP and GitHub MCP were unavailable, so the
  backlogit CLI (`INDEX_SYNC_OK (CLI fallback)`) and `gh` were used. Intercom was
  unavailable, so events were emitted as labelled session output and are
  recorded here and in the closure PR body.

## Compaction Status (P-020)

`done`. The mandatory compact-context run (target `all`, P-020) completed as
a bounded, threshold-gated consolidation of the just-closed release unit's
memory:

* Compacted: `docs/memory/2026-10-08/stage-38d29192-copilot-review-body-findings-harvest.md`
  and `docs/memory/2026-10-10-ship-208-s-halt.md` into
  `docs/memory/compacted/2026-10-10-208-s-201-f-compacted.md`. The originals
  were moved, not deleted, to `docs/archive/memory/` with the same relative
  paths.
* Session record: `docs/memory/2026-10-10-ship-208-s-post-merge-closure.md`.
* Deferred candidates, not compacted in this run: the 201-F plan
  (`docs/plans/2026-10-08-copilot-review-body-findings-gate-plan.md`) is a
  decided-plan candidate, but the 201.00x-T tasks and this closure cite the
  plan path, so consolidating it is deferred (the decided-plan path defect is
  tracked by `9749EC1C`). Older closure records are threshold-gated and were
  not selected. The legacy `docs/memory` backlog remains above the 40-file and
  500 KB thresholds, tracked by `3A3C72D0`.
* compact-context did not fail, so `degraded` does not apply.

---
shipment: 127-S
feature: 118-F
tasks: [118.001-T, 118.002-T, 118.003-T, 118.004-T, 118.005-T, 118.006-T, 118.007-T]
feature_pr: 326
closure_pr: 327
merge_commit: 8ccd3a2ded777393703136da6747e846619f4294
merged_at: "2026-08-13T02:14:36Z"
reviewed_head: 3c0c2836
closure_status: READY
compaction_status: done
feature_terminal_status: done
feature_archived_status: done
shipment_close_path: cascade
---

# 127-S / 118-F Post-Merge Closure — S1 Copilot Supervisor Safety Contracts + Characterization Baseline

Shipment `127-S` implemented Shipment 1 of the strict serial chain
`127-S -> 128-S -> 129-S` for Plan 1 (Local Copilot CLI supervisor /
control-plane runtime), superseding retired `124-S`/`125-S`/`126-S`.
Covering feature `118-F` is a root feature (no parent) with exactly 7
children, all of which are this shipment's manifest — the "fully-covered
root" topology this shipment's own `118.007-T` implements the classifier
for. Scope: safety contracts + characterization baseline (P0), with an
explicit zero-observable-behavior-change boundary (no runtime wiring).

## Merge Confirmation

- PR **#326** ("feat: shipment 127-S safety contracts and characterization
  baseline") merged to `main` at `2026-08-13T02:14:36Z` with merge commit
  `8ccd3a2ded777393703136da6747e846619f4294`. Confirmed via
  `git show -s --format="%P"` on the merge commit: two parents
  (`c6766c8c24a155ff220f0d8ee4f0c16a6a8aff0a` prior `main` tip +
  `3c0c2836...` feature branch HEAD), preserving the P-009 merge-commit
  strategy structurally. Confirmed ancestor of `origin/main` (`git fetch
  origin main` then `git merge-base --is-ancestor 8ccd3a2d... origin/main`
  -> exit 0).
- Repo merge-strategy settings (P-009), verified before merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" is possible.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Local review (report-only) | 2 findings, both fixed with regression tests. Outcome `READY`. 0 of 3 review-fix cycles used. |
| Full local build / test evidence | `python -m unittest discover -s tests`: 1588 passed. `pytest`: 1575 passed, 13 skipped, 582 subtests. Re-verified after every remediation commit through final HEAD `3c0c2836`. `uv run autoharness --help` smoke test PASS. |
| CI (PR #326) | `detect code changes`, `test`, `ci gate` SUCCESS at final polled HEAD. `pipeline-topology (ambient)` raw-failed with the expected/authorized `PREDECESSOR_NOT_SHIPPED` token (advisory-only job, does not block `ci gate`). |
| Fix-CI cycles | 3 of 5 available — pytest->unittest conversion (project convention: CI's `test` job runs bare `python -m unittest discover`, no pytest installed), a real Windows `_windows_pid_exists` liveness bug fix in `locking.py`, a Windows-only test-suite platform-gating fix. |
| Copilot review (PR #326) | **4 remediation rounds, 21 threads total** (GitHub recorded these across 6 discrete review submissions: 16 initial threads across the first 3 submissions, bundled into my remediation round 1, + 5 follow-on threads across 3 further submissions). 13 fixed + 2 deferred (P2) + 2 informational-only in round 1, 3 fixed in round 2, 1 fixed in round 3 (3 of 3 review-fix cycles used), 1 further finding explicitly deferred in round 4 (P2, circuit breaker exhausted). See detail below. |
| P-018 copilot-review gate | `SATISFIED` at final HEAD `3c0c2836` (zero unresolved threads), re-confirmed unconditionally immediately before merge (headRefOid unchanged). |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `3c0c2836`: PR body Local Review Readiness block refreshed to this HEAD, outcome `READY_WITH_FOLLOWUPS`, P0=0/P1=0, full local build evidence recorded, 2 explicit P2 follow-ups with rationale, Copilot/P-018 result explicitly recorded `SATISFIED`. |
| Dark-mode merge authorization | `DARK_MODE_MERGE_AUTHORIZED` for PR #326: scope matched `127-S` only, `merge_approval_pre_authorized: true`, §1.9 and P-018 both passed at HEAD (re-verified immediately before merge), checks green, P-009/P-016 verified. Admin fallback was pre-authorized but never invoked — the normal merge (`gh pr merge 326 --merge`) succeeded directly. |
| Worktree/PR topology (P-016) | Single worktree throughout; no parallel worktree created or used. `pipeline-topology` lifecycle gate PASS (forced, sole authorized token) immediately before build, before PR creation, and before closure/safe-close. |

### Copilot review detail (4 remediation rounds, 21 threads, 17 fixed / 2 deferred as P2 / 2 informational-only)

Deep, genuine safety-critical bugs across three new modules — race
conditions in `locking.py`'s acquire/release/force_unlock ordering,
multiple fail-closed gaps in `redact.py`'s secret-redaction choke point
(unsupported types, non-string keys, exception-message/exception-class-name
leak vectors), and multiple fail-closed gaps in `shipment_closure.py`'s
destructive P-015 classifier (glob-injection, missing frontmatter-id
verification, malformed `parent_id` ambiguity, filename-stem trust
fallback, symlink-following — the last deferred). Full detail and the
generalizable lesson recorded in
`docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`.

Round 1 (13 fixed, 2 deferred as P2, 2 informational-only) spans the
first 3 raw GitHub review submissions (11 + 2 + 3 = 16 threads, submitted
at `00:23:56Z`/`00:58:00Z`/`01:18:21Z` against commits `a52278eb`/
`e01e7f23`/`9280d404`), triaged and remediated together in one commit.
Round 2 (3 fixed) and Round 3 (1 fixed) each correspond to one further
GitHub review submission (3 threads, then 1 thread). Round 4 (1 finding,
deferred) corresponds to the final GitHub review submission (1 thread).
11+2+3+3+1+1 = 21 threads across 6 submissions, confirmed via
`gh api graphql` against PR #326's `reviews`/`reviewThreads` (`totalCount:
27` reviews including reply-comments, `totalCount: 21` review threads).

Fix commits: `20853d6c` (round 1, 13 findings), `1875c879` (round 2, 3
findings — plus a self-caught latent bug from the round-1 fix),
`3c0c2836` (round 3, 1 finding). All fixes verified via both
`python -m unittest discover` and `pytest`, re-ran the forced lifecycle
topology gate, pushed, replied to and GraphQL-resolved every thread.

**Round-1 deferred/informational findings (from the 16-thread bundle)**:
1. P2 — symlink-containment tradeoff in `locking.py:106` (deferred).
2. Informational — the `shipment-reconcile` skill was not wired to the
   new close-path classifier (out of scope for this zero-runtime-wiring
   slice at the time; **remediated on the post-merge closure PR** after a
   follow-on Copilot review on the closure PR itself correctly pointed out
   that `118.007-T`'s own acceptance criteria required this surface — see
   the Backlog Reconciliation section below).
3. Informational — a test-coverage-enhancement suggestion (not a defect).

**Round-4 deferred finding (P2)**: symlink-following in
`shipment_closure.py`'s backlog lookup path — same risk class as the
round-1 `locking.py:106` finding. Deferred per the exhausted 3-cycle
circuit breaker, listed explicitly in the PR body and here as an
operator-visible follow-up.

**Total this shipment (PR #326): 21 Copilot review comments across 4
remediation rounds (6 raw GitHub review submissions). 17 fixed ->
committed -> pushed -> replied -> GraphQL-resolved. 2 deferred as P2
(circuit breaker exhausted for the second). 2 informational-only comments
— one of which (the skill-wiring gap) was subsequently remediated on this
very closure PR after a follow-on Copilot review confirmed it was a
genuine gap, not merely informational.**

## Runtime Verification

**Surface**: pure additions (new Python modules, none yet wired into any
executable runtime path) plus characterization tests pinning
`start.ps1`/`start.sh`'s *existing* behavior unchanged. Explicit
zero-observable-behavior-change scope; no new runtime surface introduced.

| Field | Evidence |
| --- | --- |
| Validator | Ship pre-merge/post-merge runtime verification, per `runtime_validation.validator_manifest` in `.autoharness/workspace-profile.yaml`. |
| Surface adapter | CLI-help probe (`cli` surface, `command` adapter). |
| Runtime probe | `uv run autoharness --help` — exit 0. Run pre-merge at feature-branch HEAD `3c0c2836` and again post-merge after pulling fresh `main` at `8ccd3a2d`. |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures" — HELD at both HEADs. |
| Blocked prerequisites | None for the CLI surface. No browser/API/background-job surface applies — the new supervisor modules are not yet wired into any invocable path (explicit scope boundary), so there is no additional runtime surface to exercise beyond the unit/characterization test suites already run as build evidence. |
| Verdict | **PASS** — the only in-scope runtime surface (the packaged CLI entrypoint) was exercised pre-merge and post-merge with no regression. No fabricated automation was used for the deliberately-unwired supervisor modules. |

## Backlog Reconciliation — P-015 Verified Fully-Covered-Root Cascade Close

Unlike prior shipments in this repository's closure history (which used
single-artifact safe-close), `127-S` is the first shipment closed via the
**cascade** path, selected by the verified fully-covered-root exception this
shipment's own `118.007-T` implemented.

- **Classifier run**: `classify_shipment_close_path(['118-F', '118.001-T',
  '118.002-T', '118.003-T', '118.004-T', '118.005-T', '118.006-T',
  '118.007-T'], '.backlogit')` returned `ClosePath.CASCADE` with reason
  "every feature member is a verified fully-covered root; cascade close is
  permitted", `qualifying_feature_ids: ('118-F',)`.
- **Dynamic engine attestation** (pre-close, per the P1-1 ruling
  superseding the former exact-commit pin): installed CLI identified as
  `v1.9.0`, commit `39528a4`, build `2026-08-12T03:49:03Z`. A stale
  long-lived MCP daemon process (PID 45252) was found still serving the
  pre-upgrade `v1.8.0-dirty`/`fd8d2c9d` binary (Windows-renamed image
  `backlogit.exe.old`) and was stopped PID-specifically
  (`Stop-Process -Id 45252 -Force`, never by name). This session performed
  all backlog mutations via the CLI directly (no MCP tool function is
  exposed in this agent's toolset), so CLI/MCP staleness never affected an
  actual mutation; the MCP restart was operator-mandated hygiene.
- **Closure simulation re-run** against the attested engine:
  `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1`
  — **66/66 assertions passed**.
- **Lifecycle topology gate**: re-run immediately before the close
  mutation. Unforced run returned the sole expected/authorized token
  `PREDECESSOR_NOT_SHIPPED` (archived, superseded `126-S`); forced re-run
  (narrow, pre-authorized `--force` override) returned exit 0, audit logged
  to `.autoharness/gates/pipeline-topology-force-audit.log`.
- **Cascade execution**: `backlogit shipment ship 127-S --sha
  8ccd3a2ded777393703136da6747e846619f4294 --message "..." --author
  "dewilliams"`. Result: `shipment_status: shipped`, `returned_ids: []`,
  `archived_ids: [118.001-T, 118.002-T, 118.003-T, 118.004-T, 118.005-T,
  118.006-T, 118.007-T, 118-F, 127-S]` — matching the shipment's own
  Stage-authored predicted outcome exactly.
- **Post-close verification**: every task's `parent_id: 118-F` preserved
  unchanged in the archived record. `118-F` archived with
  `archived_status: done`. `127-S` archived with `archived_status:
  shipped`. `git status --short` after the mutation showed exactly the 9
  manifest artifacts' queue/archive/log files touched — no out-of-scope
  shipment, feature, or task mutated; no `parent_id` cleared anywhere.

### Close-path decision correction (recorded for future close-path decisions)

An earlier planning pass (across a context-compaction boundary) had
provisionally concluded "safe-close" based on a partial reading of the
Ship agent's P-015 section that captured the unconditional-prohibition
sentence but missed the immediately-following conditional exception clause.
Re-reading the full current section before acting surfaced the exception;
running the classifier confirmed `CASCADE`, matching both the manifest's
own description and the operator's brief. See
`docs/compound/2026-08-12-close-path-decisions-must-use-the-classifier-not-summarized-prose.md`.

## Post-Merge Closure PR (#327) Review

The closure PR itself (#327, this branch) was subject to the full P-014
local review + hosted Copilot review protocol, not merely rubber-stamped:

- **Local review**: `.backlogit/` diff scoped to exactly the 9 manifest
  archival artifacts (confirmed via `git status --short`); YAML frontmatter
  of all 6 new/modified docs validated; cross-references (compound docs,
  memory files, source modules) confirmed to exist. Outcome `READY`, 0
  P0/P1. Full local build recorded as **not applicable** — no `src/` or
  `tests/` file is touched by this diff.
- **Hosted Copilot review** (1 round, 6 threads, all genuine — 0 false
  positives):
  1. **`118.007-T` marked `done` without its own acceptance criteria fully
     satisfied**: `118.007-T`'s task text required amending 4 surfaces
     coherently (P-015 policy template, Ship agent template, the
     `shipment-reconcile` skill, and the compound close-path doc), but the
     `shipment-reconcile` skill template was never actually wired to the
     new classifier — confirmed by grep (zero hits for
     `classify_shipment_close_path`/`fully-covered` in
     `templates/skills/shipment-reconcile/SKILL.md.tmpl` before this fix).
     **Fixed**: added a new Step 0 (close-path selection) and a Cascade
     Close Sub-Procedure to the skill template, matching the same
     preconditions already present in the generic
     `templates/agents/_ship.agent.md.tmpl`, so the skill now implements
     the precondition check and selects the close path from its result
     rather than from prose — completing `118.007-T`'s originally-scoped
     4th surface after the fact.
  2. **Review-thread-count arithmetic error (3 threads, same root cause)**:
     this closure artifact, the compacted memory, and the archived session
     memory all stated PR #326 had "20 threads (16 initial + 4 follow-on)",
     but `gh api graphql` against PR #326 confirms `totalCount: 21`
     threads across 6 discrete review submissions (11+2+3+3+1+1). **Fixed**:
     corrected the arithmetic in all 3 affected documents (this file, the
     compacted summary, and the archived session memory) to the verified
     16 initial + 5 follow-on = 21 total, with an explicit note that "4
     remediation rounds" (my own fix-cycle grouping) spans 6 raw GitHub
     review submissions (the first 3 were bundled into round 1).
  3. **Windows `.exe.old` compound doc overgeneralization**: the doc
     originally asserted Windows automatically renames a running process's
     image to `*.exe.old` on any in-place binary replacement — this is
     actually updater/installer-specific behavior (chosen by the tool doing
     the replacement), not a Windows platform guarantee, and whether an
     in-use image can be renamed at all depends on file-sharing-mode
     semantics. **Fixed**: reworded the compound doc to describe this as an
     observed updater convention to corroborate with process start time and
     binary identity, not a universal Windows behavior.
- **Fix commit**: `7f8852a5` on `post-merge/118-copilot-supervisor-safety-contracts`.
  All 6 threads replied to and GraphQL-resolved.
- **P-018 copilot-review gate**: re-run after the fix push; `SATISFIED`
  required before this PR could be presented as merge-ready.

This closure PR's own review is itself a second concrete data point for
the lesson in
`docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`:
hosted review caught a real, substantive task-completeness gap
(`118.007-T`) even in a "documentation-only" closure PR that local review
and CI both passed cleanly.

## Context Compaction (P-020)

- **Status: done** — mandatory per-merge `compact-context` (`target: all`)
  invocation performed this session. Candidate identified: this release
  unit's own just-written session memory (completed-work rule). Bounded
  Tier-1 consolidation performed: 1 memory file compacted, 0 active
  checkpoints touched, 0 plans consolidated (none pending for this release
  unit), 0 additional closure records compacted (none exceeded
  `threshold_days`).
- Session memory: written to
  `docs/memory/2026-08-12-ship-127-S-118-F-session.md`, then moved verbatim
  to `docs/archive/memory/2026-08-12-ship-127-S-118-F-session.md` as part of
  this compaction pass.
- Compacted memory:
  `docs/memory/compacted/2026-08-12-127S-118F-compacted.md` (decisions,
  files modified, key learnings/cross-references to the 3 new compound
  docs, outcomes) — written during this compaction pass.

## Operational Closure

- **Healthy signals**:
  - Feature PR #326 merged with a merge commit (two parents; P-009
    preserved).
  - Local review `READY` (P0=0/P1=0); 4 remediation rounds of Copilot
    review (21 threads across 6 raw GitHub review submissions), 17
    fixed/replied/resolved, 2 deferred as explicit P2 follow-ups, 2
    informational-only (one subsequently remediated on the closure PR
    itself), re-confirmed `SATISFIED` via P-018 immediately before merge.
  - CI green at every required check on every polled HEAD.
  - Cascade close (verified fully-covered-root exception) reconciled all 7
    tasks + `118-F` + `127-S` with `returned_ids: []` and zero out-of-scope
    mutation — the first real-world exercise of the new close-path
    classifier against a live, non-simulated manifest, matching its own
    66/66-simulation-predicted behavior exactly.
  - Dark-factory bounded scope `127-S` fully executed; `128-S`/`129-S` were
    explicitly NOT claimed, planned, or expanded into.
  - Closure PR #327's own Copilot review caught 2 genuine documentation
    accuracy findings (review-count arithmetic) and 1 genuine remediation
    gap (`shipment-reconcile` skill wiring) — all fixed on the closure
    branch itself; see the Post-Merge Closure PR Review section below.
- **Failure signals to watch**: none specific to this shipment's own
  closure. The Copilot review-fix circuit breaker (3 cycles) was fully
  exhausted on PR #326 — a genuine signal that this PR required unusually
  deep remediation, though every fix was verified and every deferred item
  is a documented, non-blocking P2.
- **Follow-ups** (non-blocking; `closure_status: READY`):
  1. P2: symlink-following in `shipment_closure.py`'s backlog lookup path
     (Copilot round-4 finding, deferred per exhausted circuit breaker).
  2. P2 (pre-existing, re-confirmed not newly introduced this session):
     symlink-containment tradeoff in `locking.py:106`.
  3. Informational: the `shipment-reconcile` skill template is not yet
     wired to call `classify_shipment_close_path` automatically; Ship must
     invoke it manually per the agent instructions' item "e" until a
     future shipment wires it in. Explicitly out of scope for this
     zero-runtime-wiring slice (this is the same gap `118.007-T`'s own
     task text names as deliberately out of scope).
  4. Informational: a Copilot test-coverage-enhancement suggestion, not a
     defect.
  5. `128-S` is now unblocked (its sole predecessor `127-S` reached
     `shipped`), but was explicitly NOT claimed by this session per the
     operator's scope boundary — the Orchestrator will reload current
     `main` and advance the cursor.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): the shipped capability is pure additive
  Python modules (result/error/contract types, redaction, locking, a
  close-path classifier) plus characterization tests — no runtime wiring,
  no new distribution/packaging change, no scheduler/auto-claim capability
  introduced. Rollback = revert merge commit `8ccd3a2d` (additive modules +
  tests + docs only). **Verdict: READY.**

## Closure Tasks (this branch)

1. Compound-learning docs:
   `docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`,
   `docs/compound/2026-08-12-windows-stale-process-exe-old-detection.md`,
   `docs/compound/2026-08-12-close-path-decisions-must-use-the-classifier-not-summarized-prose.md`
   — **done** (this branch).
2. This canonical closure artifact (this file) — **done**.
3. Session memory write + compaction to
   `docs/memory/compacted/2026-08-12-127S-118F-compacted.md` (verbose
   original archived to
   `docs/archive/memory/2026-08-12-ship-127-S-118-F-session.md`) — **done**
   (this branch).
4. Mandatory P-020 `compact-context` (`target: all`) invocation — **done**
   (this branch): 1 memory file compacted (this release unit's own session
   memory, completed-work rule), 0 active checkpoints touched, 0 plans
   consolidated, 0 additional closure records compacted.
5. Closure index resync (`backlogit sync`) — **done**, both immediately
   after the cascade close mutation and again after this branch's closure
   commits.

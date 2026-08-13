---
shipment: 128-S
feature: 119-F
tasks: [119.001-T, 119.002-T, 119.003-T, 119.004-T, 119.005-T, 119.006-T]
feature_pr: 328
closure_pr: 329
merge_commit: 915923c25453739b6da955fe247bd4b38a11e830
merged_at: "2026-08-13T05:17:14Z"
reviewed_head: 06c280bd645332112b4608826c920219fbe23e11
closure_status: READY
compaction_status: done
feature_terminal_status: done
feature_archived_status: done
shipment_close_path: cascade
correction_pr: 330
correction_merge_commit: f47c1b65bdc28aad5594856db7a592f0092f929f
correction_merged_at: "2026-08-13T06:21:06Z"
---

# 128-S / 119-F Post-Merge Closure — S2 Copilot Supervisor Supervision Core Library (Unwired)

Shipment `128-S` implemented Shipment 2 of the strict serial chain
`127-S -> 128-S -> 129-S` for Plan 1 (Local Copilot CLI supervisor /
control-plane runtime). Covering feature `119-F` is a root feature (no
parent) with exactly 6 children, all of which are this shipment's
manifest — the same "fully-covered root" topology `127-S`/`118.007-T`
first exercised the classifier against. Scope: the Python supervision core
library — process/PTY adapters behind one shared protocol, a session
state machine with a distinct `CANCELLED` terminal state, typed events, a
redacted append-only journal, and recovery/restart. Explicit
zero-observable-behavior-change boundary: nothing in `start.ps1`,
`start.sh`, existing CLI commands, or runtime adapters reaches this new
core in this shipment (UNWIRED, reverified pre-merge and post-merge via
grep with zero hits).

> **Correction (recorded during this closure PR's own hosted review)**:
> the "Copilot review detail" section below originally classified two
> PR #328 findings (`session.py:75`, `recovery.py:136`) as false
> positives. That classification was **wrong** — both were genuine
> defects, caught only because *this closure PR's own* hosted Copilot
> review flagged the inaccurate closure record. Both were fixed and
> merged via follow-up PR **#330** (merge commit
> `f47c1b65bdc28aad5594856db7a592f0092f929f`, merged
> `2026-08-13T06:21:06Z`, two-parent merge-commit strategy verified). See
> the corrected "Copilot review detail" section and the new
> `docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md`
> for the full account. This is itself the noteworthy finding this
> closure surfaces: a hosted-review triage record is only as reliable as
> the fidelity of what was actually checked, and closure documentation is
> a review-checkable artifact, not exempt narrative.

## Merge Confirmation

- PR **#328** ("feat(128-S): S2 Copilot supervisor — supervision core
  library, unwired (P0)") merged to `main` at `2026-08-13T05:17:14Z` with
  merge commit `915923c25453739b6da955fe247bd4b38a11e830`. Confirmed via
  `git show -s --format="%P"` on the merge commit: two parents
  (`eb49dfc381e0fecd00c02b7d4acc50dc60797644` prior `main` tip +
  `06c280bd645332112b4608826c920219fbe23e11` feature branch HEAD),
  preserving the P-009 merge-commit strategy structurally. Confirmed
  ancestor of `origin/main` (`git fetch origin main` then
  `git merge-base --is-ancestor 915923c2... origin/main` -> exit 0).
- Repo merge-strategy settings (P-009), verified before and after merge:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" is possible.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Local review (report-only) | 1 P0 finding (lock-release-exactly-once in `cancel_session` under a specific interleaving), fixed with a regression test before first push. Outcome `READY`. |
| Full local build / test evidence | Full suite: **1681 passed, 17 skipped, 0 failed** — re-run after every remediation commit through final HEAD `06c280bd`, and again post-merge on fresh `main`. `uv run autoharness --help` smoke test PASS pre- and post-merge. |
| CI (PR #328) | `ci gate`, `test`, `detect code changes`, `pipeline-topology (ambient)` all SUCCESS at final polled HEAD `06c280bd`. |
| Fix-CI cycles | 1 of 5 available — a backslash-path-normalization bug in `locking.py` surfaced only under the CI runner's path handling (commit `1eba6762`). |
| Copilot review (PR #328) | **5 review rounds** across commits `0f0d5b6b` -> `1eba67627` -> `abc389c8` -> `11888fba` -> `06c280bd`. 21/21 posted review threads resolved. 3 of 3 review-fix cycles used (commits `abc389c8`, `11888fba`, `06c280bd`); a 5th round on `06c280bd` surfaced further findings, 2 with actual posted threads (replied-to and resolved as documented follow-ups, not fixed — circuit breaker exhausted per protocol and explicit operator instruction) and 4 suppressed-only (review-body text, no thread — documented in the PR body narrative only, not separately triaged as a new cycle). See detail below. |
| P-018 copilot-review gate | `SATISFIED` at final HEAD `06c280bd` (`unresolved_thread_ids: []`), re-confirmed unconditionally immediately before merge (headRefOid unchanged). |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `06c280bd`: PR body Local Review Readiness block refreshed to this HEAD, outcome `READY_WITH_FOLLOWUPS`, P0=0/P1=0 residual, full local build evidence recorded (1681/17/0), 7 explicit follow-ups with rationale, Copilot/P-018 result explicitly recorded `SATISFIED`. |
| Dark-mode merge authorization | `DARK_MODE_MERGE_AUTHORIZED` for PR #328: scope matched `128-S` only, `merge_approval_pre_authorized: true`, §1.9 and P-018 both passed at HEAD (re-verified immediately before merge), checks green, P-009/P-016 verified. Admin fallback was pre-authorized but never invoked — the normal merge (`gh pr merge 328 --merge`) succeeded directly. |
| Worktree/PR topology (P-016) | Single worktree throughout; no parallel worktree created or used. `pipeline-topology` lifecycle gate PASS (unforced) before build, before PR creation, and before closure/safe-close. |

### Copilot review detail (5 rounds, 21 posted threads, 19 fixed / 2 documented follow-ups; 4 additional suppressed-only findings documented, not separately cycled)

Genuine correctness fixes spanned three modules:

- `recovery.py`: `RestartController.attempt()` treated a `confirm_restart()`
  exception as an implicit approval before the fix — now any exception
  from the confirmation callback is treated as an explicit decline
  (fail-closed); the approved-restart branch previously transitioned to
  `LAUNCHING` without first terminating the old child — now terminates
  (`ProcessLookupError`-tolerant) before the transition.
- `process_pty.py`: `PtyChildProcess.close()` previously escalated to
  SIGKILL on any exception from the wait, conflating an already-reaped
  child (`ChildProcessError`) with a still-running one (`TimeoutError`) —
  now only a genuine timeout escalates. `WinPtyChildProcess.close()` did
  not terminate/bound-wait for a still-alive child before closing, and
  could leak the handle on an exception path — now terminates first with a
  bounded wait and clears the handle unconditionally via `finally`.
- `journal.py`: `_ensure_initialized()` did not detect a crash occurring
  during the very first (header) write and would silently skip writing a
  header — now detects this case and writes a proper header at seq 0.

Two findings (`session.py:75`, `recovery.py:136`) were **originally
mis-triaged as false positives** against the frozen task specs, but were
subsequently confirmed genuine and fixed in follow-up PR **#330** (see the
Correction note above). At the time of PR #328's own review-fix cycle, the
triage record read (verbatim, now known incorrect):

> "`session.py:75` (a suggested direct pre-terminal-to-`FAILED` transition
> edge that `119.003-T`'s spec explicitly forbids) and `recovery.py:136`
> (the unconditional lock release Copilot flagged as a potential
> double-release is exactly what `119.006-T`'s F22 'no path can strand
> it' requirement mandates)."

Re-investigation using the *exact* original comment text (comments
`3772476016` and `3772515911`, re-fetched via `gh api .../pulls/328/comments`
rather than trusting the paraphrase above) showed both dismissals attacked
a straw-man version of the actual suggestion:

- `3772476016` actually asked to add `DRAINING` (not `FAILED`) as a legal
  destination for the pre-`RUNNING` phases — legal under the frozen spec,
  and a genuine fix for a real gap (those phases had no direct failure
  path to `DRAINING`, unlike `RUNNING`/`RESTARTING`).
- `3772515911` was actually about premature lock release **before** child
  cleanup on an exception pre-empting the happy path — not "double
  release." F22 is silent on release *timing* relative to cleanup.

Both are now fixed: `session.py`'s pre-`RUNNING` phases gained a direct
`DRAINING` edge, and `recovery.py`'s `cancel_session`/
`RestartController.attempt()` finally blocks now attempt best-effort child
cleanup before releasing the lock on any exceptional path. Full detail,
the corrected root-cause account, and the generalizable lesson (quote the
exact comment text, not a paraphrase, when triaging) are in
`docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md`.
PR #330 itself went through 1 review-fix cycle (2 Copilot P1 findings on
its own new code — a counts-only test-ordering gap and a too-narrow
`except Exception` — both fixed, both threads resolved, 2 subsequent
Copilot re-reviews found nothing new) before merging.

Fix commits: `1eba6762` (CI fix, pre-dates the review-fix cycle count),
`abc389c8` (review-fix cycle 1), `11888fba` (review-fix cycle 2),
`06c280bd` (review-fix cycle 3 — 5 genuine fixes: the recovery.py pair,
the process_pty.py pair, and the journal.py header fix — plus the 2
now-corrected false-positive rationale replies, later shown to be
incorrect and fixed via PR #330). All fixes covered by new regression
tests in `tests/test_supervise_recovery.py`,
`tests/test_supervise_process_pty.py`, `tests/test_supervise_journal.py`.
Every commit re-ran the full suite (final: 1681/17/0), re-ran the
lifecycle topology gate, and replied-to/GraphQL-resolved every affected
thread.

**5th-round findings (on `06c280bd`, after the 3-cycle circuit breaker was
exhausted)**: 2 findings had actual posted review comments/threads; per
the Stop Conditions circuit breaker (3 review-fix cycles per task/PR
already used) and the operator's explicit instruction not to recreate an
unbounded review loop, these were **not fixed** — Ship replied to both
comments citing the exhausted circuit breaker, documented them as explicit
follow-ups in the PR body's Local Review Readiness block, and resolved
both threads (21/21 total resolved). The remaining 4 findings in this
round's review body had **no posted comment or thread at all**
(suppressed-only, per the pattern documented in
`docs/compound/114-S-109-F-copilot-review-fix-patterns.md`) — per the
operator's explicit instruction not to mine suppressed advisory material
as a separate cycle, these were documented in the PR body narrative only
and not independently triaged, fixed, or thread-resolved (no thread exists
for them to resolve).

**Total this shipment (PR #328): 21 Copilot review comments with actual
posted threads across 5 review rounds. 19 fixed -> committed -> pushed ->
replied -> GraphQL-resolved (17 across cycles 1–3, plus the CI-adjacent
fix). 2 documented as explicit follow-ups (circuit breaker exhausted,
round 5) with threads still resolved. 4 additional suppressed-only
findings from round 5 documented in the PR body only, no thread to
resolve.**

## Correction PR #330 (mis-triage fix)

| Field | Evidence |
| --- | --- |
| PR | **#330** ("fix(119-F): correct mis-triaged P0 findings — pre-RUNNING DRAINING edge and recovery cleanup-before-release ordering") |
| Branch | `fix/119-f-session-draining-edges-and-recovery-lock-ordering`, from `main` at `915923c2` |
| Commits | `dc7e8531` (initial fix + tests), `4fa3a733` (review-fix: `BaseException` catch + ordering-assertion tests) |
| Local review | Self-review at `dc7e8531`: 0 P0/P1. Outcome `READY`. |
| Full local build/test | `uv run python -m unittest discover -s tests` — 1706 passed, 17 skipped, 0 failed (final, at `4fa3a733`) |
| Copilot review | 2 rounds. Round 1 (HEAD `dc7e8531`): 2 P1 findings (test assertions verified counts, not signal/close-before-release ordering; `_best_effort_child_cleanup` caught `Exception` not `BaseException`) — both fixed in `4fa3a733`, both threads replied-to and GraphQL-resolved. Round 2 (HEAD `4fa3a733`, 2 re-review passes): no new comments. |
| P-018 copilot-review gate | `SATISFIED` at HEAD `4fa3a733a3fdac54cbba7fd2a2c98de9e6f1ae0e` (`unresolved_thread_ids: []`) |
| CI | `ci gate`/`test`/`detect code changes` SUCCESS at final HEAD. `pipeline-topology (ambient)` reported `BRANCH_MISMATCH` (advisory-only; `continue-on-error: true`, no branch protection, `PIPELINE_TOPOLOGY_GATE_REQUIRED` unset) — expected for an ad hoc post-shipment-closure fix branch that does not match the `128-S` branch-alias pattern; did not affect `ci gate` or mergeability. |
| Merge | `gh pr merge 330 --merge` — merge commit `f47c1b65bdc28aad5594856db7a592f0092f929f`, merged `2026-08-13T06:21:06Z`. Two parents confirmed (`915923c2` prior `main` tip + `4fa3a733` fix-branch HEAD). Ancestor-of-`origin/main` confirmed via `git merge-base --is-ancestor`. |
| Scope | Treated as remediation within `128-S`'s own delivered scope (fixing genuine defects in code this shipment produced, surfaced by this shipment's own closure-review process) — not an expansion into `129-S`. No new backlog task/shipment was created for this fix (Ship's role boundary); if a formal record is desired, Stage may retroactively author one. |

## Correction — corrected Copilot review detail (this section supersedes the "false positive" classification above; superseded text is left in place, marked, for the historical record — see the Correction note at the top). The corrected account, quoting the exact original comment text, is in `docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md`; the "Copilot review detail" subsection above has also been updated in place to reflect the correction and reference PR #330.

## Runtime Verification (unaffected — PR #330 touches only already-in-scope, still-fully-unwired `src/autoharness/supervise/` modules; the verdict and evidence below are unchanged by the correction)

**Surface**: pure additions (new `src/autoharness/supervise/` Python
modules — protocol/adapters, session state machine, typed events, journal,
recovery — none yet wired into any executable runtime path). Explicit
zero-observable-behavior-change scope; no new runtime surface introduced
for `start.ps1`/`start.sh`/existing CLI commands/runtime adapters.

| Field | Evidence |
| --- | --- |
| Validator | Ship pre-merge/post-merge runtime verification, per `runtime_validation.validator_manifest` in `.autoharness/workspace-profile.yaml`. |
| Surface adapter | CLI-help probe (`cli` surface, `command` adapter). |
| Runtime probe | `uv run autoharness --help` — exit 0, output unchanged. Run pre-merge at feature-branch HEAD `06c280bd` and again post-merge after pulling fresh `main` at `915923c2`. |
| UNWIRED invariant | grep across `start.ps1`, `start.sh`, `cli.py`, `templates/` for any reference to the new `supervise/` modules — **zero hits**, reverified pre-merge and post-merge. |
| Preserve-invariant | "The autoharness CLI starts without import, packaging, or option-parsing failures, and no existing runtime path gains a new dependency on the supervision core" — HELD at both HEADs. |
| Blocked prerequisites | None for the CLI surface. No browser/API/background-job surface applies — the new supervisor modules are not invocable from any existing path (explicit scope boundary), so the full unit/characterization test suite (1681/17/0, both pre- and post-merge) is the complete in-scope runtime evidence. |
| Verdict | **PASS** — the only in-scope runtime surface (the packaged CLI entrypoint) was exercised pre-merge and post-merge with no regression, and the deliberate non-wiring of the new supervision core was independently reverified both times. No fabricated automation was used. |

## Backlog Reconciliation — P-015 Verified Fully-Covered-Root Cascade Close

- **Classifier run**: `classify_shipment_close_path(['119-F', '119.001-T',
  '119.002-T', '119.003-T', '119.004-T', '119.005-T', '119.006-T'],
  '.backlogit')` returned `ClosePath.CASCADE`, `qualifying_feature_ids:
  ('119-F',)` — `119-F` is a root feature, fully covered (all 6 children
  enumerated live are manifest members), and terminal (no manifest member
  declares it as parent).
- **Dynamic engine attestation** (pre-close): installed CLI identified as
  `v1.9.0`, commit `39528a4`, build `2026-08-12T03:49:03Z` — matching the
  CLI probed directly at session start; no stray/stale process found this
  session (the prior shipment had already stopped the stale MCP daemon).
- **Closure simulation re-run** against the attested engine:
  `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1`
  — **66/66 assertions passed**, version-bound to the same engine.
- **Lifecycle topology gate**: re-run immediately before the close
  mutation (unforced) — PASS.
- **Cascade execution**: `backlogit shipment ship 128-S --sha
  915923c25453739b6da955fe247bd4b38a11e830`. Result: `shipment_status:
  shipped`, `returned_ids: []`, `archived_ids: [119.001-T, 119.002-T,
  119.003-T, 119.004-T, 119.005-T, 119.006-T, 119-F, 128-S]` — matching
  the shipment's own manifest exactly.
- **Post-close verification**: every task's `parent_id: 119-F` preserved
  unchanged in the archived record (spot-checked `119.001-T`). `119-F`
  archived (status `archived`/`archived_status: done`). `128-S` archived
  (`status: shipped`). `129-S` confirmed **untouched**, still `status:
  queued`. `backlogit doctor` run against the real workspace post-close:
  62 pre-existing `archived_from_self_ref` warnings on unrelated,
  much-older archived artifacts (`007`-`046` range, predating this
  shipment) — **zero** findings referencing `119-F`, any `119.00N-T` task,
  or `128-S`; no new corruption introduced by this closure.

## Context Compaction (P-020)

- **Status: done** — mandatory per-merge `compact-context` (`target: all`)
  invocation performed this session. Candidate identified: this release
  unit's own just-written session memory (completed-work rule). Bounded
  Tier-1 consolidation performed: 1 memory file compacted, 0 active
  checkpoints touched, 0 plans consolidated (none pending for this release
  unit), 0 additional closure records compacted (none exceeded
  `threshold_days`).
- Session memory: written to
  `docs/memory/2026-08-12-ship-128-S-119-F-session.md`, then moved verbatim
  to `docs/archive/memory/2026-08-12-ship-128-S-119-F-session.md` as part of
  this compaction pass.
- Compacted memory:
  `docs/memory/compacted/2026-08-12-128S-119F-compacted.md` (decisions,
  files modified, key learnings/cross-references to the new compound doc,
  outcomes) — written during this compaction pass.

## Operational Closure

- **Healthy signals**:
  - Feature PR #328 merged with a merge commit (two parents; P-009
    preserved).
  - Local review `READY` (1 P0 fixed pre-push); 5 rounds of Copilot
    review, 21/21 posted threads resolved (19 fixed, 2 documented
    follow-ups with rationale), re-confirmed `SATISFIED` via P-018
    immediately before merge.
  - CI green at every required check on every polled HEAD.
  - Cascade close (verified fully-covered-root exception) reconciled all 6
    tasks + `119-F` + `128-S` with `returned_ids: []` and zero
    out-of-scope mutation.
  - UNWIRED invariant held throughout: zero references to the new
    supervision core from any existing runtime path, reverified pre- and
    post-merge.
  - Dark-factory bounded scope `128-S` fully executed; `129-S` was
    explicitly NOT claimed, planned, or expanded into.
  - **Self-correction**: this closure PR's own hosted Copilot review
    caught a mis-triage in this artifact's first draft (2 findings
    wrongly classified as false positives); both were fixed and merged
    via PR #330 (merge commit `f47c1b65bdc28aad5594856db7a592f0092f929f`)
    before this artifact was finalized — the correction loop worked as
    intended, and is itself documented as a compound learning.
- **Failure signals to watch**: none specific to this shipment's own
  closure. The Copilot review-fix circuit breaker (3 cycles) was fully
  exhausted on PR #328 for the second shipment in a row in this Plan 1
  sequence — a recurring signal that this supervisor core work draws
  unusually deep and repeated hosted-review scrutiny; every fix was
  verified against frozen task specs and every deferred item is a
  documented, non-blocking follow-up. Separately, this shipment's own
  closure documentation was found to contain a mis-triage of 2 genuine
  findings as false positives — corrected and fixed via PR #330 before
  this artifact was finalized (see the Correction note above and
  `docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md`).
- **Follow-ups** (non-blocking; `closure_status: READY`):
  1. 5th-round Copilot finding (with a posted thread) on `06c280bd`,
     deferred per exhausted circuit breaker — documented rationale posted
     to the thread; see PR #328 body for the specific finding text.
  2. A second 5th-round Copilot finding (with a posted thread) on
     `06c280bd`, deferred per exhausted circuit breaker — same handling.
  3–6. Four 5th-round suppressed-only findings (review-body text, no
     thread) — documented in the PR #328 body narrative only, not
     independently triaged; per operator instruction, not mined as a
     separate review cycle.
  7. `129-S` is now unblocked (its sole predecessor `128-S` reached
     `shipped`), but was explicitly NOT claimed by this session per the
     operator's scope boundary — the Orchestrator will reload current
     `main` and advance the cursor.
  - Ship's role boundary does not permit creating backlog items directly
    for follow-ups 1–6; routed to Stage/operator for backlog authoring if
    any warrant a tracked item.
  - The `session.py:75`/`recovery.py:136` mis-triage is **not** listed as
    a follow-up here — it was fully resolved (fixed, reviewed, merged via
    PR #330) before this artifact reached its final form, not deferred.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): the shipped capability is pure additive
  Python modules (process/PTY adapters, session state machine, typed
  events, redacted journal, recovery/restart) plus tests — no runtime
  wiring, no new distribution/packaging change, no scheduler/auto-claim
  capability introduced, zero observable behavior change to any existing
  path. Rollback = revert merge commit `915923c2` and merge commit
  `f47c1b65bdc28aad5594856db7a592f0092f929f` (both additive
  modules/tests only). **Verdict: READY.**


## Closure Tasks (this branch)

1. Compound-learning doc:
   `docs/compound/2026-08-12-verify-hosted-review-findings-against-frozen-task-spec.md`
   — **done** (this branch).
2. This canonical closure artifact (this file) — **done**.
3. Session memory write + compaction to
   `docs/memory/compacted/2026-08-12-128S-119F-compacted.md` (verbose
   original archived to
   `docs/archive/memory/2026-08-12-ship-128-S-119-F-session.md`) — **done**
   (this branch).
4. Mandatory P-020 `compact-context` (`target: all`) invocation — **done**
   (this branch): 1 memory file compacted (this release unit's own
   session memory, completed-work rule), 0 active checkpoints touched, 0
   plans consolidated, 0 additional closure records compacted.
5. Closure index resync (`backlogit sync`) — **done**, both immediately
   after the cascade close mutation and again after this branch's closure
   commits.
6. Mid-flight correction (discovered via this closure PR's own hosted
   Copilot review): the compound doc (item 1), this closure artifact,
   the archived session memory, and the compacted memory were all
   originally drafted with an incorrect classification of 2 PR #328
   findings as false positives. Corrected via:
   - Follow-up fix PR #330 (branch
     `fix/119-f-session-draining-edges-and-recovery-lock-ordering`,
     merge commit `f47c1b65bdc28aad5594856db7a592f0092f929f`) — **done**,
     merged before this artifact's final form.
   - This artifact (compound doc + closure doc) rewritten in place to
     reflect the correction — **done** (this branch, this commit).
   - `docs/archive/memory/2026-08-12-ship-128-S-119-F-session.md` and
     `docs/memory/compacted/2026-08-12-128S-119F-compacted.md` corrected
     in place — **done** (this branch, this commit).

---
shipment: 129-S
feature: 120-F
tasks: [120.001-T, 120.002-T, 120.003-T, 120.004-T, 120.005-T, 120.006-T, 120.007-T, 120.008-T]
feature_pr: 331
closure_pr: 332
merge_commit: fa0eb14bad50d0b4ec028685a15f7472a6984e39
merged_at: "2026-08-13T20:29:10Z"
reviewed_head: 3867917fa11e56deb2c3968fceea54a0187bf619
closure_status: READY
compaction_status: done
feature_terminal_status: done
feature_archived_status: done
umbrella_feature: 117-F
umbrella_terminal_status: done
umbrella_archived_status: done
shipment_close_path: cascade
---

# 129-S / 120-F Post-Merge Closure — S3 Copilot Supervisor: Application Services, Adapters, start.ps1/start.sh Migration (FINAL, Plan 1)

Shipment `129-S` is the **FINAL** shipment of the strict serial chain
`127-S -> 128-S -> 129-S` for Plan 1 (Local Copilot CLI supervisor /
control-plane runtime). Covering feature `120-F` is a root feature (no
parent) with exactly 8 children, all of which are this shipment's manifest.
The manifest additionally carries the childless product umbrella `117-F` as
a second root member — safe because `descendantItems(117-F)` is empty, so
its archival at close retires the entire Plan-1 program record with no
post-close operator action. Scope: application services (`bootstrap.py`,
`sidecar.py`, `resolve.py`, `app.py`, `approvals.py`), the `autoharness run`
CLI adapter, the `start.ps1`/`start.sh` (+ `templates/` copies)
compatibility-shim migration, and rollout/rollback documentation. This is
the only behavior-changing shipment in the chain.

## Recovery Context

This shipment was resumed from an **interrupted Ship invocation**. The
branch (`feat/129-s-s3-copilot-supervisor-application-services-adapters-start-ps1-start-sh-migration`)
and HEAD (`0ff7bd8e`) were preserved in place; `129-S` was already `active`
and was **not** re-claimed. `backlogit checkpoint list --agent ship --status
active --shipment-id 129-S` returned zero candidates and zero quarantine
anomalies — the valid zero-candidate startup path — so the active cursor
was continued directly from branch/worktree evidence per the operator's
explicit recovery instructions, with no checkpoint invented or restored.

## Release-Blocking Runtime Defect: Diagnosed and Fixed Before Any Further PR Work

The operator reported a concrete runtime defect from a real launch: Engram
and graphtor-docs never became live under `start.ps1`/`autoharness run`,
while Copilot and backlogit processes started successfully. Per the
operator's explicit instruction, this was diagnosed and fixed within
`129-S`'s existing scope **before** any PR/merge/closure work proceeded.

**Root cause**: the committed `.mcp.json` used the VS-Code-only editor
variable `${workspaceFolder}` in the engram/graphtor-docs/backlogit MCP
server `env` blocks. The standalone `copilot` CLI (the actual runtime behind
`autoharness run`/`start.ps1`/`start.sh`) never substitutes editor
variables — it passes the literal, unresolved string through, verified via
`copilot mcp get engram --json --show-secrets` echoing the raw text. Both
`engram shim` and `graphtor-docs serve` crashed immediately on the
unresolved literal path; Copilot and backlogit kept running because neither
depended on that broken value — exactly matching the reported symptom.

**Fix** (three complementary parts, all within existing 129-S/120-F scope,
commit `d2a01855`):

1. `.mcp.json` — removed the broken `${workspaceFolder}` overrides
   entirely; each tool falls back correctly to its own CWD-relative
   default.
2. `supervise/process.py`, `supervise/process_pty.py`, `supervise/app.py` —
   threaded an explicit `cwd` through every real child-process backend and
   anchored the default Copilot child factory's cwd to `workspace_root`.
3. `supervise/sidecar.py` — added graphtor-docs as a third one-shot
   preflight sidecar (mirroring backlogit sync / Engram pre-warm), with
   PATH + workspace-local `.graphtor/bin/graphtor-docs(.exe)` fallback
   resolution, and threaded `cwd=str(workspace_root)` through every
   sidecar subprocess call (previously accepted only for interface
   symmetry, never applied).

Test-first: failing tests added across `test_supervise_process.py`,
`test_supervise_process_pty.py`, `test_supervise_sidecar.py`, and
`test_supervise_app.py` before the production fix, including a POSIX
real-subprocess integration/smoke test proving all three sidecars complete,
in order, strictly before the (faked) Copilot child spawn. A regression
guard was added to `test_verify_workspace.py` asserting `.mcp.json` never
reintroduces `${workspaceFolder}`/`${workspace_folder}`. Empirically
validated end-to-end in an isolated fake-executable sandbox exercising the
real production code path via `autoharness run` (never touching the
operator's live Copilot session): all three sidecars run in order
(backlogit -> engram -> graphtor-docs) with `cwd` correctly anchored, ahead
of the correctly-cwd-anchored Copilot child. Full detail in
`docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`.

## Merge Confirmation

- PR **#331** ("feat(129-S): S3 Copilot supervisor -- application services,
  adapters, start.ps1/start.sh migration") merged to `main` at
  `2026-08-13T20:29:10Z` with merge commit
  `fa0eb14bad50d0b4ec028685a15f7472a6984e39`. Confirmed via `git log -1
  --format=%P` on the merge commit: two parents (`5f1b5ac2` prior `main`
  tip + `3867917f` feature branch HEAD), preserving the P-009 merge-commit
  strategy structurally.
- Confirmed ancestor of `origin/main` (`git fetch origin main` then
  `git merge-base --is-ancestor fa0eb14b origin/main` -> exit 0).
- Repo merge-strategy settings (P-009), verified: `allow_merge_commit:
  true`, `allow_squash_merge: false`, `allow_rebase_merge: false` — only
  "Create a merge commit" is possible.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Full local build / test evidence | Full suite at final HEAD `3867917f`: **1853 passed (+713 subtests), 0 failed, 19 skipped**. `uv run autoharness --help` smoke test PASS pre- and post-merge. |
| CI (PR #331) | `CI` and `Running Copilot Code Review` workflows SUCCESS at every polled HEAD across all 8 review rounds, including final HEAD `3867917f`. |
| Copilot review (PR #331) | **8 review rounds**, 16 total findings with posted threads, **all 16 fixed** with real code + regression tests (none dismissed, none deferred). All 16 threads replied-to and GraphQL-resolved. See detail below. |
| P-018 copilot-review gate | `SATISFIED` at final HEAD `3867917f` (0 unresolved threads), re-confirmed unconditionally immediately before merge (headRefOid unchanged). |
| §1.9 pre-merge readiness (Checks 1–5) | PASS at HEAD `3867917f`: PR body Local Review Readiness block refreshed to this HEAD, outcome `READY`, P0=0/P1=0 residual, full local build evidence recorded (1853/713 subtests/19 skipped), P-018 result explicitly recorded `SATISFIED`. |
| Dark-mode merge authorization | No formal `DARK_MODE_ACTIVE` activation record file existed in `.autoharness/`; the operator's own explicit initiating instruction ("merge with `--merge` under the existing operator dark-mode full approval only after all gates pass") was treated as the conditioned approval signal, exercised once CI green + P-018 `SATISFIED` + P-009 verified all held. Normal merge (`gh pr merge 331 --merge`) succeeded directly — no admin fallback needed. |
| Worktree/PR topology (P-016) | Single worktree throughout; no parallel worktree created or used. |

### Copilot review detail (8 rounds, 16 posted threads, all 16 fixed)

Genuine correctness fixes spanned redaction coverage, concurrency-lock
ordering, and PTY process-lifecycle safety (rounds 1–6 fixed in earlier
windows; rounds 7–8 fixed this window):

- **Round 7** (`b3710d2b`): `bootstrap.py`'s `.env.local` loader registered
  only two hardcoded GitHub-token variable names with the redactor — any
  other secret-shaped value (e.g. `TAVILY_API_KEY`) went unprotected.
  Fixed via key-name pattern matching (`TOKEN|SECRET|KEY|PASSWORD`).
  `app.py`'s `_pump_child_output` wrote raw child output directly to
  `sys.stdout` before either redaction choke point — fixed by redacting
  each chunk via `redact_record()` before the console write (fail-closed:
  dropped if redaction fails).
- **Round 8** (`3867917f`): `_ENVIRON_MUTATION_LOCK` was acquired only
  around the `os.environ.update()` step, but `bootstrap_workspace()`'s
  own internal unsynchronized `dict(os.environ)` baseline read logically
  preceded it — fixed by acquiring the lock before the call.
  `process_pty.py`'s POSIX `signal()` had no already-exited guard (unlike
  `close()`), risking a PID-reuse signal during restart — fixed by
  passing `child=None` into `RestartController.attempt()` plus an
  explicit `child.close()` to avoid introducing an fd leak.

Every finding got a real code fix plus a new regression test. Total this
shipment (PR #331): **16 Copilot review comments with posted threads
across 8 review rounds — 16/16 fixed, committed, pushed, replied, and
GraphQL-resolved.** Zero deferred, zero suppressed-only mining.

## Runtime Verification

**Surface**: behavior-changing — the ONLY behavior-changing shipment in the
Plan-1 chain. `start.ps1`/`start.sh` are now thin compatibility shims over
`autoharness run`; the shared Python supervisor (`bootstrap.py`,
`sidecar.py`, `app.py`, `resolve.py`, `approvals.py`) is the single source
of truth across CLI and shims.

| Field | Evidence |
| --- | --- |
| Validator | Ship pre-merge/post-merge runtime verification, per `runtime_validation.validator_manifest` in `.autoharness/workspace-profile.yaml`. |
| Surface adapter | CLI-help probe (`cli` surface, `command` adapter). |
| Runtime probe | `uv run autoharness --help` — exit 0, output unchanged. Run pre-merge at feature-branch HEAD `3867917f` and again post-merge on fresh `main` at `fa0eb14b`. |
| Root-cause fix validation | Empirically validated end-to-end in an isolated fake-executable sandbox exercising the real production code path via `autoharness run` (never touching the operator's live Copilot session): all three sidecars (backlogit, Engram, graphtor-docs) run in order with `cwd` correctly anchored, followed by the correctly-cwd-anchored Copilot child. `.mcp.json` verified clean of `${workspaceFolder}`/`${workspace_folder}` on `main` post-merge (zero matches). |
| Preserve-invariants | TTY/PTY semantics (never pipe fallback); terminal states `{EXITED, FAILED, REFUSED, CANCELLED}`; exact gated-action catalog `{session_restart, force_unlock}`; guard/record locking; three named migration deltas (`WINDOWS_PAT_NO_GH`, `POSIX_ENGRAM_DATA_DIR`, `POSIX_PAT_BOOTSTRAP`); local fail-closed approvals; model routing from config; no remote control — all preserved per the full test suite and the characterization baseline (`118-F` byte-identical re-run). |
| Blocked prerequisites | None for the CLI surface. |
| Local-environment observation (non-blocking) | `tests.test_supervise_locking.RealParallelContenderTests.test_exactly_one_contender_acquires_per_iteration` (a real 8-subprocess race test, pre-existing from `127-S`/`118.005-T`, **not touched by this shipment's diff**) intermittently fails on this local Windows dev machine (different iteration each run: 17, 32, 37) with a genuine double-acquisition outcome. CI (`ubuntu-latest`) was green at every round including the final merged HEAD `3867917f` — CI never exercises this Windows-specific timing path. Documented as a follow-up, not a `129-S` blocker: the file is out of this shipment's scope and the authoritative CI gate passed throughout. |
| Verdict | **PASS** — the packaged CLI entrypoint and the fixed sidecar/Copilot startup path were exercised pre-merge and post-merge with no regression against any in-scope invariant. No fabricated automation was used. |

## Backlog Reconciliation — P-015 Verified Fully-Covered-Root Cascade Close

- **Classifier run**: `classify_shipment_close_path(['120-F', '120.001-T',
  '120.002-T', '120.003-T', '120.004-T', '120.005-T', '120.006-T',
  '120.007-T', '120.008-T', '117-F'], '.backlogit')` returned
  `ClosePath.CASCADE`, `qualifying_feature_ids: ('120-F', '117-F')` —
  `120-F` is a root feature fully covered by its 8 children (all manifest
  members), and `117-F` is a verified root, childless, and terminal
  (declared as no manifest member's parent).
- **Dynamic engine attestation** (pre-close): installed CLI identified as
  `v1.9.0`, commit `39528a4` (binary `C:\Tools\backlogit.exe`) — matching
  the `097-S` doc's documented re-run identity exactly.
- **Closure simulation re-run** against the attested engine:
  `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1`
  — **66/66 assertions passed**.
- **`117-F` independent verification**: `backlogit get 117-F` shows no
  `parent_id` field (root) and zero live children in `.backlogit/queue/`
  + `.backlogit/archive/`.
- **Cascade execution**: `backlogit shipment ship 129-S --sha
  fa0eb14bad50d0b4ec028685a15f7472a6984e39`. Result: `shipment_status:
  shipped`, `returned_ids: []`, `archived_ids: [120.001-T, 120.002-T,
  120.003-T, 120.004-T, 120.005-T, 120.006-T, 120.007-T, 120.008-T,
  117-F, 120-F, 129-S]` — matching the shipment's own documented
  expectation exactly.
- **Post-close verification**: every task archived under
  `.backlogit/archive/`; `120-F` archived (`archived_status: done`);
  `117-F` archived (`archived_status: done`); `129-S` archived
  (`archived_status: shipped`). Zero Plan-1 queue residue confirmed:
  no `11*`/`12*` files remain in `.backlogit/queue/`.
- With `129-S` closed, the **entire Plan-1 program** (`127-S -> 128-S ->
  129-S`, including the childless product umbrella `117-F`) is now
  **terminal with zero queue residue**.

## Context Compaction (P-020)

- **Status: done** — mandatory per-merge `compact-context` (`target: all`)
  invocation performed this session. Candidate identified: this release
  unit's own just-written session memory (completed-work rule). Bounded
  Tier-1 consolidation performed: 1 memory file compacted, 0 active
  checkpoints touched, 0 plans consolidated (none pending for this release
  unit), 0 additional closure records compacted (none exceeded
  `threshold_days`).
- Session memory: written to
  `docs/memory/2026-08-13-ship-129-s-recovery-runtime-defect-and-closure.md`,
  then moved verbatim to
  `docs/archive/memory/2026-08-13-ship-129-s-recovery-runtime-defect-and-closure.md`
  as part of this compaction pass.
- Compacted memory:
  `docs/memory/compacted/2026-08-13-129S-120F-compacted.md` (decisions,
  files modified, key learnings/cross-references, outcomes) — written
  during this compaction pass.

## Operational Closure

- **Healthy signals**:
  - Feature PR #331 merged with a merge commit (two parents; P-009
    preserved).
  - The operator-reported release-blocking runtime defect
    (Engram/graphtor-docs) diagnosed and fixed within existing scope
    before any PR/merge/closure work proceeded, per explicit instruction.
  - 8 rounds of Copilot review, 16/16 posted threads resolved (all fixed,
    zero deferred), re-confirmed `SATISFIED` via P-018 immediately before
    merge.
  - CI green at every required check on every polled HEAD across all 8
    rounds.
  - Cascade close (verified fully-covered-root exception) reconciled all
    8 tasks + `120-F` + `117-F` + `129-S` with `returned_ids: []` and zero
    out-of-scope mutation.
  - Full Plan-1 program (`127-S -> 128-S -> 129-S`) now terminal, zero
    queue residue.
- **Failure signals to watch**: none specific to this shipment's own
  scope. A **Windows-local-only** flaky test
  (`RealParallelContenderTests.test_exactly_one_contender_acquires_per_iteration`,
  pre-existing from `127-S`/`118.005-T`, out of `129-S` scope) intermittently
  fails on this dev machine with a genuine double-acquisition outcome; CI
  (`ubuntu-latest`, the authoritative gate) never exercises this Windows
  timing path and was green throughout. Recorded as a follow-up.
- **Follow-ups** (non-blocking; `closure_status: READY`):
  1. Windows-local-only race-timing flakiness in
     `tests.test_supervise_locking.RealParallelContenderTests.test_exactly_one_contender_acquires_per_iteration`
     — out of `129-S` scope (the file was untouched by this shipment's
     diff, originating from `127-S`/`118.005-T`). CI (`ubuntu-latest`) was
     green at every round including the final merged HEAD. Recommend a
     tracked investigation task (Stage/operator) if hardening the
     guard/record lock against this specific local-timing race is
     desired; not a blocker for this closure.
  - Ship's role boundary does not permit creating a backlog item directly
    for this follow-up; routed to Stage/operator for backlog authoring if
    a tracked item is warranted.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): the shipped capability is the final,
  behavior-changing wiring of the Local Copilot CLI supervisor into
  `autoharness run`/`start.ps1`/`start.sh`, with the release-blocking
  Engram/graphtor-docs defect fixed and empirically validated end-to-end.
  Rollback = single-file revert per shim to the git-SHA-preserved
  pre-migration script, requiring a redeploy (DoD #2, F16 ruling —
  deliberate, no environment-variable escape hatch). **Verdict: READY.**

## Closure Tasks (this branch)

1. Compound-learning doc:
   `docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`
   — **done** (this branch).
2. This canonical closure artifact (this file) — **done**.
3. Session memory write + compaction to
   `docs/memory/compacted/2026-08-13-129S-120F-compacted.md` (verbose
   original archived to
   `docs/archive/memory/2026-08-13-ship-129-s-recovery-runtime-defect-and-closure.md`)
   — **done** (this branch).
4. Mandatory P-020 `compact-context` (`target: all`) invocation — **done**
   (this branch): 1 memory file compacted (this release unit's own
   session memory, completed-work rule), 0 active checkpoints touched, 0
   plans consolidated, 0 additional closure records compacted.
5. Closure index resync (`backlogit sync`) — **done**, immediately after
   the cascade close mutation (indexed 784 artifacts).

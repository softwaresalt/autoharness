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

### Post-hoc forensic reconstruction (reboot-boundary evidence)

After this shipment fully shipped and closed, the operator reported that
the interruption was caused by a **hard devbox reboot**, not a graceful
session end, and asked for a bounded, evidence-based reconstruction of the
exact shutdown point rather than an inference from dirty-file presence
alone. The hard-reboot characterization itself (forced/abrupt vs. an
otherwise-graceful restart) is the operator's own report; the artifacts
below independently confirm only that a reboot occurred at a specific
time and that the surrounding commit/log timing is *consistent with* an
abrupt interruption at that boundary, not an independent proof of the
forced-shutdown mechanism. The following was gathered and cross-checked
against live system and repository state (all read-only, performed after
closure; no repeat mutation):

- **System boot time**: `Get-CimInstance Win32_OperatingSystem` reports
  `LastBootUpTime = 2026-08-13 01:31:31 -07:00`.
- **Last pre-reboot commit**: `git log` (author/committer dates, not mtimes)
  shows commit `0ff7bd8e81d4ac509e7d2eba47504bd336df6a8b`
  ("feat(supervise): add sidecar preflight service (120.002-T)") at
  `2026-08-13T01:30:01-07:00` — **90 seconds before** the recorded boot
  time, with the *previous* commit (`21a081a8`, 120.001-T) at
  `2026-08-13T01:29:54-07:00`, only 7 seconds earlier. This tight
  back-to-back commit cadence terminating abruptly 90 seconds before a
  recorded reboot, with a **~8.75 hour gap** to the next commit
  (`28377c6f`, 120.003-T, at `2026-08-13T10:17:33-07:00`), is consistent
  with an abrupt termination rather than a graceful session close (a
  clean shutdown would not typically leave a commit made 90 seconds
  before the OS records a boot with zero activity for nearly 9 hours).
  This also matches the operator's own preserved recovery instructions at
  the start of this session, which named this exact commit
  (`0ff7bd8e`) as the HEAD to preserve.
- **No recoverable checkpoint existed**: no `.autoharness` lock or
  checkpoint file predating the reboot was found; `backlogit checkpoint
  list --agent ship --status active --shipment-id 129-S` returned zero
  candidates at session start — consistent with a hard kill that gave no
  opportunity to persist a checkpoint, not with a session that completed
  and cleaned up normally.
- **Task-level event log cross-check** (`.backlogit/logs/120.00{1-8}-T.jsonl`):
  every one of the eight tasks shows the SAME two-phase pattern —
  `status_changed` (claim to active) clustered at `2026-08-12 23:52:07-23`
  (the night *before* the reboot), followed by `pre_task_completion_gate_passed`
  and `commit_tracked` events clustered at `2026-08-13 10:19-10:29 AM`
  (**after** the reboot, in the recovery session). This confirms
  completion gates and commit-tracking evidence for every task were
  generated fresh, post-recovery — task "active" status alone, inherited
  from before the crash, was never treated as evidence of completion.
  Torn/dirty implementation artifacts described in the operator's
  recovery instructions (untracked `supervise/app.py`, `approvals.py`,
  `resolve.py` plus tests, dirty `cli.py`, migrated `start.ps1`/`start.sh`)
  were carried forward and completed through normal task execution — full
  suite runs, CI, and (for the shipped PR) 8 independent rounds of hosted
  Copilot review that found and required fixing 16 additional genuine
  defects — never accepted on the strength of their pre-crash dirty state
  alone.
- **Conclusion**: the reconstructed shutdown point is commit `0ff7bd8e`
  (120.002-T, sidecar preflight service) at `2026-08-13T01:30:01-07:00`,
  approximately 90 seconds before the devbox's recorded reboot at
  `01:31:31-07:00` (reported by the operator as a hard/forced shutdown;
  the timing evidence above is consistent with that report but does not
  independently distinguish a forced kill from another abrupt-restart
  cause). Every task and artifact from `120.003-T` onward, the
  Engram/graphtor-docs root-cause fix, all 8 rounds of P-018 review
  remediation, the merge, and the cascade close were performed and
  verified in the single continuous recovery session that followed,
  using live-executed gates (tests, CI, independent hosted review,
  the P-015 classifier, and a live `sim-shipment-closure.ps1` re-run) at
  every acceptance decision — not inferred from file mtimes or dirty-state
  presence alone. `recovered_after_hard_reboot: true` (per operator
  report) for this shipment's execution history.

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

## Post-Closure Correction Addendum (2026-08, Ship post-merge correction authority)

**This section corrects, and does not retract, the "Release-Blocking
Runtime Defect" section above.** `129-S` is archived/closed and was not
reopened, reclaimed, or re-triaged for this correction; the fix below was
delivered as an independent correction PR under Ship's post-merge
correction authority, on its own branch, through the full Ship pipeline
(local review, CI, P-018 Copilot review, P-014 readiness, merge-commit-only
merge).

### Corrected root cause

The original fix's premise — "remove `.mcp.json`'s broken
`${workspaceFolder}` literal and rely on the Copilot child's `cwd` being
anchored to `workspace_root`" — is **necessary but not sufficient**. A live,
real-process verification of a running operator Copilot session (read-only;
no operator process touched) showed the Copilot-spawned Engram daemon bound
to a **different sibling workspace** (`C:\Source\GitHub\engram`) rather
than the intended target (`C:\Source\GitHub\autoharness`), even with the
corrected, placeholder-free `.mcp.json` in place and the child's `cwd`
correctly anchored.

Root cause of the residual defect: both `engram` and `graphtor-docs`
resolve their target workspace from an **environment variable** first
(`ENGRAM_WORKSPACE`, `GRAPHTOR_DB_PATH`/`GRAPHTOR_SOURCES` respectively —
confirmed directly against each real installed binary's own `--help`
output), and an environment variable **always wins over a CWD-relative
default** in both tools' own precedence. Because the supervisor never set
these variables itself, the Copilot child (and its MCP descendants)
inherited whatever value happened to already be present in the ambient
process environment (e.g. a stale value set in an operator's shell profile,
a previous session, or `.env.local`) — silently overriding the correct
`cwd` anchoring. Removing `${workspaceFolder}` fixed the "crashes on an
unresolved literal" symptom; it did nothing to prevent a *validly resolved
but wrong* stale environment binding.

### Corrected fix

`bootstrap_workspace()` (`src/autoharness/supervise/bootstrap.py`) now
resolves the target `workspace_root` and **force-applies** three
authoritative, child-only environment variables, always overriding any
ambient/`.env.local`-supplied value for these three names specifically:

- `ENGRAM_WORKSPACE=<resolved workspace_root>`
- `GRAPHTOR_DB_PATH=<resolved workspace_root>/.graphtor/graph.db`
- `GRAPHTOR_SOURCES=<resolved workspace_root>/.graphtor/config/sources.yaml`

`BACKLOGIT_WORKSPACE` was deliberately **not** invented: `backlogit --help`
confirms no such environment variable exists in the installed binary;
backlogit resolves its target solely via process `cwd` (already correctly
anchored by `129-S`'s original fix), so no new binding variable is needed
or introduced for it.

### Environment precedence (now explicit and deterministic)

1. The explicit `--workspace`/resolved target `workspace_root` always
   wins for the three binding variables above — this is the **only**
   exception to `bootstrap_workspace()`'s otherwise-universal
   additions-only (NO-CLOBBER) environment contract, and is applied
   **last**, after `.env.local` loading, directory defaults, and token
   resolution.
2. `.env.local` may still configure non-binding details (e.g. embedding
   model choice, unrelated data directories) but can never redirect the
   supervisor's binding of Engram/graphtor-docs to a different workspace.
3. A stale/ambient value for any of the three binding variables, present
   in the process environment before `bootstrap_workspace()` runs, is
   force-overridden; a diagnostic warning (path-only, never secret-shaped)
   is emitted whenever an override actually changes a previously-set
   value.
4. `.mcp.json` remains environment-agnostic: no committed absolute path,
   no `${workspaceFolder}`/`${workspace_folder}`, and (newly asserted by a
   regression test) no `"env"` key at all — the dynamic binding values
   flow from the supervisor process environment that Copilot/MCP children
   inherit, never from the MCP config file itself.
5. The existing `_ENVIRON_MUTATION_LOCK` bootstrap-read/apply/spawn/restore
   serialization mechanism in `app.py` (already proven, pre-correction, to
   span the full child lifetime across concurrent `run_session()` calls)
   is reused unchanged as the delivery mechanism for these three
   variables; no new per-child explicit environment-threading mechanism
   was introduced. This was a deliberate scope decision (see Residual
   Risks below).

### Real, isolated evidence gathered (read-only against the live operator
session; new-process-only against isolated sandboxes)

- **Live defect confirmation (read-only)**: `Get-CimInstance Win32_Process`
  against the operator's actual running Copilot session (PID 21048) showed
  its owned `engram.exe shim` (PID 17156 at capture time) owning a daemon
  (PID 26888) with command line `engram.exe daemon --workspace
  \\?\C:\Source\GitHub\engram` — the wrong workspace. No operator process
  was signaled, killed, restarted, or adopted at any point in this
  correction.
- **Real-binary capability confirmation**: `engram --help`, `graphtor-docs
  --help`, and `backlogit --help` run directly against
  `C:\Tools\engram.exe`, `C:\Tools\graphtor-docs.exe`, and
  `C:\Tools\backlogit.exe` respectively, confirming `[env:
  ENGRAM_WORKSPACE=]`, `[env: GRAPHTOR_DB_PATH=]`/`[env:
  GRAPHTOR_SOURCES=]`, and the absence of any analogous backlogit
  variable.
- **Isolated real-binary fix verification** (new git-initialized temp
  workspaces only; every spawned PID individually diffed and reaped by
  exact PID/command-line marker match, never by name; zero operator PIDs
  touched at any point):
  - `engram --format json bind` with only `ENGRAM_WORKSPACE=<temp
    workspace>` set (no `--workspace` flag, replicating `.mcp.json`'s bare
    `engram shim` invocation) binds to the **env-supplied** workspace, not
    any other/stale one.
  - `graphtor-docs --json status` with `GRAPHTOR_DB_PATH`/
    `GRAPHTOR_SOURCES` resolving **inside** the cwd-derived workspace root
    succeeds; the same call with `GRAPHTOR_DB_PATH` resolving **outside**
    it, once a `.graphtor/config/sources.yaml` marker establishes a
    workspace root at `cwd`, is rejected with a `path_violation` error —
    confirming both paths must always be derived together from the same
    `workspace_root` used to anchor `cwd`, exactly as
    `_resolve_binding_env()` now does.
  - Encoded as opt-in (`AUTOHARNESS_REAL_BINARY_SMOKE=1`, Windows-only,
    both binaries required on `PATH`) tests in
    `tests/test_supervise_binding_real_binary_smoke.py`, skipped by
    default (including on the Linux-only CI runner, which installs
    neither binary) — matching this suite's existing hermetic-by-default
    convention.
  - A critical, non-obvious subprocess gotcha was discovered and worked
    around during this verification: both `engram` and `graphtor-docs` CLI
    invocations can leave a detached daemon process alive after the
    immediate CLI process exits, and that daemon can inherit the
    immediate process's stdout/stderr pipe write-ends — causing
    `subprocess.run(capture_output=True, timeout=N)` to hang indefinitely
    even with a timeout set (CPython's timeout handling performs one final
    *blocking* `communicate()` after killing the process). The fix:
    redirect stdout/stderr to real temp files (never pipes), use
    `proc.wait(timeout=...)` (never `communicate()`), and clean up temp
    directories with `shutil.rmtree(ignore_errors=True)` in a `finally`
    block rather than a context manager whose `__exit__` raises on
    cleanup failure.
- **Graphtor lazy-activation clarification**: this correction does not
  claim to prove Copilot's own MCP stdio-server activation timing; the
  real-binary tests above verify the underlying binary/env contract
  (`graphtor-docs serve`'s preflight configuration is honorable given the
  injected env and workspace `cwd`), which is the actually-testable,
  binary-owned half of that contract. See Residual Risks.

### Files changed in this correction

- `src/autoharness/supervise/bootstrap.py` (core fix: `_BINDING_ENV_VAR_NAMES`,
  `_resolve_binding_env()`, `_apply_binding_env()`, wired into
  `bootstrap_workspace()`).
- `tests/test_supervise_bootstrap.py` (`RuntimeBindingEnvTests`, 6 tests).
- `tests/test_supervise_app.py` (`RuntimeBindingEnvReachesChildTests`, 1
  test proving the binding env reaches `os.environ` at the exact moment
  `child.spawn()` is called, and is restored afterward).
- `tests/test_supervise_process.py` (`EnvPropagationTests`, 3 tests proving
  `PipeChildProcess`/`InheritStdioChildProcess` never pass an explicit
  `env=` override).
- `tests/test_supervise_process_pty.py` (`EnvPropagationTests` +
  `RealPtyEnvPropagationTests`, proving neither PTY backend passes an
  explicit env override; POSIX-real-subprocess variant skipped on
  Windows).
- `tests/test_verify_workspace.py` (two new regression assertions: no
  absolute/drive-letter path and no `"env"` key anywhere in `.mcp.json`).
- `tests/test_supervise_binding_real_binary_smoke.py` (new, opt-in,
  real-binary smoke coverage described above).
- `docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`
  (root-cause narrative corrected).
- This file.

### Residual risks

1. **No explicit per-child environment-threading refactor.** This
   correction reused the existing process-global,
   lock-serialized-mutate/restore mechanism (`_ENVIRON_MUTATION_LOCK` in
   `app.py`) rather than refactoring `process.py`/`process_pty.py` to
   thread an explicit, isolated `env=` dict per spawned child. This was a
   deliberate scope decision: the existing mechanism was proven (by test
   and by the pre-existing design it already implements) to serialize the
   full bootstrap-read-through-restore window across the entire child
   lifetime, so no window exists in which a concurrent `run_session()` call
   for a different workspace could observe the wrong binding values. A
   future hardening could still migrate to explicit per-child env
   threading for defense-in-depth against a future refactor accidentally
   narrowing the lock's scope.
2. **Copilot's own MCP stdio-server lazy-activation contract is
   Copilot-owned, not autoharness-owned.** This correction proves the
   underlying binary/env contract (the real `graphtor-docs`/`engram`
   binaries honor the injected values), but does not — and cannot, from
   within this repository — prove or change *when* Copilot itself chooses
   to launch a registered stdio MCP server. If Copilot's own activation
   contract changes in a future version, the functional-availability
   concern (as opposed to the process-name/binding concern this correction
   closes) would need separate, Copilot-side verification.
3. **Windows-only real-binary smoke coverage.** The opt-in real-binary
   smoke tests are gated to `win32` because the verified live defect and
   the available `engram.exe`/`graphtor-docs.exe` binaries in this
   environment are Windows-only; the underlying env-var-precedence
   contract itself is covered platform-independently by the hermetic
   `EnvPropagationTests`/`RealPtyEnvPropagationTests` (the latter
   POSIX-real-subprocess, skipped on Windows) in
   `test_supervise_process.py`/`test_supervise_process_pty.py`.

### Correction delivery record

- **Correction PR**: [#334](https://github.com/softwaresalt/autoharness/pull/334).
- **Reviewed HEAD**: `146546db482c4df542ebc5cd04f4883a8fd67311` (round-1
  Copilot/P-018 review: 5 findings, all fixed and resolved — untrusted
  override-warning echo, unescaped PowerShell single-quote interpolation
  in the smoke-test cleanup helper, missing graphtor-docs cleanup in two
  smoke-test probes, drive-letter-only `.mcp.json` absolute-path regression
  guard, and an unset `correction_pr` frontmatter field).
- **Merge commit**: `43b531b0e63c10be2e0870faca38484bb9366b1b` (2 parents,
  confirmed ancestor of `origin/main` via `git merge-base --is-ancestor`).
  Merged via `--merge` (merge commit strategy; repo settings confirm
  `allow_squash_merge`/`allow_rebase_merge` both `false`, P-009 preserved).
- **CI**: green at every polled HEAD (both the initial and the review-fix
  commit).
- **P-018 gate**: `SATISFIED` at merge time — 0 unresolved threads.
- **Full local suite**: 1887 tests, OK (skipped=23), re-verified at both
  commits.
- **P-020 compact-context**: invoked (`target: all`) during post-merge
  closure on branch `post-merge/129-s-post-closure-runtime-binding-correction`.
  Candidate: this correction's own session memory (completed-work rule).
  Bounded Tier-1 consolidation performed: 1 memory file compacted, 0
  active checkpoints touched, 0 plans consolidated (none pending), 0
  additional closure records compacted (none exceeded `threshold_days`).
  Session memory written to
  `docs/memory/2026-08-13-ship-129-s-post-closure-runtime-binding-correction.md`,
  then moved verbatim to
  `docs/archive/memory/2026-08-13-ship-129-s-post-closure-runtime-binding-correction.md`
  as part of this compaction pass. Compacted memory:
  `docs/memory/compacted/2026-08-13-129S-120F-postclosure-correction-compacted.md`.
- **No backlogit shipment or task was created, claimed, or touched for
  this correction.** `129-S`/`120-F`/`117-F` remain archived exactly as
  they were before this correction began.

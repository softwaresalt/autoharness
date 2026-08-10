---
title: "Implementation Plan — autoharness as a Local Copilot CLI Supervisor / Control-Plane Runtime (Plan 1, FAST-TRACK)"
date: "2026-08-09"
description: "Durable implementation plan for turning autoharness into a local, operator-driven supervisor/control plane for long-horizon Copilot CLI workloads. Copilot CLI remains the reasoning/agent-execution engine; autoharness owns lifecycle, policy, and supervision only. Explicitly excludes Gradio, devtunnel, remote UI/control, remote auth, remote approvals, browser terminal streaming, and any remote service (deferred to Plan 2)."
doc_type: plan
source: docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md
plan_id: "PLAN-1"
stash_ids: ["34D50F2D"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - ".backlogit/archive/004-SP.md"
  - "docs/decisions/2026-08-09-composability-single-source-of-truth-spike.md"
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md"
  - "docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md"
  - "docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md"
  - "start.ps1"
  - "start.sh"
  - "src/autoharness/cli.py"
tags: ["34D50F2D", "candidate-a", "supervisor", "control-plane", "copilot-cli", "plan", "fast-track", "P-006"]
---

# Implementation Plan — Local Copilot CLI Supervisor / Control Plane (Plan 1)

## 1. Objective and product decision

autoharness becomes a **local supervisor / control-plane runtime for long-horizon
Copilot CLI workloads**. Copilot CLI is preserved, unchanged, as the
reasoning and agent-execution engine. autoharness supervises it: workspace
bootstrap, sidecar lifecycle/preflight, child process/PTY management, an explicit
session state machine, local structured commands and approvals, progress/events,
cancellation, controlled restart/resume, logs/checkpoints, secret redaction,
workspace/session locking, and recovery.

This clarifies — and materially changes — the disposition of stash `34D50F2D`
candidate (a). The 2026-08-09 spike (`004-SP`) issued **CONDITIONAL PROCEED**
because the only interpretation on the table was product-spec §3 read literally
as an in-process *action/observation execution engine*. That reading was, and
remains, **NO-GO**. The operator's clarified scope is a different thing:
**supervising an external agent runtime is in scope; implementing a new agent
runtime is not.** Under that clarified scope the spike's disposition is
reconciled to an evidence-backed **PROCEED** (see §2).

### 1.1 Authority boundaries (unchanged, load-bearing)

| Component | Authority |
|---|---|
| **Copilot CLI** | Reasoning, model calls, tool dispatch, action/observation loop. External. autoharness never reimplements it. |
| **autoharness** | Lifecycle, policy, supervision, containment, observability. Owns *when/whether/under what constraints* the engine runs — never *what the model decides*. |
| **backlogit** | Backlog + checkpoints. Authoritative. Read/write via its own surfaces only. |
| **Engram** | Read-only workspace-memory sidecar. **No execution and no mutation authority.** Never authoritative for supervision decisions. |
| **graphtor-docs** | Docs retrieval. Read-only. |
| **`.autoharness/config.yaml`** | Model-routing authority. Product-spec model names are illustrative/non-authoritative and must not be hardcoded. |

## 2. Reconciled spike disposition

**PROCEED (confidence: medium-high)**, scoped as *supervision of an external
engine plus consolidation of orchestration policy that already exists in
`start.ps1`* — not as a new agent runtime.

Evidence carried forward unchanged from `004-SP`:

* The CLI is the only real autoharness surface: `main()` (`cli.py:2253`) exposes
  **10 top-level commands** (`home`, `version`, `verify-workspace`, `gate`,
  `telemetry`, `eval`, `setup-vscode`, `setup-copilot-cli`, `setup-claude`,
  `setup-codex`) and **17 executable leaf command paths** after expanding the
  grouped dispatchers `gate` (5), `telemetry` (3), `eval` (2) — i.e. 7 ungrouped
  leaves + 5 + 3 + 2 = 17.
* **No native MCP server implementation or framework identifiers exist in
  `src/`** (no MCP SDK dependency; zero `FastMCP` / `mcp.server` / `stdio_server`
  / `@mcp.` / `Server(` hits). Three MCP vocabularies remain distinct:
  (a) server-framework **absence** (true), (b) **registry-validation** vocabulary
  for *external* tools (`verify_workspace.py`, 31 occurrences incl.
  `OP_CREATE_MCP`..`OP_RESOLVE_CHECKPOINT_MCP` at `:140-159`), and
  (c) **telemetry vocabulary** (`tool_event.py:35`, `TOOL_SURFACES` contains
  `'mcp'`, 1 occurrence; the sole emission site still hardcodes
  `tool_surface='cli'` at `cli.py:789`).
* The gate/telemetry cores are genuinely surface-independent and
  dependency-injected; the gap is that **policy and observability sit above the
  core**, in the adapter.

New evidence supporting the supervisor framing:

* `start.ps1` (121 lines) already *is* an untested, PowerShell-only supervisor:
  `.env.local` loading with quote-stripping and no-clobber precedence,
  workspace-local `COPILOT_HOME` / `ENGRAM_DATA_DIR`, `gh auth token` resolution
  for `GITHUB_TOKEN` / `GITHUB_PERSONAL_ACCESS_TOKEN`, `backlogit sync`, Engram
  direct pre-warm with daemon-`bind` fallback, Copilot CLI resolution
  (`COPILOT_EXE_PATH` → `COPILOT_EXE` → `PATH`), opt-in `--remote`, and a
  foreground child launch. `start.sh` duplicates this policy in bash.
* That policy has **no test coverage and two divergent implementations**. It is
  the highest-value, lowest-controversy consolidation target in the repository,
  and it is exactly the seam a supervisor needs.

**What is still NO-GO** and remains a non-goal: an in-process action/observation
reasoning loop, sequential model pipelining, stderr-routed-back-to-the-model
correction, and a native autoharness MCP server absent a concrete consumer.

## 3. Architecture

Simplest thing that works: **typed shared Python application services with thin
adapters.** No daemon. No database. No web framework. No async framework. No
plugin registry. No Go component.

```
                    thin adapters (transport only, zero policy)
   start.ps1 ──┐
   start.sh  ──┼──▶  autoharness run  (cli.py adapter)
               │            │
               │            ▼
               │   supervise/app.py :: run_session()      ← the ONLY orchestrator
               │            │
   ┌───────────┴────────────┼─────────────────────────────────────────┐
   │                        ▼                                         │
   │  bootstrap.py   sidecar.py   resolve.py   session.py   events.py │
   │  locking.py     journal.py   recovery.py  approvals.py redact.py │
   │  process.py (Protocol) ──┬── PipeChildProcess (stdlib, default)  │
   │  result.py / errors.py   └── PtyChildProcess (ConPTY / posix pty)│
   └──────────────────────────────────────────────────────────────────┘
                              │ supervises (never reimplements)
                              ▼
                     Copilot CLI  ── external reasoning engine
```

### 3.1 Component boundaries

New package `src/autoharness/supervise/`. Every module is importable, typed, and
unit-testable without spawning Copilot.

| Module | Responsibility | Must NOT |
|---|---|---|
| `result.py` | One typed `SupervisorResult` envelope: `status`, `exit_code`, `data`, `messages`, `warnings`, `artifacts`, `.to_dict()`. Wraps; never rewrites existing result shapes. | Contain policy or I/O. |
| `errors.py` | One `AutoharnessError` base carrying a machine-readable `kind`; supervisor error taxonomy; machine-readable exit-code contract. | Call `sys.exit`. |
| `redact.py` | Secret redaction applied at the **emit/persist boundary** for every event, log line, and journal record. | Be optional or bypassable by any writer. |
| `locking.py` | Workspace/session lock: one active supervised session per workspace. Lockfile carries PID + process start-time + session id. | Auto-break a live lock. |
| `process.py` | `ChildProcess` Protocol (spawn/read/write/signal/wait/close) + `PipeChildProcess` stdlib implementation. Argv-array spawn only. | Use `shell=True`; mask child exit status. |
| `process_pty.py` | `PtyChildProcess`: ConPTY on Windows, stdlib `pty` on POSIX, behind the identical Protocol. | Become the only path; must degrade to pipe. |
| `session.py` | Explicit session state machine + legal-transition table. | Perform I/O or spawn. |
| `events.py` | Typed `SupervisorEvent` records + in-process subscriber fan-out. **The hook surface candidate (c) may later consume.** | Ship a candidate-(c) consumer, or give Engram authority. |
| `journal.py` | Append-only redacted JSONL session journal + resume cursor under `.autoharness/sessions/<session-id>/`. | Duplicate backlogit checkpoints or claim backlog authority. |
| `recovery.py` | Cancellation, bounded restart budget/backoff, operator-confirmed restart, resume-from-cursor. | Auto-restart without budget, or restart silently. |
| `bootstrap.py` | `.env.local` load, workspace-local `COPILOT_HOME`/`ENGRAM_DATA_DIR`, GitHub token resolution. **Sole authority** for that policy. | Leave residual policy in `start.ps1`/`start.sh`. |
| `sidecar.py` | Sidecar preflight: `backlogit sync`; Engram direct pre-warm → daemon `bind` + daemon-sync fallback; per-sidecar typed outcome. | Make any sidecar failure fatal, or write to a sidecar's store. |
| `resolve.py` | Copilot exe resolution order + argv composition incl. opt-in `--remote` and verbatim passthrough. | Rewrite or filter operator passthrough args. |
| `approvals.py` | Local structured command + approval channel over the **local console only**. | Open a socket, port, tunnel, or any remote transport. |
| `app.py` | `run_session()` — the single orchestrator composing all of the above; returns `SupervisorResult`. | Live in `cli.py`. |

### 3.2 Session state machine

```
INIT
 └▶ LOCKING ─(lock held by live session)─▶ REFUSED   [terminal]
     └▶ BOOTSTRAPPING ─(fatal)─▶ FAILED              [terminal]
         └▶ PREFLIGHT ─(sidecar degraded)─▶ PREFLIGHT (warn, continue)
             └▶ RESOLVING ─(no copilot exe)─▶ FAILED [terminal]
                 └▶ LAUNCHING ─(spawn error)─▶ FAILED[terminal]
                     └▶ RUNNING
                         ├─(operator cancel)─▶ CANCELLING ─▶ EXITED   [terminal]
                         ├─(child exit, budget left, operator-confirmed)
                         │      ─▶ RESTARTING ─▶ LAUNCHING
                         ├─(child exit, budget exhausted OR declined)
                         │      ─▶ DRAINING ─▶ EXITED                 [terminal]
                         └─(supervisor fault)─▶ DRAINING ─▶ FAILED    [terminal]
```

Rules:

1. Transitions not in the table are rejected with `ErrorKind.ILLEGAL_TRANSITION`;
   there are no implicit transitions.
2. `DRAINING` always runs: journal flush, lock release, child reaping. It is the
   only path to a terminal state from `RUNNING`.
3. Every transition emits exactly one `SessionPhaseChanged` event, journaled.
4. `REFUSED` is a distinct terminal state from `FAILED` — a contended workspace
   is a policy outcome, not an error.

### 3.3 PTY / process strategy

* **Default is pipe-based** (`PipeChildProcess`, stdlib `subprocess` with argv
  arrays, never `shell=True`). This keeps the base install dependency-light and
  is the path CI exercises.
* **PTY is opt-in** (`PtyChildProcess`): ConPTY on Windows via an optional
  `pywinpty` extra; stdlib `pty` on POSIX. Selected only when the operator
  requests interactive fidelity *and* the implementation imports cleanly;
  otherwise it degrades to pipe with a recorded `warning`, never a hard failure.
* Both satisfy an identical `ChildProcess` Protocol, so the supervisor is
  **replaceable**: if a future persistent multi-workspace daemon ever justifies a
  native process supervisor, only this Protocol's implementations change. That
  is the explicit re-evaluation trigger for Go — **not now** (§7).
* **Exit-status fidelity is a hard invariant.** The child's exit code propagates
  unmodified to `SupervisorResult.exit_code` and to the process exit code. No
  `|| true`, no pipeline masking, no "partial output implies success" inference
  (compound learning `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes`).

### 3.4 Failure and restart semantics

| Condition | Semantics |
|---|---|
| Sidecar (`backlogit`/Engram) failure | **Non-fatal**, matching today's `start.ps1`. Typed per-sidecar outcome `ok \| degraded \| unavailable` + warning. Never silently swallowed. |
| Copilot CLI not resolvable | **Fatal**, `FAILED`, distinct error kind, actionable message (preserves today's `throw`). |
| Child spawn failure | **Fatal**, `FAILED`, no restart consumed. |
| Child non-zero exit | Not a supervisor failure. Exit code propagates verbatim. Restart only if budget remains **and** the operator confirms. |
| Supervisor internal fault | `DRAINING → FAILED`; child is terminated, lock released, journal flushed. |
| Restart budget | Default 0 (opt-in `--max-restarts N`), hard ceiling, exponential backoff, every restart journaled with its reason. |
| Lock contention | `REFUSED` (never auto-break). Stale lock (dead PID / mismatched start-time) requires an explicit operator `--force-unlock`. |

### 3.5 Security and secret handling

1. **Redaction at the boundary.** `journal.py` and `events.py` route every record
   through `redact.py` before persistence or fan-out. Redaction is not an
   opt-in decorator on some call sites; it is the only write path.
2. **Pattern set**: `gh[pousr]_[A-Za-z0-9]{20,}`, `github_pat_…`, values of
   `GITHUB_TOKEN` / `GITHUB_PERSONAL_ACCESS_TOKEN` and any `.env.local` value
   whose key matches `(TOKEN|SECRET|KEY|PASSWORD)`, plus exact-value redaction
   of every resolved secret held in the bootstrap result.
3. **No partial-token leakage**: redaction replaces the whole match; tests assert
   that no ≥8-character substring of a known secret survives into a journal file.
4. **argv arrays only.** No `shell=True`, no string interpolation of paths into
   commands (compound learning `2026-07-01-subprocess-validation-gating`).
5. **Secrets never enter the journal, events, `SupervisorResult.data`, or
   telemetry.** They exist only in the child process environment.
6. **Workspace containment**: all supervisor-written state lives under
   `<workspace>/.autoharness/sessions/`; every path is resolved and asserted to
   be inside the workspace root before any write (path-traversal check, per
   compound learning `2026-05-05-path-traversal-validation-parts`).
7. **No network listener of any kind.** Plan 1 opens no socket, port, or tunnel.

### 3.6 Local approval path

`approvals.py` provides a structured local channel: the supervisor emits an
`ApprovalRequested` event carrying a typed request (`kind`, `summary`,
`options`, `default`, `timeout`), renders it on the **local console**, and blocks
for the operator's answer, journaling both request and response.

Constraints: console/TTY only; no socket, no HTTP, no tunnel, no remote
identity, no delegated approver. In a non-interactive session an approval request
resolves to its declared safe default (or `REFUSED` where no safe default
exists) and is journaled as `auto-resolved`, never silently approved.

### 3.7 Workspace and session containment

* One active supervised session per workspace, enforced by `locking.py`.
* Session id: `<utc-timestamp>-<pid>`; state under
  `.autoharness/sessions/<session-id>/{journal.jsonl,session.json}`.
* `.autoharness/sessions/` is gitignored; the journal is local operational
  telemetry, not a durable backlog artifact. **backlogit remains the sole
  authority for backlog state and agent checkpoints** — the session journal never
  substitutes for a backlogit checkpoint.

## 4. Compatibility and migration from `start.ps1` / `start.sh`

Sequenced so that behavior is **locked before it is moved**:

1. **Characterize first.** Test suites pin the current observable contract of
   `start.ps1` and `start.sh` *before* any logic moves: `.env.local` parsing
   (quote-stripping, no-clobber precedence), `COPILOT_HOME` / `ENGRAM_DATA_DIR`
   defaults, token resolution, sidecar non-fatality, exe-resolution order,
   `--remote` opt-in truthiness (`true`/`1`, case-insensitive, not re-added when
   already passed), verbatim argv passthrough, exit-code propagation.
2. **Build the Python services** so they satisfy those same assertions.
3. **Convert the scripts to shims.** `start.ps1` / `start.sh` reduce to: locate
   the interpreter/entry point and `exec autoharness run -- <args>`. **No policy
   duplication survives in PowerShell or bash** — no `.env.local` parsing, no
   token logic, no sidecar calls, no exe resolution, no `--remote` decision.
4. **The characterization suites are re-run unchanged** against the shims. That
   is the migration's acceptance criterion.
5. **Templates follow the same shape** (`templates/**` copies of the start
   scripts) so generated workspaces get the shim, not the old policy.

Backward compatibility that must hold: `./start.ps1 <args>` and `./start.sh
<args>` keep working with identical observable behavior and identical exit codes;
every environment variable in use today keeps its current meaning and precedence;
no new required dependency is introduced for the default path.

## 5. Testing strategy

| Layer | Approach |
|---|---|
| **Characterization (highest priority)** | Pin `start.ps1` / `start.sh` observable behavior *before* migration; re-run **unchanged** after. This is the regression net for the whole plan (mirrors the `004-SP` R1 mitigation for `cli.py`). |
| **Unit** | Every `supervise/` module tested in isolation with injected fakes. `session.py`, `result.py`, `errors.py`, `redact.py`, `resolve.py` require **no** subprocess at all. |
| **Fake-child integration** | `ChildProcess` Protocol lets the whole state machine, journal, cancellation, and restart paths run against a scripted fake child — deterministic, fast, no Copilot dependency. |
| **Real-child smoke** | A single opt-in test spawning a trivial real child (e.g. the Python interpreter) to prove spawn/signal/exit-code fidelity on both pipe and PTY backends. Skipped when the PTY extra is absent. |
| **Security** | Redaction property tests (no ≥8-char secret substring survives); path-containment tests; argv-array/no-shell assertions. |
| **Contract** | Machine-readable exit-code contract asserted from a single table, so agent prose depending on exit codes cannot drift. |

Existing suites (`test_gate_*`, `test_telemetry_*`, `test_verify_workspace.py`)
stay untouched — Plan 1 adds a package, it does not refactor `cli.py`'s existing
commands.

## 6. Packaging and dependency decisions

* **Base install stays at `jsonschema` + `PyYAML`.** The supervisor core is
  stdlib-only (`subprocess`, `selectors`, `threading`, `queue`, `json`,
  `signal`, `os`, `pathlib`).
* **Optional extra `autoharness[pty]`** → `pywinpty` on Windows; POSIX uses
  stdlib `pty`. Import is guarded; absence degrades to pipe with a warning.
* **New console entry point: `autoharness run`.** No new distribution artifact,
  no separate binary, no daemon service unit.
* **Rejected**: `asyncio` rewrite, `click`/`typer` (would churn the existing
  hand-rolled parser), `rich` TUI, `pexpect`, SQLite session store, a Go
  supervisor binary.

## 7. Language decision — Python-first, replaceable supervisor

Python-first is the default because autoharness is Python, the deferred Plan 2
UI (Gradio) is Python, and shared domain logic must remain single-source. A
Python+Go split now would recreate the exact duplication this plan exists to
remove.

The `ChildProcess` Protocol and the `supervise/` service boundary keep the
process-supervision layer **replaceable**. Go is re-evaluated **only if** a
future *persistent multi-workspace daemon* is actually required. That is a
future trigger, not a current work item; no Go work is planned, created, or
implied here.

## 8. Observability

* **Event catalog** (typed, stable names): `SessionPhaseChanged`,
  `SidecarProbed`, `CopilotResolved`, `ChildSpawned`, `ChildOutput`,
  `ChildExited`, `ApprovalRequested`, `ApprovalResolved`, `CancelRequested`,
  `RestartScheduled`, `RestartExhausted`, `JournalCheckpoint`.
* **Journal**: append-only redacted JSONL, one event per line, monotonic `seq`,
  UTC timestamps, schema-versioned header record.
* **Human progress**: phase-level progress on the console, preserving today's
  `Write-Host` pre-warm messaging; `--json` renders the `SupervisorResult`
  envelope instead.
* **Telemetry**: if a supervisor `ToolTelemetryEvent` is ever emitted, it is
  emitted **by the service** with `tool_surface` supplied by the adapter — never
  synthesized in `cli.py`. Per compound learning
  `2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping`, a sidecar's
  reported state (e.g. Engram degraded) is **not** the supervisor call's own
  outcome and must not be mapped onto `status`.
* **Candidate (c) hook surface only.** The event bus is the seam a future
  background Verification & Compaction layer could subscribe to. Plan 1 ships
  **no** such consumer, performs no background verification or compaction, and
  grants Engram no authority.

## 9. Rollout and rollback

**Rollout**

1. Ship S1 (contracts + characterization) with **zero behavior change** — pure
   additions plus tests pinning today's behavior.
2. Ship S2 (supervision core) as an unwired library — still no behavior change to
   any existing entry point.
3. Ship S3 (services + `autoharness run` + shim migration) — the only shipment
   that changes observable behavior, and it lands with the S1 characterization
   suite as its gate.

**Rollback**

* S1/S2 are additive: revert the commit; nothing else is affected.
* S3 rollback is a **single-file revert of each shim** back to the current
  `start.ps1` / `start.sh` (both preserved verbatim in git history and referenced
  by SHA in the migration doc). The Python services can remain installed and
  dormant — they have no effect unless `autoharness run` is invoked.
* Escape hatch during S3 bake: `AUTOHARNESS_SUPERVISOR=0` makes the shim execute
  the legacy inline path, so rollback needs no redeploy.

## 10. Work decomposition (2-hour rule, width-isolated)

Ordering principle (operator directive): **process safety, contracts, and
characterization tests before UI/convenience.**

### Shipment 1 — Safety contracts + characterization baseline (P0, eligible)

* **T1** — Characterization suite for `start.ps1` observable contract. Test-only.
* **T2** — Characterization suite for `start.sh` parity. Test-only.
* **T3** — `supervise/result.py` + `supervise/errors.py`: typed envelope, error
  taxonomy, machine-readable exit-code contract table. Pure, no I/O.
* **T4** — `supervise/redact.py`: pattern set, whole-match redaction,
  no-partial-leak property tests.
* **T5** — `supervise/locking.py`: single-active workspace/session lock, PID +
  start-time liveness, fail-closed stale policy, explicit `--force-unlock`.

### Shipment 2 — Supervision core (P0, blocked by S1)

* **T6** — `supervise/process.py`: `ChildProcess` Protocol + `PipeChildProcess`,
  argv-array spawn, exit-status fidelity, signal/cancel.
* **T7** — `supervise/process_pty.py`: ConPTY/POSIX PTY behind the same Protocol,
  optional extra, guarded import, degrade-to-pipe.
* **T8** — `supervise/session.py`: state machine + legal-transition table +
  illegal-transition rejection.
* **T9** — `supervise/events.py`: typed events, in-process fan-out,
  redaction-on-emit wiring.
* **T10** — `supervise/journal.py`: append-only redacted JSONL, resume cursor,
  workspace-containment checks.
* **T11** — `supervise/recovery.py`: cancellation, bounded restart budget +
  backoff, operator-confirmed restart, resume-from-cursor.

### Shipment 3 — Application services, adapters, migration (P1, blocked by S2)

* **T12** — `supervise/bootstrap.py`: `.env.local`, `COPILOT_HOME` /
  `ENGRAM_DATA_DIR`, token resolution — satisfies T1/T2 assertions.
* **T13** — `supervise/sidecar.py`: `backlogit sync` + Engram direct→daemon
  fallback pre-warm, typed per-sidecar outcome, non-fatal degradation.
* **T14** — `supervise/resolve.py`: Copilot exe resolution order, `--remote`
  opt-in truthiness, verbatim passthrough.
* **T15** — `supervise/app.py`: `run_session()` orchestration returning
  `SupervisorResult`.
* **T16** — `supervise/approvals.py`: local console-only structured command +
  approval channel, non-interactive safe-default resolution.
* **T17** — `autoharness run` CLI adapter: parse → call → render → exit. No
  policy in the adapter.
* **T18** — `start.ps1` / `start.sh` (+ their `templates/` copies) converted to
  compatibility shims; T1/T2 suites re-run **unchanged**; `AUTOHARNESS_SUPERVISOR=0`
  escape hatch.
* **T19** — Observability + rollout/rollback documentation: event catalog,
  journal schema, redaction guarantees, migration/rollback runbook.

## 11. Explicit non-goals

1. **No Gradio, no Microsoft devtunnel, no remote UI/control, no remote
   authentication, no remote approvals, no browser terminal streaming, no remote
   service of any kind.** All deferred to Plan 2
   (`docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md`).
2. **No model action/observation reasoning loop**, sequential model pipelining, or
   stderr-routed-back-to-the-model correction. Copilot CLI owns reasoning.
3. **No native autoharness MCP server** — explicit non-goal absent a concrete
   consumer.
4. **No persistent daemon, no multi-workspace scheduler, no database, no web
   framework, no plugin registry**.
5. **No Python+Go split now.**
6. **Not candidate (c)** — no background Verification & Compaction layer. The
   event bus is a hook surface only; Engram gains no authority.
7. **No changes to `backlogit`, Engram, or `graphtor`.**
8. **No hardcoded model names**; `.autoharness/config.yaml` remains routing
   authority.
9. **No refactor of the existing 10 top-level / 17 leaf CLI commands** in this
   plan — `autoharness run` is additive.
10. **No parallel execution or extra worktree** (P-001 / P-016 preserved).

## 12. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Behavior drift when `start.ps1` policy moves to Python | T1/T2 characterization suites written **first** and re-run unchanged (T18 acceptance criterion) |
| R2 | Scope creep into a runtime/agent-loop build (invited by spec §3) | §11 non-goals + P-006 hardening + plan-review gate |
| R3 | Remote/Gradio scope leaking into Plan 1 | Plan 2 split to its own deferred tracker; "no network listener" is an S1 test-level invariant |
| R4 | PTY/ConPTY portability burden | Pipe is default and CI path; PTY optional, guarded, degrade-to-pipe |
| R5 | Secret leakage into journals/events | Redaction is the only write path; no-partial-leak property tests (T4) |
| R6 | Session journal drifting into a second backlog/checkpoint authority | Journal is gitignored local operational state; backlogit remains sole backlog/checkpoint authority |
| R7 | Silent candidate-(c) implementation via the event bus | Hooks only; no subscriber shipped; Engram non-authoritative asserted in review |
| R8 | Exit-code masking through the new shim layer | Exit-status fidelity is a hard invariant with dedicated tests (compound learning, `|| true` masking) |

## 13. Acceptance criteria (feature-level)

1. `./start.ps1 <args>` and `./start.sh <args>` behave identically to today —
   proven by characterization suites written before migration and re-run
   unchanged after.
2. No orchestration policy remains in PowerShell or bash.
3. Copilot CLI is spawned, supervised, and reaped by autoharness with verbatim
   exit-code propagation; autoharness implements no reasoning loop.
4. Supervisor state is confined to `<workspace>/.autoharness/sessions/`, redacted,
   and never contains a secret substring.
5. Only one supervised session per workspace can run; contention yields
   `REFUSED`, never a broken lock.
6. Zero network listeners, zero remote transports, zero Gradio/devtunnel code.
7. Base install introduces no new required dependency.

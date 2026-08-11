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
  foreground child launch.
* **CORRECTED 2026-08-11 (F17, ruling 4).** The earlier claim that `start.sh`
  "duplicates this policy in bash" was **factually wrong and is withdrawn**. The
  two scripts do not implement the same policy at different fidelities; they
  implement **different, smaller and larger, policies**. `start.sh` (80 lines)
  implements only five dimensions: `.env.local` parsing, a workspace-local
  `COPILOT_HOME` default, an **unguarded** `export GITHUB_TOKEN="$(gh auth token)"`,
  Copilot executable resolution, and `exec "$copilot_exe" "$@"` at line 66. It
  **does not** set `ENGRAM_DATA_DIR` (the line exists but is commented out), does
  **not** handle `GITHUB_PERSONAL_ACCESS_TOKEN`, has **no** `COPILOT_USE_REMOTE` /
  `--remote` logic, and runs **neither** `backlogit sync` **nor** any Engram
  pre-warm. `start.ps1:65` conversely assigns the PAT **unguarded** while its
  `GITHUB_TOKEN` assignment sits in a guarded, non-fatal `try/catch` — so even
  the shared dimension is not shared behaviour.
* Two consequences follow, and both are load-bearing. **(a)** Characterization
  (T1/T2) pins **each script's own contract**, asserting `start.sh`'s four
  absences **as absences**; a parity assertion would have been unsatisfiable, and
  writing one is what F17 caught. **(b)** Convergence is therefore a **deliberate
  behaviour change on POSIX**, owned by Shipment 3, not a free side effect of
  consolidation.
* The policy nonetheless has **no test coverage** in either implementation, which
  is the actual justification for this work: it is the highest-value,
  lowest-controversy consolidation target in the repository, and exactly the seam
  a supervisor needs.

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
   │  process.py (Protocol) ──┬── InheritStdio (DEFAULT, TTY-attached)│
   │  contracts.py            ├── PtyChildProcess (opt-in capture)    │
   │  result.py / errors.py   └── PipeChildProcess (tests/non-interactive)│
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
| `contracts.py` | **Shared core contracts (F19, ruling 2): the `SupervisorEvent` type catalog, the approval request/response types, and the enumerated GATED-ACTION catalog (F32/F33, ruling 1).** Definition lives here so no runtime component depends on the event bus or the approval channel merely to *name* what it emits. **This row previously also credited F21; that attribution is WITHDRAWN** — placing the types here fixed definition ORDERING only, and never created the caller F21 was about. | Contain transport, delivery, or I/O — definition only. |
| `process.py` | `ChildProcess` Protocol (spawn/read/write/signal/wait/close) + **`InheritStdioChildProcess` (the DEFAULT, preserving TTY attachment)** and `PipeChildProcess` (tests / explicitly non-interactive runs). Argv-array spawn only. | Use `shell=True`; mask child exit status; make pipes the interactive default. |
| `process_pty.py` | `PtyChildProcess`: ConPTY on Windows, stdlib `pty` on POSIX, behind the identical Protocol. Opt-in, adds **output capture** without losing terminal semantics. | Become the only path; **must degrade to inherited stdio, never to pipes**. |
| `session.py` | Explicit session state machine + legal-transition table. | Perform I/O or spawn. |
| `events.py` | In-process subscriber fan-out and **delivery** of `SupervisorEvent` records whose **types are defined upstream in `contracts.py`** (F19). Also owns the H7 anti-drift guard, which is **behavioural** (a `sys.addaudithook` socket interception with mandatory positive controls over `socket.create_server`, `socketserver.TCPServer`, `asyncio.start_server` and `http.server.HTTPServer`), with the lexical denylist demoted to a fast pre-filter (F28, ruling 10). **The hook surface candidate (c) may later consume.** | Define event types; ship a candidate-(c) consumer; give Engram authority; rely on lexical checks alone. |
| `journal.py` | Append-only redacted JSONL session journal + resume cursor under `.autoharness/sessions/<session-id>/`. **Owns the ignore rule for its own state (F24, ruling 6):** on journal-root creation it idempotently ensures `.autoharness/sessions/` is git-ignored, verified by a test asserting a fresh session directory is *actually* ignored. | Duplicate backlogit checkpoints or claim backlog authority; assume some other surface installs its ignore rule. |
| `recovery.py` | Cancellation, bounded restart budget/backoff, operator-confirmed restart, resume-from-cursor. | Auto-restart without budget, or restart silently. |
| `bootstrap.py` | `.env.local` load, workspace-local `COPILOT_HOME`/`ENGRAM_DATA_DIR`, GitHub token resolution. **Sole authority** for that policy. | Leave residual policy in `start.ps1`/`start.sh`. |
| `sidecar.py` | Sidecar preflight: `backlogit sync`; Engram direct pre-warm → daemon `bind` + daemon-sync fallback; per-sidecar typed outcome. | Make any sidecar failure fatal, or write to a sidecar's store. |
| `resolve.py` | Copilot exe resolution order + argv composition incl. opt-in `--remote` and verbatim passthrough. | Rewrite or filter operator passthrough args. |
| `approvals.py` | Local structured command + approval channel over the **local console only**. | Open a socket, port, tunnel, or any remote transport. |
| `app.py` | `run_session()` — the single orchestrator composing all of the above; returns `SupervisorResult`. | Live in `cli.py`. |

### 3.2 Session state machine

```
INIT
 └▶ LOCKING ─(lock held by live session)─▶ REFUSED   [terminal, NO lock acquired]
     └▶ BOOTSTRAPPING ─(fatal)───────┐
         └▶ PREFLIGHT ─(sidecar degraded)─▶ PREFLIGHT (warn, continue)
             └▶ RESOLVING ─(no copilot exe)─┤
                 └▶ LAUNCHING ─(spawn error)──┤
                     └▶ RUNNING                │
                         ├─(child exit, budget left, operator-confirmed)
                         │      ─▶ RESTARTING ─▶ LAUNCHING
                         ├─(child exit, budget exhausted OR declined)
                         │                       │
                         └─(supervisor fault)────┤
                                                 │
   (operator cancel, legal from ANY of          │
    BOOTSTRAPPING/PREFLIGHT/RESOLVING/          │
    LAUNCHING/RUNNING/RESTARTING)               │
                         └─▶ CANCELLING ────────┤
                                                 │
                                                 ▼
                                             DRAINING
                                    (journal flush, lock release,
                                     child reaping — ALWAYS)
                                                 │
                          ┌──────────────────────┼────────────┐
                          ▼                      ▼                ▼
                       EXITED                 FAILED          CANCELLED
                     [terminal]             [terminal]        [terminal]
```

**CORRECTED 2026-08-11 (F18 + F22 + F23, ruling 1).** The previous diagram routed
`CANCELLING → EXITED` directly, contradicting its own Rule 2, and sent three
post-`LOCKING` failure edges (`BOOTSTRAPPING`/`RESOLVING`/`LAUNCHING` → `FAILED`)
straight to a terminal state without ever passing through `DRAINING` — where lock
release lives. Because §3.4 never auto-breaks a stale lock, the most likely
first-run failure of all (no Copilot executable on `PATH`) would have left the
operator **locked out of their own workspace**, with every retry returning
`REFUSED`. The diagram above eliminates that class of defect structurally rather
than by adding cases.

Rules:

1. Transitions not in the table are rejected with `ErrorKind.ILLEGAL_TRANSITION`;
   there are no implicit transitions.
2. **`DRAINING` is the SOLE TERMINAL GATEWAY.** Every path from any state at or
   after `LOCKING` to any terminal state passes through `DRAINING`, which always
   runs journal flush, **lock release**, and child reaping. There is no
   `CANCELLING → EXITED` edge and no direct failure edge to `FAILED`. The single
   exception is `REFUSED`, which is reachable only from `LOCKING` **before** a
   lock is acquired, so there is nothing to release. Release is **idempotent**, so
   a fault inside `DRAINING` cannot double-release.
3. **Operator cancellation is legal from EVERY post-`LOCKING` phase**, not only
   from `RUNNING`. This is what makes 119.006-T's "cancel during launch" case
   satisfiable; under the previous table it could only ever be refused.
4. Rules 2 and 3 are verified by a **graph-property test**, not by a
   hand-enumerated list of paths: for every state and every edge, assert that no
   terminal state is reachable except through `DRAINING`. The defect this prevents
   is precisely an edge nobody thought to enumerate, so enumeration cannot be the
   control.
5. Every transition emits exactly one `SessionPhaseChanged` event, journaled.
   The event **type** is defined in the shared core (`supervise/contracts.py`,
   T3), not in the event bus — see F19, ruling 2.
6. `REFUSED` is a distinct terminal state from `FAILED` — a contended workspace
   is a policy outcome, not an error.

### 3.3 PTY / process strategy

* **CORRECTED 2026-08-11 (F29, ruling 11).** The default was previously specified
  as redirected pipes. That is **not** the contract being migrated: `start.sh:66`
  is `exec "$copilot_exe" "$@"` and `start.ps1` inherits terminal handles, so the
  child today runs **TTY-attached**. `subprocess.PIPE` makes stdin/stdout/stderr
  non-TTY, changing interactive prompts, input handling, colour and buffering — a
  migration could have passed every assertion while breaking ordinary interactive
  Copilot sessions, contradicting the zero-observable-change premise of S1/S2.
* **Default is inherited stdio** (`InheritStdioChildProcess`, stdlib `subprocess`
  with argv arrays, never `shell=True`, child file handles inherited). This
  preserves terminal attachment exactly as today and keeps the base install
  dependency-light. T1/T2 characterize TTY attachment explicitly.
* `PipeChildProcess` is **retained but demoted** to tests and explicitly
  non-interactive runs. It is never selected implicitly for an interactive
  session.
* **PTY is opt-in** (`PtyChildProcess`) and exists to add **output capture**
  without losing terminal semantics: ConPTY on Windows via an optional
  `pywinpty` extra; stdlib `pty` on POSIX. Selected only when the operator
  requests capture *and* the implementation imports cleanly; otherwise it
  **degrades to inherited stdio — never to pipes** — with a recorded `warning`.
  A missing optional extra therefore costs *capture*, never *terminal
  attachment*.
* Under inherited stdio the supervisor cannot observe child output, so
  `journal.py` (T10) writes an explicit `ChildOutputUnavailable(reason=
  "inherited-stdio")` marker rather than silently journaling an empty stream. The
  absence of capture is a **declared degradation**, not an invisible one.
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
| Copilot CLI not resolvable | **Fatal**, `DRAINING → FAILED` (lock released on the way out — F22), distinct error kind, actionable message (preserves today's `throw`). |
| Child spawn failure | **Fatal**, `DRAINING → FAILED` (lock released — F22), no restart consumed. |
| Bootstrap fatal | **Fatal**, `DRAINING → FAILED` (lock released — F22). |
| Operator cancel (any post-`LOCKING` phase) | `CANCELLING → DRAINING → CANCELLED` (lock released — F18/F23). |
| Child non-zero exit | Not a supervisor failure. Exit code propagates verbatim. Restart only if budget remains **and** the operator confirms. |
| Supervisor internal fault | `DRAINING → FAILED`; child is terminated, lock released, journal flushed. |
| Restart budget | Default 0 (opt-in `--max-restarts N`), hard ceiling, exponential backoff, every restart journaled with its reason. |
| Lock contention | `REFUSED` (never auto-break). Stale lock (dead PID / mismatched start-time) requires an explicit operator `--force-unlock`, which §10/T17 obliges the CLI to actually expose (F25) and T6/118.006-T to implement, including rejection of a **recycled PID** whose start-time does not match. |
| Lock acquisition | **Atomic** — `O_CREAT\|O_EXCL` or an OS advisory lock (F27). Check-then-write is **prohibited**: two supervisors starting simultaneously could both observe no live lock and both write it, producing exactly the concurrent sessions the module exists to prevent. The PID + start-time record is **diagnosis of staleness only**, never the acquisition mechanism, and contention is proven by a **parallel-contender** test, not a sequential one. |

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

**Runtime wiring is mandatory and structural (F32/F33, ruling 1).** An earlier
revision claimed F21 was discharged by moving the approval *types* into
`contracts.py`. **That claim was false and is withdrawn.** Contract placement
fixed F19, a definition-ordering defect. F21 was a *wiring* defect, and moving a
type definition upstream does not create a caller: T16 still had **zero** reverse
dependencies, and T15 — the single orchestrator — did not reference approvals at
all, so the fail-closed guarantee above remained fully omissible from a shipped
supervisor while every task passed.

The fix is structural, in two halves:

* **Graph half.** The `T16 → T15` dependency is **reversed** to `T15 → T16`, so
  approvals sit *on* the critical path and the runtime chain
  T15 → T17 → T18 → T19 can no longer be satisfied with approvals unstarted.
* **Test half.** T15 takes the approval service as a **required parameter with no
  default** (no `None`-accepting overload, no module-level fallback); the set of
  **gated actions** is declared once in `contracts.py` and T15's dispatch must
  cover it exhaustively; and a spy service asserts every gated action raised an
  `ApprovalRequested` and consumed a decision **before** the side effect is
  observable.

**Negative controls are mandatory**, because the failure mode here is a check
that passes without exercising anything: a `DENY` must suppress the side effect
and resolve the session to `REFUSED`; an approval service that *raises* must fail
closed; and a deliberately-unwired fixture orchestrator must be **rejected** by
the same assertions. A non-interactive end-to-end run asserts the safe-default /
`REFUSED` resolution **at the T15 level**, not only inside T16's own unit tests —
F21's whole point was that a guarantee proven only in an unreachable module is
not a guarantee.

### 3.7 Workspace and session containment

* One active supervised session per workspace, enforced by `locking.py`.
* Session id: `<utc-timestamp>-<pid>`; state under
  `.autoharness/sessions/<session-id>/{journal.jsonl,session.json}`.
* `.autoharness/sessions/` is gitignored **by `journal.py` itself** — corrected
  2026-08-11 under F24/ruling 6. The earlier plan assumed a "gitignore template"
  in `templates/`; **no such artifact exists**, and workspace ignore rules are
  handled procedurally by the install-harness skill, which merely *confirms* an
  existing `.gitignore` covers `.env.local`. The requirement was therefore
  satisfiable **by vacuity** — "met" by finding nothing to change — and it failed
  **silently**, leaving every supervised session's JSONL git-tracked in generated
  workspaces. Core now ensures the rule and a `git check-ignore` test enforces it,
  so the H6 containment property is *enforced* rather than asserted. The journal is
  local operational telemetry, not a durable backlog artifact. **backlogit remains the sole
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

* The **childless product umbrella** `117-F` stays `queued` for the entire chain
  and is closed engine-natively as a member of the final shipment `129-S`. It
  has no children, so no single shipment close can promote, archive, or orphan
  any Plan-1 work through it (H10.5).
* Each shipment's own ROOT covering feature (`118-F`/`119-F`/`120-F`) is fully
  covered by its own manifest, so a close affects only that shipment's scope.
  Rolling back one shipment never disturbs a sibling's parentage.
* S1/S2 are additive: revert the commit; nothing else is affected.
* S3 rollback is a **single-file revert of each shim** back to the current
  `start.ps1` / `start.sh` (both preserved verbatim in git history and referenced
  by SHA in the migration doc). The Python services can remain installed and
  dormant — they have no effect unless `autoharness run` is invoked.
* **WITHDRAWN 2026-08-11 (F16, ruling 3).** An earlier draft offered an escape
  hatch during S3 bake — `AUTOHARNESS_SUPERVISOR=0` making the shim execute the
  legacy inline path so rollback needed no redeploy. That requirement was
  **mutually exclusive with DoD #2**: retaining an executable legacy inline path
  inside the shim *is* orchestration policy remaining in PowerShell and bash. The
  contradiction is resolved **in favour of DoD #2**, which is preserved intact.
* There is therefore **no environment-variable escape hatch**. Rollback is a
  single-file revert per shim to the git-SHA-preserved pre-migration script, and
  it **requires a redeploy**. That cost is accepted deliberately: it buys the
  guarantee that no orchestration policy survives in shell, which is the entire
  point of the migration. A test asserts that no shim contains an
  environment-variable branch into any legacy path, so the hatch cannot
  reappear silently.

## 10. Work decomposition (2-hour rule, width-isolated)

Ordering principle (operator directive): **process safety, contracts, and
characterization tests before UI/convenience.**

### Shipment 1 — Safety contracts + characterization baseline (P0, eligible)

> **Manifest contract (H10.5 — supersedes H10.4):** each shipment owns its own
> **ROOT** covering feature that is **fully covered by** and an **explicit member
> of** that shipment's manifest, listed **first**:
>
> | Shipment | Covering feature (ROOT) | Tasks |
> |---|---|---|
> | `127-S` (S1) | `118-F` | `118.001-T`…`118.005-T` |
> | `128-S` (S2) | `119-F` | `119.001-T`…`119.006-T` |
> | `129-S` (S3) | `120-F` | `120.001-T`…`120.008-T` (+ `117-F` last) |
>
> Full coverage means `returnUnreleasedFeatureItems` has nothing to return, so
> **no** `parent_id` is ever cleared; ROOT placement means `featureScopeRoots`
> cannot walk out of one shipment's scope into a sibling's. The product umbrella
> `117-F` is **childless** and grouped to these features by non-hierarchical
> `related_to` links only. No close requires `adopt_item` or any post-close
> repair. See H10.5 in the hardening doc for the engine-level rationale and the
> executed closure proof.

* **T1** — Characterization suite for `start.ps1` observable contract. Test-only.
* **T2** — Characterization suite for **`start.sh`'s own five-dimension contract**,
  with its four absences (no `ENGRAM_DATA_DIR`, no PAT, no `--remote`, no sidecars)
  asserted **as absences**. Not a parity suite — see §5 (F17, ruling 4). Test-only.
* **T3** — `supervise/result.py` + `supervise/errors.py` **+ `supervise/contracts.py`**:
  typed envelope, error taxonomy, machine-readable exit-code contract table, and
  the shared **event type catalog + approval request/response contracts** that T8,
  T9 and T16 all bind to (F19/F21, ruling 2). Pure, no I/O.
* **T4** — `supervise/redact.py`: pattern set, whole-match redaction,
  no-partial-leak property tests.
* **T5** — `supervise/locking.py`: single-active workspace/session lock with
  **atomic acquisition** (`O_CREAT|O_EXCL` or OS advisory lock; check-then-write
  prohibited), **idempotent release**, and a **parallel-contender** test suite
  (F27, ruling 9). PID + start-time is staleness *diagnosis* only.
* **T6a (118.006-T)** — stale-lock lifecycle, `--force-unlock` semantics, and
  **cleanup mutual exclusion (F31, ruling 3): force-unlock must ACQUIRE the same
  OS-backed primitive as acquisition and hold it across BOTH inspection and
  removal as one critical section, re-reading the holder record inside it and
  REFUSING on any mismatch. Ruling 9 made *acquisition* atomic; it did not make
  *cleanup* safe — a diagnosed-stale holder can be replaced by a live acquirer
  before the delete lands, so an unchecked delete removes a LIVE holder through
  the very remedy meant to restore the invariant. A real concurrent
  contender-vs-cleanup race test is required, with a positive control proving it
  fails against a compare-free delete.**
  Also covers **recycled-PID rejection**; split from T5 to stay inside the 2-hour box.
* **T7a (118.007-T)** — amend **P-015** (policy template, Ship agent template,
  shipment-reconcile skill, compound close-path doc) so the permitted close
  operation and the executable evidence agree, via a machine-checkable
  *fully-covered-root* exception **quantified over every feature member**
  (F26, ruling 8; **corrected by F30, ruling 2**, which withdrew the
  single-covering-feature "and nothing else" wording that would have rejected
  `129-S` and its verified-childless terminal umbrella `117-F`). Childlessness
  must be **positively verified**, never inferred, since it makes full coverage
  vacuously true. Must land before **any** close.

### Shipment 2 — Supervision core (P0, blocked by S1)

* **T6** — `supervise/process.py`: `ChildProcess` Protocol + **`InheritStdioChildProcess`
  as the DEFAULT** (TTY-attached, F29) with `PipeChildProcess` retained for tests
  and non-interactive runs; argv-array spawn, exit-status fidelity, signal/cancel.
* **T7** — `supervise/process_pty.py`: ConPTY/POSIX PTY behind the same Protocol,
  optional extra, guarded import, **degrade to inherited stdio — never to pipes**.
* **T8** — `supervise/session.py`: state machine + legal-transition table with
  **`DRAINING` as the sole terminal gateway** and cancel legal from every
  post-`LOCKING` phase, enforced by a **graph-property test**; illegal-transition
  rejection (F18/F22/F23, ruling 1).
* **T9** — `supervise/events.py`: fan-out and delivery of the **contracts.py**
  event catalog, redaction-on-emit wiring, and the **behavioural** H7 listener
  guard with mandatory positive controls (F19 + F28).
* **T10** — `supervise/journal.py`: append-only redacted JSONL, resume cursor,
  workspace-containment checks, **core-owned session ignore rule with a
  `git check-ignore` test** (F24), and an explicit `ChildOutputUnavailable`
  marker under inherited stdio (F29).
* **T11** — `supervise/recovery.py`: cancellation, bounded restart budget +
  backoff, operator-confirmed restart, resume-from-cursor.

### Shipment 3 — Application services, adapters, migration (P1, blocked by S2)

* **T12** — `supervise/bootstrap.py`: `.env.local`, `COPILOT_HOME` /
  `ENGRAM_DATA_DIR`, token resolution — satisfies T1/T2 assertions.
* **T13** — `supervise/sidecar.py`: `backlogit sync` + Engram direct→daemon
  fallback pre-warm, typed per-sidecar outcome, non-fatal degradation. **Scope of
  the no-mutation rule is narrowed (F20, ruling 5):** no *domain/authority*
  mutation (no artifact/shipment/checkpoint writes, no Engram authority records,
  no decision authority), while `backlogit sync` and Engram pre-warm/bind are
  **explicitly permitted** as derived-index maintenance creating no domain facts.
  The previous blanket "backlogit and graphtor are not mutated" phrasing
  contradicted this task's own mandate and is withdrawn.
* **T14** — `supervise/resolve.py`: Copilot exe resolution order, `--remote`
  opt-in truthiness, verbatim passthrough.
* **T15** — `supervise/app.py`: `run_session()` orchestration returning
  `SupervisorResult`. **Depends on T16 and must route every gated action through
  it (F32/F33, ruling 1)**, with the approval service as a required no-default
  parameter and an exhaustive gated-action catalog.
* **T16** — `supervise/approvals.py`: local console-only structured command +
  approval channel **implementing the upstream `contracts.py` approval contract**
  (F19, ruling 2), non-interactive safe-default resolution. **The former claim
  that upstream contract placement alone made the channel non-omissible is
  WITHDRAWN (F32/F33)** — it did not, because a type definition creates no
  caller. What makes it non-omissible is the **reversed `T15 → T16` edge**, which
  puts approvals on the runtime critical path.
* **T17** — `autoharness run` CLI adapter: parse → call → render → exit. No
  policy in the adapter. **Defines the complete, stable option contract (F25,
  ruling 7)** and is the only surface exposing it — including `--force-unlock`
  (the sole reachable remedy for a stranded lock, compounding F22) and
  `--max-restarts N` (default 0). Every option is tested both for **parsing** and
  for **forwarding**, since parsing alone was never evidence of reachability.
* **T18** — `start.ps1` / `start.sh` (+ their `templates/` copies) converted to
  compatibility shims; T1/T2 suites re-run **unchanged**, including the TTY
  attachment case (F29). **No `AUTOHARNESS_SUPERVISOR=0` escape hatch** —
  withdrawn under ruling 3 to preserve DoD #2 (see §9); rollback is a single-file
  revert requiring redeploy.
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
| R4 | PTY/ConPTY portability burden | **Inherited stdio** is default and CI path (F29); PTY optional, guarded, degrades to inherited stdio never to pipes |
| R5 | Secret leakage into journals/events | Redaction is the only write path; no-partial-leak property tests (T4) |
| R6 | Session journal drifting into a second backlog/checkpoint authority | Journal is gitignored local operational state — **the ignore rule installed and tested by `journal.py` itself** (F24), not assumed from a nonexistent template; backlogit remains sole backlog/checkpoint authority |
| R7 | Silent candidate-(c) implementation via the event bus | Hooks only; no subscriber shipped; Engram non-authoritative asserted in review; **listener drift caught behaviourally by an audit hook with positive controls** (F28) rather than by a bypassable lexical denylist |
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

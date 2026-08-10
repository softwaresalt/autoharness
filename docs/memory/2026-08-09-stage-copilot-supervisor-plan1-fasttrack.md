---
session_id: stage-2026-08-09-plan1-copilot-supervisor-fasttrack
agent: stage
date: 2026-08-09
branch: chore/spike-unified-surfaces-20260809
pr: 325
tracker: 34D50F2D
supersedes: docs/memory/2026-08-09-stage-34d50f2d-candidate-a-composability-spike.md
status: complete
---

# Stage session memory — Plan 1 fast-track (local Copilot CLI supervisor / control plane)

## Operator product decision (authoritative)

The operator issued a new authoritative product decision extending the completed
`34D50F2D` candidate-(a) composability spike and open PR #325:

1. **FAST-TRACK Plan 1** — autoharness becomes a **local Copilot CLI supervisor /
   control-plane runtime** for long-horizon workloads, preserving Copilot CLI as the
   reasoning/agent execution engine. All local runtime components are in scope;
   everything Gradio / devtunnel / remote UI / remote control / remote authentication /
   remote approvals / browser terminal streaming / remote services is **excluded**.
2. **DEFER Plan 2** — Gradio + Microsoft devtunnel + remote-control services move to a
   later autoharness version with their own design/operational plan and tracking item,
   and **no implementation feature, tasks, or shipment now**.

## The bright line that resolved the spike

> **Supervising an external agent runtime is IN SCOPE.
> Implementing a new agent runtime is OUT OF SCOPE.**

The original spike returned `CONDITIONAL PROCEED` against spec §3 read as an
**in-process action/observation execution engine**. That reading **remains NO-GO** and
was not overturned — it was *narrowed*. Supervising an external Copilot child process is
a different activity, and it is exactly the "consolidation of logic that already exists"
condition the spike attached: `start.ps1` / `start.sh` already perform bootstrap, sidecar
preflight, resolution, and launch. Plan 1 consolidates duplicated policy rather than
inventing a new capability. Disposition reconciled to **PROCEED** under the clarified
scope.

### Two corrections PR #325 required

1. **MCP parity is NOT recommended.** A native autoharness MCP server remains an
   **explicit non-goal** absent a concrete consumer.
2. **Process-supervision scope is NOT wholly rejected.** The NO-GO narrows to a model
   reasoning loop, sequential model pipelining, and stderr-to-model routing.

### Evidence preserved verbatim (must not regress)

* **10 top-level commands / 17 executable leaf command paths** (`main()` at
  `cli.py:2253`); 7 ungrouped leaves + `gate` 5 + `telemetry` 3 + `eval` 2 = 17. The
  retracted "11 commands" figure is **not** reinstated.
* **Three distinct MCP vocabularies**: (a) server-framework **absence** in `src/`
  (no MCP SDK; zero `FastMCP` / `mcp.server` / `stdio_server` / `@mcp.` / `Server(`
  hits) — the supported narrow claim; (b) registry-validation vocabulary for *external*
  tools (`verify_workspace.py`, 31 occurrences, `OP_CREATE_MCP`..`OP_RESOLVE_CHECKPOINT_MCP`
  at `:140-159`); (c) telemetry vocabulary (`tool_event.py:35`, `TOOL_SURFACES` contains
  `'mcp'`, 1 occurrence; sole emission site hardcodes `tool_surface='cli'` at
  `cli.py:789`).

## Plan 1 — artifacts and gates

| Artifact | Path | Verdict |
|---|---|---|
| Implementation plan | `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md` | authored |
| P-006 hardening | `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md` | **HARDENED** (H1–H10) |
| Plan review gate | `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md` | **PASS**, 0 P0 / 0 P1 outstanding, 1 of 3 cycles |

Hardening themes: H1 characterize-before-migrate (hard ordering constraint), H2
fail-closed invariant table, H3 exit-status fidelity, H4 subprocess safety (argv-array
only, no `shell=True`), H5 single redaction choke point, H6 authority containment, H7
anti-drift (no bind/listen, web/tunnel import ban), H8 per-task de-risking for the four
riskiest tasks, H9 backward-compatibility contract, H10 shipment gating.

## Architecture decided

New package `src/autoharness/supervise/`: `result.py`, `errors.py`, `redact.py`,
`locking.py`, `process.py` (ChildProcess Protocol + PipeChildProcess default),
`process_pty.py` (ConPTY / POSIX, optional `pywinpty` extra, degrade-to-pipe),
`session.py`, `events.py`, `journal.py`, `recovery.py`, `bootstrap.py`, `sidecar.py`,
`resolve.py`, `approvals.py`, `app.py` (`run_session()` — the **only** orchestrator).
The sole adapter is `autoharness run` in `cli.py`; `start.ps1` / `start.sh` become thin
compatibility shims with **no surviving policy duplication**. Base install stays stdlib +
existing `jsonschema` / `PyYAML`.

**Session state machine:**
`INIT → LOCKING → BOOTSTRAPPING → PREFLIGHT → RESOLVING → LAUNCHING → RUNNING →
{CANCELLING | RESTARTING | DRAINING} → {EXITED | FAILED | REFUSED}`.
`REFUSED` (lock contention) is a distinct terminal state from `FAILED`; `DRAINING` is the
only path from `RUNNING` to a terminal state.

**Language decision:** Python-first, **no Python+Go split now**. Process-supervisor
interfaces stay replaceable; Go is reevaluated only if a future persistent multi-workspace
daemon requires it.

**Authority boundaries (unchanged):** Engram is a read-only memory sidecar with no
authority; backlogit is the sole owner of backlog items and agent checkpoints (the
supervisor session journal is gitignored local operational state and is **never** a
checkpoint); graphtor owns docs retrieval; autoharness owns lifecycle/policy/supervision
only; `.autoharness/config.yaml` remains the model-routing authority.

## Harvested backlog (Plan 1 only)

**Covering feature `117-F`** — "Local Copilot CLI supervisor / control-plane runtime
(Plan 1, fast-track)" with 19 width-isolated sub-2h tasks `117.001-T`…`117.019-T`, each
carrying **two independent axes** (`size` + `complexity`) as structured fields *and* as
labeled prose, plus **27 `blocks` dependency edges**.

**Serial shipment chain (only the first is eligible):**

| Order | ID | Scope | Priority | Items |
|---|---|---|---|---|
| 1 (cursor) | `124-S` | S1 safety contracts + characterization baseline — zero behavior change | critical (P0) | `117-F`, `117.002-T`, `117.001-T`, `117.003-T`, `117.005-T`, `117.004-T` |
| 2 | `125-S` | S2 supervision core — unwired library | critical (P0) | `117.006-T`…`117.011-T` |
| 3 | `126-S` | S3 application services, adapters, `start.ps1`/`start.sh` migration — the only behavior-changing shipment | high (P1) | `117.012-T`…`117.019-T` |

`125-S` **blocks-on** `124-S`; `126-S` **blocks-on** `125-S`. Ordering deliberately
front-loads process safety, typed contracts, and characterization tests **before** any
adapter or convenience surface.

### Task ↔ plan map (note: the first five task IDs are not in T-order)

| Plan | ID | Focus | Shipment | Size | Complexity |
|---|---|---|---|---|---|
| T1 | `117.001-T` | `start.ps1` characterization suite | S1 | M | medium |
| T3 | `117.002-T` | `result.py` + `errors.py` contracts | S1 | S | low |
| T2 | `117.003-T` | `start.sh` characterization suite | S1 | S | low |
| T5 | `117.004-T` | `locking.py` | S1 | M | medium |
| T4 | `117.005-T` | `redact.py` | S1 | S | medium |
| T6 | `117.006-T` | `process.py` Protocol + Pipe backend | S2 | M | medium |
| T7 | `117.007-T` | `process_pty.py` ConPTY/POSIX | S2 | M | high |
| T8 | `117.008-T` | `session.py` state machine | S2 | M | medium |
| T9 | `117.009-T` | `events.py` event bus | S2 | S | low |
| T10 | `117.010-T` | `journal.py` | S2 | M | medium |
| T11 | `117.011-T` | `recovery.py` | S2 | M | high |
| T12 | `117.012-T` | `bootstrap.py` | S3 | M | medium |
| T13 | `117.013-T` | `sidecar.py` | S3 | M | medium |
| T14 | `117.014-T` | `resolve.py` | S3 | S | low |
| T15 | `117.015-T` | `app.py` `run_session()` | S3 | M | high |
| T16 | `117.016-T` | `approvals.py` (console-only) | S3 | M | medium |
| T17 | `117.017-T` | `autoharness run` CLI adapter | S3 | S | medium |
| T18 | `117.018-T` | `start.ps1`/`start.sh` → shims | S3 | M | high |
| T19 | `117.019-T` | observability + rollout/rollback docs | S3 | S | low |

## Plan 2 — deferred

* Design doc: `docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md`
  (remote threat model with 6 assets / 6 adversary classes / T1–T10 threats; Entra ID
  authentication; 4-tier authorization with a local-only privileged tier; cryptographic
  workspace binding; two-channel streaming/control protocol; remote approvals; devtunnel
  lifecycle with crash-safe teardown; multi-user/session concerns; optional-extra
  deployment; rollback; 7 open questions).
* Dedicated living tracker: **stash `04AFF97B`** (kind `feature`, priority `low`, marked
  DEFERRED).
* **No implementation feature, tasks, or shipment exist**, and Plan 2 is **not** a Plan 1
  dependency and must not be added to Plan 1's dependency graph or shipment chain.

## Candidate (c) boundary

Background **Verification & Compaction** remains a later, distinct, unselected capability
and is the reason `34D50F2D` **stays ACTIVE**. Plan 1 exposes the typed event bus
(`117.009-T`) and session journal (`117.010-T`) as hook surfaces a future candidate-(c)
layer could consume, but Plan 1 must not silently implement candidate (c) and must not
make Engram authoritative — enforced as H7 anti-drift with a test asserting `supervise/`
opens no socket, binds no port, and imports no web/tunnel framework.

## Non-goals reaffirmed

* Native autoharness MCP server (explicit non-goal absent a concrete consumer).
* Any model action/observation reasoning loop, model pipelining, or stderr-to-model routing.
* Any remote surface, socket, port, tunnel, or web framework in `supervise/`.
* Daemon, database, or framework overreach; no Python+Go split.
* Candidate (c) implementation.

## Decisions worth carrying forward

* Characterize-before-migrate is a **hard ordering constraint**, not a preference: the
  characterization suites are re-run byte-identical by `117.018-T`, and any required
  assertion change escalates as an operator product decision.
* Exit-status fidelity is a hard invariant across the pipe backend, the PTY backend, the
  orchestrator, the CLI adapter, and both shims.
* The restart budget defaults to **0** so the default path is simply cancel-and-drain;
  the complex restart path is opt-in and separately testable.
* PTY is opt-in and degrades to pipe with a recorded warning — never a silent
  substitution, never a hard failure.

## Session boundaries

Stage-scoped planning only: **no** source/template/schema/config implementation, **no**
branch or worktree creation, **no** commit/push/PR mutation, **no** shipment claim, and
**no** Ship execution. All changes are left **uncommitted** for the Orchestrator.

## Next steps for Ship

1. Claim `124-S` (S1) — the only eligible cursor. `125-S` and `126-S` are blocked.
2. Honor H1: land the characterization suites before any policy moves to Python.
3. Do not begin S3 migration until S1 and S2 are released.

---
title: "Plan Hardening (P-006) — Local Copilot CLI Supervisor / Control Plane (Plan 1)"
date: "2026-08-09"
description: "P-006 plan hardening for the Plan 1 local Copilot CLI supervisor/control-plane plan. Enumerates blast-radius controls, fail-closed invariants, backward-compatibility guarantees, and de-risking for the high-complexity tasks."
doc_type: plan-hardening
source: docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md
plan_id: "PLAN-1"
stash_ids: ["34D50F2D"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md"
  - ".backlogit/archive/004-SP.md"
tags: ["P-006", "hardening", "supervisor", "copilot-cli", "34D50F2D", "candidate-a"]
---

# Plan Hardening (P-006) — Local Copilot CLI Supervisor / Control Plane

## Blast-radius summary — hardening REQUIRED

The plan rewrites **`start.ps1` and `start.sh`**, which are the entry point every
operator and every generated workspace uses to launch the agent runtime, plus
their `templates/` counterparts (so the blast radius extends to every future
installed workspace), plus packaging (`pyproject.toml` entry points and an
optional dependency extra). A defect here does not degrade a feature — it
prevents the harness from starting at all, in this repository *and* in every
downstream workspace generated from the templates. It additionally introduces
child-process spawning and secret-bearing log persistence, which are security
surfaces the product does not currently have.

`Requires plan hardening: yes.`

## H1 — Characterize-before-migrate is a hard ordering constraint, not a preference

**Risk.** The single largest failure mode is silently changing `start.ps1`
semantics while "porting" them. The current behavior is subtle: no-clobber
`.env.local` precedence, single-pair quote stripping, `--remote` added only when
`COPILOT_USE_REMOTE` is `true`/`1` **and** the operator did not already pass
`--remote`, non-fatal sidecar failures, and `throw` on unresolvable Copilot.

**Hardening.**

1. T1/T2 (characterization) are **P0 and land in Shipment 1**, before any service
   exists. Shipment 2 and 3 are blocked on Shipment 1 by explicit `blocks` edges.
2. T18 (shim conversion) has an acceptance criterion that T1/T2 are re-run
   **byte-identical** — no test may be edited to accommodate the migration. If a
   characterization assertion must change, that is a **product decision requiring
   operator sign-off**, not an implementation detail.
3. The characterization suites must assert the *observable contract* (env state,
   argv handed to the child, exit code), not internal script structure, so the
   shims can satisfy them.

## H2 — Fail-closed invariants

| Invariant | Fail-closed behavior |
|---|---|
| Workspace lock contention | `REFUSED` terminal state. **Never** auto-break a lock whose PID is live. Stale lock (dead PID or start-time mismatch) still requires explicit `--force-unlock`. |
| Path containment | Every supervisor write path is resolved and asserted inside the workspace root **before** the write. A path escaping the root aborts the session; it is never "clamped" or silently rewritten. |
| Redaction | If the redactor cannot process a record, the record is **dropped with a warning**, never written raw. Redaction failure never degrades to pass-through. |
| Illegal state transition | Raises `ErrorKind.ILLEGAL_TRANSITION`; the session drains and fails. There is no permissive fallback transition. |
| Non-interactive approval | Resolves to a declared safe default, or `REFUSED` where none exists. **Never auto-approves.** |
| Restart budget | Default **0**. Restart requires both remaining budget and explicit operator confirmation. Budget exhaustion drains to a terminal state; it never loops. |
| PTY unavailable | Degrades to pipe with a recorded warning. A *requested-and-unavailable* PTY never silently becomes an interactive-looking pipe without that warning. |
| Copilot CLI unresolvable | Fatal `FAILED` with the current actionable message. Never falls back to a guessed path. |

## H3 — Exit-status fidelity (regression-class defect already in the corpus)

Compound learning `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes`
records this exact class of bug in this repository's shell scripts: a trailing
`|| true` discarded a pipeline's failure while partial stdout still implied
success.

**Hardening.** The child's exit code propagates verbatim through
`ChildProcess.wait()` → `SupervisorResult.exit_code` → process exit. Explicitly
prohibited: `|| true` / `-ErrorAction SilentlyContinue` around the child launch
in the shims, inferring success from non-empty output, and remapping a non-zero
child exit into a supervisor-level status. A dedicated test asserts a table of
child exit codes (0, 1, 2, 42, 130) round-trips unchanged through both the pipe
and PTY backends **and** through both shims.

## H4 — Subprocess safety

Compound learning `2026-07-01-subprocess-validation-gating` documents the
injection surface from interpolating paths into command strings.

**Hardening.** Argv-array spawn only; `shell=True` is prohibited and asserted
against in tests. Operator passthrough args are forwarded **verbatim as a list**
and never re-parsed, re-quoted, joined, or filtered. Sidecar invocations
(`backlogit sync`, `engram sync/bind`) likewise use argv arrays with resolved
absolute executable paths.

## H5 — Secret handling is a single choke point

**Risk.** Three writers (events, journal, console) could each grow their own
redaction, and one of them will forget.

**Hardening.** There is exactly **one** persistence/emit path, and it runs the
redactor. `journal.py` and `events.py` must not expose a raw-write API. Property
tests assert that for a generated secret `S`, no substring of `S` of length ≥ 8
appears in any produced journal file, event payload, or `SupervisorResult`.
Resolved secret *values* (not just patterns) are registered with the redactor at
bootstrap, so a token that does not match any regex is still redacted.

## H6 — Authority containment (backlogit / Engram / graphtor / config)

**Risk.** A session journal with checkpoints and a resume cursor looks a lot like
a backlog checkpoint store, and an event bus looks a lot like a place to let
Engram drive.

**Hardening.**

1. The session journal is **gitignored local operational state**. It must not be
   referenced as a backlog artifact, must not be read by any agent-recovery
   protocol, and must not be presented as a checkpoint. **backlogit remains the
   sole authority for backlog items and agent checkpoints.**
2. Engram stays **read-only with no execution or mutation authority**. No
   supervisor decision (restart, approval, cancellation, phase transition) may
   read from or depend on Engram.
3. graphtor-docs is untouched.
4. `.autoharness/config.yaml` remains the model-routing authority. The supervisor
   does not select, name, or hardcode models; it does not read model routing at
   all in Plan 1.
5. Plan-review must explicitly confirm all four.

## H7 — Anti-drift guard against candidate (c) and against Plan 2

**Risk.** The event bus is precisely the hook a background Verification &
Compaction layer (candidate (c)) needs, and "just add a small web view" is one
import away from Plan 2.

**Hardening.**

1. Plan 1 ships **zero** event subscribers beyond the journal and console
   renderer. No background thread performs verification, summarization, or
   compaction.
2. A test asserts the supervisor opens **no listening socket** (no `bind`/`listen`
   in `supervise/`), and a repository-level check asserts `supervise/` imports
   nothing from `gradio`, `fastapi`, `flask`, `uvicorn`, `aiohttp`, or a devtunnel
   client.
3. Candidate (c) remains a separate, later capability with its own
   spike → impl-plan → plan-review → harvest cycle; `34D50F2D` stays ACTIVE as its
   living tracker.

## H8 — De-risking the high-complexity tasks

Three tasks carry `complexity: high`. Each gets an explicit de-risking control so
"high complexity" does not silently mean "> 2 hours".

| Task | Why high | De-risking control |
|---|---|---|
| **T7** — PTY/ConPTY backend | Platform-divergent, optional dependency, hardest to test | Bounded by the `ChildProcess` Protocol already fixed by T6. Scope is *one* class. Not on the default path. If `pywinpty` integration exceeds the box, the fallback is to ship pipe-only and re-file PTY as a follow-up — the plan degrades gracefully. |
| **T11** — cancellation / restart / resume | Concurrency + partial state | State machine (T8) and journal (T10) are already fixed contracts. Restart budget defaults to **0**, so the default path is "cancel and drain" — the complex restart path is opt-in and separately testable against the fake child. |
| **T15** — `run_session()` orchestration | Integrates everything | Pure composition: every dependency (T6, T8, T10, T12, T13, T14) is already implemented and independently tested. T15 adds no new algorithm; if it grows one, that is a decomposition failure and the task must be split. |
| **T18** — shim migration | Highest blast radius | Gated by the unchanged T1/T2 suites, plus the `AUTOHARNESS_SUPERVISOR=0` escape hatch and a single-file-revert rollback. |

## H9 — Backward-compatibility guarantees (explicit contract)

1. `./start.ps1 <args>` and `./start.sh <args>` continue to work with identical
   observable behavior and identical exit codes.
2. Every currently-honored environment variable keeps its meaning **and its
   precedence**: `COPILOT_HOME`, `ENGRAM_DATA_DIR`, `GITHUB_TOKEN`,
   `GITHUB_PERSONAL_ACCESS_TOKEN`, `COPILOT_EXE_PATH`, `COPILOT_EXE`,
   `COPILOT_USE_REMOTE`, and every `.env.local` key.
3. The base install gains **no new required dependency**; PTY is an optional
   extra.
4. The existing 10 top-level / 17 leaf CLI commands are unchanged. `autoharness
   run` is purely additive.
5. Workspaces generated from `templates/` receive the shim; no generated
   workspace is left with orphaned inline policy.
6. Rollback is a single-file revert per shim, with the Python package able to
   remain installed and dormant.

## H10 — Shipment gating

The three shipments form a **strict serial chain** with explicit `blocks` edges:
`S1 → S2 → S3`. Only S1 is eligible at harvest time.

* **S1** must land with **zero observable behavior change** — pure additions plus
  characterization tests. If S1 changes any existing behavior, it is
  mis-decomposed.
* **S2** must land as an **unwired library** — nothing in `cli.py`, `start.ps1`,
  or `start.sh` calls it yet.
* **S3** is the only shipment permitted to change observable behavior, and it
  lands behind the S1 characterization gate plus the `AUTOHARNESS_SUPERVISOR=0`
  escape hatch.

## Hardening verdict

**HARDENED.** H1–H10 are bound into the plan's task acceptance criteria, the
shipment sequencing, and the non-goals. Proceed to plan-review.

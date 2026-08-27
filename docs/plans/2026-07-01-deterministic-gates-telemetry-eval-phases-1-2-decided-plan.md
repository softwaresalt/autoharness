---
source: docs/plans/2026-07-01-deterministic-gates-telemetry-eval-phases-1-2-decided-plan.md
title: "Deterministic Validation Gates + Telemetry & Evaluation Engine (Phases 1-2) — decided plan"
doc_type: decided-plan
status: shipped
created: 2026-07-01
supersedes:
  - docs/archive/plans/2026-06-30-deterministic-validation-gates-phase1-plan.md
  - docs/archive/plans/2026-07-01-telemetry-eval-phase2-plan.md
---

# Decided Plan: Deterministic Validation Gates + Telemetry & Evaluation Engine (Phases 1-2)

**Outcome:** Epic `93E85A44` reached a reviewed two-phase design for deterministic
validation gates plus telemetry/evaluation. The Phase 1 plan-review verdict is
**PASS**, P0 = 0, P1 = 0; the Phase 2 / feature `051-F` plan-review verdict is
**PASS**, P0 = 0, P1 = 0. No PR number, merge commit, or other complete shipment
evidence is recorded in these plan artifacts for the combined Phase 1/2 scope, so
this decided-plan records the result as **reviewed**, not shipped. This replaces
the verbose originals, archived for traceability at `docs/archive/plans/2026-06-30-deterministic-validation-gates-phase1-plan.md` and
`docs/archive/plans/2026-07-01-telemetry-eval-phase2-plan.md`.

**Delivery status (verified against the backlog at compaction time):** shipped — `051-F` confirmed complete in `.backlogit/`.

## Decisions

1. **Deliver both phases as self-contained CLI capabilities plus documented runtime
   integration contracts, not as in-process loop interception.** Phase 1 becomes
   `autoharness gate check`; Phase 2 becomes `autoharness telemetry record` and
   later `autoharness eval`. Rationale: the autoharness CLI is an install/tune
   tool, not the live agent execution host.
2. **Keep the gate layer additive, optional, and atomic.** `lifecycle_hooks` /
   `telemetry` config is a no-op when absent, but when enabled Phase 1 blocks task
   completion if any matched file fails a gate. Enforcement is absolute by default,
   with operator-only `--force`.
3. **Keep subprocess execution safe and reviewable.** Gate commands run as
   argv-array subprocesses with timeout kill, injection-safe interpolation, a
   shared typed result object, and a 3-failure block/requeue path aligned to the
   circuit breaker contract.
4. **Make Phase 2's first shipment the telemetry-capture core only.** The
   surviving first boundary is U1–U7: typed epoch model, telemetry config,
   repo-local SQLite sink, emit-only JSONL sink, `telemetry record` CLI,
   gitignore/template activation, and documentation. Eval, reviewer scoring, and
   pre-execution sizing remain later shipments.
5. **Keep telemetry repo-local and fail-open.** The SQLite database lives under
   `.autoharness/metrics/`; JSONL emission is observational and must never block
   task completion. A broken sink warns and continues rather than becoming a
   completion gate.
6. **Preserve hard external boundaries.** JSONL is emit-only at the
   agent-engram/docline boundary; the backlogit size writeback is invoke-only; no
   CozoDB schema code, backlogit schema code, or global multi-repo telemetry
   aggregation is added inside autoharness.

## Implementation

### Phase 1 — Deterministic validation gates (8 tasks)

| Task | Scope |
|---|---|
| T1 | `validation_gates` JSON Schema for `lifecycle_hooks` + reserved `telemetry` keys |
| T2 | Config template / loader support so absent blocks remain a no-op |
| T3 | Git-diff discovery utility returning repo-relative normalized paths |
| T4 | Glob matching + cross-platform path normalization |
| T5 | Timeout-bounded argv-array subprocess gate runner |
| T6 | `autoharness gate check --task <id> --base <ref>` CLI aggregation / atomic block |
| T7 | Structured correction feedback, advisory vs absolute enforcement, repeated-failure handling |
| T8 | Integration contract + documentation of the completion-path hook point |

### Phase 2 — Telemetry & evaluation engine (feature `051-F`)

| Unit | Scope | Shipment |
|---|---|---|
| U1 | `ExecutionEpoch` model + four payload classes | A |
| U2 | Telemetry-owned typed config loader | A |
| U3 | Repo-local SQLite sink | A |
| U4 | Emit-only JSONL sink | A |
| U5 | `autoharness telemetry record` CLI + sink dispatch | A |
| U6 | `.autoharness/metrics/` gitignore + config-template activation | A |
| U7 | Telemetry / emission-contract documentation | A |
| U8 | `autoharness eval` frozen-state runner | B |
| U9 | Deterministic reviewer matrix with cited penalties | B |
| U10 | Pre-execution T-shirt sizing via external backlogit CLI | C |

Shipment A is the self-contained capture-core first slice; B depends on A; C is
sequenced last behind the external backlogit dependency.

## Key constraints preserved

- **No-loop caveat:** neither phase may pretend the CLI owns the live agent
  execution loop.
- **Backward compatibility:** Phase 1 extends the existing config family
  additively; Phase 2 activates already-reserved telemetry keys rather than
  inventing a second contract.
- **Atomic gate semantics:** one gate failure blocks completion; advisory mode
  only warns; operator-only `--force` is the bypass.
- **Failure handling:** repeated gate failures escalate to block/requeue after
  three failures; telemetry sinks fail open and never become a completion block.
- **Runtime-artifact hygiene:** `.autoharness/metrics/` and SQLite sidecars must
  be gitignored so emissions never dirty a consumer workspace.
- **Isolation:** the `telemetry/` package stays import-decoupled from `gates/`
  and install/tune modules; sink paths resolve repo-relative with cross-platform
  normalization and WAL/short-lived SQLite connections.
- **External-boundary integrity:** JSONL stops at the file boundary; the sizing
  unit invokes `backlogit update ... --size ...` but never reimplements backlog
  schemas or ingestion paths.

## Rejected alternatives

- **Refactor or intercept a non-existent in-process CLI execution loop** —
  rejected because it misstates where agent execution actually happens.
- **Implement telemetry in Phase 1** — rejected by review and sequencing; Phase 1
  stays a deterministic gate layer, Phase 2 owns measurement.
- **Global / multi-repo telemetry aggregation** — rejected; Phase 2 is explicitly
  repo-local.
- **Cross the external boundaries into agent-engram ingestion or backlogit schema
  work** — rejected to preserve separation of concerns and keep Shipment A tight.

## Review findings that changed the plan

### Phase 1 findings folded in

- Add an explicit negative test that shell metacharacters in `{file_path}` cannot
  inject a second command and that `shell=True` is never used.
- Keep the new `gates/` package import-decoupled from install/tune modules.
- Reuse one typed `GateResult`-style object across runner, aggregation, and
  feedback instead of ad-hoc dicts.
- Ship the config block through templates, not hard-coded config.
- Keep Phase 2 telemetry out of the Phase 1 task set.

### Phase 2 findings folded in

- Add a fail-open sink test so SQLite/JSONL errors do not become completion
  blockers.
- Keep the telemetry package import-decoupled from `gates/` and install/tune.
- Reuse one typed epoch / payload object across sinks and CLI dispatch.
- Put telemetry activation guidance in `harness-config.yaml.tmpl`, not a
  hard-coded config file.
- Add negative checks that no CozoDB or backlogit-schema code is introduced.
- Keep the first shipment at the capture-core boundary only; eval, reviewer
  scoring, and sizing remain later work.

## Rollback

- **Phase 1:** remove or empty the `lifecycle_hooks` block to disable gating with
  no code change.
- **Phase 2:** set `telemetry.mode: none` (or remove the block) to disable
  emission; delete `.autoharness/metrics/` to reset local telemetry data.
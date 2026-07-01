---
title: "Telemetry & Evaluation Engine (Phase 2) — autoharness Implementation Plan"
description: "Phase 2 of the Deterministic Gates, Telemetry & Evaluation Engine design (§4) — autoharness portion only"
source_documents:
  - "docs/design-docs/autoharness-evals-gates-design.md"
  - "docs/plans/2026-06-30-deterministic-validation-gates-phase1-plan.md"
  - "docs/compound/2026-07-01-subprocess-validation-gating.md"
epic: "93E85A44"
feature: "051-F"
tasks:
  - "051.001-T"
  - "051.002-T"
  - "051.003-T"
  - "051.004-T"
  - "051.005-T"
  - "051.006-T"
scope: "autoharness-only (Phase 2)"
tags:
  - "telemetry"
  - "evaluation"
  - "phase-2"
  - "dark-factory"
---

## Problem Frame

Phase 2 of the design doc (§4) makes autoharness measure its own efficiency
("Best Outcome at the Best Price") by capturing high-fidelity execution
telemetry and enabling headless evaluation. It builds on the Phase 1 gate layer
(shipped as the `autoharness gate` CLI + `src/autoharness/gates/` package) whose
gate exit codes become the "Absolute Outcome" payload of an execution epoch.

**Critical architectural caveat (must be respected by every unit — carried
forward from the Phase 1 plan):** autoharness's CLI (`src/autoharness/` —
`cli.py`, `schema_contracts.py`, `verify_workspace.py`, `gates/`) is an
**install/tune tool**, not a live agent execution host. There is **no
in-process execution loop** in this codebase to "wrap" or intercept. The agent
execution loop lives in the harness runtime (Copilot CLI / VS Code /
build-feature skill). Design §4's "wrap the execution loop to log …" therefore
reframes exactly as Phase 1 reframed §3's interceptor:

> Phase 2 delivers telemetry as a **self-contained CLI capability**
> (`autoharness telemetry record …`, `autoharness eval …`) plus a **documented
> emission contract** that the harness runtime invokes at execution boundaries,
> **not** as an in-process interceptor of a loop that does not exist here.

The harness runtime already knows its route configuration, token/COGS/duration,
CLI tools used, and gate exit codes at task-completion time; it hands those to
autoharness through the record command. autoharness owns the **sink** (SQLite +
JSONL) and the **epoch schema**, not the collection of raw runtime signals.

**Forward-compatibility already in place (do not re-invent):**

* `schemas/validation-gates/1.0.0.schema.json` already reserves the `telemetry`
  block keys `mode` (`sqlite`|`none`), `database_path`, and `emit_jsonl`
  ("Phase 1 does not build the telemetry sink; these keys are reserved …").
  Phase 2 **activates** them; it does not add a new top-level config surface.
* `src/autoharness/gates/config.py` already parses and retains the `telemetry`
  dict on `GatesConfig.telemetry`. Phase 2 consumes that mapping through a
  **telemetry-owned** typed loader (no reverse coupling into `gates/`).
* `templates/harness-config.yaml.tmpl` already ships a commented telemetry block
  pointing at `.autoharness/metrics/execution_epochs.db`. Phase 2 documents the
  activation path.

**Runtime-artifact isolation (Phase 1 gitignore learning —
`docs/compound/2026-07-01-subprocess-validation-gating.md`):** Phase 1 established
that tool-generated runtime state under `.autoharness/gates/` and
`.autoharness/staging/` is **gitignored so tool invocations never dirty a
consumer's working tree**. Phase 2 introduces `.autoharness/metrics/`
(the `execution_epochs.db` SQLite file, its `-wal`/`-shm` sidecars, and JSONL
output). This directory **must** be added to `.gitignore` following the same
learning, or every telemetry emission would dirty the target repo.

## Scope Boundaries (non-negotiable)

* **In scope (autoharness):** epoch schema/model; repo-local SQLite sink at
  `.autoharness/metrics/execution_epochs.db` (§6.3); emit-only JSONL output;
  the `autoharness telemetry record` and `autoharness eval` CLI surfaces; the
  deterministic reviewer matrix; the pre-execution sizing decision.
* **Out of scope (external boundary — do NOT implement):**
  * agent-engram / docline CozoDB **telemetry schema and ingestion path** —
    051.006 is **emit-only**; autoharness writes JSONL and stops at the boundary.
  * backlogit `--size` **mutation CLI** — 051.002 depends on it; autoharness
    only *invokes* `backlogit update <task_id> --size <result>`.
  * **Global / multi-repo** telemetry aggregation — §6.3 recommendation is
    keep telemetry **repo-local** for Phase 2. No global DB.

## Requirements Trace (task → unit)

| Source requirement (design §4 / task) | Implementation unit(s) | Shipment |
|---|---|---|
| Execution Epoch emitter — 4 payload classes (051.001) | U1, U5 | A (first) |
| Local SQLite aggregator, repo-local `.db` (051.003, §6.3) | U2, U3 | A (first) |
| JSONL emitter, emit-only (051.006) | U2, U4 | A (first) |
| Sink dispatch / `telemetry record` CLI (051.001 wiring) | U5 | A (first) |
| Runtime-artifact gitignore + config activation (§5, §6.3) | U6 | A (first) |
| Telemetry & emission-contract docs (§4) | U7 | A (first) |
| Headless eval runner `autoharness eval` (051.004) | U8 | B |
| Deterministic reviewer matrix (051.005) | U9 | B |
| Pre-execution T-shirt sizing gate (051.002) | U10 | C |

## Implementation Units

Each unit obeys the 2-hour rule (<3 files, <5 functions, <4 test scenarios),
width isolation (single domain), and produces an atomic verifiable milestone.
Units **U1–U7 constitute the first shipment (A)**; U8–U10 are decomposed here
for sequencing but are **deferred** to later shipments.

### Shipment A — Telemetry-Capture Core (FIRST)

#### U1 — ExecutionEpoch model + four payload classes  *(domain: CLI code)*

* **Changes**: Define the immutable `ExecutionEpoch` dataclass composing the four
  design-§4 payload classes: `RouteConfiguration` (models used),
  `EconomicPayload` (tokens, COGS, duration), `OperationalReality` (CLI tools
  used), `AbsoluteOutcome` (gate exit codes). Provide `to_record()` /
  `from_mapping()` for a stable serialized shape.
* **Files**: `src/autoharness/telemetry/__init__.py`, `src/autoharness/telemetry/epoch.py`.
* **Tests**: (1) construct a full epoch; (2) round-trip `to_record`↔`from_mapping`;
  (3) missing required payload class raises.
* **Posture**: test-first. **Depends on**: none.

#### U2 — TelemetryConfig typed loader  *(domain: config)*

* **Changes**: Telemetry-owned loader that consumes the already-parsed
  `telemetry` mapping (from `GatesConfig.telemetry` or a raw dict) into a typed,
  immutable `TelemetryConfig` (`enabled`, `mode`, `database_path`, `emit_jsonl`).
  Absent/`mode: none` ⇒ disabled (no-op). Repo-relative `database_path` resolved
  against the workspace root. **No import of `gates/` internals** — decoupled per
  Phase 1 review P2-2.
* **Files**: `src/autoharness/telemetry/config.py`.
* **Tests**: (1) absent/`none` ⇒ disabled; (2) `sqlite` + path parsed;
  (3) path resolves repo-relative under workspace root.
* **Posture**: test-first. **Depends on**: none (schema keys already reserved).

#### U3 — SQLite epoch sink (repo-local aggregator, 051.003)  *(domain: CLI code)*

* **Changes**: Create/idempotently migrate the schema in
  `.autoharness/metrics/execution_epochs.db` (parent dirs auto-created); insert one
  row per epoch with columns supporting quantitative metric queries (route, tokens,
  COGS, duration, tools, gate outcome, timestamps). Uses stdlib `sqlite3` only.
* **Files**: `src/autoharness/telemetry/sqlite_sink.py`.
* **Tests**: (1) DB + schema created at repo-relative path; (2) migration idempotent
  (re-open no-op); (3) epoch persisted and queryable back.
* **Posture**: test-first. **Depends on**: U1, U2.

#### U4 — JSONL epoch sink (emit-only, 051.006)  *(domain: CLI code)*

* **Changes**: Append each epoch as **one well-formed JSON object per line** to the
  configured JSONL path (default alongside the DB under `.autoharness/metrics/`).
  **Emit-only** — the CozoDB schema and ingestion are external (agent-engram);
  this unit stops at the file boundary. Stable field contract shared with U1.
* **Files**: `src/autoharness/telemetry/jsonl_sink.py`.
* **Tests**: (1) each line parses as JSON with the contract fields; (2) append
  semantics (existing lines preserved); (3) disabled `emit_jsonl` ⇒ no file write.
* **Posture**: test-first. **Depends on**: U1, U2.

#### U5 — `autoharness telemetry record` CLI subcommand + dispatch  *(domain: CLI code)*

* **Changes**: New `autoharness telemetry record` subcommand — the CLI realization
  of the "emitter" honoring the no-loop caveat. Accepts an epoch payload (JSON via
  `--from-json <path>` or stdin) produced by the harness runtime at execution
  close, loads `TelemetryConfig` (U2), and routes the epoch to every enabled sink
  (SQLite U3 + JSONL U4). Wire into the `if/elif` dispatcher in `cli.py:main()`.
* **Files**: `src/autoharness/telemetry/record.py`, `src/autoharness/cli.py` (wiring only).
* **Tests**: (1) enabled telemetry ⇒ epoch reaches both sinks; (2) disabled
  telemetry ⇒ no-op exit 0; (3) invalid payload ⇒ exit 2 with actionable message.
* **Posture**: test-first. **Depends on**: U3, U4.

#### U6 — Runtime-artifact gitignore + config template activation  *(domain: config/template)*

* **Changes**: (a) Add `.autoharness/metrics/` (plus `*.db-wal`/`*.db-shm`
  sidecars if not already covered) to `.gitignore` — applying the Phase 1
  gitignore learning so telemetry emission never dirties a consumer's tree.
  (b) In `templates/harness-config.yaml.tmpl`, document the telemetry activation
  path (uncomment guidance: `mode: sqlite`, `database_path`, `emit_jsonl: true`).
* **Files**: `.gitignore`, `templates/harness-config.yaml.tmpl`.
* **Tests**: (1) `git check-ignore .autoharness/metrics/execution_epochs.db`
  matches; (2) template resolves with no unresolved `{{VARIABLE}}`; (3) config
  round-trip validates against `validation-gates/1.0.0.schema.json`.
* **Posture**: test-first (gitignore + round-trip). **Depends on**: none.

#### U7 — Telemetry & emission-contract documentation  *(domain: docs)*

* **Changes**: New telemetry reference doc: the epoch schema (4 payload classes),
  the SQLite table shape, the **JSONL emit contract** (fields + one-object-per-line),
  the repo-local `.autoharness/metrics/` layout, and — critically — **where and how
  the harness runtime invokes `autoharness telemetry record`** at execution close
  (the emission contract that substitutes for the non-existent in-process loop).
  Cross-link from getting-started / gates reference. State the external boundary
  (engram ingestion out of scope).
* **Files**: `docs/` (new telemetry reference) + one getting-started xref.
* **Tests**: doc cross-reference integrity (referenced files/commands exist);
  no unresolved template vars.
* **Posture**: characterization/doc. **Depends on**: U1–U6.

### Deferred Units (later shipments — decomposed for sequencing only)

#### U8 — Headless eval runner `autoharness eval` (051.004)  *(Shipment B; domain: CLI code)*

* Runs a **frozen git state** across ≥2 model configurations and records
  comparable baseline epochs via the U1 model + U3 SQLite sink. Reads a config
  matrix; emits one epoch per config run; summarizes comparative metrics.
* **Depends on**: U1, U3 (telemetry core) — hence sequenced after Shipment A.
* Likely 2–3 sub-units at build time (matrix loader; frozen-state runner; summary)
  to hold the 2-hour rule; flagged for re-decomposition at Stage-time for B.

#### U9 — Deterministic reviewer matrix (051.005)  *(Shipment B; domain: CLI/prompt)*

* Headless deterministic grading prompt over the final `git diff`, scoring
  dimensions (Maintainability, Security, …) with **mandatory line-number
  citations for every penalty**. Deterministic (temperature-pinned / seeded)
  so scores are reproducible. Feeds eval scoring (U8).
* **Depends on**: Phase 1 diff surface (`gates/discovery.py`) + U1 epoch outcome.

#### U10 — Pre-execution T-shirt sizing gate (051.002)  *(Shipment C; domain: CLI code)*

* When `task.size == null`, estimate T-shirt complexity via a lightweight model
  and write back through `backlogit update <task_id> --size <result>` (**external
  backlogit mutation CLI** — invoke only; do not implement). Never overwrite an
  existing size.
* **Depends on**: external backlogit `--size` mutation CLI (external dependency)
  — sequenced **last** so the external dependency can land first.

## Dependency Graph (acyclic)

```text
# Shipment A (first) — telemetry-capture core
U1 (epoch model) ─┬─> U3 (sqlite sink) ─┐
U2 (telem config)─┴─> U4 (jsonl sink) ──┼─> U5 (record CLI) ─┐
                                        │                    ├─> U7 (docs)
U6 (gitignore+template) ────────────────┴────────────────────┘

# Later shipments (depend on Shipment A core)
U1, U3 ─> U8 (eval runner)          [Shipment B]
Phase1 diff + U1 ─> U9 (reviewer)   [Shipment B]  (U9 feeds U8 scoring)
external backlogit --size ─> U10    [Shipment C]
```

No cycles. Shipment A is self-contained (no dependency on U8–U10). B depends on
A; C depends on an external dependency, not on A or B.

## Decisions and Rationale

* **Telemetry delivered as `autoharness telemetry record` CLI + emission
  contract**, not an in-process loop interceptor — because no CLI execution loop
  exists (same honest reframing as Phase 1). autoharness owns the epoch schema
  and the sinks; the harness runtime supplies the raw signals.
* **First shipment = capture core (U1–U7 → tasks 051.001 + 051.003 + 051.006)** —
  a self-contained, fully testable "record an epoch to SQLite + JSONL" capability
  with zero external runtime dependency. Eval/reviewer/sizing are deliberately
  excluded from the first boundary because they add model-invocation and
  external-CLI dependencies that exceed a tight, testable first slice
  (honors Phase 1 review P3-1 scope discipline).
* **Repo-local SQLite (§6.3), not global** — telemetry binds to the target repo's
  architecture; global aggregation is explicitly out of scope for Phase 2.
* **JSONL is emit-only (051.006)** — the CozoDB schema + ingestion are an external
  agent-engram boundary; crossing it here would violate the design's strict
  separation of concerns.
* **Telemetry package is import-decoupled from `gates/`** — carries forward Phase 1
  review P2-2 (module-boundary direction) so telemetry and gating evolve
  independently; `TelemetryConfig` consumes a plain mapping.
* **Schema/template already reserve the surface** — Phase 2 activates existing
  reserved keys rather than adding a new config contract, minimizing blast radius.

## Risks and Caveats

* **No-loop framing (highest-signal item):** design §4 says "wrap the execution
  loop"; there is no such loop in this CLI. Implementers MUST build the record
  command + emission contract, not hunt for a loop to patch. This is the single
  most important thing reviewers/implementers must internalize (mirrors Phase 1).
* **Working-tree dirtying:** if `.autoharness/metrics/` is not gitignored (U6),
  every emission dirties the consumer repo — a correctness bug, not cosmetics.
  U6 gitignore test is a hard gate.
* **External-boundary scope bleed:** 051.006 (JSONL) and 051.002 (sizing) invite
  implementing engram ingestion / backlogit `--size`. Both are external; keep the
  autoharness side emit-only / invoke-only.
* **Concurrency on the SQLite file:** parallel emissions could contend; use WAL
  and short-lived connections; sidecar `-wal`/`-shm` files must be gitignored.
* **Cross-platform paths (§6.2):** repo-relative DB/JSONL paths must normalize on
  Windows/Linux; reuse the Phase 1 path-normalization discipline.

## Plan Hardening Signals (REQUIRED)

* **Public API / schema / contract change**: PRESENT — new `autoharness telemetry
  record` (and later `autoharness eval`) CLI subcommands; new JSONL emission
  contract other tools (agent-engram) depend on; new SQLite table shape.
* **Security / auth / permission-sensitive behavior**: PRESENT (lower than Phase 1)
  — U10 invokes an external `backlogit update` subprocess with an interpolated
  `{task_id}`/`{result}` (argv-array, quoted; deferred to Shipment C). Telemetry
  payloads may carry model/cost data written to a repo-local file.
* **Migration / backfill / destructive / irreversible step**: ABSENT — additive,
  optional; DB is created on demand; no migration of existing data.
* **External integration / operator checkpoint / external dependency**: PRESENT —
  emit-only JSONL boundary to agent-engram/docline (051.006); external backlogit
  `--size` mutation CLI (051.002); model invocations in eval/reviewer/sizing.
* **High runtime / rollout / rollback risk**: PRESENT (low-moderate) — telemetry
  sits off the critical path (record is fire-and-forget after task close); a
  broken sink must **fail open** (log + continue), never block task completion.

Conclusion: **Requires plan hardening: yes.**

## Plan Hardening

**Hardening required: YES.** New CLI contract, new external JSONL emission
contract, and a new repo-local SQLite runtime surface justify hardening even
though blast radius is lower than Phase 1 (telemetry is off the completion
critical path).

### Risk triggers and protected invariants

* **Trigger — telemetry must never break task completion.** **Invariant:** a
  failing/misconfigured/absent telemetry sink degrades to **fail-open** (warn +
  continue); `autoharness telemetry record` returning non-zero MUST NOT be
  interpreted by the harness as a completion blocker. Telemetry is observational,
  not a gate.
* **Trigger — runtime artifacts must not dirty the consumer tree.**
  **Invariant:** `.autoharness/metrics/` (DB + `-wal`/`-shm` + JSONL) is
  gitignored (U6); emission never produces a tracked-file diff.
* **Trigger — external-boundary integrity.** **Invariant:** 051.006 writes JSONL
  and stops; no CozoDB code. 051.002 shells `backlogit update` and stops; no
  backlogit schema code.
* **Trigger — public contract stability.** **Invariant:** the JSONL field
  contract and epoch schema are versioned/additive; the config surface reuses the
  already-reserved `telemetry` keys (backward compatible; `mode: none`/absent is a
  no-op).
* **Trigger — subprocess invocation (U10, deferred).** **Invariant:** argv-array
  execution only, `{task_id}`/`{result}` passed as single quoted argv elements,
  no `shell=True` — reuse the Phase 1 A1 control.

### Reinforced instructions and learnings consulted

* `docs/compound/2026-07-01-subprocess-validation-gating.md` — runtime artifacts
  under `.autoharness/` are gitignored so tool invocations never dirty the tree;
  `.autoharness/metrics/` MUST follow the same rule (drives U6).
* Phase 1 plan review **P3-1** — telemetry is Phase 2 (this feature); keep the
  eval runner / reviewer matrix out of the FIRST shipment if they exceed a tight,
  testable boundary — honored: first shipment is capture-core only.
* Phase 1 plan review **P2-2** — keep the new package import-decoupled from
  install/tune and gates modules (drives U2's decoupling).
* `circuit-breaker.instructions.md` — sink failures are transient/observational;
  fail-open + optional cooldown, never spin blocking a completion.
* `coding-discipline.instructions.md` — simplicity/surgical: small isolated
  `telemetry/` package, stdlib `sqlite3`, no new deps.
* No existing `docs/compound/` entry covers telemetry epoch emission — capture a
  compound learning at operational closure.

### Risky actions (ProposedAction / ActionRisk / ActionResult)

* **ProposedAction A1 — Write epochs to a repo-local SQLite DB + JSONL (U3/U4).**
  * **ActionRisk: LOW** (local file writes; potential tree-dirtying / concurrency).
  * **Required controls:** gitignore `.autoharness/metrics/` (U6); WAL + short-lived
    connections; parent-dir auto-create; **fail-open** on any sink error.
  * **ActionResult (expected):** epochs persist without dirtying the tree or
    blocking completion; concurrent emissions do not corrupt the DB.
* **ProposedAction A2 — Emit JSONL across the agent-engram boundary (U4/051.006).**
  * **ActionRisk: LOW** (contract-only; no external write).
  * **Required controls:** emit-only; versioned additive field contract; no CozoDB
    code; document the contract for the external consumer (U7).
  * **ActionResult (expected):** a stable, well-formed JSONL stream the external
    ingestion path can consume without autoharness knowing CozoDB internals.
* **ProposedAction A3 — Shell `backlogit update --size` (U10, Shipment C, deferred).**
  * **ActionRisk: MEDIUM** (external subprocess with interpolated args).
  * **Required controls:** argv-array only, quoted `{task_id}`/`{result}`, no
    `shell=True`; never overwrite an existing size; treat a missing `backlogit`
    binary as a configuration failure, not a task failure.
  * **ActionResult (expected):** size written back safely, or a clear actionable
    message; deferred to Shipment C behind the external CLI landing.

### Added verification, monitoring, rollback, and checkpoint detail

* **Environment prechecks:** verify the workspace is a repo and
  `.autoharness/metrics/` is (or becomes) gitignored before first emission; if the
  sink cannot be created, log a warning and continue (fail-open).
* **Target scenarios (Shipment A runtime verification):** epoch → SQLite persisted
  & queryable; epoch → JSONL well-formed & appended; disabled telemetry ⇒ no-op;
  invalid payload ⇒ exit 2; emission produces **no** `git status` diff (gitignore
  proof); concurrent emissions do not corrupt the DB.
* **Monitoring signals:** rows written / JSONL lines appended / sink errors
  (fail-open count) surfaced by `telemetry record` output.
* **Rollback trigger + procedure:** documented kill-switch — set `telemetry.mode:
  none` (or remove the block) to disable all emission with zero code change; delete
  `.autoharness/metrics/` to reset local data. Primary rollback; called out in U7.
* **Owner + validation window:** assigned at shipment/ship time.

### Unresolved operator decisions that still block safe execution

* None block Shipment A. Open items are confined to later shipments: the reviewer
  matrix's exact grading dimensions/weights (U9) and the eval model-config matrix
  source (U8) are implementation-time config, and the sizing model tier (U10) is
  Model-Routing config — none gate the capture-core first shipment.

## Runtime Verification and Closure

* **Changed runtime surfaces (Shipment A):** new `autoharness telemetry record`
  CLI subcommand; new `src/autoharness/telemetry/` package; new repo-local SQLite
  DB + JSONL under `.autoharness/metrics/`; `.gitignore` + config template.
* **Runtime verification before absorption:** exercise `autoharness telemetry
  record` against a seeded epoch for each scenario above (persist, emit, no-op,
  invalid, gitignore-clean, concurrent) and confirm exit codes + sink contents +
  a clean `git status`.
* **Operational closure artifacts:** rollback = `telemetry.mode: none` kill-switch
  (documented in U7) and deletion of `.autoharness/metrics/`; monitoring = per-run
  rows/lines/errors counts; healthy signal = clean tree + queryable DB + parseable
  JSONL; failure signal = sink error count > 0 (fail-open, investigate); owner +
  validation window recorded at ship time. Capture a compound learning on epoch
  emission + fail-open telemetry at closure.

## Plan Review

**Reviewers (single-model fallback — cross-model subagents unavailable in this
headless Stage run):** Constitution Reviewer, Python Reviewer, Scope Boundary
Auditor, Learnings Researcher, Architecture Strategist, Security Lens Reviewer
(triggered: external subprocess in U10 + external JSONL boundary in U4).

**Gate decision: PASS (with advisory P2/P3 items).**

Rationale: the plan shows hardening signals AND contains a `## Plan Hardening`
section classifying the risky actions (A1–A3) with `ProposedAction`/`ActionRisk`
and explicit controls. The no-execution-loop caveat is honored, the first-shipment
boundary is tight and self-contained, external boundaries are explicit, and the
Phase 1 gitignore learning is applied. No P0/P1 findings.

### Findings by severity

**P0 — none.**

**P1 — none.** (The highest-risk item, the external `backlogit update` subprocess,
is deferred to Shipment C and pre-constrained to argv-array/quoted/no-`shell=True`.
The tree-dirtying risk is closed by the U6 gitignore hard-gate. Telemetry is
fail-open and off the completion critical path.)

**P2 (record as backlog follow-ups / acceptance criteria):**

* **P2-1 (Security Lens):** U3/U4 must **fail open** on any sink exception — add an
  explicit test that a sink raising an error does not propagate a non-zero
  completion-blocking signal. Fold into U5 acceptance criteria.
* **P2-2 (Architecture Strategist):** Assert the `telemetry/` package has **no
  import** of `gates/` internals or install/tune modules (module-boundary
  direction), so telemetry evolves independently. Fold into U2 acceptance.
* **P2-3 (Python Reviewer):** Define **one** typed epoch/result object (U1
  `ExecutionEpoch` + payload dataclasses) reused by U3/U4/U5 to avoid divergent
  ad-hoc dict shapes across sinks.
* **P2-4 (Constitution Reviewer):** Because "templates are the product," U6 must
  ship the telemetry activation guidance through `harness-config.yaml.tmpl` (a
  `.tmpl`-resolvable artifact), not a hard-coded config, so target workspaces
  receive it via normal install/tune.
* **P2-5 (Scope Boundary Auditor):** U4 (051.006) and U10 (051.002) must include a
  negative check that **no** CozoDB / backlogit-schema code is added — emit-only /
  invoke-only boundaries asserted.

**P3 (advisory):**

* **P3-1 (Scope Boundary Auditor):** Keep U8 (eval) and U9 (reviewer) fully out of
  Shipment A; re-decompose them at Stage-time for Shipment B against the 2-hour
  rule (U8 likely splits into matrix-loader / frozen-runner / summary).
* **P3-2 (Learnings Researcher):** No existing `docs/compound/` entry covers
  telemetry epoch emission; capture a compound learning at operational closure.

### Runtime verification & closure check

Present and adequate: six runtime scenarios enumerated (including the
gitignore-clean-tree and concurrent-emission proofs), a documented kill-switch
rollback (`telemetry.mode: none` + delete `.autoharness/metrics/`), and monitoring
counts. Owner and validation window correctly deferred to ship time.

### Decomposition & scope check

Seven first-shipment units (U1–U7), each single-domain (CLI code / config /
template / docs) and within the 2-hour rule; the dependency graph is acyclic and
Shipment A is self-contained. Deferred units (U8–U10) are sequenced with explicit
dependencies and flagged for Stage-time re-decomposition. Width isolation is
respected — no unit mixes schema, CLI, and docs. **Ready for harvest.**

## Recommended Shipment Boundary

| Shipment | Scope | Tasks | Rationale |
|---|---|---|---|
| **A (FIRST)** | Telemetry-capture core | 051.001, 051.003, 051.006 (+ 051-F parent) | Self-contained "record epoch → SQLite + JSONL"; zero external runtime dependency; fully testable. |
| **B (next)** | Headless evaluation | 051.004, 051.005 | Both build on A's epoch model + SQLite sink; reviewer matrix (051.005) feeds eval scoring (051.004). |
| **C (last)** | Pre-execution sizing gate | 051.002 | Blocked on the **external** backlogit `--size` mutation CLI; sequence last so the external dependency can land first. |

Each shipment is an independently reviewable/shippable slice of feature 051-F,
respecting P-001 (one top-level release unit at a time; the feature ships across
sequential shipments, never in parallel).

---
title: "Deterministic Validation Gates (Phase 1) — autoharness Implementation Plan"
description: "Phase 1 of the Deterministic Gates, Telemetry & Evaluation Engine design — autoharness portion only"
source_documents:
  - "docs/decisions/2026-06-30-validation-gates-config-schema-deliberation.md"
  - "docs/decisions/2026-06-30-gate-policy-deliberation.md"
  - "docs/design-docs/autoharness-evals-gates-design.md"
epic: "93E85A44"
folds_stash:
  - "3F257C83"
  - "DB1057B5"
  - "036B2404"
  - "CD0EFDF3"
  - "9BBF6370"
  - "60E8ABBB"
scope: "autoharness-only (Phase 1)"
tags:
  - "deterministic-gates"
  - "phase-1"
  - "dark-factory"
---

## Problem Frame

Phase 1 of the design doc transitions autoharness from a prompt-only orchestrator
toward a deterministic gating layer: no file should enter the repo/graph without
passing a strict binary validation check, eliminating "hallucinated completion."

**Critical architectural caveat (must be respected by every unit):** autoharness's
CLI (`src/autoharness/` — `cli.py`, `schema_contracts.py`, `verify_workspace.py`)
today is an **install/tune tool**, not a live agent execution host. There is no
existing "core execution loop" in the CLI to refactor; the agent execution loop
lives in the harness runtime (Copilot CLI / VS Code / build-feature skill). Phase 1
therefore delivers the gate as a **self-contained CLI capability**
(`autoharness gate ...`) plus a **documented integration contract** that the
harness's task-completion flow invokes, rather than an in-process interceptor of a
loop that does not exist in this codebase. This reframes design doc §3's "hijack
the mark_task_complete tool call" as: expose a deterministic gate command the
task-completion path calls, and document where the harness invokes it.

## Requirements Trace

| Source requirement | Implementation unit(s) |
|---|---|
| config.yaml `validation_gates` schema contract (9BBF6370, §5) | T1, T2 |
| Lifecycle-hooks config read (3F257C83, §3) | T2, T6 |
| Git-diff discovery engine (DB1057B5, §3) | T3 |
| Glob match + cross-platform paths (§6.2) | T4 |
| Subprocess interceptor + timeout (036B2404, §3) | T5, T6 |
| Atomic block on non-zero exit (036B2404, gate-policy Q1) | T6 |
| Forced-correction loop: capture stderr + inject (CD0EFDF3, §3) | T7 |
| Enforcement modes + repeated-failure→blocked (60E8ABBB, Q2/Q3) | T7 |
| Integration contract + docs | T8 |

## Implementation Units

Each unit obeys the 2-hour rule (<3 files, <5 functions, <4 test scenarios),
width isolation (single domain), and produces an atomic verifiable milestone.

### T1 — validation_gates JSON Schema  *(domain: schema)*

* **Changes**: Add a versioned JSON Schema for the `lifecycle_hooks` + `telemetry`
  blocks (extend the harness-config schema family under `schemas/`), encoding the
  closed interpolation vocabulary (`{file_path}`, `{task_id}`, `{result}`),
  enum'd `enforcement`/`on_repeated_failure`, `action` namespacing
  (`internal:`/`shell:`), and optionality.
* **Files**: `schemas/harness-config/*.schema.json` (+ pointer schema).
* **Tests**: schema validates the design-doc §5 example; rejects unknown
  placeholder; rejects bad enum.
* **Posture**: test-first (schema fixture validation).

### T2 — config.yaml lifecycle_hooks block + resolution  *(domain: config/template)*

* **Changes**: Add the additive `lifecycle_hooks`/`telemetry` block to the config
  template and the config-loading/resolution path so an absent block is a no-op.
* **Files**: config template under `templates/foundation/` (or config emitter) +
  `src/autoharness/schema_contracts.py` loader hook.
* **Tests**: absent block ⇒ gates disabled (no behavior change); present block ⇒
  parsed into typed structure.
* **Posture**: test-first. **Depends on**: T1.

### T3 — Git-diff discovery utility  *(domain: CLI code)*

* **Changes**: Utility running `git diff --name-only <base>...<head>` to list
  modified files relative to the task branch base; returns forward-slash,
  repo-relative paths.
* **Files**: new module in `src/autoharness/` (e.g. `gates/discovery.py`).
* **Tests**: parses diff output; handles empty diff; normalizes separators.
* **Posture**: test-first. **Depends on**: T1, T2.

### T4 — Glob matcher + cross-platform path normalization  *(domain: CLI code)*

* **Changes**: Match discovered paths against gate `pattern` doublestar globs over
  normalized paths; host-appropriate case sensitivity (§6.2).
* **Files**: `src/autoharness/gates/match.py`.
* **Tests**: `docs/**/*.md` matches nested; Windows backslash normalized; case rule.
* **Posture**: test-first. **Depends on**: T1, T2.

### T5 — Subprocess gate runner (timeout + argv-array)  *(domain: CLI code)*

* **Changes**: Execute the interpolated `command` per matched file with
  `timeout_seconds`; capture exit code + stderr; use argv-array execution with
  strictly-quoted `{file_path}` to prevent shell injection (plan-harden item).
* **Files**: `src/autoharness/gates/runner.py`.
* **Tests**: non-zero exit captured; timeout enforced; injection-safe interpolation.
* **Posture**: test-first. **Depends on**: T1, T2.

### T6 — pre_task_completion gate command (atomic block)  *(domain: CLI code)*

* **Changes**: New `autoharness gate check --task <id> --base <ref>` subcommand:
  discovery(T3) → match(T4) → run(T5) for every matched file; aggregate results;
  exit non-zero (block) if ANY file fails (atomic all-or-nothing, gate-policy Q1).
* **Files**: `src/autoharness/gates/gate.py` + `cli.py` subcommand wiring.
* **Tests**: all pass ⇒ exit 0; one fail ⇒ non-zero + per-file report; no matches ⇒ pass.
* **Posture**: test-first. **Depends on**: T3, T4, T5.

### T7 — Forced-correction feedback + enforcement modes  *(domain: CLI code)*

* **Changes**: Emit a structured per-file pass/fail + stderr correction report on
  the completion path for agent self-healing (CD0EFDF3); honor
  `enforcement: absolute|advisory`; enforce `on_repeated_failure`/`max_gate_failures`
  (default block+requeue after 3; opt-in escalate) with operator-only `--force`.
* **Files**: `src/autoharness/gates/feedback.py` (+ small `gate.py` wiring).
* **Tests**: advisory warns-not-blocks; 3rd failure ⇒ blocked signal; force bypass logged.
* **Posture**: test-first. **Depends on**: T6.

### T8 — Integration contract + documentation  *(domain: docs)*

* **Changes**: Document the config schema, gate policy, `autoharness gate check`
  contract, and exactly where the harness task-completion flow invokes it
  (build-feature / mark-task-complete integration point). Update getting-started.
* **Files**: `docs/` (new gates reference) + `docs/getting-started.md`.
* **Tests**: doc cross-reference integrity (referenced files/commands exist).
* **Posture**: characterization/doc. **Depends on**: T1–T7.

## Dependency Graph

```text
T1 ─┬─> T3 ─┐
    ├─> T4 ─┼─> T6 ─> T7 ─┐
    └─> T5 ─┘             │
T2 ─┴──────────────────────> (all CLI units read config)
T1..T7 ─> T8 (docs last)
```

No cycles.

## Decisions and Rationale

* **Gate delivered as `autoharness gate check` CLI + integration contract** rather
  than in-process loop interception — because no CLI execution loop exists to
  intercept; a deterministic, independently-testable command is the honest and
  testable realization of design §3 in this codebase.
* **Atomic all-or-nothing task gating** — per gate-policy deliberation Q1;
  preserves the atomic-milestone principle and blocks hallucinated completion.
* **Absolute-by-default enforcement, operator-only force** — per gate-policy Q2;
  agents cannot self-bypass.
* **3-failure block+requeue aligned to circuit-breaker** — per Q3.
* **Local telemetry deferred to Phase 2** — §6.3; Phase 1 does not build telemetry.

## Risks and Caveats

* The "execution loop refactor" framing in the stash/design doc overstates what
  exists in the CLI; mitigated by the integration-contract reframing above. This
  is the single most important thing for reviewers/implementers to internalize.
* Subprocess execution of config-supplied commands is a security surface
  (injection, arbitrary command execution) — hardened in T5 and Plan Hardening.
* Cross-platform path/glob correctness is easy to get subtly wrong on Windows —
  covered by T4 tests.

## Plan Hardening Signals (REQUIRED)

* **Public API / schema / contract change**: PRESENT — new config schema
  (`schemas/`), new `autoharness gate` CLI subcommand, and a harness integration
  contract other agents depend on.
* **Security / auth / permission-sensitive behavior**: PRESENT — executes
  config-supplied subprocess commands with interpolated file paths (command
  injection / arbitrary execution surface).
* **Migration / backfill / destructive / irreversible step**: ABSENT — additive,
  optional config; no data migration.
* **External integration / operator checkpoint / external dependency**: PRESENT —
  depends on external `git`, and on external tools (`engram verify`,
  `backlogit doctor`, `pytest`) referenced by example gates; operator `--force`
  checkpoint.
* **High runtime / rollout / rollback risk**: PRESENT (moderate) — gates sit on
  the task-completion critical path; a broken gate can block all completions.

Conclusion: **Requires plan hardening: yes.**

## Runtime Verification and Closure

* **Changed runtime surfaces**: new `autoharness gate check` CLI subcommand; config
  loading path; task-completion integration point.
* **Runtime verification before absorption**: exercise `autoharness gate check`
  against a seeded repo with (a) all-pass, (b) one-fail, (c) no-match, (d) timeout,
  (e) advisory-mode, and (f) 3-consecutive-failure→blocked scenarios; verify exit
  codes and correction-report content.
* **Operational closure artifacts**: rollback trigger = disable via removing/empty
  `lifecycle_hooks` block (documented kill-switch); monitoring = gate
  pass/fail/timeout counts surfaced in the correction report; owner + validation
  window recorded at ship time. Because gates are on the completion critical path,
  closure must document the config kill-switch prominently.

## Plan Hardening

**Hardening required: YES.** Confirmed elevated blast radius — the plan changes a
public schema, adds a new CLI contract, and executes config-supplied subprocess
commands on the task-completion critical path.

### Risk triggers and protected invariants

* **Trigger — arbitrary command execution:** gate `command` strings are executed
  as subprocesses with an interpolated `{file_path}`. **Invariant to preserve:**
  a crafted or attacker-influenced file path must never break out of its argument
  position or inject additional commands.
* **Trigger — completion-path availability:** gates sit on `mark_task_complete`.
  **Invariant:** a misconfigured, missing, or absent `lifecycle_hooks` block must
  fail *open to today's behavior* (no gates ⇒ no blocking), never crash the
  completion path.
* **Trigger — public contract stability:** the config schema and
  `autoharness gate check` CLI are depended upon by the harness runtime.
  **Invariant:** additive, versioned, backward-compatible; existing installs with
  no `lifecycle_hooks` are unaffected.

### Reinforced instructions and learnings consulted

* `circuit-breaker.instructions.md` — `MAXIMUM_RETRY_THRESHOLD = 3`; the
  `max_gate_failures` default (3) and block+requeue behavior MUST match this
  contract, including logging a circuit-breaker checkpoint on the 3rd failure.
* `coding-discipline.instructions.md` — simplicity/surgical: implement the gate as
  a small, isolated `gates/` package; do not refactor unrelated CLI code.
* Gate-policy deliberation (Q2/Q3) — absolute default, operator-only force,
  block+requeue.
* No prior `docs/compound/` entry covers subprocess gating (searched); this is new
  institutional surface — a compound learning should be captured at closure.

### Risky actions (ProposedAction / ActionRisk / ActionResult)

* **ProposedAction A1 — Execute config-supplied subprocess per matched file (T5/T6).**
  * **ActionRisk: HIGH** (arbitrary code execution / command injection).
  * **Required controls:** argv-array execution ONLY (never `shell=True`);
    `{file_path}` passed as a single quoted argv element; reject `command`
    templates whose interpolation would alter argv arity; enforce
    `timeout_seconds` with hard process kill; run with the invoking user's
    privileges only (no elevation).
  * **ActionResult (expected):** each gate runs in an isolated subprocess with a
    bounded lifetime; failures and stderr are captured, never suppressed.
* **ProposedAction A2 — Operator `--force` bypass of a failing gate (T7).**
  * **ActionRisk: MEDIUM** (deliberate gate bypass).
  * **Required controls:** flag is operator/CLI-only and MUST NOT be reachable
    from any agent-accessible surface; every use emits P-005 telemetry and is
    echoed in the correction report and closure artifact.
  * **ActionResult (expected):** bypass is rare, explicit, human-initiated, and
    fully audited.
* **ProposedAction A3 — Force task to `blocked` + requeue after 3 failures (T7).**
  * **ActionRisk: LOW-MEDIUM** (state transition on failure).
  * **Required controls:** align with circuit-breaker; write a checkpoint under
    `docs/memory/` capturing the failure chain before transitioning.

### Added verification, monitoring, rollback, and checkpoint detail

* **Environment prechecks:** verify `git` is available and the working tree is a
  git repo before discovery; if not, gate degrades to "no modified files
  discovered" and logs a warning rather than crashing.
* **Target scenarios (must be verified at runtime):** all-pass, one-fail,
  no-match, timeout-kill, advisory-warn, 3-consecutive-failure→blocked, and
  operator-`--force`-bypass-audited.
* **Blocked-path handling:** if a gate `command` binary is missing (e.g.
  `engram verify` absent), treat as a gate *configuration* failure with a clear
  actionable message, distinct from a validation *content* failure.
* **Monitoring signals:** per-run counts of gates run / passed / failed / timed-out
  / forced; emit to the correction report (telemetry DB is Phase 2, not now).
* **Rollback trigger + procedure:** documented kill-switch — remove or empty the
  `lifecycle_hooks` block to instantly disable all gating with zero code change;
  this is the primary rollback and MUST be called out in T8 docs and closure.
* **Owner + validation window:** assigned at shipment/ship time.

### Unresolved operator decisions that still block safe execution

* None that block Phase 1 planning. The `on_repeated_failure: escalate` target
  model tier is deferred to implementation-time Model Routing config and does not
  gate harvest (default `block` is fully specified).

**Hardening outcome:** plan is ready for `plan-review`. Security controls (A1)
are now explicit and testable; availability invariant (fail-open-to-current) is
pinned; rollback kill-switch is defined.

## Plan Review

**Reviewers (single-model fallback — cross-model subagents unavailable in headless run):**
Constitution Reviewer, Python Reviewer, Scope Boundary Auditor, Learnings
Researcher, Architecture Strategist, Security Lens Reviewer (triggered: subprocess
execution + external integrations).

**Gate decision: PASS (with advisory P2/P3 items).**

Rationale: the plan shows hardening signals AND contains a `## Plan Hardening`
section that classifies the risky actions (A1–A3) with `ProposedAction`/`ActionRisk`
and explicit controls. No P0/P1 findings. Hardening-required gate is satisfied.

### Findings by severity

**P0 — none.**

**P1 — none.** (The most dangerous item, config-driven subprocess execution, is
already constrained to argv-array-only with quoted `{file_path}` and timeout kill
in Plan Hardening A1; the availability invariant fails open to current behavior.)

**P2 (record as backlog follow-ups / acceptance criteria):**

* **P2-1 (Security Lens):** T5 should include an explicit negative test proving
  `shell=True` is never used and that a `{file_path}` containing shell
  metacharacters (`;`, `&&`, `$(...)`, backticks) cannot inject a second command.
  Fold into T5 acceptance criteria.
* **P2-2 (Architecture Strategist):** Keep the new `gates/` package free of import
  coupling to install/tune modules (`verify_workspace.py`) so gating can evolve
  independently; assert module-boundary direction in T6.
* **P2-3 (Python Reviewer):** Define one typed result object (e.g. `GateResult`
  with file, pattern, command, exit_code, stderr, duration) shared across
  T5/T6/T7 to avoid divergent ad-hoc dict shapes.
* **P2-4 (Constitution Reviewer):** Because "templates are the product," T2 must
  ensure the config block ships as a `.tmpl`-resolvable artifact, not a
  hard-coded config, so target workspaces receive it through normal install/tune.

**P3 (advisory):**

* **P3-1 (Scope Boundary Auditor):** Do NOT implement any Phase 2 telemetry in
  Phase 1 tasks — the SQLite DB, epoch emitter, and JSONL are Feature B only.
  Watch for scope bleed in T7 (it emits counts to the report, not to a DB — keep
  it that way).
* **P3-2 (Learnings Researcher):** No existing `docs/compound/` entry covers
  subprocess gating; capture a compound learning at operational closure.

### Runtime verification & closure check

Present and adequate: the plan enumerates six runtime scenarios, a documented
kill-switch rollback (empty `lifecycle_hooks`), and monitoring counts. Owner and
validation window are correctly deferred to ship time.

### Decomposition & scope check

Eight units, each single-domain (schema / config-template / CLI / docs) and within
the 2-hour rule; dependency graph is acyclic. Width isolation is respected — no
unit mixes schema, CLI, and docs. **Ready for harvest.**

---
title: "Validation Gate Policy: Partial Completion, Enforcement Modes, and Loop Limits"
description: "Resolves gate-policy open questions — partial-completion handling, force-override vs absolute gate, infinite correction loops, cross-platform paths, telemetry locality"
topic: "Resolve gate-policy open questions (Dark Factory + design doc §6)"
depth: "deep"
decision_status: "decided"
promoted_to: "plan"
linked_artifacts:
  - "docs/plans/2026-06-30-deterministic-validation-gates-phase1-plan.md"
  - "docs/decisions/2026-06-30-validation-gates-config-schema-deliberation.md"
  - "docs/design-docs/autoharness-evals-gates-design.md"
source_stash_ids:
  - "60E8ABBB"
resolves_design_open_questions:
  - "§6.1 Infinite correction loops"
  - "§6.2 Cross-platform paths"
  - "§6.3 Global vs local telemetry"
tags:
  - "deterministic-gates"
  - "gate-policy"
  - "dark-factory"
---

## Problem Frame

Stash entry `60E8ABBB` (high) requires resolving the **policy** questions that
govern how validation gates behave at runtime, independent of the wire-format
schema (resolved in the companion config-schema deliberation). Two policy
questions come from the stash entry directly, and three overlapping questions
come from design doc §6. They are resolved together because they are coupled:

1. **Partial-completion handling** — when a task modifies multiple files and some
   pass their gate while others fail, does the task complete, partially complete,
   or block?
2. **Force-override vs absolute gate per dev mode** — can a gate failure ever be
   overridden, and by whom (agent vs operator), and does the answer differ by
   development mode?
3. **(§6.1) Infinite correction loops** — after repeated gate failures, force
   `blocked` and requeue, or auto-escalate to a heavier model?
4. **(§6.2) Cross-platform paths** — how are glob matching and subprocess paths
   normalized across Windows/POSIX runners?
5. **(§6.3) Global vs local telemetry** — does the metrics DB live in-repo or
   globally?

Autonomy note: headless session. Operator-confirmation points are replaced with
documented default decisions consistent with declared operator preferences
(strict gating, sequential single-PR workflow, safety-first guardrails).

## Research Findings

* The design doc's central goal is eliminating "hallucinated completion" — the
  policy must therefore fail *closed*, not *open*.
* `circuit-breaker.instructions.md` already pins `MAXIMUM_RETRY_THRESHOLD = 3`
  for same-error retries and prescribes `blocked` + operator escalation. The gate
  loop policy should align with this rather than invent a new limit.
* Primitive 5 (guardrails) requires destructive/override actions be operator-
  legible and not agent-self-serviceable; Primitive 3 (model routing) permits
  escalation to a heavier tier on repeated failure.
* Design doc §6.3 already recommends **local** telemetry for Phase 1.

## Options Evaluated

### Q1 — Partial-completion handling

* **Option A — Atomic all-or-nothing (task-level gate):** if ANY matched file
  fails, block the whole `mark_task_complete`; report per-file pass/fail so the
  agent knows exactly what to fix.
* **Option B — Per-file partial completion:** allow the task to complete for
  passing files and defer only failing ones.

**Decision: Option A.** A backlog task is an atomic unit of work with a single
verifiable exit state (2-hour-rule / atomic-milestone principle). Allowing
partial completion reintroduces exactly the ambiguous, half-done states the
design doc exists to eliminate. The gate runs every matched file, aggregates
results, and blocks completion if the aggregate contains any failure — but the
injected feedback enumerates each file's individual pass/fail + stderr so
correction is targeted, not blind.

### Q2 — Force-override vs absolute gate

* **Option A — Absolute by default; operator-only force-override; opt-in advisory
  mode.** Default `enforcement: absolute` — the gate is a hard stop the agent
  cannot bypass. A human operator may override via an explicit out-of-band
  `--force` flag (never exposed to the agent). A per-gate or global
  `enforcement: advisory` opt-in downgrades failures to warnings for local/dev
  ergonomics.
* **Option B — Agent-accessible override flag.** Let the agent decide to proceed
  past a gate.

**Decision: Option A.** Option B defeats the anti-hallucination purpose (an agent
that can bypass a gate will). "Per dev mode" is honored via the `advisory`
enforcement value rather than an agent override: teams working locally can set
`advisory` to warn-not-block, while CI/production runs keep `absolute`. Force is a
human escape hatch only, and every override is logged for observability (P-005).

### Q3 — Infinite correction loops (§6.1)

* **Option A — Block + requeue after N failures (default), with opt-in escalation.**
  After `max_gate_failures` (default 3, aligned with circuit-breaker) consecutive
  gate failures on the same task, force the task to `blocked`, return it to the
  queue, and surface to the operator. `on_repeated_failure: escalate` is an opt-in
  that first routes the task to a heavier model tier before blocking.
* **Option B — Always auto-escalate model.** Escalate on every repeated failure.

**Decision: Option A.** Default `block` matches the existing circuit-breaker
contract (3 same-error failures ⇒ stop + escalate to operator) and avoids
unbounded cost from silent model escalation. `escalate` remains available for
teams that prefer an automated heavier-model retry before blocking; even then, a
second failure after escalation blocks.

### Q4 — Cross-platform paths (§6.2)

**Decision:** Normalize all discovered paths to **forward-slash, repo-relative**
form before glob matching and before `{file_path}` interpolation. Glob matching
uses doublestar semantics; case-sensitivity follows the host filesystem
(sensitive on POSIX, insensitive on Windows) applied to the normalized path.
Subprocess execution resolves the command on the host's default shell but passes
`{file_path}` as a normalized, individually-quoted argument. plan-harden must
evaluate argv-array execution to eliminate shell-injection risk from crafted
paths.

### Q5 — Global vs local telemetry (§6.3)

**Decision:** **Local** for Phase 1 — `.autoharness/metrics/execution_epochs.db`
inside the target repo, per the design doc recommendation, binding telemetry to
the repo's specific architecture. Global multi-repo aggregation is explicitly
deferred to Phase 2 / future and recorded as a follow-up, not built now.

## Trade-off Comparison

| Question | Chosen | Fails safe? | Aligns existing harness rule |
|---|---|---|---|
| Partial completion | Atomic all-or-nothing | Yes | Atomic-milestone / 2-hr rule |
| Override | Absolute + operator-only force | Yes | Primitive 5 guardrails |
| Repeated failure | Block+requeue (escalate opt-in) | Yes | circuit-breaker (3) |
| Paths | Forward-slash normalized | n/a | Cross-platform mandate |
| Telemetry locality | Local (Phase 1) | n/a | Design doc §6.3 recommendation |

## Decision (summary)

The gate is **fail-closed, atomic, and operator-governed**: any matched-file
failure blocks the whole task completion; the agent cannot self-bypass; repeated
failures block and requeue after 3 attempts (optionally escalating model tier
first); paths are forward-slash normalized; telemetry is repo-local for Phase 1.
These map directly onto the schema fields `enforcement`, `on_repeated_failure`,
and `max_gate_failures` defined in the companion config-schema deliberation.

## Rejected Alternatives

* Per-file partial completion — reintroduces ambiguous half-done task states.
* Agent-accessible override — defeats anti-hallucination guarantee.
* Always auto-escalate model — unbounded cost; inconsistent with circuit-breaker.
* Global telemetry in Phase 1 — premature; deferred per §6.3.

## Unresolved Questions

* Exact model tier to escalate to when `on_repeated_failure: escalate` is set —
  defer to Model Routing (Primitive 3) configuration during implementation.
* Whether `advisory` mode should still emit telemetry marking the would-be block
  — recommend yes; confirm during impl-plan.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Operator `--force` becomes a habitual bypass | Log every force override as P-005 telemetry; surface in closure |
| `advisory` mode silently hides real failures in CI | Restrict recommended `advisory` use to local/dev; keep CI on `absolute`; still emit telemetry |
| Shell-injection via `{file_path}` | plan-harden to require argv-array execution / strict quoting |
| Requeue thrash on a genuinely-broken gate | 3-failure block + operator escalation stops the loop (circuit-breaker parity) |

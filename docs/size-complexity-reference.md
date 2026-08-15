---
title: Size + Complexity Semantics Reference
description: Non-conflated task-level size (effort/volume) and complexity (difficulty/uncertainty) semantics, enum tables, the two-axis 2-hour reliability gate, and the provenance-completeness rule.
---

# Size + Complexity Semantics Reference

> **Navigation**: [README](../README.md) · [Architecture](ARCHITECTURE.md) · [Validation Gates](gates-reference.md) · [Telemetry Reference](telemetry-reference.md)

This reference adopts backlogit's released task-only `size` and `complexity` metadata
contract verbatim. autoharness's Stage decomposition workflow (agent template + harvest
skill) consumes this contract as first-class, validated, non-conflated planning metadata
when staging tasks. backlogit owns the field definitions, storage, and validation;
autoharness owns applying them consistently during decomposition.

## Non-conflation invariant

`size` and `complexity` answer two different questions and MUST NEVER be combined into a
single scalar, label, or derived score:

* **`size` answers "how much implementation volume/effort is this?"** — an ordinal measure
  of the amount of work: files touched, functions changed, test scenarios required.
* **`complexity` answers "how hard, uncertain, cross-cutting, or cognitively risky is
  this?"** — an ordinal measure of implementation difficulty and reasoning/risk, independent
  of how much code the work touches.

A task can be small and hard (e.g., a one-line concurrency fix, size `XS` / complexity
`high`) or large and easy (e.g., a mechanical rename across many files, size `L` /
complexity `trivial`). Treating either axis as a proxy for the other, or folding both into
one field, destroys the planning signal each axis exists to provide.

## Enum tables

### `size` (implementation volume/effort)

| Value | Meaning |
|---|---|
| `XS` | Trivial volume: a handful of lines, one file, no new test scenarios |
| `S` | Small volume: a single focused change, one or two files |
| `M` | Moderate volume: several files or functions, a few test scenarios |
| `L` | Large volume: many files or functions, broad test coverage |
| `XL` | Very large volume: should usually be split further before staging |

### `complexity` (implementation difficulty/uncertainty)

| Value | Meaning |
|---|---|
| `trivial` | Mechanical change; no design decisions, no unknowns |
| `low` | Straightforward change; minor judgment calls, well-understood approach |
| `medium` | Meaningful design or integration judgment; some open questions |
| `high` | Cross-cutting, uncertain, or cognitively risky; requires de-risking, spikes, or splitting |

## The two-axis 2-hour reliability gate

Agent reliability drops below 50% for tasks exceeding 2 hours of human-equivalent effort
(the 2-hour rule). Both axes feed this gate **independently**:

* **`size` bounds volume.** A task whose size estimate implies more than 2 hours of
  human-equivalent effort must be split, regardless of its complexity.
* **High `complexity` forces a split or de-risking step regardless of size.** A task
  labeled `complexity: high` is not automatically safe to execute in one pass even when
  its `size` is small — uncertainty and cognitive risk can blow the reliability budget
  just as surely as raw volume. High-complexity work should be de-risked (via a spike,
  additional deliberation, or further decomposition) or explicitly split before being
  staged as a single executable task.

Neither axis alone determines readiness for staging; both must be evaluated, and a task
that fails either check is not backlog-ready as-is.

## Provenance-completeness rule

A non-empty `size_source` requires a non-empty `size_ruleset_version`. Provenance fields
are recorded together or not at all:

* `size_source` — who/what produced the estimate (`human`, `agent`, or `derived`)
* `size_ruleset_version` — the named, versioned ruleset used to produce the estimate
  (Stage-authored tasks use `ah-stage-sizing-v1`)

A task carrying `size_source` without a corresponding `size_ruleset_version` (or vice
versa) has incomplete provenance and should be treated as a staging defect: the estimate
cannot be traced to the rules that produced it.

`complexity` currently has no equivalent provenance pair in the backlogit contract; it is
recorded as a plain enum value without a `complexity_source`/`complexity_ruleset_version`
pair.

## Storage and validation

`size` and `complexity` are **not** supported by the same set of artifact types in
the active backlogit storage root's `header-def.yaml` (`.backlog/header-def.yaml`
for new installs; this repository currently retains the legacy
`.backlogit/header-def.yaml`):

* **`size`** is stored on both the `task` and `subtask` artifact types (both `optional`,
  same `XS|S|M|L|XL` enum). Features and shipments expose computed, not stored, size
  composition.
* **`complexity`** is stored on the `task` artifact type only. There is no `subtask`,
  feature, or shipment-level `complexity` field in the current backlogit contract.

This staging workflow's own mandate (harvest skill, Stage agent) targets **task-kind
work items**, so both fields are emitted together there — but that task-only emission
scope must not be read as "both fields are task-only in storage": `size` alone extends to
subtasks. Both fields, wherever stored, are validated against the enum values defined in
the active backlogit storage root's `header-def.yaml` before write — invalid
values are rejected fail-closed rather
than silently coerced or defaulted.

## Cross-references

* [`templates/agents/_stage.agent.md.tmpl`](../templates/agents/_stage.agent.md.tmpl) and
  the installed [`.github/agents/_stage.agent.md`](../.github/agents/_stage.agent.md) —
  mandate size + complexity at task-creation time.
* [`templates/skills/harvest/SKILL.md.tmpl`](../templates/skills/harvest/SKILL.md.tmpl) —
  emits size + complexity on every harvested work item and enforces the enum validation
  gate.
* [`docs/telemetry-reference.md`](telemetry-reference.md) — `WorkSizingSnapshot` and the
  telemetry-facing view of task-level `size`.

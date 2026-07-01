---
title: "validation_gates Configuration Schema Contract"
description: "Exact YAML/JSON schema for .autoharness/config.yaml lifecycle_hooks and validation_gates"
topic: "Define .autoharness/config.yaml validation_gates schema (Dark Factory prerequisite)"
depth: "deep"
decision_status: "decided"
promoted_to: "plan"
linked_artifacts:
  - "docs/plans/2026-06-30-deterministic-validation-gates-phase1-plan.md"
  - "docs/design-docs/autoharness-evals-gates-design.md"
source_stash_ids:
  - "9BBF6370"
supersedes_epic: "93E85A44 (partial — Phase 1 config contract)"
tags:
  - "deterministic-gates"
  - "config-schema"
  - "dark-factory"
---

## Problem Frame

Stash entry `9BBF6370` (high) requires an exact, authoritative schema for the
`.autoharness/config.yaml` block that drives deterministic validation gates. This
schema is a **hard prerequisite** — every downstream hook-implementation task
(git-diff discovery, subprocess interceptor, forced-correction loop) reads from
this contract, so it must be pinned before any implementation planning proceeds.

The design doc `docs/design-docs/autoharness-evals-gates-design.md` §5 already
provides a concrete configuration block. This deliberation formalizes that block
into a committed contract, resolves format/validation questions the design doc
left implicit, and defines the interpolation-variable vocabulary and
backward-compatibility posture.

Autonomy note: this session is headless. Where the deliberate skill would consult
the operator, the sensible default is taken and its rationale documented inline.

### Context constraints (from repository inspection)

* Existing `.autoharness/config.yaml` is already YAML — the new block must be YAML
  and must merge additively without breaking existing keys.
* autoharness convention: JSON Schemas for config live under `schemas/`
  (e.g. `schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json`).
  A new/extended schema is the natural validation home.
* autoharness is cross-platform (Windows + POSIX runners) — glob and path handling
  must normalize deterministically (design doc §6.2).

## Research Findings

* Design doc §5 pins three sub-blocks: `lifecycle_hooks.pre_execution` (list),
  `lifecycle_hooks.pre_task_completion.validation_gates` (list of
  `{pattern, command, timeout_seconds}`), and a top-level `telemetry` block.
* The `command` strings use `{file_path}`, `{task_id}`, and `{result}`
  placeholders — these must be enumerated as a closed interpolation vocabulary so
  implementation does not invent ad-hoc variables.
* Existing `model_routing` config precedent shows autoharness config blocks are
  optional and schema-validated; the same optionality applies here for backward
  compatibility.

## Options Evaluated

### Option A: YAML block in config.yaml + JSON Schema in schemas/ (design-doc-aligned)

Adopt the design doc §5 YAML structure verbatim, add a JSON Schema under
`schemas/` to validate it, and enumerate the interpolation vocabulary.

* **Pros**: Matches existing config format; reuses schema convention; zero new
  file formats; directly satisfies the design contract.
* **Cons**: Requires keeping two artifacts (YAML example + JSON Schema) in sync.
* **Effort**: Low-Medium. **Fit**: Excellent.

### Option B: Standalone `.autoharness/gates.yaml` file

Put gates in a dedicated file rather than the main config.

* **Pros**: Isolation of gate concerns.
* **Cons**: Diverges from design doc §5 ("must be added to .autoharness/config.yaml");
  fragments configuration; more discovery paths to resolve.
* **Effort**: Medium. **Fit**: Poor (contradicts the design contract).

### Option C: Inline JSON in config

Express gates as embedded JSON.

* **Pros**: None material over YAML.
* **Cons**: Inconsistent with the YAML config file; worse ergonomics.
* **Effort**: Low. **Fit**: Poor.

## Trade-off Comparison

| Criterion | Option A | Option B | Option C |
|---|---|---|---|
| Design-doc alignment | Full | Contradicts §5 | Partial |
| Format consistency | High | Medium | Low |
| Validation story | JSON Schema (existing convention) | New | Awkward |
| Backward compatibility | Additive/optional | Additive | Additive |

## Decision

**Adopt Option A.** The contract is:

```yaml
# .autoharness/config.yaml  (additive; entire lifecycle_hooks block is OPTIONAL)
lifecycle_hooks:
  pre_execution:
    - name: "estimate_complexity"          # string, required, unique within list
      condition: "task.size == null"       # string expr, optional (default: always)
      action: "internal:estimate_tshirt_size"  # "internal:<fn>" | "shell:<cmd>", required
      write_back: "backlogit update {task_id} --size {result}"  # optional shell template

  pre_task_completion:
    enforcement: "absolute"                # enum: absolute | advisory ; default absolute
    on_repeated_failure: "block"           # enum: block | escalate ; default block
    max_gate_failures: 3                   # int >=1 ; default 3 (aligns circuit-breaker)
    validation_gates:
      - pattern: "docs/**/*.md"            # doublestar glob (forward-slash), required
        command: "engram verify {file_path}"  # required; interpolated shell template
        timeout_seconds: 15                # int >0 ; required
        enforcement: "absolute"            # optional per-gate override of block default
      - pattern: ".backlogit/queue/*.md"
        command: "backlogit doctor --target {file_path}"
        timeout_seconds: 5
      - pattern: "src/**/*.py"
        command: "pytest tests/ --lf"
        timeout_seconds: 60

telemetry:
  mode: "sqlite"                           # enum: sqlite | none ; default none
  database_path: ".autoharness/metrics/execution_epochs.db"  # repo-relative
  emit_jsonl: true                         # bool ; default false
```

### Resolved contract decisions

1. **Format**: YAML in `.autoharness/config.yaml`; validated by a JSON Schema
   published under `schemas/` (extend the harness-config schema family, versioned).
2. **Interpolation vocabulary (closed set)** — the only permitted placeholders:
   * `{file_path}` — repo-relative, forward-slash-normalized path of the matched
     modified file (one gate invocation per matched file).
   * `{task_id}` — the active backlog task ID.
   * `{result}` — the value produced by a `pre_execution` action (e.g. size),
     valid only in `write_back`.
   Unknown placeholders are a schema/validation error, not silently passed through.
3. **Glob semantics**: doublestar (`**`) matching over forward-slash-normalized
   paths; matching is case-sensitive on POSIX, case-insensitive on Windows,
   applied to the normalized path (resolves §6.2 at the schema layer).
4. **Optionality / backward compatibility**: the entire `lifecycle_hooks` and
   `telemetry` blocks are OPTIONAL. Absent `lifecycle_hooks` ⇒ no gates run and
   behavior is identical to today (no regression for existing installs).
5. **`enforcement` and `on_repeated_failure`** live in the schema but their
   *policy semantics* are defined in the companion gate-policy deliberation
   (`60E8ABBB`). The schema only pins their allowed values and defaults.
6. **`action` namespacing**: `internal:<name>` for autoharness built-ins,
   `shell:<cmd>` for external commands — prevents ambiguity between the two.

## Rejected Alternatives

* Option B/C rejected: they contradict design doc §5 ("must be added to
  .autoharness/config.yaml") and fragment or degrade the configuration surface.
* An open-ended interpolation grammar was rejected in favor of a closed
  placeholder set to keep subprocess construction auditable and injection-safe.

## Unresolved Questions

* Policy semantics for `enforcement`, `on_repeated_failure`, and partial-file
  failure are resolved in the companion deliberation
  (`2026-06-30-gate-policy-deliberation.md`), not here.
* Whether `command` should support argument-array form (vs shell string) to avoid
  shell-injection is flagged to plan-harden as a security refinement.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Shell-string `command` enables injection via crafted file paths | plan-harden to evaluate argv-array execution and `{file_path}` quoting/allowlisting |
| YAML example and JSON Schema drift | Single versioned schema is the source of truth; config example generated/checked against it |
| Cross-platform glob mismatch | Normalize to forward-slash before matching; document case-sensitivity rule |
| `internal:` action registry unbounded | Enumerate allowed internal actions in schema `enum` |

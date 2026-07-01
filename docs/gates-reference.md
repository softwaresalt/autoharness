---
title: Validation Gates Reference
description: Deterministic pre-task-completion validation gates — configuration schema, gate policy, the autoharness gate check CLI contract, and the kill-switch rollback
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md)

## Overview

Deterministic validation gates let the harness enforce **non-LLM, exit-code-based
checks** on the files a task modified, before that task is allowed to complete.
Instead of trusting a model loop to decide whether documentation, backlog items,
or source files are valid, the harness runs operator-authored commands and blocks
completion when any of them fail.

This is **Phase 1** of the Deterministic Gates & Evaluation Engine design. It
delivers the gate execution surface only. Telemetry (SQLite epochs, JSONL emission)
and estimation are **Phase 2** and are intentionally *not* implemented here — see
[the design document](design-docs/autoharness-evals-gates-design.md) §4.

Gates are **entirely opt-in**. When no `lifecycle_hooks` block is configured, the
harness behaves exactly as it did before gates existed (fail-open-to-current). See
the [Kill-Switch Rollback](#kill-switch-rollback) below.

## Configuration Schema

Gates are configured under a `lifecycle_hooks` block in the workspace
`.autoharness/config.yaml`. The block is validated against the versioned
[`validation-gates` JSON Schema](../schemas/validation-gates/1.0.0.schema.json).
The **entire block is optional**; every field within it that is not marked
required has a documented default.

### `lifecycle_hooks.pre_task_completion.validation_gates`

Each validation gate is a `pattern` → `command` pair:

| Field | Required | Description |
|---|---|---|
| `pattern` | yes | A doublestar glob (e.g. `docs/**/*.md`) matched against forward-slash-normalized, repo-relative modified paths. |
| `command` | yes | The command template to run per matched file. Executed as an argv array with `shell=False` — never through a shell. |
| `timeout_seconds` | yes | Hard timeout; the process is killed if it exceeds this. |
| `enforcement` | no | `absolute` (default, blocks) or `advisory` (warns, never blocks). Overrides the block-level policy for this gate only. |

**Closed interpolation vocabulary.** A `command` may reference only these
placeholders, each substituted into a single argv token:

| Placeholder | Meaning |
|---|---|
| `{file_path}` | The matched, repo-relative file path. |
| `{task_id}` | The active backlog task ID. |
| `{result}` | A prior action result (used by `pre_execution` write-backs). |

Any other `{placeholder}` is rejected at schema-validation time.

### `lifecycle_hooks.pre_task_completion` policy

| Field | Default | Values | Description |
|---|---|---|---|
| `enforcement` | `absolute` | `absolute` \| `advisory` | Block-level default enforcement for all gates. |
| `on_repeated_failure` | `block` | `block` \| `escalate` | What to do when the failure limit is reached. |
| `max_gate_failures` | `3` | integer ≥ 1 | Consecutive-failure limit per task, aligned with `MAXIMUM_RETRY_THRESHOLD=3` in the circuit-breaker instructions. |

### `lifecycle_hooks.pre_execution`

Optional pre-execution actions (e.g. complexity sizing). Each action's `action`
field is namespaced `internal:` (a built-in) or `shell:` (an external command).

### Example

The following block is the reference configuration from the design document
([§5 Configuration Schema Contract](design-docs/autoharness-evals-gates-design.md)),
transcribed as valid YAML:

```yaml
lifecycle_hooks:
  pre_execution:
    - name: "estimate_complexity"
      condition: "task.size == null"
      action: "internal:estimate_tshirt_size"
      write_back: "backlogit update {task_id} --size {result}"

  pre_task_completion:
    validation_gates:
      - pattern: "docs/**/*.md"
        command: "engram verify {file_path}"
        timeout_seconds: 15

      - pattern: ".backlogit/queue/*.md"
        command: "backlogit doctor --target {file_path}"
        timeout_seconds: 5

      - pattern: "src/**/*.py"
        command: "pytest tests/ --lf"
        timeout_seconds: 60

telemetry:
  mode: "sqlite"
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true
```

> The `telemetry` block is accepted and stored but **not acted upon** in Phase 1.
> Gate execution does not read it. It exists so Phase 2 can consume it without a
> schema migration.

## Gate Policy

* **Atomic all-or-nothing.** A gate check runs every configured gate against every
  matching modified file. If **any** matched file fails, the whole check is
  **blocked** (exit 1). All-pass, no-match, and no-gates all produce exit 0.
* **Absolute vs. advisory.** `advisory` gates (or an `advisory` block policy) emit
  a warning and their failures never block completion. A per-gate `enforcement`
  overrides the block-level policy.
* **Repeated-failure circuit breaker.** Consecutive blocking failures for the same
  task are counted in `.autoharness/gate-state.json`. On the `max_gate_failures`-th
  (default 3rd) consecutive failure the task is **requeued** (or **escalated**, when
  `on_repeated_failure: escalate`) and a circuit-breaker checkpoint is written to
  `docs/memory/{YYYY-MM-DD}/circuit-break-gate-{task}.md`. A passing check resets
  the counter.
* **Operator `--force` bypass.** `--force` bypasses a blocking result. It is an
  **operator-only** control that must never be invoked from an agent surface, and
  every use is audited to `.autoharness/gate-force-audit.log` (P-005 telemetry
  style) and echoed in the correction report.
* **Correction report.** Every run emits a per-file pass/fail report enumerating
  each file's exit code and stderr, so an agent can self-heal deterministically.
  `--json` emits the same data as a machine-readable object.

The distinction between a **missing gate binary** (a configuration error — clear,
actionable message) and a **content failure** (the gate ran and returned non-zero)
is preserved in the result and the report.

## The `autoharness gate check` CLI Contract

```bash
autoharness gate check --base <ref> [--task <id>] [--head <ref>] \
                       [--workspace <path>] [--json] [--force]
```

| Flag | Default | Description |
|---|---|---|
| `--base <ref>` | *required* | Git ref to diff against (the task branch base). |
| `--task <id>` | — | Active backlog task ID, interpolated as `{task_id}`. |
| `--head <ref>` | `HEAD` | Git ref for the modified side of the diff. |
| `--workspace`, `-w` | `.` | Workspace root containing `.autoharness/config.yaml`. |
| `--json` | off | Emit the correction report as JSON. |
| `--force` | off | Operator-only bypass of a failing gate. Audited. |

Modified files are discovered with `git diff --name-only <base>...<head>`, returned
as forward-slash, repo-relative paths. If git is unavailable or the workspace is not
a repository, discovery degrades gracefully to an empty list with a warning — it
never crashes.

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | All matched gates passed, or no gates configured, or no files matched (or all failures advisory). |
| `1` | At least one matched file failed its gate (blocked). |
| `2` | Invalid arguments or invalid gate configuration. |

## Where the Harness Invokes Gates

Gates run at the **`pre_task_completion`** lifecycle point — after a task's work is
built and just before the task is marked complete in the backlog:

* In the **build-feature** skill, the gate check belongs in the **Post-Loop Quality
  Gates** step: after the harness loop passes (lint, format, full test suite) and
  before the **Commit / mark-task-complete** step. A blocking gate result prevents
  the task from moving to `done` and, on repeated failure, requeues it.
* Any custom **mark-task-complete** flow should invoke `autoharness gate check
  --base <task-branch-base> --task <id>` and treat a non-zero exit as a hard stop on
  completion (subject to the advisory/circuit-breaker policy above).

Because the gate subsystem is isolated (it must not import the install/tune modules),
it can be invoked as a standalone CLI step from any task-completion flow without
pulling in the rest of the harness engine.

## Kill-Switch Rollback

**To disable all gating with zero code change, remove or empty the `lifecycle_hooks`
block in `.autoharness/config.yaml`.**

An absent or empty `lifecycle_hooks` block makes gate configuration resolve to a
**disabled** state (`enabled = false`). `autoharness gate check` then reports that no
gates are configured and exits 0, and any task-completion flow proceeds exactly as it
did before gates existed. This is the fail-open-to-current guarantee: gating is
additive and fully reversible by configuration alone — no re-installation, no code
edit, no schema change.

### Runtime artifacts

`autoharness gate check` writes transient per-workspace state to a dedicated
runtime directory, **`.autoharness/gates/`**, which is gitignored so running a
gate check never dirties the working tree:

* `.autoharness/gates/gate-state.json` — consecutive-failure counters per task.
* `.autoharness/gates/gate-force-audit.log` — append-only `--force` bypass audit.

Circuit-breaker checkpoints (written on the 3rd consecutive failure) are the one
intentional exception: they are committed session memory under
`docs/memory/{date}/circuit-break-gate-{task}.md`.

## References

* [Deterministic Gates, Telemetry & Evaluation Engine — design document](design-docs/autoharness-evals-gates-design.md)
* [Gate policy deliberation](decisions/2026-06-30-gate-policy-deliberation.md)
* [Validation-gates config schema deliberation](decisions/2026-06-30-validation-gates-config-schema-deliberation.md)
* [`validation-gates` JSON Schema (1.0.0)](../schemas/validation-gates/1.0.0.schema.json)
* [Circuit Breaker instructions](../.github/instructions/circuit-breaker.instructions.md)

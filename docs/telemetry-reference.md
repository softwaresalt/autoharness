---
title: Telemetry Reference
description: Execution Epoch schema, the autoharness telemetry record emission contract, repo-local SQLite/JSONL sinks, and the telemetry.mode none kill-switch
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Validation Gates](gates-reference.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md)

## Overview

Telemetry lets autoharness measure its own efficiency ("Best Outcome at the Best
Price") by capturing high-fidelity **Execution Epochs** — one structured record
per task-completion boundary. Each epoch carries the route configuration, the
economic payload, the operational reality, and the absolute gate outcome, and is
written to a repo-local SQLite aggregator plus an optional JSONL stream.

This is **Phase 2 (capture core)** of the Deterministic Gates, Telemetry &
Evaluation Engine design — see [the design document](design-docs/autoharness-evals-gates-design.md) §4
and §6.3. The headless evaluation runner, deterministic reviewer matrix, and
pre-execution sizing gate are later shipments and are intentionally *not*
implemented here.

### The no-execution-loop framing

autoharness's CLI is an **install/tune tool**, not a live agent execution host.
There is **no in-process execution loop** to wrap. The design doc's "wrap the
execution loop to log …" is therefore delivered as a **self-contained CLI
capability** (`autoharness telemetry record`) plus this documented **emission
contract**: the harness runtime (Copilot CLI / VS Code / the build-feature
skill) already knows its route, token/COGS/duration, CLI tools used, and gate
exit codes at task-completion time, and it hands those to autoharness through the
record command. autoharness owns the **epoch schema** and the **sinks**, not the
collection of raw runtime signals.

### Fail-open by design

Telemetry is **observational and off the completion critical path**. An absent or
`mode: none` telemetry block disables all emission (behavior identical to an
install without telemetry). A failing or misconfigured sink is reported but never
raises — `autoharness telemetry record` returning non-zero MUST NOT be
interpreted by the harness as a completion blocker.

## Configuration

Telemetry is configured under a `telemetry` block in the workspace
`.autoharness/config.yaml`, validated against the versioned
[`validation-gates` JSON Schema](../schemas/validation-gates/1.0.0.schema.json)
(the `telemetry` definition). The block is **entirely optional**.

```yaml
telemetry:
  mode: "sqlite"                                    # sqlite | none (default none)
  database_path: ".autoharness/metrics/execution_epochs.db"
  emit_jsonl: true                                  # append one JSON epoch per line
```

| Field | Required | Default | Description |
|---|---|---|---|
| `mode` | no | `none` | `sqlite` enables the SQLite aggregator; `none` disables all telemetry (kill-switch). |
| `database_path` | no | `.autoharness/metrics/execution_epochs.db` | Repo-relative path to the local SQLite DB. Resolved against the workspace root and **confined to it** (see below). |
| `emit_jsonl` | no | `false` | When `true`, also append a JSONL epoch stream alongside the DB. |

Telemetry artifacts are **confined to the workspace**. `database_path` (and the
JSONL stream derived from it) is resolved against the workspace root, and the
resolved real path must live **inside** the workspace. A `database_path` that
escapes the repo — an absolute path outside the workspace, or a relative path
using `..` traversal — is rejected and telemetry **fails open to disabled** (a
warning is logged; nothing is emitted outside the repo). The **default**
location `.autoharness/metrics/` is gitignored, so default emission never dirties
the working tree. If you override `database_path` to an in-workspace location
*outside* `.autoharness/metrics/`, confinement still holds, but those artifacts
are **not** covered by the default gitignore rule — add your own ignore entry so
emission does not produce tracked-file changes.

The commented activation guidance ships through
[`templates/harness-config.yaml.tmpl`](../templates/harness-config.yaml.tmpl) so
target workspaces receive it through the normal install/tune flow.

## Execution Epoch Schema

An `ExecutionEpoch` composes the four design-§4 payload classes. The serialized
shape below (`to_record()`) is the **stable contract** shared by both sinks and
the external ingestion boundary.

```json
{
  "epoch_id": "b6b1…",
  "schema_version": "1.0.0",
  "task_id": "051.001-T",
  "timestamp": "2026-07-01T08:53:00+00:00",
  "route":      { "models": ["claude-opus-4.8", "gpt-5.4-mini"] },
  "economics":  { "input_tokens": 1200, "output_tokens": 800, "cogs_usd": 0.042, "duration_seconds": 93.5 },
  "operations": { "cli_tools": ["git", "pytest", "backlogit"] },
  "outcome":    { "gate_exit_codes": [0, 0, 1] }
}
```

| Payload class | Field(s) | Meaning |
|---|---|---|
| `RouteConfiguration` | `models` | The models used (first element is the primary model). |
| `EconomicPayload` | `input_tokens`, `output_tokens`, `cogs_usd`, `duration_seconds` | Cost and duration of the epoch. |
| `OperationalReality` | `cli_tools` | The CLI tools actually invoked. |
| `AbsoluteOutcome` | `gate_exit_codes` | The gate exit code(s); any non-zero marks the epoch `blocked`. |

`task_id` and the four payload classes are **required**; a payload missing any of
them is rejected with exit code `2`. `epoch_id`, `timestamp`, and
`schema_version` are auto-populated when omitted.

## Emission Contract

The harness runtime invokes the record command at execution close, supplying the
epoch payload as a JSON object via `--from-json <path>` or stdin:

```bash
# From a file the runtime wrote at task close:
autoharness telemetry record --from-json epoch.json --workspace .

# Or piped on stdin:
Get-Content epoch.json | autoharness telemetry record --workspace .
```

The command loads the workspace `telemetry` config, constructs an
`ExecutionEpoch` from the payload, and routes it to every enabled sink.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Epoch recorded, **or** telemetry disabled (no-op), **or** a sink failed (fail-open — reported, not blocking). |
| `2` | Invalid arguments, or a malformed/incomplete epoch payload. |

## Sinks

### SQLite aggregator (repo-local)

Each epoch is written as one row to the `execution_epochs` table in
`.autoharness/metrics/execution_epochs.db` (§6.3 — telemetry is kept **repo-local**,
not global). Parent directories are auto-created; the connection uses **WAL**
journaling with short-lived per-write connections so concurrent emissions do not
contend. Columns support quantitative metric queries:

```text
epoch_id, schema_version, task_id, timestamp,
primary_model, models,
input_tokens, output_tokens, total_tokens,
cogs_usd, duration_seconds,
cli_tools, gate_exit_codes, blocked
```

### JSONL stream (emit-only)

When `emit_jsonl: true`, each epoch is also appended as **one well-formed JSON
object per line** to `execution_epochs.jsonl` alongside the DB. This sink is
**emit-only**: the external relational schema and the ingestion path that consumes
the stream are an [agent-engram](design-docs/autoharness-evals-gates-design.md)
concern (design §4) and are **not** implemented by autoharness. autoharness writes
JSONL and stops at the file boundary.

## Runtime-Artifact Isolation

Everything under `.autoharness/metrics/` — the SQLite DB, its `-wal`/`-shm`
sidecars, and the JSONL stream — is **gitignored** so emission never dirties a
consumer's working tree. This applies the same runtime-artifact learning
established for `.autoharness/gates/` and `.autoharness/staging/` in Phase 1.

## Kill-Switch Rollback

Telemetry has a **zero-code kill-switch**: set `telemetry.mode: none` (or remove
the `telemetry` block entirely) in `.autoharness/config.yaml`. All emission stops
immediately and the harness fails open to its prior behavior. To also reset the
local data, delete the `.autoharness/metrics/` directory.

## Related

- [Validation Gates Reference](gates-reference.md) — Phase 1 gate execution surface whose exit codes become the epoch's `AbsoluteOutcome`.
- [Design Document](design-docs/autoharness-evals-gates-design.md) — §4 (Phase 2) and §6.3 (repo-local telemetry).

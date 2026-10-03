---
title: Validation Gates Reference
description: Deterministic pre-task-completion validation gates — configuration schema, gate policy, the autoharness gate check CLI contract, the optional detector registry and gate pre-review reader, the kill-switch rollback, and the evidence-capturing autoharness shipment cascade-close command with the closure-evidence gate's close-path checks
doc_type: reference
source: docs/gates-reference.md
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md)

## Overview

Deterministic validation gates let the harness enforce **non-LLM, exit-code-based
checks** on the files a task modified, before that task is allowed to complete.
Instead of trusting a model loop to decide whether documentation, backlog items,
or source files are valid, the harness runs operator-authored commands and blocks
completion when any of them fail.

This is **Phase 1** of the Deterministic Gates & Evaluation Engine design. It
delivers the gate execution surface only. Telemetry capture (SQLite epochs, JSONL
emission) is **Phase 2** — see the [Telemetry Reference](telemetry-reference.md)
and [the design document](design-docs/autoharness-evals-gates-design.md) §4.

Gates are **entirely opt-in**. When no `lifecycle_hooks` block is configured, the
harness behaves exactly as it did before gates existed (fail-open-to-current). See
the [Kill-Switch Rollback](#kill-switch-rollback) below.

## Configuration Schema

Gates are configured under a `lifecycle_hooks` block in the workspace
`.autoharness/config.yaml`. The block is validated against the versioned
[`validation-gates` JSON Schema](../schemas/validation-gates/1.1.0.schema.json).
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

      - pattern: ".backlog/queue/*.md"
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

> For legacy backlogit workspaces, use `.backlogit/queue/*.md` in place of the
> `.backlog/queue/*.md` example above. New installs default to `.backlog/`, and
> both roots present at once should be resolved manually before relying on a
> path-specific gate.

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
  When gates run, JSON reports also include a top-level `repeated_failure`
  object so callers can consume the circuit-breaker state without parsing the
  human checkpoint file:

  ```json
  {
    "repeated_failure": {
      "count": 2,
      "threshold": 3,
      "reached": false,
      "action": "block"
    }
  }
  ```

  `count` is the consecutive blocking-failure count for the task after this run,
  `threshold` is `max_gate_failures`, `reached` is true when `count >= threshold`,
  and `action` is the configured `on_repeated_failure` value (`block` or
  `escalate`). Passing gate runs reset `count` to `0` and report
  `reached: false`. When `--no-count` is used, the field reports the current
  stored counter without incrementing or resetting it. The field is additive
  metadata; exit codes remain unchanged.

The distinction between a **missing gate binary** (a configuration error — clear,
actionable message) and a **content failure** (the gate ran and returned non-zero)
is preserved in the result and the report.

## The `autoharness gate check` CLI Contract

```bash
autoharness gate check --base <ref> [--task <id>] [--head <ref>] \
                       [--workspace <path>] [--json] [--force] [--no-count]
```

| Flag | Default | Description |
|---|---|---|
| `--base <ref>` | *required* | Git ref to diff against (the task branch base). |
| `--task <id>` | — | Active backlog task ID, interpolated as `{task_id}`. |
| `--head <ref>` | `HEAD` | Git ref for the modified side of the diff. |
| `--workspace`, `-w` | `.` | Workspace root containing `.autoharness/config.yaml`. |
| `--json` | off | Emit the correction report as JSON. |
| `--force` | off | Operator-only bypass of a failing gate. Audited. Cannot be combined with `--no-count`. |
| `--no-count` | off | Advisory/manual pre-check mode. Do not increment or reset the repeated-failure counter. Cannot be combined with `--force`. |

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

## Detector Registry & `autoharness gate pre-review` (S1)

Alongside the `pattern` → `command` validation gates above, the same
`.autoharness/config.yaml` may declare a top-level, optional **`detectors`**
block: a registry of report-only, non-blocking "pre-review" nodes evaluated by
`autoharness gate pre-review`, independent of the `pre_task_completion`
enforcement path.

### `detectors` schema block

The `detectors` block is a JSON array of detector nodes validated against the
same versioned [`validation-gates` JSON Schema (1.1.0)](../schemas/validation-gates/1.1.0.schema.json)
used by `lifecycle_hooks` — runtime validation always resolves the **versioned**
document (`schemas/validation-gates/1.1.0.schema.json`), never the pointer file
directly; the pointer (`schemas/validation-gates.schema.json`) is kept
structurally identical to the versioned schema (differing only in `$id`) so the
two never drift. The prior `1.0.0.schema.json` mirror (published in 052-S,
before the `detectors` block existed) remains published unchanged as an
immutable historical snapshot; the `detectors` block first appears in `1.1.0`.

Each detector node declares:

| Field | Required | Description |
|---|---|---|
| `node_id` | yes | `det:<domain>/<detector_id>@<version>` (e.g. `det:D-ART/ART-01@1`). |
| `applies_when` | yes | Applicability predicate: `changed_paths_any`, `shipment_has_items_of_type`, `workspace_surfaces_any`, or `always`. |
| `producer.kind` | yes | Evidence-producer kind. **Only `pure` is implemented in S1** — `command` is schema-declared for forward compatibility but is currently rejected at load time (`producer.kind 'command' is not implemented in S1`). |
| `producer.ref` | yes | `module:callable` reference; must resolve inside the `autoharness.detectors` namespace. |
| `validator.ref` | yes | `module:callable` reference for the evidence-to-`NodeResult` validator; same namespace constraint. |
| `depends_on` | no | Other `node_id`s this node depends on (validated for existence; cycles are rejected). |
| `severity` | yes | Detector severity classification. |
| `mode` | yes | Must be `report_only` in S1 — any other value is rejected at load time. |
| `remediation` | yes | `class`, `hint`, `target_refs`, `authority` guidance surfaced alongside a failing result. |

A missing or absent `detectors` key is a valid, backward-compatible "zero
detector nodes" configuration (exit 0, nothing evaluated). A **present but
malformed** `detectors` block — non-mapping top-level YAML, invalid YAML
syntax, or a value that fails schema validation — is a fail-closed
`DetectorRegistryError` (exit 2), never a silent zero-nodes fallback.

### The canonical detector result contract

Every detector node produces exactly one `NodeResult` with a single canonical
`status` field drawn from a closed set of named values (there is no separate
`verdict` field in the emitted report — `status` is the sole source of truth).
Detector evaluation is always **report-only**: even a `failed` status never
blocks a build or a merge by itself; it is evidence for downstream human or
gate consumers.

### `autoharness gate pre-review`

```bash
autoharness gate pre-review --base <ref> [--json]
```

| Flag | Default | Description |
|---|---|---|
| `--base <ref>` | *required* | Git ref to diff against; head is always `HEAD`. Both refs must resolve to a full 40-hex-character SHA through the same option-injection-safe resolution used by `gate check` — an unresolvable or option-like `--base` exits 2 with no report written. |
| `--json` | off | Emit the pre-review payload as JSON. |

The command loads the workspace's `detectors` registry, evaluates each node's
applicability against the changed-path/shipment/workspace-surface context, runs
every applicable node's producer/validator pair, and emits an append-only,
epoch-keyed report under **`.autoharness/gates/pre-review/{head_sha}-{fingerprint}.json`**
(never overwritten — a new epoch key is derived whenever the registry version,
schema version, or resolved tool versions change).

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Registry loaded and evaluated (including when individual detector nodes report `failed` — pre-review is report-only and never blocks on a normal finding). |
| `2` | Invalid detector registry (malformed config, unknown ref, cycle, disallowed `producer.kind`/`mode`), an unresolvable/option-like `--base`/head ref, or any evaluated node reporting `status: "invalid"` (a detector-implementation SDK contract violation — e.g. a validator returning something other than a `NodeResult` — distinct from a normal report-only `failed`/`insufficient_evidence` finding). |

Codes `1` and `3` are never emitted by this command; any occurrence is a
regression.

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

## Shipment Close Commands

`autoharness shipment cascade-close` (192-F) captures durable evidence for every
shipment close. It lives under `autoharness shipment`, not `autoharness gate`,
because it is **not a gate**: a gate is a read-only, exit-code-based check, while
`cascade-close` writes an evidence record and, in its mutating mode, invokes the
destructive `backlogit shipment ship` cascade. The read-only check over its output is
the `closure-evidence` gate described in
[Closure-evidence gate: close-path checks](#closure-evidence-gate-close-path-checks).

The `shipment-reconcile` skill owns the routing. Every close, on either close path,
starts with `--classify-only`. CASCADE runs only through the mutating command, which
needs the same operator approval as a direct `backlogit shipment ship` call. A direct
`backlogit shipment ship` CLI call or `backlogit_ship_shipment` MCP call is a P-005
deviation, and the closure-evidence gate refuses the closure it produces.

### Invocation and modes

```text
autoharness shipment cascade-close --shipment <S> --feature <F> --sha <merge_sha>
                      --message <text> --author <name> [--timeout <seconds>]
                      [--workspace <path>] [--json]
autoharness shipment cascade-close --classify-only [--replace-pre-close]
                      --shipment <S> --feature <F> --sha <merge_sha>
                      [--workspace <path>] [--json]
```

| Mode | Behavior | Approval |
|---|---|---|
| plain `--classify-only` | Re-runs the classifier, probes the engine, selects the close path, and writes a new `pre_close` record. No-clobber: an existing `pre_close` record exits 2 and is left untouched. Never invokes the cascade. | None |
| `--classify-only --replace-pre-close` | Overwrites an existing `pre_close` record through the pre_close takeover (a compare-and-swap on the prior `run_id`). | Destructive-command approval |
| mutating (no `--classify-only`) | Invokes `backlogit shipment ship` only when the selected close path is `CASCADE`, then verifies the postconditions and writes the `post_close` record. `--message` and `--author` are required; `--timeout` is 30-900 seconds (default 120). | Destructive-command approval |

The evidence record is written to the fixed path
`docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json`. That path
is never derived from the closure directory. The record is committed with the
closure artifact, kept permanently, and never hand-edited. Its `phase` is
`pre_close`, `invoking`, or `post_close`. The command writes the record before the
close; if that write fails, nothing is invoked.

### Engine-semantics gate and close-path selection

No cascade runs unless `select_close_path` selects `CASCADE`. That requires a
classifier verdict of `CASCADE` and an engine-semantics verdict of `VERIFIED` from
`assess_cascade_engine_semantics`, probed on the CLI surface the command invokes
(released builds only). Otherwise the command records the verdict and exits 3,
having invoked nothing. Immediately before invocation, the mutating mode re-probes
the engine and revalidates the snapshot. Any difference, including a difference from
the `cascade`-selected `--classify-only` record, exits 4 with nothing mutated. Exit 4
is never answered with `SAFE_CLOSE`.

### Exit codes

| Code | Meaning | `mutation_possible` (mutating mode) | Operator review |
|---|---|---|---|
| `0` | Mutating: every postcondition passed. `--classify-only`: `CASCADE` selected. | `yes` | No |
| `2` | Input, I/O, no-clobber refusal, disposition planning error, or pre-invocation write failure. Nothing mutated. | `no` | No |
| `3` | The selected close path is not `CASCADE` (classifier `SAFE_CLOSE`, or engine `UNVERIFIED`). Verdict recorded, nothing invoked. | `no` | No |
| `4` | Pre-invocation revalidation drift: snapshot, engine re-probe, binary hash, or a difference from the `cascade`-selected `--classify-only` record. Nothing invoked. Never answered with `SAFE_CLOSE`. | `no` | Yes |
| `5` | A postcondition failed, including a non-empty `post_close.linked_deliberation_drift`. | `yes` | Yes |
| `6` | `backlogit` exited non-zero, timed out, or its output did not parse. | `indeterminate` | Yes |
| `7` | The pair lock is already held, or an existing evidence record is an `invoking` record, unreadable, ambiguous, or names a different pair. Nothing invoked. | `unknown` | Yes |
| `8` | The post-close evidence write failed after invocation. | `yes` | Yes |

Exits 5, 6, 7, and 8 forbid committing the backlog root, re-running
`cascade-close`, calling `backlogit shipment ship` directly, or substituting
`SAFE_CLOSE` until an operator reviews the backlog state and the record.

**Pair lock (exit 7).** Every run takes a per-pair lock, created exclusively at
`.autoharness/gates/cascade-close/{shipment_id}-{feature_id}.lock` (Git-ignored),
and releases it before exiting. A lock the command finds already present is never
broken automatically: the run exits 7 and names the lock path. Because a finishing
run releases its own lock, a lingering lock means a run for that pair is still in
progress or was killed or crashed. Removing a stale lock is an **operator-only**
action, taken only after the operator confirms no `cascade-close` run for that pair
is still in progress and reviews the evidence record (an `invoking` phase means a
prior run may have mutated the backlog). An agent must never delete, rename, or
overwrite the lock file; it HALTs on exit 7 instead.

### `--json` output

`--json` emits one JSON object:

| Field | Meaning |
|---|---|
| `mode` | `mutating`, `classify_only`, or `replace_pre_close` |
| `exit_code` | The exit code above |
| `evidence_path` | The evidence record path, or `null` |
| `phase_written` | The record phase this run wrote, or `null` |
| `classifier_verdict` | `CASCADE` or `SAFE_CLOSE` from the fresh classifier run |
| `engine_verdict` | `VERIFIED` or `UNVERIFIED` from the engine-semantics gate |
| `selected_close_path` | The close path `select_close_path` selected |
| `mutation_possible` | `no`, `yes`, `indeterminate`, or `unknown` |
| `postcondition_verdict` | `pass`, `fail`, or `null` when no postconditions ran |
| `failures` | A list of failure messages |
| `operator_action` | `none` for exits 0, 2, and 3; otherwise `review_required` |

### Evidence record fields

The record's selection and disposition fields:

* `pre_close.engine_semantics`: `verdict`, `reason`, `probed_version`,
  `minor_line`, `probed_commit`, `probe_surface`, and `invocation_surface` (always
  `cli`). The record carries no probe excerpt here; the probe's stdout excerpt is
  `tool.version_excerpt`.
* `pre_close.close_path_selection`: `selected_close_path` and `reason`, as
  `select_close_path` returns them.
* `pre_close.linked_deliberation_disposition`: the planned disposition of each
  linked deliberation (`dispositions`, `unresolved_references`, `read_failures`,
  and `planning_error`). A `retained_*` outcome does not halt. The command never
  archives a deliberation; the `shipment-reconcile` Linked-Deliberation Disposition
  step (P-015 INV-12) reads these inputs from the record after the close and remains
  the only archiver.
* `pre_close.observation_set`: recorded only on a selected `SAFE_CLOSE`.
* `post_close.allowed_ids` and `post_close.required_ids`: flat sets computed from
  the `pre_close` section only. `allowed_ids` is the manifest items plus the
  shipment ID. `required_ids` is the shipment ID, plus the qualifying feature IDs,
  plus every manifest item that was not already archived before the close.
* `post_close.parsed_result`: the parsed `backlogit shipment ship` result
  (`shipment_id`, `shipment_status`, `archived_ids`, `returned_ids`, and
  `commit_sha`). Its `shipment_id` must equal the record's top-level
  `shipment_id`.
* Derived `post_close` fields are recomputed, not trusted. Record validation
  recomputes `allowed_ids` and `required_ids` from `pre_close`, both set
  differences (`unexpected_archived` and `missing_required`) from
  `parsed_result.archived_ids`, and `shipment_archived_shipped` from the recorded
  re-read shipment status. A stored value that differs from its recomputation is
  rejected. A `cascade` record also requires `parsed_result.shipment_status:
  shipped`.
* `post_close.linked_deliberation_drift`: a list of disposition-set deliberations
  that the cascade archived or modified. That is engine drift; a non-empty list
  fails the postconditions (exit 5).

### Closure-evidence gate: close-path checks

`autoharness gate closure-evidence` stays read-only. After its existing checks
(workspace containment, input, filename, `frontmatter_predicate`, and
discoverability) pass, it checks the close path. Either refusal exits 1:

| `failed_check` | Refused when |
|---|---|
| `close_path` | The closure artifact does not declare `close_path: cascade` or `close_path: safe_close`. |
| `close_evidence` | `close_evidence` is not the canonical `docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json` path (relative POSIX, no `..`, no drive or UNC prefix), is not a regular file of at most 512 KiB reached through no symlink or junction, or does not validate as a record whose selected close path equals the declared `close_path`. Also refused: a `merge_commit` key that differs from the record's `merge_commit_sha`, and, for `safe_close`, a failed observation-set re-check. |

The observation-set re-check requires every recorded entry to remain at its recorded
backlog path and location with its recorded SHA-256. Every entry recorded `missing`
must still be missing, and each path is containment-checked before any read. The gate
never reads a disposition outcome and does not re-check the disposition snapshot. A
disposition-set deliberation is re-checked only as an ordinary observation-set entry,
where the `SAFE_CLOSE` observation set includes it.

**Enforcement scope.** The close-path checks are enforced only at write time: the
`cascade-close` command validates its `pre_close` record before writing it, and
this gate checks the closure artifact's `close_path`, `close_evidence`, and the
record it names before the artifact is committed. The `pipeline-topology` gate's
predecessor-closure predicate (`closure_complete` in
`src/autoharness/gates/topology.py`) does **not** enforce them: it reads only
`compaction_status` (or legacy `compaction`) and `closure_status` with its
`conditions`, and never reads `close_path`, `close_evidence`, or the evidence
record. A successor's `pre_claim` therefore does not re-verify the close path, so
skipping this gate before commit is not caught downstream.

**Closures recorded before 192-F.** Closure artifacts committed before 192-F carry
no `close_path` or `close_evidence` key and have no evidence record, so they are not
expected to pass the close-path checks, and a `close_path` refusal on one of them is
not a defect. They remain predecessor-closure evidence for the topology gate, which
never checked these keys. Do not backfill the keys into them or fabricate an
evidence record for them.

With `--json`, the result also carries `warnings[]`, a list of non-blocking notes:

* the closure artifact has no `merge_commit` key, so the record's `merge_commit_sha`
  was not cross-checked;
* the `SAFE_CLOSE` observation set is empty, so the re-check was vacuous.

A warning never changes the exit code. The structured-evidence request to the
upstream `backlogit` maintainers is recorded in
[the backlogit `shipment ship` structured-evidence request](bugs/2026-09-27-backlogit-shipment-ship-structured-evidence-request.md).
autoharness does not depend on it.

## References

* [Copilot-Review Merge Gate Reference](copilot-review-gate.md) — the separate fail-closed `autoharness gate copilot-review` CLI and P-018
* [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) — the deterministic shipment/worktree topology gate (P-001/P-016), its `pre_claim`/`post_claim`/`lifecycle`/`ambient` phase contract, and the `CLAIM_NOT_OBSERVED` retry-required outcome
* [DAG Readiness Gate Reference](dag-readiness-gate.md) — the read-only `autoharness gate dag-readiness` ready-set/critical-path/downstream-dependents report over the same shipment-blocks DAG, its deterministic next-eligible resumption-cursor advisory, and its permanent no-scheduler NON-GOAL
* [Deterministic Gates, Telemetry & Evaluation Engine — design document](design-docs/autoharness-evals-gates-design.md)
* [Gate policy deliberation](decisions/2026-06-30-gate-policy-deliberation.md)
* [Validation-gates config schema deliberation](decisions/2026-06-30-validation-gates-config-schema-deliberation.md)
* [`validation-gates` JSON Schema (1.1.0)](../schemas/validation-gates/1.1.0.schema.json)
* [Circuit Breaker instructions](../.github/instructions/circuit-breaker.instructions.md)

---
title: DAG Readiness Gate Reference
description: The read-only autoharness gate dag-readiness CLI — ready-set, critical-path, and downstream-dependents reporting over backlogit's existing shipment-blocks DAG; the --json output shape; the read-only/existence-guarded/DEGRADED contract; and the permanent no-scheduler NON-GOAL (P-001/P-016)
doc_type: reference
source: docs/dag-readiness-gate.md
---

> **Navigation**: [README](../README.md) · [Validation Gates Reference](gates-reference.md) · [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) · [Copilot-Review Merge Gate Reference](copilot-review-gate.md) · [Primitives](primitives.md)

## Overview

The **dag-readiness gate** is a deterministic, non-LLM, **read-only** reporting
command that surfaces visibility into backlogit's existing shipment-blocks DAG —
the same graph the [pipeline-topology gate](pipeline-topology-gate.md) already
reads (`ShipmentState.blocking_predecessor_ids`, sourced from each shipment
record's `dependencies` frontmatter field). It computes and reports three things:

1. The **ready-set** — live `queued` shipments whose every predecessor has
   reached a genuine no-longer-blocking terminal closure.
2. The **critical path** — the longest chain in the blocks DAG by node count.
3. **Downstream dependents** — for every shipment, the full transitive closure
   of shipments that (directly or indirectly) depend on it.

This is Phase 1 of the deferred DAG-visibility follow-up from spike `001-SP`
(stash `33CC445C`). It is **visibility/reporting only**: it introduces no
scheduler, no mutation, and no parallelism. See
[Permanent NON-GOAL](#permanent-non-goal-no-scheduler-no-parallel-execution)
below.

Cycle detection is **owned by this analyzer**, not the reused shipment-blocks
reader — the reader performs no cycle detection of its own (see
[Cycle Detection](#cycle-detection)).

## The `autoharness gate dag-readiness` CLI Contract

```bash
autoharness gate dag-readiness [--workspace <path>] [--json]
```

| Flag | Default | Description |
|---|---|---|
| `--workspace`, `-w` | `.` | Workspace root containing `.backlogit/`. |
| `--json` | off | Emit the report as a machine-readable JSON object (see [`--json` Output Shape](#--json-output-shape)). |

All reads are performed through the same read-only `FilesystemTopologyReaders`
interface the pipeline-topology gate uses; this command performs **no
backlogit or git mutation on any path**.

## Ready-Set Definition

The ready-set contains **ONLY** live `queued` shipments (`status == "queued"`)
whose **every** predecessor block has reached a genuine no-longer-blocking
terminal closure:

* A predecessor counts as **finished** only when it is completed with a valid
  `shipped`/`done` closure (the same `shipped`-terminal test the
  pipeline-topology gate's `PREDECESSOR_NOT_SHIPPED` check already applies).
* A `queued` **or** `active` predecessor is **UNFINISHED and BLOCKS** its
  dependent. An `active` shipment is in-progress work — it is **not** a
  terminal state and **not** non-blocking.
* A predecessor in an `abandoned`, malformed, or **unknown** state (a
  predecessor id that does not resolve to any shipment in the graph at all)
  is **FAIL-CLOSED**: treated as unfinished, never casually treated as
  terminal-ready.
* Separately, a shipment that is itself `active`, `shipped`, `abandoned`, or
  archived-only (no live `queued` record) is **NEVER** a ready candidate —
  even when it has no blocking predecessors at all (dependency-free).

This mirrors, and deliberately reuses the same terminal-closure test as, the
pipeline-topology gate's `_shipment_readiness_check`/`PREDECESSOR_NOT_SHIPPED`
logic — dag-readiness does not introduce a second, divergent definition of
"finished".

## Critical Path

The critical path is the **longest chain** in the blocks DAG by **node
count** — shipments are not time-weighted. Ties are broken deterministically
(lowest shipment id first) so the reported path is stable across runs over
the same graph.

## Downstream Dependents

For every shipment node, `downstream_dependents` reports the **full
transitive closure** of shipments that directly or indirectly declare it as
a blocking predecessor — not just immediate dependents. A node with no
dependents reports an empty list.

## Cycle Detection

Cycle detection is **owned by this analyzer** (`compute_dag_readiness` in
`src/autoharness/gates/topology.py`), not by the reused shipment-blocks
reader — `FilesystemTopologyReaders.list_shipments()` performs no cycle
detection of its own; it only returns each shipment's declared
`blocking_predecessor_ids`.

When a cycle is detected anywhere in the graph, the analyzer **degrades
safely**: it reports `cycle_detected: true` and the involved `cycle_nodes`,
and it **never fabricates** a `ready_set` or `critical_path` — both are
reported empty for that run. This preserves the read-only, fail-closed
posture already established by pipeline-topology's P-001/P-016 checks.

## `--json` Output Shape

```json
{
  "ready_set": ["003-S"],
  "critical_path": ["001-S", "002-S", "003-S"],
  "downstream_dependents": {
    "001-S": ["002-S", "003-S"],
    "002-S": ["003-S"],
    "003-S": []
  },
  "cycle_detected": false,
  "cycle_nodes": [],
  "degraded_reason": null,
  "status": "ok"
}
```

| Field | Type | Description |
|---|---|---|
| `ready_set` | array of shipment ids | See [Ready-Set Definition](#ready-set-definition). Sorted, deterministic. |
| `critical_path` | array of shipment ids | See [Critical Path](#critical-path). Ordered from the earliest predecessor to the latest dependent. |
| `downstream_dependents` | object (shipment id → array of shipment ids) | See [Downstream Dependents](#downstream-dependents). One entry per known shipment node. |
| `cycle_detected` | boolean | `true` when a cycle was found anywhere in the graph. When `true`, `ready_set` and `critical_path` are always `[]`. |
| `cycle_nodes` | array of shipment ids | The shipment ids participating in the detected cycle. Empty when `cycle_detected` is `false`. |
| `degraded_reason` | string or `null` | Populated only when `status` is `"degraded"` — see [Existence Guard and DEGRADED Behavior](#existence-guard-and-degraded-behavior). |
| `status` | `"ok"` \| `"empty"` \| `"degraded"` | `"empty"` when zero shipments exist; `"degraded"` when the backlog was unreachable; `"ok"` otherwise. |

The human-readable (non-`--json`) report renders the same information,
omitting empty downstream-dependents entries for readability.

## Existence Guard and DEGRADED Behavior

* **Existence-guarded**: when the workspace has zero shipments, the report
  is empty (`ready_set: []`, `critical_path: []`,
  `downstream_dependents: {}`, `status: "empty"`) and the command exits
  **0**.
* **DEGRADED**: when the backlog is unreachable (e.g. a missing or
  unreadable `.backlogit/` directory, or a malformed shipment record — the
  same conditions that raise `BacklogUnavailableError` in
  `autoharness.gates.topology`), the command reports `status: "degraded"`
  with a `degraded_reason`, and exits **0** (non-fatal/advisory). It never
  fabricates a graph.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Report produced — `ok`, `empty`, or `degraded`. Always non-fatal; there is no BLOCK verdict. |
| `2` | Invalid arguments (unknown flag, missing value). |

Unlike [pipeline-topology](pipeline-topology-gate.md) or
[copilot-review](copilot-review-gate.md), dag-readiness is a pure reporting
command — it has no fail-closed BLOCK outcome of its own.

## Permanent NON-GOAL: No Scheduler, No Parallel Execution

This gate is **visibility/reporting only**. It does not, and will never:

* Claim, activate, or mutate any shipment or task.
* Select or execute a "next" shipment automatically.
* Enable or encourage multiple active shipments, multiple implementation
  worktrees, or any form of parallel execution.

The at-most-one-active-shipment invariant (P-001) and the single
implementation worktree/branch invariant (P-016), enforced by the
[pipeline-topology gate](pipeline-topology-gate.md), are fully preserved.
A Phase 2 deterministic next-eligible resumption helper remains
**operator-gated** and deferred in the living tracker (stash `33CC445C`);
it is explicitly out of scope here.

## References

* [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) — the reused
  shipment-blocks reader (`ShipmentState`, `FilesystemTopologyReaders`) and
  the P-001/P-016 invariants this gate preserves
* [Validation Gates Reference](gates-reference.md)
* [Copilot-Review Merge Gate Reference](copilot-review-gate.md)

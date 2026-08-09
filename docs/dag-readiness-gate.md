---
title: DAG Readiness Gate Reference
description: The read-only autoharness gate dag-readiness CLI — ready-set, critical-path, and downstream-dependents reporting over backlogit's existing shipment-blocks DAG; the deterministic next-eligible resumption-cursor advisory; the --json output shape; the read-only/existence-guarded/DEGRADED contract; and the permanent no-scheduler NON-GOAL (P-001/P-016)
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

Phase 2, delivered by feature `115-F` (deliberation `014-DL`, stash `33CC445C`
Phase 2), adds a **deterministic next-eligible resumption-cursor advisory** on
top of this same read-only substrate. See
[Next-Eligible Resumption Cursor](#next-eligible-resumption-cursor) below.

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

## Next-Eligible Resumption Cursor

Feature `115-F` (deliberation `014-DL`, stash `33CC445C` Phase 2) adds a
**deterministic, READ-ONLY resumption-cursor advisory** — `next_eligible` —
computed over this same read-only substrate. It answers "which single
shipment should a human or the Orchestrator look at next?" without claiming,
activating, or mutating anything. See the
[Permanent NON-GOAL](#permanent-non-goal-no-scheduler-no-parallel-execution)
section below for the non-negotiable boundary this advisory operates within.

### Seven-Outcome Resolution Order and Ownership Split

The gate exposes **seven** observable `next_eligible_reason` outcomes,
evaluated in this order (anomaly-first, over the full unfiltered shipment
enumeration):

| # | Reason | Owner |
|---|---|---|
| 1 | `degraded` | **CLI** (`src/autoharness/cli.py`) |
| 2 | `cycle_detected` | Analyzer (`compute_next_eligible`) |
| 3 | `ambiguous_provenance` | Analyzer |
| 4 | `multi_active_anomaly` | Analyzer |
| 5 | `resume_active` | Analyzer |
| 6 | `ready_set_head` | Analyzer |
| 7 | `no_candidates` | Analyzer |

**Ownership split (normative).** Outcome 1, `degraded`, is synthesized by the
CLI, in the `BacklogUnavailableError` handler, **before** the analyzer is ever
invoked — `readers.list_shipments()` raises before a `shipments` tuple or a
`DagReadinessResult` ever comes into existence, so there is nothing to hand
the analyzer on that path. Outcomes 2–7 are `compute_next_eligible`'s **six**
branches (`src/autoharness/gates/topology.py`); the analyzer is a pure
function of already-successfully-read data and **never** emits `degraded` —
it accepts no `is_degraded`/`degraded` sentinel input by design. This document
never describes a seven-branch analyzer; it is six analyzer branches plus one
CLI-synthesized outcome.

Resolution order for the six analyzer branches — using the same canonical
outcome numbers as the ownership-split table above (outcome 1 is the CLI's
`degraded`; the analyzer owns outcomes 2–7), evaluated against the full
unfiltered shipment enumeration (anomaly-first — never an early-narrowed
subset):

2. `readiness.cycle_detected` → null cursor / `cycle_detected`.
   `next_eligible_detail` stays `{"candidate_ids": [], "offending_ids": []}`
   here — the cycle's participating nodes are already reported via the
   existing Phase 1 `cycle_nodes` field, not duplicated into
   `next_eligible_detail`.
3. Any shipment with ambiguous live+archive provenance → null cursor /
   `ambiguous_provenance` (offending ids = the ambiguous shipment ids).
   Checked **before** active/ready partitioning — a single `active` shipment
   that is **also** ambiguous reports `ambiguous_provenance`, never
   `resume_active`, and is never folded into `multi_active_anomaly` or
   `no_candidates`.
4. More than one `active` shipment → null cursor / `multi_active_anomaly`
   (offending ids = every active shipment id). Never picks a winner and never
   falls through to the ready-set.
5. Exactly one `active` shipment → that id is the cursor, reason
   `resume_active`. `candidate_ids` stays empty here too — there is exactly
   one `active` shipment and nothing to tie-break, so the resolved cursor is
   reported only via `next_eligible` itself.
6. Zero `active`, non-empty `ready_set` → the tie-broken head of
   `ready_set`, reason `ready_set_head` (`candidate_ids` = the full
   tie-broken `ready_set`, in order).
7. Zero `active`, empty `ready_set` → null cursor / `no_candidates`.

**`next_eligible_detail` population is normative, not "empty unless
otherwise noted"**: `candidate_ids` is non-empty **only** for outcome 6
(`ready_set_head`); `offending_ids` is non-empty **only** for outcomes 3
(`ambiguous_provenance`) and 4 (`multi_active_anomaly`). Every other outcome
— including `degraded`, `cycle_detected`, `resume_active`, and
`no_candidates` — reports both arrays empty.

### Tie-Break (branch 6, `ready_set_head`, ONLY)

When more than one shipment is in `ready_set`, the cursor is chosen by:

1. **Descending** transitive downstream-dependent count
   (`len(downstream_dependents[id])`) — prefer the candidate that unblocks
   the most other work.
2. **Ascending** shipment id — the final tie-break.

Shipment ids are unique, so this ordering is **total**: it never depends on
dict/filesystem iteration order and is therefore run-to-run stable for the
same graph, regardless of input ordering. This tie-break applies to branch 6
(`ready_set_head`) **only** — it never applies to branch 5 (`resume_active`),
which by definition has exactly one `active` shipment and nothing to
tie-break.

### `next_eligible` vs. `ready_set` — Interop Contract

**`next_eligible` is NOT guaranteed to be a member of `ready_set`.** Under
`resume_active`, the cursor is an `active` shipment — and `ready_set`, by
definition, contains only live `queued` shipments. Consumers **must** use
`next_eligible_reason` as the authoritative discriminator and **must not**
treat non-membership in `ready_set` as an error.

### Exit Codes and BLOCK Verdict Ownership

Exit codes are **unchanged** by this advisory: `0` for every report (`ok` /
`empty` / `degraded`), `2` for invalid arguments. `dag-readiness` still has
**no BLOCK verdict** of its own — a `multi_active_anomaly` is **reported**
here, never escalated to a non-zero exit. The
[pipeline-topology gate](pipeline-topology-gate.md) remains the sole owner of
that BLOCK verdict.

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
  "status": "ok",
  "next_eligible": "003-S",
  "next_eligible_reason": "ready_set_head",
  "next_eligible_detail": {
    "candidate_ids": ["003-S"],
    "offending_ids": []
  }
}
```

A `degraded` sample (backlog unreachable) shows the two-empty-arrays detail
shape:

```json
{
  "ready_set": [],
  "critical_path": [],
  "downstream_dependents": {},
  "cycle_detected": false,
  "cycle_nodes": [],
  "degraded_reason": "backlog directory is unavailable",
  "status": "degraded",
  "next_eligible": null,
  "next_eligible_reason": "degraded",
  "next_eligible_detail": {
    "candidate_ids": [],
    "offending_ids": []
  }
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
| `next_eligible` | shipment id or `null` | The resumption cursor. See [Next-Eligible Resumption Cursor](#next-eligible-resumption-cursor). Always present, on every path. |
| `next_eligible_reason` | one of `resume_active`, `ready_set_head`, `no_candidates`, `multi_active_anomaly`, `ambiguous_provenance`, `cycle_detected`, `degraded` | Always populated, even when `next_eligible` is `null`. The first six come verbatim from the analyzer; `degraded` is CLI-synthesized (see [ownership split](#seven-outcome-resolution-order-and-ownership-split)). |
| `next_eligible_detail` | object | **Always** exactly `{"candidate_ids": [...], "offending_ids": [...]}` — both keys always present as arrays (empty arrays when not applicable), on **every** path including `degraded`. Never `{}`, never `null`, never a partial key set. |

The human-readable (non-`--json`) report renders the same information,
omitting empty downstream-dependents entries for readability, and adds at
most one `next eligible: ...` line rendered on every path — including the
`cycle` and `degraded` early-return paths.

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
Feature `115-F` (deliberation `014-DL`) delivers the Phase 2 deterministic
next-eligible resumption cursor described above; it is no longer deferred.

### Reconciling the NON-GOAL with the Delivered Resumption Cursor

The permanent NON-GOAL sentence above **remains in force, verbatim, and is
not weakened by the Phase 2 delivery**. The distinction is explicit:

* **PROHIBITED, PERMANENTLY**: automatic selection-**for-execution** —
  claiming, activating, or executing a shipment without an explicit
  human/Ship decision; and any scheduler or parallel execution (P-001/P-016).
  This gate, and its `next_eligible` advisory, do not and will never do this.
* **DELIVERED**: a deterministic, **READ-ONLY RECOMMENDATION** that a human
  or the Orchestrator must still act on explicitly. `next_eligible` claims
  nothing, activates nothing, mutates nothing, creates no branch or
  worktree, and does not authorize a claim. Ship's claim authority is
  untouched by this advisory. **A `null` cursor never authorizes a claim
  either** — it is simply the absence of a recommendation.

## References

* [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) — the reused
  shipment-blocks reader (`ShipmentState`, `FilesystemTopologyReaders`) and
  the P-001/P-016 invariants this gate preserves
* [Validation Gates Reference](gates-reference.md)
* [Copilot-Review Merge Gate Reference](copilot-review-gate.md)

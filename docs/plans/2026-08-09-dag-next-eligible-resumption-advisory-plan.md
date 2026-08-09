---
title: Deterministic next-eligible resumption advisory (33CC445C Phase 2)
description: Implementation plan for a read-only, advisory-only deterministic resumption cursor layered additively on the shipped dag-readiness substrate — analyzer, CLI field, and non-goal reconciliation docs
doc_type: plan
source: docs/plans/2026-08-09-dag-next-eligible-resumption-advisory-plan.md
status: reviewed
deliberation: 014-DL
stash: 33CC445C
---

> **Navigation**: [DAG Readiness Gate Reference](../dag-readiness-gate.md) ·
> [Pipeline-Topology Gate Reference](../pipeline-topology-gate.md) ·
> [Validation Gates Reference](../gates-reference.md)

## Source of truth

Deliberation `014-DL` (Option C — advisory-only deterministic resumption cursor),
itself grounded in spike `001-SP` and the Phase 1 delivery `110-F` / `117-S`
(both archived; `autoharness gate dag-readiness`).

## Problem

`compute_dag_readiness` returns a lexically-sorted `ready_set` with **no cursor
semantics** and **no representation of in-flight work** — an `active` shipment is
never a ready candidate. After a crash, restart, or context loss, a reader of
`ready_set` alone can wrongly conclude a *new* shipment should be started while an
`active` one is still in flight. That is precisely the P-001 single-active failure
mode. There is no `next_eligible` implementation anywhere in autoharness, and none
in external backlogit 1.8.0 — this is additive and non-duplicative.

## Surface

Three width-isolated surfaces, one per task:

| Surface | Files | Task |
|---|---|---|
| Analyzer (pure logic) | `src/autoharness/gates/topology.py`, `tests/test_gates_dag_readiness.py` | 115.001-T |
| CLI (presentation) | `src/autoharness/cli.py`, `tests/test_gate_dag_readiness_cli.py` | 115.002-T |
| Documentation | `docs/dag-readiness-gate.md`, `docs/gates-reference.md` | 115.003-T |

No schema change. No template change. No agent-template weaving. No installed
dogfood mirror refresh. No new gate family. No exit-code change. No backlogit or
other external change.

## Design

### Resolution order (resumption-first)

Evaluated in this exact order against the **unfiltered** shipment enumeration:

1. **DEGRADED** (backlog unreachable, `BacklogUnavailableError`) →
   `next_eligible: null`, `next_eligible_reason: "degraded"`. The graph was never
   read; any cursor would be fabricated.
2. **Cycle detected** → `null`, reason `"cycle_detected"`. Mirrors Phase 1's
   existing refusal to fabricate a `ready_set` or `critical_path` under a cycle.
3. **Any shipment carrying ambiguous live/archive provenance** (the same corruption
   Phase 1's `_has_ambiguous_shipment_records` already detects) → `null`, reason
   `"ambiguous_provenance"`, with the offending ids surfaced. This check runs on the
   **full unfiltered enumeration** and **before** any active/ready partitioning, so
   an ambiguous record can never be silently skipped, and can never be mistaken for
   the absence of in-flight work. It is a distinct reason code — never folded into
   `multi_active_anomaly` and never into `no_candidates`.
4. **More than one `active` shipment** (a P-001 anomaly) → `null`, reason
   `"multi_active_anomaly"`, with the offending ids surfaced. Fail closed; the
   pipeline-topology gate owns the actual BLOCK verdict.
5. **Exactly one `active` shipment** → **that shipment is the cursor**, reason
   `"resume_active"`. Resume in-flight work; never recommend starting new work.
6. **Zero `active` shipments** → the deterministic first element of the existing
   `ready_set` under the tie-break below, reason `"ready_set_head"`.
7. **Zero `active` and empty `ready_set`** → `null`, reason `"no_candidates"`.

Branch 3 deliberately precedes branches 4–7 so that provenance corruption is
reported as itself rather than being re-expressed as some downstream symptom.

### `next_eligible` is NOT a `ready_set` member (interop contract)

Under branch 5 the cursor is an **`active`** shipment, and Phase 1's `ready_set`
contains **only live `queued`** shipments. Therefore `next_eligible` is **not**
guaranteed to appear in `ready_set`, and a consumer MUST NOT assume membership or
treat `next_eligible not in ready_set` as an error. `next_eligible_reason` is the
authoritative discriminator: `resume_active` means the cursor is in-flight work to
be resumed, `ready_set_head` means it is a ready-set candidate. This must be stated
in both the docs task and the `--json` field table.

### Deterministic tie-break (branch 5)

Sort candidates by:

1. **DESC** transitive `downstream_dependents` count — prefer the candidate that
   unblocks the most downstream work.
2. **ASC** shipment id — total-order fallback.

Shipment ids are unique, so the order is **total**: the cursor is never ambiguous
and never depends on dict or filesystem iteration order. `downstream_dependents`
is already computed by the same `compute_dag_readiness` call — no new traversal.

### Fail-closed structural pattern

Per compound learning `2026-08-07-copilot-review-fix-introduces-new-filter-bug`:
**enumerate unfiltered → check anomalies first → only then partition.** No early
narrowing filter may be introduced that could hide the very anomaly the cursor
exists to surface. Every null result carries a populated machine-readable reason;
a silently-empty or reasonless null is a defect.

### Advisory-only invariant

The cursor **recommends**; it never claims, activates, mutates, creates a branch or
worktree, or authorizes a claim. A null cursor NEVER authorizes a claim either —
consistent with the compound rule that a degraded/handoff path must not be treated
as satisfying a downstream success gate. Ship's claim authority is untouched.

## Backward compatibility

Three **additive** JSON fields are emitted **unconditionally** — no opt-in flag is
added (resolved from `014-DL` open question 1; an opt-in flag would create two
payload shapes to test and document for no benefit, and additive fields are already
backward compatible):

| Field | Type | Description |
|---|---|---|
| `next_eligible` | shipment id or `null` | The single recommended cursor, or `null` on any fail-closed branch. |
| `next_eligible_reason` | string | Exactly one of `resume_active`, `ready_set_head`, `no_candidates`, `multi_active_anomaly`, `ambiguous_provenance`, `cycle_detected`, `degraded`. Always populated — never empty, even when `next_eligible` is `null`. |
| `next_eligible_detail` | object | `{"candidate_ids": [...], "offending_ids": [...]}`. `candidate_ids` holds the tie-broken ordered candidate list under `ready_set_head` (empty otherwise); `offending_ids` holds the ids that triggered `multi_active_anomaly` or `ambiguous_provenance` (empty otherwise). Both keys are always present so consumers need no key-existence checks. |

Every Phase 1 field keeps its exact meaning and shape. Exit codes stay
`0` (report: ok/empty/degraded) and `2` (bad args) — dag-readiness still has no
BLOCK verdict. The human-readable report gains at most one line. Existing Phase 1
tests must pass unmodified.

## P-006 hardening conclusion

**Requires plan hardening: YES.** Field explicitly set, not absent.

Justification: although each change is additive and read-only, the blast radius is
elevated because (a) it edits `gates/topology.py`, the shared module that also backs
the pipeline-topology gate — autoharness's P-001/P-016 enforcement surface; (b) it
reconciles a documented **permanent NON-GOAL**, a policy-adjacent edit; and (c) a
mis-specified cursor could induce a P-001 violation downstream even without
mutating anything itself. See the Hardening section below.

## Hardening (P-006, H1–H6)

* **H1 — Shared-module non-regression.** The new analyzer is a *separate* pure
  function. `compute_dag_readiness`, `DagReadinessResult`'s existing fields,
  `_dag_all_predecessors_finished`, `_shipment_map`, and every symbol the
  pipeline-topology gate depends on are **not** modified. Verified by the
  pre-existing `tests/test_gates_topology.py` and `tests/test_gates_dag_readiness.py`
  passing unmodified.
* **H2 — Non-goal reconciliation is explicit, never a silent softening.** The
  existing non-goal sentence stays in force. The docs task must add a clearly
  labelled subsection distinguishing *automatic selection-for-execution*
  (prohibited, permanently) from *deterministic read-only recommendation*
  (delivered here), and must restate that the gate still never claims, activates,
  or executes anything. Deleting or quietly rewording the non-goal is a P0 defect.
* **H3 — Multi-active fails closed, never picks.** With two or more `active`
  shipments the cursor MUST be null with reason `multi_active_anomaly`. Choosing
  one of them, or falling through to the ready-set, is a P0 defect: it would
  paper over exactly the P-001 violation the operator must see. Requires a
  dedicated regression test.
* **H3b — Ambiguous provenance is anomaly-first and distinctly named.** The
  ambiguous live/archive provenance check runs on the full unfiltered enumeration
  before any active/ready partitioning, and reports reason `ambiguous_provenance`.
  Folding it into `multi_active_anomaly`, into `no_candidates`, or skipping the
  ambiguous record and continuing is a P0 defect — it is the "narrower filter hides
  the anomaly" failure mode named in the compound learning. Requires a dedicated
  regression test, including the single-active-but-ambiguous case.
* **H4 — Read-only proof.** The analyzer receives already-read `ShipmentState`
  values and performs no I/O. The CLI path adds no write. A regression test asserts
  no backlogit/git mutation occurs on any branch, including the anomaly branches.
* **H5 — Total-order determinism.** A regression test feeds the same graph with
  shuffled input ordering and asserts an identical cursor across runs, covering a
  fan-out tie resolved by the id fallback.
* **H6 — No exit-code or payload regression.** A regression test asserts Phase 1's
  exit codes and every Phase 1 JSON field are unchanged, and that a consumer
  ignoring the new fields still parses the payload.

## Out of scope / deferred

* Agent-template weaving (Orchestrator/Stage/Ship consulting the cursor) and the
  consequent installed dogfood mirror refresh — deferred; re-triage only after the
  cursor ships and proves stable.
* Any scheduler, auto-claim, or parallel execution — **permanent** non-goal under
  P-001/P-016.
* Time-weighting the critical path; changing the ready-set definition.

## Verification

* `python -m pytest tests/test_gates_dag_readiness.py tests/test_gate_dag_readiness_cli.py tests/test_gates_topology.py tests/test_gate_pipeline_topology_cli.py`
* `autoharness gate dag-readiness --json` on this workspace — smoke check that the
  payload is additive and the cursor is present and correct.

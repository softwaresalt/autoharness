---
title: "Deterministic next-eligible resumption advisory"
doc_type: decided-plan
status: reviewed
created: 2026-08-09
tasks: ["115.001-T", "115.002-T", "115.003-T"]
supersedes:
  - docs/archive/plans/2026-08-09-dag-next-eligible-resumption-advisory-plan.md
---

# Decided Plan: Deterministic next-eligible resumption advisory

**Outcome:** Reviewed as a read-only extension to the shipped DAG-readiness substrate. The source plan itself is marked `reviewed` and includes P-006 hardening, but it does not contain a PR number or merge commit, so status remains `reviewed`. The decided scope adds an advisory `next_eligible` cursor for restart and resumption scenarios without turning DAG readiness into a scheduler, claim mechanism, or new enforcement surface.

## Decisions

- Add a **read-only advisory cursor** on top of DAG readiness. The cursor recommends what should be resumed or started next; it never claims, activates, creates a branch/worktree, or authorizes execution.
- Split responsibility by reachability: `degraded` is synthesized **only by the CLI** when backlog reads fail, because the analyzer's inputs do not exist on that path. The analyzer owns the remaining six outcomes on successfully read data.
- Preserve the settled seven-outcome order: `degraded`, `cycle_detected`, `ambiguous_provenance`, `multi_active_anomaly`, `resume_active`, `ready_set_head`, `no_candidates`.
- Make `next_eligible_reason` authoritative. Under `resume_active`, the cursor is an `active` shipment and is **not** required to be a member of `ready_set`.
- Use a deterministic tie-break only for `ready_set_head`: descending transitive `downstream_dependents`, then ascending shipment id.
- Emit the new JSON fields **unconditionally**: `next_eligible`, `next_eligible_reason`, and `next_eligible_detail`. The detail object always contains both `candidate_ids` and `offending_ids`, even when both arrays are empty.

## Implementation (3 tasks)

- **115.001-T — Analyzer:** add the pure `compute_next_eligible` logic on top of successfully read shipments/readiness data without changing the existing DAG-readiness core.
- **115.002-T — CLI presentation:** synthesize the degraded payload on `BacklogUnavailableError`, expose the new fields, and keep exit codes unchanged.
- **115.003-T — Documentation:** update the DAG-readiness and gate reference docs so the new advisory cursor, non-goals, and field contract are explicit.

## Key constraints preserved

- The structural pattern is anomaly-first: **enumerate unfiltered, check anomalies first, then partition**. No early filter may hide an ambiguous or multi-active record.
- `ambiguous_provenance` stays distinct from `multi_active_anomaly` and `no_candidates`; provenance corruption is surfaced as its own reason.
- The analyzer remains read-only and pure; no backlogit or git mutation is introduced on any path.
- Existing Phase 1 fields and exit codes keep their meaning. The new fields are additive and backward compatible.
- The change stays out of template, schema, and agent-weaving surfaces. It is a narrow analyzer/CLI/docs increment only.

## Rejected alternatives

- **Implementing `degraded` inside the analyzer or adding a separate degraded input flag** — rejected because the analyzer cannot truthfully see that state once backlog reads fail, and an explicit degraded input would create self-contradictory inputs.
- **Hiding the new fields behind an opt-in flag** — rejected because the payload is additive and a second JSON shape would only add test and documentation burden.
- **Treating the cursor as a scheduler or auto-claim path** — rejected as a permanent non-goal under P-001/P-016.
- **Assuming `next_eligible` must belong to `ready_set`** — rejected because the `resume_active` case is intentionally an in-flight cursor, not a ready candidate.

## Review findings that changed the plan

- Hardening made `degraded` a **single-sited CLI responsibility** and explicitly ruled out an unreachable analyzer-side degraded branch.
- Hardening elevated **ambiguous live/archive provenance** into its own anomaly-first reason code ahead of active/ready partitioning so corruption can never be filtered away.
- The compound-learning-derived structural rule — **enumerate unfiltered → check anomalies first → only then partition** — became a first-class constraint of the decided design.
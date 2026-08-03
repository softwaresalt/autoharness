---
title: "plan-review — Size + Complexity first-class staging & backlogit telemetry evidence mapping"
type: plan-review
date: 2026-08-03
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
plan: docs/plans/2026-08-03-size-complexity-telemetry-staging-plan.md
deliberation: docs/decisions/2026-08-03-size-complexity-telemetry-staging-deliberation.md
verdict: PASS
---

## Verdict: PASS

The plan is dependency-correct, width-isolated, non-conflating, and each task is single-family
and ≤ 2h. Plan hardening is present and adequate for the one schema-mutating task. Proceed to
harvest.

## Findings

### P0 — Blocking (0)
None.

### P1 — Must-fix before harvest (0)
None.

### P2 — Advisory (3, non-blocking; folded into acceptance)
- P2-a (F2.T2): The complexity-field placement (top-level vs a dedicated optional sub-object)
  is a design choice. Acceptance for F2.T2 must require the implementer to (i) keep it
  structurally separate from `work_sizing_snapshot`, and (ii) record the chosen shape + the
  schema version decision (additive-optional ⇒ minor or in-place) in the PR description.
- P2-b (F2.T1): Guard against implying precision — every ToolTelemetryEvent target field in the
  map must carry BOTH a `metric_sources` and a `metric_quality` value; "observed" is reserved
  for host_reported/backlogit-direct fields only. Folded into F2.T1 acceptance.
- P2-c (F1.T4): If no lightweight fixture harness exists in-repo, F1.T4 degrades to a reviewer
  checklist only (no new test framework) — do not introduce a test runner to satisfy this task.

## Scope / Policy Checks
- Non-conflation invariant (size=volume, complexity=difficulty/uncertainty) is adopted verbatim
  from backlogit's released contract and enforced across F1.T1/F1.T4/F2.T2 — PASS.
- P-003 granularity: 7 tasks, each single-family, ≤2h, explicit deps and acceptance — PASS.
- P-010 boundary: Stage authored only planning docs + backlog; all implementation is delegated
  to Ship via tasks — PASS.
- Blast radius (F2.T2 schema): additive-optional behind a forward contract with no live
  emitter/consumer; hardening section covers failure modes + additive rollback — PASS.
- Sensitivity: F2.T3 restricts the backlogit boundary to counts/durations/labels/hashes and
  documents redaction/secret-scan defaults; no raw-content exfiltration — PASS.
- Boundary confirmations honored: 34D50F2D (a)/(c)/(d) NOT harvested (deferred per 011-DL);
  936C68F3 external guard recorded as superseded upstream, part (2) left operator-gated — PASS.

## Disposition
PASS — proceed to harvest. Three P2 advisories folded into F2.T2 / F2.T1 / F1.T4 acceptance
criteria. Ordered shipment chain S1 (F1) queued, S2 (F2) blocked-on-S1. S2 is the backlogit-only
carve-out that unblocks the backlogit portion of 082-F; other packs stay blocked-on-operator.

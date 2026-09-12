---
title: "Plan review — DAG-authoritative predecessor derivation"
description: "Multi-persona adversarial plan review of docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md, gating harvest."
doc_type: review
source: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
date: 2026-09-12
plan_path: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
decision: PASS
---

# Plan Review — DAG-Authoritative Predecessor Derivation

## Dispatch Capability and Declared Degradation

```text
TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass
TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass
```

No subagent dispatch surface and no alternate model route are available in this
session. Per the plan-review skill, every persona below was still applied inline
against its rubric — **no persona was skipped**. Reviewer route:
`claude-opus-5`/`anthropic`/`high` (same as caller).

## Persona Findings

### Constitution Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | Principle II (Test-First, NON-NEGOTIABLE): satisfied. T1/T4 author RED tests before T2/T5 implementation, and dependency edges enforce the ordering. | OK |
| — | Principle VIII (Explicit Safety Modes for Elevated Risk): satisfied by the `unsequenced_shipment` switch and `UNSEQUENCED_SHIPMENT` provenance signal. | OK |
| — | Principle V (Structured Observability): `predecessor_source` on both blocked and passed payloads (H2/F1) satisfies auditability. | OK |
| — | Principle VI (Single Responsibility): T2 (derivation) and T7 (closure evidence) are correctly separated rather than conflated. | OK |
| P2 | Principle IV (CLI Workspace Containment) is not explicitly addressed for the new config read path. | Recorded as follow-up; T2 reads an existing workspace config surface, no new path traversal introduced. |

### Python Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| P2 | Plan does not state the type of the new provenance field. Recommend a `Literal["explicit", "none"]` rather than a bare `str` to keep the contract enumerable. | Follow-up; non-blocking. |
| — | F7 hardening already requires enum validation with fail-closed behaviour for the config value. | OK |
| — | Retiring `_prior_shipment_id` as a *claim-blocking input* while leaving the function referenced elsewhere is handled: T2 scope says "retire as claim-blocking input", not "delete", avoiding a dangling-reference break. | OK |

### Scope Boundary Auditor

| Sev | Finding | Disposition |
|---|---|---|
| — | `86498B64`, `9B582824`, `97B28746`, `50434138`, `58A85283` all explicitly fenced out (deliberation §Scope boundary, hardening H3). | OK |
| — | H1 self-corrected an unverified edit surface (`workflow-policies.md.tmpl`) rather than carrying a speculative scope item. This is the correct anti-scope-creep behaviour. | OK |
| P2 | T8 bundles templates + installed dogfood copies + agent sequencing text. This is near the 2h ceiling. | Mitigated: sized `M`, documentation-class only, width-isolated from engine work. Flagged for split if execution exceeds budget. |

### Learnings Researcher

| Sev | Finding | Disposition |
|---|---|---|
| — | Plan does **not** contradict any prior resolution. It is consistent with both topology compound learnings, which document the heuristic as repeatedly defective. | OK |
| — | The "still unfixed on `main`" forward-dependent defect is explicitly handled by hardening F6, which requires proving moot-ness by test rather than assuming it. This is the correct treatment of a known outstanding learning. | OK |
| — | `2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md` is relevant to T5's `next_eligible` disambiguation and is cited. | OK |

### Architecture Strategist

| Sev | Finding | Disposition |
|---|---|---|
| — | Shared-helper requirement (H2/F3) prevents the two gates from re-diverging — this addresses the root architectural cause of the advisory mismatch, not just its symptom. | OK |
| — | `pre_claim` retained as sole claim authority; advisory gate never authorizes. Authority boundary is preserved. | OK |
| P3 | Could state whether the shared helper lives in `topology.py` or a new module. | Advisory. |

### Agent-Native Parity Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | Gate output changes are additive (H4), so existing agent consumers do not break. | OK |
| — | Orchestrator/Ship sequencing text is coupled in T8, so agent-facing instructions match the engine contract. | OK |

### Security Lens Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | No auth/authz, secrets, or external integration surface. `--force` semantics explicitly unchanged and still human-authorized/audited (H3). | OK |
| — | The one genuine safety concern — silent fail-open on migration — is the plan's central design constraint and is mitigated three ways (signal, opt-in strict mode, migration guide). | OK |

## Critical Verification — Premise Integrity

The review specifically re-verified the plan's most dangerous potential defect:
a plan built on the incorrect claim that removing numeric adjacency unblocks
`163-S`.

The plan **explicitly records the correction** (§1 "Carried-forward critical
correction"), reproduces the evidence, forbids any task from claiming the fix,
and routes the real cause to a separate task (T7). This is correct and is the
single highest-value property of this plan.

## Merged Findings

```text
[PLAN-REVIEW] Merged: 5 findings (0 P0, 0 P1, 4 P2, 1 P3)
```

| Severity | Count | Blocking |
|---|---|---|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 4 | No — recorded as follow-ups |
| P3 | 1 | No — advisory |

## Gate Decision

```text
[PLAN-REVIEW] Gate: PASS
decision: PASS
```

Zero P0 and zero P1 findings. The plan is **harvest-ready**. P2/P3 findings are
recorded above as non-blocking follow-ups and do not require a review-fix cycle.

Review cycles used: 1 of 3.

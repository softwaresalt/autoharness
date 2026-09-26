---
title: "Plan review attempt 03 — Checkpoint resume-hint / payload-shape contract (plan revision 3)"
description: "Immutable per-attempt plan-review artifact. Re-review of docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md at revision 3 after remediation cycle 1. Verifies the named callable author-time validation boundary wired into both the Stage and Ship producer paths, policy-then-producers-then-validation ordering encoded as machine dependencies, the invariant-based replacement for the pinned historical count, truthful operator-authored-repair provenance for checkpoint-20260916-064310.json, and the newly persisted P-006 hardening record. Gate decision: PASS, 0 P0 / 0 P1 open."
doc_type: review
source: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 3
attempt_range: "03"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempts-01-02-combined.md
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_revision: 3
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 2
source_stash_id: 24D4E0F8
review_cycle: 3
review_cycles_remaining: 0
dispatch_mode: declared-degradation
decision: PASS
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "checkpoint-contract"
  - "provenance"
  - "remediation-cycle-1"
---

# Plan review attempt 03 — Checkpoint resume-hint / payload-shape contract

## Scope of this attempt

Remediation re-review. Operative input set: plan revision 3 and the
consolidated blocking findings. Attempts 01–02 preserved in `review-history/`
and excluded.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. Personas applied inline: Constitution Reviewer, Python Reviewer,
Scope Boundary Auditor, Learnings Researcher (always-on); Architecture
Strategist and Agent-Native Parity Reviewer (cross-model, inline — the plan
changes both Stage and Ship producer contracts and their installed mirrors).

## Plan hardening (P-006)

Revision 2 declared `requires_plan_hardening: "no"`. **That declaration was
wrong.** The plan changes a contract consumed by two agent roles at
session-boundary time, rewrites instruction text plus installed mirrors, and
adds a validation boundary that can refuse a write — session-boundary
durability is exactly where an unhardened change costs the most, because the
failure surfaces only after the session that could have corrected it is gone.

Revision 3 declares `requires_plan_hardening: "yes"`,
`plan_hardening_status: complete`, and persists
`## Plan Hardening Record (P-006)` named by `plan_hardening_section`.
Verified substantive: trigger on three named axes, five protected invariants
including the never-hand-edit rule, eight sources consulted, nine findings
H0–H8, five classified `ProposedAction` entries, rollback coupling, a concrete
monitoring signal, one operator checkpoint, and a P-012 carry-forward.

## Findings

### Attempt 03 — remediation verification

| ID | Persona | Sev | Finding under review | Verdict |
|---|---|---|---|---|
| R1-F1 | Architecture Strategist | **P1** (consolidated finding 6) | No callable author-time validation boundary was identified; validation existed only as instruction prose plus a post-hoc corpus scan, so a malformed payload could be written and only discovered later | **Closed.** One surface named — `validate_checkpoint_payload(payload, *, origin) -> ValidationOutcome` — evaluated **before** the write, returning outcome-as-data rather than raising, with `origin` partitioning the token space structurally so a Stage-only rule cannot silently apply to a Ship payload. A wiring table names both producer call sites (Stage Step 6, Ship closure) plus the startup scan, so "wired into both paths" is checkable rather than claimed |
| R1-F2 | Constitution Reviewer | **P1** (consolidated finding 6) | Task ordering did not enforce policy → producers → validation; a validator landing before the producers it validates would have failed against payloads no producer yet emitted | **Closed.** Full edge set encoded in a `Blocked by` column: T2→T1; T3→T1,T2; T4→T1,T2; **T5→T1,T2,T3,T4**; T6→T5; T7→T5. The rationale is stated, and the transitive consequence (validation cannot precede either producer) is explicit |
| R1-F3 | Python Reviewer | P2 | T7 pinned the historical corpus at 51 records — a volatile count that every subsequent Stage or Ship session invalidates, so the test would have begun failing for correct behaviour | **Closed, and closed the better way.** T7 rewritten as five invariants over whatever the corpus contains, with synthetic fixture corpora for the positive and negative cases. Volatility is removed rather than re-pinned. The stale value is separately corrected: the corpus was **52** at this session's start, not 51 |
| R1-F4 | Constitution Reviewer | **P1** (consolidated finding 10) | The publication diff includes `.backlogit/checkpoints/checkpoint-20260916-064310.json`, while the plan and review claimed no committed checkpoint was modified — the artifacts contradicted the diff | **Closed by telling the truth.** Now recorded as an **operator-authored, operator-authorized pre-existing repair**, included for durable startup consistency. Explicitly stated as *not* an agent migration and *not* evidence that an official repair mechanism exists. Residual policy risk recorded: the file sits under a path the instruction reserves, the repair was a direct edit, and it is denied as precedent. The operator's change is preserved unmodified — correct, and the only honest disposition |
| R1-F5 | Scope Boundary Auditor | P2 | The 51-record enumeration was also carried in the deliberation as a durable fact | **Closed.** Labelled there as a point-in-time session-start observation, with the current value noted and pinning called out as an anti-pattern |
| R1-F6 | Constitution Reviewer | **P1** (consolidated finding 1) | `plan_hardening` claim unverifiable | **Closed.** See Plan hardening above |

### Attempt 03 — new observations

No new P0 or P1. Three observations, **accepted without change**:

* **P2-1** (Scope Boundary Auditor): the plan now carries an out-of-scope note
  about `checkpoint-20260918-052706.json`'s top-level `progress`. Accepted —
  the note correctly states that the record is superseded through the official
  lifecycle and never hand-edited, which is the same never-hand-edit invariant
  the plan protects, applied to itself.
* **P3-1** (Python Reviewer): backlogit's own V1 schema permits a top-level
  `progress` object, so the harness contract is strictly narrower than the
  tool's validator and `checkpoint get` reports `valid: true` for a payload the
  harness forbids. Accepted — this divergence is exactly why an author-time
  harness-side boundary (R1-F1) is needed rather than relying on the tool.
* **P3-2** (Agent-Native Parity Reviewer): the Stage and Ship producer edits
  must land with their installed mirrors. Accepted — T3 and T4 each scope their
  own mirror pair.

## Persona coverage

| Persona | Findings | Open P0/P1 |
|---|---|---|
| Constitution Reviewer | R1-F2, R1-F4, R1-F6 | 0 |
| Python Reviewer | R1-F3, P3-1 | 0 |
| Scope Boundary Auditor | R1-F5, P2-1 | 0 |
| Learnings Researcher | — (no prior compound entry on checkpoint payload shape) | 0 |
| Architecture Strategist | R1-F1 | 0 |
| Agent-Native Parity Reviewer | P3-2 | 0 |

## Gate decision

decision: PASS

0 P0 open, 0 P1 open. Cleared for harvest at plan revision 3.

Explicitly re-verified before passing: no historical checkpoint is rewritten,
migrated, or deleted by this release unit; the never-hand-edit rule is
preserved and was honoured in this session's own checkpoint remediation; the
validation boundary can refuse a write but cannot silently drop one; and no
claim about an official repair mechanism survives anywhere in the plan,
deliberation, or this review.

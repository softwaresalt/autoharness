---
title: "Plan review attempt 03 — P-004 red-phase precondition scoping (plan revision 3)"
description: "Immutable per-attempt plan-review artifact. Re-review of docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md at revision 3 after remediation cycle 1. Verifies the typed expected_red entry shape, the stdlib-unittest TestResult observation contract, and the newly persisted P-006 hardening record. Gate decision: PASS, 0 P0 / 0 P1 open."
doc_type: review
source: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-03.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 3
attempt_range: "03"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempts-01-02-combined.md
plan_path: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
plan_revision: 3
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 2
source_stash_id: 76EBDE6D
review_cycle: 3
review_cycles_remaining: 0
dispatch_mode: declared-degradation
decision: PASS
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "policy"
  - "p-004"
  - "remediation-cycle-1"
---

# Plan review attempt 03 — P-004 red-phase precondition scoping

## Scope of this attempt

This is a **remediation re-review**, not a fresh review. Its operative input
set is exactly two documents: plan revision 3, and the consolidated blocking
finding it was remediated against. Attempts 01–02 are preserved at
`docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempts-01-02-combined.md`
and are **excluded from the operative input set** — they are history, and
judging revision 3 against superseded prose is the defect the sibling
single-governing-plan work exists to eliminate.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. Every selected persona rubric applied inline with a separate
finding list. No persona skipped.

Personas applied: Constitution Reviewer, Python Reviewer, Scope Boundary
Auditor, Learnings Researcher (always-on); Architecture Strategist
(cross-model, inline). Security Lens Reviewer not triggered — no auth/authz,
secrets, or external trust boundary. Agent-Native Parity Reviewer triggered
this attempt because revision 3 changes the harness-architect skill contract in
both its template and installed copies.

## Plan hardening (P-006)

Revision 2 declared `requires_plan_hardening: "no"`. **That declaration was
wrong** and attempts 01–02 confirmed it without challenge — a persona-coverage
miss recorded here rather than elsewhere. The plan changes a `schemas/`
contract, rewrites a consumer-installed policy registry plus its installed
mirror, changes a skill in both copies, and adds executable gate code. Every
one of those is an enumerated P-006 hardening signal.

Revision 3 declares `requires_plan_hardening: "yes"`,
`plan_hardening_status: complete`, and — the part attempts 01–02 never checked
on any plan in this portfolio — **persists the record itself** at
`## Plan Hardening Record (P-006)`, named by the `plan_hardening_section`
frontmatter key so the claim is mechanically checkable rather than asserted.

Hardening outputs verified present and substantive: eight findings H0–H8 with
resolutions, five classified `ProposedAction` entries with risk levels and
rollbacks, explicit rollback coupling, a named monitoring signal, one operator
checkpoint, and a P-012 carry-forward.

## Findings

### Attempt 03 — remediation verification

| ID | Persona | Sev | Finding under review | Verdict |
|---|---|---|---|---|
| R1-F1 | Python Reviewer | **P1** (from consolidated finding 2) | `expected_red` was a bare identifier list while the gate predicate required a per-test marker — no deterministic ID→marker mapping existed, making the gate as specified unimplementable | **Closed.** Typed entry shape `{test_id, marker}` defined with a worked YAML example; marker required on red and prohibited on green (`P004_MARKER_MISPLACED`); uniqueness enforced within and across both lists (`P004_DUPLICATE_DECLARATION`, `P004_SET_OVERLAP`). The declared outcome map is stated as total and deterministic, with positional and convention-derived association explicitly excluded |
| R1-F2 | Python Reviewer | **P1** (from consolidated finding 2) | No runner contract: "expected failure markers in the output" would have been matched over merged process output, so with two failing tests each marker could be satisfied by the other test's traceback | **Closed.** Observation is specified against `unittest.TestResult`: `P004Result` subclasses `TextTestResult` and records `(test.id(), outcome, detail_text)` per test, where `detail_text` is the per-test string handed to `addFailure`/`addError`. Marker matching is per test against that test's own text. The crossed-marker case is pinned in Verification |
| R1-F3 | Python Reviewer | P2 | Unresolvable declared IDs would surface as `_FailedTest` errors, indistinguishable from genuine reds — a renamed test would have *satisfied* the red requirement | **Closed.** `loadTestsFromNames` placeholder detection at load time, before the run, classified `P004_MISSING_OBSERVATION`. Correctly identified as load-time rather than traceback-text-derived |
| R1-F4 | Python Reviewer | P2 | Skip / expected-failure / unexpected-success outcomes unmodelled | **Closed.** All three recorded as their own outcomes; a skipped declared test is `P004_MISSING_OBSERVATION`, never a pass and never a red |
| R1-F5 | Architecture Strategist | P2 | The regression suite could re-implement the comparison, so a runner defect would pass its own tests | **Closed.** T7 ships the runner as importable code in `src/autoharness/`; T5 blocks on T7 and imports it |
| R1-F6 | Constitution Reviewer | **P1** (from consolidated finding 1) | `plan_hardening` claim unverifiable — no persisted section | **Closed.** See Plan hardening above |

### Attempt 03 — new observations

No new P0 or P1. Three P2/P3 observations, **accepted without change**:

* **P2-1** (Scope Boundary Auditor): revision 3 grows the task count from six
  to seven (T7, the runner). Accepted — T7 is not new scope, it is the
  executable boundary the schema and policy text already described and which
  revision 2 left unowned. Each task remains within the 2-hour rule.
* **P3-1** (Agent-Native Parity Reviewer): the typed entry shape is defined in
  the plan and the schema but the harness-architect skill's authoring guidance
  will need a worked example to match. Accepted — that is T4's scope and the
  plan names it.
* **P3-2** (Learnings Researcher): the per-test-attribution failure mode has no
  compound entry yet. Accepted — a compound entry is a post-execution artifact,
  not a planning precondition.

## Persona coverage

| Persona | Findings | Open P0/P1 |
|---|---|---|
| Constitution Reviewer | R1-F6 | 0 |
| Python Reviewer | R1-F1, R1-F2, R1-F3, R1-F4 | 0 |
| Scope Boundary Auditor | P2-1 | 0 |
| Learnings Researcher | P3-2 | 0 |
| Architecture Strategist | R1-F5 | 0 |
| Agent-Native Parity Reviewer | P3-1 | 0 |

## Gate decision

decision: PASS

0 P0 open, 0 P1 open. Cleared for harvest at plan revision 3.

Explicitly re-verified before passing: the plan adds no command to CI and
removes none; authorizes no bypass, waiver, or `--force` path for P-004; does
not modify `168-S`'s manifest; and every fail-closed token names the offending
`test_id`.

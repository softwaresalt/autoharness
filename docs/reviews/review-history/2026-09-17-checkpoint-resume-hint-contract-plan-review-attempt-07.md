---
title: "Plan review attempt 07 (terminal) — Checkpoint resume_hint contract"
description: "Immutable per-attempt plan-review artifact recording the terminal independent review of docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md at revision 6, against reviewed content HEAD 22bca5c8. Gate result FAIL; decision BLOCKED on seven deduplicated P1 findings covering an invalid intermediate activation order, a CLI-only guarded create against registries and agent declarations that still advertise the raw operation, a startup scan that cannot call a Python predicate from Markdown, a non-total classification, an ambiguous and unconstrained --state-dump surface with a compatibility-downgrading public --origin, a text scan that cannot distinguish prohibitive documentation from a producer bypass, and adapter RED tests that do not pin the exact safe activation boundary. One P2 on installed-registry semantic-link parity is recorded but does not alter substantive scope. The authorized extra remediation cycle is exhausted: no remediation was performed, no finding is closed, and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-07.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 7
attempt_range: "07"
attempt_conformance: conforming
review_terminal: true
verdict_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_id: checkpoint-resume-hint-contract
reviewed_revision: 6
reviewed_content_head: 22bca5c8
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 71200CBB
feature_id: 172-F
shipment_id: 180-S
review_cycle: 7
dispatch_mode: declared-degradation
anchor_route: absent
anchor_route_note: "No cross-model anchor was available. The cross-model rubric ran under same-model declared degradation; this is recorded, not compensated for."
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: BLOCKED
verdict_at_entry_plan_revision: 6
remediation_authorization: none-exhausted
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 7
p2_open: 1
persona_coverage:
  - persona: constitution
    status: complete
  - persona: python
    status: complete
  - persona: scope-boundary
    status: complete
    findings: none
  - persona: learnings
    status: degraded
    note: "Not-ready/degraded: could not inspect the diff. Relevant prior lessons were retrieved and applied."
  - persona: architecture
    status: complete
  - persona: agent-native-parity
    status: complete
  - persona: security-lens
    status: complete
tags:
  - "plan-review"
  - "terminal-review"
  - "checkpoint"
  - "resume-hint"
  - "guarded-adapter"
  - "argv-safety"
---

# Plan review attempt 07 (terminal) — Checkpoint `resume_hint` contract

This artifact records **one thing**: the independent reviewer's verdict on plan
revision 6 as it stands at content HEAD `22bca5c8`. It has no Part 2. The
operator-authorized extra remediation cycle is **exhausted**, so no remediation
followed this review, no finding below is closed, and Stage asserts no `PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md` |
| Reviewed revision | 6 |
| Reviewed content HEAD | `22bca5c8` |
| Covering feature / shipment | `172-F` / `180-S` |
| Dispatch mode | `declared-degradation` |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

## Dispatch and coverage

Multi-agent persona coverage is **complete**: Constitution, Python, Scope
Boundary, Learnings, Architecture, Agent-Native Parity, and Security Lens all
ran.

* **Anchor route absent** — the cross-model rubric executed under *same-model
  declared degradation*. No cross-model anchor existed.
* **Learnings degraded / not-ready** — could not inspect the diff; relevant
  prior lessons were nonetheless retrieved and applied.
* **Scope Boundary returned no P0/P1.**

## P1 findings (7, deduplicated)

**E1 — the activation order produces an invalid intermediate architecture.**
The ordering **prohibits the raw operation path in the instruction before** the
guarded adapter exists and before all producer wiring is in place. Between those
two points the workspace has an instruction forbidding the only path that works
and an adapter that does not yet exist — an intermediate state in which no
lawful producer exists at all. The prohibition must not land before its
replacement is complete.

**E2 — the guarded create is CLI-only while the raw operation stays advertised.**
The guarded create is delivered as a **CLI-only** surface, while the **agent/MCP
registry still advertises the raw `backlogit_create_checkpoint`** operation. Any
agent reading the registry reaches the unguarded path. The inventory compounds
this: it **omits the installed and template registries and the agent
declarations**, so the surfaces that actually advertise the raw operation are
outside the set the plan proposes to change.

**E3 — the startup scan has no executable form.**
The Stage/Ship startup scan is specified as Markdown instruction text that
**calls a Python predicate**. Markdown cannot call Python. The scan needs a
single **atomic executable historical-scan command or tool**, with parity
between the CLI and agent/MCP surfaces, rather than prose describing an
invocation no agent can perform.

**E4 — classification is not total.**
The classification omits **`abandoned`** status and omits **malformed and
future-schema** records. A classification used as a gate must be total over the
status and schema domains it will actually encounter; the omitted cases have no
defined outcome.

**E5 — `--state-dump` is ambiguous and unconstrained, and `--origin` downgrades.**
`--state-dump` accepts **either a path or inline JSON** with no disambiguation
rule. It lacks **workspace containment**, **link/reparse-point/device
rejection**, **size and depth bounds**, and an explicit **no-shell argv**
requirement. Separately, exposing **`--origin` publicly** lets a caller
**downgrade a record to the compatibility (legacy) origin**, which is precisely
the classification branch the contract is being introduced to constrain.

**E6 — a text scan cannot tell prohibition from bypass.**
Detecting raw operation names by **text scan** cannot distinguish a document
that **prohibits** the operation (and must therefore name it) from a producer
that **calls** it. The check reports both identically, so it is either
permanently noisy or permanently defeated.

**E7 — adapter RED tests do not pin the safe activation boundary.**
The adapter RED tests and their ordering still need to pin the **exact** safe
activation boundary — the point at which the guarded path becomes the only path.
Without that boundary asserted, E1's invalid intermediate state is unobservable
to the suite.

## P2 findings (1)

**E8 — installed-registry semantic-link parity.**
Semantic-link parity between the installed registry and its template
counterpart is recorded as a **P2 follow-up only**. It does **not** alter
substantive backlog scope now.

## Disposition

**No remediation.** The extra cycle authorized after attempt 06 is exhausted.
`remediation_revision` is `null`, `disposition` is `null`, and the governing
revision remains 6 — the revision that was reviewed and found BLOCKED.

This plan is **not harvest-ready and not Ship-ready**.

## Date note

This artifact carries the true session date `2026-09-18`, matching the commit
clock. Earlier attempt artifacts in this series carry `date: 2026-09-19`, which
runs ahead of that clock. Those artifacts are immutable and are **not** edited
to correct it. Attempt ordering is given by `attempt`, never by `date`.

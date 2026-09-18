---
title: "Plan review attempt 06 — Checkpoint resume_hint contract"
description: "Immutable per-attempt plan-review artifact. Part 1 records the independent review opened against docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md at revision 5 — verdict BLOCKED on an undefined ValidationOutcome for an active historical checkpoint with a missing or empty resume_hint, a TDD spine whose RED, implementation, wiring and verification tasks were mis-ordered and mis-owned, and an unplanned atomic update to the authoritative Checkpoint Payload Contract that still advertised direct checkpoint-create calls as permitted harness producer paths. Part 2 records, separately, the operator-authorized remediation that raised the plan to revision 6. Disposition REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-06.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 6
attempt_range: "06"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-05.md
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_id: checkpoint-resume-hint-contract
reviewed_revision: 5
remediation_revision: 6
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 71200CBB
feature_id: 172-F
shipment_id: 180-S
review_cycle: 6
dispatch_mode: declared-degradation
decision: REMEDIATED-PENDING-REVIEW
verdict_at_entry: BLOCKED
verdict_at_entry_plan_revision: 5
remediation_authorization: operator-authorized-final-extra-cycle
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "checkpoint"
  - "resume-hint"
  - "tdd-ordering"
  - "payload-contract"
---

# Plan review attempt 06 — Checkpoint resume_hint contract

Two strictly separated halves. **Part 1** is the independent reviewer's verdict
at plan revision 5. **Part 2** is the **operator-authorized** remediation that
followed. See
`docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md`.

---

## Part 1 — Review verdict at plan revision 5

Opened against **plan revision 5**; verdict **BLOCKED**. Operative input set:
plan revision 5 and the live `172-F` / `180-S` records at entry. Attempts 01–02,
03, 04 and 05 are superseded history and were excluded.

dispatch_mode: `declared-degradation`
decision: `BLOCKED`

### P1 findings

**D12 — an active historical checkpoint with no `resume_hint` had no defined
outcome.** Revision 5 classified historical records as exempt without splitting
them by `status`. An **active** hintless record therefore fell through the
classification, which is the one case that must fail closed: a recovery
candidate no consumer can resume is worse than no candidate at all. Resolved
historical compatibility is a separate, legitimate concern and must remain
separate.

**D13 — the TDD spine was mis-ordered and mis-owned.** The RED task did not
cover the executable checkpoint-create adapter, the implementation task did not
distinguish an inert boundary from a wired one, enforcement wiring was not
sequenced after the adapter was green, and structural verification did not
follow wiring. A plan that describes the right five steps in the wrong order
authorizes the wrong execution order.

**D14 — the authoritative Checkpoint Payload Contract was not planned for
update.** `.github/instructions/backlogit.instructions.md` and its template
mirror still advertised direct `backlogit_create_checkpoint` /
`backlogit checkpoint create` calls as permitted harness producer paths, and the
structural coverage proposed was two agent templates rather than the full
producer surface.

**Portfolio-wide finding 7 (relayed).** The plan did not carry the mandated
seven-field plan identity wire format.

---

## Part 2 — Operator-authorized remediation to plan revision 6

**Authorization:** `operator-authorized-final-extra-cycle`. Stage work; nothing
below was verified closed by an independent reviewer.

* **D12 closed.** Classification is now **total and deterministic** and never
  returns `None`. `origin: harness` yields blocking
  `CHECKPOINT_RESUME_HINT_MISSING` or `CHECKPOINT_RESUME_HINT_EMPTY`.
  `origin: historical` is split **by `status` alone**: `resolved` yields the
  reported, non-blocking `CHECKPOINT_LEGACY_HINTLESS_RESOLVED`; `active` yields
  the new **blocking `CHECKPOINT_ACTIVE_HINTLESS`**. An active record is never
  exempt at any corpus size.
* **D13 closed.** One order is now stated in the plan, every task body and every
  machine edge — and only that order:
  `172.008-T` (RED: tests both the predicate **and** the executable
  checkpoint-create adapter) → `172.005-T` (implements the predicate plus an
  **inert** adapter wired into no write path) → `172.009-T` (wires the Stage and
  Ship producers, only after the adapter is green) → `172.006-T` (GREEN plus
  structural verification **after** wiring) → `172.007-T` (live-corpus invariant
  audit). Superseded orderings were rewritten out of the bodies rather than
  annotated.
* **D14 closed as a plan, not as an implementation.** `172.001-T` now owns the
  **atomic** Part 1b update of `.github/instructions/backlogit.instructions.md`
  together with its template mirror
  `templates/instructions/backlogit.instructions.md.tmpl`, including
  install-manifest checksum regeneration, so the two can never drift apart. New
  task **`172.010-T`** adds an **inventory-backed** structural verifier that
  derives the producer surface across agents, skills, instructions, docs and
  `src/`, and proves a synthetic bypassing producer is caught — replacing the
  two-template check. No source or template file was modified in this cycle.
* **Finding 7 closed.** The plan carries the seven identity fields.

`180-S` now carries eleven members (covering feature plus ten tasks). Terminal
tasks are `172.007-T` and `172.010-T`, which are mutually independent.

### Disposition

`REMEDIATED-PENDING-REVIEW` at plan revision 6. **No PASS is asserted.** The
next reviewer pass is **attempt 07**, independent and terminal.

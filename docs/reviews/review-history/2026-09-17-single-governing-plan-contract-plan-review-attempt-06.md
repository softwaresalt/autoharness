---
title: "Plan review attempt 06 — Single governing plan contract"
description: "Immutable per-attempt plan-review artifact. Part 1 records the independent review opened against docs/plans/2026-09-17-single-governing-plan-contract-plan.md at revision 5 — verdict BLOCKED on five coupled contract defects: an unenforced plan identity wire format that still used status as a plan-role substitute and retained plan_revision_reviewed, an unenforced verdict-manifest wire format, an undecidable legacy boundary, a self-contradictory history-input rule, and a task DAG whose leak-token verifier preceded the assembler and predicate that own the token. Part 2 records, separately, the operator-authorized remediation that raised the plan to revision 6. Disposition REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-06.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 6
attempt_range: "06"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-single-governing-plan-contract-plan-review-attempt-05.md
plan_path: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
plan_id: single-governing-plan-contract
reviewed_revision: 5
remediation_revision: 6
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: C9CD24F3
feature_id: 171-F
shipment_id: 179-S
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
  - "plan-identity"
  - "verdict-manifest"
  - "review-input-set"
  - "legacy-boundary"
---

# Plan review attempt 06 — Single governing plan contract

Two strictly separated halves. **Part 1** is the independent reviewer's verdict
at plan revision 5. **Part 2** is the **operator-authorized** remediation that
followed. The separation is the contract this very plan specifies; see
`docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md`.

---

## Part 1 — Review verdict at plan revision 5

Opened against **plan revision 5**; verdict **BLOCKED**. Operative input set:
plan revision 5 and the live `171-F` / `179-S` records at entry. Attempts 01–02,
03, 04 and 05 are superseded history and were excluded.

dispatch_mode: `declared-degradation`
decision: `BLOCKED`

### P1 findings

**C7 — plan identity had no single enforced wire format.** Across the plan,
`171-F`, `179-S`, the `171.*` tasks and the live verdict manifests, identity was
expressed inconsistently: `status` was used as a plan-role substitute, and
`plan_revision_reviewed` persisted as a field name. A contract whose own
artifacts disagree about its wire format cannot be enforced.

**C8 — the verdict manifest had no single enforced wire format.** Key names
varied (`latest_attempt_artifact` vs. `latest_artifact`),
`carried_forward_context[]` was sometimes absent rather than empty, and roster
entries carried one revision number that merged the reviewed revision with the
Stage-produced one.

**C9 — the legacy boundary was not mechanically decidable.** Without a decidable
boundary, a **newly authored** plan that simply omits `plan_id` passes as
"legacy" instead of blocking.

**C10 — the history-input rule contradicted itself.** The plan simultaneously
required that earlier attempts never be operative and permitted carried-forward
history to enter the operative input set, and the leak rule keyed partly on
naming. `171.013` and related surfaces carried the contradiction.

**C11 — the task DAG mis-owned `REVIEW_INPUT_HISTORY_LEAK`.** The verifier task
followed only the RED test, not the assembler (`171.004-T`) and the
leak-predicate implementation (`171.013-T`) that actually own the token, which
invited a duplicate implementation of the predicate.

---

## Part 2 — Operator-authorized remediation to plan revision 6

**Authorization:** `operator-authorized-final-extra-cycle`. Stage work; nothing
below was verified closed by an independent reviewer.

* **C7 closed.** One identity wire format is now stated once and applied
  everywhere: `plan_id`, `plan_role` (enum `active|superseded|history`),
  `revision`, path-valued `supersedes`, path-valued `superseded_by` (null iff
  active), ordered `source_history` path list, and `review_manifest` path.
  `status` is explicitly **not** a plan-role substitute, and
  `plan_revision_reviewed` is removed as a field name. All six portfolio plans
  now carry the seven fields; legacy `linked_review`, `review_history` and
  `latest_review_*` keys were removed.
* **C8 closed.** One manifest wire format of **exactly eight keys**: `plan_id`,
  `plan_path`, `plan_revision`, `latest_attempt`, `verdict`, `latest_artifact`,
  `attempts[]`, `carried_forward_context[]` (always present, possibly empty).
  Roster entry shape is
  `{attempt, artifact, reviewed_revision, verdict, remediation_revision, disposition}`;
  `verdict` is reviewer-only (`PASS|BLOCKED`), `REMEDIATED-PENDING-REVIEW` is a
  **disposition** and never a verdict, and the top-level `verdict` is **derived**
  from the highest-numbered roster entry so a fabricated headline is a detectable
  inconsistency. All six live portfolio manifests were normalized to it.
* **C9 closed.** The boundary is an **immutable committed allowlist**,
  `schemas/plan-legacy-allowlist.json`, generated once at introduction with
  exact-path membership, append-never and edit-never. A date cutoff was
  explicitly rejected as author-controlled and gameable. On-allowlist with no
  `plan_id` reports `PLAN_LEGACY_UNIDENTIFIED`; **off-allowlist omission blocks
  with `PLAN_IDENTITY_MISSING`**, so a newly authored omission can never pass as
  legacy.
* **C10 closed.** The contradiction was removed, not annotated: earlier attempts
  are **never** operative; `carried_forward_context[]` entries appear **only** in
  the `context` band of the two-band `ReviewInputSet`; and
  `REVIEW_INPUT_HISTORY_LEAK` is **naming-independent**, keyed on four metadata
  facts — review-artifact schema match, `plan_role: superseded|history`,
  `source_history` membership, `carried_forward_context[]` membership — never on
  filename, directory or title. `171.013-T` and every related surface were
  rewritten.
* **C11 closed.** `171.013-T` is the **sole** implementer of the predicate and
  sole emitter of the token. `171.006-T` implements five tokens directly and
  **delegates** the sixth, with real backlogit dependency edges added onto
  `171.004-T` and `171.013-T`. `171.011-T` asserts the single-definition
  invariant structurally, so a duplicate implementation fails rather than
  silently coexisting. New risks R8–R11 and hardening rows H10–H13 record the
  reasoning.

### Disposition

`REMEDIATED-PENDING-REVIEW` at plan revision 6. **No PASS is asserted.** The
next reviewer pass is **attempt 07**, independent and terminal.

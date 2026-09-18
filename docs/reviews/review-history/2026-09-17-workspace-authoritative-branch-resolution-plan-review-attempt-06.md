---
title: "Plan review attempt 06 — Workspace-authoritative branch resolution"
description: "Immutable per-attempt plan-review artifact. Part 1 records the independent review opened against docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md at revision 5 — verdict BLOCKED on an over-broad divergence set that classified the whole @{...} family as divergence from git check-ref-format --branch rather than as shared rejection, and on an impossible repository-wide ban on the literal workspace_convention. Part 2 records, separately, the operator-authorized remediation that raised the plan to revision 6. Disposition REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation and asserts no PASS."
doc_type: review
source: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-06.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 6
attempt_range: "06"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-05.md
plan_path: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
plan_id: workspace-authoritative-branch-resolution
reviewed_revision: 5
remediation_revision: 6
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 86498B64
feature_id: 170-F
shipment_id: 178-S
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
  - "branch-resolution"
  - "check-ref-format"
  - "divergence-set"
---

# Plan review attempt 06 — Workspace-authoritative branch resolution

Two strictly separated halves. **Part 1** is the independent reviewer's verdict
at plan revision 5. **Part 2** is the **operator-authorized**, not
reviewer-approved, remediation that followed. See
`docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md`
for why the two are never merged.

---

## Part 1 — Review verdict at plan revision 5

Opened against **plan revision 5**; verdict **BLOCKED**. Operative input set:
plan revision 5 and the live `170-F` / `178-S` records at entry. Attempts 01–02,
03, 04 and 05 are superseded history and were excluded.

dispatch_mode: `declared-degradation`
decision: `BLOCKED`

### P1 findings

**B5 — the divergence set was over-broad, and in the direction that falsifies
the superset claim.** Revision 5 described the whole `@{...}` family as
diverging from `git check-ref-format --branch`. It does not. `git` runs
`interpret_branch_name`, which expands **only** the `@{-N}` previous-checkout
form, and then `check_refname_format`, whose "cannot contain `@{`" rule rejects
everything else. `foo@{1}`, `main@{0}`, `a@{b}`, `@{u}`, `@{upstream}`,
`foo@{upstream}` and `@{-0}` all exit 128 — they agree with V10 and are
**shared rejections**. Classifying them as divergences makes the
strict-superset-of-rejections assertion false in exactly the direction it is
supposed to guarantee. The true divergence set D has exactly two shapes: the
bare `@`, and `@{-N}` for N ≥ 1 that *actually resolves* in the invoking
repository. The over-broad prose had propagated into `170-F`, `178-S` and the
`170.*` bodies, notably `170.009` and `170.010`.

**B6 — the `workspace_convention` criterion was not executable.** Revision 5
required that the literal string `workspace_convention` appear nowhere in the
repository. That is unsatisfiable by construction: the plan, the review history,
the decision record and the `170-*` backlog records all necessarily name the
retired third rung in order to retire it. A criterion no artifact can satisfy is
not a gate.

**Portfolio-wide finding 7 (relayed).** The plan did not carry the mandated
seven-field plan identity wire format.

---

## Part 2 — Operator-authorized remediation to plan revision 6

**Authorization:** `operator-authorized-final-extra-cycle`. Stage work; nothing
below was verified closed by an independent reviewer.

* **B5 closed.** `170-F`, `178-S` and every affected `170.*` body now state D as
  exactly two shapes — bare `@`, and fixture-resolvable `@{-N}` (N ≥ 1) — with
  the wider `@{...}` family named explicitly as **shared rejection** at exit 128.
  Because `@{-N}` resolution is repository-state-dependent, its arm is asserted
  only inside a **hermetic fixture repository** with scripted checkout history;
  probing the ambient reflog is prohibited. The superseded broad-family prose was
  **rewritten out** of `170.009-T` and `170.010-T` rather than annotated, and the
  stale provenance trailers on `170.001-T` and `170.003-T`…`170.008-T` were
  normalized. Behaviour is measured against git 2.55.0.windows.5.
* **B6 closed.** `170.002-T` now carries a **scoped executable** criterion in
  three parts: (a) zero occurrences of the literal under `src/autoharness/`,
  `schemas/*.json` and `.autoharness/config.yaml` key paths — i.e. no fallback
  resolver, config or runtime source; (b) a frozen two-member `resolution_source`
  enum `{explicit_contract, title_alias}`; (c) all remaining occurrences confined
  to an enumerated historical set (the plan, the `170-*` records,
  `docs/reviews/`, `docs/decisions/`, `docs/memory/`). Verification stays
  auditable because the permitted set is enumerated rather than open.
* **Finding 7 closed.** The plan carries the seven identity fields.

### Disposition

`REMEDIATED-PENDING-REVIEW` at plan revision 6. **No PASS is asserted.** The
next reviewer pass is **attempt 07**, independent and terminal.

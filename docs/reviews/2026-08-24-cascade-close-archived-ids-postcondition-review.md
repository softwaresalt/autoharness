---
title: "Plan Review: cascade-close archived_ids post-condition correction"
date: 2026-08-24
source: "docs/reviews/2026-08-24-cascade-close-archived-ids-postcondition-review.md"
doc_type: "review"
reviews: docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md
hardening: docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-hardening.md
deliberation: .backlogit/queue/027-DL.md
stash_id: 5CFA8198
verdict: PASS
cycles: 1
agent: stage
---

# Plan Review - cascade-close `archived_ids` post-condition correction

Adversarial review of
`docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md`
(post-hardening, amendments A1-A4 applied in place).

## Review dimensions

### 1. Is the diagnosis actually correct? (the highest-stakes question)

The plan reverses a shipped safety claim. If the diagnosis were wrong, the fix
would DISABLE a working gate. Checked independently:

* `archiveItems()` L1130 `if item.Status == models.StatusArchived { continue }`
  - the skipped item is not appended to the returned slice. Verified by reading
  the function body, not by inference from a summary.
* That slice reaches `ArchivedIDs` at L670 -> L709. Verified.
* Candidate collection applies the same exclusion at L799 (feature) and L808
  (descendants). Verified.
* Empirically corroborated: 154-S and 153-S logs both show the predicted shape.

The diagnosis holds. **No finding.**

### 2. Does the new gate preserve both safety properties?

* "Nothing outside scope was touched" -> `archived_ids - allowed_ids == empty`.
  Strength UNCHANGED: `allowed_ids` is exactly the old expected set, so no ID
  that would previously have been flagged is now permitted.
* "Nothing that had to be done was skipped" -> `required_ids - archived_ids
  == empty`. Strength UNCHANGED for every artifact that had work to do;
  relaxed ONLY for artifacts that provably had none.

The relaxation is scoped by a snapshot of declared status, not by a blanket
allowance. **No finding.**

### 3. F1 (MINOR, addressed) - could `required_ids` be empty in a legitimate close, making the check vacuous?

Yes - if every allowed artifact were already truly archived. But in that case
the cascade genuinely has nothing to do, and the allowed-set check plus the
preserved persisted-final-state and shipment-status checks still apply. The
shipment record itself is never pre-archived on a live close, so `required_ids`
contains at least the shipment record in every real invocation.

The plan's step 5 report already records `required_ids`, so a vacuous case is
VISIBLE in the report rather than silent. Sufficient. **Addressed, no
amendment.**

### 4. F2 (MINOR, addressed) - does A4 fully close the snapshot-timing hole?

A4 pins the Step 0(b) snapshot and adds scenario 8. Reviewed for the subtler
variant: could an implementer capture Step 0(b) but re-derive `required_ids`
after the call from the snapshot's IDs while re-reading statuses? A4's "never a
freshly-read or assumed value" language, inherited verbatim from the step 4
precedent, forbids exactly this. **Addressed.**

### 5. F3 (MINOR, addressed) - A2's anti-merge rule is unusual; is it justified?

Forbidding two conditions from being merged into one test is an unusual
constraint to write into contract text. It is justified here by a concrete,
same-session precedent: external defect `B57F9E24` is caused by precisely this
- `json.Unmarshal(...) == nil && probe.SchemaVersion == 1` conflates "is this
valid JSON?" with "is this V1?". Citing a live defect rather than an abstract
principle makes the constraint defensible to a future editor. **Addressed.**

### 6. Scope discipline (P-021)

Every non-goal from stash `5CFA8198` is carried into the plan verbatim in
substance: no engine change, no fresh spike, no relaxation of out-of-scope ID
detection, no cascade-selection or safe-close change, no backlogit blocker, no
rewriting of the 154-S closure or changelog history. The external workspace is
read-only throughout. T4 explicitly preserves the historical closure record.
**No finding.**

### 7. Task granularity (2-hour rule, width isolation)

Four tasks, each touching one surface family: policy template (T1), skill
template (T2), tests (T3), docs (T4). T2 is the largest and is correctly the
only one rated complexity `high`. No task combines template work with CLI or
schema work. Dependency chain `T1 -> T2 -> T3`, `T4` after `T3`, is coherent
and matches the normative-source-before-implementation ordering.
**No finding.**

### 8. Testability

Every normative clause maps to at least one scenario in T3: clause 4 ->
scenarios 5 and the unexpected-ID halt-string assertion; clause 5 -> scenario 4
plus the required-ID halt-string assertion; clause 6 -> scenarios 2 and 3;
clause 1 -> scenarios 7 and 8; preserved checks -> scenario 6. No orphan
clause. **No finding.**

### 9. Reversibility

All changes are text-only in templates, tests, and docs. No data migration, no
schema change, no engine dependency. Fully revertible by `git revert`.
**No finding.**

## Findings summary

| ID | Severity | Status |
|----|----------|--------|
| F1 | MINOR | Addressed - vacuity is visible in the step 5 report; shipment record always in `required_ids` |
| F2 | MINOR | Addressed by A4 |
| F3 | MINOR | Addressed - constraint justified by live precedent B57F9E24 |

No MAJOR or BLOCKING findings. No new amendments required beyond A1-A4.

## Verdict

**PASS** (cycle 1 of a maximum 3).

The plan corrects a genuinely false claim, preserves both safety properties of
the gate it modifies at full strength, is grounded in engine source rather than
the black-box evidence it supersedes, and is decomposed into four
width-isolated tasks each inside the 2-hour rule. Cleared for harvest.

---
title: "Plan Hardening: cascade-close archived_ids post-condition correction (P-006)"
date: 2026-08-24
policy: P-006
hardens: docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md
source_deliberation: .backlogit/queue/027-DL.md
source_stash: 5CFA8198
features: [147-F]
shipments: [155-S]
source: docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-hardening.md
doc_type: plan-hardening
agent: stage
---

# Plan Hardening (P-006)

## Why hardening is required

`requires_plan_hardening: yes`. Three independent elevated-blast-radius signals:

1. **Two template families in one change.** `templates/policies/` and
   `templates/skills/` both mutate. A correction applied to one and not the
   other leaves the shipped contract self-contradictory in exactly the way that
   produced this bug.
2. **The artifact under change IS a fail-closed safety control.** Every future
   cascade close, for both Stage and Ship, runs this gate. An error here does
   not fail loudly at edit time - it fails silently, later, on somebody else's
   shipment.
3. **The change loosens a check.** Any edit that makes a safety gate accept
   more inputs than before carries an inherent risk of accepting too much. This
   is the precise class of change that warrants adversarial review before
   decomposition.

## Hardening Findings and Binding Amendments

### H1 - "must never be relaxed" is being relaxed; the plan must say so explicitly (Amendment A1, BINDING)

The current text does not merely assert full-set equality - it forbids its own
amendment ("must never be relaxed to exclude them", policy L444; "which is why
it must never be relaxed", skill L567). A future reader who encounters the new
two-set gate WITHOUT an explicit record of this supersession will reasonably
conclude the gate was tampered with, since the prior text told them it never
legitimately could be.

**Amendment A1 (BINDING):** T1 and T2 must each carry an explicit, in-artifact
supersession note stating that the prior never-relax clause is withdrawn, WHY
(it protected a claim that was never true of the engine), and that the safety
properties it was protecting are now carried by the two-set gate. A changelog
row alone is insufficient - the note must sit at the point of change, because
that is where the contradicting instruction sat.

### H2 - the plan must forbid Option A collapse structurally, not just narratively (Amendment A2, BINDING)

Plan risk R1 identifies over-correction into a bare allowed-set check, but
mitigates it only by a test scenario. Test scenarios are removable by the same
hand that removes the check.

**Amendment A2 (BINDING):** the skill's step 3 must state the two set relations
as TWO SEPARATELY LABELLED, INDEPENDENTLY FAILING conditions with two DISTINCT
halt messages (as the plan already specifies), and must state that neither
condition may be evaluated as a precondition of the other, nor merged into a
single combined test. This mirrors the structural lesson already learned in
backlogit's own V1-probe defect (external tracker B57F9E24), where conflating
two questions into one condition is the root cause. Additionally, T3 must
assert the PRESENCE of both distinct halt strings in the template text, so
deleting one condition breaks a test rather than silently widening the gate.

### H3 - "qualifying feature members" is load-bearing and currently undefined at the point of use (Amendment A3, BINDING)

`allowed_ids` includes "qualifying feature members". If that term is left to
the reader, the allowed set becomes elastic - and an elastic ALLOWED set is
precisely how out-of-scope mutations get waved through. The engine's own
behavior here is subtle: the covering feature appears in `archived_ids` because
it transits `done` inside the invocation, which is an implementation detail the
contract must NOT depend on.

**Amendment A3 (BINDING):** T2 must define "qualifying feature members" at the
point of use by reference to the Step 0(c) classifier's own qualifying-feature
determination - the same set the classifier already computes - and must state
that the definition is deliberately independent of HOW the engine happens to
transition them. The contract asserts membership in the allowed set, never a
mechanism.

### H4 - the snapshot must be the Step 0(b) snapshot, not a fresh read (Amendment A4, BINDING)

The plan says "pre-close snapshot" but does not pin WHICH snapshot. Step 4
(parent_id preservation) already contains the hard-won rule that the comparison
must be against the Step 0(b) snapshot and "never a freshly-read or assumed
value, since the field being verified is the very one a cascade could have just
cleared." The identical hazard applies here with greater force: `status` is the
exact field the cascade mutates. A post-close read of `status` would report
`archived` for everything the cascade just archived, collapsing `required_ids`
to empty and silently disabling the completeness check entirely.

**Amendment A4 (BINDING):** T2 must specify that the declared-status snapshot
is captured in Step 0(b), BEFORE the cascade invocation, and must carry the
same "never a freshly-read or assumed value" warning with the reason stated.
T3 must include a scenario in which a post-close status read would pass but the
Step 0(b) snapshot correctly HALTs, so this failure mode is pinned by test and
not only by prose.

## Non-amendments (considered, deliberately not imposed)

* **Merging T1 and T2 into one task.** Rejected: they are separate template
  families, and the split keeps each task inside the 2-hour rule. The
  self-contradiction risk H1 raises is addressed by A1 and by shipping both in
  one shipment, not by merging the tasks.
* **Adding a backlogit-side test as a dependency.** Rejected: 027-DL Q1 records
  it as OPTIONAL and NON-BLOCKING, and the stash entry names "no Backlogit-side
  work as a blocker" as an explicit non-goal.
* **Re-running a behavioral spike to re-validate the engine claim.** Rejected:
  the claim is now grounded in engine SOURCE (`shipment_lifecycle.go` L1130,
  L799, L808), which is stronger evidence than the black-box arms it replaces,
  and a fresh spike is an explicit non-goal of the entry.

## Verdict

**HARDENED.** Four binding amendments (A1-A4). All are additive constraints on
T1-T3; none changes the selected direction, the task count, or the scope
boundary. Plan may proceed to `plan-review`.

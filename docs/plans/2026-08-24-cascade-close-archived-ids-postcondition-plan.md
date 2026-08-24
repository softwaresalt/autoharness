---
title: "P-015 / shipment-reconcile cascade-close archived_ids post-condition - replace false full-set equality with a two-set allowed/required gate"
date: 2026-08-24
source: "docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md"
doc_type: "plan"
stash_id: 5CFA8198
deliberation: ".backlogit/archive/027-DL.md"
requires_plan_hardening: yes
hardening_present: yes
hardening: docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-hardening.md
review: docs/reviews/2026-08-24-cascade-close-archived-ids-postcondition-review.md
review_verdict: PASS
amendments: "A1, A2, A3, A4 (binding, applied in place)"
execution_prerequisite: "SATISFIED 2026-08-24 by commit 470eff090780dda59344061ece7196e7a18428d3 - 154-S predecessor-closure evidence repair (Ship-owned, OUTSIDE 155-S) landed; was BLOCKING. See 'Execution prerequisite' section"
execution_prerequisite_status: satisfied
execution_prerequisite_satisfied_by: 470eff090780dda59344061ece7196e7a18428d3
blast_radius: "elevated (two template families: templates/policies/workflow-policies.md.tmpl P-015 clause + changelog, and templates/skills/shipment-reconcile/SKILL.md.tmpl cascade-close step 3 and its preamble; one new repo-side regression test module; three evidence documents under docs/spikes and docs/compound. No installed dogfood counterpart exists for either template. No schema, no CLI, no backlogit engine change.)"
---

# Implementation Plan - cascade-close `archived_ids` post-condition correction

Date: 2026-08-24
Agent: Stage (planning only - Ship executes)
Stash source: `5CFA8198` (DEFERRED SCOPE EXPANSION, P-021 C2 capture)
Deliberation: `027-DL`
Classification: **bug / false safety-invariant claim in shipped autoharness contract text**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)
Source refs: feature `146-F` (archived), shipment `154-S` (shipped), PR #405,
review threads `PRRT_kwDORzpWpM6bj72w` and `PRRT_kwDORzpWpM6bj72-`

## Execution prerequisite (SATISFIED 2026-08-24, Ship-owned, OUTSIDE this shipment)

**Status: SATISFIED.** Ship landed the narrow predecessor-closure evidence
repair in commit `470eff090780dda59344061ece7196e7a18428d3`
(*docs(closure): add machine-readable conditions block to 154-S closure
evidence*). `docs/closure/154-S-146-F-post-merge-closure.md` now carries a
machine-readable `conditions:` list whose single entry
(`5CFA8198-archived-ids-contract-reconciliation`) records the
**capture-and-ownership handoff** as `satisfied: true` with concrete
`evidence:` - the `5CFA8198` -> `027-DL` -> `147-F` / `155-S` chain - and
explicitly states that successor shipment `155-S` owns implementation of the
reconciliation itself. The `READY_WITH_CONDITIONS` verdict value is unchanged
and the historical closure narrative was not rewritten.

Re-verified read-only against the installed gate helpers at this HEAD:
`closure_status=READY_WITH_CONDITIONS`, `compaction_status=done`,
`conditions` non-empty, `_closure_conditions_satisfied=True`,
`_closure_artifact_complete=True`. The `PREDECESSOR_CLOSURE_INCOMPLETE`
pre-claim block for `155-S` is therefore cleared.

**Scope note (unchanged).** What the condition records as satisfied is the
capture-and-ownership handoff, **not** the correction work itself. `155-S`
has **not** shipped: `147.001-T`-`147.004-T` remain unexecuted and `155-S`
remains queued and unclaimed. Clearing this prerequisite makes `155-S`
*claimable*; it does not make it *done*, and stash `5CFA8198` still must not
be archived until the corrections have shipped (work-contract item 5).

### Historical record - why this was BLOCKING (retained, superseded)

Added 2026-08-24 by a narrow Stage follow-up, after the original handoff, and
true until commit `470eff09`. At that time **`155-S` could not be claimed in
its then-current state.**

The installed pre-claim topology gate
(`src/autoharness/gates/topology.py`, `shipment_readiness`) returned:

```text
PREDECESSOR_CLOSURE_INCOMPLETE: predecessor 154-S is terminal but missing
required closure evidence
```

**Cause (read-only evidence, reproduced 2026-08-24, since remediated).**
`docs/closure/154-S-146-F-post-merge-closure.md` declared
`closure_status: READY_WITH_CONDITIONS` and `compaction_status: done`, but
carried **no machine-readable `conditions:` frontmatter list**.
`_closure_artifact_complete` (`topology.py:294`) accepts
`READY_WITH_CONDITIONS` only when `_closure_conditions_satisfied` finds a
non-empty `conditions:` list in which every entry is a mapping with
`satisfied: true` and a non-empty `evidence:` string. With `conditions` absent
(`None`) the helper returned `False`, so `closure_complete("154-S")` was
`False` and `shipment_readiness` blocked. Direct evaluation at the time
confirmed `closure_status=READY_WITH_CONDITIONS`, `compaction_status=done`,
`conditions=None`, `complete=False`.

The closure artifact's **body** already recorded the captured follow-up
(`5CFA8198`, now deliberation `027-DL` -> feature `147-F` / shipment `155-S`).
So this was an evidence-**form** gap in Ship-owned closure frontmatter, not a
genuinely unmet release condition, and not a defect in this plan. The repair
in `470eff09` closed exactly that form gap.

**Constraints that governed the repair (honoured, retained for the record):**

* Stage did **not** modify the Ship-owned closure artifact and did **not**
  bypass, disable, or weaken the gate. The gate behaved correctly throughout;
  only the frontmatter was incomplete, and Ship supplied it.
* The repair was deliberately **not** added to `T1`-`T4` and **not** added to
  the `155-S` manifest. Doing so would have been **circular**: the gate blocks
  the claim of `155-S`, so no work item inside `155-S` could ever unblock it.
  It landed as separate, narrow, pre-claim Ship work, as required.
* It does **not** overlap `T4`. `T4`'s append-only forward cross-reference to
  `027-DL` and this plan stays inside `155-S` and remains a body-only addition;
  the prerequisite repair touched only the frontmatter `conditions:` block and
  happened first.
* It did not rewrite the historical 154-S closure narrative or its verdict
  (plan non-goal preserved).

## Goal

Make the cascade-close post-condition assert something TRUE, without weakening
either of the two safety properties it actually provides.

1. Correct P-015's fully-covered-root exception item 7, which asserts a false
   full-set equality over `archived_ids`.
2. Rewrite the `shipment-reconcile` cascade-close step 3 gate as a two-set
   `allowed_ids` / `required_ids` check keyed on a pre-close snapshot of
   DECLARED status.
3. Pin the new contract with regression coverage, including the specific
   confusion that invalidated the original spike (`archive/` location vs.
   declared `status: archived`).
4. Correct and supersede the evidence trail that manufactured the false
   invariant, without rewriting history.

## Background (from 027-DL)

`archived_ids` is a TRANSITION LOG, not a manifest echo. Verified by reading
backlogit engine source at `b0772938` (READ-ONLY, external workspace):

* `internal/core/shipment_lifecycle.go` `archiveItems()` L1122-L1139 -
  `if item.Status == models.StatusArchived { continue }`. The item is skipped
  AND is not appended to the returned slice that becomes `ArchivedIDs`
  (L670, L709).
* Candidate collection L799 / L808 applies the same exclusion to features and
  descendants.

So a truly pre-archived artifact has no transition to report and is correctly
absent. The covering feature still appears because it is temporarily moved to
`done` and re-archived within the invocation - a genuine transition.

The 2026-08-18 spike built its "pre-archived" arms with `move --status done`,
which relocates the record but leaves declared `status: done`. Against the
L1130 guard `done != archived`, so those artifacts WERE archived by the call
and DID legitimately appear. All three arms were, at the guard that matters,
the control arm. The invariant was never exercised.

## Non-goals

* No backlogit engine behavior change, and no backlogit-side blocker. An
  upstream doc/test follow-up is OPTIONAL and NON-BLOCKING (027-DL Q1).
* No fresh behavior spike. Prior-evidence review plus engine-source reading is
  the authorized method for this entry.
* No relaxation of unexpected / out-of-scope ID detection. That check keeps
  full strength.
* No change to cascade SELECTION (Step 0(c) classifier), to safe-close mode, or
  to any other shipment lifecycle behavior.
* No change to the protected-set rules. The protected set retains NO
  pre-archived exemption.
* No rewriting of the 154-S closure artifact or of existing changelog history.
* No mutation of `C:\Source\GitHub\backlogit`.

## Normative contract to implement

1. **Snapshot semantics.** The pre-close snapshot records each manifest
   member's DECLARED `status` field. "Truly archived" means declared
   `status: archived`. Directory location alone is NEVER sufficient: a record
   residing in `{{BACKLOG_DIRECTORY}}/archive/` while declaring `status: done`
   is NOT truly archived.
   **(A4, BINDING)** This snapshot is the **Step 0(b) snapshot**, captured
   BEFORE the cascade invocation - never a freshly-read or assumed value, since
   `status` is the very field the cascade mutates. A post-close read would
   report `archived` for everything the cascade just archived, collapsing
   `required_ids` to empty and silently disabling the completeness check.
   Once Step 0(c) identifies qualifying feature members, record their declared
   pre-close statuses in the same status map before invoking the cascade.
2. `allowed_ids` = manifest task items + qualifying feature members + the
   shipment record.
   **(A3, BINDING)** "Qualifying feature members" means the set the Step 0(c)
   classifier already determines as qualifying - defined at the point of use,
   and deliberately independent of HOW the engine happens to transition them.
   The contract asserts SET MEMBERSHIP, never a mechanism.
3. `required_ids` = the shipment record (unconditionally) + every other
   allowed artifact NOT truly `status: archived` in the pre-close status map.
   The shipment record MUST NOT be omitted by deriving this set only from
   Step 0(b)'s manifest-member entries.
4. FAIL when `archived_ids - allowed_ids` is non-empty ->
   `HALT - cascade archived unexpected artifact {id}` + P-005.
5. FAIL when `required_ids - archived_ids` is non-empty ->
   `HALT - cascade did not archive required artifact {id}` + P-005.
6. An already-archived allowed member MAY be included or omitted from
   `archived_ids`; neither outcome fails the gate.
   **(A2, BINDING)** Conditions 4 and 5 are TWO SEPARATELY LABELLED,
   INDEPENDENTLY FAILING conditions with two DISTINCT halt messages. Neither
   may be evaluated as a precondition of the other, and the two MUST NOT be
   merged into a single combined test. (Conflating two questions into one
   condition is the documented root cause of external defect `B57F9E24`.)
7. PRESERVED UNCHANGED: persisted-final-state verification, `returned_ids`
   empty check, parent_id preservation against the Step 0(b) snapshot,
   shipment-status verification, protected-set rules, and the no-substitution
   rule.

## Tasks

Four tasks. Policy and skill are SPLIT so each task touches exactly one
template family (width isolation) and each stays inside the 2-hour rule.

### T1 - P-015 policy clause correction + changelog correction entry

File: `templates/policies/workflow-policies.md.tmpl`

* Rewrite fully-covered-root exception item 7 (currently L444). REMOVE the
  claim that the cascade operation "returns them in its `archived_ids` result
  exactly as it does newly-archived members" and the assertion that the
  exact-match post-condition "remains unchanged and must never be relaxed to
  exclude them."
* REPLACE with the correct definition: `archived_ids` reports the artifacts
  ACTUALLY TRANSITIONED to archived during that invocation; a truly
  `status: archived` member has no transition to report and is correctly
  absent.
* PRESERVE, verbatim in force: that a pre-archived manifest member does not
  disqualify the CASCADE verdict, does not constitute a classifier ambiguity
  or unresolved precondition, does not authorize safe-close fallback; and the
  no-substitution rule.
* PRESERVE fail-closed handling of unexpected / out-of-scope IDs, and point
  item 7 at the two-set gate as the live guard.
* Add a NEW changelog row (next version, `{{DATE}}`) recording this as a
  CORRECTION of the 1.19.0 row. Do NOT edit or delete the 1.19.0 row (L767).
* **(A1, BINDING)** Add an explicit in-artifact SUPERSESSION NOTE at the point
  of change stating that the prior "must never be relaxed" clause is WITHDRAWN,
  WHY (it protected a claim that was never true of the engine), and that the
  safety properties it guarded are now carried by the two-set gate. A changelog
  row alone is insufficient - the note must sit where the contradicting
  instruction sat.

Acceptance: no surviving full-set-equality claim in the policy template; the
1.19.0 changelog row is byte-identical to before; new correction row present.

Size S / complexity medium.

### T2 - shipment-reconcile cascade-close two-set gate

File: `templates/skills/shipment-reconcile/SKILL.md.tmpl`

* Amend the pre-archived preamble (L535-L567) so classification records
  DECLARED STATUS, not directory location, and explicitly distinguishes a true
  `status: archived` from a merely relocated `status: done`. Remove the
  citation of the superseded spike as authority for byte-identical
  `archived_ids`, and remove "must never be relaxed" as applied to full-set
  equality.
* Rewrite step 3 (L600-L604) as the two-set gate: compute `allowed_ids` and
  `required_ids` per the normative contract above; emit
  `HALT - cascade archived unexpected artifact {id}` for the allowed-set
  breach and `HALT - cascade did not archive required artifact {id}` for the
  required-set breach; both P-005.
* Update step 6's gate decision (L618-L621) to reference both set relations
  instead of "matches exactly".
* Update step 5's cascade-close report to record the snapshot, `allowed_ids`,
  `required_ids`, and the two set differences.
* PRESERVE step 2 (`returned_ids` empty), step 4 (parent_id preservation
  against the Step 0(b) snapshot), the protected-set rules and their absence
  of any pre-archived exemption, the no-substitution rule, and persisted
  final-state verification.
* Run a diagnostic grep over `templates/`, `docs/`, `.github/` for
  restatements of the false claim (`nothing more, nothing less`, `never be
  relaxed`, `full item set`, `archived_ids`). T2 corrects only the skill
  template; route policy-template findings to T1 and documentation findings to
  T4. Record any other-family finding for its owning task rather than editing
  it in T2 (027-DL Q2).
* **(A1, BINDING)** Carry the same explicit supersession note at the skill's
  point of change (the L557-L567 paragraph that pins the never-relax rule).
* **(A3, BINDING)** Define "qualifying feature members" at the point of use by
  reference to the Step 0(c) classifier's own determination; assert membership,
  never mechanism.
* **(A4, BINDING)** Specify that the declared-status snapshot is the Step 0(b)
  snapshot captured before the invocation, carrying the same "never a
  freshly-read or assumed value" warning as step 4, with the reason stated.

Depends on T1 (policy is the normative source; skill implements it).

Acceptance: step 3 states both set relations; no surviving full-set-equality
claim; all preserved checks textually intact; frontmatter valid; no unresolved
`{{...}}` beyond legitimate template variables.

Size M / complexity high.

### T3 - regression coverage

File: new `tests/test_cascade_close_archived_ids_postcondition.py` (repo-side
contract test over the template text, matching the existing
`tests/test_shipment_reconcile_*.py` pattern).

Cover the seven scenarios named in the work contract:

1. all-new members -> gate passes;
2. omitted truly pre-archived tasks -> gate passes;
3. an allowed pre-archived member still INCLUDED in `archived_ids` -> passes;
4. missing required IDs (`required_ids - archived_ids` non-empty) -> HALT;
5. unexpected IDs (`archived_ids - allowed_ids` non-empty) -> HALT;
6. incorrect persisted final state -> HALT (preserved check still asserted);
7. an archive-directory record declaring `status: done` is NOT treated as
   truly archived -> it is therefore in `required_ids`, and omitting it HALTs.

Scenario 7 is mandatory: it pins the exact confusion that invalidated the
2026-08-18 spike (027-DL Option D rejection).

**(A2, BINDING)** Also assert the PRESENCE of BOTH distinct halt strings
(`cascade archived unexpected artifact` and `cascade did not archive required
artifact`) in the template text, so deleting either condition breaks a test
rather than silently widening the gate.

Also assert that the shipment record is an unconditional member of
`required_ids`, independent of Step 0(b)'s manifest-member entries, and that
the declared statuses of qualifying feature members are captured after Step
0(c) identifies them and before the cascade invocation.

**(A4, BINDING)** Add scenario 8: a case in which a POST-close status read
would pass but the Step 0(b) snapshot correctly HALTs - pinning the
snapshot-timing failure mode by test, not only by prose.

Also assert the policy template no longer contains the full-set-equality
claim, and that the 1.19.0 changelog row is preserved.

Depends on T1 and T2.

Size M / complexity medium.

### T4 - evidence trail correction

* `docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md` -
  prepend a SUPERSEDED banner: the arms were constructed with
  `move --status done` and therefore never produced true `status: archived`
  inputs; the byte-identical-shape finding is valid ONLY for
  relocated-but-`done` records and must not be cited as evidence about truly
  archived members; its L111-L115 recommendation against adjusting the
  post-condition is RETRACTED. Body otherwise preserved.
* `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md` -
  correct any dependence on the false full-set equality claim; add a
  cross-reference to 027-DL.
* `docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md` -
  RETRACT the "1.10.1 regression" framing. Record that the skip guard is
  longstanding, unconditional and correct, and that the defect was the
  autoharness expectation. Retract the ad hoc "operating rule" that PR #405
  review threads flagged.
* `docs/closure/` 154-S closure artifact - KEEP INTACT. Add a forward
  cross-reference to 027-DL and this plan only; do NOT rewrite the historical
  closure record or its READY verdict.

Independent of T1-T3 in content, sequenced after them for a coherent PR
narrative.

Acceptance: all three evidence docs carry an explicit correction/supersession
notice; 154-S closure body unchanged apart from an appended cross-reference;
docline frontmatter conformance preserved on every touched doc.

Size S / complexity low.

## Sequencing

PREREQUISITE (outside this shipment, Ship-owned, before the `155-S` claim):
154-S predecessor-closure evidence repair - **SATISFIED 2026-08-24 by commit
`470eff090780dda59344061ece7196e7a18428d3`**; see "Execution prerequisite"
above. No pre-claim work remains. `155-S` itself is still queued/unclaimed and
its implementation has not shipped.

`T1 -> T2 -> T3`, with `T4` after `T3`.

## Risks

* **R1 - over-correction into Option A.** A careless edit could leave only the
  allowed-set check, silently permitting a cascade that archived nothing.
  Mitigated by T3 scenario 4 and by the hardening doc's H2.
* **R2 - location-vs-status regression.** Re-introducing directory-location
  reasoning rebuilds the original defect. Mitigated by T3 scenario 7.
* **R3 - stale restatements.** The false claim may be restated elsewhere.
  Mitigated by T2's grep sweep.
* **R4 - downstream drift.** Already-installed copies in other workspaces keep
  the old gate until re-installed. Out of scope; the changelog correction entry
  must be explicit enough for a downstream reader to notice.

## Verification (Ship)

* Targeted contract coverage for
  `tests/test_cascade_close_archived_ids_postcondition.py`, the existing
  `tests/test_shipment_reconcile_*.py`, and
  `tests/test_shipment_closure_classification.py` is green.
* `PYTHONPATH=src python -m unittest discover -s tests` is green as the
  repository's canonical full test gate.
* `verify-workspace` shows no new schema blockers, blockers, warnings, or
  unresolved placeholders.
* Manual read-through confirming every PRESERVED check is textually intact.

---
title: "Plan review - Ship pre-archived manifest-member execution exclusion"
date: 2026-08-20
plan: docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md
hardening: docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-hardening.md
stash_id: B19E9662
deliberation: "022-DL (archived 2026-08-20 to .backlogit/archive/022-DL.md)"
verdict: PASS
---

# Plan Review - Ship pre-archived manifest-member execution exclusion

Date: 2026-08-20
Agent: Stage (plan-review gate)
Plan: `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md`
Hardening: `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-hardening.md` (HARDENED, H1-H7, amendments A1/A2 applied)
Stash: `B19E9662`  Deliberation: `022-DL` (archived 2026-08-20 to `.backlogit/archive/022-DL.md`)

## Verdict

**PASS** - 1 P1 raised and resolved by amendment A3; 3 P2 raised, 2 resolved by
amendment, 1 accepted as an execution-time verification item. 0 unresolved
P0/P1. Review-fix cycles used: 1 of 3.

## P1-1 (RESOLVED by amendment A3) - Task 2 assertion A5 duplicates shipped coverage

**Finding.** The plan's Task 2 assertion A5 proposes a data-level regression
over "a synthetic closure-valid manifest whose covering feature has a superseded
archived child", asserting `classify_shipment_close_path` still returns cascade.
That test **already exists and is already green**:

* `tests/test_shipment_closure_classification.py::test_mixed_pre_archived_and_queued_manifest_members_still_selects_cascade`
  builds a queued feature `223-F` with children `223.001-T` (archive),
  `223.002-T` (queue), `223.003-T` (archive), classifies the full four-member
  manifest, and asserts `ClosePath.CASCADE`. This is exactly the 144-S shape.
* Sibling coverage: `test_feature_queued_children_pre_archived_still_selects_cascade`,
  `test_feature_pre_archived_children_queued_still_selects_cascade`,
  `test_all_manifest_members_pre_archived_still_selects_cascade`,
  `test_pre_archived_out_of_manifest_child_falls_back_to_safe_close`.

That suite was shipped by feature 132-F / shipment 141-S out of archived stash
`EDE3CC2D` - the closure-side counterpart of this defect. Writing A5 as
specified would land a byte-equivalent duplicate of an existing assertion,
which is redundant coverage, not a regression guard, and would make the closure
invariant harder to maintain (two places to update).

**Resolution (PLAN AMENDMENT A3, applied).** A5 is replaced by a documented
cross-reference: Task 2's module docstring cites the existing tests by name as
the authoritative closure-side invariant, and Task 2 adds **no new
`classify_shipment_close_path` test**. The invariant "manifests keep their
pre-archived members" therefore remains pinned - by the tests that already pin
it. Task 2's own new assertions stay confined to the execution-contract text
(A1-A4, A6, A7), which is genuinely uncovered today.

**Effect on sizing.** Task 2 gets smaller, not larger. Size S / complexity low
still holds with margin.

## P2-1 (RESOLVED by amendment A3) - "regression coverage" wording overstated the new surface

The plan's goal statement implied the fix needs new closure-path coverage. After
P1-1 the accurate statement is: the closure path is already covered; the
**execution** path is not. Amendment A3 restates it so a future reader does not
re-add A5.

## P2-2 (RESOLVED by amendment A3) - existing agent-contract tests must be re-checked, not assumed

`tests/test_ship_safe_close_pointer.py`, `tests/test_ship_claim_integrity_guards.py`,
and `tests/test_pipeline_topology_gate_agent_wiring.py` all assert over the same
two Ship files, several with ordering-sensitive or normalized-whitespace
assertions ("Both halts fire **before** ... moves any task to `active`"). Task 1
inserts text near exactly those anchors.

**Resolution.** Task 1's acceptance criteria gain: the insertion must not
relocate, reword, or break any existing asserted anchor phrase, and the three
modules above are named explicitly as must-stay-green.

## P2-3 (ACCEPTED, execution-time verification) - installed/template structural divergence

The installed mirror (798 lines) and the template (1073 lines) have materially
different step numbering: the installed Step 2 is the task loop, while the
template's loop is Step 4 with a Step 3 ready-queue construction. The plan
already directs mirroring the contract into each file's own structure rather
than re-rendering, per the width-isolation precedent. This is correct, but it
means Ship must place the text by **semantic anchor**, not line number.
Accepted as-is; called out in Task 1's notes.

## Checks performed

| Check | Result |
|---|---|
| Goal traceable to stash `B19E9662` and deliberation `022-DL` | PASS |
| P-021 C1 classification (different contract + test surface) justified | PASS |
| Closure membership not weakened; no manifest mutation planned | PASS |
| No unarchiving / reactivation of 136.001-T, 137.005-T, 137.006-T | PASS |
| Non-goals explicit and bounded (no `src/`, schema, or CLI change) | PASS |
| Both the installed AND template contract addressed | PASS |
| Harness-manifest checksum refresh atomic with the instruction edit | PASS |
| P-006 hardening performed; H1-H7 mitigated; A1/A2 applied | PASS |
| Every task within the 2-hour rule | PASS |
| Each task independently gate-atomic (green at each boundary) | PASS |
| Width isolation (no template + CLI + schema mixing) | PASS |
| New shipment contains no pre-archived members (executable today) | PASS |
| Chain `146-S -> new -> 144-S -> 145-S` stated and justified | PASS |
| Topology-compatibility edge `144-S -> 146-S` retained alongside the critical path (corrected 2026-08-21; redundant, does not reorder the chain) | PASS |
| Mandatory post-merge instruction reload recorded | PASS |
| Duplicate coverage against the existing suite | **P1-1**, resolved |
| Unresolved P0/P1 remaining | **0** |

## Post-review verdict

**PASS.** Proceed to harvest with amendments A1, A2, A3 applied.

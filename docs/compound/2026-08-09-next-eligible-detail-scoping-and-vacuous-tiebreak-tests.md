---
title: "next_eligible_detail field scoping and vacuous tie-break regression tests"
date: 2026-08-09
source: "docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md"
citations:
  - "123-S / 115-F (PR #323 Copilot review)"
tags: [testing, contract-fidelity, tie-break, regression-tests, dag-readiness]
doc_type: learning
---

# `next_eligible_detail` field scoping and vacuous tie-break regression tests

## Context

Feature `115-F` added a `compute_next_eligible` analyzer with six branches,
each populating a `next_eligible_detail` object of exactly
`{"candidate_ids": [...], "offending_ids": [...]}`. The implementation
plan (`docs/archive/plans/2026-08-09-dag-next-eligible-resumption-advisory-plan.md:160`)
was explicit and normative about *which* branches populate *which* array,
but the first-pass implementation over-populated both arrays "for
helpfulness" on two branches where the plan required them empty. A
regression test for the tie-break logic also passed even when its own
sort-key assertion was removed, because the test's fixture data did not
distinguish the criterion under test from the tie-break's own fallback
criterion. Both defects were caught by Copilot PR review, not by the
original TDD cycle, because the original tests were written to match the
(incorrect) implementation rather than independently against the plan.

## Lesson 1 — Field population must be checked against the written contract, not "seems reasonable"

When a plan/spec states a field is populated **only** under specific named
conditions ("`candidate_ids` holds the tie-broken ordered candidate list
under `ready_set_head` (an empty array otherwise)"), an implementer's
instinct to also surface "obviously related" information on adjacent
branches (e.g. putting the single resolved cursor into `candidate_ids` for
`resume_active`, or duplicating cycle nodes into `offending_ids` for
`cycle_detected` when they are already reported via an existing sibling
field) is a **contract violation**, even though the extra data is
harmless-looking and arguably more informative to a naive caller. A
schema/contract line like `"Both keys are present on every outcome...
Consumers therefore need no key-existence checks and may index both keys
unconditionally"` is a promise about *shape*, but the *population rule* is
a separate, independently binding promise about *content*. When
implementing multi-branch code against a written outcome table, verify
each branch's field population against the table's textual rule, one
branch at a time — do not infer population rules by analogy from
neighboring branches.

## Lesson 2 — A tie-break regression test must make the primary and fallback sort keys disagree

`test_tie_break_prefers_higher_downstream_fan_out` asserted that the
higher-fan-out candidate wins the tie-break. The original fixture used
`002-S` (fan-out 1) vs. `003-S` (fan-out 0) — but `002-S` is *also*
lexicographically first, so an implementation that dropped the fan-out
sort key entirely and fell back straight to ascending-id ordering would
still produce the exact same expected output and the test would pass
**vacuously**. The fix: construct the fixture so the higher-fan-out
candidate has a **lexicographically later** id than the zero-fan-out
candidate (e.g. `005-S` fan-out 1 vs. `002-S` fan-out 0) — this makes the
primary sort key (fan-out) and the fallback sort key (ascending id)
disagree on the winner, so the assertion only passes if the code under
test actually applies the primary key.

**General rule for any composite/tie-break sort test**: when a test
asserts that criterion A takes priority over fallback criterion B, the
fixture must be constructed so that A and B would select *different*
winners if evaluated independently. If a fixture accidentally makes A and
B agree, removing the code path for A is invisible to the test — the test
provides no actual regression protection for the priority ordering it
claims to cover.

## Applicability

Any analyzer/gate exposing a machine-readable "detail"/"reason" payload
with per-branch field population rules, and any test asserting a
multi-criterion sort/tie-break, should apply these two checks during
review: (1) re-derive each branch's field population directly from the
written contract text, not from what "looks right"; (2) for tie-break
tests, confirm the fixture makes the criteria disagree, not merely produce
the same answer by coincidence.

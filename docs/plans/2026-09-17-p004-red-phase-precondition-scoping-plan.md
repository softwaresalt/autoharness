---
title: "P-004 red-phase precondition scoped to the declared shipment harness set"
description: "Implementation plan replacing P-004's unsatisfiable whole-suite every-function-red precondition with a declared-harness-set precondition admitting two disjoint expected-outcome classes (expected-red and expected-green-characterization) and asserting exact set equality against observed outcomes, delivered atomically across the policy template and its installed mirror, with a deterministic selector, a harness-manifest field, and regression tests that pin both the satisfiability of the new precondition and the continued green status of the default-branch whole-suite CI gate."
doc_type: plan
source: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 is the canonical statement of the intended design. Review findings were remediated by editing the affected requirements in place rather than appending correction notes, so this document states exactly one binding requirement per topic. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_stash_id: 76EBDE6D
stash_ids:
  - 76EBDE6D
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md
linked_review: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
covering_feature: 168-F
shipment: 176-S
requires_plan_hardening: "no"
tags:
  - "policy"
  - "tdd-gate"
  - "p-004"
  - "fail-closed-design"
---

# P-004 red-phase precondition scoped to the declared harness set

## Problem

`.github/policies/workflow-policies.md` lines 78–90 state the P-004
precondition as:

> `python -m py_compile src/autoharness/cli.py` exits 0 AND
> `PYTHONPATH=src python -m unittest discover -s tests` exits **non-zero** with
> expected failure markers in the output **for every test function**.

`.github/workflows/ci.yml` runs the identical command as the authoritative
required gate on the default branch, where it exits **zero**. The two cannot
both hold. A second, independent obstruction is scale-free: a CHARACTERIZATION
case passes by construction, so an every-function-red precondition is
unsatisfiable for any mixed harness even against an empty pre-existing suite.

Measured scope: `tests/` holds 106 files and 2025 test functions. `168-S`
(SHIP-10) and every subsequent TDD shipment cannot pass harness-ready as the
policy is written. No bypass is authorized; the gate stays fail-closed.

## Decision being implemented

Decision **D4**: adopt an explicit selector for the harness under confirmation.
The precondition is stated over the **declared harness set** for the shipment
under confirmation, never over whole-suite discover, and admits two disjoint
declared classes with exact set equality against observed outcomes.

Rejected on its own terms and not implemented: stating the precondition over
"newly authored RED-FIRST functions only", which re-introduces the
characterization obstruction because a newly authored characterization test is
both newly authored and green by construction.

## Design

### Declared harness set

The harness-architect declares, at harness authoring time, two **disjoint**
sets of fully-qualified test identifiers in the harness manifest:

| Field | Meaning |
|---|---|
| `harness.expected_red` | Test IDs that MUST fail, each with an expected failure marker |
| `harness.expected_green_characterization` | Test IDs that MUST pass, pinning pre-existing behaviour |

Both sets are non-optional. `expected_red` MUST be non-empty — a harness with
no red test confirms nothing. `expected_green_characterization` MAY be empty.
The two sets MUST be disjoint; overlap is a fail-closed authoring error.

### Selector

Confirmation runs the union of the two declared sets, addressed by explicit
test ID, not by discovery:

```text
PYTHONPATH=src python -m unittest <id-1> <id-2> ... <id-n>
```

Addressing by ID rather than by marker, tag, or naming convention is
deliberate: it makes the confirmed set exactly the declared set, so a test that
silently fails to be collected is a missing observation rather than a silently
empty pass.

### Gate predicate

The gate compares the **observed outcome map** against the **declared outcome
map** for exact set equality, in both directions:

* every ID in `expected_red` observed as failing, with its declared marker
  present in the output;
* every ID in `expected_green_characterization` observed as passing;
* no ID observed that was not declared;
* no declared ID unobserved.

Any asymmetry fails closed with a distinguishable token:

| Token | Condition |
|---|---|
| `P004_UNEXPECTED_GREEN` | A declared `expected_red` ID passed |
| `P004_UNEXPECTED_RED` | A declared `expected_green_characterization` ID failed |
| `P004_MISSING_OBSERVATION` | A declared ID produced no outcome (not collected) |
| `P004_UNDECLARED_OBSERVATION` | An outcome appeared for an undeclared ID |
| `P004_MARKER_ABSENT` | An `expected_red` ID failed without its declared marker |
| `P004_EMPTY_RED_SET` | `expected_red` is empty |
| `P004_SET_OVERLAP` | The two declared sets intersect |

The compile precondition (`python -m py_compile`) is unchanged and still exits 0.

### What is explicitly unchanged

* `.github/workflows/ci.yml` line 112 and the whole-suite default-branch gate.
  It must continue to exit **zero**. This plan adds no command to CI and
  removes none.
* P-002's harness-ready label semantics and its violation action.
* The postcondition wording `Compilation: PASS` / `Red Phase: CONFIRMED`,
  which gains the declared-set summary but keeps its existing markers.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Add `harness.expected_red` and `harness.expected_green_characterization` to the harness-manifest schema with disjointness and non-empty-red constraints | `schemas/` |
| T2 | Rewrite the P-004 precondition, postcondition, and violation action in the policy **template** | `templates/policies/workflow-policies.md.tmpl` |
| T3 | Apply the identical rewrite to the installed mirror, atomically with T2 | `.github/policies/workflow-policies.md` |
| T4 | Update the harness-architect skill to declare both sets and run the ID-addressed selector | `.github/skills/` + `templates/skills/` |
| T5 | Composed state-machine regression test: one legitimate passing state, one failing state per token | `tests/` |
| T6 | CI-invariant regression test asserting the whole-suite gate is unmodified and still green | `tests/` |

T2 and T3 are separate tasks but a single atomic change set: an installed
mirror that disagrees with its template is the exact drift class recorded in
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`.
T3 declares a `blocks` dependency on T2 so ordering is explicit.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits **0** (unchanged).
* The new test module produces one passing case per token in the table above.
* `autoharness gate check` passes on every modified file.
* Template and installed mirror are byte-identical after variable resolution
  for the P-004 section.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | A harness author declares a trivially-red test to satisfy the gate | The gate requires a declared **marker** per red test; marker text is reviewed at the operator approval gate, unchanged from today |
| R2 | ID-addressed selection silently drops a renamed test | `P004_MISSING_OBSERVATION` fires; this is the reason for exact set equality rather than a subset check |
| R3 | The rewrite weakens the fail-closed posture | Every failure path in the token table halts; no path returns a pass on ambiguity |
| R4 | Template/mirror drift between T2 and T3 | T3 blocks on T2; the byte-identity check in Verification is a gate, not an aspiration |

## Out of scope

* Any change to the default-branch CI workflow.
* Any retroactive re-confirmation of already-shipped harnesses.
* Any bypass, waiver, or `--force` path for P-004.
* `168-S`'s own manifest, which is not modified by this release unit.

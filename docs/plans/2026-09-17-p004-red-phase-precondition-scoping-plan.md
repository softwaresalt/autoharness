---
title: "P-004 red-phase precondition scoped to the declared shipment harness set"
description: "Implementation plan replacing P-004's unsatisfiable whole-suite every-function-red precondition with a declared-harness-set precondition admitting two disjoint expected-outcome classes (expected-red and expected-green-characterization) and asserting exact set equality against observed outcomes, delivered atomically across the policy template and its installed mirror, with a typed per-entry declaration shape binding each expected-red test identifier to its own failure marker, a stdlib-unittest TestResult-based observation contract that evaluates markers per test rather than over merged output, a deterministic selector, a harness-manifest field, and regression tests that pin both the satisfiability of the new precondition and the continued green status of the default-branch whole-suite CI gate."
doc_type: plan
source: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
date: 2026-09-17
status: reviewed
revision: 3
revision_note: "Revision 3 is the canonical statement of the intended design. Review findings were remediated by editing the affected requirements in place rather than appending correction notes, so this document states exactly one binding requirement per topic. Revision 3 closes the remediation-cycle-1 P1 that `expected_red` was declared as a bare identifier list while the gate predicate required a per-test marker, leaving the identifier-to-marker mapping undefined: the declaration is now a typed per-entry shape and observation is specified against `unittest.TestResult` rather than against merged runner output. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 2
source_stash_id: 76EBDE6D
stash_ids:
  - 76EBDE6D
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md
linked_review: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
review_history:
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-03.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact."
latest_review_attempt: 3
latest_review_artifact: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-03.md
latest_review_verdict: PASS
covering_feature: 168-F
shipment: 176-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
plan_hardening_section: "## Plan Hardening Record (P-006)"
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
sets of fully-qualified test identifiers in the harness manifest. Both fields
are **lists of typed entries**, never bare identifier lists — the bare-list
shape is what left the identifier-to-marker mapping undefined and is rejected
by the schema.

| Field | Entry shape | Meaning |
|---|---|---|
| `harness.expected_red` | `{ test_id: str, marker: str }` | Test IDs that MUST fail, each carrying **its own** expected failure marker |
| `harness.expected_green_characterization` | `{ test_id: str }` | Test IDs that MUST pass, pinning pre-existing behaviour |

```yaml
harness:
  expected_red:
    - test_id: tests.test_gates_topology.TestResolveExpectedBranches.test_explicit_contract_wins
      marker: "AttributeError: module 'autoharness.gates.topology' has no attribute 'resolve_expected_branches'"
    - test_id: tests.test_gates_topology.TestResolveExpectedBranches.test_malformed_never_falls_back
      marker: "IMPLEMENTATION_BRANCH_MALFORMED"
  expected_green_characterization:
    - test_id: tests.test_gates_topology.TestBranchAliases.test_title_alias_unchanged
```

Binding constraints on the declaration, all fail-closed authoring errors:

* `test_id` is a fully-qualified `unittest` name resolvable by
  `unittest.defaultTestLoader.loadTestsFromNames()`. It is the **exact string**
  returned by `TestCase.id()` for that test, so declared and observed
  identifiers are comparable without normalization.
* `marker` is a **non-empty** literal substring, matched case-sensitively. It
  is required on every `expected_red` entry and is **prohibited** on
  `expected_green_characterization` entries (a passing test produces no
  failure text to match).
* `test_id` values are unique **within and across** both lists. A duplicate
  `test_id` inside one list is `P004_DUPLICATE_DECLARATION`; the same
  `test_id` in both lists is `P004_SET_OVERLAP`.
* `expected_red` MUST be non-empty — a harness with no red test confirms
  nothing. `expected_green_characterization` MAY be empty.

The **declared outcome map** is therefore total and deterministic:
`test_id -> (expected_outcome, marker_or_None)`. There is no positional,
order-derived, or convention-derived association anywhere in the contract.

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

### Observation contract (stdlib `unittest`, `TestResult`-based)

The command line above is the **human-readable** statement of the selector.
The gate itself does **not** parse that command's merged stdout/stderr. Merged
output cannot attribute a marker to a specific test when more than one test
fails, which is the exact ambiguity that made the bare-identifier declaration
unusable. Observation is instead defined against the stdlib result object:

1. **Load.** `unittest.defaultTestLoader.loadTestsFromNames(declared_ids)`
   against a loader rooted so that `PYTHONPATH=src` and the repository root
   resolve identically to the CI invocation. `loadTestsFromNames` does not
   raise on an unresolvable name; it substitutes a `unittest.loader._FailedTest`
   placeholder whose `id()` is the requested name and which errors at run time.
   The runner therefore records, **before running**, the set of names that
   produced a placeholder and classifies each as
   `P004_MISSING_OBSERVATION` — never as a genuine red observation. This
   distinction is load-time, not traceback-text-derived.
2. **Run.** `unittest.TextTestRunner(resultclass=P004Result, verbosity=0)` over
   the loaded suite. `P004Result` subclasses `unittest.TextTestResult` and
   overrides `addSuccess`, `addFailure`, `addError`, `addSkip`,
   `addExpectedFailure`, and `addUnexpectedSuccess` to record, per test, the
   tuple `(test.id(), outcome, detail_text)`.
   * `detail_text` for a failure or error is the **per-test** formatted
     traceback string that `unittest` hands to `addFailure` / `addError` — the
     same string that lands in `result.failures` / `result.errors` — and
     nothing else. It is never the concatenated run output.
   * `addSkip`, `addExpectedFailure`, and `addUnexpectedSuccess` are recorded
     as their own outcomes and are **not** silently folded into pass or fail.
     A skipped declared test is `P004_MISSING_OBSERVATION`: it produced no
     evidence either way.
3. **Compare.** Build the observed outcome map `test_id -> (outcome,
   detail_text)` and compare it against the declared outcome map for exact set
   equality, per the gate predicate below. Marker matching is performed on
   **that test's own `detail_text`**, so `P004_MARKER_ABSENT` names exactly one
   test.
4. **Isolation.** The confirmation run is a separate process invocation from
   the default-branch whole-suite gate and shares no state with it. It imports
   no test module outside the declared set beyond what those modules import
   themselves.

`P004Result` and the runner entry point live in `src/autoharness/` and are
importable, so the regression suite exercises the same code path the gate
executes rather than a re-implementation of it.

### Gate predicate

The gate compares the **observed outcome map** against the **declared outcome
map** for exact set equality, in both directions:

* every ID in `expected_red` observed with outcome `failure` or `error`, and
  its **own** declared marker present as a substring of **its own**
  `detail_text`;
* every ID in `expected_green_characterization` observed with outcome
  `success`;
* no ID observed that was not declared;
* no declared ID unobserved, where "unobserved" includes load-placeholder and
  skip outcomes.

Any asymmetry fails closed with a distinguishable token:

| Token | Condition |
|---|---|
| `P004_UNEXPECTED_GREEN` | A declared `expected_red` ID was observed `success` |
| `P004_UNEXPECTED_RED` | A declared `expected_green_characterization` ID was observed `failure` or `error` |
| `P004_MISSING_OBSERVATION` | A declared ID produced a load placeholder, a skip, or no result entry at all |
| `P004_UNDECLARED_OBSERVATION` | A result entry appeared for an ID not in either declared list |
| `P004_MARKER_ABSENT` | An `expected_red` ID failed, but its declared marker is not a substring of that test's own `detail_text` |
| `P004_EMPTY_RED_SET` | `expected_red` is empty |
| `P004_SET_OVERLAP` | A `test_id` appears in both declared lists |
| `P004_DUPLICATE_DECLARATION` | A `test_id` appears twice within one declared list |
| `P004_MARKER_MISPLACED` | An `expected_red` entry omits `marker`, or an `expected_green_characterization` entry supplies one |

Every token names the offending `test_id`(s). A token that cannot name a
specific identifier is a defect in the runner, not an acceptable outcome.

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
| T1 | Add `harness.expected_red` and `harness.expected_green_characterization` to the harness-manifest schema as **typed entry lists** (`{test_id, marker}` / `{test_id}`) with the marker-placement, uniqueness, disjointness, and non-empty-red constraints | `schemas/` |
| T2 | Rewrite the P-004 precondition, postcondition, and violation action in the policy **template** | `templates/policies/workflow-policies.md.tmpl` |
| T3 | Apply the identical rewrite to the installed mirror, atomically with T2 | `.github/policies/workflow-policies.md` |
| T4 | Update the harness-architect skill to declare typed entries and run the ID-addressed selector | `.github/skills/` + `templates/skills/` |
| T5 | Composed state-machine regression test: one legitimate passing state, one failing state per token | `tests/` |
| T6 | CI-invariant regression test asserting the whole-suite gate is unmodified and still green | `tests/` |
| T7 | Implement the `P004Result` / runner entry point: `loadTestsFromNames` placeholder detection, per-test outcome and per-test `detail_text` capture, and the observed-map builder | `src/autoharness/` |

T2 and T3 are separate tasks but a single atomic change set: an installed
mirror that disagrees with its template is the exact drift class recorded in
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`.
T3 declares a `blocks` dependency on T2 so ordering is explicit.

T7 is the executable observation boundary the schema (T1) and the policy text
(T2/T3) both describe. T5 declares a `blocks` dependency on T7 and on T1: the
token matrix is exercised against the real runner, never against a test-local
re-implementation of it.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits **0** (unchanged).
* The new test module produces one passing case per token in the table above.
* A two-red-test fixture where each test fails with the *other* test's declared
  marker emits `P004_MARKER_ABSENT` naming **both** IDs — the case that merged
  output would have silently passed.
* A declared ID that does not resolve emits `P004_MISSING_OBSERVATION` and is
  distinguishable in the runner output from a test that genuinely errored.
* A declared ID that is `@unittest.skip`-ped emits `P004_MISSING_OBSERVATION`,
  not a pass and not a red.
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
| R5 | A marker declared for one test is satisfied by a different test's failure text | Markers are matched against the per-test `detail_text` from `TestResult`, never against merged output; Verification carries the crossed-marker case explicitly |
| R6 | An unresolvable declared ID is read as a legitimate red | `loadTestsFromNames` placeholders are detected at load time, before the run, and classified `P004_MISSING_OBSERVATION` |
| R7 | The runner drifts from the regression suite's model of it | T7 ships the runner as importable code in `src/autoharness/`; T5 blocks on T7 and imports it rather than re-implementing the comparison |

## Out of scope

* Any change to the default-branch CI workflow.
* Any retroactive re-confirmation of already-shipped harnesses.
* Any bypass, waiver, or `--force` path for P-004.
* `168-S`'s own manifest, which is not modified by this release unit.

## Plan Hardening Record (P-006)

Hardening applied 2026-09-18 during remediation cycle 1. Revision 2 declared
`requires_plan_hardening: "no"`; that declaration was wrong and is corrected
here (H0). The plan changes a `schemas/` contract, rewrites a policy template
**and** its installed mirror, changes a skill in both template and installed
copies, and adds executable gate code — elevated blast radius on the exact axes
P-006 enumerates, and the same axes on which its four sibling plans correctly
declared `yes`.

**Hardening trigger.** Schema contract change; policy-registry change shipped
to every consumer workspace; two template/installed-mirror pairs; and a
rewrite of the **red-phase precondition of a fail-closed TDD gate** that every
downstream shipment must pass. A defect here either blocks all TDD work or —
far worse — silently admits an unconfirmed harness.

**Protected invariants.**

* `.github/workflows/ci.yml` line 112 and the whole-suite default-branch gate
  must continue to exit **zero**. No command is added to CI and none removed.
* The gate stays fail-closed on every path. No token returns a pass on
  ambiguity; no bypass, waiver, or `--force` path is introduced.
* P-002's harness-ready label semantics and violation action are untouched.
* Template and installed mirror never diverge.
* `168-S`'s own manifest is not modified by this release unit.

**Instructions and learnings consulted.**
`.github/policies/workflow-policies.md` (P-004 lines 78–90, P-002),
`.github/workflows/ci.yml`,
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`,
`docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md`,
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`,
and the Python `unittest` loader/result API contract.

| # | Hardening finding | Resolution |
|---|---|---|
| H0 | Revision 2 declared `requires_plan_hardening: "no"` despite a `schemas/` change, a consumer-installed policy rewrite, two mirror pairs, and new gate code | Corrected to `yes`; this section is the record |
| H1 | `expected_red` was a bare identifier list while the gate predicate required a per-test marker, leaving the ID→marker mapping undefined — the gate as specified was unimplementable | Typed per-entry shape `{test_id, marker}`; declared outcome map is total and deterministic |
| H2 | "Expected failure markers in the output" would have been matched against merged runner output, so with two failing tests each test's marker could be satisfied by the *other* test's traceback — a false CONFIRMED on an unconfirmed harness | Observation defined against `unittest.TestResult`; markers matched per test against that test's own `detail_text`; Verification carries the crossed-marker case |
| H3 | An unresolvable declared ID would surface as a `_FailedTest` error and be indistinguishable from a genuine red — a renamed or deleted test would have *satisfied* the red requirement | Load-time placeholder detection classifies it `P004_MISSING_OBSERVATION` before the run |
| H4 | Skips, expected-failures, and unexpected-successes were unmodelled and would have folded into pass or fail | Recorded as their own outcomes; a skipped declared test is `P004_MISSING_OBSERVATION`, never a red |
| H5 | No marker-placement rule, so a `expected_green_characterization` entry could carry a meaningless marker and a red entry could omit one | `P004_MARKER_MISPLACED` added; marker required on red, prohibited on green |
| H6 | Duplicate `test_id` within one list was unhandled | `P004_DUPLICATE_DECLARATION` added; uniqueness asserted within and across both lists |
| H7 | The regression suite could have re-implemented the comparison, so a runner defect would pass its own tests | T7 ships the runner as importable code in `src/autoharness/`; T5 blocks on T7 and imports it |
| H8 | Tokens that could not name an offending identifier would be undiagnosable in practice | Every token names its `test_id`(s); a token that cannot is declared a runner defect, not an acceptable outcome |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Rewrite the P-004 precondition in `templates/policies/workflow-policies.md.tmpl` (T2) | **High** — changes a fail-closed gate every consumer workspace installs | Operator review of the rewritten precondition text | Revert the P-004 section; change is confined to one clause |
| Apply the identical rewrite to `.github/policies/workflow-policies.md` (T3) | High — must land atomically with T2 | Same review | Revert together; T3 blocks on T2; byte-identity check is a gate |
| Add typed fields to the harness-manifest schema (T1) | Medium — existing manifests declaring the old bare-list shape become invalid | Standard PR review | Revert schema; no manifest in this repository declares either field yet |
| Add the `P004Result` runner to `src/autoharness/` (T7) | Medium — new executable gate path | Standard PR review | Revert; the runner is additive and nothing calls it until T2/T3 land |
| Change the harness-architect skill in both copies (T4) | Medium — mirrored pair | Standard PR review | Revert both copies together |

**Rollback coupling.** T2+T3 revert together (policy mirror pair). T4's two
copies revert together. T1 and T7 are additive and revert independently. T5/T6
are test-only. No persisted state is mutated anywhere in the unit.

**Monitoring and validation window.** The first shipment to declare a harness
set under the new schema is the live signal: its confirmation run must emit a
per-token summary naming concrete test IDs. The default-branch whole-suite gate
must remain green throughout — T6 is the standing assertion of that, and it
runs on every CI invocation.

**Operator checkpoints.** One: review of the rewritten P-004 precondition text
(T2/T3) before merge, since it changes a policy every consumer installs.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers, and MUST apply both the Constitution
Reviewer persona (policy-registry change) and the Python Reviewer persona
(`unittest` loader/result semantics) inline.

**Unresolved operator decisions blocking safe execution.** None.

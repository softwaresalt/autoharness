---
title: "P-004 red-phase precondition scoped to the declared shipment harness set"
description: "Implementation plan replacing P-004's unsatisfiable whole-suite every-function-red precondition with a declared-harness-set precondition admitting two disjoint expected-outcome classes (expected-red and expected-green-characterization) and asserting exact set equality against observed outcomes, delivered atomically across the policy template and its installed mirror, with a typed per-entry declaration shape binding each expected-red test identifier to its own failure marker, a stdlib-unittest TestResult-based observation contract that evaluates markers per test rather than over merged output, a deterministic selector, a harness-manifest field, and regression tests that pin both the satisfiability of the new precondition and the continued green status of the default-branch whole-suite CI gate."
doc_type: plan
source: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
date: 2026-09-17
status: reviewed
revision: 5
revision_note: "Revision 5 (remediation cycle 3) answers review attempt 05, which returned BLOCKED at revision 4 on four findings against this plan. (1) LOADER CONTRACT WAS WRONG. Revision 4 asserted that `loadTestsFromNames(names)` yields one top-level TEST per input name and that `TestLoader.errors` can be keyed by the requested name. Both are false: `loadTestsFromName` returns `suiteClass((_FailedTest(...),))` on failure, so `loadTestsFromNames` yields one top-level SUITE per name, and `TestLoader.errors` is a flat LIST of formatted message strings appended in load order with no name key. Revision 5 replaces positional correlation entirely with a stdlib-only algorithm that loads each declared name INDEPENDENTLY via `loadTestsFromName`, recursively FLATTENS the returned suite, attributes load errors by a per-name `len(loader.errors)` SNAPSHOT, and correlates observed results back to requested names by test-OBJECT IDENTITY rather than by any `id()` string. (2) SCHEMA OVER-ASSIGNMENT. Revision 4 assigned `test_id` uniqueness and red/green disjointness to a Draft-07 schema, which cannot express property-key uniqueness within an array of objects nor any cross-property value comparison. Revision 5 splits the validation boundary: the schema owns PER-ITEM SHAPE ONLY, and `P004_DUPLICATE_DECLARATION` / `P004_SET_OVERLAP` move to an executable Python declaration validator. The keyed-map alternative was considered and rejected. (3) BOOTSTRAP IMPOSSIBILITY. 176-S could not be executed at all: every task needs `harness-ready` under P-002, `harness-ready` needs a P-004 red-phase confirmation, and the P-004 precondition this plan exists to repair is unsatisfiable — so the shipment that fixes P-004 was itself gated behind broken P-004. Revision 5 adds bootstrap task T0 as the entry point of 176-S with an explicit, bounded, fail-closed self-ratification contract and no force grant. (4) Risk R7 and hardening finding H7 named `T5`, which is not a task in this plan; corrected to `T5b`. Revision 5 is STAGE-REMEDIATED AND PENDING INDEPENDENT REVIEW ATTEMPT 06; Stage does not review its own remediation and asserts no PASS. The bounded audit trail lives in `linked_review`. Revision 4 (remediation cycle 2) adopted decision revision 3 and closed the propagation findings from local review cycle 2. The revision-3 design was never encoded into the executable backlog records: the nine-token contract was harvested as seven tokens, the typed `{test_id, marker}` entry shape was absent from the task bodies, no `P004Result` boundary was named, and the red/implementation/green ordering existed only as prose. Revision 4 restates the token set as exactly NINE, names `P004Result` as the real per-test observation boundary, and requires the TDD triple to be encoded as dependency edges — red contract tests authored and observed failing BEFORE the boundary exists, implementation blocked on the red task, green verification blocked on the implementation, and the red task explicitly NOT depending on the implementation. Revision 4 also corrects two stdlib facts that revision 3 stated inaccurately: `TestResult.addFailure`/`addError` receive an `exc_info` TUPLE (not a formatted string) and traceback formatting is INHERITED via `TestResult._exc_info_to_string`; and `unittest.loader._FailedTest.id()` is NOT guaranteed to equal the requested name. Revision 4's own replacement for that — positional correspondence of `loadTestsFromNames(names)` corroborated by `isinstance` and a name-keyed lookup into `loader.errors` — is ITSELF WITHDRAWN AND SUPERSEDED by revision 5 finding (1) above; it is retained in this note only as history and is not an instruction."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
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
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-05.md
review_history_note: "Attempts 01-02 were authored as one mutable file covering two cycles; it is preserved verbatim and classified rather than retroactively split into records that were never independently authored. Attempt 03 is a conforming single-attempt immutable artifact. Attempt 04 records local review cycle 2 (BLOCKED at revision 3, on non-propagation of the design into the executable backlog records) and the Stage remediation response. Attempt 05 records the final independent review cycle (BLOCKED at revision 4, on the unittest loader contract, the Draft-07 schema over-assignment, the 176-S bootstrap impossibility, and the R7/H7 label defect) and the Stage remediation cycle 3 response that produced revision 5."
latest_review_attempt: 5
latest_review_artifact: docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-05.md
latest_review_verdict: REMEDIATED-PENDING-REVIEW
latest_review_verdict_note: "Attempt 05 returned BLOCKED at plan revision 4. Stage remediation cycle 3 closed every attempt-05 finding and raised this plan to revision 5. Stage does not review its own remediation, so NO PASS is asserted at revision 5; the next independent reviewer pass is attempt 06."
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
  `unittest.defaultTestLoader.loadTestsFromName()`. It is the **exact string**
  returned by `TestCase.id()` for that test, so declared and observed
  identifiers are comparable without normalization. It MUST address **exactly
  one** test function — never a module, class, or package.
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

### Where each constraint is enforced (revision 5)

Revision 4 assigned **every** constraint above to the harness-manifest JSON
Schema. That was a correctness defect, not a distribution preference: this
repository's schemas are **JSON Schema Draft-07** (`$schema:
http://json-schema.org/draft-07/schema#` in all nine files under `schemas/`),
and Draft-07 cannot express two of the constraints at all.

* **Uniqueness of a property *value* across array items is inexpressible.**
  Draft-07's only uniqueness vocabulary is `uniqueItems`, which compares
  **whole item instances**. Two entries
  `{test_id: X, marker: "a"}` and `{test_id: X, marker: "b"}` are distinct
  instances, so `uniqueItems` accepts them — while the contract must reject
  them as `P004_DUPLICATE_DECLARATION`. Conversely `uniqueItems` rejects two
  byte-identical entries, which is a *different* rule from the one required.
* **Cross-property value comparison is inexpressible.** Nothing in Draft-07
  can compare the `test_id` values in `expected_red` against those in
  `expected_green_characterization`, so `P004_SET_OVERLAP` has no schema
  formulation whatsoever.

**The keyed-map alternative was considered and rejected.** Re-shaping both
fields as YAML mappings keyed by `test_id` would obtain within-list uniqueness
from the object-key rule — but it still cannot express cross-list disjointness,
and it makes a duplicate declaration **silently last-wins** in every mainstream
YAML loader rather than a fail-closed authoring error. Trading a loud error for
a silent overwrite is the opposite of the fail-closed posture this plan exists
to restore. The typed-entry-list shape stands.

The boundary is therefore split, and each token has **exactly one** owner:

| Layer | Owns | Tokens it may raise | Task |
|---|---|---|---|
| **Schema** (`schemas/harness-manifest.schema.json`, Draft-07) | **Per-item shape only**: both fields are arrays of objects; `expected_red` items `required: [test_id, marker]`; `expected_green_characterization` items `required: [test_id]` with `additionalProperties: false` so a `marker` key is rejected; `test_id` and `marker` are `{type: string, minLength: 1}`; `expected_red` carries `minItems: 1` | `P004_MARKER_MISPLACED`, `P004_EMPTY_RED_SET` | T1 |
| **Python declaration validator** (`src/autoharness/`, `validate_declared_harness_set()`) | **Whole-declaration relational constraints**: within-list `test_id` uniqueness and cross-list disjointness, evaluated over the parsed manifest | `P004_DUPLICATE_DECLARATION`, `P004_SET_OVERLAP` | T7 |

`validate_declared_harness_set()` runs **before** the load step and fails
closed; the runner never proceeds to load a declaration that did not pass it.
No token is raised by both layers, and neither layer restates the other's rule.
A schema that attempts `uniqueItems` for `P004_DUPLICATE_DECLARATION`, or any
re-statement of a relational rule in the schema, is a review-visible defect.

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

1. **Load — each declared name independently.** Revision 4 specified
   `loadTestsFromNames(declared_ids)` with **positional** correlation and a
   name-keyed lookup into `loader.errors`. Both halves were factually wrong and
   are withdrawn:

   * `TestLoader.loadTestsFromName(name)` returns a **`TestSuite`**, not a
     `TestCase`. On an unresolvable name it returns
     `self.suiteClass((_FailedTest(<derived-method-name>, exc),))` — a suite
     wrapping the placeholder. `loadTestsFromNames(names)` is defined as
     `self.suiteClass([self.loadTestsFromName(n) for n in names])`, so its
     top-level members are one **suite** per input name, never one **test** per
     input name. A resolvable name may also expand to many tests (a module or
     class name), so "one top-level test per input name" does not hold in the
     success case either.
   * `TestLoader.errors` is a flat **`list` of formatted message strings**
     appended in load order. It is **not** a mapping and has no name key, so
     `name in loader.errors` is meaningless and cannot corroborate anything.

   The runner therefore performs the load itself, **one declared name at a
   time**, and attributes both tests and errors by per-name loader state:

   ```python
   import unittest
   from unittest.loader import _FailedTest

   def _flatten(suite):
       """Recursively yield TestCase leaves; TestSuite is iterable of tests/suites."""
       for item in suite:
           if isinstance(item, unittest.TestSuite):
               yield from _flatten(item)
           else:
               yield item

   def load_declared(declared_ids):
       loader = unittest.TestLoader()      # fresh loader: errors starts empty
       requested_of = {}                   # id(test object) -> requested name
       loaded = {}                         # requested name -> [TestCase, ...]
       unloadable = {}                     # requested name -> [error strings]
       for name in declared_ids:
           before = len(loader.errors)              # snapshot BEFORE this name
           suite = loader.loadTestsFromName(name)   # load this name ALONE
           new_errors = loader.errors[before:]      # slice => this name's errors only
           tests = list(_flatten(suite))            # flatten; never assume depth 1
           loaded[name] = tests
           for t in tests:
               requested_of[id(t)] = name           # OBJECT IDENTITY, not id() string
           if new_errors or len(tests) != 1 or isinstance(tests[0], _FailedTest):
               unloadable[name] = new_errors
       return loader, loaded, requested_of, unloadable
   ```

   Three properties make this correct where revision 4 was not:

   * **Independent loading** removes the need for positional correspondence
     entirely. Each `loadTestsFromName` call concerns exactly one requested
     name, so nothing has to be matched up afterwards.
   * **Error attribution is by list-length snapshot**, `loader.errors[before:]`,
     which is the only sound way to read an append-only list of unkeyed
     strings. No string is parsed and no name is looked up.
   * **Result correlation is by test-object identity.** The map
     `id(test_object) -> requested_name` is built at load time from the very
     objects that are about to be run, so an observed result is attributed to
     its requested name without ever comparing `TestCase.id()` to the declared
     string. This is what makes `_FailedTest.id()` differing from the requested
     name a non-issue rather than a hazard.

   **Classification at load time, before anything runs.** A declared name is
   `P004_MISSING_OBSERVATION` when it produced any load error, or resolved to a
   `_FailedTest`, or resolved to **zero** tests. A declared name that resolves
   to **more than one** test is a declaration defect: the declared `test_id`
   itself is reported `P004_MISSING_OBSERVATION` (it addressed no single test),
   and every surplus resolved test id that is not itself declared is reported
   `P004_UNDECLARED_OBSERVATION`. Both are existing tokens; the token set
   remains exactly **NINE**. None of these classifications is ever a genuine
   red observation, and none is derived from traceback text or from an `id()`
   string comparison.

   The loader is rooted so that `PYTHONPATH=src` and the repository root
   resolve identically to the CI invocation.
2. **Run.** `unittest.TextTestRunner(resultclass=P004Result, verbosity=0)` over
   a suite rebuilt from the flattened, load-classified tests. `P004Result`
   subclasses `unittest.TextTestResult` and overrides `addSuccess`,
   `addFailure`, `addError`, `addSkip`, `addExpectedFailure`, and
   `addUnexpectedSuccess` to record, per test, the tuple
   `(requested_of[id(test)], test.id(), outcome, detail_text)`. The **first**
   element — the requested name recovered from the load-time identity map — is
   the key everything downstream is compared on; `test.id()` is recorded as
   corroborating evidence and is never used to look a test up.
   * **`addFailure(test, err)` and `addError(test, err)` receive an `exc_info`
     TUPLE** `(type, value, traceback)` — **not** a formatted string. Revision 3
     stated this inaccurately. The formatted per-test traceback string is
     produced by the **inherited** `TestResult._exc_info_to_string(err, test)`,
     which the overrides call (or which the base implementation calls when the
     override delegates via `super()`); it is the same string that lands in
     `result.failures` / `result.errors`. `detail_text` is exactly that
     per-test string and nothing else. It is never the concatenated run output,
     and the overrides must not attempt to treat `err` as text.
   * `addSkip`, `addExpectedFailure`, and `addUnexpectedSuccess` are recorded
     as their own outcomes and are **not** silently folded into pass or fail.
     A skipped declared test is `P004_MISSING_OBSERVATION`: it produced no
     evidence either way.
3. **Compare.** Build the observed outcome map **keyed by requested name**,
   `test_id -> (outcome, detail_text)`, merging in the load-time
   classifications from step 1, and compare it against the declared outcome map
   for exact set equality, per the gate predicate below. Because both maps are
   keyed by the *declared* string, the comparison needs no normalization and no
   `id()`-string matching. Marker matching is performed on **that test's own
   `detail_text`**, so `P004_MARKER_ABSENT` names exactly one test.
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
| `P004_MISSING_OBSERVATION` | A declared ID produced a load error or a `_FailedTest` placeholder, resolved to zero tests, resolved to more than one test (so it addressed no single test), was skipped, or produced no result entry at all |
| `P004_UNDECLARED_OBSERVATION` | A result entry appeared for an ID not in either declared list — including a surplus test pulled in because a declared name resolved to a module or class rather than a single test function |
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

## Bootstrap: how `176-S` becomes executable at all (revision 5)

Review attempt 05 asked for a **verified, executable, policy-compliant path**
from claiming `176-S` through harness-ready / red-phase to the first task claim.
The verification was performed against the installed policy text and the answer
is that **no such path exists today**:

1. P-002 (`Gate Point: Queue building (Step 2) and task claiming (Step 3)`)
   states the ship agent "may only claim and implement a task after the
   harness-architect has confirmed that the test harness compiles and all tests
   fail in the red phase", with precondition "the task carries the
   `harness-ready` label" and enforcement "filter ready queue to only tasks
   carrying the `harness-ready` label". There is **no** unlabelled-task path.
2. `harness-ready` is applied only after P-004's red-phase confirmation.
3. P-004's installed precondition requires
   `PYTHONPATH=src python -m unittest discover -s tests` to exit **non-zero**
   with expected failure markers "for every test function". As the Problem
   section establishes, that is unsatisfiable for any mixed harness at any
   scale, and it is exactly what `176-S` exists to repair.

So the shipment that repairs P-004 was itself gated behind unrepaired P-004.
That is a genuine bootstrap deadlock, not a scheduling inconvenience, and it
blocks the entire portfolio because `177-S`–`181-S` and the pre-existing
`168-S` all descend from `176-S`.

**Resolution: a declared bootstrap unit, not a force grant.** `T0` is added as
the entry point of `176-S`. No `--force`, no waiver, no `harness-ready` applied
without confirmation, and no relaxation of any exit-code requirement is
introduced anywhere. What `T0` does is apply **the exact contract this plan is
authorized to establish** — decision D4's declared-harness-set precondition
with two disjoint expected-outcome classes under exact set equality — to
`176-S`'s own harness, one step before the same contract is installed as policy
text by `T2`/`T3`.

**Bootstrap acceptance contract (binding, and narrower than the general gate):**

* `T0` declares `176-S`'s own `harness.expected_red` and
  `harness.expected_green_characterization` entries in the typed shape, in the
  shipment harness manifest.
* Red-phase confirmation for `176-S` is evaluated over **that declared set**,
  by explicit test ID, never over whole-suite `discover`.
* The confirmation remains **fail-closed and complete**: `python -m py_compile
  src/autoharness/cli.py` MUST exit 0; every declared `expected_red` ID MUST be
  observed failing **with its own declared marker**; every declared
  characterization ID MUST be observed passing; exact set equality MUST hold in
  both directions. Any asymmetry halts and no label is applied.
* The default-branch whole-suite gate is **not touched** and MUST stay green
  throughout (`T6` is the standing assertion).
* **Scope of the bootstrap authority is exactly one shipment.** It names
  `176-S` explicitly, it is ratified by the policy text that `T2`/`T3` install
  in this same release unit, and it **expires when `T3` lands**. `177-S`
  through `181-S`, `168-S`, and every later shipment run the gate under the
  installed policy text, never under this clause. A second shipment citing this
  clause is a policy violation, not a precedent.
* `T0` requires the **P-004 operator approval gate**, which is the existing,
  already-authorized authority for red-phase confirmation
  (`Gate Point: Operator Approval Gate`). No new authority is invented.

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T0 | **BOOTSTRAP** — declare `176-S`'s own typed harness set and perform the declared-set red-phase confirmation under the bounded, expiring, fail-closed acceptance contract above, so `176-S`'s tasks can legitimately receive `harness-ready` | harness manifest + harness-architect confirmation record | — |
| T1 | Add `harness.expected_red` and `harness.expected_green_characterization` to the harness-manifest schema as **typed entry lists** (`{test_id, marker}` / `{test_id}`) — **per-item shape only**: requiredness, `additionalProperties: false` on characterization entries, `minLength: 1` strings, `minItems: 1` on `expected_red`. **No uniqueness and no disjointness rule is expressed in the schema**; those move to T7 | `schemas/` | T0 |
| T2 | Rewrite the P-004 precondition, postcondition, and violation action in the policy **template**, enumerating all **nine** tokens | `templates/policies/workflow-policies.md.tmpl` | T1 |
| T3 | Apply the byte-identical rewrite to the installed mirror, atomically with T2 | `.github/policies/workflow-policies.md` | T2 |
| T4 | Update the harness-architect skill to declare typed entries and run the ID-addressed selector | `.github/skills/` + `templates/skills/` | T1, T2 |
| T5a | **RED** — author the composed state-machine contract tests (one legitimate passing state, one failing state per token, all nine) against the not-yet-existing `P004Result` entry point, and **observe them failing** | `tests/` | T1 |
| T6 | CI-invariant regression test asserting the whole-suite gate is unmodified and still green | `tests/` | T3 |
| T7 | **IMPLEMENTATION** — `validate_declared_harness_set()` (within-list uniqueness, cross-list disjointness) plus the `P004Result` / runner entry point: independent per-name `loadTestsFromName` loading, recursive suite flattening, `len(loader.errors)` snapshot attribution, test-object-identity correlation to requested names, `exc_info`-tuple handling with inherited `_exc_info_to_string` formatting, per-test outcome and per-test `detail_text` capture, and the observed-map builder | `src/autoharness/` | T5a |
| T5b | **GREEN** — observe the full nine-token contract suite passing against the shipped `P004Result` and `validate_declared_harness_set()`, and add the regression cases that only make sense against a real implementation | `tests/` | T7 |

T2 and T3 are separate tasks but a single atomic change set: an installed
mirror that disagrees with its template is the exact drift class recorded in
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`.
T3 declares a `blocks` dependency on T2 so ordering is explicit.

### TDD ordering (revision 4 — machine-encoded)

Revision 3 inverted the TDD relationship: it made the token-matrix test (T5)
block on the implementation (T7), which is a test-**after** ordering wearing a
red-phase label. Revision 4 splits the test surface and encodes the triple as
`blocks` edges in the backlog, not as prose:

* **T5a (RED) blocks on T1 only.** It is authored against the schema's typed
  entry shape and the *declared* nine-token contract, and is observed failing
  because `P004Result` does not yet exist. **T5a does NOT depend on T7.** That
  asymmetry is the whole content of the red phase; reversing it reproduces the
  revision-3 defect.
* **T7 (IMPLEMENTATION) blocks on T5a.** The executable observation boundary the
  schema (T1) and the policy text (T2/T3) both describe is written to turn an
  already-failing, already-reviewed contract green.
* **T5b (GREEN) blocks on T7.** The token matrix is then observed passing
  against the real runner, never against a test-local re-implementation of it.
* **T0 (BOOTSTRAP) blocks nothing and is blocked by nothing except the operator
  approval gate; T1 blocks on T0.** T0 is the single entry point of `176-S`.
  It must precede T1 because no task in the shipment — T1 included — can be
  claimed under P-002 until the declared-set red-phase confirmation has been
  performed. T0 is deliberately NOT a successor of the policy rewrite it
  anticipates: it is the one-shipment bootstrap, and T2/T3 are what retire it.

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
* A declared ID naming a **module or class** rather than a single test function
  emits `P004_MISSING_OBSERVATION` for the declared ID and
  `P004_UNDECLARED_OBSERVATION` for each surplus test.
* A fixture in which `_FailedTest.id()` differs from the requested name is still
  attributed to the requested name, proving correlation is by object identity
  and not by string comparison.
* A two-name load in which only the **second** name fails attributes the load
  error to the second name alone, proving `len(loader.errors)` snapshot
  attribution rather than a whole-list read.
* A declaration with a duplicated `test_id` emits `P004_DUPLICATE_DECLARATION`
  from `validate_declared_harness_set()`, and a declaration with the same
  `test_id` in both lists emits `P004_SET_OVERLAP` — both from the Python
  boundary, and neither from the schema.
* The schema rejects a characterization entry carrying a `marker`
  (`additionalProperties: false`) and an empty `expected_red` (`minItems: 1`),
  and **accepts** a duplicate `test_id`, which is the positive proof that the
  relational rules are not being silently expected of it.
* `176-S`'s T0 declared-set confirmation exits fail-closed on every asymmetry,
  applies no label without a complete confirmation, and leaves the
  default-branch whole-suite gate green.
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
| R6 | An unresolvable declared ID is read as a legitimate red | Each name is loaded independently by `loadTestsFromName`, its errors attributed by a `len(loader.errors)` snapshot, and the result flattened and inspected at load time — before the run — and classified `P004_MISSING_OBSERVATION` |
| R7 | The runner drifts from the regression suite's model of it | T7 ships the runner as importable code in `src/autoharness/`; **T5b** blocks on T7 and imports it rather than re-implementing the comparison |
| R8 | A Draft-07 schema is written that silently fails to enforce uniqueness or disjointness, so two declarations collide unnoticed | Those two rules are removed from the schema entirely and owned solely by `validate_declared_harness_set()` in T7; the split is stated normatively with one owner per token, and a `uniqueItems` attempt in the schema is a review-visible defect |
| R9 | The T0 bootstrap is read as a general escape hatch and cited by a later shipment | The acceptance contract names `176-S` explicitly, expires on T3, introduces no `--force`/waiver/exit-code relaxation, and states that a second citation is a policy violation rather than a precedent; T0 runs through the existing P-004 operator approval gate |
| R10 | A declared `test_id` addresses a module or class, silently widening the confirmed set | A declared name resolving to anything other than exactly one test is classified at load time: the declared ID is `P004_MISSING_OBSERVATION` and every surplus id is `P004_UNDECLARED_OBSERVATION`; the token set stays at nine |

## Out of scope

* Any change to the default-branch CI workflow.
* Any retroactive re-confirmation of already-shipped harnesses.
* Any bypass, waiver, or `--force` path for P-004. The T0 bootstrap is **not**
  such a path: it runs the full fail-closed confirmation over a declared set and
  halts on any asymmetry, introduces no override flag, and expires at T3.
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
| H7 | The regression suite could have re-implemented the comparison, so a runner defect would pass its own tests | T7 ships the runner as importable code in `src/autoharness/`; **T5b** blocks on T7 and imports it |
| H8 | Tokens that could not name an offending identifier would be undiagnosable in practice | Every token names its `test_id`(s); a token that cannot is declared a runner defect, not an acceptable outcome |
| H9 | *(revision 5)* The stdlib loader contract was stated incorrectly: `loadTestsFromNames` yields one top-level **suite** per name, not one test, and `TestLoader.errors` is a flat list of formatted strings with no name key — so revision 4's positional correlation plus name-keyed `loader.errors` lookup could not have been implemented as written | Replaced with independent per-name `loadTestsFromName`, recursive suite flattening, `len(loader.errors)` snapshot attribution, and test-object-identity correlation to requested names |
| H10 | *(revision 5)* `test_id` uniqueness and red/green disjointness were assigned to a Draft-07 schema that cannot express either (`uniqueItems` compares whole instances; no cross-property comparison exists), so two of the nine tokens had no enforceable owner | Validation boundary split with one owner per token: schema owns per-item shape (`P004_MARKER_MISPLACED`, `P004_EMPTY_RED_SET`), `validate_declared_harness_set()` owns the relational rules (`P004_DUPLICATE_DECLARATION`, `P004_SET_OVERLAP`). Keyed-map alternative considered and rejected for silent last-wins semantics |
| H11 | *(revision 5)* `176-S` was unexecutable: P-002 admits no unlabelled task, `harness-ready` requires P-004 confirmation, and the P-004 precondition under repair is unsatisfiable — the shipment that fixes P-004 was gated behind broken P-004 | Bootstrap task T0 added as the entry point, applying the plan's own authorized declared-harness-set contract to `176-S` alone, fail-closed and complete, expiring at T3, through the existing P-004 operator approval gate. No force grant, waiver, or exit-code relaxation |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Rewrite the P-004 precondition in `templates/policies/workflow-policies.md.tmpl` (T2) | **High** — changes a fail-closed gate every consumer workspace installs | Operator review of the rewritten precondition text | Revert the P-004 section; change is confined to one clause |
| Apply the identical rewrite to `.github/policies/workflow-policies.md` (T3) | High — must land atomically with T2 | Same review | Revert together; T3 blocks on T2; byte-identity check is a gate |
| Add typed fields to the harness-manifest schema (T1) | Medium — existing manifests declaring the old bare-list shape become invalid | Standard PR review | Revert schema; no manifest in this repository declares either field yet |
| Perform the `176-S` bootstrap declared-set red-phase confirmation (T0) | **High** — it is the one place the gate runs under a clause the policy text has not yet installed | **P-004 operator approval gate**, which already governs every red-phase confirmation; the bootstrap acceptance contract is reviewed with it | Withdraw the `harness-ready` labels; T0 modifies no source, schema, or policy file |
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

**Operator checkpoints.** Two. One: the **T0 bootstrap** declared-set red-phase
confirmation, at the existing P-004 operator approval gate, with its bounded
acceptance contract reviewed alongside it. Two: review of the rewritten P-004
precondition text (T2/T3) before merge, since it changes a policy every
consumer installs.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers, and MUST apply both the Constitution
Reviewer persona (policy-registry change) and the Python Reviewer persona
(`unittest` loader/result semantics) inline.

**Unresolved operator decisions blocking safe execution.** None.

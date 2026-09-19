---
title: "P-004 red-phase precondition scoped to the declared shipment harness set"
description: "Implementation plan replacing P-004's ambiguously-scoped, literally-unsatisfiable whole-suite every-function-red precondition with a declared-harness-set precondition admitting two disjoint expected-outcome classes (expected-red and expected-green-characterization) and asserting exact set equality against observed outcomes, delivered atomically across the policy template and its installed mirror, with a typed per-entry declaration shape binding each expected-red test identifier to its own failure marker, a stdlib-unittest TestResult-based observation contract that evaluates markers per test (including subtests) rather than over merged output, a deterministic selector, shipment-scoped declaration storage under a dedicated schema, a single atomic public gate entrypoint, a structured token-subject model, an explicit schema-error-to-token mapping at the Python validation boundary, and regression tests that pin both the satisfiability of the new precondition and the continued green status of the default-branch whole-suite CI gate."
doc_type: plan
source: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
date: 2026-09-17
status: reviewed
plan_id: p004-red-phase-precondition-scoping
plan_role: superseded
revision: 7
supersedes: null
superseded_by: docs/plans/2026-09-18-p004-observation-gate-plan.md
superseded_by_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
supersession_note: "Superseded at architecture level by the 2026-09-18 shared-execution-architecture decision. This document is retained unchanged as the historical contract of attempts 1-8; it is no longer the operative plan for its shipment and is not to be edited further. The successor named in superseded_by is the current state."
source_history:
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempts-01-02-combined.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-03.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-04.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-05.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-06.md
  - docs/reviews/review-history/2026-09-17-p004-red-phase-precondition-scoping-plan-review-attempt-07.md
  - docs/reviews/review-history/2026-09-17-portfolio-attempt-05-provenance-erratum.md
review_manifest: docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
revision_note: "Revision 7 is maintained as one coherent current-state contract rather than as an accreting record of corrections. Superseded requirement variants from revision 6 — the singleton-manifest harness-set field, the nine-token set, the identity-only result correlation, the 'every token names a test_id' invariant, and the shipment-execution-precondition halt narrative — are REWRITTEN OUT of this body rather than annotated. Prior-revision deltas and reviewer chronology are not carried here: the immutable per-attempt review artifacts listed in source_history and the mutable verdict manifest named by review_manifest are the authoritative record of that chronology. Latest attempt and verdict are read from the manifest, never from this file."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 76EBDE6D
stash_ids:
  - 76EBDE6D
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md
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
required gate on the default branch, where it exits **zero**. That alone is not
a contradiction — the two run against different tree states — but it establishes
that the whole suite is expected to be green as a matter of standing policy.

The defect is the clause **"for every test function"**, whose scope is
unstated. Read literally over the discovered tree it is unsatisfiable
independently of branch state and independently of scale: a CHARACTERIZATION
case passes by construction, so an every-function-red precondition cannot hold
for any mixed harness, even against an empty pre-existing suite. With 106 test
files and 2025 test functions under `tests/`, it additionally requires every
unrelated pre-existing test to fail.

That literal reading is **not** the operative one — the normatively primary
Statement row scopes the requirement to "all **harness tests**", the Applies To
row nominates a producer procedure that is already harness-scoped, and 17 live
`harness-ready` records exist that the literal reading would retroactively
invalidate. So the gate is reachable today (see "Executability of `176-S` under
the installed lifecycle"), and this plan is **not** unblocking a deadlock.

What the ambiguity does cost is real and is the reason this release unit
exists: two conforming agents can read the same Precondition row and disagree
about what must be red, the mechanized check names no declared set to compare
against, marker matching is specified over merged output rather than per test,
and there is no single entrypoint that produces the verdict — so a `CONFIRMED`
postcondition is not reproducible evidence of anything. Measured scope: `168-S`
(SHIP-10) and every subsequent TDD shipment inherit that ambiguity. No bypass
is authorized; the gate stays fail-closed.

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

### Declared harness set — storage, ownership, and lifecycle

The declared harness set is **per shipment**, and it does **not** live in
`.autoharness/harness-manifest.yaml`. That file is the **singleton installation
manifest**: a ~150 KB install inventory keyed by `schema_version`,
`installed_at`, `profile_hash`, `config_hash` and a per-file checksum table for
the whole installed tree. It has exactly one instance per workspace, it is
rewritten by `autoharness install` / `autoharness tune`, and it has no shipment
dimension at all. Two concurrent shipments cannot both declare a harness set in
it, a declaration written into it would be destroyed by the next install, and
nothing in it names a reader. Overloading it was the defect.

#### Storage contract

| Property | Value |
|---|---|
| Path | `.autoharness/harness-sets/{shipment_id}.yaml` |
| Key | `shipment_id`, one file per shipment |
| Schema | `schemas/declared-harness-set.schema.json` (new, Draft-07) |
| Writer | the **harness-architect skill**, at its Step 6, in the same step that applies `harness-ready` |
| Authoritative reader | `autoharness.gates.p004.load_declared_harness_set(workspace, shipment_id)` — the **sole** reader; no other code path parses this file |
| Retention | on shipment archive, moved to `.autoharness/gates/harness-set-archive/{shipment_id}-{utc_timestamp}.yaml`; never deleted in place |

This mirrors the installed, already-reviewed `.autoharness/bootstrap-grants/{shipment_id}.yaml`
pattern (`src/autoharness/gates/bootstrap_grant.py`), which solves the identical
problem — per-shipment, operator-visible, auditable gate state that must not be
squeezed into a singleton — and reuses its `_SHIPMENT_ID_PATTERN` identifier
validation and its `compute_manifest_digest()` helper rather than inventing a
second convention.

#### Document shape

```yaml
schema_version: 1
shipment_id: 176-S
feature_id: 168-F
created_at: "2026-09-18T21:00:00Z"
head_sha: 689c48a0c7bd570da0c843b5b6c1b8d8d10c354a
manifest_digest: "<sha256 of the shipment's ordered custom_fields.items>"
harness:
  expected_red:
    - test_id: tests.test_gates_topology.TestResolveExpectedBranches.test_explicit_contract_wins
      marker: "P004_RED: resolve_expected_branches is not implemented"
  expected_green_characterization:
    - test_id: tests.test_gates_topology.TestBranchAliases.test_title_alias_unchanged
```

#### Stale-data rejection (fail-closed, three independent checks)

The reader rejects before the gate runs, and each rejection is a distinct
observable outcome:

1. **Absent file** → `P004_HARNESS_SET_MISSING`, subject
   `DocumentSubject(.autoharness/harness-sets/{shipment_id}.yaml)`.
2. **Identity mismatch** — the document's own `shipment_id` differs from the
   requested one → `P004_HARNESS_SET_STALE`, subject `DocumentSubject`. A file
   copied or renamed between shipments cannot be silently consumed.
3. **Manifest drift** — the reader recomputes `compute_manifest_digest()` over
   the live shipment's ordered `custom_fields.items` and compares it to the
   recorded `manifest_digest`. A mismatch means the shipment's membership
   changed after the harness was declared, so the declaration no longer
   describes the work under confirmation → `P004_HARNESS_SET_STALE`.

There is no "tolerate and continue" path on any of the three. A superseded
declaration is replaced by writing a new document for the same shipment; the
prior one is moved to the archive directory, never edited in place.

#### Declared entry shape

Both fields are **lists of typed entries**, never bare identifier lists — a
bare list leaves the identifier-to-marker mapping undefined and is rejected by
the schema.

| Field | Entry shape | Meaning |
|---|---|---|
| `harness.expected_red` | `{ test_id: str, marker: str }` | Test IDs that MUST fail, each carrying **its own** expected failure marker |
| `harness.expected_green_characterization` | `{ test_id: str }` | Test IDs that MUST pass, pinning pre-existing behaviour |

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

### Validation boundary — schema versus executable validator

This repository's schemas are **JSON Schema Draft-07** (`$schema:
http://json-schema.org/draft-07/schema#` in every existing file under `schemas/`),
and Draft-07 cannot express two of the constraints above at all:

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

**The keyed-map alternative is rejected.** Re-shaping both fields as YAML
mappings keyed by `test_id` would obtain within-list uniqueness from the
object-key rule — but it still cannot express cross-list disjointness, and it
makes a duplicate declaration **silently last-wins** in every mainstream YAML
loader rather than a fail-closed authoring error. Trading a loud error for a
silent overwrite is the opposite of the fail-closed posture this plan exists to
restore. The typed-entry-list shape stands.

The boundary is therefore split, and each token has **exactly one** owner:

| Layer | Owns | Tokens it may raise | Task |
|---|---|---|---|
| **Schema** (`schemas/declared-harness-set.schema.json`, Draft-07) | **Per-item shape only**: both fields are arrays of objects; `expected_red` items `required: [test_id, marker]`; `expected_green_characterization` items `required: [test_id]` with `additionalProperties: false` so a `marker` key is rejected; `test_id` and `marker` are `{type: string, minLength: 1}`; `expected_red` carries `minItems: 1`; document-level `required: [schema_version, shipment_id, feature_id, created_at, manifest_digest, harness]` | — (a schema emits no tokens; see below) | T1 |
| **Python declaration validator** (`src/autoharness/gates/p004.py`, `validate_declared_harness_set()`) | **Token emission for every declaration defect**: it runs the schema and maps each `jsonschema` error to its token, then evaluates the two relational constraints the schema cannot express | `P004_MARKER_MISPLACED`, `P004_EMPTY_RED_SET`, `P004_DUPLICATE_DECLARATION`, `P004_SET_OVERLAP` | T7 |
| **Python storage reader** (`src/autoharness/gates/p004.py`, `load_declared_harness_set()`) | **Document identity and freshness**: existence, `shipment_id` identity, and `manifest_digest` recomputation | `P004_HARNESS_SET_MISSING`, `P004_HARNESS_SET_STALE` | T1b |

#### A schema does not emit tokens — the mapping is concrete and tested

A JSON Schema validator produces `jsonschema.ValidationError` objects, not
autoharness tokens. Saying "the schema owns `P004_MARKER_MISPLACED`" names the
layer that *detects* the defect while leaving the layer that *reports* it
undefined — and an undefined reporting boundary is how a fail-closed token
silently degrades into an opaque stack trace. The mapping is therefore stated
here as an executable contract with a single owner.

`validate_declared_harness_set(manifest)` is the **only** declaration-validation
entry point. It runs, in this order, and returns the accumulated token list:

1. **Shape validation.** `jsonschema.Draft7Validator(schema).iter_errors(manifest)`,
   consumed with `sorted(..., key=jsonschema.exceptions.relevance)` so ordering
   is deterministic. Each error is mapped to a token by its
   `(absolute_path, validator)` pair — structural attributes of the error
   object, never its human-readable `message` string, which is library-version
   dependent and must not be parsed:

   | `validator` | `absolute_path` prefix | Token | Named identifier |
   |---|---|---|---|
   | `required` (missing `marker`) | `harness.expected_red[i]` | `P004_MARKER_MISPLACED` | `test_id` of item `i` |
   | `additionalProperties` (surplus `marker`) | `harness.expected_green_characterization[i]` | `P004_MARKER_MISPLACED` | `test_id` of item `i` |
   | `minItems` | `harness.expected_red` | `P004_EMPTY_RED_SET` | *(none — the list is empty)* |
   | `required` (missing `test_id`), `type`, `minLength` | either list | `P004_MARKER_MISPLACED` | JSON pointer to the offending item |

   The identifier is recovered by indexing the **parsed document** with
   `error.absolute_path`, so every emitted token carries a structured subject
   naming its offending entry per the subject model below.
2. **Unmapped-error fail-closed rule.** A `ValidationError` whose
   `(absolute_path, validator)` pair matches no row above raises
   `P004_DECLARATION_SCHEMA_ERROR` — **not** a member of the gate's thirteen-token
   set but a hard error that halts the run and reports the raw
   `error.json_path` and `error.validator`. A shape defect is never silently
   dropped, and the thirteen-token set is never silently extended.
3. **Relational validation**, evaluated over the parsed document only after
   step 1 produced no tokens: within-list `test_id` uniqueness
   (`P004_DUPLICATE_DECLARATION`) and cross-list disjointness
   (`P004_SET_OVERLAP`).

`validate_declared_harness_set()` runs **before** the load step and fails
closed; the runner never proceeds to load a declaration that did not pass it.
Each token is emitted from exactly one place, and the schema restates no
relational rule. A `uniqueItems` attempt in the schema, or any re-statement of a
relational rule there, is a review-visible defect.

### The single atomic public gate entrypoint

There is **exactly one** public way to obtain a P-004 red-phase verdict, and
every surface that needs one crosses it.

```text
autoharness gate p004 --shipment <shipment_id> [--json]
```

backed by the importable

```python
autoharness.gates.p004.run_p004_gate(workspace, shipment_id) -> P004GateResult
```

`run_p004_gate()` owns the whole pipeline atomically, in this fixed order, and
no caller may perform, skip, reorder, or substitute any stage of it:

1. `load_declared_harness_set()` — existence, identity, freshness
   (`P004_HARNESS_SET_MISSING` / `P004_HARNESS_SET_STALE`).
2. `validate_declared_harness_set()` — schema plus relational validation, with
   `P004_DECLARATION_SCHEMA_ERROR` as the unmapped-shape halt.
3. Independent per-name load with the identity checks below.
4. Run under `P004Result` (including the mandatory `addSubTest` override).
5. Exact-set-equality comparison against the declared outcome map, producing
   the outcome × declared-class matrix's tokens.
6. Emit `P004GateResult` and its JSON serialization.

**A bare `python -m unittest <ids>` invocation does not satisfy P-004 and never
produces a red-phase verdict.** It performs stage 4 only: it reads no
declaration, validates nothing, correlates nothing, compares nothing, and emits
no token. The policy text (T2/T3) states this as a normative prohibition, and
the harness-architect skill (T4) invokes the gate command rather than a bare
test command. The ID-addressed selector below remains in the contract as the
**human-readable statement of which tests the gate runs**, not as an alternative
invocation.

#### `P004GateResult` JSON

```json
{
  "shipment_id": "176-S",
  "gate_result": "CONFIRMED | FAILED",
  "declaration_path": ".autoharness/harness-sets/176-S.yaml",
  "declaration_digest": "<sha256 of the declaration document bytes>",
  "manifest_digest": "<sha256 of the shipment's ordered items>",
  "compilation": "PASS | FAIL",
  "tokens": [
    {"token": "P004_MARKER_ABSENT",
     "subject": {"kind": "test", "test_id": "tests.x.Y.test_z"},
     "detail": "declared marker not present in this test's own failure text"}
  ]
}
```

`Red Phase: CONFIRMED` may be recorded **only** from a `gate_result:
"CONFIRMED"` in this JSON, and the recording surface carries the
`declaration_digest` so the postcondition is bound to the exact declaration it
confirmed.

#### Agent-facing parity where terminal execution is unavailable

An agent that cannot execute a terminal command must not be able to reach a
weaker verdict than one that can. The parity contract is:

* The agent emits a literal `P004_GATE_REQUEST` block naming the exact command
  (`autoharness gate p004 --shipment <id> --json`) and halts pending its
  result.
* The operator or runtime executes it and returns the JSON.
* The agent records the returned JSON **verbatim** as the postcondition
  evidence, including `declaration_digest`.
* The agent **may not** synthesize `CONFIRMED` from its own reading of test
  output, from a transcript, from a partial run, or from a prior session's
  result, and may not apply `harness-ready` without a verbatim `CONFIRMED`
  JSON body for the current `declaration_digest`.
* If neither the CLI nor an operator-executed equivalent is available, the
  harness-architect halts under P-004's Violation Action — **do not apply
  `harness-ready`, halt and report**. There is no degraded-mode pass.

### Selector (which tests the gate runs)

The gate runs the union of the two declared sets, addressed by explicit test
ID, not by discovery. Written out, the addressed set is:

```text
PYTHONPATH=src python -m unittest <id-1> <id-2> ... <id-n>
```

Addressing by ID rather than by marker, tag, or naming convention is
deliberate: it makes the confirmed set exactly the declared set, so a test that
silently fails to be collected is a missing observation rather than a silently
empty pass. This line is documentation of the addressed set. It is **not** an
invocation a producer may substitute for `autoharness gate p004`.

### Observation contract (stdlib `unittest`, `TestResult`-based)

The command line above is the **human-readable** statement of the selector.
The gate itself does **not** parse that command's merged stdout/stderr. Merged
output cannot attribute a marker to a specific test when more than one test
fails, which is the exact ambiguity that makes a bare-identifier declaration
unusable. Observation is defined against the stdlib result object:

1. **Load — each declared name independently.** Two stdlib facts govern this
   step and rule out the obvious shortcuts:

   * `TestLoader.loadTestsFromName(name)` returns a **`TestSuite`**, not a
     `TestCase`. On an unresolvable name it returns
     `self.suiteClass((_FailedTest(<derived-method-name>, exc),))` — a suite
     wrapping the placeholder. `loadTestsFromNames(names)` is defined as
     `self.suiteClass([self.loadTestsFromName(n) for n in names])`, so its
     top-level members are one **suite** per input name, never one **test** per
     input name; and a resolvable name may expand to many tests (a module or
     class name). Positional correlation over `loadTestsFromNames` is therefore
     unsound in both the failure and the success case, and is not used.
   * `TestLoader.errors` is a flat **`list` of formatted message strings**
     appended in load order. It is **not** a mapping and has no name key, so
     `name in loader.errors` is meaningless and corroborates nothing.

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
       id_mismatch = {}                    # requested name -> observed TestCase.id()
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
           elif tests[0].id() != name:              # DECLARATION CONFORMANCE CHECK
               id_mismatch[name] = tests[0].id()
       return loader, loaded, requested_of, unloadable, id_mismatch
   ```

   Four properties make this correct:

   * **Independent loading** removes any need for positional correspondence.
     Each `loadTestsFromName` call concerns exactly one requested name, so
     nothing has to be matched up afterwards.
   * **Error attribution is by list-length snapshot**, `loader.errors[before:]`,
     which is the only sound way to read an append-only list of unkeyed
     strings. No string is parsed and no name is looked up.
   * **Result correlation is by test-object identity.** The map
     `id(test_object) -> requested_name` is built at load time from the very
     objects that are about to be run, so an observed result is attributed to
     its requested name reliably. `unittest.loader._FailedTest.id()` is **not**
     guaranteed to equal the requested name; identity correlation makes that a
     non-issue for *attribution*.
   * **Declaration conformance is verified separately, by string equality.**
     Object identity answers *which object came back*; it does not answer *is
     this the test that was declared*. These are two different questions and
     the contract enforces both, independently:

     | Question | Mechanism | Governs |
     |---|---|---|
     | Which requested name owns this result? | `requested_of[id(test)]` — object identity | **Attribution** |
     | Is the loaded test the declared test? | `tests[0].id() == requested_name` — exact string equality | **Declaration conformance** |

     A successfully-loaded, singleton-resolving name whose `TestCase.id()` does
     **not** equal the requested string emits **`P004_DECLARED_ID_MISMATCH`**
     with `TestSubject(requested_name)` and the observed id in `detail`. This is
     the case a rename, a relocation, or a loader alias produces: object
     identity is perfectly satisfied — the loader did return an object and the
     runner will attribute its result correctly — while the declaration is
     violated, because the test that ran is not the test that was declared.
     Without this check that violation is invisible.

     `_FailedTest` placeholders are **excluded** from the equality check because
     they are already classified `P004_MISSING_OBSERVATION` at load time; running
     the check on them would emit a second, redundant token for the same defect.
     Neither check substitutes for the other, and neither is derived from the
     other.

   **Classification at load time, before anything runs.** A declared name is
   `P004_MISSING_OBSERVATION` when it produced any load error, or resolved to a
   `_FailedTest`, or resolved to **zero** tests. A declared name that resolves
   to **more than one** test is a declaration defect: the declared `test_id`
   itself is reported `P004_MISSING_OBSERVATION` (it addressed no single test),
   and every surplus resolved test id that is not itself declared is reported
   `P004_UNDECLARED_OBSERVATION`. Both are existing tokens; the token set
   remains exactly **THIRTEEN**. None of these classifications is ever a genuine
   red observation, and none is derived from traceback text or from an `id()`
   string comparison.

   The loader is rooted so that `PYTHONPATH=src` and the repository root
   resolve identically to the CI invocation.
2. **Run.** `unittest.TextTestRunner(resultclass=P004Result, verbosity=0)` over
   a suite rebuilt from the flattened, load-classified tests. `P004Result`
   subclasses `unittest.TextTestResult` and overrides `addSuccess`,
   `addFailure`, `addError`, `addSubTest`, `addSkip`, `addExpectedFailure`, and
   `addUnexpectedSuccess` to record, per test, the tuple
   `(requested_of[id(test)], test.id(), outcome, detail_text)`. The **first**
   element — the requested name recovered from the load-time identity map — is
   the key everything downstream is compared on; `test.id()` is recorded as
   corroborating evidence and is never used to look a test up.
   * **`addFailure(test, err)` and `addError(test, err)` receive an `exc_info`
     TUPLE** `(type, value, traceback)` — **not** a formatted string. The
     formatted per-test traceback string is produced by the **inherited**
     `TestResult._exc_info_to_string(err, test)`, which the overrides call (or
     which the base implementation calls when the override delegates via
     `super()`); it is the same string that lands in `result.failures` /
     `result.errors`. `detail_text` is exactly that per-test string and nothing
     else. It is never the concatenated run output, and the overrides must not
     treat `err` as text.
   * **`addSubTest(test, subtest, err)` is overridden and is not optional.**
     A `unittest` subtest failure is reported **only** through `addSubTest`; the
     base `TestResult` never calls `addFailure`/`addError` for it, and a
     `TestCase` whose subtests all failed still reaches `addSuccess`. A
     `P004Result` that omits the override therefore records a red harness test
     as `success` and the gate emits a spurious `P004_UNEXPECTED_GREEN` — a
     silent false pass, which is the exact failure class this plan exists to
     remove. The override's contract:
     * `err is None` means that subtest passed; record nothing and do **not**
       alter the parent's recorded outcome.
     * `err` is an `exc_info` **tuple**, formatted per subtest by the same
       inherited `_exc_info_to_string(err, subtest)`.
     * Attribution is by the **parent** `test` object: `requested_of[id(test)]`.
       `subtest` is a `_SubTest` proxy created at run time and is **not** in the
       load-time identity map, so keying on it would lose the requested name.
     * The parent's recorded outcome becomes `failure` (or `error` when the
       exception is not an `AssertionError` subclass) on the **first** failing
       subtest, and the parent's `detail_text` is the **concatenation of every
       failing subtest's own formatted string, in call order**, each prefixed
       with that subtest's `_subDescription()`. Marker matching then runs
       against that concatenation, so a marker declared for a test whose only
       red path is a subtest is still matched — and it is still **that test's
       own** text, never another test's and never merged run output.
     * A test that reaches `addSuccess` **after** at least one failing subtest
       keeps the failure outcome; the success call must not overwrite it.
   * `addSkip`, `addExpectedFailure`, and `addUnexpectedSuccess` are recorded
     as their own distinct outcomes and are **never** folded into pass or fail.
     Their gate treatment is defined by the total outcome matrix below.
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
| `P004_INCONCLUSIVE_OUTCOME` | A declared ID (either class) was observed `expected_failure` or `unexpected_success` |
| `P004_DECLARED_ID_MISMATCH` | A declared name loaded exactly one non-placeholder test whose `TestCase.id()` is not equal to the declared string |
| `P004_HARNESS_SET_MISSING` | No declaration document exists at `.autoharness/harness-sets/{shipment_id}.yaml` |
| `P004_HARNESS_SET_STALE` | The declaration's `shipment_id` differs from the requested one, or its `manifest_digest` no longer matches the live shipment manifest |
| `P004_EMPTY_RED_SET` | `expected_red` is empty |
| `P004_SET_OVERLAP` | A `test_id` appears in both declared lists |
| `P004_DUPLICATE_DECLARATION` | A `test_id` appears twice within one declared list |
| `P004_MARKER_MISPLACED` | An `expected_red` entry omits `marker`, or an `expected_green_characterization` entry supplies one |

Thirteen tokens. `P004_DECLARATION_SCHEMA_ERROR` is deliberately **not** among
them: it is the hard unmapped-shape halt, not a gate outcome.

#### Total outcome matrix — every declared class × every observed outcome

The gate's classification is **total**: every cell below is defined, and there
is no default, fallthrough, or "other" branch. An observed outcome that matches
no enumerated value is itself a runner defect and halts.

| Observed outcome | `expected_red` | `expected_green_characterization` | Undeclared |
|---|---|---|---|
| `success` | `P004_UNEXPECTED_GREEN` | **pass** (no token) | `P004_UNDECLARED_OBSERVATION` |
| `failure` | **pass** if its own marker is present, else `P004_MARKER_ABSENT` | `P004_UNEXPECTED_RED` | `P004_UNDECLARED_OBSERVATION` |
| `error` | **pass** if its own marker is present, else `P004_MARKER_ABSENT` | `P004_UNEXPECTED_RED` | `P004_UNDECLARED_OBSERVATION` |
| `skip` | `P004_MISSING_OBSERVATION` | `P004_MISSING_OBSERVATION` | `P004_UNDECLARED_OBSERVATION` |
| `expected_failure` | `P004_INCONCLUSIVE_OUTCOME` | `P004_INCONCLUSIVE_OUTCOME` | `P004_UNDECLARED_OBSERVATION` |
| `unexpected_success` | `P004_INCONCLUSIVE_OUTCOME` | `P004_INCONCLUSIVE_OUTCOME` | `P004_UNDECLARED_OBSERVATION` |
| absent (no result entry) | `P004_MISSING_OBSERVATION` | `P004_MISSING_OBSERVATION` | n/a — an undeclared ID with no result is not observed at all |
| load error / `_FailedTest` / zero tests / >1 test | `P004_MISSING_OBSERVATION` (+ `P004_UNDECLARED_OBSERVATION` per surplus id) | same | n/a |
| loaded but `id()` ≠ declared | `P004_DECLARED_ID_MISMATCH` | `P004_DECLARED_ID_MISMATCH` | n/a |

**Why `expected_failure` and `unexpected_success` are blocking rather than
folded.** `@unittest.expectedFailure` inverts the runner's exit semantics: a
test that fails is reported through `addExpectedFailure` and the run still
exits **zero**, while a test that passes is reported through
`addUnexpectedSuccess` and the run exits **non-zero**. Folding
`expected_failure` into "red" would let a decorated harness test satisfy the
red requirement while the run exits zero, destroying the "exits non-zero"
component of the precondition; folding `unexpected_success` into "green" would
let a *passing* test masquerade as a characterization pass while the run exits
non-zero. Neither direction can be made sound, and the decorator's presence
means the harness author has already declared the test's outcome twice, in two
places, with no guarantee they agree. The only defensible treatment is to
refuse the observation: `P004_INCONCLUSIVE_OUTCOME`, blocking, with remediation
being removal of the decorator from declared harness tests. Harness tests are
authored by the harness-architect in the same step as the declaration, so this
is always actionable.

#### Token subjects — the structured subject model

A token does **not** always have an offending `test_id`, and requiring one was
unsatisfiable: `P004_EMPTY_RED_SET` is a property of a *collection*, and
`P004_MARKER_MISPLACED` can fire on a malformed entry that has **no** `test_id`
at all (that is precisely why it is malformed). Every token therefore carries
exactly one **tagged subject**, and the subject kind is part of the token's
definition:

```text
TokenSubject :=
    TestSubject       { kind: "test",       test_id }
  | CollectionSubject { kind: "collection", field }
  | EntrySubject      { kind: "entry",      field, index, json_pointer, test_id? }
  | DocumentSubject   { kind: "document",   path }
```

| Token | Subject kind |
|---|---|
| `P004_UNEXPECTED_GREEN`, `P004_UNEXPECTED_RED`, `P004_MISSING_OBSERVATION`, `P004_UNDECLARED_OBSERVATION`, `P004_MARKER_ABSENT`, `P004_INCONCLUSIVE_OUTCOME`, `P004_DECLARED_ID_MISMATCH` | `TestSubject` |
| `P004_EMPTY_RED_SET` | `CollectionSubject(field: "harness.expected_red")` |
| `P004_SET_OVERLAP`, `P004_DUPLICATE_DECLARATION` | `EntrySubject` (the *later* offending entry; `test_id` present by definition) |
| `P004_MARKER_MISPLACED` | `EntrySubject` — `field`, `index`, and `json_pointer` are always present; `test_id` is **optional** and omitted when the malformed entry has none |
| `P004_HARNESS_SET_MISSING`, `P004_HARNESS_SET_STALE` | `DocumentSubject(path)` |
| `P004_DECLARATION_SCHEMA_ERROR` (hard error) | `EntrySubject` when `error.absolute_path` is non-empty, otherwise `DocumentSubject` |

The binding invariant is therefore: **every token carries exactly one
well-formed tagged subject, and a token whose subject cannot be constructed is
a runner defect, not an acceptable outcome.** This replaces the unsatisfiable
"every token names a `test_id`" rule, and the same four-variant model is
restated verbatim in the policy text (T2/T3), in the JSON serialization, and in
the contract tests (T5a/T5b), so plan, policy, tasks, and tests agree.

The compile precondition (`python -m py_compile`) is unchanged and still exits 0.

### What is explicitly unchanged

* `.github/workflows/ci.yml` line 112 and the whole-suite default-branch gate.
  It must continue to exit **zero**. This plan adds no command to CI and
  removes none.
* P-002's harness-ready label semantics and its violation action.
* The postcondition wording `Compilation: PASS` / `Red Phase: CONFIRMED`,
  which gains the declared-set summary but keeps its existing markers.

## Executability of `176-S` under the installed lifecycle

`176-S` repairs P-004, so whether it can itself execute under the installed
P-002/P-004 pair is a load-bearing question rather than a scheduling detail.
It is answered from the **installed lifecycle as it actually runs**. The answer
is that `176-S` is executable today, through the ordinary composed path below,
with **no** bootstrap task, no bootstrap grant, no waiver, no `--force`, no
exit-code relaxation, no out-of-DAG operator policy edit, and no
self-authorized mutation of any kind.

### The composed lawful path, step by step

The Ship agent template (`templates/agents/_ship.agent.md.tmpl`) fixes the
order, and each step's precondition is discharged by the step before it:

1. **Shipment claim (Step 0.5).** Claiming a shipment has **no**
   `harness-ready` precondition. P-002's gate point is "Queue building (Step 2)
   and task claiming (Step 3)", not shipment claim. `176-S` is claimable as it
   stands.
2. **Harness generation (Step 2), strictly before any task claim.** Ship
   partitions the shipment's queued tasks into already-harnessed and
   needs-harness and invokes the **harness-architect** skill for the batch.
   Harness generation is an agent-invoked skill step, **not a claimable backlog
   task**, so it is never itself subject to P-002's `harness-ready` filter.
   This is the producer/consumer split P-002 states in its own Applies To row:
   "`ship` (consumer; harness-architect skill is the producer)".
3. **The harness-architect authors the harness into `tests/`.** For `176-S`
   that is T5a's contract tests plus the structural stubs they import. Those
   tests are ordinary modules under `tests/`, so they are **discovered by the
   very command P-004's Precondition names**.
4. **P-004's Precondition is then evaluated, and both components hold.**

   | Component | Status after step 3 | Why |
   |---|---|---|
   | `python -m py_compile src/autoharness/cli.py` exits **0** | holds | Harness authoring adds test modules and compilable structural stubs; P-004's own Statement row requires the harness to *compile*, and the harness-architect verifies compilation before the red check |
   | `PYTHONPATH=src python -m unittest discover -s tests` exits **non-zero** | holds | The freshly authored harness tests are discoverable and fail. The whole-suite run is RED **because of** the new harness — this is the exact state the Precondition demands, produced by the step that precedes the gate |
   | "with expected failure markers in the output for every test function" | holds | Scoped by the Statement row to the harness tests; each authored harness test carries its own declared marker |

5. **`harness-ready` is applied**, and only then does Step 3's ready-queue
   build and Step 4.1's claim apply P-002's filter — by which time every task
   in the shipment carries the label.

**This is the bootstrap.** The full-suite RED state is not an obstacle to be
worked around; it is the observable the precondition is written to detect, and
harness generation is what produces it, one lifecycle step before the gate that
reads it. Nothing in `176-S` needs to exist before that happens.

### The one genuinely ambiguous clause, and how it is read

The trailing qualifier **"for every test function"** is the only clause that
could be read to demand an expected-failure marker from *every function in the
discovered tree*, including the hundreds of pre-existing passing tests. That
reading is rejected, on the installed text itself:

* **The Statement row is normatively primary and explicitly harness-scoped**:
  "all **harness tests** compile and fail with expected markers." The
  Precondition is the mechanized check *of that statement*; it cannot enlarge
  the statement's quantifier.
* **The Applies To row designates the enforcement vehicle** — `ship` *via the
  harness-architect skill* — and that skill's installed Step 5.2 reads "Run
  `{{TEST_COMMAND}}` **for the harness tests**. ALL tests MUST fail with the
  expected failure marker." The producer procedure the policy itself nominates
  is already harness-scoped.
* **The whole-suite reading voids the gate universally.** Under it no shipment
  in the project's history could ever have satisfied P-004, because a green
  regression suite has no markers by construction. Yet 17 live backlog records
  carry `harness-ready`, and `094.001-T` records an explicitly harness-scoped
  red phase. A reading that makes the gate's entire operative history unlawful
  is not the operative reading.
* **The exit-code components are not in conflict with CI.**
  `.github/workflows/ci.yml` requires the whole suite to exit **zero** on the
  default branch; P-004 requires it to exit **non-zero** at the red gate. These
  observe different states of different refs — the pre-implementation harness
  state on the feature branch, and the post-implementation state on the default
  branch. The transient full-suite RED is a feature-branch state and is lawful.

So the clause is a **clarity defect**, not a reachability barrier. `T2`/`T3`
replace it with the explicit harness-scoped wording and the thirteen-token
contract, which is a repair of ambiguous text — not the unlocking of a
deadlock, because there is no deadlock.

### What is not claimed

* No `--force`, waiver, `skip_policy`, bootstrap grant, or exit-code relaxation
  is introduced anywhere by this release unit.
* No out-of-DAG operator policy edit is required, requested, or relied upon at
  any point. `176-S` has no shipment execution precondition beyond the ordinary
  lifecycle.
* No shipment-scoped exemption clause exists to be cited by a later shipment.
* Operator approval is never asserted to change the installed P-004
  precondition. P-004's Violation Action ("Do NOT apply `harness-ready`. Halt
  and report") remains the response to a genuine red-phase failure, and this
  plan neither weakens nor invokes it as an escape hatch.
* The default-branch whole-suite gate is untouched and must be green at merge
  (`T6` is the standing assertion).

## Work Breakdown

| # | Task | Scope | Blocked by |
|---|---|---|---|
| T1 | Add `schemas/declared-harness-set.schema.json` (Draft-07) for the **shipment-scoped** declaration — **per-item shape only**: typed entry lists `{test_id, marker}` / `{test_id}`, requiredness, `additionalProperties: false` on characterization entries, `minLength: 1` strings, `minItems: 1` on `expected_red`, plus the document-level required keys. **No uniqueness and no disjointness rule is expressed in the schema**; those belong to T7. `schemas/harness-manifest.schema.json` is **not** modified | `schemas/` | — |
| T1a | **RED** — author the failing storage-lifecycle tests for `load_declared_harness_set()`: absent document, `shipment_id` identity mismatch, `manifest_digest` drift, archive-on-close retention, and sole-reader containment | `tests/` | T1 |
| T1b | **IMPLEMENTATION** — `load_declared_harness_set()` and the writer/retention helpers over `.autoharness/harness-sets/{shipment_id}.yaml`, reusing `bootstrap_grant.compute_manifest_digest()` and its shipment-id pattern; emits `P004_HARNESS_SET_MISSING` / `P004_HARNESS_SET_STALE` | `src/autoharness/gates/p004.py` | T1a |
| T2 | Rewrite the P-004 Statement, Precondition, Postcondition, and Violation Action in the policy **template**: harness-scoped quantifier, all **thirteen** tokens with their subject kinds, the structured subject model, and the normative statement that a bare `python -m unittest <ids>` invocation does not satisfy P-004 | `templates/policies/workflow-policies.md.tmpl` | T1 |
| T3 | Apply the byte-identical rewrite to the installed mirror, atomically with T2 | `.github/policies/workflow-policies.md` | T2 |
| T4 | Update the harness-architect skill to write the shipment-scoped declaration at its Step 6 and to obtain its red-phase verdict **only** from `autoharness gate p004 --shipment <id> --json`, recording the returned JSON verbatim; include the `P004_GATE_REQUEST` parity block for terminal-unavailable runtimes. **The skill exists as `templates/skills/harness-architect/SKILL.md.tmpl` and has no installed mirror under `.github/skills/` in this workspace**; the task edits the template, and edits an installed mirror only where one is present | `templates/skills/harness-architect/` (+ installed mirror where present) | T2, T7b |
| T5a | **RED** — author the composed state-machine contract tests: one legitimate passing state, one failing state per token (all **thirteen**), the full declared-class × observed-outcome matrix including `expected_failure`/`unexpected_success`, the `addSubTest` case, the `TestCase.id()`-mismatch case, the schema-error-mapping case, and one subject-model assertion per subject kind. **Import-safe** (see below), authored against the not-yet-existing entry points, and **observed failing** | `tests/` | T1 |
| T6 | CI-invariant regression test asserting the whole-suite gate is unmodified and still green | `tests/` | T3 |
| T7 | **IMPLEMENTATION** — `validate_declared_harness_set()` (schema validation with `jsonschema` error-to-token mapping, within-list uniqueness, cross-list disjointness) plus `P004Result` and the observation machinery: independent per-name `loadTestsFromName` loading, recursive suite flattening, `len(loader.errors)` snapshot attribution, test-object-identity correlation, the separate `TestCase.id()` declaration-conformance check, `exc_info`-tuple handling with inherited `_exc_info_to_string` formatting, **`addSubTest` handling**, the total outcome matrix, and the tagged-subject constructor | `src/autoharness/gates/p004.py` | T5a, T1b |
| T7b | **IMPLEMENTATION** — the single atomic public entrypoint `run_p004_gate()` and its `autoharness gate p004 --shipment <id> [--json]` CLI surface, owning load → validate → run → compare → tokens → JSON, and the `P004GateResult` serialization | `src/autoharness/gates/p004.py`, `src/autoharness/cli.py` | T7 |
| T5b | **GREEN** — observe the full thirteen-token contract suite passing against the shipped gate, and add the regression cases that only make sense against a real implementation, including the end-to-end assertion that a bare `python -m unittest <ids>` run produces no `P004GateResult` | `tests/` | T7b |

### RED-task import safety (binding on T1a and T5a)

A RED test module that raises at **import** time does not produce a red
observation — the loader records a `_FailedTest` placeholder, and the gate
classifies that `P004_MISSING_OBSERVATION`, which is a missing observation and
**not** valid red. A RED task whose tests cannot be collected therefore fails
its own gate.

Both RED tasks are consequently authored so that:

* every module under test that does not yet exist is imported **inside the test
  body**, through a small `_load_boundary()` helper, never at module top level;
* each declared RED test **individually executes** and fails or errors on its
  own, producing **its own** `detail_text` containing **its own** declared
  marker;
* the module imports cleanly under `unittest.defaultTestLoader` with zero
  `loader.errors`, which is asserted directly;
* each test carries the exact marker string recorded for it in the shipment's
  declaration document.

This rule is not specific to `176-S`. The analogous RED tasks in the sibling
release units — `170.011-T`, `171.015-T`, and `172.008-T` — carry the same
obligation, stated in their own current-state task records rather than
cross-referenced from here.

T2 and T3 are separate tasks but a single atomic change set: an installed
mirror that disagrees with its template is the exact drift class recorded in
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`.
T3 declares a `blocks` dependency on T2 so ordering is explicit.

### Dependency order (machine-encoded)

The ordering below is encoded as `blocks` edges in the backlog, not as prose:

* **T1 is the single entry point of `176-S`.** It is blocked by nothing. No task
  in this release unit performs harness generation; the harness-architect skill
  does that at Ship Step 2, before any task in the shipment is claimed.
* **T5a (RED) blocks on T1 only.** It is authored against the schema's typed
  entry shape and the *declared* thirteen-token contract, and is observed failing
  because `P004Result` does not yet exist. **T5a does NOT depend on T7.** That
  asymmetry is the whole content of the red phase; reversing it would make T5a
  a test-after task wearing a red-phase label.
* **T1a (RED, storage) blocks on T1 only**, and **T1b blocks on T1a**, so the
  shipment-scoped storage boundary is likewise test-first.
* **T7 (IMPLEMENTATION) blocks on T5a and T1b.** The executable observation
  boundary the schema (T1) and the policy text (T2/T3) both describe is written
  to turn an already-failing, already-reviewed contract green, and it consumes
  the storage reader rather than re-implementing it.
* **T7b (the atomic public entrypoint) blocks on T7**, so the gate surface is
  assembled only once every part it composes exists.
* **T5b (GREEN) blocks on T7b.** The token matrix is observed passing against
  the real gate entrypoint, never against a test-local re-implementation of it.
* **T3 blocks on T2**, **T4 blocks on T2 and T7b** (the skill cannot be wired
  to an entrypoint that does not exist), and **T6 blocks on T3**, so the
  mirror, the skill, and the CI-invariant assertion all follow the surface they
  describe.

### TDD order

```text
T1 ──┬─> T1a ─> T1b ──┐
     ├─> T5a ─────────┴─> T7 ─> T7b ─┬─> T5b
     └─> T2 ─> T3 ─> T6              └─> T4
```

RED (`T1a`, `T5a`) strictly precedes IMPLEMENTATION (`T1b`, `T7`, `T7b`), which
strictly precedes GREEN (`T5b`) and the producer wiring (`T4`).

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
* A fixture in which a declared name loads exactly one **real** test whose
  `TestCase.id()` differs from the declared string emits
  `P004_DECLARED_ID_MISMATCH` **while its result is still correctly attributed**
  — proving the two checks are independent rather than one derived from the
  other.
* A declared test decorated `@unittest.expectedFailure` that fails emits
  `P004_INCONCLUSIVE_OUTCOME` and the gate result is `FAILED`, even though the
  bare runner would exit 0; the mirror case (an `expectedFailure`-decorated test
  that passes, reported `unexpected_success`) emits the same token.
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
* `validate_declared_harness_set()` converts the `jsonschema` `required` error
  for a missing `marker` into `P004_MARKER_MISPLACED` carrying an
  `EntrySubject` with `field`, `index`, and `json_pointer`, converts the
  `additionalProperties` error for a surplus `marker` into the same token for
  its entry, and converts the `minItems` error into `P004_EMPTY_RED_SET`
  carrying a `CollectionSubject`. Each assertion is made on the returned token
  and subject values, not on any exception message text.
* A malformed `expected_red` entry that **omits `test_id` entirely** emits
  `P004_MARKER_MISPLACED` with an `EntrySubject` whose `test_id` is absent and
  whose `json_pointer` resolves — the case the former "every token names a
  `test_id`" rule could not express.
* Every emitted token in every fixture carries exactly one tagged subject whose
  `kind` matches the subject table, asserted by a single parameterized test over
  the whole token set.
* `load_declared_harness_set()` emits `P004_HARNESS_SET_MISSING` for an absent
  document, and `P004_HARNESS_SET_STALE` for both a `shipment_id` mismatch and a
  recomputed `manifest_digest` mismatch, with no tolerate-and-continue path.
* A synthetic `ValidationError` whose `(absolute_path, validator)` pair matches
  no mapping row raises `P004_DECLARATION_SCHEMA_ERROR` and halts, proving no
  shape defect is silently dropped and the thirteen-token set is not silently
  extended.
* `run_p004_gate()` is the only producer of a `CONFIRMED` verdict: an
  end-to-end fixture runs the identical declared IDs through a bare
  `python -m unittest` invocation and asserts no `P004GateResult` and no
  `CONFIRMED` marker is produced by it.
* A declared `expected_red` test whose **only** failing path is a
  `self.subTest(...)` block is observed as a **failure**, not a success: the
  case fails without an `addSubTest` override and passes with it, so the
  regression pins the silent-false-pass defect directly.
* A declared test with three subtests of which the second and third fail
  produces a `detail_text` containing **both** failing subtests' formatted text
  in call order, and a marker declared against the third subtest's text is
  matched.
* A declared test whose subtests all pass is observed `success` and is not
  downgraded.
* Both RED task modules (`T1a`, `T5a`) import cleanly: loading each module
  through `unittest.defaultTestLoader` yields zero `loader.errors` and zero
  `_FailedTest` placeholders, and each declared RED test individually executes
  and fails with its own declared marker in its own `detail_text`.
* `176-S` is verified executable under the installed lifecycle without any
  bootstrap task, bootstrap grant, waiver, or operator policy edit: shipment
  claim carries no `harness-ready` precondition, harness generation runs as a
  harness-architect skill step before any task claim, and the full-suite RED
  state that P-004's Precondition requires is produced by that step. No
  `--force`, waiver, `skip_policy`, or exit-code relaxation appears anywhere in
  this release unit.
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
| R8 | A Draft-07 schema silently fails to enforce uniqueness or disjointness, so two declarations collide unnoticed | Those two rules live solely in `validate_declared_harness_set()` (T7); the split is stated normatively with one owner per token, and a `uniqueItems` attempt in the schema is a review-visible defect |
| R9 | A schema shape violation surfaces as an opaque `jsonschema` stack trace instead of a named token, so a fail-closed token degrades into an unhandled exception | `validate_declared_harness_set()` is the sole declaration-validation entry point and maps every `ValidationError` to a token by its structural `(absolute_path, validator)` pair — never by parsing `message`. An unmapped pair raises `P004_DECLARATION_SCHEMA_ERROR` and halts, so no shape defect is dropped |
| R10 | A declared `test_id` addresses a module or class, silently widening the confirmed set | A declared name resolving to anything other than exactly one test is classified at load time: the declared ID is `P004_MISSING_OBSERVATION` and every surplus id is `P004_UNDECLARED_OBSERVATION`; the token set stays at thirteen |
| R11 | A red harness test whose only failing path is a subtest is recorded as a pass, emitting a spurious `P004_UNEXPECTED_GREEN` | `addSubTest` is a required override with a stated attribution and detail-concatenation contract; T5a authors the subtest cases red and T5b verifies them green, so the silent false pass is pinned by a test that fails without the override |
| R12 | `176-S` cannot execute under the installed P-002/P-004 pair it repairs | Grounded in the installed lifecycle: shipment claim has no `harness-ready` precondition, and harness generation is a harness-architect **skill step at Ship Step 2**, before any task claim — so no bootstrap task is needed and none exists. The residual literal-reading risk on P-004's Precondition row resolves through P-004's own installed Violation Action (halt and report), with an operator-performed policy-registry amendment as the only remedy. No force grant, waiver, or reinterpretation of operator approval is introduced |

## Out of scope

* Any change to the default-branch CI workflow.
* Any retroactive re-confirmation of already-shipped harnesses.
* Any bypass, waiver, or `--force` path for P-004. None is introduced by this
  release unit, and none is needed: `176-S` reaches harness generation through
  the installed lifecycle, and the residual literal-reading risk on P-004's
  Precondition row resolves through that policy's own Violation Action — halt
  and report — never through a self-granted exemption.
* `168-S`'s own manifest, which is not modified by this release unit.

## Plan Hardening Record (P-006)

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

| # | Hazard | Resolution in this contract |
|---|---|---|
| H1 | A bare identifier list leaves the ID→marker mapping undefined while the gate predicate requires a per-test marker, making the gate unimplementable | Typed per-entry shape `{test_id, marker}`; the declared outcome map is total and deterministic |
| H2 | Matching "expected failure markers in the output" against merged runner output lets one test's marker be satisfied by another test's traceback — a false CONFIRMED on an unconfirmed harness | Observation defined against `unittest.TestResult`; markers matched per test against that test's own `detail_text`; Verification carries the crossed-marker case |
| H3 | An unresolvable declared ID surfaces as a `_FailedTest` error indistinguishable from a genuine red, so a renamed or deleted test would *satisfy* the red requirement | Load-time placeholder detection classifies it `P004_MISSING_OBSERVATION` before the run |
| H4 | Skips, expected-failures, and unexpected-successes fold into pass or fail if unmodelled | Recorded as their own outcomes in a **total** declared-class x observed-outcome matrix with no default branch; a skipped declared test is `P004_MISSING_OBSERVATION`, and `expected_failure` / `unexpected_success` are the blocking `P004_INCONCLUSIVE_OUTCOME` because `@unittest.expectedFailure` inverts the run's exit code and makes the "exits non-zero" component unobservable in either direction |
| H5 | Without a marker-placement rule, a characterization entry could carry a meaningless marker and a red entry could omit one | `P004_MARKER_MISPLACED`; marker required on red, prohibited on green |
| H6 | A duplicate `test_id` within one list goes unhandled | `P004_DUPLICATE_DECLARATION`; uniqueness asserted within and across both lists |
| H7 | A regression suite that re-implements the comparison lets a runner defect pass its own tests | T7 ships the runner as importable code in `src/autoharness/`; **T5b** blocks on T7 and imports it |
| H8 | Tokens that cannot name an offending identifier are undiagnosable in practice, but collection-level and malformed-entry defects have no `test_id` to name | Structured tagged-subject model (`TestSubject` / `CollectionSubject` / `EntrySubject` / `DocumentSubject`); every token carries exactly one well-formed subject, and a token whose subject cannot be constructed is a runner defect |
| H9 | Correlating declared names to results by position over `loadTestsFromNames`, or by a name-keyed lookup into `TestLoader.errors`, is unimplementable: the former yields one suite per name and the latter is a flat list of strings | Independent per-name `loadTestsFromName`, recursive suite flattening, `len(loader.errors)` snapshot attribution, and test-object-identity correlation to requested names |
| H10 | Assigning `test_id` uniqueness and red/green disjointness to a Draft-07 schema leaves two of the thirteen tokens with no enforceable owner (`uniqueItems` compares whole instances; no cross-property comparison exists) | Validation boundary split by *rule*, with token **emission** consolidated in one place: the schema expresses per-item shape only; `validate_declared_harness_set()` runs it, maps each `jsonschema` error to `P004_MARKER_MISPLACED` / `P004_EMPTY_RED_SET` by structural `(absolute_path, validator)` pair, and then evaluates the relational rules for `P004_DUPLICATE_DECLARATION` / `P004_SET_OVERLAP`; keyed-map alternative rejected for silent last-wins semantics |
| H11 | `176-S` is unexecutable under the very P-002/P-004 pair it repairs | Resolved by grounding in the installed lifecycle rather than by inventing authority: shipment claim carries no `harness-ready` precondition; harness generation is a harness-architect **skill step at Ship Step 2**, before any task claim, and is never itself a claimable task. That step authors discoverable, failing harness tests into `tests/`, which is precisely what makes `discover -s tests` exit non-zero — so the Precondition's observable is **produced by the step that precedes the gate reading it**. The trailing "for every test function" qualifier is scoped by the normatively primary Statement row ("all harness tests") and by the Applies To row's nominated producer procedure, and the whole-suite reading is rejected because it would void the gate's entire operative history (17 live `harness-ready` records). Clarity defect, repaired by T2/T3 — not a deadlock. No bootstrap task, no bootstrap grant, no force, no waiver, no exit-code relaxation, no out-of-DAG operator policy edit, and no claim that operator approval alters the installed precondition |
| H12 | A subtest-only red path reaches `addSuccess`, so the gate reports a spurious `P004_UNEXPECTED_GREEN` on a genuinely red harness | `addSubTest` is a required override with stated attribution (parent test object, via the load-time identity map), first-failure outcome promotion, and in-call-order detail concatenation; the subtest cases are authored red in T5a and verified green in T5b |
| H13 | "The schema owns token X" names a detector with no reporter, so a fail-closed token degrades to an opaque `jsonschema` traceback | The mapping is an executable contract: one entry point, structural `(absolute_path, validator)` keys never message parsing, an identifier recovered from the parsed document, and `P004_DECLARATION_SCHEMA_ERROR` as a hard halt on any unmapped pair |
| H14 | Declaring the harness set in `.autoharness/harness-manifest.yaml` is unimplementable: that file is a singleton install inventory with no shipment dimension, rewritten by `autoharness install`/`tune`, so two shipments cannot both declare and any declaration is destroyed on the next install | Shipment-scoped storage `.autoharness/harness-sets/{shipment_id}.yaml` under its own `schemas/declared-harness-set.schema.json`, mirroring the installed `bootstrap-grants/{shipment_id}.yaml` precedent; named writer, single authoritative reader, archive-based retention, and three independent fail-closed staleness checks |
| H15 | Object-identity correlation answers "which object came back" but not "is this the declared test", so a rename or loader alias satisfies attribution while silently violating the declaration | Two independent checks with separate mechanisms: `requested_of[id(test)]` governs **attribution**; exact `TestCase.id() == requested_name` string equality governs **declaration conformance** and emits `P004_DECLARED_ID_MISMATCH`. Neither is derived from the other; `_FailedTest` placeholders are excluded to avoid a duplicate token for an already-classified defect |
| H16 | Multiple entry points (skill prose, a bare `python -m unittest <ids>` line, an agent reading raw output) can each produce a `CONFIRMED` verdict, so the weakest path defines the gate | One atomic public entrypoint `run_p004_gate()` / `autoharness gate p004`, owning load-validate-run-compare-tokens-JSON; `CONFIRMED` is recordable **only** from its JSON, bound to a `declaration_digest`; a bare unittest invocation is normatively declared insufficient in policy text and pinned by an end-to-end regression; terminal-unavailable runtimes use the `P004_GATE_REQUEST` parity block and record the returned JSON verbatim, never synthesizing a verdict |
| H17 | A RED test module that raises at import time yields a `_FailedTest` placeholder, which the gate classifies `P004_MISSING_OBSERVATION` — so the RED task fails its own gate while appearing to be "correctly red" | Binding import-safety rule on every RED task: not-yet-existing boundaries are imported **inside** the test body via `_load_boundary()`, each declared RED test individually executes and fails with its own marker in its own `detail_text`, and zero `loader.errors` is asserted directly. Applied here to T1a/T5a and, in their own records, to `170.011-T`, `171.015-T`, `172.008-T` |

**Risky actions (`ProposedAction` / `ActionRisk`).**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| Rewrite the P-004 precondition in `templates/policies/workflow-policies.md.tmpl` (T2) | **High** — changes a fail-closed gate every consumer workspace installs | Operator review of the rewritten precondition text | Revert the P-004 section; change is confined to one clause |
| Apply the identical rewrite to `.github/policies/workflow-policies.md` (T3) | High — must land atomically with T2 | Same review | Revert together; T3 blocks on T2; byte-identity check is a gate |
| Add `schemas/declared-harness-set.schema.json` (T1) | Low — a new, additive schema file; `schemas/harness-manifest.schema.json` and every existing installation manifest are untouched | Standard PR review | Delete the schema and the `.autoharness/harness-sets/` directory; no live declaration exists yet |
| Add the `P004Result` runner to `src/autoharness/` (T7) | Medium — new executable gate path | Standard PR review | Revert; the runner is additive and nothing calls it until T2/T3 land |
| Change the harness-architect skill (T4) | Medium — template, plus installed mirror where one exists | Standard PR review | Revert all touched copies together |

**Rollback coupling.** T2+T3 revert together (policy mirror pair). T4's touched
copies revert together. T1 and T7 are additive and revert independently. T5a,
T5b, and T6 are test-only. No persisted state is mutated anywhere in the unit.

**Monitoring and validation window.** The first shipment to declare a harness
set under the new schema is the live signal: its confirmation run must emit a
per-token summary naming concrete test IDs. The default-branch whole-suite gate
must remain green throughout — T6 is the standing assertion of that, and it
runs on every CI invocation.

**Operator checkpoints.** Two. One: if a conforming harness-architect fails
closed on P-004's installed Precondition row while generating `176-S`'s harness,
it halts and reports, and the operator decides whether to land the `T2`/`T3`
precondition amendment ahead of the shipment. This is an operator action on the
operator's own policy registry, not an agent bypass, and no `harness-ready`
label is applied until the amended precondition is satisfied. Two: review of the
rewritten P-004 precondition text (T2/T3) before merge, since it changes a
policy every consumer installs.

**Review-gate capability risk (P-012).** Reviewer-subagent dispatch was
degraded in the authoring session. Plan review MUST emit literal
`dispatch_mode:` and `decision:` markers, and MUST apply both the Constitution
Reviewer persona (policy-registry change) and the Python Reviewer persona
(`unittest` loader/result semantics) inline.

**Unresolved operator decisions blocking safe execution.** None.

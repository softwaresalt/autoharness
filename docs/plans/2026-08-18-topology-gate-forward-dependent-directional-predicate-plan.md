# Implementation Plan — Topology gate: directional predicate for forward-dependent suppression

Date: 2026-08-18
Agent: Stage (planning only — Ship executes)
Source of truth: `docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`
Classification: **reliability hotfix (P1 gate-correctness defect, unfixed on `main`)**
Feature: `131-F` · Task: `131.001-T` · Shipment: `140-S`
Sequencing: **predecessor of `138-S`** (explicit `blocks` edge)

## Goal

Restore the topology gate's implicit-predecessor fallback so it is suppressed
**only** by a genuine reverse edge (a numerically **lower** shipment declaring
the target as its dependency), and **not** by an ordinary forward dependent (a
numerically **higher** shipment declaring the target as its dependency).

The current code silently **allows a claim that should have been blocked** by
`PREDECESSOR_NOT_SHIPPED`. This is a false-negative in a safety gate: it fails
open, not closed.

## Non-goals

* No redesign of the numeric-adjacency heuristic itself. The heuristic's
  existence, its `^(\d+)-S$` shape, and its "highest number strictly below the
  target" selection are all unchanged.
* No change to any other gate, token, exit code, or the `TopologyInput` /
  `ShipmentState` contracts.
* No change to explicit-dependency handling (`blocking_predecessor_ids`
  semantics are untouched).
* No rediscovery. The fix and its regression test are already verified; this
  plan **reuses the recorded diff verbatim** rather than re-deriving it.
* No touching of `138-S`, `129-F`, or the cancelled migration scope beyond the
  sequencing edge.

## Defect summary (confirmed read-only against `main` @ `747193fe`)

`src/autoharness/gates/topology.py::_prior_shipment_id`, line **1345**:

```python
if any(target in shipment.blocking_predecessor_ids for shipment in shipments):
    return None
```

The predicate tests only *"does an edge involving this target exist at all"*,
with **no directionality filter**. Introduced by PR #357 / commit `0568f044`
(shipment `139-S`) while fixing a narrower multi-hop gap.

### Reproduction (from the compound doc; verified present on `main`)

```python
readers = _FakeReaders(shipments=(
    _shipment('111-S', 'queued'),
    _shipment('112-S', 'queued'),
    _shipment('113-S', 'queued', deps=('112-S',)),  # NORMAL forward dep
))
evaluate(TopologyInput(mode='agent', phase='pre_claim', target_shipment_id='112-S'), readers=readers)
# ACTUAL:   exit_code 0, primary_token None          <-- claim wrongly ALLOWED
# EXPECTED: primary_token 'PREDECESSOR_NOT_SHIPPED', predecessor_id '111-S'
```

`113-S depends on 112-S` is the **normal forward-order case the heuristic
exists to support**. It says nothing about whether `112-S` has an undeclared
implicit predecessor — and `111-S` is queued and numerically prior, so the
gate should block.

## The change

### Step 1 — `src/autoharness/gates/topology.py::_prior_shipment_id`

Replace the direction-blind `any(...)` guard with an explicit
**numerically-lower-only** loop, per the verified diff recorded in the
compound doc:

```python
for shipment in shipments:
    other = re.match(r"^(\d+)-S$", shipment.shipment_id)
    if not other:
        continue
    if int(other.group(1)) >= target_num:
        continue
    if target in shipment.blocking_predecessor_ids:
        return None
```

Replace the accompanying comment block with the corrected rationale (also
recorded verbatim in the compound doc), which must state *why* the direction
filter is load-bearing — not merely that it exists.

Everything after this guard (the `prior` selection loop and `return`) is
**unchanged**.

### Step 2 — `tests/test_gates_topology.py`

Add one regression test to the existing
`ImplicitNumericPredecessorTests` class (line ~1609):

`test_higher_numbered_forward_dependent_does_not_suppress_targets_own_predecessor_check`

asserting the reproduction above now yields `PREDECESSOR_NOT_SHIPPED` with
`predecessor_id == '111-S'`. Use the existing `_FakeReaders` (line 20) and
`_shipment(...)` (line 61) helpers — no new fixtures.

## Regression safety analysis (done at plan time, not deferred)

The single highest risk is re-opening the multi-hop gap that commit
`0568f044` closed. Analysed explicitly:

| Existing test | Scenario | Under fixed predicate | Verdict |
|---|---|---|---|
| `test_multi_hop_reverse_dependency_disables_fallback_entirely_not_just_the_violator` (line 1677) | target `139-S`; `138-S` declares `deps=(139-S,)`; `137-S` unrelated | `138 < 139` **and** `139-S ∈ 138-S.deps` → `return None`. Fallback still fully disabled; `137-S` still never injected. | **passes unchanged** |
| New forward-dependent test | target `112-S`; `113-S` declares `deps=(112-S,)` | `113 >= 112` → `continue`; no other declarer → falls through to numeric adjacency → `111-S` | **newly passes** |

The two cases are **separated exactly by the numeric direction of the
declaring shipment**, which is precisely the predicate being introduced. The
multi-hop fix and this fix are therefore complementary, not competing.

Live-shipment impact: the `138-S → 139-S` relationship is **unaffected** —
`138-S` is numerically lower, so it is handled by the retained lower-numbered
branch, identically before and after. The compound doc records no known active
false-negative in the current live set; this is a latent defect being closed
before it can bite.

## Verification

Already performed once with the fix applied locally (recorded in the compound
doc): `tests/test_gates_topology.py` **94/94 tests, 113/113 subtests pass**;
full suite **1550 passed**. Ship must independently re-run:

1. `tests/test_gates_topology.py` — expect 95 tests (94 + 1 new), all passing.
2. Full `tests/` suite — no new failures.

Known-unrelated pre-existing failure, **not** caused by this change and not to
be "fixed" here:
`tests/test_deploy_harness_scripts.py::DeployHarnessPs1ChecklistExecutionTests::test_checklist_report_prints_non_interactively`
(local environment version-string mismatch; reproduces identically with and
without the fix).

## Blast radius

| Dimension | Assessment |
|---|---|
| Files touched | 2 (`src/autoharness/gates/topology.py`, `tests/test_gates_topology.py`) |
| Functions touched | 1 (`_prior_shipment_id`) |
| Public API / contracts | none |
| Schemas | none |
| Templates | none |
| CLI distribution | none |
| Behaviour change | strictly *more* blocking (fail-closed direction) |

The change can only cause the gate to block **more** often, never less. A
regression would surface as a spurious `PREDECESSOR_NOT_SHIPPED` — loud,
immediate, and non-destructive — rather than as a silent mis-permit.

## Requires plan hardening

**yes** — see `docs/plans/2026-08-18-topology-gate-forward-dependent-directional-predicate-hardening.md`.

Rationale: the blast radius is small, but the artifact is a **safety gate that
authorises shipment claims**, and this is the **third** correction to the same
predicate (skip-violator → any-direction → directional). The failure mode of
the two prior attempts was *reasoning about the predicate in isolation rather
than against both directional cases at once*. That pattern justifies a
hardening pass despite the small diff.

## Sequencing

`140-S` is made the **next eligible shipment**, and `138-S` carries an explicit
`blocks` edge on `140-S`, so this reliability fix merges **before** any
abandonment/closure handling that itself exercises the topology gate
(`138-S`'s abandonment requires a `claim`, which runs `pre_claim`).

## 2-hour rule

Single task, single function, one recorded diff, one recorded test, fix already
verified. Well inside the 2-hour envelope. `size: XS`, `complexity: low`
(mechanical application of a verified diff; the *reasoning* was the hard part
and is already banked in the compound doc).

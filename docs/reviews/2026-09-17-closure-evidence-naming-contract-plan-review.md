---
title: "Plan review — Closure-evidence naming contract reconciliation (cycle 1)"
description: "Multi-persona plan review of docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md, gating harvest. Cycle 1 returned PASS_WITH_CONDITIONS with 0 P0 / 2 P1 / 3 P2 / 2 P3; all P1 and in-scope P2 findings were resolved in plan revision 2, resolving the gate to PASS."
doc_type: review
source: docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md
date: 2026-09-17
plan_path: docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
plan_revision: 2
source_decision: docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md
source_stash_id: FD0CCB42
review_cycle: 1
review_cycles_remaining: 2
dispatch_mode: declared-degradation
decision: PASS
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "closure"
  - "contract-drift"
  - "fail-closed-design"
---

# Plan Review — Closure-Evidence Naming Contract (cycle 1)

**Gate decision: PASS** (entered the cycle as `PASS_WITH_CONDITIONS`; all
conditions were resolved in plan revision 2 within the same cycle).

**Dispatch mode**: declared degradation. Cross-model reviewer persona dispatch is
unavailable in this session (no `agent-engram` search surface, no cross-model
subagent transport). Always-on personas were applied directly by Stage against
the plan text, the decision artifact, and the live codebase. This degradation is
declared rather than silent, per the plan-review contract; it means persona
independence is weaker than a dispatched review, and that limitation is recorded
as a known property of this verdict.

## Inputs

| Artifact | Path | Revision reviewed |
|---|---|---|
| Plan | `docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` | 1 → 2 |
| Decision | `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md` | 1 |
| Source bug evidence | `docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md` | — |
| Prior learning | `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md` | — |
| Stash entry | `FD0CCB42` | live |

## Findings

Severity scale: **P0** blocks the gate outright; **P1** must be resolved before
harvest; **P2** should be resolved or explicitly accepted; **P3** is recorded
for follow-up.

### F-1 (P1) — Reader protocol change did not account for in-repo test doubles

**Observation.** U2 adds a `closure_discovery` member to the reader protocol
declared at `src/autoharness/gates/topology.py:131`. Inspection of
`tests/test_gates_topology.py` finds roughly fifteen structural implementations
of `closure_complete` (lines 91, 161, 1690, 1705, 1731, 1746, 1787, 1818, 1835,
1944, 1955, 2151, 2538, 3024, 3068, 3334) acting as test doubles, plus
`_NullReaders` at `topology.py:751`.

**Why it matters.** A protocol change that silently breaks fifteen call sites is
exactly the kind of mid-execution surprise that produces unplanned scope
widening — the failure mode the 2-hour rule and width isolation exist to
prevent. An executing agent that discovers this at U2 would be pushed toward
either an oversized commit or an improvised workaround.

**Resolution (applied in revision 2).** Risk **R10** added to the plan's Risks
and Caveats table, and U2's Changes section now explicitly names `_NullReaders`,
the protocol declaration, and the in-repo test doubles as in-scope for that
unit. The work remains within U2's 2-hour envelope because the doubles change
mechanically and identically.

### F-2 (P1) — The plan's single most important safety property was prose-only

**Observation.** The plan asserted in several places that
`_closure_artifact_complete` (`topology.py:303-337`) and
`_closure_conditions_satisfied` (`topology.py:281-300`) remain unchanged. No
mechanical check enforced that assertion.

**Why it matters.** This is the property that keeps the gate fail-closed. The
source bug report's non-goals list "relaxing the consumer predicate" first, and
the compound learning documents that per-clause review reliably passes locally
correct changes whose composition is wrong. An unenforced invariant on a
fail-closed release gate is the highest-leverage weakness available in this
plan.

**Resolution (applied in revision 2).** Hardening item **H1.1** promotes
byte-identity of both functions to a hard acceptance criterion on U2, with a
diff over the named line ranges as required evidence. It is now a blocking
condition rather than an assertion.

### F-3 (P2) — "Closed enumeration" was unenforced

**Observation.** Decision D3 describes the recognized-read pattern set as
**closed**, which is the property that keeps read-side recognition from
degenerating into an ever-widening wildcard. Nothing prevented a future change
from appending a third pattern.

**Resolution (applied in revision 2).** Hardening item **H1.4** adds a
cardinality assertion: the recognized-read tuple must contain exactly two
members, so adding a third fails the suite and forces a deliberate contract
decision.

### F-4 (P2) — New gate token could be silently swallowed downstream

**Observation.** U3 introduces `PREDECESSOR_CLOSURE_UNRECOGNIZED` into the
gate's public token vocabulary. The compound learning's "Unrecognised is loud"
rule states that a consumer which falls through silently on an unknown value
converts a vocabulary extension into an undetected behaviour change.

**Resolution (applied in revision 2).** Hardening item **H6** adds a mandatory
sweep of `PREDECESSOR_CLOSURE_*` token-dispatch sites to U3, classifying any
silent fall-through as a blocking finding for that unit rather than a follow-up.

### F-5 (P2) — U7 exceeded the 2-hour test-scenario ceiling

**Observation.** Revision 1's composed-test unit carried five scenarios
(composed round-trip, real-corpus proof, dual-artifact precedence, historical
failure shapes, adversarial ID collision), above the plan contract's ceiling of
four.

**Resolution (applied in revision 2).** The historical failure shapes and the
adversarial collision test were split into a new unit **U8**; U7 and U8 now
carry four scenarios each. The plan's unit count moved from eight to nine and
the dependency graph, execution order, and requirements trace were updated
consistently.

### F-6 (P3) — No canonical closure *writer* is delivered

The source bug report's acceptance criterion 2 asks for a canonical writer that
generates path **and** frontmatter. This plan delivers a path builder and a
validator, which fully closes the naming axis, but not artifact-body generation.
**Accepted as out of scope** per decision **OQ-1**. Recorded for follow-up; not
captured as a new stash entry by this session.

### F-7 (P3) — Closure frontmatter schema not promoted into `schemas/`

**Accepted as out of scope** per decision **OQ-2**. Promoting it would cross into
schema evolution and materially widen blast radius beyond the stash entry's
scope fence.

## Persona Verdicts

| Persona | Verdict | Basis |
|---|---|---|
| **Architecture** | PASS | The contract is placed in a new `gates/closure_contract.py` rather than inside `topology.py`, correctly separating definition from consumer (P-D1). Module shape matches the established `shipment_closure.py` / `bootstrap_grant.py` / `sizing.py` siblings. The CLI addition is a purely additive branch in a flat dispatcher. |
| **Scope boundary** | PASS | Every unit carries an explicit scope guard. D8's zero-closure-artifact invariant is mechanically verified by H3's `git diff --name-status … -- docs/closure/` check. The decision names every excluded adjacent stash entry, and `3EF5AAF2` is explicitly declared untouched. No unit reaches into `165-F`/`173-S` territory. |
| **Standards / granularity** | PASS (after F-5) | All nine units satisfy < 3 production files, < 5 functions, < 4 test scenarios. Width isolation holds: U1-U4 are Python source/CLI, U5-U6 are documentation (template + installed mirror), U7-U9 are tests. No unit mixes Python source with template work, and no unit mixes template work with schema work. |
| **Fail-closed / safety** | PASS (after F-2, F-3, F-4) | The validity predicate is mechanically pinned; the read set's closedness is asserted; token-vocabulary extension is swept for silent fall-through; `BacklogUnavailableError` on malformed frontmatter is preserved and tested. The read-side widening is a closed two-regex enumeration, not a wildcard. |
| **Test efficacy** | PASS | D7's binding construction rule (the composed test must obtain its filename from `build_closure_path`) plus U7's real-corpus assertion on `162-S`/`174-S` directly defeat the hand-written-fixture anti-pattern that allowed this defect to survive six occurrences across two workspaces. This is the strongest element of the plan. |
| **Dependency / sequencing** | PASS | The unit graph is acyclic with a clean topological order U1→U9. H2 promotes the U1-before-U2/U5 ordering to a merge-order constraint, and U9's parity test mechanically detects a violation. The shipment-level DAG edge is cycle-free by construction (the new shipment is `dag-root` with no outgoing edges) and is verified by re-running `dag-readiness`. |

## Unsatisfiable-Gate Check

Per compound lesson 6 (carried as OQ-6 of the prior learning), each gate outcome
introduced or modified was checked for reachability. All seven rows of the
decision's D3 outcome table name a concrete legitimate state. The new
`PREDECESSOR_CLOSURE_UNRECOGNIZED` outcome is both reachable (a file named
`162-S-notes.md` in `docs/closure/`) and escapable (rename to the canonical
pattern), so it is not a trap state. **No unreachable or unsatisfiable gate was
found.**

## Verification of the Plan's Central Claim

The reviewer independently reproduced the plan's core evidence rather than
accepting it from the plan text:

* `FilesystemTopologyReaders(Path('.')).closure_complete('162-S')` → `None`;
  `('174-S')` → `None`; `('173-S')` → `True`; `('161-S')` → `True`.
* `autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json`
  → `exit_code: 1`, `token: PREDECESSOR_CLOSURE_INCOMPLETE`,
  `details.predecessor_source: "explicit"`, `details.closure_complete: null`.
* `.backlogit/archive/162-S.md` → `archived_status: shipped`;
  `.backlogit/queue/163-S.md` → `dependencies: [162-S]`.
* `autoharness gate dag-readiness --json` → `cycle_detected: false`,
  `ready_set: ["163-S"]`.

The plan's claim that this work is the **direct and only** unblocker for
`163-S` is confirmed: predecessor derivation is already explicit and correct,
and the sole failing condition is closure-artifact discovery.

## Gate Outcome

**PASS.** 0 P0 open, 0 P1 open. The plan is cleared for `harvest`. Two review
cycles remain unused.

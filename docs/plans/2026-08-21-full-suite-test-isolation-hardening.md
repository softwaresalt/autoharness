---
title: "Plan hardening - full-suite test-isolation repair"
date: 2026-08-21
plan: docs/plans/2026-08-21-full-suite-test-isolation-plan.md
stash_id: E8158860
deliberation: ".backlogit/queue/024-DL.md"
outcome: HARDENED
amendments: [A1, A2, A3]
---

# Plan Hardening - full-suite test-isolation repair

Date: 2026-08-21
Agent: Stage (P-006 hardening gate)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Why hardening applies

`requires_plan_hardening: yes`. Three independent hardening signals: (1) the root
cause is UNKNOWN at plan time, so the plan is partly conditional; (2) Task 2 is a
58-call-site mechanical edit across four test modules, a classic
looks-mechanical-but-changes-semantics surface; (3) five of the affected tests
are themselves REGRESSION GUARDS, so a careless "fix" can destroy protection
while turning the suite green - the single most dangerous outcome available here.

## H1 - The plan must not be able to succeed by weakening a guard

**Risk.** The cheapest path to a green suite is to relax
`test_root_tracked_json_matches_allowlist` (a 133-F/142-S guard), broaden the
telemetry gitignore assertions, or delete a victim. Every one of those turns the
gate green while removing the protection the gate exists to provide.

**Hardening.** AC10 already requires the five victims' assertions to be unchanged
by diff. Strengthen it: **AMENDMENT A1** - Task 3 must additionally re-run the
five victim tests IN ISOLATION and confirm identical pass/fail semantics, and the
task record must include the verbatim `git diff` of the five victim files showing
either no change at all, or changes confined to `setUp`/`tearDown`/imports with
zero assertion-line edits.

## H2 - The "hard stop" must be a real stop, not a soft suggestion

**Risk.** Task 1 step 5 says stop if the pair is not isolated. Under time
pressure the natural failure mode is to skip to Task 2/3 and "fix it anyway,"
producing a change that may coincidentally green the suite for unrelated reasons
and permanently hides the real defect.

**Hardening.** **AMENDMENT A2** - Task 3 is BLOCKED on Task 1 producing AC1 (a
minimal reproducing pair). If Task 1 hard-stops, Task 3 must be returned blocked
via the official return-blocked operation with the narrowed candidate set, and
the shipment closes with Tasks 1-2 only. Tasks 1 and 2 are independently
valuable and independently mergeable; Task 3 is not. This is encoded as a real
dependency edge at harvest, not as prose.

## H3 - Task 2's anchor change can silently alter what a test asserts

**Risk.** `tempfile.TemporaryDirectory(dir=Path.cwd())` in the topology and
backlog-root tests is not decoration: several of those tests exercise
WORKSPACE-CONTAINMENT logic, where the temp workspace being inside the repository
is part of the scenario. Moving such a test to system temp changes the scenario
while keeping the assertion text, which is worse than leaving it alone.

**Hardening.** AC6 already requires a recorded containment determination per
module. Strengthen to per-CALL-SITE for the two modules that mix concerns
(`test_gates_topology.py`, `test_gate_pipeline_topology_cli.py`), and require
that the isolation pass-count check in AC7 be run per module before and after.
Default when uncertain: anchor to `Path(__file__).resolve().parents[1]` (repo
root, deterministic) rather than relocating. Anchoring is always safe;
relocating is not.

## H4 - A Windows-only defect cannot be guarded by Linux CI

**Risk.** Hosted CI is green today and will stay green after the fix, so CI
cannot detect a regression of this defect. A behavioural regression test would
give false assurance.

**Hardening.** The regression guard must be STRUCTURAL and platform-independent -
the AST guard in Task 2 (`tests/test_test_suite_isolation_contract.py`), which
runs identically on both platforms. **AMENDMENT A3** - additionally, the guard
must assert the ABSENCE of the anti-pattern rather than the presence of a fix,
and must name every offending file and line in its failure message so a future
reintroduction is self-explaining.

## H5 - Scope containment against production code

**Risk.** If the bisect implicates a module-level cache or global in
`src/autoharness/`, the tempting move is a one-line fix "while we're here."

**Hardening.** Already handled by 024-DL R5 and the plan's Non-goals; confirmed
sufficient. Stage's static scan found no module-level cache in
`autoharness/backlog_root.py` (120 lines, no caching) or
`autoharness/gates/topology.py` (module-level constants are frozensets and
compiled regexes only, all immutable). The scan was not exhaustive, so the stop
rule stands.

## H6 - Evidence quality of the bisect

**Risk.** A bisect that reports "excluding module X makes it pass" is a
correlation, not a mechanism, and would license a fix that treats the symptom.

**Hardening.** AC2 (verbatim `git init` stderr) and AC3 (causal claim with
evidence) already require mechanism. Confirmed sufficient - the exit-128 stderr
text is the single highest-value unrecorded datum in this whole finding and its
capture is non-negotiable.

## H7 - Interaction with the other two shipments staged this session

**Risk.** The variable-derivation shipment extends
`test_scope_containment_policy_contract.py`, one of the three modules implicated
here. Landing both concurrently would confound the bisect.

**Hardening.** Confirmed by sequencing: this shipment executes BEFORE the
variable-derivation shipment, enforced by a shipment dependency edge. Recorded
in both plans.

## Outcome

**HARDENED.** Amendments A1, A2, A3 to be applied to
`docs/plans/2026-08-21-full-suite-test-isolation-plan.md` before plan-review.

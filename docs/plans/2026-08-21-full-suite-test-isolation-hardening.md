---
title: "Plan hardening - full-suite test-isolation repair"
date: 2026-08-21
plan: docs/plans/2026-08-21-full-suite-test-isolation-plan.md
stash_id: E8158860
deliberation: ".backlogit/queue/024-DL.md"
outcome: HARDENED
amendments: [A1, A2R, A3]
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

## H2R - The "hard stop" must be a real stop, and it must also be EXECUTABLE

*(Supersedes H2/amendment A2, rewritten in review-fix cycle 2, PR #386, thread
`PRRT_kwDORzpWpM6bSzNF`.)*

**Risk 1 (original).** Task 1 step 5 says stop if the pair is not isolated. Under
time pressure the natural failure mode is to skip to Task 2/3 and "fix it anyway,"
producing a change that may coincidentally green the suite for unrelated reasons
and permanently hides the real defect.

**Risk 2 (discovered in review).** The original hardening created a WORSE failure
than the one it prevented. A2 required Task 3 to be "returned blocked via the
official return-blocked operation" while "the shipment closes with Tasks 1-2
only". That resolution is not executable:

* `.github/agents/_ship.agent.md:325-340` makes the shipment manifest the closure
  membership record, explicitly "never mutated to make execution proceed";
* its status rule is exhaustive and positive - KEEP `queued`/`active`,
  SKIP-AND-REPORT pre-archived, REPORT `already_done`, and **any other status is a
  FAIL-CLOSED HALT, never a skip**;
* backlogit 1.8.0 defines no shipment `blocked` status
  (`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`: only
  `queued -> active`, `active -> shipped`, `active -> abandoned`);
* the installed Ship contract never instructs Ship to use
  `backlogit_return_blocked`: `.github/agents/_ship.agent.md` carries ZERO prose
  references to it across all `return_blocked` / `return-blocked` / `return blocked`
  variants. Ship holds tool ACCESS through the `'backlogit/*'` frontmatter wildcard,
  but access is not instruction - the contract gives the operation no semantics on
  any step, gate, or failure path, and the Step 2 derivation halts fail-closed on a
  `blocked` member regardless of how it got there. (By contrast the operation IS
  enumerated in Stage's own allowlist in `.github/agents/_stage.agent.md`, which is
  a further sign it was never intended as a Ship-side lifecycle lever.) A2 therefore
  relied on Ship behaviour its contract does not define.

A `blocked` member therefore DEADLOCKS the whole shipment rather than permitting
the intended partial close. A hardening that predictably deadlocks the shipment is
a hardening defect, not an execution problem.

**Hardening.** **AMENDMENT A2R** - separate conditional from unconditional work by
a SHIPMENT BOUNDARY rather than by a task status:

1. Tasks 1-2 (diagnosis + ambient-cwd decoupling) are unconditional and ship as
   **149-S** / feature 141-F. Every member has exactly one terminal outcome, so
   149-S can always close.
2. Tasks 3a-3b (git self-diagnosis + conditional polluter remediation) ship as the
   successor **151-S** / feature 143-F, gated by a shipment dependency edge.
3. Task 1 has TWO terminal outcomes, both closing `done`: `VERDICT: PAIR-ISOLATED`
   or `VERDICT: INCONCLUSIVE` (narrowed candidate set is the deliverable).
4. Task 3b has THREE dispositions (R1 remediate / R2 no longer reproduces / R3 no
   polluter isolated) and all three close `done` with recorded evidence.
5. No task in either shipment can end `blocked`; neither shipment needs
   abandonment; no manifest is ever mutated.

**H2's original intent is preserved STRUCTURALLY, and more strongly than by A2.**
There is no remediation work inside 149-S for a time-pressured agent to slip into,
because remediation is not in that shipment at all. And Task 3b AC13 forbids ANY
source edit, in ANY disposition, that does not cite Task 1's recorded minimal
reproducing pair - a citation that a speculative fix cannot produce. A2 relied on a
status transition an agent could mis-apply; A2R relies on work simply not being
present, plus an evidence citation that is checkable at review.

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

**Hardening.** Confirmed by sequencing, enforced by shipment dependency edges:
`148-S -> 149-S -> 151-S -> 150-S`. BOTH test-isolation shipments (149-S diagnosis
and decoupling, 151-S remediation) execute BEFORE the variable-derivation shipment
150-S, so 150-S cannot land changes to `test_scope_containment_policy_contract.py`
either before the bisect (confounding the diagnosis) or between the bisect and the
remediation (invalidating the recorded reproducer). Recorded in both plans.

*(Updated in review-fix cycle 2: A2R split the test-isolation work across two
shipments, so H7's "before the variable-derivation shipment" constraint now binds
151-S as well as 149-S. Placing 151-S BEFORE 150-S rather than after it is
deliberate. Because every task in 151-S terminates `done`, 151-S always reaches
`shipped` and can never strand 150-S on an unsatisfied dependency edge - the
compound record notes such an edge clears on predecessor SHIP, and an abandoned
predecessor would have left 150-S permanently blocked. Task 3b's Step 0 gate still
re-verifies the reproducer at 151-S's head, so the R2 disposition covers the case
where Task 2's own anchor work already removed the defect.)*

## Outcome

**HARDENED.** Amendments A1, A2R, A3 applied to
`docs/plans/2026-08-21-full-suite-test-isolation-plan.md`. A1 and A3 were applied
before plan-review; A2 was applied before plan-review and then WITHDRAWN AND
REPLACED by A2R in review-fix cycle 2 (PR #386) after Copilot review established
that A2's blocked-member resolution deadlocks the shipment rather than permitting
a partial close. The plan carries A2R, not A2.
